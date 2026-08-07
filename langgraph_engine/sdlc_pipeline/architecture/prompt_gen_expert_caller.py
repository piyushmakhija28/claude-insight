#!/usr/bin/env python3
"""
Level 3 - Prompt Generation Expert Caller

Reads CLI args, resolves the master ORCHESTRATION_TEMPLATE.md from
claude-global-library, prepends the runtime grounding block (call-graph risk,
complexity and the KG ROUTING summary from FR-3's KGRouter pre-injection), and
writes the assembled prompt to stdout as JSON.

This script assembles a prompt; it does not execute one. It previously spawned
`claude -p` and captured the child's stdout, which cannot work against the
master template: that template's save-and-stop protocol explicitly forbids
printing the generated prompt and requires writing it to docs/ instead.
Execution belongs to the active Claude Code session.

Invoked by: call_execution_script("prompt_gen_expert_caller", args)
Output: JSON with keys: status, prompt, llm_response, error (on failure).
  'llm_response' is always empty -- the caller reads `llm_response or prompt`,
  so the assembled prompt is what travels downstream.
"""

import json
import logging
import os
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Import bootstrap: put the repo root on sys.path so absolute
# langgraph_engine.* imports resolve when this file runs as a script.
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = Path(__file__).resolve().parent.parent.parent.parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_MASTER_TEMPLATE_RELPATH = "ORCHESTRATION_TEMPLATE.md"

ERROR_KIND_TEMPLATE_LOAD_FAILED = "TEMPLATE_LOAD_FAILED"
"""Emitted when the master orchestration template cannot be resolved.

Distinguishes an unrecoverable failure -- without the template there is no
orchestration to perform -- from a downstream LLM failure, where the assembled
prompt is still valid. The caller hard-aborts on this kind rather than
degrading to the raw user message, which would bypass KG routing, the decision
tree and the mandatory anti-hallucination layer with only a log line to show
for it.
"""

_RUNTIME_CONTEXT_TEMPLATE = """\
=== RUNTIME CONTEXT (injected by claude-workflow-engine) ===

This block is authoritative. Every value below was computed from the actual
codebase before this prompt was assembled. Treat each as established fact: do
not re-derive it, do not contradict it, and do not ask the user for it. Where a
step of the orchestration template below would otherwise compute one of these
values, use the value given here instead.

USER REQUIREMENTS:
%s

COMPLEXITY SCORE: %s
CODEBASE RISK   : %s
DANGER ZONES    : %s
AFFECTED METHODS: %s
HOT NODES       : %s

RUNTIME CONTEXT JSON:
%s

KG ROUTING (pre-resolved by KGRouter against claude-global-library):
%s

=== END RUNTIME CONTEXT -- the master orchestration template follows ===

"""

DEBUG = os.getenv("CLAUDE_DEBUG") == "1"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_args(argv):
    """Parse CLI arguments into a dict.

    Supported flags:
      --task-description <str>
      --complexity-score <int>        (space-separated)
      --complexity-score=<int>        (equals form)
      --call-graph-json <json-string>
      --kg-routing-json <json-string>
      --runtime-context-json <json-string>
    """
    args = {
        "task_description": "",
        "complexity_score": 5,
        "call_graph_json": "{}",
        "kg_routing_json": "{}",
        "runtime_context_json": "{}",
    }

    i = 1
    while i < len(argv):
        token = argv[i]
        if token == "--task-description" and i + 1 < len(argv):
            args["task_description"] = argv[i + 1]
            i += 2
        elif token == "--complexity-score" and i + 1 < len(argv):
            try:
                args["complexity_score"] = int(argv[i + 1])
            except ValueError:
                args["complexity_score"] = 5
            i += 2
        elif token.startswith("--complexity-score="):
            try:
                args["complexity_score"] = int(token.split("=", 1)[1])
            except ValueError:
                args["complexity_score"] = 5
            i += 1
        elif token == "--call-graph-json" and i + 1 < len(argv):
            args["call_graph_json"] = argv[i + 1]
            i += 2
        elif token == "--kg-routing-json" and i + 1 < len(argv):
            args["kg_routing_json"] = argv[i + 1]
            i += 2
        elif token == "--runtime-context-json" and i + 1 < len(argv):
            args["runtime_context_json"] = argv[i + 1]
            i += 2
        else:
            i += 1

    return args


def _load_template():
    """Load the master ORCHESTRATION_TEMPLATE.md from claude-global-library.

    Resolved through the 3-tier ``ResourceResolver`` chain (local sibling ->
    opt-in GitHub -> typed hard-fail), so the library stays the single source of
    truth for orchestration.

    There is deliberately no fallback template. The engine used to carry its own
    ``templates/orchestration_system_prompt.txt``, a fork of this master that had
    drifted to 198 lines against its 1,996 and lost nine steps along the way --
    including STEP 7, the anti-hallucination layer the master marks "MANDATORY
    for ALL projects -- NO exceptions". That file has been deleted rather than
    kept as a fallback: serving it when the library is unreachable would
    reintroduce, invisibly, exactly the drift this loader exists to remove. A
    missing library is reported as an error instead.

    Returns:
        Tuple of (template_text, error_message); exactly one element is None.
    """
    try:
        from langgraph_engine.library import build_default_resolver

        resource = build_default_resolver().fetch_kg_file(_MASTER_TEMPLATE_RELPATH)
        return resource.content, None
    except Exception as exc:
        return None, "Failed to load %s from claude-global-library: %s" % (
            _MASTER_TEMPLATE_RELPATH,
            exc,
        )


def _render_kg_routing_block(kg_routing):
    """Render the KG ROUTING grounding block for the ``{kg_routing_block}``
    placeholder.

    Summarizes a resolved ``KGRouter`` route (lead agent, skills, a
    persona-loaded marker) or emits a one-line legacy-path note when
    unresolved/library_missing. Never embeds the full ``persona_markdown`` --
    it can be large; a concise summary plus size marker is enough grounding
    for the LLM to trust the pre-resolved route without re-deriving it.
    """
    legacy_note = "No confident KG match -- proceed with keyword-based domain detection below (legacy path)."
    if not isinstance(kg_routing, dict) or kg_routing.get("status") != "resolved":
        notes = kg_routing.get("notes") if isinstance(kg_routing, dict) else ""
        return legacy_note + (f" ({notes})" if notes else "")

    lead_agent = kg_routing.get("lead_agent") or {}
    agent_name = lead_agent.get("name", "unknown")
    agent_role = lead_agent.get("role", "")
    skills = kg_routing.get("skills") or []
    skills_str = ", ".join(skills) if skills else "none"
    persona = kg_routing.get("persona_markdown") or ""
    persona_note = "full persona loaded, %d chars" % len(persona) if persona else "persona not loaded"
    role_line = ("  Role: " + agent_role + "\n") if agent_role else ""

    return ("Domain: %s | Pattern: %s\n" "Lead agent: %s\n" "%s" "Skills: %s\n" "Persona: %s") % (
        kg_routing.get("domain", "unknown"),
        kg_routing.get("pattern_id", "unknown"),
        agent_name,
        role_line,
        skills_str,
        persona_note,
    )


def _build_filled_prompt(template, args):
    """Prepend the runtime-context grounding block to the master template.

    The master ORCHESTRATION_TEMPLATE.md is a standalone instruction document,
    not a parameterised prompt -- the braces inside it (``{slug}``, ``{N}``,
    ``{date}``) are path patterns and authoring instructions the orchestrator
    fills itself, not substitution slots. Rewriting them here would corrupt the
    template. The eight runtime values the engine computes are therefore
    delivered as an authoritative header block ahead of the template body.

    Returns:
        The grounding block followed by the unmodified master template.
    """
    call_graph = {}
    try:
        call_graph = json.loads(args["call_graph_json"]) if args["call_graph_json"] else {}
    except (json.JSONDecodeError, TypeError):
        call_graph = {}

    kg_routing = {}
    try:
        kg_routing = json.loads(args["kg_routing_json"]) if args["kg_routing_json"] else {}
    except (json.JSONDecodeError, TypeError):
        kg_routing = {}

    runtime_context = {}
    try:
        runtime_context = json.loads(args["runtime_context_json"]) if args["runtime_context_json"] else {}
    except (json.JSONDecodeError, TypeError):
        runtime_context = {}

    risk_level = call_graph.get("risk_level", "unknown")
    danger_zones = call_graph.get("danger_zones", [])
    affected_methods = call_graph.get("affected_methods", [])
    hot_nodes = call_graph.get("hot_nodes", [])

    danger_zones_str = ", ".join(danger_zones) if danger_zones else "none"
    affected_str = ", ".join(affected_methods[:10]) if affected_methods else "none"
    hot_nodes_str = ", ".join(hot_nodes[:10]) if hot_nodes else "none"

    runtime_block = json.dumps(runtime_context, indent=2, ensure_ascii=True)

    # combined_complexity_score is on a 1-25 scale (not 1-10)
    complexity = args["complexity_score"]
    if complexity <= 8:
        tier = "low"
    elif complexity <= 16:
        tier = "medium"
    else:
        tier = "high"
    complexity_display = str(complexity) + "/25 (" + tier + ")"

    grounding = _RUNTIME_CONTEXT_TEMPLATE % (
        args["task_description"],
        complexity_display,
        str(risk_level),
        danger_zones_str,
        affected_str,
        hot_nodes_str,
        runtime_block,
        _render_kg_routing_block(kg_routing),
    )

    return grounding + template


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    """CLI entry point: build the orchestration prompt from the task description and
    runtime context, printing the result as JSON to stdout.
    """
    if DEBUG:
        print("[prompt_gen_expert_caller] Starting", file=sys.stderr, flush=True)

    args = _parse_args(sys.argv)

    if not args["task_description"]:
        print(json.dumps({"status": "ERROR", "error": "No --task-description provided"}))
        return

    # Load template
    template, err = _load_template()
    if err:
        print(json.dumps({"status": "ERROR", "error_kind": ERROR_KIND_TEMPLATE_LOAD_FAILED, "error": err}))
        return

    if DEBUG:
        print("[prompt_gen_expert_caller] Template loaded", file=sys.stderr, flush=True)

    # Fill placeholders
    filled_prompt = _build_filled_prompt(template, args)

    # No LLM call. This script assembles the orchestration prompt and returns it;
    # executing it belongs to the active Claude Code session, not to a nested
    # `claude -p` subprocess. The master template's own save-and-stop protocol
    # forbids printing a generated prompt, so capturing one from a child's stdout
    # was never going to work against it.
    #
    # 'llm_response' is kept as an empty string rather than dropped: the caller
    # reads `llm_response or prompt`, so an empty value routes the assembled
    # prompt downstream and the existing contract holds unchanged.
    result = {
        "status": "SUCCESS",
        "prompt": filled_prompt,
        "llm_response": "",
        "parsed_plan": None,
        "complexity_score": args["complexity_score"],
        "schema_warnings": [],
    }

    print(json.dumps(result, ensure_ascii=True))


if __name__ == "__main__":
    main()

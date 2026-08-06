#!/usr/bin/env python3
"""
Level 3 - Prompt Generation Expert Caller

Reads CLI args, loads the orchestration system prompt template,
fills the 8 placeholders (including the KG ROUTING grounding block from
FR-3's KGRouter pre-injection), calls the claude CLI subprocess, and writes
JSON to stdout.

Invoked by: call_execution_script("prompt_gen_expert_caller", args)
Output: JSON with keys: status, prompt, llm_response, error (on failure)

Environment:
  STEP1_PROMPT_GEN_SILENCE  seconds of claude CLI silence tolerated before the
                            child is treated as stuck (default: unbounded)

The former STEP1_PROMPT_GEN_TIMEOUT killed the claude CLI after a fixed 60
seconds regardless of whether it was working. Its replacement measures silence
rather than duration and defaults to no bound at all, per NFR-2 / ADR-016.
"""

import json
import logging
import os
import shutil
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Schema verifier (best-effort; non-blocking when import fails)
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = Path(__file__).resolve().parent.parent.parent.parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))


def _verify_prompt_schema(prompt):
    """Return list of error strings from schema_verifier (empty = valid)."""
    if os.getenv("ENABLE_RUNTIME_VERIFICATION", "0") != "1":
        return []
    try:
        from langgraph_engine.runtime_verification.schema_verifier import verify_orchestration_prompt

        return verify_orchestration_prompt(prompt or "")
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
_TEMPLATE_FILE = _TEMPLATES_DIR / "orchestration_system_prompt.txt"

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
_SILENCE_ENV_VAR = "STEP1_PROMPT_GEN_SILENCE"


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

    There is deliberately no fallback to the in-repo
    ``orchestration_system_prompt.txt``. That file is a fork of this template
    that drifted to 198 lines against the master's 1,996 and lost nine steps
    along the way -- including STEP 7, the anti-hallucination layer the master
    marks "MANDATORY for ALL projects -- NO exceptions". Serving it silently
    when the library is unreachable would reintroduce exactly the drift this
    loader exists to remove, and would do so invisibly. A missing library is
    reported as an error instead.

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


def _call_claude_cli(prompt):
    """Call claude CLI in headless print mode via stdin. Returns (response_text, error).

    Bounded by progress rather than by elapsed time: the CLI is left alone for as
    long as it keeps producing output, and only silence -- and only when an
    operator has configured an interval -- ends it. The circuit breaker observes
    the outcome so that a systemically failing CLI stops being called at all,
    which is the mechanism that replaces the deadline this used to carry.
    """
    from langgraph_engine.liveness import BreakerOpen, NoProgress, env_optional_seconds, run_supervised

    claude_path = shutil.which("claude")
    if not claude_path:
        return None, "claude CLI binary not found in PATH"

    if DEBUG:
        print("[prompt_gen_expert_caller] Running: claude CLI -p", file=sys.stderr, flush=True)

    try:
        result = run_supervised(
            [claude_path, "-p"],
            input=prompt,
            lease_interval=env_optional_seconds(_SILENCE_ENV_VAR),
            lease_name="prompt_gen_claude_cli",
            breaker_name="claude_cli",
        )

        if result.returncode != 0 and not result.stdout:
            stderr_preview = (result.stderr or "")[:300]
            return None, "claude CLI non-zero exit (%d): %s" % (result.returncode, stderr_preview)

        response_text = (result.stdout or "").strip()
        if response_text:
            return response_text, None
        return None, "claude CLI returned empty response"

    except BreakerOpen as exc:
        return None, "claude CLI circuit breaker open, call not attempted: " + str(exc)
    except NoProgress as exc:
        return None, "claude CLI made no progress: " + str(exc)
    except Exception as exc:
        return None, "claude CLI call failed: " + str(exc)


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

    if DEBUG:
        print("[prompt_gen_expert_caller] Calling claude CLI", file=sys.stderr, flush=True)

    # Call claude CLI subprocess
    llm_response, err = _call_claude_cli(filled_prompt)
    if err:
        print(json.dumps({"status": "ERROR", "error": err, "prompt": filled_prompt[:500]}))
        return

    if DEBUG:
        print("[prompt_gen_expert_caller] claude CLI responded", file=sys.stderr, flush=True)

    # Schema verification (non-blocking)
    schema_errors = _verify_prompt_schema(llm_response)
    if schema_errors:
        print(
            "[prompt_gen_expert_caller] schema warnings: " + "; ".join(schema_errors),
            file=sys.stderr,
            flush=True,
        )

    # Try to parse response as JSON (it should be per template instructions)
    parsed_plan = None
    try:
        if llm_response and "{" in llm_response:
            json_start = llm_response.index("{")
            json_end = llm_response.rindex("}") + 1
            parsed_plan = json.loads(llm_response[json_start:json_end])
    except Exception:
        parsed_plan = None

    result = {
        "status": "SUCCESS",
        "prompt": filled_prompt,
        "llm_response": llm_response,
        "parsed_plan": parsed_plan,
        "complexity_score": args["complexity_score"],
        "schema_warnings": schema_errors,
    }

    print(json.dumps(result, ensure_ascii=True))


if __name__ == "__main__":
    main()

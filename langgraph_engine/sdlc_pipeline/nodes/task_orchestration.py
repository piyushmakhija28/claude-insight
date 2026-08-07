"""Level 3 v2 step node wrapper.

Extracted from sdlc_pipeline/subgraph.py for modularity.
Windows-safe: ASCII only.

CHANGE LOG (v1.13.0):
  Removed Steps 1, 3, 4 node wrappers -- collapsed into Step 0 template call.
  Step 0 now injects combined_complexity_score (1-25 from Level 1) and
  CallGraph analysis into the template context before the subprocess calls.
  Step 0 output populates the fields that Steps 1,3,4,5,6,7 previously provided.

CHANGE LOG (v1.14.0):
  Step 0 caller scripts now use claude CLI subprocess (not direct llm_call API).
  Step 2 (plan execution) removed from pipeline -- orchestrator subprocess
  already produces a comprehensive plan. step1_plan_execution_node kept as
  deprecated no-op for backward compatibility with test imports.
"""

import os
from pathlib import Path
from typing import Any, Dict

try:
    from loguru import logger
except ImportError:
    import logging

    logger = logging.getLogger(__name__)

try:
    from ...flow_state import FlowState
except ImportError:
    FlowState = dict  # type: ignore[misc,assignment]

from ...liveness import env_optional_seconds as _env_optional_seconds


def _library_version() -> str:
    """Read the claude-global-library VERSION through the resolver chain.

    Recorded alongside the emitted prompt so a trace can be tied back to the
    exact library revision that produced it -- the master template lives there,
    not here, so the engine's own version says nothing about what was emitted.

    Returns:
        The version string, or "unknown" if the library cannot be reached. This
        is metadata for traces, never a gate: a missing version must not fail a
        step that has already produced a valid prompt.
    """
    try:
        from ...library import build_default_resolver

        return build_default_resolver().fetch_kg_file("VERSION").content.strip()
    except Exception as exc:
        logger.debug("[v2] Step 1 library version unavailable: {}", exc)
        return "unknown"


class OrchestrationTemplateUnavailable(RuntimeError):
    """Raised when Step 1 cannot obtain the master orchestration template.

    Deliberately fatal. The alternative -- continuing on the raw user message --
    runs the entire pipeline with no KG routing, no decision-tree traversal and
    no STEP 7 anti-hallucination layer, while every downstream step still
    reports success. That failure is invisible in the output and visible only as
    one line in a log, which is the most dangerous shape a failure can take.

    ``step1_task_analysis_node`` is deliberately not wrapped in
    ``node_error_handler``, so this propagates out of the graph rather than
    being folded into a fallback result.
    """


def step1_task_analysis_node(state: FlowState) -> Dict[str, Any]:
    """Step 0 v2: prompt_gen_expert -> orchestrator_agent chain.

    Phase 1: calls prompt_gen_expert_caller (fast, captured stdout), which
    resolves the master orchestration template from claude-global-library and
    prepends a runtime-context header carrying combined_complexity_score,
    CallGraph risk data and the KG route. It assembles the prompt only -- no
    LLM runs in this phase.

    Phase 2: emits the assembled prompt for the active session to execute, and
    records what was emitted in orchestrator_result. It no longer decomposes the
    prompt or runs agents itself -- the master template's STEP 13 produces the
    multi-agent bundle, and this node runs inside a hook subprocess that cannot
    execute in the session it is serving.

    Post-call: populates migration fields so Steps 8-14 receive correct data.
    """
    import json as _json

    # --- PRE-INJECTION A: combined_complexity_score from Level 1 (1-25 scale) ---
    # Do NOT re-compute; read directly from state. Scale is 1-25, not 1-10.
    complexity_score = state.get("combined_complexity_score", 5)

    # --- PRE-INJECTION B: CallGraph impact analysis ---
    call_graph_risk_level = "LOW"
    call_graph_danger_zones = []
    call_graph_affected_methods = []
    try:
        from ..call_graph_analyzer import analyze_impact_before_change

        project_root = state.get("project_root", ".")
        target_files = state.get("step1_target_files", [])
        task_desc = state.get("user_message", "")
        cg_result = analyze_impact_before_change(project_root, target_files, task_desc)
        if cg_result.get("call_graph_available"):
            call_graph_risk_level = cg_result.get("risk_level", "LOW")
            call_graph_danger_zones = cg_result.get("danger_zones", [])
            call_graph_affected_methods = cg_result.get("affected_methods", [])
            logger.info(
                "[v2] Step 0 CallGraph pre-injection: risk={} danger_zones={} affected={}",
                call_graph_risk_level,
                len(call_graph_danger_zones),
                len(call_graph_affected_methods),
            )
    except Exception as _cg_exc:
        logger.debug("[v2] Step 0 CallGraph pre-injection skipped (fail-open): {}", _cg_exc)

    user_message = state.get("user_message", "") or os.environ.get("CURRENT_USER_MESSAGE", "")

    # --- PRE-INJECTION C: KG-based deterministic routing (FR-3, ADR-3) ---
    kg_routing_result: Dict[str, Any] = {"status": "unresolved", "notes": "kg routing not attempted"}
    try:
        from ...routing.kg_router import route_task as _kg_route_task

        kg_routing_result = _kg_route_task(user_message)
        logger.info(
            "[v2] Step 0 KG routing pre-injection: status={} domain={} pattern={}",
            kg_routing_result.get("status"),
            kg_routing_result.get("domain"),
            kg_routing_result.get("pattern_id"),
        )
    except Exception as _kg_exc:
        logger.debug("[v2] Step 0 KG routing pre-injection skipped (fail-open): {}", _kg_exc)
        kg_routing_result = {"status": "unresolved", "notes": f"kg routing pre-injection failed: {_kg_exc}"}

    # --- PRE-INJECTION D: standards selection (FR-4, ADR-4) ---
    standards_selection_result: Dict[str, Any] = {}
    try:
        from ...standards.selector import select_standards as _select_standards

        _standards_project_root = state.get("project_root", ".")
        _standards_session_id = state.get("session_id") or os.environ.get("CURRENT_SESSION_ID", "") or "unknown-session"
        standards_selection_result = _select_standards(_standards_project_root, _standards_session_id)
        logger.info(
            "[v2] Step 0 standards selection pre-injection: project_type={} framework={} total_loaded={}",
            standards_selection_result.get("project_type"),
            standards_selection_result.get("framework"),
            standards_selection_result.get("total_loaded"),
        )
    except Exception as _std_exc:
        logger.debug("[v2] Step 0 standards selection pre-injection skipped (fail-open): {}", _std_exc)
        standards_selection_result = {}

    # --- PHASE 1: prompt_gen_expert_caller (assembles the prompt; no LLM call) ---
    # This line used to read STEP1_PROMPT_GEN_TIMEOUT (default 60) and apply it
    # below as "+ 15", composing a 75-second wall-clock abort on the Step 1
    # pipeline path against a claude CLI whose latency nothing here controls.
    # NFR-2 / ADR-016 replace it: unbounded unless an operator configures a
    # silence interval, which measures no-progress rather than duration.
    _pg_silence = _env_optional_seconds("STEP1_PROMPT_GEN_SILENCE")
    _call_graph_json = _json.dumps(
        {
            "risk_level": call_graph_risk_level,
            "danger_zones": call_graph_danger_zones,
            "affected_methods": call_graph_affected_methods,
        }
    )
    _kg_routing_json = _json.dumps(kg_routing_result)
    prompt_gen_args = [
        "--task-description",
        user_message,
        "--complexity-score",
        str(complexity_score),
        "--call-graph-json",
        _call_graph_json,
        "--kg-routing-json",
        _kg_routing_json,
    ]

    try:
        import importlib as _il

        _helpers_mod = _il.import_module("langgraph_engine.sdlc_pipeline.helpers")
        _call_execution_script = _helpers_mod.call_execution_script
    except ImportError:
        from ..helpers import call_execution_script as _call_execution_script  # noqa: PLC0415

    prompt_gen_raw = _call_execution_script(
        "prompt_gen_expert_caller",
        prompt_gen_args,
        model_tier="fast",
        silence_interval=_pg_silence,
    )

    _pg_status = prompt_gen_raw.get("status", "")
    if _pg_status == "ERROR":
        from ..architecture.prompt_gen_expert_caller import ERROR_KIND_TEMPLATE_LOAD_FAILED  # noqa: PLC0415

        _pg_error = prompt_gen_raw.get("error", "unknown")
        if prompt_gen_raw.get("error_kind") == ERROR_KIND_TEMPLATE_LOAD_FAILED:
            raise OrchestrationTemplateUnavailable(f"Step 1 cannot build an orchestration prompt: {_pg_error}")
        # On other ERRORs the caller's 'prompt' field is only a truncated copy of the
        # INPUT template, not a usable orchestration prompt, so fall back to the raw task.
        logger.error(f"[v2] Step 0 prompt_gen_expert_caller ERROR: {_pg_error} -- falling back to raw task")
        orchestration_prompt = user_message
    else:
        orchestration_prompt = prompt_gen_raw.get("llm_response", "") or prompt_gen_raw.get("prompt", "")
        if not orchestration_prompt:
            orchestration_prompt = user_message
            logger.warning("[v2] Step 0 prompt_gen_expert_caller returned no llm_response/prompt; using raw task")
        else:
            logger.info(
                f"[v2] Step 0 prompt_gen_expert_caller: orchestration_prompt length={len(orchestration_prompt)}"
            )

    # --- PHASE 2: emit the assembled prompt; the active session executes it ---
    # This phase used to decompose the prompt into a TODO list via todo_decomposer
    # and run each TODO through orchestrator_agent_caller, each a nested `claude -p`
    # subprocess. Both are gone. The master template's STEP 13 produces the
    # MULTI-AGENT PROMPT BUNDLE itself, so a separate decomposition call re-derived
    # what the template already specifies; and the pipeline is a subprocess of a
    # hook, so it cannot "run in the session" -- it can only hand the session
    # something to run. orchestrator_result now records what was emitted rather
    # than what was executed.
    # Phase 1 no longer runs an LLM, so what arrives here is the master orchestration
    # template plus its runtime-context header -- not a generated bundle. Describing it
    # as one would tell the reader the MULTI-AGENT PROMPT BUNDLE already exists when
    # producing it is still the work to be done.
    _full_prompt = (
        "You are orchestrator-agent. Below is the master orchestration template, preceded "
        "by an authoritative runtime-context header. Follow the template to produce the "
        "orchestration plan and its MULTI-AGENT PROMPT BUNDLE.\n\n"
        "--- BEGIN ORCHESTRATION TEMPLATE ---\n\n" + orchestration_prompt + "\n\n--- END ORCHESTRATION TEMPLATE ---"
    )

    # Structural check on what is about to be emitted. Both degraded paths above
    # already log -- an ERROR from prompt_gen, or an empty response -- so this is
    # not here to catch those. It is here for the case neither covers: a response
    # that is non-empty and therefore silent, but not a usable orchestration
    # prompt (a truncated template, the wrong file, a stub). Until now that was
    # indistinguishable from a good prompt.
    #
    # Warnings are recorded and logged, never fatal. The raw-task fallback is a
    # legitimate degraded path -- STEP1_CONTRACT documents it as such -- and it
    # trips both checks by design, so failing here would turn a recoverable run
    # into a dead one.
    from ...runtime_verification.schema_verifier import verify_orchestration_prompt  # noqa: PLC0415

    prompt_warnings = verify_orchestration_prompt(orchestration_prompt)

    orch_result: Dict[str, Any] = {
        "mode": "emitted",
        "success": True,
        "prompt_chars": len(_full_prompt),
        "template_source": "claude-global-library/ORCHESTRATION_TEMPLATE.md",
        "library_version": _library_version(),
        "prompt_warnings": prompt_warnings,
    }
    if prompt_warnings:
        logger.warning(
            "[v2] Step 1 emitted a structurally questionable orchestration prompt: {}",
            "; ".join(prompt_warnings),
        )
    logger.info(
        "[v2] Step 1 emitted orchestration prompt: {} chars, library v{}",
        orch_result["prompt_chars"],
        orch_result["library_version"],
    )

    # --- Build result from orchestrator output + migration fields ---
    result = _map_step1_result_to_state(state, orchestration_prompt, orch_result)

    # Store the injected context for observability
    result["step1_call_graph_risk_level"] = call_graph_risk_level
    result["step1_call_graph_danger_zones_count"] = len(call_graph_danger_zones)
    result["step1_call_graph_affected_methods_count"] = len(call_graph_affected_methods)
    result["step1_complexity_injected"] = complexity_score
    result["routing"] = kg_routing_result
    result["standards_selection"] = standards_selection_result
    result["standards_merged_rules"] = standards_selection_result.get("merged_rules", {})
    if "standards_count" not in state:
        result["standards_count"] = standards_selection_result.get("total_loaded", 0)
    result["orchestration_prompt"] = orchestration_prompt
    result["orchestrator_result"] = orch_result

    # Apply call graph complexity boost from orchestration_pre_analysis_node
    # (legacy boost path -- pre_analysis uses 1-10 scale boost on top of step1_complexity)
    try:
        graph_metrics = state.get("call_graph_metrics", {}) or {}
        boost = graph_metrics.get("complexity_boost", 0)
        if boost != 0 and graph_metrics.get("call_graph_available"):
            current = result.get("step1_complexity", 5)
            boosted = max(1, min(10, current + boost))
            if boosted != current:
                result["step1_complexity"] = boosted
                result["step1_complexity_boosted"] = True
                result["step1_complexity_boost_source"] = "call_graph"
                logger.info(
                    "[v2] Step 0 complexity adjusted by call graph: {} -> {} (boost={:+})",
                    current,
                    boosted,
                    boost,
                )
    except Exception as exc:
        logger.debug(f"[step0] call-graph complexity boost skipped: {exc}")

    return result


def _map_step1_result_to_state(
    state: FlowState,
    orchestration_prompt: str,
    orch_result: Dict[str, Any],
) -> Dict[str, Any]:
    """Map this node's emitted-prompt result to FlowState migration fields.

    Populates all fields that Steps 1, 3, 4, 5, 6, 7 previously wrote so that
    Steps 8-14 continue to receive the correct state keys regardless of which
    orchestration path produced the data.

    Args:
        state: Current pipeline state (read-only reference for fallback values).
        orchestration_prompt: The prompt text produced by prompt_gen_expert_caller.
        orch_result: The emission record this node builds -- mode, prompt_chars,
            template_source and library_version. It was once the parsed JSON
            returned by orchestrator_agent_caller, which no longer exists.

    Returns:
        A flat dict of state updates ready to merge into FlowState.
    """
    result: Dict[str, Any] = {}

    # Core Step 0 fields
    result["step1_task_type"] = orch_result.get("task_type", "General Task")
    _combined = state.get("combined_complexity_score", 0)
    _complexity_1to10 = max(1, min(10, round(_combined / 2.5))) if _combined else 5
    try:
        result["step1_complexity"] = max(1, min(10, int(orch_result.get("complexity", _complexity_1to10))))
    except (TypeError, ValueError):
        result["step1_complexity"] = _complexity_1to10
    result["step1_reasoning"] = orch_result.get("reasoning", "")
    raw_tasks = orch_result.get("tasks", {})
    result["step1_tasks"] = raw_tasks if isinstance(raw_tasks, dict) else {"count": 1, "tasks": []}
    result["step1_task_count"] = orch_result.get("task_count", 1)
    result["step1_error"] = orch_result.get("error") if not orch_result.get("success", True) else None

    # From Step 1: plan_required decision (always False -- Step 2 removed in v1.14.0)
    result.setdefault("step1_plan_required", False)

    # From Step 3: validated task list
    if isinstance(raw_tasks, dict):
        task_list = raw_tasks.get("tasks", [])
    else:
        task_list = []
    result.setdefault("step1_tasks_validated", task_list)

    # From Step 4: model selection
    result.setdefault("step1_model", orch_result.get("model_recommendation", "complex_reasoning"))

    # From Step 5: skill and agent selection
    result.setdefault("step1_skill", orch_result.get("selected_skill", ""))
    result.setdefault("step1_agent", orch_result.get("selected_agent", ""))
    result.setdefault("step1_skills", orch_result.get("skills", []))
    result.setdefault("step1_agents", orch_result.get("agents", []))
    result.setdefault("step1_skill_definition", orch_result.get("skill_definition", ""))
    result.setdefault("step1_agent_definition", orch_result.get("agent_definition", ""))

    # From Step 6: skill readiness (always True -- orchestrator already validated)
    result.setdefault("step1_skill_ready", True)
    result.setdefault("step1_agent_ready", True)
    result.setdefault("step1_validation_status", "OK")

    # From Step 7: execution prompt
    execution_prompt = orch_result.get("execution_prompt", "") or orchestration_prompt
    result.setdefault("step1_execution_prompt", execution_prompt)
    result.setdefault("step1_prompt_saved", bool(execution_prompt))

    # Write execution prompt to disk (what Step 7 used to do)
    try:
        session_dir = state.get("session_dir", "")
        if session_dir and execution_prompt:
            sp_file = Path(session_dir) / "system_prompt.txt"
            sp_file.parent.mkdir(parents=True, exist_ok=True)
            sp_file.write_text(execution_prompt, encoding="utf-8")
            result["step1_system_prompt_file"] = str(sp_file)
            result["step1_system_prompt_loaded"] = True
            logger.info("[v2] Step 0 wrote execution prompt to {}", sp_file)
    except Exception as _sp_exc:
        logger.debug("[v2] Step 0 prompt file write skipped: {}", _sp_exc)

    return result


# REMOVED: step1_plan_mode_decision_node -- collapsed into Step 0 template (v1.13.0)
# REMOVED: step1_plan_execution_node -- dead stub removed (v1.20.2 dead-code sweep)
# REMOVED: step1_task_breakdown_node -- collapsed into Step 0 template (v1.13.0)
# REMOVED: step1_toon_refinement_node -- collapsed into Step 0 template (v1.13.0)
#
# These functions are intentionally absent or stubbed. Their FlowState outputs are now
# populated by step1_task_analysis_node after the orchestration subprocess calls.

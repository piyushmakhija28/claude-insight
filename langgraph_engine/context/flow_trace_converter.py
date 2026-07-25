"""context/flow_trace_converter.py -- FlowState to flow-trace.json converter.

Moved from langgraph_engine/flow_trace_converter.py to the context/ domain package.
Backward-compat shim at the original location re-exports from here.

Marker scheme (Level/Step domain-driven rename):
    LEVEL_0_PREFLIGHT           - Level 0: Pre-Flight Sanity Guard
    LEVEL_1_SESSION/CONTEXT     - Level 1: Session & Context Synchronization (unchanged)
    SDLC_STEP_0 .. SDLC_STEP_8  - Level 2: SDLC Execution Core, Steps 0-8

LEGACY_MARKER_ALIASES below maps the old marker strings (LEVEL_MINUS_1,
LEVEL_3_STEP_0, ...) to their new equivalents so any downstream reader of
a pre-rename flow-trace.json (e.g. MCP tools that scan historical trace
files generically) can normalize old and new files the same way. No live
hook currently matches on these old markers -- pre_tool_enforcer's
policies only match LEVEL_1_* markers, which are unchanged by this rename.

Windows-safe: ASCII only (cp1252 compatible).
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from langgraph_engine.core.logger_factory import get_logger
from langgraph_engine.flow_state import FlowState

logger = get_logger(__name__)

try:
    import sys as _sys

    _sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))
    from utils.path_resolver import get_claude_home

    _FLOW_TRACE_MEMORY_DIR = get_claude_home() / "memory"
except ImportError:
    _FLOW_TRACE_MEMORY_DIR = Path.home() / ".claude" / "memory"


# Old marker -> new marker, for any consumer normalizing pre-rename flow-trace.json files.
LEGACY_MARKER_ALIASES: Dict[str, str] = {
    "LEVEL_MINUS_1": "LEVEL_0_PREFLIGHT",
    "LEVEL_2_STANDARDS": "STANDARDS",
    "LEVEL_3_STEP_0": "SDLC_STEP_1",
    "LEVEL_3_STEP_8": "SDLC_STEP_2",
    "LEVEL_3_STEP_9": "SDLC_STEP_3",
    "LEVEL_3_STEP_10": "SDLC_STEP_4",
    "LEVEL_3_STEP_11": "SDLC_STEP_5",
    "LEVEL_3_STEP_12": "SDLC_STEP_6",
    "LEVEL_3_STEP_13": "SDLC_STEP_7",
    "LEVEL_3_STEP_14": "SDLC_STEP_8",
}


def normalize_legacy_marker(marker: str) -> str:
    """Map a pre-rename flow-trace 'step' marker to its current equivalent.

    Returns the marker unchanged if it is already current or unrecognized.
    """
    return LEGACY_MARKER_ALIASES.get(marker, marker)


def convert_flow_state_to_trace(state: FlowState) -> Dict[str, Any]:
    """Convert FlowState to flow-trace.json format.

    Maps all FlowState fields to pipeline entries compatible with
    pre-tool-enforcer.py and other downstream consumers.

    Args:
        state: Completed FlowState from LangGraph execution.

    Returns:
        Dict in flow-trace.json format.
    """
    timestamp = state.get("timestamp", datetime.now().isoformat())
    session_id = state.get("session_id", "SESSION-UNKNOWN")

    pipeline = []

    if state.get("preflight_status"):
        pipeline.append(
            {
                "step": "LEVEL_0_PREFLIGHT",
                "name": "Pre-Flight Sanity Guard",
                "level": 0,
                "order": 0,
                "is_blocking": True,
                "timestamp": timestamp,
                "duration_ms": state.get("level_durations", {}).get("preflight_guard", 0),
                "input": {
                    "trigger": "user_prompt_received",
                    "purpose": "Verify ALL systems operational before any work",
                    "is_blocking": True,
                },
                "policy_output": {
                    "status": state.get("preflight_status"),
                    "unicode_check": state.get("unicode_check", False),
                    "encoding_check": state.get("encoding_check", False),
                    "windows_path_check": state.get("windows_path_check", False),
                },
                "decision": "Auto-fix checks completed - {}".format(state.get("preflight_status")),
                "passed_to_next": {
                    "status": state.get("preflight_status"),
                },
            }
        )

    if state.get("level1_status"):
        pipeline.append(
            {
                "step": "LEVEL_1_SESSION",
                "name": "Session Init (Level 1)",
                "level": 1,
                "order": 1,
                "is_blocking": False,
                "timestamp": timestamp,
                "duration_ms": state.get("level_durations", {}).get("level1_session", 0),
                "input": {
                    "purpose": "Create session and initialize session directory",
                },
                "policy_output": {
                    "session_id": session_id,
                    "session_created": True,
                },
                "decision": "Session created - {}".format(session_id),
                "passed_to_next": {
                    "session_id": session_id,
                },
            }
        )
        pipeline.append(
            {
                "step": "LEVEL_1_CONTEXT",
                "name": "Context Sync (Level 1 Parallel)",
                "level": 1,
                "order": 2,
                "is_blocking": False,
                "timestamp": timestamp,
                "duration_ms": state.get("level_durations", {}).get("level1", 0),
                "input": {
                    "purpose": "Load context and calculate complexity",
                },
                "policy_output": {
                    "context_loaded": state.get("context_loaded", False),
                    "context_percentage": state.get("context_percentage", 0),
                    "complexity_score": state.get("complexity_score", 0),
                },
                "decision": "Level 1 completed - {}".format(state.get("level1_status")),
                "passed_to_next": {
                    "context_pct": state.get("context_percentage", 0),
                    "context_threshold_exceeded": state.get("context_threshold_exceeded", False),
                },
            }
        )

    # NOTE: no numbered "Level 2: Standards" trace entry -- that concept was
    # retired (it never had pipeline nodes; state["level2_status"] was never
    # assigned a real value anywhere). Standards loading is an always-on,
    # disk-loaded mechanism, not a pipeline phase, so it has no trace step.

    sdlc_steps = [
        (
            1,
            "Task Orchestration & Planning",
            "step1_task_type",
            {
                "task_type": state.get("step1_task_type"),
                "complexity": state.get("step1_complexity"),
                "reasoning": state.get("step1_reasoning"),
                "task_count": state.get("step1_task_count"),
            },
        ),
        (
            2,
            "Issue Tracking",
            "step2_status",
            {
                "issue_id": state.get("step2_issue_id"),
                "issue_created": state.get("step2_issue_created"),
                "status": state.get("step2_status"),
            },
        ),
        (
            3,
            "Branch & Workspace Setup",
            "step3_status",
            {
                "branch_name": state.get("step3_branch_name"),
                "branch_created": state.get("step3_branch_created"),
                "status": state.get("step3_status"),
            },
        ),
        (
            4,
            "Implementation & Code Generation",
            "step4_status",
            {
                "implementation_status": state.get("step4_implementation_status"),
                "tasks_executed": state.get("step4_tasks_executed"),
                "modified_files": state.get("step4_modified_files"),
            },
        ),
        (
            5,
            "Pull Request & Automated Review",
            "step5_status",
            {
                "review_passed": state.get("step5_review_passed"),
                "retry_count": state.get("step5_retry_count"),
                "status": state.get("step5_status"),
            },
        ),
        (
            6,
            "Issue & Ticket Closure",
            "step6_status",
            {
                "issue_closed": state.get("step6_issue_closed"),
                "status": state.get("step6_status"),
            },
        ),
        (
            7,
            "Documentation & UML Generation",
            "step7_documentation_status",
            {
                "updates_prepared": state.get("step7_updates_prepared"),
                "status": state.get("step7_documentation_status"),
            },
        ),
        (
            8,
            "Final Telemetry & Summary Report",
            "step8_status",
            {
                "status": state.get("step8_status"),
                "summary": state.get("step8_summary"),
            },
        ),
    ]

    for step_num, step_name, state_key, step_output in sdlc_steps:
        pipeline.append(
            {
                "step": "SDLC_STEP_%d" % step_num,
                "name": step_name,
                "level": 2,
                "order": 3 + step_num,
                "is_blocking": False,
                "timestamp": timestamp,
                "duration_ms": state.get("level_durations", {}).get(state_key, 0),
                "input": {},
                "policy_output": step_output,
                "decision": "Step {} - {}".format(step_num, step_name),
                "passed_to_next": {},
            }
        )

    trace = {
        "meta": {
            "flow_version": "7.5.0-langgraph",
            "script": "3-level-flow.py (LangGraph Engine)",
            "mode": "langgraph-orchestration",
            "flow_start": state.get("timestamp"),
            "flow_end": datetime.now().isoformat(),
            "duration_seconds": state.get("execution_time_ms", 0) / 1000,
            "session_id": session_id,
            "engine": "LangGraph",
        },
        "user_input": {
            "prompt": "[Generated by LangGraph flow]",
            "received_at": timestamp,
            "source": "LangGraph Engine",
        },
        "pipeline": pipeline,
        "final_decision": {
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id,
            "task_type": state.get("step1_task_type", "General Task"),
            "complexity": state.get("step1_complexity", 5),
            "context_pct": state.get("context_percentage", 0),
            "standards_active": state.get("standards_count", 0),
            "model_selected": state.get("step1_model", "haiku"),
            "plan_required": False,
            "issue_id": state.get("step2_issue_id", ""),
            "branch_name": state.get("step3_branch_name", ""),
            "proceed": state.get("final_status") != "BLOCKED",
            "summary": "Status={} Context={:.1f}%".format(
                state.get("final_status"),
                (state.get("context_percentage") or 0),
            ),
        },
        "work_started": state.get("final_status") != "BLOCKED",
        "status": state.get("final_status", "UNKNOWN"),
        "synthesis": {
            "synthesized_prompt": state.get("synthesized_prompt", ""),
            "synthesis_metadata": state.get("synthesis_metadata", {}),
            "context_optimization": {
                "workflow_memory_size_kb": state.get("workflow_memory_size_kb", 0),
                "step_optimization_stats": state.get("step_optimization_stats", {}),
            },
        },
    }

    return trace


def write_flow_trace_json(state: FlowState, session_dir: Optional[Path] = None) -> Path:
    """Write flow-trace.json file from FlowState.

    Args:
        state:       Completed FlowState.
        session_dir: Directory to write flow-trace.json to.
                     Defaults to ~/.claude/memory/logs/sessions/{session_id}/

    Returns:
        Path: Path to written file.
    """
    if session_dir is None:
        session_id = state.get("session_id", "SESSION-UNKNOWN")
        session_dir = _FLOW_TRACE_MEMORY_DIR / "logs" / "sessions" / session_id

    session_dir.mkdir(parents=True, exist_ok=True)

    trace = convert_flow_state_to_trace(state)
    trace_file = session_dir / "flow-trace.json"

    trace_file.write_text(
        json.dumps(trace, indent=2),
        encoding="utf-8",
    )

    return trace_file


def print_flow_checkpoint(state: FlowState, verbose: bool = False) -> None:
    """Print flow checkpoint summary with synthesized prompt integration.

    Args:
        state:   Completed FlowState.
        verbose: If True, print full error and warning details.
    """
    status = state.get("final_status", "UNKNOWN")
    session_id = state.get("session_id", "SESSION-UNKNOWN")
    context_pct = state.get("context_percentage", 0)
    model = state.get("step1_model", "complex_reasoning")
    synthesized_prompt = state.get("synthesized_prompt", "")

    print("\n[FLOW CHECKPOINT]")
    print("  Status: {}".format(status))
    print("  Session: {}".format(session_id))
    print("  Context: {:.1f}%".format(context_pct))
    print("  Model: {}".format(model))

    if synthesized_prompt:
        try:
            synthesis_file = _FLOW_TRACE_MEMORY_DIR / "current-synthesis.txt"
            synthesis_file.parent.mkdir(parents=True, exist_ok=True)
            synthesis_file.write_text(synthesized_prompt, encoding="utf-8")
            print("  Synthesis: Generated ({} chars)".format(len(synthesized_prompt)))
            print("  Location: {}".format(synthesis_file))
        except OSError as exc:
            logger.debug(f"[flow_trace] synthesis file write skipped: {exc}")

        print("\n--- SYNTHESIZED CONTEXT (from 3-level pipeline) ---")
        print(synthesized_prompt)
        print("--- END SYNTHESIZED CONTEXT ---\n")

    orchestrator_result = state.get("orchestrator_result", "")
    if orchestrator_result:
        print("  Orchestrator: result available ({} chars)".format(len(str(orchestrator_result))))

    if verbose:
        if state.get("errors"):
            print("  Errors ({}): {}".format(len(state["errors"]), state["errors"][:2]))
        if state.get("warnings"):
            print("  Warnings ({}): {}".format(len(state["warnings"]), state["warnings"][:2]))

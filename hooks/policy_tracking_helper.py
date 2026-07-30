#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Policy Tracking Helper - Simplified interface for policies to record execution

This helper provides easy-to-use functions that policies can call to record
their execution details. It abstracts away PolicyTracker complexity and ensures
consistent data format across all policies.

Version: 1.0.0
Last Modified: 2026-03-05
Windows-Safe: No Unicode chars (ASCII only, cp1252 compatible)
"""

import json
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

try:
    from session_context import append_jsonl, get_sessions_root, locked_json_update
    from session_context import resolve_session_id as _resolve_session_id
except ImportError:  # pragma: no cover - path bootstrap for direct script runs
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from session_context import append_jsonl, get_sessions_root, locked_json_update
    from session_context import resolve_session_id as _resolve_session_id

# Cap on retained detail records in flow-trace.json's all_policies_executed /
# decisions_timeline lists. The file is fully read + rewritten on every
# policy-tracked tool call, so leaving these unbounded turns every call
# progressively slower across a long session (real sessions observed at
# 1.4MB / tens of thousands of records). See record_policy_execution().
_MAX_RETAINED_POLICY_RECORDS = 200

# Session IDs that mean "resolution failed" rather than naming a real session.
# Writing traces under these fabricates a directory that looks like a session
# and silently collects records from every unresolved hook invocation. They are
# routed to a clearly non-session folder instead.
_UNRESOLVED_SESSION_IDS = {"", "unknown", "SESSION-unknown", "none", "None"}
_UNRESOLVED_DIRNAME = "_unresolved"

# Windows-safe encoding
if sys.platform == "win32":
    import io

    try:
        if getattr(sys.stdout, "encoding", "utf-8") != "utf-8":
            try:
                sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            except (AttributeError, io.UnsupportedOperation):
                if hasattr(sys.stdout, "buffer"):
                    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        if getattr(sys.stderr, "encoding", "utf-8") != "utf-8":
            try:
                sys.stderr.reconfigure(encoding="utf-8", errors="replace")
            except (AttributeError, io.UnsupportedOperation):
                if hasattr(sys.stderr, "buffer"):
                    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    except Exception:
        pass  # Never crash on encoding setup


def _session_dirname(session_id: str) -> str:
    """Return the directory name to store a trace under.

    Args:
        session_id (str): Session ID as supplied by the caller.

    Returns:
        str: The canonical session ID, or the shared ``_unresolved`` folder name
            when the caller could not determine a session.
    """
    if not session_id or str(session_id).strip() in _UNRESOLVED_SESSION_IDS:
        return _UNRESOLVED_DIRNAME
    return str(session_id).strip()


def get_session_id():
    """Get the active session ID.

    Delegates to :func:`session_context.resolve_session_id`, which reads the
    session bound from the current hook's stdin payload before falling back to
    the pointer and progress files. The "unknown" default is preserved for
    callers that log an identifier unconditionally.

    Returns:
        str: Session ID (e.g. SESSION-20260307-131645-8F7H) or "unknown".
    """
    return _resolve_session_id(default="unknown")


def record_policy_execution(
    session_id: str,
    policy_name: str,
    policy_script: str,
    policy_type: str,
    input_params: Dict[str, Any],
    output_results: Dict[str, Any],
    decision: str,
    duration_ms: int,
    sub_operations: Optional[List[Dict]] = None,
) -> bool:
    """
    Record a policy execution to flow-trace.json.

    This is the main function policies should call to record their execution.
    It handles all the complexity of appending to flow-trace.json.

    Args:
        session_id (str): Session ID (SESSION-...)
        policy_name (str): Policy name (e.g., 'session-id-generator')
        policy_script (str): Script filename (e.g., 'session-id-generator.py')
        policy_type (str): Type (e.g., 'Utility Hook', 'Policy Script')
        input_params (dict): Input parameters to policy
        output_results (dict): Output results from policy
        decision (str): Decision text (what the policy decided)
        duration_ms (int): How long policy took to execute
        sub_operations (list, optional): List of sub-operations

    Returns:
        bool: True when the record reached the durable append-only
            ``flow-trace.jsonl`` stream. The ``flow-trace.json`` aggregate is
            updated on a best-effort basis and is skipped rather than raced when
            its lock is contended, so it is not what success is measured on.

    Example:
        >>> record_policy_execution(
        ...     session_id="SESSION-20260305-180752-DR8R",
        ...     policy_name="session-id-generator",
        ...     policy_script="session-id-generator.py",
        ...     policy_type="Utility Hook",
        ...     input_params={"mode": "auto", "pid": 12345},
        ...     output_results={"session_id": "SESSION-...", "is_new": True},
        ...     decision="Created new session",
        ...     duration_ms=45
        ... )
    """
    try:
        session_dir = get_sessions_root() / _session_dirname(session_id)
        flow_trace_file = session_dir / "flow-trace.json"
        session_dir.mkdir(parents=True, exist_ok=True)

        policy_record = {
            "policy_name": policy_name,
            "policy_script": policy_script,
            "policy_type": policy_type,
            "timestamp": datetime.now().isoformat(),
            "duration_ms": duration_ms,
            "input": input_params,
            "output": output_results,
            "decision": decision,
        }

        if sub_operations:
            policy_record["sub_operations"] = sub_operations

        # The JSONL stream is the durable record: a single O_APPEND write cannot
        # interleave, whereas the aggregate below is a read-modify-write that is
        # deliberately skipped when the lock is contended. Success is therefore
        # reported on the append, not on the aggregate.
        appended = append_jsonl(session_dir / "flow-trace.jsonl", policy_record)

        def _apply(flow_trace):
            """Merge one policy record into the flow-trace aggregate.

            Runs inside the cross-process lock held by locked_json_update, so
            concurrent pre-tool / post-tool / stop hooks serialize here instead
            of interleaving their rewrites.
            """
            if not isinstance(flow_trace, dict):
                flow_trace = _create_empty_flow_trace(session_id)

            policies = flow_trace.setdefault("all_policies_executed", [])
            policies.append(policy_record)

            summary = flow_trace.setdefault("execution_summary", {})
            summary["total_policies_executed"] = summary.get("total_policies_executed", 0) + 1

            if len(policies) > _MAX_RETAINED_POLICY_RECORDS:
                flow_trace["all_policies_executed"] = policies[-_MAX_RETAINED_POLICY_RECORDS:]

            timeline = flow_trace.setdefault("decisions_timeline", [])
            timeline.append({"timestamp": policy_record["timestamp"], "policy": policy_name, "decision": decision})
            if len(timeline) > _MAX_RETAINED_POLICY_RECORDS:
                flow_trace["decisions_timeline"] = timeline[-_MAX_RETAINED_POLICY_RECORDS:]

            return flow_trace

        locked_json_update(
            flow_trace_file,
            _apply,
            default=_create_empty_flow_trace(session_id),
        )

        return appended

    except Exception as e:
        print(f"[ERROR] Failed to record policy execution: {e}")
        return False


def record_sub_operation(
    session_id: str,
    policy_name: str,
    operation_name: str,
    input_params: Dict[str, Any],
    output_results: Dict[str, Any],
    duration_ms: int,
) -> Dict[str, Any]:
    """
    Create a sub-operation record for inclusion in a policy execution.

    Sub-operations are operations within a single policy that should be
    tracked individually (e.g., different checks in auto-fix-enforcer).

    Args:
        session_id (str): Session ID
        policy_name (str): Parent policy name
        operation_name (str): Operation name
        input_params (dict): Operation input
        output_results (dict): Operation output
        duration_ms (int): Operation duration

    Returns:
        dict: Sub-operation record

    Example:
        >>> sub_op = record_sub_operation(
        ...     session_id="SESSION-...",
        ...     policy_name="auto-fix-enforcer",
        ...     operation_name="check_python_available",
        ...     input_params={"required": "3.8+"},
        ...     output_results={"found": True, "version": "3.9"},
        ...     duration_ms=20
        ... )
        >>> # Now include sub_op in policy record when calling record_policy_execution
    """
    return {
        "operation": operation_name,
        "timestamp": datetime.now().isoformat(),
        "duration_ms": duration_ms,
        "input": input_params,
        "output": output_results,
    }


def _create_empty_flow_trace(session_id: str) -> Dict[str, Any]:
    """
    Create an empty flow-trace.json structure.

    Args:
        session_id (str): Session ID

    Returns:
        dict: Empty flow-trace structure
    """
    return {
        "meta": {"session_id": session_id, "created_at": datetime.now().isoformat(), "schema_version": "1.0"},
        "user_input": {},
        "all_policies_executed": [],
        "execution_summary": {"total_policies_executed": 0},
        "decisions_timeline": [],
    }


def get_flow_trace_summary(session_id: str) -> Optional[Dict[str, Any]]:
    """
    Get summary statistics from a session's flow-trace.

    Args:
        session_id (str): Session ID

    Returns:
        dict: Summary with counts, slowest/fastest policies, decisions
    """
    try:
        session_dir = get_sessions_root() / _session_dirname(session_id)
        flow_trace_file = session_dir / "flow-trace.json"

        if not flow_trace_file.exists():
            return None

        flow_trace = json.loads(flow_trace_file.read_text(encoding="utf-8"))

        policies = flow_trace.get("all_policies_executed", [])

        # Find slowest and fastest
        sorted_by_speed = sorted(policies, key=lambda p: p.get("duration_ms", 0))

        summary = {
            "total_policies": len(policies),
            "total_duration_ms": sum(p.get("duration_ms", 0) for p in policies),
            "slowest_policy": sorted_by_speed[-1] if sorted_by_speed else None,
            "fastest_policy": sorted_by_speed[0] if sorted_by_speed else None,
            "average_duration_ms": (sum(p.get("duration_ms", 0) for p in policies) / len(policies) if policies else 0),
            "decisions_count": len(flow_trace.get("decisions_timeline", [])),
        }

        return summary

    except Exception as e:
        print(f"[ERROR] Failed to get flow-trace summary: {e}")
        return None


if __name__ == "__main__":
    print("[OK] Policy Tracking Helper loaded successfully")

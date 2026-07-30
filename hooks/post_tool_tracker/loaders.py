"""
post_tool_tracker/loaders.py - Shared data loading helpers.

Provides cached flow-trace context loading and raw flow-trace loading
so all modules read from the same source without re-parsing files.
"""

import json
import os
import sys
from pathlib import Path

_pt_dir = os.path.dirname(os.path.abspath(__file__))
_hooks_dir = str(Path(_pt_dir).parent)
if _hooks_dir not in sys.path:
    sys.path.insert(0, _hooks_dir)

from session_context import get_sessions_root  # noqa: E402
from session_context import normalize_session_id as _normalize_session_id  # noqa: E402
from session_context import resolve_session_id as _resolve_session_id  # noqa: E402

# ---------------------------------------------------------------------------
# Session ID helper (shared dependency - defined here, imported by other mods)
# ---------------------------------------------------------------------------


def _get_session_id_from_progress(session_state_file=None, flag_dir=None):
    """Get the current session ID.

    Delegates to :func:`session_context.resolve_session_id`, which prefers the
    session bound from this hook's stdin payload over any file on disk. The
    ``session_state_file`` argument is still honored as a last resort for
    sessions whose progress file predates per-session scoping.

    Args:
        session_state_file: Path to a progress file used as a final fallback.
        flag_dir: Unused, kept for signature compatibility.

    Returns:
        str: Active session ID (e.g. "SESSION-20260307-115241-GQQQ"), or
             empty string when no valid session ID can be found.
    """
    sid = _resolve_session_id()
    if sid:
        return sid

    if session_state_file is not None:
        try:
            sf = Path(session_state_file)
            if sf.exists():
                with open(sf, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return _normalize_session_id(data.get("session_id", ""))
        except Exception:
            pass
    return ""


# ---------------------------------------------------------------------------
# Flow-trace loader (module-level cache, reset per process invocation)
# ---------------------------------------------------------------------------

_flow_trace_cache = None


def _load_flow_trace_context(session_state_file=None):
    """
    Load flow-trace.json from the current session to chain context from 3-level-flow.
    Returns dict with task_type, complexity, model, skill.
    Cached per invocation (module-level).

    Context chain: 3-level-flow.py -> flow-trace.json -> post-tool-tracker
    This enables:
    - Enriching tool-tracker.jsonl entries with task context
    - Better progress estimation weighted by complexity
    - Task-aware git commit messages

    Args:
        session_state_file: Path to SESSION_STATE_FILE for session ID lookup.

    Returns:
        dict: Keys task_type, complexity, model, skill.  Empty dict on failure.
    """
    global _flow_trace_cache
    if _flow_trace_cache is not None:
        return _flow_trace_cache

    _flow_trace_cache = {}
    try:
        session_id = _get_session_id_from_progress(session_state_file)
        if not session_id:
            return _flow_trace_cache

        trace_file = get_sessions_root() / session_id / "flow-trace.json"
        if trace_file.exists():
            with open(trace_file, "r", encoding="utf-8") as f:
                raw = json.load(f)
            # v4.4.0+: array of traces - use latest entry
            if isinstance(raw, list) and raw:
                data = raw[-1]
            elif isinstance(raw, dict):
                data = raw
            else:
                data = {}
            final_decision = data.get("final_decision", {})
            _flow_trace_cache = {
                "task_type": final_decision.get("task_type", ""),
                "complexity": final_decision.get("complexity", 0),
                "model": final_decision.get("model_selected", ""),
                "skill": final_decision.get("skill_or_agent", ""),
            }
    except Exception:
        pass
    return _flow_trace_cache


def _load_raw_flow_trace(session_state_file=None):
    """
    Load and return the raw flow-trace.json dict for the current session.

    Returns the latest entry if the file contains a list, or the dict
    directly.  Returns an empty dict on any failure.

    Args:
        session_state_file: Path to SESSION_STATE_FILE for session ID lookup.

    Returns:
        dict: Raw flow-trace data or empty dict.
    """
    try:
        session_id = _get_session_id_from_progress(session_state_file)
        if not session_id:
            return {}
        trace_file = get_sessions_root() / session_id / "flow-trace.json"
        if not trace_file.exists():
            return {}
        with open(trace_file, "r", encoding="utf-8") as f:
            raw = json.load(f)
        if isinstance(raw, list) and raw:
            return raw[-1]
        if isinstance(raw, dict):
            return raw
    except Exception:
        pass
    return {}

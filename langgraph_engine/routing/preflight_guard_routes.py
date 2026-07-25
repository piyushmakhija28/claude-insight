"""Level 0 (Pre-Flight Sanity Guard) routing functions - Auto-fix enforcement conditional edges.

Extracted from orchestrator.py. Controls flow through Level 0 (Pre-Flight Sanity Guard) checks
and the user choice / retry loop.
"""

from typing import Literal

from langgraph_engine.runtime_verification.verifier import RuntimeVerifier

from ..flow_state import FlowState, StepKeys

# Must match MAX_PREFLIGHT_ATTEMPTS in subgraphs/preflight_guard.py
_MAX_PREFLIGHT_ATTEMPTS = 3


def route_after_preflight_guard(state: FlowState) -> Literal["ask_preflight_guard_fix", "level1_session"]:
    """Route based on Level 0 (Pre-Flight Sanity Guard) status.

    - If OK: go to Level 1 session loader (level1_session)
    - If FAILED: ask user for recovery (ask_preflight_guard_fix)
    """
    _rv = RuntimeVerifier.get_instance()
    _rv_violations = _rv.check_level_transition("preflight_guard", "level1", state)
    if _rv_violations:
        import logging as _logging

        _logging.getLogger(__name__).warning(
            "[RuntimeVerifier] transition guard violations on preflight_guard->level1: %s",
            _rv_violations,
        )

    status = state.get(StepKeys.PREFLIGHT_STATUS, "FAILED")
    if status == "OK":
        return "level1_session"
    else:
        return "ask_preflight_guard_fix"


def route_after_preflight_guard_user_choice(state: FlowState) -> Literal["fix_preflight_guard", "level1_session"]:
    """Route based on user choice for Level 0 (Pre-Flight Sanity Guard) failures.

    - 'auto-fix': Attempt fixes and retry Level 0 (Pre-Flight Sanity Guard)
    - 'skip': Continue to Level 1 (session_loader) anyway
    - default: Skip (user will fix manually)
    """
    _rv = RuntimeVerifier.get_instance()
    _rv_violations = _rv.check_level_transition("preflight_guard", "level1", state)
    if _rv_violations:
        import logging as _logging

        _logging.getLogger(__name__).warning(
            "[RuntimeVerifier] transition guard violations on preflight_guard->level1: %s",
            _rv_violations,
        )

    choice = state.get(StepKeys.PREFLIGHT_USER_CHOICE, "skip")

    if choice == "auto-fix":
        # Check retry count to prevent infinite loops (max 3 attempts: counts 0,1,2 allowed)
        retry_count = state.get(StepKeys.PREFLIGHT_RETRY_COUNT, 0)
        if retry_count < _MAX_PREFLIGHT_ATTEMPTS:
            return "fix_preflight_guard"
        # Max attempts reached: ask node set choice="force_continue"; fall through below

    # "force_continue": max-attempts path (ask node sets this when retry_count >= 3)
    # "skip": user explicitly chose to proceed without fixing
    # default/unknown: continue safely to Level 1
    return "level1_session"

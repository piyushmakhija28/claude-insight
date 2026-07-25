"""Level 2 (SDLC Execution Core) routing functions - Execution pipeline conditional edges.

Extracted from orchestrator.py. Controls routing within Level 2 steps:
- Step 5 (Pull Request & Automated Review): pass/retry conditional loop

CHANGE LOG (v1.13.0):
  route_after_step1_decision removed -- Step 1 (pre-v1.13.0 numbering) no
  longer exists in the graph. Deprecated stub kept for backward-compat
  test imports.

CHANGE LOG (Level/Step domain-driven rename):
  The deprecated route_after_step1_decision stub was deleted outright --
  nothing imports it and the "Step 1" it referenced predates the current
  numbering entirely.
"""

from typing import Literal

from ..flow_state import FlowState, StepKeys


def route_after_step5_review(state: FlowState) -> Literal["sdlc_step6_issue_closure", "sdlc_step5_retry"]:
    """Conditional routing after PR review: if failed and retries < 3, retry; else continue to closure."""
    review_passed = state.get(StepKeys.REVIEW_PASSED, False)
    retry_count = state.get(StepKeys.RETRY_COUNT, 0)

    if review_passed or retry_count >= 3:
        return "sdlc_step6_issue_closure"
    else:
        # Route to retry node (which will increment count via proper state return)
        return "sdlc_step5_retry"

"""Level-transition invariant guards.

LEVEL_TRANSITION_GUARDS maps (from_level, to_level) to the PreconditionSpecs that
must hold on the state before the pipeline crosses that boundary. get_transition_guard()
looks up the specs for a given transition.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

from langgraph_engine.runtime_verification.contracts import PreconditionSpec

# Level transition guards: keyed by (from_level, to_level)
# For str expected_type: min_val = minimum string length
# IMPORTANT: combined_complexity_score is 1-25 scale (NOT 1-10)
LEVEL_TRANSITION_GUARDS: Dict[Tuple[str, str], List[PreconditionSpec]] = {
    ("preflight_guard", "level1"): [
        PreconditionSpec(
            key="auto_fix_complete",
            expected_type=bool,
            required=True,
        ),
    ],
    ("level1", "level3"): [
        PreconditionSpec(
            key="combined_complexity_score",
            expected_type=(int, float),
            required=True,
            min_val=1,
            max_val=25,  # 1-25 scale: simple*0.3 + graph*0.7
        ),
        PreconditionSpec(
            key="session_synced",
            expected_type=bool,
            required=True,
        ),
    ],
    ("pre_analysis", "step0"): [
        PreconditionSpec(
            key="pre_analysis_result",
            expected_type=dict,
            required=True,
        ),
        PreconditionSpec(
            key="call_graph_metrics",
            expected_type=dict,
            required=True,
        ),
    ],
    ("step0", "step8"): [
        PreconditionSpec(
            key="orchestration_prompt",
            expected_type=str,
            required=True,
            min_val=200,  # min length for str
        ),
        # orchestrator_result has always been written as a dict by
        # step1_task_analysis_node, never a string. This guard asked for a str of
        # at least 50 characters and would have rejected every real run; it never
        # fired only because ENABLE_RUNTIME_VERIFICATION defaults to 0, so the
        # whole guard set is dormant. node_contracts.py described the same key
        # correctly as a dict, so the two disagreed with each other as well.
        # Corrected 2026-08-07 to match what the node actually produces.
        PreconditionSpec(
            key="orchestrator_result",
            expected_type=dict,
            required=True,
        ),
    ],
}


def get_transition_guard(from_level: str, to_level: str) -> List[PreconditionSpec]:
    """Return the list of PreconditionSpec for the given level transition, or [] if not guarded."""
    return LEVEL_TRANSITION_GUARDS.get((from_level, to_level), [])

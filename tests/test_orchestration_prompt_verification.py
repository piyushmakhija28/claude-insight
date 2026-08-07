"""Step 1 must actually run verify_orchestration_prompt on what it emits.

The function was written, exported and unit-tested, and then called by nothing.
Its sibling verify_orchestrator_result was deleted for that reason plus a false
premise; this one encodes a true contract, so it was wired in instead.

A wire-in needs a test that would notice the wire coming loose, otherwise it
recreates the original problem in a new place -- a validator that exists, passes
its own unit tests, and never sees production data. So every assertion here goes
through step1_task_analysis_node rather than calling the verifier directly:
tests/test_schema_verifier.py already covers the function in isolation, and that
coverage is exactly what failed to notice it had no callers.

The two cases are a pair on purpose. A test that only asserts "a good prompt
produces no warnings" passes just as well when the verifier is never invoked,
because an unwired check and a satisfied check both produce an empty list.
"""

import sys
from pathlib import Path
from unittest.mock import patch

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# Long enough to clear the 200-char floor and carrying the "Phase" keyword the
# verifier looks for, so it stands in for a real master template.
WELL_FORMED_PROMPT = "Phase A -- foundation. " + ("orchestration detail. " * 40)

# Non-empty, so neither degraded path in the node fires and nothing else logs:
# this is the case the wire-in exists for.
MALFORMED_PROMPT = "do the thing"


def _script_mock(prompt_text):
    """Return a call_execution_script stand-in yielding the given prompt."""

    def _side_effect(script_name, args=None, model_tier=None, silence_interval=None):
        if script_name == "prompt_gen_expert_caller":
            return {"status": "SUCCESS", "llm_response": prompt_text, "prompt": "raw"}
        return {"status": "SUCCESS"}

    return _side_effect


def _run_node(prompt_text):
    """Drive step1_task_analysis_node with a mocked prompt-gen response."""
    from langgraph_engine.sdlc_pipeline.nodes.task_orchestration import step1_task_analysis_node

    state = {"user_message": "Add a new endpoint", "project_root": str(_PROJECT_ROOT)}
    with patch(
        "langgraph_engine.sdlc_pipeline.helpers.call_execution_script",
        side_effect=_script_mock(prompt_text),
    ):
        return step1_task_analysis_node(state)


class TestTheVerifierRunsOnWhatIsEmitted:
    """The check must reach the emitted prompt, not merely exist."""

    def test_a_well_formed_prompt_records_no_warnings(self):
        result = _run_node(WELL_FORMED_PROMPT)
        orch = result["orchestrator_result"]
        assert "prompt_warnings" in orch, "the verifier result must reach orchestrator_result"
        assert orch["prompt_warnings"] == []

    def test_a_malformed_prompt_records_warnings(self):
        """The half that fails if the verifier is never called.

        A non-empty but unusable prompt is the case neither degraded path in the
        node covers -- prompt_gen returned something, so nothing else logs. If
        this list came back empty the check would be unwired, and the pass case
        above could not tell the difference.
        """
        result = _run_node(MALFORMED_PROMPT)
        warnings = result["orchestrator_result"]["prompt_warnings"]
        assert warnings, "a 12-character prompt with no 'Phase' keyword must be reported"
        joined = " ".join(warnings).lower()
        assert "short" in joined or "200" in joined
        assert "phase" in joined


class TestWarningsAreNotFatal:
    """A questionable prompt is reported, not turned into a failed run."""

    def test_the_step_still_emits_and_reports_success(self):
        """The raw-task fallback trips both checks by design.

        STEP1_CONTRACT documents a short raw task as a legitimate degraded path,
        so a verifier that failed the step would convert every recoverable run
        into a dead one.
        """
        result = _run_node(MALFORMED_PROMPT)
        orch = result["orchestrator_result"]
        assert orch["prompt_warnings"]
        assert orch["success"] is True
        assert orch["mode"] == "emitted"
        assert result["orchestration_prompt"] == MALFORMED_PROMPT

    def test_prompt_chars_still_counts_the_full_emitted_prompt(self):
        """Guards against the wire-in being placed where it truncates the result."""
        result = _run_node(WELL_FORMED_PROMPT)
        assert result["orchestrator_result"]["prompt_chars"] > len(WELL_FORMED_PROMPT)

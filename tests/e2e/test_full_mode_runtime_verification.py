"""E2E tests: ENABLE_RUNTIME_VERIFICATION=1 in full mode (CLAUDE_HOOK_MODE=0).

Validates that:
  - Verifier singleton is reused across multiple node calls in full mode
  - ORCHESTRATOR_CONTRACT precondition enforces orchestration_prompt min_length=200
  - Strict-mode gate (STRICT_RUNTIME_VERIFICATION=1) sets passed=False on violations
    without raising an exception (ADR-3)
  - Non-strict mode gate allows violations through without blocking
  - check_level_transition works as a direct API call (no automatic call site -- Gap 5)
  - _verified_nodes list is populated after successful node execution
  - build_report.pass_fail=True when no violations occurred

All external I/O is mocked (ADR-1 / ADR-2).

Run:
    pytest tests/e2e/test_full_mode_runtime_verification.py -v
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.e2e

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_LONG_PROMPT = "A" * 250


# ===========================================================================
# Test 1: Verifier singleton is reused across node calls
# ===========================================================================


def test_verifier_singleton_reused_across_node_calls(monkeypatch):
    """RuntimeVerifier.get_instance() returns the same object on repeated calls."""
    monkeypatch.setenv("ENABLE_RUNTIME_VERIFICATION", "1")
    monkeypatch.setenv("CLAUDE_HOOK_MODE", "0")

    from langgraph_engine.runtime_verification.verifier import RuntimeVerifier

    v1 = RuntimeVerifier.get_instance()
    v2 = RuntimeVerifier.get_instance()

    assert v1 is v2, "get_instance() must return the same singleton object"


# ===========================================================================
# Test 2: ORCHESTRATOR_CONTRACT passes with long prompt
# ===========================================================================


def test_orchestrator_contract_passes_with_long_prompt(monkeypatch):
    """ORCHESTRATOR_CONTRACT precondition satisfied when orchestration_prompt >= 200 chars."""
    monkeypatch.setenv("ENABLE_RUNTIME_VERIFICATION", "1")
    monkeypatch.setenv("CLAUDE_HOOK_MODE", "0")

    from langgraph_engine.runtime_verification.node_contracts import ORCHESTRATOR_CONTRACT
    from langgraph_engine.runtime_verification.verifier import RuntimeVerifier

    verifier = RuntimeVerifier.get_instance()
    verifier.register(ORCHESTRATOR_CONTRACT)

    state = {"orchestration_prompt": _LONG_PROMPT}
    violations = verifier.check_preconditions(ORCHESTRATOR_CONTRACT.node_name, state)

    assert violations == []


# ===========================================================================
# Test 3: ORCHESTRATOR_CONTRACT fails with short prompt
# ===========================================================================


def test_orchestrator_contract_fails_with_short_prompt(monkeypatch):
    """ORCHESTRATOR_CONTRACT precondition fails when orchestration_prompt < 200 chars."""
    monkeypatch.setenv("ENABLE_RUNTIME_VERIFICATION", "1")
    monkeypatch.setenv("CLAUDE_HOOK_MODE", "0")

    from langgraph_engine.runtime_verification.node_contracts import ORCHESTRATOR_CONTRACT
    from langgraph_engine.runtime_verification.verifier import RuntimeVerifier

    verifier = RuntimeVerifier.get_instance()
    verifier.register(ORCHESTRATOR_CONTRACT)

    state = {"orchestration_prompt": "short"}
    violations = verifier.check_preconditions(ORCHESTRATOR_CONTRACT.node_name, state)

    assert len(violations) >= 1
    # Short string is a range violation -- severity is ERROR
    assert any(v["severity"] in ("ERROR", "CRITICAL") for v in violations)


# ===========================================================================
# Test 4: Strict-mode gate sets passed=False without raising (ADR-3)
# ===========================================================================


def test_strict_mode_gate_sets_passed_false_on_violations(monkeypatch):
    """STRICT_RUNTIME_VERIFICATION=1 + violations -> gate['passed'] is False.

    ADR-3: strict-mode halt is a GATE FLAG, not an exception.
    This test must NOT use pytest.raises -- the gate function returns normally.
    """
    monkeypatch.setenv("ENABLE_RUNTIME_VERIFICATION", "1")
    monkeypatch.setenv("STRICT_RUNTIME_VERIFICATION", "1")
    monkeypatch.setenv("CLAUDE_HOOK_MODE", "0")

    from langgraph_engine.sdlc_pipeline.quality_gate import evaluate_quality_gate

    # State contains a verification report with violations
    state = {
        "verification_report": {
            "violations": [
                {
                    "node_name": "orchestrator_agent_caller",
                    "check_type": "precondition",
                    "key": "orchestration_prompt",
                    "message": "too short",
                    "severity": "ERROR",
                }
            ],
            "pass_fail": False,
        },
        "step4_modified_files": [],
        "step5_review_result": {},
        "step5_pr_url": "",
    }

    # evaluate_quality_gate must NOT raise -- it returns a dict (ADR-3)
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        result = evaluate_quality_gate(tmpdir, state)

    assert isinstance(result, dict)
    assert "gates" in result
    verification_gate = result["gates"].get("verification", {})
    assert (
        verification_gate.get("passed") is False
    ), "Strict mode must set verification gate passed=False when violations exist"


# ===========================================================================
# Test 5: Non-strict mode gate does NOT block on violations
# ===========================================================================


def test_non_strict_mode_gate_does_not_block_on_violations(monkeypatch):
    """STRICT_RUNTIME_VERIFICATION=0 (default) -- violations produce warning but gate passes."""
    monkeypatch.setenv("ENABLE_RUNTIME_VERIFICATION", "1")
    monkeypatch.setenv("STRICT_RUNTIME_VERIFICATION", "0")
    monkeypatch.setenv("CLAUDE_HOOK_MODE", "0")

    from langgraph_engine.sdlc_pipeline.quality_gate import evaluate_quality_gate

    state = {
        "verification_report": {
            "violations": [
                {
                    "node_name": "orchestrator_agent_caller",
                    "check_type": "precondition",
                    "key": "orchestration_prompt",
                    "message": "too short",
                    "severity": "ERROR",
                }
            ],
            "pass_fail": False,
        },
        "step4_modified_files": [],
        "step5_review_result": {},
        "step5_pr_url": "",
    }

    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        result = evaluate_quality_gate(tmpdir, state)

    verification_gate = result["gates"].get("verification", {})
    # Non-strict: violations present but gate.passed must still be True
    assert verification_gate.get("passed") is True, "Non-strict mode must not block merge when violations are present"


# ===========================================================================
# Test 6: Gate disabled when ENABLE_RUNTIME_VERIFICATION=0
# ===========================================================================


def test_verification_gate_disabled_when_env_not_set(monkeypatch):
    """evaluate_quality_gate verification sub-gate passes trivially when RV disabled."""
    monkeypatch.delenv("ENABLE_RUNTIME_VERIFICATION", raising=False)
    monkeypatch.setenv("CLAUDE_HOOK_MODE", "0")

    from langgraph_engine.sdlc_pipeline.quality_gate import evaluate_quality_gate

    state = {
        "step4_modified_files": [],
        "step5_review_result": {},
        "step5_pr_url": "",
    }

    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        result = evaluate_quality_gate(tmpdir, state)

    verification_gate = result["gates"].get("verification", {})
    assert verification_gate.get("passed") is True
    assert "disabled" in verification_gate.get("reason", "").lower()


# ===========================================================================
# Test 7: check_level_transition direct call (Gap 5 -- no auto call site)
# ===========================================================================


def test_check_level_transition_direct_call(monkeypatch):
    """check_level_transition("level1", "level3", state) is a direct verifier API call.

    Gap 5 note: there is NO automatic call site in any pipeline node for
    check_level_transition.  Tests that need transition guard coverage must
    call the verifier directly.  This test documents and verifies that
    behavior: the API exists, accepts the correct arguments, and returns
    a list (empty when the transition guard has no registered specs for
    this level pair, or a list of violations when combined_complexity_score
    is out of range).
    """
    monkeypatch.setenv("ENABLE_RUNTIME_VERIFICATION", "1")
    monkeypatch.setenv("CLAUDE_HOOK_MODE", "0")

    from langgraph_engine.runtime_verification.verifier import RuntimeVerifier

    verifier = RuntimeVerifier.get_instance()

    # Valid state: combined_complexity_score in expected range [1, 25]
    valid_state = {"combined_complexity_score": 10, "user_message": "task description"}
    result = verifier.check_level_transition("level1", "level3", valid_state)

    # Must return a list (empty or with violations -- both are valid)
    assert isinstance(result, list), "check_level_transition must return a list of violation dicts"


# ===========================================================================
# Test 8: _verified_nodes populated after decorated node call
# ===========================================================================


def test_verified_nodes_populated_after_node_execution(monkeypatch, mock_create_span):
    """After a decorated node runs, node_name appears in verifier._verified_nodes."""
    monkeypatch.setenv("ENABLE_RUNTIME_VERIFICATION", "1")
    monkeypatch.setenv("CLAUDE_HOOK_MODE", "0")

    from langgraph_engine.runtime_verification.contracts import NodeContract, PreconditionSpec
    from langgraph_engine.runtime_verification.decorators import verify_node
    from langgraph_engine.runtime_verification.verifier import RuntimeVerifier

    verifier = RuntimeVerifier.get_instance()

    contract = NodeContract(
        node_name="full_mode_node_tracking",
        preconditions=[PreconditionSpec(key="user_message", expected_type=str, required=True)],
        postconditions=[],
        invariants=[],
    )

    @verify_node(contract)
    def _tracked_node(state):
        return {"output": "tracked"}

    _tracked_node({"user_message": "track me"})

    assert "full_mode_node_tracking" in verifier._verified_nodes


# ===========================================================================
# Test 9: build_report pass_fail=True when no violations in full mode
# ===========================================================================


def test_build_report_clean_in_full_mode(monkeypatch, mock_create_span):
    """No violations in full mode -> build_report().pass_fail is True."""
    monkeypatch.setenv("ENABLE_RUNTIME_VERIFICATION", "1")
    monkeypatch.setenv("CLAUDE_HOOK_MODE", "0")

    from langgraph_engine.runtime_verification.contracts import NodeContract, PreconditionSpec
    from langgraph_engine.runtime_verification.decorators import verify_node
    from langgraph_engine.runtime_verification.verifier import RuntimeVerifier

    verifier = RuntimeVerifier.get_instance()

    contract = NodeContract(
        node_name="full_mode_clean_node",
        preconditions=[PreconditionSpec(key="user_message", expected_type=str, required=True)],
        postconditions=[],
        invariants=[],
    )

    @verify_node(contract)
    def _clean_node(state):
        return {"output": "clean"}

    _clean_node({"user_message": "all good"})

    report = verifier.build_report()
    assert report.pass_fail is True
    assert report.violations == []

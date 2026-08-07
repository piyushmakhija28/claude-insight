"""Tests for langgraph_engine.runtime_verification.schema_verifier.

Pure function tests -- no fixtures, no monkeypatching, no singleton state needed.
Covers: happy path, empty input, whitespace-only, too-short, error-string detection.

Constants under test:
    _MIN_PROMPT_LEN = 200
"""

from langgraph_engine.runtime_verification.schema_verifier import verify_orchestration_prompt

# ---------------------------------------------------------------------------
# verify_orchestration_prompt -- 4 tests
# ---------------------------------------------------------------------------


def test_verify_orchestration_prompt_valid():
    """A prompt with length >= 200 and containing 'Phase' must return no errors."""
    # Arrange: 20 chars of prefix + 240 padding = 260 chars total, contains "Phase"
    prompt = "Phase A foundation: " + "x" * 240
    assert len(prompt) == 260  # sanity check for the test itself

    # Act
    errors = verify_orchestration_prompt(prompt)

    # Assert
    assert errors == [], f"Expected no errors but got: {errors}"


def test_verify_orchestration_prompt_empty():
    """An empty string must produce at least one error mentioning 'empty'."""
    # Act
    errors = verify_orchestration_prompt("")

    # Assert
    assert len(errors) >= 1
    assert any("empty" in e.lower() for e in errors), f"Expected an 'empty' error in {errors}"


def test_verify_orchestration_prompt_whitespace_only():
    """Whitespace-only input is treated as empty and must produce at least one error."""
    # Act
    errors = verify_orchestration_prompt("   ")

    # Assert -- whitespace-only triggers the empty branch (prompt.strip() is falsy)
    assert len(errors) >= 1


def test_verify_orchestration_prompt_too_short():
    """A prompt that contains 'Phase' but is under the 200-char minimum must flag length.

    The error message must reference 'short', '200', or 'min' so callers understand
    the threshold that was violated.
    """
    # Arrange: well under 200 chars, but 'Phase' keyword is present
    prompt = "Phase short"
    assert len(prompt) < 200  # sanity check

    # Act
    errors = verify_orchestration_prompt(prompt)

    # Assert: at least one error and it mentions the length constraint
    assert len(errors) >= 1
    assert any(
        "short" in e.lower() or "200" in e or "min" in e.lower() for e in errors
    ), f"Expected a length-related error in {errors}"

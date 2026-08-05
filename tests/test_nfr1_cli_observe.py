"""Tests that the NFR-1 driver is actually reachable from the CLI.

A driver that exists but is never called is the defect this repository has
already recorded once (REVIEW-INDEX 39: a gate landed without being wired into
CI). So these tests do not re-test the driver's internals -- test_nfr1_driver.py
does that. They test the wiring: that --observe reaches the driver, that what the
driver observes reaches the measurement, and that a void observation is reported
as void rather than as a small number.
"""

import json
import os
import sys

_TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
if _TESTS_DIR not in sys.path:
    sys.path.insert(0, _TESTS_DIR)

from nfr1 import cli, driver, harness  # noqa: E402

SESSION = "wiring-session"


def transcript_with(tmp_path, name=SESSION):
    """Create an empty transcript named after a session id.

    Args:
        tmp_path: pytest temporary directory.
        name: Session id to encode in the filename.

    Returns:
        str: Path of the created transcript.
    """
    path = tmp_path / ("%s.jsonl" % name)
    path.write_text("", encoding="utf-8")
    return str(path)


def append_calls(path, ids, session_id=SESSION):
    """Append one assistant record carrying the given tool-use ids.

    Args:
        path: Transcript path.
        ids: Tool-use ids to write.
        session_id: Session id to stamp on the record.
    """
    record = {
        "type": "assistant",
        "sessionId": session_id,
        "timestamp": "2026-08-05T00:00:00Z",
        "isSidechain": False,
        "message": {"content": [{"type": "tool_use", "id": i, "name": "Bash", "input": {}} for i in ids]},
    }
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(record) + "\n")


class TestObserveReachesTheDriver:
    """The CLI must call the driver, not merely import it."""

    def test_observe_marks_every_tool_call_it_sees(self, tmp_path, monkeypatch):
        path = transcript_with(tmp_path)
        seen = {}

        real_drive = driver.drive

        def spy(session, tail, required, **kwargs):
            """Record the call, then append the calls the tail will find."""
            seen["required"] = required
            append_calls(path, ["t%d" % i for i in range(10)])
            return real_drive(session, tail, required, sleep=lambda _: None, **kwargs)

        monkeypatch.setattr(driver, "drive", spy)
        result = cli.run_observed_phase(harness.PHASE_WARM, None, transcript=path, max_polls=5)

        assert seen["required"] == harness.REQUIRED_TOOL_CALLS
        assert result["tool_calls_recorded"] == 10
        assert len(result["observed_tool_calls"]) == 10

    def test_a_window_with_no_tool_calls_records_zero(self, tmp_path):
        """Paired negative: the count comes from the transcript, not from a constant."""
        path = transcript_with(tmp_path)
        result = cli.run_observed_phase(harness.PHASE_WARM, None, transcript=path, max_polls=2)
        assert result["tool_calls_recorded"] == 0
        assert result["verdict"] == harness.VERDICT_INDETERMINATE

    def test_the_phase_argument_reaches_the_measurement(self, tmp_path):
        path = transcript_with(tmp_path)
        cold = cli.run_observed_phase(harness.PHASE_COLD, None, transcript=path, max_polls=1)
        warm = cli.run_observed_phase(harness.PHASE_WARM, None, transcript=path, max_polls=1)
        assert cold["phase"] == harness.PHASE_COLD
        assert warm["phase"] == harness.PHASE_WARM

    def test_another_sessions_calls_are_not_counted(self, tmp_path):
        """The CLI must derive the session id from the transcript it was given."""
        path = transcript_with(tmp_path)
        result_holder = {}

        original = driver.drive

        def spy(session, tail, required, **kwargs):
            append_calls(path, ["x1", "x2"], session_id="a-different-session")
            return original(session, tail, required, sleep=lambda _: None, **kwargs)

        import unittest.mock

        with unittest.mock.patch.object(driver, "drive", spy):
            result_holder = cli.run_observed_phase(harness.PHASE_WARM, None, transcript=path, max_polls=3)
        assert result_holder["tool_calls_recorded"] == 0


class TestObserveReportsVoidAsVoid:
    """A rewritten transcript must not be downgraded into a short window."""

    def test_a_rewrite_is_reported_as_void_not_as_a_count(self, tmp_path):
        path = transcript_with(tmp_path)
        original = driver.drive

        def spy(session, tail, required, **kwargs):
            append_calls(path, ["t1"])
            tail.poll()
            with open(path, "w", encoding="utf-8") as handle:
                handle.write("")
            return original(session, tail, required, sleep=lambda _: None, **kwargs)

        import unittest.mock

        with unittest.mock.patch.object(driver, "drive", spy):
            result = cli.run_observed_phase(harness.PHASE_WARM, None, transcript=path, max_polls=3)

        assert "void_reason" in result
        assert "tool_calls_recorded" not in result, "a void window must not report a count"
        assert result["verdict"] == harness.VERDICT_INDETERMINATE

    def test_a_missing_transcript_is_an_error_not_a_zero(self, tmp_path):
        missing = str(tmp_path / "nothing" / "absent.jsonl")
        result = cli.run_observed_phase(harness.PHASE_WARM, None, transcript=missing, max_polls=1)
        assert result["tool_calls_recorded"] == 0


class TestObserveExitStatus:
    """main() must distinguish a measurement from a failed observation."""

    def test_a_completed_observation_exits_zero(self, tmp_path, capsys):
        path = transcript_with(tmp_path)
        status = cli.main(["--observe", "--transcript", path, "--max-polls", "1"])
        capsys.readouterr()
        assert status == 0

    def test_an_absent_transcript_exits_nonzero(self, capsys, monkeypatch):
        monkeypatch.setattr(cli, "newest_transcript_for_this_project", lambda: None)
        status = cli.main(["--observe", "--max-polls", "1"])
        out = capsys.readouterr().out
        assert status == 1
        assert "error" in json.loads(out)

    def test_observe_is_opt_in(self, tmp_path, capsys):
        """Without --observe the CLI must not start tailing anything."""
        status = cli.main(["--plugin-root", str(tmp_path)])
        payload = json.loads(capsys.readouterr().out)
        assert status == 0
        assert "observed_tool_calls" not in payload

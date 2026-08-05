"""Tests for the CheckpointManager durability contract (V2-031 / GitHub #287).

Covers the four acceptance criteria of PRD NFR-3 / SRS NFR-9:

AC1  Kill a process mid-pipeline and confirm resume picks up at the correct step
     boundary, using the existing CheckpointManager writer.
AC2  A checkpoint-save failure is no longer swallowed: the session is marked
     degraded and the resume path refuses to trust it.
AC3  The per-step progress surface is a projection of the checkpoint record, not
     a second writer.
AC4  Re-executing a side-effecting step under the same session-id-plus-step-number
     key produces no duplicate external effect.

Every check has a companion negative test proving it can fail. No test writes to
any real settings file and no test creates a real GitHub issue.

ASCII-safe, UTF-8 encoded - Windows cp1252 compatible.
"""

import importlib.util
import json
import subprocess
import sys
import textwrap
import types
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# ---------------------------------------------------------------------------
# Pre-import stubs (mirrors tests/test_checkpoint_manager.py)
# ---------------------------------------------------------------------------


def _stub(name, **attrs):
    m = types.ModuleType(name)
    for k, v in attrs.items():
        setattr(m, k, v)
    sys.modules[name] = m
    return m


_stub("loguru", logger=MagicMock())

_REPO_ROOT = str(Path(__file__).resolve().parent.parent)
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

_LE_ROOT = Path(_REPO_ROOT) / "langgraph_engine"

_le = types.ModuleType("langgraph_engine")
_le.__path__ = [str(_LE_ROOT)]
_le.__package__ = "langgraph_engine"
sys.modules["langgraph_engine"] = _le


def _load_module(name, rel_path):
    full_path = _LE_ROOT / rel_path
    spec = importlib.util.spec_from_file_location(name, str(full_path))
    mod = importlib.util.module_from_spec(spec)
    mod.__package__ = "langgraph_engine"
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


_cp_mod = _load_module("langgraph_engine.checkpoint_manager", "checkpoint_manager.py")
_ledger_mod = _load_module("langgraph_engine.effect_ledger", "effect_ledger.py")

CheckpointManager = _cp_mod.CheckpointManager
CheckpointDegradedError = _cp_mod.CheckpointDegradedError
write_progress_projection = _cp_mod.write_progress_projection
PROGRESS_PROJECTION_FILENAME = _cp_mod.PROGRESS_PROJECTION_FILENAME

EffectLedger = _ledger_mod.EffectLedger
EffectReplayError = _ledger_mod.EffectReplayError
STATUS_PENDING = _ledger_mod.STATUS_PENDING


def _make_manager(tmp_path, session_id="contract-session"):
    return CheckpointManager(session_id=session_id, base_dir=str(tmp_path))


# ===========================================================================
# AC1 - Crash mid-pipeline, resume at the correct step boundary
# ===========================================================================


_CRASH_CHILD = textwrap.dedent(
    """
    import importlib.util, os, sys, types
    from pathlib import Path
    from unittest.mock import MagicMock

    repo_root = sys.argv[1]
    base_dir = sys.argv[2]
    session_id = sys.argv[3]
    crash_at = int(sys.argv[4])

    m = types.ModuleType("loguru")
    m.logger = MagicMock()
    sys.modules["loguru"] = m

    sys.path.insert(0, repo_root)
    le_root = Path(repo_root) / "langgraph_engine"
    le = types.ModuleType("langgraph_engine")
    le.__path__ = [str(le_root)]
    le.__package__ = "langgraph_engine"
    sys.modules["langgraph_engine"] = le

    spec = importlib.util.spec_from_file_location(
        "langgraph_engine.checkpoint_manager", str(le_root / "checkpoint_manager.py")
    )
    mod = importlib.util.module_from_spec(spec)
    mod.__package__ = "langgraph_engine"
    sys.modules["langgraph_engine.checkpoint_manager"] = mod
    spec.loader.exec_module(mod)

    cp = mod.CheckpointManager(session_id=session_id, base_dir=base_dir)
    for step in range(0, 9):
        if step == crash_at:
            os._exit(137)
        cp.save_checkpoint(step, {"session_id": session_id, "progress": step})
    """
)


def _run_child_until_crash(tmp_path, session_id, crash_at):
    script = tmp_path / "crash_child.py"
    script.write_text(_CRASH_CHILD, encoding="utf-8")
    return subprocess.run(
        [
            sys.executable,
            str(script),
            _REPO_ROOT,
            str(tmp_path),
            session_id,
            str(crash_at),
        ],
        capture_output=True,
    )


class TestAC1CrashResume:
    """AC1 - resume picks up at the correct step boundary after a hard kill."""

    def test_resume_after_hard_kill_resumes_at_next_step(self, tmp_path):
        session_id = "crash-session"
        proc = _run_child_until_crash(tmp_path, session_id, crash_at=5)

        assert proc.returncode != 0, "child must have died, not exited cleanly"

        cp = CheckpointManager(session_id=session_id, base_dir=str(tmp_path))
        last_step, state = cp.get_last_checkpoint()

        assert last_step == 4, "steps 0-4 completed before the kill at step 5"
        assert state is not None
        assert state["progress"] == 4
        assert not cp.is_degraded(), "a clean kill loses no write, so the chain is intact"

    def test_resume_boundary_is_not_the_crashed_step(self, tmp_path):
        """Negative control: the crashed step must NOT appear as completed."""
        session_id = "crash-session-neg"
        _run_child_until_crash(tmp_path, session_id, crash_at=5)

        cp = CheckpointManager(session_id=session_id, base_dir=str(tmp_path))
        last_step, _ = cp.get_last_checkpoint()

        assert last_step != 5, "step 5 never ran; reporting it complete would skip real work"
        assert cp.load_checkpoint(5) is None

    def test_crash_at_a_different_step_moves_the_boundary(self, tmp_path):
        """Specificity (tighter): the boundary tracks the kill point, it is not a constant."""
        session_id = "crash-session-early"
        _run_child_until_crash(tmp_path, session_id, crash_at=2)

        cp = CheckpointManager(session_id=session_id, base_dir=str(tmp_path))
        last_step, _ = cp.get_last_checkpoint()

        assert last_step == 1, "a kill at step 2 must resume at 1, not at the step-5 value"


# ===========================================================================
# AC2 - A failed checkpoint save degrades the session; resume refuses it
# ===========================================================================


class TestAC2FailedSaveIsNotSwallowed:
    """AC2 - a checkpoint-save failure sets a flag the resume path refuses to trust."""

    def test_failed_save_returns_false_and_marks_degraded(self, tmp_path, monkeypatch):
        cp = _make_manager(tmp_path)
        cp.save_checkpoint(1, {"ok": True})

        def _boom(path, content):
            raise OSError("simulated disk full")

        monkeypatch.setattr(cp, "_atomic_write", _boom)
        result = cp.save_checkpoint(2, {"ok": True})

        assert result is False, "a lost write must be reported, not absorbed"
        assert cp.is_degraded() is True
        assert cp.degraded_marker_path.is_file(), "marker must be durable for another process"

    def test_resume_refuses_a_degraded_session(self, tmp_path, monkeypatch):
        cp = _make_manager(tmp_path)
        cp.save_checkpoint(1, {"ok": True})
        monkeypatch.setattr(cp, "_atomic_write", MagicMock(side_effect=OSError("disk full")))
        cp.save_checkpoint(2, {"ok": True})

        with pytest.raises(CheckpointDegradedError):
            cp.get_last_checkpoint()
        with pytest.raises(CheckpointDegradedError):
            cp.get_last_successful_checkpoint()
        with pytest.raises(CheckpointDegradedError):
            cp.load_checkpoint_by_id("contract-session:step-01")

    def test_degradation_is_visible_to_a_fresh_manager(self, tmp_path, monkeypatch):
        """The process that lost the write may not survive to report it in memory."""
        cp = _make_manager(tmp_path)
        cp.save_checkpoint(1, {"ok": True})
        monkeypatch.setattr(cp, "_atomic_write", MagicMock(side_effect=OSError("disk full")))
        cp.save_checkpoint(2, {"ok": True})

        reopened = _make_manager(tmp_path)
        assert reopened.is_degraded() is True
        with pytest.raises(CheckpointDegradedError):
            reopened.get_last_checkpoint()

    def test_truncated_write_is_caught_by_read_back(self, tmp_path, monkeypatch):
        """The non-atomic fallback path can leave a partial file; read-back must catch it."""
        cp = _make_manager(tmp_path)

        def _truncate(path, content):
            Path(path).write_text(content[: len(content) // 2], encoding="utf-8")

        monkeypatch.setattr(cp, "_atomic_write", _truncate)
        result = cp.save_checkpoint(3, {"ok": True})

        assert result is False, "an unparseable checkpoint is not a checkpoint"
        assert cp.is_degraded() is True

    def test_allow_degraded_is_an_explicit_opt_in(self, tmp_path, monkeypatch):
        cp = _make_manager(tmp_path)
        cp.save_checkpoint(1, {"ok": True})
        monkeypatch.setattr(cp, "_atomic_write", MagicMock(side_effect=OSError("disk full")))
        cp.save_checkpoint(2, {"ok": True})

        last_step, state = cp.get_last_checkpoint(allow_degraded=True)
        assert last_step == 1
        assert state is not None

    # -- negative controls ---------------------------------------------------

    def test_healthy_session_is_not_degraded(self, tmp_path):
        """Negative control: the guard must not fire when nothing failed."""
        cp = _make_manager(tmp_path)
        assert cp.save_checkpoint(1, {"ok": True}) is True
        assert cp.is_degraded() is False
        assert cp.degradation_details() is None

        last_step, state = cp.get_last_checkpoint()
        assert last_step == 1
        assert state == {"ok": True}

    def test_degradation_details_name_the_failing_step(self, tmp_path, monkeypatch):
        """Specificity (tighter): the marker must identify which step lost its write."""
        cp = _make_manager(tmp_path)
        monkeypatch.setattr(cp, "_atomic_write", MagicMock(side_effect=OSError("disk full")))
        cp.save_checkpoint(6, {"ok": True})

        details = cp.degradation_details()
        assert details is not None
        assert details["degraded_at_step"] == 6, "a constant step number would pass a looser check"
        assert "disk full" in details["reason"]


# ===========================================================================
# AC3 - The progress surface is a projection, not a second writer
# ===========================================================================


class TestAC3ProgressIsAProjection:
    """AC3 - no dual-write path: the progress surface is derived from the record."""

    def test_projection_matches_the_checkpoint_record(self, tmp_path):
        cp = _make_manager(tmp_path)
        cp.save_checkpoint(4, {"ok": True}, success_status=True)

        session_dir = tmp_path / "session"
        session_dir.mkdir()
        projected = write_progress_projection(cp, 4, str(session_dir), "STEP 4")

        written = json.loads((session_dir / PROGRESS_PROJECTION_FILENAME).read_text(encoding="utf-8"))
        record = cp.load_checkpoint_metadata(4)

        assert projected == written
        assert written["last_step"] == record["step"]
        assert written["session_id"] == record["session_id"]
        assert written["timestamp"] == record["timestamp"]
        assert written["checkpoint_id"] == record["checkpoint_id"]
        assert written["projected_from"] == "checkpoint"

    def test_projection_status_is_derived_from_the_record_not_the_caller(self, tmp_path):
        """A second writer could claim SUCCESS for a step the record calls FAILED."""
        cp = _make_manager(tmp_path)
        cp.save_checkpoint(4, {"ok": False}, success_status=False, error_message="boom")

        session_dir = tmp_path / "session"
        session_dir.mkdir()
        projected = write_progress_projection(cp, 4, str(session_dir), "STEP 4")

        assert projected["last_step_status"] == "FAILED"

    def test_no_projection_is_written_without_a_checkpoint_record(self, tmp_path):
        """The surface must never advance past what the checkpoint durably carries."""
        cp = _make_manager(tmp_path)
        session_dir = tmp_path / "session"
        session_dir.mkdir()

        projected = write_progress_projection(cp, 7, str(session_dir), "STEP 7")

        assert projected is None
        assert not (session_dir / PROGRESS_PROJECTION_FILENAME).exists()

    def test_failed_save_leaves_the_previous_projection_in_place(self, tmp_path, monkeypatch):
        """The end-to-end dual-write property: a lost checkpoint cannot advance progress."""
        cp = _make_manager(tmp_path)
        session_dir = tmp_path / "session"
        session_dir.mkdir()

        cp.save_checkpoint(2, {"ok": True})
        write_progress_projection(cp, 2, str(session_dir), "STEP 2")

        monkeypatch.setattr(cp, "_atomic_write", MagicMock(side_effect=OSError("disk full")))
        cp.save_checkpoint(3, {"ok": True})
        write_progress_projection(cp, 3, str(session_dir), "STEP 3")

        written = json.loads((session_dir / PROGRESS_PROJECTION_FILENAME).read_text(encoding="utf-8"))
        assert written["last_step"] == 2, "progress must not report step 3, whose record was lost"

    # -- negative control ----------------------------------------------------

    def test_projection_advances_when_the_checkpoint_does(self, tmp_path):
        """Negative control: the projection is not simply frozen."""
        cp = _make_manager(tmp_path)
        session_dir = tmp_path / "session"
        session_dir.mkdir()

        cp.save_checkpoint(2, {"ok": True})
        write_progress_projection(cp, 2, str(session_dir), "STEP 2")
        cp.save_checkpoint(3, {"ok": True})
        write_progress_projection(cp, 3, str(session_dir), "STEP 3")

        written = json.loads((session_dir / PROGRESS_PROJECTION_FILENAME).read_text(encoding="utf-8"))
        assert written["last_step"] == 3


# ===========================================================================
# AC4 - Replay idempotency for a side-effecting step
# ===========================================================================


class _FakeGitHub:
    """Simulated GitHub issue API. Never touches the network."""

    def __init__(self):
        self.calls = 0
        self.created_issue_numbers = []

    def create_issue(self):
        self.calls += 1
        number = 255 + self.calls
        self.created_issue_numbers.append(number)
        return {"success": True, "issue_number": number, "issue_url": "https://example.invalid/%d" % number}


class TestAC4ReplayIdempotency:
    """AC4 - the same session-id-plus-step key commits one external effect only."""

    def test_second_execution_creates_no_duplicate_issue(self, tmp_path):
        github = _FakeGitHub()
        ledger = EffectLedger("dup-session", base_dir=str(tmp_path))
        key = ledger.effect_key(step=2, effect_name="github_issue")

        first, replayed_first = ledger.run_once(key, github.create_issue)
        second, replayed_second = ledger.run_once(key, github.create_issue)

        assert github.calls == 1, "a second execution must not POST again (issues 256 and 257)"
        assert replayed_first is False
        assert replayed_second is True
        assert first == second
        assert github.created_issue_numbers == [256]

    def test_replay_survives_a_new_ledger_instance(self, tmp_path):
        """A crash means a fresh process, so the guard must be on disk, not in memory."""
        github = _FakeGitHub()
        key_args = dict(step=2, effect_name="github_issue")

        ledger_a = EffectLedger("crash-dup", base_dir=str(tmp_path))
        ledger_a.run_once(ledger_a.effect_key(**key_args), github.create_issue)

        ledger_b = EffectLedger("crash-dup", base_dir=str(tmp_path))
        effect, replayed = ledger_b.run_once(ledger_b.effect_key(**key_args), github.create_issue)

        assert github.calls == 1
        assert replayed is True
        assert effect["issue_number"] == 256

    def test_unknown_outcome_refuses_rather_than_guessing(self, tmp_path):
        """A PENDING entry cannot be distinguished from a committed effect."""
        github = _FakeGitHub()
        ledger = EffectLedger("pending-session", base_dir=str(tmp_path))
        key = ledger.effect_key(step=2, effect_name="github_issue")

        ledger.mark_pending(key)

        with pytest.raises(EffectReplayError):
            ledger.run_once(key, github.create_issue)
        assert github.calls == 0, "re-executing an unknown outcome is how duplicates happen"

    def test_failed_attempt_is_not_recorded_as_committed(self, tmp_path):
        """A creation that never committed must remain retryable."""
        attempts = {"n": 0}

        def _flaky():
            attempts["n"] += 1
            if attempts["n"] == 1:
                return {"success": False, "error": "github unreachable"}
            return {"success": True, "issue_number": 256}

        def predicate(result):
            return bool(result.get("success"))

        ledger = EffectLedger("flaky-session", base_dir=str(tmp_path))
        key = ledger.effect_key(step=2, effect_name="github_issue")

        ledger.run_once(key, _flaky, commit_predicate=predicate)
        effect, replayed = ledger.run_once(key, _flaky, commit_predicate=predicate)

        assert replayed is False, "a failed attempt must not be replayed as a committed effect"
        assert effect["success"] is True
        assert attempts["n"] == 2

    def test_raising_effect_clears_the_pending_entry(self, tmp_path):
        ledger = EffectLedger("raise-session", base_dir=str(tmp_path))
        key = ledger.effect_key(step=2, effect_name="github_issue")

        def _raises():
            raise RuntimeError("network reset")

        with pytest.raises(RuntimeError):
            ledger.run_once(key, _raises)

        assert ledger.lookup(key) is None, "a raised effect committed nothing; leave it retryable"

    # -- negative controls and specificity -----------------------------------

    def test_a_different_step_is_a_different_effect(self, tmp_path):
        """Specificity (looser direction): the key must not collapse distinct steps."""
        github = _FakeGitHub()
        ledger = EffectLedger("multi-step", base_dir=str(tmp_path))

        ledger.run_once(ledger.effect_key(step=2, effect_name="github_issue"), github.create_issue)
        ledger.run_once(ledger.effect_key(step=5, effect_name="github_issue"), github.create_issue)

        assert github.calls == 2, "step 2 and step 5 are separate effects, not one"

    def test_a_different_session_is_a_different_effect(self, tmp_path):
        github = _FakeGitHub()
        a = EffectLedger("session-a", base_dir=str(tmp_path))
        b = EffectLedger("session-b", base_dir=str(tmp_path))

        a.run_once(a.effect_key(step=2, effect_name="github_issue"), github.create_issue)
        b.run_once(b.effect_key(step=2, effect_name="github_issue"), github.create_issue)

        assert github.calls == 2, "two sessions each legitimately create their own issue"

    def test_without_the_guard_a_duplicate_is_produced(self, tmp_path):
        """Negative control proving the guard is what prevents the duplicate."""
        github = _FakeGitHub()

        github.create_issue()
        github.create_issue()

        assert github.calls == 2
        assert github.created_issue_numbers == [256, 257], "the unguarded shape of the shipped bug"

    def test_effect_key_uses_the_checkpoint_identity(self, tmp_path):
        """The ledger and the checkpoint chain must agree on what 'this step' means."""
        cp = CheckpointManager(session_id="key-session", base_dir=str(tmp_path))
        ledger = EffectLedger("key-session", base_dir=str(tmp_path))

        assert ledger.effect_key(step=2) == cp._make_checkpoint_id(2)
        assert ledger.effect_key(step=2, effect_name="github_issue").startswith(cp._make_checkpoint_id(2))

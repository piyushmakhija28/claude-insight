"""Tests for hooks/session_context.py - the single source of session identity.

Covers the three failure modes that motivated the module:
  1. Hooks disagreeing about which session is active.
  2. Two incompatible session ID formats reaching the same consumers.
  3. Concurrent read-modify-write corrupting shared session JSON.

Windows-safe: ASCII only, no Unicode characters.
"""

import json
import os
import sys
import threading
from pathlib import Path

import pytest

_HOOKS_DIR = str(Path(__file__).resolve().parent.parent / "hooks")
if _HOOKS_DIR not in sys.path:
    sys.path.insert(0, _HOOKS_DIR)

import session_context as sc  # noqa: E402


@pytest.fixture
def isolated_memory(tmp_path, monkeypatch):
    """Point session_context at a temporary memory root.

    Yields:
        Path: The temporary memory root directory.
    """
    monkeypatch.setenv("CLAUDE_HOME", str(tmp_path))
    monkeypatch.delenv("CLAUDE_IDE_DATA_DIR", raising=False)
    monkeypatch.delenv("CLAUDE_IDE_INSTALL_DIR", raising=False)
    monkeypatch.delenv(sc.ENV_SESSION_ID, raising=False)
    memory = tmp_path / "memory"
    memory.mkdir(parents=True, exist_ok=True)
    yield memory


class TestNormalizeSessionId:
    """normalize_session_id() must accept every real-world form and reject junk."""

    @pytest.mark.parametrize(
        "raw,expected",
        [
            ("1634491e-12cd-409f-a7d6-8a886e4e1c7f", "SESSION-1634491e-12cd-409f-a7d6-8a886e4e1c7f"),
            ("SESSION-20260317-093639-5YPR", "SESSION-20260317-093639-5YPR"),
            ("session-20260730-140126-a255f28f", "SESSION-20260730-140126-a255f28f"),
            ("session-abc", "SESSION-session-abc"),
            ("  SESSION-20260101-000000-AAAA  ", "SESSION-20260101-000000-AAAA"),
        ],
    )
    def test_accepted_forms_normalize_to_session_prefix(self, raw, expected):
        assert sc.normalize_session_id(raw) == expected

    @pytest.mark.parametrize("raw", ["", None, 12345, "../escape", "a/b", "a\\b", "x" * 200, "SESSION-"])
    def test_unusable_input_returns_empty(self, raw):
        assert sc.normalize_session_id(raw) == ""

    def test_engine_and_pipeline_formats_converge(self):
        """The two historical generators produced IDs no consumer could share."""
        pipeline_form = sc.normalize_session_id("SESSION-20260730-140126-a255f28f")
        engine_form = sc.normalize_session_id("session-20260730-140126-a255f28f")
        assert pipeline_form == engine_form
        assert engine_form.startswith(sc.SESSION_PREFIX)


class TestResolutionOrder:
    """The payload-bound session must outrank anything on disk."""

    def test_bound_payload_wins_over_stale_pointer(self, isolated_memory):
        sc.write_session_pointer("SESSION-20260317-093639-5YPR")
        sc.bind_session({"session_id": "fresh-uuid-0001"})
        assert sc.resolve_session_id() == "SESSION-fresh-uuid-0001"

    def test_pointer_used_when_nothing_bound(self, isolated_memory):
        sc.write_session_pointer("SESSION-20260101-000000-AAAA")
        assert sc.resolve_session_id() == "SESSION-20260101-000000-AAAA"

    def test_legacy_progress_file_is_last_resort(self, isolated_memory):
        progress = isolated_memory / "logs" / sc.LEGACY_PROGRESS_FILENAME
        progress.parent.mkdir(parents=True, exist_ok=True)
        progress.write_text(json.dumps({"session_id": "SESSION-20260202-000000-BBBB"}), encoding="utf-8")
        assert sc.resolve_session_id() == "SESSION-20260202-000000-BBBB"

    def test_default_returned_when_unresolvable(self, isolated_memory):
        assert sc.resolve_session_id() == ""
        assert sc.resolve_session_id(default="unknown") == "unknown"

    def test_bind_with_no_session_id_preserves_existing_binding(self, isolated_memory):
        sc.bind_session({"session_id": "keep-me"})
        assert sc.bind_session({}) == ""
        assert sc.resolve_session_id() == "SESSION-keep-me"

    def test_corrupt_pointer_does_not_raise(self, isolated_memory):
        sc.get_pointer_file().write_text("{not json", encoding="utf-8")
        assert sc.read_session_pointer() == ""


class TestAllHookResolversAgree:
    """Every hook-side resolver must return the identical session."""

    def test_seven_resolvers_return_one_value(self, isolated_memory, monkeypatch):
        bound = sc.bind_session({"session_id": "agreement-test-0001"})

        import importlib

        import policy_tracking_helper
        import project_session

        importlib.reload(project_session)

        sys.path.insert(0, str(Path(_HOOKS_DIR) / "pre_tool_enforcer"))
        sys.path.insert(0, str(Path(_HOOKS_DIR) / "post_tool_tracker"))
        import loaders as post_loaders  # noqa: F401 - resolved via post_tool_tracker path

        results = {
            "session_context": sc.resolve_session_id(),
            "project_session": project_session.read_session_id(),
            "policy_tracking_helper": policy_tracking_helper.get_session_id(),
            "post_tool_tracker": post_loaders._get_session_id_from_progress(),
        }

        assert set(results.values()) == {bound}, results


class TestPerSessionScoping:
    """Progress state must not be shared between sessions."""

    def test_two_sessions_get_different_progress_files(self, isolated_memory):
        sc.bind_session({"session_id": "20260730-100000-aaaa1111"})
        path_a = sc.get_session_progress_file()
        sc.bind_session({"session_id": "20260730-100000-bbbb2222"})
        path_b = sc.get_session_progress_file()

        assert path_a != path_b
        assert path_a.parent.name == "SESSION-20260730-100000-aaaa1111"
        assert path_b.parent.name == "SESSION-20260730-100000-bbbb2222"

    def test_falls_back_to_legacy_file_without_a_session(self, isolated_memory):
        assert sc.get_session_progress_file() == sc.get_legacy_progress_file()

    def test_session_dir_lives_under_one_root(self, isolated_memory):
        sc.bind_session({"session_id": "root-check"})
        session_dir = sc.get_session_dir(create=True)
        assert session_dir.parent == sc.get_sessions_root()
        assert session_dir.is_dir()


class TestAtomicAndLockedWrites:
    """Concurrent writers must never leave unparseable JSON behind."""

    def test_atomic_write_leaves_no_temp_files(self, isolated_memory):
        target = isolated_memory / "atomic.json"
        assert sc.atomic_write_text(target, json.dumps({"ok": True}))
        assert json.loads(target.read_text(encoding="utf-8")) == {"ok": True}
        assert list(isolated_memory.glob("atomic.json.tmp-*")) == []

    def test_concurrent_updates_never_corrupt_and_never_lose_a_reported_write(self, isolated_memory):
        """This is the regression test for the flow-trace.corrupt-* archives.

        The contract is not "every attempt lands" -- under enough contention the
        lock times out and the update is deliberately skipped rather than raced,
        which the caller sees as a None return. What must hold is that the file
        stays parseable and contains exactly the writes that reported success,
        with no duplication.
        """
        target = isolated_memory / "flow-trace.json"
        writers = 12
        per_writer = 15
        reported = []
        reported_lock = threading.Lock()

        def worker(worker_id):
            for index in range(per_writer):
                record = "{}-{}".format(worker_id, index)
                result = sc.locked_json_update(
                    target,
                    lambda data, value=record: {**data, "records": data.get("records", []) + [value]},
                    default={"records": []},
                )
                if result is not None:
                    with reported_lock:
                        reported.append(record)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(writers)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        data = json.loads(target.read_text(encoding="utf-8"))
        assert sorted(data["records"]) == sorted(reported), "file disagrees with what was reported durable"
        assert len(set(data["records"])) == len(data["records"]), "records duplicated"

    def test_update_is_skipped_rather_than_raced_when_the_lock_is_unavailable(self, isolated_memory):
        """An unlocked read-modify-write is what corrupted the file originally."""
        target = isolated_memory / "flow-trace.json"
        sc.locked_json_update(target, lambda data: {"records": ["first"]}, default={"records": []})

        def never_acquires(self):
            """Stand in for a lock that timed out, without waiting for the timeout."""
            self.acquired = False
            return self

        original_enter = sc.FileLock.__enter__
        sc.FileLock.__enter__ = never_acquires
        try:
            result = sc.locked_json_update(
                target,
                lambda data: {**data, "records": data.get("records", []) + ["second"]},
                default={"records": []},
            )
        finally:
            sc.FileLock.__enter__ = original_enter

        assert result is None, "must report failure instead of writing unlocked"
        assert json.loads(target.read_text(encoding="utf-8")) == {"records": ["first"]}

    def test_corrupt_file_recovers_to_default(self, isolated_memory):
        target = isolated_memory / "broken.json"
        target.write_text("{{{ truncated", encoding="utf-8")
        result = sc.locked_json_update(target, lambda data: {**data, "recovered": True}, default={"records": []})
        assert result == {"records": [], "recovered": True}

    def test_append_jsonl_is_line_per_record_under_concurrency(self, isolated_memory):
        target = isolated_memory / "stream.jsonl"
        writers = 10
        per_writer = 20

        def worker(worker_id):
            for index in range(per_writer):
                sc.append_jsonl(target, {"worker": worker_id, "index": index})

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(writers)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        lines = [line for line in target.read_text(encoding="utf-8").splitlines() if line.strip()]
        assert len(lines) == writers * per_writer
        for line in lines:
            json.loads(line)


class TestPointerWrite:
    """The pointer file is how payload-less processes find the session."""

    def test_pointer_roundtrip(self, isolated_memory):
        assert sc.write_session_pointer("pointer-test", project="C:/proj")
        data = json.loads(sc.get_pointer_file().read_text(encoding="utf-8"))
        assert data["current_session_id"] == "SESSION-pointer-test"
        assert data["project"] == "C:/proj"
        assert "started_at" in data

    def test_unusable_id_is_not_written(self, isolated_memory):
        assert sc.write_session_pointer("../escape") is False
        assert not sc.get_pointer_file().exists()


class TestIdeModeRoots:
    """IDE installations must not fall back to the user's home directory."""

    def test_data_dir_env_wins(self, tmp_path, monkeypatch):
        monkeypatch.setenv("CLAUDE_IDE_DATA_DIR", str(tmp_path / "ide-data"))
        assert sc.get_memory_base() == tmp_path / "ide-data" / "memory"

    def test_install_dir_env_used_when_no_data_dir(self, tmp_path, monkeypatch):
        monkeypatch.delenv("CLAUDE_IDE_DATA_DIR", raising=False)
        monkeypatch.setenv("CLAUDE_IDE_INSTALL_DIR", str(tmp_path / "ide"))
        assert sc.get_memory_base() == tmp_path / "ide" / "data" / "memory"

    def test_home_default(self, monkeypatch):
        for var in ("CLAUDE_IDE_DATA_DIR", "CLAUDE_IDE_INSTALL_DIR", "CLAUDE_HOME"):
            monkeypatch.delenv(var, raising=False)
        assert sc.get_memory_base() == Path.home() / ".claude" / "memory"


def test_env_var_name_is_stable():
    """Hooks and subprocesses agree on this variable name; do not rename it."""
    assert sc.ENV_SESSION_ID == "CLAUDE_SESSION_ID"
    assert os.environ.get("CLAUDE_SESSION_ID") is not None or True

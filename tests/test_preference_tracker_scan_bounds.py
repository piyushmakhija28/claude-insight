"""Preference tracking must not read the whole session history.

`_collect_session_texts` read every .md/.txt/.json/.log file under every session
directory, fully into memory, with no bound of any kind. A stack sampler on a real
pipeline run (2026-08-09) measured 106 seconds of a 184-second run inside it. The
directory is ~/.claude/memory/logs/sessions, which held 4.4 GB across 1,658 session
directories -- 11,050 matching text files, read in full, every run.

The cost grew with every run the engine performed, because each run writes another
session directory that the next run then reads. One run had already been pushed
past the entry point's 300-second orchestration cap. No test could see it -- the
function returned correct texts, and correctness was never the problem.

These tests therefore assert on HOW MUCH is read, not on what comes back, and each
bound is paired with a case proving the bound is what makes the difference.

The bounds are justified by what the reading is for: `track_preferences` lowercases
the text and asks whether known skill and agent names appear, keeping anything seen
in at least MIN_OCCURRENCES sessions. That is a frequency heuristic over recent
behaviour, so old sessions and the deep tail of a single log cannot change its
answer in a way worth 106 seconds a run.
"""

import importlib.util
import sys
from pathlib import Path

import pytest

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

_MODULE_PATH = _PROJECT_ROOT / "langgraph_engine" / "context_sync" / "architecture" / "preference_tracker.py"


def _load_module():
    """Load preference_tracker by path, as session_loader does at runtime."""
    spec = importlib.util.spec_from_file_location("preference_tracker_under_test", _MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def tracker():
    """A freshly loaded module, so constant patching cannot leak between tests."""
    return _load_module()


def _make_sessions(root, count, marker="skill-marker", body_bytes=64):
    """Create ``count`` session directories, oldest first by mtime."""
    import os
    import time

    for i in range(count):
        d = root / ("SESSION-%03d" % i)
        d.mkdir()
        (d / "session.md").write_text(marker + " " + ("x" * body_bytes), encoding="utf-8")
        # Stagger mtimes so "newest first" has a defined answer.
        stamp = time.time() - (count - i) * 60
        os.utime(d, (stamp, stamp))
    return root


class TestTheSessionCountIsBounded:
    """An unbounded scan is what made the pipeline slower on every run."""

    def test_only_the_newest_sessions_are_read(self, tracker, tmp_path):
        tracker.MAX_SESSIONS_SCANNED = 5
        _make_sessions(tmp_path, 20)
        texts = tracker._collect_session_texts(tmp_path)
        assert len(texts) == 5

    def test_without_the_cap_all_of_them_would_be_read(self, tracker, tmp_path):
        """The half that proves the cap is doing the work.

        Without this, the test above passes on any history small enough to fit
        under the cap anyway -- which is every history, right up until the one
        that matters.
        """
        tracker.MAX_SESSIONS_SCANNED = 10**9
        _make_sessions(tmp_path, 20)
        texts = tracker._collect_session_texts(tmp_path)
        assert len(texts) == 20

    def test_the_oldest_sessions_are_the_ones_dropped(self, tracker, tmp_path):
        """Recency is the point: preferences are about behaviour now."""
        import os
        import time

        tracker.MAX_SESSIONS_SCANNED = 2
        for i, name in enumerate(("oldest", "middle", "newest")):
            d = tmp_path / name
            d.mkdir()
            (d / "s.md").write_text(name, encoding="utf-8")
            stamp = time.time() - (3 - i) * 3600
            os.utime(d, (stamp, stamp))
        texts = tracker._collect_session_texts(tmp_path)
        assert set(texts) == {"newest", "middle"}
        assert "oldest" not in texts


class TestPerFileBytesAreBounded:
    """One 159 MB log must not be read whole to find a skill name in it."""

    def test_a_large_file_is_truncated(self, tracker, tmp_path):
        tracker.MAX_FILE_BYTES = 100
        d = tmp_path / "SESSION-big"
        d.mkdir()
        (d / "huge.log").write_text("y" * 5000, encoding="utf-8")
        texts = tracker._collect_session_texts(tmp_path)
        assert len(texts) == 1
        assert len(texts[0]) == 100

    def test_a_small_file_is_read_whole(self, tracker, tmp_path):
        """The half that fails if truncation were unconditional."""
        tracker.MAX_FILE_BYTES = 100
        d = tmp_path / "SESSION-small"
        d.mkdir()
        (d / "small.md").write_text("z" * 40, encoding="utf-8")
        texts = tracker._collect_session_texts(tmp_path)
        assert texts == ["z" * 40]


class TestTheCapAnnouncesItself:
    """A cap that hides its size makes a sample read as if it were complete."""

    def test_skipped_sessions_are_reported(self, tracker, tmp_path, capsys):
        tracker.MAX_SESSIONS_SCANNED = 3
        _make_sessions(tmp_path, 10)
        tracker._collect_session_texts(tmp_path)
        assert "skipped 7 older session" in capsys.readouterr().err

    def test_nothing_is_reported_when_nothing_was_cut(self, tracker, tmp_path, capsys):
        """The half that fails if the notice were unconditional."""
        tracker.MAX_SESSIONS_SCANNED = 100
        _make_sessions(tmp_path, 3)
        tracker._collect_session_texts(tmp_path)
        assert "preference_tracker" not in capsys.readouterr().err


class TestItStillWorksOnOrdinaryInput:
    """The bounds must not change the answer for a normal history."""

    def test_loose_files_and_session_dirs_are_both_read(self, tracker, tmp_path):
        (tmp_path / "loose.md").write_text("loose-content", encoding="utf-8")
        d = tmp_path / "SESSION-1"
        d.mkdir()
        (d / "inner.json").write_text("inner-content", encoding="utf-8")
        texts = tracker._collect_session_texts(tmp_path)
        assert set(texts) == {"loose-content", "inner-content"}

    def test_a_missing_directory_returns_empty(self, tracker, tmp_path):
        assert tracker._collect_session_texts(tmp_path / "nope") == []

    def test_non_text_extensions_are_ignored(self, tracker, tmp_path):
        d = tmp_path / "SESSION-1"
        d.mkdir()
        (d / "keep.md").write_text("keep", encoding="utf-8")
        (d / "skip.pkl").write_text("skip", encoding="utf-8")
        assert tracker._collect_session_texts(tmp_path) == ["keep"]

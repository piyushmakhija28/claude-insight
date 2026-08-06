"""Tests for the NFR-1 external driver.

The driver exists because `MeasurementSession`'s observer mode needs something to
call `mark_tool_call()` once per real tool call, and nothing shipped that. So the
thing these tests must establish first is that the driver COUNTS, and second that
it counts only what the criterion means by a tool call.

Every positive assertion is paired with a negative that proves it can fail, and
the filters are paired with specificity tests proving they do not swallow the
events they are meant to keep -- a driver that counted nothing would satisfy every
exclusion test on its own.
"""

import json
import os
import sys

import pytest

_TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
if _TESTS_DIR not in sys.path:
    sys.path.insert(0, _TESTS_DIR)

from nfr1 import driver  # noqa: E402

SESSION = "session-under-measurement"
OTHER_SESSION = "some-other-session"


def assistant_record(tool_ids, session_id=SESSION, sidechain=False, extra_blocks=()):
    """Build one transcript record carrying the given tool-use blocks.

    Args:
        tool_ids: Ids for the tool_use blocks to include.
        session_id: Session id to stamp on the record.
        sidechain: Whether to mark the record as a subagent turn.
        extra_blocks: Additional content blocks to include verbatim.

    Returns:
        str: The record as a JSONL line, newline included.
    """
    blocks = [{"type": "tool_use", "id": tid, "name": "Bash", "input": {}} for tid in tool_ids]
    blocks.extend(extra_blocks)
    record = {
        "type": "assistant",
        "sessionId": session_id,
        "timestamp": "2026-08-05T00:00:00Z",
        "isSidechain": sidechain,
        "message": {"content": blocks},
    }
    return json.dumps(record) + "\n"


class TestTheTranscriptDirectoryIsResolvedCorrectly:
    """The path must match what Claude Code actually created, not a plausible guess.

    The first version of this resolver was never tested and produced a directory
    that does not exist. Its whole failure mode was silence: no transcript found,
    nothing observed, no error. So the load-bearing test here is the last one,
    which checks the transform against the real filesystem.
    """

    def test_a_windows_drive_letter_yields_a_doubled_hyphen(self):
        slug = driver.project_slug("C:" + os.sep + "Users" + os.sep + "x")
        assert slug.startswith("C--Users"), slug

    def test_dots_in_a_directory_name_become_hyphens(self):
        slug = driver.project_slug("C:" + os.sep + "w" + os.sep + "tool-4.27.0-new")
        assert "4-27-0-new" in slug, slug
        assert "." not in slug, slug

    def test_the_home_override_is_honoured(self):
        path = driver.transcript_dir_for("C:" + os.sep + "w", home="/tmp/h")
        assert path.startswith(os.path.join("/tmp/h", ".claude", "projects"))

    def test_the_slug_matches_the_directory_claude_code_really_made(self):
        """The check that the earlier version would have failed.

        Skipped rather than asserted-around when the directory is absent, because
        on a machine that has never run Claude Code against this checkout there is
        nothing to compare with -- and inventing a pass there is the failure this
        whole harness exists to avoid.
        """
        repo_root = os.path.dirname(_TESTS_DIR)
        resolved = driver.transcript_dir_for(repo_root)
        if not os.path.isdir(os.path.dirname(resolved)):
            pytest.skip("no ~/.claude/projects on this machine")
        if not os.path.isdir(resolved):
            pytest.fail(
                "computed transcript directory does not exist: %s\nsiblings: %s"
                % (resolved, sorted(os.listdir(os.path.dirname(resolved)))[:5])
            )
        assert os.path.isdir(resolved)


class TestExtractionCounts:
    """The driver must see a tool call at all."""

    def test_a_tool_use_block_is_extracted(self):
        events = driver.iter_tool_use_events(assistant_record(["t1"]), SESSION)
        assert [e["id"] for e in events] == ["t1"]

    def test_several_blocks_in_one_record_all_count(self):
        """One assistant turn can issue more than one tool call."""
        events = driver.iter_tool_use_events(assistant_record(["t1", "t2", "t3"]), SESSION)
        assert [e["id"] for e in events] == ["t1", "t2", "t3"]

    def test_the_extractor_can_return_nothing(self):
        """Paired negative: a record with no tool_use yields no events."""
        line = assistant_record([], extra_blocks=({"type": "text", "text": "hello"},))
        assert driver.iter_tool_use_events(line, SESSION) == []


class TestExtractionIsSelective:
    """It must count only what the criterion means, in both directions."""

    def test_another_session_is_not_counted(self):
        line = assistant_record(["t1"], session_id=OTHER_SESSION)
        assert driver.iter_tool_use_events(line, SESSION) == []

    def test_the_session_filter_is_not_a_blanket_reject(self):
        """Specificity: the same record under the measured session DOES count."""
        line = assistant_record(["t1"], session_id=SESSION)
        assert len(driver.iter_tool_use_events(line, SESSION)) == 1

    def test_sidechain_records_are_excluded_by_default(self):
        line = assistant_record(["t1"], sidechain=True)
        assert driver.iter_tool_use_events(line, SESSION) == []

    def test_sidechains_count_when_the_caller_asks(self):
        """The exclusion is a choice, not a hard-coded truth."""
        line = assistant_record(["t1"], sidechain=True)
        assert len(driver.iter_tool_use_events(line, SESSION, include_sidechains=True)) == 1

    def test_a_non_assistant_record_carrying_a_tool_use_block_is_not_counted(self):
        """The record-type filter must be what excludes it, not an empty block list.

        Measured against a real 23 MB transcript, all 1187 tool_use blocks sat in
        assistant records, so this filter discriminates nothing on today's data and
        a fixture drawn from real records cannot exercise it. The block below is
        therefore synthetic: it asserts the filter's contract directly, so that a
        future record type carrying tool_use blocks -- or a mutation deleting the
        type check -- is caught rather than silently counted.
        """
        line = (
            json.dumps(
                {
                    "type": "user",
                    "sessionId": SESSION,
                    "message": {"content": [{"type": "tool_use", "id": "t1", "name": "Bash"}]},
                }
            )
            + "\n"
        )
        assert driver.iter_tool_use_events(line, SESSION) == []

    def test_an_assistant_record_with_that_same_block_is_counted(self):
        """Specificity: only the record type differs between this and the test above."""
        assert len(driver.iter_tool_use_events(assistant_record(["t1"]), SESSION)) == 1

    def test_a_malformed_line_is_skipped_rather_than_fatal(self):
        chunk = "{not json\n" + assistant_record(["t1"])
        assert [e["id"] for e in driver.iter_tool_use_events(chunk, SESSION)] == ["t1"]


class TestTailReadsOnlyWhatIsNew:
    """The tail must not re-count history, nor miss a split write."""

    def test_pre_existing_content_is_not_counted(self, tmp_path):
        path = tmp_path / "t.jsonl"
        path.write_text(assistant_record(["old"]), encoding="utf-8")
        tail = driver.TranscriptTail(str(path), SESSION)
        assert tail.poll() == []

    def test_appended_events_are_returned(self, tmp_path):
        path = tmp_path / "t.jsonl"
        path.write_text(assistant_record(["old"]), encoding="utf-8")
        tail = driver.TranscriptTail(str(path), SESSION)
        with open(str(path), "a", encoding="utf-8") as handle:
            handle.write(assistant_record(["new"]))
        assert [e["id"] for e in tail.poll()] == ["new"]

    def test_the_same_event_is_never_returned_twice(self, tmp_path):
        path = tmp_path / "t.jsonl"
        path.write_text("", encoding="utf-8")
        tail = driver.TranscriptTail(str(path), SESSION)
        with open(str(path), "a", encoding="utf-8") as handle:
            handle.write(assistant_record(["t1"]))
        assert len(tail.poll()) == 1
        assert tail.poll() == []

    def test_a_half_written_line_is_held_until_complete(self, tmp_path):
        """A record split across two flushes is parsed once, whole."""
        path = tmp_path / "t.jsonl"
        path.write_text("", encoding="utf-8")
        tail = driver.TranscriptTail(str(path), SESSION)
        line = assistant_record(["t1"])
        head, rest = line[:40], line[40:]
        with open(str(path), "a", encoding="utf-8") as handle:
            handle.write(head)
        assert tail.poll() == [], "a partial line must not yield an event"
        with open(str(path), "a", encoding="utf-8") as handle:
            handle.write(rest)
        assert [e["id"] for e in tail.poll()] == ["t1"]


class TestARewrittenTranscriptVoidsTheWindow:
    """Append-only is an assumption, so it is checked rather than trusted."""

    def _tail_with_history(self, tmp_path, ids):
        """Build a tail that has already consumed one appended record.

        Args:
            tmp_path: pytest temporary directory.
            ids: Tool-use ids for the record to append and consume.

        Returns:
            tuple: ``(path, tail)`` with the tail positioned past the record.
        """
        path = tmp_path / "t.jsonl"
        path.write_text("", encoding="utf-8")
        tail = driver.TranscriptTail(str(path), SESSION)
        with open(str(path), "a", encoding="utf-8") as handle:
            handle.write(assistant_record(ids))
        assert len(tail.poll()) == len(ids), "setup must consume the appended record"
        return path, tail

    def test_a_shrinking_transcript_raises(self, tmp_path):
        path, tail = self._tail_with_history(tmp_path, ["t1", "t2", "t3"])
        path.write_text("", encoding="utf-8")
        with pytest.raises(driver.TranscriptRewritten):
            tail.poll()

    def test_a_same_or_larger_rewrite_also_raises(self, tmp_path):
        """The case a size check alone cannot see -- and the bug that found it.

        Rewriting one three-call record as two one-call records leaves the file
        no smaller, so a shrink check passes it and the tail resumes reading from
        an offset that now lands mid-record. The anchor check is what catches it.
        """
        path, tail = self._tail_with_history(tmp_path, ["t1", "t2", "t3"])
        rewritten = assistant_record(["t1"]) + assistant_record(["t4"])
        path.write_text(rewritten, encoding="utf-8")
        assert len(rewritten.encode()) >= tail._offset, "fixture must not shrink the file"
        with pytest.raises(driver.TranscriptRewritten):
            tail.poll()

    def test_an_ordinary_append_does_not_raise(self, tmp_path):
        """Specificity: the integrity check must not fire on normal growth.

        Without this, a tail that raised on every poll would satisfy both tests
        above while making the driver useless.
        """
        path, tail = self._tail_with_history(tmp_path, ["t1"])
        with open(str(path), "a", encoding="utf-8") as handle:
            handle.write(assistant_record(["t2"]))
        assert [e["id"] for e in tail.poll()] == ["t2"]

    def test_repeated_appends_keep_the_anchor_in_step(self, tmp_path):
        """The anchor advances with the offset, so it must survive many polls."""
        path, tail = self._tail_with_history(tmp_path, ["t0"])
        for index in range(5):
            with open(str(path), "a", encoding="utf-8") as handle:
                handle.write(assistant_record(["t%d" % (index + 1)]))
            assert [e["id"] for e in tail.poll()] == ["t%d" % (index + 1)]

    def test_the_void_propagates_out_of_drive(self, tmp_path):
        """A rewritten transcript must not be downgraded into a short window.

        max_polls is not decoration. Without it the loop's only exit is the
        exception under test, so a regression that stops raising turns this into
        an infinite busy-loop rather than a failure -- a hung CI job instead of a
        red one. A mutation run found exactly that and burned seven minutes of
        CPU proving it.
        """
        path, tail = self._tail_with_history(tmp_path, ["t1"])
        path.write_text("", encoding="utf-8")
        session = _FakeSession()
        with pytest.raises(driver.TranscriptRewritten):
            driver.drive(session, tail, 10, max_polls=3, sleep=lambda _: None)
        assert session.closed, "the window must still be closed when voided"


class _FakeSession(object):
    """Minimal stand-in recording the observer-mode calls the driver makes."""

    def __init__(self):
        self.opened = False
        self.closed = False
        self.marks = 0

    def open(self):
        self.opened = True

    def mark_tool_call(self):
        if not self.opened or self.closed:
            raise RuntimeError("mark outside an open session")
        self.marks += 1

    def close(self):
        self.closed = True
        return "measurement"


class _ScriptedTail(object):
    """Returns a fixed sequence of poll results, then nothing."""

    def __init__(self, batches):
        self.batches = list(batches)

    def poll(self):
        return self.batches.pop(0) if self.batches else []


class TestDriveMarksEachCall:
    """The driver's whole purpose is one mark per observed tool call."""

    def test_ten_calls_produce_ten_marks(self):
        session = _FakeSession()
        tail = _ScriptedTail([[{"id": "t%d" % i} for i in range(10)]])
        measurement, observed = driver.drive(session, tail, 10, max_polls=5, sleep=lambda _: None)
        assert session.marks == 10
        assert len(observed) == 10
        assert measurement == "measurement"

    def test_the_session_is_opened_and_closed_exactly_once(self):
        session = _FakeSession()
        tail = _ScriptedTail([[{"id": "t1"}]])
        driver.drive(session, tail, 1, max_polls=5, sleep=lambda _: None)
        assert session.opened and session.closed

    def test_marks_stop_at_the_required_count(self):
        """Over-delivery in one batch must not inflate the window."""
        session = _FakeSession()
        tail = _ScriptedTail([[{"id": "t%d" % i} for i in range(25)]])
        driver.drive(session, tail, 10, max_polls=5, sleep=lambda _: None)
        assert session.marks == 10


class TestDriveRefusesToInvent:
    """A short window must report what it saw, not what it needed."""

    def test_a_starved_window_marks_only_what_arrived(self):
        session = _FakeSession()
        tail = _ScriptedTail([[{"id": "t1"}, {"id": "t2"}]])
        _, observed = driver.drive(session, tail, 10, max_polls=3, sleep=lambda _: None)
        assert session.marks == 2
        assert len(observed) == 2

    def test_the_session_is_still_closed_when_starved(self):
        """A bound must not leak an open session and its sampler thread."""
        session = _FakeSession()
        _, _ = driver.drive(session, _ScriptedTail([]), 10, max_polls=2, sleep=lambda _: None)
        assert session.closed

    def test_the_session_is_closed_even_if_polling_raises(self):
        class _Exploding(object):
            def poll(self):
                raise RuntimeError("probe failed")

        session = _FakeSession()
        with pytest.raises(RuntimeError):
            driver.drive(session, _Exploding(), 10, sleep=lambda _: None)
        assert session.closed, "a failed poll must not leave the window open"


class TestBoundsAreOptIn:
    """Neither bound may be a hidden wall-clock default."""

    def test_no_deadline_is_applied_unless_asked(self):
        """Two empty polls must not end the window; only a bound or the count may.

        A generous max_polls is kept so a regression fails instead of hanging. It
        does not weaken the claim: what is being denied here is a hidden
        wall-clock deadline, not a poll budget the caller asked for.
        """
        session = _FakeSession()
        tail = _ScriptedTail([[], [], [{"id": "t1"}]])
        _, observed = driver.drive(session, tail, 1, max_polls=50, sleep=lambda _: None)
        assert len(observed) == 1, "polling must continue across empty polls until satisfied"

    def test_an_explicit_deadline_stops_the_window(self):
        session = _FakeSession()
        _, observed = driver.drive(session, _ScriptedTail([]), 10, deadline=0.0, sleep=lambda _: None)
        assert observed == []


class TestAnchoringAtTheCurrentAssistantRecord:
    """A window opened at EOF cannot see the calls of the record that launched it.

    That is not cosmetic. The criterion wants ten tool calls inside ONE response turn,
    and the retained Stop hook fires at every turn boundary, so launching in one turn
    and calling in the next produces a window the turn-boundary guard rejects -- which
    is exactly what happened on the first attempt at a real measurement. Anchoring at
    the last assistant record is what lets a single message do both.
    """

    def test_the_offset_finder_locates_the_last_assistant_record(self, tmp_path):
        """Written as bytes on purpose.

        Real transcripts are LF-only -- measured against a live one -- but
        Path.write_text translates newlines on Windows, which silently shifts every
        offset this test asserts on and makes the fixture disagree with production.
        """
        path = tmp_path / "t.jsonl"
        first = assistant_record(["a1"])
        user_line = json.dumps({"type": "user", "sessionId": SESSION}) + "\n"
        second = assistant_record(["b1"])
        path.write_bytes((first + user_line + second).encode("utf-8"))
        offset = driver.last_assistant_record_offset(str(path))
        assert offset == len((first + user_line).encode("utf-8"))

    def test_a_crlf_transcript_is_still_located_correctly(self, tmp_path):
        """Transcripts are LF today, but a stripped record must not depend on that."""
        path = tmp_path / "t.jsonl"
        first = assistant_record(["a1"]).replace("\n", "\r\n")
        second = assistant_record(["b1"]).replace("\n", "\r\n")
        path.write_bytes((first + second).encode("utf-8"))
        assert driver.last_assistant_record_offset(str(path)) == len(first.encode("utf-8"))

    def test_anchoring_counts_the_launching_records_calls(self, tmp_path):
        path = tmp_path / "t.jsonl"
        path.write_text(assistant_record(["t1", "t2", "t3"]), encoding="utf-8")
        tail = driver.TranscriptTail(str(path), SESSION, start_offset=driver.last_assistant_record_offset(str(path)))
        assert [e["id"] for e in tail.poll()] == ["t1", "t2", "t3"]

    def test_without_anchoring_the_same_calls_are_invisible(self, tmp_path):
        """The paired half, and the defect this option exists to fix."""
        path = tmp_path / "t.jsonl"
        path.write_text(assistant_record(["t1", "t2", "t3"]), encoding="utf-8")
        tail = driver.TranscriptTail(str(path), SESSION)
        assert tail.poll() == []

    def test_an_empty_transcript_anchors_at_zero(self, tmp_path):
        path = tmp_path / "t.jsonl"
        path.write_text("", encoding="utf-8")
        assert driver.last_assistant_record_offset(str(path)) == 0

    def test_a_transcript_with_no_assistant_record_anchors_at_zero(self, tmp_path):
        path = tmp_path / "t.jsonl"
        path.write_text(json.dumps({"type": "user", "sessionId": SESSION}) + "\n", encoding="utf-8")
        assert driver.last_assistant_record_offset(str(path)) == 0

    def test_the_finder_widens_its_window_past_a_large_trailing_record(self, tmp_path):
        """The search reads backwards in windows, so a big tail must not hide the anchor.

        The target sits AFTER a leading filler line on purpose. An earlier version of
        this test put it at offset 0, where "found it" and "gave up and returned 0" are
        the same answer -- a mutation that removed the widening loop entirely passed it.
        """
        path = tmp_path / "t.jsonl"
        head = json.dumps({"type": "user", "sessionId": SESSION, "pad": "h" * 100}) + "\n"
        target = assistant_record(["t1"])
        filler = json.dumps({"type": "user", "sessionId": SESSION, "pad": "x" * 4000}) + "\n"
        path.write_bytes((head + target + filler * 400).encode("utf-8"))
        found = driver.last_assistant_record_offset(str(path), window=1024)
        assert found == len(head.encode("utf-8"))
        assert found != 0, "a fixture whose answer is 0 cannot detect a finder that gives up"


class TestSkippingTheLaunchingCall:
    """The launching call began before the window opened and must not be counted."""

    def test_skip_leading_drops_exactly_that_many(self, tmp_path):
        path = tmp_path / "t.jsonl"
        path.write_text(assistant_record(["launch", "t1", "t2"]), encoding="utf-8")
        tail = driver.TranscriptTail(
            str(path),
            SESSION,
            start_offset=driver.last_assistant_record_offset(str(path)),
            skip_leading=1,
        )
        assert [e["id"] for e in tail.poll()] == ["t1", "t2"]

    def test_skip_leading_zero_drops_nothing(self, tmp_path):
        """Specificity: the drop must be opt-in, not a silent off-by-one."""
        path = tmp_path / "t.jsonl"
        path.write_text(assistant_record(["launch", "t1"]), encoding="utf-8")
        tail = driver.TranscriptTail(str(path), SESSION, start_offset=driver.last_assistant_record_offset(str(path)))
        assert [e["id"] for e in tail.poll()] == ["launch", "t1"]

    def test_the_skip_budget_is_spent_once_not_per_poll(self, tmp_path):
        """A per-poll skip would silently eat one real call from every later batch."""
        path = tmp_path / "t.jsonl"
        path.write_text(assistant_record(["launch"]), encoding="utf-8")
        tail = driver.TranscriptTail(
            str(path),
            SESSION,
            start_offset=driver.last_assistant_record_offset(str(path)),
            skip_leading=1,
        )
        assert tail.poll() == []
        with open(str(path), "a", encoding="utf-8") as handle:
            handle.write(assistant_record(["t1", "t2"]))
        assert [e["id"] for e in tail.poll()] == ["t1", "t2"]

    def test_a_skip_larger_than_the_first_batch_carries_over(self, tmp_path):
        path = tmp_path / "t.jsonl"
        path.write_text(assistant_record(["a"]), encoding="utf-8")
        tail = driver.TranscriptTail(
            str(path),
            SESSION,
            start_offset=driver.last_assistant_record_offset(str(path)),
            skip_leading=2,
        )
        assert tail.poll() == []
        with open(str(path), "a", encoding="utf-8") as handle:
            handle.write(assistant_record(["b", "c"]))
        assert [e["id"] for e in tail.poll()] == ["c"]

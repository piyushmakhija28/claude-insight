"""External driver for the NFR-1 harness, reading Claude Code's own transcript.

WHY THIS EXISTS
---------------
`MeasurementSession` has two modes. Driven mode invokes a synthetic callable and
exists only for self-test. Observer mode -- the one a real NFR-1 run needs --
requires an external driver to call ``open()``, then ``mark_tool_call()`` once
per real tool call, then ``close()``. **No such driver shipped**, so the harness
could report INDETERMINATE and nothing else, whatever else was fixed. That is
why issue #259 stayed open with the harness built.

The natural place to call ``mark_tool_call()`` was the PostToolUse hook, which
fired once per tool call -- and that hook was deleted by the release the
measurement exists to justify. The signal used here is written by Claude Code
itself and survives that deletion: the session transcript at
``~/.claude/projects/<slug>/<session-id>.jsonl``, whose ``assistant`` records
carry ``message.content[]`` blocks of ``type == "tool_use"``.

WHAT IT COUNTS, AND WHAT IT REFUSES TO COUNT
--------------------------------------------
Sidechain records -- subagent turns -- are excluded by default. A subagent's tool
calls belong to its own context, not to the session under measurement, and
counting them would inflate the window with work the user never issued. The
choice is a parameter, because it changes what the number means.

Only ``assistant`` records are read. Measured against a real 23 MB transcript,
all 1187 tool-use blocks were in assistant records and none were sidechains, so
that filter discriminates nothing on today's data. It is kept as a contract, not
as an observed necessity, and its test says so.

WHY A REWRITE IS FATAL RATHER THAN RECOVERABLE
-----------------------------------------------
The tail assumes the transcript is append-only, and it verifies that assumption
on every poll instead of trusting it: it re-reads the bytes immediately before
its offset and compares them to what it consumed. A mismatch means the file was
rewritten underneath the window.

That one check is the whole mechanism. A separate size-shrink check was written
first and then removed: a truncated file returns a short read at the same
offset, so the comparison already catches it, and a mutation run confirmed the
size check could be deleted without any test noticing. Two checks where one
carries the weight is one untested branch, not defence in depth.

That is not recoverable. Re-scanning from the start would sweep up records
written before the window opened, and there is no way to tell those from calls
the window should count. So the tail raises. A void observation must stay void:
the alternative is a number nobody can defend, which is the one outcome NFR-1
forbids.

WHAT IT WILL NOT DO
-------------------
It will not fabricate a count. If the window ends having seen fewer than the
required number of tool calls, that is what it reports, and the harness turns
that into INDETERMINATE rather than a verdict. There is no default wall-clock
deadline: bounding this by time would reintroduce exactly the temporal proxy
NFR-2 exists to remove, so the bound is an explicit poll budget or an explicit
deadline the caller opts into.
"""

import json
import os
import time

DEFAULT_POLL_SECONDS = 0.25
ANCHOR_BYTES = 64


class TranscriptRewritten(Exception):
    """Raised when the transcript stopped being append-only mid-window.

    Carries no recovery path by design: see the module docstring.
    """


def project_slug(project_root):
    """Return the directory name Claude Code derives from a project path.

    Every character that cannot appear in a directory name, plus the dot, is
    replaced by a hyphen -- one hyphen each, with no collapsing. A Windows drive
    letter therefore yields a doubled hyphen (``C:\\Users`` -> ``C--Users``) and a
    dotted directory keeps a hyphen per dot, which is what makes the real
    directory on this machine end ``4-4-27-0-new`` rather than ``4-4.27.0-new``.

    An earlier version of this function dropped the colon instead of replacing it
    and left dots alone. It produced a path that did not exist, so the driver
    found no transcript and observed nothing -- silently, and on the real machine
    only. It was untested, which is why nothing said so.

    Args:
        project_root: Absolute path of the project checkout.

    Returns:
        str: The slug Claude Code uses for that project's transcript directory.
    """
    resolved = os.path.abspath(project_root)
    for char in (":", os.sep, "/", "."):
        resolved = resolved.replace(char, "-")
    return resolved


def transcript_dir_for(project_root, home=None):
    """Return the directory Claude Code writes this project's transcripts to.

    Args:
        project_root: Absolute path of the repository checkout.
        home: Override for the user home directory, for tests.

    Returns:
        str: Absolute path of the per-project transcript directory.
    """
    base = home if home is not None else os.path.expanduser("~")
    return os.path.join(base, ".claude", "projects", project_slug(project_root))


def newest_transcript(directory):
    """Return the most recently modified transcript in a directory.

    Args:
        directory: Directory holding ``*.jsonl`` transcripts.

    Returns:
        str or None: Path of the newest transcript, or None when there is none.
    """
    if not os.path.isdir(directory):
        return None
    candidates = [os.path.join(directory, name) for name in os.listdir(directory) if name.endswith(".jsonl")]
    if not candidates:
        return None
    return max(candidates, key=lambda path: os.stat(path).st_mtime)


def session_id_from_path(path):
    """Return the session id Claude Code encoded in a transcript filename.

    Args:
        path: Path of a ``<session-id>.jsonl`` transcript.

    Returns:
        str: The session id.
    """
    return os.path.splitext(os.path.basename(path))[0]


def last_assistant_record_offset(path, window=1 << 20, max_window=1 << 25):
    """Return the byte offset where the transcript's last assistant record begins.

    A window opened at end-of-file cannot see the tool calls of the assistant record
    that launched it, because that record was written before the tool ran. That is not
    a detail: the criterion requires ten tool calls inside ONE response turn, and the
    retained Stop hook fires at every turn boundary, so launching in one turn and
    calling in the next produces a window the turn-boundary guard correctly rejects.
    Anchoring here instead lets a single assistant message carry both the launch and
    the calls.

    The file is read backwards in growing windows rather than whole, because a real
    transcript runs to tens of megabytes.

    Args:
        path: Transcript path.
        window: Initial number of trailing bytes to search.
        max_window: Give up and return 0 beyond this.

    Returns:
        int: Offset of the last assistant record, or 0 if none was found.
    """
    size = os.stat(path).st_size
    while window <= max_window:
        start = max(0, size - window)
        with open(path, "rb") as handle:
            handle.seek(start)
            chunk = handle.read()
        if start > 0:
            cut = chunk.find(b"\n")
            if cut == -1:
                window *= 4
                continue
            offset_base = start + cut + 1
            chunk = chunk[cut + 1 :]
        else:
            offset_base = 0
        found = None
        position = 0
        while True:
            newline = chunk.find(b"\n", position)
            if newline == -1:
                break
            line = chunk[position:newline].strip()
            if line.startswith(b"{"):
                try:
                    record = json.loads(line.decode("utf-8", errors="replace"))
                except ValueError:
                    record = None
                if isinstance(record, dict) and record.get("type") == "assistant":
                    found = offset_base + position
            position = newline + 1
        if found is not None:
            return found
        if start == 0:
            return 0
        window *= 4
    return 0


def _is_assistant_record(line):
    """Return whether a raw JSONL line parses to an assistant record.

    Parsed rather than substring-matched: a tool call whose command text happened
    to contain the words being searched for would otherwise be mistaken for the
    record type itself.

    Args:
        line: One raw line of the transcript, without its newline.

    Returns:
        bool
    """
    stripped = line.strip()
    if not stripped.startswith(b"{"):
        return False
    try:
        record = json.loads(stripped.decode("utf-8", errors="replace"))
    except ValueError:
        return False
    return isinstance(record, dict) and record.get("type") == "assistant"


def find_launching_record_offset(path, needle, window=1 << 20, max_window=1 << 25):
    """Return the offset of the assistant record that launched this measurement.

    Anchoring at the LAST assistant record was wrong, and a real cold run proved it.
    Claude Code writes **one assistant record per tool call**, and it writes all of a
    response's records **before** the tools execute. Eleven calls issued in a single
    response therefore appear as eleven records, all present on disk seconds before
    the launcher's own process opens the window. Anchoring at the last of them lands
    past every call in the batch: the run counted zero and polled its whole budget.

    So the anchor has to be the record that launched THIS process, not the newest
    one. The needle is a distinctive substring of this invocation -- the --json-out
    path serves, being unique per run -- and the search takes the LAST record
    containing it, so a repeated run anchors on its own launch rather than an
    earlier one that used the same output path.

    Args:
        path: Transcript path.
        needle: Substring identifying this run's launching tool call.
        window: Initial number of trailing bytes to search.
        max_window: Give up beyond this.

    Returns:
        int or None: Offset of the launching record, or None if it was not found.
    """
    if not needle:
        return None
    probe = needle.encode("utf-8")
    size = os.stat(path).st_size
    while window <= max_window:
        start = max(0, size - window)
        with open(path, "rb") as handle:
            handle.seek(start)
            chunk = handle.read()
        if start > 0:
            cut = chunk.find(b"\n")
            if cut == -1:
                window *= 4
                continue
            offset_base = start + cut + 1
            chunk = chunk[cut + 1 :]
        else:
            offset_base = 0
        found = None
        position = 0
        while True:
            newline = chunk.find(b"\n", position)
            if newline == -1:
                break
            line = chunk[position:newline]
            if probe in line and _is_assistant_record(line):
                found = offset_base + position
            position = newline + 1
        if found is not None:
            return found
        if start == 0:
            return None
        window *= 4
    return None


def iter_tool_use_events(chunk, session_id=None, include_sidechains=False):
    """Extract tool-use events from a chunk of transcript text.

    Args:
        chunk: Text containing zero or more whole JSONL records.
        session_id: When given, only records carrying this session id count.
        include_sidechains: Whether subagent (sidechain) records count.

    Returns:
        list: One dict per tool-use block, with ``id``, ``name`` and ``timestamp``.
    """
    events = []
    for line in chunk.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except ValueError:
            continue
        if record.get("type") != "assistant":
            continue
        if session_id is not None and record.get("sessionId") != session_id:
            continue
        if record.get("isSidechain") and not include_sidechains:
            continue
        blocks = (record.get("message") or {}).get("content")
        if not isinstance(blocks, list):
            continue
        for block in blocks:
            if not isinstance(block, dict) or block.get("type") != "tool_use":
                continue
            events.append(
                {
                    "id": block.get("id"),
                    "name": block.get("name"),
                    "timestamp": record.get("timestamp"),
                }
            )
    return events


def iter_tool_result_ids(chunk, session_id=None, include_sidechains=False):
    """Extract the ids of tool calls that COMPLETED, from a chunk of transcript.

    A `tool_use` block records an intention and is written before the tool runs. A
    `tool_result` block, carried on a `user` record, records the completion. The
    difference decides whether a measurement window covers any work at all: a cold
    run anchored on tool_use saw all ten calls the instant it opened, because their
    records already existed, and closed after **0.19 seconds** having measured a
    window that contained none of the execution it was supposed to bracket.

    Args:
        chunk: Text containing zero or more whole JSONL records.
        session_id: When given, only records carrying this session id count.
        include_sidechains: Whether subagent records count.

    Returns:
        list: tool_use_id strings, one per completed call, in order.
    """
    completed = []
    for line in chunk.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except ValueError:
            continue
        if record.get("type") != "user":
            continue
        if session_id is not None and record.get("sessionId") != session_id:
            continue
        if record.get("isSidechain") and not include_sidechains:
            continue
        blocks = (record.get("message") or {}).get("content")
        if not isinstance(blocks, list):
            continue
        for block in blocks:
            if isinstance(block, dict) and block.get("type") == "tool_result":
                identifier = block.get("tool_use_id")
                if identifier:
                    completed.append(identifier)
    return completed


class TranscriptTail(object):
    """Yields tool-use events appended to a transcript after construction.

    The file is read in binary so that offsets are true byte offsets comparable
    with ``st_size``; a text-mode ``tell()`` returns an opaque cookie that only
    happens to look like one. Only whole lines are decoded. A trailing partial
    line stays in the buffer as bytes and is re-read on the next poll, so a
    record written across two flushes -- or split mid-character -- is parsed once
    and completely rather than being dropped or mangled.
    """

    def __init__(
        self,
        path,
        session_id=None,
        include_sidechains=False,
        start_offset=None,
        skip_leading=0,
        count_completions=False,
    ):
        self.path = path
        self.session_id = session_id
        self.include_sidechains = include_sidechains
        self.skip_leading = skip_leading
        self.count_completions = count_completions
        self._skipped = 0
        self._issued = {}
        self._reported = set()
        if start_offset is not None:
            self._offset = start_offset
        else:
            self._offset = os.stat(path).st_size if os.path.exists(path) else 0
        self._pending = b""
        self._anchor = self._read_anchor(self._offset)

    def _read_anchor(self, offset):
        """Return the bytes immediately preceding an offset, for continuity checks.

        Args:
            offset: Byte offset whose preceding bytes should be captured.

        Returns:
            bytes: Up to ANCHOR_BYTES bytes ending at the offset.
        """
        if offset <= 0 or not os.path.exists(self.path):
            return b""
        start = max(0, offset - ANCHOR_BYTES)
        with open(self.path, "rb") as handle:
            handle.seek(start)
            return handle.read(offset - start)

    def poll(self):
        """Read whatever has been appended and return the tool-use events in it.

        Returns:
            list: Events appended since the previous poll.

        Raises:
            TranscriptRewritten: If the transcript stopped being append-only.
        """
        if not os.path.exists(self.path):
            return []
        size = os.stat(self.path).st_size
        if self._read_anchor(self._offset) != self._anchor:
            raise TranscriptRewritten(
                "the {0} bytes before offset {1} changed or vanished (file is now {2} "
                "bytes); the transcript is no longer append-only".format(len(self._anchor), self._offset, size)
            )
        if size == self._offset:
            return []
        with open(self.path, "rb") as handle:
            handle.seek(self._offset)
            chunk = handle.read()
        self._offset += len(chunk)
        self._anchor = self._read_anchor(self._offset)
        chunk = self._pending + chunk
        cut = chunk.rfind(b"\n")
        if cut == -1:
            self._pending = chunk
            return []
        self._pending = chunk[cut + 1 :]
        whole = chunk[: cut + 1].decode("utf-8", errors="replace")
        events = iter_tool_use_events(whole, self.session_id, self.include_sidechains)
        events = self._drop_leading(events)
        if not self.count_completions:
            return events
        for event in events:
            if event.get("id"):
                self._issued[event["id"]] = event
        matured = []
        for identifier in iter_tool_result_ids(whole, self.session_id, self.include_sidechains):
            if identifier in self._issued and identifier not in self._reported:
                self._reported.add(identifier)
                matured.append(self._issued[identifier])
        return matured

    def _drop_leading(self, events):
        """Discard the first skip_leading events ever seen by this tail.

        Anchoring at the current assistant record makes that record's own tool calls
        visible, and one of them is the call that launched the measurement. It began
        before the window opened, so counting it would credit the window with a call it
        did not contain. Dropping it is explicit rather than inferred, because the tail
        cannot know its own tool-use id.

        Args:
            events: Events just read, in order.

        Returns:
            list: The events that remain after the leading ones are discarded.
        """
        if self._skipped >= self.skip_leading:
            return events
        remaining = self.skip_leading - self._skipped
        dropped = min(remaining, len(events))
        self._skipped += dropped
        return events[dropped:]


def drive(session, tail, required, poll_seconds=DEFAULT_POLL_SECONDS, max_polls=None, deadline=None, sleep=None):
    """Run one observer-mode window, marking each real tool call as it appears.

    The session is opened, polled until the required number of tool calls has
    been observed or a bound is reached, then closed. Both bounds are optional
    and default to unbounded, because bounding a measurement by wall clock is the
    temporal proxy NFR-2 exists to remove.

    A ``TranscriptRewritten`` from the tail is deliberately not caught here. The
    session is still closed, but the caller is told the observation is void
    rather than being handed a partial count that looks like a short window.

    Args:
        session: An unopened ``MeasurementSession``.
        tail: A ``TranscriptTail`` positioned at the current end of the transcript.
        required: How many tool calls the criterion requires.
        poll_seconds: Delay between polls.
        max_polls: Optional cap on poll iterations.
        deadline: Optional absolute ``time.time()`` value after which to stop.
        sleep: Injectable sleep, for tests.

    Returns:
        tuple: ``(measurement, observed_events)``.
    """
    naptime = sleep if sleep is not None else time.sleep
    observed = []
    session.open()
    try:
        polls = 0
        while len(observed) < required:
            if max_polls is not None and polls >= max_polls:
                break
            if deadline is not None and time.time() >= deadline:
                break
            for event in tail.poll():
                observed.append(event)
                session.mark_tool_call()
                if len(observed) >= required:
                    break
            polls += 1
            if len(observed) < required:
                naptime(poll_seconds)
    finally:
        measurement = session.close()
    return measurement, observed

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


class TranscriptTail(object):
    """Yields tool-use events appended to a transcript after construction.

    The file is read in binary so that offsets are true byte offsets comparable
    with ``st_size``; a text-mode ``tell()`` returns an opaque cookie that only
    happens to look like one. Only whole lines are decoded. A trailing partial
    line stays in the buffer as bytes and is re-read on the next poll, so a
    record written across two flushes -- or split mid-character -- is parsed once
    and completely rather than being dropped or mangled.
    """

    def __init__(self, path, session_id=None, include_sidechains=False):
        self.path = path
        self.session_id = session_id
        self.include_sidechains = include_sidechains
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
        return iter_tool_use_events(whole, self.session_id, self.include_sidechains)


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

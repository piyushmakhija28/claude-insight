"""Concurrency-aware writer for a Claude Code settings JSON file.

WHY THIS IS NOT ``AtomicJsonStore``
-----------------------------------
``AtomicJsonStore`` (``src/mcp/base/persistence.py:27`` in this repo, and
``mcp_base/persistence.py:26`` in the sibling ``mcp-base`` checkout) already
implements a write-to-temp-then-rename read-modify-write, and it was evaluated
first. It is not reused here for two independent reasons, either of which alone
would be decisive.

1. FAILURE MODE. ``AtomicJsonStore.load()`` returns a caller-supplied default
   when the target file is missing OR unparseable OR unreadable, silently and
   with no distinction between those cases. ``modify()`` then writes that
   default back. Against a cache or a state file that is correct. Against
   ``settings.json`` it IS the ADV-008 clobber: a user who leaves a trailing
   comma in their settings would have the entire file replaced by whatever
   subset this command happened to construct. This module refuses to write when
   an existing file does not parse, and says so, because a live configuration
   file has no safe default.

2. REACHABILITY. ``mcp-base`` is vendored by copy. Neither copy is importable
   from an installed plugin, whose files live under the plugin manager's cache
   directory with no relationship to this repository or to the sibling
   checkout. An installed ``register-mcp`` therefore cannot import it at all.

If ``AtomicJsonStore`` is ever hardened against reason 1, BOTH vendored copies
need the change; fixing one reaches nothing else.

WHAT THIS MODULE GUARANTEES, AND WHAT IT DOES NOT
-------------------------------------------------
The write is a merge against a fresh read (HLD section 8.4) with an added
content-hash condition: the bytes read at the start of the cycle must still be
the bytes on disk immediately before the rename, or the cycle restarts. That is
optimistic concurrency, which detects a competing write rather than silently
losing it.

It is NOT a lock. A residual window remains between the final verification read
and ``os.replace``. A competing writer whose own rename lands inside that window
still produces a lost update. Only OS-level locking eliminates the window rather
than narrowing it, and this module does not take one, because the contending
writers here are interactive commands a user runs by hand rather than a service
under load. The residual risk is stated rather than papered over.

Atomic rename is used as well, but for the different property it actually
provides: no reader ever observes a half-written file. It does not address the
lost-update race above and is not claimed to.
"""

import hashlib
import json
import os
import tempfile
from pathlib import Path

MERGE_ATTEMPTS = 4


class SettingsWriteError(Exception):
    """Base class for every failure this module raises."""


class SettingsUnreadable(SettingsWriteError):
    """The settings file exists but cannot be used as a merge base.

    Raised when the file cannot be read, does not parse as JSON, or parses to
    something other than a JSON object. In every one of those cases the correct
    action is to refuse the write, because any default substituted here would be
    written over the user's real configuration.
    """


class ConcurrentModification(SettingsWriteError):
    """The file changed underneath every merge attempt.

    Raised after MERGE_ATTEMPTS cycles each observed a different on-disk digest
    between the base read and the pre-write verification read.
    """


class WriteResult:
    """Outcome of one merge-against-fresh-read cycle.

    Attributes:
        changed: True when bytes were written, False when the merge produced
            content identical to what was already on disk.
        attempts: Number of read-merge-verify cycles performed.
        digest_before: sha256 of the file's bytes before the write, or None
            when the file did not exist.
        digest_after: sha256 of the file's bytes after the write.
        note: Human-readable one-line summary.
    """

    def __init__(self, changed, attempts, digest_before, digest_after, note):
        """Store the outcome fields verbatim.

        Args:
            changed: Whether the file's bytes were replaced.
            attempts: Number of cycles performed.
            digest_before: Pre-write sha256 hex digest, or None.
            digest_after: Post-write sha256 hex digest.
            note: One-line summary.
        """
        self.changed = changed
        self.attempts = attempts
        self.digest_before = digest_before
        self.digest_after = digest_after
        self.note = note


def sha256_of(path):
    """Return the sha256 hex digest of a file's bytes.

    Args:
        path: Path-like pointing at the file to digest.

    Returns:
        str: Hex digest, or None when the file does not exist.
    """
    target = Path(path)
    try:
        return hashlib.sha256(target.read_bytes()).hexdigest()
    except FileNotFoundError:
        return None


def _read_base(path):
    """Read the file and return its bytes, parsed object and digest.

    Args:
        path: Path of the settings file.

    Returns:
        tuple: (dict base, str digest or None, bytes raw or None). A missing
        file yields an empty base and a None digest, which is the only case
        where an empty merge base is legitimate.

    Raises:
        SettingsUnreadable: The file exists but is unreadable, is not JSON, or
            is not a JSON object.
    """
    target = Path(path)
    try:
        raw = target.read_bytes()
    except FileNotFoundError:
        return {}, None, None
    except OSError as exc:
        raise SettingsUnreadable("cannot read {0}: {1}".format(target, exc)) from exc

    digest = hashlib.sha256(raw).hexdigest()
    try:
        parsed = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SettingsUnreadable(
            "{0} exists but does not parse as JSON ({1}); refusing to write, "
            "because writing here would replace the whole file".format(target, exc)
        ) from exc
    if not isinstance(parsed, dict):
        raise SettingsUnreadable(
            "{0} parses to {1}, not a JSON object; refusing to write".format(target, type(parsed).__name__)
        )
    return parsed, digest, raw


def _newline_style(raw):
    """Detect which line ending a file already uses.

    Rewriting a CRLF settings file with LF endings would churn every line of a
    file the command was asked to touch two keys of. Detected once and mirrored
    on output so the diff a user sees is the change they asked for.

    Args:
        raw: The file's current bytes, or None when it does not exist.

    Returns:
        str: The newline sequence to emit.
    """
    if raw and b"\r\n" in raw:
        return "\r\n"
    return "\n"


def _serialise(data, trailing_newline, newline):
    """Render a settings object back to bytes.

    Args:
        data: The merged settings dictionary.
        trailing_newline: Whether to end the output with a newline, mirroring
            whatever the file already had so a no-op round trip does not churn
            the final byte.
        newline: The line ending sequence to emit.

    Returns:
        bytes: UTF-8 encoded JSON.
    """
    text = json.dumps(data, indent=2, ensure_ascii=False)
    if newline != "\n":
        text = text.replace("\n", newline)
    if trailing_newline:
        text += newline
    return text.encode("utf-8")


def _atomic_replace(path, payload):
    """Write payload to a unique temp file in the same directory, then rename.

    A unique temp name is used rather than a fixed ``.tmp`` sibling. A fixed
    name is itself a race: two writers would write the same scratch file and one
    could rename the other's bytes into place.

    Args:
        path: Destination path.
        payload: Bytes to write.

    Returns:
        None

    Raises:
        SettingsWriteError: The rename failed, which on Windows most often means
            another process holds an open handle to the destination.
    """
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    handle, temp_name = tempfile.mkstemp(
        prefix=target.name + ".",
        suffix=".tmp",
        dir=str(target.parent),
    )
    try:
        with os.fdopen(handle, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_name, str(target))
    except OSError as exc:
        try:
            os.unlink(temp_name)
        except OSError:
            pass
        raise SettingsWriteError("could not replace {0}: {1}".format(target, exc)) from exc


def merge_write(path, merge_fn, attempts=MERGE_ATTEMPTS):
    """Apply merge_fn to a freshly read settings file and write the result.

    The cycle is: read the current bytes and digest, parse, apply merge_fn to
    the parsed object, re-read the bytes and compare digests, and only then
    rename the new content into place. A digest mismatch restarts the cycle
    rather than overwriting whatever the competing writer put there.

    merge_fn must be pure with respect to the filesystem: it may be called more
    than once, so it must not perform side effects of its own.

    Args:
        path: Path of the settings file to update.
        merge_fn: Callable taking the parsed settings dict and returning the
            dict to write. Returning the input unchanged makes the call a no-op.
        attempts: Maximum number of read-merge-verify cycles.

    Returns:
        WriteResult: Outcome of the cycle.

    Raises:
        SettingsUnreadable: The file exists but cannot serve as a merge base.
        ConcurrentModification: Every attempt observed a competing write.
        SettingsWriteError: The rename itself failed.
    """
    target = Path(path)
    last_digest = None
    for attempt in range(1, attempts + 1):
        base, digest_before, raw = _read_base(target)
        last_digest = digest_before
        trailing_newline = raw.endswith(b"\n") if raw is not None else True
        newline = _newline_style(raw)

        merged = merge_fn(json.loads(json.dumps(base)))
        if not isinstance(merged, dict):
            raise SettingsWriteError("merge function returned {0}, not a dict".format(type(merged).__name__))

        payload = _serialise(merged, trailing_newline, newline)
        if digest_before is not None and hashlib.sha256(payload).hexdigest() == digest_before:
            return WriteResult(False, attempt, digest_before, digest_before, "no change required")
        if merged == base and digest_before is not None:
            return WriteResult(False, attempt, digest_before, digest_before, "no change required")

        verify_digest = sha256_of(target)
        if verify_digest != digest_before:
            continue

        _atomic_replace(target, payload)
        return WriteResult(
            True,
            attempt,
            digest_before,
            sha256_of(target),
            "merged against a fresh read and replaced atomically",
        )

    raise ConcurrentModification(
        "{0} changed during every one of {1} merge attempts; the last digest "
        "seen was {2}. Nothing was written.".format(target, attempts, last_digest)
    )

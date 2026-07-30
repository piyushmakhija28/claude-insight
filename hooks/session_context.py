#!/usr/bin/env python
"""Canonical session identity and safe session-file I/O for all hooks.

Single source of truth for "which session am I in?". Claude Code passes a
``session_id`` field in every hook stdin payload, and that value is the only
identifier that stays stable for the whole lifetime of one conversation.
Before this module existed, seven separate resolvers each guessed the session
from a pointer file that nothing wrote, which meant every hook could disagree
with every other hook and with the pipeline.

Resolution order (first hit wins):

1. ``CLAUDE_SESSION_ID`` process environment variable, set by :func:`bind_session`
   as soon as a hook parses its stdin payload.
2. ``{memory}/.current-session.json`` pointer file (``current_session_id`` key).
3. ``{memory}/logs/session-progress.json`` legacy fallback (``session_id`` key).

This module deliberately imports nothing from the ``hooks`` package:
``ide_paths`` imports ``project_session``, which delegates here, so any import
back into the package would create a cycle.

Windows-safe: ASCII only, no Unicode characters.
"""

import json
import os
import sys
import time
from pathlib import Path

ENV_SESSION_ID = "CLAUDE_SESSION_ID"
SESSION_PREFIX = "SESSION-"
POINTER_FILENAME = ".current-session.json"
LEGACY_PROGRESS_FILENAME = "session-progress.json"
PROGRESS_FILENAME = "progress.json"

_MAX_SESSION_ID_LEN = 128
_ALLOWED_ID_CHARS = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.")
_LOCK_TIMEOUT_SEC = 5.0
_LOCK_POLL_SEC = 0.02


def get_memory_base():
    """Return the memory root directory that holds all session state.

    Mirrors the resolution used by ``ide_paths.MEMORY_BASE`` without importing
    it, so IDE-mode installations and ``CLAUDE_HOME`` overrides land in the
    same place the rest of the system uses.

    Returns:
        Path: Memory root, e.g. ``~/.claude/memory``.
    """
    data_dir = os.environ.get("CLAUDE_IDE_DATA_DIR", "").strip()
    if data_dir:
        return Path(data_dir) / "memory"

    install_dir = os.environ.get("CLAUDE_IDE_INSTALL_DIR", "").strip()
    if install_dir:
        return Path(install_dir) / "data" / "memory"

    claude_home = os.environ.get("CLAUDE_HOME", "").strip()
    if claude_home:
        return Path(claude_home) / "memory"

    return Path.home() / ".claude" / "memory"


def get_sessions_root():
    """Return the one directory under which every session folder lives.

    Both the hooks and the pipeline must agree on this path. Historically the
    hooks hardcoded ``{memory}/logs/sessions`` while an engine import fallback
    used ``~/.claude/logs/sessions``, splitting session data across two trees.

    Returns:
        Path: ``{memory}/logs/sessions``.
    """
    return get_memory_base() / "logs" / "sessions"


def get_pointer_file():
    """Return the path of the current-session pointer file.

    Returns:
        Path: ``{memory}/.current-session.json``.
    """
    return get_memory_base() / POINTER_FILENAME


def get_legacy_progress_file():
    """Return the path of the global (pre-per-session) progress file.

    Retained as a read fallback so a session that started before this module
    was introduced still resolves.

    Returns:
        Path: ``{memory}/logs/session-progress.json``.
    """
    return get_memory_base() / "logs" / LEGACY_PROGRESS_FILENAME


def normalize_session_id(raw):
    """Normalize any known session identifier form to the canonical form.

    Three formats reach this function: Claude Code's own payload UUID, the
    pipeline's ``SESSION-<timestamp>-<suffix>`` string, and the engine's
    lowercase ``session-<timestamp>-<hex>`` string. Every downstream consumer
    validates with ``startswith("SESSION-")``, so all three are canonicalized
    to that prefix rather than teaching each consumer three formats.

    The lowercase prefix is only rewritten when a timestamp follows it, which is
    what makes the engine form recognizable. Stripping it unconditionally would
    map both ``x`` and ``session-x`` onto ``SESSION-x`` and merge two distinct
    sessions into one folder.

    Repeated canonical prefixes are collapsed so a value that was double-prefixed
    by an earlier caller resolves to the same session as the clean form. No real
    session body begins with the prefix, so the collapse cannot merge two
    distinct sessions.

    Args:
        raw: Candidate identifier, may be None or any type.

    Returns:
        str: Canonical ``SESSION-...`` identifier, or "" when the input is
            missing or not usable as a directory name.
    """
    if not raw or not isinstance(raw, str):
        return ""

    candidate = raw.strip()
    if not candidate or len(candidate) > _MAX_SESSION_ID_LEN:
        return ""

    body = candidate
    while body.startswith(SESSION_PREFIX):
        body = body[len(SESSION_PREFIX) :]
    if body == candidate and candidate.lower().startswith("session-") and candidate[len("session-") :][:8].isdigit():
        body = candidate[len("session-") :]

    if not body or not set(body) <= _ALLOWED_ID_CHARS:
        return ""

    return SESSION_PREFIX + body


def bind_session(payload):
    """Bind this process to the session named in a hook payload.

    Call this immediately after parsing hook stdin. It publishes the session
    identity into the process environment so that every resolver in this
    process, and every child process it spawns, agrees on one session without
    any function signature having to thread the value through.

    Args:
        payload: Parsed hook payload dict (any dict carrying a ``session_id``
            key), or a bare session identifier string.

    Returns:
        str: The canonical session ID that was bound, or "" when the payload
            carried no usable identifier (the existing binding is left alone).
    """
    raw = ""
    if isinstance(payload, dict):
        raw = payload.get("session_id") or payload.get("sessionId") or ""
    elif isinstance(payload, str):
        raw = payload

    session_id = normalize_session_id(raw)
    if not session_id:
        return ""

    os.environ[ENV_SESSION_ID] = session_id
    return session_id


def resolve_session_id(default=""):
    """Resolve the active session ID.

    Args:
        default: Value to return when no session can be resolved. Callers that
            previously fell back to the literal string "unknown" pass it here.

    Returns:
        str: Canonical session ID, or ``default`` when unresolvable.
    """
    bound = normalize_session_id(os.environ.get(ENV_SESSION_ID, ""))
    if bound:
        return bound

    pointer = read_session_pointer()
    if pointer:
        return pointer

    try:
        progress_file = get_legacy_progress_file()
        if progress_file.exists():
            with open(progress_file, "r", encoding="utf-8") as handle:
                data = json.load(handle)
            from_progress = normalize_session_id(data.get("session_id", ""))
            if from_progress:
                return from_progress
    except Exception:
        pass

    return default


def read_session_pointer():
    """Read the session ID recorded in the pointer file.

    Returns:
        str: Canonical session ID, or "" when the file is missing, unreadable,
            or holds an unusable value.
    """
    try:
        pointer = get_pointer_file()
        if not pointer.exists():
            return ""
        with open(pointer, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        return normalize_session_id(data.get("current_session_id", ""))
    except Exception:
        return ""


def write_session_pointer(session_id, project=""):
    """Publish a session ID to the pointer file for other processes to read.

    The pointer is what lets a freshly spawned hook process that received no
    payload still find the right session. It is written atomically so a reader
    never observes a partially written file.

    Args:
        session_id: Session identifier in any accepted form.
        project: Optional project name or path recorded alongside the ID.

    Returns:
        bool: True when the pointer was written.
    """
    canonical = normalize_session_id(session_id)
    if not canonical:
        return False

    from datetime import datetime

    payload = {
        "current_session_id": canonical,
        "started_at": datetime.now().isoformat(),
    }
    if project:
        payload["project"] = str(project)

    return atomic_write_text(get_pointer_file(), json.dumps(payload, indent=2))


def get_session_dir(session_id="", create=False):
    """Return the directory holding one session's state files.

    Args:
        session_id: Session identifier; resolved automatically when omitted.
        create: When True, create the directory (and parents) if absent.

    Returns:
        Path or None: Session directory, or None when no session resolves.
    """
    canonical = normalize_session_id(session_id) or resolve_session_id()
    if not canonical:
        return None

    session_dir = get_sessions_root() / canonical
    if create:
        try:
            session_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            return None
    return session_dir


def get_session_progress_file(session_id=""):
    """Return the per-session progress file path.

    Progress counters used to live in one global file, so two projects open at
    once shared a single tool count, context estimate and dirty-file list. They
    are now scoped per session; the global file remains only as a read
    fallback for sessions that predate the change.

    Args:
        session_id: Session identifier; resolved automatically when omitted.

    Returns:
        Path: Per-session progress file, or the legacy global file when no
            session can be resolved.
    """
    session_dir = get_session_dir(session_id)
    if session_dir is None:
        return get_legacy_progress_file()
    return session_dir / PROGRESS_FILENAME


def atomic_write_text(path, text):
    """Write text to a path atomically via a temp file and os.replace.

    Args:
        path: Destination path.
        text: Full file content to write.

    Returns:
        bool: True on success, False on any failure.
    """
    try:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp = target.with_name(target.name + ".tmp-" + str(os.getpid()))
        with open(tmp, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(str(tmp), str(target))
        return True
    except Exception:
        try:
            if tmp.exists():
                tmp.unlink()
        except Exception:
            pass
        return False


class FileLock:
    """Cross-process advisory lock built on a sidecar ``.lock`` file.

    Guards read-modify-write cycles on shared JSON state. Pre-tool, post-tool
    and stop hooks all fire concurrently against the same files, and an
    unguarded rewrite is what produced the ``flow-trace.corrupt-*`` archives.
    Acquisition failure is not fatal: the caller proceeds unlocked rather than
    letting a lock problem break the underlying tool call.

    Args:
        path: Path of the file being guarded (the lock is ``<path>.lock``).
        timeout: Seconds to wait for the lock before giving up.
    """

    def __init__(self, path, timeout=_LOCK_TIMEOUT_SEC):
        self._lock_path = Path(str(path) + ".lock")
        self._timeout = timeout
        self._handle = None
        self.acquired = False

    def __enter__(self):
        deadline = time.time() + self._timeout
        while time.time() < deadline:
            if self._try_acquire():
                self.acquired = True
                return self
            time.sleep(_LOCK_POLL_SEC)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._release()
        return False

    def _try_acquire(self):
        """Attempt a single non-blocking lock acquisition.

        Returns:
            bool: True when the lock is now held by this process.
        """
        try:
            self._lock_path.parent.mkdir(parents=True, exist_ok=True)
            self._handle = open(self._lock_path, "a+b")
        except Exception:
            self._handle = None
            return False

        try:
            if sys.platform == "win32":
                import msvcrt

                msvcrt.locking(self._handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(self._handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            return True
        except Exception:
            try:
                self._handle.close()
            except Exception:
                pass
            self._handle = None
            return False

    def _release(self):
        """Release the lock and close the sidecar handle."""
        if self._handle is None:
            return
        try:
            if sys.platform == "win32":
                import msvcrt

                msvcrt.locking(self._handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(self._handle.fileno(), fcntl.LOCK_UN)
        except Exception:
            pass
        try:
            self._handle.close()
        except Exception:
            pass
        self._handle = None
        self.acquired = False


def locked_json_update(path, mutator, default=None):
    """Read, mutate and rewrite a JSON file under a cross-process lock.

    A read-modify-write is only safe while the lock is held, so if the lock could
    not be acquired this skips the update and reports failure rather than racing.
    Proceeding unlocked is what produced the original interleaved rewrites, and a
    caller that also appends to a JSONL stream still has the durable record. This
    is the opposite choice from a full-file replace under ``atomic_write_text``,
    where an unlocked write can lose an update but can never corrupt the file.

    Args:
        path: JSON file to update.
        mutator: Callable taking the loaded object and returning the object to
            write. It may mutate and return the same object.
        default: Value to start from when the file is missing or corrupt.

    Returns:
        The object that was written, or None when the update was skipped or
        failed. A non-None return means the write is durable.
    """
    target = Path(path)
    with FileLock(target) as lock:
        if not lock.acquired:
            return None
        try:
            current = default if default is not None else {}
            if target.exists():
                try:
                    with open(target, "r", encoding="utf-8") as handle:
                        current = json.load(handle)
                except (json.JSONDecodeError, ValueError):
                    current = default if default is not None else {}
            updated = mutator(current)
            if updated is None:
                return None
            if atomic_write_text(target, json.dumps(updated, indent=2)):
                return updated
            return None
        except Exception:
            return None


def append_jsonl(path, record):
    """Append one JSON record as a line, concurrency-safe.

    Uses a single ``os.write`` on an ``O_APPEND`` descriptor rather than buffered
    text I/O, and holds the sidecar lock across the call. Buffered ``open(...,
    "a")`` handles from concurrent writers were observed dropping records on
    Windows, where O_APPEND is emulated as seek-to-end followed by write and the
    two steps can interleave.

    Args:
        path: Destination ``.jsonl`` file.
        record: JSON-serializable object to append.

    Returns:
        bool: True on success.
    """
    try:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = (json.dumps(record, default=str) + "\n").encode("utf-8")
        flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND
        if hasattr(os, "O_BINARY"):
            flags |= os.O_BINARY
        with FileLock(target):
            descriptor = os.open(str(target), flags, 0o644)
            try:
                os.write(descriptor, payload)
            finally:
                os.close(descriptor)
        return True
    except Exception:
        return False

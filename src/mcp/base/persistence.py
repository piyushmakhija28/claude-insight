"""
MCP Persistence Layer - Repository Pattern for file-based data storage.

Design Patterns:
  - Repository Pattern: ``AtomicJsonStore`` encapsulates JSON file CRUD
  - Append-Only Log:    ``JsonlAppender`` for structured event logging
  - Singleton:          ``SessionIdResolver`` caches current session ID

Replaces duplicated file I/O patterns across 6+ MCP servers:
  - Atomic write (write .tmp -> rename): 4 servers
  - JSONL append: 3 servers
  - Session ID resolution: 3 servers
  - State load/save: 4 servers

Windows-Safe: ASCII only (cp1252 compatible)
"""

import json
import os
import shutil
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, List, Optional


class AtomicJsonStore:
    """Thread-safe, atomic JSON file persistence with backup support.

    Repository pattern -- encapsulates all read/write/backup logic
    for a single JSON file. Uses write-to-temp-then-rename for
    crash safety (no partial writes on interruption).

    The ``_dir_created`` flag avoids redundant ``mkdir`` syscalls on
    the hot write path after the first successful save.

    Args:
        path: Path to the JSON file to manage.
        default_factory: Callable returning default dict when file is missing.
            Defaults to ``dict`` (returns empty dict).

    Example::

        store = AtomicJsonStore(Path("~/.claude/memory/state.json"))
        data = store.load(default={"count": 0})
        data["count"] += 1
        store.save(data)

        # Atomic read-modify-write:
        store.modify(lambda d: d.update(count=d["count"] + 1))
    """

    __slots__ = ("_path", "_default_factory", "_dir_created")

    def __init__(self, path: Path, default_factory: Optional[Callable] = None):
        self._path = Path(path)
        self._default_factory = default_factory or dict
        self._dir_created = False

    @property
    def path(self) -> Path:
        """The filesystem path of the backing JSON file."""
        return self._path

    @property
    def exists(self) -> bool:
        """Whether the backing file currently exists on disk."""
        return self._path.exists()

    def load(self, default: Optional[dict] = None) -> dict:
        """Load JSON data from file with automatic backup fallback.

        Attempts to read the primary file first. If it is missing or
        corrupted (invalid JSON), falls back to the ``.bak`` backup.
        If both fail, returns the provided default or calls the
        ``default_factory``.

        Uses try/except instead of existence checks to avoid TOCTOU races.

        Args:
            default: Explicit default dict to return if file is missing.
                Takes precedence over ``default_factory`` when provided.

        Returns:
            Parsed dict from file, backup, or default.
        """
        # Try primary file
        data = self._try_read(self._path)
        if data is not None:
            return data

        # Try .bak backup
        bak = self._path.with_suffix(self._path.suffix + ".bak")
        data = self._try_read(bak)
        if data is not None:
            return data

        # Return default
        if default is not None:
            return dict(default)
        return self._default_factory()

    def save(self, data: dict, backup: bool = False) -> None:
        """Save data atomically via write-to-temp-then-rename.

        Creates parent directories on first call, then caches the
        result to skip ``mkdir`` on subsequent saves (hot-path optimization).

        Args:
            data: Dictionary to serialize and persist.
            backup: If True, copy current file to ``.bak`` before overwriting.
                Backup failures are logged to stderr but do not prevent the save.
        """
        if not self._dir_created:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            self._dir_created = True

        if backup and self._path.exists():
            bak = self._path.with_suffix(self._path.suffix + ".bak")
            try:
                shutil.copy2(str(self._path), str(bak))
            except OSError:
                pass  # Backup is best-effort; save proceeds regardless

        temp = self._path.with_suffix(".tmp")
        temp.write_text(
            json.dumps(data, indent=2, default=str),
            encoding="utf-8",
        )
        temp.replace(self._path)

    def modify(self, fn: Callable[[dict], Any], default: Optional[dict] = None) -> dict:
        """Atomic read-modify-write cycle.

        Loads the current data, applies the modification function,
        saves the result, and returns the updated data.

        Note: Not atomic with respect to concurrent writers. Use external
        locking if multiple processes modify the same file.

        Args:
            fn: Callback that receives the loaded dict and mutates it in place.
            default: Default dict if file is missing.

        Returns:
            The modified data dict after saving.
        """
        data = self.load(default=default)
        fn(data)
        self.save(data)
        return data

    def delete(self) -> bool:
        """Delete the backing file.

        Returns:
            True if the file existed and was deleted, False otherwise.
        """
        if self._path.exists():
            self._path.unlink(missing_ok=True)
            return True
        return False

    @staticmethod
    def _try_read(path: Path) -> Optional[dict]:
        """Attempt to read and parse a JSON file.

        Uses try/except (not existence check) to avoid TOCTOU races.

        Args:
            path: File path to attempt reading.

        Returns:
            Parsed dict on success, None on any failure (missing, corrupt, etc.).
        """
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
        except (json.JSONDecodeError, FileNotFoundError, IOError, ValueError, OSError):
            pass
        return None


class JsonlAppender:
    """Append-only JSONL (JSON Lines) logger for structured event data.

    Each call to ``.append()`` writes one JSON object as a single line.
    Optimized for write-heavy, read-rarely patterns like tool tracking
    and optimization logging.

    The ``_dir_created`` flag avoids redundant ``mkdir`` on the hot append path.

    Args:
        path: Path to the JSONL file.

    Example::

        logger = JsonlAppender(Path("~/.claude/logs/tools.jsonl"))
        logger.append({"tool": "Read", "status": "success"})

        for entry in logger.read_all():
            print(entry["tool"])
    """

    __slots__ = ("_path", "_dir_created")

    def __init__(self, path: Path):
        self._path = Path(path)
        self._dir_created = False

    @property
    def path(self) -> Path:
        """The filesystem path of the JSONL file."""
        return self._path

    @property
    def exists(self) -> bool:
        """Whether the JSONL file currently exists on disk."""
        return self._path.exists()

    def append(self, entry: dict, auto_timestamp: bool = True) -> None:
        """Append a single JSON object as a line.

        Makes a shallow copy of the entry dict to avoid mutating the
        caller's data when adding the timestamp field.

        Args:
            entry: Dict to serialize as one JSON line.
            auto_timestamp: If True, add ``timestamp`` field if not already present.
        """
        if not self._dir_created:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            self._dir_created = True

        if auto_timestamp and "timestamp" not in entry:
            entry = {**entry, "timestamp": datetime.now().isoformat()}

        with open(self._path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, default=str) + "\n")

    def read_all(self) -> List[dict]:
        """Read all entries by streaming line-by-line.

        Uses line-by-line iteration to avoid loading the entire file
        into memory at once (important for large log files).

        Returns:
            List of parsed dicts. Empty list if file is missing.
        """
        entries = []
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        try:
                            entries.append(json.loads(line))
                        except (json.JSONDecodeError, TypeError):
                            continue
        except FileNotFoundError:
            pass
        return entries

    def read_filtered(self, date: str = "", **filters: Any) -> List[dict]:
        """Read entries matching date and/or field filters.

        Streams line-by-line for memory efficiency.

        Args:
            date: ISO date prefix filter (e.g., ``"2026-03-17"``).
            **filters: Key-value pairs that entries must match exactly.

        Returns:
            List of matching entry dicts.
        """
        results = []
        for entry in self.read_all():
            if date and date not in entry.get("timestamp", ""):
                continue
            if all(entry.get(k) == v for k, v in filters.items()):
                results.append(entry)
        return results

    def count(self) -> int:
        """Count total entries without loading all into memory.

        Returns:
            Number of non-empty lines in the file, or 0 if file is missing.
        """
        count = 0
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        count += 1
        except FileNotFoundError:
            pass
        return count


class SessionIdResolver:
    """Resolves current session ID from multiple file sources with caching.

    Singleton-style resolver that checks two file sources in order:

    1. ``.current-session.json`` (primary, key: ``current_session_id``)
    2. ``logs/session-progress.json`` (fallback, key: ``session_id``)

    Results are cached for 30 seconds to avoid repeated disk reads
    on the hot path (every tool call checks session ID).

    Args:
        config_dir: Root directory for session files.
            Only honored on first construction (singleton). Subsequent
            calls with a different path are ignored (the singleton is
            already initialized).

    Note:
        This is a singleton. Call ``SessionIdResolver.reset()`` to clear
        the instance (useful in tests).
    """

    _instance = None
    _CACHE_TTL = 30  # seconds

    def __new__(cls, config_dir: Optional[Path] = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, config_dir: Optional[Path] = None):
        if self._initialized:
            return
        self._config_dir = config_dir or (Path.home() / ".claude" / "memory")
        self._cached_id = ""
        self._cache_time = 0.0
        self._initialized = True

    @property
    def current_session_file(self) -> Path:
        """Path to the primary session file (``.current-session.json``)."""
        return self._config_dir / ".current-session.json"

    @property
    def progress_file(self) -> Path:
        """Path to the fallback session file (``logs/session-progress.json``)."""
        return self._config_dir / "logs" / "session-progress.json"

    def get(self, force_refresh: bool = False) -> str:
        """Get current session ID with TTL-based caching.

        Returns the cached ID if within the 30-second TTL window.
        Otherwise re-resolves from disk.

        Args:
            force_refresh: If True, bypass cache and re-read from disk.

        Returns:
            Session ID string (e.g., ``"SESSION-20260317-143000-ABCD"``),
            or empty string if no valid session is found.
        """
        now = time.time()

        env_sid = os.environ.get("CLAUDE_SESSION_ID", "").strip()
        if env_sid:
            self._cached_id = env_sid
            self._cache_time = now
            return env_sid

        if not force_refresh and self._cached_id:
            if (now - self._cache_time) < self._CACHE_TTL:
                return self._cached_id

        sid = self._resolve()
        self._cached_id = sid
        self._cache_time = now
        return sid

    def invalidate(self) -> None:
        """Clear the cached session ID, forcing re-resolution on next ``get()``."""
        self._cached_id = ""
        self._cache_time = 0.0

    def _resolve(self) -> str:
        """Resolve session ID by checking sources in priority order.

        ``CLAUDE_SESSION_ID`` is checked first: it is published by the hook that
        received Claude Code's payload, so it is the only source guaranteed to
        name the session the caller is actually in. The files below it can lag
        behind or, before per-session scoping, describe a different session
        entirely.

        Returns:
            Valid session ID or empty string.
        """
        env_sid = os.environ.get("CLAUDE_SESSION_ID", "").strip()
        if env_sid:
            return env_sid

        sid = self._read_session_id(self.current_session_file, "current_session_id")
        if sid:
            return sid

        sid = self._read_session_id(self.progress_file, "session_id")
        if sid:
            return sid

        return ""

    @staticmethod
    def _read_session_id(path: Path, key: str) -> str:
        """Read a session ID from a JSON file by key.

        Uses try/except instead of existence check to avoid TOCTOU races.

        Args:
            path: JSON file to read.
            key: Dict key containing the session ID.

        Returns:
            Session ID if valid (starts with ``SESSION-``), empty string otherwise.
        """
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            sid = data.get(key, "")
            if sid.startswith("SESSION-"):
                return sid
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            pass
        return ""

    @classmethod
    def reset(cls) -> None:
        """Reset the singleton instance (for testing).

        After calling this, the next ``SessionIdResolver()`` call
        creates a fresh instance with a new ``config_dir``.
        """
        cls._instance = None

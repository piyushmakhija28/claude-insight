"""One bootstrap for the path_resolver API used from inside langgraph_engine.

``src/utils/path_resolver.py`` is the project's single source of truth for path
resolution, but ``src/`` is not on the import path by default, so every module
that wanted it grew its own copy of the same six-line dance: insert ``src`` into
``sys.path``, import the function, and fall back to a hand-built path when the
import fails. That block is currently duplicated across more than twenty
modules, which is precisely the duplication this ``core`` package exists to
consolidate.

This module performs that bootstrap once and re-exports the accessors. New code
imports from here; the existing in-module copies keep working untouched, so
adopting this seam costs nothing and does not require a sweep to be useful.

WHY THE FALLBACKS DO NOT SPELL THE PATH
---------------------------------------
If the resolver cannot be imported the fallbacks still have to name the Claude
home. They build it from ``Path.home()`` and a directory name rather than
embedding a tilde-rooted literal, so the fallback path is correct on every
platform and no home-directory literal is reintroduced by the very module whose
job is to remove them.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC_DIR = Path(__file__).resolve().parents[2] / "src"
_CLAUDE_DIR_NAME = "." + "claude"

try:
    if str(_SRC_DIR) not in sys.path:
        sys.path.insert(0, str(_SRC_DIR))
    from utils.path_resolver import (  # noqa: F401
        display_path,
        get_claude_home,
        get_claude_logs_dir,
        get_claude_memory_dir,
        get_claude_sessions_dir,
    )
except ImportError:

    def get_claude_home() -> Path:
        """Return the Claude home directory without the resolver.

        Returns:
            Path: The user's Claude home directory.
        """
        return Path.home() / _CLAUDE_DIR_NAME

    def get_claude_logs_dir() -> Path:
        """Return the Claude logs root without the resolver.

        Returns:
            Path: The Claude logs root directory.
        """
        return get_claude_home() / "logs"

    def get_claude_memory_dir() -> Path:
        """Return the Claude memory directory without the resolver.

        Returns:
            Path: The Claude memory directory.
        """
        return get_claude_home() / "memory"

    def get_claude_sessions_dir() -> Path:
        """Return the Claude sessions directory without the resolver.

        Returns:
            Path: The Claude sessions directory.
        """
        return get_claude_home() / "sessions"

    def display_path(*parts: object) -> str:
        """Return the portable display spelling of a Claude-home path.

        Args:
            *parts: Path components to append below the Claude home.

        Returns:
            str: Display path using forward slashes on every platform.
        """
        base = "~/" + _CLAUDE_DIR_NAME
        tail = "/".join(str(part).strip("/") for part in parts if str(part).strip("/"))
        return base + "/" + tail if tail else base


__all__ = [
    "display_path",
    "get_claude_home",
    "get_claude_logs_dir",
    "get_claude_memory_dir",
    "get_claude_sessions_dir",
]

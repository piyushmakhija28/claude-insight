"""Session file resolution helpers.

Thin compatibility layer over :mod:`session_context`, which owns all session
identity resolution. Kept because existing hook modules and tests import these
names directly.

Usage:
    from project_session import get_project_session_file
    session_file = get_project_session_file()
"""

import os
import sys
from pathlib import Path

try:
    from session_context import get_memory_base, get_pointer_file, resolve_session_id
except ImportError:  # pragma: no cover - path bootstrap for direct script runs
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from session_context import get_memory_base, get_pointer_file, resolve_session_id

MEMORY_BASE = get_memory_base()


def get_project_session_file():
    """Return the session pointer file path.

    Returns:
        Path: ``{memory}/.current-session.json``
    """
    return get_pointer_file()


def get_legacy_session_file():
    """Return the legacy global session file path (backward compat).

    Returns:
        Path: ``{memory}/.current-session.json``
    """
    return get_pointer_file()


def read_session_id():
    """Read the active session ID.

    Resolves from the bound hook payload first, then the pointer file, then the
    legacy progress file. See :func:`session_context.resolve_session_id`.

    Returns:
        str: Session ID, or empty string when none can be resolved.
    """
    return resolve_session_id()


__all__ = [
    "MEMORY_BASE",
    "Path",
    "get_project_session_file",
    "get_legacy_session_file",
    "read_session_id",
]

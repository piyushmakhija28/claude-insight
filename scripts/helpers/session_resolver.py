"""helpers/session_resolver.py - Shared session ID resolution.

Thin wrapper over ``hooks/session_context.py``, which owns session identity for
the whole system. Kept because github_operations and other scripts import this
module by name.

Resolution order is defined by :func:`session_context.resolve_session_id`:
the session bound from the current hook payload, then the pointer file, then the
legacy progress file.

Windows-safe: ASCII only, no Unicode characters.
"""

import sys
from pathlib import Path

_HOOKS_DIR = str(Path(__file__).resolve().parent.parent.parent / "hooks")
if _HOOKS_DIR not in sys.path:
    sys.path.insert(0, _HOOKS_DIR)

from session_context import resolve_session_id as _resolve_session_id  # noqa: E402


def get_current_session_id():
    """Get the current session ID.

    Returns:
        str or None: Session ID string, or None when unavailable.
    """
    sid = _resolve_session_id()
    return sid if sid else None

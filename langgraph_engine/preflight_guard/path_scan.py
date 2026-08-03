"""Drive-path detection for the Level 0 Windows path check.

WHY THIS IS NOT A RAW-TEXT REGEX
--------------------------------
The check exists to find hardcoded Windows drive paths such as ``C:\\Users\\x``
in Python source. Applying a regex to the raw file text cannot distinguish a
backslash that begins a path from a backslash that begins a Python escape
sequence, because both are the same character before the interpreter reads them.

That ambiguity was not theoretical. The previous raw-text pattern matched
``f:`` followed by a newline escape inside this snippet::

    "with open(p) as f:" + chr(92) + "n    pass"

It read ``f`` as a drive letter and the escape plus the following indented text
as a path body, because its character class permitted spaces. The paired
auto-fix then rewrote the backslash to a forward slash, which silently corrupted
the string and removed the match, so the check reported success precisely
because the source had been damaged. Its own comment claimed a negative
lookbehind prevented this; the lookbehind only constrains the character BEFORE
the drive letter, and a single letter preceded by a space satisfies it.

Scanning the VALUES of string literals removes the ambiguity at the root rather
than narrowing the pattern. By the time a literal is a value, an escape has
already become the character it denotes: a newline is a newline and cannot be
mistaken for a path separator. A genuine ``"C:\\\\Users"`` literal still holds a
real backslash in its value and is still found.

Files that do not parse fall back to the raw-text scan, because a file with a
syntax error still deserves the check and no better evidence is available.
"""

import ast
import re

DRIVE_PATH_RE = re.compile(r"(?<![A-Za-z0-9_])([A-Za-z]):\\(?:[A-Za-z0-9_][A-Za-z0-9_\-\. \\]+)")


def iter_string_values(source):
    """Yield the value of every string constant in a Python source text.

    Args:
        source: Python source text.

    Returns:
        list: String values, or None when the source does not parse.
    """
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError):
        return None
    values = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            values.append(node.value)
    return values


def has_drive_path(source):
    """Report whether a Python source text hardcodes a Windows drive path.

    String literals are examined by value so that an escape sequence can never
    be mistaken for a path separator. Comment text is examined as written, since
    comments carry no escape processing.

    Args:
        source: Python source text.

    Returns:
        bool: True when at least one drive path is present.
    """
    values = iter_string_values(source)
    if values is None:
        return bool(DRIVE_PATH_RE.search(source))
    for value in values:
        if DRIVE_PATH_RE.search(value):
            return True
    for line in source.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("#") and DRIVE_PATH_RE.search(stripped):
            return True
    return False

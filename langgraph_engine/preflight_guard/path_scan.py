"""Drive-path detection for the Level 0 Windows path check.

WHY THIS IS NOT A RAW-TEXT REGEX
--------------------------------
The check exists to find hardcoded Windows drive paths -- a drive letter, a
colon and a backslash, spelled out here rather than written as an example,
because this module's own scan reads string values and a literal example would
make this file a violation of the rule it implements. That is not hypothetical:
it fired on the first version of this docstring and on the fixtures in the test
module beside it, and both were rewritten to assemble their paths at run time.

Applying a regex to the raw file text cannot distinguish a
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

KNOWN LIMIT: ONE LEVEL OF QUOTING
---------------------------------
Reading values resolves escapes exactly once. A literal whose value is ITSELF
Python source -- a fixture holding a code snippet, a template, a generator -- is
raw text again at that level, and an escape inside it is once more
indistinguishable from a path separator. The test module beside this one hit
that on its own fixture representing the corrupting snippet, and assembles it at
run time instead.

This is a limit, not a bug: distinguishing the two would require knowing that a
particular string is destined to be parsed as source, which is not decidable
here. The consequence is a possible false positive on code-generating modules,
never a false negative on a real path.
"""

import ast
import re

DRIVE_PATH_RE = re.compile(r"(?<![A-Za-z0-9_])([A-Za-z]):\\(?:[A-Za-z0-9_][A-Za-z0-9_\-\. \\]+)")


_DOCSTRING_OWNERS = (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)


def _docstring_nodes(tree):
    """Collect the constant nodes that serve as docstrings.

    A docstring is the first statement of a module, class or function body. It
    is documentation rather than code, so a drive path inside one is an example
    being explained, not a path the program will use.

    Args:
        tree: Parsed module AST.

    Returns:
        set: ``id()`` of each docstring constant node.
    """
    found = set()
    for node in ast.walk(tree):
        if not isinstance(node, _DOCSTRING_OWNERS):
            continue
        body = getattr(node, "body", None)
        if not body:
            continue
        first = body[0]
        if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant):
            if isinstance(first.value.value, str):
                found.add(id(first.value))
    return found


def iter_string_values(source):
    """Yield the value of every non-docstring string constant in a source text.

    Docstrings are excluded because the check exists to find paths the program
    USES, and a path inside a docstring is an example being described. That
    distinction is the same enclosing-node classification the home-directory
    rule requires, applied to a different surface.

    Args:
        source: Python source text.

    Returns:
        list: String values, or None when the source does not parse.
    """
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError):
        return None
    docstrings = _docstring_nodes(tree)
    values = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if id(node) in docstrings:
                continue
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

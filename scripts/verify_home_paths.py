"""Verify V2-018 / SRS FR-28: no home-directory path is constructed outside path_resolver.

The project's single source of truth for path resolution is
``src/utils/path_resolver.py``. Every other module that spells a home-directory
Claude path as a string default, a call keyword or an assignment is building a
path the resolver already knows how to build, and will silently go stale the day
the layout moves. This gate finds those, and only those.

WHY THE PARTITION IS THE WHOLE POINT
------------------------------------
Two prior measurements of this same surface disagreed by roughly 7x on how much
of it is executable. One method reported 13 code-level occurrences against 103
comment-or-docstring; an independent line-oriented grep reported ~95 live
against 23 comments. The grep cannot structurally tell a docstring body from
executable code -- to a line-oriented pattern both are just text on a line -- so
it does not refute the other method, but neither figure is corroborated. This
gate exists to replace both with a measured partition, so it reports the split
as an output rather than accepting either number as an input.

The classification is therefore not a detail of the implementation; it IS the
deliverable. Three disjoint classes, decided by where the text sits:

* COMMENT   -- a ``tokenize.COMMENT`` token. Comments are absent from the AST
               entirely, so they can only be found by a token pass.
* DOCSTRING -- a string constant that is the first statement of a module, class
               or function body. The language binds it to ``__doc__``; it is
               documentation, and a path inside it is an example being described.
* CODE      -- every other string constant. Whatever its shape, the interpreter
               evaluates it and the program can use its value.

CODE is defined as the complement rather than as a list of accepted shapes.
Enumerating shapes would silently pass anything the list forgot, and the failure
mode this gate guards against is a path default nobody enumerated. The
enclosing-node label is still recorded per occurrence, so the three shapes the
acceptance criterion names -- a default in ``ast.arguments.defaults``, an
``ast.Call`` keyword, and an assignment right-hand side -- remain visible and
countable in the artifact rather than being collapsed into a single verdict.

WHY THIS READS STRING VALUES, NOT SOURCE TEXT
---------------------------------------------
Reading source text cannot distinguish a separator from the start of an escape
sequence, because before the interpreter runs they are the same character. The
Level 0 guard learned this the expensive way: its raw-text predecessor read an
escape as a path body and its paired auto-fix then rewrote the source, so the
check reported success precisely because it had corrupted the file. Reading
values resolves escapes exactly once and removes the ambiguity at the root.

That inherited limit applies here too: a literal whose value is itself Python
source is raw text again at that level. It is a limit, not a bug -- deciding it
would require knowing a given string is destined to be parsed as source.

WHY THIS FILE DOES NOT SPELL THE PATTERN
----------------------------------------
This module lives in ``scripts/``, which is inside its own scan scope. Writing
the searched-for text as a literal anywhere in it -- including in this docstring
-- would make the instrument an occurrence in its own measurement. The pattern
is assembled from parts at import time for that reason, exactly as the Level 0
scanner and its tests do.

THE TWO CHECKS MEASURE DIFFERENT SURFACES
-----------------------------------------
The home-directory check and the absolute-path check are reported separately and
are not the same population. The first looks for a tilde-rooted or
percent-expanded Claude directory reference in any string. The second looks for
a rooted filesystem path -- a drive letter with a separator, or a POSIX home
root -- and it has its own exclusions for URLs, which contain a colon and two
separators but are not filesystem paths. A file can fail one and pass the other.

The absolute-path branch requires a real path character immediately after the
separator. Without that clause it fired on the value of a regular-expression
literal, where a negated character class put a letter, a colon and a backslash
next to each other and the pattern read them as a drive path. That is the
one-level-of-quoting limit again: the value of a literal that is itself a
pattern is raw text at that level. Requiring the following character keeps every
genuine rooted path, whose next character is always a path character.

WHAT IS EXCLUDED, AND WHY EXACTLY ONE THING IS
----------------------------------------------
``src/utils/path_resolver.py`` is the destination of every remediation this gate
drives. Its own home-directory constants are the canonical source those
remediations resolve through, so counting them as violations would make the gate
demand the deletion of the thing it exists to route traffic toward. It is
excluded from the zero-CODE condition by name, and it is still scanned, still
classified and still counted in the reported total.

There is no suppression comment and no ratchet baseline. Remediation drives the
enforced count to zero in the change that introduces the gate, so a baseline
would be an empty set and a suppression token would be an ungoverned bypass with
no legitimate user.

BOTH CHECKS GATE ON CODE, AND REPORT DOCUMENTATION SEPARATELY
-------------------------------------------------------------
The zero condition applies to the CODE class in both checks, not to every
occurrence. A rooted path inside a docstring is an example being explained --
this repository has one that documents why a tokenizer runs in non-posix mode on
Windows, and rewriting it would delete the explanation of a real bug while
changing no behaviour. Documentation occurrences are counted, listed and
reported; they are not remediated and they do not fail the gate.

Exit status is 0 only when no enforced CODE occurrence, no CODE-level absolute
path literal, and no unreadable file remains.
"""

from __future__ import annotations

import argparse
import ast
import io
import re
import sys
import tokenize
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator

REPO_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_SCOPE = ("langgraph_engine", "hooks", "scripts", "src")

SKIP_DIR_NAMES = frozenset(
    {
        ".git",
        ".venv",
        "venv",
        "env",
        "__pycache__",
        "node_modules",
        "build",
        "dist",
        "site-packages",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        ".tox",
        ".eggs",
    }
)

EXCLUDED_FROM_ENFORCEMENT = frozenset({"src/utils/path_resolver.py"})

_TILDE = chr(126)
_PERCENT = chr(37)
_SEPARATORS = "[/" + chr(92) + chr(92) + "]"
_CLAUDE_DIR = re.escape("." + "claude")

HOME_PATH_RE = re.compile(
    "(?:"
    + re.escape(_TILDE)
    + "|"
    + _PERCENT
    + "USERPROFILE"
    + _PERCENT
    + "|"
    + re.escape("$")
    + "HOME"
    + "|"
    + re.escape("${HOME}")
    + ")"
    + _SEPARATORS
    + _CLAUDE_DIR
)

_PATH_CHAR = "[A-Za-z0-9_.-]"
_DRIVE_ABS_RE = "(?<![A-Za-z0-9_])[A-Za-z]:" + _SEPARATORS + _PATH_CHAR
_POSIX_HOME_RE = "/(?:Users|home|root)/" + _PATH_CHAR

ABSOLUTE_PATH_RE = re.compile("(?:" + _DRIVE_ABS_RE + "|" + _POSIX_HOME_RE + ")")

URL_SCHEME_RE = re.compile(r"[A-Za-z][A-Za-z0-9+.-]*://")

CLASS_CODE = "CODE"
CLASS_DOCSTRING = "DOCSTRING"
CLASS_COMMENT = "COMMENT"

_DOCSTRING_OWNERS = (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)

NAMED_CODE_SHAPES = frozenset({"arguments.defaults", "Call.keyword", "Assign.value"})


@dataclass(frozen=True)
class Occurrence:
    """One home-directory reference and the class decided for it.

    Attributes:
        path: Repository-relative POSIX-style path of the containing file.
        line: 1-based line number the occurrence sits on.
        node_type: Label for the enclosing AST node, or ``Comment`` for a token.
        classification: One of ``CODE``, ``DOCSTRING`` or ``COMMENT``.
        text: The matched substring, for evidence.
    """

    path: str
    line: int
    node_type: str
    classification: str
    text: str

    def record(self) -> str:
        """Return the per-occurrence record required by the acceptance criterion.

        Returns:
            str: ``file:line:node_type:classification``.
        """
        return "{}:{}:{}:{}".format(self.path, self.line, self.node_type, self.classification)

    def is_enforced(self) -> bool:
        """Report whether this occurrence must be zero after remediation.

        Returns:
            bool: True when the occurrence is CODE outside the excluded resolver.
        """
        return self.classification == CLASS_CODE and self.path not in EXCLUDED_FROM_ENFORCEMENT


def docstring_node_ids(tree: ast.AST) -> set[int]:
    """Collect the identities of the string constants that serve as docstrings.

    A docstring is the first statement of a module, class or function body. The
    same rule is implemented in ``langgraph_engine/preflight_guard/path_scan.py``
    for the Level 0 guard. It is restated here rather than imported because
    importing it drags the whole orchestration engine -- measured at 1.13s and
    1454 modules, with DEBUG logging emitted into this gate's own output. The
    two implementations are pinned together by an equivalence test that compares
    them across the entire live scope, so a drift in either fails the suite.

    Args:
        tree: Parsed module AST.

    Returns:
        set: ``id()`` of each string constant node acting as a docstring.
    """
    found: set[int] = set()
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


def _build_parent_index(tree: ast.AST) -> dict[int, tuple[ast.AST, str]]:
    """Map every node identity onto its parent node and the field that holds it.

    A single traversal records the structural position of each node, so the
    enclosing-node label for any matched constant is a dictionary lookup rather
    than a fresh search of the tree.

    Args:
        tree: Parsed module AST.

    Returns:
        dict: ``id(child)`` to ``(parent, field_name)``.
    """
    index: dict[int, tuple[ast.AST, str]] = {}
    for parent in ast.walk(tree):
        for field, value in ast.iter_fields(parent):
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, ast.AST):
                        index[id(item)] = (parent, field)
            elif isinstance(value, ast.AST):
                index[id(value)] = (parent, field)
    return index


def _owner_label(owner: ast.AST) -> str:
    """Return the docstring label for the node that owns a docstring.

    Args:
        owner: Module, class or function node.

    Returns:
        str: Label such as ``Module.docstring``.
    """
    return "{}.docstring".format(type(owner).__name__)


def _docstring_owner_label(tree: ast.AST, target: ast.Constant) -> str:
    """Find which construct a docstring constant documents.

    Args:
        tree: Parsed module AST.
        target: The constant node acting as a docstring.

    Returns:
        str: Owner label, defaulting to ``Module.docstring`` when unresolved.
    """
    for node in ast.walk(tree):
        if not isinstance(node, _DOCSTRING_OWNERS):
            continue
        body = getattr(node, "body", None)
        if not body:
            continue
        first = body[0]
        if isinstance(first, ast.Expr) and first.value is target:
            return _owner_label(node)
    return "Module.docstring"


def _node_type_label(node: ast.AST, index: dict[int, tuple[ast.AST, str]]) -> str:
    """Describe the enclosing node of a matched string constant.

    The label names the immediate structural parent and the field it occupies,
    normalised so that the three shapes the acceptance criterion calls out --
    a parameter default, a call keyword and an assignment right-hand side --
    carry stable, countable names.

    Args:
        node: The matched constant node.
        index: Parent index for the enclosing module.

    Returns:
        str: Enclosing-node label, or ``Unparented`` when the node has no parent.
    """
    entry = index.get(id(node))
    if entry is None:
        return "Unparented"
    parent, field = entry
    if isinstance(parent, ast.arguments):
        return "arguments.defaults"
    if isinstance(parent, ast.keyword):
        return "Call.keyword"
    if isinstance(parent, ast.Assign) and field == "value":
        return "Assign.value"
    if isinstance(parent, (ast.AnnAssign, ast.AugAssign)) and field == "value":
        return "Assign.value"
    if isinstance(parent, ast.Call) and field == "args":
        return "Call.args"
    if isinstance(parent, ast.Dict):
        return "Dict.key" if field == "keys" else "Dict.value"
    if isinstance(parent, (ast.List, ast.Tuple, ast.Set)):
        return "{}.elt".format(type(parent).__name__)
    if isinstance(parent, ast.Expr) and field == "value":
        return "Expr.bare-string"
    return "{}.{}".format(type(parent).__name__, field)


def _line_of_offset(node: ast.Constant, offset: int) -> int:
    """Estimate the line a match sits on inside a possibly multi-line literal.

    The offset is counted in the literal's VALUE, which for a triple-quoted
    docstring corresponds one-for-one with source lines. For a literal whose
    escapes or implicit concatenation change that correspondence the estimate can
    drift, so it is clamped to the literal's own span. Only the reported line can
    be affected; the count and the classification cannot.

    Args:
        node: The constant node containing the match.
        offset: Character offset of the match within the node's value.

    Returns:
        int: 1-based line number within the file.
    """
    start = node.lineno
    end = getattr(node, "end_lineno", None) or start
    value = node.value if isinstance(node.value, str) else ""
    estimate = start + value[:offset].count("\n")
    return max(start, min(estimate, end))


def _iter_matches(text: str, pattern: re.Pattern[str]) -> Iterator[tuple[int, str]]:
    """Yield every non-overlapping match in a text as offset and matched text.

    Args:
        text: Text to search.
        pattern: Compiled pattern to apply.

    Yields:
        tuple: ``(start_offset, matched_text)`` per match.
    """
    for match in pattern.finditer(text):
        yield match.start(), match.group(0)


def collect_comment_occurrences(source: str, display_path: str, pattern: re.Pattern[str]) -> list[Occurrence]:
    """Find matches inside comment tokens.

    Comments never reach the AST, so a token pass is the only way to see them.
    Comment text carries no escape processing, so it is matched as written.

    Args:
        source: Python source text.
        display_path: Path string used in the returned occurrences.
        pattern: Compiled pattern to apply.

    Returns:
        list: One Occurrence per match found in a comment token.
    """
    found: list[Occurrence] = []
    try:
        tokens = tokenize.generate_tokens(io.StringIO(source).readline)
        for token in tokens:
            if token.type != tokenize.COMMENT:
                continue
            for _, text in _iter_matches(token.string, pattern):
                found.append(Occurrence(display_path, token.start[0], "Comment", CLASS_COMMENT, text))
    except (tokenize.TokenError, IndentationError, SyntaxError):
        return found
    return found


def collect_string_occurrences(
    tree: ast.AST,
    display_path: str,
    pattern: re.Pattern[str],
) -> list[Occurrence]:
    """Find matches inside string constant values and classify each by position.

    One traversal builds the parent index and the docstring identity set, then a
    second pass over constants decides each match. Adding another string-shaped
    rule would reuse the same index rather than re-walking the tree.

    Args:
        tree: Parsed module AST.
        display_path: Path string used in the returned occurrences.
        pattern: Compiled pattern to apply.

    Returns:
        list: One Occurrence per match found in a string constant.
    """
    index = _build_parent_index(tree)
    docstrings = docstring_node_ids(tree)
    found: list[Occurrence] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
            continue
        matches = list(_iter_matches(node.value, pattern))
        if not matches:
            continue
        if id(node) in docstrings:
            label = _docstring_owner_label(tree, node)
            classification = CLASS_DOCSTRING
        else:
            label = _node_type_label(node, index)
            classification = CLASS_CODE
        for offset, text in matches:
            found.append(Occurrence(display_path, _line_of_offset(node, offset), label, classification, text))
    return found


def analyse_source(source: str, display_path: str, pattern: re.Pattern[str] = HOME_PATH_RE) -> list[Occurrence]:
    """Classify every home-directory reference in one module.

    Args:
        source: Python source text.
        display_path: Path string used in the returned occurrences.
        pattern: Compiled pattern to apply, defaulting to the home-path pattern.

    Returns:
        list: Occurrences ordered by line then by class.

    Raises:
        SyntaxError: When the source does not parse.
    """
    tree = ast.parse(source, filename=display_path)
    found = collect_string_occurrences(tree, display_path, pattern)
    found.extend(collect_comment_occurrences(source, display_path, pattern))
    return sorted(found, key=lambda item: (item.line, item.classification, item.node_type))


def _url_spans(value: str) -> list[tuple[int, int]]:
    """Locate the extent of every URL inside a string value.

    A URL runs from its scheme to the first whitespace or quote character. The
    span matters rather than the scheme alone: a URL's PATH can contain a
    segment that looks like a POSIX home root, and suppressing only matches that
    begin inside the scheme would let that through. A negative test covers
    exactly that case, because the first version of this function had the bug.

    Args:
        value: The full string value being searched.

    Returns:
        list: ``(start, end)`` offsets covering each URL found.
    """
    spans: list[tuple[int, int]] = []
    for scheme in URL_SCHEME_RE.finditer(value):
        end = scheme.end()
        while end < len(value) and value[end] not in " \t\r\n'\"<>()[]{}":
            end += 1
        spans.append((scheme.start(), end))
    return spans


def _is_url_context(value: str, offset: int) -> bool:
    """Report whether a rooted-path match falls inside a URL.

    Args:
        value: The full string value being searched.
        offset: Offset of the candidate match.

    Returns:
        bool: True when the match lies within a URL's extent.
    """
    return any(start <= offset < end for start, end in _url_spans(value))


def find_absolute_path_literals(source: str, display_path: str) -> list[Occurrence]:
    """Find rooted filesystem paths written as string literals.

    This is a different population from the home-directory check and is reported
    separately. A tilde-rooted reference is not a rooted path; a drive letter or
    a POSIX home root is. URL matches are excluded because a scheme separator is
    not a filesystem separator.

    Args:
        source: Python source text.
        display_path: Path string used in the returned occurrences.

    Returns:
        list: One Occurrence per rooted-path literal, classified by position.

    Raises:
        SyntaxError: When the source does not parse.
    """
    tree = ast.parse(source, filename=display_path)
    index = _build_parent_index(tree)
    docstrings = docstring_node_ids(tree)
    found: list[Occurrence] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
            continue
        for offset, text in _iter_matches(node.value, ABSOLUTE_PATH_RE):
            if _is_url_context(node.value, offset):
                continue
            if id(node) in docstrings:
                label = _docstring_owner_label(tree, node)
                classification = CLASS_DOCSTRING
            else:
                label = _node_type_label(node, index)
                classification = CLASS_CODE
            found.append(Occurrence(display_path, _line_of_offset(node, offset), label, classification, text))
    return sorted(found, key=lambda item: (item.line, item.node_type))


def iter_python_files(root: Path, scope: Iterable[str]) -> Iterator[Path]:
    """Yield every scannable Python file under the given scope directories.

    Args:
        root: Repository root.
        scope: Directory names relative to the root.

    Yields:
        Path: Python source files outside the skipped directory names.
    """
    for section in scope:
        base = root / section
        if not base.exists():
            continue
        for candidate in sorted(base.rglob("*.py")):
            if any(part in SKIP_DIR_NAMES for part in candidate.parts):
                continue
            yield candidate


def scan_paths(files: Iterable[Path], root: Path) -> tuple[list[Occurrence], list[Occurrence], list[tuple[str, str]]]:
    """Run both checks over a set of files.

    Args:
        files: Python files to analyse.
        root: Root used to render repository-relative display paths.

    Returns:
        tuple: ``(home_occurrences, absolute_occurrences, unreadable)`` where
        unreadable holds ``(path, reason)`` pairs.
    """
    home: list[Occurrence] = []
    absolute: list[Occurrence] = []
    unreadable: list[tuple[str, str]] = []
    for file_path in files:
        try:
            display = file_path.relative_to(root).as_posix()
        except ValueError:
            display = file_path.as_posix()
        try:
            source = file_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            unreadable.append((display, "unreadable: {}".format(exc)))
            continue
        try:
            home.extend(analyse_source(source, display))
            absolute.extend(find_absolute_path_literals(source, display))
        except SyntaxError as exc:
            unreadable.append((display, "unparsed: {}".format(exc)))
    return home, absolute, unreadable


def summarise(occurrences: Iterable[Occurrence]) -> dict[str, int]:
    """Count occurrences per classification.

    Args:
        occurrences: Occurrences to tally.

    Returns:
        dict: Classification label to count, with all three classes present.
    """
    counts = {CLASS_CODE: 0, CLASS_DOCSTRING: 0, CLASS_COMMENT: 0}
    for item in occurrences:
        counts[item.classification] = counts.get(item.classification, 0) + 1
    return counts


def shape_breakdown(occurrences: Iterable[Occurrence]) -> dict[str, int]:
    """Count CODE occurrences per enclosing-node label.

    Args:
        occurrences: Occurrences to tally.

    Returns:
        dict: Enclosing-node label to count, restricted to CODE occurrences.
    """
    counts: dict[str, int] = {}
    for item in occurrences:
        if item.classification != CLASS_CODE:
            continue
        counts[item.node_type] = counts.get(item.node_type, 0) + 1
    return counts


def _render_report(
    home: list[Occurrence],
    absolute: list[Occurrence],
    unreadable: list[tuple[str, str]],
    scanned: int,
) -> str:
    """Build the committed evidence artifact.

    Args:
        home: Home-directory occurrences.
        absolute: Absolute-path literal occurrences.
        unreadable: Files that could not be read or parsed.
        scanned: Number of files scanned.

    Returns:
        str: Markdown report text.
    """
    counts = summarise(home)
    total = sum(counts.values())
    files = sorted({item.path for item in home})
    enforced = [item for item in home if item.is_enforced()]
    excluded = [item for item in home if item.classification == CLASS_CODE and not item.is_enforced()]
    shapes = shape_breakdown(home)

    lines = [
        "<!-- Generated by scripts/verify_home_paths.py. Do not edit manually; re-run the gate to refresh. -->",
        "",
        "# Home-Directory Path Occurrence Classification",
        "",
        "Scope: `" + "`, `".join(DEFAULT_SCOPE) + "` (live scope only).",
        "Method: AST classification of string constant VALUES plus a `tokenize` pass for comments.",
        "",
        "## Measured totals",
        "",
        "| Metric | Measured |",
        "|---|---|",
        "| Python files scanned | {} |".format(scanned),
        "| Files with at least one occurrence | {} |".format(len(files)),
        "| Total occurrences | {} |".format(total),
        "| CODE | {} |".format(counts[CLASS_CODE]),
        "| DOCSTRING | {} |".format(counts[CLASS_DOCSTRING]),
        "| COMMENT | {} |".format(counts[CLASS_COMMENT]),
        "| CODE outside the excluded resolver (enforced) | {} |".format(len(enforced)),
        "| CODE inside `src/utils/path_resolver.py` (excluded by name) | {} |".format(len(excluded)),
        "| Absolute path literals | {} |".format(len(absolute)),
        "| Unreadable or unparsed files | {} |".format(len(unreadable)),
        "",
        "## CODE occurrences by enclosing node",
        "",
        "| Enclosing node | Count |",
        "|---|---|",
    ]
    for label in sorted(shapes, key=lambda key: (-shapes[key], key)):
        lines.append("| `{}` | {} |".format(label, shapes[label]))
    lines.extend(
        [
            "",
            "## Per-occurrence records",
            "",
            "One record per occurrence, as `file:line:node_type:classification`.",
            "",
            "```",
        ]
    )
    lines.extend(item.record() for item in sorted(home, key=lambda item: (item.path, item.line)))
    lines.extend(["```", ""])
    if absolute:
        lines.extend(["## Absolute path literals", "", "```"])
        lines.extend(item.record() for item in sorted(absolute, key=lambda item: (item.path, item.line)))
        lines.extend(["```", ""])
    if unreadable:
        lines.extend(["## Unreadable or unparsed", "", "```"])
        lines.extend("{}  {}".format(path, reason) for path, reason in unreadable)
        lines.extend(["```", ""])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    """Run the gate over a repository tree.

    Args:
        argv: Command-line arguments, defaulting to ``sys.argv[1:]``.

    Returns:
        int: 0 when no enforced CODE occurrence and no unreadable file remains.
    """
    parser = argparse.ArgumentParser(description="Classify and gate home-directory path references.")
    parser.add_argument("--root", default=str(REPO_ROOT), help="Repository root to scan.")
    parser.add_argument("--report", default=None, help="Write the evidence artifact to this path.")
    parser.add_argument("--verbose", action="store_true", help="List every occurrence, not just enforced ones.")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    files = list(iter_python_files(root, DEFAULT_SCOPE))
    home, absolute, unreadable = scan_paths(files, root)

    counts = summarise(home)
    enforced = [item for item in home if item.is_enforced()]
    absolute_code = [item for item in absolute if item.is_enforced()]
    absolute_documented = [item for item in absolute if not item.is_enforced()]
    total = sum(counts.values())
    hit_files = {item.path for item in home}

    print("verify_home_paths: scanned {} files under {}".format(len(files), root))
    print(
        "  total={}  files={}  CODE={}  DOCSTRING={}  COMMENT={}".format(
            total, len(hit_files), counts[CLASS_CODE], counts[CLASS_DOCSTRING], counts[CLASS_COMMENT]
        )
    )
    print("  enforced CODE (excluding path_resolver.py)={}".format(len(enforced)))
    print(
        "  absolute path literals: CODE={}  documented={}  unreadable={}".format(
            len(absolute_code), len(absolute_documented), len(unreadable)
        )
    )

    if args.verbose:
        for item in sorted(home, key=lambda item: (item.path, item.line)):
            print("  {}".format(item.record()))
        for item in absolute_documented:
            print("  note    {}  (documentation, not remediated)".format(item.record()))

    for item in enforced:
        print("  FAIL    {}".format(item.record()))
    for item in absolute_code:
        print("  ABSPATH {}".format(item.record()))
    for path, reason in unreadable:
        print("  ERROR   {}  {}".format(path, reason))

    if args.report:
        report_path = Path(args.report)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(_render_report(home, absolute, unreadable, len(files)), encoding="utf-8")
        print("  report written to {}".format(report_path))

    if enforced or absolute_code or unreadable:
        print("verify_home_paths: FAILED")
        return 1
    print("verify_home_paths: PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())

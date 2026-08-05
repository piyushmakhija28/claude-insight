"""Verify V2-019 / SRS FR-30: every text-mode file open passes an explicit ``encoding=``.

On Windows the built-in ``open()`` defaults to the ANSI codepage (cp1252 on this
project's primary platform) while CI runners default to UTF-8. The same file read
on two machines therefore yields different bytes, or raises ``UnicodeDecodeError``
on content the program itself wrote. This is a correctness defect, not a style
preference, and CLAUDE.md's own platform rule already requires UTF-8 everywhere.

WHY AN AST PASS AND NOT A REGEX
-------------------------------
A regex over ``open(`` misses ``io.open``, ``codecs.open``, ``Path(...).open()``,
imports aliased through ``from io import open as _open``, and calls whose argument
list spans several lines. It also fires on the literal text ``open(`` inside a
docstring or a comment. The baseline this task inherited was itself produced by a
regex that required an explicit mode string, and it undercounted by seven because
``open(path)`` with no mode argument already defaults to text mode ``'r'``. Every
one of those failure modes is a parser-level distinction, so the check is a parser.

WHAT COUNTS AS A FILE OPENER
----------------------------
The rule fires only on constructs that can actually take an ``encoding=`` keyword:

* the bare name ``open`` (and any alias bound to it by ``from io import open as X``)
* ``io.open`` and ``codecs.open``
* ``.open()`` on a receiver with demonstrated ``pathlib`` provenance

The last clause is deliberately narrow and it is the precision-critical one. An
earlier draft of this checker treated every ``.open()`` attribute call as a file
open. Measured against this repository that rule had precision 0.0: all eight of
its hits were domain methods named ``open`` (``guard.open()``, ``session.open()``,
``self.open()``) that never touch a file. Requiring pathlib provenance removes all
eight without losing the real construct, which ``test_open_encoding_gate.py``
proves by feeding the checker a genuine ``Path(...).open()`` and requiring a flag.

EXEMPTIONS, AND WHY THEY ARE THIS NARROW
----------------------------------------
Binary mode must be exempt because passing ``encoding=`` alongside it raises
``ValueError`` at runtime -- exempting it is required for correctness, not a
concession. ``tarfile``, ``gzip``, ``zipfile`` and friends have their own
signatures, and ``urllib``'s ``urlopen`` and ``os.fdopen`` are not text-file
openers at all. An exemption list any broader than this would make the gate pass
by excusing the defects it exists to find, so each entry is asserted to be
load-bearing by a companion specificity test rather than merely declared here.

An open whose mode cannot be resolved statically is reported UNDECIDABLE and fails
the gate. Silence on the cases the parser cannot decide is how a gate comes to
report clean on code it never actually judged.

THERE IS NO SUPPRESSION MECHANISM AND NO RATCHET BASELINE
---------------------------------------------------------
Both are deliberate omissions. Remediation drives the violation count to zero in
the same change that introduces the gate, so a ratchet baseline would be an empty
set, and a suppression comment would be an escape hatch with no legitimate user.
Adding either would create an ungoverned bypass ahead of any demonstrated need.

Exit status is 0 only when the violation and undecidable sets are both empty.
"""

from __future__ import annotations

import argparse
import ast
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator

REPO_ROOT = Path(__file__).resolve().parents[1]

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

EXEMPT_OPENER_MODULES = frozenset(
    {
        "tarfile",
        "gzip",
        "bz2",
        "lzma",
        "zipfile",
        "shelve",
        "dbm",
        "os",
        "socket",
        "webbrowser",
        "urllib",
        "request",
        "sqlite3",
        "wave",
    }
)

EXEMPT_OPENER_FUNCTIONS = frozenset({"urlopen", "fdopen", "popen", "startfile"})

TEXT_OPENER_MODULES = frozenset({"io", "codecs"})

PATH_FACTORIES = frozenset(
    {
        "Path",
        "PurePath",
        "PosixPath",
        "WindowsPath",
        "PurePosixPath",
        "PureWindowsPath",
    }
)

BUILTIN_SHAPE = "builtin"
PATH_SHAPE = "path-method"

MODE_INDEX = {BUILTIN_SHAPE: 1, PATH_SHAPE: 0}
ENCODING_INDEX = {BUILTIN_SHAPE: 3, PATH_SHAPE: 2}


@dataclass(frozen=True)
class Finding:
    """One resolved ``open`` call site and the verdict reached for it.

    Attributes:
        path: Repository-relative POSIX-style path of the containing file.
        line: 1-based line number of the call.
        verdict: One of ``VIOLATION``, ``UNDECIDABLE``, ``EXEMPT`` or ``OK``.
        opener: Which opener construct was recognised.
        detail: Human-readable reason supporting the verdict.
    """

    path: str
    line: int
    verdict: str
    opener: str
    detail: str

    def location(self) -> str:
        """Return the ``path:line`` location string.

        Returns:
            str: Location in ``path:line`` form.
        """
        return "{}:{}".format(self.path, self.line)

    def describe(self) -> str:
        """Return a single-line report entry.

        Returns:
            str: Location followed by the opener and the supporting detail.
        """
        return "{}  [{}] {}".format(self.location(), self.opener, self.detail)


class _PathProvenance:
    """Records which module-local names hold a ``pathlib`` object.

    The analysis is intentionally shallow: it collects names bound to a pathlib
    factory call, to another already-known path name, or to a ``/`` join, plus
    names annotated as a pathlib type. It is a precision filter for the
    ``.open()`` clause, not a general points-to analysis, and it is allowed to
    under-approximate. Under-approximating costs recall on an exotic construct;
    over-approximating costs precision on every domain method named ``open``,
    which is the failure this filter exists to prevent.
    """

    def __init__(self) -> None:
        self.names: set[str] = set()

    def collect(self, tree: ast.AST) -> None:
        """Populate the known-path name set from a parsed module.

        Args:
            tree: Parsed module AST.
        """
        for _ in range(2):
            for node in ast.walk(tree):
                if isinstance(node, ast.AnnAssign):
                    if self._annotation_is_path(node.annotation):
                        self._record_target(node.target)
                    elif node.value is not None and self.is_path_like(node.value):
                        self._record_target(node.target)
                elif isinstance(node, ast.Assign):
                    if self.is_path_like(node.value):
                        for target in node.targets:
                            self._record_target(target)
                elif isinstance(node, ast.arg):
                    if node.annotation is not None and self._annotation_is_path(node.annotation):
                        self.names.add(node.arg)
                elif isinstance(node, (ast.For, ast.comprehension)):
                    continue

    def is_path_like(self, node: ast.expr) -> bool:
        """Report whether an expression evaluates to a pathlib object.

        Args:
            node: Expression to classify.

        Returns:
            bool: True when the expression has recognised pathlib provenance.
        """
        if isinstance(node, ast.Call):
            name = _callee_name(node.func)
            if name in PATH_FACTORIES:
                return True
            if isinstance(node.func, ast.Attribute) and node.func.attr in {
                "resolve",
                "absolute",
                "expanduser",
                "parent",
                "with_suffix",
                "with_name",
                "joinpath",
            }:
                return self.is_path_like(node.func.value)
            return False
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
            return self.is_path_like(node.left) or self.is_path_like(node.right)
        if isinstance(node, ast.Attribute):
            if node.attr in {"parent", "parents"}:
                return self.is_path_like(node.value)
            return _dotted_name(node) in self.names
        if isinstance(node, ast.Name):
            return node.id in self.names
        if isinstance(node, ast.Subscript):
            return self.is_path_like(node.value)
        return False

    def _record_target(self, target: ast.expr) -> None:
        """Add an assignment target to the known-path name set.

        Args:
            target: Assignment target expression.
        """
        if isinstance(target, ast.Name):
            self.names.add(target.id)
        elif isinstance(target, ast.Attribute):
            dotted = _dotted_name(target)
            if dotted:
                self.names.add(dotted)
        elif isinstance(target, (ast.Tuple, ast.List)):
            for element in target.elts:
                self._record_target(element)

    @staticmethod
    def _annotation_is_path(annotation: ast.expr) -> bool:
        """Report whether an annotation names a pathlib type.

        Args:
            annotation: Annotation expression.

        Returns:
            bool: True when the annotation resolves to a pathlib type name.
        """
        if isinstance(annotation, ast.Constant) and isinstance(annotation.value, str):
            return annotation.value.split("[")[0].split(".")[-1] in PATH_FACTORIES
        name = _callee_name(annotation)
        if name in PATH_FACTORIES:
            return True
        if isinstance(annotation, ast.Subscript):
            return _PathProvenance._annotation_is_path(annotation.slice)
        if isinstance(annotation, ast.BinOp) and isinstance(annotation.op, ast.BitOr):
            return _PathProvenance._annotation_is_path(annotation.left) or _PathProvenance._annotation_is_path(
                annotation.right
            )
        return False


def _dotted_name(node: ast.expr) -> str:
    """Render an attribute chain as a dotted string.

    Args:
        node: Expression that may be a ``Name`` or nested ``Attribute``.

    Returns:
        str: Dotted name, or an empty string when the chain is not static.
    """
    parts: list[str] = []
    current: ast.expr = node
    while isinstance(current, ast.Attribute):
        parts.append(current.attr)
        current = current.value
    if isinstance(current, ast.Name):
        parts.append(current.id)
        return ".".join(reversed(parts))
    return ""


def _callee_name(node: ast.expr) -> str:
    """Return the final identifier of a callee expression.

    Args:
        node: Callee expression.

    Returns:
        str: Trailing identifier, or an empty string when there is none.
    """
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Call):
        return _callee_name(node.func)
    return ""


def iter_python_files(root: Path) -> Iterator[Path]:
    """Yield every scannable Python file under a root.

    Args:
        root: Directory to walk.

    Yields:
        Path: Python source files outside the skipped directory names.
    """
    for candidate in sorted(root.rglob("*.py")):
        if any(part in SKIP_DIR_NAMES for part in candidate.parts):
            continue
        yield candidate


def _collect_open_aliases(tree: ast.AST) -> dict[str, str]:
    """Map local names bound to an imported ``open`` onto their source module.

    Args:
        tree: Parsed module AST.

    Returns:
        dict: Local name to top-level source module name.
    """
    aliases: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            for alias in node.names:
                if alias.name == "open":
                    aliases[alias.asname or "open"] = node.module.split(".")[0]
    return aliases


def _classify_callee(
    call: ast.Call,
    aliases: dict[str, str],
    provenance: _PathProvenance,
) -> tuple[str, str, str] | None:
    """Decide whether a call is a file opener this rule governs.

    Args:
        call: Call node under inspection.
        aliases: Local-name to module map for imported ``open`` bindings.
        provenance: Module-local pathlib provenance record.

    Returns:
        tuple: ``(disposition, opener, shape)`` where disposition is ``CHECK`` or
        ``EXEMPT``, or None when the call is not a file opener at all.
    """
    func = call.func
    if isinstance(func, ast.Name):
        source = aliases.get(func.id)
        if source is not None:
            if source in EXEMPT_OPENER_MODULES:
                return ("EXEMPT", "{}.open".format(source), BUILTIN_SHAPE)
            return ("CHECK", "{}.open as {}".format(source, func.id), BUILTIN_SHAPE)
        if func.id == "open":
            return ("CHECK", "builtin open", BUILTIN_SHAPE)
        return None
    if not isinstance(func, ast.Attribute):
        return None
    if func.attr in EXEMPT_OPENER_FUNCTIONS:
        return ("EXEMPT", func.attr, BUILTIN_SHAPE)
    if func.attr != "open":
        return None
    base = _callee_name(func.value) if not isinstance(func.value, ast.Call) else ""
    if base in TEXT_OPENER_MODULES:
        return ("CHECK", "{}.open".format(base), BUILTIN_SHAPE)
    if base in EXEMPT_OPENER_MODULES:
        return ("EXEMPT", "{}.open".format(base), BUILTIN_SHAPE)
    if provenance.is_path_like(func.value):
        return ("CHECK", "pathlib .open()", PATH_SHAPE)
    return None


def _has_star_kwargs(call: ast.Call) -> bool:
    """Report whether a call forwards an unresolvable ``**kwargs`` mapping.

    Args:
        call: Call node under inspection.

    Returns:
        bool: True when a double-star argument is present.
    """
    return any(keyword.arg is None for keyword in call.keywords)


def _encoding_supplied(call: ast.Call, shape: str) -> bool:
    """Report whether the call passes ``encoding`` by keyword or position.

    Args:
        call: Call node under inspection.
        shape: Argument shape, either builtin or path-method.

    Returns:
        bool: True when an encoding argument is present.
    """
    for keyword in call.keywords:
        if keyword.arg == "encoding":
            return True
    return len(call.args) > ENCODING_INDEX[shape]


def _mode_expression(call: ast.Call, shape: str) -> ast.expr | None:
    """Return the expression supplying the mode argument, if any.

    Args:
        call: Call node under inspection.
        shape: Argument shape, either builtin or path-method.

    Returns:
        ast.expr: Mode expression, or None when the call omits mode entirely.
    """
    for keyword in call.keywords:
        if keyword.arg == "mode":
            return keyword.value
    index = MODE_INDEX[shape]
    if len(call.args) > index:
        return call.args[index]
    return None


def analyse_source(source: str, display_path: str) -> list[Finding]:
    """Classify every governed file-opening call in one module.

    A single traversal visits each node once and dispatches on ``Call`` nodes, so
    adding opener forms does not add tree walks.

    Args:
        source: Python source text.
        display_path: Path string used in the returned findings.

    Returns:
        list: One Finding per recognised opener call.

    Raises:
        SyntaxError: When the source does not parse.
    """
    tree = ast.parse(source, filename=display_path)
    aliases = _collect_open_aliases(tree)
    provenance = _PathProvenance()
    provenance.collect(tree)

    findings: list[Finding] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        classified = _classify_callee(node, aliases, provenance)
        if classified is None:
            continue
        disposition, opener, shape = classified
        if disposition == "EXEMPT":
            findings.append(Finding(display_path, node.lineno, "EXEMPT", opener, "not a text-file opener"))
            continue
        if _encoding_supplied(node, shape):
            findings.append(Finding(display_path, node.lineno, "OK", opener, "encoding supplied"))
            continue
        if _has_star_kwargs(node):
            findings.append(
                Finding(display_path, node.lineno, "UNDECIDABLE", opener, "**kwargs may or may not carry encoding")
            )
            continue
        mode = _mode_expression(node, shape)
        if mode is None:
            findings.append(
                Finding(display_path, node.lineno, "VIOLATION", opener, "mode-less call defaults to text mode 'r'")
            )
            continue
        if isinstance(mode, ast.Constant) and isinstance(mode.value, str):
            if "b" in mode.value:
                findings.append(
                    Finding(display_path, node.lineno, "EXEMPT", opener, "binary mode {!r}".format(mode.value))
                )
            else:
                findings.append(
                    Finding(display_path, node.lineno, "VIOLATION", opener, "text mode {!r}".format(mode.value))
                )
            continue
        findings.append(
            Finding(display_path, node.lineno, "UNDECIDABLE", opener, "mode is not a statically resolvable literal")
        )
    return findings


def scan_paths(files: Iterable[Path], root: Path) -> tuple[list[Finding], list[tuple[str, str]]]:
    """Analyse a set of files and separate parse failures from findings.

    Args:
        files: Python files to analyse.
        root: Root used to render repository-relative display paths.

    Returns:
        tuple: ``(findings, unreadable)`` where unreadable holds
        ``(path, reason)`` pairs for files that could not be read or parsed.
    """
    findings: list[Finding] = []
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
            findings.extend(analyse_source(source, display))
        except SyntaxError as exc:
            unreadable.append((display, "unparsed: {}".format(exc)))
    return findings, unreadable


def select(findings: Iterable[Finding], verdict: str) -> list[Finding]:
    """Filter findings down to a single verdict.

    Args:
        findings: Findings to filter.
        verdict: Verdict label to keep.

    Returns:
        list: Matching findings.
    """
    return [finding for finding in findings if finding.verdict == verdict]


def main(argv: list[str] | None = None) -> int:
    """Run the gate over a repository tree.

    Args:
        argv: Command-line arguments, defaulting to ``sys.argv[1:]``.

    Returns:
        int: 0 when no violation, undecidable call, or unreadable file remains.
    """
    parser = argparse.ArgumentParser(description="Verify explicit encoding= at every text-mode open().")
    parser.add_argument("--root", default=str(REPO_ROOT), help="Directory to scan (defaults to the repository root).")
    parser.add_argument("--verbose", action="store_true", help="List exempt and compliant call sites as well.")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    findings, unreadable = scan_paths(iter_python_files(root), root)

    violations = select(findings, "VIOLATION")
    undecidable = select(findings, "UNDECIDABLE")
    exempt = select(findings, "EXEMPT")
    compliant = select(findings, "OK")

    print("verify_open_encoding: scanned {}".format(root))
    print(
        "  violations={}  undecidable={}  exempt={}  compliant={}  unreadable={}".format(
            len(violations), len(undecidable), len(exempt), len(compliant), len(unreadable)
        )
    )

    if args.verbose:
        for finding in exempt + compliant:
            print("  ok      {}".format(finding.describe()))

    for finding in violations:
        print("  FAIL    {}".format(finding.describe()))
    for finding in undecidable:
        print("  UNKNOWN {}".format(finding.describe()))
    for path, reason in unreadable:
        print("  ERROR   {}  {}".format(path, reason))

    if violations or undecidable or unreadable:
        print("verify_open_encoding: FAILED")
        return 1
    print("verify_open_encoding: PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())

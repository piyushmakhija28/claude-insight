"""Verify V2-035 / PRD NFR-2 / SRS NFR-8: no fixed timeout on the long-running pipeline path.

A fixed wall-clock timeout on a pipeline step is a temporal proxy for a question
it cannot answer -- "is this making progress?" -- and it gets that question wrong
in both directions, aborting healthy slow work and permitting unhealthy fast
loops. ADR-016 replaces the proxy with five non-temporal mechanisms. This gate
enforces the absence half of that; ``tests/test_nfr2_liveness.py`` enforces the
presence half.

WHY THIS IS AN AST PASS AND NOT A GREP
--------------------------------------
The token this gate looks for, ``timeout=``, appears in prose constantly: in
docstrings explaining what a parameter used to do, in comments recording why a
value was raised, in log-format strings. A line-oriented pattern cannot tell a
keyword argument from a sentence about one. A prior gate in this repository over
``open(`` fired on docstrings and comments until it was rewritten as an AST pass,
and the same failure mode applies here exactly.

So detection is structural. A timeout is a ``ast.keyword`` named ``timeout``, a
call to ``signal.alarm``, or a call to ``socket.setdefaulttimeout``. Text that
merely says "timeout=" is not any of those, and cannot be, which is a stronger
guarantee than a cleverer regular expression could give. Both directions are
covered by specificity tests: prose does not fire, and a real keyword does.

CLASSIFYING THE VALUE IS THE WHOLE JUDGEMENT
--------------------------------------------
NFR-2 bans an UNCONDITIONAL FIXED timeout and permits a configurable one that
defaults to unbounded. Those two can be the same token at the call site, so the
gate resolves what the value actually is:

* ``UNBOUNDED``      -- literal None, or a parameter defaulting to None.
* ``CONFIGURABLE``   -- resolves through ``env_optional_seconds``, which returns
                        None when unset. Configurable AND unbounded by default.
* ``FIXED_LITERAL``  -- a number written at the call site.
* ``FIXED_DEFAULT``  -- a name or call resolving to a finite default, including
                        the ``int(os.getenv("X", "60"))`` shape. An env var makes
                        the value overridable but leaves the DEFAULT finite, so a
                        run nobody configured is still aborted at 60 seconds.
                        Overridability is not the property NFR-2 asks for.
* ``UNRESOLVED``     -- a shape this gate cannot follow.

``UNRESOLVED`` fails, deliberately. Defining the accepted set and failing the
complement means a shape nobody anticipated is caught rather than silently
allowed, which is the failure mode a gate exists to prevent.

SCOPE, STATED PRECISELY BECAUSE THE ACCEPTANCE CRITERION IS AMBIGUOUS
---------------------------------------------------------------------
The criterion says the scan "returns zero unconditional fixed timeouts on the
long-running pipeline path, scanned across BOTH the plugin's bundled code AND the
engine pipeline path". Those are two different quantities: a SCAN scope and a
ZERO condition. This gate reads them as written -- it scans the whole of
``langgraph_engine`` and the whole plugin tree, and it enforces zero on the
pipeline path.

ENFORCED_PATHS names that path explicitly rather than by heuristic: the Step 0/1
planning modules, the step-node implementations, the shared subprocess runner,
the faithfulness gate and the LLM entry point -- every module through which a
long-running unit of pipeline work actually flows. Everything else in
``langgraph_engine`` is scanned, classified and counted in the report, and is not
enforced. Opt-in integrations (SonarQube, Jenkins), diagram generators and CLI
availability probes are not the long-running pipeline path, and enforcing this
rule on them would be a different and larger change than the one this gate backs.
The report prints exactly how many sites that leaves, so the decision is visible
rather than buried.

THE DOCUMENTED EXCEPTIONS ARE A LIST, NOT A CATEGORY
-----------------------------------------------------
ADR-016 permits socket/HTTP-level timeouts on a single network I/O call, provided
they are configurable and raise a retryable error into a circuit breaker rather
than aborting the enclosing task. The acceptance criterion tightens that to
"exactly ONE documented exception".

A category-based exemption would let any number of sites qualify by argument.
DOCUMENTED_EXCEPTIONS is therefore an explicit list of file-and-symbol entries,
each with its justification, and the gate FAILS when it holds more than
MAX_DOCUMENTED_EXCEPTIONS entries. That makes the count an enforced property
rather than a claim in a report.
"""

from __future__ import annotations

import argparse
import ast
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Iterator, Optional

REPO_ROOT = Path(__file__).resolve().parents[1]

SCAN_SCOPE = ("langgraph_engine", "plugin")

ENFORCED_PATHS = (
    "langgraph_engine/sdlc_pipeline/architecture/",
    "langgraph_engine/sdlc_pipeline/nodes/",
    "langgraph_engine/sdlc_pipeline/helpers.py",
    "langgraph_engine/sdlc_pipeline/faithfulness_gate.py",
    "langgraph_engine/llm_call.py",
    "langgraph_engine/liveness/",
    "plugin/",
)

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

TIMEOUT_KEYWORDS = frozenset({"timeout"})

BANNED_CALLS = (("signal", "alarm"), ("socket", "setdefaulttimeout"))

UNBOUNDED_RESOLVERS = frozenset({"env_optional_seconds", "_env_optional_seconds"})

FINITE_RESOLVERS = frozenset({"_env_int", "env_int", "getenv", "getint"})

VALUE_UNBOUNDED = "UNBOUNDED"

VALUE_CONFIGURABLE = "CONFIGURABLE"

VALUE_FIXED_LITERAL = "FIXED_LITERAL"

VALUE_FIXED_DEFAULT = "FIXED_DEFAULT"

VALUE_UNRESOLVED = "UNRESOLVED"

FAILING_VALUE_CLASSES = frozenset({VALUE_FIXED_LITERAL, VALUE_FIXED_DEFAULT, VALUE_UNRESOLVED})

MAX_DOCUMENTED_EXCEPTIONS = 1

DOCUMENTED_EXCEPTIONS = {
    "langgraph_engine/llm_call.py::call::_anthropic_socket_timeout": (
        "The one exception ADR-016 permits: a socket/HTTP timeout on a SINGLE "
        "Anthropic API call. Configurable through ANTHROPIC_HTTP_TIMEOUT, "
        "disabled entirely by setting it to 0, and routed through the "
        "anthropic_api circuit breaker so a lapse is a retryable failure rather "
        "than an abort of the enclosing pipeline step."
    ),
}


@dataclass(frozen=True)
class Site:
    """One timeout construct found in one file.

    Attributes:
        path: Repository-relative POSIX path of the containing file.
        line: 1-based line number.
        construct: What was found -- a keyword name, or a banned call's name.
        node_type: Label for the enclosing call, for evidence.
        value_class: How the value resolves, one of the VALUE_* constants.
        detail: Short rendering of the value, for the report.
        symbol: Enclosing function name, used to match documented exceptions.
    """

    path: str
    line: int
    construct: str
    node_type: str
    value_class: str
    detail: str
    symbol: str

    def record(self) -> str:
        """Return the per-site evidence record.

        Returns:
            str: ``file:line:construct:node_type:value_class:detail``.
        """
        return "{}:{}:{}:{}:{}:{}".format(
            self.path, self.line, self.construct, self.node_type, self.value_class, self.detail
        )

    def exception_key(self) -> str:
        """Return the key this site would match in DOCUMENTED_EXCEPTIONS.

        The key names the file, the enclosing function AND the resolved value, so
        an exemption cannot silently widen to a second site that merely happens
        to share a common method name such as ``call``.
        """
        return "{}::{}::{}".format(self.path, self.symbol, self.detail)

    def is_on_enforced_path(self) -> bool:
        """Report whether this site sits on the long-running pipeline path."""
        return any(self.path.startswith(prefix) for prefix in ENFORCED_PATHS)

    def is_violation(self) -> bool:
        """Report whether this site must be zero for the gate to pass."""
        if not self.is_on_enforced_path():
            return False
        if self.value_class not in FAILING_VALUE_CLASSES:
            return False
        return self.exception_key() not in DOCUMENTED_EXCEPTIONS


@dataclass
class ModuleFacts:
    """Resolution context for one module.

    Attributes:
        assignments: Module-level name to the expression assigned to it.
        params: Function name to parameter name to its default expression.
        locals_by_func: Function name to local name to the expression assigned.
    """

    assignments: dict = field(default_factory=dict)
    params: dict = field(default_factory=dict)
    locals_by_func: dict = field(default_factory=dict)


def _module_facts(tree: ast.AST) -> ModuleFacts:
    """Collect the module-level names and function parameters a value may refer to.

    Args:
        tree: Parsed module AST.

    Returns:
        ModuleFacts: Assignment and parameter defaults available for resolution.
    """
    facts = ModuleFacts()
    for node in tree.body if isinstance(tree, ast.Module) else []:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    facts.assignments[target.id] = node.value
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.value is not None:
            facts.assignments[node.target.id] = node.value
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        table = {}
        args = node.args
        positional = list(args.posonlyargs) + list(args.args)
        offset = len(positional) - len(args.defaults)
        for index, arg in enumerate(positional):
            default = args.defaults[index - offset] if index >= offset else None
            table[arg.arg] = default
        for arg, default in zip(args.kwonlyargs, args.kw_defaults):
            table[arg.arg] = default
        facts.params[node.name] = table
        bindings = {}
        for inner in ast.walk(node):
            if isinstance(inner, ast.Assign):
                for target in inner.targets:
                    if isinstance(target, ast.Name):
                        bindings.setdefault(target.id, inner.value)
            elif isinstance(inner, ast.AnnAssign) and isinstance(inner.target, ast.Name) and inner.value is not None:
                bindings.setdefault(inner.target.id, inner.value)
        facts.locals_by_func[node.name] = bindings
    return facts


def _call_name(node: ast.AST) -> str:
    """Render the dotted name of a call target, or an empty string.

    Args:
        node: The ``func`` of an ``ast.Call``.

    Returns:
        str: Dotted name such as ``os.getenv``, or ``""`` when not a name.
    """
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = _call_name(node.value)
        return "{}.{}".format(base, node.attr) if base else node.attr
    return ""


def classify_value(value: Optional[ast.AST], facts: ModuleFacts, enclosing: str, depth: int = 0) -> tuple:
    """Decide what a timeout value actually resolves to.

    Args:
        value: The expression supplied as the timeout, or None when absent.
        facts: Module-level assignments and parameter defaults.
        enclosing: Name of the enclosing function, for parameter lookup.
        depth: Recursion guard against a name assigned from itself.

    Returns:
        tuple: ``(value_class, detail)``.
    """
    if depth > 6:
        return VALUE_UNRESOLVED, "resolution depth exceeded"
    if value is None:
        return VALUE_UNBOUNDED, "absent"
    if isinstance(value, ast.Constant):
        if value.value is None:
            return VALUE_UNBOUNDED, "None"
        if isinstance(value.value, bool):
            return VALUE_UNRESOLVED, repr(value.value)
        if isinstance(value.value, (int, float)):
            return VALUE_FIXED_LITERAL, repr(value.value)
        return VALUE_UNRESOLVED, repr(value.value)
    if isinstance(value, ast.BinOp):
        left = classify_value(value.left, facts, enclosing, depth + 1)
        right = classify_value(value.right, facts, enclosing, depth + 1)
        for outcome in (left, right):
            if outcome[0] in FAILING_VALUE_CLASSES:
                return VALUE_FIXED_DEFAULT, "arithmetic on " + outcome[1]
        return left
    if isinstance(value, ast.Call):
        name = _call_name(value.func)
        tail = name.rsplit(".", 1)[-1]
        if tail in UNBOUNDED_RESOLVERS:
            return VALUE_CONFIGURABLE, name
        if tail in FINITE_RESOLVERS:
            return VALUE_FIXED_DEFAULT, name
        if name in ("int", "float") and value.args:
            inner = classify_value(value.args[0], facts, enclosing, depth + 1)
            return (VALUE_FIXED_DEFAULT, name + "(" + inner[1] + ")") if inner[0] != VALUE_CONFIGURABLE else inner
        if tail in ("min", "max"):
            for argument in value.args:
                outcome = classify_value(argument, facts, enclosing, depth + 1)
                if outcome[0] in FAILING_VALUE_CLASSES:
                    return VALUE_FIXED_DEFAULT, name + " over " + outcome[1]
            return VALUE_CONFIGURABLE, name
        return VALUE_UNRESOLVED, name or "call"
    if isinstance(value, ast.Name):
        params = facts.params.get(enclosing, {})
        if value.id in params:
            return classify_value(params[value.id], facts, enclosing, depth + 1)
        bindings = facts.locals_by_func.get(enclosing, {})
        if value.id in bindings:
            return classify_value(bindings[value.id], facts, enclosing, depth + 1)
        if value.id in facts.assignments:
            return classify_value(facts.assignments[value.id], facts, "", depth + 1)
        return VALUE_UNRESOLVED, value.id
    if isinstance(value, ast.Attribute):
        return VALUE_UNRESOLVED, _call_name(value)
    return VALUE_UNRESOLVED, type(value).__name__


def _enclosing_functions(tree: ast.AST) -> dict:
    """Map every node identity onto the name of the function containing it.

    Args:
        tree: Parsed module AST.

    Returns:
        dict: ``id(node)`` to enclosing function name, empty at module level.
    """
    owner: dict = {}

    def walk(node: ast.AST, name: str) -> None:
        for child in ast.iter_child_nodes(node):
            child_name = child.name if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) else name
            owner[id(child)] = child_name
            walk(child, child_name)

    walk(tree, "")
    return owner


def analyse_source(source: str, display_path: str) -> list:
    """Find and classify every timeout construct in one module.

    Args:
        source: Python source text.
        display_path: Repository-relative path used in the returned sites.

    Returns:
        list: One Site per construct found, ordered by line.

    Raises:
        SyntaxError: When the source does not parse.
    """
    tree = ast.parse(source, filename=display_path)
    facts = _module_facts(tree)
    owner = _enclosing_functions(tree)
    found: list = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        enclosing = owner.get(id(node), "")
        target = _call_name(node.func)

        for prefix, attr in BANNED_CALLS:
            if target in (attr, "{}.{}".format(prefix, attr)):
                value = node.args[0] if node.args else None
                value_class, detail = classify_value(value, facts, enclosing)
                if value_class == VALUE_UNBOUNDED and node.args:
                    value_class = VALUE_UNRESOLVED
                found.append(Site(display_path, node.lineno, target, target, value_class, detail, enclosing))

        for keyword in node.keywords:
            if keyword.arg not in TIMEOUT_KEYWORDS:
                continue
            value_class, detail = classify_value(keyword.value, facts, enclosing)
            found.append(
                Site(display_path, keyword.value.lineno, "timeout=", target or "call", value_class, detail, enclosing)
            )

    return sorted(found, key=lambda item: (item.line, item.construct))


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


def scan(files: Iterable[Path], root: Path) -> tuple:
    """Run the scan over a set of files.

    Args:
        files: Python files to analyse.
        root: Root used to render repository-relative display paths.

    Returns:
        tuple: ``(sites, unreadable)`` where unreadable holds ``(path, reason)``.
    """
    sites: list = []
    unreadable: list = []
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
            sites.extend(analyse_source(source, display))
        except SyntaxError as exc:
            unreadable.append((display, "unparsed: {}".format(exc)))
    return sites, unreadable


def summarise(sites: Iterable[Site]) -> dict:
    """Count sites per value class.

    Args:
        sites: Sites to tally.

    Returns:
        dict: Value class to count, with every class present.
    """
    counts = {
        VALUE_UNBOUNDED: 0,
        VALUE_CONFIGURABLE: 0,
        VALUE_FIXED_LITERAL: 0,
        VALUE_FIXED_DEFAULT: 0,
        VALUE_UNRESOLVED: 0,
    }
    for site in sites:
        counts[site.value_class] = counts.get(site.value_class, 0) + 1
    return counts


def main(argv: Optional[list] = None) -> int:
    """Run the gate over a repository tree.

    Args:
        argv: Command-line arguments, defaulting to ``sys.argv[1:]``.

    Returns:
        int: 0 when no enforced fixed timeout and no unreadable file remains.
    """
    parser = argparse.ArgumentParser(description="Classify and gate fixed timeouts on the pipeline path.")
    parser.add_argument("--root", default=str(REPO_ROOT), help="Repository root to scan.")
    parser.add_argument("--verbose", action="store_true", help="List every site, not just violations.")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    files = list(iter_python_files(root, SCAN_SCOPE))
    sites, unreadable = scan(files, root)

    counts = summarise(sites)
    enforced = [site for site in sites if site.is_on_enforced_path()]
    violations = [site for site in sites if site.is_violation()]
    exempted = [site for site in enforced if site.exception_key() in DOCUMENTED_EXCEPTIONS]
    unenforced = [site for site in sites if not site.is_on_enforced_path()]
    unenforced_fixed = [site for site in unenforced if site.value_class in (VALUE_FIXED_LITERAL, VALUE_FIXED_DEFAULT)]
    unenforced_unresolved = [site for site in unenforced if site.value_class == VALUE_UNRESOLVED]

    print("verify_no_fixed_timeouts: scanned {} files under {}".format(len(files), root))
    print(
        "  sites={}  UNBOUNDED={}  CONFIGURABLE={}  FIXED_LITERAL={}  FIXED_DEFAULT={}  UNRESOLVED={}".format(
            len(sites),
            counts[VALUE_UNBOUNDED],
            counts[VALUE_CONFIGURABLE],
            counts[VALUE_FIXED_LITERAL],
            counts[VALUE_FIXED_DEFAULT],
            counts[VALUE_UNRESOLVED],
        )
    )
    print("  on enforced pipeline path: {}  (of which exempted: {})".format(len(enforced), len(exempted)))
    print(
        "  outside the enforced path (reported, not gated): fixed={}  unresolved={}  total-would-fail={}".format(
            len(unenforced_fixed), len(unenforced_unresolved), len(unenforced_fixed) + len(unenforced_unresolved)
        )
    )
    print("  documented exceptions declared: {} (max {})".format(len(DOCUMENTED_EXCEPTIONS), MAX_DOCUMENTED_EXCEPTIONS))

    if args.verbose:
        for site in sorted(sites, key=lambda item: (item.path, item.line)):
            print("  {}".format(site.record()))

    for site in exempted:
        print("  EXEMPT  {}".format(site.record()))
    for site in violations:
        print("  FAIL    {}".format(site.record()))
    for path, reason in unreadable:
        print("  ERROR   {}  {}".format(path, reason))

    too_many_exceptions = len(DOCUMENTED_EXCEPTIONS) > MAX_DOCUMENTED_EXCEPTIONS
    if too_many_exceptions:
        print(
            "  FAIL    {} documented exceptions declared; the criterion permits {}".format(
                len(DOCUMENTED_EXCEPTIONS), MAX_DOCUMENTED_EXCEPTIONS
            )
        )

    if violations or unreadable or too_many_exceptions:
        print("verify_no_fixed_timeouts: FAILED")
        return 1
    print("verify_no_fixed_timeouts: PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())

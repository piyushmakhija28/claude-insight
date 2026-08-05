"""Audit the Stop hook for dangling script references (V2-034, PRD FR-21 / SRS FR-33).

V2-033 measured nine referenced scripts across ``hooks/stop_notifier/`` and found
every one inert. V2-034's acceptance criteria are scoped more narrowly than that
census: criterion 1 speaks of references "removed from ``hooks/stop_notifier/core.py``",
and ``core.py`` carries exactly seven such references. The remaining two of V2-033's
nine live in ``post_impl.py`` and ``helpers.py`` and are out of this issue's scope.
Both figures are therefore correct at their own scope and neither is stale; the
scope is recorded in ``SCOPE_NOTE`` so the reconciliation is not lost.

WHY A DANGLING REFERENCE IS DEFINED BY BASENAME ABSENCE. Statically evaluating a
``Path`` expression built from seven chained ``/`` operands would require partial
interpretation of the module, and a partial interpreter that silently mis-resolves
one operand reports a verdict nobody can trust. This module instead asks a question
that is decidable from the filesystem alone: does any file with that basename exist
anywhere under the repository root? A reference naming a basename that exists nowhere
CANNOT resolve, whatever the path expression around it does, so ``DANGLING`` is a
sound verdict rather than an inferred one. A reference whose basename does exist is
reported ``SATISFIABLE`` and never ``LIVE``: whether the surrounding expression
actually reaches that file is a stronger claim than this module measures, and
overstating it is the failure mode the audit exists to prevent.

The audit is driven by tests in ``tests/test_stop_hook_dead_references.py``, which
call the functions stored here rather than re-authoring them.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_DIR = REPO_ROOT / "hooks" / "stop_notifier"
CORE_MODULE = PACKAGE_DIR / "core.py"
LEDGER_PATH = REPO_ROOT / "docs" / "reports" / "capability-disposition-ledger.md"

RETIRED_SCRIPTS = (
    "git-auto-commit-policy.py",
    "auto-save-session.py",
    "archive-old-sessions.py",
    "session-pruner.py",
    "common-failures-prevention.py",
    "preference-auto-tracker.py",
    "plan-session-archiver.py",
)

OUT_OF_SCOPE_SCRIPTS = (
    "sync-version.py",
    "voice-notifier.py",
)

SCOPE_NOTE = (
    "V2-034 names 7 references; V2-033 measured 9 across the package. The 7 are exactly "
    "the script references in core.py, which is the file criterion 1 names. The other 2 "
    "(sync-version.py in post_impl.py, voice-notifier.py in helpers.py) are out of scope."
)

DISPOSITION_VOCABULARY = (
    "keep-as-is",
    "port-to-plugin",
    "port-to-MCP",
    "demote-to-advisory",
    "delete",
)

RETIRED = "RETIRED"
DANGLING = "DANGLING"
SATISFIABLE = "SATISFIABLE"

_SKIP_DIRS = frozenset({"__pycache__", ".git", ".pytest_cache"})


@dataclass(frozen=True)
class Reference:
    """One textual occurrence of a script basename inside the audited package.

    Attributes:
        script: Script basename that was searched for.
        path: Repository-relative path of the file carrying the occurrence.
        line_no: 1-based line number of the occurrence.
        text: Stripped source line carrying the occurrence.
    """

    script: str
    path: str
    line_no: int
    text: str


@dataclass(frozen=True)
class ScriptVerdict:
    """The audit outcome for one script basename.

    Attributes:
        script: Script basename audited.
        state: One of ``RETIRED``, ``DANGLING`` or ``SATISFIABLE``.
        references: Every occurrence found inside the audited package.
        targets: Repository-relative paths of real files with this basename.
    """

    script: str
    state: str
    references: tuple[Reference, ...]
    targets: tuple[str, ...]


def iter_python_files(package_dir: Path) -> list[Path]:
    """List the Python source files of a package, ignoring caches.

    Args:
        package_dir: Directory to walk.

    Returns:
        Sorted list of ``.py`` files, excluding ``__pycache__`` and VCS trees.
    """
    if not package_dir.is_dir():
        return []
    found = [
        path for path in package_dir.rglob("*.py") if not _SKIP_DIRS.intersection(path.relative_to(package_dir).parts)
    ]
    return sorted(found)


def scan_references(package_dir: Path, script: str) -> list[Reference]:
    """Find every textual occurrence of one script basename inside a package.

    The basename is matched literally with its ``.py`` suffix, bounded so that
    ``session-pruner.py`` does not match ``my-session-pruner.py``. This is the
    same question acceptance criterion 2's grep asks, expressed once so the tests
    and the audit cannot disagree about what "a reference" means.

    Args:
        package_dir: Directory to search.
        script: Script basename, including its ``.py`` suffix.

    Returns:
        Occurrences in file then line order.
    """
    pattern = re.compile(r"(?<![\w.-])" + re.escape(script) + r"(?![\w])")
    references: list[Reference] = []
    for path in iter_python_files(package_dir):
        try:
            lines = path.read_text(encoding="utf-8").split("\n")
        except OSError:
            continue
        for line_no, line in enumerate(lines, start=1):
            if pattern.search(line):
                references.append(
                    Reference(
                        script=script,
                        path=_relative(path),
                        line_no=line_no,
                        text=line.strip(),
                    )
                )
    return references


def find_targets(repo_root: Path, script: str) -> list[str]:
    """Locate every real file in the repository carrying this basename.

    Args:
        repo_root: Repository root to search.
        script: Script basename, including its ``.py`` suffix.

    Returns:
        Sorted repository-relative paths of matching files.
    """
    if not repo_root.is_dir():
        return []
    found = [
        _relative(path, repo_root)
        for path in repo_root.rglob(script)
        if path.is_file() and not _SKIP_DIRS.intersection(path.relative_to(repo_root).parts)
    ]
    return sorted(found)


def audit_script(package_dir: Path, repo_root: Path, script: str) -> ScriptVerdict:
    """Classify one script basename against the two acceptance criteria.

    Args:
        package_dir: Package searched for references.
        repo_root: Repository root searched for real target files.
        script: Script basename, including its ``.py`` suffix.

    Returns:
        ``RETIRED`` when no reference remains; ``SATISFIABLE`` when references
        remain and a real file with that basename exists; ``DANGLING`` when
        references remain and no such file exists anywhere.
    """
    references = tuple(scan_references(package_dir, script))
    targets = tuple(find_targets(repo_root, script))
    if not references:
        state = RETIRED
    elif targets:
        state = SATISFIABLE
    else:
        state = DANGLING
    return ScriptVerdict(script=script, state=state, references=references, targets=targets)


def audit_all(package_dir: Path = PACKAGE_DIR, repo_root: Path = REPO_ROOT, scripts=RETIRED_SCRIPTS):
    """Audit every in-scope script basename.

    Args:
        package_dir: Package searched for references.
        repo_root: Repository root searched for real target files.
        scripts: Basenames to audit.

    Returns:
        One :class:`ScriptVerdict` per basename, in the order given.
    """
    return [audit_script(package_dir, repo_root, script) for script in scripts]


def evaluate_criterion_two(verdicts) -> dict:
    """Assert criterion 2: every reference is to a real file, or there are none.

    Args:
        verdicts: Verdicts produced by :func:`audit_all`.

    Returns:
        Mapping with ``verdict`` (``PASS``/``FAIL``) and a ``reasons`` list naming
        every dangling reference by file and line.
    """
    reasons = [
        f"{reference.path}:{reference.line_no} references {verdict.script!r}, "
        f"which exists nowhere in the repository"
        for verdict in verdicts
        if verdict.state == DANGLING
        for reference in verdict.references
    ]
    return {"verdict": "FAIL" if reasons else "PASS", "reasons": reasons}


def ledger_dispositions(ledger_path: Path = LEDGER_PATH) -> dict:
    """Read the retired-capability dispositions out of the ledger.

    Parses the V2-034 retirement table, which is keyed by script basename and is
    deliberately a SEPARATE table from the 27-row capability table. That table's
    gate asserts an empty symmetric difference against the machine-generated
    ``capability_loss.md``, so a row added there for a Stop-hook capability would
    fail it in direction B. The separate table is skipped by that gate's header
    match and is parsed here instead.

    Args:
        ledger_path: Path to the capability disposition ledger.

    Returns:
        Mapping of script basename to its Disposition cell value.
    """
    if not ledger_path.is_file():
        return {}
    dispositions: dict[str, str] = {}
    for line in ledger_path.read_text(encoding="utf-8").split("\n"):
        if not line.strip().startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 4:
            continue
        key = cells[0].strip("`")
        if key.endswith(".py"):
            dispositions[key] = cells[2]
    return dispositions


def evaluate_criterion_one(verdicts, dispositions) -> dict:
    """Assert criterion 1: each script is armed, or retired AND dispositioned.

    Args:
        verdicts: Verdicts produced by :func:`audit_all`.
        dispositions: Mapping from :func:`ledger_dispositions`.

    Returns:
        Mapping with ``verdict`` (``PASS``/``FAIL``) and a ``reasons`` list.
    """
    reasons: list[str] = []
    for verdict in verdicts:
        if verdict.state == DANGLING:
            reasons.append(f"{verdict.script!r} is neither armed nor retired: it still has dangling references")
            continue
        if verdict.state == SATISFIABLE:
            continue
        value = dispositions.get(verdict.script, "")
        if not value:
            reasons.append(f"{verdict.script!r} was retired but carries no disposition in the ledger")
        elif value not in DISPOSITION_VOCABULARY:
            reasons.append(f"{verdict.script!r} carries disposition {value!r}, outside the fixed vocabulary")
    return {"verdict": "FAIL" if reasons else "PASS", "reasons": reasons}


def _relative(path: Path, root: Path = REPO_ROOT) -> str:
    """Render a path repository-relative with forward slashes.

    Args:
        path: Path to render.
        root: Root to relativise against.

    Returns:
        Repository-relative POSIX-style string, or the absolute path when the
        path lies outside the root.
    """
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def main() -> int:
    """Print the audit and return a process exit status.

    Returns:
        0 when both criteria pass, 1 otherwise.
    """
    print(f"package: {PACKAGE_DIR}")
    print(f"scope  : {SCOPE_NOTE}")
    print("")
    verdicts = audit_all()
    for verdict in verdicts:
        detail = f" -> {', '.join(verdict.targets)}" if verdict.targets else ""
        print(f"  {verdict.state:<12} {verdict.script}{detail}")
        for reference in verdict.references:
            print(f"               {reference.path}:{reference.line_no}")
    print("")
    results = {
        "AC1": evaluate_criterion_one(verdicts, ledger_dispositions()),
        "AC2": evaluate_criterion_two(verdicts),
    }
    for code, result in results.items():
        print(f"[{result['verdict']}] {code}")
        for reason in result["reasons"]:
            print(f"       FAIL: {reason}")
    return 0 if all(result["verdict"] == "PASS" for result in results.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())

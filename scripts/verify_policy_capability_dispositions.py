"""Verify V2-008: every capability in the loss ledger carries a decided disposition.

Checks ``docs/phase-0-reverse-engineering/capability_loss.md`` against
``docs/reports/policy-implementation-audit-v2.md`` for the two acceptance
criteria recorded for V2-008 in ``docs/phase-6-sprint/github_issues.json``,
which restate PRD NFR-4 and SRS NFR-10.

AC1 Every capability the audit matrix accounts for carries a decided
    disposition: its accounting row's Post-plugin plan cell is non-empty and is
    not the literal ``disappeared``. NFR-4 forbids ``disappeared`` because it is
    the absence of a decision wearing the shape of one. A capability with no
    accounting row at all is recorded here as not evaluable rather than as a
    failure, because AC2 owns that condition; folding it in would leave two
    assertions unable to fail independently, which is how a check becomes
    untestable.
AC2 The ledger and the matrix agree, asserted as an empty symmetric difference
    in both directions rather than as a count of 25. A count check passes
    whenever two names are simultaneously wrong, which is the defect class this
    project has caught most often.
    Direction A is "the ledger names a capability no matrix row accounts for".
    Under NFR-4 that IS a disappearance: the capability is neither preserved by
    a kept enforcement point nor explicitly given up by a recorded disposition,
    and nothing in the matrix carries a decision about it.
    Direction B is "a matrix row rests its enforcement on a file inside the
    ledger's own declared scope, but no ledger entry names that file as an
    owner". The ledger's section headings declare exactly which packages it
    covers, and it claims one entry per lost capability within them, so a row
    grounded in a covered file that the ledger never names is a gap in the
    ledger rather than in the matrix.

SUP1 is a supporting integrity check, not one of V2-008's acceptance criteria.
    It compares the capability count CITED by the requirement sources against
    the count this gate enumerates from the ledger. It is exactly the count
    check that two simultaneous name errors defeat, so it cannot substitute for
    AC2 and is reported separately so the two are never confused.

THE JOIN, AND WHY IT IS THE OWNER FILE. The ledger is keyed by capability, the
matrix by policy filename; the two documents share no key. The only mechanical
correspondence between them is the ledger's ``Owner file`` column against the
paths the matrix cites in its ``Evidence`` column, so a matrix row accounts for
a capability when its Evidence names that capability's owner file. Resolving
the owner cell to a repository path needs the package root, which each section
heading declares in parentheses -- ``hooks/pre_tool_enforcer/``,
``hooks/post_tool_tracker/``, ``hooks/policy_tracking_helper.py``. Sections that
declare no root are out of the ledger's loss scope and are skipped; a table
inside such a section is an error rather than a silent skip, so a new lost
section cannot be added without a root and go unread. A looser join -- matching
a capability to any row citing anything in its package -- was rejected: it would
let one row's disposition silently discharge fifteen unrelated capabilities,
which is the reporting failure NFR-4 exists to prevent.

The cited count of 25 is CITED from ``prd-v2.md`` section 5's NFR-4 row and
``SRS.md``'s NFR-10 acceptance row, and is deliberately not treated as ground
truth. This gate enumerates the ledger itself and reports what it finds. If the
enumeration disagrees with 25, the citation is what is wrong; do not relax an
assertion to agree with either number.

Matrix parsing is imported from ``verify_policy_audit_matrix`` rather than
reimplemented. Two parsers over one artifact drift, and a drifted parser reports
on a document the other gates are not reading.

Exit status is 0 only when all three assertions pass; any failure exits 1. The
script takes no arguments by design, matching its siblings: an overridable input
path would let a caller point the gate at files other than the artifacts it
exists to guard.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

from verify_policy_audit_matrix import (
    MatrixError,
    Result,
    Row,
    is_table_row,
    named_paths,
    parse_matrix,
    split_cells,
    strip_cell,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = REPO_ROOT / "docs" / "reports" / "policy-implementation-audit-v2.md"
LEDGER_PATH = REPO_ROOT / "docs" / "phase-0-reverse-engineering" / "capability_loss.md"

CITED_CAPABILITY_COUNT = 25
DISAPPEARED = "disappeared"
LEDGER_TABLE_WIDTH = 3
SECTION_ROOT = re.compile(r"^##\s+.*?\((?P<root>[A-Za-z0-9_][A-Za-z0-9_./-]*(?:/|\.py))\s*,")
OWNER_FILE = re.compile(r"^`?([A-Za-z0-9_][A-Za-z0-9_./-]*\.py)`?")


class LedgerError(Exception):
    """Raised when capability_loss.md cannot be parsed unambiguously."""


@dataclass(frozen=True)
class Capability:
    """One data row of a capability_loss.md loss table.

    Attributes:
        line_no: 1-based line number of the row within the ledger.
        root: Package root declared by the section heading that carries the row.
        name: Capability column value, backticks and surrounding space removed.
        owner_cell: Owner file column value as written, including any
            parenthesised function list.
        owner_path: Repository-relative path of the owning file, resolved by
            joining the section root with the owner cell's leading path token.
        requirement: Requirement column value.
    """

    line_no: int
    root: str
    name: str
    owner_cell: str
    owner_path: str
    requirement: str


@dataclass(frozen=True)
class LedgerSection:
    """One ``## `` section of the ledger that declares a package root.

    Attributes:
        root: Package root as written in the heading's parenthetical.
        heading_line: 1-based line number of the section heading.
        entries: Table data rows in document order.
    """

    root: str
    heading_line: int
    entries: list[Capability]


def _resolve_owner_path(root: str, owner_cell: str, line_no: int) -> str:
    """Resolve one Owner file cell to a repository-relative path.

    Args:
        root: Package root declared by the section heading.
        owner_cell: Owner file cell text.
        line_no: 1-based line number of the row, used in error messages.

    Returns:
        The repository-relative path of the owning file.

    Raises:
        LedgerError: If the cell opens with no path token, or if the section
            root names a single file and the cell names a different one.
    """
    match = OWNER_FILE.match(owner_cell)
    if not match:
        raise LedgerError(f"line {line_no}: Owner file cell {owner_cell!r} does not open with a .py path")
    token = match.group(1)
    if root.endswith("/"):
        return root + token
    if Path(root).name != Path(token).name:
        raise LedgerError(f"line {line_no}: Owner file {token!r} does not match the section's declared file {root!r}")
    return root


def parse_ledger(text: str) -> list[LedgerSection]:
    """Parse every loss table out of capability_loss.md.

    A section is in the ledger's loss scope when its ``## `` heading declares a
    package root in parentheses. Sections declaring no root are out of scope and
    skipped, but a table appearing inside one is an error: silently skipping it
    would let a new loss section be added without a root and never be read.

    Args:
        text: Full text of the ledger document.

    Returns:
        The in-scope sections in document order.

    Raises:
        LedgerError: If a table row appears outside any root-declaring section;
            if a section carries a second table, a row of the wrong width, no
            ``Capability`` header row, or no data rows; if a section declares a
            root twice; or if no in-scope section is found at all.
    """
    lines = text.split("\n")
    collected: list[tuple[str, int, list[tuple[int, list[str]]]]] = []
    root: str | None = None
    heading_line = 0
    block: list[tuple[int, list[str]]] = []
    closed = False

    for line_no, line in enumerate(lines, start=1):
        if line.startswith("#"):
            if root is not None:
                collected.append((root, heading_line, block))
            match = SECTION_ROOT.match(line)
            root = match.group("root") if match else None
            heading_line = line_no
            block = []
            closed = False
            continue
        if is_table_row(line):
            if root is None:
                raise LedgerError(f"line {line_no}: table row outside any section declaring a package root")
            if closed:
                raise LedgerError(f"line {line_no}: section at line {heading_line} carries a second table")
            block.append((line_no, split_cells(line)))
        elif root is not None and block:
            closed = True
    if root is not None:
        collected.append((root, heading_line, block))

    sections: list[LedgerSection] = []
    seen_roots: set[str] = set()
    for section_root, section_line, rows in collected:
        if section_root in seen_roots:
            raise LedgerError(f"line {section_line}: package root {section_root!r} is declared by a second section")
        seen_roots.add(section_root)
        sections.append(
            LedgerSection(
                root=section_root, heading_line=section_line, entries=_parse_entries(rows, section_root, section_line)
            )
        )
    if not sections:
        raise LedgerError(f"no section of {LEDGER_PATH.name} declares a package root")
    return sections


def _parse_entries(rows: list[tuple[int, list[str]]], root: str, heading_line: int) -> list[Capability]:
    """Convert one section's raw table rows into capability entries.

    Args:
        rows: Pairs of (line number, unnormalised cells) in document order.
        root: Package root declared by the section heading.
        heading_line: 1-based line number of the section heading.

    Returns:
        The section's capability entries in document order.

    Raises:
        LedgerError: If the section carries no table, a row of the wrong width,
            no ``Capability`` header row, or no data rows.
    """
    if not rows:
        raise LedgerError(f"line {heading_line}: section declaring root {root!r} carries no table")
    entries: list[Capability] = []
    saw_header = False
    for line_no, cells in rows:
        if all(set(cell.strip()) <= set("-: ") for cell in cells):
            continue
        if len(cells) != LEDGER_TABLE_WIDTH:
            raise LedgerError(f"line {line_no}: expected {LEDGER_TABLE_WIDTH} cells, found {len(cells)}")
        name = strip_cell(cells[0])
        if not saw_header:
            if name.lower() != "capability":
                raise LedgerError(f"line {line_no}: section table does not open with a 'Capability' header row")
            saw_header = True
            continue
        owner_cell = cells[1].strip()
        entries.append(
            Capability(
                line_no=line_no,
                root=root,
                name=name,
                owner_cell=owner_cell,
                owner_path=_resolve_owner_path(root, owner_cell, line_no),
                requirement=strip_cell(cells[2]),
            )
        )
    if not entries:
        raise LedgerError(f"line {heading_line}: section declaring root {root!r} carries no data rows")
    return entries


def accounting_rows(capability: Capability, rows: list[Row]) -> list[Row]:
    """Find the matrix rows that account for one capability.

    A row accounts for a capability when its Evidence cell names the
    capability's owner file exactly. Substring matching is deliberately avoided
    so that ``core.py`` under one package cannot be credited to another.

    Args:
        capability: Capability under test.
        rows: Parsed matrix rows.

    Returns:
        Every matrix row whose Evidence names the owner file, in document order.
    """
    return [row for row in rows if capability.owner_path in named_paths(row.evidence)]


def in_ledger_scope(path: str, roots: list[str]) -> bool:
    """Report whether a cited path falls inside the ledger's declared scope.

    Args:
        path: Repository-relative path taken from an Evidence cell.
        roots: Package roots declared by the ledger's section headings.

    Returns:
        True when the path sits under a directory root or equals a file root.
    """
    return any(path.startswith(root) if root.endswith("/") else path == root for root in roots)


def check_dispositions_decided(capabilities: list[Capability], rows: list[Row]) -> Result:
    """Assert every accounted capability carries a decided disposition (AC1).

    Args:
        capabilities: Every capability the ledger enumerates.
        rows: Parsed matrix rows.

    Returns:
        Result listing every accounting row whose Post-plugin plan cell is empty
        or reads ``disappeared``, with the per-disposition tally and the
        not-evaluable set as notes.
    """
    failures: list[str] = []
    notes: list[str] = []
    tally: dict[str, int] = {}
    unaccounted: list[str] = []
    evaluated = 0

    for capability in capabilities:
        matches = accounting_rows(capability, rows)
        if not matches:
            unaccounted.append(capability.owner_path)
            continue
        evaluated += 1
        for row in matches:
            plan = row.plan.strip()
            if not plan:
                failures.append(
                    f"line {row.line_no} ({row.policy}): Post-plugin plan cell is empty; "
                    f"ledger line {capability.line_no} names {capability.owner_path} a lost capability"
                )
                continue
            if plan.lower() == DISAPPEARED:
                failures.append(
                    f"line {row.line_no} ({row.policy}): Post-plugin plan reads {DISAPPEARED!r}, "
                    f"which NFR-4 forbids as the absence of a decision"
                )
                continue
            tally[plan] = tally.get(plan, 0) + 1

    notes.append(
        f"capabilities enumerated: {len(capabilities)}; accounted for by a matrix row: {evaluated}; "
        f"undecided dispositions: {len(failures)}"
    )
    for value in sorted(tally):
        notes.append(f"{value}: {tally[value]}")
    if unaccounted:
        notes.append(
            "not evaluable -- no matrix row cites these owner files, AC2 direction A asserts on that: "
            + ", ".join(sorted(set(unaccounted)))
        )
    return Result("AC1", "Disposition decided for every accounted capability", not failures, failures, notes)


def check_capability_correspondence(sections: list[LedgerSection], rows: list[Row]) -> Result:
    """Assert the ledger and the matrix agree on capabilities, both ways (AC2).

    Three conditions fail this assertion: a capability name repeated inside the
    ledger, a ledger capability no matrix row accounts for (direction A), and a
    matrix row grounded in a file inside the ledger's declared scope that no
    ledger entry owns (direction B). None of them is a count comparison.

    Args:
        sections: Parsed ledger sections.
        rows: Parsed matrix rows.

    Returns:
        Result listing every discrepancy found in either direction.
    """
    failures: list[str] = []
    notes: list[str] = []
    capabilities = [entry for section in sections for entry in section.entries]
    roots = [section.root for section in sections]
    owned = {entry.owner_path for entry in capabilities}
    names = [entry.name for entry in capabilities]

    scoped: dict[str, list[Row]] = {}
    for row in rows:
        for path in named_paths(row.evidence):
            if path.endswith(".py") and in_ledger_scope(path, roots):
                scoped.setdefault(path, []).append(row)

    notes.append(
        f"ledger roots: {', '.join(roots)}; capabilities: {len(capabilities)}; "
        f"distinct owner files: {len(owned)}; matrix rows citing an in-scope file: {len(scoped)}"
    )
    notes.append("both directions of the symmetric difference are asserted; no assertion here is a count")

    for name in sorted({n for n in names if names.count(n) > 1}):
        failures.append(f"the ledger names the capability {name!r} more than once")
    for capability in capabilities:
        if not accounting_rows(capability, rows):
            failures.append(
                f"direction A -- ledger line {capability.line_no} names {capability.owner_path} "
                f"but no matrix row cites it, so no disposition accounts for it (NFR-4 disappearance)"
            )
    for path in sorted(set(scoped) - owned):
        carriers = ", ".join(sorted({row.policy for row in scoped[path]}))
        failures.append(
            f"direction B -- matrix row(s) {carriers} rest on {path}, which is inside the ledger's "
            f"declared scope, but no ledger entry names it as an owner file"
        )
    return Result("AC2", "Ledger capabilities and matrix rows correspond", not failures, failures, notes)


def check_cited_count(sections: list[LedgerSection]) -> Result:
    """Assert the cited capability count matches the enumeration (SUP1).

    Supporting check, not a V2-008 acceptance criterion. It compares the count
    the requirement sources cite against the count enumerated from the ledger,
    so a failure here is evidence the citation is wrong rather than evidence the
    matrix is. It is a count comparison and therefore blind to two simultaneous
    name errors; AC2 is what covers that case.

    Args:
        sections: Parsed ledger sections.

    Returns:
        Result comparing the cited count against the enumeration.
    """
    failures: list[str] = []
    notes: list[str] = []
    total = 0
    for section in sections:
        notes.append(f"section at line {section.heading_line} ({section.root}): {len(section.entries)} capabilities")
        total += len(section.entries)
    notes.append(f"cited by prd-v2.md NFR-4 and SRS.md NFR-10: {CITED_CAPABILITY_COUNT}; enumerated here: {total}")
    if total != CITED_CAPABILITY_COUNT:
        failures.append(
            f"the requirement sources cite {CITED_CAPABILITY_COUNT} capabilities but the ledger "
            f"enumerates {total}; the citation is what disagrees with the artifact"
        )
    return Result("SUP1", "Cited capability count matches the ledger enumeration", not failures, failures, notes)


def main() -> int:
    """Run all three assertions and print a report.

    Returns:
        0 when every assertion passes, 1 otherwise.
    """
    print(f"audit file : {AUDIT_PATH}")
    print(f"ledger file: {LEDGER_PATH}")
    if not AUDIT_PATH.is_file():
        print(f"FATAL: audit file not found: {AUDIT_PATH}")
        return 1
    if not LEDGER_PATH.is_file():
        print(f"FATAL: ledger file not found: {LEDGER_PATH}")
        return 1

    try:
        rows = parse_matrix(AUDIT_PATH.read_text(encoding="utf-8"))
    except MatrixError as exc:
        print(f"FATAL: {exc}")
        return 1

    try:
        sections = parse_ledger(LEDGER_PATH.read_text(encoding="utf-8"))
    except LedgerError as exc:
        print(f"FATAL: {exc}")
        return 1

    capabilities = [entry for section in sections for entry in section.entries]
    print(f"matrix rows: {len(rows)}")
    print(f"ledger sections: {len(sections)}; capabilities enumerated: {len(capabilities)}")
    print("")

    results = [
        check_dispositions_decided(capabilities, rows),
        check_capability_correspondence(sections, rows),
        check_cited_count(sections),
    ]

    for result in results:
        status = "PASS" if result.passed else "FAIL"
        print(f"[{status}] {result.code} {result.title}")
        for note in result.notes:
            print(f"       note: {note}")
        for failure in result.failures:
            print(f"       FAIL: {failure}")
        print("")

    failed = [result.code for result in results if not result.passed]
    if failed:
        print("RESULT: FAIL (" + ", ".join(failed) + ")")
        return 1
    print("RESULT: PASS (AC1, AC2, SUP1)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

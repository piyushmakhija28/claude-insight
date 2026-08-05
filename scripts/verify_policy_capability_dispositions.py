"""Verify V2-008: every lost capability carries a decided disposition.

Checks ``docs/reports/capability-disposition-ledger.md`` against
``docs/phase-0-reverse-engineering/capability_loss.md`` for the two acceptance
criteria recorded for V2-008 in ``docs/phase-6-sprint/github_issues.json``,
which restate PRD NFR-4 and SRS NFR-10.

WHY THIS GATE NO LONGER READS THE POLICY AUDIT MATRIX. An earlier revision
asserted against ``docs/reports/policy-implementation-audit-v2.md``, joining a
capability to a matrix row through the owner file named in that row's Evidence
cell. That join left 20 of 27 capabilities unaccounted for, and the obvious
repair -- adding matrix rows for them -- is structurally impossible: the
matrix's AC1 asserts row-set identity between its Policy-file column and the
``.md`` basenames in ``docs/policies/``, and a capability such as ``daemon.py``
or ``registry.py`` has no policy file at all, so any row added for it fails that
assertion in both directions. The project owner ruled on 2026-08-02 for a
second, capability-keyed ledger instead. This gate asserts against that ledger.
The two sibling gates that do read the matrix are untouched.

AC1 Every ledger row carries a decided disposition: its Disposition cell is
    non-empty and is not the literal ``disappeared``. NFR-4 forbids
    ``disappeared`` because it is the absence of a decision wearing the shape of
    one. This assertion is EXPECTED TO FAIL while rows whose disposition no
    evidence supports remain deliberately blank, and that failure is the
    mechanism that surfaces them rather than a defect in the artifact. A
    non-empty value encoding "undecided" would satisfy the letter of NFR-4 while
    defeating what it exists to force, so the correct state of an undecided row
    is empty, and the correct outcome of this gate is a failure naming it.
AC2 The capability ledger and the disposition ledger name the same capabilities,
    asserted as an empty symmetric difference in both directions rather than as
    a count. A count check passes whenever two names are simultaneously wrong,
    which is the defect class this project has caught most often. Direction A is
    "``capability_loss.md`` names a capability the disposition ledger has no row
    for" -- under NFR-4 that IS a disappearance, since nothing anywhere carries a
    decision about it. Direction B is "the disposition ledger carries a row for a
    capability ``capability_loss.md`` does not name", which is a fabricated row:
    ``capability_loss.md`` is machine-generated and is the sole authority on what
    was lost.

SUP1 is a supporting integrity check, not one of V2-008's acceptance criteria.
    It compares the capability count CITED by the requirement sources against the
    count this gate enumerates from ``capability_loss.md``. It is exactly the
    count check that two simultaneous name errors defeat, so it cannot substitute
    for AC2 and is reported separately so the two are never confused.
SUP2 is a supporting integrity check, not one of V2-008's acceptance criteria.
    It asserts that every non-empty disposition is drawn from the audit matrix's
    fixed vocabulary. Without it, AC1 forbids only the single literal
    ``disappeared``, so ``TBD``, ``deferred`` or ``pending`` would pass -- which
    is the same trap under a different spelling. It is supporting rather than an
    AC because V2-008's criterion is stated in terms of ``disappeared``
    specifically; the vocabulary constraint comes from V2-005 by way of the
    owner's instruction that both documents use one vocabulary.

THE KEY IS THE CAPABILITY NAME, NOT THE OWNER FILE. Both documents are keyed by
capability, so the join is a direct name comparison and needs no owner-file
resolution. That matters for the two cross-cutting capabilities, which share a
single owner file (``policy_tracking_helper.py``) while being distinct
capabilities: an owner-file join would silently collapse them into one and let a
single disposition discharge both. Owner files are still parsed and reported,
because parsing them validates that every ``capability_loss.md`` section
declares a package root -- a table in a section that declares none is an error
rather than a silent skip, so a new loss section cannot be added without a root
and go unread.

The cited count is READ FROM ``prd-v2.md`` at run time rather than mirrored as a
constant here, and is deliberately not treated as ground truth. This gate
enumerates ``capability_loss.md`` itself and reports what it finds; if the two
disagree, the citation is what is wrong. Do not relax an assertion to agree with
either number.

Reading it rather than hardcoding it matters. This gate previously held
``CITED_CAPABILITY_COUNT = 25`` beside a docstring claiming the value came from
the PRD. When the PRD was corrected to 27, the constant did not follow, and the
gate began asserting that the sources cite 25 -- a statement that had become
false. A mirrored figure is a second place for the same fact to live, and the
copy always rots first. If the citation cannot be found, that is a FAILURE
rather than a fallback: a gate that silently substitutes a default when its
input goes missing reports on a document it never read.

Table parsing primitives and the ``Result`` type are imported from
``verify_policy_audit_matrix`` rather than reimplemented. Two parsers over one
table format drift, and a drifted parser reports on a document the other gates
are not reading.

Exit status is 0 only when all four assertions pass; any failure exits 1. The
script takes no arguments by design, matching its siblings: an overridable input
path would let a caller point the gate at files other than the artifacts it
exists to guard.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

from verify_policy_audit_matrix import Result, is_table_row, split_cells, strip_cell

REPO_ROOT = Path(__file__).resolve().parents[1]
LOSS_PATH = REPO_ROOT / "docs" / "phase-0-reverse-engineering" / "capability_loss.md"
DISPOSITION_PATH = REPO_ROOT / "docs" / "reports" / "capability-disposition-ledger.md"

PRD_PATH = REPO_ROOT / "docs" / "phase-0-requirements" / "prd-v2.md"
CITED_COUNT_PATTERN = re.compile(r"All (\d+) capabilities named in `capability_loss\.md`")
DISAPPEARED = "disappeared"
LOSS_TABLE_WIDTH = 3
DISPOSITION_HEADER = (
    "#",
    "Capability",
    "Owner file",
    "Requirement",
    "Disposition",
    "Basis",
    "Verification",
)
DISPOSITION_VOCABULARY = (
    "keep-as-is",
    "port-to-plugin",
    "port-to-MCP",
    "demote-to-advisory",
    "delete",
)

SECTION_ROOT = re.compile(r"^##\s+.*?\((?P<root>[A-Za-z0-9_][A-Za-z0-9_./-]*(?:/|\.py))\s*,")
OWNER_FILE = re.compile(r"^`?([A-Za-z0-9_][A-Za-z0-9_./-]*\.py)`?")


class LedgerError(Exception):
    """Raised when capability_loss.md cannot be parsed unambiguously."""


class DispositionError(Exception):
    """Raised when the disposition ledger cannot be parsed into one table."""


@dataclass(frozen=True)
class Capability:
    """One data row of a capability_loss.md loss table.

    Attributes:
        line_no: 1-based line number of the row within capability_loss.md.
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
    """One ``## `` section of capability_loss.md that declares a package root.

    Attributes:
        root: Package root as written in the heading's parenthetical.
        heading_line: 1-based line number of the section heading.
        entries: Table data rows in document order.
    """

    root: str
    heading_line: int
    entries: list[Capability]


@dataclass(frozen=True)
class DispositionRow:
    """One data row of the capability disposition ledger.

    Attributes:
        line_no: 1-based line number of the row within the disposition ledger.
        index: Value of the leading ``#`` column, as written.
        capability: Capability column value, the key this gate joins on.
        owner: Owner file column value.
        requirement: Requirement column value.
        disposition: Disposition column value, empty when deliberately undecided.
        basis: Basis column value.
        verification: Verification column value.
    """

    line_no: int
    index: str
    capability: str
    owner: str
    requirement: str
    disposition: str
    basis: str
    verification: str


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


def parse_loss_ledger(text: str) -> list[LedgerSection]:
    """Parse every loss table out of capability_loss.md.

    A section is in the ledger's loss scope when its ``## `` heading declares a
    package root in parentheses. Sections declaring no root are out of scope and
    skipped, but a table appearing inside one is an error: silently skipping it
    would let a new loss section be added without a root and never be read.

    Args:
        text: Full text of capability_loss.md.

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
                root=section_root,
                heading_line=section_line,
                entries=_parse_entries(rows, section_root, section_line),
            )
        )
    if not sections:
        raise LedgerError(f"no section of {LOSS_PATH.name} declares a package root")
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
        if len(cells) != LOSS_TABLE_WIDTH:
            raise LedgerError(f"line {line_no}: expected {LOSS_TABLE_WIDTH} cells, found {len(cells)}")
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


def parse_dispositions(text: str) -> list[DispositionRow]:
    """Locate the single disposition table in the ledger and parse its rows.

    The table is identified by its exact seven-cell header. Finding zero or more
    than one such header is an error: a second table would make every downstream
    correspondence ambiguous, which is the defect class this gate exists to
    catch. Other tables in the document -- the evidence-label key, the open-items
    grouping, the change log -- carry different headers and are skipped.

    Args:
        text: Full text of the disposition ledger.

    Returns:
        The parsed data rows in document order.

    Raises:
        DispositionError: If the header is absent, duplicated, or if a data row
            does not carry exactly seven cells.
    """
    lines = text.split("\n")
    header_indices = [
        i
        for i, line in enumerate(lines)
        if is_table_row(line) and tuple(strip_cell(c) for c in split_cells(line)) == DISPOSITION_HEADER
    ]
    if not header_indices:
        raise DispositionError(
            "disposition table header not found; expected a row of " + " | ".join(DISPOSITION_HEADER)
        )
    if len(header_indices) > 1:
        found = ", ".join(str(i + 1) for i in header_indices)
        raise DispositionError(f"expected exactly one disposition table header, found at lines {found}")

    rows: list[DispositionRow] = []
    start = header_indices[0] + 1
    for offset, line in enumerate(lines[start:], start=start):
        if not is_table_row(line):
            break
        cells = split_cells(line)
        if all(set(c.strip()) <= set("-: ") for c in cells):
            continue
        if len(cells) != len(DISPOSITION_HEADER):
            raise DispositionError(f"line {offset + 1}: expected {len(DISPOSITION_HEADER)} cells, found {len(cells)}")
        rows.append(
            DispositionRow(
                line_no=offset + 1,
                index=strip_cell(cells[0]),
                capability=strip_cell(cells[1]),
                owner=strip_cell(cells[2]),
                requirement=strip_cell(cells[3]),
                disposition=strip_cell(cells[4]),
                basis=cells[5].strip(),
                verification=strip_cell(cells[6]),
            )
        )
    if not rows:
        raise DispositionError("disposition table header found but it carries no data rows")
    return rows


def read_cited_count() -> int | None:
    """Read the capability count the requirement source cites.

    Reads ``prd-v2.md`` at run time rather than mirroring the figure as a
    constant. A mirrored count is a second home for the same fact, and the copy
    rots first -- this gate previously hardcoded 25 and went on asserting it
    after the PRD was corrected to 27.

    Returns:
        The cited integer, or None when the expected row cannot be found. The
        caller treats None as a failure rather than substituting a default.
    """
    if not PRD_PATH.is_file():
        return None
    match = CITED_COUNT_PATTERN.search(PRD_PATH.read_text(encoding="utf-8"))
    return int(match.group(1)) if match else None


def check_dispositions_decided(rows: list[DispositionRow]) -> Result:
    """Assert every ledger row carries a decided disposition (AC1).

    Args:
        rows: Parsed disposition rows.

    Returns:
        Result listing every row whose Disposition cell is empty or reads
        ``disappeared``, with the per-disposition tally as notes.
    """
    failures: list[str] = []
    notes: list[str] = []
    tally: dict[str, int] = {}
    empty = 0

    for row in rows:
        value = row.disposition
        if not value:
            empty += 1
            failures.append(
                f"line {row.line_no} (row {row.index}): Disposition cell is empty -- {row.capability[:60]!r}"
            )
            continue
        if value.lower() == DISAPPEARED:
            failures.append(
                f"line {row.line_no} (row {row.index}): Disposition reads {DISAPPEARED!r}, "
                f"which NFR-4 forbids as the absence of a decision"
            )
            continue
        tally[value] = tally.get(value, 0) + 1

    notes.append(f"rows examined: {len(rows)}; decided: {sum(tally.values())}; empty: {empty}")
    for value in sorted(tally):
        notes.append(f"{value}: {tally[value]}")
    return Result(
        "AC1",
        "Disposition decided for every lost capability",
        not failures,
        failures,
        notes,
    )


def check_capability_correspondence(sections: list[LedgerSection], rows: list[DispositionRow]) -> Result:
    """Assert both documents name the same capabilities, both ways (AC2).

    Four conditions fail this assertion: a capability name repeated inside
    ``capability_loss.md``, a name repeated inside the disposition ledger, a lost
    capability with no disposition row (direction A), and a disposition row for a
    capability ``capability_loss.md`` does not name (direction B). None of them is
    a count comparison.

    Args:
        sections: Parsed capability_loss.md sections.
        rows: Parsed disposition rows.

    Returns:
        Result listing every discrepancy found in either direction.
    """
    failures: list[str] = []
    notes: list[str] = []
    capabilities = [entry for section in sections for entry in section.entries]
    lost_names = [entry.name for entry in capabilities]
    ledger_names = [row.capability for row in rows]
    lost_set = set(lost_names)
    ledger_set = set(ledger_names)
    by_name = {entry.name: entry for entry in capabilities}
    row_by_name = {row.capability: row for row in rows}

    notes.append(
        f"capability_loss.md: {len(lost_set)} distinct of {len(lost_names)} rows; "
        f"disposition ledger: {len(ledger_set)} distinct of {len(ledger_names)} rows"
    )
    notes.append("both directions of the symmetric difference are asserted; no assertion here is a count")

    for name in sorted({n for n in lost_names if lost_names.count(n) > 1}):
        failures.append(f"capability_loss.md names the capability {name[:60]!r} more than once")
    for name in sorted({n for n in ledger_names if ledger_names.count(n) > 1}):
        failures.append(f"the disposition ledger names the capability {name[:60]!r} more than once")
    for name in sorted(lost_set - ledger_set):
        entry = by_name[name]
        failures.append(
            f"direction A -- capability_loss.md line {entry.line_no} names {name[:60]!r} "
            f"({entry.owner_path}) but the disposition ledger has no row for it (NFR-4 disappearance)"
        )
    for name in sorted(ledger_set - lost_set):
        row = row_by_name[name]
        failures.append(
            f"direction B -- disposition ledger line {row.line_no} carries a row for {name[:60]!r}, "
            f"which capability_loss.md does not name"
        )
    return Result(
        "AC2",
        "Lost capabilities and disposition rows correspond",
        not failures,
        failures,
        notes,
    )


def check_cited_count(sections: list[LedgerSection]) -> Result:
    """Assert the cited capability count matches the enumeration (SUP1).

    Supporting check, NOT a V2-008 acceptance criterion. It compares the count
    the requirement sources cite against the count enumerated from
    ``capability_loss.md``, so a failure here is evidence the citation is wrong
    rather than evidence either ledger is. It is a count comparison and
    therefore blind to two simultaneous name errors; AC2 is what covers that
    case.

    Args:
        sections: Parsed capability_loss.md sections.

    Returns:
        Result comparing the cited count against the enumeration.
    """
    failures: list[str] = []
    notes: list[str] = []
    total = 0
    for section in sections:
        notes.append(f"section at line {section.heading_line} ({section.root}): {len(section.entries)} capabilities")
        total += len(section.entries)
    cited = read_cited_count()
    if cited is None:
        notes.append(f"enumerated here: {total}")
        failures.append(
            f"could not read the cited count from {PRD_PATH.name}; expected a row matching "
            f"{CITED_COUNT_PATTERN.pattern!r}. Not defaulting to a constant: a gate that "
            f"substitutes a value when its input is missing reports on a document it never read"
        )
    else:
        notes.append(f"cited by prd-v2.md NFR-4, read at run time: {cited}; enumerated here: {total}")
        if total != cited:
            failures.append(
                f"the requirement source cites {cited} capabilities but capability_loss.md "
                f"enumerates {total}; the citation is what disagrees with the artifact"
            )
    return Result(
        "SUP1",
        "Cited capability count matches the enumeration",
        not failures,
        failures,
        notes,
    )


def check_vocabulary(rows: list[DispositionRow]) -> Result:
    """Assert every decided disposition is in the fixed vocabulary (SUP2).

    Supporting check, NOT a V2-008 acceptance criterion. AC1 forbids only the
    single literal ``disappeared``; without this check ``TBD``, ``deferred`` or
    ``pending`` would satisfy AC1 while encoding the same absence of a decision.
    Empty cells are AC1's business and are skipped here, so the two assertions
    fail independently.

    Args:
        rows: Parsed disposition rows.

    Returns:
        Result listing every non-empty disposition outside the vocabulary.
    """
    failures = [
        f"line {row.line_no} (row {row.index}): Disposition {row.disposition!r} is outside the fixed vocabulary"
        for row in rows
        if row.disposition and row.disposition not in DISPOSITION_VOCABULARY
    ]
    notes = [
        "vocabulary: " + " | ".join(DISPOSITION_VOCABULARY),
        "empty cells are skipped here; AC1 owns them so the two assertions fail independently",
    ]
    return Result(
        "SUP2",
        "Decided dispositions are in the fixed vocabulary",
        not failures,
        failures,
        notes,
    )


def main() -> int:
    """Run all four assertions and print a report.

    Returns:
        0 when every assertion passes, 1 otherwise.
    """
    print(f"loss file  : {LOSS_PATH}")
    print(f"ledger file: {DISPOSITION_PATH}")
    if not LOSS_PATH.is_file():
        print(f"FATAL: loss file not found: {LOSS_PATH}")
        return 1
    if not DISPOSITION_PATH.is_file():
        print(f"FATAL: ledger file not found: {DISPOSITION_PATH}")
        return 1

    try:
        sections = parse_loss_ledger(LOSS_PATH.read_text(encoding="utf-8"))
    except LedgerError as exc:
        print(f"FATAL: {exc}")
        return 1

    try:
        rows = parse_dispositions(DISPOSITION_PATH.read_text(encoding="utf-8"))
    except DispositionError as exc:
        print(f"FATAL: {exc}")
        return 1

    capabilities = [entry for section in sections for entry in section.entries]
    print(f"loss sections: {len(sections)}; capabilities enumerated: {len(capabilities)}")
    print(f"disposition rows: {len(rows)}")
    print("")

    results = [
        check_dispositions_decided(rows),
        check_capability_correspondence(sections, rows),
        check_cited_count(sections),
        check_vocabulary(rows),
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
    print("RESULT: PASS (AC1, AC2, SUP1, SUP2)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

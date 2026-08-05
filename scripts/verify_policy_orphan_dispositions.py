"""Verify V2-007: every genuine policy orphan carries a post-plugin disposition.

Checks ``docs/reports/policy-implementation-audit-v2.md`` against the two
acceptance criteria recorded for V2-007 in
``docs/phase-6-sprint/github_issues.json``:

AC1 Every policy named in ``as-built-prd.md`` section 4.2 -- the genuine-orphan
    list -- carries a non-empty Post-plugin plan cell in the audit matrix. The
    assertion is scoped to those names only. The sibling gate's AC7 asserts the
    same property over all 46 rows plus vocabulary membership; this one exists
    because V2-007's criterion is about the orphan subset specifically, and a
    check that cannot distinguish the subset cannot report on the subset.
AC2 The section 4.2 name list and the matrix agree on names, asserted as an
    empty symmetric difference in both directions rather than as a count of 14.
    A count check passes while two names are simultaneously wrong, which is the
    defect class this project has caught most often. Direction A is "section
    4.2 names a policy no matrix row carries". Direction B is "a matrix row
    that section 4 classifies nowhere": sections 4.1 (mapped, 32) and 4.2
    (orphans, 14) partition the same 46-policy corpus the matrix enumerates, so
    a row named by neither is a row section 4.2 should have named and did not.

SUP1 is a supporting integrity check, not one of V2-007's acceptance criteria.
    Section 4's own headings declare their counts; SUP1 asserts those
    declarations equal what the tables enumerate and sum to the matrix row
    count. It is the reverse question from AC2: AC2 asks whether the matrix
    agrees with the cited list, SUP1 asks whether the cited list agrees with
    itself. SUP1 cannot substitute for AC2 -- it is exactly the count check
    that two simultaneous name errors defeat -- and is reported separately so
    the two are never confused.

The orphan count of 14 is CITED from as-built-prd.md section 4.2 and is
deliberately not re-derived here. An earlier pass in this project reported "46
of 46 policies are orphans"; that figure was false, an artifact of a
knowledge-graph build that was never given SRS.md and so had no requirement
corpus to correlate against. Re-deriving the figure means re-running that
correlation, which this work is scoped out of. If an assertion below fails, the
cited list may itself be wrong: report that, and do not relax the assertion to
agree with it.

Matrix parsing is imported from ``verify_policy_audit_matrix`` rather than
reimplemented. Two parsers over one artifact drift, and a drifted parser
reports on a document the other gate is not reading.

Exit status is 0 only when all three assertions pass; any failure exits 1. The
script takes no arguments by design, matching the sibling gate: an overridable
input path would let a caller point it at files other than the artifacts it
exists to guard.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

from verify_policy_audit_matrix import MatrixError, Result, Row, is_table_row, parse_matrix, split_cells, strip_cell

REPO_ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = REPO_ROOT / "docs" / "reports" / "policy-implementation-audit-v2.md"
PRD_PATH = REPO_ROOT / "docs" / "phase-0-reverse-engineering" / "as-built-prd.md"

MAPPED_SECTION = "4.1"
ORPHAN_SECTION = "4.2"
PRD_TABLE_WIDTH = 3
DECLARED_COUNT = re.compile(r"\((\d+)\s+of\s+(\d+)\)")


class PrdError(Exception):
    """Raised when a section 4.N policy table cannot be parsed unambiguously."""


@dataclass(frozen=True)
class PrdEntry:
    """One data row of an as-built-prd.md section 4.N policy table.

    Attributes:
        line_no: 1-based line number of the row within the PRD document.
        policy: Policy filename, backticks and surrounding space removed.
        status: Status column value.
        note: Third column value -- the SRS mapping in 4.1, the reason it maps
            to NONE in 4.2.
    """

    line_no: int
    policy: str
    status: str
    note: str


@dataclass(frozen=True)
class PrdSection:
    """One parsed ``### 4.N`` section of the as-built PRD.

    Attributes:
        number: Section number as written, such as ``4.2``.
        heading_line: 1-based line number of the section heading.
        declared_count: First number of the heading's ``(<n> of <n>)`` claim.
        declared_total: Second number of that claim -- the corpus size.
        entries: Table data rows in document order.
    """

    number: str
    heading_line: int
    declared_count: int
    declared_total: int
    entries: list[PrdEntry]


def parse_prd_section(text: str, number: str) -> PrdSection:
    """Parse one ``### 4.N`` policy table out of the as-built PRD.

    The section is identified by its heading, which must appear exactly once
    and must declare a ``(<n> of <n>)`` count. Only the first contiguous table
    block inside the section is read; a second table in the same section is an
    error, because which of the two carries the name list would then be a
    guess.

    Args:
        text: Full text of the as-built PRD.
        number: Section number to parse, such as ``4.2``.

    Returns:
        The parsed section.

    Raises:
        PrdError: If the heading is absent, duplicated, or declares no count;
            if the section carries no table, more than one table, a row of the
            wrong width, or no header row; or if the table has no data rows.
    """
    lines = text.split("\n")
    pattern = re.compile(r"^###\s+" + re.escape(number) + r"(?![0-9.])")
    headings = [i for i, line in enumerate(lines) if pattern.match(line)]
    if not headings:
        raise PrdError(f"section {number} heading not found in {PRD_PATH.name}")
    if len(headings) > 1:
        found = ", ".join(str(i + 1) for i in headings)
        raise PrdError(f"expected exactly one section {number} heading, found at lines {found}")

    start = headings[0]
    declared = DECLARED_COUNT.search(lines[start])
    if not declared:
        raise PrdError(f"line {start + 1}: section {number} heading declares no '(<n> of <n>)' count")
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("#")), len(lines))

    block: list[tuple[int, list[str]]] = []
    started = False
    closed = False
    for offset, line in enumerate(lines[start + 1 : end], start=start + 2):
        if is_table_row(line):
            if closed:
                raise PrdError(f"line {offset}: section {number} carries a second table; expected exactly one")
            started = True
            block.append((offset, split_cells(line)))
        elif started:
            closed = True
    if not block:
        raise PrdError(f"section {number} carries no table")

    entries: list[PrdEntry] = []
    saw_header = False
    for line_no, cells in block:
        if all(set(cell.strip()) <= set("-: ") for cell in cells):
            continue
        if len(cells) != PRD_TABLE_WIDTH:
            raise PrdError(f"line {line_no}: expected {PRD_TABLE_WIDTH} cells, found {len(cells)}")
        policy = strip_cell(cells[0])
        if not saw_header:
            if policy.lower() != "policy":
                raise PrdError(f"line {line_no}: section {number} table does not open with a 'Policy' header row")
            saw_header = True
            continue
        entries.append(PrdEntry(line_no=line_no, policy=policy, status=strip_cell(cells[1]), note=strip_cell(cells[2])))
    if not entries:
        raise PrdError(f"section {number} table carries no data rows")

    return PrdSection(
        number=number,
        heading_line=start + 1,
        declared_count=int(declared.group(1)),
        declared_total=int(declared.group(2)),
        entries=entries,
    )


def check_orphan_dispositions(orphans: PrdSection, rows: list[Row]) -> Result:
    """Assert every section 4.2 orphan carries a non-empty disposition (AC1).

    Scoped deliberately to the names section 4.2 supplies. A name with no
    matrix row is recorded as not evaluable rather than as a failure here:
    AC2 owns that condition, and folding it in would leave two assertions
    unable to fail independently, which is how a check becomes untestable.

    Args:
        orphans: Parsed section 4.2.
        rows: Parsed matrix rows.

    Returns:
        Result listing every orphan row whose Post-plugin plan cell is empty,
        with the per-disposition tally and the not-evaluable set as notes.
    """
    by_name = {row.policy: row for row in rows}
    failures: list[str] = []
    notes: list[str] = []
    tally: dict[str, int] = {}
    unmatched: list[str] = []
    evaluated = 0

    for entry in orphans.entries:
        row = by_name.get(entry.policy)
        if row is None:
            unmatched.append(entry.policy)
            continue
        evaluated += 1
        plan = row.plan.strip()
        if not plan:
            failures.append(
                f"line {row.line_no} ({row.policy}): Post-plugin plan cell is empty; "
                f"section {ORPHAN_SECTION} line {entry.line_no} names it a genuine orphan"
            )
            continue
        tally[plan] = tally.get(plan, 0) + 1

    notes.append(
        f"names in section {ORPHAN_SECTION}: {len(orphans.entries)}; "
        f"matrix rows found for them: {evaluated}; empty dispositions: {len(failures)}"
    )
    for value in sorted(tally):
        notes.append(f"{value}: {tally[value]}")
    if unmatched:
        notes.append(
            "not evaluable -- no matrix row carries these names, AC2 asserts on that: " + ", ".join(sorted(unmatched))
        )
    return Result("AC1", "Post-plugin plan populated for every genuine orphan", not failures, failures, notes)


def check_name_correspondence(mapped: PrdSection, orphans: PrdSection, rows: list[Row]) -> Result:
    """Assert section 4.2 and the matrix agree on names, both ways (AC2).

    Four conditions fail this assertion: a name repeated within either section,
    a name claimed by both sections at once, a section 4.2 name no matrix row
    carries (direction A), and a matrix row neither section names (direction
    B). None of them is a count comparison.

    Args:
        mapped: Parsed section 4.1.
        orphans: Parsed section 4.2.
        rows: Parsed matrix rows.

    Returns:
        Result listing every name discrepancy found in either direction.
    """
    failures: list[str] = []
    notes: list[str] = []
    orphan_names = [entry.policy for entry in orphans.entries]
    mapped_names = [entry.policy for entry in mapped.entries]
    orphan_set = set(orphan_names)
    mapped_set = set(mapped_names)
    matrix_set = {row.policy for row in rows}

    notes.append(
        f"section {ORPHAN_SECTION}: {len(orphan_set)} distinct of {len(orphan_names)} rows; "
        f"section {MAPPED_SECTION}: {len(mapped_set)} distinct of {len(mapped_names)} rows; "
        f"matrix: {len(matrix_set)} distinct of {len(rows)} rows"
    )
    notes.append("both directions of the symmetric difference are asserted; no assertion here is a count")

    for number, names in ((ORPHAN_SECTION, orphan_names), (MAPPED_SECTION, mapped_names)):
        for name in sorted({n for n in names if names.count(n) > 1}):
            failures.append(f"section {number} names {name} more than once")
    for name in sorted(orphan_set & mapped_set):
        failures.append(
            f"{name} is named by both section {MAPPED_SECTION} (mapped) and section {ORPHAN_SECTION} (orphan)"
        )
    for name in sorted(orphan_set - matrix_set):
        failures.append(f"direction A -- section {ORPHAN_SECTION} names {name} but no matrix row carries it")
    for name in sorted(matrix_set - (orphan_set | mapped_set)):
        failures.append(
            f"direction B -- matrix row {name} is classified by neither section {MAPPED_SECTION} nor "
            f"section {ORPHAN_SECTION}; if it is an orphan, section {ORPHAN_SECTION} does not name it"
        )
    return Result("AC2", "Section 4.2 names and matrix rows correspond", not failures, failures, notes)


def check_declared_counts(mapped: PrdSection, orphans: PrdSection, rows: list[Row]) -> Result:
    """Assert section 4's declared counts match its own tables (SUP1).

    Supporting check, not a V2-007 acceptance criterion. It compares the cited
    list against itself and against the corpus size, so a failure here is
    evidence the citation is internally wrong rather than evidence the matrix
    is. It is a count comparison and therefore blind to two simultaneous name
    errors; AC2 is what covers that case.

    Args:
        mapped: Parsed section 4.1.
        orphans: Parsed section 4.2.
        rows: Parsed matrix rows.

    Returns:
        Result listing every declaration that disagrees with an enumeration.
    """
    failures: list[str] = []
    notes: list[str] = []
    for section in (mapped, orphans):
        notes.append(
            f"section {section.number} (line {section.heading_line}): declares "
            f"{section.declared_count} of {section.declared_total}, enumerates {len(section.entries)}"
        )
        if section.declared_count != len(section.entries):
            failures.append(
                f"line {section.heading_line}: section {section.number} declares "
                f"{section.declared_count} policies but its table enumerates {len(section.entries)}"
            )
        if section.declared_total != len(rows):
            failures.append(
                f"line {section.heading_line}: section {section.number} declares a corpus of "
                f"{section.declared_total} but the matrix carries {len(rows)} rows"
            )
    combined = mapped.declared_count + orphans.declared_count
    notes.append(f"declared {MAPPED_SECTION} + {ORPHAN_SECTION} = {combined}; matrix rows = {len(rows)}")
    if combined != len(rows):
        failures.append(
            f"sections {MAPPED_SECTION} and {ORPHAN_SECTION} declare {combined} policies between them "
            f"but the matrix carries {len(rows)} rows"
        )
    return Result("SUP1", "Section 4 declared counts match its own tables", not failures, failures, notes)


def main() -> int:
    """Run all three assertions and print a report.

    Returns:
        0 when every assertion passes, 1 otherwise.
    """
    print(f"audit file : {AUDIT_PATH}")
    print(f"prd file   : {PRD_PATH}")
    if not AUDIT_PATH.is_file():
        print(f"FATAL: audit file not found: {AUDIT_PATH}")
        return 1
    if not PRD_PATH.is_file():
        print(f"FATAL: prd file not found: {PRD_PATH}")
        return 1

    try:
        rows = parse_matrix(AUDIT_PATH.read_text(encoding="utf-8"))
    except MatrixError as exc:
        print(f"FATAL: {exc}")
        return 1

    prd_text = PRD_PATH.read_text(encoding="utf-8")
    try:
        mapped = parse_prd_section(prd_text, MAPPED_SECTION)
        orphans = parse_prd_section(prd_text, ORPHAN_SECTION)
    except PrdError as exc:
        print(f"FATAL: {exc}")
        return 1

    print(f"matrix rows: {len(rows)}")
    print(f"section {MAPPED_SECTION}: {len(mapped.entries)} rows (heading declares {mapped.declared_count})")
    print(f"section {ORPHAN_SECTION}: {len(orphans.entries)} rows (heading declares {orphans.declared_count})")
    print("")

    results = [
        check_orphan_dispositions(orphans, rows),
        check_name_correspondence(mapped, orphans, rows),
        check_declared_counts(mapped, orphans, rows),
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

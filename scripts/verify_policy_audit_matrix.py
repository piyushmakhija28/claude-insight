"""Verify the Deliverable-1 policy audit matrix against V2-004 acceptance criteria.

Checks ``docs/reports/policy-implementation-audit-v2.md`` against the six
re-scoped acceptance criteria recorded for issue V2-004 in
``docs/phase-6-sprint/github_issues.json``:

AC1 Row-set identity -- the set of Policy-file cells in the matrix equals the set
    of ``.md`` basenames in ``docs/policies/``, tested as an empty symmetric
    difference in both directions rather than as a row count. ``docs/policies/``
    is the authoritative corpus per ADR-009; ``get_policies_dir()`` resolves at
    runtime to a partial mirror and is deliberately not consulted here.
AC2 Every row carries a Verification label drawn from the closed set
    MEASURED | CITED | INFERRED, with no blank cell.
AC3 Every MEASURED row carries at least one ``path:line`` reference in Evidence
    that resolves: the path exists under the repository root and the file holds
    at least that many lines. AC3 requires one resolving reference, not all of
    them, so shorthand references that do not resolve are reported as advisory
    notes and do not fail the assertion.
AC4 Every CITED row names at least one source artifact that exists on disk.
    Rows whose Evidence is an explicit NONE are exempt: AC5 governs those rows,
    and a row asserting that no artifact exists cannot also name one. Applying
    AC4 to them would make AC4 and AC5 mutually unsatisfiable.
AC5 NONE is explicit and never blank -- no Evidence cell is empty, a row naming
    no artifact at all carries the literal NONE, and no NONE row is labelled
    MEASURED.
AC6 The reported MEASURED/CITED/INFERRED split equals the split recomputed from
    the rows. AC6 asserts on the label's presence and correctness, never on its
    value, so no minimum MEASURED count is imposed.

Exit status is 0 only when all six assertions pass; any failure exits 1. The
script takes no arguments by design: an overridable input path would let a
caller point the gate at a file other than the artifact it exists to guard.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = REPO_ROOT / "docs" / "reports" / "policy-implementation-audit-v2.md"
POLICY_DIR = REPO_ROOT / "docs" / "policies"

MATRIX_HEADER = (
    "#",
    "Policy file",
    "Status",
    "Evidence",
    "Post-plugin plan",
    "Basis",
    "Verification",
)
VERIFICATION_LABELS = ("MEASURED", "CITED", "INFERRED")

_EXT = r"(?:py|md|json|txt|ya?ml|toml|ini|cfg|ts|tsx|js|java|kt|sh|bat)"
PATH_TOKEN = re.compile(r"[A-Za-z0-9_./-]+\." + _EXT)
PATH_LINE_TOKEN = re.compile(r"([A-Za-z0-9_./-]+\." + _EXT + r"):(\d+)(?:-(\d+))?")
NONE_TOKEN = re.compile(r"\bNONE\b")
SPLIT_DECLARATION = re.compile(r"(\d+)\s+MEASURED,\s*(\d+)\s+CITED,\s*(\d+)\s+INFERRED")


@dataclass(frozen=True)
class Row:
    """One data row of the policy implementation matrix.

    Attributes:
        line_no: 1-based line number of the row within the audit document.
        index: Value of the leading ``#`` column, as written.
        policy: Policy filename, backticks and surrounding space removed.
        status: Status column value.
        evidence: Evidence column value, verbatim apart from outer whitespace.
        plan: Post-plugin plan column value.
        basis: Basis column value.
        verification: Verification column value.
    """

    line_no: int
    index: str
    policy: str
    status: str
    evidence: str
    plan: str
    basis: str
    verification: str


@dataclass
class Result:
    """Outcome of one acceptance-criterion assertion.

    Attributes:
        code: Short identifier such as ``AC1``.
        title: Human-readable name of the assertion.
        passed: True when the assertion holds.
        failures: Lines describing each violation found.
        notes: Advisory lines that do not affect ``passed``.
    """

    code: str
    title: str
    passed: bool
    failures: list[str]
    notes: list[str]


class MatrixError(Exception):
    """Raised when the audit document cannot be parsed into exactly one matrix."""


def strip_cell(raw: str) -> str:
    """Normalise a raw pipe-delimited table cell.

    Args:
        raw: Cell text exactly as split from the row.

    Returns:
        The cell with outer whitespace stripped, outer backticks removed, and
        whitespace stripped again.
    """
    return raw.strip().strip("`").strip()


def is_table_row(line: str) -> bool:
    """Report whether a line is a pipe-delimited markdown table row.

    Args:
        line: A single line of the document.

    Returns:
        True when the stripped line both starts and ends with a pipe.
    """
    stripped = line.strip()
    return stripped.startswith("|") and stripped.endswith("|") and len(stripped) > 1


def split_cells(line: str) -> list[str]:
    """Split a markdown table row into its cells.

    Args:
        line: A line for which :func:`is_table_row` is True.

    Returns:
        The cell texts between the outer pipes, unnormalised.
    """
    return line.strip()[1:-1].split("|")


def parse_matrix(text: str) -> list[Row]:
    """Locate the single policy matrix in the document and parse its data rows.

    The matrix is identified by its exact seven-cell header. Finding zero or
    more than one such header is an error: a second matrix would make every
    downstream count ambiguous, which is the defect class this gate exists to
    catch.

    Args:
        text: Full text of the audit document.

    Returns:
        The parsed data rows in document order.

    Raises:
        MatrixError: If the header is absent, duplicated, or if a data row does
            not carry exactly seven cells.
    """
    lines = text.split("\n")
    header_indices = [
        i
        for i, line in enumerate(lines)
        if is_table_row(line) and tuple(strip_cell(c) for c in split_cells(line)) == MATRIX_HEADER
    ]
    if not header_indices:
        raise MatrixError("matrix header not found; expected a row of " + " | ".join(MATRIX_HEADER))
    if len(header_indices) > 1:
        found = ", ".join(str(i + 1) for i in header_indices)
        raise MatrixError(f"expected exactly one matrix header, found at lines {found}")

    rows: list[Row] = []
    start = header_indices[0] + 1
    for offset, line in enumerate(lines[start:], start=start):
        if not is_table_row(line):
            break
        cells = split_cells(line)
        if all(set(c.strip()) <= set("-: ") for c in cells):
            continue
        if len(cells) != len(MATRIX_HEADER):
            raise MatrixError(f"line {offset + 1}: expected {len(MATRIX_HEADER)} cells, " f"found {len(cells)}")
        rows.append(
            Row(
                line_no=offset + 1,
                index=strip_cell(cells[0]),
                policy=strip_cell(cells[1]),
                status=strip_cell(cells[2]),
                evidence=cells[3].strip(),
                plan=strip_cell(cells[4]),
                basis=strip_cell(cells[5]),
                verification=strip_cell(cells[6]),
            )
        )
    if not rows:
        raise MatrixError("matrix header found but it carries no data rows")
    return rows


def count_lines(path: Path) -> int:
    """Count the lines held by a file.

    Args:
        path: File to measure.

    Returns:
        Number of lines, counting a final unterminated line.
    """
    return len(path.read_text(encoding="utf-8", errors="replace").splitlines())


def path_line_references(evidence: str) -> list[tuple[str, int]]:
    """Extract every ``path:line`` reference from an Evidence cell.

    A range such as ``file.py:38-133`` yields the higher bound, because the
    assertion "the file has at least that many lines" is only satisfied by the
    end of the cited range.

    Args:
        evidence: Evidence cell text.

    Returns:
        Pairs of (path, required line count), in order of appearance.
    """
    refs: list[tuple[str, int]] = []
    for match in PATH_LINE_TOKEN.finditer(evidence):
        path = match.group(1)
        start = int(match.group(2))
        end = int(match.group(3)) if match.group(3) else start
        refs.append((path, max(start, end)))
    return refs


def named_paths(evidence: str) -> list[str]:
    """Extract every artifact path named in an Evidence cell.

    Args:
        evidence: Evidence cell text.

    Returns:
        Path-like tokens, in order of appearance, without line suffixes.
    """
    return PATH_TOKEN.findall(evidence)


def resolves(path: str, required_lines: int = 0) -> bool:
    """Report whether a cited path exists and is long enough.

    Args:
        path: Repository-relative path as written in the Evidence cell.
        required_lines: Minimum line count the file must hold.

    Returns:
        True when the path resolves to an existing file under the repository
        root that holds at least ``required_lines`` lines.
    """
    target = REPO_ROOT / path
    if not target.is_file():
        return False
    if required_lines and count_lines(target) < required_lines:
        return False
    return True


def is_none_row(row: Row) -> bool:
    """Report whether a row declares an explicit absence of code grounding.

    Args:
        row: Matrix row under test.

    Returns:
        True when the Evidence cell contains the literal token NONE.
    """
    return bool(NONE_TOKEN.search(row.evidence))


def check_row_set_identity(rows: list[Row]) -> Result:
    """Assert the matrix row set equals the docs/policies corpus (AC1).

    Args:
        rows: Parsed matrix rows.

    Returns:
        Result carrying both directions of the symmetric difference.
    """
    failures: list[str] = []
    notes: list[str] = []
    if not POLICY_DIR.is_dir():
        failures.append(f"corpus directory missing: {POLICY_DIR}")
        return Result("AC1", "Row-set identity", False, failures, notes)

    corpus = {p.name for p in sorted(POLICY_DIR.glob("*.md"))}
    matrix = {row.policy for row in rows}
    notes.append(
        f"corpus files (docs/policies/*.md, non-recursive): {len(corpus)}; "
        f"matrix rows: {len(rows)}; distinct policy cells: {len(matrix)}"
    )
    if len(matrix) != len(rows):
        duplicates = sorted({r.policy for r in rows if [x.policy for x in rows].count(r.policy) > 1})
        failures.append("duplicate policy cells: " + ", ".join(duplicates))
    for name in sorted(corpus - matrix):
        failures.append(f"in corpus but missing from matrix: {name}")
    for name in sorted(matrix - corpus):
        failures.append(f"in matrix but absent from corpus: {name}")
    return Result("AC1", "Row-set identity", not failures, failures, notes)


def check_verification_labels(rows: list[Row]) -> Result:
    """Assert every row carries a label from the closed vocabulary (AC2).

    Args:
        rows: Parsed matrix rows.

    Returns:
        Result listing every blank or out-of-vocabulary label.
    """
    failures = [
        f"line {row.line_no} ({row.policy}): Verification is "
        + (f"{row.verification!r}" if row.verification else "empty")
        for row in rows
        if row.verification not in VERIFICATION_LABELS
    ]
    notes = [f"vocabulary: {' | '.join(VERIFICATION_LABELS)}"]
    return Result("AC2", "Verification label present and in vocabulary", not failures, failures, notes)


def check_measured_resolve(rows: list[Row]) -> Result:
    """Assert every MEASURED row cites a resolving path:line reference (AC3).

    Args:
        rows: Parsed matrix rows.

    Returns:
        Result listing MEASURED rows with no reference or no resolving
        reference, plus advisory notes for individual references that do not
        resolve while a sibling reference does.
    """
    failures: list[str] = []
    notes: list[str] = []
    measured = [row for row in rows if row.verification == "MEASURED"]
    notes.append(f"MEASURED rows examined: {len(measured)}")
    for row in measured:
        refs = path_line_references(row.evidence)
        if not refs:
            failures.append(
                f"line {row.line_no} ({row.policy}): MEASURED but Evidence " "carries no path:line reference"
            )
            continue
        good = [(p, n) for p, n in refs if resolves(p, n)]
        bad = [(p, n) for p, n in refs if (p, n) not in good]
        if not good:
            detail = "; ".join(f"{p}:{n}" for p, n in refs)
            failures.append(f"line {row.line_no} ({row.policy}): no path:line reference " f"resolves ({detail})")
        for path, need in bad:
            target = REPO_ROOT / path
            reason = (
                "path does not exist" if not target.is_file() else f"file has {count_lines(target)} lines, needs {need}"
            )
            notes.append(f"advisory line {row.line_no} ({row.policy}): {path}:{need} " f"unresolved -- {reason}")
    return Result("AC3", "MEASURED rows resolve to path:line", not failures, failures, notes)


def check_cited_attribution(rows: list[Row]) -> Result:
    """Assert every non-NONE CITED row names an artifact that exists (AC4).

    Args:
        rows: Parsed matrix rows.

    Returns:
        Result listing CITED rows that name no artifact or name only artifacts
        absent from disk, with NONE rows recorded as exempt.
    """
    failures: list[str] = []
    notes: list[str] = []
    cited = [row for row in rows if row.verification == "CITED"]
    exempt = [row for row in cited if is_none_row(row)]
    subject = [row for row in cited if not is_none_row(row)]
    notes.append(
        f"CITED rows: {len(cited)}; explicit-NONE rows exempt under AC5: "
        f"{len(exempt)}; rows asserted against: {len(subject)}"
    )
    for row in subject:
        paths = named_paths(row.evidence)
        if not paths:
            failures.append(f"line {row.line_no} ({row.policy}): CITED but names no source " "artifact")
            continue
        if not any(resolves(path) for path in paths):
            failures.append(
                f"line {row.line_no} ({row.policy}): no named artifact exists " "on disk (" + "; ".join(paths) + ")"
            )
    return Result("AC4", "CITED rows attribute to an existing artifact", not failures, failures, notes)


def check_none_explicit(rows: list[Row]) -> Result:
    """Assert NONE is explicit, never blank, and never MEASURED (AC5).

    Args:
        rows: Parsed matrix rows.

    Returns:
        Result listing blank Evidence cells, ungrounded rows that omit the
        literal NONE, and NONE rows labelled MEASURED.
    """
    failures: list[str] = []
    notes: list[str] = []
    none_rows = [row for row in rows if is_none_row(row)]
    notes.append(f"rows carrying an explicit NONE: {len(none_rows)}")
    for row in rows:
        if not row.evidence.strip():
            failures.append(f"line {row.line_no} ({row.policy}): Evidence cell is blank")
            continue
        if not named_paths(row.evidence) and not is_none_row(row):
            failures.append(
                f"line {row.line_no} ({row.policy}): Evidence names no artifact " "and does not carry the literal NONE"
            )
        if is_none_row(row) and row.verification == "MEASURED":
            failures.append(f"line {row.line_no} ({row.policy}): explicit-NONE row is " "labelled MEASURED")
    return Result("AC5", "NONE is explicit, never blank, never MEASURED", not failures, failures, notes)


def check_reported_split(text: str, rows: list[Row]) -> Result:
    """Assert the reported verification split equals the recomputed split (AC6).

    Args:
        text: Full text of the audit document.
        rows: Parsed matrix rows.

    Returns:
        Result comparing every declared split against the row-derived split.
    """
    failures: list[str] = []
    notes: list[str] = []
    actual = {label: sum(1 for row in rows if row.verification == label) for label in VERIFICATION_LABELS}
    notes.append("recomputed from rows: " + ", ".join(f"{actual[label]} {label}" for label in VERIFICATION_LABELS))

    declarations: list[tuple[int, tuple[int, int, int]]] = []
    for line_no, line in enumerate(text.split("\n"), start=1):
        match = SPLIT_DECLARATION.search(line)
        if match:
            declarations.append((line_no, (int(match.group(1)), int(match.group(2)), int(match.group(3)))))
    if not declarations:
        failures.append(
            "no reported split found; expected a declaration matching " "'<n> MEASURED, <n> CITED, <n> INFERRED'"
        )
        return Result("AC6", "Reported split equals recomputed split", False, failures, notes)

    expected = (actual["MEASURED"], actual["CITED"], actual["INFERRED"])
    for line_no, declared in declarations:
        notes.append(
            f"declaration at line {line_no}: " f"{declared[0]} MEASURED, {declared[1]} CITED, {declared[2]} INFERRED"
        )
        if declared != expected:
            failures.append(f"line {line_no}: reported split {declared} does not equal " f"recomputed split {expected}")
    if sum(expected) != len(rows):
        failures.append(f"recomputed split sums to {sum(expected)} but the matrix has " f"{len(rows)} rows")
    return Result("AC6", "Reported split equals recomputed split", not failures, failures, notes)


def main() -> int:
    """Run all six assertions and print a report.

    Returns:
        0 when every assertion passes, 1 otherwise.
    """
    print(f"audit file : {AUDIT_PATH}")
    print(f"corpus dir : {POLICY_DIR}")
    if not AUDIT_PATH.is_file():
        print(f"FATAL: audit file not found: {AUDIT_PATH}")
        return 1

    text = AUDIT_PATH.read_text(encoding="utf-8")
    try:
        rows = parse_matrix(text)
    except MatrixError as exc:
        print(f"FATAL: {exc}")
        return 1

    print(f"data rows  : {len(rows)}")
    print("")

    results = [
        check_row_set_identity(rows),
        check_verification_labels(rows),
        check_measured_resolve(rows),
        check_cited_attribution(rows),
        check_none_explicit(rows),
        check_reported_split(text, rows),
    ]

    for result in results:
        status = "PASS" if result.passed else "FAIL"
        print(f"[{status}] {result.code} {result.title}")
        for note in result.notes:
            print(f"       note: {note}")
        for failure in result.failures:
            print(f"       FAIL: {failure}")
        print("")

    failed = [r.code for r in results if not r.passed]
    if failed:
        print("RESULT: FAIL (" + ", ".join(failed) + ")")
        return 1
    print("RESULT: PASS (AC1-AC6)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

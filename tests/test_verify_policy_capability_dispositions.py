"""Negative tests for ``scripts/verify_policy_capability_dispositions.py``.

Every assertion the gate makes is exercised here in a state where it must fail,
and every assertion that must NOT fire on an unrelated defect is exercised in a
state where it must still pass. A check never observed failing is
indistinguishable from a no-op, and a check that fails on everything is
indistinguishable from a check that reads its inputs.

The gate FAILS against the current tree, on AC1 and SUP1, and that is the
finding rather than a broken check: 8 of the 27 capabilities carry a
deliberately empty disposition because no evidence on disk supports one, and the
requirement sources cite 25 capabilities where ``capability_loss.md`` enumerates
27. ``test_gate_reports_the_current_tree_exactly`` pins that state so a later
change to either artifact cannot move it silently. A concurrent correction of
the cited 25 to 27 is in flight in other documents; when it lands, SUP1 flips to
PASS and this pin must be updated and be seen being updated.

Three assertions carry an explicit SPECIFICITY CONTROL, because each has a
plausible over-broad implementation that would pass every negative test above
while reporting on the wrong thing: an AC1 that fired on any empty table cell
anywhere in the document, an AC2 that fired on any edit to a row, and a SUP2
that fired on the empty cells AC1 already owns.

The gate is always executed from its stored form via ``subprocess``, never
imported and never re-implemented, so what these tests exercise is what a caller
runs.

Mutations are applied to a byte-identical sandbox copy of the source documents
rather than to the repository's own copies. Both artifacts are under concurrent
edit by other work, and a test that mutates and restores a file another writer is
holding can silently discard that writer's change even when the restore is
byte-exact. Each sandbox is verified against the stored originals by SHA-256
before use.
"""

from __future__ import annotations

import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_REL = Path("scripts") / "verify_policy_capability_dispositions.py"
IMPORTED_REL = Path("scripts") / "verify_policy_audit_matrix.py"
LOSS_REL = Path("docs") / "phase-0-reverse-engineering" / "capability_loss.md"
LEDGER_REL = Path("docs") / "reports" / "capability-disposition-ledger.md"
PRD_REL = Path("docs") / "phase-0-requirements" / "prd-v2.md"
SANDBOX_FILES = (SCRIPT_REL, IMPORTED_REL, LOSS_REL, LEDGER_REL, PRD_REL)

LOSS_WIDTH = 3
LEDGER_WIDTH = 7
DISPOSITION_COLUMN = 4
CAPABILITY_COLUMN = 1

DECIDED_ROW = "9"
DECIDED_CAPABILITY = "Grep content-mode head_limit enforcement"
UNDECIDED_ROW = "2"
UNDECIDED_CAPABILITY = "Skill/agent-selection-pending block"
SPARE_OWNERS = ("daemon.py", "registry.py")
SPARE_CAPABILITIES = ("Warm-daemon fast path", "PolicyRegistry")
OPEN_ITEMS_HEADING = "## 2. What is still open"

BASELINE_CAPABILITIES = 27
BASELINE_EMPTY = 8
BASELINE_DECIDED = 19
BASELINE_CITED = 27


def digest(path: Path) -> str:
    """Compute the SHA-256 of a file.

    Args:
        path: File to hash.

    Returns:
        Lowercase hexadecimal digest of the file's bytes.
    """
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture()
def sandbox(tmp_path: Path) -> Path:
    """Build a byte-identical copy of the gate and the documents it reads.

    Args:
        tmp_path: Per-test temporary directory supplied by pytest.

    Returns:
        Root of the sandbox, laid out so the copied gate resolves its own
        repository root to the sandbox rather than to the real repository.
    """
    for relative in SANDBOX_FILES:
        source = REPO_ROOT / relative
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        assert digest(target) == digest(source), f"sandbox copy of {relative} is not byte-identical"
    return tmp_path


def run_gate(root: Path) -> tuple[int, str]:
    """Execute the stored gate inside a sandbox and capture its report.

    Args:
        root: Sandbox root produced by the ``sandbox`` fixture.

    Returns:
        Pair of (exit status, combined stdout and stderr).
    """
    completed = subprocess.run(
        [sys.executable, str(root / SCRIPT_REL)],
        capture_output=True,
        text=True,
        check=False,
    )
    return completed.returncode, completed.stdout + completed.stderr


def table_row_index(lines: list[str], width: int, column: int, value: str) -> int:
    """Find a markdown table row of a given width by one cell's value.

    Args:
        lines: Document split into lines.
        width: Exact cell count the row must carry.
        column: Zero-based cell index to match on.
        value: Expected cell value after stripping space and backticks.

    Returns:
        Index of the matching row within ``lines``.

    Raises:
        AssertionError: If no row of that width carries that cell value.
    """
    for index, line in enumerate(lines):
        stripped = line.strip()
        if not (stripped.startswith("|") and stripped.endswith("|")):
            continue
        cells = stripped[1:-1].split("|")
        if len(cells) == width and cells[column].strip().strip("`").strip() == value:
            return index
    raise AssertionError(f"no {width}-cell row carries {value!r} in column {column}")


def rewrite_ledger_cell(path: Path, row_index: str, column: int, value: str) -> None:
    """Replace one cell of one disposition-ledger row in place.

    Args:
        path: Sandbox copy of the disposition ledger.
        row_index: Value of the row's leading ``#`` column.
        column: Zero-based cell index within the row.
        value: Replacement cell text, written with single-space padding.
    """
    lines = path.read_text(encoding="utf-8").split("\n")
    index = table_row_index(lines, LEDGER_WIDTH, 0, row_index)
    cells = lines[index].strip()[1:-1].split("|")
    cells[column] = f" {value} " if value else "  "
    lines[index] = "|" + "|".join(cells) + "|"
    path.write_text("\n".join(lines), encoding="utf-8")


def drop_ledger_row(path: Path, row_index: str) -> None:
    """Remove one row from the disposition ledger.

    Args:
        path: Sandbox copy of the disposition ledger.
        row_index: Value of the row's leading ``#`` column.
    """
    lines = path.read_text(encoding="utf-8").split("\n")
    del lines[table_row_index(lines, LEDGER_WIDTH, 0, row_index)]
    path.write_text("\n".join(lines), encoding="utf-8")


def append_ledger_row(path: Path, capability: str, disposition: str) -> None:
    """Append a fabricated row to the disposition ledger.

    Args:
        path: Sandbox copy of the disposition ledger.
        capability: Capability cell text for the new row.
        disposition: Disposition cell text for the new row.
    """
    lines = path.read_text(encoding="utf-8").split("\n")
    index = table_row_index(lines, LEDGER_WIDTH, 0, "27")
    row = f"| 28 | {capability} | `fabricated.py` | FR-9 | {disposition} | fabricated basis | CITED |"
    lines.insert(index + 1, row)
    path.write_text("\n".join(lines), encoding="utf-8")


def duplicate_ledger_row(path: Path, row_index: str) -> None:
    """Copy one disposition row so the ledger names its capability twice.

    Args:
        path: Sandbox copy of the disposition ledger.
        row_index: Value of the row's leading ``#`` column.
    """
    lines = path.read_text(encoding="utf-8").split("\n")
    index = table_row_index(lines, LEDGER_WIDTH, 0, row_index)
    lines.insert(index + 1, lines[index])
    path.write_text("\n".join(lines), encoding="utf-8")


def duplicate_ledger_header(path: Path) -> None:
    """Insert a second copy of the seven-cell disposition table header.

    Args:
        path: Sandbox copy of the disposition ledger.
    """
    lines = path.read_text(encoding="utf-8").split("\n")
    index = table_row_index(lines, LEDGER_WIDTH, 0, "#")
    lines.append("")
    lines.append(lines[index])
    lines.append("|---|---|---|---|---|---|---|")
    path.write_text("\n".join(lines), encoding="utf-8")


def add_empty_open_items_row(path: Path) -> None:
    """Append a row of empty cells to the ledger's open-items table.

    Args:
        path: Sandbox copy of the disposition ledger.
    """
    lines = path.read_text(encoding="utf-8").split("\n")
    index = next(i for i, line in enumerate(lines) if line.startswith(OPEN_ITEMS_HEADING))
    end = next(i for i in range(index, len(lines)) if lines[i].startswith("| follows row 2"))
    lines.insert(end + 1, "|  |  |  |")
    path.write_text("\n".join(lines), encoding="utf-8")


def drop_loss_row(path: Path, owner_token: str) -> None:
    """Remove one capability row from capability_loss.md.

    Args:
        path: Sandbox copy of capability_loss.md.
        owner_token: Leading path token of the Owner file cell to remove.
    """
    lines = path.read_text(encoding="utf-8").split("\n")
    for index, line in enumerate(lines):
        stripped = line.strip()
        if not (stripped.startswith("|") and stripped.endswith("|")):
            continue
        cells = stripped[1:-1].split("|")
        if len(cells) == LOSS_WIDTH and cells[1].strip().startswith(owner_token):
            del lines[index]
            path.write_text("\n".join(lines), encoding="utf-8")
            return
    raise AssertionError(f"no capability_loss.md row owns {owner_token}")


def add_table_to_not_lost(path: Path) -> None:
    """Insert a table into the capability_loss.md section that declares no root.

    Args:
        path: Sandbox copy of capability_loss.md.
    """
    lines = path.read_text(encoding="utf-8").split("\n")
    index = next(i for i, line in enumerate(lines) if line.startswith("## NOT lost"))
    lines[index + 1 : index + 1] = [
        "",
        "| Capability | Owner file | Requirement |",
        "|---|---|---|",
        "| Fabricated row for a negative test | fabricated.py | FR-9 |",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def test_gate_reports_the_current_tree_exactly(sandbox: Path) -> None:
    """The unmutated tree yields AC1 fail, AC2 pass, SUP1 fail, SUP2 pass.

    This is the finding V2-008 surfaces, not a broken check. Pinning the exact
    shape means a later edit that decides one of the eight blank dispositions,
    or that reconciles the cited 25 against the enumerated 27, has to update this
    test and be seen doing it.
    """
    status, report = run_gate(sandbox)
    assert status == 1, report
    assert f"capabilities enumerated: {BASELINE_CAPABILITIES}" in report
    assert f"disposition rows: {BASELINE_CAPABILITIES}" in report
    assert "[FAIL] AC1" in report
    assert "[PASS] AC2" in report
    assert "[PASS] SUP1" in report
    assert "[PASS] SUP2" in report
    assert f"decided: {BASELINE_DECIDED}; empty: {BASELINE_EMPTY}" in report
    assert report.count("Disposition cell is empty") == BASELINE_EMPTY
    assert f"read at run time: {BASELINE_CITED}; enumerated here: {BASELINE_CAPABILITIES}" in report
    assert "RESULT: FAIL (AC1)" in report


def test_ac1_fails_when_a_decided_disposition_is_emptied(sandbox: Path) -> None:
    """Emptying a decided disposition adds one AC1 failure."""
    rewrite_ledger_cell(sandbox / LEDGER_REL, DECIDED_ROW, DISPOSITION_COLUMN, "")
    status, report = run_gate(sandbox)
    assert status == 1, report
    assert "[FAIL] AC1" in report
    assert f"(row {DECIDED_ROW}): Disposition cell is empty" in report
    assert report.count("Disposition cell is empty") == BASELINE_EMPTY + 1
    assert f"decided: {BASELINE_DECIDED - 1}; empty: {BASELINE_EMPTY + 1}" in report


def test_ac1_fails_when_a_disposition_reads_disappeared(sandbox: Path) -> None:
    """The literal 'disappeared' is the absence of a decision and must fail AC1."""
    rewrite_ledger_cell(sandbox / LEDGER_REL, DECIDED_ROW, DISPOSITION_COLUMN, "disappeared")
    status, report = run_gate(sandbox)
    assert status == 1, report
    assert "[FAIL] AC1" in report
    assert f"(row {DECIDED_ROW}): Disposition reads 'disappeared'" in report


def test_ac1_ignores_an_empty_cell_in_another_table_of_the_same_file(
    sandbox: Path,
) -> None:
    """SPECIFICITY CONTROL: AC1 reads the disposition table, not every empty cell.

    The ledger carries four tables: the evidence-label key, the seven-column
    disposition table, the open-items grouping, and the change log. An AC1 that
    failed on any empty cell anywhere in the document would be indistinguishable
    from one that parses the disposition table at all, and would start reporting
    phantom undecided capabilities as soon as an unrelated table gained a blank
    cell.
    """
    add_empty_open_items_row(sandbox / LEDGER_REL)
    status, report = run_gate(sandbox)
    assert status == 1, report
    assert "[FAIL] AC1" in report
    assert report.count("Disposition cell is empty") == BASELINE_EMPTY
    assert f"decided: {BASELINE_DECIDED}; empty: {BASELINE_EMPTY}" in report


def test_ac1_ignores_an_out_of_vocabulary_token_which_sup2_catches(
    sandbox: Path,
) -> None:
    """SPECIFICITY CONTROL for AC1 and negative test for SUP2, in one state.

    AC1 forbids exactly two things: an empty cell and the literal 'disappeared'.
    A row reading 'deferred' satisfies both, and AC1 must not fail on it -- that
    is what makes SUP2 load-bearing rather than decorative. Asserting both halves
    here proves the two checks are independent: SUP2 fires, AC1 does not, and the
    trap the owner named is caught by exactly one of them.
    """
    rewrite_ledger_cell(sandbox / LEDGER_REL, DECIDED_ROW, DISPOSITION_COLUMN, "deferred")
    status, report = run_gate(sandbox)
    assert status == 1, report
    assert "[FAIL] SUP2" in report
    assert f"(row {DECIDED_ROW}): Disposition 'deferred' is outside the fixed vocabulary" in report
    assert f"(row {DECIDED_ROW}): Disposition cell is empty" not in report
    assert f"(row {DECIDED_ROW}): Disposition reads" not in report
    assert report.count("Disposition cell is empty") == BASELINE_EMPTY


def test_sup2_ignores_the_empty_cells_ac1_owns(sandbox: Path) -> None:
    """SPECIFICITY CONTROL: SUP2 skips empty cells so the two fail independently.

    Eight dispositions are blank on the unmutated tree. A SUP2 that treated an
    empty string as an out-of-vocabulary value would fail on all eight, making it
    impossible to tell an undecided row from a mis-spelled one.
    """
    status, report = run_gate(sandbox)
    assert "[FAIL] AC1" in report
    assert "[PASS] SUP2" in report
    assert "is outside the fixed vocabulary" not in report


def test_ac2_direction_a_fails_when_a_disposition_row_is_dropped(sandbox: Path) -> None:
    """A lost capability with no ledger row is an NFR-4 disappearance."""
    drop_ledger_row(sandbox / LEDGER_REL, DECIDED_ROW)
    status, report = run_gate(sandbox)
    assert status == 1, report
    assert "[FAIL] AC2" in report
    assert "direction A --" in report
    assert DECIDED_CAPABILITY in report
    assert "the disposition ledger has no row for it" in report


def test_ac2_direction_b_fails_when_the_ledger_invents_a_capability(
    sandbox: Path,
) -> None:
    """A ledger row for a capability capability_loss.md does not name fails AC2."""
    append_ledger_row(sandbox / LEDGER_REL, "Fabricated capability for a negative test", "delete")
    status, report = run_gate(sandbox)
    assert status == 1, report
    assert "[FAIL] AC2" in report
    assert "direction B --" in report
    assert "Fabricated capability for a negative test" in report
    assert "which capability_loss.md does not name" in report


def test_ac2_fails_when_the_ledger_names_a_capability_twice(sandbox: Path) -> None:
    """A repeated capability name makes the ledger ambiguous and fails AC2."""
    duplicate_ledger_row(sandbox / LEDGER_REL, DECIDED_ROW)
    status, report = run_gate(sandbox)
    assert status == 1, report
    assert "[FAIL] AC2" in report
    assert "the disposition ledger names the capability" in report
    assert "more than once" in report


def test_ac2_ignores_a_changed_disposition_value(sandbox: Path) -> None:
    """SPECIFICITY CONTROL: AC2 asserts on names, never on the rest of the row.

    An AC2 that compared whole rows, or that re-derived correspondence from the
    Owner file column, would fail whenever a disposition was decided -- turning
    the correspondence check into an obstacle to the very edits this ledger
    exists to receive.
    """
    rewrite_ledger_cell(sandbox / LEDGER_REL, UNDECIDED_ROW, DISPOSITION_COLUMN, "demote-to-advisory")
    status, report = run_gate(sandbox)
    assert status == 1, report
    assert "[PASS] AC2" in report
    assert "direction A --" not in report
    assert "direction B --" not in report
    assert f"decided: {BASELINE_DECIDED + 1}; empty: {BASELINE_EMPTY - 1}" in report


def test_sup1_passes_while_ac2_still_fails_when_two_names_are_dropped(
    sandbox: Path,
) -> None:
    """SPECIFICITY CONTROL: the count check agrees while the names stay wrong.

    Deleting two capability rows from capability_loss.md AND lowering the PRD's
    cited figure to match brings both sides to 25, so SUP1 agrees -- while the
    disposition ledger still carries rows for both dropped capabilities, and AC2
    direction B still fails. This is the defect class this project has caught
    most often, demonstrated live: SUP1 cannot substitute for AC2, and a gate
    asserting only on a count would have exited zero here.

    Both sides must be mutated now that the cited figure is read at run time
    rather than hardcoded. That is the point of reading it: the count can only
    agree at a wrong value when someone changes the citation too, which is a
    visible act rather than a constant quietly rotting.
    """
    for owner in SPARE_OWNERS:
        drop_loss_row(sandbox / LOSS_REL, owner)
    prd = sandbox / PRD_REL
    prd.write_text(
        prd.read_text(encoding="utf-8").replace(
            f"All {BASELINE_CITED} capabilities named in", "All 25 capabilities named in", 1
        ),
        encoding="utf-8",
    )
    status, report = run_gate(sandbox)
    assert status == 1, report
    assert "capabilities enumerated: 25" in report
    assert "[PASS] SUP1" in report
    assert "[FAIL] AC2" in report
    assert report.count("direction B --") == len(SPARE_CAPABILITIES)
    for capability in SPARE_CAPABILITIES:
        assert capability in report


def test_parser_refuses_a_table_in_a_section_that_declares_no_root(
    sandbox: Path,
) -> None:
    """A loss table with no package root is an error, never a silent skip."""
    add_table_to_not_lost(sandbox / LOSS_REL)
    status, report = run_gate(sandbox)
    assert status == 1, report
    assert "FATAL:" in report
    assert "table row outside any section declaring a package root" in report


def test_parser_refuses_a_second_disposition_table_header(sandbox: Path) -> None:
    """Two disposition tables would make every correspondence ambiguous."""
    duplicate_ledger_header(sandbox / LEDGER_REL)
    status, report = run_gate(sandbox)
    assert status == 1, report
    assert "FATAL:" in report
    assert "expected exactly one disposition table header" in report


def test_repository_copies_are_untouched_by_the_sandbox(sandbox: Path) -> None:
    """Mutating the sandbox leaves the repository's own files byte-identical."""
    before = {relative: digest(REPO_ROOT / relative) for relative in SANDBOX_FILES}
    rewrite_ledger_cell(sandbox / LEDGER_REL, DECIDED_ROW, DISPOSITION_COLUMN, "")
    append_ledger_row(sandbox / LEDGER_REL, "Fabricated capability for a negative test", "delete")
    add_empty_open_items_row(sandbox / LEDGER_REL)
    drop_loss_row(sandbox / LOSS_REL, SPARE_OWNERS[0])
    add_table_to_not_lost(sandbox / LOSS_REL)
    run_gate(sandbox)
    after = {relative: digest(REPO_ROOT / relative) for relative in SANDBOX_FILES}
    assert before == after


def test_sup1_fails_when_the_cited_figure_cannot_be_read(sandbox: Path) -> None:
    """The reader fails loudly rather than falling back to a constant.

    Removing the PRD row the gate reads must produce a failure, not a silent
    default. A gate that substitutes a value when its input goes missing reports
    on a document it never read -- which is exactly how this gate came to assert
    a cited count of 25 after the PRD had been corrected to 27.
    """
    prd = sandbox / PRD_REL
    prd.write_text(
        prd.read_text(encoding="utf-8").replace(
            f"All {BASELINE_CITED} capabilities named in `capability_loss.md`", "REMOVED FOR TEST", 1
        ),
        encoding="utf-8",
    )
    status, report = run_gate(sandbox)
    assert status == 1, report
    assert "[FAIL] SUP1" in report
    assert "could not read the cited count" in report
    assert "Not defaulting to a constant" in report

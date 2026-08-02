"""Negative tests for ``scripts/verify_policy_orphan_dispositions.py``.

Every assertion the gate makes is exercised here in a state where it must
fail. A check never observed failing is indistinguishable from a no-op: this
project shipped a validator that claimed to check 14 sections while checking
3, and only executing it against a broken input revealed it.

The gate is always executed from its stored form via ``subprocess``, never
imported and never re-implemented, so what these tests exercise is what a
caller runs.

Mutations are applied to a byte-identical sandbox copy of the two source
documents rather than to the repository's own copies. The audit matrix is
under concurrent edit by other work, and a test that mutates and restores a
file another writer is holding can silently discard that writer's change even
when the restore is byte-exact. Each sandbox is verified against the stored
originals by SHA-256 before use.
"""

from __future__ import annotations

import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_REL = Path("scripts") / "verify_policy_orphan_dispositions.py"
GATE_REL = Path("scripts") / "verify_policy_audit_matrix.py"
AUDIT_REL = Path("docs") / "reports" / "policy-implementation-audit-v2.md"
PRD_REL = Path("docs") / "phase-0-reverse-engineering" / "as-built-prd.md"
SANDBOX_FILES = (SCRIPT_REL, GATE_REL, AUDIT_REL, PRD_REL)

MATRIX_WIDTH = 7
ORPHAN_HEADING = "### 4.2"
SAMPLE_ORPHAN = "session-pruning-policy.md"
SAMPLE_MAPPED = "quality-gate-policy.md"


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


def matrix_row_index(lines: list[str], policy: str) -> int:
    """Find the audit-matrix row naming a policy.

    Args:
        lines: Audit document split into lines.
        policy: Policy filename to locate.

    Returns:
        Index of the matching row within ``lines``.

    Raises:
        AssertionError: If no matrix row names the policy.
    """
    for index, line in enumerate(lines):
        stripped = line.strip()
        if not (stripped.startswith("|") and stripped.endswith("|")):
            continue
        cells = stripped[1:-1].split("|")
        if len(cells) == MATRIX_WIDTH and cells[1].strip().strip("`").strip() == policy:
            return index
    raise AssertionError(f"no matrix row names {policy}")


def rewrite_matrix_cell(path: Path, policy: str, column: int, value: str) -> None:
    """Replace one cell of one audit-matrix row in place.

    Args:
        path: Sandbox copy of the audit document.
        policy: Policy filename identifying the row.
        column: Zero-based cell index within the row.
        value: Replacement cell text, written with single-space padding.
    """
    lines = path.read_text(encoding="utf-8").split("\n")
    index = matrix_row_index(lines, policy)
    cells = lines[index].strip()[1:-1].split("|")
    cells[column] = f" {value} " if value else " "
    lines[index] = "|" + "|".join(cells) + "|"
    path.write_text("\n".join(lines), encoding="utf-8")


def orphan_row_index(lines: list[str], policy: str) -> int:
    """Find the section 4.2 table row naming a policy.

    Args:
        lines: PRD document split into lines.
        policy: Policy filename to locate.

    Returns:
        Index of the matching row within ``lines``.

    Raises:
        AssertionError: If section 4.2 does not name the policy.
    """
    start = next(i for i, line in enumerate(lines) if line.startswith(ORPHAN_HEADING))
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("#")), len(lines))
    for index in range(start + 1, end):
        stripped = lines[index].strip()
        if not (stripped.startswith("|") and stripped.endswith("|")):
            continue
        if stripped[1:-1].split("|")[0].strip().strip("`").strip() == policy:
            return index
    raise AssertionError(f"section 4.2 does not name {policy}")


def drop_orphan_row(path: Path, policy: str) -> None:
    """Remove one policy from the section 4.2 orphan table.

    Args:
        path: Sandbox copy of the PRD.
        policy: Policy filename to remove.
    """
    lines = path.read_text(encoding="utf-8").split("\n")
    del lines[orphan_row_index(lines, policy)]
    path.write_text("\n".join(lines), encoding="utf-8")


def add_orphan_row(path: Path, policy: str) -> None:
    """Append a policy to the section 4.2 orphan table.

    Args:
        path: Sandbox copy of the PRD.
        policy: Policy filename to add, placed after an existing row.
    """
    lines = path.read_text(encoding="utf-8").split("\n")
    anchor = orphan_row_index(lines, SAMPLE_ORPHAN)
    lines.insert(anchor + 1, f"| {policy} | DOCUMENTED-ONLY | Fabricated row for a negative test. |")
    path.write_text("\n".join(lines), encoding="utf-8")


def test_gate_passes_against_the_unmodified_documents(sandbox: Path) -> None:
    """The gate passes on an unmutated sandbox, so failures below mean something."""
    status, report = run_gate(sandbox)
    assert status == 0, report
    assert "RESULT: PASS (AC1, AC2, SUP1)" in report


def test_ac1_fails_when_an_orphan_disposition_is_emptied(sandbox: Path) -> None:
    """Emptying one orphan's Post-plugin plan cell fails AC1."""
    rewrite_matrix_cell(sandbox / AUDIT_REL, SAMPLE_ORPHAN, 4, "")
    status, report = run_gate(sandbox)
    assert status == 1, report
    assert "[FAIL] AC1" in report
    assert f"({SAMPLE_ORPHAN}): Post-plugin plan cell is empty" in report
    assert "RESULT: FAIL (AC1)" in report


def test_ac1_ignores_an_emptied_disposition_on_a_non_orphan_row(sandbox: Path) -> None:
    """AC1 is scoped to the 14 orphans, not to every row that happens to be empty.

    Without this control, an AC1 that failed on any empty cell anywhere would
    be indistinguishable from one that reads the section 4.2 name list at all.
    """
    rewrite_matrix_cell(sandbox / AUDIT_REL, SAMPLE_MAPPED, 4, "")
    status, report = run_gate(sandbox)
    assert status == 0, report
    assert "[PASS] AC1" in report


def test_ac2_direction_a_fails_when_a_named_orphan_has_no_matrix_row(sandbox: Path) -> None:
    """Renaming an orphan's matrix row leaves its section 4.2 name unmatched."""
    rewrite_matrix_cell(sandbox / AUDIT_REL, SAMPLE_ORPHAN, 1, "`session-pruning-policy-renamed.md`")
    status, report = run_gate(sandbox)
    assert status == 1, report
    assert "[FAIL] AC2" in report
    assert f"direction A -- section 4.2 names {SAMPLE_ORPHAN} but no matrix row carries it" in report


def test_ac2_direction_b_fails_when_section_4_2_drops_a_named_orphan(sandbox: Path) -> None:
    """Dropping a row from section 4.2 leaves a matrix row classified nowhere."""
    drop_orphan_row(sandbox / PRD_REL, SAMPLE_ORPHAN)
    status, report = run_gate(sandbox)
    assert status == 1, report
    assert "[FAIL] AC2" in report
    assert f"direction B -- matrix row {SAMPLE_ORPHAN} is classified by neither" in report


def test_ac2_fails_when_section_4_2_names_a_policy_that_does_not_exist(sandbox: Path) -> None:
    """A fabricated name in section 4.2 has no matrix row and fails direction A."""
    add_orphan_row(sandbox / PRD_REL, "invented-policy.md")
    status, report = run_gate(sandbox)
    assert status == 1, report
    assert "[FAIL] AC2" in report
    assert "direction A -- section 4.2 names invented-policy.md but no matrix row carries it" in report


def test_ac2_fails_when_a_policy_is_claimed_by_both_sections(sandbox: Path) -> None:
    """A name in both 4.1 and 4.2 is ambiguous and fails AC2."""
    add_orphan_row(sandbox / PRD_REL, SAMPLE_MAPPED)
    status, report = run_gate(sandbox)
    assert status == 1, report
    assert "[FAIL] AC2" in report
    assert f"{SAMPLE_MAPPED} is named by both section 4.1 (mapped) and section 4.2 (orphan)" in report


def test_sup1_fails_when_the_declared_count_disagrees_with_the_table(sandbox: Path) -> None:
    """Editing the section 4.2 heading count alone fails SUP1 and only SUP1."""
    path = sandbox / PRD_REL
    text = path.read_text(encoding="utf-8")
    assert "### 4.2 Genuine orphans (14 of 46)" in text
    path.write_text(
        text.replace("### 4.2 Genuine orphans (14 of 46)", "### 4.2 Genuine orphans (13 of 46)", 1),
        encoding="utf-8",
    )
    status, report = run_gate(sandbox)
    assert status == 1, report
    assert "[PASS] AC1" in report
    assert "[PASS] AC2" in report
    assert "[FAIL] SUP1" in report
    assert "declares 13 policies but its table enumerates 14" in report
    assert "RESULT: FAIL (SUP1)" in report


def test_repository_copies_are_untouched_by_the_sandbox(sandbox: Path) -> None:
    """Mutating the sandbox leaves the repository's own files byte-identical."""
    before = {relative: digest(REPO_ROOT / relative) for relative in SANDBOX_FILES}
    rewrite_matrix_cell(sandbox / AUDIT_REL, SAMPLE_ORPHAN, 4, "")
    drop_orphan_row(sandbox / PRD_REL, SAMPLE_ORPHAN)
    run_gate(sandbox)
    after = {relative: digest(REPO_ROOT / relative) for relative in SANDBOX_FILES}
    assert before == after

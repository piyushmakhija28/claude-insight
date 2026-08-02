"""Negative tests for ``scripts/verify_policy_capability_dispositions.py``.

Every assertion the gate makes is exercised here in a state where it must fail,
and every assertion that must NOT fire on an unrelated defect is exercised in a
state where it must still pass. A check never observed failing is
indistinguishable from a no-op, and a check that fails on everything is
indistinguishable from a check that reads its inputs.

The gate FAILS against the current tree, on AC2 and SUP1, and that is the
finding rather than a broken check: 20 of the ledger's 27 capabilities have no
matrix row citing their owner file, and the requirement sources cite 25
capabilities where the ledger enumerates 27. ``test_gate_reports_the_current
_tree_exactly`` pins that state so a later change to either artifact cannot move
it silently.

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
GATE_REL = Path("scripts") / "verify_policy_audit_matrix.py"
AUDIT_REL = Path("docs") / "reports" / "policy-implementation-audit-v2.md"
LEDGER_REL = Path("docs") / "phase-0-reverse-engineering" / "capability_loss.md"
SANDBOX_FILES = (SCRIPT_REL, GATE_REL, AUDIT_REL, LEDGER_REL)

MATRIX_WIDTH = 7
LEDGER_WIDTH = 3
PLAN_COLUMN = 4
EVIDENCE_COLUMN = 3

ACCOUNTED_ROW = "version-release-policy.md"
ACCOUNTED_OWNER = "hooks/pre_tool_enforcer/policies/push_gate.py"
UNACCOUNTED_ROW = "quality-gate-policy.md"
OUT_OF_SCOPE_ROW = "session-pruning-policy.md"
OUT_OF_SCOPE_OWNER = "hooks/stop_notifier/core.py"
SPARE_OWNERS = ("daemon.py", "registry.py")
NOT_LOST_HEADING = "## NOT lost"

BASELINE_CAPABILITIES = 27
BASELINE_DIRECTION_A = 20
BASELINE_CITED = 25


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


def append_to_evidence(path: Path, policy: str, addition: str) -> None:
    """Append a citation to one audit-matrix row's Evidence cell.

    Args:
        path: Sandbox copy of the audit document.
        policy: Policy filename identifying the row.
        addition: Text appended after a semicolon separator.
    """
    lines = path.read_text(encoding="utf-8").split("\n")
    index = matrix_row_index(lines, policy)
    cells = lines[index].strip()[1:-1].split("|")
    cells[EVIDENCE_COLUMN] = cells[EVIDENCE_COLUMN].rstrip() + f"; {addition} "
    lines[index] = "|" + "|".join(cells) + "|"
    path.write_text("\n".join(lines), encoding="utf-8")


def ledger_row_index(lines: list[str], owner_token: str) -> int:
    """Find the ledger table row whose Owner file cell opens with a token.

    Args:
        lines: Ledger document split into lines.
        owner_token: Leading path token of the Owner file cell.

    Returns:
        Index of the matching row within ``lines``.

    Raises:
        AssertionError: If no ledger row carries that owner token.
    """
    for index, line in enumerate(lines):
        stripped = line.strip()
        if not (stripped.startswith("|") and stripped.endswith("|")):
            continue
        cells = stripped[1:-1].split("|")
        if len(cells) == LEDGER_WIDTH and cells[1].strip().startswith(owner_token):
            return index
    raise AssertionError(f"no ledger row owns {owner_token}")


def drop_ledger_row(path: Path, owner_token: str) -> None:
    """Remove one capability row from the ledger.

    Args:
        path: Sandbox copy of the ledger.
        owner_token: Leading path token of the Owner file cell to remove.
    """
    lines = path.read_text(encoding="utf-8").split("\n")
    del lines[ledger_row_index(lines, owner_token)]
    path.write_text("\n".join(lines), encoding="utf-8")


def duplicate_ledger_row(path: Path, owner_token: str) -> None:
    """Copy one capability row so the ledger names it twice.

    Args:
        path: Sandbox copy of the ledger.
        owner_token: Leading path token of the Owner file cell to duplicate.
    """
    lines = path.read_text(encoding="utf-8").split("\n")
    index = ledger_row_index(lines, owner_token)
    lines.insert(index + 1, lines[index])
    path.write_text("\n".join(lines), encoding="utf-8")


def add_table_to_not_lost(path: Path) -> None:
    """Insert a table into the section that declares no package root.

    Args:
        path: Sandbox copy of the ledger.
    """
    lines = path.read_text(encoding="utf-8").split("\n")
    index = next(i for i, line in enumerate(lines) if line.startswith(NOT_LOST_HEADING))
    lines[index + 1 : index + 1] = [
        "",
        "| Capability | Owner file | Requirement |",
        "|---|---|---|",
        "| Fabricated row for a negative test | fabricated.py | FR-9 |",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def test_gate_reports_the_current_tree_exactly(sandbox: Path) -> None:
    """The unmutated tree yields AC1 pass, AC2 fail, SUP1 fail -- pinned here.

    This is the finding V2-008 surfaces, not a broken check. Pinning the exact
    shape means a later edit that changes how many capabilities go unaccounted
    for, or that reconciles the cited 25 against the enumerated 27, has to
    update this test and be seen doing it.
    """
    status, report = run_gate(sandbox)
    assert status == 1, report
    assert f"capabilities enumerated: {BASELINE_CAPABILITIES}" in report
    assert "[PASS] AC1" in report
    assert "[FAIL] AC2" in report
    assert "[FAIL] SUP1" in report
    assert report.count("direction A --") == BASELINE_DIRECTION_A
    assert "direction B -- matrix row(s) hook-system-policy.md, tool-usage-optimization-policy.md" in report
    assert (
        f"the requirement sources cite {BASELINE_CITED} capabilities but the ledger "
        f"enumerates {BASELINE_CAPABILITIES}" in report
    )
    assert "RESULT: FAIL (AC2, SUP1)" in report


def test_ac1_fails_when_an_accounted_capability_disposition_is_emptied(sandbox: Path) -> None:
    """Emptying the plan cell of a row that accounts for a capability fails AC1."""
    rewrite_matrix_cell(sandbox / AUDIT_REL, ACCOUNTED_ROW, PLAN_COLUMN, "")
    status, report = run_gate(sandbox)
    assert status == 1, report
    assert "[FAIL] AC1" in report
    assert f"({ACCOUNTED_ROW}): Post-plugin plan cell is empty" in report
    assert ACCOUNTED_OWNER in report


def test_ac1_fails_when_a_disposition_reads_disappeared(sandbox: Path) -> None:
    """The literal 'disappeared' is the absence of a decision and must fail AC1."""
    rewrite_matrix_cell(sandbox / AUDIT_REL, ACCOUNTED_ROW, PLAN_COLUMN, "disappeared")
    status, report = run_gate(sandbox)
    assert status == 1, report
    assert "[FAIL] AC1" in report
    assert f"({ACCOUNTED_ROW}): Post-plugin plan reads 'disappeared'" in report


def test_ac1_ignores_an_emptied_disposition_on_a_row_no_capability_names(sandbox: Path) -> None:
    """SPECIFICITY CONTROL: AC1 is scoped to the ledger, not to every empty cell.

    Without this control, an AC1 that failed on any empty plan cell anywhere in
    the 46-row matrix would be indistinguishable from one that reads the
    capability ledger at all.
    """
    rewrite_matrix_cell(sandbox / AUDIT_REL, UNACCOUNTED_ROW, PLAN_COLUMN, "")
    status, report = run_gate(sandbox)
    assert status == 1, report
    assert "[PASS] AC1" in report
    assert f"({UNACCOUNTED_ROW}): Post-plugin plan cell is empty" not in report


def test_ac2_direction_a_fails_when_a_cited_owner_file_is_removed(sandbox: Path) -> None:
    """Dropping an owner file from Evidence leaves its capability unaccounted for."""
    rewrite_matrix_cell(sandbox / AUDIT_REL, ACCOUNTED_ROW, EVIDENCE_COLUMN, "NONE found")
    status, report = run_gate(sandbox)
    assert status == 1, report
    assert "[FAIL] AC2" in report
    assert f"direction A -- ledger line 32 names {ACCOUNTED_OWNER}" in report
    assert report.count("direction A --") == BASELINE_DIRECTION_A + 1


def test_ac2_direction_b_fails_when_a_row_rests_on_an_unowned_in_scope_file(sandbox: Path) -> None:
    """An in-scope file no ledger entry owns is a gap in the ledger."""
    append_to_evidence(sandbox / AUDIT_REL, UNACCOUNTED_ROW, "`hooks/pre_tool_enforcer/policies/invented.py:1`")
    status, report = run_gate(sandbox)
    assert status == 1, report
    assert "[FAIL] AC2" in report
    assert (
        f"direction B -- matrix row(s) {UNACCOUNTED_ROW} rest on "
        "hooks/pre_tool_enforcer/policies/invented.py" in report
    )


def test_ac2_direction_b_ignores_a_hook_path_outside_the_ledger_scope(sandbox: Path) -> None:
    """SPECIFICITY CONTROL: direction B reads the ledger's roots, not 'hooks/'.

    The Stop hook is retained by the change set and the ledger says so in as
    many words, so a matrix row grounded in ``hooks/stop_notifier/`` must not be
    reported as an unowned capability. A direction B that fired on any path
    under ``hooks/`` would report three false disappearances on the unmutated
    tree.
    """
    status, report = run_gate(sandbox)
    assert OUT_OF_SCOPE_OWNER not in report
    assert f"direction B -- matrix row(s) {OUT_OF_SCOPE_ROW}" not in report


def test_ac2_fails_when_the_ledger_names_a_capability_twice(sandbox: Path) -> None:
    """A repeated capability name makes the ledger ambiguous and fails AC2."""
    duplicate_ledger_row(sandbox / LEDGER_REL, SPARE_OWNERS[0])
    status, report = run_gate(sandbox)
    assert status == 1, report
    assert "[FAIL] AC2" in report
    assert "the ledger names the capability" in report
    assert "more than once" in report


def test_sup1_passes_while_ac2_still_fails_when_two_names_are_dropped(sandbox: Path) -> None:
    """SPECIFICITY CONTROL: the count check agrees while the names stay wrong.

    Deleting two unaccounted capability rows brings the enumeration to the cited
    25, so SUP1 passes -- while 18 capabilities remain unaccounted for and AC2
    still fails. This is the defect class this project has caught most often,
    demonstrated live: SUP1 cannot substitute for AC2, and a gate asserting only
    on the count of 25 would have exited zero here.
    """
    for owner in SPARE_OWNERS:
        drop_ledger_row(sandbox / LEDGER_REL, owner)
    status, report = run_gate(sandbox)
    assert status == 1, report
    assert f"capabilities enumerated: {BASELINE_CITED}" in report
    assert "[PASS] SUP1" in report
    assert "[FAIL] AC2" in report
    assert report.count("direction A --") == BASELINE_DIRECTION_A - 2
    assert "RESULT: FAIL (AC2)" in report


def test_parser_refuses_a_table_in_a_section_that_declares_no_root(sandbox: Path) -> None:
    """A loss table with no package root is an error, never a silent skip."""
    add_table_to_not_lost(sandbox / LEDGER_REL)
    status, report = run_gate(sandbox)
    assert status == 1, report
    assert "FATAL:" in report
    assert "table row outside any section declaring a package root" in report


def test_repository_copies_are_untouched_by_the_sandbox(sandbox: Path) -> None:
    """Mutating the sandbox leaves the repository's own files byte-identical."""
    before = {relative: digest(REPO_ROOT / relative) for relative in SANDBOX_FILES}
    rewrite_matrix_cell(sandbox / AUDIT_REL, ACCOUNTED_ROW, PLAN_COLUMN, "")
    append_to_evidence(sandbox / AUDIT_REL, UNACCOUNTED_ROW, "`hooks/pre_tool_enforcer/policies/invented.py:1`")
    drop_ledger_row(sandbox / LEDGER_REL, SPARE_OWNERS[0])
    add_table_to_not_lost(sandbox / LEDGER_REL)
    run_gate(sandbox)
    after = {relative: digest(REPO_ROOT / relative) for relative in SANDBOX_FILES}
    assert before == after

"""Tests for the Stop-hook dead-reference retirement (V2-034, PRD FR-21 / SRS FR-33).

Every assertion drives the audit functions as they are STORED in
``scripts/tools/stop_hook_dead_reference_audit.py``. Nothing is re-authored here,
because a check re-typed into its own test proves only that the copy agrees with
itself.

The positive assertions alone would be indistinguishable from a no-op, so each is
paired with a negative that plants a defect into a temporary package tree and
proves the same stored function reports it. Specificity is asserted in both
directions: the audit must fire on a reference whose target exists nowhere, and
must NOT fire on a reference whose target is a real file.
"""

import importlib.util
import os
import sys
from pathlib import Path

import pytest

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_MODULE_PATH = os.path.join(_REPO_ROOT, "scripts", "tools", "stop_hook_dead_reference_audit.py")

_SPEC = importlib.util.spec_from_file_location("stop_hook_dead_reference_audit", _MODULE_PATH)
audit = importlib.util.module_from_spec(_SPEC)
sys.modules["stop_hook_dead_reference_audit"] = audit
_SPEC.loader.exec_module(audit)

pytestmark = pytest.mark.unit

REPO_ROOT = Path(_REPO_ROOT)
PACKAGE_DIR = REPO_ROOT / "hooks" / "stop_notifier"
CORE_MODULE = PACKAGE_DIR / "core.py"


def _plant(tmp_path, filename, body):
    """Create a one-file package tree carrying a planted reference.

    Args:
        tmp_path: pytest temporary directory.
        filename: Name of the module to write inside the fake package.
        body: Source text to write.

    Returns:
        Path to the fake package directory.
    """
    package = tmp_path / "stop_notifier"
    package.mkdir(exist_ok=True)
    (package / filename).write_text(body, encoding="utf-8")
    return package


class TestCriterionTwo:
    """Criterion 2: a grep for the seven names yields a real file or nothing."""

    def test_no_retired_script_has_any_reference_left(self):
        for verdict in audit.audit_all():
            assert verdict.state == audit.RETIRED, f"{verdict.script}: {verdict.references}"

    def test_criterion_two_passes_on_the_real_tree(self):
        assert audit.evaluate_criterion_two(audit.audit_all())["verdict"] == "PASS"

    def test_planted_dangling_reference_is_caught(self, tmp_path):
        """Negative test: the check must be able to fail."""
        package = _plant(
            tmp_path,
            "core.py",
            'script = _dir / "archive-old-sessions.py"\n',
        )
        verdict = audit.audit_script(package, REPO_ROOT, "archive-old-sessions.py")
        assert verdict.state == audit.DANGLING
        outcome = audit.evaluate_criterion_two([verdict])
        assert outcome["verdict"] == "FAIL"
        assert "archive-old-sessions.py" in outcome["reasons"][0]

    def test_reference_to_a_real_file_is_not_flagged_dangling(self, tmp_path):
        """Specificity, other direction: a real target must not trip the check."""
        package = _plant(
            tmp_path,
            "core.py",
            'script = _dir / "sync-version.py"\n',
        )
        verdict = audit.audit_script(package, REPO_ROOT, "sync-version.py")
        assert verdict.state == audit.SATISFIABLE
        assert verdict.targets, "sync-version.py must resolve to a real file"
        assert audit.evaluate_criterion_two([verdict])["verdict"] == "PASS"

    def test_substring_match_does_not_count_as_a_reference(self, tmp_path):
        """Specificity: a longer basename must not satisfy a shorter name's grep."""
        package = _plant(tmp_path, "core.py", 'script = _dir / "my-session-pruner.py"\n')
        assert audit.audit_script(package, REPO_ROOT, "session-pruner.py").state == audit.RETIRED


class TestCriterionOne:
    """Criterion 1: each script is armed, or retired AND carries a disposition."""

    def test_criterion_one_passes_on_the_real_tree(self):
        outcome = audit.evaluate_criterion_one(audit.audit_all(), audit.ledger_dispositions())
        assert outcome["verdict"] == "PASS", outcome["reasons"]

    def test_every_retired_script_has_a_ledger_disposition(self):
        dispositions = audit.ledger_dispositions()
        for script in audit.RETIRED_SCRIPTS:
            assert dispositions.get(script), f"{script} carries no disposition"

    def test_every_disposition_is_in_the_fixed_vocabulary(self):
        dispositions = audit.ledger_dispositions()
        for script in audit.RETIRED_SCRIPTS:
            assert dispositions[script] in audit.DISPOSITION_VOCABULARY

    def test_retirement_without_a_disposition_fails(self):
        """Negative test: option (b)'s second half is genuinely enforced.

        The reason text is asserted, not merely the count. Counting alone let a
        mutant survive that deleted the missing-disposition branch entirely: the
        empty string then fell through to the vocabulary branch, which reported
        the same number of failures under a different and misleading reason.
        """
        verdicts = audit.audit_all()
        outcome = audit.evaluate_criterion_one(verdicts, {})
        assert outcome["verdict"] == "FAIL"
        assert len(outcome["reasons"]) == len(audit.RETIRED_SCRIPTS)
        assert all("carries no disposition in the ledger" in reason for reason in outcome["reasons"])

    def test_a_disposition_outside_the_vocabulary_fails(self):
        """Negative test: 'TBD' must not satisfy the ledger requirement."""
        verdicts = audit.audit_all()
        dispositions = dict(audit.ledger_dispositions())
        dispositions[audit.RETIRED_SCRIPTS[0]] = "TBD"
        outcome = audit.evaluate_criterion_one(verdicts, dispositions)
        assert outcome["verdict"] == "FAIL"
        assert "outside the fixed vocabulary" in outcome["reasons"][0]


class TestScopeReconciliation:
    """The issue names 7; V2-033 measured 9. Both are right at their own scope."""

    def test_core_module_carries_no_script_reference(self):
        for script in audit.RETIRED_SCRIPTS:
            assert not audit.scan_references(CORE_MODULE.parent, script)

    def test_the_two_out_of_scope_references_are_untouched(self):
        """V2-034 must not silently widen its own scope to V2-033's nine."""
        text = (PACKAGE_DIR / "post_impl.py").read_text(encoding="utf-8")
        assert "sync-version.py" in text
        assert "voice-notifier.py" in (PACKAGE_DIR / "helpers.py").read_text(encoding="utf-8")

    def test_no_retired_script_exists_anywhere_so_option_a_was_unreachable(self):
        for script in audit.RETIRED_SCRIPTS:
            assert audit.find_targets(REPO_ROOT, script) == []


class TestRemovalDidNotStrandTheLivePath:
    """The seven blocks carried bindings the surviving git calls depend on."""

    def test_subprocess_is_imported_at_module_level(self):
        """``subprocess`` was imported inside the first retired block.

        The surviving branch-detection and retry paths call ``subprocess.run``.
        Had the import been removed with the block, every one would have raised
        NameError into its own ``except`` and gone silently dead.
        """
        import hooks.stop_notifier.core as core

        assert hasattr(core, "subprocess")

    def test_core_module_still_imports_and_defines_main(self):
        import hooks.stop_notifier.core as core

        assert callable(core.main)

    def test_surviving_subprocess_call_sites_are_still_present(self):
        text = CORE_MODULE.read_text(encoding="utf-8")
        assert text.count("subprocess.run(") == 4

    def test_no_name_is_imported_that_is_no_longer_used(self):
        """``get_current_session_id`` was used only by the retired plan block."""
        text = CORE_MODULE.read_text(encoding="utf-8")
        assert "get_current_session_id" not in text

    def test_source_is_ascii_only(self):
        assert CORE_MODULE.read_text(encoding="utf-8").isascii()


class TestPrCreationPathUntouched:
    """REVIEW-INDEX 40: nothing here may arm unprompted PR creation."""

    def test_pr_workflow_call_sites_are_unchanged(self):
        text = CORE_MODULE.read_text(encoding="utf-8")
        assert text.count("github_pr_workflow.run_pr_workflow()") == 3

    def test_no_retired_script_was_on_the_pr_creation_path(self):
        """The seven are script spawns; the PR path is a module import."""
        text = CORE_MODULE.read_text(encoding="utf-8")
        for script in audit.RETIRED_SCRIPTS:
            assert script not in text

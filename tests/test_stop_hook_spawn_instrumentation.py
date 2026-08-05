"""Tests for the Stop-hook spawn instrumentation (V2-033, PRD FR-8a / SRS FR-19).

The gate under test is expressed as an enumerated set of spawn opportunities
rather than as a spawn count. That form was chosen because it stays valid in
both directions: it fails when a spawn appears that nobody enumerated, and it
passes when a guarded opportunity stays silent. Both directions are proved here,
because a check never observed failing is indistinguishable from a no-op, and a
check never observed passing on the inert case would re-introduce the brittleness
the enumerated form exists to avoid.

Every assertion drives ``evaluate_spawn_floor`` as it is STORED in
``scripts/tools/stop_hook_spawn_instrument.py``. Nothing is re-authored here.
"""

import importlib.util
import os
import sys

import pytest

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_MODULE_PATH = os.path.join(_REPO_ROOT, "scripts", "tools", "stop_hook_spawn_instrument.py")

_SPEC = importlib.util.spec_from_file_location("stop_hook_spawn_instrument", _MODULE_PATH)
instrument = importlib.util.module_from_spec(_SPEC)
sys.modules["stop_hook_spawn_instrument"] = instrument
_SPEC.loader.exec_module(instrument)

pytestmark = pytest.mark.unit

MEASURED_SEQUENCE = (
    ["git", "branch", "--show-current"],
    ["git", "rev-list", "--count", "main..docs/segregate-docs-tree"],
    ["git", "status", "--porcelain"],
    ["git", "rev-parse", "--abbrev-ref", "HEAD"],
    ["git", "rev-list", "--count", "main..HEAD"],
    ["git", "rev-parse", "--abbrev-ref", "HEAD"],
    ["git", "rev-list", "--count", "main..HEAD"],
)


def _attribute(sequence, guards=()):
    """Attribute a spawn sequence using the stored attributor."""
    return instrument.attribute_spawns([list(item) for item in sequence], guards)


class TestSpawnFloorSubset:
    """Acceptance criterion 2: the enumerated-subset form of the floor."""

    def test_measured_sequence_passes_the_floor(self):
        outcome = instrument.evaluate_spawn_floor(_attribute(MEASURED_SEQUENCE))
        assert outcome["verdict"] == "PASS", outcome["reasons"]

    def test_every_measured_spawn_is_inside_the_enumerated_or_excepted_set(self):
        attributions = _attribute(MEASURED_SEQUENCE)
        assert all(item["bucket"] in ("enumerated", "named_exception") for item in attributions)
        assert [item["bucket"] for item in attributions].count("unclassified") == 0

    def test_both_unconditional_opportunities_fired(self):
        sites = [item["site"] for item in _attribute(MEASURED_SEQUENCE)]
        assert "hooks/stop_notifier/post_impl.py:55" in sites
        assert "hooks/stop_notifier/post_impl.py:208" in sites

    def test_specificity_silent_guarded_opportunities_do_not_fail(self):
        outcome = instrument.evaluate_spawn_floor(_attribute(MEASURED_SEQUENCE))
        assert outcome["verdict"] == "PASS"
        assert set(outcome["silent_guarded_opportunities"]) == {
            "hooks/stop_notifier/post_impl.py:286",
            "hooks/stop_notifier/voice.py:164",
        }

    def test_specificity_guarded_opportunities_firing_also_passes(self):
        armed = list(MEASURED_SEQUENCE) + [
            [sys.executable, "hooks/stop_notifier/sync-version.py"],
            [sys.executable, "voice-notifier.py", "spoken text"],
        ]
        outcome = instrument.evaluate_spawn_floor(_attribute(armed))
        assert outcome["verdict"] == "PASS", outcome["reasons"]
        assert outcome["silent_guarded_opportunities"] == []


class TestSpawnFloorNegative:
    """Proof that the floor can fail, in each way it is meant to fail."""

    def test_negative_unknown_fifth_spawn_fails(self):
        intruder = list(MEASURED_SEQUENCE) + [["curl", "https://example.invalid/payload"]]
        outcome = instrument.evaluate_spawn_floor(_attribute(intruder))
        assert outcome["verdict"] == "FAIL"
        assert any("outside the enumerated set" in reason for reason in outcome["reasons"])

    def test_negative_unknown_spawn_of_a_python_script_fails(self):
        intruder = list(MEASURED_SEQUENCE) + [[sys.executable, "some-new-helper.py"]]
        outcome = instrument.evaluate_spawn_floor(_attribute(intruder))
        assert outcome["verdict"] == "FAIL"

    def test_negative_missing_first_unconditional_opportunity_fails(self):
        truncated = [item for item in MEASURED_SEQUENCE][:5]
        outcome = instrument.evaluate_spawn_floor(_attribute(truncated))
        assert outcome["verdict"] == "FAIL"
        assert any("post_impl.py:55" in reason for reason in outcome["reasons"])

    def test_negative_no_spawns_at_all_fails_on_both_unconditionals(self):
        outcome = instrument.evaluate_spawn_floor(_attribute(()))
        assert outcome["verdict"] == "FAIL"
        assert len(outcome["reasons"]) == 2

    def test_negative_named_exceptions_alone_are_not_sufficient(self):
        exceptions_only = MEASURED_SEQUENCE[:3]
        outcome = instrument.evaluate_spawn_floor(_attribute(exceptions_only))
        assert outcome["verdict"] == "FAIL"


class TestAttributionUsesMeasuredEvidence:
    """The duplicated git shapes must not be attributed by argv text alone."""

    def test_identical_argv_pairs_attribute_to_distinct_sites(self):
        sites = [item["site"] for item in _attribute(MEASURED_SEQUENCE)]
        assert sites[3] == "hooks/stop_notifier/post_impl.py:208"
        assert sites[5] == "hooks/stop_notifier/post_impl.py:55"
        assert sites[4] == "hooks/stop_notifier/post_impl.py:216"
        assert sites[6] == "hooks/stop_notifier/post_impl.py:64"

    def test_named_branch_rev_list_is_distinguished_from_head_rev_list(self):
        sites = [item["site"] for item in _attribute(MEASURED_SEQUENCE)]
        assert sites[1] == "hooks/stop_notifier/core.py:422"
        assert sites[1] != sites[4]

    def test_retry_flag_guard_evidence_moves_the_branch_attribution(self):
        sequence = [["git", "branch", "--show-current"]] + list(MEASURED_SEQUENCE)
        guards = [("/home/.claude/.pr-workflow-retry", True)]
        sites = [item["site"] for item in _attribute(sequence, guards)]
        assert sites[0] == "hooks/stop_notifier/core.py:349"
        assert sites[1] == "hooks/stop_notifier/core.py:377"

    def test_negative_without_retry_flag_evidence_no_site_is_349(self):
        sites = [item["site"] for item in _attribute(MEASURED_SEQUENCE, [])]
        assert "hooks/stop_notifier/core.py:349" not in sites

    def test_negative_third_rev_parse_is_unclassified_not_an_index_error(self):
        overflowing = list(MEASURED_SEQUENCE) + [["git", "rev-parse", "--abbrev-ref", "HEAD"]]
        attributions = _attribute(overflowing)
        assert attributions[-1]["site"] is None
        assert attributions[-1]["bucket"] == "unclassified"
        assert instrument.evaluate_spawn_floor(attributions)["verdict"] == "FAIL"

    def test_negative_third_rev_list_is_unclassified_not_an_index_error(self):
        overflowing = list(MEASURED_SEQUENCE) + [["git", "rev-list", "--count", "main..HEAD"]]
        attributions = _attribute(overflowing)
        assert attributions[-1]["bucket"] == "unclassified"
        assert instrument.evaluate_spawn_floor(attributions)["verdict"] == "FAIL"


class TestCensusMatchesCarriedForwardFigures:
    """Re-measurement of every figure the acceptance criterion carries forward."""

    def test_ten_call_sites_split_four_five_one(self):
        """Re-measured after V2-034 retired seven dead spawns from core.py.

        V2-033 measured 17 call sites split 11/5/1/0. V2-034 removed the seven
        ``core.py`` spawns whose targets existed nowhere on disk, so the census is
        now 10, split 4/5/1/0. The change is in ``core.py`` only, and the delta is
        exactly seven -- both asserted below rather than merely restated, so this
        test still fails if some other file's count moves.
        """
        census = instrument.census_call_sites()
        assert len(census["core.py"]) == 4
        assert len(census["post_impl.py"]) == 5
        assert len(census["voice.py"]) == 1
        assert len(census["helpers.py"]) == 0
        assert sum(len(sites) for sites in census.values() if sites) == 10

    def test_carried_forward_line_numbers_are_call_sites(self):
        census = instrument.census_call_sites()
        post_impl_lines = [site["line"] for site in census["post_impl.py"]]
        assert 55 in post_impl_lines
        assert 208 in post_impl_lines
        assert 286 in post_impl_lines

    def test_negative_voice_spawn_is_at_164_not_the_docstring_line_144(self):
        census = instrument.census_call_sites()
        voice_lines = [site["line"] for site in census["voice.py"]]
        assert voice_lines == [164]
        assert 144 not in voice_lines

    def test_all_nine_referenced_scripts_resolve_to_missing_targets(self):
        resolved = instrument.resolve_referenced_scripts()
        assert len(resolved) == 9
        assert all(entry["capability"] == "INERT" for entry in resolved)

    def test_negative_resolver_reports_armed_when_a_target_exists(self, tmp_path):
        hook_package = instrument.HOOK_PACKAGE
        try:
            instrument.HOOK_PACKAGE = tmp_path
            (tmp_path / "sync-version.py").write_text("", encoding="utf-8")
            resolved = instrument.resolve_referenced_scripts()
            entry = [item for item in resolved if item["label"] == "sync-version.py"][0]
            assert entry["capability"] == "ARMED"
        finally:
            instrument.HOOK_PACKAGE = hook_package

    def test_voice_target_resolves_under_home_not_as_a_package_sibling(self, tmp_path):
        resolved = instrument.resolve_referenced_scripts(home=tmp_path)
        entry = [item for item in resolved if item["label"] == "voice-notifier.py"][0]
        target = entry["resolved_target"].replace("\\", "/")
        assert not target.endswith("hooks/stop_notifier/voice-notifier.py")
        assert "/.claude/" in target


class TestGuardDispositionIsNotConflated:
    """A guard that never ran must not be reported as a guard that returned False."""

    def test_evaluated_false_guard_is_reported_as_skipped(self):
        guards = [("/repo/hooks/stop_notifier/sync-version.py", False)]
        summary = instrument.summarize_script_guards(guards)
        assert summary["sync-version.py"]["disposition"] == "GUARD_FALSE_SCRIPT_SKIPPED"

    def test_negative_unevaluated_guard_is_reported_as_not_reached(self):
        summary = instrument.summarize_script_guards([])
        assert summary["voice-notifier.py"]["disposition"] == "GUARD_NOT_REACHED"
        assert summary["voice-notifier.py"]["disposition"] != "GUARD_FALSE_SCRIPT_SKIPPED"

    def test_true_guard_is_reported_as_ran(self):
        guards = [("/anywhere/voice-notifier.py", True)]
        summary = instrument.summarize_script_guards(guards)
        assert summary["voice-notifier.py"]["disposition"] == "GUARD_TRUE_SCRIPT_RAN"


class TestLiveInvocation:
    """One real execution of the real entry point, so the suite is not only synthetic."""

    @pytest.mark.slow
    def test_live_invocation_matches_the_measured_sequence(self):
        report = instrument.run_invocations(count=1, control_count=0)
        observation = report["invocations"][0]
        outcome = instrument.evaluate_spawn_floor(observation["attributions"])
        assert outcome["verdict"] == "PASS", outcome["reasons"]
        assert observation["spawn_count"] >= len(instrument.REQUIRED_FIRING_SITES)
        assert observation["returncode"] == 0

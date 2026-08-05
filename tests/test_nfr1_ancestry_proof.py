"""Tests for proving a process does NOT descend from the plugin.

A live measurement showed why this exists: on a working machine, unrelated software
can never be attributed to any declared component, so the "any unattributed process
means INDETERMINATE" rule held permanently and NFR-1 could never reach a verdict.

Splitting "unknown" from "proved not plugin-descended" fixes that, and it is exactly
the kind of change that can quietly destroy the measurement. If the proof were ever
granted to a plugin-spawned process, NFR-1 would report a pass while the plugin ran.

So the load-bearing tests here are the ones that try to obtain the proof for something
that does not deserve it. Each positive is paired with the attack that must fail.
"""

import os
import sys

import pytest

_TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
if _TESTS_DIR not in sys.path:
    sys.path.insert(0, _TESTS_DIR)

from nfr1 import attribution as attribution_mod  # noqa: E402
from nfr1 import components, process_probe  # noqa: E402

pytestmark = pytest.mark.unit

PLUGIN_MARKER = "plugin_marker"


def _record(pid, ppid=None, name="python.exe", cmdline="python.exe", token="100.0", denied=False):
    """Build a synthetic ProcessRecord.

    Creation tokens default to a value high enough that any ancestor built with the
    default lower token satisfies the parent-predates-child guard.
    """
    return process_probe.ProcessRecord(
        pid=pid,
        ppid=ppid,
        name=name,
        exe=None,
        cmdline=cmdline,
        create_token=token,
        access_denied=denied,
    )


def _plugin_registry():
    """Build a registry with only a plugin component, so nothing else can absorb a match."""
    registry = components.ComponentRegistry()
    registry.register(
        components.ComponentSpec(
            key=components.KEY_PLUGIN,
            role=components.ROLE_PLUGIN_COUNTED,
            markers=[PLUGIN_MARKER],
        )
    )
    return registry


def _attribute(record, index, baseline_pids):
    """Attribute one record and return its single Attribution."""
    result = attribution_mod.attribute([record], _plugin_registry(), index, baseline_pids=baseline_pids)
    return result.attributions[0]


class TestAProofIsGrantedWhenTheChainIsClean:
    """The behaviour the change exists to enable."""

    def test_a_chain_reaching_the_baseline_with_no_plugin_is_proved(self):
        baseline = _record(10, ppid=None, cmdline="explorer.exe", token="1.0")
        child = _record(11, ppid=10, cmdline="chrome.exe", token="2.0")
        attribution = _attribute(child, {10: baseline}, {10})
        assert attribution.component_key == attribution_mod.NOT_PLUGIN_DESCENDED_KEY

    def test_a_proved_process_is_not_counted_as_unknown(self):
        baseline = _record(10, ppid=None, cmdline="explorer.exe", token="1.0")
        child = _record(11, ppid=10, cmdline="chrome.exe", token="2.0")
        result = attribution_mod.attribute([child], _plugin_registry(), {10: baseline}, baseline_pids={10})
        assert result.unattributed == []
        assert len(result.not_plugin_descended) == 1

    def test_a_multi_hop_chain_reaching_the_baseline_is_proved(self):
        baseline = _record(10, ppid=None, cmdline="explorer.exe", token="1.0")
        middle = _record(11, ppid=10, cmdline="conhost.exe", token="2.0")
        leaf = _record(12, ppid=11, cmdline="cmd.exe", token="3.0")
        attribution = _attribute(leaf, {10: baseline, 11: middle}, {10})
        assert attribution.component_key == attribution_mod.NOT_PLUGIN_DESCENDED_KEY


class TestTheProofCannotLaunderAPluginProcess:
    """The attacks. Every one of these must refuse the proof."""

    def test_a_plugin_ancestor_below_the_baseline_still_charges_the_plugin(self):
        """The single most important test in this file.

        The chain reaches the baseline cleanly, which is the proof condition -- but a
        plugin sits on it. Plugin-first precedence must find it and the proof must
        never be reached.
        """
        baseline = _record(10, ppid=None, cmdline="explorer.exe", token="1.0")
        plugin = _record(11, ppid=10, cmdline="python %s/entry.py" % PLUGIN_MARKER, token="2.0")
        leaf = _record(12, ppid=11, cmdline="bash.exe -c work", token="3.0")
        result = attribution_mod.attribute([leaf], _plugin_registry(), {10: baseline, 11: plugin}, baseline_pids={10})
        assert result.plugin_count == 1
        assert result.not_plugin_descended == []
        assert result.attributions[0].basis == attribution_mod.BASIS_ANCESTRY

    def test_a_process_that_is_itself_the_plugin_is_never_proved(self):
        baseline = _record(10, ppid=None, cmdline="explorer.exe", token="1.0")
        leaf = _record(11, ppid=10, cmdline="python %s/entry.py" % PLUGIN_MARKER, token="2.0")
        result = attribution_mod.attribute([leaf], _plugin_registry(), {10: baseline}, baseline_pids={10})
        assert result.plugin_count == 1
        assert result.not_plugin_descended == []

    def test_a_plugin_sitting_on_the_baseline_itself_still_charges_the_plugin(self):
        """The baseline is checked AFTER the ancestor's markers, not before."""
        baseline = _record(10, ppid=None, cmdline="python %s/entry.py" % PLUGIN_MARKER, token="1.0")
        leaf = _record(11, ppid=10, cmdline="bash.exe -c work", token="2.0")
        result = attribution_mod.attribute([leaf], _plugin_registry(), {10: baseline}, baseline_pids={10})
        assert result.plugin_count == 1
        assert result.not_plugin_descended == []


class TestAnIncompleteWalkIsNeverAProof:
    """Missing data must read as unknown, never as evidence of absence."""

    def test_a_missing_parent_record_is_unknown(self):
        orphan = _record(11, ppid=999, cmdline="bash.exe", token="2.0")
        attribution = _attribute(orphan, {}, {10})
        assert attribution.component_key == attribution_mod.UNATTRIBUTED_KEY

    def test_a_withheld_parent_pid_is_unknown_not_a_root(self):
        """ppid None means the backend would not say, which is missing data.

        Reading it as "this process has no parent, therefore nothing above it is the
        plugin" would manufacture a proof out of a refusal to answer.
        """
        no_parent = _record(11, ppid=None, cmdline="bash.exe", token="2.0")
        attribution = _attribute(no_parent, {}, {10})
        assert attribution.component_key == attribution_mod.UNATTRIBUTED_KEY

    def test_a_chain_that_never_reaches_the_baseline_is_unknown(self):
        outsider = _record(20, ppid=None, cmdline="svchost.exe", token="1.0")
        leaf = _record(21, ppid=20, cmdline="bash.exe", token="2.0")
        attribution = _attribute(leaf, {20: outsider}, {10})
        assert attribution.component_key == attribution_mod.UNATTRIBUTED_KEY

    def test_an_unreadable_hop_blocks_the_proof(self):
        baseline = _record(10, ppid=None, cmdline="explorer.exe", token="1.0")
        hidden = _record(11, ppid=10, cmdline=None, token="2.0", denied=True)
        leaf = _record(12, ppid=11, cmdline="bash.exe", token="3.0")
        attribution = _attribute(leaf, {10: baseline, 11: hidden}, {10})
        assert attribution.component_key == attribution_mod.UNATTRIBUTED_KEY

    def test_a_parent_created_after_its_child_is_a_broken_chain(self):
        """A reused pid can point at a process that cannot be the real parent.

        Following it would walk a chain that never existed and could terminate at a
        baseline that has nothing to do with this process.
        """
        baseline = _record(10, ppid=None, cmdline="explorer.exe", token="900.0")
        leaf = _record(11, ppid=10, cmdline="bash.exe", token="2.0")
        attribution = _attribute(leaf, {10: baseline}, {10})
        assert attribution.component_key == attribution_mod.UNATTRIBUTED_KEY

    def test_a_cycle_is_unknown(self):
        a = _record(10, ppid=11, cmdline="a.exe", token="1.0")
        b = _record(11, ppid=10, cmdline="b.exe", token="1.0")
        attribution = _attribute(_record(12, ppid=10, cmdline="leaf.exe", token="1.0"), {10: a, 11: b}, {99})
        assert attribution.component_key == attribution_mod.UNATTRIBUTED_KEY

    def test_exceeding_the_depth_guard_is_unknown(self):
        index = {}
        for hop in range(1, 40):
            index[hop] = _record(hop, ppid=hop + 1, cmdline="hop%d.exe" % hop, token="1.0")
        leaf = _record(0, ppid=1, cmdline="leaf.exe", token="1.0")
        attribution = _attribute(leaf, index, {39})
        assert attribution.component_key == attribution_mod.UNATTRIBUTED_KEY


class TestAnUnreadableHopStillLetsThePluginBeFound:
    """Refusing to read a hop must not stop the search for the plugin above it.

    Stopping there would under-report the one thing NFR-1 counts, which is the
    dangerous direction to err in. The hop poisons the proof; it does not end the walk.
    """

    def test_a_plugin_above_an_unreadable_hop_is_still_charged(self):
        baseline = _record(10, ppid=None, cmdline="explorer.exe", token="1.0")
        plugin = _record(11, ppid=10, cmdline="python %s/entry.py" % PLUGIN_MARKER, token="2.0")
        hidden = _record(12, ppid=11, cmdline=None, token="3.0", denied=True)
        leaf = _record(13, ppid=12, cmdline="bash.exe", token="4.0")
        result = attribution_mod.attribute(
            [leaf], _plugin_registry(), {10: baseline, 11: plugin, 12: hidden}, baseline_pids={10}
        )
        assert result.plugin_count == 1


class TestProofIsOptIn:
    """No caller gains proof by accident."""

    def test_without_a_baseline_nothing_is_ever_proved(self):
        parent = _record(10, ppid=None, cmdline="explorer.exe", token="1.0")
        child = _record(11, ppid=10, cmdline="chrome.exe", token="2.0")
        result = attribution_mod.attribute([child], _plugin_registry(), {10: parent})
        assert result.not_plugin_descended == []
        assert len(result.unattributed) == 1

    def test_the_same_input_with_a_baseline_is_proved(self):
        """Paired half: the previous test must fail for the absent baseline, not always."""
        parent = _record(10, ppid=None, cmdline="explorer.exe", token="1.0")
        child = _record(11, ppid=10, cmdline="chrome.exe", token="2.0")
        result = attribution_mod.attribute([child], _plugin_registry(), {10: parent}, baseline_pids={10})
        assert len(result.not_plugin_descended) == 1
        assert result.unattributed == []


class TestTheSamplerFillsTheAncestryIndex:
    """A short-lived parent seen only by the sampler must make its child walkable.

    Indexing only the endpoint snapshots left these chains broken at the first hop,
    which is what made a live window report 63 processes as unknown while every one of
    them carried a usable parent pid.
    """

    def test_index_from_records_indexes_what_the_sampler_saw(self):
        transient = _record(11, ppid=10, cmdline="sh.exe", token="2.0")
        index = attribution_mod.index_from_records([transient])
        assert index[11] is transient

    def test_a_short_lived_parent_makes_its_child_provable(self):
        baseline = _record(10, ppid=None, cmdline="explorer.exe", token="1.0")
        transient_parent = _record(11, ppid=10, cmdline="sh.exe", token="2.0")
        leaf = _record(12, ppid=11, cmdline="conhost.exe", token="3.0")

        without_parent = _attribute(leaf, {10: baseline}, {10})
        assert without_parent.component_key == attribution_mod.UNATTRIBUTED_KEY

        with_parent = _attribute(leaf, {10: baseline, 11: transient_parent}, {10})
        assert with_parent.component_key == attribution_mod.NOT_PLUGIN_DESCENDED_KEY

    def test_reuse_keeps_the_most_recent_record(self):
        older = _record(11, ppid=1, cmdline="old.exe", token="1.0")
        newer = _record(11, ppid=2, cmdline="new.exe", token="9.0")
        index = attribution_mod.index_from_records([older, newer])
        assert index[11] is newer


class TestTheBaselineIsCheckedAfterTheMarkers:
    """Order matters inside the walk, and attribute() masks getting it wrong.

    If the baseline terminated the walk before an ancestor's markers were read, a plugin
    sitting ON the baseline would hand out a proof instead of a charge. Through
    attribute() that mistake is invisible: the any-role fallback walk passes no baseline,
    so it walks past the baseline, finds the plugin and charges it anyway. A mutation
    confirmed the higher-level tests cannot see the defect at all.

    So this asserts the ordering where it is actually decided, on the walk itself. The
    fallback is defence in depth, not the guarantee, and it would evaporate the day
    somebody passes a baseline to it.
    """

    def test_a_plugin_on_the_baseline_yields_a_match_not_a_baseline_termination(self):
        baseline = _record(10, ppid=None, cmdline="python %s/entry.py" % PLUGIN_MARKER, token="1.0")
        leaf = _record(11, ppid=10, cmdline="bash.exe -c work", token="2.0")
        spec, marker, via_pid, outcome = attribution_mod._walk_ancestry(
            leaf,
            _plugin_registry(),
            {10: baseline},
            12,
            components.ROLE_PLUGIN_COUNTED,
            {10},
        )
        assert outcome == attribution_mod.WALK_MATCHED
        assert spec.key == components.KEY_PLUGIN
        assert via_pid == 10

    def test_a_clean_baseline_still_terminates_the_walk(self):
        """Paired half: the check must still fire when no marker matched."""
        baseline = _record(10, ppid=None, cmdline="explorer.exe", token="1.0")
        leaf = _record(11, ppid=10, cmdline="bash.exe -c work", token="2.0")
        _, _, _, outcome = attribution_mod._walk_ancestry(
            leaf,
            _plugin_registry(),
            {10: baseline},
            12,
            components.ROLE_PLUGIN_COUNTED,
            {10},
        )
        assert outcome == attribution_mod.WALK_REACHED_BASELINE


class TestAnUnreadableProcessIsNeverProved:
    """The proof covers ancestry, so it cannot cover the process's own identity.

    A process observed with no command line and no executable path might BE the plugin.
    Granting it a clean-ancestry proof turns a momentary failure to read into a finding
    of innocence -- and that is not hypothetical: the shipped self-test, which spawns a
    marked child and requires FAIL, returned PASS once with exactly this shape.
    """

    def test_a_process_with_no_cmdline_or_exe_is_unknown_despite_clean_ancestry(self):
        baseline = _record(10, ppid=None, cmdline="explorer.exe", token="1.0")
        blank = _record(11, ppid=10, name="python.exe", cmdline=None, token="2.0")
        attribution = _attribute(blank, {10: baseline}, {10})
        assert attribution.component_key == attribution_mod.UNATTRIBUTED_KEY

    def test_the_same_process_with_a_readable_cmdline_is_proved(self):
        """Paired half: the guard must key on readability, not reject everything."""
        baseline = _record(10, ppid=None, cmdline="explorer.exe", token="1.0")
        readable = _record(11, ppid=10, name="python.exe", cmdline="python.exe -c pass", token="2.0")
        attribution = _attribute(readable, {10: baseline}, {10})
        assert attribution.component_key == attribution_mod.NOT_PLUGIN_DESCENDED_KEY

    def test_an_exe_path_alone_is_enough_identity(self):
        baseline = _record(10, ppid=None, cmdline="explorer.exe", token="1.0")
        record = process_probe.ProcessRecord(
            pid=11,
            ppid=10,
            name="python.exe",
            exe="C:/tools/python.exe",
            cmdline=None,
            create_token="2.0",
        )
        attribution = _attribute(record, {10: baseline}, {10})
        assert attribution.component_key == attribution_mod.NOT_PLUGIN_DESCENDED_KEY

    def test_an_image_name_alone_is_not_enough_identity(self):
        """A plugin entry point runs as python.exe too; the marker lives in the cmdline."""
        assert attribution_mod.identity_is_readable(_record(11, ppid=10, name="python.exe", cmdline=None)) is False

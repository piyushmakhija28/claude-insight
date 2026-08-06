"""Tests for the NFR-1 per-component process-count harness (issue V2-003).

Every check the harness performs has a companion negative test here that drives it to
failure. A check never observed failing is indistinguishable from a no-op, and this
project has already shipped a validator that claimed to check fourteen sections while
actually checking three. The negative tests are the evidence that this harness is not
that.

The strongest of them, test_real_spawn_is_detected_and_fails, does not use a mock. It
spawns a genuine child process on the live operating system and requires the harness to
observe it, attribute it to the plugin-counted role, and return FAIL. A harness that
cannot fail that test has not been shown to detect anything at all.
"""

import json
import os
import subprocess
import sys

import pytest

# The harness package is imported as top-level ``nfr1`` rather than ``tests.nfr1``
# because an unrelated ``tests`` distribution is installed in this environment's
# site-packages. Python's finder returns the first REGULAR package it meets while
# scanning sys.path and only falls back to namespace portions when none exists
# anywhere, so the installed package wins over the repository directory regardless of
# path order, and ``tests.nfr1`` is unresolvable. Adding tests/__init__.py would fix
# the shadowing but would rename every existing test module in the suite.
_TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
if _TESTS_DIR not in sys.path:
    sys.path.insert(0, _TESTS_DIR)

from nfr1 import attribution as attribution_mod  # noqa: E402
from nfr1 import components, harness, plugin_gate, process_probe  # noqa: E402

pytestmark = pytest.mark.unit

MARKER = "nfr1_pytest_marker_process"


def _record(pid, ppid=None, name="python.exe", cmdline="python.exe", token="1.0", denied=False):
    """Build a synthetic ProcessRecord for attribution tests."""
    return process_probe.ProcessRecord(
        pid=pid,
        ppid=ppid,
        name=name,
        exe=None,
        cmdline=cmdline,
        create_token=token,
        access_denied=denied,
    )


def _plugin_registry(markers=("plugin_marker",)):
    """Build a two-component registry: one plugin-counted, one permitted exclusion."""
    registry = components.ComponentRegistry()
    registry.register(
        components.ComponentSpec(
            key=components.KEY_PLUGIN,
            role=components.ROLE_PLUGIN_COUNTED,
            markers=list(markers),
        )
    )
    registry.register(
        components.ComponentSpec(
            key=components.KEY_RETAINED_USER_HOOKS,
            role=components.ROLE_PERMITTED_EXCLUSION,
            markers=["stop_notifier"],
            justification="ADR-010",
        )
    )
    return registry


class TestComponentRegistry:
    """The exclusion cardinality that keeps NFR-1 falsifiable."""

    def test_default_registry_uses_exactly_one_exclusion(self):
        registry = components.build_default_registry(plugin_root=None)
        excluded = registry.keys_with_role(components.ROLE_PERMITTED_EXCLUSION)
        assert excluded == [components.KEY_RETAINED_USER_HOOKS]
        assert len(excluded) == components.MAX_PERMITTED_EXCLUSIONS

    def test_default_registry_still_defines_the_plugin_when_no_plugin_exists(self):
        registry = components.build_default_registry(plugin_root=None)
        plugin = registry.get(components.KEY_PLUGIN)
        assert plugin is not None
        assert plugin.role == components.ROLE_PLUGIN_COUNTED
        assert plugin.markers, "an empty marker set would make the plugin unfailable"

    def test_negative_second_exclusion_is_refused(self):
        registry = components.build_default_registry(plugin_root=None)
        with pytest.raises(components.ExclusionPolicyError):
            registry.register(
                components.ComponentSpec(
                    key="some_other_thing",
                    role=components.ROLE_PERMITTED_EXCLUSION,
                    markers=["whatever"],
                    justification="convenience",
                )
            )

    def test_negative_exclusion_without_justification_is_refused(self):
        with pytest.raises(ValueError):
            components.ComponentSpec(key="x", role=components.ROLE_PERMITTED_EXCLUSION, markers=["y"])

    def test_negative_duplicate_key_is_refused(self):
        registry = _plugin_registry()
        with pytest.raises(ValueError):
            registry.register(
                components.ComponentSpec(
                    key=components.KEY_PLUGIN,
                    role=components.ROLE_OBSERVED,
                    markers=["z"],
                )
            )


class TestAttribution:
    """Per-component attribution, which is what NFR-1 actually measures."""

    def test_direct_attribution_to_plugin(self):
        registry = _plugin_registry()
        result = attribution_mod.attribute([_record(10, cmdline="run plugin_marker go")], registry)
        assert result.plugin_count == 1
        assert result.attributions[0].basis == attribution_mod.BASIS_DIRECT

    def test_ancestry_attribution_charges_the_launcher(self):
        registry = _plugin_registry()
        parent = _record(100, cmdline="python plugin_marker/entry.py")
        child = _record(101, ppid=100, name="git.exe", cmdline="git rev-parse HEAD")
        result = attribution_mod.attribute([child], registry, {100: parent})
        assert result.plugin_count == 1
        assert result.attributions[0].basis == attribution_mod.BASIS_ANCESTRY
        assert result.attributions[0].via_pid == 100

    def test_stop_hook_process_is_excluded_not_counted(self):
        registry = _plugin_registry()
        record = _record(20, cmdline="python hooks/stop_notifier/core.py")
        result = attribution_mod.attribute([record], registry)
        assert result.plugin_count == 0
        assert result.excluded_count == 1

    def test_negative_unattributed_process_is_reported_not_dropped(self):
        registry = _plugin_registry()
        record = _record(30, name="unknown.exe", cmdline="unknown.exe --do-things")
        result = attribution_mod.attribute([record], registry)
        assert result.plugin_count == 0
        assert len(result.unattributed) == 1
        assert result.to_dict()["unattributed_processes"], "must be listed in the report"

    def test_negative_access_denied_process_is_unattributed_with_a_reason(self):
        registry = _plugin_registry()
        record = _record(31, name="", cmdline=None, denied=True)
        result = attribution_mod.attribute([record], registry)
        assert len(result.unattributed) == 1
        assert "withheld" in result.unattributed[0].reason

    def test_negative_ancestry_cycle_terminates(self):
        registry = _plugin_registry()
        a = _record(1, ppid=2, name="a.exe", cmdline="a.exe")
        b = _record(2, ppid=1, name="b.exe", cmdline="b.exe")
        result = attribution_mod.attribute([a], registry, {1: a, 2: b})
        assert len(result.unattributed) == 1


class TestPluginGate:
    """Acceptance criterion 6, which decides independently of any process count."""

    def test_absent_plugin_root_is_not_measurable_never_pass(self, tmp_path):
        result = plugin_gate.check_mcp_manifest(str(tmp_path / "nope"))
        assert result.status == plugin_gate.STATUS_NOT_MEASURABLE
        assert result.status != plugin_gate.STATUS_PASS

    def test_no_manifest_passes(self, tmp_path):
        result = plugin_gate.check_mcp_manifest(str(tmp_path))
        assert result.status == plugin_gate.STATUS_PASS

    def test_negative_manifest_with_a_server_entry_fails(self, tmp_path):
        (tmp_path / ".mcp.json").write_text(
            json.dumps({"mcpServers": {"push-gate": {"command": "python"}}}), encoding="utf-8"
        )
        result = plugin_gate.check_mcp_manifest(str(tmp_path))
        assert result.status == plugin_gate.STATUS_FAIL
        assert result.evidence["server_names"] == ["push-gate"]

    def test_negative_empty_manifest_warns_on_the_gherkin_discrepancy(self, tmp_path):
        (tmp_path / ".mcp.json").write_text(json.dumps({"mcpServers": {}}), encoding="utf-8")
        result = plugin_gate.check_mcp_manifest(str(tmp_path))
        assert result.status == plugin_gate.STATUS_WARN
        assert "Gherkin" in result.detail

    def test_negative_unparsable_manifest_fails_closed(self, tmp_path):
        (tmp_path / ".mcp.json").write_text("{ not json", encoding="utf-8")
        result = plugin_gate.check_mcp_manifest(str(tmp_path))
        assert result.status == plugin_gate.STATUS_FAIL

    def test_negative_bundled_hooks_fail_adr010(self, tmp_path):
        (tmp_path / "hooks").mkdir()
        result = plugin_gate.check_no_bundled_hooks(str(tmp_path))
        assert result.status == plugin_gate.STATUS_FAIL
        assert result.evidence["auxiliary"] is True

    def test_negative_hooks_json_anywhere_fails_adr010(self, tmp_path):
        nested = tmp_path / "commands"
        nested.mkdir()
        (nested / "hooks.json").write_text("{}", encoding="utf-8")
        result = plugin_gate.check_no_bundled_hooks(str(tmp_path))
        assert result.status == plugin_gate.STATUS_FAIL


class TestTurnBoundaryGuard:
    """Acceptance criterion 4, and the distinction between INVALID and FAIL."""

    def test_clean_window_does_not_cross(self, tmp_path):
        guard = harness.TurnBoundaryGuard(str(tmp_path / "absent.log"))
        guard.open()
        assert guard.evaluate()["crossed"] is False

    def test_negative_stop_log_growth_invalidates_the_window(self, tmp_path):
        log = tmp_path / "stop-notifier.log"
        log.write_text("a", encoding="utf-8")
        guard = harness.TurnBoundaryGuard(str(log))
        guard.open()
        log.write_text("a much longer line than before", encoding="utf-8")
        outcome = guard.evaluate()
        assert outcome["crossed"] is True
        assert "INVALID" in outcome["effect"]

    def test_negative_excluded_process_in_window_invalidates(self, tmp_path):
        guard = harness.TurnBoundaryGuard(str(tmp_path / "absent.log"))
        guard.open()
        registry = _plugin_registry()
        result = attribution_mod.attribute([_record(40, cmdline="python hooks/stop_notifier/core.py")], registry)
        assert guard.evaluate(result)["crossed"] is True

    def test_negative_declared_boundary_invalidates(self, tmp_path):
        guard = harness.TurnBoundaryGuard(str(tmp_path / "absent.log"))
        guard.open()
        guard.note_turn_boundary("driver observed a response turn")
        assert guard.evaluate()["crossed"] is True

    def test_absent_log_witness_does_not_claim_evidence_of_no_boundary(self, tmp_path):
        guard = harness.TurnBoundaryGuard(str(tmp_path / "absent.log"))
        guard.open()
        log_witness = guard.evaluate()["witnesses"][0]
        assert log_witness["fired"] is False
        assert "must not be read as evidence" in log_witness["note"]


def _measurement(plugin_count=0, unattributed=0, tool_calls=harness.REQUIRED_TOOL_CALLS, crossed=False):
    """Build a Measurement from synthetic attribution for verdict tests."""
    registry = _plugin_registry()
    records = [_record(200 + i, cmdline="plugin_marker w") for i in range(plugin_count)]
    records += [_record(300 + i, name="x.exe", cmdline="x.exe") for i in range(unattributed)]
    result = attribution_mod.attribute(records, registry)
    return harness.Measurement(
        phase=harness.PHASE_COLD,
        tool_calls=tool_calls,
        endpoint_attribution=result,
        sampled_attribution=result,
        union_attribution=result,
        turn_boundary={"crossed": crossed, "witnesses": [], "effect": ""},
        probe_summary={},
    )


class TestVerdict:
    """Acceptance criteria 1, 2 and 5."""

    def test_clean_measurement_passes(self):
        verdict, _ = _measurement().verdict()
        assert verdict == harness.VERDICT_PASS

    def test_negative_one_plugin_process_fails(self):
        verdict, reasons = _measurement(plugin_count=1).verdict()
        assert verdict == harness.VERDICT_FAIL
        assert "attributable to the plugin" in reasons[0]

    def test_negative_unattributed_process_is_indeterminate_not_pass(self):
        verdict, _ = _measurement(unattributed=1).verdict()
        assert verdict == harness.VERDICT_INDETERMINATE

    def test_negative_wrong_tool_call_count_is_indeterminate(self):
        verdict, reasons = _measurement(tool_calls=9).verdict()
        assert verdict == harness.VERDICT_INDETERMINATE
        assert "exactly 10 tool calls" in reasons[0]

    def test_negative_crossed_boundary_is_indeterminate_not_fail(self):
        verdict, _ = _measurement(crossed=True).verdict()
        assert verdict == harness.VERDICT_INDETERMINATE
        assert verdict != harness.VERDICT_FAIL

    def test_negative_missing_warm_phase_blocks_a_pass(self, tmp_path):
        report = harness.NFR1Report(
            structural={"overall": plugin_gate.STATUS_PASS, "gates": []},
            cold=_measurement(),
            warm=None,
        )
        verdict, reasons = report.overall_verdict()
        assert verdict == harness.VERDICT_INDETERMINATE
        assert "warm" in " ".join(reasons)

    def test_report_exposes_no_blended_figure(self):
        report = harness.NFR1Report(
            structural={"overall": plugin_gate.STATUS_PASS, "gates": []},
            cold=_measurement(),
            warm=_measurement(),
        )
        payload = report.to_dict()
        assert payload["cold"] is not None and payload["warm"] is not None
        for banned in ("combined", "average", "mean", "blended_count", "total_delta"):
            assert banned not in payload

    def test_negative_structural_failure_overrides_a_clean_count(self, tmp_path):
        (tmp_path / ".mcp.json").write_text(json.dumps({"mcpServers": {"s": {}}}), encoding="utf-8")
        report = harness.build_report(plugin_root=str(tmp_path), cold=_measurement(), warm=_measurement())
        verdict, reasons = report.overall_verdict()
        assert verdict == harness.VERDICT_FAIL
        assert "regardless of the process count" in reasons[0]


class TestCurrentTreeState:
    """The harness must refuse to pass against the tree as it stands today."""

    def test_no_plugin_exists_yet(self):
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        assert not os.path.exists(os.path.join(root, ".mcp.json"))
        assert not os.path.exists(os.path.join(root, "plugin.json"))

    def test_report_against_current_tree_is_not_measurable(self):
        report = harness.build_report(plugin_root=None, cold=None, warm=None)
        verdict, _ = report.overall_verdict()
        assert verdict == harness.VERDICT_NOT_MEASURABLE
        assert verdict != harness.VERDICT_PASS

    def test_report_records_the_closes_after_gate(self):
        payload = harness.build_report(plugin_root=None).to_dict()
        assert payload["closes_after"] == ["V2-015", "V2-027"]

    def test_the_closure_note_carries_both_the_original_bar_and_the_amendment(self):
        """The bar that was not met must survive the decision that waived it.

        #259 was closed without a PASS. That was the owner's ruling, and it is
        defensible -- but a note rewritten to read as though the bar had been
        cleared would erase the one fact a later reader most needs. So both halves
        are pinned: what was originally required, and what was decided instead.
        """
        note = harness.build_report(plugin_root=None).to_dict()["closure_note"]
        assert "ORIGINAL BAR" in note
        assert "never produced a pass" in note
        assert "AMENDED 2026-08-06" in note
        assert "A PASS was NOT produced" in note

    def test_the_amendment_names_where_its_evidence_lives(self):
        """A ruling with no reachable evidence is an assertion."""
        note = harness.build_report(plugin_root=None).to_dict()["closure_note"]
        assert "docs/reports/nfr1-measurement-2026-08-06.md" in note


class TestStopHookSpawnFloor:
    """The owner ruling that an inert guarded opportunity is a pass."""

    def test_four_opportunities_are_described(self):
        floor = components.describe_stop_hook_spawn_floor()
        assert floor["expected_opportunity_count"] == 4
        assert floor["observed_opportunity_count"] == 4

    def test_two_unconditional_and_two_guarded(self):
        floor = components.describe_stop_hook_spawn_floor()
        kinds = [o["kind"] for o in floor["opportunities"]]
        assert kinds.count("unconditional") == 2
        assert kinds.count("guarded") == 2

    def test_inert_guarded_opportunity_is_a_pass_not_a_failure(self):
        floor = components.describe_stop_hook_spawn_floor()
        assert floor["inert_is_a_pass"] is True
        for opportunity in floor["opportunities"]:
            if opportunity["state"] == "inert":
                assert "PASS" in opportunity["verdict_effect"]

    def test_sync_version_target_resolves_to_a_missing_sibling(self):
        floor = components.describe_stop_hook_spawn_floor()
        site = [o for o in floor["opportunities"] if o["site"].endswith("post_impl.py:286")][0]
        assert site["resolved_target"].replace("\\", "/").endswith("hooks/stop_notifier/sync-version.py")
        assert site["state"] == "inert"

    def test_voice_target_resolves_under_home_not_as_a_sibling(self):
        floor = components.describe_stop_hook_spawn_floor()
        site = [o for o in floor["opportunities"] if o["site"].endswith("voice.py:164")][0]
        resolved = site["resolved_target"].replace("\\", "/")
        assert not resolved.endswith("hooks/stop_notifier/voice-notifier.py"), (
            "helpers.py:142 resolves CURRENT_DIR, which is under the user home "
            "directory, not a sibling of helpers.py"
        )
        assert "/.claude/" in resolved


class TestProcessProbe:
    """Windows-native enumeration, and the endpoint diff's known blind spot."""

    def test_psutil_backend_is_available(self):
        assert process_probe.psutil_available()

    def test_snapshot_finds_this_process(self):
        snapshot = process_probe.take_snapshot(process_probe.BACKEND_PSUTIL)
        assert any(r.pid == os.getpid() for r in snapshot.records.values())

    def test_psutil_backend_is_not_perturbing(self):
        snapshot = process_probe.take_snapshot(process_probe.BACKEND_PSUTIL)
        assert snapshot.is_perturbing is False

    def test_identity_key_survives_pid_reuse(self):
        first = _record(500, token="1.0")
        second = _record(500, token="2.0")
        assert first.key != second.key

    def test_negative_unknown_backend_raises(self):
        with pytest.raises(process_probe.ProbeError):
            process_probe.take_snapshot("not-a-backend")

    @pytest.mark.skipif(not sys.platform.startswith("win"), reason="Windows-only backend")
    def test_powershell_cim_backend_works_on_windows(self):
        snapshot = process_probe.take_snapshot(process_probe.BACKEND_POWERSHELL_CIM)
        assert len(snapshot.records) > 0
        assert snapshot.is_perturbing is True


class TestRealSpawnDetection:
    """The proof that the harness is not a no-op, using a real operating-system spawn."""

    def test_real_spawn_is_detected_and_fails(self):
        registry = components.ComponentRegistry()
        registry.register(
            components.ComponentSpec(
                key=components.KEY_PLUGIN,
                role=components.ROLE_PLUGIN_COUNTED,
                markers=[MARKER],
            )
        )
        session = harness.MeasurementSession(
            phase=harness.PHASE_COLD,
            registry=registry,
            sample_interval_seconds=0.03,
            stop_log_path=os.devnull,
        )
        children = []

        def one_tool_call():
            """Stand in for one tool call, spawning the marked child on the first.

            The child announces itself on stdout and is not left to race the
            measurement window. ``Popen`` returns before the operating system
            has necessarily made the process enumerable, and this window is only
            as long as ten near-empty tool calls take -- so on a loaded machine
            the window could close before the child became visible, and the
            harness would be blamed for missing a spawn that had not happened
            yet. Blocking on the first byte makes the child's existence a
            precondition of the measurement rather than a race against it.
            """
            if not children:
                child = subprocess.Popen(
                    [
                        sys.executable,
                        "-c",
                        "import sys, time; sys.stdout.write('r'); sys.stdout.flush(); "
                        "time.sleep(300)  # %s" % MARKER,
                    ],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                )
                children.append(child)
                assert child.stdout.read(1) == b"r", "marked child never started"

        measurement = session.run_driven(one_tool_call, harness.REQUIRED_TOOL_CALLS)
        for child in children:
            child.terminate()
            child.wait(timeout=15)
            child.stdout.close()

        verdict, reasons = measurement.verdict()
        assert (
            measurement.authoritative_attribution.plugin_count >= 1
        ), "harness failed to observe a real spawn it was configured to detect; " "reasons=%r" % (reasons,)
        assert verdict == harness.VERDICT_FAIL

    def test_empty_sampled_delta_must_not_mask_the_endpoint_delta(self):
        """Regression guard for the defect the real-spawn test originally exposed.

        The first revision of this harness treated the sampled delta as authoritative
        outright. When the measurement window closed before the sampler thread was
        first scheduled, the sampled delta was empty, it replaced a correctly detected
        endpoint delta, and the verdict came back PASS on a real spawn. The verdict now
        reads a union, so an empty sampled delta cannot subtract an observation.
        """
        registry = _plugin_registry()
        detected = attribution_mod.attribute([_record(900, cmdline="plugin_marker running")], registry)
        empty = attribution_mod.attribute([], registry)
        measurement = harness.Measurement(
            phase=harness.PHASE_COLD,
            tool_calls=harness.REQUIRED_TOOL_CALLS,
            endpoint_attribution=detected,
            sampled_attribution=empty,
            union_attribution=detected,
            turn_boundary={"crossed": False, "witnesses": [], "effect": ""},
            probe_summary={},
        )
        assert measurement.sampled_attribution.plugin_count == 0
        assert measurement.authoritative_attribution.plugin_count == 1
        assert measurement.verdict()[0] == harness.VERDICT_FAIL

    def test_no_spawn_yields_no_plugin_attribution(self):
        registry = components.ComponentRegistry()
        registry.register(
            components.ComponentSpec(
                key=components.KEY_PLUGIN,
                role=components.ROLE_PLUGIN_COUNTED,
                markers=["marker_that_no_process_carries_zzz"],
            )
        )
        session = harness.MeasurementSession(
            phase=harness.PHASE_WARM,
            registry=registry,
            sample_interval_seconds=0.03,
            stop_log_path=os.devnull,
        )
        measurement = session.run_driven(lambda: None, harness.REQUIRED_TOOL_CALLS)
        assert measurement.authoritative_attribution.plugin_count == 0

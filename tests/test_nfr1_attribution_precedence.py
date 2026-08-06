"""Regression tests for plugin-first attribution precedence (issue V2-003 follow-up).

Before this change, ``attribution.attribute()`` resolved the FIRST matching component
in registry order against a process's own command line, and only walked the ancestor
chain when nothing matched directly. That let a broad marker on a low-priority,
uncapped OBSERVED component swallow a plugin-spawned child before the ancestry walk
that would otherwise have charged it to the plugin ever ran: a bash.exe spawned by the
plugin, whose own command line names only the shell, would direct-match an OBSERVED
component declaring "bash.exe" and never reach the ancestor that carried the plugin's
marker. NFR-1 would then report zero plugin-attributable processes while a plugin
process ran unobserved, through a role that carries no exclusion cap and needs no
justification -- exactly the failure MAX_PERMITTED_EXCLUSIONS = 1 exists to prevent, by
a different door.

Test (a) below is the load-bearing proof. It is written so it FAILS against the
attribution module as it stood before the plugin-first precedence fix, and the failure
was captured before the fix landed (see the task report for the captured output). A
positive-only test suite cannot show that; only a test with a known failing baseline can.
"""

import concurrent.futures
import os
import sys

import pytest

_TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
if _TESTS_DIR not in sys.path:
    sys.path.insert(0, _TESTS_DIR)

from nfr1 import attribution as attribution_mod  # noqa: E402
from nfr1 import components, process_probe  # noqa: E402

pytestmark = pytest.mark.unit

BARE_EXE_NAMES = ("bash.exe", "sh.exe", "cmd.exe", "node.exe", "conhost.exe")


def _record(pid, ppid=None, name="python.exe", cmdline="python.exe", token="1.0", denied=False):
    """Build a synthetic ProcessRecord for attribution tests.

    Mirrors the helper of the same name in tests/test_nfr1_harness.py; duplicated here
    rather than imported so this file stays self-contained and does not couple its
    fixtures to another test module's internals.
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


def _registry_with_broad_observed_marker():
    """Build a registry reproducing the exact shape of the swallowing defect.

    One PLUGIN_COUNTED component with a specific marker, and one OBSERVED component
    carrying a marker as broad as a bare shell executable name -- the shape Part 2 of
    this change was told never to add to the real default registry, reproduced here
    on purpose so the precedence fix can be proven against it.
    """
    registry = components.ComponentRegistry()
    registry.register(
        components.ComponentSpec(
            key=components.KEY_PLUGIN,
            role=components.ROLE_PLUGIN_COUNTED,
            markers=["plugin_marker"],
        )
    )
    registry.register(
        components.ComponentSpec(
            key="broad_observed",
            role=components.ROLE_OBSERVED,
            markers=["bash.exe"],
        )
    )
    return registry


def _plugin_only_registry(marker="plugin_marker"):
    """Build a registry containing only the plugin component.

    Used by tests that want to exercise ancestry-walk mechanics (depth, cycles,
    broken chains) without an OBSERVED component's fallback match masking the result
    under test.
    """
    registry = components.ComponentRegistry()
    registry.register(
        components.ComponentSpec(
            key=components.KEY_PLUGIN,
            role=components.ROLE_PLUGIN_COUNTED,
            markers=[marker],
        )
    )
    return registry


def _build_ancestor_chain(depth, plugin_marker_at_hop=None, base_pid=9000, marker="plugin_marker"):
    """Build a synthetic straight-line ancestor chain of the given depth.

    Hop 1 is the leaf's immediate parent; hop `depth` is the topmost ancestor built,
    whose ppid is None. When plugin_marker_at_hop is given, that hop's record carries
    `marker` in its command line; every other hop carries an inert command line that
    matches nothing.

    Args:
        depth: How many ancestor hops to build above the leaf.
        plugin_marker_at_hop: 1-based hop number that should carry the marker, or
            None for a chain with no marker anywhere.
        base_pid: Starting pid; the leaf uses base_pid, hop N uses base_pid + N.
        marker: Marker text to embed at plugin_marker_at_hop.

    Returns:
        Tuple of (leaf ProcessRecord, ancestry index dict keyed by pid).
    """
    index = {}
    for hop in range(1, depth + 1):
        pid = base_pid + hop
        parent_pid = base_pid + hop + 1 if hop < depth else None
        cmdline = "host.exe %s" % marker if hop == plugin_marker_at_hop else "host.exe inert"
        index[pid] = _record(pid, ppid=parent_pid, name="host.exe", cmdline=cmdline)
    leaf = _record(base_pid, ppid=base_pid + 1, name="bash.exe", cmdline="bash.exe -c inert")
    return leaf, index


class TestPluginFirstPrecedence:
    """Proof that plugin attribution is resolved before any other component's match."""

    def test_plugin_ancestry_wins_over_broader_observed_direct_match(self):
        """The load-bearing test: see the module docstring.

        A bash.exe child carries no plugin marker in its own command line, only its
        parent does. An OBSERVED component in this registry declares the bare marker
        "bash.exe", which without plugin-first precedence direct-matches the child
        before its ancestry is ever walked. The correct outcome is that the plugin's
        ancestry match wins and the process is charged to the plugin.
        """
        registry = _registry_with_broad_observed_marker()
        parent = _record(100, cmdline="python plugin_marker/entry.py")
        child = _record(101, ppid=100, name="bash.exe", cmdline="bash.exe -c do_a_thing")
        result = attribution_mod.attribute([child], registry, {100: parent})

        assert result.plugin_count == 1, (
            "the plugin-spawned child was swallowed by the broader OBSERVED marker "
            "instead of being charged to the plugin via ancestry"
        )
        attribution = result.attributions[0]
        assert attribution.component_key == components.KEY_PLUGIN
        assert attribution.basis == attribution_mod.BASIS_ANCESTRY
        assert attribution.via_pid == 100

    def test_observed_marker_without_plugin_ancestor_stays_observed(self):
        """The paired specificity half: an unrelated bash.exe is not swept into the plugin.

        Without this test, a broken implementation that attributed every process to
        the plugin unconditionally would make test (a) above pass for the wrong
        reason. A process matching only the OBSERVED marker, with no plugin marker
        anywhere in its ancestry, must be attributed to that OBSERVED component.
        """
        registry = _registry_with_broad_observed_marker()
        lone = _record(200, ppid=None, name="bash.exe", cmdline="bash.exe -c unrelated")
        result = attribution_mod.attribute([lone], registry)

        assert result.plugin_count == 0
        attribution = result.attributions[0]
        assert attribution.component_key == "broad_observed"
        assert attribution.basis == attribution_mod.BASIS_DIRECT

    def test_plugin_direct_match_still_wins_even_with_a_broad_observed_marker_registered(self):
        """A process that IS the plugin is still attributed directly, precedence intact."""
        registry = _registry_with_broad_observed_marker()
        direct = _record(300, name="bash.exe", cmdline="bash.exe plugin_marker inline")
        result = attribution_mod.attribute([direct], registry)

        assert result.plugin_count == 1
        assert result.attributions[0].basis == attribution_mod.BASIS_DIRECT
        assert result.attributions[0].component_key == components.KEY_PLUGIN

    def test_ancestry_cycle_guard_still_terminates_under_plugin_first_walk(self):
        """The plugin-first ancestry walk reuses the same cycle guard as the fallback.

        A two-node parent cycle that carries no plugin marker anywhere must still
        terminate and fall through to the ordinary fallback search, not loop forever.
        """
        registry = _registry_with_broad_observed_marker()
        a = _record(1, ppid=2, name="a.exe", cmdline="a.exe")
        b = _record(2, ppid=1, name="b.exe", cmdline="b.exe")
        result = attribution_mod.attribute([a], registry, {1: a, 2: b})

        assert len(result.unattributed) == 1


class TestNewObservedMarkersAreSpecific:
    """Part 2's hard constraint: no new OBSERVED marker is a bare shell/tool name."""

    def test_new_observed_markers_are_specific_not_bare_exe_names(self):
        registry = components.build_default_registry(plugin_root=None)
        new_keys = (components.KEY_STATUSLINE_HOOK, components.KEY_CLAUDE_CODE_HOST)

        for key in new_keys:
            spec = registry.get(key)
            assert spec is not None, "expected component %r to be registered" % key
            assert spec.role == components.ROLE_OBSERVED, "%r must be OBSERVED, not a new exclusion" % key
            assert spec.markers, "%r must carry at least one marker to be reachable at all" % key
            for marker in spec.markers:
                for bare in BARE_EXE_NAMES:
                    assert marker != bare, "marker %r for %r equals the bare exe name %r" % (marker, key, bare)
                    assert bare not in marker, "marker %r for %r contains the bare exe name %r as a substring" % (
                        marker,
                        key,
                        bare,
                    )
                    assert marker not in bare, "marker %r for %r is itself a substring of the bare exe name %r" % (
                        marker,
                        key,
                        bare,
                    )

    def test_no_new_component_claims_the_permitted_exclusion_role(self):
        """Part 2 explicitly forbids widening the single permitted exclusion."""
        registry = components.build_default_registry(plugin_root=None)
        excluded = registry.keys_with_role(components.ROLE_PERMITTED_EXCLUSION)
        assert excluded == [components.KEY_RETAINED_USER_HOOKS]
        assert len(excluded) == components.MAX_PERMITTED_EXCLUSIONS

    def test_claude_code_host_component_reached_only_by_ancestry_for_generic_children(self):
        """The console-host/shell class is identified by ancestry, never by its own name.

        A bash.exe with no plugin marker anywhere and a claude.exe ancestor must land
        on claude_code_host via BASIS_ANCESTRY, not via a direct marker on the child.
        """
        registry = components.build_default_registry(plugin_root=None)
        host = _record(400, name="claude.exe", cmdline=r"C:\Users\techd\.local\bin\claude.exe --flag")
        child = _record(401, ppid=400, name="bash.exe", cmdline="bash.exe -c ls")
        result = attribution_mod.attribute([child], registry, {400: host})

        attribution = result.attributions[0]
        assert attribution.component_key == components.KEY_CLAUDE_CODE_HOST
        assert attribution.basis == attribution_mod.BASIS_ANCESTRY
        assert attribution.via_pid == 400

    def test_statusline_script_direct_matches_its_own_specific_component(self):
        """The statusline hook is identified by its own script name, not by ancestry."""
        registry = components.build_default_registry(plugin_root=None)
        record = _record(
            500,
            name="bash.exe",
            cmdline=r"C:\Program Files\Git\usr\bin\bash.exe /c/Users/techd/.claude/statusline-command.sh",
        )
        result = attribution_mod.attribute([record], registry)

        attribution = result.attributions[0]
        assert attribution.component_key == components.KEY_STATUSLINE_HOOK
        assert attribution.basis == attribution_mod.BASIS_DIRECT


class TestAccessDeniedStillIndeterminate:
    """Part 3d: access_denied processes remain unattributed and force INDETERMINATE."""

    def test_access_denied_process_is_reported_unattributed_with_a_reason(self):
        registry = _registry_with_broad_observed_marker()
        denied = _record(600, name="", cmdline=None, denied=True)
        result = attribution_mod.attribute([denied], registry)

        assert len(result.unattributed) == 1
        attribution = result.unattributed[0]
        assert attribution.basis == attribution_mod.BASIS_NONE
        assert "withheld" in attribution.reason

    def test_access_denied_process_with_a_plugin_ancestor_is_still_unattributed(self):
        """Plugin-first precedence walks the ancestry index, but an access-denied child
        never resolves an ancestor chain of its own here because it has no ppid on
        record (the OS withheld it); it must not be silently attributed to anything.
        """
        registry = _registry_with_broad_observed_marker()
        denied = _record(601, ppid=None, name="", cmdline=None, denied=True)
        result = attribution_mod.attribute([denied], registry)

        assert len(result.unattributed) == 1
        assert result.plugin_count == 0

    def test_access_denied_process_forces_indeterminate_verdict_not_pass(self):
        """End-to-end: an access-denied process in a measurement must not yield PASS."""
        from nfr1 import harness

        registry = _registry_with_broad_observed_marker()
        denied = _record(700, name="", cmdline=None, denied=True)
        result = attribution_mod.attribute([denied], registry)
        measurement = harness.Measurement(
            phase=harness.PHASE_COLD,
            tool_calls=harness.REQUIRED_TOOL_CALLS,
            endpoint_attribution=result,
            sampled_attribution=result,
            union_attribution=result,
            turn_boundary={"crossed": False, "witnesses": [], "effect": ""},
            probe_summary={},
        )
        verdict, reasons = measurement.verdict()
        assert verdict == harness.VERDICT_INDETERMINATE
        assert verdict != harness.VERDICT_PASS
        assert "could not be attributed" in reasons[0]


class TestAdversarialRegistrationOrder:
    """Closes a concrete mutation-testing gap in the plugin-first precedence proof.

    A mutation run over attribute() against the tests that existed before this class
    showed neutering the plugin-first ANCESTRY walk and neutering the role filter
    were both CAUGHT, but neutering the plugin-first DIRECT match SURVIVED: every
    existing test still passed. The reason is that build_default_registry() and every
    helper registry elsewhere in this file register the plugin FIRST, so the
    pre-existing first-match-wins _direct_match() finds the plugin anyway even with
    plugin-first precedence deleted. Only a registry where a role-agnostic scan would
    reach a different component before the plugin can distinguish "plugin-first
    precedence exists" from "the plugin happens to be first in this registry".
    """

    def _registry_with_observed_registered_before_plugin(self):
        """Register OBSERVED first so a first-match-wins scan would find it, not the
        plugin, unless genuine role-restricted precedence intervenes.
        """
        registry = components.ComponentRegistry()
        registry.register(
            components.ComponentSpec(
                key="early_observed",
                role=components.ROLE_OBSERVED,
                markers=["shared_signature"],
            )
        )
        registry.register(
            components.ComponentSpec(
                key=components.KEY_PLUGIN,
                role=components.ROLE_PLUGIN_COUNTED,
                markers=["shared_signature"],
            )
        )
        return registry

    def test_plugin_direct_match_wins_when_observed_is_registered_first(self):
        """The load-bearing proof: registration order must not decide this outcome.

        Both components carry the marker "shared_signature", and OBSERVED is
        registered first. A plain first-match-wins scan (no plugin-first precedence)
        would return the OBSERVED component. Only genuine plugin-first precedence
        returns the plugin.
        """
        registry = self._registry_with_observed_registered_before_plugin()
        record = _record(900, name="python.exe", cmdline="python.exe shared_signature")

        result = attribution_mod.attribute([record], registry)

        assert result.plugin_count == 1, (
            "the plugin was not attributed even though its own marker matched "
            "directly; registration order overrode plugin-first precedence"
        )
        attribution = result.attributions[0]
        assert attribution.component_key == components.KEY_PLUGIN
        assert attribution.basis == attribution_mod.BASIS_DIRECT

    def test_observed_still_wins_when_only_it_matches_even_with_this_registry_shape(self):
        """Paired specificity half: with OBSERVED registered first, a process that
        matches only OBSERVED (no plugin marker anywhere) must still land on
        OBSERVED, not be swept into the plugin by an over-broad fix.
        """
        registry = self._registry_with_observed_registered_before_plugin()
        record = _record(901, name="python.exe", cmdline="python.exe unrelated")
        registry.register(
            components.ComponentSpec(
                key="only_observed_marker",
                role=components.ROLE_OBSERVED,
                markers=["unrelated"],
            )
        )

        result = attribution_mod.attribute([record], registry)

        assert result.plugin_count == 0
        assert result.attributions[0].component_key == "only_observed_marker"


class TestDeepAncestryAndBoundary:
    """The ancestry walk's depth guard (max_ancestry_depth, default 12) must find a
    plugin marker at any reachable depth and correctly refuse one placed one hop
    beyond the boundary, rather than silently truncating early or over-reaching.
    """

    def test_plugin_marker_three_hops_up_is_found_with_correct_via_pid(self):
        registry = _plugin_only_registry()
        leaf, index = _build_ancestor_chain(depth=5, plugin_marker_at_hop=3)

        result = attribution_mod.attribute([leaf], registry, index)

        assert result.plugin_count == 1
        attribution = result.attributions[0]
        assert attribution.basis == attribution_mod.BASIS_ANCESTRY
        assert attribution.via_pid == 9000 + 3, (
            "via_pid must name the ancestor that actually matched, not the " "immediate parent"
        )

    def test_plugin_marker_at_exactly_max_ancestry_depth_is_found(self):
        """max_ancestry_depth=12 (the default) must include the 12th ancestor."""
        registry = _plugin_only_registry()
        leaf, index = _build_ancestor_chain(depth=12, plugin_marker_at_hop=12)

        result = attribution_mod.attribute([leaf], registry, index, max_ancestry_depth=12)

        assert result.plugin_count == 1, "a marker on the 12th ancestor must be reachable at max_ancestry_depth=12"
        assert result.attributions[0].via_pid == 9000 + 12

    def test_plugin_marker_one_hop_beyond_max_ancestry_depth_is_not_found(self):
        """A marker on the 13th ancestor is one hop past the default depth guard and
        must correctly fall through to unattributed, not be silently found anyway.
        """
        registry = _plugin_only_registry()
        leaf, index = _build_ancestor_chain(depth=13, plugin_marker_at_hop=13)

        result = attribution_mod.attribute([leaf], registry, index, max_ancestry_depth=12)

        assert result.plugin_count == 0
        assert len(result.unattributed) == 1


class TestCyclicAncestry:
    """The seen_pids cycle guard must terminate on looping parent chains without
    either hanging or silently fabricating a plugin match that is not there. Each
    call here is bounded by a hard timeout: a broken guard hangs rather than fails,
    and a hang must be reported as a survivor, never mistaken for a pass.
    """

    def _run_bounded(self, records, registry, index):
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(attribution_mod.attribute, records, registry, index)
            return future.result(timeout=5)

    def test_self_referential_parent_terminates_without_hanging(self):
        """A process whose own ppid points back to itself must not spin forever."""
        registry = _registry_with_broad_observed_marker()
        looping = _record(1, ppid=1, name="a.exe", cmdline="a.exe")
        index = {1: looping}

        result = self._run_bounded([looping], registry, index)

        assert len(result.unattributed) == 1
        assert result.plugin_count == 0

    def test_multi_node_cycle_with_no_plugin_marker_falls_through_to_observed_via_fallback(self):
        """A cycle that never carries the plugin marker must not be attributed to the
        plugin, and must still surface a legitimate OBSERVED match reachable through
        the unrestricted fallback walk once the plugin-restricted walk exhausts the
        cycle without a match.
        """
        registry = _registry_with_broad_observed_marker()
        node1 = _record(1, ppid=2, name="a.exe", cmdline="a.exe")
        node2 = _record(2, ppid=3, name="bash.exe", cmdline="bash.exe -c inert")
        node3 = _record(3, ppid=1, name="c.exe", cmdline="c.exe")
        leaf = _record(10, ppid=1, name="leaf.exe", cmdline="leaf.exe")
        index = {1: node1, 2: node2, 3: node3}

        result = self._run_bounded([leaf], registry, index)

        assert result.plugin_count == 0
        attribution = result.attributions[0]
        assert attribution.component_key == "broad_observed", (
            "the cycle's OBSERVED marker on node2 must still be found by the "
            "unrestricted fallback walk after the plugin-restricted walk exhausts "
            "the cycle without a match"
        )
        assert attribution.basis == attribution_mod.BASIS_ANCESTRY
        assert attribution.via_pid == 2


class TestBrokenAncestryChain:
    """A process whose parent pid is present in the snapshot but whose grandparent is
    missing (broken chain) must stop cleanly at the break, never assume or fabricate
    what lies beyond it -- even when a plugin marker would have been found there.
    """

    def test_plugin_marker_above_a_broken_link_is_not_reachable(self):
        registry = _plugin_only_registry()
        known_parent = _record(501, ppid=502, name="host.exe", cmdline="host.exe inert")
        leaf = _record(500, ppid=501, name="leaf.exe", cmdline="leaf.exe inert")
        index = {501: known_parent}

        result = attribution_mod.attribute([leaf], registry, index)

        assert result.plugin_count == 0
        assert len(result.unattributed) == 1


class TestAccessDeniedInAncestry:
    """access_denied means the operating system withheld the command line and
    executable path for that specific process. It must never be treated as
    equivalent to "this process is not the plugin". These tests check how it behaves
    both on an ancestor mid-chain and on the leaf process being attributed.
    """

    def test_access_denied_ancestor_with_no_identity_does_not_block_the_walk(self):
        """An access-denied ancestor with no name, cmdline or exe cannot match any
        marker itself, but the walk must still continue past it using its ppid to
        reach a plugin marker further up the chain.
        """
        registry = _plugin_only_registry()
        denied_parent = _record(601, ppid=602, name="", cmdline=None, denied=True)
        grandparent = _record(602, ppid=None, name="host.exe", cmdline="host.exe plugin_marker")
        leaf = _record(600, ppid=601, name="leaf.exe", cmdline="leaf.exe inert")
        index = {601: denied_parent, 602: grandparent}

        result = attribution_mod.attribute([leaf], registry, index)

        assert result.plugin_count == 1
        attribution = result.attributions[0]
        assert attribution.basis == attribution_mod.BASIS_ANCESTRY
        assert attribution.via_pid == 602

    def test_access_denied_leaf_with_known_ppid_still_reaches_plugin_via_ancestry(self):
        """The leaf's own direct match is blocked by the blank-identity guard in
        ComponentSpec.matches, but its ppid is still on record, so ancestry can still
        identify it.
        """
        registry = _plugin_only_registry()
        parent = _record(701, ppid=None, name="host.exe", cmdline="host.exe plugin_marker")
        leaf = _record(700, ppid=701, name="", cmdline=None, denied=True)
        index = {701: parent}

        result = attribution_mod.attribute([leaf], registry, index)

        assert result.plugin_count == 1
        assert result.attributions[0].basis == attribution_mod.BASIS_ANCESTRY

    def test_access_denied_leaf_with_broken_ancestry_stays_unattributed_with_withheld_reason(self):
        """When neither the leaf nor its ancestry (broken here -- its ppid points to
        a pid absent from the index, not merely to None) can be identified, the
        process must be reported unattributed with a reason that reflects the OS
        level denial, forcing INDETERMINATE rather than PASS.
        """
        registry = _plugin_only_registry()
        leaf = _record(800, ppid=999, name="", cmdline=None, denied=True)

        result = attribution_mod.attribute([leaf], registry, {})

        assert len(result.unattributed) == 1
        attribution = result.unattributed[0]
        assert attribution.basis == attribution_mod.BASIS_NONE
        assert "withheld" in attribution.reason

    def test_access_denied_process_with_populated_name_can_still_direct_match_a_bare_marker(self):
        """DOCUMENTED FINDING, not a fix: ComponentSpec.matches() only refuses to
        match when name, cmdline AND exe are all empty. A process with cmdline and
        exe withheld by the OS (access_denied=True) but a populated `name` field is
        still eligible for a direct match against any marker that happens to equal
        or appear within that bare name -- so access_denied does not uniformly force
        the conservative "unattributed" outcome the module docstring describes; it
        only does so when the process's identity is completely blank. This is
        contained for the plugin's own detection because no PLUGIN_COUNTED marker in
        build_default_registry is a bare executable name (enforced for new
        components by TestNewObservedMarkersAreSpecific), but
        KEY_CLAUDE_CODE_HOST's own marker ("claude.exe") IS a bare executable name,
        so an access-denied claude.exe process is attributed via name alone rather
        than falling to unattributed. See the task report for the full risk
        assessment; this test documents current behaviour rather than changing it.
        """
        registry = _registry_with_broad_observed_marker()
        denied = _record(801, name="bash.exe", cmdline=None, denied=True)

        result = attribution_mod.attribute([denied], registry)

        assert len(result.unattributed) == 0, (
            "expected finding: a populated `name` field lets an access-denied "
            "process direct-match a bare-name marker instead of staying "
            "unattributed"
        )
        attribution = result.attributions[0]
        assert attribution.component_key == "broad_observed"
        assert attribution.basis == attribution_mod.BASIS_DIRECT


class TestMarkerNormalization:
    """Registry markers are lowercased and, for plugin_root-derived markers,
    backslash-normalised to forward slashes at registration time (components.py
    build_default_registry). ComponentSpec.matches() must normalise the comparison
    text the same way, or a marker built on one path-separator convention silently
    stops matching a process reported in the other -- the fix applied in this task
    closes that gap; these tests prove it.
    """

    def test_case_insensitive_marker_matches_uppercase_cmdline(self):
        """Baseline: case alone must not defeat matching -- both sides are already
        lowercased independently of the separator-normalisation fix.
        """
        registry = _plugin_only_registry()
        record = _record(1, name="PYTHON.EXE", cmdline="PYTHON.EXE PLUGIN_MARKER --flag")

        result = attribution_mod.attribute([record], registry)

        assert result.plugin_count == 1

    def test_plugin_root_marker_matches_a_backslash_style_windows_cmdline(self):
        """The full plugin_root marker is normalised to forward slashes when the
        registry is built. Before the fix in ComponentSpec.matches(), this marker
        could never match a real Windows process, whose cmdline/exe are reported
        with backslashes: the registered marker
        ("c:/users/techd/pluginstall") is not a substring of the raw
        ("c:\\users\\techd\\pluginstall\\entry.py") text, because only the marker
        side was normalised, not the process side. The fix normalises the
        comparison text the same way the marker was normalised, so both forms of the
        same path now match.
        """
        windows_style_root = r"C:\Users\techd\pluginstall"
        registry = components.build_default_registry(plugin_root=windows_style_root)
        plugin_spec = registry.get(components.KEY_PLUGIN)
        normalised_marker = windows_style_root.replace("\\", "/").lower()
        assert (
            normalised_marker in plugin_spec.markers
        ), "test assumption: build_default_registry normalises plugin_root to forward slashes"

        record = _record(1, name="python.exe", cmdline=windows_style_root + r"\entry.py")

        result = attribution_mod.attribute([record], registry)

        assert result.plugin_count == 1, (
            "a plugin_root marker built with forward-slash normalisation must "
            "still match a native Windows backslash-style command line"
        )

    def test_harness_self_dual_form_markers_remain_functional_after_normalisation(self):
        """components.py registers both "tests/nfr1" and "tests\\nfr1" for
        KEY_HARNESS_SELF, and the component must stay reachable from a command line
        written either way.

        Both marker forms now normalise to the same forward-slash string at
        construction, so the pair is redundant rather than load-bearing. It is left
        in place because removing it would change a registry this test exists to pin,
        not because either form is doing work the other does not.
        """
        registry = components.build_default_registry(plugin_root=None)
        forward_slash_record = _record(1, cmdline=r"python tests/nfr1/cli.py --self-test")
        backslash_record = _record(2, cmdline=r"python tests\nfr1\cli.py --self-test")

        forward_result = attribution_mod.attribute([forward_slash_record], registry)
        backslash_result = attribution_mod.attribute([backslash_record], registry)

        assert forward_result.attributions[0].component_key == components.KEY_HARNESS_SELF
        assert backslash_result.attributions[0].component_key == components.KEY_HARNESS_SELF


class TestAMarkerIsNormalisedOnBothSides:
    """A marker written with Windows separators must not become silently dead.

    Normalising only the process text left any backslash marker unable to match
    anything, since the text it was compared against no longer held a backslash.
    Nothing reports a marker that stopped matching: the component simply collects
    nothing, which reads exactly like "that component spawned no processes". For a
    plugin marker that failure mode is an unfailable NFR-1, so both sides are
    normalised and both directions are pinned here.
    """

    def test_a_backslash_marker_with_no_forward_slash_twin_still_matches(self):
        spec = components.ComponentSpec(
            key="plugin",
            role=components.ROLE_PLUGIN_COUNTED,
            markers=["plugins" + chr(92) + "cwe"],
        )
        record = _record(1, cmdline="python C:" + chr(92) + "plugins" + chr(92) + "cwe" + chr(92) + "entry.py")
        assert spec.matches(record) is not None

    def test_a_forward_slash_marker_matches_a_backslash_process(self):
        spec = components.ComponentSpec(
            key="plugin",
            role=components.ROLE_PLUGIN_COUNTED,
            markers=["plugins/cwe"],
        )
        record = _record(1, cmdline="python C:" + chr(92) + "plugins" + chr(92) + "cwe" + chr(92) + "entry.py")
        assert spec.matches(record) is not None

    def test_an_unrelated_path_still_does_not_match(self):
        """Paired negative: normalising must not turn matching into a blanket yes."""
        spec = components.ComponentSpec(
            key="plugin",
            role=components.ROLE_PLUGIN_COUNTED,
            markers=["plugins/cwe"],
        )
        record = _record(1, cmdline="python C:" + chr(92) + "other" + chr(92) + "tool" + chr(92) + "entry.py")
        assert spec.matches(record) is None

    def test_every_registered_marker_is_stored_normalised(self):
        """No registry entry may keep a separator form that can never match."""
        registry = components.build_default_registry(plugin_root=None)
        offenders = [(s.key, m) for s in registry for m in s.markers if chr(92) in m]
        assert offenders == [], "markers must be stored forward-slash normalised: %r" % offenders


class TestPluginMarkersAreSpecificEnough:
    """A marker broad enough to match unrelated software produces false FAILs.

    build_default_registry derived a marker from the plugin root's BASENAME, and
    this plugin's directory is named `plugin`, so the marker was the single word
    `plugin`. Any command line mentioning it -- a browser flag, an unrelated path --
    would have been charged to the plugin. Nothing matched it during the first real
    measurement, so no result was corrupted, but a metric that can fail for the
    wrong reason is no better than one that cannot fail at all.
    """

    REAL_ROOT = "C:/Users/x/dev/claude-workflow-engine/plugin"

    def test_an_unrelated_process_mentioning_plugins_is_not_charged(self):
        registry = components.build_default_registry(self.REAL_ROOT)
        record = _record(1, cmdline="chrome.exe --disable-plugins --type=renderer")
        result = attribution_mod.attribute([record], registry)
        assert result.plugin_count == 0, "a browser flag was charged to the plugin"

    def test_the_real_plugin_path_is_still_charged(self):
        """Specificity: tightening the marker must not stop it matching the plugin."""
        registry = components.build_default_registry(self.REAL_ROOT)
        record = _record(1, cmdline="python %s/scripts/pipeline_entry.py" % self.REAL_ROOT)
        result = attribution_mod.attribute([record], registry)
        assert result.plugin_count == 1

    def test_the_qualified_marker_survives_a_relocated_checkout(self):
        """The point of a short marker: match the plugin at a different absolute path."""
        registry = components.build_default_registry(self.REAL_ROOT)
        moved = "D:/elsewhere/claude-workflow-engine/plugin/scripts/entry.py"
        result = attribution_mod.attribute([_record(1, cmdline="python " + moved)], registry)
        assert result.plugin_count == 1

    def test_no_derived_marker_is_a_bare_generic_word(self):
        registry = components.build_default_registry(self.REAL_ROOT)
        generic = {"plugin", "plugins", "scripts", "bin", "src", "lib", "app"}
        for spec in registry:
            if spec.role != components.ROLE_PLUGIN_COUNTED:
                continue
            offenders = [m for m in spec.markers if m in generic]
            assert offenders == [], "generic plugin markers: %r" % offenders

    def test_a_single_component_root_yields_no_qualified_marker(self):
        assert components.qualified_tail("plugin") is None

    def test_a_two_component_root_yields_the_pair(self):
        assert components.qualified_tail("C:/claude-workflow-engine/plugin") == "claude-workflow-engine/plugin"

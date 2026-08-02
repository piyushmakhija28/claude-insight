"""
Tests for call-graph callee resolution confidence (issue #266, FR-9b / SRS FR-38).

Covers three obligations:

- AC (1) a committed check that enumerates every method FQN in danger_zones or
  hot_nodes for a full-repo run and fails when a builtin-colliding entry's
  fan-in does not survive exclusion of the collided edges. The collision name
  set is derived from the running interpreter, never hand-maintained.
- AC (2) both the raw and the high-confidence fan-in are reported as distinct
  fields at every point a fan-in is consumed.
- AC (3) a bare name matching two or more FQNs with no same-file candidate no
  longer produces a confident edge.

Each assertion is paired with a negative control that reinstates the pre-fix
resolver and proves the assertion fails against it, so no assertion is
vacuous. A specificity control proves the fix does not suppress legitimate
resolutions -- a change that resolved nothing would satisfy every collision
assertion here and be worthless.

Windows-safe: ASCII only.
"""

import builtins
from collections import deque

import pytest

from langgraph_engine.parsers.graph_model import (
    BUILTIN_CALLEE_NAMES,
    CONFIDENCE_AMBIGUOUS,
    CONFIDENCE_HIGH,
    CallGraph,
    make_call_edge,
    make_class_node,
    make_method_node,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _add_method(graph, file_path, owner, name):
    """Register a method node on the graph and return its FQN."""
    fqn = "%s::%s.%s" % (file_path, owner, name) if owner else "%s::%s" % (file_path, name)
    parent = "%s::%s" % (file_path, owner) if owner else None
    graph.methods[fqn] = make_method_node(fqn, name, file_path, 1, parent_class=parent)
    graph.nodes[fqn] = graph.methods[fqn]
    return fqn


def _add_class(graph, file_path, name):
    """Register a class node on the graph and return its FQN."""
    fqn = "%s::%s" % (file_path, name)
    graph.classes[fqn] = make_class_node(fqn, name, file_path, 1)
    graph.nodes[fqn] = graph.classes[fqn]
    return fqn


def _legacy_resolve_target(self, target, caller_fqn, name_to_fqns, class_name_to_fqn):
    """The pre-fix resolver, verbatim, adapted to the current tuple return shape.

    Used only by the negative controls: an assertion that cannot fail against
    the behaviour it was written to forbid proves nothing.
    """
    if "::" in target:
        return (target, CONFIDENCE_HIGH)
    caller_file = caller_fqn.split("::")[0] if "::" in caller_fqn else ""
    if "." in target:
        parts = target.rsplit(".", 1)
        method_name = parts[-1]
        if "::" in parts[0]:
            return (target, CONFIDENCE_HIGH)
        if method_name in name_to_fqns:
            candidates = name_to_fqns[method_name]
            same_file = [c for c in candidates if c.startswith(caller_file + "::")]
            if same_file:
                return (same_file[0], CONFIDENCE_HIGH)
            if len(candidates) == 1:
                return (candidates[0], CONFIDENCE_HIGH)
        return (target, CONFIDENCE_HIGH)
    if target in name_to_fqns:
        candidates = name_to_fqns[target]
        same_file = [c for c in candidates if c.startswith(caller_file + "::")]
        if same_file:
            return (same_file[0], CONFIDENCE_HIGH)
        if len(candidates) == 1:
            return (candidates[0], CONFIDENCE_HIGH)
        return (candidates[0], CONFIDENCE_HIGH)
    if target in class_name_to_fqn:
        class_fqn = class_name_to_fqn[target]
        init_fqn = "%s.__init__" % class_fqn
        if init_fqn in self.methods:
            return (init_fqn, CONFIDENCE_HIGH)
        return (class_fqn, CONFIDENCE_HIGH)
    return (target, CONFIDENCE_HIGH)


@pytest.fixture
def legacy_resolver(monkeypatch):
    """Reinstate the pre-fix resolver for the duration of one negative control."""
    monkeypatch.setattr(CallGraph, "_resolve_target", _legacy_resolve_target)
    return _legacy_resolve_target


def _edge_to(edges, callee_marker):
    """Return the single edge whose caller FQN contains callee_marker."""
    matches = [e for e in edges if callee_marker in e["from"]]
    assert len(matches) == 1, "Expected exactly 1 edge from %s, got %d" % (callee_marker, len(matches))
    return matches[0]


# ---------------------------------------------------------------------------
# AC (3): an ambiguous bare name must not produce a confident edge
# ---------------------------------------------------------------------------


class TestAmbiguousBareName:
    """A bare name matching 2+ FQNs with no same-file candidate is not confident."""

    @staticmethod
    def _graph():
        """Two same-named project functions in other files, one bare caller."""
        g = CallGraph()
        _add_method(g, "alpha.py", None, "handle")
        _add_method(g, "beta.py", None, "handle")
        caller = _add_method(g, "caller.py", None, "run_it")
        g.edges.append(make_call_edge(caller, "handle", 5))
        return g

    def test_ambiguous_bare_name_is_not_confident(self):
        """AC (3): the edge must not be a confident binding to an arbitrary match."""
        edges = self._graph().resolve_edges()
        edge = _edge_to(edges, "run_it")

        assert edge["confidence"] != CONFIDENCE_HIGH, "Ambiguous bare name produced a confident edge: %s" % edge
        assert edge["to"] == "handle", "Ambiguous bare name was bound to %s instead of left unresolved" % edge["to"]
        assert edge["resolved"] is False

    def test_ambiguous_bare_name_is_marked_ambiguous_not_merely_unknown(self):
        """The edge is distinguishable from a plain external call."""
        edges = self._graph().resolve_edges()
        assert _edge_to(edges, "run_it")["confidence"] == CONFIDENCE_AMBIGUOUS

    def test_negative_control_legacy_resolver_violates_the_assertion(self, legacy_resolver):
        """NEGATIVE CONTROL: the pre-fix resolver fails the assertion above.

        Proves the assertion has teeth rather than passing for any resolver.
        """
        edge = _edge_to(self._graph().resolve_edges(), "run_it")

        assert edge["confidence"] == CONFIDENCE_HIGH
        assert edge["to"] in ("alpha.py::handle", "beta.py::handle")
        assert edge["to"] != "handle", "Legacy resolver was expected to bind an arbitrary first match"


# ---------------------------------------------------------------------------
# Builtin-name collisions
# ---------------------------------------------------------------------------


class TestBuiltinNameCollision:
    """A callee named after a builtin or container method is not bound by name."""

    @staticmethod
    def _graph():
        """One project append/format, plus list.append and str.format style calls."""
        g = CallGraph()
        _add_method(g, "appender.py", "JsonlAppender", "append")
        _add_method(g, "messages.py", "ErrorMessages", "format")
        caller = _add_method(g, "worker.py", None, "collect")
        g.edges.append(make_call_edge(caller, "parts.append", 3, "method_call"))
        g.edges.append(make_call_edge(caller, "format", 4))
        return g

    def test_container_method_call_does_not_bind_to_project_method(self):
        """parts.append(x) names the list method, not the sole project append."""
        edges = self._graph().resolve_edges()
        appends = [e for e in edges if e["line"] == 3]
        assert appends[0]["to"] == "parts.append"
        assert appends[0]["confidence"] == CONFIDENCE_AMBIGUOUS

    def test_bare_builtin_named_call_does_not_bind_to_project_method(self):
        """A bare format(...) call is not evidence for a project ErrorMessages.format."""
        edges = self._graph().resolve_edges()
        formats = [e for e in edges if e["line"] == 4]
        assert formats[0]["to"] == "format"
        assert formats[0]["confidence"] == CONFIDENCE_AMBIGUOUS

    def test_negative_control_legacy_resolver_binds_both(self, legacy_resolver):
        """NEGATIVE CONTROL: the pre-fix resolver binds both calls to project methods."""
        edges = self._graph().resolve_edges()
        by_line = {e["line"]: e for e in edges}

        assert by_line[3]["to"] == "appender.py::JsonlAppender.append"
        assert by_line[4]["to"] == "messages.py::ErrorMessages.format"

    def test_collision_name_set_is_derived_not_hand_maintained(self):
        """The collision set comes from the interpreter, so it cannot go stale."""
        for name in ("append", "format", "get", "set", "open", "count", "update", "type"):
            assert name in BUILTIN_CALLEE_NAMES

        expected = set(dir(builtins))
        for container in (str, list, dict, set):
            expected.update(n for n in dir(container) if not n.startswith("_"))
        assert set(BUILTIN_CALLEE_NAMES) == expected


# ---------------------------------------------------------------------------
# SPECIFICITY CONTROL: the fix must not suppress legitimate resolutions
# ---------------------------------------------------------------------------


class TestSpecificityControl:
    """Legitimate bindings must still resolve, at high confidence.

    A change that resolved nothing would satisfy every collision assertion in
    this module. These tests are what stop that change from passing.
    """

    def test_distinctive_single_candidate_still_resolves(self):
        """A sole project definition with a distinctive name still binds."""
        g = CallGraph()
        target = _add_method(g, "helpers.py", None, "provision_skill")
        caller = _add_method(g, "caller.py", None, "run_it")
        g.edges.append(make_call_edge(caller, "manager.provision_skill", 2, "method_call"))
        g.edges.append(make_call_edge(caller, "provision_skill", 3))

        edges = g.resolve_edges()
        assert [e["to"] for e in edges] == [target, target]
        assert {e["confidence"] for e in edges} == {CONFIDENCE_HIGH}

    def test_same_file_candidate_still_resolves(self):
        """A same-file definition still wins over remote same-named ones."""
        g = CallGraph()
        _add_method(g, "other.py", None, "compute_total")
        local = _add_method(g, "here.py", None, "compute_total")
        caller = _add_method(g, "here.py", None, "run_it")
        g.edges.append(make_call_edge(caller, "compute_total", 7))

        edge = _edge_to(g.resolve_edges(), "run_it")
        assert edge["to"] == local
        assert edge["confidence"] == CONFIDENCE_HIGH

    def test_receiver_class_evidence_resolves_a_builtin_named_method(self):
        """ErrorMessages.format(...) names its owner, so the guard must not fire.

        This is the discriminating case: the same simple name that must NOT
        bind from a bare call MUST bind when the receiver identifies the class.
        """
        g = CallGraph()
        _add_class(g, "messages.py", "ErrorMessages")
        target = _add_method(g, "messages.py", "ErrorMessages", "format")
        caller = _add_method(g, "caller.py", None, "run_it")
        g.edges.append(make_call_edge(caller, "ErrorMessages.format", 9, "method_call"))

        edge = _edge_to(g.resolve_edges(), "run_it")
        assert edge["to"] == target, "Receiver-class evidence was discarded; got %s" % edge["to"]
        assert edge["confidence"] == CONFIDENCE_HIGH

    def test_constructor_call_still_resolves(self):
        """A class-name call still resolves to its constructor."""
        g = CallGraph()
        _add_class(g, "models.py", "Order")
        init = _add_method(g, "models.py", "Order", "__init__")
        caller = _add_method(g, "caller.py", None, "run_it")
        g.edges.append(make_call_edge(caller, "Order", 4))

        edge = _edge_to(g.resolve_edges(), "run_it")
        assert edge["to"] == init
        assert edge["confidence"] == CONFIDENCE_HIGH

    def test_negative_control_a_resolve_nothing_stub_fails_this_suite(self, monkeypatch):
        """NEGATIVE CONTROL: a resolver that resolves nothing fails specificity.

        Demonstrates that the specificity assertions can fail, which is what
        makes them a control rather than decoration.
        """

        def resolve_nothing(self, target, caller_fqn, name_to_fqns, class_name_to_fqn):
            return (target, CONFIDENCE_AMBIGUOUS)

        monkeypatch.setattr(CallGraph, "_resolve_target", resolve_nothing)

        g = CallGraph()
        _add_method(g, "helpers.py", None, "provision_skill")
        caller = _add_method(g, "caller.py", None, "run_it")
        g.edges.append(make_call_edge(caller, "provision_skill", 3))

        edge = _edge_to(g.resolve_edges(), "run_it")
        assert edge["confidence"] != CONFIDENCE_HIGH
        assert edge["to"] == "provision_skill"


# ---------------------------------------------------------------------------
# AC (2): both counts reported
# ---------------------------------------------------------------------------


class TestTwoFieldReporting:
    """Raw and high-confidence figures are reported as distinct fields."""

    @staticmethod
    def _graph():
        """One evidenced caller and one ambiguous caller into the same method."""
        g = CallGraph()
        _add_method(g, "store.py", "Store", "persist_record")
        _add_method(g, "store.py", "Store", "get")
        _add_method(g, "cache.py", "Cache", "get")
        evidenced = _add_method(g, "a.py", None, "caller_a")
        ambiguous = _add_method(g, "b.py", None, "caller_b")
        g.edges.append(make_call_edge(evidenced, "store.persist_record", 1, "method_call"))
        g.edges.append(make_call_edge(ambiguous, "get", 2))
        return g

    def test_confidence_summary_reports_both(self):
        """get_resolution_confidence splits the total into evidenced and not."""
        g = self._graph()
        g.resolve_edges()
        counts = g.get_resolution_confidence()

        assert counts["total_call_edges"] == 2
        assert counts["high_confidence"] == 1
        assert counts["ambiguous"] == 1
        assert counts["high_confidence"] < counts["total_call_edges"]

    def test_high_confidence_edge_accessor_is_a_strict_subset(self):
        """get_high_confidence_edges never returns more than get_edges."""
        g = self._graph()
        g.resolve_edges()
        assert len(g.get_high_confidence_edges()) < len(g.get_edges())

    def test_stats_report_both_counts(self):
        """get_stats exposes high_confidence_edges alongside resolved_edges."""
        g = self._graph()
        g.resolve_edges()
        stats = g.get_stats()
        assert "high_confidence_edges" in stats
        assert "ambiguous_edges" in stats
        assert stats["high_confidence_edges"] == 1

    def test_impact_map_high_confidence_variant_is_a_subset(self):
        """The high-confidence impact map never credits an ambiguous caller."""
        g = self._graph()
        g.resolve_edges()
        raw = g.compute_impact_map()
        high = g.compute_impact_map(high_confidence_only=True)

        for fqn, callers in high.items():
            assert callers <= raw[fqn], "High-confidence callers of %s exceed raw callers" % fqn

    def test_negative_control_unmarked_edges_are_never_high_confidence(self):
        """An unresolved graph reports no high-confidence subset."""
        g = self._graph()
        assert g.get_high_confidence_edges() == []
        assert g.get_resolution_confidence()["high_confidence"] == 0


# ---------------------------------------------------------------------------
# AC (1): committed full-repo collision check
# ---------------------------------------------------------------------------


def _is_collided_edge(raw_edge):
    """Report whether an edge could only have been bound by name collision.

    An edge is collided when the callee the parser emitted -- before any
    resolution -- is an unqualified name that a builtin or container method
    also owns. A target the parser already qualified with "::" carries
    syntactic evidence of its owner (a self/cls call) and is never a
    collision, even when its simple name is "open" or "get".
    """
    target = raw_edge["to"]
    if "::" in target:
        return False
    return target.rsplit(".", 1)[-1] in BUILTIN_CALLEE_NAMES


def _collision_excluded_caller_counts(graph, targets):
    """Count transitive callers of each target over collision-excluded edges.

    The exclusion is recomputed here from the raw edge list rather than read
    back from the confidence marker, so this check would still catch a
    resolver that mislabelled its own output.
    """
    reverse = {}
    for raw_edge, resolved_edge in zip(graph.edges, graph.get_edges()):
        if resolved_edge.get("type") == "inheritance":
            continue
        if _is_collided_edge(raw_edge):
            continue
        reverse.setdefault(resolved_edge["to"], set()).add(resolved_edge["from"])

    counts = {}
    for target in targets:
        seen = set()
        queue = deque([target])
        while queue:
            current = queue.popleft()
            for caller in reverse.get(current, set()):
                if caller not in seen:
                    seen.add(caller)
                    queue.append(caller)
        counts[target] = len(seen)
    return counts


def _simple_name(fqn):
    """Return the bare method name from a FQN."""
    tail = fqn.split("::")[-1]
    return tail.rsplit(".", 1)[-1]


@pytest.fixture(scope="module")
def repo_analysis():
    """Run a full-repo analysis once and share it across the gate checks."""
    from pathlib import Path

    from langgraph_engine.parsers.call_graph_builder_legacy import CallGraphBuilder
    from langgraph_engine.sdlc_pipeline.call_graph_analyzer import (
        analyze_impact_before_change,
        get_orchestration_context,
    )

    root = Path(__file__).resolve().parents[1]
    graph = CallGraphBuilder(str(root)).build()
    impact = analyze_impact_before_change(str(root))
    orchestration = get_orchestration_context("full repo scan", str(root))
    return {
        "graph": graph,
        "danger_zones": impact.get("danger_zones", []),
        "hot_nodes": orchestration.get("hot_nodes", []),
        "impact": impact,
        "orchestration": orchestration,
    }


@pytest.mark.slow
class TestFullRepoCollisionGate:
    """Committed check: no danger zone or hot node rests on a name collision."""

    def test_analysis_is_not_vacuous(self, repo_analysis):
        """Guard the gate itself: an empty ranking would pass every check below."""
        assert repo_analysis["impact"]["call_graph_available"] is True
        assert repo_analysis["orchestration"]["call_graph_available"] is True
        assert len(repo_analysis["danger_zones"]) > 0
        assert len(repo_analysis["hot_nodes"]) > 0

    def test_no_ranked_entry_survives_only_on_collided_edges(self, repo_analysis):
        """AC (1): a builtin-colliding entry must keep its fan-in without them.

        An entry whose fan-in survives the exclusion is legitimate and passes;
        the check is on the collision, not on the name.
        """
        entries = repo_analysis["danger_zones"] + repo_analysis["hot_nodes"]
        suspect = [e["fqn"] for e in entries if _simple_name(e["fqn"]) in BUILTIN_CALLEE_NAMES]

        surviving = _collision_excluded_caller_counts(repo_analysis["graph"], suspect)
        collapsed = [(fqn, surviving[fqn]) for fqn in suspect if surviving[fqn] < 5]

        assert not collapsed, (
            "Ranked entries whose fan-in collapses once builtin-name collisions " "are excluded: %s" % collapsed
        )

    def test_every_ranked_entry_reports_both_counts(self, repo_analysis):
        """AC (2): no ranked entry exposes a single conflated caller count."""
        for entry in repo_analysis["danger_zones"] + repo_analysis["hot_nodes"]:
            assert "callers_count" in entry
            assert "callers_count_high_confidence" in entry
            assert entry["callers_count_high_confidence"] <= entry["callers_count"]

    def test_every_get_edges_consumer_reports_both_counts(self, repo_analysis):
        """AC (2): each graph.get_edges() consumer returns edge_counts."""
        for result in (repo_analysis["impact"], repo_analysis["orchestration"]):
            counts = result["edge_counts"]
            assert counts["total"] > 0
            assert counts["high_confidence"] <= counts["total"]
            assert "ambiguous" in counts

    def test_collision_rate_is_reported(self, repo_analysis):
        """AC (1) reporting obligation: the rate is surfaced, not asserted at a target."""
        counts = repo_analysis["graph"].get_resolution_confidence()
        assert counts["total_call_edges"] == (counts["high_confidence"] + counts["ambiguous"] + counts["no_candidate"])

    def test_negative_control_gate_fires_against_the_legacy_resolver(self, legacy_resolver):
        """NEGATIVE CONTROL: the same gate fails on a legacy-resolved full-repo graph.

        Rebuilds the real repository graph with the pre-fix resolver and
        applies the identical exclusion. If this found nothing, the gate above
        would be passing by construction rather than by merit.
        """
        from pathlib import Path

        from langgraph_engine.parsers.call_graph_builder_legacy import CallGraphBuilder

        root = Path(__file__).resolve().parents[1]
        graph = CallGraphBuilder(str(root)).build()

        impact = graph.compute_impact_map()
        ranked = [fqn for fqn, callers in impact.items() if len(callers) >= 5]
        suspect = [fqn for fqn in ranked if _simple_name(fqn) in BUILTIN_CALLEE_NAMES]
        assert suspect, "Legacy resolver was expected to rank builtin-named methods"

        surviving = _collision_excluded_caller_counts(graph, suspect)
        collapsed = [fqn for fqn in suspect if surviving[fqn] < 5]
        assert collapsed, "Gate did not fire against the pre-fix resolver, so it proves nothing"

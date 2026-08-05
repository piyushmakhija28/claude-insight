"""Runtime proof that call-graph discovery and traversal are coverage-complete.

Issue #265 (local key V2-009, PRD FR-9a / SRS FR-21). Two truncation sites
bound in production and this suite asserts on the OUTPUT of a real in-process
build rather than on the value of any constant -- constant inspection is the
failure mode that let the defect ship in the first place.

The two sites under test:

1. ``langgraph_engine/parsers/call_graph_builder_legacy.py`` MAX_FILES, which
   was 300 against 411 eligible files and exhausted its budget five files
   before ``langgraph_engine/sdlc_pipeline/`` began, hiding that whole tree.
2. ``langgraph_engine/parsers/graph_model.py`` DEFAULT_MAX_PATHS, which was
   500 and truncated ``compute_call_paths()`` on every run regardless of how
   many files were ingested.

The eligibility oracle in this module is deliberately a re-implementation. It
restates the extension set, the excluded directory names and the file-size
limit as its own literals and imports none of them, so it is able to disagree
with the builder. An oracle built from the builder's own constants could only
ever agree and would prove nothing. ``TestOracleIndependence`` asserts both
properties: that no eligibility rule is imported, and that mutating the
builder's constants at runtime leaves the oracle's answer unchanged.

Windows-safe: ASCII only.
"""

import logging
import os
from pathlib import Path

import pytest

from langgraph_engine.parsers import call_graph_builder_legacy as legacy
from langgraph_engine.parsers.call_graph_builder_legacy import CallGraphBuilder
from langgraph_engine.parsers.graph_model import CallGraph, make_call_edge, make_method_node

PROJECT_ROOT = Path(__file__).resolve().parent.parent

GRAPH_MODEL_LOGGER = "langgraph_engine.parsers.graph_model"

TRUNCATION_MARKERS = ("hit max_paths=", "limit; results truncated")

CANARY_PREFIX = "langgraph_engine/sdlc_pipeline/"

# MEASURED 2026-08-01 by docs/phase-5-uml/callgraph_coverage_probe.md section 2,
# with the file cap lifted: files_analyzed=411, total_classes=480,
# total_methods=3506, functions=1340, call_edges=26114, resolved_edges=7004.
# The shipping truncated build produced 300 / 449 / 2844.
#
# CORRECTED 2026-08-03. This block previously claimed "these are floors, not
# equalities, so adding source files cannot fail the suite". That was FALSE and
# a measurement refuted it. The floor ASSERTIONS do only get safer as the tree
# grows -- but the negative control asserted the opposite direction, that a
# capped build stays BELOW the floor, and growth erodes that. Measured margin
# below FLOOR_METHODS for a 300-file capped build: +662 on 2026-08-01, +10 on
# 2026-08-03, then negative once a single new test file landed. That control is
# now anchored to the complete build of the same run instead of to these
# literals, so it cannot erode again.
#
# These literals remain a dated probe measurement and are deliberately NOT
# re-baselined here: they are cited by docs/phase-5-uml/callgraph_coverage_probe.md
# and silently moving them would break that provenance. Note the consequence
# while they stand -- a floor taken on a 411-file tree discriminates weakly
# against truncation once the tree is materially larger.
FLOOR_FILES = 411
FLOOR_CLASSES = 480
FLOOR_METHODS = 3506

TRUNCATED_BASELINE_FILES = 300

# ---------------------------------------------------------------------------
# Independent eligibility oracle -- restated literals, nothing imported
# ---------------------------------------------------------------------------

ORACLE_EXTENSIONS = frozenset({".py", ".java", ".ts", ".tsx", ".kt"})

ORACLE_EXCLUDED_DIR_NAMES = frozenset(
    {
        ".git",
        "__pycache__",
        ".venv",
        "venv",
        "node_modules",
        "dist",
        "build",
        ".tox",
        ".eggs",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
    }
)

ORACLE_MAX_FILE_SIZE_KB = 100


def enumerate_eligible_sources(project_root):
    """Enumerate every source file the builder ought to analyse, independently.

    Walks the tree with os.walk, pruning excluded directory names in place so
    vendored trees are never descended into, and applies the same three
    eligibility rules the builder applies: supported suffix, no excluded path
    component below the project root, and size within the file-size limit.
    Every rule is expressed with this module's own literals.

    Args:
        project_root: Path to the project root to enumerate.

    Returns:
        Set of repo-relative POSIX-style path strings.
    """
    root = Path(project_root).resolve()
    eligible = set()
    for dir_path, dir_names, file_names in os.walk(root):
        dir_names[:] = [d for d in dir_names if d not in ORACLE_EXCLUDED_DIR_NAMES]
        for file_name in file_names:
            candidate = Path(dir_path) / file_name
            if candidate.suffix.lower() not in ORACLE_EXTENSIONS:
                continue
            try:
                size_kb = candidate.stat().st_size / 1024.0
            except OSError:
                continue
            if size_kb > ORACLE_MAX_FILE_SIZE_KB:
                continue
            eligible.add(candidate.relative_to(root).as_posix())
    return eligible


# ---------------------------------------------------------------------------
# Module-scope log capture over the traversal logger
# ---------------------------------------------------------------------------


class RecordCollector(logging.Handler):
    """Collect every LogRecord emitted through the logger it is attached to.

    A dedicated handler is used instead of the caplog fixture because the
    assertion has to cover a whole module-scoped build, which outlives any
    function-scoped fixture.
    """

    def __init__(self):
        """Initialise an empty record buffer at the lowest capture level."""
        logging.Handler.__init__(self, level=logging.NOTSET)
        self.records = []

    def emit(self, record):
        """Append the record to the buffer."""
        self.records.append(record)


def truncation_records(records):
    """Filter captured records down to max_paths truncation warnings.

    Args:
        records: Iterable of LogRecord captured from the traversal logger.

    Returns:
        List of the formatted messages that carry both truncation markers.
    """
    matched = []
    for record in records:
        message = record.getMessage()
        if all(marker in message for marker in TRUNCATION_MARKERS):
            matched.append(message)
    return matched


class CapturedBuild(object):
    """Result of one in-process build together with everything it logged."""

    def __init__(self, graph, stats, records):
        """Store the built graph, its statistics and the captured records."""
        self.graph = graph
        self.stats = stats
        self.records = records

    @property
    def analysed_files(self):
        """Return the set of repo-relative paths the builder actually analysed."""
        return set(self.graph.files)


def run_captured_build(project_root, **builder_kwargs):
    """Build the call graph in-process while capturing traversal warnings.

    ``build()`` alone does not walk call paths, so ``get_stats()`` is called
    inside the capture window: it reaches ``compute_call_paths()`` through
    ``get_max_call_depth()``, which is where a max_paths cap would fire.

    Args:
        project_root: Project root to analyse.
        **builder_kwargs: Passed through to CallGraphBuilder. Passing nothing
            exercises the shipping default, which is what the coverage
            assertions require.

    Returns:
        CapturedBuild instance.
    """
    logger = logging.getLogger(GRAPH_MODEL_LOGGER)
    collector = RecordCollector()
    previous_level = logger.level
    logger.addHandler(collector)
    logger.setLevel(logging.DEBUG)
    try:
        graph = CallGraphBuilder(project_root, **builder_kwargs).build()
        stats = graph.get_stats()
    finally:
        logger.removeHandler(collector)
        logger.setLevel(previous_level)
    return CapturedBuild(graph, stats, collector.records)


@pytest.fixture(scope="module")
def default_build():
    """Build the real project graph once, using no max_files argument at all.

    Constructing the builder with no cap argument is deliberate: the fix is
    established by the shipping default being coverage-complete, never by
    rebinding a module global, which AC (E) forbids.
    """
    return run_captured_build(PROJECT_ROOT)


# ---------------------------------------------------------------------------
# (A) Discovery is coverage-complete
# ---------------------------------------------------------------------------


class TestDiscoveryCoverage:
    """Set equality between the analysed set and the independent oracle."""

    def test_discovery_covers_every_package(self, default_build):
        """The analysed set equals the oracle's eligible set exactly."""
        expected = enumerate_eligible_sources(PROJECT_ROOT)
        analysed = default_build.analysed_files

        assert expected, "oracle enumerated no eligible files -- the check would be vacuous"

        missing = sorted(expected - analysed)
        unexpected = sorted(analysed - expected)
        assert not missing and not unexpected, "discovery is not coverage-complete. missing=%r unexpected=%r" % (
            missing[:20],
            unexpected[:20],
        )

    def test_analysed_set_is_larger_than_the_truncated_baseline(self, default_build):
        """More files are analysed than the 300 the shipping builder managed."""
        assert len(default_build.analysed_files) > TRUNCATED_BASELINE_FILES


# ---------------------------------------------------------------------------
# (B) The named canary is whole
# ---------------------------------------------------------------------------


class TestSdlcPipelineCanary:
    """langgraph_engine/sdlc_pipeline/ was 0 of 45 analysed before the fix."""

    def test_canary_symmetric_difference_is_empty(self, default_build):
        """Every file in the canary tree is analysed, and no extras appear."""
        expected = {path for path in enumerate_eligible_sources(PROJECT_ROOT) if path.startswith(CANARY_PREFIX)}
        analysed = {path for path in default_build.analysed_files if path.startswith(CANARY_PREFIX)}

        assert expected, "canary tree enumerated empty -- the check would be vacuous"
        assert expected ^ analysed == set(), "canary tree incomplete. symmetric_difference=%r" % (
            sorted(expected ^ analysed)[:20],
        )

    def test_canary_tree_is_not_trivially_small(self, default_build):
        """The canary holds at least the 45 files measured on 2026-08-01."""
        analysed = {path for path in default_build.analysed_files if path.startswith(CANARY_PREFIX)}
        assert len(analysed) >= 45


# ---------------------------------------------------------------------------
# (C) No traversal truncation is emitted -- the load-bearing assertion
# ---------------------------------------------------------------------------


class TestNoTraversalTruncation:
    """max_paths=500 fired on both probe runs, including the uncapped one."""

    def test_build_emits_no_max_paths_truncation_record(self, default_build):
        """Zero truncation records are captured across build and get_stats."""
        emitted = truncation_records(default_build.records)
        assert emitted == [], "traversal was truncated during the build: %r" % (emitted,)

    def test_capture_window_actually_observed_the_traversal(self, default_build):
        """Guard against a vacuous pass from never reaching the traversal."""
        assert default_build.stats["max_call_depth"] > 0


# ---------------------------------------------------------------------------
# (D) Regression floor
# ---------------------------------------------------------------------------


class TestRegressionFloor:
    """Floors from the MEASURED complete probe figures, not equalities."""

    def test_files_analyzed_meets_floor(self, default_build):
        """At least the 411 files the complete probe measured."""
        assert default_build.stats["files_analyzed"] >= FLOOR_FILES

    def test_total_classes_meets_floor(self, default_build):
        """At least the 480 classes the complete probe measured."""
        assert default_build.stats["total_classes"] >= FLOOR_CLASSES

    def test_total_methods_meets_floor(self, default_build):
        """At least the 3506 methods the complete probe measured."""
        assert default_build.stats["total_methods"] >= FLOOR_METHODS


# ---------------------------------------------------------------------------
# (E) The silent-no-op trap is closed
# ---------------------------------------------------------------------------


class TestDefTimeBindingTrap:
    """The module global must be resolved at call time, not at def time."""

    def test_constructor_default_is_a_sentinel_not_a_bound_cap(self):
        """The sentinel, not a cap value, is frozen into __init__.__defaults__."""
        defaults = CallGraphBuilder.__init__.__defaults__
        assert defaults is not None and len(defaults) == 1
        assert defaults[0] is legacy._MODULE_DEFAULT, (
            "anything other than the sentinel frozen into __defaults__ reintroduces the "
            "def-time trap: rebinding MAX_FILES would be a silent no-op again"
        )

    def test_shipping_default_is_uncapped(self):
        """Constructing with no argument yields no file cap."""
        assert CallGraphBuilder(PROJECT_ROOT).max_files is None

    def test_module_global_rebind_is_now_honoured(self, monkeypatch):
        """Rebinding MAX_FILES changes discovery instead of being ignored.

        The probe MEASURED that this rebind was a silent no-op before the fix
        (still 300 files). Observing it take effect is what demonstrates the
        trap is closed. It is used here as evidence about the binding, never
        as the mechanism that establishes coverage completeness.
        """
        monkeypatch.setattr(legacy, "MAX_FILES", 5)
        discovered = CallGraphBuilder(PROJECT_ROOT)._discover_files()
        assert len(discovered) == 5

    def test_explicit_kwarg_still_overrides_the_module_global(self, monkeypatch):
        """An explicit max_files wins over the module-level default."""
        monkeypatch.setattr(legacy, "MAX_FILES", 5)
        assert len(CallGraphBuilder(PROJECT_ROOT, max_files=9)._discover_files()) == 9

    def test_explicit_none_is_honoured_as_uncapped(self, monkeypatch):
        """Passing None explicitly means uncapped, not "use the module default"."""
        monkeypatch.setattr(legacy, "MAX_FILES", 5)
        assert len(CallGraphBuilder(PROJECT_ROOT, max_files=None)._discover_files()) > 5


# ---------------------------------------------------------------------------
# Oracle independence
# ---------------------------------------------------------------------------


class TestOracleIndependence:
    """The oracle must be able to disagree with the builder."""

    def test_no_eligibility_rule_is_imported_from_the_builder(self):
        """This module's source imports none of the builder's eligibility rules."""
        source = Path(__file__).read_text(encoding="utf-8")
        import_lines = [line for line in source.splitlines() if line.startswith(("import ", "from "))]
        forbidden = ("EXCLUDED_DIRS", "MAX_FILE_SIZE_KB", "SUPPORTED_EXTENSIONS", "MAX_FILES", "parsers.config")
        for line in import_lines:
            for name in forbidden:
                assert name not in line, "oracle must not import the builder's eligibility rule %r (%r)" % (name, line)

    def test_oracle_ignores_the_builders_excluded_dirs(self, monkeypatch):
        """Emptying the builder's EXCLUDED_DIRS does not move the oracle."""
        before = enumerate_eligible_sources(PROJECT_ROOT)
        monkeypatch.setattr(legacy, "EXCLUDED_DIRS", set())
        assert enumerate_eligible_sources(PROJECT_ROOT) == before

    def test_oracle_ignores_the_builders_file_size_cap(self, monkeypatch):
        """Zeroing the builder's size cap does not move the oracle."""
        before = enumerate_eligible_sources(PROJECT_ROOT)
        monkeypatch.setattr(legacy, "MAX_FILE_SIZE_KB", 0)
        assert enumerate_eligible_sources(PROJECT_ROOT) == before


# ---------------------------------------------------------------------------
# Negative tests -- every check above is observed failing
# ---------------------------------------------------------------------------


def _build_wide_star_graph(fanout):
    """Build a 2-level star call graph: root calls c0 .. c(fanout-1).

    Args:
        fanout: Number of leaf callees hanging off the single root.

    Returns:
        CallGraph with resolved edges already populated.
    """
    graph = CallGraph()
    graph.methods["star.py::root"] = make_method_node("star.py::root", "root", "star.py", line=1, parent_class=None)
    for index in range(fanout):
        fqn = "star.py::c%d" % index
        graph.methods[fqn] = make_method_node(fqn, "c%d" % index, "star.py", line=index + 2, parent_class=None)
        graph.edges.append(make_call_edge("star.py::root", fqn, line=index + 2))
    graph._resolved_edges = list(graph.edges)
    return graph


class TestChecksCanFail:
    """A check never observed failing is indistinguishable from a no-op."""

    def test_coverage_check_fails_on_a_capped_build(self):
        """Set equality is violated when discovery is capped at 50 files."""
        capped = run_captured_build(PROJECT_ROOT, max_files=50)
        expected = enumerate_eligible_sources(PROJECT_ROOT)

        assert expected - capped.analysed_files, "capped build must miss files, otherwise (A) proves nothing"

    def test_canary_check_fails_on_a_capped_build(self):
        """The sdlc_pipeline canary is incomplete when discovery is capped."""
        capped = run_captured_build(PROJECT_ROOT, max_files=50)
        expected = {path for path in enumerate_eligible_sources(PROJECT_ROOT) if path.startswith(CANARY_PREFIX)}
        analysed = {path for path in capped.analysed_files if path.startswith(CANARY_PREFIX)}

        assert expected ^ analysed, "capped build must break the canary, otherwise (B) proves nothing"

    def test_a_capped_build_is_detectably_smaller_than_a_complete_one(self, default_build):
        """Truncation is detectable, measured against this same run's complete build.

        This control was previously anchored to the frozen FLOOR_* literals, and
        that anchoring eroded as the repository grew: the first
        TRUNCATED_BASELINE_FILES discovered files accumulate methods until a
        capped build clears a floor measured on a smaller tree. Its margin fell
        from 662 methods on 2026-08-01 to 30 BELOW zero on 2026-08-03, at which
        point the control failed while nothing it guards had regressed.

        Anchoring both sides to the same run removes the erosion entirely: a
        capped build is smaller than a complete one at every repository size.
        """
        capped = run_captured_build(PROJECT_ROOT, max_files=TRUNCATED_BASELINE_FILES)

        assert capped.stats["files_analyzed"] < default_build.stats["files_analyzed"]
        assert capped.stats["total_methods"] < default_build.stats["total_methods"]

    def test_def_time_binding_is_still_demonstrably_a_silent_no_op(self, monkeypatch):
        """Reproduce the pre-fix binding and watch the rebind be ignored.

        A default bound at function-definition time keeps whatever the module
        global held at that moment, no matter what it becomes afterwards. That
        is exactly what the probe MEASURED against the shipping builder, and
        reproducing it here is what makes the (E) assertions discriminating
        rather than vacuously true: the same rebind that this function ignores
        is the one the fixed constructor honours.
        """

        def pre_fix_cap_reader(max_files=legacy.MAX_FILES):
            """Return the cap the way the pre-fix constructor resolved it."""
            return max_files

        monkeypatch.setattr(legacy, "MAX_FILES", 5)

        assert pre_fix_cap_reader() != 5, "the def-time reproduction must ignore the rebind"
        assert CallGraphBuilder(PROJECT_ROOT).max_files == 5, "the fixed constructor must honour the rebind"

    def test_truncation_check_fails_when_a_max_paths_cap_is_in_force(self):
        """The log-capture assertion observes the record it exists to forbid."""
        logger = logging.getLogger(GRAPH_MODEL_LOGGER)
        collector = RecordCollector()
        previous_level = logger.level
        logger.addHandler(collector)
        logger.setLevel(logging.DEBUG)
        try:
            _build_wide_star_graph(fanout=10).compute_call_paths(max_paths=2)
        finally:
            logger.removeHandler(collector)
            logger.setLevel(previous_level)

        assert truncation_records(
            collector.records
        ), "the truncation record must be observable, otherwise (C) is a no-op"

    def test_uncapped_traversal_of_the_same_graph_emits_nothing(self):
        """The same graph run uncapped emits no truncation record."""
        logger = logging.getLogger(GRAPH_MODEL_LOGGER)
        collector = RecordCollector()
        previous_level = logger.level
        logger.addHandler(collector)
        logger.setLevel(logging.DEBUG)
        try:
            _build_wide_star_graph(fanout=10).compute_call_paths()
        finally:
            logger.removeHandler(collector)
            logger.setLevel(previous_level)

        assert truncation_records(collector.records) == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""Six explicit slash-command entry points (PRD FR-7 / SRS FR-17, issue V2-026).

WHAT THE TWO ACCEPTANCE CRITERIA ASK, AND WHAT EACH LAYER CAN ANSWER
--------------------------------------------------------------------
AC 1: each of the 6 named entry points is invocable by name and reaches its
pipeline steps.
AC 2: the full-pipeline command executes Steps 0 through 8 in order.

Three layers exist here, and they are kept apart on purpose because only the
first two can be measured today:

1. THE PLAN LAYER, measured. ``plugin/scripts/pipeline_entry.py`` binds each of
   the six names to the steps it owns and to a concrete engine dispatch. The
   plans are checked against each other (the five phases partition Steps 0-8 in
   order, with no gap and no overlap) and against the dispatch each one builds.

2. THE GRAPH LAYER, measured. ``create_flow_graph(hook_mode=False)`` is built
   and its step nodes and edges are read. Step ordering is asserted as a
   reachability property -- for every i < j, some step-j node is reachable from
   a step-i node and no step-i node is reachable from any step-j node -- which
   is independent of any tie-break in a topological sort. The full-pipeline
   command's declared plan must equal the step set the real graph carries.
   Nothing here INVOKES the graph: a real run creates a GitHub issue, a branch,
   a pull request and a merge.

3. THE INVOCATION LAYER, BLOCKED. Whether Claude Code discovers ``/plan`` and
   the other five from an installed plugin needs a live ``claude plugin
   install``. The project owner ruled that no live install/uninstall cycle may
   be run: install writes ``enabledPlugins`` and ``extraKnownMarketplaces`` into
   a settings scope and uninstall only empties them, plus it leaves an orphaned
   cache directory. The blocked test below is complete and skips LOUDLY, and a
   rehearsal drives its identical body with synthetic input requiring both a
   clean and a dirty verdict.

THE STANDING OBLIGATION FROM V2-017
-----------------------------------
Every FR-17 command runs the ADR-020 layer-2 start-up check first. It is proven
here to be the SAME function object the three earlier commands call, not a copy,
and to start no process: every spawn and socket entry point is replaced and
call-counted while it runs.

No test in this module writes to a real settings file. Every settings path is a
tmp_path, and a module-scoped fixture hashes all three live settings files
before and after.
"""

import hashlib
import importlib.util
import json
import os
import re
import shlex
import socket
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = REPO_ROOT / "plugin"
SCRIPT_DIR = PLUGIN_ROOT / "scripts"
COMMANDS_DIR = PLUGIN_ROOT / "commands"
ENTRY_SCRIPT = SCRIPT_DIR / "pipeline_entry.py"
SUBGRAPH_SOURCE = REPO_ROOT / "langgraph_engine" / "sdlc_pipeline" / "subgraph.py"
PROCEDURE_DOC = REPO_ROOT / "docs" / "guides" / "fr17-entry-point-invocation-verification.md"

LIVE_INSTALL_ENV = "CWE_ALLOW_LIVE_PLUGIN_INSTALL"
DISCOVERED_COMMANDS_ENV = "CWE_FR17_DISCOVERED_COMMANDS"

PRE_EXISTING_COMMANDS = ("about", "doctor", "register-mcp", "unregister-mcp")

STEP_NODE_PATTERN = re.compile(r"^sdlc_step(\d+)_")
DRY_RUN_GUARD_PATTERN = re.compile(r"step_number\s*>=\s*(\d+)\s*and[^\n]*CLAUDE_DRY_RUN")

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def _load(name, path):
    """Import a module by explicit file path.

    ``plugin/scripts`` is not an importable package, and an installed plugin
    could not import it by name either, so both plugin modules are loaded by
    location.

    Args:
        name: Module name to register under.
        path: Filesystem path of the module.

    Returns:
        module: The loaded module.
    """
    if str(SCRIPT_DIR) not in sys.path:
        sys.path.insert(0, str(SCRIPT_DIR))
    spec = importlib.util.spec_from_file_location(name, str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


pipeline = _load("pipeline_entry_under_test", ENTRY_SCRIPT)
registration = sys.modules["mcp_registration"]


def _guarded_settings_paths():
    """List every live settings file that no test in this module may write.

    Returns:
        list: Absolute paths, de-duplicated, order stable.
    """
    homes = [Path.home() / ".claude"]
    try:
        from utils.path_resolver import get_claude_home

        homes.append(Path(get_claude_home()))
    except Exception:
        pass

    candidates = []
    for home in homes:
        candidates.append(home / "settings.json")
        candidates.append(home / "settings.local.json")
    candidates.append(REPO_ROOT / ".claude" / "settings.local.json")

    seen = []
    for candidate in candidates:
        resolved = candidate.resolve() if candidate.exists() else candidate
        if resolved not in seen:
            seen.append(resolved)
    return seen


def _digest(path):
    """Return the sha256 of a file, or a marker when it is absent.

    Args:
        path: File to digest.

    Returns:
        str: Hex digest, or ``ABSENT``.
    """
    try:
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()
    except FileNotFoundError:
        return "ABSENT"


@pytest.fixture(scope="module", autouse=True)
def live_settings_are_never_touched():
    """Fail the module if any live settings file changes while it runs.

    Yields:
        None
    """
    paths = _guarded_settings_paths()
    before = {path.as_posix(): _digest(path) for path in paths}
    yield
    after = {path.as_posix(): _digest(path) for path in paths}
    assert before == after, "a test modified a live settings file: {0} -> {1}".format(before, after)


def _settings(with_hook, servers=None):
    """Build a settings document with or without a PreToolUse hook.

    Args:
        with_hook: Whether a PreToolUse entry is present.
        servers: Optional mcpServers block.

    Returns:
        dict: The settings document.
    """
    document = {"model": "opus"}
    if with_hook:
        document["hooks"] = {"PreToolUse": [{"matcher": "*", "hooks": []}]}
    if servers:
        document["mcpServers"] = servers
    return document


def _write_json(path, document):
    """Write a JSON document and return its path.

    Args:
        path: Destination path.
        document: Object to serialise.

    Returns:
        Path: The written path.
    """
    Path(path).write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
    return Path(path)


def _fake_engine_root(base):
    """Create a directory shaped like an engine checkout.

    Args:
        base: Directory to create the tree under.

    Returns:
        Path: The engine root.
    """
    root = Path(base) / "engine"
    entry = root / pipeline.ENGINE_ENTRY
    entry.parent.mkdir(parents=True, exist_ok=True)
    entry.write_text("import sys\nsys.exit(0)\n", encoding="utf-8")
    return root


def _recording_engine_root(base):
    """Create an engine stand-in that records how it was invoked.

    The recorder is what turns "the dispatcher built the right argv" into "the
    dispatcher executed the right argv". It writes the arguments and the two
    environment values the plan controls, then exits zero.

    Args:
        base: Directory to create the tree under.

    Returns:
        tuple: (engine root, path the invocation record is written to).
    """
    root = Path(base) / "recording-engine"
    record = root / "invocation.json"
    entry = root / pipeline.ENGINE_ENTRY
    entry.parent.mkdir(parents=True, exist_ok=True)
    source = "\n".join(
        [
            "import json, os, sys",
            "payload = dict(",
            "    argv=sys.argv[1:],",
            "    cwd=os.getcwd(),",
            '    hook_mode=os.environ.get("CLAUDE_HOOK_MODE"),',
            '    dry_run_env=os.environ.get("CLAUDE_DRY_RUN"),',
            ")",
            "target = RECORD_PATH",
            'with open(target, "w", encoding="utf-8") as handle:',
            "    json.dump(payload, handle)",
            "sys.exit(0)",
            "",
        ]
    ).replace("RECORD_PATH", repr(str(record)))
    entry.write_text(source, encoding="utf-8")
    return root, record


def _run_cli(args, settings_path=None, plugin_root=None):
    """Run the entry-point script as a real process against scratch files only.

    Args:
        args: Sub-command and flags.
        settings_path: Scratch settings path, or None for the default.
        plugin_root: Plugin root override, or None for the real one.

    Returns:
        subprocess.CompletedProcess: The finished process.
    """
    argv = [sys.executable, str(ENTRY_SCRIPT), "--plugin-root", str(plugin_root or PLUGIN_ROOT)]
    if settings_path is not None:
        argv.extend(["--settings", str(settings_path)])
    return subprocess.run(argv + list(args), capture_output=True, text=True, timeout=120)


class TestTheSixNamesAreExactlySix:
    """Specificity in both directions on the entry-point name set."""

    def test_the_six_names_are_the_five_phases_plus_the_full_pipeline(self):
        """The count and the names both come from PRD FR-7 / SRS FR-17."""
        assert pipeline.PHASE_COMMANDS == ("plan", "implement", "review", "document", "release")
        assert pipeline.FULL_PIPELINE_COMMAND == "run-pipeline"
        assert len(pipeline.command_names()) == 6
        assert set(pipeline.command_names()) == set(pipeline.COMMAND_PLANS)

    def test_every_named_entry_point_has_a_command_file(self):
        """SPECIFICITY: a plan with no file is a command nobody can invoke."""
        for name in pipeline.command_names():
            path = COMMANDS_DIR / "{0}.md".format(name)
            assert path.is_file(), "missing command file: {0}".format(path.as_posix())

    def test_no_command_file_lacks_a_plan_except_the_four_that_predate_this(self):
        """SPECIFICITY, the other direction: an unplanned command file is caught.

        ``about``, ``doctor``, ``register-mcp`` and ``unregister-mcp`` are not
        FR-17 entry points and are named here rather than pattern-excluded, so a
        seventh pipeline command added without a plan fails this test.
        """
        on_disk = {path.stem for path in COMMANDS_DIR.glob("*.md")}
        assert on_disk - set(pipeline.command_names()) == set(PRE_EXISTING_COMMANDS)

    def test_negative_an_unknown_name_is_rejected_rather_than_defaulted(self):
        """NEGATIVE: plan_for cannot silently answer for a name it has no plan for."""
        with pytest.raises(pipeline.PipelineEntryError) as excinfo:
            pipeline.plan_for("deploy")
        assert "deploy" in str(excinfo.value)
        for name in pipeline.command_names():
            assert name in str(excinfo.value)

    def test_specificity_each_of_the_six_resolves(self):
        """SPECIFICITY: the rejection above is about the name, not about all names."""
        for name in pipeline.command_names():
            assert pipeline.plan_for(name)["steps"]


def partition_problems(plans, phase_names, full_name):
    """Report where the phase plans fail to partition the full pipeline plan.

    The property asserted is exactly what SRS FR-17 implies: five phases plus one
    command that runs everything, so concatenating the five phases in declared
    order must reproduce the full command's step list with no gap, no overlap and
    no reordering.

    Args:
        plans: Mapping of command name to plan record.
        phase_names: Ordered phase command names.
        full_name: The full-pipeline command name.

    Returns:
        list: One message per violation.
    """
    concatenated = []
    for name in phase_names:
        concatenated.extend(plans[name]["steps"])
    full = list(plans[full_name]["steps"])
    problems = []
    if len(set(concatenated)) != len(concatenated):
        problems.append("phase plans overlap: {0}".format(concatenated))
    if sorted(set(concatenated)) != sorted(set(full)):
        problems.append("phase plans do not cover the full pipeline: {0} vs {1}".format(concatenated, full))
    if concatenated != full:
        problems.append("phase plans are not in pipeline order: {0} vs {1}".format(concatenated, full))
    return problems


class TestThePlansPartitionThePipeline:
    """AC 1 at the plan layer: every step is owned by exactly one phase."""

    def test_the_five_phases_partition_steps_0_to_8_in_order(self):
        """No gap, no overlap, no reordering."""
        assert partition_problems(pipeline.COMMAND_PLANS, pipeline.PHASE_COMMANDS, pipeline.FULL_PIPELINE_COMMAND) == []

    def test_the_full_pipeline_plan_is_steps_0_through_8(self):
        """AC 2 at the plan layer."""
        assert pipeline.COMMAND_PLANS[pipeline.FULL_PIPELINE_COMMAND]["steps"] == tuple(range(0, 9))

    def test_every_owned_step_is_actually_performed_by_the_dispatch(self):
        """A phase that declared a step its dispatch cannot reach is caught."""
        for name in pipeline.command_names():
            report = pipeline.plan_report(name)
            assert report["unreached"] == [], "{0} cannot reach {1}".format(name, report["unreached"])

    def test_exactly_two_entry_points_are_exact(self):
        """The engine has one graph entry, so only a prefix phase can be exact."""
        exact = [name for name in pipeline.command_names() if pipeline.plan_report(name)["exact"]]
        assert exact == ["plan", "run-pipeline"]

    def test_every_step_carries_a_label(self):
        """A plan naming a step the label table does not know is caught."""
        assert set(pipeline.STEP_LABELS) == set(range(0, 9))
        for name in pipeline.command_names():
            for step in pipeline.COMMAND_PLANS[name]["steps"]:
                assert pipeline.STEP_LABELS[step]

    def test_mutation_one_plan_per_command_would_not_partition(self):
        """MUTATION: give every phase the whole pipeline and the check must fail.

        Stated because a partition check that cannot fail is decoration. The
        mutant is the mistake a copy-paste author actually makes.
        """
        mutant = {name: {"steps": tuple(range(0, 9))} for name in pipeline.command_names()}
        assert partition_problems(mutant, pipeline.PHASE_COMMANDS, pipeline.FULL_PIPELINE_COMMAND)

    def test_negative_a_gap_in_the_phase_plans_is_caught(self):
        """NEGATIVE: dropping one step from one phase is caught."""
        mutant = {name: dict(plan) for name, plan in pipeline.COMMAND_PLANS.items()}
        mutant["review"] = dict(mutant["review"], steps=(5,))
        problems = partition_problems(mutant, pipeline.PHASE_COMMANDS, pipeline.FULL_PIPELINE_COMMAND)
        assert problems
        assert any("do not cover" in problem for problem in problems)

    def test_negative_two_phases_owning_one_step_is_caught(self):
        """NEGATIVE: an overlap is caught, not absorbed by the coverage check."""
        mutant = {name: dict(plan) for name, plan in pipeline.COMMAND_PLANS.items()}
        mutant["document"] = dict(mutant["document"], steps=(6, 7))
        problems = partition_problems(mutant, pipeline.PHASE_COMMANDS, pipeline.FULL_PIPELINE_COMMAND)
        assert problems
        assert any("overlap" in problem for problem in problems)


def step_nodes(node_names):
    """Map each pipeline step number to the graph nodes that carry it.

    Args:
        node_names: Iterable of graph node identifiers.

    Returns:
        dict: Step number to a set of node identifiers.
    """
    found = {}
    for name in node_names:
        match = STEP_NODE_PATTERN.match(name)
        if match:
            found.setdefault(int(match.group(1)), set()).add(name)
    return found


def forward_edges(edges, by_step):
    """Drop edges that run backwards between step nodes.

    A failed Step 5 review routes back to Step 4. That retry edge is a designed
    cycle, not an ordering violation, so it is excluded before the ordering
    property is evaluated -- and excluded by rule rather than by name, so a
    second retry edge added later is handled the same way.

    Args:
        edges: Iterable of (source, target) pairs.
        by_step: Output of ``step_nodes``.

    Returns:
        list: The remaining edges.
    """
    number = {}
    for step, names in by_step.items():
        for name in names:
            number[name] = step
    return [
        (source, target)
        for source, target in edges
        if not (source in number and target in number and number[target] < number[source])
    ]


def reachable_from(start, edges):
    """Return every node reachable from a start node over a set of edges.

    Args:
        start: Node identifier to start from.
        edges: Iterable of (source, target) pairs.

    Returns:
        set: Reachable node identifiers, excluding the start node itself unless
        a cycle returns to it.
    """
    adjacency = {}
    for source, target in edges:
        adjacency.setdefault(source, set()).add(target)
    seen = set()
    frontier = list(adjacency.get(start, ()))
    while frontier:
        node = frontier.pop()
        if node in seen:
            continue
        seen.add(node)
        frontier.extend(adjacency.get(node, ()))
    return seen


def ordering_problems(by_step, edges):
    """Report where the step nodes fail to run in ascending step order.

    Order is asserted as a reachability property rather than as a position in a
    topological sort, because a topological sort has tie-breaks and this
    question does not.

    Args:
        by_step: Output of ``step_nodes``.
        edges: Forward edges between graph nodes.

    Returns:
        list: One message per violation.
    """
    problems = []
    steps = sorted(by_step)
    closure = {}
    for names in by_step.values():
        for name in names:
            closure[name] = reachable_from(name, edges)
    for index, earlier in enumerate(steps):
        for later in steps[index + 1 :]:
            forward = any(closure[a] & by_step[later] for a in by_step[earlier])
            if not forward:
                problems.append("Step {0} does not reach Step {1}".format(earlier, later))
            backward = [b for b in by_step[later] if closure[b] & by_step[earlier]]
            if backward:
                problems.append("Step {0} reaches back to Step {1} via {2}".format(later, earlier, sorted(backward)))
    return problems


@pytest.fixture(scope="module")
def measured_graph():
    """Build the full-mode pipeline graph once and read its structure.

    The graph is BUILT, never invoked. A real invocation creates a GitHub issue,
    a branch, a pull request and a merge.

    Returns:
        dict: by_step mapping and the forward edge list.
    """
    from langgraph_engine.orchestrator import create_flow_graph

    drawn = create_flow_graph(hook_mode=False).get_graph()
    names = list(drawn.nodes)
    edges = [(edge.source, edge.target) for edge in drawn.edges]
    by_step = step_nodes(names)
    return {"by_step": by_step, "edges": forward_edges(edges, by_step), "nodes": names}


class TestTheGraphCarriesStepsZeroToEightInOrder:
    """AC 2 at the graph layer: measured from the real StateGraph."""

    def test_the_full_mode_graph_carries_exactly_steps_0_to_8(self, measured_graph):
        """The step set is measured, not carried forward from CLAUDE.md."""
        assert sorted(measured_graph["by_step"]) == list(range(0, 9))

    def test_the_steps_are_reachable_in_ascending_order(self, measured_graph):
        """For every i < j: j is reachable from i, and i is not reachable from j."""
        assert ordering_problems(measured_graph["by_step"], measured_graph["edges"]) == []

    def test_the_full_pipeline_plan_equals_the_measured_graph(self, measured_graph):
        """The declared plan is checked against the graph, not against a document."""
        measured = tuple(sorted(measured_graph["by_step"]))
        assert pipeline.COMMAND_PLANS[pipeline.FULL_PIPELINE_COMMAND]["steps"] == measured

    def test_the_retry_edge_exists_and_is_the_only_backward_edge(self, measured_graph):
        """The exclusion rule is checked against what it actually excludes."""
        from langgraph_engine.orchestrator import create_flow_graph

        drawn = create_flow_graph(hook_mode=False).get_graph()
        all_edges = [(edge.source, edge.target) for edge in drawn.edges]
        excluded = [pair for pair in all_edges if pair not in measured_graph["edges"]]
        assert excluded == [("sdlc_step5_retry", "sdlc_step4_implementation")]

    def test_negative_a_planted_backward_edge_is_caught(self):
        """NEGATIVE: the ordering checker can fail."""
        by_step = {0: {"sdlc_step0_a"}, 1: {"sdlc_step1_a"}}
        edges = [("sdlc_step0_a", "sdlc_step1_a"), ("sdlc_step1_a", "sdlc_step0_a")]
        problems = ordering_problems(by_step, edges)
        assert problems
        assert any("reaches back" in problem for problem in problems)

    def test_negative_a_missing_forward_path_is_caught(self):
        """NEGATIVE: an unreachable later step is caught, not silently passed."""
        by_step = {0: {"sdlc_step0_a"}, 1: {"sdlc_step1_a"}}
        problems = ordering_problems(by_step, [])
        assert problems
        assert any("does not reach" in problem for problem in problems)

    def test_specificity_a_correct_chain_produces_no_problems(self):
        """SPECIFICITY: the checker passes a graph that is genuinely ordered."""
        by_step = {0: {"a0"}, 1: {"a1"}, 2: {"a2"}}
        edges = [("a0", "a1"), ("a1", "a2")]
        assert ordering_problems(by_step, edges) == []


class TestTheDryRunThresholdIsNotCopiedFromMemory:
    """The plan layer mirrors an engine constant, so it needs a drift guard."""

    def _extract(self, text):
        """Pull the dry-run skip threshold out of engine source text.

        Args:
            text: Source text to search.

        Returns:
            int: The threshold.

        Raises:
            AssertionError: No guard was found.
        """
        match = DRY_RUN_GUARD_PATTERN.search(text)
        assert match is not None, "no CLAUDE_DRY_RUN step guard found"
        return int(match.group(1))

    def test_the_mirrored_threshold_matches_the_engine(self):
        """``plan``'s exactness rests on this number being right."""
        measured = self._extract(SUBGRAPH_SOURCE.read_text(encoding="utf-8"))
        assert measured == pipeline.DRY_RUN_SKIP_FROM

    def test_the_named_source_file_is_the_one_that_was_read(self):
        """The constant records where it came from; that path must be real."""
        assert (REPO_ROOT / pipeline.DRY_RUN_GUARD_SOURCE).is_file()

    def test_negative_a_changed_threshold_is_caught(self):
        """NEGATIVE: the drift guard can fail."""
        planted = 'if step_number >= 4 and _os.environ.get("CLAUDE_DRY_RUN") == "1":'
        assert self._extract(planted) != pipeline.DRY_RUN_SKIP_FROM

    def test_negative_a_removed_guard_is_caught_rather_than_passing(self):
        """NEGATIVE: extraction fails loudly instead of finding nothing and passing."""
        with pytest.raises(AssertionError):
            self._extract("# the guard was deleted\n")


class TestTheStartUpCheckIsTheSameOneAndSpawnsNothing:
    """The standing obligation inherited from V2-017."""

    def test_the_detector_is_the_shipped_function_not_a_copy(self):
        """Identity, not equivalence. Two detectors is one too many."""
        assert pipeline.push_gate_precondition_line is registration.push_gate_precondition_line

    def test_the_detector_came_from_the_plugins_own_scripts_directory(self):
        """The identity above is only meaningful if the source is the shipped one."""
        assert Path(registration.__file__).resolve() == (SCRIPT_DIR / "mcp_registration.py").resolve()

    def test_it_speaks_once_when_no_local_push_gate_is_in_place(self, tmp_path):
        """POSITIVE: the unsafe state produces exactly one line."""
        path = _write_json(tmp_path / "s.json", _settings(False))
        line = pipeline.start_up_check_line(PLUGIN_ROOT, path)
        assert line is not None
        assert line.startswith("[UNSAFE]")
        assert "\n" not in line

    def test_specificity_it_says_nothing_when_the_state_is_safe(self, tmp_path):
        """SPECIFICITY: a detector that speaks every time is one nobody reads."""
        path = _write_json(tmp_path / "s.json", _settings(True))
        assert pipeline.start_up_check_line(PLUGIN_ROOT, path) is None

    def test_it_says_nothing_rather_than_failing_on_an_unreadable_settings_file(self, tmp_path):
        """A start-up check must never be what stops the command it precedes."""
        path = tmp_path / "s.json"
        path.write_text("{ not json", encoding="utf-8")
        assert pipeline.start_up_check_line(PLUGIN_ROOT, path) is None

    def test_no_process_or_socket_primitive_is_invoked(self, tmp_path, monkeypatch):
        """Every spawn and socket entry point is replaced and call-counted."""
        calls = []

        def _forbid(name):
            """Build a replacement that records its own invocation.

            Args:
                name: Entry-point name to record.

            Returns:
                callable: A stand-in that records and raises.
            """

            def _blocked(*args, **kwargs):
                calls.append(name)
                raise AssertionError("start-up check invoked {0}".format(name))

            return _blocked

        monkeypatch.setattr(subprocess, "Popen", _forbid("subprocess.Popen"))
        monkeypatch.setattr(subprocess, "run", _forbid("subprocess.run"))
        monkeypatch.setattr(subprocess, "call", _forbid("subprocess.call"))
        monkeypatch.setattr(subprocess, "check_output", _forbid("subprocess.check_output"))
        monkeypatch.setattr(socket, "socket", _forbid("socket.socket"))
        monkeypatch.setattr(os, "system", _forbid("os.system"))
        for name in ("fork", "posix_spawn", "spawnv", "spawnve"):
            if hasattr(os, name):
                monkeypatch.setattr(os, name, _forbid("os." + name))

        path = _write_json(tmp_path / "s.json", _settings(False))
        assert pipeline.start_up_check_line(PLUGIN_ROOT, path) is not None
        assert calls == []

    def test_negative_the_interception_harness_would_catch_a_spawn(self, monkeypatch):
        """NEGATIVE: prove the harness above is not vacuous."""
        calls = []

        def _blocked(*args, **kwargs):
            """Record an invocation and refuse it.

            Returns:
                None
            """
            calls.append("subprocess.run")
            raise AssertionError("spawned")

        monkeypatch.setattr(subprocess, "run", _blocked)
        with pytest.raises(AssertionError):
            subprocess.run([sys.executable, "-c", "pass"])
        assert calls == ["subprocess.run"]

    def test_the_check_runs_before_the_engine_is_resolved(self, tmp_path, monkeypatch):
        """It must still speak when the command is about to refuse.

        A check that only runs on the success path is absent exactly when the
        session is in trouble.
        """
        monkeypatch.delenv(pipeline.ENGINE_ROOT_ENV, raising=False)
        path = _write_json(tmp_path / "s.json", _settings(False))
        completed = _run_cli(["run", "run-pipeline", "--task", "x"], path)
        assert completed.returncode == pipeline.EXIT_REFUSED
        lines = [line for line in completed.stdout.splitlines() if line.strip()]
        assert lines[0].startswith("[UNSAFE]")
        assert lines[1].startswith("REFUSED:")

    def test_specificity_the_safe_state_leaves_only_the_refusal(self, tmp_path, monkeypatch):
        """SPECIFICITY: nothing extra is printed when the gate is in place."""
        monkeypatch.delenv(pipeline.ENGINE_ROOT_ENV, raising=False)
        path = _write_json(tmp_path / "s.json", _settings(True))
        completed = _run_cli(["run", "run-pipeline", "--task", "x"], path)
        lines = [line for line in completed.stdout.splitlines() if line.strip()]
        assert lines[0].startswith("REFUSED:")
        assert "[UNSAFE]" not in completed.stdout


class TestTheEngineRootIsNeverGuessed:
    """M6: a CWD-relative resolver passes every local test and fails every install."""

    def test_it_refuses_when_nothing_names_the_engine(self, monkeypatch):
        """NEGATIVE: an unresolvable root is reported, not assumed."""
        monkeypatch.delenv(pipeline.ENGINE_ROOT_ENV, raising=False)
        with pytest.raises(pipeline.PipelineEntryError) as excinfo:
            pipeline.resolve_engine_root(None)
        message = str(excinfo.value)
        assert pipeline.ENGINE_ROOT_ENV in message
        assert pipeline.ENGINE_ENTRY.as_posix() in message

    def test_specificity_an_explicit_root_resolves(self, tmp_path, monkeypatch):
        """SPECIFICITY: the refusal is about absence, not about all inputs."""
        monkeypatch.delenv(pipeline.ENGINE_ROOT_ENV, raising=False)
        root = _fake_engine_root(tmp_path)
        assert pipeline.resolve_engine_root(str(root)) == root.resolve()

    def test_the_environment_variable_resolves_it(self, tmp_path, monkeypatch):
        """The second candidate is honoured when the flag is absent."""
        root = _fake_engine_root(tmp_path)
        monkeypatch.setenv(pipeline.ENGINE_ROOT_ENV, str(root))
        assert pipeline.resolve_engine_root(None) == root.resolve()

    def test_negative_the_working_directory_is_never_used(self, tmp_path, monkeypatch):
        """NEGATIVE: standing inside an engine checkout does not resolve it.

        This is the correct-by-coincidence failure: an author's own dev loop runs
        from the repository root, so a CWD-based resolver passes there and
        resolves to nothing for every real installed user.
        """
        monkeypatch.delenv(pipeline.ENGINE_ROOT_ENV, raising=False)
        root = _fake_engine_root(tmp_path)
        monkeypatch.chdir(root)
        with pytest.raises(pipeline.PipelineEntryError):
            pipeline.resolve_engine_root(None)

    def test_negative_a_directory_without_the_entry_point_is_refused(self, tmp_path, monkeypatch):
        """NEGATIVE: existence of the directory is not enough."""
        monkeypatch.delenv(pipeline.ENGINE_ROOT_ENV, raising=False)
        empty = tmp_path / "not-an-engine"
        empty.mkdir()
        with pytest.raises(pipeline.PipelineEntryError):
            pipeline.resolve_engine_root(str(empty))


class TestTheDispatchMatchesThePlan:
    """What each entry point actually asks the engine to do."""

    def test_the_full_pipeline_dispatch_asks_for_every_step(self, tmp_path):
        """AC 2 at the dispatch layer: hook mode off, dry run off."""
        root = _fake_engine_root(tmp_path)
        dispatch = pipeline.build_dispatch("run-pipeline", "a task", root)
        assert dispatch["env"] == {"CLAUDE_HOOK_MODE": "0"}
        assert "--dry-run" not in dispatch["argv"]
        assert dispatch["argv"][-1] == "--message=a task"

    def test_the_plan_dispatch_stops_before_anything_is_tracked(self, tmp_path):
        """``plan`` is exact only because it dispatches with the dry-run control."""
        root = _fake_engine_root(tmp_path)
        dispatch = pipeline.build_dispatch("plan", "a task", root)
        assert dispatch["env"] == {"CLAUDE_HOOK_MODE": "1"}
        assert "--dry-run" in dispatch["argv"]

    def test_hook_mode_is_used_only_as_a_stop_point_selector(self):
        """The value is derived from the plan's stop point, nothing else."""
        assert pipeline.hook_mode_value({"stop_after": 3}) == "1"
        assert pipeline.hook_mode_value({"stop_after": 8}) == "0"
        assert pipeline.hook_mode_value({"stop_after": 9}) == "0"

    def test_the_session_and_project_flags_reach_the_engine(self, tmp_path):
        """A resumed session must be passed through, not dropped."""
        root = _fake_engine_root(tmp_path)
        dispatch = pipeline.build_dispatch("implement", "t", root, session_id="s-1", project_root="/p")
        assert "--session-id=s-1" in dispatch["argv"]
        assert "--project=/p" in dispatch["argv"]

    def test_negative_a_slash_task_is_refused_rather_than_silently_discarded(self):
        """NEGATIVE: the engine discards these, so they are stopped here.

        ``scripts/3-level-flow.py`` exits zero without running anything when the
        message starts with "/" or "!". Dispatching one would produce a
        successful-looking run that reached no step at all.
        """
        for task in ("/commit", "!git status", "   /clear"):
            with pytest.raises(pipeline.PipelineEntryError) as excinfo:
                pipeline.validate_task(task)
            assert "discards" in str(excinfo.value)

    def test_negative_an_empty_task_is_refused(self):
        """NEGATIVE: a blank task is caught before it becomes an empty run."""
        for task in ("", "   ", None):
            with pytest.raises(pipeline.PipelineEntryError):
                pipeline.validate_task(task)

    def test_specificity_an_ordinary_task_is_accepted(self):
        """SPECIFICITY: the refusal is about the prefix, not about punctuation."""
        for task in ("fix the login bug", "add /health endpoint", "why not!"):
            pipeline.validate_task(task)

    def test_the_full_pipeline_command_really_executes_the_engine_entry_point(self, tmp_path):
        """AC 2 at the dispatch layer, observed rather than constructed.

        A stand-in engine records the argv and environment it was actually
        started with. This is the furthest AC 2 can be taken without running the
        real engine, which creates a GitHub issue, a branch, a pull request and a
        merge.
        """
        root, record = _recording_engine_root(tmp_path)
        settings_path = _write_json(tmp_path / "s.json", _settings(True))
        completed = _run_cli(
            ["run", "run-pipeline", "--task", "a scratch task", "--engine-root", str(root)],
            settings_path,
        )

        assert completed.returncode == pipeline.EXIT_OK, completed.stdout + completed.stderr
        payload = json.loads(record.read_text(encoding="utf-8"))
        assert payload["argv"] == ["--invoked-by=run-pipeline", "--message=a scratch task"]
        assert payload["hook_mode"] == "0"
        assert payload["dry_run_env"] is None

    def test_the_plan_command_really_executes_with_the_dry_run_control(self, tmp_path):
        """The one control that makes ``plan`` exact is observed, not assumed."""
        root, record = _recording_engine_root(tmp_path)
        settings_path = _write_json(tmp_path / "s.json", _settings(True))
        completed = _run_cli(
            ["run", "plan", "--task", "a scratch task", "--engine-root", str(root)],
            settings_path,
        )

        assert completed.returncode == pipeline.EXIT_OK, completed.stdout + completed.stderr
        payload = json.loads(record.read_text(encoding="utf-8"))
        assert "--dry-run" in payload["argv"]
        assert payload["hook_mode"] == "1"

    def test_negative_print_only_executes_nothing(self, tmp_path):
        """NEGATIVE: the flag the docs offer for a safe preview must be safe.

        The recorder writes its file on every start, so its absence is direct
        evidence that no process ran -- not an inference from an exit code the
        stand-in would have produced either way.
        """
        root, record = _recording_engine_root(tmp_path)
        settings_path = _write_json(tmp_path / "s.json", _settings(True))
        completed = _run_cli(
            ["run", "run-pipeline", "--task", "t", "--engine-root", str(root), "--print-only"],
            settings_path,
        )

        assert completed.returncode == pipeline.EXIT_OK
        assert not record.exists(), "print-only started the engine"

    def test_the_engine_exit_status_is_returned_rather_than_swallowed(self, tmp_path):
        """A failed run must not report success."""
        root = Path(tmp_path) / "failing-engine"
        entry = root / pipeline.ENGINE_ENTRY
        entry.parent.mkdir(parents=True, exist_ok=True)
        entry.write_text("import sys\nsys.exit(3)\n", encoding="utf-8")
        settings_path = _write_json(tmp_path / "s.json", _settings(True))

        completed = _run_cli(["run", "release", "--task", "t", "--engine-root", str(root)], settings_path)

        assert completed.returncode == 3

    def test_the_engine_is_not_started_inside_its_own_checkout(self, tmp_path, monkeypatch):
        """The pipeline must run against the user's project, not the engine repo.

        The engine entry point bootstraps its imports from its own file location
        and derives the project it works on from the working directory. A
        dispatcher that moved into the engine checkout would run the whole
        pipeline against the engine repository -- opening an issue and a branch
        on the wrong repository -- and would look correct in every other
        assertion here.
        """
        root, record = _recording_engine_root(tmp_path)
        settings_path = _write_json(tmp_path / "s.json", _settings(True))
        elsewhere = tmp_path / "the-users-project"
        elsewhere.mkdir()
        monkeypatch.chdir(elsewhere)

        completed = _run_cli(["run", "release", "--task", "t", "--engine-root", str(root)], settings_path)

        assert completed.returncode == pipeline.EXIT_OK, completed.stdout + completed.stderr
        payload = json.loads(record.read_text(encoding="utf-8"))
        assert Path(payload["cwd"]).resolve() == elsewhere.resolve()
        assert Path(payload["cwd"]).resolve() != root.resolve()

    def test_the_coverage_lines_name_the_extra_steps_rather_than_hiding_them(self):
        """A NOT EXACT command must say which steps it also runs."""
        lines = pipeline.coverage_lines("implement")
        joined = " ".join(lines)
        assert "NOT EXACT" in joined
        for step in (0, 1, 5, 6, 7, 8):
            assert "Step {0}".format(step) in joined

    def test_specificity_an_exact_command_claims_nothing_extra(self):
        """SPECIFICITY: the exact commands do not carry the warning."""
        for name in ("plan", "run-pipeline"):
            joined = " ".join(pipeline.coverage_lines(name))
            assert "EXACT" in joined
            assert "NOT EXACT" not in joined


class TestTheStoredCommandsExecute:
    """Standing rule: run each command from its STORED form, not an authored one."""

    def _stored_command(self, name, directory=None):
        """Pull the entry-point invocation out of a command file.

        Args:
            name: Entry-point name.
            directory: Directory holding the command files. Defaults to the
                shipped one; overridden only by the negative test.

        Returns:
            str: The command exactly as the document stores it.

        Raises:
            AssertionError: No stored command matched.
        """
        source = Path(directory) if directory else COMMANDS_DIR
        text = (source / "{0}.md".format(name)).read_text(encoding="utf-8")
        pattern = r"^(python .*pipeline_entry\.py\" run {0} .*)$".format(re.escape(name))
        match = re.search(pattern, text, re.MULTILINE)
        assert match, "no stored pipeline_entry command found in {0}.md".format(name)
        return match.group(1)

    def _run_stored(self, name, settings_path, engine_root):
        """Execute a stored command with only its variable parts substituted.

        ``${CLAUDE_PLUGIN_ROOT}`` is expanded the way Claude Code expands it, the
        interpreter is this one, and the placeholder task is replaced. No flag the
        shipped string does not carry is injected into it: the scratch settings
        file is supplied through ``CLAUDE_SETTINGS_FILE``, which is the same
        redirect an operator would use, so the executed argv stays the shipped
        argv plus the two flags the document itself documents.

        Args:
            name: Entry-point name.
            settings_path: Scratch settings path.
            engine_root: Engine root to dispatch against.

        Returns:
            subprocess.CompletedProcess: The finished process.
        """
        stored = self._stored_command(name).replace("${CLAUDE_PLUGIN_ROOT}", PLUGIN_ROOT.as_posix())
        argv = shlex.split(stored, posix=True)
        argv[0] = sys.executable
        argv = [part if part != "<the task>" else "a scratch task" for part in argv]
        argv.extend(["--engine-root", str(engine_root), "--print-only"])
        env = dict(os.environ)
        env["CLAUDE_SETTINGS_FILE"] = str(settings_path)
        env["CLAUDE_PLUGIN_ROOT"] = str(PLUGIN_ROOT)
        return subprocess.run(argv, capture_output=True, text=True, timeout=120, env=env)

    @pytest.mark.parametrize("name", list(pipeline.command_names()))
    def test_each_stored_command_resolves_and_reports_its_own_steps(self, name, tmp_path):
        """Every one of the six runs from the string its file ships."""
        settings_path = _write_json(tmp_path / "s.json", _settings(True))
        completed = self._run_stored(name, settings_path, _fake_engine_root(tmp_path))
        assert completed.returncode == pipeline.EXIT_OK, completed.stdout + completed.stderr
        assert completed.stdout.startswith("{0}: owns ".format(name))
        for step in pipeline.COMMAND_PLANS[name]["steps"]:
            assert "Step {0}".format(step) in completed.stdout

    @pytest.mark.parametrize("name", list(pipeline.command_names()))
    def test_each_stored_command_names_the_plugin_root_variable(self, name):
        """A bundled path resolved any other way breaks once installed."""
        assert "${CLAUDE_PLUGIN_ROOT}" in self._stored_command(name)

    @pytest.mark.parametrize("name", list(pipeline.command_names()))
    def test_each_command_file_carries_a_description(self, name):
        """The frontmatter description is what a user sees in the picker."""
        text = (COMMANDS_DIR / "{0}.md".format(name)).read_text(encoding="utf-8")
        assert text.startswith("---\n")
        assert re.search(r"^description: \S", text, re.MULTILINE)

    @pytest.mark.parametrize("name", list(pipeline.command_names()))
    def test_each_command_file_tells_the_reader_to_relay_the_unsafe_line(self, name):
        """The inherited obligation is visible in the document, not only in code."""
        text = (COMMANDS_DIR / "{0}.md".format(name)).read_text(encoding="utf-8")
        assert "[UNSAFE]" in text
        assert "verbatim" in text
        assert "register-mcp" in text

    @pytest.mark.parametrize("name", list(pipeline.command_names()))
    def test_no_command_file_describes_the_gate_as_branch_protection(self, name):
        """The scope of the missing gate must not be inflated.

        Whitespace is normalised before the match. A line-oriented version of
        this check passed five files and failed the sixth purely because the
        sentence had wrapped, which is a property of the paragraph and not of
        what it says.
        """
        text = (COMMANDS_DIR / "{0}.md".format(name)).read_text(encoding="utf-8")
        assert "not branch protection" in " ".join(text.split())

    def test_negative_the_branch_protection_check_can_fail(self, tmp_path):
        """NEGATIVE: a file that omits the disclaimer is caught."""
        text = "---\ndescription: x\n---\n\nrelay the [UNSAFE] line verbatim, run register-mcp\n"
        assert "not branch protection" not in " ".join(text.split())

    def test_negative_extraction_fails_when_the_stored_command_is_gone(self, tmp_path):
        """NEGATIVE: the extractor cannot find nothing and pass."""
        empty = tmp_path / "commands"
        empty.mkdir()
        (empty / "plan.md").write_text("# plan\n\nno command here\n", encoding="utf-8")
        with pytest.raises(AssertionError):
            self._stored_command("plan", directory=empty)

    def test_negative_extraction_rejects_a_command_for_a_different_entry_point(self, tmp_path):
        """NEGATIVE: a file whose stored command runs another command is caught.

        This is the copy-paste defect the parametrised tests above would
        otherwise absorb: six files, five of them still invoking ``plan``.
        """
        wrong = tmp_path / "commands"
        wrong.mkdir()
        (wrong / "review.md").write_text(
            '# review\n\n```\npython "${CLAUDE_PLUGIN_ROOT}/scripts/pipeline_entry.py" run plan --task "x"\n```\n',
            encoding="utf-8",
        )
        with pytest.raises(AssertionError):
            self._stored_command("review", directory=wrong)


class TestTheStepsReportIsMachineReadable:
    """``steps --json`` is what any other tool should read, not the prose."""

    def test_the_json_report_covers_all_six(self, tmp_path):
        """One record per entry point, keyed by name."""
        settings_path = _write_json(tmp_path / "s.json", _settings(True))
        completed = _run_cli(["steps", "--json"], settings_path)
        assert completed.returncode == pipeline.EXIT_OK, completed.stderr
        payload = json.loads(completed.stdout)
        names = [record["command"] for record in payload["entry_points"]]
        assert names == list(pipeline.command_names())

    def test_the_json_report_marks_exactly_the_two_exact_commands(self, tmp_path):
        """The exactness claim is machine-readable, not buried in prose."""
        settings_path = _write_json(tmp_path / "s.json", _settings(True))
        payload = json.loads(_run_cli(["steps", "--json"], settings_path).stdout)
        exact = [record["command"] for record in payload["entry_points"] if record["exact"]]
        assert exact == ["plan", "run-pipeline"]

    def test_a_single_entry_point_can_be_reported_alone(self, tmp_path):
        """The report narrows on request rather than always printing everything."""
        settings_path = _write_json(tmp_path / "s.json", _settings(True))
        payload = json.loads(_run_cli(["steps", "--json", "run-pipeline"], settings_path).stdout)
        assert [record["command"] for record in payload["entry_points"]] == ["run-pipeline"]
        assert payload["entry_points"][0]["steps"] == list(range(0, 9))


class TestTheNewFilesShipUnderTheProjectEncodingRule:
    """ASCII-only source and documents, like everything else here."""

    @pytest.mark.parametrize(
        "path",
        [ENTRY_SCRIPT] + [PLUGIN_ROOT / "commands" / "{0}.md".format(name) for name in pipeline.command_names()],
    )
    def test_the_file_is_ascii_only(self, path):
        """A non-ASCII byte breaks the Windows console this project targets."""
        text = Path(path).read_text(encoding="utf-8")
        offenders = sorted({character for character in text if ord(character) > 127})
        assert not offenders, offenders


class TestLiveInvocationByName:
    """AC 1's invocation half: blocked by an owner ruling, not by a limitation."""

    def test_every_entry_point_is_discovered_by_name_in_an_installed_plugin(self):
        """Judge a discovery snapshot a live installed session produced.

        This test is complete and runnable. What it does not do, and must not do,
        is perform the install itself: the owner ruled that no live
        install/uninstall cycle may be run, because install writes
        ``enabledPlugins`` and ``extraKnownMarketplaces`` into a settings scope
        and uninstall only empties them, leaving an orphaned cache directory as
        well. The operator performs the authorised half by following
        ``docs/guides/fr17-entry-point-invocation-verification.md``, which writes
        the snapshot this test then judges.
        """
        if not _live_measurement_available():
            pytest.skip(_blocked_reason())

        discovered = json.loads(Path(os.environ[DISCOVERED_COMMANDS_ENV]).read_text(encoding="utf-8"))
        names = discovered.get("commands")
        assert isinstance(names, list) and names, (
            "the snapshot lists no commands, so this run measures nothing. "
            "Procedure step 3 did not capture the command list; fix and repeat."
        )
        missing = [name for name in pipeline.command_names() if name not in names]
        assert missing == [], "entry points not discovered by name: {0}".format(missing)

    def test_the_blocked_test_body_is_rehearsed_against_both_verdicts(self, tmp_path, monkeypatch):
        """Prove the blocked test computes a verdict rather than never running.

        A skipped test is indistinguishable from a test whose body cannot work.
        This drives the identical snapshot-reading path with synthetic files and
        requires a clean verdict on a complete discovery and a dirty one on an
        incomplete discovery.
        """
        complete = tmp_path / "complete.json"
        complete.write_text(
            json.dumps({"commands": list(pipeline.command_names()) + list(PRE_EXISTING_COMMANDS)}),
            encoding="utf-8",
        )
        incomplete = tmp_path / "incomplete.json"
        incomplete.write_text(json.dumps({"commands": list(pipeline.command_names())[:-1]}), encoding="utf-8")
        empty = tmp_path / "empty.json"
        empty.write_text(json.dumps({"commands": []}), encoding="utf-8")

        monkeypatch.setenv(LIVE_INSTALL_ENV, "1")

        monkeypatch.setenv(DISCOVERED_COMMANDS_ENV, str(complete))
        assert _live_measurement_available()
        self.test_every_entry_point_is_discovered_by_name_in_an_installed_plugin()

        monkeypatch.setenv(DISCOVERED_COMMANDS_ENV, str(incomplete))
        with pytest.raises(AssertionError) as excinfo:
            self.test_every_entry_point_is_discovered_by_name_in_an_installed_plugin()
        assert "run-pipeline" in str(excinfo.value)

        monkeypatch.setenv(DISCOVERED_COMMANDS_ENV, str(empty))
        with pytest.raises(AssertionError) as excinfo:
            self.test_every_entry_point_is_discovered_by_name_in_an_installed_plugin()
        assert "measures nothing" in str(excinfo.value)

    def test_the_measurement_is_recorded_as_not_performed(self):
        """The blocked state is written down, in the shape V2-016 established."""
        assert PROCEDURE_DOC.is_file(), "missing procedure: {0}".format(PROCEDURE_DOC.as_posix())
        text = PROCEDURE_DOC.read_text(encoding="utf-8")
        assert "NOT PERFORMED" in text
        assert LIVE_INSTALL_ENV in text
        assert DISCOVERED_COMMANDS_ENV in text
        assert "test_every_entry_point_is_discovered_by_name_in_an_installed_plugin" in text

    def test_the_procedure_document_is_ascii_only(self):
        """The document ships under the same encoding rule as everything else."""
        text = PROCEDURE_DOC.read_text(encoding="utf-8")
        offenders = sorted({character for character in text if ord(character) > 127})
        assert not offenders, offenders

    def test_the_skip_reason_names_the_ruling_and_the_way_forward(self):
        """A skip a reader cannot act on is a silent skip with extra words."""
        reason = _blocked_reason()
        assert "owner" in reason.lower()
        assert LIVE_INSTALL_ENV in reason
        assert DISCOVERED_COMMANDS_ENV in reason
        assert PROCEDURE_DOC.name in reason


class TestTheFullPipelineIsNotExecutedHere:
    """AC 2's execution half: blocked by consequence, and said so out loud."""

    def test_no_test_in_this_module_invokes_the_compiled_graph(self):
        """The graph is built and read; invoking it mutates a live repository.

        A real full-mode run creates a GitHub issue, a branch, a pull request and
        a merge. That is not a slow test, it is a destructive one, and no opt-in
        flag makes it appropriate for a unit suite.

        The forbidden tokens are assembled from parts. Spelling them whole here
        would make this module an offender in its own scan, which is the
        instrument-inside-its-own-scope problem ``scripts/verify_home_paths.py``
        documents and solves the same way.
        """
        text = Path(__file__).read_text(encoding="utf-8")
        forbidden = ["." + "invoke(", "." + "stream(", "." + "ainvoke("]
        offenders = [token for token in forbidden if token in text]
        assert offenders == [], offenders
        assert "get_graph()" in text

    def test_negative_the_invocation_scan_can_fail(self):
        """NEGATIVE: a planted invocation is caught, so the scan means something."""
        planted = "graph = build()\nresult = graph." + "invoke(state)\n"
        forbidden = ["." + "invoke(", "." + "stream("]
        assert [token for token in forbidden if token in planted]


def _live_measurement_available():
    """Report whether an authorised live measurement supplied its snapshot.

    Returns:
        bool: True when authorisation and the snapshot file are both present.
    """
    if os.environ.get(LIVE_INSTALL_ENV, "").strip() != "1":
        return False
    value = os.environ.get(DISCOVERED_COMMANDS_ENV, "").strip()
    return bool(value) and Path(value).is_file()


def _blocked_reason():
    """Return the skip message for the blocked invocation measurement.

    Returns:
        str: A message naming the cause, the criterion and the way forward.
    """
    return (
        "BLOCKED, NOT PASSED. SRS FR-17 acceptance criterion 1's invocation half "
        "needs a live claude plugin install so Claude Code can discover the six "
        "commands by name. The project owner ruled that no live cycle may be "
        "run: install writes enabledPlugins and extraKnownMarketplaces into a "
        "settings scope and uninstall only empties them, so at user scope the "
        "ruling protects the owner's live configuration and at local scope a "
        "git-tracked file in this repository. This test is complete and will run "
        "as written once an operator with authorisation follows {0} and exports "
        "{1}=1 together with {2}. Do not substitute a hand-written command list "
        "for the measurement.".format(PROCEDURE_DOC.name, LIVE_INSTALL_ENV, DISCOVERED_COMMANDS_ENV)
    )

"""Only an explicit FR-17 command starts the pipeline (PRD FR-5 / SRS FR-15, V2-028).

WHICH ACCEPTANCE CRITERION EACH LAYER CAN ANSWER, AND WHICH IT CANNOT
---------------------------------------------------------------------
AC 1: a user prompt no longer invokes ``scripts/3-level-flow.py``.
AC 2: pipeline execution begins only from an explicit SRS FR-17 command.

AC 1 is a property of the ``UserPromptSubmit`` registration in a live settings
file. The project owner ruled that no agent may write to one for this issue, so
AC 1 is BLOCKED and nothing here claims it. Every test below hashes all three
live settings files and fails the module if any of them changes.

AC 2 is a property of the code path, and is measured here in three layers:

1. THE DECISION, measured in process. ``scripts/pipeline_invocation.py``
   decides, from arguments alone, whether a run may start. Both directions are
   covered: near-miss flag names and unknown command names are refused, and each
   of the six real names is accepted.

2. THE WIRE CONTRACT, measured. The plugin dispatcher and the engine each hold
   their own copy of the six command names, because an installed plugin cannot
   import the engine and the engine cannot import the plugin. The two lists are
   asserted equal so they cannot drift apart in silence.

3. THE REAL ENTRY POINT, measured as a process. ``scripts/3-level-flow.py`` is
   copied with ONE exact, asserted substitution that replaces the call into the
   engine, so the copy can be run for real without creating a GitHub issue, a
   branch, a pull request or a merge. An undeclared run must not reach the
   engine; a declared one must; and a third copy with the gate line deleted must
   reach it, which is what proves the gate is the thing stopping it.
"""

import hashlib
import importlib.util
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
ENGINE_ENTRY = SCRIPTS_DIR / "3-level-flow.py"
INVOCATION_MODULE = SCRIPTS_DIR / "pipeline_invocation.py"
PLUGIN_ENTRY = REPO_ROOT / "plugin" / "scripts" / "pipeline_entry.py"

ENGINE_CALL = "run_langgraph_engine(session_id, project_root, user_message)"
NEUTRALISED_CALL = '{"final_status": "neutralised-for-test"}'
GATE_CALL = "enforce_explicit_invocation(sys.argv[1:])"
ENGINE_REACHED_PROBE = "[DEBUG] Before run_langgraph_engine:"

SUBPROCESS_BUDGET_SECONDS = 120

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def _load(name, path):
    """Import a module by explicit file path.

    Neither ``scripts`` nor ``plugin/scripts`` is an importable package, and the
    engine entry point's own filename is not a legal module name, so everything
    here is loaded by location.

    Args:
        name: Module name to register under.
        path: Filesystem path of the module.

    Returns:
        module: The loaded module.
    """
    if str(SCRIPTS_DIR) not in sys.path:
        sys.path.insert(0, str(SCRIPTS_DIR))
    spec = importlib.util.spec_from_file_location(name, str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


invocation = _load("pipeline_invocation_under_test", INVOCATION_MODULE)


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


def _plugin_command_names():
    """Read the six entry-point names the plugin dispatcher declares.

    The plugin module is parsed rather than imported, because importing it pulls
    in the plugin's registration modules and their settings-file readers. Reading
    the two tuples it defines answers the drift question without any of that.

    Returns:
        tuple: The plugin's command names in declared order.
    """
    source = PLUGIN_ENTRY.read_text(encoding="utf-8")
    phases = re.search(r"^PHASE_COMMANDS = \(([^)]*)\)", source, re.MULTILINE)
    full = re.search(r'^FULL_PIPELINE_COMMAND = "([^"]+)"', source, re.MULTILINE)
    assert phases is not None, "PHASE_COMMANDS not found in the plugin dispatcher"
    assert full is not None, "FULL_PIPELINE_COMMAND not found in the plugin dispatcher"
    names = tuple(item.strip().strip('"') for item in phases.group(1).split(",") if item.strip())
    return names + (full.group(1),)


def _neutralised_engine(tmp_path, remove_gate=False):
    """Copy the real entry point with its engine call replaced, so it can be run.

    Exactly one substitution is made, and it is asserted to have applied, so a
    rename in the entry point fails this helper loudly instead of quietly
    producing a copy that no longer resembles what ships. When ``remove_gate`` is
    set, the gate line is deleted as well -- that copy is the mutation.

    Args:
        tmp_path: Directory to build the copy under.
        remove_gate: Whether to also delete the invocation gate call.

    Returns:
        Path: The copied entry point.
    """
    source = ENGINE_ENTRY.read_text(encoding="utf-8")
    assert source.count(ENGINE_CALL) == 1, "the engine call moved; this copy would run the real pipeline"
    source = source.replace(ENGINE_CALL, NEUTRALISED_CALL)

    assert source.count(GATE_CALL) == 1, "the gate call moved; the mutation would be a no-op"
    if remove_gate:
        source = source.replace(GATE_CALL, "")

    target_dir = Path(tmp_path) / ("mutant" if remove_gate else "copy") / "scripts"
    target_dir.mkdir(parents=True, exist_ok=True)
    (target_dir / "pipeline_invocation.py").write_text(INVOCATION_MODULE.read_text(encoding="utf-8"), encoding="utf-8")
    target = target_dir / "3-level-flow.py"
    target.write_text(source, encoding="utf-8")
    return target


def _run_engine_copy(entry, args, workdir):
    """Run a copied entry point as a real process against scratch files only.

    Args:
        entry: The copied entry point.
        args: Arguments to pass after the script name.
        workdir: Working directory for the process.

    Returns:
        subprocess.CompletedProcess: The finished process.
    """
    merged = dict(os.environ)
    merged["PYTHONPATH"] = str(REPO_ROOT)
    merged.pop("CLAUDE_WORKFLOW_RUNNING", None)
    return subprocess.run(
        [sys.executable, str(entry)] + list(args),
        capture_output=True,
        text=True,
        cwd=str(workdir),
        env=merged,
        stdin=subprocess.DEVNULL,
        timeout=SUBPROCESS_BUDGET_SECONDS,
    )


class TestTheDeclarationIsExactAndNotNearby:
    """What counts as a declaration, and what only looks like one."""

    def test_specificity_the_declaration_is_read_from_the_arguments(self):
        """SPECIFICITY: the real flag, anywhere in the arguments, is found."""
        assert invocation.declared_value(["--invoked-by=plan"]) == "plan"
        assert invocation.declared_value(["--message=x", "--invoked-by=review", "--dry-run"]) == "review"

    @pytest.mark.parametrize(
        "argument",
        [
            "--invoked-by",
            "--invoked-by-someone=plan",
            "--not-invoked-by=plan",
            "-invoked-by=plan",
            "invoked-by=plan",
            "--invoked_by=plan",
        ],
    )
    def test_negative_a_near_miss_flag_is_not_a_declaration(self, argument):
        """NEGATIVE: a gate that accepted near-misses could be passed by accident."""
        assert invocation.declared_value([argument]) is None

    def test_negative_an_empty_argument_list_declares_nothing(self):
        """NEGATIVE: this is exactly what the hook registration supplies."""
        assert invocation.declared_value([]) is None


class TestTheSixNamesAreTheSameSixOnBothSides:
    """The wire contract between two trees that cannot import each other."""

    def test_the_engine_and_the_plugin_name_the_same_six_commands(self):
        """A drift here would refuse a command the dispatcher still offers."""
        assert invocation.FR17_COMMANDS == _plugin_command_names()

    def test_there_are_exactly_six_of_them(self):
        """SRS FR-17 names six: five phases plus the full pipeline."""
        assert len(invocation.FR17_COMMANDS) == 6
        assert len(set(invocation.FR17_COMMANDS)) == 6

    def test_negative_the_drift_check_can_actually_fail(self):
        """NEGATIVE: the comparison is real, not a tautology on one source."""
        assert invocation.FR17_COMMANDS != _plugin_command_names() + ("planted",)

    def test_the_plugin_dispatcher_declares_the_command_it_dispatches(self):
        """The dispatch must carry the declaration the engine now requires."""
        source = PLUGIN_ENTRY.read_text(encoding="utf-8")
        assert 'INVOCATION_FLAG = "--invoked-by"' in source
        assert "INVOCATION_PREFIX, command" in source

    @pytest.mark.parametrize("command", list(invocation.FR17_COMMANDS))
    def test_the_argv_the_dispatcher_really_builds_is_authorized_by_the_engine(self, command, tmp_path):
        """The loop both halves of the contract exist to close.

        Neither half proves anything alone: the plugin could emit a declaration
        the engine rejects, or the engine could accept one the plugin never
        emits. This asks the STORED dispatcher, running as its own process, what
        arguments it would pass, and hands exactly those to the engine's own
        decision function.
        """
        engine_root = tmp_path / "engine"
        (engine_root / "scripts").mkdir(parents=True, exist_ok=True)
        (engine_root / "scripts" / "3-level-flow.py").write_text("import sys\nsys.exit(0)\n", encoding="utf-8")
        settings_path = tmp_path / "scratch-settings.json"
        settings_path.write_text("{}", encoding="utf-8")

        completed = subprocess.run(
            [
                sys.executable,
                str(PLUGIN_ENTRY),
                "--plugin-root",
                str(REPO_ROOT / "plugin"),
                "--settings",
                str(settings_path),
                "run",
                command,
                "--task",
                "scratch-task",
                "--engine-root",
                str(engine_root),
                "--print-only",
            ],
            capture_output=True,
            text=True,
            timeout=SUBPROCESS_BUDGET_SECONDS,
        )
        assert completed.returncode == 0, completed.stdout + completed.stderr

        argv_line = [line for line in completed.stdout.splitlines() if line.startswith("argv:")]
        assert argv_line, completed.stdout
        argv = argv_line[0].split(":", 1)[1].split()

        result = invocation.authorize(argv)
        assert result.authorized is True, argv
        assert result.command == command


class TestAuthorizeAcceptsOnlyTheSix:
    """The decision itself, in both directions."""

    @pytest.mark.parametrize("command", list(invocation.FR17_COMMANDS))
    def test_specificity_every_one_of_the_six_is_authorized(self, command):
        """SPECIFICITY: the gate must not refuse a command that is supposed to work."""
        result = invocation.authorize(["--invoked-by={0}".format(command), "--message=t"])
        assert result.authorized is True
        assert result.verdict == invocation.VERDICT_AUTHORIZED
        assert result.command == command

    def test_negative_an_undeclared_run_is_refused(self):
        """NEGATIVE: the hook path supplies no arguments at all."""
        result = invocation.authorize([])
        assert result.authorized is False
        assert result.verdict == invocation.VERDICT_UNDECLARED

    def test_negative_a_message_alone_is_not_an_authorization(self):
        """NEGATIVE: supplying work is not the same as asking for a run."""
        result = invocation.authorize(["--message=fix the login bug", "--project=/p"])
        assert result.authorized is False

    @pytest.mark.parametrize("value", ["", " plan", "plan ", "PLAN", "plan/decompose", "steps", "doctor", "about"])
    def test_negative_a_value_that_is_not_one_of_the_six_is_refused(self, value):
        """NEGATIVE: no normalising, no near-enough. A phase name is not a command name."""
        result = invocation.authorize(["--invoked-by={0}".format(value)])
        assert result.authorized is False
        assert result.verdict in invocation.REFUSING_VERDICTS

    def test_the_bare_flag_is_refused_and_says_which_form_is_needed(self):
        """A caller that half-declared gets told what the other half is."""
        result = invocation.authorize(["--invoked-by", "plan"])
        assert result.authorized is False
        assert "--invoked-by=" in result.detail

    def test_help_is_answered_without_a_declaration(self):
        """Printing usage starts no step, and it names the flag a refused caller needs."""
        for flag in invocation.HELP_FLAGS:
            result = invocation.authorize([flag])
            assert result.authorized is True
            assert result.verdict == invocation.VERDICT_HELP

    def test_negative_help_does_not_authorize_a_run_that_also_asks_for_work(self):
        """The help verdict is reported as HELP, never as AUTHORIZED."""
        result = invocation.authorize(["--help", "--message=t"])
        assert result.verdict != invocation.VERDICT_AUTHORIZED


class TestTheRefusalIsActionable:
    """A refusal that cannot be acted on is indistinguishable from a fault."""

    def test_the_refusal_names_the_cause_the_rule_and_the_six_names(self):
        """Every line must give the caller something to do."""
        joined = " ".join(invocation.refusal_lines(invocation.authorize([])))
        assert "FR-15" in joined
        assert "--invoked-by=" in joined
        for command in invocation.FR17_COMMANDS:
            assert command in joined

    def test_the_two_refusals_do_not_report_the_same_process_status(self):
        """An absent declaration is a hook; a wrong one is a typo. They differ."""
        undeclared = invocation.authorize([])
        mistyped = invocation.authorize(["--invoked-by=planx"])
        assert invocation.refusal_exit_code(undeclared) == invocation.EXIT_NOT_STARTED
        assert invocation.refusal_exit_code(mistyped) == invocation.EXIT_BAD_DECLARATION
        assert invocation.EXIT_NOT_STARTED != invocation.EXIT_BAD_DECLARATION

    def test_enforcement_raises_systemexit_and_writes_to_the_given_stream(self, capsys):
        """The refusal must not contaminate a hook's standard output."""
        with pytest.raises(SystemExit) as excinfo:
            invocation.enforce_explicit_invocation([])
        assert excinfo.value.code == invocation.EXIT_NOT_STARTED
        captured = capsys.readouterr()
        assert captured.out == ""
        assert "REFUSED" in captured.err

    def test_specificity_enforcement_returns_quietly_when_authorized(self, capsys):
        """SPECIFICITY: an authorized run must print nothing and not exit."""
        result = invocation.enforce_explicit_invocation(["--invoked-by=plan"])
        assert result.authorized is True
        captured = capsys.readouterr()
        assert captured.out == ""
        assert captured.err == ""


class TestTheDiscardedMessageIsReportedRatherThanSilent:
    """The pre-existing slash/shell early exit, made visible."""

    @pytest.mark.parametrize("message", ["/commit", "/clear", "!git status", "!ls"])
    def test_a_slash_or_shell_message_is_identified(self, message):
        """These reach no pipeline step, and the caller is told so."""
        assert invocation.discarded_message_prefix(message) in ("/", "!")

    @pytest.mark.parametrize("message", ["fix the login bug", "add /health endpoint", "why not!", ""])
    def test_specificity_an_ordinary_message_is_not_discarded(self, message):
        """SPECIFICITY: it is about the first character, not about punctuation."""
        assert invocation.discarded_message_prefix(message) is None

    def test_the_report_says_that_nothing_ran(self):
        """A zero exit with no work done must not read as a successful run."""
        joined = " ".join(invocation.discarded_message_lines("/"))
        assert "Nothing ran" in joined


class TestTheRealEntryPointRefusesAnUndeclaredRun:
    """AC 2 observed as a process, on a copy of the file that ships."""

    def test_an_undeclared_run_never_reaches_the_engine(self, tmp_path):
        """The hook shape -- no arguments -- must stop before the engine."""
        entry = _neutralised_engine(tmp_path)
        completed = _run_engine_copy(entry, ["--message=a scratch task"], tmp_path)

        assert ENGINE_REACHED_PROBE not in completed.stderr, completed.stderr
        assert "REFUSED" in completed.stderr
        assert completed.returncode == invocation.EXIT_NOT_STARTED

    def test_specificity_a_declared_run_does_reach_the_engine(self, tmp_path):
        """SPECIFICITY: the gate must not be a wall. A real command gets through."""
        entry = _neutralised_engine(tmp_path)
        completed = _run_engine_copy(entry, ["--invoked-by=plan", "--message=a scratch task"], tmp_path)

        assert ENGINE_REACHED_PROBE in completed.stderr, completed.stdout + completed.stderr
        assert "REFUSED" not in completed.stderr

    def test_mutation_deleting_the_gate_line_lets_the_undeclared_run_through(self, tmp_path):
        """MUTATION: proves the gate is what stops it, not something else upstream.

        The same undeclared arguments that were refused above reach the engine
        once the single gate line is deleted. Without this, a passing refusal
        test could be explained by any unrelated early exit in the entry point.
        """
        entry = _neutralised_engine(tmp_path, remove_gate=True)
        completed = _run_engine_copy(entry, ["--message=a scratch task"], tmp_path)

        assert ENGINE_REACHED_PROBE in completed.stderr, completed.stdout + completed.stderr
        assert "REFUSED" not in completed.stderr

    def test_help_still_works_without_a_declaration(self, tmp_path):
        """A refused caller must be able to read how to stop being refused."""
        entry = _neutralised_engine(tmp_path)
        completed = _run_engine_copy(entry, ["--help"], tmp_path)

        assert completed.returncode == 0
        assert "Usage:" in completed.stdout

    def test_a_mistyped_command_reports_a_failure_rather_than_success(self, tmp_path):
        """A typo that costs the caller a whole run must not exit zero."""
        entry = _neutralised_engine(tmp_path)
        completed = _run_engine_copy(entry, ["--invoked-by=implememt", "--message=t"], tmp_path)

        assert completed.returncode == invocation.EXIT_BAD_DECLARATION
        assert ENGINE_REACHED_PROBE not in completed.stderr


class TestTheGateSitsAheadOfTheExpensiveWork:
    """Where the gate is placed is part of what it is for."""

    def test_the_gate_runs_before_the_engine_is_imported(self):
        """A run nobody asked for must not pay for the LangGraph import.

        Position is asserted on the source rather than timed, because a timing
        assertion on an import would be a wall-clock threshold in disguise.
        """
        source = ENGINE_ENTRY.read_text(encoding="utf-8")
        gate_at = source.index(GATE_CALL)
        engine_import_at = source.index("from langgraph_engine.orchestrator import")
        config_loader_at = source.index("from langgraph_engine.core.config_loader import")
        assert gate_at < config_loader_at
        assert gate_at < engine_import_at

    def test_the_gate_is_called_exactly_once(self):
        """Two gates would mean two places to remove one from."""
        source = ENGINE_ENTRY.read_text(encoding="utf-8")
        assert source.count(GATE_CALL) == 1

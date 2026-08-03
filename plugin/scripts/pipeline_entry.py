"""Explicit slash-command entry points into the SDLC pipeline (SRS FR-17 / PRD FR-7).

Six entry points are named by the source documents as PHASES, not as command
names: plan/decompose, implement, review, document, release, plus one command
that runs Steps 0 through 8 end to end. This module is the single place where
those phases are bound to concrete command names, to the pipeline steps each
one owns, and to the dispatch that reaches them.

WHY A DISPATCHER AND NOT A DIRECT IMPORT
----------------------------------------
An installed plugin runs from the plugin manager's cache and cannot import
anything from the engine repository -- measured during V2-016, which got
ModuleNotFoundError for every candidate. The engine is therefore located the
same way ``register-mcp`` locates the MCP server checkouts: from an explicit
flag or an environment variable, and never guessed. An unresolvable engine root
is reported, because a plugin that silently resolved a path relative to the
caller's working directory would pass every local test and fail for every real
install.

WHAT THE ENGINE ACTUALLY EXPOSES, AND WHAT IT DOES NOT
------------------------------------------------------
The engine offers exactly two stop points and one entry point:

- ``CLAUDE_HOOK_MODE=1`` stops the graph after Step 3 (Branch & Workspace Setup)
- ``CLAUDE_HOOK_MODE=0`` continues to Step 8 (Final Telemetry & Summary Report)
- ``--dry-run`` makes every step numbered ``DRY_RUN_SKIP_FROM`` or higher return
  immediately without performing its work

There is NO start-at-step-N control. A phase whose first owned step is greater
than 0 therefore cannot be reached without the steps before it also running.
That is a property of the engine, not a choice made here, and it is reported
per invocation rather than hidden: every dispatch prints which steps the phase
OWNS and which additional steps the engine will run anyway. Exactly two commands
are EXACT in that sense -- ``plan`` and ``run-pipeline``.

THE START-UP CHECK
------------------
Every command here runs the ADR-020 layer-2 precondition check first, before
resolving anything else, so it still speaks when the engine root is
unresolvable. It is the SAME function ``about``, ``register-mcp`` and
``unregister-mcp`` call -- imported, not reimplemented -- so there is one
detector rather than two that can drift apart. It prints ONE line when no local
version-push gate is in place and prints nothing otherwise, and it starts no
process: registration state is pure configuration, so the question is answered
by reading two JSON files.

USAGE
    python pipeline_entry.py steps
    python pipeline_entry.py steps --json
    python pipeline_entry.py run plan --task "add rate limiting"
    python pipeline_entry.py run run-pipeline --task "..." --engine-root <dir>
    python pipeline_entry.py run implement --task "..." --print-only
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from mcp_registration import (  # noqa: E402
    RegistrationError,
    default_settings_path,
    find_plugin_root,
    load_registry,
    push_gate_precondition_line,
    read_settings,
)
from settings_store import SettingsUnreadable  # noqa: E402

EXIT_OK = 0
EXIT_FAILED = 1
EXIT_REFUSED = 2

ENGINE_ENTRY = Path("scripts") / "3-level-flow.py"
ENGINE_ROOT_ENV = "CWE_ENGINE_ROOT"

FIRST_STEP = 0
LAST_STEP = 8

DRY_RUN_SKIP_FROM = 2

DRY_RUN_GUARD_SOURCE = "langgraph_engine/sdlc_pipeline/subgraph.py"

STEP_LABELS = {
    0: "Pre-Analysis & CallGraph Scan",
    1: "Task Orchestration & Planning",
    2: "Issue Tracking",
    3: "Branch & Workspace Setup",
    4: "Implementation & Code Generation",
    5: "Pull Request & Automated Review",
    6: "Issue & Ticket Closure",
    7: "Documentation & UML Generation",
    8: "Final Telemetry & Summary Report",
}

FULL_PIPELINE_COMMAND = "run-pipeline"

PHASE_COMMANDS = ("plan", "implement", "review", "document", "release")

COMMAND_PLANS = {
    "plan": {
        "phase": "plan/decompose",
        "steps": (0, 1),
        "stop_after": 3,
        "dry_run": True,
    },
    "implement": {
        "phase": "implement",
        "steps": (2, 3, 4),
        "stop_after": 8,
        "dry_run": False,
    },
    "review": {
        "phase": "review",
        "steps": (5, 6),
        "stop_after": 8,
        "dry_run": False,
    },
    "document": {
        "phase": "document",
        "steps": (7,),
        "stop_after": 8,
        "dry_run": False,
    },
    "release": {
        "phase": "release",
        "steps": (8,),
        "stop_after": 8,
        "dry_run": False,
    },
    FULL_PIPELINE_COMMAND: {
        "phase": "full pipeline",
        "steps": tuple(range(FIRST_STEP, LAST_STEP + 1)),
        "stop_after": 8,
        "dry_run": False,
    },
}

REFUSED_TASK_PREFIXES = ("/", "!")


class PipelineEntryError(Exception):
    """An entry point could not reach its pipeline steps as asked."""


def command_names():
    """Return the six entry-point names in declared order.

    Returns:
        tuple: Phase command names followed by the full-pipeline command.
    """
    return PHASE_COMMANDS + (FULL_PIPELINE_COMMAND,)


def plan_for(command):
    """Return the step plan for one entry point.

    Args:
        command: Entry-point name.

    Returns:
        dict: The plan record.

    Raises:
        PipelineEntryError: The name is not one of the six entry points.
    """
    plan = COMMAND_PLANS.get(command)
    if plan is None:
        raise PipelineEntryError(
            "unknown entry point {0!r}; the six are: {1}".format(command, ", ".join(command_names()))
        )
    return plan


def engine_step_coverage(plan):
    """Describe which steps the engine will run for a plan, and which it skips.

    The engine enters every step from ``FIRST_STEP`` up to the plan's stop point.
    Under ``--dry-run`` the steps numbered ``DRY_RUN_SKIP_FROM`` or higher are
    entered and return immediately without performing their work, so they are
    reported as skipped rather than as performed.

    Args:
        plan: A plan record from COMMAND_PLANS.

    Returns:
        dict: entered, performed, skipped and also_runs step tuples. ``also_runs``
        is what the engine performs beyond the steps the phase owns.
    """
    entered = tuple(range(FIRST_STEP, plan["stop_after"] + 1))
    if plan["dry_run"]:
        performed = tuple(step for step in entered if step < DRY_RUN_SKIP_FROM)
        skipped = tuple(step for step in entered if step >= DRY_RUN_SKIP_FROM)
    else:
        performed = entered
        skipped = ()
    owned = set(plan["steps"])
    return {
        "entered": entered,
        "performed": performed,
        "skipped": skipped,
        "also_runs": tuple(step for step in performed if step not in owned),
        "unreached": tuple(step for step in plan["steps"] if step not in set(performed)),
    }


def plan_report(command):
    """Build the machine-readable plan record for one entry point.

    Args:
        command: Entry-point name.

    Returns:
        dict: Name, phase, owned steps with labels, and engine coverage.
    """
    plan = plan_for(command)
    coverage = engine_step_coverage(plan)
    return {
        "command": command,
        "phase": plan["phase"],
        "steps": list(plan["steps"]),
        "step_labels": [STEP_LABELS[step] for step in plan["steps"]],
        "stop_after": plan["stop_after"],
        "hook_mode": hook_mode_value(plan),
        "dry_run": plan["dry_run"],
        "engine_performs": list(coverage["performed"]),
        "engine_skips": list(coverage["skipped"]),
        "also_runs": list(coverage["also_runs"]),
        "unreached": list(coverage["unreached"]),
        "exact": not coverage["also_runs"] and not coverage["unreached"],
    }


def hook_mode_value(plan):
    """Return the CLAUDE_HOOK_MODE value a plan's stop point requires.

    ``hook_mode`` names an execution context that stops existing once nothing is
    a hook. What it actually selects is the graph's stop point: ``1`` ends after
    Step 3, ``0`` continues to Step 8. It is used here strictly as that stop-point
    selector.

    Args:
        plan: A plan record from COMMAND_PLANS.

    Returns:
        str: "1" when the plan stops before the last step, else "0".
    """
    return "0" if plan["stop_after"] >= LAST_STEP else "1"


def resolve_engine_root(explicit):
    """Determine where the engine repository is checked out.

    The plugin cannot guess this. An installed plugin's files live in the plugin
    manager's cache with no relationship to any engine checkout, and the caller's
    working directory is an unrelated project, so an unresolvable root is
    reported rather than assumed.

    Args:
        explicit: Value of the --engine-root flag, or None.

    Returns:
        Path: The resolved engine root.

    Raises:
        PipelineEntryError: Neither the flag nor the environment variable names
            a directory containing the engine entry point.
    """
    candidates = [explicit, os.environ.get(ENGINE_ROOT_ENV, "").strip() or None]
    for candidate in candidates:
        if candidate and (Path(candidate) / ENGINE_ENTRY).is_file():
            return Path(candidate).resolve()
    raise PipelineEntryError(
        "cannot resolve where the engine is checked out. Pass --engine-root "
        "<dir>, or set {0}. The directory must contain {1}. The plugin does not "
        "carry the engine and never resolves it from the working "
        "directory.".format(ENGINE_ROOT_ENV, ENGINE_ENTRY.as_posix())
    )


def validate_task(task):
    """Reject a task the engine entry point would silently discard.

    ``scripts/3-level-flow.py`` exits zero without running anything when the
    message begins with "/" or "!", treating it as a slash or shell command. A
    task starting that way would produce a successful-looking run that reached no
    step at all, so it is refused here where the cause can still be named.

    Args:
        task: The task text.

    Raises:
        PipelineEntryError: The task is empty or begins with a discarded prefix.
    """
    if not task or not task.strip():
        raise PipelineEntryError("no task given; pass --task with the work to be done")
    if task.lstrip().startswith(REFUSED_TASK_PREFIXES):
        raise PipelineEntryError(
            "the task begins with {0!r}, which the engine entry point treats as a "
            "slash or shell command and discards without running any step. "
            "Rephrase the task so it does not start with {1}.".format(
                task.lstrip()[0], " or ".join(repr(prefix) for prefix in REFUSED_TASK_PREFIXES)
            )
        )


def build_dispatch(command, task, engine_root, session_id=None, project_root=None):
    """Build the exact process invocation one entry point performs.

    Args:
        command: Entry-point name.
        task: Task text passed to the engine.
        engine_root: Resolved engine root.
        session_id: Optional session identifier to resume.
        project_root: Optional project directory for the engine to work in.

    Returns:
        dict: argv list, environment overrides, and the resolved entry point.
    """
    plan = plan_for(command)
    entry = Path(engine_root) / ENGINE_ENTRY
    argv = [sys.executable, str(entry), "--message={0}".format(task)]
    if plan["dry_run"]:
        argv.append("--dry-run")
    if session_id:
        argv.append("--session-id={0}".format(session_id))
    if project_root:
        argv.append("--project={0}".format(project_root))
    env_overrides = {"CLAUDE_HOOK_MODE": hook_mode_value(plan)}
    return {"argv": argv, "env": env_overrides, "entry": entry}


def coverage_lines(command):
    """Render the per-invocation statement of what will and will not run.

    Args:
        command: Entry-point name.

    Returns:
        list: Lines to print before dispatching.
    """
    report = plan_report(command)
    owned = ", ".join("Step {0} ({1})".format(step, STEP_LABELS[step]) for step in report["steps"])
    lines = ["{0}: owns {1}".format(command, owned)]
    if report["exact"]:
        lines.append("engine coverage: EXACT -- it performs these steps and no others")
        return lines
    if report["also_runs"]:
        lines.append(
            "engine coverage: NOT EXACT -- the engine exposes no start-at-step "
            "control, so it will also perform {0}".format(
                ", ".join("Step {0}".format(step) for step in report["also_runs"])
            )
        )
    if report["unreached"]:
        lines.append(
            "engine coverage: INCOMPLETE -- {0} would not be reached".format(
                ", ".join("Step {0}".format(step) for step in report["unreached"])
            )
        )
    return lines


def start_up_check_line(plugin_root, settings_path):
    """Return the ADR-020 layer-2 line, or None when the state is safe.

    This delegates to the detector ``about``, ``register-mcp`` and
    ``unregister-mcp`` already use rather than reimplementing it, so the six
    entry points cannot drift from the three commands that shipped first.

    Nothing here starts a process, opens a socket or performs an MCP handshake.
    Registration state is pure configuration, so whether a gate will run in a
    future session is answered by reading two JSON files.

    Args:
        plugin_root: Path of the plugin root.
        settings_path: Path of the settings file to inspect.

    Returns:
        str or None: One line when no local version-push gate is in place.
    """
    try:
        servers = load_registry(plugin_root)
        settings = read_settings(settings_path)
    except (RegistrationError, SettingsUnreadable):
        return None
    return push_gate_precondition_line(settings, servers, settings_path)


def do_steps(args, plugin_root, settings_path):
    """Report the step plan of every entry point, or of one named entry point.

    Args:
        args: Parsed command-line arguments.
        plugin_root: Path of the plugin root, unused here.
        settings_path: Path of the settings file, unused here.

    Returns:
        int: EXIT_OK.
    """
    names = [args.command] if args.command else list(command_names())
    reports = [plan_report(name) for name in names]
    if args.as_json:
        print(json.dumps({"entry_points": reports}, indent=2, sort_keys=True))
        return EXIT_OK
    for report in reports:
        print(
            "{0:<13} {1:<16} steps {2:<12} hook_mode={3} dry_run={4} {5}".format(
                report["command"],
                report["phase"],
                ",".join(str(step) for step in report["steps"]),
                report["hook_mode"],
                "1" if report["dry_run"] else "0",
                "EXACT" if report["exact"] else "also runs " + ",".join(str(s) for s in report["also_runs"]),
            )
        )
    return EXIT_OK


def do_run(args, plugin_root, settings_path):
    """Run one entry point: start-up check, resolve, report coverage, dispatch.

    The start-up check runs FIRST and unconditionally, before the engine root is
    resolved, so an unreachable engine never suppresses it.

    Args:
        args: Parsed command-line arguments.
        plugin_root: Path of the plugin root.
        settings_path: Path of the settings file to inspect.

    The engine is started WITHOUT relocating the working directory. The engine
    entry point bootstraps its own imports from its own file location, and it
    derives the project it works on from the working directory, so moving into
    the engine checkout would silently run the pipeline against the engine
    repository instead of the user's project.

    Returns:
        int: EXIT_OK on success, EXIT_REFUSED when the request cannot be
        dispatched as asked, or the engine's own exit status.
    """
    line = start_up_check_line(plugin_root, settings_path)
    if line:
        print(line)

    try:
        plan_for(args.command)
        validate_task(args.task)
        engine_root = resolve_engine_root(args.engine_root)
    except PipelineEntryError as exc:
        print("REFUSED: {0}".format(exc))
        return EXIT_REFUSED

    for coverage_line in coverage_lines(args.command):
        print(coverage_line)

    dispatch = build_dispatch(
        args.command,
        args.task,
        engine_root,
        session_id=args.session_id,
        project_root=args.project_root,
    )
    print("engine: {0}".format(dispatch["entry"].as_posix()))
    print("env:    {0}".format(" ".join("{0}={1}".format(k, v) for k, v in sorted(dispatch["env"].items()))))
    print("argv:   {0}".format(" ".join(dispatch["argv"][1:])))

    if args.print_only:
        return EXIT_OK

    env = dict(os.environ)
    env.update(dispatch["env"])
    completed = subprocess.run(dispatch["argv"], env=env)
    return completed.returncode


def _parse_args(argv):
    """Parse command-line arguments.

    Args:
        argv: Argument strings excluding the program name.

    Returns:
        argparse.Namespace: Parsed arguments.
    """
    parser = argparse.ArgumentParser(
        prog="pipeline_entry",
        description="Explicit slash-command entry points into the SDLC pipeline (SRS FR-17).",
    )
    parser.add_argument("--plugin-root", default=None, help="Plugin root override, for tests and local development.")
    parser.add_argument("--settings", default=None, help="Settings file to inspect. Defaults to the user scope.")
    sub = parser.add_subparsers(dest="action", required=True)

    steps = sub.add_parser("steps", help="Report which pipeline steps each entry point owns.")
    steps.add_argument("command", nargs="?", default=None, help="Report only this entry point.")
    steps.add_argument("--json", action="store_true", dest="as_json", help="Emit a machine-readable report.")

    run = sub.add_parser("run", help="Run one entry point against the engine checkout.")
    run.add_argument("command", help="Entry point name: {0}.".format(", ".join(command_names())))
    run.add_argument("--task", default="", help="The work to be done.")
    run.add_argument("--engine-root", default=None, help="Directory holding the engine checkout.")
    run.add_argument("--session-id", default=None, help="Session identifier to run under.")
    run.add_argument("--project-root", default=None, help="Project directory the engine works in.")
    run.add_argument("--print-only", action="store_true", help="Report the resolved dispatch without executing it.")
    return parser.parse_args(argv)


def main(argv=None):
    """Run the requested action and return a process exit status.

    Args:
        argv: Optional argument strings excluding the program name.

    Returns:
        int: Process exit status.
    """
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    try:
        plugin_root = Path(args.plugin_root) if args.plugin_root else find_plugin_root()
    except RegistrationError as exc:
        print("FAILED: {0}".format(exc))
        return EXIT_FAILED
    settings_path = Path(args.settings) if args.settings else default_settings_path()
    handlers = {"steps": do_steps, "run": do_run}
    return handlers[args.action](args, plugin_root, settings_path)


if __name__ == "__main__":
    sys.exit(main())

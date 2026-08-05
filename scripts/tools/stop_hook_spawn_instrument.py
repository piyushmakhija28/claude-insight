#!/usr/bin/env python3
"""Instrument the retained Stop hook and decide each of its spawn capabilities.

Serves PRD FR-8a / SRS FR-19 acceptance criterion 1, which requires, for twenty
consecutive Stop-hook invocations against this repository's current checkout:
the exact subprocess count per invocation, the wall-clock duration per
invocation, and which of the nine referenced scripts actually ran as opposed to
hitting a failed ``.exists()`` guard.

The module offers three subcommands, deliberately separated because they carry
different evidential weight and a reader must be able to tell them apart:

``census``
    A read-only AST scan of ``hooks/stop_notifier/`` that counts subprocess call
    sites per module and resolves each of the nine referenced script targets
    against the real environment. Purely observational; mutates nothing.

``observe``
    A read-only parse of the live ``stop-notifier.log`` written by genuine Stop
    events. Reports how many real invocations are evidenced in a window and what
    code paths each one is entailed to have taken. Purely observational; the
    hook is never invoked by this tool.

``run``
    Executes the real ``hooks/stop-notifier.py`` entry point N times as a real
    subprocess under an observer that records every process spawn and every
    ``Path.exists`` guard evaluation. The code path, the guards and the git
    repository are real; the trigger is this harness rather than Claude Code,
    and the home directory is redirected to a seeded replica so the owner's
    ``~/.claude`` state is never mutated. This tier is INTRUSIVE and is labelled
    as such in its own output.

No subcommand writes to any settings file, creates any GitHub artifact, or
modifies ``hooks/stop_notifier/``.
"""

import argparse
import ast
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
HOOK_PACKAGE = REPO_ROOT / "hooks" / "stop_notifier"
HOOK_ENTRY_POINT = REPO_ROOT / "hooks" / "stop-notifier.py"

SUBPROCESS_CALL_NAMES = ("run", "Popen", "call", "check_call", "check_output")

CENSUS_MODULES = ("core.py", "post_impl.py", "voice.py", "helpers.py", "__init__.py")

ENUMERATED_OPPORTUNITIES = (
    {
        "ordinal": 1,
        "site": "hooks/stop_notifier/post_impl.py:55",
        "argv_line": 56,
        "kind": "unconditional",
        "match": ("git", "rev-parse"),
        "target_description": "git rev-parse --abbrev-ref HEAD",
    },
    {
        "ordinal": 2,
        "site": "hooks/stop_notifier/post_impl.py:208",
        "argv_line": 209,
        "kind": "unconditional",
        "match": ("git", "rev-parse"),
        "target_description": "git rev-parse --abbrev-ref HEAD",
    },
    {
        "ordinal": 3,
        "site": "hooks/stop_notifier/post_impl.py:286",
        "argv_line": 286,
        "kind": "guarded",
        "match": ("sync-version.py",),
        "target_description": "python sync-version.py",
        "resolution_site": "hooks/stop_notifier/post_impl.py:284",
    },
    {
        "ordinal": 4,
        "site": "hooks/stop_notifier/voice.py:164",
        "argv_line": 165,
        "kind": "guarded",
        "match": ("voice-notifier.py",),
        "target_description": "python voice-notifier.py",
        "resolution_site": "hooks/stop_notifier/helpers.py:142",
    },
)

NAMED_EXCEPTIONS = (
    {
        "name": "post_impl_commits_ahead_create_pr",
        "site": "hooks/stop_notifier/post_impl.py:64",
        "match": ("git", "rev-list"),
        "rationale": (
            "Reached whenever HEAD is not main/master/HEAD/empty. The enumerated set was "
            "derived on the assumption that opportunity 1 returns early, which only holds "
            "on a default branch. This checkout is a feature branch, so the call fires."
        ),
    },
    {
        "name": "post_impl_commits_ahead_post_steps",
        "site": "hooks/stop_notifier/post_impl.py:216",
        "match": ("git", "rev-list"),
        "rationale": (
            "Same structure as the above, in _run_post_implementation_steps. Fires for the "
            "same reason and is the precondition for reaching enumerated opportunity 3."
        ),
    },
    {
        "name": "core_branch_detection_current_branch",
        "site": "hooks/stop_notifier/core.py:377",
        "match": ("git", "branch", "--show-current"),
        "rationale": (
            "PRIORITY 4 branch detection. Guarded only by 'not pr_triggered', which is true "
            "on every turn that writes no work-done voice flag, i.e. the common case."
        ),
    },
    {
        "name": "core_branch_detection_commits_ahead",
        "site": "hooks/stop_notifier/core.py:422",
        "match": ("git", "rev-list"),
        "rationale": (
            "Reached on a feature branch once the session-issue and progress-file checks "
            "fail to trigger, which is the common case."
        ),
    },
    {
        "name": "core_branch_detection_working_tree",
        "site": "hooks/stop_notifier/core.py:432",
        "match": ("git", "status", "--porcelain"),
        "rationale": (
            "Reached when the feature branch is ahead of main. Drives the 60-second ship "
            "debounce and therefore runs on every turn where commits_ahead is positive."
        ),
    },
    {
        "name": "core_pr_workflow_retry_branch",
        "site": "hooks/stop_notifier/core.py:349",
        "match": ("git", "branch", "--show-current"),
        "rationale": (
            "Fires only while the .pr-workflow-retry flag exists. Absent on this checkout, "
            "so it is enumerated as a permitted exception rather than an expected spawn."
        ),
    },
)

REFERENCED_SCRIPTS = (
    {
        "ordinal": 1,
        "label": "git-auto-commit-policy.py",
        "spawn_site": "hooks/stop_notifier/core.py:82",
        "anchor": "repo",
        "relative": "scripts/architecture/03-execution-system/09-git-commit/git-auto-commit-policy.py",
    },
    {
        "ordinal": 2,
        "label": "auto-save-session.py",
        "spawn_site": "hooks/stop_notifier/core.py:111",
        "anchor": "repo",
        "relative": "scripts/architecture/01-sync-system/session-management/auto-save-session.py",
    },
    {
        "ordinal": 3,
        "label": "archive-old-sessions.py",
        "spawn_site": "hooks/stop_notifier/core.py:139",
        "anchor": "repo",
        "relative": "scripts/architecture/01-sync-system/session-management/archive-old-sessions.py",
    },
    {
        "ordinal": 4,
        "label": "session-pruner.py",
        "spawn_site": "hooks/stop_notifier/core.py:163",
        "anchor": "repo",
        "relative": "scripts/architecture/01-sync-system/session-pruner.py",
    },
    {
        "ordinal": 5,
        "label": "common-failures-prevention.py",
        "spawn_site": "hooks/stop_notifier/core.py:197",
        "anchor": "repo",
        "relative": "scripts/architecture/03-execution-system/failure-prevention/common-failures-prevention.py",
    },
    {
        "ordinal": 6,
        "label": "preference-auto-tracker.py",
        "spawn_site": "hooks/stop_notifier/core.py:222",
        "anchor": "repo",
        "relative": "scripts/architecture/01-sync-system/user-preferences/preference-auto-tracker.py",
    },
    {
        "ordinal": 7,
        "label": "plan-session-archiver.py",
        "spawn_site": "hooks/stop_notifier/core.py:243",
        "anchor": "repo",
        "relative": "scripts/architecture/03-execution-system/02-plan-mode/plan-session-archiver.py",
    },
    {
        "ordinal": 8,
        "label": "sync-version.py",
        "spawn_site": "hooks/stop_notifier/post_impl.py:286",
        "anchor": "hook_package",
        "relative": "sync-version.py",
    },
    {
        "ordinal": 9,
        "label": "voice-notifier.py",
        "spawn_site": "hooks/stop_notifier/voice.py:164",
        "anchor": "home_current_dir",
        "relative": "voice-notifier.py",
    },
)

OBSERVER_SOURCE = '''"""Record process spawns and guard evaluations around the real Stop hook.

Installed as a subprocess wrapper by stop_hook_spawn_instrument.py. Adds a CPython
audit hook that captures every process creation and a recording pass-through over
Path.exists that captures every guard evaluation, then executes the real hook entry
point under run_name __main__ so the module-level dispatch behaves as it does when
Claude Code invokes it.
"""

import json
import runpy
import sys
import time
from pathlib import Path

SPAWNS = []
GUARDS = []


def _audit(event, args):
    """Append argv for every process-creation audit event."""
    if event == "subprocess.Popen":
        try:
            argv = args[1]
            if argv is None:
                SPAWNS.append([str(args[0])])
            elif isinstance(argv, (list, tuple)):
                SPAWNS.append([str(item) for item in argv])
            else:
                SPAWNS.append([str(argv)])
        except Exception:
            SPAWNS.append(["<unparsed-spawn>"])


sys.addaudithook(_audit)

_ORIGINAL_EXISTS = Path.exists


def _recording_exists(self, *args, **kwargs):
    """Delegate to the real Path.exists while recording the path and the answer."""
    outcome = _ORIGINAL_EXISTS(self, *args, **kwargs)
    GUARDS.append([str(self), bool(outcome)])
    return outcome


Path.exists = _recording_exists

_HOOK = sys.argv[1]
_RESULT = sys.argv[2]
_STATUS = "ok"
_START = time.perf_counter()
try:
    runpy.run_path(_HOOK, run_name="__main__")
except SystemExit as exc:
    _STATUS = "exit:%s" % (exc.code,)
except BaseException as exc:
    _STATUS = "exception:%s:%s" % (type(exc).__name__, exc)
_ELAPSED_MS = (time.perf_counter() - _START) * 1000.0

Path.exists = _ORIGINAL_EXISTS

Path(_RESULT).write_text(
    json.dumps({"spawns": SPAWNS, "guards": GUARDS, "status": _STATUS, "elapsed_ms": _ELAPSED_MS}),
    encoding="utf-8",
)
'''

STOP_PAYLOAD = {
    "hook_event_name": "Stop",
    "session_id": "SESSION-INSTRUMENT-FR8A",
    "stop_hook_active": False,
    "transcript_path": "",
}


def census_call_sites():
    """Count subprocess call sites per stop_notifier module by AST.

    Returns:
        Dict mapping module file name to a list of {"line", "attr"} records, in
        source order, for every ``subprocess.<name>(...)`` call in the module.
    """
    census = {}
    for module_name in CENSUS_MODULES:
        path = HOOK_PACKAGE / module_name
        if not path.exists():
            census[module_name] = None
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        sites = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if not isinstance(func, ast.Attribute) or func.attr not in SUBPROCESS_CALL_NAMES:
                continue
            if isinstance(func.value, ast.Name) and func.value.id == "subprocess":
                sites.append({"line": node.lineno, "attr": func.attr})
        census[module_name] = sorted(sites, key=lambda item: item["line"])
    return census


def resolve_referenced_scripts(home=None):
    """Resolve each of the nine referenced script targets and test its guard.

    Args:
        home: Home directory to resolve home-anchored targets against, or None
            to use the real home directory.

    Returns:
        List of dicts carrying the resolved absolute path and whether it exists.
    """
    base_home = Path(home) if home is not None else Path.home()
    scripts_dir = base_home / ".claude" / "scripts"
    current_dir = scripts_dir if scripts_dir.exists() else (base_home / ".claude" / "memory" / "current")
    resolved = []
    for entry in REFERENCED_SCRIPTS:
        if entry["anchor"] == "repo":
            target = REPO_ROOT / entry["relative"]
        elif entry["anchor"] == "hook_package":
            target = HOOK_PACKAGE / entry["relative"]
        else:
            target = current_dir / entry["relative"]
        record = dict(entry)
        record["resolved_target"] = str(target)
        record["exists"] = target.exists()
        record["capability"] = "ARMED" if target.exists() else "INERT"
        resolved.append(record)
    return resolved


ENUMERATED_SITES = frozenset(opportunity["site"] for opportunity in ENUMERATED_OPPORTUNITIES)
EXCEPTION_SITES = frozenset(exception["site"] for exception in NAMED_EXCEPTIONS)

REV_PARSE_ORDER = ("hooks/stop_notifier/post_impl.py:208", "hooks/stop_notifier/post_impl.py:55")
REV_LIST_HEAD_ORDER = ("hooks/stop_notifier/post_impl.py:216", "hooks/stop_notifier/post_impl.py:64")


def summarize_script_guards(guards):
    """Decide, per referenced script, whether its guard ran and what it answered.

    Distinguishes the two ways a script can fail to spawn. A guard that was
    evaluated and returned False proves the reference is dead. A guard that was
    never evaluated proves only that the surrounding branch was not taken this
    turn, which is a weaker statement and must not be reported as the former.

    Args:
        guards: Ordered list of (path, outcome) pairs recorded in one run.

    Returns:
        Dict mapping script label to its measured guard disposition.
    """
    summary = {}
    for entry in REFERENCED_SCRIPTS:
        matches = [
            bool(outcome) for path, outcome in guards if str(path).replace("\\", "/").endswith("/" + entry["label"])
        ]
        if not matches:
            disposition = "GUARD_NOT_REACHED"
        elif any(matches):
            disposition = "GUARD_TRUE_SCRIPT_RAN"
        else:
            disposition = "GUARD_FALSE_SCRIPT_SKIPPED"
        summary[entry["label"]] = {
            "spawn_site": entry["spawn_site"],
            "evaluations": len(matches),
            "disposition": disposition,
        }
    return summary


def spawn_shape(argv):
    """Reduce one observed argv to the shape that identifies its call site.

    Args:
        argv: Argument vector recorded by the observer's audit hook.

    Returns:
        Short shape name, or "other" when the argv matches no known shape.
    """
    joined = " ".join(str(item) for item in argv).replace("\\", "/").lower()
    if "sync-version.py" in joined:
        return "sync_version"
    if "voice-notifier.py" in joined:
        return "voice_notifier"
    for entry in REFERENCED_SCRIPTS:
        if entry["anchor"] == "repo" and entry["label"].lower() in joined:
            return "architecture_script:%s" % entry["label"]
    if "branch --show-current" in joined:
        return "branch_show_current"
    if "status --porcelain" in joined:
        return "status_porcelain"
    if "rev-parse" in joined:
        return "rev_parse_head"
    if "rev-list" in joined:
        return "rev_list_head" if "main..head" in joined else "rev_list_named_branch"
    return "other"


def attribute_spawns(spawns, guards=()):
    """Attribute an ordered spawn sequence to concrete call sites.

    Attribution combines three measured inputs rather than argv text alone,
    because several sites emit byte-identical argv. Shape narrows the candidate
    set; recorded ``Path.exists`` guard outcomes decide the sites whose
    reachability is flag-dependent; and execution order decides the remainder,
    since ``core.main`` calls ``_run_post_implementation_steps`` before
    ``_create_pr_from_pipeline_data``.

    Args:
        spawns: Ordered list of argument vectors, one per observed spawn.
        guards: Ordered list of (path, outcome) pairs recorded in the same run.

    Returns:
        List of dicts, one per spawn, carrying the attributed site and bucket.
    """
    retry_flag_present = any(
        str(path).replace("\\", "/").endswith(".claude/.pr-workflow-retry") and bool(outcome)
        for path, outcome in guards
    )
    seen = {}
    attributions = []
    for argv in spawns:
        shape = spawn_shape(argv)
        index = seen.get(shape, 0)
        seen[shape] = index + 1
        site = None
        if shape == "branch_show_current":
            if retry_flag_present:
                site = "hooks/stop_notifier/core.py:349" if index == 0 else "hooks/stop_notifier/core.py:377"
            else:
                site = "hooks/stop_notifier/core.py:377"
        elif shape == "rev_list_named_branch":
            site = "hooks/stop_notifier/core.py:422"
        elif shape == "status_porcelain":
            site = "hooks/stop_notifier/core.py:432"
        elif shape == "rev_parse_head":
            site = REV_PARSE_ORDER[index] if index < len(REV_PARSE_ORDER) else None
        elif shape == "rev_list_head":
            site = REV_LIST_HEAD_ORDER[index] if index < len(REV_LIST_HEAD_ORDER) else None
        elif shape == "sync_version":
            site = "hooks/stop_notifier/post_impl.py:286"
        elif shape == "voice_notifier":
            site = "hooks/stop_notifier/voice.py:164"
        elif shape.startswith("architecture_script:"):
            label = shape.split(":", 1)[1]
            site = next((e["spawn_site"] for e in REFERENCED_SCRIPTS if e["label"] == label), None)
        if site in ENUMERATED_SITES:
            bucket = "enumerated"
        elif site in EXCEPTION_SITES:
            bucket = "named_exception"
        else:
            bucket = "unclassified"
        attributions.append({"argv": list(argv), "shape": shape, "site": site, "bucket": bucket})
    return attributions


REQUIRED_FIRING_SITES = (
    "hooks/stop_notifier/post_impl.py:55",
    "hooks/stop_notifier/post_impl.py:208",
)


def evaluate_spawn_floor(attributions):
    """Decide whether one invocation's spawn sequence satisfies the FR-8a floor.

    The floor is expressed as an enumerated set rather than a count, so that it
    stays deterministically valid whether or not a guarded opportunity fires. A
    sequence passes when every spawn is attributable to an enumerated
    opportunity or to a documented named exception, and when both unconditional
    opportunities are present. A guarded opportunity that stays silent is the
    measured expected state and never fails the check.

    Args:
        attributions: Output of :func:`attribute_spawns` for one invocation.

    Returns:
        Dict carrying the verdict and the reasons behind it.
    """
    observed_sites = [item["site"] for item in attributions]
    outside = [item for item in attributions if item["bucket"] == "unclassified"]
    missing = [site for site in REQUIRED_FIRING_SITES if site not in observed_sites]
    reasons = []
    for item in outside:
        reasons.append(
            "spawn outside the enumerated set and the named exceptions: %s" % (" ".join(item["argv"])[:120],)
        )
    for site in missing:
        reasons.append("unconditional opportunity did not fire: %s" % site)
    return {
        "verdict": "PASS" if not reasons else "FAIL",
        "reasons": reasons,
        "observed_sites": observed_sites,
        "silent_guarded_opportunities": [
            opportunity["site"]
            for opportunity in ENUMERATED_OPPORTUNITIES
            if opportunity["kind"] == "guarded" and opportunity["site"] not in observed_sites
        ],
    }


def _seed_home(scratch_home, replicate_voice_disabled, session_id):
    """Create a seeded replica home so guard evaluation stays faithful.

    The replica reproduces the three facts about the live home that change which
    guards the hook reaches: the absence of ``~/.claude/scripts``, the presence of
    the ``.voice-disabled`` flag, and the presence of at least one session
    directory under ``~/.claude/logs/sessions``.

    Args:
        scratch_home: Directory to populate as the replica home.
        replicate_voice_disabled: Whether to create the .voice-disabled flag.
        session_id: Session directory name to create under logs/sessions.

    Returns:
        Dict recording exactly which replica facts were established.
    """
    claude_dir = scratch_home / ".claude"
    (claude_dir / "memory" / "logs").mkdir(parents=True, exist_ok=True)
    session_dir = claude_dir / "logs" / "sessions" / session_id
    session_dir.mkdir(parents=True, exist_ok=True)
    (session_dir / "execution-summary.txt").write_text(
        "Task: Feature | Complexity: 6/10 | Skill: python-core", encoding="utf-8"
    )
    (session_dir / "user_message.txt").write_text("instrumentation fixture", encoding="utf-8")
    if replicate_voice_disabled:
        (claude_dir / ".voice-disabled").write_text("", encoding="utf-8")
    return {
        "claude_scripts_absent": not (claude_dir / "scripts").exists(),
        "voice_disabled_present": (claude_dir / ".voice-disabled").exists(),
        "session_dir": str(session_dir),
    }


def _child_environment(scratch_home):
    """Build the child environment with the home directory redirected.

    Args:
        scratch_home: Replica home directory.

    Returns:
        Dict suitable for passing as the subprocess environment.
    """
    env = dict(os.environ)
    env["USERPROFILE"] = str(scratch_home)
    env["HOME"] = str(scratch_home)
    env["HOMEDRIVE"] = str(scratch_home.drive) if scratch_home.drive else ""
    env["HOMEPATH"] = str(scratch_home)[len(scratch_home.drive) :] if scratch_home.drive else str(scratch_home)
    env.pop("IDE_INSTALL_DIR", None)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def _run_one(observer_path, result_path, env, instrumented):
    """Execute the real Stop hook once and return the recorded observation.

    Args:
        observer_path: Path to the observer wrapper module.
        result_path: Path the observer writes its JSON result to.
        env: Child environment mapping.
        instrumented: True to run under the observer, False to run the entry
            point directly for an unperturbed wall-clock reading.

    Returns:
        Dict carrying wall-clock duration, spawn records and guard records.
    """
    if result_path.exists():
        result_path.unlink()
    if instrumented:
        argv = [sys.executable, str(observer_path), str(HOOK_ENTRY_POINT), str(result_path)]
    else:
        argv = [sys.executable, str(HOOK_ENTRY_POINT)]
    started = time.perf_counter()
    completed = subprocess.run(
        argv,
        cwd=str(REPO_ROOT),
        env=env,
        input=json.dumps(STOP_PAYLOAD).encode("utf-8"),
        capture_output=True,
        timeout=120,
    )
    wall_ms = (time.perf_counter() - started) * 1000.0
    observation = {
        "wall_clock_ms": round(wall_ms, 2),
        "returncode": completed.returncode,
        "instrumented": instrumented,
        "spawns": [],
        "guards": [],
        "status": None,
    }
    if instrumented and result_path.exists():
        payload = json.loads(result_path.read_text(encoding="utf-8"))
        observation["spawns"] = payload["spawns"]
        observation["guards"] = payload["guards"]
        observation["status"] = payload["status"]
        observation["in_process_ms"] = round(payload["elapsed_ms"], 2)
    return observation


def run_invocations(count, control_count, session_id="SESSION-INSTRUMENT-FR8A"):
    """Run the real Stop hook repeatedly under observation.

    Args:
        count: Number of instrumented invocations to perform.
        control_count: Number of uninstrumented invocations used to quantify the
            observer's perturbation of wall-clock duration.
        session_id: Session directory name seeded into the replica home.

    Returns:
        Dict carrying the replica description, per-invocation observations and
        the control-group durations.
    """
    workspace = Path(tempfile.mkdtemp(prefix="fr8a_stop_hook_"))
    try:
        scratch_home = workspace / "home"
        scratch_home.mkdir(parents=True, exist_ok=True)
        replica = _seed_home(scratch_home, replicate_voice_disabled=True, session_id=session_id)
        observer_path = workspace / "spawn_observer.py"
        observer_path.write_text(OBSERVER_SOURCE, encoding="utf-8")
        result_path = workspace / "observation.json"
        env = _child_environment(scratch_home)

        invocations = []
        for index in range(1, count + 1):
            observation = _run_one(observer_path, result_path, env, instrumented=True)
            observation["index"] = index
            observation["spawn_count"] = len(observation["spawns"])
            observation["attributions"] = attribute_spawns(observation["spawns"], observation["guards"])
            observation["script_guards"] = summarize_script_guards(observation["guards"])
            invocations.append(observation)

        controls = []
        for index in range(1, control_count + 1):
            control = _run_one(observer_path, result_path, env, instrumented=False)
            control["index"] = index
            controls.append(control)

        return {
            "replica_home": replica,
            "invocations": invocations,
            "controls": controls,
            "tier": "INTRUSIVE: real entry point, real guards, real git repository, harness-triggered",
        }
    finally:
        shutil.rmtree(workspace, ignore_errors=True)


def observe_real_log(baseline_lines=0, log_path=None):
    """Parse the live stop-notifier log for evidence of genuine Stop events.

    Genuine invocations are counted by the terminal marker each one writes. The
    parse is read-only and never invokes the hook.

    Args:
        baseline_lines: Number of leading lines to skip so a caller can scope the
            parse to a window it opened.
        log_path: Log file to read, or None for the real one.

    Returns:
        Dict carrying the evidenced invocation count and the entailed code paths.
    """
    path = (
        Path(log_path) if log_path is not None else (Path.home() / ".claude" / "memory" / "logs" / "stop-notifier.log")
    )
    if not path.exists():
        return {"log_present": False, "evidenced_invocations": 0, "markers": {}}
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()[baseline_lines:]
    markers = {
        "stop_hook_fired": "[OK] Stop hook fired",
        "pr_auto_reached": "[PR-AUTO] PR auto-create skipped",
        "branch_detection_reached": "[PR-WORKFLOW] Branch detection",
        "debounce_started": "[PR-WORKFLOW] Ready to ship",
        "debounce_waiting": "[PR-WORKFLOW] Ready to ship but debouncing",
        "voice_flag_handled": "[flag-resolve]",
        "voice_disabled": "[voice] Disabled",
    }
    counts = {name: sum(1 for line in lines if token in line) for name, token in markers.items()}
    return {
        "log_present": True,
        "log_path": str(path),
        "window_lines": len(lines),
        "evidenced_invocations": counts["stop_hook_fired"],
        "markers": counts,
        "tier": "OBSERVATIONAL: artifacts of genuine Claude Code Stop events; hook not invoked by this tool",
    }


def _emit(payload, output):
    """Write the payload as JSON to stdout or to a file."""
    text = json.dumps(payload, indent=2, sort_keys=True)
    if output:
        Path(output).write_text(text + "\n", encoding="utf-8")
    else:
        sys.stdout.write(text + "\n")


def main(argv=None):
    """Parse arguments and dispatch the requested subcommand."""
    parser = argparse.ArgumentParser(description="Instrument the retained Stop hook (PRD FR-8a / SRS FR-19).")
    parser.add_argument("mode", choices=("census", "observe", "run"))
    parser.add_argument("--count", type=int, default=20)
    parser.add_argument("--control-count", type=int, default=5)
    parser.add_argument("--baseline-lines", type=int, default=0)
    parser.add_argument("--output", default=None)
    args = parser.parse_args(argv)

    if args.mode == "census":
        sites = census_call_sites()
        payload = {
            "mode": "census",
            "tier": "OBSERVATIONAL: static AST scan and read-only filesystem resolution",
            "call_sites": sites,
            "call_site_totals": {name: (len(v) if v is not None else None) for name, v in sites.items()},
            "call_site_total": sum(len(v) for v in sites.values() if v),
            "referenced_scripts": resolve_referenced_scripts(),
        }
    elif args.mode == "observe":
        payload = {"mode": "observe"}
        payload.update(observe_real_log(args.baseline_lines))
    else:
        payload = {"mode": "run"}
        payload.update(run_invocations(args.count, args.control_count))

    _emit(payload, args.output)
    return 0


if __name__ == "__main__":
    sys.exit(main())

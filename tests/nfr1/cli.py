"""Runnable entry point for the NFR-1 per-component process-count harness.

Usage:
    python tests/nfr1/cli.py --plugin-root <path> [--json-out <file>]
    python tests/nfr1/cli.py --observe --phase cold [--plugin-root <path>]
    python tests/nfr1/cli.py --self-test

Invoke by path, not with -m. An unrelated ``tests`` distribution in this environment's
site-packages shadows the repository's tests directory, so ``python -m tests.nfr1.cli``
cannot resolve. The same shadowing is why tests/test_nfr1_harness.py imports the
package as top-level ``nfr1``.

Against the current tree the harness reports NOT_MEASURABLE, which is the correct and
intended result: no plugin exists to install (issue V2-015) and the PreToolUse and
PostToolUse hook registrations have not been deleted (issue V2-027). It will not report
PASS until both land and a real measurement runs.

The --observe mode is the one that actually counts tool calls. It measures a single
phase in observer mode, tailing the live Claude Code transcript and marking each real
tool call as it appears. It is separate from the default mode because a cold count is
only cold when the window opens before the session has issued anything, which means a
separate invocation against a fresh session -- the default mode's two back-to-back
phases can produce a cold-labelled slot but not a cold measurement.

Two observed phases still cannot be combined into one report: build_report takes
Measurement objects, and harness.py provides no way to read a Measurement back from
JSON. That gap is stated rather than papered over.

The --self-test mode proves the harness is not a no-op. It spawns a real, uniquely
marked child process inside a driven measurement window, registers a component that
owns that marker with the plugin-counted role, and asserts the harness returns FAIL.
Exit status 0 means the harness demonstrated it can fail; any other status means the
harness could not be shown to detect a spawn it was told to detect.
"""

import argparse
import json
import os
import subprocess
import sys
import time

_TESTS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _TESTS_DIR not in sys.path:
    sys.path.insert(0, _TESTS_DIR)

from nfr1 import components, driver, harness  # noqa: E402

SELF_TEST_MARKER = "nfr1_selftest_spawn_marker"


def _repo_root():
    """Return the repository root inferred from this file's location."""
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def run_measurement(plugin_root, sample_interval_seconds=0.05):
    """Run a cold and a warm observer-mode measurement with no tool calls driven.

    This is the shape a real NFR-1 run takes, minus the external driver that issues the
    ten tool calls. Without that driver the recorded count is zero, so both phases
    report INDETERMINATE. That is deliberate: the harness never invents a measurement
    it did not observe.

    The cold phase produced here is NOT a genuinely cold measurement. Both phases run
    back to back inside one already-running interpreter, so the label describes the
    report slot rather than the session state. A genuine cold count requires the
    external driver to invoke this immediately after a fresh session starts and before
    any tool call has run, which is the same driver the ten tool calls need. The
    structure is correct and separate for both phases; only the cold phase's freshness
    depends on the caller.

    Args:
        plugin_root: Installed plugin root, or None.
        sample_interval_seconds: Continuous sampler polling interval.

    Returns:
        NFR1Report.
    """
    registry = components.build_default_registry(plugin_root)
    measurements = {}
    for phase in (harness.PHASE_COLD, harness.PHASE_WARM):
        session = harness.MeasurementSession(
            phase=phase,
            registry=registry,
            sample_interval_seconds=sample_interval_seconds,
        )
        session.open()
        time.sleep(sample_interval_seconds * 3)
        measurements[phase] = session.close()
    return harness.build_report(
        plugin_root=plugin_root,
        cold=measurements[harness.PHASE_COLD],
        warm=measurements[harness.PHASE_WARM],
        repo_root=_repo_root(),
        registry=registry,
    )


def run_observed_phase(
    phase,
    plugin_root,
    transcript=None,
    required=harness.REQUIRED_TOOL_CALLS,
    max_polls=None,
    include_sidechains=False,
    sample_interval_seconds=0.05,
    poll_seconds=driver.DEFAULT_POLL_SECONDS,
    from_current_record=False,
    skip_leading=0,
):
    """Measure one phase in observer mode, driven by real tool calls.

    This is the mode ``run_measurement`` could not offer. It opens a window, tails
    the live Claude Code transcript, and calls ``mark_tool_call()`` once per real
    tool call the session issues, so the count is observed rather than absent.

    One phase per invocation is deliberate. A cold count is only cold if the
    window opens before the session has issued anything, which means a separate
    run against a fresh session. Both phases in one interpreter -- what
    ``run_measurement`` does -- can only produce a cold-labelled slot, not a cold
    measurement.

    Args:
        phase: harness.PHASE_COLD or harness.PHASE_WARM.
        plugin_root: Installed plugin root, or None.
        transcript: Transcript path, or None to use the newest for this project.
        required: Tool calls the criterion requires inside the window.
        max_polls: Optional cap on poll iterations before giving up.
        include_sidechains: Whether subagent tool calls count.
        from_current_record: Anchor the tail at the start of the transcript's last
            assistant record instead of at end-of-file, so a single assistant message
            can carry both this launch and the tool calls being measured. Without it
            the launch must happen in an earlier turn, and the retained Stop hook
            fires at that turn boundary, which the guard correctly rejects.
        skip_leading: Discard this many leading tool calls, normally 1 to exclude the
            call that launched the measurement.
        sample_interval_seconds: Continuous sampler polling interval.
        poll_seconds: Transcript polling interval.

    Returns:
        Dict describing the phase result, including why it is not a full report.
    """
    if transcript is None:
        transcript = newest_transcript_for_this_project()
    if transcript is None:
        return {
            "phase": phase,
            "verdict": harness.VERDICT_INDETERMINATE,
            "error": "no transcript found; nothing to observe",
        }

    registry = components.build_default_registry(plugin_root)
    session = harness.MeasurementSession(
        phase=phase,
        registry=registry,
        sample_interval_seconds=sample_interval_seconds,
    )
    start_offset = driver.last_assistant_record_offset(transcript) if from_current_record else None
    tail = driver.TranscriptTail(
        transcript,
        session_id=driver.session_id_from_path(transcript),
        include_sidechains=include_sidechains,
        start_offset=start_offset,
        skip_leading=skip_leading,
    )
    try:
        measurement, observed = driver.drive(session, tail, required, poll_seconds=poll_seconds, max_polls=max_polls)
    except driver.TranscriptRewritten as exc:
        return {
            "phase": phase,
            "verdict": harness.VERDICT_INDETERMINATE,
            "void_reason": str(exc),
            "transcript": transcript,
            "note": (
                "the transcript stopped being append-only mid-window, so the "
                "observation is void; no partial count is reported because a "
                "partial count here is indistinguishable from a short window"
            ),
        }

    payload = measurement.to_dict()
    payload["transcript"] = transcript
    payload["anchored_at"] = "current_assistant_record" if from_current_record else "end_of_file"
    payload["leading_tool_calls_skipped"] = skip_leading
    payload["observed_tool_calls"] = observed
    payload["single_phase_note"] = (
        "this is one phase, not an NFR-1 report. Assembling a report from two "
        "separately observed phases needs a Measurement that can round-trip "
        "through JSON, which harness.py does not provide; build_report takes "
        "Measurement objects only. Until that exists, the phases cannot be "
        "combined across invocations."
    )
    return payload


def newest_transcript_for_this_project():
    """Return the newest transcript Claude Code has written for this repository.

    Returns:
        str or None: Transcript path, or None when none exists.
    """
    return driver.newest_transcript(driver.transcript_dir_for(_repo_root()))


def build_combined_report(cold_json, warm_json, plugin_root):
    """Assemble one NFR-1 report from two separately observed phase files.

    Cold and warm cannot be observed in the same invocation: a cold count is only
    cold when the window opens before the session has issued anything, which means
    a fresh session. Each phase is therefore measured on its own and written to
    JSON, and this reads both back.

    Args:
        cold_json: Path to a cold phase written by --observe --phase cold.
        warm_json: Path to a warm phase written by --observe --phase warm.
        plugin_root: Installed plugin root, or None.

    Returns:
        Dict: the full NFR1Report payload.

    Raises:
        ValueError: If either file is not the phase it was supplied as, or is
            missing anything the verdict depends on.
    """
    phases = {}
    for label, path in ((harness.PHASE_COLD, cold_json), (harness.PHASE_WARM, warm_json)):
        with open(path, "r", encoding="utf-8") as handle:
            restored = harness.measurement_from_dict(json.load(handle))
        if restored.phase != label:
            raise ValueError("%s was supplied as the %s phase but records phase %r" % (path, label, restored.phase))
        phases[label] = restored

    report = harness.build_report(
        plugin_root=plugin_root,
        cold=phases[harness.PHASE_COLD],
        warm=phases[harness.PHASE_WARM],
        repo_root=_repo_root(),
    )
    return report.to_dict()


def _spawn_marked_child():
    """Spawn a short-lived child process carrying the self-test marker.

    Returns:
        The Popen handle for the spawned child.
    """
    code = "import time; time.sleep(0.6)  # %s" % SELF_TEST_MARKER
    return subprocess.Popen(
        [sys.executable, "-c", code],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def run_self_test(sample_interval_seconds=0.03):
    """Prove the harness can fail by making it observe a real spawn it must count.

    A component owning the self-test marker is registered with the plugin-counted role.
    A real child process carrying that marker is spawned inside a driven measurement
    window. If the harness returns anything other than FAIL, it did not detect a
    process it was explicitly configured to detect, and is therefore indistinguishable
    from a no-op.

    Args:
        sample_interval_seconds: Continuous sampler polling interval.

    Returns:
        Dict describing the outcome, including the observed verdict.
    """
    registry = components.ComponentRegistry()
    registry.register(
        components.ComponentSpec(
            key=components.KEY_PLUGIN,
            role=components.ROLE_PLUGIN_COUNTED,
            markers=[SELF_TEST_MARKER],
            description="synthetic stand-in for the plugin, owning the self-test marker",
        )
    )
    registry.register(
        components.ComponentSpec(
            key=components.KEY_RETAINED_USER_HOOKS,
            role=components.ROLE_PERMITTED_EXCLUSION,
            markers=["stop_notifier"],
            justification="ADR-010, mirrored from the default registry for fidelity",
        )
    )

    session = harness.MeasurementSession(
        phase=harness.PHASE_COLD,
        registry=registry,
        sample_interval_seconds=sample_interval_seconds,
        stop_log_path=os.devnull,
    )
    children = []

    def one_tool_call():
        """Stand in for one tool call, spawning the marked child on the first call."""
        if not children:
            children.append(_spawn_marked_child())
        time.sleep(sample_interval_seconds)

    measurement = session.run_driven(one_tool_call, harness.REQUIRED_TOOL_CALLS)
    for child in children:
        child.wait(timeout=10)

    verdict, reasons = measurement.verdict()
    plugin_count = measurement.authoritative_attribution.plugin_count
    return {
        "expected_verdict": harness.VERDICT_FAIL,
        "observed_verdict": verdict,
        "reasons": reasons,
        "plugin_attributable_count": plugin_count,
        "endpoint_plugin_count": measurement.endpoint_attribution.plugin_count,
        "sampled_plugin_count": measurement.sampled_attribution.plugin_count,
        "sampler_poll_count": measurement.probe_summary["sampler"]["poll_count"],
        "passed": verdict == harness.VERDICT_FAIL and plugin_count > 0,
        "note": (
            "endpoint and sampled counts may legitimately differ. A two-endpoint diff "
            "cannot observe a process that starts and exits inside the window, and a "
            "sampler that never got scheduled observes nothing at all. The verdict "
            "reads the union of both, so neither blind spot can produce a pass."
        ),
    }


def main(argv=None):
    """Parse arguments and emit a JSON report.

    Args:
        argv: Argument vector, or None to read sys.argv.

    Returns:
        Process exit status.
    """
    parser = argparse.ArgumentParser(description="NFR-1 per-component process-count measurement harness")
    parser.add_argument(
        "--plugin-root",
        default=None,
        help="path to the installed plugin root; omit when no plugin exists yet",
    )
    parser.add_argument("--json-out", default=None, help="write the JSON report to this file")
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="prove the harness can fail by making it observe a real marked spawn",
    )
    parser.add_argument(
        "--sample-interval",
        type=float,
        default=0.05,
        help="continuous sampler polling interval in seconds",
    )
    parser.add_argument(
        "--observe",
        action="store_true",
        help="measure one phase in observer mode, driven by real tool calls in the live transcript",
    )
    parser.add_argument(
        "--phase",
        choices=(harness.PHASE_COLD, harness.PHASE_WARM),
        default=harness.PHASE_WARM,
        help="which phase --observe is measuring; a cold run must start before the session issues anything",
    )
    parser.add_argument(
        "--transcript",
        default=None,
        help="transcript path to tail; defaults to the newest one for this project",
    )
    parser.add_argument(
        "--max-polls",
        type=int,
        default=None,
        help="stop after this many polls instead of waiting indefinitely for the required tool calls",
    )
    parser.add_argument(
        "--include-sidechains",
        action="store_true",
        help="count subagent tool calls too, which changes what the number means",
    )
    parser.add_argument(
        "--from-current-record",
        action="store_true",
        help="anchor the tail at the last assistant record so one message can launch and be measured",
    )
    parser.add_argument(
        "--skip-leading",
        type=int,
        default=0,
        help="discard this many leading tool calls; use 1 to exclude the launching call itself",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="combine two separately observed phase files into one NFR-1 report",
    )
    parser.add_argument("--cold-json", default=None, help="cold phase file, for --report")
    parser.add_argument("--warm-json", default=None, help="warm phase file, for --report")
    args = parser.parse_args(argv)

    if args.self_test:
        outcome = run_self_test()
        print(json.dumps(outcome, indent=2))
        return 0 if outcome["passed"] else 1

    if args.report:
        if not args.cold_json or not args.warm_json:
            parser.error("--report needs both --cold-json and --warm-json")
        payload = build_combined_report(args.cold_json, args.warm_json, args.plugin_root)
        text = json.dumps(payload, indent=2, default=str)
        if args.json_out:
            with open(args.json_out, "w", encoding="utf-8") as handle:
                handle.write(text)
        print(text)
        return 0

    if args.observe:
        outcome = run_observed_phase(
            phase=args.phase,
            plugin_root=args.plugin_root,
            transcript=args.transcript,
            max_polls=args.max_polls,
            include_sidechains=args.include_sidechains,
            sample_interval_seconds=args.sample_interval,
            from_current_record=args.from_current_record,
            skip_leading=args.skip_leading,
        )
        text = json.dumps(outcome, indent=2, default=str)
        if args.json_out:
            with open(args.json_out, "w", encoding="utf-8") as handle:
                handle.write(text)
        print(text)
        return 1 if ("error" in outcome or "void_reason" in outcome) else 0

    report = run_measurement(args.plugin_root, args.sample_interval)
    payload = report.to_dict()
    text = json.dumps(payload, indent=2, default=str)
    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as handle:
            handle.write(text)
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())

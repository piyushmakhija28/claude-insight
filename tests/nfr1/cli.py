"""Runnable entry point for the NFR-1 per-component process-count harness.

Usage:
    python tests/nfr1/cli.py --plugin-root <path> [--json-out <file>]
    python tests/nfr1/cli.py --self-test

Invoke by path, not with -m. An unrelated ``tests`` distribution in this environment's
site-packages shadows the repository's tests directory, so ``python -m tests.nfr1.cli``
cannot resolve. The same shadowing is why tests/test_nfr1_harness.py imports the
package as top-level ``nfr1``.

Against the current tree the harness reports NOT_MEASURABLE, which is the correct and
intended result: no plugin exists to install (issue V2-015) and the PreToolUse and
PostToolUse hook registrations have not been deleted (issue V2-027). It will not report
PASS until both land and a real measurement runs.

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

from nfr1 import components, harness  # noqa: E402

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
    args = parser.parse_args(argv)

    if args.self_test:
        outcome = run_self_test()
        print(json.dumps(outcome, indent=2))
        return 0 if outcome["passed"] else 1

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

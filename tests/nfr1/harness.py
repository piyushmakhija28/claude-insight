"""Measurement session, turn-boundary guard, and cold/warm verdict for NFR-1.

Acceptance criteria implemented here:

    AC 1  A process count taken immediately before and after ten tool calls in a fresh
          session, attributed per component. MeasurementSession enforces the count of
          ten and refuses to produce a verdict on any other number.
    AC 2  Pass is zero processes attributable to the plugin. Computed from the
          attribution roles, not from a total.
    AC 3  The retained user-level Stop and Notification hooks are excluded. Enforced by
          the registry's single-exclusion cardinality, not by an ad hoc filter.
    AC 4  The measurement window must not span a response-turn boundary. TurnBoundaryGuard
          watches three independent witnesses and INVALIDATES the measurement when any
          fires. Crossing a boundary is not a FAIL, it is an INVALID measurement, and
          conflating the two would blame the plugin for the retained Stop hook.
    AC 5  Cold and warm counts are reported as two separate numbers, never blended.
          NFR1Report holds them as distinct measurements, exposes no combined figure,
          and refuses a verdict unless both are present.
    AC 6  Delegated to plugin_gate, which decides independently of any count.

Verdict vocabulary is deliberately four-valued. PASS, FAIL, INDETERMINATE and
NOT_MEASURABLE are different claims, and collapsing the last two into PASS is how a
measurement harness turns into a no-op.
"""

import os
import time

from . import attribution as attribution_mod
from . import components, plugin_gate, process_probe

VERDICT_PASS = "PASS"
VERDICT_FAIL = "FAIL"
VERDICT_INDETERMINATE = "INDETERMINATE"
VERDICT_NOT_MEASURABLE = "NOT_MEASURABLE"

PHASE_COLD = "cold"
PHASE_WARM = "warm"

REQUIRED_TOOL_CALLS = 10


class TurnBoundaryGuard(object):
    """Detects whether a measurement window spanned a response-turn boundary.

    The retained Stop hook fires every response turn and holds 17 spawn sites, so a
    window that crosses a turn records spawns from a component the design deliberately
    keeps. The criterion forbids such a window outright. Detection uses three
    independent witnesses so that no single missing signal silently disarms the guard:

        stop_log        The Stop hook's log file grew or its modification time moved.
        stop_process    A process attributed to the permitted exclusion appeared inside
                        the window.
        declared        The caller explicitly declared a boundary through
                        note_turn_boundary, for a driver that knows.

    Attributes:
        stop_log_path: Path watched by the stop_log witness, or None to disable it.
    """

    def __init__(self, stop_log_path=None):
        self.stop_log_path = stop_log_path or default_stop_log_path()
        self._opened = False
        self._baseline = None
        self._declared = False
        self._declared_reasons = []

    def _probe_stop_log(self):
        """Return the watched log's size and modification time, or None if absent."""
        if not self.stop_log_path:
            return None
        try:
            stat = os.stat(self.stop_log_path)
        except OSError:
            return None
        return (stat.st_size, stat.st_mtime)

    def open(self):
        """Record the baseline state at the start of the measurement window."""
        self._opened = True
        self._declared = False
        self._declared_reasons = []
        self._baseline = self._probe_stop_log()

    def note_turn_boundary(self, reason):
        """Declare that a response-turn boundary occurred inside the window.

        Args:
            reason: Why the caller believes a boundary occurred.
        """
        self._declared = True
        self._declared_reasons.append(reason)

    def evaluate(self, attribution_result=None):
        """Decide whether the window stayed inside a single response turn.

        Args:
            attribution_result: Optional AttributionResult for the window, used by the
                stop_process witness.

        Returns:
            Dict carrying each witness's finding and a boolean crossed flag.
        """
        if not self._opened:
            raise RuntimeError("TurnBoundaryGuard.evaluate called before open")

        current = self._probe_stop_log()
        log_witness = {
            "witness": "stop_log",
            "path": self.stop_log_path,
            "watched": self._baseline is not None or current is not None,
            "baseline": self._baseline,
            "current": current,
        }
        if self._baseline is None and current is None:
            log_witness["fired"] = False
            log_witness["note"] = (
                "stop hook log absent at both endpoints; this witness contributed no "
                "evidence and must not be read as evidence of no boundary"
            )
        else:
            log_witness["fired"] = self._baseline != current

        excluded_seen = 0
        if attribution_result is not None:
            excluded_seen = attribution_result.excluded_count
        process_witness = {
            "witness": "stop_process",
            "fired": excluded_seen > 0,
            "excluded_processes_observed": excluded_seen,
            "note": (
                "a process attributed to the retained Stop or Notification hook appeared "
                "inside the window, which is only possible across a turn boundary"
            ),
        }

        declared_witness = {
            "witness": "declared",
            "fired": self._declared,
            "reasons": list(self._declared_reasons),
        }

        witnesses = [log_witness, process_witness, declared_witness]
        crossed = any(w["fired"] for w in witnesses)
        return {
            "crossed": crossed,
            "witnesses": witnesses,
            "effect": (
                "measurement INVALID: the window spanned a response-turn boundary, which "
                "the criterion forbids. This is not an NFR-1 failure."
                if crossed
                else "window stayed inside a single response turn"
            ),
        }


def default_stop_log_path():
    """Return the retained Stop hook's log path as hooks/ide_paths.py computes it.

    Returns:
        Absolute path string, or None when it cannot be determined.
    """
    home = os.path.expanduser("~")
    return os.path.join(home, ".claude", "memory", "logs", "stop-notifier.log")


class Measurement(object):
    """One cold or warm measurement over a single response turn.

    Attributes:
        phase: PHASE_COLD or PHASE_WARM.
        tool_calls: How many tool calls the driver recorded inside the window.
        endpoint_attribution: AttributionResult over the before/after endpoint delta,
            which is the criterion's literal wording.
        sampled_attribution: AttributionResult over the continuously sampled delta,
            which additionally catches short-lived spawns.
        turn_boundary: TurnBoundaryGuard evaluation for this window.
        probe_summary: Backend and sampler diagnostics.
    """

    def __init__(
        self,
        phase,
        tool_calls,
        endpoint_attribution,
        sampled_attribution,
        union_attribution,
        turn_boundary,
        probe_summary,
    ):
        self.phase = phase
        self.tool_calls = tool_calls
        self.endpoint_attribution = endpoint_attribution
        self.sampled_attribution = sampled_attribution
        self.union_attribution = union_attribution
        self.turn_boundary = turn_boundary
        self.probe_summary = probe_summary

    @property
    def authoritative_attribution(self):
        """Return the attribution the verdict is computed from.

        The verdict uses the UNION of the endpoint delta and the sampled delta, never
        one in place of the other. Each source has a blind spot the other does not: the
        endpoint delta cannot see a process that starts and exits inside the window,
        and the sampler sees nothing at all if the window closes before its thread is
        first scheduled. An earlier revision of this harness preferred the sampled
        delta outright, and a zero-poll window therefore returned an empty set that
        silently masked a correctly detected spawn and reported a pass. That defect was
        caught by the real-spawn test in tests/test_nfr1_harness.py. A union can only
        add observations, never remove them, so it cannot reproduce that failure.
        """
        return self.union_attribution

    def verdict(self):
        """Return this measurement's four-valued verdict and its reasons.

        Returns:
            Tuple of (verdict, list of reason strings).
        """
        reasons = []
        if self.turn_boundary.get("crossed"):
            reasons.append("window spanned a response-turn boundary, which the criterion forbids")
            return VERDICT_INDETERMINATE, reasons

        if self.tool_calls != REQUIRED_TOOL_CALLS:
            reasons.append(
                "criterion requires exactly %d tool calls in the window; the driver "
                "recorded %d" % (REQUIRED_TOOL_CALLS, self.tool_calls)
            )
            return VERDICT_INDETERMINATE, reasons

        result = self.authoritative_attribution
        if result.plugin_count > 0:
            reasons.append("%d process(es) attributable to the plugin; pass requires 0" % result.plugin_count)
            return VERDICT_FAIL, reasons

        unattributed = len(result.unattributed)
        if unattributed > 0:
            reasons.append(
                "%d observed process(es) could not be attributed, and could not be shown "
                "not to descend from the plugin either, because their ancestry could not "
                "be walked back to a process that predates the window" % unattributed
            )
            return VERDICT_INDETERMINATE, reasons

        proved = len(result.not_plugin_descended)
        reasons.append(
            "0 processes attributable to the plugin; %d further process(es) walked back "
            "to the pre-window baseline with no plugin anywhere on the chain" % proved
        )
        return VERDICT_PASS, reasons

    def to_dict(self):
        """Return a JSON-serialisable view of this measurement."""
        verdict, reasons = self.verdict()
        return {
            "phase": self.phase,
            "verdict": verdict,
            "reasons": reasons,
            "tool_calls_recorded": self.tool_calls,
            "tool_calls_required": REQUIRED_TOOL_CALLS,
            "turn_boundary": self.turn_boundary,
            "endpoint_delta": self.endpoint_attribution.to_dict(),
            "sampled_delta": (self.sampled_attribution.to_dict() if self.sampled_attribution else None),
            "union_delta": self.union_attribution.to_dict(),
            "authoritative_source": "union_delta",
            "authoritative_source_rationale": (
                "union of the endpoint and sampled deltas; neither source alone is "
                "sound, and preferring one lets the other's blind spot become a pass"
            ),
            "probe": self.probe_summary,
        }


class MeasurementSession(object):
    """Drives one cold or warm measurement window.

    Two usage modes exist because the criterion's ten tool calls are Claude Code tool
    calls, which this process cannot itself issue.

        Observer mode. An external driver calls open(), then mark_tool_call() once per
        tool call, then close(). This is the mode a real NFR-1 run uses.

        Driven mode. run_driven() invokes a supplied callable ten times inside the
        window. This exists for self-test, where the callable is synthetic.

    Either way the recorded count is checked against ten, and any other number yields
    INDETERMINATE rather than a verdict.
    """

    def __init__(
        self,
        phase,
        registry,
        backend=None,
        sample_interval_seconds=0.05,
        stop_log_path=None,
    ):
        if phase not in (PHASE_COLD, PHASE_WARM):
            raise ValueError("phase must be %r or %r, got %r" % (PHASE_COLD, PHASE_WARM, phase))
        self.phase = phase
        self.registry = registry
        self.backend = backend
        self.sample_interval_seconds = sample_interval_seconds
        self.guard = TurnBoundaryGuard(stop_log_path)
        self._before = None
        self._sampler = None
        self._tool_calls = 0
        self._closed = False

    def open(self):
        """Capture the before snapshot and start sampling."""
        if self._before is not None:
            raise RuntimeError("session already opened")
        self.guard.open()
        self._before = process_probe.take_snapshot(self.backend)
        self._sampler = process_probe.ContinuousSampler(self.sample_interval_seconds, self.backend)
        self._sampler.start()

    def mark_tool_call(self):
        """Record that one tool call occurred inside the window."""
        if self._before is None or self._closed:
            raise RuntimeError("mark_tool_call outside an open session")
        self._tool_calls += 1

    def note_turn_boundary(self, reason):
        """Forward a caller-declared turn boundary to the guard."""
        self.guard.note_turn_boundary(reason)

    def close(self):
        """Stop sampling, capture the after snapshot, and build the Measurement.

        Returns:
            Measurement for this window.
        """
        if self._before is None:
            raise RuntimeError("session was never opened")
        if self._closed:
            raise RuntimeError("session already closed")
        self._closed = True
        self._sampler.stop()
        after = process_probe.take_snapshot(self.backend)

        ancestry = attribution_mod.build_ancestry_index(after)
        for pid, record in attribution_mod.build_ancestry_index(self._before).items():
            ancestry.setdefault(pid, record)
        for pid, record in attribution_mod.index_from_records(self._sampler.seen_records().values()).items():
            ancestry.setdefault(pid, record)

        endpoint_records = process_probe.endpoint_delta(self._before, after)
        sampled_records = self._sampler.sampled_delta(self._before)

        merged = {}
        for record in list(endpoint_records) + list(sampled_records):
            merged[record.key] = record
        union_records = sorted(merged.values(), key=lambda r: r.pid)

        baseline_pids = set(record.pid for record in self._before.records.values())

        endpoint_attr = attribution_mod.attribute(
            endpoint_records, self.registry, ancestry, baseline_pids=baseline_pids
        )
        sampled_attr = attribution_mod.attribute(sampled_records, self.registry, ancestry, baseline_pids=baseline_pids)
        union_attr = attribution_mod.attribute(union_records, self.registry, ancestry, baseline_pids=baseline_pids)

        boundary = self.guard.evaluate(union_attr)
        sampler_summary = self._sampler.to_dict()
        sampler_summary["contributed_observations"] = self._sampler.poll_count > 0
        if self._sampler.poll_count == 0:
            sampler_summary["zero_poll_warning"] = (
                "the sampler completed no polls, so it contributed nothing to this "
                "measurement and the union rests entirely on the endpoint delta; "
                "short-lived spawns may have gone unobserved"
            )
        probe_summary = {
            "before": self._before.to_dict(),
            "after": after.to_dict(),
            "sampler": sampler_summary,
            "backend_is_perturbing": self._before.is_perturbing or after.is_perturbing,
            "window_seconds": after.captured_at - self._before.captured_at,
        }
        return Measurement(
            phase=self.phase,
            tool_calls=self._tool_calls,
            endpoint_attribution=endpoint_attr,
            sampled_attribution=sampled_attr,
            union_attribution=union_attr,
            turn_boundary=boundary,
            probe_summary=probe_summary,
        )

    def run_driven(self, tool_call, count=REQUIRED_TOOL_CALLS):
        """Open, invoke a callable count times, and close.

        Args:
            tool_call: Zero-argument callable standing in for one tool call.
            count: How many times to invoke it. Values other than REQUIRED_TOOL_CALLS
                are permitted so that a negative test can prove the count check fires.

        Returns:
            Measurement for this window.
        """
        self.open()
        try:
            for _ in range(count):
                tool_call()
                self.mark_tool_call()
        finally:
            measurement = self.close()
        return measurement


class NFR1Report(object):
    """The full NFR-1 result: structural gates plus separate cold and warm measurements.

    Cold and warm are held as distinct attributes and no combined figure is exposed.
    Cold-start benchmarking is a named anti-pattern, and averaging a cold count with a
    warm one produces a number that describes neither. A report missing either phase
    yields INDETERMINATE, which is what makes the separation enforced rather than
    merely documented.
    """

    def __init__(self, structural, cold=None, warm=None, context=None):
        self.structural = structural
        self.cold = cold
        self.warm = warm
        self.context = context or {}

    def overall_verdict(self):
        """Return the four-valued NFR-1 verdict and its reasons.

        Returns:
            Tuple of (verdict, list of reason strings).
        """
        reasons = []
        structural_status = self.structural.get("overall")
        if structural_status == plugin_gate.STATUS_FAIL:
            reasons.append(
                "structural gate failure (%s) fails NFR-1 outright, regardless of the "
                "process count" % ", ".join(self.structural.get("blocking_failures", []))
            )
            return VERDICT_FAIL, reasons

        if self.cold is None or self.warm is None:
            missing = [name for name, value in ((PHASE_COLD, self.cold), (PHASE_WARM, self.warm)) if value is None]
            reasons.append(
                "cold and warm counts must both be reported as separate numbers; " "missing: %s" % ", ".join(missing)
            )
            if structural_status == plugin_gate.STATUS_NOT_MEASURABLE:
                reasons.append(
                    "structural gates are NOT_MEASURABLE because the plugin does not " "exist yet (issue V2-015)"
                )
                return VERDICT_NOT_MEASURABLE, reasons
            return VERDICT_INDETERMINATE, reasons

        cold_verdict, cold_reasons = self.cold.verdict()
        warm_verdict, warm_reasons = self.warm.verdict()
        reasons.extend("cold: %s" % r for r in cold_reasons)
        reasons.extend("warm: %s" % r for r in warm_reasons)

        if VERDICT_FAIL in (cold_verdict, warm_verdict):
            return VERDICT_FAIL, reasons
        if structural_status == plugin_gate.STATUS_NOT_MEASURABLE:
            reasons.append(
                "structural gates are NOT_MEASURABLE because the plugin does not exist " "yet (issue V2-015)"
            )
            return VERDICT_NOT_MEASURABLE, reasons
        if VERDICT_INDETERMINATE in (cold_verdict, warm_verdict):
            return VERDICT_INDETERMINATE, reasons
        return VERDICT_PASS, reasons

    def to_dict(self):
        """Return the complete JSON-serialisable report."""
        verdict, reasons = self.overall_verdict()
        return {
            "requirement": {
                "prd": "NFR-1",
                "srs": "NFR-7",
                "issue_key": "V2-003",
                "github_issue": 259,
            },
            "generated_at": time.time(),
            "verdict": verdict,
            "reasons": reasons,
            "closes_after": ["V2-015", "V2-027"],
            "closure_note": (
                "This issue cannot close on a harness that has never produced a pass. "
                "The measurement requires a plugin to install (V2-015) and the hook "
                "registrations to be deleted (V2-027); neither exists."
            ),
            "structural_gates": self.structural,
            "cold": self.cold.to_dict() if self.cold else None,
            "warm": self.warm.to_dict() if self.warm else None,
            "blending_policy": (
                "cold and warm are reported as two separate numbers and are never "
                "blended; no combined figure is computed or exposed"
            ),
            "context": self.context,
        }


def build_report(plugin_root=None, cold=None, warm=None, repo_root=None, registry=None):
    """Assemble a full NFR-1 report.

    Args:
        plugin_root: Installed plugin root, or None when no plugin exists yet.
        cold: Measurement for the cold phase, or None.
        warm: Measurement for the warm phase, or None.
        repo_root: Repository root used for the Stop-hook spawn-floor description.
        registry: ComponentRegistry to record in the report, or None to build the
            default one for plugin_root.

    Returns:
        NFR1Report.
    """
    structural = plugin_gate.run_structural_gates(plugin_root)
    effective_registry = registry or components.build_default_registry(plugin_root)
    context = {
        "platform_support": (
            "Windows-native. Primary backend is psutil (declared dependency, in-process "
            "Win32 API, spawns nothing). Fallback is PowerShell Get-CimInstance "
            "Win32_Process. No POSIX-only mechanism is used on any code path."
        ),
        "psutil_available": process_probe.psutil_available(),
        "registry": effective_registry.to_dict(),
        "stop_hook_spawn_floor": components.describe_stop_hook_spawn_floor(repo_root),
    }
    return NFR1Report(structural, cold, warm, context)

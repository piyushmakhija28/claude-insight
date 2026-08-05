"""The call-graph risk signal and its coverage precondition.

SRS FR-22's acceptance criterion ends "never the current truncated builder".
That clause is the reason this module exists: it turns a review instruction
into a precondition the selector enforces, so a selector run against a
truncated graph fails loudly instead of producing plausible output from
worthless input.

Two truncation sites bound before issue #265 and both are now uncapped by
default, but both remain operator-overridable through environment variables.
:func:`probe_builder_coverage` reads those overrides and reports coverage as
incomplete when either is in force, which is the only condition under which the
shipping builder can still truncate.

Windows-safe: ASCII only.
"""

import os
from dataclasses import dataclass
from typing import Any, Mapping, Optional, Tuple

ENV_MAX_FILES = "CLAUDE_CG_MAX_FILES"
ENV_MAX_PATHS = "CLAUDE_CG_MAX_PATHS"

SOURCE_BUILDER = "builder"
SOURCE_SNAPSHOT = "snapshot"
SOURCE_UNAVAILABLE = "unavailable"

RISK_LOW = "low"


class TruncatedRiskSignal(Exception):
    """Raised when selection is attempted against a knowingly incomplete graph.

    Carries the caps that were in force so the message names the override to
    unset, rather than reporting a bare refusal.
    """

    def __init__(self, caps: Mapping[str, str]):
        self.caps = dict(caps)
        super().__init__(
            "call-graph risk signal is not coverage-complete; caps in force: {}. "
            "Unset them, supply a coverage-complete signal, or pass "
            "accept_partial_coverage=True to record the acceptance explicitly.".format(
                ", ".join("{}={}".format(key, value) for key, value in sorted(self.caps.items())) or "none recorded"
            )
        )


@dataclass(frozen=True)
class RiskSignal:
    """Call-graph risk input to selection.

    Attributes:
        risk_level: ``"low"``, ``"medium"`` or ``"high"`` as the impact
            analyser reports it.
        danger_zone_count: Number of high-fan-in methods the analysis found.
        coverage_complete: Whether the graph behind this signal covered every
            eligible file and path.
        source: Where the signal came from -- a live builder run, a recorded
            snapshot, or nothing at all.
        caps_in_force: Truncation overrides observed when the signal was taken.
    """

    risk_level: str
    danger_zone_count: int
    coverage_complete: bool
    source: str
    caps_in_force: Tuple[Tuple[str, str], ...] = ()

    @classmethod
    def unavailable(cls) -> "RiskSignal":
        """Return the signal used when no call graph is available at all.

        Coverage is reported as complete because nothing was truncated -- there
        was nothing. The distinction matters: "no graph" is an honest absence,
        while "a graph that silently dropped a third of the repository" is the
        defect this precondition guards against.
        """
        return cls(RISK_LOW, 0, True, SOURCE_UNAVAILABLE)

    @classmethod
    def from_impact_analysis(
        cls, analysis: Mapping[str, Any], coverage_complete: Optional[bool] = None
    ) -> "RiskSignal":
        """Build a signal from ``analyze_impact_before_change`` output.

        Args:
            analysis: The analyser's result mapping.
            coverage_complete: Explicit coverage verdict. When omitted the
                environment is probed, because the shipping builder reports no
                coverage manifest of its own.

        Returns:
            The corresponding :class:`RiskSignal`.
        """
        if not analysis.get("call_graph_available", False):
            return cls.unavailable()
        complete, caps = probe_builder_coverage()
        if coverage_complete is not None:
            complete = coverage_complete
        danger_zones = analysis.get("danger_zones") or ()
        return cls(
            risk_level=str(analysis.get("risk_level") or RISK_LOW),
            danger_zone_count=len(danger_zones),
            coverage_complete=complete,
            source=SOURCE_BUILDER,
            caps_in_force=caps,
        )

    def require_coverage(self, accept_partial: bool = False) -> None:
        """Enforce the coverage precondition.

        Args:
            accept_partial: Set by a caller that has consciously decided to
                proceed on a partial graph. The acceptance is the caller's to
                record; this module will not infer it.

        Raises:
            TruncatedRiskSignal: When coverage is incomplete and the caller has
                not accepted that.
        """
        if self.coverage_complete or accept_partial:
            return
        raise TruncatedRiskSignal(dict(self.caps_in_force))


def probe_builder_coverage(environ: Optional[Mapping[str, str]] = None) -> Tuple[bool, Tuple[Tuple[str, str], ...]]:
    """Report whether the shipping call-graph builder is currently uncapped.

    Both truncation sites default to unbounded since issue #265 and are raised
    only by an operator setting an environment override. A value that does not
    parse as a positive integer is ignored by the builder itself, so it is
    ignored here too rather than being reported as a cap that is not in force.

    Args:
        environ: Environment mapping to read. Defaults to the live process
            environment; supplying one makes the probe testable without
            mutating global state.

    Returns:
        A ``(coverage_complete, caps_in_force)`` pair.
    """
    source = os.environ if environ is None else environ
    caps = []
    for name in (ENV_MAX_FILES, ENV_MAX_PATHS):
        raw = source.get(name)
        if not raw:
            continue
        try:
            value = int(raw)
        except (TypeError, ValueError):
            continue
        if value > 0:
            caps.append((name, str(value)))
    return (not caps), tuple(caps)

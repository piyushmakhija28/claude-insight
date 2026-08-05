"""ADR-016 mechanism 2: a renewable lease instead of a fixed deadline.

A deadline asks "how long have you been running" and kills whatever answers
wrongly. A lease asks "when did you last make progress" and only kills silence.
The difference is the whole point of NFR-2: a task that streams output for six
hours renews its lease six hours' worth of times and is never touched, while a
task that produced nothing for one renewal interval is not slow, it is stuck.

WHY THE RENEWAL INTERVAL IS NOT A TIMEOUT IN DISGUISE
-----------------------------------------------------
It reads a clock, so the distinction has to be stated precisely rather than
asserted. A deadline is a bound on total elapsed time and is therefore
monotonically approached by every run, healthy or not. A renewal interval is a
bound on the gap between consecutive progress events, and is *reset* by
progress; it is approached only by a run that has stopped producing evidence of
work. Total runtime does not appear in the predicate at all. That is why
ADR-016 calls this proving liveness by renewal rather than assuming it by a
clock.

The interval defaults to ``None``, meaning no expiry at all, so the enclosing
pipeline task is unbounded unless an operator opts in -- which is what NFR-2's
"default to unbounded or user-overridable" requires.

DURABILITY, MEASURED RATHER THAN ASSUMED
----------------------------------------
A lease exists to bound the consequences of a process that stopped making
progress, including one that died. A lease held only in the memory of the
process it is supposed to outlive does not survive the crash it exists to bound.

That is the state this repository is actually in. Both import paths the
checkpointer tries -- ``langgraph.checkpoint.sqlite`` and
``langgraph_checkpoint_sqlite`` -- raise ImportError in the live environment,
despite ``langgraph-checkpoint-sqlite`` being a declared dependency in
``pyproject.toml``, so the durable checkpointer silently degrades to an
in-memory saver. :func:`durable_state_available` probes that directly instead of
trusting the declaration, and a lease constructed while it is false marks itself
degraded and says so once, out loud. It still bounds a hang inside a live
process, which is the failure this mechanism is placed against on the pipeline
path; it does not and cannot bound a lease-holder that has already vanished.
Recording the gap is the honest position, and it is the one ADR-016's own
"skill gap disclosed" paragraph models.
"""

import time

try:
    from loguru import logger
except ImportError:  # pragma: no cover - exercised only where loguru is absent
    import logging

    logger = logging.getLogger(__name__)


_DURABLE_STATE_WARNED = False


def durable_state_available():
    """Report whether a durable checkpoint backend can actually be imported.

    The two import paths tried here are the same two
    ``langgraph_engine.checkpointer`` tries, restated rather than imported so
    that probing durability does not drag in the orchestration engine. A
    conformance test pins the two lists together.

    Returns:
        bool: True when a SQLite-backed saver is importable.
    """
    try:
        from langgraph.checkpoint.sqlite import SqliteSaver  # noqa: F401,PLC0415

        return True
    except ImportError:
        pass
    try:
        from langgraph_checkpoint_sqlite import SqliteSaver  # noqa: F401,PLC0415

        return True
    except ImportError:
        return False


class LeaseExpired(RuntimeError):
    """Raised when a lease went unrenewed for longer than its renewal interval.

    This is a no-progress verdict, not a slowness verdict: the holder produced no
    evidence of work for a full interval. The distinction matters to whoever
    catches it, so the silence duration is carried on the exception.
    """

    def __init__(self, name, silent_for, interval):
        """Record which lease lapsed and how long the silence ran.

        Args:
            name: Lease name, usually the operation holding it.
            silent_for: Seconds since the last renewal.
            interval: Configured renewal interval.
        """
        super().__init__(
            "lease '%s' expired: no progress for %.1fs against a %.1fs renewal interval" % (name, silent_for, interval)
        )
        self.name = name
        self.silent_for = silent_for
        self.interval = interval


class Lease:
    """A liveness claim held by a long-running operation and renewed by progress.

    Attributes:
        name: Human-readable label for the operation holding the lease.
        interval: Seconds of silence tolerated before the lease lapses, or None
            for a lease that never lapses.
        durable: Whether a durable backend is available to outlive the holder.
    """

    def __init__(self, name, interval=None, clock=time.monotonic, warn_on_degraded=True):
        """Take out a lease, recording whether durable state backs it.

        Args:
            name: Human-readable label for the operation.
            interval: Seconds of silence tolerated before expiry. None means the
                lease never expires, which is the default so that an unconfigured
                pipeline task is unbounded.
            clock: Monotonic time source, injected so tests need no sleeping.
            warn_on_degraded: Emit the one-time degradation warning. Tests that
                construct many leases silence it.
        """
        global _DURABLE_STATE_WARNED
        self.name = name
        self.interval = None if interval is None else float(interval)
        self._clock = clock
        self.durable = durable_state_available()
        self.renewals = 0
        self._last_renewal = clock()
        if not self.durable and warn_on_degraded and not _DURABLE_STATE_WARNED:
            _DURABLE_STATE_WARNED = True
            logger.warning(
                "[Lease] No durable checkpoint backend is importable; leases are in-process only "
                "and will not survive the crash they exist to bound. Progress-based expiry still "
                "applies while the process is alive."
            )

    @property
    def degraded(self):
        """Report whether this lease lacks a durable backend."""
        return not self.durable

    def renew(self):
        """Record a progress event, resetting the silence measurement.

        Returns:
            int: The running count of renewals, which is the evidence of
            liveness this mechanism substitutes for a clock reading.
        """
        self._last_renewal = self._clock()
        self.renewals += 1
        return self.renewals

    def silent_for(self):
        """Return seconds elapsed since the last renewal."""
        return self._clock() - self._last_renewal

    def expired(self):
        """Report whether the lease lapsed through silence.

        Returns:
            bool: False whenever the interval is None, since an unbounded lease
            has no silence it will not tolerate.
        """
        if self.interval is None:
            return False
        return self.silent_for() > self.interval

    def check(self):
        """Raise when the lease has lapsed, otherwise return.

        Raises:
            LeaseExpired: When silence exceeded the renewal interval.
        """
        if self.expired():
            raise LeaseExpired(self.name, self.silent_for(), self.interval)

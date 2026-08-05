"""ADR-016 mechanism 4: one circuit breaker per external dependency.

Retry and circuit breaking are different mechanisms answering different
questions, and conflating them is the failure that turns one slow dependency
into a cascading outage. Retry assumes the next attempt will succeed and is
correct for a transient fault. A breaker assumes it will not, and is correct for
a dependency that is down. They compose -- retry lives inside the CLOSED state --
but they do not substitute for each other.

HOW THIS COMPOSES WITH WHAT IS ALREADY HERE
-------------------------------------------
``sdlc_pipeline.llm_retry`` retries a transient class at the SAME tier with
backoff. That is the CLOSED-state behaviour and this module does not replace it.
``model_fallback`` escalates the agent tier on positive rate-limit evidence only,
and deliberately refuses to escalate on a timeout, a 5xx or an empty response,
because those are equally the consequence of a crash or a bad prompt. A breaker
trip carries no such evidence either, so a trip is recorded here and never
handed to the fallback policy as though it were a throttle. Three mechanisms,
three distinct triggers, none shadowing another.

Against ``effect_ledger``: a breaker rejection must be evaluated BEFORE the
ledger's ``run_once``, not inside the callable it wraps. Consulting the breaker
first means an OPEN dependency never writes a PENDING entry, so it can never
produce the indistinguishable outcome the ledger refuses to guess at. Fail-fast
and two-phase idempotency reinforce each other in that order and only in that
order.

WHY THE REOPEN WAIT IS NOT A CONSTANT
-------------------------------------
A fixed reopen wait is itself a named anti-pattern: a dependency that is still
down gets probed on exactly the same cadence at minute one and at hour three,
which is both too much load early and too slow to notice late. The wait here
grows with the trip count -- ``min(max_wait, initial * 2 ** (trip_count - 1))`` --
so each consecutive failed probe buys the dependency more room, and the cap
keeps recovery detection from receding out of reach.

WHY THE MIN-CALLS FLOOR IS MANDATORY
------------------------------------
A failure rate over a two-call window is not a measurement. ADR-016 requires the
floor and gives the arithmetic: with a window of 10 and a true 5% failure rate,
the probability of a false open is about 0.11%. Without the floor the breaker
trips on ordinary noise and the fail-fast path becomes the common path.

SLOW-CALL RATE, WHICH IS WHY NO CALL NEEDS A DEADLINE
-----------------------------------------------------
The breaker trips on ``failure_rate >= F OR slow_call_rate >= S``. Measuring the
slow-call RATE over a window is what lets the system react to degradation
without cancelling any individual call, which is precisely the property NFR-2
needs. A call that runs long contributes one observation to a rate; it is not
aborted for having run long. That is the substitution at the heart of ADR-016:
the population is judged, the individual is not.
"""

import threading
import time
from collections import deque

from .jitter import deterministic_ceiling

STATE_CLOSED = "CLOSED"

STATE_OPEN = "OPEN"

STATE_HALF_OPEN = "HALF_OPEN"


class BreakerOpen(RuntimeError):
    """Raised instead of calling a dependency whose breaker is OPEN.

    This is a fail-fast, not a failure of the dependency: nothing was sent. The
    caller can substitute, degrade or defer, and must not record the rejection as
    evidence about the dependency's health, or the breaker would feed itself.
    """

    def __init__(self, name, reopen_in):
        """Record which dependency was skipped and when it will next be probed.

        Args:
            name: Dependency name.
            reopen_in: Seconds until the breaker admits a probe.
        """
        super().__init__("circuit breaker '%s' is OPEN; next probe in %.1fs" % (name, reopen_in))
        self.name = name
        self.reopen_in = reopen_in


class CircuitBreaker:
    """A {CLOSED, OPEN, HALF_OPEN} breaker guarding one external dependency.

    Attributes:
        name: Dependency this breaker guards.
        state: Current breaker state.
        trip_count: How many times the breaker has tripped, which drives the
            non-fixed reopen wait.
    """

    def __init__(
        self,
        name,
        failure_rate_threshold=0.5,
        slow_call_rate_threshold=0.5,
        slow_call_duration=30.0,
        min_calls=10,
        window_size=20,
        initial_wait=30.0,
        max_wait=300.0,
        clock=time.monotonic,
    ):
        """Configure a breaker for one dependency.

        Args:
            name: Dependency name, used in errors and in the registry.
            failure_rate_threshold: Failure fraction at or above which the
                breaker trips, once the min-calls floor is met.
            slow_call_rate_threshold: Slow-call fraction at or above which the
                breaker trips. This is the signal that replaces a per-call
                deadline.
            slow_call_duration: Seconds at or beyond which one call counts as
                slow. A slow call is recorded, never aborted.
            min_calls: Minimum observations in the window before either rate is
                allowed to trip anything.
            window_size: Number of recent calls the rates are measured over.
            initial_wait: First reopen wait in seconds.
            max_wait: Ceiling on the reopen wait.
            clock: Monotonic time source, injected for tests.

        Raises:
            ValueError: When min_calls exceeds window_size, which would make the
                floor unreachable and the breaker permanently inert.
        """
        if min_calls > window_size:
            raise ValueError("min_calls %d cannot exceed window_size %d" % (min_calls, window_size))
        self.name = name
        self.failure_rate_threshold = float(failure_rate_threshold)
        self.slow_call_rate_threshold = float(slow_call_rate_threshold)
        self.slow_call_duration = float(slow_call_duration)
        self.min_calls = int(min_calls)
        self.window_size = int(window_size)
        self.initial_wait = float(initial_wait)
        self.max_wait = float(max_wait)
        self._clock = clock
        self._lock = threading.RLock()
        self._window = deque(maxlen=self.window_size)
        self.state = STATE_CLOSED
        self.trip_count = 0
        self._opened_at = None

    def reopen_wait(self, trip_count=None):
        """Return the cooldown for a given trip count.

        The wait is a capped exponential in the trip count, so consecutive trips
        back off rather than probing on a fixed cadence.

        Args:
            trip_count: Trip count to compute for, defaulting to the current one.

        Returns:
            float: ``min(max_wait, initial_wait * 2 ** (trip_count - 1))``, and
            ``initial_wait`` when the breaker has never tripped.
        """
        count = self.trip_count if trip_count is None else trip_count
        if count < 1:
            return self.initial_wait
        return deterministic_ceiling(count - 1, self.initial_wait, self.max_wait)

    @property
    def failure_rate(self):
        """Return the failure fraction over the current window, or 0.0 when empty."""
        with self._lock:
            if not self._window:
                return 0.0
            failures = sum(1 for ok, _ in self._window if not ok)
            return failures / float(len(self._window))

    @property
    def slow_call_rate(self):
        """Return the slow-call fraction over the current window, or 0.0 when empty."""
        with self._lock:
            if not self._window:
                return 0.0
            slow = sum(1 for _, duration in self._window if duration >= self.slow_call_duration)
            return slow / float(len(self._window))

    @property
    def calls_in_window(self):
        """Return how many observations the window currently holds."""
        with self._lock:
            return len(self._window)

    def allows(self):
        """Report whether a call may proceed, advancing OPEN to HALF_OPEN when due.

        Returns:
            bool: True when the dependency may be called or probed.
        """
        with self._lock:
            if self.state == STATE_CLOSED:
                return True
            if self.state == STATE_HALF_OPEN:
                return True
            if self._opened_at is None:
                return True
            elapsed = self._clock() - self._opened_at
            if elapsed >= self.reopen_wait():
                self.state = STATE_HALF_OPEN
                return True
            return False

    def time_until_probe(self):
        """Return seconds remaining before an OPEN breaker admits a probe."""
        with self._lock:
            if self.state != STATE_OPEN or self._opened_at is None:
                return 0.0
            return max(0.0, self.reopen_wait() - (self._clock() - self._opened_at))

    def record_success(self, duration=0.0):
        """Record a completed call, which may still have been slow.

        A HALF_OPEN probe that succeeds closes the breaker and clears the window,
        so the recovered dependency is not immediately re-tripped by the failures
        that opened it.

        Args:
            duration: How long the call took, in seconds.
        """
        with self._lock:
            if self.state == STATE_HALF_OPEN:
                self.state = STATE_CLOSED
                self.trip_count = 0
                self._window.clear()
                self._opened_at = None
                return
            self._window.append((True, float(duration)))
            self._evaluate()

    def record_failure(self, duration=0.0):
        """Record a failed call.

        A HALF_OPEN probe that fails reopens the breaker and increments the trip
        count, which lengthens the next reopen wait.

        Args:
            duration: How long the call took before failing, in seconds.
        """
        with self._lock:
            if self.state == STATE_HALF_OPEN:
                self._trip()
                return
            self._window.append((False, float(duration)))
            self._evaluate()

    def _evaluate(self):
        """Trip the breaker when either rate crosses its threshold above the floor."""
        if self.state != STATE_CLOSED:
            return
        if len(self._window) < self.min_calls:
            return
        if self.failure_rate >= self.failure_rate_threshold or self.slow_call_rate >= self.slow_call_rate_threshold:
            self._trip()

    def _trip(self):
        """Move to OPEN and start the cooldown for the new trip count."""
        self.state = STATE_OPEN
        self.trip_count += 1
        self._opened_at = self._clock()
        self._window.clear()

    def call(self, fn):
        """Run a callable through the breaker, recording its outcome and duration.

        Args:
            fn: Zero-argument callable performing the dependency call.

        Returns:
            Whatever fn returns.

        Raises:
            BreakerOpen: When the breaker is OPEN and not yet due for a probe.
                Nothing is sent to the dependency in that case.
        """
        if not self.allows():
            raise BreakerOpen(self.name, self.time_until_probe())
        started = self._clock()
        try:
            result = fn()
        except Exception:
            self.record_failure(self._clock() - started)
            raise
        self.record_success(self._clock() - started)
        return result

    def reset(self):
        """Return the breaker to a clean CLOSED state."""
        with self._lock:
            self._window.clear()
            self.state = STATE_CLOSED
            self.trip_count = 0
            self._opened_at = None


_REGISTRY = {}

_REGISTRY_LOCK = threading.RLock()

EXTERNAL_DEPENDENCIES = ("claude_cli", "github", "jira", "anthropic_api")


def get_breaker(name, **kwargs):
    """Return the process-wide breaker for one dependency, creating it on demand.

    One breaker per dependency is the point: a GitHub outage must not fail-fast
    calls to the Anthropic API, and a shared breaker would do exactly that.

    Args:
        name: Dependency name.
        **kwargs: Constructor arguments, applied only when the breaker is first
            created.

    Returns:
        CircuitBreaker: The registered breaker for that dependency.
    """
    with _REGISTRY_LOCK:
        if name not in _REGISTRY:
            _REGISTRY[name] = CircuitBreaker(name, **kwargs)
        return _REGISTRY[name]


def reset_registry():
    """Drop every registered breaker, so tests do not leak state into each other."""
    with _REGISTRY_LOCK:
        _REGISTRY.clear()

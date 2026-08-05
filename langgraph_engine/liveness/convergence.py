"""ADR-016 mechanism 3: stop on a no-progress signal, not on a stopwatch.

The TODO executor hashes its own state once per iteration and stops after N
consecutive identical hashes. This is the livelock detector of the divergence
taxonomy: a loop whose state keeps being rewritten to the same value is busy
rather than productive, and no amount of additional wall-clock time will change
that.

It is deliberately a *convergence* signal and not a quality signal. It reports
that nothing changed; it does not claim that what is there is good. A caller
that wants a quality bar must apply its own, and a caller that wants both must
compose them -- the two answer different questions and a single threshold cannot
serve both.

The hash is computed over a canonical JSON rendering so that dictionary
insertion order, which is not part of the state's meaning, cannot masquerade as
progress. Values JSON cannot render fall back to ``repr``, which is stable
within a process for the shapes this pipeline carries.
"""

import hashlib
import json


def state_hash(state):
    """Return a stable digest of an arbitrary state value.

    Args:
        state: Any value describing the loop's current state.

    Returns:
        str: Hex SHA-256 digest of a canonical rendering of the state.
    """
    try:
        rendered = json.dumps(state, sort_keys=True, default=repr, ensure_ascii=True)
    except (TypeError, ValueError):
        rendered = repr(state)
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


class ConvergenceMonitor:
    """Detects that a loop has stopped changing its own state.

    Attributes:
        patience: Number of consecutive identical observations that constitute
            convergence.
        consecutive_identical: How many identical observations have been seen in
            a row, counting the run rather than the total.
        observations: Total number of observations recorded.
    """

    def __init__(self, patience=3, name="convergence"):
        """Configure how much repetition counts as no progress.

        Args:
            patience: Consecutive identical observations required. Must be at
                least 1; a patience of 1 declares convergence on the first
                repeat.
            name: Human-readable label used in reporting.

        Raises:
            ValueError: When patience is below 1, which would declare
                convergence before any comparison had been made.
        """
        if patience < 1:
            raise ValueError("convergence patience must be at least 1, got %r" % (patience,))
        self.patience = int(patience)
        self.name = name
        self.consecutive_identical = 0
        self.observations = 0
        self._last_hash = None

    def observe(self, state):
        """Record one iteration's state and report whether the loop has converged.

        Args:
            state: The loop's state after this iteration.

        Returns:
            bool: True once ``patience`` consecutive identical states have been
            seen, meaning the loop is making no progress.
        """
        digest = state_hash(state)
        if self._last_hash is not None and digest == self._last_hash:
            self.consecutive_identical += 1
        else:
            self.consecutive_identical = 0
        self._last_hash = digest
        self.observations += 1
        return self.converged

    @property
    def converged(self):
        """Report whether the no-progress threshold has been reached."""
        return self.consecutive_identical >= self.patience

    def reset(self):
        """Forget the observation history, so a restarted loop starts clean."""
        self.consecutive_identical = 0
        self.observations = 0
        self._last_hash = None

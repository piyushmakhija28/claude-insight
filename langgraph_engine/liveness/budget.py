"""ADR-016 mechanism 1: bound work by attempts, not by elapsed time.

A wall-clock deadline answers "has this taken too long", which is not the
question anyone wants answered. The question is "is this making progress", and
elapsed time is only a proxy for it -- a proxy that aborts healthy slow work and
permits unhealthy fast loops with equal confidence.

An attempt budget answers a question a clock cannot: how many times has this
been tried. A deterministically failing call exhausts it in bounded work
regardless of how fast or slow the underlying dependency is, and a single
long-running call that is genuinely progressing never touches it at all.

Exhaustion is a typed result, not an exception thrown at the caller's feet from
inside an unrelated frame: ADR-016 requires a ``BudgetExhausted`` the caller can
act on, so the caller can degrade rather than crash.
"""

import os


def env_int(name, default):
    """Read a non-negative integer from the environment with a fallback.

    Args:
        name: Environment variable name.
        default: Value used when the variable is unset or not an integer.

    Returns:
        int: The configured value, or the default.
    """
    try:
        return int(os.environ.get(name, str(default)))
    except (TypeError, ValueError):
        return default


def env_optional_seconds(name):
    """Read an optional silence interval from the environment.

    Returns None when the variable is unset, empty, non-numeric, or set to a
    value at or below zero. None means unbounded, which is the default NFR-2
    requires: an operator opts INTO a bound rather than out of one.

    Args:
        name: Environment variable name.

    Returns:
        float or None: The configured interval in seconds, or None for unbounded.
    """
    raw = os.environ.get(name, "").strip()
    if not raw:
        return None
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return None
    return value if value > 0 else None


class BudgetExhausted(RuntimeError):
    """Raised when an attempt budget is consumed past its configured limit.

    Carries the budget name and limit so a caller that catches it can report
    which bound was reached without re-deriving it from a message string.
    """

    def __init__(self, name, limit, attempts):
        """Record which budget was exhausted and at what count.

        Args:
            name: Budget name, usually the operation being bounded.
            limit: Configured attempt limit.
            attempts: Number of attempts consumed.
        """
        super().__init__("attempt budget '%s' exhausted after %d of %d attempts" % (name, attempts, limit))
        self.name = name
        self.limit = limit
        self.attempts = attempts


class AttemptBudget:
    """A counted bound on how many times an operation may be attempted.

    The budget is deliberately not a time budget. It is consumed by attempts and
    by iterations, so a caller that loops forever without progress exhausts it in
    a bounded number of steps, while a caller making one long successful call
    never approaches it.
    """

    def __init__(self, limit, name="attempt"):
        """Create a budget with a hard attempt limit.

        Args:
            limit: Maximum number of attempts. Must be at least 1.
            name: Human-readable label used in errors and logs.

        Raises:
            ValueError: When limit is below 1, which would forbid even the first
                attempt and make the budget unsatisfiable rather than strict.
        """
        if limit < 1:
            raise ValueError("attempt budget limit must be at least 1, got %r" % (limit,))
        self.limit = int(limit)
        self.name = name
        self.attempts = 0

    @classmethod
    def from_env(cls, var_name, default, name=""):
        """Build a budget whose limit is configurable through the environment.

        Args:
            var_name: Environment variable holding the limit.
            default: Limit applied when the variable is unset.
            name: Human-readable label, defaulting to the variable name.

        Returns:
            AttemptBudget: A budget with the resolved limit.
        """
        return cls(env_int(var_name, default), name or var_name)

    @property
    def remaining(self):
        """Return how many attempts are still permitted."""
        return max(0, self.limit - self.attempts)

    @property
    def exhausted(self):
        """Report whether the budget has no attempts left."""
        return self.remaining == 0

    def consume(self):
        """Take one attempt from the budget.

        Returns:
            int: The 1-based index of the attempt just taken.

        Raises:
            BudgetExhausted: When no attempts remain.
        """
        if self.exhausted:
            raise BudgetExhausted(self.name, self.limit, self.attempts)
        self.attempts += 1
        return self.attempts

    def reset(self):
        """Return the budget to its full allowance."""
        self.attempts = 0

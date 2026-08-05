"""Non-temporal liveness control for the long-running pipeline path (ADR-016 / NFR-2).

A fixed wall-clock timeout on a pipeline step is a temporal proxy for a question
it cannot answer -- "is this making progress?" -- and it answers that question
wrongly in both directions, aborting healthy slow work and permitting unhealthy
fast loops. This package replaces the proxy with the signals themselves:

1. :class:`~.budget.AttemptBudget`      -- bound work by attempts, not elapsed time.
2. :class:`~.lease.Lease`               -- renewal on progress, not a deadline.
3. :class:`~.convergence.ConvergenceMonitor` -- stop on no-progress, not on a clock.
4. :class:`~.breaker.CircuitBreaker`    -- per-dependency fail-fast with a
   NON-FIXED reopen wait, tripped by failure rate OR slow-call rate above a
   min-calls floor.
5. :func:`~.jitter.full_jitter_delay`   -- decorrelated retry spacing.

Mechanism 5 is counted differently by the two documents that specify this work,
and the difference is recorded rather than resolved by preference. ADR-016
enumerates slow-call rate as its fifth mechanism and treats full jitter as part
of its fourth; NFR-2's acceptance criterion promotes full jitter to a
first-class fifth and does not name slow-call rate at all. Both capabilities are
implemented here, so both readings are satisfied and neither document has to be
declared wrong to ship.

:func:`~.supervised.run_supervised` is the call-site replacement for
``subprocess.run(..., timeout=N)``: it terminates a child for silence, never for
duration, and does not terminate at all unless an interval is configured.
"""

from .breaker import (
    EXTERNAL_DEPENDENCIES,
    STATE_CLOSED,
    STATE_HALF_OPEN,
    STATE_OPEN,
    BreakerOpen,
    CircuitBreaker,
    get_breaker,
    reset_registry,
)
from .budget import AttemptBudget, BudgetExhausted, env_int, env_optional_seconds
from .convergence import ConvergenceMonitor, state_hash
from .jitter import deterministic_ceiling, equal_jitter_delay, full_jitter_delay
from .lease import Lease, LeaseExpired, durable_state_available
from .retry import call_with_liveness
from .supervised import NoProgress, SupervisedResult, run_supervised

__all__ = [
    "AttemptBudget",
    "BudgetExhausted",
    "BreakerOpen",
    "CircuitBreaker",
    "ConvergenceMonitor",
    "EXTERNAL_DEPENDENCIES",
    "Lease",
    "LeaseExpired",
    "NoProgress",
    "STATE_CLOSED",
    "STATE_HALF_OPEN",
    "STATE_OPEN",
    "SupervisedResult",
    "call_with_liveness",
    "deterministic_ceiling",
    "durable_state_available",
    "env_int",
    "env_optional_seconds",
    "equal_jitter_delay",
    "full_jitter_delay",
    "get_breaker",
    "reset_registry",
    "run_supervised",
    "state_hash",
]

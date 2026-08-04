"""The driver that composes the attempt budget, the breaker and full jitter.

Kept separate from the three mechanisms it uses so that each remains usable
alone. A call site that only needs a breaker should not have to accept a retry
policy, and a loop that only needs an attempt bound should not have to name a
dependency.

WHAT THIS DOES NOT DO
---------------------
It does not classify errors. ``sdlc_pipeline.llm_retry.is_llm_retryable`` already
owns transient-versus-terminal classification for LLM calls and is passed in
rather than reimplemented, because two classifiers drifting apart would be worse
than one imperfect one.

It does not escalate model tiers. ``model_fallback`` owns that, escalates only on
positive rate-limit evidence, and would be wrong to invoke from here: exhausting
a retry budget is not evidence of a rate limit, and treating it as such would
spend the expensive tier on exactly the bugs the fallback rule says to fix at the
root.

It does not write to the effect ledger. The breaker is consulted first precisely
so that a fail-fast rejection never reaches ``EffectLedger.run_once`` and never
leaves the PENDING entry that the ledger, correctly, refuses to guess about.
"""

import time

from .breaker import BreakerOpen, get_breaker
from .budget import AttemptBudget, BudgetExhausted
from .jitter import full_jitter_delay


def call_with_liveness(
    fn,
    budget=None,
    breaker_name=None,
    is_retryable=None,
    base_delay=1.0,
    cap_delay=30.0,
    sleep=time.sleep,
    rng=None,
):
    """Call a dependency under an attempt budget, a circuit breaker and full jitter.

    Args:
        fn: Zero-argument callable performing the dependency call.
        budget: Attempt budget bounding the retries. A default budget of three
            attempts is created when None.
        breaker_name: External dependency whose breaker guards the call, or None
            to run without a breaker.
        is_retryable: Predicate deciding whether a raised exception is worth
            another attempt. Everything is treated as terminal when None, which
            is the safe default: retrying an unclassified error can only waste
            the budget.
        base_delay: Initial backoff delay in seconds.
        cap_delay: Ceiling on the backoff delay.
        sleep: Sleep function, injected so tests need not wait.
        rng: Random source for the jitter, injected for determinism in tests.

    Returns:
        Whatever fn returns.

    Raises:
        BreakerOpen: When the dependency's breaker is OPEN. Nothing was sent.
        BudgetExhausted: When every attempt was spent on retryable failures.
        Exception: The original exception when it is not retryable.
    """
    attempts = budget if budget is not None else AttemptBudget(3, breaker_name or "call")
    breaker = get_breaker(breaker_name) if breaker_name else None
    last_error = None

    while True:
        try:
            index = attempts.consume()
        except BudgetExhausted as exhausted:
            if last_error is not None:
                raise exhausted from last_error
            raise

        try:
            return breaker.call(fn) if breaker is not None else fn()
        except BreakerOpen:
            raise
        except Exception as exc:
            last_error = exc
            if is_retryable is None or not is_retryable(exc):
                raise
            if attempts.exhausted:
                raise BudgetExhausted(attempts.name, attempts.limit, attempts.attempts) from exc
            sleep(full_jitter_delay(index - 1, base_delay, cap_delay, rng=rng))

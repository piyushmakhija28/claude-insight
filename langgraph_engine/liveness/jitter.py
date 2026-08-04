"""ADR-016 mechanism 5 (as the acceptance criterion counts them): full jitter.

Exponential backoff spreads one client's retries out in time. It does not
decorrelate several clients from each other: if N callers fail at the same
instant and share a deterministic schedule, they retry at the same instants
forever, and the retry wave re-creates the load spike that caused the failure.

Full jitter samples uniformly from zero up to the capped exponential ceiling,
so N callers land on N different instants. ADR-016 spells the formula out --
``delay = random_uniform(0, min(cap, base * 2 ** n))`` -- and the reason: without
it, N clients retry in lockstep for an O(N) spike.

Equal jitter is offered alongside because it is the right choice when a
guaranteed minimum spacing matters more than maximum decorrelation. It is not
the default: ADR-016 names full jitter specifically.
"""

import random


def full_jitter_delay(attempt, base=1.0, cap=30.0, rng=None):
    """Return a full-jitter backoff delay for a retry round.

    Args:
        attempt: Zero-based retry index. Negative values are clamped to zero.
        base: Initial delay in seconds before the exponential growth applies.
        cap: Ceiling on the deterministic component, so the schedule cannot grow
            without bound.
        rng: Source of randomness, defaulting to the module-level generator.
            Injected so a test can make the sampling deterministic.

    Returns:
        float: A delay drawn uniformly from ``[0, min(cap, base * 2 ** attempt)]``.
    """
    source = rng if rng is not None else random
    ceiling = deterministic_ceiling(attempt, base, cap)
    return source.uniform(0.0, ceiling)


def equal_jitter_delay(attempt, base=1.0, cap=30.0, rng=None):
    """Return an equal-jitter backoff delay, guaranteeing a minimum spacing.

    Half the delay is deterministic and half is sampled, so two retries are never
    closer together than half the ceiling. Prefer :func:`full_jitter_delay`
    unless a minimum spacing is genuinely required.

    Args:
        attempt: Zero-based retry index.
        base: Initial delay in seconds.
        cap: Ceiling on the deterministic component.
        rng: Source of randomness, defaulting to the module-level generator.

    Returns:
        float: A delay in ``[ceiling / 2, ceiling]``.
    """
    source = rng if rng is not None else random
    half = deterministic_ceiling(attempt, base, cap) / 2.0
    return half + source.uniform(0.0, half)


def deterministic_ceiling(attempt, base=1.0, cap=30.0):
    """Return the capped exponential ceiling a jittered delay samples below.

    Exposed separately because the ceiling is the part a test can assert on
    without controlling the random source, and because the circuit breaker reuses
    the same capped-exponential shape for its reopen wait.

    Args:
        attempt: Zero-based retry index. Negative values are clamped to zero.
        base: Initial delay in seconds.
        cap: Ceiling on the result.

    Returns:
        float: ``min(cap, base * 2 ** attempt)``.
    """
    index = max(0, int(attempt))
    return float(min(cap, base * (2**index)))

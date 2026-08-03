"""Replay-idempotency ledger for external, non-idempotent side effects.

This module is deliberately NOT a checkpoint writer. Checkpointing persists
graph state so execution can resume; this ledger persists the fact that an
*external* effect was already committed so that resuming does not commit it a
second time. The split mirrors the event-sourcing discipline that deterministic
replayable logic and isolated side effects must be tracked separately: a state
snapshot can be replayed safely, an external POST cannot.

The failure mode this exists to prevent has already occurred in this repository:
a non-idempotent retry produced two GitHub issues from one logical creation call.
Re-running a step after a crash is exactly the same shape of duplicate.

Idempotency key
---------------
The key is the checkpoint identity of the step that owns the effect,
``{session_id}:step-{NN}``, optionally suffixed with an effect name when one step
commits more than one distinct external effect. Using the checkpoint identity
means the ledger and the checkpoint chain agree on what "this step" means without
a second notion of step identity that could drift.

Two-phase records
-----------------
An entry is written as PENDING immediately before the effect is attempted and
promoted to COMMITTED once it returns. A PENDING entry found on a later run means
the process died with the outcome unknown: the effect may or may not have reached
the remote system. That is an indistinguishable state, so ``run_once`` refuses
rather than guessing. Re-executing would risk the duplicate; declaring failure
would risk orphaning a committed effect. Refusing surfaces the one case a human
or an explicit policy must settle.

Usage:
    from .effect_ledger import EffectLedger

    ledger = EffectLedger(session_id)
    key = ledger.effect_key(step=2, effect_name="github_issue")
    effect, replayed = ledger.run_once(key, lambda: create_issue(...))
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Tuple

from langgraph_engine.checkpoint_manager import CheckpointManager

try:
    from loguru import logger
except ImportError:
    import logging

    logger = logging.getLogger(__name__)


STATUS_PENDING = "PENDING"

STATUS_COMMITTED = "COMMITTED"

_UNSAFE_KEY_CHARS = re.compile(r"[^A-Za-z0-9._-]+")


class EffectReplayError(RuntimeError):
    """Raised when a previous attempt at an external effect left an unknown outcome.

    The ledger holds a PENDING entry, meaning the process died between announcing
    the effect and recording its result. Neither re-executing nor skipping is safe
    without information the ledger does not have, so the decision is escalated
    rather than guessed.
    """


class EffectLedger:
    """Durable record of external effects already committed for a session."""

    def __init__(self, session_id: str, base_dir: Optional[str] = None):
        """Initialise the ledger alongside the session's checkpoint directory.

        Args:
            session_id: Unique identifier for this execution session.
            base_dir: Override the default checkpoint base directory.
        """
        self.session_id = session_id
        if base_dir:
            checkpoint_dir = Path(base_dir).expanduser() / session_id / "checkpoints"
        else:
            checkpoint_dir = CheckpointManager.default_checkpoint_dir(session_id)
        self.ledger_dir = checkpoint_dir / "effects"
        self.ledger_dir.mkdir(parents=True, exist_ok=True)

    def effect_key(self, step: int, effect_name: str = "") -> str:
        """Build the idempotency key for one external effect of one step.

        Args:
            step: Step number that owns the effect.
            effect_name: Optional discriminator when a step commits more than
                one distinct external effect.

        Returns:
            Key of the form "{session_id}:step-{NN}" plus an optional
            ":{effect_name}" suffix.
        """
        key = "%s:step-%02d" % (self.session_id, step)
        if effect_name:
            key = "%s:%s" % (key, effect_name)
        return key

    def _path_for(self, key: str) -> Path:
        """Map an idempotency key to its on-disk ledger entry."""
        return self.ledger_dir / ("%s.json" % _UNSAFE_KEY_CHARS.sub("_", key))

    def lookup(self, key: str) -> Optional[Dict[str, Any]]:
        """Return the ledger entry for a key, or None when no attempt was recorded.

        Args:
            key: Idempotency key produced by effect_key().

        Returns:
            The stored entry dict, or None.
        """
        path = self._path_for(key)
        try:
            if not path.is_file():
                return None
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            logger.error("[EffectLedger] Unreadable entry for %s: %s" % (key, exc))
            return None

    def _write(self, key: str, entry: Dict[str, Any]) -> bool:
        """Persist a ledger entry, returning False when the write did not land."""
        try:
            self._path_for(key).write_text(json.dumps(entry, indent=2), encoding="utf-8")
            return True
        except (OSError, TypeError, ValueError) as exc:
            logger.error("[EffectLedger] Failed to write entry for %s: %s" % (key, exc))
            return False

    def mark_pending(self, key: str) -> bool:
        """Announce, before the effect runs, that it is about to be attempted.

        Args:
            key: Idempotency key produced by effect_key().

        Returns:
            True when the announcement was persisted.
        """
        return self._write(
            key,
            {
                "key": key,
                "session_id": self.session_id,
                "status": STATUS_PENDING,
                "timestamp": datetime.now().isoformat(),
            },
        )

    def record(self, key: str, effect: Any) -> bool:
        """Record an external effect as committed under its idempotency key.

        Args:
            key: Idempotency key produced by effect_key().
            effect: Serialisable description of what was committed, replayed
                verbatim to any later attempt under the same key.

        Returns:
            True when the record was persisted.
        """
        return self._write(
            key,
            {
                "key": key,
                "session_id": self.session_id,
                "status": STATUS_COMMITTED,
                "effect": effect,
                "timestamp": datetime.now().isoformat(),
            },
        )

    def run_once(
        self,
        key: str,
        fn: Callable[[], Any],
        commit_predicate: Optional[Callable[[Any], bool]] = None,
    ) -> Tuple[Any, bool]:
        """Execute a side-effecting callable at most once per idempotency key.

        A committed entry short-circuits the call and replays the recorded effect,
        so re-executing a step after a crash produces no second external effect.

        An attempt that did not commit anything must not be recorded as committed,
        or every later attempt would replay a failure that never happened remotely.
        ``commit_predicate`` decides which returned values represent a real external
        effect; when it rejects a value the PENDING entry is cleared so the effect
        may be attempted cleanly again.

        Args:
            key: Idempotency key produced by effect_key().
            fn: Zero-argument callable performing the external effect.
            commit_predicate: Returns True when the value represents a committed
                external effect. Defaults to treating any non-None value as
                committed.

        Returns:
            Tuple of (effect, replayed) where replayed is True when the effect
            came from the ledger rather than from invoking fn.

        Raises:
            EffectReplayError: When a previous attempt left a PENDING entry, so
                the outcome of that attempt is unknown.
        """
        existing = self.lookup(key)
        if existing is not None:
            status = existing.get("status")
            if status == STATUS_COMMITTED:
                logger.info("[EffectLedger] Replaying committed effect for %s (not re-executing)" % key)
                return existing.get("effect"), True
            if status == STATUS_PENDING:
                raise EffectReplayError(
                    "Effect %s was attempted but its outcome was never recorded. "
                    "Re-executing risks a duplicate external effect; skipping risks "
                    "orphaning a committed one. Resolve the entry before retrying." % key
                )

        self.mark_pending(key)
        try:
            effect = fn()
        except Exception:
            self.clear(key)
            raise

        committed = effect is not None if commit_predicate is None else bool(commit_predicate(effect))
        if committed:
            self.record(key, effect)
        else:
            self.clear(key)
        return effect, False

    def clear(self, key: str) -> bool:
        """Remove a ledger entry so its effect may be attempted again.

        Args:
            key: Idempotency key produced by effect_key().

        Returns:
            True when the entry is absent after the call.
        """
        path = self._path_for(key)
        try:
            if path.is_file():
                path.unlink()
            return True
        except OSError as exc:
            logger.error("[EffectLedger] Failed to clear entry for %s: %s" % (key, exc))
            return False

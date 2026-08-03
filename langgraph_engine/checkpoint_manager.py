"""
Checkpoint Manager - State persistence between steps.

Saves full FlowState after each step so execution can resume from any
completed checkpoint instead of restarting from the beginning.

Directory layout:
    ~/.claude/logs/sessions/{session_id}/checkpoints/
        step-01.json
        step-02.json
        ...
        latest.json  (copy of most recent)

Checkpoint payload schema:
    {
        "checkpoint_id": "{session_id}:step-{N}",
        "step": int,
        "timestamp": ISO-8601,
        "session_id": str,
        "success_status": bool,
        "error_message": str | null,
        "state": {...}
    }

Usage:
    from .checkpoint_manager import CheckpointManager

    cp = CheckpointManager(session_id)
    cp.save_checkpoint(step=3, state=state)
    cp.save_checkpoint(step=4, state=state, success_status=False,
                       error_message="LLM timeout")

    last_step, recovered_state = cp.get_last_checkpoint()
    metadata = cp.load_checkpoint_metadata(step=3)
"""

import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from langgraph_engine.core.claude_paths import get_claude_logs_dir

try:
    from loguru import logger
except ImportError:
    import logging

    logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEGRADED_MARKER_FILENAME = "checkpoint-degraded.json"

PROGRESS_PROJECTION_FILENAME = "workflow-memory.json"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _now_iso() -> str:
    return datetime.now().isoformat()


class CheckpointDegradedError(RuntimeError):
    """Raised when a resume is attempted against a session whose checkpoint chain has a hole.

    A degraded session is one in which at least one ``save_checkpoint`` call did not
    durably land. The resume path cannot distinguish "the step never ran" from "the
    step ran, committed an external side effect, and the record was lost", so it must
    refuse rather than guess. Guessing re-executes a non-idempotent node, which is the
    duplicate-external-effect failure mode this contract exists to prevent.

    Callers that genuinely accept the risk may pass ``allow_degraded=True`` to the
    resume entry points, which converts the refusal into an explicit, auditable choice.
    """


def _serialize_state(state: Dict[str, Any]) -> Dict[str, Any]:
    """Return a JSON-safe copy of state (drop non-serialisable values)."""
    safe: Dict[str, Any] = {}
    for key, value in state.items():
        try:
            json.dumps(value)  # probe
            safe[key] = value
        except (TypeError, ValueError):
            # Fall back to string representation
            try:
                safe[key] = str(value)
            except Exception:
                safe[key] = "<unserializable>"
    return safe


# ---------------------------------------------------------------------------
# CheckpointManager
# ---------------------------------------------------------------------------


class CheckpointManager:
    """Save and restore FlowState checkpoints per session."""

    @staticmethod
    def default_checkpoint_dir(session_id: str) -> Path:
        """Build the default checkpoint directory for a session.

        Replaces a module-level template string that spelled the Claude logs
        root inline. The root now comes from path_resolver, so a relocated
        layout moves this directory with it.

        Args:
            session_id: Unique identifier for this execution session.

        Returns:
            Path: Absolute checkpoint directory for the session.
        """
        return get_claude_logs_dir() / "sessions" / session_id / "checkpoints"

    def __init__(self, session_id: str, base_dir: Optional[str] = None):
        """
        Initialise checkpoint manager.

        Args:
            session_id: Unique identifier for this execution session.
            base_dir:   Override default checkpoint base directory (optional).
        """
        self.session_id = session_id

        if base_dir:
            self.checkpoint_dir = Path(base_dir).expanduser() / session_id / "checkpoints"
        else:
            self.checkpoint_dir = self.default_checkpoint_dir(session_id)

        self._degraded = False
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"CheckpointManager ready: {self.checkpoint_dir}")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def _make_checkpoint_id(self, step: int) -> str:
        """Build a unique checkpoint identifier used for resume commands."""
        return f"{self.session_id}:step-{step:02d}"

    def _atomic_write(self, path: Path, content: str) -> None:
        """
        Write content to path atomically using a temp-file + rename pattern.

        On Windows, os.replace() is atomic for files on the same volume.
        Falls back to direct write if the temp file cannot be created.

        Raises:
            IOError: If both atomic write and fallback write fail.
        """
        dir_path = path.parent
        try:
            fd, tmp_path = tempfile.mkstemp(dir=str(dir_path), suffix=".tmp")
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as fh:
                    fh.write(content)
                os.replace(tmp_path, str(path))
            except Exception:
                # Clean up temp file if replace failed
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass
                raise
        except (OSError, PermissionError):
            # Fallback: direct write (non-atomic but better than nothing)
            path.write_text(content, encoding="utf-8")

    # ------------------------------------------------------------------
    # Durability degradation tracking
    # ------------------------------------------------------------------

    @property
    def degraded_marker_path(self) -> Path:
        """Path of the durable marker recording that this session lost a checkpoint."""
        return self.checkpoint_dir / DEGRADED_MARKER_FILENAME

    def mark_degraded(self, step: int, reason: str) -> None:
        """Record, durably, that a checkpoint write for this session did not land.

        The marker is written to the session's own checkpoint directory so that a
        different process performing the resume observes it, which is required
        because the process that lost the write is by definition the one that may
        not survive to report it in memory.

        Args:
            step: Step number whose checkpoint write failed.
            reason: Short description of the failure, stored for audit.
        """
        self._degraded = True
        try:
            payload = {
                "session_id": self.session_id,
                "degraded_at_step": step,
                "reason": str(reason)[:500],
                "timestamp": _now_iso(),
            }
            self.degraded_marker_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        except OSError as exc:
            logger.error(f"[Checkpoint] Could not persist degraded marker for step {step}: {exc}")

    def is_degraded(self) -> bool:
        """Return True when this session's checkpoint chain is known to have a hole."""
        if self._degraded:
            return True
        try:
            return self.degraded_marker_path.is_file()
        except OSError:
            return False

    def degradation_details(self) -> Optional[Dict[str, Any]]:
        """Return the recorded degradation metadata, or None when the session is intact."""
        try:
            if not self.degraded_marker_path.is_file():
                return None
            return json.loads(self.degraded_marker_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {"session_id": self.session_id, "reason": "degraded marker present but unreadable"}

    def _guard_resume(self, allow_degraded: bool) -> None:
        """Refuse a resume against a degraded session unless the caller opts in.

        Args:
            allow_degraded: When True, downgrade the refusal to a warning.

        Raises:
            CheckpointDegradedError: When the session is degraded and the caller
                has not explicitly accepted the risk.
        """
        if not self.is_degraded():
            return
        details = self.degradation_details() or {}
        if allow_degraded:
            logger.warning(
                "[Checkpoint] Resuming DEGRADED session %s despite a lost checkpoint at step %s"
                % (self.session_id, details.get("degraded_at_step", "?"))
            )
            return
        raise CheckpointDegradedError(
            "Session %s is checkpoint-degraded (lost write at step %s: %s). "
            "Refusing to resume: a missing record cannot be distinguished from a step "
            "that already committed an external side effect."
            % (
                self.session_id,
                details.get("degraded_at_step", "?"),
                details.get("reason", "unknown"),
            )
        )

    def _verify_written(self, path: Path, checkpoint_id: str) -> bool:
        """Read a just-written checkpoint back and confirm it parses and matches.

        The fallback branch of ``_atomic_write`` is a plain, non-atomic write that
        can leave a truncated file behind. Without a read-back the caller would be
        told the write succeeded, so the durability claim is only as strong as this
        verification.

        Args:
            path: File that was just written.
            checkpoint_id: Identifier the file is expected to carry.

        Returns:
            True when the file parses and carries the expected checkpoint_id.
        """
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            logger.error(f"[Checkpoint] Read-back verification failed for {path.name}: {exc}")
            return False
        return data.get("checkpoint_id") == checkpoint_id

    def project_progress(self, step: int) -> Optional[Dict[str, Any]]:
        """Derive the progress surface for a step from its persisted checkpoint record.

        This is the single projection function for per-step progress. It reads the
        checkpoint record back from disk and derives every field from it, so the
        progress surface cannot report a step the checkpoint record does not carry.
        Returning None means no checkpoint record exists, in which case no progress
        surface may be written at all.

        Args:
            step: Step number to project.

        Returns:
            Projected progress dict, or None when no checkpoint record exists.
        """
        meta = self.load_checkpoint_metadata(step)
        if meta is None:
            return None
        return {
            "last_step": meta.get("step", step),
            "last_step_status": "SUCCESS" if meta.get("success_status", True) else "FAILED",
            "timestamp": meta.get("timestamp"),
            "session_id": meta.get("session_id", self.session_id),
            "checkpoint_id": meta.get("checkpoint_id"),
            "projected_from": "checkpoint",
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def save_checkpoint(
        self,
        step: int,
        state: Dict[str, Any],
        success_status: bool = True,
        error_message: Optional[str] = None,
    ) -> bool:
        """
        Persist state after a step completes.

        The checkpoint file includes:
        - checkpoint_id: unique "{session_id}:step-{N}" key for resume
        - success_status: whether the step completed without errors
        - error_message: optional error description if success_status=False
        - full serialized FlowState

        Args:
            step:           Step number (0-14).
            state:          Current FlowState dict.
            success_status: True if step succeeded, False if it errored.
            error_message:  Optional error description for failed steps.

        Returns:
            True on success, False on failure.
        """
        try:
            safe_state = _serialize_state(state)
            checkpoint_id = self._make_checkpoint_id(step)
            checkpoint = {
                "checkpoint_id": checkpoint_id,
                "step": step,
                "timestamp": _now_iso(),
                "session_id": self.session_id,
                "success_status": success_status,
                "error_message": error_message,
                "state": safe_state,
            }

            payload = json.dumps(checkpoint, indent=2)

            path = self.checkpoint_dir / f"step-{step:02d}.json"
            self._atomic_write(path, payload)

            if not self._verify_written(path, checkpoint_id):
                self.mark_degraded(step, "checkpoint read-back verification failed")
                return False

            # Also write latest.json for quick access
            latest_path = self.checkpoint_dir / "latest.json"
            self._atomic_write(latest_path, payload)

            status_tag = "OK" if success_status else "FAILED"
            logger.info(f"[Checkpoint] Saved step {step} [{status_tag}] -> {path}")
            return True

        except PermissionError as e:
            logger.error(f"[Checkpoint] Permission denied saving step {step}: {e}")
            self.mark_degraded(step, "PermissionError: %s" % e)
            return False
        except OSError as e:
            logger.error(f"[Checkpoint] OS error saving step {step} (disk full?): {e}")
            self.mark_degraded(step, "OSError: %s" % e)
            return False
        except Exception as e:
            logger.error(f"[Checkpoint] Unexpected error saving step {step}: {e}")
            self.mark_degraded(step, "%s: %s" % (type(e).__name__, e))
            return False

    def load_checkpoint(self, step: int) -> Optional[Dict[str, Any]]:
        """
        Load state from a specific step checkpoint.

        Args:
            step: Step number to load.

        Returns:
            State dict, or None if checkpoint not found / corrupt.
        """
        path = self.checkpoint_dir / f"step-{step:02d}.json"
        if not path.exists():
            logger.debug(f"[Checkpoint] No checkpoint found for step {step}")
            return None

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            logger.info(
                f"[Checkpoint] Loaded step {step} "
                f"(ts={data.get('timestamp')}, "
                f"success={data.get('success_status', 'unknown')})"
            )
            return data.get("state")
        except json.JSONDecodeError as e:
            logger.error(f"[Checkpoint] Corrupt JSON for step {step}: {e}")
            return None
        except IOError as e:
            logger.error(f"[Checkpoint] Failed to read step {step}: {e}")
            return None

    def load_checkpoint_metadata(self, step: int) -> Optional[Dict[str, Any]]:
        """
        Load checkpoint metadata without the full state payload.

        Returns:
            Dict with checkpoint_id, step, timestamp, success_status, error_message,
            or None if not found.
        """
        path = self.checkpoint_dir / f"step-{step:02d}.json"
        if not path.exists():
            return None

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return {
                "checkpoint_id": data.get("checkpoint_id", self._make_checkpoint_id(step)),
                "step": data.get("step", step),
                "timestamp": data.get("timestamp"),
                "session_id": data.get("session_id", self.session_id),
                "success_status": data.get("success_status", True),
                "error_message": data.get("error_message"),
            }
        except Exception as e:
            logger.error(f"[Checkpoint] Failed to load metadata for step {step}: {e}")
            return None

    def load_checkpoint_by_id(self, checkpoint_id: str, allow_degraded: bool = False) -> Optional[Dict[str, Any]]:
        """
        Load state from a checkpoint using its checkpoint_id string.

        Supports format: "{session_id}:step-{N}" or just "step-{N}".

        This is a resume entry point and therefore refuses to serve a session
        whose checkpoint chain is known to have a hole.

        Args:
            checkpoint_id: e.g. "my-session-123:step-05" or "step-05"
            allow_degraded: Explicitly accept resuming a degraded session.

        Returns:
            State dict, or None.

        Raises:
            CheckpointDegradedError: When the session is degraded and
                allow_degraded is False.
        """
        self._guard_resume(allow_degraded)

        # Parse step number from checkpoint_id
        try:
            if ":" in checkpoint_id:
                step_part = checkpoint_id.split(":")[-1]  # "step-05"
            else:
                step_part = checkpoint_id  # "step-05" or "05"

            if step_part.startswith("step-"):
                step = int(step_part[5:])
            else:
                step = int(step_part)
        except (ValueError, IndexError):
            logger.error(f"[Checkpoint] Cannot parse checkpoint_id: {checkpoint_id}")
            return None

        return self.load_checkpoint(step)

    def get_last_checkpoint(self, allow_degraded: bool = False) -> Tuple[Optional[int], Optional[Dict[str, Any]]]:
        """
        Find and return the most recently saved checkpoint.

        This is a resume entry point and therefore refuses to serve a session
        whose checkpoint chain is known to have a hole.

        Args:
            allow_degraded: Explicitly accept resuming a degraded session.

        Returns:
            (step_number, state_dict) or (None, None) if no checkpoints exist.

        Raises:
            CheckpointDegradedError: When the session is degraded and
                allow_degraded is False.
        """
        self._guard_resume(allow_degraded)

        checkpoint_files = sorted(self.checkpoint_dir.glob("step-*.json"))
        if not checkpoint_files:
            logger.info("[Checkpoint] No checkpoints found in session directory")
            return None, None

        last_file = checkpoint_files[-1]
        try:
            step_str = last_file.stem.split("-")[1]  # "step-03" -> "03"
            step = int(step_str)
        except (IndexError, ValueError):
            logger.warning(f"[Checkpoint] Unexpected filename format: {last_file.name}")
            return None, None

        state = self.load_checkpoint(step)
        return step, state

    def get_last_successful_checkpoint(
        self, allow_degraded: bool = False
    ) -> Tuple[Optional[int], Optional[Dict[str, Any]]]:
        """
        Find the most recently saved checkpoint where success_status=True.

        Useful when you want to resume from a known-good state rather than
        the absolute last checkpoint (which may have been for a failed step).
        This is a resume entry point and therefore refuses to serve a session
        whose checkpoint chain is known to have a hole.

        Args:
            allow_degraded: Explicitly accept resuming a degraded session.

        Returns:
            (step_number, state_dict) or (None, None) if none found.

        Raises:
            CheckpointDegradedError: When the session is degraded and
                allow_degraded is False.
        """
        self._guard_resume(allow_degraded)

        checkpoint_files = sorted(self.checkpoint_dir.glob("step-*.json"), reverse=True)
        for f in checkpoint_files:
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                if data.get("success_status", True):
                    step_str = f.stem.split("-")[1]
                    step = int(step_str)
                    return step, data.get("state")
            except (OSError, ValueError, IndexError) as exc:
                logger.debug(f"[Checkpoint] skipping unreadable checkpoint {f.name}: {exc}")
                continue

        return None, None

    def list_checkpoints(self) -> List[Dict[str, Any]]:
        """
        Return metadata list of all saved checkpoints (no state payloads).

        Returns:
            List of dicts: [{checkpoint_id, step, timestamp, success_status, path}, ...]
        """
        result = []
        for f in sorted(self.checkpoint_dir.glob("step-*.json")):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                result.append(
                    {
                        "checkpoint_id": data.get("checkpoint_id", self._make_checkpoint_id(data.get("step", 0))),
                        "step": data.get("step"),
                        "timestamp": data.get("timestamp"),
                        "success_status": data.get("success_status", True),
                        "error_message": data.get("error_message"),
                        "path": str(f),
                    }
                )
            except (OSError, ValueError) as exc:
                logger.debug(f"[Checkpoint] skipping unreadable checkpoint {f.name}: {exc}")
        return result

    def delete_checkpoint(self, step: int) -> bool:
        """
        Remove a specific checkpoint file.

        Args:
            step: Step number to remove.

        Returns:
            True if removed or did not exist, False on error.
        """
        path = self.checkpoint_dir / f"step-{step:02d}.json"
        try:
            if path.exists():
                path.unlink()
                logger.info(f"[Checkpoint] Deleted step {step} checkpoint")
            return True
        except (IOError, PermissionError) as e:
            logger.error(f"[Checkpoint] Failed to delete step {step}: {e}")
            return False

    def clear_all(self) -> int:
        """
        Remove every checkpoint file in the session directory.

        Returns:
            Count of files removed.
        """
        removed = 0
        for f in self.checkpoint_dir.glob("*.json"):
            try:
                f.unlink()
                removed += 1
            except IOError:
                pass
        logger.info(f"[Checkpoint] Cleared {removed} checkpoint(s)")
        return removed


# ---------------------------------------------------------------------------
# Convenience factory
# ---------------------------------------------------------------------------


def create_checkpoint_manager(session_id: str) -> CheckpointManager:
    """Create a CheckpointManager for the given session."""
    return CheckpointManager(session_id)


def write_progress_projection(
    manager: CheckpointManager,
    step: int,
    session_dir: str,
    step_label: str = "",
) -> Optional[Dict[str, Any]]:
    """Write the per-step progress surface as a projection of the checkpoint record.

    The progress surface exists so that a reader can learn how far a session got
    without loading a full state blob. It must never be a second writer of that
    fact: every field is read back out of the checkpoint record, so a step that
    the checkpoint does not carry can never appear here. When no checkpoint record
    exists for the step, nothing is written and None is returned, which leaves any
    previous projection in place rather than advancing it past the durable record.

    Args:
        manager: CheckpointManager owning the authoritative record.
        step: Step number to project.
        session_dir: Directory the projection file lives in.
        step_label: Human-readable step label, carried through for display only.

    Returns:
        The projected dict that was written, or None when nothing was written.
    """
    if not session_dir:
        return None

    projected = manager.project_progress(step)
    if projected is None:
        logger.debug("[Checkpoint] No checkpoint record for step %s; progress projection skipped" % step)
        return None

    if step_label:
        projected["last_step_label"] = step_label

    try:
        target = Path(session_dir) / PROGRESS_PROJECTION_FILENAME
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(projected, indent=2), encoding="utf-8")
    except OSError as exc:
        logger.debug("[Checkpoint] progress projection write skipped: %s" % exc)
        return None

    return projected


# ---------------------------------------------------------------------------
# CLI / smoke-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    sid = sys.argv[1] if len(sys.argv) > 1 else "test-session-cp"
    mgr = CheckpointManager(sid)

    dummy_state = {
        "session_id": sid,
        "user_message": "Implement feature X",
        "step1_plan_required": True,
        "step3_tasks_validated": [{"id": "t1", "description": "Write tests"}],
    }

    print("Saving checkpoint for step 3 (success)...")
    ok = mgr.save_checkpoint(3, dummy_state, success_status=True)
    print(f"  saved={ok}")

    print("Saving checkpoint for step 4 (failed)...")
    ok = mgr.save_checkpoint(4, dummy_state, success_status=False, error_message="LLM timeout after 30s")
    print(f"  saved={ok}")

    print("Loading checkpoint for step 3...")
    recovered = mgr.load_checkpoint(3)
    print(f"  user_message={recovered.get('user_message') if recovered else 'NONE'}")

    print("Loading metadata for step 4...")
    meta = mgr.load_checkpoint_metadata(4)
    print(f"  metadata={meta}")

    print("Loading by checkpoint_id...")
    cid = mgr._make_checkpoint_id(3)
    recovered_by_id = mgr.load_checkpoint_by_id(cid)
    print(f"  loaded_by_id ok={recovered_by_id is not None}")

    print("Getting last successful checkpoint...")
    last_step, _ = mgr.get_last_successful_checkpoint()
    print(f"  last_successful_step={last_step}")

    print("Getting last checkpoint (any)...")
    last_step, last_state = mgr.get_last_checkpoint()
    print(f"  last_step={last_step}")

    print("Listing all checkpoints...")
    for cp in mgr.list_checkpoints():
        print(f"  step={cp['step']} id={cp['checkpoint_id']} ok={cp['success_status']}")

    print("Done.")

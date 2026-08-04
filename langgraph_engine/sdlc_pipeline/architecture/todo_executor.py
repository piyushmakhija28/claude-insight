"""
Level 3 - TODO Executor

Executes a list of TODO items produced by todo_decomposer, calling
orchestrator_agent_caller.py as a subprocess for each TODO.

Supports resume via a sidecar checkpoint file (session_dir/todo_checkpoint.json)
that is read on entry and updated after each TODO completes.

Environment:
  STEP0_TODO_EXEC_SILENCE   seconds of per-TODO subprocess silence tolerated before
                            the child is treated as stuck (default: unbounded)
  STEP0_TODO_EXEC_ATTEMPTS  iteration bound on the TODO loop (default: 200)
  STEP0_TODO_EXEC_PATIENCE  consecutive identical loop states that count as
                            no progress (default: 3)

The former STEP0_TODO_EXEC_TIMEOUT killed each TODO at a fixed 300 seconds. Its
replacement measures silence, not duration, and defaults to unbounded. The loop
itself is bounded by an attempt budget and a convergence signal instead, per
NFR-2 / ADR-016 mechanisms 1 and 3.
"""

import json
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from ...liveness import (
    AttemptBudget,
    BreakerOpen,
    BudgetExhausted,
    ConvergenceMonitor,
    NoProgress,
    env_int,
    env_optional_seconds,
    run_supervised,
)

try:
    from loguru import logger
except ImportError:
    import logging

    logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_ORCHESTRATOR_CALLER_PATH = Path(__file__).resolve().parent / "orchestrator_agent_caller.py"
_SILENCE_ENV_VAR = "STEP0_TODO_EXEC_SILENCE"
_ATTEMPTS_ENV_VAR = "STEP0_TODO_EXEC_ATTEMPTS"
_PATIENCE_ENV_VAR = "STEP0_TODO_EXEC_PATIENCE"
_DEFAULT_ATTEMPT_LIMIT = 200
_DEFAULT_PATIENCE = 3
_CHECKPOINT_FILENAME = "todo_checkpoint.json"

# ---------------------------------------------------------------------------
# Checkpoint helpers
# ---------------------------------------------------------------------------


def _load_checkpoint(checkpoint_path):
    """Load sidecar checkpoint file. Returns (completed_ids set, results dict)."""
    try:
        path = Path(checkpoint_path)
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
            completed = set(data.get("completed_ids", []))
            results = data.get("results", {})
            return completed, results
    except Exception as exc:
        logger.debug("[todo_executor] checkpoint load failed (ignored): {}", exc)
    return set(), {}


def _save_checkpoint(checkpoint_path, completed_ids, results):
    """Write sidecar checkpoint file atomically. Never raises."""
    try:
        path = Path(checkpoint_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "completed_ids": sorted(completed_ids),
            "results": results,
        }
        path.write_text(json.dumps(data, ensure_ascii=True, indent=2), encoding="utf-8")
    except Exception as exc:
        logger.debug("[todo_executor] checkpoint save failed (ignored): {}", exc)


def _resolve_checkpoint_path(session_dir):
    """Return absolute path for the checkpoint sidecar file."""
    if session_dir:
        return str(Path(session_dir) / _CHECKPOINT_FILENAME)
    return str(Path(tempfile.gettempdir()) / _CHECKPOINT_FILENAME)


# ---------------------------------------------------------------------------
# Per-TODO execution
# ---------------------------------------------------------------------------


def _execute_single_todo(todo_item):
    """Call orchestrator_agent_caller.py for one TODO item.

    Returns a result dict with status, llm_response, and error fields.
    Never raises. Bounded by progress rather than by elapsed time: a TODO that
    keeps producing output runs as long as it needs to.
    """
    todo_id = todo_item.get("id", "unknown")
    todo_prompt = todo_item.get("prompt", "")
    prompt_file = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".txt",
            delete=False,
            encoding="utf-8",
        ) as tf:
            tf.write(todo_prompt)
            prompt_file = tf.name

        cmd = [
            sys.executable,
            str(_ORCHESTRATOR_CALLER_PATH),
            "--orchestration-prompt-file",
            prompt_file,
        ]

        logger.info("[todo_executor] Executing TODO {} via orchestrator_agent_caller", todo_id)

        proc = run_supervised(
            cmd,
            lease_interval=env_optional_seconds(_SILENCE_ENV_VAR),
            lease_name="todo_exec_%s" % todo_id,
            breaker_name="claude_cli",
        )

        stdout = proc.stdout or ""
        stderr_preview = (proc.stderr or "")[:200]

        if proc.returncode != 0 and not stdout.strip():
            return {
                "status": "FAILED",
                "todo_id": todo_id,
                "result": None,
                "error": "subprocess exit %d: %s" % (proc.returncode, stderr_preview),
            }

        parsed = {}
        try:
            if stdout.strip():
                parsed = json.loads(stdout)
        except (json.JSONDecodeError, ValueError):
            parsed = {"llm_response": stdout.strip()}

        return {
            "status": "SUCCESS",
            "todo_id": todo_id,
            "result": parsed,
            "error": None,
        }

    except BreakerOpen as exc:
        return {
            "status": "FAILED",
            "todo_id": todo_id,
            "result": None,
            "error": "circuit breaker open, subprocess not started: %s" % exc,
        }
    except NoProgress as exc:
        return {
            "status": "FAILED",
            "todo_id": todo_id,
            "result": None,
            "error": "subprocess made no progress: %s" % exc,
        }
    except Exception as exc:
        return {
            "status": "FAILED",
            "todo_id": todo_id,
            "result": None,
            "error": str(exc),
        }
    finally:
        if prompt_file:
            try:
                Path(prompt_file).unlink(missing_ok=True)
            except OSError as exc:
                logger.debug(f"todo_executor: temp prompt file cleanup skipped: {exc}")


def _observe_progress(convergence, settled, step_number):
    """Feed the loop's settled-item count to the convergence monitor.

    The observed state is the number of TODOs that have SETTLED -- completed or
    been skipped -- and deliberately not the checkpoint's completed-id set, which
    this loop grows on failure as well as on success and which therefore cannot
    distinguish the two. A run of failures leaves the settled count unchanged, so
    identical consecutive observations mean exactly what ADR-016's mechanism 3
    wants them to mean: the loop is turning without getting anywhere.

    Args:
        convergence: The monitor accumulating observations.
        settled: Count of TODOs that succeeded or were skipped.
        step_number: Pipeline step number used in log messages.

    Returns:
        bool: True when the loop should stop for lack of progress.
    """
    if not convergence.observe(settled):
        return False
    logger.error(
        "[todo_executor] step={} no progress: {} consecutive iterations settled nothing; stopping",
        step_number,
        convergence.consecutive_identical,
    )
    return True


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def execute_todo_list(
    state: Dict[str, Any],
    todo_list: List[Dict[str, Any]],
    checkpoint_manager: Optional[Any] = None,
    step_number: int = 0,
) -> List[Dict[str, Any]]:
    """Execute a list of TODO items, resuming from sidecar checkpoint if present.

    For each TODO in todo_list:
      - Skips items whose ID already appears in the checkpoint's completed_ids.
      - Calls orchestrator_agent_caller.py as a subprocess with the TODO prompt.
      - Saves the sidecar checkpoint after each completion.

    Args:
        state: FlowState dict providing session_dir and project_root.
        todo_list: List of TODO dicts from todo_decomposer.
        checkpoint_manager: Reserved for future use; ignored when None.
        step_number: Pipeline step number used in log messages.

    Returns:
        List of per-TODO result dicts, each containing todo_id, status,
        result, and error fields.
    """
    session_dir = state.get("session_dir", "") or ""
    checkpoint_path = _resolve_checkpoint_path(session_dir)

    completed_ids, checkpoint_results = _load_checkpoint(checkpoint_path)
    if completed_ids:
        logger.info(
            "[todo_executor] step={} Resume: {} already completed TODOs",
            step_number,
            len(completed_ids),
        )

    execution_results: List[Dict[str, Any]] = []
    budget = AttemptBudget.from_env(_ATTEMPTS_ENV_VAR, _DEFAULT_ATTEMPT_LIMIT, name="todo_executor")
    convergence = ConvergenceMonitor(env_int(_PATIENCE_ENV_VAR, _DEFAULT_PATIENCE), name="todo_executor")
    settled = 0

    for todo_item in todo_list:
        todo_id = todo_item.get("id", "")

        try:
            budget.consume()
        except BudgetExhausted as exhausted:
            logger.error("[todo_executor] step={} {}", step_number, exhausted)
            break

        if todo_id and todo_id in completed_ids:
            logger.info("[todo_executor] step={} Skipping completed TODO {}", step_number, todo_id)
            skipped_result = checkpoint_results.get(todo_id, {})
            execution_results.append(
                {
                    "status": "SKIPPED",
                    "todo_id": todo_id,
                    "result": skipped_result,
                    "error": None,
                }
            )
            settled += 1
            if _observe_progress(convergence, settled, step_number):
                break
            continue

        item_result = _execute_single_todo(todo_item)
        execution_results.append(item_result)
        if item_result.get("status") == "SUCCESS":
            settled += 1

        if todo_id:
            completed_ids.add(todo_id)
            checkpoint_results[todo_id] = item_result.get("result") or {}
            _save_checkpoint(checkpoint_path, completed_ids, checkpoint_results)

        if _observe_progress(convergence, settled, step_number):
            break

        logger.info(
            "[todo_executor] step={} TODO {} -> {}",
            step_number,
            todo_id,
            item_result.get("status", "UNKNOWN"),
        )

    return execution_results

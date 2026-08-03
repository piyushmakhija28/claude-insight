"""Step 8/9 implementation functions.

Facade module: wraps Level3GitHubWorkflow (Step 8 issue creation, Step 9
branch creation) behind thin, state-dict-first functions that the step
wrappers in issue_and_branch_wrapper.py invoke.

Restored 2026-04-14 during v1.16.x restoration cycle (issue #213),
adapted for:
  - v1.11 physical layout (nodes/ package)
  - loguru-with-stdlib-fallback logger import pattern (matches sibling nodes)
  - Relative import paths corrected for nodes/ subpackage depth

Design patterns:
  - Facade: thin wrapper over Level3GitHubWorkflow
  - Null Object: returns well-formed ERROR-status dict on failure (never None, never raises)
  - Defensive Import: every external import wrapped in try/except

Windows-safe: ASCII only.
"""

import os
import re
from typing import Any, Dict

try:
    from loguru import logger
except ImportError:
    import logging

    logger = logging.getLogger(__name__)

try:
    from ...flow_state import FlowState
except ImportError:
    FlowState = dict  # type: ignore[misc,assignment]

try:
    from ..github_lifecycle import Level3GitHubWorkflow
except ImportError:  # pragma: no cover
    Level3GitHubWorkflow = None  # type: ignore[misc,assignment]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _generate_issue_title(user_message: str, task_type: str, complexity: int) -> str:
    """Generate a short, descriptive GitHub issue title.

    Tries llm_call (fast model); falls back to a cleaned user message.
    """
    if not user_message:
        return "[%s] Task (complexity %d/10)" % (task_type, complexity)

    prompt = (
        "Generate a short GitHub issue title (max 70 chars) for this task. "
        "Return ONLY the title text, no quotes, no prefix, no explanation.\n\n"
        "Task type: %s\n"
        "User request: %s\n\n"
        "Title:" % (task_type, user_message[:300])
    )

    try:
        from langgraph_engine.llm_call import llm_call

        llm_title = llm_call(prompt, model="fast", temperature=0.3, timeout=30)
        if llm_title:
            llm_title = llm_title.strip().strip('"').strip("'").split("\n")[0].strip()
            if llm_title and len(llm_title) > 5:
                return llm_title[:80]
    except Exception as exc:
        logger.debug(f"[step8] LLM issue-title generation skipped: {exc}")

    clean = user_message.strip().split("\n")[0][:70]
    if clean and clean[0].islower():
        clean = clean[0].upper() + clean[1:]
    return clean


GITHUB_ISSUE_EFFECT_NAME = "github_issue"


def _create_issue_once(state: FlowState, create_fn) -> Dict[str, Any]:
    """Create the GitHub issue at most once per session-and-step.

    Issue creation is a non-idempotent external effect: a resumed or retried
    Step 2 that calls it again produces a second issue for one logical task.
    This repository has already shipped that exact duplicate. The effect ledger
    keys the creation on the step's checkpoint identity, so a replay returns the
    recorded issue instead of POSTing again.

    When the ledger is unavailable the creation proceeds unguarded rather than
    failing the step, because losing the guard is recoverable and blocking issue
    creation outright is not.

    Args:
        state: Current FlowState, used for the session identity.
        create_fn: Zero-argument callable performing the actual creation.

    Returns:
        The creation result dict, either freshly produced or replayed.
    """
    session_id = state.get("session_id", "") or os.environ.get("CURRENT_SESSION_ID", "")
    if not session_id:
        logger.warning("Step 8: no session_id available; issue creation runs without replay guard")
        return create_fn()

    try:
        from ...effect_ledger import EffectLedger
    except ImportError as exc:
        logger.warning("Step 8: effect ledger unavailable ({}); creating issue unguarded", exc)
        return create_fn()

    ledger = EffectLedger(session_id)
    key = ledger.effect_key(step=2, effect_name=GITHUB_ISSUE_EFFECT_NAME)
    effect, replayed = ledger.run_once(
        key,
        create_fn,
        commit_predicate=lambda r: bool(isinstance(r, dict) and r.get("success")),
    )
    if replayed:
        logger.info("Step 8: replayed existing issue for {} -- no duplicate created", key)
    return effect


def _slugify_title(title: str, max_len: int = 50) -> str:
    """Convert a title to a branch-name-safe slug."""
    slug = title.lower().strip()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug[:max_len].rstrip("-")


# ---------------------------------------------------------------------------
# Step 8: GitHub Issue Creation
# ---------------------------------------------------------------------------


def step2_github_issue_creation(state: FlowState) -> Dict[str, Any]:
    """Step 8: Create GitHub issue for tracking the implementation task.

    Skips issue creation for very short prompts, system notifications, and
    LLM-analysis failures.  Falls back gracefully when GitHub is unreachable.

    Returns step2_* keys including issue_id, issue_url, and status.
    """
    try:
        session_path = state.get("session_dir") or os.environ.get("CLAUDE_SESSION_PATH")
        project_root = state.get("project_root", ".")
        user_msg = state.get("user_message", "") or os.environ.get("CURRENT_USER_MESSAGE", "")

        task_type = state.get("step1_task_type", "General Task")
        complexity = state.get("step1_complexity", 5)
        reasoning = state.get("step1_reasoning", "")
        msg_lower = user_msg.strip().lower()

        # Smart-skip conditions
        should_skip = False
        skip_reason = ""

        if len(msg_lower) < 10:
            should_skip = True
            skip_reason = "prompt too short (%d chars)" % len(msg_lower)
        elif msg_lower.startswith("<task-notification>") or msg_lower.startswith("<system"):
            should_skip = True
            skip_reason = "system notification"
        elif "LLM analysis parsing failed" in reasoning:
            should_skip = True
            skip_reason = "LLM analysis failed"
        elif task_type == "General Task" and complexity == 5 and not reasoning:
            should_skip = True
            skip_reason = "default task type with no analysis"

        if should_skip:
            logger.info("Step 8: Skipping issue creation -- {}", skip_reason)
            return {
                "step2_issue_id": "0",
                "step2_issue_url": "",
                "step2_issue_created": False,
                "step2_title": "",
                "step2_label": "",
                "step2_status": "SKIPPED",
                "step2_skip_reason": skip_reason,
            }

        skill = state.get("step1_skill", "")
        agent = state.get("step1_agent", "")
        framework = state.get("detected_framework", "unknown")
        title = _generate_issue_title(user_msg, task_type, complexity)

        # Build issue body
        body_parts = [
            "## Task Summary",
            user_msg[:500],
            "",
            "## Details",
            "- **Type**: %s" % task_type,
            "- **Complexity**: %d/10" % complexity,
            "- **Framework**: %s" % framework,
        ]
        if skill:
            body_parts.append("- **Skill**: %s" % skill)
        if agent:
            body_parts.append("- **Agent**: %s" % agent)
        body_parts.append("")

        tasks = state.get("step1_tasks", {}).get("tasks", [])
        if tasks:
            body_parts.append("## Implementation Checklist")
            for task in tasks[:10]:
                if isinstance(task, dict):
                    body_parts.append("- [ ] %s" % task.get("description", task.get("id", "")))
                else:
                    body_parts.append("- [ ] %s" % str(task))
            body_parts.append("")

        body_parts += ["---", "*Generated by Claude Workflow Engine*"]
        body = "\n".join(body_parts)

        plan_text = state.get("step1_plan", "")
        if isinstance(plan_text, dict):
            plan_text = str(plan_text)

        if Level3GitHubWorkflow is not None:
            try:
                workflow = Level3GitHubWorkflow(session_dir=session_path or ".", repo_path=project_root)
                result = _create_issue_once(
                    state,
                    lambda: workflow.step2_create_issue(
                        title=title,
                        description=body,
                        task_summary=user_msg,
                        implementation_plan=plan_text,
                    ),
                )
                if result.get("success"):
                    return {
                        "step2_issue_id": str(result.get("issue_number", "0")),
                        "step2_issue_url": result.get("issue_url", ""),
                        "step2_issue_created": True,
                        "step2_title": title,
                        "step2_label": result.get("label", task_type),
                        "step2_status": "OK",
                    }
                else:
                    logger.warning("GitHub issue creation failed: {}. Using fallback.", result.get("error"))
            except Exception as gh_err:
                logger.warning("Level3GitHubWorkflow unavailable: {}. Using fallback.", gh_err)

        # Fallback
        return {
            "step2_issue_id": "0",
            "step2_issue_url": "",
            "step2_issue_created": False,
            "step2_title": title,
            "step2_label": task_type,
            "step2_status": "FALLBACK",
        }

    except Exception as e:
        return {"step2_issue_created": False, "step2_status": "ERROR", "step2_error": str(e)}


# ---------------------------------------------------------------------------
# Step 9: Branch Creation
# ---------------------------------------------------------------------------


def step3_branch_creation(state: FlowState) -> Dict[str, Any]:
    """Step 9: Create feature branch for the implementation.

    Skips branch creation when no real GitHub issue exists (issue_id == 0).
    Falls back gracefully when GitHub remote is unreachable.

    Returns step3_* keys including branch_name, branch_created, and status.
    """
    try:
        issue_id = state.get("step2_issue_id", "0")
        task_type = state.get("step1_task_type", "task").lower()
        label = state.get("step2_label", task_type)
        session_path = state.get("session_dir") or os.environ.get("CLAUDE_SESSION_PATH", ".")
        project_root = state.get("project_root", ".")

        branch_label = label.lower().strip() if label else task_type.lower().replace(" ", "-")

        # Skip if no real issue was created
        if issue_id == "0" or not state.get("step2_issue_created", False):
            logger.info("Step 9: Skipping branch creation -- no GitHub issue created (issue_id=0)")
            return {"step3_branch_name": "", "step3_branch_created": False, "step3_status": "SKIPPED"}

        if Level3GitHubWorkflow is not None:
            try:
                workflow = Level3GitHubWorkflow(session_dir=session_path, repo_path=project_root)
                result = workflow.step3_create_branch(
                    issue_number=int(issue_id) if issue_id.isdigit() else 0,
                    label=branch_label,
                    session_dir=session_path,
                )
                if result.get("success"):
                    return {
                        "step3_branch_name": result.get("branch_name", ""),
                        "step3_branch_created": True,
                        "step3_conflict_detected": result.get("conflict_detected", False),
                        "step3_status": "OK",
                    }
                else:
                    logger.warning("Branch creation failed: {}. Using fallback.", result.get("error"))
            except Exception as gh_err:
                logger.warning("Level3GitHubWorkflow unavailable for branch: {}. Using fallback.", gh_err)

        # Fallback
        branch_name = "%s/issue-%s" % (branch_label, issue_id)
        return {
            "step3_branch_name": branch_name,
            "step3_branch_created": False,
            "step3_status": "FALLBACK",
        }

    except Exception as e:
        return {"step3_branch_created": False, "step3_status": "ERROR", "step3_error": str(e)}

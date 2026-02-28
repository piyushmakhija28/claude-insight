# GitHub Branch + PR Workflow Policy

**Version:** 1.0.0
**Last Updated:** 2026-02-28
**Status:** Active
**Depends On:** github-issues-integration-policy.md

---

## Overview

This policy defines the automated GitHub workflow that runs during a Claude Code session:
**Issue -> Branch -> Work -> Commit -> Push -> PR -> Auto-Review -> Merge**

The workflow builds on the GitHub Issues integration (v1) by adding automatic branch creation,
pull request management, and auto-review with session metrics.

---

## Branch Naming

**Format:** `issue-{N}-{slug}`

- `{N}` = GitHub issue number from the first TaskCreate
- `{slug}` = lowercase, hyphenated, max 40 chars from task subject
- Example: `issue-42-implement-github-pr-workflow`

**Rules:**
- One branch per session (first TaskCreate triggers creation)
- All subsequent tasks stay on the same branch
- Branch is only created from `main` or `master`
- If already on a feature branch, branch creation is skipped

---

## Workflow Triggers

| Event | Action | Script |
|-------|--------|--------|
| First TaskCreate | Create issue + create branch | post-tool-tracker.py -> github_issue_manager.py |
| Subsequent TaskCreate | Create issue (stay on branch) | post-tool-tracker.py -> github_issue_manager.py |
| TaskUpdate(completed) | Close issue | post-tool-tracker.py -> github_issue_manager.py |
| All tasks done + Stop | Commit + Push + PR + Review + Merge | stop-notifier.py -> github_pr_workflow.py |

---

## PR Template

**Title:** Derived from session task types (max 70 chars)

**Body structure:**
```markdown
## Summary
- [bullet points from session requests]

## Session Stats
- Requests: N
- Max Complexity: X/25
- Skills: skill1, skill2

## Issues
Closes #N
Closes #M

---
_Auto-created by Claude Memory System (GitHub PR Workflow)_
```

---

## Auto-Review

The system posts a review comment (not an approval) on the PR containing:

- **Session Metrics:** request count, task types, complexity stats, skills used
- **Work Done:** list of prompts/tasks with their types and models
- **Tool Usage:** total tool calls, tasks completed, top 5 tools used

Uses `gh pr comment` instead of `gh pr review --approve` to avoid branch protection conflicts.

---

## Merge Strategy

- **Method:** `gh pr merge --merge --delete-branch`
- **Fallback:** If merge fails (branch protection, required reviews), PR is left open with a message
- **Post-merge:** Automatically switches to `main` and pulls latest
- **Never force-merges:** Respects all branch protection rules

---

## Safety

- All `gh` CLI calls have 30s timeout
- Every step is wrapped in try/except (never fails the stop hook)
- If any step fails, subsequent steps are skipped gracefully
- GitHub operations capped at 10 per session
- No force-push, no branch deletion (except via --delete-branch on merge)
- Logs all actions to `~/.claude/memory/logs/stop-notifier.log`

---

## Data Storage

**github-issues.json** (per-session) stores:
```json
{
  "task_to_issue": {
    "1": { "issue_number": 42, "status": "open", ... }
  },
  "session_branch": "issue-42-implement-github-pr-workflow",
  "branch_created_at": "2026-02-28T10:30:00",
  "branch_from_issue": 42,
  "pr_number": 15,
  "pr_url": "https://github.com/user/repo/pull/15",
  "pr_merged": true,
  "pr_merged_at": "2026-02-28T11:00:00",
  "ops_count": 5
}
```

---

## Prerequisites

1. `gh` CLI installed and authenticated (`gh auth login`)
2. Git repository with remote configured
3. GitHub Issues integration enabled (github_issue_manager.py present)
4. Session tracking active (session-progress.json exists)

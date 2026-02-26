# GitHub Issues Integration Policy - Level 3 Execution System

**Version:** 1.0.0
**Part of:** Level 3: Execution System (12 Steps)
**Status:** Active
**Date:** 2026-02-26

---

## Overview

This policy governs how the Level 3 Execution System automatically creates and manages GitHub Issues for task tracking. When tasks are auto-created during execution, corresponding GitHub Issues are created with comprehensive details, labels, and priorities.

---

## Policy Scope

**Applies to:** Level 3: Execution System, Step 3.2 (Task Breakdown) and Step 3.11 (Git Auto-Commit)

**Automatic Triggers:**
- Task creation via TaskCreate tool (Step 3.2)
- Task completion and commit (Step 3.11)
- Major policy enforcement events (Step 3.0+)

---

## GitHub Issues Management

### [3.2] Task Breakdown → Create GitHub Issues

**What Happens:**
When Level 3 auto-creates a task during execution, it ALSO creates a corresponding GitHub Issue with:

#### Issue Details

**Title Format:**
```
[TASK-{task_id}] {task_subject}
```

Example:
```
[TASK-001] Implement GitHub Issues integration for Level 3 flow
```

**Description/Body:**
```markdown
## Task Details
- **Task ID**: {task_id}
- **Status**: In Progress
- **Complexity**: {complexity_level}
- **Task Type**: {task_type}
- **Created**: {timestamp}

## Description
{task_description}

## Acceptance Criteria
- [ ] All sub-tasks completed
- [ ] Code tested and verified
- [ ] Documentation updated
- [ ] Commit created and pushed
- [ ] GitHub Issue closed

## Related Links
- Session ID: {session_id}
- Flow Trace: ~/.claude/memory/logs/sessions/{session_id}/flow-trace.json
- Task File: ~/.claude/memory/tasks/{task_id}.json

## Auto-Generated
This issue was created automatically by Level 3 Execution System.
Do not edit this issue manually - it will be auto-updated.
```

#### Labels

**Standard Labels (Auto-Applied):**

| Label | When Applied | Color |
|-------|--------------|-------|
| `task-auto-created` | Always (identifies auto-created tasks) | Blue |
| `level-3-execution` | Always (part of Level 3 system) | Purple |
| `complexity-low` | When complexity ≤ 3 | Green |
| `complexity-medium` | When complexity 4-9 | Yellow |
| `complexity-high` | When complexity ≥ 10 | Red |
| `type-feature` | When task_type == "feature" | Green |
| `type-bugfix` | When task_type == "bugfix" | Red |
| `type-refactor` | When task_type == "refactor" | Orange |
| `type-documentation` | When task_type == "documentation" | Blue |
| `priority-critical` | When complexity ≥ 15 | Red |
| `priority-high` | When complexity 10-14 | Orange |
| `priority-medium` | When complexity 5-9 | Yellow |
| `priority-low` | When complexity ≤ 4 | Green |
| `session-{session_id}` | Always (session tracking) | Gray |

#### Assignees

```
Automatic: None (open for any team member)
Optional: Can be assigned manually in GitHub
```

#### Milestones

```
Auto-Set: Current Phase (Phase X)
Example: "Phase 6 - Settings & Preferences"
```

### [3.11] Git Auto-Commit → Close GitHub Issues

**What Happens:**
When a task is completed and git auto-commit triggers (Step 3.11), the corresponding GitHub Issue is AUTOMATICALLY CLOSED.

#### Close Mechanism

**Trigger:**
1. Task marked as completed (status = "completed")
2. Git commit created successfully
3. Commit pushed to GitHub

**GitHub Issue Closure:**

```
GitHub Issue Auto-Close Pattern:
- Issue Title: [TASK-001] ...
- Commit Message Includes: "Close #123" or "Closes #123" or "Fixes #123"
- GitHub auto-link detects the pattern
- Issue automatically closed on commit push
```

**Commit Message Format:**
```
{Category}: {brief_description}

{detailed_explanation}

- Completed task {task_id}
- Fixed {issue_count} GitHub issues
- Closes #{issue_number}

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>
```

**Example:**
```
Feature: Implement GitHub Issues integration for Level 3

Add automatic GitHub Issue creation and closure for all auto-created tasks.
Integrates with Level 3 execution system for comprehensive task tracking.
Adds labels, priorities, and session tracking to GitHub Issues.

- Completed task 001
- Fixed 1 GitHub issue
- Closes #42

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>
```

---

## GitHub API Integration

### Authentication

**Method:** GitHub Personal Access Token (PAT)

**Token Scope Required:**
```
- repo:full (read/write repositories)
- issues:read/write (manage issues)
- workflow:read (optional - for workflow automation)
```

**Token Location:**
```
Environment Variable: GITHUB_TOKEN
File Location: ~/.github/token (fallback, not recommended)
```

**Setup:**
```bash
# Set environment variable
export GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

# Or in ~/.bashrc / ~/.zshrc
echo 'export GITHUB_TOKEN="ghp_..."' >> ~/.bashrc
source ~/.bashrc
```

### API Calls

#### Create Issue (Step 3.2)

**Endpoint:**
```
POST /repos/{owner}/{repo}/issues
```

**Request:**
```json
{
  "title": "[TASK-001] Implement GitHub Issues integration",
  "body": "## Task Details\n...",
  "labels": [
    "task-auto-created",
    "level-3-execution",
    "complexity-medium",
    "priority-high"
  ],
  "milestone": null
}
```

**Error Handling:**
- ✅ Network error → Log warning, continue without issue
- ✅ Auth error → Log error, skip issue creation
- ✅ Rate limited → Retry after delay
- ✅ No token → Log notice, continue

#### Close Issue (Step 3.11)

**Endpoint:**
```
PATCH /repos/{owner}/{repo}/issues/{issue_number}
```

**Request:**
```json
{
  "state": "closed",
  "state_reason": "completed"
}
```

**Auto-Link via Commit:**
```
Commit message contains: "Closes #123"
↓
GitHub auto-detects
↓
Issues #123 automatically closed on push
```

---

## Task Tracking Workflow

### Complete Lifecycle

```
┌─────────────────────────────────────────┐
│ [3.0] User sends prompt/message         │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│ [3.2] Task Breakdown                    │
├─ Auto-creates LOCAL task                │
│  └─ ~/.claude/memory/tasks/{id}.json    │
│                                          │
├─ Auto-creates GITHUB ISSUE              │
│  └─ POST /repos/{owner}/{repo}/issues   │
│  └─ With comprehensive labels + details │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│ [3.3-3.10] Execute Task                 │
├─ Work on task                           │
├─ Monitor progress                       │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│ [3.11] Git Auto-Commit                  │
├─ Create commit                          │
├─ Include "Closes #{issue_number}"       │
├─ Push to GitHub                         │
│  └─ GitHub auto-closes issue            │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│ Task Complete                           │
├─ GitHub Issue CLOSED ✓                  │
├─ Git commit PUSHED ✓                    │
├─ Session saved ✓                        │
└─────────────────────────────────────────┘
```

---

## Safety & Constraints

### Rate Limiting

**GitHub API Limits:**
- 60 requests/hour (unauthenticated)
- 5,000 requests/hour (authenticated)

**Our Strategy:**
- Batch operations where possible
- Delay between requests: 500ms
- Max 10 issue operations per session
- Log rate limit hits to ~/.claude/memory/logs/

### Error Recovery

**Network Issues:**
```
Try 1 → Fail → Wait 5s
Try 2 → Fail → Wait 10s
Try 3 → Fail → Log to errors, continue
(never block execution)
```

**Permission Issues:**
```
No GITHUB_TOKEN env var → Log notice, skip GitHub
Invalid token → Log error, skip GitHub
No repo access → Log warning, skip GitHub
(local tasks still created successfully)
```

### Data Privacy

**What's Uploaded to GitHub:**
- Task title, description, labels
- Task type and complexity
- Timestamps
- Session ID (anonymous)

**What's NOT Uploaded:**
- Full prompt/user message content
- API keys or credentials
- User personal information
- Sensitive code (can be edited in GitHub later)

---

## Monitoring & Debugging

### Logging

**Location:** `~/.claude/memory/logs/sessions/{SESSION_ID}/github-issues.log`

**Log Format:**
```
[2026-02-26T10:30:45] [CREATE] Issue #42 created
[2026-02-26T10:30:46] [LABEL] Added 4 labels
[2026-02-26T10:35:12] [CLOSE] Issue #42 closed via commit abc123
[2026-02-26T10:35:13] [SUCCESS] Task lifecycle complete
```

### Debugging Commands

```bash
# View all auto-created issues
gh issue list --label "task-auto-created" --state all

# View current session issues
gh issue list --label "session-{SESSION_ID}"

# Manually close issue (if needed)
gh issue close {ISSUE_NUMBER}

# Check GitHub API status
curl https://api.github.com/repos/{owner}/{repo}/issues

# View last GitHub operation log
tail -f ~/.claude/memory/logs/sessions/{SESSION_ID}/github-issues.log
```

---

## Configuration

### In hook-downloader.py

**Enable/Disable GitHub Issues:**
```python
# In hook-downloader.py
GITHUB_ISSUES_ENABLED = True  # Set False to disable
GITHUB_ISSUES_AUTO_CLOSE = True  # Set False to disable auto-close
```

**Repository Configuration:**
```python
# Detect from git config
GITHUB_OWNER = "piyushmakhija28"  # From git origin
GITHUB_REPO = "claude-code-ide"    # From git origin
```

### In ~/.claude/settings.json

**Add optional GitHub Issues configuration:**
```json
{
  "github": {
    "enabled": true,
    "token_env_var": "GITHUB_TOKEN",
    "auto_create_issues": true,
    "auto_close_issues": true,
    "labels_enabled": true,
    "milestone_tracking": true
  }
}
```

---

## Examples

### Example 1: Simple Bug Fix Task

**Local Task Created:**
```json
{
  "id": "001",
  "subject": "Fix authentication bug in login flow",
  "type": "bugfix",
  "complexity": 5
}
```

**GitHub Issue Created:**
```
Title: [TASK-001] Fix authentication bug in login flow
Labels: task-auto-created, level-3-execution, type-bugfix,
        complexity-medium, priority-medium, session-SESSION_ID
```

**Completed with Commit:**
```
$ git commit -m "Fix: Authentication bug in login flow

Resolve issue where login fails with special characters in password.
Added input validation and error handling.

- Completed task 001
- Closes #45

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>"
$ git push origin main
```

**GitHub Auto-Close:**
```
Issue #45: [TASK-001] Fix authentication bug in login flow
Status: CLOSED (via commit abc123d)
```

---

## Future Enhancements

1. **Linking:** Cross-link issues with related tasks
2. **Milestones:** Auto-assign to current development milestone
3. **Project Boards:** Auto-add to GitHub Project
4. **Code Review:** Link to related pull requests
5. **Notifications:** Email/Slack on issue creation/close
6. **Analytics:** Dashboard of auto-created vs manual issues

---

## References

- [GitHub Issues REST API](https://docs.github.com/en/rest/issues)
- [GitHub Personal Access Tokens](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)
- [GitHub API Rate Limiting](https://docs.github.com/en/rest/overview/resources-in-the-rest-api#rate-limiting)
- Level 3 Execution System (12 Steps)

---

**Status:** ACTIVE
**Last Updated:** 2026-02-26
**Maintainer:** Claude Memory System
**Feedback:** Create issues in claude-insight repo

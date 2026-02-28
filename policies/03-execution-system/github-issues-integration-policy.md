# GitHub Issues Integration Policy - Level 3 Execution System

**Version:** 2.0.0
**Part of:** Level 3: Execution System (12 Steps)
**Status:** Active
**Date:** 2026-02-28

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

**Description/Body (Comprehensive Story Format):**
```markdown
## Story

{Narrative describing the task context based on issue type:
  - fix: Bug identified, needs investigation and resolution
  - feature: New functionality to be designed and implemented
  - refactor: Code restructuring for maintainability
  - docs: Documentation creation or update
  - enhancement: Improving existing feature
  - test: Test coverage addition}

**What needs to be done:**

{task_description}

## Task Overview

| Field | Value |
|-------|-------|
| **Task ID** | {task_id} |
| **Subject** | {subject} |
| **Type** | {issue_type} |
| **Complexity** | {complexity}/25 |
| **Priority** | {Critical/High/Medium/Low} |
| **Model** | {model} |
| **Skill/Agent** | {skill} |

## Acceptance Criteria
- [ ] {criteria derived from description}
- [ ] {type-specific criteria: e.g., "Root cause identified" for fix}
- [ ] Changes committed and pushed

## Session Context

| Field | Value |
|-------|-------|
| **Session ID** | {session_id} |
| **Created At** | {timestamp} |
| **Context Usage** | {context_pct}% |
| **Repository** | {repo_name} |

---
_Auto-created by Claude Memory System (Level 3 Execution) | v3.0.0_
```

#### Labels (Fully Implemented in v3.0.0)

**System Labels (Always Applied):**

| Label | Purpose |
|-------|---------|
| `task-auto-created` | Identifies auto-created tasks |
| `level-3-execution` | Part of Level 3 system |

**Type Labels (Auto-Detected from subject/description):**

| Label | Detected When |
|-------|---------------|
| `bugfix` | Contains: fix, bug, error, broken, crash, issue, resolve |
| `feature` | Default (no other type detected) |
| `refactor` | Contains: refactor, cleanup, reorganize, simplify, restructure |
| `docs` | Contains: doc, readme, comment, documentation, javadoc |
| `enhancement` | Contains: update, enhance, improve, upgrade, optimize |
| `test` | Contains: test, spec, coverage, unit test, integration test |

**Priority Labels (Derived from complexity score):**

| Label | Complexity Range |
|-------|-----------------|
| `priority-critical` | complexity >= 15 |
| `priority-high` | complexity 10-14 |
| `priority-medium` | complexity 5-9 |
| `priority-low` | complexity <= 4 |

**Complexity Labels (Derived from complexity score):**

| Label | Complexity Range |
|-------|-----------------|
| `complexity-high` | complexity >= 10 |
| `complexity-medium` | complexity 4-9 |
| `complexity-low` | complexity <= 3 |

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
When a task is completed, the corresponding GitHub Issue is AUTOMATICALLY CLOSED with a
**comprehensive resolution story** that narrates what was done, how it was investigated,
what files were changed, and how it was verified.

#### Close Mechanism

**Trigger:**
1. Task marked as completed (status = "completed")
2. `close_github_issue()` called with comprehensive closing comment

**Closing Comment Format (Resolution Story):**

```markdown
## Resolution Story

{Narrative paragraph based on issue type:
  - fix: "This bug has been investigated, root-caused, and fixed.
          The investigation involved reading N file(s)...
          The fix was applied across N file(s)...
          Verification was performed using N command(s)..."
  - feature: "The new feature has been fully implemented...
              Research phase: N existing file(s) were studied...
              Implementation phase: N file(s) were created or modified...
              Validation phase: N command(s) were executed..."
  - refactor: "The code has been restructured...
               First, N file(s) were analyzed...
               The refactoring touched N file(s)..."
}

| Field | Value |
|-------|-------|
| **Status** | Completed |
| **Duration** | {Xh Ym / Xm Ys} |
| **Closed At** | {timestamp} |

## Files Changed
- `file1.py`
- `file2.py`

## Changes Made
- file1.py (+50 chars)
- file2.py (120 lines written)

## Files Investigated
- `file3.py`
- `file4.py`

## Root Cause Analysis (RCA) [only for fix type]
**Investigation:** N files investigated
**Root Cause Location:** `file1.py`, `file2.py`
**Fix Applied:** N edit(s) made
**Verification:** N command(s) run to verify fix

## Tool Usage
| Metric | Value |
|--------|-------|
| Total Tool Calls | N |
| Files Read | N |
| Files Changed | N |

## Session Context
| Field | Value |
|-------|-------|
| Session | `SESSION-ID` |
| Complexity | X/25 |
| Model | HAIKU/SONNET |

---
_Auto-closed by Claude Memory System (Level 3 Execution) | v3.0.0_
```

**Commit Message Format:**
```
{Category}: {brief_description}

{detailed_explanation}

- Completed task {task_id}
- Closes #{issue_number}

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
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

### Example 1: Bug Fix Task (complexity 5)

**Local Task Created:**
```json
{
  "id": "1",
  "subject": "Fix authentication bug in login flow",
  "type": "fix",
  "complexity": 5
}
```

**GitHub Issue Created:**
```
Title: [TASK-1] Fix authentication bug in login flow
Labels: task-auto-created, level-3-execution, bugfix, priority-medium, complexity-medium
Branch: fix/45
```

**Issue Body (Story Format):**
```markdown
## Story
A bug has been identified that needs to be resolved. The issue affects
the system behavior described below and requires investigation, root
cause analysis, and a targeted fix.

**What needs to be done:**
Fix authentication bug in login flow - login fails with special characters in password.

## Task Overview
| Field | Value |
|-------|-------|
| **Task ID** | 1 |
| **Type** | fix |
| **Complexity** | 5/25 |
| **Priority** | Medium |

## Acceptance Criteria
- [ ] Fix authentication bug in login flow
- [ ] Root cause identified and documented
- [ ] Fix verified - bug no longer reproducible
- [ ] Changes committed and pushed
```

**Issue Closed (Resolution Story):**
```markdown
## Resolution Story
This bug has been investigated, root-caused, and fixed.
The investigation involved reading 4 file(s) to understand the problem context.
The fix was applied across 2 file(s) to resolve the issue.
Verification was performed using 3 command(s) to confirm the fix works correctly.

## Root Cause Analysis (RCA)
**Investigation:** 4 files investigated
**Root Cause Location:** `src/auth/login.py`, `src/utils/validator.py`
**Fix Applied:** 2 edit(s) made
**Verification:** 3 command(s) run to verify fix
```

### Example 2: New Feature Task (complexity 12)

**GitHub Issue Created:**
```
Title: [TASK-2] Implement user dashboard analytics
Labels: task-auto-created, level-3-execution, feature, priority-high, complexity-high
Branch: feature/67
```

### Example 3: Refactoring Task (complexity 3)

**GitHub Issue Created:**
```
Title: [TASK-3] Refactor database connection pooling
Labels: task-auto-created, level-3-execution, refactor, priority-low, complexity-low
Branch: refactor/89
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
**Last Updated:** 2026-02-28
**Maintainer:** Claude Memory System
**Feedback:** Create issues in claude-insight repo

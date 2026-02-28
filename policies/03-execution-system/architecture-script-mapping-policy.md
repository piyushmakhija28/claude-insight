# Architecture Script Mapping Policy

**Version:** 1.0.0
**Last Updated:** 2026-02-28
**Total Scripts:** 65 architecture scripts + 6 hook scripts = 71 total

---

## Overview

This document maps ALL 65 architecture scripts to their execution status, hook integration point, and purpose. Every script is accounted for - either actively running in hooks, implemented inline, available as on-demand utility, or documented as Phase-4 stub.

---

## Hook Scripts (6 - Always Running)

| Script | Hook Type | Trigger | Purpose |
|--------|-----------|---------|---------|
| `3-level-flow.py` | UserPromptSubmit | Every message | Main 3-level pipeline (L-1, L1, L2, L3) |
| `clear-session-handler.py` | UserPromptSubmit | Every message (before 3-level-flow) | Session state check, /clear handling |
| `pre-tool-enforcer.py` | PreToolUse | Before every tool | L3.1/3.5 blocking + L3.6 hints + L3.7 prevention |
| `post-tool-tracker.py` | PostToolUse | After every tool | L3.9 progress tracking + GitHub issues + build validation |
| `stop-notifier.py` | Stop | After every response | Session save + voice + PR workflow + auto-commit |
| `auto-fix-enforcer.py` | via 3-level-flow.py | Every message | Level -1: 7 system health checks |

---

## Architecture Scripts - Execution Status

### Level 01: Sync System (25 scripts)

#### 01-sync-system/session-management/ (8 scripts)

| Script | Status | Execution Point | Notes |
|--------|--------|----------------|-------|
| `session-loader.py` | **ACTIVE** | `clear-session-handler.py` | Loads past session context on start |
| `session-state.py` | **ACTIVE** (v3.5.0) | `3-level-flow.py` Level 1.4 | Maintains durable session state |
| `auto-save-session.py` | **ACTIVE** (v3.5.0) | `stop-notifier.py` session end | Auto-saves session before cleanup |
| `archive-old-sessions.py` | **ACTIVE** (v3.5.0) | `stop-notifier.py` session end | Archives sessions >30 days, keeps last 10 |
| `session-search.py` | ON-DEMAND | Manual CLI | Search sessions by tags/project/date |
| `session-save-triggers.py` | ON-DEMAND | Manual CLI | Detects threshold conditions for session save |
| `protect-session-memory.py` | ON-DEMAND | Manual CLI | Verifies session files are protected |
| `session-start-check.py` | ON-DEMAND | Manual CLI | Startup health check (daemon status, recommendations) |

#### 01-sync-system/context-management/ (11 scripts)

| Script | Status | Execution Point | Notes |
|--------|--------|----------------|-------|
| `context-monitor-v2.py` | **ACTIVE** | `3-level-flow.py` Level 1.1 + Step 3.3 | Enhanced context monitor (called twice per message) |
| `context-monitor.py` | SUPERSEDED | - | Original version, replaced by context-monitor-v2.py |
| `context-estimator.py` | SUPERSEDED | - | Replaced by context-monitor-v2.py |
| `monitor-and-cleanup-context.py` | ON-DEMAND | Manual CLI | Triggers cleanup when over threshold |
| `context-extractor.py` | ON-DEMAND | Manual CLI | Extracts essential info from tool outputs |
| `smart-file-summarizer.py` | ON-DEMAND | Manual CLI | Generates intelligent file summaries |
| `context-cache.py` | ON-DEMAND | Manual CLI | File content summary caching |
| `tiered-cache.py` | ON-DEMAND | Manual CLI | Three-tier cache manager (hot/warm/cold) |
| `auto-context-pruner.py` | ON-DEMAND | Manual CLI | Auto-prunes context when >70% |
| `smart-cleanup.py` | ON-DEMAND | Manual CLI | Policy-driven cleanup with dry-run |
| `file-type-optimizer.py` | ON-DEMAND | Manual CLI | Optimal read command per file type |
| `update-context-usage.py` | ON-DEMAND | Manual CLI | Manually update context tracking file |

#### 01-sync-system/user-preferences/ (4 scripts)

| Script | Status | Execution Point | Notes |
|--------|--------|----------------|-------|
| `load-preferences.py` | **ACTIVE** (v3.5.0) | `3-level-flow.py` Level 1.3 | Loads user preferences for decision-making |
| `track-preference.py` | ON-DEMAND | Manual CLI | Records a single preference entry |
| `preference-detector.py` | ON-DEMAND | Manual CLI | Auto-detects preferences from conversation logs |
| `preference-auto-tracker.py` | DAEMON | Not hook-compatible | Requires background process (monitors logs) |

#### 01-sync-system/pattern-detection/ (2 scripts)

| Script | Status | Execution Point | Notes |
|--------|--------|----------------|-------|
| `detect-patterns.py` | ON-DEMAND | Manual CLI | Slow (reads all sessions), run manually |
| `apply-patterns.py` | ON-DEMAND | Manual CLI | Suggests stored patterns for a topic |

---

### Level 02: Standards System (1 script)

| Script | Status | Execution Point | Notes |
|--------|--------|----------------|-------|
| `standards-loader.py` | **ACTIVE** | `3-level-flow.py` Level 2 | Loads all coding standards and rules |

---

### Level 03: Execution System (39 scripts)

#### 03-execution-system/00-prompt-generation/ (2 scripts)

| Script | Status | Execution Point | Notes |
|--------|--------|----------------|-------|
| `prompt-generator.py` | **ACTIVE** | `3-level-flow.py` Steps 3.0 + 3.5 | Generates structured prompts (called twice) |
| `prompt-auto-wrapper.py` | PHASE-4 | Not ready | Phase-4 automation wrapper (auto-generates prompts) |

#### 03-execution-system/01-task-breakdown/ (3 scripts)

| Script | Status | Execution Point | Notes |
|--------|--------|----------------|-------|
| `task-auto-analyzer.py` | **ACTIVE** | `3-level-flow.py` Step 3.1 | Automatic task breakdown + complexity analysis |
| `task-auto-tracker.py` | DAEMON | Not hook-compatible | Requires `watchdog` library + background process |
| `task-phase-enforcer.py` | ON-DEMAND | Manual CLI | Validates task/phase breakdown requirements |

#### 03-execution-system/02-plan-mode/ (2 scripts)

| Script | Status | Execution Point | Notes |
|--------|--------|----------------|-------|
| `auto-plan-mode-suggester.py` | **ACTIVE** | `3-level-flow.py` Step 3.2 | Decides if plan mode needed |
| `plan-mode-auto-decider.py` | PHASE-4 | Not ready | Phase-4: auto-enters plan mode without confirmation |

#### 03-execution-system/04-model-selection/ (4 scripts)

| Script | Status | Execution Point | Notes |
|--------|--------|----------------|-------|
| `model-auto-selector.py` | INLINE | `3-level-flow.py` Step 3.4 | Logic implemented inline in 3-level-flow.py |
| `intelligent-model-selector.py` | SUPERSEDED | - | Replaced by inline logic in 3-level-flow.py |
| `model-selection-monitor.py` | ON-DEMAND | Manual CLI | Monitors model usage distribution |
| `model-selection-enforcer.py` | ON-DEMAND | Manual CLI | Enforces model selection rules |

#### 03-execution-system/05-skill-agent-selection/ (4 scripts)

| Script | Status | Execution Point | Notes |
|--------|--------|----------------|-------|
| `auto-skill-agent-selector.py` | INLINE | `3-level-flow.py` Step 3.5 | Logic implemented inline in 3-level-flow.py |
| `skill-agent-auto-executor.py` | PHASE-4 | Not ready | Phase-4: auto-executes skills without confirmation |
| `auto-register-skills.py` | ON-DEMAND | Manual CLI | Scans and registers new skills |
| `core-skills-enforcer.py` | ON-DEMAND | Manual CLI | Enforces core skill execution order |

#### 03-execution-system/06-tool-optimization/ (6 scripts)

| Script | Status | Execution Point | Notes |
|--------|--------|----------------|-------|
| `tool-usage-optimizer.py` | **ACTIVE** | `pre-tool-enforcer.py` | Pre-execution token-saving optimizations |
| `smart-read.py` | ON-DEMAND | Manual CLI | Smart offset/limit strategies for Read |
| `pre-execution-optimizer.py` | ON-DEMAND | Manual CLI | Optimizes tool parameters before execution |
| `auto-tool-wrapper.py` | ON-DEMAND | Manual CLI | Cache check + optimization hints wrapper |
| `ast-code-navigator.py` | ON-DEMAND | Manual CLI | AST extraction (Java/TS/JS/Python) |
| `tool-call-interceptor.py` | PHASE-4 | Not ready | Phase-2: intercepts and rewrites tool calls |

#### 03-execution-system/07-recommendations/ (4 scripts)

| Script | Status | Execution Point | Notes |
|--------|--------|----------------|-------|
| `skill-detector.py` | ON-DEMAND | Manual CLI | Auto-suggests skills from keywords |
| `skill-auto-suggester.py` | DAEMON | Not hook-compatible | Requires background process |
| `check-recommendations.py` | ON-DEMAND | Manual CLI | Displays latest recommendations |
| `skill-manager.py` | ON-DEMAND | Manual CLI | CRUD interface for skill registry |

#### 03-execution-system/08-progress-tracking/ (1 script)

| Script | Status | Execution Point | Notes |
|--------|--------|----------------|-------|
| `check-incomplete-work.py` | **ACTIVE** | `post-tool-tracker.py` | Detects incomplete tasks on session resume |

#### 03-execution-system/09-git-commit/ (5 scripts)

| Script | Status | Execution Point | Notes |
|--------|--------|----------------|-------|
| `auto-commit-enforcer.py` | **ACTIVE** | `stop-notifier.py` | Enforces auto-commit on task completion |
| `auto-commit-detector.py` | ON-DEMAND | Manual CLI | Detects commit trigger conditions |
| `auto-commit.py` | ON-DEMAND | Manual CLI | Executes actual commit (calls detector) |
| `trigger-auto-commit.py` | ON-DEMAND | Manual CLI | Integration trigger for commit+push |
| `git-auto-commit-ai.py` | PHASE-4 | Not ready | Phase-4: AI-generated commit messages |

#### 03-execution-system/failure-prevention/ (8 scripts)

| Script | Status | Execution Point | Notes |
|--------|--------|----------------|-------|
| `pre-execution-checker.py` | **ACTIVE** | `3-level-flow.py` Step 3.7 | Pre-execution failure KB check |
| `failure-detector.py` | **ACTIVE** (v3.5.0) | `stop-notifier.py` session end | Analyzes failure patterns from logs |
| `windows-python-unicode-checker.py` | INLINE | `pre-tool-enforcer.py` L3.7 | Logic implemented inline in pre-tool-enforcer.py |
| `failure-solution-learner.py` | ON-DEMAND | Manual CLI | Learns solutions from successful fixes |
| `failure-pattern-extractor.py` | ON-DEMAND | Manual CLI | Extracts patterns from failure logs |
| `failure-learner.py` | ON-DEMAND | Manual CLI | Updates KB with learned solutions |
| `failure-detector-v2.py` | ON-DEMAND | Manual CLI | Enhanced failure detector with --analyze mode |
| `update-failure-kb.py` | ON-DEMAND | Manual CLI | Project-specific failure learning |

---

## Summary Statistics

| Status | Count | Description |
|--------|-------|-------------|
| **ACTIVE** (subprocess) | 16 | Called by hooks via subprocess.run |
| **INLINE** | 3 | Logic implemented directly in hook code |
| ON-DEMAND | 33 | CLI utilities for manual use |
| DAEMON | 3 | Requires background process (not hook-compatible) |
| PHASE-4 | 4 | Future automation stubs (not production-ready) |
| SUPERSEDED | 3 | Replaced by newer versions |
| **Total** | **65** | All scripts accounted for |

---

## Execution Order (Per Message)

### UserPromptSubmit Hook (runs first)
```
clear-session-handler.py
  -> session-loader.py                    [01-sync-system/session-management]

3-level-flow.py
  Level -1: auto-fix-enforcer.py          [scripts/ root]
  Level 1.1: context-monitor-v2.py        [01-sync-system/context-management]
  Level 1.2: session-id-generator.py      [scripts/ root]
  Level 1.3: load-preferences.py          [01-sync-system/user-preferences]    (NEW v3.5.0)
  Level 1.4: session-state.py             [01-sync-system/session-management]  (NEW v3.5.0)
  Level 2:   standards-loader.py          [02-standards-system]
  Step 3.0:  prompt-generator.py          [03-execution-system/00-prompt-generation]
  Step 3.1:  task-auto-analyzer.py        [03-execution-system/01-task-breakdown]
  Step 3.2:  auto-plan-mode-suggester.py  [03-execution-system/02-plan-mode]
  Step 3.3:  context-monitor-v2.py        [01-sync-system/context-management] (re-verify)
  Step 3.4:  INLINE model selection       (model-auto-selector.py logic)
  Step 3.5:  INLINE skill/agent selection (auto-skill-agent-selector.py logic)
  Step 3.5b: prompt-generator.py          [03-execution-system/00-prompt-generation] (with skill context)
  Step 3.6:  INLINE tool rules            (tool-usage-optimizer.py rules loaded)
  Step 3.7:  pre-execution-checker.py     [03-execution-system/failure-prevention]
  Step 3.8:  INLINE parallel analysis
  Steps 3.9-3.12: ACTIVE (logged)
```

### PreToolUse Hook (before each tool)
```
pre-tool-enforcer.py
  -> tool-usage-optimizer.py              [03-execution-system/06-tool-optimization]
  -> INLINE dynamic skill context         (per-file skill switching v3.0.0)
  -> INLINE unicode checker               (windows-python-unicode-checker.py logic)
```

### PostToolUse Hook (after each tool)
```
post-tool-tracker.py
  -> check-incomplete-work.py             [03-execution-system/08-progress-tracking]
  -> github_issue_manager.py              [scripts/ root] (on TaskCreate/TaskUpdate)
  -> auto_build_validator.py              [scripts/ root] (on TaskUpdate completed)
```

### Stop Hook (after each response)
```
stop-notifier.py
  -> auto-commit-enforcer.py              [03-execution-system/09-git-commit]
  -> auto-save-session.py                 [01-sync-system/session-management]   (NEW v3.5.0)
  -> archive-old-sessions.py              [01-sync-system/session-management]   (NEW v3.5.0)
  -> failure-detector.py                  [03-execution-system/failure-prevention] (NEW v3.5.0)
  -> github_pr_workflow.py                [scripts/ root] (on .session-work-done)
  -> session-summary-manager.py           [scripts/ root]
```

---

## Why Some Scripts Are NOT in Hooks

### Daemons (3)
These require long-running background processes with file watchers:
- `preference-auto-tracker.py` - Monitors logs continuously
- `task-auto-tracker.py` - Uses `watchdog` library for file monitoring
- `skill-auto-suggester.py` - Monitors conversation logs continuously

### Phase-4 Stubs (4)
Future automation scripts not yet production-ready:
- `prompt-auto-wrapper.py` - Auto-generates structured prompts
- `plan-mode-auto-decider.py` - Auto-enters plan mode
- `skill-agent-auto-executor.py` - Auto-executes skills
- `tool-call-interceptor.py` - Intercepts and rewrites tool calls

### On-Demand Utilities (33)
CLI tools meant for manual/targeted use:
- Context management utilities (cleanup, caching, summarization)
- Failure analysis and learning tools
- Skill/agent registry management
- Session search and maintenance
- Git commit helpers

### Superseded (3)
Replaced by newer/inline versions:
- `context-monitor.py` -> `context-monitor-v2.py`
- `context-estimator.py` -> `context-monitor-v2.py`
- `intelligent-model-selector.py` -> inline in 3-level-flow.py

---

## Version History

- **v1.0.0** (2026-02-28): Initial mapping - audit of all 65 scripts
  - 16 ACTIVE via subprocess
  - 3 INLINE in hook code
  - 33 ON-DEMAND utilities
  - 3 DAEMON (not hook-compatible)
  - 4 PHASE-4 stubs
  - 3 SUPERSEDED

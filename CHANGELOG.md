# Changelog

All notable changes to Claude Insight will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

---

## [3.8.0] - 2026-02-23

### Added
- **Session Chaining System** - Track parent/child/related session relationships
  - New policy: `policies/01-sync-system/session-management/session-chaining-policy.md`
  - New script: `scripts/session-chain-manager.py` (7 CLI commands: link, tag, relate, context, chain, search, auto-tag)
  - New script: `scripts/session-summary-manager.py` (accumulate, finalize, read)
  - Integration: 3-level-flow.py auto-tags sessions and loads chain context
  - Integration: clear-session-handler.py finalizes summaries and links sessions on /clear
- **02-standards-system policies** - Added missing standards system folder
  - `policies/02-standards-system/coding-standards-enforcement-policy.md`
  - `policies/02-standards-system/README.md`
- **Parallel execution policy** in organized structure (`03-execution-system/`)

### Changed
- **Updated scripts** synced from global system:
  - `3-level-flow.py` - Added session chaining + summary accumulation
  - `clear-session-handler.py` - Added session finalize + chain linking
  - `pre-tool-enforcer.py` - Loophole fixes (19 loopholes hardened)
  - `post-tool-tracker.py` - Content-aware progress tracking
  - `stop-notifier.py` - LLM-powered dynamic voice notifications

### Removed
- **14 duplicate flat policy files** from `policies/` root - all policies now ONLY in organized sub-folders (01-sync-system, 02-standards-system, 03-execution-system, testing)
- **`nul` file** (Windows artifact cleanup)

### Fixed
- Policy structure: Eliminated duplicate flat + organized coexistence; single organized structure now

---

## [3.7.2] - 2026-02-22

### Fixed
- **Root cause: Claude Insight sync was not enforced as part of task completion**
  - Problem: CLAUDE.md had auto-sync rule but no hard enforcement — Claude could skip it
  - Root cause: Sync was treated as "afterthought", not part of the task itself
  - Fix: Added mandatory sync checklist to `git-auto-commit-policy.md` (v1.1.0 → v1.2.0)
  - Fix: Added same checklist to `~/.claude/CLAUDE.md` Step 3.11
  - New rule: Before `TaskUpdate(completed)` → MUST check if Claude Insight needs sync
  - Violation = incomplete task = re-open and sync first

---

## [3.7.1] - 2026-02-22

### Fixed
- **Step 3.11 Git Auto-Commit Timing Problem** — Stop hook was too aggressive
  - Problem: Stop hook fires after EVERY response, causing partial/mid-work commits
  - Root cause: "Phase complete" is semantic knowledge only Claude has; hook has no context
  - Fix: Git commit now triggers on `TaskUpdate(status=completed)` on LAST task of phase
  - Why tasks work: Task completion = perfect timing signal; Claude tracks it, can't forget
  - Updated: `policies/git-auto-commit-policy.md` (v1.0.0 → v1.1.0)
  - Updated: `~/.claude/CLAUDE.md` Step 3.11 rule
  - System version bumped: v3.7.7 → v3.7.8

---

## [3.7.0] - 2026-02-22

### Changed
- **Always-Task Policy (v2.0.0)** — Task breakdown no longer complexity-based
  - Every coding/implementation request now creates minimum 1 TaskCreate
  - Phase trigger changed: 5+ tasks = use phases (was: complexity >= 10)
  - Purpose: Policy visibility — user can see policies running every request
  - Updated: `policies/task-phase-enforcement-policy.md`
  - Updated: `policies/03-execution-system/01-task-breakdown/automatic-task-breakdown-policy.md`
  - Updated: `policies/03-execution-system/01-task-breakdown/task-phase-enforcer.py`

---

## [3.6.0] - 2026-02-22

### Added
- **PreToolUse hook: `pre-tool-enforcer.py`** (Level 3.6 + 3.7)
  - Runs BEFORE every tool call in Claude Code
  - Exit 0 = allow (with optional optimization hints to stdout)
  - Exit 1 = BLOCK tool call (prints reason to stderr)
  - Level 3.6 hints (non-blocking): Grep without `head_limit`, Read without `offset+limit`
  - Level 3.7 blocks: Windows-only commands in Bash (del, copy, dir, xcopy, ren, md, etc.)
  - Level 3.7 blocks: Unicode characters in Python files on Windows (cp1252 crash prevention)

- **PostToolUse hook: `post-tool-tracker.py`** (Level 3.9)
  - Runs AFTER every tool call (always exits 0, never blocks)
  - Logs to `~/.claude/memory/logs/tool-tracker.jsonl`
  - Updates `~/.claude/memory/logs/session-progress.json`
  - Progress deltas per tool: Read +10%, Write +40%, Edit +30%, Bash +15%, Task +20%, Grep/Glob +5%

### Updated
- **README.md** - "How the Hooks Work" section completely rewritten
  - Now shows all 4 hook types: UserPromptSubmit, PreToolUse, PostToolUse, Stop
  - Full `~/.claude/settings.json` example with all 4 hooks
  - Detailed explanation of what each hook does and how blocking works
- **CLAUDE.md** - Manual setup instructions updated
  - Added step to copy `pre-tool-enforcer.py` and `post-tool-tracker.py`
  - Added PreToolUse and PostToolUse to settings.json example
  - Added hook type summary table
- **`scripts/setup-global-claude.sh`** - Added 4 missing scripts to SCRIPTS_TO_COPY
  - Now copies: `clear-session-handler.py`, `stop-notifier.py`, `pre-tool-enforcer.py`, `post-tool-tracker.py`
  - settings.json creation now includes all 4 hook types
- **`scripts/setup-global-claude.ps1`** - Added 2 missing scripts to $scriptsToCopy
  - Now copies: `pre-tool-enforcer.py`, `post-tool-tracker.py`
  - settings.json creation now includes all 4 hook types
  - Added warning when existing settings.json is missing PreToolUse hooks

---

## [3.5.0] - 2026-02-19

### Fixed
- **Comprehensive flow-trace data source migration for 5 monitoring services**
  - All services now read from `flow-trace.json` (real data) instead of
    non-existent log files, PID files, and policy-hits.log keyword mismatches

- **`skill_agent_tracker.py`** (3 methods):
  - `get_skill_selection_stats()`: reads `LEVEL_3_STEP_3_5.policy_output.selected_name`
    (selected_type=skill) from flow-traces - now shows 50 real skill usages
  - `get_agent_usage_stats()`: reads `selected_type=agent` from flow-traces -
    now shows 12 real agent usages (ui-ux-designer, orchestrator-agent, etc.)
  - `get_plan_mode_suggestions()`: reads `final_decision.plan_mode` and
    `complexity` from flow-traces - now shows real complexity distribution

- **`memory_system_monitor.py`** (3 methods):
  - `get_daemon_status()`: replaced dead PID file checks with hook script
    presence checks (daemons removed in v3.3.0, hooks are the new enforcement)
  - `get_system_health_score()`: hooks-based formula (60pts + 20pts + 20pts)
    instead of daemon-based (always 0) - now returns real 100% health
  - `get_model_selection_distribution()`: reads `final_decision.model_selected`
    from flow-traces - now shows 96.8% Haiku, 3.2% Sonnet

- **`optimization_tracker.py`** (2 methods):
  - `get_tool_optimization_metrics()`: derives strategy counts from flow-trace
    `context_pct`, `complexity`, `execution_mode` - now shows 421 optimizations,
    148K tokens saved estimate
  - `get_standards_enforcement_stats()`: reads `final_decision.standards_active`
    and `rules_active` from flow-traces - now shows 14 standards, 89 rules avg

- **`policy_execution_tracker.py`** (2 methods):
  - `get_enforcer_state()`: derives step completion from most recent flow-trace
    pipeline steps (LEVEL_1_SESSION, LEVEL_2_STANDARDS, LEVEL_3_STEP_3_4, etc.)
  - `parse_policy_log()`: primary source now flow-trace pipeline steps mapped to
    policy categories; policy-hits.log kept as supplementary source (90K daemon
    entries provide real background enforcement data)

- **`automation_tracker.py`** (2 methods):
  - `get_session_start_recommendations()`: derives from most recent flow-trace
    `final_decision` (model, context %, standards count, tech_stack, skill/agent)
  - `get_task_breakdown_stats()`: reads `final_decision.task_count` and
    `complexity` from all sessions with bucketed distribution

---

## [3.4.0] - 2026-02-18

### Added
- **`scripts/3-level-flow.py`** v3.0.0: Complete 3-level architecture hook script with full JSON trace
  - All 17 steps logged A-to-Z (Level -1, Level 1, Level 2, Level 3 with 12 execution steps)
  - **4-layer dynamic skill/agent selection** at Step 3.5:
    - L1: Task-type exact match (`TASK_TYPE_TO_AGENT` registry — covers 30+ task types)
    - L2: Prompt keyword scoring — dynamic analysis of raw user message (no API calls)
    - L3: Tech stack file detection (reads `pom.xml`, `package.json`, `Dockerfile`, etc.)
    - L4: `adaptive-skill-intelligence` — creates new skill on-the-fly if nothing matches
  - Orchestrator escalation guard: L1 task-type matches never overridden by escalation
  - Review checkpoint (`CLAUDE_MUST`) output before coding starts
  - Windows-safe encoding (ASCII only, cp1252 compatible)
  - Install: `cp scripts/3-level-flow.py ~/.claude/memory/current/`

### Fixed
- **Orchestrator escalation threshold**: Raised from `task_count > 3` to `task_count > 8`;
  L1-matched task types (e.g. Dashboard, UI/UX) are now protected from being overridden
  by the orchestrator escalation rule

---

## [3.3.6] - 2026-02-18

### Fixed
- **`scripts/session-start.sh`**: Step 3 was calling `daemon-manager.py --status-all` which
  no longer exists (daemons removed in v3.3.0). Replaced with hooks status check that
  verifies 3 hook scripts (`3-level-flow.py`, `clear-session-handler.py`, `stop-notifier.py`)
  are present in `current/` directory
- **`src/services/monitoring/automation_tracker.py`**: Removed `daemon_9` key from
  `get_comprehensive_automation_stats()` return dict (the 9th daemon was removed in v3.3.0)

---

## [3.3.5] - 2026-02-18

### Fixed
- **Removed all daemon references from HTML templates (10 files)**
  - `dashboard.html`: "Daemons Running" stat card -> "Hooks Active" (shows 2 active hooks);
    daemon JS update logic -> static hooks display; widget IDs renamed `daemon_status` -> `hooks_status`;
    tooltip text updated; informational text updated
  - `debugging-tools.html`: removed "Daemons" dropdown option; removed entire `daemonsSection` div
    (Daemon Health Diagnostics); replaced "Restart All Daemons" button with "View Hooks Status";
    replaced `restartDaemons()` JS with `viewHooksStatus()` that shows settings.json path; removed
    daemon CSS classes (`.daemon-card`, `.daemon-stats`, `.daemon-actions`)
  - `analytics.html`: "Daemon Uptime" metric -> "Hooks Active" (static value 2)
  - `advanced-search.html`: removed "Daemons" search filter option; updated placeholder text
  - `settings.html`: "Daemon Down" alert condition -> "Hook Failure" (3 occurrences)
  - `widget-builder.html`: removed `/api/daemon-status` data source option
  - `notification-channels.html`: "Daemon Down" trigger -> "Hook Failure"
  - `dashboard-builder.html`: "Daemon Status"/"Daemon Health" widget types -> "Hooks Active"/"Policy Status"
  - `500.html`: daemon troubleshooting tip -> hooks troubleshooting tip
  - `integrations.html`: `daemon_status` metric -> `hooks_active`; "daemons" -> "hooks"

---

## [3.3.1] - 2026-02-18

### Fixed
- **Removed dead daemon API routes from `app.py`**
  - Removed `POST /api/daemon/restart/<daemon_name>` (called removed daemon-manager.py)
  - Removed `GET /api/debug/daemons/health` (returned simulated PID data, no real daemons)
  - Removed `GET /api/automation/daemon-9-status` (daemon-9 removed in v3.3.0)

- **Removed outdated test cases**
  - Deleted `tests/test-monitoring.py` (manual script testing removed daemon APIs)
  - Removed `test_get_system_health_success`, `test_get_system_health_degraded`, `test_get_daemon_status` from `tests/test_monitoring_services.py`
  - Removed `test_log_daemon_activity` from `tests/test_enforcement_logger.py`

- **Fixed `three_level_flow_tracker.py` model field parsing**
  - `_parse_flow_trace_json()` was reading `fd.get('model')` but global system writes `model_selected`
  - Fixed to `fd.get('model_selected')` so model field is correctly populated in session history

- **Fixed `metrics_collector.py` paths and dead methods**
  - Fixed context-monitor path: `memory_dir/context-monitor-v2.py` -> `memory_dir/current/context-monitor-v2.py`
  - Removed dead `restart_daemon()` method (called non-existent daemon-manager.py)
  - Removed dead `get_failure_kb_stats()` method (called pre-execution-checker.py at wrong path)

- **Fixed `memory_system_monitor.py` multiple path/logic bugs**
  - Fixed `failures.log` path: `memory_dir/failures.log` -> `logs_dir/failures.log`
  - Fixed `get_session_memory_stats()`: now reads `logs/sessions/` (contains SESSION-* dirs with flow-trace.json) instead of `sessions/` (state files only)
  - Fixed `get_session_memory_stats()`: checks `flow-trace.json` for active status instead of non-existent `project-summary.md`
  - Fixed all 10 policy file paths in `get_policy_status()` from memory root to correct 3-level subdirectory paths

- **Fixed `policy_checker.py` daemon infrastructure remnants**
  - Removed `daemon-infrastructure` policy entry (referenced non-existent `utilities/daemon-manager.py` and `utilities/pid-tracker.py`)
  - Removed `if policy['id'] == 'daemon-infrastructure'` check block
  - Removed `_check_daemons()` method
  - Fixed `_get_kb_stats()` subprocess path to correct `03-execution-system/failure-prevention/pre-execution-checker.py`
  - Removed `'daemon': 'daemon-infrastructure'` mapping from `_map_daemon_to_policy_id()`
  - Removed unused `MemorySystemMonitor` import from `__init__`

- **Fixed template 404 calls**
  - `automation-dashboard.html`: removed "9th Daemon Status" card and `loadDaemon9()`/`renderDaemon9()` JS functions
  - `debugging-tools.html`: removed "Daemon Health" card and `loadDaemonHealth()`/`displayDaemonHealth()`/`refreshDaemonHealth()`/`restartDaemon()`/`viewDaemonLogs()` JS functions

---

## [3.3.0] - 2026-02-18

### Added
- **Comprehensive Documentation Policy v2.0**
  - Added `scripts/comprehensive-docs-checker.py` - Auto-check, auto-create, and auto-update documentation
  - Minimum 50 lines requirement with required sections
  - Auto-creates missing README.md and CLAUDE.md in all git repos
  - Auto-updates non-comprehensive files (preserves .backup)
  - Flexible section matching (PROJECT/SERVICE/APPLICATION OVERVIEW accepted)

- **3-Level Flow Display System**
  - Added `test-complete-execution-flow.sh` - Complete 3-level architecture test
  - Shows all 17 steps (Level -1, Level 1, Level 2, Level 3 with 12 execution steps)
  - Mandatory display before every request for transparency
  - User-configurable TRACE_MODE flag

- **True Automation System**
  - Added `auto-enforce-all-policies.sh` - All-in-one automatic policy enforcement
  - Added `install-auto-hooks.sh` - Auto-hooks installer for pre-request execution
  - Policies now run automatically before every request (no manual intervention)
  - Blocking mode: policies must pass before response

- **Per-Request Policy Enforcement**
  - Added `per-request-enforcer.py` - Continuous policy enforcement system
  - Policies run before EVERY user request (not just session start)
  - Per-request state tracking with completion markers
  - Final check before responding to user

### Changed
- **Documentation Standards** - Updated to v2.0.0 with auto-enforcement
- **Auto-Fix Enforcement** - Enhanced with more comprehensive checks
- **Production Infrastructure** - New documentation for VPS/K8s/Three-Tier Routing

### Documentation
- Updated `docs/documentation-standards.md` to v2.0.0
- Added `docs/production-infrastructure.md` with VPS setup details
- Updated `docs/auto-fix-enforcement.md` with latest policies

---

## [2.7.0] - 2026-02-17

### Added
- **Complete Daemon Management System**
  - Added `daemon-manager.py` - Comprehensive daemon lifecycle management for all 10 daemons
  - Added `health-monitor-daemon.py` - Auto-restart monitor for dead daemons (checks every 5 min)
  - Added `daemon-logger.py` - Centralized daemon logging system
  - Added `pid-tracker.py` - Process ID tracking and management
  - All utilities added to `src/utils/` for easy access

- **Enhanced Daemon Support**
  - Now manages 10 core daemons (upgraded from 8-9)
  - Added `token-optimization-daemon` - Auto-optimizes context when >85%
  - Added `health-monitor-daemon` - Auto-restarts dead daemons
  - Removed non-existent `auto-recommendation-daemon`

- **Cross-Platform Daemon Management**
  - Windows, Linux, Mac support
  - Auto-start on system login
  - JSON status API for dashboard integration
  - Real-time daemon health monitoring

### Changed
- **daemon-manager.py** - Updated with correct subdirectory paths for all daemon scripts
- **health-monitor-daemon.py** - Fixed import paths to use `utilities/` subdirectory
- All daemon scripts now properly reference their actual locations
- Documentation updated with complete daemon system details

### Fixed
- Fixed daemon-manager.py looking for scripts in wrong directories
- Fixed health-monitor-daemon.py import errors (daemon-logger.py, pid-tracker.py, daemon-manager.py)
- Fixed missing daemon paths causing startup failures
- All 10 daemons now start and run correctly with auto-restart capability

### Documentation
- Updated README.md with daemon management system details
- Updated CLAUDE.md with complete daemon information
- Added daemon utilities documentation
- Added changelog entry for v2.7.0

---

## [2.5.2] - 2026-02-16

### Bug
- Bug fixes and minor improvements

---

## [2.5.1] - 2026-02-16

### Added
- **Automatic Versioning System**
  - VERSION file for semantic versioning
  - Version display in navbar
  - `bump-version.py` script for version management
  - `bump-version.sh` wrapper with auto-commit, tag, push, release
  - Automatic GitHub release creation using gh CLI

- **Portability Improvements**
  - PathResolver utility for smart path detection
  - Support for both Global mode (`~/.claude/memory`) and Local mode (`./data/`)
  - Auto-creation of local data directory structure
  - Batch path fixer script (`fix-paths.py`)

### Changed
- Updated 18 service files to use PathResolver instead of hardcoded paths
- Repository description updated to reflect v2.5+ features
- Removed GitHub Actions dependency (using gh CLI directly)

### Fixed
- Fixed all hardcoded `~/.claude/memory` paths for portability
- Fixed session-start.sh daemon status checking using daemon-manager.py
- Fixed Unicode encoding errors in various scripts

---

## [2.5.0] - 2026-02-15

### Added
- **Claude/Anthropic API Integration**
  - Secure credential storage with Fernet encryption
  - API key validation and connection testing
  - Auto-tracking enable/disable with configurable intervals
  - Manual session sync capability
  - Setup instructions with Anthropic Console links

- **Session Search Feature**
  - Search sessions by ID
  - Search sessions by date
  - View complete session details ("chittha")
  - Session timeline visualization
  - Work items tracking

### Changed
- Updated navigation with Session Search and Claude API links
- Added cryptography, requests, and pyotp dependencies

---

## [2.4.0] - 2026-02-15

### Added
- Migration Skill & Migration Expert Agent
- GitHub CLI (`gh`) mandatory enforcement for all GitHub operations

---

## [2.3.0] - 2026-02-10

### Changed
- Restored active enforcement mode
- Enhanced policy execution

---

## [2.2.0] - 2026-02-09

### Added
- Initial Claude Memory System integration
- Real-time monitoring capabilities
- Cost comparison features
- Session tracking

---

## Links

- [Repository](https://github.com/piyushmakhija28/claude-insight)
- [Issues](https://github.com/piyushmakhija28/claude-insight/issues)
- [Releases](https://github.com/piyushmakhija28/claude-insight/releases)

---

**Legend:**
- `Added` - New features
- `Changed` - Changes in existing functionality
- `Deprecated` - Soon-to-be removed features
- `Removed` - Removed features
- `Fixed` - Bug fixes
- `Security` - Security improvements

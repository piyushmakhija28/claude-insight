# Claude Insight v3.8.0

**Real-time Monitoring Dashboard for the Claude Memory System (3-Level Architecture)**

[![GitHub](https://img.shields.io/badge/GitHub-claude--insight-blue?logo=github)](https://github.com/piyushmakhija28/claude-insight)
[![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0-green?logo=flask)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Version](https://img.shields.io/badge/Version-3.8.0-brightgreen)](CHANGELOG.md)

Claude Insight is a Python Flask dashboard that monitors how Claude Code follows the
**3-Level Architecture enforcement policies** in real-time. Track policy execution,
session analytics, skill/agent usage, context optimization, and AI-powered anomaly
detection — all from one interface.

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Quick Start](#quick-start)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Memory System Setup](#memory-system-setup)
  - [Running the Dashboard](#running-the-dashboard)
- [The 3-Level Architecture](#the-3-level-architecture)
  - [Level -1: Auto-Fix Enforcement](#level--1-auto-fix-enforcement)
  - [Level 1: Sync System](#level-1-sync-system)
  - [Level 2: Standards System](#level-2-standards-system)
  - [Level 3: Execution System](#level-3-execution-system)
- [How the Hooks Work](#how-the-hooks-work)
- [Session Management: Our Custom System vs Claude Native](#session-management-our-custom-system-vs-claude-native)
  - [What Makes Our Session System Different?](#what-makes-our-session-system-different)
  - [Key Benefits](#key-benefits)
- [Dashboard Pages](#dashboard-pages)
- [Project Structure](#project-structure)
- [API Reference](#api-reference)
- [Configuration](#configuration)
- [Global vs Project CLAUDE.md](#global-vs-project-claudemd)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [Changelog](#changelog)
- [License](#license)

---

## Overview

### What Is Claude Insight?

Claude Insight provides visibility into the Claude Memory System — a policy enforcement
framework that runs inside Claude Code. The memory system uses a **3-level architecture**
to ensure Claude always follows coding standards, picks the right skills/agents, and
manages context efficiently.

**The problem it solves:** Without monitoring, you cannot tell if Claude is following
your enforcement policies, which model it selected, how much context it consumed, or
whether it invoked the correct skill for a task.

**Claude Insight shows you all of this in real-time.**

### How It Works

```
Claude Code (your IDE)
       |
       | Every message triggers:
       v
UserPromptSubmit Hook
       |
       v
3-level-flow.py --summary
  [Level -1] Auto-Fix Enforcement
  [Level 1]  Sync System (Context + Session)
  [Level 2]  Standards + Skill Selection
  [Level 3]  12-Step Execution
       |
       | Writes to:
       v
~/.claude/memory/logs/
       |
       | Read by:
       v
Claude Insight Dashboard (Flask)
       |
       v
Real-time charts, analytics, alerts
```

---

## Features

### Core Monitoring

| Feature | Description |
|---------|-------------|
| **3-Level Flow Tracker** | Shows each Level (-1, 1, 2, 3) execution per session |
| **Policy Execution Tracker** | Which policies ran, pass/fail per request |
| **Session Analytics** | Session duration, requests per session, context usage |
| **Session Chaining** | Parent/child session relationships, tag-based linking, cross-session summaries |
| **Skill/Agent Usage** | Which skills and agents were invoked and how often |
| **Context Monitoring** | Context % per request, optimization actions taken |
| **Model Selection Tracking** | Haiku/Sonnet/Opus distribution across requests |

### AI-Powered Analytics

| Feature | Description |
|---------|-------------|
| **Anomaly Detection** | Detects unusual patterns (context spikes, policy failures) |
| **Predictive Analytics** | Forecasts context usage and session patterns |
| **Bottleneck Analysis** | Identifies slow steps in the 3-level flow |
| **Performance Profiling** | Response time analysis per step |

### Alerting & Notifications

| Feature | Description |
|---------|-------------|
| **Alert Routing** | Multi-level alert escalation |
| **Multi-channel Notifications** | Email, Slack, webhook support |
| **Custom Alert Rules** | Define thresholds for any metric |
| **Real-time Alerts** | WebSocket-based instant notifications |

### Dashboard Capabilities

| Feature | Description |
|---------|-------------|
| **Real-time Updates** | Live data via WebSocket (SocketIO) |
| **Session Search** | Search and filter session history |
| **Export Options** | CSV, Excel, PDF report generation |
| **Multi-language** | EN, HI, ES, FR, DE support |
| **Custom Dashboard Builder** | Build personalized metric views |
| **Dark/Light Themes** | Multiple UI themes |

---

## Quick Start

### Prerequisites

- Python 3.8+
- Claude Code installed (`npm install -g @anthropic-ai/claude-code`)
- Git

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/piyushmakhija28/claude-insight.git
cd claude-insight

# 2. Create virtual environment (recommended)
python -m venv venv

# Activate on Windows:
venv\Scripts\activate

# Activate on Unix/macOS:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt
```

### Memory System Setup

The dashboard reads logs from `~/.claude/memory/`. You need to install the
3-level architecture hooks first.

**Option A — Automatic (Recommended):**

Windows (PowerShell):
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\scripts\setup-global-claude.ps1
```

Unix / macOS / WSL:
```bash
chmod +x scripts/setup-global-claude.sh
./scripts/setup-global-claude.sh
```

The setup script will:
1. Create `~/.claude/memory/current/` with enforcement scripts
2. Install hooks in `~/.claude/settings.json`
3. Install the global CLAUDE.md (3-level architecture, no project-specific info)

**Option B — Manual:**

See [CLAUDE.md](CLAUDE.md) for step-by-step manual setup instructions.

**Verify setup is working:**

After restarting Claude Code, send any message. You should see:
```
[LEVEL -1] AUTO-FIX ENFORCEMENT (BLOCKING)  [OK]
[LEVEL 1] SYNC SYSTEM                        [OK] Context: XX% | Session: SESSION-...
[LEVEL 2] STANDARDS SYSTEM                   [OK] 15 standards, 156 rules loaded
[LEVEL 3] EXECUTION SYSTEM (12 steps)        [OK] All steps verified
```

### Running the Dashboard

```bash
# Start the Flask server (default port 5000)
python run.py

# Custom port
python run.py --port 8080
```

Open http://localhost:5000 in your browser.

**Default credentials:**
- Username: `admin`
- Password: `admin`

> Change these in `src/auth/user_manager.py` before deploying.

---

## The 3-Level Architecture

The 3-level architecture runs automatically on every Claude Code request via hooks.
Here is what each level does:

### Level -1: Auto-Fix Enforcement

**Runs first. Blocks all work if any critical check fails.**

```
7 System Checks:
  [1/7] Python availability          -> CRITICAL
  [2/7] Critical files present       -> CRITICAL
  [3/7] Blocking enforcer state      -> CRITICAL (auto-fix capable)
  [4/7] Session state valid          -> HIGH
  [5/7] Background daemon status     -> INFO only
  [6/7] Git repository state         -> INFO only
  [7/7] Windows Python Unicode check -> CRITICAL on Windows
```

Exit code 0 = proceed. Exit code != 0 = all work stops.

### Level 1: Sync System

**Context, session management, and session chaining.**

- Context monitoring (checks usage %, applies optimization if >70%)
- Session ID generation (format: `SESSION-YYYYMMDD-HHMMSS-XXXX`)
- Loads previous session state if exists
- **Session Chaining** - Links sessions in parent/child relationships with auto-tagging
- **Session Summaries** - Accumulates per-request data, generates summaries on `/clear`

### Level 2: Standards System

**Loads 15 coding standards (156 rules) and selects the correct skill/agent.**

Standards loaded:
1. Project structure (packages, visibility)
2. Config management (externalize all config)
3. Secret management (never hardcode)
4. Response format standards
5. Service layer patterns
6. Entity/model patterns
7. Controller patterns
8. Constants organization
9. Common utilities
10. Error handling
11. API design (REST)
12. Database standards
13. Documentation (README + CLAUDE.md per repo)
14. Kubernetes network policies
15. K8s/Docker/Jenkins Infrastructure Standards (K8s archetypes, Dockerfile templates, Jenkins pipelines)

**Skill/Agent selection** happens here — Claude matches the task to the correct skill
(e.g., JavaFX task → `javafx-ide-designer`, Spring Boot task → `java-spring-boot-microservices`).

### Level 3: Execution System

**12 mandatory steps before implementation:**

| Step | Name | Purpose |
|------|------|---------|
| 3.0 | Prompt Generation | Anti-hallucination, verify examples from codebase |
| 3.1 | Task Breakdown | Create tasks with dependencies |
| 3.2 | Plan Mode Decision | Score 0-4: direct, 5-9: ask, 10+: plan mode |
| 3.3 | Context Check | Re-verify, apply optimizations |
| 3.4 | Model Selection | Haiku/Sonnet/Opus based on complexity |
| 3.5 | Skill/Agent Selection | Invoke matched skill via Skill tool |
| 3.6 | Tool Optimization | offset/limit on Read, head_limit on Grep |
| 3.7 | Failure Prevention | Pre-execution checks, auto-fixes |
| 3.8 | Parallel Analysis | Detect parallel execution opportunities |
| 3.9 | Execute Tasks | Auto-track progress |
| 3.10 | Session Save | Save state at milestones |
| 3.11 | Git Auto-Commit | Commit on phase completion |
| 3.12 | Logging | Log all policy applications |

---

## How the Hooks Work

The hooks are configured in `~/.claude/settings.json` and run automatically.
There are **4 hook types**, each enforcing different levels of the architecture:

| Hook Type | Trigger | Scripts | Levels Enforced |
|-----------|---------|---------|-----------------|
| `UserPromptSubmit` | Every new user message | `clear-session-handler.py` + `3-level-flow.py` | Level -1, 1, 2, 3 |
| `PreToolUse` | Before every tool call | `pre-tool-enforcer.py` | Level 3.6 (optimization hints) + 3.7 (blocking) |
| `PostToolUse` | After every tool call | `post-tool-tracker.py` | Level 3.9 (progress tracking) |
| `Stop` | After every Claude response | `stop-notifier.py` | Level 3.10 (session save + voice notification) |

**Complete `~/.claude/settings.json`:**

```json
{
  "model": "sonnet",
  "hooks": {
    "UserPromptSubmit": [{
      "hooks": [
        {
          "type": "command",
          "command": "python ~/.claude/memory/current/clear-session-handler.py",
          "timeout": 15,
          "statusMessage": "Level 1: Checking session state..."
        },
        {
          "type": "command",
          "command": "python ~/.claude/memory/current/3-level-flow.py --summary",
          "timeout": 30,
          "statusMessage": "Level -1/1/2/3: Running 3-level architecture check..."
        }
      ]
    }],
    "PreToolUse": [{
      "hooks": [{
        "type": "command",
        "command": "python ~/.claude/memory/current/pre-tool-enforcer.py",
        "timeout": 10,
        "statusMessage": "Level 3.6/3.7: Tool optimization + failure prevention..."
      }]
    }],
    "PostToolUse": [{
      "hooks": [{
        "type": "command",
        "command": "python ~/.claude/memory/current/post-tool-tracker.py",
        "timeout": 10,
        "statusMessage": "Level 3.9: Tracking task progress..."
      }]
    }],
    "Stop": [{
      "hooks": [{
        "type": "command",
        "command": "python ~/.claude/memory/current/stop-notifier.py",
        "timeout": 20,
        "statusMessage": "Level 3.10: Session save + voice notification..."
      }]
    }]
  }
}
```

### What Each Hook Does

**`UserPromptSubmit` → `clear-session-handler.py` + `3-level-flow.py`**
- Detects `/clear` command and saves old session, starts new one
- On `/clear`: finalizes session summary, links new session as child of old session
- Runs the full 3-level architecture check (Level -1 through Level 3 all 12 steps)
- Auto-tags sessions with keywords from prompt, skill, task type, and project
- Accumulates per-request summary data for session summaries
- Writes `flow-trace.json` to the session log folder
- Claude Insight reads this file for all its monitoring data

**`PreToolUse` → `pre-tool-enforcer.py`**
- Runs BEFORE every tool call (Read, Write, Edit, Bash, Grep, etc.)
- Exit 0 = allow tool (may print optimization hints to stdout for Claude to see)
- Exit 1 = BLOCK tool (prints reason to stderr, tool call is cancelled)
- **Level 3.6 hints (non-blocking):** Grep without `head_limit`, Read without `offset+limit`
- **Level 3.7 blocks (blocking):** Windows commands in Bash (del, copy, dir, xcopy...), Unicode characters in Python files on Windows

**`PostToolUse` → `post-tool-tracker.py`**
- Runs AFTER every tool call (always exits 0, never blocks)
- Logs to `~/.claude/memory/logs/tool-tracker.jsonl`
- Updates `~/.claude/memory/logs/session-progress.json`
- Progress deltas: Read +10%, Write +40%, Edit +30%, Bash +15%, Task +20%, Grep/Glob +5%

**`Stop` → `stop-notifier.py`**
- Runs after every Claude response completes
- Saves session state to `~/.claude/memory/logs/`
- Triggers Hinglish voice notification (if `~/.claude/.session-work-done` flag exists)

**No background daemons.** Everything runs per-request via hooks. When you send
a message in Claude Code, the hooks fire, run the 3-level flow, write results to
`~/.claude/memory/logs/`, and Claude Insight reads those logs.

---

## Session Management: Our Custom System vs Claude Native

### What Makes Our Session System Different?

Claude Code has built-in session management at the IDE level (per conversation window).
We've built an **advanced session system** that goes beyond IDE limitations:

| Feature | Claude Native | Our System |
|---------|---|---|
| **Persistence** | Lost on IDE close | Saved forever in `~/.claude/memory/sessions/` |
| **Continuity** | Resets after `/clear` | Auto-chains sessions with parent/child links |
| **Multi-Window** | Conflicts (shared state) | PID-based isolation (no conflicts) |
| **Context Awareness** | Single window | Project-based + cross-session |
| **Session Summaries** | None | Auto-generated with metrics |
| **Session Tagging** | None | Tag-based organization (spring-boot, devops, etc.) |
| **History Access** | Manual scrolling | Queryable database + Claude Insight dashboard |
| **Parallel Work** | Not supported | Supported with isolation |

### Key Benefits

**1. Never Lose Work**
- All sessions automatically saved
- Recoverable after IDE restart
- Complete audit trail
- Historical comparison

**2. Cross-Session Continuity**
- Sessions chained automatically after `/clear`
- Claude loads previous context automatically
- Related work discovered by tags
- Project-level awareness

**3. Multi-Window Support**
- Each window uses isolated state file (`~/.claude/.hook-state-{PID}.json`)
- Work simultaneously without conflicts
- No context mixing between windows
- Clean separation per process

**4. Advanced Analytics**
- Track time per task type
- Measure context usage trends
- Identify skill preferences
- Learn from past approaches

### Session Storage

```
~/.claude/memory/sessions/
├─ SESSION-20260224-130424-IQAV/
│  ├─ flow-trace.json              # Complete 12-step execution
│  ├─ session-summary.json         # Auto-generated summary
│  ├─ task-metadata.json           # Task tracking
│  └─ context-metrics.json         # Token usage
│
└─ chain-index.json                # Session relationships
   {
     "SESSION-20260224-130424-IQAV": {
       "parent": "SESSION-20260223-151000",
       "children": [...],
       "tags": ["spring-boot", "monitoring", "k8s"]
     }
   }
```

### How Sessions Are Tracked

```
User says "/clear" in Claude Code
    ↓
clear-session-handler.py fires
    ↓
Saves old session:
- Generates session-summary.json
- Links parent/child relationship
- Indexes by tags
- Stores flow-trace.json
    ↓
Creates new session
    ↓
Claude loads previous context:
- Reads chain-index.json
- Loads related sessions
- Shows: "In the previous session, we..."
    ↓
Claude Insight Dashboard
- Shows session history
- Displays relationships
- Searchable by tag
```

### Try It Yourself

1. **Run multiple Claude Code windows simultaneously**
   - Each gets isolated state (no conflicts)
   - Work on different projects without interference

2. **Use `/clear` in one window**
   - Previous session automatically saved
   - Context automatically chained
   - Claude references: "As we did before..."

3. **Open Claude Insight dashboard**
   - Sessions page: See all past sessions
   - Relationships: View parent/child chains
   - Tags: Filter by project or skill
   - Search: Find sessions by topic

### Complete Documentation

For full details on session management, see:
- **`docs/session-management-comparison.md`** - Complete comparison with Claude native
- **`docs/multi-window-session-isolation.md`** - PID-based isolation technical details
- **Sessions Dashboard** - Visual session explorer in Claude Insight

---

## Dashboard Pages

| Page | URL | What It Shows |
|------|-----|---------------|
| Dashboard | `/` | System overview, context %, session count |
| Sessions | `/sessions` | Session list, duration, requests per session |
| 3-Level Flow History | `/3level-flow-history` | Per-session flow execution trace |
| Policies | `/policies` | Policy enforcement pass/fail per request |
| Analytics | `/analytics` | Skill/agent usage, model distribution, costs |
| Anomaly Detection | `/anomaly-detection` | Detected unusual patterns |
| Predictive Analytics | `/predictive-analytics` | Context and usage forecasting |
| Performance Profiling | `/performance-profiling` | Step-level response times |
| Alert Routing | `/alert-routing` | Alert rules and escalation config |
| Notifications | `/notifications` | Notification history and channels |
| Advanced Search | `/advanced-search` | Search across sessions and logs |
| Logs | `/logs` | Raw log viewer |
| Settings | `/settings` | Dashboard configuration |

---

## Project Structure

```
claude-insight/
├── CLAUDE.md                    <- Claude Code instructions + setup guide
├── README.md                    <- This file
├── CHANGELOG.md                 <- Version history
├── LICENSE                      <- MIT license
├── run.py                       <- App entry point
├── requirements.txt             <- Python dependencies (17 packages)
├── setup.py                     <- Package config
│
├── src/                         <- Flask application
│   ├── app.py                   <- Main app, routes, SocketIO setup
│   ├── config.py                <- Dev/Prod/Test configuration
│   ├── auth/
│   │   └── user_manager.py      <- Authentication (bcrypt)
│   ├── models/
│   │   └── user.py              <- User model
│   ├── routes/
│   │   ├── claude_credentials.py
│   │   └── session_search.py
│   ├── middleware/
│   │   └── enforcement_logger.py  <- Logs all enforcement actions
│   ├── mcp/
│   │   └── enforcement_server.py  <- MCP enforcement server
│   ├── services/
│   │   ├── monitoring/            <- Core monitoring logic
│   │   │   ├── three_level_flow_tracker.py
│   │   │   ├── policy_execution_tracker.py
│   │   │   ├── session_tracker.py
│   │   │   ├── metrics_collector.py
│   │   │   ├── log_parser.py
│   │   │   ├── skill_agent_tracker.py
│   │   │   ├── automation_tracker.py
│   │   │   ├── optimization_tracker.py
│   │   │   └── performance_profiler.py
│   │   ├── ai/
│   │   │   ├── anomaly_detector.py
│   │   │   ├── bottleneck_analyzer.py
│   │   │   └── predictive_analytics.py
│   │   ├── notifications/
│   │   │   ├── alert_routing.py
│   │   │   ├── alert_sender.py
│   │   │   └── notification_manager.py
│   │   └── widgets/
│   │       ├── collaboration_manager.py
│   │       ├── comments_manager.py
│   │       ├── community_manager.py
│   │       └── version_manager.py
│   └── utils/
│       ├── path_resolver.py       <- Cross-platform paths
│       └── history_tracker.py
│
├── templates/                   <- 31 Jinja2 HTML templates
│   ├── base.html                <- Base layout
│   ├── dashboard.html           <- Main dashboard
│   ├── 3level-flow-history.html <- Flow history page
│   ├── sessions.html
│   ├── policies.html
│   ├── analytics.html
│   └── ...
│
├── static/                      <- CSS, JS, i18n
│   ├── css/
│   ├── js/
│   └── i18n/
│       ├── en.json
│       ├── hi.json
│       ├── es.json
│       ├── fr.json
│       └── de.json
│
├── scripts/                     <- Enforcement + setup scripts
│   ├── setup-global-claude.sh   <- Unix automatic setup
│   ├── setup-global-claude.ps1  <- Windows automatic setup
│   ├── global-claude-md-template.md  <- Public CLAUDE.md template
│   ├── install-auto-hooks.sh    <- Hook installer
│   ├── 3-level-flow.py          <- Main hook entry point
│   ├── auto-fix-enforcer.sh     <- Level -1 enforcement
│   ├── session-start.sh         <- Level 1 session init
│   ├── per-request-enforcer.py  <- Per-request enforcement
│   ├── context-monitor-v2.py    <- Context monitoring
│   ├── blocking-policy-enforcer.py
│   ├── session-id-generator.py/.sh
│   ├── session-logger.py
│   ├── clear-session-handler.py <- /clear hook handler
│   ├── stop-notifier.py         <- Stop hook handler
│   ├── session-chain-manager.py <- Session chaining (parent/child/tags)
│   ├── session-summary-manager.py <- Per-session summaries
│   └── detect-sync-eligibility.py
│
├── policies/                    <- Policy definitions (organized by level)
│   ├── 01-sync-system/          <- Level 1 foundation policies
│   ├── 02-standards-system/     <- Level 2 coding standards policies
│   ├── 03-execution-system/     <- Level 3 execution policies
│   └── testing/                 <- Test case policies
│
├── docs/                        <- Architecture documentation
│   ├── ARCHITECTURE.md
│   ├── auto-fix-enforcement.md
│   ├── session-id-tracking.md
│   └── ...
│
├── config/                      <- Runtime config JSONs
│   ├── failure-kb.json          <- Failure knowledge base
│   ├── skills-registry.json     <- Available skills registry
│   └── user-preferences.json
│
└── tests/                       <- Test suite
    ├── run_all_tests.py
    ├── test_policy_integration.py
    ├── test_enforcement_logger.py
    └── ...
```

---

## API Reference

### Sessions

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/sessions` | List all sessions |
| GET | `/api/sessions/<id>` | Get session details |
| GET | `/api/sessions/<id>/flow-trace` | Get 3-level flow trace for session |

### Metrics

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/metrics` | Current system metrics |
| GET | `/api/metrics/history` | Historical metrics (query: `?days=7`) |
| GET | `/api/metrics/context-usage` | Context usage over time |
| GET | `/api/metrics/model-distribution` | Haiku/Sonnet/Opus usage |

### Policies

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/policies` | All policy enforcement records |
| GET | `/api/policies/summary` | Pass/fail summary |
| GET | `/api/policies/<name>` | Specific policy history |

### Analytics

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/analytics/skills` | Skill usage statistics |
| GET | `/api/analytics/agents` | Agent usage statistics |
| GET | `/api/analytics/costs` | Token costs and model usage |
| GET | `/api/anomalies` | Detected anomalies |
| GET | `/api/predictions` | Predictive analytics data |

### Alerts

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/alerts` | Alert history |
| POST | `/api/alerts/rules` | Create alert rule |
| DELETE | `/api/alerts/rules/<id>` | Delete alert rule |

### Export

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/export/csv` | Export metrics as CSV |
| GET | `/api/export/excel` | Export as Excel |
| GET | `/api/export/pdf` | Export as PDF report |

---

## Configuration

All config is in `src/config.py`:

```python
class Config:
    SECRET_KEY = 'your-secret-key-here'       # Change in production!
    HOST = '0.0.0.0'
    PORT = 5000
    DEBUG = False

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False
```

**Memory System paths** (auto-detected via `src/utils/path_resolver.py`):

| Path | What It Contains |
|------|-----------------|
| `~/.claude/memory/logs/sessions/` | Per-session flow-trace.json files |
| `~/.claude/memory/logs/policy-hits.log` | Policy enforcement log |
| `~/.claude/memory/sessions/` | Session state files |
| `~/.claude/memory/current/` | Core enforcement scripts |

---

## Global vs Project CLAUDE.md

This repo ships with two CLAUDE.md-related files:

| File | Purpose | Location |
|------|---------|----------|
| `CLAUDE.md` | Project-specific instructions for Claude Code | Repo root |
| `scripts/global-claude-md-template.md` | Template for global installation | `scripts/` |

**The global CLAUDE.md** (installed by setup scripts to `~/.claude/CLAUDE.md`) contains:
- 3-level architecture enforcement rules
- Complete skill/agent registry (21 skills + 12 agents)
- Windows Unicode restrictions
- Context optimization rules

**The project CLAUDE.md** (`claude-insight/CLAUDE.md`) contains:
- Project overview and structure
- Setup instructions
- Development commands
- Project-specific conventions

**Rule:** Global policies always take precedence. Project CLAUDE.md cannot override
global policies. It adds context only.

**Important:** Never put project-specific credentials, internal paths, or
business logic in the global `~/.claude/CLAUDE.md`. Keep it generic.

---

## Troubleshooting

### Dashboard shows no data

The dashboard reads from `~/.claude/memory/logs/`. If there is no data:

1. Verify memory system is installed:
   ```bash
   ls ~/.claude/memory/current/
   ```
2. Verify hooks are in settings.json:
   ```bash
   cat ~/.claude/settings.json | grep "3-level-flow"
   ```
3. Restart Claude Code and send a test message
4. Check if log files are being created:
   ```bash
   ls ~/.claude/memory/logs/sessions/
   ```

### Hook not running

1. Check settings.json exists: `cat ~/.claude/settings.json`
2. Verify hook script exists: `ls ~/.claude/memory/current/3-level-flow.py`
3. Re-run setup: `.\scripts\setup-global-claude.ps1` (Windows)

### Python encoding errors (Windows)

If you see `UnicodeEncodeError` in Python scripts:
```bash
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
```
All Python scripts in this project use ASCII-only output (cp1252 safe).

### Flask server won't start

```bash
# Check Python version (need 3.8+)
python --version

# Check dependencies
pip install -r requirements.txt

# Check port availability
python run.py --port 8081
```

### Authentication issues

Default credentials: `admin` / `admin`

If locked out, reset in `src/auth/user_manager.py`.

---

## Contributing

Contributions are welcome! This project is focused on the monitoring dashboard and
core enforcement scripts. Please follow these guidelines:

1. **Fork** the repo and create a feature branch
2. **Follow** the project conventions in `CLAUDE.md`
3. **Test** your changes: `python -m pytest tests/ -v`
4. **No daemons** — background monitoring is via Flask + hooks only
5. **ASCII only** in Python files (Windows cp1252 compatibility)
6. **Submit** a pull request with clear description

**What fits in this repo:**
- Dashboard UI improvements
- New monitoring metrics
- Additional analytics features
- Bug fixes

**What does NOT fit:**
- Project-specific business logic
- Credentials or personal configuration
- Heavy background processes or daemons

---

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for full version history.

**Latest — v3.8.0 (2026-02-23):**
- Added session chaining system (parent/child session relationships, auto-tagging, summaries)
- Added 02-standards-system policies folder (coding-standards-enforcement-policy)
- Cleaned up duplicate flat policy files (all policies now in organized sub-folders only)
- Updated all hook scripts with loophole hardening fixes (19 loopholes, 18 fixed)
- Added session-chain-manager.py and session-summary-manager.py scripts

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

**Source:** https://github.com/piyushmakhija28/claude-insight
**Version:** 3.8.0 | **Python:** 3.8+ | **Flask:** 3.0

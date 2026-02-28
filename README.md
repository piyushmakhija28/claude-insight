# Claude Insight v3.11.0

**Real-time Monitoring Dashboard for the Claude Memory System (3-Level Architecture)**

[![GitHub](https://img.shields.io/badge/GitHub-claude--insight-blue?logo=github)](https://github.com/piyushmakhija28/claude-insight)
[![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0-green?logo=flask)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Version](https://img.shields.io/badge/Version-3.11.0-brightgreen)](CHANGELOG.md)

Claude Insight is a Python Flask dashboard that monitors how Claude Code follows the
**3-Level Architecture enforcement policies** in real-time. Track policy execution,
session analytics, skill/agent usage, context optimization, and AI-powered anomaly
detection — all from one interface.

---

## Table of Contents

1. [What Is Claude Insight?](#what-is-claude-insight)
2. [3-Tier Ecosystem Architecture](#3-tier-ecosystem-architecture)
3. [The ~/.claude/ Directory](#the-claude-directory)
4. [Quick Start](#quick-start)
   - [Prerequisites](#prerequisites)
   - [Installation](#installation)
   - [Memory System Setup](#memory-system-setup)
   - [Voice Notifications Setup](#voice-notifications-setup)
   - [Running the Dashboard](#running-the-dashboard)
5. [3-Level Architecture Overview](#3-level-architecture-overview)
   - [Level -1: Auto-Fix Enforcement](#level--1-auto-fix-enforcement)
   - [Level 1: Sync System](#level-1-sync-system)
   - [Level 2: Standards System](#level-2-standards-system)
   - [Level 3: Execution System (12 Steps)](#level-3-execution-system-12-steps)
6. [Hook Scripts Reference](#hook-scripts-reference)
   - [settings.json Configuration](#settingsjson-configuration)
   - [What Each Hook Does](#what-each-hook-does)
7. [Imports and Module Loading](#imports-and-module-loading)
8. [Session Management](#session-management)
   - [Session ID Format](#session-id-format)
   - [Session Storage](#session-storage)
   - [Session Chaining](#session-chaining)
9. [Multi-Window Session Isolation](#multi-window-session-isolation)
10. [All Policies Reference](#all-policies-reference)
11. [Dashboard Pages](#dashboard-pages)
12. [Project Structure](#project-structure)
13. [API Reference](#api-reference)
14. [Configuration](#configuration)
15. [Global vs Project CLAUDE.md](#global-vs-project-claudemd)
16. [Deployment and Distribution](#deployment-and-distribution)
17. [Troubleshooting](#troubleshooting)
18. [Contributing](#contributing)
19. [Changelog](#changelog)
20. [License](#license)

---

## What Is Claude Insight?

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
Claude Code (your IDE or CLI)
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

### Features

#### Core Monitoring

| Feature | Description |
|---------|-------------|
| **3-Level Flow Tracker** | Shows each Level (-1, 1, 2, 3) execution per session |
| **Policy Execution Tracker** | Which policies ran, pass/fail per request |
| **Session Analytics** | Session duration, requests per session, context usage |
| **Session Chaining** | Parent/child session relationships, tag-based linking, cross-session summaries |
| **Skill/Agent Usage** | Which skills and agents were invoked and how often |
| **Context Monitoring** | Context % per request, optimization actions taken |
| **Model Selection Tracking** | Haiku/Sonnet/Opus distribution across requests |

#### AI-Powered Analytics

| Feature | Description |
|---------|-------------|
| **Anomaly Detection** | Detects unusual patterns (context spikes, policy failures) |
| **Predictive Analytics** | Forecasts context usage and session patterns |
| **Bottleneck Analysis** | Identifies slow steps in the 3-level flow |
| **Performance Profiling** | Response time analysis per step |

#### Dashboard Capabilities

| Feature | Description |
|---------|-------------|
| **Real-time Updates** | Live data via WebSocket (SocketIO) |
| **Session Search** | Search and filter session history |
| **Export Options** | CSV, Excel, PDF report generation |
| **Multi-language** | EN, HI, ES, FR, DE support |
| **Custom Dashboard Builder** | Build personalized metric views |
| **Dark/Light Themes** | Multiple UI themes |

---

## 3-Tier Ecosystem Architecture

Claude Insight is **Tier 2** of a 3-tier architecture:

```
Tier 1: User Interface         (claude-code-ide)
   |  uses hooks from
Tier 2: Policy Enforcement      (THIS PROJECT - claude-insight)
   |  uses skills from
Tier 3: Knowledge Base          (claude-global-library)
```

| Tier | Repository | Purpose |
|------|-----------|---------|
| **Tier 1** | [claude-code-ide](https://github.com/piyushmakhija28/claude-code-ide) | JavaFX IDE + hook-downloader that executes hooks |
| **Tier 2** | [claude-insight](https://github.com/piyushmakhija28/claude-insight) | Python hook scripts, policies, Flask monitoring dashboard |
| **Tier 3** | [claude-global-library](https://github.com/piyushmakhija28/claude-global-library) | 21 reusable skills + 12 agents for code generation |

---

## The ~/.claude/ Directory

All three tiers converge into a single shared directory: `~/.claude/`. This is the **canonical runtime location** used by both the IDE and the CLI.

### Why ~/.claude/?

1. **Single source of truth** - One location for all Claude configuration
2. **Tool-agnostic** - IDE and CLI share the same hooks, policies, and session data
3. **Portable** - `~/` resolves correctly on Windows, macOS, and Linux
4. **No overhead** - Files are lightweight JSON summaries, not large datasets
5. **Persistent** - Survives IDE restarts, system reboots, and tool upgrades

### Directory Layout

```
~/.claude/
|-- CLAUDE.md                          # Global configuration (loaded every session)
|-- settings.json                      # Hook configuration
|
|-- scripts/                           # Hook scripts (from claude-insight GitHub)
|   |-- 3-level-flow.py               #   Main: 3-level architecture check
|   |-- clear-session-handler.py       #   Handles /clear command
|   |-- pre-tool-enforcer.py           #   Validates tool calls
|   |-- post-tool-tracker.py           #   Tracks progress
|   |-- stop-notifier.py              #   Session save + voice
|   |-- auto-fix-enforcer.py          #   System health checks
|   +-- architecture/                  #   3-Level Architecture (107 files)
|       |-- 01-sync-system/
|       |-- 02-standards-system/
|       +-- 03-execution-system/
|
|-- memory/                            # Session data (local only)
|   |-- logs/sessions/                 #   Per-session flow-trace.json
|   |-- sessions/                      #   Session state
|   |-- tasks/                         #   Task tracking
|   +-- config/                        #   Preferences, patterns
|
+-- policies/                          # Policy definitions (34+ .md)
    |-- 01-sync-system/
    |-- 02-standards-system/
    +-- 03-execution-system/
```

### What Each Part Does

| Directory | Purpose | Written By | Read By |
|-----------|---------|-----------|---------|
| `scripts/` | Hook scripts enforcing policies | hook-downloader (from this repo's GitHub) | Claude Code CLI + IDE |
| `memory/logs/sessions/` | Session traces | Hook scripts | Claude Insight dashboard |
| `memory/sessions/` | Active session state | Hook scripts | Claude (continuity) |
| `memory/config/` | User preferences | Hook scripts | Hook scripts + dashboard |
| `policies/` | Policy definitions | Setup script | 3-level-flow.py |

---

## Quick Start

### Prerequisites

- Python 3.8+
- Claude Code installed (`npm install -g @anthropic-ai/claude-code`)
- Git
- For Windows: PowerShell 5.0+

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

**Option A - Automatic (Recommended):**

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
1. Create `~/.claude/scripts/` with enforcement scripts
2. Install hooks in `~/.claude/settings.json`
3. Install the global CLAUDE.md
4. Create necessary directories (`memory/logs/`, `memory/sessions/`, `memory/config/`)
5. Verify installation is working

**Option B - Manual:**

See [CLAUDE.md](CLAUDE.md) for step-by-step manual setup instructions.

**Verify setup is working:**

After restarting Claude Code, send any message. You should see:
```
[LEVEL -1] AUTO-FIX ENFORCEMENT (BLOCKING)  [OK]
[LEVEL 1] SYNC SYSTEM                        [OK] Context: XX% | Session: SESSION-...
[LEVEL 2] STANDARDS SYSTEM                   [OK] 15 standards, 156 rules loaded
[LEVEL 3] EXECUTION SYSTEM (12 steps)        [OK] All steps verified
```

### Voice Notifications Setup

Claude Insight uses **voice notifications** to speak session summaries, greetings, and
task completion updates via text-to-speech. This requires an **OpenRouter API key**.

**Step 1: Create an OpenRouter API key**

1. Go to [https://openrouter.ai](https://openrouter.ai) and create an account
2. Navigate to **Keys** in your dashboard
3. Click **Create Key** and copy the generated API key

**Step 2: Save the API key locally**

```bash
mkdir -p ~/.claude/config
echo "YOUR_KEY_HERE" > ~/.claude/config/openrouter-api-key
```

**What voice notifications do:**

| Event | When | What It Says |
|-------|------|--------------|
| Session Start | You open Claude Code or run `/clear` | Hinglish greeting with session context |
| Task Complete | A task is marked completed | Summary of what was accomplished |
| Work Done | Session ends with completed work | Comprehensive session summary |

> **Note:** Without the OpenRouter API key, voice notifications fall back to static default messages.

### Running the Dashboard

```bash
# Start the Flask server (default port 5000)
python run.py

# Custom port
python run.py --port 8080

# With debug mode
python run.py --debug
```

Open http://localhost:5000 in your browser.

**Default credentials:**
- Username: `admin`
- Password: `admin`

> **IMPORTANT:** Change these in `src/auth/user_manager.py` before deploying to production.

---

## 3-Level Architecture Overview

The 3-level architecture runs automatically on every Claude Code request via hooks.

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

- **Context monitoring** - Checks usage %, applies optimization if >70%
- **Session ID generation** - Format: `SESSION-YYYYMMDD-HHMMSS-XXXX`
- **Previous session loading** - Automatically loads previous session state
- **Session Chaining** - Links sessions in parent/child relationships
- **Session Summaries** - Accumulates per-request data, generates summaries on `/clear`

### Level 2: Standards System

**Loads 15 coding standards (156 rules) and selects the correct skill/agent.**

Standards loaded:
1. Project structure
2. Config management
3. Secret management
4. Response format standards
5. Service layer patterns
6. Entity/model patterns
7. Controller patterns
8. Constants organization
9. Common utilities
10. Error handling
11. API design (REST)
12. Database standards
13. Documentation
14. Kubernetes network policies
15. K8s/Docker/Jenkins infrastructure standards

### Level 3: Execution System (12 Steps)

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

---

## Hook Scripts Reference

The hooks are configured in `~/.claude/settings.json` and run automatically.
There are **4 hook types**, each enforcing different levels:

| Hook Type | Trigger | Scripts | Levels Enforced |
|-----------|---------|---------|-----------------|
| `UserPromptSubmit` | Every new user message | `clear-session-handler.py` + `3-level-flow.py` | Level -1, 1, 2, 3 |
| `PreToolUse` | Before every tool call | `pre-tool-enforcer.py` | Level 3.6 + 3.7 |
| `PostToolUse` | After every tool call | `post-tool-tracker.py` | Level 3.9 |
| `Stop` | After every Claude response | `stop-notifier.py` | Level 3.10 |

### settings.json Configuration

```json
{
  "model": "sonnet",
  "hooks": {
    "UserPromptSubmit": [{
      "hooks": [
        {
          "type": "command",
          "command": "python ~/.claude/scripts/clear-session-handler.py",
          "timeout": 15
        },
        {
          "type": "command",
          "command": "python ~/.claude/scripts/3-level-flow.py --summary",
          "timeout": 30
        }
      ]
    }],
    "PreToolUse": [{
      "hooks": [{
        "type": "command",
        "command": "python ~/.claude/scripts/pre-tool-enforcer.py",
        "timeout": 10
      }]
    }],
    "PostToolUse": [{
      "hooks": [{
        "type": "command",
        "command": "python ~/.claude/scripts/post-tool-tracker.py",
        "timeout": 10
      }]
    }],
    "Stop": [{
      "hooks": [{
        "type": "command",
        "command": "python ~/.claude/scripts/stop-notifier.py",
        "timeout": 20
      }]
    }]
  }
}
```

> **IMPORTANT:** All hooks must have `"async": false` (default). If set to `true`, hook output is discarded and the checkpoint table is not displayed.

### What Each Hook Does

**`UserPromptSubmit` -> `clear-session-handler.py` + `3-level-flow.py`**
- Detects `/clear` command and saves old session, starts new one
- Runs the full 3-level architecture check (Level -1 through Level 3)
- Auto-tags sessions with keywords from prompt, skill, task type
- Writes `flow-trace.json` to the session log folder
- Claude Insight reads this file for all monitoring data

**`PreToolUse` -> `pre-tool-enforcer.py`**
- Runs BEFORE every tool call (Read, Write, Edit, Bash, Grep, etc.)
- Exit 0 = allow tool (may print optimization hints)
- Exit 1 = BLOCK tool (prints reason, tool call cancelled)
- Level 3.6 hints: Grep without `head_limit`, Read without `offset+limit`
- Level 3.7 blocks: Windows commands in Bash, Unicode in Python files on Windows

**`PostToolUse` -> `post-tool-tracker.py`**
- Runs AFTER every tool call (always exits 0, never blocks)
- Logs to `~/.claude/memory/logs/tool-tracker.jsonl`
- Progress deltas: Read +10%, Write +40%, Edit +30%, Bash +15%, Task +20%, Grep/Glob +5%

**`Stop` -> `stop-notifier.py`**
- Runs after every Claude response completes
- Saves session state to `~/.claude/memory/logs/`
- Triggers voice notification using session summary data
- Requires OpenRouter API key at `~/.claude/config/openrouter-api-key`

**No background daemons.** Everything runs per-request via hooks.

---

## Imports and Module Loading

### Local Imports (Same Project)

```python
from services.monitoring.metrics_collector import MetricsCollector
from services.ai.anomaly_detector import AnomalyDetector
from utils.import_manager import ImportManager
```

### External Imports (claude-global-library)

```python
from utils.import_manager import ImportManager

docker_skill = ImportManager.get_skill('docker')
orchestrator = ImportManager.get_agent('orchestrator-agent')
```

**GitHub URLs used:**
```
Skills:   https://raw.githubusercontent.com/.../claude-global-library/main/skills/{name}/skill.md
Agents:   https://raw.githubusercontent.com/.../claude-global-library/main/agents/{name}/agent.md
```

### Path Resolution

```python
from pathlib import Path

home = Path.home()
scripts = home / '.claude' / 'scripts'
memory = home / '.claude' / 'memory'
sessions = memory / 'sessions'

# Relative to script
script_dir = Path(__file__).parent
```

---

## Session Management

### Session ID Format

```
SESSION-YYYYMMDD-HHMMSS-XXXX
```

Example: `SESSION-20260216-173003-09RZ`

### Session Storage

```
~/.claude/memory/sessions/
|-- SESSION-20260224-130424-IQAV/
|   |-- flow-trace.json              # Complete 12-step execution
|   |-- session-summary.json         # Auto-generated summary
|   |-- task-metadata.json           # Task tracking
|   +-- context-metrics.json         # Token usage
|
+-- chain-index.json                 # Session relationships
```

### Session Chaining

Sessions are linked in parent/child relationships:

```
User says "/clear" in Claude Code
    |
clear-session-handler.py fires
    |
Saves old session (summary, tags, relationships)
    |
Creates new session (linked to parent)
    |
Claude loads previous context automatically
    |
Claude Insight shows session history
```

| Feature | Claude Native | Our System |
|---------|---|---|
| **Persistence** | Lost on IDE close | Saved forever |
| **Continuity** | Resets after /clear | Auto-chains sessions |
| **Multi-Window** | Conflicts | PID-based isolation |
| **Session Summaries** | None | Auto-generated |
| **History Access** | Manual scrolling | Dashboard + search |

---

## Multi-Window Session Isolation

Each Claude Code window gets its own isolated session state:

```
Window 1 (PID: 1234)
    +-- ~/.claude/.hook-state-1234.json (isolated)

Window 2 (PID: 5678)
    +-- ~/.claude/.hook-state-5678.json (isolated)

Central Registry:
    +-- ~/.claude/memory/window-state/active-windows.json
```

File locking (msvcrt on Windows, fcntl on Unix) prevents concurrent writes.

---

## All Policies Reference

### Level 1: Sync System (6 policies)

| Policy | Purpose | Location |
|--------|---------|----------|
| Session Memory | Stores session state, loads previous sessions | `policies/01-sync-system/session-management/` |
| Session Chaining | Links parent/child relationships, auto-tags | `policies/01-sync-system/session-management/` |
| Session Pruning | Manages cleanup, removes stale sessions | `policies/01-sync-system/session-management/` |
| Context Management | Monitors context %, optimizes when >70% | `policies/01-sync-system/context-management/` |
| User Preferences | Learns coding preferences, applies automatically | `policies/01-sync-system/user-preferences/` |
| Cross-Project Patterns | Detects and replicates patterns across services | `policies/01-sync-system/pattern-detection/` |

### Level 2: Standards System (1 policy, 156 rules)

| Policy | Purpose | Location |
|--------|---------|----------|
| Coding Standards Enforcement | Loads 15 standards with 156 rules | `policies/02-standards-system/` |

### Level 3: Execution System (17 policies)

| Policy | Step | Purpose | Location |
|--------|------|---------|----------|
| Prompt Generation | 3.0 | Anti-hallucination, verify examples | `policies/03-execution-system/00-prompt-generation/` |
| Anti-Hallucination | 3.0 | Detects hallucinations in generated code | `policies/03-execution-system/00-prompt-generation/` |
| Task Breakdown | 3.1 | Creates tasks with dependencies | `policies/03-execution-system/01-task-breakdown/` |
| Plan Mode Suggestion | 3.2 | Complexity scoring for plan mode | `policies/03-execution-system/02-plan-mode/` |
| Model Selection | 3.4 | Selects Haiku/Sonnet/Opus | `policies/03-execution-system/04-model-selection/` |
| Model Enforcement | 3.4 | Enforces correct model usage | `policies/03-execution-system/04-model-selection/` |
| Skill Registry | 3.5 | Maps tasks to 21+ skills | `policies/03-execution-system/05-skill-agent-selection/` |
| Skill/Agent Selection | 3.5 | Auto-invokes matched skill | `policies/03-execution-system/05-skill-agent-selection/` |
| Core Skills Mandate | 3.5 | Ensures core skills available | `policies/03-execution-system/05-skill-agent-selection/` |
| Tool Optimization | 3.6 | Applies limits on Read, Grep | `policies/03-execution-system/06-tool-optimization/` |
| Failure Prevention | 3.7 | Pre-execution checks, auto-fixes | `policies/03-execution-system/failure-prevention/` |
| Progress Tracking | 3.8-3.9 | Tracks task completion | `policies/03-execution-system/08-progress-tracking/` |
| Phase Enforcement | 3.8-3.9 | Ensures correct phase progression | `policies/03-execution-system/08-progress-tracking/` |
| Git Auto-Commit | 3.11 | Commits on phase completion | `policies/03-execution-system/09-git-commit/` |
| File Management | 3.6 | Manages file operations | `policies/03-execution-system/` |
| Parallel Execution | 3.8 | Detects parallelism opportunities | `policies/03-execution-system/` |
| Proactive Consultation | 3.2 | Asks user for decisions | `policies/03-execution-system/` |

### Testing Policies (1 policy)

| Policy | Purpose | Location |
|--------|---------|----------|
| Test Case Policy | Ensures comprehensive test coverage | `policies/testing/` |

**Total: 34+ policies across all levels.**

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
|-- CLAUDE.md                    Project instructions
|-- README.md                    This file
|-- CHANGELOG.md                 Version history
|-- LICENSE                      MIT license
|-- run.py                       App entry point
|-- requirements.txt             Python dependencies
|-- setup.py                     Package config
|
|-- src/                         Flask application
|   |-- app.py                   Main app, routes, SocketIO
|   |-- config.py                Dev/Prod/Test configuration
|   |-- auth/
|   |   +-- user_manager.py      Authentication (bcrypt)
|   |-- models/
|   |   +-- user.py              User model
|   |-- routes/
|   |   |-- claude_credentials.py
|   |   +-- session_search.py
|   |-- middleware/
|   |   +-- enforcement_logger.py
|   |-- services/
|   |   |-- monitoring/          Core monitoring logic
|   |   |   |-- three_level_flow_tracker.py
|   |   |   |-- policy_execution_tracker.py
|   |   |   |-- session_tracker.py
|   |   |   |-- metrics_collector.py
|   |   |   |-- log_parser.py
|   |   |   +-- [5 more trackers]
|   |   |-- ai/
|   |   |   |-- anomaly_detector.py
|   |   |   |-- bottleneck_analyzer.py
|   |   |   +-- predictive_analytics.py
|   |   |-- notifications/
|   |   |   |-- alert_routing.py
|   |   |   |-- alert_sender.py
|   |   |   +-- notification_manager.py
|   |   +-- widgets/
|   +-- utils/
|       |-- path_resolver.py     Cross-platform paths
|       |-- import_manager.py    Load skills/agents from GitHub
|       +-- history_tracker.py
|
|-- templates/                   31 Jinja2 HTML templates
|-- static/                      CSS, JS, i18n (EN, HI, ES, FR, DE)
|
|-- scripts/                     Hook scripts + setup (40+ total)
|   |-- setup-global-claude.sh   Unix setup
|   |-- setup-global-claude.ps1  Windows setup
|   |-- 3-level-flow.py          Main hook entry point
|   |-- clear-session-handler.py /clear handler
|   |-- pre-tool-enforcer.py     Tool validation
|   |-- post-tool-tracker.py     Progress tracking
|   |-- stop-notifier.py         Session finalization
|   +-- architecture/            3-Level Architecture (107 files)
|       |-- 01-sync-system/      Context & session (38 files)
|       |-- 02-standards-system/ Standards & rules (3 files)
|       +-- 03-execution-system/ Execution flows (66 files)
|
|-- policies/                    Policy definitions (34+ .md files)
|   |-- 01-sync-system/
|   |-- 02-standards-system/
|   +-- 03-execution-system/
|
|-- config/                      Runtime config JSONs
|-- docs/                        Architecture documentation
+-- tests/                       Test suite (16+ test files)
```

---

## API Reference

### Sessions

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/sessions` | List all sessions |
| GET | `/api/sessions/<id>` | Get session details |
| GET | `/api/sessions/<id>/flow-trace` | Get 3-level flow trace |

### Metrics

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/metrics` | Current system metrics |
| GET | `/api/metrics/history` | Historical metrics (`?days=7`) |
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
    SECRET_KEY = 'your-secret-key-here'
    HOST = '0.0.0.0'
    PORT = 5000
    DEBUG = False
```

### Memory System Paths

Auto-detected via `src/utils/path_resolver.py`:

| Path | What It Contains |
|------|-----------------|
| `~/.claude/scripts/` | Hook scripts (enforcement) |
| `~/.claude/scripts/architecture/` | 3-Level Architecture modules |
| `~/.claude/memory/logs/sessions/` | Per-session flow-trace.json |
| `~/.claude/memory/sessions/` | Session state files |
| `~/.claude/memory/config/` | Configuration files (JSON) |
| `~/.claude/policies/` | Policy definitions |

---

## Global vs Project CLAUDE.md

| File | Purpose | Location |
|------|---------|----------|
| Global CLAUDE.md | 3-level architecture rules, skill registry | `~/.claude/CLAUDE.md` |
| Project CLAUDE.md | Project-specific instructions, structure | Repo root |

**Rule:** Global policies always take precedence. Project CLAUDE.md cannot override
global policies - it adds context only.

---

## Deployment and Distribution

### How Scripts Get to ~/.claude/

**Option 1: IDE (hook-downloader)**
The Claude Code IDE uses `hook-downloader.py` to download scripts from this repo's GitHub on startup. Scripts are cached locally in `~/.claude/scripts/`.

**Option 2: Setup script**
Run `scripts/setup-global-claude.sh` (Unix) or `scripts/setup-global-claude.ps1` (Windows) to manually deploy scripts to `~/.claude/scripts/`.

**Option 3: Manual**
```bash
cd claude-insight
python deploy/deploy-to-local.py
```

### What Goes Where

| Content | Source | Deployed To |
|---------|--------|-------------|
| Hook scripts (40+) | `claude-insight/scripts/` | `~/.claude/scripts/` |
| Architecture (107 files) | `claude-insight/scripts/architecture/` | `~/.claude/scripts/architecture/` |
| Policies (34+ .md) | `claude-insight/policies/` | `~/.claude/policies/` |
| Session data | Generated at runtime | `~/.claude/memory/` (local only) |

---

## Troubleshooting

### Dashboard shows no data

1. Verify hooks are installed: `cat ~/.claude/settings.json | grep "3-level-flow"`
2. Verify scripts exist: `ls ~/.claude/scripts/3-level-flow.py`
3. Restart Claude Code and send a test message
4. Check logs: `ls ~/.claude/memory/logs/sessions/`

### Hook not running

1. Check settings.json: `cat ~/.claude/settings.json`
2. Verify script exists: `ls ~/.claude/scripts/3-level-flow.py`
3. Re-run setup: `./scripts/setup-global-claude.sh`

### Python encoding errors (Windows)

```bash
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
```

### Flask server won't start

```bash
python --version          # Need 3.8+
pip install -r requirements.txt
python run.py --port 8081  # Try different port
```

### Checkpoint not displayed

Ensure all hooks in `~/.claude/settings.json` have `"async": false` (or omit async entirely, as false is the default). When async is true, hook stdout is discarded.

---

## Contributing

1. **Fork** the repo and create a feature branch
2. **Follow** the project conventions in `CLAUDE.md`
3. **Test** your changes: `python -m pytest tests/ -v`
4. **ASCII only** in Python files (Windows cp1252 compatibility)
5. **Submit** a pull request with clear description

---

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for full version history.

**Latest - v3.11.0 (2026-02-28):**
- **[FIX]** All script paths corrected to canonical `~/.claude/scripts/` location
- **[FIX]** Removed all `memory/current` references (deprecated path)
- **[FIX]** Removed hardcoded `/c/Users/techd/` path from architecture_module_monitor
- **[FIX]** auto-commit-enforcer uses `CLAUDE_WORKSPACE_DIR` env var instead of hardcoded path
- **[DOCS]** README updated with ~/.claude/ directory explanation and correct paths
- **[DOCS]** settings.json example uses correct `~/.claude/scripts/` paths

**v3.10.0 (2026-02-25):**
- Added comprehensive "All Policies Reference" section to README
- Complete table of all 34+ policies across 3-level architecture

**v3.9.0 (2026-02-25):**
- Review checkpoint fix (async: false)
- Removed 61 duplicate files from scripts/architecture/

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

**Source:** https://github.com/piyushmakhija28/claude-insight
**Version:** 3.11.0 | **Python:** 3.8+ | **Flask:** 3.0
**Last Updated:** 2026-02-28

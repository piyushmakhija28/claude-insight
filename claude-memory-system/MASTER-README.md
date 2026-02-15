# Claude Memory System - Complete Guide

**Version:** 2.2.0
**Status:** 🟢 FULLY OPERATIONAL
**Last Updated:** 2026-02-15

---

## 📑 Table of Contents

### 🚀 Quick Start
- [1.1 System Overview](#11-system-overview)
- [1.2 First Time Setup](#12-first-time-setup)
- [1.3 Daily Usage](#13-daily-usage)
- [1.4 Essential Commands](#14-essential-commands)

### 🤖 System Architecture
- [2.1 Core Components](#21-core-components)
- [2.2 Daemon Infrastructure](#22-daemon-infrastructure)
- [2.3 File Structure](#23-file-structure)
- [2.4 How It Works](#24-how-it-works)

### 📜 Policies & Enforcement
- [3.1 Core Skills Mandate](#31-core-skills-mandate)
- [3.2 Model Selection Enforcement](#32-model-selection-enforcement)
- [3.3 Common Failures Prevention](#33-common-failures-prevention)
- [3.4 Context-Session Integration](#34-context-session-integration)
- [3.5 File Management Policy](#35-file-management-policy)
- [3.6 Git Auto-Commit Policy](#36-git-auto-commit-policy)
- [3.7 Proactive Consultation Policy](#37-proactive-consultation-policy)
- [3.8 Session Memory Policy](#38-session-memory-policy)
- [3.9 Session Pruning Policy](#39-session-pruning-policy)
- [3.10 User Preferences Policy](#310-user-preferences-policy)
- [3.11 Cross-Project Patterns Policy](#311-cross-project-patterns-policy)
- [3.12 Test Case Policy](#312-test-case-policy)

### 🎯 Token Optimization
- [4.1 Optimization Overview](#41-optimization-overview)
- [4.2 Smart File Summarization](#42-smart-file-summarization)
- [4.3 Tiered Caching Strategy](#43-tiered-caching-strategy)
- [4.4 Diff-Based Editing](#44-diff-based-editing)
- [4.5 Smart Grep Optimization](#45-smart-grep-optimization)
- [4.6 AST Navigation](#46-ast-navigation)
- [4.7 All 15 Optimization Strategies](#47-all-15-optimization-strategies)

### ☕ Java Spring Boot Standards
- [5.1 Project Structure](#51-project-structure)
- [5.2 Package Conventions](#52-package-conventions)
- [5.3 Mandatory Patterns](#53-mandatory-patterns)
- [5.4 Agent Collaboration Strategy](#54-agent-collaboration-strategy)

### 🔧 Configuration Management
- [6.1 Spring Cloud Config Server](#61-spring-cloud-config-server)
- [6.2 Secret Management](#62-secret-management)
- [6.3 Configuration Hierarchy](#63-configuration-hierarchy)

### 🌐 API & Web Standards
- [7.1 API Design Standards](#71-api-design-standards)
- [7.2 Error Handling Standards](#72-error-handling-standards)
- [7.3 Response Format](#73-response-format)
- [7.4 HTTP Status Codes](#74-http-status-codes)

### 🔐 Security Best Practices
- [8.1 Secret Management](#81-secret-management)
- [8.2 Password Security](#82-password-security)
- [8.3 Input Validation](#83-input-validation)
- [8.4 SQL Injection Prevention](#84-sql-injection-prevention)
- [8.5 XSS Prevention](#85-xss-prevention)
- [8.6 Security Checklist](#86-security-checklist)

### 🗄️ Database Standards
- [9.1 Entity Design Pattern](#91-entity-design-pattern)
- [9.2 Naming Conventions](#92-naming-conventions)
- [9.3 Relationships](#93-relationships)
- [9.4 Repository Pattern](#94-repository-pattern)
- [9.5 Transaction Management](#95-transaction-management)
- [9.6 Query Optimization](#96-query-optimization)

### 📝 Logging Standards
- [10.1 Log Levels](#101-log-levels)
- [10.2 Best Practices](#102-best-practices)
- [10.3 Sensitive Data Masking](#103-sensitive-data-masking)

### 🔄 Git Management
- [11.1 Repository Rules](#111-repository-rules)
- [11.2 Auto-Commit Triggers](#112-auto-commit-triggers)
- [11.3 Commit Message Format](#113-commit-message-format)

### 📊 Monitoring & Health
- [12.1 Dashboard](#121-dashboard)
- [12.2 Daemon Status](#122-daemon-status)
- [12.3 Logs](#123-logs)
- [12.4 Health Checks](#124-health-checks)

### 🛠️ Troubleshooting
- [13.1 Common Issues](#131-common-issues)
- [13.2 Daemon Problems](#132-daemon-problems)
- [13.3 Context Issues](#133-context-issues)
- [13.4 Rollback](#134-rollback)

### 📚 Reference
- [14.1 All Scripts](#141-all-scripts)
- [14.2 All Policies](#142-all-policies)
- [14.3 All Documentation](#143-all-documentation)
- [14.4 Command Cheat Sheet](#144-command-cheat-sheet)

---

# 🚀 1. Quick Start

## 1.1 System Overview

The Claude Memory System is a comprehensive automation framework that:

- **Reduces token consumption by 60-80%** through intelligent optimization
- **Prevents repeated failures** through self-learning knowledge base
- **Learns user preferences** to avoid repeated questions
- **Manages context automatically** with tiered caching and smart cleanup
- **Enforces code standards** for Java Spring Boot projects
- **Runs 8-9 background daemons** for continuous optimization

**Key Benefits:**
- 200K token budget feels like 500K+
- Zero manual intervention required
- 100% local (no cloud dependency)
- Self-learning and adaptive

---

## 1.2 First Time Setup

### Windows Auto-Startup (One-Time)

```powershell
# Run this once to auto-start all daemons on login
powershell -ExecutionPolicy Bypass -File ~/.claude/memory/setup-windows-startup.ps1
```

This creates:
- ✅ Startup batch script
- ✅ Silent wrapper (no console window)
- ✅ Task Scheduler entry
- ✅ All 8-9 daemons auto-start on Windows login

### Verify Installation

```bash
# Check system health
bash ~/.claude/memory/verify-system.sh

# View dashboard
bash ~/.claude/memory/dashboard-v2.sh

# Check daemon status
python ~/.claude/memory/daemon-manager.py --status-all
```

**Expected Result:** 8/8 or 9/9 daemons running ✅

---

## 1.3 Daily Usage

### At Session Start (MANDATORY)

```bash
# Single command - does everything!
bash ~/.claude/memory/session-start.sh
```

**This automatically:**
1. ✅ Starts auto-recommendation daemon (9th daemon)
2. ✅ Checks all 9 daemon PIDs and status
3. ✅ Shows latest recommendations (model, skills, agents)
4. ✅ Shows context status (OK/WARNING/CRITICAL)
5. ✅ Shows optimizations needed
6. ✅ Provides complete system health summary

**Alternative (Quick Check):**
```bash
# Just check latest recommendations
python ~/.claude/memory/check-recommendations.py
```

### During Work

The system works automatically:
- ✅ Context monitored every 10 min
- ✅ Sessions auto-saved every 15 min
- ✅ Preferences learned every 20 min
- ✅ Skills suggested every 5 min
- ✅ Failures prevented on every tool call
- ✅ Git commits triggered on completion
- ✅ Token optimization applied continuously

**You just code - the system handles everything!**

---

## 1.4 Essential Commands

### Daily Operations

```bash
# View comprehensive dashboard
bash ~/.claude/memory/dashboard-v2.sh

# Check daemon health
python ~/.claude/memory/daemon-manager.py --status-all

# Watch live activity
tail -f ~/.claude/memory/logs/policy-hits.log

# Check context status
python ~/.claude/memory/context-monitor-v2.py --current-status

# Get model recommendation
python ~/.claude/memory/model-selection-enforcer.py --analyze "your request"
```

### Monthly Maintenance

```bash
# Detect cross-project patterns
python ~/.claude/memory/detect-patterns.py

# Archive old sessions
python ~/.claude/memory/archive-old-sessions.py

# Run weekly health check
bash ~/.claude/memory/weekly-health-check.sh

# Check for conflicts
bash ~/.claude/memory/check-conflicts.sh
```

### Troubleshooting

```bash
# Restart all daemons
bash ~/.claude/memory/startup-hook.sh

# Rollback if needed
python ~/.claude/memory/rollback.py

# Run full test suite
python ~/.claude/memory/test-all-phases.py
```

---

# 🤖 2. System Architecture

## 2.1 Core Components

### Phase 1: Context Optimization
- **Purpose:** Reduce token consumption and manage context efficiently
- **Savings:** 40-60%

**Key Scripts:**
- `pre-execution-optimizer.py` - Optimizes tool parameters before execution
- `context-extractor.py` - Extracts essential information from tool outputs
- `context-cache.py` - Intelligent caching (hot/warm/cold tiers)
- `session-state.py` - External session memory management
- `context-monitor-v2.py` - Real-time monitoring with recommendations

**Context Status Levels:**

| Level | Range | Status | Action |
|-------|-------|--------|--------|
| Green | <70% | ✅ OK | None |
| Yellow | 70-84% | 💡 Light | Use cache, optimize |
| Orange | 85-89% | ⚠️ Moderate | Reference state, compact |
| Red | 90%+ | 🚨 Critical | Save session, restart |

### Phase 2: Daemon Infrastructure
- **Purpose:** Background automation and health monitoring
- **Daemons:** 8-9 running 24/7

### Phase 3: Failure Prevention
- **Purpose:** Learn from errors and prevent repetition
- **Patterns:** 15+ across 5 tools
- **Savings:** 900-2900 tokens per prevented failure

### Phase 4: Policy Automation
- **Purpose:** Enforce best practices automatically
- **Policies:** 12 active policies
- **Compliance:** 100% enforcement

### Phase 5: Advanced Optimization
- **Purpose:** Maximum token efficiency
- **Strategies:** 15 optimization techniques
- **Total Savings:** 60-80%

---

## 2.2 Daemon Infrastructure

### Core 8 Daemons (REQUIRED)

| # | Daemon | Interval | Purpose |
|---|--------|----------|---------|
| 1 | **context-daemon** | 10 min | Monitor context usage |
| 2 | **session-auto-save-daemon** | 15 min | Auto-save sessions |
| 3 | **preference-auto-tracker** | 20 min | Learn user preferences |
| 4 | **skill-auto-suggester** | 5 min | Suggest relevant skills |
| 5 | **commit-daemon** | 15 min | Auto-commit on triggers |
| 6 | **session-pruning-daemon** | Monthly | Clean old sessions |
| 7 | **pattern-detection-daemon** | Monthly | Detect cross-project patterns |
| 8 | **failure-prevention-daemon** | 6 hours | Learn from failures |

### Optional 9th Daemon

| # | Daemon | Interval | Purpose |
|---|--------|----------|---------|
| 9 | **token-optimization-daemon** | 5 min | Continuous optimization |

**Auto-Start:** All 8-9 daemons auto-start on Windows login via Task Scheduler

**Management:**
```bash
# Check status
python ~/.claude/memory/daemon-manager.py --status-all

# Restart specific daemon
python ~/.claude/memory/daemon-manager.py --restart context-daemon

# Restart all daemons
bash ~/.claude/memory/startup-hook.sh
```

---

## 2.3 File Structure

```
~/.claude/memory/
├── policies/                          # Policy markdown files
│   ├── core-skills-mandate.md
│   ├── model-selection-enforcement.md
│   ├── common-failures-prevention.md
│   └── ... (12 policies total)
│
├── docs/                              # Java/Spring Boot documentation
│   ├── java-project-structure.md
│   ├── spring-cloud-config.md
│   ├── secret-management.md
│   ├── api-design-standards.md
│   ├── error-handling-standards.md
│   ├── security-best-practices.md
│   ├── logging-standards.md
│   ├── database-standards.md
│   └── git-and-context.md
│
├── workflows/                         # Workflow documentation
│   ├── SYSTEM-STRUCTURE-MAP.md
│   └── AUTOMATION-GAPS-ANALYSIS.md
│
├── logs/                              # System logs
│   ├── daemons/                       # Daemon-specific logs
│   ├── policy-hits.log                # Policy applications
│   ├── failures.log                   # Prevented failures
│   └── token-optimization.log         # Optimization events
│
├── sessions/                          # Project memories (PROTECTED)
│   └── <project-name>/
│       ├── project-summary.md         # Cumulative context
│       ├── session-*.md               # Individual sessions
│       └── archive/                   # Archived sessions
│
├── backups/                           # Rollback points
│
├── .state/                            # System state
│   ├── failure-kb.json                # Failure knowledge base
│   ├── user-preferences.json          # Learned preferences
│   └── cross-project-patterns.json    # Detected patterns
│
├── .pids/                             # Daemon PID files
│
└── scripts/                           # Python automation scripts
    ├── context-*.py                   # Context management
    ├── daemon-*.py                    # Daemon infrastructure
    ├── failure-*.py                   # Failure prevention
    ├── model-*.py                     # Model selection
    └── session-*.py                   # Session management
```

---

## 2.4 How It Works

### Execution Flow (Every Request)

```
1. Context Check (REQUIRED)
   ↓
   context-monitor-v2.py --current-status
   If >70%: Apply optimizations

2. Model Selection (REQUIRED)
   ↓
   model-selection-enforcer.py --analyze "message"
   Use recommended model

3. Skill Detection (OPTIONAL)
   ↓
   core-skills-enforcer.py --next-skill
   Execute if mandatory

4. Failure Prevention (BEFORE EVERY TOOL)
   ↓
   pre-execution-checker.py --tool {TOOL}
   Apply auto-fixes

5. Execute Task
   ↓
   Use optimized tool parameters
   Apply offset/limit/head_limit

6. Session Save (ON MILESTONES)
   ↓
   Auto-triggered by daemon

7. Git Auto-Commit (ON COMPLETION)
   ↓
   Auto-triggered by daemon

8. Logging (ALWAYS)
   ↓
   Log policy applications
```

### Background Automation

**Continuous (Every 5-20 min):**
- Context usage monitored
- Sessions auto-saved
- Preferences learned
- Skills suggested
- Token optimization applied

**Periodic (Daily/Weekly/Monthly):**
- Failures analyzed and learned
- Cross-project patterns detected
- Old sessions archived
- System health checked

**Event-Driven:**
- Git commits on completion
- Context cleanup on threshold
- Daemon auto-restart on failure

---

# 📜 3. Policies & Enforcement

## 3.1 Core Skills Mandate

**Version:** 4.7.0
**Status:** ✅ Active
**Purpose:** System-level enforcement of mandatory execution flow

### 5 Mandatory Skills (In Order)

1. **Context Management**
   - ALWAYS validate context first
   - Apply optimizations if >70%
   - Use cache/state/cleanup as needed

2. **Model Selection**
   - ALWAYS choose correct model
   - Haiku: Search/find (35-45%)
   - Sonnet: Implementation (50-60%)
   - Opus: Architecture (3-8%)

3. **Adaptive Skill Intelligence**
   - Auto-detect relevant skills
   - Auto-create if missing
   - Execute when appropriate

4. **Task Planning Intelligence**
   - Score complexity (0-10)
   - 0-3: Direct execution
   - 4-6: Ask user (plan mode?)
   - 7-10: Always use plan mode

5. **Phased Execution Intelligence**
   - Score task size (0-10)
   - 0-2: Single phase
   - 3-5: Ask user (phases?)
   - 6-10: Always use phases

### Critical Protection

**NEVER cleanup session memory:**
- `~/.claude/memory/sessions/**` - PROTECTED
- `~/.claude/memory/*.md` - PROTECTED
- `~/.claude/settings*.json` - PROTECTED
- `~/.claude/memory/logs/**` - PROTECTED

**Only cleanup conversation context (temporary data)**

---

## 3.2 Model Selection Enforcement

**Version:** 1.0.0
**Status:** ✅ Active
**Purpose:** Ensure correct model usage for cost optimization

### Quick Rules

| Task Type | Model | Trigger Words |
|-----------|-------|---------------|
| **Search/Find** | Haiku | "Find", "Search", "Where is", "Show me", "List all" |
| **Implementation** | Sonnet | "Fix", "Add", "Update", "Implement", "Write" |
| **Architecture** | Opus | "Should we use", "Design the", "Architecture for" |

### Model Distribution (Healthy)

- **Haiku:** 35-45% of requests
- **Sonnet:** 50-60% of requests
- **Opus:** 3-8% of requests

### Cost Impact Example

**Wrong (Sonnet for search):**
- Tokens: 5,000
- Cost: $0.015
- Time: 12 seconds

**Right (Haiku for search):**
- Tokens: 800
- Cost: $0.0006
- Time: 2 seconds

**Savings:** 96% cost reduction, 6x faster!

### Usage

```bash
# Analyze request and get model recommendation
python ~/.claude/memory/model-selection-enforcer.py --analyze "Find all Java files"

# Monitor model usage distribution
python ~/.claude/memory/model-selection-monitor.py
```

---

## 3.3 Common Failures Prevention

**Version:** 1.0.0
**Status:** ✅ Active
**Purpose:** Self-learning failure knowledge base

### How It Works

1. **Before Tool Execution:**
   - Check failure knowledge base
   - Match patterns (tool + context)
   - Auto-apply fixes if confidence ≥75%

2. **After Failure:**
   - Extract failure pattern
   - Save to knowledge base
   - Calculate confidence score

3. **Learning:**
   - Manual fixes logged
   - Patterns refined over time
   - Confidence increases with repetition

### Auto-Fixes Applied

**Bash Tool:**
- `del` → `rm`
- `copy` → `cp`
- `dir` → `ls`
- `xcopy` → `cp -r`
- `type` → `cat`
- Add quotes for paths with spaces
- Remove `-i` flag (interactive not supported)

**Edit Tool:**
- Strip line number prefixes automatically
- "42\t    code" becomes "    code"
- Ensure old_string is unique

**Read Tool:**
- Auto-add offset/limit for files >500 lines

**Grep Tool:**
- Auto-add head_limit (default: 100)
- Suggest multiline=true for cross-line patterns

**Git Operations:**
- Stage files before commit
- Check for .git directory
- Prevent force push to main/master

### Pattern Categories (15 Initial Patterns)

1. **Bash Command Errors**
2. **Edit Tool Errors**
3. **File Operations**
4. **Tool-Specific Issues**
5. **Git Operations**
6. **Platform-Specific Issues**

### Token Savings

**Per prevented failure:** 900-2900 tokens

**Example:**
- Edit tool failure (file read + retry + fix) = 2000 tokens
- Prevention check = 100 tokens
- **Savings = 1900 tokens (95%)**

### Usage

```bash
# Check before tool execution
python ~/.claude/memory/pre-execution-checker.py --tool Bash --context "del file.txt"

# Learn from manual fix
python ~/.claude/memory/failure-solution-learner.py --learn-from-fix \
    "Edit" "line prefix error" "stripped line numbers"

# View knowledge base stats
python ~/.claude/memory/failure-detector-v2.py --stats
```

---

## 3.4 Context-Session Integration

**Version:** 1.0.0
**Status:** ✅ Active
**Purpose:** Separate temporary vs persistent memory

### Protected Directories (NEVER Cleanup)

- `~/.claude/memory/sessions/**` - All session files
- `~/.claude/memory/*.md` - All policy files
- `~/.claude/settings*.json` - User settings
- `~/.claude/memory/logs/**` - All logs
- `~/.claude/memory/.state/**` - System state

### Safe to Cleanup (Temporary Data)

- Conversation history (in-context)
- MCP responses
- Temporary analysis
- Old file reads (not in cache)

### Context Thresholds

| Range | Status | Action |
|-------|--------|--------|
| <70% | 🟢 GREEN | Continue normally |
| 70-84% | 🟡 YELLOW | Use cache, offset/limit, head_limit |
| 85-89% | 🟠 ORANGE | Use session state, extract summaries |
| 90%+ | 🔴 RED | Save session, compact context |

### Session Memory Protection

**100% Protected:**
- Never deleted
- Never compacted
- Never sent to API for cleanup
- Always persisted locally

**Session files are your long-term memory!**

---

## 3.5 File Management Policy

**Version:** 2.0.0
**Status:** ✅ Active
**Purpose:** Clean working directory & intelligent large file handling

### Rules

1. **Temporary Files:** ALWAYS use system temp
   - Windows: `%TEMP%`
   - Linux/Mac: `/tmp`

2. **Documentation:** Single `README.md` preferred
   - Avoid multiple MD files in project root
   - Exception: docs/ folder for multi-page documentation

3. **Large Files (>500 lines):** Use smart strategies
   - Structure read first (100 lines)
   - Targeted section read (offset+limit)
   - Use Edit tool (not Write)
   - Token savings: 80-95%

### Intelligent Large File Strategy

**Step 1: Structure Read**
```bash
Read file_path="large-file.java" limit=100
```
- Understand imports, classes, structure
- Decide what sections to read

**Step 2: Targeted Read**
```bash
Read file_path="large-file.java" offset=200 limit=50
```
- Read only relevant sections

**Step 3: Smart Edit**
```bash
Edit file_path="large-file.java" old_string="..." new_string="..."
```
- Use Edit tool (doesn't require full read)
- Provide unique old_string

**Exception:** README >1000 lines → Propose docs/ split

---

## 3.6 Git Auto-Commit Policy

**Version:** 1.0.0
**Status:** ✅ Active
**Purpose:** Automatic commit/push on completion events

### Triggers (MANDATORY)

1. **Phase Completion**
   - When phase is marked complete
   - TaskUpdate status="completed"

2. **Todo Completion**
   - When all todos in phase complete

3. **Periodic Checkpoints**
   - Every 3-5 file changes
   - Every 30 minutes of active work

### Commit Message Format

```
✅ Phase [N] Complete: [Phase Name]

[Summary paragraph]

Changes:
- Key change 1
- Key change 2
- Key change 3

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

### Safety Rules

- **NEVER force push** (unless explicitly requested)
- **Respect hooks** (don't use --no-verify)
- **Inform user always** (transparent commits)
- **Check .git directory** before any git command

### Repository Creation Rules

- **Always "main" branch** (NEVER "master")
- **Always private** (unless explicitly public)
- **Complete workflow:** init → branch -M main → commit → push

---

## 3.7 Proactive Consultation Policy

**Version:** 1.0.0
**Status:** ✅ Active
**Purpose:** Transparent decision-making with user collaboration

### When to Ask

1. **Planning Decision (Complexity 4-6)**
   - Use plan mode or direct execution?
   - User knows best for medium complexity

2. **Phased Execution (Task Size 3-5)**
   - Single phase or multiple phases?
   - User preference matters

3. **Model/Approach Uncertainty**
   - Multiple valid approaches
   - User input needed

4. **Technology/Library Choice**
   - Redux vs Context vs Custom
   - JWT vs Session auth
   - MySQL vs PostgreSQL

### When NOT to Ask

- **Clear Scores (0-3 or 7-10)**
  - Obvious decision, don't waste time

- **User Already Specified**
  - Instructions are clear

- **Previous Decision in Session**
  - Check consultation-tracker.py first

- **Trivial Tasks**
  - Just do it

### Format

Use `AskUserQuestion` tool:
- Clear question
- 2-4 options
- Trade-offs explained
- Recommended option marked

### Usage

```bash
# Check if you should ask again
python ~/.claude/memory/consultation-tracker.py --check "planning_mode"

# Track user's choice
python ~/.claude/memory/consultation-tracker.py --track "planning_mode" "skip"
```

---

## 3.8 Session Memory Policy

**Version:** 1.0.0
**Status:** ✅ Active
**Purpose:** 100% local persistent memory across sessions

### How It Works

1. **At Session Start:**
   - Auto-load `project-summary.md`
   - Provides cumulative context

2. **During Session:**
   - Track key decisions
   - Track files modified
   - Track important context

3. **At Session End:**
   - Auto-save session summary
   - Update project-summary.md
   - Persist to disk

### File Structure

```
~/.claude/memory/sessions/<project-name>/
├── project-summary.md           # Cumulative context (ALWAYS loaded)
├── session-2026-02-15-09-30.md  # Individual session
├── session-2026-02-14-14-20.md
└── archive/
    └── 2026-01/
        └── sessions.tar.gz      # Archived sessions
```

### What to Capture

**Technical Decisions:**
- JWT vs Session authentication
- REST vs GraphQL
- MySQL vs PostgreSQL
- Redis for caching

**User Preferences (Project-Specific):**
- Skip tests for now
- Use Docker Compose
- Commit every phase

**Files Modified:**
- List of files changed
- Brief description of changes

**Pending Work:**
- TODO items
- Next steps
- Blockers

**Important Context:**
- Architecture decisions
- Design patterns used
- Trade-offs made

### Protected from Context Cleanup

**100% Protected:**
- Session files NEVER deleted by context cleanup
- Session files NEVER sent to API
- Session files only managed by session-pruning-daemon (monthly)

---

## 3.9 Session Pruning Policy

**Version:** 1.0.0
**Status:** ✅ Active
**Purpose:** Keep session memory clean and fast

### Rules

1. **Keep Last 10 Sessions Active**
   - Always available
   - Fast access
   - Recent context

2. **Archive Sessions >30 Days Old**
   - Except last 10 (always kept)
   - Compressed by month
   - Recoverable anytime

3. **Never Archive `project-summary.md`**
   - Always active
   - Always loaded at session start

### Archive Structure

```
~/.claude/memory/sessions/<project>/archive/
├── 2026-01/
│   └── sessions.tar.gz          # All January sessions
├── 2025-12/
│   └── sessions.tar.gz          # All December sessions
└── 2025-11/
    └── sessions.tar.gz          # All November sessions
```

**Compression Ratio:** ~10:1

### When to Run

**Automatic:** Monthly (via session-pruning-daemon)

**Manual:**
```bash
# View stats (no changes)
python ~/.claude/memory/archive-old-sessions.py --stats

# Perform archiving
python ~/.claude/memory/archive-old-sessions.py

# Recovery (if needed)
cd ~/.claude/memory/sessions/<project>/archive/2026-01/
tar -xzf sessions.tar.gz
```

---

## 3.10 User Preferences Policy

**Version:** 1.0.0
**Status:** ✅ Active
**Purpose:** Learn from repeated choices, stop asking same questions

### How It Works

1. **Track User Choices**
   - Every time user makes a choice
   - Store in preferences.json

2. **After 3 Occurrences**
   - Save as global preference
   - Apply automatically (4th time onwards)

3. **User Can Override**
   - Preferences are suggestions
   - User can always change

### Preference Categories

**Technology Preferences:**
- `api_style`: REST, GraphQL
- `testing`: unit, integration, e2e, skip
- `auth_method`: JWT, Session, OAuth
- `database`: MySQL, PostgreSQL, MongoDB

**Language Preferences:**
- `backend`: Java, Python, Node.js
- `frontend`: React, Angular, Vue
- `scripting`: Bash, Python, PowerShell

**Workflow Preferences:**
- `commit_style`: every-phase, every-file, manual
- `plan_mode`: always, ask, skip
- `phased_execution`: always, ask, skip

### Example Flow

**Times 1-3:**
```
Claude: "Skip tests for now?"
User: "Yes, skip tests"
[Tracked: testing → skip (count: 1/3)]
```

**Time 4+:**
```
[Auto-apply: testing → skip]
[Skip asking, just skip tests]
[User can override: "ab tests likh do"]
```

### Usage

```bash
# Check preference
python ~/.claude/memory/consultation-tracker.py --check "testing"

# Track choice
python ~/.claude/memory/consultation-tracker.py --track "testing" "skip"

# View all preferences
cat ~/.claude/memory/.state/user-preferences.json
```

---

## 3.11 Cross-Project Patterns Policy

**Version:** 1.0.0
**Status:** ✅ Active
**Purpose:** Detect implicit patterns across all projects

### What Gets Detected

**Technology Stack:**
- Languages (Java, TypeScript, Python)
- Frameworks (Spring Boot, React, Angular)
- Databases (MySQL, PostgreSQL, MongoDB, Redis)

**API Styles:**
- REST, GraphQL, gRPC

**Authentication Methods:**
- JWT, OAuth, Session-based

**Testing Approaches:**
- Unit, Integration, E2E, Skip

**DevOps Tools:**
- Docker, Kubernetes, Jenkins

### Confidence Levels

| Range | Level | Action |
|-------|-------|--------|
| 80-100% | **Strong** | High recommendation |
| 60-79% | **Moderate** | Solid suggestion |
| 50-59% | **Weak** | Mild suggestion |
| <50% | None | No pattern detected |

### Detection Rule

**Must appear in 3+ projects** to be considered a pattern

### Example

**Detected Pattern:**
```json
{
  "authentication": {
    "method": "JWT",
    "occurrences": 8,
    "total_projects": 10,
    "confidence": 80,
    "level": "strong"
  }
}
```

**Recommendation:**
"You've used JWT authentication in 8/10 projects. Recommend JWT for this project?"

### When to Use

**Monthly Analysis:**
```bash
python ~/.claude/memory/detect-patterns.py
```

**At Project Start:**
- Check patterns
- Apply recommendations
- User can override

---

## 3.12 Test Case Policy

**Version:** 1.0.0
**Status:** ✅ Active
**Purpose:** Define mandatory vs optional testing

### Testing Categories

1. **Mandatory (ALWAYS)**
   - Development testing (manual verification during development)
   - Manual testing (basic functionality check)

2. **Optional (ASK USER)**
   - Unit tests
   - Integration tests
   - E2E tests

### Default Recommendation

**Skip tests for now (add later)**

**Benefits:**
- 30-50% faster delivery
- Focus on features first
- Tests can be added incrementally
- User can request anytime: "ab tests likh do"

### When to Ask

- Phase/task completion
- New feature added
- During planning

### Ask Format

**Question:** "Unit/Integration tests likhein ya skip karein?"

**Options:**
1. Write all tests
2. Skip for now (Recommended)
3. Only critical tests

### User Can Override

**At any time:**
- "ab tests likh do" → Write tests
- "tests skip karo" → Skip tests
- "only unit tests" → Write unit tests only

---

# 🎯 4. Token Optimization

## 4.1 Optimization Overview

**Goal:** Reduce token consumption by 60-80% through intelligent optimization

### 15 Optimization Strategies

| # | Strategy | Savings | Status |
|---|----------|---------|--------|
| 1 | Smart File Summarization | 70-95% | ✅ Active |
| 2 | Tiered Caching | 30-40% | ✅ Active |
| 3 | Diff-Based Editing | 90% | ✅ Active |
| 4 | Smart Grep | 50-60% | ✅ Active |
| 5 | Response Compression | 20-30% | ✅ Active |
| 6 | AST Navigation | 80-95% | ✅ Active |
| 7 | Session State Aggressive Mode | 60-80% | ✅ Active |
| 8 | Batch File Operations | 40-50% | ✅ Active |
| 9 | MCP Response Filtering | 70-80% | ✅ Active |
| 10 | Conversation Pruning | 30-40% | ✅ Active |
| 11 | Smart Tool Selection | 50-70% | ✅ Active |
| 12 | Incremental Updates | 60-70% | ✅ Active |
| 13 | Response Templates | 10-20% | ✅ Active |
| 14 | Lazy Context Loading | 80-90% | ✅ Active |
| 15 | File Type Optimization | 60-80% | ✅ Active |

**Total Expected Savings:** 60-80%

**Real-World Impact:**
- Before: 200K budget → ~80 turns
- After: 200K budget → ~200+ turns
- **Feels like 500K+ budget!**

---

## 4.2 Smart File Summarization

**Savings:** 70-95%

### Strategy 1: Sandwich Read

**For files >500 lines:**
```
Read first 50 lines  (imports, structure)
Skip middle          (implementation details)
Read last 50 lines   (recent changes)
```

**Result:** 100 lines vs 1000 lines = 90% savings

### Strategy 2: AST-Based (For Code)

**Extract structure only:**
- Package/module
- Classes/interfaces
- Methods/functions
- Skip method bodies

**Example:**
```
Package: com.techdeveloper.auth
Classes: [AuthController, AuthService, AuthHelper]
Methods: [login(), register(), validateToken()]
```

**Result:** ~50 tokens vs 2000 tokens = 97% savings

### Usage

```python
python ~/.claude/memory/smart-file-summarizer.py --file "path/file.java" --strategy auto
```

**Strategy Options:**
- `auto` - Auto-detect best strategy
- `sandwich` - First/last N lines
- `ast` - AST-based extraction
- `headers` - Headers/signatures only

---

## 4.3 Tiered Caching Strategy

**Savings:** 30-40%

### Cache Tiers

**TIER 1: HOT (5+ accesses in last hour)**
- Keep full content in cache
- No re-reads needed
- Examples: application.yml, constants, main configs

**TIER 2: WARM (3-4 accesses)**
- Keep summary in cache (first 50 lines)
- Re-read only on explicit request
- Examples: Service implementations, controllers

**TIER 3: COLD (1-2 accesses)**
- No caching
- Read fresh each time
- Examples: One-time file reads

### Usage

```python
# Before reading file
python ~/.claude/memory/tiered-cache.py --get-file "path/file.java"

# If cache_hit=true: Use cached content
# If cache_hit=false: Read from disk, then cache

# After reading
python ~/.claude/memory/tiered-cache.py --set-file "path/file.java" --content "..."
```

### Benefits

- **HOT files:** 100% savings (no re-reads)
- **WARM files:** 80% savings (summary only)
- **COLD files:** 0% savings (fresh reads)
- **Overall:** 30-40% savings on repeated operations

---

## 4.4 Diff-Based Editing

**Savings:** 90%

### Problem

❌ **After Edit, showing full file = 2000 tokens wasted**

### Solution

✅ **Show only changed lines = 20 tokens (95% savings!)**

### Format

```
... (lines 1-42 unchanged)
43: const oldValue = 8080;
44: const newValue = 3000;  ← Changed
45: export { newValue };
... (lines 46-500 unchanged)

✅ filepath:44 → Port changed
```

### Rules

- Show 3 lines context before/after change
- Mark changed line with `←`
- Brief summary: `✅ {file}:{line} → {what_changed}`
- Total: ~20 lines instead of 500

### Exception

**Show full file ONLY when:**
- User explicitly requests it
- First time creating file
- Major refactoring (>50% changed)

---

## 4.5 Smart Grep Optimization

**Savings:** 50-60%

### Progressive Refinement Strategy

**Step 1: Conservative search (low head_limit)**
```bash
Grep pattern="function" head_limit=10
```

**Step 2: If too broad, refine pattern**
```bash
Grep pattern="function.*User" head_limit=20
```

**Step 3: Use file type filters**
```bash
Grep pattern="function" type="ts" head_limit=30
```

**Step 4: Use glob for specific dirs**
```bash
Grep pattern="function" glob="src/services/**" head_limit=20
```

### Benefits

- Start: 10 results (40 tokens)
- vs Always: 100 results (400 tokens)
- **Savings: 90% on most searches**

### Rule

**NEVER use head_limit >100 without specific reason**

---

## 4.6 AST Navigation

**Savings:** 80-95%

### Problem

❌ **Reading full file just to find method names = 2000 tokens**

### Solution

✅ **AST extraction = 100 tokens (95% savings!)**

### Supported Languages

**Java:**
```python
python ~/.claude/memory/ast-code-navigator.py --file UserService.java
```

**Output:**
```json
{
  "package": "com.techdeveloper.auth",
  "classes": ["UserService"],
  "methods": [
    "login(String, String): boolean",
    "register(UserForm): User",
    "validateToken(String): boolean"
  ]
}
```

**TypeScript:**
- Imports, classes, interfaces, functions

**Python:**
- Imports, classes, functions

### Then Read Specific Method

```bash
Grep "public User register" -A 20 UserService.java
```

**Read just the method, not whole file!**

---

## 4.7 All 15 Optimization Strategies

### 1. Smart File Summarization (70-95%)
- Sandwich read (first/last N lines)
- AST extraction (structure only)
- Headers only

### 2. Tiered Caching (30-40%)
- HOT: Full content cached
- WARM: Summary cached
- COLD: No caching

### 3. Diff-Based Editing (90%)
- Show only changed lines
- 3 lines context before/after

### 4. Smart Grep (50-60%)
- Start with head_limit=10
- Progressive refinement
- File type filters

### 5. Response Compression (20-30%)
- Ultra-brief templates
- Action-first responses
- ✅ File created (not "I have successfully created the file...")

### 6. AST Navigation (80-95%)
- Extract structure only
- Skip method bodies
- Read specific methods when needed

### 7. Session State Aggressive Mode (60-80%)
- Reference session files instead of repeating
- "See session-2026-02-09.md, tasks #1-5"

### 8. Batch File Operations (40-50%)
- Get structure first (tree/glob)
- Read only needed files
- Combine multiple reads

### 9. MCP Response Filtering (70-80%)
- Extract essentials only
- Status, error, first N items
- Count remaining, don't load all

### 10. Conversation Pruning (30-40%)
- Auto-prune completed tasks when context >70%
- Keep only current active task

### 11. Smart Tool Selection (50-70%)
- tree -L 2 (NOT ls -R)
- Glob "**/*ClassName*.java" (NOT Grep)
- Read offset=0 limit=20 (NOT full file)

### 12. Incremental Updates (60-70%)
- Show only deltas on iterative work
- Round 1: Full implementation
- Round 2+: Only changes

### 13. Response Templates (10-20%)
- ✅ filepath (Created)
- ✅ filepath:line → change (Edited)
- ❌ filepath (Deleted)

### 14. Lazy Context Loading (80-90%)
- Don't preload what MIGHT be needed
- Load only what IS needed
- Reference files instead of loading

### 15. File Type Optimization (60-80%)
- JSON/YAML: jq/yq (80% savings)
- Logs: tail + grep (90% savings)
- Markdown: grep ^## (70% savings)
- Code: AST or grep structure (80% savings)
- Binary: Metadata only (99% savings)

---

# ☕ 5. Java Spring Boot Standards

## 5.1 Project Structure

**Base Package Convention:**
```
com.techdeveloper.${projectname}
```

**Example:**
```
com.techdeveloper.m2surgricals
com.techdeveloper.auth
```

---

## 5.2 Package Conventions

| Package | Purpose | Notes |
|---------|---------|-------|
| `controller` | REST endpoints | `@RestController` |
| `dto` | Response objects | Data Transfer Objects |
| `form` | Request objects | `@RequestBody`, extends `ValidationMessageConstants` |
| `constants` | All constants/enums | No magic strings |
| `services` | Service interfaces ONLY | Public interfaces |
| `services.impl` | Package-private implementations | Extends helper, implements interface |
| `services.helper` | Abstract helper classes | Extends `ServiceMessageConstants` |
| `entity` | Database entities | JPA/MongoDB entities |
| `repository` | JPA/MongoDB repositories | Data access layer |

---

## 5.3 Mandatory Patterns

### Form Classes Must Extend `ValidationMessageConstants`

```java
public class RegisterUserForm extends ValidationMessageConstants {
    @NotBlank(message = EMAIL_REQUIRED)
    @Email(message = EMAIL_INVALID)
    private String email;

    @NotBlank(message = PASSWORD_REQUIRED)
    @Pattern(regexp = PASSWORD_PATTERN, message = PASSWORD_INVALID)
    private String password;
}
```

### Service Implementation Pattern

**Helper extends ServiceMessageConstants:**
```java
public abstract class UserServiceHelper extends ServiceMessageConstants {
    // Common helper methods
}
```

**Impl extends Helper, implements Interface (package-private):**
```java
@Service
class UserServiceImpl extends UserServiceHelper implements UserService {
    @Override
    @Transactional
    public ApiResponseDto<UserDTO> register(RegisterUserForm form) {
        // Implementation
    }
}
```

### ALL Responses Use `ApiResponseDto<T>`

```java
// Void response (add/update/delete)
ApiResponseDto<Void>

// Single object response
ApiResponseDto<UserDTO>

// List response
ApiResponseDto<List<UserDTO>>

// Paginated response
ApiResponseDto<Page<UserDTO>>
```

**Never return bare objects!**

---

## 5.4 Agent Collaboration Strategy

### Smart Collaboration Approach

**Don't force agents to follow all standards - take their logic and apply our structure**

### Workflow

```
User Request
    ↓
Agent Provides Logic
    ↓
Apply to OUR Structure
    ↓
Final Implementation
```

### Quality Checklist (Before Submitting Code)

- ✅ Is `ApiResponseDto<T>` used?
- ✅ Are DTOs and Forms separate?
- ✅ Are all messages in constants?
- ✅ Is service impl package-private?
- ✅ Does service impl extend helper?
- ✅ Is ValidationSequence used?
- ✅ Are transactions used for writes?

---

# 🔧 6. Configuration Management

## 6.1 Spring Cloud Config Server

### Configuration Structure

```
configurations/
├── application.yml                        # Global (ALL services)
├── {project}/common/*.yml                 # Project common
└── {project}/services/{service-name}.yml  # Service-specific
```

### Configuration Hierarchy (Merge Order)

1. **Global** (`application.yml`)
2. **Project-level** (`{project}/common/*.yml`)
3. **Service-specific** (`{project}/services/{service-name}.yml`)

**Later files override earlier files**

---

## 6.2 Secret Management

### System Components

- **Secret Manager:** Port 1002
- **Project Management:** Port 8109
- **Client SDK:** Maven dependency

### How It Works

```
1. Microservice Startup
   ↓
2. SecretManagerEnvironmentPostProcessor Triggered
   ↓
3. Resolve Project ID
   ↓
4. Fetch Secrets from Secret Manager
   ↓
5. Inject into Spring Environment as properties
   ↓
6. Config Server resolves ${SECRET_KEY} placeholders
   ↓
7. Application starts with secrets available
```

### Best Practices

**DO:**
- ✅ Store ALL sensitive data in Secret Manager
- ✅ Use placeholder syntax: `${SECRET_KEY}`

**DON'T:**
- ❌ Hardcode secrets in code/configs
- ❌ Commit secrets to Git
- ❌ Log secrets

---

## 6.3 Configuration Hierarchy

### Microservice application.yml (ONLY THIS!)

```yaml
spring:
  application:
    name: service-name
  config:
    import: "configserver:http://localhost:8888"
  cloud:
    config:
      fail-fast: true
      retry:
        enabled: true

secret-manager:
  client:
    enabled: true
    project-name: "project-name"
```

### CRITICAL RULES

**❌ NEVER add in microservice's application.yml:**
- Redis config (in config server)
- Feign config (in config server)
- Database config (in config server)
- Email config (in config server)
- Port numbers (in config server)

**✅ ALWAYS check config server FIRST** before adding any configuration

**✅ Use .yml files ONLY** (NEVER .properties)

---

# 🌐 7. API & Web Standards

## 7.1 API Design Standards

### HTTP Methods

| Method | Purpose | Request Body | Response Body |
|--------|---------|--------------|---------------|
| GET | Read/Retrieve | No | Yes |
| POST | Create | Yes | Yes |
| PUT | Update (full) | Yes | Yes |
| PATCH | Update (partial) | Yes | Yes |
| DELETE | Delete | No | Optional |

### URL Structure

```
/{api-version}/{resource}/{id}/{sub-resource}
```

**Correct Examples:**
- `GET /api/v1/users`
- `GET /api/v1/users/123`
- `POST /api/v1/users`
- `PUT /api/v1/users/123`
- `DELETE /api/v1/users/123`
- `GET /api/v1/users/123/orders`

### Naming Conventions

- **Use plural nouns:** `/users`, `/products`, `/orders`
- **Use kebab-case:** `/user-profiles`, `/order-items`
- **No verbs:** `/users` NOT `/getUsers`
- **No file extensions:** `/users` NOT `/users.json`

---

## 7.2 Error Handling Standards

### Global Exception Handler (MANDATORY)

```java
@ControllerAdvice
@Slf4j
public class GlobalExceptionHandler {
    @ExceptionHandler(ResourceNotFoundException.class)
    public ResponseEntity<ApiResponseDto<Void>> handleResourceNotFound(
            ResourceNotFoundException ex) {
        log.error("Resource not found: {}", ex.getMessage());
        return ResponseEntity
            .status(HttpStatus.NOT_FOUND)
            .body(ApiResponseDto.error(ex.getMessage()));
    }

    @ExceptionHandler(DuplicateResourceException.class)
    public ResponseEntity<ApiResponseDto<Void>> handleDuplicateResource(
            DuplicateResourceException ex) {
        log.error("Duplicate resource: {}", ex.getMessage());
        return ResponseEntity
            .status(HttpStatus.CONFLICT)
            .body(ApiResponseDto.error(ex.getMessage()));
    }

    @ExceptionHandler(ValidationException.class)
    public ResponseEntity<ApiResponseDto<Map<String, String>>> handleValidation(
            ValidationException ex) {
        log.error("Validation failed: {}", ex.getMessage());
        return ResponseEntity
            .status(HttpStatus.BAD_REQUEST)
            .body(ApiResponseDto.error(ex.getMessage(), ex.getErrors()));
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<ApiResponseDto<Void>> handleGeneric(Exception ex) {
        log.error("Unexpected error", ex);
        return ResponseEntity
            .status(HttpStatus.INTERNAL_SERVER_ERROR)
            .body(ApiResponseDto.error("An unexpected error occurred"));
    }
}
```

### Custom Exception Hierarchy

```
BaseException (abstract)
├── ResourceNotFoundException (404)
├── DuplicateResourceException (409)
├── ValidationException (400)
├── UnauthorizedException (401)
└── ForbiddenException (403)
```

### Best Practices

**DO:**
- ✅ Throw exceptions in service layer
- ✅ Let GlobalExceptionHandler catch them
- ✅ Log exceptions with proper context
- ✅ Return consistent error format

**DON'T:**
- ❌ Catch exceptions in controllers
- ❌ Return null or empty objects
- ❌ Expose stack traces to clients
- ❌ Use generic Exception for business logic

---

## 7.3 Response Format

### Success Response

```json
{
  "status": true,
  "message": "User created successfully",
  "data": {
    "id": "123",
    "email": "user@example.com",
    "name": "John Doe"
  }
}
```

### Error Response

```json
{
  "status": false,
  "message": "Email already exists",
  "data": null
}
```

### Validation Error Response

```json
{
  "status": false,
  "message": "Validation failed",
  "data": {
    "email": "Email is required",
    "password": "Password must be at least 8 characters"
  }
}
```

---

## 7.4 HTTP Status Codes

| Code | Meaning | When to Use |
|------|---------|-------------|
| 200 | OK | Successful GET, PUT, PATCH, DELETE |
| 201 | Created | Successful POST |
| 204 | No Content | Successful DELETE (no response body) |
| 400 | Bad Request | Validation errors, malformed request |
| 401 | Unauthorized | Authentication failed or missing |
| 403 | Forbidden | Authenticated but not authorized |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | Duplicate resource, state conflict |
| 500 | Internal Server Error | Unexpected server-side errors |

---

# 🔐 8. Security Best Practices

## 8.1 Secret Management

### NEVER Hardcode Secrets

**❌ WRONG:**
```java
String dbPassword = "admin123";
String apiKey = "sk-1234567890";
String jwtSecret = "mySecretKey";
```

**✅ CORRECT:**
```java
@Value("${db.password}")  // From Secret Manager
private String dbPassword;

@Value("${api.key}")
private String apiKey;

@Value("${jwt.secret}")
private String jwtSecret;
```

---

## 8.2 Password Security

### ALWAYS Hash Passwords

**❌ WRONG:**
```java
user.setPassword(form.getPassword());  // Plain text!
```

**✅ CORRECT:**
```java
@Bean
public PasswordEncoder passwordEncoder() {
    return new BCryptPasswordEncoder(12);  // Strong hashing
}

// Usage
user.setPassword(passwordEncoder.encode(form.getPassword()));

// Verification
if (passwordEncoder.matches(rawPassword, user.getPassword())) {
    // Correct password
}
```

---

## 8.3 Input Validation

### ALWAYS Validate User Inputs

```java
public class RegisterUserForm extends ValidationMessageConstants {
    @NotBlank(message = EMAIL_REQUIRED)
    @Email(message = EMAIL_INVALID)
    @Size(max = 100, message = EMAIL_TOO_LONG)
    private String email;

    @NotBlank(message = PASSWORD_REQUIRED)
    @Pattern(
        regexp = "^(?=.*[0-9])(?=.*[a-z])(?=.*[A-Z])(?=.*[@#$%^&+=])(?=\\S+$).{8,}$",
        message = PASSWORD_PATTERN
    )
    private String password;

    @NotBlank(message = NAME_REQUIRED)
    @Size(min = 2, max = 50, message = NAME_LENGTH)
    private String name;
}
```

**Controller:**
```java
@PostMapping("/register")
public ResponseEntity<ApiResponseDto<UserDTO>> register(
        @Valid @RequestBody RegisterUserForm form) {
    // Validation happens automatically
}
```

---

## 8.4 SQL Injection Prevention

### ALWAYS Use Parameterized Queries

**❌ WRONG:**
```java
String query = "SELECT * FROM users WHERE email = '" + email + "'";
entityManager.createNativeQuery(query);
```

**✅ CORRECT:**
```java
@Query("SELECT u FROM User u WHERE u.email = :email")
Optional<User> findByEmail(@Param("email") String email);

// Or native query
@Query(value = "SELECT * FROM users WHERE email = :email", nativeQuery = true)
Optional<User> findByEmailNative(@Param("email") String email);
```

---

## 8.5 XSS Prevention

### Sanitize HTML Inputs

```java
import org.jsoup.Jsoup;
import org.jsoup.safety.Safelist;

public static String sanitizeHtml(String input) {
    if (input == null) return null;
    return Jsoup.clean(input, Safelist.none());
}

// Usage
String safeContent = sanitizeHtml(userInput);
```

---

## 8.6 Security Checklist

### ALWAYS DO

1. ✅ Store secrets in Secret Manager
2. ✅ Hash passwords with BCrypt (strength 12)
3. ✅ Validate ALL user inputs
4. ✅ Use parameterized queries
5. ✅ Sanitize HTML inputs
6. ✅ Validate file uploads (type, size, content)
7. ✅ Implement rate limiting
8. ✅ Use HTTPS in production
9. ✅ Set secure headers (CORS, CSP, X-Frame-Options)
10. ✅ Log security events

### NEVER DO

1. ❌ Hardcode secrets
2. ❌ Store passwords in plain text
3. ❌ Trust user input without validation
4. ❌ Concatenate SQL strings
5. ❌ Log sensitive data (passwords, tokens, credit cards)
6. ❌ Expose stack traces to clients
7. ❌ Use default credentials
8. ❌ Disable CSRF protection
9. ❌ Allow unrestricted file uploads
10. ❌ Use weak encryption algorithms

---

# 🗄️ 9. Database Standards

## 9.1 Entity Design Pattern

```java
@Entity
@Table(name = "users")
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class User {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "email", nullable = false, unique = true, length = 100)
    private String email;

    @Column(name = "password", nullable = false)
    private String password;

    @Column(name = "name", nullable = false, length = 50)
    private String name;

    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @Column(name = "updated_at")
    private LocalDateTime updatedAt;

    @PrePersist
    protected void onCreate() {
        createdAt = LocalDateTime.now();
    }

    @PreUpdate
    protected void onUpdate() {
        updatedAt = LocalDateTime.now();
    }
}
```

---

## 9.2 Naming Conventions

- **Table names:** snake_case, plural (`users`, `order_items`, `user_profiles`)
- **Column names:** snake_case (`first_name`, `created_at`, `is_active`)
- **Foreign keys:** `{table}_id` (`user_id`, `order_id`, `product_id`)
- **Junction tables:** `{table1}_{table2}` (`users_roles`, `products_categories`)

---

## 9.3 Relationships

### One-to-Many

```java
@Entity
public class User {
    @OneToMany(mappedBy = "user", cascade = CascadeType.ALL, orphanRemoval = true)
    private List<Order> orders = new ArrayList<>();
}

@Entity
public class Order {
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id", nullable = false)
    private User user;
}
```

### Many-to-Many

```java
@Entity
public class Product {
    @ManyToMany
    @JoinTable(
        name = "products_categories",
        joinColumns = @JoinColumn(name = "product_id"),
        inverseJoinColumns = @JoinColumn(name = "category_id")
    )
    private Set<Category> categories = new HashSet<>();
}

@Entity
public class Category {
    @ManyToMany(mappedBy = "categories")
    private Set<Product> products = new HashSet<>();
}
```

---

## 9.4 Repository Pattern

```java
@Repository
public interface UserRepository extends JpaRepository<User, Long> {
    Optional<User> findByEmail(String email);

    boolean existsByEmail(String email);

    @Query("SELECT u FROM User u WHERE u.email = :email AND u.status = :status")
    Optional<User> findByEmailAndStatus(
        @Param("email") String email,
        @Param("status") UserStatus status
    );

    @Query("SELECT u FROM User u LEFT JOIN FETCH u.orders WHERE u.id = :id")
    Optional<User> findByIdWithOrders(@Param("id") Long id);
}
```

---

## 9.5 Transaction Management

```java
@Service
public class OrderServiceImpl implements OrderService {
    @Override
    @Transactional  // ✅ Use for write operations
    public ApiResponseDto<OrderDTO> createOrder(CreateOrderForm form) {
        // All operations in one transaction
        // Rollback on exception
    }

    @Override
    @Transactional(readOnly = true)  // ✅ Read-only for performance
    public ApiResponseDto<OrderDTO> getOrderById(Long id) {
        // Read operation
        // No write allowed
    }
}
```

---

## 9.6 Query Optimization

### Avoid N+1 Problem

**❌ WRONG - N+1 Problem:**
```java
@Query("SELECT u FROM User u WHERE u.status = :status")
List<User> findByStatus(@Param("status") UserStatus status);

// Later accessing orders causes N+1
for (User user : users) {
    user.getOrders();  // Separate query for each user!
}
```

**✅ CORRECT - Use JOIN FETCH:**
```java
@Query("SELECT u FROM User u LEFT JOIN FETCH u.orders WHERE u.status = :status")
List<User> findByStatusWithOrders(@Param("status") UserStatus status);

// Orders loaded in single query!
```

### Use Pagination for Large Datasets

```java
@Query("SELECT u FROM User u WHERE u.status = :status")
Page<User> findByStatus(@Param("status") UserStatus status, Pageable pageable);

// Usage
Pageable pageable = PageRequest.of(0, 20, Sort.by("createdAt").descending());
Page<User> users = userRepository.findByStatus(UserStatus.ACTIVE, pageable);
```

### Best Practices

**DO:**
1. ✅ Use `@Transactional` for write operations
2. ✅ Use `@Transactional(readOnly = true)` for read operations
3. ✅ Use indexes on frequently queried columns
4. ✅ Use pagination for large datasets
5. ✅ Use `FetchType.LAZY` for relationships (default)
6. ✅ Use JOIN FETCH to avoid N+1 problem

**DON'T:**
1. ❌ Use `FetchType.EAGER` unless necessary
2. ❌ Load entire tables without pagination
3. ❌ Concatenate SQL strings (use parameterized queries)
4. ❌ Perform database operations in loops
5. ❌ Expose entities directly (use DTOs)

---

# 📝 10. Logging Standards

## 10.1 Log Levels

| Level | When to Use | Examples |
|-------|-------------|----------|
| **ERROR** | System errors, exceptions | Database connection failed, Payment processing error |
| **WARN** | Potential issues, recoverable errors | Deprecated API used, High memory usage |
| **INFO** | Important business events | User logged in, Order created, Payment successful |
| **DEBUG** | Detailed flow (dev/staging only) | Method entry/exit, Variable values |

---

## 10.2 Best Practices

### DO: Use Parameterized Logging

**✅ CORRECT:**
```java
log.info("User {} logged in from IP {}", userId, ipAddress);
log.error("Payment failed for order: {} - Reason: {}", orderId, reason);
```

**❌ WRONG:**
```java
log.info("User " + userId + " logged in");  // String concatenation!
```

### DO: Log Business Events

```java
// User registration
log.info("User registered - Email: {}", maskEmail(email));

// Order creation
log.info("Creating order for user: {}", userId);
log.info("Order created - OrderID: {}, Total: {}", orderId, total);

// Payment processing
log.info("Processing payment for order: {}", orderId);
log.info("Payment successful - TransactionID: {}", transactionId);
```

### DO: Log Exceptions with Context

```java
try {
    processPayment(orderId);
} catch (PaymentException e) {
    log.error("Payment failed for order: {} - Reason: {}",
        orderId, e.getMessage(), e);
    throw e;
}
```

---

## 10.3 Sensitive Data Masking

### DON'T: Log Sensitive Data

**❌ NEVER LOG THESE:**
```java
log.info("User password: {}", password);           // NO!
log.info("Credit card: {}", cardNumber);          // NO!
log.info("JWT token: {}", token);                 // NO!
log.info("API key: {}", apiKey);                  // NO!
log.info("SSN: {}", ssn);                         // NO!
```

### DO: Mask Sensitive Data

```java
public static String maskEmail(String email) {
    String[] parts = email.split("@");
    return parts[0].charAt(0) + "***@" + parts[1];
}

public static String maskCreditCard(String cardNumber) {
    return "**** **** **** " + cardNumber.substring(cardNumber.length() - 4);
}

// Usage
log.info("User registered - Email: {}", maskEmail(email));
log.info("Payment processed - Card: {}", maskCreditCard(cardNumber));
```

---

# 🔄 11. Git Management

## 11.1 Repository Rules

1. **Always "main" branch** (NEVER "master")
2. **Always private by default** (public only if explicitly requested)
3. **Complete workflow:** init → branch -M main → commit → push

### Repository Creation

```bash
# Initialize
git init

# Create main branch (NOT master)
git branch -M main

# Add remote
git remote add origin <url>

# First commit
git add .
git commit -m "Initial commit"

# Push
git push -u origin main
```

---

## 11.2 Auto-Commit Triggers

**Automatic commits triggered on:**

1. ✅ Task Completed (TaskUpdate status="completed")
2. ✅ Phase Completed
3. ✅ User says "done"/"finished"/"complete"
4. ✅ 10+ files modified
5. ✅ 30+ minutes elapsed since last commit

---

## 11.3 Commit Message Format

```
✅ Phase [N] Complete: [Phase Name]

[Summary paragraph describing what was accomplished]

Changes:
- Key change 1
- Key change 2
- Key change 3

Files Modified:
- path/to/file1.java
- path/to/file2.ts

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

**Example:**
```
✅ Phase 1 Complete: User Authentication

Implemented JWT-based authentication with login and register endpoints.
Added password encryption using BCrypt and token generation.

Changes:
- Created AuthController with login/register endpoints
- Implemented AuthService with JWT token generation
- Added UserRepository with email lookup
- Created validation for RegisterUserForm

Files Modified:
- backend/auth-service/src/main/java/controller/AuthController.java
- backend/auth-service/src/main/java/services/impl/AuthServiceImpl.java
- backend/auth-service/src/main/java/form/RegisterUserForm.java

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

---

# 📊 12. Monitoring & Health

## 12.1 Dashboard

### View Comprehensive Dashboard

```bash
bash ~/.claude/memory/dashboard-v2.sh
```

**Sections:**
1. 🤖 Daemon Health (8/8 or 9/9 running)
2. 📊 Context Status (usage & recommendations)
3. 🛡️ Failure Prevention (KB stats)
4. 🎯 Model Usage (distribution & compliance)
5. 💬 Consultation Preferences (learned patterns)
6. ✅ Core Skills Compliance (execution tracking)
7. 📝 Recent Activity (last 5 policy hits)
8. 💯 Overall Health Score (system-wide health)

---

## 12.2 Daemon Status

### Check All Daemons

```bash
python ~/.claude/memory/daemon-manager.py --status-all
```

**Expected Output:**
```
Daemon Status:
  context-daemon: RUNNING (PID: 12345)
  session-auto-save-daemon: RUNNING (PID: 12346)
  preference-auto-tracker: RUNNING (PID: 12347)
  skill-auto-suggester: RUNNING (PID: 12348)
  commit-daemon: RUNNING (PID: 12349)
  session-pruning-daemon: RUNNING (PID: 12350)
  pattern-detection-daemon: RUNNING (PID: 12351)
  failure-prevention-daemon: RUNNING (PID: 12352)
  token-optimization-daemon: RUNNING (PID: 12353)

Status: 9/9 daemons running ✅
```

### Restart Specific Daemon

```bash
python ~/.claude/memory/daemon-manager.py --restart context-daemon
```

### Restart All Daemons

```bash
bash ~/.claude/memory/startup-hook.sh
```

---

## 12.3 Logs

### Log Locations

```
~/.claude/memory/logs/
├── daemons/                       # Daemon-specific logs
│   ├── context-daemon.log
│   ├── session-auto-save.log
│   ├── preference-tracker.log
│   ├── skill-suggester.log
│   ├── commit-daemon.log
│   ├── session-pruning.log
│   ├── pattern-detection.log
│   ├── failure-prevention.log
│   └── token-optimization.log
│
├── policy-hits.log                # All policy applications
├── failures.log                   # Prevented failures
├── token-optimization.log         # Optimization events
└── context-pruning.log           # Context alerts
```

### Watch Live Logs

```bash
# Watch all policy applications
tail -f ~/.claude/memory/logs/policy-hits.log

# Watch specific daemon
tail -f ~/.claude/memory/logs/daemons/context-daemon.log

# Watch failures
tail -f ~/.claude/memory/logs/failures.log
```

---

## 12.4 Health Checks

### Daily Health Check

```bash
bash ~/.claude/memory/daily-health-check.sh
```

**Checks:**
- All daemons running
- Context usage OK
- No critical failures
- Model distribution healthy

### Weekly Health Check

```bash
bash ~/.claude/memory/weekly-health-check.sh
```

**Additional Checks:**
- Session pruning needed?
- Cross-project patterns detected?
- Failure KB growing?
- Token savings on track?

### Full System Verification

```bash
bash ~/.claude/memory/verify-system.sh
```

**Comprehensive Checks:**
- Phase 1: Context Optimization (7 checks)
- Phase 2: Daemon Infrastructure (8 checks)
- Phase 3: Failure Prevention (6 checks)
- Phase 4: Policy Automation (5 checks)
- Phase 5: Integration (3 checks)

---

# 🛠️ 13. Troubleshooting

## 13.1 Common Issues

### Issue: Daemons Not Running

**Symptom:** dashboard shows <8 daemons running

**Solution:**
```bash
# Restart all daemons
bash ~/.claude/memory/startup-hook.sh

# Check status
python ~/.claude/memory/daemon-manager.py --status-all
```

### Issue: High Context Usage

**Symptom:** Context >85% frequently

**Solution:**
```bash
# Check current status
python ~/.claude/memory/context-monitor-v2.py --current-status

# Apply aggressive optimization
# (Automatically suggested by context-monitor)
```

### Issue: Failure Prevention Not Working

**Symptom:** Same failures repeating

**Solution:**
```bash
# Check failure KB
python ~/.claude/memory/failure-detector-v2.py --stats

# Learn from fix
python ~/.claude/memory/failure-solution-learner.py --learn-from-fix \
    "Edit" "line prefix error" "stripped line numbers"
```

---

## 13.2 Daemon Problems

### Daemon Crashed

```bash
# Check which daemon crashed
python ~/.claude/memory/daemon-manager.py --status-all

# Restart specific daemon
python ~/.claude/memory/daemon-manager.py --restart <daemon-name>

# Or restart all
bash ~/.claude/memory/startup-hook.sh
```

### Daemon Logs Show Errors

```bash
# View daemon log
tail -50 ~/.claude/memory/logs/daemons/<daemon-name>.log

# Check for common errors:
# - Permission denied → Run as admin
# - Port already in use → Kill other process
# - File not found → Verify installation
```

---

## 13.3 Context Issues

### Context Keeps Growing

**Check what's consuming context:**
```bash
python ~/.claude/memory/context-monitor-v2.py --current-status
```

**Apply optimizations:**
- Use cache for repeated files
- Use session state for historical references
- Use offset/limit for large files
- Use head_limit for searches

### Session Files Too Large

```bash
# Archive old sessions
python ~/.claude/memory/archive-old-sessions.py --stats
python ~/.claude/memory/archive-old-sessions.py
```

---

## 13.4 Rollback

### Rollback to Previous State

```bash
python ~/.claude/memory/rollback.py
```

**This will:**
- Restore backups from `~/.claude/memory/backups/`
- Revert to last known good state
- Preserve session files (NEVER deleted)

---

# 📚 14. Reference

## 14.1 All Scripts

### Context Management
- `pre-execution-optimizer.py` - Optimize tool parameters
- `context-extractor.py` - Extract essential info
- `context-cache.py` - Tiered caching
- `session-state.py` - External memory
- `context-monitor-v2.py` - Real-time monitoring
- `auto-context-pruner.py` - Auto cleanup

### Daemon Infrastructure
- `daemon-manager.py` - Manage daemons
- `context-daemon.py` - Monitor context
- `session-auto-save-daemon.py` - Auto-save sessions
- `preference-auto-tracker.py` - Learn preferences
- `skill-auto-suggester.py` - Suggest skills
- `commit-daemon.py` - Auto-commit
- `session-pruning-daemon.py` - Clean sessions
- `pattern-detection-daemon.py` - Detect patterns
- `failure-prevention-daemon.py` - Learn failures
- `token-optimization-daemon.py` - Optimize tokens

### Failure Prevention
- `failure-detector-v2.py` - Detect failures
- `pre-execution-checker.py` - Check before execution
- `failure-pattern-extractor.py` - Extract patterns
- `failure-solution-learner.py` - Learn fixes

### Policy Automation
- `model-selection-enforcer.py` - Enforce model selection
- `model-selection-monitor.py` - Monitor usage
- `consultation-tracker.py` - Track decisions
- `core-skills-enforcer.py` - Enforce skills

### Session Management
- `auto-save-session.py` - Save sessions
- `archive-old-sessions.py` - Archive sessions
- `detect-patterns.py` - Cross-project patterns

### Optimization
- `smart-file-summarizer.py` - Summarize files
- `tiered-cache.py` - Tiered caching
- `ast-code-navigator.py` - AST navigation
- `auto-tool-wrapper.py` - Tool optimization
- `auto-post-processor.py` - Post-processing

---

## 14.2 All Policies

1. `core-skills-mandate.md` - Mandatory execution flow
2. `model-selection-enforcement.md` - Correct model usage
3. `common-failures-prevention.md` - Failure prevention KB
4. `CONTEXT-SESSION-INTEGRATION.md` - Context vs session memory
5. `file-management-policy.md` - Clean directory, large files
6. `git-auto-commit-policy.md` - Auto-commit triggers
7. `proactive-consultation-policy.md` - When to ask user
8. `session-memory-policy.md` - Persistent memory
9. `session-pruning-policy.md` - Clean old sessions
10. `user-preferences-policy.md` - Learn preferences
11. `cross-project-patterns-policy.md` - Detect patterns
12. `test-case-policy.md` - Testing strategy

---

## 14.3 All Documentation

### Java Spring Boot
1. `java-project-structure.md` - Package conventions, patterns
2. `java-agent-strategy.md` - Agent collaboration
3. `spring-cloud-config.md` - Config server setup
4. `secret-management.md` - Secret manager details

### API & Web
5. `api-design-standards.md` - REST conventions
6. `error-handling-standards.md` - Exception handling

### Security & Database
7. `security-best-practices.md` - Security guidelines
8. `logging-standards.md` - Logging best practices
9. `database-standards.md` - Database patterns

### Git & Context
10. `git-and-context.md` - Git rules, context monitoring

---

## 14.4 Command Cheat Sheet

### Daily Operations

```bash
# Session start (MANDATORY)
bash ~/.claude/memory/session-start.sh

# View dashboard
bash ~/.claude/memory/dashboard-v2.sh

# Check daemons
python ~/.claude/memory/daemon-manager.py --status-all

# Check context
python ~/.claude/memory/context-monitor-v2.py --current-status

# Watch logs
tail -f ~/.claude/memory/logs/policy-hits.log
```

### Monthly Maintenance

```bash
# Detect patterns
python ~/.claude/memory/detect-patterns.py

# Archive sessions
python ~/.claude/memory/archive-old-sessions.py

# Weekly health
bash ~/.claude/memory/weekly-health-check.sh

# Check conflicts
bash ~/.claude/memory/check-conflicts.sh
```

### Troubleshooting

```bash
# Restart daemons
bash ~/.claude/memory/startup-hook.sh

# Verify system
bash ~/.claude/memory/verify-system.sh

# Run tests
python ~/.claude/memory/test-all-phases.py

# Rollback
python ~/.claude/memory/rollback.py
```

### Context Optimization

```bash
# Check file cache
python ~/.claude/memory/context-cache.py --get-file "path/file.java"

# Set file cache
python ~/.claude/memory/context-cache.py --set-file "path/file.java" --summary '{...}'

# Session state
python ~/.claude/memory/session-state.py --summary

# Smart summarization
python ~/.claude/memory/smart-file-summarizer.py --file "path/file.java" --strategy auto

# AST navigation
python ~/.claude/memory/ast-code-navigator.py --file "path/file.java"
```

### Failure Prevention

```bash
# Pre-execution check
python ~/.claude/memory/pre-execution-checker.py --tool Bash --context "..."

# Learn from fix
python ~/.claude/memory/failure-solution-learner.py --learn-from-fix "tool" "failure" "fix"

# View KB stats
python ~/.claude/memory/failure-detector-v2.py --stats
```

### Model Selection

```bash
# Analyze request
python ~/.claude/memory/model-selection-enforcer.py --analyze "your request"

# Monitor usage
python ~/.claude/memory/model-selection-monitor.py
```

### Preferences

```bash
# Check preference
python ~/.claude/memory/consultation-tracker.py --check "testing"

# Track choice
python ~/.claude/memory/consultation-tracker.py --track "testing" "skip"

# View all preferences
cat ~/.claude/memory/.state/user-preferences.json
```

---

# 🎉 Summary

## System Status

**Version:** 2.2.0
**Status:** 🟢 FULLY OPERATIONAL
**Daemons:** 8/8 or 9/9 running
**Automation Level:** 100%
**Token Savings:** 60-80% automatic
**Manual Steps Required:** 0

## Key Features

✅ **Context Optimization** - 60-80% token savings
✅ **Failure Prevention** - Self-learning knowledge base
✅ **Model Selection** - Automatic cost optimization
✅ **Session Memory** - 100% local persistent memory
✅ **User Preferences** - Learn and apply automatically
✅ **Cross-Project Patterns** - Detect and suggest
✅ **Git Auto-Commit** - Automatic on completion
✅ **Java Standards** - Complete Spring Boot conventions
✅ **Security** - Best practices enforced
✅ **Windows Auto-Start** - Daemons start on login

## Real-World Impact

**Before Automation:**
- 200K budget → ~80 conversation turns
- Frequent manual optimization needed
- Context cleanup every 50-60 turns

**After Automation:**
- 200K budget → ~200+ conversation turns
- Zero manual intervention
- Context rarely needs cleanup (auto-managed)
- **Feels like 500K+ budget!**

---

**Location:** `C:\Users\techd\.claude\memory\MASTER-README.md`

**This document consolidates ALL policies, documentation, and system architecture into one comprehensive guide with proper indexing for easy navigation.**

---

**For Questions or Issues:**
- Check troubleshooting section (13.x)
- View dashboard: `bash ~/.claude/memory/dashboard-v2.sh`
- Check logs: `tail -f ~/.claude/memory/logs/policy-hits.log`
- Run health check: `bash ~/.claude/memory/verify-system.sh`

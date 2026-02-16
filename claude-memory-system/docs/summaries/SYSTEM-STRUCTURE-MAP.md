# Memory System - Complete Structure Map

## Version: 2.0.0 🎉
## Purpose: Complete reference for where everything is and how it's connected
## Last Updated: 2026-01-28
## Status: ✅ 100% AUTOMATION COMPLETE (8/8 systems fully automated!)

---

## 📂 Directory Structure Overview

```
~/.claude/
├── CLAUDE.md                           # Global instructions (MAIN ENTRY POINT)
├── memory/
│   ├── workflows/                      # System documentation & workflows
│   │   ├── SYSTEM-STRUCTURE-MAP.md    # THIS FILE (structure reference)
│   │   └── AUTOMATION-GAPS-ANALYSIS.md # Complete automation gaps analysis 🆕
│   │
│   ├── sessions/                       # Persistent project memory (PROTECTED!)
│   │   ├── project-name-1/
│   │   │   ├── project-summary.md     # Auto-loaded at session start
│   │   │   └── session-YYYY-MM-DD-HH-MM.md
│   │   └── project-name-2/
│   │       └── ...
│   │
│   ├── logs/                           # Execution logs (PROTECTED!)
│   │   ├── policy-hits.log            # Policy applications
│   │   ├── failures.log               # Prevented failures
│   │   ├── policy-counters.txt        # Execution counts
│   │   └── process-execution.log      # System events
│   │
│   ├── templates/                      # Template files
│   │   └── session-summary-template.md
│   │
│   ├── backups/                        # System backups
│   │   └── ...
│   │
│   ├── routing/                        # Request routing logic
│   │   └── ...
│   │
│   ├── __pycache__/                    # Python cache (auto-generated)
│   │
│   │
│   ├── ─────────────────────────────────────────────────────────────
│   │   POLICY FILES (Rules & Guidelines)
│   ├── ─────────────────────────────────────────────────────────────
│   │
│   ├── core-skills-mandate.md          # Core skill hierarchy (context → model → planning → execution)
│   ├── model-selection-enforcement.md  # Model selection guide (Haiku/Sonnet/Opus)
│   ├── proactive-consultation-policy.md # Ask user for decisions with reasoning
│   ├── session-memory-policy.md        # Persistent memory across sessions
│   ├── common-failures-prevention.md   # Known failure patterns (Tier 1: Global)
│   ├── FAILURE-LEARNING-SYSTEM.md      # Self-improving failure prevention (v2.0)
│   ├── file-management-policy.md       # Temp files, doc consolidation, large file handling
│   ├── git-auto-commit-policy.md       # Auto-commit rules on phase/todo completion
│   ├── test-case-policy.md             # User preference for test coverage
│   ├── user-preferences-policy.md      # Global preference learning & application
│   ├── session-pruning-policy.md       # Long-term session memory archival & cleanup
│   ├── cross-project-patterns-policy.md # Pattern detection across all projects
│   ├── adaptive-skill-registry.md      # Auto-created skills/agents tracking
│   ├── CONTEXT-SESSION-INTEGRATION.md  # Context cleanup + session memory (protection rules)
│   ├── SKILL-REGISTRY-SYSTEM.md        # Skill detection & auto-suggestion system
│   │
│   │
│   ├── ─────────────────────────────────────────────────────────────
│   │   AUTOMATION SCRIPTS (Working Code)
│   ├── ─────────────────────────────────────────────────────────────
│   │
│   │   SESSION MEMORY SCRIPTS
│   ├── session-start.sh                # Auto-load session context
│   ├── check-incomplete-work.py        # Proactive resume prompts
│   │
│   │   USER PREFERENCES SCRIPTS
│   ├── load-preferences.py             # Load user preferences by category
│   ├── track-preference.py             # Track user choices (threshold-based learning)
│   ├── apply-preference.sh             # Apply learned preferences
│   │
│   │   SESSION PRUNING SCRIPTS
│   ├── archive-old-sessions.py         # Archive sessions older than 30 days
│   │
│   │   CROSS-PROJECT PATTERNS SCRIPTS
│   ├── detect-patterns.py              # Detect patterns across all projects
│   ├── apply-patterns.py               # Suggest patterns based on history
│   │
│   │   SKILL DETECTION & REGISTRY SCRIPTS
│   ├── skill-detector.py               # Auto-detect relevant skills from user message
│   ├── skill-manager.py                # Manage skill registry
│   ├── auto-register-skills.py         # Auto-register skills from ~/.claude/skills/
│   ├── test-all-skills.py              # Test skill detection
│   │
│   │   MIGRATION & SETUP SCRIPTS
│   ├── migrate-local-claude.py         # Migrate local CLAUDE.md to session memory
│   ├── migrate-local-claude.sh         # Bash wrapper for migration
│   ├── initialize-system.sh            # Initialize memory system
│   ├── load-policies.sh                # Load all policies
│   ├── memory-loader.sh                # Load memory system
│   │
│   │   FAILURE LEARNING SCRIPTS
│   ├── update-failure-kb.py            # Update failure knowledge base
│   │
│   │   MONITORING & MAINTENANCE SCRIPTS
│   ├── dashboard.sh                    # System dashboard
│   ├── policy-tracker.sh               # Track policy executions
│   ├── rollback.py                     # Rollback system changes
│   ├── check-conflicts.sh              # Check for system conflicts
│   ├── verify-integration.sh           # Verify context-session integration
│   ├── verify-setup.sh                 # Verify system setup
│   │
│   │   CONTEXT MANAGEMENT SCRIPTS (✅ COMPLETE + AUTOMATED!)
│   ├── context-estimator.py            # ✅ Estimate context % from metrics
│   ├── context-daemon.py               # ✅ Background daemon (monitors every 10 min)
│   ├── auto-save-session.py            # ✅ Auto-save session before cleanup
│   ├── monitor-context.py              # ✅ Monitor context percentage & recommendations
│   ├── smart-cleanup.py                # ✅ Policy-based context cleanup with session protection
│   ├── protect-session-memory.py       # ✅ Verify session memory protection status
│   ├── trigger-context-cleanup.sh      # ✅ Manual trigger cleanup at thresholds
│   ├── startup-hook.sh                 # ✅ Auto-start ALL 8 daemons on session start (Steps 1-10)
│   │
│   │   SESSION MEMORY AUTO-SAVE SCRIPTS (✅ COMPLETE + AUTOMATED!)
│   ├── session-save-triggers.py        # ✅ Detect save triggers (files, commits, time, decisions)
│   ├── session-auto-save-daemon.py     # ✅ Background daemon (monitors every 15 min)
│   │
│   │   USER PREFERENCES AUTO-TRACKING SCRIPTS (✅ COMPLETE + AUTOMATED!)
│   ├── preference-detector.py          # ✅ Auto-detect preferences from logs
│   ├── preference-auto-tracker.py      # ✅ Background daemon (monitors every 20 min)
│   │
│   │   SKILL AUTO-SUGGESTION SCRIPTS (✅ COMPLETE + AUTOMATED!)
│   ├── skill-auto-suggester.py         # ✅ Background daemon (monitors every 5 min)
│   │
│   │   GIT AUTO-COMMIT SCRIPTS (✅ COMPLETE + AUTOMATED!)
│   ├── auto-commit-detector.py         # ✅ Detect commit triggers (10+ files, 30+ min, phases)
│   ├── auto-commit.py                  # ✅ Execute git commits with smart messages
│   ├── commit-daemon.py                # ✅ Background daemon (monitors every 15 min)
│   │
│   │   SESSION PRUNING SCRIPTS (✅ COMPLETE + AUTOMATED!)
│   ├── session-pruning-daemon.py       # ✅ Background daemon (monitors daily, 30-day intervals)
│   │
│   │   CROSS-PROJECT PATTERNS SCRIPTS (✅ COMPLETE + AUTOMATED!)
│   ├── pattern-detection-daemon.py     # ✅ Background daemon (monitors weekly, 30-day intervals)
│   │
│   │   FAILURE LEARNING SCRIPTS (✅ COMPLETE + AUTOMATED!)
│   ├── failure-detector.py             # ✅ Detect failure patterns from logs
│   ├── failure-learner.py              # ✅ Learn from failures and update KB
│   ├── failure-prevention-daemon.py    # ✅ Background daemon (monitors every 6 hours)
│   │
│   │
│   ├── ─────────────────────────────────────────────────────────────
│   │   DATA FILES (Persistent Storage)
│   ├── ─────────────────────────────────────────────────────────────
│   │
│   ├── skills-registry.json            # Skill metadata & usage stats
│   ├── user-preferences.json           # Learned user preferences
│   ├── cross-project-patterns.json     # Detected patterns across projects
│   ├── system-prompt.txt               # System prompt template
│   │
│   │
│   ├── ─────────────────────────────────────────────────────────────
│   │   QUICK START GUIDES (User Documentation)
│   ├── ─────────────────────────────────────────────────────────────
│   │
│   ├── README.md                       # Main system documentation
│   ├── HOW-IT-WORKS.md                 # Complete system guide & troubleshooting
│   ├── MEMORY-SYSTEM-QUICKSTART.md     # Quick start guide
│   ├── SESSION-RESUME-GUIDE.md         # Session resume feature guide
│   ├── SESSION-PRUNING-QUICKSTART.md   # Session pruning guide
│   ├── USER-PREFERENCES-QUICKSTART.md  # User preferences guide
│   ├── SKILL-REGISTRY-QUICK-START.md   # Skill registry guide
│   ├── CROSS-PROJECT-PATTERNS-QUICKSTART.md # Cross-project patterns guide
│   ├── FAILURE-LEARNING-QUICK-START.md # Failure learning guide
│   ├── AUTO-REGISTRATION-FIX.md        # Auto-registration troubleshooting
│   ├── LOCAL-CLAUDE-MIGRATION.md       # Local CLAUDE.md migration guide
│   ├── SKILL-DETECTION-IMPROVEMENTS.md # Skill detection improvements
│   ├── SKILL-DETECTION-TEST-RESULTS.md # Skill detection test results
│   │
│   │
│   └── ─────────────────────────────────────────────────────────────
│       IMPLEMENTATION SUMMARIES (Development Logs)
│       ─────────────────────────────────────────────────────────────
│
│       IMPLEMENTATION-SUMMARY-USER-PREFERENCES.md
│       IMPLEMENTATION-SUMMARY-SESSION-PRUNING.md
│       IMPLEMENTATION-SUMMARY-CROSS-PROJECT-PATTERNS.md
│       IMPLEMENTATION-SUMMARY-LOW-PRIORITY-FEATURES.md
│       SKILL-REGISTRY-IMPLEMENTATION-SUMMARY.md
│
│
└── skills/
    ├── ─────────────────────────────────────────────────────────────
    │   CORE SKILLS (User-Invocable)
    ├── ─────────────────────────────────────────────────────────────
    │
    ├── context-management-core/
    │   └── skill.md                    # Context validation, navigation, optimization
    │
    ├── model-selection-core/
    │   └── skill.md                    # Model selection rules (Haiku/Sonnet/Opus)
    │
    ├── adaptive-skill-intelligence/
    │   └── skill.md                    # Auto-create skills/agents on-the-fly
    │
    ├── memory-enforcer/
    │   └── skill.md                    # Enforce memory system policies
    │
    ├── phased-execution-intelligence/
    │   └── skill.md                    # Break tasks into phases
    │
    ├── task-planning-intelligence/
    │   └── skill.md                    # Plan mode intelligence
    │
    ├── ─────────────────────────────────────────────────────────────
    │   BACKEND SKILLS
    ├── ─────────────────────────────────────────────────────────────
    │
    ├── backend/
    │   ├── java-design-patterns-core/
    │   ├── java-spring-boot-microservices/
    │   ├── rdbms-core/
    │   ├── nosql-core/
    │   └── spring-boot-design-patterns-core/
    │
    ├── ─────────────────────────────────────────────────────────────
    │   FRONTEND SKILLS
    ├── ─────────────────────────────────────────────────────────────
    │
    ├── frontend/
    │   ├── animations-core/
    │   ├── css-core/
    │   └── seo-keyword-research-core/
    │
    ├── ─────────────────────────────────────────────────────────────
    │   DEVOPS SKILLS
    ├── ─────────────────────────────────────────────────────────────
    │
    ├── devops/
    │   ├── docker/
    │   ├── kubernetes/
    │   └── jenkins-pipeline/
    │
    ├── ─────────────────────────────────────────────────────────────
    │   MOBILE SKILLS
    ├── ─────────────────────────────────────────────────────────────
    │
    ├── mobile/
    │   └── ...
    │
    ├── ─────────────────────────────────────────────────────────────
    │   PAYMENT INTEGRATION SKILLS (Auto-created)
    ├── ─────────────────────────────────────────────────────────────
    │
    ├── payment-integration-java.md
    ├── payment-integration-python.md
    ├── payment-integration-typescript.md
    ├── PAYMENT-INTEGRATION-GUIDE.md
    │
    ├── ─────────────────────────────────────────────────────────────
    │   JAVAFX SKILLS (Auto-created)
    ├── ─────────────────────────────────────────────────────────────
    │
    ├── javafx-ide-designer.md
    └── JAVAFX-IDE-QUICK-START.md
```

---

## 🔄 System Integration Map

### 1. Session Start Flow (Auto-Load Context)

```
Session Starts
    ↓
Step 0: migrate-local-claude.py
    ↓ (Check & migrate local CLAUDE.md if exists)
    ↓
Step 0.5: auto-register-skills.py
    ↓ (Auto-discover & register new skills)
    ↓
Step 1: Detect PROJECT_NAME
    ↓ (basename "$PWD")
    ↓
Step 2: Check for previous context
    ↓ (~/.claude/memory/sessions/$PROJECT_NAME/project-summary.md)
    ↓
Step 3: If exists → Auto-load silently
    │         (Read project-summary.md)
    │         (Load all context: decisions, preferences, architecture)
    │
    └─ If not exists → New project, proceed normally
    ↓
Step 3.5: check-incomplete-work.py
    ↓ (Check for incomplete work from last session)
    ↓ (If found → Show resume prompt)
    ↓
Ready to work! ✅
```

**Files Involved:**
- `~/.claude/memory/migrate-local-claude.py`
- `~/.claude/memory/auto-register-skills.py`
- `~/.claude/memory/check-incomplete-work.py`
- `~/.claude/memory/sessions/$PROJECT_NAME/project-summary.md`

**Logging:**
```bash
echo "[$(date '+%Y-%m-%d %H:%M:%S')] session-memory | context-loaded | $PROJECT_NAME" >> ~/.claude/memory/logs/policy-hits.log
```

---

### 2. Skill Detection Flow (Proactive Suggestions)

```
User Message Received
    ↓
skill-detector.py "user message"
    ↓ (Analyze keywords, context, intent)
    ↓ (Match against skills-registry.json)
    ↓
Relevant skills found?
    │
    ├─ YES → Suggest to user (with confidence score)
    │         Update usage stats in skills-registry.json
    │
    └─ NO → Continue normally
```

**Files Involved:**
- `~/.claude/memory/skill-detector.py`
- `~/.claude/memory/skills-registry.json`

**Example:**
```bash
python ~/.claude/memory/skill-detector.py "implement JWT authentication"
# Output: payment-integration-java (score=0.85), rdbms-core (score=0.72)
```

---

### 3. User Preferences Flow (Learn & Apply)

```
User makes a choice
    ↓
track-preference.py <category> <value>
    ↓ (Track choice count)
    ↓
Threshold reached? (3+ times)
    │
    ├─ YES → Save to user-preferences.json
    │         (Preference learned! Apply globally)
    │
    └─ NO → Continue tracking
    ↓
Next time same category question:
    ↓
load-preferences.py <category>
    ↓ (Check if preference exists)
    ↓
Preference found?
    │
    ├─ YES → Apply automatically (user can override)
    │
    └─ NO → Ask user
```

**Files Involved:**
- `~/.claude/memory/track-preference.py`
- `~/.claude/memory/load-preferences.py`
- `~/.claude/memory/user-preferences.json`

**Example:**
```bash
# Track user choice
python ~/.claude/memory/track-preference.py "testing" "skip"

# Load preference
python ~/.claude/memory/load-preferences.py "testing"
# Output: skip (if learned)
```

---

### 4. Session End Flow (Auto-Save Summary)

```
Milestone Completed or Session Ending
    ↓
Generate session summary
    │ - What was done
    │ - Key decisions
    │ - Files modified
    │ - User preferences
    │ - Pending work
    ↓
Offer to save?
    │
    ├─ User agrees (y)
    │   ↓
    │   Save to: sessions/$PROJECT_NAME/session-YYYY-MM-DD-HH-MM.md
    │   Update: sessions/$PROJECT_NAME/project-summary.md
    │   ↓
    │   Log: policy-hits.log
    │
    └─ User declines (n)
        ↓
        Skip save
```

**Files Involved:**
- `~/.claude/memory/sessions/$PROJECT_NAME/session-YYYY-MM-DD-HH-MM.md`
- `~/.claude/memory/sessions/$PROJECT_NAME/project-summary.md`
- `~/.claude/memory/logs/policy-hits.log`

**Logging:**
```bash
echo "[$(date '+%Y-%m-%d %H:%M:%S')] session-memory | summary-saved | $PROJECT_NAME" >> ~/.claude/memory/logs/policy-hits.log
```

---

### 5. Session Pruning Flow (Archive Old Sessions)

```
Monthly Maintenance (Manual or Cron)
    ↓
archive-old-sessions.py
    ↓ (Find sessions older than 30 days)
    ↓ (Keep last 10 active sessions)
    ↓
Archive by month:
    ~/.claude/memory/sessions/archive/YYYY-MM/sessions.tar.gz
    ↓
Delete archived originals
    ↓
Log archival
```

**Files Involved:**
- `~/.claude/memory/archive-old-sessions.py`
- `~/.claude/memory/sessions/archive/YYYY-MM/sessions.tar.gz`

**Usage:**
```bash
# Archive old sessions
python ~/.claude/memory/archive-old-sessions.py

# Check stats
python ~/.claude/memory/archive-old-sessions.py --stats
```

---

### 6. Cross-Project Patterns Flow (Learn from Yourself)

```
Monthly Pattern Detection (Manual)
    ↓
detect-patterns.py
    ↓ (Analyze all projects in sessions/)
    ↓ (Detect common tech stacks, auth methods, API styles)
    ↓
Save patterns:
    cross-project-patterns.json
    ↓
When user asks about new feature:
    ↓
apply-patterns.py <topic>
    ↓ (Check if pattern exists)
    ↓
Suggest approach based on history:
    "In 75% of your projects, you used JWT authentication"
```

**Files Involved:**
- `~/.claude/memory/detect-patterns.py`
- `~/.claude/memory/apply-patterns.py`
- `~/.claude/memory/cross-project-patterns.json`

**Usage:**
```bash
# Detect patterns (run monthly)
python ~/.claude/memory/detect-patterns.py

# Apply patterns
python ~/.claude/memory/apply-patterns.py "authentication"
# Output: JWT detected in 75% of projects (6/8)
```

---

### 7. Context Management Flow (✅ FULLY AUTOMATED!)

```
Session Starts
    ↓
startup-hook.sh (auto-runs)
    ↓
Context Daemon Started (background process)
    ↓
    ↓ ◄──────────────┐
    ↓                 │
Every 10 minutes:     │ (Loop)
    ↓                 │
context-estimator.py  │
    ↓ (Estimate context % from metrics) │
    ↓                 │
Threshold reached?    │
    │                 │
    ├─ < 70% → Continue monitoring ──┘
    │
    ├─ 70-84% → LIGHT CLEANUP
    │   ↓
    │   auto-save-session.py (save session first!)
    │   ↓
    │   smart-cleanup.py --level light
    │   ↓ (Remove old file reads, MCP responses)
    │   ↓ (Protect session memory - ALWAYS!)
    │   ↓
    │   Context drops to ~50%
    │   ↓
    │   protect-session-memory.py (verify protection)
    │   ↓
    │   Continue monitoring ──────────┘
    │
    ├─ 85-89% → MODERATE CLEANUP
    │   ↓
    │   auto-save-session.py (save session first!)
    │   ↓
    │   smart-cleanup.py --level moderate
    │   ↓ (Compress completed work, keep active tasks)
    │   ↓ (Protect session memory - ALWAYS!)
    │   ↓
    │   Context drops to ~40%
    │   ↓
    │   protect-session-memory.py (verify protection)
    │   ↓
    │   Continue monitoring ──────────┘
    │
    └─ 90%+ → AGGRESSIVE CLEANUP
        ↓
        auto-save-session.py (CRITICAL: save now!)
        ↓
        smart-cleanup.py --level aggressive
        ↓ (Keep ONLY current task)
        ↓ (Protect session memory - ALWAYS!)
        ↓
        Context drops to ~10%
        ↓
        protect-session-memory.py (verify protection)
        ↓
        Continue monitoring ──────────┘

Daemon runs continuously until stopped or session ends
```

**Files Involved:**

**Automation Layer:**
- ✅ `~/.claude/memory/context-estimator.py` - Estimate context % from metrics
- ✅ `~/.claude/memory/context-daemon.py` - Background daemon (auto-monitoring)
- ✅ `~/.claude/memory/auto-save-session.py` - Auto-save before cleanup
- ✅ `~/.claude/memory/startup-hook.sh` - Auto-start on session start

**Core Scripts:**
- ✅ `~/.claude/memory/monitor-context.py` - Monitor & provide recommendations
- ✅ `~/.claude/memory/smart-cleanup.py` - Policy-based cleanup strategy
- ✅ `~/.claude/memory/protect-session-memory.py` - Verify session protection
- ✅ `~/.claude/memory/trigger-context-cleanup.sh` - Manual orchestrator

**Integration:**
- Uses: `~/.claude/memory/CONTEXT-SESSION-INTEGRATION.md` (policy)
- Uses: `~/.claude/skills/context-management-core/skill.md` (rules)
- Protects: `~/.claude/memory/sessions/**/*.md` (NEVER cleanup!)
- Saves to: `sessions/$PROJECT_NAME/session-YYYY-MM-DD.md` (auto-saved)
- Updates: `sessions/$PROJECT_NAME/project-summary.md` (cumulative)
- Logs to: `~/.claude/memory/logs/policy-hits.log`
- Logs to: `~/.claude/memory/logs/context-daemon.log`

**Data Files:**
- `.context-estimate` - Current context estimate (JSON)
- `.context-daemon.pid` - Daemon PID file

**Full Automation Features:**
✅ **Auto-detection** - Estimates context % from observable metrics
✅ **Continuous monitoring** - Background daemon checks every N minutes
✅ **Auto-trigger** - Cleanup triggered automatically at thresholds
✅ **Auto-save** - Session saved before every cleanup
✅ **Session protection** - Memory files verified & protected
✅ **Policy-based** - Smart cleanup following defined strategies
✅ **Logging** - All actions logged for audit trail

---

## 🎉 Complete Automation Overview (ALL 8 SYSTEMS - 100%)

### System 1: Context Management ✅ (startup-hook.sh Step 3)
**Auto-starts:** Yes | **Interval:** 10 minutes | **Daemon:** context-daemon.py

**Flow:**
```
Every 10 minutes → Estimate context % → Check thresholds → Auto-cleanup (70%, 85%, 90%)
```

**Features:**
- ✅ Auto-detect context % from metrics
- ✅ Background monitoring every 10 minutes
- ✅ Auto-trigger cleanup at thresholds
- ✅ Auto-save session before cleanup
- ✅ Session memory always protected

---

### System 2: Session Memory ✅ (startup-hook.sh Step 4)
**Auto-starts:** Yes | **Interval:** 15 minutes | **Daemon:** session-auto-save-daemon.py

**Flow:**
```
Every 15 minutes → Check triggers (5+ files, commits, 60+ min, decisions) → Auto-save
```

**Features:**
- ✅ Auto-load context at session start
- ✅ Auto-register skills
- ✅ Auto-check incomplete work
- ✅ Auto-save on triggers
- ✅ No manual confirmation needed

---

### System 3: User Preferences ✅ (startup-hook.sh Step 5)
**Auto-starts:** Yes | **Interval:** 20 minutes | **Daemon:** preference-auto-tracker.py

**Flow:**
```
Every 20 minutes → Detect preferences from logs → Track choices → Auto-learn after 3x
```

**Features:**
- ✅ Auto-detect preferences from conversation
- ✅ Auto-track user choices
- ✅ Auto-learn after 3 occurrences
- ✅ Auto-apply learned preferences
- ✅ Categories: testing, API style, commit frequency, etc.

---

### System 4: Skill Detection ✅ (startup-hook.sh Step 6)
**Auto-starts:** Yes | **Interval:** 5 minutes | **Daemon:** skill-auto-suggester.py

**Flow:**
```
Every 5 minutes → Monitor user messages → Auto-analyze intent → Suggest relevant skills
```

**Features:**
- ✅ Auto-register skills at session start
- ✅ Auto-monitor user messages
- ✅ Auto-suggest skills proactively
- ✅ Auto-update usage statistics
- ✅ No manual script calls needed

---

### System 5: Git Auto-Commit ✅ (startup-hook.sh Step 7)
**Auto-starts:** Yes | **Interval:** 15 minutes | **Daemon:** commit-daemon.py

**Flow:**
```
Every 15 minutes → Check triggers (10+ files, 30+ min, phase/todo) → Auto-commit
```

**Features:**
- ✅ Auto-detect commit triggers
- ✅ Auto-generate smart commit messages
- ✅ Auto-stage and commit changes
- ✅ Optional auto-push to remote
- ✅ Milestone signal detection
- ✅ 15-minute cooldown between commits

---

### System 6: Session Pruning ✅ (startup-hook.sh Step 8)
**Auto-starts:** Yes | **Interval:** 30 days (daily checks) | **Daemon:** session-pruning-daemon.py

**Flow:**
```
Daily checks → Count sessions → Trigger if 100+ sessions OR 30+ days → Archive old sessions
```

**Features:**
- ✅ Auto-monitor total session count
- ✅ Auto-trigger on thresholds (100+ sessions, 30+ days)
- ✅ Archive sessions older than 30 days
- ✅ Keep last 10 sessions always
- ✅ Compress by month (tar.gz)
- ✅ Keeps memory fast and clean

---

### System 7: Cross-Project Patterns ✅ (startup-hook.sh Step 9)
**Auto-starts:** Yes | **Interval:** 30 days (weekly checks) | **Daemon:** pattern-detection-daemon.py

**Flow:**
```
Weekly checks → Count projects → Trigger if 5+ new projects OR 30+ days → Detect patterns
```

**Features:**
- ✅ Auto-monitor project count
- ✅ Auto-trigger on thresholds (5+ new projects, 30+ days)
- ✅ Detect patterns automatically (languages, frameworks, auth methods)
- ✅ Learn from work history
- ✅ Suggest approaches based on patterns
- ✅ Minimum 3 projects required

---

### System 8: Failure Learning ✅ (startup-hook.sh Step 10)
**Auto-starts:** Yes | **Interval:** 6 hours | **Daemon:** failure-prevention-daemon.py

**Flow:**
```
Every 6 hours → Detect failures → Analyze patterns → Learn & update KB → Prevent future
```

**Features:**
- ✅ Auto-detect failure patterns from logs (12+ types)
- ✅ Auto-analyze and learn from failures
- ✅ Pattern progression: monitoring → learning → confirmed → global
- ✅ Auto-update knowledge base (project → global)
- ✅ Proactive failure prevention
- ✅ Confidence scoring system
- ✅ Promotion check every 24 hours

---

## 📊 Complete Daemon Status Commands

```bash
# Check all daemons at once
python ~/.claude/memory/context-daemon.py --status                # System 1
python ~/.claude/memory/session-auto-save-daemon.py --status      # System 2
python ~/.claude/memory/preference-auto-tracker.py --status       # System 3
python ~/.claude/memory/skill-auto-suggester.py --status          # System 4
python ~/.claude/memory/commit-daemon.py --status                 # System 5
python ~/.claude/memory/session-pruning-daemon.py --status        # System 6
python ~/.claude/memory/pattern-detection-daemon.py --status      # System 7
python ~/.claude/memory/failure-prevention-daemon.py --status     # System 8
```

---

## 🛡️ Protected Directories (NEVER AUTO-CLEANUP)

**CRITICAL:** These paths are SACRED and NEVER touched by any auto-cleanup:

1. **`~/.claude/memory/sessions/**`**
   - All project session directories
   - All `project-summary.md` files
   - All `session-*.md` files
   - All backups in `sessions/**/backups/`

2. **`~/.claude/memory/*.md`**
   - All policy files
   - All documentation files
   - All guide files

3. **`~/.claude/memory/logs/**`**
   - All log files
   - Policy execution history
   - System status logs

4. **`~/.claude/settings*.json`**
   - User configuration files
   - Local settings overrides

5. **`~/.claude/*.md`**
   - CLAUDE.md (global instructions)
   - README files
   - Documentation

---

## 📊 Monitoring & Logs

### Policy Execution Logs

**Location:** `~/.claude/memory/logs/policy-hits.log`

**Format:**
```
[YYYY-MM-DD HH:MM:SS] <policy-name> | <action> | <context>
```

**Example:**
```
[2026-01-27 08:15:23] session-memory | context-loaded | techdeveloper-ui
[2026-01-27 08:16:45] skill-detection | suggested | payment-integration-java | score=0.90
[2026-01-27 08:20:12] user-preferences | applied | testing=skip
[2026-01-27 08:35:00] session-memory | summary-saved | techdeveloper-ui
```

### Failure Prevention Logs

**Location:** `~/.claude/memory/logs/failures.log`

**Format:**
```
[YYYY-MM-DD HH:MM:SS] PATTERN | PREVENTED | details
```

### Policy Counters

**Location:** `~/.claude/memory/logs/policy-counters.txt`

**Format:**
```
session-memory=47
skill-detection=23
user-preferences=15
context-management=0
```

### System Dashboard

**Command:**
```bash
bash ~/.claude/memory/dashboard.sh
```

**Shows:**
- Policy execution counts
- Recent policy hits
- Prevented failures
- System status
- Session stats

---

## 🔧 Maintenance Commands

### View Live Logs
```bash
# Policy applications
tail -f ~/.claude/memory/logs/policy-hits.log

# Failures prevented
tail -f ~/.claude/memory/logs/failures.log

# System logs
tail -f ~/.claude/memory/logs/process-execution.log
```

### Check System Status
```bash
# Policy counters
cat ~/.claude/memory/logs/policy-counters.txt

# System status
cat ~/.claude/memory/logs/system-status.log

# Dashboard
bash ~/.claude/memory/dashboard.sh
```

### Verify Integration
```bash
# Check context-session integration
bash ~/.claude/memory/verify-integration.sh

# Verify system setup
bash ~/.claude/memory/verify-setup.sh

# Check for conflicts
bash ~/.claude/memory/check-conflicts.sh
```

### Backup & Rollback
```bash
# Rollback changes
python ~/.claude/memory/rollback.py

# Manual backup (auto-backups already happen)
cp -r ~/.claude/memory/sessions ~/.claude/memory/backups/sessions-$(date +%Y%m%d)
```

---

## 🚀 Quick Reference

### Session Start (Automatic)
```bash
# Step 0: Migrate local CLAUDE.md
python ~/.claude/memory/migrate-local-claude.py "$PWD"

# Step 0.5: Auto-register skills
python ~/.claude/memory/auto-register-skills.py

# Step 3.5: Check incomplete work
python ~/.claude/memory/check-incomplete-work.py $(basename "$PWD")
```

### Skill Detection (Proactive)
```bash
python ~/.claude/memory/skill-detector.py "user message"
```

### User Preferences (Learn & Apply)
```bash
# Load preference
python ~/.claude/memory/load-preferences.py <category>

# Track choice
python ~/.claude/memory/track-preference.py <category> <value>
```

### Session Pruning (Monthly)
```bash
python ~/.claude/memory/archive-old-sessions.py
python ~/.claude/memory/archive-old-sessions.py --stats
```

### Cross-Project Patterns (Monthly)
```bash
python ~/.claude/memory/detect-patterns.py
python ~/.claude/memory/apply-patterns.py <topic>
```

### Context Management (⚠️ TO BE BUILT!)
```bash
# Monitor context
python ~/.claude/memory/monitor-context.py

# Smart cleanup
python ~/.claude/memory/smart-cleanup.py

# Trigger cleanup
bash ~/.claude/memory/trigger-context-cleanup.sh
```

---

## 📝 Development Workflow

### Adding New Policy

1. **Create policy file:**
   ```bash
   touch ~/.claude/memory/new-policy.md
   ```

2. **Document in CLAUDE.md:**
   ```markdown
   ### X. New Policy Name
   - Brief description
   - Full details: `~/.claude/memory/new-policy.md`
   ```

3. **Add logging template:**
   ```bash
   echo "[$(date '+%Y-%m-%d %H:%M:%S')] new-policy | action | context" >> ~/.claude/memory/logs/policy-hits.log
   ```

4. **Update this map:**
   - Add to relevant section
   - Update integration flow if needed

### Adding New Script

1. **Create script:**
   ```bash
   touch ~/.claude/memory/new-script.py
   chmod +x ~/.claude/memory/new-script.py
   ```

2. **Add to integration flow:**
   - Update relevant section in this document
   - Document parameters & usage
   - Add logging

3. **Test:**
   ```bash
   python ~/.claude/memory/new-script.py --test
   ```

4. **Update dashboard.sh** (if monitoring needed)

### Adding New Skill

1. **Create skill:**
   ```bash
   mkdir -p ~/.claude/skills/new-skill
   touch ~/.claude/skills/new-skill/skill.md
   ```

2. **Auto-register:**
   ```bash
   python ~/.claude/memory/auto-register-skills.py
   ```

3. **Verify:**
   ```bash
   cat ~/.claude/memory/skills-registry.json | grep "new-skill"
   ```

---

## ⚠️ Current Gaps & TODOs

### Context Management Automation

**Status:** ✅ COMPLETE + FULLY AUTOMATED (8/8 built)

**Core Scripts:**
1. ✅ `~/.claude/memory/context-estimator.py` - Estimate context % from observable metrics
2. ✅ `~/.claude/memory/monitor-context.py` - Monitor context & provide recommendations
3. ✅ `~/.claude/memory/smart-cleanup.py` - Policy-based cleanup with session protection
4. ✅ `~/.claude/memory/protect-session-memory.py` - Verify session memory protection status
5. ✅ `~/.claude/memory/trigger-context-cleanup.sh` - Manual trigger orchestrator

**Automation Layer:**
6. ✅ `~/.claude/memory/context-daemon.py` - Background daemon (continuous monitoring)
7. ✅ `~/.claude/memory/auto-save-session.py` - Auto-save session before cleanup
8. ✅ `~/.claude/memory/startup-hook.sh` - Auto-start daemon on session start

**Integration:**
- Uses policy: `CONTEXT-SESSION-INTEGRATION.md`
- Uses skill: `context-management-core/skill.md`
- Protects: `sessions/**/*.md`
- Logs to: `logs/policy-hits.log`

**Priority:** HIGH (Built-in auto-compact is basic, advanced system needed)

**Usage:**

**Automatic Mode (Recommended):**
```bash
# Start daemon on session start (runs automatically)
bash ~/.claude/memory/startup-hook.sh

# Check daemon status
python ~/.claude/memory/context-daemon.py --status

# Stop daemon
python ~/.claude/memory/context-daemon.py --stop

# Restart with different interval
python ~/.claude/memory/context-daemon.py --stop
python ~/.claude/memory/context-daemon.py --interval 5 --project my-app
```

**Manual Mode:**
```bash
# Estimate context
python ~/.claude/memory/context-estimator.py

# Monitor context
python ~/.claude/memory/monitor-context.py --simulate 75

# Auto-save session
python ~/.claude/memory/auto-save-session.py --project my-app

# Smart cleanup (dry run)
python ~/.claude/memory/smart-cleanup.py --level moderate --project my-app

# Verify session protection
python ~/.claude/memory/protect-session-memory.py --verify

# Manual trigger (orchestrator)
bash ~/.claude/memory/trigger-context-cleanup.sh --context-percent 80 --project my-app
```

**How Full Automation Works:**
1. **Session Start** → startup-hook.sh starts daemon
2. **Daemon Runs** → Checks context every 10 minutes (configurable)
3. **Context Estimated** → Based on messages, file reads, tool calls
4. **Threshold Hit** → 70%, 85%, or 90% detected
5. **Auto-Save** → Session summary saved automatically
6. **Auto-Cleanup** → Policy-based cleanup triggered
7. **Session Protected** → Memory files NEVER deleted
8. **Loop Continues** → Daemon keeps monitoring

---

## 🎯 System Principles

1. **100% Local** - No external APIs for storage
2. **Policy-Driven** - Rules in markdown, automation in scripts
3. **Auto-Logging** - Every policy application logged
4. **Protected Directories** - Session memory never auto-deleted
5. **Learn & Apply** - User preferences learned automatically
6. **Cross-Project Intelligence** - Learn from your own patterns
7. **Proactive** - Detect and suggest before user asks

---

## 📖 Further Reading

- **Main Guide:** `~/.claude/memory/README.md`
- **How It Works:** `~/.claude/memory/HOW-IT-WORKS.md`
- **Quick Start:** `~/.claude/memory/MEMORY-SYSTEM-QUICKSTART.md`
- **Session Resume:** `~/.claude/memory/SESSION-RESUME-GUIDE.md`
- **Skill Registry:** `~/.claude/memory/SKILL-REGISTRY-QUICK-START.md`
- **User Preferences:** `~/.claude/memory/USER-PREFERENCES-QUICKSTART.md`
- **Session Pruning:** `~/.claude/memory/SESSION-PRUNING-QUICKSTART.md`
- **Cross-Project Patterns:** `~/.claude/memory/CROSS-PROJECT-PATTERNS-QUICKSTART.md`

---

**Version:** 1.0.0
**Created:** 2026-01-27
**Purpose:** Never forget where things are and how they connect
**Status:** ACTIVE - REFERENCE AS NEEDED

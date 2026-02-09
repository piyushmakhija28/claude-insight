# Claude Memory System - Complete Quick Start Guide

## 🎯 What is This?

**A comprehensive memory system that makes Claude remember everything across all your projects!**

The system includes:
- ✅ **Session Memory** - Remember context within projects
- ✅ **User Preferences** - Learn your repeated choices
- ✅ **Cross-Project Patterns** - Detect patterns across ALL projects
- ✅ **Session Pruning** - Keep memory fast by archiving old sessions
- ✅ **Skills Registry** - Auto-detect and suggest relevant skills
- ✅ **Conflict Detection** - Catch inconsistencies automatically
- ✅ **Rollback Mechanism** - Undo changes if needed

---

## 🚀 First Time Setup

### Step 1: Check Installation

```bash
cd ~/.claude/memory
ls -la
```

**You should see:**
- Policy files (*.md)
- Python scripts (*.py)
- Bash scripts (*.sh)
- JSON storage files

---

### Step 2: Run Dashboard

```bash
bash ~/.claude/memory/dashboard.sh
```

**What it shows:**
- System status
- Policy status
- User preferences
- Session memory stats
- Cross-project patterns
- Recent activity
- System health

---

## 📚 Core Features & Usage

### 1. Session Memory (Auto-Active)

**What it does:** Remembers context within each project

**How it works:**
- Automatically loads project context at session start
- Saves session summaries at milestones
- 100% local (no API calls)

**Manual commands:**
```bash
# View session for a project
cat ~/.claude/memory/sessions/<project-name>/project-summary.md

# List all projects with memory
ls ~/.claude/memory/sessions/
```

**When to use:**
- Automatic! Just work on your projects normally

---

### 2. User Preferences (Learning System)

**What it does:** Learns from your repeated choices (after 3x)

**How it works:**
- You choose "skip tests" 3 times → Preference learned
- 4th time onwards → Auto-applies without asking
- You can always override

**Commands:**
```bash
# View learned preferences
python ~/.claude/memory/load-preferences.py

# Get specific preference
python ~/.claude/memory/load-preferences.py testing

# Manual tracking (normally automatic)
python ~/.claude/memory/track-preference.py testing skip
```

**Example:**
```
Session 1-3: You choose REST API → System learns
Session 4+: Claude auto-suggests REST without asking
```

---

### 3. Cross-Project Patterns (Monthly Detection)

**What it does:** Detects patterns across ALL your projects

**How it works:**
- Scans all project memories
- Finds common technologies (JWT in 75% of projects)
- Suggests based on your history

**Commands:**
```bash
# Detect patterns (run monthly)
python ~/.claude/memory/detect-patterns.py

# View detected patterns
python ~/.claude/memory/detect-patterns.py --show

# Get pattern suggestions
python ~/.claude/memory/apply-patterns.py authentication
python ~/.claude/memory/apply-patterns.py database
python ~/.claude/memory/apply-patterns.py "rest api"
```

**Example:**
```
Analysis: JWT used in 6/8 projects (75% confidence)
Suggestion: "You consistently use JWT - use it again?"
```

---

### 4. Session Pruning (Monthly Cleanup)

**What it does:** Archives old sessions to keep memory fast

**How it works:**
- Keeps last 10 sessions active
- Archives sessions older than 30 days
- Compresses by month

**Commands:**
```bash
# Check what can be archived
python ~/.claude/memory/archive-old-sessions.py --stats

# Preview without archiving
python ~/.claude/memory/archive-old-sessions.py --dry-run

# Archive all projects
python ~/.claude/memory/archive-old-sessions.py

# Archive specific project
python ~/.claude/memory/archive-old-sessions.py project-name
```

**When to use:**
- Monthly (or when sessions accumulate)

---

### 5. Skills Registry (Proactive Suggestions)

**What it does:** Auto-detects and suggests relevant skills

**How it works:**
- Scans your skills folder
- Auto-registers new skills
- Suggests based on user message

**Commands:**
```bash
# Auto-register skills (runs at session start)
python ~/.claude/memory/auto-register-skills.py

# Detect skill from message
python ~/.claude/memory/skill-detector.py "implement payment gateway"
```

**Example:**
```
User: "I need to implement Stripe payments"
Claude: "I detected a relevant skill: payment-integration-python
         Should I use it?"
```

---

## 🛠️ Maintenance Tasks

### Monthly Routine (Recommended)

```bash
# 1. Run dashboard to check system health
bash ~/.claude/memory/dashboard.sh

# 2. Detect new patterns
python ~/.claude/memory/detect-patterns.py

# 3. Check for archival opportunities
python ~/.claude/memory/archive-old-sessions.py --stats

# 4. Archive if needed
python ~/.claude/memory/archive-old-sessions.py

# 5. Check for conflicts (optional)
bash ~/.claude/memory/check-conflicts.sh
```

---

### Weekly Quick Check

```bash
# Quick dashboard view
bash ~/.claude/memory/dashboard.sh

# Check recent activity
tail -10 ~/.claude/memory/logs/policy-hits.log
```

---

## 🔧 Advanced Features

### Conflict Detection

**What it checks:**
- Preferences vs Patterns conflicts
- Configuration inconsistencies
- Session memory integrity
- Pattern staleness
- Disk usage

**Command:**
```bash
bash ~/.claude/memory/check-conflicts.sh
```

**When to use:**
- When something feels off
- Monthly health check
- Before major changes

---

### Rollback Mechanism

**What it does:** Undo changes made by the system

**Commands:**
```bash
# List available rollback points
python ~/.claude/memory/rollback.py --list

# Rollback preferences
python ~/.claude/memory/rollback.py --preferences

# Rollback patterns
python ~/.claude/memory/rollback.py --patterns
```

**When to use:**
- After accidental preference learning
- After incorrect pattern detection
- To restore previous state

---

## 📊 Understanding the Dashboard

### Dashboard Sections:

**1. System Status**
- Memory directory active?
- Sessions directory active?
- Python available?

**2. Policy Status**
- Which policies are active
- Policy health percentage

**3. User Preferences**
- How many preferences learned
- Which categories active

**4. Session Memory**
- How many projects have memory
- Active sessions count
- Archived sessions count
- Most active projects

**5. Cross-Project Patterns**
- How many patterns detected
- When last analyzed
- Top patterns with confidence

**6. Skills Registry**
- How many skills registered
- Most used skills

**7. Policy Execution**
- Which policies executed most
- Execution statistics

**8. Recent Activity**
- Last 5 logged actions
- Total actions logged

**9. System Health**
- Disk usage
- Conflicts detected
- Failures prevented

**10. Quick Actions**
- Common commands for quick access

---

## 🎯 Common Workflows

### Workflow 1: Starting a New Project

```
1. Claude auto-loads memory (if exists)
2. You start working
3. Claude suggests patterns: "You use JWT in 75% of projects"
4. You confirm or change
5. Work proceeds with memory-informed decisions
```

---

### Workflow 2: After Completing Work

```
1. Major milestone completed
2. Claude offers to save session summary
3. You confirm: "y"
4. Summary saved to sessions/<project>/
5. Next session will remember everything!
```

---

### Workflow 3: Monthly Maintenance

```
1. Run dashboard
2. Detect new patterns
3. Archive old sessions
4. Check conflicts
5. Review preferences
```

---

## 📁 File Locations

```
~/.claude/memory/
├── CLAUDE.md                          # Main config (integrated)
├── dashboard.sh                       # Enhanced dashboard
├── check-conflicts.sh                 # Conflict detection
├── rollback.py                        # Rollback mechanism
│
├── detect-patterns.py                 # Pattern detector
├── apply-patterns.py                  # Pattern applier
├── cross-project-patterns.json        # Pattern storage
│
├── track-preference.py                # Preference tracker
├── load-preferences.py                # Preference loader
├── user-preferences.json              # Preference storage
│
├── archive-old-sessions.py            # Session archiver
│
├── sessions/                          # Project memories
│   ├── project-1/
│   │   ├── project-summary.md         # Cumulative summary
│   │   ├── session-*.md               # Active sessions
│   │   └── archive/                   # Archived sessions
│   └── project-2/
│       └── ...
│
├── logs/                              # System logs
│   ├── policy-hits.log                # All actions
│   ├── policy-counters.txt            # Execution counts
│   └── failures.log                   # Prevented failures
│
└── backups/                           # Rollback points
    └── *.json                         # Backup files
```

---

## 🆘 Troubleshooting

### Issue: "No patterns detected"

**Cause:** Less than 3 projects analyzed

**Solution:** Normal - need 3+ projects for pattern detection

---

### Issue: "Preferences not learning"

**Cause:** Haven't made same choice 3 times yet

**Solution:** Continue working - system learns after 3x

---

### Issue: "Dashboard not showing data"

**Cause:** Python not available or files missing

**Solution:**
```bash
# Check Python
python --version

# Check files
ls -la ~/.claude/memory/*.json
```

---

### Issue: "Sessions loading slowly"

**Cause:** Too many old sessions

**Solution:**
```bash
# Archive old sessions
python ~/.claude/memory/archive-old-sessions.py
```

---

### Issue: "Conflicts detected"

**Cause:** Normal - just informational

**Solution:** Review suggestions, usually no action needed

---

## 💡 Tips & Best Practices

### DO:
- ✅ Run dashboard monthly
- ✅ Detect patterns after major work
- ✅ Archive sessions when accumulating
- ✅ Check conflicts occasionally
- ✅ Let preferences learn naturally

### DON'T:
- ❌ Manually edit JSON files (use scripts)
- ❌ Delete sessions folder (use archival)
- ❌ Force preference learning (let it happen)
- ❌ Ignore conflicts (review suggestions)
- ❌ Skip monthly maintenance

---

## 🎉 Quick Reference Card

```
# Daily
- Work normally (system auto-saves)

# Weekly
- bash ~/.claude/memory/dashboard.sh

# Monthly
- python ~/.claude/memory/detect-patterns.py
- python ~/.claude/memory/archive-old-sessions.py --stats
- bash ~/.claude/memory/check-conflicts.sh

# As Needed
- python ~/.claude/memory/apply-patterns.py <topic>
- python ~/.claude/memory/load-preferences.py
- python ~/.claude/memory/rollback.py --list
```

---

## 📖 Full Documentation

**Detailed guides available:**
- `session-memory-policy.md` - Session memory details
- `user-preferences-policy.md` - Preference learning
- `cross-project-patterns-policy.md` - Pattern detection
- `session-pruning-policy.md` - Archival system
- `HOW-IT-WORKS.md` - System internals

**Quick start guides:**
- `USER-PREFERENCES-QUICKSTART.md`
- `SESSION-PRUNING-QUICKSTART.md`
- `CROSS-PROJECT-PATTERNS-QUICKSTART.md`

---

## ✅ Summary

**What you get:**
- 🧠 Claude remembers everything across projects
- 🎯 Learns your preferences automatically
- 🔍 Detects your working patterns
- ⚡ Stays fast with automatic archival
- 🛡️ Conflict detection & rollback safety
- 📊 Complete visibility via dashboard

**What you do:**
- Work normally (system handles memory)
- Run monthly maintenance (5 minutes)
- Review dashboard occasionally

**Result:**
**Claude that remembers, learns, and adapts to YOUR style!** 🎉

---

**Status:** ✅ READY TO USE | **Version:** 1.0 | **Date:** 2026-01-26

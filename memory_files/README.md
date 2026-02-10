# Claude Memory System v2.2.0 - Complete Files

This directory contains all files from the Claude Memory System v2.2.0, integrated into the Claude Monitoring System.

## 📁 Directory Structure

```
memory_files/
├── policies/           # All policy markdown files (10 policies)
├── scripts/            # All automation Python and shell scripts (62+ scripts)
├── daemons/           # All daemon scripts (8 daemons)
├── docs/              # Documentation files
└── CLAUDE.md          # Global configuration file
```

## 🧠 8 Daemon Scripts

### Monitoring Daemons:
1. **context-daemon.py** - Monitors context usage every 10 minutes
2. **session-auto-save-daemon.py** - Auto-saves session state every 15 minutes
3. **preference-tracker-daemon.py** - Tracks user preferences every 20 minutes
4. **skill-auto-suggester.py** - Suggests relevant skills every 5 minutes
5. **commit-daemon.py** - Auto-commits changes every 15 minutes
6. **session-pruning-daemon.py** - Prunes old sessions daily
7. **pattern-detection-daemon.py** - Detects usage patterns weekly
8. **failure-prevention-daemon.py** - Monitors failures every 6 hours

### Support Scripts:
- **daemon-manager.py** - Cross-platform daemon launcher
- **health-monitor-daemon.py** - Health monitoring & auto-restart
- **pid-tracker.py** - PID file management
- **daemon-logger.py** - Proper logging infrastructure

## 📋 10 Active Policies

1. **core-skills-mandate.md** - Enforced execution order
2. **model-selection-enforcement.md** - Haiku/Sonnet/Opus usage
3. **proactive-consultation-policy.md** - User preference learning
4. **session-memory-policy.md** - Auto-save and restore
5. **common-failures-prevention.md** - Auto-fix patterns
6. **file-management-policy.md** - Smart file operations
7. **git-auto-commit-policy.md** - Automatic commits
8. **user-preferences-policy.md** - Preference storage
9. **session-pruning-policy.md** - Old session cleanup
10. **CONTEXT-SESSION-INTEGRATION.md** - Context + session sync

## 🚀 Key Automation Scripts

### Context Optimization:
- **context-cache.py** - Intelligent caching
- **context-monitor-v2.py** - Enhanced monitoring
- **context-estimator.py** - Enhance estimation algorithm
- **pre-execution-optimizer.py** - Optimize before tool calls
- **context-extractor.py** - Extract essentials after execution
- **session-state.py** - External state management
- **auto-context-pruner.py** - Auto-pruning context
- **auto-tool-wrapper.py** - Automatic tool optimization
- **auto-post-processor.py** - Post-tool processing

### Token Optimization:
- **token-optimization-daemon.py** - Token optimization monitoring
- **ast-code-navigator.py** - AST-based code navigation
- **file-type-optimizer.py** - File type-specific optimization
- **smart-file-summarizer.py** - Intelligent file summarization
- **tiered-cache.py** - Multi-tier caching system

### Failure Prevention:
- **failure-detector-v2.py** - Detect failures from logs
- **failure-pattern-extractor.py** - Extract patterns
- **failure-solution-learner.py** - Learn solutions
- **pre-execution-checker.py** - Check KB before execution
- **update-failure-kb.py** - Update knowledge base

### Model Selection:
- **model-selection-enforcer.py** - Analyze request & enforce model
- **model-selection-monitor.py** - Monitor usage distribution

### Policy Enforcement:
- **core-skills-enforcer.py** - Enforce skills execution order
- **consultation-tracker.py** - Track consultation decisions

### Session Management:
- **auto-save-session.py** - Automatic session saving
- **archive-old-sessions.py** - Archive old sessions
- **protect-session-memory.py** - Protect session data
- **session-save-triggers.py** - Save triggers

### Git Automation:
- **auto-commit.py** - Git auto-commit logic
- **auto-commit-detector.py** - Detect commit triggers
- **trigger-auto-commit.py** - Trigger commits

### Pattern Detection:
- **detect-patterns.py** - Detect usage patterns
- **apply-patterns.py** - Apply learned patterns

### Preference Management:
- **preference-detector.py** - Detect preferences
- **preference-auto-tracker.py** - Auto-track preferences
- **track-preference.py** - Track preference
- **load-preferences.py** - Load preferences

### Health Monitoring:
- **daily-health-check.sh** - Daily health check
- **weekly-health-check.sh** - Weekly health check
- **monthly-optimization.sh** - Monthly optimization
- **dashboard.sh** - Dashboard display
- **dashboard-v2.sh** - Enhanced dashboard
- **verify-system.sh** - System verification

### Startup & Initialization:
- **startup-hook.sh** - Session startup hook
- **startup-hook-v2.sh** - Enhanced startup hook
- **initialize-system.sh** - System initialization
- **session-start.sh** - Session start script

## 📚 Documentation Files

### Quick Start Guides:
- **MEMORY-SYSTEM-QUICKSTART.md**
- **FAILURE-LEARNING-QUICK-START.md**
- **SKILL-REGISTRY-QUICK-START.md**
- **SESSION-PRUNING-QUICKSTART.md**
- **USER-PREFERENCES-QUICKSTART.md**
- **CROSS-PROJECT-PATTERNS-QUICKSTART.md**

### System Documentation:
- **SYSTEM-V2-OVERVIEW.md** - Complete v2 overview
- **HOW-IT-WORKS.md** - System workflows
- **API-REFERENCE.md** - All script APIs
- **TROUBLESHOOTING-V2.md** - Common issues & fixes

### Implementation Summaries:
- **AUTOMATION-COMPLETE-SUMMARY.md**
- **AUTOMATION-V2-PROGRESS.md**
- **IMPROVEMENTS-SUMMARY.md**
- **MIGRATION-GUIDE.md**

### Phase Completion Reports:
- **PHASE-1-COMPLETION-SUMMARY.md** - Context management
- **PHASE-2-COMPLETION-SUMMARY.md** - Daemon infrastructure
- **PHASE-3-COMPLETION-SUMMARY.md** - Failure learning
- **PHASE-4-COMPLETION-SUMMARY.md** - Policy automation
- **PHASE-6-COMPLETION-SUMMARY.md** - Documentation

### Advanced Documentation:
- **ADVANCED-TOKEN-OPTIMIZATION.md**
- **TOKEN-OPTIMIZATION-COMPLETE.md**
- **FAILURE-LEARNING-SYSTEM.md**
- **SKILL-REGISTRY-SYSTEM.md**
- **cross-project-patterns-policy.md**

## 🔧 Configuration Files

- **CLAUDE.md** - Global configuration (v2.2.0)
- **skills-registry.json** - All registered skills
- **failure-kb.json** - Failure knowledge base
- **consultation-preferences.json** - Consultation tracking
- **user-preferences.json** - User preferences
- **cross-project-patterns.json** - Cross-project patterns

## 📊 Data Storage

### Logs Directory (`~/.claude/memory/logs/`):
- context-daemon.log
- session-auto-save-daemon.log
- git-auto-commit.log
- policy-hits.log
- model-usage.log
- context-cache.log
- failures.log
- optimizations.log
- session-pruning.log

### Cache Directory (`~/.claude/memory/.cache/`):
- Cached file summaries
- Context optimization data

### PIDs Directory (`~/.claude/memory/.pids/`):
- Daemon PID files for tracking

### Sessions Directory (`~/.claude/memory/sessions/`):
- Project-specific session data
- Auto-saved session states

## 🎯 Usage in Monitoring System

The Claude Monitoring System (v2.12) integrates with these files to provide:

1. **Real-time daemon health monitoring**
2. **Policy enforcement tracking**
3. **Context optimization metrics**
4. **Failure prevention statistics**
5. **Model selection distribution**
6. **Session memory tracking**
7. **Git automation activity**
8. **Overall system health score**

## 📈 Monitoring Integration

All scripts are monitored via:
- `/api/memory-system/health` - Complete health statistics
- `/api/memory-system/daemons` - Daemon status details
- `/api/memory-system/policies` - Policy enforcement metrics

The monitoring system reads log files, PID files, and configuration files to provide real-time health metrics and system status.

---

**Version:** 2.2.0
**Status:** ✅ FULLY OPERATIONAL
**Last Updated:** February 2026
**Integration:** Claude Monitoring System v2.12

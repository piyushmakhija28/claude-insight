# Claude Insight - Project Instructions

**Project:** Claude Insight - Monitoring Dashboard for Claude Memory System
**Version:** 2.7.0
**Type:** Public GitHub Repository
**Status:** 🟢 Active
**Updated:** 2026-02-17 (Daemon Management System Enhanced)

---

## 📖 Project Overview

**Claude Insight** is a monitoring dashboard for the Claude Memory System v2.5.0+. It provides:
- Real-time monitoring of Claude's memory system
- Policy enforcement tracking
- Session management visualization
- Context usage analytics
- Daemon health monitoring

**Repository:** https://github.com/piyushmakhija28/claude-insight

---

## 🎯 What This Project Contains

**✅ INCLUDED (Core Memory System Files ONLY):**
1. **Core Policies:**
   - 3-Level Architecture (Sync → Rules → Execution)
   - Zero-Tolerance Failure Policy
   - Auto-Fix Enforcement
   - Session ID Tracking

2. **Core Automation Scripts:**
   - `session-start.sh` - Session initialization
   - `auto-fix-enforcer.py` - System health checks
   - `blocking-policy-enforcer.py` - Policy enforcement

3. **Daemon Management System (NEW - v2.7.0):**
   - `daemon-manager.py` - Daemon lifecycle management (10 daemons)
   - `health-monitor-daemon.py` - Auto-restart dead daemons
   - `daemon-logger.py` - Centralized daemon logging
   - `pid-tracker.py` - Process ID tracking
   - Supports all 10 core daemons with auto-restart

4. **Core Documentation:**
   - `MASTER-README.md` - Complete system documentation
   - Policy documentation (enforcement, failure prevention)

5. **Dashboard Files:**
   - Monitoring dashboard UI
   - Analytics visualization
   - Health check displays
   - Daemon status monitoring

**❌ NOT INCLUDED (These Go to Claude Global Library):**
- Skills (Docker, Kubernetes, Java, etc.)
- Agents (DevOps, Spring Boot, QA, etc.)
- Optimization patterns
- Design patterns

**❌ NEVER INCLUDED (Keep Private):**
- Personal configuration files
- Project-specific business logic
- Proprietary code
- Secrets or credentials

---

## 🏗️ Project Structure

```
claude-insight/
├── README.md                      # Public project documentation
├── CLAUDE.md                      # THIS FILE - Project-specific instructions
├── dashboard/                     # Monitoring dashboard UI
│   ├── index.html
│   ├── css/
│   └── js/
├── core/                          # Core memory system files
│   ├── policies/                  # Core policies only
│   ├── scripts/                   # Core automation scripts
│   └── docs/                      # Core documentation
├── examples/                      # Usage examples
└── tests/                         # Test files

```

---

## 🤖 Daemon Management System (v2.7.0)

**Overview:**
Claude Insight now includes a complete daemon management system that handles all 10 core daemons of the Claude Memory System.

**10 Core Daemons:**
1. **context-daemon** - Monitors context usage (hybrid: event-driven + periodic)
2. **session-auto-save-daemon** - Auto-saves sessions at milestones
3. **preference-auto-tracker** - Learns user preferences automatically
4. **skill-auto-suggester** - Suggests relevant skills/agents
5. **commit-daemon** - Auto-commits on phase completion
6. **session-pruning-daemon** - Cleans old sessions weekly
7. **pattern-detection-daemon** - Detects code patterns
8. **failure-prevention-daemon** - Smart adaptive failure detection
9. **token-optimization-daemon** - Auto-optimizes context when >85%
10. **health-monitor-daemon** - Auto-restarts dead daemons

**Daemon Utilities (`src/utils/`):**

```python
# daemon-manager.py - Main daemon controller
python daemon-manager.py --status-all     # Check all daemon status
python daemon-manager.py --start <name>   # Start specific daemon
python daemon-manager.py --stop <name>    # Stop specific daemon
python daemon-manager.py --restart <name> # Restart specific daemon

# health-monitor-daemon.py - Auto-restart monitor
# Runs continuously, checks every 5 minutes
# Auto-restarts any dead daemons
```

**Key Features:**
- ✅ Cross-platform (Windows/Linux/Mac)
- ✅ Auto-restart on failure
- ✅ Smart adaptive intervals (10-60s based on activity)
- ✅ Event-driven + periodic monitoring
- ✅ Centralized logging
- ✅ PID tracking
- ✅ JSON status output

**Startup Integration:**
- Windows: `scripts/start-all-daemons.bat` (auto-start on login)
- Linux/Mac: `scripts/start-all-daemons.sh`

**Recent Fixes (2026-02-17):**
- ✅ Fixed daemon-manager.py to use correct subdirectory paths
- ✅ Removed non-existent auto-recommendation-daemon
- ✅ Added token-optimization-daemon and health-monitor-daemon
- ✅ Fixed health-monitor-daemon import paths for utilities
- ✅ All 10 daemons now managed correctly

---

## 🤖 Working with This Project

**When asked to work on Claude Insight:**

1. **Focus:** Monitoring dashboard and core memory system ONLY
2. **No Skills/Agents:** These belong in Claude Global Library
3. **Public Context:** Everything here is public - no private info
4. **Documentation:** Keep docs focused on monitoring and dashboard usage

**File Operations:**

```bash
# Navigate to project
cd "C:\Users\techd\Documents\workspace-spring-tool-suite-4-4.27.0-new\claude-insight"

# Check what belongs here
python verify-content.py

# Sync core files (auto-detects eligibility)
bash sync-from-memory-system.sh
```

---

## 📋 Coding Standards

**For dashboard files:**
- Clean, modern HTML/CSS/JS
- Responsive design
- Clear comments
- User-friendly interface

**For Python scripts:**
- PEP 8 compliance
- Type hints
- Docstrings
- Error handling

**For documentation:**
- Clear, concise
- Public-friendly (no personal paths)
- Examples provided
- Well-structured

---

## 🚀 Development Workflow

1. **Changes to core policies/scripts:**
   - Edit in `~/.claude/memory/` first (personal system)
   - Test locally
   - Sync to claude-insight using smart-sync
   - Commit and push

2. **Changes to dashboard:**
   - Edit directly in claude-insight/dashboard/
   - Test in browser
   - Commit and push

3. **Documentation updates:**
   - Edit in claude-insight/core/docs/
   - Ensure public-friendly content
   - Commit and push

---

## 🔗 Related Projects

- **Claude Global Library:** https://github.com/piyushmakhija28/claude-global-library
  - Skills, agents, optimization patterns
  - Separate public repository

---

## 🛠️ For Contributors

**If you're using Claude Code to work on this project:**

1. This CLAUDE.md provides project-specific context
2. DO NOT expect personal memory system paths (like ~/.claude/)
3. Dashboard-focused development only
4. Follow public repository best practices

**Questions?**
- GitHub Issues: https://github.com/piyushmakhija28/claude-insight/issues
- Documentation: See README.md

---

**VERSION:** 2.7.0 (Daemon Management Enhanced)
**LAST UPDATED:** 2026-02-17
**TYPE:** Public Project Instructions
**LOCATION:** `claude-insight/CLAUDE.md`

**CHANGELOG v2.7.0:**
- Added complete daemon management system (10 daemons)
- Added daemon utilities to src/utils/
- Fixed daemon-manager.py with correct paths
- Fixed health-monitor-daemon.py imports
- Enhanced documentation with daemon details
- All systems operational and auto-restarting

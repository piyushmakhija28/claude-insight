# Claude Insight - Project Instructions

**Project:** Claude Insight - Monitoring Dashboard for Claude Memory System
**Version:** 2.7.0
**Type:** Public GitHub Repository
**Status:** 🟢 Active
**Updated:** 2026-02-17 (Daemon Management System Enhanced + Dark Mode Fixed)

---

## 📖 Project Overview

**Claude Insight** is a monitoring dashboard for the Claude Memory System v3.2.0 (3-Level Architecture). It provides:
- Real-time monitoring of Claude's memory system
- Policy enforcement tracking
- Session management visualization
- Context usage analytics
- Daemon health monitoring (10 core daemons)
- 3-Level Architecture execution flow tracking
- 12-Step Execution System visualization

**Repository:** https://github.com/piyushmakhija28/claude-insight

---

## 🎯 What This Project Contains

**✅ INCLUDED (Core Memory System Files ONLY):**
1. **Core Policies:**
   - 3-Level Architecture (Sync → Rules → Execution)
   - Zero-Tolerance Failure Policy
   - Auto-Fix Enforcement
   - Session ID Tracking
   - 12-Step Execution System

2. **Core Automation Scripts:**
   - `session-start.sh` - Session initialization
   - `auto-fix-enforcer.py` - System health checks
   - `blocking-policy-enforcer.py` - Policy enforcement
   - `test-complete-execution-flow.sh` - Full system test

3. **Daemon Management System (v2.7.0):**
   - `daemon-manager.py` - Daemon lifecycle management (10 daemons)
   - `health-monitor-daemon.py` - Auto-restart dead daemons
   - `daemon-logger.py` - Centralized daemon logging
   - `pid-tracker.py` - Process ID tracking
   - Supports all 10 core daemons with auto-restart

4. **Core Documentation:**
   - `MASTER-README.md` - Complete system documentation
   - Policy documentation (enforcement, failure prevention)
   - 3-Level Architecture documentation
   - Execution flow documentation

5. **Dashboard Files:**
   - Monitoring dashboard UI
   - Analytics visualization
   - Health check displays
   - Daemon status monitoring
   - Dark mode support with proper text visibility

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
- Global CLAUDE.md (stays in ~/.claude/)

---

## 🏗️ Project Structure

```
claude-insight/
├── README.md                      # Public project documentation
├── CLAUDE.md                      # THIS FILE - Project-specific instructions
├── VERSION                        # Version number (2.7.0)
├── dashboard/                     # Monitoring dashboard UI (deprecated, now in templates/)
├── templates/                     # Flask templates
│   ├── base.html                  # Base template with admin layout (FIXED: dark mode CSS)
│   ├── dashboard.html             # Main dashboard (FIXED: live metrics overlapping)
│   ├── login.html                 # Login page
│   └── [other pages]
├── src/                          # Flask application
│   ├── app.py                    # Main Flask app (FIXED: versions, WebSocket, /api/log-files)
│   ├── services/                 # Monitoring services
│   └── utils/                    # Daemon utilities
├── core/                         # Core memory system files
│   ├── policies/                 # Core policies only
│   ├── scripts/                  # Core automation scripts
│   └── docs/                     # Core documentation
├── examples/                     # Usage examples
├── tests/                        # Test files
└── backups/2026-02-17/          # Backups of modified files
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

## 🎨 Dashboard Fixes Applied (2026-02-17)

### **1. Live Metrics UI Overlapping - FIXED** ✅
- Added height constraint to chart container (400px)
- File: `templates/dashboard.html`, Line 108

### **2. Logout Button Visibility - ENHANCED** ✅
- Enhanced dropdown styling (z-index, positioning, shadow)
- File: `templates/base.html`, Lines 1424-1431

### **3. Session Template Check - FIXED** ✅
- Changed from `session.logged_in` to `session.get('logged_in')`
- File: `templates/base.html`, Lines 1268, 1538

### **4. Dark Mode CSS - FIXED** ✅
- Added Bootstrap color class overrides (`.text-muted`, `.bg-light`, `.text-secondary`)
- Fixed status badges for dark mode (semi-transparent backgrounds)
- Fixed card header icons contrast
- Enhanced stat icon opacity
- Fixed headings, paragraphs, lists, modals
- File: `templates/base.html`, 19 new CSS rules
- Documentation: `DARK-MODE-FIXES-APPLIED.md`

### **5. WebSocket Broadcast Error - FIXED** ✅
- Changed from `broadcast=True` to `namespace='/'`
- File: `src/app.py`, Line 5378

### **6. Missing API Endpoint - FIXED** ✅
- Added `/api/log-files` endpoint
- File: `src/app.py`, Lines 950-968

### **7. Version Numbers - UPDATED** ✅
- Startup banner now shows dynamic version (v2.7.0)
- Memory System version updated to v3.2.0
- Daemon count corrected to 10
- 3-Level Architecture mentioned
- File: `src/app.py`, Lines 5386-5427

### **8. README.md - UPDATED** ✅
- All version references updated to v3.2.0
- 3-Level Architecture mentioned
- 12-Step Execution Flow added
- File: `README.md`

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
- Dark mode support (test in both themes)

**For Python scripts:**
- PEP 8 compliance
- Type hints
- Docstrings
- Error handling
- Cross-platform compatibility

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
   - Edit directly in claude-insight/templates/ or src/
   - Test in browser (both light and dark mode)
   - Commit and push

3. **Documentation updates:**
   - Edit in claude-insight/ (README.md, CLAUDE.md, etc.)
   - Ensure public-friendly content
   - Commit and push

---

## 🧪 Testing Checklist

### **After Any Changes:**
- [ ] Restart Flask app
- [ ] Hard refresh browser (Ctrl+Shift+R)
- [ ] Test login (admin/admin)
- [ ] Check all dashboard pages
- [ ] Toggle dark mode
- [ ] Check WebSocket updates (no errors in console)
- [ ] Check all API endpoints return data
- [ ] Verify daemon status shows correctly
- [ ] Test responsive design (mobile/tablet/desktop)

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
5. Test both light and dark modes
6. No hardcoded personal information

**Questions?**
- GitHub Issues: https://github.com/piyushmakhija28/claude-insight/issues
- Documentation: See README.md

---

**VERSION:** 2.7.0 (Daemon Management Enhanced + Dashboard Fixes + Dark Mode)
**LAST UPDATED:** 2026-02-17
**TYPE:** Public Project Instructions
**LOCATION:** `claude-insight/CLAUDE.md`

**CHANGELOG v2.7.0:**
- Added complete daemon management system (10 daemons)
- Added daemon utilities to src/utils/
- Fixed daemon-manager.py with correct paths
- Fixed health-monitor-daemon.py imports
- Fixed dashboard UI overlapping in live metrics
- Fixed logout button visibility
- Fixed session template check
- Fixed dark mode CSS text visibility (19 new rules)
- Fixed WebSocket broadcast error
- Added /api/log-files endpoint
- Updated all version numbers to v3.2.0
- Enhanced documentation with all fixes applied
- All systems operational and auto-restarting

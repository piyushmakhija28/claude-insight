# Claude Insight - Memory System Configuration

**VERSION:** 2.5.2
**STATUS:** 🟢 OPERATIONAL
**PURPOSE:** Real-time monitoring dashboard for Claude Memory System

---

## 🎯 What is Claude Insight?

**Claude Insight** is a professional real-time analytics dashboard for monitoring the Claude Memory System. It provides:
- 📊 Real-time system health monitoring
- 🤖 Policy enforcement tracking
- 💰 Cost analytics and optimization
- 🚨 Alert routing and notifications
- 📈 Predictive analytics and ML-based anomaly detection

**This is a monitoring tool** - it helps you visualize and track your Claude Memory System performance.

---

## 🚀 QUICK START

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/piyushmakhija28/claude-insight.git
cd claude-insight

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your configuration

# Initialize the dashboard
python app.py
```

### 2. Access Dashboard

```
http://localhost:5000
```

Default credentials:
- Username: `admin`
- Password: `admin` (change immediately after first login)

---

## 🧠 CLAUDE MEMORY SYSTEM INTEGRATION

### What is Claude Memory System?

The Claude Memory System is an automation framework that:
- Tracks conversation sessions and context
- Enforces policies and best practices
- Monitors model usage and costs
- Provides automated recommendations

**Claude Insight monitors this system** and provides visual analytics.

### Directory Structure

```
~/.claude/
├── memory/
│   ├── 01-sync-system/           # Session and context management
│   ├── 02-standards-system/      # Coding standards and policies
│   ├── 03-execution-system/      # Automation and enforcement
│   ├── docs/                     # Documentation
│   ├── scripts/                  # Automation scripts
│   ├── logs/                     # System logs (monitored by dashboard)
│   └── sessions/                 # Session data (displayed on dashboard)
├── CLAUDE.md                     # Configuration
└── skills/                       # Optional: User skills
```

**Claude Insight reads data from** `~/.claude/memory/logs/` and `~/.claude/memory/sessions/`

---

## 🚨 SESSION START (MANDATORY)

**At the start of every conversation with Claude, run:**

```bash
bash ~/.claude/memory/session-start.sh
```

This initializes:
1. ✅ Session ID generation
2. ✅ System health checks
3. ✅ Context monitoring
4. ✅ Policy enforcement
5. ✅ Log file creation (for dashboard)

**Dashboard will display:**
- Session ID and timestamp
- System health status
- Active policies
- Context usage

---

## 📊 CORE FEATURES

### 1. System Health Monitoring
- Python availability
- Critical files check
- Daemon status
- Session state

### 2. Policy Enforcement Tracking
- 3-Level Architecture (Sync → Standards → Execution)
- Zero-Tolerance Failure Policy
- Task breakdown and planning
- Model selection

### 3. Cost Analytics
- Token usage per session
- Model selection distribution
- Cost estimation and trends
- Optimization recommendations

### 4. Alert System
- System failures
- Policy violations
- High token usage
- Anomaly detection

---

## 🔧 CONFIGURATION

### Basic Setup

Edit `~/.claude/CLAUDE.md` to configure:

```markdown
# Memory System - ACTIVE ENFORCEMENT MODE

**VERSION:** 2.5.0
**STATUS:** 🟢 FULLY OPERATIONAL

## SESSION START

bash ~/.claude/memory/session-start.sh

## POLICIES

- Zero-Tolerance Failure Policy: ACTIVE
- 3-Level Architecture: ENFORCED
- Auto Task Breakdown: ENABLED
```

### Dashboard Configuration

Edit `.env` file:

```bash
# Flask Configuration
FLASK_ENV=development
SECRET_KEY=your-secret-key-here

# Memory System Paths
CLAUDE_MEMORY_PATH=/path/to/.claude/memory
LOG_PATH=/path/to/.claude/memory/logs

# Dashboard Settings
REFRESH_INTERVAL=5000  # 5 seconds
MAX_LOG_ENTRIES=1000
```

---

## 🛡️ CORE POLICIES

### 1. Zero-Tolerance Failure Policy

**If ANY system fails → ALL work stops immediately**

```bash
# Mandatory before any action
export PYTHONIOENCODING=utf-8
bash ~/.claude/memory/auto-fix-enforcer.sh

# Exit Code 0 = Continue
# Exit Code ≠ 0 = BLOCKED
```

**Dashboard shows:** System failures, blocking status, fix instructions

### 2. 3-Level Architecture

**All work follows this order:**

```
Layer 1: SYNC SYSTEM (Foundation)
   └─ Session Started? Context Checked?

Layer 2: STANDARDS SYSTEM (Rules)
   └─ Coding Standards Loaded?

Layer 3: EXECUTION SYSTEM (Implementation)
   └─ Prompt Generated? Tasks Created? Model Selected?
```

**Dashboard shows:** Layer completion status, violations, progress

---

## 🐛 TROUBLESHOOTING

### Dashboard not loading logs

**Check:**
```bash
# Verify log path
ls ~/.claude/memory/logs/

# Check log files exist
ls ~/.claude/memory/logs/*.log

# Check permissions
chmod 644 ~/.claude/memory/logs/*.log
```

### Session not tracked

**Run session start:**
```bash
bash ~/.claude/memory/session-start.sh
```

**Check output for:**
- ✅ Session ID generated
- ✅ Logs created
- ❌ Any errors

### High memory usage

**Optimize:**
- Reduce `MAX_LOG_ENTRIES` in `.env`
- Clear old session data: `rm ~/.claude/memory/sessions/SESSION-*.json`
- Restart dashboard: `python app.py`

---

## 📖 DOCUMENTATION

### Full Documentation
- **Dashboard Guide:** `docs/DASHBOARD-GUIDE.md`
- **API Reference:** `docs/API-REFERENCE.md`
- **Memory System:** `~/.claude/memory/MASTER-README.md`

### Quick Links
- GitHub: https://github.com/piyushmakhija28/claude-insight
- Issues: https://github.com/piyushmakhija28/claude-insight/issues
- Wiki: https://github.com/piyushmakhija28/claude-insight/wiki

---

## 🎯 SKILLS & AGENTS (OPTIONAL)

**Skills and agents are available separately** in the `claude-global-library` project.

If you want to use pre-built skills (Docker, Kubernetes, Spring Boot) or agents (DevOps, QA, etc.):

1. Download: `https://github.com/piyushmakhija28/claude-global-library`
2. Copy to: `~/.claude/skills/` or `~/.claude/agents/`
3. Use in conversations with Claude

**Claude Insight does NOT require skills/agents** - they are optional enhancements.

---

## 🚀 WHAT'S NEXT?

After setup:
1. ✅ Run `bash ~/.claude/memory/session-start.sh`
2. ✅ Open dashboard at `http://localhost:5000`
3. ✅ Start a conversation with Claude
4. ✅ Watch real-time monitoring in dashboard
5. ✅ Review session analytics and costs

---

## 💡 TIPS

### For Best Results:
- Always run session-start.sh before conversations
- Check dashboard regularly for alerts
- Review cost analytics weekly
- Keep logs under 1000 entries for performance

### Customization:
- Modify dashboard themes in `static/css/`
- Add custom widgets in `templates/dashboard.html`
- Create custom alerts in `alert_routing/`

---

**VERSION:** 2.5.2
**LAST UPDATED:** 2026-02-17
**MAINTAINED BY:** TechDeveloper (https://www.techdeveloper.in)

**For support:** Open an issue on GitHub or check the Wiki for detailed guides.

# Claude Insight - Project Instructions

**Project:** Claude Insight - Monitoring Dashboard for Claude Memory System
**Version:** 2.6.0
**Type:** Public GitHub Repository
**Status:** 🟢 Active

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

3. **Core Documentation:**
   - `MASTER-README.md` - Complete system documentation
   - Policy documentation (enforcement, failure prevention)

4. **Dashboard Files:**
   - Monitoring dashboard UI
   - Analytics visualization
   - Health check displays

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

**VERSION:** 1.0.0 (Project-Specific)
**LAST UPDATED:** 2026-02-17
**TYPE:** Public Project Instructions
**LOCATION:** `claude-insight/CLAUDE.md`

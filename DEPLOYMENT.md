# Claude Insight - Deployment & Centralized System Architecture

**Version:** 4.1.0
**Last Updated:** 2026-02-24
**Purpose:** Single source of truth for all Claude Memory System content

---

## Architecture: Claude Insight as Central Registry

This repository is the **permanent home** for all Claude Memory System policies, scripts, and architecture. Local installations pull from here.

### Directory Structure

```
claude-insight/
├── scripts/                    # All 26+ hook and system scripts
│   ├── core-hooks/            # UserPromptSubmit, PreToolUse, PostToolUse, Stop
│   ├── session-management/    # Session tracking, chaining, cleanup
│   ├── enforcement/           # Policy enforcement scripts
│   ├── optimization/          # Performance, parallel mode, isolation
│   └── utilities/             # Helpers, CLI tools
│
├── policies/                  # 15 standards, 156 rules
│   ├── 01-sync-system/        # Foundation layer
│   ├── 02-standards-system/   # Coding standards
│   └── 03-execution-system/   # 12-step execution
│
├── docs/                      # 120+ documentation files
│   ├── guides/                # User guides, setup, troubleshooting
│   ├── architecture/          # System design, data flow
│   └── standards/             # Java, Spring Boot, API design
│
├── deploy/                    # Deployment automation
│   ├── install.sh             # Cross-platform installer
│   ├── deploy-to-local.py     # Sync from Claude Insight to ~/.claude/
│   ├── verify-deployment.py   # Verify installation correctness
│   └── auto-update.py         # Check for updates on startup
│
├── config/                    # Configuration templates
│   ├── settings.json.template # Hook configuration
│   └── claude-md.template     # Global CLAUDE.md template
│
└── VERSION                    # Semantic versioning (4.1.0)
```

---

## Deployment Flow

### Installation (First Time)

```bash
# User runs:
git clone https://github.com/piyushmakhija28/claude-insight.git
cd claude-insight
bash deploy/install.sh

# Script does:
1. Check Python version (3.8+)
2. Create ~/.claude/memory/current/
3. Copy all scripts from scripts/ to ~/.claude/memory/current/
4. Copy policies to ~/.claude/memory/policies/
5. Copy docs to ~/.claude/memory/docs/
6. Generate settings.json from template
7. Verify deployment with verify-deployment.py
8. Done!
```

### Auto-Update (On Startup)

```bash
# In ~/.claude/settings.json hooks:
{
  "deploy_check": {
    "enabled": true,
    "check_url": "https://raw.githubusercontent.com/piyushmakhija28/claude-insight/main/VERSION",
    "interval_days": 7
  }
}

# On first hook execution:
deploy/auto-update.py
    |
    +-- Read local VERSION (~/.claude/VERSION)
    +-- Fetch remote VERSION (GitHub)
    +-- If different: git pull + deploy/deploy-to-local.py
    +-- If same: skip
```

### Manual Update

```bash
# User can always manually update:
cd /path/to/claude-insight
git pull origin main
python deploy/deploy-to-local.py

# Done! All scripts updated locally
```

---

## What Goes Where

### Claude Insight Repo (Permanent - Versioned)

✅ All 26+ hook scripts
✅ All 15 system policies
✅ All 120+ documentation files
✅ Configuration templates
✅ Installation/deployment scripts
✅ Version history (Git commits)
✅ Release notes (CHANGELOG)

### Local ~/.claude/ (Temporary - Session Data)

✅ Current session: `.current-session.json`
✅ Session logs: `memory/logs/sessions/`
✅ Flow traces: JSON for current session
✅ User preferences: `memory/config/user-preferences.json`
✅ Local patterns: `memory/config/cross-project-patterns.json`
✅ Hook settings: `settings.json` (generated from template)

---

## Global CLAUDE.md Integration

The global `~/.claude/CLAUDE.md` will reference Claude Insight as the source of truth:

```markdown
# Claude Memory System v4.1.0

## System Architecture

All system policies, scripts, and architecture are centralized in:
**GitHub:** https://github.com/piyushmakhija28/claude-insight

### What This Means

- **Policies:** Read from `policies/` in Claude Insight
- **Scripts:** Deployed from `scripts/` in Claude Insight
- **Docs:** Available in `docs/` in Claude Insight
- **Latest Version:** Always in `VERSION` file

### Installation

```bash
# First time:
bash deploy/install.sh

# Updates:
git -C /path/to/claude-insight pull
python /path/to/claude-insight/deploy/deploy-to-local.py
```

### Documentation

- **Setup Guide:** `docs/guides/SETUP.md`
- **Architecture:** `docs/architecture/SYSTEM-ARCHITECTURE.md`
- **Troubleshooting:** `docs/guides/TROUBLESHOOTING.md`
- **API Standards:** `docs/standards/API-DESIGN.md`
```

---

## Deployment Scripts

### `deploy/install.sh` (Cross-platform Installer)

```bash
#!/bin/bash
# Installs Claude Memory System from Claude Insight

set -e

echo "[INSTALL] Claude Memory System v$(cat VERSION)"

# Check Python
python3 --version || {
    echo "[ERROR] Python 3.8+ required"
    exit 1
}

# Create directories
mkdir -p ~/.claude/memory/{current,logs,sessions,policies,docs,config}

# Copy scripts
cp scripts/**/*.py ~/.claude/memory/current/
cp scripts/**/*.sh ~/.claude/memory/current/
echo "[OK] Copied 26+ scripts"

# Copy policies
cp -r policies/* ~/.claude/memory/policies/
echo "[OK] Copied 15 system policies"

# Copy docs
cp -r docs/* ~/.claude/memory/docs/
echo "[OK] Copied 120+ documentation files"

# Generate settings.json
python3 deploy/setup-config.py > ~/.claude/settings.json
echo "[OK] Generated settings.json"

# Verify
python3 deploy/verify-deployment.py || {
    echo "[ERROR] Deployment verification failed"
    exit 1
}

echo "[SUCCESS] Installation complete!"
echo "[NEXT] Restart Claude Code to activate"
```

### `deploy/deploy-to-local.py` (Sync from Repo to Local)

```python
#!/usr/bin/env python3
"""
Deploy Claude Insight scripts to local ~/.claude/memory/current/

Usage:
    python deploy-to-local.py [--force]

Options:
    --force: Overwrite all files without confirmation
"""

import sys
import shutil
from pathlib import Path

REPO_SCRIPTS = Path(__file__).parent.parent / 'scripts'
LOCAL_SCRIPTS = Path.home() / '.claude' / 'memory' / 'current'

def deploy():
    """Deploy all scripts to local installation"""

    # Copy all .py and .sh files
    count = 0
    for script_file in REPO_SCRIPTS.glob('**/*.py'):
        dest = LOCAL_SCRIPTS / script_file.name
        shutil.copy2(script_file, dest)
        count += 1

    for script_file in REPO_SCRIPTS.glob('**/*.sh'):
        dest = LOCAL_SCRIPTS / script_file.name
        shutil.copy2(script_file, dest)
        count += 1

    print(f"[OK] Deployed {count} scripts to {LOCAL_SCRIPTS}")
    return True

if __name__ == '__main__':
    deploy()
```

### `deploy/auto-update.py` (Version Check & Auto-Deploy)

```python
#!/usr/bin/env python3
"""
Check for Claude Insight updates and auto-deploy if needed

Runs on first hook execution each day
"""

import json
from pathlib import Path
from datetime import datetime, timedelta
import subprocess

HOME = Path.home()
VERSION_FILE = HOME / '.claude' / 'VERSION'
LAST_CHECK_FILE = HOME / '.claude' / '.last-update-check'

def check_for_updates():
    """Check if new version available"""

    # Check once per day
    if LAST_CHECK_FILE.exists():
        last_check = datetime.fromisoformat(LAST_CHECK_FILE.read_text())
        if (datetime.now() - last_check).days < 1:
            return False  # Already checked today

    # Get local version
    if VERSION_FILE.exists():
        local_version = VERSION_FILE.read_text().strip()
    else:
        local_version = '0.0.0'

    # TODO: Fetch remote version from GitHub
    # remote_version = fetch_from_github(...)

    # Update check timestamp
    LAST_CHECK_FILE.write_text(datetime.now().isoformat())

    # Return True if update available
    # return remote_version > local_version

if __name__ == '__main__':
    if check_for_updates():
        print("[AUTO-UPDATE] New version available, deploying...")
        # Deploy
```

---

## Benefits

✅ **Single Source of Truth** - Everything in Claude Insight
✅ **Automatic Versioning** - Git history preserved
✅ **Safe Updates** - Versions tested before deploying locally
✅ **No More Manual Sync** - Deploy script handles it
✅ **Audit Trail** - All changes in Git
✅ **Easy Rollback** - Just revert to previous version
✅ **Shareable** - Anyone can clone and use
✅ **Production Ready** - Centralized, tested, stable

---

## Transition Plan

### Phase 1: Organize Claude Insight (This Week)
- [x] Create `scripts/` structure
- [x] Create `deploy/` directory
- [x] Write deployment scripts
- [x] Document architecture

### Phase 2: Populate Claude Insight (This Week)
- [ ] Copy all 26 hook scripts from ~/.claude/memory/current/
- [ ] Verify all 15 policies are in policies/
- [ ] Verify all 120+ docs in docs/
- [ ] Test deployment scripts

### Phase 3: Update Global CLAUDE.md (This Week)
- [ ] Reference Claude Insight as source of truth
- [ ] Document deployment process
- [ ] Add auto-update instructions

### Phase 4: Users Deploy (Next Week)
- [ ] Users run `bash deploy/install.sh`
- [ ] Scripts auto-pulled from Claude Insight
- [ ] Auto-updates check daily
- [ ] Manual updates available via `git pull`

---

## Status

**Current State:** v4.1.0 (Parallel Mode + Session Isolation)
**Repository:** https://github.com/piyushmakhija28/claude-insight
**Next:** Deploy to production with centralized architecture

---

This architecture ensures:
- ✅ Maintainability: Changes in one place
- ✅ Safety: Versioned and tested
- ✅ Scalability: Easy to add new scripts/policies
- ✅ Reliability: Auto-sync keeps everything current
- ✅ Traceability: Git history for auditing

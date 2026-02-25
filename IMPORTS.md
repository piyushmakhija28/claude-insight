# Import Guide for Claude Insight

This document explains how to handle imports correctly in Claude Insight.

## Import Types

### 1. LOCAL IMPORTS (Same Project)

**Use relative imports for modules within `src/`:**

```python
# ✅ CORRECT - Relative import
from services.monitoring.metrics_collector import MetricsCollector
from services.ai.anomaly_detector import AnomalyDetector
from utils.import_manager import ImportManager

# ❌ WRONG - Avoid absolute paths
from /Users/techd/.../src/services import ...
```

**Location:** `src/`
**Examples:**
- `app.py` → `from services.monitoring.metrics_collector import MetricsCollector`
- `services/ai/anomaly_detector.py` → `from services.monitoring.log_parser import LogParser`

---

### 2. SCRIPT IMPORTS (Same Project Scripts)

**Use relative paths with `pathlib` for cross-platform compatibility:**

```python
# ✅ CORRECT - Cross-platform path
from pathlib import Path
MEMORY_BASE = Path.home() / '.claude' / 'memory'
INSIGHT_DIR = Path(__file__).parent.parent

# ❌ WRONG - Hardcoded paths
MEMORY = "/Users/techd/.claude/memory"
```

**Location:** `scripts/`
**Examples:**
- `scripts/3-level-flow.py`: Uses `Path.home() / '.claude'` for cross-platform
- `scripts/clear-session-handler.py`: Uses `Path(__file__).parent` for relative paths

---

### 3. CLAUDE-GLOBAL-LIBRARY IMPORTS (External)

**Use GitHub raw URLs when referencing claude-global-library:**

```python
# ✅ CORRECT - GitHub URL
url = "https://raw.githubusercontent.com/piyushmakhija28/claude-global-library/main/skills/docker/skill.md"
with urllib.request.urlopen(url) as response:
    skill_content = response.read().decode('utf-8')

# Use ImportManager helper
from utils.import_manager import ImportManager
docker_skill = ImportManager.get_skill('docker')
```

**Pattern:** `https://raw.githubusercontent.com/piyushmakhija28/claude-global-library/main/<type>/<name>/<file>`

**For Skills:**
```
https://raw.githubusercontent.com/piyushmakhija28/claude-global-library/main/skills/docker/skill.md
https://raw.githubusercontent.com/piyushmakhija28/claude-global-library/main/skills/kubernetes/skill.md
https://raw.githubusercontent.com/piyushmakhija28/claude-global-library/main/skills/backend/java-spring-boot-microservices/skill.md
```

**For Agents:**
```
https://raw.githubusercontent.com/piyushmakhija28/claude-global-library/main/agents/orchestrator-agent/agent.md
https://raw.githubusercontent.com/piyushmakhija28/claude-global-library/main/agents/devops-engineer/agent.md
https://raw.githubusercontent.com/piyushmakhija28/claude-global-library/main/agents/qa-testing-agent/agent.md
```

---

## ImportManager Usage

Located in `src/utils/import_manager.py`, provides unified interface:

### Load a Skill
```python
from utils.import_manager import ImportManager

docker = ImportManager.get_skill('docker')
# Returns: {'name': 'docker', 'content': '...', 'source': 'github', 'url': '...'}
```

### Load an Agent
```python
orchestrator = ImportManager.get_agent('orchestrator-agent')
# Returns: {'name': 'orchestrator-agent', 'content': '...', 'source': 'github', 'url': '...'}
```

### Load a Policy
```python
policy = ImportManager.get_policy('01-sync-system/context-management/README.md')
# Returns: policy content string
```

### Quick Reference URLs
```python
from utils.import_manager import SKILL_URLS, AGENT_URLS, POLICY_URLS

# All available URLs mapped
SKILL_URLS = {
    'docker': 'https://...',
    'kubernetes': 'https://...',
    'python-system-scripting': 'https://...',
}

AGENT_URLS = {
    'orchestrator': 'https://...',
    'devops': 'https://...',
}
```

---

## Path Resolution

For accessing local files across platforms:

```python
from pathlib import Path

# ✅ CORRECT
home = Path.home()
memory = home / '.claude' / 'memory'
sessions = memory / 'sessions'

# ✅ CORRECT - Relative to script
script_dir = Path(__file__).parent
project_root = Path(__file__).parent.parent.parent

# ❌ WRONG - Hardcoded paths
memory = "/Users/techd/.claude/memory"
```

---

## Current Import Status

### ✅ Local Imports - VERIFIED
- All `src/` modules use correct relative imports
- All `scripts/` use Path.home() for cross-platform compatibility
- App.py correctly imports from services/ and utils/

### ✅ GitHub URLs - CONFIGURED
- DockerSKill: `https://raw.githubusercontent.com/.../docker/skill.md`
- Kubernetes: `https://raw.githubusercontent.com/.../kubernetes/skill.md`
- Agents: `https://raw.githubusercontent.com/.../agents/*/agent.md`

### ✅ Script Architecture - CORRECT
- 01-sync-system: `scripts/architecture/01-sync-system/`
- 02-standards-system: `scripts/architecture/02-standards-system/`
- 03-execution-system: `scripts/architecture/03-execution-system/`

---

## Summary

| Type | Pattern | Location | Example |
|------|---------|----------|---------|
| **Local Modules** | `from services.X import Y` | `src/` | `from services.monitoring.metrics_collector import MetricsCollector` |
| **Local Paths** | `Path.home() / '.claude'` | `scripts/` | `MEMORY = Path.home() / '.claude' / 'memory'` |
| **Claude-Global Skills** | `GITHUB_URL/skills/X/skill.md` | GitHub | `https://raw.../skills/docker/skill.md` |
| **Claude-Global Agents** | `GITHUB_URL/agents/X/agent.md` | GitHub | `https://raw.../agents/orchestrator-agent/agent.md` |
| **Helper** | `ImportManager.get_skill()` | `src/utils/import_manager.py` | `ImportManager.get_skill('docker')` |

---

**Last Updated:** 2026-02-25
**Version:** 1.0.0

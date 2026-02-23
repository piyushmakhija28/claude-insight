# Claude Insight Sync Guide
Complete guide for syncing content between local system and public repos.

---

## 🔄 CLAUDE INSIGHT AUTO-UPDATE RULE (MANDATORY -- PERMANENT)

**BHAI YE RULE YAAD RAKH: System changes = Claude Insight update AUTOMATICALLY**

### When MUST I Update Claude Insight:

**After ANY of these actions -- auto-update Claude Insight WITHOUT being asked:**

| Action | Claude Insight Update Required |
|--------|-------------------------------|
| New policy added to CLAUDE.md | YES -- update relevant policy .md in claude-insight/policies/ |
| Existing policy changed | YES -- update the matching policy file |
| New standard added (Level 2) | YES -- add/update in claude-insight/docs/ or policies/ |
| Task breakdown rule changed | YES -- update task-phase-enforcement-policy.md |
| Model selection rule changed | YES -- update model-selection-enforcement.md |
| New hook added | YES -- update CLAUDE.md in claude-insight + scripts/ |
| Architecture change | YES -- update ARCHITECTURE.md in claude-insight/docs/ |
| Version bump in local system | YES -- bump VERSION in claude-insight too |

### HOW to Update Claude Insight:

```
1. Make local system changes (CLAUDE.md, scripts, policies)
2. Immediately find matching file in:
   C:\Users\techd\Documents\workspace-spring-tool-suite-4-4.27.0-new\claude-insight\
3. Update the matching policy/doc file
4. Update CHANGELOG.md (add entry under [Unreleased] or new version)
5. Bump VERSION file
6. git add + git commit + git push origin main
7. NO user reminder needed -- I do this automatically
```

### Why This Matters:
- Claude Insight is the monitoring dashboard for the ENTIRE Claude system
- If local policies change but Claude Insight is not updated -> dashboard shows stale/wrong info
- User should NEVER have to remind me to sync Claude Insight
- This is AUTOMATIC -- always done as part of any system-level change

### Detection Keywords (I watch for these):
- "policy change", "new rule", "update CLAUDE.md"
- "system improvement", "step 3.X change"
- Any edit to: `~/.claude/CLAUDE.md`, `~/.claude/memory/03-execution-system/**`
- Any change in: task breakdown, model selection, plan mode, skill/agent rules

**ENFORCEMENT:** After this rule, every system change = Claude Insight sync. No exceptions.

---

## 🔄 SMART AUTO-SYNC TO CLAUDE-INSIGHT (MANDATORY WITH DETECTION)

**🚨 CRITICAL: Claude Insight is a PUBLIC GITHUB REPOSITORY - ONLY sync CORE MEMORY SYSTEM files!**

### 🎯 What is Claude Insight?

**Claude Insight** = Public monitoring dashboard for Claude Memory System v2.5.0
- **Users worldwide** download it from GitHub
- Contains **monitoring dashboard + core memory system files ONLY**
- **NO skills, NO agents, NO optimization patterns** (those go to claude-global-library)
- **NOT for project-specific** business logic or proprietary code

**Repository:** https://github.com/piyushmakhija28/claude-insight

---

### 🚨 CRITICAL RULE: What Goes Where

**✅ SYNC to Claude Insight (Core Memory System ONLY):**
- Core policies (3-level architecture, zero-tolerance, auto-fix enforcement)
- Core automation scripts (session-start.sh, auto-fix-enforcer.py, blocking-policy-enforcer.py)
- Core documentation (MASTER-README.md, policy docs)
- Dashboard-related files
- **NO skills, NO agents, NO optimization patterns**

**✅ SYNC to Claude Global Library (Skills/Agents/Patterns):**
- Skills (Docker, Kubernetes, Java, optimization, etc.)
- Agents (DevOps, Spring Boot, QA, etc.)
- Design patterns, optimization patterns
- **Repository:** https://github.com/piyushmakhija28/claude-global-library

**❌ DO NOT SYNC (Project-Specific - Keep Private):**
- Skills/agents with project names (`surgricalswale-*`, `techdeveloper-*`)
- Business logic specific to your company
- Project source code, configs, secrets
- Internal documentation, proprietary workflows
- Anything with: `surgricalswale`, `techdeveloper`, company-specific terms

---

### 🔍 MANDATORY DETECTION BEFORE SYNC

**BEFORE syncing ANYTHING, MUST run detection:**

```bash
# For skills
python ~/.claude/memory/detect-sync-eligibility.py --skill "skill-name"

# For agents
python ~/.claude/memory/detect-sync-eligibility.py --agent "agent-name"

# For files
python ~/.claude/memory/detect-sync-eligibility.py --file "path/to/file"
```

**Detection Output:**
- ✅ `SYNC: This is global/reusable` -> Exit code 0 -> **SAFE TO SYNC**
- ❌ `NO SYNC: This is project-specific` -> Exit code 1 -> **DO NOT SYNC**
- ⚠️ `WARNING: Contains project references` -> Exit code 2 -> **CLEANUP FIRST**

---

### ⚡ SMART SYNC COMMANDS

**For Claude Insight (Core Memory System ONLY):**

```bash
# Sync core policy (auto-detects if eligible)
bash ~/.claude/memory/smart-sync-to-claude-insight.sh --policy "3-level-architecture.md"

# Sync core doc (auto-detects if eligible)
bash ~/.claude/memory/smart-sync-to-claude-insight.sh --doc "auto-fix-enforcement.md"

# Sync core script (auto-detects if eligible)
bash ~/.claude/memory/smart-sync-to-claude-insight.sh --script "auto-fix-enforcer.py"

# Sync CLAUDE.md (dashboard-focused version)
bash ~/.claude/memory/smart-sync-to-claude-insight.sh --claude-md

# Sync MASTER-README (core documentation)
bash ~/.claude/memory/smart-sync-to-claude-insight.sh --master-readme
```

**For Claude Global Library (Skills/Agents):**

```bash
# ❌ DO NOT use smart-sync for skills/agents
# ✅ Manually copy to claude-global-library:

cp -r ~/.claude/skills/docker /path/to/claude-global-library/skills/
cp -r ~/.claude/agents/devops-engineer /path/to/claude-global-library/agents/
```

**Smart sync will:**
1. ✅ Run detection first
2. ✅ Only sync CORE files to Claude Insight
3. ✅ Block skills/agents (they go to claude-global-library)
4. ✅ Block project-specific content

---

### 📋 What to Sync - Examples

| Type | ✅ Claude Insight (Core) | ✅ Claude Global Library | ❌ NO SYNC (Private) |
|------|--------------------------|--------------------------|----------------------|
| **Skills** | ❌ None (wrong repo) | `docker`, `kubernetes`, `java` | `surgricalswale-*` |
| **Agents** | ❌ None (wrong repo) | `devops-engineer`, `qa-agent` | `techdeveloper-*` |
| **Policies** | `3-level-architecture`, `zero-tolerance` | ❌ None (core only) | Project-specific |
| **Docs** | `MASTER-README.md`, `auto-fix-enforcement.md` | `optimization-patterns.md` | `Surgricalswale-API.md` |
| **Scripts** | `auto-fix-enforcer.py`, `session-start.sh` | ❌ None (core only) | `deploy-surgricalswale.sh` |

---

### 🚨 ENFORCEMENT RULES

**I MUST follow these rules:**

1. **NEVER blindly sync** without detection
   - ❌ WRONG: `cp -r ~/.claude/skills/new-skill claude-insight/`
   - ✅ CORRECT: `bash smart-sync-to-claude-insight.sh --skill "new-skill"`

2. **ALWAYS check detection output**
   - Exit code 0 -> Proceed with sync
   - Exit code 1 -> DO NOT SYNC (project-specific)
   - Exit code 2 -> Cleanup first, then sync

3. **NEVER sync if name contains:**
   - `surgricalswale`, `techdeveloper`, `piyush`
   - Or any other project-specific identifier

4. **NEVER sync if content contains:**
   - Business logic for specific company
   - Secrets, credentials, API keys
   - Hardcoded project URLs (techdeveloper.in, surgricalswale.in)

5. **ASK USER if uncertain:**
   - If detection shows WARNING (exit code 2)
   - If not sure if something is global vs project-specific
   - When in doubt, DO NOT SYNC

---

### 🎯 When I MUST Sync (After Detection)

**To Claude Insight (Core Memory System ONLY):**

| Type | When | Command |
|------|------|---------|
| **Core Policy** | After creation + detection ✅ | `bash smart-sync-to-claude-insight.sh --policy "policy.md"` |
| **Core Doc** | After creation + detection ✅ | `bash smart-sync-to-claude-insight.sh --doc "doc.md"` |
| **Core Script** | After creation + detection ✅ | `bash smart-sync-to-claude-insight.sh --script "script.py"` |
| **CLAUDE.md** | After updates (dashboard version) | `bash smart-sync-to-claude-insight.sh --claude-md` |
| **MASTER-README** | After updates | `bash smart-sync-to-claude-insight.sh --master-readme` |

**To Claude Global Library (Manual Copy):**

| Type | When | Command |
|------|------|---------|
| **New Skill** | After creation ✅ | `cp -r ~/.claude/skills/name /path/to/claude-global-library/skills/` |
| **New Agent** | After creation ✅ | `cp -r ~/.claude/agents/name /path/to/claude-global-library/agents/` |
| **Optimization Pattern** | After creation ✅ | `cp -r ~/.claude/docs/pattern.md /path/to/claude-global-library/docs/` |

**❌ NEVER Sync to Claude Insight:**
- ❌ Skills (go to claude-global-library)
- ❌ Agents (go to claude-global-library)
- ❌ Optimization patterns (go to claude-global-library)
- ❌ Project-specific content (stays private)

---

### 🔧 Manual Override (Advanced)

**To force sync/no-sync, add comment in file:**

```markdown
# CLAUDE-INSIGHT: SYNC
<!-- This forces sync even if detection warns -->
```

```markdown
# CLAUDE-INSIGHT: NO-SYNC
<!-- This blocks sync even if detection passes -->
```

**Use sparingly - trust automated detection!**

---

### 📖 Full Documentation

**Complete sync policy:** `~/.claude/memory/CLAUDE-INSIGHT-SYNC-POLICY.md`

**Detection script:** `~/.claude/memory/detect-sync-eligibility.py`

**Smart sync script:** `~/.claude/memory/smart-sync-to-claude-insight.sh`

---

### ✅ Summary

**Golden Rules:**
> **Core Memory System -> Claude Insight** (monitoring dashboard)
> **Skills/Agents/Patterns -> Claude Global Library** (separate project)
> **Project-Specific -> Private** (never sync)

**I MUST:**
- ✅ Run detection first
- ✅ Sync ONLY core files to Claude Insight
- ✅ **NEVER sync skills/agents to Claude Insight**
- ✅ Skills/agents go to claude-global-library (manually)
- ✅ Protect proprietary content
- ✅ Keep Claude Insight focused on monitoring ONLY
- ✅ **NEVER sync global CLAUDE.md to ANY public repo**

---

## 🔒 GLOBAL CLAUDE.MD SYNC BLOCK POLICY (MANDATORY)

**🚨 CRITICAL: Global CLAUDE.md (~/.claude/CLAUDE.md) is PERSONAL and should NEVER leave your local machine!**

### 🎯 The Problem

Global CLAUDE.md contains:
- ❌ Personal paths (`C:\Users\techd\...`)
- ❌ Private session management settings
- ❌ Personal workflow preferences
- ❌ Context that's meaningless to other users
- ❌ Settings specific to your machine

**If synced to public repos:**
- 😕 Confuses other users ("Who is techd?")
- 🔓 Exposes personal information
- 🚫 Creates wrong context for public consumption
- 💥 Breaks for anyone else who downloads the repo

### ✅ The Solution

**Each repo gets its own project-specific CLAUDE.md:**

| Repository | CLAUDE.md Location | Purpose |
|------------|-------------------|---------|
| **Global (Personal)** | `~/.claude/CLAUDE.md` | Personal memory system settings (NEVER sync) |
| **Claude Insight** | `claude-insight/CLAUDE.md` | Monitoring dashboard project instructions |
| **Claude Global Library** | `claude-global-library/CLAUDE.md` | Skills/agents library project instructions |
| **Your Projects** | `project-name/CLAUDE.md` | Project-specific instructions |

### 🛡️ Enforcement Layers

**1. Detection Script (`detect-sync-eligibility.py`):**
```python
# Blocks if:
- File name is "CLAUDE.md" AND path contains "/.claude/" or "\.claude\"
- Content contains "GLOBAL-CLAUDE-MD-DO-NOT-SYNC"
- Content contains personal paths like "C:\Users\techd"
```

**2. Smart Sync Script (`smart-sync-to-claude-insight.sh`):**
```bash
# --claude-md flag is BLOCKED
# Exit code 1 with error message
# Explains why and what to do instead
```

**3. This Documentation:**
```markdown
# Clear rules at the top (you're reading them now!)
# Detection keyword in content
# Triple-layer protection
```

### 📋 What to Do Instead

**❌ WRONG:**
```bash
# Don't do this!
cp ~/.claude/CLAUDE.md claude-insight/CLAUDE.md
git add claude-insight/CLAUDE.md
git push
# This exposes personal settings to the world!
```

**✅ CORRECT:**
```bash
# Each public repo has its own project-specific CLAUDE.md
# Already created in:
# - claude-insight/CLAUDE.md (monitoring dashboard focused)
# - claude-global-library/CLAUDE.md (skills/agents focused)

# These files are:
# ✅ Project-specific
# ✅ Public-friendly
# ✅ No personal paths
# ✅ Helpful for other users
```

### 🧪 Testing

**Test that global CLAUDE.md is blocked:**
```bash
# Detection script
python ~/.claude/memory/detect-sync-eligibility.py --file "~/.claude/CLAUDE.md"
# Expected: Exit code 1, "NO SYNC: This is the GLOBAL CLAUDE.md"

# Smart sync script
bash ~/.claude/memory/smart-sync-to-claude-insight.sh --claude-md
# Expected: Exit code 1, detailed error message
```

### 📖 Summary

**Golden Rule:**
> **Global CLAUDE.md stays HOME (~/.claude/)**
> **Public repos get their own project-specific CLAUDE.md**

**Detection Keyword (in global CLAUDE.md):**
```
GLOBAL-CLAUDE-MD-DO-NOT-SYNC
```

**If you see global CLAUDE.md in a public repo:**
1. 🚨 **REMOVE IT IMMEDIATELY**
2. ✅ Create project-specific CLAUDE.md instead
3. ✅ Git commit the removal
4. ✅ Git push the fix

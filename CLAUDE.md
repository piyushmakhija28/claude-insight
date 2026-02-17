# Memory System - ACTIVE ENFORCEMENT MODE

**VERSION:** 2.6.0 (Clean Project Separation + Sync Rules)
**STATUS:** 🟢 FULLY OPERATIONAL

---

> ## 🔒🔒🔒 GLOBAL CLAUDE.MD - NEVER OVERRIDE 🔒🔒🔒
>
> **CRITICAL RULE: Global CLAUDE.md is NEVER overridden by project CLAUDE.md**
>
> **Merge Policy:**
> - ✅ Global CLAUDE.md = **BASE (Always Applied)**
> - ✅ Project CLAUDE.md = **ADDITIONAL INFO ONLY**
> - ✅ Merge: Global + Project extras
> - ❌ **NEVER replace global settings**
>
> **Precedence:**
> 1. Global policies = **MANDATORY** (cannot be changed)
> 2. Global settings = **DEFAULT** (cannot be overridden)
> 3. Project specifics = **ADDITIONAL** (merged, not replaced)
>
> See section: [CLAUDE.md Merge Policy](#-claudemd-merge-policy-mandatory-)

---

> ## 🚨🚨🚨 ZERO-TOLERANCE POLICY 🚨🚨🚨
>
> **IF ANY POLICY OR SYSTEM FAILS → ALL WORK STOPS IMMEDIATELY**
>
> **MANDATORY FIRST STEP BEFORE ANY ACTION:**
> ```bash
> export PYTHONIOENCODING=utf-8
> bash ~/.claude/memory/auto-fix-enforcer.sh
> ```
>
> **Exit Code ≠ 0 = BLOCKED - No work until fixed!**
>
> See section: [Zero-Tolerance Failure Policy](#-zero-tolerance-failure-policy-v250-)

---

> **📖 COMPREHENSIVE DOCUMENTATION:** For complete system documentation with full indexing, all policies, Java Spring Boot standards, optimization strategies, security best practices, and detailed examples, see:
>
> **[~/.claude/memory/MASTER-README.md](file:///C:/Users/techd/.claude/memory/MASTER-README.md)**
>
> This CLAUDE.md provides quick reference and session start instructions. The MASTER-README contains the complete consolidated knowledge base.

---

## 🚨 CRITICAL: MANDATORY EXECUTION AT SESSION START

**AT THE START OF EVERY CONVERSATION, I MUST RUN:**

```bash
bash ~/.claude/memory/session-start.sh
```

**This automatically:**
1. ✅ Starts auto-recommendation daemon (9th daemon)
2. ✅ Checks all 9 daemon PIDs and status
3. ✅ Shows latest recommendations (model, skills, agents)
4. ✅ Shows context status (OK/WARNING/CRITICAL)
5. ✅ **Detects active Claude Code plan (Free/Pro/Team/Enterprise)**
6. ✅ **Generates unique Session ID for tracking**
7. ✅ Provides complete system health summary

**I MUST apply these recommendations BEFORE responding!**

**🎯 MANDATORY: After session start, I MUST provide the Session ID to user:**
- Format: `SESSION-YYYYMMDD-HHMMSS-XXXX`
- Example: `SESSION-20260216-173003-09RZ`
- **Always show this ID** for tracking purposes
- User needs this to track the session in logs

**Alternative (If above fails):**
```bash
nohup python ~/.claude/memory/auto-recommendation-daemon.py start > /dev/null 2>&1 &
sleep 2
python ~/.claude/memory/session-start-check.py
```

**⚠️ CRITICAL: Always use `python` command, NOT `python3`!**

---

## 🚨 ZERO-TOLERANCE FAILURE POLICY (v2.5.0) 🚨

**🔴 CRITICAL RULE: IF ANY POLICY OR SYSTEM FAILS → STOP ALL WORK IMMEDIATELY**

### **Mandatory Before EVERY Action:**

```bash
export PYTHONIOENCODING=utf-8
bash ~/.claude/memory/auto-fix-enforcer.sh
```

**Exit Code 0:** ✅ All systems OK → Continue work
**Exit Code ≠ 0:** 🚨 **STOP EVERYTHING** → Fix failures → Retry

### **What Gets Checked:**

| Check | Priority | If Fails |
|-------|----------|----------|
| Python availability | 🔴 CRITICAL | **BLOCK ALL WORK** |
| Critical files present | 🔴 CRITICAL | **BLOCK ALL WORK** |
| Blocking enforcer initialized | 🔴 CRITICAL | **BLOCK ALL WORK** (auto-fix) |
| Session state valid | 🟠 HIGH | **BLOCK ALL WORK** |
| Daemon status | ℹ️ INFO | Continue (just report) |
| Git repository | ℹ️ INFO | Continue (just report) |

### **Enforcement Rules:**

1. **🚨 BEFORE responding to ANY user request:**
   - Run auto-fix-enforcer.sh FIRST
   - Check exit code
   - If ≠ 0: **STOP, report failures, wait for fix**

2. **🚨 BEFORE using ANY tool:**
   - Verify systems are OK
   - If enforcer failed earlier: **REFUSE to proceed**

3. **🚨 BEFORE starting ANY task:**
   - Systems must be operational
   - No exceptions, no workarounds

4. **🚨 IF any failure detected:**
   - **IMMEDIATELY stop all work**
   - Report failure clearly
   - Provide fix instructions
   - Wait for user to fix
   - Re-run enforcer
   - Only continue when exit code = 0

### **Auto-Fix Capabilities:**

- ✅ **Can auto-fix:** Blocking enforcer state, session markers
- ⚠️ **Manual fix needed:** Python install, missing files, daemons

### **Philosophy:**

- ❌ **NEVER** work around failures
- ❌ **NEVER** ignore warnings
- ❌ **NEVER** proceed with broken systems
- ✅ **ALWAYS** fix immediately and properly
- ✅ **ALWAYS** verify before continuing

### **Example:**

```
User: "Create a new service"
Me:
  1. Run auto-fix-enforcer.sh
  2. Check exit code
  3. If 0 → Proceed with creating service
  4. If ≠ 0 → "🚨 System failures detected. Fix these first: [list]"
```

**📖 Full docs:** `~/.claude/memory/docs/auto-fix-enforcement.md`

---

## 🔒 CLAUDE.MD MERGE POLICY (MANDATORY) 🔒

**🔴 CRITICAL: Global CLAUDE.md is NEVER overridden by project-specific CLAUDE.md**

### **The Problem:**

Projects may have their own `CLAUDE.md` files with project-specific instructions. However:
- ❌ **NEVER** let project CLAUDE.md override global settings
- ❌ **NEVER** let project CLAUDE.md disable global policies
- ❌ **NEVER** let project CLAUDE.md change enforcement rules

### **The Solution: MERGE, Not Override**

```
Final Configuration = Global CLAUDE.md + Project CLAUDE.md (extras only)
```

### **Merge Rules:**

| Type | Source | Can Override? | Action |
|------|--------|---------------|--------|
| **Policies** | Global | ❌ NEVER | Always enforced from global |
| **Enforcement** | Global | ❌ NEVER | Always from global |
| **System Settings** | Global | ❌ NEVER | Always from global |
| **Project Info** | Project | ✅ YES | Add to context (not replace) |
| **Project Rules** | Project | ✅ YES | Add to context (additional) |
| **Project Paths** | Project | ✅ YES | Add to context |

### **Precedence Order:**

```
1. 🔴 Global Policies (MANDATORY - Cannot be changed)
   - Zero-Tolerance Failure Policy
   - Auto-Fix Enforcement
   - Session ID Tracking
   - Task/Phase Breakdown
   - Model Selection
   - All enforcement policies

2. 🟠 Global Settings (DEFAULT - Cannot be overridden)
   - Session start procedure
   - Context optimization rules
   - Tool usage policies
   - Git/GitHub rules
   - Background automation

3. 🟢 Global Standards (BASELINE - Applied first)
   - Java Spring Boot standards
   - Config Server rules
   - Secret Management
   - API design patterns

4. 🔵 Project-Specific (ADDITIONAL - Merged in)
   - Project structure
   - Project-specific paths
   - Project conventions
   - Additional requirements
   - Project documentation
```

### **How I MUST Handle Both Files:**

**Step 1: Load Global CLAUDE.md (ALWAYS FIRST)**
```
✅ Load: ~/.claude/CLAUDE.md
✅ Parse all policies, settings, standards
✅ Mark as BASELINE (cannot be overridden)
```

**Step 2: Check for Project CLAUDE.md**
```
✅ Check: <project-root>/CLAUDE.md exists?
✅ If YES: Continue to Step 3
✅ If NO: Use only global CLAUDE.md
```

**Step 3: Load Project CLAUDE.md (ADDITIONAL ONLY)**
```
✅ Load: <project-root>/CLAUDE.md
✅ Extract ONLY project-specific information:
   - Project structure/paths
   - Project-specific conventions
   - Additional requirements
   - Project documentation

❌ IGNORE any attempts to override:
   - Policies
   - Enforcement rules
   - System settings
   - Global standards
```

**Step 4: Merge (Global + Project Extras)**
```
✅ Start with Global CLAUDE.md (complete)
✅ Add project-specific info from Project CLAUDE.md
✅ Keep global policies intact
✅ Result: Enhanced context with project info
```

### **Example Merge:**

**Global CLAUDE.md says:**
```
- Zero-Tolerance Failure Policy: MANDATORY
- Session ID: Must show on every session start
- Auto-Fix Enforcement: BLOCKING
```

**Project CLAUDE.md says:**
```
- Project Name: "MyApp"
- Project Path: /path/to/myapp
- Tech Stack: React, Node.js
- Specific Rule: "Always use TypeScript"
```

**❌ WRONG (Override):**
```
Use ONLY project CLAUDE.md
Ignore global policies
```

**✅ CORRECT (Merge):**
```
Global Policies: ACTIVE (unchanged)
  - Zero-Tolerance Failure Policy
  - Session ID tracking
  - Auto-Fix Enforcement

PLUS Project Info:
  - Project: MyApp
  - Path: /path/to/myapp
  - Tech: React, Node.js
  - Extra Rule: Use TypeScript
```

### **What Can Be Added from Project CLAUDE.md:**

**✅ Allowed (Additional Context):**
1. Project name, description, purpose
2. Project-specific file paths
3. Project structure/organization
4. Technology stack details
5. Project-specific coding conventions
6. Custom build/deploy scripts
7. Project documentation links
8. Team-specific preferences
9. Additional linting rules
10. Project-specific constants

**❌ Forbidden (Cannot Override):**
1. ~~Disable zero-tolerance policy~~
2. ~~Skip auto-fix enforcement~~
3. ~~Change session ID rules~~
4. ~~Override model selection~~
5. ~~Disable task breakdown~~
6. ~~Change Git/GitHub rules~~
7. ~~Modify context optimization~~
8. ~~Skip session start procedure~~
9. ~~Change global standards~~
10. ~~Disable any enforcement~~

### **Enforcement Code:**

**I MUST follow this logic:**

```python
# Pseudo-code for merge logic

def load_claude_md_config():
    # Step 1: Load global (MANDATORY)
    global_config = load_file("~/.claude/CLAUDE.md")
    global_policies = extract_policies(global_config)
    global_settings = extract_settings(global_config)

    # Mark as immutable
    global_policies.lock()
    global_settings.lock()

    # Step 2: Check for project CLAUDE.md
    project_claude_md = find_project_claude_md()

    if not project_claude_md:
        # No project file, use global only
        return global_config

    # Step 3: Load project CLAUDE.md (extras only)
    project_config = load_file(project_claude_md)
    project_extras = extract_project_specifics(project_config)

    # Step 4: Merge
    final_config = {
        'policies': global_policies,        # ← GLOBAL (locked)
        'settings': global_settings,        # ← GLOBAL (locked)
        'standards': global_standards,      # ← GLOBAL (baseline)
        'project': project_extras           # ← PROJECT (additional)
    }

    return final_config
```

### **What I Say to User:**

**When both files exist:**

```
📋 Configuration Loaded:

✅ Global CLAUDE.md: Loaded (all policies active)
✅ Project CLAUDE.md: Loaded (additional context added)

🔒 Global Policies: ENFORCED
   - Zero-Tolerance Failure Policy
   - Auto-Fix Enforcement
   - Session ID Tracking
   - [All global policies active]

📂 Project Context: ADDED
   - Project: MyApp
   - Path: /path/to/myapp
   - Tech Stack: React, Node.js
   - [Project-specific info loaded]

🎯 Merge Status: SUCCESS
   Global policies UNCHANGED
   Project info MERGED
```

### **Detection of Override Attempts:**

**If project CLAUDE.md tries to override:**

```
❌ OVERRIDE ATTEMPT DETECTED in project CLAUDE.md:

Attempted: "Disable Zero-Tolerance Policy"
Action: IGNORED
Reason: Global policies cannot be overridden

✅ Global Policy REMAINS ACTIVE
```

**I MUST:**
1. Detect override attempts
2. Ignore them completely
3. Warn user about the attempt
4. Continue with global policy

### **Summary:**

**Simple Rule:**
```
Global CLAUDE.md = BOSS (always in charge)
Project CLAUDE.md = ASSISTANT (helps with project info)
```

**Analogy:**
- Global CLAUDE.md = Constitution (cannot be changed)
- Project CLAUDE.md = Local laws (additional, not conflicting)

**Result:**
- ✅ Global policies always active
- ✅ Project context enhanced
- ✅ No conflicts
- ✅ Best of both worlds

---

## 🔧 BACKGROUND AUTOMATION

**9 daemons run 24/7, auto-started on Windows login:**

1. context-daemon - Monitors context usage
2. session-auto-save-daemon - Auto-saves sessions
3. preference-auto-tracker - Learns preferences
4. skill-auto-suggester - Suggests skills
5. commit-daemon - Auto-commits changes
6. session-pruning-daemon - Cleans sessions
7. pattern-detection-daemon - Detects patterns
8. failure-prevention-daemon - Learns failures
9. auto-recommendation-daemon - Generates recommendations (every 5 sec)

---

## 🆔 SESSION ID TRACKING (MANDATORY)

**Every session and work item gets a unique tracking ID!**

### **Format:**
```
SESSION-YYYYMMDD-HHMMSS-XXXX
```

**Example:** `SESSION-20260216-173003-09RZ`

### **When Generated:**
- ✅ **Session start** - Automatically during session-start.sh
- ✅ **Work item start** - When starting any major task
- ✅ **On request** - Anytime user asks

### **Mandatory Display:**

**I MUST show Session ID after:**
1. Running session-start.sh
2. Starting any new work/task
3. User explicitly requests it

**Format to show:**
```
🆔 Session ID: SESSION-20260216-173003-09RZ
```

### **Session ID Banner:**

Full banner displayed automatically:
```
================================================================================
📋 SESSION ID FOR TRACKING
================================================================================

🆔 Session ID: SESSION-20260216-173003-09RZ
📅 Started: 2026-02-16T17:30:03
📊 Status: ACTIVE
📝 Description: Session started at 2026-02-16 17:30:03

💡 Use this ID to track this session in logs and reports
================================================================================
```

### **Usage:**

**Generate new session:**
```bash
bash ~/.claude/memory/session-id-generator.sh create --description "Your description"
```

**Show current session:**
```bash
bash ~/.claude/memory/session-id-generator.sh current
```

**List recent sessions:**
```bash
bash ~/.claude/memory/session-id-generator.sh list
```

**Get session stats:**
```bash
python ~/.claude/memory/session-id-generator.py stats --session-id SESSION-20260216-173003-09RZ
```

### **Tracking Benefits:**

1. **📊 Session Logs** - Track all activity by session ID
2. **🔍 Debugging** - Find exact session when issues occur
3. **📈 Analytics** - Analyze session duration, work items
4. **🤝 Collaboration** - Share session ID for support
5. **📝 Reporting** - Generate reports by session

### **Session Data Stored:**

**Location:** `~/.claude/memory/sessions/SESSION-*.json`

**Contains:**
- Session ID and timestamps
- Work items and their status
- Session metadata
- Duration and completion stats

**Log:** `~/.claude/memory/logs/sessions.log`

### **Enforcement:**

**I MUST:**
- ✅ Generate session ID on session start
- ✅ Display session ID banner to user
- ✅ Provide session ID for tracking
- ✅ Log all session events
- ❌ NEVER skip showing session ID

---

## 📋 PLAN DETECTION (AUTO)

**Automatically detects your active Claude Code subscription plan!**

**Detected Plans:**
- 🆓 **Free Plan** - Basic features, limited usage (100K context)
- ⭐ **Pro Plan** - Full features, extended context (200K), background tasks
- 👥 **Team Plan** - Pro + team collaboration, shared workspaces
- 🏢 **Enterprise Plan** - All features, SLA, custom deployment

**Auto-runs on session start** to show your current plan and limits.

**Manual check:**
```bash
# Full display
bash ~/.claude/memory/scripts/plan-detector.sh

# Summary only
bash ~/.claude/memory/scripts/plan-detector.sh --summary

# JSON output
bash ~/.claude/memory/scripts/plan-detector.sh --json
```

**📖 Full docs:** `~/.claude/memory/docs/plan-detection.md`

---

## 🗺️ SYSTEM STRUCTURE

| Resource | Path |
|----------|------|
| Master Docs | `~/.claude/memory/MASTER-README.md` |
| Detailed Docs | `~/.claude/memory/docs/` |
| Logs | `~/.claude/memory/logs/` |
| Sessions | `~/.claude/memory/sessions/` |
| Templates | `~/.claude/memory/templates/` |
| Plan Detection | `~/.claude/memory/scripts/plan-detector.py` |
| **Claude Insight** | `C:\Users\techd\Documents\workspace-spring-tool-suite-4-4.27.0-new\claude-insight\` |
| **Claude Global Library** | `C:\Users\techd\Documents\workspace-spring-tool-suite-4-4.27.0-new\claude-global-library\` |

**Public GitHub Repositories:**
- **Claude Insight:** https://github.com/piyushmakhija28/claude-insight (Monitoring Dashboard)
- **Claude Global Library:** https://github.com/piyushmakhija28/claude-global-library (Skills/Agents)

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
- ✅ `SYNC: This is global/reusable` → Exit code 0 → **SAFE TO SYNC**
- ❌ `NO SYNC: This is project-specific` → Exit code 1 → **DO NOT SYNC**
- ⚠️ `WARNING: Contains project references` → Exit code 2 → **CLEANUP FIRST**

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
   - Exit code 0 → Proceed with sync
   - Exit code 1 → DO NOT SYNC (project-specific)
   - Exit code 2 → Cleanup first, then sync

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
> **Core Memory System → Claude Insight** (monitoring dashboard)
> **Skills/Agents/Patterns → Claude Global Library** (separate project)
> **Project-Specific → Private** (never sync)

**I MUST:**
- ✅ Run detection first
- ✅ Sync ONLY core files to Claude Insight
- ✅ **NEVER sync skills/agents to Claude Insight**
- ✅ Skills/agents go to claude-global-library (manually)
- ✅ Protect proprietary content
- ✅ Keep Claude Insight focused on monitoring ONLY

---

## 🚀 CONTEXT OPTIMIZATION (ACTIVE)

**MANDATORY: Apply on EVERY tool call**

### Quick Rules:
- **Read Tool:** Files >500 lines → Use offset + limit
- **Grep Tool:** ALWAYS use head_limit (default: 100)
- **Cache:** Files accessed 3+ times → Use context-cache.py
- **Session State:** Context >85% → Use external session state

### Context Thresholds:

| % | Status | Action |
|---|--------|--------|
| <70% | 🟢 GREEN | Continue normally |
| 70-84% | 🟡 YELLOW | Use cache, offset/limit, head_limit |
| 85-89% | 🟠 ORANGE | Use session state, extract summaries |
| 90%+ | 🔴 RED | Save session, compact context |

---

## 🛡️ FAILURE PREVENTION (ACTIVE)

### Auto-Fixes Applied:

**Bash Tool:**
- `del` → `rm`, `copy` → `cp`, `dir` → `ls`, `xcopy` → `cp -r`, `type` → `cat`

**GitHub Operations:**
- Use `gh` CLI for: repos, PRs, issues, releases, workflows, API calls
- Use `git` for: add, commit, push, pull, checkout, branch, merge, rebase

**Tool Optimizations:**
- Edit Tool: Line number prefixes stripped automatically
- Read Tool: Files >500 lines → Auto-add offset/limit
- Grep Tool: Missing head_limit → Auto-add (default: 100)

---

## 🤖 POLICY AUTOMATION (ACTIVE)

### Model Selection Rules:
- **Haiku**: Search, read, status (35-45%)
- **Sonnet**: Implementation, editing, fixes (50-60%)
- **Opus**: Architecture, planning, complex analysis (3-8%)

### Core Skills Enforcement (MANDATORY ORDER):
1. Context validation & optimization (REQUIRED)
2. Model selection (REQUIRED)
3. Skill/agent detection (optional)
4. Task planning (optional for simple tasks)

---

## 📁 POLICY FILES

**All in `~/.claude/memory/`:**

**🔵 SYNC SYSTEM (Foundation):**
- **session-memory-policy.md** (📦 Session Management with IDs)
- **context-management-core** (skill) (📖 Context Understanding)

**🟢 RULES/STANDARDS SYSTEM (Middle Layer):**
- **coding-standards-enforcement-policy.md** (🔧 Load BEFORE Execution)

**🔴 EXECUTION SYSTEM (Implementation):**
- **prompt-generation-policy.md** (🔴 STEP 0 - MANDATORY FIRST)
- **anti-hallucination-enforcement.md** (🛡️ Integrated with Step 0)
- **automatic-task-breakdown-policy.md** (🎯 STEP 1 - AUTO TASK/PHASE)
- **auto-plan-mode-suggestion-policy.md** (🎯 STEP 2 - AUTO PLAN MODE)
- **intelligent-model-selection-policy.md** (🤖 STEP 4 - SMART MODEL CHOICE)
- **auto-skill-agent-selection-policy.md** (🤖 STEP 5 - AUTO SKILL/AGENT)
- **tool-usage-optimization-policy.md** (⚡ STEP 6 - TOKEN OPTIMIZED TOOLS)
- **parallel-execution-policy.md** (🚀 STEP 8 - PARALLEL EXECUTION)
- core-skills-mandate.md
- task-progress-tracking-policy.md (🤖 AUTO-TRACKING)
- common-failures-prevention.md
- github-cli-enforcement.md
- git-auto-commit-policy.md
- user-preferences-policy.md

**📖 See MASTER-README.md for complete policy list**

---

## 📂 WORKSPACE & GIT STRUCTURE

```
workspace-spring-tool-suite-4-4.27.0-new\
└── surgricalswale\                   (Project Folder)
    ├── frontend\                     ✅ HAS .git
    └── backend\                      ❌ NO .git
        ├── auth-service\             ✅ HAS .git
        ├── user-service\             ✅ HAS .git
        └── product-service\          ✅ HAS .git
```

**Git Rules:**
- ✅ `.git` in: `frontend/`, `backend/service-name/`
- ❌ NO `.git` in: workspace root, project root, backend folder
- **Before ANY git command:** `test -d .git || echo "No git repo"`

---

## 🏢 CENTRAL SERVICES

**Location:** `C:\Users\techd\Documents\workspace-spring-tool-suite-4-4.27.0-new\techdeveloper\backend\`

**Ports:**
- Gateway: 8085
- Eureka: 8761
- Config Server: 8888
- Secret Manager: 1002
- Project Management: 8109

---

## ⚙️ SPRING CLOUD CONFIG SERVER

**📖 Full docs:** `~/.claude/memory/docs/spring-cloud-config.md`

**Config Location:** `techdeveloper/backend/techdeveloper-config-server/configurations`

**Structure:**
```
configurations/
├── application.yml                    # Global (ALL services)
├── {project}/common/*.yml             # Project common
└── {project}/services/{service}.yml   # Service-specific
```

**Microservice application.yml (ONLY THIS!):**
```yaml
spring:
  application:
    name: service-name
  config:
    import: "configserver:http://localhost:8888"
  cloud:
    config:
      fail-fast: true
      retry:
        enabled: true

secret-manager:
  client:
    enabled: true
    project-name: "project-name"
```

**❌ NEVER add to microservice application.yml:**
Redis, Feign, Database, Email configs, Port numbers → All in config server!

---

## 🔐 SECRET MANAGEMENT

**📖 Full docs:** `~/.claude/memory/docs/secret-management.md`

**Services:** Secret Manager (1002), Project Management (8109)

**Microservice config:**
```yaml
secret-manager:
  client:
    enabled: true
    project-name: "surgricalswale"
    base-url: "http://localhost:8085/api/v1/secrets"
```

**🚨 NEVER hardcode secrets!**

---

## 🏗️ JAVA PROJECT STRUCTURE

**📖 Full docs:** `~/.claude/memory/docs/java-project-structure.md`

**Base Package:** `com.techdeveloper.${projectname}`

**Package Structure:**
| Package | Purpose |
|---------|---------|
| `controller` | REST endpoints |
| `dto` | Response objects |
| `form` | Request objects |
| `constants` | All constants/enums |
| `services` | Interfaces only |
| `services.impl` | Package-private implementations |
| `services.helper` | Helper classes |
| `entity` | Database entities |
| `repository` | Data access |

**Mandatory Rules:**
1. ALL responses use `ApiResponseDto<T>`
2. Form classes extend `ValidationMessageConstants`
3. Service impl extends Helper
4. NO hardcoded messages (use constants)
5. `@Transactional` for all write operations

---

## 🔍 JPA AUDITING PATTERN

**📖 Full docs:** `~/.claude/memory/docs/jpa-auditing-pattern.md`

**Automatic audit tracking for all entities across microservices.**

**Key Components:**
1. **AuditableEntity** - Base class with `createdAt`, `updatedAt`, `createdBy`, `updatedBy`
2. **AuditorAwareImpl** - Extracts current user from UserContextHolder
3. **@EnableJpaAuditing** - Enable on main application class

**Quick Setup:**
```java
// 1. Entity extends AuditableEntity
@Entity
public class Product extends AuditableEntity {
    @Id
    private Long id;
    // Audit fields inherited automatically
}

// 2. Enable in Application class
@SpringBootApplication
@EnableJpaAuditing(auditorAwareRef = "auditorAwareImpl")
public class ServiceApplication { }
```

**Integration:**
- Works with UserContext from centralized auth
- Auto-populated on INSERT/UPDATE
- Falls back to "SYSTEM" if no user context

**Implemented in:**
- ✅ All 12 Surgricalswale services
- ✅ TechDeveloper common-utility

---

## 🔐 CENTRALIZED AUTHENTICATION & SECURITY

**📖 Full docs:** `~/.claude/memory/docs/centralized-auth-security-pattern.md`

**Gateway-based authentication with JWT, CSRF, CORS, and role-based authorization.**

**Architecture:**
- **Gateway** - Central authentication point (port 8085)
- **Admin Login** - Multi-tenant admin management (project-based)
- **Customer Login** - Project-specific customer authentication
- **JWT Tokens** - Access + Refresh tokens with rotation
- **Security Context** - Propagated to all microservices

**Key Features:**
1. **Role-Based Authorization**
   - Public paths (GET requests for catalog data)
   - Admin-only paths (POST/PUT/DELETE for catalog management)
   - User-authenticated paths (customer operations)

2. **CSRF Protection**
   - Cookie-based token repository
   - Frontend integration with X-CSRF-TOKEN header

3. **CORS Configuration**
   - Multi-domain support (techdeveloper.in, surgricalswale.in)
   - Credentials enabled for authenticated requests

4. **Method-Specific Path Matching**
   - GET /api/v1/products → Public
   - POST /api/v1/products → Admin only

**Config Server Setup:**
```yaml
security:
  public-paths:
    - GET /api/v1/products/**
  admin-paths:
    - POST /api/v1/products/**
    - PUT /api/v1/products/**
    - DELETE /api/v1/products/**
  cors:
    allowed-origins:
      - https://techdeveloper.in
      - https://surgricalswale.in
```

**Implemented in:**
- ✅ TechDeveloper Gateway
- ✅ Surgricalswale Gateway
- ✅ All microservices (via UserContextFilter)

---

## 🐳 DEVOPS PATTERNS (DOCKER/JENKINS/K8S)

**📖 Full docs:** `~/.claude/memory/docs/devops-patterns.md`

**Standardized DevOps patterns across all projects.**

**Docker Patterns:**
1. **Spring Boot** - Single-stage build with OpenJDK 17
2. **Angular** - Multi-stage build (Node.js build + Nginx runtime)
3. **Nginx Config** - SPA routing with history API fallback

**Jenkins Patterns:**
1. **Simple Backend** - Build + Push to registry
2. **Backend with Dependencies** - Wait for Config Server/Eureka
3. **Angular Frontend** - Multi-stage build with nginx

**Kubernetes Patterns:**
1. **Deployments** - Resource limits, health probes, security context
2. **Services** - ClusterIP for internal, NodePort for external
3. **Ingress** - Path-based routing with TLS
4. **Network Policies** - Namespace isolation, DNS egress

**Common Patterns:**
- Private Docker Registry: `148.113.197.135:5000`
- Non-root containers (user 1000:1000)
- Resource limits (500m CPU, 512Mi memory)
- Health probes (liveness + readiness)
- Config Server dependency management

**Templates Location:** `~/.claude/memory/templates/`

---

## 🎯 TOKEN OPTIMIZATION (ACTIVE)

### Response Compression Mode:

**Use ultra-brief responses for routine operations:**

✅ **File Operations:**
- Created: `✅ {filepath}`
- Edited: `✅ {filepath}:{line} → {change}`
- Deleted: `❌ {filepath}`

✅ **Tests/Commands:**
- Passed: `✅ {test_name}`
- Failed: `❌ {test_name}: {error}`
- Running: `⏳ {command}...`

✅ **Status:**
- 🟢 Running, 🔴 Error, 🟡 Warning, ⏸️ Stopped

❌ **AVOID:** "I'll now read...", "The file has been successfully..."
✅ **USE:** "Reading...", "✅ Updated", "Checking..."

### Diff-Based Editing:

**After Edit tool, show ONLY changed lines (3 lines context):**
```
... (lines 1-42 unchanged)
43: const oldValue = 8080;
44: const newValue = 3000;  ← Changed
45: export { newValue };
... (lines 46-500 unchanged)

✅ {filepath}:44 → Port changed
```

### Smart Tool Selection:

| Need | ✅ Light Tool | Savings |
|------|---------------|---------|
| 🌳 **Understand structure** | `tree -L 2 backend/service/` | **90%** |
| 🌳 **Find file locations** | `tree -L 3` then direct Read | **87%** |
| File list | `tree -L 2` or `ls -1` | 90% |
| Find class | `tree -P "*.java"` or Glob | 90% |
| Get imports | `Read offset=0 limit=20` | 95% |
| Function signature | `Grep "def funcName" -A 2` | 97% |
| Check file exists | `ls {file}` | 98% |

### Advanced Optimizations:

**📖 See MASTER-README.md for:**
- Smart Grep Optimization
- Tiered Caching Strategy
- Session State Aggressive Mode
- Incremental Updates
- File Type Optimization
- Lazy Context Loading
- Smart File Summarization
- Batch File Operations
- MCP Response Filtering
- Conversation Pruning
- AST-Based Code Navigation

**EXPECTED TOTAL SAVINGS: 60-80%** 🚀

---

## ⚡ ACTIVE POLICY ENFORCEMENT

**I MUST follow these on EVERY request:**

| Policy | Enforcement |
|--------|-------------|
| **🚨 Auto-Fix Enforcement** | **MANDATORY FIRST: bash auto-fix-enforcer.sh (BLOCKING)** |
| Context Check | Run context-monitor-v2.py BEFORE responding |
| Model Selection | Run model-selection-enforcer.py BEFORE task |
| **Task/Phase Breakdown** | **🚨 BLOCKING: task-phase-enforcer.py --analyze (STEP 3)** |
| Task Tracking | TaskCreate/Update MANDATORY when enforcer requires it |
| GitHub CLI | ALWAYS use `gh` for GitHub ops (repos, PRs, issues) |
| Git Operations | Use `git` for local ops (commit, push, pull, branch) |
| Auto-Commit | Run auto-commit-enforcer.py AFTER TaskUpdate(completed) |
| Failure Prevention | Run pre-execution-checker.py BEFORE tools |
| Context Optimization | Apply offset/limit/head_limit on tools |
| Session Memory | Auto-load at start, auto-save at milestones |

---

## 🎯 EXECUTION FLOW (MANDATORY)

**🤖 TRUE AUTOMATION MODE (OPTION B - RECOMMENDED):**

```bash
# ONE-TIME SETUP: Install automatic hooks
bash ~/.claude/memory/install-auto-hooks.sh

# That's it! Hooks now run automatically before EVERY request
# No manual intervention needed!
```

**Hooks installed:**
- ✅ `pre-request` hook → Runs `auto-enforce-all-policies.sh` automatically
- ✅ `user-prompt-submit` hook → Runs before processing user prompt
- 🔒 **Blocking mode** → Must pass to proceed

**What happens automatically:**
1. New request detected
2. Auto-enforce-all-policies.sh runs
3. All 3 layers enforced automatically
4. Response only if all policies pass

---

**📋 MANUAL BACKUP MODE (OPTION A - FALLBACK):**

If hooks don't work or disabled, use manual mode:

```bash
# STEP -2: START NEW REQUEST (Run this BEFORE every response!)
python ~/.claude/memory/per-request-enforcer.py --new-request

# OR use the all-in-one automatic script:
bash ~/.claude/memory/auto-enforce-all-policies.sh
```

---

**On EVERY user request (Manual Mode):**

```
🚨 AUTO-FIX ENFORCEMENT (STEP -1 - BEFORE EVERYTHING) 🚨
   → export PYTHONIOENCODING=utf-8
   → bash auto-fix-enforcer.sh

   🔍 CHECK ALL SYSTEMS (6 CHECKS):
   → Python availability (CRITICAL)
   → Critical files present (CRITICAL)
   → Blocking enforcer initialized (CRITICAL)
   → Session state valid (HIGH)
   → Daemon status (INFO)
   → Git repository clean (INFO)

   🔧 AUTO-FIX FAILURES:
   → Blocking enforcer state → Auto-fix
   → Session markers → Auto-fix
   → Other failures → Manual fix required

   🚨 IF ANY CRITICAL FAILURE:
   → STOP ALL WORK IMMEDIATELY
   → Report failure + fix instructions
   → Wait for user to fix
   → Re-run enforcer
   → Only proceed when ALL OK

   ✅ EXIT CODE 0 → Continue to Step 0
   ❌ EXIT CODE != 0 → BLOCKED, fix first

   📄 Output: All systems operational

        ↓

🔵 SYNC SYSTEM (FOUNDATION - ALWAYS FIRST)
   → Context Management + Session Management
   → Load project README, service .md files
   → Load previous session (if exists)
   → Understand: Current state + History
   → Output: Complete context loaded

   ✅ MARK COMPLETE:
   python ~/.claude/memory/per-request-enforcer.py --mark-complete context_checked

        ↓

🟢 RULES/STANDARDS SYSTEM (MIDDLE LAYER - LOAD BEFORE EXECUTION)
   → python standards-loader.py --load-all

   📋 LOAD ALL CODING STANDARDS:
   → Java project structure (packages, visibility)
   → Config Server rules (what goes where)
   → Secret Management (never hardcode)
   → Response format (ApiResponseDto<T>)
   → Service layer pattern (Helper, package-private)
   → Entity pattern (audit fields, naming)
   → Controller pattern (REST, validation)
   → Constants organization (no magic strings)
   → Common utilities (reusable code)
   → Error handling (global handler)
   → API design standards (REST patterns)
   → Database standards (naming, indexes)

   ✅ ALL STANDARDS LOADED
   → Ready to enforce during code generation
   → Every piece of code will follow these rules
   → 100% consistency guaranteed

   📄 Output: Standards loaded and available

        ↓

🔴 EXECUTION SYSTEM (IMPLEMENTATION - FOLLOWS LOADED RULES)

0. 🔴 Prompt Generation (MANDATORY - FIRST STEP) 🔴
   → prompt-generator.py "{USER_MESSAGE}"

   🧠 PHASE 1: THINKING
   → Understand user intent
   → Break into sub-questions
   → Identify information needed
   → Plan where to find it

   🔍 PHASE 2: INFORMATION GATHERING
   → Search for similar code (BEFORE answering)
   → Read existing implementations
   → Check documentation
   → Verify project structure

   ✅ PHASE 3: VERIFICATION
   → Verify all examples exist
   → Validate patterns from actual code
   → Flag uncertainties/assumptions
   → Answer based on FOUND info ONLY

   📄 Output: Structured prompt with verified examples

   ✅ MARK COMPLETE:
   python ~/.claude/memory/per-request-enforcer.py --mark-complete prompt_verified

1. 🎯 Automatic Task Breakdown (MANDATORY - SECOND STEP) 🎯
   → task-auto-breakdown.py "{STRUCTURED_PROMPT}"

   📊 ANALYZE COMPLEXITY
   → Calculate complexity score
   → Determine if phases needed
   → Estimate number of tasks

   📋 DIVIDE INTO PHASES (if complex)
   → Foundation → Business Logic → API Layer → Config
   → Each phase has specific purpose
   → Phases execute sequentially

   ✅ BREAK INTO TASKS
   → Each file = 1 task
   → Each endpoint = 1 task
   → Each config = 1 task
   → Automatically create all tasks

   🔗 CREATE DEPENDENCIES
   → Entity before Repository
   → Repository before Service
   → Service before Controller
   → Auto-detect dependency chain

   🤖 START AUTO-TRACKER
   → Monitor tool calls
   → Auto-update task status
   → Track progress automatically
   → No manual updates needed

   📄 Output: All tasks created, auto-tracking enabled

   ✅ MARK COMPLETE:
   python ~/.claude/memory/per-request-enforcer.py --mark-complete task_analyzed

2. 🎯 Auto Plan Mode Suggestion (MANDATORY - THIRD STEP) 🎯
   → auto-plan-mode-suggester.py "{COMPLEXITY}" "{PROMPT}"

   📊 ANALYZE RISKS
   → Multi-service impact?
   → Database changes?
   → Security critical?
   → No similar examples?
   → Adjust complexity score

   🎯 MAKE DECISION
   → Score 0-4: NO plan mode needed ✅
   → Score 5-9: OPTIONAL - Ask user ⚠️
   → Score 10-19: RECOMMENDED - Strong suggest ✅
   → Score 20+: MANDATORY - Auto-enter 🔴

   📋 AUTO-SUGGEST
   → SIMPLE: Proceed directly
   → MODERATE: Ask user preference
   → COMPLEX: Show benefits, recommend plan mode
   → VERY_COMPLEX: Auto-enter plan mode (no skip)

   🔀 EXECUTE DECISION
   → If auto-enter → EnterPlanMode (blocking)
   → If ask user → Wait for choice
   → If no plan mode → Continue to execution

   📄 Output: Plan mode decision + optional plan

3. Context Check (REQUIRED)
   → context-monitor-v2.py --current-status
   → If >70%: Apply optimizations

4. 🤖 Intelligent Model Selection (MANDATORY - ENHANCED) 🤖
   → intelligent-model-selector.py "{COMPLEXITY}" "{TASK_TYPE}" "{PLAN_MODE}"

   📊 ANALYZE CONTEXT
   → Complexity score (from Step 1)
   → Task type (from Step 0)
   → Plan mode decision (from Step 2)
   → Risk factors

   🎯 DECISION RULES
   → Plan mode? → OPUS (mandatory)
   → Score 0-4 (SIMPLE)? → HAIKU
   → Score 5-9 (MODERATE)? → HAIKU or SONNET (task-based)
   → Score 10-19 (COMPLEX)? → SONNET
   → Score 20+ (VERY_COMPLEX)? → SONNET (or OPUS if planning)

   🔒 RISK OVERRIDES
   → Security-critical? → Upgrade to SONNET minimum
   → Multi-service? → Upgrade to SONNET minimum
   → Architecture? → OPUS
   → Novel problem? → Upgrade one level

   💰 COST OPTIMIZATION
   → Show estimated tokens
   → Show estimated cost
   → Alternative models if applicable

   🔄 DYNAMIC UPGRADE
   → Enable upgrade conditions
   → Build failures >= 3 → Upgrade
   → Security issues → Upgrade
   → Architectural needs → Upgrade to OPUS

   📄 Output: Selected model with reasoning

   ✅ MARK COMPLETE:
   python ~/.claude/memory/per-request-enforcer.py --mark-complete model_determined

5. 🎯 Auto Skill & Agent Selection (MANDATORY - SMART SELECTION) 🎯
   → auto-skill-agent-selector.py "{TASK_TYPE}" "{COMPLEXITY}" "{PROMPT}"

   📊 ANALYZE ALL CONTEXT:
   → Task type (from Step 0)
   → Complexity score (from Step 1)
   → Technologies (from Step 0)
   → Model selected (from Step 4)

   🔍 MATCH FROM REGISTRY:
   → Check available skills (adaptive-skill-registry.md)
   → Check available agents (adaptive-skill-registry.md)
   → NO CREATE unless absolutely needed

   📚 SKILLS (For Knowledge):
   → java-spring-boot-microservices (Spring Boot)
   → docker, kubernetes (Containerization)
   → rdbms-core, nosql-core (Databases)
   → jenkins-pipeline (CI/CD)

   🤖 AGENTS (For Autonomous Execution):
   → spring-boot-microservices (Complex Java)
   → devops-engineer (Deployment/CI/CD)
   → qa-testing-agent (Testing)
   → orchestrator-agent (Multi-service)

   🎯 DECISION RULES:
   → Complexity < 10 + Tech → Skill
   → Complexity >= 10 + Tech → Agent
   → Multi-service → orchestrator-agent
   → Simple task → No skill/agent (direct)

   📄 Output: Selected skills/agents + execution plan

6. 🔧 Tool Usage Optimization (MANDATORY - BEFORE EVERY TOOL) 🔧
   → tool-usage-optimizer.py "{TOOL}" "{PARAMS}"

   📊 BEFORE EVERY TOOL CALL:
   → Analyze which tool is being called
   → Apply tool-specific optimizations
   → Validate parameters are optimized

   🔧 TOOL-SPECIFIC RULES:
   → 🌳 Bash/Tree: First time in directory? → Use tree -L 2/3
   → 🌳 Tree Pattern: Understand structure → Direct file access
   → Read: File >500 lines? → offset/limit
   → Read: Accessed 3+ times? → Use cache
   → Grep: ALWAYS add head_limit (100)
   → Grep: Default to files_with_matches
   → Glob: Restrict path if service known (or use tree!)
   → Bash: Combine sequential commands
   → Edit/Write: Brief confirmation only

   💰 TOKEN SAVINGS:
   → Read optimization: 70-95% savings
   → Grep optimization: 50-90% savings
   → Glob optimization: 40-60% savings
   → Edit/Write: 90-95% savings
   → Overall: 60-80% reduction

   ✅ ENFORCEMENT:
   → Mandatory before EVERY tool
   → Auto-applied optimizations
   → No manual intervention needed

   📖 REFERENCES (NO DUPLICATION):
   → ADVANCED-TOKEN-OPTIMIZATION.md (15 strategies)
   → TOKEN-OPTIMIZATION-COMPLETE.md (status)
   → Consolidates existing work

   ✅ MARK COMPLETE:
   python ~/.claude/memory/per-request-enforcer.py --mark-complete tools_optimized

7. Failure Prevention (BEFORE EVERY TOOL)
   → pre-execution-checker.py --tool {TOOL}
   → Apply auto-fixes

8. 🚀 Parallel Execution Analysis (MANDATORY - NEW!) 🚀
   → auto-parallel-detector.py --tasks-file "{TASKS_JSON}"

   📊 ANALYZE TASKS FOR PARALLELIZATION:
   → Check for independent tasks (no blockedBy deps)
   → Calculate estimated speedup
   → Determine if parallel execution worth it

   🎯 DECISION RULES:
   → 3+ independent tasks? → Use parallel execution
   → Estimated speedup >= 1.5x? → Use parallel execution
   → All tasks have dependencies? → Use sequential

   ⚡ IF PARALLEL EXECUTION:
   → Group tasks by dependency waves
   → Create/check temporary skills/agents if needed
   → Launch all tasks in parallel (Task tool with subagents)
   → Monitor progress across all parallel tasks
   → Collect results from all executions
   → Intelligently merge results
   → Cleanup temporary resources (keep useful, delete unused)

   📈 BENEFITS:
   → 3-10x faster execution
   → Auto-create temporary skills/agents as needed
   → Smart result merging
   → Automatic cleanup

   📄 Output: Parallel execution plan OR sequential continuation

9. Execute Tasks (AUTOMATIC TRACKING)
   → 🤖 Auto-tracker monitors every tool call
   → Read → Update progress +10%
   → Write → Update progress +40%, mark items complete
   → Edit → Update progress +30%, mark items complete
   → Build SUCCESS → Update progress +20%, complete verification
   → Test PASS → Update progress +15%, complete verification
   → 100% progress → Auto-complete task
   → Task complete → Unlock dependent tasks
   → Phase complete → Unlock next phase
   → **Parallel tasks tracked independently then merged**

10. Session Save (ON MILESTONES)
   → Auto-triggered by daemon

11. Git Auto-Commit (AUTOMATIC ON PHASE COMPLETION)
   → Phase complete → Auto-commit all repos
   → python auto-commit-enforcer.py --enforce-now
   → Uses gh for PR creation if needed

12. Logging (ALWAYS)
   → Log policy applications
   → Log task updates
   → Log progress tracking
   → Log tool optimizations

🚨 FINAL CHECK (BEFORE RESPONDING TO USER) 🚨
   → python ~/.claude/memory/per-request-enforcer.py --check-status

   📋 VERIFY ALL POLICIES ENFORCED:
   → context_checked ✅
   → prompt_verified ✅
   → task_analyzed ✅
   → model_determined ✅
   → tools_optimized ✅

   ✅ ALL COMPLETE → Respond to user
   ❌ ANY PENDING → Cannot respond yet
```

---

## 🐙 GITHUB CLI (gh) - MANDATORY

**📖 Full docs:** `~/.claude/memory/docs/github-cli-usage.md`

**CRITICAL: ALWAYS use `gh` CLI for GitHub operations!**

### Quick Reference:

| Operation | Command | Tool |
|-----------|---------|------|
| Clone repo | `gh repo clone owner/repo` | ✅ gh |
| Create repo | `gh repo create name --private` | ✅ gh |
| View PR | `gh pr view 123` | ✅ gh |
| Create PR | `gh pr create --title "..." --body "..."` | ✅ gh |
| Merge PR | `gh pr merge 123 --squash` | ✅ gh |
| View issue | `gh issue view 456` | ✅ gh |
| Create issue | `gh issue create --title "..." --body "..."` | ✅ gh |
| View releases | `gh release list` | ✅ gh |
| View workflows | `gh workflow list` | ✅ gh |
| Local commit | `git add . && git commit -m "..."` | ⚠️ git |
| Push code | `git push origin main` | ⚠️ git |

**Always verify authentication:** `gh auth status || gh auth login`

**📖 See github-cli-usage.md for templates, automation, multi-repo ops, error handling**

---

## 📦 GIT AUTO-COMMIT

**📖 Full docs:** `~/.claude/memory/docs/git-and-context.md`

**Repo Creation:**
```bash
# ✅ ALWAYS use gh
gh repo create project-name --private --description "..." --clone

# ❌ NEVER use just git init
```

**Branch Rules:**
- Always "main" (NEVER "master")
- Always private (unless explicitly public)
- Verify: `gh repo view --json isPrivate`

**Auto-Commit Triggers:**
- Task completed → Commit + Push (git)
- Phase completed → Commit + Push + PR (gh pr create)
- User says "done"/"finished" → Commit + Push + PR
- 10+ files modified → Commit + Push
- 30+ minutes elapsed → Commit + Push

---

## 🔧 TEMPLATES (AUTO-USE)

**📖 Location:** `~/.claude/memory/templates/`

**Auto-use for:**
- Dockerfile (Spring Boot / Angular)
- Jenkinsfile (CI/CD)
- Kubernetes deployment/service
- GitHub PR/Issue templates

**NEVER ask - just use templates directly!**

---

## 🔄 MIGRATION SKILL & AGENT

**📖 Full docs:** `~/.claude/skills/migration/skill.md`

**Use for:** Framework upgrades, database migrations, API version changes, major dependency upgrades

**Quick Usage:**
```bash
# Interactive
/migration

# Direct invocation
/migration --framework "Spring Boot" --from "2.7.18" --to "3.2.0"

# Use Task tool for complex migrations
Task(subagent_type="migration-expert", prompt="...")
```

**Every migration MUST have:**
- ✅ Full backup (verified)
- ✅ Rollback script (tested)
- ✅ Migration plan (documented)
- ✅ Staging test (passed)
- ✅ Auto-rollback on failure

---

## 📖 DETAILED DOCUMENTATION

**Location:** `~/.claude/memory/docs/`

**Available:**

**🏗️ Architecture & Policies:**
- `policy-architecture-flow.md` - Complete architecture (Auto vs Manual, Order, Flow)
- `java-agent-strategy.md` - Agent collaboration patterns

**☁️ Infrastructure & DevOps:**
- `spring-cloud-config.md` - Config Server patterns
- `secret-management.md` - Secret Manager integration
- `devops-patterns.md` - **Docker/Jenkins/K8s patterns** (NEW!)

**🔐 Security & Authentication:**
- `centralized-auth-security-pattern.md` - **Gateway auth, JWT, CSRF, CORS, role-based authorization** (NEW!)
- `security-best-practices.md` - Security standards

**☕ Java & Spring Boot:**
- `java-project-structure.md` - Package structure, coding standards
- `jpa-auditing-pattern.md` - **Automatic audit tracking for entities** (NEW!)
- `spring-boot-design-patterns-core.md` - Design patterns in Spring Boot

**🔧 Development Standards:**
- `api-design-standards.md` - REST API conventions
- `error-handling-standards.md` - Exception handling
- `logging-standards.md` - Logging patterns
- `database-standards.md` - Database design
- `documentation-standards.md` - **2-file .md policy (README.md + CLAUDE.md only)** (NEW!)

**🐙 Git & GitHub:**
- `git-and-context.md` - Git workflow rules
- `github-cli-usage.md` - GitHub CLI (`gh`) usage

---

## 📊 MONITORING & HEALTH

**Dashboard:** `bash ~/.claude/memory/dashboard.sh`
**Live logs:** `tail -f ~/.claude/memory/logs/policy-hits.log`
**Daemon status:** `python ~/.claude/memory/daemon-manager.py --status-all`

---

## 🚨 TROUBLESHOOTING

**If something breaks:**
1. Check daemons: `python ~/.claude/memory/daemon-manager.py --status-all`
2. View logs: `tail -f ~/.claude/memory/logs/policy-hits.log`
3. Restart: `bash ~/.claude/memory/startup-hook.sh`
4. Health check: `bash ~/.claude/memory/verify-system.sh`
5. Rollback: `python ~/.claude/memory/rollback.py`

---

**VERSION:** 3.0.0 (TRUE AUTOMATION - Auto-Hooks)
**LAST UPDATED:** 2026-02-17
**STATUS:** 🤖 FULLY AUTOMATED
**LOCATION:** `~/.claude/CLAUDE.md`

**CHANGELOG:**
- v3.0.0 (2026-02-17): 🤖 **TRUE AUTOMATION - Auto-Hooks:**
  - Created auto-enforce-all-policies.sh (all-in-one automatic script)
  - Created install-auto-hooks.sh (automatic hook installer)
  - Installed pre-request and user-prompt-submit hooks
  - Policies now run AUTOMATICALLY before every request (no manual steps!)
  - Added Option B (TRUE automation) + Option A (manual backup)
  - Blocking mode: Policies must pass before response
  - Complete 3-level architecture runs automatically
- v2.9.0 (2026-02-17): 🔄 **Per-Request Policy Enforcement:**
  - Created per-request-enforcer.py for continuous policy enforcement
  - Policies now run BEFORE EVERY user request (not just session start)
  - Added per-request state tracking (resets for each request)
  - Added policy completion markers throughout execution flow
  - Added final check before responding to user
  - Fixed: Policies were only enforced once at session start
  - Fixed: tree command replaced with find (Git Bash compatibility)
- v2.8.0 (2026-02-17): 📋 **Documentation Standards Policy:**
  - Added 2-file .md policy (README.md + CLAUDE.md only per project)
  - Created documentation-standards.md with comprehensive rules
  - Updated standards-loader.py to include documentation standards
  - Applied to surgricalswale/backend (consolidated 6 .md files → 1 README.md)
  - Applied to email-service (consolidated 3 extra .md files)
  - All projects now compliant with documentation standards
- v2.7.0 (2026-02-17): 🚀 **Major Project Reorganization:**
  - Created Claude Global Library (separate public repo for skills/agents)
  - Cleaned Claude Insight (now focused on monitoring dashboard only)
  - Updated sync rules: Skills/Agents → claude-global-library, Core → claude-insight
  - Added comprehensive FUTURE-SYNC-RULES.md with decision trees
  - Both projects pushed to GitHub
- v2.6.0 (2026-02-17): 📚 Added comprehensive documentation:
  - JPA Auditing Pattern (automatic audit tracking)
  - Centralized Auth & Security Pattern (Gateway, JWT, CSRF, CORS, roles)
  - DevOps Patterns (Docker/Jenkins/K8s standardization)
- v2.5.0 (2026-02-16): 🚨 Added Auto-Fix Enforcement System - Zero-Tolerance Failure Policy
- v2.4.0 (2026-02-16): Added Plan Detection System (Free/Pro/Team/Enterprise)
- v2.3.0 (2026-02-15): Added GitHub CLI (`gh`) mandatory enforcement
- v2.2.0 (2026-02-10): Active enforcement mode restored
- v2.1.0 (2026-02-09): Initial memory system release

# Memory System - ACTIVE ENFORCEMENT MODE

**VERSION:** 2.4.0 (Migration System Mode)
**STATUS:** 🟢 FULLY OPERATIONAL

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
5. ✅ Provides complete system health summary

**I MUST apply these recommendations BEFORE responding!**

**Alternative (If above fails):**
```bash
nohup python ~/.claude/memory/auto-recommendation-daemon.py start > /dev/null 2>&1 &
sleep 2
python ~/.claude/memory/session-start-check.py
```

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

## 🗺️ SYSTEM STRUCTURE

| Resource | Path |
|----------|------|
| Master Docs | `~/.claude/memory/MASTER-README.md` |
| Detailed Docs | `~/.claude/memory/docs/` |
| Logs | `~/.claude/memory/logs/` |
| Sessions | `~/.claude/memory/sessions/` |
| Templates | `~/.claude/memory/templates/` |

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

**On EVERY user request:**

```
🔵 SYNC SYSTEM (FOUNDATION - ALWAYS FIRST)
   → Context Management + Session Management
   → Load project README, service .md files
   → Load previous session (if exists)
   → Understand: Current state + History
   → Output: Complete context loaded

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

7. Failure Prevention (BEFORE EVERY TOOL)
   → pre-execution-checker.py --tool {TOOL}
   → Apply auto-fixes

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
- `policy-architecture-flow.md` - **🏗️ COMPLETE ARCHITECTURE** (Auto vs Manual, Order, Flow)
- `spring-cloud-config.md` - Config server
- `secret-management.md` - Secret manager
- `java-project-structure.md` - Java patterns
- `java-agent-strategy.md` - Agent collaboration
- `git-and-context.md` - Git rules
- `github-cli-usage.md` - GitHub CLI
- `api-design-standards.md` - REST conventions
- `error-handling-standards.md` - Exceptions
- `security-best-practices.md` - Security
- `logging-standards.md` - Logging
- `database-standards.md` - Database

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

**VERSION:** 2.4.0 (Migration System Mode)
**LAST UPDATED:** 2026-02-16
**STATUS:** 🟢 FULLY OPERATIONAL
**LOCATION:** `~/.claude/CLAUDE.md`

**CHANGELOG:**
- v2.4.0 (2026-02-15): Added Migration Skill & Migration Expert Agent
- v2.3.0 (2026-02-15): Added GitHub CLI (`gh`) mandatory enforcement
- v2.2.0 (2026-02-10): Active enforcement mode restored
- v2.1.0 (2026-02-09): Initial memory system release

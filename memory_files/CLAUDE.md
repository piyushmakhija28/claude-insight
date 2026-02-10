# Memory System - ACTIVE ENFORCEMENT MODE

**VERSION:** 2.2.0 (FIXED - Active Enforcement Restored)
**STATUS:** 🟢 FULLY OPERATIONAL

---

## 🚨 CRITICAL: MANDATORY EXECUTION ON EVERY REQUEST

**BEFORE responding to ANY user request, I MUST execute these in order:**

### Step 1: Context Check (REQUIRED)
```python
# Check if context is safe
result = context-monitor-v2.py --current-status
if result['percentage'] > 70:
    # Apply optimizations: use offset/limit, head_limit, cache
if result['percentage'] > 85:
    # Use session-state.py for external memory
```

### Step 2: Model Selection (REQUIRED)
```python
# Determine correct model for task
result = model-selection-enforcer.py --analyze "{USER_MESSAGE}"
# Use: result['recommended_model'] (haiku/sonnet/opus)
```

### Step 3: Failure Prevention (BEFORE EVERY TOOL CALL)
```python
# Check for known failure patterns
result = pre-execution-checker.py --tool {TOOL} --params '{JSON}'
# If auto_fix_applied: Use fixed version
```

### Step 4: Token Optimization (BEFORE EVERY TOOL CALL)
```python
# Auto-wrapper handles:
# - Cache check
# - File type optimization
# - AST vs summarize vs full read
# - Parameter optimization
result = auto-tool-wrapper.py --tool {TOOL} --params '{JSON}'

# If optimized=true: Use optimized strategy
# Strategies: cache_hot, ast, summary, optimized_read
```

### Step 5: Post-Tool Processing (AFTER EVERY TOOL CALL)
```python
# Auto-processor handles:
# - Update cache
# - Extract essentials
# - Log token usage
result = auto-post-processor.py --tool {TOOL} --result '{JSON}' --filepath "{PATH}"
```

---

## 🗺️ SYSTEM STRUCTURE

| Resource | Path |
|----------|------|
| Structure Map | `~/.claude/memory/workflows/SYSTEM-STRUCTURE-MAP.md` |
| Automation Gaps | `~/.claude/memory/workflows/AUTOMATION-GAPS-ANALYSIS.md` |
| Logs | `~/.claude/memory/logs/` |
| Sessions | `~/.claude/memory/sessions/` |
| Docs | `~/.claude/memory/docs/` |

---

## 🧠 SESSION START (AUTO-EXECUTED)

**These run automatically via startup-hook.sh:**

1. ✅ Context daemon (monitors every 10 min)
2. ✅ Session auto-save daemon (monitors every 15 min)
3. ✅ Preference tracker daemon (monitors every 20 min)
4. ✅ Skill suggester daemon (monitors every 5 min)
5. ✅ Git auto-commit daemon (monitors every 15 min)
6. ✅ Session pruning daemon (monitors daily)
7. ✅ Pattern detection daemon (monitors weekly)
8. ✅ Failure prevention daemon (monitors every 6 hours)

**Manual session tasks:**
```bash
# Load project context (if exists)
PROJECT_NAME=$(basename "$PWD")
CONTEXT_FILE=~/.claude/memory/sessions/$PROJECT_NAME/project-summary.md

# Check incomplete work
python ~/.claude/memory/check-incomplete-work.py $PROJECT_NAME
```

---

## 🚀 CONTEXT OPTIMIZATION (ACTIVE)

**MANDATORY: Apply on EVERY tool call**

### Read Tool:
- Files >500 lines: ALWAYS use offset + limit
- Example: `offset=0, limit=500`

### Grep Tool:
- ALWAYS use head_limit (default: 100)
- Example: `head_limit=100`

### Cache Strategy:
- Files accessed 3+ times: Use context-cache.py
- Check cache: `python ~/.claude/memory/context-cache.py --get-file "{PATH}"`
- Set cache: `python ~/.claude/memory/context-cache.py --set-file "{PATH}" --summary '{JSON}'`

### Session State (External Memory):
When context >85%, use session state instead of full history:
```python
# Get current state
python ~/.claude/memory/session-state.py --summary

# Update state
python ~/.claude/memory/session-state.py --set-task "description"
python ~/.claude/memory/session-state.py --add-file "path/file.py"
python ~/.claude/memory/session-state.py --add-decision "type" "desc" "choice"
python ~/.claude/memory/session-state.py --complete-task "result"
```

---

## 🛡️ FAILURE PREVENTION (ACTIVE)

**MANDATORY: Check before EVERY tool execution**

### Auto-Fixes Applied:

**Bash Tool:**
- `del` → `rm`
- `copy` → `cp`
- `dir` → `ls`
- `xcopy` → `cp -r`
- `type` → `cat`

**Edit Tool:**
- Line number prefixes stripped automatically
- "42\t    code" becomes "    code"

**Read Tool:**
- Files >500 lines: Auto-add offset/limit

**Grep Tool:**
- Missing head_limit: Auto-add (default: 100)

### Learning System:
```python
# When you fix a failure manually, log it:
python ~/.claude/memory/failure-solution-learner.py --learn-from-fix \
    "{TOOL}" "{FAILURE_MSG}" "{FIX_APPLIED}"
```

---

## 🤖 POLICY AUTOMATION (ACTIVE)

### Model Selection Rules:
- **Haiku**: Search, read, status (35-45% of requests)
- **Sonnet**: Implementation, editing, fixes (50-60% of requests)
- **Opus**: Architecture, planning, complex analysis (3-8% of requests)

### Consultation Tracking:
```python
# Before asking user repeated questions:
result = consultation-tracker.py --check "{DECISION_TYPE}"
if result['should_ask'] == false:
    # Use result['default'], don't ask again
```

**Decision Types:**
- planning_mode, testing_approach, api_style, error_handling, commit_frequency

### Core Skills Enforcement:
**Order (MANDATORY):**
1. Context validation & optimization (REQUIRED)
2. Model selection (REQUIRED)
3. Skill/agent detection (optional)
4. Task planning (optional for simple tasks)

---

## 📁 POLICY FILES (All in ~/.claude/memory/)

| Policy | File | Status |
|--------|------|--------|
| Core Skills | `core-skills-mandate.md` | ✅ Active |
| Model Selection | `model-selection-enforcement.md` | ✅ Active |
| Consultation | `proactive-consultation-policy.md` | ✅ Active |
| Session Memory | `session-memory-policy.md` | ✅ Active |
| Failure Prevention | `common-failures-prevention.md` | ✅ Active |
| File Management | `file-management-policy.md` | ✅ Active |
| Git Auto-Commit | `git-auto-commit-policy.md` | ✅ Active |
| User Preferences | `user-preferences-policy.md` | ✅ Active |
| Session Pruning | `session-pruning-policy.md` | ✅ Active |
| Context Integration | `CONTEXT-SESSION-INTEGRATION.md` | ✅ Active |

---

## 📂 WORKSPACE & GIT STRUCTURE

```
workspace-spring-tool-suite-4-4.27.0-new\
└── m2-surgricals\                    (Project Folder)
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

**Services:**
- Gateway: 8085
- Eureka: 8761
- Config Server: 8888
- Secret Manager: 1002
- Project Management: 8109

---

## ⚙️ SPRING CLOUD CONFIG SERVER

**📖 Full docs:** `~/.claude/memory/docs/spring-cloud-config.md`

**Config Location:**
```bash
cd techdeveloper/backend/techdeveloper-config-server/configurations
```

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
- Redis config (in config server)
- Feign config (in config server)
- Database config (in config server)
- Email config (in config server)
- Port numbers (in config server)

---

## 🔐 SECRET MANAGEMENT

**📖 Full docs:** `~/.claude/memory/docs/secret-management.md`

**Services:**
- Secret Manager: port 1002
- Project Management: port 8109

**How it works:**
- Secrets fetched at startup
- Injected as `${SECRET_KEY}`
- **🚨 NEVER hardcode secrets!**

**Microservice config:**
```yaml
secret-manager:
  client:
    enabled: true
    project-name: "m2-surgricals"
    base-url: "http://localhost:8085/api/v1/secrets"
```

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

## 🤖 JAVA AGENT STRATEGY

**📖 Full docs:** `~/.claude/memory/docs/java-agent-strategy.md`

**Approach:** Agent provides logic → I adapt to OUR structure

**Quality Checklist:**
- ✅ `ApiResponseDto<T>` used?
- ✅ DTO vs Form separate?
- ✅ Messages in constants?
- ✅ Service impl package-private?
- ✅ Service impl extends helper?

---

## 🎯 TOKEN OPTIMIZATION RULES

**Mandatory for efficient operation:**

### Basic Optimizations:
1. **Large files:** Use offset/limit, edit without full read
2. **Scripts:** Read header only (`head -50`)
3. **Batch ops:** Combine multiple commands
4. **Cache:** Files accessed 3+ times

### **RESPONSE COMPRESSION MODE** (ACTIVE):

**For ALL routine operations, use ultra-brief responses:**

✅ **File Operations:**
- Created: `✅ {filepath}`
- Edited: `✅ {filepath}:{lines} → {change}`
- Deleted: `❌ {filepath}`

✅ **Tests/Commands:**
- Passed: `✅ {test_name}`
- Failed: `❌ {test_name}: {error}`
- Running: `⏳ {command}...`

✅ **Status Checks:**
- Running: `🟢 {service}: {status}`
- Error: `🔴 {service}: {error}`
- Warning: `🟡 {service}: {warning}`

❌ **AVOID (Token Waste):**
- "I'll now read the configuration file to check..."
- "The file has been successfully updated with..."
- "Let me examine the contents of..."

✅ **USE INSTEAD:**
- "Reading config..."
- "✅ Updated"
- "Checking..."

**Exception:** Provide details ONLY when:
- User explicitly asks for explanation
- Error occurred and needs context
- Critical decision requires discussion

### **DIFF-BASED EDITING** (ACTIVE):

**After using Edit tool, show ONLY changed lines:**

❌ **AVOID (Showing full file):**
```
Showing all 500 lines after edit = 2000 tokens wasted
```

✅ **USE (Show diff only):**
```
... (lines 1-42 unchanged)
43: const oldValue = 8080;
44: const newValue = 3000;  ← Changed
45: export { newValue };
... (lines 46-500 unchanged)

✅ {filepath}:44 → Port changed
```

**Format:**
- Show 3 lines context before/after change
- Mark changed line with `←`
- Brief summary: `✅ {file}:{line} → {what_changed}`
- Total: ~20 lines instead of 500 (95% savings!)

**Exception:** Show full file ONLY when:
- User explicitly requests it
- First time creating file
- Major refactoring (>50% changed)

### **SMART TOOL SELECTION** (MANDATORY):

**Always choose the LIGHTEST tool that works:**

| Need | ❌ Heavy Tool | ✅ Light Tool | Savings |
|------|---------------|---------------|---------|
| File list | `ls -R` (500 tokens) | `tree` (50 tokens) | 90% |
| Find class | `Grep "class Name"` (200 tokens) | `Glob "**/*Name*.java"` (20 tokens) | 90% |
| Get imports | `Read full file` (2000 tokens) | `Read offset=0 limit=20` (100 tokens) | 95% |
| Function signature | `Read full file` (2000 tokens) | `Grep "def funcName" -A 2` (50 tokens) | 97% |
| Directory structure | `find . -type f` (1000 tokens) | `tree -L 2` (100 tokens) | 90% |
| Check file exists | `Read file` (500 tokens) | `ls {file}` (10 tokens) | 98% |

**Decision Matrix:**

```
NEED FILE LIST?
  → tree -L 2 (NOT ls -R)
  → Cost: 50 tokens vs 500 tokens

NEED TO FIND CLASS?
  → Glob "**/*ClassName*.java" (NOT Grep)
  → Cost: 20 tokens vs 200 tokens

NEED IMPORTS ONLY?
  → Read offset=0 limit=20 (NOT full file)
  → Cost: 100 tokens vs 2000 tokens

NEED FUNCTION BODY?
  → Grep "function name" -A 10 (get just function)
  → Read full file ONLY if complex

NEED FILE METADATA?
  → ls -lh {file} (NOT Read)
  → Cost: 10 tokens vs 500 tokens
```

**Principle:** Start small, expand only if needed

### **RESPONSE TEMPLATES** (MANDATORY):

**Use these ultra-brief templates for common operations:**

```markdown
# File Operations:
✅ {filepath}                          # Created
✅ {filepath}:{line} → {change}        # Edited
❌ {filepath}                          # Deleted
📁 {dirpath} ({count} files)          # Directory created

# Test Results:
✅ {test_name}                         # Passed
❌ {test_name}: {error}                # Failed
⏭️ {test_name}                          # Skipped
📊 {passed}/{total} tests passed       # Summary

# Command Execution:
⏳ {command}...                        # Running
✅ {command} (exit 0)                  # Success
❌ {command} (exit {code}): {error}    # Failed

# Service Status:
🟢 {service}: Running (port {port})   # Healthy
🔴 {service}: Error - {error}          # Down
🟡 {service}: Warning - {warning}      # Degraded
⏸️ {service}: Stopped                  # Stopped

# Git Operations:
✅ Committed: {message}                # Commit success
📤 Pushed to {branch}                  # Push success
🔀 Merged {source} → {target}          # Merge success
⚠️ Conflicts in {files}                # Merge conflict

# Searches:
Found {count} matches in {files}      # Search results
No matches for "{pattern}"            # No results
```

**10-20% token savings on routine operations**

### **SMART GREP OPTIMIZATION** (MANDATORY):

**Start narrow, expand only if needed:**

```python
# Step 1: Conservative search (low head_limit)
Grep pattern="function" head_limit=10

# Step 2: If too broad, refine pattern
if results > 50:
    Grep pattern="function.*User" head_limit=20

# Step 3: Use file type filters
Grep pattern="function" type="ts" head_limit=30

# Step 4: Use glob for specific dirs
Grep pattern="function" glob="src/services/**" head_limit=20
```

**Progressive Refinement Strategy:**

```
Try 1: head_limit=10  (estimate scope)
  → If not enough: head_limit=20
  → If still not enough: refine pattern

Try 2: Add context (package/class name)
  → "AuthService.login" instead of just "login"

Try 3: Filter by file type
  → type="java" or glob="**/*.ts"

Try 4: Specific directory
  → glob="src/auth/**" instead of whole project
```

**Benefits:**
- Start: 10 results (40 tokens)
- vs Always: 100 results (400 tokens)
- **Savings: 90% on most searches**

**NEVER use head_limit >100 without specific reason**

### **TIERED CACHING STRATEGY** (ACTIVE):

**Cache files based on access frequency:**

```
TIER 1: HOT (5+ accesses in last hour)
- Keep full content in cache
- No re-reads needed
- Examples: application.yml, constants, main configs

TIER 2: WARM (3-4 accesses)
- Keep summary in cache (first 50 lines)
- Re-read only on explicit request
- Examples: Service implementations, controllers

TIER 3: COLD (1-2 accesses)
- No caching
- Read fresh each time
- Examples: One-time file reads
```

**Usage:**
```python
# Before reading file:
python ~/.claude/memory/tiered-cache.py --get-file "{filepath}"

# If cache_hit=true: Use cached content
# If cache_hit=false: Read from disk, then cache

# After reading:
python ~/.claude/memory/tiered-cache.py --set-file "{filepath}" --content "{content}"
```

**Benefits:**
- HOT files: 100% savings (no re-reads)
- WARM files: 80% savings (summary only)
- COLD files: 0% savings (fresh reads)
- **Overall: 30-40% savings on repeated operations**

### **SESSION STATE AGGRESSIVE MODE** (MANDATORY):

**Use session state for ALL historical references:**

❌ **AVOID (Repeating inline):**
```
You: "What did we do yesterday?"
Me: "Yesterday we implemented authentication with JWT tokens,
     created UserService with login/register methods,
     added validation for email and password,
     configured Redis for session storage,
     created AuthController with 3 endpoints..." (200 tokens)
```

✅ **USE (Reference session file):**
```
You: "What did we do yesterday?"
Me: "See session-2026-02-09.md, tasks #1-5"
     or
Me: "Auth implementation (5 tasks). Details: session-2026-02-09.md"
     (20 tokens = 90% savings!)
```

**When to use session state:**

```python
# ALWAYS reference instead of repeating:
- Historical summaries (previous sessions)
- Completed tasks list
- Decisions made in past
- Files modified earlier

# ONLY inline when:
- Current active task (happening now)
- User explicitly asks for details
- Critical context for current decision
```

**Format:**
```markdown
# Historical reference:
"See {session-file}, tasks #{range}"

# Summary + reference:
"{Brief 1-line summary}. Details: {session-file}"

# Multiple sessions:
"Sessions 2026-02-08 to 02-09 (12 tasks). Files: sessions/project/"
```

**Benefits: 60-80% savings on historical queries**

### **INCREMENTAL UPDATES** (ACTIVE):

**For iterative work, show ONLY deltas:**

❌ **AVOID (Repeating full state):**
```
Round 1: Full implementation (500 lines)
Round 2: Added error handling → Show full 510 lines again
Round 3: Fixed typo → Show full 510 lines again
Total: 1520 lines shown
```

✅ **USE (Show only changes):**
```
Round 1: Full implementation (500 lines)
Round 2: +Error handling (10 new lines only)
Round 3: Line 245 typo fix (1 line only)
Total: 511 lines shown (66% savings!)
```

**Format:**
```markdown
# Round 1 (initial):
Show full implementation

# Round 2+ (incremental):
✅ Added: Lines 501-510 (error handling)
✅ Modified: Line 245 (typo fix)
✅ Deleted: Lines 100-102 (dead code)

# Only show full file if:
- User requests it
- >50% of file changed
```

**Benefits: 60-70% savings on iterative development**

### **FILE TYPE OPTIMIZATION** (MANDATORY):

**Optimize based on file type:**

| File Type | Strategy | Tool | Savings |
|-----------|----------|------|---------|
| JSON/YAML | Extract specific keys | `jq/yq` | 80% |
| Logs | Recent + grep errors | `tail + grep` | 90% |
| Markdown | Read by section | `grep ^##` | 70% |
| Code | AST or grep structure | `grep class/function` | 80% |
| Config | Usually small, read full | `Read` | N/A |
| Binary | Metadata only, NEVER content | `file` | 99% |

**Usage:**
```python
# Get optimization strategy:
python ~/.claude/memory/file-type-optimizer.py --file "{path}" --purpose "{purpose}"

# Example outputs:
# JSON: "Use jq .services.auth config.json"
# Log: "tail -100 app.log | grep ERROR"
# Code: "grep ^class UserService.java"
```

**Benefits: 60-80% per file type**

### **LAZY CONTEXT LOADING** (ACTIVE):

**Load minimal context on session start:**

❌ **AVOID (Eager loading):**
```
Session starts → Auto-load:
- Project summary (500 tokens)
- All policies (1000 tokens)
- Recent history (800 tokens)
- Cross-project patterns (300 tokens)
Total: 2600 tokens preloaded
```

✅ **USE (Lazy loading):**
```
Session starts → Load ONLY:
- Active task (if exists) (100 tokens)
- Load others ON-DEMAND when needed

User asks for history → THEN load session files
User needs policy → THEN reference policy file
```

**Principle:**
- Don't preload what MIGHT be needed
- Load only what IS needed
- Reference files instead of loading

**Benefits: 80-90% savings on session start**

### **SMART FILE SUMMARIZATION** (ACTIVE):

**For files >500 lines, use intelligent summarization:**

**Strategy 1: Sandwich Read**
```
Read first 50 lines (imports, structure)
Skip middle (implementation details)
Read last 50 lines (recent changes)
Total: 100 lines vs 1000 lines (90% savings!)
```

**Strategy 2: AST-Based (for code)**
```
Extract: package, classes, interfaces, methods
Skip: method bodies (read only when needed)
Example:
  Package: com.techdeveloper.auth
  Classes: [AuthController, AuthService, AuthHelper]
  Methods: [login(), register(), validateToken()]
Total: ~50 tokens vs 2000 tokens (97% savings!)
```

**Usage:**
```python
python ~/.claude/memory/smart-file-summarizer.py --file "{path}" --strategy auto
```

**Benefits: 70-95% on large files**

### **BATCH FILE OPERATIONS** (MANDATORY):

**Combine multiple reads into single operation:**

❌ **AVOID (Multiple individual reads):**
```
Read: src/auth/controller.ts (500 tokens)
Read: src/auth/service.ts (500 tokens)
Read: src/auth/dto.ts (300 tokens)
Total: 1300 tokens + 3 tool calls
```

✅ **USE (Batch strategy):**
```
Step 1: Get structure
  tree src/auth --level 2 (50 tokens)

Step 2: Strategic read
  Glob: src/auth/*.ts → [list files]
  Read only NEEDED files based on task

Total: 200 tokens + 2 tool calls (85% savings!)
```

**Principle:**
- Understand structure FIRST (tree/glob)
- Read only NEEDED files
- Use file type optimization per file

**Benefits: 40-50% on exploration tasks**

### **MCP RESPONSE FILTERING** (ACTIVE):

**Extract only essential fields from MCP responses:**

❌ **AVOID (Processing all data):**
```
MCP returns 500-line JSON response
Process all 500 lines (2000 tokens)
```

✅ **USE (Extract essentials immediately):**
```python
result = mcp.call()
essential = {
    'status': result.status,
    'data': result.data[0:5],  # First 5 items only
    'error': result.error,
    'total': len(result.data)  # Count, not all items
}
# Discard remaining 400 lines

Total: ~100 tokens (95% savings!)
```

**Principle:**
- Extract status, error, first N items
- Count remaining items, don't load all
- Load more only if user requests

**Benefits: 70-80% on MCP operations**

### **CONVERSATION PRUNING** (ACTIVE):

**Auto-prune completed tasks when context >70%:**

```python
# After task completion:
1. Save summary to session state
2. Mark conversation turns as "completed"
3. When context >70%: Prune completed turns
4. Keep only current active task

Example:
Before pruning: 50 turns (80% context)
After pruning: 15 turns (40% context)
Savings: 40% context freed!
```

**What to prune:**
- Completed tasks (saved in session state)
- Old file reads (cached or outdated)
- Historical discussions (saved in sessions)

**What to keep:**
- Current active task
- Recent decisions (last 5 turns)
- Error context (if unresolved)

**Benefits: 30-40% on long sessions**

### **AST-BASED CODE NAVIGATION** (ACTIVE):

**For code files, use AST instead of full read:**

❌ **AVOID (Reading full file):**
```
Read UserService.java (500 lines = 2000 tokens)
Just to find: What methods exist?
```

✅ **USE (AST extraction):**
```python
python ~/.claude/memory/ast-code-navigator.py --file UserService.java

Output:
{
  "package": "com.techdeveloper.auth",
  "classes": ["UserService"],
  "methods": [
    "login(String, String): boolean",
    "register(UserForm): User",
    "validateToken(String): boolean"
  ]
}
Total: ~100 tokens (95% savings!)
```

**Then read specific method only when needed:**
```
Grep "public User register" -A 20 UserService.java
(Read just the method, not whole file)
```

**Supported Languages:**
- Java: package, classes, methods
- TypeScript: imports, classes, interfaces, functions
- Python: imports, classes, functions

**Benefits: 80-95% on code exploration**

---

## 📊 **TOTAL OPTIMIZATION IMPACT**

**All 15 optimizations active:**
- Response Compression: 20-30%
- Diff Editing: 90%
- Smart Tools: 50-70%
- Templates: 10-20%
- Smart Grep: 50-60%
- Tiered Cache: 30-40%
- Session State: 60-80%
- Incremental: 60-70%
- File Types: 60-80%
- Lazy Loading: 80-90%
- Summarization: 70-95%
- Batch Ops: 40-50%
- MCP Filter: 70-80%
- Conversation Prune: 30-40%
- AST Navigation: 80-95%

**EXPECTED TOTAL SAVINGS: 60-80%** 🚀

**200K token budget feels like 500K+!**

---

## ⚡ ACTIVE POLICY ENFORCEMENT

**I MUST follow these on EVERY request:**

| Policy | Enforcement |
|--------|-------------|
| Context Check | Run context-monitor-v2.py BEFORE responding |
| Model Selection | Run model-selection-enforcer.py BEFORE task |
| Failure Prevention | Run pre-execution-checker.py BEFORE tools |
| Context Optimization | Apply offset/limit/head_limit on tools |
| User Preferences | Check consultation-tracker.py before asking |
| Session Memory | Auto-load at start, auto-save at milestones |
| Git Auto-Commit | Trigger on completion events |

---

## 📝 AUTO-LOGGING (ACTIVE)

**Every policy application is logged:**
```bash
echo "[$(date '+%Y-%m-%d %H:%M:%S')] <policy> | <action> | <context>" \
  >> ~/.claude/memory/logs/policy-hits.log
```

---

## 📊 MONITORING & HEALTH

**Dashboard:**
```bash
bash ~/.claude/memory/dashboard.sh
```

**Live logs:**
```bash
tail -f ~/.claude/memory/logs/policy-hits.log
```

**Stats:**
```bash
cat ~/.claude/memory/logs/policy-counters.txt
```

**Daemon status:**
```bash
python ~/.claude/memory/daemon-manager.py --status-all
```

---

## 🎯 EXECUTION FLOW (MANDATORY)

**On EVERY user request:**

```
1. Context Check (REQUIRED)
   → context-monitor-v2.py --current-status
   → If >70%: Apply optimizations

2. Model Selection (REQUIRED)
   → model-selection-enforcer.py --analyze "{MSG}"
   → Use recommended model

3. Skill Detection (OPTIONAL)
   → core-skills-enforcer.py --next-skill
   → Execute if mandatory

4. Failure Prevention (BEFORE EVERY TOOL)
   → pre-execution-checker.py --tool {TOOL}
   → Apply auto-fixes

5. Execute Task
   → Use optimized tool parameters
   → Apply offset/limit/head_limit

6. Session Save (ON MILESTONES)
   → Auto-triggered by daemon

7. Git Auto-Commit (ON COMPLETION)
   → Auto-triggered by daemon

8. Logging (ALWAYS)
   → Log policy applications
```

---

## 📦 GIT AUTO-COMMIT

**📖 Full docs:** `~/.claude/memory/docs/git-and-context.md`

**Repo Creation Rules:**
- Always "main" branch (NEVER "master")
- Always private (unless explicitly public)

**Auto-Commit Triggers:**
- Task completed
- Phase completed
- User says "done"/"finished"
- 10+ files modified
- 30+ minutes elapsed

---

## 📊 CONTEXT THRESHOLDS

**Auto-triggered actions:**

| % | Status | Action |
|---|--------|--------|
| <70% | 🟢 GREEN | Continue normally |
| 70-84% | 🟡 YELLOW | Use cache, offset/limit, head_limit |
| 85-89% | 🟠 ORANGE | Use session state, extract summaries |
| 90%+ | 🔴 RED | Save session, compact context |

**🛡️ Session memory is ALWAYS protected!**

---

## 💾 SESSION SAVE TRIGGERS

**Auto-save when:**
- Major milestone reached
- 5+ files modified
- User says "done"/"finished"
- Before context cleanup

**What is saved:**
- Tasks completed
- Key decisions made
- Files modified
- Pending work
- Important context

---

## 🔧 TEMPLATES (AUTO-USE)

**📖 Location:** `~/.claude/memory/templates/`

**Auto-use for:**
- Dockerfile (Spring Boot / Angular)
- Jenkinsfile (CI/CD)
- Kubernetes deployment/service

**NEVER ask - just use templates directly!**

---

## 📖 DETAILED DOCUMENTATION

**Location:** `~/.claude/memory/docs/`

**Available docs:**
- `spring-cloud-config.md` - Config server setup
- `secret-management.md` - Secret manager details
- `java-project-structure.md` - Full Java patterns
- `java-agent-strategy.md` - Agent collaboration
- `git-and-context.md` - Git rules, context monitoring
- `api-design-standards.md` - REST API conventions
- `error-handling-standards.md` - Exception patterns
- `security-best-practices.md` - Security guidelines
- `logging-standards.md` - Logging best practices
- `database-standards.md` - Database patterns

---

## 🔍 SYSTEM HEALTH CHECK

**Verify system status:**
```bash
# Quick verification
bash ~/.claude/memory/verify-system.sh

# Full health check
bash ~/.claude/memory/weekly-health-check.sh

# Test all phases
python ~/.claude/memory/test-all-phases.py
```

---

## 🚨 TROUBLESHOOTING

**If something breaks:**
1. Check daemon status: `python ~/.claude/memory/daemon-manager.py --status-all`
2. View logs: `tail -f ~/.claude/memory/logs/policy-hits.log`
3. Restart daemons: `bash ~/.claude/memory/startup-hook.sh`
4. Check health: `bash ~/.claude/memory/verify-system.sh`

**Rollback if needed:**
```bash
python ~/.claude/memory/rollback.py
```

---

**VERSION:** 2.2.0 (Active Enforcement Mode)
**LAST UPDATED:** 2026-02-10
**STATUS:** 🟢 FULLY OPERATIONAL
**LOCATION:** `~/.claude/CLAUDE.md`

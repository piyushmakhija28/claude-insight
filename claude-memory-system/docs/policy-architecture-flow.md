# 🏗️ Policy Architecture & Execution Flow

**VERSION:** 1.0.0
**CREATED:** 2026-02-16
**PURPOSE:** Complete architecture showing what happens when, what's automatic vs manual, and execution order

---

## 📊 SYSTEM ARCHITECTURE OVERVIEW

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         USER SENDS MESSAGE                               │
└────────────────────────────┬────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    🤖 CLAUDE CODE RECEIVES MESSAGE                       │
└────────────────────────────┬────────────────────────────────────────────┘
                             │
                             ▼
        ╔════════════════════════════════════════════╗
        ║  STEP 0: PROMPT GENERATION (NEW!)         ║
        ║  ------------------------------------      ║
        ║  🔴 MANDATORY: FIRST STEP ALWAYS           ║
        ║  Script: prompt-generator.py               ║
        ║                                            ║
        ║  Converts natural language → structured:   ║
        ║  - Analyzes task type & complexity         ║
        ║  - Extracts entities & operations          ║
        ║  - Finds similar examples from codebase    ║
        ║  - Defines conditions (pre/post)           ║
        ║  - Structures input/output                 ║
        ║  - Validates architecture alignment        ║
        ║                                            ║
        ║  Output: Structured prompt with:           ║
        ║  - Clear requirements                      ║
        ║  - Examples from existing code             ║
        ║  - Success criteria                        ║
        ║  - Pre/post conditions                     ║
        ╚════════════════════════════════════════════╝
                             │
                             ▼
        ┌────────────────────────────────────────────┐
        │  SESSION START CHECK (First message only)  │
        │  ----------------------------------------  │
        │  🔴 MANUAL: User must send first message   │
        │  🟢 AUTO: session-start.sh runs            │
        │  - Starts 9 daemons (if not running)       │
        │  - Shows recommendations                    │
        │  - Shows context status                     │
        └────────────────────┬───────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    MANDATORY EXECUTION PIPELINE                          │
│                    (Runs on EVERY message)                               │
└─────────────────────────────────────────────────────────────────────────┘
                             │
                             ▼
        ╔════════════════════════════════════════════╗
        ║  STEP 1: CONTEXT CHECK                     ║
        ║  ------------------------------------      ║
        ║  🟢 AUTO: context-daemon monitors 24/7     ║
        ║  🟢 AUTO: Claude checks before responding  ║
        ║  Script: context-monitor-v2.py             ║
        ║                                            ║
        ║  Outputs:                                  ║
        ║  - Current context usage %                 ║
        ║  - Status: GREEN/YELLOW/ORANGE/RED         ║
        ║  - Optimization recommendations            ║
        ║                                            ║
        ║  Actions Applied:                          ║
        ║  <70%: ✅ Continue normally                ║
        ║  70-84%: ⚠️ Use cache, offset/limit       ║
        ║  85-89%: 🔶 Use session state              ║
        ║  90%+: 🔴 Save & compact                   ║
        ╚════════════════════════════════════════════╝
                             │
                             ▼
        ╔════════════════════════════════════════════╗
        ║  STEP 2: MODEL SELECTION                   ║
        ║  ------------------------------------      ║
        ║  🟢 AUTO: Analyzes user message            ║
        ║  Script: model-selection-enforcer.py       ║
        ║                                            ║
        ║  Decision Tree:                            ║
        ║  - Search/Read/Status → Haiku (35-45%)     ║
        ║  - Implementation/Edit → Sonnet (50-60%)   ║
        ║  - Architecture/Plan → Opus (3-8%)         ║
        ║                                            ║
        ║  Output:                                   ║
        ║  - Recommended model                       ║
        ║  - Reasoning                               ║
        ║  - Token estimate                          ║
        ╚════════════════════════════════════════════╝
                             │
                             ▼
        ╔════════════════════════════════════════════╗
        ║  STEP 3: TASK/PHASE ENFORCEMENT            ║
        ║  ------------------------------------      ║
        ║  🟢 AUTO: Analyzes task complexity         ║
        ║  🔴 BLOCKING: Must comply before work      ║
        ║  Script: task-phase-enforcer.py            ║
        ║                                            ║
        ║  Analysis:                                 ║
        ║  - Complexity Score (1-10)                 ║
        ║  - Size Score (1-10)                       ║
        ║  - File Impact Count                       ║
        ║                                            ║
        ║  Requirements:                             ║
        ║  Complexity >= 3 → TaskCreate REQUIRED     ║
        ║  Size >= 6 → Phases REQUIRED               ║
        ║                                            ║
        ║  🚨 BLOCKS execution if not complied!      ║
        ╚════════════════════════════════════════════╝
                             │
                             ▼
        ╔════════════════════════════════════════════╗
        ║  STEP 4: SKILL DETECTION (Optional)        ║
        ║  ------------------------------------      ║
        ║  🟢 AUTO: Detects if skill needed          ║
        ║  🟡 OPTIONAL: Not required for all tasks   ║
        ║  Script: core-skills-enforcer.py           ║
        ║  Daemon: skill-auto-suggester              ║
        ║                                            ║
        ║  Detection Rules:                          ║
        ║  - Docker keywords → /docker               ║
        ║  - Jenkins keywords → /jenkins-pipeline    ║
        ║  - K8s keywords → /kubernetes              ║
        ║  - Migration keywords → /migration         ║
        ║  - Spring Boot → /java-spring-boot-micro   ║
        ║                                            ║
        ║  Output:                                   ║
        ║  - Recommended skill (if any)              ║
        ║  - Auto-invoke if mandatory                ║
        ╚════════════════════════════════════════════╝
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         TASK CREATION PHASE                              │
│                    (If Step 3 requires it)                               │
└─────────────────────────────────────────────────────────────────────────┘
                             │
                             ▼
        ╔════════════════════════════════════════════╗
        ║  TaskCreate                                ║
        ║  ------------------------------------      ║
        ║  🔴 MANUAL: Claude creates tasks           ║
        ║  🟢 AUTO: task-progress-tracker logs it    ║
        ║                                            ║
        ║  Required Fields:                          ║
        ║  - subject: Brief title                    ║
        ║  - description: Detailed requirements      ║
        ║  - activeForm: "Working on..."             ║
        ║                                            ║
        ║  Optional:                                 ║
        ║  - metadata: Custom tracking data          ║
        ║  - phases: If Size >= 6                    ║
        ╚════════════════════════════════════════════╝
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         EXECUTION PHASE                                  │
└─────────────────────────────────────────────────────────────────────────┘
                             │
                             ▼
        ╔════════════════════════════════════════════╗
        ║  BEFORE EVERY TOOL CALL                    ║
        ║  ------------------------------------      ║
        ║  🟢 AUTO: Failure prevention check         ║
        ║  Script: pre-execution-checker.py          ║
        ║  Daemon: failure-prevention-daemon         ║
        ║                                            ║
        ║  Auto-Fixes:                               ║
        ║  - Windows commands → Bash equivalents     ║
        ║  - Git operations → Verify .git exists     ║
        ║  - GitHub ops → Ensure using 'gh' CLI      ║
        ║  - Tool params → Add optimizations         ║
        ║                                            ║
        ║  Examples:                                 ║
        ║  del → rm                                  ║
        ║  copy → cp                                 ║
        ║  dir → ls                                  ║
        ║  Read >500 lines → Add offset/limit        ║
        ║  Grep → Add head_limit                     ║
        ╚════════════════════════════════════════════╝
                             │
                             ▼
        ╔════════════════════════════════════════════╗
        ║  TaskUpdate(status="in_progress")          ║
        ║  ------------------------------------      ║
        ║  🔴 MANUAL: Claude updates when starting   ║
        ║  🟢 AUTO: Logged by daemon                 ║
        ║                                            ║
        ║  Marks task as actively being worked on    ║
        ╚════════════════════════════════════════════╝
                             │
                             ▼
        ╔════════════════════════════════════════════╗
        ║  TOOL EXECUTION (Read/Edit/Write/Bash)     ║
        ║  ------------------------------------      ║
        ║  🔴 MANUAL: Claude calls tools             ║
        ║  🟢 AUTO: Context optimizations applied    ║
        ║  🟢 AUTO: Failure prevention applied       ║
        ║                                            ║
        ║  Context Optimizations:                    ║
        ║  - Read: offset + limit for large files    ║
        ║  - Grep: head_limit (default 100)          ║
        ║  - Cache: Files accessed 3+ times          ║
        ║                                            ║
        ║  GitHub Operations:                        ║
        ║  - ALWAYS use 'gh' CLI                     ║
        ║  - Repos, PRs, Issues, Releases            ║
        ║  - Auto-verify: gh auth status             ║
        ║                                            ║
        ║  Git Operations:                           ║
        ║  - ALWAYS verify .git exists first         ║
        ║  - Use 'git' for local ops                 ║
        ║  - Commits, push, pull, branch, merge      ║
        ╚════════════════════════════════════════════╝
                             │
                             ▼
        ╔════════════════════════════════════════════╗
        ║  TaskUpdate(metadata={...})                ║
        ║  ------------------------------------      ║
        ║  🔴 MANUAL: Every 2-3 tool calls           ║
        ║  🟢 AUTO: Logged by daemon                 ║
        ║                                            ║
        ║  Granular Progress Tracking:               ║
        ║  - current_step: What's happening now      ║
        ║  - progress: % complete                    ║
        ║  - completed_items: What's done            ║
        ║  - next_items: What's next                 ║
        ║  - blockers: Any issues                    ║
        ║                                            ║
        ║  Example:                                  ║
        ║  {                                         ║
        ║    current_step: "Creating controller",    ║
        ║    progress: 45,                           ║
        ║    completed_items: ["Form", "DTO"],       ║
        ║    next_items: ["Service", "Repository"]   ║
        ║  }                                         ║
        ╚════════════════════════════════════════════╝
                             │
                             ▼
        ╔════════════════════════════════════════════╗
        ║  REPEAT TOOL EXECUTION                     ║
        ║  (Until task complete)                     ║
        ╚════════════════════════════════════════════╝
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         COMPLETION PHASE                                 │
└─────────────────────────────────────────────────────────────────────────┘
                             │
                             ▼
        ╔════════════════════════════════════════════╗
        ║  TaskUpdate(status="completed")            ║
        ║  ------------------------------------      ║
        ║  🔴 MANUAL: Claude marks complete          ║
        ║  🟢 AUTO: Triggers auto-commit             ║
        ║                                            ║
        ║  Final metadata update with:               ║
        ║  - progress: 100                           ║
        ║  - completed_items: All items              ║
        ║  - completion_time: Timestamp              ║
        ╚════════════════════════════════════════════╝
                             │
                             ▼
        ╔════════════════════════════════════════════╗
        ║  GIT AUTO-COMMIT                           ║
        ║  ------------------------------------      ║
        ║  🟢 AUTO: Triggered by task completion     ║
        ║  Script: auto-commit-enforcer.py           ║
        ║  Daemon: commit-daemon                     ║
        ║                                            ║
        ║  Process:                                  ║
        ║  1. Detect all repos with changes          ║
        ║  2. For each repo:                         ║
        ║     a. Verify .git exists                  ║
        ║     b. git add .                           ║
        ║     c. git commit -m "..."                 ║
        ║     d. git push origin main                ║
        ║  3. If phase complete:                     ║
        ║     a. gh pr create (if applicable)        ║
        ║                                            ║
        ║  Commit Message Format:                    ║
        ║  - Based on task subject                   ║
        ║  - Includes Co-Authored-By: Claude         ║
        ╚════════════════════════════════════════════╝
                             │
                             ▼
        ╔════════════════════════════════════════════╗
        ║  SESSION SAVE                              ║
        ║  ------------------------------------      ║
        ║  🟢 AUTO: Triggered on milestones          ║
        ║  Daemon: session-auto-save-daemon          ║
        ║                                            ║
        ║  Triggers:                                 ║
        ║  - Task completed                          ║
        ║  - Phase completed                         ║
        ║  - 10+ files modified                      ║
        ║  - 30+ minutes elapsed                     ║
        ║  - Context >85%                            ║
        ║                                            ║
        ║  Saves:                                    ║
        ║  - Conversation history                    ║
        ║  - Task states                             ║
        ║  - User preferences                        ║
        ║  - Context summaries                       ║
        ╚════════════════════════════════════════════╝
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         CONTINUOUS MONITORING                            │
│                    (Running 24/7 in background)                          │
└─────────────────────────────────────────────────────────────────────────┘

        ╔════════════════════════════════════════════╗
        ║  9 BACKGROUND DAEMONS                      ║
        ║  ------------------------------------      ║
        ║  🟢 AUTO: All run continuously             ║
        ║  Started: Windows login / session-start.sh ║
        ║                                            ║
        ║  1. context-daemon                         ║
        ║     - Monitors context every 5 sec         ║
        ║     - Alerts on >70%, >85%, >90%           ║
        ║                                            ║
        ║  2. session-auto-save-daemon               ║
        ║     - Auto-saves on triggers               ║
        ║     - Every 30 min or on events            ║
        ║                                            ║
        ║  3. preference-auto-tracker                ║
        ║     - Learns user patterns                 ║
        ║     - Updates preferences.json             ║
        ║                                            ║
        ║  4. skill-auto-suggester                   ║
        ║     - Detects skill opportunities          ║
        ║     - Suggests skills to use               ║
        ║                                            ║
        ║  5. commit-daemon                          ║
        ║     - Monitors file changes                ║
        ║     - Triggers auto-commit                 ║
        ║                                            ║
        ║  6. session-pruning-daemon                 ║
        ║     - Cleans old sessions                  ║
        ║     - Archives completed tasks             ║
        ║                                            ║
        ║  7. pattern-detection-daemon               ║
        ║     - Detects coding patterns              ║
        ║     - Learns user style                    ║
        ║                                            ║
        ║  8. failure-prevention-daemon              ║
        ║     - Monitors for common mistakes         ║
        ║     - Updates prevention rules             ║
        ║                                            ║
        ║  9. auto-recommendation-daemon             ║
        ║     - Generates recommendations            ║
        ║     - Model, skill, agent suggestions      ║
        ║     - Every 5 seconds                      ║
        ╚════════════════════════════════════════════╝

---

## 🎯 EXECUTION ORDER SUMMARY

### **Every Message:**
```
0. 🔴 Prompt Generation (MANDATORY - FIRST STEP)
   🧠 Think → 🔍 Gather Info → ✅ Verify

1. 🎯 Automatic Task Breakdown (MANDATORY - SECOND STEP)
   📊 Analyze → 📋 Divide Phases → ✅ Create Tasks → 🔗 Dependencies

2. 🎯 Auto Plan Mode Suggestion (MANDATORY - THIRD STEP)
   📊 Assess Risks → 🎯 Make Decision → 📋 Suggest/Enforce

   Decision Matrix:
   - Score 0-4: NO plan mode → Direct execution
   - Score 5-9: OPTIONAL → Ask user
   - Score 10-19: RECOMMENDED → Suggest strongly
   - Score 20+: MANDATORY → Auto-enter plan mode

3. 🤖 Auto-Tracker Starts (AUTOMATIC)
   Monitors all tool calls, updates status automatically

4. ✅ Model Selection (AUTO)
5. ✅ Context Check (AUTO)
6. ✅ Pre-execution Check (AUTO before each tool)
7. ⚠️ Tool Execution (MANUAL - Claude works)
8. 🤖 Status Auto-Update (AUTO - tracker updates)
9. 🤖 Task Auto-Complete (AUTO - when progress = 100%)
10. 🤖 Phase Complete (AUTO - all tasks done)
11. ✅ Auto-Commit (AUTO - on phase completion)
12. ✅ Session Save (AUTO on triggers)
```

### **First Message Only:**
```
0. ✅ session-start.sh (AUTO - recommended)
   - Starts daemons
   - Shows recommendations
   - Shows status
```

---

## 🟢 AUTOMATIC vs 🔴 MANUAL

### **🟢 AUTOMATIC (No Action Needed):**
1. ✅ Context monitoring (daemon)
2. ✅ Model selection analysis
3. ✅ Task/phase requirement check
4. ✅ Skill detection
5. ✅ Pre-execution checks
6. ✅ Context optimizations
7. ✅ Failure prevention
8. ✅ Auto-commit (on task complete)
9. ✅ Session save (on triggers)
10. ✅ All 9 daemons monitoring
11. ✅ Preference learning
12. ✅ Pattern detection

### **🔴 MANUAL (Claude Must Do):**
1. ⚠️ TaskCreate (when enforcer requires)
2. ⚠️ TaskUpdate(in_progress) (when starting)
3. ⚠️ TaskUpdate(metadata) (every 2-3 tools)
4. ⚠️ TaskUpdate(completed) (when done)
5. ⚠️ Tool calls (Read/Edit/Write/Bash)
6. ⚠️ Skill invocation (if recommended)

### **🟡 OPTIONAL (Recommended):**
1. 🟡 session-start.sh (first message)
2. 🟡 Skill usage (if detected)

---

## 🚨 BLOCKING vs NON-BLOCKING

### **🔴 BLOCKING (MUST comply):**
1. **Task/Phase Enforcement**
   - If Complexity >= 3 → MUST create task
   - If Size >= 6 → MUST create phases
   - Cannot proceed until complied

2. **Context Limits**
   - If >90% → MUST save session
   - Cannot continue without cleanup

### **🟡 NON-BLOCKING (Should comply):**
1. Model selection (recommended but not enforced)
2. Skill suggestions (helpful but optional)
3. Context optimizations (should use but not required)

---

## 📊 DEPENDENCY GRAPH

```
session-start.sh
    │
    ├─→ Starts 9 daemons ──┐
    │                       │
    └─→ Shows recommendations
                            │
                            ▼
                    Daemons run 24/7
                            │
    ┌───────────────────────┴───────────────────────┐
    │                                               │
    ▼                                               ▼
context-daemon                              auto-recommendation-daemon
    │                                               │
    └─→ Feeds data to ─────────────────────────────┘
                            │
                            ▼
                    User sends message
                            │
    ┌───────────────────────┼───────────────────────┐
    │                       │                       │
    ▼                       ▼                       ▼
Context Check      Model Selection      Task/Phase Check
    │                       │                       │
    └───────────────────────┴───────────────────────┘
                            │
                            ▼
                      Task Required?
                       │           │
                    Yes│           │No
                       │           │
                       ▼           ▼
                  TaskCreate    Direct Execution
                       │           │
                       └─────┬─────┘
                             │
                             ▼
                    TaskUpdate(in_progress)
                             │
                             ▼
                    Pre-execution Check
                             │
                             ▼
                      Tool Execution
                             │
                             ▼
                    TaskUpdate(metadata)
                             │
                             ▼
                    More tools needed?
                       │           │
                    Yes│           │No
                       │           │
                       │           ▼
                       │   TaskUpdate(completed)
                       │           │
                       └───────────┤
                                   │
                                   ▼
                              Auto-Commit
                                   │
                                   ▼
                              Session Save
```

---

## 🔧 COMPONENT INTERACTIONS

### **Context Management:**
```
context-daemon (monitoring)
    ↓
context-monitor-v2.py (analysis)
    ↓
Claude (applies optimizations)
    ↓
Tools (use offset/limit/head_limit)
```

### **Task Management:**
```
task-phase-enforcer.py (analyzes)
    ↓
TaskCreate (creates task)
    ↓
TaskUpdate(in_progress) (starts)
    ↓
TaskUpdate(metadata) (tracks)
    ↓
TaskUpdate(completed) (finishes)
    ↓
auto-commit-enforcer.py (commits)
```

### **GitHub/Git Operations:**
```
github-cli-enforcement.md (policy)
    ↓
pre-execution-checker.py (validates)
    ↓
gh CLI (for GitHub ops: repos, PRs, issues)
    ↓
git CLI (for local ops: commit, push, pull)
```

### **Model Selection:**
```
User message
    ↓
model-selection-enforcer.py (analyzes)
    ↓
Recommends: Haiku/Sonnet/Opus
    ↓
Claude uses recommended model
```

---

## 🎯 WHAT CAN GO WRONG & PREVENTION

### **❌ Missing Task Creation:**
**Problem:** Complex task but no TaskCreate
**Prevention:** task-phase-enforcer.py BLOCKS execution
**Fix:** Auto-requires TaskCreate if Complexity >= 3

### **❌ Wrong Git Command:**
**Problem:** Using git for GitHub operations
**Prevention:** pre-execution-checker.py validates
**Fix:** Auto-suggests 'gh' CLI instead

### **❌ Context Overflow:**
**Problem:** Context >90%
**Prevention:** context-daemon alerts
**Fix:** Auto-saves session, forces cleanup

### **❌ No Progress Updates:**
**Problem:** Task running but no updates
**Prevention:** task-progress-tracking-policy.md
**Fix:** Reminds to update every 2-3 tool calls

### **❌ Forgot Auto-Commit:**
**Problem:** Task done but no commit
**Prevention:** TaskUpdate(completed) triggers it
**Fix:** auto-commit-enforcer.py runs automatically

---

## 📝 QUICK REFERENCE CHECKLIST

### **Before Starting Work:**
- [ ] session-start.sh run? (First message)
- [ ] Context checked? (<70% green)
- [ ] Model selected? (Haiku/Sonnet/Opus)
- [ ] Task complexity analyzed?
- [ ] TaskCreate if Complexity >= 3?

### **During Work:**
- [ ] Pre-execution check before tools?
- [ ] TaskUpdate(in_progress)?
- [ ] Using optimized tool parameters?
- [ ] Using 'gh' for GitHub ops?
- [ ] Using 'git' for local ops?
- [ ] TaskUpdate(metadata) every 2-3 tools?

### **After Completion:**
- [ ] TaskUpdate(completed)?
- [ ] Auto-commit triggered?
- [ ] Session saved?
- [ ] All repos committed?
- [ ] PR created if needed?

---

## 🚀 PERFORMANCE OPTIMIZATIONS

### **Token Savings:**
```
Context Monitoring → 60-80% savings
- Smart tool parameters
- Offset/limit for large files
- head_limit for grep
- Caching frequently accessed files

Response Compression → 70% savings
- Brief responses
- Diff-based edits
- Status emojis
- No verbose explanations

Smart Tool Selection → 90% savings
- Glob instead of find
- Grep instead of read all
- Direct paths instead of search
```

### **Execution Speed:**
```
Pre-execution Checks → Prevents failures
- Auto-fixes common mistakes
- Validates before execution
- No retry loops

Background Daemons → Proactive monitoring
- Issues detected early
- Recommendations ready
- No reactive delays

Task Tracking → Clear progress
- No confusion
- No duplicate work
- Clear next steps
```

---

## 📚 RELATED DOCUMENTATION

| Topic | File |
|-------|------|
| Complete System | MASTER-README.md |
| Context Management | context-optimization.md |
| Task Tracking | task-progress-tracking-policy.md |
| GitHub Operations | github-cli-usage.md |
| Git & Commits | git-and-context.md |
| Model Selection | model-selection-enforcement.md |
| Failure Prevention | common-failures-prevention.md |

---

**VERSION:** 1.0.0
**LAST UPDATED:** 2026-02-16
**LOCATION:** `~/.claude/memory/docs/policy-architecture-flow.md`

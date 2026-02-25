# 🎯 COMPLETE SYSTEM FLOW DIAGRAM

**VERSION:** 1.0.0
**DATE:** 2026-02-16
**STATUS:** 🟢 PRODUCTION READY

---

## 📊 MASTER FLOW: From User Request to Completion

```
┌─────────────────────────────────────────────────────────────────────┐
│                        🚀 CLAUDE CODE START                         │
└─────────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────────┐
│                    SESSION START (Automatic)                        │
├─────────────────────────────────────────────────────────────────────┤
│  1. Generate unique session ID                                      │
│     → session_id = "20260216-1430-a3f7"                            │
│                                                                     │
│  2. Save to temp file                                              │
│     → ~/.claude/memory/.current-session-id                         │
│                                                                     │
│  3. Run session-start.sh                                           │
│     ✅ Start 9 daemons                                             │
│     ✅ Load recommendations                                        │
│     ✅ Check system health                                         │
└─────────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────────┐
│              👤 USER REQUEST                                        │
├─────────────────────────────────────────────────────────────────────┤
│  User: "Product service me authentication add karo"                │
└─────────────────────────────────────────────────────────────────────┘
                                  ↓
╔═════════════════════════════════════════════════════════════════════╗
║                 🔴 STEP 0: FOUNDATION (ALWAYS FIRST)                ║
║            Context Management + Session Management                  ║
║                         (SYNCED TOGETHER)                           ║
╚═════════════════════════════════════════════════════════════════════╝
                                  ↓
        ┌─────────────────────────────────────────┐
        │  0A. SESSION MANAGEMENT (History)       │
        ├─────────────────────────────────────────┤
        │  Check: Previous sessions exist?        │
        │         ↓                               │
        │    YES → Load previous session          │
        │         ↓                               │
        │  Search sessions:                       │
        │  - Tags: ["product", "authentication"] │
        │  - Project: "m2-surgricals"            │
        │         ↓                               │
        │  Found: session-20260215-1020-b8c3     │
        │         ↓                               │
        │  Load session context:                  │
        │  ✅ User service auth already done     │
        │  ✅ JWT pattern used                   │
        │  ✅ Spring Security configured         │
        │  ✅ Secret Manager integrated          │
        │         ↓                               │
        │  Result: HISTORY LOADED                 │
        └─────────────────────────────────────────┘
                                  ↓
        ┌─────────────────────────────────────────┐
        │  0B. CONTEXT MANAGEMENT (Current State) │
        ├─────────────────────────────────────────┤
        │  1. Read Project README                 │
        │     → m2-surgricals/README.md          │
        │         ↓                               │
        │     Context loaded:                     │
        │     ✅ Microservices architecture      │
        │     ✅ Spring Boot services            │
        │     ✅ Config Server (8888)            │
        │     ✅ Secret Manager (1002)           │
        │     ✅ Services list                   │
        │         ↓                               │
        │  2. Read Service Documentation          │
        │     → product-service/product-service.md│
        │         ↓                               │
        │     Context loaded:                     │
        │     ✅ Current APIs                    │
        │     ✅ Database schema (PostgreSQL)    │
        │     ✅ Package structure               │
        │     ✅ Dependencies                    │
        │     ✅ Existing patterns               │
        │         ↓                               │
        │  3. Check File Structure (Find)         │
        │     → find backend/product-service/ -maxdepth 3 -type d | sort│
        │         ↓                               │
        │     Structure known:                    │
        │     ✅ controller/                     │
        │     ✅ services/impl/                  │
        │     ✅ entity/                         │
        │     ✅ repository/                     │
        │         ↓                               │
        │  Result: CURRENT STATE LOADED           │
        └─────────────────────────────────────────┘
                                  ↓
        ┌─────────────────────────────────────────┐
        │  0C. SYNC: History + Current            │
        ├─────────────────────────────────────────┤
        │  Combined Context:                      │
        │                                         │
        │  FROM HISTORY (Session):                │
        │  • JWT auth pattern used before        │
        │  • Spring Security config pattern      │
        │  • Secret Manager integration pattern  │
        │  • User preferences (skip tests, etc)  │
        │                                         │
        │  FROM CURRENT (Context):                │
        │  • Product service structure           │
        │  • Existing APIs                       │
        │  • Database schema                     │
        │  • Package conventions                 │
        │                                         │
        │  SYNCED RESULT:                        │
        │  ✅ Know what was done before          │
        │  ✅ Know current state                 │
        │  ✅ Can replicate patterns             │
        │  ✅ Consistent architecture            │
        └─────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────────┐
│                    STEP 1: PROMPT GENERATION                        │
├─────────────────────────────────────────────────────────────────────┤
│  Run: prompt-generator.py                                          │
│                                                                     │
│  Input: "Product service me authentication add karo"               │
│         ↓                                                           │
│  PHASE 1: THINKING                                                  │
│  → Analyze request                                                  │
│  → Understand intent                                                │
│  → Check anti-hallucination rules                                  │
│         ↓                                                           │
│  PHASE 2: INFORMATION GATHERING                                     │
│  → Already have context (from Step 0)                              │
│  → Already have session history (from Step 0)                      │
│  → Find similar patterns from history                              │
│         ↓                                                           │
│  PHASE 3: VERIFICATION                                              │
│  → Verify context is complete                                      │
│  → Verify no hallucination                                         │
│  → Ready to proceed                                                 │
│         ↓                                                           │
│  OUTPUT: Structured Prompt                                          │
│  {                                                                  │
│    "task_type": "API Creation",                                    │
│    "service": "product-service",                                   │
│    "feature": "authentication",                                    │
│    "pattern": "replicate-from-user-service",                       │
│    "technologies": ["Spring Boot", "JWT", "Spring Security"]       │
│  }                                                                  │
└─────────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────────┐
│                   STEP 2: TASK BREAKDOWN                            │
├─────────────────────────────────────────────────────────────────────┤
│  Run: task-auto-tracker.py --analyze                               │
│                                                                     │
│  ANALYZE:                                                           │
│  → Task: "Add authentication to product-service"                   │
│  → Similar to previous session (user-service auth)                 │
│  → Estimate: 5 files, 3 endpoints, 1 config                       │
│         ↓                                                           │
│  COMPLEXITY SCORE:                                                  │
│  Files: 5 × 2 = 10                                                 │
│  Operations: 3 endpoints × 3 = 9                                   │
│  Entities: 0 (reuse existing User)                                │
│  Dependencies: 2 (Spring Security, Secret Manager)                 │
│  Total: 10 + 9 + 0 + 2 = 21 (COMPLEX)                             │
│         ↓                                                           │
│  PHASE DIVISION: (Score >= 6 → Phases required)                   │
│  Phase 1: Security Configuration                                   │
│    - Task 1: Add Spring Security dependency                       │
│    - Task 2: Create SecurityConfig class                          │
│    - Task 3: Configure JWT filter                                 │
│                                                                     │
│  Phase 2: Authentication Controller                                │
│    - Task 4: Create AuthController                                │
│    - Task 5: Add login endpoint                                   │
│    - Task 6: Add logout endpoint                                  │
│                                                                     │
│  Phase 3: Token Service                                            │
│    - Task 7: Create TokenService                                  │
│    - Task 8: Generate JWT tokens                                  │
│    - Task 9: Validate tokens                                      │
│         ↓                                                           │
│  OUTPUT:                                                            │
│  ✅ 3 Phases created                                               │
│  ✅ 9 Tasks created                                                │
│  ✅ Dependencies auto-detected                                     │
│  ✅ Auto-tracking enabled                                          │
└─────────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────────┐
│                   STEP 3: PLAN MODE DECISION                        │
├─────────────────────────────────────────────────────────────────────┤
│  Run: auto-plan-mode-suggester.py                                  │
│                                                                     │
│  INPUT:                                                             │
│  - Complexity: 21 (COMPLEX)                                        │
│  - Risk factors:                                                   │
│    • Security-critical (authentication)                            │
│    • Cross-service pattern replication                            │
│         ↓                                                           │
│  DECISION MATRIX:                                                   │
│  Score 21 → Base: RECOMMENDED                                      │
│  + Security (+3) → MANDATORY                                       │
│         ↓                                                           │
│  DECISION: ENTER PLAN MODE (MANDATORY)                             │
│         ↓                                                           │
│  EnterPlanMode()                                                    │
│    → User approval required                                        │
│    → Design implementation plan                                    │
│    → Review architecture                                           │
│    → Exit plan mode when approved                                 │
│         ↓                                                           │
│  OUTPUT:                                                            │
│  ✅ Implementation plan created                                    │
│  ✅ User approved                                                  │
│  ✅ Ready to execute                                               │
└─────────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────────┐
│                   STEP 4: MODEL SELECTION                           │
├─────────────────────────────────────────────────────────────────────┤
│  Run: intelligent-model-selector.py                                │
│                                                                     │
│  INPUT:                                                             │
│  - Complexity: 21 (COMPLEX)                                        │
│  - Task Type: "API Creation"                                       │
│  - Plan Mode: YES (entered)                                        │
│  - Risk: Security-critical                                         │
│         ↓                                                           │
│  DECISION RULES:                                                    │
│  Plan Mode = YES → OPUS (mandatory for planning)                   │
│  After plan approval → SONNET (for implementation)                 │
│         ↓                                                           │
│  SELECTED MODEL:                                                    │
│  Planning Phase: OPUS                                              │
│  Execution Phase: SONNET                                           │
│         ↓                                                           │
│  COST ESTIMATE:                                                     │
│  OPUS: ~15K tokens × $15/M = $0.225                               │
│  SONNET: ~30K tokens × $3/M = $0.09                               │
│  Total: ~$0.315                                                    │
│         ↓                                                           │
│  OUTPUT:                                                            │
│  ✅ OPUS for plan                                                  │
│  ✅ SONNET for implementation                                      │
└─────────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────────┐
│                 STEP 5: SKILL & AGENT SELECTION                     │
├─────────────────────────────────────────────────────────────────────┤
│  Run: auto-skill-agent-selector.py                                 │
│                                                                     │
│  INPUT:                                                             │
│  - Technologies: ["Spring Boot", "JWT", "Spring Security"]         │
│  - Complexity: 21                                                  │
│  - Task Type: "API Creation"                                       │
│         ↓                                                           │
│  MATCHING:                                                          │
│  Spring Boot detected → Complexity 21 >= 10                        │
│    → Use AGENT: spring-boot-microservices                          │
│         ↓                                                           │
│  SKILLS AVAILABLE:                                                  │
│  - java-spring-boot-microservices (knowledge)                      │
│  - spring-boot-design-patterns-core (patterns)                     │
│  - rdbms-core (database)                                           │
│         ↓                                                           │
│  OUTPUT:                                                            │
│  ✅ Agent: spring-boot-microservices                               │
│  ✅ Skills: java-spring-boot-microservices,                        │
│             spring-boot-design-patterns-core                        │
│  ✅ Execution: Task(subagent_type='spring-boot-microservices')    │
└─────────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────────┐
│                 STEP 6: TOOL USAGE OPTIMIZATION                     │
├─────────────────────────────────────────────────────────────────────┤
│  Run: tool-usage-optimizer.py (before EVERY tool call)            │
│                                                                     │
│  OPTIMIZATIONS:                                                     │
│                                                                     │
│  About to call: Read(file_path="SecurityConfig.java")             │
│    ↓                                                                │
│  CHECK: File size = 850 lines                                      │
│    ↓                                                                │
│  OPTIMIZE: Add offset=0, limit=100                                 │
│    ↓                                                                │
│  EXECUTE: Read("SecurityConfig.java", offset=0, limit=100)        │
│  SAVINGS: 75% tokens (750 lines skipped)                          │
│         ↓                                                           │
│  About to call: Grep(pattern="@RestController")                   │
│    ↓                                                                │
│  OPTIMIZE: Add head_limit=100, output_mode='files_with_matches'   │
│    ↓                                                                │
│  EXECUTE: Grep("@RestController", head_limit=100)                 │
│  SAVINGS: 80% tokens (file list only)                             │
│         ↓                                                           │
│  About to call: Bash("find . -name *.java")                       │
│    ↓                                                                │
│  SUGGEST: Use tree instead for structure                           │
│    ↓                                                                │
│  EXECUTE: find backend/product-service/ -name "*.java" -type f | sort│
│  SAVINGS: 85% tokens (structure vs list)                          │
│         ↓                                                           │
│  TOTAL SAVINGS: 60-85% tokens on every tool call                  │
└─────────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────────┐
│                      STEP 7: EXECUTION                              │
├─────────────────────────────────────────────────────────────────────┤
│  Execute with: SONNET model + spring-boot-microservices agent      │
│                                                                     │
│  PHASE 1: Security Configuration                                   │
│  ┌───────────────────────────────────────────────────────────┐    │
│  │ Task 1: Add Spring Security dependency                    │    │
│  │   → Edit pom.xml                                          │    │
│  │   → TaskUpdate(status='in_progress')                      │    │
│  │   → Write changes                                         │    │
│  │   → TaskUpdate(status='completed')                        │    │
│  │   ✅ Done                                                 │    │
│  ├───────────────────────────────────────────────────────────┤    │
│  │ Task 2: Create SecurityConfig class                       │    │
│  │   → Write SecurityConfig.java                             │    │
│  │   → TaskUpdate(status='in_progress')                      │    │
│  │   → Use pattern from user-service (from session history)  │    │
│  │   → TaskUpdate(status='completed')                        │    │
│  │   ✅ Done                                                 │    │
│  ├───────────────────────────────────────────────────────────┤    │
│  │ Task 3: Configure JWT filter                              │    │
│  │   → Write JwtAuthenticationFilter.java                    │    │
│  │   → TaskUpdate(status='in_progress')                      │    │
│  │   → Replicate from session 20260215-1020-b8c3            │    │
│  │   → TaskUpdate(status='completed')                        │    │
│  │   ✅ Done                                                 │    │
│  └───────────────────────────────────────────────────────────┘    │
│  ✅ PHASE 1 COMPLETE                                               │
│         ↓                                                           │
│  🚨 AUTO-COMMIT TRIGGERED (Phase complete)                         │
│  → git add -A                                                      │
│  → git commit -m "✅ Phase 1: Security Configuration"             │
│  → git push                                                        │
│  ✅ Committed + Pushed                                             │
│         ↓                                                           │
│  PHASE 2: Authentication Controller                                │
│  [Similar execution...]                                            │
│  ✅ PHASE 2 COMPLETE → AUTO-COMMIT                                │
│         ↓                                                           │
│  PHASE 3: Token Service                                            │
│  [Similar execution...]                                            │
│  ✅ PHASE 3 COMPLETE → AUTO-COMMIT                                │
└─────────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────────┐
│                STEP 8: PROGRESS TRACKING (Automatic)                │
├─────────────────────────────────────────────────────────────────────┤
│  Auto-updates after every 2-3 tool calls:                          │
│                                                                     │
│  TaskUpdate(                                                        │
│    taskId='1',                                                     │
│    status='in_progress',                                           │
│    metadata={                                                      │
│      'progress': 40,                                               │
│      'current_step': 'Creating SecurityConfig',                   │
│      'completed': ['Add dependency'],                             │
│      'remaining': ['JWT filter', 'AuthController', 'TokenService']│
│    }                                                               │
│  )                                                                  │
│         ↓                                                           │
│  User sees real-time progress:                                     │
│  ⏳ Task 1: In Progress (40%)                                      │
│     Current: Creating SecurityConfig                               │
│     ✅ Add dependency                                              │
│     ⏸️ JWT filter                                                  │
└─────────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────────┐
│                   STEP 9: GIT AUTO-COMMIT                           │
├─────────────────────────────────────────────────────────────────────┤
│  ALL PHASES COMPLETE                                                │
│         ↓                                                           │
│  Run: auto-commit-enforcer.py --enforce-now                        │
│         ↓                                                           │
│  SCAN WORKSPACE:                                                    │
│  Found repos with changes:                                         │
│  • backend/product-service/                                        │
│         ↓                                                           │
│  FOR EACH REPO:                                                     │
│  ┌─────────────────────────────────────────────────┐              │
│  │ Repository: product-service                      │              │
│  ├─────────────────────────────────────────────────┤              │
│  │ Files changed:                                   │              │
│  │ • pom.xml                                        │              │
│  │ • SecurityConfig.java (new)                      │              │
│  │ • JwtAuthenticationFilter.java (new)             │              │
│  │ • AuthController.java (new)                      │              │
│  │ • TokenService.java (new)                        │              │
│  │                                                  │              │
│  │ git add -A                                       │              │
│  │ git commit -m "✓ Task Complete: Add auth to     │              │
│  │                 product-service                  │              │
│  │                                                  │              │
│  │ - Spring Security configured                     │              │
│  │ - JWT authentication added                       │              │
│  │ - Auth endpoints created                         │              │
│  │                                                  │              │
│  │ Co-Authored-By: Claude Sonnet 4.5"              │              │
│  │                                                  │              │
│  │ git push                                         │              │
│  │                                                  │              │
│  │ ✅ Committed: abc123def                         │              │
│  │ ✅ Pushed: Success                               │              │
│  └─────────────────────────────────────────────────┘              │
│         ↓                                                           │
│  OUTPUT:                                                            │
│  ✅ All repos committed and pushed                                │
└─────────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────────┐
│                  STEP 10: SESSION SAVE                              │
├─────────────────────────────────────────────────────────────────────┤
│  Daemon: session-auto-save-daemon.py (runs every 10-30 min)       │
│         ↓                                                           │
│  CHECK: Should save session?                                       │
│  ✅ Task completed                                                 │
│  ✅ Multiple files modified (5)                                    │
│  ✅ 45 minutes elapsed                                             │
│         ↓                                                           │
│  SAVE SESSION:                                                      │
│  session_id: "20260216-1430-a3f7"                                 │
│         ↓                                                           │
│  GENERATE SUMMARY:                                                  │
│  ---                                                                │
│  session_id: "20260216-1430-a3f7"                                 │
│  timestamp: "2026-02-16 14:30:00"                                 │
│  project: "m2-surgricals"                                         │
│  purpose: "Add authentication to product-service"                 │
│  tags: ["authentication", "jwt", "product-service", "security"]   │
│  duration: "45 minutes"                                            │
│  files_modified: 5                                                 │
│  status: "completed"                                               │
│                                                                     │
│  auto_committed: true                                              │
│  repos_committed: ["product-service"]                              │
│  commit_hashes:                                                    │
│    - repo: "product-service"                                       │
│      hash: "abc123def456"                                          │
│      message: "✓ Task Complete: Add auth"                         │
│      pushed: true                                                  │
│  ---                                                                │
│         ↓                                                           │
│  SAVE FILES:                                                        │
│  1. sessions/m2-surgricals/session-20260216-1430-a3f7.md         │
│  2. sessions/session-index.json (update)                           │
│  3. sessions/m2-surgricals/project-summary.md (update)            │
│         ↓                                                           │
│  🚨 TRIGGER AUTO-COMMIT (integrated)                               │
│  → Already committed in Step 9                                     │
│  → Just log the commit hashes                                      │
│         ↓                                                           │
│  OUTPUT:                                                            │
│  ✅ Session saved with ID: 20260216-1430-a3f7                     │
│  ✅ Index updated                                                  │
│  ✅ Project summary updated                                        │
│  ✅ All code committed and pushed                                 │
└─────────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────────┐
│                     STEP 11: LOGGING                                │
├─────────────────────────────────────────────────────────────────────┤
│  Log all policy applications:                                      │
│                                                                     │
│  ~/.claude/memory/logs/policy-hits.log:                           │
│  [2026-02-16 14:30:00] prompt-generation | structured-prompt      │
│  [2026-02-16 14:30:05] task-breakdown | 9-tasks-created           │
│  [2026-02-16 14:30:08] plan-mode-suggester | mandatory-enter      │
│  [2026-02-16 14:30:15] model-selector | opus-then-sonnet          │
│  [2026-02-16 14:30:18] skill-selector | spring-boot-agent         │
│  [2026-02-16 14:30:20] tool-optimizer | 65%-savings               │
│  [2026-02-16 14:45:00] auto-commit | 1-repo-committed             │
│  [2026-02-16 14:45:05] session-save | saved-with-id               │
│         ↓                                                           │
│  ~/.claude/memory/logs/policy-counters.txt:                       │
│  prompt-generation=47                                              │
│  task-breakdown=38                                                 │
│  plan-mode-suggester=12                                            │
│  model-selector=47                                                 │
│  skill-selector=35                                                 │
│  tool-optimizer=289                                                │
│  auto-commit=25                                                    │
│  session-save=18                                                   │
└─────────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────────┐
│                         ✅ WORK COMPLETE                            │
├─────────────────────────────────────────────────────────────────────┤
│  DELIVERABLES:                                                      │
│  ✅ Authentication added to product-service                        │
│  ✅ 5 files created/modified                                       │
│  ✅ Spring Security configured                                     │
│  ✅ JWT tokens implemented                                         │
│  ✅ Pattern replicated from user-service (consistent!)            │
│         ↓                                                           │
│  SESSION:                                                           │
│  ✅ Saved with ID: 20260216-1430-a3f7                             │
│  ✅ Can load later: python session-loader.py load 20260216-...    │
│  ✅ Searchable by tags: authentication, jwt, product-service      │
│         ↓                                                           │
│  GIT:                                                               │
│  ✅ All changes committed                                          │
│  ✅ Pushed to remote (backed up)                                   │
│  ✅ Commit hash: abc123def456                                      │
│         ↓                                                           │
│  CONTEXT:                                                           │
│  ✅ project-summary.md updated                                     │
│  ✅ product-service.md updated (new APIs documented)               │
│  ✅ Ready for next session                                         │
└─────────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────────┐
│                      USER: "Next task?"                             │
└─────────────────────────────────────────────────────────────────────┘
                                  ↓
                    [CYCLE REPEATS FROM STEP 0]

```

---

## 🔄 PARALLEL PROCESSES (Background Daemons)

```
While main flow executes, 9 daemons run in background:

┌─────────────────────────────────────────────────────────────────────┐
│                     DAEMON 1: context-daemon                        │
│  Monitors context usage (70%, 85%, 90% thresholds)                │
│  Triggers cleanup when needed                                      │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                DAEMON 2: session-auto-save-daemon                   │
│  Every 10-30 min: Check if session should be saved                │
│  Triggers: Task complete, files modified, time elapsed             │
│  → Saves session + triggers auto-commit                            │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│               DAEMON 3: preference-auto-tracker                     │
│  Learns user preferences from interactions                         │
│  Updates user preference file                                      │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                DAEMON 4: skill-auto-suggester                       │
│  Monitors task patterns                                            │
│  Suggests skills proactively                                       │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                   DAEMON 5: commit-daemon                           │
│  Monitors git repos for changes                                    │
│  Triggers commits based on file count, time                        │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│              DAEMON 6: session-pruning-daemon                       │
│  Cleans old sessions (archive after 90 days)                      │
│  Maintains session index                                           │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│              DAEMON 7: pattern-detection-daemon                     │
│  Detects code patterns across sessions                             │
│  Builds pattern library                                            │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│            DAEMON 8: failure-prevention-daemon                      │
│  Monitors for common failures                                      │
│  Auto-applies fixes                                                │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│            DAEMON 9: auto-recommendation-daemon                     │
│  Every 5 sec: Generate recommendations                             │
│  Model, skills, agents, context status                             │
│  Used by session-start.sh                                          │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 📊 CONTEXT + SESSION SYNC (Detailed)

```
┌─────────────────────────────────────────────────────────────────────┐
│                    CONTEXT MANAGEMENT LAYER                         │
├─────────────────────────────────────────────────────────────────────┤
│  REAL-TIME (Current Understanding)                                  │
│                                                                     │
│  Data Sources:                                                      │
│  • Project README.md (architecture, services)                      │
│  • Service .md files (APIs, database, structure)                   │
│  • Tree structure (file locations)                                 │
│  • Code files (current implementations)                            │
│                                                                     │
│  Provides:                                                          │
│  ✅ "What exists NOW"                                              │
│  ✅ "Where files are located"                                      │
│  ✅ "Current architecture"                                         │
│  ✅ "Existing patterns"                                            │
└─────────────────────────────────────────────────────────────────────┘
                                  ↕️  SYNC
┌─────────────────────────────────────────────────────────────────────┐
│                    SESSION MANAGEMENT LAYER                         │
├─────────────────────────────────────────────────────────────────────┤
│  HISTORICAL (Past Work Record)                                      │
│                                                                     │
│  Data Sources:                                                      │
│  • session-{id}.md files (what was done)                           │
│  • session-index.json (searchable registry)                        │
│  • project-summary.md (cumulative history)                         │
│  • Git commits (code snapshots)                                    │
│                                                                     │
│  Provides:                                                          │
│  ✅ "What was done BEFORE"                                         │
│  ✅ "Decisions made in past"                                       │
│  ✅ "Patterns used previously"                                     │
│  ✅ "User preferences learned"                                     │
└─────────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────────┐
│                    COMBINED INTELLIGENCE                            │
├─────────────────────────────────────────────────────────────────────┤
│  CONTEXT (Now) + SESSION (History) = COMPLETE UNDERSTANDING         │
│                                                                     │
│  Example:                                                           │
│  • Context: "product-service has /products API"                    │
│  • Session: "user-service used JWT pattern for auth"              │
│  • Combined: "Add JWT auth to product-service using same pattern" │
│                                                                     │
│  Benefits:                                                          │
│  ✅ Consistent architecture across services                        │
│  ✅ No re-explaining patterns                                      │
│  ✅ Fast implementation (replicate from history)                   │
│  ✅ 70-90% token savings (no context gathering needed)            │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🎯 CRITICAL PATH (Mandatory Steps)

```
CANNOT BE SKIPPED:

Step 0:  Context + Session Loading         ← FOUNDATION
Step 4:  Model Selection                   ← QUALITY
Step 6:  Tool Optimization                 ← EFFICIENCY
Step 9:  Auto-Commit                       ← SAFETY
Step 10: Session Save                      ← CONTINUITY

CAN BE CONDITIONAL:

Step 1:  Prompt Generation                 (simple tasks can skip)
Step 2:  Task Breakdown                    (complexity < 3 can skip)
Step 3:  Plan Mode                         (complexity < 10 can skip)
Step 5:  Skill/Agent Selection             (simple tasks can skip)
Step 7:  Execution                         (main work - always runs)
Step 8:  Progress Tracking                 (simple tasks can skip)
```

---

## 📈 TOKEN SAVINGS (Cumulative)

```
WITHOUT SYSTEM (Traditional Approach):
  - No context docs → Blind search (15K tokens)
  - No session history → Re-explain (10K tokens)
  - No tool optimization → Full reads (20K tokens)
  - No pattern reuse → Design from scratch (15K tokens)
  Total: ~60K tokens per task

WITH SYSTEM (Our Approach):
  - Read README + service.md (2K tokens)
  - Load session history (1K tokens)
  - Optimized tool calls (5K tokens)
  - Replicate pattern (2K tokens)
  Total: ~10K tokens per task

SAVINGS: 83% tokens! 🚀
```

---

## 🔒 ISOLATION GUARANTEES

```
Context + Session:
  ✅ Always run FIRST
  ✅ Never skipped
  ✅ Independent from other policies
  ✅ Synced with each other
  ❌ Cannot be disabled
  ❌ Cannot be modified by other policies

Other Policies:
  ✅ Run AFTER context/session
  ✅ Use context/session data
  ✅ Can be conditional
  ✅ Can be skipped
  ❌ Cannot modify context/session logic
  ❌ Cannot run before context/session
```

---

**VERSION:** 1.0.0
**CREATED:** 2026-02-16
**LOCATION:** `~/.claude/memory/docs/COMPLETE-SYSTEM-FLOW.md`

**Ye raha complete flow diagram bhai!** 🎯

Har step crystal clear - session start se lekar completion tak! 🚀

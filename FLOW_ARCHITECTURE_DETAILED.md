# Claude Insight - Complete Flow Architecture

**Version:** 3.3.0
**Date:** 2026-03-05
**Purpose:** Explain how policies are chained, loaded, and executed

---

## 🎯 High-Level Flow

```
USER INPUT
    ↓
[HOOK: UserPromptSubmit]
    ├─ clear-session-handler.py
    └─ 3-level-flow.py (MAIN ORCHESTRATOR)
         ├─ Level -1: AUTO-FIX
         ├─ Level 1: SYNC SYSTEM
         ├─ Level 2: STANDARDS SYSTEM
         └─ Level 3: EXECUTION SYSTEM (12 steps)
              └─ Writes: flow-trace.json
    ↓
USER MESSAGE ENHANCED with CHECKPOINT
    ↓
CLAUDE PROCESSES MESSAGE
    ↓
[HOOK: PreToolUse]
    └─ pre-tool-enforcer.py (Reads flow-trace.json)
         ├─ Level 3.3: Checkpoint validation
         ├─ Level 3.5: Skill/Agent context (TASK-AWARE)
         ├─ Level 3.6: Tool optimization
         ├─ Level 3.7: Failure prevention
         └─ Outputs: Hints + Blocks
    ↓
[HOOK: PostToolUse]
    └─ post-tool-tracker.py
         ├─ Progress tracking
         └─ Flag clearing
    ↓
[HOOK: Stop]
    └─ stop-notifier.py
         ├─ Session saving
         └─ Voice notification
    ↓
SESSION COMPLETE
```

---

## 📋 DETAILED BREAKDOWN: Session Start to End

### **PHASE 0: Session Initialization**

```
Timeline: T+0s
Trigger: User opens Claude Code IDE

Actions:
1. Read ~/.claude/settings.json (hooks configuration)
2. Load all 4 hooks:
   - UserPromptSubmit (ASYNC=false)
   - PreToolUse (ASYNC=false)
   - PostToolUse (ASYNC=false)
   - Stop (ASYNC=false)
3. Initialize metrics_emitter (non-blocking)
4. Create .current-session.json with SESSION_ID
5. Generate session logs directory: ~/.claude/memory/logs/sessions/{SESSION_ID}/

Status: Ready for user input
```

---

### **PHASE 1: User Submits Message**

```
Timeline: T+1s
Trigger: User types message and submits

Example:
  "Implement JWT auth in Spring Boot API with Angular UI and Docker deployment"

Actions at this moment:
1. Claude Code captures raw message
2. Triggers [Hook: UserPromptSubmit]
3. Message queued for hook processing
```

---

### **PHASE 2: Hook #1 - UserPromptSubmit (Session Handler)**

```
Timeline: T+1.1s
Script: clear-session-handler.py

Flow:
1. Load ~/.claude/memory/.current-session.json
2. Check if this is NEW session or CONTINUING session
3. If CONTINUING:
   a. Save previous context to ~/.claude/memory/logs/sessions/{OLD_SESSION_ID}/
   b. Mark old session as complete
4. Create new session context:
   {
     "session_id": "SESSION-20260305-210424-75B6",
     "start_time": "2026-03-05T21:04:24Z",
     "pid": 12345,
     "user_message": "Implement JWT auth...",
     "status": "in_progress"
   }

Output: Session state cleared, ready for processing
```

---

### **PHASE 3: Hook #1 Part 2 - 3-Level Flow (MAIN ORCHESTRATOR)**

```
Timeline: T+1.2s
Script: 3-level-flow.py (THE BRAIN)

MOST IMPORTANT PART - Let me break it down:

═══════════════════════════════════════════════════════════════════

LEVEL -1: AUTO-FIX ENFORCEMENT (Loophole Prevention)
───────────────────────────────────────────────────────────────────
Location: scripts/architecture/03-execution-system/failure-prevention/
Script: auto-fix-enforcer.py

Checks (7 validations):
1. ✓ Flag directory exists: ~/.claude
2. ✓ Memory structure valid: ~/.claude/memory/
3. ✓ Log directory valid: ~/.claude/memory/logs/
4. ✓ Session directory exists: ~/.claude/memory/logs/sessions/
5. ✓ Scripts accessible: ~/.claude/scripts/
6. ✓ Policies loaded: ~/.claude/policies/
7. ✓ Metrics system ready: metrics_emitter.py accessible

IF ANY CHECK FAILS → BLOCK AND REPORT ERROR

Output: Auto-fix report, system health status

═══════════════════════════════════════════════════════════════════

LEVEL 1: SYNC SYSTEM (Context Management)
───────────────────────────────────────────────────────────────────
Location: scripts/architecture/01-sync-system/

Sub-Policies Executed:
1. Session Context Policy
   - Load current session ID
   - Load user preferences
   - Load conversation history
   File: session-management/load-session-state-policy.py

2. Context Management Policy
   - Calculate current context usage (e.g., 92% of 200k tokens)
   - Detect context overflow
   - Apply context optimization if needed
   File: context-management/context-optimization-policy.py

3. Pattern Detection Policy
   - Detect user coding patterns
   - Detect common mistakes
   File: pattern-detection/pattern-detector-policy.py

Output:
{
  "session_id": "SESSION-20260305-210424-75B6",
  "context_usage": 92,
  "user_preferences": {...},
  "patterns": {...}
}

═══════════════════════════════════════════════════════════════════

LEVEL 2: STANDARDS SYSTEM (Policy Loading)
───────────────────────────────────────────────────────────────────
Location: scripts/architecture/02-standards-system/

Action: LOAD ALL POLICIES
1. Read from: ~/.claude/policies/
2. Load directory structure:
   ├─ 01-sync-system/ (6 policies)
   ├─ 02-standards-system/ (2 policies)
   └─ 03-execution-system/ (26 policies)

Total: 34 policies loaded into memory
File: standards-enforcement-policy.py

Output:
{
  "policies_loaded": 34,
  "standards": 15,
  "rules": 156,
  "status": "compliant"
}

═══════════════════════════════════════════════════════════════════

LEVEL 3: EXECUTION SYSTEM (12-Step Task Execution)
───────────────────────────────────────────────────────────────────
Location: scripts/architecture/03-execution-system/

**THIS IS WHERE THE MAGIC HAPPENS**

Step 3.0: PROMPT GENERATION
  File: 00-prompt-generation/enhanced-prompt-generation-policy.py
  Action:
    - Detect user intent from raw message
    - Add policy context
    - Create "enhanced prompt"
  Output:
    Original: "Implement JWT auth in Spring Boot..."
    Enhanced: "{SYSTEM INSTRUCTIONS + USER MESSAGE + POLICIES}"

Step 3.1: TASK BREAKDOWN
  File: 01-task-breakdown/automatic-task-breakdown-policy.py
  Action:
    1. detect_tech_from_message()
       Input: "Implement JWT auth in Spring Boot API with Angular..."
       Output: tech_stack = ['spring-boot', 'angular', 'docker']

    2. extract_entities()
       Output: entities = ['jwt', 'auth']

    3. estimate_file_count()
       Output: file_count = 12

    4. estimate_complexity()
       Output: complexity = 18

    5. detect_phases(tech_stack=tech_stack)
       Since backend detected → Use backend phases:
       Output: phases = [
         'Foundation',
         'Business Logic',
         'API Layer',
         'Configuration'
       ]

    6. generate_tasks()
       Output: task_list = [
         Task 1: Create User entity (phase: Foundation)
         Task 2: Create User repository (phase: Foundation)
         Task 3: Implement Auth service (phase: Business Logic)
         ...etc
       ]

  Output to flow-trace.json:
  {
    "tech_stack": ["spring-boot", "angular", "docker"],
    "entities": ["jwt", "auth"],
    "file_count": 12,
    "complexity": 18,
    "needs_phases": true,
    "phases": [...]
  }

Step 3.2: PLAN MODE
  File: 02-plan-mode/plan-mode-detection-policy.py
  Action:
    - Check if task needs plan mode
    - Complexity >= 15? → Show plan mode
    - Otherwise → Skip
  Output: plan_mode = true

Step 3.4: MODEL SELECTION
  File: 04-model-selection/model-selection-policy.py
  Action:
    - Analyze complexity (18/25)
    - Analyze context usage (92%)
    - Select appropriate model

  Decision Tree:
    If complexity >= 20 → Use OPUS
    Elif complexity >= 15 → Use SONNET
    Else → Use HAIKU

  Output: model_selected = "sonnet"

Step 3.5: SKILL/AGENT SELECTION ⭐ (NEW v3.3.0)
  File: 05-skill-agent-selection/auto-skill-agent-selection-policy.py
  Action:
    1. match_technologies(["spring-boot", "angular", "docker"])
       - spring-boot → java-spring-boot-microservices (agent)
       - angular → angular-engineer (agent)
       - docker → devops-engineer (agent)

    2. Check multi-domain escalation rule
       Domains detected: BACKEND + FRONTEND + DEVOPS (3 domains)
       → Escalate to orchestrator-agent ⭐

    3. Build supplementary_skills list
       - java-spring-boot-microservices
       - angular-engineer
       - devops-engineer

  Output to flow-trace.json:
  {
    "skill_or_agent": "orchestrator-agent",
    "skill_type": "agent",
    "supplementary_skills": ["java-spring-boot-microservices", "angular-engineer", "devops-engineer"],
    "reasoning": "Multi-domain task (backend, frontend, devops) → orchestrator-agent"
  }

Step 3.6: TOOL OPTIMIZATION
  File: 06-tool-optimization/tool-usage-optimization-policy.py
  Action:
    - Analyze anticipated tool usage
    - Suggest optimization hints
    - Example: "For Grep on large files, use --head-limit"
  Output: Optimization hints (non-blocking)

Step 3.7: FAILURE PREVENTION
  File: failure-prevention/common-failures-prevention.py
  Action:
    - Consult failure-kb.json
    - Suggest common failure patterns
    - Example: "Don't delete files without backup"
  Output: Prevention hints (non-blocking)

Step 3.8: RECOMMENDATIONS
  File: 07-recommendations/contextual-recommendations-policy.py
  Action:
    - Suggest best practices for detected tech
    - Example: "Use async/await for FastAPI"
  Output: Recommendation hints (non-blocking)

Step 3.9: PROGRESS TRACKING
  File: 08-progress-tracking/progress-tracking-policy.py
  Action:
    - Initialize task tracking
    - Create active-tasks.json
  Output: Task tracking initialized

Step 3.10: GIT COMMIT
  File: 09-git-commit/git-auto-commit-policy.py
  Action:
    - Check if code changes exist
    - Generate commit message
    - Auto-commit with flags
  Output: Git commit metadata

═══════════════════════════════════════════════════════════════════

FINAL OUTPUT FROM 3-LEVEL-FLOW.py
───────────────────────────────────────────────────────────────────

Writes to: ~/.claude/memory/logs/sessions/{SESSION_ID}/flow-trace.json

Structure:
{
  "session_id": "SESSION-20260305-210424-75B6",
  "timestamp": "2026-03-05T21:04:30Z",
  "user_input": {
    "prompt": "Implement JWT auth in Spring Boot..."
  },
  "final_decision": {
    "task_type": "API Development",
    "complexity": 18,
    "model_selected": "sonnet",
    "plan_mode": true,
    "skill_or_agent": "orchestrator-agent",
    "supplementary_skills": ["java-spring-boot-microservices", "angular-engineer", "devops-engineer"],
    "tech_stack": ["spring-boot", "angular", "docker"],
    "entities": ["jwt", "auth"],
    "file_count": 12,
    "needs_phases": true,
    "phases": ["Foundation", "Business Logic", "API Layer", "Configuration"]
  },
  "checkpoint": {
    "session_id": "SESSION-20260305-210424-75B6",
    "complexity": "18/25",
    "model": "sonnet",
    "context": "92%"
  }
}

This JSON is the SINGLE SOURCE OF TRUTH for the entire session!
```

---

### **PHASE 4: Display Checkpoint to User**

```
Timeline: T+1.5s
Hook Output:

╔════════════════════════════════════════════════════════════════╗
║                    ✓ CHECKPOINT - APPROVED                    ║
╠════════════════════════════════════════════════════════════════╣
║ Session:    SESSION-20260305-210424-75B6                      ║
║ Complexity: 18/25 (Medium-High)                               ║
║ Model:      sonnet (appropriate for complexity)               ║
║ Context:    92% (4 optimizations applied)                     ║
║ Status:     Ready to proceed                                  ║
║ Tech Stack: spring-boot, angular, docker                      ║
║ Primary:    orchestrator-agent (multi-domain)                 ║
╚════════════════════════════════════════════════════════════════╝
```

---

### **PHASE 5: Claude Processes Message**

```
Timeline: T+2s to T+N (depends on task complexity)

Claude uses the ENHANCED PROMPT which includes:
1. Original user message
2. System policies (34 policies)
3. Checkpoint context
4. Task breakdown
5. Phase information
6. Skill/Agent selection

Claude can now:
- Use orchestrator-agent as primary brain
- Delegate to java-spring-boot-microservices when writing Java
- Delegate to angular-engineer when writing TypeScript
- Delegate to devops-engineer when writing Docker configs
- All while being AWARE of what other files exist in the task
```

---

### **PHASE 6: Hook #2 - PreToolUse (Before Each Tool)**

```
Timeline: T+X (every time Claude calls a tool)
Script: pre-tool-enforcer.py

Example 1: Claude calls Read on UserController.java

Actions:
1. Load flow-trace.json (CACHED IN MEMORY)
   {
     "tech_stack": ["spring-boot", "angular", "docker"],
     "skill": "orchestrator-agent",
     "supplementary_skills": [...]
   }

2. Check tool type and file
   tool_name = "Read"
   file_path = "src/main/java/com/example/controller/UserController.java"

3. Run check_dynamic_skill_context(tool_name, file_path, trace_context=flow_ctx)

   File analysis:
   - Extension: .java
   - Pattern match: FILE_EXT_SKILL_MAP[".java"] = "java-spring-boot-microservices"

   Output hint:
   [SKILL-CONTEXT] UserController.java → java-spring-boot-microservices (skill)
     CONTEXT: Java/Spring Boot patterns, annotations, DI, REST controllers
     TASK TECH STACK: spring-boot, angular, docker
     SESSION PRIMARY: orchestrator-agent
     OTHER FILES IN THIS TASK: .ts → angular-engineer | Dockerfile → docker
     ACTION: Apply java-spring-boot-microservices patterns...

4. Run tool optimization checks
   - File size > 1000 lines? → Suggest limit + offset
   - Using Grep? → Suggest head_limit parameter

5. Consult failure-kb.json
   - Are there known failures for Read on Java files?
   - Print hints if found

Exit: 0 (allow tool), print hints to stdout
```

Example 2: Claude calls Write on Dockerfile

```
Actions:
1. Same flow-trace.json load
2. File analysis:
   - filename: "Dockerfile"
   - Pattern match: FILENAME_SKILL_MAP["Dockerfile"] = "docker"

   Output hint:
   [SKILL-CONTEXT] Dockerfile → docker (skill)
     CONTEXT: Docker image definitions, layers, optimization
     TASK TECH STACK: spring-boot, angular, docker
     SESSION PRIMARY: orchestrator-agent
     OTHER FILES IN THIS TASK: .java → java-spring-boot-microservices | .ts → angular-engineer
     ACTION: Apply docker patterns...

3. Check failure-kb for Dockerfile mistakes
4. Suggest optimizations (multi-stage builds, etc.)
Exit: 0
```

Example 3: Claude calls Write on auth.component.ts

```
Output hint:
[SKILL-CONTEXT] auth.component.ts → angular-engineer (agent)
  CONTEXT: Angular components, services, RxJS patterns
  TASK TECH STACK: spring-boot, angular, docker
  SESSION PRIMARY: orchestrator-agent
  OTHER FILES IN THIS TASK: .java → java-spring-boot-microservices | Dockerfile → docker
  ACTION: Apply angular-engineer patterns...
```

**KEY POINT:** Every tool call shows complete context!
User knows which technologies are in play, what the session-level coordinator is, and what other files they'll touch.
```

---

### **PHASE 7: Hook #3 - PostToolUse (After Each Tool)**

```
Timeline: T+X+0.1s (immediately after tool completes)
Script: post-tool-tracker.py

Actions:
1. Log tool execution:
   {
     "tool": "Read",
     "file": "UserController.java",
     "status": "success",
     "duration_ms": 150
   }

2. Update task progress
   - If task marked complete → increment progress
   - Update active-tasks.json

3. Clear flags if needed
   - If skill selection just completed → clear .skill-selection-pending.json
   - If task breakdown completed → clear .task-breakdown-pending.json

Exit: Continue to next tool or response
```

---

### **PHASE 8: Hook #4 - Stop (Session End)**

```
Timeline: T+N (when Claude finishes response)
Script: stop-notifier.py

Actions:
1. Load final session state
2. Aggregate all metrics:
   - Tools used: [Read, Write, Edit, Bash, ...]
   - Tasks completed: 5/8
   - Files modified: 12
   - Duration: 15 minutes

3. Save session summary to:
   ~/.claude/memory/logs/sessions/{SESSION_ID}/session-summary.json

4. Check context usage:
   - If context > 90% used
   - Execute cleanup: delete old sessions (keep last 5)

5. Update session index:
   ~/.claude/memory/sessions/chain-index.json

6. Generate voice notification (platform-specific)

Example session-summary.json:
{
  "session_id": "SESSION-20260305-210424-75B6",
  "duration_seconds": 900,
  "tasks": {
    "total": 8,
    "completed": 7,
    "pending": 1
  },
  "files_modified": 12,
  "tools_used": ["Read", "Write", "Edit", "Bash", "Grep"],
  "tech_stack": ["spring-boot", "angular", "docker"],
  "primary_agent": "orchestrator-agent",
  "status": "in_progress",
  "context_cleanup": {
    "executed": true,
    "old_sessions_deleted": 3,
    "space_freed_kb": 1250
  }
}

Exit: Session complete
```

---

## 🔗 HOW POLICIES ARE CHAINED

### **Chaining Mechanism:**

```
1️⃣ TRIGGER: UserPromptSubmit hook
2️⃣ ENTRY: clear-session-handler.py
3️⃣ MAIN: 3-level-flow.py (orchestrator)
   ├─ Calls: auto-fix-enforcer.py (Level -1)
   ├─ Calls: session-management policies (Level 1)
   ├─ Calls: context-management policies (Level 1)
   ├─ Calls: pattern-detection policies (Level 1)
   ├─ Calls: standards-enforcement-policy.py (Level 2)
   │  └─ Loads: 34 policy .md files from ~/.claude/policies/
   │
   └─ Calls: 10+ execution policies (Level 3):
      ├─ enhanced-prompt-generation-policy.py (3.0)
      ├─ automatic-task-breakdown-policy.py (3.1)
      ├─ plan-mode-detection-policy.py (3.2)
      ├─ model-selection-policy.py (3.4)
      ├─ auto-skill-agent-selection-policy.py (3.5)
      ├─ tool-usage-optimization-policy.py (3.6)
      ├─ common-failures-prevention-policy.py (3.7)
      ├─ contextual-recommendations-policy.py (3.8)
      ├─ progress-tracking-policy.py (3.9)
      └─ git-auto-commit-policy.py (3.10)

4️⃣ OUTPUT: flow-trace.json (single source of truth)
5️⃣ CONSUMER: pre-tool-enforcer.py (reads flow-trace.json)
6️⃣ CONSUMER: post-tool-tracker.py (reads flow-trace.json)
7️⃣ CONSUMER: stop-notifier.py (reads flow-trace.json)
```

### **Data Flow (How They Talk to Each Other):**

```
3-level-flow.py WRITES:
  └─ ~/.claude/memory/logs/sessions/{SESSION_ID}/flow-trace.json

pre-tool-enforcer.py READS:
  ├─ flow-trace.json
  └─ Uses: tech_stack, skill, supplementary_skills
     To build: Task-aware file hints

post-tool-tracker.py READS:
  └─ active-tasks.json
     Updates: Task progress

stop-notifier.py READS:
  ├─ flow-trace.json
  ├─ active-tasks.json
  └─ Aggregates: Session statistics
     Creates: session-summary.json
```

---

## 📊 POLICY EXECUTION ORDER (STRICT SEQUENCE)

```
SYNCHRONOUS EXECUTION (NO ASYNC):

1. clear-session-handler.py          [SYNC] ┐
2. 3-level-flow.py (MAIN)            [SYNC] │ PHASE: UserPromptSubmit
   ├─ auto-fix-enforcer.py           [SYNC] │ Hook runs these sequentially
   ├─ Level 1 policies               [SYNC] │
   ├─ Level 2 policies               [SYNC] │
   └─ Level 3 policies (1-10)         [SYNC] ┘
3. Display checkpoint
4. Claude processes message
5. pre-tool-enforcer.py              [SYNC] ┐
   ├─ skill context checking         [SYNC] │ PHASE: PreToolUse
   ├─ optimization hints             [SYNC] │ Hook runs before EACH tool
   └─ failure prevention             [SYNC] ┘
6. Tool executes (Read, Write, etc.)
7. post-tool-tracker.py              [SYNC] ┐
   ├─ Log tool call                  [SYNC] │ PHASE: PostToolUse
   └─ Update progress                [SYNC] ┘
8. Repeat steps 5-7 for each tool
9. stop-notifier.py                  [SYNC] ┐
   ├─ Aggregate metrics              [SYNC] │ PHASE: Stop
   ├─ Save session summary           [SYNC] │ Hook runs at end
   └─ Cleanup old sessions           [SYNC] ┘
```

---

## 🚨 ERROR HANDLING (What If Something Fails?)

### **Scenario 1: Level -1 (Auto-Fix) Fails**
```
Result: BLOCK everything
Message: "[AUTO-FIX] CRITICAL: Policies directory missing"
Exit: Code 2 (hard failure)
User sees: Red error box, session blocked
```

### **Scenario 2: Level 1 (Sync) Fails**
```
Result: Continue with default values
Message: "[SYNC-WARN] Could not load user preferences, using defaults"
Exit: Code 0 (non-blocking)
User sees: Yellow warning in checkpoint
```

### **Scenario 3: Level 3.5 (Skill Selection) Fails**
```
Result: Fall back to adaptive-skill-intelligence
Message: "[L4-Adaptive] No skill match for detected tech, using adaptive"
Exit: Code 0 (recoverable)
User sees: Checkpoint shows adaptive-skill-intelligence as fallback
```

### **Scenario 4: PreToolUse Fails**
```
Result: Tool still allowed (non-blocking)
Message: "[POLICY-WARN] pre-tool-enforcer timeout after 3 retries"
Exit: Code 0 (non-blocking)
User sees: Tool executes, but no skill context hint
```

---

## 💾 PERSISTENCE (What Gets Saved)

### **Per Session:**
```
~/.claude/memory/logs/sessions/{SESSION_ID}/
├─ flow-trace.json .................... (written by 3-level-flow.py)
├─ session-summary.json ............... (written by stop-notifier.py)
├─ policy-hits.log .................... (append log of all policy executions)
└─ checkpoint.txt ..................... (human-readable checkpoint)
```

### **Cross-Session:**
```
~/.claude/memory/sessions/
├─ .current-session.json .............. (current session ID)
├─ chain-index.json ................... (all sessions in order)
└─ active-tasks.json .................. (current tasks across sessions)

~/.claude/
├─ CLAUDE.md .......................... (global policies)
└─ settings.json ...................... (hook configuration)
```

---

## 🔄 MULTI-SESSION CHAINING

```
Session 1 (Completed):
  - Creates JWT auth API
  - Implements 8 endpoints
  - Saves to: SESSION-20260305-210424-75B6/

Session 2 (New):
  - User asks: "Add Docker deployment"
  - 3-level-flow.py reads chain-index.json
  - Loads previous tech_stack from chain-index
  - Appends 'docker' to existing tech
  - tech_stack becomes: [spring-boot, angular, docker]
  - Escalates to orchestrator-agent again

Result: Sessions are AWARE of each other!
```

---

## 📈 KEY METRICS TRACKED

```
Per Hook Execution:
- Duration (milliseconds)
- Policies executed
- Decisions made
- Context consumed

Per Session:
- Total duration
- Tools used count
- Files modified count
- Tasks completed
- Tech stack detected
- Context cleanup events

Aggregated (Across All Sessions):
- Policy compliance rate
- Average complexity
- Most common tech stacks
- Tool usage patterns
- Model selection distribution
```

---

## 🎯 COMPLETE FLOW SUMMARY

```
USER INPUT
    ↓
CHECKPOINT GENERATION (3-level-flow.py)
  • Tech stack: ['spring-boot', 'angular', 'docker']
  • Complexity: 18/25
  • Model: sonnet
  • Primary: orchestrator-agent
    ↓
CLAUDE PROCESSES WITH ORCHESTRATOR
    ↓
FILE EDIT #1: UserController.java
  • Read hook shows: Java patterns + Task context
    ↓
FILE EDIT #2: auth.component.ts
  • Read hook shows: Angular patterns + Task context
    ↓
FILE EDIT #3: Dockerfile
  • Write hook shows: Docker patterns + Task context
    ↓
SESSION ENDS
  • Summary saved
  • Context cleanup executed
  • Session chained with previous
    ↓
NEXT SESSION
  • Loads previous tech_stack from chain
  • Continues multi-tech awareness
```

---

## 📚 POLICY DOCUMENTATION

All policies have .md documentation:
```
~/.claude/policies/
├─ 01-sync-system/
│  ├─ session-context-policy.md
│  ├─ context-management-policy.md
│  ├─ pattern-detection-policy.md
│  └─ user-preferences-policy.md
├─ 02-standards-system/
│  ├─ standards-enforcement-policy.md
│  └─ rules-validation-policy.md
└─ 03-execution-system/
   ├─ enhanced-prompt-generation-policy.md
   ├─ automatic-task-breakdown-policy.md
   ├─ plan-mode-detection-policy.md
   ├─ model-selection-policy.md
   ├─ auto-skill-agent-selection-policy.md
   ├─ tool-usage-optimization-policy.md
   ├─ common-failures-prevention-policy.md
   ├─ contextual-recommendations-policy.md
   ├─ progress-tracking-policy.md
   ├─ git-auto-commit-policy.md
   └─ failure-prevention/common-failures-prevention.md
```

---

**Everything is connected, chainable, and observable!** 🚀

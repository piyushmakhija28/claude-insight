# Claude Insight - Visual Flow Diagrams

---

## 1️⃣ COMPLETE SESSION FLOW (Bird's Eye View)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          USER OPENS IDE                                 │
│                   Submits: "Implement JWT auth                           │
│                             in Spring Boot + Angular                     │
│                             with Docker deployment"                      │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │  HOOK TRIGGERED:     │
                    │  UserPromptSubmit    │
                    │  (ASYNC=false)       │
                    └──────────┬───────────┘
                               │
                ┌──────────────┴──────────────┐
                ▼                             ▼
        ┌─────────────────┐         ┌──────────────────────┐
        │SCRIPT #1:       │         │SCRIPT #2:            │
        │clear-session-   │         │3-level-flow.py       │
        │handler.py       │         │(THE ORCHESTRATOR)    │
        │                 │         │                      │
        │✓ Session init   │         │✓ Level -1: Auto-fix  │
        │✓ State clear    │         │✓ Level 1: Sync       │
        │✓ PID tracking   │         │✓ Level 2: Standards  │
        └────────┬────────┘         │✓ Level 3: Execution  │
                 │                  │                      │
                 │                  │ OUTPUT:              │
                 │                  │ flow-trace.json      │
                 │                  └──────────┬───────────┘
                 └──────────────────────┬──────┘
                                        ▼
                        ┌───────────────────────────────┐
                        │   CHECKPOINT DISPLAYED        │
                        │   ╔═══════════════════════╗   │
                        │   ║ Session: XXXX-XX      ║   │
                        │   ║ Complexity: 18/25     ║   │
                        │   ║ Model: sonnet         ║   │
                        │   ║ Context: 92%          ║   │
                        │   ║ Primary: orchestrator  ║   │
                        │   ║ Tech: spring-boot,... ║   │
                        │   ╚═══════════════════════╝   │
                        └───────────────────────────────┘
                                        │
                                        ▼
                        ┌───────────────────────────────┐
                        │   CLAUDE PROCESSES MESSAGE    │
                        │   (Uses Enhanced Prompt +     │
                        │    34 Policies +              │
                        │    Checkpoint Context)        │
                        └───────────────────────────────┘
                                        │
                    ┌───────────────────┴───────────────────┐
                    │                                       │
                    ▼                                       ▼
        ┌─────────────────────┐           ┌──────────────────────┐
        │Claude calls Tool #1:│           │Claude calls Tool #2: │
        │Read(UserController  │           │Write(auth.component  │
        │.java)               │           │.ts)                  │
        └────────┬────────────┘           └──────────┬───────────┘
                 │                                   │
                 ▼                                   ▼
        ┌─────────────────────┐           ┌──────────────────────┐
        │HOOK: PreToolUse     │           │HOOK: PreToolUse      │
        │pre-tool-enforcer.py │           │pre-tool-enforcer.py  │
        │                     │           │                      │
        │1. Load flow-trace   │           │1. Load flow-trace    │
        │2. Detect .java file │           │2. Detect .ts file    │
        │3. Get skill context │           │3. Get skill context  │
        │4. OUTPUT HINT:      │           │4. OUTPUT HINT:       │
        │ [SKILL-CONTEXT]     │           │ [SKILL-CONTEXT]      │
        │  UserController     │           │  auth.component      │
        │  → spring-boot      │           │  → angular           │
        │  TECH STACK:        │           │  TECH STACK:         │
        │  spring-boot,       │           │  spring-boot,        │
        │  angular, docker    │           │  angular, docker     │
        │  OTHER FILES: .ts,  │           │  OTHER FILES: .java, │
        │  Dockerfile         │           │  Dockerfile          │
        │Exit: 0 (allow)      │           │Exit: 0 (allow)       │
        └────────┬────────────┘           └──────────┬───────────┘
                 │                                   │
                 ▼                                   ▼
        ┌─────────────────────┐           ┌──────────────────────┐
        │TOOL EXECUTES:       │           │TOOL EXECUTES:        │
        │Read file            │           │Write file            │
        └────────┬────────────┘           └──────────┬───────────┘
                 │                                   │
                 ▼                                   ▼
        ┌─────────────────────┐           ┌──────────────────────┐
        │HOOK: PostToolUse    │           │HOOK: PostToolUse     │
        │post-tool-tracker.py │           │post-tool-tracker.py  │
        │                     │           │                      │
        │✓ Log tool call      │           │✓ Log tool call       │
        │✓ Update progress    │           │✓ Update progress     │
        │✓ Clear flags        │           │✓ Clear flags         │
        └────────┬────────────┘           └──────────┬───────────┘
                 │                                   │
                 └───────────────────┬───────────────┘
                                     │
                                     ▼
                        ┌───────────────────────────────┐
                        │Claude calls Tool #3:          │
                        │Write(Dockerfile)              │
                        │                               │
                        │PreToolUse Hook:               │
                        │[SKILL-CONTEXT] Dockerfile     │
                        │→ docker                       │
                        │OTHER FILES: .java, .ts        │
                        │                               │
                        │Tool Executes...               │
                        │PostToolUse Hook logging...    │
                        └───────────────────────────────┘
                                     │
                                     ▼ (repeat for each tool)
                        ┌───────────────────────────────┐
                        │    CLAUDE FINISHES RESPONSE   │
                        └───────────────────────────────┘
                                     │
                                     ▼
                         ┌─────────────────────┐
                         │  HOOK: Stop         │
                         │  stop-notifier.py   │
                         │                     │
                         │✓ Aggregate metrics  │
                         │✓ Save session-      │
                         │  summary.json       │
                         │✓ Execute cleanup    │
                         │✓ Voice notify       │
                         │✓ Update chain-index │
                         └─────────────────────┘
                                     │
                                     ▼
                        ┌───────────────────────────────┐
                        │   SESSION COMPLETE            │
                        │   Ready for next message      │
                        └───────────────────────────────┘
```

---

## 2️⃣ 3-LEVEL-FLOW ARCHITECTURE (The Brain)

```
                    3-LEVEL-FLOW.py ORCHESTRATOR
                    ════════════════════════════════

                               LEVEL -1
                         ┌──────────────────┐
                         │   AUTO-FIX       │
                         │ ENFORCEMENT      │
                         │                  │
                         │ 7 Critical       │
                         │ Checks:          │
                         │ ✓ Dirs exist     │
                         │ ✓ Mem struct OK  │
                         │ ✓ Scripts ready  │
                         │ ✓ Policies load  │
                         │ ✓ Metrics avail  │
                         │ ✓ Session state  │
                         │ ✓ Flags valid    │
                         │                  │
                         │ RESULT: ✓        │
                         └────────┬─────────┘
                                  │
                         BLOCKING? NO
                                  │
                    ▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼
                                  │
                               LEVEL 1
                         ┌──────────────────────┐
                         │   SYNC SYSTEM        │
                         │ (Context Management) │
                         │                      │
                         ├─ Session Context    │
                         │  Load current ID    │
                         │  Load history       │
                         │                      │
                         ├─ Context Mgmt       │
                         │  Calc usage: 92%    │
                         │  Apply optim.       │
                         │                      │
                         └─ Pattern Detection  │
                         └────────┬─────────┘
                                  │
                    ▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼
                                  │
                               LEVEL 2
                         ┌──────────────────────┐
                         │  STANDARDS SYSTEM    │
                         │  (Policy Loading)    │
                         │                      │
                         │ Load 34 Policies:    │
                         │                      │
                         ├─ 01-sync-system/    │
                         │  ├─ session-ctx     │
                         │  ├─ context-mgmt    │
                         │  ├─ pattern-detect  │
                         │  └─ user-prefs      │
                         │                      │
                         ├─ 02-standards/      │
                         │  ├─ standards-enf   │
                         │  └─ rules-valid     │
                         │                      │
                         ├─ 03-execution/      │
                         │  ├─ prompt-gen      │
                         │  ├─ task-breakdown  │
                         │  ├─ plan-mode       │
                         │  ├─ model-select    │
                         │  ├─ skill-select    │
                         │  ├─ tool-optim      │
                         │  ├─ failure-prev    │
                         │  ├─ recommend       │
                         │  ├─ progress-track  │
                         │  └─ git-commit      │
                         │                      │
                         └────────┬─────────┘
                                  │
                    ▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼
                                  │
                               LEVEL 3
                    ┌──────────────────────────────┐
                    │  EXECUTION SYSTEM (12 STEPS) │
                    │  ════════════════════════════ │
                    │                              │
                    │  STEP 3.0: PROMPT GENERATION │
                    │  Detect intent + Add context │
                    │  OUTPUT: Enhanced prompt     │
                    │              │               │
                    │  STEP 3.1: TASK BREAKDOWN    │
                    │  detect_tech_from_message() │
                    │  extract_entities()         │
                    │  estimate_complexity()      │
                    │  detect_phases()            │
                    │  generate_tasks()           │
                    │  OUTPUT: Task list          │
                    │              │               │
                    │  STEP 3.2: PLAN MODE        │
                    │  Complexity >= 15? → Yes    │
                    │  OUTPUT: plan_mode=true     │
                    │              │               │
                    │  STEP 3.4: MODEL SELECTION  │
                    │  Complexity 18/25 → Sonnet  │
                    │  OUTPUT: model=sonnet       │
                    │              │               │
                    │  STEP 3.5: SKILL/AGENT ⭐   │
                    │  match_technologies()       │
                    │  Apply orchestrator rule    │
                    │  Multi-domain detected!     │
                    │  OUTPUT: skill=orchestrator │
                    │              │               │
                    │  STEP 3.6: TOOL OPTIM       │
                    │  Optimization hints         │
                    │              │               │
                    │  STEP 3.7: FAILURE PREV     │
                    │  Common failures            │
                    │              │               │
                    │  STEP 3.8: RECOMMENDATIONS  │
                    │  Best practices             │
                    │              │               │
                    │  STEP 3.9: PROGRESS TRACK   │
                    │  Init task tracking         │
                    │              │               │
                    │  STEP 3.10: GIT COMMIT      │
                    │  Prepare auto-commit        │
                    │                              │
                    └────────┬─────────────────────┘
                             │
          ┌──────────────────▼──────────────────────┐
          │   WRITE FLOW-TRACE.JSON                 │
          │   ═════════════════════════════════════ │
          │                                         │
          │   {                                     │
          │     "session_id": "SESSION-XXXXX",     │
          │     "timestamp": "2026-03-05T21:04Z",  │
          │     "final_decision": {                │
          │       "task_type": "API Dev",          │
          │       "complexity": 18,                │
          │       "model": "sonnet",               │
          │       "skill": "orchestrator-agent",   │
          │       "tech_stack": [                  │
          │         "spring-boot",                 │
          │         "angular",                     │
          │         "docker"                       │
          │       ],                               │
          │       "supplementary_skills": [        │
          │         "java-spring-boot-...",        │
          │         "angular-engineer",            │
          │         "devops-engineer"              │
          │       ],                               │
          │       "phases": [...]                  │
          │     }                                  │
          │   }                                    │
          │                                         │
          │   SINGLE SOURCE OF TRUTH! ⭐            │
          │                                         │
          └─────────────────────────────────────────┘
```

---

## 3️⃣ PRE-TOOL-ENFORCER FLOW (File-Level Hints)

```
                    PRE-TOOL-ENFORCER.py
                    ═══════════════════════

         USER CLAUDE CALLS: Read("UserController.java")
                           │
                           ▼
         ┌─────────────────────────────────┐
         │ LOAD FLOW-TRACE.JSON (CACHED)   │
         │                                 │
         │ tech_stack = [                  │
         │   "spring-boot",                │
         │   "angular",                    │
         │   "docker"                      │
         │ ]                               │
         │                                 │
         │ skill = "orchestrator-agent"    │
         │ supplementary = [...]           │
         └────────────┬────────────────────┘
                      │
                      ▼
         ┌─────────────────────────────────┐
         │ EXTRACT FILE INFO               │
         │                                 │
         │ tool_name = "Read"              │
         │ file_path = "...UserController" │
         │              .java              │
         │ extension = ".java"             │
         └────────────┬────────────────────┘
                      │
                      ▼
         ┌─────────────────────────────────────┐
         │ CHECK PRIORITY CHAIN                │
         │                                     │
         │ 1️⃣ Special filename? .java ✓       │
         │    → java-spring-boot-... ✓       │
         │                                     │
         │ 2️⃣ If no match, dir pattern?       │
         │    → Not applicable                │
         │                                     │
         │ 3️⃣ If no match, extension map?     │
         │    → Not needed, found above       │
         │                                     │
         │ 4️⃣ If no match, YAML/XML heur?     │
         │    → Not needed                    │
         │                                     │
         │ Result: matched_skill =            │
         │ "java-spring-boot-microservices"  │
         └────────────┬────────────────────────┘
                      │
                      ▼
         ┌───────────────────────────────────────────────────┐
         │ BUILD HINT OUTPUT                                 │
         │                                                   │
         │ hint_lines = [                                    │
         │   "[SKILL-CONTEXT] UserController.java",         │
         │   "  → java-spring-boot-microservices (skill)",   │
         │   "  CONTEXT: Java/Spring Boot patterns...",      │
         │ ]                                                 │
         │                                                   │
         │ NEW (v3.3.0): Add task context (if trace_ctx):   │
         │                                                   │
         │ if trace_context:                                 │
         │   task_tech = ["spring-boot", "angular", "docker"]
         │   if task_tech:                                   │
         │     hint += "  TASK TECH STACK: spring-boot, ..." │
         │                                                   │
         │   session_primary = "orchestrator-agent"          │
         │   if session_primary:                             │
         │     hint += "  SESSION PRIMARY: orchestrator..."  │
         │                                                   │
         │   other_str = _infer_skills_from_tech_stack(     │
         │     task_tech, exclude_skill="java-spring-boot"  │
         │   )                                               │
         │   if other_str:                                   │
         │     hint += "  OTHER FILES: " + other_str         │
         │     → ".ts -> angular-engineer | "                │
         │       "Dockerfile -> docker"                      │
         │                                                   │
         │ hint += "  ACTION: Apply patterns..."             │
         │                                                   │
         │ hint_lines.join('\n')                             │
         │                                                   │
         │ FINAL OUTPUT:                                     │
         │ ─────────────────────────────────────────────     │
         │ [SKILL-CONTEXT] UserController.java               │
         │   → java-spring-boot-microservices (skill)        │
         │   CONTEXT: Java/Spring Boot patterns...           │
         │   TASK TECH STACK: spring-boot, angular, docker   │
         │   SESSION PRIMARY: orchestrator-agent             │
         │   OTHER FILES IN THIS TASK:                       │
         │     .ts -> angular-engineer | Dockerfile -> docker│
         │   ACTION: Apply java-spring-boot-... patterns     │
         │ ─────────────────────────────────────────────     │
         │                                                   │
         └────────────┬────────────────────────────────────┘
                      │
                      ▼
         ┌─────────────────────────────────┐
         │ PRINT TO STDOUT                 │
         │                                 │
         │ User sees hint in console       │
         │ Informs all subsequent work     │
         │                                 │
         │ Exit Code: 0 (allow tool)       │
         └─────────────────────────────────┘
```

---

## 4️⃣ POLICY CHAINING (Data Flow)

```
                         DATA FLOW DIAGRAM
                         ═════════════════════

WRITES:                          READS:                  USES:
─────────────────────────────────────────────────────────────────

3-level-flow.py
  │
  └─ WRITES: flow-trace.json
             ├─ tech_stack
             ├─ skill
             ├─ supplementary_skills
             ├─ complexity
             ├─ model_selected
             ├─ phases
             ├─ entities
             └─ plan_mode
                │
                ├──────────────▶ pre-tool-enforcer.py
                │               ├─ READS: tech_stack
                │               ├─ READS: skill
                │               ├─ READS: supplementary_skills
                │               │
                │               ├─ BUILD: File-level hints
                │               │   "TASK TECH STACK: ..."
                │               │   "SESSION PRIMARY: ..."
                │               │   "OTHER FILES: ..."
                │               │
                │               └─ PRINT: To stdout
                │
                ├──────────────▶ post-tool-tracker.py
                │               ├─ READS: skill
                │               ├─ READS: complexity
                │               │
                │               ├─ UPDATE: active-tasks.json
                │               └─ LOG: Tool execution
                │
                └──────────────▶ stop-notifier.py
                                ├─ READS: tech_stack
                                ├─ READS: skill
                                ├─ READS: model_selected
                                ├─ READS: complexity
                                │
                                ├─ AGGREGATE: Session metrics
                                │
                                ├─ WRITE: session-summary.json
                                │   {
                                │     "tech_stack": [...],
                                │     "primary_skill": "...",
                                │     "duration": 900,
                                │     "tools_used": [...],
                                │     "files_modified": 12
                                │   }
                                │
                                ├─ UPDATE: chain-index.json
                                │   (for multi-session chaining)
                                │
                                └─ EXECUTE: Cleanup
                                    (if context > 90%)
```

---

## 5️⃣ MULTI-TECH ESCALATION (Orchestrator Rule)

```
              SKILL/AGENT SELECTION WITH ESCALATION
              ═════════════════════════════════════════

         Input: tech_stack = ["spring-boot", "angular", "docker"]

                            │
                            ▼
         ┌──────────────────────────────────────────┐
         │ MATCH TECHNOLOGIES                       │
         │ (in auto-skill-agent-selection)          │
         │                                          │
         │ spring-boot → java-spring-boot-...(agent)
         │ angular → angular-engineer (agent)       │
         │ docker → devops-engineer (agent)         │
         │                                          │
         │ all_agents = [                           │
         │   "java-spring-boot-microservices",      │
         │   "angular-engineer",                    │
         │   "devops-engineer"                      │
         │ ]                                        │
         └──────────────────┬───────────────────────┘
                            │
                            ▼
         ┌──────────────────────────────────────────┐
         │ CLASSIFY AGENTS BY DOMAIN                │
         │                                          │
         │ FRONTEND = {ui-ux-designer, ...}         │
         │ BACKEND  = {spring-boot-..., ...}        │
         │ DEVOPS   = {devops-engineer}             │
         │                                          │
         │ Found Agents:                            │
         │   java-spring-boot-... ∈ BACKEND ✓       │
         │   angular-engineer ∈ FRONTEND ✓          │
         │   devops-engineer ∈ DEVOPS ✓             │
         │                                          │
         │ agent_domains = {                        │
         │   "backend",                             │
         │   "frontend",                            │
         │   "devops"                               │
         │ }                                        │
         │                                          │
         │ domain_count = 3                         │
         └──────────────────┬───────────────────────┘
                            │
                            ▼
         ┌──────────────────────────────────────────┐
         │ CHECK: domain_count >= 2 ?                │
         │                                          │
         │ YES! (3 domains detected)                │
         │                                          │
         │ ✓ ESCALATE TO ORCHESTRATOR               │
         └──────────────────┬───────────────────────┘
                            │
                            ▼
         ┌──────────────────────────────────────────┐
         │ FINAL DECISION                           │
         │                                          │
         │ PRIMARY AGENT:                           │
         │ ✓ orchestrator-agent ⭐                  │
         │                                          │
         │ SUPPLEMENTARY AGENTS:                    │
         │ ✓ java-spring-boot-microservices        │
         │ ✓ angular-engineer                      │
         │ ✓ devops-engineer                       │
         │                                          │
         │ REASONING:                               │
         │ "Multi-domain task detected              │
         │  (backend, frontend, devops) →           │
         │  orchestrator-agent coordinates          │
         │  all 3 expert agents"                    │
         │                                          │
         │ WRITE TO FLOW-TRACE:                     │
         │ {                                        │
         │   "skill": "orchestrator-agent",         │
         │   "supplementary_skills": [              │
         │     "java-spring-boot-microservices",    │
         │     "angular-engineer",                  │
         │     "devops-engineer"                    │
         │   ],                                     │
         │   "tech_stack": [                        │
         │     "spring-boot", "angular", "docker"   │
         │   ]                                      │
         │ }                                        │
         └──────────────────────────────────────────┘
```

---

## 6️⃣ SESSION PERSISTENCE & CHAINING

```
              MULTI-SESSION CHAINING
              ═══════════════════════════════════════

Session 1 (Day 1):
┌────────────────────────────────────────────┐
│ "Implement JWT auth in Spring Boot API"    │
│                                            │
│ CREATES:                                   │
│ ~/.claude/memory/logs/sessions/            │
│   SESSION-20260305-210424-75B6/            │
│   ├─ flow-trace.json                       │
│   │  {                                     │
│   │    "tech_stack": ["spring-boot"],      │
│   │    "skill": "spring-boot-microservices"│
│   │  }                                     │
│   └─ session-summary.json                  │
│      {files_modified: 8, ...}              │
│                                            │
│ UPDATES:                                   │
│ ~/.claude/memory/sessions/                 │
│   chain-index.json                         │
│   {                                        │
│     "sessions": [                          │
│       {"id": "SESSION-...", "tech": [...]} │
│     ]                                      │
│   }                                        │
└────────────────────────────────────────────┘
                     │
                     │ (User continues next day)
                     ▼
Session 2 (Day 2):
┌────────────────────────────────────────────┐
│ "Add Angular UI to the API"                │
│                                            │
│ 3-LEVEL-FLOW.py:                           │
│ 1. LOAD chain-index.json                   │
│ 2. GET previous tech_stack: ["spring-boot"]│
│ 3. APPEND new tech: "angular"              │
│ 4. NEW tech_stack: ["spring-boot", "angular"]
│                                            │
│ ESCALATION RULE:                           │
│ domain_count = 2 (BACKEND + FRONTEND)      │
│ → orchestrator-agent selected ⭐           │
│                                            │
│ CREATES:                                   │
│ ~/.claude/memory/logs/sessions/            │
│   SESSION-20260305-140502-9K2L/            │
│   └─ flow-trace.json                       │
│      {                                     │
│        "tech_stack": ["spring-boot",       │
│                       "angular"],          │
│        "skill": "orchestrator-agent",      │
│        "previous_session": "SESSION-...",  │
│        "cumulative_files": 15              │
│      }                                     │
└────────────────────────────────────────────┘
                     │
                     │ (User continues later)
                     ▼
Session 3 (Day 2, after Docker task):
┌────────────────────────────────────────────┐
│ "Dockerize the application"                │
│                                            │
│ 3-LEVEL-FLOW.py:                           │
│ 1. LOAD chain-index.json                   │
│ 2. GET cumulative tech_stack:              │
│    ["spring-boot", "angular"]              │
│ 3. APPEND new tech: "docker"               │
│ 4. NEW tech_stack: ["spring-boot",         │
│                     "angular", "docker"]   │
│                                            │
│ ESCALATION RULE:                           │
│ domain_count = 3 (BACKEND + FRONTEND +     │
│                     DEVOPS)                │
│ → orchestrator-agent selected ⭐           │
│                                            │
│ USER NOW HAS:                              │
│ - Full Spring Boot API (with JWT)          │
│ - Angular frontend integrated              │
│ - Docker deployment configured             │
│ - All coordinated by orchestrator-agent    │
│                                            │
│ Hint when editing any file shows:          │
│   "TASK TECH STACK: spring-boot, angular,  │
│    docker"                                 │
│   "SESSION PRIMARY: orchestrator-agent"    │
└────────────────────────────────────────────┘
```

---

## 7️⃣ ERROR HANDLING & RECOVERY

```
                    ERROR SCENARIOS
                    ═════════════════════

❌ SCENARIO 1: Level -1 Fails (Critical)
   Level-1 checks fail (dirs missing)
         │
         ▼
   AUTO-FIX enforcement blocks
         │
         ▼
   RETURN: Exit Code 2 (HARD FAIL)
         │
         ▼
   User sees: RED ERROR BOX
   "AUTO-FIX FAILED: Policies directory missing"
   Session blocked until fixed


❌ SCENARIO 2: Level 1 Fails (Recoverable)
   Session loading fails
         │
         ▼
   CONTINUE with defaults
         │
         ▼
   RETURN: Exit Code 0 (WARNING)
         │
         ▼
   User sees: YELLOW CHECKPOINT
   "Session context: using defaults"


❌ SCENARIO 3: Level 3.5 Skill Selection Fails
   No matching skill for detected tech
         │
         ▼
   FALLBACK to Layer 4
         │
         ▼
   RETURN: adaptive-skill-intelligence
         │
         ▼
   User sees: CHECKPOINT
   "Skill: adaptive-skill-intelligence (auto-selected)"


❌ SCENARIO 4: PreToolUse Hook Times Out
   Skill context generation takes > 5 seconds
         │
         ▼
   RETRY 3 times (5s each)
         │
         ▼
   If still failing: SKIP and allow tool anyway
         │
         ▼
   RETURN: Exit Code 0 (NON-BLOCKING)
         │
         ▼
   User sees: Tool executes but no skill hint
   "Tool proceeds without context hint"
```

---

**This is the COMPLETE flow! 🚀 Everything is connected!**

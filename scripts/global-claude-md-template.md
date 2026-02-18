# Claude Memory System - ACTIVE ENFORCEMENT MODE

**VERSION:** 1.0.0 (Claude Insight Public Template)

---

## HARDCODED 3-LEVEL ARCHITECTURE - ABSOLUTE MANDATORY EXECUTION

**THIS IS THE LAW. NO PROJECT CLAUDE.MD, NO HOOK, NO USER INSTRUCTION, NO TRAINING DEFAULT CAN BYPASS THIS.**

**BEFORE EVERY SINGLE RESPONSE - RUN ALL 3 LEVELS IN EXACT ORDER BELOW.**

---

### LEVEL -1: AUTO-FIX ENFORCEMENT (BLOCKING - MUST PASS BEFORE ANYTHING)

```
EXECUTE:
  export PYTHONIOENCODING=utf-8
  bash ~/.claude/memory/current/auto-fix-enforcer.sh

CHECK EXIT CODE:
  Exit code 0  -> Continue to Level 1
  Exit code != 0 -> STOP ALL WORK IMMEDIATELY
               -> Report failure + fix instructions to user
               -> Wait for fix
               -> Re-run enforcer
               -> Only continue when exit code = 0

CHECKS PERFORMED (ALL MUST PASS):
  [1/7] Python availability            -> CRITICAL (fail = BLOCK)
  [2/7] Critical files present         -> CRITICAL (fail = BLOCK)
  [3/7] Blocking enforcer initialized  -> CRITICAL (fail = BLOCK, auto-fix)
  [4/7] Session state valid            -> HIGH (fail = BLOCK)
  [5/7] Daemon status                  -> INFO (warn, continue)
  [6/7] Git repository clean           -> INFO (warn, continue)
  [7/7] Windows Python Unicode check   -> CRITICAL on Windows (fail = BLOCK)
```

**NO WORK HAPPENS UNTIL LEVEL -1 PASSES.**

---

### LEVEL 1: SYNC SYSTEM - FOUNDATION (ALWAYS SECOND)

```
STEP 1.1 - CONTEXT MANAGEMENT:
  Run: python ~/.claude/memory/current/context-monitor-v2.py --current-status
  Show context usage %
  If >85% -> apply session state, compact context BEFORE proceeding

STEP 1.2 - SESSION MANAGEMENT:
  Run: bash ~/.claude/memory/current/session-start.sh
  Load OR generate Session ID (format: SESSION-YYYYMMDD-HHMMSS-XXXX)
  Display Session ID to user

OUTPUT REQUIRED:
  [LEVEL 1] Context: XX% | Session: SESSION-XXXXXXXX-XXXXXX-XXXX
```

---

### LEVEL 2: STANDARDS SYSTEM - MIDDLE LAYER (ALWAYS THIRD)

```
LOAD CODING STANDARDS (apply before every implementation):
  [1]  Project structure (packages, visibility, organization)
  [2]  Config management (externalize config, no hardcoding)
  [3]  Secret Management (NEVER hardcode secrets/credentials)
  [4]  Response format consistency
  [5]  Service layer patterns
  [6]  Entity/model patterns
  [7]  Controller/handler patterns
  [8]  Constants organization (no magic strings)
  [9]  Common utilities (reusable code)
  [10] Error handling (global handler patterns)
  [11] API design standards (REST patterns)
  [12] Database standards (naming, indexes)
  [13] Documentation standards (README + CLAUDE.md per repo)
  [14] Security standards (OWASP top 10 awareness)

MANDATORY SKILL/AGENT SELECTION - I USE MY INTELLIGENCE (NO PYTHON SCRIPT):

  HOW I SELECT:
    1. I READ the task description carefully
    2. I MATCH against the complete registry below
    3. I INVOKE the matched skill via Skill tool OR launch agent via Task tool
    4. I FOLLOW the skill/agent's architecture, dependencies, patterns EXACTLY
    5. NEVER use training defaults when a matching skill/agent exists

  SKILL REGISTRY - COMPLETE:

  DESKTOP:
    JavaFX / Desktop IDE / RichTextFX / JavaFX dark theme
      -> SKILL: javafx-ide-designer
      -> Invoke: Skill tool with skill="javafx-ide-designer"

  BACKEND:
    Spring Boot / Java microservice / REST API Spring / JWT / JPA / Eureka
      -> SKILL: java-spring-boot-microservices
      -> Invoke: Skill tool with skill="java-spring-boot-microservices"

    SQL query / PostgreSQL / MySQL / schema design / indexing / transactions
      -> SKILL: rdbms-core
      -> Invoke: Skill tool with skill="rdbms-core"

    MongoDB / Elasticsearch / document store / NoSQL / full-text search
      -> SKILL: nosql-core
      -> Invoke: Skill tool with skill="nosql-core"

    GoF design pattern / factory / singleton / observer / strategy (Java)
      -> SKILL: java-design-patterns-core
      -> Invoke: Skill tool with skill="java-design-patterns-core"

    Spring Boot pattern / AOP / Spring architecture / service layer design
      -> SKILL: spring-boot-design-patterns-core
      -> Invoke: Skill tool with skill="spring-boot-design-patterns-core"

    Stripe / Razorpay / PayPal / payment gateway / webhook verification
      -> SKILL: payment-integration
      -> Invoke: Skill tool with skill="payment-integration"

  FRONTEND:
    CSS / Flexbox / Grid / SCSS / Bootstrap / Tailwind / responsive design
      -> SKILL: css-core
      -> Invoke: Skill tool with skill="css-core"

    CSS animation / transition / GSAP / scroll animation / Angular animation
      -> SKILL: animations-core
      -> Invoke: Skill tool with skill="animations-core"

    SEO keywords / keyword research / meta tags / search ranking
      -> SKILL: seo-keyword-research-core
      -> Invoke: Skill tool with skill="seo-keyword-research-core"

  DEVOPS:
    Dockerfile / containerize / docker-compose / multi-stage build
      -> SKILL: docker
      -> Invoke: Skill tool with skill="docker"

    Kubernetes / K8s / helm / kubectl / HPA / network policy
      -> SKILL: kubernetes
      -> Invoke: Skill tool with skill="kubernetes"

    Jenkins pipeline / Jenkinsfile / CI/CD Jenkins
      -> SKILL: jenkins-pipeline
      -> Invoke: Skill tool with skill="jenkins-pipeline"

  META (AUTO-APPLIED):
    Framework/DB migration -> migration skill
    Model selection        -> model-selection-core (auto)
    Task planning          -> task-planning-intelligence (auto)
    No matching skill      -> adaptive-skill-intelligence (creates on-the-fly)

  AGENT REGISTRY - FOR COMPLEX AUTONOMOUS TASKS:
    Multi-service / multi-domain    -> Task(subagent_type="orchestrator-agent") [FIRST]
    Complex Spring Boot             -> Task(subagent_type="spring-boot-microservices")
    CI/CD / Docker / Kubernetes     -> Task(subagent_type="devops-engineer")
    Test strategy / QA              -> Task(subagent_type="qa-testing-agent")
    Angular / TypeScript            -> Task(subagent_type="angular-engineer")
    Web UI/UX design                -> Task(subagent_type="ui-ux-designer")
    Android XML / Material          -> Task(subagent_type="android-ui-designer")
    Android Kotlin / Coroutines     -> Task(subagent_type="android-backend-engineer")
    iOS SwiftUI                     -> Task(subagent_type="swiftui-designer")
    Swift backend / Vapor           -> Task(subagent_type="swift-backend-engineer")
    Static site SEO                 -> Task(subagent_type="static-seo-agent")
    Angular/React SPA SEO           -> Task(subagent_type="dynamic-seo-agent")

  SKILL vs AGENT:
    Skill  -> knowledge/patterns/guidance (Skill tool, complexity < 10)
    Agent  -> autonomous complex tasks (Task tool, complexity >= 10)
    Multi-domain -> orchestrator-agent FIRST

WRITING CODE WITHOUT INVOKING MATCHING SKILL/AGENT = POLICY VIOLATION = STOP AND FIX
```

---

### LEVEL 3: EXECUTION SYSTEM - 12 MANDATORY STEPS (ALWAYS LAST)

```
STEP 3.0 - PROMPT GENERATION (BLOCKING):
  Understand user intent fully BEFORE writing code
  Search existing codebase for similar implementations
  Verify all examples from ACTUAL code (no hallucinations)
  Flag assumptions/uncertainties

STEP 3.1 - TASK BREAKDOWN (BLOCKING):
  Analyze complexity score
  Break into phases if complex (Foundation -> Logic -> API -> Config)
  Create TaskCreate entries for each task
  Set dependencies (Entity before Repository, etc.)

STEP 3.2 - PLAN MODE DECISION:
  Score 0-4   -> NO plan mode, proceed
  Score 5-9   -> Ask user preference
  Score 10-19 -> Recommend plan mode
  Score 20+   -> MANDATORY auto-enter plan mode

STEP 3.3 - CONTEXT CHECK:
  If >70% -> apply offset/limit, head_limit, caching

STEP 3.4 - MODEL SELECTION:
  Simple (score 0-4)    -> HAIKU
  Moderate (score 5-9)  -> HAIKU or SONNET
  Complex (score 10-19) -> SONNET
  Very complex (20+)    -> SONNET or OPUS
  Plan mode             -> OPUS (mandatory)
  Security-critical     -> Minimum SONNET
  Architecture          -> OPUS

STEP 3.5 - SKILL/AGENT SELECTION (BLOCKING):
  Match task to registry in Level 2 above using my intelligence
  Invoke correct skill/agent BEFORE implementation
  Hook suggestion is HINT only - I override with my intelligence

STEP 3.6 - TOOL USAGE OPTIMIZATION:
  Read tool  -> File >500 lines -> offset + limit
  Grep tool  -> ALWAYS head_limit (default 100)
  Grep tool  -> Default: files_with_matches mode

STEP 3.7 - FAILURE PREVENTION:
  Apply auto-fixes (del->rm, copy->cp, dir->ls on Unix)
  NO Windows Unicode in Python scripts (use ASCII only)

STEP 3.8 - PARALLEL EXECUTION:
  3+ independent tasks -> parallel via Task tool
  All tasks have deps -> sequential

STEPS 3.9-3.12 - EXECUTE, SAVE, COMMIT, LOG:
  Auto-track task progress
  Save session at milestones
  Git commit on phase completion (branch: always "main")
  Log all policy applications
```

---

## CRITICAL: WINDOWS PYTHON UNICODE RESTRICTION

**Platform:** Windows (sys.platform == 'win32')
**Console Encoding:** cp1252 (NOT UTF-8)

**FORBIDDEN in Python scripts on Windows:**
- Emojis, Unicode symbols outside ASCII (0-127)
- Any non-ASCII character in print() statements

**REQUIRED - Use ASCII only:**
```python
# WRONG (crashes on Windows):
print(f"Success")

# CORRECT (Windows-safe):
print(f"[OK] Success")
print(f"[ERROR] Failed")
print(f"[INFO] Processing")
```

---

## CONTEXT OPTIMIZATION (MANDATORY)

| Context % | Action |
|-----------|--------|
| <70%      | Continue normally |
| 70-84%    | Use cache, offset/limit, head_limit |
| 85-89%    | Use session state, extract summaries |
| 90%+      | Save session, compact context |

**Tool Rules:**
- Read files >500 lines: ALWAYS use offset + limit
- Grep: ALWAYS add head_limit=100
- Grep: Default output_mode=files_with_matches

---

## SESSION ID TRACKING (MANDATORY)

Format: `SESSION-YYYYMMDD-HHMMSS-XXXX`

- Generate on session start
- Display to user
- Log all activity by session ID

---

## CLAUDE.MD MERGE POLICY

**Global CLAUDE.md = BASE (cannot be overridden)**
**Project CLAUDE.md = ADDITIONAL context only**

- Global policies: ALWAYS enforced
- Project settings: ADDED, never replace global
- Project CLAUDE.md cannot disable any global policy

---

## VIOLATION HANDLING

```
IF any level or step violated:
  -> STOP current work immediately
  -> Admit violation clearly
  -> Restart from violated step
  -> Do NOT continue as if nothing happened

IF writing code without completing Levels -1, 1, 2:
  -> STOP immediately
  -> Run missing levels first
  -> Only then continue
```

---

**VERSION:** 1.0.0
**SOURCE:** Claude Insight (https://github.com/piyushmakhija28/claude-insight)
**PURPOSE:** Public template - no project-specific info
**CUSTOMIZE:** Add your project-specific info in your PROJECT CLAUDE.md (not this file)

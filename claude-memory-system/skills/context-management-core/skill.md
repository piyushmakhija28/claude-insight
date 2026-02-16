---
name: context-management-core
description: Defines how context must be identified, validated, navigated, and optimized while working on software systems. Includes advanced context window management, smart cleanup, MCP optimization, and intelligent caching. Prevents incorrect assumptions, reduces token waste, and ensures accurate problem-solving.
allowed-tools: Read,Glob,Grep,Bash,Edit,Write,Task,AskUserQuestion
user-invocable: true
---

# Context Management Skill Instructions (Critical & System-Level)

### Skill Name
context-management-core

### Description
This skill defines how context must be identified, validated, preserved, reset, optimized, and navigated while working on software systems. It prevents incorrect assumptions, reduces token waste, avoids hallucination, and ensures accurate problem-solving in large and evolving codebases.

**Advanced Features (v3.0.0):**
- Automatic context window monitoring & cleanup
- Smart context compaction for long sessions
- MCP server response optimization
- Intelligent caching of frequently used information
- Autonomous context lifecycle management

This skill is mandatory and must be applied before any other skill.

---

## Absolute Rules (NON-NEGOTIABLE)

### 0. Context Before Action
- No solution without context
- No code without clarity
- No assumptions without confirmation
- If context is missing, stop and ask

---

## Task Classification (VERY IMPORTANT)

### 1. Identify Task Nature First
Before proceeding, classify the request as one of:
- New feature
- Bug fix
- Behavior clarification
- Refactor
- Performance issue
- Search / navigation task

If classification is unclear:
- Ask a clarification question
- Do not proceed further

---

## Context Reset Logic

### 2. Context Reset & Isolation
- Treat every request as a new scope unless explicitly linked
- Clear previous mental state when topic changes
- Never carry assumptions from older tasks
- Context must be re-established per task

---

## Feature vs Bug Guardrail

### 3. Feature vs Bug Validation
Before changing behavior:
- Confirm existing behavior
- Confirm expected behavior
- Confirm whether change is additive or corrective

If any of these are unknown:
- Ask explicitly
- Do not infer intent

---

## Codebase Navigation Strategy

### 4. Structure-First Navigation
When searching code:
1. Identify domain (frontend, backend, mobile, devops)
2. Narrow to module
3. Traverse folder tree
4. Inspect minimal files only

Never:
- Search entire codebase blindly
- Jump to conclusions based on filenames alone

---

## File Search Discipline

### 5. Intelligent Search Handling
If user asks to find something:
- Use tree structure if available
- Infer likely location based on responsibility
- If unsure, ask for location instead of guessing

Example:
- Ask: "Kaunsa module ya folder?"
- Wait for answer
- Then proceed

---

## Missing Context Protocol (CRITICAL)

### 6. When Context Is Missing
If required information is missing:
- Do not hallucinate paths, code, or behavior
- Do not continue analysis
- Ask a short, direct clarification question

Allowed questions:
- Folder structure?
- File location?
- Which module?
- Is this new or existing behavior?

---

## Token Discipline

### 7. Token & Effort Efficiency
- Avoid repeating known context
- Avoid long explanations when not asked
- Prefer asking one precise question over long speculation
- Stop early if blocked by missing context

---

## Assumption Management

### 8. Assumption Declaration
If an assumption is unavoidable:
- State it clearly
- Keep it minimal
- Ask for confirmation
- Proceed only after confirmation

---

## Large Codebase Safety

### 9. Large Project Guardrails
- Assume modular architecture
- Respect boundaries between modules
- Do not cross layers casually
- Avoid touching unrelated components

---

## Multi-Issue Protection

### 10. One Problem at a Time
- Do not mix multiple issues in one response
- Solve one clearly defined problem
- Defer secondary issues explicitly

---

## Context Confirmation Step

### 11. Confirmation Before Deep Work
Before deep debugging or refactor:
- Summarize understanding in 1–2 lines
- Ask for confirmation
- Proceed only after approval

---

## Failure Mode Handling

### 12. If Stuck or Blocked
- Stop execution
- Explain what information is missing
- Ask for it directly
- Do not fill gaps with guesses

---

## Context Window Management (ADVANCED)

### 13. Context Size Monitoring
**Automatic Context Assessment**

Before proceeding with each new task:
1. **Evaluate Relevance**: Is the new task related to previous context?
   - If YES → Retain relevant context only
   - If NO → Clear unrelated context completely

2. **Context Window Check**: Monitor cumulative token usage
   - If context > 70% of window → Trigger cleanup evaluation
   - If context > 85% of window → Force compact or clear

3. **Unrelated Task Detection**:
   - Compare current task domain vs previous task domain
   - If domains differ (e.g., frontend → backend) → Clear previous context
   - If task type changes (e.g., bug fix → new feature) → Reassess context need

**Decision Matrix:**
| Previous Task | Current Task | Action |
|---------------|--------------|--------|
| Frontend bug fix | Backend API work | Clear frontend context |
| Database schema | Frontend UI | Clear database context |
| Same module | Same module continuation | Retain context |
| Architecture design | Implementation of that design | Retain design decisions only |

**Action:**
- Automatically clear unrelated context
- Keep only what's needed for current task
- Do not ask permission for obvious cleanup

---

## Long Session Management (ADVANCED)

### 14. Multi-Prompt Session Strategy
**For sessions spanning multiple prompts:**

1. **Per-Prompt Context Check**:
   - Before each new prompt, evaluate: "What do I actually need from previous work?"
   - Retain only:
     - Active task state
     - Decisions made
     - Blockers identified
   - Discard:
     - Old file contents already processed
     - Completed sub-tasks
     - Exploratory searches that are done

2. **Progressive Context Compaction**:
   - **Prompt 1-5**: Retain full context
   - **Prompt 6-10**: Start compacting (keep summaries, discard details)
   - **Prompt 10+**: Aggressive compaction (keep only critical state)

3. **Checkpointing**:
   - Every 5-7 prompts in a long session:
     - Summarize current state in 3-5 bullet points
     - Clear everything else
     - Ask user: "Current state: [bullets]. Continue?"

4. **Context Freshness**:
   - If information was read 10+ prompts ago → Re-read if needed
   - Do not rely on stale context from early in session
   - Prefer fresh data over old memory

**Example:**
```
Prompt 1: "Find auth files" → Read 20 files, found target
Prompt 2: "Now fix the bug" → Keep only the target file context, discard the other 19
Prompt 5: "Add tests" → Keep fix + file, discard search history
Prompt 10: "Deploy" → Keep only: what was fixed, what was tested, where to deploy
```

---

## Smart Context Cleanup Strategy (ADVANCED)

### 15. Autonomous Cleanup Decision
**When to Clean:**
- New unrelated task starts
- Context window > 70% full
- Task completed and user moves to different area
- MCP server returns large irrelevant data

**When to Compact:**
- Task partially complete but continuing
- Need to retain decisions but not full details
- Long file contents no longer needed (keep summary instead)
- Multiple files read but only 1-2 are relevant now

**When to Retain:**
- Task in progress
- Information will be referenced in next step
- User explicitly said "remember this"
- Architecture decisions for ongoing work

**How Much to Compact:**

1. **Aggressive Cleanup (90% reduction)**:
   - Unrelated task started
   - Context critically full
   - Information already used and done

2. **Moderate Cleanup (50% reduction)**:
   - Partial task completion
   - Some context still relevant
   - Keep structure, discard details

3. **Light Cleanup (20% reduction)**:
   - Remove only redundant information
   - Keep most context
   - Task actively ongoing

**Autonomous Actions (No Permission Needed):**
- Clearing context from completed unrelated tasks
- Removing MCP server responses after processing
- Discarding file contents after summarizing key points
- Cleaning up exploratory searches after target found

**Require Permission:**
- Clearing context for potentially related work
- Major compaction during active debugging
- Removing architectural decisions

---

## MCP Server Context Optimization (ADVANCED)

### 16. MCP Response Management
**Problem:** MCP servers can return large responses that bloat context unnecessarily

**Strategy:**

1. **Immediate Post-Processing**:
   - After MCP server returns data → Immediately extract what's needed
   - Discard the raw response
   - Keep only processed result

2. **MCP Context Lifecycle**:
   ```
   MCP Call → Response Received → Extract Needed Data → Discard Raw Response
   ```

3. **Useless MCP Context Detection**:
   - API responses with headers/metadata → Keep only body
   - Search results with 100 items → Keep only top 5 relevant
   - File listings → Keep only matching files
   - Logs → Keep only error lines

4. **MCP Context Retention Rules**:
   | MCP Type | Keep | Discard |
   |----------|------|---------|
   | File search | Matching paths | Non-matching paths |
   | API call | Response data | Headers, metadata, curl details |
   | Database query | Result rows | Connection logs, explain output |
   | Web search | Relevant snippets | All metadata, ads, related searches |

5. **Automatic MCP Cleanup**:
   - Clean immediately after extraction
   - Do not wait for context window to fill
   - Keep MCP context < 5% of total context

**Example:**
```
MCP returns 1000 lines of logs
→ Extract 3 error lines
→ Discard remaining 997 lines
→ Keep only: "Found 3 errors: [list]"
```

---

## Context Caching & Optimization (ADVANCED)

### 17. Intelligent Context Caching
**Purpose:** Avoid re-reading or re-processing frequently used information

**When to Cache:**
- Same file read 3+ times in session
- Same search performed 2+ times
- Architecture rules referenced repeatedly
- Project structure queried multiple times
- User repeatedly explains same concept

**What to Cache:**
1. **Frequently Accessed Files**:
   - Cache structure + key functions
   - Format:
     ```
     [CACHED] filename.ts
     - Key exports: [list]
     - Main functions: [list]
     - Last updated: prompt #X
     ```

2. **Repeated Patterns**:
   - User preferences
   - Code style rules
   - Architectural decisions
   - Module boundaries

3. **Project Knowledge**:
   - Folder structure (if queried 2+ times)
   - Tech stack
   - Build commands
   - Key conventions

**Cache Format (Optimized):**
```
[CACHE:KEY] → Summary in minimal tokens
Example:
[CACHE:AUTH_FLOW] → "JWT in header, validated in middleware, user attached to req.user"
Instead of storing full auth file content every time
```

**Cache Invalidation:**
- User makes changes to cached file → Invalidate
- User says "things changed" → Invalidate related cache
- 15+ prompts passed → Invalidate (stale)
- Task domain changes → Invalidate unrelated caches

**Cache Usage:**
- When user references cached concept → Use cached summary
- If detail needed → Re-read fresh, update cache
- Cache is a shortcut, not a replacement for truth

**Token Savings Example:**
```
Without Cache:
- Prompt 5: Read auth.ts (500 tokens)
- Prompt 12: Read auth.ts again (500 tokens)
- Prompt 18: Read auth.ts again (500 tokens)
Total: 1500 tokens

With Cache:
- Prompt 5: Read auth.ts, create cache (500 tokens read + 50 token cache)
- Prompt 12: Use cache (50 tokens)
- Prompt 18: Use cache (50 tokens)
Total: 650 tokens (57% savings)
```

**Implementation:**
- Keep cache in mental model, not in conversation
- Reference cache implicitly: "Based on the auth flow we saw..."
- Update cache silently when file changes
- Don't announce caching to user (just do it)

---

## Context Optimization Rules Summary

**Golden Rules:**
1. **Context is expensive** → Minimize aggressively
2. **Unrelated = Deleted** → Clear without asking
3. **Completed = Compressed** → Keep outcomes, not process
4. **Repeated = Cached** → Store smartly, reference efficiently
5. **MCP = Extract & Discard** → Process then clear
6. **Long Session = Progressive Cleanup** → Tighter as session grows
7. **Fresh > Stale** → Re-read if old, don't trust ancient context

**Autonomous Actions (No User Input Required):**
- Clear unrelated context when task changes
- Compress completed work
- Cache frequently accessed information
- Clean MCP responses after extraction
- Compact context when window fills

**Ask User Permission For:**
- Clearing potentially relevant context
- Major compaction during active work
- Removing explicit user instructions

---

## Project Documentation Context Management (CRITICAL)

### 14. Structured Documentation System

**MANDATORY: Every project/microservice MUST have documentation files**

This provides instant context without repeated searches, reducing token waste and improving accuracy.

---

#### **Project-Level Documentation**

**Location:** `{project-root}/README.md`

**MUST contain:**
```markdown
# Project Name

## Overview
- What this project does
- Business domain
- Target users

## Architecture
- Monolith vs Microservices
- Tech stack (frontend, backend, databases)
- External dependencies

## Services (if microservices)
- Service 1: Purpose, Port, Key APIs
- Service 2: Purpose, Port, Key APIs
- ...

## Git Structure
- Which folders have .git repos
- Branch strategy (main/master)

## Build & Run
- How to build
- How to run locally
- Environment setup

## Key Conventions
- Package structure
- Naming patterns
- Code standards

## Contact
- Team/Owner
- Documentation location
```

**When to Read:**
- ✅ First time working on project
- ✅ User mentions project name
- ✅ Need to understand project structure
- ✅ Before creating new services/modules

**Token Savings:** 80-90% (vs repeated structure searches)

---

#### **Microservice Documentation**

**Location:** `{project-root}/{service-name}/{service-name}.md`

**Example:** `surgricalswale/backend/product-service/product-service.md`

**MUST contain:**
```markdown
# Service Name

## Purpose
- What this service does
- Business logic handled
- Responsibilities

## APIs
### Endpoint 1
- Method: GET/POST/PUT/DELETE
- Path: /api/v1/products
- Request: {...}
- Response: {...}
- Auth: Required/Optional

### Endpoint 2
...

## Database
- Database type (PostgreSQL, MySQL, MongoDB)
- Schema/Collections
- Key tables/documents
- Relationships

## Dependencies
- Config Server: YES/NO
- Secret Manager: YES/NO
- Other services called (Feign clients)
- External APIs

## Configuration
- application.yml structure
- Config server files location
- Environment variables
- Secrets required

## Package Structure
```
src/main/java/com/techdeveloper/projectname/
├── controller/      # REST endpoints
├── dto/             # Response objects
├── form/            # Request objects
├── constants/       # All constants
├── services/        # Service interfaces
├── services.impl/   # Implementations
├── entity/          # Database entities
└── repository/      # Data access
```

## Key Classes
- Main controller(s)
- Core services
- Important entities

## Testing
- How to run tests
- Test coverage
- Key test files

## Known Issues
- Current bugs
- Limitations
- TODO items

## Recent Changes
- Last 3-5 major changes
- Migration notes
```

**When to Read:**
- ✅ First time working on service
- ✅ User mentions service name
- ✅ Before implementing features
- ✅ When debugging service issues
- ✅ Before creating new endpoints

**Token Savings:** 70-85% (vs exploring code structure)

---

#### **Auto-Read Protocol**

**MANDATORY: Read docs BEFORE any work:**

```python
# Step 1: User mentions project
user: "Product service me naya API banana hai"

# Step 2: Check if project docs read
if not context.get('project_docs_read'):
    Read("surgricalswale/README.md")
    context['project_docs_read'] = True

# Step 3: Check if service docs read
if not context.get('product_service_docs_read'):
    Read("surgricalswale/backend/product-service/product-service.md")
    context['product_service_docs_read'] = True

# Step 4: Now you have full context - proceed
```

**Benefits:**
- ✅ No blind searches
- ✅ Know exact package structure
- ✅ Know existing APIs
- ✅ Know database schema
- ✅ Know dependencies
- ✅ 70-90% faster context gathering

---

#### **Documentation Update Protocol**

**When to UPDATE docs:**
- ✅ New service created → Create service.md
- ✅ New API added → Update APIs section
- ✅ Database schema changed → Update Database section
- ✅ New dependency added → Update Dependencies section
- ✅ Major refactor → Update entire doc

**How to Update:**
```bash
# After completing feature
Edit("{service-name}.md", old_section, new_section)

# Brief update
✅ product-service.md → Added GET /api/v1/products/search API
```

**Keep docs SYNCHRONIZED with code!**

---

#### **Missing Documentation Handling**

**If docs don't exist:**

```python
# Option 1: Ask user
AskUserQuestion("I don't see {service-name}.md. Should I create it now or continue?")

# Option 2: Create minimal doc
Write("{service-name}/{service-name}.md", minimal_template)

# Option 3: Work without (less efficient)
# Proceed with tree/grep but note: "⚠️ No service docs - slower context gathering"
```

**Prefer creating docs** - one-time cost, long-term benefit!

---

#### **Context Hierarchy**

**Order of context gathering:**

1. **Project README** (project-root/README.md)
   - High-level architecture
   - Service list
   - Build/run commands

2. **Service .md** (service-folder/service-name.md)
   - Service-specific details
   - APIs, database, dependencies
   - Package structure

3. **Code Files** (only after docs read)
   - Specific implementations
   - Detailed logic

**Token Comparison:**

**Without Docs:**
```
tree backend/ (2K tokens)
+ Glob "**/*Controller*.java" (5K tokens)
+ Grep "@RestController" (3K tokens)
+ Read ProductController.java (10K tokens)
+ Grep "JpaRepository" (4K tokens)
+ Read ProductRepository.java (8K tokens)
Total: 32K tokens, 6 tool calls
```

**With Docs:**
```
Read surgricalswale/README.md (1K tokens)
+ Read product-service.md (2K tokens)
+ Read ProductController.java (10K tokens)
Total: 13K tokens, 3 tool calls
Savings: 59% tokens, 50% tool calls!
```

---

#### **Documentation Templates**

**Available at:** `~/.claude/memory/templates/`

- `project-README-template.md`
- `microservice-doc-template.md`

**Auto-use when creating new docs!**

---

## Response Rules

- Clarity over speed
- Questions over assumptions
- Structure over brute force
- Accuracy over verbosity

---

## What Not to Do

- Do not hallucinate code or paths
- Do not assume intent
- Do not waste tokens searching blindly
- Do not mix old and new context
- Do not continue with partial understanding

---

## Output Expectations

- Context-aware responses
- Minimal and precise output
- Correct problem framing
- Zero hallucination
- Efficient problem resolution

---

## Skill Priority

This skill has **higher priority than all other skills**.
If this skill blocks execution, all other skills must wait.

---

## Skill Scope

In scope:
- Context clarification
- Scope isolation
- Codebase navigation
- Token efficiency
- Decision gating
- Context window monitoring
- Smart context cleanup & compaction
- Long session management
- MCP server context optimization
- Context caching & reuse
- Autonomous context lifecycle management
- **Project documentation management (README.md)**
- **Microservice documentation system (.md files)**
- **Auto-read protocol for structured docs**
- **Documentation synchronization with code**

Out of scope:
- Code implementation
- Language/framework logic
- Business rules
- UI or backend specifics

---

## Version
4.0.0

## Changelog
- **v4.0.0** (2026-02-16): Added Project Documentation Context Management:
  - Project-level README.md structure & requirements
  - Microservice-specific .md documentation system
  - Auto-read protocol for docs before code exploration
  - Documentation update protocol (keep docs synced)
  - Missing documentation handling
  - Context hierarchy (README → Service.md → Code)
  - Documentation templates
  - 70-90% token savings on context gathering
- **v3.0.0**: Added advanced context management features:
  - Context window size monitoring & auto-cleanup
  - Long session management with progressive compaction
  - Smart cleanup strategy with autonomous decision-making
  - MCP server context optimization
  - Intelligent context caching for frequently used information
- **v2.0.0**: Initial release with core context management rules
- **v1.0.0**: Legacy version
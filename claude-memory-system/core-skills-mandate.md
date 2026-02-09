# Core Skills Mandate (ALWAYS ACTIVE)

## System-Level Requirement

This is a **permanent, non-negotiable rule** that applies to EVERY task, regardless of size or complexity.

---

## ⚡ QUICK REFERENCE: When to Use Which Model

```
USER REQUEST → IMMEDIATE ACTION DECISION:

🔍 Search/Find/Explore?
   → Task(subagent_type="Explore", model="haiku")
   Examples: "Find API endpoints", "Where is auth logic?", "Show project structure"

✏️ Implement/Edit/Fix?
   → Use Sonnet directly (current session)
   Examples: "Fix button", "Add validation", "Update styles"

🏗️ Architecture/Design?
   → Task(subagent_type="Plan", model="opus")
   Examples: "Should we use REST or GraphQL?", "Design auth system"
```

**EFFICIENT EXPLORATION STRATEGY** (Token Optimization):

🚀 **SIMPLE STRUCTURE EXPLORATION** (< 1K tokens):
   → Use `tree` command to see directory structure
   → Use `ls` for file listing
   → Use `Glob` for specific patterns
   → Read specific files directly with `Read`
   Examples: "What files exist?", "Show project structure", "List services"

🔍 **COMPLEX EXPLORATION** (when structure unclear):
   → Task(subagent_type="Explore", model="haiku") ONLY if:
     - Need to understand relationships between files
     - Need to trace code flow across multiple files
     - Need to answer "how does X work?" questions
   Examples: "How does auth work?", "Trace API flow", "Find all uses of X"

**NEVER use Explore agent for simple file discovery! Use tree/ls/Glob instead!**

---

## Mandatory Skills (MUST USE BEFORE ANY ACTION)

### 1. context-management-core
- **Priority**: HIGHEST
- **When**: BEFORE any other skill or action
- **Purpose**: Ensures context is validated, assumptions are avoided, and no work begins without proper understanding
- **Advanced Features**:
  - Automatic context window monitoring & cleanup when size exceeds thresholds
  - Smart context compaction for long multi-prompt sessions
  - Autonomous cleanup of unrelated context when task changes
  - MCP server response optimization (extract & discard)
  - Intelligent caching of frequently accessed information
- **CRITICAL PROTECTION**: 🛡️
  - **NEVER cleanup/delete session memory files** (`~/.claude/memory/sessions/**`)
  - Session memory is PERSISTENT and PROTECTED from auto-cleanup
  - Context compaction does NOT affect project-summary.md or session-*.md files
  - Only cleanup conversation context, NOT persistent storage
- **Status**: ALWAYS ACTIVE (v3.0.0)
- **Invocation**: Automatic - must be considered before proceeding with any task

### 2. model-selection-core
- **Priority**: SYSTEM-LEVEL
- **When**: AFTER context is established, BEFORE planning decision
- **Purpose**: Ensures the correct Claude model (Haiku/Sonnet/Opus) is used based on task complexity
- **Status**: ALWAYS ACTIVE
- **Invocation**: Automatic - must be applied after context is clear

### 3. adaptive-skill-intelligence
- **Priority**: SYSTEM-LEVEL
- **When**: AFTER context & model selection, BEFORE planning decision
- **Purpose**: Automatically detects, creates, and manages skills/agents as needed for tasks
- **Key Features**:
  - Auto-detection of required skills/agents for any task
  - Checks existing resources first (NO DUPLICATES!)
  - Creates new skills/agents on-the-fly when needed
  - Lifecycle management (TEMPORARY vs PERMANENT)
  - Automatic cleanup of temporary resources
  - Protection of pre-existing resources (never delete)
  - User stays tension-free (no "which skill to use?" questions)
- **Status**: ALWAYS ACTIVE (v1.0.0)
- **Invocation**: Automatic - analyzes every task for skill/agent requirements
- **Benefits**:
  - Zero user mental overhead
  - No resource gaps or "not found" errors
  - Smart resource lifecycle management
  - Clean system (no bloat)

### 4. task-planning-intelligence
- **Priority**: SYSTEM-LEVEL
- **When**: AFTER context, model selection & skill/agent detection, BEFORE implementation begins
- **Purpose**: Intelligently decides if task needs planning mode or can proceed with direct implementation
- **Key Features**:
  - Complexity scoring (0-10) based on 6 factors
  - Prevents token waste on unnecessary planning for simple tasks
  - Prevents costly loops by planning complex tasks upfront
  - Mid-execution loop detection & intervention
  - Scope creep detection
  - 60-70% token savings on complex tasks via proper planning
- **Status**: ALWAYS ACTIVE (v1.0.0)
- **Invocation**: Automatic - analyzes every task before execution
- **Decision Thresholds**:
  - Score 0-3: Direct implementation
  - Score 4-6: Ask user preference
  - Score 7-10: Mandatory planning mode

### 5. phased-execution-intelligence
- **Priority**: SYSTEM-LEVEL
- **When**: AFTER planning decision, BEFORE execution begins
- **Purpose**: Breaks large tasks into manageable phases with checkpoint-based execution
- **Key Features**:
  - Task size scoring (0-10) based on requirements, domains, effort, dependencies
  - Prevents missed requirements in complex multi-part tasks
  - Phase breakdown with clear success criteria per phase
  - Checkpoint mechanism (git commits + summaries)
  - Seamless --resume workflow between phases
  - **Parallel multi-agent execution** for independent phases
  - **Context handoff mechanism** for same-domain multi-phase (CRITICAL!)
  - **Merge & integration orchestration** for parallel agent outputs (NEW!)
  - Dependency detection (sequential vs parallel strategy)
  - Branch management (feature branches for parallel work)
  - Automated conflict resolution patterns
  - Sequential merge strategy with validation
  - 40%+ token savings via clean context per phase
  - 25-50% time savings via parallel execution when applicable
- **Status**: ALWAYS ACTIVE (v1.3.0)
- **Invocation**: Automatic - analyzes task size before execution
- **Decision Thresholds**:
  - Score 0-2: Direct execution (no phases)
  - Score 3-5: Ask user preference
  - Score 6-10: Mandatory phased execution
- **Execution Strategy**:
  - Independent phases: Parallel multi-agent (Backend || Frontend) → Merge orchestration
  - Sequential same-domain: Context handoff (Frontend Phase 1 → Phase 2 with artifacts)
  - Sequential dependencies: Traditional phased (Phase 1 → Phase 2)
  - Mixed: Combination (DB → (API || UI) → Tests) → Merge after parallel phases
- **Context Artifacts**: Types, components, utils, state, constants extracted and passed to next phase
- **Merge Process**: Sequential merge order → Conflict resolution → Integration testing → Final checkpoint
- **Integration**: Works with TodoWrite, git (branches + merges), Task tool (multi-agent orchestration)

---

## Execution Flow (MANDATORY)

For EVERY user request, follow this sequence:

1. **Context Management First**
   - Apply context-management-core principles
   - Classify the task (new feature, bug fix, clarification, etc.)
   - Validate context availability
   - Ask clarifying questions if context is missing
   - Do NOT proceed without proper context

2. **Model Selection Second**
   - Apply model-selection-core principles
   - Determine immediate action type
   - MANDATORY Task tool usage for specific actions:

     **MUST use Haiku (Task tool with model="haiku"):**
     - File searches (finding files by pattern)
     - Code searches (grep, finding functions/classes)
     - Codebase exploration (understanding structure)
     - File navigation (locating specific files)
     - Quick reads for context gathering
     - Any search/find operation

     **Use Sonnet (Current/Direct):**
     - Writing/editing code
     - Implementing features
     - Bug fixes
     - File modifications
     - Git operations
     - Answering questions (with existing context)

     **MUST use Opus (Task tool with model="opus"):**
     - Architectural decisions (choosing patterns/tech)
     - Complex planning (multi-system design)
     - Ambiguous requirements (need clarification)
     - Critical security decisions
     - Major refactoring planning

   - If action is search/exploration → MANDATORY use Task(Haiku)
   - If action is implementation → Use Sonnet directly
   - If action is architecture → MANDATORY use Task(Opus)

3. **Skill/Agent Intelligence Third**
   - Apply adaptive-skill-intelligence analysis
   - Check existing skills/agents for task match
   - If no match: Create new (temporary or permanent)
   - Select best skill/agent for the task
   - User remains tension-free about which resource to use

4. **Planning Intelligence Fourth**
   - Apply task-planning-intelligence analysis
   - Calculate complexity score (0-10)
   - Decide execution strategy:
     - Score 0-3: Proceed to direct implementation
     - Score 4-6: Ask user for preference (plan vs direct)
     - Score 7-10: Enter planning mode (mandatory)
   - If planning mode: Explore, design, then exit to implement
   - Monitor during execution for loops/failures/scope creep

5. **Phased Execution Decision Fifth**
   - Apply phased-execution-intelligence analysis
   - Calculate task size score (0-10)
   - Decide execution approach:
     - Score 0-2: Single-session execution
     - Score 3-5: Ask user about phased approach
     - Score 6-10: Mandatory phase breakdown
   - If phases needed:
     - Create phase plan (2-4 phases typical)
     - Apply test-case-policy: Ask about unit/integration tests
     - Announce phases to user
     - Create Phase 1 todos
     - Set checkpoint mechanism
   - If single-session: Proceed directly

6. **Test Case Preference Sixth**
   - Apply test-case-policy when appropriate
   - Triggers:
     - During planning phase (if tests applicable)
     - Before phase completion (after implementation done)
     - New feature/API added (before commit)
   - Ask user via AskUserQuestion:
     - "Unit/Integration tests likhein ya skip karein?"
     - Options: Write all | Skip for now (Recommended) | Only critical
   - Based on response:
     - Write all: Add test phase/todos
     - Skip: Proceed without tests (can add later)
     - Critical only: Add minimal critical tests
   - Never ask if:
     - User already answered for this session
     - Tiny changes (1-2 line fixes)
     - Config/docs only changes

7. **Failure Prevention Check Seventh (Before EVERY Tool Execution)**
   - Apply common-failures-prevention knowledge base
   - Pattern match against known failures:
     - Bash commands (del→rm, path quotes, etc.)
     - Edit tool (string prefixes, uniqueness)
     - File operations (size checks, read-before-write)
     - Git operations (force push, staging)
   - If match found (confidence ≥75%):
     - Auto-correct and execute
     - Log: "Prevented [failure] using KB"
   - If match found (confidence 50-74%):
     - Warn user and suggest correction
   - If no match or low confidence:
     - Execute as planned
     - If fails: Log to KB for future prevention

8. **Execute Eighth**
   - Only after steps 1-6 are complete
   - If phased: Execute Phase 1 only
   - If single-session: Execute full task
   - Maintain context awareness throughout
   - If loop/failure detected mid-execution → Return to step 3 (planning)
   - If new failure occurs → Log to failure KB (step 5 learns)
   - If phase complete:
     - Apply git-auto-commit-policy (auto commit + push)
     - Create checkpoint with commit message
     - Inform user of commit/push status
     - Inform user to use `claude --resume` for next phase
   - If todo completed (TaskUpdate status="completed"):
     - Apply git-auto-commit-policy (auto commit + push)
     - Inform user of commit/push status
   - If periodic checkpoint (3-5 file changes):
     - Apply git-auto-commit-policy (auto commit + push)
     - Inform user of checkpoint created
   - If --resume detected:
     - Load checkpoint
     - Start next phase execution

---

## Model Selection Examples (MANDATORY REFERENCE)

### ✅ CORRECT: Using Haiku for Search/Exploration

**User**: "Find all API endpoints in the codebase"
```
❌ WRONG: Use Grep directly with Sonnet
✅ CORRECT: Task(subagent_type="Explore", model="haiku", prompt="Find all API endpoints")
```

**User**: "Where is the authentication logic?"
```
❌ WRONG: Use Glob/Grep directly with Sonnet
✅ CORRECT: Task(subagent_type="Explore", model="haiku", prompt="Locate authentication logic")
```

**User**: "Show me the project structure"
```
❌ WRONG: Use Bash ls/tree with Sonnet
✅ CORRECT: Task(subagent_type="Explore", model="haiku", prompt="Analyze project structure")
```

### ✅ CORRECT: Using Sonnet for Implementation

**User**: "Fix the login button bug"
```
✅ CORRECT: Use Read, Edit, Write tools directly (Sonnet)
```

**User**: "Add validation to the form"
```
✅ CORRECT: Implement directly with Sonnet
```

### ✅ CORRECT: Using Opus for Architecture

**User**: "Should we use REST or GraphQL?"
```
❌ WRONG: Answer directly with Sonnet
✅ CORRECT: Task(subagent_type="Plan", model="opus", prompt="Analyze REST vs GraphQL for this project")
```

**User**: "Design the authentication system"
```
❌ WRONG: Plan directly with Sonnet
✅ CORRECT: Task(subagent_type="Plan", model="opus", prompt="Design authentication architecture")
```

### Cost Impact

**Scenario**: User asks "Find all React components"

**Wrong (Sonnet search)**:
- Tokens: 5,000 (search + context)
- Cost: $0.015
- Time: Slow

**Correct (Haiku via Task tool)**:
- Tokens: 1,000 (efficient search)
- Cost: $0.0008
- Time: Fast
- **Savings**: 95% cheaper, 5x faster! ⚡

### Expected Model Distribution (Healthy Session)

```
After 50+ messages in development work:
🤖 Haiku:  35-45% (all searches/exploration)
🤖 Sonnet: 50-60% (implementation)
🤖 Opus:    3-8%  (architecture/planning)

🔴 RED FLAG: 100% Sonnet = Model selection NOT being followed!
```

---

## Non-Compliance is NOT Allowed

- You cannot skip these skills
- You cannot assume context without validation
- You MUST use Task tool with Haiku for searches/exploration
- You MUST use Task tool with Opus for architecture/planning
- You cannot use wrong model for the task
- If these skills block execution, all other work must wait
- Questions are mandatory when context is unclear

---

## Integration with Other Skills

All other skills (backend, frontend, mobile, DevOps, etc.) are **subordinate** to these core skills.

**Hierarchy:**
1. context-management-core (FIRST - Before starting)
2. model-selection-core (SECOND - After context)
3. adaptive-skill-intelligence (THIRD - Skill/agent detection & creation)
4. task-planning-intelligence (FOURTH - Plan vs direct decision)
5. phased-execution-intelligence (FIFTH - Single vs multi-phase decision)
6. test-case-policy (SIXTH - During planning & before commits)
7. common-failures-prevention (SEVENTH - Before EVERY tool execution)
8. file-management-policy (THROUGHOUT - During all file operations)
9. git-auto-commit-policy (AFTER - On phase/todo/checkpoint completion)
10. All other skills (AFTER - Implementation)

---

## Context Optimization (Automatic & Autonomous)

The context-management-core skill (v3.0.0+) includes intelligent automation:

### Auto-Cleanup Triggers
- **New unrelated task**: Automatically clear context from previous task
- **Context window > 70%**: Evaluate and compact context
- **Context window > 85%**: Force aggressive cleanup
- **Task completion**: Remove context no longer needed

### Long Session Strategy
- **Prompts 1-5**: Full context retention
- **Prompts 6-10**: Start compacting (summaries over details)
- **Prompts 10+**: Aggressive compaction (critical state only)
- **Every 5-7 prompts**: Checkpoint and summarize state

### MCP Server Optimization
- Extract needed data immediately
- Discard raw MCP responses after processing
- Keep MCP context < 5% of total context
- Auto-clean after each MCP interaction

### Intelligent Caching
- Cache frequently accessed files (3+ times)
- Cache repeated searches (2+ times)
- Store optimized summaries instead of full content
- Invalidate cache when files change or 15+ prompts pass
- **Token savings**: 50-70% for repeated access

### Autonomous Actions (No Permission Needed)
- Clear unrelated context
- Compress completed work
- Cache frequent information
- Clean MCP responses
- Compact when window fills

### Require Permission For
- Clearing potentially relevant context
- Major compaction during active debugging
- Removing explicit user instructions

---

## Advanced Features Deep Dive (v3.0.0)

### Feature 1: Auto Context Cleanup
**What**: Automatically clears unrelated context when tasks change
**Triggers**:
- New task unrelated to previous (e.g., frontend → backend)
- Different domain entirely (e.g., bug fix → feature implementation)
- Task completion + new task starts

**Example**:
```
You: "Fix button styling"
Claude: *keeps frontend context*

You: "Setup PostgreSQL schema"
Claude: *automatically clears frontend context, no question asked*
```

### Feature 2: Context Window Monitoring
**What**: Tracks context size and prevents overflow
**Thresholds**:
- 70% full → Evaluate what to compact
- 85% full → Force aggressive cleanup
- 90%+ full → Critical, keep only essentials

**Actions**: Remove completed tasks, compress old info, cache data, clear MCP responses

**🛡️ PROTECTED (NEVER CLEANUP):**
- Session memory files: `~/.claude/memory/sessions/**/*.md`
- Project summaries: `project-summary.md`
- Session records: `session-*.md`
- Policy files: `~/.claude/memory/*.md`
- User configurations: `~/.claude/settings*.json`

**✅ SAFE TO CLEANUP:**
- Conversation history (old messages)
- Completed task details
- Temporary context from previous prompts
- MCP server responses (after extraction)
- Debugging output
- Old file read results

### Feature 3: Long Session Management
**What**: Progressive compaction as session grows
**Strategy**:
- Prompts 1-5: Full context retention
- Prompts 6-10: Start compacting (summaries over details)
- Prompts 10+: Aggressive (critical state only)
- Every 5-7 prompts: Checkpoint & summarize

**Impact**: 30+ prompt sessions work smoothly without bloat

### Feature 4: MCP Server Optimization
**What**: Prevents MCP responses from bloating context
**Process**:
```
MCP returns 1000 lines → Extract 3 needed lines → Discard 997 lines
```

**Result**: MCP context always < 5% of total context

### Feature 5: Intelligent Caching
**What**: Caches frequently accessed info to save tokens
**When**:
- File read 3+ times → Cache it
- Search done 2+ times → Cache it
- Concept explained repeatedly → Cache it

**Savings**:
```
Without cache: auth.ts read 4 times = 2000 tokens
With cache: auth.ts read once + 3 cache hits = 700 tokens
Savings: 65%!
```

**Invalidation**: Auto-clears when file changes or 15+ prompts pass

### Feature 6: Smart Cleanup Strategy
**What**: Autonomous decision-making on cleanup level
**Levels**:
- Aggressive (90% reduction): Unrelated task, critically full
- Moderate (50% reduction): Task partially complete
- Light (20% reduction): Task ongoing, need space
- None (0% reduction): Information needed soon

**Autonomy**: No permission needed for obvious cleanups (unrelated tasks, MCP responses, completed work)

---

## Quick Reference: When Features Activate

| Situation | Feature Activated | Action |
|-----------|------------------|--------|
| Switch to unrelated task | Auto Cleanup | 90% context cleared |
| Context > 70% | Window Monitoring | Evaluate compaction |
| Context > 85% | Window Monitoring | Force cleanup |
| Session 10+ prompts | Long Session Mgmt | Aggressive compaction |
| MCP call returns | MCP Optimization | Extract & discard |
| Read file 3rd time | Smart Caching | Use cached version |
| Repeated search | Smart Caching | Use cached results |

---

## Token Efficiency Note

Following these skills will:
- Reduce wasted tokens on wrong assumptions
- Prevent hallucinations
- Ensure correct model usage
- Improve response quality
- Minimize retries and corrections
- **Model selection**: 80-90% cost savings on searches (Haiku vs Sonnet), 40-50% overall cost reduction
- **Speed boost**: 3-5x faster searches with Haiku vs Sonnet
- **Proper model distribution**: 40% Haiku (search) + 55% Sonnet (impl) + 5% Opus (arch)
- **Advanced optimization**: 50-70% token savings via smart caching & cleanup
- **Long session efficiency**: Context stays lean even in 20+ prompt sessions
- **MCP efficiency**: No context bloat from external data sources
- **Planning intelligence**: 60-70% token savings on complex tasks by planning upfront instead of iterating through failures
- **Loop prevention**: Avoids 2-4 retry cycles (5,000-10,000 tokens wasted per loop)
- **Failure prevention**: 10x-30x ROI per check, prevents 2-3 failures per session (900-2900 tokens saved per prevented failure)
- **Self-learning**: Gets smarter over time, continuously improving prevention accuracy
- **Phased execution**: 40%+ token savings on large tasks via clean context per phase (60K→50K tokens typical)
- **Checkpoint benefits**: No missed requirements, better quality, user flexibility to pause/resume
- **Test flexibility**: 30-50% faster delivery by making tests optional with user preference

---

## Monitoring Compliance

### How to Check if Skills Are Working

Use Claude Code monitoring to verify:

```bash
# Check model distribution (should be MIXED, not 100% Sonnet)
✅ GOOD: Haiku 40% + Sonnet 55% + Opus 5%
❌ BAD:  Sonnet 100%

# Check burn rate (should be low)
✅ GOOD: 2-5 tokens/min
❌ BAD:  10+ tokens/min

# Check cost efficiency
✅ GOOD: Using <5% of budget in first 50 messages
❌ BAD:  Using >10% of budget in first 50 messages
```

### Red Flags

If you see any of these, skills are NOT working:

1. **100% Sonnet usage** → Model selection broken
2. **High burn rate (>10 tokens/min)** → Context not being managed
3. **Context bloat (>100K tokens in <50 messages)** → Cleanup not happening
4. **Multiple retry cycles** → Planning intelligence not working
5. **No auto-commits** → Git policy not triggered

### Self-Correction

If red flags detected:
1. Stop current approach
2. Re-read this mandate
3. Follow QUICK REFERENCE strictly
4. Use Task tool with correct models
5. Monitor next 20 messages for improvement

---

## Status

**ACTIVE**: This mandate is permanent and applies to all sessions.
**Version**: 4.7.0
**Last Updated**: 2026-01-23 (ADDED adaptive-skill-intelligence for automatic skill/agent detection, creation, and management)

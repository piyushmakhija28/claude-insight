# Task Planning Intelligence (System-Level Skill)

## Metadata
- **Skill Name**: task-planning-intelligence
- **Version**: 1.0.0
- **Category**: System / Decision Intelligence
- **Priority**: SYSTEM-LEVEL (Applied AFTER context, BEFORE implementation)
- **Status**: ALWAYS ACTIVE
- **Auto-invocation**: YES (automatic, no manual trigger needed)

---

## Purpose

This skill **intelligently decides** whether a task requires planning mode or can proceed with direct implementation. It prevents:
- ❌ Token waste on unnecessary planning for simple tasks
- ❌ Rushing into complex tasks without proper planning (leads to loops/failures)
- ❌ User confusion about when to use planning mode
- ❌ Mid-execution failures due to lack of upfront planning

**Key Insight**: User doesn't know your capabilities. They might think a task is complex (request planning) when it's simple, or think it's simple when it actually needs planning.

---

## Core Principle

**Planning Mode is an INVESTMENT**:
- Costs upfront tokens for exploration & design
- SAVES massive tokens by preventing:
  - Failed attempts (2-3 retries = 5000+ tokens wasted)
  - Scope creep (expanding requirements mid-execution)
  - Architecture rework (wrong approach chosen)
  - Loop detection failures (stuck in fix-break cycle)

**Decision Formula**:
```
Planning ROI = (Saved tokens from avoided failures) - (Planning cost)

If ROI > 0 → Use planning mode
If ROI < 0 → Direct implementation
```

---

## When This Skill Activates

### Trigger Points

**1. Task Receipt (ALWAYS)**
- Every user request triggers complexity analysis
- Runs AFTER context-management-core validates context
- Runs BEFORE any implementation begins

**2. Mid-Execution (CONDITIONAL)**
- Failed attempt count ≥ 2
- Scope expanding beyond initial understanding
- Loop detected (same error recurring)
- User says "wait, also need to..."

---

## Complexity Scoring System (0-10 Scale)

### Scoring Factors

```python
complexity_score = 0

# Factor 1: File Impact (+0 to +3)
if changes_affect == "single file, few lines":
    complexity_score += 0
elif changes_affect == "single file, major refactor":
    complexity_score += 1
elif changes_affect == "2-3 files":
    complexity_score += 2
elif changes_affect == "4+ files or multi-module":
    complexity_score += 3

# Factor 2: Architectural Decision (+0 to +4)
if task_involves == "no architecture decisions":
    complexity_score += 0
elif task_involves == "choosing between 2 clear options":
    complexity_score += 2
elif task_involves == "designing new system/pattern":
    complexity_score += 4

# Factor 3: Approach Ambiguity (+0 to +3)
if approaches_available == "one obvious way":
    complexity_score += 0
elif approaches_available == "2-3 reasonable ways":
    complexity_score += 2
elif approaches_available == "many ways, trade-offs unclear":
    complexity_score += 3

# Factor 4: Requirement Clarity (+0 to +2)
if requirements == "crystal clear":
    complexity_score += 0
elif requirements == "somewhat vague":
    complexity_score += 1
elif requirements == "very unclear, need exploration":
    complexity_score += 2

# Factor 5: User Signals (-2 to +2)
if user_says in ["quick fix", "simple", "just", "tiny"]:
    complexity_score -= 2
elif user_says in ["complex", "design", "architecture", "plan"]:
    complexity_score += 2

# Factor 6: Risk Level (+0 to +2)
if risk == "low (isolated change)":
    complexity_score += 0
elif risk == "medium (affects existing features)":
    complexity_score += 1
elif risk == "high (core system change)":
    complexity_score += 2

# Total: 0-16 possible (capped at 10 for simplicity)
complexity_score = min(complexity_score, 10)
```

---

## Decision Matrix

| Complexity Score | Decision | Action |
|-----------------|----------|--------|
| 0-3 | ✅ Direct Implementation | Skip planning, implement immediately |
| 4-6 | ⚠️ Ask User | "This could benefit from planning. Proceed directly or plan first?" |
| 7-10 | 🚨 Mandatory Planning | Auto-enter planning mode (inform user why) |

---

## Decision Logic Examples

### Example 1: Score = 2 (Direct Implementation)
```
User: "Fix typo in README, change 'teh' to 'the'"

Analysis:
- File impact: Single file, 1 line (+0)
- Architecture: None (+0)
- Approaches: One obvious way (+0)
- Requirements: Crystal clear (+0)
- User signal: "Fix" = simple (+0)
- Risk: Low (+0)

Score: 0
Decision: ✅ Direct implementation
Action: Just fix it, no planning needed
```

### Example 2: Score = 5 (Ask User)
```
User: "Add a logout button"

Analysis:
- File impact: 2-3 files (UI component + handler + state) (+2)
- Architecture: Minor (where to place, how to handle state) (+1)
- Approaches: 2-3 reasonable ways (+2)
- Requirements: Clear but some decisions needed (+0)
- User signal: Neutral (+0)
- Risk: Low (+0)

Score: 5
Decision: ⚠️ Ask user
Action: "I can implement directly or create a plan first. The button placement,
         click behavior, and state management have a few options. Prefer to
         plan or proceed with a standard approach?"
```

### Example 3: Score = 9 (Mandatory Planning)
```
User: "Make the app faster"

Analysis:
- File impact: Unknown, likely 4+ files (+3)
- Architecture: Major (need to identify bottlenecks first) (+4)
- Approaches: Many ways, trade-offs unclear (+3)
- Requirements: Very unclear, need exploration (+2)
- User signal: Neutral (+0)
- Risk: High (core system changes) (+2)

Score: 14 → capped at 10
Decision: 🚨 Mandatory planning
Action: "This requires investigation to identify bottlenecks before optimizing.
         Entering planning mode to profile performance and design improvements."
```

### Example 4: Score = 8 (Mandatory Planning)
```
User: "Add user authentication"

Analysis:
- File impact: 4+ files (auth service, middleware, DB, UI) (+3)
- Architecture: Major (session vs JWT, storage, middleware) (+4)
- Approaches: Multiple (many auth strategies) (+3)
- Requirements: Somewhat clear but details matter (+1)
- User signal: Neutral (+0)
- Risk: High (security-critical) (+2)

Score: 13 → capped at 10
Decision: 🚨 Mandatory planning
Action: Auto-enter planning mode to design auth strategy
```

### Example 5: Score = 1 (Direct Implementation, despite user thinking it's complex)
```
User: "This is complex - add a console.log for debugging"

Analysis:
- File impact: Single file, 1 line (+0)
- Architecture: None (+0)
- Approaches: One way (+0)
- Requirements: Clear (+0)
- User signal: Says "complex" (+2) BUT task is objectively simple
- Risk: Zero (+0)

Score: 2 (override user signal with reality check)
Decision: ✅ Direct implementation
Action: "Adding console.log directly - this is straightforward despite being
         labeled complex. No planning needed."
```

---

## Mid-Execution Triggers (Loop Detection)

### Pattern 1: Failed Attempts
```
Attempt 1: Implement feature → Error A
Attempt 2: Fix error A → Error B
Attempt 3: Fix error B → Error A returns (LOOP DETECTED!)

Action: 🛑 STOP
Message: "I've hit a fix-break loop. Let me pause and create a plan to
          understand the root cause before continuing."
Trigger: Auto-enter planning mode
```

### Pattern 2: Scope Creep
```
Initial: "Add login form"
During work: User says "Oh, also add password reset"
During work: User says "And social login too"

Action: 🛑 PAUSE
Message: "The scope is expanding. Let me create a comprehensive plan for
          authentication that covers login, reset, and social auth together."
Trigger: Suggest planning mode
```

### Pattern 3: Architectural Confusion
```
During implementation: "Wait, should this be a component or a hook?"
Next step: "Actually, maybe a context provider?"
Next step: "Or a service class?"

Action: 🛑 PAUSE
Message: "I'm uncertain about the best architecture here. Let me step back
          and plan the proper structure before continuing."
Trigger: Auto-enter planning mode
```

---

## Integration with Existing Skills

### Execution Flow (Updated)

```
User Request
    ↓
1. context-management-core (FIRST)
   ↓ Validate context, classify task
   ↓
2. model-selection-core (SECOND)
   ↓ Select appropriate model
   ↓
3. task-planning-intelligence (THIRD) ← NEW!
   ↓ Calculate complexity score
   ↓ Decide: Direct vs Planning vs Ask
   ↓
   ├─ Score 0-3 → Direct implementation
   ├─ Score 4-6 → Ask user preference
   └─ Score 7-10 → Auto-enter planning mode
       ↓
4. Implementation OR Planning (FOURTH)
   ↓ Execute based on decision
   ↓
5. Mid-execution monitoring (ONGOING)
   ↓ Watch for loops/failures/scope creep
   └─ If detected → Pause, suggest/force planning
```

### Priority Hierarchy

1. **HIGHEST**: Context validation (context-management-core)
2. **SYSTEM-LEVEL**: Model selection (model-selection-core)
3. **SYSTEM-LEVEL**: Planning intelligence (task-planning-intelligence) ← NEW
4. **SYSTEM-LEVEL**: File management (file-management-policy)
5. **NORMAL**: Implementation skills (backend, frontend, etc.)

---

## User Communication Templates

### Template 1: Direct Implementation (Score 0-3)
```
[No announcement, just do it]
```

### Template 2: Ask User (Score 4-6)
```
"I can implement this directly or create a plan first. [Brief reasoning].
 Prefer to plan or proceed with [suggested approach]?"
```

### Template 3: Auto Planning (Score 7-10)
```
"This task requires planning because:
 - [Reason 1: e.g., affects multiple files]
 - [Reason 2: e.g., architectural decisions needed]
 - [Reason 3: e.g., unclear requirements]

 Entering planning mode to [what will be explored]."
```

### Template 4: Mid-Execution Pause
```
"⚠️ Pausing implementation. I've detected [loop/scope creep/confusion].
 Let me create a plan to [address root cause] before continuing.
 This will save time and tokens in the long run."
```

---

## Token Economics

### Example: Authentication Feature

**Without Planning Intelligence** (Direct implementation of complex task):
```
Attempt 1: Implement session-based auth → 3000 tokens → Fails (scalability)
Attempt 2: Switch to JWT → 3000 tokens → Fails (refresh token issue)
Attempt 3: Fix refresh logic → 2000 tokens → Fails (security flaw)
Attempt 4: Redesign security → 4000 tokens → Finally works

Total: 12,000 tokens
Time: 4 iterations
User frustration: HIGH
```

**With Planning Intelligence** (Detects complexity, plans first):
```
Planning mode: Explore auth patterns, design approach → 2000 tokens
Implementation: Execute planned approach → 3000 tokens → Works first time

Total: 5,000 tokens
Savings: 7,000 tokens (58%)
Time: 1 iteration
User satisfaction: HIGH
```

### ROI Calculation

```
Average complex task without planning: 8,000-15,000 tokens (multiple attempts)
Average complex task with planning: 3,000-6,000 tokens (planned execution)

Savings per complex task: 5,000-9,000 tokens (60-70%)

Planning cost: 1,500-2,500 tokens
ROI: 2x-4x return on planning investment
```

---

## Special Cases

### Case 1: User Explicitly Requests Planning
```
User: "Let's plan this first before implementing"

Action: Honor user request (override score)
Decision: Enter planning mode regardless of complexity score
```

### Case 2: User Explicitly Requests Direct Implementation
```
User: "No planning, just do it"

Action: IF score < 7 → Honor request
        IF score ≥ 7 → Warn user, then honor request

Warning: "This is complex and may require iteration. Proceeding as requested."
```

### Case 3: Microservices Project Context
```
Context: Working in microservices architecture

Modifier: +1 to complexity score (more moving parts)
Reason: Changes often affect multiple services, need coordination
```

### Case 4: Time-Sensitive Fix
```
User: "Production is down, fix NOW"

Action: IF score ≤ 5 → Direct implementation
        IF score > 5 → Quick triage plan (2 min), then implement

Note: Balance urgency with need to avoid making it worse
```

---

## Monitoring & Learning

### Track Patterns

Keep mental note of:
- **Planning → Success rate**: Did planning prevent failures?
- **Direct → Failure rate**: Did skipping planning cause loops?
- **User override outcomes**: Was user right to override suggestion?

### Adjust Thresholds

If patterns emerge:
- Too many false positives (unnecessary planning) → Increase threshold
- Too many loops (should have planned) → Decrease threshold

Current thresholds (v1.0.0):
- Direct: 0-3
- Ask: 4-6
- Mandatory: 7-10

---

## Quick Decision Flowchart

```
                    User Task Received
                           ↓
            [Context validated by context-mgmt-core]
                           ↓
              [Model selected by model-selection-core]
                           ↓
            ┌──────────────────────────────┐
            │  Calculate Complexity Score  │
            │  (0-10 based on 6 factors)  │
            └──────────────────────────────┘
                           ↓
              ┌────────────┴────────────┐
              ↓                         ↓
         Score 0-3                 Score 4-6              Score 7-10
              ↓                         ↓                      ↓
    ┌─────────────────┐      ┌──────────────────┐   ┌──────────────────┐
    │ Direct Implement│      │   Ask User       │   │ Auto Planning    │
    │ (No announcement)│      │ (Give choice)    │   │ (Explain why)    │
    └─────────────────┘      └──────────────────┘   └──────────────────┘
              ↓                         ↓                      ↓
    ┌─────────────────┐      ┌──────────────────┐   ┌──────────────────┐
    │  Implement      │      │ User decides     │   │ Enter Plan Mode  │
    └─────────────────┘      └──────────────────┘   └──────────────────┘
              ↓                    ↓       ↓                  ↓
    ┌─────────────────┐           ↓       ↓         ┌──────────────────┐
    │ Monitor for:    │    ┌──────┘       └──────┐  │ Explore & Design │
    │ - Loops         │    ↓                     ↓  └──────────────────┘
    │ - Failures (2+) │  Plan               Implement         ↓
    │ - Scope creep   │    ↓                     ↓    ┌──────────────────┐
    └─────────────────┘    └──────────┬──────────┘    │ Exit Plan Mode   │
              ↓                       ↓                └──────────────────┘
         Detected?                Implement                    ↓
              ↓                       ↓                    Implement
         ┌────┴────┐                 ↓                        ↓
         ↓         ↓                 ↓                        ↓
        Yes       No          ┌─────────────┐         ┌─────────────┐
         ↓         ↓          │   Success   │         │   Success   │
    Pause &    Continue       └─────────────┘         └─────────────┘
    Plan          ↓
         ↓         ↓
    Resume    Complete
```

---

## Status

**Version**: 1.0.0
**Status**: ACTIVE (Automatic enforcement)
**Created**: 2026-01-22
**Integration**: Works with context-management-core, model-selection-core, file-management-policy

---

## Summary (TL;DR)

**What**: Decides if task needs planning or can be implemented directly
**How**: Complexity scoring (0-10) based on 6 factors
**When**: After context validation, before implementation + mid-execution monitoring
**Why**: Prevents token waste on unnecessary planning AND prevents costly loops from insufficient planning

**Thresholds**:
- 0-3: Direct
- 4-6: Ask user
- 7-10: Plan first

**Saves**: 60-70% tokens on complex tasks by planning upfront instead of iterating through failures

---

**Remember**: Planning is an investment with 2x-4x ROI on complex tasks!

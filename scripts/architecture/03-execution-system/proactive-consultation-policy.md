# Proactive Decision Consultation Policy

## Version: 1.0.0
## Status: ALWAYS ACTIVE
## Priority: SYSTEM-LEVEL (Before making ANY judgment calls)

---

## Purpose

Bridges the gap between AI guidelines and actual decision-making by making the AI's reasoning transparent and collaborative with the user.

---

## The Problem (Before This Policy)

**Scenario:**
```
User: "Add authentication to the app"
Claude: *silently decides score is 8/10*
Claude: *enters plan mode without explaining why*
User: "Wait, why are we planning? Just add it!"
```

**Issues:**
- User doesn't know WHY decisions are made
- AI makes silent judgment calls
- User feels out of control
- Decisions might be wrong (no user input)

---

## The Solution (With This Policy)

**Scenario:**
```
User: "Add authentication to the app"
Claude: "Bhai, maine task analyze kiya:

        Complexity Score: 8/10
        Reasons:
        - Multiple files touch hongi (auth service, guards, middleware)
        - Architecture decision chahiye (JWT vs Session)
        - Database schema change hoga
        - Security-critical implementation

        Meri recommendation: Plan mode use karte hain

        Benefits:
        ✅ Approach finalize karenge (JWT/Session/OAuth)
        ✅ Architecture design karenge
        ✅ Tumse approval lenge
        ✅ Phir implement karenge (no loops, no mistakes)

        Drawback:
        ⚠️ 2-3 extra minutes planning mein lagenge

        Kya main Plan mode enter karu?"

User: "Haan theek hai" → Proceeds with plan mode
OR
User: "Nahi, JWT use karo seedha" → Proceeds direct with JWT
```

**Benefits:**
✅ User knows WHY decision is being made
✅ User stays in control
✅ AI reasoning is transparent
✅ Better decisions (user + AI combined knowledge)
✅ No surprises

---

## When to Apply This Policy

Use **AskUserQuestion** tool in these situations:

### 1. Planning Decision (Score 4-6)
When complexity is medium, ask user:
```
"Task complexity moderate hai (score 5/10).

 Reasons: [list reasons]

 Options:
 1. Plan mode (better for: multiple approaches, architectural decisions)
 2. Direct implementation (faster for: clear requirements)

 Tumhari recommendation kya hai?"
```

### 2. Phased Execution Decision (Score 3-5)
When task size is medium, ask user:
```
"Task size moderate hai (score 4/10).

 Reasons: [list reasons]

 Options:
 1. Phased execution (benefits: checkpoints, better quality, can pause/resume)
 2. Single session (benefits: faster, simpler)

 Kaunsa approach prefer karoge?"
```

### 3. Model/Approach Selection Uncertainty
When multiple valid approaches exist:
```
"Is task ke liye 2 approaches hain:

 Approach A (REST API):
 ✅ Simple, proven
 ⚠️ Multiple endpoints needed

 Approach B (GraphQL):
 ✅ Single endpoint, flexible
 ⚠️ Learning curve, complex setup

 Tumhara preference?"
```

### 4. Technology/Library Choice
When choosing between technologies:
```
"Date formatting ke liye options:

 Option 1: date-fns (lightweight, 2KB)
 Option 2: moment.js (feature-rich, 67KB)
 Option 3: native Intl API (no dependency)

 Kaunsa use karein?"
```

---

## Format for AskUserQuestion

**Template:**
```javascript
AskUserQuestion({
  questions: [{
    question: "Clear question ending with '?'",
    header: "Short label (12 chars max)",
    multiSelect: false, // or true if multiple choices allowed
    options: [
      {
        label: "Option 1 (Recommended)", // if you prefer this
        description: "Why this option? What are trade-offs?"
      },
      {
        label: "Option 2",
        description: "Why this option? What are trade-offs?"
      }
    ]
  }]
})
```

**Example (Real):**
```javascript
AskUserQuestion({
  questions: [{
    question: "Task complexity 8/10 hai. Plan mode use karein?",
    header: "Plan Mode",
    multiSelect: false,
    options: [
      {
        label: "Haan, plan mode use karo (Recommended)",
        description: "Architecture design + approach finalization + no loops/mistakes. 2-3 min extra lagega but better quality."
      },
      {
        label: "Nahi, seedha implement karo",
        description: "Faster start but risk of loops if approach galat ho. User ko approach batana hoga."
      }
    ]
  }]
})
```

---

## Logging After Decision

**MANDATORY**: After user responds, log the decision:

```bash
echo "[$(date '+%Y-%m-%d %H:%M:%S')] proactive-consultation | <decision> | <context>" >> ~/.claude/memory/logs/policy-hits.log
```

**Examples:**
```bash
# User chose plan mode
echo "[$(date '+%Y-%m-%d %H:%M:%S')] proactive-consultation | user-chose-plan-mode | auth-implementation-score-8" >> ~/.claude/memory/logs/policy-hits.log

# User chose direct implementation
echo "[$(date '+%Y-%m-%d %H:%M:%S')] proactive-consultation | user-chose-direct | auth-implementation-user-specified-jwt" >> ~/.claude/memory/logs/policy-hits.log

# User chose phased approach
echo "[$(date '+%Y-%m-%d %H:%M:%S')] proactive-consultation | user-chose-phased | ecommerce-app-score-7" >> ~/.claude/memory/logs/policy-hits.log
```

---

## DO NOT Ask When

**Skip AskUserQuestion in these cases:**

1. **Clear scores (no ambiguity)**
   - Score 0-3: Direct implementation (obvious)
   - Score 7-10: Plan mode mandatory (obvious)

2. **User already specified**
   - User said "plan it first" → Use plan mode
   - User said "just fix it" → Direct implementation

3. **Previous decision in session**
   - User already chose preference earlier
   - Apply same preference for similar tasks

4. **Trivial tasks**
   - Single line fixes
   - Typo corrections
   - Config changes

5. **Extremely urgent requests**
   - User said "urgent", "quick", "ASAP"
   - Emergency bug fixes

---

## Benefits Summary

**For User:**
- ✅ Stays in control of all major decisions
- ✅ Understands WHY AI recommends something
- ✅ Can override AI if they know better
- ✅ No surprises or unwanted actions

**For AI:**
- ✅ Transparent decision-making
- ✅ User input improves decision quality
- ✅ Less likely to make wrong assumptions
- ✅ Builds user trust

**For Process:**
- ✅ Collaborative instead of dictatorial
- ✅ Better outcomes (user + AI knowledge combined)
- ✅ Logged decisions for future reference
- ✅ Reduces frustration and rework

---

## Integration with Core Skills

**Updated Execution Flow:**

1. Context Management
2. Model Selection
3. Skill/Agent Intelligence
4. Planning Intelligence
   - Calculate score
   - **IF score 4-6 → Apply Proactive Consultation Policy** ← NEW
   - If score 7-10 → Enter plan mode (mandatory)
5. Phased Execution Decision
   - Calculate score
   - **IF score 3-5 → Apply Proactive Consultation Policy** ← NEW
   - If score 6-10 → Phased execution (mandatory)
6. Test Case Preference (already uses AskUserQuestion ✅)
7. Failure Prevention
8. Execute

---

## Success Metrics

**Track in logs:**
- Number of consultations (should be 10-20% of tasks)
- User overrides (if >50%, AI scoring needs calibration)
- User satisfaction (fewer complaints about unwanted actions)

**Dashboard addition:**
```bash
proactive-consultation=0  # in policy-counters.txt
```

---

## Examples (Before vs After)

### Example 1: Authentication

**Before:**
```
User: "Add auth"
Claude: *enters plan mode silently*
User: "Why planning? Just add JWT!"
```

**After:**
```
User: "Add auth"
Claude: "Score 8/10. Recommend plan mode for architecture decisions. Kya main proceed karu?"
User: "Nahi, JWT use karo seedha"
Claude: "Theek hai, JWT implementation start karta hoon" ✅
```

### Example 2: Large Feature

**Before:**
```
User: "Build e-commerce checkout"
Claude: *breaks into 4 phases without asking*
User: "Bhai itna complex kyun bana rahe ho?"
```

**After:**
```
User: "Build e-commerce checkout"
Claude: "Task size 7/10. Phased execution recommended (4 phases with checkpoints). Agree?"
User: "Haan sahi hai, phases mein karo"
Claude: "Perfect! Phase 1: Cart → Checkout UI" ✅
```

---

## Status

**ACTIVE**: This policy is permanent and applies to all judgment decisions.
**Version**: 1.0.0
**Created**: 2026-01-25
**Integration**: Works with core-skills-mandate.md, task-planning-intelligence, phased-execution-intelligence

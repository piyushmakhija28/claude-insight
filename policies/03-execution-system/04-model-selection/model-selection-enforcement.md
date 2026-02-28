# Model Selection Enforcement (CRITICAL)

## 🚨 READ THIS BEFORE EVERY USER REQUEST

---

## The One Rule to Remember

```
IF user asks to FIND/SEARCH/EXPLORE something
   THEN use: Task(subagent_type="Explore", model="haiku")

IF user asks to BUILD/FIX/EDIT something
   THEN use: Sonnet directly (current)

IF user asks to DESIGN/CHOOSE/PLAN architecture
   THEN use: Task(subagent_type="Plan", model="opus")
```

---

## Common Violations (AVOID THESE!)

### ❌ VIOLATION 1: Direct Grep/Glob for Searches
```
User: "Find all API routes"
❌ WRONG: Grep/Glob directly
✅ RIGHT: Task(Explore, haiku, "Find all API routes")
```

### ❌ VIOLATION 2: Sonnet for Exploration
```
User: "What's the project structure?"
❌ WRONG: Use Bash/Read with Sonnet
✅ RIGHT: Task(Explore, haiku, "Analyze project structure")
```

### ❌ VIOLATION 3: Sonnet for Architecture
```
User: "Should we use MongoDB or PostgreSQL?"
❌ WRONG: Answer directly with Sonnet
✅ RIGHT: Task(Plan, opus, "Compare MongoDB vs PostgreSQL")
```

---

## Pre-Flight Checklist (Use EVERY Time!)

Before responding to user:

1. ☑️ **Is this a search/find request?**
   - YES → Use Task(Explore, haiku)
   - NO → Continue

2. ☑️ **Is this an architecture/design request?**
   - YES → Use Task(Plan, opus)
   - NO → Continue

3. ☑️ **Is this an implementation request?**
   - YES → Use Sonnet directly
   - NO → Ask for clarification

---

## Cost Impact (Why This Matters)

**Scenario**: User asks to find auth logic in large codebase

### Wrong Approach (Sonnet 4.6 search):
```
Model: Sonnet 4.6 "The Workhorse" ($3/$15 per MTok)
Tokens: 5,000
Cost: $0.045
Time: 12 seconds
Result: Slow, expensive ❌
```

### Right Approach (Haiku 4.5 via Task):
```
Model: Haiku 4.5 "The Executor" ($1/$5 per MTok)
Tokens: 800
Cost: $0.0032
Time: 2 seconds
Result: Fast, cheap ✅
Savings: ~93% cost, 6x faster!
```

### Model Cost Reference (per MTok):
| Model | Input | Output | Speed | Intelligence |
|-------|-------|--------|-------|--------------|
| Opus 4.6 "The Strategist" | $5 | $25 | Moderate | Highest (Frontier) |
| Sonnet 4.6 "The Workhorse" | $3 | $15 | Fast | Balanced (Strong) |
| Haiku 4.5 "The Executor" | $1 | $5 | Fastest | Near-Frontier |

**Pro Tip:** Use Sonnet for main development, only switch to Opus when you hit a logic wall or need architectural review. Haiku is ~5x cheaper than Sonnet for search/read tasks.

---

## Expected Results

### Healthy Session (50+ messages):
```
🤖 Model Distribution:
   Haiku:  35-45% ✅
   Sonnet: 50-60% ✅
   Opus:    3-8%  ✅

💰 Cost: $2-4 for 50 messages ✅
🔥 Burn Rate: 2-5 tokens/min ✅
```

### Broken Session (NOT following policy):
```
🤖 Model Distribution:
   Sonnet: 100% ❌ ← RED FLAG!

💰 Cost: $8-12 for 50 messages ❌
🔥 Burn Rate: 10+ tokens/min ❌
```

---

## Trigger Words (Auto-Detection)

When you see these words, use Haiku:
- "Find..."
- "Search..."
- "Where is..."
- "Show me..."
- "List all..."
- "Locate..."
- "Explore..."
- "What files..."

When you see these words, use Opus:
- "Should we use..."
- "Design the..."
- "Architecture for..."
- "Choose between..."
- "Plan the..."
- "Best approach for..."

When you see these words, use Sonnet:
- "Fix..."
- "Add..."
- "Update..."
- "Implement..."
- "Write..."
- "Edit..."

---

## Self-Monitoring

After every 10 responses, ask yourself:
1. Did I use Task(haiku) for any searches?
2. Did I use Task(opus) for any architecture questions?
3. Am I following the QUICK REFERENCE?

If answer to #1 or #2 is NO, and user asked search/architecture questions:
→ You're violating the policy! ⚠️

---

## Status

**Priority**: SYSTEM-LEVEL (applies before all implementation)
**Version**: 2.0.0 (Updated Model Tiers - Opus 4.6, Sonnet 4.6, Haiku 4.5)
**Last Updated**: 2026-02-28
**Compliance**: MANDATORY - Cannot be skipped or bypassed

# Failure Learning System - Quick Start Guide

## Version: 2.0.0
## Status: PRODUCTION READY ✅

---

## What This Does

**Automatically learns from failures and prevents them in future!**

```
Failure happens once → Logged
Failure happens twice → Pattern detected
Prevention works → Confirmed
Never happens again → Success! ✅
```

---

## Usage (For Claude)

### 1. Before Executing Tool/Command

```python
# Check both Global KB and Project KB
project_name = get_current_project()

# Check Global KB first
if pattern_in_global_kb(command):
    use_global_solution()

# Check Project KB
elif pattern_in_project_kb(project_name, command):
    use_project_solution()

# No pattern found - execute normally
else:
    execute(command)
```

### 2. After Failure Occurs

```bash
# Log the failure
python ~/.claude/memory/update-failure-kb.py PROJECT_NAME log "SIGNATURE" "DETAILS" "SOLUTION"

# Example:
python ~/.claude/memory/update-failure-kb.py techdeveloper-ui log "npm-not-found" "npm install failed" "Use yarn install"
```

### 3. After Prevention Works

```bash
# Log successful prevention
python ~/.claude/memory/update-failure-kb.py PROJECT_NAME prevent "SIGNATURE" true

# Example:
python ~/.claude/memory/update-failure-kb.py techdeveloper-ui prevent "npm-not-found" true
```

### 4. Check Pattern Status

```bash
# Check if pattern exists
python ~/.claude/memory/update-failure-kb.py PROJECT_NAME check "SIGNATURE"

# Example:
python ~/.claude/memory/update-failure-kb.py techdeveloper-ui check "npm-not-found"
```

---

## Pattern Lifecycle Example

### Occurrence 1: Discovery

```
User: "Install dependencies"
Claude: npm install
Error: npm: command not found

→ Log failure
python update-failure-kb.py my-project log "npm-not-found" "npm install failed" "Use yarn install"

Result: Pattern created
Status: Monitoring 👁️
Frequency: 1
```

### Occurrence 2: Pattern Detection

```
User: "Add new package"
Claude: npm install lodash
Error: npm: command not found (again!)

→ Log failure again
python update-failure-kb.py my-project log "npm-not-found" "npm install failed again"

Result: Pattern detected!
Status: Learning ⚠️
Frequency: 2
```

### Occurrence 3: Apply Prevention

```
User: "Update dependencies"

Claude: (checks failures.md)
        → Sees: npm-not-found pattern (Learning, freq=2)
        → Tries: yarn upgrade instead
Success! ✅

→ Log successful prevention
python update-failure-kb.py my-project prevent "npm-not-found" true

Result: Confidence increased
Preventions: 1/1 (100%)
```

### Occurrence 4: Confirmation

```
User: "Install another package"

Claude: (checks failures.md)
        → Pattern confirmed (freq=3, confidence=100%)
        → Auto-prevents: yarn add package
Success! ✅

→ Log another successful prevention
python update-failure-kb.py my-project prevent "npm-not-found" true

Result: Pattern confirmed!
Status: Confirmed ✅
Frequency: 3
Preventions: 2/2 (100%)
```

### Future: Never Fails Again

```
User: "Do anything with packages"

Claude: (checks failures.md)
        → Pattern CONFIRMED
        → Always uses yarn, never npm
Success every time! ✅
```

---

## Files Structure

```
~/.claude/memory/sessions/
└── my-project/
    ├── project-summary.md          (Session memory)
    ├── failures.md                 (Human-readable report) ← NEW!
    ├── failures.json               (Machine-readable storage) ← NEW!
    └── session-*.md                (Session history)
```

---

## Failure Statuses

| Status | Meaning | Frequency | Action |
|--------|---------|-----------|--------|
| 👁️ Monitoring | First time seen | 1 | Watch & wait |
| ⚠️ Learning | Pattern detected | 2+ | Apply prevention |
| ✅ Confirmed | High confidence | 3+ & 80%+ confidence | Always prevent |
| ⭐ Global | Promoted to all projects | 5+ OR 3+ projects | Universal prevention |

---

## Integration with Execution Flow

```
User Request
    ↓
1. Context Validation
    ↓
2. Model Selection
    ↓
3. Task Planning
    ↓
4. FAILURE PREVENTION CHECK ✅
   │
   ├─ Load Global KB (common-failures-prevention.md)
   │  └─ Check: del → rm, grep → Grep, etc.
   │
   ├─ Load Project KB (sessions/PROJECT/failures.md)
   │  └─ Check: npm → yarn, .env → .env.local, etc.
   │
   └─ Pattern match?
      ├─ YES: Use solution from KB ✅
      └─ NO: Proceed normally
    ↓
5. Execute Tool/Command
    ↓
6. SUCCESS?
   ├─ YES: Done ✅
   │       If prevention was used → Log success
   │
   └─ NO (FAILED):
       └─ Log failure to project KB
           → Next time will be prevented ✅
```

---

## Quick Commands

### Log a New Failure

```bash
python ~/.claude/memory/update-failure-kb.py PROJECT_NAME log SIGNATURE DETAILS [SOLUTION]
```

### Log Successful Prevention

```bash
python ~/.claude/memory/update-failure-kb.py PROJECT_NAME prevent SIGNATURE true
```

### Check Pattern

```bash
python ~/.claude/memory/update-failure-kb.py PROJECT_NAME check SIGNATURE
```

### View Project Failures

```bash
cat ~/.claude/memory/sessions/PROJECT_NAME/failures.md
```

### View All Project Patterns

```bash
cat ~/.claude/memory/sessions/PROJECT_NAME/failures.json | jq
```

---

## Real-World Benefits

### Without Failure Learning:

```
Session 1:
User: "Delete temp file"
Claude: del temp.txt
Error: bash: del: command not found
Claude: rm temp.txt ✅

Session 2 (Next day):
User: "Delete another file"
Claude: del file.txt          ← SAME MISTAKE!
Error: bash: del: command not found
Claude: rm file.txt ✅
```

### With Failure Learning:

```
Session 1:
User: "Delete temp file"
Claude: del temp.txt
Error: bash: del: command not found
→ Logged to failures.md (Monitoring)
Claude: rm temp.txt ✅

Session 2 (Next day):
User: "Delete another file"
Claude: (checks failures.md)
        → Pattern detected: del → rm
        → Auto-prevents: rm file.txt ✅
Success! No error! 🎉
```

---

## Promotion to Global KB

When a pattern is seen in **3+ projects** OR has **frequency 5+** in one project:

```
Pattern confirmed in multiple projects
    ↓
Auto-promote to Global KB
    ↓
All future projects benefit ✅
```

**Example:**
```
Project A: "Edit without Read" → 3 times
Project B: "Edit without Read" → 2 times
Project C: "Edit without Read" → 2 times

System: 3+ projects affected!
        → Promote to global KB ⭐

Result: ALL projects now prevent this! ✅
```

---

## Statistics Tracking

Each project tracks:
- Total failures
- Patterns learned
- Prevention success rate
- Confidence scores
- Pattern frequency

**Example Stats:**
```
Project: techdeveloper-ui
- Total Failures: 15
- Patterns Learned: 8
- Prevention Rate: 93%
- Patterns Confirmed: 6
- Patterns Learning: 2
```

---

## Best Practices

### 1. Log All Failures

```
Even if you fix it immediately → Log it!
Next time it won't happen at all.
```

### 2. Include Solutions

```bash
# Good
python update-failure-kb.py my-project log "npm-not-found" "npm failed" "Use yarn"

# Better (more detail)
python update-failure-kb.py my-project log "npm-not-found" "npm install failed - command not found" "Use yarn install instead"
```

### 3. Log Prevention Results

```bash
# After prevention works
python update-failure-kb.py my-project prevent "npm-not-found" true

# After prevention fails (rare)
python update-failure-kb.py my-project prevent "npm-not-found" false
```

### 4. Review Patterns Regularly

```bash
# Check what patterns are learned
cat ~/.claude/memory/sessions/my-project/failures.md

# See pattern details
cat ~/.claude/memory/sessions/my-project/failures.json | jq
```

---

## Troubleshooting

### Q: Pattern not being applied?

**A:** Check status and confidence:
```bash
python update-failure-kb.py my-project check "SIGNATURE"
```

Pattern must be:
- Status: Learning or Confirmed
- Confidence: 80%+

### Q: False pattern detected?

**A:** Pattern will auto-discard if preventions fail:
- If prevention fails repeatedly
- Confidence drops below 80%
- Pattern gets demoted to Monitoring

### Q: Want to manually promote pattern?

**A:** Edit `failures.json` directly:
```json
{
  "status": "Confirmed",
  "confidence": 100,
  "frequency": 5
}
```

---

## Status

✅ **PRODUCTION READY**
✅ **TESTED** - Pattern evolution verified
✅ **INTEGRATED** - Works with session memory
✅ **AUTOMATED** - Auto-updates on failures

**Next Steps:**
1. Use in real projects
2. Build pattern library
3. Cross-project learning
4. Global KB auto-updates

---

**Version:** 2.0.0
**Date:** 2026-01-26
**Status:** Active & Ready to Learn! 🚀

# Failure Learning System (Self-Improving with Persistent Memory)

## Version: 2.0.0
## Status: ALWAYS ACTIVE
## Priority: SYSTEM-LEVEL
## Upgrade: Integrated with Persistent Session Memory

---

## What's New in v2.0

### Before (v1.0):
- ✅ Static KB of common failures
- ✅ Basic logging to failures.log
- ❌ No learning between sessions
- ❌ Manual KB updates
- ❌ No project-specific patterns
- ❌ No frequency tracking

### After (v2.0):
- ✅ **Persistent failure memory per project**
- ✅ **Auto-learning from failures**
- ✅ **Pattern frequency tracking**
- ✅ **Project-specific adaptations**
- ✅ **Auto-KB updates**
- ✅ **Failure trend analysis**
- ✅ **Smart pattern promotion**

---

## Architecture

### Two-Tier Failure Memory

```
┌─────────────────────────────────────────────────────────┐
│  TIER 1: Global Failure KB (Seed Knowledge)            │
│  ═══════════════════════════════════════════════════    │
│  ~/.claude/memory/common-failures-prevention.md        │
│                                                         │
│  - Universal patterns (all projects)                   │
│  - High-confidence solutions (80%+)                    │
│  - Static seed knowledge                               │
│  - Manually curated                                    │
│                                                         │
│  Examples:                                             │
│  • del → rm (Windows cmd in bash)                     │
│  • grep via Bash → Use Grep tool                      │
│  • Edit without Read → Read first                     │
└─────────────────────────────────────────────────────────┘
                         ↓
            Used by all projects
                         ↓
┌─────────────────────────────────────────────────────────┐
│  TIER 2: Project-Specific Failure Memory               │
│  ═══════════════════════════════════════════════════    │
│  ~/.claude/memory/sessions/{project}/failures.md       │
│                                                         │
│  - Project-specific patterns                           │
│  - Learning from actual failures                       │
│  - Frequency tracking per pattern                      │
│  - Auto-updated on failures                            │
│  - Pattern evolution (Learning → Confirmed → Global)   │
│                                                         │
│  Examples:                                             │
│  • This project uses yarn, not npm (learned)           │
│  • Config file is .env.local not .env (learned)        │
│  • Tests fail without Docker running (learned)         │
└─────────────────────────────────────────────────────────┘
                         ↓
              Per-project learning
```

---

## Storage Structure

### Project Failure Memory Location

```
~/.claude/memory/sessions/
├── techdeveloper-ui/
│   ├── project-summary.md
│   ├── failures.md                    ← NEW! Project failures
│   └── session-*.md
│
├── medspy-node/
│   ├── project-summary.md
│   ├── failures.md                    ← NEW! Project failures
│   └── session-*.md
│
└── triglav-node/
    ├── project-summary.md
    ├── failures.md                    ← NEW! Project failures
    └── session-*.md
```

---

## Project Failures File Format

### Template: `failures.md`

```markdown
# Failure Memory: {project-name}

**Last Updated:** 2026-01-26 14:00
**Total Failures Recorded:** 15
**Patterns Learned:** 8
**Patterns Promoted to Global:** 2

---

## Active Patterns (Auto-Applied)

### Pattern 1: Package Manager
**Signature:** `npm install` command
**Learned From:** Session 2026-01-23 (npm not found error)
**Frequency:** 5 occurrences
**Status:** Confirmed ✅
**Solution:** Use `yarn install` instead
**Confidence:** 100% (5/5 times)

**Prevention Rule:**
```bash
# Auto-replace npm → yarn for this project
if command contains "npm install"; then
    replace with "yarn install"
fi
```

---

### Pattern 2: Environment Config
**Signature:** Reading `.env` file
**Learned From:** Session 2026-01-24 (file not found)
**Frequency:** 3 occurrences
**Status:** Confirmed ✅
**Solution:** Use `.env.local` instead
**Confidence:** 100% (3/3 times)

**Prevention Rule:**
```bash
if reading ".env"; then
    check ".env.local" first
fi
```

---

### Pattern 3: Docker Dependency
**Signature:** Running tests
**Learned From:** Session 2026-01-25 (connection refused)
**Frequency:** 2 occurrences
**Status:** Learning ⚠️
**Solution:** Check Docker is running first
**Confidence:** 100% (2/2 times)

**Prevention Rule:**
```bash
before "npm test"; then
    check docker ps (should succeed)
    if fails: warn user "Docker not running"
fi
```

---

## Failed Attempts (Under Observation)

### Attempt 1: Database Connection
**Signature:** Connecting to PostgreSQL
**First Seen:** 2026-01-26 10:00
**Frequency:** 1 occurrence
**Status:** Monitoring 👁️
**Details:** Connection to localhost:5432 failed
**Hypothesis:** Database not running or wrong port
**Next Steps:** Wait for 2nd occurrence to confirm pattern

---

## Pattern Promotion History

### Promoted to Global KB

1. **Pattern:** Edit tool used without Read first
   - **Promoted:** 2026-01-24
   - **Reason:** 100% failure rate across 5 projects
   - **Now in:** common-failures-prevention.md

2. **Pattern:** Using bash grep instead of Grep tool
   - **Promoted:** 2026-01-25
   - **Reason:** 100% applies to all projects
   - **Now in:** common-failures-prevention.md

---

## Statistics

**Failure Prevention Score:** 87% (13/15 prevented after first occurrence)

**Top Prevented Failures:**
1. npm → yarn replacement: 5 times ✅
2. .env → .env.local: 3 times ✅
3. Docker check before tests: 2 times ✅

**Learning Efficiency:**
- Patterns identified: 8
- Patterns confirmed: 6
- False positives: 1 (discarded)
- Patterns promoted to global: 2

---

## Auto-Learning Triggers

**When to log:**
- ✅ Tool/command fails
- ✅ Same pattern fails 2nd time → Confirm
- ✅ Pattern fails 5+ times → Consider global promotion

**When to apply:**
- ✅ Pattern confidence > 80%
- ✅ At least 2 occurrences
- ✅ Solution verified working

**When to promote:**
- ✅ Pattern applies across multiple projects
- ✅ Confidence 100%
- ✅ 5+ occurrences OR 3+ projects affected
```

---

## Auto-Learning Workflow

### Step 1: Failure Detection

```
Tool/Command Executed
    ↓
Did it fail? NO → Done ✅
    ↓ YES
Log to failures.md
    ↓
Extract pattern signature
    ↓
Check: First time seeing this?
    ↓ YES
Status: "Monitoring 👁️"
    ↓ NO (seen before)
Increment frequency counter
    ↓
Status: "Learning ⚠️" (2nd occurrence)
    ↓
Apply prevention next time
```

### Step 2: Pattern Confirmation

```
Pattern occurs 2+ times
    ↓
Solution worked every time?
    ↓ YES
Status: "Confirmed ✅"
    ↓
Confidence: (success_count / total_count) * 100%
    ↓
If confidence > 80%:
    Auto-apply prevention
```

### Step 3: Pattern Promotion

```
Pattern confirmed in 1 project
    ↓
Check: Does this apply to other projects?
    ↓ YES
Seen in 3+ projects? OR Frequency 5+ in one project?
    ↓ YES
Promote to Global KB
    ↓
Update common-failures-prevention.md
    ↓
Log promotion
    ↓
All future projects benefit ✅
```

---

## Integration with Execution Flow

### Updated Execution Flow

```
User Request
    ↓
1. Context Validation
    ↓
2. Model Selection
    ↓
3. Task Planning
    ↓
4. FAILURE PREVENTION CHECK (v2.0) ← ENHANCED!
   ├─ Load Global KB (Tier 1)
   ├─ Load Project Failures (Tier 2)
   ├─ Pattern match against both
   │
   ├─ Match found in Global KB?
   │  └─ YES: Use global solution ✅
   │
   ├─ Match found in Project KB?
   │  └─ YES: Use project-specific solution ✅
   │
   └─ No match found
      └─ Proceed with execution
    ↓
5. Execute Tool/Command
    ↓
6. SUCCESS? → Done ✅
    ↓ NO (FAILED)
7. AUTO-LEARNING TRIGGER
   ├─ Log to project failures.md
   ├─ Extract pattern signature
   ├─ Update frequency counter
   ├─ Determine status (Monitoring/Learning/Confirmed)
   ├─ Check promotion criteria
   └─ Next time → Will be prevented ✅
```

---

## Failure Pattern Lifecycle

```
┌─────────────────────────────────────────────────┐
│  Stage 1: First Failure                         │
│  ════════════════════                            │
│  Status: Monitoring 👁️                          │
│  Frequency: 1                                    │
│  Confidence: N/A                                 │
│  Action: Log only, observe                       │
└─────────────────────────────────────────────────┘
                   ↓
          (Occurs again)
                   ↓
┌─────────────────────────────────────────────────┐
│  Stage 2: Pattern Detected                      │
│  ═══════════════════════                         │
│  Status: Learning ⚠️                             │
│  Frequency: 2+                                   │
│  Confidence: Calculating                         │
│  Action: Apply prevention                        │
└─────────────────────────────────────────────────┘
                   ↓
     (Prevention successful 2+ times)
                   ↓
┌─────────────────────────────────────────────────┐
│  Stage 3: Pattern Confirmed                     │
│  ════════════════════════                        │
│  Status: Confirmed ✅                            │
│  Frequency: 3+                                   │
│  Confidence: 80%+                                │
│  Action: Always prevent                          │
└─────────────────────────────────────────────────┘
                   ↓
   (Seen in 3+ projects OR frequency 5+)
                   ↓
┌─────────────────────────────────────────────────┐
│  Stage 4: Promoted to Global                    │
│  ═══════════════════════════                     │
│  Status: Global ⭐                               │
│  Location: common-failures-prevention.md         │
│  Confidence: 100%                                │
│  Action: All projects benefit                    │
└─────────────────────────────────────────────────┘
```

---

## Auto-Update Script

### Script: `update-failure-kb.sh`

```bash
#!/bin/bash
# Auto-updates failure KB from session logs

PROJECT_NAME=$(basename "$PWD")
SESSION_DIR=~/.claude/memory/sessions/$PROJECT_NAME
FAILURES_FILE="$SESSION_DIR/failures.md"
GLOBAL_KB=~/.claude/memory/common-failures-prevention.md

# Create failures.md if doesn't exist
if [ ! -f "$FAILURES_FILE" ]; then
    cat > "$FAILURES_FILE" <<EOF
# Failure Memory: $PROJECT_NAME

**Last Updated:** $(date '+%Y-%m-%d %H:%M')
**Total Failures Recorded:** 0
**Patterns Learned:** 0
**Patterns Promoted to Global:** 0

---

## Active Patterns (Auto-Applied)

(No patterns learned yet)

---

## Failed Attempts (Under Observation)

(No failures recorded yet)
EOF
fi

# Function to log new failure
log_failure() {
    local signature="$1"
    local details="$2"

    # Check if pattern already exists
    if grep -q "$signature" "$FAILURES_FILE"; then
        # Increment frequency
        # ... (implementation)
    else
        # Add new pattern
        # ... (implementation)
    fi
}

# Check for promotion eligibility
check_promotion() {
    # ... (implementation)
}
```

---

## Real-World Examples

### Example 1: Learning Package Manager

**Session 1 (2026-01-23):**
```
User: "Install dependencies"
Claude: npm install
Error: npm: command not found

→ Logged to failures.md
  Status: Monitoring 👁️
  Frequency: 1
```

**Session 2 (2026-01-24):**
```
User: "Add a new package"
Claude: (checks failures.md)
        → Sees: npm failed before
        → Tries: yarn add instead
Success! ✅

→ Updated failures.md
  Status: Learning ⚠️
  Frequency: 2
  Confidence: 100% (1/1 prevention worked)
```

**Session 3 (2026-01-25):**
```
User: "Update dependencies"
Claude: (checks failures.md)
        → Pattern confirmed (2+ occurrences)
        → Auto-prevents: yarn upgrade
Success! ✅

→ Updated failures.md
  Status: Confirmed ✅
  Frequency: 3
  Confidence: 100% (2/2 preventions worked)
```

**Result:** Never uses npm again for this project! ✅

---

### Example 2: Pattern Promotion

**Project A (techdeveloper-ui):**
```
Failure: Edit tool without Read
Frequency: 3
Status: Confirmed ✅
```

**Project B (medspy-node):**
```
Failure: Edit tool without Read
Frequency: 2
Status: Confirmed ✅
```

**Project C (triglav-node):**
```
Failure: Edit tool without Read
Frequency: 2
Status: Confirmed ✅
```

**System Detects:**
```
Pattern seen in 3+ projects
Confidence: 100%
→ PROMOTE TO GLOBAL KB ⭐
```

**Result:**
- Added to common-failures-prevention.md
- All future projects benefit
- No project makes this mistake again! ✅

---

## Benefits

### For Users:

1. **Fewer Failures**
   - Same mistake never repeated
   - Project-specific adaptations
   - Faster execution

2. **Time Savings**
   - No error → retry cycles
   - Auto-corrects before failure
   - Smart prevention

3. **Better Experience**
   - Feels like Claude "learns"
   - Remembers project quirks
   - Intelligent assistance

### For System:

1. **Token Efficiency**
   - Prevent wasted tokens on failures
   - No retry overhead
   - Optimal execution

2. **Knowledge Growth**
   - KB grows automatically
   - Patterns emerge organically
   - Cross-project learning

3. **Intelligence**
   - Appears more capable
   - Contextually aware
   - Self-improving

---

## Statistics & Metrics

### Track These Metrics:

```markdown
# Failure Learning Dashboard

**Global Statistics:**
- Total patterns in Global KB: 45
- Total patterns across all projects: 127
- Patterns promoted to global: 12
- Overall prevention rate: 89%

**Per Project:**
- techdeveloper-ui: 15 patterns, 93% prevention rate
- medspy-node: 8 patterns, 85% prevention rate
- triglav-node: 12 patterns, 91% prevention rate

**Learning Efficiency:**
- Average patterns per project: 4.2
- Average time to confirm pattern: 2.3 sessions
- False positive rate: 3%
- Promotion rate: 8% (good patterns promoted)

**Top Prevented Failures (Global):**
1. del → rm: 127 times prevented
2. Edit without Read: 89 times prevented
3. grep via Bash → Grep tool: 56 times prevented
```

---

## Implementation Checklist

### Phase 1: Storage Setup ✅
- [x] Create failures.md per project
- [x] Define schema/template
- [x] Integrate with sessions/

### Phase 2: Auto-Learning 🚧
- [ ] Auto-detect failures
- [ ] Extract pattern signatures
- [ ] Update frequency counters
- [ ] Calculate confidence scores

### Phase 3: Auto-Prevention 🚧
- [ ] Load Global KB before execution
- [ ] Load Project KB before execution
- [ ] Pattern matching algorithm
- [ ] Apply solutions automatically

### Phase 4: Pattern Promotion 📅
- [ ] Detect cross-project patterns
- [ ] Promotion criteria checker
- [ ] Auto-update Global KB
- [ ] Logging & notification

### Phase 5: Analytics 📅
- [ ] Dashboard script
- [ ] Prevention rate calculator
- [ ] Pattern effectiveness tracker
- [ ] Reporting system

---

## Status

✅ **DESIGNED** - Architecture complete
🚧 **IN PROGRESS** - Storage integration
📅 **PLANNED** - Auto-learning & promotion

**Next Steps:**
1. Create failures.md template
2. Implement auto-logging
3. Build pattern matcher
4. Enable auto-prevention

---

**Version:** 2.0.0
**Date:** 2026-01-26
**Status:** Enhanced with Persistent Memory
**Priority:** SYSTEM-LEVEL (ALWAYS ACTIVE)

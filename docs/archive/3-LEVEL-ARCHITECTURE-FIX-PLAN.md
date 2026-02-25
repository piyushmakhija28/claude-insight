# 3-Level Architecture - Fix Plan

**Date:** 2026-02-17
**Issue:** Scripts exist but have inconsistent argument interfaces
**Status:** 🔧 FIXING

---

## ✅ Scripts That Exist (All 7 Core Scripts)

1. ✅ `auto-fix-enforcer.sh` - WORKING ✅
2. ✅ `context-monitor-v2.py` - WORKING ✅
3. ✅ `standards-loader.py` - WORKING ✅
4. ✅ `prompt-generator.py` - WORKING ✅
5. ✅ `task-auto-analyzer.py` - NEEDS FIX 🔧
6. ✅ `auto-plan-mode-suggester.py` - WORKING ✅
7. ✅ `intelligent-model-selector.py` - NEEDS FIX 🔧

---

## 🔧 Issues Found & Solutions

### Issue #1: `task-auto-analyzer.py` - Wrong arguments

**Current behavior:**
```bash
# Accepts only message, no flags
python task-auto-analyzer.py "message"

# Does NOT accept:
python task-auto-analyzer.py "message" --complexity 3 --task-type "Database"
```

**Expected (per CLAUDE.md):**
```bash
task-auto-breakdown.py "{STRUCTURED_PROMPT}"
```

**Problem:**
- File named `task-auto-analyzer.py` but CLAUDE.md references `task-auto-breakdown.py`
- Doesn't accept complexity/task-type flags
- Output is generic

**Solution Options:**

**A. Update CLAUDE.md (Quick Fix):**
```markdown
# OLD:
→ task-auto-breakdown.py "{STRUCTURED_PROMPT}"

# NEW:
→ task-auto-analyzer.py "{USER_MESSAGE}"
# Note: Complexity is calculated internally, no flags needed
```

**B. Create wrapper script:**
```python
# Create: task-auto-breakdown.py
# Wrapper that accepts old interface and calls task-auto-analyzer.py
```

**C. Fix task-auto-analyzer.py:**
- Add argparse for --complexity, --task-type
- Use these hints if provided, calculate if not

**Recommendation:** Option A (Update docs) - Fastest, script works fine as-is

---

### Issue #2: `intelligent-model-selector.py` - Expects JSON file

**Current behavior:**
```bash
# Expects JSON file path as argument
python intelligent-model-selector.py analysis.json

# Does NOT accept direct args:
python intelligent-model-selector.py 9 "Database" "false"
```

**Expected (per CLAUDE.md):**
```bash
intelligent-model-selector.py "{COMPLEXITY}" "{TASK_TYPE}" "{PLAN_MODE}"
```

**Problem:**
- Script expects JSON file path
- CLAUDE.md shows direct arguments
- Interface mismatch

**Solution Options:**

**A. Use `model-auto-selector.py` instead:**
```bash
# This script accepts JSON string directly
python model-auto-selector.py --task-info '{"type":"Database","complexity":5}'
```

**B. Create wrapper:**
```python
# Accept direct args, create temp JSON, call intelligent-model-selector.py
```

**C. Update CLAUDE.md:**
```markdown
# OLD:
→ intelligent-model-selector.py "{COMPLEXITY}" "{TASK_TYPE}" "{PLAN_MODE}"

# NEW:
→ model-auto-selector.py --task-info '{"type":"Database","complexity":5}'
```

**Recommendation:** Option C (Use model-auto-selector.py in docs) - Already works!

---

## 📋 Standardized 3-Level Architecture Flow (CORRECTED)

### LEVEL -1: AUTO-FIX ENFORCEMENT ✅
```bash
export PYTHONIOENCODING=utf-8
bash ~/.claude/memory/auto-fix-enforcer.sh
```
**Status:** ✅ WORKING

---

### LEVEL 1: SYNC SYSTEM ✅

**Step 1.1: Context Management**
```bash
python ~/.claude/memory/01-sync-system/context-management/context-monitor-v2.py --current-status
```
**Status:** ✅ WORKING

**Step 1.2: Session Management**
```bash
python ~/.claude/memory/session-id-generator.py current
```
**Status:** ✅ WORKING

---

### LEVEL 2: RULES/STANDARDS SYSTEM ✅

**Step 2.1: Load Standards**
```bash
python ~/.claude/memory/02-standards-system/standards-loader.py --load-all
```
**Status:** ✅ WORKING

---

### LEVEL 3: EXECUTION SYSTEM

**Step 3.0: Prompt Generation** ✅
```bash
python ~/.claude/memory/03-execution-system/00-prompt-generation/prompt-generator.py "User message here"
```
**Status:** ✅ WORKING
**Output:** Structured prompt with complexity, task type, patterns

---

**Step 3.1: Task Breakdown** 🔧 NEEDS DOC UPDATE
```bash
# CURRENT (WORKING):
python ~/.claude/memory/03-execution-system/01-task-breakdown/task-auto-analyzer.py "User message here"

# OLD DOCS (INCORRECT):
# python task-auto-breakdown.py "{MESSAGE}" --complexity 3 --task-type "Database"
```
**Status:** ✅ SCRIPT WORKS, ❌ DOCS WRONG
**Fix:** Update CLAUDE.md to use `task-auto-analyzer.py` without flags

---

**Step 3.2: Plan Mode Suggestion** ✅
```bash
python ~/.claude/memory/03-execution-system/02-plan-mode/auto-plan-mode-suggester.py 5 "User message here"
```
**Status:** ✅ WORKING
**Args:** `<complexity_score> "<message>"`

---

**Step 3.3: Model Selection** 🔧 NEEDS DOC UPDATE
```bash
# CURRENT (WORKING):
python ~/.claude/memory/03-execution-system/04-model-selection/model-auto-selector.py \
  --task-info '{"type":"Database","complexity":5}'

# OLD DOCS (INCORRECT):
# python intelligent-model-selector.py 9 "Database" "false"
```
**Status:** ✅ SCRIPT WORKS, ❌ DOCS WRONG
**Fix:** Update CLAUDE.md to use `model-auto-selector.py --task-info '{...}'`

---

## 🎯 Action Plan

### Phase 1: Update CLAUDE.md (Quick Win) ✅

Update execution flow documentation with correct commands:

1. **Task Breakdown Section:**
   ```markdown
   # OLD:
   → task-auto-breakdown.py "{STRUCTURED_PROMPT}"

   # NEW:
   → task-auto-analyzer.py "{USER_MESSAGE}"
   # Complexity calculated internally from message analysis
   ```

2. **Model Selection Section:**
   ```markdown
   # OLD:
   → intelligent-model-selector.py "{COMPLEXITY}" "{TASK_TYPE}" "{PLAN_MODE}"

   # NEW:
   → model-auto-selector.py --task-info '{"type":"<TASK_TYPE>","complexity":<SCORE>}'
   ```

### Phase 2: Create Convenience Wrapper (Optional)

**File:** `~/.claude/memory/run-3-level-flow.sh`
```bash
#!/bin/bash
# Complete 3-level architecture flow with one command

USER_MESSAGE="$1"

echo "========================================="
echo "3-LEVEL ARCHITECTURE EXECUTION"
echo "========================================="

# LEVEL -1: Auto-Fix
echo "[LEVEL -1] Auto-Fix Enforcement..."
bash ~/.claude/memory/auto-fix-enforcer.sh || exit 1

# LEVEL 1: Sync System
echo "[LEVEL 1] Context Check..."
python ~/.claude/memory/01-sync-system/context-management/context-monitor-v2.py --current-status

echo "[LEVEL 1] Session ID..."
python ~/.claude/memory/session-id-generator.py current

# LEVEL 2: Standards
echo "[LEVEL 2] Loading Standards..."
python ~/.claude/memory/02-standards-system/standards-loader.py --load-all

# LEVEL 3: Execution
echo "[LEVEL 3.0] Prompt Generation..."
python ~/.claude/memory/03-execution-system/00-prompt-generation/prompt-generator.py "$USER_MESSAGE"

echo "[LEVEL 3.1] Task Analysis..."
python ~/.claude/memory/03-execution-system/01-task-breakdown/task-auto-analyzer.py "$USER_MESSAGE"

echo "[LEVEL 3.2] Plan Mode Suggestion..."
# Get complexity from task-auto-analyzer output (parse JSON)
# For now, use default 5
python ~/.claude/memory/03-execution-system/02-plan-mode/auto-plan-mode-suggester.py 5 "$USER_MESSAGE"

echo "[LEVEL 3.3] Model Selection..."
python ~/.claude/memory/03-execution-system/04-model-selection/model-auto-selector.py \
  --task-info '{"type":"Implementation","complexity":5}'

echo "========================================="
echo "✅ 3-LEVEL FLOW COMPLETE"
echo "========================================="
```

### Phase 3: Backward Compatibility (If Needed)

Create symlinks/wrappers for old names:
```bash
# Create: task-auto-breakdown.py → calls task-auto-analyzer.py
# Accepts old interface, converts to new
```

---

## ✅ Verification Test

**Command:**
```bash
# Test full flow with sample message
bash ~/.claude/memory/run-3-level-flow.sh "Create a Product entity with name, description, price"
```

**Expected Result:**
- All levels execute without errors
- Each step produces JSON/structured output
- Flow completes successfully

---

## 📊 Summary

| Component | Status | Action Needed |
|-----------|--------|---------------|
| **Scripts** | ✅ All exist | None |
| **Documentation** | ❌ Outdated | Update CLAUDE.md |
| **Integration** | ⚠️ Manual | Create wrapper script (optional) |
| **Testing** | ❌ Not tested | Run verification test |

**Bottom Line:**
- ✅ Scripts work individually
- ❌ CLAUDE.md has wrong command examples
- 🔧 Need to update docs + create convenience wrapper

**Time to Fix:** 10-15 minutes
**Priority:** HIGH (blocking users from using 3-level architecture)

---

**Next Step:** Update CLAUDE.md with correct commands

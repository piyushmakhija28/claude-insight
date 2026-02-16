# Auto-Fix Enforcement System v1.0.0

**🚨 CRITICAL: If ANY policy or system fails → STOP ALL WORK → FIX IMMEDIATELY**

---

## 🎯 Purpose

The Auto-Fix Enforcement System ensures that:
1. **ALL systems are checked** before any work begins
2. **Work is BLOCKED** if any critical failure is detected
3. **Failures are auto-fixed** whenever possible
4. **Clear fix instructions** are provided for manual fixes

---

## 🚨 Philosophy

**Zero Tolerance for Failures:**
- ❌ Don't work around failures
- ❌ Don't ignore warnings
- ❌ Don't proceed with broken systems
- ✅ Fix immediately and properly

**Blocking Enforcement:**
- If Python is missing → BLOCK
- If critical files are missing → BLOCK
- If session not started → BLOCK
- If enforcer not initialized → BLOCK

---

## 🔍 What It Checks

### 1. **Python Availability** (CRITICAL)
- Checks: `python --version`
- Fix: Install Python, add to PATH
- Auto-fixable: No

### 2. **Critical Files** (CRITICAL)
- Checks: blocking-policy-enforcer.py, session-start.sh, plan-detector.py, etc.
- Fix: Restore from backup/repository
- Auto-fixable: No

### 3. **Blocking Enforcer** (CRITICAL)
- Checks: Enforcer initialized, session started
- Fix: Run session-start.sh
- Auto-fixable: Yes (can initialize state)

### 4. **Session State** (HIGH)
- Checks: Session started, context checked
- Fix: Complete session initialization
- Auto-fixable: Partial

### 5. **Daemons** (INFO)
- Checks: 9 daemon statuses
- Fix: Restart daemons if needed
- Auto-fixable: No (informational only)
- Note: System works without daemons, automation disabled

### 6. **Git Repository** (INFO)
- Checks: Git status, uncommitted changes
- Fix: Commit changes
- Auto-fixable: No (informational only)

---

## 🚀 Usage

### Automatic (Recommended)

Run at session start or before any major action:

```bash
# Set encoding and run
export PYTHONIOENCODING=utf-8
bash ~/.claude/memory/auto-fix-enforcer.sh
```

### Manual Check Only

Check systems without auto-fixing:

```bash
bash ~/.claude/memory/auto-fix-enforcer.sh --check
```

### JSON Output

Get failures as JSON:

```bash
python ~/.claude/memory/auto-fix-enforcer.py --json
```

---

## 📊 Example Output

### All Systems OK

```
================================================================================
🚨 AUTO-FIX ENFORCER - CHECKING ALL SYSTEMS
================================================================================

🔍 [1/6] Checking Python...
   ✅ Python available: Python 3.13.12

🔍 [2/6] Checking critical files...
   ✅ All critical files present

🔍 [3/6] Checking blocking enforcer...
   ✅ Blocking enforcer initialized

🔍 [4/6] Checking session state...
   ✅ Session state valid

🔍 [5/6] Checking daemons...
   ℹ️  Daemons: 0 running, 9 stopped
   ℹ️  Daemon status is informational only (not blocking)

🔍 [6/6] Checking git repositories...
   ✅ Git repository clean

================================================================================
✅ ALL SYSTEMS OPERATIONAL - NO FAILURES DETECTED
================================================================================
```

### With Failures

```
================================================================================
🚨 AUTO-FIX ENFORCER - CHECKING ALL SYSTEMS
================================================================================

🔍 [1/6] Checking Python...
   ❌ Python NOT FOUND - CRITICAL!

🔍 [2/6] Checking critical files...
   ❌ Missing: scripts/plan-detector.py (Plan detector)

🔍 [3/6] Checking blocking enforcer...
   ⚠️  Blocking enforcer state not found
   ✅ Auto-fixed: Blocking enforcer initialized

================================================================================
🔧 ATTEMPTING AUTO-FIXES
================================================================================

🔧 Fixing: Blocking Enforcer - Enforcer not initialized
   ✅ Fixed!

✅ Auto-fixed 1 issue(s)

================================================================================
🚨 SYSTEM FAILURES DETECTED - WORK BLOCKED
================================================================================

🔴 CRITICAL FAILURES: 2

   [1] Python: Python command not found or not working
   📋 Fix Instructions:
      • Install Python from python.org
      • Add Python to PATH
      • Verify: python --version

   [2] Critical Files: 2 critical files missing
   📋 Fix Instructions:
      • Restore missing files from backup or repository
      • Run: cp -r claude-insight/scripts/* ~/.claude/memory/scripts/
      • Verify file permissions

================================================================================
🚨 WORK IS BLOCKED - FIX ALL FAILURES BEFORE CONTINUING
================================================================================
```

---

## 🔧 Auto-Fix Capabilities

### ✅ Can Auto-Fix:
1. **Blocking enforcer state** - Creates initial state file
2. **Session markers** - Marks session as started

### ❌ Cannot Auto-Fix (Manual Required):
1. **Python not installed** - Requires user installation
2. **Missing files** - Requires file restoration
3. **Git conflicts** - Requires manual resolution
4. **Daemon failures** - Requires daemon restart

---

## 📋 Integration Points

### 1. Session Start

**File:** `session-start.sh`

Add before any other checks:
```bash
# Run auto-fix enforcer FIRST
export PYTHONIOENCODING=utf-8
bash ~/.claude/memory/auto-fix-enforcer.sh
if [ $? -ne 0 ]; then
    echo "🚨 CRITICAL FAILURES DETECTED - FIX BEFORE CONTINUING"
    exit 1
fi
```

### 2. CLAUDE.md Execution Flow

**MANDATORY STEP 0 (BEFORE ALL OTHER STEPS):**
```
0. Auto-Fix Enforcement (BLOCKING - BEFORE EVERYTHING)
   → bash auto-fix-enforcer.sh
   → If exit code != 0: STOP, FIX, RETRY
   → Only proceed when all systems OK
```

### 3. Before Any Tool Call

Claude should check:
```python
# Pseudo-code
if about_to_use_tool():
    result = run_auto_fix_enforcer()
    if not result.all_ok:
        stop_and_report_failures()
        wait_for_user_to_fix()
        retry_enforcer()
```

### 4. Blocking Policy Enforcer Integration

The auto-fix enforcer works WITH blocking enforcer:
- Auto-fix: Checks system health, fixes issues
- Blocking enforcer: Ensures policy compliance

Both are MANDATORY and BLOCKING.

---

## 🔄 Execution Flow

```
User Request
     ↓
🚨 STEP 0: Auto-Fix Enforcement (BLOCKING)
     ↓
Check all systems (6 checks)
     ↓
Failures found? ──No──> ✅ Continue to Step 1
     │
    Yes
     ↓
Attempt auto-fix
     ↓
Re-check systems
     ↓
Still failing? ──No──> ✅ Continue to Step 1
     │
    Yes
     ↓
🚨 BLOCK ALL WORK
     ↓
Report failures + fix instructions
     ↓
Wait for user to fix
     ↓
User fixes issues
     ↓
Re-run enforcer
     ↓
All OK? ──Yes──> ✅ Continue to Step 1
     │
    No
     ↓
🚨 Keep blocking until fixed
```

---

## 🎯 Failure Priority Levels

| Level | Meaning | Action |
|-------|---------|--------|
| 🔴 **CRITICAL** | System cannot function | BLOCK immediately, must fix |
| 🟠 **HIGH** | Major degradation | BLOCK, should fix soon |
| 🟡 **MEDIUM** | Minor issues | WARN, fix when convenient |
| ℹ️ **INFO** | Informational only | Continue, no action needed |

---

## ⚙️ Exit Codes

| Code | Meaning |
|------|---------|
| 0 | All systems OK |
| 1 | General failure (non-critical) |
| 2+ | Number of critical failures |

**Usage in scripts:**
```bash
bash auto-fix-enforcer.sh
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
    echo "🚨 $EXIT_CODE critical failure(s) detected!"
    exit $EXIT_CODE
fi
```

---

## 🐛 Troubleshooting

### Enforcer Itself Fails

If the enforcer script fails to run:

1. **Check Python:**
   ```bash
   python --version
   ```

2. **Check file exists:**
   ```bash
   ls ~/.claude/memory/auto-fix-enforcer.py
   ```

3. **Run with error output:**
   ```bash
   export PYTHONIOENCODING=utf-8
   python ~/.claude/memory/auto-fix-enforcer.py 2>&1
   ```

### False Positives

If enforcer reports failures incorrectly:

1. Check state file:
   ```bash
   cat ~/.claude/memory/.blocking-state.json
   ```

2. Reset state:
   ```bash
   rm ~/.claude/memory/.blocking-state.json
   bash ~/.claude/memory/session-start.sh
   ```

### Auto-Fix Not Working

If auto-fix fails:

1. Run in check-only mode to see what's failing:
   ```bash
   bash ~/.claude/memory/auto-fix-enforcer.sh --check
   ```

2. Follow manual fix instructions from output

3. Re-run enforcer after manual fixes

---

## 📈 Future Enhancements

- [ ] Auto-fix Python PATH issues
- [ ] Auto-restore missing files from repository
- [ ] Auto-restart stopped daemons
- [ ] Auto-commit uncommitted changes (with user permission)
- [ ] Email/SMS alerts on critical failures
- [ ] Integration with dashboard for visual monitoring
- [ ] Rollback capability for failed auto-fixes

---

## 🔗 Related Systems

- **Blocking Policy Enforcer** - Policy compliance enforcement
- **Session Start** - Initial system setup
- **Plan Detector** - Subscription plan detection
- **Context Monitor** - Context usage monitoring

---

**Created:** 2026-02-16
**Version:** 1.0.0
**Status:** 🟢 Active
**Mandatory:** Yes (run before every action)

# Troubleshooting Guide - Claude Memory System
Quick reference for diagnosing and fixing issues.

---

**If something breaks, follow this sequence:**

### **Step 1: Check System Version**
```bash
cat ~/.claude/VERSION
cat ~/.claude/memory/current/VERSION
# Should show v3.0.0+ (system) and v3.0.1+ (memory)
```

### **Step 2: Check What's Current**
```bash
cat ~/.claude/memory/current/MANIFEST.md
# Shows all 15 current scripts with versions
# If this file doesn't exist, system is broken!
```

### **Step 3: Run Auto-Fix Enforcer**
```bash
export PYTHONIOENCODING=utf-8
export PYTHONUTF8=1
bash ~/.claude/memory/current/auto-fix-enforcer.sh

# Exit code 0 = OK
# Exit code != 0 = Issues found (read output for details)
```

### **Step 4: Test 3-Level Flow**
```bash
bash ~/.claude/memory/current/3-level-flow.sh "Test message"
# Should complete all 17 steps successfully
# If fails, check which step failed
```

### **Step 5: Check Test Report**
```bash
cat ~/.claude/memory/current/TEST-REPORT-2026-02-18.md 2>/dev/null
# See what was tested and results (if exists)
```

### **Step 6: View Logs**
```bash
tail -f ~/.claude/memory/logs/policy-hits.log
# Watch for errors in real-time
```

### **Step 7: Check Daemons**
```bash
python ~/.claude/memory/utilities/daemon-manager.py --status-all
# All daemons should be running
```

### **Step 8: Find Documentation**
```bash
# Quick reference (most important docs)
cat ~/.claude/memory/docs/QUICK-REFERENCE.md

# Complete index (118 docs)
cat ~/.claude/memory/docs/INDEX.md

# Search for specific topic
cat ~/.claude/memory/docs/INDEX.md | grep -i "error"
cat ~/.claude/memory/docs/INDEX.md | grep -i "troubleshoot"
```

### **Step 9: Rollback (if needed)**
```bash
# Old versions are archived (not deleted):
ls ~/.claude/memory/archived/2026-02-18/

# To rollback a specific script:
cp ~/.claude/memory/archived/2026-02-18/script-name.sh ~/.claude/memory/current/script-name.sh

# Example: rollback auto-fix-enforcer
cp ~/.claude/memory/archived/2026-02-18/auto-fix-enforcer.sh ~/.claude/memory/current/auto-fix-enforcer.sh
```

### **Common Issues & Fixes:**

| Issue | Fix |
|-------|-----|
| Script not found | Check path - use `current/` prefix! |
| Old path used | Update to `~/.claude/memory/current/script.sh` |
| Permission denied | `chmod +x ~/.claude/memory/current/*.sh` |
| Python encoding error | `export PYTHONIOENCODING=utf-8` |
| Version mismatch | Check `current/VERSION` matches expected |

### **Emergency Reset:**
```bash
# If everything is broken, start fresh session:
bash ~/.claude/memory/current/session-start.sh

# Then run auto-fix:
bash ~/.claude/memory/current/auto-fix-enforcer.sh

# Then test:
bash ~/.claude/memory/current/3-level-flow.sh "Test"
```

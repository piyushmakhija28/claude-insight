# 🚀 Quick Setup: Windows Auto-Start (3 Minutes)

**Tumhara idea bilkul sahi hai!** System startup pe automatic setup.

---

## ✅ What You'll Get

**After setup:**
```
Windows Login
    ↓
Automatic: 8 daemons start silently
    ↓
Always running, hamesha ready
    ↓
Tumhe kuch karna hi nahi padega! ✅
```

**Daemons that auto-start:**
1. ✅ Context monitoring
2. ✅ Session auto-save
3. ✅ Preference learning
4. ✅ Skill suggestions
5. ✅ Git auto-commit
6. ✅ Session pruning
7. ✅ Pattern detection
8. ✅ Failure learning

---

## 🎯 Setup (Choose One Method)

### Method 1: Automatic (Recommended - 1 Minute)

**Open PowerShell as Administrator:**
```
Win+X → "Windows PowerShell (Admin)"
```

**Run this command:**
```powershell
cd $env:USERPROFILE\.claude\memory
powershell -ExecutionPolicy Bypass -File setup-windows-startup.ps1
```

**That's it!** Script automatically:
- Creates scheduled task
- Registers with Windows
- Starts daemons now
- Tests everything

**Expected output:**
```
[1/4] Creating scheduled task... ✓
[2/4] Registering task... SUCCESS!
[3/4] Verifying task... READY
[4/4] Testing startup... 8/8 daemons running

Setup Complete!
```

---

### Method 2: Manual (5 Minutes)

**Step 1: Open Task Scheduler**
```
Win+R → type "taskschd.msc" → Enter
```

**Step 2: Create Task**
- Click "Create Task"
- Name: `ClaudeMemorySystemStartup`
- Description: `Auto-start Claude Memory daemons`

**Step 3: Trigger (When to run)**
- Triggers tab → New
- Begin: "At log on"
- User: (your username)
- OK

**Step 4: Action (What to run)**
- Actions tab → New
- Program: `wscript.exe`
- Arguments: `"C:\Users\techd\.claude\memory\windows-startup-silent.vbs"`
- OK

**Step 5: Settings**
- Settings tab
- ☑ Allow task to be run on demand
- ☑ Run as soon as possible after missed start
- OK

**Step 6: Test**
- Right-click task → Run
- Check: `python ~/.claude/memory/daemon-manager.py --status-all`
- Should show all 8 running

---

## 🧪 Verify Setup

**Check task exists:**
```powershell
Get-ScheduledTask -TaskName "ClaudeMemorySystemStartup"
```

**Check daemons running:**
```bash
python ~/.claude/memory/daemon-manager.py --status-all
```

**All 8 should show:** `"running": true`

---

## 🔄 Test Restart

**Full test:**
1. Restart Windows
2. Login
3. Wait 1 minute
4. Run: `python ~/.claude/memory/daemon-manager.py --status-all`
5. All 8 should be running automatically! ✅

---

## 📁 Files Created

All ready at `~/.claude/memory/`:

| File | Purpose |
|------|---------|
| `windows-startup.bat` | Main startup script |
| `windows-startup-silent.vbs` | Silent wrapper (no console) |
| `setup-windows-startup.ps1` | Auto-setup script |
| `AUTO-STARTUP-SETUP-GUIDE.md` | Detailed guide |
| `QUICK-SETUP-WINDOWS-AUTOSTART.md` | This quick guide |

---

## ⚙️ Manage Auto-Startup

**Disable (stop auto-starting):**
```powershell
Disable-ScheduledTask -TaskName "ClaudeMemorySystemStartup"
```

**Re-enable:**
```powershell
Enable-ScheduledTask -TaskName "ClaudeMemorySystemStartup"
```

**Remove completely:**
```powershell
Unregister-ScheduledTask -TaskName "ClaudeMemorySystemStartup" -Confirm:$false
```

**View in GUI:**
```
Win+R → taskschd.msc
→ Look for "ClaudeMemorySystemStartup"
```

---

## 🎯 Current Status

**Right now (before setup):**
- ✅ Daemons running (manually started)
- ❌ Will stop after Windows restart
- ❌ Need manual `startup-hook.sh` after reboot

**After setup:**
- ✅ Daemons auto-start on login
- ✅ Survive Windows restarts
- ✅ No manual commands needed
- ✅ Always running 24/7

---

## 📊 What Runs Automatically

| Daemon | Runs Every | Does What |
|--------|------------|-----------|
| context-daemon | 10 min | Checks context usage |
| session-auto-save | 15 min | Saves your sessions |
| preference-tracker | 20 min | Learns your patterns |
| skill-suggester | 5 min | Suggests skills |
| commit-daemon | 15 min | Auto-commits code |
| session-pruning | Monthly | Cleans old sessions |
| pattern-detection | Monthly | Finds patterns |
| failure-learning | 6 hours | Learns from errors |

**Total:** 8 processes running silently in background

---

## 💡 Benefits

### Before:
```
Windows restart
  → Daemons stopped
  → Manual: bash startup-hook.sh
  → Remember to do it
  → Sometimes forget ❌
```

### After:
```
Windows restart
  → Auto-start (1 min after login)
  → All 8 daemons running
  → Zero manual work
  → Always ready ✅
```

---

## 🐛 Troubleshooting

### Daemons not starting after restart?

**Check 1: Task enabled?**
```powershell
Get-ScheduledTask -TaskName "ClaudeMemorySystemStartup"
```
Should show "Ready"

**Check 2: Python in PATH?**
```bash
python --version
```
Should show version number

**Check 3: Files exist?**
```bash
ls ~/.claude/memory/windows-startup-silent.vbs
ls ~/.claude/memory/daemon-manager.py
```
Both should exist

**Fix:** Run setup again:
```powershell
powershell -ExecutionPolicy Bypass -File ~/.claude/memory/setup-windows-startup.ps1
```

---

## ✅ Quick Checklist

Setup complete when:

- [ ] Ran `setup-windows-startup.ps1` (or manual setup)
- [ ] Task shows in Task Scheduler
- [ ] All 8 daemons currently running
- [ ] Tested manual trigger (works)
- [ ] Restarted Windows (optional but recommended)
- [ ] Verified auto-start after login (works)

---

## 🎯 Summary

**One-time setup command:**
```powershell
powershell -ExecutionPolicy Bypass -File ~/.claude/memory/setup-windows-startup.ps1
```

**Result:**
- ✅ Runs automatically on Windows login
- ✅ Silent (no console window)
- ✅ All 8 daemons always running
- ✅ No manual intervention ever needed

**Verify anytime:**
```bash
python ~/.claude/memory/daemon-manager.py --status-all
```

**Tumhara idea implement ho gaya!** 🎉

Ab system restart ke baad bhi sab kuch automatically chalta rahega. Tumhe kuch karna hi nahi padega! 🚀

---

**Created:** 2026-02-15
**Status:** ✅ Ready to use
**Next:** Run setup command above

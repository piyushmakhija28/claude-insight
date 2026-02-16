# Windows Auto-Startup Setup Guide

**Date:** February 15, 2026
**Purpose:** Automatically start Claude Memory System daemons on Windows login
**Status:** ✅ Ready to Deploy

---

## 🎯 What This Does

**After setup:**
- ✅ All 8 daemons auto-start when Windows boots
- ✅ Runs silently in background (no console window)
- ✅ No manual intervention needed
- ✅ Works after system restart
- ✅ Always running, always ready

**Before setup:**
- ❌ Manual: `bash ~/.claude/memory/startup-hook.sh`
- ❌ Daemons stop after Windows restart
- ❌ Need to remember to start

---

## 🚀 Quick Setup (Recommended)

### Option 1: Automatic Setup (PowerShell)

**Step 1: Run setup script**

Open PowerShell as Administrator:
```powershell
# Right-click PowerShell -> Run as Administrator
cd ~/.claude/memory
powershell -ExecutionPolicy Bypass -File setup-windows-startup.ps1
```

**That's it!** Setup is automatic.

The script will:
1. Create scheduled task
2. Register with Windows Task Scheduler
3. Start daemons immediately
4. Verify everything works

**Expected output:**
```
[1/4] Creating scheduled task...
[2/4] Registering task with Windows Task Scheduler...
   SUCCESS: Task registered successfully!
[3/4] Verifying task...
   Task Name: ClaudeMemorySystemStartup
   State: Ready
[4/4] Testing startup...

All daemons running (8/8)
Setup Complete!
```

---

### Option 2: Manual Setup (Task Scheduler GUI)

**Step 1: Open Task Scheduler**
```
Press Win+R → type "taskschd.msc" → Enter
```

**Step 2: Create New Task**
- Click "Create Task" (not "Create Basic Task")
- Name: `ClaudeMemorySystemStartup`
- Description: `Automatically starts Claude Memory System daemons`
- Check: "Run whether user is logged on or not"
- Uncheck: "Run with highest privileges"

**Step 3: Add Trigger**
- Triggers tab → New
- Begin the task: "At log on"
- Specific user: (your username)
- Click OK

**Step 4: Add Action**
- Actions tab → New
- Action: "Start a program"
- Program/script: `wscript.exe`
- Arguments: `"C:\Users\techd\.claude\memory\windows-startup-silent.vbs"`
- Click OK

**Step 5: Configure Settings**
- Settings tab
- Check: "Allow task to be run on demand"
- Check: "Run task as soon as possible after scheduled start is missed"
- Check: "If task fails, restart every: 1 minute"
- Attempt to restart up to: 3 times
- Click OK

**Step 6: Test**
- Right-click task → Run
- Verify daemons started:
  ```bash
  python ~/.claude/memory/daemon-manager.py --status-all
  ```

---

## 🧪 Testing

### Test 1: Immediate Test
```bash
# Start daemons now
wscript.exe "C:\Users\techd\.claude\memory\windows-startup-silent.vbs"

# Wait 5 seconds
timeout /t 5

# Check status
python ~/.claude/memory/daemon-manager.py --status-all
```

**Expected:** All 8 daemons running

### Test 2: Restart Test
```
1. Restart Windows
2. Wait 1 minute after login
3. Check status:
   python ~/.claude/memory/daemon-manager.py --status-all
```

**Expected:** All 8 daemons running automatically

### Test 3: Manual Trigger Test
```
1. Open Task Scheduler
2. Find "ClaudeMemorySystemStartup"
3. Right-click → Run
4. Check status
```

**Expected:** All 8 daemons running

---

## 📁 Files Created

| File | Purpose | Location |
|------|---------|----------|
| `windows-startup.bat` | Startup batch script | ~/.claude/memory/ |
| `windows-startup-silent.vbs` | Silent wrapper (no console) | ~/.claude/memory/ |
| `setup-windows-startup.ps1` | Automatic setup script | ~/.claude/memory/ |
| `AUTO-STARTUP-SETUP-GUIDE.md` | This guide | ~/.claude/memory/ |

---

## 🔍 Verification

### Check Task Status
```powershell
Get-ScheduledTask -TaskName "ClaudeMemorySystemStartup"
```

**Expected output:**
```
TaskName                    State
--------                    -----
ClaudeMemorySystemStartup   Ready
```

### Check Daemon Status
```bash
python ~/.claude/memory/daemon-manager.py --status-all
```

**Expected:** JSON with all 8 daemons showing `"running": true`

### View Logs
```bash
# Check if daemons started at login
tail -20 ~/.claude/memory/logs/policy-hits.log
```

**Expected:** Recent entries with startup timestamps

---

## ⚙️ Configuration

### Change Startup Behavior

**Disable auto-startup:**
```powershell
# Option 1: Disable task
Disable-ScheduledTask -TaskName "ClaudeMemorySystemStartup"

# Option 2: Delete task
Unregister-ScheduledTask -TaskName "ClaudeMemorySystemStartup" -Confirm:$false
```

**Re-enable:**
```powershell
Enable-ScheduledTask -TaskName "ClaudeMemorySystemStartup"
```

**Delay startup (wait 2 minutes after login):**
```
Task Scheduler → Edit task → Triggers → Edit
→ Delay task for: 2 minutes
```

---

## 🐛 Troubleshooting

### Task doesn't run at login

**Check 1: Task enabled?**
```powershell
Get-ScheduledTask -TaskName "ClaudeMemorySystemStartup" | Select State
```
Should show "Ready"

**Check 2: User account correct?**
```
Task Scheduler → Task properties → General
→ Should show your username
```

**Check 3: Path correct?**
```
Task Scheduler → Task properties → Actions
→ Should point to windows-startup-silent.vbs
```

### Daemons not starting

**Check 1: Python in PATH?**
```bash
python --version
```
Should show Python version

**Check 2: Files exist?**
```bash
ls ~/.claude/memory/daemon-manager.py
ls ~/.claude/memory/*.py
```
All should exist

**Check 3: Manual start works?**
```bash
python ~/.claude/memory/daemon-manager.py --start-all
```
Should start successfully

### Console window appears (not silent)

**Issue:** Using .bat instead of .vbs

**Fix:** Ensure Task Scheduler action points to:
```
wscript.exe "path\to\windows-startup-silent.vbs"
```
NOT:
```
cmd.exe /c "path\to\windows-startup.bat"
```

---

## 📊 What Runs Automatically

Once setup, these 8 daemons auto-start on every Windows login:

| Daemon | Interval | Purpose |
|--------|----------|---------|
| context-daemon | 10 min | Monitor context usage |
| session-auto-save-daemon | 15 min | Auto-save sessions |
| preference-auto-tracker | 20 min | Learn preferences |
| skill-auto-suggester | 5 min | Suggest skills |
| commit-daemon | 15 min | Auto-commit changes |
| session-pruning-daemon | Monthly | Clean old sessions |
| pattern-detection-daemon | Monthly | Detect patterns |
| failure-prevention-daemon | 6 hours | Learn from failures |

**Total:** 8 daemons running 24/7

---

## 💡 Benefits

### Before Auto-Startup:
- ❌ Manual: `bash startup-hook.sh` after every restart
- ❌ Forget to start = no automation
- ❌ Daemons stop randomly = need to restart
- ❌ Need to remember commands

### After Auto-Startup:
- ✅ Automatic: Starts on Windows login
- ✅ Always running = full automation
- ✅ Survives restarts = reliable
- ✅ Zero manual intervention = effortless

---

## 🎯 Summary

**Setup Command (One-time):**
```powershell
powershell -ExecutionPolicy Bypass -File ~/.claude/memory/setup-windows-startup.ps1
```

**After Setup:**
- Restart Windows → Daemons auto-start ✅
- Login to Windows → Daemons auto-start ✅
- No manual commands needed ✅
- Always running 24/7 ✅

**Verify Anytime:**
```bash
python ~/.claude/memory/daemon-manager.py --status-all
```

**That's it!** Full automation achieved. 🚀

---

## 📝 Logs

**Startup logs:**
```bash
# View daemon startup activity
tail -50 ~/.claude/memory/logs/policy-hits.log | grep startup

# View daemon health
tail -20 ~/.claude/memory/logs/daemons/context-daemon.log
```

**Task Scheduler logs:**
```
Event Viewer → Windows Logs → Application
→ Filter by source: "Task Scheduler"
```

---

## ✅ Checklist

Before marking as complete:

- [ ] Created startup scripts (bat, vbs, ps1)
- [ ] Ran setup-windows-startup.ps1
- [ ] Task registered in Task Scheduler
- [ ] Task shows "Ready" state
- [ ] All 8 daemons running
- [ ] Tested manual trigger (works)
- [ ] Tested restart (works)
- [ ] Verified logs (recent activity)
- [ ] No console windows appear
- [ ] Silent background operation

**If all checked:** Setup complete! ✅

---

**Guide Created:** 2026-02-15 20:52 UTC
**Status:** Ready to deploy
**Next Step:** Run `setup-windows-startup.ps1`

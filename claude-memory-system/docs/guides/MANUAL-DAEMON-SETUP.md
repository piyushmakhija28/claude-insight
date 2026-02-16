# Manual Daemon Permanent Setup

## Problem
Daemons run manually but not permanently. Windows restart hone pe band ho jate hain.

## Solution: Windows Task Scheduler Setup

### Step 1: Open Task Scheduler
```
Windows Key + R
Type: taskschd.msc
Press Enter
```

### Step 2: Create Basic Task
1. Click "Create Basic Task" (right panel)
2. Name: `ClaudeMemoryDaemons`
3. Description: `Auto-start Claude memory system daemons on login`
4. Click "Next"

### Step 3: Set Trigger
1. Select: "When I log on"
2. Click "Next"

### Step 4: Set Action
1. Select: "Start a program"
2. Click "Next"
3. Program/script: `C:\Program Files\Git\bin\bash.exe`
4. Arguments: `C:\Users\techd\.claude\memory\startup-hook.sh`
5. Click "Next"

### Step 5: Finish
1. Check: "Open Properties dialog when I click Finish"
2. Click "Finish"

### Step 6: Advanced Settings
In the Properties dialog that opens:
1. **General tab:**
   - Check: "Run with highest privileges"
   - Check: "Run whether user is logged on or not"

2. **Conditions tab:**
   - UNCHECK: "Start only if on AC power"
   - UNCHECK: "Stop if computer switches to battery"

3. **Settings tab:**
   - Check: "Allow task to be run on demand"
   - Check: "Run task as soon as possible after scheduled start is missed"
   - UNCHECK: "Stop task if it runs longer than"

4. Click "OK"

### Step 7: Test
```powershell
# Run task manually to test
schtasks /run /tn "ClaudeMemoryDaemons"

# Wait 10 seconds, then check
python C:\Users\techd\.claude\memory\daemon-manager.py --status-all

# Should show 9/9 daemons running
```

### Step 8: Verify Auto-Start
```powershell
# Check task is scheduled
schtasks /query /tn "ClaudeMemoryDaemons" /fo LIST

# Should show:
# Status: Ready
# Logon Mode: Interactive/Background
# Next Run Time: At log on
```

---

## Alternative: PowerShell Direct Setup

Run this in **PowerShell (Admin)**:

```powershell
$action = New-ScheduledTaskAction `
    -Execute "C:\Program Files\Git\bin\bash.exe" `
    -Argument "C:\Users\techd\.claude\memory\startup-hook.sh"

$trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME

$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable

$principal = New-ScheduledTaskPrincipal `
    -UserId $env:USERNAME `
    -RunLevel Highest

Register-ScheduledTask `
    -TaskName "ClaudeMemoryDaemons" `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Principal $principal `
    -Force
```

---

## Verification

After setup, verify permanent running:

```bash
# Check daemons
python ~/.claude/memory/daemon-manager.py --status-all

# Should show 9/9 running
# PIDs should persist across sessions
```

---

## Watchdog (Optional)

For auto-restart of dead daemons, create another task:

1. Name: `ClaudeDaemonWatchdog`
2. Trigger: At log on
3. Action: `powershell.exe -File C:\Users\techd\.claude\memory\daemon-watchdog.ps1`
4. Settings: Run indefinitely, no time limit

Watchdog script checks every 5 minutes and restarts dead daemons.

---

## Status

- ✅ Context threshold FIXED (70% triggers auto-compact)
- ⏳ Task Scheduler MANUAL SETUP NEEDED
- ✅ Wrapper scripts created
- ✅ Startup hook ready

**Action Required:** Follow Step 1-8 above to complete permanent setup!

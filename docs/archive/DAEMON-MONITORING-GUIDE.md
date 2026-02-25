# 🤖 Daemon Monitoring & Management Guide

**Last Updated:** 2026-02-17
**Session:** SESSION-20260217-121025-AFV3

---

## 📋 Overview

The Claude Memory System runs **9 background daemons** that provide continuous automation and monitoring. These daemons run 24/7 from Windows startup to shutdown.

---

## 🎯 The 9 Daemons

| # | Daemon Name | Purpose | Default Interval | Status File |
|---|-------------|---------|------------------|-------------|
| 1 | **context-daemon** | Monitor context usage, auto-cleanup | **2 minutes** ⚡ | `.context-daemon.pid` |
| 2 | **session-auto-save-daemon** | Auto-save session state | Variable | `.session-save-daemon.pid` |
| 3 | **preference-auto-tracker** | Learn user preferences | Variable | `.preference-tracker.pid` |
| 4 | **skill-auto-suggester** | Suggest relevant skills | Variable | `.skill-suggester.pid` |
| 5 | **commit-daemon** | Auto-commit code changes | Variable | `.commit-daemon.pid` |
| 6 | **session-pruning-daemon** | Clean old sessions | Variable | `.session-pruning.pid` |
| 7 | **pattern-detection-daemon** | Detect usage patterns | Variable | `.pattern-daemon.pid` |
| 8 | **failure-prevention-daemon** | Learn from failures, prevent recurring | **10 minutes** ⚡ | `.failure-daemon.pid` |
| 9 | **auto-recommendation-daemon** | Generate real-time recommendations | **5 seconds** ⚡ | `.auto-recommendation-daemon.pid` |

⚡ = Recently optimized for real-time monitoring (was hours/minutes, now seconds/minutes)

---

## 🚀 Auto-Start on Windows Boot

### How It Works

```
Windows Startup
    ↓
C:\Users\techd\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\
    ↓
Claude Memory System.lnk
    ↓
windows-startup-silent.vbs (runs hidden, no window)
    ↓
~/.claude/memory/windows-startup.bat
    ↓
daemon-manager.py --start-all
    ↓
All 9 daemons start automatically
```

### Files Involved

1. **Startup Link:**
   ```
   C:\Users\techd\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\Claude Memory System.lnk
   ```

2. **VBS Script (Silent Runner):**
   ```
   ~/.claude/memory/scripts/windows-startup-silent.vbs
   ```

3. **Batch Script:**
   ```
   ~/.claude/memory/scripts/windows-startup.bat
   ```

4. **Daemon Manager:**
   ```
   ~/.claude/memory/utilities/daemon-manager.py
   ```

---

## ✅ Checking Daemon Status

### Quick Status Check

```bash
# Check all 9 daemons
python ~/.claude/memory/utilities/daemon-manager.py --status-all

# Pretty table format
python ~/.claude/memory/utilities/daemon-manager.py --status-all --format table

# JSON format
python ~/.claude/memory/utilities/daemon-manager.py --status-all --format json
```

### Check Specific Daemon

```bash
# Context daemon
python ~/.claude/memory/01-sync-system/context-management/context-daemon.py --status

# Failure prevention daemon
python ~/.claude/memory/03-execution-system/failure-prevention/failure-prevention-daemon.py --status

# Auto-recommendation daemon
python ~/.claude/memory/03-execution-system/07-recommendations/auto-recommendation-daemon.py status
```

### At Session Start

```bash
# Runs automatically in session-start.sh
bash ~/.claude/memory/session-start.sh

# Shows:
# - Which daemons are running (with PIDs)
# - Which daemons are stopped
# - Overall health: X / 9 running
```

---

## 🔄 Starting/Stopping/Restarting Daemons

### Start All Daemons

```bash
python ~/.claude/memory/utilities/daemon-manager.py --start-all
```

### Stop All Daemons

```bash
python ~/.claude/memory/utilities/daemon-manager.py --stop-all
```

### Restart All Daemons

```bash
python ~/.claude/memory/utilities/daemon-manager.py --restart-all
```

### Start/Stop/Restart Specific Daemon

```bash
# Start
python ~/.claude/memory/utilities/daemon-manager.py --start context-daemon

# Stop
python ~/.claude/memory/utilities/daemon-manager.py --stop context-daemon

# Restart
python ~/.claude/memory/utilities/daemon-manager.py --restart context-daemon
```

---

## 📊 Daemon Intervals & Real-Time Monitoring

### Recent Optimizations (2026-02-17)

**BEFORE (❌ Too Slow):**
- failure-prevention-daemon: **6 HOURS**
- context-daemon: **10 minutes**

**AFTER (✅ Real-Time):**
- failure-prevention-daemon: **10 minutes** (36x faster!)
- context-daemon: **2 minutes** (5x faster!)
- auto-recommendation-daemon: **5 seconds** (continuous)

### Why This Matters

**Old Way (Interval-Based, Long Sleeps):**
```
Daemon checks → Sleeps 6 hours → Checks again
Problem: If system down during sleep, checks missed!
```

**New Way (Frequent Checks):**
```
Daemon checks → Sleeps 10 minutes → Checks again
Benefit: Near real-time monitoring, catches issues fast!
```

### Customizing Intervals

**Context Daemon:**
```bash
# Default: 2 minutes
python context-daemon.py --interval 2

# Custom: 1 minute (faster)
python context-daemon.py --interval 1

# Custom: 5 minutes (slower)
python context-daemon.py --interval 5
```

**Failure Prevention Daemon:**
```bash
# Default: 0.167 hours (10 minutes)
python failure-prevention-daemon.py --interval 0.167

# Custom: 5 minutes
python failure-prevention-daemon.py --interval 0.083

# Custom: 30 minutes
python failure-prevention-daemon.py --interval 0.5
```

---

## 📁 Daemon Files & Logs

### PID Files (Process IDs)

**Location:** `~/.claude/memory/.pids/`

**Format:** `{daemon-name}.pid`

**Example:**
```bash
cat ~/.claude/memory/.pids/context-daemon.pid
# Output: 11584
```

### Log Files

**Location:** `~/.claude/memory/logs/daemons/`

**Format:** `{daemon-name}.log`

**View Logs:**
```bash
# Last 50 lines
tail -50 ~/.claude/memory/logs/daemons/context-daemon.log

# Last 20 lines
tail -20 ~/.claude/memory/logs/daemons/failure-prevention-daemon.log

# Follow live (real-time)
tail -f ~/.claude/memory/logs/daemons/auto-recommendation-daemon.log

# All daemon logs
ls -lh ~/.claude/memory/logs/daemons/
```

---

## 🚨 Troubleshooting

### Problem: Daemon Not Running

**Check:**
```bash
python daemon-manager.py --status {daemon-name}
```

**Fix:**
```bash
# Start it
python daemon-manager.py --start {daemon-name}

# Or restart all
python daemon-manager.py --restart-all
```

### Problem: Stale PID File

**Symptom:**
```
Status: Stale PID file (process XXXXX not running)
```

**Fix:**
```bash
# Remove stale PID
rm ~/.claude/memory/.pids/{daemon-name}.pid

# Restart daemon
python daemon-manager.py --start {daemon-name}
```

### Problem: Daemon Crashes Immediately

**Check Logs:**
```bash
tail -100 ~/.claude/memory/logs/daemons/{daemon-name}.log
```

**Common Causes:**
1. **UnicodeDecodeError** → Check subprocess calls have `encoding='utf-8'`
2. **Wrong paths** → Check script paths are absolute and correct
3. **Missing files** → Check required files exist
4. **Python version** → Ensure Python 3.7+ installed

**Fix:**
```bash
# Check Python
python --version

# Verify paths
ls -la ~/.claude/memory/03-execution-system/failure-prevention/

# Check for encoding issues in logs
grep -i "unicode\|encoding" ~/.claude/memory/logs/daemons/*.log
```

### Problem: Session-Start Shows Parse Error

**Symptom:**
```
❌ CRITICAL: Could not parse recommendations
This is a BLOCKING FAILURE - System cannot proceed!
```

**Cause:**
Auto-recommendation daemon stopped or recommendations file corrupted.

**Fix:**
```bash
# 1. Restart auto-recommendation daemon
python ~/.claude/memory/03-execution-system/07-recommendations/auto-recommendation-daemon.py restart

# 2. Or delete corrupted file
rm ~/.claude/memory/.last-automation-check.json

# 3. Re-run session start
bash ~/.claude/memory/session-start.sh
```

### Problem: Daemons Don't Start on Boot

**Check Startup Link:**
```bash
ls -la "C:/Users/techd/AppData/Roaming/Microsoft/Windows/Start Menu/Programs/Startup/" | grep Claude
```

**Should see:**
```
Claude Memory System.lnk
```

**If missing, recreate:**
```bash
# Copy from backup
cp ~/.claude/memory/scripts/startup-backup/Claude\ Memory\ System.lnk \
   "C:/Users/techd/AppData/Roaming/Microsoft/Windows/Start Menu/Programs/Startup/"
```

### Problem: Access Denied When Stopping Daemon

**Symptom:**
```
ERROR: The process with PID XXXXX could not be terminated.
Reason: Access is denied.
```

**Fix:**
```bash
# Run as administrator or
# Let it restart on next boot (new interval will apply)
```

---

## 📊 Health Monitoring

### Overall System Health

```bash
python ~/.claude/memory/utilities/daemon-manager.py --health
```

**Output:**
```json
{
  "total_daemons": 9,
  "running": 8,
  "stopped": 1,
  "health_score": 88.9,
  "status": "HEALTHY"
}
```

### Health Score Interpretation

| Score | Status | Action |
|-------|--------|--------|
| 100% | 🟢 **PERFECT** | All daemons running |
| 90-99% | 🟡 **GOOD** | 1 daemon down, investigate |
| 70-89% | 🟠 **WARNING** | 2+ daemons down, restart |
| <70% | 🔴 **CRITICAL** | Restart all daemons immediately |

---

## 🎯 Best Practices

### 1. **Daily Health Check**
```bash
# Quick check each morning
python daemon-manager.py --status-all --format table
```

### 2. **Monitor Logs for Errors**
```bash
# Check for errors weekly
grep -i "error\|failed\|critical" ~/.claude/memory/logs/daemons/*.log
```

### 3. **Restart After System Updates**
```bash
# After Windows updates
python daemon-manager.py --restart-all
```

### 4. **Keep Intervals Short**
- Context daemon: 1-2 minutes
- Failure prevention: 5-10 minutes
- Auto-recommendation: 5-10 seconds

### 5. **Don't Manually Kill Processes**
Always use daemon manager:
```bash
# ❌ WRONG
kill -9 12345

# ✅ CORRECT
python daemon-manager.py --stop {daemon-name}
```

---

## 📖 Quick Reference

### Essential Commands

```bash
# Status check
python daemon-manager.py --status-all

# Restart all
python daemon-manager.py --restart-all

# View logs
tail -f ~/.claude/memory/logs/daemons/{daemon-name}.log

# Session start (checks everything)
bash ~/.claude/memory/session-start.sh
```

### Critical Files

```bash
# Startup
~/.claude/memory/scripts/windows-startup-silent.vbs
~/.claude/memory/scripts/windows-startup.bat

# Manager
~/.claude/memory/utilities/daemon-manager.py

# PIDs
~/.claude/memory/.pids/*.pid

# Logs
~/.claude/memory/logs/daemons/*.log
```

---

## 🔄 After Interval Changes

When you change daemon intervals (like we did for failure-prevention and context daemons), you need to restart them:

```bash
# Stop old daemon
python daemon-manager.py --stop {daemon-name}

# Start with new interval
python {daemon-path}/{daemon-name}.py --interval {new-value}

# Or restart all to pick up new defaults
python daemon-manager.py --restart-all
```

**New intervals apply:**
- Immediately after manual restart
- Automatically on next Windows boot

---

## ✅ Summary

**What You Need to Know:**

1. **9 daemons run 24/7** from Windows startup
2. **Auto-start on boot** via Windows Startup folder
3. **Real-time monitoring** with short intervals (seconds/minutes)
4. **Parse errors now FAIL** (not just warn)
5. **Check status** anytime with `daemon-manager.py`
6. **View logs** in `~/.claude/memory/logs/daemons/`
7. **Restart after changes** or system updates

**Key Commands:**
```bash
# Status
python daemon-manager.py --status-all

# Restart
python daemon-manager.py --restart-all

# Logs
tail -f ~/.claude/memory/logs/daemons/*.log
```

---

**Status:** 🟢 **FULLY DOCUMENTED**
**Daemons:** 9 total, optimized for real-time monitoring
**Startup:** ✅ Configured for Windows boot
**Parse Error:** ✅ Now fails properly (blocking)

---

**Guide Created:** 2026-02-17
**Author:** Claude Sonnet 4.5
**Session:** SESSION-20260217-121025-AFV3

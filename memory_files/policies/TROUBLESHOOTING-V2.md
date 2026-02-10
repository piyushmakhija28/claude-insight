# Troubleshooting Guide: Memory System v2.0

## Quick Diagnostic

**First step for any issue**: Run the diagnostic script

```bash
bash ~/.claude/memory/verify-system.sh
```

If it returns "FULLY OPERATIONAL", the core system is fine. Skip to specific issue sections below.

If it returns "VERIFICATION FAILED", note which checks failed and proceed accordingly.

---

## Common Issues

### 1. Daemons Not Starting

#### Symptom
```bash
python ~/.claude/memory/daemon-manager.py --status-all
```
Shows "NOT RUNNING" for one or more daemons.

#### Causes & Solutions

**Cause 1: Python executable not found**

Check:
```bash
which python
python --version
```

Solution:
```bash
# Linux/Mac: Ensure python3 is available
sudo ln -s /usr/bin/python3 /usr/bin/python

# Windows: Add Python to PATH
# Control Panel → System → Environment Variables → Path
```

**Cause 2: Port already in use (rare)**

Check:
```bash
# See if any old daemon processes still running
ps aux | grep daemon | grep -v grep
```

Solution:
```bash
# Kill old processes
pkill -f "context-daemon"
pkill -f "failure-prevention-daemon"
# etc.

# Restart v2
bash ~/.claude/memory/startup-hook-v2.sh
```

**Cause 3: Permissions issue**

Check:
```bash
ls -la ~/.claude/memory/*.py
```

Solution:
```bash
# Make scripts executable
chmod +x ~/.claude/memory/*.py
chmod +x ~/.claude/memory/*.sh
```

**Cause 4: Missing directories**

Check:
```bash
ls -la ~/.claude/memory/.pids/
ls -la ~/.claude/memory/.restarts/
ls -la ~/.claude/memory/logs/daemons/
```

Solution:
```bash
# Create missing directories
mkdir -p ~/.claude/memory/.pids
mkdir -p ~/.claude/memory/.restarts
mkdir -p ~/.claude/memory/logs/daemons
mkdir -p ~/.claude/memory/.cache
mkdir -p ~/.claude/memory/.state
```

**Cause 5: Import errors**

Check daemon logs:
```bash
tail -50 ~/.claude/memory/logs/daemons/daemon-manager.log
```

Look for "ModuleNotFoundError" or "ImportError".

Solution:
```bash
# Install missing dependencies
pip install psutil  # Optional but recommended
```

---

### 2. Health Monitor Shows 0% Score

#### Symptom
```bash
python ~/.claude/memory/pid-tracker.py --health
```
Returns: `{health_score: 0.0}`

#### Causes & Solutions

**Cause 1: PID files missing**

Check:
```bash
ls -la ~/.claude/memory/.pids/
```

Should show 8 .pid files.

Solution:
```bash
# Restart all daemons (creates PID files)
python ~/.claude/memory/daemon-manager.py --stop-all
python ~/.claude/memory/daemon-manager.py --start-all
```

**Cause 2: Stale PID files**

PIDs in files don't match running processes.

Check:
```bash
# Check if PIDs are actually running
for pid in $(cat ~/.claude/memory/.pids/*.pid); do
    ps -p $pid > /dev/null && echo "PID $pid: RUNNING" || echo "PID $pid: DEAD"
done
```

Solution:
```bash
# Clean up stale PIDs
rm ~/.claude/memory/.pids/*.pid

# Restart daemons
bash ~/.claude/memory/startup-hook-v2.sh
```

**Cause 3: psutil not installed**

Tracker falls back to platform commands which may fail.

Check:
```bash
python -c "import psutil; print('OK')" 2>&1
```

Solution:
```bash
# Install psutil
pip install psutil
```

---

### 3. Failure KB Not Loading

#### Symptom
```bash
python ~/.claude/memory/pre-execution-checker.py --stats
```
Returns: `{total_patterns: 0}`

#### Causes & Solutions

**Cause 1: KB file missing**

Check:
```bash
ls -lh ~/.claude/memory/failure-kb.json
```

Solution:
```bash
# Create default KB structure
cat > ~/.claude/memory/failure-kb.json << 'EOF'
{
  "Bash": [],
  "Edit": [],
  "Read": [],
  "Grep": [],
  "Write": []
}
EOF

# Populate from existing logs
python ~/.claude/memory/failure-detector-v2.py --analyze logs/policy-hits.log
python ~/.claude/memory/failure-pattern-extractor.py --update-kb
```

**Cause 2: JSON syntax error**

Check:
```bash
python -m json.tool ~/.claude/memory/failure-kb.json
```

If error, KB has invalid JSON.

Solution:
```bash
# Backup corrupted KB
cp ~/.claude/memory/failure-kb.json ~/.claude/memory/failure-kb-broken.json

# Restore from backup or create fresh
# (See Cause 1 solution)
```

**Cause 3: Permissions**

Check:
```bash
ls -la ~/.claude/memory/failure-kb.json
```

Solution:
```bash
chmod 644 ~/.claude/memory/failure-kb.json
```

---

### 4. Context Not Optimizing

#### Symptom
Context usage stays high despite optimization system.

#### Causes & Solutions

**Cause 1: Pre-execution optimizer not being called**

Check logs:
```bash
grep "pre-execution-optimizer" ~/.claude/memory/logs/policy-hits.log
```

If no entries, optimizer isn't being invoked.

Solution:
```bash
# Verify optimizer works
python ~/.claude/memory/pre-execution-optimizer.py --test-large-file

# Check CLAUDE.md has CONTEXT OPTIMIZATION section
grep "CONTEXT OPTIMIZATION" ~/.claude/CLAUDE.md
```

**Cause 2: Cache not working**

Check cache:
```bash
python ~/.claude/memory/context-cache.py --stats
```

Should show cached entries.

Solution:
```bash
# Clear and rebuild cache
rm -rf ~/.claude/memory/.cache/summaries
mkdir -p ~/.claude/memory/.cache/summaries

# Cache will rebuild on next use
```

**Cause 3: Session state not being used**

Check:
```bash
ls -lh ~/.claude/memory/.state/session-state.json
```

Solution:
```bash
# Initialize session state
python ~/.claude/memory/session-state.py --init
```

---

### 5. Model Selection Giving Wrong Results

#### Symptom
```bash
python ~/.claude/memory/model-selection-enforcer.py --analyze "Find all files"
```
Returns wrong model (not haiku).

#### Causes & Solutions

**Cause 1: Ambiguous request**

"Find all files to implement" has conflicting keywords.

Solution:
```bash
# Break into two analyses
python ~/.claude/memory/model-selection-enforcer.py --analyze "Find all files"
# Should return haiku

python ~/.claude/memory/model-selection-enforcer.py --analyze "Implement feature"
# Should return sonnet
```

**Cause 2: Low confidence**

Check confidence score in output. If <0.5, may be wrong.

Solution:
```bash
# Review keyword matching
python ~/.claude/memory/model-selection-enforcer.py --analyze "your query" --verbose
```

**Cause 3: Need to update keywords**

Solution:
Edit `model-selection-enforcer.py` and add new keywords to KEYWORD_MAP.

---

### 6. Auto-Restart Not Working

#### Symptom
Daemon crashes but doesn't auto-restart.

#### Causes & Solutions

**Cause 1: Health monitor not running**

Check:
```bash
python ~/.claude/memory/daemon-manager.py --status health-monitor
```

Solution:
```bash
python ~/.claude/memory/daemon-manager.py --start health-monitor
```

**Cause 2: Rate limit reached**

Max 3 restarts per hour per daemon.

Check:
```bash
cat ~/.claude/memory/.restarts/context-daemon_restart_history.json
```

If 3+ restarts in last hour, rate limited.

Solution:
```bash
# Wait 1 hour for rate limit reset, OR
# Manually restart
python ~/.claude/memory/daemon-manager.py --start context-daemon
```

**Cause 3: Cooldown period**

60s cooldown between restarts.

Solution:
Wait 60 seconds, then health monitor will auto-restart.

---

### 7. Consultation Tracker Not Auto-Skipping

#### Symptom
Same question asked repeatedly despite 2+ consistent answers.

#### Causes & Solutions

**Cause 1: Not logged properly**

Check:
```bash
python ~/.claude/memory/consultation-tracker.py --history planning_mode
```

Should show 2+ entries with same choice.

Solution:
```bash
# Manually log consultations
python ~/.claude/memory/consultation-tracker.py --log \
    "planning_mode" "Should I enter plan mode?" '["yes","no"]' "yes"

# Repeat for second time
python ~/.claude/memory/consultation-tracker.py --log \
    "planning_mode" "Should I enter plan mode?" '["yes","no"]' "yes"
```

**Cause 2: Different decision types**

Each unique decision type tracked separately.

Check:
```bash
python ~/.claude/memory/consultation-tracker.py --stats
```

Solution:
Use consistent decision_type strings in logs.

**Cause 3: Preferences file corrupted**

Check:
```bash
python -m json.tool ~/.claude/memory/consultation-preferences.json
```

Solution:
```bash
# Backup and reset
cp ~/.claude/memory/consultation-preferences.json ~/.claude/memory/consultation-preferences-backup.json
echo '{}' > ~/.claude/memory/consultation-preferences.json
```

---

### 8. Dashboard Not Showing Data

#### Symptom
```bash
bash ~/.claude/memory/dashboard-v2.sh
```
Shows "ERROR" or "Unknown" for sections.

#### Causes & Solutions

**Cause 1: Scripts not executable**

Solution:
```bash
chmod +x ~/.claude/memory/dashboard-v2.sh
chmod +x ~/.claude/memory/*.py
```

**Cause 2: Missing data files**

Check which section fails and check corresponding file:
- Daemon Health → `.pids/*.pid`
- Context Status → `.cache/`, `.state/`
- Failure Prevention → `failure-kb.json`
- Model Usage → `logs/model-usage.log`

Solution:
```bash
# Run startup to initialize all systems
bash ~/.claude/memory/startup-hook-v2.sh
```

**Cause 3: Path issues**

Check:
```bash
MEMORY_DIR=~/.claude/memory
ls -la $MEMORY_DIR
```

Solution:
Ensure `MEMORY_DIR` variable in dashboard-v2.sh matches your actual path.

---

### 9. Tests Failing

#### Symptom
```bash
python ~/.claude/memory/test-all-phases.py
```
Shows "FAILED" for one or more phases.

#### Diagnosis

Run tests with details:
```bash
python ~/.claude/memory/test-all-phases.py 2>&1 | tee test-output.log
```

Review `test-output.log` for specific errors.

#### Solutions by Phase

**Phase 1 Test Fails**:
```bash
# Test each component individually
python ~/.claude/memory/pre-execution-optimizer.py --test-large-file
python ~/.claude/memory/context-cache.py --stats
python ~/.claude/memory/session-state.py --summary
python ~/.claude/memory/context-monitor-v2.py --current-status
```

**Phase 2 Test Fails**:
```bash
# Test daemon infrastructure
python ~/.claude/memory/test-phase2-infrastructure.py
# Review specific failure
```

**Phase 3 Test Fails**:
```bash
# Test failure detection
python ~/.claude/memory/failure-detector-v2.py --stats
python ~/.claude/memory/pre-execution-checker.py --stats
```

**Phase 4 Test Fails**:
```bash
# Test policy automation
python ~/.claude/memory/model-selection-enforcer.py --test
python ~/.claude/memory/consultation-tracker.py --stats
python ~/.claude/memory/core-skills-enforcer.py --stats
```

**Phase 5 Test Fails**:
```bash
# Check integration
bash ~/.claude/memory/dashboard-v2.sh
bash ~/.claude/memory/verify-system.sh
```

---

### 10. High Resource Usage

#### Symptom
System using too much CPU or memory.

#### Diagnosis

Check daemon resource usage:
```bash
# Linux/Mac
ps aux | grep daemon | grep -v grep

# Windows (PowerShell)
Get-Process | Where-Object {$_.ProcessName -like "*python*"}
```

#### Solutions

**High Memory**:
```bash
# Check for memory leaks in logs
tail -100 ~/.claude/memory/logs/daemons/*.log | grep -i "memory\|leak"

# Restart daemons to free memory
python ~/.claude/memory/daemon-manager.py --restart-all
```

**High CPU**:
```bash
# Check which daemon is consuming CPU
top -p $(cat ~/.claude/memory/.pids/*.pid | tr '\n' ',')

# Check health monitor interval (default 5 min)
# Edit health-monitor-daemon.py if needed to increase interval
```

**High Disk I/O**:
```bash
# Check log sizes
du -sh ~/.claude/memory/logs/*

# Old logs should auto-rotate at 10MB
# If not, manually clean
find ~/.claude/memory/logs -name "*.log" -size +20M -delete
```

---

## Error Messages

### "UnicodeEncodeError: 'charmap' codec can't encode"

**Cause**: Windows console encoding issue with Unicode characters.

**Solution**:
```bash
# Set UTF-8 encoding (Windows PowerShell)
$Env:PYTHONIOENCODING = "utf-8"

# Or edit script to force UTF-8
# All v2.0 scripts already have encoding='utf-8', so this should be rare
```

### "ModuleNotFoundError: No module named 'daemon_manager'"

**Cause**: Python can't import files with hyphens.

**Solution**:
Already fixed in v2.0 using importlib. If you see this:
```bash
# Check file exists
ls -la ~/.claude/memory/daemon-manager.py

# Verify import method
grep "importlib" ~/.claude/memory/test-all-phases.py
```

### "PermissionError: [Errno 13] Permission denied"

**Cause**: Insufficient permissions on files or directories.

**Solution**:
```bash
# Fix permissions
chmod -R u+rwX ~/.claude/memory/

# Ensure user owns directory
chown -R $USER ~/.claude/memory/
```

### "FileNotFoundError: [Errno 2] No such file or directory"

**Cause**: Required file or directory missing.

**Solution**:
```bash
# Run verification to see what's missing
bash ~/.claude/memory/verify-system.sh

# Create missing directories
mkdir -p ~/.claude/memory/{.pids,.restarts,.cache,.state,logs/daemons}

# Re-run startup
bash ~/.claude/memory/startup-hook-v2.sh
```

### "JSONDecodeError: Expecting value"

**Cause**: Corrupted JSON file.

**Solution**:
```bash
# Identify which JSON file
# Common files: failure-kb.json, consultation-preferences.json

# Validate JSON
python -m json.tool ~/.claude/memory/failure-kb.json

# If invalid, backup and recreate
cp ~/.claude/memory/failure-kb.json ~/.claude/memory/failure-kb-broken.json
# Recreate with valid JSON (see section 3 above)
```

---

## Platform-Specific Issues

### Windows

**Issue**: Daemons not starting

**Check**:
```powershell
# Check pythonw.exe exists
where pythonw
```

**Solution**:
```powershell
# Ensure Python installed for all users with py launcher
py --version
```

**Issue**: Backslash path issues

**Solution**:
v2.0 uses Path objects which handle this. If you see errors:
```python
# In scripts, ensure pathlib is used:
from pathlib import Path
path = Path(r"C:\Users\...").resolve()
```

### Linux/Mac

**Issue**: nohup not found

**Solution**:
```bash
# Install coreutils (rare issue)
# Ubuntu/Debian
sudo apt-get install coreutils

# macOS
brew install coreutils
```

**Issue**: Permission denied on startup-hook-v2.sh

**Solution**:
```bash
chmod +x ~/.claude/memory/startup-hook-v2.sh
```

---

## Performance Tuning

### Reduce Health Check Frequency

Default: Every 5 minutes

To reduce CPU usage:

Edit `health-monitor-daemon.py`:
```python
# Line ~50
CHECK_INTERVAL = 600  # 10 minutes instead of 300 (5 min)
```

### Reduce Log Retention

Default: 5 backup files, 10MB each = 50MB total per log

To reduce disk usage:

Edit daemon scripts:
```python
# In daemon-logger.py
handler = RotatingFileHandler(
    log_file,
    maxBytes=5*1024*1024,  # 5MB instead of 10MB
    backupCount=2  # 2 backups instead of 5
)
```

### Disable Caching

If memory is constrained:

```bash
# Don't use context-cache.py
# Remove calls from workflow
```

### Increase Cache TTL

To reduce file reads:

Edit `context-cache.py`:
```python
# Line ~20
self.file_summary_ttl = 86400 * 2  # 48 hours instead of 24
```

---

## Advanced Diagnostics

### Full System Check

```bash
# 1. Check all files exist
bash ~/.claude/memory/verify-system.sh

# 2. Check all daemons running
python ~/.claude/memory/daemon-manager.py --status-all

# 3. Check health score
python ~/.claude/memory/pid-tracker.py --health

# 4. Check KB loaded
python ~/.claude/memory/pre-execution-checker.py --stats

# 5. Check logs for errors
grep -i error ~/.claude/memory/logs/*.log

# 6. Run full test suite
python ~/.claude/memory/test-all-phases.py

# 7. View dashboard
bash ~/.claude/memory/dashboard-v2.sh
```

### Collect Diagnostic Info

```bash
# Create diagnostic report
cat > /tmp/memory-system-diagnostic.txt << EOF
System Diagnostic Report
Date: $(date)

=== System Info ===
OS: $(uname -a)
Python: $(python --version)

=== Verification ===
$(bash ~/.claude/memory/verify-system.sh 2>&1)

=== Daemon Status ===
$(python ~/.claude/memory/daemon-manager.py --status-all 2>&1)

=== Health Score ===
$(python ~/.claude/memory/pid-tracker.py --health 2>&1)

=== KB Stats ===
$(python ~/.claude/memory/pre-execution-checker.py --stats 2>&1)

=== Recent Errors ===
$(grep -i error ~/.claude/memory/logs/*.log 2>&1 | tail -50)

=== PID Files ===
$(ls -la ~/.claude/memory/.pids/ 2>&1)

=== Test Results ===
$(python ~/.claude/memory/test-all-phases.py 2>&1)
EOF

cat /tmp/memory-system-diagnostic.txt
```

---

## Reset Procedures

### Soft Reset (Restart Daemons)

```bash
# Stop all daemons
python ~/.claude/memory/daemon-manager.py --stop-all

# Wait 5 seconds
sleep 5

# Start all daemons
python ~/.claude/memory/daemon-manager.py --start-all

# Verify
python ~/.claude/memory/daemon-manager.py --status-all
```

### Medium Reset (Clear Cache & State)

```bash
# Stop daemons
python ~/.claude/memory/daemon-manager.py --stop-all

# Clear cache and state
rm -rf ~/.claude/memory/.cache/*
rm -rf ~/.claude/memory/.state/*

# Keep PID files, KB, preferences

# Restart
bash ~/.claude/memory/startup-hook-v2.sh
```

### Hard Reset (Full Reinstall)

```bash
# CAUTION: This removes all v2 data

# Stop daemons
python ~/.claude/memory/daemon-manager.py --stop-all

# Backup what you want to keep
cp ~/.claude/memory/failure-kb.json ~/failure-kb-backup.json
cp ~/.claude/memory/consultation-preferences.json ~/consultation-preferences-backup.json

# Remove v2 directories
rm -rf ~/.claude/memory/.pids
rm -rf ~/.claude/memory/.restarts
rm -rf ~/.claude/memory/.cache
rm -rf ~/.claude/memory/.state
rm -rf ~/.claude/memory/logs/daemons

# Re-create directories
mkdir -p ~/.claude/memory/{.pids,.restarts,.cache,.state,logs/daemons}

# Restore backups
cp ~/failure-kb-backup.json ~/.claude/memory/failure-kb.json
cp ~/consultation-preferences-backup.json ~/.claude/memory/consultation-preferences.json

# Restart
bash ~/.claude/memory/startup-hook-v2.sh
```

---

## Getting Additional Help

### Check Documentation

1. `SYSTEM-V2-OVERVIEW.md` - System architecture and how it works
2. `MIGRATION-GUIDE.md` - Upgrading from v1
3. `API-REFERENCE.md` - All script APIs and parameters
4. `TROUBLESHOOTING-V2.md` - This file

### Check Logs

All logs in `~/.claude/memory/logs/`:
- `policy-hits.log` - All policy applications
- `model-usage.log` - Model selections
- `consultations.log` - User decisions
- `core-skills-execution.log` - Skills execution
- `health.log` - System health events
- `daemons/*.log` - Per-daemon logs

### Run Diagnostic Commands

```bash
# Quick health check
bash ~/.claude/memory/verify-system.sh

# Detailed dashboard
bash ~/.claude/memory/dashboard-v2.sh

# Full test suite
python ~/.claude/memory/test-all-phases.py

# Health score
python ~/.claude/memory/pid-tracker.py --health
```

---

**Troubleshooting Guide Version**: 1.0
**Last Updated**: 2026-02-09
**Compatible with**: Memory System v2.0

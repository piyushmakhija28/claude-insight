# Session Memory Pruning - Quick Start Guide

## 🎯 What is This?

**Keep your session memory fast by automatically archiving old sessions.**

Over time, projects accumulate many session files. This tool:
- ✅ Keeps last 10 sessions active (fast access)
- ✅ Archives sessions older than 30 days
- ✅ Compresses archives by month
- ✅ Maintains fast session loading

---

## 📚 Quick Commands

### Check What Needs Archiving:
```bash
python ~/.claude/memory/archive-old-sessions.py --stats
```

**Output:**
```
📊 Session Memory Statistics
======================================================================

📁 techdeveloper-ui
   Active sessions: 25
   Archivable (>30d, beyond last 10): 15
   Oldest active session: 2025-10-15 (103 days old)

📁 my-other-project
   Active sessions: 8
   Archivable (>30d, beyond last 10): 0

======================================================================
📊 Total:
   Active sessions: 33
   Archivable sessions: 15
```

---

### Preview Without Archiving (Dry Run):
```bash
python ~/.claude/memory/archive-old-sessions.py --dry-run
```

**Output:**
```
[DRY RUN] Archiving sessions for 8 projects...

📦 techdeveloper-ui:
   Total sessions: 25
   Keeping active: 10
   Archiving: 15
  [DRY RUN] Would archive 10 sessions to 2025-12/
  [DRY RUN] Would archive 5 sessions to 2025-11/

📊 Would archive 15 sessions
```

---

### Archive All Projects:
```bash
python ~/.claude/memory/archive-old-sessions.py
```

**Output:**
```
🗂️  Archiving sessions for 8 projects...
   Rules: Keep last 10 sessions, archive older than 30 days

📦 techdeveloper-ui:
   Total sessions: 25
   Keeping active: 10
   Archiving: 15
  ✓ Archived: session-2025-12-15-16-45.md → 2025-12/sessions.tar.gz (age: 42 days)
  ✓ Archived: session-2025-12-10-09-15.md → 2025-12/sessions.tar.gz (age: 47 days)
  ...

✅ Archived 15 sessions successfully!
```

---

### Archive Specific Project:
```bash
python ~/.claude/memory/archive-old-sessions.py techdeveloper-ui
```

---

## 📁 Archive Structure

### Before:
```
sessions/techdeveloper-ui/
├── project-summary.md           (always kept)
├── session-2026-01-26-14-30.md  (recent)
├── session-2026-01-25-10-15.md  (recent)
├── session-2026-01-20-09-00.md  (recent)
├── ... (7 more recent sessions)
├── session-2025-12-15-16-45.md  (old - 42 days)
├── session-2025-11-28-11-20.md  (old - 59 days)
└── session-2025-11-10-08-30.md  (old - 77 days)
```

### After:
```
sessions/techdeveloper-ui/
├── project-summary.md           (always kept)
├── session-2026-01-26-14-30.md  (active - fast access)
├── session-2026-01-25-10-15.md  (active - fast access)
├── session-2026-01-20-09-00.md  (active - fast access)
├── ... (7 more active sessions = 10 total)
└── archive/
    ├── 2025-12/
    │   └── sessions.tar.gz      (compressed)
    └── 2025-11/
        └── sessions.tar.gz      (compressed)
```

---

## 🔧 Rules

### Rule 1: Always Keep Recent
**Last 10 sessions always kept** (regardless of age)

### Rule 2: Archive Old
**Archive sessions older than 30 days** (except last 10)

### Rule 3: Never Archive Summary
**project-summary.md is NEVER archived**

---

## 🗂️ Restore Archived Sessions

### View Archive Contents:
```bash
tar -tzf ~/.claude/memory/sessions/project-name/archive/2025-12/sessions.tar.gz
```

**Output:**
```
session-2025-12-15-16-45.md
session-2025-12-10-09-15.md
session-2025-12-05-11-20.md
```

---

### Extract Specific Session:
```bash
cd ~/.claude/memory/sessions/project-name/archive/2025-12
tar -xzf sessions.tar.gz session-2025-12-15-16-45.md

# View it
cat session-2025-12-15-16-45.md
```

---

### Extract All Sessions from Month:
```bash
cd ~/.claude/memory/sessions/project-name/archive/2025-12
tar -xzf sessions.tar.gz

# Sessions extracted to current directory
# Move back to parent if needed
mv session-*.md ../../
```

---

## 📅 When to Run

**Recommended:** Monthly

```bash
# First Sunday of each month
python ~/.claude/memory/archive-old-sessions.py --stats  # Check first
python ~/.claude/memory/archive-old-sessions.py          # Then archive
```

**Or when:**
- Session loading feels slow
- Many projects with long history
- Disk space cleanup needed

---

## 🎯 Benefits

### Before Archival:
- 50+ old sessions loading at session start
- Slow initialization
- Cluttered memory with irrelevant context

### After Archival:
- 10 recent sessions loading (fast!)
- Relevant context only
- Old sessions compressed & recoverable

**Result:**
- ⚡ Faster session startup
- 🧹 Cleaner memory
- 💾 Disk space savings (10:1 compression)
- 🔍 Old sessions still recoverable

---

## 📊 Monitoring

### View Logs:
```bash
tail -f ~/.claude/memory/logs/policy-hits.log | grep session-pruning
```

**Output:**
```
[2026-01-26 20:38:02] session-pruning | archived | archive-test-project | 5 sessions
[2026-01-26 21:15:30] session-pruning | archived-all | 47 total sessions
```

---

### Check Archive Sizes:
```bash
du -sh ~/.claude/memory/sessions/*/archive/
```

**Output:**
```
2.5M    sessions/techdeveloper-ui/archive/
1.2M    sessions/my-other-project/archive/
```

---

## ⚠️ Important Notes

### Safety:
- ✅ Dry run mode available (`--dry-run`)
- ✅ Files deleted only AFTER successful compression
- ✅ project-summary.md never archived
- ✅ All actions logged

### Performance:
- Text compression: ~10:1 ratio
- 100 sessions (5MB) → 500KB archived
- Extraction is instant when needed

### What Gets Archived:
- ✅ session-*.md files (old ones)
- ❌ project-summary.md (never)
- ❌ failures.json/md (not touched)

---

## 🧪 Example Workflow

```bash
# Month 1: Check status
$ python ~/.claude/memory/archive-old-sessions.py --stats
📊 Total: 45 active sessions, 20 archivable

# Preview what would happen
$ python ~/.claude/memory/archive-old-sessions.py --dry-run
📊 Would archive 20 sessions

# Archive
$ python ~/.claude/memory/archive-old-sessions.py
✅ Archived 20 sessions successfully!

# Verify
$ python ~/.claude/memory/archive-old-sessions.py --stats
📊 Total: 25 active sessions, 0 archivable, 20 archived (1.2 MB)

# Month 2: Repeat
# (New old sessions accumulated)
```

---

## 📞 Troubleshooting

### Issue: "No sessions found"
**Cause:** Project has no session files yet
**Solution:** Normal - nothing to archive

### Issue: "Already archived" shows 0
**Cause:** First time running archival
**Solution:** Normal - no archives yet

### Issue: Can't extract archive
**Cause:** Corrupted tar.gz file
**Solution:** File is deleted only after successful compression - shouldn't happen

---

## 🎉 Summary

**What it does:**
- Keeps your 10 most recent sessions active
- Archives older sessions by month
- Compresses for disk space savings
- Maintains fast session loading

**When to use:**
- Monthly (recommended)
- When sessions accumulate
- When loading feels slow

**How to use:**
```bash
# Check → Preview → Archive
python ~/.claude/memory/archive-old-sessions.py --stats
python ~/.claude/memory/archive-old-sessions.py --dry-run
python ~/.claude/memory/archive-old-sessions.py
```

**Status:** ✅ READY TO USE | **Location:** `~/.claude/memory/archive-old-sessions.py`

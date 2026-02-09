# Local CLAUDE.md Migration Guide

## Problem

When projects have their own local `CLAUDE.md` files, they **override** the global policies defined in `~/.claude/CLAUDE.md`. This breaks the automated memory system, policy enforcement, and session persistence features.

## Solution

Migrate local `CLAUDE.md` files to the **session-based memory system** (`~/.claude/memory/sessions/<project-name>/project-summary.md`). This preserves project-specific instructions while allowing global policies to work.

---

## Migration Script

**Location:** `~/.claude/memory/migrate-local-claude.py`

### Usage

```bash
# Migrate current directory
python ~/.claude/memory/migrate-local-claude.py

# Migrate specific project
python ~/.claude/memory/migrate-local-claude.py /path/to/project

# On systems with python3
python3 ~/.claude/memory/migrate-local-claude.py /path/to/project
```

### What It Does

1. ✅ Detects local `CLAUDE.md` (or `claude.md`)
2. ✅ Creates/updates `~/.claude/memory/sessions/<project-name>/project-summary.md`
3. ✅ Migrates content from local file to session memory
4. ✅ Creates backup of local `CLAUDE.md` before deletion
5. ✅ Deletes local `CLAUDE.md` to enable global policies
6. ✅ Logs migration action

### Example

```bash
$ cd ~/projects/my-app
$ ls
CLAUDE.md  src/  package.json

$ python ~/.claude/memory/migrate-local-claude.py
[Migration] Found local CLAUDE.md in project: my-app
[Migration] Creating new project-summary.md
[OK] Migration complete!
   -> Migrated to: /Users/you/.claude/memory/sessions/my-app/project-summary.md
   -> Backup: /Users/you/.claude/memory/sessions/my-app/backups/CLAUDE.md.backup-20260126-125518
   -> Deleted local CLAUDE.md

[SUCCESS] Global policies will now work properly!

$ ls
src/  package.json
# CLAUDE.md is gone - global policies now work!
```

---

## Manual Migration (Fallback)

If the Python script doesn't work on your system:

```bash
cd /path/to/your/project
PROJECT_NAME=$(basename "$PWD")
SESSION_DIR=~/.claude/memory/sessions/$PROJECT_NAME

# Create directories
mkdir -p "$SESSION_DIR/backups"

# Create project-summary.md
cat > "$SESSION_DIR/project-summary.md" <<EOF
# Project Memory: $PROJECT_NAME

**Last Updated:** $(date '+%Y-%m-%d %H:%M:%S')
**Status:** Active

---

## Project-Specific Instructions

**Source:** Local CLAUDE.md (migrated manually)

$(cat CLAUDE.md)

---

## Session History

This section will be automatically updated as you work on this project.

EOF

# Backup and delete
cp CLAUDE.md "$SESSION_DIR/backups/CLAUDE.md.backup-$(date +%Y%m%d-%H%M%S)"
rm CLAUDE.md

echo "✅ Migration complete!"
```

---

## Automated Migration (Session Start)

The CLAUDE.md global instructions include this migration step in the **SESSION START AUTO-LOAD** process:

**STEP 0:** Before loading project context, automatically check for and migrate local CLAUDE.md files.

This ensures:
- ✅ Projects with local files get migrated automatically
- ✅ Global policies always work
- ✅ Project-specific instructions are preserved in session memory
- ✅ No manual intervention needed

---

## After Migration

### Your project's instructions are preserved

```bash
$ cat ~/.claude/memory/sessions/my-app/project-summary.md
# Project Memory: my-app

**Last Updated:** 2026-01-26 12:55:18
**Status:** Active

---

## Project-Specific Instructions

**Source:** Local CLAUDE.md (migrated on 2026-01-26 12:55:18)

# My App

**Tech Stack:** React + Node.js
**Preferences:** TypeScript, ESLint strict mode
...

---

## Session History

This section will be automatically updated as you work on this project.
```

### Global policies now work

- ✅ Context validation active
- ✅ Model selection enforced
- ✅ Failure prevention active
- ✅ Session memory working
- ✅ Auto-logging enabled
- ✅ All memory system features functional

---

## Verification

### Check if migration needed

```bash
cd ~/projects/my-app
if [ -f "CLAUDE.md" ] || [ -f "claude.md" ]; then
    echo "⚠️  Local CLAUDE.md found - migration recommended"
else
    echo "✅ No local CLAUDE.md - global policies active"
fi
```

### Check if project has session memory

```bash
PROJECT_NAME=$(basename "$PWD")
if [ -f ~/.claude/memory/sessions/$PROJECT_NAME/project-summary.md ]; then
    echo "✅ Project has session memory"
    cat ~/.claude/memory/sessions/$PROJECT_NAME/project-summary.md | head -20
else
    echo "ℹ️  No session memory (new project)"
fi
```

---

## Troubleshooting

### Python not found

If `python` command doesn't work:

```bash
# Try these alternatives
which python
which python3
/c/Python*/python  # Windows Git Bash
```

If Python is not installed, use the **Manual Migration** method above.

### Git Bash fork errors on Windows

If you see errors like:
```
child_copy: cygheap read copy failed
fatal error in forked process
```

This is a known Windows Git Bash issue. **Use the Python script instead of bash scripts** - Python doesn't have fork() issues on Windows.

### Backup location

All backups are stored in:
```
~/.claude/memory/sessions/<project-name>/backups/
```

To restore:
```bash
cd ~/projects/my-app
cp ~/.claude/memory/sessions/my-app/backups/CLAUDE.md.backup-* ./CLAUDE.md
```

---

## Benefits

### Before Migration
❌ Local `CLAUDE.md` overrides global policies
❌ No session memory
❌ No policy enforcement
❌ No auto-logging
❌ Have to repeat project context each session

### After Migration
✅ Global policies work
✅ Session memory active
✅ Policy enforcement enabled
✅ Auto-logging functional
✅ Project context auto-loads
✅ Project instructions preserved

---

## Files Created

```
~/.claude/memory/sessions/<project-name>/
├── project-summary.md          # Migrated content + session history
└── backups/
    └── CLAUDE.md.backup-*      # Original file backup
```

---

## Log Entry

Every migration is logged:

```bash
$ tail ~/.claude/memory/logs/policy-hits.log
[2026-01-26 12:55:18] local-claude-migration | migrated | my-app | source: /home/user/projects/my-app/CLAUDE.md
```

---

## When to Use

### Migrate if:
- ✅ You have a project with local `CLAUDE.md` or `claude.md`
- ✅ You want global policies to work
- ✅ You want session memory features
- ✅ You're starting a new session on an existing project

### Don't migrate if:
- ❌ Project has no local CLAUDE.md (nothing to migrate)
- ❌ You're in the `~/.claude` directory itself (global config)

---

**Version:** 1.0.0
**Last Updated:** 2026-01-26
**Status:** Production Ready

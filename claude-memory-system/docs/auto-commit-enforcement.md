# Auto-Commit Enforcement

## Overview

The auto-commit enforcer ensures that all code changes are automatically committed and pushed when tasks complete, eliminating the need for manual git operations.

## How It Works

### Automatic Trigger

When you complete a task using `TaskUpdate(status="completed")`, the auto-commit enforcer:

1. **Scans workspace** for all git repositories
2. **Checks for changes** in each repository
3. **Triggers auto-commit** for repos with uncommitted changes
4. **Auto-pushes** to remote if configured

### Manual Trigger

You can also manually enforce auto-commit:

```bash
python ~/.claude/memory/auto-commit-enforcer.py --enforce-now
```

## Integration

### Mandatory Execution Flow

```
1. TaskCreate("Description")
2. TaskUpdate(taskId, status="in_progress")
3. [Do the work - modify files]
4. TaskUpdate(taskId, status="completed")
5. auto-commit-enforcer.py --enforce-now  ← MANDATORY
```

### What Gets Committed

- All git repos in workspace with uncommitted changes
- Uses descriptive commit messages based on task/context
- Includes "Co-Authored-By: Claude Sonnet 4.5" footer

### Skip Conditions

Auto-commit is skipped when:
- No uncommitted changes exist
- Repository is not a git repo
- Commit would be empty

## Configuration

### Location
- **Script:** `~/.claude/memory/auto-commit-enforcer.py`
- **Logs:** `~/.claude/memory/logs/policy-hits.log`

### Workspace Scan

Scans this location:
```
~/Documents/workspace-spring-tool-suite-4-4.27.0-new/
```

Recursively checks all subdirectories for `.git` folders.

## Examples

### Successful Enforcement

```
======================================================================
🚨 AUTO-COMMIT ENFORCER
======================================================================

🔍 Scanning for repositories with uncommitted changes...

📋 Found 2 repository(ies) with changes:

   • jenkins-seed-config
   • surgricalswale-cart-service

======================================================================
📦 Repository: jenkins-seed-config
======================================================================

✅ Commit recommended
💾 Running auto-commit...
✅ AUTO-COMMIT SUCCESSFUL!

======================================================================
✅ Successfully processed 2/2 repositories
======================================================================
```

### No Changes Found

```
======================================================================
🚨 AUTO-COMMIT ENFORCER
======================================================================

🔍 Scanning for repositories with uncommitted changes...

✅ No uncommitted changes found - nothing to commit
```

## Policy Violations

If auto-commit fails to run after task completion:

1. Violation logged to `~/.claude/memory/logs/policy-violations.log`
2. Manual commit required
3. User must explicitly request commit

## Benefits

- ✅ Never forget to commit work
- ✅ Automatic backup of all changes
- ✅ Consistent commit messages
- ✅ No manual git commands needed
- ✅ Multi-repo support

## Related

- **Policy:** `~/.claude/memory/git-auto-commit-policy.md`
- **Daemon:** `~/.claude/memory/commit-daemon.py`
- **Trigger:** `~/.claude/memory/trigger-auto-commit.py`
- **CLAUDE.md:** Execution flow step 9

---

**Last Updated:** 2026-02-16
**Status:** 🟢 ACTIVE

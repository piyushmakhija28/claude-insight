# Git & Context Management

## Git Repository Creation Rules

### Rule 1: Always "main" Branch (NEVER "master")
```bash
git init
git branch -M main
git add .
git commit -m "feat: initial commit"
git push -u origin main
```

### Rule 2: Always Private (Default)
```bash
gh repo create org/repo-name --private --source=. --remote=origin --push
```
**Exception:** Only public if user explicitly requests

### Rule 3: Complete Workflow
```bash
git init && git branch -M main
# Add .gitignore
git add .
git commit -m "feat: initial commit

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
gh repo create org/repo-name --private --source=. --remote=origin --push
```

### Pre-Creation Checklist
- ✅ Branch = "main"
- ✅ Visibility = "private"
- ✅ .gitignore added
- ✅ Descriptive commit message

**🚨 GOLDEN RULE: Private + Main = Default! 🚨**

---

## Git Auto-Commit Automation

### When to Auto-Trigger
1. ✅ Task Completed (`TaskUpdate(status="completed")`)
2. ✅ Phase Completed
3. ✅ User says "done", "finished", "complete"
4. ✅ 10+ files modified
5. ✅ 30+ minutes since last commit

### How to Trigger
```bash
python ~/.claude/memory/trigger-auto-commit.py --event "task-completed" --project-dir "$PWD"
```

### User Notification
```
✅ Auto-committed: Task Complete
📤 Pushed to remote successfully
```

**🚨 After every task/phase completion, MUST call trigger-auto-commit.py! 🚨**

---

## Context Window Monitoring (200K Limit)

### Two Separate Systems
1. **Our Persistent Memory** (sessions/) - NEVER deleted
2. **Claude Code Context** (200K tokens) - Needs monitoring

### Thresholds & Actions
| Context % | Level | Action |
|-----------|-------|--------|
| < 70% | ✅ OK | None |
| 70-84% | 💡 Light | `claude compact --light` |
| 85-89% | ⚠️ Moderate | `claude compact` |
| 90%+ | 🚨 Critical | `claude compact --full` |

### Update Context
```bash
python ~/.claude/memory/update-context-usage.py --tokens-used CURRENT --tokens-total 200000
```

### Monitor
```bash
python ~/.claude/memory/monitor-and-cleanup-context.py
```

**Session memory is ALWAYS protected - never deleted by cleanup!**

---

## Session End Auto-Save

### When to Save
- Major milestone completed
- 5+ files modified
- Git commit made
- User says "done", "thanks", "finished"

### Save Process
```bash
PROJECT_NAME=$(basename "$PWD")
# Save to: ~/.claude/memory/sessions/$PROJECT_NAME/project-summary.md
```

### What to Include
- ✅ What was done
- ✅ Key decisions
- ✅ Files modified
- ✅ User preferences
- ✅ Pending work

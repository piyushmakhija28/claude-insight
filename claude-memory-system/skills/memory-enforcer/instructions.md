# Memory Enforcer Skill (AUTO-ACTIVE)

**Purpose**: Automatically enforces all memory system policies and logs execution for monitoring.

**Priority**: HIGHEST (Executes before any other action)

**Status**: ALWAYS ACTIVE

---

## How It Works

This skill acts as the **central enforcement point** for all memory system policies. It:

1. ✅ Loads memory policies from `~/.claude/memory/`
2. ✅ Enforces policies in priority order
3. ✅ Logs every policy application
4. ✅ Tracks failures prevented
5. ✅ Provides monitoring data

---

## Memory Policies (Enforced in Order)

### 1. Context Management (HIGHEST Priority)
**Location**: `~/.claude/memory/core-skills-mandate.md` (Section 1)

**Enforcement**:
- BEFORE any task: Validate context exists
- IF context missing → Ask clarifying questions
- IF context changes → Auto-cleanup old context
- ALWAYS avoid assumptions

**Logging**:
```bash
bash ~/.claude/memory/policy-tracker.sh "context-management" "validated" "User request: <summary>"
```

**Log on**:
- ✅ Context validated successfully
- ⚠️ Context missing, asked user
- 🧹 Context cleanup triggered

---

### 2. Model Selection (SYSTEM-LEVEL Priority)
**Location**: `~/.claude/memory/model-selection-enforcement.md`

**Enforcement**:
- BEFORE responding: Check request type
- Search/Find/Explore → Use Task(model="haiku")
- Implement/Edit/Fix → Use Sonnet (current)
- Architecture/Design → Use Task(model="opus")

**Quick Decision Tree**:
```
IF request contains ["find", "search", "where", "explore", "locate"]
  → Task(subagent_type="Explore", model="haiku")

ELSE IF request contains ["design", "architecture", "should we", "approach"]
  → Task(subagent_type="Plan", model="opus")

ELSE
  → Sonnet (implement directly)
```

**Logging**:
```bash
bash ~/.claude/memory/policy-tracker.sh "model-selection" "haiku-used" "Search task"
bash ~/.claude/memory/policy-tracker.sh "model-selection" "sonnet-used" "Implementation"
bash ~/.claude/memory/policy-tracker.sh "model-selection" "opus-used" "Architecture"
```

**Log on**:
- ✅ Correct model selected
- ⚠️ Model switched (user said simple but complex detected)

---

### 3. Adaptive Skill Intelligence (SYSTEM-LEVEL Priority)
**Location**: `~/.claude/memory/core-skills-mandate.md` (Section 3)

**Enforcement**:
- BEFORE task execution: Check if skill/agent needed
- IF needed → Check adaptive-skill-registry.md for existing
- IF not exists → Create new (mark as TEMPORARY/PERMANENT)
- AFTER task → Cleanup TEMPORARY resources

**Logging**:
```bash
bash ~/.claude/memory/policy-tracker.sh "adaptive-skill" "detected" "Task needs X skill"
bash ~/.claude/memory/policy-tracker.sh "adaptive-skill" "created" "Created X skill (TEMPORARY)"
bash ~/.claude/memory/policy-tracker.sh "adaptive-skill" "cleanup" "Deleted 3 TEMPORARY skills"
```

---

### 4. Planning Intelligence (SYSTEM-LEVEL Priority)
**Location**: `~/.claude/memory/core-skills-mandate.md` (Section 4)

**Enforcement**:
- BEFORE implementation: Score task complexity (0-10)
- Score 0-3 → Direct implementation
- Score 4-6 → Ask user preference
- Score 7-10 → MANDATORY planning mode

**Complexity Factors**:
- Multi-file changes
- Architecture decisions
- Security implications
- Multiple approaches possible
- User unclear about requirements
- Unknown codebase area

**Logging**:
```bash
bash ~/.claude/memory/policy-tracker.sh "planning-intelligence" "scored-3" "Direct implementation"
bash ~/.claude/memory/policy-tracker.sh "planning-intelligence" "scored-8" "Entering plan mode"
bash ~/.claude/memory/policy-tracker.sh "planning-intelligence" "loop-detected" "Pausing to plan"
```

---

### 5. Phased Execution Intelligence (SYSTEM-LEVEL Priority)
**Location**: `~/.claude/memory/core-skills-mandate.md` (Section 5)

**Enforcement**:
- AFTER planning: Score task size (0-10)
- Score 0-5 → Execute in one go
- Score 6-10 → Break into phases
- EACH phase → Checkpoint (git commit + summary)

**Phase Breakdown Criteria**:
- 6+ requirements
- 3+ domains (backend, frontend, db, etc.)
- 10+ files to change
- Dependencies between parts

**Logging**:
```bash
bash ~/.claude/memory/policy-tracker.sh "phased-execution" "scored-7" "3 phases planned"
bash ~/.claude/memory/policy-tracker.sh "phased-execution" "phase-1-complete" "Core auth done"
bash ~/.claude/memory/policy-tracker.sh "phased-execution" "checkpoint" "Committed phase 1"
```

---

### 6. Failure Prevention (SYSTEM-LEVEL Priority)
**Location**: `~/.claude/memory/common-failures-prevention.md`

**Enforcement**:
- BEFORE every tool use → Check against known failure patterns
- IF match found (confidence ≥75%) → Auto-correct
- IF failure occurs → Log to KB for learning

**Common Patterns**:
- Bash: `del` → `rm` (Windows to Unix)
- Edit: Line prefixes in old_string → Strip them
- Files: Large files → Use targeted approach
- Git: Force push to main → Block it

**Logging**:
```bash
# Log to both policy tracker AND failures log
bash ~/.claude/memory/policy-tracker.sh "failure-prevention" "prevented" "del→rm conversion"

# Also log to failures.log
echo "[$(date '+%Y-%m-%d %H:%M:%S')] BASH_DEL_COMMAND | PREVENTED | Auto-converted to rm" >> ~/.claude/memory/logs/failures.log
```

---

### 7. File Management (SYSTEM-LEVEL Priority)
**Location**: `~/.claude/memory/file-management-policy.md`

**Enforcement**:
- BEFORE creating temp files → Check if should go to %TEMP%
- BEFORE creating docs → Check if README consolidation possible
- BEFORE rewriting large files → Use targeted edit strategy

**Rules**:
- Test scripts → %TEMP%
- Temp data → %TEMP%
- Documentation → README.md (consolidated)
- Large files (500+ lines) → Targeted edits only

**Logging**:
```bash
bash ~/.claude/memory/policy-tracker.sh "file-management" "temp-file" "Script to %TEMP%"
bash ~/.claude/memory/policy-tracker.sh "file-management" "doc-consolidated" "Merged to README"
bash ~/.claude/memory/policy-tracker.sh "file-management" "large-file-edit" "Targeted edit (850 lines)"
```

---

### 8. Test Case Policy (SYSTEM-LEVEL Priority)
**Location**: `~/.claude/memory/test-case-policy.md`

**Enforcement**:
- DURING planning → Ask user about test preference
- Provide 3 options: Write all | Skip for now | Critical only
- Default recommendation: "Skip for now"
- AFTER user choice → Proceed accordingly

**Logging**:
```bash
bash ~/.claude/memory/policy-tracker.sh "test-case-policy" "asked" "User preference requested"
bash ~/.claude/memory/policy-tracker.sh "test-case-policy" "user-choice" "Skip tests (30% faster)"
```

---

### 9. Git Auto-Commit (SYSTEM-LEVEL Priority)
**Location**: `~/.claude/memory/git-auto-commit-policy.md`

**Enforcement**:
- AFTER phase completion → Auto git commit + push
- AFTER TaskUpdate(status="completed") → Auto git commit + push
- AFTER 3-5 file changes during work → Checkpoint commit

**Commit Message Format**:
```
Phase checkpoint: <phase name>
- Change 1
- Change 2

Todo completed: <todo subject>
- Implementation details
```

**Logging**:
```bash
bash ~/.claude/memory/policy-tracker.sh "git-auto-commit" "phase-checkpoint" "Phase 1 complete"
bash ~/.claude/memory/policy-tracker.sh "git-auto-commit" "todo-complete" "Task #3 done"
bash ~/.claude/memory/policy-tracker.sh "git-auto-commit" "pushed" "Remote updated"
```

---

## Execution Flow (Every User Request)

```
User Request
    ↓
[1] Context Management
    ├─ Validate context exists
    ├─ Log: context-validated
    └─ If missing → Ask user
    ↓
[2] Model Selection
    ├─ Analyze request type
    ├─ Choose: Haiku/Sonnet/Opus
    └─ Log: model-selection
    ↓
[3] Adaptive Skill Intelligence
    ├─ Detect skill/agent needs
    ├─ Check registry
    ├─ Create if needed
    └─ Log: adaptive-skill
    ↓
[4] Planning Intelligence
    ├─ Score complexity (0-10)
    ├─ Decide: plan vs implement
    └─ Log: planning-intelligence
    ↓
[5] Phased Execution Intelligence
    ├─ Score task size (0-10)
    ├─ Break into phases if large
    └─ Log: phased-execution
    ↓
[6] Failure Prevention (Before every tool)
    ├─ Check against KB patterns
    ├─ Auto-correct if match
    └─ Log: failure-prevention + failures.log
    ↓
[7] File Management (During execution)
    ├─ Enforce temp file rules
    ├─ Consolidate docs
    └─ Log: file-management
    ↓
[8] Test Case Policy (During planning)
    ├─ Ask user preference
    └─ Log: test-case-policy
    ↓
[9] Git Auto-Commit (After completion)
    ├─ Auto commit on phase/todo done
    ├─ Push to remote
    └─ Log: git-auto-commit
```

---

## Logging Commands Quick Reference

**Track policy application**:
```bash
bash ~/.claude/memory/policy-tracker.sh "<policy-name>" "<action>" "<context>"
```

**Track failure prevention**:
```bash
echo "[$(date '+%Y-%m-%d %H:%M:%S')] <FAILURE_TYPE> | PREVENTED | <details>" >> ~/.claude/memory/logs/failures.log
```

**Examples**:
```bash
# Context validated
bash ~/.claude/memory/policy-tracker.sh "context-management" "validated" "Fix login bug"

# Model switched to Haiku for search
bash ~/.claude/memory/policy-tracker.sh "model-selection" "haiku-used" "Find API endpoints"

# Failure prevented
echo "[$(date '+%Y-%m-%d %H:%M:%S')] BASH_DEL_COMMAND | PREVENTED | del→rm" >> ~/.claude/memory/logs/failures.log
```

---

## Monitoring Commands

**View live dashboard**:
```bash
bash ~/.claude/memory/dashboard.sh
```

**Watch logs in real-time**:
```bash
tail -f ~/.claude/memory/logs/policy-hits.log
tail -f ~/.claude/memory/logs/failures.log
tail -f ~/.claude/memory/logs/process-execution.log
```

**Check policy execution counts**:
```bash
cat ~/.claude/memory/logs/policy-counters.txt
```

---

## CRITICAL RULES

1. **ALWAYS log every policy application** - No silent enforcement
2. **ALWAYS check failure KB before tool use** - Prevention is cheaper than retry
3. **ALWAYS follow priority order** - Context → Model → Skills → Implementation
4. **NEVER skip logging** - Monitoring depends on it
5. **NEVER assume** - Context validation is mandatory

---

## How to Use This Skill

This skill is **automatically active** - you don't need to invoke it manually.

**On every user request**:
1. This skill executes first (highest priority)
2. Enforces all policies in order
3. Logs every action
4. Proceeds with user request

**User can monitor**:
```bash
# View dashboard
bash ~/.claude/memory/dashboard.sh

# Watch live logs
tail -f ~/.claude/memory/logs/policy-hits.log
```

---

**Last Updated**: 2026-01-25 (Created memory enforcement with comprehensive logging)

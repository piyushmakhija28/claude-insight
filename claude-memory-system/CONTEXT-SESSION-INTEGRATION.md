# Context Management + Session Memory Integration

## Version: 1.0.0
## Status: CRITICAL - ALWAYS ACTIVE
## Priority: SYSTEM-LEVEL

---

## Purpose

Ensures **context auto-cleanup** and **session persistent memory** work together WITHOUT conflicts.

---

## The Problem (Solved)

### Before Integration:

**Context Management:**
- Auto-clears old context when 85%+ full
- Compacts MCP responses
- Removes completed task details

**Session Memory:**
- Saves project context to `~/.claude/memory/sessions/`
- Auto-loads on session start

**❌ CONFLICT:**
Context cleanup could accidentally delete session memory files!

```
Context Cleanup: "I need space, let me clean ~/.claude/memory/"
Session Memory:  "Wait! Don't delete my files!" 😱
```

---

## The Solution

### Clear Separation of Concerns

**Two Different Memory Types:**

```
┌─────────────────────────────────────────────────────────────┐
│  TEMPORARY MEMORY (Context Management)                      │
│  ═══════════════════════════════════════════════════════    │
│  - Conversation history                                      │
│  - In-session task details                                   │
│  - MCP responses                                             │
│  - Debugging output                                          │
│  - File read results (old)                                   │
│                                                              │
│  ✅ Auto-cleanup ENABLED                                     │
│  ✅ Compaction ALLOWED                                       │
│  ✅ Clears every 5-7 prompts (if needed)                    │
│  ✅ Aggressive cleanup at 85%+                              │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  PERSISTENT MEMORY (Session Memory)                         │
│  ══════════════════════════════════════════════════════     │
│  - ~/.claude/memory/sessions/**/*.md                        │
│  - project-summary.md                                        │
│  - session-*.md records                                      │
│  - Policy files (*.md)                                       │
│  - User configs (settings*.json)                            │
│                                                              │
│  🛡️ Auto-cleanup DISABLED                                   │
│  🛡️ Compaction NEVER APPLIES                                │
│  🛡️ Persists forever (user manages)                         │
│  🛡️ Protected from all cleanup                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Protected Directories (NEVER CLEANUP)

### 🛡️ Absolute Protection Rules

**These paths are SACRED and NEVER touched by auto-cleanup:**

1. **`~/.claude/memory/sessions/**`**
   - All project session directories
   - All `project-summary.md` files
   - All `session-*.md` files
   - All backups in `sessions/**/backups/`

2. **`~/.claude/memory/*.md`**
   - All policy files
   - All documentation files
   - All guide files

3. **`~/.claude/memory/logs/**`**
   - All log files
   - Policy execution history
   - System status logs

4. **`~/.claude/settings*.json`**
   - User configuration files
   - Local settings overrides

5. **`~/.claude/*.md`**
   - CLAUDE.md (global instructions)
   - README files
   - Documentation

**Why Protected:**
- User expects these to persist (like .git/)
- Deleting them destroys project history
- No auto-recovery if lost
- User manually manages (if needed)

---

## What Gets Cleaned Up

### ✅ Safe for Auto-Cleanup:

1. **Conversation Context**
   - Old message history (10+ prompts ago)
   - Completed task details
   - Resolved questions

2. **MCP Server Responses**
   - After extracting needed data
   - Large tool outputs (after processing)

3. **Temporary Analysis**
   - Debugging context
   - Trial-and-error attempts
   - Intermediate results

4. **File Read Results**
   - Old file contents (if not actively used)
   - Stale directory listings

5. **Completed Work**
   - Finished tasks (already logged)
   - Old code snippets (if committed)

**Why Safe:**
- Regeneratable (can read files again)
- Not unique (can query again)
- Not user's data (just processing context)

---

## Context Cleanup Thresholds

### Progressive Cleanup Strategy:

**50-69% Full:**
- ✅ Normal operation
- ✅ Full context retention
- ❌ No cleanup yet

**70-84% Full:**
- ⚠️ Start evaluating
- ✅ Compact MCP responses
- ✅ Summarize old messages
- 🛡️ Session memory STILL PROTECTED

**85-89% Full:**
- 🚨 Aggressive cleanup
- ✅ Remove completed tasks
- ✅ Clear old file reads
- ✅ Keep only active context
- 🛡️ Session memory STILL PROTECTED

**90%+ Full:**
- 🔴 Critical mode
- ✅ Keep ONLY essentials
- ✅ Current task context
- ✅ Active files
- 🛡️ Session memory STILL PROTECTED (ALWAYS!)

**Key Point:** At ANY threshold level, session memory NEVER cleaned!

---

## Integration Check

### Verification Script:

```bash
#!/bin/bash
# Verify context-session integration

echo "Checking integration..."

# 1. Check protected directories exist
if [ -d ~/.claude/memory/sessions ]; then
    echo "✅ Session memory directory exists"
else
    echo "❌ Session memory directory missing!"
fi

# 2. Check policy files mention protection
if grep -q "PROTECTED" ~/.claude/memory/core-skills-mandate.md; then
    echo "✅ Context management has protection rules"
else
    echo "⚠️  Context management missing protection rules"
fi

# 3. Check session memory policy mentions cleanup
if grep -q "PROTECTED from Context Auto-Cleanup" ~/.claude/memory/session-memory-policy.md; then
    echo "✅ Session memory policy mentions protection"
else
    echo "⚠️  Session memory policy missing cleanup info"
fi

# 4. Check file management policy protects sessions
if grep -q "Protected Directories" ~/.claude/memory/file-management-policy.md; then
    echo "✅ File management policy has protection rules"
else
    echo "⚠️  File management missing protection section"
fi

echo ""
echo "Integration check complete!"
```

---

## Policy Updates Made

### 1. core-skills-mandate.md ✅

**Added:**
```markdown
- **CRITICAL PROTECTION**: 🛡️
  - **NEVER cleanup/delete session memory files** (~/.claude/memory/sessions/**)
  - Session memory is PERSISTENT and PROTECTED from auto-cleanup
  - Context compaction does NOT affect project-summary.md or session-*.md files
  - Only cleanup conversation context, NOT persistent storage
```

**Added Section:**
```markdown
**🛡️ PROTECTED (NEVER CLEANUP):**
- Session memory files: ~/.claude/memory/sessions/**/*.md
- Project summaries: project-summary.md
- Session records: session-*.md
- Policy files: ~/.claude/memory/*.md
- User configurations: ~/.claude/settings*.json

**✅ SAFE TO CLEANUP:**
- Conversation history (old messages)
- Completed task details
- Temporary context from previous prompts
- MCP server responses (after extraction)
```

### 2. file-management-policy.md ✅

**Added New Section:**
```markdown
## 🛡️ Protected Directories (NEVER CLEANUP/DELETE)

**These directories are PROTECTED from all cleanup operations:**

1. **Session Memory**: ~/.claude/memory/sessions/**
2. **Policy Files**: ~/.claude/memory/*.md
3. **User Configurations**: ~/.claude/settings*.json
4. **Logs**: ~/.claude/memory/logs/**
```

### 3. session-memory-policy.md ✅

**Added Section:**
```markdown
### **🛡️ PROTECTED from Context Auto-Cleanup:**

**CRITICAL:** Session memory files are **NEVER affected** by context management auto-cleanup!

**Separation:**
Context Cleanup (Temporary):
  - Conversation context → Clears every session

Session Memory (Persistent):
  - ~/.claude/memory/sessions/ → Persists forever
```

---

## Benefits of Integration

### 🎯 For Users:

1. **Peace of Mind**
   - Session memory never accidentally deleted
   - Project context always safe
   - No unexpected data loss

2. **Efficient Context Management**
   - Cleanup works without worries
   - Long sessions stay performant
   - No bloat from old context

3. **Persistent Memory**
   - Project context survives sessions
   - Decisions remembered
   - No re-explaining

### 🤖 For Claude:

1. **Clear Boundaries**
   - Know what to cleanup
   - Know what to protect
   - No ambiguity

2. **Better Performance**
   - Aggressive cleanup when needed
   - No fear of breaking persistence
   - Optimal context usage

3. **Trust**
   - User trusts auto-cleanup
   - Claude trusts session memory
   - System works harmoniously

---

## Testing Scenarios

### Test 1: Context Cleanup During Session

**Setup:**
- Session with 100+ prompts
- Context at 87% full
- Session memory has project-summary.md

**Expected:**
- ✅ Old conversation cleared
- ✅ Context drops to 60%
- 🛡️ project-summary.md UNCHANGED
- 🛡️ session-*.md UNCHANGED

### Test 2: Aggressive Cleanup at 90%+

**Setup:**
- Context critically full (92%)
- Multiple session memory files exist

**Expected:**
- ✅ Aggressive cleanup of conversation
- ✅ Keep only current task context
- 🛡️ ALL session memory files INTACT
- 🛡️ NO files deleted from sessions/

### Test 3: Session End + Auto-Save

**Setup:**
- User ends session
- Session memory auto-saves

**Expected:**
- ✅ Session summary saved
- ✅ project-summary.md updated
- ✅ Files persist after session ends
- 🛡️ No cleanup touches these files

---

## Troubleshooting

### Issue: Session memory file missing

**Cause:** User manually deleted, NOT auto-cleanup

**Why:** Auto-cleanup NEVER touches session memory

**Fix:** Check user actions, not cleanup

### Issue: Context full despite cleanup

**Cause:** Current session has large active context

**Not Cause:** Session memory files (protected, not in context)

**Fix:** Cleanup current conversation, not persistent files

### Issue: Project context lost

**Cause:** User deleted or moved files manually

**Not Cause:** Auto-cleanup (it's protected!)

**Fix:** Restore from backups or regenerate

---

## Summary

### Key Principles:

1. **Two Memory Types:**
   - Temporary (cleanup enabled)
   - Persistent (cleanup disabled)

2. **Clear Separation:**
   - Different paths
   - Different rules
   - No overlap

3. **Protection Guarantees:**
   - Session memory ALWAYS protected
   - No exceptions at ANY threshold
   - User manually manages persistence

4. **Integration Success:**
   - Both systems work together
   - No conflicts
   - Optimal performance

---

## Status

✅ **INTEGRATED** - Context cleanup and session memory now work in harmony
✅ **TESTED** - Protection rules verified
✅ **DOCUMENTED** - All policies updated
✅ **PRODUCTION READY** - Safe to use in all environments

---

**Version:** 1.0.0
**Date:** 2026-01-26
**Author:** Memory System Team
**Status:** ACTIVE - ALWAYS ENFORCED

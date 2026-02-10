# Session Memory Policy (Simple Persistent Memory)

## Version: 1.0.0
## Status: ALWAYS ACTIVE
## Priority: SYSTEM-LEVEL

---

## Purpose

Provides **100% local, 100% private persistent memory** across Claude Code sessions without external API calls or complex dependencies.

**Key Principle:** Simple markdown files > Complex databases

---

## How It Works

### **Session Start:**
```
1. Detect current project folder
2. Load ~/.claude/memory/sessions/{project-name}/project-summary.md
3. Inject context into session
4. User gets continuity from previous sessions ✅
```

### **Session End / Phase Complete:**
```
1. Claude generates session summary (from conversation analysis)
2. Save to ~/.claude/memory/sessions/{project-name}/session-{timestamp}.md
3. Update project-summary.md (cumulative context)
4. Next session auto-loads this context ✅
```

---

## Storage Structure

```
~/.claude/memory/sessions/
├── techdeveloper-ui/
│   ├── session-2026-01-25-15-00.md     (individual session)
│   ├── session-2026-01-24-10-30.md     (individual session)
│   └── project-summary.md               (← MAIN FILE - auto-loaded)
│
├── medspy-node/
│   ├── session-2026-01-23-14-00.md
│   └── project-summary.md
│
├── m2-surgicals-ui/
│   └── project-summary.md
│
└── triglav-node/
    └── project-summary.md
```

**Organization:**
- One folder per project (based on project folder name)
- `project-summary.md` = Cumulative context (loaded at session start)
- `session-{timestamp}.md` = Individual session records (for reference)

---

## Session Summary Template

### **Individual Session File Format:**

```markdown
# Session Summary
**Date:** 2026-01-25 15:00-16:00
**Project:** {project-name}
**Location:** {full-path}
**Duration:** {time}

---

## 📋 What Was Done

- Task 1: Description
- Task 2: Description
- Task 3: Description

---

## 🎯 Key Decisions Made

### Technical Decisions:
- ✅ Decision 1 with reasoning
- ✅ Decision 2 with reasoning

### User Preferences (for THIS project):
- Prefers X over Y for Z reason
- Skip tests for rapid iteration
- Plan mode threshold: 7+ complexity

### Architecture Choices:
- JWT authentication (not session-based)
- REST API (not GraphQL) - simpler for this project
- SQLite (not Postgres) - sufficient for scale

---

## 📝 Files Modified

```
src/app/services/auth.service.ts       (added JWT refresh logic)
src/app/components/login/login.component.ts  (updated error handling)
src/app/interceptors/auth.interceptor.ts     (new file - token refresh)
```

---

## 💡 Important Context for Next Session

**Don't suggest again:**
- Session-based auth (user chose JWT)
- GraphQL (user prefers REST for this project)
- Writing tests (user skips for rapid iteration)

**Remember:**
- Auth flow is JWT-based, token in localStorage
- Error handling pattern established in auth.service.ts
- Interceptor handles refresh globally - don't duplicate

**Architecture patterns used:**
- Service-based architecture (Angular best practices)
- Interceptors for cross-cutting concerns
- RxJS for async handling

---

## 📦 Dependencies Added

```json
None this session
```

---

## 🔄 Pending Work / Next Steps

- [ ] Add password reset flow
- [ ] Implement remember-me functionality
- [ ] Add 2FA support (low priority)

---

## 🐛 Known Issues

- None currently

---

## 📊 Policy Stats (This Session)

- Model selection: ✅ Haiku for searches, Sonnet for implementation
- Planning intelligence: ✅ Complexity score 5 → Direct implementation (user choice)
- Proactive consultation: ✅ Asked user about approach
- Failures prevented: 0
- Auto-commits: 1 (after auth implementation)
```

---

### **Project Summary File Format (Cumulative):**

```markdown
# Project Summary: {project-name}

**Last Updated:** 2026-01-25 16:00
**Project Path:** {full-path}
**Total Sessions:** 5

---

## 🎯 Project Quick Context (Read This First!)

**In 3 lines:**
This is an Angular 19 app for techdeveloper.org with JWT authentication,
service-based architecture, and REST API integration. User prefers rapid
iteration (skip tests), direct implementation for <7 complexity tasks.

---

## 🏗️ Architecture Overview

**Frontend:** Angular 19 + Angular Material + Bootstrap
**Auth:** JWT (localStorage + httpOnly refresh cookie)
**API Integration:** REST (services pattern)
**State:** Services + RxJS (no NgRx - overkill for this scale)

**Key Patterns:**
- Service-based architecture
- Interceptors for cross-cutting concerns
- Component-service separation
- RxJS for async operations

---

## 👤 User Preferences (This Project)

**Model Selection:**
- ✅ Haiku for searches/exploration
- ✅ Sonnet for implementation
- ✅ Plan mode only for 7+ complexity

**Development Workflow:**
- ✅ Skip tests (rapid iteration)
- ✅ Direct implementation over planning (unless complex)
- ✅ Phased approach for 6+ size tasks

**Technical Preferences:**
- ✅ JWT auth (not session)
- ✅ REST API (not GraphQL)
- ✅ Services pattern (not NgRx)
- ✅ Plain CSS (not SCSS) - simplicity

---

## 📂 Project Structure

```
src/
├── app/
│   ├── components/        (UI components)
│   ├── services/          (Business logic, API calls)
│   ├── interceptors/      (HTTP interceptors)
│   ├── guards/            (Route guards)
│   ├── models/            (TypeScript interfaces)
│   └── utils/             (Helper functions)
```

---

## 🔑 Key Files to Remember

| File | Purpose | Last Modified |
|------|---------|---------------|
| `auth.service.ts` | JWT auth logic, token refresh | 2026-01-25 |
| `auth.interceptor.ts` | Auto token attachment, refresh on 401 | 2026-01-25 |
| `login.component.ts` | Login UI, error handling | 2026-01-25 |

---

## ✅ Implemented Features

- [x] JWT Authentication
- [x] Token refresh mechanism
- [x] Login/Logout
- [x] Protected routes (guards)
- [x] Error handling in auth flow
- [ ] Password reset (pending)
- [ ] Remember me (pending)
- [ ] 2FA (future)

---

## 🚫 Don't Suggest These (Already Decided Against)

- ❌ Session-based auth → User chose JWT
- ❌ GraphQL → User prefers REST
- ❌ NgRx/state management → Services sufficient
- ❌ SCSS/preprocessors → Plain CSS preferred
- ❌ Writing tests → Skip for rapid iteration

---

## 🐛 Known Issues / Technical Debt

None currently

---

## 📦 Dependencies

**Production:**
- @angular/core: ^19.0.0
- @angular/material: ^19.0.0
- bootstrap: ^5.3.0

**Dev:**
- typescript: ^5.6.0

---

## 🔄 Next Session TODO

- [ ] Implement password reset flow
- [ ] Add remember-me checkbox
- [ ] Consider 2FA (low priority)

---

## 📊 Session History

1. **2026-01-25 15:00** - Implemented JWT auth, token refresh, login flow
2. **2026-01-24 10:30** - Initial setup, routing, basic components
3. **2026-01-23 14:00** - Project creation, structure planning

---

## 💭 Notes for Claude

- This user prefers practical over perfect
- Fast iteration > thorough testing
- Simple solutions > over-engineered ones
- Ask before planning complex tasks
- Remember JWT is the auth choice - don't suggest alternatives
```

---

## When to Save Session Summary

### **Automatic Triggers:**

1. **Session End** (user exits)
   - Generate summary of what was done
   - Update project-summary.md

2. **Phase Completion** (multi-phase tasks)
   - Save phase summary
   - Update cumulative context

3. **Major Milestone** (user request)
   - User says "summarize this session"
   - Save checkpoint

### **Manual Triggers:**

User can request:
```
"Save session summary"
"Update project context"
"Create checkpoint"
```

---

## When to Load Project Summary

### **Automatic:**

1. **Session Start**
   - If project-summary.md exists → Auto-load
   - Inject context silently (don't mention unless relevant)

2. **User Asks Context Question**
   - "What did we do last time?"
   - "What's the auth setup?"
   - Reference summary to answer

### **On-Demand:**

User can request:
```
"Load project context"
"What do you remember about this project?"
"Show me previous decisions"
```

---

## What to Capture in Summary

### **MUST Include:**

1. **Technical Decisions**
   - Technology choices (JWT vs Session, REST vs GraphQL)
   - Architecture patterns used
   - Why these choices were made

2. **User Preferences** (project-specific)
   - Model selection preferences
   - Planning threshold
   - Test policy preference
   - Code style preferences

3. **Files Modified**
   - What changed
   - Why it changed
   - Key functions/components added

4. **Important Context**
   - What NOT to suggest (rejected alternatives)
   - Established patterns (don't violate)
   - Known issues or constraints

5. **Pending Work**
   - Clear TODO list
   - Next logical steps

### **SKIP (Don't Capture):**

1. **Sensitive Data**
   - API keys, passwords, tokens
   - Personal information
   - Client confidential data

2. **Temporary Context**
   - Debugging output
   - Trial-and-error attempts
   - One-off experiments

3. **Obvious Info**
   - Standard framework conventions
   - Common knowledge
   - Generic best practices

---

## Privacy & Security

### **100% Local:**

- ✅ All summaries stored locally in `~/.claude/memory/sessions/`
- ✅ No external API calls for storage
- ✅ No cloud sync
- ✅ Plain markdown (human-readable)

### **User Control:**

**View all sessions:**
```bash
ls -la ~/.claude/memory/sessions/{project-name}/
```

**Read summary:**
```bash
cat ~/.claude/memory/sessions/{project-name}/project-summary.md
```

**Edit summary:**
```bash
nano ~/.claude/memory/sessions/{project-name}/project-summary.md
```

**Delete old sessions:**
```bash
rm ~/.claude/memory/sessions/{project-name}/session-2026-01-20*.md
```

**Delete entire project context:**
```bash
rm -rf ~/.claude/memory/sessions/{project-name}/
```

**Delete sensitive content:**
Just edit the MD file and remove lines!

---

## Integration with Existing Policies

### **Works WITH:**

1. **core-skills-mandate.md**
   - Session summaries INCLUDE policy stats
   - Track model selection, planning decisions
   - Log compliance

2. **proactive-consultation-policy.md**
   - Save user's decision preferences per project
   - Don't ask same question twice for same project

3. **git-auto-commit-policy.md**
   - Session end triggers summary + commit
   - Checkpoint summaries on git commits

4. **file-management-policy.md**
   - Session summaries stored in memory/ folder
   - Old sessions can be archived/deleted

### **🛡️ PROTECTED from Context Auto-Cleanup:**

**CRITICAL:** Session memory files are **NEVER affected** by context management auto-cleanup!

**What Context Cleanup Does:**
- ✅ Clears old conversation messages
- ✅ Compacts MCP responses
- ✅ Removes completed task details
- ✅ Summarizes long prompts

**What Context Cleanup NEVER Does:**
- ❌ Delete session memory files (`~/.claude/memory/sessions/**`)
- ❌ Remove project-summary.md
- ❌ Clean up session-*.md records
- ❌ Touch policy files or configurations

**Why This Matters:**
- Session memory = persistent storage (like git history)
- Context cleanup = temporary memory management (like RAM)
- Mixing them would destroy user's project context!

**Separation:**
```
Context Cleanup (Temporary):
  - Conversation context
  - In-session task details
  - MCP responses
  - Debugging output
  ↓
  Clears every session (intentional)

Session Memory (Persistent):
  - ~/.claude/memory/sessions/
  - project-summary.md
  - session-*.md files
  ↓
  Persists forever (intentional)
```

### **Enhances:**

- **Context management** - Perfect historical context
- **Model selection** - Remember per-project preferences
- **Planning intelligence** - Remember complexity thresholds
- **User preferences** - No re-asking same questions

---

## Summary Generation Process

### **How Claude Generates Summary:**

**Analysis Sources:**
1. Conversation history (what user requested)
2. Tool usage (files read, edited, created)
3. Git diff (what actually changed)
4. User decisions made (from AskUserQuestion responses)
5. Policies applied (from logs)

**Format:**
1. Extract key points
2. Identify decisions
3. List files modified
4. Note user preferences
5. Suggest next steps

**Quality:**
- Concise (not verbose)
- Actionable (useful for next session)
- Accurate (based on actual work done)
- Organized (easy to scan)

---

## Folder Naming Convention

**Project Name Detection:**

```bash
# Option 1: Use current folder name
PROJECT_NAME=$(basename "$PWD")

# Option 2: Use git repo name
PROJECT_NAME=$(basename $(git rev-parse --show-toplevel 2>/dev/null) || basename "$PWD")

# Option 3: User override (in project .clauderc)
# .clauderc file:
#   CLAUDE_PROJECT_NAME="techdeveloper-ui"
```

**Examples:**
```
/c/Users/techd/Documents/workspace/techdeveloper/frontend/techdeveloper-ui
→ sessions/techdeveloper-ui/

/c/Users/techd/Documents/workspace/medspy/backend/medspy-node
→ sessions/medspy-node/

Custom override in .clauderc:
→ sessions/custom-project-name/
```

---

## Workflow Examples

### **Example 1: New Project (First Session)**

```
Session starts in: techdeveloper-ui/
Claude checks: ~/.claude/memory/sessions/techdeveloper-ui/project-summary.md
Result: File doesn't exist
Claude: Starts fresh (no previous context)

[Work happens: User implements auth]

Session ends:
Claude: Generates summary
Saves to:
  - sessions/techdeveloper-ui/session-2026-01-25-15-00.md
  - sessions/techdeveloper-ui/project-summary.md (created)
```

### **Example 2: Continuing Project (Second Session)**

```
Session starts in: techdeveloper-ui/
Claude checks: ~/.claude/memory/sessions/techdeveloper-ui/project-summary.md
Result: File exists! ✅
Claude loads:
  - JWT auth is implemented
  - User prefers Haiku for searches
  - User chose REST over GraphQL
  - Password reset is pending

User: "Add password reset"
Claude: "I see JWT auth is already implemented in auth.service.ts.
         I'll add password reset following the same pattern.
         Should I use the existing error handling approach?"

[User feels continuity! Claude remembers context!]
```

### **Example 3: Switching Projects**

```
Morning session in: techdeveloper-ui/
Claude loads: techdeveloper-ui context ✅

Afternoon session in: medspy-node/
Claude detects project change
Claude loads: medspy-node context ✅
(Doesn't confuse with techdeveloper context!)
```

---

## Maintenance

### **Storage Management:**

**Growth rate:**
- ~1-2 KB per session summary
- ~5-10 KB project summary
- 100 sessions = ~200 KB (negligible)

**Cleanup strategy:**
```bash
# Archive old sessions (older than 30 days)
find ~/.claude/memory/sessions/ -name "session-*.md" -mtime +30 -exec mv {} ~/.claude/memory/archive/ \;

# Delete archived sessions (older than 90 days)
find ~/.claude/memory/archive/ -name "session-*.md" -mtime +90 -delete

# Or manual cleanup anytime
rm ~/.claude/memory/sessions/old-project/session-2025-*.md
```

**project-summary.md:**
- Keep updated (don't let it get stale)
- Review and edit manually if needed
- Regenerate if confused (delete and let Claude rebuild)

---

## Logging

**Session memory actions should be logged:**

```bash
# When summary is saved
echo "[$(date '+%Y-%m-%d %H:%M:%S')] session-memory | summary-saved | project-name" >> ~/.claude/memory/logs/policy-hits.log

# When context is loaded
echo "[$(date '+%Y-%m-%d %H:%M:%S')] session-memory | context-loaded | project-name" >> ~/.claude/memory/logs/policy-hits.log

# Update counter
policy="session-memory" && counter_file=~/.claude/memory/logs/policy-counters.txt && \
current=$(grep "^$policy=" "$counter_file" 2>/dev/null | cut -d'=' -f2 || echo "0") && \
new=$((current + 1)) && \
sed -i "s/^$policy=.*/$policy=$new/" "$counter_file" 2>/dev/null || echo "$policy=$new" >> "$counter_file"
```

---

## Status

**ACTIVE**: This policy provides persistent memory across sessions.
**Version**: 1.0.0
**Created**: 2026-01-25
**Privacy**: 100% local, 0% cloud
**Dependencies**: None (just markdown files)
**Complexity**: Minimal (simple file read/write)
**User Control**: 100% (manual file management)

---

## Success Metrics

**Track:**
- Number of projects with summaries
- Number of sessions recorded
- Context load success rate
- User satisfaction (fewer re-explanations)

**Expected improvement:**
- Session startup context: 0% → 80%+ (huge win!)
- User re-explanation time: 50% reduction
- Claude accuracy on project context: 90%+
- Privacy preserved: 100% ✅

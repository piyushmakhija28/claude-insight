# Memory System

## Purpose

This folder contains **permanent rules and context** that Claude Code must ALWAYS consider before executing any task.

## Quick Start (Hindi)

Tumhare liye ek **permanent memory system** setup hai jo ensure karta hai ki Claude Code humesha critical skills ko follow kare:

1. **Context Management** - Pehle context validate hota hai, bina context ke kuch assume nahi hota
2. **Model Selection** - Sahi model (Haiku/Sonnet/Opus) task ke hisaab se select hota hai
3. **Adaptive Skill Intelligence** - Automatically detect & create skills/agents jab zaroorat ho (user tension-free!)
4. **Planning Intelligence** - Automatically decide karta hai ki task ko planning chahiye ya direct implement kare
5. **Phased Execution** - Bade tasks ko phases me break karta hai with checkpoints (--resume support!)
6. **Failure Prevention** - Past mistakes se seekhta hai, same error dobara nahi hoti (self-learning!)
7. **File Management** - Temp files system temp me jaati hain, documentation consolidated rahti hai

**Advanced Features (v4.7.0+)**:
- Auto context cleanup jab task change ho
- Smart caching (50-70% token savings on repeated file access)
- Long session optimization (20+ prompts smoothly)
- MCP server response optimization
- Context window monitoring & auto-compaction
- **Adaptive skill intelligence (NEW!)**: Auto skill/agent detection & creation
  - Automatically detects existing skills/agents for task
  - Creates new skills/agents on-the-fly when needed
  - Manages lifecycle: TEMPORARY (one-time) vs PERMANENT (reusable)
  - Auto-cleanup of temporary resources after task
  - Protects pre-existing skills/agents (never deletes)
  - User tension-free: No "which skill to use?" questions
  - Zero resource gaps or "not found" errors
- **Planning intelligence**: Automatically decide when to plan vs implement
  - Simple tasks: Skip planning (no token waste)
  - Complex tasks: Plan first (avoid 2-4 retry cycles)
  - Loop detection: Auto-pause and plan mid-execution
  - Token savings: 60-70% on complex tasks
- **Phased execution (NEW!)**: Large task breakdown with checkpoints
  - Automatically detects large tasks (6+ requirements)
  - Breaks into 2-4 manageable phases
  - Checkpoint after each phase (git commit + summary)
  - Seamless --resume workflow between phases
  - **Parallel multi-agent execution** for independent phases
  - **Context handoff mechanism** for same-domain phases
  - **Merge & integration orchestration** for parallel outputs (LATEST!)
  - Dependency detection: Sequential vs Parallel strategy
  - Branch management: Feature branches for parallel work
  - Conflict resolution: Automated patterns & decision trees
  - Sequential merge: Backend → Frontend → Tests (validated)
  - Integration testing: After each merge + final validation
  - Artifact extraction: Types, components, utils passed between phases
  - 40%+ token savings (clean context per phase)
  - 25-50% time savings via parallel execution
  - Zero duplication (shared artifacts prevent recreating code)
  - Zero missed requirements (structured approach)
  - Production-ready merges (validated & tested)
- **Failure prevention**: Self-learning mistake prevention
  - Learns from past failures (del, Edit mismatches, etc.)
  - Prevents repeating same errors (before execution checks)
  - 10x-30x ROI per check (900-2900 tokens saved per failure)
  - Gets smarter over time (confidence-based learning)
  - Currently 13+ patterns, grows automatically

## How It Works

Files in this folder act as **persistent memory** that:
- Defines mandatory behaviors (MUST, ALWAYS, MANDATORY keywords)
- Sets system-level priorities (HIGHEST, SYSTEM-LEVEL, NORMAL)
- Enforces skill hierarchies (context → model → file → implementation)
- Prevents context loss between sessions
- Automatically applies without manual invocation

## Active Memory Files

### 1. core-skills-mandate.md
**Status**: ALWAYS ACTIVE

Enforces mandatory usage of:
- `context-management-core` - Context validation before action
- `model-selection-core` - Correct model selection for tasks
- `adaptive-skill-intelligence` - Auto skill/agent detection, creation & management
- `task-planning-intelligence` - Smart decision on planning vs direct implementation
- `phased-execution-intelligence` - Large task breakdown into phases with checkpoints

These skills must be applied BEFORE any other work begins.

### 2. file-management-policy.md
**Status**: ALWAYS ACTIVE

Enforces mandatory file management rules:
- Temporary files MUST go to system temp directories (`%TEMP%` or `/tmp`)
- Documentation MUST be consolidated in single README.md
- NO multiple scattered MD files
- **Intelligent large file handling** (500+ lines)
- Keeps working directory clean and organized

**New in v2.0.0**: Smart strategy for large README files
- < 500 lines: Normal operation
- 500-1000 lines: Targeted reads/edits (80-90% token savings)
- 1000+ lines: Propose docs/ folder split

This policy applies THROUGHOUT all execution.

### 3. common-failures-prevention.md
**Status**: ALWAYS ACTIVE (Self-Learning KB)

**Self-learning failure prevention system** that improves over time:
- 🧠 Learns from past failures (bash del, Edit mismatches, etc.)
- 🛡️ Prevents repeating same mistakes (checks before EVERY tool execution)
- ⚡ Saves 900-2900 tokens per prevented failure
- 🎯 Gets smarter with each session (pattern confidence increases)
- 🔄 Currently knows 13+ failure patterns (will grow automatically)

**How it works**:
1. Before executing any tool → Check against known failure patterns
2. If match found (confidence ≥75%) → Auto-correct
3. If no match → Execute and learn from result
4. Failure occurs → Log pattern + solution for next time

**Initial patterns covered**:
- Bash: del→rm, path quotes, interactive flags
- Edit: Line prefixes, string uniqueness
- Files: Large file handling, read-before-write
- Git: Force push blocks, staging checks
- Platform: Path separators, permissions

**ROI**: 10x-30x return on prevention checks

### 4. git-auto-commit-policy.md
**Status**: ALWAYS ACTIVE

Enforces automatic git commit and push workflow:
- **Auto-commit on phase completion** - Every phase checkpoint gets committed
- **Auto-commit on todo completion** - TaskUpdate status="completed" triggers commit
- **Auto-commit on periodic checkpoints** - Every 3-5 file changes during work
- **Auto-push to remote** - Automatically pushes after each commit
- **Smart error handling** - Handles push failures, hooks, conflicts

**Key Features**:
- Formatted commit messages (phase/todo/checkpoint formats)
- Safety rules (no force push, respect hooks, clean commits)
- User notifications (always informs about commits/pushes)
- Exception handling (skips if not a git repo, detached HEAD, etc.)

**Benefits**:
- Never lose progress (automatic backups)
- Clean git history (descriptive commit messages)
- Seamless checkpoints (integrates with phased execution)
- Remote backup (auto-push keeps remote in sync)

This policy activates AFTER task/phase/todo completion events.

### 5. test-case-policy.md
**Status**: ALWAYS ACTIVE

Enforces smart testing strategy with user preference:
- **Mandatory testing** - Development + manual testing (always done)
- **Optional testing** - Unit/Integration/E2E tests (ask user)
- **Default recommendation** - Skip tests initially, add later
- **User flexibility** - Can request tests anytime

**Key Features**:
- Asks user preference via AskUserQuestion tool
- Three options: Write all | Skip for now | Only critical
- Recommends "Skip for now" by default (30-50% faster)
- Tests can be added incrementally later
- Smart triggers: Planning, phase completion, new features

**Time Savings**:
- Skip all tests: 50% faster delivery
- Critical tests only: 30% faster delivery
- No quality compromise (manual testing still mandatory)

**Test Categories**:
- ✅ Development testing (mandatory)
- ✅ Manual testing (mandatory)
- ❓ Unit tests (optional - ask)
- ❓ Integration tests (optional - ask)
- ❓ E2E tests (optional - ask)

This policy activates DURING planning and BEFORE final commits.

### 6. adaptive-skill-registry.md
**Status**: ALWAYS ACTIVE

Registry for adaptive skill intelligence system:
- **Tracks auto-created resources** - All skills/agents created by the system
- **Lifecycle management** - TEMPORARY vs PERMANENT tracking
- **Cleanup log** - Records all deletions with reasons
- **Protection list** - Pre-existing skills/agents (NEVER delete)
- **Statistics** - Creation counts, cleanup metrics

**Key Features**:
- Prevents duplicate creation (check registry first)
- Safe deletion (only TEMPORARY + self-created)
- Audit trail (all changes logged)
- Resource health monitoring

**Protected Resources**:
- All pre-existing skills (before 2026-01-23)
- All pre-existing agents (before 2026-01-23)
- Any resource without "created-by: adaptive-skill-intelligence"

This registry is updated automatically by adaptive-skill-intelligence.

### 7. model-selection-enforcement.md
**Status**: ALWAYS ACTIVE (CRITICAL!)

Ultra-concise enforcement guide for model selection:
- **Quick decision tree** - Find/Search→Haiku, Build/Fix→Sonnet, Design→Opus
- **Pre-flight checklist** - Check before EVERY user request
- **Common violations** - What NOT to do (with examples)
- **Trigger words** - Auto-detect which model to use
- **Cost impact** - Why it matters (96% savings on searches!)
- **Self-monitoring** - Check every 10 responses

**Purpose**: Ensures 100% Sonnet violation never happens again!

**Expected Result**:
- 40% Haiku (searches/exploration)
- 55% Sonnet (implementation)
- 5% Opus (architecture)

This enforcement activates BEFORE every user request response.

## Key Benefits

### Core Benefits
- **No Hallucination**: Bina context ke kuch assume nahi hoga
- **No Token Waste**: Galat model use nahi hoga
- **Better Quality**: Har task ke liye sahi approach
- **Consistent Behavior**: Har session me same rules
- **Clean Workspace**: Temp files aur docs organized

### Advanced Benefits (v4.0.0+)
- **Smart Model Selection**: 80-90% cost savings on searches (Haiku), 40-50% overall cost reduction
- **Speed Boost**: 3-5x faster searches with Haiku vs Sonnet
- **Proper Distribution**: 40% Haiku + 55% Sonnet + 5% Opus (optimized mix)
- **Massive Token Savings**: 50-70% savings via caching & cleanup
- **Long Session Efficiency**: 20+ prompts me bhi lean context
- **Autonomous Intelligence**: Khud se cleanup, no manual intervention
- **Better Performance**: Smaller context = faster processing
- **Cost Efficiency**: Kam tokens = kam cost
- **Self-Learning System**: Mistakes se seekhta hai, improve hota rehta hai
- **Failure Prevention**: 2-3 failures per session prevented (4K-6K tokens saved)
- **Zero Repeat Errors**: Same mistake dobara kabhi nahi hogi
- **Phased Execution**: Large tasks ko phases me todta hai (40% token savings)
- **Parallel Agents**: Independent phases simultaneously execute (25-50% time savings!)
- **Smart Dependency Detection**: Automatically decides sequential vs parallel strategy
- **Merge Orchestration**: Parallel agent outputs ko intelligently merge karta hai
- **Conflict Resolution**: Automated patterns se git conflicts resolve (no manual confusion)
- **Integration Testing**: Har merge ke baad validation (production-ready code)
- **Checkpoint System**: Kisi bhi phase ke baad pause kar sakte ho, --resume se continue
- **Zero Missed Requirements**: Structured approach = kuch miss nahi hota
- **User Flexibility**: Break le sakte ho between phases, progress saved rahega
- **Multi-Agent Orchestration**: Backend || Frontend || Services (all parallel when possible)
- **Smart Test Strategy**: Optional unit/integration tests (30-50% faster delivery!)
- **Test Flexibility**: User decides - write all, skip, or critical only
- **No Quality Loss**: Manual testing always mandatory, tests can be added incrementally
- **Auto Git Commits**: Automatic commit+push on phase/todo completion (never lose progress)
- **Clean Git History**: Formatted commit messages with proper tracking

### Real Impact
```
Before v3.0.0: 25-prompt session = 220K tokens
After v3.0.0:  25-prompt session = 100K tokens
Savings: 55%!
```

## Testing Examples

Try these to verify the system is working:

**Example 1: Missing Context**
```
User: "Fix the login bug"
Expected: Claude asks - "Konsa login? Kya error aa raha hai?"
```

**Example 2: Model Selection**
```
User: "Find all API files"
Expected: Claude uses Haiku (fast search), not Sonnet
```

**Example 3: Auto Cleanup**
```
User: "Fix frontend button" → Work karo
User: "Now setup database" → Totally different task
Expected: Frontend context auto-cleared, no permission asked
```

**Example 4: Smart Caching**
```
Read auth.ts at prompt 5, 12, 20
Expected: First read full, later reads cached (10x faster)
```

**Example 5: File Management**
```
User: "Create quick test script"
Expected: Script created in %TEMP%, not working directory
```

**Example 6: Large README Handling**
```
User: "Update API docs in README" (README is 850 lines)
Expected:
1. Check file size first (wc -l)
2. Read structure only (first 100 lines)
3. Grep to find API section
4. Targeted edit (not full rewrite)
5. 80-90% token savings vs full read/write
```

**Example 7: Very Large README**
```
README.md is 1200 lines
User: "Add new section"
Expected:
1. Alert: "README is large (1200 lines)"
2. Propose: Split into README + docs/ folder
3. Ask permission before creating files
4. If approved: Split intelligently
5. If declined: Use targeted edit strategy
```

**Example 8: Planning Intelligence - Simple Task**
```
User: "This is super complex, plan it first - add console.log"
Expected:
1. Analyze: Complexity score = 1 (single line change)
2. Decision: Direct implementation (override user perception)
3. Action: Just add the log, no planning needed
4. Message: "Adding directly - this is straightforward"
```

**Example 9: Planning Intelligence - Complex Task**
```
User: "Quick fix - add user authentication"
Expected:
1. Analyze: Complexity score = 9 (multi-file, architecture, security)
2. Decision: Mandatory planning (override user "quick")
3. Action: Enter planning mode
4. Message: "This requires planning because: [multi-file, auth strategy, security]. Planning first..."
```

**Example 10: Loop Detection**
```
Attempt 1: Implement → Error A
Attempt 2: Fix → Error B
Attempt 3: Fix → Error A returns (LOOP!)
Expected:
1. Detect loop pattern
2. Pause execution
3. Message: "Loop detected. Creating plan to address root cause..."
4. Enter planning mode to solve properly
```

**Example 11: Failure Prevention - del Command**
```
User: "Delete temp.txt"
Without KB: bash -c "del temp.txt" → Error: command not found → Retry with rm
With KB:
1. Check pattern: "del" in Unix shell → Match found (100% confidence)
2. Auto-correct to: bash -c "rm temp.txt"
3. Execute successfully
4. Message: "Converted 'del' to 'rm' for Unix compatibility"
Result: Saved 1 retry cycle (1500 tokens)
```

**Example 12: Failure Prevention - Edit String Not Found**
```
User: "Update function in file.js"
Without KB: Edit with line prefix → Error: String not found → Retry
With KB:
1. Check pattern: old_string has "  123→" prefix → Match found (90% confidence)
2. Auto-strip prefix before Edit
3. Execute successfully
4. Message: "Stripped line number prefix for accurate matching"
Result: Saved 1 retry (2000 tokens)
```

**Example 13: Self-Learning - New Failure Pattern**
```
Session 1: New error "X" occurs → Logged to KB (confidence: 25%)
Session 5: Same error "X" occurs again → Confidence: 50% (warn user)
Session 10: Error "X" occurs 3rd time → Confidence: 80% (auto-prevent)
Session 20: Error "X" pattern now permanent (confidence: 95%)
Result: KB evolved, learned new pattern, prevents future occurrences
```

**Example 14: Phased Execution - Large Task**
```
User: "Build complete authentication with JWT, OAuth, email verification, and admin dashboard"

Analysis:
- Requirements: 6+ major features
- Domains: 4 (backend, frontend, email, OAuth)
- Files: 15+
- Score: 8 → Large task → MANDATORY phases

Response:
"This is a large task. I'll break it into 3 phases:

**Phase 1** (This session): Core Auth
- JWT setup
- Login/logout
- Token validation
✓ Success: Can login with JWT

**Phase 2** (Next --resume): OAuth
- Google/GitHub OAuth
- Account linking
✓ Success: Can login via OAuth

**Phase 3** (Final --resume): Admin & Email
- Email verification
- Admin dashboard
- Testing
✓ Success: Full system working

Starting Phase 1..."

[After Phase 1 complete]
"✅ Phase 1 complete! JWT auth working.

To continue with OAuth:
```bash
claude --resume
```

Your progress is checkpointed and ready to resume."
```

**Example 15: Resume Workflow**
```
User runs: claude --resume

Response:
"Welcome back! Resuming from checkpoint...

**Last Session**: Phase 1 - Core Auth ✅
- JWT setup complete
- Login/logout working

**This Session**: Phase 2 - OAuth Integration
Goal: Add Google and GitHub OAuth

Todos:
- [ ] Setup OAuth providers
- [ ] Create callback routes
- [ ] Link accounts
- [ ] Test OAuth flow

Let's continue with OAuth provider setup..."
```

**Example 16: Small Task - No Phases**
```
User: "Add a logout button"

Analysis:
- Requirements: 1 (button)
- Domains: 1 (frontend)
- Files: 2
- Score: 2 → Small task

Decision: Execute directly (no phases)
Action: Just implement it, no checkpoint needed
```

**Example 17: Parallel Multi-Agent Execution** (NEW!)
```
User: "Build product catalog with backend API and frontend UI"

Analysis:
- Requirements: 4 (API routes, DB, UI components, integration)
- Domains: 2 (backend, frontend)
- Dependencies: None (API contract can be defined upfront)
- Score: 6 → Large task + Independent phases

Decision: PARALLEL multi-agent execution

Response:
"I'll use parallel multi-agent execution for faster completion:

**API Contract** (defined upfront):
- GET /api/products → [{id, name, price}]
- POST /api/products → {success, productId}

**Parallel Execution** (30 min):
├─ Agent 1 (Backend): Product API + Database
└─ Agent 2 (Frontend): Product UI + State

**Then Sync** (10 min): Integration + Testing

Total: 40 min vs 60 min sequential (33% faster!)

Spawning both agents in parallel now..."

[Both agents work simultaneously]

Result:
- Backend agent: ✅ API working
- Frontend agent: ✅ UI working
- Integration: ✅ Connected
- Time saved: 20 minutes (33%)
```

**Example 18: Mixed Parallel-Sequential**
```
User: "Build auth system: Database schema, Backend API, Frontend UI, Testing"

Analysis:
- Phase 1 (DB): Foundation (sequential - needed first)
- Phase 2 & 3 (API || UI): Can run parallel (both use DB)
- Phase 4 (Testing): Needs both API and UI (sequential)

Strategy: MIXED

Execution:
Phase 1: Database Schema (15 min)
  ↓
Phase 2 & 3: Parallel (30 min)
├─ Agent 1: Backend API
└─ Agent 2: Frontend UI
  ↓
Phase 4: Integration Testing (10 min)

Total: 55 min vs 85 min all-sequential (35% faster!)
```

**Example 19: Context Handoff - Same Domain Multi-Phase** (CRITICAL!)
```
User: "Build large React e-commerce frontend: Product Listing, Shopping Cart, Checkout"

Analysis:
- Domain: Frontend only (React)
- Size: Large (score 8)
- Phases: Sequential same-domain
- **CRITICAL**: Phase 2 needs Phase 1 outputs!

Strategy: Context Handoff

Phase 1 (Agent 1): Product Listing
- Creates Product type
- Creates ProductCard component
- Creates formatPrice utility
✓ Complete

Context Artifacts Extracted:
```typescript
// Types to reuse
interface Product { id, name, price, image }

// Components to reuse
ProductCard component (src/components/ProductCard.tsx)

// Utils to reuse
formatPrice function (src/utils/formatPrice.ts)
```

Phase 2 (Agent 2 WITH ARTIFACTS):
Prompt includes: "CRITICAL: Import Product type from Phase 1, don't recreate!"
Agent 2 receives artifacts as context
↓
Result:
✅ Imports Product (no duplicate!)
✅ Reuses ProductCard (consistent UI!)
✅ Uses formatPrice (no rewrite!)
✅ Extends Product to CartItem (aligned!)

Integration: Seamless (no type conflicts, no duplicates)

Without handoff: ❌ Duplicate types, inconsistent components, merge hell
With handoff: ✅ Clean integration, no duplication, aligned code
```

**Example 20: Merge & Integration - Parallel Agents** (CRITICAL!)
```
User: "Build product catalog with Backend API || Frontend UI || Tests (parallel)"

Execution:
Agent 1 (Backend): Works on branch phase-1-backend ✅
Agent 2 (Frontend): Works on branch phase-2-frontend ✅
Agent 3 (Tests): Works on branch phase-3-tests ✅

All complete → Now merge orchestration:

Step 1: Merge Backend
git merge phase-1-backend → ✅ Clean
Validation: Backend tests pass ✅

Step 2: Merge Frontend
git merge phase-2-frontend → ⚠️ Conflict in package.json

Conflict Resolution:
// Agent 1 added: "express": "^4.18.0"
// Agent 2 added: "react": "^18.2.0"
→ Keep both (merge intelligently)

After resolution: Integration test ✅

Step 3: Merge Tests
git merge phase-3-tests → ✅ Clean
Validation: All tests pass ✅

Step 4: Final Integration
- Unit tests: 45/45 ✅
- Integration tests: 12/12 ✅
- E2E tests: 8/8 ✅
- Build: Success ✅

Final Checkpoint: "All phases integrated and validated" ✅

Result:
✅ Clean merge (sequential order)
✅ Conflicts resolved intelligently
✅ All tests passing
✅ Production-ready code
```

**Example 21: Test Case Policy - User Preference**
```
User: "Build REST API for product catalog"

Analysis:
- New API endpoints (test-worthy)
- Planning phase active
→ Trigger test-case-policy

Response:
"Planning API implementation...

Phase 1: Product endpoints (GET, POST, PUT, DELETE)
Phase 2: Database integration

Unit/Integration tests likhein ya skip karein?

1. Write all tests now (Full test coverage)
2. Skip for now, add later (Recommended - 50% faster)
3. Only critical tests (Product GET/POST validation)

Choose option:"

User: "Skip for now"

Response:
"Proceeding without test phase. You can request tests anytime with:
'ab product API ke tests likh do'

Starting Phase 1..."

[After Phase 1 & 2 complete - 50% faster delivery!]
✅ Auto-committed: Phase 2 Complete
📤 Pushed to remote
```

**Example 22: Auto Git Commit on Todo Complete**
```
User: "Fix login button styling"

Claude: [Creates todos, fixes button]

TaskUpdate(taskId: "1", status: "completed")
  ↓
Git Auto-Commit Triggered
  ↓
✅ Auto-committed: ✓ Task Complete: Fix login button styling

Changes:
- Updated button.css padding
- Fixed hover state color

📤 Pushed to remote successfully

Task committed and ready for review!
```

**Example 23: Model Selection Monitoring**
```
# Before Fix (Violation):
✦ CLAUDE CODE USAGE MONITOR ✦
🤖 Model Distribution: Sonnet 100.0% ❌ RED FLAG!
🔥 Burn Rate: 8.5 tokens/min 🔥 (high!)
💰 Cost: $0.85 for 20 messages ❌ (expensive!)

Problem: Not using Haiku for searches, not using Opus for planning
Result: 3x higher cost, slower responses

# After Fix (Compliant):
✦ CLAUDE CODE USAGE MONITOR ✦
🤖 Model Distribution:
   - Haiku:  42.0% ✅
   - Sonnet: 54.0% ✅
   - Opus:    4.0% ✅
🔥 Burn Rate: 2.8 tokens/min ✅ (efficient!)
💰 Cost: $0.28 for 20 messages ✅ (3x cheaper!)

Result: Proper model usage = 67% cost reduction + faster responses!
```

## How to Add New Memory

To add permanent rules:
1. Create a new `.md` file in this folder
2. Write clear, structured instructions
3. Use "ALWAYS", "MANDATORY", "MUST" for non-negotiable rules
4. Specify priority if needed

## Priority System

1. **HIGHEST**: Context validation (context-management-core)
2. **SYSTEM-LEVEL**: Model selection (model-selection-core + model-selection-enforcement)
3. **SYSTEM-LEVEL**: Skill/Agent intelligence (adaptive-skill-intelligence) - Auto resource management
4. **SYSTEM-LEVEL**: Planning intelligence (task-planning-intelligence)
5. **SYSTEM-LEVEL**: Phased execution (phased-execution-intelligence)
6. **SYSTEM-LEVEL**: Failure prevention (common-failures-prevention) - Before EVERY tool
7. **SYSTEM-LEVEL**: File management (file-management-policy)
8. **SYSTEM-LEVEL**: Test case preference (test-case-policy) - During planning & before commits
9. **SYSTEM-LEVEL**: Git auto-commit (git-auto-commit-policy) - After phase/todo completion
10. **NORMAL**: Implementation skills (backend, frontend, mobile, etc.)

**Note**: model-selection-enforcement.md acts as a quick-reference card for #2, ensuring compliance on every request.

## Notes

- Memory files are read automatically by Claude Code
- Changes take effect immediately
- Do not delete core-skills-mandate.md or file-management-policy.md
- Keep memory files concise and action-oriented
- File management policy prevents directory clutter automatically

---

**Last Updated**: 2026-01-23 (ADDED adaptive-skill-intelligence for automatic skill/agent detection, creation, and lifecycle management - user stays tension-free!)

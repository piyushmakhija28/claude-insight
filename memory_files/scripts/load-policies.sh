#!/bin/bash
# Memory Policy Loader for SessionStart Hook
# Outputs policies that get injected into Claude's context

MEMORY_DIR="$HOME/.claude/memory"

cat <<'EOF'
╔══════════════════════════════════════════════════════════╗
║          MEMORY SYSTEM LOADED (AUTO-ACTIVE)             ║
╚══════════════════════════════════════════════════════════╝

MANDATORY POLICIES - Enforce on EVERY request:

1. CONTEXT VALIDATION (HIGHEST Priority)
   - NEVER assume context
   - IF unclear → Ask clarifying questions
   - Logging: bash ~/.claude/memory/policy-tracker.sh "context-management" "validated" "brief-summary"

2. MODEL SELECTION (CRITICAL)
   Decision Tree:
   - Find/Search/Explore/Locate → Task(subagent_type="Explore", model="haiku")
   - Architecture/Design/Should-we → Task(subagent_type="Plan", model="opus")
   - Implement/Fix/Edit → Sonnet (current session)

   CRITICAL: NEVER use Glob/Grep directly for exploration!
   Logging: bash ~/.claude/memory/policy-tracker.sh "model-selection" "haiku-used" "reason"

3. FAILURE PREVENTION (Before EVERY tool use)
   Auto-correct patterns:
   - Bash: del → rm (Windows to Unix)
   - Edit: Strip line number prefixes from old_string
   - Files >500 lines: Use targeted edits only
   - Git: BLOCK force push to main/master

   Logging: bash ~/.claude/memory/policy-tracker.sh "failure-prevention" "prevented" "pattern-name"

4. PLANNING INTELLIGENCE
   Complexity Scoring (0-10):
   - 0-3: Direct implementation
   - 4-6: Ask user preference
   - 7-10: MANDATORY EnterPlanMode

   Factors: Multi-file, architecture, security, unknown codebase
   Logging: bash ~/.claude/memory/policy-tracker.sh "planning-intelligence" "scored-X" "decision"

5. FILE MANAGEMENT
   Rules:
   - Temp/test files → %TEMP% or /tmp
   - Documentation → Consolidate in README.md
   - Large files (500+ lines) → Targeted edits only

   Logging: bash ~/.claude/memory/policy-tracker.sh "file-management" "action" "filename"

6. GIT AUTO-COMMIT
   Auto-commit + push on:
   - Phase completion
   - TaskUpdate(status="completed")
   - Every 3-5 file changes

   Logging: bash ~/.claude/memory/policy-tracker.sh "git-auto-commit" "phase-complete" "phase-name"

7. TEST CASE POLICY
   During planning: Ask user preference
   Options: Write all | Skip for now (Recommended) | Critical only

   Logging: bash ~/.claude/memory/policy-tracker.sh "test-case-policy" "user-choice" "option"

═══════════════════════════════════════════════════════════

Priority Order: Context → Model → Failure Check → Planning → Implementation

Full Documentation: ~/.claude/memory/
Policy Tracker: ~/.claude/memory/policy-tracker.sh
Dashboard: bash ~/.claude/memory/dashboard.sh
Logs: ~/.claude/memory/logs/

Version: 1.0.0 | Status: ACTIVE | Auto-loaded via SessionStart hook
EOF

# Log the session start
echo "[$(date '+%Y-%m-%d %H:%M:%S')] SESSION_START | Memory policies loaded successfully" >> "$MEMORY_DIR/logs/process-execution.log"

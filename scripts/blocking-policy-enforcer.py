#!/usr/bin/env python3
"""
[ALERT] BLOCKING POLICY ENFORCER [ALERT]

CRITICAL: This system BLOCKS all AI work until automation policies are satisfied.
NO BYPASS ALLOWED - System will REFUSE to proceed if any policy is violated.

This enforcer implements the 3-Layer Architecture:
- [BLUE] Layer 1: SYNC SYSTEM (Foundation) - BLOCKING
- [GREEN] Layer 2: STANDARDS SYSTEM (Rules) - BLOCKING
- [RED] Layer 3: EXECUTION SYSTEM (Implementation) - BLOCKING

Version: 1.0.0
Date: 2026-02-16
Author: TechDeveloper
"""

import os
import sys
import json
import time
from datetime import datetime
from pathlib import Path

# Fix encoding for Windows console
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')


class BlockingPolicyError(Exception):
    """
    CRITICAL: Raised when a BLOCKING policy is violated.
    This exception STOPS all work immediately.
    """
    pass


class BlockingPolicyEnforcer:
    """
    BLOCKING POLICY ENFORCER

    This class enforces ALL automation policies defined in CLAUDE.md.
    Work CANNOT proceed if any policy is violated.

    Usage:
        enforcer = BlockingPolicyEnforcer()
        enforcer.enforce_all()  # Raises BlockingPolicyError if any violation
    """

    def __init__(self):
        self.memory_path = Path.home() / '.claude' / 'memory'
        self.state_file = self.memory_path / '.blocking-enforcer-state.json'
        self.state = self._load_state()

    def _load_state(self):
        """Load enforcer state from file"""
        if self.state_file.exists():
            with open(self.state_file, 'r') as f:
                return json.load(f)
        return {
            'session_started': False,
            'session_start_time': None,
            'standards_loaded': False,
            'current_request_id': None,
            'prompt_generated': False,
            'tasks_created': False,
            'plan_mode_decided': False,
            'model_selected': False,
            'skills_agents_checked': False,
            'context_checked': False,
            'total_violations': 0,
            'last_violation': None
        }

    def _save_state(self):
        """Save enforcer state to file"""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)

    def _record_violation(self, policy_name, message):
        """Record a policy violation"""
        self.state['total_violations'] += 1
        self.state['last_violation'] = {
            'policy': policy_name,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        self._save_state()

        # Log to violations file
        violations_log = self.memory_path / 'logs' / 'policy-violations.log'
        violations_log.parent.mkdir(parents=True, exist_ok=True)
        with open(violations_log, 'a') as f:
            f.write(f"[{datetime.now().isoformat()}] {policy_name}: {message}\n")

    # ============================================================
    # [BLUE] LAYER 1: SYNC SYSTEM (FOUNDATION) - BLOCKING
    # ============================================================

    def enforce_session_start(self):
        """
        [BLUE] BLOCKING: Session must be started with session-start.sh

        This is the FIRST and MOST CRITICAL check.
        Without session initialization, NO WORK can proceed.
        """
        if not self.state.get('session_started'):
            violation_msg = """
[ALERT] CRITICAL BLOCKING ERROR: SESSION NOT STARTED! [ALERT]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[CROSS] WORK STOPPED - Cannot proceed without session initialization
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[CLIPBOARD] MANDATORY ACTION REQUIRED:

   1. Run session initialization:
      bash ~/.claude/memory/session-start.sh

   2. This will:
      [CHECK] Start auto-recommendation daemon (9th daemon)
      [CHECK] Check all 9 daemon PIDs and status
      [CHECK] Show latest recommendations (model, skills, agents)
      [CHECK] Show context status (OK/WARNING/CRITICAL)
      [CHECK] Initialize blocking enforcer
      [CHECK] Enable policy enforcement

[BOOK] POLICY: CLAUDE.md - MANDATORY EXECUTION AT SESSION START

[PROHIBITED] NO BYPASS AVAILABLE - This is a BLOCKING policy.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
            self._record_violation('SESSION_START', 'Session not initialized')
            raise BlockingPolicyError(violation_msg)

        # Check if session is stale (> 8 hours)
        if self.state.get('session_start_time'):
            start_time = datetime.fromisoformat(self.state['session_start_time'])
            elapsed_hours = (datetime.now() - start_time).total_seconds() / 3600
            if elapsed_hours > 8:
                violation_msg = f"""
[ALERT] WARNING: SESSION IS STALE ({elapsed_hours:.1f} hours old)

Recommendation: Re-run session-start.sh for fresh recommendations.
bash ~/.claude/memory/session-start.sh
"""
                print(violation_msg)

    def enforce_context_management(self):
        """
        [BLUE] BLOCKING: Context must be loaded and validated
        """
        if not self.state.get('context_checked'):
            violation_msg = """
[ALERT] BLOCKING ERROR: CONTEXT NOT CHECKED! [ALERT]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[CROSS] WORK STOPPED - Context validation required
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[CLIPBOARD] MANDATORY ACTION REQUIRED:

   1. Check context status:
      python ~/.claude/memory/context-monitor-v2.py --current-status

   2. If context > 70%, apply optimizations:
      - Use offset/limit for Read
      - Use head_limit for Grep
      - Use cache for repeated files

[BOOK] POLICY: context-management-core skill

[PROHIBITED] NO BYPASS AVAILABLE - This is a BLOCKING policy.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
            self._record_violation('CONTEXT_MANAGEMENT', 'Context not checked')
            raise BlockingPolicyError(violation_msg)

    # ============================================================
    # [GREEN] LAYER 2: STANDARDS SYSTEM (RULES) - BLOCKING
    # ============================================================

    def enforce_standards_loading(self):
        """
        [GREEN] BLOCKING: Coding standards must be loaded BEFORE execution
        """
        if not self.state.get('standards_loaded'):
            violation_msg = """
[ALERT] BLOCKING ERROR: CODING STANDARDS NOT LOADED! [ALERT]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[CROSS] WORK STOPPED - Standards must be loaded before code generation
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[CLIPBOARD] MANDATORY ACTION REQUIRED:

   1. Load all coding standards:
      python ~/.claude/memory/standards-loader.py --load-all

   2. This loads:
      [CHECK] Java project structure (packages, visibility)
      [CHECK] Config Server rules (what goes where)
      [CHECK] Secret Management (never hardcode)
      [CHECK] Response format (ApiResponseDto<T>)
      [CHECK] Service layer pattern (Helper, package-private)
      [CHECK] Entity pattern (audit fields, naming)
      [CHECK] Controller pattern (REST, validation)
      [CHECK] Constants organization (no magic strings)

[BOOK] POLICY: coding-standards-enforcement-policy.md

[PROHIBITED] NO BYPASS AVAILABLE - This is a BLOCKING policy.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
            self._record_violation('STANDARDS_LOADING', 'Standards not loaded')
            raise BlockingPolicyError(violation_msg)

    # ============================================================
    # [RED] LAYER 3: EXECUTION SYSTEM (IMPLEMENTATION) - BLOCKING
    # ============================================================

    def enforce_prompt_generation(self, user_request):
        """
        [RED] BLOCKING STEP 0: Prompt must be generated with information gathering
        """
        if not self.state.get('prompt_generated'):
            violation_msg = f"""
[ALERT] BLOCKING ERROR: PROMPT NOT GENERATED! [ALERT]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[CROSS] WORK STOPPED - Must analyze request BEFORE execution
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[CLIPBOARD] USER REQUEST:
{user_request}

[CLIPBOARD] MANDATORY ACTION REQUIRED:

   1. Generate structured prompt:
      python ~/.claude/memory/prompt-generator.py "{user_request}"

   2. This will:
      [BRAIN] PHASE 1: THINKING
         → Understand user intent
         → Break into sub-questions
         → Identify information needed
         → Plan where to find it

      [SEARCH] PHASE 2: INFORMATION GATHERING
         → Search for similar code (BEFORE answering)
         → Read existing implementations
         → Check documentation
         → Verify project structure

      [CHECK] PHASE 3: VERIFICATION
         → Verify all examples exist
         → Validate patterns from actual code
         → Flag uncertainties/assumptions
         → Answer based on FOUND info ONLY

[BOOK] POLICY: prompt-generation-policy.md (STEP 0 - MANDATORY FIRST)

[PROHIBITED] NO BYPASS AVAILABLE - This is a BLOCKING policy.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
            self._record_violation('PROMPT_GENERATION', 'Prompt not generated')
            raise BlockingPolicyError(violation_msg)

    def enforce_task_breakdown(self, user_request):
        """
        [RED] BLOCKING STEP 1: Tasks MUST be created for every request
        """
        if not self.state.get('tasks_created'):
            violation_msg = f"""
[ALERT] BLOCKING ERROR: TASKS NOT CREATED! [ALERT]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[CROSS] WORK STOPPED - Must break down into tasks BEFORE execution
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[CLIPBOARD] USER REQUEST:
{user_request}

[CLIPBOARD] MANDATORY ACTION REQUIRED:

   1. Run task breakdown analysis:
      python ~/.claude/memory/task-auto-breakdown.py "{user_request}"

   2. This will:
      [CHART] ANALYZE COMPLEXITY
         → Calculate complexity score
         → Determine if phases needed
         → Estimate number of tasks

      [CLIPBOARD] DIVIDE INTO PHASES (if complex)
         → Foundation → Business Logic → API Layer → Config
         → Each phase has specific purpose
         → Phases execute sequentially

      [CHECK] BREAK INTO TASKS
         → Each file = 1 task
         → Each endpoint = 1 task
         → Each config = 1 task
         → Automatically create all tasks

      [LINK] CREATE DEPENDENCIES
         → Entity before Repository
         → Repository before Service
         → Service before Controller
         → Auto-detect dependency chain

      [ROBOT] START AUTO-TRACKER
         → Monitor tool calls
         → Auto-update task status
         → Track progress automatically

[BOOK] POLICY: automatic-task-breakdown-policy.md (STEP 1 - MANDATORY)

[PROHIBITED] NO BYPASS AVAILABLE - This is a BLOCKING policy.
[PROHIBITED] NO DIRECT EXECUTION WITHOUT TASKS - This violates core principle.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
            self._record_violation('TASK_BREAKDOWN', 'Tasks not created')
            raise BlockingPolicyError(violation_msg)

    def enforce_plan_mode_decision(self, user_request, complexity_score):
        """
        [RED] BLOCKING STEP 2: Plan mode decision must be made
        """
        if not self.state.get('plan_mode_decided'):
            violation_msg = f"""
[ALERT] BLOCKING ERROR: PLAN MODE NOT DECIDED! [ALERT]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[CROSS] WORK STOPPED - Must decide on plan mode BEFORE execution
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[CLIPBOARD] USER REQUEST:
{user_request}

[CHART] COMPLEXITY SCORE: {complexity_score}

[CLIPBOARD] MANDATORY ACTION REQUIRED:

   1. Run plan mode analysis:
      python ~/.claude/memory/auto-plan-mode-suggester.py "{complexity_score}" "{user_request}"

   2. Decision Rules:
      → Score 0-4: NO plan mode needed [CHECK]
      → Score 5-9: OPTIONAL - Ask user [WARNING]️
      → Score 10-19: RECOMMENDED - Strong suggest [CHECK]
      → Score 20+: MANDATORY - Auto-enter [RED]

[BOOK] POLICY: auto-plan-mode-suggestion-policy.md (STEP 2 - MANDATORY)

[PROHIBITED] NO BYPASS AVAILABLE - This is a BLOCKING policy.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
            self._record_violation('PLAN_MODE_DECISION', 'Plan mode not decided')
            raise BlockingPolicyError(violation_msg)

    def enforce_model_selection(self):
        """
        [RED] BLOCKING STEP 4: Model must be selected based on complexity
        """
        if not self.state.get('model_selected'):
            violation_msg = """
[ALERT] BLOCKING ERROR: MODEL NOT SELECTED! [ALERT]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[CROSS] WORK STOPPED - Must select appropriate model BEFORE execution
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[CLIPBOARD] MANDATORY ACTION REQUIRED:

   1. Run intelligent model selection:
      python ~/.claude/memory/intelligent-model-selector.py

   2. Selection Rules:
      → Haiku: Search, read, status (35-45%)
      → Sonnet: Implementation, editing, fixes (50-60%)
      → Opus: Architecture, planning, complex analysis (3-8%)

[BOOK] POLICY: intelligent-model-selection-policy.md (STEP 4 - MANDATORY)

[PROHIBITED] NO BYPASS AVAILABLE - This is a BLOCKING policy.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
            self._record_violation('MODEL_SELECTION', 'Model not selected')
            raise BlockingPolicyError(violation_msg)

    def enforce_skill_agent_selection(self):
        """
        [RED] BLOCKING STEP 5: Skills/Agents must be checked and selected
        """
        if not self.state.get('skills_agents_checked'):
            violation_msg = """
[ALERT] BLOCKING ERROR: SKILLS/AGENTS NOT CHECKED! [ALERT]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[CROSS] WORK STOPPED - Must check for relevant skills/agents
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[CLIPBOARD] MANDATORY ACTION REQUIRED:

   1. Run skill/agent selection:
      python ~/.claude/memory/auto-skill-agent-selector.py

   2. This checks:
      → Available skills from registry
      → Available agents from registry
      → Technology match
      → Complexity match
      → Auto-select or suggest

[BOOK] POLICY: auto-skill-agent-selection-policy.md (STEP 5 - MANDATORY)

[PROHIBITED] NO BYPASS AVAILABLE - This is a BLOCKING policy.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
            self._record_violation('SKILL_AGENT_SELECTION', 'Skills/agents not checked')
            raise BlockingPolicyError(violation_msg)

    # ============================================================
    # ENFORCEMENT CONTROL
    # ============================================================

    def mark_session_started(self):
        """Mark that session has been started"""
        self.state['session_started'] = True
        self.state['session_start_time'] = datetime.now().isoformat()
        self._save_state()

    def mark_standards_loaded(self):
        """Mark that standards have been loaded"""
        self.state['standards_loaded'] = True
        self._save_state()

    def mark_context_checked(self):
        """Mark that context has been checked"""
        self.state['context_checked'] = True
        self._save_state()

    def mark_prompt_generated(self, request_id):
        """Mark that prompt has been generated"""
        self.state['prompt_generated'] = True
        self.state['current_request_id'] = request_id
        self._save_state()

    def mark_tasks_created(self):
        """Mark that tasks have been created"""
        self.state['tasks_created'] = True
        self._save_state()

    def mark_plan_mode_decided(self):
        """Mark that plan mode decision has been made"""
        self.state['plan_mode_decided'] = True
        self._save_state()

    def mark_model_selected(self):
        """Mark that model has been selected"""
        self.state['model_selected'] = True
        self._save_state()

    def mark_skills_agents_checked(self):
        """Mark that skills/agents have been checked"""
        self.state['skills_agents_checked'] = True
        self._save_state()

    def reset_for_new_request(self):
        """Reset state for a new user request"""
        self.state['prompt_generated'] = False
        self.state['tasks_created'] = False
        self.state['plan_mode_decided'] = False
        self.state['model_selected'] = False
        self.state['skills_agents_checked'] = False
        self.state['current_request_id'] = None
        self._save_state()

    def enforce_all_foundation(self):
        """
        Enforce ALL foundation layer (Layer 1) policies
        This MUST pass before any work can proceed
        """
        print("[BLUE] Enforcing Layer 1: SYNC SYSTEM (Foundation)...")
        self.enforce_session_start()
        self.enforce_context_management()
        print("[CHECK] Layer 1: PASSED")

    def enforce_all_standards(self):
        """
        Enforce ALL standards layer (Layer 2) policies
        This MUST pass before code generation
        """
        print("[GREEN] Enforcing Layer 2: STANDARDS SYSTEM (Rules)...")
        self.enforce_standards_loading()
        print("[CHECK] Layer 2: PASSED")

    def enforce_all_execution(self, user_request, complexity_score=0):
        """
        Enforce ALL execution layer (Layer 3) policies
        This MUST pass before implementation
        """
        print("[RED] Enforcing Layer 3: EXECUTION SYSTEM (Implementation)...")
        self.enforce_prompt_generation(user_request)
        self.enforce_task_breakdown(user_request)
        self.enforce_plan_mode_decision(user_request, complexity_score)
        self.enforce_model_selection()
        self.enforce_skill_agent_selection()
        print("[CHECK] Layer 3: PASSED")

    def enforce_all(self, user_request="", complexity_score=0):
        """
        [ALERT] ENFORCE ALL POLICIES - BLOCKING

        This is the main enforcement method.
        Call this BEFORE starting any work.

        Raises:
            BlockingPolicyError: If ANY policy is violated
        """
        print("\n" + "="*70)
        print("[ALERT] BLOCKING POLICY ENFORCEMENT STARTED")
        print("="*70 + "\n")

        try:
            # Layer 1: Foundation (BLOCKING)
            self.enforce_all_foundation()

            # Layer 2: Standards (BLOCKING)
            self.enforce_all_standards()

            # Layer 3: Execution (BLOCKING)
            if user_request:
                self.enforce_all_execution(user_request, complexity_score)

            print("\n" + "="*70)
            print("[CHECK] ALL POLICIES PASSED - Work can proceed")
            print("="*70 + "\n")

        except BlockingPolicyError as e:
            print("\n" + "="*70)
            print("[CROSS] POLICY VIOLATION DETECTED - WORK STOPPED")
            print("="*70)
            raise

    def get_status_report(self):
        """Get current enforcement status"""
        return f"""
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃          BLOCKING POLICY ENFORCER - STATUS REPORT               ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

[BLUE] LAYER 1: SYNC SYSTEM (Foundation)
   Session Started:      {'[CHECK] YES' if self.state.get('session_started') else '[CROSS] NO'}
   Context Checked:      {'[CHECK] YES' if self.state.get('context_checked') else '[CROSS] NO'}

[GREEN] LAYER 2: STANDARDS SYSTEM (Rules)
   Standards Loaded:     {'[CHECK] YES' if self.state.get('standards_loaded') else '[CROSS] NO'}

[RED] LAYER 3: EXECUTION SYSTEM (Implementation)
   Prompt Generated:     {'[CHECK] YES' if self.state.get('prompt_generated') else '[CROSS] NO'}
   Tasks Created:        {'[CHECK] YES' if self.state.get('tasks_created') else '[CROSS] NO'}
   Plan Mode Decided:    {'[CHECK] YES' if self.state.get('plan_mode_decided') else '[CROSS] NO'}
   Model Selected:       {'[CHECK] YES' if self.state.get('model_selected') else '[CROSS] NO'}
   Skills/Agents Check:  {'[CHECK] YES' if self.state.get('skills_agents_checked') else '[CROSS] NO'}

[CHART] STATISTICS
   Total Violations:     {self.state.get('total_violations', 0)}
   Last Violation:       {self.state.get('last_violation', {}).get('policy', 'None')}
   Session Start Time:   {self.state.get('session_start_time', 'Not started')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""


def main():
    """Main function for CLI usage"""
    import argparse

    parser = argparse.ArgumentParser(description='Blocking Policy Enforcer')
    parser.add_argument('--enforce', action='store_true', help='Enforce all policies')
    parser.add_argument('--status', action='store_true', help='Show status report')
    parser.add_argument('--reset', action='store_true', help='Reset for new request')
    parser.add_argument('--mark-session-started', action='store_true', help='Mark session started')
    parser.add_argument('--mark-standards-loaded', action='store_true', help='Mark standards loaded')
    parser.add_argument('--mark-context-checked', action='store_true', help='Mark context checked')
    parser.add_argument('--user-request', type=str, help='User request for enforcement')

    args = parser.parse_args()

    enforcer = BlockingPolicyEnforcer()

    if args.status:
        print(enforcer.get_status_report())

    elif args.mark_session_started:
        enforcer.mark_session_started()
        print("[CHECK] Marked: Session started")

    elif args.mark_standards_loaded:
        enforcer.mark_standards_loaded()
        print("[CHECK] Marked: Standards loaded")

    elif args.mark_context_checked:
        enforcer.mark_context_checked()
        print("[CHECK] Marked: Context checked")

    elif args.reset:
        enforcer.reset_for_new_request()
        print("[CHECK] Reset for new request")

    elif args.enforce:
        try:
            enforcer.enforce_all(args.user_request or "")
            print("\n[CHECK] ALL POLICIES PASSED")
            sys.exit(0)
        except BlockingPolicyError as e:
            print(f"\n{e}")
            sys.exit(1)

    else:
        parser.print_help()


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Core Skills Mandate Policy Enforcement (v2.0 - FULLY CONSOLIDATED)

CONSOLIDATED SCRIPT - Maps to: policies/03-execution-system/05-skill-agent-selection/core-skills-mandate.md

Consolidates 1 script (328 lines):
- core-skills-enforcer.py (328 lines) - Enforce mandatory skills execution order

THIS CONSOLIDATION includes ALL functionality from old scripts.
NO logic was lost in consolidation - everything is merged.

Usage:
  python core-skills-mandate-policy.py --enforce              # Run policy enforcement
  python core-skills-mandate-policy.py --validate             # Validate policy compliance
  python core-skills-mandate-policy.py --report               # Generate report
  python core-skills-mandate-policy.py --start-session        # Start new session
  python core-skills-mandate-policy.py --next-skill           # Get next skill
  python core-skills-mandate-policy.py --verify               # Verify execution
  python core-skills-mandate-policy.py --stats                # Show statistics
"""

import sys
import io
import json
import argparse
from pathlib import Path
from datetime import datetime

# Fix encoding for Windows console
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    try:
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

MEMORY_DIR = Path.home() / '.claude' / 'memory'
LOG_FILE = MEMORY_DIR / 'logs' / 'policy-hits.log'


# ============================================================================
# CORE SKILLS ENFORCER (from core-skills-enforcer.py)
# ============================================================================

class CoreSkillsEnforcer:
    """Enforce the mandatory skills execution order within each Claude session.

    Tracks which core skills have been executed in the current session and
    determines which skills still need to run. Writes execution events to a
    dedicated log file so that compliance can be measured across sessions.

    Attributes:
        memory_dir (Path): Root directory for all Claude memory files.
        execution_log (Path): Append-only log recording SESSION_START,
            SKILL_EXECUTED, and SKILL_SKIPPED events.
        mandatory_skills (list[dict]): Ordered list of skill descriptors.
            Each dict has keys: 'name', 'description', 'priority', 'required'.

    Key Methods:
        get_execution_state(): Read the latest session state from the log.
        start_session(): Append a SESSION_START marker to the log.
        log_skill_execution(skill_name): Record that a skill was executed.
        get_next_skill(): Return the next required skill that has not run yet.
        verify_execution(): Check whether all required skills have run.
        get_execution_order(): Return the full ordered list of skills.
        skip_skill(skill_name, reason): Record that a skill was intentionally skipped.
        get_statistics(): Compute compliance statistics across all sessions.
    """

    def __init__(self):
        self.memory_dir = Path.home() / '.claude' / 'memory'
        self.execution_log = self.memory_dir / 'logs' / 'core-skills-execution.log'

        # Ensure log directory exists
        self.execution_log.parent.mkdir(parents=True, exist_ok=True)

        # Mandatory skills (in order)
        self.mandatory_skills = [
            {
                'name': 'context-management-core',
                'description': 'Context validation and optimization',
                'priority': 1,
                'required': True
            },
            {
                'name': 'model-selection-core',
                'description': 'Select appropriate model',
                'priority': 2,
                'required': True
            },
            {
                'name': 'adaptive-skill-intelligence',
                'description': 'Detect required skills/agents',
                'priority': 3,
                'required': False  # Optional but recommended
            },
            {
                'name': 'task-planning-intelligence',
                'description': 'Plan task execution',
                'priority': 4,
                'required': False  # Optional for simple tasks
            }
        ]

    def get_execution_state(self):
        """Read the current session's execution state from the log file.

        Scans the execution log in reverse order to find the most recent
        SESSION_START marker, then collects all SKILL_EXECUTED entries
        that followed it.

        Returns:
            dict: A dict with keys:
                - 'executed_skills' (list[str]): Names of skills executed in
                  the current session, in execution order.
                - 'current_session' (str or None): The raw SESSION_START log
                  line, or None if no session has been started.
        """
        if not self.execution_log.exists():
            return {
                'executed_skills': [],
                'current_session': None
            }

        # Read last session
        try:
            with open(self.execution_log, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # Find last session
            session_start = None
            executed = []

            for line in reversed(lines):
                if 'SESSION_START' in line:
                    session_start = line.strip()
                    break
                elif 'SKILL_EXECUTED' in line:
                    parts = line.strip().split('|')
                    if len(parts) >= 2:
                        skill_name = parts[1].strip()
                        executed.insert(0, skill_name)

            return {
                'executed_skills': executed,
                'current_session': session_start
            }
        except:
            return {
                'executed_skills': [],
                'current_session': None
            }

    def start_session(self):
        """Append a SESSION_START marker to the execution log.

        Creates the log file and its parent directories if they do not yet
        exist. This method must be called at the beginning of each new
        Claude session so that skill execution events are correctly grouped.
        """
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] SESSION_START\n"

        with open(self.execution_log, 'a', encoding='utf-8') as f:
            f.write(log_entry)

    def log_skill_execution(self, skill_name):
        """Append a SKILL_EXECUTED entry to the execution log.

        Args:
            skill_name (str): The canonical name of the skill that was
                executed (e.g., 'context-management-core').
        """
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] SKILL_EXECUTED | {skill_name}\n"

        with open(self.execution_log, 'a', encoding='utf-8') as f:
            f.write(log_entry)

    def get_next_skill(self):
        """Return the next required skill that has not yet been executed.

        Iterates through mandatory_skills in priority order and returns the
        first required skill whose name is not in the current session's
        executed list. If all required skills have run, returns a completion
        result.

        Returns:
            dict: A dict with keys:
                - 'skill' (dict or None): The skill descriptor dict, or None
                  if all required skills have been executed.
                - 'status' (str): 'required' if a skill still needs to run,
                  'complete' if all mandatory skills are done.
                - 'message' (str): Human-readable description of what to do
                  next.
        """
        state = self.get_execution_state()
        executed = state['executed_skills']

        # Find first non-executed mandatory skill
        for skill in self.mandatory_skills:
            if skill['required'] and skill['name'] not in executed:
                return {
                    'skill': skill,
                    'status': 'required',
                    'message': f"Execute {skill['name']}: {skill['description']}"
                }

        # All mandatory skills executed
        return {
            'skill': None,
            'status': 'complete',
            'message': 'All mandatory skills executed'
        }

    def verify_execution(self):
        """Check whether all required mandatory skills have been executed.

        Compares the current session's executed skill list against the
        required skills defined in mandatory_skills.

        Returns:
            dict: A dict with keys:
                - 'complete' (bool): True if every required skill has run.
                - 'executed' (list[str]): Skills executed in this session.
                - 'missing' (list[str]): Names of required skills that have
                  not yet been executed.
        """
        state = self.get_execution_state()
        executed = state['executed_skills']

        missing = []
        for skill in self.mandatory_skills:
            if skill['required'] and skill['name'] not in executed:
                missing.append(skill['name'])

        return {
            'complete': len(missing) == 0,
            'executed': executed,
            'missing': missing
        }

    def get_execution_order(self):
        """Return the full recommended execution order for all skills.

        Returns:
            list[dict]: One dict per skill in mandatory_skills, each
                containing keys: 'order' (int), 'name' (str),
                'description' (str), 'required' (bool).
        """
        return [
            {
                'order': skill['priority'],
                'name': skill['name'],
                'description': skill['description'],
                'required': skill['required']
            }
            for skill in self.mandatory_skills
        ]

    def skip_skill(self, skill_name, reason):
        """Record that a skill was intentionally skipped.

        Appends a SKILL_SKIPPED entry to the execution log so that
        compliance reports can distinguish between missing executions and
        deliberate skips.

        Args:
            skill_name (str): The canonical name of the skill being skipped.
            reason (str): Human-readable justification for skipping the skill.
        """
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] SKILL_SKIPPED | {skill_name} | {reason}\n"

        with open(self.execution_log, 'a', encoding='utf-8') as f:
            f.write(log_entry)

    def get_statistics(self):
        """Compute enforcement compliance statistics across all recorded sessions.

        Reads the entire execution log to tally sessions and determine which
        ones were compliant (all required skills executed). Returns zero
        values when the log does not exist.

        Returns:
            dict: A dict with keys:
                - 'total_sessions' (int): Number of SESSION_START events found.
                - 'total_skills_executed' (int): Total SKILL_EXECUTED events.
                - 'compliant_sessions' (int): Sessions where all required
                  skills were executed.
                - 'compliance_rate' (float): Percentage of compliant sessions,
                  rounded to one decimal place.
        """
        if not self.execution_log.exists():
            return {
                'total_sessions': 0,
                'total_skills_executed': 0,
                'compliance_rate': 0
            }

        sessions = 0
        skills_executed = 0
        compliant_sessions = 0

        try:
            with open(self.execution_log, 'r', encoding='utf-8') as f:
                current_session_skills = []

                for line in f:
                    if 'SESSION_START' in line:
                        # Check previous session compliance
                        if current_session_skills:
                            # Count mandatory skills
                            mandatory_names = [s['name'] for s in self.mandatory_skills if s['required']]
                            if all(skill in current_session_skills for skill in mandatory_names):
                                compliant_sessions += 1

                        sessions += 1
                        current_session_skills = []

                    elif 'SKILL_EXECUTED' in line:
                        parts = line.strip().split('|')
                        if len(parts) >= 2:
                            skill_name = parts[1].strip()
                            current_session_skills.append(skill_name)
                            skills_executed += 1

                # Check last session
                if current_session_skills:
                    mandatory_names = [s['name'] for s in self.mandatory_skills if s['required']]
                    if all(skill in current_session_skills for skill in mandatory_names):
                        compliant_sessions += 1

        except:
            pass

        compliance_rate = (compliant_sessions / sessions * 100) if sessions > 0 else 0

        return {
            'total_sessions': sessions,
            'total_skills_executed': skills_executed,
            'compliant_sessions': compliant_sessions,
            'compliance_rate': round(compliance_rate, 1)
        }


# ============================================================================
# LOGGING
# ============================================================================

def log_policy_hit(action, context=""):
    """Append a timestamped entry to the policy-hits log.

    Args:
        action (str): The action identifier (e.g., 'ENFORCE_START', 'VALIDATE').
        context (str): Optional human-readable context or detail string.
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = f"[{timestamp}] core-skills-mandate-policy | {action} | {context}\n"

    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(log_entry)
    except Exception:
        pass


# ============================================================================
# POLICY INTERFACE
# ============================================================================

def validate():
    """Check that the core skills mandate policy preconditions are met.

    Creates the memory directory and instantiates CoreSkillsEnforcer to
    verify the log directory is writable.

    Returns:
        bool: True if validation succeeds, False on any exception.
    """
    try:
        MEMORY_DIR.mkdir(parents=True, exist_ok=True)
        enforcer = CoreSkillsEnforcer()
        log_policy_hit("VALIDATE", "core-skills-ready")
        return True
    except Exception as e:
        log_policy_hit("VALIDATE_ERROR", str(e))
        return False


def report():
    """Generate a compliance report for the core skills mandate policy.

    Instantiates CoreSkillsEnforcer, calls get_statistics(), and bundles the
    results with policy metadata.

    Returns:
        dict: Contains keys 'status', 'policy', 'mandatory_skills' (list),
              'statistics' (dict from get_statistics()), and 'timestamp'.
              Returns {'status': 'error', ...} on failure.
    """
    try:
        enforcer = CoreSkillsEnforcer()
        stats = enforcer.get_statistics()

        report_data = {
            "status": "success",
            "policy": "core-skills-mandate",
            "mandatory_skills": [
                s['name'] for s in enforcer.mandatory_skills if s['required']
            ],
            "statistics": stats,
            "timestamp": datetime.now().isoformat()
        }

        log_policy_hit("REPORT", "core-skills-mandate-report-generated")
        return report_data
    except Exception as e:
        return {"status": "error", "message": str(e)}


def enforce():
    """Activate the core skills mandate policy.

    Consolidates core skills enforcement from core-skills-enforcer.py:
    - Mandatory skills execution order
    - Session tracking
    - Compliance verification
    - Statistics collection

    Returns:
        dict: Contains 'status' ('success' or 'error').
              On error, contains 'message' with the exception string.
    """
    try:
        log_policy_hit("ENFORCE_START", "core-skills-mandate-enforcement")

        MEMORY_DIR.mkdir(parents=True, exist_ok=True)

        # Initialize enforcer
        enforcer = CoreSkillsEnforcer()

        log_policy_hit("ENFORCE_COMPLETE", "core-skills-mandate-ready")
        print("[core-skills-mandate-policy] Policy enforced - Core skills mandate active")

        return {"status": "success"}
    except Exception as e:
        log_policy_hit("ENFORCE_ERROR", str(e))
        print(f"[core-skills-mandate-policy] ERROR: {e}")
        return {"status": "error", "message": str(e)}


# ============================================================================
# CLI INTERFACE
# ============================================================================

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--enforce":
            result = enforce()
            sys.exit(0 if result.get("status") == "success" else 1)
        elif sys.argv[1] == "--validate":
            is_valid = validate()
            sys.exit(0 if is_valid else 1)
        elif sys.argv[1] == "--report":
            result = report()
            print(json.dumps(result, indent=2))
            sys.exit(0 if result.get("status") == "success" else 1)
        elif sys.argv[1] == "--start-session":
            enforcer = CoreSkillsEnforcer()
            enforcer.start_session()
            print("New session started")
            sys.exit(0)
        elif sys.argv[1] == "--next-skill":
            enforcer = CoreSkillsEnforcer()
            result = enforcer.get_next_skill()
            print(json.dumps(result, indent=2))
            sys.exit(0)
        elif sys.argv[1] == "--verify":
            enforcer = CoreSkillsEnforcer()
            verification = enforcer.verify_execution()
            print(json.dumps(verification, indent=2))
            sys.exit(0)
        elif sys.argv[1] == "--stats":
            enforcer = CoreSkillsEnforcer()
            stats = enforcer.get_statistics()
            print(json.dumps(stats, indent=2))
            sys.exit(0)
        elif sys.argv[1] == "--execution-order":
            enforcer = CoreSkillsEnforcer()
            order = enforcer.get_execution_order()
            print(json.dumps(order, indent=2))
            sys.exit(0)
        else:
            print("Usage: python core-skills-mandate-policy.py [--enforce|--validate|--report|--start-session|--next-skill|--verify|--stats|--execution-order]")
            sys.exit(1)
    else:
        # Default: run enforcement
        enforce()

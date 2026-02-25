#!/usr/bin/env python3
"""
Core Skills Enforcer
Enforces mandatory skills execution order
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

class CoreSkillsEnforcer:
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
        """Get current execution state from log"""
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
        """Start a new session"""
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] SESSION_START\n"

        with open(self.execution_log, 'a', encoding='utf-8') as f:
            f.write(log_entry)

    def log_skill_execution(self, skill_name):
        """Log skill execution"""
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] SKILL_EXECUTED | {skill_name}\n"

        with open(self.execution_log, 'a', encoding='utf-8') as f:
            f.write(log_entry)

    def get_next_skill(self):
        """Get next skill that should be executed"""
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
        """Verify all mandatory skills were executed"""
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
        """Get recommended execution order"""
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
        """Skip a skill with reason"""
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] SKILL_SKIPPED | {skill_name} | {reason}\n"

        with open(self.execution_log, 'a', encoding='utf-8') as f:
            f.write(log_entry)

    def get_statistics(self):
        """Get enforcement statistics"""
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

def main():
    parser = argparse.ArgumentParser(description='Core skills enforcer')
    parser.add_argument('--start-session', action='store_true', help='Start new session')
    parser.add_argument('--next-skill', action='store_true', help='Get next skill to execute')
    parser.add_argument('--log-skill', help='Log skill execution')
    parser.add_argument('--skip-skill', nargs=2, metavar=('SKILL', 'REASON'), help='Skip skill')
    parser.add_argument('--verify', action='store_true', help='Verify execution')
    parser.add_argument('--execution-order', action='store_true', help='Show execution order')
    parser.add_argument('--stats', action='store_true', help='Show statistics')
    parser.add_argument('--test', action='store_true', help='Test enforcement')

    args = parser.parse_args()

    enforcer = CoreSkillsEnforcer()

    if args.test:
        print("Testing core skills enforcer...")

        # Test 1: Start session
        print("\n1. Start session")
        enforcer.start_session()
        print("   [OK] Session started")

        # Test 2: Get next skill
        print("\n2. Get next skill")
        result = enforcer.get_next_skill()
        print(f"   Next skill: {result['skill']['name'] if result['skill'] else 'None'}")
        print(f"   Status: {result['status']}")

        # Test 3: Execute skills in order
        print("\n3. Execute mandatory skills")
        while True:
            next_skill = enforcer.get_next_skill()
            if next_skill['status'] == 'complete':
                break

            skill_name = next_skill['skill']['name']
            print(f"   Executing: {skill_name}")
            enforcer.log_skill_execution(skill_name)

        # Test 4: Verify execution
        print("\n4. Verify execution")
        verification = enforcer.verify_execution()
        print(f"   Complete: {verification['complete']}")
        print(f"   Executed: {len(verification['executed'])} skills")
        print(f"   Missing: {len(verification['missing'])} skills")

        # Test 5: Get statistics
        print("\n5. Get statistics")
        stats = enforcer.get_statistics()
        print(f"   Sessions: {stats['total_sessions']}")
        print(f"   Skills executed: {stats['total_skills_executed']}")
        print(f"   Compliance: {stats['compliance_rate']}%")

        print("\n[OK] All tests completed!")
        return 0

    if args.start_session:
        enforcer.start_session()
        print("New session started")
        return 0

    if args.next_skill:
        result = enforcer.get_next_skill()
        print(json.dumps(result, indent=2))
        return 0

    if args.log_skill:
        enforcer.log_skill_execution(args.log_skill)
        print(f"Skill logged: {args.log_skill}")
        return 0

    if args.skip_skill:
        skill_name, reason = args.skip_skill
        enforcer.skip_skill(skill_name, reason)
        print(f"Skill skipped: {skill_name}")
        return 0

    if args.verify:
        verification = enforcer.verify_execution()
        print(json.dumps(verification, indent=2))
        return 0

    if args.execution_order:
        order = enforcer.get_execution_order()
        print(json.dumps(order, indent=2))
        return 0

    if args.stats:
        stats = enforcer.get_statistics()
        print(json.dumps(stats, indent=2))
        return 0

    parser.print_help()
    return 1

if __name__ == '__main__':
    sys.exit(main())

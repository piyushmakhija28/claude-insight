#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Plan Mode Auto-Decider (Phase 4)
Automatically decides when to enter plan mode - no user confirmation needed

PHASE 4 AUTOMATION - SMART PLAN MODE DECISION
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

# Fix encoding for Windows console
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')


class PlanModeAutoDecider:
    """
    Automatically decides when plan mode is needed
    Thresholds:
    - Score 0-9: NO plan mode (proceed directly)
    - Score 10-19: AUTO ENTER plan mode
    - Score 20+: MANDATORY plan mode
    """

    def __init__(self):
        self.memory_path = Path.home() / '.claude' / 'memory'
        self.logs_path = self.memory_path / 'logs'
        self.plan_log = self.logs_path / 'plan-mode-decisions.log'

    def calculate_risk_score(self, task_info):
        """
        Calculate risk score (0-30)
        Higher = more risky = needs plan mode
        """
        score = 0

        # Multi-service impact
        service_count = task_info.get('service_count', 0)
        if service_count > 3:
            score += 10
        elif service_count > 1:
            score += 5

        # Database changes
        if task_info.get('database_changes', False):
            score += 7

        # Security critical
        if task_info.get('security_critical', False):
            score += 8

        # No similar examples
        if task_info.get('no_examples', False):
            score += 6

        # Architecture changes
        if task_info.get('architecture_change', False):
            score += 10

        # Novel problem
        if task_info.get('novel_problem', False):
            score += 8

        # New framework/technology
        if task_info.get('new_technology', False):
            score += 5

        # Integration complexity
        if task_info.get('complex_integration', False):
            score += 6

        # File count
        file_count = task_info.get('file_count', 0)
        if file_count > 15:
            score += 7
        elif file_count > 10:
            score += 4
        elif file_count > 5:
            score += 2

        return min(score, 30)

    def decide(self, complexity_score, risk_score):
        """
        Make plan mode decision

        Rules:
        - Total < 10: NO plan mode
        - Total 10-19: YES plan mode (auto-enter)
        - Total 20+: MANDATORY plan mode
        """
        total_score = complexity_score + risk_score

        if total_score < 10:
            return {
                'decision': 'NO',
                'reason': 'Simple task - proceed directly without plan mode',
                'total_score': total_score,
                'auto_enter': False,
                'mandatory': False
            }
        elif total_score < 20:
            return {
                'decision': 'YES',
                'reason': 'Moderate complexity/risk - plan mode recommended',
                'total_score': total_score,
                'auto_enter': True,
                'mandatory': False
            }
        else:
            return {
                'decision': 'MANDATORY',
                'reason': 'High complexity/risk - plan mode required',
                'total_score': total_score,
                'auto_enter': True,
                'mandatory': True
            }

    def get_plan_mode_benefits(self, decision):
        """Get benefits of using plan mode for this task"""
        benefits = []

        if decision['total_score'] >= 20:
            benefits = [
                'Prevent costly mistakes in complex implementation',
                'Validate architecture decisions upfront',
                'Identify dependencies and conflicts early',
                'Get user approval before major changes',
                'Reduce rework and debugging time'
            ]
        elif decision['total_score'] >= 10:
            benefits = [
                'Better understand scope and approach',
                'Identify potential issues early',
                'Get user alignment on strategy',
                'More organized implementation'
            ]
        else:
            benefits = [
                'Not needed - task is straightforward'
            ]

        return benefits

    def auto_decide(self, task_info):
        """
        Main entry point - automatic decision
        Returns decision with full context
        """
        # Get complexity from task info
        complexity_score = task_info.get('complexity_score', 0)

        # Calculate risk
        risk_score = self.calculate_risk_score(task_info)

        # Make decision
        decision = self.decide(complexity_score, risk_score)

        # Get benefits
        benefits = self.get_plan_mode_benefits(decision)

        result = {
            'complexity_score': complexity_score,
            'risk_score': risk_score,
            'decision': decision['decision'],
            'reason': decision['reason'],
            'total_score': decision['total_score'],
            'auto_enter': decision['auto_enter'],
            'mandatory': decision['mandatory'],
            'benefits': benefits,
            'timestamp': datetime.now().isoformat()
        }

        # Log decision
        self.log_decision(result)

        # Mark as decided in blocking enforcer
        if decision['decision'] != 'NO':
            try:
                import subprocess
                subprocess.run(
                    ['python', str(self.memory_path / 'blocking-policy-enforcer.py'),
                     '--mark-plan-mode-decided'],
                    capture_output=True,
                    timeout=5
                )
            except:
                pass

        return result

    def log_decision(self, result):
        """Log decision"""
        self.logs_path.mkdir(parents=True, exist_ok=True)

        log_entry = {
            'timestamp': result['timestamp'],
            'decision': result['decision'],
            'total_score': result['total_score'],
            'auto_enter': result['auto_enter']
        }

        with open(self.plan_log, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')

    def print_result(self, result):
        """Print formatted result"""
        print(f"\n{'='*70}")
        print(f"🎯 Plan Mode Auto-Decider (Phase 4)")
        print(f"{'='*70}\n")

        print(f"📊 Scores:")
        print(f"   Complexity: {result['complexity_score']}/30")
        print(f"   Risk: {result['risk_score']}/30")
        print(f"   Total: {result['total_score']}/60")

        print(f"\n✅ Decision: {result['decision']}")
        print(f"   Reason: {result['reason']}")

        if result['auto_enter']:
            print(f"\n🚀 Action: AUTO-ENTERING PLAN MODE")
            if result['mandatory']:
                print(f"   Status: MANDATORY (no skip option)")
            else:
                print(f"   Status: RECOMMENDED (can skip if needed)")

        print(f"\n💡 Benefits:")
        for benefit in result['benefits']:
            print(f"   • {benefit}")

        print(f"\n{'='*70}\n")


def main():
    """CLI usage"""
    import argparse

    parser = argparse.ArgumentParser(description='Plan Mode Auto-Decider (Phase 4)')
    parser.add_argument('--task-info', required=True, help='Task information (JSON)')

    args = parser.parse_args()

    try:
        task_info = json.loads(args.task_info)
    except json.JSONDecodeError:
        print(f"❌ Invalid JSON task info: {args.task_info}")
        sys.exit(1)

    decider = PlanModeAutoDecider()
    result = decider.auto_decide(task_info)

    decider.print_result(result)

    # Exit with code based on decision
    # 0 = NO plan mode
    # 1 = YES plan mode (recommended)
    # 2 = MANDATORY plan mode
    if result['decision'] == 'NO':
        sys.exit(0)
    elif result['decision'] == 'YES':
        sys.exit(1)
    else:
        sys.exit(2)


if __name__ == '__main__':
    main()

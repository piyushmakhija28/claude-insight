#!/usr/bin/env python3
"""
Script Name: per-request-enforcer.py
Version: 1.0.0
Last Modified: 2026-02-17
Description: Per-request policy enforcement for continuous policy compliance
Author: Claude Memory System
Changelog: See CHANGELOG.md

CRITICAL: This enforcer runs BEFORE EVERY user request/response.
Policies are enforced continuously throughout the session.
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path

# Fix encoding
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')


class PerRequestEnforcer:
    """
    Enforces policies BEFORE EVERY user request/response.

    Per-Session (once):
    - Session started
    - Standards loaded

    Per-Request (every time):
    - Context check
    - Prompt generation
    - Task breakdown
    - Model selection
    - Tool optimization
    """

    def __init__(self):
        self.memory_path = Path.home() / '.claude' / 'memory'
        self.state_file = self.memory_path / '.per-request-state.json'
        self.state = self._load_state()

    def _load_state(self):
        """Load current state"""
        if self.state_file.exists():
            with open(self.state_file, 'r') as f:
                return json.load(f)
        return {
            'request_count': 0,
            'last_request_time': None,
            'current_request_policies': {}
        }

    def _save_state(self):
        """Save state"""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)

    def start_new_request(self):
        """
        Called BEFORE processing each user request.
        Resets per-request flags.
        """
        self.state['request_count'] += 1
        self.state['last_request_time'] = datetime.now().isoformat()
        self.state['current_request_policies'] = {
            'context_checked': False,
            'prompt_verified': False,
            'task_analyzed': False,
            'model_determined': False,
            'tools_optimized': False
        }
        self._save_state()

        print("\n" + "="*70)
        print(f"[REFRESH] REQUEST #{self.state['request_count']} - POLICY ENFORCEMENT ACTIVE")
        print("="*70)

    def mark_policy_complete(self, policy_name):
        """Mark a policy as completed for this request"""
        if policy_name in self.state['current_request_policies']:
            self.state['current_request_policies'][policy_name] = True
            self._save_state()
            print(f"   [OK] {policy_name}: ENFORCED")

    def check_required_policies(self):
        """
        Check if all required policies have been enforced.
        Called BEFORE generating response.
        """
        print("\n[CLIPBOARD] POLICY ENFORCEMENT STATUS:")
        print("-" * 70)

        policies = self.state['current_request_policies']
        all_complete = True

        for policy, status in policies.items():
            status_icon = "[OK]" if status else "[ERROR]"
            print(f"   {status_icon} {policy}: {'DONE' if status else 'PENDING'}")
            if not status:
                all_complete = False

        print("-" * 70)

        if not all_complete:
            print("\n[WARN]  WARNING: Not all policies enforced yet!")
            print("   Policies should run automatically before response.")
        else:
            print("\n[OK] ALL POLICIES ENFORCED - Ready to respond")

        print("="*70 + "\n")

        return all_complete


def main():
    """CLI interface"""
    import argparse

    parser = argparse.ArgumentParser(description="Per-request policy enforcer")
    parser.add_argument('--new-request', action='store_true',
                       help='Start new request (reset per-request flags)')
    parser.add_argument('--mark-complete', type=str,
                       help='Mark policy as complete')
    parser.add_argument('--check-status', action='store_true',
                       help='Check current policy enforcement status')

    args = parser.parse_args()

    enforcer = PerRequestEnforcer()

    if args.new_request:
        enforcer.start_new_request()
    elif args.mark_complete:
        enforcer.mark_policy_complete(args.mark_complete)
    elif args.check_status:
        enforcer.check_required_policies()
    else:
        # Default: start new request
        enforcer.start_new_request()


if __name__ == '__main__':
    main()

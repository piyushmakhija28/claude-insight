#!/usr/bin/env python
"""
AUTO-FIX ENFORCER v1.0.0
========================

🚨 CRITICAL: If ANY policy or system fails → STOP ALL WORK → FIX IMMEDIATELY

This enforcer:
1. Detects ALL system failures (policies, daemons, files, dependencies)
2. BLOCKS all work until failures are fixed
3. Auto-fixes common issues
4. Provides clear fix instructions for manual issues

MANDATORY: Run BEFORE every action!
"""

import os
import sys
import json
import subprocess
from datetime import datetime
from pathlib import Path

class AutoFixEnforcer:
    """Detects and auto-fixes all system failures"""

    def __init__(self):
        self.memory_path = Path.home() / '.claude' / 'memory'
        self.failures = []
        self.auto_fixed = []
        self.manual_fixes_needed = []

    def check_all_systems(self):
        """Check ALL systems and collect failures"""
        print("\n" + "="*80)
        print("🚨 AUTO-FIX ENFORCER - CHECKING ALL SYSTEMS")
        print("="*80 + "\n")

        # Check critical components
        self._check_python()
        self._check_critical_files()
        self._check_blocking_enforcer()
        self._check_session_state()
        self._check_daemons()
        self._check_git_repos()

        return len(self.failures) == 0

    def _check_python(self):
        """Check if Python is available"""
        print("🔍 [1/6] Checking Python...")
        try:
            result = subprocess.run(['python', '--version'],
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                version = result.stdout.strip()
                print(f"   ✅ Python available: {version}")
                return True
        except:
            pass

        self.failures.append({
            'type': 'CRITICAL',
            'component': 'Python',
            'issue': 'Python command not found or not working',
            'auto_fixable': False,
            'fix_instructions': [
                'Install Python from python.org',
                'Add Python to PATH',
                'Verify: python --version'
            ]
        })
        print("   ❌ Python NOT FOUND - CRITICAL!")
        return False

    def _check_critical_files(self):
        """Check if critical system files exist"""
        print("\n🔍 [2/6] Checking critical files...")

        critical_files = {
            'blocking-policy-enforcer.py': 'Blocking enforcer',
            'session-start.sh': 'Session start script',
            'scripts/plan-detector.py': 'Plan detector',
            'scripts/plan-detector.sh': 'Plan detector shell wrapper'
        }

        missing_files = []
        for file_path, description in critical_files.items():
            full_path = self.memory_path / file_path
            if not full_path.exists():
                missing_files.append((file_path, description))
                print(f"   ❌ Missing: {file_path} ({description})")

        if missing_files:
            self.failures.append({
                'type': 'CRITICAL',
                'component': 'Critical Files',
                'issue': f'{len(missing_files)} critical files missing',
                'details': missing_files,
                'auto_fixable': False,
                'fix_instructions': [
                    'Restore missing files from backup or repository',
                    'Run: cp -r claude-insight/scripts/* ~/.claude/memory/scripts/',
                    'Verify file permissions'
                ]
            })
        else:
            print("   ✅ All critical files present")

    def _check_blocking_enforcer(self):
        """Check if blocking enforcer is initialized"""
        print("\n🔍 [3/6] Checking blocking enforcer...")

        state_file = self.memory_path / '.blocking-state.json'
        if not state_file.exists():
            print("   ⚠️  Blocking enforcer state not found")
            # Try to initialize
            if self._auto_fix_blocking_enforcer():
                print("   ✅ Auto-fixed: Blocking enforcer initialized")
                self.auto_fixed.append('Blocking enforcer state')
                return True
            else:
                self.failures.append({
                    'type': 'HIGH',
                    'component': 'Blocking Enforcer',
                    'issue': 'Enforcer not initialized',
                    'auto_fixable': True,
                    'fix_instructions': [
                        'Run: export PYTHONIOENCODING=utf-8',
                        'Run: bash ~/.claude/memory/session-start.sh'
                    ]
                })
                return False

        try:
            with open(state_file, 'r') as f:
                state = json.load(f)

            # Check if session started
            if not state.get('session_started', False):
                print("   ⚠️  Session not started")
                self.failures.append({
                    'type': 'CRITICAL',
                    'component': 'Session',
                    'issue': 'Session not started',
                    'auto_fixable': True,
                    'fix_instructions': [
                        'Run: export PYTHONIOENCODING=utf-8',
                        'Run: bash ~/.claude/memory/session-start.sh'
                    ]
                })
                return False

            print("   ✅ Blocking enforcer initialized")
            return True

        except Exception as e:
            print(f"   ❌ Error reading enforcer state: {e}")
            self.failures.append({
                'type': 'HIGH',
                'component': 'Blocking Enforcer',
                'issue': f'Cannot read state: {e}',
                'auto_fixable': False
            })
            return False

    def _check_session_state(self):
        """Check session state"""
        print("\n🔍 [4/6] Checking session state...")

        state_file = self.memory_path / '.blocking-state.json'
        if not state_file.exists():
            print("   ⚠️  No session state")
            return False

        try:
            with open(state_file, 'r') as f:
                state = json.load(f)

            # Check required states
            required_checks = {
                'session_started': 'Session started',
                'context_checked': 'Context checked'
            }

            missing = []
            for key, desc in required_checks.items():
                if not state.get(key, False):
                    missing.append(desc)

            if missing:
                print(f"   ⚠️  Missing: {', '.join(missing)}")
                # Not critical, just warning
            else:
                print("   ✅ Session state valid")

            return True

        except Exception as e:
            print(f"   ❌ Error checking session state: {e}")
            return False

    def _check_daemons(self):
        """Check daemon status"""
        print("\n🔍 [5/6] Checking daemons...")

        # Note: Daemons being stopped is WARNING, not CRITICAL
        # System can work without daemons, just with reduced automation

        pid_dir = self.memory_path / '.pids'
        if not pid_dir.exists():
            print("   ⚠️  No daemon PID directory (daemons not started)")
            print("   ℹ️  System will work, but automation is disabled")
            return True

        daemon_names = [
            'context-daemon',
            'session-auto-save-daemon',
            'preference-auto-tracker',
            'skill-auto-suggester',
            'commit-daemon',
            'session-pruning-daemon',
            'pattern-detection-daemon',
            'failure-prevention-daemon',
            'auto-recommendation-daemon'
        ]

        running = 0
        stopped = 0

        for daemon in daemon_names:
            pid_file = pid_dir / f'{daemon}.pid'
            if pid_file.exists():
                try:
                    pid = int(pid_file.read_text().strip())
                    # Check if process is running (Windows compatible)
                    try:
                        subprocess.run(['tasklist', '/FI', f'PID eq {pid}'],
                                     capture_output=True, timeout=2)
                        running += 1
                    except:
                        stopped += 1
                except:
                    stopped += 1
            else:
                stopped += 1

        print(f"   ℹ️  Daemons: {running} running, {stopped} stopped")
        print("   ℹ️  Daemon status is informational only (not blocking)")
        return True

    def _check_git_repos(self):
        """Check git repository status"""
        print("\n🔍 [6/6] Checking git repositories...")

        # Check if we're in a git repo
        try:
            result = subprocess.run(['git', 'rev-parse', '--git-dir'],
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                # Check for uncommitted changes
                result = subprocess.run(['git', 'status', '--porcelain'],
                                      capture_output=True, text=True, timeout=5)
                if result.stdout.strip():
                    print("   ⚠️  Uncommitted changes detected")
                    print("   ℹ️  Consider committing before major changes")
                else:
                    print("   ✅ Git repository clean")
                return True
        except:
            print("   ℹ️  Not in a git repository (or git not available)")

        return True

    def _auto_fix_blocking_enforcer(self):
        """Try to auto-fix blocking enforcer state"""
        try:
            state_file = self.memory_path / '.blocking-state.json'
            state_file.parent.mkdir(parents=True, exist_ok=True)

            initial_state = {
                'session_started': True,
                'context_checked': False,
                'standards_loaded': False,
                'prompt_generated': False,
                'tasks_created': False,
                'plan_mode_decided': False,
                'model_selected': False,
                'skills_agents_checked': False,
                'violations': [],
                'last_violation': None,
                'session_start_time': datetime.now().isoformat()
            }

            with open(state_file, 'w') as f:
                json.dump(initial_state, f, indent=2)

            return True
        except:
            return False

    def auto_fix_failures(self):
        """Attempt to auto-fix all fixable failures"""
        if not self.failures:
            return True

        print("\n" + "="*80)
        print("🔧 ATTEMPTING AUTO-FIXES")
        print("="*80 + "\n")

        fixed_count = 0
        for failure in self.failures:
            if failure.get('auto_fixable', False):
                print(f"🔧 Fixing: {failure['component']} - {failure['issue']}")

                # Attempt fix based on component
                if failure['component'] == 'Blocking Enforcer':
                    if self._auto_fix_blocking_enforcer():
                        print("   ✅ Fixed!")
                        fixed_count += 1
                        self.auto_fixed.append(failure['component'])
                        continue

                print("   ❌ Auto-fix failed, manual intervention needed")

        if fixed_count > 0:
            print(f"\n✅ Auto-fixed {fixed_count} issue(s)")

        return fixed_count

    def report_failures(self):
        """Report all failures and required fixes"""
        if not self.failures:
            print("\n" + "="*80)
            print("✅ ALL SYSTEMS OPERATIONAL - NO FAILURES DETECTED")
            print("="*80 + "\n")
            return True

        print("\n" + "="*80)
        print("🚨 SYSTEM FAILURES DETECTED - WORK BLOCKED")
        print("="*80 + "\n")

        critical = [f for f in self.failures if f['type'] == 'CRITICAL']
        high = [f for f in self.failures if f['type'] == 'HIGH']
        medium = [f for f in self.failures if f['type'] == 'MEDIUM']

        if critical:
            print(f"🔴 CRITICAL FAILURES: {len(critical)}")
            for i, failure in enumerate(critical, 1):
                print(f"\n   [{i}] {failure['component']}: {failure['issue']}")
                if 'fix_instructions' in failure:
                    print("   📋 Fix Instructions:")
                    for instruction in failure['fix_instructions']:
                        print(f"      • {instruction}")

        if high:
            print(f"\n🟠 HIGH PRIORITY FAILURES: {len(high)}")
            for i, failure in enumerate(high, 1):
                print(f"\n   [{i}] {failure['component']}: {failure['issue']}")
                if 'fix_instructions' in failure:
                    print("   📋 Fix Instructions:")
                    for instruction in failure['fix_instructions']:
                        print(f"      • {instruction}")

        if medium:
            print(f"\n🟡 MEDIUM PRIORITY FAILURES: {len(medium)}")
            for i, failure in enumerate(medium, 1):
                print(f"\n   [{i}] {failure['component']}: {failure['issue']}")

        print("\n" + "="*80)
        print("🚨 WORK IS BLOCKED - FIX ALL FAILURES BEFORE CONTINUING")
        print("="*80 + "\n")

        return False

    def run(self, auto_fix=True):
        """Main enforcement run"""
        # Check all systems
        all_ok = self.check_all_systems()

        if all_ok:
            self.report_failures()
            return 0

        # Try auto-fix if enabled
        if auto_fix:
            self.auto_fix_failures()

            # Re-check after fixes
            self.failures = []
            all_ok = self.check_all_systems()

        # Report status
        self.report_failures()

        # Return exit code
        if all_ok:
            return 0
        else:
            # Count critical failures
            critical_count = sum(1 for f in self.failures if f['type'] == 'CRITICAL')
            return critical_count if critical_count > 0 else 1


def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description='Auto-Fix Enforcer')
    parser.add_argument('--no-auto-fix', action='store_true',
                       help='Disable auto-fix, only report failures')
    parser.add_argument('--json', action='store_true',
                       help='Output failures as JSON')

    args = parser.parse_args()

    enforcer = AutoFixEnforcer()
    exit_code = enforcer.run(auto_fix=not args.no_auto_fix)

    if args.json:
        output = {
            'failures': enforcer.failures,
            'auto_fixed': enforcer.auto_fixed,
            'all_ok': len(enforcer.failures) == 0
        }
        print(json.dumps(output, indent=2))

    sys.exit(exit_code)


if __name__ == '__main__':
    main()

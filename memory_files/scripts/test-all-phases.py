#!/usr/bin/env python3
"""
Comprehensive Test Suite
Tests all 4 phases together
"""

import sys
import json
import subprocess
from pathlib import Path

class ComprehensiveTests:
    def __init__(self):
        self.memory_dir = Path.home() / '.claude' / 'memory'
        self.passed = 0
        self.failed = 0
        self.tests = []

    def run_command(self, cmd, description):
        """Run a command and return output"""
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=10
            )
            return {
                'success': result.returncode == 0,
                'output': result.stdout,
                'error': result.stderr
            }
        except Exception as e:
            return {
                'success': False,
                'output': '',
                'error': str(e)
            }

    def test(self, name, test_func):
        """Run a test"""
        print(f"\n{'='*60}")
        print(f"TEST: {name}")
        print('='*60)

        try:
            result = test_func()
            if result:
                print(f"[OK] {name} PASSED")
                self.passed += 1
                self.tests.append((name, True, None))
                return True
            else:
                print(f"[FAIL] {name} FAILED")
                self.failed += 1
                self.tests.append((name, False, "Test returned False"))
                return False
        except Exception as e:
            print(f"[ERROR] {name} ERRORED: {e}")
            self.failed += 1
            self.tests.append((name, False, str(e)))
            return False

    def test_phase1_context_optimization(self):
        """Test Phase 1: Context Optimization"""
        print("Testing context optimization...")

        # Test pre-execution optimizer
        result = self.run_command(
            f'python {self.memory_dir}/pre-execution-optimizer.py --test-large-file',
            'Pre-execution optimizer'
        )
        if not result['success'] or '[OK]' not in result['output']:
            print(f"  [FAIL] Pre-execution optimizer failed")
            return False
        print("  [OK] Pre-execution optimizer working")

        # Test context cache
        result = self.run_command(
            f'python {self.memory_dir}/context-cache.py --stats',
            'Context cache'
        )
        if not result['success']:
            print(f"  [FAIL] Context cache failed")
            return False
        print("  [OK] Context cache working")

        # Test session state
        result = self.run_command(
            f'python {self.memory_dir}/session-state.py --summary',
            'Session state'
        )
        if not result['success']:
            print(f"  [FAIL] Session state failed")
            return False
        print("  [OK] Session state working")

        # Test context monitor
        result = self.run_command(
            f'python {self.memory_dir}/context-monitor-v2.py --current-status',
            'Context monitor'
        )
        if not result['success']:
            print(f"  [FAIL] Context monitor failed")
            return False
        print("  [OK] Context monitor working")

        return True

    def test_phase2_daemon_infrastructure(self):
        """Test Phase 2: Daemon Infrastructure"""
        print("Testing daemon infrastructure...")

        # Test daemon manager
        result = self.run_command(
            f'python {self.memory_dir}/daemon-manager.py --status-all --format json',
            'Daemon manager'
        )
        if not result['success']:
            print(f"  [FAIL] Daemon manager failed")
            return False

        try:
            status = json.loads(result['output'])
            running_count = sum(1 for s in status.values() if s.get('running'))
            print(f"  [OK] Daemon manager: {running_count} daemons running")
        except:
            print(f"  [FAIL] Cannot parse daemon status")
            return False

        # Test PID tracker
        result = self.run_command(
            f'python {self.memory_dir}/pid-tracker.py --health',
            'PID tracker'
        )
        if not result['success']:
            print(f"  [FAIL] PID tracker failed")
            return False

        try:
            health = json.loads(result['output'])
            score = health.get('health_score', 0)
            print(f"  [OK] PID tracker: Health score {score}%")
        except:
            print(f"  [FAIL] Cannot parse health data")
            return False

        # Test daemon logger (check log files exist)
        log_dir = self.memory_dir / 'logs' / 'daemons'
        log_count = len(list(log_dir.glob('*.log')))
        if log_count > 0:
            print(f"  [OK] Daemon logger: {log_count} log files")
        else:
            print(f"  [FAIL] No daemon log files found")
            return False

        return True

    def test_phase3_failure_prevention(self):
        """Test Phase 3: Failure Prevention"""
        print("Testing failure prevention...")

        # Test failure detector
        result = self.run_command(
            f'python {self.memory_dir}/failure-detector-v2.py --stats',
            'Failure detector'
        )
        if not result['success']:
            print(f"  [FAIL] Failure detector failed")
            return False
        print("  [OK] Failure detector working")

        # Test pre-execution checker
        result = self.run_command(
            f'python {self.memory_dir}/pre-execution-checker.py --stats',
            'Pre-execution checker'
        )
        if not result['success']:
            print(f"  [FAIL] Pre-execution checker failed")
            return False

        try:
            stats = json.loads(result['output'])
            patterns = stats.get('total_patterns', 0)
            print(f"  [OK] Pre-execution checker: {patterns} patterns in KB")
        except:
            print(f"  [FAIL] Cannot parse KB stats")
            return False

        # Test failure KB exists
        kb_file = self.memory_dir / 'failure-kb.json'
        if kb_file.exists():
            print(f"  [OK] Failure KB exists")
        else:
            print(f"  [FAIL] Failure KB not found")
            return False

        # Test solution learner
        result = self.run_command(
            f'python {self.memory_dir}/failure-solution-learner.py --stats',
            'Solution learner'
        )
        if not result['success']:
            print(f"  [FAIL] Solution learner failed")
            return False
        print("  [OK] Solution learner working")

        return True

    def test_phase4_policy_automation(self):
        """Test Phase 4: Policy Automation"""
        print("Testing policy automation...")

        # Test model selection enforcer
        result = self.run_command(
            f'python {self.memory_dir}/model-selection-enforcer.py --analyze "Find all files"',
            'Model selection enforcer'
        )
        if not result['success']:
            print(f"  [FAIL] Model selection enforcer failed")
            return False

        try:
            analysis = json.loads(result['output'])
            model = analysis.get('recommended_model')
            if model == 'haiku':
                print(f"  [OK] Model selection: Correctly selected {model}")
            else:
                print(f"  [WARN] Model selection: Selected {model} (expected haiku)")
        except:
            print(f"  [FAIL] Cannot parse model analysis")
            return False

        # Test model selection monitor
        result = self.run_command(
            f'python {self.memory_dir}/model-selection-monitor.py --distribution',
            'Model selection monitor'
        )
        if not result['success']:
            print(f"  [FAIL] Model selection monitor failed")
            return False
        print("  [OK] Model selection monitor working")

        # Test consultation tracker
        result = self.run_command(
            f'python {self.memory_dir}/consultation-tracker.py --stats',
            'Consultation tracker'
        )
        if not result['success']:
            print(f"  [FAIL] Consultation tracker failed")
            return False

        try:
            stats = json.loads(result['output'])
            consultations = stats.get('total_consultations', 0)
            print(f"  [OK] Consultation tracker: {consultations} consultations logged")
        except:
            print(f"  [FAIL] Cannot parse consultation stats")
            return False

        # Test core skills enforcer
        result = self.run_command(
            f'python {self.memory_dir}/core-skills-enforcer.py --stats',
            'Core skills enforcer'
        )
        if not result['success']:
            print(f"  [FAIL] Core skills enforcer failed")
            return False

        try:
            stats = json.loads(result['output'])
            compliance = stats.get('compliance_rate', 0)
            print(f"  [OK] Core skills enforcer: {compliance}% compliance")
        except:
            print(f"  [FAIL] Cannot parse skills stats")
            return False

        return True

    def test_integration(self):
        """Test system integration"""
        print("Testing system integration...")

        # Test dashboard
        result = self.run_command(
            f'bash {self.memory_dir}/dashboard-v2.sh',
            'Dashboard v2'
        )
        if not result['success']:
            print(f"  [FAIL] Dashboard failed")
            return False

        if 'MEMORY SYSTEM DASHBOARD v2.0' in result['output']:
            print(f"  [OK] Dashboard v2 running")
        else:
            print(f"  [FAIL] Dashboard output unexpected")
            return False

        # Check all log files exist
        required_logs = [
            'logs/policy-hits.log',
            'logs/model-usage.log',
            'logs/consultations.log',
            'logs/core-skills-execution.log'
        ]

        missing = []
        for log in required_logs:
            if not (self.memory_dir / log).exists():
                missing.append(log)

        if missing:
            print(f"  [WARN] Missing log files: {', '.join(missing)}")
        else:
            print(f"  [OK] All required log files exist")

        # Check directories exist
        required_dirs = [
            '.pids',
            '.restarts',
            '.cache',
            '.state',
            'logs/daemons'
        ]

        missing_dirs = []
        for dir_name in required_dirs:
            if not (self.memory_dir / dir_name).exists():
                missing_dirs.append(dir_name)

        if missing_dirs:
            print(f"  [FAIL] Missing directories: {', '.join(missing_dirs)}")
            return False
        else:
            print(f"  [OK] All required directories exist")

        return True

    def run_all_tests(self):
        """Run all tests"""
        print("\n" + "="*60)
        print("COMPREHENSIVE TEST SUITE - ALL PHASES")
        print("="*60)

        tests = [
            ("Phase 1: Context Optimization", self.test_phase1_context_optimization),
            ("Phase 2: Daemon Infrastructure", self.test_phase2_daemon_infrastructure),
            ("Phase 3: Failure Prevention", self.test_phase3_failure_prevention),
            ("Phase 4: Policy Automation", self.test_phase4_policy_automation),
            ("System Integration", self.test_integration),
        ]

        for test_name, test_func in tests:
            self.test(test_name, test_func)

        # Summary
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)

        total = self.passed + self.failed
        for test_name, passed, error in self.tests:
            status = "[OK] PASSED" if passed else "[FAIL] FAILED"
            print(f"{status:15} {test_name}")
            if error:
                print(f"                Error: {error}")

        print(f"\nTotal: {self.passed}/{total} tests passed")

        if self.passed == total:
            print("\n[OK] ALL TESTS PASSED!")
            return 0
        else:
            print(f"\n[FAIL] {self.failed} tests failed")
            return 1

def main():
    tests = ComprehensiveTests()
    return tests.run_all_tests()

if __name__ == '__main__':
    sys.exit(main())

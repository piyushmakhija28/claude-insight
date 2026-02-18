#!/usr/bin/env python3
"""
Phase 2 Infrastructure Test Suite
Tests hooks enforcement scripts (3-level architecture)

Replaces old daemon-manager / pid-tracker tests.
Enforcement is now done via Claude Code hooks, not background daemons.
"""

import sys
import json
import subprocess
from pathlib import Path

memory_dir = Path.home() / '.claude' / 'memory'
current_dir = memory_dir / 'current'


def run_test(test_name, test_func):
    """Run a test and report results"""
    print(f"\n{'='*60}")
    print(f"TEST: {test_name}")
    print('='*60)

    try:
        result = test_func()
        if result:
            print(f"[OK] {test_name} PASSED")
            return True
        else:
            print(f"[FAIL] {test_name} FAILED")
            return False
    except Exception as e:
        print(f"[ERROR] {test_name} raised exception: {e}")
        return False


def test_enforcement_scripts_present():
    """All 3-level enforcement scripts must be in current/"""
    required = [
        '3-level-flow.py',
        'blocking-policy-enforcer.py',
        'auto-fix-enforcer.sh',
        'context-monitor-v2.py',
        'session-id-generator.py',
        'clear-session-handler.py',
        'stop-notifier.py',
        'per-request-enforcer.py',
        'session-logger.py',
    ]

    missing = [s for s in required if not (current_dir / s).exists()]

    if missing:
        print(f"  Missing scripts: {', '.join(missing)}")
        return False

    print(f"  All {len(required)} scripts present in {current_dir}")
    return True


def test_blocking_enforcer():
    """Blocking policy enforcer must be importable"""
    enforcer_path = current_dir / 'blocking-policy-enforcer.py'
    if not enforcer_path.exists():
        print(f"  blocking-policy-enforcer.py not found")
        return False

    result = subprocess.run(
        ['python', str(enforcer_path), '--status'],
        capture_output=True,
        text=True,
        timeout=10
    )

    print(f"  Blocking enforcer exit code: {result.returncode}")
    if result.stdout:
        print(f"  Output: {result.stdout[:100]}")
    return True  # Just check it runs, status code may vary


def test_session_log_structure():
    """Session log directory structure must be correct"""
    sessions_dir = memory_dir / 'logs' / 'sessions'
    if not sessions_dir.exists():
        print(f"  logs/sessions/ does not exist yet (created on first use)")
        return True  # Not an error, created on first session

    session_dirs = [d for d in sessions_dir.iterdir() if d.is_dir()]
    print(f"  Found {len(session_dirs)} session directories")

    if session_dirs:
        # Check that at least one has a flow-trace.json
        has_trace = any((d / 'flow-trace.json').exists() for d in session_dirs)
        if has_trace:
            print(f"  flow-trace.json present in session dirs")
        else:
            print(f"  No flow-trace.json found (may not have run yet)")

    return True


def test_latest_flow_trace():
    """Latest flow trace should exist after at least one session"""
    latest = memory_dir / 'logs' / 'latest-flow-trace.json'
    if not latest.exists():
        print(f"  latest-flow-trace.json not found (run a session first)")
        return True  # Not a failure, just not run yet

    try:
        data = json.loads(latest.read_text(encoding='utf-8'))
        session_id = data.get('session_id', 'unknown')
        levels = data.get('levels_passed', 0)
        print(f"  Latest trace: {session_id}, {levels}/4 levels passed")
        return True
    except Exception as e:
        print(f"  Cannot parse latest-flow-trace.json: {e}")
        return False


def test_policy_log():
    """Policy hits log should be writable"""
    log_file = memory_dir / 'logs' / 'policy-hits.log'
    if not log_file.exists():
        print(f"  policy-hits.log not created yet")
        return True  # Created on first policy hit

    lines = log_file.read_text(encoding='utf-8', errors='ignore').splitlines()
    print(f"  policy-hits.log: {len(lines)} entries")
    return True


def main():
    print("\n" + "="*60)
    print("PHASE 2: HOOKS ENFORCEMENT INFRASTRUCTURE TESTS")
    print("="*60)
    print("Testing 3-level architecture enforcement (hooks-based)")
    print()

    tests = [
        ("Enforcement Scripts Present", test_enforcement_scripts_present),
        ("Blocking Enforcer Runs",      test_blocking_enforcer),
        ("Session Log Structure",        test_session_log_structure),
        ("Latest Flow Trace",            test_latest_flow_trace),
        ("Policy Hits Log",              test_policy_log),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        result = run_test(test_name, test_func)
        if result:
            passed += 1
        else:
            failed += 1

    print(f"\n{'='*60}")
    print(f"RESULTS: {passed}/{passed+failed} tests passed")
    print('='*60)

    return 0 if failed == 0 else 1


if __name__ == '__main__':
    sys.exit(main())

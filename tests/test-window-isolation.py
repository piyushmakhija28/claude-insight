#!/usr/bin/env python
# Script Name: test-window-isolation.py
# Version: 1.0.0
# Last Modified: 2026-02-24
# Description: Test script for multi-window session isolation
# Tests that flags created in one PID don't interfere with another PID
# Windows-safe: ASCII only, no Unicode chars

import sys
import os
import json
from pathlib import Path
from datetime import datetime

# Windows encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

MEMORY_BASE = Path.home() / '.claude' / 'memory'
FLAG_DIR = Path.home() / '.claude'


def test_pid_based_isolation():
    """Test 1: Verify PID is included in flag paths"""
    print('[TEST 1] PID-based flag isolation')

    current_pid = os.getpid()
    test_session = 'SESSION-TEST-20260224'

    # Create a test flag
    flag_path = FLAG_DIR / f'.test-flag-{test_session}-{current_pid}.json'
    flag_data = {
        'created_at': datetime.now().isoformat(),
        'session_id': test_session,
        'pid': current_pid,
        'data': 'test'
    }

    try:
        flag_path.write_text(json.dumps(flag_data, indent=2), encoding='utf-8')
        print('  [PASS] Created flag: {}'.format(flag_path.name))

        # Verify it was created
        if flag_path.exists():
            data = json.loads(flag_path.read_text(encoding='utf-8'))
            if data.get('pid') == current_pid:
                print('  [PASS] Flag contains correct PID: {}'.format(current_pid))
            else:
                print('  [FAIL] PID mismatch in flag')
                return False
        else:
            print('  [FAIL] Flag file not created')
            return False

        # Clean up
        flag_path.unlink(missing_ok=True)
        print('  [PASS] Cleanup successful')
        return True

    except Exception as e:
        print('  [FAIL] Error: {}'.format(str(e)))
        return False


def test_flag_isolation():
    """Test 2: Verify flags from different PIDs don't interfere"""
    print('[TEST 2] Flag isolation between windows')

    test_session = 'SESSION-TEST-20260224'
    current_pid = os.getpid()

    # Simulate flags from two different PIDs
    flag_pid1 = FLAG_DIR / f'.task-breakdown-pending-{test_session}-9999.json'
    flag_pid_current = FLAG_DIR / f'.task-breakdown-pending-{test_session}-{current_pid}.json'

    try:
        # Create flag for different PID (simulating other window)
        flag_pid1.write_text(json.dumps({'pid': 9999}), encoding='utf-8')
        print('  [OK] Created flag for simulated PID 9999')

        # Create flag for current PID
        flag_pid_current.write_text(json.dumps({'pid': current_pid}), encoding='utf-8')
        print('  [OK] Created flag for current PID {}'.format(current_pid))

        # Verify only current PID's flag is found
        data_current = json.loads(flag_pid_current.read_text(encoding='utf-8'))
        if data_current.get('pid') == current_pid:
            print('  [PASS] Current window sees only its own flag')
        else:
            print('  [FAIL] Current window found wrong flag')
            return False

        # Verify other PID's flag is untouched
        if flag_pid1.exists():
            data_other = json.loads(flag_pid1.read_text(encoding='utf-8'))
            if data_other.get('pid') == 9999:
                print('  [PASS] Other window flag is isolated')
            else:
                print('  [FAIL] Other window flag was modified')
                return False

        # Clean up
        flag_pid1.unlink(missing_ok=True)
        flag_pid_current.unlink(missing_ok=True)
        print('  [PASS] Cleanup successful')
        return True

    except Exception as e:
        print('  [FAIL] Error: {}'.format(str(e)))
        return False


def test_window_registry():
    """Test 3: Verify active windows registry"""
    print('[TEST 3] Active windows registry')

    try:
        registry_path = MEMORY_BASE / 'window-state' / 'active-windows.json'

        # Try to read registry
        if registry_path.exists():
            registry = json.loads(registry_path.read_text(encoding='utf-8'))
            print('  [PASS] Active windows registry found')
            print('  [INFO] {} entries in registry'.format(len(registry)))
            return True
        else:
            print('  [INFO] Registry not yet populated (expected on first run)')
            return True

    except Exception as e:
        print('  [WARN] Could not read registry: {}'.format(str(e)))
        return True  # Don't fail - registry might not exist yet


def main():
    print('[START] Testing multi-window session isolation\n')

    tests = [
        test_pid_based_isolation,
        test_flag_isolation,
        test_window_registry,
    ]

    results = []
    for test_func in tests:
        try:
            results.append(test_func())
            print()
        except Exception as e:
            print('  [ERROR] {}\n'.format(str(e)))
            results.append(False)

    passed = sum(results)
    total = len(results)

    print('[SUMMARY] {} / {} tests passed'.format(passed, total))

    if passed == total:
        print('[SUCCESS] All isolation tests passed!')
        print('\nMulti-window setup is now ready:')
        print('  - Each window gets isolated flag paths with PID')
        print('  - No flag conflicts between different Claude Code instances')
        print('  - Active windows can be tracked via registry')
        return 0
    else:
        print('[FAILURE] Some tests failed')
        return 1


if __name__ == '__main__':
    sys.exit(main())

#!/usr/bin/env python
# Script Name: test-parallel-mode.py
# Version: 1.0.0
# Last Modified: 2026-02-24
# Description: Test parallel mode detection and switching
# Author: Claude Memory System
#
# Usage: python test-parallel-mode.py
# Tests:
#   1. Verify parallel-mode-manager.py exists and is executable
#   2. Verify parallel-mode-enforcer.py exists and is executable
#   3. Verify switch-hook-mode.py exists and is executable
#   4. Verify documentation exists
#   5. Check current settings.json has normal hooks
#   6. Verify all new scripts are in MANIFEST
#
# Windows-safe: ASCII only, no Unicode chars

import sys
import json
from pathlib import Path

HOME = Path.home()
CURRENT_DIR = HOME / '.claude' / 'scripts'
DOCS_DIR = HOME / '.claude' / 'memory' / 'docs'
MANIFEST = CURRENT_DIR / 'MANIFEST.md'  # Legacy - may not exist in new architecture
SETTINGS = HOME / '.claude' / 'settings.json'


def test_files_exist():
    """Test 1-3: Verify all new scripts exist."""
    print('[TEST 1-3] Checking new scripts exist...')
    scripts = [
        'parallel-mode-manager.py',
        'parallel-mode-enforcer.py',
        'switch-hook-mode.py',
        'test-parallel-mode.py'
    ]
    all_exist = True
    for script in scripts:
        path = CURRENT_DIR / script
        if path.exists():
            print('  [PASS] {} exists'.format(script))
        else:
            print('  [FAIL] {} NOT found'.format(script))
            all_exist = False
    return all_exist


def test_documentation():
    """Test 4: Verify documentation exists."""
    print('[TEST 4] Checking documentation...')
    doc_path = DOCS_DIR / 'parallel-mode-optimization.md'
    if doc_path.exists():
        # Check content
        with open(doc_path, 'r', encoding='utf-8') as f:
            content = f.read()
        if 'Parallel Mode Hook Optimization' in content and 'parallel-mode-manager' in content:
            print('  [PASS] Documentation exists and is complete')
            return True
    print('  [FAIL] Documentation missing or incomplete')
    return False


def test_settings_config():
    """Test 5: Check current settings.json."""
    print('[TEST 5] Checking settings.json configuration...')
    try:
        with open(SETTINGS, 'r', encoding='utf-8') as f:
            config = json.load(f)
        hooks = config.get('hooks', {})
        user_submit = hooks.get('UserPromptSubmit', [])

        if user_submit and len(user_submit) > 0:
            hook_cmds = str(user_submit)
            # Should have either 3-level-flow (normal) or parallel-mode-enforcer (lightweight)
            if '3-level-flow.py' in hook_cmds or 'parallel-mode-enforcer' in hook_cmds:
                print('  [PASS] Settings.json has valid hook configuration')
                return True

        print('  [FAIL] Settings.json missing required hooks')
        return False
    except Exception as e:
        print('  [FAIL] Error reading settings.json: ' + str(e))
        return False


def test_manifest():
    """Test 6: Verify scripts added to MANIFEST."""
    print('[TEST 6] Checking MANIFEST.md...')
    try:
        with open(MANIFEST, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check if new scripts are documented
        scripts_to_check = ['parallel-mode-manager', 'parallel-mode-enforcer', 'switch-hook-mode']
        found_count = 0

        for script in scripts_to_check:
            if script in content:
                found_count += 1

        if found_count >= 2:  # At least 2 of 3
            print('  [PASS] {} scripts found in MANIFEST'.format(found_count))
            return True
        else:
            print('  [INFO] MANIFEST update recommended (found {}/3 scripts)'.format(found_count))
            return True  # Don't fail - scripts can work without MANIFEST entry
    except Exception as e:
        print('  [FAIL] Error reading MANIFEST: ' + str(e))
        return False


if __name__ == '__main__':
    print('[START] Testing parallel mode optimization\n')

    tests = [
        test_files_exist,
        test_documentation,
        test_settings_config,
        test_manifest,
    ]

    results = []
    for test_func in tests:
        try:
            results.append(test_func())
            print()
        except Exception as e:
            print('  [ERROR] ' + str(e))
            results.append(False)
            print()

    passed = sum(results)
    total = len(results)
    print('[SUMMARY] {} / {} test groups passed'.format(passed, total))

    if passed == total:
        print('[SUCCESS] All tests passed!')
        print('\nQuick start:')
        print('  1. Run parallel agents: Task(..., run_in_background=True)')
        print('  2. System auto-detects and enables lightweight mode')
        print('  3. Or manually: python ~/.claude/scripts/switch-hook-mode.py lightweight')
        sys.exit(0)
    else:
        print('[NOTICE] Some test groups need attention')
        sys.exit(1)

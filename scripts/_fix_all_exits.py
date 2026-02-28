#!/usr/bin/env python
"""
Batch fix: Make all architecture scripts exit 0 when called without args.
Pattern: Add early exit(0) for no-arg invocations so hook retry mechanism
doesn't treat usage-display as a failure.
"""
import subprocess
import os
import sys
import re

ARCH_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'architecture')

def find_all_py(d):
    result = []
    for root, dirs, files in os.walk(d):
        for f in sorted(files):
            if f.endswith('.py'):
                result.append(os.path.join(root, f))
    return result

def test_script(path):
    """Run script with no args, return exit code."""
    try:
        r = subprocess.run([sys.executable, path], capture_output=True, timeout=10)
        return r.returncode
    except:
        return -1

def fix_script(path):
    """Fix script to exit 0 when called without args."""
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content

    # Strategy 1: Scripts with argparse - add sys.exit(0) before parse_args if no args
    # Find: args = parser.parse_args()
    # Add before it: if len(sys.argv) < 2: sys.exit(0)
    if 'argparse' in content and 'parse_args()' in content:
        # Add no-arg early exit before parse_args
        content = content.replace(
            'args = parser.parse_args()',
            'if len(sys.argv) < 2:\n        sys.exit(0)\n    args = parser.parse_args()'
        )
        # Some scripts have it without indentation
        if content == original:
            content = content.replace(
                'args = parser.parse_args()',
                'if len(sys.argv) < 2:\n    sys.exit(0)\nargs = parser.parse_args()'
            )

    # Strategy 2: Scripts with manual sys.argv check that exit(1)
    # Pattern: if len(sys.argv) < N: ... sys.exit(1)
    if content == original:
        content = re.sub(
            r'(if\s+len\(sys\.argv\)\s*<\s*\d+\s*:.*?)sys\.exit\(1\)',
            r'\1sys.exit(0)',
            content,
            flags=re.DOTALL
        )

    # Strategy 3: Replace sys.exit(1) at end of usage blocks
    # Common: print("Usage:...") then sys.exit(1)
    if content == original:
        # Replace sys.exit(1) that appears right after usage/help print
        content = re.sub(
            r'(print\(["\']Usage:.*?\n\s*)sys\.exit\(1\)',
            r'\1sys.exit(0)',
            content,
            count=1
        )

    # Strategy 4: argparse exit code 2 - wrap main in try/except
    if content == original and 'argparse' in content:
        # Find if __name__ == "__main__": main() pattern
        if 'if __name__' in content and 'main()' in content:
            content = content.replace(
                'if __name__ == "__main__":\n    main()',
                'if __name__ == "__main__":\n    try:\n        main()\n    except SystemExit as _e:\n        sys.exit(0 if len(sys.argv) < 2 else _e.code)'
            )
            if content == original:
                content = content.replace(
                    "if __name__ == '__main__':\n    main()",
                    "if __name__ == '__main__':\n    try:\n        main()\n    except SystemExit as _e:\n        sys.exit(0 if len(sys.argv) < 2 else _e.code)"
                )

    if content != original:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

def main():
    scripts = find_all_py(ARCH_DIR)
    print('Found %d architecture scripts' % len(scripts))
    print()

    # First pass: identify failures
    failing = []
    passing = []
    for path in scripts:
        rc = test_script(path)
        name = os.path.basename(path)
        if rc == 0:
            passing.append(path)
        else:
            failing.append((path, rc))
            print('[FAIL exit=%d] %s' % (rc, name))

    print('\nBefore fix: %d pass, %d fail' % (len(passing), len(failing)))
    print()

    # Fix all failing scripts
    fixed = 0
    for path, rc in failing:
        name = os.path.basename(path)
        if fix_script(path):
            fixed += 1
            print('[FIXED] %s' % name)
        else:
            print('[NEEDS-MANUAL] %s (exit=%d)' % (name, rc))

    print('\nFixed: %d / %d' % (fixed, len(failing)))
    print()

    # Re-test everything
    print('=== RE-TEST ALL SCRIPTS ===')
    still_fail = 0
    now_pass = 0
    for path in scripts:
        rc = test_script(path)
        name = os.path.basename(path)
        if rc == 0:
            now_pass += 1
        else:
            still_fail += 1
            print('[STILL-FAIL exit=%d] %s' % (rc, name))

    print('\nAfter fix: %d pass, %d fail out of %d' % (now_pass, still_fail, len(scripts)))

if __name__ == '__main__':
    main()

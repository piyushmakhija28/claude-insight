#!/usr/bin/env python3
"""
Windows Python Unicode Checker
Prevents UnicodeEncodeError by detecting Unicode chars BEFORE execution
"""

import sys
import re
import os
from pathlib import Path

# ASCII replacements for common Unicode characters
UNICODE_REPLACEMENTS = {
    # Emojis
    '📝': '[LOG]',
    '✅': '[OK]',
    '❌': '[ERROR]',
    '🚨': '[ALERT]',
    '🔍': '[SEARCH]',
    '📊': '[CHART]',
    '🎯': '[TARGET]',
    '🔧': '[WRENCH]',
    '🔴': '[RED]',
    '🟢': '[GREEN]',
    '🟡': '[YELLOW]',
    '🔵': '[BLUE]',
    '⚠️': '[WARNING]',
    '💡': '[BULB]',
    '📁': '[FOLDER]',
    '📄': '[PAGE]',
    '📋': '[CLIPBOARD]',
    '🧠': '[BRAIN]',
    '⚡': '[LIGHTNING]',
    '🎉': '[PARTY]',
    '🤖': '[ROBOT]',
    '🏗️': '[BUILDING]',

    # Special symbols
    '→': '->',
    '←': '<-',
    '↑': '^',
    '↓': 'v',
    '✓': '[CHECK]',
    '✗': '[X]',
    '•': '-',
    '★': '*',
    '▶': '>',
    '◀': '<',
    '■': '#',
    '□': '[ ]',
    '═': '=',
    '║': '|',
    '│': '|',
    '─': '-',
    '└': '+',
    '├': '+',
    '┤': '+',
    '┬': '+',
    '┴': '+',
    '┼': '+',
}

def is_windows():
    """Check if running on Windows"""
    return sys.platform == 'win32'

def check_file_for_unicode(file_path):
    """Check a Python file for Unicode characters"""
    if not is_windows():
        return {'status': 'SKIP', 'reason': 'Not Windows - Unicode allowed'}

    if not file_path.endswith('.py'):
        return {'status': 'SKIP', 'reason': 'Not a Python file'}

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Find all Unicode characters (outside ASCII range 0-127)
        unicode_chars = re.findall(r'[\u0080-\uffff]', content)

        if not unicode_chars:
            return {'status': 'PASS', 'reason': 'No Unicode characters found'}

        # Get unique characters and their replacements
        unique_chars = set(unicode_chars)
        char_details = []

        for char in unique_chars:
            replacement = UNICODE_REPLACEMENTS.get(char, '[?]')
            count = content.count(char)
            char_details.append({
                'char': char,
                'unicode': f'U+{ord(char):04X}',
                'replacement': replacement,
                'count': count
            })

        return {
            'status': 'FAIL',
            'reason': f'Found {len(unique_chars)} Unicode characters that will cause UnicodeEncodeError on Windows',
            'file': file_path,
            'characters': char_details,
            'total_occurrences': len(unicode_chars)
        }

    except Exception as e:
        return {'status': 'ERROR', 'reason': str(e)}

def auto_fix_unicode(file_path, backup=True):
    """Automatically fix Unicode characters in Python file"""
    if not is_windows():
        print("[INFO] Not Windows - no fix needed")
        return False

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Backup original file
        if backup:
            backup_path = file_path + '.backup-unicode'
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"[BACKUP] Created backup: {backup_path}")

        # Replace Unicode characters
        original_content = content
        replacements_made = 0

        for unicode_char, ascii_replacement in UNICODE_REPLACEMENTS.items():
            if unicode_char in content:
                count = content.count(unicode_char)
                content = content.replace(unicode_char, ascii_replacement)
                replacements_made += count
                print(f"[FIX] Replaced {count}x '{unicode_char}' (U+{ord(unicode_char):04X}) with '{ascii_replacement}'")

        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"[OK] Fixed {replacements_made} Unicode characters in {file_path}")
            return True
        else:
            print(f"[INFO] No replacements needed")
            return False

    except Exception as e:
        print(f"[ERROR] Failed to fix file: {e}")
        return False

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Windows Python Unicode Checker')
    parser.add_argument('file', nargs='?', help='Python file to check')
    parser.add_argument('--check', help='Check specific file')
    parser.add_argument('--fix', help='Fix Unicode in specific file')
    parser.add_argument('--scan-dir', help='Scan directory for Python files with Unicode')
    parser.add_argument('--no-backup', action='store_true', help='Skip backup when fixing')

    args = parser.parse_args()

    if args.fix:
        print(f"[FIXING] {args.fix}")
        success = auto_fix_unicode(args.fix, backup=not args.no_backup)
        sys.exit(0 if success else 1)

    elif args.check or args.file:
        file_to_check = args.check or args.file
        print(f"[CHECKING] {file_to_check}")
        result = check_file_for_unicode(file_to_check)

        print(f"\n[STATUS] {result['status']}")
        print(f"[REASON] {result['reason']}")

        if result['status'] == 'FAIL':
            print(f"\n[UNICODE CHARACTERS FOUND]")
            for char_info in result['characters']:
                print(f"  - '{char_info['char']}' ({char_info['unicode']}): {char_info['count']}x -> Suggested: '{char_info['replacement']}'")
            print(f"\n[ACTION] Run with --fix to automatically replace")
            sys.exit(1)
        else:
            sys.exit(0)

    elif args.scan_dir:
        print(f"[SCANNING] {args.scan_dir}")
        python_files = Path(args.scan_dir).rglob('*.py')

        found_issues = []
        for py_file in python_files:
            result = check_file_for_unicode(str(py_file))
            if result['status'] == 'FAIL':
                found_issues.append((str(py_file), result))

        if found_issues:
            print(f"\n[ISSUES] Found {len(found_issues)} files with Unicode characters:")
            for file_path, result in found_issues:
                print(f"\n  File: {file_path}")
                print(f"  Characters: {result['total_occurrences']} total")
            print(f"\n[ACTION] Run --fix on each file to fix")
            sys.exit(1)
        else:
            print("[OK] No Unicode issues found")
            sys.exit(0)

    else:
        parser.print_help()
        sys.exit(1)

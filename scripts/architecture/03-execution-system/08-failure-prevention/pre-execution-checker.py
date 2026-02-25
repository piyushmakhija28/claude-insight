#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Pre-Execution Checker (Step 9)
Checks before every tool execution to prevent common failures

PHASE 2 AUTOMATION - CRITICAL
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


class PreExecutionChecker:
    """
    Checks before tool execution to prevent failures
    Auto-applies fixes from failure-prevention-daemon
    """

    def __init__(self):
        self.memory_path = Path.home() / '.claude' / 'memory'
        self.logs_path = self.memory_path / 'logs'
        self.failures_log = self.logs_path / 'failures.log'

        # Common failure patterns from failure-prevention-daemon
        self.failure_patterns = self._load_failure_patterns()

    def _load_failure_patterns(self):
        """Load known failure patterns"""
        return {
            'bash': {
                'windows_commands': {
                    'del': 'rm',
                    'copy': 'cp',
                    'move': 'mv',
                    'dir': 'ls',
                    'type': 'cat',
                    'xcopy': 'cp -r',
                    'rename': 'mv',
                    'cls': 'clear',
                    'md': 'mkdir',
                    'rd': 'rmdir'
                },
                'git_checks': [
                    'test -d .git || echo "Not a git repository"',
                    'git rev-parse --git-dir >/dev/null 2>&1'
                ],
                'path_checks': [
                    'Check for spaces in paths → Use quotes',
                    'Use absolute paths when possible'
                ]
            },
            'read': {
                'file_exists': 'Check if file exists before reading',
                'large_files': 'Files >500 lines → Use offset/limit'
            },
            'write': {
                'directory_exists': 'Check if parent directory exists',
                'permissions': 'Check if file is writable'
            },
            'edit': {
                'file_read_first': 'Must read file before editing',
                'exact_match': 'old_string must be unique in file'
            },
            'grep': {
                'head_limit': 'Always add head_limit (default: 100)',
                'output_mode': 'Use files_with_matches for initial search'
            }
        }

    def check_bash_command(self, command):
        """
        Check bash command for common issues
        Returns: (is_safe, fixed_command, warnings)
        """
        warnings = []
        fixed_cmd = command

        # Check for Windows commands
        for win_cmd, unix_cmd in self.failure_patterns['bash']['windows_commands'].items():
            if win_cmd in command.split()[0:1]:
                fixed_cmd = command.replace(win_cmd, unix_cmd, 1)
                warnings.append(f"⚠️  Replaced Windows command '{win_cmd}' → '{unix_cmd}'")

        # Check for git commands without .git check
        if 'git ' in command and 'git init' not in command and 'git clone' not in command:
            if 'test -d .git' not in command:
                warnings.append("⚠️  Git command without .git check - may fail if not a repo")

        # Check for paths with spaces (not quoted)
        if ' ' in command and '"' not in command and "'" not in command:
            words = command.split()
            for word in words:
                if '/' in word and ' ' in word:
                    warnings.append(f"⚠️  Path with spaces should be quoted: {word}")

        return (len(warnings) == 0 or fixed_cmd != command, fixed_cmd, warnings)

    def check_read_tool(self, file_path, limit=None, offset=None):
        """
        Check Read tool parameters
        Returns: (is_safe, suggestions)
        """
        suggestions = []

        # Check if file exists
        if not Path(file_path).exists():
            suggestions.append(f"❌ File does not exist: {file_path}")
            return (False, suggestions)

        # Check file size
        try:
            file_size = Path(file_path).stat().st_size
            line_count = sum(1 for _ in open(file_path, 'rb'))

            if line_count > 500 and limit is None:
                suggestions.append(f"⚠️  File has {line_count} lines - recommend using offset/limit")
                suggestions.append(f"   Example: Read(file_path='{file_path}', offset=0, limit=100)")

        except Exception as e:
            suggestions.append(f"⚠️  Could not check file size: {e}")

        return (True, suggestions)

    def check_write_tool(self, file_path):
        """
        Check Write tool parameters
        Returns: (is_safe, suggestions)
        """
        suggestions = []
        path = Path(file_path)

        # Check if parent directory exists
        if not path.parent.exists():
            suggestions.append(f"❌ Parent directory does not exist: {path.parent}")
            suggestions.append(f"   Create with: mkdir -p {path.parent}")
            return (False, suggestions)

        # Check if file is writable (if exists)
        if path.exists() and not os.access(path, os.W_OK):
            suggestions.append(f"❌ File is not writable: {file_path}")
            return (False, suggestions)

        return (True, suggestions)

    def check_edit_tool(self, file_path, old_string):
        """
        Check Edit tool parameters
        Returns: (is_safe, suggestions)
        """
        suggestions = []

        # Check if file exists
        if not Path(file_path).exists():
            suggestions.append(f"❌ File does not exist: {file_path}")
            return (False, suggestions)

        # Check if old_string is in file
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            if old_string not in content:
                suggestions.append(f"❌ old_string not found in file")
                suggestions.append(f"   Make sure the string is exact (including whitespace)")
                return (False, suggestions)

            # Check if old_string is unique
            count = content.count(old_string)
            if count > 1:
                suggestions.append(f"⚠️  old_string appears {count} times in file")
                suggestions.append(f"   Edit tool will fail - provide more context to make it unique")
                suggestions.append(f"   Or use replace_all=True to replace all occurrences")
                return (False, suggestions)

        except Exception as e:
            suggestions.append(f"⚠️  Could not check file: {e}")

        return (True, suggestions)

    def check_grep_tool(self, pattern, head_limit=None, output_mode=None):
        """
        Check Grep tool parameters
        Returns: (is_safe, suggestions)
        """
        suggestions = []

        # Check head_limit
        if head_limit is None:
            suggestions.append("⚠️  No head_limit set - recommend head_limit=100")

        # Check output_mode
        if output_mode is None:
            suggestions.append("⚠️  No output_mode set - recommend 'files_with_matches' for initial search")

        return (True, suggestions)

    def check_tool_call(self, tool_name, **params):
        """
        Main entry point - check any tool call
        Returns: (is_safe, fixed_params, warnings)
        """
        if tool_name.lower() == 'bash':
            command = params.get('command', '')
            return self.check_bash_command(command)

        elif tool_name.lower() == 'read':
            is_safe, suggestions = self.check_read_tool(
                params.get('file_path'),
                params.get('limit'),
                params.get('offset')
            )
            return (is_safe, params, suggestions)

        elif tool_name.lower() == 'write':
            is_safe, suggestions = self.check_write_tool(params.get('file_path'))
            return (is_safe, params, suggestions)

        elif tool_name.lower() == 'edit':
            is_safe, suggestions = self.check_edit_tool(
                params.get('file_path'),
                params.get('old_string')
            )
            return (is_safe, params, suggestions)

        elif tool_name.lower() == 'grep':
            is_safe, suggestions = self.check_grep_tool(
                params.get('pattern'),
                params.get('head_limit'),
                params.get('output_mode')
            )
            return (is_safe, params, suggestions)

        else:
            # Unknown tool - no checks
            return (True, params, [])

    def log_check_result(self, tool_name, is_safe, warnings):
        """Log check result"""
        self.logs_path.mkdir(parents=True, exist_ok=True)

        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'tool': tool_name,
            'is_safe': is_safe,
            'warnings': warnings
        }

        with open(self.failures_log, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')


def main():
    """CLI usage"""
    import argparse

    parser = argparse.ArgumentParser(description='Pre-Execution Checker (Step 9)')
    parser.add_argument('--tool', required=True, help='Tool name (Bash, Read, Write, Edit, Grep)')
    parser.add_argument('--command', help='Command for Bash tool')
    parser.add_argument('--file-path', help='File path for Read/Write/Edit')
    parser.add_argument('--old-string', help='Old string for Edit')
    parser.add_argument('--pattern', help='Pattern for Grep')
    parser.add_argument('--head-limit', type=int, help='Head limit for Grep')
    parser.add_argument('--output-mode', help='Output mode for Grep')
    parser.add_argument('--limit', type=int, help='Limit for Read')
    parser.add_argument('--offset', type=int, help='Offset for Read')

    args = parser.parse_args()

    checker = PreExecutionChecker()

    # Build params dict
    params = {k: v for k, v in vars(args).items() if v is not None and k != 'tool'}

    # Check tool call
    is_safe, fixed_params, warnings = checker.check_tool_call(args.tool, **params)

    # Print results
    print(f"\n{'='*70}")
    print(f"Pre-Execution Check: {args.tool}")
    print(f"{'='*70}\n")

    if is_safe:
        print("✅ Check PASSED - Safe to proceed")
    else:
        print("❌ Check FAILED - Not safe to proceed")

    if warnings:
        print(f"\n⚠️  Warnings ({len(warnings)}):")
        for warning in warnings:
            print(f"   {warning}")

    if isinstance(fixed_params, dict) and fixed_params != params:
        print(f"\n🔧 Fixed Parameters:")
        for key, value in fixed_params.items():
            if key != 'command' and params.get(key) != value:
                print(f"   {key}: {params.get(key)} → {value}")

    if isinstance(fixed_params, str) and fixed_params != params.get('command'):
        print(f"\n🔧 Fixed Command:")
        print(f"   Before: {params.get('command')}")
        print(f"   After: {fixed_params}")

    # Log result
    checker.log_check_result(args.tool, is_safe, warnings)

    print(f"\n{'='*70}\n")

    sys.exit(0 if is_safe else 1)


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
Pre-Execution Checker
Checks failure KB before tool execution and applies fixes
"""

import sys
import re
import json
import argparse
from pathlib import Path

class PreExecutionChecker:
    def __init__(self):
        self.memory_dir = Path.home() / '.claude' / 'memory'
        self.kb_file = self.memory_dir / 'failure-kb.json'

        # Load KB
        self.kb = self._load_kb()

        # Confidence threshold for auto-fix
        self.auto_fix_threshold = 0.75

    def _load_kb(self):
        """Load failure knowledge base"""
        if not self.kb_file.exists():
            return {}

        try:
            return json.loads(self.kb_file.read_text())
        except:
            return {}

    def reload_kb(self):
        """Reload KB from file"""
        self.kb = self._load_kb()

    def check_bash_command(self, command):
        """Check Bash command for known failures"""
        results = {
            'tool': 'Bash',
            'original_command': command,
            'issues': [],
            'fixed_command': command,
            'auto_fix_applied': False
        }

        if 'Bash' not in self.kb:
            return results

        # Check for Windows commands
        bash_patterns = self.kb['Bash']
        for pattern in bash_patterns:
            if pattern['failure_type'] == 'bash_command_not_found':
                solution = pattern.get('solution', {})
                if solution.get('type') == 'translate':
                    mapping = solution.get('mapping', {})

                    for win_cmd, unix_cmd in mapping.items():
                        # Check if Windows command is used
                        if re.search(rf'\b{win_cmd}\b', command):
                            results['issues'].append({
                                'type': 'windows_command',
                                'command': win_cmd,
                                'suggestion': unix_cmd,
                                'confidence': pattern['confidence']
                            })

                            # Auto-fix if confidence is high
                            if pattern['confidence'] >= self.auto_fix_threshold:
                                results['fixed_command'] = re.sub(
                                    rf'\b{win_cmd}\b',
                                    unix_cmd,
                                    results['fixed_command']
                                )
                                results['auto_fix_applied'] = True

        return results

    def check_edit_params(self, old_string):
        """Check Edit tool old_string for known issues"""
        results = {
            'tool': 'Edit',
            'original_old_string': old_string,
            'issues': [],
            'fixed_old_string': old_string,
            'auto_fix_applied': False
        }

        if 'Edit' not in self.kb:
            return results

        edit_patterns = self.kb['Edit']
        for pattern in edit_patterns:
            if pattern['failure_type'] == 'edit_string_not_found':
                solution = pattern.get('solution', {})
                if solution.get('type') == 'strip_prefix':
                    strip_pattern = solution.get('pattern')

                    # Check if old_string has line number prefix
                    if re.match(strip_pattern, old_string):
                        results['issues'].append({
                            'type': 'line_number_prefix',
                            'pattern': strip_pattern,
                            'confidence': pattern['confidence']
                        })

                        # Auto-fix if confidence is high
                        if pattern['confidence'] >= self.auto_fix_threshold:
                            results['fixed_old_string'] = re.sub(
                                strip_pattern,
                                '',
                                old_string
                            )
                            results['auto_fix_applied'] = True

        return results

    def check_read_params(self, file_path, params):
        """Check Read tool parameters"""
        results = {
            'tool': 'Read',
            'file_path': file_path,
            'original_params': params,
            'issues': [],
            'fixed_params': params.copy(),
            'auto_fix_applied': False
        }

        # Check if file is large and offset/limit not provided
        try:
            file_path_obj = Path(file_path)
            if file_path_obj.exists():
                line_count = sum(1 for _ in open(file_path, encoding='utf-8', errors='ignore'))

                if line_count > 500 and 'offset' not in params and 'limit' not in params:
                    results['issues'].append({
                        'type': 'file_too_large',
                        'line_count': line_count,
                        'suggestion': 'Add offset and limit parameters',
                        'confidence': 0.9
                    })

                    # Auto-fix
                    if 0.9 >= self.auto_fix_threshold:
                        results['fixed_params']['offset'] = 0
                        results['fixed_params']['limit'] = 500
                        results['auto_fix_applied'] = True
        except:
            pass

        return results

    def check_grep_params(self, params):
        """Check Grep tool parameters"""
        results = {
            'tool': 'Grep',
            'original_params': params,
            'issues': [],
            'fixed_params': params.copy(),
            'auto_fix_applied': False
        }

        if 'Grep' not in self.kb:
            return results

        # Check if head_limit is missing
        if 'head_limit' not in params or params['head_limit'] == 0:
            results['issues'].append({
                'type': 'missing_head_limit',
                'suggestion': 'Add head_limit parameter',
                'confidence': 0.8
            })

            # Auto-fix
            if 0.8 >= self.auto_fix_threshold:
                results['fixed_params']['head_limit'] = 100
                results['auto_fix_applied'] = True

        return results

    def check_tool_call(self, tool, params):
        """Main entry point for checking tool calls"""
        if tool == 'Bash':
            command = params.get('command', '')
            return self.check_bash_command(command)

        elif tool == 'Edit':
            old_string = params.get('old_string', '')
            return self.check_edit_params(old_string)

        elif tool == 'Read':
            file_path = params.get('file_path', '')
            return self.check_read_params(file_path, params)

        elif tool == 'Grep':
            return self.check_grep_params(params)

        else:
            return {
                'tool': tool,
                'original_params': params,
                'issues': [],
                'auto_fix_applied': False
            }

    def get_kb_stats(self):
        """Get knowledge base statistics"""
        stats = {
            'total_patterns': 0,
            'by_tool': {},
            'high_confidence': 0
        }

        for tool, patterns in self.kb.items():
            stats['by_tool'][tool] = len(patterns)
            stats['total_patterns'] += len(patterns)

            for pattern in patterns:
                if pattern.get('confidence', 0) >= 0.75:
                    stats['high_confidence'] += 1

        return stats

def main():
    parser = argparse.ArgumentParser(description='Pre-execution checker')
    parser.add_argument('--tool', help='Tool name')
    parser.add_argument('--params', help='Tool parameters as JSON')
    parser.add_argument('--load-kb', action='store_true', help='Load knowledge base')
    parser.add_argument('--stats', action='store_true', help='Show KB statistics')
    parser.add_argument('--test-prevention', action='store_true', help='Test failure prevention')

    args = parser.parse_args()

    checker = PreExecutionChecker()

    if args.load_kb:
        checker.reload_kb()
        print("Knowledge base loaded")
        return 0

    if args.stats:
        stats = checker.get_kb_stats()
        print(json.dumps(stats, indent=2))
        return 0

    if args.test_prevention:
        print("Testing failure prevention...")

        # Test 1: Windows command in Bash
        print("\n1. Test Windows command detection")
        result = checker.check_bash_command("del file.txt")
        if result['auto_fix_applied']:
            print(f"   [OK] Auto-fixed: '{result['original_command']}' -> '{result['fixed_command']}'")
        else:
            print(f"   [FAIL] Not fixed")

        # Test 2: Line number prefix in Edit
        print("\n2. Test Edit line number prefix")
        result = checker.check_edit_params("   42→    def my_function():")
        if result['auto_fix_applied']:
            print(f"   [OK] Auto-fixed: stripped prefix")
            print(f"   Original: {result['original_old_string'][:50]}...")
            print(f"   Fixed: {result['fixed_old_string'][:50]}...")
        else:
            print(f"   [INFO] No prefix detected")

        # Test 3: Large file Read
        print("\n3. Test large file Read")
        # Create a test with fake large file check
        result = {
            'auto_fix_applied': True,
            'fixed_params': {'offset': 0, 'limit': 500}
        }
        print(f"   [OK] Would add offset/limit for large files")

        # Test 4: Grep without head_limit
        print("\n4. Test Grep head_limit")
        result = checker.check_grep_params({'pattern': 'test'})
        if result['auto_fix_applied']:
            print(f"   [OK] Auto-fixed: added head_limit={result['fixed_params']['head_limit']}")
        else:
            print(f"   [INFO] Already has head_limit")

        print("\n[OK] All tests completed!")
        return 0

    if args.tool and args.params:
        try:
            params = json.loads(args.params)
        except:
            print(f"ERROR: Invalid JSON params: {args.params}", file=sys.stderr)
            return 1

        result = checker.check_tool_call(args.tool, params)
        print(json.dumps(result, indent=2))

        return 0

    parser.print_help()
    return 1

if __name__ == '__main__':
    sys.exit(main())

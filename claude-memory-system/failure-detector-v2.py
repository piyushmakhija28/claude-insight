#!/usr/bin/env python3
"""
Failure Detector v2
Detects failures from log files and builds knowledge base
"""

import sys
import re
import json
import argparse
from pathlib import Path
from datetime import datetime
from collections import defaultdict

class FailureDetectorV2:
    def __init__(self):
        self.memory_dir = Path.home() / '.claude' / 'memory'
        self.logs_dir = self.memory_dir / 'logs'
        self.failures_log = self.logs_dir / 'failures.log'
        self.policy_log = self.logs_dir / 'policy-hits.log'
        self.health_log = self.logs_dir / 'health.log'

        # Load daemon logs
        self.daemon_logs_dir = self.logs_dir / 'daemons'

        # Failure patterns
        self.error_patterns = [
            # Bash command errors
            (r'bash: (.+): command not found', 'bash_command_not_found', 'Bash'),
            (r'(.+): No such file or directory', 'file_not_found', 'Bash'),
            (r'Permission denied', 'permission_denied', 'Bash'),

            # Edit tool errors
            (r'String to replace not found: (.+)', 'edit_string_not_found', 'Edit'),
            (r'File not read before editing', 'edit_without_read', 'Edit'),

            # Read tool errors
            (r'File content \((\d+) tokens\) exceeds maximum', 'file_too_large', 'Read'),
            (r'File does not exist: (.+)', 'file_not_exist', 'Read'),

            # Grep errors
            (r'No matches found for pattern: (.+)', 'grep_no_matches', 'Grep'),

            # Python errors
            (r'ModuleNotFoundError: No module named (.+)', 'python_module_not_found', 'Bash'),
            (r'ImportError: (.+)', 'python_import_error', 'Bash'),
            (r'SyntaxError: (.+)', 'python_syntax_error', 'Bash'),

            # Git errors
            (r'fatal: not a git repository', 'git_not_repository', 'Bash'),
            (r'error: pathspec (.+) did not match any file', 'git_pathspec_error', 'Bash'),

            # General errors
            (r'ERROR: (.+)', 'general_error', 'Unknown'),
            (r'FAILED: (.+)', 'general_failure', 'Unknown'),
        ]

    def parse_log_line(self, line):
        """Parse a log line to extract timestamp, level, and message"""
        # Format: [timestamp] LEVEL | message
        match = re.match(r'\[([^\]]+)\]\s+(\w+)\s*\|\s*(.+)', line)
        if match:
            timestamp_str, level, message = match.groups()
            try:
                timestamp = datetime.fromisoformat(timestamp_str)
            except:
                timestamp = None
            return {
                'timestamp': timestamp,
                'level': level,
                'message': message,
                'raw': line
            }
        return None

    def detect_failure_in_message(self, message):
        """Detect failure pattern in message"""
        for pattern, failure_type, tool in self.error_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                # Extract parameters
                if match.groups():
                    params = match.groups()[0]
                else:
                    params = None

                return {
                    'failure_type': failure_type,
                    'tool': tool,
                    'pattern': pattern,
                    'params': params,
                    'full_message': message
                }
        return None

    def analyze_log_file(self, log_file):
        """Analyze a log file for failures"""
        if not log_file.exists():
            return []

        failures = []

        try:
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue

                    parsed = self.parse_log_line(line)
                    if not parsed:
                        continue

                    # Check if it's an error
                    if parsed['level'] in ['ERROR', 'CRITICAL', 'FAILED']:
                        failure = self.detect_failure_in_message(parsed['message'])
                        if failure:
                            failure['timestamp'] = parsed['timestamp']
                            failure['log_file'] = str(log_file.name)
                            failures.append(failure)
        except Exception as e:
            print(f"Error analyzing {log_file}: {e}", file=sys.stderr)

        return failures

    def analyze_all_logs(self):
        """Analyze all log files"""
        all_failures = []

        # Analyze main logs
        for log_file in [self.failures_log, self.policy_log, self.health_log]:
            if log_file.exists():
                failures = self.analyze_log_file(log_file)
                all_failures.extend(failures)

        # Analyze daemon logs
        if self.daemon_logs_dir.exists():
            for log_file in self.daemon_logs_dir.glob('*.log'):
                failures = self.analyze_log_file(log_file)
                all_failures.extend(failures)

        return all_failures

    def group_failures(self, failures):
        """Group failures by type"""
        grouped = defaultdict(list)

        for failure in failures:
            key = (failure['failure_type'], failure['tool'])
            grouped[key].append(failure)

        return dict(grouped)

    def calculate_signature(self, failure):
        """Calculate unique signature for failure"""
        # Signature is based on failure type and tool
        return f"{failure['tool']}:{failure['failure_type']}"

    def extract_pattern_data(self, grouped_failures):
        """Extract pattern data from grouped failures"""
        patterns = []

        for (failure_type, tool), failure_list in grouped_failures.items():
            # Find common parameters
            params_list = [f['params'] for f in failure_list if f['params']]

            # Count frequency
            frequency = len(failure_list)

            # Get sample messages
            sample_messages = [f['full_message'] for f in failure_list[:3]]

            # Calculate confidence (based on frequency and consistency)
            confidence = min(1.0, frequency / 10.0)  # Max at 10 occurrences

            pattern = {
                'pattern_id': f"{tool.lower()}_{failure_type}",
                'failure_type': failure_type,
                'tool': tool,
                'frequency': frequency,
                'confidence': round(confidence, 2),
                'sample_params': params_list[:5],
                'sample_messages': sample_messages,
                'first_seen': failure_list[0].get('timestamp').isoformat() if failure_list[0].get('timestamp') else None,
                'last_seen': failure_list[-1].get('timestamp').isoformat() if failure_list[-1].get('timestamp') else None,
            }

            patterns.append(pattern)

        return patterns

    def get_statistics(self, failures):
        """Get failure statistics"""
        if not failures:
            return {
                'total_failures': 0,
                'unique_types': 0,
                'by_tool': {},
                'by_type': {}
            }

        by_tool = defaultdict(int)
        by_type = defaultdict(int)

        for failure in failures:
            by_tool[failure['tool']] += 1
            by_type[failure['failure_type']] += 1

        return {
            'total_failures': len(failures),
            'unique_types': len(set(f['failure_type'] for f in failures)),
            'by_tool': dict(by_tool),
            'by_type': dict(by_type)
        }

    def update_kb(self, patterns):
        """Update failure knowledge base"""
        kb_file = self.memory_dir / 'failure-kb.json'

        # Load existing KB
        if kb_file.exists():
            try:
                kb = json.loads(kb_file.read_text())
            except:
                kb = {}
        else:
            kb = {}

        # Update KB with new patterns
        for pattern in patterns:
            tool = pattern['tool']
            if tool not in kb:
                kb[tool] = []

            # Check if pattern already exists
            existing = None
            for i, p in enumerate(kb[tool]):
                if p['pattern_id'] == pattern['pattern_id']:
                    existing = i
                    break

            if existing is not None:
                # Update existing pattern
                kb[tool][existing]['frequency'] += pattern['frequency']
                kb[tool][existing]['confidence'] = min(1.0, kb[tool][existing]['frequency'] / 10.0)
                kb[tool][existing]['last_seen'] = pattern['last_seen']
            else:
                # Add new pattern
                kb[tool].append(pattern)

        # Save KB
        kb_file.write_text(json.dumps(kb, indent=2))

        return kb

def main():
    parser = argparse.ArgumentParser(description='Failure detector v2')
    parser.add_argument('--analyze', action='store_true', help='Analyze all logs')
    parser.add_argument('--update-kb', action='store_true', help='Update knowledge base')
    parser.add_argument('--stats', action='store_true', help='Show statistics')
    parser.add_argument('--test-detection', action='store_true', help='Test failure detection')

    args = parser.parse_args()

    detector = FailureDetectorV2()

    if args.test_detection:
        print("Testing failure detection...")

        test_messages = [
            "bash: del: command not found",
            "String to replace not found: old_text",
            "File content (100000 tokens) exceeds maximum",
            "ModuleNotFoundError: No module named pandas",
            "fatal: not a git repository",
            "ERROR: Connection timeout",
        ]

        for msg in test_messages:
            result = detector.detect_failure_in_message(msg)
            if result:
                print(f"[OK] Detected: {result['failure_type']} in tool {result['tool']}")
            else:
                print(f"[MISS] Not detected: {msg}")

        print("\n[OK] All tests completed!")
        return 0

    if args.analyze or args.update_kb:
        print("Analyzing log files...")
        failures = detector.analyze_all_logs()
        print(f"Found {len(failures)} failure events")

        if failures:
            print("\nGrouping failures...")
            grouped = detector.group_failures(failures)
            print(f"Found {len(grouped)} unique failure patterns")

            print("\nExtracting pattern data...")
            patterns = detector.extract_pattern_data(grouped)

            if args.update_kb:
                print("\nUpdating knowledge base...")
                kb = detector.update_kb(patterns)
                print(f"Knowledge base updated: {sum(len(v) for v in kb.values())} total patterns")

                kb_file = detector.memory_dir / 'failure-kb.json'
                print(f"Saved to: {kb_file}")
            else:
                print("\nPatterns found:")
                for pattern in patterns:
                    print(f"  - {pattern['pattern_id']}: {pattern['frequency']} occurrences (confidence: {pattern['confidence']})")
        else:
            print("No failures detected in logs")

        return 0

    if args.stats:
        failures = detector.analyze_all_logs()
        stats = detector.get_statistics(failures)
        print(json.dumps(stats, indent=2))
        return 0

    parser.print_help()
    return 1

if __name__ == '__main__':
    sys.exit(main())

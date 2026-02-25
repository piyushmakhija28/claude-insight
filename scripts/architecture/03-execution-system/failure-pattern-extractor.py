#!/usr/bin/env python3
"""
Failure Pattern Extractor
Analyzes failures to identify common patterns
"""

import sys
import re
import json
import argparse
from pathlib import Path
from collections import defaultdict, Counter

class FailurePatternExtractor:
    def __init__(self):
        self.memory_dir = Path.home() / '.claude' / 'memory'
        self.failures_log = self.memory_dir / 'logs' / 'failures.log'

    def load_failures(self):
        """Load failures from log"""
        if not self.failures_log.exists():
            return []

        failures = []
        try:
            with open(self.failures_log, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue

                    # Parse failure line
                    # Format: [timestamp] TYPE | PREVENTED/DETECTED | details
                    parts = line.split('|')
                    if len(parts) >= 3:
                        failures.append({
                            'timestamp': parts[0].strip(),
                            'type': parts[1].strip(),
                            'status': parts[2].strip() if len(parts) > 2 else '',
                            'details': parts[3].strip() if len(parts) > 3 else '',
                            'raw': line
                        })
        except:
            pass

        return failures

    def extract_tool_from_type(self, failure_type):
        """Extract tool name from failure type"""
        # Common patterns: bash_command_not_found, edit_string_not_found, etc.
        if '_' in failure_type:
            parts = failure_type.split('_')
            tool = parts[0].capitalize()
            return tool
        return 'Unknown'

    def group_by_similarity(self, failures):
        """Group failures by similarity"""
        # Group by type first
        by_type = defaultdict(list)
        for failure in failures:
            by_type[failure['type']].append(failure)

        # Calculate similarity within each group
        grouped = {}
        for failure_type, failure_list in by_type.items():
            # Extract common patterns
            details_list = [f['details'] for f in failure_list]

            # Find common substrings
            common = self._find_common_patterns(details_list)

            grouped[failure_type] = {
                'count': len(failure_list),
                'common_patterns': common,
                'samples': failure_list[:5]  # Keep 5 samples
            }

        return grouped

    def _find_common_patterns(self, strings):
        """Find common patterns in list of strings"""
        if not strings:
            return []

        # Simple approach: find words that appear in multiple strings
        word_counts = Counter()
        for s in strings:
            words = set(re.findall(r'\b\w+\b', s))
            word_counts.update(words)

        # Return words that appear in at least 30% of strings
        threshold = max(1, len(strings) * 0.3)
        common = [word for word, count in word_counts.items() if count >= threshold]

        return common

    def calculate_confidence(self, pattern_data):
        """Calculate confidence score for pattern"""
        count = pattern_data['count']

        # Confidence increases with frequency, maxes at 1.0
        if count >= 10:
            return 1.0
        elif count >= 5:
            return 0.8
        elif count >= 3:
            return 0.6
        else:
            return 0.4

    def extract_patterns(self):
        """Extract patterns from failures"""
        failures = self.load_failures()

        if not failures:
            return []

        grouped = self.group_by_similarity(failures)

        patterns = []
        for failure_type, data in grouped.items():
            tool = self.extract_tool_from_type(failure_type)

            pattern = {
                'pattern_id': failure_type.lower(),
                'failure_type': failure_type,
                'tool': tool,
                'frequency': data['count'],
                'confidence': self.calculate_confidence(data),
                'common_patterns': data['common_patterns'],
                'sample_failures': [
                    {
                        'timestamp': f['timestamp'],
                        'details': f['details']
                    }
                    for f in data['samples']
                ]
            }

            patterns.append(pattern)

        # Sort by frequency
        patterns.sort(key=lambda x: x['frequency'], reverse=True)

        return patterns

    def suggest_solutions(self, pattern):
        """Suggest solutions for a pattern"""
        suggestions = []

        failure_type = pattern['failure_type'].lower()

        # Known solution mappings
        if 'command_not_found' in failure_type:
            suggestions.append({
                'type': 'translate',
                'description': 'Translate Windows command to Unix equivalent',
                'action': 'Add command mapping to KB'
            })

        elif 'string_not_found' in failure_type:
            suggestions.append({
                'type': 'strip_prefix',
                'description': 'Remove line number prefixes',
                'action': 'Strip line number prefix before edit'
            })

        elif 'file_too_large' in failure_type:
            suggestions.append({
                'type': 'add_params',
                'description': 'Add offset/limit parameters',
                'action': 'Force offset/limit for large files'
            })

        elif 'no_matches' in failure_type:
            suggestions.append({
                'type': 'improve_pattern',
                'description': 'Pattern too specific or incorrect',
                'action': 'Review and improve search pattern'
            })

        else:
            suggestions.append({
                'type': 'manual_review',
                'description': 'Requires manual analysis',
                'action': 'Review failure details'
            })

        return suggestions

def main():
    parser = argparse.ArgumentParser(description='Failure pattern extractor')
    parser.add_argument('--extract', action='store_true', help='Extract patterns')
    parser.add_argument('--with-solutions', action='store_true', help='Include solution suggestions')
    parser.add_argument('--output', help='Output file for patterns')

    args = parser.parse_args()

    extractor = FailurePatternExtractor()

    if args.extract:
        print("Extracting failure patterns...")

        patterns = extractor.extract_patterns()

        if not patterns:
            print("No patterns found")
            return 0

        print(f"Found {len(patterns)} patterns")

        # Add solution suggestions if requested
        if args.with_solutions:
            for pattern in patterns:
                pattern['suggested_solutions'] = extractor.suggest_solutions(pattern)

        # Output
        output_data = {
            'extracted_at': Path(extractor.failures_log).stat().st_mtime if extractor.failures_log.exists() else None,
            'total_patterns': len(patterns),
            'patterns': patterns
        }

        if args.output:
            output_file = Path(args.output)
            output_file.write_text(json.dumps(output_data, indent=2))
            print(f"Patterns saved to: {output_file}")
        else:
            print(json.dumps(output_data, indent=2))

        return 0

    parser.print_help()
    return 1

if __name__ == '__main__':
    sys.exit(main())

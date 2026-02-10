#!/usr/bin/env python3
"""
Pre-Execution Optimizer
Optimizes tool parameters BEFORE execution to reduce context usage
"""

import sys
import json
import argparse
from pathlib import Path

class PreExecutionOptimizer:
    def __init__(self):
        self.max_file_lines = 500  # Max lines to read without offset/limit
        self.max_grep_results = 100  # Max grep results
        self.cache_threshold = 3  # Cache after 3 accesses

    def optimize_read(self, file_path, full_params):
        """Optimize Read tool parameters"""
        file_path_obj = Path(file_path)

        if not file_path_obj.exists():
            return full_params  # Can't optimize non-existent file

        # Get file size in lines
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                line_count = sum(1 for _ in f)
        except:
            return full_params  # Can't read file, return as-is

        # If file is large, add offset/limit
        if line_count > self.max_file_lines:
            optimized = full_params.copy()
            optimized['limit'] = self.max_file_lines
            optimized['offset'] = 0
            return {
                'optimized': optimized,
                'warning': f'File has {line_count} lines, reading first {self.max_file_lines}. Use offset to read more.',
                'total_lines': line_count
            }

        return full_params

    def optimize_grep(self, full_params):
        """Optimize Grep tool parameters"""
        optimized = full_params.copy()

        # Force head_limit if not set
        if 'head_limit' not in optimized or optimized['head_limit'] == 0:
            optimized['head_limit'] = self.max_grep_results

        # Default to files_with_matches for large searches
        if 'output_mode' not in optimized:
            optimized['output_mode'] = 'files_with_matches'

        return {
            'optimized': optimized,
            'note': f'Limited to {optimized["head_limit"]} results'
        }

    def optimize_glob(self, full_params):
        """Optimize Glob tool parameters"""
        # Glob is already efficient, just validate
        return full_params

    def optimize_bash(self, command):
        """Optimize Bash commands"""
        warnings = []
        optimized_command = command

        # Detect commands that should use dedicated tools
        if any(cmd in command for cmd in ['cat ', 'head ', 'tail ']):
            warnings.append('Consider using Read tool instead of cat/head/tail')

        if 'grep ' in command or 'rg ' in command:
            warnings.append('Consider using Grep tool instead of grep/rg')

        if 'find ' in command:
            warnings.append('Consider using Glob tool instead of find')

        # Detect piped commands that may be inefficient
        if command.count('|') > 2:
            warnings.append('Complex piped command may be inefficient')

        result = {'command': optimized_command}
        if warnings:
            result['warnings'] = warnings

        return result

    def should_use_cache(self, file_path):
        """Check if file should be cached"""
        cache_file = Path.home() / '.claude' / 'memory' / '.cache' / 'access_count.json'

        if not cache_file.exists():
            cache_file.parent.mkdir(parents=True, exist_ok=True)
            cache_file.write_text('{}')

        try:
            access_count = json.loads(cache_file.read_text())
        except:
            access_count = {}

        # Increment access count
        access_count[str(file_path)] = access_count.get(str(file_path), 0) + 1
        cache_file.write_text(json.dumps(access_count, indent=2))

        # Should cache if accessed >= threshold
        return access_count[str(file_path)] >= self.cache_threshold

    def optimize(self, tool, params):
        """Main optimization entry point"""
        if tool == 'Read':
            file_path = params.get('file_path')
            if file_path:
                # Check if should use cache
                if self.should_use_cache(file_path):
                    cache_result = self._check_cache(file_path)
                    if cache_result:
                        return {
                            'use_cache': True,
                            'cached_summary': cache_result,
                            'note': 'Using cached summary (file accessed 3+ times)'
                        }

                return self.optimize_read(file_path, params)

        elif tool == 'Grep':
            return self.optimize_grep(params)

        elif tool == 'Glob':
            return self.optimize_glob(params)

        elif tool == 'Bash':
            command = params.get('command', '')
            return self.optimize_bash(command)

        return params  # No optimization needed

    def _check_cache(self, file_path):
        """Check if file summary is cached"""
        cache_dir = Path.home() / '.claude' / 'memory' / '.cache' / 'summaries'
        cache_file = cache_dir / f'{Path(file_path).name}.json'

        if cache_file.exists():
            try:
                cached = json.loads(cache_file.read_text())
                return cached.get('summary')
            except:
                pass

        return None

def main():
    parser = argparse.ArgumentParser(description='Pre-execution optimizer')
    parser.add_argument('--tool', help='Tool name (Read/Grep/Glob/Bash)')
    parser.add_argument('--params', help='Tool parameters as JSON')
    parser.add_argument('--test-large-file', action='store_true', help='Test with large file')

    args = parser.parse_args()

    if args.test_large_file:
        # Test mode
        print("Testing pre-execution optimizer...")
        optimizer = PreExecutionOptimizer()

        # Test large file optimization
        test_params = {'file_path': __file__}
        result = optimizer.optimize('Read', test_params)
        print(f"[OK] Large file optimization: {json.dumps(result, indent=2)}")

        # Test grep optimization
        grep_params = {'pattern': 'test', 'path': '.'}
        result = optimizer.optimize('Grep', grep_params)
        print(f"[OK] Grep optimization: {json.dumps(result, indent=2)}")

        # Test bash optimization
        bash_params = {'command': 'cat file.txt | grep pattern'}
        result = optimizer.optimize('Bash', bash_params)
        print(f"[OK] Bash optimization: {json.dumps(result, indent=2)}")

        print("\n[OK] All tests passed!")
        return 0

    # Normal operation
    if not args.tool or not args.params:
        print("ERROR: --tool and --params required for normal operation", file=sys.stderr)
        return 1

    try:
        params = json.loads(args.params)
    except:
        print(f"ERROR: Invalid JSON params: {args.params}", file=sys.stderr)
        return 1

    optimizer = PreExecutionOptimizer()
    result = optimizer.optimize(args.tool, params)

    print(json.dumps(result, indent=2))
    return 0

if __name__ == '__main__':
    sys.exit(main())

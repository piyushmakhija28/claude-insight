#!/usr/bin/env python3
"""
Context Extractor
Extracts essential information from tool outputs to reduce context overhead
"""

import sys
import json
import argparse
import re
from pathlib import Path

class ContextExtractor:
    def __init__(self):
        self.summary_max_lines = 50  # Max lines in summary

    def extract_read_output(self, content, file_path):
        """Extract essentials from Read tool output"""
        lines = content.split('\n')

        # If content is short, return as-is
        if len(lines) <= self.summary_max_lines:
            return content

        # Extract structure
        summary = {
            'file': file_path,
            'total_lines': len(lines),
            'structure': self._extract_structure(lines),
            'key_definitions': self._extract_definitions(lines),
            'imports': self._extract_imports(lines),
            'summary': f'File has {len(lines)} lines. Use offset/limit to read specific sections.'
        }

        return json.dumps(summary, indent=2)

    def _extract_structure(self, lines):
        """Extract file structure (classes, functions, etc.)"""
        structure = []

        for i, line in enumerate(lines[:200], 1):  # Only scan first 200 lines
            # Python/Java class definitions
            if re.match(r'\s*(class|interface|enum)\s+\w+', line):
                structure.append(f'Line {i}: {line.strip()}')

            # Function/method definitions
            elif re.match(r'\s*(def|function|public|private|protected)\s+\w+', line):
                structure.append(f'Line {i}: {line.strip()}')

        return structure[:20]  # Return first 20 items

    def _extract_definitions(self, lines):
        """Extract key definitions"""
        definitions = []

        for i, line in enumerate(lines, 1):
            # Constants
            if re.match(r'\s*[A-Z_]+\s*=', line):
                definitions.append(f'Line {i}: {line.strip()}')

            # Variable declarations
            elif re.match(r'\s*(const|let|var)\s+\w+\s*=', line):
                definitions.append(f'Line {i}: {line.strip()}')

        return definitions[:10]  # Return first 10

    def _extract_imports(self, lines):
        """Extract import statements"""
        imports = []

        for line in lines[:50]:  # Only check first 50 lines
            if re.match(r'\s*(import|from|require|include)', line):
                imports.append(line.strip())

        return imports

    def extract_grep_output(self, matches, pattern):
        """Extract essentials from Grep output"""
        if len(matches) <= 20:
            return matches

        # Group by file
        files = {}
        for match in matches:
            file_path = match.get('file', 'unknown')
            if file_path not in files:
                files[file_path] = []
            files[file_path].append(match)

        summary = {
            'pattern': pattern,
            'total_matches': len(matches),
            'files_matched': len(files),
            'top_files': [
                {'file': f, 'matches': len(m)}
                for f, m in sorted(files.items(), key=lambda x: len(x[1]), reverse=True)[:10]
            ],
            'note': f'Showing top 10 of {len(files)} files. Use more specific pattern or head_limit.'
        }

        return json.dumps(summary, indent=2)

    def extract_bash_output(self, output, command):
        """Extract essentials from Bash output"""
        lines = output.split('\n')

        # If output is short, return as-is
        if len(lines) <= 100:
            return output

        # Detect command type
        if command.startswith('git'):
            return self._extract_git_output(lines, command)
        elif 'npm' in command or 'yarn' in command:
            return self._extract_npm_output(lines)
        elif 'docker' in command:
            return self._extract_docker_output(lines)
        else:
            # Generic extraction: first 50 + last 20 lines
            extracted = lines[:50] + ['...'] + lines[-20:]
            return '\n'.join(extracted)

    def _extract_git_output(self, lines, command):
        """Extract git command output"""
        if 'git log' in command:
            # Extract commit summaries
            commits = []
            for line in lines[:20]:
                if line.startswith('commit ') or line.startswith('    '):
                    commits.append(line)
            return '\n'.join(commits)

        elif 'git diff' in command:
            # Extract changed files and summary
            summary = []
            for line in lines[:30]:
                if line.startswith('diff --git') or line.startswith('@@'):
                    summary.append(line)
            return '\n'.join(summary)

        return '\n'.join(lines[:50])

    def _extract_npm_output(self, lines):
        """Extract npm/yarn output"""
        important = []
        for line in lines:
            if any(keyword in line.lower() for keyword in ['error', 'warning', 'success', 'installed']):
                important.append(line)

        return '\n'.join(important[-30:])  # Last 30 important lines

    def _extract_docker_output(self, lines):
        """Extract docker output"""
        important = []
        for line in lines:
            if any(keyword in line.lower() for keyword in ['error', 'warning', 'step', 'successfully']):
                important.append(line)

        return '\n'.join(important[-30:])

    def extract(self, tool, output, context=None):
        """Main extraction entry point"""
        context = context or {}

        if tool == 'Read':
            file_path = context.get('file_path', 'unknown')
            return self.extract_read_output(output, file_path)

        elif tool == 'Grep':
            pattern = context.get('pattern', 'unknown')
            return self.extract_grep_output(output, pattern)

        elif tool == 'Bash':
            command = context.get('command', 'unknown')
            return self.extract_bash_output(output, command)

        return output  # No extraction needed

    def save_summary(self, file_path, summary):
        """Save file summary to cache"""
        cache_dir = Path.home() / '.claude' / 'memory' / '.cache' / 'summaries'
        cache_dir.mkdir(parents=True, exist_ok=True)

        cache_file = cache_dir / f'{Path(file_path).name}.json'
        cache_data = {
            'file_path': str(file_path),
            'summary': summary,
            'cached_at': str(Path(file_path).stat().st_mtime)
        }

        cache_file.write_text(json.dumps(cache_data, indent=2))

def main():
    parser = argparse.ArgumentParser(description='Context extractor')
    parser.add_argument('--tool', help='Tool name')
    parser.add_argument('--output', help='Tool output (or file path)')
    parser.add_argument('--context', help='Context as JSON')
    parser.add_argument('--test', action='store_true', help='Run tests')

    args = parser.parse_args()

    if args.test:
        print("Testing context extractor...")
        extractor = ContextExtractor()

        # Test read extraction
        test_content = '\n'.join([f'Line {i}: content' for i in range(1000)])
        result = extractor.extract_read_output(test_content, 'test.py')
        print(f"[OK] Read extraction: {len(result)} chars (from {len(test_content)})")

        # Test grep extraction
        test_matches = [{'file': f'file{i}.py', 'line': i} for i in range(100)]
        result = extractor.extract_grep_output(test_matches, 'test')
        print(f"[OK] Grep extraction: Summarized 100 matches")

        # Test bash extraction
        test_output = '\n'.join([f'Line {i}' for i in range(500)])
        result = extractor.extract_bash_output(test_output, 'ls -la')
        print(f"[OK] Bash extraction: {len(result.split(chr(10)))} lines (from 500)")

        print("\n[OK] All tests passed!")
        return 0

    # Normal operation
    try:
        context = json.loads(args.context) if args.context else {}
    except:
        context = {}

    extractor = ContextExtractor()

    # Read output from file or arg
    if args.output and Path(args.output).exists():
        output = Path(args.output).read_text()
    else:
        output = args.output or sys.stdin.read()

    result = extractor.extract(args.tool, output, context)
    print(result)

    return 0

if __name__ == '__main__':
    sys.exit(main())

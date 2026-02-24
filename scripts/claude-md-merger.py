#!/usr/bin/env python
"""
CLAUDE.MD MERGER v1.0.0
=======================

Merges global and project-specific CLAUDE.md files.

Rule: Global CLAUDE.md is NEVER overridden, only enhanced with project info.

Usage:
    python claude-md-merger.py --project-path /path/to/project
"""

# Fix encoding for Windows console
import sys
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    try:
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        import io
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


import os
import json
import re
from pathlib import Path
from datetime import datetime

class ClaudeMdMerger:
    """Merges global and project CLAUDE.md files"""

    def __init__(self):
        self.global_claude_md = Path.home() / '.claude' / 'CLAUDE.md'
        self.merge_log = Path.home() / '.claude' / 'memory' / 'logs' / 'claude-md-merge.log'

    def find_project_claude_md(self, project_path):
        """Find project CLAUDE.md file"""
        project_path = Path(project_path)

        # Check common locations
        possible_locations = [
            project_path / 'CLAUDE.md',
            project_path / 'claude.md',
            project_path / '.claude' / 'CLAUDE.md',
            project_path / 'docs' / 'CLAUDE.md'
        ]

        for location in possible_locations:
            if location.exists():
                return location

        return None

    def extract_project_specifics(self, project_md_content):
        """Extract ONLY project-specific information (no policy overrides)"""

        project_info = {
            'project_name': None,
            'project_description': None,
            'tech_stack': [],
            'file_paths': {},
            'conventions': [],
            'additional_rules': [],
            'documentation_links': [],
            'raw_content': project_md_content
        }

        lines = project_md_content.split('\n')

        # Extract project-specific markers
        project_section = False
        for line in lines:
            # Look for project-specific sections
            if re.match(r'##?\s+(Project|About|Tech Stack|Structure|Paths)', line, re.IGNORECASE):
                project_section = True

            # Skip policy/enforcement sections (these are global-only)
            if re.match(r'##?\s+(Policy|Enforcement|Zero-Tolerance|Auto-Fix|Session)', line, re.IGNORECASE):
                project_section = False

            # Extract project name
            if 'project name' in line.lower() or 'project:' in line.lower():
                match = re.search(r':\s*(.+)', line)
                if match:
                    project_info['project_name'] = match.group(1).strip()

            # Extract tech stack
            if 'tech stack' in line.lower() or 'technologies' in line.lower():
                match = re.search(r':\s*(.+)', line)
                if match:
                    tech_items = match.group(1).split(',')
                    project_info['tech_stack'].extend([t.strip() for t in tech_items])

        return project_info

    def detect_override_attempts(self, project_md_content):
        """Detect if project CLAUDE.md tries to override global policies"""

        override_attempts = []

        # Keywords that indicate override attempts
        forbidden_keywords = [
            'disable.*zero-tolerance',
            'skip.*auto-fix',
            'ignore.*session.*id',
            'override.*global',
            'disable.*enforcement',
            'skip.*policies',
            'no.*blocking',
            'disable.*mandatory'
        ]

        lines = project_md_content.split('\n')

        for i, line in enumerate(lines, 1):
            for keyword in forbidden_keywords:
                if re.search(keyword, line, re.IGNORECASE):
                    override_attempts.append({
                        'line': i,
                        'content': line.strip(),
                        'keyword': keyword
                    })

        return override_attempts

    def merge_configs(self, project_path):
        """Merge global and project CLAUDE.md"""

        # Step 1: Load global CLAUDE.md (MANDATORY)
        if not self.global_claude_md.exists():
            print("[CROSS] ERROR: Global CLAUDE.md not found!")
            print(f"   Expected: {self.global_claude_md}")
            return None

        with open(self.global_claude_md, 'r', encoding='utf-8') as f:
            global_content = f.read()

        # Step 2: Find project CLAUDE.md
        project_claude_md = self.find_project_claude_md(project_path)

        if not project_claude_md:
            print("[INFO]  No project CLAUDE.md found")
            print("[CHECK] Using global CLAUDE.md only")
            return {
                'type': 'global_only',
                'global_content': global_content,
                'project_content': None,
                'merged_content': global_content,
                'project_info': None,
                'override_attempts': []
            }

        # Step 3: Load project CLAUDE.md
        with open(project_claude_md, 'r', encoding='utf-8') as f:
            project_content = f.read()

        # Step 4: Extract project-specific info
        project_info = self.extract_project_specifics(project_content)

        # Step 5: Detect override attempts
        override_attempts = self.detect_override_attempts(project_content)

        # Step 6: Create merged content
        merged_content = self._create_merged_content(
            global_content,
            project_info,
            override_attempts
        )

        # Log merge
        self._log_merge(project_path, project_claude_md, override_attempts)

        return {
            'type': 'merged',
            'global_content': global_content,
            'project_content': project_content,
            'merged_content': merged_content,
            'project_info': project_info,
            'override_attempts': override_attempts,
            'global_file': str(self.global_claude_md),
            'project_file': str(project_claude_md)
        }

    def _create_merged_content(self, global_content, project_info, override_attempts):
        """Create merged configuration text"""

        merged = global_content

        # Add project-specific section at the end
        project_section = "\n\n---\n\n"
        project_section += "## [U+1F4C2] PROJECT-SPECIFIC CONFIGURATION\n\n"
        project_section += "**Added from project CLAUDE.md (additional context only)**\n\n"

        if project_info.get('project_name'):
            project_section += f"**Project Name:** {project_info['project_name']}\n\n"

        if project_info.get('tech_stack'):
            project_section += "**Tech Stack:**\n"
            for tech in project_info['tech_stack']:
                project_section += f"- {tech}\n"
            project_section += "\n"

        if project_info.get('conventions'):
            project_section += "**Project Conventions:**\n"
            for conv in project_info['conventions']:
                project_section += f"- {conv}\n"
            project_section += "\n"

        if override_attempts:
            project_section += "\n**[WARNING] Override Attempts Detected (IGNORED):**\n"
            for attempt in override_attempts:
                project_section += f"- Line {attempt['line']}: {attempt['content'][:100]}\n"
            project_section += "\n**All override attempts ignored. Global policies remain active.**\n\n"

        project_section += "**[LOCK] Global Policies:** UNCHANGED (always enforced)\n"
        project_section += "**[U+1F4C2] Project Info:** MERGED (additional context added)\n"

        merged += project_section

        return merged

    def _log_merge(self, project_path, project_file, override_attempts):
        """Log merge event"""

        self.merge_log.parent.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().isoformat()
        log_line = f"{timestamp} | MERGE | Project: {project_path} | "
        log_line += f"Project File: {project_file} | "
        log_line += f"Override Attempts: {len(override_attempts)}\n"

        with open(self.merge_log, 'a') as f:
            f.write(log_line)

    def display_merge_report(self, merge_result):
        """Display merge report"""

        if not merge_result:
            return

        print("\n" + "="*80)
        print("[CLIPBOARD] CLAUDE.MD MERGE REPORT")
        print("="*80 + "\n")

        if merge_result['type'] == 'global_only':
            print("[CHECK] Configuration: Global CLAUDE.md ONLY")
            print(f"[U+1F4C1] Global File: {self.global_claude_md}")
            print("[INFO]  No project CLAUDE.md found")
            print("\n[LOCK] All global policies: ACTIVE")

        else:  # merged
            print("[CHECK] Configuration: MERGED (Global + Project)")
            print(f"[U+1F4C1] Global File: {merge_result['global_file']}")
            print(f"[U+1F4C1] Project File: {merge_result['project_file']}")

            print("\n[LOCK] Global Policies: ENFORCED (unchanged)")
            print("   - Zero-Tolerance Failure Policy")
            print("   - Auto-Fix Enforcement")
            print("   - Session ID Tracking")
            print("   - All enforcement policies ACTIVE")

            project_info = merge_result['project_info']
            if project_info:
                print("\n[U+1F4C2] Project Context: ADDED")
                if project_info.get('project_name'):
                    print(f"   - Project: {project_info['project_name']}")
                if project_info.get('tech_stack'):
                    print(f"   - Tech Stack: {', '.join(project_info['tech_stack'])}")

            if merge_result['override_attempts']:
                print(f"\n[WARNING]  Override Attempts: {len(merge_result['override_attempts'])} DETECTED & IGNORED")
                for attempt in merge_result['override_attempts'][:5]:  # Show first 5
                    print(f"   - Line {attempt['line']}: {attempt['content'][:80]}")
                if len(merge_result['override_attempts']) > 5:
                    remaining = len(merge_result['override_attempts']) - 5
                    print(f"   - ... and {remaining} more")
                print("\n   [CHECK] All override attempts IGNORED")
                print("   [CHECK] Global policies REMAIN ACTIVE")

        print("\n" + "="*80)
        print("[CHECK] MERGE COMPLETE - Global policies unchanged, project context enhanced")
        print("="*80 + "\n")


def main():
    """Main function"""
    import sys
    import argparse

    parser = argparse.ArgumentParser(description='CLAUDE.md Merger')
    parser.add_argument('--project-path', required=True,
                       help='Path to project directory')
    parser.add_argument('--output', help='Output merged config to file')
    parser.add_argument('--json', action='store_true',
                       help='Output as JSON')

    args = parser.parse_args()

    merger = ClaudeMdMerger()
    result = merger.merge_configs(args.project_path)

    if not result:
        sys.exit(1)

    if args.json:
        # Output as JSON (excluding full content for brevity)
        json_output = {
            'type': result['type'],
            'project_info': result.get('project_info'),
            'override_attempts': result.get('override_attempts', []),
            'global_file': result.get('global_file'),
            'project_file': result.get('project_file')
        }
        print(json.dumps(json_output, indent=2))
    else:
        merger.display_merge_report(result)

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(result['merged_content'])
        print(f"\n[CHECK] Merged config saved to: {args.output}")


if __name__ == '__main__':
    main()

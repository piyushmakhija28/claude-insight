#!/usr/bin/env python
"""
CLAUDE INSIGHT SYNC ELIGIBILITY DETECTOR

Automatically detects if a file/skill/agent should be synced to Claude Insight
based on whether it's GLOBAL/REUSABLE vs PROJECT-SPECIFIC.

Usage:
    python detect-sync-eligibility.py --file "path/to/file"
    python detect-sync-eligibility.py --skill "skill-name"
    python detect-sync-eligibility.py --agent "agent-name"

Output:
    ✅ SYNC: This is global/reusable
    ❌ NO SYNC: This is project-specific (reason)
    ⚠️  WARNING: Contains project-specific references (needs cleanup)

Exit Codes:
    0 = SYNC (eligible)
    1 = NO SYNC (project-specific)
    2 = WARNING (needs manual review/cleanup)
"""

import sys
import os
import re
from pathlib import Path

# Fix encoding
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Project-specific keywords that indicate NO SYNC
PROJECT_KEYWORDS = [
    'surgricalswale',
    'surgical swale',
    'techdeveloper',
    'tech developer',
    'piyushmakhija',
    'piyush makhija',
]

# Sensitive patterns that indicate NO SYNC
SENSITIVE_PATTERNS = [
    r'password\s*=',
    r'api[_-]?key\s*=',
    r'secret\s*=',
    r'token\s*=',
    r'\.env',
    r'jdbc:.*@',  # Database connection strings
    r'https?://.*techdeveloper\.in',
    r'https?://.*surgricalswale\.in',
    r'GLOBAL-CLAUDE-MD-DO-NOT-SYNC',  # Global CLAUDE.md marker
    r'C:\\Users\\techd',  # Personal paths
    r'/Users/techd',  # Personal paths (Unix)
]

# Paths that indicate project-specific code (NO SYNC)
PROJECT_PATHS = [
    'surgricalswale',
    'techdeveloper/backend',
    'workspace-spring-tool-suite',
]

# Manual override markers
SYNC_MARKER = '# CLAUDE-INSIGHT: SYNC'
NO_SYNC_MARKER = '# CLAUDE-INSIGHT: NO-SYNC'


class SyncEligibilityDetector:
    """Detects if content should be synced to Claude Insight"""

    def __init__(self, file_path=None, skill_name=None, agent_name=None):
        self.file_path = file_path
        self.skill_name = skill_name
        self.agent_name = agent_name
        self.issues = []
        self.warnings = []
        self.eligible = True

    def detect(self):
        """Run all detection checks"""

        # Determine file path
        if self.skill_name:
            self.file_path = Path.home() / '.claude' / 'skills' / self.skill_name / 'skill.md'
        elif self.agent_name:
            self.file_path = Path.home() / '.claude' / 'agents' / self.agent_name / 'agent.md'

        if not self.file_path:
            print("❌ ERROR: No file, skill, or agent specified")
            return 1

        file_path = Path(self.file_path)

        if not file_path.exists():
            print(f"❌ ERROR: File not found: {file_path}")
            return 1

        # 🚨 CRITICAL: Block global CLAUDE.md (NEVER sync personal config)
        if file_path.name == 'CLAUDE.md':
            # Check if it's the global CLAUDE.md in ~/.claude/
            if str(file_path.parent).endswith('.claude') or '/.claude' in str(file_path) or '\\.claude\\' in str(file_path):
                print(f"❌ NO SYNC: This is the GLOBAL CLAUDE.md (personal configuration)")
                print(f"   File: {file_path}")
                print(f"   Reason: Global CLAUDE.md contains personal settings and should NEVER be synced to public repos")
                print(f"   Action: Create project-specific CLAUDE.md instead for each public repo")
                return 1

        # Read file content
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"❌ ERROR: Cannot read file: {e}")
            return 1

        # Check for manual override
        if SYNC_MARKER in content:
            print(f"✅ SYNC: Manual override marker found")
            print(f"   File: {file_path}")
            return 0

        if NO_SYNC_MARKER in content:
            print(f"❌ NO SYNC: Manual override marker found")
            print(f"   File: {file_path}")
            return 1

        # Run detection checks
        self._check_name(file_path)
        self._check_path(file_path)
        self._check_content(content)
        self._check_sensitive_patterns(content)

        # Determine result
        return self._get_result()

    def _check_name(self, file_path):
        """Check if name contains project-specific terms"""
        name = file_path.stem.lower()

        for keyword in PROJECT_KEYWORDS:
            if keyword.lower() in name:
                self.eligible = False
                self.issues.append(f"Name contains '{keyword}' (project-specific)")
                return

    def _check_path(self, file_path):
        """Check if path indicates project-specific code"""
        path_str = str(file_path).lower()

        for proj_path in PROJECT_PATHS:
            if proj_path.lower() in path_str:
                # Check if it's in project source code (not .claude directory)
                if '/.claude/' not in path_str and '\\.claude\\' not in path_str:
                    self.eligible = False
                    self.issues.append(f"Path contains '{proj_path}' (project source code)")
                    return

    def _check_content(self, content):
        """Check content for project-specific references"""
        content_lower = content.lower()

        for keyword in PROJECT_KEYWORDS:
            if keyword.lower() in content_lower:
                # Count occurrences
                count = content_lower.count(keyword.lower())

                if count > 3:
                    # Too many references - likely project-specific
                    self.eligible = False
                    self.issues.append(f"Content contains '{keyword}' {count} times (project-specific)")
                else:
                    # Few references - might be just examples
                    self.warnings.append(f"Content contains '{keyword}' {count} time(s) (check if just examples)")

    def _check_sensitive_patterns(self, content):
        """Check for sensitive/secret patterns"""
        for pattern in SENSITIVE_PATTERNS:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                self.eligible = False
                self.issues.append(f"Contains sensitive pattern: {pattern}")
                return

    def _get_result(self):
        """Determine final result and print output"""

        if not self.eligible:
            # NOT eligible - project-specific
            print("❌ NO SYNC: This is project-specific")
            print()
            print("Reasons:")
            for issue in self.issues:
                print(f"   - {issue}")
            print()
            print("Action: Do NOT sync to Claude Insight")
            return 1

        elif self.warnings:
            # Eligible but has warnings - needs review
            print("⚠️  WARNING: Contains project-specific references")
            print()
            print("Warnings:")
            for warning in self.warnings:
                print(f"   - {warning}")
            print()
            print("Recommendation:")
            print("   1. Review the file")
            print("   2. Replace project-specific examples with generic examples")
            print("   3. Then sync to Claude Insight")
            return 2

        else:
            # Fully eligible - no issues
            print("✅ SYNC: This is global/reusable")
            print()
            print("Checks:")
            print("   ✅ Name: No project-specific terms")
            print("   ✅ Path: Not in project source code")
            print("   ✅ Content: No project-specific business logic")
            print("   ✅ Security: No sensitive information")
            print()
            print("Action: Safe to sync to Claude Insight")
            return 0


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Detect if content should be synced to Claude Insight')
    parser.add_argument('--file', help='File path to check')
    parser.add_argument('--skill', help='Skill name to check')
    parser.add_argument('--agent', help='Agent name to check')

    args = parser.parse_args()

    if not any([args.file, args.skill, args.agent]):
        print("❌ ERROR: Must specify --file, --skill, or --agent")
        print()
        print("Usage:")
        print("  python detect-sync-eligibility.py --file 'path/to/file'")
        print("  python detect-sync-eligibility.py --skill 'skill-name'")
        print("  python detect-sync-eligibility.py --agent 'agent-name'")
        return 1

    detector = SyncEligibilityDetector(
        file_path=args.file,
        skill_name=args.skill,
        agent_name=args.agent
    )

    return detector.detect()


if __name__ == '__main__':
    sys.exit(main())

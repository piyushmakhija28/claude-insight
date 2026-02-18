#!/usr/bin/env python3
"""
Auto-Sync Policies from Global Memory System to Claude Insight

This script:
1. Scans ~/.claude/memory for all policy files
2. Detects 3-Level Architecture policies
3. Auto-generates PolicyChecker code with correct paths
4. Handles path differences between global and local systems
"""

import os
import sys
from pathlib import Path
import json

# Color codes for terminal
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

def find_policy_files(memory_dir):
    """Scan memory directory for policy files"""
    print(f"{Colors.BLUE}[1/4] Scanning global memory system...{Colors.RESET}")

    policy_files = {
        # Level -1: Auto-Fix Enforcement
        'auto-fix-enforcement': [
            'auto-fix-enforcer.sh',
            'blocking-policy-enforcer.py'
        ],

        # Level 1: Sync System
        'context-management': [
            '01-sync-system/context-management/context-monitor-v2.py'
        ],
        'session-management': [
            'session-id-generator.py'
        ],

        # Level 2: Standards System
        'standards-loader': [
            '02-standards-system/standards-loader.py'
        ],

        # Level 3: Execution System (12 Steps)
        'prompt-generation': [
            '03-execution-system/00-prompt-generation/prompt-generator.py'
        ],
        'task-breakdown': [
            '03-execution-system/01-task-breakdown/task-auto-analyzer.py'
        ],
        'plan-mode-suggestion': [
            '03-execution-system/02-plan-mode/auto-plan-mode-suggester.py'
        ],
        'model-selection': [
            '03-execution-system/04-model-selection/model-auto-selector.py'
        ],
        'skill-agent-selection': [
            '03-execution-system/05-skill-agent-selection/auto-skill-agent-selector.py'
        ],
        'tool-optimization': [
            '03-execution-system/06-tool-optimization/pre-execution-optimizer.py'
        ],
        'failure-prevention': [
            '03-execution-system/failure-prevention/pre-execution-checker.py'
        ],
        'parallel-execution': [
            'scripts/auto-parallel-detector.py'
        ],
        'git-auto-commit': [
            '03-execution-system/09-git-commit/auto-commit-enforcer.py'
        ],

    }

    found_policies = {}
    missing_policies = {}

    for policy_id, files in policy_files.items():
        found_files = []
        missing_files = []

        for file_path in files:
            full_path = memory_dir / file_path
            if full_path.exists():
                found_files.append(file_path)
            else:
                missing_files.append(file_path)

        if found_files:
            found_policies[policy_id] = found_files
            if missing_files:
                print(f"  {Colors.YELLOW}[PARTIAL] {policy_id}: {len(found_files)}/{len(files)} files{Colors.RESET}")
        else:
            missing_policies[policy_id] = missing_files
            print(f"  {Colors.RED}[MISSING] {policy_id}: No files found{Colors.RESET}")

    print(f"\n  {Colors.GREEN}Found: {len(found_policies)} policies{Colors.RESET}")
    print(f"  {Colors.RED}Missing: {len(missing_policies)} policies{Colors.RESET}")

    return found_policies

def generate_policy_definitions(found_policies):
    """Generate Python code for PolicyChecker"""
    print(f"\n{Colors.BLUE}[2/4] Generating policy definitions...{Colors.RESET}")

    policy_metadata = {
        'auto-fix-enforcement': {
            'name': 'Auto-Fix Enforcement',
            'description': 'Zero-Tolerance blocking enforcement - checks all systems',
            'phase': -1,
            'level': 'LEVEL -1'
        },
        'context-management': {
            'name': 'Context Management',
            'description': 'Proactive context optimization (-30 to -50% usage)',
            'phase': 1,
            'level': 'LEVEL 1'
        },
        'session-management': {
            'name': 'Session Management',
            'description': 'Session ID tracking and state management',
            'phase': 1,
            'level': 'LEVEL 1'
        },
        'standards-loader': {
            'name': 'Standards Loader',
            'description': '13 coding standards with 77+ rules enforcement',
            'phase': 2,
            'level': 'LEVEL 2'
        },
        'prompt-generation': {
            'name': 'Prompt Generation',
            'description': 'Anti-hallucination verified prompt generation (Step 0)',
            'phase': 0,
            'level': 'LEVEL 3'
        },
        'task-breakdown': {
            'name': 'Task Breakdown',
            'description': 'Automatic task and phase breakdown (Step 1)',
            'phase': 1,
            'level': 'LEVEL 3'
        },
        'plan-mode-suggestion': {
            'name': 'Plan Mode Suggestion',
            'description': 'Auto plan mode detection based on complexity (Step 2)',
            'phase': 2,
            'level': 'LEVEL 3'
        },
        'model-selection': {
            'name': 'Model Selection',
            'description': 'Intelligent model selection - Haiku/Sonnet/Opus (Step 4)',
            'phase': 4,
            'level': 'LEVEL 3'
        },
        'skill-agent-selection': {
            'name': 'Skill & Agent Selection',
            'description': 'Auto skill and agent recommendation (Step 5)',
            'phase': 5,
            'level': 'LEVEL 3'
        },
        'tool-optimization': {
            'name': 'Tool Optimization',
            'description': 'Tool usage optimization - offset/limit/head_limit (Step 6)',
            'phase': 6,
            'level': 'LEVEL 3'
        },
        'failure-prevention': {
            'name': 'Failure Prevention',
            'description': 'Pre-execution checks and auto-fixes (Step 7)',
            'phase': 7,
            'level': 'LEVEL 3'
        },
        'parallel-execution': {
            'name': 'Parallel Execution',
            'description': 'Auto-detect parallel task execution opportunities (Step 8)',
            'phase': 8,
            'level': 'LEVEL 3'
        },
        'git-auto-commit': {
            'name': 'Git Auto-Commit',
            'description': 'Auto-commit on phase completion (Step 11)',
            'phase': 11,
            'level': 'LEVEL 3'
        },
        'daemon-infrastructure': {
            'name': 'Daemon Infrastructure',
            'description': 'Cross-platform daemon management (10 core daemons)',
            'phase': 2,
            'level': 'Infrastructure'
        }
    }

    policy_list = []

    for policy_id, files in sorted(found_policies.items(), key=lambda x: policy_metadata.get(x[0], {}).get('phase', 999)):
        meta = policy_metadata.get(policy_id, {
            'name': policy_id.replace('-', ' ').title(),
            'description': 'Auto-detected policy',
            'phase': 0,
            'level': 'Unknown'
        })

        policy_def = f"""            {{
                'id': '{policy_id}',
                'name': '{meta['name']}',
                'description': '{meta['description']}',
                'files': {files},
                'phase': {meta['phase']},
                'level': '{meta['level']}'
            }}"""

        policy_list.append(policy_def)
        print(f"  {Colors.GREEN}[OK] {meta['name']}{Colors.RESET}")

    return ',\n'.join(policy_list)

def update_policy_checker(policy_definitions):
    """Update PolicyChecker with new policy definitions"""
    print(f"\n{Colors.BLUE}[3/4] Updating PolicyChecker...{Colors.RESET}")

    policy_checker_path = Path(__file__).parent.parent / 'src' / 'services' / 'monitoring' / 'policy_checker.py'

    if not policy_checker_path.exists():
        print(f"  {Colors.RED}[ERROR] PolicyChecker not found: {policy_checker_path}{Colors.RESET}")
        return False

    # Read current file
    with open(policy_checker_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find the policies list and replace it
    start_marker = "# 3-Level Architecture Policies"
    end_marker = "        ]"

    start_idx = content.find(start_marker)
    if start_idx == -1:
        print(f"  {Colors.RED}[ERROR] Start marker not found in PolicyChecker{Colors.RESET}")
        return False

    # Find the end of the policies list
    end_idx = content.find(end_marker, start_idx)
    if end_idx == -1:
        print(f"  {Colors.RED}[ERROR] End marker not found in PolicyChecker{Colors.RESET}")
        return False

    # Build new content
    new_policies_section = f"""# 3-Level Architecture Policies (v3.2.0) - Auto-generated
        self.policies = [
{policy_definitions}
        ]"""

    new_content = content[:start_idx] + new_policies_section + content[end_idx + len(end_marker):]

    # Backup original
    backup_path = policy_checker_path.with_suffix('.py.backup')
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)

    # Write new content
    with open(policy_checker_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f"  {Colors.GREEN}[OK] PolicyChecker updated{Colors.RESET}")
    print(f"  {Colors.YELLOW}[BACKUP] Original saved: {backup_path.name}{Colors.RESET}")

    return True

def verify_sync():
    """Verify the sync worked by testing PolicyChecker"""
    print(f"\n{Colors.BLUE}[4/4] Verifying sync...{Colors.RESET}")

    try:
        # Add src to path
        sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
        from services.monitoring.policy_checker import PolicyChecker

        checker = PolicyChecker()
        total = len(checker.policies)

        # Get detailed status
        statuses = checker.get_all_policies_status()
        active = sum(1 for p in statuses if p['status'] == 'active')
        error = sum(1 for p in statuses if p['status'] == 'error')
        warning = sum(1 for p in statuses if p['status'] == 'warning')

        print(f"\n  {Colors.GREEN}Total Policies: {total}{Colors.RESET}")
        print(f"  {Colors.GREEN}Active: {active}{Colors.RESET}")
        if warning > 0:
            print(f"  {Colors.YELLOW}Warning: {warning}{Colors.RESET}")
        if error > 0:
            print(f"  {Colors.RED}Error: {error}{Colors.RESET}")

        return True

    except Exception as e:
        print(f"  {Colors.RED}[ERROR] Verification failed: {e}{Colors.RESET}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("="*80)
    print(f"{Colors.GREEN}Auto-Sync Policies from Global Memory System{Colors.RESET}")
    print("="*80)
    print()

    # Check if global memory exists
    memory_dir = Path.home() / '.claude' / 'memory'

    if not memory_dir.exists():
        print(f"{Colors.RED}[ERROR] Global memory system not found: {memory_dir}{Colors.RESET}")
        print(f"{Colors.YELLOW}[INFO] Claude Insight will use local mode{Colors.RESET}")
        return 1

    print(f"  {Colors.GREEN}Memory System: {memory_dir}{Colors.RESET}")
    print()

    # Step 1: Find policies
    found_policies = find_policy_files(memory_dir)

    if not found_policies:
        print(f"\n{Colors.RED}[ERROR] No policies found to sync{Colors.RESET}")
        return 1

    # Step 2: Generate definitions
    policy_definitions = generate_policy_definitions(found_policies)

    # Step 3: Update PolicyChecker
    if not update_policy_checker(policy_definitions):
        return 1

    # Step 4: Verify
    if not verify_sync():
        return 1

    print()
    print("="*80)
    print(f"{Colors.GREEN}[SUCCESS] Policies synced successfully!{Colors.RESET}")
    print("="*80)
    print()
    print(f"{Colors.YELLOW}Next steps:{Colors.RESET}")
    print(f"  1. Restart Flask app: python src/app.py")
    print(f"  2. Check dashboard for updated policy count")
    print()

    return 0

if __name__ == '__main__':
    sys.exit(main())

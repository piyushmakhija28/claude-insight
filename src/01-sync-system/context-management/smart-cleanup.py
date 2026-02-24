#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Smart Context Cleanup
Policy-based context cleanup with session memory protection

Usage:
    python smart-cleanup.py [--level LEVEL] [--project PROJECT]

Levels:
    light      - Remove old file reads, MCP responses (70-84% context)
    moderate   - Compress completed work (85-89% context)
    aggressive - Keep only essentials (90%+ context)

Examples:
    python smart-cleanup.py --level light --project my-app
    python smart-cleanup.py --level aggressive
"""

import sys
import os
import argparse
import json
from datetime import datetime
from pathlib import Path

# Fix Windows encoding issues
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Protected directories (NEVER cleanup!)
PROTECTED_PATHS = [
    "~/.claude/memory/sessions/",
    "~/.claude/memory/logs/",
    "~/.claude/memory/*.md",
    "~/.claude/settings*.json",
    "~/.claude/*.md",
]

def log_policy_hit(action, context):
    """Log policy execution"""
    log_file = os.path.expanduser("~/.claude/memory/logs/policy-hits.log")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] context-cleanup | {action} | {context}\n"

    try:
        with open(log_file, 'a') as f:
            f.write(log_entry)
    except Exception as e:
        print(f"Warning: Could not write to log: {e}", file=sys.stderr)

def get_cleanup_strategy(level):
    """
    Get cleanup strategy based on level

    Returns dict with:
    - what_to_keep: List of items to preserve
    - what_to_remove: List of items to cleanup
    - save_before_cleanup: Items to save to session memory first
    """

    strategies = {
        "light": {
            "description": "Light Cleanup (70-84% context)",
            "what_to_keep": [
                "[CHECK] All session memory files (PROTECTED)",
                "[CHECK] User preferences & learned patterns",
                "[CHECK] Active task context",
                "[CHECK] Recent decisions (last 5-10 prompts)",
                "[CHECK] Architecture notes",
                "[CHECK] Files currently being worked on",
                "[CHECK] Pending work / next steps",
            ],
            "what_to_remove": [
                "[CROSS] Old file reads (15+ prompts ago, not actively used)",
                "[CROSS] Processed MCP responses (data already extracted)",
                "[CROSS] Redundant information (repeated content)",
                "[CROSS] Exploratory searches (if target already found)",
            ],
            "save_before_cleanup": [
                "[FLOPPY] Important decisions from old prompts",
                "[FLOPPY] User-stated preferences not yet saved",
            ],
            "compaction": "20% reduction",
        },

        "moderate": {
            "description": "Moderate Cleanup (85-89% context)",
            "what_to_keep": [
                "[CHECK] All session memory files (PROTECTED)",
                "[CHECK] User preferences & learned patterns",
                "[CHECK] Current task context only",
                "[CHECK] Key decisions (summary format)",
                "[CHECK] Active files only",
                "[CHECK] Immediate next steps",
            ],
            "what_to_remove": [
                "[CROSS] Old file reads (10+ prompts ago)",
                "[CROSS] Completed task details (keep outcomes only)",
                "[CROSS] Debugging context (if issue resolved)",
                "[CROSS] Trial-and-error attempts (keep final solution)",
                "[CROSS] Old conversation (summarize to key points)",
            ],
            "save_before_cleanup": [
                "[FLOPPY] Completed work summary",
                "[FLOPPY] Key architectural decisions",
                "[FLOPPY] Files modified (git status)",
                "[FLOPPY] User preferences stated",
            ],
            "compaction": "50% reduction",
        },

        "aggressive": {
            "description": "Aggressive Cleanup (90%+ context)",
            "what_to_keep": [
                "[CHECK] All session memory files (PROTECTED - ALWAYS!)",
                "[CHECK] User preferences (global)",
                "[CHECK] ONLY current task",
                "[CHECK] Active file being edited",
                "[CHECK] Immediate next action",
            ],
            "what_to_remove": [
                "[CROSS] ALL old file reads (re-read if needed)",
                "[CROSS] ALL completed tasks",
                "[CROSS] ALL old conversation (except current)",
                "[CROSS] ALL debugging context",
                "[CROSS] ALL exploratory work",
            ],
            "save_before_cleanup": [
                "[FLOPPY] CRITICAL: Save session summary NOW!",
                "[FLOPPY] What was done this session",
                "[FLOPPY] All decisions made",
                "[FLOPPY] All files modified",
                "[FLOPPY] Pending work",
            ],
            "compaction": "90% reduction",
        },
    }

    return strategies.get(level, strategies["light"])

def check_session_memory_protection():
    """
    Verify session memory files are protected
    Returns list of protected paths
    """
    protected = []

    sessions_path = os.path.expanduser("~/.claude/memory/sessions/")
    if os.path.exists(sessions_path):
        # Find all session-related files
        for root, dirs, files in os.walk(sessions_path):
            for file in files:
                if file.endswith('.md'):
                    protected.append(os.path.join(root, file))

    return protected

def save_to_session_summary(project_name, strategy):
    """
    Generate session summary template before cleanup
    """
    print("\n" + "=" * 70)
    print("[FLOPPY] SAVE TO SESSION SUMMARY (BEFORE CLEANUP)")
    print("=" * 70)

    print(f"\nProject: {project_name}")
    print(f"Cleanup Level: {strategy['description']}")

    print("\n[CLIPBOARD] What to save:")
    for item in strategy['save_before_cleanup']:
        print(f"  {item}")

    print("\n[U+1F4DD] Session Summary Template:")
    print("-" * 70)

    template = f"""
# Session Summary - {datetime.now().strftime('%Y-%m-%d')}

## Project: {project_name}

## What Was Done:
- [Bullet points of completed work]
- [Features implemented]
- [Bugs fixed]

## Key Decisions:
- [Important architectural decisions]
- [Tech choices made]
- [Approach selected]

## Files Modified:
```
[Output of: git status / git diff --name-only]
```

## User Preferences:
- [Any preferences user stated this session]
- [Code style choices]
- [Workflow preferences]

## Pending Work / Next Steps:
- [ ] [Task 1]
- [ ] [Task 2]
- [ ] [Task 3]

## Important Context for Next Session:
- [Anything crucial to remember]
- [Blockers or issues]
- [Dependencies or requirements]
"""

    print(template)
    print("-" * 70)

    # Suggest save location
    session_file = f"~/.claude/memory/sessions/{project_name}/session-{datetime.now().strftime('%Y-%m-%d-%H-%M')}.md"
    project_summary = f"~/.claude/memory/sessions/{project_name}/project-summary.md"

    print(f"\n[U+1F4C1] Save to:")
    print(f"   Individual: {session_file}")
    print(f"   Cumulative: {project_summary}")

    print("\n[WARNING]️  IMPORTANT: Save session summary BEFORE proceeding with cleanup!")
    print("=" * 70)

def execute_cleanup(level, project=None, dry_run=True):
    """
    Execute cleanup strategy
    """
    strategy = get_cleanup_strategy(level)

    print("\n" + "=" * 70)
    print(f"[U+1F9F9] SMART CONTEXT CLEANUP")
    print("=" * 70)

    print(f"\nLevel: {strategy['description']}")
    print(f"Expected Compaction: {strategy['compaction']}")

    if dry_run:
        print("\n[WARNING]️  DRY RUN MODE (No actual cleanup, showing recommendations only)")

    # Step 1: Check session memory protection
    print("\n" + "=" * 70)
    print("[SHIELD]️  STEP 1: VERIFY SESSION MEMORY PROTECTION")
    print("=" * 70)

    protected_files = check_session_memory_protection()
    if protected_files:
        print(f"\n[CHECK] Protected: {len(protected_files)} session memory files")
        print(f"   Location: ~/.claude/memory/sessions/")
        print(f"   These files will NEVER be touched during cleanup!")
    else:
        print("\n[WARNING]️  No session memory files found (new project?)")

    # Step 2: Save to session summary (if project specified)
    if project:
        print("\n" + "=" * 70)
        print("[SHIELD]️  STEP 2: SAVE IMPORTANT CONTEXT (BEFORE CLEANUP)")
        print("=" * 70)
        save_to_session_summary(project, strategy)
    else:
        print("\n" + "=" * 70)
        print("[SHIELD]️  STEP 2: SAVE SESSION SUMMARY")
        print("=" * 70)
        print("\n[WARNING]️  No project specified. To save session summary:")
        print("   Run: python smart-cleanup.py --level", level, "--project <project-name>")

    # Step 3: Show cleanup strategy
    print("\n" + "=" * 70)
    print("[SHIELD]️  STEP 3: WHAT TO KEEP (PROTECTED)")
    print("=" * 70)
    for item in strategy['what_to_keep']:
        print(f"  {item}")

    print("\n" + "=" * 70)
    print("[U+1F9F9] STEP 4: WHAT TO REMOVE (CLEANUP)")
    print("=" * 70)
    for item in strategy['what_to_remove']:
        print(f"  {item}")

    # Step 4: Log cleanup action
    if dry_run:
        log_policy_hit("dry-run", f"level={level}, project={project or 'none'}")
    else:
        log_policy_hit("cleanup-executed", f"level={level}, compaction={strategy['compaction']}")

    print("\n" + "=" * 70)
    print("[CHECK] CLEANUP STRATEGY READY")
    print("=" * 70)

    if dry_run:
        print("\nThis was a DRY RUN. No cleanup performed.")
        print("To execute cleanup, add --execute flag (future implementation)")

def main():
    parser = argparse.ArgumentParser(
        description="Smart context cleanup with session memory protection"
    )
    parser.add_argument(
        '--level',
        type=str,
        choices=['light', 'moderate', 'aggressive'],
        default='light',
        help='Cleanup level (light/moderate/aggressive)'
    )
    parser.add_argument(
        '--project',
        type=str,
        default=None,
        help='Project name (for session save recommendations)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        default=True,
        help='Show recommendations only (no actual cleanup)'
    )

    args = parser.parse_args()

    # Execute cleanup strategy
    execute_cleanup(args.level, args.project, args.dry_run)

if __name__ == "__main__":
    main()

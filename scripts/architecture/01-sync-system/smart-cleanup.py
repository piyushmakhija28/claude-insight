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
                "✅ All session memory files (PROTECTED)",
                "✅ User preferences & learned patterns",
                "✅ Active task context",
                "✅ Recent decisions (last 5-10 prompts)",
                "✅ Architecture notes",
                "✅ Files currently being worked on",
                "✅ Pending work / next steps",
            ],
            "what_to_remove": [
                "❌ Old file reads (15+ prompts ago, not actively used)",
                "❌ Processed MCP responses (data already extracted)",
                "❌ Redundant information (repeated content)",
                "❌ Exploratory searches (if target already found)",
            ],
            "save_before_cleanup": [
                "💾 Important decisions from old prompts",
                "💾 User-stated preferences not yet saved",
            ],
            "compaction": "20% reduction",
        },

        "moderate": {
            "description": "Moderate Cleanup (85-89% context)",
            "what_to_keep": [
                "✅ All session memory files (PROTECTED)",
                "✅ User preferences & learned patterns",
                "✅ Current task context only",
                "✅ Key decisions (summary format)",
                "✅ Active files only",
                "✅ Immediate next steps",
            ],
            "what_to_remove": [
                "❌ Old file reads (10+ prompts ago)",
                "❌ Completed task details (keep outcomes only)",
                "❌ Debugging context (if issue resolved)",
                "❌ Trial-and-error attempts (keep final solution)",
                "❌ Old conversation (summarize to key points)",
            ],
            "save_before_cleanup": [
                "💾 Completed work summary",
                "💾 Key architectural decisions",
                "💾 Files modified (git status)",
                "💾 User preferences stated",
            ],
            "compaction": "50% reduction",
        },

        "aggressive": {
            "description": "Aggressive Cleanup (90%+ context)",
            "what_to_keep": [
                "✅ All session memory files (PROTECTED - ALWAYS!)",
                "✅ User preferences (global)",
                "✅ ONLY current task",
                "✅ Active file being edited",
                "✅ Immediate next action",
            ],
            "what_to_remove": [
                "❌ ALL old file reads (re-read if needed)",
                "❌ ALL completed tasks",
                "❌ ALL old conversation (except current)",
                "❌ ALL debugging context",
                "❌ ALL exploratory work",
            ],
            "save_before_cleanup": [
                "💾 CRITICAL: Save session summary NOW!",
                "💾 What was done this session",
                "💾 All decisions made",
                "💾 All files modified",
                "💾 Pending work",
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
    print("💾 SAVE TO SESSION SUMMARY (BEFORE CLEANUP)")
    print("=" * 70)

    print(f"\nProject: {project_name}")
    print(f"Cleanup Level: {strategy['description']}")

    print("\n📋 What to save:")
    for item in strategy['save_before_cleanup']:
        print(f"  {item}")

    print("\n📝 Session Summary Template:")
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

    print(f"\n📁 Save to:")
    print(f"   Individual: {session_file}")
    print(f"   Cumulative: {project_summary}")

    print("\n⚠️  IMPORTANT: Save session summary BEFORE proceeding with cleanup!")
    print("=" * 70)

def execute_cleanup(level, project=None, dry_run=True):
    """
    Execute cleanup strategy
    """
    strategy = get_cleanup_strategy(level)

    print("\n" + "=" * 70)
    print(f"🧹 SMART CONTEXT CLEANUP")
    print("=" * 70)

    print(f"\nLevel: {strategy['description']}")
    print(f"Expected Compaction: {strategy['compaction']}")

    if dry_run:
        print("\n⚠️  DRY RUN MODE (No actual cleanup, showing recommendations only)")

    # Step 1: Check session memory protection
    print("\n" + "=" * 70)
    print("🛡️  STEP 1: VERIFY SESSION MEMORY PROTECTION")
    print("=" * 70)

    protected_files = check_session_memory_protection()
    if protected_files:
        print(f"\n✅ Protected: {len(protected_files)} session memory files")
        print(f"   Location: ~/.claude/memory/sessions/")
        print(f"   These files will NEVER be touched during cleanup!")
    else:
        print("\n⚠️  No session memory files found (new project?)")

    # Step 2: Save to session summary (if project specified)
    if project:
        print("\n" + "=" * 70)
        print("🛡️  STEP 2: SAVE IMPORTANT CONTEXT (BEFORE CLEANUP)")
        print("=" * 70)
        save_to_session_summary(project, strategy)
    else:
        print("\n" + "=" * 70)
        print("🛡️  STEP 2: SAVE SESSION SUMMARY")
        print("=" * 70)
        print("\n⚠️  No project specified. To save session summary:")
        print("   Run: python smart-cleanup.py --level", level, "--project <project-name>")

    # Step 3: Show cleanup strategy
    print("\n" + "=" * 70)
    print("🛡️  STEP 3: WHAT TO KEEP (PROTECTED)")
    print("=" * 70)
    for item in strategy['what_to_keep']:
        print(f"  {item}")

    print("\n" + "=" * 70)
    print("🧹 STEP 4: WHAT TO REMOVE (CLEANUP)")
    print("=" * 70)
    for item in strategy['what_to_remove']:
        print(f"  {item}")

    # Step 4: Log cleanup action
    if dry_run:
        log_policy_hit("dry-run", f"level={level}, project={project or 'none'}")
    else:
        log_policy_hit("cleanup-executed", f"level={level}, compaction={strategy['compaction']}")

    print("\n" + "=" * 70)
    print("✅ CLEANUP STRATEGY READY")
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

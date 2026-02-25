#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Auto-Commit Executor
Automatically commits changes when triggers are met

This script:
1. Uses auto-commit-detector.py to check triggers
2. Generates smart commit messages
3. Stages relevant files
4. Creates commits with co-author tag
5. Optional auto-push

Usage:
    python auto-commit.py [--project-dir DIR] [--push] [--dry-run]

Examples:
    python auto-commit.py
    python auto-commit.py --push
    python auto-commit.py --dry-run --project-dir /path/to/repo
"""

import sys
import os
import subprocess
import json
from datetime import datetime

# Fix Windows encoding issues
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

def log_policy_hit(action, context):
    """Log policy execution"""
    log_file = os.path.expanduser("~/.claude/memory/logs/policy-hits.log")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] auto-commit | {action} | {context}\n"

    try:
        with open(log_file, 'a') as f:
            f.write(log_entry)
    except Exception as e:
        print(f"Warning: Could not write to log: {e}", file=sys.stderr)

def check_git_repo(project_dir):
    """Check if directory is a git repo"""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            cwd=project_dir,
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0
    except:
        return False

def get_commit_message_style(project_dir):
    """Analyze recent commits to match style"""
    try:
        result = subprocess.run(
            ["git", "log", "-10", "--pretty=format:%s"],
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0 and result.stdout.strip():
            messages = result.stdout.strip().split('\n')

            # Detect style patterns
            has_type_prefix = any(':' in msg[:20] for msg in messages)
            has_emoji = any(any(ord(c) > 127 for c in msg[:10]) for msg in messages)
            avg_length = sum(len(msg) for msg in messages) / len(messages)

            return {
                "type_prefix": has_type_prefix,  # feat:, fix:, etc.
                "emoji": has_emoji,
                "length": "short" if avg_length < 50 else "medium" if avg_length < 80 else "long"
            }

        return None

    except Exception as e:
        return None

def generate_commit_message(git_status, triggers, style=None):
    """Generate smart commit message based on changes and triggers"""

    # Analyze what changed
    staged_files = git_status.get("staged", [])

    # Categorize changes
    file_types = {}
    for f in staged_files:
        ext = os.path.splitext(f)[1] if '.' in f else 'other'
        file_types[ext] = file_types.get(ext, 0) + 1

    # Determine change type
    change_type = "update"

    if "phase_completion" in triggers:
        change_type = "feat"
        summary = "Complete implementation phase"
    elif "todo_completion" in triggers:
        change_type = "feat"
        summary = "Complete task milestone"
    elif "milestone_signals" in triggers:
        signals = triggers.get("milestone_signals", {}).get("signals", [])
        if "bug fixed" in signals or "fix" in signals:
            change_type = "fix"
            summary = "Fix reported issues"
        elif "feature complete" in signals:
            change_type = "feat"
            summary = "Complete feature implementation"
        else:
            change_type = "feat"
            summary = "Complete milestone"
    elif len(staged_files) >= 10:
        change_type = "feat"
        summary = "Implement major changes"
    else:
        # Infer from file types
        if any(f.endswith('.test.js') or f.endswith('.spec.ts') or 'test' in f for f in staged_files):
            change_type = "test"
            summary = "Add/update tests"
        elif any('readme' in f.lower() or f.endswith('.md') for f in staged_files):
            change_type = "docs"
            summary = "Update documentation"
        elif any(f.endswith('.css') or f.endswith('.scss') or f.endswith('.sass') for f in staged_files):
            change_type = "style"
            summary = "Update styling"
        else:
            change_type = "update"
            summary = "Update implementation"

    # Build message
    if style and style.get("type_prefix"):
        message = f"{change_type}: {summary}"
    else:
        message = summary.capitalize()

    # Add file details
    if len(staged_files) <= 3:
        message += f"\n\nFiles: {', '.join(os.path.basename(f) for f in staged_files)}"
    else:
        message += f"\n\n{len(staged_files)} files modified"
        # Group by type
        if file_types:
            message += "\n" + ", ".join(f"{count} {ext} files" for ext, count in sorted(file_types.items())[:3])

    # Add trigger info
    trigger_names = [t.replace('_', ' ').title() for t in triggers.keys() if t != 'reason']
    if trigger_names:
        message += f"\n\nTriggered by: {', '.join(trigger_names)}"

    # Add co-author
    message += "\n\nCo-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

    return message

def stage_files(project_dir, git_status):
    """Stage relevant files for commit"""
    modified_files = git_status.get("modified", [])

    if not modified_files:
        # All changes already staged
        return True

    # Stage modified files (not untracked)
    try:
        result = subprocess.run(
            ["git", "add", "-u"],
            cwd=project_dir,
            capture_output=True,
            timeout=10
        )

        return result.returncode == 0
    except Exception as e:
        print(f"Error staging files: {e}", file=sys.stderr)
        return False

def create_commit(project_dir, message, dry_run=False):
    """Create git commit"""
    if dry_run:
        print("\n[DRY RUN] Would create commit with message:")
        print("=" * 70)
        print(message)
        print("=" * 70)
        return True

    try:
        result = subprocess.run(
            ["git", "commit", "-m", message],
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            print("\n✅ Commit created successfully!")
            print(result.stdout)
            return True
        else:
            print(f"\n❌ Commit failed: {result.stderr}", file=sys.stderr)
            return False

    except Exception as e:
        print(f"Error creating commit: {e}", file=sys.stderr)
        return False

def push_changes(project_dir, dry_run=False):
    """Push commits to remote"""
    if dry_run:
        print("\n[DRY RUN] Would push to remote")
        return True

    try:
        result = subprocess.run(
            ["git", "push"],
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode == 0:
            print("\n✅ Pushed to remote!")
            print(result.stdout)
            return True
        else:
            print(f"\n⚠️ Push failed: {result.stderr}", file=sys.stderr)
            return False

    except Exception as e:
        print(f"Error pushing: {e}", file=sys.stderr)
        return False

def auto_commit(project_dir, push=False, dry_run=False):
    """Execute auto-commit process"""

    print("\n" + "=" * 70)
    print("🔄 AUTO-COMMIT EXECUTOR")
    print("=" * 70)
    print(f"\nProject: {project_dir}")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print("")

    # Step 1: Check if git repo
    if not check_git_repo(project_dir):
        print("❌ Not a git repository")
        return False

    # Step 2: Run detector
    print("Step 1: Checking commit triggers...")
    try:
        result = subprocess.run(
            ["python", os.path.expanduser("~/.claude/memory/auto-commit-detector.py"),
             "--project-dir", project_dir, "--json"],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            print("⏸️  No commit needed")
            return False

        detection = json.loads(result.stdout)

        if not detection.get("should_commit"):
            print("⏸️  No triggers met")
            return False

        print(f"✅ {detection['trigger_count']} triggers met")
        for trigger in detection['triggers_met']:
            details = detection['details'].get(trigger, {})
            reason = details.get('reason', 'N/A')
            print(f"   ✅ {trigger.replace('_', ' ').title()}: {reason}")

    except Exception as e:
        print(f"❌ Error checking triggers: {e}", file=sys.stderr)
        return False

    git_status = detection.get("git_status", {})
    triggers = detection.get("details", {})

    # Step 3: Stage files
    print("\nStep 2: Staging files...")
    if not stage_files(project_dir, git_status):
        print("❌ Failed to stage files")
        return False
    print("✅ Files staged")

    # Step 4: Generate commit message
    print("\nStep 3: Generating commit message...")
    style = get_commit_message_style(project_dir)
    message = generate_commit_message(git_status, triggers, style)
    print("✅ Message generated")

    # Step 5: Create commit
    print("\nStep 4: Creating commit...")
    if not create_commit(project_dir, message, dry_run):
        return False

    log_policy_hit("commit-created", f"triggers={detection['trigger_count']}, files={git_status['staged_count']}")

    # Step 6: Push (optional)
    if push:
        print("\nStep 5: Pushing to remote...")
        push_changes(project_dir, dry_run)

    print("\n" + "=" * 70)
    print("✅ AUTO-COMMIT COMPLETE")
    print("=" * 70)

    return True

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Auto-commit changes when triggers are met"
    )
    parser.add_argument(
        '--project-dir',
        type=str,
        default=None,
        help='Project directory (default: current directory)'
    )
    parser.add_argument(
        '--push',
        action='store_true',
        help='Push to remote after commit'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Dry run (show what would happen)'
    )

    args = parser.parse_args()

    # Default to current directory
    if not args.project_dir:
        args.project_dir = os.getcwd()

    # Execute auto-commit
    success = auto_commit(args.project_dir, args.push, args.dry_run)

    # Exit code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()

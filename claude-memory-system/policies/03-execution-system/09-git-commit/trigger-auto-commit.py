#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Auto-Commit Trigger Integration
Automatically triggers git commit+push when called

This script is meant to be called after:
1. TaskUpdate(status="completed")
2. Phase completion
3. Significant milestones

Usage:
    python trigger-auto-commit.py [--project-dir DIR] [--event EVENT] [--no-push]

Examples:
    python trigger-auto-commit.py --event "task-completed"
    python trigger-auto-commit.py --event "phase-complete" --project-dir /path/to/repo
    python trigger-auto-commit.py --no-push
"""

import sys
import os
import subprocess
from datetime import datetime

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

def log_policy_hit(action, context):
    """Log policy execution"""
    log_file = os.path.expanduser("~/.claude/memory/logs/policy-hits.log")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] auto-commit-trigger | {action} | {context}\n"

    try:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)
    except Exception as e:
        print(f"Warning: Could not write log: {e}", file=sys.stderr)

def find_git_root(start_dir):
    """Find git root directory by walking up"""
    current = os.path.abspath(start_dir)

    # Walk up max 5 levels
    for _ in range(5):
        git_dir = os.path.join(current, '.git')
        if os.path.exists(git_dir):
            return current

        parent = os.path.dirname(current)
        if parent == current:  # Reached filesystem root
            break
        current = parent

    return None

def trigger_auto_commit(project_dir, event="manual", push=True):
    """Trigger auto-commit process"""

    print("\n" + "=" * 70)
    print("🚀 AUTO-COMMIT TRIGGER")
    print("=" * 70)
    print(f"\nEvent: {event}")
    print(f"Directory: {project_dir}")
    print(f"Push: {'Yes' if push else 'No'}")
    print("")

    # Find git root
    git_root = find_git_root(project_dir)

    if not git_root:
        print("❌ No git repository found")
        print(f"   Searched from: {project_dir}")
        log_policy_hit("no-git-repo", f"event={event}, dir={project_dir}")
        return False

    print(f"✅ Git repository: {git_root}")

    # Log event
    log_policy_hit("triggered", f"event={event}, repo={os.path.basename(git_root)}")

    # Step 1: Check if commit is needed (run detector)
    print("\n📊 Checking commit triggers...")

    detector_script = os.path.expanduser("~/.claude/memory/auto-commit-detector.py")

    try:
        result = subprocess.run(
            ["python", detector_script, "--project-dir", git_root],
            capture_output=True,
            text=True,
            timeout=30
        )

        # Detector exits with 0 if commit is recommended, 1 if not
        should_commit = (result.returncode == 0)

        if not should_commit:
            print("\n⏸️  No commit needed (no triggers met)")
            log_policy_hit("skipped", f"event={event}, reason=no-triggers")
            return False

        print("✅ Commit recommended")

    except Exception as e:
        print(f"⚠️  Detector check failed: {e}")
        print("   Proceeding anyway...")

    # Step 2: Run auto-commit
    print("\n💾 Running auto-commit...")

    commit_script = os.path.expanduser("~/.claude/memory/auto-commit.py")

    cmd = ["python", commit_script, "--project-dir", git_root]

    if push:
        cmd.append("--push")

    try:
        result = subprocess.run(
            cmd,
            capture_output=False,  # Show output directly
            timeout=120
        )

        if result.returncode == 0:
            print("\n✅ AUTO-COMMIT SUCCESSFUL!")
            log_policy_hit("success", f"event={event}, repo={os.path.basename(git_root)}, push={push}")
            return True
        else:
            print("\n⚠️  Auto-commit failed")
            log_policy_hit("failed", f"event={event}, repo={os.path.basename(git_root)}")
            return False

    except subprocess.TimeoutExpired:
        print("\n⏱️  Timeout: Auto-commit took too long")
        log_policy_hit("timeout", f"event={event}")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        log_policy_hit("error", f"event={event}, error={str(e)}")
        return False

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Trigger auto-commit after events"
    )
    parser.add_argument(
        '--project-dir',
        type=str,
        default=None,
        help='Project directory (default: current directory)'
    )
    parser.add_argument(
        '--event',
        type=str,
        default='manual',
        help='Event that triggered this (e.g., task-completed, phase-complete)'
    )
    parser.add_argument(
        '--no-push',
        action='store_true',
        help='Do not push to remote (commit only)'
    )

    args = parser.parse_args()

    # Default to current directory
    if not args.project_dir:
        args.project_dir = os.getcwd()

    # Trigger auto-commit
    success = trigger_auto_commit(
        args.project_dir,
        event=args.event,
        push=not args.no_push
    )

    # Exit code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()

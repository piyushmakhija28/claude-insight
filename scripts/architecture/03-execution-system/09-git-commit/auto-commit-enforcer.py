#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Auto-Commit Enforcer
Ensures auto-commit is triggered on task completion

This enforcer MUST be called after TaskUpdate(status="completed")
when file modifications are involved.

Usage:
    python auto-commit-enforcer.py --check-task TASK_ID
    python auto-commit-enforcer.py --enforce-now

Examples:
    # Check if task requires commit
    python auto-commit-enforcer.py --check-task "1"
    
    # Force commit enforcement
    python auto-commit-enforcer.py --enforce-now
"""

import sys
import os
import subprocess
import json
from datetime import datetime
from pathlib import Path

MEMORY_DIR = Path.home() / ".claude" / "memory"

# Fix Windows encoding
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass


def run_git_command(args, timeout=30):
    """Run a git command and return the result."""
    try:
        return subprocess.run(
            ['git'] + args,
            capture_output=True, text=True, timeout=timeout
        )
    except Exception as e:
        # Return a fake result object on error
        class _R:
            returncode = 1
            stdout = ''
            stderr = str(e)
        return _R()

def log_policy_hit(action, context):
    """Log policy enforcement"""
    log_file = os.path.expanduser("~/.claude/memory/logs/policy-hits.log")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] auto-commit-enforcer | {action} | {context}\n"
    
    try:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)
    except Exception as e:
        print(f"Warning: Could not write log: {e}", file=sys.stderr)

def find_git_repos_with_changes():
    """Find all git repos in workspace with uncommitted changes"""
    repos_with_changes = []
    
    # Detect workspace from environment or current working directory
    workspace = os.environ.get("CLAUDE_WORKSPACE_DIR", os.getcwd())

    if not os.path.exists(workspace):
        return repos_with_changes
    
    # Walk through workspace
    for root, dirs, files in os.walk(workspace):
        # Skip .git internals
        if '.git' in root.split(os.sep):
            continue
            
        # Check if this is a git repo
        if '.git' in dirs:
            try:
                # Check git status
                result = run_git_command(['-C', root, 'status', '--porcelain'])
                
                if result.returncode == 0 and result.stdout.strip():
                    repos_with_changes.append(root)
                    
            except Exception:
                pass
    
    return repos_with_changes

def trigger_commit_for_repo(repo_path):
    """Trigger auto-commit for a specific repo"""
    print('\n' + '='*70)
    print('Repository: ' + os.path.basename(repo_path))
    print('='*70 + '\n')

    # Look for trigger-auto-commit.py in the same directory as this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    trigger_script = os.path.join(script_dir, 'trigger-auto-commit.py')
    if not os.path.exists(trigger_script):
        # Fallback to legacy path
        trigger_script = os.path.expanduser("~/.claude/memory/trigger-auto-commit.py")
    if not os.path.exists(trigger_script):
        # No trigger script available - skip silently
        log_policy_hit("commit-skipped", "trigger-auto-commit.py not found for " + os.path.basename(repo_path))
        return True  # Not an error - just nothing to do

    try:
        result = subprocess.run(
            [
                sys.executable, trigger_script,
                '--project-dir', repo_path,
                '--event', 'task-completed'
            ],
            timeout=120, capture_output=True
        )

        if result.returncode == 0:
            log_policy_hit("commit-triggered", "repo=" + os.path.basename(repo_path))
            return True
        else:
            stderr_msg = result.stderr.decode('utf-8', errors='replace').strip() if result.stderr else 'no stderr'
            log_policy_hit("commit-failed", "repo=" + os.path.basename(repo_path) + ", stderr=" + stderr_msg[:200])
            return False

    except Exception as e:
        log_policy_hit("commit-error", "repo=" + os.path.basename(repo_path) + ", error=" + str(e))
        return False

def enforce_auto_commit():
    """Enforce auto-commit on all repos with changes"""
    print("\n" + "="*70)
    print("[ALERT] AUTO-COMMIT ENFORCER")
    print("="*70 + "\n")
    
    # Find repos with changes
    print("[SEARCH] Scanning for repositories with uncommitted changes...\n")
    repos = find_git_repos_with_changes()
    
    if not repos:
        print("[CHECK] No uncommitted changes found - nothing to commit\n")
        log_policy_hit("no-changes", "scan-complete")
        return True
    
    print("[FOUND] " + str(len(repos)) + " repository(ies) with changes:\n")
    for repo in repos:
        print("   - " + os.path.basename(repo))
    print()

    # Trigger commit for each repo
    success_count = 0
    for repo in repos:
        if trigger_commit_for_repo(repo):
            success_count += 1

    print("\n" + "="*70)
    if success_count == len(repos):
        print("[OK] Successfully processed " + str(success_count) + "/" + str(len(repos)) + " repositories")
        log_policy_hit("enforce-success", "repos=" + str(len(repos)))
    else:
        print("[WARN] Processed " + str(success_count) + "/" + str(len(repos)) + " repositories")
        log_policy_hit("enforce-partial", "success=" + str(success_count) + ", total=" + str(len(repos)))
    print("="*70 + "\n")

    return True  # Always return True - commit enforcement is best-effort

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Enforce auto-commit policy on task completion"
    )
    parser.add_argument(
        '--check-task',
        type=str,
        help='Check if task requires auto-commit'
    )
    parser.add_argument(
        '--enforce-now',
        action='store_true',
        help='Force auto-commit enforcement immediately'
    )
    
    args = parser.parse_args()
    
    if args.enforce_now:
        success = enforce_auto_commit()
        sys.exit(0 if success else 1)
    
    elif args.check_task:
        # For now, always recommend commit after task completion
        # In future, could check task metadata to see if files were modified
        print(f"Task {args.check_task} completed - auto-commit recommended")
        log_policy_hit("task-check", f"task_id={args.check_task}")
        sys.exit(0)
    
    else:
        # No args = called from stop-notifier hook as a check.
        # Run enforce_auto_commit by default so commit enforcement works.
        success = enforce_auto_commit()
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()

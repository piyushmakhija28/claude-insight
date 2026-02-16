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

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

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
    
    # Common project locations
    workspace = os.path.expanduser("~/Documents/workspace-spring-tool-suite-4-4.27.0-new")
    
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
                result = subprocess.run(
                    ['git', '-C', root, 'status', '--porcelain'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0 and result.stdout.strip():
                    repos_with_changes.append(root)
                    
            except Exception:
                pass
    
    return repos_with_changes

def trigger_commit_for_repo(repo_path):
    """Trigger auto-commit for a specific repo"""
    print(f"\n{'='*70}")
    print(f"📦 Repository: {os.path.basename(repo_path)}")
    print(f"{'='*70}\n")
    
    trigger_script = os.path.expanduser("~/.claude/memory/trigger-auto-commit.py")
    
    try:
        result = subprocess.run(
            [
                'python', trigger_script,
                '--project-dir', repo_path,
                '--event', 'task-completed'
            ],
            timeout=120
        )
        
        if result.returncode == 0:
            log_policy_hit("commit-triggered", f"repo={os.path.basename(repo_path)}")
            return True
        else:
            log_policy_hit("commit-failed", f"repo={os.path.basename(repo_path)}")
            return False
            
    except Exception as e:
        print(f"❌ Error triggering commit: {e}")
        log_policy_hit("commit-error", f"repo={os.path.basename(repo_path)}, error={str(e)}")
        return False

def enforce_auto_commit():
    """Enforce auto-commit on all repos with changes"""
    print("\n" + "="*70)
    print("🚨 AUTO-COMMIT ENFORCER")
    print("="*70 + "\n")
    
    # Find repos with changes
    print("🔍 Scanning for repositories with uncommitted changes...\n")
    repos = find_git_repos_with_changes()
    
    if not repos:
        print("✅ No uncommitted changes found - nothing to commit\n")
        log_policy_hit("no-changes", "scan-complete")
        return True
    
    print(f"📋 Found {len(repos)} repository(ies) with changes:\n")
    for repo in repos:
        print(f"   • {os.path.basename(repo)}")
    print()
    
    # Trigger commit for each repo
    success_count = 0
    for repo in repos:
        if trigger_commit_for_repo(repo):
            success_count += 1
    
    print("\n" + "="*70)
    if success_count == len(repos):
        print(f"✅ Successfully processed {success_count}/{len(repos)} repositories")
        log_policy_hit("enforce-success", f"repos={len(repos)}")
    else:
        print(f"⚠️  Processed {success_count}/{len(repos)} repositories")
        log_policy_hit("enforce-partial", f"success={success_count}, total={len(repos)}")
    print("="*70 + "\n")
    
    return success_count > 0

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
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()

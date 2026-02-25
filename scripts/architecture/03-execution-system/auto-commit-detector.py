#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Auto-Commit Trigger Detector
Detects when to automatically commit changes

Triggers:
1. Phase completion (phased execution)
2. Todo completion (task completion)
3. Milestone signals ("done", "complete", "finished")
4. File threshold (10+ files staged)
5. Time threshold (30+ min since last commit)

Usage:
    python auto-commit-detector.py [--project-dir DIR]

Examples:
    python auto-commit-detector.py
    python auto-commit-detector.py --project-dir /path/to/repo
"""

import sys
import os
import subprocess
import json
from datetime import datetime, timedelta

# Fix Windows encoding issues
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Thresholds
THRESHOLDS = {
    "staged_files": 10,         # 10+ files staged → commit
    "time_since_last_commit_min": 30,  # 30+ minutes → commit
    "phase_completion": True,   # Phase complete → commit
    "todo_completion": True,    # Todo complete → commit
}

# Milestone keywords
MILESTONE_KEYWORDS = [
    "done", "finished", "complete", "completed",
    "phase complete", "milestone", "todo done",
    "feature complete", "bug fixed",
]

def log_policy_hit(action, context):
    """Log policy execution"""
    log_file = os.path.expanduser("~/.claude/memory/logs/policy-hits.log")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] auto-commit-detector | {action} | {context}\n"

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

def get_git_status(project_dir):
    """Get git status - staged files, modified files, etc."""
    try:
        # Get staged files
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=5
        )

        staged_files = []
        if result.returncode == 0:
            staged_files = [f for f in result.stdout.strip().split('\n') if f]

        # Get modified but not staged
        result = subprocess.run(
            ["git", "diff", "--name-only"],
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=5
        )

        modified_files = []
        if result.returncode == 0:
            modified_files = [f for f in result.stdout.strip().split('\n') if f]

        # Get untracked files
        result = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard"],
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=5
        )

        untracked_files = []
        if result.returncode == 0:
            untracked_files = [f for f in result.stdout.strip().split('\n') if f]

        return {
            "staged": staged_files,
            "modified": modified_files,
            "untracked": untracked_files,
            "staged_count": len(staged_files),
            "modified_count": len(modified_files),
            "untracked_count": len(untracked_files),
        }

    except Exception as e:
        print(f"Warning: Could not get git status: {e}", file=sys.stderr)
        return None

def get_last_commit_time(project_dir):
    """Get time of last commit"""
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%ct"],
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0 and result.stdout.strip():
            timestamp = int(result.stdout.strip())
            return datetime.fromtimestamp(timestamp)
        else:
            return None

    except Exception as e:
        return None

def detect_milestone_signals():
    """Detect milestone completion signals from logs"""
    log_file = os.path.expanduser("~/.claude/memory/logs/policy-hits.log")

    if not os.path.exists(log_file):
        return []

    signals = []
    cutoff_time = datetime.now() - timedelta(minutes=15)

    try:
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()

            for line in lines[-100:]:
                try:
                    if line.startswith('['):
                        timestamp_str = line[1:20]
                        timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")

                        if timestamp > cutoff_time:
                            line_lower = line.lower()
                            for keyword in MILESTONE_KEYWORDS:
                                if keyword in line_lower:
                                    signals.append(keyword)
                                    break
                except:
                    continue

    except Exception as e:
        print(f"Warning: Could not detect signals: {e}", file=sys.stderr)

    return list(set(signals))

def detect_phase_completion():
    """Detect phase completion from logs"""
    log_file = os.path.expanduser("~/.claude/memory/logs/policy-hits.log")

    if not os.path.exists(log_file):
        return False

    cutoff_time = datetime.now() - timedelta(minutes=15)

    try:
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()

            for line in lines[-50:]:
                try:
                    if line.startswith('['):
                        timestamp_str = line[1:20]
                        timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")

                        if timestamp > cutoff_time:
                            if 'phase-complete' in line.lower() or 'phase completed' in line.lower():
                                return True
                except:
                    continue

    except:
        pass

    return False

def detect_todo_completion():
    """Detect todo completion from logs"""
    log_file = os.path.expanduser("~/.claude/memory/logs/policy-hits.log")

    if not os.path.exists(log_file):
        return False

    cutoff_time = datetime.now() - timedelta(minutes=15)

    try:
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()

            for line in lines[-50:]:
                try:
                    if line.startswith('['):
                        timestamp_str = line[1:20]
                        timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")

                        if timestamp > cutoff_time:
                            if 'todo-complete' in line.lower() or 'task completed' in line.lower():
                                return True
                except:
                    continue

    except:
        pass

    return False

def check_commit_triggers(project_dir):
    """Check all commit triggers"""
    triggers_met = []
    trigger_details = {}

    # Check if git repo
    if not check_git_repo(project_dir):
        return {
            "should_commit": False,
            "reason": "Not a git repository",
            "triggers_met": [],
            "trigger_count": 0,
            "details": {},
        }

    # Get git status
    git_status = get_git_status(project_dir)

    if not git_status:
        return {
            "should_commit": False,
            "reason": "Could not get git status",
            "triggers_met": [],
            "trigger_count": 0,
            "details": {},
        }

    # No changes to commit
    if git_status["staged_count"] == 0 and git_status["modified_count"] == 0:
        return {
            "should_commit": False,
            "reason": "No changes to commit",
            "triggers_met": [],
            "trigger_count": 0,
            "details": {},
            "git_status": git_status,
        }

    # 1. Staged files threshold
    if git_status["staged_count"] >= THRESHOLDS["staged_files"]:
        triggers_met.append("staged_files")
        trigger_details["staged_files"] = {
            "count": git_status["staged_count"],
            "threshold": THRESHOLDS["staged_files"],
            "reason": f"{git_status['staged_count']} files staged (threshold: {THRESHOLDS['staged_files']})"
        }

    # 2. Time since last commit
    last_commit = get_last_commit_time(project_dir)
    if last_commit:
        time_diff = (datetime.now() - last_commit).total_seconds() / 60

        if time_diff >= THRESHOLDS["time_since_last_commit_min"]:
            triggers_met.append("time_since_commit")
            trigger_details["time_since_commit"] = {
                "minutes": round(time_diff, 1),
                "threshold": THRESHOLDS["time_since_last_commit_min"],
                "reason": f"{time_diff:.1f} minutes since last commit"
            }

    # 3. Phase completion
    if THRESHOLDS["phase_completion"] and detect_phase_completion():
        triggers_met.append("phase_completion")
        trigger_details["phase_completion"] = {
            "reason": "Phase completion detected in recent logs"
        }

    # 4. Todo completion
    if THRESHOLDS["todo_completion"] and detect_todo_completion():
        triggers_met.append("todo_completion")
        trigger_details["todo_completion"] = {
            "reason": "Todo completion detected in recent logs"
        }

    # 5. Milestone signals
    milestone_signals = detect_milestone_signals()
    if milestone_signals:
        triggers_met.append("milestone_signals")
        trigger_details["milestone_signals"] = {
            "signals": milestone_signals,
            "reason": f"Milestone signals detected: {', '.join(milestone_signals)}"
        }

    return {
        "should_commit": len(triggers_met) > 0,
        "triggers_met": triggers_met,
        "trigger_count": len(triggers_met),
        "details": trigger_details,
        "git_status": git_status,
        "project_dir": project_dir,
        "timestamp": datetime.now().isoformat(),
    }

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Detect auto-commit triggers"
    )
    parser.add_argument(
        '--project-dir',
        type=str,
        default=None,
        help='Project directory (default: current directory)'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output as JSON'
    )

    args = parser.parse_args()

    # Default to current directory
    if not args.project_dir:
        args.project_dir = os.getcwd()

    # Check triggers
    result = check_commit_triggers(args.project_dir)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("\n" + "=" * 70)
        print("📊 AUTO-COMMIT TRIGGER DETECTION")
        print("=" * 70)
        print(f"\nProject: {result.get('project_dir', 'N/A')}")
        print(f"Timestamp: {result.get('timestamp', 'N/A')}")

        if result['should_commit']:
            print(f"\n✅ AUTO-COMMIT RECOMMENDED ({result['trigger_count']} triggers met)")

            if 'git_status' in result:
                git = result['git_status']
                print(f"\n📁 Git Status:")
                print(f"   Staged: {git['staged_count']} files")
                print(f"   Modified: {git['modified_count']} files")
                print(f"   Untracked: {git['untracked_count']} files")

            print("\n🎯 Triggers Met:")
            for trigger in result['triggers_met']:
                details = result['details'].get(trigger, {})
                reason = details.get('reason', 'N/A')
                print(f"   ✅ {trigger.replace('_', ' ').title()}: {reason}")

            print("\n💾 Action: Auto-commit changes")

        else:
            reason = result.get('reason', 'No triggers met')
            print(f"\n⏸️  NO COMMIT NEEDED")
            print(f"   Reason: {reason}")

        print("\n" + "=" * 70)

    # Log trigger check
    log_policy_hit(
        "trigger-check",
        f"should_commit={result['should_commit']}, triggers={result['trigger_count']}"
    )

    # Exit code indicates whether to commit
    sys.exit(0 if result['should_commit'] else 1)

if __name__ == "__main__":
    main()

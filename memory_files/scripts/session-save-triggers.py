#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Session Save Trigger Detector
Automatically detects when to save session summary

Triggers:
1. File count threshold (5+ files modified)
2. Git commit detected
3. Time threshold (60+ minutes session)
4. User signals ("done", "finished", "complete")
5. Major decision detected

Usage:
    python session-save-triggers.py [--project PROJECT]

Examples:
    python session-save-triggers.py --project my-app
"""

import sys
import os
import subprocess
import json
from datetime import datetime, timedelta
from pathlib import Path

# Fix Windows encoding issues
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Trigger thresholds
THRESHOLDS = {
    "file_count": 5,           # 5+ files modified → save
    "session_duration_min": 60, # 60+ minutes → save
    "git_commits": 1,          # 1+ commits → save
    "major_decisions": 1,      # 1+ major decisions → save
}

# User signal keywords
USER_SIGNALS = [
    "done", "finished", "complete", "completed",
    "that's it", "all done", "finished working",
    "bye", "goodbye", "done for now", "done for today",
    "perfect", "great", "awesome", "excellent",
]

def log_policy_hit(action, context):
    """Log policy execution"""
    log_file = os.path.expanduser("~/.claude/memory/logs/policy-hits.log")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] session-save-trigger | {action} | {context}\n"

    try:
        with open(log_file, 'a') as f:
            f.write(log_entry)
    except Exception as e:
        print(f"Warning: Could not write to log: {e}", file=sys.stderr)

def get_git_status(project_dir=None):
    """
    Get git status - files modified, commits made
    """
    if not project_dir:
        project_dir = os.getcwd()

    try:
        # Check if git repo
        result = subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode != 0:
            return {"is_repo": False}

        # Get modified files
        result = subprocess.run(
            ["git", "status", "--short"],
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=5
        )

        modified_files = []
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            modified_files = [line for line in lines if line.strip()]

        # Get recent commits (last 2 hours)
        result = subprocess.run(
            ["git", "log", "--since=2.hours.ago", "--oneline"],
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=5
        )

        recent_commits = []
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            recent_commits = [line for line in lines if line.strip()]

        return {
            "is_repo": True,
            "modified_files": modified_files,
            "modified_count": len(modified_files),
            "recent_commits": recent_commits,
            "commit_count": len(recent_commits),
        }

    except Exception as e:
        return {"is_repo": False, "error": str(e)}

def get_session_duration():
    """
    Get current session duration from logs
    """
    log_file = os.path.expanduser("~/.claude/memory/logs/policy-hits.log")

    if not os.path.exists(log_file):
        return 0

    try:
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()

            # Find session start (recent context-loaded entry)
            session_start = None
            cutoff_time = datetime.now() - timedelta(hours=4)

            for line in reversed(lines[-500:]):
                if 'context-loaded' in line or 'session-start' in line:
                    try:
                        timestamp_str = line[1:20]
                        timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                        if timestamp > cutoff_time:
                            session_start = timestamp
                            break
                    except:
                        continue

            if session_start:
                duration = datetime.now() - session_start
                return duration.total_seconds() / 60  # Minutes

    except Exception as e:
        print(f"Warning: Could not read session duration: {e}", file=sys.stderr)

    return 0

def detect_major_decisions():
    """
    Detect major decisions from recent logs
    """
    log_file = os.path.expanduser("~/.claude/memory/logs/policy-hits.log")

    if not os.path.exists(log_file):
        return []

    decisions = []

    try:
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()

            # Check last 100 log entries
            for line in lines[-100:]:
                # Look for decision indicators
                if any(keyword in line.lower() for keyword in [
                    'decision', 'chose', 'selected', 'plan-mode',
                    'architecture', 'approach', 'proactive-consultation'
                ]):
                    parts = line.split('|')
                    if len(parts) >= 3:
                        decisions.append(parts[2].strip())

    except Exception as e:
        print(f"Warning: Could not detect decisions: {e}", file=sys.stderr)

    return list(set(decisions))[:5]  # Max 5 unique decisions

def detect_user_signals():
    """
    Detect user completion signals from logs
    """
    log_file = os.path.expanduser("~/.claude/memory/logs/policy-hits.log")

    if not os.path.exists(log_file):
        return []

    signals = []

    try:
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()

            # Check last 50 log entries
            for line in lines[-50:]:
                line_lower = line.lower()
                for signal in USER_SIGNALS:
                    if signal in line_lower:
                        signals.append(signal)
                        break

    except Exception as e:
        print(f"Warning: Could not detect user signals: {e}", file=sys.stderr)

    return list(set(signals))

def check_triggers(project_name=None):
    """
    Check all save triggers
    """
    triggers_met = []
    trigger_details = {}

    # 1. Git status check
    git_status = get_git_status()
    if git_status.get("is_repo"):
        file_count = git_status.get("modified_count", 0)
        commit_count = git_status.get("commit_count", 0)

        if file_count >= THRESHOLDS["file_count"]:
            triggers_met.append("file_count")
            trigger_details["file_count"] = {
                "count": file_count,
                "threshold": THRESHOLDS["file_count"],
                "reason": f"{file_count} files modified (threshold: {THRESHOLDS['file_count']})"
            }

        if commit_count >= THRESHOLDS["git_commits"]:
            triggers_met.append("git_commits")
            trigger_details["git_commits"] = {
                "count": commit_count,
                "threshold": THRESHOLDS["git_commits"],
                "reason": f"{commit_count} commits made in last 2 hours"
            }

    # 2. Session duration check
    session_duration = get_session_duration()
    if session_duration >= THRESHOLDS["session_duration_min"]:
        triggers_met.append("session_duration")
        trigger_details["session_duration"] = {
            "duration_min": round(session_duration, 1),
            "threshold": THRESHOLDS["session_duration_min"],
            "reason": f"Session running for {session_duration:.1f} minutes"
        }

    # 3. Major decisions check
    decisions = detect_major_decisions()
    if len(decisions) >= THRESHOLDS["major_decisions"]:
        triggers_met.append("major_decisions")
        trigger_details["major_decisions"] = {
            "count": len(decisions),
            "decisions": decisions,
            "reason": f"{len(decisions)} major decisions detected"
        }

    # 4. User signals check
    user_signals = detect_user_signals()
    if user_signals:
        triggers_met.append("user_signals")
        trigger_details["user_signals"] = {
            "signals": user_signals,
            "reason": f"User completion signals detected: {', '.join(user_signals)}"
        }

    return {
        "should_save": len(triggers_met) > 0,
        "triggers_met": triggers_met,
        "trigger_count": len(triggers_met),
        "details": trigger_details,
        "project": project_name or os.path.basename(os.getcwd()),
        "timestamp": datetime.now().isoformat(),
    }

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Detect session save triggers"
    )
    parser.add_argument(
        '--project',
        type=str,
        default=None,
        help='Project name (auto-detected if not specified)'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output as JSON'
    )

    args = parser.parse_args()

    # Auto-detect project
    if not args.project:
        args.project = os.path.basename(os.getcwd())

    # Check triggers
    result = check_triggers(args.project)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("\n" + "=" * 70)
        print("📊 SESSION SAVE TRIGGER DETECTION")
        print("=" * 70)
        print(f"\nProject: {result['project']}")
        print(f"Timestamp: {result['timestamp']}")

        if result['should_save']:
            print(f"\n✅ AUTO-SAVE RECOMMENDED ({result['trigger_count']} triggers met)")

            print("\n🎯 Triggers Met:")
            for trigger in result['triggers_met']:
                details = result['details'].get(trigger, {})
                reason = details.get('reason', 'N/A')
                print(f"   ✅ {trigger.replace('_', ' ').title()}: {reason}")

            print("\n💾 Action: Auto-save session summary")

        else:
            print("\n⏸️  NO TRIGGERS MET")
            print("   Continue working - save not needed yet")

        print("\n" + "=" * 70)

    # Log trigger check
    log_policy_hit(
        "trigger-check",
        f"project={result['project']}, should_save={result['should_save']}, triggers={result['trigger_count']}"
    )

    # Exit code indicates whether to save
    sys.exit(0 if result['should_save'] else 1)

if __name__ == "__main__":
    main()

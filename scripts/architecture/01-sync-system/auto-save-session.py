#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Auto-Save Session Summary
Automatically saves session summary before context cleanup

Usage:
    python auto-save-session.py --project PROJECT_NAME

Examples:
    python auto-save-session.py --project my-app
"""

import sys
import os
import json
import argparse
from datetime import datetime
from pathlib import Path

# Fix Windows encoding issues
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

def log_policy_hit(action, context):
    """Log policy execution"""
    log_file = os.path.expanduser("~/.claude/memory/logs/policy-hits.log")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] auto-save-session | {action} | {context}\n"

    try:
        with open(log_file, 'a') as f:
            f.write(log_entry)
    except Exception as e:
        print(f"Warning: Could not write to log: {e}", file=sys.stderr)

def get_recent_activity():
    """
    Extract recent activity from logs
    """
    activity = {
        "files_modified": [],
        "decisions_made": [],
        "tasks_completed": [],
        "preferences_stated": [],
    }

    log_file = os.path.expanduser("~/.claude/memory/logs/policy-hits.log")

    if not os.path.exists(log_file):
        return activity

    try:
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()

            # Get last 100 log entries
            for line in lines[-100:]:
                # Extract activity patterns
                if 'file-read' in line or 'Edit' in line or 'Write' in line:
                    # Extract file mentions
                    parts = line.split('|')
                    if len(parts) >= 3:
                        context = parts[2].strip()
                        if '/' in context or '\\' in context:
                            activity["files_modified"].append(context)

                if 'decision' in line.lower() or 'chose' in line.lower():
                    parts = line.split('|')
                    if len(parts) >= 3:
                        activity["decisions_made"].append(parts[2].strip())

                if 'completed' in line.lower() or 'finished' in line.lower():
                    parts = line.split('|')
                    if len(parts) >= 3:
                        activity["tasks_completed"].append(parts[2].strip())

                if 'preference' in line.lower() or 'user-preferences' in line:
                    parts = line.split('|')
                    if len(parts) >= 3:
                        activity["preferences_stated"].append(parts[2].strip())

    except Exception as e:
        print(f"Warning: Could not read activity logs: {e}", file=sys.stderr)

    # Deduplicate
    for key in activity:
        activity[key] = list(set(activity[key]))[:10]  # Keep max 10 unique items

    return activity

def generate_session_summary(project_name):
    """
    Generate session summary automatically
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    date_str = datetime.now().strftime("%Y-%m-%d")

    # Get recent activity
    activity = get_recent_activity()

    # Load context estimate
    estimate_file = os.path.expanduser("~/.claude/memory/.context-estimate")
    context_info = {}
    if os.path.exists(estimate_file):
        try:
            with open(estimate_file, 'r') as f:
                context_info = json.load(f)
                # Handle legacy float format
                if isinstance(context_info, (int, float)):
                    context_info = {
                        'context_percent': float(context_info),
                        'recommendation': {'action': 'N/A'},
                        'metrics': {'session_duration_minutes': 0}
                    }
        except:
            pass

    # Generate summary
    summary = f"""# Auto-Generated Session Summary

**Project:** {project_name}
**Timestamp:** {timestamp}
**Generated:** Automatically before context cleanup

---

## Context Status

- **Estimated Context Usage:** {context_info.get('context_percent', 'Unknown')}%
- **Recommendation:** {context_info.get('recommendation', {}).get('action', 'N/A')}
- **Session Duration:** {context_info.get('metrics', {}).get('session_duration_minutes', 0):.1f} minutes

---

## Recent Activity

### Files Modified
"""

    if activity["files_modified"]:
        for file in activity["files_modified"]:
            summary += f"- {file}\n"
    else:
        summary += "- (No file modifications detected)\n"

    summary += "\n### Tasks Completed\n"
    if activity["tasks_completed"]:
        for task in activity["tasks_completed"]:
            summary += f"- {task}\n"
    else:
        summary += "- (No completed tasks detected)\n"

    summary += "\n### Decisions Made\n"
    if activity["decisions_made"]:
        for decision in activity["decisions_made"]:
            summary += f"- {decision}\n"
    else:
        summary += "- (No decisions detected)\n"

    summary += "\n### User Preferences\n"
    if activity["preferences_stated"]:
        for pref in activity["preferences_stated"]:
            summary += f"- {pref}\n"
    else:
        summary += "- (No preferences stated)\n"

    summary += """
---

## Important Context

*(This section can be manually updated by user)*

- Key architectural decisions:
- Pending work / next steps:
- Blockers or issues:
- Important notes:

---

## Session Metrics

"""

    metrics = context_info.get('metrics', {})
    summary += f"- Messages: {metrics.get('message_count', 0)}\n"
    summary += f"- File Reads: {metrics.get('file_reads', 0)}\n"
    summary += f"- Tool Calls: {metrics.get('tool_calls', 0)}\n"
    summary += f"- MCP Responses: {metrics.get('mcp_responses', 0)}\n"

    summary += "\n---\n\n"
    summary += "*Auto-saved before context cleanup to preserve important information*\n"

    return summary

def save_session_summary(project_name, summary):
    """
    Save session summary to session directory
    """
    # Create session directory if doesn't exist
    session_dir = os.path.expanduser(f"~/.claude/memory/sessions/{project_name}")
    os.makedirs(session_dir, exist_ok=True)

    # Save individual session file
    timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M")
    session_file = os.path.join(session_dir, f"session-{timestamp}.md")

    try:
        with open(session_file, 'w', encoding='utf-8') as f:
            f.write(summary)

        print(f"✅ Session saved: {session_file}")
        log_policy_hit("session-saved", f"project={project_name}, file={session_file}")

    except Exception as e:
        print(f"❌ Failed to save session: {e}", file=sys.stderr)
        log_policy_hit("save-failed", f"project={project_name}, error={str(e)}")
        return False

    # Update project summary (cumulative)
    project_summary_file = os.path.join(session_dir, "project-summary.md")

    # If project summary doesn't exist, use session summary as base
    if not os.path.exists(project_summary_file):
        try:
            with open(project_summary_file, 'w', encoding='utf-8') as f:
                f.write(f"# Project Summary: {project_name}\n\n")
                f.write(f"**Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write("---\n\n")
                f.write(summary)

            print(f"✅ Project summary created: {project_summary_file}")

        except Exception as e:
            print(f"Warning: Could not create project summary: {e}", file=sys.stderr)

    else:
        # Append to existing summary
        try:
            with open(project_summary_file, 'a', encoding='utf-8') as f:
                f.write("\n\n---\n\n")
                f.write(f"## Session Update: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
                f.write(summary)

            print(f"✅ Project summary updated: {project_summary_file}")

        except Exception as e:
            print(f"Warning: Could not update project summary: {e}", file=sys.stderr)

    return True

def main():
    parser = argparse.ArgumentParser(
        description="Auto-save session summary before context cleanup"
    )
    parser.add_argument(
        '--project',
        type=str,
        required=True,
        help='Project name'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show summary without saving'
    )

    args = parser.parse_args()

    print("\n" + "=" * 70)
    print("💾 AUTO-SAVE SESSION SUMMARY")
    print("=" * 70)
    print(f"\nProject: {args.project}")

    # Generate summary
    print("\n📝 Generating session summary...")
    summary = generate_session_summary(args.project)

    if args.dry_run:
        print("\n" + "=" * 70)
        print("DRY RUN - Summary Preview:")
        print("=" * 70)
        print(summary)
        print("=" * 70)
        print("\n(Not saved - dry run mode)")
    else:
        # Save summary
        print("\n💾 Saving session summary...")
        if save_session_summary(args.project, summary):
            print("\n✅ Session summary saved successfully!")
        else:
            print("\n❌ Failed to save session summary")
            sys.exit(1)

    print("\n" + "=" * 70)

if __name__ == "__main__":
    main()

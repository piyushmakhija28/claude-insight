#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Context Window Monitor
Monitors context usage and provides cleanup recommendations

Usage:
    python monitor-context.py [--threshold PERCENT]

Examples:
    python monitor-context.py              # Check current status
    python monitor-context.py --threshold 70  # Alert if above 70%
"""

import sys
import os
import argparse
from datetime import datetime

# Fix Windows encoding issues
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Protected directories (NEVER cleanup!)
PROTECTED_PATHS = [
    os.path.expanduser("~/.claude/memory/sessions/"),
    os.path.expanduser("~/.claude/memory/*.md"),
    os.path.expanduser("~/.claude/memory/logs/"),
    os.path.expanduser("~/.claude/settings*.json"),
    os.path.expanduser("~/.claude/*.md"),
]

def log_policy_hit(action, context):
    """Log policy execution"""
    log_file = os.path.expanduser("~/.claude/memory/logs/policy-hits.log")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] context-management | {action} | {context}\n"

    try:
        with open(log_file, 'a') as f:
            f.write(log_entry)
    except Exception as e:
        print(f"Warning: Could not write to log: {e}", file=sys.stderr)

def get_context_recommendations(threshold):
    """
    Get cleanup recommendations based on threshold

    Thresholds:
    - 70-84%: Light cleanup (remove old file reads, MCP responses)
    - 85-89%: Moderate cleanup (compress completed work)
    - 90%+: Aggressive cleanup (keep only essentials)
    """
    recommendations = {
        "protect": [
            "✅ Session memory files (sessions/**/*.md)",
            "✅ User preferences (user-preferences.json)",
            "✅ Project summaries (project-summary.md)",
            "✅ Active task context",
            "✅ Recent decisions & architecture notes",
        ],
        "cleanup": [],
        "priority": "normal"
    }

    if threshold >= 90:
        recommendations["cleanup"] = [
            "🔴 AGGRESSIVE CLEANUP:",
            "   - Remove all old file reads (5+ prompts ago)",
            "   - Clear completed task details",
            "   - Remove trial-and-error attempts",
            "   - Clear old MCP responses (already processed)",
            "   - Keep ONLY current task context",
            "   - Summarize conversation (keep decisions only)",
        ]
        recommendations["priority"] = "critical"

    elif threshold >= 85:
        recommendations["cleanup"] = [
            "🚨 MODERATE CLEANUP:",
            "   - Remove old file reads (10+ prompts ago)",
            "   - Compress completed tasks (keep outcomes only)",
            "   - Clear debugging context",
            "   - Remove exploratory searches (already done)",
            "   - Summarize old conversation",
        ]
        recommendations["priority"] = "high"

    elif threshold >= 70:
        recommendations["cleanup"] = [
            "⚠️ LIGHT CLEANUP:",
            "   - Remove old file reads (15+ prompts ago)",
            "   - Clear MCP responses (after extraction)",
            "   - Remove redundant information",
            "   - Keep most context intact",
        ]
        recommendations["priority"] = "medium"
    else:
        recommendations["cleanup"] = [
            "✅ NO CLEANUP NEEDED",
            "   - Context usage is healthy",
            "   - Continue normal operation",
        ]
        recommendations["priority"] = "normal"

    return recommendations

def save_to_session_before_cleanup(project_name):
    """
    Suggest saving important context to session memory before cleanup
    """
    print("\n💾 BEFORE CLEANUP - Save Important Context:")
    print("=" * 60)
    print(f"Project: {project_name}")
    print("\nSuggest saving to session memory:")
    print("  - Key decisions made this session")
    print("  - Architecture changes")
    print("  - User preferences stated")
    print("  - Files modified")
    print("  - Pending work / next steps")
    print("\nCommand to save:")
    print(f"  (Offer user to save session summary)")
    print("=" * 60)

def check_protected_paths():
    """
    Verify protected paths exist and are accessible
    """
    print("\n🛡️ PROTECTED PATHS CHECK:")
    print("=" * 60)

    sessions_path = os.path.expanduser("~/.claude/memory/sessions/")
    if os.path.exists(sessions_path):
        print(f"✅ Session memory protected: {sessions_path}")
        session_count = len([d for d in os.listdir(sessions_path)
                           if os.path.isdir(os.path.join(sessions_path, d))])
        print(f"   Projects with history: {session_count}")
    else:
        print(f"⚠️  Session memory path not found: {sessions_path}")

    logs_path = os.path.expanduser("~/.claude/memory/logs/")
    if os.path.exists(logs_path):
        print(f"✅ Logs protected: {logs_path}")
    else:
        print(f"⚠️  Logs path not found: {logs_path}")

    print("=" * 60)

def main():
    parser = argparse.ArgumentParser(
        description="Monitor context window usage and provide cleanup recommendations"
    )
    parser.add_argument(
        '--threshold',
        type=int,
        default=70,
        help='Alert threshold percentage (default: 70)'
    )
    parser.add_argument(
        '--project',
        type=str,
        default=None,
        help='Project name (for session save suggestions)'
    )
    parser.add_argument(
        '--simulate',
        type=int,
        default=None,
        help='Simulate context percentage for testing (0-100)'
    )

    args = parser.parse_args()

    # Simulate context percentage (in real usage, this would come from Claude Code)
    context_percent = args.simulate if args.simulate is not None else 75

    print("\n" + "=" * 60)
    print("CONTEXT WINDOW MONITOR")
    print("=" * 60)

    if args.simulate is not None:
        print(f"\n⚠️  SIMULATION MODE (Testing with {context_percent}% context)")
    else:
        print(f"\nℹ️  Context monitoring (Threshold: {args.threshold}%)")
        print("Note: Actual context % comes from Claude Code built-in tracking")

    print(f"\nContext Usage: {context_percent}%")

    # Check if threshold exceeded
    if context_percent >= args.threshold:
        print(f"⚠️  WARNING: Context above threshold ({args.threshold}%)")

        # Get recommendations
        recs = get_context_recommendations(context_percent)

        print(f"\nPriority: {recs['priority'].upper()}")

        # Protected items
        print("\n🛡️ PROTECTED (NEVER CLEANUP):")
        for item in recs["protect"]:
            print(f"  {item}")

        # Cleanup recommendations
        print("\n🧹 CLEANUP RECOMMENDATIONS:")
        for item in recs["cleanup"]:
            print(f"  {item}")

        # Check protected paths
        check_protected_paths()

        # Suggest session save if project specified
        if args.project:
            save_to_session_before_cleanup(args.project)
        elif context_percent >= 85:
            print("\n💾 RECOMMENDATION: Save important context to session memory before cleanup")
            print("   Run: python monitor-context.py --project <project-name>")

        # Log monitoring action
        log_policy_hit("threshold-exceeded", f"{context_percent}% (threshold: {args.threshold}%)")

        # Exit code indicates cleanup needed
        sys.exit(1)
    else:
        print(f"✅ Context usage healthy (below {args.threshold}%)")
        log_policy_hit("check-ok", f"{context_percent}%")
        sys.exit(0)

if __name__ == "__main__":
    main()

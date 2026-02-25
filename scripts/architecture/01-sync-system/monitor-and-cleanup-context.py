#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Context Monitor and Auto-Cleanup
Monitors ACTUAL Claude Code context usage and triggers cleanup

This script:
1. Reads actual context from .context-usage file
2. Checks against thresholds (70%, 85%, 90%)
3. Triggers appropriate cleanup action
4. Protects session memory (NEVER deletes)

Usage:
    python monitor-and-cleanup-context.py [--auto-trigger] [--dry-run]

Examples:
    python monitor-and-cleanup-context.py
    python monitor-and-cleanup-context.py --auto-trigger
    python monitor-and-cleanup-context.py --dry-run
"""

import sys
import os
import json
import subprocess
from datetime import datetime

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Thresholds
THRESHOLDS = {
    "light": 70,
    "moderate": 85,
    "aggressive": 90,
}

def log_policy_hit(action, context):
    """Log policy execution"""
    log_file = os.path.expanduser("~/.claude/memory/logs/policy-hits.log")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] context-monitor | {action} | {context}\n"

    try:
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)
    except Exception as e:
        print(f"Warning: Could not write log: {e}", file=sys.stderr)

def get_actual_context():
    """Read actual context usage from tracking file"""
    tracking_file = os.path.expanduser("~/.claude/memory/.context-usage")

    if not os.path.exists(tracking_file):
        print("⚠️  No context tracking data found")
        print("   Update with: python update-context-usage.py --tokens-used USED")
        return None

    try:
        with open(tracking_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error reading context data: {e}", file=sys.stderr)
        return None

def determine_cleanup_action(context_percent):
    """Determine what cleanup action is needed"""
    if context_percent >= THRESHOLDS["aggressive"]:
        return {
            "level": "aggressive",
            "action": "full-compact",
            "command": "claude compact --full",
            "message": "🚨 CRITICAL: Full compact required!",
            "protect_session": True,
        }
    elif context_percent >= THRESHOLDS["moderate"]:
        return {
            "level": "moderate",
            "action": "auto-compact",
            "command": "claude compact",
            "message": "⚠️  HIGH: Auto-compact recommended",
            "protect_session": True,
        }
    elif context_percent >= THRESHOLDS["light"]:
        return {
            "level": "light",
            "action": "light-cleanup",
            "command": "claude compact --light",
            "message": "💡 MEDIUM: Light cleanup suggested",
            "protect_session": True,
        }
    else:
        return {
            "level": "none",
            "action": "none",
            "command": None,
            "message": "✅ OK: No cleanup needed",
            "protect_session": False,
        }

def trigger_cleanup(action_info, dry_run=False):
    """Trigger cleanup action"""

    if not action_info["command"]:
        print("\n✅ No cleanup needed")
        return True

    print(f"\n{action_info['message']}")
    print(f"Action: {action_info['action']}")
    print(f"Command: {action_info['command']}")

    if dry_run:
        print("\n[DRY RUN] Would execute cleanup")
        return True

    # Execute cleanup
    try:
        print("\n⏳ Executing cleanup...")

        # Note: In real usage, Claude Code should be told to run these commands
        # For now, just log the recommendation
        log_policy_hit(
            "cleanup-recommended",
            f"level={action_info['level']}, action={action_info['action']}"
        )

        print(f"\n💡 RECOMMENDATION:")
        print(f"   Run: {action_info['command']}")
        print(f"   This will: {action_info['message']}")

        if action_info["protect_session"]:
            print("\n🛡️  Session memory will be PROTECTED")
            print("   - Session summaries: SAFE")
            print("   - Project context: SAFE")
            print("   - Only conversation history will be compacted")

        return True

    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        return False

def monitor_context(auto_trigger=False, dry_run=False):
    """Monitor context and optionally trigger cleanup"""

    print("\n" + "=" * 70)
    print("🔍 CONTEXT MONITOR - ACTUAL USAGE")
    print("=" * 70)

    # Get actual context
    context_data = get_actual_context()

    if not context_data:
        return False

    # Display current status
    print(f"\n📊 Current Status:")
    print(f"   Tokens Used: {context_data['tokens_used']:,} / {context_data['tokens_total']:,}")
    print(f"   Context: {context_data['context_percent']}%")
    print(f"   Remaining: {context_data['tokens_remaining']:,} tokens")
    print(f"   Last Updated: {context_data['timestamp']}")

    # Check thresholds
    print(f"\n🎯 Thresholds:")
    print(f"   Light cleanup: {THRESHOLDS['light']}%")
    print(f"   Moderate cleanup: {THRESHOLDS['moderate']}%")
    print(f"   Aggressive cleanup: {THRESHOLDS['aggressive']}%")

    # Determine action
    action_info = determine_cleanup_action(context_data['context_percent'])

    print(f"\n📋 Assessment:")
    print(f"   Level: {action_info['level'].upper()}")
    print(f"   {action_info['message']}")

    # Trigger cleanup if auto-trigger enabled
    if auto_trigger and action_info['command']:
        print("\n🔄 Auto-trigger ENABLED")
        trigger_cleanup(action_info, dry_run)
    elif action_info['command']:
        print("\n💡 Auto-trigger DISABLED")
        print(f"   To auto-trigger, run with --auto-trigger")
        print(f"   Or manually run: {action_info['command']}")

    log_policy_hit(
        "monitored",
        f"{context_data['context_percent']}%, level={action_info['level']}"
    )

    print("\n" + "=" * 70)

    # Exit code indicates cleanup urgency
    if context_data['context_percent'] >= THRESHOLDS["aggressive"]:
        return 2  # Critical
    elif context_data['context_percent'] >= THRESHOLDS["light"]:
        return 1  # Warning
    else:
        return 0  # OK

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Monitor actual context usage and trigger cleanup"
    )
    parser.add_argument(
        '--auto-trigger',
        action='store_true',
        help='Automatically trigger cleanup if needed'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Dry run (show what would happen)'
    )

    args = parser.parse_args()

    # Monitor context
    exit_code = monitor_context(
        auto_trigger=args.auto_trigger,
        dry_run=args.dry_run
    )

    sys.exit(exit_code if isinstance(exit_code, int) else 1)

if __name__ == "__main__":
    main()

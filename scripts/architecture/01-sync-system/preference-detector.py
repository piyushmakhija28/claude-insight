#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
User Preference Detector
Automatically detects user preferences from conversation logs

Detects preferences for:
- Testing approach (skip/include)
- API style (REST/GraphQL)
- Commit frequency (frequent/milestone)
- Documentation (inline/separate)
- Error handling (verbose/minimal)

Usage:
    python preference-detector.py [--analyze-logs] [--category CATEGORY]

Examples:
    python preference-detector.py --analyze-logs
    python preference-detector.py --category testing
"""

import sys
import os
import json
import re
from datetime import datetime, timedelta
from pathlib import Path

# Fix Windows encoding issues
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Preference detection patterns
PREFERENCE_PATTERNS = {
    "testing": {
        "skip": ["skip test", "no test", "skip testing", "without test", "don't need test"],
        "include": ["write test", "add test", "include test", "with test", "test case"],
        "tdd": ["tdd", "test driven", "test first"],
    },
    "api_style": {
        "rest": ["rest api", "restful", "rest endpoint", "use rest"],
        "graphql": ["graphql", "use graphql", "graph ql"],
        "grpc": ["grpc", "use grpc"],
    },
    "commit_frequency": {
        "frequent": ["commit often", "frequent commit", "small commit", "commit each"],
        "milestone": ["commit milestone", "commit phase", "commit when done", "big commit"],
        "feature": ["commit per feature", "feature commit"],
    },
    "documentation": {
        "inline": ["inline doc", "doc comment", "comment code", "document inline"],
        "separate": ["separate doc", "readme", "doc file", "external doc"],
        "minimal": ["minimal doc", "no doc", "skip doc", "light doc"],
    },
    "error_handling": {
        "verbose": ["verbose error", "detailed error", "full error", "show all error"],
        "minimal": ["minimal error", "simple error", "basic error", "hide error"],
        "user_friendly": ["user friendly error", "friendly error", "nice error"],
    },
    "code_style": {
        "verbose": ["verbose", "explicit", "detailed code", "full variable name"],
        "concise": ["concise", "short", "compact code", "brief"],
        "functional": ["functional", "immutable", "pure function"],
    },
}

def log_policy_hit(action, context):
    """Log policy execution"""
    log_file = os.path.expanduser("~/.claude/memory/logs/policy-hits.log")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] preference-detector | {action} | {context}\n"

    try:
        with open(log_file, 'a') as f:
            f.write(log_entry)
    except Exception as e:
        print(f"Warning: Could not write to log: {e}", file=sys.stderr)

def analyze_logs_for_preferences():
    """
    Analyze policy logs to detect user preferences
    """
    log_file = os.path.expanduser("~/.claude/memory/logs/policy-hits.log")

    if not os.path.exists(log_file):
        return {}

    detected_preferences = {}

    try:
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()

            # Analyze last 500 log entries
            for line in lines[-500:]:
                line_lower = line.lower()

                # Check each preference category
                for category, patterns in PREFERENCE_PATTERNS.items():
                    for value, keywords in patterns.items():
                        for keyword in keywords:
                            if keyword in line_lower:
                                # Preference detected
                                if category not in detected_preferences:
                                    detected_preferences[category] = {}

                                if value not in detected_preferences[category]:
                                    detected_preferences[category][value] = 0

                                detected_preferences[category][value] += 1
                                break

    except Exception as e:
        print(f"Warning: Could not analyze logs: {e}", file=sys.stderr)

    return detected_preferences

def get_strongest_preference(category_prefs):
    """
    Get the strongest preference from detected patterns
    """
    if not category_prefs:
        return None

    # Find value with highest count
    max_count = 0
    strongest = None

    for value, count in category_prefs.items():
        if count > max_count:
            max_count = count
            strongest = value

    return strongest, max_count

def load_existing_preferences():
    """
    Load existing learned preferences
    """
    pref_file = os.path.expanduser("~/.claude/memory/user-preferences.json")

    if not os.path.exists(pref_file):
        return {}

    try:
        with open(pref_file, 'r') as f:
            return json.load(f)
    except:
        return {}

def should_track_preference(category, value, count):
    """
    Determine if preference should be tracked/learned
    """
    # Track if seen 2+ times (threshold for learning is 3)
    return count >= 2

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Detect user preferences from conversation logs"
    )
    parser.add_argument(
        '--analyze-logs',
        action='store_true',
        help='Analyze logs for preferences'
    )
    parser.add_argument(
        '--category',
        type=str,
        default=None,
        help='Check specific category only'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output as JSON'
    )

    args = parser.parse_args()

    # Analyze logs
    detected = analyze_logs_for_preferences()

    # Load existing preferences
    existing = load_existing_preferences()

    # Filter by category if specified
    if args.category:
        detected = {args.category: detected.get(args.category, {})}

    if args.json:
        output = {
            "detected": detected,
            "existing": existing,
            "timestamp": datetime.now().isoformat(),
        }
        print(json.dumps(output, indent=2))
    else:
        print("\n" + "=" * 70)
        print("🔍 USER PREFERENCE DETECTION")
        print("=" * 70)

        if not detected:
            print("\n⚠️  No preferences detected in recent logs")
            print("\n💡 Preferences are detected from conversation patterns")
        else:
            print("\n📊 Detected Preferences:")

            for category, values in detected.items():
                strongest, count = get_strongest_preference(values)

                print(f"\n📌 {category.replace('_', ' ').title()}:")

                for value, val_count in sorted(values.items(), key=lambda x: x[1], reverse=True):
                    marker = "✅" if value == strongest else "  "
                    learned = "✓ LEARNED" if category in existing and existing[category] == value else ""
                    trackable = "→ TRACKABLE" if should_track_preference(category, value, val_count) else ""

                    print(f"   {marker} {value}: {val_count} occurrences {learned} {trackable}")

            print("\n" + "=" * 70)
            print("💾 Existing Learned Preferences:")

            if existing:
                for category, value in existing.items():
                    print(f"   ✅ {category.replace('_', ' ').title()}: {value}")
            else:
                print("   (None learned yet - need 3+ occurrences)")

        print("\n" + "=" * 70)

    # Log detection
    total_detected = sum(len(values) for values in detected.values())
    log_policy_hit("detection-complete", f"categories={len(detected)}, patterns={total_detected}")

if __name__ == "__main__":
    main()

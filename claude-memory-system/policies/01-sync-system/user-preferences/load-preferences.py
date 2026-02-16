#!/usr/bin/env python3
"""
Global User Preference Loader
Loads learned user preferences for decision-making.

Usage:
  python load-preferences.py                    # Show all preferences
  python load-preferences.py <category>         # Get specific preference
  python load-preferences.py --has <category>   # Check if preference exists

Examples:
  python load-preferences.py                    # Show all
  python load-preferences.py testing            # Get testing preference
  python load-preferences.py --has api_style    # Check if set
"""

import json
import sys
import io
from pathlib import Path

# Fix Windows console encoding for emojis
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

PREFS_FILE = Path.home() / ".claude" / "memory" / "user-preferences.json"


def load_preferences():
    """Load current preferences from file."""
    if not PREFS_FILE.exists():
        return None

    try:
        with open(PREFS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None


def get_preference(category):
    """Get a specific preference value."""
    prefs = load_preferences()
    if not prefs:
        return None

    # Check all top-level categories
    for cat_name in ['technology_preferences', 'language_preferences', 'workflow_preferences']:
        if category in prefs[cat_name]:
            return prefs[cat_name][category]

    return None


def has_preference(category):
    """Check if a preference has been learned."""
    value = get_preference(category)
    return value is not None


def show_all_preferences():
    """Display all learned preferences."""
    prefs = load_preferences()
    if not prefs:
        print("❌ No preferences file found")
        return

    print("🎯 Global User Preferences")
    print("=" * 60)

    # Technology Preferences
    print("\n📱 Technology Preferences:")
    tech = prefs['technology_preferences']
    for key, value in tech.items():
        if value:
            print(f"  ✓ {key}: {value}")
        else:
            print(f"  - {key}: (not set)")

    # Language Preferences
    print("\n💻 Language Preferences:")
    lang = prefs['language_preferences']
    for key, value in lang.items():
        if value:
            print(f"  ✓ {key}: {value}")
        else:
            print(f"  - {key}: (not set)")

    # Workflow Preferences
    print("\n⚙️  Workflow Preferences:")
    workflow = prefs['workflow_preferences']
    for key, value in workflow.items():
        if value:
            print(f"  ✓ {key}: {value}")
        else:
            print(f"  - {key}: (not set)")

    # Metadata
    print("\n📊 Statistics:")
    meta = prefs['metadata']
    print(f"  Total preferences learned: {meta['total_preferences_learned']}")
    print(f"  Learning threshold: {meta['learning_threshold']}")
    if meta['last_updated']:
        print(f"  Last updated: {meta['last_updated']}")


def main():
    if len(sys.argv) == 1:
        # No arguments - show all preferences
        show_all_preferences()

    elif len(sys.argv) == 2:
        # Get specific preference
        category = sys.argv[1]
        value = get_preference(category)

        if value:
            print(value)
        else:
            sys.exit(1)  # Not set - exit with error code

    elif len(sys.argv) == 3 and sys.argv[1] == "--has":
        # Check if preference exists
        category = sys.argv[2]
        if has_preference(category):
            print("yes")
            sys.exit(0)
        else:
            print("no")
            sys.exit(1)

    else:
        print("Usage: python load-preferences.py [category]")
        print("       python load-preferences.py --has <category>")
        sys.exit(1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Memory System Rollback Mechanism
Allows undoing changes made by the memory system.

Features:
- Rollback user preferences
- Rollback session summaries
- Rollback pattern detections
- Restore archived sessions

Usage:
  python rollback.py --list                    # List available rollback points
  python rollback.py --preferences             # Rollback last preference change
  python rollback.py --patterns                # Rollback last pattern detection
  python rollback.py --restore-session <file>  # Restore archived session

Examples:
  python rollback.py --list
  python rollback.py --preferences
  python rollback.py --patterns
"""

import json
import os
import sys
import io
import shutil
from datetime import datetime
from pathlib import Path

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

MEMORY_DIR = Path.home() / ".claude" / "memory"
BACKUP_DIR = MEMORY_DIR / "backups"
LOG_FILE = MEMORY_DIR / "logs" / "policy-hits.log"


def log_action(action, context):
    """Log rollback action."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = f"[{timestamp}] rollback | {action} | {context}\n"

    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(log_entry)


def ensure_backup_dir():
    """Ensure backup directory exists."""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)


def create_backup(file_path, backup_name):
    """Create a backup of a file."""
    ensure_backup_dir()

    if not Path(file_path).exists():
        return None

    timestamp = datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
    backup_file = BACKUP_DIR / f"{backup_name}-{timestamp}.json"

    shutil.copy2(file_path, backup_file)
    return backup_file


def list_backups():
    """List all available backups."""
    ensure_backup_dir()

    backups = {
        'preferences': [],
        'patterns': [],
        'skills': []
    }

    for backup_file in BACKUP_DIR.glob('*.json'):
        name = backup_file.stem
        if 'user-preferences' in name:
            backups['preferences'].append(backup_file)
        elif 'cross-project-patterns' in name:
            backups['patterns'].append(backup_file)
        elif 'skills-registry' in name:
            backups['skills'].append(backup_file)

    return backups


def show_backups():
    """Display all available backups."""
    backups = list_backups()

    print("📦 Available Rollback Points")
    print("=" * 70)

    if backups['preferences']:
        print("\n💾 User Preferences Backups:")
        for backup in sorted(backups['preferences'], reverse=True)[:5]:
            timestamp = backup.stem.split('-', 2)[-1]
            size = backup.stat().st_size
            print(f"  • {timestamp} ({size} bytes)")
    else:
        print("\n💾 User Preferences Backups: None")

    if backups['patterns']:
        print("\n🔍 Pattern Detection Backups:")
        for backup in sorted(backups['patterns'], reverse=True)[:5]:
            timestamp = backup.stem.split('-', 3)[-1]
            size = backup.stat().st_size
            print(f"  • {timestamp} ({size} bytes)")
    else:
        print("\n🔍 Pattern Detection Backups: None")

    if backups['skills']:
        print("\n🛠️  Skills Registry Backups:")
        for backup in sorted(backups['skills'], reverse=True)[:5]:
            timestamp = backup.stem.split('-', 2)[-1]
            size = backup.stat().st_size
            print(f"  • {timestamp} ({size} bytes)")
    else:
        print("\n🛠️  Skills Registry Backups: None")

    print("\n" + "=" * 70)


def rollback_preferences():
    """Rollback user preferences to last backup."""
    backups = list_backups()

    if not backups['preferences']:
        print("❌ No preference backups found")
        return

    # Get most recent backup
    latest_backup = sorted(backups['preferences'], reverse=True)[0]
    prefs_file = MEMORY_DIR / "user-preferences.json"

    # Create current backup before rollback
    current_backup = create_backup(prefs_file, "user-preferences-pre-rollback")

    # Restore from backup
    shutil.copy2(latest_backup, prefs_file)

    print(f"✅ Rolled back preferences to: {latest_backup.stem}")
    print(f"   Current state backed up to: {current_backup.name}")

    log_action('preferences-rollback', f'restored from {latest_backup.stem}')


def rollback_patterns():
    """Rollback pattern detection to last backup."""
    backups = list_backups()

    if not backups['patterns']:
        print("❌ No pattern backups found")
        return

    # Get most recent backup
    latest_backup = sorted(backups['patterns'], reverse=True)[0]
    patterns_file = MEMORY_DIR / "cross-project-patterns.json"

    # Create current backup before rollback
    current_backup = create_backup(patterns_file, "cross-project-patterns-pre-rollback")

    # Restore from backup
    shutil.copy2(latest_backup, patterns_file)

    print(f"✅ Rolled back patterns to: {latest_backup.stem}")
    print(f"   Current state backed up to: {current_backup.name}")

    log_action('patterns-rollback', f'restored from {latest_backup.stem}')


def auto_backup_before_change(file_type):
    """Automatically create backup before making changes."""
    files = {
        'preferences': MEMORY_DIR / "user-preferences.json",
        'patterns': MEMORY_DIR / "cross-project-patterns.json",
        'skills': MEMORY_DIR / "skills-registry.json"
    }

    if file_type not in files:
        return None

    file_path = files[file_type]
    if not file_path.exists():
        return None

    backup_file = create_backup(file_path, f"{file_type}-auto")
    return backup_file


def main():
    if '--list' in sys.argv:
        show_backups()

    elif '--preferences' in sys.argv:
        rollback_preferences()

    elif '--patterns' in sys.argv:
        rollback_patterns()

    elif '--restore-session' in sys.argv:
        print("❌ Session restoration not yet implemented")
        print("   Use: tar -xzf archive/YYYY-MM/sessions.tar.gz <file>")

    elif '--help' in sys.argv or len(sys.argv) == 1:
        print("Memory System Rollback")
        print("=" * 70)
        print("\nUsage:")
        print("  python rollback.py --list               # List backups")
        print("  python rollback.py --preferences        # Rollback preferences")
        print("  python rollback.py --patterns           # Rollback patterns")
        print("  python rollback.py --restore-session    # Restore session")
        print("\nExamples:")
        print("  python rollback.py --list")
        print("  python rollback.py --preferences")

    else:
        print("❌ Unknown option. Use --help for usage information.")
        sys.exit(1)


if __name__ == "__main__":
    main()

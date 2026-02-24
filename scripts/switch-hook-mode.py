#!/usr/bin/env python
# Script Name: switch-hook-mode.py
# Version: 1.0.0
# Last Modified: 2026-02-24
# Description: Switch between normal and lightweight hook modes
# Author: Claude Memory System
#
# Usage: python switch-hook-mode.py normal|lightweight|auto
#   normal      - Restore full hook output and verification
#   lightweight - Reduce timeouts and skip verbose output
#   auto        - Detect mode automatically (2+ tasks = lightweight)
#
# Windows-safe: ASCII only, no Unicode chars

import sys
import json
from pathlib import Path
import shutil

HOME = Path.home()
SETTINGS_FILE = HOME / '.claude' / 'settings.json'
SETTINGS_BACKUP = HOME / '.claude' / 'settings.json.backup'
MODE_FILE = HOME / '.claude' / '.hook-mode.json'


NORMAL_CONFIG = {
    "model": "haiku",
    "hooks": {
        "UserPromptSubmit": [
            {
                "hooks": [
                    {
                        "type": "command",
                        "command": "python C:/Users/techd/.claude/memory/current/clear-session-handler.py",
                        "timeout": 15,
                        "statusMessage": "Level 1: Checking session state..."
                    },
                    {
                        "type": "command",
                        "command": "python C:/Users/techd/.claude/memory/current/3-level-flow.py --summary",
                        "timeout": 30,
                        "statusMessage": "Level -1/1/2/3: Running 3-level architecture check..."
                    }
                ]
            }
        ],
        "PreToolUse": [
            {
                "hooks": [
                    {
                        "type": "command",
                        "command": "python C:/Users/techd/.claude/memory/current/pre-tool-enforcer.py",
                        "timeout": 10,
                        "statusMessage": "Level 3.6/3.7: Tool optimization + failure prevention..."
                    }
                ]
            }
        ],
        "PostToolUse": [
            {
                "hooks": [
                    {
                        "type": "command",
                        "command": "python C:/Users/techd/.claude/memory/current/post-tool-tracker.py",
                        "timeout": 10,
                        "statusMessage": "Level 3.9: Tracking task progress..."
                    }
                ]
            }
        ],
        "Stop": [
            {
                "hooks": [
                    {
                        "type": "command",
                        "command": "python C:/Users/techd/.claude/memory/current/stop-notifier.py",
                        "timeout": 60,
                        "statusMessage": "Level 3.10: Session save + voice notification..."
                    }
                ]
            }
        ]
    },
    "skipDangerousModePermissionPrompt": True
}


LIGHTWEIGHT_CONFIG = {
    "model": "haiku",
    "hooks": {
        "UserPromptSubmit": [
            {
                "hooks": [
                    {
                        "type": "command",
                        "command": "python C:/Users/techd/.claude/memory/current/clear-session-handler.py",
                        "timeout": 10,
                        "statusMessage": "[FAST] Checking session..."
                    },
                    {
                        "type": "command",
                        "command": "python C:/Users/techd/.claude/memory/current/parallel-mode-enforcer.py",
                        "timeout": 5,
                        "statusMessage": "[PARALLEL] Lightweight mode active..."
                    }
                ]
            }
        ],
        "PreToolUse": [
            {
                "hooks": [
                    {
                        "type": "command",
                        "command": "python C:/Users/techd/.claude/memory/current/pre-tool-enforcer.py",
                        "timeout": 5,
                        "statusMessage": "[PARALLEL] Checking..."
                    }
                ]
            }
        ],
        "PostToolUse": [
            {
                "hooks": [
                    {
                        "type": "command",
                        "command": "python C:/Users/techd/.claude/memory/current/post-tool-tracker.py",
                        "timeout": 5,
                        "statusMessage": "[PARALLEL] Tracking..."
                    }
                ]
            }
        ],
        "Stop": [
            {
                "hooks": [
                    {
                        "type": "command",
                        "command": "python C:/Users/techd/.claude/memory/current/stop-notifier.py",
                        "timeout": 30,
                        "statusMessage": "[FAST] Session save..."
                    }
                ]
            }
        ]
    },
    "skipDangerousModePermissionPrompt": True
}


def save_mode(mode):
    """Save current mode to file."""
    MODE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(MODE_FILE, 'w', encoding='utf-8') as f:
        json.dump({'mode': mode}, f)


def get_mode():
    """Get current hook mode."""
    try:
        if MODE_FILE.exists():
            with open(MODE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f).get('mode', 'normal')
    except:
        pass
    return 'normal'


def switch_to_mode(mode):
    """Switch settings.json to specified mode."""
    if mode == 'normal':
        config = NORMAL_CONFIG
    elif mode == 'lightweight':
        config = LIGHTWEIGHT_CONFIG
    else:
        print('[ERROR] Invalid mode. Use: normal|lightweight')
        sys.exit(1)

    # Backup current settings
    if SETTINGS_FILE.exists():
        shutil.copy(str(SETTINGS_FILE), str(SETTINGS_BACKUP))

    # Write new config
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2)

    save_mode(mode)
    print('[OK] Switched to {} hook mode'.format(mode))


def detect_auto_mode():
    """Detect mode automatically based on active tasks."""
    try:
        import sys
        sys.path.insert(0, str(Path.home() / '.claude' / 'memory' / 'current'))
        from parallel_mode_manager import count_active_tasks
        if count_active_tasks() >= 2:
            return 'lightweight'
    except:
        pass
    return 'normal'


if __name__ == '__main__':
    if len(sys.argv) < 2:
        current = get_mode()
        print('[INFO] Current hook mode: {}'.format(current))
        print('[USAGE] python switch-hook-mode.py normal|lightweight|auto')
        sys.exit(0)

    target_mode = sys.argv[1]

    if target_mode == 'auto':
        target_mode = detect_auto_mode()

    switch_to_mode(target_mode)

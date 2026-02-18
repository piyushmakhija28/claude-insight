#!/bin/bash
#
# Install Automatic Policy Enforcement Hooks
#
# This updates ~/.claude/settings.json with the 3-level flow hooks
# so policy enforcement runs automatically before every Claude Code request.
#
# Hooks installed:
#   UserPromptSubmit:
#     1. clear-session-handler.py  (detects /clear, manages sessions)
#     2. 3-level-flow.py --summary (runs full 3-level architecture)
#   Stop:
#     1. stop-notifier.py          (session summary notification)
#

set -e

CLAUDE_DIR="$HOME/.claude"
MEMORY_CURRENT="$CLAUDE_DIR/memory/current"
SETTINGS_FILE="$CLAUDE_DIR/settings.json"

echo "================================================================================"
echo "INSTALLING AUTO-ENFORCEMENT HOOKS (settings.json)"
echo "================================================================================"
echo ""

# Ensure .claude directory and memory/current exist
mkdir -p "$MEMORY_CURRENT"

# Backup existing settings if present
if [ -f "$SETTINGS_FILE" ]; then
    cp "$SETTINGS_FILE" "$SETTINGS_FILE.backup"
    echo "[OK] Backed up existing settings.json"
fi

# Check if hooks already configured
if [ -f "$SETTINGS_FILE" ] && grep -q "3-level-flow" "$SETTINGS_FILE" 2>/dev/null; then
    echo "[OK] Hooks already configured in settings.json"
    echo ""
    echo "Current hook commands:"
    grep '"command"' "$SETTINGS_FILE" | head -10
    echo ""
    echo "To reinstall: delete ~/.claude/settings.json and run this script again"
    exit 0
fi

# Install hooks via Python (handles JSON properly, Windows-safe ASCII output)
python3 << PYTHON_SCRIPT
import sys
import json
from pathlib import Path

memory_current = Path.home() / '.claude' / 'memory' / 'current'
settings_file  = Path.home() / '.claude' / 'settings.json'

# Load existing settings or create new
if settings_file.exists():
    with open(settings_file, 'r', encoding='utf-8') as f:
        settings = json.load(f)
else:
    settings = {}

# Set default model if not set
if 'model' not in settings:
    settings['model'] = 'sonnet'

# Build hook commands using actual paths
cmd_clear  = 'python ' + str(memory_current / 'clear-session-handler.py')
cmd_flow   = 'python ' + str(memory_current / '3-level-flow.py') + ' --summary'
cmd_stop   = 'python ' + str(memory_current / 'stop-notifier.py')

# Install hooks
settings['hooks'] = {
    'Stop': [
        {
            'hooks': [
                {
                    'type': 'command',
                    'command': cmd_stop,
                    'timeout': 20,
                    'statusMessage': 'Checking if session summary needed...'
                }
            ]
        }
    ],
    'UserPromptSubmit': [
        {
            'hooks': [
                {
                    'type': 'command',
                    'command': cmd_clear,
                    'timeout': 15,
                    'statusMessage': 'Checking session state...'
                },
                {
                    'type': 'command',
                    'command': cmd_flow,
                    'timeout': 30,
                    'statusMessage': 'Running 3-level architecture check...'
                }
            ]
        }
    ]
}

# Write settings.json
with open(settings_file, 'w', encoding='utf-8') as f:
    json.dump(settings, f, indent=2)

print('[OK] settings.json updated with 3-level flow hooks')
print('[OK] Location: ' + str(settings_file))
print('')
print('Hooks installed:')
print('  UserPromptSubmit[0]: ' + cmd_clear)
print('  UserPromptSubmit[1]: ' + cmd_flow)
print('  Stop[0]: ' + cmd_stop)
PYTHON_SCRIPT

echo ""
echo "================================================================================"
echo "[OK] HOOKS INSTALLATION COMPLETE"
echo "================================================================================"
echo ""
echo "Hooks installed in: $SETTINGS_FILE"
echo ""
echo "What happens on every message:"
echo "  1. clear-session-handler.py  - Detects /clear, saves old session"
echo "  2. 3-level-flow.py --summary - Runs full 3-level architecture:"
echo "       Level -1: Auto-Fix Enforcement (7 system checks)"
echo "       Level 1:  Sync System (Context + Session)"
echo "       Level 2:  Standards System (14 standards, 89 rules)"
echo "       Level 3:  Execution System (12 steps)"
echo ""
echo "On session end:"
echo "  3. stop-notifier.py - Session summary notification"
echo ""
echo "NEXT STEP: Restart Claude Code to activate hooks."
echo ""

#!/bin/bash
################################################################################
# AUTO-FIX ENFORCER - Shell Wrapper
#
# 🚨 CRITICAL: If ANY system fails → STOP ALL WORK → FIX IMMEDIATELY
#
# Usage:
#   bash ~/.claude/memory/auto-fix-enforcer.sh           # Check and auto-fix
#   bash ~/.claude/memory/auto-fix-enforcer.sh --check   # Check only, no fix
#
# Exit Codes:
#   0 = All systems OK
#   1+ = Number of critical failures
################################################################################

set -e

MEMORY_PATH="$HOME/.claude/memory"
ENFORCER_SCRIPT="$MEMORY_PATH/auto-fix-enforcer.py"

# Set UTF-8 encoding for Python
export PYTHONIOENCODING=utf-8

# Check if enforcer exists
if [ ! -f "$ENFORCER_SCRIPT" ]; then
    echo "❌ ERROR: Auto-fix enforcer script not found!"
    echo "   Expected: $ENFORCER_SCRIPT"
    exit 1
fi

# Run enforcer
if [ "$1" == "--check" ]; then
    # Check only, no auto-fix
    python "$ENFORCER_SCRIPT" --no-auto-fix
else
    # Check and auto-fix
    python "$ENFORCER_SCRIPT"
fi

exit $?

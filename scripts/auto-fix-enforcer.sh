#!/bin/bash
################################################################################
# Script Name: auto-fix-enforcer.sh
# Version: 2.0.0
# Last Modified: 2026-02-18
# Description: Shell wrapper for auto-fix-enforcer.py with proper encoding
# Author: Claude Memory System
# Changelog: See CHANGELOG.md
#
# [ALERT] CRITICAL: If ANY system fails -> STOP ALL WORK -> FIX IMMEDIATELY
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
ENFORCER_SCRIPT="$MEMORY_PATH/current/auto-fix-enforcer.py"

# Set UTF-8 encoding for Python (comprehensive settings)
export PYTHONIOENCODING=utf-8
export PYTHONUTF8=1

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

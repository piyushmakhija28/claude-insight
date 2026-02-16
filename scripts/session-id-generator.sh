#!/bin/bash
################################################################################
# SESSION ID GENERATOR - Shell Wrapper
#
# Generates unique session IDs for tracking purposes
#
# Usage:
#   bash session-id-generator.sh create              # Create new session
#   bash session-id-generator.sh current             # Show current session
#   bash session-id-generator.sh list                # List recent sessions
################################################################################

MEMORY_PATH="$HOME/.claude/memory"
GENERATOR_SCRIPT="$MEMORY_PATH/session-id-generator.py"

# Set UTF-8 encoding for Python
export PYTHONIOENCODING=utf-8

# Check if generator exists
if [ ! -f "$GENERATOR_SCRIPT" ]; then
    echo "❌ ERROR: Session ID generator not found!"
    echo "   Expected: $GENERATOR_SCRIPT"
    exit 1
fi

# Run generator with all arguments
python "$GENERATOR_SCRIPT" "$@"
exit $?

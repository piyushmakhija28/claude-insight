#!/bin/bash
# Plan Detector Shell Wrapper
# Automatically shows active Claude Code plan

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLAN_DETECTOR="$SCRIPT_DIR/plan-detector.py"

# Check if Python is available
if command -v python &> /dev/null; then
    PYTHON_CMD="python"
elif command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
else
    echo "❌ Python not found. Please install Python to use plan detector."
    exit 1
fi

# Run plan detector
$PYTHON_CMD "$PLAN_DETECTOR" "$@"

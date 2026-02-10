#!/bin/bash
# Policy Execution Tracker - Simplified version
# Usage: ./policy-tracker.sh <policy-name> <action> <context>

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$SCRIPT_DIR/logs"
HITS_LOG="$LOG_DIR/policy-hits.log"
COUNTER_FILE="$LOG_DIR/policy-counters.txt"

# Create log directory if needed
mkdir -p "$LOG_DIR"

# Get arguments
POLICY_NAME="$1"
ACTION="$2"
CONTEXT="$3"

# Get timestamp
timestamp="$(date '+%Y-%m-%d %H:%M:%S')"

# Log the policy hit
printf "[%s] %s | %s | %s\n" "$timestamp" "$POLICY_NAME" "$ACTION" "$CONTEXT" >> "$HITS_LOG"

# Initialize counters file if it doesn't exist
if [ ! -f "$COUNTER_FILE" ]; then
    cat > "$COUNTER_FILE" << 'COUNTERS'
context-management=0
model-selection=0
adaptive-skill=0
planning-intelligence=0
phased-execution=0
failure-prevention=0
file-management=0
git-auto-commit=0
test-case-policy=0
COUNTERS
fi

# Update counter for this policy
if grep -q "^${POLICY_NAME}=" "$COUNTER_FILE" 2>/dev/null; then
    current_count="$(grep "^${POLICY_NAME}=" "$COUNTER_FILE" | cut -d'=' -f2)"
    new_count=$((current_count + 1))
    # Use temp file for sed on Windows/Git Bash
    sed "s/^${POLICY_NAME}=.*/${POLICY_NAME}=${new_count}/" "$COUNTER_FILE" > "$COUNTER_FILE.tmp"
    mv "$COUNTER_FILE.tmp" "$COUNTER_FILE"
else
    printf "%s=1\n" "$POLICY_NAME" >> "$COUNTER_FILE"
fi

# Keep log file trimmed (last 500 lines)
if [ $(wc -l < "$HITS_LOG") -gt 500 ]; then
    tail -500 "$HITS_LOG" > "$HITS_LOG.tmp"
    mv "$HITS_LOG.tmp" "$HITS_LOG"
fi

# Debug output if enabled
if [ "$DEBUG_MEMORY" = "true" ]; then
    printf "✓ POLICY LOGGED: %s | %s\n" "$POLICY_NAME" "$ACTION" >&2
fi

exit 0

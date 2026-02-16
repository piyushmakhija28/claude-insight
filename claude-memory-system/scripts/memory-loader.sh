#!/bin/bash
# Memory System Loader & Monitor
# Loads all memory policies and tracks their execution

MEMORY_DIR="$(dirname "$0")"
LOG_DIR="$MEMORY_DIR/logs"
PROCESS_LOG="$LOG_DIR/process-execution.log"
STATUS_LOG="$LOG_DIR/system-status.log"

# Create logs directory
mkdir -p "$LOG_DIR"

# Initialize log files
timestamp=$(date '+%Y-%m-%d %H:%M:%S')

# Log system startup
echo "========================================" >> "$PROCESS_LOG"
echo "[$timestamp] MEMORY SYSTEM STARTUP" >> "$PROCESS_LOG"
echo "========================================" >> "$PROCESS_LOG"

# Function to log policy execution
log_policy() {
    local policy_name=$1
    local status=$2
    local details=$3
    echo "[$timestamp] POLICY: $policy_name | STATUS: $status | DETAILS: $details" >> "$PROCESS_LOG"
}

# Load and summarize all memory files
echo "" >> "$PROCESS_LOG"
echo "=== LOADING MEMORY POLICIES ===" >> "$PROCESS_LOG"

# 1. Core Skills Mandate
if [ -f "$MEMORY_DIR/core-skills-mandate.md" ]; then
    log_policy "core-skills-mandate" "LOADED" "Mandatory skills hierarchy active"
else
    log_policy "core-skills-mandate" "MISSING" "File not found!"
fi

# 2. Context Management
if [ -f "$MEMORY_DIR/context-management-core.md" ]; then
    log_policy "context-management" "LOADED" "Context validation enforced"
else
    log_policy "context-management" "MISSING" "File not found!"
fi

# 3. Model Selection
if [ -f "$MEMORY_DIR/model-selection-enforcement.md" ]; then
    log_policy "model-selection" "LOADED" "Haiku/Sonnet/Opus routing active"
else
    log_policy "model-selection" "MISSING" "File not found!"
fi

# 4. File Management
if [ -f "$MEMORY_DIR/file-management-policy.md" ]; then
    log_policy "file-management" "LOADED" "Temp files & doc consolidation enforced"
else
    log_policy "file-management" "MISSING" "File not found!"
fi

# 5. Failure Prevention
if [ -f "$MEMORY_DIR/common-failures-prevention.md" ]; then
    log_policy "failure-prevention" "LOADED" "Self-learning KB active"
else
    log_policy "failure-prevention" "MISSING" "File not found!"
fi

# 6. Git Auto-Commit
if [ -f "$MEMORY_DIR/git-auto-commit-policy.md" ]; then
    log_policy "git-auto-commit" "LOADED" "Auto-commit on phase/todo completion"
else
    log_policy "git-auto-commit" "MISSING" "File not found!"
fi

# 7. Test Case Policy
if [ -f "$MEMORY_DIR/test-case-policy.md" ]; then
    log_policy "test-case-policy" "LOADED" "User preference for tests active"
else
    log_policy "test-case-policy" "MISSING" "File not found!"
fi

# 8. Adaptive Skill Registry
if [ -f "$MEMORY_DIR/adaptive-skill-registry.md" ]; then
    log_policy "adaptive-skill-registry" "LOADED" "Skill/agent lifecycle tracking"
else
    log_policy "adaptive-skill-registry" "MISSING" "File not found!"
fi

# Generate status summary
echo "" >> "$PROCESS_LOG"
echo "=== SYSTEM STATUS ===" >> "$PROCESS_LOG"
echo "[$timestamp] Memory policies loaded and ready for enforcement" >> "$PROCESS_LOG"
echo "[$timestamp] Log location: $PROCESS_LOG" >> "$PROCESS_LOG"
echo "" >> "$PROCESS_LOG"

# Create status dashboard
cat > "$STATUS_LOG" <<EOF
╔════════════════════════════════════════════════════════════╗
║          CLAUDE CODE MEMORY SYSTEM STATUS                 ║
╠════════════════════════════════════════════════════════════╣
║  Last Updated: $timestamp
╠════════════════════════════════════════════════════════════╣
║  ACTIVE POLICIES:
║
║  ✓ Core Skills Mandate          (Priority: HIGHEST)
║  ✓ Context Management           (Auto cleanup enabled)
║  ✓ Model Selection              (Haiku/Sonnet/Opus routing)
║  ✓ File Management              (Temp files + doc consolidation)
║  ✓ Failure Prevention           (Self-learning KB)
║  ✓ Git Auto-Commit              (Phase/todo triggers)
║  ✓ Test Case Policy             (User preference)
║  ✓ Adaptive Skill Registry      (Auto skill/agent management)
║
╠════════════════════════════════════════════════════════════╣
║  EXECUTION LOGS:
║
║  Process Log: $LOG_DIR/process-execution.log
║  Policy Hits: $LOG_DIR/policy-hits.log
║  Failures:    $LOG_DIR/failures.log
║
╠════════════════════════════════════════════════════════════╣
║  MONITORING:
║
║  tail -f $LOG_DIR/process-execution.log
║
╚════════════════════════════════════════════════════════════╝
EOF

# Display status
cat "$STATUS_LOG"

# Initialize policy hit counter
cat > "$LOG_DIR/policy-hits.log" <<EOF
# Policy Execution Counter
# Format: [timestamp] POLICY_NAME | ACTION | CONTEXT

EOF

# Initialize failures log
cat > "$LOG_DIR/failures.log" <<EOF
# Failure Detection & Prevention Log
# Format: [timestamp] FAILURE_TYPE | PREVENTED | DETAILS

EOF

echo ""
echo "✅ Memory system initialized!"
echo "📊 View status: cat $STATUS_LOG"
echo "📝 Monitor logs: tail -f $PROCESS_LOG"

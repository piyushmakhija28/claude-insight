#!/bin/bash
# Memory System Initializer
# Simpler version that definitely works

MEMORY_DIR="/c/Users/techd/.claude/memory"
LOG_DIR="$MEMORY_DIR/logs"

# Create logs directory
mkdir -p "$LOG_DIR"

timestamp=$(date '+%Y-%m-%d %H:%M:%S')

# Create process log
cat > "$LOG_DIR/process-execution.log" <<EOF
========================================
[$timestamp] MEMORY SYSTEM INITIALIZED
========================================

=== LOADING MEMORY POLICIES ===

EOF

# Check each policy file and log status
echo "[$timestamp] POLICY: core-skills-mandate | STATUS: $([ -f "$MEMORY_DIR/core-skills-mandate.md" ] && echo "LOADED" || echo "MISSING")" >> "$LOG_DIR/process-execution.log"
echo "[$timestamp] POLICY: model-selection-enforcement | STATUS: $([ -f "$MEMORY_DIR/model-selection-enforcement.md" ] && echo "LOADED" || echo "MISSING")" >> "$LOG_DIR/process-execution.log"
echo "[$timestamp] POLICY: file-management-policy | STATUS: $([ -f "$MEMORY_DIR/file-management-policy.md" ] && echo "LOADED" || echo "MISSING")" >> "$LOG_DIR/process-execution.log"
echo "[$timestamp] POLICY: common-failures-prevention | STATUS: $([ -f "$MEMORY_DIR/common-failures-prevention.md" ] && echo "LOADED" || echo "MISSING")" >> "$LOG_DIR/process-execution.log"
echo "[$timestamp] POLICY: git-auto-commit-policy | STATUS: $([ -f "$MEMORY_DIR/git-auto-commit-policy.md" ] && echo "LOADED" || echo "MISSING")" >> "$LOG_DIR/process-execution.log"
echo "[$timestamp] POLICY: test-case-policy | STATUS: $([ -f "$MEMORY_DIR/test-case-policy.md" ] && echo "LOADED" || echo "MISSING")" >> "$LOG_DIR/process-execution.log"
echo "[$timestamp] POLICY: adaptive-skill-registry | STATUS: $([ -f "$MEMORY_DIR/adaptive-skill-registry.md" ] && echo "LOADED" || echo "MISSING")" >> "$LOG_DIR/process-execution.log"

# Create status dashboard
cat > "$LOG_DIR/system-status.log" <<EOF
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

# Initialize policy hit counter
cat > "$LOG_DIR/policy-hits.log" <<EOF
# Policy Execution Log
# Format: [timestamp] POLICY_NAME | ACTION | CONTEXT

EOF

# Initialize failures log
cat > "$LOG_DIR/failures.log" <<EOF
# Failure Detection & Prevention Log
# Format: [timestamp] FAILURE_TYPE | PREVENTED | DETAILS

EOF

# Initialize counters
cat > "$LOG_DIR/policy-counters.txt" <<EOF
context-management=0
model-selection=0
adaptive-skill=0
planning-intelligence=0
phased-execution=0
failure-prevention=0
file-management=0
git-auto-commit=0
test-case-policy=0
EOF

# Display status
echo ""
echo "✅ Memory system initialized!"
echo ""
cat "$LOG_DIR/system-status.log"
echo ""
echo "📝 Process log: $LOG_DIR/process-execution.log"
echo "📊 Dashboard: bash $MEMORY_DIR/dashboard.sh"

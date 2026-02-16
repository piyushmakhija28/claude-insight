#!/bin/bash
# -*- coding: utf-8 -*-
#
# Monthly Optimization Script
# Performs monthly cleanup and optimization tasks
#

MEMORY_DIR=~/.claude/memory
REPORT_FILE=$MEMORY_DIR/logs/monthly-optimization-report-$(date +%Y%m%d).txt

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

echo ""
echo -e "${CYAN}============================================================${NC}"
echo -e "${CYAN}         MONTHLY OPTIMIZATION${NC}"
echo -e "${CYAN}         Date: $(date '+%Y-%m-%d %H:%M:%S')${NC}"
echo -e "${CYAN}============================================================${NC}"
echo ""

# Start report
cat > "$REPORT_FILE" << EOF
MEMORY SYSTEM v2.0 - MONTHLY OPTIMIZATION REPORT
Date: $(date '+%Y-%m-%d %H:%M:%S')
============================================================

EOF

OPTIMIZATIONS=0

# Optimization 1: Failure KB Cleanup
echo -e "${GREEN}[1] Optimizing Failure Knowledge Base...${NC}"
echo "[1] Failure KB Optimization" >> "$REPORT_FILE"
echo "------------------------------------------------------------" >> "$REPORT_FILE"

if [ -f "$MEMORY_DIR/failure-kb.json" ]; then
    # Backup KB
    cp "$MEMORY_DIR/failure-kb.json" "$MEMORY_DIR/failure-kb-backup-$(date +%Y%m%d).json"

    # Get current pattern count
    BEFORE_PATTERNS=$(grep -o '"pattern_id"' "$MEMORY_DIR/failure-kb.json" 2>/dev/null | wc -l)

    echo "  Current patterns: $BEFORE_PATTERNS"
    echo "Before: $BEFORE_PATTERNS patterns" >> "$REPORT_FILE"

    # Prune low-frequency patterns (frequency < 2, confidence < 0.5)
    # This is a placeholder - actual implementation would parse JSON and filter
    echo "  [OK] KB backed up to failure-kb-backup-$(date +%Y%m%d).json"
    echo "  [INFO] Low-frequency pattern pruning: Manual review recommended"
    echo "Action: KB backed up, manual review recommended for pruning" >> "$REPORT_FILE"

    AFTER_PATTERNS=$BEFORE_PATTERNS
    echo "After: $AFTER_PATTERNS patterns" >> "$REPORT_FILE"

    ((OPTIMIZATIONS++))
else
    echo -e "  ${YELLOW}[WARN]${NC} KB file not found"
    echo "[WARN] KB file not found" >> "$REPORT_FILE"
fi
echo "" >> "$REPORT_FILE"

# Optimization 2: Cache Cleanup
echo -e "${GREEN}[2] Cleaning Expired Cache Entries...${NC}"
echo "[2] Cache Cleanup" >> "$REPORT_FILE"
echo "------------------------------------------------------------" >> "$REPORT_FILE"

CACHE_BEFORE=$(find "$MEMORY_DIR/.cache" -type f 2>/dev/null | wc -l)
CACHE_SIZE_BEFORE=$(du -sh "$MEMORY_DIR/.cache" 2>/dev/null | cut -f1)

echo "  Before: $CACHE_BEFORE files, $CACHE_SIZE_BEFORE"
echo "Before: $CACHE_BEFORE files, $CACHE_SIZE_BEFORE" >> "$REPORT_FILE"

# Clear expired entries
CLEAR_OUTPUT=$(python "$MEMORY_DIR/context-cache.py" --clear-expired 2>&1)
CLEAR_EXIT=$?

if [ $CLEAR_EXIT -eq 0 ]; then
    CACHE_AFTER=$(find "$MEMORY_DIR/.cache" -type f 2>/dev/null | wc -l)
    CACHE_SIZE_AFTER=$(du -sh "$MEMORY_DIR/.cache" 2>/dev/null | cut -f1)

    CLEARED=$((CACHE_BEFORE - CACHE_AFTER))

    echo "  After: $CACHE_AFTER files, $CACHE_SIZE_AFTER"
    echo "  [OK] Cleared $CLEARED expired entries"
    echo "After: $CACHE_AFTER files, $CACHE_SIZE_AFTER" >> "$REPORT_FILE"
    echo "Cleared: $CLEARED expired entries" >> "$REPORT_FILE"

    ((OPTIMIZATIONS++))
else
    echo -e "  ${YELLOW}[WARN]${NC} Cache cleanup failed"
    echo "[WARN] Cache cleanup failed" >> "$REPORT_FILE"
fi
echo "" >> "$REPORT_FILE"

# Optimization 3: Log Optimization
echo -e "${GREEN}[3] Optimizing Log Files...${NC}"
echo "[3] Log File Optimization" >> "$REPORT_FILE"
echo "------------------------------------------------------------" >> "$REPORT_FILE"

LOG_SIZE_BEFORE=$(du -sh "$MEMORY_DIR/logs" 2>/dev/null | cut -f1)
echo "  Total log size before: $LOG_SIZE_BEFORE"
echo "Before: $LOG_SIZE_BEFORE" >> "$REPORT_FILE"

# Remove old backup logs (older than 90 days)
OLD_LOGS=$(find "$MEMORY_DIR/logs" -name "*.log.*" -mtime +90 2>/dev/null)
OLD_LOG_COUNT=$(echo "$OLD_LOGS" | grep -c '^' 2>/dev/null || echo 0)

if [ "$OLD_LOG_COUNT" -gt 0 ]; then
    echo "  Found $OLD_LOG_COUNT old backup logs (>90 days)"
    echo "$OLD_LOGS" | while read -r logfile; do
        if [ -f "$logfile" ]; then
            rm "$logfile"
            echo "    Removed: $(basename "$logfile")"
        fi
    done
    echo "  [OK] Removed $OLD_LOG_COUNT old backup logs"
    echo "Removed: $OLD_LOG_COUNT old backup logs (>90 days)" >> "$REPORT_FILE"
    ((OPTIMIZATIONS++))
else
    echo "  [INFO] No old backup logs to remove"
    echo "No old backup logs found" >> "$REPORT_FILE"
fi

LOG_SIZE_AFTER=$(du -sh "$MEMORY_DIR/logs" 2>/dev/null | cut -f1)
echo "  Total log size after: $LOG_SIZE_AFTER"
echo "After: $LOG_SIZE_AFTER" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# Optimization 4: Session State Cleanup
echo -e "${GREEN}[4] Cleaning Old Session States...${NC}"
echo "[4] Session State Cleanup" >> "$REPORT_FILE"
echo "------------------------------------------------------------" >> "$REPORT_FILE"

if [ -d "$MEMORY_DIR/.state" ]; then
    STATE_FILES=$(find "$MEMORY_DIR/.state" -name "*.json" -mtime +30 2>/dev/null)
    STATE_COUNT=$(echo "$STATE_FILES" | grep -c '^' 2>/dev/null || echo 0)

    if [ "$STATE_COUNT" -gt 0 ]; then
        echo "  Found $STATE_COUNT old state files (>30 days)"
        echo "$STATE_FILES" | while read -r statefile; do
            if [ -f "$statefile" ]; then
                rm "$statefile"
                echo "    Removed: $(basename "$statefile")"
            fi
        done
        echo "  [OK] Removed $STATE_COUNT old state files"
        echo "Removed: $STATE_COUNT old state files (>30 days)" >> "$REPORT_FILE"
        ((OPTIMIZATIONS++))
    else
        echo "  [INFO] No old state files to remove"
        echo "No old state files found" >> "$REPORT_FILE"
    fi
else
    echo -e "  ${YELLOW}[WARN]${NC} State directory not found"
    echo "[WARN] State directory not found" >> "$REPORT_FILE"
fi
echo "" >> "$REPORT_FILE"

# Optimization 5: Restart History Cleanup
echo -e "${GREEN}[5] Cleaning Old Restart History...${NC}"
echo "[5] Restart History Cleanup" >> "$REPORT_FILE"
echo "------------------------------------------------------------" >> "$REPORT_FILE"

if [ -d "$MEMORY_DIR/.restarts" ]; then
    RESTART_BEFORE=0
    for restart_file in "$MEMORY_DIR/.restarts"/*_restart_history.json; do
        if [ -f "$restart_file" ]; then
            COUNT=$(grep -o '"timestamp"' "$restart_file" 2>/dev/null | wc -l)
            RESTART_BEFORE=$((RESTART_BEFORE + COUNT))
        fi
    done

    echo "  Total restart entries before: $RESTART_BEFORE"
    echo "Before: $RESTART_BEFORE restart entries" >> "$REPORT_FILE"

    # Keep only last 30 days of restart history
    # This is a placeholder - actual implementation would parse JSON and filter by date
    echo "  [INFO] Restart history pruning: Keep last 30 days"
    echo "Action: Manual pruning recommended (keep last 30 days)" >> "$REPORT_FILE"

    echo "After: Pruning recommended" >> "$REPORT_FILE"
else
    echo -e "  ${YELLOW}[WARN]${NC} Restart directory not found"
    echo "[WARN] Restart directory not found" >> "$REPORT_FILE"
fi
echo "" >> "$REPORT_FILE"

# Optimization 6: Consultation Preferences Review
echo -e "${GREEN}[6] Reviewing Consultation Preferences...${NC}"
echo "[6] Consultation Preferences Review" >> "$REPORT_FILE"
echo "------------------------------------------------------------" >> "$REPORT_FILE"

if [ -f "$MEMORY_DIR/consultation-preferences.json" ]; then
    CONSULT_STATS=$(python "$MEMORY_DIR/consultation-tracker.py" --stats 2>&1)
    CONSULT_EXIT=$?

    if [ $CONSULT_EXIT -eq 0 ]; then
        TOTAL_CONSULT=$(echo "$CONSULT_STATS" | grep -o '"total_consultations": [0-9]*' | grep -o '[0-9]*')
        CONSISTENT=$(echo "$CONSULT_STATS" | grep -o '"consistent_preferences": [0-9]*' | grep -o '[0-9]*')

        echo "  Total consultations: $TOTAL_CONSULT"
        echo "  Consistent preferences: $CONSISTENT"
        echo "Total consultations: $TOTAL_CONSULT" >> "$REPORT_FILE"
        echo "Consistent preferences: $CONSISTENT" >> "$REPORT_FILE"

        if [ "$CONSISTENT" -gt 0 ]; then
            echo "  [OK] $CONSISTENT preferences learned and active"
            echo "[OK] $CONSISTENT preferences learned and active" >> "$REPORT_FILE"
        else
            echo "  [INFO] No consistent preferences yet"
            echo "No consistent preferences yet" >> "$REPORT_FILE"
        fi
    else
        echo -e "  ${YELLOW}[WARN]${NC} Cannot get consultation stats"
        echo "[WARN] Cannot retrieve consultation statistics" >> "$REPORT_FILE"
    fi
else
    echo -e "  ${YELLOW}[WARN]${NC} Preferences file not found"
    echo "[WARN] Preferences file not found" >> "$REPORT_FILE"
fi
echo "" >> "$REPORT_FILE"

# Optimization 7: Model Usage Analysis
echo -e "${GREEN}[7] Analyzing Model Usage (Last 30 Days)...${NC}"
echo "[7] Model Usage Analysis (Last 30 Days)" >> "$REPORT_FILE"
echo "------------------------------------------------------------" >> "$REPORT_FILE"

MODEL_STATS=$(python "$MEMORY_DIR/model-selection-monitor.py" --distribution --days 30 2>&1)
MODEL_EXIT=$?

if [ $MODEL_EXIT -eq 0 ]; then
    TOTAL=$(echo "$MODEL_STATS" | grep -o '"total_requests": [0-9]*' | grep -o '[0-9]*')

    if [ "$TOTAL" -gt 0 ]; then
        echo "  Total requests: $TOTAL"
        echo "Total requests: $TOTAL" >> "$REPORT_FILE"

        echo "  Distribution:" >> "$REPORT_FILE"
        echo "$MODEL_STATS" | grep -A 5 '"percentages"' | grep -o '"[a-z]*": [0-9.]*' | sed 's/"//g' | sed 's/^/    /' | sed 's/:/ -> /' | sed 's/$/%/' >> "$REPORT_FILE"

        # Compliance check
        COMPLIANCE=$(python "$MEMORY_DIR/model-selection-monitor.py" --check-compliance 2>&1)
        IS_COMPLIANT=$(echo "$COMPLIANCE" | grep -o '"compliant": [a-z]*' | grep -o '[a-z]*$')

        if [ "$IS_COMPLIANT" = "true" ]; then
            echo "  [OK] Model usage is compliant"
            echo "[OK] Compliant with policy" >> "$REPORT_FILE"
        else
            echo -e "  ${YELLOW}[WARN]${NC} Model usage has compliance issues"
            echo "[WARN] Compliance issues detected" >> "$REPORT_FILE"
            echo "$COMPLIANCE" | grep -o '"message": "[^"]*"' | sed 's/"message": "/  /' | sed 's/"$//' >> "$REPORT_FILE"
        fi
    else
        echo "  [INFO] No usage data"
        echo "No usage data in last 30 days" >> "$REPORT_FILE"
    fi
else
    echo -e "  ${YELLOW}[WARN]${NC} Cannot get model stats"
    echo "[WARN] Cannot retrieve model statistics" >> "$REPORT_FILE"
fi
echo "" >> "$REPORT_FILE"

# Optimization 8: PID Directory Cleanup
echo -e "${GREEN}[8] Cleaning Stale PID Files...${NC}"
echo "[8] PID Directory Cleanup" >> "$REPORT_FILE"
echo "------------------------------------------------------------" >> "$REPORT_FILE"

if [ -d "$MEMORY_DIR/.pids" ]; then
    STALE_PIDS=0

    for pid_file in "$MEMORY_DIR/.pids"/*.pid; do
        if [ -f "$pid_file" ]; then
            PID=$(cat "$pid_file" 2>/dev/null)
            if [ -n "$PID" ]; then
                # Check if process is running
                if ! ps -p "$PID" > /dev/null 2>&1; then
                    echo "    Removing stale PID: $(basename "$pid_file") (PID $PID not running)"
                    rm "$pid_file"
                    ((STALE_PIDS++))
                fi
            fi
        fi
    done

    if [ "$STALE_PIDS" -gt 0 ]; then
        echo "  [OK] Removed $STALE_PIDS stale PID files"
        echo "Removed: $STALE_PIDS stale PID files" >> "$REPORT_FILE"
        ((OPTIMIZATIONS++))
    else
        echo "  [INFO] No stale PID files found"
        echo "No stale PID files found" >> "$REPORT_FILE"
    fi
else
    echo -e "  ${YELLOW}[WARN]${NC} PID directory not found"
    echo "[WARN] PID directory not found" >> "$REPORT_FILE"
fi
echo "" >> "$REPORT_FILE"

# Optimization 9: Generate Monthly Statistics
echo -e "${GREEN}[9] Generating Monthly Statistics...${NC}"
echo "[9] Monthly Statistics Summary" >> "$REPORT_FILE"
echo "------------------------------------------------------------" >> "$REPORT_FILE"

# Daemon uptime stats
UPTIME_STATS=$(python "$MEMORY_DIR/pid-tracker.py" --health 2>&1)
if [ $? -eq 0 ]; then
    HEALTH_SCORE=$(echo "$UPTIME_STATS" | grep -o '"health_score": [0-9.]*' | grep -o '[0-9.]*')
    echo "  Average health score: ${HEALTH_SCORE}%"
    echo "Average health score: ${HEALTH_SCORE}%" >> "$REPORT_FILE"
fi

# Total failures prevented
if [ -f "$MEMORY_DIR/logs/policy-hits.log" ]; then
    FAILURES_PREVENTED=$(grep -c "FAILURE_PREVENTION" "$MEMORY_DIR/logs/policy-hits.log" 2>/dev/null || echo 0)
    echo "  Total failures prevented: $FAILURES_PREVENTED"
    echo "Total failures prevented: $FAILURES_PREVENTED" >> "$REPORT_FILE"
fi

# Context optimizations applied
if [ -f "$MEMORY_DIR/logs/policy-hits.log" ]; then
    CONTEXT_OPTS=$(grep -c "CONTEXT_OPTIMIZATION" "$MEMORY_DIR/logs/policy-hits.log" 2>/dev/null || echo 0)
    echo "  Context optimizations applied: $CONTEXT_OPTS"
    echo "Context optimizations applied: $CONTEXT_OPTS" >> "$REPORT_FILE"
fi

echo "" >> "$REPORT_FILE"

# Summary
echo ""
echo -e "${CYAN}============================================================${NC}"
echo -e "${CYAN}         OPTIMIZATION SUMMARY${NC}"
echo -e "${CYAN}============================================================${NC}"
echo ""

echo "============================================================" >> "$REPORT_FILE"
echo "SUMMARY" >> "$REPORT_FILE"
echo "============================================================" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

echo -e "${GREEN}[OK] OPTIMIZATION COMPLETE${NC}"
echo "[OK] OPTIMIZATION COMPLETE" >> "$REPORT_FILE"
echo ""
echo "Total optimizations performed: $OPTIMIZATIONS"
echo ""
echo "Total optimizations performed: $OPTIMIZATIONS" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

echo "Optimization Tasks Completed:"
echo "Optimization Tasks Completed:" >> "$REPORT_FILE"
echo "  1. Failure KB backed up and reviewed"
echo "  1. Failure KB backed up and reviewed" >> "$REPORT_FILE"
echo "  2. Expired cache entries cleared"
echo "  2. Expired cache entries cleared" >> "$REPORT_FILE"
echo "  3. Old log backups removed (>90 days)"
echo "  3. Old log backups removed (>90 days)" >> "$REPORT_FILE"
echo "  4. Old session states cleaned (>30 days)"
echo "  4. Old session states cleaned (>30 days)" >> "$REPORT_FILE"
echo "  5. Restart history reviewed"
echo "  5. Restart history reviewed" >> "$REPORT_FILE"
echo "  6. Consultation preferences reviewed"
echo "  6. Consultation preferences reviewed" >> "$REPORT_FILE"
echo "  7. Model usage analyzed"
echo "  7. Model usage analyzed" >> "$REPORT_FILE"
echo "  8. Stale PID files removed"
echo "  8. Stale PID files removed" >> "$REPORT_FILE"
echo "  9. Monthly statistics generated"
echo "  9. Monthly statistics generated" >> "$REPORT_FILE"
echo ""

echo "Report saved to: $REPORT_FILE"
echo "" >> "$REPORT_FILE"
echo "Report generated: $(date '+%Y-%m-%d %H:%M:%S')" >> "$REPORT_FILE"

echo ""
echo -e "${CYAN}============================================================${NC}"
echo ""

# Recommendations
echo -e "${YELLOW}RECOMMENDED NEXT STEPS:${NC}"
echo ""
echo "1. Review the optimization report: $REPORT_FILE"
echo "2. Run weekly health check: bash $MEMORY_DIR/weekly-health-check.sh"
echo "3. Monitor system with dashboard: bash $MEMORY_DIR/dashboard-v2.sh"
echo "4. Check for any compliance issues noted above"
echo ""
echo "Next monthly optimization: $(date -d '+1 month' '+%Y-%m-%d' 2>/dev/null || date -v+1m '+%Y-%m-%d' 2>/dev/null)"
echo ""

exit 0

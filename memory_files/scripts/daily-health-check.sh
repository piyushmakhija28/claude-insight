#!/bin/bash
# -*- coding: utf-8 -*-
#
# Daily Health Check Script
# Quick daily verification of critical system components
#

MEMORY_DIR=~/.claude/memory
REPORT_FILE=$MEMORY_DIR/logs/daily-health-report-$(date +%Y%m%d).txt

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

echo ""
echo -e "${CYAN}============================================================${NC}"
echo -e "${CYAN}         DAILY HEALTH CHECK${NC}"
echo -e "${CYAN}         Date: $(date '+%Y-%m-%d %H:%M:%S')${NC}"
echo -e "${CYAN}============================================================${NC}"
echo ""

# Start report
cat > "$REPORT_FILE" << EOF
MEMORY SYSTEM v2.0 - DAILY HEALTH REPORT
Date: $(date '+%Y-%m-%d %H:%M:%S')
============================================================

EOF

CRITICAL=0
WARNINGS=0

# Check 1: Daemon Health (Critical)
echo -e "${GREEN}[1] Checking Daemons...${NC}"
echo "[1] Daemon Health" >> "$REPORT_FILE"
echo "------------------------------------------------------------" >> "$REPORT_FILE"

DAEMON_STATUS=$(python "$MEMORY_DIR/daemon-manager.py" --status-all --format json 2>&1)
DAEMON_EXIT=$?

if [ $DAEMON_EXIT -eq 0 ]; then
    RUNNING=$(echo "$DAEMON_STATUS" | grep -o '"running": true' | wc -l)
    TOTAL=$(echo "$DAEMON_STATUS" | grep -o '"daemon"' | wc -l)

    if [ "$RUNNING" -eq "$TOTAL" ]; then
        echo -e "  ${GREEN}[OK]${NC} All daemons running ($RUNNING/$TOTAL)"
        echo "[OK] All $TOTAL daemons running" >> "$REPORT_FILE"
    else
        echo -e "  ${RED}[CRITICAL]${NC} Some daemons down ($RUNNING/$TOTAL)"
        echo "[CRITICAL] Only $RUNNING/$TOTAL daemons running" >> "$REPORT_FILE"

        # Show which daemons are down
        python "$MEMORY_DIR/daemon-manager.py" --status-all --format table 2>&1 | grep "NOT RUNNING" >> "$REPORT_FILE"
        ((CRITICAL++))
    fi
else
    echo -e "  ${RED}[CRITICAL]${NC} Cannot get daemon status"
    echo "[CRITICAL] Cannot retrieve daemon status" >> "$REPORT_FILE"
    ((CRITICAL++))
fi
echo "" >> "$REPORT_FILE"

# Check 2: Health Score
echo -e "${GREEN}[2] Checking Health Score...${NC}"
echo "[2] Health Score" >> "$REPORT_FILE"
echo "------------------------------------------------------------" >> "$REPORT_FILE"

HEALTH=$(python "$MEMORY_DIR/pid-tracker.py" --health 2>&1)
HEALTH_EXIT=$?

if [ $HEALTH_EXIT -eq 0 ]; then
    HEALTH_SCORE=$(echo "$HEALTH" | grep -o '"health_score": [0-9.]*' | grep -o '[0-9.]*')

    if [ -n "$HEALTH_SCORE" ]; then
        SCORE_INT=${HEALTH_SCORE%.*}

        if [ "$SCORE_INT" -ge 90 ]; then
            echo -e "  ${GREEN}[OK]${NC} Health: ${HEALTH_SCORE}% (Excellent)"
            echo "[OK] Health: ${HEALTH_SCORE}% (Excellent)" >> "$REPORT_FILE"
        elif [ "$SCORE_INT" -ge 70 ]; then
            echo -e "  ${YELLOW}[WARN]${NC} Health: ${HEALTH_SCORE}% (Good)"
            echo "[WARN] Health: ${HEALTH_SCORE}% (Good)" >> "$REPORT_FILE"
            ((WARNINGS++))
        else
            echo -e "  ${RED}[CRITICAL]${NC} Health: ${HEALTH_SCORE}% (Poor)"
            echo "[CRITICAL] Health: ${HEALTH_SCORE}% (Poor)" >> "$REPORT_FILE"
            ((CRITICAL++))
        fi
    else
        echo -e "  ${YELLOW}[WARN]${NC} Cannot parse health score"
        echo "[WARN] Cannot parse health score" >> "$REPORT_FILE"
        ((WARNINGS++))
    fi
else
    echo -e "  ${RED}[CRITICAL]${NC} Cannot get health score"
    echo "[CRITICAL] Cannot retrieve health score" >> "$REPORT_FILE"
    ((CRITICAL++))
fi
echo "" >> "$REPORT_FILE"

# Check 3: Recent Errors (Last 24 hours)
echo -e "${GREEN}[3] Checking Recent Errors...${NC}"
echo "[3] Recent Errors (Last 24 Hours)" >> "$REPORT_FILE"
echo "------------------------------------------------------------" >> "$REPORT_FILE"

# Count errors in logs from last 24 hours
ERROR_COUNT=0
if [ -d "$MEMORY_DIR/logs" ]; then
    # Check all log files for errors in last 24 hours
    for log_file in "$MEMORY_DIR/logs"/*.log; do
        if [ -f "$log_file" ]; then
            # Count ERROR lines from today
            TODAY_ERRORS=$(grep -i "ERROR\|CRITICAL\|FAIL" "$log_file" 2>/dev/null | grep "$(date +%Y-%m-%d)" | wc -l)
            ERROR_COUNT=$((ERROR_COUNT + TODAY_ERRORS))
        fi
    done

    if [ "$ERROR_COUNT" -eq 0 ]; then
        echo -e "  ${GREEN}[OK]${NC} No errors in last 24 hours"
        echo "[OK] No errors in last 24 hours" >> "$REPORT_FILE"
    elif [ "$ERROR_COUNT" -le 5 ]; then
        echo -e "  ${YELLOW}[WARN]${NC} $ERROR_COUNT errors in last 24 hours"
        echo "[WARN] $ERROR_COUNT errors in last 24 hours" >> "$REPORT_FILE"
        ((WARNINGS++))
    else
        echo -e "  ${RED}[CRITICAL]${NC} $ERROR_COUNT errors in last 24 hours (high)"
        echo "[CRITICAL] $ERROR_COUNT errors in last 24 hours" >> "$REPORT_FILE"

        # Show last 5 errors
        echo "  Last 5 errors:" >> "$REPORT_FILE"
        grep -i "ERROR\|CRITICAL\|FAIL" "$MEMORY_DIR/logs"/*.log 2>/dev/null | grep "$(date +%Y-%m-%d)" | tail -5 >> "$REPORT_FILE"
        ((CRITICAL++))
    fi
else
    echo -e "  ${YELLOW}[WARN]${NC} Logs directory not found"
    echo "[WARN] Logs directory not found" >> "$REPORT_FILE"
    ((WARNINGS++))
fi
echo "" >> "$REPORT_FILE"

# Check 4: Daemon Restarts (Last 24 hours)
echo -e "${GREEN}[4] Checking Daemon Restarts...${NC}"
echo "[4] Daemon Restarts (Last 24 Hours)" >> "$REPORT_FILE"
echo "------------------------------------------------------------" >> "$REPORT_FILE"

RESTART_COUNT=0
if [ -d "$MEMORY_DIR/.restarts" ]; then
    # Check restart files for today's date
    for restart_file in "$MEMORY_DIR/.restarts"/*_restart_history.json; do
        if [ -f "$restart_file" ]; then
            TODAY_RESTARTS=$(grep "$(date +%Y-%m-%d)" "$restart_file" 2>/dev/null | grep -o '"timestamp"' | wc -l)

            if [ "$TODAY_RESTARTS" -gt 0 ]; then
                DAEMON_NAME=$(basename "$restart_file" _restart_history.json)
                RESTART_COUNT=$((RESTART_COUNT + TODAY_RESTARTS))
                echo "  $DAEMON_NAME: $TODAY_RESTARTS restarts today" >> "$REPORT_FILE"
            fi
        fi
    done

    if [ "$RESTART_COUNT" -eq 0 ]; then
        echo -e "  ${GREEN}[OK]${NC} No restarts in last 24 hours"
        echo "[OK] No restarts in last 24 hours" >> "$REPORT_FILE"
    elif [ "$RESTART_COUNT" -le 2 ]; then
        echo -e "  ${YELLOW}[WARN]${NC} $RESTART_COUNT restarts in last 24 hours"
        echo "[WARN] $RESTART_COUNT restarts" >> "$REPORT_FILE"
        ((WARNINGS++))
    else
        echo -e "  ${RED}[CRITICAL]${NC} $RESTART_COUNT restarts in last 24 hours (high)"
        echo "[CRITICAL] Excessive restarts: $RESTART_COUNT" >> "$REPORT_FILE"
        ((CRITICAL++))
    fi
else
    echo -e "  ${YELLOW}[WARN]${NC} Restart directory not found"
    echo "[WARN] Restart directory not found" >> "$REPORT_FILE"
    ((WARNINGS++))
fi
echo "" >> "$REPORT_FILE"

# Check 5: Disk Space
echo -e "${GREEN}[5] Checking Disk Space...${NC}"
echo "[5] Disk Space" >> "$REPORT_FILE"
echo "------------------------------------------------------------" >> "$REPORT_FILE"

MEMORY_SIZE=$(du -sh "$MEMORY_DIR" 2>/dev/null | cut -f1)
LOG_SIZE=$(du -sh "$MEMORY_DIR/logs" 2>/dev/null | cut -f1)

echo "  Memory system size: $MEMORY_SIZE"
echo "  Logs size: $LOG_SIZE"
echo "Memory system size: $MEMORY_SIZE" >> "$REPORT_FILE"
echo "Logs size: $LOG_SIZE" >> "$REPORT_FILE"

# Check if any single log file is too large
LARGE_LOGS=$(find "$MEMORY_DIR/logs" -name "*.log" -size +50M 2>/dev/null)

if [ -z "$LARGE_LOGS" ]; then
    echo -e "  ${GREEN}[OK]${NC} All log files within limits"
    echo "[OK] All log files < 50MB" >> "$REPORT_FILE"
else
    echo -e "  ${YELLOW}[WARN]${NC} Large log files detected (>50MB)"
    echo "[WARN] Large log files detected:" >> "$REPORT_FILE"
    echo "$LARGE_LOGS" | while read -r logfile; do
        SIZE=$(du -h "$logfile" | cut -f1)
        echo "    $logfile ($SIZE)"
        echo "  $logfile ($SIZE)" >> "$REPORT_FILE"
    done
    ((WARNINGS++))
fi
echo "" >> "$REPORT_FILE"

# Check 6: Critical Failure KB
echo -e "${GREEN}[6] Checking Failure KB...${NC}"
echo "[6] Failure Knowledge Base" >> "$REPORT_FILE"
echo "------------------------------------------------------------" >> "$REPORT_FILE"

if [ -f "$MEMORY_DIR/failure-kb.json" ]; then
    KB_STATS=$(python "$MEMORY_DIR/pre-execution-checker.py" --stats 2>&1)
    KB_EXIT=$?

    if [ $KB_EXIT -eq 0 ]; then
        TOTAL_PATTERNS=$(echo "$KB_STATS" | grep -o '"total_patterns": [0-9]*' | grep -o '[0-9]*')

        if [ -n "$TOTAL_PATTERNS" ] && [ "$TOTAL_PATTERNS" -gt 0 ]; then
            echo -e "  ${GREEN}[OK]${NC} KB has $TOTAL_PATTERNS patterns"
            echo "[OK] $TOTAL_PATTERNS patterns loaded" >> "$REPORT_FILE"
        else
            echo -e "  ${YELLOW}[WARN]${NC} KB has no patterns"
            echo "[WARN] KB empty (no patterns)" >> "$REPORT_FILE"
            ((WARNINGS++))
        fi
    else
        echo -e "  ${YELLOW}[WARN]${NC} Cannot get KB stats"
        echo "[WARN] Cannot retrieve KB stats" >> "$REPORT_FILE"
        ((WARNINGS++))
    fi
else
    echo -e "  ${RED}[CRITICAL]${NC} KB file missing"
    echo "[CRITICAL] Failure KB file not found" >> "$REPORT_FILE"
    ((CRITICAL++))
fi
echo "" >> "$REPORT_FILE"

# Summary
echo ""
echo -e "${CYAN}============================================================${NC}"
echo -e "${CYAN}         DAILY HEALTH SUMMARY${NC}"
echo -e "${CYAN}============================================================${NC}"
echo ""

echo "============================================================" >> "$REPORT_FILE"
echo "SUMMARY" >> "$REPORT_FILE"
echo "============================================================" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

if [ $CRITICAL -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}[OK] SYSTEM HEALTHY${NC}"
    echo "[OK] SYSTEM HEALTHY" >> "$REPORT_FILE"
    echo ""
    echo "Status: ALL CHECKS PASSED"
    echo "  - No critical issues"
    echo "  - No warnings"
    echo "  - All systems operational"
    echo ""
    echo "Status: ALL CHECKS PASSED" >> "$REPORT_FILE"
    echo "  - No critical issues" >> "$REPORT_FILE"
    echo "  - No warnings" >> "$REPORT_FILE"
elif [ $CRITICAL -eq 0 ]; then
    echo -e "${YELLOW}[WARN] MINOR ISSUES DETECTED${NC}"
    echo "[WARN] MINOR ISSUES DETECTED" >> "$REPORT_FILE"
    echo ""
    echo "Status: GOOD (with warnings)"
    echo "  - No critical issues"
    echo "  - $WARNINGS warnings detected"
    echo "  - System operational"
    echo ""
    echo "Status: GOOD (with warnings)" >> "$REPORT_FILE"
    echo "  - Warnings: $WARNINGS" >> "$REPORT_FILE"
else
    echo -e "${RED}[CRITICAL] IMMEDIATE ATTENTION REQUIRED${NC}"
    echo "[CRITICAL] IMMEDIATE ATTENTION REQUIRED" >> "$REPORT_FILE"
    echo ""
    echo "Status: NEEDS IMMEDIATE ATTENTION"
    echo "  - Critical Issues: $CRITICAL"
    echo "  - Warnings: $WARNINGS"
    echo "  - Review issues above immediately"
    echo ""
    echo "Status: NEEDS IMMEDIATE ATTENTION" >> "$REPORT_FILE"
    echo "  - Critical Issues: $CRITICAL" >> "$REPORT_FILE"
    echo "  - Warnings: $WARNINGS" >> "$REPORT_FILE"
fi

echo "Report saved to: $REPORT_FILE"
echo "" >> "$REPORT_FILE"
echo "Report generated: $(date '+%Y-%m-%d %H:%M:%S')" >> "$REPORT_FILE"

echo ""
echo -e "${CYAN}============================================================${NC}"
echo ""

# Quick Actions
if [ $CRITICAL -gt 0 ]; then
    echo -e "${RED}IMMEDIATE ACTIONS REQUIRED:${NC}"
    echo ""

    if [ $CRITICAL -gt 0 ]; then
        echo "1. Check critical issues in report: $REPORT_FILE"
        echo "2. View full dashboard: bash $MEMORY_DIR/dashboard-v2.sh"
        echo "3. Check daemon status: python $MEMORY_DIR/daemon-manager.py --status-all"
        echo "4. Restart daemons if needed: bash $MEMORY_DIR/startup-hook-v2.sh"
        echo "5. Review recent logs: tail -50 $MEMORY_DIR/logs/health.log"
    fi

    echo ""
elif [ $WARNINGS -gt 0 ]; then
    echo -e "${YELLOW}RECOMMENDED ACTIONS:${NC}"
    echo ""
    echo "1. Review warnings in report: $REPORT_FILE"
    echo "2. Monitor with dashboard: bash $MEMORY_DIR/dashboard-v2.sh"
    echo "3. Consider running weekly check: bash $MEMORY_DIR/weekly-health-check.sh"
    echo ""
fi

# Exit code
if [ $CRITICAL -gt 0 ]; then
    exit 2  # Critical issues
elif [ $WARNINGS -gt 0 ]; then
    exit 1  # Warnings only
else
    exit 0  # All good
fi

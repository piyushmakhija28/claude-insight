#!/bin/bash
# -*- coding: utf-8 -*-
#
# Weekly Health Check Script
# Performs comprehensive system health verification
#

MEMORY_DIR=~/.claude/memory
REPORT_FILE=$MEMORY_DIR/logs/weekly-health-report-$(date +%Y%m%d).txt

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

echo ""
echo -e "${CYAN}============================================================${NC}"
echo -e "${CYAN}         WEEKLY HEALTH CHECK${NC}"
echo -e "${CYAN}         Date: $(date '+%Y-%m-%d %H:%M:%S')${NC}"
echo -e "${CYAN}============================================================${NC}"
echo ""

# Start report
cat > "$REPORT_FILE" << EOF
MEMORY SYSTEM v2.0 - WEEKLY HEALTH REPORT
Date: $(date '+%Y-%m-%d %H:%M:%S')
============================================================

EOF

ISSUES=0
WARNINGS=0

# Check 1: System Verification
echo -e "${GREEN}[1] Running System Verification...${NC}"
echo "[1] System Verification" >> "$REPORT_FILE"
echo "------------------------------------------------------------" >> "$REPORT_FILE"

VERIFY_OUTPUT=$(bash "$MEMORY_DIR/verify-system.sh" 2>&1)
VERIFY_EXIT=$?

if [ $VERIFY_EXIT -eq 0 ]; then
    echo -e "  ${GREEN}[OK]${NC} System verification passed"
    echo "[OK] All verification checks passed" >> "$REPORT_FILE"
else
    echo -e "  ${RED}[FAIL]${NC} System verification failed"
    echo "[FAIL] Verification failed:" >> "$REPORT_FILE"
    echo "$VERIFY_OUTPUT" >> "$REPORT_FILE"
    ((ISSUES++))
fi
echo "" >> "$REPORT_FILE"

# Check 2: Daemon Health
echo -e "${GREEN}[2] Checking Daemon Health...${NC}"
echo "[2] Daemon Health" >> "$REPORT_FILE"
echo "------------------------------------------------------------" >> "$REPORT_FILE"

DAEMON_STATUS=$(python "$MEMORY_DIR/daemon-manager.py" --status-all --format json 2>&1)
DAEMON_EXIT=$?

if [ $DAEMON_EXIT -eq 0 ]; then
    RUNNING=$(echo "$DAEMON_STATUS" | grep -o '"running": true' | wc -l)
    TOTAL=$(echo "$DAEMON_STATUS" | grep -o '"daemon"' | wc -l)

    if [ "$RUNNING" -eq "$TOTAL" ]; then
        echo -e "  ${GREEN}[OK]${NC} All daemons healthy ($RUNNING/$TOTAL)"
        echo "[OK] All $TOTAL daemons running" >> "$REPORT_FILE"
    else
        echo -e "  ${YELLOW}[WARN]${NC} Some daemons not running ($RUNNING/$TOTAL)"
        echo "[WARN] Only $RUNNING/$TOTAL daemons running" >> "$REPORT_FILE"
        python "$MEMORY_DIR/daemon-manager.py" --status-all --format table >> "$REPORT_FILE"
        ((WARNINGS++))
    fi
else
    echo -e "  ${RED}[FAIL]${NC} Cannot get daemon status"
    echo "[FAIL] Cannot retrieve daemon status" >> "$REPORT_FILE"
    ((ISSUES++))
fi
echo "" >> "$REPORT_FILE"

# Check 3: Health Score
echo -e "${GREEN}[3] Checking Health Score...${NC}"
echo "[3] Health Score" >> "$REPORT_FILE"
echo "------------------------------------------------------------" >> "$REPORT_FILE"

HEALTH=$(python "$MEMORY_DIR/pid-tracker.py" --health 2>&1)
HEALTH_EXIT=$?

if [ $HEALTH_EXIT -eq 0 ]; then
    HEALTH_SCORE=$(echo "$HEALTH" | grep -o '"health_score": [0-9.]*' | grep -o '[0-9.]*')

    if [ -n "$HEALTH_SCORE" ]; then
        SCORE_INT=${HEALTH_SCORE%.*}

        if [ "$SCORE_INT" -ge 90 ]; then
            echo -e "  ${GREEN}[OK]${NC} Health score: ${HEALTH_SCORE}% (Excellent)"
            echo "[OK] Health score: ${HEALTH_SCORE}% (Excellent)" >> "$REPORT_FILE"
        elif [ "$SCORE_INT" -ge 70 ]; then
            echo -e "  ${YELLOW}[WARN]${NC} Health score: ${HEALTH_SCORE}% (Good)"
            echo "[WARN] Health score: ${HEALTH_SCORE}% (Good)" >> "$REPORT_FILE"
            ((WARNINGS++))
        else
            echo -e "  ${RED}[FAIL]${NC} Health score: ${HEALTH_SCORE}% (Poor)"
            echo "[FAIL] Health score: ${HEALTH_SCORE}% (Poor)" >> "$REPORT_FILE"
            ((ISSUES++))
        fi
    else
        echo -e "  ${YELLOW}[WARN]${NC} Cannot parse health score"
        echo "[WARN] Cannot parse health score" >> "$REPORT_FILE"
        ((WARNINGS++))
    fi
else
    echo -e "  ${RED}[FAIL]${NC} Cannot get health score"
    echo "[FAIL] Cannot retrieve health score" >> "$REPORT_FILE"
    ((ISSUES++))
fi
echo "" >> "$REPORT_FILE"

# Check 4: Log File Sizes
echo -e "${GREEN}[4] Checking Log File Sizes...${NC}"
echo "[4] Log File Sizes" >> "$REPORT_FILE"
echo "------------------------------------------------------------" >> "$REPORT_FILE"

LARGE_LOGS=$(find "$MEMORY_DIR/logs" -name "*.log" -size +20M 2>/dev/null)

if [ -z "$LARGE_LOGS" ]; then
    echo -e "  ${GREEN}[OK]${NC} All log files within limits"
    echo "[OK] All log files < 20MB (rotation working)" >> "$REPORT_FILE"
else
    echo -e "  ${YELLOW}[WARN]${NC} Large log files found:"
    echo "[WARN] Large log files (>20MB):" >> "$REPORT_FILE"
    echo "$LARGE_LOGS" | while read -r logfile; do
        SIZE=$(du -h "$logfile" | cut -f1)
        echo "    $logfile ($SIZE)"
        echo "  $logfile ($SIZE)" >> "$REPORT_FILE"
    done
    ((WARNINGS++))
fi

# Total log size
TOTAL_LOG_SIZE=$(du -sh "$MEMORY_DIR/logs" 2>/dev/null | cut -f1)
echo "  Total log size: $TOTAL_LOG_SIZE"
echo "Total log directory size: $TOTAL_LOG_SIZE" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# Check 5: Failure KB Stats
echo -e "${GREEN}[5] Checking Failure Knowledge Base...${NC}"
echo "[5] Failure Knowledge Base" >> "$REPORT_FILE"
echo "------------------------------------------------------------" >> "$REPORT_FILE"

KB_STATS=$(python "$MEMORY_DIR/pre-execution-checker.py" --stats 2>&1)
KB_EXIT=$?

if [ $KB_EXIT -eq 0 ]; then
    TOTAL_PATTERNS=$(echo "$KB_STATS" | grep -o '"total_patterns": [0-9]*' | grep -o '[0-9]*')
    HIGH_CONF=$(echo "$KB_STATS" | grep -o '"high_confidence": [0-9]*' | grep -o '[0-9]*')

    if [ -n "$TOTAL_PATTERNS" ]; then
        echo -e "  ${GREEN}[OK]${NC} KB has $TOTAL_PATTERNS patterns ($HIGH_CONF high confidence)"
        echo "[OK] $TOTAL_PATTERNS patterns ($HIGH_CONF high confidence)" >> "$REPORT_FILE"

        # Show by tool
        echo "  Patterns by tool:" >> "$REPORT_FILE"
        echo "$KB_STATS" | grep -A 10 '"by_tool"' | grep -o '"[A-Za-z]*": [0-9]*' | sed 's/"//g' | sed 's/^/    /' >> "$REPORT_FILE"
    else
        echo -e "  ${YELLOW}[WARN]${NC} Cannot parse KB stats"
        echo "[WARN] Cannot parse KB statistics" >> "$REPORT_FILE"
        ((WARNINGS++))
    fi
else
    echo -e "  ${RED}[FAIL]${NC} Cannot get KB stats"
    echo "[FAIL] Cannot retrieve KB statistics" >> "$REPORT_FILE"
    ((ISSUES++))
fi
echo "" >> "$REPORT_FILE"

# Check 6: Model Usage Distribution
echo -e "${GREEN}[6] Checking Model Usage Distribution...${NC}"
echo "[6] Model Usage Distribution (Last 7 Days)" >> "$REPORT_FILE"
echo "------------------------------------------------------------" >> "$REPORT_FILE"

MODEL_STATS=$(python "$MEMORY_DIR/model-selection-monitor.py" --distribution --days 7 2>&1)
MODEL_EXIT=$?

if [ $MODEL_EXIT -eq 0 ]; then
    TOTAL=$(echo "$MODEL_STATS" | grep -o '"total_requests": [0-9]*' | grep -o '[0-9]*')

    if [ "$TOTAL" -gt 0 ]; then
        echo -e "  ${GREEN}[OK]${NC} $TOTAL requests in last 7 days"
        echo "[OK] Total requests: $TOTAL" >> "$REPORT_FILE"

        # Show distribution
        echo "  Distribution:" >> "$REPORT_FILE"
        echo "$MODEL_STATS" | grep -A 5 '"percentages"' | grep -o '"[a-z]*": [0-9.]*' | sed 's/"//g' | sed 's/^/    /' | sed 's/:/ -> /' | sed 's/$/%/' >> "$REPORT_FILE"

        # Check compliance
        COMPLIANCE=$(python "$MEMORY_DIR/model-selection-monitor.py" --check-compliance 2>&1)
        IS_COMPLIANT=$(echo "$COMPLIANCE" | grep -o '"compliant": [a-z]*' | grep -o '[a-z]*$')

        if [ "$IS_COMPLIANT" = "true" ]; then
            echo -e "  ${GREEN}[OK]${NC} Model usage is compliant"
            echo "[OK] Model usage is compliant with policy" >> "$REPORT_FILE"
        else
            echo -e "  ${YELLOW}[WARN]${NC} Model usage compliance issues"
            echo "[WARN] Model usage has compliance issues:" >> "$REPORT_FILE"
            echo "$COMPLIANCE" | grep -o '"message": "[^"]*"' | sed 's/"message": "/  /' | sed 's/"$//' >> "$REPORT_FILE"
            ((WARNINGS++))
        fi
    else
        echo -e "  ${YELLOW}[WARN]${NC} No usage data in last 7 days"
        echo "[WARN] No usage data found" >> "$REPORT_FILE"
        ((WARNINGS++))
    fi
else
    echo -e "  ${YELLOW}[WARN]${NC} Cannot get model stats"
    echo "[WARN] Cannot retrieve model statistics" >> "$REPORT_FILE"
    ((WARNINGS++))
fi
echo "" >> "$REPORT_FILE"

# Check 7: Cache Statistics
echo -e "${GREEN}[7] Checking Cache Statistics...${NC}"
echo "[7] Cache Statistics" >> "$REPORT_FILE"
echo "------------------------------------------------------------" >> "$REPORT_FILE"

CACHE_STATS=$(python "$MEMORY_DIR/context-cache.py" --stats 2>&1)
CACHE_EXIT=$?

if [ $CACHE_EXIT -eq 0 ]; then
    CACHE_ENTRIES=$(echo "$CACHE_STATS" | grep -o '"summary_cache_entries": [0-9]*' | grep -o '[0-9]*')
    CACHE_SIZE=$(echo "$CACHE_STATS" | grep -o '"total_size_mb": [0-9.]*' | grep -o '[0-9.]*')

    if [ -n "$CACHE_ENTRIES" ]; then
        echo -e "  ${GREEN}[OK]${NC} Cache: $CACHE_ENTRIES entries, ${CACHE_SIZE}MB"
        echo "[OK] $CACHE_ENTRIES cached entries, ${CACHE_SIZE}MB" >> "$REPORT_FILE"

        # Check cache size
        if [ $(echo "$CACHE_SIZE > 80" | bc 2>/dev/null || echo 0) -eq 1 ]; then
            echo -e "  ${YELLOW}[WARN]${NC} Cache size near limit (${CACHE_SIZE}MB / 100MB)"
            echo "[WARN] Cache approaching size limit (${CACHE_SIZE}MB / 100MB)" >> "$REPORT_FILE"
            ((WARNINGS++))
        fi
    else
        echo -e "  ${YELLOW}[WARN]${NC} Cannot parse cache stats"
        echo "[WARN] Cannot parse cache statistics" >> "$REPORT_FILE"
        ((WARNINGS++))
    fi
else
    echo -e "  ${YELLOW}[WARN]${NC} Cannot get cache stats"
    echo "[WARN] Cannot retrieve cache statistics" >> "$REPORT_FILE"
    ((WARNINGS++))
fi
echo "" >> "$REPORT_FILE"

# Check 8: Restart History
echo -e "${GREEN}[8] Checking Restart History...${NC}"
echo "[8] Daemon Restart History (Last 7 Days)" >> "$REPORT_FILE"
echo "------------------------------------------------------------" >> "$REPORT_FILE"

RESTART_COUNT=0
if [ -d "$MEMORY_DIR/.restarts" ]; then
    # Count restarts in last 7 days
    SEVEN_DAYS_AGO=$(date -d '7 days ago' +%s 2>/dev/null || date -v-7d +%s 2>/dev/null)

    for restart_file in "$MEMORY_DIR/.restarts"/*_restart_history.json; do
        if [ -f "$restart_file" ]; then
            DAEMON_NAME=$(basename "$restart_file" _restart_history.json)
            DAEMON_RESTARTS=$(grep -o '"timestamp"' "$restart_file" 2>/dev/null | wc -l)

            if [ "$DAEMON_RESTARTS" -gt 0 ]; then
                RESTART_COUNT=$((RESTART_COUNT + DAEMON_RESTARTS))
                echo "  $DAEMON_NAME: $DAEMON_RESTARTS restarts" >> "$REPORT_FILE"
            fi
        fi
    done

    if [ "$RESTART_COUNT" -eq 0 ]; then
        echo -e "  ${GREEN}[OK]${NC} No daemon restarts in last 7 days"
        echo "[OK] No daemon restarts" >> "$REPORT_FILE"
    elif [ "$RESTART_COUNT" -le 3 ]; then
        echo -e "  ${YELLOW}[WARN]${NC} $RESTART_COUNT daemon restarts in last 7 days"
        echo "[WARN] $RESTART_COUNT daemon restarts" >> "$REPORT_FILE"
        ((WARNINGS++))
    else
        echo -e "  ${RED}[FAIL]${NC} $RESTART_COUNT daemon restarts in last 7 days (excessive)"
        echo "[FAIL] Excessive restarts: $RESTART_COUNT" >> "$REPORT_FILE"
        ((ISSUES++))
    fi
else
    echo -e "  ${YELLOW}[WARN]${NC} Restart directory not found"
    echo "[WARN] Restart history directory not found" >> "$REPORT_FILE"
    ((WARNINGS++))
fi
echo "" >> "$REPORT_FILE"

# Summary
echo ""
echo -e "${CYAN}============================================================${NC}"
echo -e "${CYAN}         HEALTH CHECK SUMMARY${NC}"
echo -e "${CYAN}============================================================${NC}"
echo ""

echo "============================================================" >> "$REPORT_FILE"
echo "SUMMARY" >> "$REPORT_FILE"
echo "============================================================" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

if [ $ISSUES -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}[OK] ALL CHECKS PASSED${NC}"
    echo "[OK] ALL CHECKS PASSED" >> "$REPORT_FILE"
    echo ""
    echo "System Status: HEALTHY"
    echo "  - No issues detected"
    echo "  - No warnings"
    echo "  - All systems operational"
    echo ""
    echo "System Status: HEALTHY" >> "$REPORT_FILE"
    echo "  - No issues detected" >> "$REPORT_FILE"
    echo "  - No warnings" >> "$REPORT_FILE"
elif [ $ISSUES -eq 0 ]; then
    echo -e "${YELLOW}[WARN] CHECKS COMPLETED WITH WARNINGS${NC}"
    echo "[WARN] CHECKS COMPLETED WITH WARNINGS" >> "$REPORT_FILE"
    echo ""
    echo "System Status: GOOD (with warnings)"
    echo "  - No critical issues"
    echo "  - $WARNINGS warnings detected"
    echo "  - Review warnings above"
    echo ""
    echo "System Status: GOOD (with warnings)" >> "$REPORT_FILE"
    echo "  - Warnings: $WARNINGS" >> "$REPORT_FILE"
else
    echo -e "${RED}[FAIL] HEALTH CHECK FAILED${NC}"
    echo "[FAIL] HEALTH CHECK FAILED" >> "$REPORT_FILE"
    echo ""
    echo "System Status: NEEDS ATTENTION"
    echo "  - Critical Issues: $ISSUES"
    echo "  - Warnings: $WARNINGS"
    echo "  - Review issues above and take corrective action"
    echo ""
    echo "System Status: NEEDS ATTENTION" >> "$REPORT_FILE"
    echo "  - Critical Issues: $ISSUES" >> "$REPORT_FILE"
    echo "  - Warnings: $WARNINGS" >> "$REPORT_FILE"
fi

echo "Report saved to: $REPORT_FILE"
echo "" >> "$REPORT_FILE"
echo "Report generated: $(date '+%Y-%m-%d %H:%M:%S')" >> "$REPORT_FILE"

echo ""
echo -e "${CYAN}============================================================${NC}"
echo ""

# Recommendations
if [ $ISSUES -gt 0 ] || [ $WARNINGS -gt 0 ]; then
    echo -e "${YELLOW}RECOMMENDED ACTIONS:${NC}"
    echo ""

    if [ $ISSUES -gt 0 ]; then
        echo "1. Review critical issues in report: $REPORT_FILE"
        echo "2. Run: bash $MEMORY_DIR/verify-system.sh"
        echo "3. Check logs: tail -100 $MEMORY_DIR/logs/health.log"
        echo "4. Restart daemons: bash $MEMORY_DIR/startup-hook-v2.sh"
    fi

    if [ $WARNINGS -gt 0 ]; then
        echo "5. Review warnings and optimize as needed"
        echo "6. Consider running: bash $MEMORY_DIR/monthly-optimization.sh"
    fi

    echo ""
fi

# Exit code
if [ $ISSUES -gt 0 ]; then
    exit 1
else
    exit 0
fi

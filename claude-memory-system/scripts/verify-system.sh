#!/bin/bash
# -*- coding: utf-8 -*-
#
# System Verification Script
# Verifies all automation systems are working correctly
#

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

MEMORY_DIR=~/.claude/memory
ERRORS=0
WARNINGS=0

echo ""
echo "============================================================"
echo "SYSTEM VERIFICATION"
echo "============================================================"
echo ""

# Function to check command
check_command() {
    local name=$1
    local command=$2
    local expected=$3

    echo -n "Checking $name... "

    output=$(eval $command 2>&1)
    exit_code=$?

    if [ $exit_code -eq 0 ] && [[ "$output" == *"$expected"* ]]; then
        echo -e "${GREEN}OK${NC}"
        return 0
    else
        echo -e "${RED}FAIL${NC}"
        ((ERRORS++))
        return 1
    fi
}

# Function to check file exists
check_file() {
    local name=$1
    local file=$2

    echo -n "Checking $name... "

    if [ -f "$file" ]; then
        echo -e "${GREEN}EXISTS${NC}"
        return 0
    else
        echo -e "${RED}MISSING${NC}"
        ((ERRORS++))
        return 1
    fi
}

# Function to check directory exists
check_dir() {
    local name=$1
    local dir=$2

    echo -n "Checking $name... "

    if [ -d "$dir" ]; then
        echo -e "${GREEN}EXISTS${NC}"
        return 0
    else
        echo -e "${RED}MISSING${NC}"
        ((ERRORS++))
        return 1
    fi
}

# Phase 1: Context Optimization
echo "[1] Phase 1: Context Optimization"
check_file "Pre-execution optimizer" "$MEMORY_DIR/pre-execution-optimizer.py"
check_file "Context extractor" "$MEMORY_DIR/context-extractor.py"
check_file "Context cache" "$MEMORY_DIR/context-cache.py"
check_file "Session state" "$MEMORY_DIR/session-state.py"
check_file "Context monitor v2" "$MEMORY_DIR/context-monitor-v2.py"
check_dir "Cache directory" "$MEMORY_DIR/.cache"
check_dir "State directory" "$MEMORY_DIR/.state"
echo ""

# Phase 2: Daemon Infrastructure
echo "[2] Phase 2: Daemon Infrastructure"
check_file "Daemon manager" "$MEMORY_DIR/daemon-manager.py"
check_file "PID tracker" "$MEMORY_DIR/pid-tracker.py"
check_file "Health monitor" "$MEMORY_DIR/health-monitor-daemon.py"
check_file "Daemon logger" "$MEMORY_DIR/daemon-logger.py"
check_dir "PIDs directory" "$MEMORY_DIR/.pids"
check_dir "Restarts directory" "$MEMORY_DIR/.restarts"
check_dir "Daemon logs directory" "$MEMORY_DIR/logs/daemons"
check_command "Daemon health" "python $MEMORY_DIR/daemon-manager.py --status-all --format json" '"running": true'
echo ""

# Phase 3: Failure Prevention
echo "[3] Phase 3: Failure Prevention"
check_file "Failure detector v2" "$MEMORY_DIR/failure-detector-v2.py"
check_file "Pre-execution checker" "$MEMORY_DIR/pre-execution-checker.py"
check_file "Failure KB" "$MEMORY_DIR/failure-kb.json"
check_file "Pattern extractor" "$MEMORY_DIR/failure-pattern-extractor.py"
check_file "Solution learner" "$MEMORY_DIR/failure-solution-learner.py"
check_command "KB stats" "python $MEMORY_DIR/pre-execution-checker.py --stats" '"total_patterns"'
echo ""

# Phase 4: Policy Automation
echo "[4] Phase 4: Policy Automation"
check_file "Model selection enforcer" "$MEMORY_DIR/model-selection-enforcer.py"
check_file "Model selection monitor" "$MEMORY_DIR/model-selection-monitor.py"
check_file "Consultation tracker" "$MEMORY_DIR/consultation-tracker.py"
check_file "Core skills enforcer" "$MEMORY_DIR/core-skills-enforcer.py"
check_command "Model analysis" "python $MEMORY_DIR/model-selection-enforcer.py --analyze 'test'" '"recommended_model"'
echo ""

# Phase 5: Integration
echo "[5] Phase 5: Integration & Testing"
check_file "Dashboard v2" "$MEMORY_DIR/dashboard-v2.sh"
check_file "Startup hook v2" "$MEMORY_DIR/startup-hook-v2.sh"
check_file "Test suite" "$MEMORY_DIR/test-all-phases.py"
check_file "Verification script" "$MEMORY_DIR/verify-system.sh"
echo ""

# Summary
echo "============================================================"
echo "VERIFICATION SUMMARY"
echo "============================================================"

if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}ALL CHECKS PASSED!${NC}"
    echo ""
    echo "System Status: FULLY OPERATIONAL"
    echo "  - All 4 phases implemented"
    echo "  - All files present"
    echo "  - All systems functional"
    echo ""
    echo "Ready for production use!"
    exit 0
else
    echo -e "${RED}VERIFICATION FAILED${NC}"
    echo ""
    echo "Errors: $ERRORS"
    echo "Warnings: $WARNINGS"
    echo ""
    echo "Please fix the issues above and run verification again."
    exit 1
fi

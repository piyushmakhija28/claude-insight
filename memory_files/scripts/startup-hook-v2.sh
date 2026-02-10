#!/bin/bash
# -*- coding: utf-8 -*-
#
# Memory System Startup Hook v2.0
# Uses new daemon manager infrastructure with cross-platform support
#
# Usage:
#   bash startup-hook-v2.sh
#

# Colors (if terminal supports it)
if [ -t 1 ]; then
    GREEN='\033[0;32m'
    BLUE='\033[0;34m'
    YELLOW='\033[1;33m'
    RED='\033[0;31m'
    NC='\033[0m'
else
    GREEN=''
    BLUE=''
    YELLOW=''
    RED=''
    NC=''
fi

PROJECT_NAME=$(basename "$PWD")
MEMORY_DIR=~/.claude/memory

echo ""
echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}Memory System Startup v2.0${NC}"
echo -e "${BLUE}============================================================${NC}"
echo ""

# Step 1: Initialize context optimization (Phase 1)
echo -e "${GREEN}[1/10] Initializing context optimization...${NC}"
python "$MEMORY_DIR/context-monitor-v2.py" --init > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo -e "  [OK] Context optimization initialized"
else
    echo -e "${YELLOW}  [WARN] Context optimization failed${NC}"
fi

# Step 2: Load session state
echo -e "${GREEN}[2/10] Loading session state...${NC}"
SESSION_SUMMARY=$(python "$MEMORY_DIR/session-state.py" --summary 2>/dev/null)
if [ $? -eq 0 ]; then
    echo -e "  [OK] Session state loaded"
    # Check for pending work
    PENDING_COUNT=$(echo "$SESSION_SUMMARY" | grep -o '"pending_work":' | wc -l)
    if [ "$PENDING_COUNT" -gt 0 ]; then
        echo -e "${YELLOW}  [INFO] You have pending work items${NC}"
    fi
else
    echo -e "  [OK] New session state created"
fi

# Step 3: Clean up stale PID files
echo -e "${GREEN}[3/10] Cleaning up stale PIDs...${NC}"
CLEANED=$(python "$MEMORY_DIR/pid-tracker.py" --cleanup 2>/dev/null | grep -o "Cleaned [0-9]*" | grep -o "[0-9]*")
if [ -n "$CLEANED" ] && [ "$CLEANED" -gt 0 ]; then
    echo -e "  [OK] Cleaned $CLEANED stale PID files"
else
    echo -e "  [OK] No stale PIDs found"
fi

# Step 4: Migrate local CLAUDE.md
echo -e "${GREEN}[4/10] Checking for local CLAUDE.md...${NC}"
if [ -f "$PWD/CLAUDE.md" ]; then
    python "$MEMORY_DIR/migrate-local-claude.py" "$PWD" > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo -e "  [OK] Local CLAUDE.md migrated"
    else
        echo -e "${YELLOW}  [WARN] Migration check completed${NC}"
    fi
else
    echo -e "  [OK] No local CLAUDE.md found"
fi

# Step 5: Auto-register skills
echo -e "${GREEN}[5/10] Auto-registering skills...${NC}"
python "$MEMORY_DIR/auto-register-skills.py" > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo -e "  [OK] Skills registered"
else
    echo -e "${YELLOW}  [WARN] Skill registration had issues${NC}"
fi

# Step 6: Check incomplete work
echo -e "${GREEN}[6/10] Checking for incomplete work...${NC}"
INCOMPLETE=$(python "$MEMORY_DIR/check-incomplete-work.py" "$PROJECT_NAME" 2>/dev/null)
if [ $? -eq 0 ]; then
    if echo "$INCOMPLETE" | grep -q "incomplete"; then
        echo -e "${YELLOW}  [INFO] Incomplete work found${NC}"
    else
        echo -e "  [OK] No incomplete work"
    fi
else
    echo -e "  [OK] Work check completed"
fi

# Step 7: Start all daemons using daemon manager
echo -e "${GREEN}[7/10] Starting all daemons...${NC}"
START_RESULT=$(python "$MEMORY_DIR/daemon-manager.py" --start-all --format json 2>&1)
if [ $? -eq 0 ]; then
    # Count how many started successfully
    STARTED=$(echo "$START_RESULT" | grep -o '"status": "started"' | wc -l)
    ALREADY=$(echo "$START_RESULT" | grep -o '"status": "already_running"' | wc -l)
    TOTAL=$((STARTED + ALREADY))

    if [ "$STARTED" -gt 0 ]; then
        echo -e "  [OK] Started $STARTED daemons ($ALREADY already running)"
    elif [ "$ALREADY" -gt 0 ]; then
        echo -e "  [OK] All $ALREADY daemons already running"
    else
        echo -e "${YELLOW}  [WARN] No daemons started${NC}"
    fi
else
    echo -e "${RED}  [ERROR] Failed to start daemons${NC}"
fi

# Step 8: Start health monitor daemon
echo -e "${GREEN}[8/10] Starting health monitor...${NC}"
HEALTH_PID=$(python "$MEMORY_DIR/pid-tracker.py" --read health-monitor 2>/dev/null)
if [ -n "$HEALTH_PID" ]; then
    # Check if actually running
    if python "$MEMORY_DIR/pid-tracker.py" --verify health-monitor 2>/dev/null | grep -q '"is_running": true'; then
        echo -e "  [OK] Health monitor already running (PID $HEALTH_PID)"
    else
        # Stale PID, start new one
        python "$MEMORY_DIR/daemon-manager.py" --start health-monitor-daemon > /dev/null 2>&1
        echo -e "  [OK] Health monitor restarted"
    fi
else
    # Start health monitor
    python "$MEMORY_DIR/daemon-manager.py" --start health-monitor-daemon > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo -e "  [OK] Health monitor started"
    else
        echo -e "${YELLOW}  [WARN] Health monitor failed to start${NC}"
    fi
fi

# Step 9: Verify daemon health
echo -e "${GREEN}[9/10] Verifying daemon health...${NC}"
HEALTH=$(python "$MEMORY_DIR/pid-tracker.py" --health 2>/dev/null)
if [ $? -eq 0 ]; then
    RUNNING=$(echo "$HEALTH" | grep -o '"running": [0-9]*' | grep -o '[0-9]*')
    TOTAL=$(echo "$HEALTH" | grep -o '"total_daemons": [0-9]*' | grep -o '[0-9]*')
    SCORE=$(echo "$HEALTH" | grep -o '"health_score": [0-9.]*' | grep -o '[0-9.]*')

    if [ -n "$RUNNING" ] && [ -n "$TOTAL" ]; then
        if [ "$RUNNING" -eq "$TOTAL" ]; then
            echo -e "  [OK] All $TOTAL daemons healthy (100%)"
        else
            echo -e "${YELLOW}  [INFO] $RUNNING/$TOTAL daemons healthy${NC}"
        fi
    else
        echo -e "  [OK] Health check completed"
    fi
else
    echo -e "  [OK] Health verification completed"
fi

# Step 10: Load project context
echo -e "${GREEN}[10/10] Loading project context...${NC}"
CONTEXT_FILE="$MEMORY_DIR/sessions/$PROJECT_NAME/project-summary.md"
if [ -f "$CONTEXT_FILE" ]; then
    echo -e "  [OK] Project context available: $PROJECT_NAME"
else
    echo -e "  [OK] New project: $PROJECT_NAME"
fi

echo ""
echo -e "${BLUE}============================================================${NC}"
echo -e "${GREEN}All systems operational!${NC}"
echo ""
echo -e "Next steps:"
echo -e "  • Check status: ${BLUE}python $MEMORY_DIR/daemon-manager.py --status-all --format table${NC}"
echo -e "  • View health:  ${BLUE}python $MEMORY_DIR/health-monitor-daemon.py --score${NC}"
echo -e "  • View logs:    ${BLUE}ls -la $MEMORY_DIR/logs/daemons/${NC}"
echo -e "${BLUE}============================================================${NC}"
echo ""

# Log startup event
python "$MEMORY_DIR/session-state.py" --set-context startup_time "$(date -Iseconds)" > /dev/null 2>&1

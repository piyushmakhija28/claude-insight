#!/bin/bash
# -*- coding: utf-8 -*-
#
# Context Management Startup Hook
# Automatically starts context daemon on session start
#
# Usage:
#   bash startup-hook.sh [--interval MINUTES] [--no-daemon]
#
# Examples:
#   bash startup-hook.sh                # Start daemon with defaults
#   bash startup-hook.sh --interval 5   # Check every 5 minutes
#   bash startup-hook.sh --no-daemon    # Skip daemon (manual mode)

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
INTERVAL=10
START_DAEMON=true
PROJECT_NAME=$(basename "$PWD")

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --interval)
            INTERVAL="$2"
            shift 2
            ;;
        --no-daemon)
            START_DAEMON=false
            shift
            ;;
        --project)
            PROJECT_NAME="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Log function
log_startup() {
    local action="$1"
    local context="$2"
    local log_file=~/.claude/memory/logs/policy-hits.log
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    echo "[$timestamp] startup-hook | $action | $context" >> "$log_file"
}

echo ""
echo -e "${BLUE}======================================================================${NC}"
echo -e "${BLUE}🚀 CONTEXT MANAGEMENT STARTUP${NC}"
echo -e "${BLUE}======================================================================${NC}"
echo ""

# Step 1: Run initial context estimate
echo -e "${GREEN}Step 1: Initial context estimation...${NC}"
python ~/.claude/memory/context-estimator.py > /dev/null 2>&1
echo -e "${GREEN}✅ Context estimated${NC}"
echo ""

# Step 2: Verify session protection
echo -e "${GREEN}Step 2: Verifying session memory protection...${NC}"
python ~/.claude/memory/protect-session-memory.py --verify > /dev/null 2>&1
echo -e "${GREEN}✅ Session memory protected${NC}"
echo ""

# Step 3: Clean stale PIDs and start all daemons using daemon-manager
if [ "$START_DAEMON" = true ]; then
    echo -e "${GREEN}Step 3: Checking daemon status...${NC}"

    # Get current status
    STATUS_JSON=$(python ~/.claude/memory/daemon-manager.py --status-all 2>/dev/null)

    # Count running daemons
    RUNNING_COUNT=$(echo "$STATUS_JSON" | grep -c '"running": true' 2>/dev/null || echo "0")
    RUNNING_COUNT=$(echo "$RUNNING_COUNT" | tr -d '\n\r' | head -c 2)  # Clean output

    if [ "$RUNNING_COUNT" -ge 8 ]; then
        echo -e "${GREEN}✅ All daemons already running ($RUNNING_COUNT/8)${NC}"
        log_startup "all-daemons-verified" "running=$RUNNING_COUNT"
    else
        echo -e "${YELLOW}⚠️  Some daemons not running ($RUNNING_COUNT/8)${NC}"
        echo -e "${GREEN}Step 4: Cleaning stale PIDs...${NC}"

        # Clean stale PIDs
        rm -f ~/.claude/memory/.pids/*.pid 2>/dev/null
        echo -e "${GREEN}✅ Stale PIDs cleared${NC}"

        echo -e "${GREEN}Step 5: Starting all daemons...${NC}"

        # Start all daemons using daemon-manager
        START_RESULT=$(python ~/.claude/memory/daemon-manager.py --start-all 2>&1)

        # Check if successful
        if echo "$START_RESULT" | grep -q '"status": "started"'; then
            STARTED_COUNT=$(echo "$START_RESULT" | grep -c '"status": "started"' 2>/dev/null || echo "0")
            STARTED_COUNT=$(echo "$STARTED_COUNT" | tr -d '\n\r' | head -c 2)  # Clean output
            echo -e "${GREEN}✅ Successfully started $STARTED_COUNT daemons${NC}"
            log_startup "daemons-started" "count=$STARTED_COUNT, interval=${INTERVAL}, project=${PROJECT_NAME}"
        else
            echo -e "${YELLOW}⚠️  Some daemons failed to start${NC}"
            log_startup "daemons-start-partial-failure" "interval=${INTERVAL}"
        fi
    fi
else
    echo -e "${YELLOW}Step 3: Daemon startup skipped (manual mode)${NC}"
    log_startup "daemons-skipped" "manual-mode"
fi

# Verify final daemon status
FINAL_STATUS=$(python ~/.claude/memory/daemon-manager.py --status-all 2>/dev/null)
FINAL_RUNNING=$(echo "$FINAL_STATUS" | grep -c '"running": true' 2>/dev/null || echo "0")
FINAL_RUNNING=$(echo "$FINAL_RUNNING" | tr -d '\n\r' | head -c 2)  # Clean output

echo ""
echo -e "${BLUE}======================================================================${NC}"

if [ "$FINAL_RUNNING" -ge 8 ]; then
    echo -e "${GREEN}✅ ALL AUTOMATION SYSTEMS ACTIVE ($FINAL_RUNNING/8 - 100%)${NC}"
elif [ "$FINAL_RUNNING" -gt 0 ]; then
    echo -e "${YELLOW}⚠️  PARTIAL AUTOMATION ACTIVE ($FINAL_RUNNING/8 daemons)${NC}"
else
    echo -e "${YELLOW}⚠️  MANUAL MODE - No daemons running${NC}"
fi

echo -e "${BLUE}======================================================================${NC}"
echo ""

if [ "$START_DAEMON" = true ] && [ "$FINAL_RUNNING" -gt 0 ]; then
    echo "📊 Automatic Features:"
    echo "   ✅ Context monitoring (every 10 minutes)"
    echo "   ✅ Auto-cleanup at thresholds (70%, 85%, 90%)"
    echo "   ✅ Session memory protection"
    echo "   ✅ Auto-save before cleanup"
    echo "   ✅ Auto-save on triggers (files, commits, time, decisions)"
    echo "   ✅ Auto-track user preferences (learns after 3x)"
    echo "   ✅ Auto-suggest skills (proactive recommendations)"
    echo "   ✅ Auto-commit on triggers (phase/todo completion, file threshold)"
    echo "   ✅ Auto-prune old sessions (monthly, 100+ sessions)"
    echo "   ✅ Auto-detect patterns (monthly, 5+ new projects)"
    echo "   ✅ Auto-learn from failures (every 6 hours)"
    echo ""
    echo "💡 Quick Commands:"
    echo "   python ~/.claude/memory/daemon-manager.py --status-all        # Check all daemons"
    echo "   python ~/.claude/memory/daemon-manager.py --stop-all          # Stop all daemons"
    echo "   python ~/.claude/memory/daemon-manager.py --restart-all       # Restart all daemons"
else
    echo "📊 Manual Mode:"
    echo "   ⚠️  Daemons not started (run manually when needed)"
    echo "   💡 Start: python ~/.claude/memory/daemon-manager.py --start-all"
fi

echo ""
echo -e "${BLUE}======================================================================${NC}"

# Log startup completion
log_startup "startup-complete" "daemon=${START_DAEMON}, interval=${INTERVAL}"

exit 0

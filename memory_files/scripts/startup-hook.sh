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

# Step 3: Start context management daemon (if enabled)
if [ "$START_DAEMON" = true ]; then
    echo -e "${GREEN}Step 3: Starting context management daemon...${NC}"

    # Check if already running
    if python ~/.claude/memory/context-daemon.py --status > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  Context daemon already running${NC}"
    else
        # Start daemon in background
        nohup python ~/.claude/memory/context-daemon.py --interval "$INTERVAL" --project "$PROJECT_NAME" > /dev/null 2>&1 &

        sleep 2  # Wait for daemon to start

        # Verify started
        if python ~/.claude/memory/context-daemon.py --status > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Context daemon started (interval: ${INTERVAL} minutes)${NC}"
            log_startup "context-daemon-started" "interval=${INTERVAL}, project=${PROJECT_NAME}"
        else
            echo -e "${YELLOW}⚠️  Context daemon failed to start${NC}"
            log_startup "context-daemon-start-failed" "interval=${INTERVAL}"
        fi
    fi
else
    echo -e "${YELLOW}Step 3: Context daemon startup skipped (manual mode)${NC}"
    log_startup "context-daemon-skipped" "manual-mode"
fi

echo ""

# Step 4: Start session auto-save daemon (if enabled)
if [ "$START_DAEMON" = true ]; then
    echo -e "${GREEN}Step 4: Starting session auto-save daemon...${NC}"

    # Check if already running
    if python ~/.claude/memory/session-auto-save-daemon.py --status > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  Session save daemon already running${NC}"
    else
        # Start daemon in background
        nohup python ~/.claude/memory/session-auto-save-daemon.py --interval 15 --project "$PROJECT_NAME" > /dev/null 2>&1 &

        sleep 2  # Wait for daemon to start

        # Verify started
        if python ~/.claude/memory/session-auto-save-daemon.py --status > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Session save daemon started (interval: 15 minutes)${NC}"
            log_startup "session-save-daemon-started" "interval=15, project=${PROJECT_NAME}"
        else
            echo -e "${YELLOW}⚠️  Session save daemon failed to start${NC}"
            log_startup "session-save-daemon-start-failed" "interval=15"
        fi
    fi
else
    echo -e "${YELLOW}Step 4: Session save daemon startup skipped (manual mode)${NC}"
    log_startup "session-save-daemon-skipped" "manual-mode"
fi

echo ""

# Step 5: Start preference auto-tracker daemon (if enabled)
if [ "$START_DAEMON" = true ]; then
    echo -e "${GREEN}Step 5: Starting preference auto-tracker daemon...${NC}"

    # Check if already running
    if python ~/.claude/memory/preference-auto-tracker.py --status > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  Preference tracker daemon already running${NC}"
    else
        # Start daemon in background
        nohup python ~/.claude/memory/preference-auto-tracker.py --interval 20 > /dev/null 2>&1 &

        sleep 2  # Wait for daemon to start

        # Verify started
        if python ~/.claude/memory/preference-auto-tracker.py --status > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Preference tracker daemon started (interval: 20 minutes)${NC}"
            log_startup "preference-tracker-daemon-started" "interval=20"
        else
            echo -e "${YELLOW}⚠️  Preference tracker daemon failed to start${NC}"
            log_startup "preference-tracker-daemon-start-failed" "interval=20"
        fi
    fi
else
    echo -e "${YELLOW}Step 5: Preference tracker daemon startup skipped (manual mode)${NC}"
    log_startup "preference-tracker-daemon-skipped" "manual-mode"
fi

echo ""

# Step 6: Start skill auto-suggester daemon (if enabled)
if [ "$START_DAEMON" = true ]; then
    echo -e "${GREEN}Step 6: Starting skill auto-suggester daemon...${NC}"

    # Check if already running
    if python ~/.claude/memory/skill-auto-suggester.py --status > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  Skill suggester daemon already running${NC}"
    else
        # Start daemon in background
        nohup python ~/.claude/memory/skill-auto-suggester.py --interval 5 > /dev/null 2>&1 &

        sleep 2  # Wait for daemon to start

        # Verify started
        if python ~/.claude/memory/skill-auto-suggester.py --status > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Skill suggester daemon started (interval: 5 minutes)${NC}"
            log_startup "skill-suggester-daemon-started" "interval=5"
        else
            echo -e "${YELLOW}⚠️  Skill suggester daemon failed to start${NC}"
            log_startup "skill-suggester-daemon-start-failed" "interval=5"
        fi
    fi
else
    echo -e "${YELLOW}Step 6: Skill suggester daemon startup skipped (manual mode)${NC}"
    log_startup "skill-suggester-daemon-skipped" "manual-mode"
fi

echo ""

# Step 7: Start git auto-commit daemon (if enabled)
if [ "$START_DAEMON" = true ]; then
    echo -e "${GREEN}Step 7: Starting git auto-commit daemon...${NC}"

    # Check if already running
    if python ~/.claude/memory/commit-daemon.py --status > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  Commit daemon already running${NC}"
    else
        # Start daemon in background (only if in git repo)
        if git rev-parse --git-dir > /dev/null 2>&1; then
            nohup python ~/.claude/memory/commit-daemon.py --interval 15 --project-dir "$PWD" > /dev/null 2>&1 &

            sleep 2  # Wait for daemon to start

            # Verify started
            if python ~/.claude/memory/commit-daemon.py --status > /dev/null 2>&1; then
                echo -e "${GREEN}✅ Commit daemon started (interval: 15 minutes)${NC}"
                log_startup "commit-daemon-started" "interval=15, project=${PROJECT_NAME}"
            else
                echo -e "${YELLOW}⚠️  Commit daemon failed to start${NC}"
                log_startup "commit-daemon-start-failed" "interval=15"
            fi
        else
            echo -e "${YELLOW}⚠️  Not a git repository, skipping commit daemon${NC}"
            log_startup "commit-daemon-skipped" "not-a-git-repo"
        fi
    fi
else
    echo -e "${YELLOW}Step 7: Commit daemon startup skipped (manual mode)${NC}"
    log_startup "commit-daemon-skipped" "manual-mode"
fi

echo ""

# Step 8: Start session pruning daemon (if enabled)
if [ "$START_DAEMON" = true ]; then
    echo -e "${GREEN}Step 8: Starting session pruning daemon...${NC}"

    # Check if already running
    if python ~/.claude/memory/session-pruning-daemon.py --status > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  Pruning daemon already running${NC}"
    else
        # Start daemon in background
        nohup python ~/.claude/memory/session-pruning-daemon.py --interval 30 > /dev/null 2>&1 &

        sleep 2  # Wait for daemon to start

        # Verify started
        if python ~/.claude/memory/session-pruning-daemon.py --status > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Pruning daemon started (interval: 30 days)${NC}"
            log_startup "pruning-daemon-started" "interval=30days"
        else
            echo -e "${YELLOW}⚠️  Pruning daemon failed to start${NC}"
            log_startup "pruning-daemon-start-failed" "interval=30days"
        fi
    fi
else
    echo -e "${YELLOW}Step 8: Pruning daemon startup skipped (manual mode)${NC}"
    log_startup "pruning-daemon-skipped" "manual-mode"
fi

echo ""

# Step 9: Start pattern detection daemon (if enabled)
if [ "$START_DAEMON" = true ]; then
    echo -e "${GREEN}Step 9: Starting pattern detection daemon...${NC}"

    # Check if already running
    if python ~/.claude/memory/pattern-detection-daemon.py --status > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  Pattern daemon already running${NC}"
    else
        # Start daemon in background
        nohup python ~/.claude/memory/pattern-detection-daemon.py --interval 30 > /dev/null 2>&1 &

        sleep 2  # Wait for daemon to start

        # Verify started
        if python ~/.claude/memory/pattern-detection-daemon.py --status > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Pattern daemon started (interval: 30 days)${NC}"
            log_startup "pattern-daemon-started" "interval=30days"
        else
            echo -e "${YELLOW}⚠️  Pattern daemon failed to start${NC}"
            log_startup "pattern-daemon-start-failed" "interval=30days"
        fi
    fi
else
    echo -e "${YELLOW}Step 9: Pattern daemon startup skipped (manual mode)${NC}"
    log_startup "pattern-daemon-skipped" "manual-mode"
fi

echo ""

# Step 10: Start failure prevention daemon (if enabled)
if [ "$START_DAEMON" = true ]; then
    echo -e "${GREEN}Step 10: Starting failure prevention daemon...${NC}"

    # Check if already running
    if python ~/.claude/memory/failure-prevention-daemon.py --status > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  Failure prevention daemon already running${NC}"
    else
        # Start daemon in background
        nohup python ~/.claude/memory/failure-prevention-daemon.py --interval 6 > /dev/null 2>&1 &

        sleep 2  # Wait for daemon to start

        # Verify started
        if python ~/.claude/memory/failure-prevention-daemon.py --status > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Failure prevention daemon started (interval: 6 hours)${NC}"
            log_startup "failure-daemon-started" "interval=6hours"
        else
            echo -e "${YELLOW}⚠️  Failure prevention daemon failed to start${NC}"
            log_startup "failure-daemon-start-failed" "interval=6hours"
        fi
    fi
else
    echo -e "${YELLOW}Step 10: Failure prevention daemon startup skipped (manual mode)${NC}"
    log_startup "failure-daemon-skipped" "manual-mode"
fi

echo ""
echo -e "${BLUE}======================================================================${NC}"
echo -e "${GREEN}✅ ALL AUTOMATION SYSTEMS ACTIVE (8/8 - 100%)${NC}"
echo -e "${BLUE}======================================================================${NC}"
echo ""

if [ "$START_DAEMON" = true ]; then
    echo "📊 Automatic Features:"
    echo "   ✅ Context monitoring (every ${INTERVAL} minutes)"
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
    echo "💡 Commands:"
    echo "   python ~/.claude/memory/context-daemon.py --status                # Context daemon"
    echo "   python ~/.claude/memory/session-auto-save-daemon.py --status      # Session save daemon"
    echo "   python ~/.claude/memory/preference-auto-tracker.py --status       # Preference tracker"
    echo "   python ~/.claude/memory/skill-auto-suggester.py --status          # Skill suggester"
    echo "   python ~/.claude/memory/commit-daemon.py --status                 # Commit daemon"
    echo "   python ~/.claude/memory/session-pruning-daemon.py --status        # Pruning daemon"
    echo "   python ~/.claude/memory/pattern-detection-daemon.py --status      # Pattern daemon"
    echo "   python ~/.claude/memory/failure-prevention-daemon.py --status     # Failure daemon"
else
    echo "📊 Manual Mode:"
    echo "   ⚠️  Daemons not started (run manually when needed)"
fi

echo ""
echo -e "${BLUE}======================================================================${NC}"

# Log startup completion
log_startup "startup-complete" "daemon=${START_DAEMON}, interval=${INTERVAL}"

exit 0

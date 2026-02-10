#!/bin/bash
# -*- coding: utf-8 -*-
#
# Memory System Dashboard v2.0
# Unified monitoring for all automation systems
#

# Colors (if terminal supports it)
if [ -t 1 ]; then
    GREEN='\033[0;32m'
    BLUE='\033[0;34m'
    YELLOW='\033[1;33m'
    RED='\033[0;31m'
    CYAN='\033[0;36m'
    NC='\033[0m'
else
    GREEN=''
    BLUE=''
    YELLOW=''
    RED=''
    CYAN=''
    NC=''
fi

MEMORY_DIR=~/.claude/memory

echo ""
echo -e "${BLUE}============================================================${NC}"
echo -e "${CYAN}         MEMORY SYSTEM DASHBOARD v2.0${NC}"
echo -e "${BLUE}============================================================${NC}"
echo ""

# Section 1: Daemon Health
echo -e "${GREEN}[1] DAEMON HEALTH${NC}"
echo "------------------------------------------------------------"

DAEMON_STATUS=$(python "$MEMORY_DIR/daemon-manager.py" --status-all --format json 2>/dev/null)
if [ $? -eq 0 ]; then
    RUNNING=$(echo "$DAEMON_STATUS" | grep -o '"running": true' | wc -l)
    TOTAL=$(echo "$DAEMON_STATUS" | grep -o '"daemon"' | wc -l)

    if [ "$RUNNING" -eq "$TOTAL" ]; then
        echo -e "  Status: ${GREEN}ALL HEALTHY${NC} ($RUNNING/$TOTAL daemons)"
    else
        echo -e "  Status: ${YELLOW}DEGRADED${NC} ($RUNNING/$TOTAL daemons)"
    fi

    # Show daemon status
    python "$MEMORY_DIR/daemon-manager.py" --status-all --format table 2>/dev/null | tail -n +2
else
    echo -e "  Status: ${RED}ERROR${NC} (cannot get status)"
fi

echo ""

# Section 2: Context Status
echo -e "${GREEN}[2] CONTEXT STATUS${NC}"
echo "------------------------------------------------------------"

CONTEXT_STATUS=$(python "$MEMORY_DIR/context-monitor-v2.py" --current-status 2>/dev/null)
if [ $? -eq 0 ]; then
    PERCENTAGE=$(echo "$CONTEXT_STATUS" | grep -o '"percentage": [0-9.]*' | grep -o '[0-9.]*')
    LEVEL=$(echo "$CONTEXT_STATUS" | grep -o '"level": "[^"]*"' | sed 's/"level": "\(.*\)"/\1/')

    if [ -n "$PERCENTAGE" ]; then
        echo "  Usage: ${PERCENTAGE}% (Level: $LEVEL)"

        # Show recommendations if not green
        if [ "$LEVEL" != "green" ]; then
            echo "  Recommendations:"
            echo "$CONTEXT_STATUS" | grep -A 10 '"recommendations"' | grep -o '".* ->.*"' | sed 's/"//g' | sed 's/^/    /'
        fi
    else
        echo "  Usage: Unknown"
    fi

    # Cache stats
    CACHE_STATS=$(python "$MEMORY_DIR/context-cache.py" --stats 2>/dev/null)
    if [ $? -eq 0 ]; then
        CACHE_ENTRIES=$(echo "$CACHE_STATS" | grep -o '"summary_cache_entries": [0-9]*' | grep -o '[0-9]*')
        echo "  Cache: $CACHE_ENTRIES file summaries cached"
    fi
else
    echo "  Status: ${RED}ERROR${NC} (cannot get status)"
fi

echo ""

# Section 3: Failure Prevention
echo -e "${GREEN}[3] FAILURE PREVENTION${NC}"
echo "------------------------------------------------------------"

KB_STATS=$(python "$MEMORY_DIR/pre-execution-checker.py" --stats 2>/dev/null)
if [ $? -eq 0 ]; then
    TOTAL_PATTERNS=$(echo "$KB_STATS" | grep -o '"total_patterns": [0-9]*' | grep -o '[0-9]*')
    HIGH_CONF=$(echo "$KB_STATS" | grep -o '"high_confidence": [0-9]*' | grep -o '[0-9]*')

    echo "  Knowledge Base: $TOTAL_PATTERNS patterns ($HIGH_CONF high confidence)"

    # Show by tool
    echo "$KB_STATS" | grep -A 10 '"by_tool"' | grep -o '"\w*": [0-9]*' | sed 's/"//g' | sed 's/^/    /'
else
    echo "  Status: ${RED}ERROR${NC} (cannot get KB stats)"
fi

echo ""

# Section 4: Model Usage
echo -e "${GREEN}[4] MODEL USAGE${NC}"
echo "------------------------------------------------------------"

MODEL_STATS=$(python "$MEMORY_DIR/model-selection-monitor.py" --distribution --days 7 2>/dev/null)
if [ $? -eq 0 ]; then
    TOTAL=$(echo "$MODEL_STATS" | grep -o '"total_requests": [0-9]*' | grep -o '[0-9]*')

    if [ "$TOTAL" -gt 0 ]; then
        echo "  Total Requests (7 days): $TOTAL"
        echo "  Distribution:"

        # Show percentages
        echo "$MODEL_STATS" | grep -A 5 '"percentages"' | grep -o '"\w*": [0-9.]*' | sed 's/"//g' | sed 's/^/    /' | sed 's/:/ -> /' | sed 's/$/%/'

        # Check compliance
        COMPLIANCE=$(python "$MEMORY_DIR/model-selection-monitor.py" --check-compliance 2>/dev/null)
        IS_COMPLIANT=$(echo "$COMPLIANCE" | grep -o '"compliant": \w*' | grep -o '\w*$')

        if [ "$IS_COMPLIANT" = "true" ]; then
            echo -e "  Compliance: ${GREEN}OK${NC}"
        else
            echo -e "  Compliance: ${YELLOW}ISSUES DETECTED${NC}"
            echo "$COMPLIANCE" | grep -o '"message": "[^"]*"' | sed 's/"message": "\(.*\)"/    \1/'
        fi
    else
        echo "  No usage data yet"
    fi
else
    echo "  Status: ${RED}ERROR${NC} (cannot get model stats)"
fi

echo ""

# Section 5: Consultation Preferences
echo -e "${GREEN}[5] CONSULTATION PREFERENCES${NC}"
echo "------------------------------------------------------------"

CONSULT_STATS=$(python "$MEMORY_DIR/consultation-tracker.py" --stats 2>/dev/null)
if [ $? -eq 0 ]; then
    TOTAL_CONSULT=$(echo "$CONSULT_STATS" | grep -o '"total_consultations": [0-9]*' | grep -o '[0-9]*')
    CONSISTENT=$(echo "$CONSULT_STATS" | grep -o '"consistent_preferences": [0-9]*' | grep -o '[0-9]*')

    echo "  Total Consultations: $TOTAL_CONSULT"
    echo "  Consistent Preferences: $CONSISTENT"

    if [ "$CONSISTENT" -gt 0 ]; then
        echo "  Auto-skip enabled for $CONSISTENT decision types"
    fi
else
    echo "  No consultation data yet"
fi

echo ""

# Section 6: Core Skills Compliance
echo -e "${GREEN}[6] CORE SKILLS COMPLIANCE${NC}"
echo "------------------------------------------------------------"

SKILLS_STATS=$(python "$MEMORY_DIR/core-skills-enforcer.py" --stats 2>/dev/null)
if [ $? -eq 0 ]; then
    SESSIONS=$(echo "$SKILLS_STATS" | grep -o '"total_sessions": [0-9]*' | grep -o '[0-9]*')
    COMPLIANCE=$(echo "$SKILLS_STATS" | grep -o '"compliance_rate": [0-9.]*' | grep -o '[0-9.]*')

    if [ "$SESSIONS" -gt 0 ]; then
        echo "  Total Sessions: $SESSIONS"
        echo "  Compliance Rate: ${COMPLIANCE}%"

        if [ "${COMPLIANCE%.*}" -eq 100 ]; then
            echo -e "  Status: ${GREEN}PERFECT COMPLIANCE${NC}"
        elif [ "${COMPLIANCE%.*}" -ge 80 ]; then
            echo -e "  Status: ${GREEN}GOOD${NC}"
        else
            echo -e "  Status: ${YELLOW}NEEDS IMPROVEMENT${NC}"
        fi
    else
        echo "  No session data yet"
    fi
else
    echo "  No compliance data yet"
fi

echo ""

# Section 7: Recent Activity
echo -e "${GREEN}[7] RECENT ACTIVITY${NC}"
echo "------------------------------------------------------------"

echo "  Recent Policy Hits (last 5):"
if [ -f "$MEMORY_DIR/logs/policy-hits.log" ]; then
    tail -5 "$MEMORY_DIR/logs/policy-hits.log" | sed 's/^/    /'
else
    echo "    No activity logged"
fi

echo ""

# Section 8: System Health Score
echo -e "${GREEN}[8] OVERALL HEALTH SCORE${NC}"
echo "------------------------------------------------------------"

HEALTH=$(python "$MEMORY_DIR/pid-tracker.py" --health 2>/dev/null)
if [ $? -eq 0 ]; then
    HEALTH_SCORE=$(echo "$HEALTH" | grep -o '"health_score": [0-9.]*' | grep -o '[0-9.]*')

    if [ -n "$HEALTH_SCORE" ]; then
        SCORE_INT=${HEALTH_SCORE%.*}

        if [ "$SCORE_INT" -ge 90 ]; then
            echo -e "  Health Score: ${GREEN}${HEALTH_SCORE}%${NC} - Excellent"
        elif [ "$SCORE_INT" -ge 70 ]; then
            echo -e "  Health Score: ${YELLOW}${HEALTH_SCORE}%${NC} - Good"
        else
            echo -e "  Health Score: ${RED}${HEALTH_SCORE}%${NC} - Poor"
        fi
    else
        echo "  Health Score: Unknown"
    fi
else
    echo "  Cannot calculate health score"
fi

echo ""
echo -e "${BLUE}============================================================${NC}"
echo ""

# Quick commands
echo -e "${CYAN}Quick Commands:${NC}"
echo "  View logs:       tail -f $MEMORY_DIR/logs/daemons/health-monitor.log"
echo "  Restart daemon:  python $MEMORY_DIR/daemon-manager.py --restart <name>"
echo "  Check context:   python $MEMORY_DIR/context-monitor-v2.py --current-status"
echo "  View KB:         cat $MEMORY_DIR/failure-kb.json"
echo ""

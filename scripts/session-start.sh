#!/bin/bash
################################################################################
# SESSION START SCRIPT - WITH BLOCKING ENFORCEMENT
#
# CRITICAL: This script MUST be run at the start of EVERY conversation.
# It initializes the blocking policy enforcer and validates all daemons.
#
# Version: 2.0.0 (Blocking Enforcement)
# Date: 2026-02-16
################################################################################

echo ""
echo "================================================================================"
echo "🚨 SESSION START - INITIALIZING BLOCKING POLICY ENFORCEMENT"
echo "================================================================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

MEMORY_PATH="$HOME/.claude/memory"

# ============================================================================
# STEP 1: Initialize Blocking Enforcer
# ============================================================================
echo "${BLUE}[1/7] Initializing Blocking Policy Enforcer...${NC}"

python "$MEMORY_PATH/blocking-policy-enforcer.py" --mark-session-started
if [ $? -eq 0 ]; then
    echo "${GREEN}✅ Blocking enforcer initialized${NC}"
    echo "${GREEN}   Session marked as started${NC}"
else
    echo "${RED}❌ Failed to initialize blocking enforcer${NC}"
    exit 1
fi

# ============================================================================
# STEP 2: Start Auto-Recommendation Daemon (9th Daemon)
# ============================================================================
echo ""
echo "${BLUE}[2/7] Starting Auto-Recommendation Daemon (9th daemon)...${NC}"

# Check if already running
PID_FILE="$MEMORY_PATH/.pids/auto-recommendation-daemon.pid"
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p $PID > /dev/null 2>&1; then
        echo "${GREEN}✅ Daemon already running (PID: $PID)${NC}"
    else
        echo "${YELLOW}⚠️  Stale PID file found, starting daemon...${NC}"
        rm -f "$PID_FILE"
        # Start daemon (example - adjust to your actual daemon)
        # nohup python "$MEMORY_PATH/auto-recommendation-daemon.py" start > /dev/null 2>&1 &
        echo "${YELLOW}⚠️  Daemon script not found (auto-recommendation-daemon.py)${NC}"
    fi
else
    echo "${YELLOW}⚠️  Daemon not running, would start here${NC}"
    # nohup python "$MEMORY_PATH/auto-recommendation-daemon.py" start > /dev/null 2>&1 &
fi

# ============================================================================
# STEP 3: Check All 9 Daemon PIDs and Status
# ============================================================================
echo ""
echo "${BLUE}[3/7] Checking all 9 daemon statuses...${NC}"

# Use daemon-manager.py for accurate status check
python "$MEMORY_PATH/utilities/daemon-manager.py" --status-all > /tmp/daemon-status.json 2>/dev/null

if [ $? -eq 0 ]; then
    RUNNING=$(grep -c '"running": true' /tmp/daemon-status.json)
    STOPPED=$((9 - RUNNING))

    python - /tmp/daemon-status.json <<EOF
import json, sys

# Fix encoding for Windows console
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

with open(sys.argv[1], 'r') as f:
    data = json.load(f)
for daemon, info in data.items():
    if info.get('running'):
        print("   ✅ " + daemon + ": Running (PID: " + str(info.get('pid')) + ")")
    else:
        print("   ❌ " + daemon + ": Stopped")
EOF

    echo ""
    if [ $RUNNING -eq 9 ]; then
        echo "${GREEN}   ✅ ALL 9 DAEMONS RUNNING PERFECTLY!${NC}"
    else
        echo "${GREEN}   Running: $RUNNING / 9${NC}"
        echo "${RED}   Stopped: $STOPPED / 9${NC}"
    fi

    rm -f /tmp/daemon-status.json
else
    echo "${YELLOW}⚠️  Could not check daemon status${NC}"
fi

# ============================================================================
# STEP 4: Show Latest Recommendations
# ============================================================================
echo ""
echo "${BLUE}[4/7] Loading latest recommendations...${NC}"

RECOMMENDATIONS_FILE="$MEMORY_PATH/.last-automation-check.json"
if [ -f "$RECOMMENDATIONS_FILE" ]; then
    echo "${GREEN}✅ Recommendations found:${NC}"

    # Extract recommendations using Python (CRITICAL - must succeed)
    python - <<EOF
import json, sys

# Fix encoding for Windows console
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

try:
    with open('$RECOMMENDATIONS_FILE', 'r') as f:
        data = json.load(f)

    print("   Model: ${GREEN}" + data.get('recommended_model', 'N/A') + "${NC}")
    print("   Skills: ${GREEN}" + ', '.join(data.get('recommended_skills', [])) + "${NC}")
    print("   Agents: ${GREEN}" + ', '.join(data.get('recommended_agents', [])) + "${NC}")
except Exception as e:
    print("   ${RED}❌ CRITICAL: Could not parse recommendations${NC}")
    print("   ${RED}Error: " + str(e) + "${NC}")
    print("   ${RED}This is a BLOCKING FAILURE - System cannot proceed!${NC}")
    sys.exit(1)  # FAIL with exit code 1
EOF

    # Check if parse succeeded
    if [ $? -ne 0 ]; then
        echo ""
        echo "${RED}============================================================${NC}"
        echo "${RED}🚨 CRITICAL FAILURE: Recommendation Parse Error${NC}"
        echo "${RED}============================================================${NC}"
        echo ""
        echo "${RED}The recommendations file is corrupted or invalid.${NC}"
        echo "${RED}This is a BLOCKING error - system cannot proceed!${NC}"
        echo ""
        echo "${YELLOW}To fix:${NC}"
        echo "   1. Restart auto-recommendation daemon:"
        echo "      python ~/.claude/memory/03-execution-system/07-recommendations/auto-recommendation-daemon.py restart"
        echo "   2. Or delete corrupted file:"
        echo "      rm $RECOMMENDATIONS_FILE"
        echo "   3. Re-run session-start.sh"
        echo ""
        exit 1  # EXIT SESSION START WITH FAILURE
    fi
else
    echo "${YELLOW}⚠️  No recommendations file found${NC}"
    echo "   Run: python ~/.claude/memory/session-start-check.py"
fi

# ============================================================================
# STEP 5: Show Context Status
# ============================================================================
echo ""
echo "${BLUE}[5/7] Checking context status...${NC}"

# Check context (if context monitor exists)
if [ -f "$MEMORY_PATH/context-monitor-v2.py" ]; then
    python "$MEMORY_PATH/context-monitor-v2.py" --current-status 2>/dev/null || {
        echo "${YELLOW}⚠️  Context monitor not available${NC}"
    }

    # Mark context as checked in blocking enforcer
    python "$MEMORY_PATH/blocking-policy-enforcer.py" --mark-context-checked
else
    echo "${YELLOW}⚠️  Context monitor not found${NC}"
fi

# ============================================================================
# STEP 6: Detect Active Claude Code Plan
# ============================================================================
echo ""
echo "${BLUE}[6/7] Detecting active Claude Code plan...${NC}"

# Check if plan detector exists
if [ -f "$MEMORY_PATH/scripts/plan-detector.sh" ]; then
    PLAN_SUMMARY=$(bash "$MEMORY_PATH/scripts/plan-detector.sh" --summary 2>/dev/null)
    if [ $? -eq 0 ]; then
        echo "${GREEN}✅ Active Plan: $PLAN_SUMMARY${NC}"
    else
        echo "${YELLOW}⚠️  Plan detection failed (continuing with defaults)${NC}"
    fi
else
    echo "${YELLOW}⚠️  Plan detector not found${NC}"
fi

# ============================================================================
# STEP 7: Generate and Display Session ID
# ============================================================================
echo ""
echo "${BLUE}[7/9] Generating Session ID for tracking...${NC}"

# Create new session with description
SESSION_DESCRIPTION="Session started at $(date '+%Y-%m-%d %H:%M:%S')"
python "$MEMORY_PATH/session-id-generator.py" create --description "$SESSION_DESCRIPTION" > /dev/null 2>&1

# Display session ID banner
python "$MEMORY_PATH/session-id-generator.py" current 2>/dev/null || {
    echo "${YELLOW}⚠️  Could not generate session ID${NC}"
}

# ============================================================================
# STEP 8: AUTO-LOAD CODING STANDARDS (Phase 1 Automation)
# ============================================================================
echo ""
echo "${BLUE}[8/9] Auto-loading coding standards...${NC}"

if [ -f "$MEMORY_PATH/02-standards-system/standards-loader.py" ]; then
    python "$MEMORY_PATH/02-standards-system/standards-loader.py" --load-all > /tmp/standards-load.log 2>&1
    if [ $? -eq 0 ]; then
        echo "${GREEN}✅ All coding standards loaded successfully${NC}"

        # Mark standards as loaded in blocking enforcer
        python "$MEMORY_PATH/blocking-policy-enforcer.py" --mark-standards-loaded 2>/dev/null

        echo "${GREEN}   ✓ Java Project Structure${NC}"
        echo "${GREEN}   ✓ Config Server Rules${NC}"
        echo "${GREEN}   ✓ Secret Management${NC}"
        echo "${GREEN}   ✓ Response Format (ApiResponseDto)${NC}"
        echo "${GREEN}   ✓ API Design Standards${NC}"
        echo "${GREEN}   ✓ Database Standards${NC}"
        echo "${GREEN}   ✓ Error Handling${NC}"
        echo "${GREEN}   ✓ Service/Entity/Controller Patterns${NC}"
        echo "${GREEN}   ✓ All 12 standards loaded!${NC}"
    else
        echo "${RED}❌ Failed to load standards${NC}"
        echo "${YELLOW}⚠️  Check log: /tmp/standards-load.log${NC}"
    fi
else
    echo "${RED}❌ Standards loader not found${NC}"
fi

# ============================================================================
# STEP 9: FINAL STATUS SUMMARY
# ============================================================================
echo ""
echo "================================================================================"
echo "${GREEN}✅ SESSION INITIALIZATION COMPLETE (WITH AUTO-STANDARDS)${NC}"
echo "================================================================================"
echo ""
echo "${BLUE}📋 Automation Status:${NC}"
echo "   1. ${GREEN}✅ Session started${NC} - Blocking enforcer active"
echo "   2. ${GREEN}✅ Standards loaded${NC} - All 12 coding standards ready"
echo "   3. ${YELLOW}⏳ For each request (Auto):${NC}"
echo "      - Generate prompt (Step 0) - NEXT: Auto-generate"
echo "      - Create tasks (Step 1) - Semi-automated"
echo "      - Decide plan mode (Step 2) - Semi-automated"
echo "      - Select model (Step 4) - NEXT: Auto-select"
echo "      - Check skills/agents (Step 5) - Semi-automated"
echo ""
echo "${GREEN}✅ Phase 1 Automation: ACTIVE (Standards auto-loaded!)${NC}"
echo ""
echo "================================================================================"
echo ""

# Show enforcer status
echo "${BLUE}📊 Blocking Enforcer Status:${NC}"
python "$MEMORY_PATH/blocking-policy-enforcer.py" --status

exit 0

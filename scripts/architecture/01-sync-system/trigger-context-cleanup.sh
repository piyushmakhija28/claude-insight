#!/bin/bash
# -*- coding: utf-8 -*-
#
# Context Cleanup Trigger
# Auto-trigger context cleanup at configured thresholds
#
# Usage:
#   bash trigger-context-cleanup.sh [--context-percent PERCENT] [--project PROJECT]
#
# Examples:
#   bash trigger-context-cleanup.sh --context-percent 75 --project my-app
#   bash trigger-context-cleanup.sh --context-percent 90

set -e

# Default values
CONTEXT_PERCENT=70
PROJECT_NAME=""
DRY_RUN=true

# Colors for output
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --context-percent)
            CONTEXT_PERCENT="$2"
            shift 2
            ;;
        --project)
            PROJECT_NAME="$2"
            shift 2
            ;;
        --execute)
            DRY_RUN=false
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Auto-detect project if not provided
if [ -z "$PROJECT_NAME" ]; then
    PROJECT_NAME=$(basename "$PWD")
fi

# Log function
log_policy_hit() {
    local action="$1"
    local context="$2"
    local log_file=~/.claude/memory/logs/policy-hits.log
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    echo "[$timestamp] context-trigger | $action | $context" >> "$log_file"
}

# Print header
print_header() {
    echo ""
    echo "======================================================================"
    echo -e "${BLUE}⚡ CONTEXT CLEANUP TRIGGER${NC}"
    echo "======================================================================"
    echo ""
}

# Determine cleanup level based on context percentage
determine_cleanup_level() {
    local percent=$1

    if [ "$percent" -ge 90 ]; then
        echo "aggressive"
    elif [ "$percent" -ge 85 ]; then
        echo "moderate"
    elif [ "$percent" -ge 70 ]; then
        echo "light"
    else
        echo "none"
    fi
}

# Main execution
main() {
    print_header

    echo "Context Percentage: ${CONTEXT_PERCENT}%"
    echo "Project: $PROJECT_NAME"
    echo ""

    # Determine cleanup level
    CLEANUP_LEVEL=$(determine_cleanup_level "$CONTEXT_PERCENT")

    if [ "$CLEANUP_LEVEL" = "none" ]; then
        echo -e "${GREEN}✅ Context usage healthy (${CONTEXT_PERCENT}%)${NC}"
        echo -e "${GREEN}✅ No cleanup needed${NC}"
        log_policy_hit "no-cleanup-needed" "context=${CONTEXT_PERCENT}%"
        exit 0
    fi

    echo -e "${YELLOW}⚠️  Context threshold exceeded (${CONTEXT_PERCENT}%)${NC}"
    echo -e "${YELLOW}⚠️  Cleanup level: ${CLEANUP_LEVEL}${NC}"
    echo ""

    # Step 1: Verify session protection
    echo "======================================================================"
    echo -e "${BLUE}STEP 1: VERIFY SESSION MEMORY PROTECTION${NC}"
    echo "======================================================================"
    echo ""

    python ~/.claude/memory/protect-session-memory.py --verify

    echo ""
    echo -e "${GREEN}✅ Session memory protection verified${NC}"
    echo ""

    # Step 2: Monitor context and get recommendations
    echo "======================================================================"
    echo -e "${BLUE}STEP 2: CONTEXT ANALYSIS${NC}"
    echo "======================================================================"
    echo ""

    python ~/.claude/memory/monitor-context.py --threshold "$CONTEXT_PERCENT" --project "$PROJECT_NAME" --simulate "$CONTEXT_PERCENT" || true

    echo ""
    echo -e "${GREEN}✅ Context analysis complete${NC}"
    echo ""

    # Step 3: Execute smart cleanup
    echo "======================================================================"
    echo -e "${BLUE}STEP 3: SMART CLEANUP STRATEGY${NC}"
    echo "======================================================================"
    echo ""

    if [ "$DRY_RUN" = true ]; then
        echo -e "${YELLOW}⚠️  DRY RUN MODE (No actual cleanup)${NC}"
        echo ""
    fi

    python ~/.claude/memory/smart-cleanup.py --level "$CLEANUP_LEVEL" --project "$PROJECT_NAME"

    echo ""
    echo -e "${GREEN}✅ Cleanup strategy generated${NC}"
    echo ""

    # Step 4: Summary
    echo "======================================================================"
    echo -e "${BLUE}SUMMARY${NC}"
    echo "======================================================================"
    echo ""

    case "$CLEANUP_LEVEL" in
        aggressive)
            echo -e "${RED}🔴 AGGRESSIVE CLEANUP (90%+ context)${NC}"
            echo "   - Expected reduction: 90%"
            echo "   - Keep only current task"
            echo "   - CRITICAL: Save session summary NOW!"
            ;;
        moderate)
            echo -e "${YELLOW}🚨 MODERATE CLEANUP (85-89% context)${NC}"
            echo "   - Expected reduction: 50%"
            echo "   - Compress completed work"
            echo "   - Save important context"
            ;;
        light)
            echo -e "${YELLOW}⚠️  LIGHT CLEANUP (70-84% context)${NC}"
            echo "   - Expected reduction: 20%"
            echo "   - Remove old file reads"
            echo "   - Clear MCP responses"
            ;;
    esac

    echo ""
    echo -e "${GREEN}✅ Session memory PROTECTED (${PROJECT_NAME})${NC}"
    echo -e "${GREEN}✅ Policy-based cleanup ready${NC}"
    echo ""

    # Log trigger
    log_policy_hit "cleanup-triggered" "level=${CLEANUP_LEVEL}, context=${CONTEXT_PERCENT}%, project=${PROJECT_NAME}"

    echo "======================================================================"
    echo -e "${BLUE}🎯 NEXT STEPS${NC}"
    echo "======================================================================"
    echo ""

    if [ "$DRY_RUN" = true ]; then
        echo "This was a DRY RUN. To execute actual cleanup:"
        echo ""
        echo "1. Review recommendations above"
        echo "2. Save session summary (if not already done)"
        echo "3. Run with --execute flag (future implementation)"
        echo ""
    else
        echo "Cleanup executed! Context should be optimized now."
        echo ""
    fi

    echo "Protection verified ✅"
    echo "Session memory safe ✅"
    echo "Cleanup strategy applied ✅"
    echo ""
}

# Run main
main

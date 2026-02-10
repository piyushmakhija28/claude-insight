#!/bin/bash
################################################################################
# Session Start Auto-Loader
################################################################################
# Purpose: Automatically run at session start to:
#   1. Migrate local CLAUDE.md to session memory (if exists)
#   2. Load project context from previous sessions
################################################################################

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Paths
MEMORY_DIR=~/.claude/memory
SESSIONS_DIR="$MEMORY_DIR/sessions"
LOG_FILE="$MEMORY_DIR/logs/policy-hits.log"

# Get project directory
PROJECT_DIR="${1:-$PWD}"
PROJECT_NAME=$(basename "$PROJECT_DIR")

################################################################################
# STEP 0: Migrate Local CLAUDE.md
################################################################################

echo -e "${CYAN}🔍 [Session Start] Checking for local CLAUDE.md...${NC}"

# Run migration script (silent if no local claude.md)
if bash "$MEMORY_DIR/migrate-local-claude.sh" "$PROJECT_DIR" 2>/dev/null; then
    # Check if migration actually happened
    if grep -q "local-claude-migration.*$PROJECT_NAME" "$LOG_FILE" 2>/dev/null | tail -1 | grep -q "$(date '+%Y-%m-%d')"; then
        echo -e "${GREEN}✅ Local CLAUDE.md migrated to session memory${NC}"
    fi
fi

################################################################################
# STEP 1: Load Project Context
################################################################################

SESSION_DIR="$SESSIONS_DIR/$PROJECT_NAME"
SUMMARY_FILE="$SESSION_DIR/project-summary.md"

echo -e "${CYAN}🔍 [Session Start] Checking for previous context...${NC}"

if [[ -f "$SUMMARY_FILE" ]]; then
    echo -e "${GREEN}✅ Found project context: $PROJECT_NAME${NC}"
    echo -e "${BLUE}📁 Loading from: $SUMMARY_FILE${NC}"
    echo ""

    # Display summary preview (first 20 lines)
    echo -e "${YELLOW}📝 Context Preview:${NC}"
    echo -e "${CYAN}$(head -20 "$SUMMARY_FILE")${NC}"
    echo ""
    echo -e "${YELLOW}... (full context loaded)${NC}"
    echo ""

    # Log context load
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] session-memory | context-loaded | $PROJECT_NAME" >> "$LOG_FILE"

    echo -e "${GREEN}✅ Project context loaded successfully!${NC}"
else
    echo -e "${YELLOW}ℹ️  No previous context found for: $PROJECT_NAME${NC}"
    echo -e "${BLUE}   This appears to be a new project.${NC}"
    echo ""
fi

################################################################################
# Ready!
################################################################################

echo -e "${GREEN}🚀 Ready to work on: $PROJECT_NAME${NC}"
echo ""

exit 0

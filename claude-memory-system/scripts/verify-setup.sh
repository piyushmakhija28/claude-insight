#!/bin/bash

# Memory System Verification Script
# Run this to verify your memory setup is correct

echo "========================================"
echo "  Memory System Verification"
echo "========================================"
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

ERRORS=0

# Check memory folder
echo "1. Checking memory folder..."
if [ -d "/c/Users/techd/.claude/memory" ]; then
    echo -e "${GREEN}✓${NC} Memory folder exists"
else
    echo -e "${RED}✗${NC} Memory folder missing"
    ERRORS=$((ERRORS+1))
fi

# Check core mandate file
echo "2. Checking core-skills-mandate.md..."
if [ -f "/c/Users/techd/.claude/memory/core-skills-mandate.md" ]; then
    echo -e "${GREEN}✓${NC} Core mandate file exists"
    LINES=$(wc -l < "/c/Users/techd/.claude/memory/core-skills-mandate.md")
    echo "   Lines: $LINES"
else
    echo -e "${RED}✗${NC} Core mandate file missing"
    ERRORS=$((ERRORS+1))
fi

# Check conventions file
echo "3. Checking conventions enforcement..."
if [ -f "/c/Users/techd/.claude/conventions/core-skills-enforcement.md" ]; then
    echo -e "${GREEN}✓${NC} Convention file exists"
else
    echo -e "${RED}✗${NC} Convention file missing"
    ERRORS=$((ERRORS+1))
fi

# Check context-management-core skill
echo "4. Checking context-management-core skill..."
if [ -d "/c/Users/techd/.claude/skills/context-management-core" ]; then
    echo -e "${GREEN}✓${NC} context-management-core skill exists"
    if [ -f "/c/Users/techd/.claude/skills/context-management-core/skill.md" ]; then
        echo -e "${GREEN}✓${NC} skill.md found"
    else
        echo -e "${RED}✗${NC} skill.md missing"
        ERRORS=$((ERRORS+1))
    fi
else
    echo -e "${RED}✗${NC} context-management-core skill missing"
    ERRORS=$((ERRORS+1))
fi

# Check model-selection-core skill
echo "5. Checking model-selection-core skill..."
if [ -d "/c/Users/techd/.claude/skills/model-selection-core" ]; then
    echo -e "${GREEN}✓${NC} model-selection-core skill exists"
    if [ -f "/c/Users/techd/.claude/skills/model-selection-core/skill.md" ]; then
        echo -e "${GREEN}✓${NC} skill.md found"
    else
        echo -e "${RED}✗${NC} skill.md missing"
        ERRORS=$((ERRORS+1))
    fi
else
    echo -e "${RED}✗${NC} model-selection-core skill missing"
    ERRORS=$((ERRORS+1))
fi

# Summary
echo ""
echo "========================================"
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed!${NC}"
    echo "Memory system is properly configured."
    echo ""
    echo "Next steps:"
    echo "1. Start a new Claude Code session"
    echo "2. Try asking vague questions to test context management"
    echo "3. Observe if Claude asks clarifying questions"
else
    echo -e "${RED}✗ Found $ERRORS error(s)${NC}"
    echo "Please fix the issues above."
fi
echo "========================================"

#!/bin/bash
# Enhanced Memory System Dashboard
# Shows comprehensive status of all memory system components

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

MEMORY_DIR="$HOME/.claude/memory"
SESSIONS_DIR="$MEMORY_DIR/sessions"
LOGS_DIR="$MEMORY_DIR/logs"

clear

echo -e "${CYAN}╔══════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║${NC}         ${PURPLE}Claude Memory System - Enhanced Dashboard${NC}              ${CYAN}║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# 1. System Status
echo -e "${BLUE}═══ 1. SYSTEM STATUS ═══${NC}"
echo ""

if [ -d "$MEMORY_DIR" ]; then
    echo -e "  ${GREEN}✓${NC} Memory directory: ${GREEN}Active${NC}"
else
    echo -e "  ${RED}✗${NC} Memory directory: ${RED}Not found${NC}"
fi

if [ -d "$SESSIONS_DIR" ]; then
    PROJECT_COUNT=$(find "$SESSIONS_DIR" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | wc -l)
    echo -e "  ${GREEN}✓${NC} Sessions directory: ${GREEN}Active${NC} ($PROJECT_COUNT projects)"
else
    echo -e "  ${RED}✗${NC} Sessions directory: ${RED}Not found${NC}"
fi

if [ -d "$LOGS_DIR" ]; then
    echo -e "  ${GREEN}✓${NC} Logs directory: ${GREEN}Active${NC}"
else
    echo -e "  ${YELLOW}!${NC} Logs directory: ${YELLOW}Not found${NC}"
fi

# Check Python
if command -v python &> /dev/null || command -v python3 &> /dev/null; then
    echo -e "  ${GREEN}✓${NC} Python: ${GREEN}Available${NC}"
else
    echo -e "  ${RED}✗${NC} Python: ${RED}Not found${NC} (some features disabled)"
fi

echo ""

# 2. Policy Status
echo -e "${BLUE}═══ 2. POLICY STATUS ═══${NC}"
echo ""

POLICIES=(
    "core-skills-mandate.md:Core Skills"
    "model-selection-enforcement.md:Model Selection"
    "proactive-consultation-policy.md:Proactive Consultation"
    "session-memory-policy.md:Session Memory"
    "user-preferences-policy.md:User Preferences"
    "session-pruning-policy.md:Session Pruning"
    "cross-project-patterns-policy.md:Cross-Project Patterns"
    "common-failures-prevention.md:Failure Prevention"
)

ACTIVE_POLICIES=0
TOTAL_POLICIES=${#POLICIES[@]}

for policy in "${POLICIES[@]}"; do
    IFS=':' read -r file name <<< "$policy"
    if [ -f "$MEMORY_DIR/$file" ]; then
        echo -e "  ${GREEN}✓${NC} $name"
        ((ACTIVE_POLICIES++))
    else
        echo -e "  ${RED}✗${NC} $name (missing)"
    fi
done

echo ""
POLICY_HEALTH=$((ACTIVE_POLICIES * 100 / TOTAL_POLICIES))
echo -e "  ${CYAN}Policy Health:${NC} $POLICY_HEALTH% ($ACTIVE_POLICIES/$TOTAL_POLICIES active)"

echo ""

# 3. User Preferences
echo -e "${BLUE}═══ 3. USER PREFERENCES ═══${NC}"
echo ""

if [ -f "$MEMORY_DIR/user-preferences.json" ]; then
    if command -v python &> /dev/null || command -v python3 &> /dev/null; then
        PYTHON_CMD=$(command -v python3 || command -v python)
        PREFS=$($PYTHON_CMD "$MEMORY_DIR/load-preferences.py" 2>/dev/null)

        if [ $? -eq 0 ]; then
            LEARNED_COUNT=$(echo "$PREFS" | grep -c "✓")
            TOTAL_CATEGORIES=$(echo "$PREFS" | grep -E "^  [✓-]" | wc -l)
            echo -e "  ${CYAN}Preferences learned:${NC} ${GREEN}$LEARNED_COUNT${NC} / $TOTAL_CATEGORIES categories"

            # Show learned preferences
            if [ $LEARNED_COUNT -gt 0 ]; then
                echo ""
                echo -e "  ${CYAN}Learned preferences:${NC}"
                echo "$PREFS" | grep "✓" | head -5 | sed 's/^/    /'
                if [ $LEARNED_COUNT -gt 5 ]; then
                    echo -e "    ${CYAN}... and $((LEARNED_COUNT - 5)) more${NC}"
                fi
            else
                echo -e "  ${YELLOW}!${NC} No preferences learned yet (need 3x repetition)"
            fi
        else
            echo -e "  ${YELLOW}!${NC} Unable to load preferences"
        fi
    else
        echo -e "  ${YELLOW}!${NC} Python not available"
    fi
else
    echo -e "  ${RED}✗${NC} No preferences file found"
fi

echo ""

# 4. Session Memory Statistics
echo -e "${BLUE}═══ 4. SESSION MEMORY ═══${NC}"
echo ""

if [ -d "$SESSIONS_DIR" ]; then
    ACTIVE_SESSIONS=$(find "$SESSIONS_DIR" -name "session-*.md" 2>/dev/null | wc -l)
    SUMMARIES=$(find "$SESSIONS_DIR" -name "project-summary.md" 2>/dev/null | wc -l)
    ARCHIVED=$(find "$SESSIONS_DIR"/*/archive -name "sessions.tar.gz" 2>/dev/null | wc -l)

    echo -e "  ${CYAN}Projects with memory:${NC} $SUMMARIES"
    echo -e "  ${CYAN}Active sessions:${NC} $ACTIVE_SESSIONS"

    if [ $ARCHIVED -gt 0 ]; then
        echo -e "  ${CYAN}Archived months:${NC} $ARCHIVED"
    fi

    # Most active project
    if [ $ACTIVE_SESSIONS -gt 0 ]; then
        echo ""
        echo -e "  ${CYAN}Most active projects:${NC}"
        find "$SESSIONS_DIR" -name "session-*.md" 2>/dev/null | \
            sed 's|.*/sessions/||;s|/.*||' | \
            sort | uniq -c | sort -rn | head -3 | \
            awk '{printf "    %s (%d sessions)\n", $2, $1}'
    fi
else
    echo -e "  ${RED}✗${NC} No sessions directory"
fi

echo ""

# 5. Cross-Project Patterns
echo -e "${BLUE}═══ 5. CROSS-PROJECT PATTERNS ═══${NC}"
echo ""

if [ -f "$MEMORY_DIR/cross-project-patterns.json" ]; then
    if command -v python &> /dev/null || command -v python3 &> /dev/null; then
        PYTHON_CMD=$(command -v python3 || command -v python)

        PATTERN_COUNT=$($PYTHON_CMD -c "import json; f=open('$MEMORY_DIR/cross-project-patterns.json'); d=json.load(f); print(len(d['patterns']))" 2>/dev/null)
        PROJECTS_ANALYZED=$($PYTHON_CMD -c "import json; f=open('$MEMORY_DIR/cross-project-patterns.json'); d=json.load(f); print(d['metadata'].get('projects_analyzed', 0))" 2>/dev/null)
        LAST_ANALYSIS=$($PYTHON_CMD -c "import json; f=open('$MEMORY_DIR/cross-project-patterns.json'); d=json.load(f); print(d['metadata'].get('last_analysis', 'Never'))" 2>/dev/null)

        if [ ! -z "$PATTERN_COUNT" ]; then
            echo -e "  ${CYAN}Patterns detected:${NC} $PATTERN_COUNT"
            echo -e "  ${CYAN}Projects analyzed:${NC} $PROJECTS_ANALYZED"
            echo -e "  ${CYAN}Last analysis:${NC} $LAST_ANALYSIS"

            # Show top patterns
            if [ $PATTERN_COUNT -gt 0 ]; then
                echo ""
                echo -e "  ${CYAN}Top patterns:${NC}"
                $PYTHON_CMD -c "
import json
import sys
sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None
with open('$MEMORY_DIR/cross-project-patterns.json') as f:
    data = json.load(f)
    patterns = sorted(data['patterns'], key=lambda x: x['confidence'], reverse=True)[:3]
    for p in patterns:
        conf_bar = '█' * int(p['confidence'] * 10)
        print(f\"    {p['name'].upper():15} [{conf_bar:10}] {int(p['confidence']*100)}%\")
" 2>/dev/null
            fi
        fi
    fi
else
    echo -e "  ${YELLOW}!${NC} No patterns detected yet"
    echo -e "    ${CYAN}Run:${NC} python $MEMORY_DIR/detect-patterns.py"
fi

echo ""

# 6. Skills Registry
echo -e "${BLUE}═══ 6. SKILLS REGISTRY ═══${NC}"
echo ""

if [ -f "$MEMORY_DIR/skills-registry.json" ]; then
    if command -v python &> /dev/null || command -v python3 &> /dev/null; then
        PYTHON_CMD=$(command -v python3 || command -v python)

        SKILL_COUNT=$($PYTHON_CMD -c "import json; f=open('$MEMORY_DIR/skills-registry.json'); d=json.load(f); print(len(d.get('skills', [])))" 2>/dev/null)

        if [ ! -z "$SKILL_COUNT" ]; then
            echo -e "  ${CYAN}Registered skills:${NC} $SKILL_COUNT"

            # Top used skills
            echo ""
            echo -e "  ${CYAN}Most used skills:${NC}"
            $PYTHON_CMD -c "
import json
import sys
sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None
with open('$MEMORY_DIR/skills-registry.json') as f:
    data = json.load(f)
    skills = sorted(data.get('skills', []), key=lambda x: x.get('usage_count', 0), reverse=True)[:3]
    for s in skills:
        count = s.get('usage_count', 0)
        print(f\"    {s['name']:30} (used {count}x)\")
" 2>/dev/null || echo "    (Unable to display)"
        fi
    fi
else
    echo -e "  ${YELLOW}!${NC} No skills registry found"
fi

echo ""

# 7. Policy Execution Statistics
echo -e "${BLUE}═══ 7. POLICY EXECUTION ═══${NC}"
echo ""

if [ -f "$LOGS_DIR/policy-counters.txt" ]; then
    echo -e "  ${CYAN}Top executed policies:${NC}"
    sort -t'=' -k2 -rn "$LOGS_DIR/policy-counters.txt" 2>/dev/null | head -5 | while IFS='=' read -r policy count; do
        printf "    %-30s : %s times\n" "$policy" "$count"
    done
else
    echo -e "  ${YELLOW}!${NC} No execution data yet"
fi

echo ""

# 8. Recent Activity
echo -e "${BLUE}═══ 8. RECENT ACTIVITY ═══${NC}"
echo ""

if [ -f "$LOGS_DIR/policy-hits.log" ]; then
    TOTAL_LOGS=$(wc -l < "$LOGS_DIR/policy-hits.log")
    echo -e "  ${CYAN}Total logged actions:${NC} $TOTAL_LOGS"
    echo ""
    echo -e "  ${CYAN}Last 5 actions:${NC}"
    tail -5 "$LOGS_DIR/policy-hits.log" | sed 's/^/    /'
else
    echo -e "  ${YELLOW}!${NC} No activity log found"
fi

echo ""

# 9. System Health
echo -e "${BLUE}═══ 9. SYSTEM HEALTH ═══${NC}"
echo ""

# Check disk usage
DISK_USAGE=$(du -sh "$MEMORY_DIR" 2>/dev/null | awk '{print $1}')
echo -e "  ${CYAN}Total disk usage:${NC} $DISK_USAGE"

# Check for conflicts
CONFLICTS=0
if [ -f "$MEMORY_DIR/conflicts.json" ]; then
    if command -v python &> /dev/null || command -v python3 &> /dev/null; then
        PYTHON_CMD=$(command -v python3 || command -v python)
        CONFLICTS=$($PYTHON_CMD -c "import json; f=open('$MEMORY_DIR/conflicts.json'); d=json.load(f); print(len(d.get('conflicts', [])))" 2>/dev/null || echo "0")
    fi
fi

if [ $CONFLICTS -gt 0 ]; then
    echo -e "  ${YELLOW}⚠${NC}  Conflicts detected: ${YELLOW}$CONFLICTS${NC}"
    echo -e "      ${CYAN}Run:${NC} bash $MEMORY_DIR/check-conflicts.sh"
else
    echo -e "  ${GREEN}✓${NC} No conflicts detected"
fi

# Failures prevented
if [ -f "$LOGS_DIR/failures.log" ]; then
    FAILURE_COUNT=$(grep -v "^#" "$LOGS_DIR/failures.log" 2>/dev/null | wc -l)
    if [ $FAILURE_COUNT -gt 0 ]; then
        echo -e "  ${GREEN}✓${NC} Failures prevented: ${GREEN}$FAILURE_COUNT${NC}"
    fi
fi

echo ""

# 10. Quick Actions
echo -e "${BLUE}═══ 10. QUICK ACTIONS ═══${NC}"
echo ""
echo -e "  ${CYAN}Detect patterns:${NC}       python $MEMORY_DIR/detect-patterns.py"
echo -e "  ${CYAN}View preferences:${NC}      python $MEMORY_DIR/load-preferences.py"
echo -e "  ${CYAN}Archive sessions:${NC}      python $MEMORY_DIR/archive-old-sessions.py --stats"
echo -e "  ${CYAN}Check conflicts:${NC}       bash $MEMORY_DIR/check-conflicts.sh"
echo -e "  ${CYAN}View this dashboard:${NC}   bash $MEMORY_DIR/dashboard.sh"

echo ""
echo -e "${CYAN}════════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}Dashboard last updated: $(date '+%Y-%m-%d %H:%M:%S')${NC}"
echo -e "${CYAN}════════════════════════════════════════════════════════════════════${NC}"

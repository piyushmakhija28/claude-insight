#!/bin/bash
# Memory System Conflict Detection
# Detects conflicts between preferences, patterns, and configurations

MEMORY_DIR="$HOME/.claude/memory"
CONFLICTS_FILE="$MEMORY_DIR/conflicts.json"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔍 Memory System - Conflict Detection${NC}"
echo "═══════════════════════════════════════════════════════════════"
echo ""

CONFLICTS=0

# Initialize conflicts file
cat > "$CONFLICTS_FILE" << 'EOF'
{
  "conflicts": [],
  "last_check": "",
  "total_conflicts": 0
}
EOF

# Function to add conflict
add_conflict() {
    local type="$1"
    local severity="$2"
    local description="$3"
    local suggestion="$4"

    echo -e "${YELLOW}⚠  CONFLICT DETECTED${NC}"
    echo -e "   Type: $type"
    echo -e "   Severity: $severity"
    echo -e "   Description: $description"
    echo -e "   Suggestion: $suggestion"
    echo ""

    ((CONFLICTS++))
}

# 1. Check User Preferences vs Cross-Project Patterns
echo -e "${CYAN}1. Checking Preferences vs Patterns...${NC}"

if command -v python &> /dev/null || command -v python3 &> /dev/null; then
    PYTHON_CMD=$(command -v python3 || command -v python)

    # Check if both files exist
    if [ -f "$MEMORY_DIR/user-preferences.json" ] && [ -f "$MEMORY_DIR/cross-project-patterns.json" ]; then
        # Check for REST preference vs GraphQL pattern
        REST_PREF=$($PYTHON_CMD -c "import json; f=open('$MEMORY_DIR/user-preferences.json'); d=json.load(f); print(d.get('technology_preferences', {}).get('api_style', ''))" 2>/dev/null)

        # Check patterns
        GRAPHQL_PATTERN=$($PYTHON_CMD -c "
import json
with open('$MEMORY_DIR/cross-project-patterns.json') as f:
    data = json.load(f)
    for p in data.get('patterns', []):
        if p['name'] == 'graphql' and p['confidence'] >= 0.6:
            print('graphql')
            break
" 2>/dev/null)

        if [ "$REST_PREF" = "REST" ] && [ "$GRAPHQL_PATTERN" = "graphql" ]; then
            add_conflict "Preference vs Pattern" "MEDIUM" \
                "User preference is REST but historical pattern shows GraphQL (60%+ confidence)" \
                "Review recent projects - pattern may have changed"
        fi

        # Check for JWT preference vs Session pattern
        JWT_PREF=$($PYTHON_CMD -c "import json; f=open('$MEMORY_DIR/user-preferences.json'); d=json.load(f); print(d.get('technology_preferences', {}).get('auth_method', ''))" 2>/dev/null)

        SESSION_PATTERN=$($PYTHON_CMD -c "
import json
with open('$MEMORY_DIR/cross-project-patterns.json') as f:
    data = json.load(f)
    for p in data.get('patterns', []):
        if p['name'] == 'session' and p['confidence'] >= 0.7:
            print('session')
            break
" 2>/dev/null)

        if [ "$JWT_PREF" = "jwt" ] && [ "$SESSION_PATTERN" = "session" ]; then
            add_conflict "Preference vs Pattern" "LOW" \
                "User preference is JWT but historical pattern shows Session auth (70%+ confidence)" \
                "User may be transitioning to JWT - monitor future projects"
        fi
    fi
fi

if [ $CONFLICTS -eq 0 ]; then
    echo -e "   ${GREEN}✓${NC} No conflicts between preferences and patterns"
fi

echo ""

# 2. Check Configuration Consistency
echo -e "${CYAN}2. Checking Configuration Consistency...${NC}"

if [ -f "$MEMORY_DIR/user-preferences.json" ]; then
    # Check for contradictory learning data
    if command -v python &> /dev/null || command -v python3 &> /dev/null; then
        PYTHON_CMD=$(command -v python3 || command -v python)

        CONTRADICTION=$($PYTHON_CMD -c "
import json
with open('$MEMORY_DIR/user-preferences.json') as f:
    data = json.load(f)
    learning = data.get('learning_data', {})

    # Check for testing contradictions
    testing_data = learning.get('testing', [])
    skip_count = sum(1 for item in testing_data if item.get('value') == 'skip')
    full_count = sum(1 for item in testing_data if item.get('value') == 'full_coverage')

    if skip_count >= 2 and full_count >= 2:
        print('testing_contradiction')
" 2>/dev/null)

        if [ "$CONTRADICTION" = "testing_contradiction" ]; then
            add_conflict "Preference Contradiction" "LOW" \
                "User has chosen both 'skip tests' and 'full coverage' multiple times" \
                "This is normal - preferences can vary by project context"
        fi
    fi
fi

if [ $CONFLICTS -eq 0 ]; then
    echo -e "   ${GREEN}✓${NC} No configuration contradictions"
fi

echo ""

# 3. Check Session Memory Integrity
echo -e "${CYAN}3. Checking Session Memory Integrity...${NC}"

SESSIONS_DIR="$MEMORY_DIR/sessions"
if [ -d "$SESSIONS_DIR" ]; then
    # Check for orphaned archives (archive exists but no active sessions)
    for project_dir in "$SESSIONS_DIR"/*/; do
        if [ -d "$project_dir" ]; then
            project_name=$(basename "$project_dir")
            archive_dir="$project_dir/archive"

            if [ -d "$archive_dir" ] && [ -n "$(ls -A "$archive_dir" 2>/dev/null)" ]; then
                # Check if project has any active sessions
                active_count=$(find "$project_dir" -maxdepth 1 -name "session-*.md" 2>/dev/null | wc -l)

                if [ $active_count -eq 0 ]; then
                    summary_exists=false
                    if [ -f "$project_dir/project-summary.md" ]; then
                        summary_exists=true
                    fi

                    if [ "$summary_exists" = false ]; then
                        add_conflict "Session Integrity" "LOW" \
                            "Project '$project_name' has archives but no active sessions or summary" \
                            "Consider extracting recent sessions or removing old archives"
                    fi
                fi
            fi
        fi
    done
fi

if [ $CONFLICTS -eq 0 ]; then
    echo -e "   ${GREEN}✓${NC} Session memory integrity OK"
fi

echo ""

# 4. Check Pattern Staleness
echo -e "${CYAN}4. Checking Pattern Freshness...${NC}"

if [ -f "$MEMORY_DIR/cross-project-patterns.json" ]; then
    if command -v python &> /dev/null || command -v python3 &> /dev/null; then
        PYTHON_CMD=$(command -v python3 || command -v python)

        LAST_ANALYSIS=$($PYTHON_CMD -c "import json; f=open('$MEMORY_DIR/cross-project-patterns.json'); d=json.load(f); print(d['metadata'].get('last_analysis', ''))" 2>/dev/null)

        if [ -n "$LAST_ANALYSIS" ]; then
            # Check if last analysis was more than 60 days ago
            if command -v date &> /dev/null; then
                LAST_EPOCH=$(date -d "$LAST_ANALYSIS" +%s 2>/dev/null || date -j -f "%Y-%m-%d %H:%M:%S" "$LAST_ANALYSIS" +%s 2>/dev/null || echo "0")
                NOW_EPOCH=$(date +%s)
                DAYS_AGO=$(( (NOW_EPOCH - LAST_EPOCH) / 86400 ))

                if [ $DAYS_AGO -gt 60 ]; then
                    add_conflict "Pattern Staleness" "LOW" \
                        "Patterns last analyzed $DAYS_AGO days ago (recommended: monthly)" \
                        "Run: python $MEMORY_DIR/detect-patterns.py"
                fi
            fi
        fi
    fi
fi

if [ $CONFLICTS -eq 0 ]; then
    echo -e "   ${GREEN}✓${NC} Patterns are fresh"
fi

echo ""

# 5. Check Disk Usage
echo -e "${CYAN}5. Checking Disk Usage...${NC}"

DISK_USAGE=$(du -s "$MEMORY_DIR" 2>/dev/null | awk '{print $1}')
if [ -n "$DISK_USAGE" ]; then
    # Convert to MB
    DISK_MB=$((DISK_USAGE / 1024))

    if [ $DISK_MB -gt 100 ]; then
        add_conflict "Disk Usage" "LOW" \
            "Memory system using ${DISK_MB}MB (recommended cleanup at 100MB+)" \
            "Run: python $MEMORY_DIR/archive-old-sessions.py"
    else
        echo -e "   ${GREEN}✓${NC} Disk usage OK (${DISK_MB}MB)"
    fi
else
    echo -e "   ${YELLOW}!${NC} Unable to check disk usage"
fi

echo ""

# Summary
echo "═══════════════════════════════════════════════════════════════"
if [ $CONFLICTS -eq 0 ]; then
    echo -e "${GREEN}✅ No conflicts detected - System healthy!${NC}"
else
    echo -e "${YELLOW}⚠  Found $CONFLICTS potential conflict(s)${NC}"
    echo ""
    echo "Most conflicts are informational and don't require immediate action."
    echo "Review suggestions above for optimization opportunities."
fi

# Update conflicts file
cat > "$CONFLICTS_FILE" << EOF
{
  "conflicts": [],
  "last_check": "$(date '+%Y-%m-%d %H:%M:%S')",
  "total_conflicts": $CONFLICTS
}
EOF

echo "═══════════════════════════════════════════════════════════════"

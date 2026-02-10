#!/bin/bash
# Local CLAUDE.md Migration Script
# Migrates local project CLAUDE.md files to session-based memory system

MEMORY_DIR="$HOME/.claude/memory"
SESSIONS_DIR="$MEMORY_DIR/sessions"
LOG_FILE="$MEMORY_DIR/logs/policy-hits.log"

PROJECT_DIR="${1:-$PWD}"
PROJECT_NAME=$(basename "$PROJECT_DIR")

# Skip if this is the global .claude directory
if [ "$(cd "$PROJECT_DIR" && pwd)" = "$(cd ~/.claude && pwd)" ]; then
    exit 0
fi

# Check for local CLAUDE.md
LOCAL_CLAUDE=""
if [ -f "$PROJECT_DIR/CLAUDE.md" ]; then
    LOCAL_CLAUDE="$PROJECT_DIR/CLAUDE.md"
elif [ -f "$PROJECT_DIR/claude.md" ]; then
    LOCAL_CLAUDE="$PROJECT_DIR/claude.md"
fi

# Exit if no local CLAUDE.md found
if [ -z "$LOCAL_CLAUDE" ]; then
    exit 0
fi

echo "[Migration] Found local CLAUDE.md in project: $PROJECT_NAME"

# Create session directory
SESSION_DIR="$SESSIONS_DIR/$PROJECT_NAME"
mkdir -p "$SESSION_DIR"
mkdir -p "$SESSION_DIR/backups"

SUMMARY_FILE="$SESSION_DIR/project-summary.md"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# Create or update project-summary.md
if [ -f "$SUMMARY_FILE" ]; then
    echo "[Migration] Merging with existing project-summary.md"
    cp "$SUMMARY_FILE" "$SUMMARY_FILE.backup-$(date +%Y%m%d-%H%M%S)"

    echo "" >> "$SUMMARY_FILE"
    echo "---" >> "$SUMMARY_FILE"
    echo "" >> "$SUMMARY_FILE"
    echo "## 📝 Migrated Local Project Instructions" >> "$SUMMARY_FILE"
    echo "" >> "$SUMMARY_FILE"
    echo "**Source:** Local CLAUDE.md (migrated on $TIMESTAMP)" >> "$SUMMARY_FILE"
    echo "" >> "$SUMMARY_FILE"
    cat "$LOCAL_CLAUDE" >> "$SUMMARY_FILE"
else
    echo "[Migration] Creating new project-summary.md"

    echo "# Project Memory: $PROJECT_NAME" > "$SUMMARY_FILE"
    echo "" >> "$SUMMARY_FILE"
    echo "**Last Updated:** $TIMESTAMP" >> "$SUMMARY_FILE"
    echo "**Status:** Active" >> "$SUMMARY_FILE"
    echo "" >> "$SUMMARY_FILE"
    echo "---" >> "$SUMMARY_FILE"
    echo "" >> "$SUMMARY_FILE"
    echo "## 📝 Project-Specific Instructions" >> "$SUMMARY_FILE"
    echo "" >> "$SUMMARY_FILE"
    echo "**Source:** Local CLAUDE.md (migrated on $TIMESTAMP)" >> "$SUMMARY_FILE"
    echo "" >> "$SUMMARY_FILE"
    cat "$LOCAL_CLAUDE" >> "$SUMMARY_FILE"
    echo "" >> "$SUMMARY_FILE"
    echo "---" >> "$SUMMARY_FILE"
    echo "" >> "$SUMMARY_FILE"
    echo "## 🎯 Session History" >> "$SUMMARY_FILE"
    echo "" >> "$SUMMARY_FILE"
    echo "This section will be automatically updated as you work on this project." >> "$SUMMARY_FILE"
    echo "" >> "$SUMMARY_FILE"
fi

# Create backup
BACKUP_FILE="$SESSION_DIR/backups/CLAUDE.md.backup-$(date +%Y%m%d-%H%M%S)"
cp "$LOCAL_CLAUDE" "$BACKUP_FILE"

# Delete local CLAUDE.md
rm -f "$LOCAL_CLAUDE"

# Log migration
echo "[$TIMESTAMP] local-claude-migration | migrated | $PROJECT_NAME | source: $LOCAL_CLAUDE" >> "$LOG_FILE"

echo "✅ Migration complete!"
echo "   → Migrated to: $SUMMARY_FILE"
echo "   → Backup: $BACKUP_FILE"
echo "   → Deleted local CLAUDE.md"
echo ""
echo "🎉 Global policies will now work properly!"

exit 0

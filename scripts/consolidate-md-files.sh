#!/bin/bash
#
# Consolidate MD Files
# Merges all .md files in a project into README.md with proper indexing
#

set -e

PROJECT_PATH="${1:-.}"

echo "================================================================================"
echo "📋 MARKDOWN FILES CONSOLIDATION"
echo "================================================================================"
echo ""
echo "Project Path: $PROJECT_PATH"
echo ""

cd "$PROJECT_PATH" || exit 1

# Find all .md files except README.md and CLAUDE.md
MD_FILES=$(find . -maxdepth 1 -name "*.md" ! -name "README.md" ! -name "CLAUDE.md" -type f)

if [ -z "$MD_FILES" ]; then
    echo "✅ No extra .md files found. Already compliant!"
    exit 0
fi

echo "📄 Found .md files to consolidate:"
echo "$MD_FILES" | sed 's/^/   - /'
echo ""

# Backup existing README.md if it exists
if [ -f "README.md" ]; then
    echo "📦 Backing up existing README.md..."
    cp README.md README.md.backup
    echo "   ✅ Backup created: README.md.backup"
    echo ""
fi

# Create new comprehensive README.md
echo "📝 Creating comprehensive README.md with Table of Contents..."
echo ""

# Get project name from directory name
PROJECT_NAME=$(basename "$PWD")

# Start building the new README
cat > README.md.new << 'EOF_HEADER'
# PROJECT_NAME_PLACEHOLDER

Brief project description

## Table of Contents

EOF_HEADER

# Replace project name placeholder
sed -i "s/PROJECT_NAME_PLACEHOLDER/$PROJECT_NAME/" README.md.new

# Generate Table of Contents entries
SECTION_NUMBER=1
declare -A FILE_TO_SECTION

echo "$MD_FILES" | while read -r file; do
    if [ -n "$file" ]; then
        filename=$(basename "$file" .md)
        # Convert filename to title case and create anchor
        section_title=$(echo "$filename" | sed 's/-/ /g' | sed 's/_/ /g' | awk '{for(i=1;i<=NF;i++)sub(/./,toupper(substr($i,1,1)),$i)}1')
        section_anchor=$(echo "$filename" | tr '[:upper:]' '[:lower:]' | sed 's/ /-/g')

        echo "$SECTION_NUMBER. [$section_title](#$section_anchor)" >> README.md.new
        FILE_TO_SECTION["$file"]="$section_title|$section_anchor"
        SECTION_NUMBER=$((SECTION_NUMBER + 1))
    fi
done

# Add separator after TOC
cat >> README.md.new << 'EOF_SEPARATOR'

---

EOF_SEPARATOR

# Add content from each file as a section
echo "$MD_FILES" | while read -r file; do
    if [ -n "$file" ]; then
        filename=$(basename "$file" .md)
        section_title=$(echo "$filename" | sed 's/-/ /g' | sed 's/_/ /g' | awk '{for(i=1;i<=NF;i++)sub(/./,toupper(substr($i,1,1)),$i)}1')
        section_anchor=$(echo "$filename" | tr '[:upper:]' '[:lower:]' | sed 's/ /-/g')

        # Add section header
        echo "" >> README.md.new
        echo "## $section_title" >> README.md.new
        echo "" >> README.md.new

        # Add content from file
        cat "$file" >> README.md.new

        # Add separator
        echo "" >> README.md.new
        echo "---" >> README.md.new
        echo "" >> README.md.new
    fi
done

# Add footer
cat >> README.md.new << 'EOF_FOOTER'

## Additional Information

**Documentation Standards:** This README.md consolidates all project documentation following the 2-file markdown policy.

**Last Updated:** TIMESTAMP_PLACEHOLDER

EOF_FOOTER

# Replace timestamp
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")
sed -i "s/TIMESTAMP_PLACEHOLDER/$TIMESTAMP/" README.md.new

# Replace old README
mv README.md.new README.md
echo "   ✅ README.md created with comprehensive content"
echo ""

# Delete consolidated files
echo "🗑️  Deleting consolidated .md files..."
echo "$MD_FILES" | while read -r file; do
    if [ -n "$file" ]; then
        echo "   - Deleting: $file"
        rm -f "$file"
    fi
done
echo "   ✅ All extra .md files deleted"
echo ""

# Check final state
REMAINING_MD=$(find . -maxdepth 1 -name "*.md" -type f | wc -l)

echo "================================================================================"
echo "✅ CONSOLIDATION COMPLETE"
echo "================================================================================"
echo ""
echo "📊 Final State:"
echo "   - Remaining .md files: $REMAINING_MD"
find . -maxdepth 1 -name "*.md" -type f | sed 's/^/     /'
echo ""
echo "✅ README.md now contains all documentation with indexing"
echo "✅ Project compliant with 2-file markdown policy"
echo ""

exit 0

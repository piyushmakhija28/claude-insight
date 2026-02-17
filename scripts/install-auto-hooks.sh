#!/bin/bash
#
# Install Automatic Policy Enforcement Hooks
#
# This creates hooks that run automatically in Claude Code
# Making policy enforcement truly automatic
#

set -e

CLAUDE_DIR="$HOME/.claude"
MEMORY_DIR="$CLAUDE_DIR/memory"
HOOKS_FILE="$CLAUDE_DIR/hooks.json"

echo "================================================================================"
echo "🔧 INSTALLING AUTO-ENFORCEMENT HOOKS"
echo "================================================================================"
echo ""

# Create hooks.json if it doesn't exist
if [ ! -f "$HOOKS_FILE" ]; then
    echo "📝 Creating hooks.json..."
    cat > "$HOOKS_FILE" << 'EOF'
{
  "version": "1.0.0",
  "hooks": {}
}
EOF
    echo "   ✅ Created hooks.json"
else
    echo "   ✅ hooks.json already exists"
fi

# Backup existing hooks
if [ -f "$HOOKS_FILE" ]; then
    cp "$HOOKS_FILE" "$HOOKS_FILE.backup"
    echo "   ✅ Backed up existing hooks"
fi

# Install pre-request hook
echo ""
echo "📦 Installing pre-request hook..."

# Create hook configuration
python << 'PYTHON_SCRIPT'
import sys
import json
from pathlib import Path

# Fix encoding
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

hooks_file = Path.home() / '.claude' / 'hooks.json'
memory_dir = Path.home() / '.claude' / 'memory'

# Load existing hooks
if hooks_file.exists():
    with open(hooks_file, 'r', encoding='utf-8') as f:
        hooks = json.load(f)
else:
    hooks = {"version": "1.0.0", "hooks": {}}

# Add pre-request hook
hooks['hooks']['pre-request'] = {
    "enabled": True,
    "script": str(memory_dir / 'auto-enforce-all-policies.sh'),
    "description": "Automatic 3-level architecture policy enforcement",
    "mode": "blocking",
    "timeout": 30000
}

# Add user-prompt-submit hook (if available in Claude Code)
hooks['hooks']['user-prompt-submit'] = {
    "enabled": True,
    "script": str(memory_dir / 'auto-enforce-all-policies.sh'),
    "description": "Runs before processing user prompt",
    "mode": "blocking",
    "timeout": 30000
}

# Save hooks
with open(hooks_file, 'w', encoding='utf-8') as f:
    json.dump(hooks, f, indent=2)

print("   OK Hooks installed successfully")
print(f"   Location: {hooks_file}")
PYTHON_SCRIPT

echo ""
echo "================================================================================"
echo "✅ HOOKS INSTALLATION COMPLETE"
echo "================================================================================"
echo ""
echo "📋 Installed Hooks:"
echo "   1. pre-request hook → Runs auto-enforce-all-policies.sh"
echo "   2. user-prompt-submit hook → Runs auto-enforce-all-policies.sh"
echo ""
echo "🎯 Automation Level: FULL"
echo "   • Policies run automatically before EVERY request"
echo "   • No manual intervention needed"
echo "   • Blocking mode (must pass to proceed)"
echo ""
echo "📖 View hooks: cat ~/.claude/hooks.json"
echo "🔧 Disable: Edit ~/.claude/hooks.json and set enabled: false"
echo ""
echo "================================================================================"

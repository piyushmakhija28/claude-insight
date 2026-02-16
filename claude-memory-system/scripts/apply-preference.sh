#!/bin/bash
# Global User Preference Application Helper
# Checks if a preference exists and suggests the appropriate action.
#
# Usage:
#   bash apply-preference.sh <category> <question> <default_if_not_set>
#
# Examples:
#   bash apply-preference.sh testing "Skip tests?" "ask"
#   bash apply-preference.sh api_style "Use REST or GraphQL?" "ask"
#   bash apply-preference.sh plan_mode "Enter plan mode?" "ask"

CATEGORY="$1"
QUESTION="$2"
DEFAULT="$3"

# Load preference
PREF_VALUE=$(python ~/.claude/memory/load-preferences.py "$CATEGORY" 2>/dev/null)

if [ -n "$PREF_VALUE" ]; then
    # Preference exists - use it
    echo "preference_found"
    echo "$PREF_VALUE"

    # Log the application
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] user-preferences | applied | $CATEGORY=$PREF_VALUE" >> ~/.claude/memory/logs/policy-hits.log
else
    # No preference - ask user or use default
    echo "preference_not_found"
    echo "$DEFAULT"
fi

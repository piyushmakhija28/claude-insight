#!/bin/bash
#
# Session Start Script - Complete Automation
# Run this at the start of every conversation
#

echo ""
echo "=================================================="
echo "SESSION START - Initializing Automation"
echo "=================================================="
echo ""

# Step 1: Start auto-recommendation daemon
echo "[1/2] Starting auto-recommendation daemon..."
nohup python ~/.claude/memory/auto-recommendation-daemon.py start > /dev/null 2>&1 &
sleep 2
echo "  Started"
echo ""

# Step 2: Run session start check
echo "[2/2] Running session start check..."
echo ""
python ~/.claude/memory/session-start-check.py

echo ""
echo "Session initialization complete!"
echo ""

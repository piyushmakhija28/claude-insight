#!/usr/bin/env bash
# Test Intelligent Prompt Generator
# No Python imports - Direct execution

echo "================================================================================"
echo "TESTING INTELLIGENT PROMPT GENERATOR"
echo "================================================================================"

cd ~/.claude/memory/03-execution-system/00-prompt-generation

echo ""
echo "================================================================================"
echo "TEST 1: Hinglish Input"
echo "================================================================================"
echo "Input: 'admin wala ni ara, overlapping ho rahi hai, logout ni hai'"
echo ""
python prompt-generator.py "admin wala ni ara, overlapping ho rahi hai, logout ni hai" 2>&1 | grep -A 30 "task_type:"

echo ""
echo "================================================================================"
echo "TEST 2: Full Claude Insight Dashboard Message"
echo "================================================================================"
echo "Input: 'Fix Claude Insight dashboard - admin panel not showing, UI overlapping'"
echo ""
python prompt-generator.py "Fix Claude Insight dashboard - admin panel not showing, UI overlapping in live metrics, no logout button" 2>&1 | grep -A 30 "task_type:"

echo ""
echo "================================================================================"
echo "TEST 3: Simple Dashboard Issue"
echo "================================================================================"
echo "Input: 'dashboard me overlapping fix karo'"
echo ""
python prompt-generator.py "dashboard me overlapping fix karo" 2>&1 | grep -A 30 "task_type:"

echo ""
echo "================================================================================"
echo "TEST 4: Logout Button"
echo "================================================================================"
echo "Input: 'logout button add karna hai'"
echo ""
python prompt-generator.py "logout button add karna hai" 2>&1 | grep -A 30 "task_type:"

echo ""
echo "================================================================================"
echo "✅ ALL TESTS COMPLETE"
echo "================================================================================"

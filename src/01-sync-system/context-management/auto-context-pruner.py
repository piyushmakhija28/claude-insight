#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Automatic Context Pruner
Monitors context usage and auto-prunes when >70%

Features:
1. Monitor context percentage
2. Auto-save session before pruning
3. Suggest compact command
4. Log pruning events

Usage (called automatically by daemon):
    python auto-context-pruner.py --check
    python auto-context-pruner.py --prune
"""

import sys
import os
import json
from datetime import datetime
from pathlib import Path

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

MEMORY_DIR = os.path.expanduser("~/.claude/memory")
PRUNE_LOG = os.path.join(MEMORY_DIR, "logs/context-pruning.log")

# Import modules using importlib (files have hyphens)
try:
    import importlib.util

    # Load context-monitor-v2.py
    spec = importlib.util.spec_from_file_location(
        "context_monitor_v2",
        os.path.join(MEMORY_DIR, "context-monitor-v2.py")
    )
    context_monitor_v2 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(context_monitor_v2)

    # Load auto-save-session.py
    spec = importlib.util.spec_from_file_location(
        "auto_save_session",
        os.path.join(MEMORY_DIR, "01-sync-system", "session-management", "auto-save-session.py")
    )
    auto_save_session = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(auto_save_session)

    DIRECT_IMPORT_AVAILABLE = True
except Exception as e:
    print(f"Warning: Could not import modules, using subprocess fallback: {e}", file=sys.stderr)
    import subprocess
    DIRECT_IMPORT_AVAILABLE = False

def log_prune_event(event_type, context_percent, details=""):
    """Log pruning event"""
    try:
        os.makedirs(os.path.dirname(PRUNE_LOG), exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {event_type} | Context: {context_percent}% | {details}\n"

        with open(PRUNE_LOG, 'a', encoding='utf-8') as f:
            f.write(log_entry)
    except Exception as e:
        print(f"Warning: Could not log pruning: {e}", file=sys.stderr)

def get_context_status():
    """Get current context status"""
    try:
        if DIRECT_IMPORT_AVAILABLE:
            # Direct class instantiation
            monitor = context_monitor_v2.ContextMonitorV2()
            return monitor.get_current_status()
        else:
            # Fallback to subprocess
            import subprocess
            result = subprocess.run(
                ["python", os.path.join(MEMORY_DIR, "context-monitor-v2.py"), "--current-status"],
                capture_output=True,
                text=True,
                timeout=5,
                creationflags=0x08000000 if sys.platform == 'win32' else 0
            )

            if result.returncode == 0:
                return json.loads(result.stdout)
            return None
    except:
        return None

def save_session(project_name):
    """Save session before pruning"""
    try:
        if DIRECT_IMPORT_AVAILABLE:
            # Direct function call
            summary = auto_save_session.generate_session_summary(project_name)
            result = auto_save_session.save_session_summary(project_name, summary)
            return result
        else:
            # Fallback to subprocess
            import subprocess
            result = subprocess.run(
                ["python", os.path.join(MEMORY_DIR, "01-sync-system", "session-management", "auto-save-session.py"), "--project", project_name],
                capture_output=True,
                text=True,
                timeout=30,
                creationflags=0x08000000 if sys.platform == 'win32' else 0
            )
            return result.returncode == 0
    except:
        return False

def check_and_prune():
    """Check context and prune if needed"""
    status = get_context_status()

    if not status:
        return {
            'checked': False,
            'error': 'Could not get context status'
        }

    percentage = status.get('percentage', 0)
    level = status.get('level', 'green')

    if percentage < 70:
        log_prune_event('CHECK', percentage, 'No pruning needed (green zone)')
        return {
            'checked': True,
            'prune_needed': False,
            'percentage': percentage,
            'level': level,
            'message': 'Context is healthy'
        }

    elif percentage < 85:
        log_prune_event('WARNING', percentage, 'Context elevated (yellow zone)')
        return {
            'checked': True,
            'prune_needed': False,
            'percentage': percentage,
            'level': level,
            'message': 'Context elevated, monitor closely',
            'suggestion': 'Use cache, offset/limit, head_limit more aggressively'
        }

    elif percentage < 90:
        log_prune_event('ALERT', percentage, 'Context high (orange zone)')

        # Auto-save session
        project = os.path.basename(os.getcwd())
        saved = save_session(project)

        return {
            'checked': True,
            'prune_needed': True,
            'percentage': percentage,
            'level': level,
            'message': 'Context high, pruning recommended',
            'session_saved': saved,
            'action': 'Suggest: claude compact'
        }

    else:  # >= 90%
        log_prune_event('CRITICAL', percentage, 'Context critical (red zone)')

        # Auto-save session
        project = os.path.basename(os.getcwd())
        saved = save_session(project)

        return {
            'checked': True,
            'prune_needed': True,
            'percentage': percentage,
            'level': level,
            'message': 'Context CRITICAL, immediate pruning required',
            'session_saved': saved,
            'action': 'EXECUTE: claude compact --full'
        }

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Auto Context Pruner')
    parser.add_argument('--check', action='store_true', help='Check and prune if needed')
    parser.add_argument('--prune', action='store_true', help='Force prune (save session)')

    args = parser.parse_args()

    if args.check or args.prune:
        result = check_and_prune()
        print(json.dumps(result, indent=2))
    else:
        parser.print_help()

if __name__ == "__main__":
    main()

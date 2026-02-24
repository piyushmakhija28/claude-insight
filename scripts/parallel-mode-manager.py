#!/usr/bin/env python
# Script Name: parallel-mode-manager.py
# Version: 1.0.0
# Last Modified: 2026-02-24
# Description: Auto-detect parallel execution and switch hook modes
# Author: Claude Memory System
#
# Policies enforced:
#   - Detects when 2+ async tasks are running
#   - Switches to lightweight hook mode (skip verbose output, reduce timeouts)
#   - Restores normal mode when parallel execution completes
#
# Windows-safe: ASCII only, no Unicode chars

import sys
import json
from pathlib import Path
from datetime import datetime, timedelta

HOME = Path.home()
FLAG_DIR = HOME / '.claude'
PARALLEL_MODE_FILE = FLAG_DIR / '.parallel-mode-active.json'
TASK_TRACKING_FILE = FLAG_DIR / 'memory' / 'logs' / 'tool-tracker.jsonl'


def count_active_tasks():
    """Count tasks that started in the last 5 minutes (active/pending)."""
    if not TASK_TRACKING_FILE.exists():
        return 0

    try:
        active_count = 0
        cutoff = datetime.now() - timedelta(minutes=5)

        with open(TASK_TRACKING_FILE, 'r', encoding='utf-8', errors='replace') as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    log = json.loads(line)
                    if log.get('tool') == 'Task' and log.get('status') == 'start':
                        log_time = datetime.fromisoformat(log.get('timestamp', ''))
                        if log_time > cutoff:
                            active_count += 1
                except:
                    pass

        return active_count
    except:
        return 0


def is_parallel_mode_active():
    """Check if parallel mode is currently active."""
    try:
        if PARALLEL_MODE_FILE.exists():
            with open(PARALLEL_MODE_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            expiry = datetime.fromisoformat(data.get('expires', ''))
            if datetime.now() < expiry:
                return True
    except:
        pass
    return False


def enable_parallel_mode():
    """Enable parallel mode for 10 minutes."""
    PARALLEL_MODE_FILE.parent.mkdir(parents=True, exist_ok=True)
    expires = datetime.now() + timedelta(minutes=10)
    data = {
        'active': True,
        'started': datetime.now().isoformat(),
        'expires': expires.isoformat(),
        'task_count': count_active_tasks()
    }
    with open(PARALLEL_MODE_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f)


def disable_parallel_mode():
    """Disable parallel mode."""
    if PARALLEL_MODE_FILE.exists():
        PARALLEL_MODE_FILE.unlink()


def check_and_update_mode():
    """
    Check active tasks and update parallel mode.
    Returns: 'parallel' or 'normal'
    """
    active_tasks = count_active_tasks()

    if active_tasks >= 2:
        enable_parallel_mode()
        return 'parallel'
    else:
        disable_parallel_mode()
        return 'normal'


if __name__ == '__main__':
    mode = check_and_update_mode()
    print(mode)
    sys.exit(0)

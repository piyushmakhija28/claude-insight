#!/usr/bin/env python
# Script Name: parallel-mode-enforcer.py
# Version: 1.0.0
# Last Modified: 2026-02-24
# Description: Lightweight hook that detects parallel mode and skips verbose output
# Author: Claude Memory System
#
# Hook Type: UserPromptSubmit (wrapper)
# Trigger: Before UserPromptSubmit hooks execute
# Decision: Skip 3-level-flow.py output if 2+ tasks running, run normally otherwise
#
# Windows-safe: ASCII only, no Unicode chars

import sys
import subprocess
from pathlib import Path

HOME = Path.home()
CURRENT_DIR = HOME / '.claude' / 'memory' / 'current'
MANAGER = CURRENT_DIR / 'parallel-mode-manager.py'


def get_mode():
    """Get current execution mode (parallel or normal)."""
    try:
        result = subprocess.run(
            [sys.executable, str(MANAGER)],
            capture_output=True,
            timeout=3,
            text=True
        )
        return result.stdout.strip()
    except:
        return 'normal'


def run_clear_session():
    """Run clear-session-handler.py (always runs)."""
    try:
        handler = CURRENT_DIR / 'clear-session-handler.py'
        subprocess.run(
            [sys.executable, str(handler)],
            capture_output=True,
            timeout=15
        )
    except:
        pass


def run_flow_trace():
    """Run 3-level-flow.py --summary (only if not in parallel mode)."""
    try:
        flow = CURRENT_DIR / '3-level-flow.py'
        subprocess.run(
            [sys.executable, str(flow), '--summary'],
            capture_output=True,
            timeout=30
        )
    except:
        pass


if __name__ == '__main__':
    mode = get_mode()

    # Always run session handler
    run_clear_session()

    # Skip verbose flow trace if parallel mode active
    if mode == 'normal':
        run_flow_trace()
    else:
        # In parallel mode, show minimal info
        print('[PARALLEL MODE] Skipping verbose architecture trace. Running 2/5 agents...')

    sys.exit(0)

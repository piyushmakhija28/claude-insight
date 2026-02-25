#!/usr/bin/env python
# Script Name: post-tool-tracker.py
# Version: 1.0.0
# Last Modified: 2026-02-19
# Description: PostToolUse hook - Level 3.9 (task auto-tracking)
# Author: Claude Memory System
#
# Hook Type: PostToolUse
# Trigger: Runs AFTER every tool call (NEVER blocks)
# Exit: Always 0
#
# Policies enforced:
#   Level 3.9 - Execute Tasks (Auto-Tracking):
#     - Read  -> progress +10%
#     - Write -> progress +40%  (likely completed something)
#     - Edit  -> progress +30%  (likely completed something)
#     - Bash  -> progress +15%  (ran a command)
#     - Task  -> progress +20%  (delegated work)
#     - Grep/Glob -> progress +5% (searching)
#
# Logs to: ~/.claude/memory/logs/tool-tracker.jsonl
# Windows-safe: ASCII only, no Unicode chars

import sys
import json
from pathlib import Path
from datetime import datetime

# Progress delta per tool call (approximate % contribution)
PROGRESS_DELTA = {
    'Read':         10,
    'Write':        40,
    'Edit':         30,
    'NotebookEdit': 25,
    'Bash':         15,
    'Task':         20,
    'Grep':          5,
    'Glob':          5,
    'WebFetch':      8,
    'WebSearch':     8,
}

# Session state file to accumulate progress
SESSION_STATE_FILE = Path.home() / '.claude' / 'memory' / 'logs' / 'session-progress.json'
TRACKER_LOG = Path.home() / '.claude' / 'memory' / 'logs' / 'tool-tracker.jsonl'


def load_session_progress():
    """Load current session progress."""
    try:
        if SESSION_STATE_FILE.exists():
            with open(SESSION_STATE_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data
    except Exception:
        pass
    return {
        'total_progress': 0,
        'tool_counts': {},
        'started_at': datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
        'tasks_completed': 0,
        'errors_seen': 0,
    }


def save_session_progress(state):
    """Save current session progress."""
    try:
        SESSION_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(SESSION_STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2)
    except Exception:
        pass


def log_tool_entry(entry):
    """Append tool usage entry to tracker log."""
    try:
        TRACKER_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(TRACKER_LOG, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry) + '\n')
    except Exception:
        pass


def is_error_response(tool_response):
    """Check if the tool call resulted in an error."""
    if isinstance(tool_response, dict):
        # Check for is_error flag
        if tool_response.get('is_error', False):
            return True
        # Check content for error indicators
        content = tool_response.get('content', '')
        if isinstance(content, str):
            lower = content.lower()
            if lower.startswith('error:') or lower.startswith('failed:'):
                return True
    return False


def main():
    # Read tool result from stdin
    try:
        raw = sys.stdin.read()
        if not raw or not raw.strip():
            sys.exit(0)
        data = json.loads(raw)
    except Exception:
        sys.exit(0)

    tool_name = data.get('tool_name', '')
    tool_input = data.get('tool_input', {})
    tool_response = data.get('tool_response', {})

    try:
        # Determine status
        is_error = is_error_response(tool_response)
        status = 'error' if is_error else 'success'

        # Calculate progress delta
        delta = 0 if is_error else PROGRESS_DELTA.get(tool_name, 0)

        # Build log entry
        entry = {
            'ts': datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
            'tool': tool_name,
            'status': status,
            'progress_delta': delta,
        }

        # Add file path info for file operations (useful for tracking what was done)
        if tool_name in ('Read', 'Write', 'Edit', 'NotebookEdit'):
            file_path = (
                (tool_input or {}).get('file_path', '') or
                (tool_input or {}).get('notebook_path', '') or
                ''
            )
            if file_path:
                # Shorten path for log readability
                parts = file_path.replace('\\', '/').split('/')
                entry['file'] = '/'.join(parts[-3:]) if len(parts) > 3 else file_path

        # Log the entry
        log_tool_entry(entry)

        # Update session progress
        state = load_session_progress()
        state['total_progress'] = min(100, state['total_progress'] + delta)
        state['tool_counts'][tool_name] = state['tool_counts'].get(tool_name, 0) + 1
        state['last_tool'] = tool_name
        state['last_tool_at'] = entry['ts']

        if is_error:
            state['errors_seen'] = state.get('errors_seen', 0) + 1

        # Auto-complete threshold: if Write/Edit happened, likely a task completed
        if tool_name in ('Write', 'Edit') and not is_error:
            state['tasks_completed'] = state.get('tasks_completed', 0) + 1

        save_session_progress(state)

    except Exception:
        pass  # NEVER block on tracking errors

    sys.exit(0)


if __name__ == '__main__':
    main()

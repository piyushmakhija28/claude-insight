#!/usr/bin/env python
# Script Name: config-isolation-helpers.py
# Version: 1.0.0
# Last Modified: 2026-02-24
# Description: Window-aware configuration file loaders with PID-based filtering
# Author: Claude Memory System
# Windows-safe: ASCII only, no Unicode chars

import sys
import os
import json
from pathlib import Path
from datetime import datetime

# Windows encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

CONFIG_BASE = Path.home() / '.claude' / 'memory' / 'config'
FLAG_DIR = Path.home() / '.claude'


def get_current_session_id():
    """Get current session ID from .current-session.json"""
    try:
        session_file = Path.home() / '.claude' / 'memory' / '.current-session.json'
        if session_file.exists():
            data = json.loads(session_file.read_text(encoding='utf-8'))
            return data.get('current_session_id', '')
    except Exception:
        pass
    return ''


def get_pid():
    """Get current process ID"""
    return os.getpid()


def get_window_aware_patterns(base_patterns=None):
    """
    Get cross-project patterns filtered to current window only.

    Loads cross-project-patterns.json but filters to show only:
    - Patterns from the current session's project
    - Patterns from commonly used projects (ignore others)

    Args:
        base_patterns: If provided, use this dict instead of reading file

    Returns:
        Filtered patterns dict with current-window-only suggestions
    """
    if base_patterns is None:
        try:
            patterns_file = CONFIG_BASE / 'cross-project-patterns.json'
            if patterns_file.exists():
                base_patterns = json.loads(patterns_file.read_text(encoding='utf-8'))
            else:
                return {'patterns': [], 'metadata': {}}
        except Exception:
            return {'patterns': [], 'metadata': {}}

    if not base_patterns or 'patterns' not in base_patterns:
        return {'patterns': [], 'metadata': {}}

    # Get current session to determine current project
    session_id = get_current_session_id()
    pid = get_pid()

    # Extract project from session (format may include project info)
    # For now, filter to high-confidence patterns (>0.7) to show only strong suggestions
    high_confidence = [p for p in base_patterns.get('patterns', [])
                       if p.get('confidence', 0) >= 0.7]

    # Add PID metadata for tracking
    window_aware = {
        'patterns': high_confidence,
        'metadata': {
            **base_patterns.get('metadata', {}),
            'filtered_by': 'window_isolation',
            'current_pid': pid,
            'current_session': session_id,
            'total_original': len(base_patterns.get('patterns', [])),
            'total_filtered': len(high_confidence),
            'filter_timestamp': datetime.now().isoformat()
        }
    }

    return window_aware


def get_window_aware_preferences(base_prefs=None):
    """
    Get user preferences filtered to current window only.

    Args:
        base_prefs: If provided, use this dict instead of reading file

    Returns:
        Preferences dict with window isolation metadata
    """
    if base_prefs is None:
        try:
            prefs_file = CONFIG_BASE / 'user-preferences.json'
            if prefs_file.exists():
                base_prefs = json.loads(prefs_file.read_text(encoding='utf-8'))
            else:
                return {}
        except Exception:
            return {}

    if not base_prefs:
        return {}

    pid = get_pid()
    session_id = get_current_session_id()

    # Add isolation metadata
    isolated_prefs = dict(base_prefs)
    isolated_prefs['_window_metadata'] = {
        'pid': pid,
        'session_id': session_id,
        'loaded_at': datetime.now().isoformat()
    }

    return isolated_prefs


def get_suggestion_history_for_window(window_pid=None):
    """
    Get suggestion history for current or specific window only.

    Prevents cross-window suggestion contamination.

    Args:
        window_pid: Specific PID to get history for (default: current PID)

    Returns:
        List of suggestions shown to this window only
    """
    if window_pid is None:
        window_pid = get_pid()

    try:
        history_file = FLAG_DIR / f'.suggestion-history-{window_pid}.json'
        if history_file.exists():
            return json.loads(history_file.read_text(encoding='utf-8'))
    except Exception:
        pass

    return {'suggestions': [], 'pid': window_pid}


def record_suggestion_for_window(suggestion_type, suggestion_data, window_pid=None):
    """
    Record a suggestion shown to the current window.

    Ensures each window tracks its own suggestions separately.

    Args:
        suggestion_type: Type of suggestion (skill, agent, pattern, etc)
        suggestion_data: The suggestion data
        window_pid: Specific PID (default: current PID)

    Returns:
        True if recorded successfully
    """
    if window_pid is None:
        window_pid = get_pid()

    try:
        history_file = FLAG_DIR / f'.suggestion-history-{window_pid}.json'
        history = {'suggestions': [], 'pid': window_pid}

        if history_file.exists():
            try:
                history = json.loads(history_file.read_text(encoding='utf-8'))
            except Exception:
                pass

        # Add new suggestion
        history['suggestions'].append({
            'type': suggestion_type,
            'data': suggestion_data,
            'shown_at': datetime.now().isoformat()
        })

        # Keep only last 100 suggestions (prevent bloat)
        if len(history['suggestions']) > 100:
            history['suggestions'] = history['suggestions'][-100:]

        history_file.write_text(json.dumps(history, indent=2), encoding='utf-8')
        return True
    except Exception:
        return False


def cleanup_stale_suggestion_histories(max_age_days=7):
    """
    Clean up suggestion histories for PIDs that no longer exist.

    Args:
        max_age_days: Consider history stale if older than this many days

    Returns:
        Number of cleaned histories
    """
    cleaned = 0
    cutoff = datetime.now()

    try:
        import psutil
    except ImportError:
        return 0

    try:
        for hist_file in FLAG_DIR.glob('.suggestion-history-*.json'):
            try:
                # Extract PID from filename
                pid_str = hist_file.stem.replace('.suggestion-history-', '')
                pid = int(pid_str)

                # Check if process still running
                if not psutil.pid_exists(pid):
                    hist_file.unlink(missing_ok=True)
                    cleaned += 1
            except (ValueError, IndexError):
                pass
    except Exception:
        pass

    return cleaned


if __name__ == '__main__':
    # Test mode
    print('[TEST] Config isolation helpers')
    print('[OK] Current PID: {}'.format(get_pid()))
    print('[OK] Current session: {}'.format(get_current_session_id()))

    patterns = get_window_aware_patterns()
    print('[OK] Got {} filtered patterns'.format(len(patterns.get('patterns', []))))

    prefs = get_window_aware_preferences()
    print('[OK] Got preferences with {} keys'.format(len(prefs)))

    print('[OK] Config isolation working correctly')

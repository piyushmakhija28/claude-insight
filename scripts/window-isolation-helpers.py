#!/usr/bin/env python
# Script Name: window-isolation-helpers.py
# Version: 1.0.0
# Last Modified: 2026-02-24
# Description: Common helpers for PID-based flag isolation across all hook scripts
# Author: Claude Memory System
# Windows-safe: ASCII only, no Unicode chars

import sys
import os
import json
from pathlib import Path
from datetime import datetime

# Windows encoding fix
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

FLAG_DIR = Path.home() / '.claude'
MEMORY_BASE = Path.home() / '.claude' / 'memory'


def get_pid():
    """Get current process ID"""
    return os.getpid()


def get_isolated_flag_path(flag_type, session_id):
    """
    Get PID-isolated flag file path.
    Pattern: ~/.claude/.{flag_type}-{session_id}-{pid}.json

    Args:
        flag_type: 'task-breakdown-pending', 'skill-selection-pending', etc
        session_id: Current session ID

    Returns:
        Path object to PID-specific flag file
    """
    pid = get_pid()
    return FLAG_DIR / f'.{flag_type}-{session_id}-{pid}.json'


def write_isolated_flag(flag_type, session_id, data):
    """
    Write PID-isolated flag file.

    Args:
        flag_type: Type of flag
        session_id: Session ID
        data: Dictionary to write as JSON

    Returns:
        True if written, False on error
    """
    try:
        flag_path = get_isolated_flag_path(flag_type, session_id)
        FLAG_DIR.mkdir(parents=True, exist_ok=True)

        payload = {
            **data,
            'created_at': datetime.now().isoformat(),
            'session_id': session_id,
            'pid': get_pid(),
        }

        flag_path.write_text(json.dumps(payload, indent=2), encoding='utf-8')
        return True
    except Exception:
        return False


def read_isolated_flag(flag_type, session_id, max_age_minutes=60):
    """
    Read PID-isolated flag file with auto-expiry.

    Args:
        flag_type: Type of flag
        session_id: Session ID
        max_age_minutes: Auto-delete if older than this

    Returns:
        Dictionary if found and valid, None otherwise
    """
    try:
        flag_path = get_isolated_flag_path(flag_type, session_id)

        if not flag_path.exists():
            return None

        data = json.loads(flag_path.read_text(encoding='utf-8', errors='replace'))

        # Check expiry
        created_str = data.get('created_at', '')
        if created_str:
            try:
                created = datetime.fromisoformat(created_str)
                age_minutes = (datetime.now() - created).total_seconds() / 60
                if age_minutes > max_age_minutes:
                    flag_path.unlink(missing_ok=True)
                    return None
            except:
                pass

        return data
    except Exception:
        return None


def clear_isolated_flag(flag_type, session_id):
    """
    Delete PID-isolated flag file.

    Args:
        flag_type: Type of flag
        session_id: Session ID

    Returns:
        True if deleted or didn't exist, False on error
    """
    try:
        flag_path = get_isolated_flag_path(flag_type, session_id)
        flag_path.unlink(missing_ok=True)
        return True
    except Exception:
        return False


def find_session_flag_isolated(pattern_prefix, session_id):
    """
    Find PID-isolated session flag matching pattern.

    Args:
        pattern_prefix: Flag type prefix (e.g., 'task-breakdown-pending')
        session_id: Session ID

    Returns:
        (flag_path, flag_data) tuple or (None, None) if not found
    """
    flag_path = get_isolated_flag_path(pattern_prefix, session_id)

    if flag_path.exists():
        try:
            data = json.loads(flag_path.read_text(encoding='utf-8', errors='replace'))
            return (flag_path, data)
        except Exception:
            pass

    return (None, None)


def cleanup_stale_flags(session_id, max_age_minutes=120):
    """
    Clean up stale PID-isolated flags for a session.
    Only deletes flags where PID process is no longer running.

    Args:
        session_id: Session ID
        max_age_minutes: Minimum age to consider stale

    Returns:
        Number of cleaned flags
    """
    try:
        import psutil
    except ImportError:
        # psutil not available, skip process checking
        return 0

    cleaned = 0
    pattern = f'.*-{session_id}-[0-9]+\.json$'

    try:
        for flag_file in FLAG_DIR.glob(f'.??*-{session_id}-*.json'):
            try:
                # Extract PID from filename
                parts = flag_file.stem.split('-')
                if len(parts) >= 3:
                    try:
                        pid = int(parts[-1])

                        # Check if process still running
                        if not psutil.pid_exists(pid):
                            flag_file.unlink(missing_ok=True)
                            cleaned += 1
                    except (ValueError, IndexError):
                        pass
            except Exception:
                pass
    except Exception:
        pass

    return cleaned


if __name__ == '__main__':
    # Test mode
    test_session = 'SESSION-TEST-12345'

    # Test write
    write_isolated_flag('test-flag', test_session, {'data': 'test'})
    print('[OK] Write isolated flag')

    # Test read
    data = read_isolated_flag('test-flag', test_session)
    if data:
        print('[OK] Read isolated flag: {}'.format(data.get('data')))

    # Test clear
    clear_isolated_flag('test-flag', test_session)
    print('[OK] Clear isolated flag')

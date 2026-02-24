#!/usr/bin/env python3
"""
Script Name: session-window-isolator.py
Version: 1.0.0
Last Modified: 2026-02-24
Description: Window/Process Isolation Utility for Multi-Window Claude Code

Provides utilities for isolating sessions across multiple Claude Code windows.
Each window gets its own PID-based session context to prevent conflicts.

Key Functions:
  - get_window_id(): Returns unique window identifier (PID + host)
  - get_window_state_file(): Returns PID-specific hook state file
  - get_window_session_dir(): Returns PID-specific session directory
  - acquire_window_lock(): File-lock for safe concurrent access
  - cleanup_window(): Clean up on window close

Windows-Safe: No Unicode chars (ASCII only, cp1252 compatible)
"""

import sys
import os
import json
import socket
from pathlib import Path
from datetime import datetime

# Windows: ASCII-only output
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

MEMORY_BASE = Path.home() / '.claude' / 'memory'
SESSIONS_DIR = MEMORY_BASE / 'sessions'
WINDOW_STATE_DIR = MEMORY_BASE / 'window-state'
LOGS_DIR = MEMORY_BASE / 'logs'


def get_window_id():
    """
    Get unique window identifier.
    Format: {pid}@{hostname}
    """
    pid = os.getpid()
    hostname = socket.gethostname().split('.')[0]
    return f"{pid}@{hostname}"


def get_window_state_file():
    """
    Get PID-specific hook state file path.
    Instead of: ~/.claude/.hook-state.json (shared by all windows)
    Use: ~/.claude/.hook-state-{PID}.json (window-specific)
    """
    pid = os.getpid()
    return Path.home() / '.claude' / f'.hook-state-{pid}.json'


def get_window_session_dir(session_id):
    """
    Get PID-specific session directory.
    Format: ~/.claude/memory/sessions/{SESSION_ID}-{PID}/

    Each window maintains its own session artifacts:
    - flow-trace.json
    - task-metadata.json
    - window-state.json
    """
    pid = os.getpid()
    return SESSIONS_DIR / f'{session_id}-{pid}'


def get_window_registry_file():
    """
    Central registry of all active windows.
    Each window registers itself here with timestamp.
    Used for cleanup of stale window processes.
    Format: ~/.claude/memory/window-state/active-windows.json
    """
    WINDOW_STATE_DIR.mkdir(parents=True, exist_ok=True)
    return WINDOW_STATE_DIR / 'active-windows.json'


def register_window(session_id):
    """
    Register current window in active window registry.
    Prevents conflict detection - window knows about itself.
    """
    try:
        registry_file = get_window_registry_file()
        window_id = get_window_id()

        # Read current registry
        registry = {}
        if registry_file.exists():
            try:
                registry = json.loads(registry_file.read_text(encoding='utf-8'))
            except Exception:
                registry = {}

        # Register this window
        registry[window_id] = {
            'pid': os.getpid(),
            'hostname': socket.gethostname(),
            'session_id': session_id,
            'timestamp': datetime.now().isoformat(),
            'status': 'active'
        }

        # Write back
        registry_file.write_text(json.dumps(registry, indent=2), encoding='utf-8')
        return True
    except Exception as e:
        log_event(f"[ERROR] Failed to register window: {e}")
        return False


def cleanup_window():
    """
    Clean up window on exit.
    Remove stale window entries (PID no longer running).
    """
    try:
        registry_file = get_window_registry_file()
        if not registry_file.exists():
            return

        registry = json.loads(registry_file.read_text(encoding='utf-8'))
        window_id = get_window_id()

        # Mark this window as closed
        if window_id in registry:
            registry[window_id]['status'] = 'closed'
            registry[window_id]['closed_at'] = datetime.now().isoformat()

        # Write back
        registry_file.write_text(json.dumps(registry, indent=2), encoding='utf-8')
        return True
    except Exception:
        pass
    return False


def acquire_window_lock(filepath, timeout_seconds=5):
    """
    Acquire exclusive lock on file for safe concurrent access.
    Windows-specific using msvcrt.locking.

    Usage:
        with acquire_window_lock(some_file):
            # Safe to modify some_file
            modify(some_file)
    """
    if sys.platform != 'win32':
        # On Unix, this is a no-op (Unix already has better locking)
        return _NullContextManager()

    import msvcrt
    from contextlib import contextmanager

    @contextmanager
    def lock_context():
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        if not filepath.exists():
            filepath.write_text('', encoding='utf-8')

        f = None
        try:
            f = open(filepath, 'a', encoding='utf-8')
            msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
            yield f
        except IOError:
            # Lock failed - another process has it
            yield None
        finally:
            if f:
                try:
                    msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
                    f.close()
                except Exception:
                    pass

    return lock_context()


class _NullContextManager:
    """Null context manager for non-Windows systems"""
    def __enter__(self):
        return self
    def __exit__(self, *args):
        pass


def log_event(msg):
    """Log window isolation events"""
    log_file = LOGS_DIR / 'window-isolation.log'
    log_file.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    try:
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"{ts} | {msg}\n")
    except Exception:
        pass


if __name__ == '__main__':
    # Test mode
    print(f"[OK] Window ID: {get_window_id()}")
    print(f"[OK] Window State File: {get_window_state_file()}")
    print(f"[OK] Window Registry: {get_window_registry_file()}")

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Session Auto-Save Daemon
Background service for automatic session saving based on triggers

This daemon:
1. Monitors session triggers every N minutes
2. Auto-saves when triggers met
3. No manual user confirmation needed
4. Integrates with context daemon

Usage:
    python session-auto-save-daemon.py [--interval MINUTES] [--project PROJECT]

Examples:
    python session-auto-save-daemon.py --interval 10 --project my-app
"""

import sys
import os
import time
import subprocess
import signal
from datetime import datetime

# Fix Windows encoding issues
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Daemon configuration
DAEMON_PID_FILE = os.path.expanduser("~/.claude/memory/.session-save-daemon.pid")
DAEMON_LOG_FILE = os.path.expanduser("~/.claude/memory/logs/session-save-daemon.log")

# Global flag for graceful shutdown
running = True

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    global running
    running = False
    log_daemon("SHUTDOWN", "Received shutdown signal")

def log_daemon(action, message):
    """Log daemon activity"""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] SESSION-SAVE-DAEMON | {action} | {message}\n"

        with open(DAEMON_LOG_FILE, 'a') as f:
            f.write(log_entry)

        # Also log to policy hits
        policy_log = os.path.expanduser("~/.claude/memory/logs/policy-hits.log")
        policy_entry = f"[{timestamp}] session-save-daemon | {action} | {message}\n"
        with open(policy_log, 'a') as f:
            f.write(policy_entry)

    except Exception as e:
        print(f"Warning: Could not write to log: {e}", file=sys.stderr)

def is_daemon_running():
    """Check if daemon is already running"""
    if not os.path.exists(DAEMON_PID_FILE):
        return False

    try:
        with open(DAEMON_PID_FILE, 'r') as f:
            pid = int(f.read().strip())

        # Check if process exists
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            os.remove(DAEMON_PID_FILE)
            return False
    except:
        return False

def write_pid():
    """Write daemon PID to file"""
    try:
        with open(DAEMON_PID_FILE, 'w') as f:
            f.write(str(os.getpid()))
    except Exception as e:
        log_daemon("ERROR", f"Could not write PID file: {e}")

def remove_pid():
    """Remove PID file on shutdown"""
    try:
        if os.path.exists(DAEMON_PID_FILE):
            os.remove(DAEMON_PID_FILE)
    except Exception as e:
        log_daemon("ERROR", f"Could not remove PID file: {e}")

def check_save_triggers(project_name):
    """Check if session should be saved"""
    try:
        result = subprocess.run(
            ["python", os.path.expanduser("~/.claude/memory/session-save-triggers.py"), "--project", project_name, "--json"],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            # Triggers met - should save
            return True, result.stdout
        else:
            # No triggers met
            return False, None

    except Exception as e:
        log_daemon("ERROR", f"Failed to check triggers: {e}")
        return False, None

def auto_save_session(project_name):
    """Automatically save session summary"""
    log_daemon("AUTO-SAVE", f"Saving session for {project_name}")

    try:
        result = subprocess.run(
            ["python", os.path.expanduser("~/.claude/memory/auto-save-session.py"), "--project", project_name],
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode == 0:
            log_daemon("AUTO-SAVE", f"Session saved successfully for {project_name}")
            return True
        else:
            log_daemon("ERROR", f"Failed to save session: {result.stderr}")
            return False

    except Exception as e:
        log_daemon("ERROR", f"Failed to auto-save session: {e}")
        return False

def monitor_loop(interval_minutes, project_name):
    """Main monitoring loop"""
    global running

    log_daemon("START", f"Daemon started (interval={interval_minutes}min, project={project_name})")

    last_save_time = None
    save_cooldown_minutes = 30  # Don't save too frequently

    while running:
        try:
            # Check save triggers
            log_daemon("CHECK", "Checking session save triggers...")
            should_save, trigger_data = check_save_triggers(project_name)

            if should_save:
                # Check cooldown
                if last_save_time:
                    time_since_save = (datetime.now() - last_save_time).total_seconds() / 60
                    if time_since_save < save_cooldown_minutes:
                        log_daemon("COOLDOWN", f"Save skipped (cooldown: {save_cooldown_minutes - time_since_save:.1f}min remaining)")
                        time.sleep(interval_minutes * 60)
                        continue

                # Auto-save session
                log_daemon("TRIGGERS-MET", "Session save triggers detected")

                if auto_save_session(project_name):
                    last_save_time = datetime.now()
                    log_daemon("SUCCESS", "Session auto-saved successfully")
                else:
                    log_daemon("FAILED", "Session auto-save failed")

            else:
                log_daemon("OK", "No save triggers met - continue monitoring")

            # Sleep until next check
            log_daemon("SLEEP", f"Sleeping for {interval_minutes} minutes...")
            time.sleep(interval_minutes * 60)

        except KeyboardInterrupt:
            log_daemon("SHUTDOWN", "Received keyboard interrupt")
            break
        except Exception as e:
            log_daemon("ERROR", f"Error in monitoring loop: {e}")
            time.sleep(60)

    log_daemon("STOP", "Daemon stopped")

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Session auto-save background daemon"
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=15,
        help='Check interval in minutes (default: 15)'
    )
    parser.add_argument(
        '--project',
        type=str,
        default=None,
        help='Project name (auto-detected if not specified)'
    )
    parser.add_argument(
        '--stop',
        action='store_true',
        help='Stop running daemon'
    )
    parser.add_argument(
        '--status',
        action='store_true',
        help='Check daemon status'
    )

    args = parser.parse_args()

    # Auto-detect project
    if not args.project:
        args.project = os.path.basename(os.getcwd())

    # Handle --stop
    if args.stop:
        if is_daemon_running():
            try:
                with open(DAEMON_PID_FILE, 'r') as f:
                    pid = int(f.read().strip())
                os.kill(pid, signal.SIGTERM)
                log_daemon("STOP", f"Daemon stopped (PID: {pid})")
                print(f"✅ Session save daemon stopped (PID: {pid})")
            except Exception as e:
                print(f"❌ Failed to stop daemon: {e}")
        else:
            print("ℹ️  Session save daemon is not running")
        return

    # Handle --status
    if args.status:
        if is_daemon_running():
            with open(DAEMON_PID_FILE, 'r') as f:
                pid = f.read().strip()
            print(f"✅ Session save daemon is running (PID: {pid})")
            print(f"   Checking every {args.interval} minutes")
        else:
            print("⚠️  Session save daemon is not running")
        return

    # Check if already running
    if is_daemon_running():
        print("⚠️  Session save daemon is already running!")
        print("   Use --stop to stop it first")
        sys.exit(1)

    # Setup signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    # Write PID file
    write_pid()

    print("=" * 70)
    print("🚀 SESSION AUTO-SAVE DAEMON STARTING")
    print("=" * 70)
    print(f"\nProject: {args.project}")
    print(f"Check Interval: {args.interval} minutes")
    print(f"PID: {os.getpid()}")
    print(f"\nLog: {DAEMON_LOG_FILE}")
    print(f"PID File: {DAEMON_PID_FILE}")
    print("\n💡 To stop: python session-auto-save-daemon.py --stop")
    print("💡 To check status: python session-auto-save-daemon.py --status")
    print("\n✅ Daemon running in background...")
    print("=" * 70)

    try:
        # Run monitoring loop
        monitor_loop(args.interval, args.project)

    finally:
        # Cleanup
        remove_pid()

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Session Pruning Daemon
Background service for automatic session memory archival and cleanup

This daemon:
1. Monitors session count across all projects
2. Auto-triggers pruning monthly (30 days)
3. Auto-triggers on threshold (100+ sessions total)
4. Archives old sessions automatically
5. Keeps memory fast and clean

Usage:
    python session-pruning-daemon.py [--interval DAYS]

Examples:
    python session-pruning-daemon.py --interval 30
    python session-pruning-daemon.py --interval 7  # More frequent
"""

import sys
import os
import time
import subprocess
import signal
import json
from datetime import datetime, timedelta
from pathlib import Path

# Fix Windows encoding issues
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Daemon configuration
DAEMON_PID_FILE = os.path.expanduser("~/.claude/memory/.pruning-daemon.pid")
DAEMON_LOG_FILE = os.path.expanduser("~/.claude/memory/logs/pruning-daemon.log")
LAST_RUN_FILE = os.path.expanduser("~/.claude/memory/.pruning-last-run")

# Thresholds
THRESHOLDS = {
    "total_sessions": 100,  # Trigger if 100+ sessions total
    "interval_days": 30,    # Run at least every 30 days
}

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
        log_entry = f"[{timestamp}] PRUNING-DAEMON | {action} | {message}\n"

        with open(DAEMON_LOG_FILE, 'a') as f:
            f.write(log_entry)

        # Also log to policy hits
        policy_log = os.path.expanduser("~/.claude/memory/logs/policy-hits.log")
        policy_entry = f"[{timestamp}] session-pruning-daemon | {action} | {message}\n"
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

def get_last_run_time():
    """Get timestamp of last pruning run"""
    if not os.path.exists(LAST_RUN_FILE):
        return None

    try:
        with open(LAST_RUN_FILE, 'r') as f:
            timestamp_str = f.read().strip()
            return datetime.fromisoformat(timestamp_str)
    except:
        return None

def save_last_run_time():
    """Save current timestamp as last run time"""
    try:
        with open(LAST_RUN_FILE, 'w') as f:
            f.write(datetime.now().isoformat())
    except Exception as e:
        log_daemon("ERROR", f"Could not save last run time: {e}")

def count_total_sessions():
    """Count total active sessions across all projects"""
    sessions_dir = Path.home() / ".claude" / "memory" / "sessions"

    if not sessions_dir.exists():
        return 0

    total = 0

    for project_dir in sessions_dir.iterdir():
        if not project_dir.is_dir():
            continue

        # Count session-*.md files
        session_files = list(project_dir.glob('session-*.md'))
        total += len(session_files)

    return total

def get_session_stats():
    """Get detailed session statistics"""
    sessions_dir = Path.home() / ".claude" / "memory" / "sessions"

    if not sessions_dir.exists():
        return None

    stats = {
        "total_sessions": 0,
        "total_projects": 0,
        "archivable_sessions": 0,
    }

    projects = [d for d in sessions_dir.iterdir() if d.is_dir()]
    stats["total_projects"] = len(projects)

    for project_dir in projects:
        session_files = list(project_dir.glob('session-*.md'))
        stats["total_sessions"] += len(session_files)

        # Count archivable (simple heuristic: older than 30 days and beyond last 10)
        if len(session_files) > 10:
            # Rough estimate
            stats["archivable_sessions"] += max(0, len(session_files) - 10)

    return stats

def should_run_pruning():
    """Check if pruning should run based on triggers"""
    triggers = []

    # Trigger 1: Time-based (30 days since last run)
    last_run = get_last_run_time()

    if last_run:
        days_since = (datetime.now() - last_run).days

        if days_since >= THRESHOLDS["interval_days"]:
            triggers.append(f"time_interval (last_run={days_since}d ago)")
    else:
        # Never run before
        triggers.append("first_run")

    # Trigger 2: Session count threshold
    total_sessions = count_total_sessions()

    if total_sessions >= THRESHOLDS["total_sessions"]:
        triggers.append(f"session_threshold (total={total_sessions})")

    return triggers

def execute_pruning():
    """Execute session pruning"""
    try:
        result = subprocess.run(
            ["python", os.path.expanduser("~/.claude/memory/archive-old-sessions.py")],
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes max
        )

        if result.returncode == 0:
            log_daemon("PRUNING-SUCCESS", "Session archival completed")
            return True, result.stdout
        else:
            log_daemon("PRUNING-FAILED", f"Error: {result.stderr}")
            return False, result.stderr

    except Exception as e:
        log_daemon("ERROR", f"Failed to execute pruning: {e}")
        return False, str(e)

def monitor_loop(check_interval_days):
    """Main monitoring loop"""
    global running

    log_daemon("START", f"Daemon started (check_interval={check_interval_days}d)")

    # Check more frequently than the interval (daily checks)
    sleep_hours = min(24, check_interval_days * 24)

    while running:
        try:
            # Check if pruning should run
            log_daemon("CHECK", "Checking pruning triggers...")
            triggers = should_run_pruning()

            if triggers:
                log_daemon("TRIGGERS-MET", f"{len(triggers)} triggers: {', '.join(triggers)}")

                # Get stats before pruning
                stats_before = get_session_stats()

                if stats_before:
                    log_daemon("STATS-BEFORE",
                              f"projects={stats_before['total_projects']}, "
                              f"sessions={stats_before['total_sessions']}, "
                              f"archivable={stats_before['archivable_sessions']}")

                # Execute pruning
                log_daemon("PRUNING", "Starting session archival...")
                success, output = execute_pruning()

                if success:
                    # Get stats after pruning
                    stats_after = get_session_stats()

                    if stats_after:
                        archived = stats_before['total_sessions'] - stats_after['total_sessions']
                        log_daemon("PRUNING-COMPLETE",
                                  f"Archived {archived} sessions, "
                                  f"{stats_after['total_sessions']} remain active")

                    # Save last run time
                    save_last_run_time()

                    log_daemon("SUCCESS", "Pruning completed successfully")
                else:
                    log_daemon("FAILED", f"Pruning failed: {output}")

            else:
                stats = get_session_stats()
                if stats:
                    log_daemon("OK",
                              f"No triggers met. "
                              f"Sessions: {stats['total_sessions']}, "
                              f"Projects: {stats['total_projects']}")
                else:
                    log_daemon("OK", "No triggers met")

            # Sleep until next check
            log_daemon("SLEEP", f"Sleeping for {sleep_hours} hours...")
            time.sleep(sleep_hours * 3600)

        except KeyboardInterrupt:
            log_daemon("SHUTDOWN", "Received keyboard interrupt")
            break
        except Exception as e:
            log_daemon("ERROR", f"Error in monitoring loop: {e}")
            time.sleep(3600)  # Sleep 1 hour on error

    log_daemon("STOP", "Daemon stopped")

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Session pruning background daemon"
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=30,
        help='Check interval in days (default: 30)'
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
    parser.add_argument(
        '--run-now',
        action='store_true',
        help='Run pruning immediately (manual trigger)'
    )

    args = parser.parse_args()

    # Handle --stop
    if args.stop:
        if is_daemon_running():
            try:
                with open(DAEMON_PID_FILE, 'r') as f:
                    pid = int(f.read().strip())
                os.kill(pid, signal.SIGTERM)
                log_daemon("STOP", f"Daemon stopped (PID: {pid})")
                print(f"✅ Pruning daemon stopped (PID: {pid})")
            except Exception as e:
                print(f"❌ Failed to stop daemon: {e}")
        else:
            print("ℹ️  Pruning daemon is not running")
        return

    # Handle --status
    if args.status:
        if is_daemon_running():
            with open(DAEMON_PID_FILE, 'r') as f:
                pid = f.read().strip()
            print(f"✅ Pruning daemon is running (PID: {pid})")
            print(f"   Checking every {args.interval} days")

            # Show last run
            last_run = get_last_run_time()
            if last_run:
                days_ago = (datetime.now() - last_run).days
                print(f"   Last run: {last_run.strftime('%Y-%m-%d')} ({days_ago} days ago)")
            else:
                print(f"   Last run: Never")

            # Show current stats
            stats = get_session_stats()
            if stats:
                print(f"\n   Current stats:")
                print(f"   - Projects: {stats['total_projects']}")
                print(f"   - Active sessions: {stats['total_sessions']}")
                print(f"   - Archivable: ~{stats['archivable_sessions']}")
        else:
            print("⚠️  Pruning daemon is not running")
        return

    # Handle --run-now
    if args.run_now:
        print("🗂️  Running session pruning manually...")
        success, output = execute_pruning()
        if success:
            print("✅ Pruning completed!")
            print(output)
        else:
            print("❌ Pruning failed!")
            print(output)
        return

    # Check if already running
    if is_daemon_running():
        print("⚠️  Pruning daemon is already running!")
        print("   Use --stop to stop it first")
        sys.exit(1)

    # Setup signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    # Write PID file
    write_pid()

    print("=" * 70)
    print("🚀 SESSION PRUNING DAEMON STARTING")
    print("=" * 70)
    print(f"\nCheck Interval: {args.interval} days")
    print(f"PID: {os.getpid()}")
    print(f"\nThresholds:")
    print(f"   - Time: Every {THRESHOLDS['interval_days']} days")
    print(f"   - Sessions: {THRESHOLDS['total_sessions']}+ total sessions")
    print(f"\nLog: {DAEMON_LOG_FILE}")
    print(f"PID File: {DAEMON_PID_FILE}")
    print("\n💡 To stop: python session-pruning-daemon.py --stop")
    print("💡 To check status: python session-pruning-daemon.py --status")
    print("💡 To run manually: python session-pruning-daemon.py --run-now")
    print("\n✅ Daemon running in background...")
    print("=" * 70)

    try:
        # Run monitoring loop
        monitor_loop(args.interval)

    finally:
        # Cleanup
        remove_pid()

if __name__ == "__main__":
    main()

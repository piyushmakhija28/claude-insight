#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Git Auto-Commit Daemon
Background service for automatic git commits when triggers are met

This daemon:
1. Monitors git repository status
2. Checks commit triggers periodically
3. Auto-commits when thresholds met
4. Optional auto-push

Usage:
    python commit-daemon.py [--interval MINUTES] [--project-dir DIR] [--push]

Examples:
    python commit-daemon.py --interval 15
    python commit-daemon.py --interval 10 --push
    python commit-daemon.py --project-dir /path/to/repo
"""

import sys
import os
import time
import subprocess
import signal
import json
from datetime import datetime

# Fix Windows encoding issues
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Daemon configuration
DAEMON_PID_FILE = os.path.expanduser("~/.claude/memory/.commit-daemon.pid")
DAEMON_LOG_FILE = os.path.expanduser("~/.claude/memory/logs/commit-daemon.log")

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
        log_entry = f"[{timestamp}] COMMIT-DAEMON | {action} | {message}\n"

        with open(DAEMON_LOG_FILE, 'a') as f:
            f.write(log_entry)

        # Also log to policy hits
        policy_log = os.path.expanduser("~/.claude/memory/logs/policy-hits.log")
        policy_entry = f"[{timestamp}] commit-daemon | {action} | {message}\n"
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

def check_git_repo(project_dir):
    """Check if directory is a git repo"""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            cwd=project_dir,
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0
    except:
        return False

def check_commit_triggers(project_dir):
    """Check if commit triggers are met"""
    try:
        result = subprocess.run(
            ["python", os.path.expanduser("~/.claude/memory/auto-commit-detector.py"),
             "--project-dir", project_dir, "--json"],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            return None

        detection = json.loads(result.stdout)
        return detection if detection.get("should_commit") else None

    except Exception as e:
        log_daemon("ERROR", f"Failed to check triggers: {e}")
        return None

def execute_auto_commit(project_dir, push=False):
    """Execute auto-commit"""
    try:
        cmd = [
            "python",
            os.path.expanduser("~/.claude/memory/auto-commit.py"),
            "--project-dir", project_dir
        ]

        if push:
            cmd.append("--push")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120
        )

        if result.returncode == 0:
            log_daemon("COMMIT-SUCCESS", f"Auto-committed changes in {project_dir}")
            return True
        else:
            log_daemon("COMMIT-FAILED", f"Failed: {result.stderr}")
            return False

    except Exception as e:
        log_daemon("ERROR", f"Failed to execute auto-commit: {e}")
        return False

def monitor_loop(project_dir, interval_minutes, push=False):
    """Main monitoring loop"""
    global running

    log_daemon("START", f"Daemon started (interval={interval_minutes}min, project={project_dir}, push={push})")

    # Cooldown to prevent repeated commits
    last_commit_time = None
    cooldown_minutes = 15

    while running:
        try:
            # Check if git repo
            if not check_git_repo(project_dir):
                log_daemon("SKIP", "Not a git repository")
                time.sleep(interval_minutes * 60)
                continue

            # Check cooldown
            if last_commit_time:
                elapsed = (datetime.now() - last_commit_time).total_seconds() / 60
                if elapsed < cooldown_minutes:
                    log_daemon("COOLDOWN", f"{elapsed:.1f} min since last commit (cooldown: {cooldown_minutes} min)")
                    time.sleep(interval_minutes * 60)
                    continue

            # Check triggers
            log_daemon("CHECK", f"Checking commit triggers for {project_dir}...")
            detection = check_commit_triggers(project_dir)

            if detection:
                trigger_count = detection.get("trigger_count", 0)
                triggers = detection.get("triggers_met", [])

                log_daemon("TRIGGERS-MET", f"{trigger_count} triggers: {', '.join(triggers)}")

                # Execute auto-commit
                if execute_auto_commit(project_dir, push):
                    last_commit_time = datetime.now()
                    log_daemon("SUCCESS", "Auto-commit executed successfully")
                else:
                    log_daemon("FAILED", "Auto-commit execution failed")
            else:
                log_daemon("OK", "No triggers met")

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
        description="Git auto-commit background daemon"
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=15,
        help='Check interval in minutes (default: 15)'
    )
    parser.add_argument(
        '--project-dir',
        type=str,
        default=None,
        help='Project directory to monitor (default: current directory)'
    )
    parser.add_argument(
        '--push',
        action='store_true',
        help='Auto-push after commit'
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

    # Default to current directory
    if not args.project_dir:
        args.project_dir = os.getcwd()

    # Handle --stop
    if args.stop:
        if is_daemon_running():
            try:
                with open(DAEMON_PID_FILE, 'r') as f:
                    pid = int(f.read().strip())
                os.kill(pid, signal.SIGTERM)
                log_daemon("STOP", f"Daemon stopped (PID: {pid})")
                print(f"✅ Commit daemon stopped (PID: {pid})")
            except Exception as e:
                print(f"❌ Failed to stop daemon: {e}")
        else:
            print("ℹ️  Commit daemon is not running")
        return

    # Handle --status
    if args.status:
        if is_daemon_running():
            with open(DAEMON_PID_FILE, 'r') as f:
                pid = f.read().strip()
            print(f"✅ Commit daemon is running (PID: {pid})")
            print(f"   Project: {args.project_dir}")
            print(f"   Checking every {args.interval} minutes")
        else:
            print("⚠️  Commit daemon is not running")
        return

    # Check if already running
    if is_daemon_running():
        print("⚠️  Commit daemon is already running!")
        print("   Use --stop to stop it first")
        sys.exit(1)

    # Setup signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    # Write PID file
    write_pid()

    print("=" * 70)
    print("🚀 GIT AUTO-COMMIT DAEMON STARTING")
    print("=" * 70)
    print(f"\nProject: {args.project_dir}")
    print(f"Check Interval: {args.interval} minutes")
    print(f"Auto-push: {'Yes' if args.push else 'No'}")
    print(f"PID: {os.getpid()}")
    print(f"\nLog: {DAEMON_LOG_FILE}")
    print(f"PID File: {DAEMON_PID_FILE}")
    print("\n💡 To stop: python commit-daemon.py --stop")
    print("💡 To check status: python commit-daemon.py --status")
    print("\n✅ Daemon running in background...")
    print("=" * 70)

    try:
        # Run monitoring loop
        monitor_loop(args.project_dir, args.interval, args.push)

    finally:
        # Cleanup
        remove_pid()

if __name__ == "__main__":
    main()

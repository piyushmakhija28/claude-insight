#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Context Management Daemon
Background service for continuous context monitoring and auto-cleanup

This daemon:
1. Monitors context usage every N minutes
2. Auto-triggers cleanup at thresholds
3. Protects session memory
4. Auto-saves session summaries

Usage:
    python context-daemon.py [--interval MINUTES] [--project PROJECT]

Examples:
    python context-daemon.py --interval 5 --project my-app
    python context-daemon.py --interval 10  # Auto-detect project
"""

import sys
import os
import time
import json
import subprocess
import signal
import argparse
from datetime import datetime
from pathlib import Path

# Fix Windows encoding issues
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Daemon configuration
DAEMON_PID_FILE = os.path.expanduser("~/.claude/memory/.context-daemon.pid")
DAEMON_LOG_FILE = os.path.expanduser("~/.claude/memory/logs/context-daemon.log")
ESTIMATE_FILE = os.path.expanduser("~/.claude/memory/.context-estimate")

# Thresholds
THRESHOLDS = {
    "light_cleanup": 70,
    "moderate_cleanup": 85,
    "aggressive_cleanup": 90,
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
        log_entry = f"[{timestamp}] DAEMON | {action} | {message}\n"

        with open(DAEMON_LOG_FILE, 'a') as f:
            f.write(log_entry)

        # Also log to policy hits
        policy_log = os.path.expanduser("~/.claude/memory/logs/policy-hits.log")
        policy_entry = f"[{timestamp}] context-daemon | {action} | {message}\n"
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
            os.kill(pid, 0)  # Signal 0 checks if process exists
            return True
        except OSError:
            # Process doesn't exist, remove stale PID file
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

def get_current_estimate():
    """Get current context estimate"""
    try:
        if os.path.exists(ESTIMATE_FILE):
            with open(ESTIMATE_FILE, 'r') as f:
                data = json.load(f)
                # Handle legacy float format (corrupted file)
                if isinstance(data, (int, float)):
                    return {
                        "context_percent": float(data),
                        "timestamp": datetime.now().isoformat(),
                        "metrics": {},
                        "recommendation": {"level": "unknown", "action": "Unknown", "urgency": "low", "color": "gray"}
                    }
                return data
    except:
        pass

    return None

def run_estimator():
    """Run context estimator and get result"""
    try:
        result = subprocess.run(
            ["python", os.path.expanduser("~/.claude/memory/context-estimator.py")],
            capture_output=True,
            text=True,
            timeout=30
        )

        # Read estimate file
        return get_current_estimate()

    except Exception as e:
        log_daemon("ERROR", f"Failed to run estimator: {e}")
        return None

def should_trigger_cleanup(estimate):
    """Determine if cleanup should be triggered"""
    if not estimate:
        return False, None

    context_percent = estimate.get("context_percent", 0)

    if context_percent >= THRESHOLDS["aggressive_cleanup"]:
        return True, "aggressive"
    elif context_percent >= THRESHOLDS["moderate_cleanup"]:
        return True, "moderate"
    elif context_percent >= THRESHOLDS["light_cleanup"]:
        return True, "light"

    return False, None

def auto_save_session(project_name):
    """Auto-save session summary before cleanup"""
    log_daemon("AUTO-SAVE", f"Saving session for {project_name}")

    try:
        # Run auto-save script (we'll create this next)
        subprocess.run(
            ["python", os.path.expanduser("~/.claude/memory/auto-save-session.py"), "--project", project_name],
            timeout=60
        )

        log_daemon("AUTO-SAVE", f"Session saved successfully for {project_name}")
        return True

    except Exception as e:
        log_daemon("ERROR", f"Failed to auto-save session: {e}")
        return False

def trigger_cleanup(level, project_name):
    """Trigger automated cleanup"""
    log_daemon("AUTO-TRIGGER", f"Triggering {level} cleanup for {project_name}")

    try:
        # First, auto-save session
        auto_save_session(project_name)

        # Then run cleanup
        result = subprocess.run(
            [
                "python",
                os.path.expanduser("~/.claude/memory/smart-cleanup.py"),
                "--level", level,
                "--project", project_name
            ],
            capture_output=True,
            text=True,
            timeout=60
        )

        log_daemon("AUTO-TRIGGER", f"Cleanup triggered: level={level}, exit_code={result.returncode}")

        # Verify session protection
        subprocess.run(
            ["python", os.path.expanduser("~/.claude/memory/protect-session-memory.py"), "--verify"],
            timeout=30
        )

        return True

    except Exception as e:
        log_daemon("ERROR", f"Failed to trigger cleanup: {e}")
        return False

def monitor_loop(interval_minutes, project_name):
    """Main monitoring loop"""
    global running

    log_daemon("START", f"Daemon started (interval={interval_minutes}min, project={project_name})")

    last_cleanup_time = None
    cleanup_cooldown_minutes = 30  # Don't cleanup too frequently

    while running:
        try:
            # Run estimator
            log_daemon("CHECK", "Running context estimator...")
            estimate = run_estimator()

            if estimate:
                context_percent = estimate.get("context_percent", 0)
                recommendation = estimate.get("recommendation", {})

                log_daemon("ESTIMATE", f"{context_percent}% (level={recommendation.get('level', 'unknown')})")

                # Check if cleanup needed
                should_cleanup, cleanup_level = should_trigger_cleanup(estimate)

                if should_cleanup:
                    # Check cooldown
                    if last_cleanup_time:
                        time_since_cleanup = (datetime.now() - last_cleanup_time).total_seconds() / 60
                        if time_since_cleanup < cleanup_cooldown_minutes:
                            log_daemon("COOLDOWN", f"Cleanup skipped (cooldown: {cleanup_cooldown_minutes - time_since_cleanup:.1f}min remaining)")
                            time.sleep(interval_minutes * 60)
                            continue

                    # Trigger cleanup
                    log_daemon("THRESHOLD", f"Threshold exceeded: {context_percent}% >= {THRESHOLDS.get(cleanup_level + '_cleanup', 0)}%")

                    if trigger_cleanup(cleanup_level, project_name):
                        last_cleanup_time = datetime.now()
                        log_daemon("SUCCESS", f"Cleanup completed: {cleanup_level}")
                    else:
                        log_daemon("FAILED", f"Cleanup failed: {cleanup_level}")

                else:
                    log_daemon("OK", f"Context healthy: {context_percent}%")

            # Sleep until next check
            log_daemon("SLEEP", f"Sleeping for {interval_minutes} minutes...")
            time.sleep(interval_minutes * 60)

        except KeyboardInterrupt:
            log_daemon("SHUTDOWN", "Received keyboard interrupt")
            break
        except Exception as e:
            log_daemon("ERROR", f"Error in monitoring loop: {e}")
            time.sleep(60)  # Sleep 1 min on error

    log_daemon("STOP", "Daemon stopped")

def main():
    parser = argparse.ArgumentParser(
        description="Context management background daemon"
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=10,
        help='Check interval in minutes (default: 10)'
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
                print(f"✅ Daemon stopped (PID: {pid})")
            except Exception as e:
                print(f"❌ Failed to stop daemon: {e}")
        else:
            print("ℹ️  Daemon is not running")
        return

    # Handle --status
    if args.status:
        if is_daemon_running():
            with open(DAEMON_PID_FILE, 'r') as f:
                pid = f.read().strip()
            print(f"✅ Daemon is running (PID: {pid})")

            # Show last estimate
            estimate = get_current_estimate()
            if estimate:
                print(f"\n📊 Last Context Estimate:")
                print(f"   Context: {estimate['context_percent']}%")
                print(f"   Level: {estimate['recommendation']['level']}")
                print(f"   Time: {estimate['timestamp']}")
        else:
            print("⚠️  Daemon is not running")
        return

    # Check if already running
    if is_daemon_running():
        print("⚠️  Daemon is already running!")
        print("   Use --stop to stop it first")
        sys.exit(1)

    # Setup signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    # Write PID file
    write_pid()

    print("=" * 70)
    print("🚀 CONTEXT MANAGEMENT DAEMON STARTING")
    print("=" * 70)
    print(f"\nProject: {args.project}")
    print(f"Check Interval: {args.interval} minutes")
    print(f"PID: {os.getpid()}")
    print(f"\nLog: {DAEMON_LOG_FILE}")
    print(f"PID File: {DAEMON_PID_FILE}")
    print("\n💡 To stop: python context-daemon.py --stop")
    print("💡 To check status: python context-daemon.py --status")
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

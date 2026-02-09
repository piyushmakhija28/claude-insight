#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Failure Prevention Daemon
Background service for automatic failure detection, learning, and prevention

This daemon:
1. Monitors failure logs continuously
2. Auto-detects failure patterns
3. Auto-learns from failures
4. Updates knowledge base automatically
5. Prevents future failures proactively

Usage:
    python failure-prevention-daemon.py [--interval HOURS]

Examples:
    python failure-prevention-daemon.py --interval 6   # Check every 6 hours
    python failure-prevention-daemon.py --interval 24  # Check daily
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
DAEMON_PID_FILE = os.path.expanduser("~/.claude/memory/.failure-daemon.pid")
DAEMON_LOG_FILE = os.path.expanduser("~/.claude/memory/logs/failure-daemon.log")
LAST_RUN_FILE = os.path.expanduser("~/.claude/memory/.failure-last-run")

# Thresholds
THRESHOLDS = {
    "check_interval_hours": 6,       # Check every 6 hours
    "min_failures_for_learning": 2,  # Minimum failures to trigger learning
    "promotion_check_interval": 24,  # Check for promotion every 24 hours
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
        log_entry = f"[{timestamp}] FAILURE-DAEMON | {action} | {message}\n"

        with open(DAEMON_LOG_FILE, 'a') as f:
            f.write(log_entry)

        # Also log to policy hits
        policy_log = os.path.expanduser("~/.claude/memory/logs/policy-hits.log")
        policy_entry = f"[{timestamp}] failure-prevention-daemon | {action} | {message}\n"
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

def get_last_run_data():
    """Get data from last run"""
    if not os.path.exists(LAST_RUN_FILE):
        return None

    try:
        with open(LAST_RUN_FILE, 'r') as f:
            return json.load(f)
    except:
        return None

def save_last_run_data(detection_count, learned_count, promoted_count=0):
    """Save current run data"""
    try:
        data = {
            "timestamp": datetime.now().isoformat(),
            "detection_count": detection_count,
            "learned_count": learned_count,
            "promoted_count": promoted_count
        }
        with open(LAST_RUN_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        log_daemon("ERROR", f"Could not save last run data: {e}")

def get_current_project():
    """Get current project name"""
    try:
        cwd = Path.cwd()
        return cwd.name
    except:
        return None

def run_failure_detection():
    """Run failure detection"""
    try:
        result = subprocess.run(
            ["python", os.path.expanduser("~/.claude/memory/failure-detector.py"),
             "--analyze-logs"],
            capture_output=True,
            text=True,
            timeout=120
        )

        if result.returncode == 0:
            log_daemon("DETECTION-SUCCESS", "Failure detection completed")
            return True, result.stdout
        else:
            log_daemon("DETECTION-FAILED", f"Error: {result.stderr}")
            return False, result.stderr

    except Exception as e:
        log_daemon("ERROR", f"Failed to run detection: {e}")
        return False, str(e)

def run_failure_learning(project_name):
    """Run failure learning"""
    try:
        result = subprocess.run(
            ["python", os.path.expanduser("~/.claude/memory/failure-learner.py"),
             "--project", project_name],
            capture_output=True,
            text=True,
            timeout=120
        )

        if result.returncode == 0:
            log_daemon("LEARNING-SUCCESS", f"Learning completed for {project_name}")
            return True, result.stdout
        else:
            log_daemon("LEARNING-FAILED", f"Error: {result.stderr}")
            return False, result.stderr

    except Exception as e:
        log_daemon("ERROR", f"Failed to run learning: {e}")
        return False, str(e)

def run_promotion_check(project_name):
    """Check and promote patterns to global"""
    try:
        result = subprocess.run(
            ["python", os.path.expanduser("~/.claude/memory/failure-learner.py"),
             "--project", project_name, "--promote"],
            capture_output=True,
            text=True,
            timeout=120
        )

        if result.returncode == 0:
            log_daemon("PROMOTION-SUCCESS", f"Promotion check completed for {project_name}")
            return True, result.stdout
        else:
            log_daemon("PROMOTION-FAILED", f"Error: {result.stderr}")
            return False, result.stderr

    except Exception as e:
        log_daemon("ERROR", f"Failed to run promotion: {e}")
        return False, str(e)

def get_failure_count():
    """Get count of recent failures"""
    detection_file = Path.home() / ".claude" / "memory" / "logs" / "failure-detection.json"

    if not detection_file.exists():
        return 0

    try:
        with open(detection_file, 'r') as f:
            data = json.load(f)
            return data.get("summary", {}).get("total_failures", 0)
    except:
        return 0

def should_check_promotion():
    """Check if it's time for promotion check"""
    last_run = get_last_run_data()

    if not last_run:
        return False  # Don't promote on first run

    last_time = datetime.fromisoformat(last_run["timestamp"])
    hours_since = (datetime.now() - last_time).total_seconds() / 3600

    return hours_since >= THRESHOLDS["promotion_check_interval"]

def monitor_loop(check_interval_hours):
    """Main monitoring loop"""
    global running

    log_daemon("START", f"Daemon started (check_interval={check_interval_hours}h)")

    project_name = get_current_project()
    if not project_name:
        project_name = "default-project"

    log_daemon("PROJECT", f"Monitoring project: {project_name}")

    while running:
        try:
            # Step 1: Run failure detection
            log_daemon("CHECK", "Running failure detection...")
            success, output = run_failure_detection()

            if success:
                failure_count = get_failure_count()
                log_daemon("DETECTION-COMPLETE", f"{failure_count} failures detected")

                # Step 2: Run learning if enough failures
                if failure_count >= THRESHOLDS["min_failures_for_learning"]:
                    log_daemon("LEARNING", f"Starting learning ({failure_count} failures)...")
                    success, output = run_failure_learning(project_name)

                    if success:
                        log_daemon("LEARNING-COMPLETE", "Learning completed successfully")

                        # Step 3: Check for promotion (if time)
                        if should_check_promotion():
                            log_daemon("PROMOTION-CHECK", "Checking for global promotion...")
                            success, output = run_promotion_check(project_name)

                            if success:
                                log_daemon("PROMOTION-COMPLETE", "Promotion check completed")

                        # Save run data
                        save_last_run_data(failure_count, 1, 0)
                    else:
                        log_daemon("LEARNING-FAILED", "Learning failed")
                else:
                    log_daemon("OK", f"Not enough failures for learning ({failure_count} < {THRESHOLDS['min_failures_for_learning']})")

            else:
                log_daemon("DETECTION-FAILED", "Detection failed")

            # Sleep until next check
            log_daemon("SLEEP", f"Sleeping for {check_interval_hours} hours...")
            time.sleep(check_interval_hours * 3600)

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
        description="Failure prevention background daemon"
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=6,
        help='Check interval in hours (default: 6)'
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
        help='Run detection and learning immediately'
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
                print(f"✅ Failure prevention daemon stopped (PID: {pid})")
            except Exception as e:
                print(f"❌ Failed to stop daemon: {e}")
        else:
            print("ℹ️  Failure prevention daemon is not running")
        return

    # Handle --status
    if args.status:
        if is_daemon_running():
            with open(DAEMON_PID_FILE, 'r') as f:
                pid = f.read().strip()
            print(f"✅ Failure prevention daemon is running (PID: {pid})")
            print(f"   Checking every {args.interval} hours")

            # Show last run
            last_run = get_last_run_data()
            if last_run:
                last_time = datetime.fromisoformat(last_run["timestamp"])
                hours_ago = (datetime.now() - last_time).total_seconds() / 3600
                print(f"   Last run: {last_time.strftime('%Y-%m-%d %H:%M')} ({hours_ago:.1f}h ago)")
                print(f"   Failures detected: {last_run.get('detection_count', 0)}")
                print(f"   Patterns learned: {last_run.get('learned_count', 0)}")
            else:
                print(f"   Last run: Never")
        else:
            print("⚠️  Failure prevention daemon is not running")
        return

    # Handle --run-now
    if args.run_now:
        print("🔍 Running failure detection and learning manually...")

        project_name = get_current_project() or "default-project"

        # Run detection
        print("   Step 1: Detecting failures...")
        success, output = run_failure_detection()
        if not success:
            print(f"   ❌ Detection failed: {output}")
            return

        # Run learning
        print("   Step 2: Learning from failures...")
        success, output = run_failure_learning(project_name)
        if not success:
            print(f"   ❌ Learning failed: {output}")
            return

        print("   ✅ Complete!")
        return

    # Check if already running
    if is_daemon_running():
        print("⚠️  Failure prevention daemon is already running!")
        print("   Use --stop to stop it first")
        sys.exit(1)

    # Setup signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    # Write PID file
    write_pid()

    print("=" * 70)
    print("🚀 FAILURE PREVENTION DAEMON STARTING")
    print("=" * 70)
    print(f"\nCheck Interval: {args.interval} hours")
    print(f"PID: {os.getpid()}")
    print(f"\nThresholds:")
    print(f"   - Min failures for learning: {THRESHOLDS['min_failures_for_learning']}")
    print(f"   - Promotion check: Every {THRESHOLDS['promotion_check_interval']} hours")
    print(f"\nLog: {DAEMON_LOG_FILE}")
    print(f"PID File: {DAEMON_PID_FILE}")
    print("\n💡 To stop: python failure-prevention-daemon.py --stop")
    print("💡 To check status: python failure-prevention-daemon.py --status")
    print("💡 To run manually: python failure-prevention-daemon.py --run-now")
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

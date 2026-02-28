#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Preference Auto-Tracker Daemon
Background service for automatic preference tracking and learning

This daemon:
1. Monitors logs for preference patterns
2. Auto-tracks detected preferences
3. Auto-learns after threshold (3x)
4. Auto-applies learned preferences

Usage:
    python preference-auto-tracker.py [--interval MINUTES]

Examples:
    python preference-auto-tracker.py --interval 20
"""

import sys
import os
import time
import signal
import json
from datetime import datetime

# Import functions directly instead of using subprocess
import importlib.util

# Load preference-detector.py
pref_detector_path = os.path.expanduser("~/.claude/memory/01-sync-system/user-preferences/preference-detector.py")
spec = importlib.util.spec_from_file_location("preference_detector", pref_detector_path)
pref_detector_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pref_detector_module)
analyze_logs_for_preferences = pref_detector_module.analyze_logs_for_preferences

# Load track-preference.py
track_pref_path = os.path.expanduser("~/.claude/memory/01-sync-system/user-preferences/track-preference.py")
spec = importlib.util.spec_from_file_location("track_preference", track_pref_path)
track_pref_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(track_pref_module)
track_preference_func = track_pref_module.track_preference

# Fix Windows encoding issues
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Daemon configuration
DAEMON_PID_FILE = os.path.expanduser("~/.claude/memory/.pids/preference-auto-tracker.pid")
DAEMON_LOG_FILE = os.path.expanduser("~/.claude/memory/logs/preference-tracker-daemon.log")

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
        log_entry = f"[{timestamp}] PREF-TRACKER-DAEMON | {action} | {message}\n"

        with open(DAEMON_LOG_FILE, 'a') as f:
            f.write(log_entry)

        # Also log to policy hits
        policy_log = os.path.expanduser("~/.claude/memory/logs/policy-hits.log")
        policy_entry = f"[{timestamp}] preference-auto-tracker | {action} | {message}\n"
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

def detect_preferences():
    """Detect preferences from logs"""
    try:
        # Call analyze_logs_for_preferences directly
        result = analyze_logs_for_preferences()
        return result

    except Exception as e:
        log_daemon("ERROR", f"Failed to detect preferences: {e}")
        return None

def track_preference_daemon(category, value):
    """Track a preference using existing script"""
    try:
        # Call track_preference directly
        success = track_preference_func(category, value)

        if success:
            log_daemon("TRACKED", f"{category}={value}")
            return True
        else:
            log_daemon("TRACK-FAILED", f"{category}={value}")
            return False

    except Exception as e:
        log_daemon("ERROR", f"Failed to track preference: {e}")
        return False

def process_detected_preferences(detection_result):
    """Process detected preferences and track them"""
    if not detection_result:
        return 0

    detected = detection_result.get("detected", {})
    existing = detection_result.get("existing", {})

    tracked_count = 0

    for category, values in detected.items():
        if not values:
            continue

        # Find strongest preference
        max_count = 0
        strongest_value = None

        for value, count in values.items():
            if count > max_count:
                max_count = count
                strongest_value = value

        # Track if count >= 2 and not already learned
        if max_count >= 2:
            # Check if already learned
            already_learned = False

            if category in existing:
                # Handle different formats
                existing_val = existing[category]
                if isinstance(existing_val, dict):
                    already_learned = existing_val.get(category) == strongest_value
                else:
                    already_learned = existing_val == strongest_value

            if not already_learned:
                # Track this preference
                log_daemon("AUTO-TRACK", f"Tracking: {category}={strongest_value} (count={max_count})")
                if track_preference_daemon(category, strongest_value):
                    tracked_count += 1

    return tracked_count

def monitor_loop(interval_minutes):
    """Main monitoring loop"""
    global running

    log_daemon("START", f"Daemon started (interval={interval_minutes}min)")

    while running:
        try:
            # Detect preferences
            log_daemon("CHECK", "Detecting preferences from logs...")
            detection_result = detect_preferences()

            if detection_result:
                detected = detection_result.get("detected", {})

                if detected:
                    log_daemon("DETECTED", f"{len(detected)} categories with preferences")

                    # Process and track
                    tracked = process_detected_preferences(detection_result)

                    if tracked > 0:
                        log_daemon("SUCCESS", f"{tracked} preferences auto-tracked")
                    else:
                        log_daemon("OK", "No new preferences to track")
                else:
                    log_daemon("OK", "No preferences detected in recent logs")
            else:
                log_daemon("OK", "No detection result")

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
        description="Preference auto-tracking background daemon"
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=20,
        help='Check interval in minutes (default: 20)'
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

    if len(sys.argv) < 2:
        sys.exit(0)
    args = parser.parse_args()

    # Handle --stop
    if args.stop:
        if is_daemon_running():
            try:
                with open(DAEMON_PID_FILE, 'r') as f:
                    pid = int(f.read().strip())
                os.kill(pid, signal.SIGTERM)
                log_daemon("STOP", f"Daemon stopped (PID: {pid})")
                print(f"[CHECK] Preference tracker daemon stopped (PID: {pid})")
            except Exception as e:
                print(f"[CROSS] Failed to stop daemon: {e}")
        else:
            print("[INFO]️  Preference tracker daemon is not running")
        return

    # Handle --status
    if args.status:
        if is_daemon_running():
            with open(DAEMON_PID_FILE, 'r') as f:
                pid = f.read().strip()
            print(f"[CHECK] Preference tracker daemon is running (PID: {pid})")
            print(f"   Checking every {args.interval} minutes")
        else:
            print("[WARNING]️  Preference tracker daemon is not running")
        return

    # Check if already running
    if is_daemon_running():
        print("[WARNING]️  Preference tracker daemon is already running!")
        print("   Use --stop to stop it first")
        sys.exit(1)

    # Setup signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    # Write PID file
    write_pid()

    print("=" * 70)
    print("[ROCKET] PREFERENCE AUTO-TRACKER DAEMON STARTING")
    print("=" * 70)
    print(f"\nCheck Interval: {args.interval} minutes")
    print(f"PID: {os.getpid()}")
    print(f"\nLog: {DAEMON_LOG_FILE}")
    print(f"PID File: {DAEMON_PID_FILE}")
    print("\n[BULB] To stop: python preference-auto-tracker.py --stop")
    print("[BULB] To check status: python preference-auto-tracker.py --status")
    print("\n[CHECK] Daemon running in background...")
    print("=" * 70)

    try:
        # Run monitoring loop
        monitor_loop(args.interval)

    finally:
        # Cleanup
        remove_pid()

if __name__ == "__main__":
    main()

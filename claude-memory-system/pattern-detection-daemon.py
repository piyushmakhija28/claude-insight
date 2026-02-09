#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cross-Project Pattern Detection Daemon
Background service for automatic pattern detection across projects

This daemon:
1. Monitors project count
2. Auto-triggers detection monthly (30 days)
3. Auto-triggers on threshold (5+ new projects)
4. Detects patterns automatically
5. Learns from work history

Usage:
    python pattern-detection-daemon.py [--interval DAYS]

Examples:
    python pattern-detection-daemon.py --interval 30
    python pattern-detection-daemon.py --interval 7  # More frequent
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
DAEMON_PID_FILE = os.path.expanduser("~/.claude/memory/.pattern-daemon.pid")
DAEMON_LOG_FILE = os.path.expanduser("~/.claude/memory/logs/pattern-daemon.log")
LAST_RUN_FILE = os.path.expanduser("~/.claude/memory/.pattern-last-run")

# Thresholds
THRESHOLDS = {
    "new_projects": 5,      # Trigger if 5+ new projects since last run
    "interval_days": 30,    # Run at least every 30 days
    "min_projects": 3,      # Minimum projects needed for pattern detection
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
        log_entry = f"[{timestamp}] PATTERN-DAEMON | {action} | {message}\n"

        with open(DAEMON_LOG_FILE, 'a') as f:
            f.write(log_entry)

        # Also log to policy hits
        policy_log = os.path.expanduser("~/.claude/memory/logs/policy-hits.log")
        policy_entry = f"[{timestamp}] pattern-detection-daemon | {action} | {message}\n"
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
    """Get data from last detection run"""
    if not os.path.exists(LAST_RUN_FILE):
        return None

    try:
        with open(LAST_RUN_FILE, 'r') as f:
            return json.load(f)
    except:
        return None

def save_last_run_data(project_count, patterns_count):
    """Save current run data"""
    try:
        data = {
            "timestamp": datetime.now().isoformat(),
            "project_count": project_count,
            "patterns_detected": patterns_count
        }
        with open(LAST_RUN_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        log_daemon("ERROR", f"Could not save last run data: {e}")

def count_projects():
    """Count total projects with sessions"""
    sessions_dir = Path.home() / ".claude" / "memory" / "sessions"

    if not sessions_dir.exists():
        return 0

    projects = [d for d in sessions_dir.iterdir() if d.is_dir()]
    return len(projects)

def get_pattern_stats():
    """Get current pattern statistics"""
    patterns_file = Path.home() / ".claude" / "memory" / "cross-project-patterns.json"

    if not patterns_file.exists():
        return {
            "total_patterns": 0,
            "projects_analyzed": 0,
            "last_analysis": None
        }

    try:
        with open(patterns_file, 'r') as f:
            data = json.load(f)

        metadata = data.get("metadata", {})
        return {
            "total_patterns": len(data.get("patterns", [])),
            "projects_analyzed": metadata.get("projects_analyzed", 0),
            "last_analysis": metadata.get("last_analysis")
        }
    except:
        return {
            "total_patterns": 0,
            "projects_analyzed": 0,
            "last_analysis": None
        }

def should_run_detection():
    """Check if pattern detection should run"""
    triggers = []

    current_projects = count_projects()

    # Need minimum projects for detection
    if current_projects < THRESHOLDS["min_projects"]:
        return []

    # Trigger 1: Time-based (30 days since last run)
    last_run = get_last_run_data()

    if last_run:
        last_time = datetime.fromisoformat(last_run["timestamp"])
        days_since = (datetime.now() - last_time).days

        if days_since >= THRESHOLDS["interval_days"]:
            triggers.append(f"time_interval ({days_since}d since last run)")

        # Trigger 2: New projects threshold
        last_count = last_run.get("project_count", 0)
        new_projects = current_projects - last_count

        if new_projects >= THRESHOLDS["new_projects"]:
            triggers.append(f"new_projects ({new_projects} new projects)")
    else:
        # Never run before
        triggers.append("first_run")

    return triggers

def execute_pattern_detection():
    """Execute pattern detection"""
    try:
        result = subprocess.run(
            ["python", os.path.expanduser("~/.claude/memory/detect-patterns.py")],
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes max
        )

        if result.returncode == 0:
            log_daemon("DETECTION-SUCCESS", "Pattern detection completed")
            return True, result.stdout
        else:
            log_daemon("DETECTION-FAILED", f"Error: {result.stderr}")
            return False, result.stderr

    except Exception as e:
        log_daemon("ERROR", f"Failed to execute detection: {e}")
        return False, str(e)

def monitor_loop(check_interval_days):
    """Main monitoring loop"""
    global running

    log_daemon("START", f"Daemon started (check_interval={check_interval_days}d)")

    # Check more frequently than the interval (weekly checks)
    sleep_hours = min(24 * 7, check_interval_days * 24)  # Max 1 week

    while running:
        try:
            # Check if detection should run
            log_daemon("CHECK", "Checking pattern detection triggers...")
            triggers = should_run_detection()

            if triggers:
                log_daemon("TRIGGERS-MET", f"{len(triggers)} triggers: {', '.join(triggers)}")

                # Get stats before detection
                stats_before = get_pattern_stats()
                project_count = count_projects()

                log_daemon("STATS-BEFORE",
                          f"projects={project_count}, "
                          f"patterns={stats_before['total_patterns']}")

                # Execute detection
                log_daemon("DETECTING", "Starting pattern detection...")
                success, output = execute_pattern_detection()

                if success:
                    # Get stats after detection
                    stats_after = get_pattern_stats()

                    new_patterns = stats_after['total_patterns'] - stats_before['total_patterns']

                    log_daemon("DETECTION-COMPLETE",
                              f"Analyzed {project_count} projects, "
                              f"detected {stats_after['total_patterns']} patterns "
                              f"({new_patterns} new)")

                    # Save last run data
                    save_last_run_data(project_count, stats_after['total_patterns'])

                    log_daemon("SUCCESS", "Pattern detection completed successfully")
                else:
                    log_daemon("FAILED", f"Pattern detection failed: {output}")

            else:
                project_count = count_projects()
                stats = get_pattern_stats()

                if project_count < THRESHOLDS["min_projects"]:
                    log_daemon("SKIP",
                              f"Not enough projects ({project_count} < {THRESHOLDS['min_projects']})")
                else:
                    log_daemon("OK",
                              f"No triggers met. "
                              f"Projects: {project_count}, "
                              f"Patterns: {stats['total_patterns']}")

            # Sleep until next check
            log_daemon("SLEEP", f"Sleeping for {sleep_hours/24:.1f} days...")
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
        description="Pattern detection background daemon"
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
        help='Run detection immediately (manual trigger)'
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
                print(f"✅ Pattern detection daemon stopped (PID: {pid})")
            except Exception as e:
                print(f"❌ Failed to stop daemon: {e}")
        else:
            print("ℹ️  Pattern detection daemon is not running")
        return

    # Handle --status
    if args.status:
        if is_daemon_running():
            with open(DAEMON_PID_FILE, 'r') as f:
                pid = f.read().strip()
            print(f"✅ Pattern detection daemon is running (PID: {pid})")
            print(f"   Checking every {args.interval} days")

            # Show last run
            last_run = get_last_run_data()
            if last_run:
                last_time = datetime.fromisoformat(last_run["timestamp"])
                days_ago = (datetime.now() - last_time).days
                print(f"   Last run: {last_time.strftime('%Y-%m-%d')} ({days_ago} days ago)")
                print(f"   Projects analyzed: {last_run.get('project_count', 0)}")
                print(f"   Patterns detected: {last_run.get('patterns_detected', 0)}")
            else:
                print(f"   Last run: Never")

            # Show current stats
            project_count = count_projects()
            stats = get_pattern_stats()
            print(f"\n   Current stats:")
            print(f"   - Projects: {project_count}")
            print(f"   - Patterns: {stats['total_patterns']}")
        else:
            print("⚠️  Pattern detection daemon is not running")
        return

    # Handle --run-now
    if args.run_now:
        print("🔍 Running pattern detection manually...")
        success, output = execute_pattern_detection()
        if success:
            print("✅ Pattern detection completed!")
            print(output)
        else:
            print("❌ Pattern detection failed!")
            print(output)
        return

    # Check if already running
    if is_daemon_running():
        print("⚠️  Pattern detection daemon is already running!")
        print("   Use --stop to stop it first")
        sys.exit(1)

    # Setup signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    # Write PID file
    write_pid()

    print("=" * 70)
    print("🚀 PATTERN DETECTION DAEMON STARTING")
    print("=" * 70)
    print(f"\nCheck Interval: {args.interval} days")
    print(f"PID: {os.getpid()}")
    print(f"\nThresholds:")
    print(f"   - Time: Every {THRESHOLDS['interval_days']} days")
    print(f"   - New projects: {THRESHOLDS['new_projects']}+ new projects")
    print(f"   - Minimum projects: {THRESHOLDS['min_projects']} projects")
    print(f"\nLog: {DAEMON_LOG_FILE}")
    print(f"PID File: {DAEMON_PID_FILE}")
    print("\n💡 To stop: python pattern-detection-daemon.py --stop")
    print("💡 To check status: python pattern-detection-daemon.py --status")
    print("💡 To run manually: python pattern-detection-daemon.py --run-now")
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

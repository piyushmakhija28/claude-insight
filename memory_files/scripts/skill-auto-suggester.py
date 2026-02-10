#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skill Auto-Suggester Daemon
Background service for automatic skill suggestion based on user messages

This daemon:
1. Monitors conversation logs for user messages
2. Auto-analyzes messages for skill relevance
3. Proactively suggests skills (no manual calls)
4. Auto-updates usage statistics

Usage:
    python skill-auto-suggester.py [--interval MINUTES]

Examples:
    python skill-auto-suggester.py --interval 5
"""

import sys
import os
import time
import subprocess
import signal
import json
from datetime import datetime, timedelta

# Fix Windows encoding issues
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Daemon configuration
DAEMON_PID_FILE = os.path.expanduser("~/.claude/memory/.skill-suggester-daemon.pid")
DAEMON_LOG_FILE = os.path.expanduser("~/.claude/memory/logs/skill-suggester-daemon.log")

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
        log_entry = f"[{timestamp}] SKILL-SUGGESTER-DAEMON | {action} | {message}\n"

        with open(DAEMON_LOG_FILE, 'a') as f:
            f.write(log_entry)

        # Also log to policy hits
        policy_log = os.path.expanduser("~/.claude/memory/logs/policy-hits.log")
        policy_entry = f"[{timestamp}] skill-auto-suggester | {action} | {message}\n"
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

def get_recent_messages():
    """
    Extract recent user messages from logs
    """
    log_file = os.path.expanduser("~/.claude/memory/logs/policy-hits.log")

    if not os.path.exists(log_file):
        return []

    messages = []
    cutoff_time = datetime.now() - timedelta(minutes=10)

    try:
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()

            for line in lines[-100:]:
                try:
                    if line.startswith('['):
                        timestamp_str = line[1:20]
                        timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")

                        if timestamp > cutoff_time:
                            # Extract context (user message indicators)
                            if 'user-message' in line or 'context-loaded' in line or 'session-start' in line:
                                parts = line.split('|')
                                if len(parts) >= 3:
                                    context = parts[2].strip()
                                    if context and len(context) > 10:
                                        messages.append(context)
                except:
                    continue

    except Exception as e:
        log_daemon("ERROR", f"Could not read messages: {e}")

    return messages

def detect_skills_for_message(message):
    """
    Detect relevant skills for a message using skill-detector.py
    """
    try:
        result = subprocess.run(
            ["python", os.path.expanduser("~/.claude/memory/skill-detector.py"), message],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            # Parse output for skill suggestions
            output = result.stdout

            # Extract skill names and scores
            skills = []
            for line in output.split('\n'):
                if 'score=' in line.lower() or 'confidence' in line.lower():
                    # Parse skill suggestion
                    skills.append(line.strip())

            return skills if skills else None
        else:
            return None

    except Exception as e:
        log_daemon("ERROR", f"Failed to detect skills: {e}")
        return None

def update_skill_usage(skill_name):
    """
    Update skill usage statistics
    """
    try:
        result = subprocess.run(
            ["python", os.path.expanduser("~/.claude/memory/skill-manager.py"), "update-usage", skill_name],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            log_daemon("USAGE-UPDATED", f"{skill_name}")
            return True
        else:
            return False

    except Exception as e:
        log_daemon("ERROR", f"Failed to update usage: {e}")
        return False

def monitor_loop(interval_minutes):
    """Main monitoring loop"""
    global running

    log_daemon("START", f"Daemon started (interval={interval_minutes}min)")

    processed_messages = set()

    while running:
        try:
            # Get recent messages
            messages = get_recent_messages()

            if messages:
                new_messages = [m for m in messages if m not in processed_messages]

                if new_messages:
                    log_daemon("CHECK", f"Found {len(new_messages)} new messages")

                    for message in new_messages:
                        # Detect skills for this message
                        skills = detect_skills_for_message(message)

                        if skills:
                            log_daemon("SKILLS-DETECTED", f"{len(skills)} skills for: {message[:50]}...")

                            # Log suggestions (proactive)
                            for skill in skills:
                                log_daemon("SUGGEST", f"{skill}")

                            # Update usage stats
                            # (In real implementation, would suggest to user and track if accepted)

                        # Mark as processed
                        processed_messages.add(message)

                else:
                    log_daemon("OK", "No new messages to process")
            else:
                log_daemon("OK", "No recent messages found")

            # Cleanup old processed messages (keep last 100)
            if len(processed_messages) > 100:
                processed_messages = set(list(processed_messages)[-100:])

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
        description="Skill auto-suggester background daemon"
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=5,
        help='Check interval in minutes (default: 5)'
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

    # Handle --stop
    if args.stop:
        if is_daemon_running():
            try:
                with open(DAEMON_PID_FILE, 'r') as f:
                    pid = int(f.read().strip())
                os.kill(pid, signal.SIGTERM)
                log_daemon("STOP", f"Daemon stopped (PID: {pid})")
                print(f"✅ Skill suggester daemon stopped (PID: {pid})")
            except Exception as e:
                print(f"❌ Failed to stop daemon: {e}")
        else:
            print("ℹ️  Skill suggester daemon is not running")
        return

    # Handle --status
    if args.status:
        if is_daemon_running():
            with open(DAEMON_PID_FILE, 'r') as f:
                pid = f.read().strip()
            print(f"✅ Skill suggester daemon is running (PID: {pid})")
            print(f"   Checking every {args.interval} minutes")
        else:
            print("⚠️  Skill suggester daemon is not running")
        return

    # Check if already running
    if is_daemon_running():
        print("⚠️  Skill suggester daemon is already running!")
        print("   Use --stop to stop it first")
        sys.exit(1)

    # Setup signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    # Write PID file
    write_pid()

    print("=" * 70)
    print("🚀 SKILL AUTO-SUGGESTER DAEMON STARTING")
    print("=" * 70)
    print(f"\nCheck Interval: {args.interval} minutes")
    print(f"PID: {os.getpid()}")
    print(f"\nLog: {DAEMON_LOG_FILE}")
    print(f"PID File: {DAEMON_PID_FILE}")
    print("\n💡 To stop: python skill-auto-suggester.py --stop")
    print("💡 To check status: python skill-auto-suggester.py --status")
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

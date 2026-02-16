#!/usr/bin/env python3
"""
Auto-Recommendation Daemon - Real-time automation engine

Watches for user messages and automatically provides recommendations.
Runs in background, always ready with latest analysis.

How it works:
    1. Monitors policy-hits.log for new user-message entries
    2. Automatically runs unified-automation analysis
    3. Saves recommendations to .latest-recommendations.json
    4. Updates in real-time (checks every 5 seconds)
    5. Claude just reads the recommendations file!

Usage:
    python auto-recommendation-daemon.py --start
    python auto-recommendation-daemon.py --status
    python auto-recommendation-daemon.py --stop
"""

import os
import sys
import json
import time
import signal
import subprocess
from datetime import datetime
from pathlib import Path

MEMORY_DIR = Path.home() / ".claude" / "memory"
PID_FILE = MEMORY_DIR / ".pids" / "auto-recommendation-daemon.pid"
LOG_FILE = MEMORY_DIR / "logs" / "auto-recommendation-daemon.log"
POLICY_LOG = MEMORY_DIR / "logs" / "policy-hits.log"
RECOMMENDATIONS_FILE = MEMORY_DIR / ".latest-recommendations.json"
LAST_PROCESSED_FILE = MEMORY_DIR / ".last-processed-message.txt"

class AutoRecommendationDaemon:
    def __init__(self):
        self.running = False
        self.last_message_time = None
        self.check_interval = 5  # Check every 5 seconds

    def log(self, message):
        """Log to daemon log file"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"

        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(log_entry)

        print(log_entry.strip())

    def get_last_user_message(self):
        """Get the most recent user message from policy-hits.log"""
        try:
            if not POLICY_LOG.exists():
                return None

            # Read last 100 lines of policy log
            with open(POLICY_LOG, 'r', encoding='utf-8', errors='replace') as f:
                lines = f.readlines()

            # Find last user-message entry
            for line in reversed(lines[-100:]):
                if 'user-message | content |' in line:
                    # Extract timestamp and message
                    parts = line.strip().split('|')
                    if len(parts) >= 3:
                        timestamp = parts[0].strip('[] ')
                        message = parts[2].strip()
                        return {
                            'timestamp': timestamp,
                            'message': message
                        }

            return None

        except Exception as e:
            self.log(f"ERROR: Failed to read user message: {e}")
            return None

    def get_last_processed_time(self):
        """Get timestamp of last processed message"""
        try:
            if LAST_PROCESSED_FILE.exists():
                with open(LAST_PROCESSED_FILE, 'r') as f:
                    return f.read().strip()
            return None
        except:
            return None

    def save_processed_time(self, timestamp):
        """Save timestamp of processed message"""
        try:
            LAST_PROCESSED_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(LAST_PROCESSED_FILE, 'w') as f:
                f.write(timestamp)
        except Exception as e:
            self.log(f"ERROR: Failed to save processed time: {e}")

    def run_unified_automation(self, message):
        """Run unified-automation.py for the message"""
        try:
            self.log(f"Running unified-automation for: {message[:50]}...")

            script_path = MEMORY_DIR / "unified-automation.py"

            result = subprocess.run(
                ["python", str(script_path), message],
                capture_output=True,
                text=True,
                timeout=30,
                encoding='utf-8',
                errors='replace'
            )

            if result.returncode == 0:
                self.log("Unified-automation completed successfully")

                # Check if recommendations file was created
                if RECOMMENDATIONS_FILE.exists():
                    with open(RECOMMENDATIONS_FILE, 'r') as f:
                        data = json.load(f)

                    self.log(f"Recommendations saved: Model={data.get('model', {}).get('recommended', 'N/A')}")
                    return True
                else:
                    self.log("WARNING: Recommendations file not created")
                    return False
            else:
                self.log(f"ERROR: unified-automation failed with code {result.returncode}")
                self.log(f"STDERR: {result.stderr[:200]}")
                return False

        except Exception as e:
            self.log(f"ERROR: Failed to run unified-automation: {e}")
            return False

    def process_new_message(self, message_data):
        """Process a new user message"""
        message = message_data['message']
        timestamp = message_data['timestamp']

        self.log(f"NEW MESSAGE detected: {message[:50]}...")

        # Run unified automation
        success = self.run_unified_automation(message)

        if success:
            # Mark as processed
            self.save_processed_time(timestamp)
            self.log("Message processed successfully")
        else:
            self.log("Message processing failed")

    def check_for_new_messages(self):
        """Check for new user messages and process them"""
        # Get last user message
        last_message = self.get_last_user_message()

        if not last_message:
            return

        # Get last processed timestamp
        last_processed = self.get_last_processed_time()

        # Check if this is a new message
        if last_processed != last_message['timestamp']:
            self.log(f"New message detected (timestamp: {last_message['timestamp']})")
            self.process_new_message(last_message)

    def run(self):
        """Main daemon loop"""
        self.running = True
        self.log("Auto-Recommendation Daemon started")
        self.log(f"Checking for new messages every {self.check_interval} seconds")

        while self.running:
            try:
                self.check_for_new_messages()
                time.sleep(self.check_interval)

            except KeyboardInterrupt:
                self.log("Received interrupt signal")
                break
            except Exception as e:
                self.log(f"ERROR in main loop: {e}")
                time.sleep(self.check_interval)

        self.log("Auto-Recommendation Daemon stopped")

    def start(self):
        """Start daemon"""
        # Check if already running
        if PID_FILE.exists():
            try:
                with open(PID_FILE, 'r') as f:
                    old_pid = int(f.read().strip())

                # Check if process is actually running
                try:
                    os.kill(old_pid, 0)
                    print(f"Daemon already running (PID: {old_pid})")
                    return
                except OSError:
                    # Process not running, remove stale PID
                    PID_FILE.unlink()
            except:
                pass

        # Save PID
        PID_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(PID_FILE, 'w') as f:
            f.write(str(os.getpid()))

        # Run daemon
        self.run()

    def stop(self):
        """Stop daemon"""
        if not PID_FILE.exists():
            print("Daemon not running")
            return

        try:
            with open(PID_FILE, 'r') as f:
                pid = int(f.read().strip())

            # Send termination signal
            os.kill(pid, signal.SIGTERM)

            # Remove PID file
            PID_FILE.unlink()

            print(f"Daemon stopped (PID: {pid})")

        except Exception as e:
            print(f"ERROR: Failed to stop daemon: {e}")

    def status(self):
        """Check daemon status"""
        if not PID_FILE.exists():
            print("Daemon: STOPPED")
            print("Status: Not running")
            return

        try:
            with open(PID_FILE, 'r') as f:
                pid = int(f.read().strip())

            # Check if process is running
            try:
                os.kill(pid, 0)
                print(f"Daemon: RUNNING")
                print(f"PID: {pid}")
                print(f"Check interval: {self.check_interval} seconds")

                # Show last recommendations if available
                if RECOMMENDATIONS_FILE.exists():
                    with open(RECOMMENDATIONS_FILE, 'r') as f:
                        data = json.load(f)

                    print(f"\nLatest Recommendations:")
                    print(f"  Model: {data.get('model', {}).get('recommended', 'N/A')}")
                    print(f"  Skills: {len(data.get('skills', []))}")
                    print(f"  Agents: {len(data.get('agents', []))}")
                    print(f"  Timestamp: {data.get('timestamp', 'N/A')}")
                else:
                    print("\nNo recommendations available yet")

            except OSError:
                print(f"Daemon: STOPPED")
                print(f"Status: Stale PID file (process {pid} not running)")
                PID_FILE.unlink()

        except Exception as e:
            print(f"ERROR: Failed to check status: {e}")

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Auto-Recommendation Daemon")
    parser.add_argument('action', choices=['start', 'stop', 'status', 'restart'],
                       help="Action to perform")

    args = parser.parse_args()

    daemon = AutoRecommendationDaemon()

    if args.action == 'start':
        daemon.start()
    elif args.action == 'stop':
        daemon.stop()
    elif args.action == 'status':
        daemon.status()
    elif args.action == 'restart':
        daemon.stop()
        time.sleep(2)
        daemon.start()

if __name__ == "__main__":
    main()

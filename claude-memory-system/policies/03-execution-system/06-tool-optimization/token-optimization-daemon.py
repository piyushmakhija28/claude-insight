#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Token Optimization Daemon
Monitors and automates token optimizations

Features:
1. Auto-check context every 5 minutes
2. Auto-prune when context >85%
3. Generate token usage reports
4. Clean old cache entries

Usage:
    python token-optimization-daemon.py [--interval MINUTES]
"""

import sys
import os
import time
import json
import subprocess
import signal
from datetime import datetime, timedelta
from pathlib import Path

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

MEMORY_DIR = os.path.expanduser("~/.claude/memory")
PID_FILE = os.path.join(MEMORY_DIR, ".token-optimization-daemon.pid")
LOG_FILE = os.path.join(MEMORY_DIR, "logs/token-optimization-daemon.log")

running = True

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    global running
    running = False
    log_daemon("SHUTDOWN", "Received shutdown signal")

def log_daemon(action, message):
    """Log daemon activity"""
    try:
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {action} | {message}\n"

        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(log_entry)

        # Also log to policy hits
        policy_log = os.path.join(MEMORY_DIR, "logs/policy-hits.log")
        policy_entry = f"[{timestamp}] token-optimization-daemon | {action} | {message}\n"
        with open(policy_log, 'a', encoding='utf-8') as f:
            f.write(policy_entry)

    except Exception as e:
        print(f"Warning: Could not log: {e}", file=sys.stderr)

def write_pid():
    """Write daemon PID"""
    try:
        with open(PID_FILE, 'w') as f:
            f.write(str(os.getpid()))
    except Exception as e:
        log_daemon("ERROR", f"Could not write PID: {e}")

def remove_pid():
    """Remove PID file"""
    try:
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
    except:
        pass

def check_context():
    """Check context and prune if needed"""
    try:
        result = subprocess.run(
            ["python", os.path.join(MEMORY_DIR, "auto-context-pruner.py"), "--check"],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            data = json.loads(result.stdout)
            percentage = data.get('percentage', 0)
            prune_needed = data.get('prune_needed', False)

            log_daemon("CONTEXT-CHECK", f"{percentage}% - Prune needed: {prune_needed}")

            if prune_needed:
                action = data.get('action', '')
                log_daemon("PRUNE-ALERT", f"Action: {action}")

            return data

    except Exception as e:
        log_daemon("ERROR", f"Context check failed: {e}")

    return None

def generate_report():
    """Generate token usage report"""
    try:
        token_log = os.path.join(MEMORY_DIR, "logs/token-optimization.log")

        if not os.path.exists(token_log):
            return {
                'total_optimizations': 0,
                'total_tokens_saved': 0
            }

        with open(token_log, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()

        # Count optimizations in last 24 hours
        cutoff = datetime.now() - timedelta(hours=24)
        recent_optimizations = 0
        total_saved = 0

        for line in lines:
            try:
                if '| Saved:' in line:
                    # Parse: [timestamp] Tool | Type | Saved: N tokens
                    parts = line.split('| Saved:')
                    if len(parts) > 1:
                        tokens_str = parts[1].split('tokens')[0].strip()
                        tokens = int(tokens_str)
                        total_saved += tokens
                        recent_optimizations += 1
            except:
                continue

        return {
            'total_optimizations': recent_optimizations,
            'total_tokens_saved': total_saved,
            'average_per_optimization': total_saved // recent_optimizations if recent_optimizations > 0 else 0
        }

    except Exception as e:
        log_daemon("ERROR", f"Report generation failed: {e}")
        return None

def cleanup_old_cache():
    """Clean cache entries older than 7 days"""
    try:
        cache_dir = os.path.join(MEMORY_DIR, ".cache")
        if not os.path.exists(cache_dir):
            return

        cutoff = datetime.now().timestamp() - (7 * 24 * 3600)
        cleaned = 0

        for cache_file in Path(cache_dir).glob("*.cache"):
            if cache_file.stat().st_mtime < cutoff:
                cache_file.unlink()
                cleaned += 1

        if cleaned > 0:
            log_daemon("CLEANUP", f"Removed {cleaned} old cache entries")

    except Exception as e:
        log_daemon("ERROR", f"Cache cleanup failed: {e}")

def monitor_loop(interval_minutes=5):
    """Main monitoring loop"""
    global running

    log_daemon("START", f"Daemon started (interval={interval_minutes}min)")

    write_pid()

    # Register signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    iteration = 0

    while running:
        try:
            iteration += 1

            # Every iteration: Check context
            check_context()

            # Every 6 iterations (30 min): Generate report
            if iteration % 6 == 0:
                report = generate_report()
                if report:
                    log_daemon("REPORT",
                              f"Optimizations: {report['total_optimizations']}, "
                              f"Tokens saved: {report['total_tokens_saved']}")

            # Every 12 iterations (1 hour): Cleanup cache
            if iteration % 12 == 0:
                cleanup_old_cache()

            # Sleep
            time.sleep(interval_minutes * 60)

        except Exception as e:
            log_daemon("ERROR", f"Monitoring loop error: {e}")
            time.sleep(interval_minutes * 60)

    # Cleanup on exit
    remove_pid()
    log_daemon("STOPPED", "Daemon stopped cleanly")

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Token Optimization Daemon')
    parser.add_argument('--interval', type=int, default=5, help='Check interval in minutes')

    args = parser.parse_args()

    monitor_loop(args.interval)

if __name__ == "__main__":
    main()

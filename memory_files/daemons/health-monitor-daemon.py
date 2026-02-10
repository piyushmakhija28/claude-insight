#!/usr/bin/env python3
"""
Health Monitor Daemon
Monitors all daemons and auto-restarts dead ones
"""

import sys
import os
import time
import json
import argparse
import importlib.util
from pathlib import Path
from datetime import datetime, timedelta

# Add memory dir to path for imports
memory_dir = Path.home() / '.claude' / 'memory'
sys.path.insert(0, str(memory_dir))

# Import or define components
DaemonLogger = None
PIDTracker = None
DaemonManager = None

# Try importing daemon_logger
try:
    import importlib.util
    spec = importlib.util.spec_from_file_location("daemon_logger", memory_dir / "daemon-logger.py")
    if spec and spec.loader:
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        DaemonLogger = module.DaemonLogger
except Exception as e:
    print(f"Warning: Could not import daemon_logger: {e}", file=sys.stderr)

# Fallback logger if import failed
if DaemonLogger is None:
    class DaemonLogger:
        def __init__(self, name):
            self.name = name
        def info(self, msg, **kwargs):
            print(f"[INFO] {msg}")
        def warning(self, msg, **kwargs):
            print(f"[WARN] {msg}")
        def error(self, msg, **kwargs):
            print(f"[ERROR] {msg}")
        def debug(self, msg, **kwargs):
            pass  # Silent in fallback
        def health_event(self, event, msg, severity):
            print(f"[{severity}] {event}: {msg}")
        def log_startup(self, pid):
            print(f"[INFO] Started with PID {pid}")
        def log_exception(self, e):
            print(f"[ERROR] Exception: {e}")

# Try importing pid_tracker
try:
    spec = importlib.util.spec_from_file_location("pid_tracker", memory_dir / "pid-tracker.py")
    if spec and spec.loader:
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        PIDTracker = module.PIDTracker
except Exception as e:
    print(f"ERROR: Could not import pid_tracker: {e}", file=sys.stderr)
    sys.exit(1)

# Try importing daemon_manager
try:
    spec = importlib.util.spec_from_file_location("daemon_manager", memory_dir / "daemon-manager.py")
    if spec and spec.loader:
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        DaemonManager = module.DaemonManager
except Exception as e:
    print(f"ERROR: Could not import daemon_manager: {e}", file=sys.stderr)
    sys.exit(1)

class HealthMonitor:
    def __init__(self):
        self.memory_dir = Path.home() / '.claude' / 'memory'
        self.restarts_dir = self.memory_dir / '.restarts'
        self.restarts_dir.mkdir(parents=True, exist_ok=True)

        self.logger = DaemonLogger('health-monitor')
        self.pid_tracker = PIDTracker()
        self.daemon_manager = DaemonManager()

        # Configuration
        self.check_interval = 300  # 5 minutes
        self.max_restarts_per_hour = 3
        self.restart_cooldown = 60  # 1 minute between restarts

        # Daemons to monitor (exclude health-monitor itself)
        self.monitored_daemons = [
            name for name in self.daemon_manager.daemons.keys()
            if name != 'health-monitor'
        ]

    def get_restart_log_file(self, daemon_name):
        """Get restart log file for daemon"""
        return self.restarts_dir / f'{daemon_name}.json'

    def load_restart_history(self, daemon_name):
        """Load restart history for daemon"""
        log_file = self.get_restart_log_file(daemon_name)

        if not log_file.exists():
            return []

        try:
            data = json.loads(log_file.read_text())
            return data.get('restarts', [])
        except:
            return []

    def save_restart_event(self, daemon_name, reason):
        """Save restart event"""
        log_file = self.get_restart_log_file(daemon_name)

        history = self.load_restart_history(daemon_name)

        restart_event = {
            'timestamp': datetime.now().isoformat(),
            'reason': reason,
            'success': False  # Will be updated after restart attempt
        }

        history.append(restart_event)

        # Keep only last 100 events
        history = history[-100:]

        data = {
            'daemon': daemon_name,
            'total_restarts': len(history),
            'restarts': history
        }

        log_file.write_text(json.dumps(data, indent=2))

        return len(history) - 1  # Return index of this restart

    def update_restart_success(self, daemon_name, index, success):
        """Update restart success status"""
        log_file = self.get_restart_log_file(daemon_name)

        if not log_file.exists():
            return

        try:
            data = json.loads(log_file.read_text())
            if index < len(data['restarts']):
                data['restarts'][index]['success'] = success
                log_file.write_text(json.dumps(data, indent=2))
        except:
            pass

    def count_recent_restarts(self, daemon_name, hours=1):
        """Count restarts in last N hours"""
        history = self.load_restart_history(daemon_name)
        cutoff = datetime.now() - timedelta(hours=hours)

        recent = [
            r for r in history
            if datetime.fromisoformat(r['timestamp']) > cutoff
        ]

        return len(recent)

    def should_restart(self, daemon_name):
        """Check if daemon should be restarted"""
        # Check restart rate limit
        recent_restarts = self.count_recent_restarts(daemon_name, hours=1)

        if recent_restarts >= self.max_restarts_per_hour:
            self.logger.warning(
                f"Restart rate limit reached for {daemon_name}",
                recent_restarts=recent_restarts,
                max_allowed=self.max_restarts_per_hour
            )
            return False

        # Check cooldown from last restart
        history = self.load_restart_history(daemon_name)
        if history:
            last_restart = datetime.fromisoformat(history[-1]['timestamp'])
            cooldown_end = last_restart + timedelta(seconds=self.restart_cooldown)

            if datetime.now() < cooldown_end:
                self.logger.debug(
                    f"Cooldown period for {daemon_name}",
                    seconds_remaining=(cooldown_end - datetime.now()).seconds
                )
                return False

        return True

    def restart_daemon(self, daemon_name, reason):
        """Attempt to restart a daemon"""
        if not self.should_restart(daemon_name):
            return False

        self.logger.warning(f"Restarting {daemon_name}: {reason}")

        # Save restart event
        restart_index = self.save_restart_event(daemon_name, reason)

        # Attempt restart
        result = self.daemon_manager.start_daemon(daemon_name)

        success = result['status'] in ['started', 'already_running']

        # Update restart status
        self.update_restart_success(daemon_name, restart_index, success)

        if success:
            self.logger.info(f"Successfully restarted {daemon_name}", pid=result.get('pid'))
            self.logger.health_event('RESTART_SUCCESS', f"{daemon_name} restarted", 'INFO')
        else:
            self.logger.error(f"Failed to restart {daemon_name}", error=result.get('message'))
            self.logger.health_event('RESTART_FAILED', f"{daemon_name} restart failed", 'ERROR')

        return success

    def check_daemon_health(self, daemon_name):
        """Check health of a single daemon"""
        verification = self.pid_tracker.verify_daemon(daemon_name)

        if verification['status'] == 'running':
            # Daemon is healthy
            return {
                'daemon': daemon_name,
                'status': 'healthy',
                'action': None
            }

        elif verification['status'] == 'stale_pid':
            # PID file exists but process is dead
            self.logger.warning(f"Stale PID detected for {daemon_name}")

            # Clean up stale PID
            self.pid_tracker.delete_pid(daemon_name)

            # Attempt restart
            restarted = self.restart_daemon(daemon_name, 'stale_pid')

            return {
                'daemon': daemon_name,
                'status': 'dead',
                'action': 'restarted' if restarted else 'restart_failed'
            }

        elif verification['status'] == 'no_pid_file':
            # No PID file - daemon never started or PID was deleted
            self.logger.info(f"No PID file for {daemon_name}, attempting start")

            # Attempt start
            restarted = self.restart_daemon(daemon_name, 'no_pid_file')

            return {
                'daemon': daemon_name,
                'status': 'not_running',
                'action': 'started' if restarted else 'start_failed'
            }

        else:
            # Unknown status
            return {
                'daemon': daemon_name,
                'status': 'unknown',
                'action': None
            }

    def check_all_daemons(self):
        """Check health of all monitored daemons"""
        results = {}

        for daemon_name in self.monitored_daemons:
            results[daemon_name] = self.check_daemon_health(daemon_name)

        return results

    def get_health_summary(self):
        """Get overall health summary"""
        results = self.check_all_daemons()

        summary = {
            'timestamp': datetime.now().isoformat(),
            'total_daemons': len(results),
            'healthy': 0,
            'unhealthy': 0,
            'restarted': 0,
            'failed': 0,
            'daemons': results
        }

        for result in results.values():
            if result['status'] == 'healthy':
                summary['healthy'] += 1
            else:
                summary['unhealthy'] += 1

            if result['action'] in ['restarted', 'started']:
                summary['restarted'] += 1
            elif result['action'] in ['restart_failed', 'start_failed']:
                summary['failed'] += 1

        summary['health_percentage'] = (summary['healthy'] / summary['total_daemons'] * 100) if summary['total_daemons'] > 0 else 0

        return summary

    def run_once(self):
        """Run one health check cycle"""
        self.logger.debug("Running health check cycle")

        summary = self.get_health_summary()

        self.logger.info(
            "Health check complete",
            healthy=summary['healthy'],
            total=summary['total_daemons'],
            restarted=summary['restarted']
        )

        # Log to health.log if any issues
        if summary['unhealthy'] > 0:
            self.logger.health_event(
                'HEALTH_CHECK',
                f"{summary['unhealthy']} daemons unhealthy, {summary['restarted']} restarted",
                'WARNING' if summary['restarted'] > 0 else 'ERROR'
            )

        return summary

    def run_daemon(self):
        """Run as daemon - continuous monitoring"""
        pid = os.getpid()
        self.logger.log_startup(pid)

        # Write our own PID
        self.pid_tracker.write_pid('health-monitor', pid)

        self.logger.info(f"Health monitor started, checking every {self.check_interval}s")

        try:
            iteration = 0
            while True:
                iteration += 1
                self.logger.debug(f"Iteration {iteration}")

                self.run_once()

                time.sleep(self.check_interval)

        except KeyboardInterrupt:
            self.logger.info("Received interrupt signal")
        except Exception as e:
            self.logger.error(f"Unexpected error: {str(e)}")
            self.logger.log_exception(e)
        finally:
            self.logger.info("Health monitor shutting down")
            self.pid_tracker.delete_pid('health-monitor')

def main():
    parser = argparse.ArgumentParser(description='Health monitor daemon')
    parser.add_argument('--start', action='store_true', help='Start daemon')
    parser.add_argument('--check-once', action='store_true', help='Run one health check')
    parser.add_argument('--status', action='store_true', help='Get health status')
    parser.add_argument('--score', action='store_true', help='Get health score only')
    parser.add_argument('--restart-history', help='Get restart history for daemon')

    args = parser.parse_args()

    monitor = HealthMonitor()

    if args.start:
        # Run as daemon
        monitor.run_daemon()
        return 0

    if args.check_once:
        summary = monitor.run_once()
        print(json.dumps(summary, indent=2))
        return 0

    if args.status:
        summary = monitor.get_health_summary()
        print(json.dumps(summary, indent=2))
        return 0

    if args.score:
        summary = monitor.get_health_summary()
        print(f"Health Score: {summary['health_percentage']:.1f}%")
        print(f"Healthy: {summary['healthy']}/{summary['total_daemons']}")
        if summary['restarted'] > 0:
            print(f"Auto-restarted: {summary['restarted']}")
        if summary['failed'] > 0:
            print(f"Failed restarts: {summary['failed']}")
        return 0

    if args.restart_history:
        history = monitor.load_restart_history(args.restart_history)
        print(json.dumps(history, indent=2))
        return 0

    # Default: run as daemon
    monitor.run_daemon()
    return 0

if __name__ == '__main__':
    sys.exit(main())

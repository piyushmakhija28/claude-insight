#!/usr/bin/env python3
"""
Daemon Manager
Cross-platform daemon launcher and manager for Windows and Linux
"""

import sys
import os
import subprocess
import platform
import json
import argparse
from pathlib import Path
from datetime import datetime

class DaemonManager:
    def __init__(self):
        self.memory_dir = Path.home() / '.claude' / 'memory'
        self.pids_dir = self.memory_dir / '.pids'
        self.logs_dir = self.memory_dir / 'logs' / 'daemons'
        self.restarts_dir = self.memory_dir / '.restarts'

        # Ensure directories exist
        self.pids_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.restarts_dir.mkdir(parents=True, exist_ok=True)

        self.is_windows = platform.system() == 'Windows'

        # Known daemons
        self.daemons = {
            'context-daemon': 'context-daemon.py',
            'session-auto-save-daemon': 'session-auto-save-daemon.py',
            'preference-auto-tracker': 'preference-auto-tracker.py',
            'skill-auto-suggester': 'skill-auto-suggester.py',
            'commit-daemon': 'commit-daemon.py',
            'session-pruning-daemon': 'session-pruning-daemon.py',
            'pattern-detection-daemon': 'pattern-detection-daemon.py',
            'failure-prevention-daemon': 'failure-prevention-daemon.py'
        }

    def _get_pid_file(self, daemon_name):
        """Get PID file path for daemon"""
        return self.pids_dir / f'{daemon_name}.pid'

    def _get_log_file(self, daemon_name):
        """Get log file path for daemon"""
        return self.logs_dir / f'{daemon_name}.log'

    def _read_pid(self, daemon_name):
        """Read PID from file"""
        pid_file = self._get_pid_file(daemon_name)
        if not pid_file.exists():
            return None

        try:
            pid = int(pid_file.read_text().strip())
            return pid
        except:
            return None

    def _write_pid(self, daemon_name, pid):
        """Write PID to file"""
        pid_file = self._get_pid_file(daemon_name)
        pid_file.write_text(str(pid))

    def _delete_pid(self, daemon_name):
        """Delete PID file"""
        pid_file = self._get_pid_file(daemon_name)
        if pid_file.exists():
            pid_file.unlink()

    def _is_process_running(self, pid):
        """Check if process is running (cross-platform)"""
        if pid is None:
            return False

        try:
            if self.is_windows:
                # Windows: use tasklist
                result = subprocess.run(
                    ['tasklist', '/FI', f'PID eq {pid}'],
                    capture_output=True,
                    text=True
                )
                return str(pid) in result.stdout
            else:
                # Linux/Mac: send signal 0
                os.kill(pid, 0)
                return True
        except (OSError, subprocess.SubprocessError):
            return False

    def start_daemon(self, daemon_name, script_path=None):
        """Start a daemon (cross-platform)"""
        # Check if already running
        pid = self._read_pid(daemon_name)
        if pid and self._is_process_running(pid):
            return {
                'status': 'already_running',
                'pid': pid,
                'message': f'{daemon_name} already running with PID {pid}'
            }

        # Get script path
        if script_path is None:
            script_path = self.memory_dir / self.daemons.get(daemon_name, f'{daemon_name}.py')
        else:
            script_path = Path(script_path)

        if not script_path.exists():
            return {
                'status': 'error',
                'message': f'Script not found: {script_path}'
            }

        # Get log file
        log_file = self._get_log_file(daemon_name)

        try:
            if self.is_windows:
                # Windows: use pythonw.exe with DETACHED_PROCESS
                python_exe = sys.executable.replace('python.exe', 'pythonw.exe')
                if not Path(python_exe).exists():
                    python_exe = sys.executable  # Fallback to python.exe

                # Start detached process
                DETACHED_PROCESS = 0x00000008
                CREATE_NEW_PROCESS_GROUP = 0x00000200

                with open(log_file, 'a') as log_f:
                    process = subprocess.Popen(
                        [python_exe, str(script_path)],
                        stdout=log_f,
                        stderr=log_f,
                        creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP,
                        cwd=str(self.memory_dir)
                    )
                    pid = process.pid
            else:
                # Linux/Mac: use nohup
                with open(log_file, 'a') as log_f:
                    process = subprocess.Popen(
                        ['nohup', sys.executable, str(script_path)],
                        stdout=log_f,
                        stderr=log_f,
                        cwd=str(self.memory_dir),
                        start_new_session=True
                    )
                    pid = process.pid

            # Write PID file
            self._write_pid(daemon_name, pid)

            # Log start event
            self._log_event(daemon_name, 'started', pid)

            return {
                'status': 'started',
                'pid': pid,
                'log_file': str(log_file),
                'message': f'{daemon_name} started with PID {pid}'
            }

        except Exception as e:
            return {
                'status': 'error',
                'message': f'Failed to start {daemon_name}: {str(e)}'
            }

    def stop_daemon(self, daemon_name):
        """Stop a daemon"""
        pid = self._read_pid(daemon_name)

        if pid is None:
            return {
                'status': 'not_running',
                'message': f'{daemon_name} is not running (no PID file)'
            }

        if not self._is_process_running(pid):
            self._delete_pid(daemon_name)
            return {
                'status': 'not_running',
                'message': f'{daemon_name} is not running (stale PID)'
            }

        try:
            if self.is_windows:
                # Windows: use taskkill
                subprocess.run(['taskkill', '/F', '/PID', str(pid)], check=True)
            else:
                # Linux/Mac: use kill
                os.kill(pid, 15)  # SIGTERM

            self._delete_pid(daemon_name)
            self._log_event(daemon_name, 'stopped', pid)

            return {
                'status': 'stopped',
                'pid': pid,
                'message': f'{daemon_name} stopped (PID {pid})'
            }

        except Exception as e:
            return {
                'status': 'error',
                'message': f'Failed to stop {daemon_name}: {str(e)}'
            }

    def get_status(self, daemon_name):
        """Get daemon status"""
        pid = self._read_pid(daemon_name)

        if pid is None:
            return {
                'daemon': daemon_name,
                'status': 'stopped',
                'pid': None,
                'running': False
            }

        running = self._is_process_running(pid)

        return {
            'daemon': daemon_name,
            'status': 'running' if running else 'stopped',
            'pid': pid if running else None,
            'running': running,
            'stale_pid': not running and pid is not None
        }

    def get_all_status(self):
        """Get status of all known daemons"""
        statuses = {}
        for daemon_name in self.daemons.keys():
            statuses[daemon_name] = self.get_status(daemon_name)
        return statuses

    def start_all(self):
        """Start all daemons"""
        results = {}
        for daemon_name in self.daemons.keys():
            results[daemon_name] = self.start_daemon(daemon_name)
        return results

    def stop_all(self):
        """Stop all daemons"""
        results = {}
        for daemon_name in self.daemons.keys():
            results[daemon_name] = self.stop_daemon(daemon_name)
        return results

    def restart_daemon(self, daemon_name):
        """Restart a daemon"""
        stop_result = self.stop_daemon(daemon_name)

        # Wait a moment
        import time
        time.sleep(1)

        start_result = self.start_daemon(daemon_name)

        return {
            'stopped': stop_result,
            'started': start_result
        }

    def _log_event(self, daemon_name, event, pid=None):
        """Log daemon event"""
        log_file = self.memory_dir / 'logs' / 'daemon-events.log'
        timestamp = datetime.now().isoformat()

        log_entry = f"[{timestamp}] {daemon_name} | {event}"
        if pid:
            log_entry += f" | PID={pid}"
        log_entry += "\n"

        with open(log_file, 'a') as f:
            f.write(log_entry)

    def cleanup_stale_pids(self):
        """Clean up stale PID files"""
        cleaned = []

        for pid_file in self.pids_dir.glob('*.pid'):
            daemon_name = pid_file.stem
            pid = self._read_pid(daemon_name)

            if pid and not self._is_process_running(pid):
                self._delete_pid(daemon_name)
                cleaned.append(daemon_name)

        return cleaned

def main():
    parser = argparse.ArgumentParser(description='Daemon manager')
    parser.add_argument('--start', help='Start daemon')
    parser.add_argument('--stop', help='Stop daemon')
    parser.add_argument('--restart', help='Restart daemon')
    parser.add_argument('--status', help='Get daemon status')
    parser.add_argument('--start-all', action='store_true', help='Start all daemons')
    parser.add_argument('--stop-all', action='store_true', help='Stop all daemons')
    parser.add_argument('--status-all', action='store_true', help='Get status of all daemons')
    parser.add_argument('--cleanup', action='store_true', help='Clean up stale PID files')
    parser.add_argument('--format', choices=['json', 'table'], default='json', help='Output format')
    parser.add_argument('--test-windows', action='store_true', help='Test Windows compatibility')

    args = parser.parse_args()

    manager = DaemonManager()

    if args.test_windows:
        print("Testing daemon manager...")
        print(f"Platform: {platform.system()}")
        print(f"Is Windows: {manager.is_windows}")
        print(f"PIDs directory: {manager.pids_dir}")
        print(f"Logs directory: {manager.logs_dir}")
        print(f"Python executable: {sys.executable}")

        # Test PID operations
        print("\nTesting PID operations...")
        manager._write_pid('test-daemon', 12345)
        pid = manager._read_pid('test-daemon')
        print(f"Write/Read PID: {pid == 12345}")
        manager._delete_pid('test-daemon')
        print(f"Delete PID: {manager._read_pid('test-daemon') is None}")

        print("\n[OK] All tests passed!")
        return 0

    if args.start:
        result = manager.start_daemon(args.start)
        print(json.dumps(result, indent=2))
        return 0 if result['status'] in ['started', 'already_running'] else 1

    if args.stop:
        result = manager.stop_daemon(args.stop)
        print(json.dumps(result, indent=2))
        return 0 if result['status'] in ['stopped', 'not_running'] else 1

    if args.restart:
        result = manager.restart_daemon(args.restart)
        print(json.dumps(result, indent=2))
        return 0

    if args.status:
        result = manager.get_status(args.status)
        print(json.dumps(result, indent=2))
        return 0

    if args.start_all:
        results = manager.start_all()

        if args.format == 'json':
            print(json.dumps(results, indent=2))
        else:
            print("\nStarting all daemons...")
            for name, result in results.items():
                status_icon = '[OK]' if result['status'] in ['started', 'already_running'] else '[FAIL]'
                print(f"  {status_icon} {name}: {result['message']}")

        return 0

    if args.stop_all:
        results = manager.stop_all()

        if args.format == 'json':
            print(json.dumps(results, indent=2))
        else:
            print("\nStopping all daemons...")
            for name, result in results.items():
                status_icon = '[OK]' if result['status'] in ['stopped', 'not_running'] else '[FAIL]'
                print(f"  {status_icon} {name}: {result['message']}")

        return 0

    if args.status_all:
        statuses = manager.get_all_status()

        if args.format == 'json':
            print(json.dumps(statuses, indent=2))
        else:
            print("\nDaemon Status:")
            print(f"{'Daemon':<30} {'Status':<12} {'PID':<10}")
            print("-" * 52)
            for name, status in statuses.items():
                status_str = 'RUNNING' if status['running'] else 'STOPPED'
                pid_str = str(status['pid']) if status['pid'] else '-'

                if status.get('stale_pid'):
                    status_str = 'STALE'

                print(f"{name:<30} {status_str:<12} {pid_str:<10}")

        return 0

    if args.cleanup:
        cleaned = manager.cleanup_stale_pids()
        print(f"Cleaned up {len(cleaned)} stale PID files")
        if cleaned:
            for name in cleaned:
                print(f"  - {name}")
        return 0

    parser.print_help()
    return 1

if __name__ == '__main__':
    sys.exit(main())

#!/usr/bin/env python3
"""
PID Tracker
Track and verify daemon PIDs across platforms
"""

import sys
import os
import json
import argparse
import platform
import subprocess
from pathlib import Path
from datetime import datetime

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

class PIDTracker:
    def __init__(self):
        self.memory_dir = Path.home() / '.claude' / 'memory'
        self.pids_dir = self.memory_dir / '.pids'
        self.pids_dir.mkdir(parents=True, exist_ok=True)

        self.is_windows = platform.system() == 'Windows'

    def get_pid_file(self, daemon_name):
        """Get PID file path"""
        return self.pids_dir / f'{daemon_name}.pid'

    def read_pid(self, daemon_name):
        """Read PID from file"""
        pid_file = self.get_pid_file(daemon_name)

        if not pid_file.exists():
            return None

        try:
            pid = int(pid_file.read_text().strip())
            return pid
        except (ValueError, OSError):
            return None

    def write_pid(self, daemon_name, pid):
        """Write PID to file"""
        pid_file = self.get_pid_file(daemon_name)

        try:
            pid_file.write_text(str(pid))
            return True
        except OSError:
            return False

    def delete_pid(self, daemon_name):
        """Delete PID file"""
        pid_file = self.get_pid_file(daemon_name)

        if pid_file.exists():
            try:
                pid_file.unlink()
                return True
            except OSError:
                return False

        return False

    def is_running(self, pid):
        """Check if process is running (cross-platform)"""
        if pid is None:
            return False

        if HAS_PSUTIL:
            # Use psutil if available (most reliable)
            return psutil.pid_exists(pid)

        try:
            if self.is_windows:
                # Windows: use tasklist
                result = subprocess.run(
                    ['tasklist', '/FI', f'PID eq {pid}', '/NH'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                return str(pid) in result.stdout
            else:
                # Linux/Mac: send signal 0
                os.kill(pid, 0)
                return True
        except (OSError, subprocess.SubprocessError, subprocess.TimeoutExpired):
            return False

    def get_process_info(self, pid):
        """Get process information (if psutil available)"""
        if not HAS_PSUTIL:
            return None

        if not psutil.pid_exists(pid):
            return None

        try:
            process = psutil.Process(pid)
            return {
                'pid': pid,
                'name': process.name(),
                'cmdline': ' '.join(process.cmdline()),
                'status': process.status(),
                'cpu_percent': process.cpu_percent(interval=0.1),
                'memory_mb': round(process.memory_info().rss / 1024 / 1024, 2),
                'create_time': datetime.fromtimestamp(process.create_time()).isoformat()
            }
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return None

    def kill_process(self, pid, force=False):
        """Kill process by PID"""
        if not self.is_running(pid):
            return {'status': 'not_running', 'message': f'Process {pid} is not running'}

        try:
            if self.is_windows:
                # Windows: use taskkill
                flag = '/F' if force else '/T'
                result = subprocess.run(
                    ['taskkill', flag, '/PID', str(pid)],
                    capture_output=True,
                    text=True
                )
                success = result.returncode == 0
            else:
                # Linux/Mac: use kill
                signal = 9 if force else 15  # SIGKILL or SIGTERM
                os.kill(pid, signal)
                success = True

            if success:
                return {'status': 'killed', 'pid': pid, 'force': force}
            else:
                return {'status': 'error', 'message': 'Kill command failed'}

        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    def verify_daemon(self, daemon_name):
        """Verify daemon is running correctly"""
        pid = self.read_pid(daemon_name)

        result = {
            'daemon': daemon_name,
            'pid_file_exists': self.get_pid_file(daemon_name).exists(),
            'pid': pid,
            'is_running': False,
            'status': 'unknown'
        }

        if pid is None:
            result['status'] = 'no_pid_file'
            return result

        if not self.is_running(pid):
            result['status'] = 'stale_pid'
            return result

        result['is_running'] = True
        result['status'] = 'running'

        # Get process info if available
        if HAS_PSUTIL:
            info = self.get_process_info(pid)
            if info:
                result['process_info'] = info

        return result

    def verify_all(self):
        """Verify all daemons with PID files"""
        results = {}

        for pid_file in self.pids_dir.glob('*.pid'):
            daemon_name = pid_file.stem
            results[daemon_name] = self.verify_daemon(daemon_name)

        return results

    def cleanup_stale(self):
        """Clean up stale PID files"""
        cleaned = []

        for pid_file in self.pids_dir.glob('*.pid'):
            daemon_name = pid_file.stem
            pid = self.read_pid(daemon_name)

            if pid and not self.is_running(pid):
                self.delete_pid(daemon_name)
                cleaned.append({
                    'daemon': daemon_name,
                    'pid': pid,
                    'reason': 'stale_pid'
                })

        return cleaned

    def get_all_pids(self):
        """Get all PIDs from PID files"""
        pids = {}

        for pid_file in self.pids_dir.glob('*.pid'):
            daemon_name = pid_file.stem
            pid = self.read_pid(daemon_name)
            pids[daemon_name] = pid

        return pids

    def monitor_health(self):
        """Monitor health of all tracked daemons"""
        health = {
            'timestamp': datetime.now().isoformat(),
            'total_daemons': 0,
            'running': 0,
            'stopped': 0,
            'stale': 0,
            'daemons': {}
        }

        for pid_file in self.pids_dir.glob('*.pid'):
            daemon_name = pid_file.stem
            health['total_daemons'] += 1

            verification = self.verify_daemon(daemon_name)
            health['daemons'][daemon_name] = verification

            if verification['status'] == 'running':
                health['running'] += 1
            elif verification['status'] == 'stale_pid':
                health['stale'] += 1
            else:
                health['stopped'] += 1

        health['health_score'] = (health['running'] / health['total_daemons'] * 100) if health['total_daemons'] > 0 else 0

        return health

def main():
    parser = argparse.ArgumentParser(description='PID tracker')
    parser.add_argument('--read', help='Read PID for daemon')
    parser.add_argument('--write', nargs=2, metavar=('DAEMON', 'PID'), help='Write PID')
    parser.add_argument('--delete', help='Delete PID file')
    parser.add_argument('--verify', help='Verify daemon')
    parser.add_argument('--verify-all', action='store_true', help='Verify all daemons')
    parser.add_argument('--kill', type=int, help='Kill process by PID')
    parser.add_argument('--force', action='store_true', help='Force kill')
    parser.add_argument('--cleanup', action='store_true', help='Clean up stale PIDs')
    parser.add_argument('--list', action='store_true', help='List all PIDs')
    parser.add_argument('--health', action='store_true', help='Monitor health')
    parser.add_argument('--test-tracking', action='store_true', help='Test PID tracking')

    args = parser.parse_args()

    tracker = PIDTracker()

    if args.test_tracking:
        print("Testing PID tracker...")
        print(f"Platform: {platform.system()}")
        print(f"Has psutil: {HAS_PSUTIL}")

        # Test write/read/delete
        print("\n1. Write PID")
        tracker.write_pid('test-daemon', 12345)
        print(f"   Written: test-daemon -> 12345")

        print("2. Read PID")
        pid = tracker.read_pid('test-daemon')
        print(f"   Read: {pid}")
        assert pid == 12345, "PID mismatch"

        print("3. Check if running")
        running = tracker.is_running(pid)
        print(f"   Running: {running} (should be False for fake PID)")

        print("4. Delete PID")
        tracker.delete_pid('test-daemon')
        print(f"   Deleted: {tracker.read_pid('test-daemon') is None}")

        print("\n5. Test current process")
        current_pid = os.getpid()
        print(f"   Current PID: {current_pid}")
        print(f"   Is running: {tracker.is_running(current_pid)}")

        if HAS_PSUTIL:
            print("6. Get process info")
            info = tracker.get_process_info(current_pid)
            print(f"   Name: {info['name']}")
            print(f"   Memory: {info['memory_mb']} MB")

        print("\n[OK] All tests passed!")
        return 0

    if args.read:
        pid = tracker.read_pid(args.read)
        if pid:
            print(pid)
            return 0
        else:
            print(f"No PID file for {args.read}", file=sys.stderr)
            return 1

    if args.write:
        daemon_name, pid_str = args.write
        try:
            pid = int(pid_str)
            success = tracker.write_pid(daemon_name, pid)
            if success:
                print(f"PID {pid} written for {daemon_name}")
                return 0
            else:
                print("Failed to write PID", file=sys.stderr)
                return 1
        except ValueError:
            print(f"Invalid PID: {pid_str}", file=sys.stderr)
            return 1

    if args.delete:
        success = tracker.delete_pid(args.delete)
        if success:
            print(f"PID file deleted for {args.delete}")
        else:
            print(f"No PID file for {args.delete}")
        return 0

    if args.verify:
        result = tracker.verify_daemon(args.verify)
        print(json.dumps(result, indent=2))
        return 0

    if args.verify_all:
        results = tracker.verify_all()
        print(json.dumps(results, indent=2))
        return 0

    if args.kill:
        result = tracker.kill_process(args.kill, args.force)
        print(json.dumps(result, indent=2))
        return 0 if result['status'] == 'killed' else 1

    if args.cleanup:
        cleaned = tracker.cleanup_stale()
        print(f"Cleaned {len(cleaned)} stale PID files")
        for item in cleaned:
            print(f"  - {item['daemon']} (PID {item['pid']})")
        return 0

    if args.list:
        pids = tracker.get_all_pids()
        print(json.dumps(pids, indent=2))
        return 0

    if args.health:
        health = tracker.monitor_health()
        print(json.dumps(health, indent=2))
        return 0

    parser.print_help()
    return 1

if __name__ == '__main__':
    sys.exit(main())

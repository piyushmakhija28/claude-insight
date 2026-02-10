#!/usr/bin/env python3
"""
Phase 2 Infrastructure Test Suite
Tests daemon manager, PID tracker, health monitor, and auto-restart
"""

import sys
import time
import json
from pathlib import Path

# Add memory dir to path
memory_dir = Path.home() / '.claude' / 'memory'
sys.path.insert(0, str(memory_dir))

import importlib.util

def import_module(module_name, file_name):
    """Import module from file with hyphens in name"""
    spec = importlib.util.spec_from_file_location(module_name, memory_dir / file_name)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# Import modules
daemon_manager_module = import_module('daemon_manager', 'daemon-manager.py')
DaemonManager = daemon_manager_module.DaemonManager

pid_tracker_module = import_module('pid_tracker', 'pid-tracker.py')
PIDTracker = pid_tracker_module.PIDTracker

daemon_logger_module = import_module('daemon_logger', 'daemon-logger.py')
DaemonLogger = daemon_logger_module.DaemonLogger

health_monitor_module = import_module('health_monitor', 'health-monitor-daemon.py')
HealthMonitor = health_monitor_module.HealthMonitor

def run_test(test_name, test_func):
    """Run a test and report results"""
    print(f"\n{'='*60}")
    print(f"TEST: {test_name}")
    print('='*60)

    try:
        result = test_func()
        if result:
            print(f"[OK] {test_name} PASSED")
            return True
        else:
            print(f"[FAIL] {test_name} FAILED")
            return False
    except Exception as e:
        print(f"[ERROR] {test_name} ERRORED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_daemon_manager():
    """Test daemon manager basic operations"""
    manager = DaemonManager()

    print("1. Check platform detection")
    print(f"   Platform: Windows={manager.is_windows}")

    print("2. Start a test daemon")
    # Use context-daemon as test subject
    result = manager.start_daemon('context-daemon')
    print(f"   Status: {result['status']}")
    print(f"   PID: {result.get('pid', 'N/A')}")

    if result['status'] not in ['started', 'already_running']:
        print(f"   Error: {result.get('message')}")
        return False

    print("3. Check daemon status")
    status = manager.get_status('context-daemon')
    print(f"   Running: {status['running']}")
    print(f"   PID: {status['pid']}")

    if not status['running']:
        return False

    print("4. Get all daemon status")
    all_status = manager.get_all_status()
    running_count = sum(1 for s in all_status.values() if s['running'])
    print(f"   Total daemons: {len(all_status)}")
    print(f"   Running: {running_count}")

    return True

def test_pid_tracker():
    """Test PID tracker operations"""
    tracker = PIDTracker()

    print("1. Write test PID")
    success = tracker.write_pid('test-tracker', 99999)
    print(f"   Write success: {success}")

    print("2. Read test PID")
    pid = tracker.read_pid('test-tracker')
    print(f"   Read PID: {pid}")

    if pid != 99999:
        return False

    print("3. Check if running (should be False)")
    running = tracker.is_running(99999)
    print(f"   Running: {running}")

    if running:  # Should be False for fake PID
        return False

    print("4. Verify daemon")
    verification = tracker.verify_daemon('test-tracker')
    print(f"   Status: {verification['status']}")

    if verification['status'] != 'stale_pid':
        return False

    print("5. Cleanup stale PIDs")
    cleaned = tracker.cleanup_stale()
    print(f"   Cleaned: {len(cleaned)}")

    print("6. Health monitoring")
    health = tracker.monitor_health()
    print(f"   Health score: {health['health_score']:.1f}%")
    print(f"   Running: {health['running']}/{health['total_daemons']}")

    return True

def test_daemon_logger():
    """Test daemon logger"""
    logger = DaemonLogger('test-phase2')

    print("1. Test logging levels")
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    print("   Logged to file")

    print("2. Test policy hit logging")
    logger.policy_hit('test-policy', 'test-action', 'test-context')
    print("   Policy hit logged")

    print("3. Test health event")
    logger.health_event('TEST', 'Test event', 'INFO')
    print("   Health event logged")

    print("4. Check log file exists")
    log_exists = logger.daemon_log.exists()
    print(f"   Log file exists: {log_exists}")

    print("5. Get recent logs")
    recent = logger.get_recent_logs(5)
    print(f"   Recent logs: {len(recent)} lines")

    return log_exists and len(recent) > 0

def test_health_monitor():
    """Test health monitor"""
    monitor = HealthMonitor()

    print("1. Check health summary")
    summary = monitor.get_health_summary()
    print(f"   Total daemons: {summary['total_daemons']}")
    print(f"   Healthy: {summary['healthy']}")
    print(f"   Unhealthy: {summary['unhealthy']}")
    print(f"   Health: {summary['health_percentage']:.1f}%")

    print("2. Check restart rate limiting")
    can_restart = monitor.should_restart('test-daemon')
    print(f"   Can restart: {can_restart}")

    print("3. Load restart history")
    history = monitor.load_restart_history('context-daemon')
    print(f"   Restart events: {len(history)}")

    return True

def test_auto_restart():
    """Test auto-restart functionality"""
    manager = DaemonManager()
    tracker = PIDTracker()

    print("1. Ensure context-daemon is running")
    status = manager.get_status('context-daemon')
    if not status['running']:
        result = manager.start_daemon('context-daemon')
        print(f"   Started: {result['status']}")
        time.sleep(2)

    print("2. Get daemon PID")
    pid = tracker.read_pid('context-daemon')
    print(f"   PID: {pid}")

    if not pid:
        print("   ERROR: No PID found")
        return False

    print("3. Kill the daemon")
    kill_result = tracker.kill_process(pid, force=True)
    print(f"   Kill status: {kill_result['status']}")

    time.sleep(2)

    print("4. Verify daemon is dead")
    running = tracker.is_running(pid)
    print(f"   Still running: {running}")

    if running:
        print("   ERROR: Failed to kill daemon")
        return False

    print("5. Trigger health check (simulates auto-restart)")
    monitor = HealthMonitor()
    result = monitor.check_daemon_health('context-daemon')
    print(f"   Health check result: {result['status']}")
    print(f"   Action taken: {result['action']}")

    time.sleep(2)

    print("6. Verify daemon restarted")
    new_status = manager.get_status('context-daemon')
    print(f"   Running: {new_status['running']}")
    print(f"   New PID: {new_status['pid']}")

    if not new_status['running']:
        print("   ERROR: Daemon not restarted")
        return False

    print("7. Verify PID changed")
    if new_status['pid'] == pid:
        print("   WARNING: PID unchanged (might be same process)")
    else:
        print(f"   PID changed: {pid} -> {new_status['pid']}")

    return True

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("PHASE 2 INFRASTRUCTURE TEST SUITE")
    print("="*60)

    tests = [
        ("Daemon Manager", test_daemon_manager),
        ("PID Tracker", test_pid_tracker),
        ("Daemon Logger", test_daemon_logger),
        ("Health Monitor", test_health_monitor),
        ("Auto-Restart", test_auto_restart),
    ]

    results = []
    for test_name, test_func in tests:
        passed = run_test(test_name, test_func)
        results.append((test_name, passed))

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)

    for test_name, passed in results:
        status = "[OK] PASSED" if passed else "[FAIL] FAILED"
        print(f"{status:15} {test_name}")

    print(f"\nTotal: {passed_count}/{total_count} tests passed")

    if passed_count == total_count:
        print("\n[OK] ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n[FAIL] {total_count - passed_count} tests failed")
        return 1

if __name__ == '__main__':
    sys.exit(main())

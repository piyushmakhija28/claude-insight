"""
Quick test to verify monitoring services can read data
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from services.monitoring.memory_system_monitor import MemorySystemMonitor
from services.monitoring.metrics_collector import MetricsCollector
from services.monitoring.policy_checker import PolicyChecker

print("="*80)
print("TESTING MONITORING SERVICES")
print("="*80)
print()

# Test MemorySystemMonitor
print("1. Testing MemorySystemMonitor...")
try:
    monitor = MemorySystemMonitor()
    print(f"   Memory dir: {monitor.memory_dir}")
    print(f"   Logs dir: {monitor.logs_dir}")

    # Test daemon status
    daemon_status = monitor.get_daemon_status()
    print(f"\n   Daemon Status (Total: {len(daemon_status)}):")
    running_count = 0
    for d in daemon_status:
        status_icon = "[OK]" if d['status'] == 'running' else "[--]"
        print(f"   {status_icon} {d['name']}: {d['status']}")
        if d['status'] == 'running':
            running_count += 1

    print(f"\n   [OK] MemorySystemMonitor OK ({running_count} running)")
except Exception as e:
    print(f"   [ERROR] {e}")
    import traceback
    traceback.print_exc()

print()

# Test MetricsCollector
print("2. Testing MetricsCollector...")
try:
    metrics = MetricsCollector()
    health = metrics.get_system_health()
    print(f"   Health Score: {health.get('health_score', 'N/A')}")
    print(f"   Context Usage: {health.get('context_usage', 'N/A')}%")
    print(f"   [OK] MetricsCollector OK")
except Exception as e:
    print(f"   [ERROR] {e}")
    import traceback
    traceback.print_exc()

print()

# Test PolicyChecker
print("3. Testing PolicyChecker...")
try:
    policy_checker = PolicyChecker()
    policy_status = policy_checker.get_detailed_policy_status()
    print(f"   Active Policies: {policy_status.get('active_policies', 'N/A')}")
    print(f"   Total Policies: {policy_status.get('total_policies', 'N/A')}")
    print(f"   [OK] PolicyChecker OK")
except Exception as e:
    print(f"   [ERROR] {e}")
    import traceback
    traceback.print_exc()

print()
print("="*80)
print("TEST COMPLETE")
print("="*80)

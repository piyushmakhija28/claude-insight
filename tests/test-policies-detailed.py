"""
Detailed policy status checker
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from services.monitoring.policy_checker import PolicyChecker

print("="*80)
print("DETAILED POLICY STATUS CHECK")
print("="*80)
print()

checker = PolicyChecker()
all_statuses = checker.get_all_policies_status()

active_count = 0
error_count = 0
warning_count = 0

for policy in all_statuses:
    status_icon = "[OK]" if policy['status'] == 'active' else "[ERROR]" if policy['status'] == 'error' else "[WARN]"

    print(f"{status_icon} {policy['name']}")
    print(f"    Level: {policy.get('level', 'N/A')}")
    print(f"    Phase: {policy['phase']}")
    print(f"    Status: {policy['status']}")
    print(f"    Details: {policy['details']}")
    print()

    if policy['status'] == 'active':
        active_count += 1
    elif policy['status'] == 'error':
        error_count += 1
    elif policy['status'] == 'warning':
        warning_count += 1

print("="*80)
print(f"SUMMARY: {active_count} Active, {error_count} Error, {warning_count} Warning")
print(f"Total: {len(all_statuses)} policies")
print("="*80)

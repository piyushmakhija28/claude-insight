#!/usr/bin/env python3
"""
Session Start Check - Run at the beginning of every conversation

This script checks:
1. All hooks enforcement scripts are present (3-level architecture)
2. Latest flow trace from previous session
3. System health summary

Usage:
    python session-start-check.py [--verbose]
"""

import sys
import json
from pathlib import Path
from datetime import datetime

MEMORY_DIR = Path.home() / ".claude" / "memory"
CURRENT_DIR = MEMORY_DIR / "current"
LATEST_TRACE = MEMORY_DIR / "logs" / "latest-flow-trace.json"

# Colors
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
CYAN = '\033[96m'
RESET = '\033[0m'
BOLD = '\033[1m'

# Hook scripts that must be present (3-level architecture enforcement)
REQUIRED_SCRIPTS = [
    ('3-level-flow.py',           'Main 3-level flow hook'),
    ('blocking-policy-enforcer.py', 'Level -1 blocking enforcement'),
    ('auto-fix-enforcer.sh',      'Auto-fix enforcement'),
    ('context-monitor-v2.py',     'Level 1 context monitoring'),
    ('session-id-generator.py',   'Level 1 session tracking'),
    ('clear-session-handler.py',  'Session clear handler'),
    ('stop-notifier.py',          'Stop hook notifier'),
    ('per-request-enforcer.py',   'Per-request policy check'),
]


def check_hooks():
    """Check that all 3-level enforcement scripts are present"""
    results = []
    all_present = True

    for script_name, description in REQUIRED_SCRIPTS:
        script_path = CURRENT_DIR / script_name
        present = script_path.exists()
        if not present:
            all_present = False
        results.append({
            'name': script_name,
            'description': description,
            'present': present
        })

    return {
        'status': 'healthy' if all_present else 'degraded',
        'total': len(REQUIRED_SCRIPTS),
        'present': sum(1 for r in results if r['present']),
        'scripts': results
    }


def check_latest_session():
    """Check latest flow trace from previous session"""
    try:
        if not LATEST_TRACE.exists():
            return None

        with open(LATEST_TRACE, 'r', encoding='utf-8', errors='ignore') as f:
            data = json.load(f)

        timestamp_str = data.get('timestamp', '')
        try:
            ts = datetime.fromisoformat(timestamp_str)
            age_minutes = int((datetime.now() - ts).total_seconds() / 60)
        except Exception:
            age_minutes = None

        final = data.get('final_decision', {})
        return {
            'session_id': data.get('session_id', 'unknown'),
            'model': final.get('model_selected', 'unknown'),
            'complexity': final.get('complexity', 0),
            'context_pct': data.get('level_1', {}).get('context_pct', 0),
            'age_minutes': age_minutes,
            'levels_passed': sum(1 for k in ['level_minus1', 'level_1', 'level_2', 'level_3']
                                 if data.get(k, {}).get('status') == 'passed')
        }

    except Exception:
        return None


def main():
    verbose = '--verbose' in sys.argv or '-v' in sys.argv

    print(f"\n{BOLD}{'='*60}{RESET}")
    print(f"{BOLD}{BLUE}SESSION START CHECK - 3-LEVEL ARCHITECTURE{RESET}")
    print(f"{BOLD}{'='*60}{RESET}\n")

    # Check hooks/enforcement scripts
    print(f"{BOLD}[1/2] Checking Enforcement Scripts (current/)...{RESET}")
    hook_status = check_hooks()

    if hook_status['status'] == 'healthy':
        print(f"  {GREEN}[OK]{RESET} All {hook_status['present']}/{hook_status['total']} scripts present")
    else:
        print(f"  {YELLOW}[!]{RESET} Only {hook_status['present']}/{hook_status['total']} scripts present")

    if verbose or hook_status['status'] != 'healthy':
        print()
        for script in hook_status['scripts']:
            if script['present']:
                print(f"    {GREEN}[OK]{RESET} {script['name']:35s} {script['description']}")
            else:
                print(f"    {RED}[X]{RESET} {script['name']:35s} MISSING")

    print()

    # Check latest session trace
    print(f"{BOLD}[2/2] Checking Latest Session Trace...{RESET}")
    session = check_latest_session()

    if session:
        age = session['age_minutes']
        age_str = f"{age} min ago" if age is not None else "unknown age"
        print(f"  {GREEN}[OK]{RESET} Last session: {session['session_id']} ({age_str})")
        print(f"    {BOLD}Model:{RESET}     {session['model'].upper()}")
        print(f"    {BOLD}Complexity:{RESET} {session['complexity']}")
        print(f"    {BOLD}Context:{RESET}   {session['context_pct']}%")
        print(f"    {BOLD}Levels OK:{RESET} {session['levels_passed']}/4")
    else:
        print(f"  {YELLOW}[!]{RESET} No previous session trace found")
        print(f"    {BOLD}Tip:{RESET} Send a message to generate flow trace")

    print(f"\n{BOLD}{'='*60}{RESET}")
    print(f"{BOLD}STATUS SUMMARY{RESET}")
    print(f"{BOLD}{'='*60}{RESET}\n")

    if hook_status['status'] == 'healthy':
        print(f"{GREEN}[OK] Enforcement Scripts: READY{RESET}")
        print(f"{GREEN}[OK] 3-Level Architecture: ACTIVE{RESET}")
        if session:
            print(f"{GREEN}[OK] Last Session: AVAILABLE{RESET}")
        else:
            print(f"{YELLOW}[!] Last Session: None yet{RESET}")
        print(f"\n{BOLD}System ready. Hooks will enforce policies on every message.{RESET}")
    else:
        missing = [s['name'] for s in hook_status['scripts'] if not s['present']]
        print(f"{RED}[X] Enforcement Scripts: DEGRADED{RESET}")
        print(f"{YELLOW}[!] Missing: {', '.join(missing)}{RESET}")
        print(f"\n{BOLD}Run setup script to reinstall missing scripts.{RESET}")

    print(f"\n{BOLD}{'='*60}{RESET}\n")

    return 0 if hook_status['status'] == 'healthy' else 1


if __name__ == "__main__":
    sys.exit(main())

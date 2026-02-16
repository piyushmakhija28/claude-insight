#[!]/usr/bin/env python3
"""
Session Start Check - Run at the beginning of every conversation

This script checks:
1. All daemon PIDs and status
2. Latest recommendations
3. System health
4. Provides quick summary for Claude to know the state

Usage:
    python session-start-check.py [--verbose]
"""

import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime

MEMORY_DIR = Path.home() / ".claude" / "memory"
RECOMMENDATIONS_FILE = MEMORY_DIR / ".latest-recommendations.json"

# Colors
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
CYAN = '\033[96m'
RESET = '\033[0m'
BOLD = '\033[1m'

def check_daemons():
    """Check status of all daemons"""
    try:
        result = subprocess.run(
            ["python", str(MEMORY_DIR / "daemon-manager.py"), "--status-all"],
            capture_output=True,
            text=True,
            timeout=10,
            encoding='utf-8',
            errors='replace'
        )

        if result.returncode == 0:
            data = json.loads(result.stdout)

            running = sum(1 for d in data.values() if d.get('running', False))
            total = len(data)

            # 8/9 is healthy (auto-recommendation is optional)
            # 8 core daemons must be running
            is_healthy = running >= 8

            return {
                "total": total,
                "running": running,
                "status": "healthy" if is_healthy else "degraded",
                "daemons": data
            }
        else:
            return {"total": 0, "running": 0, "status": "error", "daemons": {}}

    except Exception as e:
        return {"total": 0, "running": 0, "status": "error", "error": str(e), "daemons": {}}

def check_recommendations():
    """Check latest recommendations"""
    try:
        if not RECOMMENDATIONS_FILE.exists():
            return None

        with open(RECOMMENDATIONS_FILE, 'r') as f:
            data = json.load(f)

        # Calculate age
        timestamp_str = data.get('timestamp', '')
        try:
            ts = datetime.fromisoformat(timestamp_str)
            age_seconds = (datetime.now() - ts).total_seconds()
            age_minutes = int(age_seconds / 60)
        except:
            age_minutes = None

        return {
            "model": data.get('model', {}).get('recommended', 'unknown'),
            "skills": data.get('skills', []),
            "agents": data.get('agents', []),
            "context_status": data.get('context', {}).get('status', 'unknown'),
            "age_minutes": age_minutes,
            "optimizations": len(data.get('optimizations', [])),
            "warnings": len(data.get('warnings', []))
        }

    except Exception as e:
        return None

def main():
    verbose = '--verbose' in sys.argv or '-v' in sys.argv

    print(f"\n{BOLD}{'='*60}{RESET}")
    print(f"{BOLD}{BLUE}SESSION START CHECK{RESET}")
    print(f"{BOLD}{'='*60}{RESET}\n")

    # Check daemons
    print(f"{BOLD}[1/2] Checking Daemons...{RESET}")
    daemon_status = check_daemons()

    if daemon_status['status'] == 'healthy':
        print(f"  {GREEN}[OK]{RESET} All {daemon_status['running']}/{daemon_status['total']} daemons running")
    elif daemon_status['status'] == 'degraded':
        print(f"  {YELLOW}[!]{RESET} Only {daemon_status['running']}/{daemon_status['total']} daemons running")
    else:
        print(f"  {RED}[X]{RESET} Daemon check failed")

    if verbose and daemon_status.get('daemons'):
        print(f"\n  {BOLD}Daemon Details:{RESET}")
        for name, info in daemon_status['daemons'].items():
            status = info.get('status', 'unknown')
            pid = info.get('pid', 'N/A')

            if status == 'running':
                print(f"    {GREEN}[OK]{RESET} {name:30s} PID: {pid}")
            else:
                print(f"    {RED}[X]{RESET} {name:30s} STOPPED")

    print()

    # Check recommendations
    print(f"{BOLD}[2/2] Checking Latest Recommendations...{RESET}")
    recommendations = check_recommendations()

    if recommendations:
        age = recommendations['age_minutes']
        age_str = f"{age} min ago" if age is not None else "unknown age"

        print(f"  {GREEN}[OK]{RESET} Recommendations available ({age_str})")
        print(f"    {BOLD}Model:{RESET} {recommendations['model'].upper()}")
        print(f"    {BOLD}Skills:{RESET} {len(recommendations['skills'])} detected")
        print(f"    {BOLD}Agents:{RESET} {len(recommendations['agents'])} detected")
        print(f"    {BOLD}Context:{RESET} {recommendations['context_status']}")

        if recommendations['skills']:
            print(f"\n    {BOLD}Suggested Skills:{RESET}")
            for skill in recommendations['skills'][:3]:
                print(f"      -> {CYAN}{skill}{RESET}")

        if recommendations['agents']:
            print(f"\n    {BOLD}Suggested Agents:{RESET}")
            for agent in recommendations['agents'][:2]:
                print(f"      -> {BLUE}{agent}{RESET}")

        if recommendations['optimizations'] > 0:
            print(f"\n    {BOLD}Optimizations:{RESET} {recommendations['optimizations']} recommended")

        if recommendations['warnings'] > 0:
            print(f"    {YELLOW}Warnings:{RESET} {recommendations['warnings']} detected")
    else:
        print(f"  {YELLOW}[!]{RESET} No recommendations available yet")
        print(f"    {BOLD}Tip:{RESET} Send a message to generate recommendations")

    print(f"\n{BOLD}{'='*60}{RESET}")
    print(f"{BOLD}STATUS SUMMARY{RESET}")
    print(f"{BOLD}{'='*60}{RESET}\n")

    # Overall status
    if daemon_status['status'] == 'healthy' and recommendations:
        print(f"{GREEN}[OK] System: READY{RESET}")
        print(f"{GREEN}[OK] Automation: ACTIVE{RESET}")
        print(f"{GREEN}[OK] Recommendations: AVAILABLE{RESET}")
        print(f"\n{BOLD}You can proceed with full automation support[!]{RESET}")
    elif daemon_status['status'] == 'healthy':
        print(f"{GREEN}[OK] System: READY{RESET}")
        print(f"{GREEN}[OK] Automation: ACTIVE{RESET}")
        print(f"{YELLOW}[!] Recommendations: Not yet generated{RESET}")
        print(f"\n{BOLD}System ready. Send a message to get recommendations.{RESET}")
    else:
        print(f"{RED}[X] System: DEGRADED{RESET}")
        print(f"{YELLOW}[!] Automation: PARTIAL{RESET}")
        print(f"\n{BOLD}Some daemons not running. Check status above.{RESET}")

    print(f"\n{BOLD}{'='*60}{RESET}\n")

    # Exit code
    if daemon_status['status'] == 'healthy':
        return 0
    else:
        return 1

if __name__ == "__main__":
    sys.exit(main())

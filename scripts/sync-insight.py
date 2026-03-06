#!/usr/bin/env python3
"""Selective Sync for Claude Insight Repository.

This Python wrapper delegates to the appropriate sync script based on OS.
- Windows: Runs sync-insight.bat
- Unix/Linux/macOS: Runs sync-insight (bash)

Purpose: Quick sync for claude-insight updates (scripts, policies, dashboard).
"""

import sys
import os
import subprocess
import platform
from pathlib import Path


def main():
    """Run selective sync for claude-insight."""
    script_dir = Path(__file__).parent

    # Detect OS and run appropriate script
    if platform.system() == 'Windows':
        # Windows: use .bat file
        sync_script = script_dir / 'sync-insight.bat'
        if not sync_script.exists():
            print(f"[ERROR] sync-insight.bat not found in {script_dir}")
            return 1

        try:
            result = subprocess.run([str(sync_script)], check=False)
            return result.returncode
        except Exception as e:
            print(f"[ERROR] Failed to run sync-insight.bat: {e}")
            return 1
    else:
        # Unix/Linux/macOS: use bash script
        sync_script = script_dir / 'sync-insight'
        if not sync_script.exists():
            print(f"[ERROR] sync-insight not found in {script_dir}")
            return 1

        try:
            result = subprocess.run(['bash', str(sync_script)], check=False)
            return result.returncode
        except Exception as e:
            print(f"[ERROR] Failed to run sync-insight: {e}")
            return 1


if __name__ == '__main__':
    sys.exit(main())

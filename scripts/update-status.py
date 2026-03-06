#!/usr/bin/env python3
"""Update Status Reporter - Shows clear success/warning/failed messages.

This Python wrapper delegates to the appropriate status script based on OS.
- Windows: Runs update-status.bat
- Unix/Linux/macOS: Runs update-status (bash)

Purpose: Show clear, user-friendly update completion messages.
Distinguishes between:
  - Successful updates with optional warnings (still works!)
  - Actual failures (system broken)

Usage:
  update-status success
  update-status warning "optional warning message"
  update-status failed "error message"
"""

import sys
import subprocess
import platform
from pathlib import Path


def main():
    """Run update status reporter."""
    script_dir = Path(__file__).parent

    # Get arguments (status and optional message)
    if len(sys.argv) < 2:
        print("Usage: update-status [success|warning|failed] [optional message]")
        return 1

    status = sys.argv[1]
    message = ' '.join(sys.argv[2:]) if len(sys.argv) > 2 else ""

    # Detect OS and run appropriate script
    if platform.system() == 'Windows':
        # Windows: use .bat file
        status_script = script_dir / 'update-status.bat'
        if not status_script.exists():
            print(f"[ERROR] update-status.bat not found in {script_dir}")
            return 1

        try:
            if message:
                result = subprocess.run([str(status_script), status, message], check=False)
            else:
                result = subprocess.run([str(status_script), status], check=False)
            return result.returncode
        except Exception as e:
            print(f"[ERROR] Failed to run update-status.bat: {e}")
            return 1
    else:
        # Unix/Linux/macOS: use bash script
        status_script = script_dir / 'update-status'
        if not status_script.exists():
            print(f"[ERROR] update-status not found in {script_dir}")
            return 1

        try:
            if message:
                result = subprocess.run(['bash', str(status_script), status, message], check=False)
            else:
                result = subprocess.run(['bash', str(status_script), status], check=False)
            return result.returncode
        except Exception as e:
            print(f"[ERROR] Failed to run update-status: {e}")
            return 1


if __name__ == '__main__':
    sys.exit(main())

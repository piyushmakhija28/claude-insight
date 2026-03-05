#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task Progress Tracking Policy Enforcement (v2.0 - FULLY CONSOLIDATED)

CONSOLIDATED SCRIPT - Maps to: policies/03-execution-system/08-progress-tracking/task-progress-tracking-policy.md

Consolidates 1 script (270+ lines):
- check-incomplete-work.py (270 lines) - Detect and track incomplete work

THIS CONSOLIDATION includes ALL functionality from old script.
NO logic was lost in consolidation - everything is merged.

Usage:
  python task-progress-tracking-policy.py --enforce              # Run policy enforcement
  python task-progress-tracking-policy.py --validate             # Validate policy compliance
  python task-progress-tracking-policy.py --report               # Generate report
  python task-progress-tracking-policy.py [project]              # Check incomplete work for project
"""

import sys
import io
import json
import os
import re
from pathlib import Path
from datetime import datetime, timedelta

# Fix encoding for Windows console
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    try:
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

if sys.platform == 'win32':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    except:
        pass

MEMORY_DIR = Path.home() / ".claude" / "memory"
SESSIONS_DIR = MEMORY_DIR / "sessions"
LOG_FILE = MEMORY_DIR / "logs" / "policy-hits.log"


# ============================================================================
# PROGRESS TRACKING (from check-incomplete-work.py)
# ============================================================================

def get_current_project():
    """Get the current project name from the working directory name.

    Returns:
        str: Name of the current working directory.
    """
    cwd = Path.cwd()
    return cwd.name


def find_incomplete_markers(content):
    """Search text content for markers indicating incomplete work.

    Looks for TODO, PENDING, WIP, unchecked checkboxes, Next steps,
    Remaining, and Pending lines using regex patterns.

    Args:
        content (str): File or session text to scan.

    Returns:
        list[str]: List of matching lines indicating incomplete work.
    """
    incomplete_patterns = [
        r'(?:TODO|PENDING|IN PROGRESS|WIP|INCOMPLETE):\s*(.+)',
        r'Phase \d+/\d+.*(?:in progress|pending|not started)',
        r'Step \d+/\d+.*(?:in progress|pending|not started)',
        r'[PAUSE]️|[CYCLE]|[CROSS].*',
        r'\[ \].*',  # Unchecked checkboxes
        r'Next steps?:\s*(.+)',
        r'Remaining:\s*(.+)',
        r'Pending:\s*(.+)',
    ]

    incomplete_items = []

    for pattern in incomplete_patterns:
        matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
        for match in matches:
            line = match.group(0).strip()
            if line and len(line) > 10:
                incomplete_items.append(line)

    return incomplete_items


def check_project_summary(project):
    """Scan the project summary file for incomplete work sections.

    Args:
        project (str): Project name (subdirectory name in SESSIONS_DIR).

    Returns:
        dict: Contains 'file', 'sections' (list), and 'items' (list)
              if incomplete work is found, or None otherwise.
    """
    summary_file = SESSIONS_DIR / project / "project-summary.md"

    if not summary_file.exists():
        return None

    try:
        with open(summary_file, 'r', encoding='utf-8') as f:
            content = f.read()

        sections_to_check = [
            'Next Steps',
            'Pending Work',
            'TODO',
            'In Progress',
            'Remaining Tasks',
            'Current Work'
        ]

        incomplete_info = {
            'file': 'project-summary.md',
            'sections': [],
            'items': []
        }

        for section in sections_to_check:
            pattern = rf'#{1,3}\s*{section}.*?\n(.*?)(?=\n#{1,3}|\Z)'
            match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)

            if match:
                section_content = match.group(1).strip()
                if section_content and len(section_content) > 20:
                    incomplete_info['sections'].append({
                        'name': section,
                        'content': section_content[:500]
                    })

        incomplete_info['items'] = find_incomplete_markers(content)

        if incomplete_info['sections'] or len(incomplete_info['items']) > 2:
            return incomplete_info

        return None

    except (IOError, UnicodeDecodeError):
        return None


def check_recent_session(project):
    """Scan the most recent session file (within 3 days) for incomplete markers.

    Args:
        project (str): Project name (subdirectory name in SESSIONS_DIR).

    Returns:
        dict: Contains 'file', 'age_days', and 'items' (list) if recent
              incomplete work is found, or None if none found or session is old.
    """
    project_dir = SESSIONS_DIR / project

    if not project_dir.exists():
        return None

    session_files = sorted(project_dir.glob('session-*.md'), reverse=True)

    if not session_files:
        return None

    recent_session = session_files[0]

    try:
        mtime = datetime.fromtimestamp(recent_session.stat().st_mtime)
        now = datetime.now()
        days_ago = (now - mtime).days

        if days_ago > 3:
            return None

        with open(recent_session, 'r', encoding='utf-8') as f:
            content = f.read()

        incomplete_items = find_incomplete_markers(content)

        if len(incomplete_items) >= 2:
            return {
                'file': recent_session.name,
                'age_days': days_ago,
                'items': incomplete_items[:10]
            }

    except (IOError, UnicodeDecodeError, OSError):
        pass

    return None


def show_resume_prompt(project):
    """Print a formatted resume prompt if incomplete work is detected.

    Checks both the project summary and the most recent session file. If
    either has incomplete markers, prints a formatted welcome-back prompt.

    Args:
        project (str): Project name to check.

    Returns:
        bool: True if incomplete work was found, False otherwise.
    """
    print("[SEARCH] Checking for incomplete work...")
    print()

    summary_incomplete = check_project_summary(project)
    session_incomplete = check_recent_session(project)

    if not summary_incomplete and not session_incomplete:
        print("[CHECK] No incomplete work detected")
        print("   You can start fresh or continue with new tasks!")
        return False

    print("=" * 70)
    print("[U+1F44B] Welcome back!")
    print("=" * 70)
    print()
    print(f"[U+1F4C2] Project: {project}")
    print()

    if summary_incomplete:
        print("[CLIPBOARD] I found incomplete work in your project summary:")
        print()

        for section in summary_incomplete.get('sections', []):
            print(f"  [U+1F4CC] {section['name']}:")
            lines = section['content'].split('\n')[:7]
            for line in lines:
                if line.strip():
                    print(f"     {line.strip()}")
            if len(section['content'].split('\n')) > 7:
                print("     ...")
            print()

        items = summary_incomplete.get('items', [])
        if items:
            unique_items = list(set(items))[:8]
            if unique_items:
                print("  [U+1F516] Incomplete markers detected:")
                for item in unique_items:
                    item_clean = item.replace('[PAUSE]️', '').replace('[CYCLE]', '').strip()
                    if len(item_clean) > 10:
                        print(f"     - {item_clean}")
                print()

    if session_incomplete:
        age = session_incomplete.get('age_days', 0)
        age_str = "today" if age == 0 else f"{age} day{'s' if age > 1 else ''} ago"

        print(f"[U+1F4DD] Last session ({age_str}) had incomplete items:")
        print()

        for item in session_incomplete.get('items', [])[:7]:
            print(f"     - {item}")

        print()

    print("=" * 70)
    print("[BULB] Do you want to:")
    print("   1. Resume from where we stopped")
    print("   2. Start something new")
    print("=" * 70)
    print()
    print("Tip: I have full context from previous sessions in my memory!")

    return True


# ============================================================================
# LOGGING
# ============================================================================

def log_policy_hit(action, context=""):
    """Append a timestamped entry to the policy-hits log.

    Args:
        action (str): The action identifier (e.g., 'ENFORCE_START', 'VALIDATE').
        context (str): Optional human-readable context or detail string.
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = f"[{timestamp}] task-progress-tracking-policy | {action} | {context}\n"

    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(log_entry)


# ============================================================================
# POLICY INTERFACE
# ============================================================================

def validate():
    """Check that the task progress tracking policy preconditions are met.

    Returns:
        bool: True if validation succeeds, False on any exception.
    """
    try:
        SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
        log_policy_hit("VALIDATE", "progress-tracking-ready")
        return True
    except Exception as e:
        log_policy_hit("VALIDATE_ERROR", str(e))
        return False


def report():
    """Generate a compliance report for the task progress tracking policy.

    Returns:
        dict: Contains 'status', 'policy', 'projects_tracked', and 'timestamp'.
              Returns {'status': 'error', ...} on failure.
    """
    try:
        project_count = len([d for d in SESSIONS_DIR.iterdir() if d.is_dir()]) if SESSIONS_DIR.exists() else 0

        report_data = {
            "status": "success",
            "policy": "task-progress-tracking",
            "projects_tracked": project_count,
            "timestamp": datetime.now().isoformat()
        }

        log_policy_hit("REPORT", "task-progress-tracking-report-generated")
        return report_data
    except Exception as e:
        return {"status": "error", "message": str(e)}


def enforce():
    """Activate the task progress tracking policy.

    Consolidates progress tracking from check-incomplete-work.py:
    - Project summary analysis
    - Recent session checking
    - Incomplete work detection

    Returns:
        dict: Contains 'status' ('success' or 'error') and 'projects' count.
              On error, contains 'message'.
    """
    try:
        log_policy_hit("ENFORCE_START", "task-progress-tracking-enforcement")

        SESSIONS_DIR.mkdir(parents=True, exist_ok=True)

        project_count = len([d for d in SESSIONS_DIR.iterdir() if d.is_dir()]) if SESSIONS_DIR.exists() else 0

        log_policy_hit("ENFORCE_COMPLETE", f"progress-tracking-ready | projects={project_count}")
        print(f"[task-progress-tracking-policy] {project_count} projects being tracked")

        return {"status": "success", "projects": project_count}
    except Exception as e:
        log_policy_hit("ENFORCE_ERROR", str(e))
        print(f"[task-progress-tracking-policy] ERROR: {e}")
        return {"status": "error", "message": str(e)}


# ============================================================================
# CLI INTERFACE
# ============================================================================

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--enforce":
            result = enforce()
            sys.exit(0 if result.get("status") == "success" else 1)
        elif sys.argv[1] == "--validate":
            is_valid = validate()
            sys.exit(0 if is_valid else 1)
        elif sys.argv[1] == "--report":
            result = report()
            print(json.dumps(result, indent=2))
            sys.exit(0 if result.get("status") == "success" else 1)
        else:
            # Check for incomplete work on specified project
            project = sys.argv[1]
            has_incomplete = show_resume_prompt(project)
            sys.exit(1 if has_incomplete else 0)
    else:
        # Default: check current project
        project = get_current_project()
        has_incomplete = show_resume_prompt(project)
        sys.exit(1 if has_incomplete else 0)

#!/usr/bin/env python3
"""
Local CLAUDE.md Migration Script
Migrates local project CLAUDE.md files to session-based memory system
"""

import os
import sys
import shutil
from datetime import datetime
from pathlib import Path

def migrate_local_claude(project_dir=None):
    """Migrate local CLAUDE.md to session memory"""

    # Setup paths
    home = Path.home()
    memory_dir = home / ".claude" / "memory"
    sessions_dir = memory_dir / "sessions"
    log_file = memory_dir / "logs" / "policy-hits.log"

    # Get project directory
    if project_dir is None:
        project_dir = Path.cwd()
    else:
        project_dir = Path(project_dir)

    project_name = project_dir.name

    # Skip if this is the global .claude directory
    global_claude_dir = home / ".claude"
    if project_dir.resolve() == global_claude_dir.resolve():
        return

    # Check for local CLAUDE.md (case-insensitive)
    local_claude = None
    for filename in ["CLAUDE.md", "claude.md", ".claude/CLAUDE.md"]:
        candidate = project_dir / filename
        if candidate.exists():
            local_claude = candidate
            break

    # Exit if no local CLAUDE.md found
    if local_claude is None:
        return

    print(f"[Migration] Found local CLAUDE.md in project: {project_name}")

    # Create session directory
    session_dir = sessions_dir / project_name
    session_dir.mkdir(parents=True, exist_ok=True)
    (session_dir / "backups").mkdir(exist_ok=True)

    summary_file = session_dir / "project-summary.md"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Read local CLAUDE.md content
    with open(local_claude, 'r', encoding='utf-8') as f:
        local_content = f.read()

    # Create or update project-summary.md
    if summary_file.exists():
        print("[Migration] Merging with existing project-summary.md")

        # Create backup
        backup_name = f"{summary_file.name}.backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        shutil.copy2(summary_file, summary_file.parent / backup_name)

        # Append local content
        with open(summary_file, 'a', encoding='utf-8') as f:
            f.write(f"\n\n---\n\n")
            f.write(f"## Migrated Local Project Instructions\n\n")
            f.write(f"**Source:** Local CLAUDE.md (migrated on {timestamp})\n\n")
            f.write(local_content)
    else:
        print("[Migration] Creating new project-summary.md")

        # Create new project summary
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(f"# Project Memory: {project_name}\n\n")
            f.write(f"**Last Updated:** {timestamp}\n")
            f.write(f"**Status:** Active\n\n")
            f.write(f"---\n\n")
            f.write(f"## Project-Specific Instructions\n\n")
            f.write(f"**Source:** Local CLAUDE.md (migrated on {timestamp})\n\n")
            f.write(local_content)
            f.write(f"\n\n---\n\n")
            f.write(f"## Session History\n\n")
            f.write(f"This section will be automatically updated as you work on this project.\n\n")

    # Create backup of local CLAUDE.md
    backup_file = session_dir / "backups" / f"CLAUDE.md.backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    shutil.copy2(local_claude, backup_file)

    # Delete local CLAUDE.md
    local_claude.unlink()

    # Log migration
    log_file.parent.mkdir(parents=True, exist_ok=True)
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"[{timestamp}] local-claude-migration | migrated | {project_name} | source: {local_claude}\n")

    print("[OK] Migration complete!")
    print(f"   -> Migrated to: {summary_file}")
    print(f"   -> Backup: {backup_file}")
    print(f"   -> Deleted local CLAUDE.md")
    print()
    print("[SUCCESS] Global policies will now work properly!")


if __name__ == "__main__":
    project_path = sys.argv[1] if len(sys.argv) > 1 else None
    try:
        migrate_local_claude(project_path)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

#!/usr/bin/env python3
"""
Release Automation - Bump version, update changelog, sync, and tag.

Usage:
    python scripts/release.py patch          # 7.5.0 -> 7.5.1
    python scripts/release.py minor          # 7.5.0 -> 7.6.0
    python scripts/release.py major          # 7.5.0 -> 8.0.0
    python scripts/release.py --dry-run patch  # Preview without changes

Steps:
    1. Read current version from VERSION file
    2. Bump major/minor/patch
    3. Write new VERSION
    4. Run sync-version.py to propagate to README, CLAUDE.md, etc.
    5. Add CHANGELOG.md entry
    6. Print git tag command (user runs manually)

Windows-safe: ASCII only (cp1252 compatible).
"""

import subprocess
import sys
from datetime import datetime
from pathlib import Path

# scripts/tools/release.py -> scripts/tools -> scripts -> repo root. Was
# parent.parent, which resolved to scripts/ and made VERSION_FILE and
# CHANGELOG_FILE point at files that do not exist there.
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
VERSION_FILE = PROJECT_ROOT / "VERSION"
CHANGELOG_FILE = PROJECT_ROOT / "CHANGELOG.md"
SYNC_SCRIPT = Path(__file__).resolve().parent / "sync-version.py"


def read_version():
    """Read current version from VERSION file."""
    if not VERSION_FILE.exists():
        print("[ERROR] VERSION file not found: %s" % VERSION_FILE)
        sys.exit(1)
    return VERSION_FILE.read_text(encoding="utf-8").strip()


def bump_version(current, bump_type):
    """Bump version string by type (major/minor/patch)."""
    parts = current.split(".")
    if len(parts) != 3:
        print("[ERROR] Invalid version format: %s (expected X.Y.Z)" % current)
        sys.exit(1)

    major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])

    if bump_type == "major":
        major += 1
        minor = 0
        patch = 0
    elif bump_type == "minor":
        minor += 1
        patch = 0
    elif bump_type == "patch":
        patch += 1
    else:
        print("[ERROR] Unknown bump type: %s (use major/minor/patch)" % bump_type)
        sys.exit(1)

    return "%d.%d.%d" % (major, minor, patch)


def update_changelog(old_version, new_version):
    """Add release entry to CHANGELOG.md."""
    today = datetime.now().strftime("%Y-%m-%d")

    entry = "\n## [%s] - %s\n\n" % (new_version, today)
    entry += "### Changed\n\n"
    entry += "- Bumped from %s to %s\n" % (old_version, new_version)

    if CHANGELOG_FILE.is_file():
        existing = CHANGELOG_FILE.read_text(encoding="utf-8", errors="replace")
        # Insert after the first heading
        insert_pos = existing.find("\n## ")
        if insert_pos >= 0:
            new_content = existing[:insert_pos] + entry + existing[insert_pos:]
        else:
            new_content = existing + "\n" + entry
        CHANGELOG_FILE.write_text(new_content, encoding="utf-8")
    else:
        header = "# Changelog\n\n"
        header += "All notable changes to this project will be "
        header += "documented in this file.\n"
        CHANGELOG_FILE.write_text(header + entry, encoding="utf-8")

    print("[OK] CHANGELOG.md updated with %s entry" % new_version)


def sync_version(new_version):
    """Run sync-version.py to propagate version to all files."""
    if not SYNC_SCRIPT.exists():
        print("[WARN] sync-version.py not found, skipping sync")
        return

    try:
        result = subprocess.run(
            [sys.executable, str(SYNC_SCRIPT), new_version],
            timeout=30,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            print("[OK] Version synced to all project files")
        else:
            print("[WARN] sync-version.py returned code %d" % result.returncode)
            if result.stderr:
                print("  stderr: %s" % result.stderr[:200])
    except Exception as e:
        print("[WARN] sync-version.py failed: %s" % str(e))


def main():
    """Entry point for release automation."""
    dry_run = "--dry-run" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("--")]

    if not args:
        print("Usage: python scripts/release.py [--dry-run] <major|minor|patch>")
        print("")
        current = read_version()
        print("Current version: %s" % current)
        print("  patch -> %s" % bump_version(current, "patch"))
        print("  minor -> %s" % bump_version(current, "minor"))
        print("  major -> %s" % bump_version(current, "major"))
        sys.exit(0)

    bump_type = args[0].lower()
    current = read_version()
    new_version = bump_version(current, bump_type)

    print("")
    print("Release: %s -> %s (%s bump)" % (current, new_version, bump_type))
    print("")

    if dry_run:
        print("[DRY RUN] No changes made")
        print("  Would update: VERSION, CHANGELOG.md")
        print("  Would sync: README.md, CLAUDE.md, SRS.md")
        print("  Would suggest: git tag v%s" % new_version)
        return

    # 1. Write new version
    VERSION_FILE.write_text(new_version + "\n", encoding="utf-8")
    print("[OK] VERSION updated: %s -> %s" % (current, new_version))

    # 2. Sync to all files
    sync_version(new_version)

    # 3. Update changelog
    update_changelog(current, new_version)

    # 4. Print next steps
    print("")
    print("Next steps:")
    print("  git add VERSION CHANGELOG.md README.md CLAUDE.md")
    print("  git commit -m 'bump: v%s -> v%s'" % (current, new_version))
    print("  git tag v%s" % new_version)
    print("  git push && git push --tags")


if __name__ == "__main__":
    main()

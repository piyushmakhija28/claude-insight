#!/usr/bin/env python3
"""
Version Sync - Single source of truth from VERSION file.

Reads the VERSION file and propagates it to every place the version is written
by hand:

- README.md                      (**Version:** X.Y.Z + **Last Updated:**)
- CLAUDE.md                      (**Version:** X.Y.Z + **Last Updated:**)
- SRS.md                         (**Version:** X.Y.Z + **Date:** / **Last Updated:**)
- langgraph_engine/__init__.py    (__version__ = "X.Y.Z")
- setup.py                       (reads VERSION dynamically, nothing to do)

Usage:
    python scripts/tools/sync-version.py            # propagate current VERSION
    python scripts/tools/sync-version.py 1.21.0     # set VERSION, then propagate
    python scripts/tools/sync-version.py --dry-run  # report without writing

Windows-safe: ASCII only (cp1252 compatible).
"""

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path

# scripts/tools/sync-version.py -> scripts/tools -> scripts -> repo root.
# This was previously parent.parent, which resolved to scripts/ and made every
# target path wrong: VERSION_FILE pointed at scripts/VERSION (so the real root
# VERSION was never read or written, and a stray scripts/VERSION got created)
# while each markdown target reported "[SKIP] not found". The script therefore
# reported success on every run while propagating nothing.
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
VERSION_FILE = PROJECT_ROOT / "VERSION"
TODAY = datetime.now().strftime("%Y-%m-%d")

SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")

_VERSION_LINE = (r"\*\*Version:\*\*\s*[\d.]+", "**Version:** {version}")
_LAST_UPDATED = (r"\*\*Last Updated:\*\*\s*\d{4}-\d{2}-\d{2}", "**Last Updated:** " + TODAY)
_DATE_LINE = (r"\*\*Date:\*\*\s*\d{4}-\d{2}-\d{2}", "**Date:** " + TODAY)

TARGETS = [
    {"file": PROJECT_ROOT / "README.md", "patterns": [_VERSION_LINE, _LAST_UPDATED]},
    {"file": PROJECT_ROOT / "CLAUDE.md", "patterns": [_VERSION_LINE, _LAST_UPDATED]},
    {"file": PROJECT_ROOT / "SRS.md", "patterns": [_VERSION_LINE, _DATE_LINE, _LAST_UPDATED]},
    {
        "file": PROJECT_ROOT / "langgraph_engine" / "__init__.py",
        "patterns": [(r'__version__\s*=\s*["\'][\d.]+["\']', '__version__ = "{version}"')],
    },
]


def read_text_preserving(path):
    """Read a file as text without normalizing its line terminators.

    Returns:
        str: File contents, CR characters intact.
    """
    return path.read_bytes().decode("utf-8")


def write_text_preserving(path, content):
    """Write text without translating line terminators.

    ``Path.write_text`` opens in text mode, which on Windows rewrites every
    ``\\n`` as ``\\r\\n``. Since these targets are committed LF, using it turned
    a two-line version bump into a whole-file diff. Writing bytes leaves the
    terminators exactly as the regex substitutions left them.

    Args:
        path: Destination file.
        content: Full text to write.
    """
    path.write_bytes(content.encode("utf-8"))


def read_version():
    """Read the current version from the VERSION file.

    Returns:
        str: Version string, or "0.0.0" when the file is absent.
    """
    if VERSION_FILE.exists():
        return read_text_preserving(VERSION_FILE).strip()
    return "0.0.0"


def set_version(new_version):
    """Write a validated version to the VERSION file.

    Args:
        new_version: Semver string to write.

    Returns:
        bool: True when written.
    """
    VERSION_FILE.write_bytes((new_version + "\n").encode("utf-8"))
    print("[VERSION] Set VERSION file to %s" % new_version)
    return True


def sync_file(filepath, patterns, version, dry_run=False):
    """Update version references in one file.

    Args:
        filepath: File to update.
        patterns: List of (regex, replacement) pairs; ``{version}`` is expanded.
        version: Version string to write in.
        dry_run: When True, report without writing.

    Returns:
        bool: True when the file changed (or would change).
    """
    content = read_text_preserving(filepath)
    original = content
    changes = 0

    for pattern, replacement in patterns:
        repl = replacement.replace("{version}", version)
        new_content = re.sub(pattern, repl, content)
        if new_content != content:
            changes += 1
        content = new_content

    if content == original:
        print("[OK] %s already up to date" % filepath.name)
        return False

    if dry_run:
        print("[DRY-RUN] %s would change (%d replacement(s))" % (filepath.name, changes))
        return True

    write_text_preserving(filepath, content)
    print("[UPDATED] %s (%d replacement(s))" % (filepath.name, changes))
    return True


def main():
    """Propagate the VERSION file to every hand-written version reference.

    Returns:
        int: Process exit code. Non-zero on an invalid version argument or a
            missing target file.
    """
    parser = argparse.ArgumentParser(
        description="Propagate the VERSION file to every hand-written version reference.",
    )
    parser.add_argument(
        "version",
        nargs="?",
        help="new version to write to VERSION first (MAJOR.MINOR.PATCH); omit to propagate the current one",
    )
    parser.add_argument("--dry-run", action="store_true", help="report what would change without writing")
    args = parser.parse_args()

    # Without validation any argument was written straight into VERSION, so a
    # typo or a stray flag became the project version. rules/11 requires a bare
    # semver line, so anything else is rejected before a single file is touched.
    if args.version is not None:
        candidate = args.version.strip()
        if not SEMVER_RE.match(candidate):
            print("[ERROR] Not a valid version: %r" % args.version, file=sys.stderr)
            print("        Expected MAJOR.MINOR.PATCH, e.g. 1.21.0", file=sys.stderr)
            return 2
        if args.dry_run:
            print("[DRY-RUN] Would set VERSION file to %s" % candidate)
        else:
            set_version(candidate)

    version = read_version()
    if not SEMVER_RE.match(version):
        print("[ERROR] VERSION file does not contain a valid semver: %r" % version, file=sys.stderr)
        return 2

    print("\n=== Version Sync: %s (%s)%s ===\n" % (version, TODAY, " [dry-run]" if args.dry_run else ""))

    # A target that cannot be found used to print "[SKIP] not found" and still
    # exit 0. With the root resolved correctly a missing target means the repo
    # layout moved, which is a real problem worth failing on.
    missing = [str(t["file"].relative_to(PROJECT_ROOT)) for t in TARGETS if not t["file"].exists()]

    updated = 0
    for target in TARGETS:
        if not target["file"].exists():
            print("[MISSING] %s" % target["file"].relative_to(PROJECT_ROOT))
            continue
        if sync_file(target["file"], target["patterns"], version, dry_run=args.dry_run):
            updated += 1

    print("[OK] setup.py reads VERSION dynamically")
    print("\n=== Done: %d file(s) updated, version %s ===\n" % (updated, version))

    if missing:
        print("[ERROR] %d target(s) missing: %s" % (len(missing), ", ".join(missing)), file=sys.stderr)
        print("        Update TARGETS in this script to match the current layout.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

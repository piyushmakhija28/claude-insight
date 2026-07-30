#!/usr/bin/env python
"""Consolidate historical session directories onto one root and one ID format.

Before ``hooks/session_context.py`` became the single authority for session
identity, session state was written to two different roots by two different ID
generators:

  ~/.claude/memory/logs/sessions/SESSION-<ts>-<suffix>   (pipeline, hooks)
  ~/.claude/memory/logs/sessions/session-<ts>-<hex>      (engine)
  ~/.claude/logs/sessions/...                            (engine import fallback)
  ~/.claude/memory/logs/sessions/unknown/                (resolver miss fallback)

This script normalizes every directory name to the canonical ``SESSION-`` form
and moves everything under the canonical root. Nothing is deleted: a directory
that cannot be normalized cleanly, or whose canonical name is already taken by
different content, is moved into a timestamped archive folder instead.

Usage:
    python scripts/tools/migrate_session_dirs.py            # dry run, report only
    python scripts/tools/migrate_session_dirs.py --apply    # perform the moves

Windows-safe: ASCII only, no Unicode characters.
"""

import argparse
import shutil
import sys
from datetime import datetime
from pathlib import Path

_HOOKS_DIR = str(Path(__file__).resolve().parent.parent.parent / "hooks")
if _HOOKS_DIR not in sys.path:
    sys.path.insert(0, _HOOKS_DIR)

from session_context import get_memory_base, get_sessions_root, normalize_session_id  # noqa: E402

ARCHIVE_DIRNAME = "_archive"
UNRESOLVED_NAMES = {"unknown", "", "_unresolved"}


def get_legacy_roots():
    """Return session roots that predate the single-root rule.

    Returns:
        list[Path]: Roots to drain into the canonical root, canonical excluded.
    """
    canonical = get_sessions_root()
    candidates = [
        get_memory_base().parent / "logs" / "sessions",
        Path.home() / ".claude" / "logs" / "sessions",
    ]
    roots = []
    for candidate in candidates:
        if candidate.resolve() == canonical.resolve():
            continue
        if candidate.is_dir() and candidate not in roots:
            roots.append(candidate)
    return roots


def _is_empty_dir(path):
    """Return True when a directory holds no entries at all.

    Args:
        path: Directory to inspect.

    Returns:
        bool: True when the directory exists and is empty.
    """
    try:
        next(path.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False


def _recase_dir(source, canonical_name):
    """Rename a directory to fix only the casing of its name.

    A direct rename to a name that differs only by case is a no-op (or an error)
    on a case-insensitive filesystem, so the rename goes through a temporary
    name first.

    Args:
        source: Directory whose name has the wrong casing.
        canonical_name: Target directory name.

    Returns:
        None
    """
    staging = source.with_name(canonical_name + ".recase-tmp")
    if staging.exists():
        shutil.rmtree(str(staging))
    source.rename(staging)
    staging.rename(source.with_name(canonical_name))


def _merge_into(source, target):
    """Move every entry from source into target without overwriting.

    Args:
        source: Directory whose contents are moved.
        target: Existing directory that receives the contents.

    Returns:
        tuple[int, int]: Count of entries moved and entries skipped as conflicts.
    """
    moved = 0
    skipped = 0
    for entry in list(source.iterdir()):
        destination = target / entry.name
        if destination.exists():
            skipped += 1
            continue
        shutil.move(str(entry), str(destination))
        moved += 1
    return moved, skipped


def plan_migration():
    """Build the list of actions needed to reach one root and one ID format.

    Returns:
        dict: Keys ``rename``, ``recase``, ``merge``, ``archive``, ``keep``,
            ``stats``.
    """
    canonical_root = get_sessions_root()
    plan = {"rename": [], "recase": [], "merge": [], "archive": [], "keep": [], "stats": {}}
    corrupt_files = 0
    lock_files = 0

    roots = [canonical_root] + get_legacy_roots()
    seen_targets = set()

    for root in roots:
        if not root.is_dir():
            continue
        for entry in sorted(root.iterdir()):
            if not entry.is_dir():
                continue
            if entry.name in (ARCHIVE_DIRNAME, "_unresolved"):
                continue

            corrupt_files += len(list(entry.glob("flow-trace.corrupt-*")))
            lock_files += len(list(entry.glob("*.lock")))

            canonical_name = "" if entry.name in UNRESOLVED_NAMES else normalize_session_id(entry.name)

            if not canonical_name:
                plan["archive"].append((entry, "unresolvable session name"))
                continue

            target = canonical_root / canonical_name

            if target == entry:
                # Path equality is case-insensitive on Windows, so a lowercase
                # engine-format directory compares equal to its canonical name
                # and is already the same directory on disk. The stored casing
                # still needs fixing: on a case-sensitive filesystem (Linux CI,
                # a copied backup) the two names are different directories.
                if entry.name != canonical_name:
                    plan["recase"].append((entry, canonical_name))
                else:
                    plan["keep"].append(entry)
                seen_targets.add(target)
                continue

            if target.exists() or target in seen_targets:
                if _is_empty_dir(entry):
                    plan["archive"].append((entry, "empty duplicate of " + canonical_name))
                else:
                    plan["merge"].append((entry, target))
                continue

            plan["rename"].append((entry, target))
            seen_targets.add(target)

    plan["stats"] = {
        "roots_scanned": len([r for r in roots if r.is_dir()]),
        "canonical_root": str(canonical_root),
        "legacy_roots": [str(r) for r in get_legacy_roots()],
        "corrupt_archives_found": corrupt_files,
        "lock_files_found": lock_files,
    }
    return plan


def apply_migration(plan, archive_root):
    """Execute a migration plan.

    Args:
        plan: Plan produced by :func:`plan_migration`.
        archive_root: Directory that receives everything not cleanly normalized.

    Returns:
        dict: Counts of applied, merged, archived, and failed actions.
    """
    result = {"renamed": 0, "recased": 0, "merged": 0, "merge_conflicts": 0, "archived": 0, "failed": 0}

    for source, canonical_name in plan["recase"]:
        try:
            _recase_dir(source, canonical_name)
            result["recased"] += 1
        except Exception as exc:
            print("  FAILED recase {}: {}".format(source.name, exc))
            result["failed"] += 1

    for source, target in plan["rename"]:
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source), str(target))
            result["renamed"] += 1
        except Exception as exc:
            print("  FAILED rename {}: {}".format(source.name, exc))
            result["failed"] += 1

    for source, target in plan["merge"]:
        try:
            target.mkdir(parents=True, exist_ok=True)
            moved, skipped = _merge_into(source, target)
            result["merged"] += moved
            result["merge_conflicts"] += skipped
            if _is_empty_dir(source):
                source.rmdir()
            else:
                archive_root.mkdir(parents=True, exist_ok=True)
                shutil.move(str(source), str(archive_root / (source.parent.name + "__" + source.name)))
                result["archived"] += 1
        except Exception as exc:
            print("  FAILED merge {}: {}".format(source.name, exc))
            result["failed"] += 1

    for source, reason in plan["archive"]:
        try:
            archive_root.mkdir(parents=True, exist_ok=True)
            destination = archive_root / (source.parent.name + "__" + source.name)
            if destination.exists():
                destination = archive_root / (source.parent.name + "__" + source.name + "__dup")
            shutil.move(str(source), str(destination))
            result["archived"] += 1
        except Exception as exc:
            print("  FAILED archive {} ({}): {}".format(source.name, reason, exc))
            result["failed"] += 1

    return result


def main():
    """Report or apply the session-directory migration.

    Returns:
        int: Process exit code.
    """
    parser = argparse.ArgumentParser(description="Consolidate session directories onto one root and ID format.")
    parser.add_argument("--apply", action="store_true", help="perform the moves (default is a dry run)")
    args = parser.parse_args()

    plan = plan_migration()
    stats = plan["stats"]

    print("Session directory migration")
    print("  canonical root : " + stats["canonical_root"])
    for legacy in stats["legacy_roots"]:
        print("  legacy root    : " + legacy)
    print("")
    print("  already canonical      : {}".format(len(plan["keep"])))
    print("  to fix casing only     : {}".format(len(plan["recase"])))
    print("  to rename              : {}".format(len(plan["rename"])))
    print("  to merge into existing  : {}".format(len(plan["merge"])))
    print("  to archive              : {}".format(len(plan["archive"])))
    print("  corrupt flow-trace files: {}".format(stats["corrupt_archives_found"]))
    print("  stale lock files        : {}".format(stats["lock_files_found"]))
    print("")

    for source, target in plan["rename"][:5]:
        print("  rename  {}  ->  {}".format(source.name, target.name))
    if len(plan["rename"]) > 5:
        print("  ... and {} more renames".format(len(plan["rename"]) - 5))
    for source, target in plan["merge"][:5]:
        print("  merge   {}  ->  {}".format(source.name, target.name))
    if len(plan["merge"]) > 5:
        print("  ... and {} more merges".format(len(plan["merge"]) - 5))
    for source, reason in plan["archive"][:5]:
        print("  archive {}  ({})".format(source.name, reason))
    if len(plan["archive"]) > 5:
        print("  ... and {} more archives".format(len(plan["archive"]) - 5))

    if not args.apply:
        print("")
        print("Dry run only. Re-run with --apply to perform these moves.")
        return 0

    archive_root = get_sessions_root() / ARCHIVE_DIRNAME / datetime.now().strftime("%Y%m%d-%H%M%S")
    print("")
    print("Applying. Archive target: " + str(archive_root))
    result = apply_migration(plan, archive_root)
    print("")
    print("  recased         : {}".format(result["recased"]))
    print("  renamed         : {}".format(result["renamed"]))
    print("  files merged    : {}".format(result["merged"]))
    print("  merge conflicts : {} (left in archived source)".format(result["merge_conflicts"]))
    print("  archived dirs   : {}".format(result["archived"]))
    print("  failed          : {}".format(result["failed"]))
    return 1 if result["failed"] else 0


if __name__ == "__main__":
    sys.exit(main())

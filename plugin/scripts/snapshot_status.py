"""Staleness check for the plugin's pinned library snapshot (SRS FR-29, ADR-007).

WHY THIS LIVES IN THE PLUGIN AND IMPORTS NOTHING FROM THE ENGINE
----------------------------------------------------------------
This check has to run where the snapshot actually is: inside an installed
plugin, under the plugin manager's cache directory, on a machine that may have
no ``claude-workflow-engine`` checkout and no ``claude-global-library`` checkout
at all. V2-016 established that an installed plugin gets ``ModuleNotFoundError``
for every import back into the engine repository, so this module imports only
the standard library. ``scripts/build_library_snapshot.py`` is the engine-side
builder and is deliberately NOT imported here for the same reason.

The snapshot root is resolved from ``${CLAUDE_PLUGIN_ROOT}``, never from the
current working directory. A CWD-relative path resolves correctly during local
development purely because the author happens to be running from the plugin's
own directory, and then fails for essentially every installed user, whose
working directory is some unrelated project.

WHAT "FIRES" MEANS, AND WHAT DELIBERATELY DOES NOT FIRE
-------------------------------------------------------
The check compares the library VERSION pinned into the snapshot at build time
against a live library checkout, and reports BEHIND or AHEAD when they differ.

It reports NO_LIBRARY, and does NOT fire, when no library checkout is present.
That is the normal condition on an end user's machine and it is the entire point
of the snapshot: a plugin that works with no library must not warn about the
absence of a library on every invocation. A staleness check that fires
unconditionally is noise, and a gate that always fails gets switched off.

Windows-safe: ASCII only. Paths are built with pathlib, never with separator
literals.
"""

import argparse
import json
import os
import sys
from pathlib import Path

PLUGIN_ROOT_ENV = "CLAUDE_PLUGIN_ROOT"
LIBRARY_ENV = "CLAUDE_GLOBAL_LIBRARY"
LIBRARY_DIR_NAME = "claude-global-library"
SNAPSHOT_DIR_NAME = "snapshot"
MANIFEST_NAME = "snapshot.json"

STATUS_CURRENT = "current"
STATUS_BEHIND = "behind"
STATUS_AHEAD = "ahead"
STATUS_NO_LIBRARY = "no_library"
STATUS_NO_SNAPSHOT = "no_snapshot"
STATUS_UNREADABLE = "unreadable"

FIRING_STATUSES = frozenset({STATUS_BEHIND, STATUS_AHEAD, STATUS_NO_SNAPSHOT, STATUS_UNREADABLE})


class SnapshotStatus(object):
    """Outcome of one staleness check.

    Attributes:
        status: One of the module-level STATUS_ constants.
        snapshot_version: Library version pinned into the snapshot, or "".
        library_version: Live library version, or "" when none was found.
        detail: Human-readable explanation.
    """

    def __init__(self, status, snapshot_version="", library_version="", detail=""):
        """Store the outcome fields."""
        self.status = status
        self.snapshot_version = snapshot_version
        self.library_version = library_version
        self.detail = detail

    @property
    def fires(self):
        """Return True when this outcome should be surfaced to the user."""
        return self.status in FIRING_STATUSES

    @property
    def is_stale(self):
        """Return True only for a genuine version divergence."""
        return self.status in (STATUS_BEHIND, STATUS_AHEAD)

    def as_dict(self):
        """Return the outcome as a plain dictionary."""
        return {
            "status": self.status,
            "fires": self.fires,
            "is_stale": self.is_stale,
            "snapshot_version": self.snapshot_version,
            "library_version": self.library_version,
            "detail": self.detail,
        }

    def __repr__(self):
        """Return a debug representation."""
        return "SnapshotStatus({0!r}, snapshot={1!r}, library={2!r})".format(
            self.status, self.snapshot_version, self.library_version
        )


def find_plugin_root(start=None):
    """Resolve the plugin root.

    Args:
        start: Explicit path that wins when given.

    Returns:
        Path: The resolved plugin root.

    Raises:
        RuntimeError: When the root cannot be located.
    """
    if start:
        return Path(start).resolve()
    from_env = os.environ.get(PLUGIN_ROOT_ENV, "").strip()
    if from_env and Path(from_env).is_dir():
        return Path(from_env).resolve()
    here = Path(__file__).resolve().parent.parent
    if (here / ".claude-plugin").is_dir():
        return here
    raise RuntimeError(
        "cannot locate the plugin root: {0} is unset or wrong, and {1} carries "
        "no .claude-plugin directory".format(PLUGIN_ROOT_ENV, here)
    )


def snapshot_root_for(plugin_root):
    """Return the snapshot directory inside a plugin root."""
    return Path(plugin_root) / SNAPSHOT_DIR_NAME


def read_manifest(snapshot_root):
    """Read the snapshot manifest.

    Args:
        snapshot_root: Path of the snapshot directory.

    Returns:
        dict: The parsed manifest, or None when absent or unreadable.
    """
    path = Path(snapshot_root) / MANIFEST_NAME
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return payload if isinstance(payload, dict) else None


def locate_library_root(explicit=None, search_from=None):
    """Locate a live library checkout, if one exists on this machine.

    Absence is an ordinary, expected result here, so this returns None rather
    than raising: on an end user's machine there is no library, and that is the
    condition the snapshot exists to serve.

    Args:
        explicit: Caller-supplied path that wins when given.
        search_from: Directory whose siblings are searched.

    Returns:
        Path or None.
    """
    candidates = []
    if explicit:
        candidates.append(Path(explicit))
    from_env = os.environ.get(LIBRARY_ENV, "").strip()
    if from_env:
        candidates.append(Path(from_env))
    if search_from:
        candidates.append(Path(search_from).parent / LIBRARY_DIR_NAME)
    for candidate in candidates:
        if (candidate / "VERSION").is_file():
            return candidate.resolve()
    return None


def read_version_file(library_root):
    """Read a library checkout's VERSION file.

    Args:
        library_root: Path of the library checkout.

    Returns:
        str: The stripped version, or "" when unreadable.
    """
    try:
        return (Path(library_root) / "VERSION").read_text(encoding="utf-8").strip()
    except OSError:
        return ""


def parse_semver(value):
    """Parse a version string into a comparable tuple.

    Args:
        value: Version string such as "29.73.0".

    Returns:
        tuple or None: Numeric components, or None when unparseable.
    """
    if not isinstance(value, str):
        return None
    parts = value.strip().split(".")
    numbers = []
    for part in parts:
        head = part.split("-", 1)[0].split("+", 1)[0]
        if not head.isdigit():
            return None
        numbers.append(int(head))
    return tuple(numbers) if numbers else None


def compare_versions(snapshot_version, library_version):
    """Compare two version strings.

    Args:
        snapshot_version: Version pinned into the snapshot.
        library_version: Version of the live library.

    Returns:
        str: STATUS_CURRENT, STATUS_BEHIND or STATUS_AHEAD.
    """
    if snapshot_version == library_version:
        return STATUS_CURRENT
    left = parse_semver(snapshot_version)
    right = parse_semver(library_version)
    if left is None or right is None:
        return STATUS_BEHIND
    if left == right:
        return STATUS_CURRENT
    return STATUS_BEHIND if left < right else STATUS_AHEAD


def check_snapshot(plugin_root=None, library_root=None):
    """Check the pinned snapshot against a live library checkout.

    Args:
        plugin_root: Plugin root. Resolved from the environment when omitted.
        library_root: Library checkout. Searched for when omitted.

    Returns:
        SnapshotStatus: The outcome.
    """
    root = find_plugin_root(plugin_root)
    snapshot_root = snapshot_root_for(root)

    if not snapshot_root.is_dir():
        return SnapshotStatus(
            STATUS_NO_SNAPSHOT,
            detail=(
                "no snapshot at {0}. The plugin cannot resolve agents or skills "
                "without it. Build one with: python scripts/build_library_snapshot.py".format(snapshot_root)
            ),
        )

    manifest = read_manifest(snapshot_root)
    if manifest is None:
        return SnapshotStatus(
            STATUS_UNREADABLE,
            detail="snapshot manifest at {0} is missing or not valid JSON".format(snapshot_root / MANIFEST_NAME),
        )

    pinned = manifest.get("library_version") or ""
    if not isinstance(pinned, str) or not pinned:
        return SnapshotStatus(
            STATUS_UNREADABLE,
            detail="snapshot manifest records no library_version",
        )

    found = locate_library_root(library_root, search_from=root)
    if found is None:
        return SnapshotStatus(
            STATUS_NO_LIBRARY,
            snapshot_version=pinned,
            detail=(
                "no {0} checkout on this machine, so there is nothing to compare "
                "against. This is the expected condition for an installed plugin: "
                "the snapshot pinned at library {1} is what the plugin runs "
                "on.".format(LIBRARY_DIR_NAME, pinned)
            ),
        )

    live = read_version_file(found)
    if not live:
        return SnapshotStatus(
            STATUS_UNREADABLE,
            snapshot_version=pinned,
            detail="found a library at {0} but its VERSION file is unreadable".format(found),
        )

    status = compare_versions(pinned, live)
    if status == STATUS_CURRENT:
        detail = "snapshot is current: pinned and live library are both {0}".format(pinned)
    elif status == STATUS_BEHIND:
        detail = (
            "snapshot is BEHIND the library: pinned {0}, live {1} at {2}. Rebuild "
            "with: python scripts/build_library_snapshot.py".format(pinned, live, found)
        )
    else:
        detail = (
            "snapshot is AHEAD of the library: pinned {0}, live {1} at {2}. The "
            "checkout is older than the snapshot was built from.".format(pinned, live, found)
        )
    return SnapshotStatus(status, snapshot_version=pinned, library_version=live, detail=detail)


def _parse_args(argv):
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Report whether the pinned library snapshot is stale.")
    parser.add_argument("--plugin-root", default=None, help="Plugin root. Defaults to $CLAUDE_PLUGIN_ROOT.")
    parser.add_argument("--library", default=None, help="Library checkout to compare against.")
    parser.add_argument("--json", action="store_true", help="Emit the outcome as JSON.")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero when the check fires.")
    return parser.parse_args(argv)


def main(argv=None):
    """Entry point.

    Returns:
        int: 0, or 1 under --strict when the check fires.
    """
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    try:
        outcome = check_snapshot(args.plugin_root, args.library)
    except RuntimeError as exc:
        print("[FAIL] {0}".format(exc))
        return 1

    if args.json:
        print(json.dumps(outcome.as_dict(), indent=2, sort_keys=True))
    else:
        label = "STALE" if outcome.is_stale else outcome.status.upper()
        print("[{0}] {1}".format(label, outcome.detail))

    return 1 if (args.strict and outcome.fires) else 0


if __name__ == "__main__":
    sys.exit(main())

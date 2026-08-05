"""Remove named hook registrations from a Claude Code settings file (PRD FR-4 / SRS FR-13).

WHAT THIS IS FOR
----------------
V2-027 deletes the ``PreToolUse``, ``PostToolUse`` and ``UserPromptSubmit``
registrations from the user-scope settings file. That file is a live machine
configuration: a change takes effect on the next prompt its owner types. Editing
it by hand is a single-keystroke distance from destroying an unrelated block, so
the removal is expressed as a tool that states exactly what it will touch,
proves what it did not touch, and can be re-run without further effect.

WHY IT REUSES ``settings_store`` RATHER THAN WRITING JSON ITSELF
---------------------------------------------------------------
``plugin/scripts/settings_store.merge_write`` already solves the three problems
this write has: it REFUSES when an existing file does not parse, rather than
substituting a default over the owner's real configuration; it merges against a
read taken moments before the rename, so a competing writer is detected rather
than silently lost; and it mirrors the file's existing newline style and
trailing byte so the diff is the change that was asked for. Re-implementing any
of that here would be a second, less-tested copy of the same logic.

THE RETENTION PROOF IS THE POINT, NOT A COURTESY
------------------------------------------------
Issue #288 requires ``Stop`` and ``Notification`` to survive this operation
unchanged, and ``Stop`` in particular is a hook whose behaviour is under active
review. Asserting that those names are still PRESENT afterwards would pass even
if their commands, timeouts or shells had been rewritten. This tool therefore
canonicalises every retained hook entry to sorted-key JSON before and after the
write and compares the resulting bytes. A retained hook that changed at all
fails the run and is reported per hook.

IDEMPOTENCE
-----------
Removing a hook that is already absent is a no-op that reports ``ABSENT`` and
exits zero. Re-running after a successful removal writes nothing, because the
merge produces content identical to what is on disk and ``merge_write`` returns
without replacing the file.

Windows-safe: ASCII only, no Unicode characters.
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "plugin" / "scripts"))

from settings_store import (  # noqa: E402
    ConcurrentModification,
    SettingsUnreadable,
    SettingsWriteError,
    merge_write,
    sha256_of,
)

FR4_HOOKS = ("PreToolUse", "PostToolUse", "UserPromptSubmit")
RETAINED_HOOKS = ("Stop", "Notification")

EXIT_OK = 0
EXIT_FAILED = 1


class RetainedHookAltered(Exception):
    """A hook that was required to survive unchanged did not."""


def default_settings_path():
    """Return the user-scope settings path this tool targets by default.

    Returns:
        Path: The standard user-scope settings location.
    """
    return Path.home() / ".claude" / "settings.json"


def canonical(value):
    """Serialise a settings fragment to stable, comparable text.

    Sorted keys and no insignificant whitespace, so the comparison is about the
    fragment's content and not about how a serialiser happened to lay it out.

    Args:
        value: Any JSON-serialisable fragment.

    Returns:
        str: Canonical JSON rendering.
    """
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest_of(value):
    """Return the sha256 of a fragment's canonical rendering.

    Args:
        value: Any JSON-serialisable fragment.

    Returns:
        str: Hex digest.
    """
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def read_settings(path):
    """Read a settings file for inspection only.

    Args:
        path: Path of the settings file.

    Returns:
        dict: Parsed settings, or an empty dict when the file is absent.

    Raises:
        SettingsUnreadable: The file exists but cannot be parsed as an object.
    """
    target = Path(path)
    try:
        raw = target.read_text(encoding="utf-8")
    except FileNotFoundError:
        return {}
    except OSError as exc:
        raise SettingsUnreadable("cannot read {0}: {1}".format(target, exc)) from exc
    try:
        parsed = json.loads(raw)
    except ValueError as exc:
        raise SettingsUnreadable("{0} does not parse as JSON: {1}".format(target, exc)) from exc
    if not isinstance(parsed, dict):
        raise SettingsUnreadable("{0} parses to {1}, not an object".format(target, type(parsed).__name__))
    return parsed


def hooks_block(settings):
    """Return the hooks block of a parsed settings object.

    Args:
        settings: Parsed settings dictionary.

    Returns:
        dict: The hooks mapping, empty when absent or malformed.
    """
    block = settings.get("hooks")
    return block if isinstance(block, dict) else {}


def retained_fingerprint(settings, retained=RETAINED_HOOKS):
    """Fingerprint every retained hook entry that is present.

    Args:
        settings: Parsed settings dictionary.
        retained: Hook names required to survive unchanged.

    Returns:
        dict: Hook name to canonical-JSON digest, for present hooks only.
    """
    block = hooks_block(settings)
    return {name: digest_of(block[name]) for name in retained if name in block}


def plan_removal(settings, targets):
    """Classify each named hook as present or already absent.

    Args:
        settings: Parsed settings dictionary.
        targets: Hook names to remove.

    Returns:
        dict: Hook name to either "PRESENT" or "ABSENT".
    """
    block = hooks_block(settings)
    return {name: ("PRESENT" if name in block else "ABSENT") for name in targets}


def apply_removal(settings, targets):
    """Return a settings object with the named hook registrations removed.

    The hooks block itself is left in place when it becomes empty, because an
    empty block and an absent block are read identically by every consumer in
    this repository and removing the key would be a change nobody asked for.

    Args:
        settings: Parsed settings dictionary; mutated in place.
        targets: Hook names to remove.

    Returns:
        dict: The same settings object, with the named hooks gone.
    """
    block = settings.get("hooks")
    if not isinstance(block, dict):
        return settings
    for name in targets:
        block.pop(name, None)
    settings["hooks"] = block
    return settings


def verify_retained(before, after, retained=RETAINED_HOOKS):
    """Compare retained hook entries byte for byte across the write.

    Args:
        before: Fingerprint taken before the write.
        after: Fingerprint taken after the write.
        retained: Hook names required to survive unchanged.

    Returns:
        dict: Hook name to a verdict of "IDENTICAL", "ALTERED" or "LOST".

    Raises:
        RetainedHookAltered: Any retained hook changed or disappeared.
    """
    verdicts = {}
    for name in retained:
        if name not in before:
            continue
        if name not in after:
            verdicts[name] = "LOST"
        elif before[name] == after[name]:
            verdicts[name] = "IDENTICAL"
        else:
            verdicts[name] = "ALTERED"
    broken = sorted(name for name, verdict in verdicts.items() if verdict != "IDENTICAL")
    if broken:
        raise RetainedHookAltered(
            "retained hook(s) did not survive unchanged: {0}. Restore the settings "
            "file from its backup before doing anything else.".format(", ".join(broken))
        )
    return verdicts


def remove(settings_path, targets, retained=RETAINED_HOOKS, dry_run=False):
    """Remove the named hook registrations and prove the retained ones survived.

    Args:
        settings_path: Path of the settings file to update.
        targets: Hook names to remove.
        retained: Hook names required to survive unchanged.
        dry_run: When True, report the plan and write nothing.

    Returns:
        dict: The report, with plan, digests, retention verdicts and end state.

    Raises:
        SettingsUnreadable: The file cannot serve as a merge base.
        ConcurrentModification: A competing writer won every attempt.
        SettingsWriteError: The replacement itself failed.
        RetainedHookAltered: A retained hook changed across the write.
    """
    target_path = Path(settings_path)
    before = read_settings(target_path)
    report = {
        "settings": target_path.as_posix(),
        "requested": list(targets),
        "plan": plan_removal(before, targets),
        "hooks_before": sorted(hooks_block(before)),
        "digest_before": sha256_of(target_path),
        "dry_run": bool(dry_run),
    }
    fingerprint_before = retained_fingerprint(before, retained)
    report["retained_before"] = fingerprint_before

    if dry_run:
        report["hooks_after"] = sorted(name for name in hooks_block(before) if name not in set(targets))
        report["written"] = False
        return report

    def merge(current):
        """Remove the named hooks from a freshly read settings object.

        Args:
            current: The settings object read moments before the write.

        Returns:
            dict: The settings object to write.
        """
        return apply_removal(current, targets)

    result = merge_write(target_path, merge)
    after = read_settings(target_path)
    fingerprint_after = retained_fingerprint(after, retained)

    report["written"] = bool(result.changed)
    report["write_note"] = result.note
    report["write_attempts"] = result.attempts
    report["digest_after"] = result.digest_after
    report["hooks_after"] = sorted(hooks_block(after))
    report["retained_after"] = fingerprint_after
    report["retained_verdict"] = verify_retained(fingerprint_before, fingerprint_after, retained)
    report["removed"] = sorted(name for name in targets if name not in hooks_block(after))
    report["still_present"] = sorted(name for name in targets if name in hooks_block(after))
    return report


def _parse_args(argv):
    """Parse command-line arguments.

    Args:
        argv: Argument strings excluding the program name.

    Returns:
        argparse.Namespace: Parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description="Remove named hook registrations from a Claude Code settings file (PRD FR-4 / SRS FR-13)."
    )
    parser.add_argument(
        "--settings",
        default=None,
        help="Settings file to operate on. Defaults to the user-scope settings file.",
    )
    parser.add_argument(
        "--hook",
        action="append",
        default=[],
        dest="hooks",
        help="Hook registration to remove. Repeatable. Defaults to the three PRD FR-4 hooks.",
    )
    parser.add_argument(
        "--retain",
        action="append",
        default=[],
        help="Hook required to survive byte-identical. Repeatable. Defaults to Stop and Notification.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report what would be removed and write nothing.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="Emit the report as JSON.",
    )
    return parser.parse_args(argv)


def _print_report(report):
    """Render a report as human-readable lines.

    Args:
        report: The mapping returned by ``remove``.

    Returns:
        None
    """
    print("settings: {0}".format(report["settings"]))
    print("digest:   {0} -> {1}".format(report["digest_before"], report.get("digest_after", "(unwritten)")))
    print("hooks before: {0}".format(", ".join(report["hooks_before"]) or "(none)"))
    print("hooks after:  {0}".format(", ".join(report["hooks_after"]) or "(none)"))
    for name, state in sorted(report["plan"].items()):
        print("  {0:<10} {1}".format(state, name))
    for name, verdict in sorted(report.get("retained_verdict", {}).items()):
        print("  RETAINED {0:<14} {1}".format(verdict, name))
    if report["dry_run"]:
        print("DRY RUN: nothing was written.")
    elif report["still_present"]:
        print("INCOMPLETE: still present -> {0}".format(", ".join(report["still_present"])))
    else:
        print("OK: {0}".format(report["write_note"]))


def main(argv=None):
    """Run the removal and return a process exit status.

    Args:
        argv: Optional argument strings excluding the program name.

    Returns:
        int: 0 on success, 1 on any failure.
    """
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    settings_path = Path(args.settings) if args.settings else default_settings_path()
    targets = tuple(args.hooks) if args.hooks else FR4_HOOKS
    retained = tuple(args.retain) if args.retain else RETAINED_HOOKS
    try:
        report = remove(settings_path, targets, retained=retained, dry_run=args.dry_run)
    except (SettingsUnreadable, ConcurrentModification, SettingsWriteError, RetainedHookAltered) as exc:
        print("FAILED: {0}".format(exc), file=sys.stderr)
        return EXIT_FAILED
    if args.as_json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        _print_report(report)
    return EXIT_OK if (report["dry_run"] or not report["still_present"]) else EXIT_FAILED


if __name__ == "__main__":
    sys.exit(main())

"""register-mcp / unregister-mcp: opt-in user-scope MCP registration (SRS FR-37).

Under ADR-019 the plugin bundles zero MCP servers, so this command is the ONLY
route to any MCP-backed capability. Registration is a pure configuration
mutation: adding an entry starts no process, and a stdio server is spawned only
when a later session actually resolves it.

THREE SEPARATE CLAIMS, KEPT SEPARATE
------------------------------------
- REVERSIBLE: unregister reverses exactly what register did, and nothing else.
  Provenance is tracked in a plugin-owned ledger beside the settings file rather
  than inside it, so a server the user registered by some other route is never
  claimed and never removed. Where ``--force`` displaced a pre-existing entry,
  reversing means RESTORING that entry, not deleting the name: the ledger keeps
  the displaced spec so the user's own configuration comes back. Deleting it
  would make ``--force`` a one-way door while still being described as
  reversible.
- ROUND TRIP: a capability that was unreachable becomes reachable after
  register and unreachable again after unregister.
- BYTE-IDENTICAL: NOT claimed. The written file is re-serialised with two-space
  indentation, so a settings file that was formatted any other way will differ
  in bytes after a round trip even though it is equal as an object. Use
  ``--verify-round-trip`` to see both comparisons reported separately.

ADR-020 LAYER 1
---------------
``unregister`` refuses by default when ``PreToolUse`` is absent from the
settings file's hooks block, because that combination leaves no local
version-push gate at all. The refusal names the consequence and both ways
forward. It can be overridden with ``--acknowledge-no-push-gate``: the action
stays possible, but never by accident.

USAGE
    python mcp_registration.py status
    python mcp_registration.py status --one-line
    python mcp_registration.py register --server-root <dir>
    python mcp_registration.py unregister
"""

import argparse
import json
import os
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from settings_store import (  # noqa: E402
    ConcurrentModification,
    SettingsUnreadable,
    SettingsWriteError,
    merge_write,
    sha256_of,
)

REGISTRY_FILE_NAME = "mcp-registry.json"
LEDGER_FILE_NAME = "cwe-mcp-registrations.json"
MANIFEST_MARKER = Path(".claude-plugin") / "plugin.json"

EXIT_OK = 0
EXIT_FAILED = 1
EXIT_REFUSED = 2


class RegistrationError(Exception):
    """A registration operation could not be completed as asked."""


def find_plugin_root(start=None):
    """Locate the plugin root that owns this script.

    Resolution order matches the plugin surface skill: the CLAUDE_PLUGIN_ROOT
    environment variable Claude Code populates for anything it spawns, then an
    ascent from this file's own directory looking for the manifest. A path
    relative to the current working directory is never used, because after a
    real install the plugin's files and the user's working directory are
    unrelated locations.

    Args:
        start: Directory to begin the ascent from. Defaults to this file's
            directory.

    Returns:
        Path: The plugin root.

    Raises:
        RegistrationError: No manifest was found by either route.
    """
    from_env = os.environ.get("CLAUDE_PLUGIN_ROOT", "").strip()
    if from_env:
        candidate = Path(from_env)
        if (candidate / MANIFEST_MARKER).is_file():
            return candidate.resolve()

    current = Path(start).resolve() if start else SCRIPT_DIR
    for directory in [current] + list(current.parents):
        if (directory / MANIFEST_MARKER).is_file():
            return directory
    raise RegistrationError(
        "cannot locate the plugin root: CLAUDE_PLUGIN_ROOT is unset or wrong, "
        "and no ancestor of {0} contains {1}".format(current, MANIFEST_MARKER.as_posix())
    )


def default_settings_path():
    """Return the user-scope settings path this command targets.

    Returns:
        Path: The value of CLAUDE_SETTINGS_FILE when set, else the standard
        user-scope location.
    """
    override = os.environ.get("CLAUDE_SETTINGS_FILE", "").strip()
    if override:
        return Path(override)
    return Path.home() / ".claude" / "settings.json"


def load_registry(plugin_root):
    """Read the catalogue of registrable servers.

    Args:
        plugin_root: Path of the plugin root.

    Returns:
        list: Server descriptor dictionaries.

    Raises:
        RegistrationError: The catalogue is missing or malformed.
    """
    path = Path(plugin_root) / REGISTRY_FILE_NAME
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RegistrationError("server catalogue not found at {0}".format(path)) from exc
    except json.JSONDecodeError as exc:
        raise RegistrationError("server catalogue at {0} is not valid JSON: {1}".format(path, exc)) from exc
    servers = data.get("servers")
    if not isinstance(servers, list) or not servers:
        raise RegistrationError("server catalogue at {0} declares no servers".format(path))
    return servers


def resolve_server_root(explicit):
    """Determine where the MCP server repositories are checked out.

    The plugin cannot guess this. The server repositories are separate
    checkouts whose location is a property of the user's machine, not of the
    plugin, so an unresolvable root is reported rather than assumed.

    Args:
        explicit: Value of the --server-root flag, or None.

    Returns:
        Path: The resolved server root.

    Raises:
        RegistrationError: Neither the flag nor the environment variable
            names an existing directory.
    """
    candidates = [explicit, os.environ.get("CWE_MCP_SERVER_ROOT", "").strip() or None]
    for candidate in candidates:
        if candidate and Path(candidate).is_dir():
            return Path(candidate).resolve()
    raise RegistrationError(
        "cannot resolve where the MCP server repositories live. Pass "
        "--server-root <dir>, or set CWE_MCP_SERVER_ROOT. The directory must "
        "contain the mcp-* server checkouts."
    )


def server_entry_path(server, server_root):
    """Compute the on-disk path of a server's entry point.

    Args:
        server: Server descriptor from the catalogue.
        server_root: Directory holding the server checkouts.

    Returns:
        Path: Absolute path of the server's entry script.
    """
    return Path(server_root) / server["repo"] / server["entry"]


def build_spec(server, server_root):
    """Build the settings.json entry for one server.

    The spec is the minimum Claude Code needs to spawn a stdio server: the
    interpreter, the absolute path of its entry point, and an empty environment.
    No field is included that the spawn does not require.

    Args:
        server: Server descriptor from the catalogue.
        server_root: Directory holding the server checkouts.

    Returns:
        dict: The mcpServers entry value.
    """
    return {
        "command": server["interpreter"],
        "args": [server_entry_path(server, server_root).as_posix()],
        "env": {},
    }


def read_ledger(path):
    """Read the provenance ledger of registrations this command performed.

    Args:
        path: Path of the ledger file.

    Each record carries the spec this command wrote and, when ``--force``
    displaced an entry the user already had, the displaced spec under
    ``displaced`` so unregister can put it back.

    Returns:
        dict: Mapping of server id to the recorded registration record. An
        absent or unreadable ledger yields an empty mapping, which is safe here
        because the ledger only ever narrows what unregister will touch.
    """
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}
    entries = data.get("registered")
    return entries if isinstance(entries, dict) else {}


def write_ledger(path, entries):
    """Persist the provenance ledger.

    Args:
        path: Path of the ledger file.
        entries: Mapping of server id to registration record.

    Returns:
        None
    """
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "what_this_is": (
            "Provenance for MCP server entries written by the plugin's "
            "register-mcp command. unregister-mcp removes only names listed "
            "here, so a server registered by any other route is never touched."
        ),
        "registered": entries,
    }
    target.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def read_settings(path):
    """Read a settings file for inspection only.

    Args:
        path: Path of the settings file.

    Returns:
        dict: Parsed settings, or an empty dict when the file is absent.

    Raises:
        RegistrationError: The file exists but does not parse.
    """
    try:
        raw = Path(path).read_text(encoding="utf-8")
    except FileNotFoundError:
        return {}
    except OSError as exc:
        raise RegistrationError("cannot read {0}: {1}".format(path, exc)) from exc
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RegistrationError("{0} is not valid JSON: {1}".format(path, exc)) from exc
    return parsed if isinstance(parsed, dict) else {}


def registered_names(settings):
    """Return the set of server names present in the settings mcpServers block.

    Args:
        settings: Parsed settings dictionary.

    Returns:
        set: Server names currently registered at user scope.
    """
    block = settings.get("mcpServers")
    return set(block) if isinstance(block, dict) else set()


def pre_tool_use_present(settings):
    """Report whether a PreToolUse hook entry exists in the settings file.

    Args:
        settings: Parsed settings dictionary.

    Returns:
        bool: True when the hooks block declares a non-empty PreToolUse.
    """
    hooks = settings.get("hooks")
    if not isinstance(hooks, dict):
        return False
    return bool(hooks.get("PreToolUse"))


def capability_report(servers, settings, server_root=None):
    """Describe every catalogued capability and whether it is reachable.

    Reachability is decided by the settings file, which is the thing that
    determines whether a future session can spawn the server at all. When a
    server root is supplied, an entry pointing at a file that does not exist is
    reported as registered-but-broken rather than as reachable.

    Args:
        servers: Catalogue server descriptors.
        settings: Parsed settings dictionary.
        server_root: Optional directory holding the server checkouts.

    Returns:
        list: One dictionary per server with id, capability, registered,
        reachable and detail keys.
    """
    present = registered_names(settings)
    rows = []
    for server in servers:
        is_registered = server["id"] in present
        detail = ""
        reachable = is_registered
        if is_registered and server_root is not None:
            entry = server_entry_path(server, server_root)
            if not entry.is_file():
                reachable = False
                detail = "registered, but its entry point {0} does not exist".format(entry.as_posix())
        elif not is_registered and server.get("not_built_yet"):
            detail = server["not_built_yet"]
        rows.append(
            {
                "id": server["id"],
                "capability": server["capability"],
                "registered": is_registered,
                "reachable": reachable,
                "detail": detail,
            }
        )
    return rows


def one_line_precondition(rows):
    """Render the single actionable line other plugin commands emit.

    ADR-019's "what is lost" item 3 requires that a plugin command detecting an
    unregistered server emits ONE actionable line naming register-mcp, so a
    missing capability never presents as a working one. This is that line, and
    it is deliberately one line rather than a report.

    Args:
        rows: Output of capability_report.

    Returns:
        str: The line to emit.
    """
    missing = [row["capability"] for row in rows if not row["reachable"]]
    if not missing:
        return "MCP capabilities reachable: {0}.".format(", ".join(row["capability"] for row in rows))
    return "MCP capability not registered: {0}. Run register-mcp to enable it; " "until then it is unavailable.".format(
        ", ".join(sorted(missing))
    )


def _selected(servers, capabilities):
    """Filter the catalogue down to the requested capabilities.

    Args:
        servers: Catalogue server descriptors.
        capabilities: List of capability names, or an empty list for all.

    Returns:
        list: Matching server descriptors.

    Raises:
        RegistrationError: A named capability is not in the catalogue.
    """
    if not capabilities:
        return list(servers)
    known = {server["capability"]: server for server in servers}
    chosen = []
    for name in capabilities:
        if name not in known:
            raise RegistrationError(
                "unknown capability {0!r}; the catalogue offers: {1}".format(name, ", ".join(sorted(known)))
            )
        chosen.append(known[name])
    return chosen


def do_register(args, plugin_root, settings_path, ledger_path):
    """Add user-scope MCP registrations for the selected capabilities.

    Args:
        args: Parsed command-line arguments.
        plugin_root: Path of the plugin root.
        settings_path: Path of the settings file to update.
        ledger_path: Path of the provenance ledger.

    Returns:
        int: Process exit status.
    """
    servers = load_registry(plugin_root)
    server_root = resolve_server_root(args.server_root)
    chosen = _selected(servers, args.capability)

    settings = read_settings(settings_path)
    already = registered_names(settings)
    ledger = read_ledger(ledger_path)

    to_write = {}
    skipped = []
    for server in chosen:
        entry = server_entry_path(server, server_root)
        if not entry.is_file():
            skipped.append((server, "entry point not found at {0}".format(entry.as_posix())))
            continue
        if server["id"] in already and server["id"] not in ledger and not args.force:
            skipped.append(
                (
                    server,
                    "already registered by something other than this command; "
                    "left untouched. Re-run with --force to take ownership.",
                )
            )
            continue
        to_write[server["id"]] = build_spec(server, server_root)

    for server, reason in skipped:
        print("  SKIP  {0:<20} {1}".format(server["capability"], reason))

    if not to_write:
        print("Nothing to register.")
        return EXIT_OK if not args.capability else EXIT_FAILED

    displaced = {}

    def merge(current):
        """Insert the selected server entries into a freshly read settings object.

        Any entry being overwritten is captured into ``displaced`` from this
        fresh read rather than from the earlier inspection read, so what gets
        recorded is what was actually replaced. The capture is reset on every
        call because merge_write may retry, and only the landing call's view is
        correct.

        Args:
            current: The settings object read moments before the write.

        Returns:
            dict: The settings object to write.
        """
        block = current.get("mcpServers")
        if not isinstance(block, dict):
            block = {}
        displaced.clear()
        for server_id, spec in to_write.items():
            existing = block.get(server_id)
            if isinstance(existing, dict) and existing != spec:
                displaced[server_id] = existing
        block.update(to_write)
        current["mcpServers"] = block
        return current

    result = merge_write(settings_path, merge)

    for server_id in sorted(to_write):
        record = {"spec": to_write[server_id]}
        prior_displaced = ledger.get(server_id, {}).get("displaced")
        if isinstance(prior_displaced, dict):
            record["displaced"] = prior_displaced
        elif server_id in displaced and server_id not in ledger:
            record["displaced"] = displaced[server_id]
        ledger[server_id] = record
    write_ledger(ledger_path, ledger)

    for server_id in sorted(to_write):
        if "displaced" in ledger[server_id]:
            print("  ADDED {0} (displaced an existing entry; unregister-mcp will " "restore it)".format(server_id))
        else:
            print("  ADDED {0}".format(server_id))
    print("settings: {0}".format(Path(settings_path).as_posix()))
    print("write:    {0} (attempt {1})".format(result.note, result.attempts))
    print("digest:   {0} -> {1}".format(result.digest_before, result.digest_after))
    print(one_line_precondition(capability_report(servers, read_settings(settings_path), server_root)))
    return EXIT_OK


def do_unregister(args, plugin_root, settings_path, ledger_path):
    """Remove the user-scope MCP registrations this command previously added.

    Args:
        args: Parsed command-line arguments.
        plugin_root: Path of the plugin root.
        settings_path: Path of the settings file to update.
        ledger_path: Path of the provenance ledger.

    Returns:
        int: Process exit status.
    """
    servers = load_registry(plugin_root)
    chosen = _selected(servers, args.capability)
    settings = read_settings(settings_path)
    ledger = read_ledger(ledger_path)

    removable = [
        server["id"] for server in chosen if server["id"] in ledger and server["id"] in registered_names(settings)
    ]
    if not removable:
        print("Nothing to unregister; this command has no recorded registrations to reverse.")
        return EXIT_OK

    if not pre_tool_use_present(settings) and not args.acknowledge_no_push_gate:
        print("REFUSED: unregistering would leave no local version-push gate.")
        print("  PreToolUse is absent from {0}, so the hook-side gate is not".format(Path(settings_path).as_posix()))
        print("  running, and removing the MCP-side gate would leave neither.")
        print("  Two ways forward:")
        print("    1. Restore the PreToolUse entry in the settings file, then re-run.")
        print("    2. Re-run with --acknowledge-no-push-gate to proceed anyway.")
        print("  The CI-side assertion still applies; the LOCAL guard would not.")
        return EXIT_REFUSED

    def merge(current):
        """Reverse the recorded registrations in a freshly read settings object.

        Reversing a registration that displaced a pre-existing entry means
        putting that entry back, not deleting the name. Only a registration that
        added a name which was not there before is reversed by removal.

        Args:
            current: The settings object read moments before the write.

        Returns:
            dict: The settings object to write.
        """
        block = current.get("mcpServers")
        if not isinstance(block, dict):
            return current
        for server_id in removable:
            restored = ledger.get(server_id, {}).get("displaced")
            if isinstance(restored, dict):
                block[server_id] = restored
            else:
                block.pop(server_id, None)
        if block:
            current["mcpServers"] = block
        else:
            current.pop("mcpServers", None)
        return current

    result = merge_write(settings_path, merge)

    reversal = {server_id: "displaced" in ledger.get(server_id, {}) for server_id in removable}
    for server_id in removable:
        ledger.pop(server_id, None)
    write_ledger(ledger_path, ledger)

    for server_id in removable:
        if reversal[server_id]:
            print("  RESTORED {0} to the entry that was there before " "register-mcp --force".format(server_id))
        else:
            print("  REMOVED {0}".format(server_id))
    print("settings: {0}".format(Path(settings_path).as_posix()))
    print("write:    {0} (attempt {1})".format(result.note, result.attempts))
    print("digest:   {0} -> {1}".format(result.digest_before, result.digest_after))
    print(one_line_precondition(capability_report(servers, read_settings(settings_path))))
    return EXIT_OK


def do_status(args, plugin_root, settings_path, ledger_path):
    """Report which catalogued capabilities are reachable.

    Args:
        args: Parsed command-line arguments.
        plugin_root: Path of the plugin root.
        settings_path: Path of the settings file to inspect.
        ledger_path: Path of the provenance ledger.

    Returns:
        int: Process exit status.
    """
    servers = load_registry(plugin_root)
    settings = read_settings(settings_path)
    server_root = None
    if args.server_root or os.environ.get("CWE_MCP_SERVER_ROOT", "").strip():
        server_root = resolve_server_root(args.server_root)
    rows = capability_report(servers, settings, server_root)

    if args.one_line:
        print(one_line_precondition(rows))
        return EXIT_OK

    if args.as_json:
        print(
            json.dumps(
                {
                    "settings": Path(settings_path).as_posix(),
                    "settings_sha256": sha256_of(settings_path),
                    "ledger": Path(ledger_path).as_posix(),
                    "pre_tool_use_present": pre_tool_use_present(settings),
                    "capabilities": rows,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return EXIT_OK

    print("settings: {0}".format(Path(settings_path).as_posix()))
    print("ledger:   {0}".format(Path(ledger_path).as_posix()))
    for row in rows:
        state = "REACHABLE" if row["reachable"] else "UNREACHABLE"
        print("  {0:<12} {1:<22} {2}".format(state, row["capability"], row["detail"]))
    print(one_line_precondition(rows))
    return EXIT_OK


def _parse_args(argv):
    """Parse command-line arguments.

    Args:
        argv: Argument strings excluding the program name.

    Returns:
        argparse.Namespace: Parsed arguments.
    """
    parser = argparse.ArgumentParser(
        prog="mcp_registration",
        description="Opt-in user-scope MCP server registration for the Claude Workflow Engine plugin (SRS FR-37).",
    )
    parser.add_argument(
        "--settings",
        default=None,
        help="Settings file to operate on. Defaults to the user scope.",
    )
    parser.add_argument(
        "--ledger",
        default=None,
        help="Provenance ledger path. Defaults to a sibling of the settings file.",
    )
    parser.add_argument(
        "--plugin-root",
        default=None,
        help="Plugin root override, for tests and local development.",
    )
    sub = parser.add_subparsers(dest="action", required=True)

    status = sub.add_parser("status", help="Report which capabilities are reachable.")
    status.add_argument(
        "--one-line",
        action="store_true",
        help="Emit only the single actionable precondition line.",
    )
    status.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="Emit a machine-readable report.",
    )
    status.add_argument(
        "--server-root",
        default=None,
        help="Directory holding the mcp-* server checkouts.",
    )

    register = sub.add_parser("register", help="Add user-scope MCP registrations.")
    register.add_argument(
        "--server-root",
        default=None,
        help="Directory holding the mcp-* server checkouts.",
    )
    register.add_argument(
        "--capability",
        action="append",
        default=[],
        help="Register only this capability. Repeatable.",
    )
    register.add_argument(
        "--force",
        action="store_true",
        help="Take ownership of an entry registered by another route.",
    )

    unregister = sub.add_parser("unregister", help="Reverse registrations made by this command.")
    unregister.add_argument(
        "--capability",
        action="append",
        default=[],
        help="Unregister only this capability. Repeatable.",
    )
    unregister.add_argument(
        "--acknowledge-no-push-gate",
        action="store_true",
        help="Proceed even though PreToolUse is absent and no local push gate would remain.",
    )
    return parser.parse_args(argv)


def main(argv=None):
    """Run the requested action and return a process exit status.

    Args:
        argv: Optional argument strings excluding the program name.

    Returns:
        int: 0 on success, 1 on failure, 2 when an action was refused.
    """
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    try:
        plugin_root = Path(args.plugin_root).resolve() if args.plugin_root else find_plugin_root()
        settings_path = Path(args.settings) if args.settings else default_settings_path()
        ledger_path = Path(args.ledger) if args.ledger else settings_path.parent / LEDGER_FILE_NAME
        handlers = {
            "status": do_status,
            "register": do_register,
            "unregister": do_unregister,
        }
        return handlers[args.action](args, plugin_root, settings_path, ledger_path)
    except SettingsUnreadable as exc:
        print("REFUSED: {0}".format(exc), file=sys.stderr)
        return EXIT_REFUSED
    except ConcurrentModification as exc:
        print("ABORTED: {0}".format(exc), file=sys.stderr)
        return EXIT_FAILED
    except (RegistrationError, SettingsWriteError) as exc:
        print("ERROR: {0}".format(exc), file=sys.stderr)
        return EXIT_FAILED


if __name__ == "__main__":
    sys.exit(main())

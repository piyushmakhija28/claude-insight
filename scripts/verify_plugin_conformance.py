"""Verify the Claude Code plugin tree against its packaging conformance rules.

This is the CI-blocking fitness function for PRD FR-14 / SRS FR-26 (issue
V2-015). It composes four atomic, triggered, static fitness functions into one
holistic gate. Each is evaluated against the plugin tree as it exists on disk,
never against a declaration about the tree, so a manifest that claims conformance
while the filesystem disagrees fails here rather than at a user's install.

FF-1 MANIFEST SCHEMA (severity ERROR)
    ``.claude-plugin/plugin.json`` exists, parses, and validates against a
    CLOSED-WORLD jsonschema: ``name`` and ``description`` are required, ``version``
    is required and must be explicit semver, and every key present must be a
    member of the permitted field set. A key outside that set rejects the whole
    manifest rather than being reported and passed over.

    The permitted set was MEASURED, not carried forward from documentation.
    Method: a scratch plugin was validated once per candidate key with
    ``claude plugin validate <root> --strict``, holding every other field
    constant, and the key was admitted only when that run exited 0. Result on
    Claude Code CLI 2.1.220: 8 metadata keys (name, version, description,
    author, homepage, repository, license, keywords) plus 10 structural and
    path-override keys (commands, agents, skills, hooks, outputStyles,
    mcpServers, lspServers, experimental, userConfig, settings). Rejected under
    ``--strict``: any unknown key, plus ``monitors`` (deprecated at top level in
    favour of ``experimental.monitors``) and ``strict``/``source`` (marketplace
    entry keys, not manifest keys). Re-run the probe when the CLI version
    changes; the set is a measurement, not a constant.

FF-2 ADR-010 ZERO HOOKS (severity CRITICAL)
    No ``hooks`` directory and no ``*hooks.json`` file anywhere in the plugin
    tree, and no ``hooks`` key in the manifest. Plugin hook entries merge into a
    flat, unlabelled, session-wide pipeline; nothing survives that merge to say
    which plugin contributed which entry, so no per-hook disable can exist even
    in principle. Whole-plugin disable is the only correct granularity, which
    means shipping a hook hands the user strictly less control than they have
    today.

FF-3 ADR-019 ZERO BUNDLED MCP (severity CRITICAL)
    No ``.mcp.json`` anywhere in the plugin tree, and no ``mcpServers`` key in
    the manifest. A bundled stdio server is spawned when the plugin is ENABLED,
    with no tool call made - measured, not inferred. Any bundled server,
    however minimal, therefore puts processes on a user's machine that the user
    never asked for.

FF-4 DISCOVERY LAYOUT (severity ERROR)
    Capability directories sit at the plugin ROOT. Discovery scans a fixed set
    of names at the root only, so a capability directory nested inside
    ``.claude-plugin/`` is invisible to it. That mistake produces a plugin which
    installs with a well-formed manifest and exposes zero capabilities, with no
    error raised anywhere - the single most expensive layout defect available,
    because nothing reports it.

WHY THE MANIFEST-KEY CHECKS EXIST ALONGSIDE THE FILESYSTEM CHECKS
    FR-26's acceptance criterion states the ADR-010 check as a find over the
    plugin tree for ``hooks/`` or ``*hooks.json``. That check alone is evadable:
    the manifest supports explicit ``hooks`` and ``mcpServers`` path-override
    keys, both MEASURED as accepted by ``claude plugin validate --strict``, and
    either can point at a file whose name the find pattern does not match. FF-2
    and FF-3 therefore assert on the manifest key as well as on the filesystem.
    Removing either half reopens the bypass.

USAGE
    python scripts/verify_plugin_conformance.py
    python scripts/verify_plugin_conformance.py --plugin-root <path>
    python scripts/verify_plugin_conformance.py --json

Exit status is 0 only when every fitness function passes; any finding exits 1.
The ``--plugin-root`` override exists so the negative tests can point the gate
at a scratch tree carrying a planted violation and prove the gate can fail. A
gate that has never been observed to fail is not a gate.
"""

import argparse
import json
import os
import sys
from pathlib import Path

import jsonschema

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PLUGIN_ROOT = REPO_ROOT / "plugin"

MANIFEST_DIR_NAME = ".claude-plugin"
MANIFEST_FILE_NAME = "plugin.json"

SEMVER_PATTERN = (
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)"
    r"(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?"
    r"(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"
)

PERMITTED_MANIFEST_FIELDS_MEASURED_AGAINST = "Claude Code CLI 2.1.220"

PERMITTED_MANIFEST_FIELDS = (
    "name",
    "version",
    "description",
    "author",
    "homepage",
    "repository",
    "license",
    "keywords",
    "commands",
    "agents",
    "skills",
    "hooks",
    "outputStyles",
    "mcpServers",
    "lspServers",
    "experimental",
    "userConfig",
    "settings",
)

FORBIDDEN_MANIFEST_FIELDS = {
    "hooks": (
        "CRITICAL",
        "ADR-010",
        "a hooks path-override reintroduces bundled hooks without creating a "
        "hooks/ directory the filesystem check would see",
    ),
    "mcpServers": (
        "CRITICAL",
        "ADR-019",
        "an mcpServers path-override bundles servers without creating a " ".mcp.json the filesystem check would see",
    ),
}

DISCOVERED_CAPABILITY_NAMES = (
    "commands",
    "agents",
    "skills",
    "hooks",
    "output-styles",
    "monitors",
    "bin",
)

PRUNED_WALK_DIRS = frozenset({".git", "__pycache__", "node_modules", ".pytest_cache"})

BUNDLED_MCP_FILE_NAME = ".mcp.json"
HOOKS_DIR_NAME = "hooks"
HOOKS_FILE_SUFFIX = "hooks.json"


class Finding:
    """A single conformance violation with the rule and evidence that produced it.

    Attributes:
        check: Identifier of the fitness function that produced the finding.
        severity: Either "CRITICAL" or "ERROR".
        rule: The decision record or requirement the finding violates.
        path: Repository-relative path of the offending artefact, or None when
            the finding is about the manifest as a whole.
        message: One-line statement of what is wrong.
    """

    def __init__(self, check, severity, rule, message, path=None):
        """Store the finding's fields verbatim.

        Args:
            check: Fitness function identifier, for example "FF-2".
            severity: "CRITICAL" or "ERROR".
            rule: Violated decision record or requirement identifier.
            message: One-line statement of the defect.
            path: Offending path as a string, or None.
        """
        self.check = check
        self.severity = severity
        self.rule = rule
        self.message = message
        self.path = path

    def as_dict(self):
        """Return the finding as a plain dictionary for JSON output.

        Returns:
            dict: Keys check, severity, rule, path, message.
        """
        return {
            "check": self.check,
            "severity": self.severity,
            "rule": self.rule,
            "path": self.path,
            "message": self.message,
        }

    def __str__(self):
        """Return a single-line human-readable rendering of the finding.

        Returns:
            str: Formatted finding line.
        """
        location = self.path if self.path else "(manifest)"
        return "[{0}] {1} {2} {3}: {4}".format(self.severity, self.check, self.rule, location, self.message)


def build_manifest_schema():
    """Build the closed-world jsonschema for ``.claude-plugin/plugin.json``.

    The schema is deliberately stricter than the Claude Code CLI's own
    validator in two respects, both MEASURED rather than assumed on CLI 2.1.220:

    1. The CLI accepts a non-semver ``version`` string under ``--strict``. FR-26
       requires an explicit semver version, so the pattern is enforced here.
    2. The CLI reports an unknown top-level key as a warning, promoted to an
       error only by ``--strict``. This schema rejects it unconditionally, which
       is the closed-world reading FR-26's "validates against the CONFIRMED-list
       contract" requires.

    Returns:
        dict: A draft-2020-12 schema object.
    """
    properties = {name: {} for name in PERMITTED_MANIFEST_FIELDS}
    properties["name"] = {"type": "string", "minLength": 1}
    properties["description"] = {"type": "string", "minLength": 1}
    properties["version"] = {"type": "string", "pattern": SEMVER_PATTERN}
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "Claude Code plugin manifest (closed-world)",
        "type": "object",
        "required": ["name", "description", "version"],
        "properties": properties,
        "additionalProperties": False,
    }


def _relative(path, plugin_root):
    """Render a path relative to the plugin root using forward slashes.

    Args:
        path: Path object to render.
        plugin_root: Path object the result is relative to.

    Returns:
        str: Forward-slash relative path, or the absolute path when the target
        does not sit under plugin_root.
    """
    try:
        return Path(path).resolve().relative_to(Path(plugin_root).resolve()).as_posix()
    except ValueError:
        return Path(path).as_posix()


def _iter_tree(plugin_root):
    """Walk the plugin tree, yielding (dirpath, dirnames, filenames) triples.

    Directories in PRUNED_WALK_DIRS are pruned in place so their contents are
    never visited and never reported.

    Args:
        plugin_root: Path object of the plugin root directory.

    Yields:
        tuple: (Path dirpath, list dirnames, list filenames).
    """
    for dirpath, dirnames, filenames in os.walk(str(plugin_root)):
        dirnames[:] = [d for d in dirnames if d not in PRUNED_WALK_DIRS]
        yield Path(dirpath), dirnames, filenames


def load_manifest(plugin_root):
    """Read and parse the plugin manifest.

    Args:
        plugin_root: Path object of the plugin root directory.

    Returns:
        tuple: (manifest dict or None, list of Finding).
    """
    manifest_path = Path(plugin_root) / MANIFEST_DIR_NAME / MANIFEST_FILE_NAME
    if not manifest_path.is_file():
        return None, [
            Finding(
                "FF-1",
                "ERROR",
                "FR-26",
                "plugin manifest not found; a plugin root must carry it",
                _relative(manifest_path, plugin_root),
            )
        ]
    try:
        raw = manifest_path.read_text(encoding="utf-8")
    except OSError as exc:
        return None, [
            Finding(
                "FF-1",
                "ERROR",
                "FR-26",
                "plugin manifest is unreadable: {0}".format(exc),
                _relative(manifest_path, plugin_root),
            )
        ]
    try:
        return json.loads(raw), []
    except json.JSONDecodeError as exc:
        return None, [
            Finding(
                "FF-1",
                "ERROR",
                "FR-26",
                "plugin manifest is not valid JSON: {0}".format(exc),
                _relative(manifest_path, plugin_root),
            )
        ]


def check_manifest_schema(manifest):
    """Validate the manifest against the closed-world schema (FF-1).

    Args:
        manifest: Parsed manifest dictionary.

    Returns:
        list: Finding objects, empty when the manifest validates.
    """
    manifest_rel = "{0}/{1}".format(MANIFEST_DIR_NAME, MANIFEST_FILE_NAME)
    validator = jsonschema.Draft202012Validator(build_manifest_schema())
    findings = []
    for error in sorted(validator.iter_errors(manifest), key=str):
        pointer = "/".join(str(part) for part in error.absolute_path) or "(root)"
        findings.append(
            Finding(
                "FF-1",
                "ERROR",
                "FR-26",
                "manifest schema violation at {0}: {1}".format(pointer, error.message),
                manifest_rel,
            )
        )
    return findings


def check_no_hooks(manifest, plugin_root):
    """Assert the plugin tree carries no hooks artefact of any kind (FF-2).

    Args:
        manifest: Parsed manifest dictionary, or None when it failed to load.
        plugin_root: Path object of the plugin root directory.

    Returns:
        list: Finding objects, empty when no hooks artefact exists.
    """
    findings = []
    for dirpath, dirnames, filenames in _iter_tree(plugin_root):
        for name in dirnames:
            if name.lower() == HOOKS_DIR_NAME:
                findings.append(
                    Finding(
                        "FF-2",
                        "CRITICAL",
                        "ADR-010",
                        "plugin tree contains a hooks directory; the plugin " "ships zero hooks",
                        _relative(dirpath / name, plugin_root),
                    )
                )
        for name in filenames:
            if name.lower().endswith(HOOKS_FILE_SUFFIX):
                findings.append(
                    Finding(
                        "FF-2",
                        "CRITICAL",
                        "ADR-010",
                        "plugin tree contains a hooks configuration file; the " "plugin ships zero hooks",
                        _relative(dirpath / name, plugin_root),
                    )
                )
    findings.extend(_check_forbidden_manifest_field(manifest, "hooks", "FF-2"))
    return findings


def check_no_bundled_mcp(manifest, plugin_root):
    """Assert the plugin tree bundles no MCP server configuration (FF-3).

    Args:
        manifest: Parsed manifest dictionary, or None when it failed to load.
        plugin_root: Path object of the plugin root directory.

    Returns:
        list: Finding objects, empty when nothing MCP-related is bundled.
    """
    findings = []
    for dirpath, _dirnames, filenames in _iter_tree(plugin_root):
        for name in filenames:
            if name.lower() == BUNDLED_MCP_FILE_NAME:
                findings.append(
                    Finding(
                        "FF-3",
                        "CRITICAL",
                        "ADR-019",
                        "plugin tree bundles an MCP server configuration; a "
                        "bundled server spawns on plugin enable with no tool "
                        "call made",
                        _relative(dirpath / name, plugin_root),
                    )
                )
    findings.extend(_check_forbidden_manifest_field(manifest, "mcpServers", "FF-3"))
    return findings


def _check_forbidden_manifest_field(manifest, field, check_id):
    """Report a manifest path-override key that reintroduces a forbidden artefact.

    Args:
        manifest: Parsed manifest dictionary, or None.
        field: Manifest key name to test for presence.
        check_id: Fitness function identifier to attribute the finding to.

    Returns:
        list: Finding objects, empty when the key is absent.
    """
    if not isinstance(manifest, dict) or field not in manifest:
        return []
    severity, rule, reason = FORBIDDEN_MANIFEST_FIELDS[field]
    return [
        Finding(
            check_id,
            severity,
            rule,
            "manifest declares a forbidden '{0}' key: {1}".format(field, reason),
            "{0}/{1}".format(MANIFEST_DIR_NAME, MANIFEST_FILE_NAME),
        )
    ]


def check_discovery_layout(plugin_root):
    """Assert capability directories sit at the plugin root, not nested (FF-4).

    Args:
        plugin_root: Path object of the plugin root directory.

    Returns:
        list: Finding objects, empty when the layout is discoverable.
    """
    findings = []
    manifest_dir = Path(plugin_root) / MANIFEST_DIR_NAME
    if manifest_dir.is_dir():
        for entry in sorted(manifest_dir.iterdir()):
            if entry.is_dir() and entry.name.lower() in DISCOVERED_CAPABILITY_NAMES:
                findings.append(
                    Finding(
                        "FF-4",
                        "ERROR",
                        "FR-26",
                        "capability directory is nested inside {0}; discovery "
                        "scans the plugin root only, so this exposes zero "
                        "capabilities with no error raised".format(MANIFEST_DIR_NAME),
                        _relative(entry, plugin_root),
                    )
                )
    if not any((Path(plugin_root) / name).is_dir() for name in ("commands", "agents", "skills")):
        findings.append(
            Finding(
                "FF-4",
                "ERROR",
                "FR-26",
                "no commands/, agents/ or skills/ directory at the plugin root; "
                "the plugin would install cleanly and expose nothing",
                ".",
            )
        )
    return findings


def discovery_trace(plugin_root):
    """Report which convention-discovered names exist at the plugin root.

    Args:
        plugin_root: Path object of the plugin root directory.

    Returns:
        dict: Mapping of discovered name to a bool presence flag.
    """
    root = Path(plugin_root)
    trace = {}
    for name in DISCOVERED_CAPABILITY_NAMES:
        trace[name + "/"] = (root / name).is_dir()
    trace[BUNDLED_MCP_FILE_NAME] = (root / BUNDLED_MCP_FILE_NAME).is_file()
    trace[".lsp.json"] = (root / ".lsp.json").is_file()
    return trace


def run_all(plugin_root):
    """Run every fitness function against a plugin root.

    Args:
        plugin_root: Path object or string of the plugin root directory.

    Returns:
        list: Finding objects from all checks, in check order.
    """
    root = Path(plugin_root)
    if not root.is_dir():
        return [
            Finding(
                "FF-1",
                "ERROR",
                "FR-26",
                "plugin root does not exist or is not a directory",
                str(root),
            )
        ]
    manifest, findings = load_manifest(root)
    if manifest is not None:
        findings.extend(check_manifest_schema(manifest))
    findings.extend(check_no_hooks(manifest, root))
    findings.extend(check_no_bundled_mcp(manifest, root))
    findings.extend(check_discovery_layout(root))
    return findings


def _parse_args(argv):
    """Parse command-line arguments.

    Args:
        argv: List of argument strings, excluding the program name.

    Returns:
        argparse.Namespace: Parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description="Verify the Claude Code plugin tree against ADR-010, " "ADR-019 and the FR-26 manifest contract."
    )
    parser.add_argument(
        "--plugin-root",
        default=str(DEFAULT_PLUGIN_ROOT),
        help="Plugin root to check. Defaults to the repository's plugin/ tree.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="Emit findings as JSON instead of human-readable lines.",
    )
    return parser.parse_args(argv)


def main(argv=None):
    """Run the gate and return a process exit status.

    Args:
        argv: Optional list of argument strings, excluding the program name.

    Returns:
        int: 0 when every fitness function passes, 1 otherwise.
    """
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    plugin_root = Path(args.plugin_root)
    findings = run_all(plugin_root)
    if args.as_json:
        payload = {
            "plugin_root": str(plugin_root),
            "passed": not findings,
            "discovery_trace": discovery_trace(plugin_root) if plugin_root.is_dir() else {},
            "findings": [f.as_dict() for f in findings],
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 1 if findings else 0
    print("Plugin conformance gate: {0}".format(plugin_root))
    if plugin_root.is_dir():
        for name, present in sorted(discovery_trace(plugin_root).items()):
            print("  discovery {0:<16} {1}".format(name, "FOUND" if present else "-"))
    if not findings:
        print("PASS: FF-1 manifest, FF-2 zero hooks, FF-3 zero bundled MCP, " "FF-4 discovery layout")
        return 0
    print("FAIL: {0} finding(s)".format(len(findings)))
    for finding in findings:
        print("  {0}".format(finding))
    return 1


if __name__ == "__main__":
    sys.exit(main())

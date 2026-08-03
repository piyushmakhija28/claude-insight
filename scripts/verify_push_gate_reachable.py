"""Assert the version-push gate survives PreToolUse deletion (PRD FR-23, ADR-017).

This is the CI-blocking fitness function HLD v2 section 7.7 specifies as
``assert_push_gate_reachable()``. It is the third of the three deliverables that
``docs/phase-6-sprint/sequencing_risks.md`` R-1 names as jointly blocking PRD
FR-4 -- the deletion of the PreToolUse and PostToolUse registrations -- and it is
the only one of the three that enforces the ordering mechanically rather than by
review.

FF-1 REACHABILITY (severity CRITICAL)
    The build fails IFF the PreToolUse registration is absent AND no MCP tool
    named as the version-push gate is reachable. Both halves of that
    biconditional are load-bearing and are enumerated as a four-cell truth table
    in ``tests/test_push_gate_reachable.py``.

    THE POLARITY IS THE ENTIRE DESIGN. A check that failed whenever the
    PreToolUse registration was absent would satisfy a careless reading of the
    same sentence and would block the very deletion this gate exists to make
    safe. ADR-017 calls the correct polarity MONOTONE: it can only be satisfied
    by building the replacement, and it stays satisfied forever afterwards.

    WHAT THIS CHECK MUST NEVER LOOK AT. ADR-017 and HLD 7.7 both state that this
    assertion MUST NOT assert on the presence of ``hooks/pre_tool_enforcer/``.
    It therefore reasons about the registration recorded in a settings file and
    about the replacement's own reachability. It never stats a path under
    ``hooks/``. Those two facts come apart in both directions: the directory can
    survive a commit that removes the registration, and a registration can name
    a script that is already gone. ``TestIgnoresTheHookDirectory`` proves the
    verdict does not move when the directory is created and removed.

FF-2 EQUIVALENCE EVIDENCE (severity ERROR)
    ``tests/test_push_gate_mcp_tool.py`` carries the corpus proving the MCP tool
    is equivalent to the hook policy it replaces, together with the
    ``ASSERTION_MAP`` recording which of the hook suite's 23 assertions were
    carried over and which were not. Two of that module's classes SELF-SKIP the
    moment the hook policy file disappears, which is correct while the file
    still exists and dangerous afterwards: the natural way to write the deletion
    commit is to remove the hook and its tests together, at which point the
    equivalence record vanishes with no test failing anywhere.

    V2-024 recorded that obligation and handed it here explicitly. FF-2 is that
    obligation made mechanical. It asserts the record still exists and still
    holds 23 entries composed 17/4/2. It does NOT require the hook to exist, so
    it constrains how the deletion is written without ever blocking it.

    FF-2 IS BEYOND THE ISSUE'S ACCEPTANCE CRITERIA and is labelled as such
    wherever it is reported.

WHY THIS TAKES ARGUMENTS WHEN HLD 7.7 WRITES IT WITH NONE
    HLD 7.7 gives the signature as ``assert_push_gate_reachable() -> None``. A
    zero-argument function must resolve a settings file internally, which would
    make the test suite's result depend on whatever the machine running it has
    in ``~/.claude/settings.json`` -- a file that is edited by hand and is not
    version controlled. ``settings`` is therefore a REQUIRED parameter, so the
    caller cannot avoid deciding, and the default lives in the command-line
    layer where it is visible. The return type is unchanged: None on pass, a
    raised ``PushGateUnreachable`` on fail.

WHICH SETTINGS FILE THE COMMAND LINE DEFAULTS TO, AND WHY THAT ONE
    ``.claude/settings.local.json``, the repository's own tracked file. Not
    ``~/.claude/settings.json``. MEASURED 2026-08-03: that user-scope file
    carries a live PreToolUse entry, so defaulting to it would put this gate in
    the registration-present half of the truth table, where it passes whatever
    the replacement does -- vacuous today and flipping the moment its owner
    edits a file CI cannot see. The tracked file declares an empty hooks block,
    so the gate runs in the registration-absent half from its first run, which
    is the post-deletion steady state. The gate is live-fire now rather than
    dormant until PRD FR-4 lands.

Windows-safe: ASCII only, no Unicode characters.
"""

import argparse
import ast
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SETTINGS_PATH = REPO_ROOT / ".claude" / "settings.local.json"
DEFAULT_CATALOGUE_PATH = REPO_ROOT / "plugin" / "mcp-registry.json"
DEFAULT_EVIDENCE_PATH = REPO_ROOT / "tests" / "test_push_gate_mcp_tool.py"

PUSH_GATE_CAPABILITY = "version-push-gate"
PUSH_GATE_TOOL_NAME = "check_push_allowed"
PROTOCOL_VERSION = "2025-06-18"
SPAWN_TIMEOUT_SECONDS = 90

EVIDENCE_SYMBOL = "ASSERTION_MAP"
EVIDENCE_TOTAL = 23
EVIDENCE_COMPOSITION = {"VERBATIM": 17, "EQUIVALENT": 4, "NOT CARRIED": 2}

RULE_REACHABILITY = "ADR-017/FR-23"
RULE_EVIDENCE = "V2-024-handoff"


class PushGateUnreachable(Exception):
    """The version-push gate has neither a hook registration nor a reachable tool."""


class Finding:
    """A single conformance violation with the rule and evidence that produced it.

    Attributes:
        check: Identifier of the fitness function that produced the finding.
        severity: Either "CRITICAL" or "ERROR".
        rule: The decision record or requirement the finding violates.
        message: One-line statement of what is wrong.
        path: Repository-relative path of the offending artefact, or None.
    """

    def __init__(self, check, severity, rule, message, path=None):
        """Store the finding's fields verbatim.

        Args:
            check: Fitness function identifier, for example "FF-1".
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
        location = self.path if self.path else "(configuration)"
        return "[{0}] {1} {2} {3}: {4}".format(self.severity, self.check, self.rule, location, self.message)


class Reachability:
    """The measured answer to whether a version-push-gate tool can be reached.

    Attributes:
        reachable: True when a tool named as the version-push gate answered.
        detail: One line describing how the answer was reached, in both the
            positive and the negative case, so a failure names its own cause.
        tools: Tool names the server advertised, empty when none were obtained.
    """

    def __init__(self, reachable, detail, tools=()):
        """Store the probe outcome.

        Args:
            reachable: Boolean outcome.
            detail: Explanation of how the outcome was determined.
            tools: Iterable of advertised tool names.
        """
        self.reachable = bool(reachable)
        self.detail = detail
        self.tools = tuple(tools)

    def as_dict(self):
        """Return the outcome as a plain dictionary for JSON output.

        Returns:
            dict: Keys reachable, detail, tools.
        """
        return {"reachable": self.reachable, "detail": self.detail, "tools": list(self.tools)}


def registration_present(settings):
    """Report whether a settings structure declares a non-empty PreToolUse hook.

    The argument may be a parsed mapping or a path. Nothing is read from disk
    unless a path is supplied, and no path is ever chosen by this function, so a
    caller cannot accidentally consult a machine-specific file.

    An absent or unparseable settings file counts as no registration. That is
    the safe direction: it pushes the verdict onto the replacement's
    reachability rather than granting a pass on a file that could not be read.

    Args:
        settings: Parsed settings mapping, or a path to a JSON settings file.

    Returns:
        bool: True when hooks.PreToolUse is present and non-empty.
    """
    if isinstance(settings, (str, Path)):
        try:
            parsed = json.loads(Path(settings).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return False
    else:
        parsed = settings
    if not isinstance(parsed, dict):
        return False
    hooks = parsed.get("hooks")
    if not isinstance(hooks, dict):
        return False
    return bool(hooks.get("PreToolUse"))


def load_catalogue(catalogue_path):
    """Read the registrable-server catalogue.

    Args:
        catalogue_path: Path of the mcp-registry.json catalogue.

    Returns:
        list: Server descriptor mappings, empty when the file is unusable.
    """
    try:
        data = json.loads(Path(catalogue_path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    servers = data.get("servers")
    return servers if isinstance(servers, list) else []


def push_gate_descriptor(catalogue):
    """Return the catalogue entry carrying the version-push-gate capability.

    Keyed off the capability rather than a server id, so the catalogue stays the
    single source of truth for which server carries the gate. This mirrors
    ``plugin/scripts/mcp_registration.py``, which resolves the same question the
    same way.

    Args:
        catalogue: Server descriptor mappings.

    Returns:
        dict or None: The matching descriptor, or None when none declares it.
    """
    for server in catalogue:
        if isinstance(server, dict) and server.get("capability") == PUSH_GATE_CAPABILITY:
            return server
    return None


def resolve_entry_point(descriptor, repo_root):
    """Locate the entry script of the version-push-gate server.

    Registration resolves an entry as ``<server root>/<repo>/<entry>``, where the
    server root holds the checkouts side by side. The push-gate server is the one
    catalogue entry that lives inside this repository rather than in a sibling
    ``mcp-*`` checkout, so the in-repository location is tried first and the
    sibling-checkout convention second. Trying both means a CI checkout whose
    directory name differs from the repository name still resolves.

    Args:
        descriptor: Catalogue descriptor of the push-gate server.
        repo_root: Path of this repository's root.

    Returns:
        Path or None: The entry script, or None when neither location holds it.
    """
    if not isinstance(descriptor, dict) or not descriptor.get("entry"):
        return None
    entry = str(descriptor["entry"])
    root = Path(repo_root)
    in_repo = root / entry
    if in_repo.is_file():
        return in_repo
    sibling = root.parent / str(descriptor.get("repo", "")) / entry
    if sibling.is_file():
        return sibling
    return None


def _handshake_messages():
    """Build the JSON-RPC lines that initialise a server and list its tools.

    Returns:
        list: Message mappings in send order.
    """
    return [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": PROTOCOL_VERSION}},
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
    ]


def _advertised_tools(entry_point):
    """Spawn the server and return the tool names it advertises.

    Args:
        entry_point: Path of the server's entry script.

    Returns:
        tuple: (tool name list, error string or None).
    """
    payload = "\n".join(json.dumps(message) for message in _handshake_messages()) + "\n"
    try:
        process = subprocess.run(
            [sys.executable, str(entry_point)],
            input=payload,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=SPAWN_TIMEOUT_SECONDS,
        )
    except OSError as exc:
        return [], "server could not be spawned: {0}".format(exc)
    except subprocess.TimeoutExpired:
        return [], "server did not answer within {0}s".format(SPAWN_TIMEOUT_SECONDS)
    if process.returncode != 0:
        return [], "server exited {0}: {1}".format(process.returncode, (process.stderr or "").strip()[:200])
    for line in process.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            message = json.loads(line)
        except ValueError:
            continue
        if message.get("id") == 2 and isinstance(message.get("result"), dict):
            tools = message["result"].get("tools")
            if isinstance(tools, list):
                return [tool.get("name") for tool in tools if isinstance(tool, dict)], None
    return [], "server answered the handshake but listed no tools"


def probe_reachability(catalogue_path=None, repo_root=None, tool_name=PUSH_GATE_TOOL_NAME):
    """Measure whether a tool named as the version-push gate can be reached.

    Reachability is established by spawning the real server process and driving a
    real JSON-RPC lifecycle against it, never by importing a module and asserting
    that it exists. A module that imports is not evidence that a session could
    ever call the tool; a completed handshake that lists the name is.

    Args:
        catalogue_path: Catalogue to resolve the server from.
        repo_root: Repository root used to resolve the entry point.
        tool_name: Tool name that must be advertised.

    Returns:
        Reachability: The measured outcome with its explanation.
    """
    catalogue_path = DEFAULT_CATALOGUE_PATH if catalogue_path is None else catalogue_path
    repo_root = REPO_ROOT if repo_root is None else repo_root

    descriptor = push_gate_descriptor(load_catalogue(catalogue_path))
    if descriptor is None:
        return Reachability(
            False,
            "no catalogue entry declares the {0} capability in {1}".format(
                PUSH_GATE_CAPABILITY, Path(catalogue_path).as_posix()
            ),
        )
    entry_point = resolve_entry_point(descriptor, repo_root)
    if entry_point is None:
        return Reachability(
            False,
            "the {0} entry names {1!r}, which exists at neither the in-repository "
            "nor the sibling-checkout location".format(PUSH_GATE_CAPABILITY, descriptor.get("entry")),
        )
    tools, error = _advertised_tools(entry_point)
    if error is not None:
        return Reachability(False, "{0} at {1}".format(error, entry_point.as_posix()))
    if tool_name not in tools:
        return Reachability(
            False,
            "{0} answered but advertises {1}, not {2!r}".format(entry_point.as_posix(), sorted(tools), tool_name),
            tools,
        )
    return Reachability(
        True,
        "{0!r} is advertised by {1} over a completed JSON-RPC handshake".format(tool_name, entry_point.as_posix()),
        tools,
    )


def assert_push_gate_reachable(settings, reachability=None):
    """Fail the build IFF no version-push gate survives, by either mechanism.

    HLD v2 section 7.7, verbatim: fails the build IFF the PreToolUse
    registration is absent AND no MCP tool named as the version-push gate is
    reachable. The condition is a biconditional, so three of its four cells must
    pass. In particular the cell where the registration is absent and the tool IS
    reachable must pass: that is the post-deletion steady state PRD FR-4
    produces, and a check that failed there would block the deletion it exists to
    protect.

    Nothing here consults ``hooks/pre_tool_enforcer/``, per ADR-017.

    Args:
        settings: Parsed settings mapping, or a path to a JSON settings file.
            Required rather than defaulted, so no caller can silently depend on
            a machine-specific file.
        reachability: A pre-measured Reachability, or None to probe now.

    Returns:
        None: When at least one mechanism holds the gate.

    Raises:
        PushGateUnreachable: When the registration is absent and no tool named as
            the version-push gate is reachable.
    """
    registered = registration_present(settings)
    measured = probe_reachability() if reachability is None else reachability
    if registered or measured.reachable:
        return None
    raise PushGateUnreachable(
        "no version-push gate survives: the PreToolUse registration is absent "
        "and no MCP tool named as the version-push gate is reachable ({0}). "
        "PRD FR-23 requires the MCP replacement to be reachable before PRD FR-4 "
        "removes the hook registration; see ADR-017 and sequencing_risks.md R-1.".format(measured.detail)
    )


def check_reachability(settings, reachability=None):
    """Run FF-1 and return it as findings rather than as an exception.

    Args:
        settings: Parsed settings mapping, or a path to a JSON settings file.
        reachability: A pre-measured Reachability, or None to probe now.

    Returns:
        list: Finding objects, empty when the gate holds.
    """
    try:
        assert_push_gate_reachable(settings, reachability=reachability)
    except PushGateUnreachable as exc:
        return [Finding("FF-1", "CRITICAL", RULE_REACHABILITY, str(exc))]
    return []


def _assertion_map_dispositions(evidence_path):
    """Extract the equivalence record's dispositions without importing the module.

    The module is parsed rather than imported because importing a test module
    executes its collection-time code and pulls in pytest, neither of which this
    gate should require in order to answer a question about the file's contents.

    Args:
        evidence_path: Path of the module carrying the equivalence record.

    Returns:
        tuple: (list of disposition strings, error string or None).
    """
    try:
        source = Path(evidence_path).read_text(encoding="utf-8")
    except OSError as exc:
        return [], "cannot be read: {0}".format(exc)
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        return [], "does not parse: {0}".format(exc)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        targets = [t.id for t in node.targets if isinstance(t, ast.Name)]
        if EVIDENCE_SYMBOL not in targets or not isinstance(node.value, ast.Dict):
            continue
        dispositions = []
        for value in node.value.values:
            parts = [n.value for n in ast.walk(value) if isinstance(n, ast.Constant) and isinstance(n.value, str)]
            dispositions.append(" ".join(parts))
        return dispositions, None
    return [], "no {0} assignment found".format(EVIDENCE_SYMBOL)


def check_equivalence_evidence(evidence_path=None):
    """Run FF-2: the hook-to-MCP equivalence record must outlive the hook.

    Two classes in the evidence module self-skip once the hook policy file is
    gone, so after PRD FR-4 nothing in the suite fails if the module is deleted
    outright. This check is what fails instead. It never asks whether the hook
    exists, so it constrains how the deletion is written without blocking it.

    This check is beyond the acceptance criteria of the issue that introduced
    this gate, and is reported as such.

    Args:
        evidence_path: Module carrying the equivalence record.

    Returns:
        list: Finding objects, empty when the record is intact.
    """
    evidence_path = DEFAULT_EVIDENCE_PATH if evidence_path is None else evidence_path
    relative = Path(evidence_path).name
    if not Path(evidence_path).is_file():
        return [
            Finding(
                "FF-2",
                "ERROR",
                RULE_EVIDENCE,
                "the hook-to-MCP equivalence record is gone. Two of its classes "
                "self-skip once the hook policy file is deleted, so removing this "
                "module alongside the hook destroys the equivalence evidence "
                "without failing any test. Keep the module and its ASSERTION_MAP.",
                relative,
            )
        ]
    dispositions, error = _assertion_map_dispositions(evidence_path)
    if error is not None:
        return [Finding("FF-2", "ERROR", RULE_EVIDENCE, "the equivalence record {0}".format(error), relative)]
    if len(dispositions) != EVIDENCE_TOTAL:
        return [
            Finding(
                "FF-2",
                "ERROR",
                RULE_EVIDENCE,
                "the equivalence record holds {0} entries, expected {1} -- one per "
                "assertion in the hook suite it carries over".format(len(dispositions), EVIDENCE_TOTAL),
                relative,
            )
        ]
    findings = []
    for label, expected in sorted(EVIDENCE_COMPOSITION.items()):
        actual = sum(1 for text in dispositions if label in text)
        if actual != expected:
            findings.append(
                Finding(
                    "FF-2",
                    "ERROR",
                    RULE_EVIDENCE,
                    "the equivalence record marks {0} entries {1!r}, expected {2}".format(actual, label, expected),
                    relative,
                )
            )
    return findings


def run_all(settings_path=None, catalogue_path=None, evidence_path=None, repo_root=None, skip_evidence=False):
    """Run every fitness function and return their findings in check order.

    Args:
        settings_path: Settings file to read the registration from.
        catalogue_path: Catalogue to resolve the push-gate server from.
        evidence_path: Module carrying the equivalence record.
        repo_root: Repository root used to resolve the entry point.
        skip_evidence: When True, run FF-1 only.

    Returns:
        tuple: (list of Finding, Reachability, bool registration present).
    """
    settings_path = DEFAULT_SETTINGS_PATH if settings_path is None else settings_path
    measured = probe_reachability(catalogue_path=catalogue_path, repo_root=repo_root)
    registered = registration_present(settings_path)
    findings = check_reachability(settings_path, reachability=measured)
    if not skip_evidence:
        findings.extend(check_equivalence_evidence(evidence_path))
    return findings, measured, registered


def _parse_args(argv):
    """Parse command-line arguments.

    Args:
        argv: List of argument strings, excluding the program name.

    Returns:
        argparse.Namespace: Parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description="Assert a version-push gate survives PreToolUse deletion (ADR-017, PRD FR-23)."
    )
    parser.add_argument(
        "--settings",
        default=str(DEFAULT_SETTINGS_PATH),
        help="Settings file to read the PreToolUse registration from. Defaults "
        "to the repository's tracked .claude/settings.local.json, never the "
        "user-scope file.",
    )
    parser.add_argument(
        "--catalogue",
        default=str(DEFAULT_CATALOGUE_PATH),
        help="Server catalogue used to resolve the version-push-gate entry point.",
    )
    parser.add_argument(
        "--evidence",
        default=str(DEFAULT_EVIDENCE_PATH),
        help="Module carrying the hook-to-MCP equivalence record (FF-2).",
    )
    parser.add_argument(
        "--repo-root",
        default=str(REPO_ROOT),
        help="Repository root used to resolve the server entry point.",
    )
    parser.add_argument(
        "--skip-evidence",
        action="store_true",
        help="Run FF-1 only, omitting the FF-2 equivalence-record check.",
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
    findings, measured, registered = run_all(
        settings_path=args.settings,
        catalogue_path=args.catalogue,
        evidence_path=args.evidence,
        repo_root=args.repo_root,
        skip_evidence=args.skip_evidence,
    )
    if args.as_json:
        payload = {
            "settings": Path(args.settings).as_posix(),
            "pre_tool_use_registered": registered,
            "reachability": measured.as_dict(),
            "passed": not findings,
            "findings": [f.as_dict() for f in findings],
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 1 if findings else 0

    print("Push-gate reachability gate (ADR-017 / PRD FR-23)")
    print("  settings          {0}".format(Path(args.settings).as_posix()))
    print("  PreToolUse        {0}".format("REGISTERED" if registered else "ABSENT"))
    print("  MCP push gate     {0}".format("REACHABLE" if measured.reachable else "UNREACHABLE"))
    print("  evidence          {0}".format(measured.detail))
    if not findings:
        checks = "FF-1 reachability" if args.skip_evidence else "FF-1 reachability, FF-2 equivalence record"
        print("PASS: {0}".format(checks))
        return 0
    print("FAIL: {0} finding(s)".format(len(findings)))
    for finding in findings:
        print("  {0}".format(finding))
    return 1


if __name__ == "__main__":
    sys.exit(main())

"""Plugin-attributable uninstall residue (PRD FR-18 / SRS FR-31, issue V2-022).

WHAT THIS MODULE MEASURES, AND WHAT IT REFUSES TO MEASURE
---------------------------------------------------------
SRS FR-31 asks for zero PLUGIN-ATTRIBUTABLE functional residue after uninstall.
The word that carries the whole requirement is *attributable*. Two comparisons
would both report "residue" on this machine today, and both would be wrong:

- WHOLE-FILE EQUALITY against a pre-install snapshot. The owner's live
  ``settings.json`` acquired empty ``enabledPlugins`` and
  ``extraKnownMarketplaces`` keys during the FR-14a spike and has never lost
  them. Those are Claude Code's own bookkeeping, accepted as a host-level
  limitation in ``docs/guides/uninstall-residue.md`` section 6. A byte or object
  comparison calls them our residue.
- NAME MATCHING against the registrable server catalogue. V2-021 measured this
  machine's ``mcpServers`` holding an entry named ``post-tool-tracker`` with no
  ledger beside it. That entry is the user's own. A name-matching check calls it
  our residue and a name-matching cleanup deletes it.

Every check here is therefore driven by the PROVENANCE LEDGER that
``register-mcp`` writes (``mcp_registration.LEDGER_FILE_NAME``), which records
the spec it wrote and, when ``--force`` displaced an entry the user already had,
the displaced spec. The ledger is the only thing that distinguishes our entry
from an identically named one we never wrote.

THREE CLAIMS, KEPT SEPARATE
---------------------------
- REVERSIBLE: the ledger-driven reversal removes exactly the entries the ledger
  claims and restores exactly the entries it displaced. This is what the
  assertions below make.
- ROUND TRIP: a capability flips unreachable -> reachable -> unreachable. Proved
  by ``tests/test_register_mcp.py`` with a real process spawn and a real
  JSON-RPC handshake. NOT re-proved here.
- BYTE-IDENTICAL: NOT claimed, here or anywhere. The writer re-serialises with
  two-space indentation, so a settings file formatted any other way differs in
  bytes after a correct round trip. The mutation test below uses exactly that
  fact to prove a whole-file comparison is the wrong instrument.

WHAT IS BLOCKED
---------------
Acceptance criterion (a) -- no MCP tool the plugin registered remains callable
after ``claude plugin uninstall`` -- requires a live install/uninstall cycle. The
project owner ruled that no such cycle may be run: at user scope it mutates the
owner's live configuration, and at local scope it mutates a git-tracked file in
this repository. That is ADR-020 Path C, and the executable procedure is
``docs/guides/fr31-uninstall-residue-verification.md``.

The live test below is written to run the moment authorisation exists. It skips
LOUDLY rather than passing silently, and a rehearsal test drives the identical
code path with synthetic snapshots so the blocked test's body is proved capable
of both verdicts rather than merely never executed.
"""

import copy
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = REPO_ROOT / "plugin"
SCRIPT_DIR = PLUGIN_ROOT / "scripts"
RUNBOOK_PATH = REPO_ROOT / "docs" / "guides" / "uninstall-residue.md"
PROCEDURE_DOC = REPO_ROOT / "docs" / "guides" / "fr31-uninstall-residue-verification.md"
RUNBOOK_TEST_PATH = Path(__file__).resolve().parent / "test_uninstall_residue_runbook.py"
TESTS_DIR = Path(__file__).resolve().parent

LIVE_INSTALL_ENV = "CWE_ALLOW_LIVE_PLUGIN_INSTALL"
SNAPSHOT_BEFORE_ENV = "CWE_UNINSTALL_SNAPSHOT_BEFORE"
SNAPSHOT_AFTER_ENV = "CWE_UNINSTALL_SNAPSHOT_AFTER"
SNAPSHOT_LEDGER_ENV = "CWE_UNINSTALL_SNAPSHOT_LEDGER"

MCP_BLOCK = "mcpServers"

ACCEPTED_HOST_KEYS = ("enabledPlugins", "extraKnownMarketplaces")

ABSENCE_ASSERTION_RE = re.compile(
    r"assert\s+not\b|assert\s+.*\bis\s+False\b|assert\s+.*==\s*False\b|assertFalse\s*\(",
)

CACHE_RESIDUE_TOKENS = ("plugins/cache", "plugins\\cache", ".orphaned_at")


def _load(name, path):
    """Import a module by explicit file path.

    ``plugin/scripts`` is not an importable package and ``tests`` is not one
    either, so both are loaded by location. This mirrors the loader in
    ``tests/test_register_mcp.py`` rather than relying on whatever pytest
    happened to put on ``sys.path`` for this invocation.

    Args:
        name: Module name to register under.
        path: Filesystem path of the module.

    Returns:
        module: The loaded module.
    """
    if str(SCRIPT_DIR) not in sys.path:
        sys.path.insert(0, str(SCRIPT_DIR))
    spec = importlib.util.spec_from_file_location(name, str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


registration = _load("mcp_registration_for_residue", SCRIPT_DIR / "mcp_registration.py")
runbook_checks = _load("uninstall_residue_runbook_checks", RUNBOOK_TEST_PATH)


def _guarded_settings_paths():
    """List every live settings file that no test in this module may write.

    Three files, not two. ``tests/test_register_mcp.py`` guards the user-scope
    ``settings.json`` and the repository's git-tracked
    ``.claude/settings.local.json``, and misses the user-scope
    ``settings.local.json``, which is a real file on this machine. Both the
    resolver's Claude home and the plain home directory are consulted, because
    the resolver honours a ``CLAUDE_HOME`` override and a guard that follows the
    override would stop protecting the file it exists to protect.

    Returns:
        list: Absolute paths, de-duplicated, order stable.
    """
    homes = [Path.home() / ".claude"]
    try:
        from utils.path_resolver import get_claude_home

        homes.append(Path(get_claude_home()))
    except Exception:
        pass

    candidates = []
    for home in homes:
        candidates.append(home / "settings.json")
        candidates.append(home / "settings.local.json")
    candidates.append(REPO_ROOT / ".claude" / "settings.local.json")

    seen = []
    for candidate in candidates:
        resolved = candidate.resolve() if candidate.exists() else candidate
        if resolved not in seen:
            seen.append(resolved)
    return seen


def _digest(path):
    """Return the sha256 of a file, or a marker when it is absent.

    Args:
        path: File to digest.

    Returns:
        str: Hex digest, or ``ABSENT``.
    """
    try:
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()
    except FileNotFoundError:
        return "ABSENT"


@pytest.fixture(scope="module", autouse=True)
def live_settings_are_never_touched():
    """Fail the module if any live settings file changes while it runs.

    Yields:
        None
    """
    paths = _guarded_settings_paths()
    before = {path.as_posix(): _digest(path) for path in paths}
    yield
    after = {path.as_posix(): _digest(path) for path in paths}
    assert before == after, "a test modified a live settings file: {0} -> {1}".format(before, after)


def ledger_records(ledger):
    """Return the registration records a parsed ledger document carries.

    Args:
        ledger: Parsed ledger document, or any non-conforming value.

    Returns:
        dict: Server id to record. An absent or malformed ledger yields an empty
        mapping, which makes every check below claim nothing.
    """
    if not isinstance(ledger, dict):
        return {}
    entries = ledger.get("registered")
    return entries if isinstance(entries, dict) else {}


def _mcp_block(settings):
    """Return the mcpServers block of a settings object.

    Args:
        settings: Parsed settings dictionary.

    Returns:
        dict: The block, or an empty mapping when absent or malformed.
    """
    if not isinstance(settings, dict):
        return {}
    block = settings.get(MCP_BLOCK)
    return block if isinstance(block, dict) else {}


def expected_after_reversal(before, ledger):
    """Build the settings object a correct ledger-driven reversal would produce.

    Reversal is not always deletion. Where the ledger records a ``displaced``
    spec, ``register-mcp --force`` took a name the user already held, and
    reversing means putting the user's entry back under that name. Deleting it
    would make ``--force`` a one-way door while still being described as
    reversible.

    Args:
        before: Settings object as it stood when uninstall began.
        ledger: Parsed provenance ledger.

    Returns:
        dict: The expected post-reversal settings object.
    """
    result = copy.deepcopy(before) if isinstance(before, dict) else {}
    block = dict(_mcp_block(result))
    for server_id, record in ledger_records(ledger).items():
        displaced = record.get("displaced") if isinstance(record, dict) else None
        if isinstance(displaced, dict):
            block[server_id] = displaced
        else:
            block.pop(server_id, None)
    if block:
        result[MCP_BLOCK] = block
    else:
        result.pop(MCP_BLOCK, None)
    return result


def attributable_residue(before, after, ledger):
    """Report entries this plugin wrote that survived the uninstall unreversed.

    An entry counts as residue only when the ledger claims its id AND the value
    still present is the spec the ledger says this command wrote. An entry whose
    id the ledger does not claim is never residue, however closely its name
    matches the registrable catalogue -- that is the ``post-tool-tracker``
    -without-a-ledger case V2-021 measured on a live machine.

    ``register-mcp`` records ``displaced`` only when the pre-existing entry
    differed from the spec it was about to write, so a displaced spec can never
    be equal to our spec and the two branches below cannot collide.

    Args:
        before: Settings object as it stood when uninstall began.
        after: Settings object after the uninstall.
        ledger: Parsed provenance ledger.

    Returns:
        list: One message per surviving plugin-attributable entry.
    """
    actual = _mcp_block(after)
    records = ledger_records(ledger)
    problems = []
    for server_id in sorted(records):
        record = records[server_id] if isinstance(records[server_id], dict) else {}
        spec = record.get("spec")
        if server_id in actual and actual[server_id] == spec:
            problems.append(
                "{0}: the mcpServers entry register-mcp wrote is still present after uninstall".format(server_id)
            )
    return problems


def collateral_damage(before, after, ledger):
    """Report changes the plugin had no provenance claim to make.

    Two shapes, both over-removal in the sense ADR-020 and the packaging skill
    use the term:

    - an ``mcpServers`` entry the ledger does not claim was added, removed or
      altered;
    - an entry the ledger records as ``displaced`` was not put back.

    Args:
        before: Settings object as it stood when uninstall began.
        after: Settings object after the uninstall.
        ledger: Parsed provenance ledger.

    Returns:
        list: One message per unclaimed change.
    """
    records = ledger_records(ledger)
    prior = _mcp_block(before)
    actual = _mcp_block(after)
    problems = []
    for server_id in sorted(set(prior) | set(actual)):
        if server_id in records:
            record = records[server_id] if isinstance(records[server_id], dict) else {}
            displaced = record.get("displaced")
            if isinstance(displaced, dict) and actual.get(server_id) != displaced:
                problems.append(
                    "{0}: the entry register-mcp --force displaced was not restored; "
                    "the user's own configuration was lost".format(server_id)
                )
            continue
        if prior.get(server_id) != actual.get(server_id):
            problems.append(
                "{0}: an mcpServers entry this plugin never claimed changed "
                "(before={1!r}, after={2!r})".format(server_id, prior.get(server_id), actual.get(server_id))
            )
    return problems


def unattributable_changes(before, after, ledger):
    """Describe top-level settings changes outside the plugin's provenance.

    This is REPORTED, never asserted on. ``enabledPlugins`` and
    ``extraKnownMarketplaces`` land here: ``claude plugin uninstall`` empties
    them and leaves them in place, which is the accepted Claude-Code-level
    limitation recorded in ``docs/guides/uninstall-residue.md`` section 6. A
    check that failed on them would be asserting the host's behaviour is a
    defect in this plugin.

    Args:
        before: Settings object as it stood when uninstall began.
        after: Settings object after the uninstall.
        ledger: Parsed provenance ledger, accepted for signature symmetry.

    Returns:
        dict: ``added``, ``removed`` and ``changed`` top-level key names.
    """
    prior = before if isinstance(before, dict) else {}
    actual = after if isinstance(after, dict) else {}
    prior_keys = set(prior) - {MCP_BLOCK}
    actual_keys = set(actual) - {MCP_BLOCK}
    return {
        "added": sorted(actual_keys - prior_keys),
        "removed": sorted(prior_keys - actual_keys),
        "changed": sorted(key for key in prior_keys & actual_keys if prior[key] != actual[key]),
    }


def audit_uninstall(before, after, ledger):
    """Compute the full plugin-attributable verdict for one uninstall.

    Args:
        before: Settings object as it stood when uninstall began.
        after: Settings object after the uninstall.
        ledger: Parsed provenance ledger.

    Returns:
        dict: ``residue`` and ``damage`` lists that must both be empty, plus a
        ``host`` mapping that is reported and never asserted.
    """
    return {
        "residue": attributable_residue(before, after, ledger),
        "damage": collateral_damage(before, after, ledger),
        "host": unattributable_changes(before, after, ledger),
    }


def whole_file_equality_verdict(before, after):
    """The comparison acceptance criterion (b) forbids, kept so it can be shown wrong.

    This exists only as the mutant for the mutation test. It is never used by any
    assertion about real residue.

    Args:
        before: Settings bytes or object as it stood when uninstall began.
        after: Settings bytes or object after the uninstall.

    Returns:
        list: A single message when the two differ at all, else empty.
    """
    if before == after:
        return []
    return ["settings.json differs from the pre-install snapshot"]


def _spec(entry_path):
    """Build an mcpServers entry value of the shape register-mcp writes.

    Args:
        entry_path: Path string the spawned server would run.

    Returns:
        dict: The entry value.
    """
    return {"command": "python", "args": [entry_path], "env": {}}


def _ledger(**records):
    """Build a parsed ledger document from keyword records.

    Args:
        **records: Server id to record mapping.

    Returns:
        dict: A ledger document in the shape ``write_ledger`` produces.
    """
    return {"what_this_is": "test fixture", "registered": dict(records)}


@pytest.fixture()
def server_root(tmp_path):
    """Create a directory holding a runnable stand-in for each catalogued server.

    Args:
        tmp_path: pytest-provided temporary directory.

    Returns:
        Path: The server root.
    """
    root = tmp_path / "servers"
    for server in json.loads((PLUGIN_ROOT / "mcp-registry.json").read_text(encoding="utf-8"))["servers"]:
        entry = root / server["repo"] / server["entry"]
        entry.parent.mkdir(parents=True, exist_ok=True)
        entry.write_text("import sys\nsys.exit(0)\n", encoding="utf-8")
    return root


@pytest.fixture()
def settings_file(tmp_path):
    """Create a scratch settings file carrying unrelated content.

    The unrelated keys exist so that a test asserting they survived is asserting
    something. A file containing only ``mcpServers`` could not tell a merge from
    a clobber.

    Args:
        tmp_path: pytest-provided temporary directory.

    Returns:
        Path: The scratch settings file.
    """
    path = tmp_path / "settings.json"
    path.write_text(
        json.dumps(
            {
                "model": "opus",
                "hooks": {"PreToolUse": [{"matcher": "*", "hooks": []}]},
                "mcpServers": {"a-server-the-user-owns": _spec("/somewhere/else/server.py")},
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return path


@pytest.fixture()
def ledger_file(tmp_path):
    """Return the scratch ledger path.

    Args:
        tmp_path: pytest-provided temporary directory.

    Returns:
        Path: The scratch ledger file path.
    """
    return tmp_path / "cwe-mcp-registrations.json"


def _run_cli(args, settings_file, ledger_file):
    """Run the registration command against scratch files only.

    Args:
        args: Sub-command and flags.
        settings_file: Scratch settings path.
        ledger_file: Scratch ledger path.

    Returns:
        subprocess.CompletedProcess: The finished process.
    """
    return subprocess.run(
        [
            sys.executable,
            str(SCRIPT_DIR / "mcp_registration.py"),
            "--settings",
            str(settings_file),
            "--ledger",
            str(ledger_file),
            "--plugin-root",
            str(PLUGIN_ROOT),
        ]
        + args,
        capture_output=True,
        text=True,
        timeout=120,
    )


def _read_json(path, default=None):
    """Read a JSON document, tolerating absence.

    Args:
        path: File to read.
        default: Value returned when the file is absent.

    Returns:
        object: The parsed document, or the default.
    """
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {} if default is None else default


class TestAttributionAgainstARealRegisterUnregisterCycle:
    """The delta is computed from the ledger, against real command output."""

    def test_specificity_a_real_reversal_leaves_no_attributable_residue(self, settings_file, server_root, ledger_file):
        """SPECIFICITY: the correct cycle is judged clean by the real instrument."""
        _run_cli(["register", "--server-root", str(server_root)], settings_file, ledger_file)
        before = _read_json(settings_file)
        ledger = _read_json(ledger_file)
        assert ledger_records(ledger), "the fixture registered nothing; the rest of this test is vacuous"

        _run_cli(["unregister", "--acknowledge-no-push-gate"], settings_file, ledger_file)
        after = _read_json(settings_file)

        verdict = audit_uninstall(before, after, ledger)
        assert verdict["residue"] == []
        assert verdict["damage"] == []

    def test_specificity_the_users_own_entry_survives_and_is_not_claimed(self, settings_file, server_root, ledger_file):
        """SPECIFICITY: an unclaimed entry is neither flagged nor removed."""
        _run_cli(["register", "--server-root", str(server_root)], settings_file, ledger_file)
        before = _read_json(settings_file)
        ledger = _read_json(ledger_file)

        _run_cli(["unregister", "--acknowledge-no-push-gate"], settings_file, ledger_file)
        after = _read_json(settings_file)

        assert "a-server-the-user-owns" in _mcp_block(after)
        assert audit_uninstall(before, after, ledger)["damage"] == []

    def test_a_forced_registration_is_reversed_by_restoring_not_deleting(self, settings_file, server_root, ledger_file):
        """A displaced entry comes back; the audit agrees it came back."""
        original = _spec("/the/users/own/post-tool-tracker.py")
        settings = _read_json(settings_file)
        settings[MCP_BLOCK]["post-tool-tracker"] = original
        settings_file.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")

        _run_cli(["register", "--server-root", str(server_root), "--force"], settings_file, ledger_file)
        before = _read_json(settings_file)
        ledger = _read_json(ledger_file)
        assert ledger["registered"]["post-tool-tracker"].get("displaced") == original

        _run_cli(["unregister", "--acknowledge-no-push-gate"], settings_file, ledger_file)
        after = _read_json(settings_file)

        assert _mcp_block(after)["post-tool-tracker"] == original
        assert audit_uninstall(before, after, ledger) == {
            "residue": [],
            "damage": [],
            "host": {"added": [], "removed": [], "changed": []},
        }


class TestTheCheckCanFail:
    """Every check above is paired with a planted violation it must reject."""

    def test_negative_a_surviving_plugin_entry_is_flagged_as_residue(self):
        """NEGATIVE: our own spec left behind is caught."""
        spec = _spec("/servers/mcp-post-tool-tracker/server.py")
        before = {MCP_BLOCK: {"post-tool-tracker": spec}}
        after = {MCP_BLOCK: {"post-tool-tracker": spec}}
        ledger = _ledger(**{"post-tool-tracker": {"spec": spec}})

        problems = attributable_residue(before, after, ledger)
        assert problems, "a surviving plugin-written entry produced no violation"
        assert any("post-tool-tracker" in problem for problem in problems)

    def test_negative_an_unclaimed_entry_that_vanished_is_flagged_as_damage(self):
        """NEGATIVE: over-removal of a user-owned entry is caught."""
        spec = _spec("/servers/mcp-post-tool-tracker/server.py")
        theirs = _spec("/the/users/own/thing.py")
        before = {MCP_BLOCK: {"post-tool-tracker": spec, "theirs": theirs}}
        after = {MCP_BLOCK: {}}
        ledger = _ledger(**{"post-tool-tracker": {"spec": spec}})

        problems = collateral_damage(before, after, ledger)
        assert problems, "deleting an entry the ledger never claimed produced no violation"
        assert any("theirs" in problem for problem in problems)

    def test_negative_a_displaced_entry_deleted_instead_of_restored_is_flagged(self):
        """NEGATIVE: reversal-by-deletion of a displaced entry is caught.

        This is the failure the ledger's ``displaced`` field exists to prevent,
        and it is invisible to any check that treats reversal as deletion.
        """
        spec = _spec("/servers/mcp-post-tool-tracker/server.py")
        theirs = _spec("/the/users/own/post-tool-tracker.py")
        before = {MCP_BLOCK: {"post-tool-tracker": spec}}
        after = {MCP_BLOCK: {}}
        ledger = _ledger(**{"post-tool-tracker": {"spec": spec, "displaced": theirs}})

        problems = collateral_damage(before, after, ledger)
        assert problems, "a displaced entry that was deleted produced no violation"
        assert any("displaced" in problem for problem in problems)

    def test_specificity_an_identically_named_unclaimed_entry_is_not_residue(self):
        """SPECIFICITY, the half acceptance criterion (b) exists for.

        This reproduces the live condition V2-021 measured: ``mcpServers`` holds
        ``post-tool-tracker`` and no ledger records it. A name-matching check
        calls that our residue. A ledger-driven check does not.
        """
        theirs = _spec("/the/users/own/post-tool-tracker.py")
        before = {MCP_BLOCK: {"post-tool-tracker": theirs}}
        after = {MCP_BLOCK: {"post-tool-tracker": theirs}}

        assert attributable_residue(before, after, _ledger()) == []
        assert collateral_damage(before, after, _ledger()) == []

    def test_specificity_an_entry_matching_the_catalogue_by_name_only_is_not_claimed(self):
        """SPECIFICITY: every catalogued id is safe from a nameless claim."""
        catalogue = json.loads((PLUGIN_ROOT / "mcp-registry.json").read_text(encoding="utf-8"))["servers"]
        theirs = {server["id"]: _spec("/the/users/own/{0}.py".format(server["id"])) for server in catalogue}
        before = {MCP_BLOCK: dict(theirs)}
        after = {MCP_BLOCK: dict(theirs)}

        assert audit_uninstall(before, after, _ledger())["residue"] == []
        assert audit_uninstall(before, after, _ledger())["damage"] == []

    def test_negative_an_empty_ledger_claims_nothing_rather_than_everything(self):
        """NEGATIVE: a malformed ledger must narrow the claim, never widen it."""
        spec = _spec("/servers/mcp-post-tool-tracker/server.py")
        before = {MCP_BLOCK: {"post-tool-tracker": spec}}
        after = {MCP_BLOCK: {"post-tool-tracker": spec}}

        for broken in (None, {}, {"registered": []}, {"registered": "nonsense"}, "not a document"):
            assert attributable_residue(before, after, broken) == []
            assert collateral_damage(before, after, broken) == []


class TestTheAttributionSourceIsTheRealLedger:
    """The checks read the ledger the shipped command actually writes."""

    def test_the_ledger_reader_here_agrees_with_the_shipped_one(self, tmp_path):
        """Drift guard: two readers of one format is one format too many.

        ``ledger_records`` is a second reader of the ledger, so it can drift from
        ``mcp_registration.read_ledger`` and take every check above with it. This
        pins them together across the shapes that matter, including the malformed
        ones where a disagreement would silently widen what unregister touches.
        """
        spec = _spec("/servers/mcp-post-tool-tracker/server.py")
        documents = [
            _ledger(**{"post-tool-tracker": {"spec": spec}}),
            _ledger(**{"post-tool-tracker": {"spec": spec, "displaced": _spec("/theirs.py")}}),
            _ledger(),
            {"registered": []},
            {"registered": "nonsense"},
            {},
        ]

        for index, document in enumerate(documents):
            path = tmp_path / "ledger-{0}.json".format(index)
            path.write_text(json.dumps(document), encoding="utf-8")
            assert ledger_records(document) == registration.read_ledger(path), document

    def test_the_ledger_file_name_is_not_duplicated_from_memory(self):
        """The runbook's R5 path and the shipped constant are the same string."""
        assert registration.LEDGER_FILE_NAME in RUNBOOK_PATH.read_text(encoding="utf-8")

    def test_the_registrable_catalogue_is_the_only_source_of_server_ids(self):
        """No id is hardcoded here that the catalogue does not declare.

        ``push-gate`` is not built yet (V2-024). When it lands it becomes a second
        entry the ledger can claim, and every check above already covers it,
        because they iterate the ledger rather than a fixed list. This test is
        what makes that claim checkable rather than asserted.
        """
        catalogue = json.loads((PLUGIN_ROOT / "mcp-registry.json").read_text(encoding="utf-8"))["servers"]
        declared = {server["id"] for server in catalogue}

        assert "post-tool-tracker" in declared
        assert len(declared) == len(catalogue), "the catalogue declares a duplicate server id"


class TestHostResidueIsReportedNotAsserted:
    """Acceptance criterion (c) at the code level, not only in prose."""

    def test_the_accepted_host_keys_land_in_the_reported_bucket(self):
        """The emptied bookkeeping keys are described, never failed on."""
        before = {"model": "opus"}
        after = dict(before, **{key: {} for key in ACCEPTED_HOST_KEYS})

        verdict = audit_uninstall(before, after, _ledger())

        assert verdict["residue"] == []
        assert verdict["damage"] == []
        assert verdict["host"]["added"] == sorted(ACCEPTED_HOST_KEYS)

    def test_specificity_a_non_host_key_disappearing_is_still_only_reported(self):
        """The reported bucket carries real signal, not just the accepted keys."""
        before = {"model": "opus", "somethingElse": 1}
        after = {"model": "sonnet"}

        host = audit_uninstall(before, after, _ledger())["host"]

        assert host["removed"] == ["somethingElse"]
        assert host["changed"] == ["model"]

    def test_negative_the_reported_bucket_is_empty_when_nothing_outside_mcpservers_moved(self):
        """NEGATIVE: the reporter can return nothing, so a report means something."""
        entry = _spec("/theirs.py")
        before = {"model": "opus", MCP_BLOCK: {"theirs": entry}}
        after = {"model": "opus", MCP_BLOCK: {}}

        assert audit_uninstall(before, after, _ledger())["host"] == {
            "added": [],
            "removed": [],
            "changed": [],
        }


class TestTheForbiddenComparisonIsRejected:
    """MUTATION: substituting whole-file equality must break the suite."""

    def test_mutation_whole_file_equality_flags_the_users_own_entry(self):
        """The mutant reports residue exactly where the real check reports none."""
        theirs = _spec("/the/users/own/post-tool-tracker.py")
        before = {"model": "opus", MCP_BLOCK: {"post-tool-tracker": theirs}}
        after = dict(before, enabledPlugins={}, extraKnownMarketplaces={})

        assert attributable_residue(before, after, _ledger()) == []
        assert collateral_damage(before, after, _ledger()) == []
        assert whole_file_equality_verdict(before, after), "the mutant did not differ from the real check"

    def test_mutation_whole_file_equality_flags_a_formatting_only_round_trip(self, tmp_path, server_root, ledger_file):
        """The mutant fails on a byte difference no claim was ever made about.

        Byte-identical restoration is explicitly not claimed. A four-space
        settings file comes back two-space indented after a correct round trip,
        and the mutant calls that residue.
        """
        path = tmp_path / "settings.json"
        path.write_text(json.dumps({"model": "opus"}, indent=4) + "\n", encoding="utf-8")
        before_bytes = path.read_bytes()

        _run_cli(["register", "--server-root", str(server_root)], path, ledger_file)
        before = _read_json(path)
        ledger = _read_json(ledger_file)
        _run_cli(["unregister", "--acknowledge-no-push-gate"], path, ledger_file)
        after = _read_json(path)
        after_bytes = path.read_bytes()

        assert audit_uninstall(before, after, ledger)["residue"] == []
        assert before_bytes != after_bytes, "the fixture did not produce a formatting difference"
        assert whole_file_equality_verdict(before_bytes, after_bytes)

    def test_mutation_the_two_instruments_agree_on_a_genuine_residue(self):
        """The mutant is not uniformly wrong; it is wrong about attribution.

        Stated so the mutation result is not read as "any difference means the
        mutant is stricter". On a genuine plugin-attributable residue both
        instruments report a problem, which is why only the attribution cases
        above separate them.
        """
        spec = _spec("/servers/mcp-post-tool-tracker/server.py")
        before = {MCP_BLOCK: {"post-tool-tracker": spec}}
        after = {MCP_BLOCK: {"post-tool-tracker": spec}, "enabledPlugins": {}}

        assert attributable_residue(before, after, _ledger(**{"post-tool-tracker": {"spec": spec}}))
        assert whole_file_equality_verdict(before, after)


class TestAcceptedHostLevelLimitation:
    """Acceptance criterion (c): documented, never asserted to be zero."""

    def test_the_runbook_carries_the_anchor_section_v2_022_points_at(self):
        """SPECIFICITY: the sibling module's own check passes on the real file."""
        text = RUNBOOK_PATH.read_text(encoding="utf-8")
        assert runbook_checks.check_limitation_section(text) == []

    def test_the_limitation_section_says_what_the_criterion_requires(self):
        """SPECIFICITY: the real section satisfies every clause of criterion (c)."""
        section = _limitation_section(RUNBOOK_PATH.read_text(encoding="utf-8"))
        assert check_accepted_limitation(section) == []

    @pytest.mark.parametrize(
        "removed,expected",
        [
            ("known and accepted limitations of Claude Code itself", "accepted"),
            (".orphaned_at", "orphaned_at"),
            ("no test in this\nrepository should assert they are absent", "assert"),
        ],
    )
    def test_negative_each_clause_of_the_criterion_is_separately_required(self, removed, expected):
        """NEGATIVE: deleting any one clause is caught, not absorbed by the others."""
        section = _limitation_section(RUNBOOK_PATH.read_text(encoding="utf-8"))
        assert removed in section, "the fixture text is stale: {0!r}".format(removed)

        problems = check_accepted_limitation(section.replace(removed, ""))

        assert problems, "removing {0!r} produced no violation".format(removed)
        assert any(expected in problem for problem in problems), problems

    def test_no_test_in_this_repository_asserts_the_cache_directory_is_absent(self):
        """The criterion's "rather than asserted to be zero", enforced.

        Limitation stated rather than hidden: this is a line-oriented text check.
        It cannot see an absence assertion split across lines or routed through a
        helper, and it is not claimed to.
        """
        offenders = _cache_absence_assertions(TESTS_DIR)
        assert offenders == [], offenders

    def test_negative_a_planted_cache_absence_assertion_is_caught(self, tmp_path):
        """NEGATIVE: the check above can fail.

        The planted line is assembled from parts. Spelling it whole here would
        make this module an offender in its own scan -- the same
        instrument-inside-its-own-scope problem ``scripts/verify_home_paths.py``
        documents and solves the same way.
        """
        token = "plugins/" + "cache"
        planted = tmp_path / "test_planted.py"
        planted.write_text(
            "def test_x():\n    assert not (home / '{0}' / 'x').is_dir()\n".format(token),
            encoding="utf-8",
        )

        offenders = _cache_absence_assertions(tmp_path)
        assert offenders, "a planted absence assertion produced no violation"
        assert any("test_planted.py" in offender for offender in offenders)

    def test_specificity_a_mention_that_is_not_an_absence_assertion_passes(self, tmp_path):
        """SPECIFICITY: naming the path without asserting absence is allowed."""
        token = "plugins/" + "cache"
        allowed = tmp_path / "test_allowed.py"
        allowed.write_text(
            "def test_x():\n    assert '{0}' in runbook_text\n".format(token),
            encoding="utf-8",
        )

        assert _cache_absence_assertions(tmp_path) == []


class TestTheRunbookProcedureRunsFromItsStoredForm:
    """The commands CI proves working are the commands the document ships."""

    def test_the_stored_bookkeeping_removal_step_executes_and_removes_the_keys(self, tmp_path):
        """Run step A3 verbatim out of the runbook against a scratch file."""
        command = _stored_python_command(RUNBOOK_PATH.read_text(encoding="utf-8"), "enabledPlugins")
        target = tmp_path / "settings.json"
        target.write_text(
            json.dumps({"model": "opus", "enabledPlugins": {}, "extraKnownMarketplaces": {}}, indent=2) + "\n",
            encoding="utf-8",
        )

        completed = _run_stored_command(command, target)

        assert completed.returncode == 0, completed.stderr
        remaining = json.loads(target.read_text(encoding="utf-8"))
        assert "enabledPlugins" not in remaining
        assert "extraKnownMarketplaces" not in remaining
        assert remaining["model"] == "opus"

    def test_specificity_the_stored_step_leaves_a_non_empty_key_alone(self, tmp_path):
        """SPECIFICITY: a still-registered plugin is not deregistered by cleanup."""
        command = _stored_python_command(RUNBOOK_PATH.read_text(encoding="utf-8"), "enabledPlugins")
        target = tmp_path / "settings.json"
        target.write_text(
            json.dumps({"enabledPlugins": {"someone-elses@marketplace": True}, "extraKnownMarketplaces": {}}, indent=2)
            + "\n",
            encoding="utf-8",
        )

        completed = _run_stored_command(command, target)

        assert completed.returncode == 0, completed.stderr
        remaining = json.loads(target.read_text(encoding="utf-8"))
        assert remaining["enabledPlugins"] == {"someone-elses@marketplace": True}
        assert "extraKnownMarketplaces" not in remaining

    def test_the_stored_step_is_idempotent_as_the_runbook_claims(self, tmp_path):
        """The document says "yes" under Idempotent; this measures it."""
        command = _stored_python_command(RUNBOOK_PATH.read_text(encoding="utf-8"), "enabledPlugins")
        target = tmp_path / "settings.json"
        target.write_text(json.dumps({"model": "opus", "enabledPlugins": {}}, indent=2) + "\n", encoding="utf-8")

        _run_stored_command(command, target)
        first = target.read_bytes()
        second_run = _run_stored_command(command, target)

        assert second_run.returncode == 0, second_run.stderr
        assert "removed: []" in second_run.stdout
        assert target.read_bytes() == first

    def test_negative_extraction_fails_when_the_stored_command_is_gone(self):
        """NEGATIVE: the extractor cannot silently find nothing and pass."""
        with pytest.raises(AssertionError):
            _stored_python_command("# a runbook with no commands in it\n", "enabledPlugins")


class TestLiveUninstallMeasurement:
    """Acceptance criterion (a): blocked by an owner ruling, not by a limitation."""

    def test_live_uninstall_leaves_zero_attributable_residue(self):
        """Compute the FR-31 verdict from snapshots a live cycle produced.

        This test is complete and runnable. What it does not do, and must not do,
        is perform the install/uninstall cycle itself: the owner ruled that no
        live cycle may be run, because install writes ``enabledPlugins`` and
        ``extraKnownMarketplaces`` into a settings scope and uninstall never
        removes them. The operator performs the authorised half by following
        ``docs/guides/fr31-uninstall-residue-verification.md``, which writes the
        three snapshots this test then judges.
        """
        if not _live_measurement_available():
            pytest.skip(_blocked_reason())

        before = _read_json(os.environ[SNAPSHOT_BEFORE_ENV])
        after = _read_json(os.environ[SNAPSHOT_AFTER_ENV])
        ledger = _read_json(os.environ[SNAPSHOT_LEDGER_ENV])

        assert ledger_records(ledger), (
            "the ledger snapshot claims no registration, so this run measures nothing. "
            "Procedure step 3 did not write an entry; fix --server-root and repeat."
        )

        verdict = audit_uninstall(before, after, ledger)
        assert verdict["residue"] == [], verdict["residue"]
        assert verdict["damage"] == [], verdict["damage"]

    def test_the_blocked_test_body_is_rehearsed_against_both_verdicts(self, tmp_path, monkeypatch):
        """Prove the blocked test computes a verdict rather than never running.

        A skipped test is indistinguishable from a test whose body cannot work.
        This drives the identical snapshot-reading path with synthetic files and
        requires it to produce a clean verdict on a correct reversal and a dirty
        one on a residue.
        """
        spec = _spec("/servers/mcp-post-tool-tracker/server.py")
        ledger_path = tmp_path / "ledger.json"
        ledger_path.write_text(json.dumps(_ledger(**{"post-tool-tracker": {"spec": spec}})), encoding="utf-8")
        before_path = tmp_path / "before.json"
        before_path.write_text(json.dumps({MCP_BLOCK: {"post-tool-tracker": spec}}), encoding="utf-8")

        clean = tmp_path / "after-clean.json"
        clean.write_text(json.dumps({"enabledPlugins": {}}), encoding="utf-8")
        dirty = tmp_path / "after-dirty.json"
        dirty.write_text(json.dumps({MCP_BLOCK: {"post-tool-tracker": spec}, "enabledPlugins": {}}), encoding="utf-8")

        monkeypatch.setenv(LIVE_INSTALL_ENV, "1")
        monkeypatch.setenv(SNAPSHOT_BEFORE_ENV, str(before_path))
        monkeypatch.setenv(SNAPSHOT_LEDGER_ENV, str(ledger_path))

        monkeypatch.setenv(SNAPSHOT_AFTER_ENV, str(clean))
        assert _live_measurement_available()
        self.test_live_uninstall_leaves_zero_attributable_residue()

        monkeypatch.setenv(SNAPSHOT_AFTER_ENV, str(dirty))
        with pytest.raises(AssertionError):
            self.test_live_uninstall_leaves_zero_attributable_residue()

    def test_the_measurement_is_recorded_as_not_performed(self):
        """The blocked state is written down, in the shape V2-016 established."""
        assert PROCEDURE_DOC.is_file(), "missing procedure: {0}".format(PROCEDURE_DOC.as_posix())
        text = PROCEDURE_DOC.read_text(encoding="utf-8")

        assert "NOT PERFORMED" in text
        assert LIVE_INSTALL_ENV in text
        assert SNAPSHOT_BEFORE_ENV in text
        assert SNAPSHOT_AFTER_ENV in text
        assert SNAPSHOT_LEDGER_ENV in text
        assert "test_live_uninstall_leaves_zero_attributable_residue" in text

    def test_the_procedure_document_is_ascii_only(self):
        """The document ships under the same encoding rule as everything else."""
        text = PROCEDURE_DOC.read_text(encoding="utf-8")
        offenders = sorted({character for character in text if ord(character) > 127})
        assert not offenders, offenders

    def test_the_skip_reason_names_the_ruling_and_the_way_forward(self):
        """A skip a reader cannot act on is a silent skip with extra words."""
        reason = _blocked_reason()

        assert "owner" in reason.lower()
        assert LIVE_INSTALL_ENV in reason
        assert PROCEDURE_DOC.name in reason


NO_ASSERTION_RE = re.compile(
    r"no test\b.{0,80}?should assert (?:they|it) (?:are|is) absent",
    re.IGNORECASE | re.DOTALL,
)


def check_accepted_limitation(section):
    """Check the runbook section satisfies every clause of criterion (c).

    Criterion (c) asks for four things, and a section can carry any three of them
    while failing the requirement, so each is a separate check with its own
    negative test.

    Args:
        section: Body of the accepted-limitation section.

    Returns:
        list: One message per unmet clause.
    """
    problems = []
    lowered = section.lower()
    if "accepted limitation" not in lowered or "claude code" not in lowered:
        problems.append("section does not state the items are accepted limitations of Claude Code itself")
    if ".orphaned_at" not in section:
        problems.append("section does not name the .orphaned_at marker file")
    if "~/.claude/plugins/cache/" not in section:
        problems.append("section does not name the orphaned plugin cache directory")
    if NO_ASSERTION_RE.search(section) is None:
        problems.append("section does not state that no test should assert the residue is absent")
    return problems


def _limitation_section(text):
    """Return the body of the runbook's accepted-limitation section.

    Args:
        text: Full runbook text.

    Returns:
        str: Section body up to the next second-level heading.
    """
    match = runbook_checks.LIMITATION_HEADING_PATTERN.search(text)
    assert match is not None, "the runbook has no accepted-limitation heading"
    body = text[match.end() :]
    following = re.search(r"^##\s", body, re.MULTILINE)
    return body[: following.start()] if following else body


def _cache_absence_assertions(root):
    """Find test lines that assert the orphaned cache residue is absent.

    Args:
        root: Directory to scan for ``test_*.py`` files.

    Returns:
        list: ``path:line: text`` records, one per offending line.
    """
    offenders = []
    for path in sorted(Path(root).rglob("test_*.py")):
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeDecodeError):
            continue
        for number, line in enumerate(lines, start=1):
            if not any(token in line for token in CACHE_RESIDUE_TOKENS):
                continue
            if ABSENCE_ASSERTION_RE.search(line):
                offenders.append("{0}:{1}: {2}".format(path.name, number, line.strip()))
    return offenders


def _stored_python_command(text, must_contain):
    """Extract one fenced ``python -c`` command from a markdown document.

    Args:
        text: Full document text.
        must_contain: Substring identifying the wanted command.

    Returns:
        str: The command exactly as the document stores it.

    Raises:
        AssertionError: No stored command matched.
    """
    blocks = re.findall(r"^```\n(python -c .*?)\n```", text, re.MULTILINE | re.DOTALL)
    matching = [block for block in blocks if must_contain in block]
    assert matching, "no stored python command containing {0!r} was found".format(must_contain)
    return matching[0]


def _run_stored_command(command, target):
    """Execute a stored one-liner with its settings argument redirected.

    The runbook's commands end in ``~/.claude/settings.json``. Only that final
    argument is replaced, so the executed body is the shipped body.

    Args:
        command: The stored command string.
        target: Scratch settings file to operate on instead.

    Returns:
        subprocess.CompletedProcess: The finished process.
    """
    body = re.search(r'python -c "(.*)"', command, re.DOTALL)
    assert body is not None, "stored command is not a python -c invocation: {0}".format(command)
    return subprocess.run(
        [sys.executable, "-c", body.group(1), str(target)],
        capture_output=True,
        text=True,
        timeout=120,
    )


def _live_measurement_available():
    """Report whether an authorised live measurement supplied its snapshots.

    Returns:
        bool: True when authorisation and all three snapshot files are present.
    """
    if os.environ.get(LIVE_INSTALL_ENV, "").strip() != "1":
        return False
    for name in (SNAPSHOT_BEFORE_ENV, SNAPSHOT_AFTER_ENV, SNAPSHOT_LEDGER_ENV):
        value = os.environ.get(name, "").strip()
        if not value or not Path(value).is_file():
            return False
    return True


def _blocked_reason():
    """Return the skip message for the blocked live measurement.

    Returns:
        str: A message naming the cause, the criterion and the way forward.
    """
    return (
        "BLOCKED, NOT PASSED. SRS FR-31 acceptance criterion (a) needs a live "
        "claude plugin install followed by claude plugin uninstall. The project "
        "owner ruled that no live cycle may be run: install writes enabledPlugins "
        "and extraKnownMarketplaces into a settings scope and uninstall only "
        "empties them, so at user scope the ruling protects the owner's live "
        "configuration and at local scope a git-tracked file in this repository. "
        "This test is complete and will run as written once an operator with "
        "authorisation follows {0} and exports {1}=1 together with {2}, {3} and "
        "{4}. Do not substitute a hand-edited settings file for the measurement.".format(
            PROCEDURE_DOC.name,
            LIVE_INSTALL_ENV,
            SNAPSHOT_BEFORE_ENV,
            SNAPSHOT_AFTER_ENV,
            SNAPSHOT_LEDGER_ENV,
        )
    )

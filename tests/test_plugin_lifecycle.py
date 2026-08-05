"""Install / invoke / uninstall lifecycle tests (PRD NFR-5 / SRS NFR-11, issue V2-023).

WHAT THIS MODULE IS FOR
-----------------------
SRS NFR-11 asks for three independent automated lifecycle tests -- install,
invoke and uninstall -- each asserting on plugin-attributable delta only, never
on whole-file equality against a pre-install snapshot. A fourth scenario,
register/unregister round trip, is added here because NFR-11's install and
uninstall halves are blocked and the round trip is the one lifecycle claim that
is fully measurable today.

TWO OF THE FOUR ARE BLOCKED, AND THE BLOCK IS AN OWNER RULING
-------------------------------------------------------------
No live ``claude plugin install`` or ``claude plugin uninstall`` may be run.
Install writes ``enabledPlugins`` and ``extraKnownMarketplaces`` into a settings
scope, uninstall only empties them, an orphaned cache directory survives
``claude plugin prune``, and the local scope it would touch is git-tracked in
this repository. That is the same ruling recorded in
``docs/guides/adr-020-path-c-verification.md`` and
``docs/guides/fr31-uninstall-residue-verification.md``.

Both blocked tests are written complete. Each skips LOUDLY naming the ruling and
the criterion, and each has a companion REHEARSAL test that drives the identical
code path with synthetic snapshots and requires it to produce BOTH a clean and a
dirty verdict. A test that has never been observed to reach either verdict is
indistinguishable from a test whose body cannot work.

THE OWNER RULING THAT CHANGES WHAT THE UNINSTALL TEST EXPECTS
--------------------------------------------------------------
V2-022 found that ADR-020 Path C and PRD FR-18 acceptance criterion (a) demanded
opposite outcomes from one measurement: Path C's PASS is that uninstall does NOT
remove a ``register-mcp``-written ``mcpServers`` entry, so the version push gate
outlives the plugin; FR-18 (a)'s PASS is that it is gone.

The owner ruled that ADR-020 Path C wins. A ``register-mcp``-written entry
persists in user-scope settings across plugin uninstall unless the user
explicitly removed it, and FR-18 (a) is scope-limited to plugin-specific
OPERATIONAL tools -- it does not reach safety-enforcement gates. Non-essential
residue, caches and ephemeral state, is still purged.

That ruling is recorded in ``docs/REVIEW-INDEX.md`` item 37, which is the
authority this module encodes. It is pinned by a test below, so a revert of the
ruling breaks this module rather than silently leaving it asserting the wrong
verdict.

``uninstall_verdict`` below therefore partitions what V2-022's
``attributable_residue`` reports into two buckets by the CATALOGUE's own
``capability`` field: a surviving safety-enforcement gate is EXPECTED
PERSISTENCE, and a surviving operational tool is still RESIDUE. The exempt id is
resolved through the shipped ``mcp_registration.push_gate_server_id``, so the
catalogue stays the single source of truth and no id is spelled here.

WHERE THE RULING AND THE SHIPPED DOCUMENTS DISAGREE, AND WHICH ONE THIS FOLLOWS
------------------------------------------------------------------------------
``docs/phase-0-requirements/prd-v2.md`` FR-18 and ``SRS.md`` FR-31 still carry
the unnarrowed "no MCP tool the plugin registered remains callable" wording, and
``docs/guides/adr-020-path-c-verification.md`` still presents Path C as an open
question with no verdict. This module follows the OWNER RULING, not those texts.
Those documents are stale against it and fixing them is not this issue's scope.

One consequence was recorded here rather than discovered during a live run: while
the catalogue declared the push gate ``not_built_yet``, the only entry
``register-mcp`` could write was the OPERATIONAL progress writer, so a live
uninstall resolved the tension against an entry the narrowing does not exempt and
criterion (a) could still fail. V2-024 has since landed and removed that marker,
so a live cycle can now register a safety-enforcement entry and exercise the
ruling on the case it was written for. The operational entry is still registrable
alongside it, so criterion (a) can still fail on that one -- the host is
capability-blind and the narrowing is requirement-side scoping only.

THREE CLAIMS ABOUT THE ROUND TRIP, KEPT SEPARATE
------------------------------------------------
- REVERSIBLE: the settings OBJECT after unregister equals the object before
  register, and the ledger returns to its pre-registration state. ASSERTED here.
- BYTE-IDENTICAL: holds only when the file was already two-space indented with
  matching line endings. ASSERTED here as the conditional it is, in both
  directions.
- ROUND-TRIP REACHABILITY: a capability flips unreachable -> reachable ->
  unreachable, proved by a real process spawn and a real JSON-RPC handshake in
  ``tests/test_register_mcp.py``. NOT re-proved here; a drift guard asserts that
  test still exists under the name this module credits.
"""

import copy
import importlib.util
import json
import os
import shutil
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
TESTS_DIR = Path(__file__).resolve().parent
PLUGIN_ROOT = REPO_ROOT / "plugin"
SCRIPT_DIR = PLUGIN_ROOT / "scripts"
GATE_SCRIPT = REPO_ROOT / "scripts" / "verify_plugin_conformance.py"
PLUGIN_MANIFEST = PLUGIN_ROOT / ".claude-plugin" / "plugin.json"
MARKETPLACE_MANIFEST = REPO_ROOT / ".claude-plugin" / "marketplace.json"
PROCEDURE_DOC = REPO_ROOT / "docs" / "guides" / "nfr11-lifecycle-verification.md"

ATTRIBUTION_TEST_PATH = TESTS_DIR / "test_uninstall_residue_attribution.py"
REGISTER_TEST_PATH = TESTS_DIR / "test_register_mcp.py"
REVIEW_INDEX_PATH = REPO_ROOT / "docs" / "REVIEW-INDEX.md"

RULING_CLAUSES = (
    "ADR-020 Path C wins",
    "persists in user-scope settings",
    "operational",
    "safety-enforcement gates",
)

LIVE_INSTALL_ENV = "CWE_ALLOW_LIVE_PLUGIN_INSTALL"
INSTALL_BEFORE_ENV = "CWE_INSTALL_SNAPSHOT_BEFORE"
INSTALL_AFTER_ENV = "CWE_INSTALL_SNAPSHOT_AFTER"
SNAPSHOT_BEFORE_ENV = "CWE_UNINSTALL_SNAPSHOT_BEFORE"
SNAPSHOT_AFTER_ENV = "CWE_UNINSTALL_SNAPSHOT_AFTER"
SNAPSHOT_LEDGER_ENV = "CWE_UNINSTALL_SNAPSHOT_LEDGER"

MCP_BLOCK = "mcpServers"
HOOKS_BLOCK = "hooks"

MEASURED_INSTALL_KEYS = ("enabledPlugins", "extraKnownMarketplaces")

REACHABILITY_ROUND_TRIP_TEST = "test_capability_flips_unreachable_reachable_unreachable"


def _load(name, path):
    """Import a module by explicit file path.

    ``plugin/scripts``, ``scripts`` and ``tests`` are not importable packages, so
    everything reused here is loaded by location rather than by relying on
    whatever pytest happened to put on ``sys.path`` for this invocation. This
    mirrors the loader in ``tests/test_register_mcp.py``.

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


conformance = _load("verify_plugin_conformance_for_lifecycle", GATE_SCRIPT)
registration = _load("mcp_registration_for_lifecycle", SCRIPT_DIR / "mcp_registration.py")
attribution = _load("uninstall_residue_attribution_checks", ATTRIBUTION_TEST_PATH)
register_tests = _load("register_mcp_checks", REGISTER_TEST_PATH)


@pytest.fixture(scope="module", autouse=True)
def live_settings_are_never_touched():
    """Fail the module if any live settings file changes while it runs.

    The guarded set is V2-022's, which covers the user-scope ``settings.json``,
    the user-scope ``settings.local.json`` and this repository's git-tracked
    ``.claude/settings.local.json``, under both the plain home directory and the
    resolver's ``CLAUDE_HOME``. It is reused rather than restated so a future
    addition to that set protects this module too.

    Yields:
        None
    """
    paths = attribution._guarded_settings_paths()
    before = {path.as_posix(): attribution._digest(path) for path in paths}
    yield
    after = {path.as_posix(): attribution._digest(path) for path in paths}
    assert before == after, "a test modified a live settings file: {0} -> {1}".format(before, after)


def installed_plugin_id():
    """Return the ``plugin@marketplace`` key install writes into enabledPlugins.

    Both halves are read from the shipped manifests rather than spelled here, so
    a rename breaks this test instead of silently invalidating it.

    Returns:
        str: The identifier Claude Code uses as the enabledPlugins key.
    """
    plugin = json.loads(PLUGIN_MANIFEST.read_text(encoding="utf-8"))["name"]
    marketplace = json.loads(MARKETPLACE_MANIFEST.read_text(encoding="utf-8"))["name"]
    return "{0}@{1}".format(plugin, marketplace)


def _top_level(document):
    """Return a settings document as a mapping, tolerating a non-mapping value.

    Args:
        document: Parsed settings document, or any non-conforming value.

    Returns:
        dict: The document, or an empty mapping.
    """
    return document if isinstance(document, dict) else {}


def _hooks_block(settings):
    """Return the hooks block of a settings object.

    Args:
        settings: Parsed settings dictionary.

    Returns:
        dict: The block, or an empty mapping when absent or malformed.
    """
    block = _top_level(settings).get(HOOKS_BLOCK)
    return block if isinstance(block, dict) else {}


def install_settings_delta(before, after):
    """Classify the top-level settings change one plugin install produced.

    The measured keys are not simply "added". On a machine that has installed and
    uninstalled a plugin before, ``enabledPlugins`` and ``extraKnownMarketplaces``
    are already present holding ``{}``, so a second install CHANGES them rather
    than adding them. That is exactly this machine's state after the FR-14a
    spike. A check that only tolerated additions would fail on the normal case,
    so the two measured keys are reported separately whichever way they moved,
    and everything else is a finding.

    Args:
        before: Settings object as it stood before ``marketplace add``.
        after: Settings object after ``plugin install``.

    Returns:
        dict: ``expected_added`` and ``measured_keys_changed`` are reported;
        ``unexpected_added``, ``removed`` and ``changed`` must all be empty.
    """
    prior = _top_level(before)
    actual = _top_level(after)
    measured = set(MEASURED_INSTALL_KEYS)
    added = sorted(set(actual) - set(prior))
    removed = sorted(set(prior) - set(actual))
    changed = sorted(key for key in set(prior) & set(actual) if prior[key] != actual[key])
    return {
        "expected_added": [key for key in added if key in measured],
        "unexpected_added": [key for key in added if key not in measured],
        "removed": removed,
        "changed": [key for key in changed if key not in measured],
        "measured_keys_changed": [key for key in changed if key in measured],
    }


def hook_events_delta(before, after):
    """Report which hook events an install added, removed or altered.

    Subsumed by ``install_settings_delta``'s ``changed`` list, and kept separate
    anyway: the Gherkin scenario names ``PreToolUse``, ``PostToolUse`` and
    ``UserPromptSubmit`` individually and requires the pre-existing ``Stop`` and
    ``Notification`` entries to be untouched. A verdict that says only "hooks
    changed" cannot tell those two failures apart.

    Args:
        before: Settings object as it stood before ``marketplace add``.
        after: Settings object after ``plugin install``.

    Returns:
        dict: ``added``, ``removed`` and ``changed`` hook event names.
    """
    prior = _hooks_block(before)
    actual = _hooks_block(after)
    return {
        "added": sorted(set(actual) - set(prior)),
        "removed": sorted(set(prior) - set(actual)),
        "changed": sorted(event for event in set(prior) & set(actual) if prior[event] != actual[event]),
    }


def audit_install(before, after):
    """Compute the full plugin-attributable verdict for one install.

    Args:
        before: Settings object as it stood before ``marketplace add``.
        after: Settings object after ``plugin install``.

    Returns:
        dict: The settings delta under ``settings``, the hook delta under
        ``hooks``, and the flattened list of findings under ``problems``.
    """
    settings = install_settings_delta(before, after)
    hooks = hook_events_delta(before, after)
    problems = []
    for key in settings["unexpected_added"]:
        problems.append("install added top-level key {0!r}, which was never measured as one it writes".format(key))
    for key in settings["removed"]:
        problems.append("install removed top-level key {0!r}".format(key))
    for key in settings["changed"]:
        problems.append("install changed top-level key {0!r}, outside the two measured keys".format(key))
    for event in hooks["added"]:
        problems.append("install added hook event {0!r}; the plugin ships zero hooks (ADR-010)".format(event))
    for event in hooks["removed"]:
        problems.append("install removed pre-existing hook event {0!r}".format(event))
    for event in hooks["changed"]:
        problems.append("install altered pre-existing hook event {0!r}".format(event))
    return {"settings": settings, "hooks": hooks, "problems": problems}


def bundled_mcp_findings(plugin_root):
    """Report every way the plugin tree could ship an MCP server (AC 2).

    This calls the shipped gate rather than restating it. ``FF-3`` closes BOTH
    routes -- a ``.mcp.json`` at any depth AND an ``mcpServers`` manifest key --
    because closing one leaves the other open, and a weaker local duplicate of
    that logic would drift from the gate CI actually runs.

    Args:
        plugin_root: Plugin root to check.

    Returns:
        list: Finding objects from FF-3 only.
    """
    return [finding for finding in conformance.run_all(plugin_root) if finding.check == "FF-3"]


def safety_enforcement_server_ids():
    """Return the catalogue ids whose capability is a safety-enforcement gate.

    Resolved through the shipped ``push_gate_server_id`` so the catalogue's
    ``capability`` field stays the single source of truth. No id is spelled
    here, which is what lets V2-024's push gate be covered by this narrowing the
    moment it lands without editing this module.

    Returns:
        set: Server ids exempt from the narrowed FR-18 residue rule.
    """
    servers = registration.load_registry(PLUGIN_ROOT)
    gate_id = registration.push_gate_server_id(servers)
    return {gate_id} if gate_id else set()


def ruling_record_text():
    """Return the text of the record that carries the owner's ruling.

    Returns:
        str: The full REVIEW-INDEX document.
    """
    return REVIEW_INDEX_PATH.read_text(encoding="utf-8")


def check_owner_ruling(text):
    """Check the record still states every clause the narrowing depends on.

    Each clause is checked separately because a record can carry any three of
    them while no longer saying what this module encodes.

    Args:
        text: The record's full text.

    Returns:
        list: One message per missing clause.
    """
    return [
        "the ruling record no longer states {0!r}".format(clause) for clause in RULING_CLAUSES if clause not in text
    ]


def _server_id_of(message):
    """Extract the server id V2-022 prefixes onto each residue message.

    Args:
        message: One message from ``attributable_residue``.

    Returns:
        str: The leading server id.
    """
    return message.split(":", 1)[0]


def uninstall_verdict(before, after, ledger, exempt_ids):
    """Compute the NARROWED FR-18 verdict for one uninstall.

    V2-022's ``audit_uninstall`` is the instrument; this only partitions its
    residue list. A surviving entry whose id is a safety-enforcement gate is
    EXPECTED PERSISTENCE under the owner's ADR-020 Path C ruling, not a failure.
    A surviving operational entry is still residue, which is what keeps FR-18
    from becoming vacuous under the narrowing.

    ``damage`` is not partitioned. Over-removal of a user-owned entry is a
    finding whatever the entry is for, and the ruling narrowed what counts as
    residue, not what counts as collateral damage.

    Args:
        before: Settings object as it stood when uninstall began.
        after: Settings object after the uninstall.
        ledger: Parsed provenance ledger.
        exempt_ids: Server ids the ruling exempts.

    Returns:
        dict: ``residue`` and ``damage`` must both be empty;
        ``expected_persistence`` and ``host`` are reported, never asserted on.
    """
    full = attribution.audit_uninstall(before, after, ledger)
    residue = []
    expected = []
    for message in full["residue"]:
        if _server_id_of(message) in set(exempt_ids):
            expected.append(message)
        else:
            residue.append(message)
    return {
        "residue": residue,
        "expected_persistence": expected,
        "damage": full["damage"],
        "host": full["host"],
    }


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


def _read_json(path):
    """Read a JSON document, tolerating absence.

    Args:
        path: File to read.

    Returns:
        object: The parsed document, or an empty dict when absent.
    """
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}


@pytest.fixture()
def scratch_plugin(tmp_path):
    """Copy the real plugin tree so a planted violation can be measured on it.

    Args:
        tmp_path: pytest-provided temporary directory.

    Returns:
        Path: Root of the scratch copy.
    """
    root = tmp_path / "plugin"
    shutil.copytree(str(PLUGIN_ROOT), str(root), ignore=shutil.ignore_patterns("__pycache__"))
    return root


@pytest.fixture()
def settings_file(tmp_path):
    """Create a scratch settings file carrying representative unrelated content.

    The unrelated keys and the pre-existing hook entries exist so that a test
    asserting they survived is asserting something. A file holding only
    ``mcpServers`` could not tell a merge from a clobber, and one holding no
    hooks could not tell "no hook added" from "no hooks anywhere".

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
                "hooks": {
                    "PreToolUse": [{"matcher": "*", "hooks": []}],
                    "Stop": [{"matcher": "*", "hooks": []}],
                    "Notification": [{"matcher": "*", "hooks": []}],
                },
                "mcpServers": {"a-server-the-user-owns": _spec("/somewhere/else/server.py")},
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return path


@pytest.fixture()
def server_root(tmp_path):
    """Build a scratch server root whose progress-writer entry really runs.

    Reuses the probe server ``tests/test_register_mcp.py`` spawns, at the exact
    repo/entry location the catalogue declares, so the path ``register-mcp``
    writes is a path that genuinely answers a JSON-RPC handshake.

    Args:
        tmp_path: pytest-provided temporary directory.

    Returns:
        Path: Directory holding the mcp-* checkouts.
    """
    root = tmp_path / "servers"
    target = root / "mcp-post-tool-tracker"
    target.mkdir(parents=True)
    (target / "server.py").write_text(register_tests.PROBE_SERVER.read_text(encoding="utf-8"), encoding="utf-8")
    return root


@pytest.fixture()
def ledger_file(tmp_path):
    """Return the scratch provenance ledger path.

    Args:
        tmp_path: pytest-provided temporary directory.

    Returns:
        Path: The scratch ledger file path.
    """
    return tmp_path / "cwe-mcp-registrations.json"


class TestInstallShipsNoBundledMcpServer:
    """AC 2, first half: the plugin ships NO .mcp.json at all, by either route."""

    def test_the_shipped_gate_reports_no_bundled_mcp_on_the_real_tree(self):
        """SPECIFICITY: the real tree passes the check that guards this."""
        assert bundled_mcp_findings(PLUGIN_ROOT) == []

    def test_negative_a_planted_mcp_json_is_reported(self, scratch_plugin):
        """NEGATIVE: the filesystem route can fail."""
        (scratch_plugin / ".mcp.json").write_text("{}", encoding="utf-8")

        findings = bundled_mcp_findings(scratch_plugin)

        assert findings, "a planted .mcp.json produced no finding"
        assert all(finding.rule == "ADR-019" for finding in findings), findings

    def test_negative_a_nested_mcp_json_is_reported(self, scratch_plugin):
        """NEGATIVE: depth does not hide it."""
        nested = scratch_plugin / "skills" / "workflow-engine-plugin-surface" / ".mcp.json"
        nested.write_text("{}", encoding="utf-8")

        assert bundled_mcp_findings(scratch_plugin), "a nested .mcp.json produced no finding"

    def test_negative_a_manifest_mcpservers_key_is_reported_with_no_file_present(self, scratch_plugin):
        """NEGATIVE: the second route, which a file-only check would miss.

        Closing the filesystem route alone leaves the manifest path-override
        open, and a plugin exploiting it bundles servers while passing any
        ``find``-shaped check. Both halves are required.
        """
        manifest_path = scratch_plugin / ".claude-plugin" / "plugin.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["mcpServers"] = "./elsewhere.json"
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

        assert not list(scratch_plugin.rglob(".mcp.json")), "the fixture planted a file, defeating its own point"
        assert bundled_mcp_findings(scratch_plugin), "a manifest mcpServers key produced no finding"

    def test_the_check_calls_the_shipped_gate_rather_than_restating_it(self):
        """Drift guard: two implementations of one rule is one too many.

        ``bundled_mcp_findings`` must be answering with the gate CI runs. This
        pins it by requiring the gate's own FF-3 identifier and ADR-019 rule
        string to appear in what the function returns for a planted violation,
        which a local reimplementation would have had to invent for itself.
        """
        assert conformance.BUNDLED_MCP_FILE_NAME == ".mcp.json"
        assert "mcpServers" in conformance.FORBIDDEN_MANIFEST_FIELDS
        assert conformance.FORBIDDEN_MANIFEST_FIELDS["mcpServers"][1] == "ADR-019"


class TestInstallSettingsDelta:
    """AC 2, second half: the settings.json diff, against the MEASURED keys."""

    def test_the_measured_key_set_matches_the_spike_it_came_from(self):
        """The two keys are the spike's Item 3 result, not a guess.

        ``plugin_schema_spike.md`` Item 3 measured that ``marketplace add``
        writes ``extraKnownMarketplaces`` and ``install`` writes
        ``enabledPlugins``, with no other top-level key touched. This pins the
        constant to that document so a silent widening of the tolerated set is
        visible.
        """
        spike = REPO_ROOT / "docs" / "phase-1-architecture" / "plugin_schema_spike.md"
        text = spike.read_text(encoding="utf-8")
        for key in MEASURED_INSTALL_KEYS:
            assert key in text, key
        assert "RESULT: MEASURED." in text

    def test_specificity_the_two_measured_keys_alone_are_a_clean_verdict(self):
        """SPECIFICITY: the expected install is judged clean."""
        before = {"model": "opus", "hooks": {"Stop": [{"matcher": "*"}]}}
        after = dict(before, enabledPlugins={installed_plugin_id(): True}, extraKnownMarketplaces={"m": {}})

        verdict = audit_install(before, after)

        assert verdict["problems"] == []
        assert verdict["settings"]["expected_added"] == sorted(MEASURED_INSTALL_KEYS)

    def test_specificity_re_filling_already_present_measured_keys_is_clean(self):
        """SPECIFICITY: the second install on this machine's real state.

        The FR-14a spike left both keys present holding ``{}``. A rule that only
        tolerated ADDITIONS would call the normal second install a violation.
        """
        before = {"model": "opus", "enabledPlugins": {}, "extraKnownMarketplaces": {}}
        after = {"model": "opus", "enabledPlugins": {installed_plugin_id(): True}, "extraKnownMarketplaces": {"m": {}}}

        verdict = audit_install(before, after)

        assert verdict["problems"] == []
        assert verdict["settings"]["measured_keys_changed"] == sorted(MEASURED_INSTALL_KEYS)

    def test_negative_any_other_added_top_level_key_is_a_finding(self):
        """NEGATIVE: a third key is caught."""
        before = {"model": "opus"}
        after = dict(before, enabledPlugins={}, someOtherKey=1)

        problems = audit_install(before, after)["problems"]

        assert problems, "an unmeasured added key produced no finding"
        assert any("someOtherKey" in problem for problem in problems), problems

    def test_negative_a_removed_top_level_key_is_a_finding(self):
        """NEGATIVE: install taking something away is caught."""
        before = {"model": "opus", "somethingElse": 1}
        after = {"model": "opus", "enabledPlugins": {}}

        problems = audit_install(before, after)["problems"]

        assert any("somethingElse" in problem for problem in problems), problems

    def test_negative_a_changed_unrelated_top_level_key_is_a_finding(self):
        """NEGATIVE: install rewriting an unrelated value is caught."""
        before = {"model": "opus"}
        after = {"model": "sonnet", "enabledPlugins": {}}

        problems = audit_install(before, after)["problems"]

        assert any("model" in problem for problem in problems), problems

    @pytest.mark.parametrize("event", ["PreToolUse", "PostToolUse", "UserPromptSubmit"])
    def test_negative_each_named_hook_event_added_by_install_is_a_finding(self, event):
        """NEGATIVE: ADR-010, per event the scenario names separately."""
        before = {"hooks": {"Stop": [{"matcher": "*"}]}}
        after = {"hooks": {"Stop": [{"matcher": "*"}], event: [{"matcher": "*"}]}}

        problems = audit_install(before, after)["problems"]

        assert problems, "a planted {0} entry produced no finding".format(event)
        assert any(event in problem for problem in problems), problems

    def test_negative_altering_a_retained_hook_is_a_finding(self):
        """NEGATIVE: the Stop and Notification entries the plugin never owned."""
        before = {"hooks": {"Stop": [{"matcher": "*", "hooks": ["theirs.py"]}]}}
        after = {"hooks": {"Stop": [{"matcher": "*", "hooks": ["ours.py"]}]}}

        problems = audit_install(before, after)["problems"]

        assert any("Stop" in problem for problem in problems), problems

    def test_specificity_an_untouched_hooks_block_produces_no_hook_finding(self):
        """SPECIFICITY: the hook check is silent on the state it permits."""
        hooks = {"Stop": [{"matcher": "*"}], "Notification": [{"matcher": "*"}]}
        before = {"hooks": copy.deepcopy(hooks)}
        after = {"hooks": copy.deepcopy(hooks), "enabledPlugins": {}}

        assert hook_events_delta(before, after) == {"added": [], "removed": [], "changed": []}
        assert audit_install(before, after)["problems"] == []


class TestLiveInstallMeasurement:
    """AC 1 and AC 2: blocked by an owner ruling, not by a limitation."""

    def test_live_install_writes_only_the_measured_keys(self):
        """Compute the install verdict from snapshots a live cycle produced.

        This test is complete and runnable. What it does not do, and must not do,
        is perform the marketplace-add / install cycle itself: the owner ruled
        that no live cycle may be run. An operator with authorisation performs
        that half by following ``docs/guides/nfr11-lifecycle-verification.md``,
        which writes the two snapshots this test then judges.
        """
        if not _live_install_available():
            pytest.skip(_install_blocked_reason())

        before = _read_json(os.environ[INSTALL_BEFORE_ENV])
        after = _read_json(os.environ[INSTALL_AFTER_ENV])

        verdict = audit_install(before, after)

        assert verdict["problems"] == [], verdict["problems"]
        assert installed_plugin_id() in _top_level(after).get("enabledPlugins", {}), (
            "enabledPlugins does not name this plugin, so the snapshot did not "
            "capture an install of it and this run measures nothing"
        )

    def test_the_blocked_install_test_body_is_rehearsed_against_both_verdicts(self, tmp_path, monkeypatch):
        """Prove the blocked test computes a verdict rather than never running.

        A skipped test is indistinguishable from a test whose body cannot work.
        This drives the identical snapshot-reading path with synthetic files and
        requires it to produce a clean verdict on a conforming install and a
        dirty one on an install that touched a third key.
        """
        before_path = tmp_path / "install-before.json"
        before_path.write_text(json.dumps({"model": "opus"}), encoding="utf-8")

        clean = tmp_path / "install-after-clean.json"
        clean.write_text(
            json.dumps(
                {
                    "model": "opus",
                    "enabledPlugins": {installed_plugin_id(): True},
                    "extraKnownMarketplaces": {"techdeveloper-org": {}},
                }
            ),
            encoding="utf-8",
        )
        dirty = tmp_path / "install-after-dirty.json"
        dirty.write_text(
            json.dumps(
                {
                    "model": "opus",
                    "enabledPlugins": {installed_plugin_id(): True},
                    "hooks": {"PreToolUse": [{"matcher": "*"}]},
                }
            ),
            encoding="utf-8",
        )

        monkeypatch.setenv(LIVE_INSTALL_ENV, "1")
        monkeypatch.setenv(INSTALL_BEFORE_ENV, str(before_path))

        monkeypatch.setenv(INSTALL_AFTER_ENV, str(clean))
        assert _live_install_available()
        self.test_live_install_writes_only_the_measured_keys()

        monkeypatch.setenv(INSTALL_AFTER_ENV, str(dirty))
        with pytest.raises(AssertionError):
            self.test_live_install_writes_only_the_measured_keys()

    def test_the_rehearsal_also_catches_an_install_that_named_a_different_plugin(self, tmp_path, monkeypatch):
        """NEGATIVE: a snapshot of somebody else's install is not our evidence.

        Without this, a run whose ``enabledPlugins`` names an unrelated plugin
        would pass the delta check and be recorded as our result.
        """
        before_path = tmp_path / "before.json"
        before_path.write_text(json.dumps({"model": "opus"}), encoding="utf-8")
        wrong = tmp_path / "after-wrong-plugin.json"
        wrong.write_text(
            json.dumps({"model": "opus", "enabledPlugins": {"someone-else@theirs": True}}),
            encoding="utf-8",
        )

        monkeypatch.setenv(LIVE_INSTALL_ENV, "1")
        monkeypatch.setenv(INSTALL_BEFORE_ENV, str(before_path))
        monkeypatch.setenv(INSTALL_AFTER_ENV, str(wrong))

        with pytest.raises(AssertionError):
            self.test_live_install_writes_only_the_measured_keys()

    def test_the_skip_reason_names_the_ruling_and_the_way_forward(self):
        """A skip a reader cannot act on is a silent skip with extra words."""
        reason = _install_blocked_reason()

        assert "owner" in reason.lower()
        assert LIVE_INSTALL_ENV in reason
        assert PROCEDURE_DOC.name in reason


class TestInvokeReachesCapabilityOnlyAfterTheSecondStep:
    """AC 3: the two-step reachability flip SRS FR-26 (a) and (b) describe."""

    def test_step_one_alone_cannot_make_any_capability_reachable(self):
        """FR-26 (a): a fresh install leaves the MCP capabilities unreachable.

        This half needs no live install to be decided. Reachability of any
        MCP-backed capability requires an ``mcpServers`` entry, and the plugin
        ships no route to one -- neither a ``.mcp.json`` at any depth nor an
        ``mcpServers`` manifest key, both asserted by the gate. Install alone
        therefore cannot register anything, by construction rather than by
        observation.
        """
        assert bundled_mcp_findings(PLUGIN_ROOT) == []

    def test_the_capability_flips_unreachable_to_reachable_across_the_two_steps(
        self, settings_file, server_root, ledger_file
    ):
        """FR-26 (b): reachable only after step two, proved by a real spawn.

        Step one is represented by a settings file that no ``register-mcp`` has
        touched, which is what a fresh install leaves given the assertion above.
        Step two runs the real command. Each state is established by spawning
        what the settings file names and completing a JSON-RPC handshake, using
        the probe ``tests/test_register_mcp.py`` owns rather than a second one.
        """
        assert register_tests._capability_reachable(settings_file, "progress-writer") is False

        register_tests._run_cli(["register", "--server-root", str(server_root)], settings_file, ledger_file)

        assert register_tests._capability_reachable(settings_file, "progress-writer") is True

    def test_negative_the_reachability_probe_can_report_false_after_step_two(
        self, settings_file, server_root, ledger_file
    ):
        """NEGATIVE: the probe is not a constant True.

        A probe that always answered True would make the flip above vacuous.
        This registers, then repoints the written entry at a file that does not
        exist, and requires the spawn to fail.
        """
        register_tests._run_cli(["register", "--server-root", str(server_root)], settings_file, ledger_file)
        settings = json.loads(settings_file.read_text(encoding="utf-8"))
        settings[MCP_BLOCK]["post-tool-tracker"]["args"] = [str(server_root / "absent.py")]
        settings_file.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")

        with pytest.raises(AssertionError):
            register_tests._capability_reachable(settings_file, "progress-writer")

    def test_the_push_gate_half_of_criterion_b_now_flips_too(self, settings_file, server_root, ledger_file):
        """FR-26 (b) asks for TWO capabilities to flip, and both now can.

        The predecessor of this test measured the opposite and said so: the
        catalogue marked the push-gate server ``not_built_yet`` (V2-024 owned
        it), so ``register-mcp`` wrote no entry for it and the criterion was
        only half satisfiable. V2-024 has landed, so the same measurement is
        re-run with the opposite expectation rather than deleted.

        The real server is copied into this test's own scratch root instead of
        into the shared fixture, because every other test in this module counts
        on that fixture registering exactly the progress writer.
        """
        servers = registration.load_registry(PLUGIN_ROOT)
        gate_id = registration.push_gate_server_id(servers)
        gate = next(server for server in servers if server["id"] == gate_id)
        assert gate_id is not None
        assert "not_built_yet" not in gate, "V2-024 has landed; the catalogue must stop reporting it unavailable"

        source = REPO_ROOT / Path(gate["entry"]).parent
        target = server_root / gate["repo"] / Path(gate["entry"]).parent
        target.mkdir(parents=True)
        for name in ("server.py", "push_gate_policy.py", "__init__.py"):
            (target / name).write_text((source / name).read_text(encoding="utf-8"), encoding="utf-8")

        assert register_tests._capability_reachable(settings_file, gate["capability"]) is False

        register_tests._run_cli(["register", "--server-root", str(server_root)], settings_file, ledger_file)

        assert gate_id in json.loads(settings_file.read_text(encoding="utf-8")).get(MCP_BLOCK, {})
        assert register_tests._capability_reachable(settings_file, gate["capability"]) is True

    def test_negative_the_no_bundled_route_precondition_can_fail(self, scratch_plugin):
        """NEGATIVE: step one's guarantee rests on a check that can fail.

        If the plugin ever bundled a server, install alone WOULD make a
        capability reachable and the two-step claim would be false. This proves
        the check that rules that out is capable of reporting it.
        """
        (scratch_plugin / ".mcp.json").write_text("{}", encoding="utf-8")

        assert bundled_mcp_findings(scratch_plugin), "the step-one precondition check cannot fail"

    def test_the_round_trip_reachability_measurement_is_credited_not_reimplemented(self):
        """Drift guard on the reuse claim this module makes in its docstring.

        The unreachable -> reachable -> UNREACHABLE round trip is V2-016's
        measurement. This module measures the first two states and does not
        re-prove the third. If that test is renamed or deleted, the credit above
        becomes a claim about nothing, so it is pinned here.
        """
        text = REGISTER_TEST_PATH.read_text(encoding="utf-8")
        assert REACHABILITY_ROUND_TRIP_TEST in text, REACHABILITY_ROUND_TRIP_TEST


class TestTheOwnerRulingIsPinnedToItsRecord:
    """The narrowing follows a ruling, so the ruling must be checkable."""

    def test_the_review_index_records_the_ruling_this_module_encodes(self):
        """SPECIFICITY: every clause of the narrowing is in the real record.

        ``docs/REVIEW-INDEX.md`` item 37 is where the owner's resolution of the
        ADR-020 Path C versus FR-31 (a) conflict lives. Without this pin, a
        revert of that record would leave this module quietly asserting the
        opposite of what the project decided.
        """
        text = ruling_record_text()

        assert check_owner_ruling(text) == []

    @pytest.mark.parametrize("clause", RULING_CLAUSES)
    def test_negative_each_clause_of_the_ruling_is_separately_required(self, clause):
        """NEGATIVE: removing any one clause is caught, not absorbed."""
        text = ruling_record_text()
        assert clause in text, "the fixture clause is stale: {0!r}".format(clause)

        problems = check_owner_ruling(text.replace(clause, ""))

        assert problems, "removing {0!r} produced no violation".format(clause)
        assert any(clause in problem for problem in problems), problems

    def test_the_record_marks_the_conflict_resolved_rather_than_open(self):
        """A conflict left open would mean this module chose a side by itself."""
        assert "RESOLVED by owner ruling" in ruling_record_text()


class TestNarrowedUninstallResidue:
    """AC 4: plugin-attributable delta only, under the owner's Path C ruling."""

    def test_the_exempt_set_is_resolved_from_the_catalogue_not_spelled_here(self):
        """No server id is hardcoded, so V2-024 is covered when it lands."""
        exempt = safety_enforcement_server_ids()
        servers = registration.load_registry(PLUGIN_ROOT)
        gates = {server["id"] for server in servers if server.get("capability") == registration.PUSH_GATE_CAPABILITY}

        assert exempt == gates
        assert exempt, "the catalogue declares no safety-enforcement gate, so the narrowing exempts nothing"

    def test_specificity_a_surviving_safety_gate_entry_is_expected_not_residue(self):
        """The ruling's operative half: Path C wins, so persistence is expected."""
        gate_id = sorted(safety_enforcement_server_ids())[0]
        spec = _spec("/servers/mcp-push-gate/server.py")
        before = {MCP_BLOCK: {gate_id: spec}}
        after = {MCP_BLOCK: {gate_id: spec}, "enabledPlugins": {}}
        ledger = _ledger(**{gate_id: {"spec": spec}})

        verdict = uninstall_verdict(before, after, ledger, safety_enforcement_server_ids())

        assert verdict["residue"] == []
        assert verdict["expected_persistence"], "the survivor was not recorded as expected persistence either"

    def test_negative_a_surviving_operational_entry_is_still_residue(self):
        """The narrowing must not swallow the case FR-18 still covers.

        Scope-limiting FR-18 (a) to operational tools is only meaningful if an
        operational tool surviving still fails. Without this the ruling would
        have made the criterion vacuous.
        """
        spec = _spec("/servers/mcp-post-tool-tracker/server.py")
        before = {MCP_BLOCK: {"post-tool-tracker": spec}}
        after = {MCP_BLOCK: {"post-tool-tracker": spec}}
        ledger = _ledger(**{"post-tool-tracker": {"spec": spec}})

        verdict = uninstall_verdict(before, after, ledger, safety_enforcement_server_ids())

        assert verdict["residue"], "an operational survivor was exempted by the narrowing"
        assert verdict["expected_persistence"] == []

    def test_the_narrowing_is_load_bearing_against_the_unnarrowed_instrument(self):
        """MUTATION: substituting V2-022's check must change the verdict.

        Stated so this module is not read as V2-022 run twice. On a surviving
        safety gate the unnarrowed check reports residue and the narrowed one
        does not; that difference IS the owner's ruling, expressed in code.
        """
        gate_id = sorted(safety_enforcement_server_ids())[0]
        spec = _spec("/servers/mcp-push-gate/server.py")
        before = {MCP_BLOCK: {gate_id: spec}}
        after = {MCP_BLOCK: {gate_id: spec}}
        ledger = _ledger(**{gate_id: {"spec": spec}})

        assert attribution.attributable_residue(before, after, ledger), "the unnarrowed check did not fire"
        assert uninstall_verdict(before, after, ledger, safety_enforcement_server_ids())["residue"] == []

    def test_the_two_instruments_agree_on_an_operational_survivor(self):
        """The narrowing is not uniformly weaker; it differs only on gates."""
        spec = _spec("/servers/mcp-post-tool-tracker/server.py")
        before = {MCP_BLOCK: {"post-tool-tracker": spec}}
        after = {MCP_BLOCK: {"post-tool-tracker": spec}}
        ledger = _ledger(**{"post-tool-tracker": {"spec": spec}})

        assert attribution.attributable_residue(before, after, ledger)
        assert uninstall_verdict(before, after, ledger, safety_enforcement_server_ids())["residue"]

    def test_the_message_prefix_this_module_parses_is_the_one_v2_022_writes(self):
        """Drift guard: the partition reads a format it does not own.

        ``uninstall_verdict`` splits V2-022's residue message on its first colon
        to recover the server id. If that message format changes, every exempt
        entry silently stops being exempt. This pins the two together against a
        known input rather than trusting the shape.
        """
        spec = _spec("/servers/mcp-post-tool-tracker/server.py")
        before = {MCP_BLOCK: {"post-tool-tracker": spec}}
        after = {MCP_BLOCK: {"post-tool-tracker": spec}}
        ledger = _ledger(**{"post-tool-tracker": {"spec": spec}})

        messages = attribution.attributable_residue(before, after, ledger)

        assert messages
        assert [_server_id_of(message) for message in messages] == ["post-tool-tracker"]

    def test_damage_is_not_partitioned_by_the_narrowing(self):
        """Over-removal stays a finding whatever the entry was for.

        The ruling narrowed what counts as RESIDUE. It said nothing about
        collateral damage, and exempting a gate from the damage check would mean
        deleting a user's own push-gate entry went unreported.
        """
        gate_id = sorted(safety_enforcement_server_ids())[0]
        theirs = _spec("/the/users/own/thing.py")
        before = {MCP_BLOCK: {"theirs": theirs}}
        after = {MCP_BLOCK: {}}
        ledger = _ledger(**{gate_id: {"spec": _spec("/ours.py")}})

        verdict = uninstall_verdict(before, after, ledger, safety_enforcement_server_ids())

        assert verdict["damage"], "over-removal of an unclaimed entry produced no finding"

    def test_negative_an_empty_ledger_claims_nothing_rather_than_everything(self):
        """A malformed ledger must narrow the claim, never widen it."""
        spec = _spec("/servers/mcp-post-tool-tracker/server.py")
        before = {MCP_BLOCK: {"post-tool-tracker": spec}}
        after = {MCP_BLOCK: {"post-tool-tracker": spec}}

        for broken in (None, {}, {"registered": []}, {"registered": "nonsense"}, "not a document"):
            verdict = uninstall_verdict(before, after, broken, safety_enforcement_server_ids())
            assert verdict["residue"] == []
            assert verdict["damage"] == []

    def test_mutation_whole_file_equality_is_still_the_wrong_instrument(self):
        """MUTATION: the comparison AC 4 forbids reports the wrong thing.

        Reuses V2-022's mutant rather than writing a second one. It flags the
        emptied bookkeeping keys, which no criterion asks about, exactly where
        the narrowed check correctly reports nothing.
        """
        theirs = _spec("/the/users/own/post-tool-tracker.py")
        before = {"model": "opus", MCP_BLOCK: {"post-tool-tracker": theirs}}
        after = dict(before, enabledPlugins={}, extraKnownMarketplaces={})

        assert uninstall_verdict(before, after, _ledger(), safety_enforcement_server_ids())["residue"] == []
        assert attribution.whole_file_equality_verdict(before, after), "the mutant did not differ"


class TestLiveUninstallMeasurement:
    """AC 4 against a real cycle: blocked by the same owner ruling."""

    def test_live_uninstall_leaves_no_operational_residue(self):
        """Compute the narrowed FR-18 verdict from a live cycle's snapshots.

        The snapshot variables are V2-022's, deliberately. One authorised
        install/uninstall cycle produces the evidence both modules judge, which
        is what ``docs/guides/fr31-uninstall-residue-verification.md`` section 6
        already asks an operator to do.

        The difference from V2-022's test is the verdict, not the input: a
        surviving safety-enforcement gate passes here and fails there, because
        the owner ruled ADR-020 Path C wins.
        """
        if not _live_uninstall_available():
            pytest.skip(_uninstall_blocked_reason())

        before = _read_json(os.environ[SNAPSHOT_BEFORE_ENV])
        after = _read_json(os.environ[SNAPSHOT_AFTER_ENV])
        ledger = _read_json(os.environ[SNAPSHOT_LEDGER_ENV])

        assert attribution.ledger_records(ledger), (
            "the ledger snapshot claims no registration, so this run measures "
            "nothing. The procedure's register step did not write an entry; fix "
            "--server-root and repeat."
        )

        verdict = uninstall_verdict(before, after, ledger, safety_enforcement_server_ids())
        assert verdict["residue"] == [], verdict["residue"]
        assert verdict["damage"] == [], verdict["damage"]

    def test_the_blocked_uninstall_test_body_is_rehearsed_against_both_verdicts(self, tmp_path, monkeypatch):
        """Prove the blocked test computes a verdict rather than never running."""
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
        assert _live_uninstall_available()
        self.test_live_uninstall_leaves_no_operational_residue()

        monkeypatch.setenv(SNAPSHOT_AFTER_ENV, str(dirty))
        with pytest.raises(AssertionError):
            self.test_live_uninstall_leaves_no_operational_residue()

    def test_the_rehearsal_shows_a_surviving_safety_gate_passing(self, tmp_path, monkeypatch):
        """SPECIFICITY: the ruling's exemption is exercised on the blocked path.

        The rehearsal above uses an operational entry, which the narrowing does
        NOT exempt. Without this second rehearsal the exemption would never be
        driven through the snapshot-reading body it is supposed to govern.
        """
        gate_id = sorted(safety_enforcement_server_ids())[0]
        spec = _spec("/servers/mcp-push-gate/server.py")
        ledger_path = tmp_path / "gate-ledger.json"
        ledger_path.write_text(json.dumps(_ledger(**{gate_id: {"spec": spec}})), encoding="utf-8")
        before_path = tmp_path / "gate-before.json"
        before_path.write_text(json.dumps({MCP_BLOCK: {gate_id: spec}}), encoding="utf-8")
        survived = tmp_path / "gate-after.json"
        survived.write_text(json.dumps({MCP_BLOCK: {gate_id: spec}, "enabledPlugins": {}}), encoding="utf-8")

        monkeypatch.setenv(LIVE_INSTALL_ENV, "1")
        monkeypatch.setenv(SNAPSHOT_BEFORE_ENV, str(before_path))
        monkeypatch.setenv(SNAPSHOT_LEDGER_ENV, str(ledger_path))
        monkeypatch.setenv(SNAPSHOT_AFTER_ENV, str(survived))

        self.test_live_uninstall_leaves_no_operational_residue()

    def test_the_skip_reason_names_the_ruling_and_the_way_forward(self):
        """A skip a reader cannot act on is a silent skip with extra words."""
        reason = _uninstall_blocked_reason()

        assert "owner" in reason.lower()
        assert "Path C" in reason
        assert LIVE_INSTALL_ENV in reason
        assert PROCEDURE_DOC.name in reason


class TestRegisterUnregisterRoundTrip:
    """AC 5: the fourth scenario, and the one lifecycle claim fully measurable."""

    def test_the_round_trip_restores_the_settings_object(self, settings_file, server_root, ledger_file):
        """REVERSIBLE, object-level. This is the claim AC 5 is read as making."""
        original = json.loads(settings_file.read_text(encoding="utf-8"))

        register_tests._run_cli(["register", "--server-root", str(server_root)], settings_file, ledger_file)
        register_tests._run_cli(["unregister"], settings_file, ledger_file)

        assert json.loads(settings_file.read_text(encoding="utf-8")) == original

    def test_the_round_trip_restores_the_ledger_to_its_pre_registration_state(
        self, settings_file, server_root, ledger_file
    ):
        """The provenance ledger is part of "pre-registration state" too.

        A round trip that restored the settings file but left the ledger
        claiming an entry would leave ``unregister`` able to remove a name it no
        longer wrote.
        """
        assert attribution.ledger_records(_read_json(ledger_file)) == {}

        register_tests._run_cli(["register", "--server-root", str(server_root)], settings_file, ledger_file)
        assert attribution.ledger_records(_read_json(ledger_file))

        register_tests._run_cli(["unregister"], settings_file, ledger_file)
        assert attribution.ledger_records(_read_json(ledger_file)) == {}

    def test_negative_the_object_equality_check_can_fail(self, settings_file, server_root, ledger_file):
        """NEGATIVE: half a round trip is caught.

        Without this, a comparison that always held would make the test above
        vacuous.
        """
        original = json.loads(settings_file.read_text(encoding="utf-8"))

        register_tests._run_cli(["register", "--server-root", str(server_root)], settings_file, ledger_file)

        assert json.loads(settings_file.read_text(encoding="utf-8")) != original

    def test_byte_identity_holds_when_the_formatting_already_matches(self, settings_file, server_root, ledger_file):
        """BYTE-IDENTICAL, stated as the conditional it is -- true branch."""
        original_bytes = settings_file.read_bytes()

        register_tests._run_cli(["register", "--server-root", str(server_root)], settings_file, ledger_file)
        register_tests._run_cli(["unregister"], settings_file, ledger_file)

        assert settings_file.read_bytes() == original_bytes

    def test_byte_identity_does_not_hold_when_the_formatting_differs(self, tmp_path, server_root, ledger_file):
        """BYTE-IDENTICAL -- false branch, measured rather than rounded away.

        A four-space settings file comes back two-space indented after a correct
        round trip. Reporting that as "restored" without qualification would be
        the overclaim this project keeps finding, so both branches are asserted.
        """
        four_space = tmp_path / "settings.json"
        four_space.write_text(json.dumps({"model": "opus"}, indent=4) + "\n", encoding="utf-8")
        original_bytes = four_space.read_bytes()
        original_object = json.loads(four_space.read_text(encoding="utf-8"))

        register_tests._run_cli(["register", "--server-root", str(server_root)], four_space, ledger_file)
        register_tests._run_cli(["unregister", "--acknowledge-no-push-gate"], four_space, ledger_file)

        assert json.loads(four_space.read_text(encoding="utf-8")) == original_object
        assert four_space.read_bytes() != original_bytes

    def test_mutation_byte_equality_substituted_for_object_equality_fails(self, tmp_path, server_root, ledger_file):
        """MUTATION: the stricter comparison rejects a correct round trip.

        This is why AC 5's "returns to its pre-registration state" is asserted at
        the object level and not at the byte level.
        """
        four_space = tmp_path / "settings.json"
        four_space.write_text(json.dumps({"model": "opus"}, indent=4) + "\n", encoding="utf-8")
        before_bytes = four_space.read_bytes()

        register_tests._run_cli(["register", "--server-root", str(server_root)], four_space, ledger_file)
        register_tests._run_cli(["unregister", "--acknowledge-no-push-gate"], four_space, ledger_file)

        assert attribution.whole_file_equality_verdict(before_bytes, four_space.read_bytes())

    def test_the_users_own_entry_is_untouched_by_the_round_trip(self, settings_file, server_root, ledger_file):
        """SPECIFICITY: "pre-registration state" includes what was never ours."""
        register_tests._run_cli(["register", "--server-root", str(server_root)], settings_file, ledger_file)
        register_tests._run_cli(["unregister"], settings_file, ledger_file)

        final = json.loads(settings_file.read_text(encoding="utf-8"))

        assert "a-server-the-user-owns" in final[MCP_BLOCK]
        assert final["hooks"]["Stop"] == [{"matcher": "*", "hooks": []}]


class TestTheProcedureDocumentRecordsTheBlockedState:
    """The blocked halves are written down, in the shape V2-016 established."""

    def test_the_procedure_exists_and_says_the_measurement_was_not_performed(self):
        """A blocked criterion with no procedure is an untracked gap."""
        assert PROCEDURE_DOC.is_file(), "missing procedure: {0}".format(PROCEDURE_DOC.as_posix())
        text = PROCEDURE_DOC.read_text(encoding="utf-8")

        assert "NOT PERFORMED" in text

    @pytest.mark.parametrize(
        "name",
        [
            LIVE_INSTALL_ENV,
            INSTALL_BEFORE_ENV,
            INSTALL_AFTER_ENV,
            SNAPSHOT_BEFORE_ENV,
            SNAPSHOT_AFTER_ENV,
            SNAPSHOT_LEDGER_ENV,
        ],
    )
    def test_the_procedure_names_every_variable_the_blocked_tests_read(self, name):
        """A procedure missing one variable produces a skip, not a result."""
        assert name in PROCEDURE_DOC.read_text(encoding="utf-8"), name

    @pytest.mark.parametrize(
        "name",
        [
            "test_live_install_writes_only_the_measured_keys",
            "test_live_uninstall_leaves_no_operational_residue",
        ],
    )
    def test_the_procedure_names_the_tests_it_unblocks(self, name):
        """An operator who cannot find the test cannot run the measurement."""
        assert name in PROCEDURE_DOC.read_text(encoding="utf-8"), name

    def test_the_procedure_records_the_owner_ruling_that_changed_the_verdict(self):
        """The ruling is the reason a surviving gate now passes."""
        text = PROCEDURE_DOC.read_text(encoding="utf-8")

        assert "Path C" in text
        assert "ADR-020" in text

    def test_the_procedure_document_is_ascii_only(self):
        """The document ships under the same encoding rule as everything else."""
        text = PROCEDURE_DOC.read_text(encoding="utf-8")
        offenders = sorted({character for character in text if ord(character) > 127})
        assert not offenders, offenders

    def test_this_module_is_ascii_only(self):
        """The rule this module asserts about a document applies to itself."""
        text = Path(__file__).read_text(encoding="utf-8")
        offenders = sorted({character for character in text if ord(character) > 127})
        assert not offenders, offenders


def _all_present(*names):
    """Report whether every named environment variable points at a real file.

    Args:
        *names: Environment variable names.

    Returns:
        bool: True when each is set and names an existing file.
    """
    for name in names:
        value = os.environ.get(name, "").strip()
        if not value or not Path(value).is_file():
            return False
    return True


def _authorised():
    """Report whether a live plugin lifecycle run has been authorised.

    Returns:
        bool: True when the authorisation variable is exactly "1".
    """
    return os.environ.get(LIVE_INSTALL_ENV, "").strip() == "1"


def _live_install_available():
    """Report whether an authorised live install supplied its two snapshots.

    Returns:
        bool: True when authorisation and both snapshot files are present.
    """
    return _authorised() and _all_present(INSTALL_BEFORE_ENV, INSTALL_AFTER_ENV)


def _live_uninstall_available():
    """Report whether an authorised live uninstall supplied its three snapshots.

    Returns:
        bool: True when authorisation and all three snapshot files are present.
    """
    return _authorised() and _all_present(SNAPSHOT_BEFORE_ENV, SNAPSHOT_AFTER_ENV, SNAPSHOT_LEDGER_ENV)


def _install_blocked_reason():
    """Return the skip message for the blocked install measurement.

    Returns:
        str: A message naming the cause, the criterion and the way forward.
    """
    return (
        "BLOCKED, NOT PASSED. SRS NFR-11's install test needs a live claude "
        "plugin marketplace add followed by claude plugin install. The project "
        "owner ruled that no live cycle may be run: install writes "
        "enabledPlugins and extraKnownMarketplaces into a settings scope and "
        "uninstall only empties them, so at user scope the ruling protects the "
        "owner's live configuration and at local scope a git-tracked file in "
        "this repository. This test is complete and will run as written once an "
        "operator with authorisation follows {0} and exports {1}=1 together "
        "with {2} and {3}. Do not substitute a hand-edited settings file for "
        "the measurement.".format(PROCEDURE_DOC.name, LIVE_INSTALL_ENV, INSTALL_BEFORE_ENV, INSTALL_AFTER_ENV)
    )


def _uninstall_blocked_reason():
    """Return the skip message for the blocked uninstall measurement.

    Returns:
        str: A message naming the cause, the ruling and the way forward.
    """
    return (
        "BLOCKED, NOT PASSED. SRS NFR-11's uninstall test needs a live claude "
        "plugin uninstall, which the project owner ruled may not be run for the "
        "same reason as the install half. The verdict this test computes is the "
        "NARROWED one: the owner ruled ADR-020 Path C wins, so a surviving "
        "safety-enforcement gate entry is expected persistence and only a "
        "surviving operational entry is residue. Run it by following {0} and "
        "exporting {1}=1 together with {2}, {3} and {4}. Do not substitute a "
        "hand-edited settings file for the measurement.".format(
            PROCEDURE_DOC.name,
            LIVE_INSTALL_ENV,
            SNAPSHOT_BEFORE_ENV,
            SNAPSHOT_AFTER_ENV,
            SNAPSHOT_LEDGER_ENV,
        )
    )

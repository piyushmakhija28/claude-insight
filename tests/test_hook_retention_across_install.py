"""Retention of the user's own Stop and Notification hooks (PRD FR-8 / SRS FR-18, issue V2-032).

THE CRITERION, AND THE WORD IN IT THAT DOES THE WORK
----------------------------------------------------
"An install/uninstall cycle leaves the pre-existing user-level ``Stop`` and
``Notification`` entries BYTE-IDENTICAL to their pre-install state."

Byte-identity is a stronger claim than "present and equivalent", and it is not a
single claim: it means different things at different granularities. This module
measures four of them and is explicit about which one it asserts.

    G1  whole file            sha256 of the settings file's own bytes.
    G2  hooks block           canonical-JSON digest of ``settings["hooks"]``.
    G3  entry value           canonical-JSON digest of one hook event's value.
    G0  entry source bytes    sha256 of the raw text span that spells the entry.

The ladder is not redundant. Each rung fails for reasons the rung below it
cannot see, and each rung passes in cases the rung above it fails:

- G1 fails on ANY install, because install writes ``enabledPlugins`` and
  ``extraKnownMarketplaces`` (FR-14a spike item 4). It says nothing about hooks.
- G2 sees a sibling hook event appearing or vanishing; G3 cannot.
- G3 is what V2-027 proved when it removed three hook registrations, and it is
  the strongest claim that survives a document the host chose to re-serialise.
- G0 is the only rung that is literally about bytes at the granularity the
  criterion names -- and it fails on a pure re-indentation that changes nothing
  about the hook.

WHAT THIS MODULE ASSERTS, AND WHAT IT ONLY REPORTS
---------------------------------------------------
- ASSERTED, unconditionally: G3 for each retained entry that existed before the
  cycle, plus the absence of a retained entry the cycle CREATED.
- ASSERTED, conditionally: G0, and only while the document's own formatting
  fingerprint is unchanged across the cycle. This is the same shape of
  conditional V2-016 was forced into for register/unregister byte-identity, and
  for the same reason: a re-serialised document differs in bytes for reasons
  that have nothing to do with the subject of the claim. When the fingerprint
  moves, the byte claim is recorded as NOT MADE, by name, in ``unproved``.
- REPORTED, never asserted: G1, and the movement of hook events OTHER than the
  two retained ones. ``tests/test_plugin_lifecycle.py::install_verdict`` already
  asserts the sibling-event claim for the INSTALL half; a second owner of one
  assertion is one owner too many.

WHAT V2-027 ALREADY PROVED, AND WHY IT IS NOT THIS
---------------------------------------------------
``scripts/remove_hook_registrations.py`` removed three hook registrations from
the live user-scope file and proved ``Stop`` and ``Notification`` came through at
G3. That is evidence about a HOOK-DELETION operation. This criterion is about an
INSTALL/UNINSTALL cycle. They are different operations against the same keys, and
the earlier result is not transferable. What IS reused, deliberately, is the
instrument: this module imports that tool's ``RETAINED_HOOKS`` and ``digest_of``
rather than respelling either, so the two results are computed by one
canonicaliser and remain comparable.

WHY THESE TWO HOOKS
-------------------
They are the only hooks that survive the plugin migration. The plugin ships zero
hooks (ADR-010), because a plugin's hook contribution merges into a flat
unlabelled union with no per-plugin provenance and cannot afterwards be
subtracted. These two are the user's own registrations; an install must not be
able to disturb them.

WHAT IS BLOCKED
---------------
The cycle the criterion names cannot be run. The project owner ruled that no
live ``claude plugin install`` or ``claude plugin uninstall`` may be performed:
install writes bookkeeping keys a later uninstall only empties, an orphaned cache
directory survives ``claude plugin prune``, and the local scope it would touch is
git-tracked here. The live test below is written complete, skips LOUDLY naming
the ruling and the criterion, and is rehearsed against synthetic snapshots that
require it to reach BOTH verdicts. The procedure an authorised operator follows
is ``docs/guides/fr8-hook-retention-verification.md``.
"""

import copy
import hashlib
import importlib.util
import json
import os
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
TESTS_DIR = Path(__file__).resolve().parent
TOOL_PATH = REPO_ROOT / "scripts" / "remove_hook_registrations.py"
ATTRIBUTION_TEST_PATH = TESTS_DIR / "test_uninstall_residue_attribution.py"
PROCEDURE_DOC = REPO_ROOT / "docs" / "guides" / "fr8-hook-retention-verification.md"
CONFORMANCE_GATE = REPO_ROOT / "scripts" / "verify_plugin_conformance.py"

LIVE_INSTALL_ENV = "CWE_ALLOW_LIVE_PLUGIN_INSTALL"
SNAPSHOT_BEFORE_ENV = "CWE_HOOK_SNAPSHOT_BEFORE"
SNAPSHOT_AFTER_ENV = "CWE_HOOK_SNAPSHOT_AFTER"

GRANULARITY_TOKENS = ("whole file", "hooks block", "entry value", "entry source bytes")

INDENT_PATTERN = re.compile(r"^( +)\S", re.MULTILINE)


def _load(name, path):
    """Import a module by explicit file path.

    Neither ``scripts`` nor ``tests`` is an importable package, so everything
    reused here is loaded by location rather than by relying on whatever pytest
    happened to put on ``sys.path`` for this invocation. This mirrors the loader
    in ``tests/test_uninstall_residue_attribution.py``.

    Args:
        name: Module name to register under.
        path: Filesystem path of the module.

    Returns:
        module: The loaded module.
    """
    spec = importlib.util.spec_from_file_location(name, str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


tool = _load("remove_hook_registrations_for_retention", TOOL_PATH)
attribution = _load("uninstall_residue_attribution_for_retention", ATTRIBUTION_TEST_PATH)

RETAINED_HOOKS = tool.RETAINED_HOOKS


@pytest.fixture(scope="module", autouse=True)
def live_settings_are_never_touched():
    """Fail the module if any live settings file changes while it runs.

    The path list is the sibling module's, not a second copy: it is the one that
    covers the user-scope ``settings.local.json`` the earlier guards missed, and
    it consults both the plain home directory and the resolver's ``CLAUDE_HOME``
    so an override cannot move the guard off the file it exists to protect.

    Yields:
        None
    """
    paths = attribution._guarded_settings_paths()
    before = {path.as_posix(): attribution._digest(path) for path in paths}
    yield
    after = {path.as_posix(): attribution._digest(path) for path in paths}
    assert before == after, "a test modified a live settings file: {0} -> {1}".format(before, after)


def parse_settings(raw):
    """Parse a settings document, treating anything unusable as empty.

    Args:
        raw: Full text of a settings file.

    Returns:
        dict: The parsed object, or an empty mapping when it does not parse to
        one. An empty mapping makes every check below claim nothing rather than
        claim everything.
    """
    try:
        parsed = json.loads(raw)
    except ValueError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def file_digest(raw):
    """Return the G1 digest: sha256 of the document's own bytes.

    Args:
        raw: Full text of a settings file.

    Returns:
        str: Hex digest.
    """
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def entry_source_span(raw, event, value):
    """Locate the raw text span that spells one hook event's value.

    The span is found by scanning for every ``"event":`` token in the document
    and decoding from just past each one. A candidate survives only when the
    decode succeeds AND yields a value equal to the parsed entry, which discards
    an occurrence of the same token inside a command string. When more or fewer
    than one candidate survives the locator REFUSES, because a span it guessed
    would make a byte-level verdict about the wrong region.

    Args:
        raw: Full text of a settings file.
        event: Hook event name.
        value: The parsed value the span must decode to.

    Returns:
        tuple: ``(start, end)`` character offsets, or None when unlocatable.
    """
    decoder = json.JSONDecoder()
    pattern = re.compile(r'"{0}"\s*:\s*'.format(re.escape(event)))
    hits = []
    for match in pattern.finditer(raw):
        try:
            decoded, end = decoder.raw_decode(raw, match.end())
        except ValueError:
            continue
        if decoded == value:
            hits.append((match.end(), end))
    return hits[0] if len(hits) == 1 else None


def entry_source_digest(raw, event, value):
    """Return the G0 digest: sha256 of the raw span that spells the entry.

    The document is handled as text and the span re-encoded as UTF-8, which is
    byte-identical to the original region for any valid UTF-8 input.

    Args:
        raw: Full text of a settings file.
        event: Hook event name.
        value: The parsed value the span must decode to.

    Returns:
        str: Hex digest, or None when the span could not be located.
    """
    span = entry_source_span(raw, event, value)
    if span is None:
        return None
    return hashlib.sha256(raw[span[0] : span[1]].encode("utf-8")).hexdigest()


def formatting_fingerprint(raw):
    """Describe the document's own serialisation style.

    This is what the G0 claim is conditioned on. A host that re-serialises the
    file changes the bytes of every entry in it without touching any entry's
    meaning, and asserting byte-identity across such a rewrite would be
    asserting something about the host's formatter.

    Limitation stated rather than hidden: the indent unit is read from the first
    space-indented line, so a tab-indented document reports 0 and a document
    with no indentation at all is indistinguishable from one that is tab
    indented. Both cases still compare equal to themselves, which is all the
    conditional needs.

    Args:
        raw: Full text of a settings file.

    Returns:
        dict: Newline style, indent width and trailing-newline flag.
    """
    match = INDENT_PATTERN.search(raw)
    return {
        "newline": "crlf" if "\r\n" in raw else "lf",
        "indent": len(match.group(1)) if match else 0,
        "trailing_newline": raw.endswith("\n"),
    }


def sibling_event_delta(before_hooks, after_hooks, retained=RETAINED_HOOKS):
    """Report movement among hook events other than the retained ones.

    Reported, never asserted on. ``tests/test_plugin_lifecycle.py`` owns the
    assertion that install adds no hook event, for the install half of the same
    cycle, and duplicating it here would give one claim two owners that can
    disagree.

    Args:
        before_hooks: Hooks block as it stood before the cycle.
        after_hooks: Hooks block after the cycle.
        retained: Hook names this module claims about, and therefore excludes.

    Returns:
        dict: ``added``, ``removed`` and ``changed`` event names.
    """
    excluded = set(retained)
    prior = {name: value for name, value in before_hooks.items() if name not in excluded}
    actual = {name: value for name, value in after_hooks.items() if name not in excluded}
    return {
        "added": sorted(set(actual) - set(prior)),
        "removed": sorted(set(prior) - set(actual)),
        "changed": sorted(name for name in set(prior) & set(actual) if prior[name] != actual[name]),
    }


def retention_verdict(before_raw, after_raw, retained=RETAINED_HOOKS):
    """Compute the full retention verdict for one install/uninstall cycle.

    Args:
        before_raw: Settings document text taken BEFORE the install.
        after_raw: Settings document text taken AFTER the uninstall.
        retained: Hook names required to survive.

    Returns:
        dict: Per-granularity verdicts, the asserted ``problems`` and
        ``byte_problems`` lists, the reported ``unproved`` list, and the
        reported sibling-event delta.
    """
    before_hooks = tool.hooks_block(parse_settings(before_raw))
    after_hooks = tool.hooks_block(parse_settings(after_raw))

    entries = {}
    problems = []
    unproved = []
    for name in retained:
        if name not in before_hooks:
            if name in after_hooks:
                problems.append(
                    "{0}: absent before the cycle and present after it; the cycle created a hook".format(name)
                )
            else:
                unproved.append("{0}: not registered before the cycle, so nothing about it is claimed".format(name))
            continue
        if name not in after_hooks:
            entries[name] = "LOST"
            problems.append("{0}: the pre-existing registration did not survive the cycle".format(name))
        elif tool.digest_of(before_hooks[name]) == tool.digest_of(after_hooks[name]):
            entries[name] = "IDENTICAL"
        else:
            entries[name] = "ALTERED"
            problems.append("{0}: the pre-existing registration changed across the cycle".format(name))

    reformatted = formatting_fingerprint(before_raw) != formatting_fingerprint(after_raw)
    entry_bytes = {}
    byte_problems = []
    for name in retained:
        if name not in before_hooks or name not in after_hooks:
            continue
        left = entry_source_digest(before_raw, name, before_hooks[name])
        right = entry_source_digest(after_raw, name, after_hooks[name])
        if left is None or right is None:
            entry_bytes[name] = "UNLOCATABLE"
        elif left == right:
            entry_bytes[name] = "IDENTICAL"
        else:
            entry_bytes[name] = "DIFFERENT"
    if reformatted:
        unproved.append(
            "byte-level retention is NOT CLAIMED: the document was re-serialised "
            "({0} -> {1}), which changes the bytes of every entry in it".format(
                formatting_fingerprint(before_raw), formatting_fingerprint(after_raw)
            )
        )
    else:
        for name in sorted(entry_bytes):
            if entry_bytes[name] == "DIFFERENT":
                byte_problems.append("{0}: the source bytes of the entry changed across the cycle".format(name))
            elif entry_bytes[name] == "UNLOCATABLE":
                byte_problems.append(
                    "{0}: the entry's source span could not be located unambiguously, so the "
                    "byte-level claim could not be made".format(name)
                )

    return {
        "entries": entries,
        "entry_bytes": entry_bytes,
        "hooks_block": "IDENTICAL" if tool.digest_of(before_hooks) == tool.digest_of(after_hooks) else "CHANGED",
        "whole_file": "IDENTICAL" if before_raw == after_raw else "DIFFERENT",
        "siblings": sibling_event_delta(before_hooks, after_hooks, retained),
        "problems": problems,
        "byte_problems": byte_problems,
        "unproved": unproved,
    }


def presence_only_verdict(before_raw, after_raw, retained=RETAINED_HOOKS):
    """The check the criterion forbids, kept so it can be shown insufficient.

    This is the mutant for the mutation tests: it asks only whether the names are
    still there. It is never used by any assertion about real retention.

    Args:
        before_raw: Settings document text taken before the cycle.
        after_raw: Settings document text taken after the cycle.
        retained: Hook names required to survive.

    Returns:
        list: One message per name that vanished, and nothing else.
    """
    before_hooks = tool.hooks_block(parse_settings(before_raw))
    after_hooks = tool.hooks_block(parse_settings(after_raw))
    return ["{0}: missing".format(name) for name in retained if name in before_hooks and name not in after_hooks]


STOP_ENTRY = [{"hooks": [{"type": "command", "command": "python stop-notifier.py", "timeout": 60, "async": False}]}]
NOTIFICATION_ENTRY = [{"hooks": [{"type": "command", "command": "beep", "shell": "powershell", "timeout": 15}]}]


def _document(hooks=None, indent=2, **extra):
    """Render a settings document of the shape the live file has.

    The unrelated top-level keys exist so that a test asserting they are ignored
    is asserting something. A document containing only ``hooks`` could not tell
    "the check ignored an unrelated change" from "there was nothing to ignore".

    Args:
        hooks: Hooks block, defaulting to both retained entries.
        indent: Indent width to serialise with.
        **extra: Additional top-level keys.

    Returns:
        str: The document text.
    """
    payload = {
        "model": "opus",
        "hooks": (
            copy.deepcopy(hooks) if hooks is not None else {"Stop": STOP_ENTRY, "Notification": NOTIFICATION_ENTRY}
        ),
        "mcpServers": {"a-server-the-user-owns": {"command": "python"}},
    }
    payload.update(extra)
    return json.dumps(payload, indent=indent) + "\n"


class TestTheFourGranularitiesAreGenuinelyDifferent:
    """The ladder is measured, not asserted in prose."""

    def test_an_unrelated_key_moves_g1_alone(self):
        """The install's own bookkeeping keys break G1 and nothing else."""
        before = _document()
        after = _document(enabledPlugins={}, extraKnownMarketplaces={})

        verdict = retention_verdict(before, after)

        assert verdict["whole_file"] == "DIFFERENT"
        assert verdict["hooks_block"] == "IDENTICAL"
        assert verdict["entries"] == {"Stop": "IDENTICAL", "Notification": "IDENTICAL"}
        assert verdict["entry_bytes"] == {"Stop": "IDENTICAL", "Notification": "IDENTICAL"}
        assert verdict["problems"] == []
        assert verdict["byte_problems"] == []

    def test_a_re_serialisation_moves_g0_but_not_g3(self):
        """This is the whole reason the byte claim is a conditional.

        A four-space rewrite changes the bytes of both entries while changing
        nothing about either hook. A test that asserted byte-identity flatly
        would fail here and would be reporting the host's formatter as a hook
        defect.
        """
        before = _document(indent=2)
        after = _document(indent=4)

        verdict = retention_verdict(before, after)

        assert verdict["entries"] == {"Stop": "IDENTICAL", "Notification": "IDENTICAL"}
        assert verdict["entry_bytes"] == {"Stop": "DIFFERENT", "Notification": "DIFFERENT"}
        assert verdict["problems"] == []
        assert verdict["byte_problems"] == [], "a re-serialisation must not be reported as a hook failure"
        assert any("NOT CLAIMED" in note for note in verdict["unproved"])

    def test_a_key_reordering_moves_g0_but_not_g3_at_identical_formatting(self):
        """G0 and G3 differ even when the document's formatting did not move.

        The canonical digest sorts keys, so a re-ordered entry is identical at
        G3 and different at G0. Without this case the conditional above could be
        read as "G0 only ever differs when the file was reformatted", which is
        false.
        """
        before = _document(hooks={"Stop": [{"a": 1, "b": 2}], "Notification": NOTIFICATION_ENTRY})
        after = before.replace('"a": 1,\n        "b": 2', '"b": 2,\n        "a": 1')

        assert after != before, "the fixture did not produce a re-ordering"
        verdict = retention_verdict(before, after)

        assert verdict["entries"]["Stop"] == "IDENTICAL"
        assert verdict["entry_bytes"]["Stop"] == "DIFFERENT"
        assert verdict["problems"] == []
        assert verdict["byte_problems"], "a byte-level difference at unchanged formatting must be reported"

    def test_a_sibling_event_moves_g2_but_not_g3(self):
        """G2 sees what G3 structurally cannot."""
        before = _document()
        after = _document(
            hooks={"Stop": STOP_ENTRY, "Notification": NOTIFICATION_ENTRY, "PreToolUse": [{"matcher": "*"}]}
        )

        verdict = retention_verdict(before, after)

        assert verdict["hooks_block"] == "CHANGED"
        assert verdict["entries"] == {"Stop": "IDENTICAL", "Notification": "IDENTICAL"}
        assert verdict["siblings"]["added"] == ["PreToolUse"]
        assert verdict["problems"] == [], "a sibling event is reported here, and asserted by V2-023"


class TestTheCheckCanFail:
    """Every asserted check is paired with a planted violation it must reject."""

    def test_negative_an_altered_entry_is_reported_and_named(self):
        """NEGATIVE: a changed timeout inside the Stop entry is caught."""
        altered = copy.deepcopy(STOP_ENTRY)
        altered[0]["hooks"][0]["timeout"] = 61
        before = _document()
        after = _document(hooks={"Stop": altered, "Notification": NOTIFICATION_ENTRY})

        verdict = retention_verdict(before, after)

        assert verdict["entries"]["Stop"] == "ALTERED"
        assert verdict["entries"]["Notification"] == "IDENTICAL"
        assert any("Stop" in problem for problem in verdict["problems"])
        assert not any("Notification" in problem for problem in verdict["problems"])

    def test_negative_a_lost_entry_is_reported(self):
        """NEGATIVE: an entry the cycle deleted is caught."""
        before = _document()
        after = _document(hooks={"Notification": NOTIFICATION_ENTRY})

        verdict = retention_verdict(before, after)

        assert verdict["entries"]["Stop"] == "LOST"
        assert any("did not survive" in problem for problem in verdict["problems"])

    def test_negative_an_entry_the_cycle_created_is_reported(self):
        """NEGATIVE: install adding a retained-name hook is caught.

        Retention is not creation, so an absent entry is not claimed about -- but
        an entry that APPEARS is a hook the cycle registered, and the plugin
        ships zero hooks (ADR-010).
        """
        before = _document(hooks={"Stop": STOP_ENTRY})
        after = _document()

        verdict = retention_verdict(before, after)

        assert any("created a hook" in problem for problem in verdict["problems"])

    def test_negative_an_unlocatable_span_fails_rather_than_degrades(self):
        """NEGATIVE: an ambiguous span is a byte problem, not a silent pass.

        Two structurally identical ``Stop`` values at different nesting levels
        leave the locator unable to say which span is the hook's. Reporting
        nothing here would drop the byte claim without saying so.
        """
        before = _document(hooks={"Stop": STOP_ENTRY, "Notification": NOTIFICATION_ENTRY}, decoy={"Stop": STOP_ENTRY})
        after = before

        verdict = retention_verdict(before, after)

        assert verdict["entry_bytes"]["Stop"] == "UNLOCATABLE"
        assert any("could not be located" in problem for problem in verdict["byte_problems"])

    def test_negative_a_malformed_document_claims_nothing_rather_than_everything(self):
        """NEGATIVE: unparseable input must narrow the claim, never widen it."""
        for broken in ("", "{,}", "[1, 2, 3]", "not json at all"):
            verdict = retention_verdict(broken, broken)
            assert verdict["problems"] == []
            assert verdict["byte_problems"] == []
            assert verdict["entries"] == {}

    def test_negative_the_reporters_can_be_empty_so_a_report_means_something(self):
        """NEGATIVE: an unchanged cycle produces empty reports across the board."""
        before = _document()

        verdict = retention_verdict(before, before)

        assert verdict["whole_file"] == "IDENTICAL"
        assert verdict["siblings"] == {"added": [], "removed": [], "changed": []}
        assert verdict["unproved"] == []
        assert verdict["problems"] == []
        assert verdict["byte_problems"] == []


class TestSpecificityBothDirections:
    """The check must fire on an altered entry and stay silent on everything else."""

    def test_specificity_a_correct_cycle_is_judged_clean(self):
        """SPECIFICITY: the realistic clean cycle passes the real instrument.

        This is the shape a measured cycle is expected to produce: the two
        bookkeeping keys appear, everything else stands still.
        """
        before = _document()
        after = _document(enabledPlugins={"claude-workflow-engine@techdeveloper-org": True}, extraKnownMarketplaces={})

        verdict = retention_verdict(before, after)

        assert verdict["problems"] == []
        assert verdict["byte_problems"] == []
        assert verdict["unproved"] == []

    @pytest.mark.parametrize(
        "extra",
        [
            {"enabledPlugins": {}},
            {"extraKnownMarketplaces": {"techdeveloper-org": {}}},
            {"model": "sonnet"},
            {"mcpServers": {"post-tool-tracker": {"command": "python"}}},
            {"statusLine": {"type": "command"}},
        ],
    )
    def test_specificity_no_unrelated_settings_change_fires_the_check(self, extra):
        """SPECIFICITY, direction two: each unrelated change separately proved inert."""
        before = _document()
        after = _document(**extra)

        verdict = retention_verdict(before, after)

        assert verdict["problems"] == [], extra
        assert verdict["byte_problems"] == [], extra

    def test_specificity_each_retained_entry_is_checked_independently(self):
        """SPECIFICITY: altering Notification alone implicates Notification alone."""
        altered = copy.deepcopy(NOTIFICATION_ENTRY)
        altered[0]["hooks"][0]["command"] = "different"
        before = _document()
        after = _document(hooks={"Stop": STOP_ENTRY, "Notification": altered})

        verdict = retention_verdict(before, after)

        assert verdict["entries"] == {"Stop": "IDENTICAL", "Notification": "ALTERED"}
        assert len(verdict["problems"]) == 1


class TestTheInstrumentIsTheShippedOne:
    """One canonicaliser and one retained-name list, not two of each."""

    def test_the_retained_names_come_from_the_shipped_tool(self):
        """Drift guard: a second spelling of the pair could diverge silently."""
        assert set(RETAINED_HOOKS) == {"Stop", "Notification"}
        assert set(RETAINED_HOOKS).isdisjoint(set(tool.FR4_HOOKS))

    def test_the_canonical_digest_is_the_v2_027_digest(self):
        """The two results are comparable only if one function computed both."""
        assert tool.digest_of(STOP_ENTRY) == tool.digest_of(json.loads(json.dumps(STOP_ENTRY)))
        assert tool.digest_of(STOP_ENTRY) != tool.digest_of(NOTIFICATION_ENTRY)

    def test_the_canonical_digest_ignores_key_order_and_the_source_digest_does_not(self):
        """The two instruments must disagree, or the ladder has one rung."""
        raw_a = _document(hooks={"Stop": [{"a": 1, "b": 2}]})
        raw_b = raw_a.replace('"a": 1,\n        "b": 2', '"b": 2,\n        "a": 1')
        value_a = tool.hooks_block(parse_settings(raw_a))["Stop"]
        value_b = tool.hooks_block(parse_settings(raw_b))["Stop"]

        assert tool.digest_of(value_a) == tool.digest_of(value_b)
        assert entry_source_digest(raw_a, "Stop", value_a) != entry_source_digest(raw_b, "Stop", value_b)

    def test_specificity_the_span_locator_finds_the_real_entry(self):
        """SPECIFICITY: the locator is not uniformly refusing.

        A locator that always returned None would make every byte verdict
        UNLOCATABLE, which the negative test above would still accept as a
        failure. This pins the positive case.
        """
        raw = _document()
        hooks = tool.hooks_block(parse_settings(raw))
        for name in RETAINED_HOOKS:
            span = entry_source_span(raw, name, hooks[name])
            assert span is not None, name
            assert json.loads(raw[span[0] : span[1]]) == hooks[name]

    def test_specificity_the_locator_ignores_the_event_name_inside_a_string(self):
        """SPECIFICITY: a command that merely mentions the name is not a span."""
        raw = _document(hooks={"Stop": STOP_ENTRY}, note='the "Stop": hook is retained')
        hooks = tool.hooks_block(parse_settings(raw))

        assert entry_source_span(raw, "Stop", hooks["Stop"]) is not None


class TestTheCrossScopeGapIsClosedElsewhere:
    """The criterion is weaker than it looks, and a different gate covers the gap.

    Byte-identity of the USER-scope entry does not imply the user's ``Stop``
    behaviour is unchanged. Hook contributions merge across the four settings
    scopes into one flat unlabelled list per event, so a plugin that registered a
    ``Stop`` handler at PROJECT scope would leave the user-scope entry
    byte-identical while changing what actually runs on Stop. Nothing measurable
    from a single user-scope snapshot can see that.

    For THIS plugin the gap is closed, but by a different control: FF-2 in the
    conformance gate asserts the plugin ships no hooks artefact at all, by both
    the filesystem route and the manifest path-override route. That control is
    credited here, not re-proved -- and pinned, so deleting it breaks a test
    rather than silently invalidating this module's scope argument.
    """

    def test_the_conformance_gate_still_carries_the_zero_hooks_check(self):
        """Drift guard: this module's cross-scope argument rests on FF-2 existing."""
        text = CONFORMANCE_GATE.read_text(encoding="utf-8")

        assert "def check_no_hooks(" in text
        assert "FF-2" in text

    def test_the_procedure_document_states_the_cross_scope_limit(self):
        """The limitation must reach the operator, not only this docstring."""
        text = PROCEDURE_DOC.read_text(encoding="utf-8")

        assert "merge" in text
        assert "project" in text and "managed" in text


class TestTheWeakerChecksAreRejected:
    """MUTATION: substituting a weaker instrument must change the outcome."""

    def test_mutation_a_presence_only_check_passes_where_the_real_one_fails(self):
        """The mutant is blind to exactly what the criterion is about."""
        altered = copy.deepcopy(STOP_ENTRY)
        altered[0]["hooks"][0]["command"] = "python something-else.py"
        before = _document()
        after = _document(hooks={"Stop": altered, "Notification": NOTIFICATION_ENTRY})

        assert presence_only_verdict(before, after) == [], "the mutant did not differ from the real check"
        assert retention_verdict(before, after)["problems"], "the real check missed a rewritten command"

    def test_mutation_whole_file_equality_fails_where_the_real_one_is_silent(self):
        """The mutant reports a failure exactly where the criterion permits one.

        The comparison is the sibling module's, not a second copy, so the two
        modules reject the same wrong instrument.
        """
        before = _document()
        after = _document(enabledPlugins={}, extraKnownMarketplaces={})

        assert retention_verdict(before, after)["problems"] == []
        assert attribution.whole_file_equality_verdict(before, after)

    def test_mutation_the_instruments_agree_on_a_genuine_loss(self):
        """The mutants are not uniformly wrong; they are wrong in one direction.

        Stated so the results above are not read as "any weaker check always
        disagrees". On an entry the cycle deleted, all three report a problem.
        """
        before = _document()
        after = _document(hooks={"Notification": NOTIFICATION_ENTRY})

        assert retention_verdict(before, after)["problems"]
        assert presence_only_verdict(before, after)
        assert attribution.whole_file_equality_verdict(before, after)


class TestTheProcedureRunsFromItsStoredForm:
    """The command CI proves working is the command the document ships."""

    def test_the_stored_fingerprint_command_executes_and_prints_all_four_digests(self, tmp_path):
        """Run the stored snapshot command verbatim against a scratch file."""
        command = attribution._stored_python_command(PROCEDURE_DOC.read_text(encoding="utf-8"), "hooks")
        target = tmp_path / "settings.json"
        target.write_text(_document(), encoding="utf-8")

        completed = attribution._run_stored_command(command, target)

        assert completed.returncode == 0, completed.stderr
        printed = json.loads(completed.stdout)
        assert printed["file"] == file_digest(_document())
        hooks = tool.hooks_block(parse_settings(_document()))
        assert printed["hooks_block"] == tool.digest_of(hooks)
        assert printed["entries"]["Stop"] == tool.digest_of(hooks["Stop"])
        assert printed["entry_bytes"]["Notification"] == entry_source_digest(
            _document(), "Notification", hooks["Notification"]
        )

    def test_specificity_the_stored_command_distinguishes_two_documents(self, tmp_path):
        """SPECIFICITY: a command printing constants would satisfy the test above."""
        command = attribution._stored_python_command(PROCEDURE_DOC.read_text(encoding="utf-8"), "hooks")
        altered = copy.deepcopy(STOP_ENTRY)
        altered[0]["hooks"][0]["timeout"] = 61
        first = tmp_path / "a.json"
        second = tmp_path / "b.json"
        first.write_text(_document(), encoding="utf-8")
        second.write_text(_document(hooks={"Stop": altered, "Notification": NOTIFICATION_ENTRY}), encoding="utf-8")

        left = json.loads(attribution._run_stored_command(command, first).stdout)
        right = json.loads(attribution._run_stored_command(command, second).stdout)

        assert left["entries"]["Stop"] != right["entries"]["Stop"]
        assert left["entries"]["Notification"] == right["entries"]["Notification"]

    def test_negative_extraction_fails_when_the_stored_command_is_gone(self):
        """NEGATIVE: the extractor cannot silently find nothing and pass."""
        with pytest.raises(AssertionError):
            attribution._stored_python_command("# a procedure with no commands in it\n", "hooks")


class TestTheProcedureDocumentSaysWhatItMust:
    """The granularity distinction cannot be allowed to drop out of the document."""

    def test_the_document_records_the_measurement_as_not_performed(self):
        """The blocked state is written down, in the shape V2-016 established."""
        assert PROCEDURE_DOC.is_file(), "missing procedure: {0}".format(PROCEDURE_DOC.as_posix())
        text = PROCEDURE_DOC.read_text(encoding="utf-8")

        assert "NOT PERFORMED" in text
        assert LIVE_INSTALL_ENV in text
        assert SNAPSHOT_BEFORE_ENV in text
        assert SNAPSHOT_AFTER_ENV in text
        assert "test_live_cycle_leaves_the_retained_hooks_intact" in text

    def test_the_document_names_all_four_granularities(self):
        """The ladder is the finding; a document that lost it lost the point."""
        assert check_granularity_ladder(PROCEDURE_DOC.read_text(encoding="utf-8")) == []

    @pytest.mark.parametrize("token", GRANULARITY_TOKENS)
    def test_negative_dropping_any_one_granularity_is_caught(self, token):
        """NEGATIVE: each rung is separately required, not absorbed by the others."""
        text = PROCEDURE_DOC.read_text(encoding="utf-8")
        assert token in text, "the fixture text is stale: {0!r}".format(token)

        problems = check_granularity_ladder(text.replace(token, ""))

        assert problems, "removing {0!r} produced no violation".format(token)
        assert any(token in problem for problem in problems), problems

    def test_the_document_is_ascii_only(self):
        """The document ships under the same encoding rule as everything else."""
        text = PROCEDURE_DOC.read_text(encoding="utf-8")
        offenders = sorted({character for character in text if ord(character) > 127})
        assert not offenders, offenders


class TestLiveCycleMeasurement:
    """The criterion itself: blocked by an owner ruling, not by a limitation."""

    def test_live_cycle_leaves_the_retained_hooks_intact(self):
        """Compute the FR-8 verdict from snapshots a live cycle produced.

        This test is complete and runnable. What it does not do, and must not do,
        is perform the install/uninstall cycle itself: the owner ruled that no
        live cycle may be run. The operator performs the authorised half by
        following ``docs/guides/fr8-hook-retention-verification.md``, which
        writes the two snapshots this test then judges.

        The two snapshots are NOT the ones V2-022 and V2-023 consume. Theirs are
        taken after install and after register; this criterion's window opens
        BEFORE install and closes AFTER uninstall, and using their ``before.json``
        here would measure a strictly narrower window and report it as this one.
        """
        if not _live_measurement_available():
            pytest.skip(_blocked_reason())

        before = Path(os.environ[SNAPSHOT_BEFORE_ENV]).read_text(encoding="utf-8")
        after = Path(os.environ[SNAPSHOT_AFTER_ENV]).read_text(encoding="utf-8")

        verdict = retention_verdict(before, after)

        assert verdict["entries"], (
            "the pre-install snapshot registered neither retained hook, so this run measures "
            "nothing. Confirm the snapshot is the settings file the host actually writes and repeat."
        )
        assert verdict["problems"] == [], verdict["problems"]
        assert verdict["byte_problems"] == [], verdict["byte_problems"]

    def test_the_blocked_test_body_is_rehearsed_against_both_verdicts(self, tmp_path, monkeypatch):
        """Prove the blocked test computes a verdict rather than never running.

        A skipped test is indistinguishable from a test whose body cannot work.
        This drives the identical snapshot-reading path with synthetic files and
        requires a clean verdict on a correct cycle and a dirty one on an
        altered entry.
        """
        altered = copy.deepcopy(STOP_ENTRY)
        altered[0]["hooks"][0]["command"] = "python someone-elses-notifier.py"
        before_path = tmp_path / "install-before.json"
        before_path.write_text(_document(), encoding="utf-8")
        clean = tmp_path / "after-clean.json"
        clean.write_text(_document(enabledPlugins={}, extraKnownMarketplaces={}), encoding="utf-8")
        dirty = tmp_path / "after-dirty.json"
        dirty.write_text(
            _document(hooks={"Stop": altered, "Notification": NOTIFICATION_ENTRY}, enabledPlugins={}),
            encoding="utf-8",
        )

        monkeypatch.setenv(LIVE_INSTALL_ENV, "1")
        monkeypatch.setenv(SNAPSHOT_BEFORE_ENV, str(before_path))

        monkeypatch.setenv(SNAPSHOT_AFTER_ENV, str(clean))
        assert _live_measurement_available()
        self.test_live_cycle_leaves_the_retained_hooks_intact()

        monkeypatch.setenv(SNAPSHOT_AFTER_ENV, str(dirty))
        with pytest.raises(AssertionError):
            self.test_live_cycle_leaves_the_retained_hooks_intact()

    def test_the_rehearsal_also_covers_the_vacuous_snapshot(self, tmp_path, monkeypatch):
        """A snapshot with no retained hook must fail, not pass by having nothing to check."""
        before_path = tmp_path / "install-before.json"
        before_path.write_text(_document(hooks={}), encoding="utf-8")
        after_path = tmp_path / "after.json"
        after_path.write_text(_document(hooks={}), encoding="utf-8")

        monkeypatch.setenv(LIVE_INSTALL_ENV, "1")
        monkeypatch.setenv(SNAPSHOT_BEFORE_ENV, str(before_path))
        monkeypatch.setenv(SNAPSHOT_AFTER_ENV, str(after_path))

        with pytest.raises(AssertionError) as raised:
            self.test_live_cycle_leaves_the_retained_hooks_intact()
        assert "measures" in str(raised.value)

    def test_the_skip_reason_names_the_ruling_and_the_way_forward(self):
        """A skip a reader cannot act on is a silent skip with extra words."""
        reason = _blocked_reason()

        assert "owner" in reason.lower()
        assert LIVE_INSTALL_ENV in reason
        assert PROCEDURE_DOC.name in reason
        assert "byte-identical" in reason.lower()

    def test_the_availability_gate_refuses_a_partial_environment(self):
        """NEGATIVE: two of three signals must not read as authorisation."""
        assert not _live_measurement_available()


def check_granularity_ladder(text):
    """Check a document names every granularity this module distinguishes.

    Args:
        text: Full document text.

    Returns:
        list: One message per missing granularity.
    """
    return [
        "the document does not name the {0!r} granularity".format(token)
        for token in GRANULARITY_TOKENS
        if token not in text
    ]


def _live_measurement_available():
    """Report whether an authorised live measurement supplied its snapshots.

    Returns:
        bool: True when authorisation and both snapshot files are present.
    """
    if os.environ.get(LIVE_INSTALL_ENV, "").strip() != "1":
        return False
    for name in (SNAPSHOT_BEFORE_ENV, SNAPSHOT_AFTER_ENV):
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
        "BLOCKED, NOT PASSED. SRS FR-18 asks that an install/uninstall cycle leave the "
        "pre-existing user-level Stop and Notification entries byte-identical, and that "
        "needs a live claude plugin install followed by claude plugin uninstall. The "
        "project owner ruled that no live cycle may be run: install writes enabledPlugins "
        "and extraKnownMarketplaces into a settings scope and uninstall only empties them, "
        "so at user scope the ruling protects the owner's live configuration and at local "
        "scope a git-tracked file in this repository. V2-027 proved these two entries "
        "survive a HOOK-DELETION operation; that is a different operation and is not "
        "evidence for this one. This test is complete and will run as written once an "
        "operator with authorisation follows {0} and exports {1}=1 together with {2} and "
        "{3}. Do not substitute a hand-edited settings file for the measurement.".format(
            PROCEDURE_DOC.name,
            LIVE_INSTALL_ENV,
            SNAPSHOT_BEFORE_ENV,
            SNAPSHOT_AFTER_ENV,
        )
    )

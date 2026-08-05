"""Tests for the uninstall-residue runbook (PRD FR-24 / SRS FR-36).

The acceptance criterion for FR-36 asks only that the NFR-11 uninstall test
assert the runbook file exists. That assertion alone is close to worthless: a
file can exist and name a marketplace that was renamed six months ago, and the
test would still pass. What actually rots in a document like this is the exact
path strings, so the checks here derive every name from the two manifests --
``plugin/.claude-plugin/plugin.json`` and ``.claude-plugin/marketplace.json`` --
and fail when the runbook and the manifests disagree. A rename now breaks a
test instead of silently invalidating the document.

Two further things are machine-checked because this project's history says they
are the two that go wrong:

- Every row of the residue inventory carries an evidence label drawn from a
  closed vocabulary, so a claim cannot be promoted from INFERRED to MEASURED by
  accident. ADR-020 Path C is the live example: it is inferred and must stay
  labelled that way.
- The line citations into ``plugin_schema_spike.md`` are resolved against the
  file. REVIEW-INDEX corrections 28-30 record 36 stale citations across 6
  documents, several landing on blank lines, from exactly this failure mode.

Every check below is paired with a NEGATIVE test that plants a violation and
proves the check rejects it, and with a SPECIFICITY test proving the same check
accepts the real, correct document. A check observed only to pass is
indistinguishable from a check that cannot fail.
"""

import json
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
RUNBOOK_PATH = REPO_ROOT / "docs" / "guides" / "uninstall-residue.md"
PLUGIN_MANIFEST_PATH = REPO_ROOT / "plugin" / ".claude-plugin" / "plugin.json"
MARKETPLACE_MANIFEST_PATH = REPO_ROOT / ".claude-plugin" / "marketplace.json"
SPIKE_PATH = REPO_ROOT / "docs" / "phase-1-architecture" / "plugin_schema_spike.md"

EVIDENCE_VOCABULARY = frozenset({"MEASURED", "INFERRED", "NOT MEASURED"})

LIMITATION_HEADING_PATTERN = re.compile(
    r"^##\s+\d+\.\s+Accepted Claude-Code-level limitation: the orphaned plugin cache directory\s*$",
    re.MULTILINE,
)

PLACEHOLDER_PATTERNS = (
    "<marketplace>",
    "<plugin>",
    "<plugin-name>",
    "<version>",
    "<MARKETPLACE>",
    "<PLUGIN>",
    "<VERSION>",
    "PLACEHOLDER",
    "TODO",
    "TBD",
    "FIXME",
    "XXX",
    "fr14a-spike",
    "your-plugin",
    "your-marketplace",
    "example-plugin",
    "example-marketplace",
)

SPIKE_CITATIONS = (
    (3, "2.1.220"),
    (171, "## Item 4 --"),
    (176, "`enabledPlugins` key is **not removed**"),
    (182, ".orphaned_at"),
    (189, "`extraKnownMarketplaces` key is **not removed**"),
    (198, "claude plugin prune -y"),
)


def read_identity():
    """Read the plugin and marketplace identity strings from the manifests.

    These are the source of truth for every name the runbook is allowed to use.
    Nothing here is hardcoded, so a rename in either manifest propagates into
    every assertion below.

    Returns:
        dict: Keys ``plugin``, ``version``, ``marketplace``, ``source``.
    """
    plugin = json.loads(PLUGIN_MANIFEST_PATH.read_text(encoding="utf-8"))
    marketplace = json.loads(MARKETPLACE_MANIFEST_PATH.read_text(encoding="utf-8"))
    entries = [e for e in marketplace["plugins"] if e.get("name") == plugin["name"]]
    return {
        "plugin": plugin["name"],
        "version": plugin["version"],
        "marketplace": marketplace["name"],
        "source": entries[0]["source"] if entries else None,
    }


def expected_strings(identity):
    """Build the exact strings the runbook must contain for this identity.

    Args:
        identity: Mapping returned by :func:`read_identity`.

    Returns:
        dict: Label to required literal string.
    """
    plugin = identity["plugin"]
    marketplace = identity["marketplace"]
    version = identity["version"]
    return {
        "qualified plugin id": "{0}@{1}".format(plugin, marketplace),
        "orphaned cache directory": "~/.claude/plugins/cache/{0}/{1}/{2}".format(marketplace, plugin, version),
        "plugin data directory": "~/.claude/plugins/data/{0}-{1}".format(plugin, marketplace),
        "marketplace name": marketplace,
        "plugin name": plugin,
    }


def check_identity_strings(text, identity):
    """Check the runbook names the identity the manifests actually declare.

    Args:
        text: Full runbook text.
        identity: Mapping returned by :func:`read_identity`.

    Returns:
        list: One message per required string that is absent.
    """
    return [
        "runbook does not contain the {0}: {1}".format(label, value)
        for label, value in sorted(expected_strings(identity).items())
        if value not in text
    ]


def check_no_placeholders(text):
    """Check the runbook carries no unfilled or stale placeholder text.

    Args:
        text: Full runbook text.

    Returns:
        list: One message per placeholder token found.
    """
    return [
        "runbook contains placeholder or stale text: {0}".format(token)
        for token in PLACEHOLDER_PATTERNS
        if token in text
    ]


def check_manifests_agree(identity):
    """Check the two manifests describe the same plugin at the same location.

    The runbook's cache path is built from both manifests. If the marketplace
    entry stopped pointing at the directory that holds the plugin manifest, the
    path would be wrong in a way no string search of the runbook could detect.

    Args:
        identity: Mapping returned by :func:`read_identity`.

    Returns:
        list: One message per inconsistency found.
    """
    problems = []
    if identity["source"] is None:
        problems.append("marketplace.json has no plugins entry named {0}".format(identity["plugin"]))
        return problems
    resolved = (MARKETPLACE_MANIFEST_PATH.parent.parent / identity["source"]).resolve()
    if resolved != PLUGIN_MANIFEST_PATH.parent.parent.resolve():
        problems.append(
            "marketplace source {0} resolves to {1}, not the directory holding plugin.json".format(
                identity["source"], resolved.as_posix()
            )
        )
    return problems


def inventory_rows(text):
    """Extract the residue inventory rows from the runbook.

    Args:
        text: Full runbook text.

    Returns:
        list: One list of stripped cell strings per row whose first cell is an
        ``R``-prefixed identifier.
    """
    rows = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if cells and re.fullmatch(r"R\d+", cells[0]):
            rows.append(cells)
    return rows


def check_evidence_labels(text, minimum_rows=6):
    """Check every residue row carries labels from the closed vocabulary.

    Args:
        text: Full runbook text.
        minimum_rows: Least number of inventory rows the runbook must carry.

    Returns:
        list: One message per row with a missing or out-of-vocabulary label.
    """
    rows = inventory_rows(text)
    problems = []
    if len(rows) < minimum_rows:
        problems.append("residue inventory has {0} rows, expected at least {1}".format(len(rows), minimum_rows))
    for cells in rows:
        if len(cells) < 4:
            problems.append("row {0} has {1} columns, expected at least 4".format(cells[0], len(cells)))
            continue
        for column, label in (("behaviour", cells[2]), ("path", cells[3])):
            if label not in EVIDENCE_VOCABULARY:
                problems.append(
                    "row {0} {1} evidence is {2!r}, not one of {3}".format(
                        cells[0], column, label, sorted(EVIDENCE_VOCABULARY)
                    )
                )
    return problems


def check_limitation_section(text):
    """Check the V2-022 anchor section exists and names both accepted items.

    Args:
        text: Full runbook text.

    Returns:
        list: One message per missing element.
    """
    match = LIMITATION_HEADING_PATTERN.search(text)
    if match is None:
        return ["runbook has no 'Accepted Claude-Code-level limitation' heading for the orphaned cache directory"]
    body = text[match.end() :]
    next_heading = re.search(r"^##\s", body, re.MULTILINE)
    section = body[: next_heading.start()] if next_heading else body
    problems = []
    if ".orphaned_at" not in section:
        problems.append("limitation section does not name the .orphaned_at marker")
    if "~/.claude/plugins/cache/" not in section:
        problems.append("limitation section does not name the orphaned cache directory path")
    return problems


def check_spike_citations(spike_lines, citations=SPIKE_CITATIONS):
    """Check each cited spike line still carries the content cited from it.

    Args:
        spike_lines: The spike document split into lines, 0-indexed.
        citations: Iterable of ``(line_number, expected_substring)`` pairs, with
            line numbers 1-indexed as they appear in the runbook's citations.

    Returns:
        list: One message per citation that no longer resolves.
    """
    problems = []
    for number, expected in citations:
        if number > len(spike_lines):
            problems.append("spike citation line {0} is past end of file".format(number))
            continue
        line = spike_lines[number - 1]
        if expected not in line:
            problems.append("spike line {0} does not contain {1!r}; found {2!r}".format(number, expected, line.strip()))
    return problems


@pytest.fixture(scope="module")
def runbook_text():
    """Load the runbook once for the module.

    Returns:
        str: Full runbook text.
    """
    return RUNBOOK_PATH.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def identity():
    """Load the manifest identity once for the module.

    Returns:
        dict: Mapping returned by :func:`read_identity`.
    """
    return read_identity()


def test_runbook_file_exists():
    """The runbook file exists at the path FR-36 and PRD FR-24 both name."""
    assert RUNBOOK_PATH.is_file(), "missing runbook: {0}".format(RUNBOOK_PATH.as_posix())


def test_runbook_is_ascii_only(runbook_text):
    """The runbook contains no non-ASCII characters."""
    offenders = sorted({character for character in runbook_text if ord(character) > 127})
    assert not offenders, "non-ASCII characters in runbook: {0}".format(offenders)


def test_identity_strings_present(runbook_text, identity):
    """SPECIFICITY: the real runbook names the real manifest identity."""
    assert check_identity_strings(runbook_text, identity) == []


def test_identity_strings_reject_a_renamed_marketplace(runbook_text, identity):
    """NEGATIVE: a marketplace rename that the runbook missed is caught."""
    renamed = dict(identity, marketplace="renamed-org")
    problems = check_identity_strings(runbook_text, renamed)
    assert problems, "a renamed marketplace produced no violation"
    assert any("renamed-org" in problem for problem in problems)


def test_identity_strings_reject_a_bumped_version(runbook_text, identity):
    """NEGATIVE: a version bump the runbook's cache path missed is caught."""
    bumped = dict(identity, version="9.9.9")
    problems = check_identity_strings(runbook_text, bumped)
    assert problems, "a bumped version produced no violation"
    assert any("9.9.9" in problem for problem in problems)


def test_identity_strings_reject_a_stale_path_in_the_runbook(identity):
    """NEGATIVE: a stale path left in the runbook body is caught."""
    stale = RUNBOOK_PATH.read_text(encoding="utf-8").replace(identity["marketplace"], "old-org")
    problems = check_identity_strings(stale, identity)
    assert problems, "a runbook naming the wrong marketplace produced no violation"


def test_no_placeholders_present(runbook_text):
    """SPECIFICITY: the real runbook carries no placeholder or stale text."""
    assert check_no_placeholders(runbook_text) == []


@pytest.mark.parametrize("token", ["<marketplace>", "TODO", "fr14a-spike", "PLACEHOLDER"])
def test_placeholder_check_rejects_planted_tokens(runbook_text, token):
    """NEGATIVE: each planted placeholder token is caught."""
    planted = runbook_text + "\n\nLeftover: {0}\n".format(token)
    problems = check_no_placeholders(planted)
    assert any(token in problem for problem in problems), "planted {0} was not caught".format(token)


def test_placeholder_check_does_not_fire_on_ordinary_prose(runbook_text):
    """SPECIFICITY: adding harmless prose does not trip the placeholder check."""
    benign = runbook_text + "\n\nThis paragraph names no placeholder at all.\n"
    assert check_no_placeholders(benign) == []


def test_manifests_agree(identity):
    """SPECIFICITY: the marketplace entry points at the real plugin directory."""
    assert check_manifests_agree(identity) == []


def test_manifests_agree_rejects_a_dangling_source(identity):
    """NEGATIVE: a marketplace source pointing elsewhere is caught."""
    problems = check_manifests_agree(dict(identity, source="./does-not-exist"))
    assert problems, "a dangling marketplace source produced no violation"


def test_manifests_agree_rejects_a_missing_entry(identity):
    """NEGATIVE: a marketplace with no entry for this plugin is caught."""
    problems = check_manifests_agree(dict(identity, source=None))
    assert problems, "a missing marketplace entry produced no violation"


def test_evidence_labels_present(runbook_text):
    """SPECIFICITY: every residue row carries in-vocabulary evidence labels."""
    assert check_evidence_labels(runbook_text) == []


def test_evidence_rows_cover_every_documented_item(runbook_text):
    """Every residue row identifier from R1 to R6 is present exactly once."""
    identifiers = [cells[0] for cells in inventory_rows(runbook_text)]
    assert identifiers == ["R1", "R2", "R3", "R4", "R5", "R6"], identifiers


def test_adr020_path_c_row_is_not_labelled_measured(runbook_text):
    """The register-mcp row stays INFERRED until ADR-020 Path C is measured.

    This is the specific inference this project has most often promoted to a
    measurement by accident. The verification procedure that would settle it is
    ``docs/guides/adr-020-path-c-verification.md`` and it has not been run.
    """
    rows = {cells[0]: cells for cells in inventory_rows(runbook_text)}
    assert rows["R4"][2] == "INFERRED", "R4 behaviour evidence is {0!r}".format(rows["R4"][2])


def test_evidence_label_check_rejects_an_out_of_vocabulary_label(runbook_text):
    """NEGATIVE: a made-up evidence label such as CONFIRMED is caught."""
    row = next(cells for cells in inventory_rows(runbook_text) if cells[0] == "R4")
    original = "| {0} |".format(" | ".join(row))
    assert original in runbook_text, "row reconstruction does not match the source line"
    mutated = "| {0} |".format(" | ".join(row[:2] + ["CONFIRMED"] + row[3:]))
    problems = check_evidence_labels(runbook_text.replace(original, mutated, 1))
    assert any("CONFIRMED" in problem for problem in problems), problems


def test_evidence_label_check_rejects_a_truncated_inventory(runbook_text):
    """NEGATIVE: dropping residue rows below the required minimum is caught."""
    trimmed = "\n".join(line for line in runbook_text.splitlines() if not line.strip().startswith("| R"))
    problems = check_evidence_labels(trimmed)
    assert any("expected at least" in problem for problem in problems), problems


def test_limitation_section_present(runbook_text):
    """SPECIFICITY: the V2-022 anchor section exists and names both items."""
    assert check_limitation_section(runbook_text) == []


def test_limitation_section_check_rejects_a_renamed_heading(runbook_text):
    """NEGATIVE: renaming the anchor heading is caught."""
    renamed = runbook_text.replace(
        "Accepted Claude-Code-level limitation: the orphaned plugin cache directory",
        "Some other section title",
    )
    assert check_limitation_section(renamed), "a renamed anchor heading produced no violation"


def test_limitation_section_check_rejects_a_missing_marker(runbook_text):
    """NEGATIVE: dropping the .orphaned_at marker from the section is caught."""
    match = LIMITATION_HEADING_PATTERN.search(runbook_text)
    head, tail = runbook_text[: match.end()], runbook_text[match.end() :]
    next_heading = re.search(r"^##\s", tail, re.MULTILINE)
    section, rest = tail[: next_heading.start()], tail[next_heading.start() :]
    stripped = head + section.replace(".orphaned_at", "the marker file") + rest
    problems = check_limitation_section(stripped)
    assert any("orphaned_at" in problem for problem in problems), problems


def test_spike_citations_resolve():
    """SPECIFICITY: every cited spike line still carries what is cited from it.

    REVIEW-INDEX corrections 28-30 record 36 stale citations across 6 documents.
    This check is why the runbook's line numbers are worth carrying at all.
    """
    lines = SPIKE_PATH.read_text(encoding="utf-8").splitlines()
    assert check_spike_citations(lines) == []


def test_spike_citation_check_rejects_drift():
    """NEGATIVE: inserting lines above a citation is caught as drift."""
    lines = SPIKE_PATH.read_text(encoding="utf-8").splitlines()
    shifted = ["inserted line"] * 5 + lines
    problems = check_spike_citations(shifted)
    assert problems, "a five-line upward shift produced no citation violation"


def test_spike_citation_check_rejects_a_citation_past_end_of_file():
    """NEGATIVE: a citation beyond the file's length is caught."""
    problems = check_spike_citations(["only line"], citations=((999, "anything"),))
    assert any("past end of file" in problem for problem in problems), problems


def check_registry_ids_named(text, registry):
    """Check the runbook names every MCP server id the plugin can register.

    R4's path is only correct while these ids match ``plugin/mcp-registry.json``.
    A server renamed there, or a third one added, silently invalidates the row.

    Args:
        text: Full runbook text.
        registry: Parsed ``mcp-registry.json`` mapping.

    Returns:
        list: One message per server id the runbook does not name.
    """
    return [
        "runbook does not name MCP server id {0} from mcp-registry.json".format(server["id"])
        for server in registry["servers"]
        if server["id"] not in text
    ]


def test_registry_ids_named(runbook_text):
    """SPECIFICITY: the runbook names every registrable MCP server id."""
    registry = json.loads((REPO_ROOT / "plugin" / "mcp-registry.json").read_text(encoding="utf-8"))
    assert check_registry_ids_named(runbook_text, registry) == []


def test_registry_id_check_rejects_an_unnamed_server(runbook_text):
    """NEGATIVE: a server id the runbook never mentions is caught."""
    registry = {"servers": [{"id": "some-server-nobody-documented"}]}
    problems = check_registry_ids_named(runbook_text, registry)
    assert problems, "an undocumented server id produced no violation"


def test_ledger_file_name_matches_the_source(runbook_text):
    """R5's path matches the ledger file name the plugin script declares.

    The runbook names ``~/.claude/cwe-mcp-registrations.json``. That is only
    right while ``mcp_registration.py`` still uses that file name; a rename
    there would leave the runbook pointing at a file that never exists.
    """
    source = (REPO_ROOT / "plugin" / "scripts" / "mcp_registration.py").read_text(encoding="utf-8")
    match = re.search(r'LEDGER_FILE_NAME\s*=\s*"([^"]+)"', source)
    assert match is not None, "LEDGER_FILE_NAME not found in mcp_registration.py"
    assert match.group(1) in runbook_text, "runbook does not name the ledger file {0}".format(match.group(1))


def test_runbook_names_the_adr020_verification_procedure(runbook_text):
    """The runbook points at the procedure that would settle its one inference."""
    assert "docs/guides/adr-020-path-c-verification.md" in runbook_text


def test_runbook_names_its_own_evidence_source(runbook_text):
    """The runbook cites the spike it draws every MEASURED claim from."""
    assert "docs/phase-1-architecture/plugin_schema_spike.md" in runbook_text

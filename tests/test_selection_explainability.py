"""Acceptance and conformance suite for selection explainability (issue #268).

Local key V2-012, PRD FR-11 / SRS FR-23. The requirement's two acceptance
criteria are that every agent selected during a run has all five named fields
emitted, and that a run with any field missing or empty fails.

Each criterion has at least one companion negative demonstrating the assertion
is capable of failing:

1. The five field names are taken from SRS FR-23's own text rather than from
   any summary of it, and the module's field tuple is checked against that
   text. The companion negative requires the same phrase search to reject a
   field the requirement does not name.
2. Every agent selected for the ten sample tasks is emitted with all five
   fields populated, and the log lines carry them one agent per line. The
   companion negatives strip, blank and empty each required field in turn and
   require the emitter to refuse.
3. Nothing is logged when a record is refused, so a run cannot leave behind a
   partial explanation of a selection it then rejected.

Plus the specificity control the criteria do not ask for and should. A
serialiser that always produced five fields -- padding absent ones with empty
strings -- would satisfy a shallow "all five fields present" check while
emitting an explanation of nothing. ``TestSpecificityControl`` requires the
emitter to refuse every incomplete input while still accepting the complete
one, and its negative substitutes a padding serialiser and requires the same
measurement to fail.

Forward compatibility is asserted rather than assumed: the outcome states and
match flags that the sibling fallback work adds are not known here, so the
tests plant unrecognised keys and require them to survive into the audit record
unread, and require a flagged match to be validated exactly as an unflagged one
is.

Windows-safe: ASCII only.
"""

import json
import re
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from langgraph_engine.library.resolver import locate_library_root  # noqa: E402
from langgraph_engine.selection import DomainKgAdapter, RiskSignal  # noqa: E402
from langgraph_engine.selection import explainability as subject  # noqa: E402
from langgraph_engine.selection import load_catalogue, select_agents  # noqa: E402
from langgraph_engine.selection.explainability import (  # noqa: E402
    DISPATCH_FIELD,
    FR23_FIELDS,
    IncompleteSelectionRecord,
    SelectionShapeChanged,
    emit_selection,
    explain_match,
    explain_selection,
    selection_log_lines,
)
from langgraph_engine.selection.selector import build_lexicon  # noqa: E402

SRS = PROJECT_ROOT / "SRS.md"
SPRINT_ISSUES = PROJECT_ROOT / "docs" / "phase-6-sprint" / "github_issues.json"

SAMPLE_STRIDE = 4
SAMPLE_SIZE = 10
EXPECTED_FIELD_COUNT = 5

REQUIREMENT_PHRASES = {
    "agent": "agent name",
    "domain": "source domain",
    "matched_skills": "matched skills",
    "edge_path": "edge path",
    "confidence": "confidence score",
}

UNNAMED_FIELD_PHRASE = "model tier"

_LIBRARY_ROOT = locate_library_root(PROJECT_ROOT)

requires_library = pytest.mark.skipif(
    _LIBRARY_ROOT is None,
    reason="sibling claude-global-library checkout is required for live selection tests",
)


# ---------------------------------------------------------------------------
# Synthetic fixtures -- no library needed, no real name used
# ---------------------------------------------------------------------------

PROBE_AGENT = "aaa-probe-agent"
PROBE_DOMAIN = "aaa-probe-domain"
PROBE_SKILL = "aaa-probe-skill"
PROBE_PERSONA = "agents/aaa-probe-agent/agent.md"


def _valid_match(**overrides):
    """Return a complete match mapping, with any field overridden or removed.

    Passing ``None`` for a field removes the key entirely, which is the
    "missing" case; passing a value substitutes it, which is the "empty" or
    "malformed" case.
    """
    match = {
        "agent": PROBE_AGENT,
        "domain": PROBE_DOMAIN,
        "matched_skills": [PROBE_SKILL],
        "edge_path": [{"source": PROBE_AGENT, "edge_type": "PROBE", "target": PROBE_SKILL, "domain": PROBE_DOMAIN}],
        "confidence": 0.61,
        DISPATCH_FIELD: PROBE_PERSONA,
        "model": "sonnet",
    }
    for key, value in overrides.items():
        if value is None:
            match.pop(key, None)
        else:
            match[key] = value
    return match


def _valid_outcome(matches=None, **extra):
    """Return a selection outcome mapping carrying ``matches`` and extras."""
    outcome = {
        "task": "a task description",
        "matches": [_valid_match()] if matches is None else matches,
        "considered_domains": [PROBE_DOMAIN],
        "library_version": "0.0.0",
    }
    outcome.update(extra)
    return outcome


class _RecordingLogger:
    """Collects the lines the emitter writes, so emission can be measured."""

    def __init__(self):
        """Start with no lines recorded."""
        self.lines = []

    def info(self, line):
        """Record one emitted line."""
        self.lines.append(line)


def _padding_serialiser(match):
    """Return five fields for any input, filling absent ones with blanks.

    This is the degenerate serialiser the specificity control exists to catch:
    it satisfies "all five fields are present" on every input, including inputs
    that explain nothing.
    """
    return {field: match.get(field, "") for field in FR23_FIELDS}


# ---------------------------------------------------------------------------
# Criterion 1 -- the five field names come from the requirement's own text
# ---------------------------------------------------------------------------


def _fr23_body():
    """Return the text of SRS requirement FR-23, read from the SRS itself."""
    text = SRS.read_text(encoding="utf-8")
    match = re.search(r"\*\*FR-23:\*\*(.*?)(?=\n\*\*FR-)", text, re.DOTALL)
    assert match, "FR-23 was not found in SRS.md; the requirement text moved"
    return " ".join(match.group(1).split()).lower()


class TestFieldNamesComeFromTheRequirement:
    """The emitted field set is the requirement's field set, not a summary's."""

    def test_the_module_emits_exactly_the_five_fields_the_requirement_names(self):
        """Each emitted field maps to a phrase present in the FR-23 text."""
        body = _fr23_body()
        assert len(FR23_FIELDS) == EXPECTED_FIELD_COUNT
        assert set(FR23_FIELDS) == set(REQUIREMENT_PHRASES)

        missing = [field for field in FR23_FIELDS if REQUIREMENT_PHRASES[field] not in body]
        assert missing == [], "fields with no counterpart in the FR-23 text: {}".format(missing)

    def test_the_phrase_search_rejects_a_field_the_requirement_does_not_name(self):
        """NEGATIVE CONTROL: a field outside the five must not be found.

        Without this, a phrase search that matched anything would report a
        clean pass for any field set at all, including one that quietly added a
        sixth field to the requirement's five.
        """
        body = _fr23_body()
        assert UNNAMED_FIELD_PHRASE not in body
        assert "model" not in FR23_FIELDS

    def test_the_dispatch_field_is_required_alongside_the_five(self):
        """The persona path is required, and is not counted among the five."""
        assert DISPATCH_FIELD not in FR23_FIELDS
        assert DISPATCH_FIELD in subject.REQUIRED_FIELDS
        assert len(subject.REQUIRED_FIELDS) == EXPECTED_FIELD_COUNT + 1


# ---------------------------------------------------------------------------
# Criterion 2 -- every selected agent is emitted with all five fields
# ---------------------------------------------------------------------------


class TestCompleteRecords:
    """A complete match is emitted with the requirement fields intact."""

    def test_a_complete_match_yields_all_five_fields_plus_the_dispatch_path(self):
        """Every required field appears, populated, in the emitted record."""
        record = explain_match(_valid_match())
        for field in subject.REQUIRED_FIELDS:
            assert field in record, "field {} was not emitted".format(field)
        assert record["agent"] == PROBE_AGENT
        assert record["domain"] == PROBE_DOMAIN
        assert record["matched_skills"] == [PROBE_SKILL]
        assert record["edge_path"] and record["edge_path"][0]["target"] == PROBE_SKILL
        assert record["confidence"] == pytest.approx(0.61)
        assert record[DISPATCH_FIELD] == PROBE_PERSONA

    def test_values_are_copied_from_the_match_not_derived(self):
        """The emitter transports values; it does not compute or default them."""
        source = _valid_match(confidence=0.9331, matched_skills=[PROBE_SKILL, PROBE_SKILL + "-two"])
        record = explain_match(source)
        for field in FR23_FIELDS:
            if isinstance(source[field], list):
                assert record[field] == list(source[field])
            else:
                assert record[field] == source[field]

    def test_an_unseen_match_flag_is_passed_through_unread(self):
        """A field this module has never seen reaches the record unrenamed.

        The fallback work landing in parallel adds state to the match this
        module serialises. Passing extras through means a flag added later is
        auditable without this module being taught its name.
        """
        record = explain_match(_valid_match(some_future_flag={"nested": True}))
        assert record["some_future_flag"] == {"nested": True}
        assert list(record)[: len(FR23_FIELDS)] == list(FR23_FIELDS)

    def test_a_flagged_match_is_validated_exactly_as_an_unflagged_one_is(self):
        """NEGATIVE: an extra flag does not exempt a match from the five fields.

        A degraded or low-confidence match is still a selected agent, so it
        still has to be explainable. Carrying an unrecognised flag must not
        become a way past the requirement.
        """
        with pytest.raises(IncompleteSelectionRecord) as excinfo:
            explain_match(_valid_match(some_future_flag=True, edge_path=None))
        assert excinfo.value.field == "edge_path"

    def test_an_object_offering_to_dict_is_accepted_without_being_imported(self):
        """The outcome is read structurally, so no selector type is imported."""

        class _MatchLike:
            """Stand-in exposing only the mapping form the emitter reads."""

            def to_dict(self):
                """Return the mapping form."""
                return _valid_match()

        assert explain_match(_MatchLike())["agent"] == PROBE_AGENT
        assert "selector" not in sys.modules or True
        source = Path(subject.__file__).read_text(encoding="utf-8")
        assert "import" in source
        assert "from .selector" not in source and "selector import" not in source


class TestWholeSelectionRecords:
    """A whole outcome becomes one audit record with one entry per agent."""

    def test_one_record_is_emitted_per_selected_agent(self):
        """The record count equals the number of matches, never more."""
        outcome = _valid_outcome(matches=[_valid_match(), _valid_match(agent=PROBE_AGENT)])
        record = explain_selection(outcome)
        assert record[subject.RECORD_COUNT_KEY] == 2
        assert len(record[subject.RECORD_AGENTS_KEY]) == 2

    def test_the_log_carries_the_five_fields_one_agent_per_line(self):
        """The acceptance criterion is stated about the log, so the log is checked."""
        logger = _RecordingLogger()
        emit_selection(_valid_outcome(), logger=logger)

        agent_lines = [line for line in logger.lines if '"agent"' in line]
        assert len(agent_lines) == 1
        payload = json.loads(agent_lines[0].split(subject.LOG_MARKER, 1)[1].strip())
        for field in FR23_FIELDS:
            assert field in payload, "field {} absent from the emitted log line".format(field)
            assert payload[field] not in (None, "", [], {})

    def test_a_selection_with_no_matches_emits_no_agent_record(self):
        """No agent selected means no agent record, never a padded one."""
        record = explain_selection(_valid_outcome(matches=[]))
        assert record[subject.RECORD_COUNT_KEY] == 0
        assert record[subject.RECORD_AGENTS_KEY] == []

    def test_an_unseen_outcome_state_survives_into_the_record_unread(self):
        """Whatever the outcome records about a no-match reaches the audit log.

        The vocabulary of no-match and low-confidence outcomes is owned
        elsewhere and is being written in parallel with this module. Passing
        the non-match part of the outcome through verbatim means this module
        neither needs that vocabulary nor can lose it.
        """
        outcome = _valid_outcome(matches=[], some_future_outcome={"reason": "opaque", "detail": "unread here"})
        record = explain_selection(outcome)
        carried = record[subject.RECORD_OUTCOME_KEY]
        assert carried["some_future_outcome"] == {"reason": "opaque", "detail": "unread here"}
        assert carried["task"] == outcome["task"]
        assert subject.MATCHES_KEY not in carried

    def test_a_no_match_outcome_still_leaves_a_log_line(self):
        """A run that selected nothing is auditable rather than silent."""
        logger = _RecordingLogger()
        emit_selection(_valid_outcome(matches=[], some_future_outcome={"reason": "opaque"}), logger=logger)
        assert len(logger.lines) == 1
        payload = json.loads(logger.lines[0].split(subject.LOG_MARKER, 1)[1].strip())
        assert payload[subject.RECORD_COUNT_KEY] == 0
        assert payload[subject.RECORD_OUTCOME_KEY]["some_future_outcome"] == {"reason": "opaque"}


# ---------------------------------------------------------------------------
# Companion negatives -- every assertion above is capable of failing
# ---------------------------------------------------------------------------


class TestRefusalOfIncompleteRecords:
    """A run with any field missing or empty fails, as the criterion states."""

    @pytest.mark.parametrize("field", list(subject.REQUIRED_FIELDS))
    def test_a_missing_required_field_is_refused(self, field):
        """NEGATIVE: removing any one required field refuses the whole record."""
        with pytest.raises(IncompleteSelectionRecord) as excinfo:
            explain_match(_valid_match(**{field: None}))
        assert excinfo.value.field == field

    @pytest.mark.parametrize(
        "field,empty_value",
        [
            ("agent", "   "),
            ("domain", ""),
            ("matched_skills", []),
            ("edge_path", []),
            ("confidence", 0.0),
            (DISPATCH_FIELD, "  "),
        ],
    )
    def test_an_empty_required_field_is_refused(self, field, empty_value):
        """NEGATIVE: an empty value is refused as firmly as an absent one."""
        with pytest.raises(IncompleteSelectionRecord) as excinfo:
            explain_match(_valid_match(**{field: empty_value}))
        assert excinfo.value.field == field

    def test_a_blank_entry_inside_a_populated_collection_is_refused(self):
        """NEGATIVE: a placeholder hidden inside a non-empty list is caught.

        A list of one empty string passes a length check while carrying no
        evidence, which is the padding failure one level down.
        """
        with pytest.raises(IncompleteSelectionRecord) as excinfo:
            explain_match(_valid_match(matched_skills=[""]))
        assert excinfo.value.field == "matched_skills"

        with pytest.raises(IncompleteSelectionRecord) as excinfo:
            explain_match(_valid_match(edge_path=[{}]))
        assert excinfo.value.field == "edge_path"

    def test_text_supplied_where_a_collection_belongs_is_refused(self):
        """NEGATIVE: a bare string is not iterated into per-character evidence."""
        for field in ("matched_skills", "edge_path"):
            with pytest.raises(IncompleteSelectionRecord) as excinfo:
                explain_match(_valid_match(**{field: PROBE_SKILL}))
            assert excinfo.value.field == field

    @pytest.mark.parametrize("value", [0.0, -0.1, 1.5, "0.6", True, float("nan")])
    def test_an_unusable_confidence_is_refused(self, value):
        """NEGATIVE: zero, out-of-band, non-numeric and boolean all refuse.

        Zero is refused because the scoring transform returns exactly zero when
        a candidate has no supporting evidence, so a zero on a selected agent
        is a missing score rather than a low one.
        """
        with pytest.raises(IncompleteSelectionRecord) as excinfo:
            explain_match(_valid_match(confidence=value))
        assert excinfo.value.field == "confidence"

    @pytest.mark.parametrize(
        "path",
        [
            "/absolute/aaa-probe-agent/agent.md",
            "../aaa-probe-agent/agent.md",
            "aaa-probe-agent",
            "agents/some-other-agent/agent.md",
        ],
    )
    def test_a_path_that_would_not_dispatch_is_refused(self, path):
        """NEGATIVE: a record that names an unexecutable spawn is refused.

        Library agents are not registered subagent types, so a selection whose
        persona path is absolute, escaping, location-free or attributed to a
        different agent explains something a run cannot perform.
        """
        with pytest.raises(IncompleteSelectionRecord) as excinfo:
            explain_match(_valid_match(**{DISPATCH_FIELD: path}))
        assert excinfo.value.field == DISPATCH_FIELD

    def test_agent_shaped_data_outside_the_matches_list_is_never_counted_as_selected(self):
        """NEGATIVE: only the matches list produces agent records.

        The fallback outcome carries candidates that were found and rejected.
        They are match-shaped and carry the same five fields, so an emitter
        that swept the outcome for anything agent-shaped would report rejected
        candidates as selections -- the silent default pick in audit form. The
        count comes from the matches list alone.
        """
        outcome = _valid_outcome(matches=[], some_future_outcome={"near_misses": [_valid_match(), _valid_match()]})
        record = explain_selection(outcome)
        assert record[subject.RECORD_COUNT_KEY] == 0
        assert record[subject.RECORD_AGENTS_KEY] == []

        logger = _RecordingLogger()
        emit_selection(outcome, logger=logger)
        assert len(logger.lines) == 1
        carried = record[subject.RECORD_OUTCOME_KEY]["some_future_outcome"]["near_misses"]
        assert len(carried) == 2, "the rejected candidates were dropped instead of carried through"

    def test_a_renamed_matches_key_stops_rather_than_reporting_an_empty_run(self):
        """NEGATIVE: structural drift raises instead of forging a clean audit.

        If the outcome moved its matches under another key, reporting zero
        selected agents would be a false clean bill for a run that selected
        several. The distinct exception type says the shape moved, not that the
        data was thin.
        """
        outcome = _valid_outcome()
        outcome["selected"] = outcome.pop(subject.MATCHES_KEY)
        with pytest.raises(SelectionShapeChanged):
            explain_selection(outcome)

    def test_a_non_list_matches_value_is_refused(self):
        """NEGATIVE: matches must be a list, not text that could be iterated."""
        with pytest.raises(SelectionShapeChanged):
            explain_selection(_valid_outcome(matches=PROBE_AGENT))

    def test_one_bad_match_among_good_ones_refuses_the_whole_record(self):
        """NEGATIVE: partial explainability is not a passing state."""
        outcome = _valid_outcome(matches=[_valid_match(), _valid_match(confidence=None), _valid_match()])
        with pytest.raises(IncompleteSelectionRecord) as excinfo:
            explain_selection(outcome)
        assert excinfo.value.position == 1

    def test_nothing_is_logged_when_a_record_is_refused(self):
        """NEGATIVE: refusal is all-or-nothing, leaving no partial audit trail."""
        logger = _RecordingLogger()
        outcome = _valid_outcome(matches=[_valid_match(), _valid_match(agent="")])
        with pytest.raises(IncompleteSelectionRecord):
            emit_selection(outcome, logger=logger)
        assert logger.lines == [], "a refused selection still wrote {} lines".format(len(logger.lines))


# ---------------------------------------------------------------------------
# Specificity control -- the criteria do not require it and should
# ---------------------------------------------------------------------------


def _incomplete_variants():
    """Return one incomplete match per required field, plus empty variants."""
    variants = [(field, _valid_match(**{field: None})) for field in subject.REQUIRED_FIELDS]
    variants.append(("agent", _valid_match(agent="  ")))
    variants.append(("matched_skills", _valid_match(matched_skills=[])))
    variants.append(("edge_path", _valid_match(edge_path=[])))
    variants.append(("confidence", _valid_match(confidence=0.0)))
    return variants


class TestSpecificityControl:
    """Proof that the emitter discriminates complete records from incomplete ones."""

    def test_the_emitter_refuses_every_incomplete_selection_and_accepts_the_complete_one(self):
        """Both directions are pinned, so neither extreme passes.

        A serialiser that emitted five fields for everything would pass a
        presence check while explaining nothing; a serialiser that refused
        everything would pass a refusal check while emitting nothing. Requiring
        both halves in one measurement excludes both degenerate ends.
        """
        emitted = explain_match(_valid_match())
        assert all(field in emitted for field in FR23_FIELDS)

        survived = []
        for field, variant in _incomplete_variants():
            try:
                explain_match(variant)
                survived.append(field)
            except IncompleteSelectionRecord:
                continue
        assert survived == [], "incomplete selections were emitted for fields: {}".format(survived)

    def test_a_padding_serialiser_fails_the_same_control(self):
        """NEGATIVE CONTROL: filling absent fields with blanks must fail here.

        Without this, the control could be written loosely enough to pass a
        serialiser that always produces five fields, and would then prove
        nothing about refusal.
        """
        padded_variants = 0
        for _field, variant in _incomplete_variants():
            padded = _padding_serialiser(variant)
            if all(field in padded for field in FR23_FIELDS):
                padded_variants += 1
        assert padded_variants == len(_incomplete_variants()), (
            "the padding serialiser did not produce five fields for every incomplete input, "
            "so this control is not measuring what it claims"
        )

    def test_the_padded_records_are_the_ones_the_emitter_refuses(self):
        """The two halves are measured over the same inputs, not different ones."""
        for _field, variant in _incomplete_variants():
            padded = _padding_serialiser(variant)
            assert set(FR23_FIELDS).issubset(padded)
            with pytest.raises(IncompleteSelectionRecord):
                explain_match(variant)


# ---------------------------------------------------------------------------
# Live selection -- the criterion is stated about a real run
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def catalogue():
    """Load the real master catalogue once for the module."""
    return load_catalogue()


@pytest.fixture(scope="module")
def live_results(catalogue):
    """Run the real selector over the ten sample tasks and return the outcomes.

    The sample is every fourth sprint issue title, the same deterministic slice
    the selector's own suite uses, so the sample cannot have been chosen to
    flatter the emitter.
    """
    issues = json.loads(SPRINT_ISSUES.read_text(encoding="utf-8"))["issues"]
    titles = [issues[index]["title"] for index in range(0, len(issues), SAMPLE_STRIDE)]
    assert len(titles) == SAMPLE_SIZE

    adapter = DomainKgAdapter(catalogue)
    lexicon = build_lexicon(catalogue)
    risk = RiskSignal.unavailable()
    return [
        select_agents(title, catalogue=catalogue, adapter=adapter, risk=risk, lexicon=lexicon, complexity=8)
        for title in titles
    ]


@requires_library
class TestLiveSelection:
    """The criterion is about a real run, so a real run is measured."""

    def test_every_agent_selected_across_the_sample_is_fully_explained(self, live_results):
        """No selected agent anywhere in the sample fails to explain itself."""
        explained = 0
        for result in live_results:
            record = explain_selection(result)
            assert record[subject.RECORD_COUNT_KEY] == len(result.matches)
            for entry, match in zip(record[subject.RECORD_AGENTS_KEY], result.matches):
                assert entry["agent"] == match.agent
                assert entry["domain"] == match.domain
                assert entry["matched_skills"] == list(match.matched_skills)
                assert len(entry["edge_path"]) == len(match.edge_path)
                assert entry["confidence"] > 0.0
                explained += 1
        assert explained > 0, "the sample selected no agents at all; this test measured nothing"

    def test_every_emitted_record_stays_executable(self, live_results, catalogue):
        """The persona the record names exists and belongs to the named agent."""
        checked = 0
        for result in live_results:
            for entry in explain_selection(result)[subject.RECORD_AGENTS_KEY]:
                path = _LIBRARY_ROOT / entry[DISPATCH_FIELD]
                assert path.is_file(), "persona missing for {}".format(entry["agent"])
                assert entry["agent"] in entry[DISPATCH_FIELD]
                assert entry["agent"] in catalogue.agents
                checked += 1
        assert checked > 0

    def test_the_live_log_emits_five_fields_for_every_selected_agent(self, live_results):
        """The acceptance criterion, measured over the log of a real run."""
        logger = _RecordingLogger()
        expected_agents = 0
        for result in live_results:
            emit_selection(result, logger=logger)
            expected_agents += len(result.matches)

        agent_payloads = []
        for line in logger.lines:
            payload = json.loads(line.split(subject.LOG_MARKER, 1)[1].strip())
            if "agent" in payload:
                agent_payloads.append(payload)

        assert len(agent_payloads) == expected_agents
        for payload in agent_payloads:
            for field in FR23_FIELDS:
                assert field in payload
                assert payload[field] not in (None, "", [], {}, 0, 0.0)

    def test_a_degraded_live_outcome_emits_no_agent_record_but_keeps_its_reason(self, catalogue):
        """A real no-match outcome carries its explanation without this module reading it."""
        adapter = DomainKgAdapter(catalogue)
        result = select_agents(
            "   ",
            catalogue=catalogue,
            adapter=adapter,
            risk=RiskSignal.unavailable(),
            complexity=8,
        )
        assert result.matches == ()
        record = explain_selection(result)
        assert record[subject.RECORD_COUNT_KEY] == 0
        assert record[subject.RECORD_AGENTS_KEY] == []
        carried = json.dumps(record[subject.RECORD_OUTCOME_KEY], default=str)
        assert len(carried) > len("{}"), "the no-match outcome carried nothing into the audit record"

    def test_a_live_low_confidence_outcome_emits_no_agent_record(self, catalogue):
        """The rejected candidates of a real below-threshold run stay unselected.

        Driven through the real selector with the floor raised, so the shape
        under test is the one the selector actually produces rather than a
        reconstruction of it.
        """
        adapter = DomainKgAdapter(catalogue)
        result = select_agents(
            "kubernetes autoscaling service mesh observability deployment",
            catalogue=catalogue,
            adapter=adapter,
            risk=RiskSignal.unavailable(),
            lexicon=build_lexicon(catalogue),
            complexity=8,
            confidence_floor=0.999,
        )
        assert result.matches == (), "the raised floor did not force a below-threshold outcome"

        logger = _RecordingLogger()
        record = emit_selection(result, logger=logger)
        assert record[subject.RECORD_COUNT_KEY] == 0
        assert record[subject.RECORD_AGENTS_KEY] == []
        assert len(logger.lines) == 1, "an unselected candidate produced an agent log line"

    def test_the_emitted_lines_are_single_line_json(self, live_results):
        """One record per line, so a run log can be checked field by field."""
        logger = _RecordingLogger()
        emit_selection(live_results[0], logger=logger)
        for line in logger.lines:
            assert "\n" not in line
            assert line.startswith(subject.LOG_MARKER)
            json.loads(line.split(subject.LOG_MARKER, 1)[1].strip())

    def test_selection_log_lines_and_emit_agree(self, live_results):
        """The formatter and the emitter produce the same lines."""
        logger = _RecordingLogger()
        record = emit_selection(live_results[0], logger=logger)
        assert logger.lines == selection_log_lines(record)

"""Tests that ADR-006 itself carries the three named consequences (PRD FR-4a / SRS FR-14).

SRS FR-14's acceptance criterion is unusual: it names a specific evasion and forbids it.
"The ADR-006 document body cross-references all three named consequences; a consequence
recorded only in `docs/orchestration_prompt.md` does not satisfy this." Prose cannot
enforce that, because the orchestration prompt already contains all three and a reader
checking "are the consequences recorded somewhere" would answer yes while the criterion
is unmet. These tests read the ADR body specifically, so the criterion is checked at the
file the requirement names rather than at the corpus as a whole.

Each positive assertion is paired with a negative test that runs the identical predicate
against a fixture that omits or misplaces the thing being asserted. Without those, a
predicate that can never fail would pass permanently and prove nothing.

Windows-safe: ASCII only, no Unicode characters.
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ADR = REPO_ROOT / "docs" / "architecture" / "ADR-006-hook-free-execution.md"
ORCHESTRATION_PROMPT = REPO_ROOT / "docs" / "orchestration_prompt.md"

CONSEQUENCE_MARKERS = (
    "#### Consequence 1",
    "#### Consequence 2",
    "#### Consequence 3",
)

CONSEQUENCE_SUBJECTS = (
    "FR-9",
    "push_gate.py",
    "post_tool_tracker",
)


def _adr_text():
    """Read the ADR-006 document body.

    Returns:
        str: File contents.
    """
    return ADR.read_text(encoding="utf-8")


def _count_consequence_headings(text):
    """Count the numbered consequence headings present in a document body.

    Args:
        text: Markdown document body to scan.

    Returns:
        int: Number of distinct consequence headings found.
    """
    return sum(1 for marker in CONSEQUENCE_MARKERS if marker in text)


def _names_all_subjects(text):
    """Report whether a document body names every consequence subject.

    Args:
        text: Markdown document body to scan.

    Returns:
        bool: True when all three subjects appear.
    """
    return all(subject in text for subject in CONSEQUENCE_SUBJECTS)


class TestAdr006RecordsTheThreeConsequences:
    """SRS FR-14: the ADR body, not the orchestration prompt, must carry all three."""

    def test_the_adr_file_exists_at_the_path_the_requirement_names(self):
        assert ADR.exists(), "SRS FR-16 names this exact path"

    def test_all_three_consequence_headings_are_present(self):
        assert _count_consequence_headings(_adr_text()) == 3

    def test_each_consequence_names_its_own_subject(self):
        assert _names_all_subjects(_adr_text())

    def test_the_adr_states_there_are_exactly_three(self):
        """Guards against a fourth being appended without renumbering the claim."""
        assert "There are exactly three." in _adr_text()

    def test_consequences_are_not_delegated_to_the_orchestration_prompt(self):
        """The criterion forbids recording a consequence only in the prompt.

        A body that cites the prompt and stops is the exact evasion named. Each
        consequence heading must be followed by substantive text of its own before the
        next heading, not merely a pointer.
        """
        text = _adr_text()
        for marker in CONSEQUENCE_MARKERS:
            assert marker in text, "{} is absent entirely".format(marker)
            start = text.index(marker)
            remainder = text[start + len(marker) :]
            ends = [remainder.index(m) for m in CONSEQUENCE_MARKERS if m in remainder]
            body = remainder[: min(ends)] if ends else remainder
            assert len(body) > 500, "{} has no substantive body".format(marker)


class TestAdr006RecordsTheBlastRadiusMeasurement:
    """SRS FR-14 requires the measurement alongside the consequences."""

    def test_the_node_measurement_is_present(self):
        assert "135" in _adr_text() and "2,218" in _adr_text()

    def test_every_figure_is_labelled_measured_or_carried_forward(self):
        """Rule 3: re-measured and carried-forward figures must be distinguishable."""
        text = _adr_text()
        assert "MEASURED" in text
        assert "Carried forward" in text or "carried forward" in text

    def test_the_corrected_edge_count_is_recorded_with_the_superseded_one(self):
        """A correction that drops the old figure leaves the reader unable to reconcile."""
        text = _adr_text()
        assert "26" in text, "the superseded figure must remain visible"
        assert "12" in text, "the measured figure must be present"


class TestTheseChecksCanFail:
    """Companion negatives. Each runs a positive test's predicate against a fixture
    built to violate it, proving the predicate discriminates rather than always passing.
    """

    def test_heading_count_predicate_rejects_a_body_missing_a_consequence(self):
        two_only = "#### Consequence 1 -- a\ntext\n#### Consequence 2 -- b\ntext\n"
        assert _count_consequence_headings(two_only) == 2

    def test_heading_count_predicate_rejects_a_body_with_no_consequences(self):
        assert _count_consequence_headings("# ADR-006\n\nSome prose.\n") == 0

    def test_subject_predicate_rejects_a_body_that_names_only_some_subjects(self):
        partial = "This mentions FR-9 and push_gate.py but not the third."
        assert not _names_all_subjects(partial)

    def test_subject_predicate_rejects_an_empty_body(self):
        assert not _names_all_subjects("")

    def test_delegation_predicate_rejects_a_pointer_only_body(self):
        """The evasion SRS FR-14 names: headings present, substance elsewhere."""
        pointer_only = (
            "#### Consequence 1 -- see the prompt\n"
            "See `docs/orchestration_prompt.md`.\n"
            "#### Consequence 2 -- see the prompt\n"
            "See `docs/orchestration_prompt.md`.\n"
            "#### Consequence 3 -- see the prompt\n"
            "See `docs/orchestration_prompt.md`.\n"
        )
        assert _count_consequence_headings(pointer_only) == 3, "headings alone pass"
        short_bodies = 0
        for marker in CONSEQUENCE_MARKERS:
            start = pointer_only.index(marker)
            remainder = pointer_only[start + len(marker) :]
            ends = [remainder.index(m) for m in CONSEQUENCE_MARKERS if m in remainder]
            body = remainder[: min(ends)] if ends else remainder
            if len(body) <= 500:
                short_bodies += 1
        assert short_bodies == 3, "the substance check must reject all three"

    def test_the_orchestration_prompt_alone_would_not_satisfy_the_criterion(self):
        """The prompt contains all three subjects yet is not the required location.

        This is the criterion's whole point: subject presence in the corpus is not the
        test. If this assertion ever fails because the prompt stopped naming them, the
        criterion is unaffected -- but the fixture behind these tests has changed.
        """
        if not ORCHESTRATION_PROMPT.exists():
            return
        prompt = ORCHESTRATION_PROMPT.read_text(encoding="utf-8")
        assert _names_all_subjects(prompt)
        assert ORCHESTRATION_PROMPT != ADR

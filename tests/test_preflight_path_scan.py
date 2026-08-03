"""Tests for the Level 0 drive-path scanner in preflight_guard/path_scan.py.

The scanner replaced a raw-text regex that corrupted source. That regex matched
an escape sequence as a drive path, and the auto-fix paired with it rewrote the
backslash, which damaged the string AND removed the match -- so the check
reported success because of the damage it had done.

The regression test for that exact input is the reason this file exists, and it
is paired throughout with sensitivity tests: a scanner that reports False for
everything would satisfy the false-positive tests alone while removing the check
entirely.
"""

import pytest

from langgraph_engine.preflight_guard.path_scan import has_drive_path

ESCAPE_ONLY_SOURCE = 'x = "with open(p) as f:\\n    pass\\n"\n'
REAL_PATH_SOURCE = 'BASE = "C:\\\\Users\\\\techd\\\\thing"\n'


class TestScannerRejectsEscapeSequences:
    """No Python escape sequence may be read as a path separator."""

    def test_the_exact_input_that_was_corrupted_is_not_flagged(self):
        """Regression: 'as f:' plus a newline escape was read as drive f."""
        assert has_drive_path(ESCAPE_ONLY_SOURCE) is False

    @pytest.mark.parametrize("escape", ["n", "t", "r", "0", "b", "f", "v", "a"])
    def test_no_single_letter_name_before_a_colon_escape_is_a_drive(self, escape):
        """The pattern that broke needs only a space, a letter and a colon."""
        source = 'x = "as f:\\%s    tail"\n' % escape
        assert has_drive_path(source) is False

    def test_a_repository_relative_forward_slash_path_is_not_flagged(self):
        assert has_drive_path('P = "tests/nfr1/probe.py"\n') is False


class TestScannerStillFindsRealPaths:
    """The check must keep failing on what it exists to catch."""

    def test_a_hardcoded_drive_path_in_a_string_is_flagged(self):
        assert has_drive_path(REAL_PATH_SOURCE) is True

    def test_a_drive_path_in_a_comment_is_flagged(self):
        assert has_drive_path("# see C:\\Users\\techd for details\n") is True

    def test_a_raw_string_drive_path_is_flagged(self):
        assert has_drive_path('P = r"C:\\Users\\techd\\x"\n') is True

    def test_an_escaped_drive_path_is_flagged_where_the_raw_scan_missed_it(self):
        """The escaped form is the one the superseded raw-text scan could not see.

        In source, an escaped literal reads ``"C:\\\\Users"``. A raw-text pattern
        needs a word character straight after the drive backslash and finds a
        second backslash instead, so it matched only raw-string literals. Reading
        the VALUE makes both forms identical and both detectable.
        """
        assert has_drive_path(REAL_PATH_SOURCE) is True


class TestScannerDegradesSafely:
    """A file that does not parse still gets checked, by the raw scan."""

    def test_unparseable_source_with_a_real_path_is_still_flagged(self):
        source = 'def broken(:\nP = r"C:\\Users\\techd\\x"\n'
        assert has_drive_path(source) is True

    def test_unparseable_source_without_a_path_is_not_flagged(self):
        assert has_drive_path("def broken(:\n") is False


class TestTheCheckIsNotVacuous:
    """A scanner that always returns False would pass every test above."""

    def test_the_two_representative_inputs_disagree(self):
        """Sensitivity and specificity are asserted against each other.

        If a change makes the scanner constant in either direction, this fails
        even when every individual case above is read in isolation.
        """
        assert has_drive_path(REAL_PATH_SOURCE) != has_drive_path(ESCAPE_ONLY_SOURCE)

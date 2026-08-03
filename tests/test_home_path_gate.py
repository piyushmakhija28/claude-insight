"""Tests for the home-directory path classifier in scripts/verify_home_paths.py.

The gate's whole value is the CODE / DOCSTRING / COMMENT partition, because two
prior measurements of the same surface disagreed about that split by roughly 7x.
A classifier that silently called everything one class would report a clean
codebase just as convincingly as a correct one, so these tests pin the partition
from both directions: a docstring occurrence must never be reported CODE, and a
genuine code occurrence must never be reported DOCSTRING. Testing only one
direction would pass for a classifier that had collapsed to a constant.

The fixtures assemble the searched-for text at run time rather than spelling it,
because this module sits under a scanned tree in the same way the Level 0
scanner's tests do, and a literal here would make the test file a finding in the
measurement it exists to verify.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import verify_home_paths as gate  # noqa: E402

HOME = "~" + "/" + "." + "claude"
DRIVE = "C" + ":" + chr(92) + "Users" + chr(92) + "someone"


def classify(source: str) -> list[gate.Occurrence]:
    """Run the classifier over a source string.

    Args:
        source: Python source text.

    Returns:
        list: Occurrences found.
    """
    return gate.analyse_source(source, "fixture.py")


def classes_of(source: str) -> list[str]:
    """Return just the classifications produced for a source string.

    Args:
        source: Python source text.

    Returns:
        list: Classification labels in report order.
    """
    return [item.classification for item in classify(source)]


class TestDetection:
    """The pattern must fire on real references and stay silent otherwise."""

    def test_finds_nothing_in_a_clean_module(self):
        assert classify("import os\n\n\ndef f():\n    return os.getcwd()\n") == []

    def test_finds_a_reference_in_an_assignment(self):
        assert len(classify('P = "' + HOME + '/logs"\n')) == 1

    def test_a_bare_tilde_is_not_a_reference(self):
        assert classify('P = "~/documents/notes.txt"\n') == []

    def test_a_bare_claude_directory_name_is_not_a_reference(self):
        assert classify('P = ".claude"\n') == []

    def test_counts_every_occurrence_in_one_literal(self):
        source = 'P = "' + HOME + "/logs and " + HOME + '/skills"\n'
        assert len(classify(source)) == 2


class TestCodeClassification:
    """Each shape the acceptance criterion names must classify as CODE."""

    def test_parameter_default_is_code(self):
        source = 'def f(base="' + HOME + '/logs"):\n    return base\n'
        found = classify(source)
        assert [item.classification for item in found] == [gate.CLASS_CODE]
        assert found[0].node_type == "arguments.defaults"

    def test_call_keyword_is_code(self):
        source = 'parser.add_argument("--x", help="' + HOME + '/logs")\n'
        found = classify(source)
        assert [item.classification for item in found] == [gate.CLASS_CODE]
        assert found[0].node_type == "Call.keyword"

    def test_assignment_right_hand_side_is_code(self):
        source = 'BASE = "' + HOME + '/logs"\n'
        found = classify(source)
        assert [item.classification for item in found] == [gate.CLASS_CODE]
        assert found[0].node_type == "Assign.value"

    def test_call_positional_argument_is_code(self):
        source = 'print("' + HOME + '/logs")\n'
        assert classes_of(source) == [gate.CLASS_CODE]

    def test_f_string_part_is_code(self):
        source = 'name = "x"\nP = f"' + HOME + '/skills/{name}"\n'
        assert classes_of(source) == [gate.CLASS_CODE]

    def test_list_element_is_code(self):
        source = 'LOCATIONS = ["' + HOME + '/policies"]\n'
        assert classes_of(source) == [gate.CLASS_CODE]


class TestDocstringClassification:
    """Docstrings are documentation and must never be reported as CODE."""

    def test_module_docstring_is_docstring(self):
        source = '"""Paths live under ' + HOME + '/logs."""\n'
        found = classify(source)
        assert [item.classification for item in found] == [gate.CLASS_DOCSTRING]
        assert found[0].node_type == "Module.docstring"

    def test_function_docstring_is_docstring(self):
        source = 'def f():\n    """Reads ' + HOME + '/logs."""\n    return 1\n'
        found = classify(source)
        assert [item.classification for item in found] == [gate.CLASS_DOCSTRING]
        assert found[0].node_type == "FunctionDef.docstring"

    def test_class_docstring_is_docstring(self):
        source = 'class C:\n    """Stores under ' + HOME + '/memory."""\n\n    x = 1\n'
        found = classify(source)
        assert [item.classification for item in found] == [gate.CLASS_DOCSTRING]
        assert found[0].node_type == "ClassDef.docstring"

    def test_async_function_docstring_is_docstring(self):
        source = 'async def f():\n    """Reads ' + HOME + '/logs."""\n    return 1\n'
        assert classes_of(source) == [gate.CLASS_DOCSTRING]

    def test_a_constructor_call_inside_a_docstring_example_is_not_code(self):
        source = (
            'class C:\n    """Doc.\n\n    Example::\n\n        S(Path("' + HOME + '/memory/state.json"))\n    """\n'
        )
        assert classes_of(source) == [gate.CLASS_DOCSTRING]

    def test_a_string_after_the_first_statement_is_not_a_docstring(self):
        source = 'x = 1\n"' + HOME + '/logs"\n'
        found = classify(source)
        assert [item.classification for item in found] == [gate.CLASS_CODE]
        assert found[0].node_type == "Expr.bare-string"


class TestCommentClassification:
    """Comments never reach the AST, so only the token pass can see them."""

    def test_full_line_comment_is_comment(self):
        assert classes_of("# see " + HOME + "/logs\n") == [gate.CLASS_COMMENT]

    def test_trailing_comment_is_comment(self):
        assert classes_of("x = 1  # see " + HOME + "/logs\n") == [gate.CLASS_COMMENT]

    def test_comment_and_code_on_the_same_line_are_both_found(self):
        source = 'BASE = "' + HOME + '/logs"  # default ' + HOME + "/logs\n"
        assert sorted(classes_of(source)) == [gate.CLASS_CODE, gate.CLASS_COMMENT]


class TestSpecificityBothDirections:
    """A collapsed classifier must fail, whichever class it collapsed to."""

    def test_docstring_and_code_in_one_module_are_told_apart(self):
        source = '"""Doc mentions ' + HOME + '/logs."""\n\nBASE = "' + HOME + '/logs"\n'
        found = classify(source)
        by_class = {item.classification for item in found}
        assert by_class == {gate.CLASS_DOCSTRING, gate.CLASS_CODE}

    def test_no_docstring_occurrence_is_ever_reported_as_code(self):
        source = (
            '"""Module doc ' + HOME + '/a."""\n\n\n'
            'class C:\n    """Class doc ' + HOME + '/b."""\n\n'
            '    def m(self):\n        """Method doc ' + HOME + '/c."""\n        return 1\n'
        )
        assert classes_of(source) == [gate.CLASS_DOCSTRING] * 3

    def test_no_code_occurrence_is_ever_reported_as_docstring(self):
        source = 'A = "' + HOME + '/a"\n' 'def f(b="' + HOME + '/b"):\n' '    return g(key="' + HOME + '/c")\n'
        assert classes_of(source) == [gate.CLASS_CODE] * 3

    def test_all_three_classes_are_produced_from_one_module(self):
        source = '"""Doc ' + HOME + '/a."""\n\n# note ' + HOME + '/b\nBASE = "' + HOME + '/c"\n'
        assert sorted(classes_of(source)) == [
            gate.CLASS_CODE,
            gate.CLASS_COMMENT,
            gate.CLASS_DOCSTRING,
        ]


class TestValueNotSourceText:
    """Reading values is what keeps an escape from being read as a path."""

    def test_an_escape_sequence_is_not_a_path_separator(self):
        source = 'P = "with open(p) as f:" + chr(92) + "n    pass"\n'
        assert gate.find_absolute_path_literals(source, "fixture.py") == []

    def test_a_genuine_drive_path_is_still_found(self):
        source = 'P = r"' + DRIVE + '"\n'
        found = gate.find_absolute_path_literals(source, "fixture.py")
        assert [item.classification for item in found] == [gate.CLASS_CODE]

    def test_a_regex_character_class_is_not_a_drive_path(self):
        source = 'import re\nM = re.search(r"((?:[A-Za-z]:)?[/' + chr(92) * 2 + r"][^" + r"\s:" + '\\"' + "']+)\", t)\n"
        assert gate.find_absolute_path_literals(source, "fixture.py") == []

    def test_a_url_is_not_an_absolute_path(self):
        source = 'U = "https://example.com/home/someone/x"\n'
        assert gate.find_absolute_path_literals(source, "fixture.py") == []


class TestEnforcementScope:
    """Only CODE outside the canonical resolver counts toward the zero condition."""

    def test_a_code_occurrence_is_enforced(self):
        item = gate.Occurrence("langgraph_engine/x.py", 1, "Assign.value", gate.CLASS_CODE, HOME)
        assert item.is_enforced() is True

    def test_the_canonical_resolver_is_excluded_by_name(self):
        item = gate.Occurrence("src/utils/path_resolver.py", 1, "Assign.value", gate.CLASS_CODE, HOME)
        assert item.is_enforced() is False

    def test_a_docstring_occurrence_is_never_enforced(self):
        item = gate.Occurrence("langgraph_engine/x.py", 1, "Module.docstring", gate.CLASS_DOCSTRING, HOME)
        assert item.is_enforced() is False

    def test_record_format_matches_the_acceptance_criterion(self):
        item = gate.Occurrence("a/b.py", 7, "Call.keyword", gate.CLASS_CODE, HOME)
        assert item.record() == "a/b.py:7:Call.keyword:CODE"


class TestGateCanFail:
    """A check that cannot fail proves nothing about the code it passes on."""

    def test_gate_fails_on_a_tree_containing_a_code_occurrence(self, tmp_path):
        package = tmp_path / "langgraph_engine"
        package.mkdir()
        (package / "bad.py").write_text('BASE = "' + HOME + '/logs"\n', encoding="utf-8")
        assert gate.main(["--root", str(tmp_path)]) == 1

    def test_gate_passes_on_a_tree_with_only_documentation_occurrences(self, tmp_path):
        package = tmp_path / "langgraph_engine"
        package.mkdir()
        (package / "ok.py").write_text(
            '"""Doc ' + HOME + '/logs."""\n\n# note ' + HOME + "/logs\n",
            encoding="utf-8",
        )
        assert gate.main(["--root", str(tmp_path)]) == 0

    def test_gate_fails_on_an_absolute_path_literal_in_code(self, tmp_path):
        package = tmp_path / "scripts"
        package.mkdir()
        (package / "bad.py").write_text('W = r"' + DRIVE + '"\n', encoding="utf-8")
        assert gate.main(["--root", str(tmp_path)]) == 1

    def test_gate_fails_on_an_unparsable_file(self, tmp_path):
        package = tmp_path / "hooks"
        package.mkdir()
        (package / "broken.py").write_text("def f(:\n", encoding="utf-8")
        assert gate.main(["--root", str(tmp_path)]) == 1

    def test_gate_passes_on_an_empty_tree(self, tmp_path):
        assert gate.main(["--root", str(tmp_path)]) == 0


class TestMutationDetection:
    """Replacing the classifier with a degenerate one must be caught."""

    @staticmethod
    def _all_docstring(source: str) -> list[str]:
        """Classify every occurrence as DOCSTRING, ignoring position.

        Args:
            source: Python source text.

        Returns:
            list: One DOCSTRING label per occurrence found by the pattern.
        """
        return [gate.CLASS_DOCSTRING] * len(classify(source))

    @staticmethod
    def _all_code(source: str) -> list[str]:
        """Classify every occurrence as CODE, ignoring position.

        Args:
            source: Python source text.

        Returns:
            list: One CODE label per occurrence found by the pattern.
        """
        return [gate.CLASS_CODE] * len(classify(source))

    def test_an_all_docstring_classifier_disagrees_with_the_real_one(self):
        source = 'BASE = "' + HOME + '/logs"\n'
        assert self._all_docstring(source) != classes_of(source)

    def test_an_all_code_classifier_disagrees_with_the_real_one(self):
        source = '"""Doc ' + HOME + '/logs."""\n'
        assert self._all_code(source) != classes_of(source)

    def test_neither_degenerate_classifier_reproduces_a_mixed_module(self):
        source = '"""Doc ' + HOME + '/a."""\n\nBASE = "' + HOME + '/b"\n'
        real = classes_of(source)
        assert self._all_docstring(source) != real
        assert self._all_code(source) != real


class TestDocstringRuleAgreesWithLevel0Scanner:
    """The restated docstring rule must not drift from the Level 0 original.

    The gate does not import ``path_scan`` because doing so pulls in the whole
    orchestration engine. That makes drift possible, so it is checked directly
    against every file in the live scope rather than assumed.
    """

    def test_docstring_node_sets_match_across_the_live_scope(self):
        preflight = pytest.importorskip("langgraph_engine.preflight_guard.path_scan")
        checked = 0
        for path in gate.iter_python_files(REPO_ROOT, gate.DEFAULT_SCOPE):
            try:
                source = path.read_text(encoding="utf-8")
                tree = ast.parse(source)
            except (OSError, UnicodeDecodeError, SyntaxError):
                continue
            assert gate.docstring_node_ids(tree) == preflight._docstring_nodes(tree), path
            checked += 1
        assert checked > 100


class TestRepositoryIsClean:
    """The live repository must satisfy the terminal condition."""

    def test_no_enforced_code_occurrence_remains(self):
        files = list(gate.iter_python_files(REPO_ROOT, gate.DEFAULT_SCOPE))
        home, absolute, unreadable = gate.scan_paths(files, REPO_ROOT)
        assert [item.record() for item in home if item.is_enforced()] == []
        assert [item.record() for item in absolute if item.is_enforced()] == []
        assert unreadable == []

    def test_the_measured_total_is_reported_not_asserted(self):
        files = list(gate.iter_python_files(REPO_ROOT, gate.DEFAULT_SCOPE))
        home, _, _ = gate.scan_paths(files, REPO_ROOT)
        counts = gate.summarise(home)
        assert sum(counts.values()) == len(home)
        assert counts[gate.CLASS_DOCSTRING] + counts[gate.CLASS_COMMENT] == len(home)

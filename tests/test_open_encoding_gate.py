"""Tests for the V2-019 / SRS FR-30 encoding gate in ``scripts/verify_open_encoding.py``.

The gate asserts that no text-mode file open in this repository relies on the
platform default codepage. On Windows that default is cp1252 and on the CI
runners it is UTF-8, so an unencoded open makes the same file read differently on
two machines, or raise ``UnicodeDecodeError`` on content the program itself wrote.

Three classes of test are present, and the third is the one that gives the first
two their meaning.

SENSITIVITY (the gate can fail). A check that cannot fail is indistinguishable
from a check that passes. Every opener form the rule governs -- the mode-less
call, each explicit text mode, ``io.open``, ``codecs.open``, an aliased import,
and a genuine ``Path(...).open()`` -- is planted unencoded and asserted to be
flagged. The mode-less form is called out separately because the baseline this
task inherited was produced by a regex that required an explicit mode string and
therefore missed seven such calls, undercounting by more than a third.

SPECIFICITY (the gate flags only what it should). An exemption list wide enough
to make the gate pass by excusing the defects is the failure mode that matters
here, so each exemption is asserted to be load-bearing rather than declared. The
binary-mode exemption is asserted to be mode-precise rather than file-wide, and
the ``tarfile``/``urllib`` exemptions are asserted not to generalise into a blanket
"any dotted call named open" pass. The docstring and comment cases exist because
the regex this AST pass replaces fired on both.

MUTATION (the assertions are load-bearing). A permissive stand-in classifier is
substituted for the real one and the repository assertion is required to stop
passing. Without this, a gate that silently classified everything as exempt would
report a clean tree and every other test here would still be green.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
GATE_PATH = REPO_ROOT / "scripts" / "verify_open_encoding.py"


def _load_gate():
    """Import the gate module from its stored path.

    The module is loaded from ``scripts/`` rather than copied or re-implemented
    here so the tests exercise the same file CI executes. A second copy of the
    classifier would drift from the one the gate actually runs.

    Returns:
        module: The imported ``verify_open_encoding`` module.
    """
    spec = importlib.util.spec_from_file_location("verify_open_encoding_under_test", GATE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


gate = _load_gate()


def verdicts(source: str) -> list[str]:
    """Return the verdict for each opener call found in a source snippet.

    Args:
        source: Python source text to analyse.

    Returns:
        list: Verdict labels in traversal order.
    """
    return [finding.verdict for finding in gate.analyse_source(source, "snippet.py")]


class TestGateIsSensitive:
    """Every governed opener form must be flagged when it lacks an encoding."""

    def test_mode_less_open_is_flagged(self):
        """The form the inherited regex baseline missed entirely."""
        assert verdicts("with open(p) as f:\n    pass\n") == ["VIOLATION"]

    @pytest.mark.parametrize("mode", ["r", "w", "a", "x", "r+", "w+", "a+", "rt", "wt"])
    def test_every_explicit_text_mode_is_flagged(self, mode):
        assert verdicts('open(p, "{}")\n'.format(mode)) == ["VIOLATION"]

    def test_keyword_mode_is_flagged(self):
        assert verdicts('open(p, mode="w")\n') == ["VIOLATION"]

    def test_io_open_is_flagged(self):
        assert verdicts("import io\nio.open(p)\n") == ["VIOLATION"]

    def test_codecs_open_is_flagged(self):
        assert verdicts("import codecs\ncodecs.open(p)\n") == ["VIOLATION"]

    def test_aliased_import_of_open_is_flagged(self):
        """A regex over the token ``open(`` never sees this call site."""
        assert verdicts("from io import open as _open\n_open(p)\n") == ["VIOLATION"]

    def test_pathlib_open_is_flagged(self):
        """The clause the precision filter must not have removed."""
        source = "from pathlib import Path\ntarget = Path('x')\ntarget.open()\n"
        assert verdicts(source) == ["VIOLATION"]

    def test_pathlib_open_on_a_direct_constructor_is_flagged(self):
        assert verdicts("from pathlib import Path\nPath('x').open('w')\n") == ["VIOLATION"]

    def test_pathlib_open_through_a_join_is_flagged(self):
        source = "from pathlib import Path\nroot = Path('x')\n(root / 'y').open()\n"
        assert verdicts(source) == ["VIOLATION"]

    def test_annotated_path_parameter_is_flagged(self):
        source = "from pathlib import Path\ndef read(target: Path):\n    return target.open()\n"
        assert verdicts(source) == ["VIOLATION"]

    def test_call_split_across_lines_is_flagged(self):
        """A line-oriented regex cannot see the mode argument from the open line."""
        source = "open(\n    p,\n    'w',\n)\n"
        assert verdicts(source) == ["VIOLATION"]

    def test_multiple_violations_in_one_file_are_all_reported(self):
        source = "open(a)\nopen(b, 'w')\nopen(c, 'a')\n"
        assert verdicts(source) == ["VIOLATION"] * 3


class TestGateIsSpecific:
    """The gate must not flag constructs that cannot take an encoding argument."""

    @pytest.mark.parametrize("mode", ["rb", "wb", "ab", "xb", "r+b", "rb+", "wb+", "ab+"])
    def test_binary_modes_are_exempt(self, mode):
        """Passing encoding= alongside a binary mode raises ValueError at runtime."""
        assert verdicts('open(p, "{}")\n'.format(mode)) == ["EXEMPT"]

    def test_binary_exemption_is_mode_precise_not_file_wide(self):
        """A binary open in the same file must not excuse a text open beside it."""
        assert verdicts("open(a, 'rb')\nopen(b, 'r')\n") == ["EXEMPT", "VIOLATION"]

    def test_tarfile_open_is_exempt(self):
        assert verdicts("import tarfile\ntarfile.open(p)\n") == ["EXEMPT"]

    def test_bare_urlopen_is_not_recognised_as_an_opener(self):
        """Excluded by name, before the exemption list is ever consulted."""
        assert verdicts("from urllib.request import urlopen\nurlopen(u)\n") == []

    def test_urllib_request_urlopen_attribute_form_is_exempt(self):
        assert verdicts("import urllib.request\nurllib.request.urlopen(u)\n") == ["EXEMPT"]

    def test_os_fdopen_is_exempt(self):
        assert verdicts("import os\nos.fdopen(fd)\n") == ["EXEMPT"]

    def test_gzip_open_is_exempt(self):
        assert verdicts("import gzip\ngzip.open(p)\n") == ["EXEMPT"]

    def test_tarfile_exemption_does_not_generalise_to_any_dotted_open(self):
        """The exemption is keyed to named modules, not to attribute-call shape.

        A blanket "any ``X.open()`` is exempt" rule would pass this repository just
        as well while silently excusing every pathlib open in it.
        """
        source = "from pathlib import Path\ntarget = Path('x')\ntarget.open()\n"
        assert verdicts(source) == ["VIOLATION"]

    def test_domain_method_named_open_is_not_flagged(self):
        """Measured precision defect: an earlier draft flagged all eight of these.

        ``guard.open()`` in ``tests/nfr1`` opens no file. Treating every attribute
        call named ``open`` as a file open gave that rule precision 0.0 against
        this repository, which is why the pathlib provenance filter exists.
        """
        assert verdicts("guard = TurnBoundaryGuard(p)\nguard.open()\n") == []

    def test_self_open_is_not_flagged(self):
        assert verdicts("class S:\n    def go(self):\n        self.open()\n") == []

    def test_open_inside_a_docstring_is_not_flagged(self):
        """The literal text a regex over ``open(`` cannot distinguish from code."""
        assert verdicts('"""Call open(p) to read it."""\n') == []

    def test_open_inside_a_comment_is_not_flagged(self):
        assert verdicts("# open(p, 'w')\nx = 1\n") == []

    def test_open_inside_a_string_literal_is_not_flagged(self):
        assert verdicts('msg = "use open(p) here"\n') == []


class TestGateAcceptsCompliantCode:
    """Correctly encoded calls must be recorded as compliant, not flagged."""

    def test_keyword_encoding_is_accepted(self):
        assert verdicts('open(p, "w", encoding="utf-8")\n') == ["OK"]

    def test_mode_less_call_with_encoding_is_accepted(self):
        assert verdicts('open(p, encoding="utf-8")\n') == ["OK"]

    def test_positional_encoding_is_accepted(self):
        assert verdicts('open(p, "w", -1, "utf-8")\n') == ["OK"]

    def test_pathlib_positional_encoding_is_accepted(self):
        source = "from pathlib import Path\nt = Path('x')\nt.open('w', -1, 'utf-8')\n"
        assert verdicts(source) == ["OK"]


class TestGateRefusesToGuess:
    """Calls the parser cannot decide must fail, not pass silently."""

    def test_dynamic_mode_without_encoding_is_undecidable(self):
        assert verdicts("open(p, mode_var)\n") == ["UNDECIDABLE"]

    def test_star_kwargs_without_encoding_is_undecidable(self):
        assert verdicts("open(p, **opts)\n") == ["UNDECIDABLE"]

    def test_dynamic_mode_with_explicit_encoding_is_accepted(self):
        """The rule is satisfied once an encoding is present, whatever the mode."""
        assert verdicts('open(p, mode_var, encoding="utf-8")\n') == ["OK"]

    def test_undecidable_calls_fail_the_gate(self, tmp_path):
        (tmp_path / "m.py").write_text("open(p, mode_var)\n", encoding="utf-8")
        assert gate.main(["--root", str(tmp_path)]) == 1


class TestGateExitStatus:
    """The command-line contract CI depends on."""

    def test_violation_exits_nonzero(self, tmp_path):
        (tmp_path / "bad.py").write_text("open(p, 'w')\n", encoding="utf-8")
        assert gate.main(["--root", str(tmp_path)]) == 1

    def test_clean_tree_exits_zero(self, tmp_path):
        (tmp_path / "good.py").write_text('open(p, "w", encoding="utf-8")\n', encoding="utf-8")
        assert gate.main(["--root", str(tmp_path)]) == 0

    def test_unparsable_file_fails_rather_than_being_skipped(self, tmp_path):
        """A file the gate cannot read is not a file the gate has cleared."""
        (tmp_path / "broken.py").write_text("def (:\n", encoding="utf-8")
        assert gate.main(["--root", str(tmp_path)]) == 1

    def test_skipped_directories_are_not_scanned(self, tmp_path):
        vendored = tmp_path / ".venv" / "lib"
        vendored.mkdir(parents=True)
        (vendored / "dep.py").write_text("open(p, 'w')\n", encoding="utf-8")
        assert gate.main(["--root", str(tmp_path)]) == 0


class TestRepositoryIsClean:
    """The acceptance criterion itself, asserted against the real tree."""

    def test_no_unencoded_text_mode_open_remains(self):
        findings, unreadable = gate.scan_paths(gate.iter_python_files(REPO_ROOT), REPO_ROOT)
        violations = gate.select(findings, "VIOLATION")
        assert violations == [], "unencoded text-mode open() at: " + ", ".join(v.location() for v in violations)
        assert unreadable == []

    def test_no_undecidable_open_remains(self):
        findings, _ = gate.scan_paths(gate.iter_python_files(REPO_ROOT), REPO_ROOT)
        undecidable = gate.select(findings, "UNDECIDABLE")
        assert undecidable == [], "undecidable open() at: " + ", ".join(u.location() for u in undecidable)

    def test_the_scan_actually_reached_call_sites(self):
        """A scan that reached nothing would satisfy every assertion above."""
        findings, _ = gate.scan_paths(gate.iter_python_files(REPO_ROOT), REPO_ROOT)
        assert len(gate.select(findings, "OK")) > 50
        assert len(gate.select(findings, "EXEMPT")) > 10

    def test_the_remediated_sites_are_present_and_compliant(self):
        """The 19 sites this change fixed are still reached and still pass.

        Guards against a later edit deleting a call site and leaving the zero-
        violation assertion trivially true.
        """
        remediated = {
            "langgraph_engine/engine_logging/setup.py": 1,
            "langgraph_engine/sdlc_pipeline/documentation_generator.py": 4,
            "langgraph_engine/sdlc_pipeline/architecture/01-task-breakdown/task_auto_analyzer.py": 1,
            "scripts/agents/computer-use-agent.py": 1,
            "scripts/agents/dummy-project-seeder.py": 5,
            "scripts/agents/verify-computer-use-prerequisites.py": 3,
            "src/services/claude_integration.py": 4,
        }
        assert sum(remediated.values()) == 19
        findings, _ = gate.scan_paths(gate.iter_python_files(REPO_ROOT), REPO_ROOT)
        compliant = gate.select(findings, "OK")
        for relative_path, expected in remediated.items():
            actual = len([f for f in compliant if f.path == relative_path])
            assert actual >= expected, "{} has {} compliant opens, expected at least {}".format(
                relative_path, actual, expected
            )


class TestMutationResistance:
    """A permissive stand-in classifier must break the repository assertion."""

    def test_blanket_exemption_stand_in_breaks_the_clean_tree_assertion(self, monkeypatch, tmp_path):
        """Replacing the classifier with 'exempt everything' must stop the gate failing.

        If this passes with the stand-in installed, the gate reports clean without
        judging anything, and every assertion in this file is decorative.
        """
        (tmp_path / "bad.py").write_text("open(p, 'w')\n", encoding="utf-8")
        assert gate.main(["--root", str(tmp_path)]) == 1

        monkeypatch.setattr(gate, "_classify_callee", lambda *_args, **_kwargs: None)
        assert gate.main(["--root", str(tmp_path)]) == 0

    def test_mode_less_blindness_stand_in_breaks_the_gate(self, monkeypatch, tmp_path):
        """A stand-in reproducing the inherited regex's blind spot must be caught.

        The original baseline required an explicit mode string. A classifier with
        that blind spot passes a mode-less call, which is exactly the undercount
        this task was given as already-corrected.
        """
        (tmp_path / "bad.py").write_text("open(p)\n", encoding="utf-8")
        assert gate.main(["--root", str(tmp_path)]) == 1

        original = gate._mode_expression

        def mode_blind(call, shape):
            """Return a benign binary mode when the real call omits mode entirely.

            Args:
                call: Call node under inspection.
                shape: Argument shape passed through to the real resolver.

            Returns:
                ast.expr: The real mode expression, or a fabricated binary literal.
            """
            resolved = original(call, shape)
            if resolved is None:
                import ast as _ast

                return _ast.Constant(value="rb")
            return resolved

        monkeypatch.setattr(gate, "_mode_expression", mode_blind)
        assert gate.main(["--root", str(tmp_path)]) == 0

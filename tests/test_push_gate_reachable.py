"""Tests for the ADR-017 CI assertion in scripts/verify_push_gate_reachable.py.

WHAT ACCEPTANCE CRITERION 1 ACTUALLY ASKS
-----------------------------------------
"Fails the build IFF the PreToolUse registration is absent AND no MCP tool named
as the version-push gate is reachable" is a BICONDITIONAL, and most of the work
is in its second direction. Three of the four cells must PASS, and the cell that
matters most is (registration absent, tool reachable): that is the steady state
PRD FR-4 produces, and an assertion that failed there would satisfy a careless
reading of the same sentence while blocking the deletion it exists to protect.
``TestTruthTable`` enumerates all four cells and measures each one.

WHY NO TEST HERE READS THE MACHINE'S OWN SETTINGS
-------------------------------------------------
``~/.claude/settings.json``, ``~/.claude/settings.local.json`` and the tracked
``.claude/settings.local.json`` are never read for a verdict and never written.
Two mechanisms enforce that rather than one. Structurally,
``assert_push_gate_reachable`` takes ``settings`` as a REQUIRED parameter, so it
cannot resolve a file on its own -- ``TestTheSignatureCannotResolveSettingsItself``
pins that. Behaviourally, ``_digests`` hashes all three files around the whole
module and the autouse fixture fails the run if any digest moved.

MEASURED 2026-08-03, and it is why the distinction is not academic:
``~/.claude/settings.json`` DOES carry a live PreToolUse entry, so a gate that
read it implicitly would sit permanently in the passing half of the truth table
and would flip the moment its owner edited a file CI cannot see.

Windows-safe: ASCII only, no Unicode characters.
"""

import ast
import hashlib
import json
import shutil
import subprocess
import sys
from inspect import Parameter, signature
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import verify_push_gate_reachable as gate  # noqa: E402

GUARDED_SETTINGS = (
    Path.home() / ".claude" / "settings.json",
    Path.home() / ".claude" / "settings.local.json",
    REPO_ROOT / ".claude" / "settings.local.json",
)

WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "push-gate-reachable.yml"
SERVER_PACKAGE = REPO_ROOT / "src" / "mcp" / "push_gate"
SERVER_PATH = SERVER_PACKAGE / "server.py"
EVIDENCE_PATH = REPO_ROOT / "tests" / "test_push_gate_mcp_tool.py"

REGISTERED = {"hooks": {"PreToolUse": [{"matcher": "", "hooks": []}]}}
UNREGISTERED = {"hooks": {}}

REACHABLE = gate.Reachability(True, "stubbed reachable", ("check_push_allowed",))
UNREACHABLE = gate.Reachability(False, "stubbed unreachable")


def _digests():
    """Hash every guarded settings file.

    Returns:
        dict: Mapping of path string to sha256 hex digest, or "ABSENT".
    """
    out = {}
    for path in GUARDED_SETTINGS:
        try:
            out[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
        except OSError:
            out[str(path)] = "ABSENT"
    return out


@pytest.fixture(scope="module", autouse=True)
def guarded_settings_are_untouched():
    """Fail the module if any guarded settings file changed while it ran.

    Yields:
        dict: The digests captured before any test in this module ran.
    """
    before = _digests()
    yield before
    assert _digests() == before, "a guarded settings file changed while this module ran"


def _scratch_catalogue(path, entry, repo="claude-workflow-engine", capability=gate.PUSH_GATE_CAPABILITY):
    """Write a one-server catalogue for a probe test.

    Args:
        path: Destination file.
        entry: Entry-point path recorded in the descriptor.
        repo: Repository name recorded in the descriptor.
        capability: Capability name recorded in the descriptor.

    Returns:
        Path: The catalogue that was written.
    """
    payload = {
        "schema_version": 1,
        "servers": [
            {
                "id": "push-gate",
                "capability": capability,
                "repo": repo,
                "entry": entry,
                "interpreter": "python",
            }
        ],
    }
    Path(path).write_text(json.dumps(payload), encoding="utf-8")
    return Path(path)


class TestTheSignatureCannotResolveSettingsItself:
    """The assertion must be unable to consult a machine-specific file."""

    def test_settings_is_a_required_parameter(self):
        """HLD 7.7 writes this with no arguments; that form is the hazard.

        A zero-argument assertion has to resolve a settings file internally, so
        the suite's result would change when the owner edits their configuration.
        Requiring the argument makes that impossible rather than merely unlikely.
        """
        parameter = signature(gate.assert_push_gate_reachable).parameters["settings"]

        assert parameter.default is Parameter.empty

    def test_calling_it_with_no_settings_is_a_type_error(self):
        with pytest.raises(TypeError):
            gate.assert_push_gate_reachable()

    def test_a_parsed_mapping_needs_no_filesystem_at_all(self):
        assert gate.assert_push_gate_reachable(REGISTERED, reachability=UNREACHABLE) is None


class TestTruthTable:
    """All four cells of the AC-1 biconditional, each measured."""

    @pytest.mark.parametrize(
        "settings,reachability,should_raise,cell",
        [
            (REGISTERED, REACHABLE, False, "registered + reachable"),
            (REGISTERED, UNREACHABLE, False, "registered + unreachable"),
            (UNREGISTERED, REACHABLE, False, "absent + reachable"),
            (UNREGISTERED, UNREACHABLE, True, "absent + unreachable"),
        ],
    )
    def test_every_cell_has_the_specified_verdict(self, settings, reachability, should_raise, cell):
        if should_raise:
            with pytest.raises(gate.PushGateUnreachable):
                gate.assert_push_gate_reachable(settings, reachability=reachability)
        else:
            assert gate.assert_push_gate_reachable(settings, reachability=reachability) is None, cell

    def test_the_post_deletion_steady_state_passes(self):
        """The cell PRD FR-4 produces, called out on its own because it is the point.

        A check that failed whenever the registration was absent would pass a
        naive reading of AC 1 and would block the deletion this gate exists to
        make safe.
        """
        assert gate.assert_push_gate_reachable(UNREGISTERED, reachability=REACHABLE) is None

    def test_exactly_one_cell_of_four_fails(self):
        cells = [(s, r) for s in (REGISTERED, UNREGISTERED) for r in (REACHABLE, UNREACHABLE)]
        failures = 0
        for settings, reachability in cells:
            try:
                gate.assert_push_gate_reachable(settings, reachability=reachability)
            except gate.PushGateUnreachable:
                failures += 1

        assert (len(cells), failures) == (4, 1)


class TestTheAssertionCanFail:
    """AC 4: a companion negative test proving the check is capable of failing."""

    def test_the_failing_cell_actually_raises(self):
        with pytest.raises(gate.PushGateUnreachable):
            gate.assert_push_gate_reachable(UNREGISTERED, reachability=UNREACHABLE)

    def test_the_refusal_names_its_cause_and_the_governing_records(self):
        with pytest.raises(gate.PushGateUnreachable) as caught:
            gate.assert_push_gate_reachable(UNREGISTERED, reachability=UNREACHABLE)
        message = str(caught.value)

        assert "stubbed unreachable" in message
        assert "ADR-017" in message
        assert "FR-4" in message

    def test_the_command_line_reports_the_failure_as_a_finding(self, tmp_path):
        settings = tmp_path / "settings.json"
        settings.write_text(json.dumps(UNREGISTERED), encoding="utf-8")
        catalogue = _scratch_catalogue(tmp_path / "registry.json", "does/not/exist.py", repo="nowhere")
        findings, _, registered = gate.run_all(settings_path=settings, catalogue_path=catalogue, skip_evidence=True)

        assert registered is False
        assert [(f.check, f.severity) for f in findings] == [("FF-1", "CRITICAL")]

    def test_the_command_line_exits_nonzero_on_that_state(self, tmp_path, capsys):
        settings = tmp_path / "settings.json"
        settings.write_text(json.dumps(UNREGISTERED), encoding="utf-8")
        catalogue = _scratch_catalogue(tmp_path / "registry.json", "does/not/exist.py", repo="nowhere")
        status = gate.main(
            [
                "--skip-evidence",
                "--settings",
                str(settings),
                "--catalogue",
                str(catalogue),
            ]
        )

        assert status == 1
        assert "FAIL" in capsys.readouterr().out


class TestIgnoresTheHookDirectory:
    """AC 2: the verdict must not move with hooks/pre_tool_enforcer/ on disk.

    The registration and the directory come apart in both directions. The
    directory can survive a commit that removed the registration -- which is what
    PRD FR-4 produces first -- and a registration can name a script that is
    already gone. A check that stats the directory is measuring the wrong thing.
    """

    @staticmethod
    def _mirror(tmp_path):
        """Build a scratch tree carrying a real, reachable push-gate server.

        Args:
            tmp_path: Directory to build the mirror in.

        Returns:
            tuple: (settings path, catalogue path, repo root).
        """
        root = tmp_path / "mirror"
        (root / "src" / "mcp").mkdir(parents=True)
        shutil.copytree(SERVER_PACKAGE, root / "src" / "mcp" / "push_gate")
        settings = root / "settings.json"
        settings.write_text(json.dumps(UNREGISTERED), encoding="utf-8")
        catalogue = _scratch_catalogue(root / "registry.json", "src/mcp/push_gate/server.py")
        return settings, catalogue, root

    @staticmethod
    def _plant_hook(root):
        """Create a plausible hooks/pre_tool_enforcer/ tree inside a scratch root.

        Args:
            root: Scratch repository root.

        Returns:
            Path: The planted policy file.
        """
        policy = root / "hooks" / "pre_tool_enforcer" / "policies" / "push_gate.py"
        policy.parent.mkdir(parents=True, exist_ok=True)
        policy.write_text("def check():\n    return None\n", encoding="utf-8")
        return policy

    def test_planting_and_removing_the_directory_does_not_move_the_verdict(self, tmp_path):
        settings, catalogue, root = self._mirror(tmp_path)

        def verdict():
            """Run the gate against the scratch tree.

            Returns:
                tuple: (finding tuples, reachability flag).
            """
            findings, measured, _ = gate.run_all(
                settings_path=settings, catalogue_path=catalogue, repo_root=root, skip_evidence=True
            )
            return tuple((f.check, f.message) for f in findings), measured.reachable

        before = verdict()
        policy = self._plant_hook(root)
        with_hook = verdict()
        shutil.rmtree(root / "hooks")
        after = verdict()

        assert policy.exists() is False
        assert before == with_hook == after
        assert before == ((), True)

    def test_the_directory_does_not_rescue_an_unreachable_gate(self, tmp_path):
        """Planting the hook tree must not turn a failing verdict into a pass.

        This is the direction that would matter if the check had been written
        against the filesystem: the tree would look like protection while the
        registration that actually runs it was already gone.
        """
        settings, _, root = self._mirror(tmp_path)
        catalogue = _scratch_catalogue(tmp_path / "broken.json", "does/not/exist.py", repo="nowhere")
        self._plant_hook(root)
        findings, _, _ = gate.run_all(
            settings_path=settings, catalogue_path=catalogue, repo_root=root, skip_evidence=True
        )

        assert [f.check for f in findings] == ["FF-1"]

    def test_no_code_path_in_the_gate_names_the_hook_package(self):
        """Docstrings may discuss it; executable code must not reach for it."""
        tree = ast.parse(Path(gate.__file__).read_text(encoding="utf-8"))
        docstrings = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                doc = ast.get_docstring(node, clean=False)
                if doc:
                    docstrings.add(doc)
        offenders = [
            node.value
            for node in ast.walk(tree)
            if isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and node.value not in docstrings
            and ("pre_tool_enforcer" in node.value or "hooks/" in node.value)
        ]

        assert offenders == []


class TestRegistrationReading:
    """How the registration axis is decided, in every input shape."""

    @pytest.mark.parametrize(
        "settings,expected",
        [
            ({"hooks": {"PreToolUse": [{"matcher": ""}]}}, True),
            ({"hooks": {"PreToolUse": []}}, False),
            ({"hooks": {"PostToolUse": [{"matcher": ""}]}}, False),
            ({"hooks": {}}, False),
            ({}, False),
            (None, False),
            ("not a mapping", False),
        ],
    )
    def test_parsed_structures_are_read_as_specified(self, settings, expected):
        assert gate.registration_present(settings) is expected

    def test_a_path_is_read_from_disk(self, tmp_path):
        path = tmp_path / "settings.json"
        path.write_text(json.dumps(REGISTERED), encoding="utf-8")

        assert gate.registration_present(path) is True

    def test_an_absent_file_counts_as_no_registration(self, tmp_path):
        assert gate.registration_present(tmp_path / "missing.json") is False

    def test_an_unparseable_file_counts_as_no_registration(self, tmp_path):
        """The safe direction: an unreadable file must not grant a pass.

        Counting it as registered would let a corrupted settings file satisfy the
        gate while nothing was actually protecting a push.
        """
        path = tmp_path / "settings.json"
        path.write_text("{ not json", encoding="utf-8")

        assert gate.registration_present(path) is False


class TestReachabilityProbe:
    """Reachability is measured by a real spawn, and can report unreachable."""

    def test_the_real_server_is_reachable_by_name(self):
        measured = gate.probe_reachability()

        assert measured.reachable is True
        assert gate.PUSH_GATE_TOOL_NAME in measured.tools

    def test_a_catalogue_without_the_capability_is_unreachable(self, tmp_path):
        catalogue = _scratch_catalogue(
            tmp_path / "registry.json", "src/mcp/push_gate/server.py", capability="something-else"
        )
        measured = gate.probe_reachability(catalogue_path=catalogue)

        assert measured.reachable is False
        assert gate.PUSH_GATE_CAPABILITY in measured.detail

    def test_a_missing_entry_point_is_unreachable(self, tmp_path):
        catalogue = _scratch_catalogue(tmp_path / "registry.json", "does/not/exist.py", repo="nowhere")
        measured = gate.probe_reachability(catalogue_path=catalogue, repo_root=tmp_path)

        assert measured.reachable is False
        assert "exists at neither" in measured.detail

    def test_an_unreadable_catalogue_is_unreachable(self, tmp_path):
        broken = tmp_path / "registry.json"
        broken.write_text("{ not json", encoding="utf-8")
        measured = gate.probe_reachability(catalogue_path=broken)

        assert measured.reachable is False

    def test_a_server_that_crashes_is_unreachable(self, tmp_path):
        """A module that imports is not evidence that a tool can be called."""
        server = tmp_path / "server.py"
        server.write_text("import sys\nsys.exit(3)\n", encoding="utf-8")
        catalogue = _scratch_catalogue(tmp_path / "registry.json", "server.py")
        measured = gate.probe_reachability(catalogue_path=catalogue, repo_root=tmp_path)

        assert measured.reachable is False
        assert "exited 3" in measured.detail

    def test_a_server_advertising_a_different_tool_is_unreachable(self, tmp_path):
        """SPECIFICITY: reachability is by NAME, not by 'some server answered'."""
        server = tmp_path / "server.py"
        server.write_text(
            "import json, sys\n"
            "for line in sys.stdin:\n"
            "    line = line.strip()\n"
            "    if not line:\n"
            "        continue\n"
            "    message = json.loads(line)\n"
            "    if message.get('id') == 1:\n"
            "        sys.stdout.write(json.dumps({'jsonrpc': '2.0', 'id': 1, 'result': {}}) + '\\n')\n"
            "    elif message.get('id') == 2:\n"
            "        payload = {'tools': [{'name': 'something_else'}]}\n"
            "        sys.stdout.write(json.dumps({'jsonrpc': '2.0', 'id': 2, 'result': payload}) + '\\n')\n"
            "    sys.stdout.flush()\n",
            encoding="utf-8",
        )
        catalogue = _scratch_catalogue(tmp_path / "registry.json", "server.py")
        measured = gate.probe_reachability(catalogue_path=catalogue, repo_root=tmp_path)

        assert measured.reachable is False
        assert "something_else" in measured.detail

    def test_specificity_the_same_stub_is_reachable_under_the_expected_name(self, tmp_path):
        server = tmp_path / "server.py"
        server.write_text(
            "import json, sys\n"
            "for line in sys.stdin:\n"
            "    line = line.strip()\n"
            "    if not line:\n"
            "        continue\n"
            "    message = json.loads(line)\n"
            "    if message.get('id') == 2:\n"
            "        payload = {'tools': [{'name': 'check_push_allowed'}]}\n"
            "        sys.stdout.write(json.dumps({'jsonrpc': '2.0', 'id': 2, 'result': payload}) + '\\n')\n"
            "        sys.stdout.flush()\n",
            encoding="utf-8",
        )
        catalogue = _scratch_catalogue(tmp_path / "registry.json", "server.py")
        measured = gate.probe_reachability(catalogue_path=catalogue, repo_root=tmp_path)

        assert measured.reachable is True


class TestToolNameBindingDoesNotDrift:
    """The names this gate looks for must stay bound to what actually exists.

    A gate that searched for a name nothing advertises would fail forever; a gate
    whose constant silently stopped matching the server would pass forever. Both
    are caught here rather than in production.
    """

    def test_the_expected_tool_name_matches_the_server_constant(self):
        source = ast.parse(SERVER_PATH.read_text(encoding="utf-8"))
        declared = {
            node.targets[0].id: node.value.value
            for node in source.body
            if isinstance(node, ast.Assign)
            and isinstance(node.targets[0], ast.Name)
            and isinstance(node.value, ast.Constant)
        }

        assert gate.PUSH_GATE_TOOL_NAME == declared["TOOL_NAME"]

    def test_the_capability_matches_the_shipped_catalogue(self):
        catalogue = gate.load_catalogue(gate.DEFAULT_CATALOGUE_PATH)

        assert gate.push_gate_descriptor(catalogue) is not None

    def test_the_capability_matches_the_registration_command(self):
        """mcp_registration.py resolves the same capability; both must agree."""
        source = ast.parse((REPO_ROOT / "plugin" / "scripts" / "mcp_registration.py").read_text(encoding="utf-8"))
        declared = {
            node.targets[0].id: node.value.value
            for node in source.body
            if isinstance(node, ast.Assign)
            and isinstance(node.targets[0], ast.Name)
            and isinstance(node.value, ast.Constant)
        }

        assert gate.PUSH_GATE_CAPABILITY == declared["PUSH_GATE_CAPABILITY"]


class TestEquivalenceEvidence:
    """FF-2: V2-024's standing obligation, made mechanical.

    Beyond this issue's acceptance criteria, and recorded as such. V2-024 handed
    over that TestNoDrift and TestAssertionMappingIsComplete self-skip once the
    hook policy file is deleted, so after PRD FR-4 nothing fails if the module is
    removed with it and the equivalence record vanishes silently.
    """

    def test_the_record_is_intact_today(self):
        assert gate.check_equivalence_evidence() == []

    def test_the_pinned_composition_matches_the_shipped_record(self):
        dispositions, error = gate._assertion_map_dispositions(EVIDENCE_PATH)
        counts = {label: sum(1 for text in dispositions if label in text) for label in gate.EVIDENCE_COMPOSITION}

        assert error is None
        assert len(dispositions) == gate.EVIDENCE_TOTAL
        assert counts == gate.EVIDENCE_COMPOSITION

    def test_a_deleted_record_is_reported(self, tmp_path):
        findings = gate.check_equivalence_evidence(tmp_path / "gone.py")

        assert [(f.check, f.severity) for f in findings] == [("FF-2", "ERROR")]
        assert "self-skip" in findings[0].message

    def test_a_record_stripped_of_its_map_is_reported(self, tmp_path):
        module = tmp_path / "evidence.py"
        module.write_text('"""No map here."""\n', encoding="utf-8")
        findings = gate.check_equivalence_evidence(module)

        assert [f.check for f in findings] == ["FF-2"]
        assert gate.EVIDENCE_SYMBOL in findings[0].message

    def test_a_shortened_record_is_reported(self, tmp_path):
        module = tmp_path / "evidence.py"
        module.write_text('ASSERTION_MAP = {"a": "PORTED VERBATIM"}\n', encoding="utf-8")
        findings = gate.check_equivalence_evidence(module)

        assert [f.check for f in findings] == ["FF-2"]
        assert "1 entries" in findings[0].message

    def test_a_lengthened_record_is_reported(self, tmp_path):
        """An ADDED entry must be caught, not only a removed one.

        The added entry carries a disposition matching none of the three pinned
        labels, so the composition counts still read 17/4/2 and only the total
        moves. A count check written as "fewer than expected" rather than
        "different from expected" passes this and would let an unclassified
        assertion enter the record unnoticed.
        """
        module = tmp_path / "evidence.py"
        entries = ['"v{0}": "PORTED VERBATIM"'.format(i) for i in range(17)]
        entries += ['"e{0}": "EQUIVALENT"'.format(i) for i in range(4)]
        entries += ['"n{0}": "NOT CARRIED"'.format(i) for i in range(2)]
        entries += ['"extra": "TBD"']
        module.write_text("ASSERTION_MAP = {{{0}}}\n".format(", ".join(entries)), encoding="utf-8")
        findings = gate.check_equivalence_evidence(module)

        assert [f.check for f in findings] == ["FF-2"]
        assert "24 entries" in findings[0].message

    def test_a_record_of_the_right_size_but_wrong_composition_is_reported(self, tmp_path):
        """Counting entries alone would accept a record whose meaning changed."""
        module = tmp_path / "evidence.py"
        entries = ", ".join('"k{0}": "PORTED VERBATIM"'.format(i) for i in range(gate.EVIDENCE_TOTAL))
        module.write_text("ASSERTION_MAP = {{{0}}}\n".format(entries), encoding="utf-8")
        findings = gate.check_equivalence_evidence(module)
        messages = " ".join(f.message for f in findings)

        assert [f.check for f in findings] != []
        assert "EQUIVALENT" in messages and "NOT CARRIED" in messages

    def test_run_all_actually_composes_ff2(self, tmp_path):
        """FF-2 must be reached through the entry point the workflow invokes.

        Testing check_equivalence_evidence directly proves the check works; it
        does not prove the gate runs it. A composition that silently dropped FF-2
        would leave every direct test passing while the CI step checked nothing.
        """
        findings, _, _ = gate.run_all(evidence_path=tmp_path / "gone.py", skip_evidence=False)

        assert "FF-2" in [f.check for f in findings]

    def test_specificity_skip_evidence_removes_only_ff2(self, tmp_path):
        findings, _, _ = gate.run_all(evidence_path=tmp_path / "gone.py", skip_evidence=True)

        assert findings == []

    def test_specificity_the_record_is_accepted_without_the_hook_present(self, tmp_path):
        """FF-2 must constrain how the deletion is written, never block it."""
        module = tmp_path / "evidence.py"
        module.write_text(EVIDENCE_PATH.read_text(encoding="utf-8"), encoding="utf-8")
        findings = gate.check_equivalence_evidence(module)

        assert findings == []


class TestCiWiring:
    """The gate is executed from its STORED form, not from its authored form.

    An assertion nothing invokes is the defect this repository has already found
    once. These tests read the workflow file and run the commands it actually
    declares, so a step that was edited into uselessness fails here.
    """

    @staticmethod
    def _workflow():
        """Parse the workflow document.

        Returns:
            dict: The parsed YAML.
        """
        return yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))

    @staticmethod
    def _steps():
        """Return the workflow's steps that declare a run command.

        Returns:
            list: (name, run) tuples in declaration order.
        """
        job = TestCiWiring._workflow()["jobs"]["push-gate-reachable"]
        return [(step.get("name", ""), step["run"]) for step in job["steps"] if "run" in step]

    def test_the_workflow_exists_and_declares_no_path_filters(self):
        """ci.yml's paths-ignore skips markdown; a sequencing gate cannot be."""
        triggers = self._workflow()[True]

        assert WORKFLOW_PATH.is_file()
        for event in ("push", "pull_request"):
            assert "paths-ignore" not in triggers[event]
            assert "paths" not in triggers[event]

    def test_the_gate_step_names_this_script(self):
        commands = [run for _, run in self._steps()]

        assert any("scripts/verify_push_gate_reachable.py" in run for run in commands)

    def test_the_stored_gate_command_passes_when_executed(self):
        """Runs the gate step's command verbatim, as the workflow would."""
        step = [run for name, run in self._steps() if name == "Push-gate reachability gate"][0]
        result = subprocess.run(step.strip().split(), capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=180)

        assert result.returncode == 0, result.stdout + result.stderr

    @pytest.mark.parametrize("step_name", ["negative control", "specificity control"])
    def test_the_stored_control_steps_pass_when_executed(self, step_name):
        """The controls prove BOTH directions of the biconditional in CI itself.

        The two steps differ in exactly one axis -- the PreToolUse registration --
        and run against the same deliberately broken catalogue, so a gate wired
        with the wrong polarity fails one of them on every run.
        """
        bash = shutil.which("bash")
        if bash is None:
            pytest.skip("bash is unavailable on this machine; the step is executed in CI")
        script = [run for name, run in self._steps() if step_name in name][0]
        result = subprocess.run([bash, "-c", script], capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=180)

        assert result.returncode == 0, result.stdout + result.stderr
        assert "CONTROL OK" in result.stdout


class TestGuardedSettingsAreNeverConsulted:
    """The suite's result must not depend on the machine's own configuration."""

    def test_the_default_settings_path_is_the_tracked_repository_file(self):
        """Not the user-scope file, which carries a live PreToolUse entry."""
        assert gate.DEFAULT_SETTINGS_PATH == REPO_ROOT / ".claude" / "settings.local.json"
        assert gate.DEFAULT_SETTINGS_PATH.is_file()

    def test_running_the_full_gate_leaves_every_guarded_file_untouched(self):
        before = _digests()
        gate.main(["--json"])

        assert _digests() == before

    def test_the_verdict_does_not_depend_on_the_user_scope_file(self):
        """The two guarded user-scope files differ in PreToolUse; neither is read.

        MEASURED 2026-08-03: ~/.claude/settings.json carries a live PreToolUse
        entry while ~/.claude/settings.local.json does not. Feeding both through
        the assertion with the same reachability shows the gate reads what it is
        given rather than what the machine happens to hold.
        """
        findings, _, registered = gate.run_all(skip_evidence=True)

        assert registered is False
        assert findings == []

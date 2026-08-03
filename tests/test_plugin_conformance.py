"""Tests for the plugin packaging conformance gate (PRD FR-14 / SRS FR-26).

Every check in ``scripts/verify_plugin_conformance.py`` is paired here with a
NEGATIVE test that plants a violation and proves the check rejects it, and with
a SPECIFICITY test that proves the same check accepts content which violates
nothing. A gate observed only to pass is indistinguishable from a gate that
cannot fail, and a gate that rejects everything has no discriminating power; a
check needs both halves before it is worth wiring into CI.

The CI workflow's own gate command is executed from its STORED form: the test
parses ``.github/workflows/plugin-conformance.yml``, extracts the ``run`` string
of the gate step, and runs exactly that string. An assertion written in a test
that merely resembles the one CI runs proves nothing about CI.

Scope note. AC 4(b) of issue V2-015 - "after ``register-mcp`` runs, the push
gate and progress writer become reachable" - is NOT tested here and cannot be.
``register-mcp`` is V2-016's deliverable and zero lines of it exist. What IS
tested is AC 3(a)'s other half: that the shipped tree bundles no MCP
configuration by any route, so the push gate is provably NOT reachable from a
fresh install. That is the precondition AC 4(b) will later flip.
"""

import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = REPO_ROOT / "plugin"
GATE_SCRIPT = REPO_ROOT / "scripts" / "verify_plugin_conformance.py"
WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "plugin-conformance.yml"
MANIFEST_PATH = PLUGIN_ROOT / ".claude-plugin" / "plugin.json"


def _load_gate_module():
    """Import the conformance gate module directly from its file path.

    ``scripts/`` is not an importable package, so the module is loaded by
    explicit file location rather than by name.

    Returns:
        module: The loaded ``verify_plugin_conformance`` module.
    """
    spec = importlib.util.spec_from_file_location("verify_plugin_conformance", str(GATE_SCRIPT))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gate = _load_gate_module()


def _usable_bash():
    """Find a bash that can actually execute a script on this machine.

    ``shutil.which("bash")`` is not sufficient on Windows: it resolves to the
    WSL launcher stub, which fails with an exec error when no distribution is
    installed. Each candidate is therefore probed by running a trivial script
    rather than trusted because it is on PATH.

    Returns:
        str or None: Path to a working bash, or None when none was found.
    """
    candidates = [shutil.which("bash")]
    candidates.append(r"C:/Program Files/Git/bin/bash.exe")
    candidates.append(r"C:/Program Files (x86)/Git/bin/bash.exe")
    candidates.append("/bin/bash")
    for candidate in candidates:
        if not candidate or not Path(candidate).exists():
            continue
        try:
            probe = subprocess.run([candidate, "-c", "exit 0"], capture_output=True, timeout=30)
        except OSError:
            continue
        if probe.returncode == 0:
            return candidate
    return None


BASH = _usable_bash()


@pytest.fixture()
def scratch_plugin(tmp_path):
    """Copy the real plugin tree into a scratch directory.

    Args:
        tmp_path: pytest-provided temporary directory.

    Returns:
        Path: Root of the scratch copy, which starts out conformant.
    """
    destination = tmp_path / "plugin"
    shutil.copytree(str(PLUGIN_ROOT), str(destination))
    return destination


def _write_manifest(plugin_root, manifest):
    """Overwrite a scratch tree's manifest with the given object.

    Args:
        plugin_root: Path of the scratch plugin root.
        manifest: Object to serialise as the manifest.

    Returns:
        None
    """
    target = Path(plugin_root) / ".claude-plugin" / "plugin.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def _findings_for(plugin_root):
    """Run every fitness function and return the findings.

    Args:
        plugin_root: Path of the plugin root to check.

    Returns:
        list: Finding objects produced by the gate.
    """
    return gate.run_all(Path(plugin_root))


def _rules(findings):
    """Collect the distinct rule identifiers present in a finding list.

    Args:
        findings: Iterable of Finding objects.

    Returns:
        set: Rule identifier strings.
    """
    return {finding.rule for finding in findings}


def _checks(findings):
    """Collect the distinct fitness function identifiers in a finding list.

    Args:
        findings: Iterable of Finding objects.

    Returns:
        set: Check identifier strings.
    """
    return {finding.check for finding in findings}


class TestRealTreePasses:
    """The shipped plugin tree must satisfy every fitness function."""

    def test_real_plugin_tree_has_no_findings(self):
        """The tree committed to this repository passes the gate outright."""
        findings = _findings_for(PLUGIN_ROOT)
        assert findings == [], "\n".join(str(f) for f in findings)

    def test_gate_exits_zero_on_real_tree_as_a_subprocess(self):
        """Running the gate as CI runs it exits 0 on the real tree."""
        result = subprocess.run(
            [sys.executable, str(GATE_SCRIPT)],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stdout + result.stderr

    def test_manifest_declares_explicit_semver_version(self):
        """FR-26 requires an explicit semver version, not an implied one."""
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        assert "version" in manifest
        assert gate.check_manifest_schema(manifest) == []


class TestSpecificityControl:
    """The gate must discriminate, not reject everything it is shown."""

    def test_unrelated_content_does_not_trip_any_check(self, scratch_plugin):
        """Files and directories that merely mention hooks or mcp are ignored."""
        reference = scratch_plugin / "reference"
        (reference / "hooks-notes").mkdir(parents=True)
        (reference / "hooks-notes" / "webhooks.md").write_text("notes about hooks\n", encoding="utf-8")
        (reference / "hooks.md").write_text("not a hooks config\n", encoding="utf-8")
        (reference / "mcp-notes.md").write_text("notes about mcp\n", encoding="utf-8")
        (reference / "mcp.json.sample").write_text("{}\n", encoding="utf-8")
        (reference / ".mcp.json.bak").write_text("{}\n", encoding="utf-8")
        findings = _findings_for(scratch_plugin)
        assert findings == [], "\n".join(str(f) for f in findings)

    def test_extra_permitted_manifest_fields_are_accepted(self, scratch_plugin):
        """A permitted-but-unused metadata field is not a violation."""
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        manifest["license"] = "MIT"
        manifest["keywords"] = ["sdlc", "orchestration"]
        manifest["repository"] = "https://github.com/techdeveloper-org/claude-workflow-engine"
        _write_manifest(scratch_plugin, manifest)
        findings = _findings_for(scratch_plugin)
        assert findings == [], "\n".join(str(f) for f in findings)

    @pytest.mark.parametrize(
        "field",
        [f for f in gate.PERMITTED_MANIFEST_FIELDS if f not in gate.FORBIDDEN_MANIFEST_FIELDS],
    )
    def test_every_measured_permitted_field_passes_the_schema(self, field):
        """The closed-world schema admits every key the host CLI admits.

        A schema narrower than the measured permitted set would block a future
        issue from using a key Claude Code supports, and the failure would look
        like a manifest defect rather than a gate that is out of date.
        """
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        manifest.setdefault(field, "placeholder")
        assert gate.check_manifest_schema(manifest) == [], field

    def test_additional_capability_content_is_accepted(self, scratch_plugin):
        """Adding more commands, agents and skills is not a violation."""
        (scratch_plugin / "commands" / "another.md").write_text(
            "---\ndescription: another command\n---\nbody\n", encoding="utf-8"
        )
        (scratch_plugin / "agents" / "another.md").write_text(
            "---\nname: another\ndescription: another agent\n---\nbody\n",
            encoding="utf-8",
        )
        skill_dir = scratch_plugin / "skills" / "another-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(
            "---\nname: another-skill\ndescription: another skill\n---\nbody\n",
            encoding="utf-8",
        )
        assert _findings_for(scratch_plugin) == []


class TestAdr010ZeroHooks:
    """FF-2: any hooks artefact in the plugin tree is a CRITICAL failure."""

    def test_planted_hooks_json_is_rejected(self, scratch_plugin):
        """The canonical violation - hooks/hooks.json - fails the gate."""
        hooks_dir = scratch_plugin / "hooks"
        hooks_dir.mkdir()
        (hooks_dir / "hooks.json").write_text('{"hooks": {}}', encoding="utf-8")
        findings = _findings_for(scratch_plugin)
        assert findings, "gate accepted a planted hooks/hooks.json"
        assert "ADR-010" in _rules(findings)
        assert all(f.severity == "CRITICAL" for f in findings if f.rule == "ADR-010")

    def test_bare_hooks_directory_is_rejected(self, scratch_plugin):
        """A hooks directory with no hooks.json in it still fails."""
        hooks_dir = scratch_plugin / "hooks"
        hooks_dir.mkdir()
        (hooks_dir / "notes.md").write_text("placeholder\n", encoding="utf-8")
        findings = [f for f in _findings_for(scratch_plugin) if f.rule == "ADR-010"]
        assert findings, "gate accepted a bare hooks/ directory"

    def test_renamed_hooks_config_is_rejected(self, scratch_plugin):
        """A *hooks.json file outside a hooks/ directory still fails."""
        nested = scratch_plugin / "config"
        nested.mkdir()
        (nested / "my-hooks.json").write_text('{"hooks": {}}', encoding="utf-8")
        findings = [f for f in _findings_for(scratch_plugin) if f.rule == "ADR-010"]
        assert findings, "gate accepted config/my-hooks.json"

    def test_hooks_nested_under_claude_plugin_is_rejected(self, scratch_plugin):
        """Hooks hidden inside .claude-plugin/ are found, not missed."""
        nested = scratch_plugin / ".claude-plugin" / "hooks"
        nested.mkdir(parents=True)
        (nested / "hooks.json").write_text('{"hooks": {}}', encoding="utf-8")
        findings = [f for f in _findings_for(scratch_plugin) if f.rule == "ADR-010"]
        assert findings, "gate missed hooks nested under .claude-plugin/"

    def test_manifest_hooks_key_is_rejected_without_any_hooks_file(self, scratch_plugin):
        """The path-override bypass is closed.

        FR-26 states the ADR-010 check as a find for ``hooks/`` or
        ``*hooks.json``. The manifest's ``hooks`` path-override key can point at
        a file matching neither pattern, so a find-only gate would pass this
        tree while the runtime loaded the hooks anyway.
        """
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        manifest["hooks"] = "./handlers.json"
        _write_manifest(scratch_plugin, manifest)
        findings = [f for f in _findings_for(scratch_plugin) if f.rule == "ADR-010"]
        assert findings, "gate accepted a manifest hooks path-override"
        assert findings[0].severity == "CRITICAL"


class TestAdr019ZeroBundledMcp:
    """FF-3: any bundled MCP configuration is a CRITICAL failure."""

    def test_planted_mcp_json_at_root_is_rejected(self, scratch_plugin):
        """The canonical violation - a root .mcp.json - fails the gate."""
        (scratch_plugin / ".mcp.json").write_text('{"mcpServers": {"x": {"command": "python"}}}', encoding="utf-8")
        findings = [f for f in _findings_for(scratch_plugin) if f.rule == "ADR-019"]
        assert findings, "gate accepted a bundled .mcp.json"
        assert findings[0].severity == "CRITICAL"

    def test_nested_mcp_json_is_rejected(self, scratch_plugin):
        """A .mcp.json anywhere below the root also fails."""
        nested = scratch_plugin / "vendor"
        nested.mkdir()
        (nested / ".mcp.json").write_text('{"mcpServers": {}}', encoding="utf-8")
        findings = [f for f in _findings_for(scratch_plugin) if f.rule == "ADR-019"]
        assert findings, "gate accepted a nested .mcp.json"

    def test_manifest_mcpservers_key_is_rejected_without_any_mcp_file(self, scratch_plugin):
        """The mcpServers path-override bypass is closed for the same reason."""
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        manifest["mcpServers"] = "./servers.json"
        _write_manifest(scratch_plugin, manifest)
        findings = [f for f in _findings_for(scratch_plugin) if f.rule == "ADR-019"]
        assert findings, "gate accepted a manifest mcpServers path-override"
        assert findings[0].severity == "CRITICAL"


class TestManifestSchema:
    """FF-1: the manifest validates against a closed-world contract."""

    @pytest.mark.parametrize("missing", ["name", "description", "version"])
    def test_required_field_absence_is_rejected(self, scratch_plugin, missing):
        """Each of the three required fields is individually load-bearing."""
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        del manifest[missing]
        _write_manifest(scratch_plugin, manifest)
        findings = [f for f in _findings_for(scratch_plugin) if f.check == "FF-1"]
        assert findings, "gate accepted a manifest missing {0}".format(missing)

    @pytest.mark.parametrize("version", ["1.2", "v1.2.3", "1.2.3.4", "latest", "", "01.2.3"])
    def test_non_semver_version_is_rejected(self, scratch_plugin, version):
        """FR-26 requires explicit semver, which the host CLI does not enforce."""
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        manifest["version"] = version
        _write_manifest(scratch_plugin, manifest)
        findings = [f for f in _findings_for(scratch_plugin) if f.check == "FF-1"]
        assert findings, "gate accepted version {0!r}".format(version)

    @pytest.mark.parametrize("version", ["0.1.0", "1.0.0", "2.0.0-rc.1", "1.21.5", "1.0.0+build.7"])
    def test_valid_semver_version_is_accepted(self, scratch_plugin, version):
        """Valid semver, including prerelease and build metadata, passes."""
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        manifest["version"] = version
        _write_manifest(scratch_plugin, manifest)
        findings = [f for f in _findings_for(scratch_plugin) if f.check == "FF-1"]
        assert findings == [], "gate rejected valid semver {0!r}".format(version)

    def test_out_of_schema_key_rejects_the_whole_manifest(self, scratch_plugin):
        """An unsanctioned key is a rejection, never a note to move past."""
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        manifest["licenseType"] = "MIT"
        _write_manifest(scratch_plugin, manifest)
        findings = [f for f in _findings_for(scratch_plugin) if f.check == "FF-1"]
        assert findings, "gate accepted an out-of-schema manifest key"

    def test_absent_manifest_is_rejected(self, scratch_plugin):
        """A plugin root with no manifest fails rather than being skipped."""
        (scratch_plugin / ".claude-plugin" / "plugin.json").unlink()
        findings = _findings_for(scratch_plugin)
        assert any(f.check == "FF-1" for f in findings)

    def test_malformed_manifest_json_is_rejected(self, scratch_plugin):
        """A syntactically broken manifest fails rather than raising."""
        (scratch_plugin / ".claude-plugin" / "plugin.json").write_text("{ not json", encoding="utf-8")
        findings = _findings_for(scratch_plugin)
        assert any(f.check == "FF-1" for f in findings)


class TestDiscoveryLayout:
    """FF-4: capability directories must sit where discovery looks."""

    def test_capability_directory_nested_under_manifest_dir_is_rejected(self, scratch_plugin):
        """The most expensive layout defect is detected, not silently allowed."""
        nested = scratch_plugin / ".claude-plugin" / "commands"
        nested.mkdir(parents=True)
        (nested / "hidden.md").write_text("---\ndescription: hidden\n---\nbody\n", encoding="utf-8")
        findings = [f for f in _findings_for(scratch_plugin) if f.check == "FF-4"]
        assert findings, "gate accepted a capability directory nested under the manifest directory"

    def test_tree_with_no_capability_directories_is_rejected(self, scratch_plugin):
        """A manifest-only tree installs cleanly and exposes nothing."""
        for name in ("commands", "agents", "skills"):
            shutil.rmtree(str(scratch_plugin / name))
        findings = [f for f in _findings_for(scratch_plugin) if f.check == "FF-4"]
        assert findings, "gate accepted a tree exposing zero capabilities"

    def test_missing_plugin_root_is_rejected(self, tmp_path):
        """A plugin root that does not exist is a failure, not a pass."""
        findings = _findings_for(tmp_path / "absent")
        assert findings


class TestFreshInstallSurface:
    """AC 3(a): what a fresh install with no register-mcp run does and does not give."""

    def test_commands_agents_and_skills_are_discoverable_at_the_plugin_root(self):
        """All three capability classes are present where discovery scans."""
        commands = sorted((PLUGIN_ROOT / "commands").glob("*.md"))
        agents = sorted((PLUGIN_ROOT / "agents").glob("*.md"))
        skills = sorted((PLUGIN_ROOT / "skills").glob("*/SKILL.md"))
        assert commands, "no discoverable command at the plugin root"
        assert agents, "no discoverable agent at the plugin root"
        assert skills, "no discoverable skill at the plugin root"

    @pytest.mark.parametrize("relative", ["commands", "agents", "skills"])
    def test_capability_directories_are_not_nested_under_manifest_dir(self, relative):
        """Nothing discovery needs is hidden inside .claude-plugin/."""
        assert (PLUGIN_ROOT / relative).is_dir()
        assert not (PLUGIN_ROOT / ".claude-plugin" / relative).exists()

    def test_every_capability_artefact_carries_yaml_frontmatter(self):
        """A capability file without frontmatter is not loadable."""
        artefacts = (
            sorted((PLUGIN_ROOT / "commands").glob("*.md"))
            + sorted((PLUGIN_ROOT / "agents").glob("*.md"))
            + sorted((PLUGIN_ROOT / "skills").glob("*/SKILL.md"))
        )
        for artefact in artefacts:
            text = artefact.read_text(encoding="utf-8")
            assert text.startswith("---\n"), artefact
            _, _, remainder = text.partition("---\n")
            block, separator, _ = remainder.partition("\n---\n")
            assert separator, artefact
            parsed = yaml.safe_load(block)
            assert isinstance(parsed, dict) and parsed.get("description"), artefact

    def test_push_gate_is_not_reachable_from_a_fresh_install(self):
        """AC 3(a): the FR-23 push gate is unreachable, and that is expected.

        Reachability of any MCP-backed capability requires an MCP server
        registration. The plugin ships no route to one: no ``.mcp.json`` file by
        any name or depth, and no ``mcpServers`` manifest key. Both routes are
        asserted, because closing only one leaves the capability reachable
        through the other.
        """
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        assert "mcpServers" not in manifest
        found = [
            os.path.join(dirpath, name)
            for dirpath, _dirs, files in os.walk(str(PLUGIN_ROOT))
            for name in files
            if name.lower() == ".mcp.json"
        ]
        assert found == [], found

    def test_register_mcp_and_its_inverse_are_present(self):
        """V2-016 landed the real command pair, so the anti-stub guard retires.

        The predecessor of this test asserted register-mcp was ABSENT, to stop
        V2-015 faking V2-016's deliverable with a stub. The real pair now ships,
        which is the intended reason for that guard's removal. Reachability of
        what these commands write is measured in tests/test_register_mcp.py; all
        that is asserted here is that the plugin surface exposes both halves,
        because a register with no inverse is not reversible.
        """
        command_names = {p.stem for p in (PLUGIN_ROOT / "commands").glob("*.md")}
        assert "register-mcp" in command_names
        assert "unregister-mcp" in command_names

    def test_shipped_executable_code_never_resolves_a_path_from_the_cwd(self):
        """The path-resolution audit its predecessor said would become required.

        The earlier form of this test asserted the plugin shipped no executable
        code at all, and said in its own docstring that the moment that failed,
        a path-resolution audit against CLAUDE_PLUGIN_ROOT became required. It
        has failed, so this is that audit. After a real install the plugin's
        files sit under the plugin manager's cache while the working directory
        is whatever project the user is in, so a cwd-relative path passes every
        test the author runs and fails for essentially every installed user.
        """
        forbidden = ("Path.cwd(", "os.getcwd(", "os.curdir", 'Path(".")', "Path('.')")
        offenders = []
        for dirpath, _dirs, files in os.walk(str(PLUGIN_ROOT)):
            for name in files:
                if not name.endswith((".py", ".sh", ".ps1", ".js")):
                    continue
                path = Path(dirpath) / name
                text = path.read_text(encoding="utf-8")
                for token in forbidden:
                    if token in text:
                        offenders.append("{0}: {1}".format(path, token))
        assert offenders == [], offenders

    def test_shipped_executable_code_anchors_itself_to_the_manifest(self):
        """Every shipped executable must be able to find its own plugin root.

        The plugin surface skill names two acceptable mechanisms: the
        CLAUDE_PLUGIN_ROOT environment variable, and an ascent to the directory
        containing the manifest. A shipped script that references neither has no
        correct way to locate the files it ships alongside.
        """
        scripts = [
            Path(dirpath) / name
            for dirpath, _dirs, files in os.walk(str(PLUGIN_ROOT))
            for name in files
            if name.endswith((".py", ".sh", ".ps1", ".js"))
        ]
        assert scripts, "no shipped executable code found; this audit has nothing to check"
        entry_points = [p for p in scripts if "__main__" in p.read_text(encoding="utf-8")]
        assert entry_points, "no shipped entry point found"
        for path in entry_points:
            text = path.read_text(encoding="utf-8")
            assert "CLAUDE_PLUGIN_ROOT" in text or "find_plugin_root" in text, path


class TestCiWiring:
    """The gate must be wired into CI in a form that can actually fail a build."""

    @staticmethod
    def _workflow():
        """Parse the plugin conformance workflow.

        Returns:
            dict: Parsed workflow document.
        """
        return yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))

    @staticmethod
    def _steps():
        """Return the workflow job's step list.

        Returns:
            list: Step dictionaries.
        """
        return TestCiWiring._workflow()["jobs"]["plugin-conformance"]["steps"]

    def _gate_step(self):
        """Locate the step that invokes the conformance gate directly.

        Returns:
            dict: The gate step.
        """
        for step in self._steps():
            run = step.get("run", "")
            if "verify_plugin_conformance.py" in run and "--plugin-root" not in run:
                return step
        raise AssertionError("no CI step invokes the conformance gate")

    def test_workflow_exists_and_declares_no_path_filters(self):
        """A markdown-only commit must not be able to skip the gate.

        The repository's main CI workflow ignores ``**/*.md``. The plugin tree is
        almost entirely markdown, so a gate living only in that workflow could be
        skipped by the very commit most likely to introduce a violation.
        """
        workflow = self._workflow()
        triggers = workflow[True] if True in workflow else workflow["on"]
        for event in ("push", "pull_request"):
            assert event in triggers
            assert "paths-ignore" not in (triggers[event] or {})
            assert "paths" not in (triggers[event] or {})

    def test_gate_step_runs_from_its_stored_form(self):
        """Execute the exact command string CI will execute, not a paraphrase."""
        command = self._gate_step()["run"].strip()
        result = subprocess.run(
            command,
            cwd=str(REPO_ROOT),
            shell=True,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, command + "\n" + result.stdout + result.stderr

    def test_gate_step_cannot_be_soft_failed(self):
        """A gate with continue-on-error is a report, not a gate."""
        assert self._gate_step().get("continue-on-error") in (None, False)

    def test_workflow_carries_a_negative_control_step(self):
        """CI itself must prove on every run that the gate can reject."""
        runs = [s.get("run", "") for s in self._steps()]
        negative = [r for r in runs if "NEGATIVE CONTROL" in r]
        assert negative, "workflow has no negative control step"
        assert "hooks.json" in negative[0]
        assert "--plugin-root" in negative[0]

    def test_workflow_carries_a_specificity_control_step(self):
        """CI must also prove the gate does not reject everything."""
        runs = [s.get("run", "") for s in self._steps()]
        assert any("SPECIFICITY CONTROL" in r for r in runs)

    @pytest.mark.skipif(BASH is None, reason="no working bash on this runner")
    @pytest.mark.parametrize("marker", ["NEGATIVE CONTROL", "SPECIFICITY CONTROL"])
    def test_control_steps_run_from_their_stored_form(self, marker):
        """Execute the stored control scripts, not a reimplementation of them."""
        script = next(s["run"] for s in self._steps() if marker in s.get("run", ""))
        result = subprocess.run(
            [BASH, "-c", script],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert marker + " OK" in result.stdout


class TestHostCliCrossCheck:
    """Cross-check the manifest against the host's own validator where present."""

    @pytest.mark.skipif(shutil.which("claude") is None, reason="claude CLI unavailable")
    def test_host_cli_accepts_the_plugin_manifest_in_strict_mode(self):
        """An independent validator agrees the manifest is well formed."""
        result = subprocess.run(
            ["claude", "plugin", "validate", str(PLUGIN_ROOT), "--strict"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stdout + result.stderr

    @pytest.mark.skipif(shutil.which("claude") is None, reason="claude CLI unavailable")
    def test_host_cli_accepts_the_marketplace_manifest_in_strict_mode(self):
        """The catalog entry that makes install-by-name possible also validates."""
        result = subprocess.run(
            ["claude", "plugin", "validate", str(REPO_ROOT), "--strict"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stdout + result.stderr

    @pytest.mark.skipif(shutil.which("claude") is None, reason="claude CLI unavailable")
    def test_host_cli_does_not_enforce_semver_so_the_local_gate_must(self, scratch_plugin):
        """Records the measured gap this gate exists to close.

        Claude Code CLI 2.1.220 accepts a non-semver ``version`` under
        ``--strict``. FR-26 requires explicit semver, so relying on the host
        validator alone would leave that criterion unenforced. If a future CLI
        starts rejecting it, this test fails and the redundancy can be revisited
        deliberately rather than discovered by accident.
        """
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        manifest["version"] = "not-semver"
        _write_manifest(scratch_plugin, manifest)
        host = subprocess.run(
            ["claude", "plugin", "validate", str(scratch_plugin), "--strict"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
        )
        local = [f for f in _findings_for(scratch_plugin) if f.check == "FF-1"]
        assert host.returncode == 0, "host CLI now rejects non-semver versions; revisit the local check"
        assert local, "local gate must reject what the host CLI permits"


class TestCheckIdentifiers:
    """Guard the finding taxonomy the CI output and reports depend on."""

    def test_every_finding_carries_a_check_and_a_rule(self, scratch_plugin):
        """Findings are attributable, never anonymous."""
        (scratch_plugin / ".mcp.json").write_text('{"mcpServers": {}}', encoding="utf-8")
        (scratch_plugin / "hooks").mkdir()
        findings = _findings_for(scratch_plugin)
        assert findings
        for finding in findings:
            assert finding.check
            assert finding.rule
            assert finding.severity in ("CRITICAL", "ERROR")
            assert finding.message

    def test_both_critical_rules_can_fire_together(self, scratch_plugin):
        """A tree violating both ADRs reports both, not just the first."""
        (scratch_plugin / ".mcp.json").write_text('{"mcpServers": {}}', encoding="utf-8")
        (scratch_plugin / "hooks").mkdir()
        findings = _findings_for(scratch_plugin)
        assert {"ADR-010", "ADR-019"}.issubset(_rules(findings))
        assert {"FF-2", "FF-3"}.issubset(_checks(findings))

    def test_json_output_is_machine_readable(self):
        """The --json surface stays parseable for downstream consumers."""
        result = subprocess.run(
            [sys.executable, str(GATE_SCRIPT), "--json"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
        )
        payload = json.loads(result.stdout)
        assert payload["passed"] is True
        assert payload["findings"] == []
        assert payload["discovery_trace"][".mcp.json"] is False
        assert payload["discovery_trace"]["hooks/"] is False

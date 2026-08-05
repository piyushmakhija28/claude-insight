"""Tests for the pinned library snapshot, staleness check and release gate.

Covers SRS FR-29 / PRD FR-16 acceptance criteria:

1. The plugin functions on a machine with no ``claude-global-library`` checkout.
2. A staleness check against the library VERSION fires when the snapshot is
   behind.
3. The release script FAILS if ``CLAUDE_PLUGIN_DEV_MODE`` is set in the
   publishing environment.

Every check here has a companion negative test. A gate that cannot be shown to
fail proves nothing, and a staleness check that fires unconditionally is noise
rather than a signal, so both halves are asserted for AC 2 and AC 3.

The AC 3 tests drive ``scripts/tools/release.py`` as a SUBPROCESS, so the
assertion runs against the stored script exactly as a publishing environment
would invoke it, rather than against an in-process import of it.

No test writes to a real settings file. ``test_real_settings_files_untouched``
hashes both live settings files before and after exercising every operation in
this module and asserts the digests are unchanged.

Windows-safe: ASCII only.
"""

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
PLUGIN_DIR = REPO_ROOT / "plugin"
RELEASE_SCRIPT = SCRIPTS_DIR / "tools" / "release.py"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
if str(PLUGIN_DIR / "scripts") not in sys.path:
    sys.path.insert(0, str(PLUGIN_DIR / "scripts"))

import build_library_snapshot as bls  # noqa: E402
import snapshot_status as ss  # noqa: E402

DEV_MODE_ENV = "CLAUDE_PLUGIN_DEV_MODE"

REAL_SETTINGS_FILES = (
    Path.home() / ".claude" / "settings.json",
    REPO_ROOT / ".claude" / "settings.local.json",
)


def _digest(path):
    """Return the sha256 of a file, or a marker when it does not exist."""
    try:
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()
    except OSError:
        return "ABSENT"


def _clean_env(**overrides):
    """Return an environment copy with the dev-mode flag removed by default."""
    env = dict(os.environ)
    env.pop(DEV_MODE_ENV, None)
    for key, value in overrides.items():
        if value is None:
            env.pop(key, None)
        else:
            env[key] = value
    return env


def _make_library(root, version="1.2.3", agents=("alpha-agent", "beta-agent")):
    """Create a minimal but structurally faithful library checkout.

    Args:
        root: Directory to populate.
        version: Contents of the VERSION file.
        agents: Agent slugs to create catalogue records and personas for.

    Returns:
        Path: The library root.
    """
    root = Path(root)
    (root / "VERSION").parent.mkdir(parents=True, exist_ok=True)
    (root / "VERSION").write_text(version + "\n", encoding="utf-8")

    master = root / "knowledge-graph" / "_master"
    master.mkdir(parents=True, exist_ok=True)

    agent_records = []
    for index, name in enumerate(agents):
        agent_records.append(
            {
                "name": name,
                "id": "agent:{0}".format(name),
                "primary_home_kg": "demo-domain",
                "description": "Description for {0}".format(name),
                "role": "Role for {0}".format(name),
                "model": "sonnet",
                "mandatory_skills": ["demo-skill"],
                "optional_skills": [],
                "shared_across_count": index,
                "home_kgs": ["demo-domain"],
                "tools": ["Read", "Write"],
            }
        )
        persona = root / "agents" / name / "agent.md"
        persona.parent.mkdir(parents=True, exist_ok=True)
        persona.write_text("# {0}\n\nPersona body.\n".format(name), encoding="utf-8")

    _write(
        master / "agents_all.json",
        {"library_version": version, "kg_version": "1.0.0", "agent_count": len(agent_records), "agents": agent_records},
    )
    _write(
        master / "skills_all.json",
        {
            "library_version": version,
            "skills": [
                {
                    "name": "demo-skill",
                    "id": "skill:demo-skill",
                    "primary_home_kg": "demo-domain",
                    "description": "A demo skill.",
                }
            ],
        },
    )
    _write(
        master / "domains_all.json",
        {"library_version": version, "domains": [{"slug": "demo-domain", "name": "Demo Domain"}]},
    )
    _write(
        master / "edges_all.json",
        {
            "library_version": version,
            "edges": [
                {"source": "agent:alpha-agent", "target": "skill:demo-skill", "type": "uses"},
                {"source": "skill:demo-skill", "target": "domain:demo-domain", "type": "in"},
                {"source": "agent:beta-agent", "target": "skill:demo-skill", "type": "uses"},
            ],
        },
    )
    skill_file = root / "skills" / "demo-skill" / "SKILL.md"
    skill_file.parent.mkdir(parents=True, exist_ok=True)
    skill_file.write_text("# demo-skill\n", encoding="utf-8")
    return root


def _write(path, payload):
    """Write a JSON payload to disk."""
    Path(path).write_text(json.dumps(payload), encoding="utf-8")


def _make_plugin(root, snapshot_from=None, snapshot_version=None):
    """Create a plugin root, optionally carrying a snapshot.

    Args:
        root: Directory to populate.
        snapshot_from: Library root to build a snapshot from.
        snapshot_version: Override the pinned version in the manifest.

    Returns:
        Path: The plugin root.
    """
    root = Path(root)
    (root / ".claude-plugin").mkdir(parents=True, exist_ok=True)
    _write(
        root / ".claude-plugin" / "plugin.json",
        {"name": "demo", "version": "0.1.0", "description": "Fixture plugin for snapshot tests."},
    )
    (root / "commands").mkdir(exist_ok=True)
    if snapshot_from is not None:
        bls.build_snapshot(snapshot_from, root / "snapshot", plugin_root=root)
    if snapshot_version is not None:
        manifest_path = root / "snapshot" / "snapshot.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["library_version"] = snapshot_version
        _write(manifest_path, manifest)
    return root


# ---------------------------------------------------------------------------
# AC 3: the release script fails when dev mode is set
# ---------------------------------------------------------------------------


class TestAC3ReleaseGate:
    """The publishing gate, proven in both directions."""

    def _run_release(self, env):
        """Invoke the stored release script with --dry-run."""
        return subprocess.run(
            [sys.executable, str(RELEASE_SCRIPT), "--dry-run", "patch"],
            capture_output=True,
            text=True,
            env=env,
            cwd=str(REPO_ROOT),
        )

    def test_release_fails_when_dev_mode_set(self):
        """POSITIVE: the gate fires and the release script exits non-zero."""
        result = self._run_release(_clean_env(**{DEV_MODE_ENV: "1"}))
        assert result.returncode != 0, "release script exited 0 with dev mode set; the gate did not fire"
        assert "BLOCKED" in result.stdout
        assert DEV_MODE_ENV in result.stdout

    def test_release_proceeds_when_dev_mode_unset(self):
        """NEGATIVE: with the flag unset the same script runs to completion.

        Without this half the positive test above proves nothing: a script that
        always exits non-zero would pass it.
        """
        result = self._run_release(_clean_env())
        assert result.returncode == 0, "release script failed with dev mode unset: {0}".format(
            result.stdout + result.stderr
        )
        assert "DRY RUN" in result.stdout
        assert "BLOCKED" not in result.stdout

    def test_release_gate_runs_before_any_write(self):
        """The gate must precede the dry-run branch, so it cannot be skipped."""
        result = self._run_release(_clean_env(**{DEV_MODE_ENV: "1"}))
        assert "DRY RUN" not in result.stdout

    @pytest.mark.parametrize("value", ["1", "true", "TRUE", "yes", "on", "anything"])
    def test_truthy_spellings_block(self, value):
        """Any non-falsey spelling of the flag blocks the release."""
        with pytest.raises(bls.DevModeRelease):
            bls.assert_not_dev_mode(env={DEV_MODE_ENV: value})

    @pytest.mark.parametrize("value", ["0", "false", "no", "off", ""])
    def test_falsey_spellings_do_not_block(self, value):
        """NEGATIVE: explicit falsey spellings must not block."""
        bls.assert_not_dev_mode(env={DEV_MODE_ENV: value})

    def test_absent_flag_does_not_block(self):
        """NEGATIVE: an environment without the flag proceeds."""
        bls.assert_not_dev_mode(env={})

    def test_snapshot_build_refuses_in_dev_mode_under_release_flag(self, tmp_path):
        """The builder's own release path refuses too, not only release.py."""
        library = _make_library(tmp_path / "lib")
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS_DIR / "build_library_snapshot.py"),
                "--release",
                "--library",
                str(library),
                "--plugin-root",
                str(tmp_path / "plug"),
                "--out",
                str(tmp_path / "plug" / "snapshot"),
            ],
            capture_output=True,
            text=True,
            env=_clean_env(**{DEV_MODE_ENV: "1"}),
        )
        assert result.returncode != 0
        assert DEV_MODE_ENV in result.stdout

    def _publish_step(self):
        """Extract the guard command verbatim from the stored publish workflow.

        The assertion must run exactly as CI will run it, not as it was
        authored. An earlier revision of this step passed locally only because
        this machine has a library checkout the CI runner does not, which is
        precisely the correct-by-coincidence failure the extraction avoids.
        """
        workflow = (REPO_ROOT / ".github" / "workflows" / "publish.yml").read_text(encoding="utf-8")
        for line in workflow.splitlines():
            stripped = line.strip()
            if stripped.startswith("run:") and "build_library_snapshot.py" in stripped:
                return stripped[len("run:") :].strip().split()
        raise AssertionError("publish.yml carries no build_library_snapshot.py guard step")

    def test_stored_publish_step_blocks_dev_mode(self, tmp_path):
        """POSITIVE: the workflow's own command exits non-zero under dev mode."""
        command = self._publish_step()
        result = subprocess.run(
            [sys.executable] + command[1:],
            capture_output=True,
            text=True,
            env=_clean_env(**{DEV_MODE_ENV: "1"}),
            cwd=str(REPO_ROOT),
        )
        assert result.returncode != 0
        assert "BLOCKED" in result.stdout

    def test_stored_publish_step_passes_without_a_library(self, tmp_path):
        """NEGATIVE + library-free: it exits 0 on a runner with no library.

        A CI runner has no claude-global-library checkout. The guard must not
        depend on one, or the publish job fails for the wrong reason.
        """
        command = self._publish_step()
        workdir = tmp_path / "runner"
        (workdir / "scripts").mkdir(parents=True)
        (workdir / "scripts" / "build_library_snapshot.py").write_bytes(
            (REPO_ROOT / "scripts" / "build_library_snapshot.py").read_bytes()
        )
        result = subprocess.run(
            [sys.executable] + command[1:],
            capture_output=True,
            text=True,
            env=_clean_env(),
            cwd=str(workdir),
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert "not set" in result.stdout

    def test_manifest_records_dev_mode_build(self, tmp_path, monkeypatch):
        """A dev-mode build is tagged, so it can never be mistaken for pinned."""
        library = _make_library(tmp_path / "lib")
        monkeypatch.setenv(DEV_MODE_ENV, "1")
        manifest = bls.build_snapshot(library, tmp_path / "snap")
        assert manifest["built_in_dev_mode"] is True

    def test_manifest_records_clean_build(self, tmp_path, monkeypatch):
        """NEGATIVE: a normal build is not tagged dev."""
        library = _make_library(tmp_path / "lib")
        monkeypatch.delenv(DEV_MODE_ENV, raising=False)
        manifest = bls.build_snapshot(library, tmp_path / "snap")
        assert manifest["built_in_dev_mode"] is False


# ---------------------------------------------------------------------------
# AC 2: the staleness check
# ---------------------------------------------------------------------------


class TestAC2Staleness:
    """Staleness detection, with the specificity control that matters."""

    def test_fires_when_snapshot_behind(self, tmp_path):
        """POSITIVE: an older pinned version against a newer library fires."""
        library = _make_library(tmp_path / "lib", version="1.2.3")
        plugin = _make_plugin(tmp_path / "plug", snapshot_from=library, snapshot_version="1.0.0")
        outcome = ss.check_snapshot(plugin_root=plugin, library_root=library)
        assert outcome.status == ss.STATUS_BEHIND
        assert outcome.fires is True
        assert outcome.is_stale is True
        assert "1.0.0" in outcome.detail and "1.2.3" in outcome.detail

    def test_does_not_fire_when_current(self, tmp_path):
        """SPECIFICITY: a snapshot built from the live library must be silent.

        This is the control that makes the positive test meaningful. A check
        that fires unconditionally would pass the BEHIND test and be useless.
        """
        library = _make_library(tmp_path / "lib", version="1.2.3")
        plugin = _make_plugin(tmp_path / "plug", snapshot_from=library)
        outcome = ss.check_snapshot(plugin_root=plugin, library_root=library)
        assert outcome.status == ss.STATUS_CURRENT
        assert outcome.fires is False
        assert outcome.is_stale is False

    def test_does_not_fire_with_no_library(self, tmp_path):
        """SPECIFICITY: the normal installed condition must stay silent.

        An end user has no library checkout. If absence fired, every user would
        see a staleness warning on every invocation and would switch it off.
        """
        library = _make_library(tmp_path / "lib", version="1.2.3")
        plugin = _make_plugin(tmp_path / "plug", snapshot_from=library)
        outcome = ss.check_snapshot(plugin_root=plugin, library_root=tmp_path / "nonexistent")
        assert outcome.status == ss.STATUS_NO_LIBRARY
        assert outcome.fires is False
        assert outcome.is_stale is False
        assert outcome.snapshot_version == "1.2.3"

    def test_fires_when_snapshot_missing(self, tmp_path):
        """A plugin with no snapshot at all is a firing condition."""
        plugin = _make_plugin(tmp_path / "plug")
        outcome = ss.check_snapshot(plugin_root=plugin, library_root=tmp_path / "nope")
        assert outcome.status == ss.STATUS_NO_SNAPSHOT
        assert outcome.fires is True

    def test_fires_when_manifest_unreadable(self, tmp_path):
        """A corrupt manifest fires rather than being silently treated as fine."""
        library = _make_library(tmp_path / "lib")
        plugin = _make_plugin(tmp_path / "plug", snapshot_from=library)
        (plugin / "snapshot" / "snapshot.json").write_text("{not json", encoding="utf-8")
        outcome = ss.check_snapshot(plugin_root=plugin, library_root=library)
        assert outcome.status == ss.STATUS_UNREADABLE
        assert outcome.fires is True

    def test_detects_ahead(self, tmp_path):
        """A snapshot newer than the checkout is reported distinctly."""
        library = _make_library(tmp_path / "lib", version="1.0.0")
        plugin = _make_plugin(tmp_path / "plug", snapshot_from=library, snapshot_version="2.0.0")
        outcome = ss.check_snapshot(plugin_root=plugin, library_root=library)
        assert outcome.status == ss.STATUS_AHEAD
        assert outcome.fires is True

    @pytest.mark.parametrize(
        "pinned,live,expected",
        [
            ("29.73.0", "29.73.0", ss.STATUS_CURRENT),
            ("29.72.0", "29.73.0", ss.STATUS_BEHIND),
            ("29.73.0", "29.72.0", ss.STATUS_AHEAD),
            ("9.0.0", "10.0.0", ss.STATUS_BEHIND),
            ("29.73.0", "29.73.1", ss.STATUS_BEHIND),
        ],
    )
    def test_version_ordering_is_numeric_not_lexical(self, pinned, live, expected):
        """9.0.0 must sort below 10.0.0, which string comparison gets wrong."""
        assert ss.compare_versions(pinned, live) == expected

    def test_strict_exit_code_from_stored_script(self, tmp_path):
        """The stored checker exits non-zero under --strict when it fires."""
        library = _make_library(tmp_path / "lib", version="2.0.0")
        plugin = _make_plugin(tmp_path / "plug", snapshot_from=library, snapshot_version="1.0.0")
        command = [
            sys.executable,
            str(PLUGIN_DIR / "scripts" / "snapshot_status.py"),
            "--plugin-root",
            str(plugin),
            "--library",
            str(library),
            "--strict",
        ]
        stale = subprocess.run(command, capture_output=True, text=True, env=_clean_env())
        assert stale.returncode == 1
        assert "STALE" in stale.stdout

    def test_strict_exit_zero_when_current_from_stored_script(self, tmp_path):
        """NEGATIVE: the same stored invocation exits 0 when nothing is wrong."""
        library = _make_library(tmp_path / "lib", version="2.0.0")
        plugin = _make_plugin(tmp_path / "plug", snapshot_from=library)
        result = subprocess.run(
            [
                sys.executable,
                str(PLUGIN_DIR / "scripts" / "snapshot_status.py"),
                "--plugin-root",
                str(plugin),
                "--library",
                str(library),
                "--strict",
            ],
            capture_output=True,
            text=True,
            env=_clean_env(),
        )
        assert result.returncode == 0
        assert "CURRENT" in result.stdout


# ---------------------------------------------------------------------------
# AC 1: the plugin functions with no library checkout
# ---------------------------------------------------------------------------


class TestAC1Standalone:
    """The snapshot must be sufficient on a machine with no library."""

    def test_snapshot_drives_the_real_loader_with_no_library(self, tmp_path):
        """The production catalogue loader runs against the snapshot alone.

        The snapshot reproduces the library's relative layout exactly, so the
        real LocalSiblingAdapter can be pointed at it unchanged. Nothing here
        reads the library: it is built, then the path is abandoned.
        """
        from langgraph_engine.library.resolver import ChainedResourceResolver, HardFailAdapter, LocalSiblingAdapter
        from langgraph_engine.selection.catalogue import load_catalogue, verify_persona

        library = _make_library(tmp_path / "lib")
        snapshot = tmp_path / "snap"
        bls.build_snapshot(library, snapshot)

        resolver = ChainedResourceResolver([LocalSiblingAdapter(snapshot), HardFailAdapter(snapshot)])
        catalogue = load_catalogue(resolver)

        assert set(catalogue.agents) == {"alpha-agent", "beta-agent"}
        assert "demo-skill" in catalogue.skills
        assert "demo-domain" in catalogue.domains
        assert catalogue.library_version == "1.2.3"
        for record in catalogue.agents.values():
            assert verify_persona(resolver, record) == record.persona_relpath

    def test_snapshot_is_self_contained(self, tmp_path):
        """Deleting the library after the build leaves the snapshot usable."""
        import shutil

        from langgraph_engine.library.resolver import ChainedResourceResolver, HardFailAdapter, LocalSiblingAdapter
        from langgraph_engine.selection.catalogue import load_catalogue

        library = _make_library(tmp_path / "lib")
        snapshot = tmp_path / "snap"
        bls.build_snapshot(library, snapshot)
        shutil.rmtree(str(library))
        assert not library.exists()

        resolver = ChainedResourceResolver([LocalSiblingAdapter(snapshot), HardFailAdapter(snapshot)])
        catalogue = load_catalogue(resolver)
        assert len(catalogue.agents) == 2

    def test_projection_preserves_type_words(self, tmp_path):
        """The 3 MB edge catalogue projects without changing the vocabulary."""
        library = _make_library(tmp_path / "lib")
        snapshot = tmp_path / "snap"
        bls.build_snapshot(library, snapshot)
        assert bls.verify_snapshot_fidelity(library, snapshot) == []

    def test_agents_without_personas_are_excluded(self, tmp_path):
        """A catalogued agent with no persona file is not snapshotted."""
        library = _make_library(tmp_path / "lib")
        (library / "agents" / "beta-agent" / "agent.md").unlink()
        manifest = bls.build_snapshot(library, tmp_path / "snap")
        assert manifest["agent_count"] == 1
        assert manifest["skipped_agents"] == ["beta-agent"]

    def test_build_refuses_when_no_persona_resolves(self, tmp_path):
        """An empty snapshot is refused rather than silently shipped."""
        library = _make_library(tmp_path / "lib")
        for name in ("alpha-agent", "beta-agent"):
            (library / "agents" / name / "agent.md").unlink()
        with pytest.raises(bls.LibraryUnavailable):
            bls.build_snapshot(library, tmp_path / "snap")

    def test_missing_library_raises(self, tmp_path):
        """A missing library is a typed error naming the paths tried."""
        with pytest.raises(bls.LibraryUnavailable) as excinfo:
            bls.locate_library_root(tmp_path / "absent", tmp_path)
        assert "VERSION" in str(excinfo.value)

    def test_build_is_deterministic(self, tmp_path):
        """Two builds of one library produce byte-identical catalogues."""
        library = _make_library(tmp_path / "lib")
        first = bls.build_snapshot(library, tmp_path / "a")
        second = bls.build_snapshot(library, tmp_path / "b")
        assert first["files"] == second["files"]


# ---------------------------------------------------------------------------
# Plugin conformance interaction
# ---------------------------------------------------------------------------


class TestPluginConstraints:
    """The snapshot must not break the ADR-019 conformance gate."""

    def test_rejects_snapshot_at_a_discovered_capability_name(self, tmp_path):
        """Writing personas to plugin/agents/ would publish them as subagents."""
        plugin = tmp_path / "plug"
        (plugin / "agents").mkdir(parents=True)
        with pytest.raises(bls.SnapshotError) as excinfo:
            bls.assert_not_discovered(plugin / "agents", plugin)
        assert "discovered" in str(excinfo.value)

    def test_accepts_snapshot_at_a_non_discovered_name(self, tmp_path):
        """NEGATIVE: the chosen 'snapshot' name is accepted."""
        plugin = tmp_path / "plug"
        (plugin / "snapshot").mkdir(parents=True)
        bls.assert_not_discovered(plugin / "snapshot", plugin)

    def test_detects_a_bundled_mcp_config(self, tmp_path):
        """A library that ever adds .mcp.json must fail the build, loudly."""
        snapshot = tmp_path / "snap"
        (snapshot / "nested").mkdir(parents=True)
        (snapshot / "nested" / ".mcp.json").write_text("{}", encoding="utf-8")
        with pytest.raises(bls.SnapshotError) as excinfo:
            bls.assert_no_bundled_server_config(snapshot)
        assert "ADR-019" in str(excinfo.value)

    def test_clean_snapshot_passes_the_server_config_check(self, tmp_path):
        """NEGATIVE: a real built snapshot carries no server configuration."""
        library = _make_library(tmp_path / "lib")
        snapshot = tmp_path / "snap"
        bls.build_snapshot(library, snapshot)
        bls.assert_no_bundled_server_config(snapshot)

    def test_built_snapshot_leaves_conformance_gate_passing(self, tmp_path):
        """The stored conformance gate still passes with a snapshot present."""
        library = _make_library(tmp_path / "lib")
        plugin = _make_plugin(tmp_path / "plug", snapshot_from=library)
        result = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "verify_plugin_conformance.py"), "--plugin-root", str(plugin)],
            capture_output=True,
            text=True,
            env=_clean_env(),
        )
        assert result.returncode == 0, result.stdout + result.stderr


# ---------------------------------------------------------------------------
# Safety: the live settings files are never touched
# ---------------------------------------------------------------------------


def test_real_settings_files_untouched(tmp_path):
    """Prove this module's operations never move a live settings file.

    Hashes both real settings files, exercises the release gate, a snapshot
    build and a staleness check, then re-hashes. Any write would change a
    digest.
    """
    before = {str(path): _digest(path) for path in REAL_SETTINGS_FILES}

    subprocess.run(
        [sys.executable, str(RELEASE_SCRIPT), "--dry-run", "patch"],
        capture_output=True,
        text=True,
        env=_clean_env(**{DEV_MODE_ENV: "1"}),
        cwd=str(REPO_ROOT),
    )
    library = _make_library(tmp_path / "lib")
    plugin = _make_plugin(tmp_path / "plug", snapshot_from=library)
    ss.check_snapshot(plugin_root=plugin, library_root=library)

    after = {str(path): _digest(path) for path in REAL_SETTINGS_FILES}
    assert before == after, "a live settings file changed: {0} -> {1}".format(before, after)

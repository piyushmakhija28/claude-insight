"""Tests for register-mcp / unregister-mcp (SRS FR-37, issue V2-016).

Every assertion here runs against a temporary settings file. The real
``~/.claude/settings.json`` and the repository's git-tracked
``.claude/settings.local.json`` are digested once at session start and again at
session end, and a change to either fails the suite loudly rather than being
absorbed as incidental.

Three properties are proved separately because they are three different claims:

- REVERSIBILITY - unregister removes exactly what register added.
- ROUND TRIP - a capability flips unreachable -> reachable -> unreachable.
- BYTE-IDENTICAL RESTORATION - deliberately NOT claimed, and the test that
  measures it records that it does not hold for arbitrary input formatting.

Reachability is MEASURED, not asserted. The round-trip test reads the entry back
out of the settings file, spawns exactly the process that entry names, and
completes a real JSON-RPC lifecycle handshake against it. Asserting that
register-mcp wrote what register-mcp wrote would prove nothing.
"""

import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = REPO_ROOT / "plugin"
SCRIPT_DIR = PLUGIN_ROOT / "scripts"
REGISTRATION_SCRIPT = SCRIPT_DIR / "mcp_registration.py"
GATE_SCRIPT = REPO_ROOT / "scripts" / "verify_plugin_conformance.py"
PROBE_SERVER = Path(__file__).resolve().parent / "fixtures" / "reachability_mcp_server.py"

REAL_USER_SETTINGS = Path.home() / ".claude" / "settings.json"
REAL_PROJECT_SETTINGS = REPO_ROOT / ".claude" / "settings.local.json"


def _load(name, path):
    """Import a module by explicit file path.

    ``plugin/scripts`` is not an importable package, so both modules under test
    are loaded by location rather than by name.

    Args:
        name: Module name to register under.
        path: Filesystem path of the module.

    Returns:
        module: The loaded module.
    """
    if str(SCRIPT_DIR) not in sys.path:
        sys.path.insert(0, str(SCRIPT_DIR))
    spec = importlib.util.spec_from_file_location(name, str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


store = _load("settings_store", SCRIPT_DIR / "settings_store.py")
registration = _load("mcp_registration", REGISTRATION_SCRIPT)


def _digest(path):
    """Return the sha256 of a file, or a marker when it is absent.

    Args:
        path: File to digest.

    Returns:
        str: Hex digest, or "ABSENT".
    """
    try:
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()
    except FileNotFoundError:
        return "ABSENT"


@pytest.fixture(scope="module", autouse=True)
def real_settings_are_never_touched():
    """Fail the module if either real settings file changes while it runs.

    Constraint 2 of this issue: no test may write to a live configuration file.
    This fixture is the mechanical proof of that, not a promise about it.

    Yields:
        None
    """
    before = {
        str(REAL_USER_SETTINGS): _digest(REAL_USER_SETTINGS),
        str(REAL_PROJECT_SETTINGS): _digest(REAL_PROJECT_SETTINGS),
    }
    yield
    after = {
        str(REAL_USER_SETTINGS): _digest(REAL_USER_SETTINGS),
        str(REAL_PROJECT_SETTINGS): _digest(REAL_PROJECT_SETTINGS),
    }
    assert before == after, "a test modified a real settings file: {0} -> {1}".format(before, after)


@pytest.fixture()
def settings_file(tmp_path):
    """Create a scratch settings file with representative unrelated content.

    The unrelated keys exist so that any test asserting they survived is
    asserting something real. A settings file containing only ``mcpServers``
    could not distinguish a merge from a clobber.

    Args:
        tmp_path: pytest-provided temporary directory.

    Returns:
        Path: The scratch settings file.
    """
    path = tmp_path / "settings.json"
    path.write_text(
        json.dumps(
            {
                "model": "opus",
                "hooks": {
                    "PreToolUse": [{"matcher": "*", "hooks": []}],
                    "Stop": [{"matcher": "*", "hooks": []}],
                },
                "mcpServers": {
                    "pre-existing-unrelated": {
                        "command": "python",
                        "args": ["elsewhere.py"],
                        "env": {},
                    }
                },
                "permissions": {"allow": ["Read"]},
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return path


@pytest.fixture()
def server_root(tmp_path):
    """Build a scratch server root whose progress-writer entry really runs.

    The probe server is copied to the exact repo/entry location the catalogue
    declares, so the path register-mcp writes is a path that genuinely spawns.

    Args:
        tmp_path: pytest-provided temporary directory.

    Returns:
        Path: Directory holding the mcp-* checkouts.
    """
    root = tmp_path / "servers"
    target = root / "mcp-post-tool-tracker"
    target.mkdir(parents=True)
    (target / "server.py").write_text(PROBE_SERVER.read_text(encoding="utf-8"), encoding="utf-8")
    return root


@pytest.fixture()
def ledger_file(tmp_path):
    """Return the scratch provenance ledger path.

    Args:
        tmp_path: pytest-provided temporary directory.

    Returns:
        Path: Ledger path inside the scratch directory.
    """
    return tmp_path / "cwe-mcp-registrations.json"


def _run_cli(args, settings, ledger):
    """Invoke the registration CLI in-process against scratch paths.

    Args:
        args: Subcommand and flag strings.
        settings: Scratch settings path.
        ledger: Scratch ledger path.

    Returns:
        int: The CLI exit status.
    """
    return registration.main(
        [
            "--plugin-root",
            str(PLUGIN_ROOT),
            "--settings",
            str(settings),
            "--ledger",
            str(ledger),
        ]
        + args
    )


def _spawn_and_handshake(entry, skip_initialized=False):
    """Spawn a server entry and run the MCP lifecycle handshake against it.

    Args:
        entry: The settings mcpServers entry to spawn, verbatim.
        skip_initialized: When True, send tools/list without the initialized
            notification, to exercise the lifecycle gate.

    Returns:
        dict: The parsed response to tools/list.
    """
    command = [entry["command"]] + list(entry["args"])
    if Path(command[0]).name.lower().startswith("python"):
        command[0] = sys.executable
    process = subprocess.Popen(
        command,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
    )
    lines = [
        json.dumps(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {"protocolVersion": "2025-06-18"},
            }
        ),
    ]
    if not skip_initialized:
        lines.append(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}))
    lines.append(json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list"}))
    stdout, _stderr = process.communicate("\n".join(lines) + "\n", timeout=60)
    responses = [json.loads(line) for line in stdout.splitlines() if line.strip()]
    for response in responses:
        if response.get("id") == 2:
            return response
    raise AssertionError("server produced no answer to tools/list: {0}".format(stdout))


def _capability_reachable(settings_path, capability):
    """Decide reachability by spawning what the settings file actually names.

    This never consults the ledger and never consults the value the caller
    wrote. It reads the file, finds the entry for the capability's server, and
    proves the server answers.

    Args:
        settings_path: Settings file to read.
        capability: Capability name from the catalogue.

    Returns:
        bool: True when a tool was listed by the spawned server.
    """
    settings = json.loads(Path(settings_path).read_text(encoding="utf-8"))
    catalogue = registration.load_registry(PLUGIN_ROOT)
    server_id = next(item["id"] for item in catalogue if item["capability"] == capability)
    entry = settings.get("mcpServers", {}).get(server_id)
    if entry is None:
        return False
    response = _spawn_and_handshake(entry)
    return bool(response.get("result", {}).get("tools"))


class TestWriteSafety:
    """The merge-against-fresh-read contract, with its failure modes proved."""

    def test_merge_preserves_a_key_written_after_the_base_read(self, settings_file):
        """AC 1 positive: a competing write inside the window is not lost.

        The merge function mutates the file on disk, simulating a second writer
        whose change lands after this writer's base read. A naive full-file
        read-modify-write would drop that key. The retry cycle keeps it.
        """
        calls = []

        def merge(current):
            """Insert our key, and on the first pass perturb the file on disk.

            Args:
                current: Freshly read settings object.

            Returns:
                dict: The object to write.
            """
            calls.append(1)
            if len(calls) == 1:
                other = json.loads(settings_file.read_text(encoding="utf-8"))
                other["writtenByCompetingWriter"] = True
                settings_file.write_text(json.dumps(other, indent=2) + "\n", encoding="utf-8")
            current.setdefault("mcpServers", {})["ours"] = {
                "command": "python",
                "args": [],
                "env": {},
            }
            return current

        result = store.merge_write(settings_file, merge)
        final = json.loads(settings_file.read_text(encoding="utf-8"))

        assert result.changed is True
        assert result.attempts == 2
        assert final["writtenByCompetingWriter"] is True
        assert "ours" in final["mcpServers"]
        assert final["model"] == "opus"

    def test_specificity_uncontended_write_takes_exactly_one_attempt(self, settings_file):
        """Specificity: the retry machinery does not fire on ordinary input.

        A check that retries or rejects unconditionally has no discriminating
        power. With no competing writer the cycle must complete on attempt one.
        """

        def merge(current):
            """Add one key and nothing else.

            Args:
                current: Freshly read settings object.

            Returns:
                dict: The object to write.
            """
            current["addedQuietly"] = True
            return current

        result = store.merge_write(settings_file, merge)

        assert result.attempts == 1
        assert result.changed is True
        assert json.loads(settings_file.read_text(encoding="utf-8"))["addedQuietly"] is True

    def test_negative_unrelenting_competing_writer_aborts_without_writing(self, settings_file):
        """Negative: the concurrency check can fail, and fails without writing."""
        original = settings_file.read_bytes()

        def merge(current):
            """Perturb the file on every pass so no attempt can verify.

            Args:
                current: Freshly read settings object.

            Returns:
                dict: The object that will never be written.
            """
            other = json.loads(settings_file.read_text(encoding="utf-8"))
            other["churn"] = other.get("churn", 0) + 1
            settings_file.write_text(json.dumps(other, indent=2) + "\n", encoding="utf-8")
            current["neverLands"] = True
            return current

        with pytest.raises(store.ConcurrentModification):
            store.merge_write(settings_file, merge, attempts=3)

        assert b"neverLands" not in settings_file.read_bytes()
        assert original != settings_file.read_bytes()

    def test_negative_unparseable_settings_are_refused_not_defaulted(self, tmp_path):
        """Negative: the ADV-008 clobber is refused rather than performed.

        This is the specific behaviour that made AtomicJsonStore unusable here.
        Its load() would substitute a default for an unparseable file and its
        save() would then write that default over the user's configuration.
        """
        broken = tmp_path / "settings.json"
        broken.write_text('{"model": "opus",}', encoding="utf-8")
        before = broken.read_bytes()

        with pytest.raises(store.SettingsUnreadable):
            store.merge_write(broken, lambda current: {"replaced": True})

        assert broken.read_bytes() == before

    def test_specificity_a_missing_file_is_created_rather_than_refused(self, tmp_path):
        """Specificity: absence is the one case where an empty base is correct."""
        fresh = tmp_path / "nested" / "settings.json"

        result = store.merge_write(fresh, lambda current: dict(current, model="opus"))

        assert result.changed is True
        assert result.digest_before is None
        assert json.loads(fresh.read_text(encoding="utf-8")) == {"model": "opus"}

    def test_a_merge_producing_no_change_writes_nothing(self, settings_file):
        """An identical merge must not churn the file's bytes."""
        before = settings_file.read_bytes()

        result = store.merge_write(settings_file, lambda current: current)

        assert result.changed is False
        assert settings_file.read_bytes() == before

    def test_no_scratch_file_survives_the_write(self, settings_file):
        """Temp files are unique and are consumed by the rename."""
        store.merge_write(settings_file, lambda current: dict(current, touched=True))

        leftovers = [p.name for p in settings_file.parent.iterdir() if p.name != settings_file.name]
        assert leftovers == [], leftovers


class TestRegisterUnregister:
    """AC 1, AC 2 and AC 3 against a scratch settings file."""

    def test_register_writes_only_the_mcpservers_block(self, settings_file, server_root, ledger_file):
        """AC 1: registration is a merge, not a replacement."""
        before = json.loads(settings_file.read_text(encoding="utf-8"))

        status = _run_cli(["register", "--server-root", str(server_root)], settings_file, ledger_file)
        after = json.loads(settings_file.read_text(encoding="utf-8"))

        assert status == registration.EXIT_OK
        assert after["model"] == before["model"]
        assert after["hooks"] == before["hooks"]
        assert after["permissions"] == before["permissions"]
        assert after["mcpServers"]["pre-existing-unrelated"] == before["mcpServers"]["pre-existing-unrelated"]
        assert "post-tool-tracker" in after["mcpServers"]

    def test_a_server_with_no_entry_point_is_skipped_not_written(self, settings_file, server_root, ledger_file):
        """A capability whose server does not exist must not be registered.

        The push gate is V2-024's deliverable and does not exist. Writing an
        entry for it would present a missing capability as a working one, which
        is the exact defect ADR-019's item 3 forbids.
        """
        _run_cli(["register", "--server-root", str(server_root)], settings_file, ledger_file)
        after = json.loads(settings_file.read_text(encoding="utf-8"))

        assert "push-gate" not in after["mcpServers"]

    def test_unregister_removes_only_what_register_added(self, settings_file, server_root, ledger_file):
        """AC 2: reversibility is scoped by provenance, not by pattern match."""
        _run_cli(["register", "--server-root", str(server_root)], settings_file, ledger_file)
        _run_cli(["unregister"], settings_file, ledger_file)
        after = json.loads(settings_file.read_text(encoding="utf-8"))

        assert "post-tool-tracker" not in after["mcpServers"]
        assert "pre-existing-unrelated" in after["mcpServers"]

    def test_negative_unregister_will_not_claim_an_entry_it_did_not_write(
        self, settings_file, server_root, ledger_file
    ):
        """Negative: an entry registered by another route survives unregister.

        The catalogue knows the name ``post-tool-tracker``, so a name-matching
        implementation would delete it. Provenance is what prevents that.
        """
        settings = json.loads(settings_file.read_text(encoding="utf-8"))
        settings["mcpServers"]["post-tool-tracker"] = {
            "command": "python",
            "args": ["someone-elses.py"],
            "env": {},
        }
        settings_file.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")

        _run_cli(["unregister"], settings_file, ledger_file)
        after = json.loads(settings_file.read_text(encoding="utf-8"))

        assert after["mcpServers"]["post-tool-tracker"]["args"] == ["someone-elses.py"]

    def test_register_leaves_a_foreign_entry_alone_without_force(self, settings_file, server_root, ledger_file):
        """An entry this command did not write is not silently overwritten."""
        settings = json.loads(settings_file.read_text(encoding="utf-8"))
        settings["mcpServers"]["post-tool-tracker"] = {
            "command": "python",
            "args": ["someone-elses.py"],
            "env": {},
        }
        settings_file.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")

        _run_cli(["register", "--server-root", str(server_root)], settings_file, ledger_file)
        after = json.loads(settings_file.read_text(encoding="utf-8"))

        assert after["mcpServers"]["post-tool-tracker"]["args"] == ["someone-elses.py"]

    def test_round_trip_restores_the_object_but_not_necessarily_the_bytes(self, tmp_path, server_root, ledger_file):
        """Three claims measured separately, and one of them reported false.

        Object equality after a round trip holds. Byte equality holds only when
        the file was already formatted the way this command serialises. The
        second case is measured here rather than rounded to "restored".
        """
        four_space = tmp_path / "settings.json"
        four_space.write_text(
            json.dumps({"model": "opus", "hooks": {"PreToolUse": [{"matcher": "*"}]}}, indent=4) + "\n",
            encoding="utf-8",
        )
        original_bytes = four_space.read_bytes()
        original_object = json.loads(four_space.read_text(encoding="utf-8"))

        _run_cli(["register", "--server-root", str(server_root)], four_space, ledger_file)
        _run_cli(["unregister"], four_space, ledger_file)

        assert json.loads(four_space.read_text(encoding="utf-8")) == original_object
        assert four_space.read_bytes() != original_bytes

    def test_round_trip_is_byte_identical_when_formatting_already_matches(
        self, settings_file, server_root, ledger_file
    ):
        """The byte-identical case, stated as the conditional it actually is."""
        original_bytes = settings_file.read_bytes()

        _run_cli(["register", "--server-root", str(server_root)], settings_file, ledger_file)
        _run_cli(["unregister"], settings_file, ledger_file)

        assert settings_file.read_bytes() == original_bytes

    def test_crlf_line_endings_survive_a_round_trip(self, tmp_path, server_root, ledger_file):
        """A CRLF settings file is not silently normalised to LF.

        The first version of this writer emitted LF unconditionally, which
        rewrote every line of a CRLF file to change two keys. Caught by the
        byte-identical test above on Windows, and fixed rather than excused.
        """
        crlf = tmp_path / "settings.json"
        body = json.dumps({"model": "opus", "hooks": {"PreToolUse": [{"matcher": "*"}]}}, indent=2) + "\n"
        crlf.write_bytes(body.replace("\n", "\r\n").encode("utf-8"))
        original_bytes = crlf.read_bytes()

        _run_cli(["register", "--server-root", str(server_root)], crlf, ledger_file)
        after_register = crlf.read_bytes()
        _run_cli(["unregister"], crlf, ledger_file)

        assert b"\r\n" in after_register
        assert after_register.count(b"\n") == after_register.count(b"\r\n")
        assert crlf.read_bytes() == original_bytes


class TestForceIsReversibleToo:
    """AC 2 on the --force path, where reversal means restore, not delete.

    The first implementation of this command recorded a ``pre_existing`` flag it
    never read and then deleted the name on unregister, so ``register --force``
    followed by ``unregister`` destroyed whatever entry the user already had
    under that name. The command was described as reversible throughout. These
    tests exist because that gap was found by probing --force directly rather
    than by reading the reversibility test, which only covered the path where
    nothing was displaced.
    """

    @staticmethod
    def _plant_foreign_entry(settings_file):
        """Put a user-owned entry under a name the catalogue also knows.

        Args:
            settings_file: Scratch settings path.

        Returns:
            dict: The entry that was planted.
        """
        entry = {
            "command": "node",
            "args": ["/the/users/own/server.js"],
            "env": {"USER_KEY": "important"},
        }
        settings = json.loads(settings_file.read_text(encoding="utf-8"))
        settings["mcpServers"]["post-tool-tracker"] = entry
        settings_file.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
        return entry

    def test_force_then_unregister_restores_the_displaced_entry(self, settings_file, server_root, ledger_file):
        """AC 2: taking ownership is reversible, so the original comes back."""
        original = self._plant_foreign_entry(settings_file)

        _run_cli(
            ["register", "--server-root", str(server_root), "--force"],
            settings_file,
            ledger_file,
        )
        after_register = json.loads(settings_file.read_text(encoding="utf-8"))
        _run_cli(["unregister"], settings_file, ledger_file)
        after_unregister = json.loads(settings_file.read_text(encoding="utf-8"))

        assert after_register["mcpServers"]["post-tool-tracker"] != original
        assert after_unregister["mcpServers"]["post-tool-tracker"] == original

    def test_specificity_a_registration_that_displaced_nothing_is_reversed_by_removal(
        self, settings_file, server_root, ledger_file
    ):
        """Specificity: restore must not fire where there was nothing to restore.

        An implementation that always re-created the name would leave a stale
        entry behind on the ordinary path and would pass the test above.
        """
        _run_cli(
            ["register", "--server-root", str(server_root), "--force"],
            settings_file,
            ledger_file,
        )
        _run_cli(["unregister"], settings_file, ledger_file)
        after = json.loads(settings_file.read_text(encoding="utf-8"))

        assert "post-tool-tracker" not in after["mcpServers"]
        assert "pre-existing-unrelated" in after["mcpServers"]

    def test_re_forcing_a_second_time_does_not_overwrite_the_recorded_original(
        self, settings_file, server_root, ledger_file, tmp_path
    ):
        """The displaced spec recorded is the user's, not our own previous one.

        A second --force run sees OUR entry sitting under the name. Recording
        that as the thing to restore would quietly replace the user's original
        with a copy of ours, which looks like a successful restore and is not.
        """
        original = self._plant_foreign_entry(settings_file)

        _run_cli(
            ["register", "--server-root", str(server_root), "--force"],
            settings_file,
            ledger_file,
        )
        moved_root = tmp_path / "servers-moved"
        (moved_root / "mcp-post-tool-tracker").mkdir(parents=True)
        (moved_root / "mcp-post-tool-tracker" / "server.py").write_text(
            PROBE_SERVER.read_text(encoding="utf-8"), encoding="utf-8"
        )
        _run_cli(
            ["register", "--server-root", str(moved_root), "--force"],
            settings_file,
            ledger_file,
        )
        _run_cli(["unregister"], settings_file, ledger_file)
        after = json.loads(settings_file.read_text(encoding="utf-8"))

        assert after["mcpServers"]["post-tool-tracker"] == original

    def test_re_registering_from_a_moved_server_root_still_reverses_by_removal(
        self, settings_file, server_root, ledger_file, tmp_path
    ):
        """Our own superseded entry must never be mistaken for the user's.

        Registering twice from different server roots replaces our own entry.
        Nothing of the user's was displaced, so unregister must still remove the
        name. Recording our superseded spec as ``displaced`` would instead leave
        a dangling registration pointing at the old checkout after the user had
        asked for it to be gone - an unregister that does not unregister.
        """
        _run_cli(["register", "--server-root", str(server_root)], settings_file, ledger_file)
        moved_root = tmp_path / "servers-elsewhere"
        (moved_root / "mcp-post-tool-tracker").mkdir(parents=True)
        (moved_root / "mcp-post-tool-tracker" / "server.py").write_text(
            PROBE_SERVER.read_text(encoding="utf-8"), encoding="utf-8"
        )
        _run_cli(["register", "--server-root", str(moved_root)], settings_file, ledger_file)
        ledger = json.loads(ledger_file.read_text(encoding="utf-8"))["registered"]
        _run_cli(["unregister"], settings_file, ledger_file)
        after = json.loads(settings_file.read_text(encoding="utf-8"))

        assert "displaced" not in ledger["post-tool-tracker"]
        assert "post-tool-tracker" not in after["mcpServers"]
        assert "pre-existing-unrelated" in after["mcpServers"]

    def test_the_ledger_records_the_displaced_spec_rather_than_a_bare_flag(
        self, settings_file, server_root, ledger_file
    ):
        """A boolean cannot restore anything; the spec itself must be kept."""
        original = self._plant_foreign_entry(settings_file)

        _run_cli(
            ["register", "--server-root", str(server_root), "--force"],
            settings_file,
            ledger_file,
        )
        ledger = json.loads(ledger_file.read_text(encoding="utf-8"))["registered"]

        assert ledger["post-tool-tracker"]["displaced"] == original


class TestTheWriteIsActuallyAtomic:
    """The rename-into-place claim, discriminated from a plain in-place write.

    Mutating ``os.replace`` into ``target.write_bytes`` was the one mutation the
    inherited suite did not catch: every assertion it makes about the resulting
    file holds equally for a non-atomic write. Atomic rename does not solve the
    lost-update race and is not claimed to, but it does guarantee no reader ever
    sees a half-written settings file, and that property needs its own test.
    """

    def test_the_new_content_lands_by_renaming_a_sibling_temp_file(self, settings_file, monkeypatch):
        """os.replace is called with a temp path in the destination directory."""
        calls = []
        real_replace = store.os.replace

        def recording_replace(src, dst):
            """Record the rename, then perform it.

            Args:
                src: Temp file path.
                dst: Destination path.
            """
            calls.append((str(src), str(dst)))
            return real_replace(src, dst)

        monkeypatch.setattr(store.os, "replace", recording_replace)
        store.merge_write(settings_file, lambda current: dict(current, landed=True))

        assert len(calls) == 1, calls
        source, destination = calls[0]
        assert destination == str(settings_file)
        assert source != str(settings_file)
        assert Path(source).parent == settings_file.parent
        assert json.loads(settings_file.read_text(encoding="utf-8"))["landed"] is True

    def test_negative_a_failing_rename_damages_nothing_and_leaves_no_scratch_file(self, settings_file, monkeypatch):
        """The failure path is loud, non-destructive and self-cleaning.

        Induced portably here. The Windows-specific cause that actually triggers
        it is measured in the next test.
        """
        before = settings_file.read_bytes()

        def failing_replace(src, dst):
            """Fail the way a Windows sharing violation fails.

            Args:
                src: Temp file path.
                dst: Destination path.
            """
            raise OSError(5, "Access is denied")

        monkeypatch.setattr(store.os, "replace", failing_replace)

        with pytest.raises(store.SettingsWriteError):
            store.merge_write(settings_file, lambda current: dict(current, x=True))

        assert settings_file.read_bytes() == before
        leftovers = [p.name for p in settings_file.parent.iterdir() if p.name != settings_file.name]
        assert leftovers == [], leftovers

    @pytest.mark.skipif(sys.platform != "win32", reason="rename-under-open-handle is Windows semantics")
    def test_an_open_handle_on_the_target_blocks_the_rename_measurably(self, settings_file):
        """Measured Windows behaviour, not assumed.

        On Windows another process merely holding the settings file open for
        reading - an editor, a tail - is enough to fail the rename. The command
        must surface that as a refusal with the file intact, never as a partial
        write. This is asserted rather than reasoned about because the answer is
        platform-specific and this is the platform.
        """
        before = settings_file.read_bytes()

        with open(str(settings_file), "r", encoding="utf-8"):
            with pytest.raises(store.SettingsWriteError) as caught:
                store.merge_write(settings_file, lambda current: dict(current, x=True))

        assert "could not replace" in str(caught.value)
        assert settings_file.read_bytes() == before
        leftovers = [p.name for p in settings_file.parent.iterdir() if p.name != settings_file.name]
        assert leftovers == [], leftovers


class TestConcurrencyAgainstARealSecondProcess:
    """The competing writer is a separate OS process, not a callback.

    The write-safety tests above simulate contention from inside the merge
    function, which runs in this process and cannot exercise the file-sharing
    behaviour that a real second writer does. This does.
    """

    def test_a_second_process_writing_inside_the_window_is_not_lost(self, settings_file, tmp_path):
        """M5's lost update, attempted for real, and detected rather than lost."""
        writer = tmp_path / "competing_writer.py"
        writer.write_text(
            "import json, sys, time\n"
            "from pathlib import Path\n"
            "target = Path(sys.argv[1])\n"
            "time.sleep(0.15)\n"
            "data = json.loads(target.read_text(encoding='utf-8'))\n"
            "data['writtenByAnotherProcess'] = True\n"
            "target.write_text(json.dumps(data, indent=2) + '\\n', encoding='utf-8')\n",
            encoding="utf-8",
        )
        process = subprocess.Popen([sys.executable, str(writer), str(settings_file)])
        calls = []

        def slow_merge(current):
            """Hold the window open long enough for the other process to land.

            Args:
                current: Freshly read settings object.

            Returns:
                dict: The object to write.
            """
            calls.append(1)
            if len(calls) == 1:
                time.sleep(0.6)
            current.setdefault("mcpServers", {})["ours"] = {
                "command": "python",
                "args": [],
                "env": {},
            }
            return current

        try:
            result = store.merge_write(settings_file, slow_merge)
        finally:
            process.wait(timeout=60)

        final = json.loads(settings_file.read_text(encoding="utf-8"))

        assert result.attempts >= 2, "the competing write was never observed"
        assert final["writtenByAnotherProcess"] is True
        assert "ours" in final["mcpServers"]
        assert final["model"] == "opus"


class TestReachabilityIsMeasured:
    """AC 3: reachability proved by spawning what the settings file names."""

    def test_capability_flips_unreachable_reachable_unreachable(self, settings_file, server_root, ledger_file):
        """The full round trip, with each state established by a real spawn."""
        assert _capability_reachable(settings_file, "progress-writer") is False

        _run_cli(["register", "--server-root", str(server_root)], settings_file, ledger_file)
        assert _capability_reachable(settings_file, "progress-writer") is True

        _run_cli(["unregister"], settings_file, ledger_file)
        assert _capability_reachable(settings_file, "progress-writer") is False

    def test_negative_the_probe_can_report_unreachable_for_a_broken_entry(self, settings_file, tmp_path):
        """Negative: the reachability probe is capable of returning False.

        A probe that always answers True would make the round-trip test above
        vacuous. This plants an entry pointing at a file that does not exist and
        requires the spawn to fail.
        """
        settings = json.loads(settings_file.read_text(encoding="utf-8"))
        settings["mcpServers"]["post-tool-tracker"] = {
            "command": "python",
            "args": [(tmp_path / "does-not-exist.py").as_posix()],
            "env": {},
        }
        settings_file.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")

        with pytest.raises(AssertionError):
            _capability_reachable(settings_file, "progress-writer")

    def test_the_probe_server_enforces_the_lifecycle_gate(self, settings_file, server_root, ledger_file):
        """A tools/list before initialized is answered with a protocol error.

        The handshake is a gate, so a server that helpfully answers early is
        violating the protocol even when the answer would be correct.
        """
        _run_cli(["register", "--server-root", str(server_root)], settings_file, ledger_file)
        settings = json.loads(settings_file.read_text(encoding="utf-8"))
        entry = settings["mcpServers"]["post-tool-tracker"]

        response = _spawn_and_handshake(entry, skip_initialized=True)

        assert "error" in response
        assert "result" not in response


class TestAdr020RefusalLayer:
    """ADR-020 layer 1: prevention where the plugin owns the action."""

    def test_unregister_refuses_when_no_pretooluse_remains(self, settings_file, server_root, ledger_file):
        """Refusal, with the settings file left untouched."""
        _run_cli(["register", "--server-root", str(server_root)], settings_file, ledger_file)
        settings = json.loads(settings_file.read_text(encoding="utf-8"))
        del settings["hooks"]["PreToolUse"]
        settings_file.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
        before = settings_file.read_bytes()

        status = _run_cli(["unregister"], settings_file, ledger_file)

        assert status == registration.EXIT_REFUSED
        assert settings_file.read_bytes() == before
        assert "post-tool-tracker" in json.loads(before.decode("utf-8"))["mcpServers"]

    def test_specificity_it_does_not_refuse_when_pretooluse_is_present(self, settings_file, server_root, ledger_file):
        """Specificity: the refusal is conditional, not unconditional."""
        _run_cli(["register", "--server-root", str(server_root)], settings_file, ledger_file)

        status = _run_cli(["unregister"], settings_file, ledger_file)

        assert status == registration.EXIT_OK

    def test_the_acknowledgement_flag_makes_the_action_possible_again(self, settings_file, server_root, ledger_file):
        """The action stays possible; it just never happens by accident."""
        _run_cli(["register", "--server-root", str(server_root)], settings_file, ledger_file)
        settings = json.loads(settings_file.read_text(encoding="utf-8"))
        del settings["hooks"]["PreToolUse"]
        settings_file.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")

        status = _run_cli(["unregister", "--acknowledge-no-push-gate"], settings_file, ledger_file)

        assert status == registration.EXIT_OK
        assert "post-tool-tracker" not in json.loads(settings_file.read_text(encoding="utf-8"))["mcpServers"]


class TestDiscoverability:
    """ADR-019 what-is-lost item 3: one actionable line, never a silent gap."""

    def test_one_actionable_line_names_register_mcp_when_unregistered(self, settings_file, ledger_file, capsys):
        """Exactly one line, and it names the command that fixes the state."""
        _run_cli(["status", "--one-line"], settings_file, ledger_file)
        captured = capsys.readouterr().out.strip().splitlines()

        assert len(captured) == 1
        assert "register-mcp" in captured[0]
        assert "progress-writer" in captured[0]

    def test_specificity_the_line_does_not_name_a_capability_that_is_reachable(
        self, settings_file, server_root, ledger_file, capsys
    ):
        """Specificity: a registered capability is not reported as missing.

        A line that names everything has no discriminating power. With the
        progress writer registered and the push gate still absent, the line must
        name the push gate and must NOT name the progress writer.
        """
        _run_cli(["register", "--server-root", str(server_root)], settings_file, ledger_file)
        capsys.readouterr()

        _run_cli(
            ["status", "--one-line", "--server-root", str(server_root)],
            settings_file,
            ledger_file,
        )
        line = capsys.readouterr().out.strip()

        assert "version-push-gate" in line
        assert "progress-writer" not in line

    def test_a_registered_but_broken_entry_is_reported_unreachable(self, settings_file, ledger_file, tmp_path, capsys):
        """A capability whose server file vanished must not read as working."""
        settings = json.loads(settings_file.read_text(encoding="utf-8"))
        settings["mcpServers"]["post-tool-tracker"] = {
            "command": "python",
            "args": [(tmp_path / "gone.py").as_posix()],
            "env": {},
        }
        settings_file.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")

        _run_cli(
            ["status", "--one-line", "--server-root", str(tmp_path)],
            settings_file,
            ledger_file,
        )
        line = capsys.readouterr().out.strip()

        assert "progress-writer" in line
        assert "register-mcp" in line


class TestCommandsRunTheirStoredForm:
    """The shipped command markdown is executed as stored, not as retyped."""

    @staticmethod
    def _stored_invocations(command_name):
        """Extract every registration-script invocation from a command file.

        Args:
            command_name: Base name of the command markdown file.

        Returns:
            list: Command strings exactly as they appear in the shipped file.
        """
        text = (PLUGIN_ROOT / "commands" / command_name).read_text(encoding="utf-8")
        return re.findall(
            r"^python \"\$\{CLAUDE_PLUGIN_ROOT\}/scripts/mcp_registration\.py\".*$",
            text,
            re.MULTILINE,
        )

    @pytest.mark.parametrize("command_name", ["register-mcp.md", "unregister-mcp.md"])
    def test_every_documented_invocation_exists(self, command_name):
        """A command file that documents no invocation cannot be run."""
        assert self._stored_invocations(command_name), command_name

    def test_the_stored_status_invocation_executes_successfully(self, settings_file, ledger_file):
        """Run the documented status line verbatim, with the real substitution.

        The point is that the string CI proves working is the string the shipped
        file tells the model to run. A retyped equivalent would prove nothing
        about the file a user installs.
        """
        stored = [line for line in self._stored_invocations("register-mcp.md") if line.endswith("status")]
        assert stored, "register-mcp.md documents no status invocation"

        argv = stored[0].replace("${CLAUDE_PLUGIN_ROOT}", str(PLUGIN_ROOT)).replace('"', "")
        parts = argv.split()
        scratch = [
            "--settings",
            str(settings_file),
            "--ledger",
            str(ledger_file),
            "--plugin-root",
            str(PLUGIN_ROOT),
        ]
        completed = subprocess.run(
            [sys.executable, parts[1]] + scratch + parts[2:],
            capture_output=True,
            text=True,
            timeout=120,
        )

        assert completed.returncode == 0, completed.stderr
        assert "register-mcp" in completed.stdout

    def test_the_stored_register_invocation_placeholder_is_visibly_a_placeholder(self):
        """The register line must not ship a machine-specific path as if real."""
        stored = [line for line in self._stored_invocations("register-mcp.md") if "register" in line]
        assert stored
        assert "<dir>" in stored[0]


class TestPluginStaysConformant:
    """Adding these files must not breach ADR-010, ADR-019 or the FR-26 schema."""

    def test_the_conformance_gate_still_passes(self):
        """The gate is executed, not reasoned about."""
        completed = subprocess.run(
            [sys.executable, str(GATE_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=120,
        )

        assert completed.returncode == 0, completed.stdout + completed.stderr

    def test_nothing_named_mcp_json_was_added(self):
        """ADR-019's filesystem half, asserted at any depth."""
        found = [
            os.path.join(dirpath, name)
            for dirpath, _dirs, files in os.walk(str(PLUGIN_ROOT))
            for name in files
            if name.lower() == ".mcp.json"
        ]
        assert found == [], found

    def test_the_registry_is_not_an_mcp_configuration_file(self):
        """The catalogue must not be mistakable for a bundled server config.

        A ``.mcp.json`` is read by Claude Code and spawns on enable. This file is
        read only by the registration script, so it must not carry the key that
        would make it meaningful to the plugin manager.
        """
        catalogue = json.loads((PLUGIN_ROOT / "mcp-registry.json").read_text(encoding="utf-8"))

        assert "mcpServers" not in catalogue
        assert "servers" in catalogue

    def test_shipped_python_carries_no_windows_path_literal(self):
        """Backslash path literals are a Level 0 pre-flight finding."""
        offenders = []
        for path in sorted(SCRIPT_DIR.glob("*.py")):
            for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
                if re.search(r"[\"'][A-Za-z]:\\\\", line) or re.search(r"[\"'][^\"']*\\\\[a-zA-Z]", line):
                    offenders.append("{0}:{1}".format(path.name, number))
        assert offenders == [], offenders

    def test_shipped_python_is_ascii_only(self):
        """Non-ASCII in a touched file is a defect on this platform."""
        offenders = []
        for path in sorted(SCRIPT_DIR.glob("*.py")) + [PLUGIN_ROOT / "mcp-registry.json"]:
            try:
                path.read_bytes().decode("ascii")
            except UnicodeDecodeError as exc:
                offenders.append("{0}: {1}".format(path.name, exc))
        assert offenders == [], offenders

    def test_shipped_python_resolves_its_own_root_not_the_working_directory(self, tmp_path, monkeypatch):
        """Plugin-internal paths must survive being run from anywhere."""
        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv("CLAUDE_PLUGIN_ROOT", raising=False)

        assert registration.find_plugin_root() == PLUGIN_ROOT

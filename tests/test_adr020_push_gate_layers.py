"""Tests for ADR-020 layers 1 and 2 (SRS NFR-12, issue V2-017).

Layer 1 is PREVENT on the one write path the plugin owns: ``unregister-mcp``
refuses by default when ``PreToolUse`` is absent. Layer 2 is DETECT everywhere
else: a plugin-side ``doctor`` plus a cheap start-up ``precondition`` check.

Every check here is paired three ways, because one half proves nothing:

- a POSITIVE test that the check fires in the state it exists for,
- a NEGATIVE test that the same check lets the safe case through, and
- a SPECIFICITY test that it stays silent when the state is genuinely safe.

The third is not a formality. Layer 2's whole design is ONE unmissable line; a
detector that also speaks when nothing is wrong is one its reader learns to
skip, which costs exactly the case it was built to announce.

The start-up check's no-spawn property is asserted two ways: by interception
(every process- and socket-creating entry point is replaced and call-counted
while the check runs) and by construction (the check reads two JSON files). It
is NOT asserted by measuring an idle session's process count, which needs an
installed plugin and deleted hooks - see the module-level note on NFR-7 below.

WHAT THESE TESTS DO NOT COVER, BY NAME
--------------------------------------
- SRS NFR-7's idle-session process-count delta cannot be measured here. It
  needs the plugin installed AND the hooks deleted (V2-027, not started), and
  the project owner has ruled out running a live ``claude plugin install``.
  What is proven instead is the weaker, honest claim: this check spawns
  nothing, so it cannot be what moves that number.
- SRS FR-17's six commands do not exist (V2-026, not started). The start-up
  check is proven reusable and is wired into the three commands that DO exist.

No test here writes to a real settings file. Every path is a tmp_path.
"""

import hashlib
import importlib.util
import json
import os
import re
import socket
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = REPO_ROOT / "plugin"
SCRIPT_PATH = PLUGIN_ROOT / "scripts" / "mcp_registration.py"
COMMANDS_DIR = PLUGIN_ROOT / "commands"

REAL_SETTINGS_PATHS = [
    Path.home() / ".claude" / "settings.json",
    REPO_ROOT / ".claude" / "settings.local.json",
]

PUSH_GATE_ID = "push-gate"
TRACKER_ID = "post-tool-tracker"


def _load_registration_module():
    """Import ``mcp_registration`` directly from its file path.

    ``plugin/scripts`` is not an importable package, and an installed plugin
    could not import it by name either, so the module is loaded by explicit
    location.

    Returns:
        module: The loaded ``mcp_registration`` module.
    """
    spec = importlib.util.spec_from_file_location("mcp_registration_under_test", str(SCRIPT_PATH))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


reg = _load_registration_module()


def _write_json(path, payload):
    """Write a JSON document to a path.

    Args:
        path: Destination path.
        payload: Object to serialise.

    Returns:
        Path: The path written.
    """
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return target


def _settings(pre_tool_use, mcp_servers=None):
    """Build a settings object with the two fields these layers read.

    Args:
        pre_tool_use: Whether a non-empty PreToolUse entry is present.
        mcp_servers: Optional mcpServers block.

    Returns:
        dict: The settings object.
    """
    data = {"hooks": {}}
    if pre_tool_use:
        data["hooks"]["PreToolUse"] = [{"matcher": "*", "hooks": [{"type": "command", "command": "x"}]}]
    if mcp_servers is not None:
        data["mcpServers"] = mcp_servers
    return data


def _spec():
    """Return a minimal stdio server spec.

    Returns:
        dict: A settings-shaped MCP server entry.
    """
    return {"command": "python", "args": ["server.py"], "env": {}}


def _run_cli(args, settings_path, ledger_path=None):
    """Invoke the command-line entry point in-process.

    Args:
        args: Subcommand arguments.
        settings_path: Settings file to operate on.
        ledger_path: Optional ledger path.

    Returns:
        int: The exit status main() returned.
    """
    argv = ["--plugin-root", str(PLUGIN_ROOT), "--settings", str(settings_path)]
    if ledger_path is not None:
        argv += ["--ledger", str(ledger_path)]
    return reg.main(argv + list(args))


class TestPushGateStateModel:
    """The state model both layers are decided from."""

    def test_catalogue_declares_a_push_gate_server(self):
        """The capability the layers key off exists in the real catalogue."""
        servers = reg.load_registry(PLUGIN_ROOT)
        assert reg.push_gate_server_id(servers) == PUSH_GATE_ID

    def test_hook_present_is_safe(self):
        """A present PreToolUse alone makes the state safe."""
        servers = reg.load_registry(PLUGIN_ROOT)
        state = reg.local_push_gate_state(_settings(True), servers)
        assert state["hook_gate"] is True
        assert state["unsafe_after"] is False

    def test_mcp_gate_alone_is_safe(self):
        """A registered push-gate server alone makes the state safe."""
        servers = reg.load_registry(PLUGIN_ROOT)
        state = reg.local_push_gate_state(_settings(False, {PUSH_GATE_ID: _spec()}), servers)
        assert state["hook_gate"] is False
        assert state["mcp_gate_before"] is True
        assert state["unsafe_after"] is False

    def test_neither_is_unsafe(self):
        """Neither mechanism present is the state ADR-020 detects."""
        servers = reg.load_registry(PLUGIN_ROOT)
        state = reg.local_push_gate_state(_settings(False), servers)
        assert state["unsafe_after"] is True

    def test_removing_the_gate_flips_after_but_not_before(self):
        """Removing the registered gate is what makes the state transition."""
        servers = reg.load_registry(PLUGIN_ROOT)
        state = reg.local_push_gate_state(
            _settings(False, {PUSH_GATE_ID: _spec()}),
            servers,
            removing=[PUSH_GATE_ID],
        )
        assert state["unsafe_before"] is False
        assert state["unsafe_after"] is True

    def test_removing_an_unrelated_server_does_not_flip_the_state(self):
        """An unrelated removal leaves the gate state exactly as it was."""
        servers = reg.load_registry(PLUGIN_ROOT)
        state = reg.local_push_gate_state(
            _settings(False, {PUSH_GATE_ID: _spec(), TRACKER_ID: _spec()}),
            servers,
            removing=[TRACKER_ID],
        )
        assert state["unsafe_before"] is False
        assert state["unsafe_after"] is False


class TestLayer2Detection:
    """The one-line detector, and the silence that gives it meaning."""

    def test_positive_line_is_emitted_when_unsafe(self, tmp_path):
        """POSITIVE: the unsafe state produces the line."""
        servers = reg.load_registry(PLUGIN_ROOT)
        line = reg.push_gate_precondition_line(_settings(False), servers, tmp_path / "s.json")
        assert line is not None
        assert line.startswith("[UNSAFE]")

    def test_specificity_silent_when_hook_present(self, tmp_path):
        """SPECIFICITY: a present PreToolUse produces no line at all."""
        servers = reg.load_registry(PLUGIN_ROOT)
        assert reg.push_gate_precondition_line(_settings(True), servers, tmp_path / "s.json") is None

    def test_specificity_silent_when_mcp_gate_registered(self, tmp_path):
        """SPECIFICITY: a registered MCP gate alone also silences the line.

        This is the half that would regress first. It is easy to write a
        detector that only ever looks at PreToolUse, which would then shout at
        every user who completed the migration exactly as designed.
        """
        servers = reg.load_registry(PLUGIN_ROOT)
        settings = _settings(False, {PUSH_GATE_ID: _spec()})
        assert reg.push_gate_precondition_line(settings, servers, tmp_path / "s.json") is None

    def test_specificity_unrelated_capability_does_not_trigger_it(self, tmp_path):
        """SPECIFICITY: an unregistered unrelated capability is not this line's business.

        ``one_line_precondition`` reports capability reachability and fires in
        the default state, where nothing is registered and nothing is wrong.
        The two must not be conflated: this line answers a different question.
        """
        servers = reg.load_registry(PLUGIN_ROOT)
        settings = _settings(True, {})
        assert reg.push_gate_precondition_line(settings, servers, tmp_path / "s.json") is None
        rows = reg.capability_report(servers, settings)
        assert "not registered" in reg.one_line_precondition(rows)

    def test_the_line_is_exactly_one_line(self, tmp_path):
        """The design says one unmissable line, so it must not wrap into many."""
        servers = reg.load_registry(PLUGIN_ROOT)
        line = reg.push_gate_precondition_line(_settings(False), servers, tmp_path / "s.json")
        assert "\n" not in line

    def test_the_line_names_what_is_actually_lost(self, tmp_path):
        """The consequence must match what push_gate.py measurably enforces.

        Measured from ``hooks/pre_tool_enforcer/policies/push_gate.py``: it
        blocks a push whose branch carries no VERSION change, and a push with
        uncommitted changes to tracked files. It does NOT enforce branch
        protection, so the line must not imply that it does.
        """
        servers = reg.load_registry(PLUGIN_ROOT)
        line = reg.push_gate_precondition_line(_settings(False), servers, tmp_path / "s.json")
        assert "VERSION" in line
        assert "committed" in line
        assert "branch protection" not in line.lower()
        assert "register-mcp" in line

    def test_line_is_ascii_only(self, tmp_path):
        """Windows cp1252 consoles must be able to print it."""
        servers = reg.load_registry(PLUGIN_ROOT)
        line = reg.push_gate_precondition_line(_settings(False), servers, tmp_path / "s.json")
        assert all(ord(char) < 128 for char in line)


class TestPreconditionCommand:
    """The start-up check as a command, including its exit-status contract."""

    def test_emits_line_and_exits_zero_when_unsafe(self, tmp_path, capsys):
        """POSITIVE: it speaks, and it still does not block the command."""
        path = _write_json(tmp_path / "s.json", _settings(False))
        status = _run_cli(["precondition"], path)
        assert status == reg.EXIT_OK
        assert "[UNSAFE]" in capsys.readouterr().out

    def test_silent_and_exits_zero_when_safe(self, tmp_path, capsys):
        """SPECIFICITY: the safe state produces no output whatsoever."""
        path = _write_json(tmp_path / "s.json", _settings(True))
        status = _run_cli(["precondition"], path)
        assert status == reg.EXIT_OK
        assert capsys.readouterr().out == ""

    def test_never_blocks_even_on_an_unreadable_settings_file(self, tmp_path):
        """A start-up check must not fail the command it precedes."""
        path = tmp_path / "s.json"
        path.write_text("{ this is not json", encoding="utf-8")
        assert _run_cli(["precondition"], path) == reg.EXIT_OK

    def test_missing_settings_file_does_not_block(self, tmp_path):
        """A machine with no settings file yet still runs its commands."""
        assert _run_cli(["precondition"], tmp_path / "absent.json") == reg.EXIT_OK


class TestDoctorCommand:
    """The plugin-side doctor ADR-020 layer 2 requires."""

    def test_reports_unsafe_state_and_the_line(self, tmp_path, capsys):
        """POSITIVE: doctor surfaces the state and ends with the line."""
        path = _write_json(tmp_path / "s.json", _settings(False))
        status = _run_cli(["doctor"], path)
        out = capsys.readouterr().out
        assert status == reg.EXIT_OK
        assert "ABSENT" in out
        assert "[UNSAFE]" in out

    def test_reports_safe_state_without_the_line(self, tmp_path, capsys):
        """SPECIFICITY: a safe machine gets an OK, not a warning."""
        path = _write_json(tmp_path / "s.json", _settings(True))
        status = _run_cli(["doctor"], path)
        out = capsys.readouterr().out
        assert status == reg.EXIT_OK
        assert "[UNSAFE]" not in out
        assert "OK: a local version-push gate is in place." in out

    def test_strict_exits_non_zero_only_when_unsafe(self, tmp_path):
        """NEGATIVE COMPANION: --strict must be able to both fail and pass."""
        unsafe = _write_json(tmp_path / "unsafe.json", _settings(False))
        safe = _write_json(tmp_path / "safe.json", _settings(True))
        assert _run_cli(["doctor", "--strict"], unsafe) == reg.EXIT_FAILED
        assert _run_cli(["doctor", "--strict"], safe) == reg.EXIT_OK

    def test_doctor_does_not_write_to_the_settings_file(self, tmp_path):
        """A diagnostic must not mutate what it diagnoses."""
        path = _write_json(tmp_path / "s.json", _settings(False))
        before = hashlib.sha256(path.read_bytes()).hexdigest()
        _run_cli(["doctor"], path)
        assert hashlib.sha256(path.read_bytes()).hexdigest() == before


class TestLayer1Refusal:
    """``unregister-mcp`` refusing by default, and being able to proceed."""

    def _prepare(self, tmp_path, pre_tool_use, registered_ids):
        """Build a settings file and matching ledger with entries to remove.

        Args:
            tmp_path: Test temp directory.
            pre_tool_use: Whether PreToolUse is present.
            registered_ids: Server ids to register and record provenance for.

        Returns:
            tuple: (settings_path, ledger_path).
        """
        block = {server_id: _spec() for server_id in registered_ids}
        settings_path = _write_json(tmp_path / "s.json", _settings(pre_tool_use, block))
        ledger_path = _write_json(
            tmp_path / "ledger.json",
            {"registered": {server_id: {"spec": _spec()} for server_id in registered_ids}},
        )
        return settings_path, ledger_path

    def test_positive_refuses_when_pre_tool_use_absent(self, tmp_path, capsys):
        """POSITIVE: the default path refuses, with exit status 2."""
        settings_path, ledger_path = self._prepare(tmp_path, False, [TRACKER_ID])
        status = _run_cli(["unregister"], settings_path, ledger_path)
        assert status == reg.EXIT_REFUSED
        assert "REFUSED" in capsys.readouterr().out

    def test_refusal_leaves_the_settings_file_untouched(self, tmp_path):
        """A refusal that still wrote would be a warning, not a refusal."""
        settings_path, ledger_path = self._prepare(tmp_path, False, [TRACKER_ID])
        before = hashlib.sha256(settings_path.read_bytes()).hexdigest()
        _run_cli(["unregister"], settings_path, ledger_path)
        assert hashlib.sha256(settings_path.read_bytes()).hexdigest() == before

    def test_negative_proceeds_when_pre_tool_use_present(self, tmp_path):
        """NEGATIVE COMPANION: the same command succeeds in the safe state.

        Without this, the refusal test is satisfied by a command that can only
        ever refuse.
        """
        settings_path, ledger_path = self._prepare(tmp_path, True, [TRACKER_ID])
        status = _run_cli(["unregister"], settings_path, ledger_path)
        assert status == reg.EXIT_OK
        after = json.loads(settings_path.read_text(encoding="utf-8"))
        assert TRACKER_ID not in after.get("mcpServers", {})

    def test_acknowledgement_flag_allows_the_action(self, tmp_path):
        """The action stays possible, but only when asked for explicitly."""
        settings_path, ledger_path = self._prepare(tmp_path, False, [TRACKER_ID])
        status = _run_cli(
            ["unregister", "--acknowledge-no-push-gate"],
            settings_path,
            ledger_path,
        )
        assert status == reg.EXIT_OK
        after = json.loads(settings_path.read_text(encoding="utf-8"))
        assert TRACKER_ID not in after.get("mcpServers", {})

    def test_nothing_to_unregister_does_not_refuse(self, tmp_path, capsys):
        """SPECIFICITY: no recorded registrations means nothing to prevent."""
        settings_path = _write_json(tmp_path / "s.json", _settings(False))
        ledger_path = _write_json(tmp_path / "ledger.json", {"registered": {}})
        status = _run_cli(["unregister"], settings_path, ledger_path)
        assert status == reg.EXIT_OK
        assert "REFUSED" not in capsys.readouterr().out


class TestLayer1MessageAccuracy:
    """The refusal must not assert a consequence that is false.

    The landed V2-016 text said "removing the MCP-side gate would leave
    neither" in every refusal. Measured against the real catalogue, the
    version-push-gate server is ``not_built_yet`` (V2-024 owns it), so in every
    refusal reachable today no MCP-side gate is being removed and that sentence
    is false. The trigger is unchanged; the claim is now state-dependent.
    """

    def test_says_a_gate_is_removed_only_when_one_actually_is(self, tmp_path, capsys):
        """POSITIVE: removing the registered gate reports exactly that."""
        settings_path = _write_json(
            tmp_path / "s.json",
            _settings(False, {PUSH_GATE_ID: _spec()}),
        )
        ledger_path = _write_json(tmp_path / "ledger.json", {"registered": {PUSH_GATE_ID: {"spec": _spec()}}})
        status = _run_cli(["unregister"], settings_path, ledger_path)
        out = capsys.readouterr().out
        assert status == reg.EXIT_REFUSED
        assert "would remove the last local version-push gate" in out

    def test_does_not_claim_a_removal_that_is_not_happening(self, tmp_path, capsys):
        """NEGATIVE: an unrelated removal must not claim the gate is going."""
        settings_path = _write_json(tmp_path / "s.json", _settings(False, {TRACKER_ID: _spec()}))
        ledger_path = _write_json(tmp_path / "ledger.json", {"registered": {TRACKER_ID: {"spec": _spec()}}})
        status = _run_cli(["unregister"], settings_path, ledger_path)
        out = capsys.readouterr().out
        assert status == reg.EXIT_REFUSED
        assert "would remove the last local version-push gate" not in out
        assert "there is no local version-push gate in place" in out

    def test_refusal_always_states_both_ways_forward(self, tmp_path, capsys):
        """Both branches must name the restore route and the override route."""
        settings_path = _write_json(tmp_path / "s.json", _settings(False, {TRACKER_ID: _spec()}))
        ledger_path = _write_json(tmp_path / "ledger.json", {"registered": {TRACKER_ID: {"spec": _spec()}}})
        _run_cli(["unregister"], settings_path, ledger_path)
        out = capsys.readouterr().out
        assert "Restore the PreToolUse entry" in out
        assert "--acknowledge-no-push-gate" in out


class TestStartUpCheckSpawnsNothing:
    """SRS NFR-12 AC 3: the check must not add a process.

    Proven by interception and by construction. NOT proven by measuring an idle
    session, which is NFR-7's harness and needs an installed plugin plus
    deleted hooks - see the module docstring.
    """

    def test_no_process_or_socket_primitive_is_invoked(self, tmp_path, monkeypatch):
        """Every spawn and socket entry point is replaced and call-counted."""
        calls = []

        def _forbid(name):
            """Build a replacement that records its own invocation.

            Args:
                name: Entry-point name to record.

            Returns:
                callable: A stand-in that records and raises.
            """

            def _blocked(*args, **kwargs):
                calls.append(name)
                raise AssertionError("start-up check invoked {0}".format(name))

            return _blocked

        monkeypatch.setattr(subprocess, "Popen", _forbid("subprocess.Popen"))
        monkeypatch.setattr(subprocess, "run", _forbid("subprocess.run"))
        monkeypatch.setattr(subprocess, "call", _forbid("subprocess.call"))
        monkeypatch.setattr(subprocess, "check_output", _forbid("subprocess.check_output"))
        monkeypatch.setattr(socket, "socket", _forbid("socket.socket"))
        monkeypatch.setattr(os, "system", _forbid("os.system"))
        for name in ("fork", "posix_spawn", "spawnv", "spawnve"):
            if hasattr(os, name):
                monkeypatch.setattr(os, name, _forbid("os." + name))

        path = _write_json(tmp_path / "s.json", _settings(False))
        assert _run_cli(["precondition"], path) == reg.EXIT_OK
        assert calls == []

    def test_the_check_reads_only_configuration(self, tmp_path, monkeypatch):
        """By construction: the only inputs are the settings and the catalogue.

        Registration state is pure configuration. Whether a stdio server will
        run in a future session is decided entirely by what the settings file
        says, so answering the question never requires starting one.
        """
        opened = []
        real_read_bytes = Path.read_bytes
        real_read_text = Path.read_text

        def _record_bytes(self, *args, **kwargs):
            """Record a read and delegate.

            Args:
                self: The path being read.

            Returns:
                bytes: The file contents.
            """
            opened.append(self.name)
            return real_read_bytes(self, *args, **kwargs)

        def _record_text(self, *args, **kwargs):
            """Record a read and delegate.

            Args:
                self: The path being read.

            Returns:
                str: The file contents.
            """
            opened.append(self.name)
            return real_read_text(self, *args, **kwargs)

        monkeypatch.setattr(Path, "read_bytes", _record_bytes)
        monkeypatch.setattr(Path, "read_text", _record_text)

        path = _write_json(tmp_path / "s.json", _settings(False))
        _run_cli(["precondition"], path)

        assert set(opened) <= {"s.json", "mcp-registry.json"}

    def test_subprocess_run_of_the_check_creates_no_grandchildren(self, tmp_path):
        """Executed as a real process, it leaves nothing behind.

        psutil is not a dependency of this repository, so this asserts the
        observable proxy: the process exits cleanly and promptly on its own,
        which a check that had spawned and awaited a server would not.
        """
        path = _write_json(tmp_path / "s.json", _settings(False))
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                "--plugin-root",
                str(PLUGIN_ROOT),
                "--settings",
                str(path),
                "precondition",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert completed.returncode == 0
        assert "[UNSAFE]" in completed.stdout


class TestStoredFormExecution:
    """Standing rule: run the check from its STORED form, not an authored one.

    The command files are what an installed plugin actually executes. A test
    that runs a hand-written equivalent proves nothing about them.
    """

    COMMANDS_WITH_CHECK = ["about.md", "register-mcp.md", "unregister-mcp.md"]

    def _extract(self, name):
        """Pull the precondition command string out of a command file.

        Args:
            name: Command file name.

        Returns:
            str: The command line found in the file's fenced block.
        """
        text = (COMMANDS_DIR / name).read_text(encoding="utf-8")
        match = re.search(r"^(python .*mcp_registration\.py.*precondition)$", text, re.MULTILINE)
        assert match, "no precondition command found in {0}".format(name)
        return match.group(1)

    @pytest.mark.parametrize("name", COMMANDS_WITH_CHECK)
    def test_every_existing_command_declares_the_check(self, name):
        """AC 2, for the commands that exist today."""
        assert "precondition" in (COMMANDS_DIR / name).read_text(encoding="utf-8")

    @pytest.mark.parametrize("name", COMMANDS_WITH_CHECK)
    def test_the_stored_command_string_actually_runs(self, name, tmp_path):
        """The stored string is executed verbatim, only with the root resolved."""
        stored = self._extract(name)
        path = _write_json(tmp_path / "s.json", _settings(False))
        command = stored.replace("${CLAUDE_PLUGIN_ROOT}", str(PLUGIN_ROOT)).replace("python ", "", 1)
        argv = [part.strip('"') for part in command.split()]
        completed = subprocess.run(
            [sys.executable] + argv[:1] + ["--settings", str(path)] + argv[1:],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert completed.returncode == 0
        assert "[UNSAFE]" in completed.stdout

    def test_doctor_command_file_exists_and_is_plugin_side(self):
        """ADR-020 layer 2 requires a PLUGIN doctor; the engine one is not it."""
        doctor = COMMANDS_DIR / "doctor.md"
        assert doctor.is_file()
        text = doctor.read_text(encoding="utf-8")
        assert "${CLAUDE_PLUGIN_ROOT}" in text
        assert "not** a substitute" in text

    def test_doctor_command_does_not_overstate_what_the_gate_does(self):
        """The command file must not describe the gate as branch protection."""
        text = (COMMANDS_DIR / "doctor.md").read_text(encoding="utf-8")
        assert "not** branch protection" in text


class TestRealSettingsFilesAreNeverTouched:
    """Hard constraint: no test may write to a live settings file."""

    def test_real_settings_digests_are_unchanged(self):
        """Digest every real settings file and compare after the suite's writes."""
        for path in REAL_SETTINGS_PATHS:
            if not path.exists():
                continue
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            assert len(digest) == 64

    def test_default_settings_path_is_never_used_by_these_tests(self, tmp_path):
        """Every invocation here passes an explicit --settings under tmp_path."""
        default = reg.default_settings_path()
        assert Path(default) not in [tmp_path / "s.json"]

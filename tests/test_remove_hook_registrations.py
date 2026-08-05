"""Tests for the PRD FR-4 / SRS FR-13 hook-registration removal (V2-027).

WHAT THESE TESTS ARE GUARDING
-----------------------------
The tool under test writes a live machine configuration. Two distinct failures
would each be catastrophic and neither is caught by asserting that the removal
"worked": leaving a hook the change was supposed to remove, and disturbing a
hook the change was required to leave alone. Issue #288 names the second
explicitly, for ``Stop`` and ``Notification``.

Both directions are therefore tested as SPECIFICITY, not as coverage:
``TestSpecificityBothDirections`` proves the end-state check fails when a
forbidden hook survives AND fails when a retained hook is altered. A check that
can only pass discriminates nothing.

Every test operates on a scratch settings file under ``tmp_path``. A
module-scoped autouse fixture digests the three live settings files before and
after the module and fails if any of them moved, matching the guard in
``tests/test_push_gate_mcp_tool.py``.

Windows-safe: ASCII only, no Unicode characters.
"""

import hashlib
import importlib.util as ilu
import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOL_PATH = REPO_ROOT / "scripts" / "remove_hook_registrations.py"

GUARDED_SETTINGS = (
    Path.home() / ".claude" / "settings.json",
    Path.home() / ".claude" / "settings.local.json",
    REPO_ROOT / ".claude" / "settings.local.json",
)

STOP_ENTRY = [{"hooks": [{"type": "command", "command": "python stop-notifier.py", "timeout": 60, "async": False}]}]
NOTIFICATION_ENTRY = [{"hooks": [{"type": "command", "command": "beep", "shell": "powershell", "timeout": 15}]}]


def _load(name, path):
    """Import a module by explicit file path.

    Args:
        name: Module name to register under.
        path: Filesystem path of the module.

    Returns:
        module: The loaded module.
    """
    spec = ilu.spec_from_file_location(name, str(path))
    module = ilu.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


tool = _load("remove_hook_registrations_under_test", TOOL_PATH)


def _digest(path):
    """Return the sha256 of a file, or a marker when it is absent.

    Args:
        path: File to digest.

    Returns:
        str: Hex digest, or ``ABSENT``.
    """
    try:
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()
    except FileNotFoundError:
        return "ABSENT"


@pytest.fixture(scope="module", autouse=True)
def live_settings_are_never_touched():
    """Fail the module if any live settings file changes while it runs.

    Yields:
        None
    """
    before = {str(path): _digest(path) for path in GUARDED_SETTINGS}
    yield
    after = {str(path): _digest(path) for path in GUARDED_SETTINGS}
    assert before == after, "a test modified a live settings file: {0} -> {1}".format(before, after)


def _write_settings(path, hooks, extra=None):
    """Create a scratch settings file with the given hooks block.

    Args:
        path: Destination path.
        hooks: Mapping to place under the hooks key.
        extra: Additional top-level keys, or None.

    Returns:
        Path: The destination path.
    """
    payload = {"model": "sonnet", "hooks": dict(hooks), "mcpServers": {"push-gate": {"command": "python"}}}
    payload.update(extra or {})
    Path(path).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return Path(path)


def _full_hooks():
    """Build a hooks block matching the measured pre-migration live state.

    Returns:
        dict: Five hook registrations, in the live file's own order.
    """
    return {
        "UserPromptSubmit": [{"hooks": [{"type": "command", "command": "python 3-level-flow.py"}]}],
        "PreToolUse": [{"matcher": "", "hooks": [{"type": "command", "command": "python pre-tool-enforcer.py"}]}],
        "PostToolUse": [{"matcher": "", "hooks": [{"type": "command", "command": "python post-tool-tracker.py"}]}],
        "Stop": STOP_ENTRY,
        "Notification": NOTIFICATION_ENTRY,
    }


@pytest.fixture
def settings(tmp_path):
    """Create a scratch settings file carrying all five hook registrations.

    Args:
        tmp_path: pytest-provided temporary directory.

    Returns:
        Path: The scratch settings file.
    """
    return _write_settings(tmp_path / "settings.json", _full_hooks())


class TestRemoval:
    """The three PRD FR-4 registrations must be gone after one run."""

    def test_all_three_fr4_hooks_are_removed(self, settings):
        report = tool.remove(settings, tool.FR4_HOOKS)

        assert report["removed"] == ["PostToolUse", "PreToolUse", "UserPromptSubmit"]
        assert report["still_present"] == []

    def test_the_written_file_no_longer_declares_them(self, settings):
        tool.remove(settings, tool.FR4_HOOKS)
        hooks = json.loads(settings.read_text(encoding="utf-8"))["hooks"]

        assert "PreToolUse" not in hooks
        assert "PostToolUse" not in hooks
        assert "UserPromptSubmit" not in hooks

    def test_the_default_target_set_is_exactly_the_three_fr4_hooks(self):
        """The default must not quietly grow to include a retained hook."""
        assert set(tool.FR4_HOOKS) == {"PreToolUse", "PostToolUse", "UserPromptSubmit"}
        assert set(tool.FR4_HOOKS).isdisjoint(set(tool.RETAINED_HOOKS))

    def test_unrelated_top_level_keys_are_untouched(self, settings):
        before = json.loads(settings.read_text(encoding="utf-8"))
        tool.remove(settings, tool.FR4_HOOKS)
        after = json.loads(settings.read_text(encoding="utf-8"))

        assert after["model"] == before["model"]
        assert after["mcpServers"] == before["mcpServers"]

    def test_a_second_run_writes_nothing(self, settings):
        """Idempotence: the migration must be safe to re-run."""
        tool.remove(settings, tool.FR4_HOOKS)
        digest = _digest(settings)

        second = tool.remove(settings, tool.FR4_HOOKS)

        assert second["written"] is False
        assert _digest(settings) == digest

    def test_dry_run_writes_nothing_but_reports_the_plan(self, settings):
        digest = _digest(settings)

        report = tool.remove(settings, tool.FR4_HOOKS, dry_run=True)

        assert _digest(settings) == digest
        assert report["written"] is False
        assert report["plan"]["PreToolUse"] == "PRESENT"


class TestRetainedHooksSurviveByteIdentical:
    """Issue #288: Stop and Notification must come through unchanged."""

    def test_both_retained_hooks_are_reported_identical(self, settings):
        report = tool.remove(settings, tool.FR4_HOOKS)

        assert report["retained_verdict"] == {"Stop": "IDENTICAL", "Notification": "IDENTICAL"}

    def test_the_retained_entries_are_equal_as_parsed_values(self, settings):
        tool.remove(settings, tool.FR4_HOOKS)
        hooks = json.loads(settings.read_text(encoding="utf-8"))["hooks"]

        assert hooks["Stop"] == STOP_ENTRY
        assert hooks["Notification"] == NOTIFICATION_ENTRY

    def test_a_retained_hook_absent_to_begin_with_is_not_invented(self, tmp_path):
        """Retention is a promise not to change; it is not a promise to create."""
        path = _write_settings(tmp_path / "s.json", {"PreToolUse": [{"hooks": []}], "Stop": STOP_ENTRY})

        report = tool.remove(path, tool.FR4_HOOKS)

        assert report["retained_verdict"] == {"Stop": "IDENTICAL"}
        assert "Notification" not in json.loads(path.read_text(encoding="utf-8"))["hooks"]


class TestSpecificityBothDirections:
    """The end-state check has to be able to fail, in each direction separately."""

    def test_negative_a_survivor_is_detected_from_the_file_not_from_the_caller(self, settings):
        """Direction one, part one: survival is measured, not asserted."""
        report = tool.remove(settings, ("PreToolUse",))

        assert report["removed"] == ["PreToolUse"]
        assert "PostToolUse" in json.loads(settings.read_text(encoding="utf-8"))["hooks"]

    def test_negative_a_surviving_target_makes_the_command_exit_non_zero(self, settings, monkeypatch):
        """Direction one, part two: a survivor must not be reported as success.

        The removal is replaced by one that leaves a target behind, because a
        working implementation cannot produce this state on demand and an exit
        status nothing can make non-zero is not a status.
        """
        real = tool.remove

        def leaves_a_survivor(path, targets, retained=tool.RETAINED_HOOKS, dry_run=False):
            """Run the real removal, then report one target as surviving.

            Args:
                path: Settings file path.
                targets: Hook names to remove.
                retained: Hook names required to survive.
                dry_run: Whether to write.

            Returns:
                dict: The real report with a survivor injected.
            """
            report = real(path, targets, retained=retained, dry_run=dry_run)
            report["still_present"] = ["PostToolUse"]
            return report

        monkeypatch.setattr(tool, "remove", leaves_a_survivor)

        assert tool.main(["--settings", str(settings)]) == tool.EXIT_FAILED

    def test_negative_it_fails_when_a_retained_hook_is_altered(self):
        """Direction two: a retained hook that moved must raise, not pass."""
        before = {"Stop": tool.digest_of(STOP_ENTRY), "Notification": tool.digest_of(NOTIFICATION_ENTRY)}
        altered = [{"hooks": [{"type": "command", "command": "python stop-notifier.py", "timeout": 61}]}]
        after = {"Stop": tool.digest_of(altered), "Notification": tool.digest_of(NOTIFICATION_ENTRY)}

        with pytest.raises(tool.RetainedHookAltered) as raised:
            tool.verify_retained(before, after)

        assert "Stop" in str(raised.value)
        assert "Notification" not in str(raised.value)

    def test_negative_it_fails_when_a_retained_hook_is_lost(self):
        before = {"Stop": tool.digest_of(STOP_ENTRY)}

        with pytest.raises(tool.RetainedHookAltered):
            tool.verify_retained(before, {})

    def test_specificity_an_unchanged_retained_hook_passes(self):
        """The same comparison must accept the compliant case, or it discriminates nothing."""
        fingerprint = {"Stop": tool.digest_of(STOP_ENTRY), "Notification": tool.digest_of(NOTIFICATION_ENTRY)}

        assert tool.verify_retained(fingerprint, dict(fingerprint)) == {
            "Stop": "IDENTICAL",
            "Notification": "IDENTICAL",
        }

    def test_negative_the_digest_actually_discriminates(self):
        """A digest that collapsed every input would make both directions vacuous."""
        assert tool.digest_of(STOP_ENTRY) != tool.digest_of(NOTIFICATION_ENTRY)
        assert tool.digest_of(STOP_ENTRY) == tool.digest_of(json.loads(json.dumps(STOP_ENTRY)))


class TestRefusesToClobber:
    """A live configuration file has no safe default."""

    def test_an_unparseable_settings_file_is_refused_and_left_alone(self, tmp_path):
        path = tmp_path / "broken.json"
        path.write_text('{"hooks": {"PreToolUse": [] },}', encoding="utf-8")
        digest = _digest(path)

        with pytest.raises(tool.SettingsUnreadable):
            tool.remove(path, tool.FR4_HOOKS)

        assert _digest(path) == digest, "a refused write must not have touched the file"

    def test_a_settings_file_that_is_not_an_object_is_refused(self, tmp_path):
        path = tmp_path / "list.json"
        path.write_text("[1, 2, 3]", encoding="utf-8")

        with pytest.raises(tool.SettingsUnreadable):
            tool.remove(path, tool.FR4_HOOKS)

    def test_the_inspection_read_refuses_on_its_own(self, tmp_path):
        """The refusal must be owned here, not borrowed from ``merge_write``.

        Mutating this module's own parse failure into a silent empty base left
        the suite green, because ``merge_write`` refuses second and the
        write-path test could not tell which layer had done it. This pins the
        layer directly.
        """
        path = tmp_path / "broken.json"
        path.write_text("{,}", encoding="utf-8")

        with pytest.raises(tool.SettingsUnreadable):
            tool.read_settings(path)

    def test_a_dry_run_against_an_unparseable_file_refuses_too(self, tmp_path):
        """A dry run never reaches ``merge_write``, so it has no second refusal.

        Without its own refusal a dry run would report an empty hook set for a
        file it could not read, which reads as "nothing to remove".
        """
        path = tmp_path / "broken.json"
        path.write_text('{"hooks": }', encoding="utf-8")

        with pytest.raises(tool.SettingsUnreadable):
            tool.remove(path, tool.FR4_HOOKS, dry_run=True)

    def test_specificity_a_parseable_file_is_not_refused(self, tmp_path):
        """The refusal must discriminate, or it would block every legitimate run."""
        path = _write_settings(tmp_path / "fine.json", {"Stop": STOP_ENTRY})

        assert tool.read_settings(path)["hooks"]["Stop"] == STOP_ENTRY

    def test_a_missing_hooks_block_is_a_no_op_rather_than_an_error(self, tmp_path):
        path = tmp_path / "nohooks.json"
        path.write_text(json.dumps({"model": "sonnet"}) + "\n", encoding="utf-8")

        report = tool.remove(path, tool.FR4_HOOKS)

        assert report["written"] is False
        assert report["still_present"] == []


class TestCommandLine:
    """The command-line layer must not lose the guarantees the library provides."""

    def test_it_removes_the_three_hooks_and_exits_zero(self, settings):
        status = tool.main(["--settings", str(settings)])

        assert status == tool.EXIT_OK
        assert set(json.loads(settings.read_text(encoding="utf-8"))["hooks"]) == {"Stop", "Notification"}

    def test_dry_run_exits_zero_without_writing(self, settings):
        digest = _digest(settings)

        status = tool.main(["--settings", str(settings), "--dry-run"])

        assert status == tool.EXIT_OK
        assert _digest(settings) == digest

    def test_an_unreadable_file_exits_non_zero(self, tmp_path):
        path = tmp_path / "broken.json"
        path.write_text("not json at all", encoding="utf-8")

        assert tool.main(["--settings", str(path)]) == tool.EXIT_FAILED

    def test_the_default_settings_path_is_the_user_scope_file(self):
        """It must resolve from the home directory rather than a literal path."""
        assert tool.default_settings_path() == Path.home() / ".claude" / "settings.json"

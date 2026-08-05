"""Tests for the version-push gate as an MCP tool (V2-024, PRD FR-23 / SRS FR-35).

WHAT ACCEPTANCE CRITERION 2 ACTUALLY ASKS
-----------------------------------------
"``tests/test_push_gate.py``'s existing assertions, or their direct equivalents,
pass against the MCP-tool code path" is an equivalence claim, not a request for
some tests. It is answered here by carrying that file's assertion corpus over
verbatim -- the same command strings, the same repository shapes, the same
expected verdicts -- and running it against ``src/mcp/push_gate``. The mapping is
written out in the module-level ``ASSERTION_MAP`` below so it can be read rather
than inferred, and a test requires it to name every test in that file: 23 of
them, of which 17 port verbatim, 4 carry over as stated equivalents, and 2 do
NOT carry over at all. ``TestAssertionMappingIsComplete`` pins all four numbers,
because the first two times this sentence was written from memory it was wrong
both times.

THE DIVERGENCE GUARD, AND WHY IT IS TEMPORARY BY DESIGN
-------------------------------------------------------
Porting before deleting means two implementations exist at once. ``TestNoDrift``
runs the whole corpus through BOTH and requires them to agree, so a change to
either one during the overlap window fails here rather than being discovered
after the hook is gone. When PRD FR-4 deletes ``hooks/pre_tool_enforcer/`` that
class skips itself, which is the correct end state: there is nothing left to
diverge from.

WHAT THIS MODULE DOES NOT COVER
-------------------------------
Acceptance criterion 3 -- that this lands BEFORE the hook-deletion PR -- is not
testable here. The deletion does not exist yet. What is asserted is the half
that is checkable now: the MCP tool is reachable while the hook is still
present. The other half is an obligation on whoever writes the deletion.

Windows-safe: ASCII only, no Unicode characters.
"""

import hashlib
import importlib.util as ilu
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN_ROOT = REPO_ROOT / "plugin"
HOOK_GATE_PATH = REPO_ROOT / "hooks" / "pre_tool_enforcer" / "policies" / "push_gate.py"
MCP_PACKAGE = REPO_ROOT / "src" / "mcp" / "push_gate"
MCP_POLICY_PATH = MCP_PACKAGE / "push_gate_policy.py"
MCP_SERVER_PATH = MCP_PACKAGE / "server.py"

REGISTRY_CAPABILITY = "version-push-gate"
TOOL_NAME = "check_push_allowed"

GUARDED_SETTINGS = (
    Path.home() / ".claude" / "settings.json",
    Path.home() / ".claude" / "settings.local.json",
    REPO_ROOT / ".claude" / "settings.local.json",
)

ASSERTION_MAP = {
    "TestPushDetection.test_not_treated_as_a_push": "PORTED VERBATIM -> TestPushDetection (11 cases)",
    "TestPushDetection.test_recognized_as_a_push": "PORTED VERBATIM -> TestPushDetection (11 cases)",
    "TestCommandSettlesStateBeforePush.test_self_committing_commands_are_exempt": (
        "PORTED VERBATIM -> TestCommandSettlesStateBeforePush (5 cases)"
    ),
    "TestCommandSettlesStateBeforePush.test_plain_pushes_are_still_judged": (
        "PORTED VERBATIM -> TestCommandSettlesStateBeforePush (3 cases)"
    ),
    "TestCommandSettlesStateBeforePush.test_dirty_tree_does_not_block_a_self_committing_command": (
        "PORTED VERBATIM -> TestCleanTreeGate"
    ),
    "TestCommandSettlesStateBeforePush.test_version_rule_still_applies_to_a_self_committing_command": (
        "PORTED VERBATIM -> TestVersionGate"
    ),
    "TestCommandSettlesStateBeforePush.test_pending_version_bump_satisfies_the_rule_before_it_is_committed": (
        "PORTED VERBATIM -> TestVersionGate"
    ),
    "TestVersionGate.test_branch_without_version_change_is_blocked": "PORTED VERBATIM -> TestVersionGate",
    "TestVersionGate.test_branch_with_version_change_is_allowed": "PORTED VERBATIM -> TestVersionGate",
    "TestVersionGate.test_later_commit_on_a_bumped_branch_still_allowed": "PORTED VERBATIM -> TestVersionGate",
    "TestVersionGate.test_repo_without_a_version_file_is_never_blocked": "PORTED VERBATIM -> TestVersionGate",
    "TestVersionGate.test_non_push_command_never_blocks": "PORTED VERBATIM -> TestVersionGate",
    "TestVersionGate.test_non_bash_tool_never_blocks": "EQUIVALENT -> TestVersionGate, plus the tool_name argument",
    "TestVersionGate.test_unresolvable_repo_fails_open": (
        "EQUIVALENT -> TestVersionGate, and STRENGTHENED: the MCP path additionally reports the "
        "fail-open as determination=UNDETERMINED, which the hook's two-value result could not express"
    ),
    "TestCleanTreeGate.test_modified_tracked_file_blocks": "PORTED VERBATIM -> TestCleanTreeGate",
    "TestCleanTreeGate.test_reported_paths_are_not_truncated": "PORTED VERBATIM -> TestCleanTreeGate",
    "TestCleanTreeGate.test_untracked_file_does_not_block": "PORTED VERBATIM -> TestCleanTreeGate",
    "TestCleanTreeGate.test_clean_tree_allows": "PORTED VERBATIM -> TestCleanTreeGate",
    "TestCleanTreeGate.test_dirty_repo_does_not_block_a_push_in_another_repo": "PORTED VERBATIM -> TestCleanTreeGate",
    "TestHookWiring.test_registered_in_pre_tool_enforcer": (
        "NOT CARRIED OVER. It asserts the two checks are wired into hooks/pre_tool_enforcer/core.py. "
        "The MCP equivalent is not a wiring string but reachability by name, which "
        "TestToolIsReachableByName measures by spawning the server and listing its tools."
    ),
    "TestHookWiring.test_no_longer_invoked_from_post_tool_tracker": (
        "NOT CARRIED OVER. It is a historical guard that the gates left PostToolUse in issue #249. "
        "It has no MCP analogue and remains the hook suite's business until that suite is deleted."
    ),
    "TestHookWiring.test_pre_tool_hook_exits_two_on_a_blocked_push": (
        "EQUIVALENT, NOT IDENTICAL -> TestToolIsReachableByName.test_a_blocked_push_comes_back_as_a_block. "
        "Exit code 2 is a PreToolUse contract that has no meaning over JSON-RPC. The MCP path expresses "
        "the same outcome as allowed=false with the violations listed, and DELIBERATELY not as isError."
    ),
    "TestHookWiring.test_pre_tool_hook_allows_a_command_merely_mentioning_push": (
        "EQUIVALENT -> TestToolIsReachableByName.test_a_command_merely_mentioning_push_is_allowed"
    ),
}

NOT_PUSHES = (
    'grep -n "git push" hooks/core.py',
    'grep -rn "git push blocked" hooks/',
    "echo git push",
    'echo "remember to git push later"',
    'git commit -m "chore: document git push policy"',
    "python x.py git push",
    "git pushx origin main",
    "cd /a && git status | grep push",
    "git push --dry-run",
    "git push -n",
    "git push origin --delete old",
)

REAL_PUSHES = (
    ("git push", ""),
    ("git push -u origin main", ""),
    ("git status && git push origin main", ""),
    ("git fetch; git rebase; git push --force-with-lease", ""),
    ("/usr/bin/git push", ""),
    ("GIT_TRACE=1 git push", ""),
    ("env GIT_SSH=x git push", ""),
    ("sudo git push", ""),
    ("git -c user.name=bot push", ""),
    ("cd /c/repo && git push", "/c/repo"),
    ("git -C /c/other push", "/c/other"),
)

SETTLING_COMMANDS = (
    "git add . && git commit -m x && git push",
    "git commit -qam x && git push",
    "git stash && git push",
    "git fetch && git rebase origin/main && git push",
    "git checkout -b b && git add f && git commit -m m && git push -u origin b",
)

NON_SETTLING_COMMANDS = (
    "git push",
    "git status && git push",
    "git push && git commit -m after",
)


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


policy = _load("push_gate_policy_under_test", MCP_POLICY_PATH)
server = _load("push_gate_server_under_test", MCP_SERVER_PATH)
registration = _load("mcp_registration_for_push_gate", PLUGIN_ROOT / "scripts" / "mcp_registration.py")


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

    Three files, matching the guard in ``test_uninstall_residue_attribution``:
    the user-scope ``settings.json`` and ``settings.local.json``, and the
    repository's git-tracked ``.claude/settings.local.json``.

    Yields:
        None
    """
    before = {str(path): _digest(path) for path in GUARDED_SETTINGS}
    yield
    after = {str(path): _digest(path) for path in GUARDED_SETTINGS}
    assert before == after, "a test modified a live settings file: {0} -> {1}".format(before, after)


def _git(args, cwd):
    """Run git in a directory, raising on failure.

    Args:
        args: Arguments after the git executable.
        cwd: Working directory.

    Returns:
        str: Stripped stdout.
    """
    result = subprocess.run(["git"] + args, cwd=str(cwd), capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, "git {0} failed: {1}".format(" ".join(args), result.stderr)
    return result.stdout.strip()


def _init_repo(root, with_version=True):
    """Create a git repository with a main branch and one commit.

    Args:
        root: Directory to initialise. Created if absent.
        with_version: Whether to track a VERSION file.

    Returns:
        Path: The repository root.
    """
    root.mkdir(parents=True, exist_ok=True)
    _git(["init", "-q", "-b", "main"], root)
    _git(["config", "user.email", "t@t"], root)
    _git(["config", "user.name", "t"], root)
    if with_version:
        (root / "VERSION").write_text("1.0.0\n", encoding="utf-8")
    (root / "app.py").write_text("x = 1\n", encoding="utf-8")
    _git(["add", "."], root)
    _git(["commit", "-q", "-m", "initial"], root)
    return root


@pytest.fixture
def repo(tmp_path):
    """Create a git repo with a main branch, a VERSION file and one commit.

    Args:
        tmp_path: pytest-provided temporary directory.

    Returns:
        Path: The repository root.
    """
    return _init_repo(tmp_path / "repo")


class TestPushDetection:
    """A push must be recognized by parsing, not by substring.

    Direct port of ``test_push_gate.py::TestPushDetection``, same 22 cases.
    """

    @pytest.mark.parametrize("command", NOT_PUSHES)
    def test_not_treated_as_a_push(self, command):
        assert policy.find_push_target(command) is None, command

    @pytest.mark.parametrize("command,expected", REAL_PUSHES)
    def test_recognized_as_a_push(self, command, expected):
        assert policy.find_push_target(command) == expected, command


class TestCommandSettlesStateBeforePush:
    """A command that commits before pushing must not be judged on its pre-state.

    Direct port of ``test_push_gate.py::TestCommandSettlesStateBeforePush``.
    """

    @pytest.mark.parametrize("command", SETTLING_COMMANDS)
    def test_self_committing_commands_are_exempt(self, command):
        assert policy.command_settles_state_before_push(command) is True, command

    @pytest.mark.parametrize("command", NON_SETTLING_COMMANDS)
    def test_plain_pushes_are_still_judged(self, command):
        assert policy.command_settles_state_before_push(command) is False, command


class TestVersionGate:
    """The VERSION question must be asked of the branch, not of one push.

    Direct port of ``test_push_gate.py::TestVersionGate`` and the two version
    assertions inside its ``TestCommandSettlesStateBeforePush``.
    """

    def test_branch_without_version_change_is_blocked(self, repo):
        _git(["checkout", "-q", "-b", "feature"], repo)
        (repo / "app.py").write_text("x = 2\n", encoding="utf-8")
        _git(["commit", "-qam", "change app"], repo)

        verdict = policy.evaluate_push("git -C {0} push".format(repo))

        assert verdict["allowed"] is False
        assert verdict["determination"] == policy.DETERMINATION_BLOCKED
        assert [item["rule"] for item in verdict["violations"]] == [policy.RULE_VERSION]
        assert "no VERSION change on this branch" in verdict["violations"][0]["message"]

    def test_branch_with_version_change_is_allowed(self, repo):
        _git(["checkout", "-q", "-b", "feature"], repo)
        (repo / "VERSION").write_text("1.0.1\n", encoding="utf-8")
        _git(["commit", "-qam", "bump"], repo)

        verdict = policy.evaluate_push("git -C {0} push".format(repo))

        assert verdict["allowed"] is True
        assert verdict["determination"] == policy.DETERMINATION_ALLOWED

    def test_later_commit_on_a_bumped_branch_still_allowed(self, repo):
        """The multi-commit false positive: one bump must cover the whole branch."""
        _git(["checkout", "-q", "-b", "feature"], repo)
        (repo / "VERSION").write_text("1.0.1\n", encoding="utf-8")
        _git(["commit", "-qam", "bump"], repo)
        (repo / "app.py").write_text("x = 3\n", encoding="utf-8")
        _git(["commit", "-qam", "follow-up change with no bump"], repo)

        verdict = policy.evaluate_push("git -C {0} push".format(repo))

        assert verdict["allowed"] is True, "a follow-up commit must not re-report a satisfied branch"

    def test_repo_without_a_version_file_is_never_blocked(self, tmp_path):
        """A repo that tracks no VERSION file cannot satisfy the rule, so it is exempt."""
        root = _init_repo(tmp_path / "no-version-repo", with_version=False)
        _git(["checkout", "-q", "-b", "feature"], root)
        (root / "app.py").write_text("x = 2\n", encoding="utf-8")
        _git(["commit", "-qam", "change"], root)

        verdict = policy.evaluate_push("git -C {0} push".format(root))

        assert verdict["allowed"] is True
        assert verdict["determination"] == policy.DETERMINATION_UNDETERMINED
        assert any("tracks no VERSION file" in reason for reason in verdict["undetermined"])

    def test_non_push_command_never_blocks(self, repo):
        verdict = policy.evaluate_push('grep -n "git push" x.py')

        assert verdict["push_detected"] is False
        assert verdict["allowed"] is True

    def test_non_bash_tool_never_blocks(self):
        verdict = policy.evaluate_push("git push", tool_name="Write")

        assert verdict["push_detected"] is False
        assert verdict["allowed"] is True

    def test_unresolvable_repo_fails_open_and_says_so(self, tmp_path):
        """Fail-open is preserved, and the MCP path additionally reports it.

        The hook could only answer "not blocked" here, which is the same value
        it returns for a genuinely clean push. The port keeps the verdict and
        adds the distinction.
        """
        outside = tmp_path / "not-a-repo"
        outside.mkdir()

        verdict = policy.evaluate_push("git -C {0} push".format(outside))

        assert verdict["allowed"] is True
        assert verdict["determination"] == policy.DETERMINATION_UNDETERMINED
        assert verdict["repo"] is None

    def test_version_rule_still_applies_to_a_self_committing_command(self, repo):
        """``git commit && git push`` must not be a blanket bypass of the version rule."""
        _git(["checkout", "-q", "-b", "feature"], repo)
        (repo / "app.py").write_text("x = 2\n", encoding="utf-8")
        command = "git -C {0} commit -qam change && git -C {0} push".format(repo)

        verdict = policy.evaluate_push(command)

        assert verdict["allowed"] is False
        assert [item["rule"] for item in verdict["violations"]] == [policy.RULE_VERSION]

    def test_pending_version_bump_satisfies_the_rule_before_it_is_committed(self, repo):
        """A VERSION edit waiting to be committed counts as the bump."""
        _git(["checkout", "-q", "-b", "feature"], repo)
        (repo / "app.py").write_text("x = 2\n", encoding="utf-8")
        (repo / "VERSION").write_text("1.0.1\n", encoding="utf-8")
        command = "git -C {0} add . && git -C {0} commit -m bump && git -C {0} push".format(repo)

        verdict = policy.evaluate_push(command)

        assert verdict["allowed"] is True


class TestCleanTreeGate:
    """Only tracked modifications block; untracked artifacts do not.

    Direct port of ``test_push_gate.py::TestCleanTreeGate``.
    """

    def test_modified_tracked_file_blocks(self, repo):
        (repo / "app.py").write_text("dirty\n", encoding="utf-8")

        verdict = policy.evaluate_push("git -C {0} push".format(repo))

        assert verdict["allowed"] is False
        rules = [item["rule"] for item in verdict["violations"]]
        assert policy.RULE_CLEAN_TREE in rules
        message = next(item["message"] for item in verdict["violations"] if item["rule"] == policy.RULE_CLEAN_TREE)
        assert "uncommitted changes to tracked files" in message

    def test_reported_paths_are_not_truncated(self, repo):
        """A porcelain-prefix slice used to eat the first character of the first path."""
        (repo / "app.py").write_text("dirty\n", encoding="utf-8")

        verdict = policy.evaluate_push("git -C {0} push".format(repo))
        message = next(item["message"] for item in verdict["violations"] if item["rule"] == policy.RULE_CLEAN_TREE)

        assert "app.py" in message
        assert "pp.py" not in message.replace("app.py", "")

    def test_untracked_file_does_not_block(self, repo):
        (repo / ".coverage").write_text("artifact\n", encoding="utf-8")

        verdict = policy.evaluate_push("git -C {0} push".format(repo))
        rules = [item["rule"] for item in verdict["violations"]]

        assert policy.RULE_CLEAN_TREE not in rules, "untracked artifacts must not block a push"

    def test_clean_tree_allows(self, repo):
        verdict = policy.evaluate_push("git -C {0} push".format(repo))

        assert verdict["allowed"] is True
        assert verdict["determination"] == policy.DETERMINATION_ALLOWED

    def test_dirty_repo_does_not_block_a_push_in_another_repo(self, tmp_path, repo):
        """The old gate used a session-wide file list that spanned repositories."""
        other = _init_repo(tmp_path / "other")
        (repo / "app.py").write_text("dirty in the first repo\n", encoding="utf-8")

        verdict = policy.evaluate_push("git -C {0} push".format(other))

        assert verdict["allowed"] is True, "a dirty unrelated repo must not block this push"

    def test_dirty_tree_does_not_block_a_self_committing_command(self, repo):
        (repo / "app.py").write_text("dirty\n", encoding="utf-8")
        command = "git -C {0} add . && git -C {0} commit -m x && git -C {0} push".format(repo)

        verdict = policy.evaluate_push(command)
        rules = [item["rule"] for item in verdict["violations"]]

        assert policy.RULE_CLEAN_TREE not in rules


class TestSpecificityBothDirections:
    """A gate that refuses everything is not a gate, and neither is one that never does."""

    def test_both_rules_can_fire_together(self, repo):
        """POSITIVE: two independent refusals are both reported, not just the first."""
        _git(["checkout", "-q", "-b", "feature"], repo)
        (repo / "app.py").write_text("x = 2\n", encoding="utf-8")
        _git(["commit", "-qam", "change app"], repo)
        (repo / "app.py").write_text("and now dirty\n", encoding="utf-8")

        verdict = policy.evaluate_push("git -C {0} push".format(repo))
        rules = sorted(item["rule"] for item in verdict["violations"])

        assert rules == sorted([policy.RULE_VERSION, policy.RULE_CLEAN_TREE])

    def test_a_fully_compliant_push_is_permitted(self, repo):
        """SPECIFICITY: the compliant case must pass, or the gate discriminates nothing."""
        _git(["checkout", "-q", "-b", "feature"], repo)
        (repo / "VERSION").write_text("1.0.1\n", encoding="utf-8")
        (repo / "app.py").write_text("x = 2\n", encoding="utf-8")
        _git(["commit", "-qam", "bump and change"], repo)

        verdict = policy.evaluate_push("git -C {0} push".format(repo))

        assert verdict["allowed"] is True
        assert verdict["violations"] == []
        assert verdict["undetermined"] == []
        assert verdict["determination"] == policy.DETERMINATION_ALLOWED

    def test_the_caller_cwd_argument_actually_selects_the_repository(self, tmp_path):
        """The one behaviour that could not be ported unchanged, proved rather than asserted.

        The hook resolved a bare ``git push`` against ``os.getcwd()``, which was
        the caller's directory because the hook ran inside the caller. A server
        is a separate process, so the same fallback would silently judge the
        wrong repository. This proves the explicit argument reaches the right one.
        """
        clean = _init_repo(tmp_path / "clean")
        _git(["checkout", "-q", "-b", "feature"], clean)
        (clean / "VERSION").write_text("1.0.1\n", encoding="utf-8")
        _git(["commit", "-qam", "bump"], clean)

        dirty = _init_repo(tmp_path / "dirty")
        (dirty / "app.py").write_text("dirty\n", encoding="utf-8")

        assert policy.evaluate_push("git push", caller_cwd=str(clean))["allowed"] is True
        assert policy.evaluate_push("git push", caller_cwd=str(dirty))["allowed"] is False
        assert policy.evaluate_push("git push", caller_cwd=str(dirty))["cwd_source"] == "caller"
        assert policy.evaluate_push("git push")["cwd_source"] == "server-process"


class TestNoDrift:
    """Both implementations must agree while both exist.

    The port creates a window in which two copies of the same rules are live.
    This class is the mechanical detector for that window. It disappears with
    the hook, which is the correct end state rather than lost coverage.
    """

    @staticmethod
    def _hook():
        """Load the hook implementation, or skip when PRD FR-4 has removed it.

        Returns:
            module: The hook's push_gate module.
        """
        if not HOOK_GATE_PATH.is_file():
            pytest.skip("hooks/pre_tool_enforcer/policies/push_gate.py is gone (PRD FR-4); nothing left to diverge")
        return _load("push_gate_hook_for_drift", HOOK_GATE_PATH)

    @pytest.mark.parametrize("command", NOT_PUSHES + tuple(item[0] for item in REAL_PUSHES))
    def test_push_detection_agrees(self, command):
        assert self._hook().find_push_target(command) == policy.find_push_target(command), command

    @pytest.mark.parametrize("command", SETTLING_COMMANDS + NON_SETTLING_COMMANDS)
    def test_settling_detection_agrees(self, command):
        hook = self._hook()
        assert hook.command_settles_state_before_push(command) == policy.command_settles_state_before_push(command)

    def test_version_rule_agrees_on_a_blocked_branch(self, repo):
        _git(["checkout", "-q", "-b", "feature"], repo)
        (repo / "app.py").write_text("x = 2\n", encoding="utf-8")
        _git(["commit", "-qam", "change app"], repo)
        payload = {"command": "git -C {0} push".format(repo)}

        assert self._hook().check_push_version("Bash", payload) == policy.check_push_version("Bash", payload)

    def test_clean_tree_rule_agrees_on_a_dirty_tree(self, repo):
        (repo / "app.py").write_text("dirty\n", encoding="utf-8")
        payload = {"command": "git -C {0} push".format(repo)}

        assert self._hook().check_push_clean_tree("Bash", payload) == policy.check_push_clean_tree("Bash", payload)

    def test_negative_the_drift_detector_can_actually_fail(self):
        """A comparison that can never disagree proves nothing about agreement."""
        hook = self._hook()
        mutated = "git pushed nothing"

        assert hook.find_push_target(mutated) == policy.find_push_target(mutated)
        assert hook.find_push_target("git push") != policy.find_push_target("git pushx")


def _spawn(lines, timeout=90):
    """Run the push-gate server against a scripted sequence of JSON-RPC lines.

    Args:
        lines: Message dictionaries to send, in order.
        timeout: Seconds to wait for the process to exit.

    Returns:
        list: Parsed response objects, in the order received.
    """
    process = subprocess.Popen(
        [sys.executable, str(MCP_SERVER_PATH)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
    )
    payload = "\n".join(json.dumps(line) for line in lines) + "\n"
    stdout, stderr = process.communicate(payload, timeout=timeout)
    assert process.returncode == 0, stderr
    return [json.loads(line) for line in stdout.splitlines() if line.strip()]


def _initialised(*requests):
    """Build a fully handshaken message sequence ending in the given requests.

    Args:
        requests: Request dictionaries to append after the handshake.

    Returns:
        list: The full message sequence.
    """
    return [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18"}},
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
    ] + list(requests)


def _answer(responses, request_id):
    """Return the response carrying a given id.

    Args:
        responses: Parsed response objects.
        request_id: The id to find.

    Returns:
        dict: The matching response.
    """
    for response in responses:
        if response.get("id") == request_id:
            return response
    raise AssertionError("no response with id {0}: {1}".format(request_id, responses))


class TestToolIsReachableByName:
    """AC 1: the logic is reachable as an MCP tool callable by name.

    Measured by spawning the real server process and driving a real JSON-RPC
    lifecycle against it, never by importing the module and asserting it exists.
    """

    def test_the_tool_is_listed_under_its_name(self):
        responses = _spawn(_initialised({"jsonrpc": "2.0", "id": 2, "method": "tools/list"}))
        tools = _answer(responses, 2)["result"]["tools"]

        assert [tool["name"] for tool in tools] == [TOOL_NAME]

    def test_the_descriptor_declares_every_annotation(self):
        """An unannotated tool sits at the least-safe point of the four-hint lattice."""
        responses = _spawn(_initialised({"jsonrpc": "2.0", "id": 2, "method": "tools/list"}))
        annotations = _answer(responses, 2)["result"]["tools"][0]["annotations"]

        assert annotations == {
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        }

    def test_every_input_property_carries_a_description(self):
        responses = _spawn(_initialised({"jsonrpc": "2.0", "id": 2, "method": "tools/list"}))
        schema = _answer(responses, 2)["result"]["tools"][0]["inputSchema"]

        assert schema["required"] == ["command"]
        for name, spec in schema["properties"].items():
            assert spec.get("description"), name

    def test_a_blocked_push_comes_back_as_a_block(self, repo):
        """The MCP equivalent of the hook's exit code 2.

        A refusal is a successful answer, so it arrives as a result with
        ``isError`` false and the refusal in the payload -- not as an error.
        """
        (repo / "app.py").write_text("dirty\n", encoding="utf-8")
        call = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": TOOL_NAME, "arguments": {"command": "git -C {0} push".format(repo)}},
        }
        result = _answer(_spawn(_initialised(call)), 2)["result"]
        structured = result["structuredContent"]
        messages = " ".join(item["message"] for item in structured["violations"])

        assert result["isError"] is False
        assert structured["allowed"] is False
        assert structured["determination"] == "BLOCKED"
        assert "uncommitted changes to tracked files" in messages
        assert "clean-tree" in result["content"][0]["text"]

    def test_a_command_merely_mentioning_push_is_allowed(self):
        call = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": TOOL_NAME, "arguments": {"command": 'grep -rn "git push" hooks/'}},
        }
        result = _answer(_spawn(_initialised(call)), 2)["result"]

        assert result["structuredContent"]["push_detected"] is False
        assert result["structuredContent"]["allowed"] is True

    def test_a_compliant_push_is_allowed_over_the_wire(self, repo):
        """SPECIFICITY over the protocol: the tool is not a constant refusal."""
        _git(["checkout", "-q", "-b", "feature"], repo)
        (repo / "VERSION").write_text("1.0.1\n", encoding="utf-8")
        _git(["commit", "-qam", "bump"], repo)
        call = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": TOOL_NAME, "arguments": {"command": "git -C {0} push".format(repo)}},
        }
        result = _answer(_spawn(_initialised(call)), 2)["result"]

        assert result["structuredContent"]["allowed"] is True
        assert result["structuredContent"]["determination"] == "ALLOWED"


class TestLifecycleGate:
    """No tool call is answered before the initialized notification has fired."""

    def test_a_tool_call_before_initialized_is_refused(self, repo):
        """NEGATIVE: the gate can refuse, and the refusal is a protocol error."""
        (repo / "app.py").write_text("dirty\n", encoding="utf-8")
        call = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": TOOL_NAME, "arguments": {"command": "git -C {0} push".format(repo)}},
        }
        responses = _spawn(
            [
                {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18"}},
                call,
            ]
        )
        answer = _answer(responses, 2)

        assert "result" not in answer
        assert answer["error"]["code"] == -32002

    def test_tools_list_before_initialized_is_refused(self):
        responses = _spawn(
            [
                {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18"}},
                {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
            ]
        )

        assert _answer(responses, 2)["error"]["code"] == -32002

    def test_specificity_the_same_call_succeeds_once_initialized(self):
        """The gate must refuse only the premature call, not the method itself."""
        responses = _spawn(_initialised({"jsonrpc": "2.0", "id": 2, "method": "tools/list"}))

        assert "result" in _answer(responses, 2)

    def test_a_second_initialize_is_a_protocol_violation(self):
        responses = _spawn(
            [
                {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18"}},
                {"jsonrpc": "2.0", "id": 2, "method": "initialize", "params": {"protocolVersion": "2025-06-18"}},
            ]
        )

        assert _answer(responses, 2)["error"]["code"] == -32600


class TestProtocolErrorsVersusBusinessOutcomes:
    """Malformed calls are protocol errors; refusals are results."""

    def test_a_missing_command_argument_is_a_protocol_error(self):
        call = {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": TOOL_NAME, "arguments": {}}}

        assert _answer(_spawn(_initialised(call)), 2)["error"]["code"] == -32602

    def test_a_non_string_command_argument_is_a_protocol_error(self):
        call = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": TOOL_NAME, "arguments": {"command": 17}},
        }

        assert _answer(_spawn(_initialised(call)), 2)["error"]["code"] == -32602

    def test_an_unknown_tool_name_is_a_protocol_error(self):
        call = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": "check_everything", "arguments": {"command": "git push"}},
        }

        assert _answer(_spawn(_initialised(call)), 2)["error"]["code"] == -32602

    def test_an_unknown_method_is_a_protocol_error(self):
        responses = _spawn(_initialised({"jsonrpc": "2.0", "id": 2, "method": "resources/list"}))

        assert _answer(responses, 2)["error"]["code"] == -32601

    def test_specificity_a_refusal_is_not_encoded_as_an_error(self, repo):
        """The distinction has to run both ways or it is not a distinction."""
        (repo / "app.py").write_text("dirty\n", encoding="utf-8")
        call = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": TOOL_NAME, "arguments": {"command": "git -C {0} push".format(repo)}},
        }
        answer = _answer(_spawn(_initialised(call)), 2)

        assert "error" not in answer
        assert answer["result"]["isError"] is False


class TestRegistrationPath:
    """The catalogue must now be able to register this server."""

    def test_the_catalogue_no_longer_marks_the_gate_unbuilt(self):
        servers = registration.load_registry(PLUGIN_ROOT)
        gate = next(item for item in servers if item["capability"] == REGISTRY_CAPABILITY)

        assert "not_built_yet" not in gate, "V2-024 has landed; the catalogue must stop reporting it unavailable"
        assert gate["id"] == "push-gate"

    def test_the_catalogue_entry_points_at_a_file_that_exists(self):
        """The path register-mcp would write must be a real, spawnable file.

        Resolved through the shipped ``server_entry_path`` against this
        repository's own parent, which is the server root a real install uses.
        """
        servers = registration.load_registry(PLUGIN_ROOT)
        gate = next(item for item in servers if item["capability"] == REGISTRY_CAPABILITY)
        entry = registration.server_entry_path(gate, REPO_ROOT.parent)

        assert entry.resolve() == MCP_SERVER_PATH.resolve(), entry

    def test_registering_makes_the_capability_reachable(self, tmp_path):
        """AC 1 end to end: catalogue -> settings entry -> spawn -> tool listed.

        The scratch server root mirrors the catalogue's declared layout and
        carries a real copy of the server, so what is spawned is what the
        settings file names rather than a stand-in.
        """
        servers = registration.load_registry(PLUGIN_ROOT)
        gate = next(item for item in servers if item["capability"] == REGISTRY_CAPABILITY)
        target = tmp_path / "servers" / gate["repo"] / Path(gate["entry"]).parent
        target.mkdir(parents=True)
        for name in ("server.py", "push_gate_policy.py", "__init__.py"):
            (target / name).write_text((MCP_PACKAGE / name).read_text(encoding="utf-8"), encoding="utf-8")

        settings_path = tmp_path / "settings.json"
        settings_path.write_text(json.dumps({"model": "opus"}, indent=2) + "\n", encoding="utf-8")
        status = registration.main(
            [
                "--plugin-root",
                str(PLUGIN_ROOT),
                "--settings",
                str(settings_path),
                "--ledger",
                str(tmp_path / "ledger.json"),
                "register",
                "--server-root",
                str(tmp_path / "servers"),
                "--capability",
                REGISTRY_CAPABILITY,
            ]
        )

        assert status == registration.EXIT_OK
        entry = json.loads(settings_path.read_text(encoding="utf-8"))["mcpServers"]["push-gate"]
        command = [sys.executable] + list(entry["args"])
        process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        )
        payload = "\n".join(
            json.dumps(line) for line in _initialised({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
        )
        stdout, stderr = process.communicate(payload + "\n", timeout=90)
        responses = [json.loads(line) for line in stdout.splitlines() if line.strip()]

        assert process.returncode == 0, stderr
        assert [tool["name"] for tool in _answer(responses, 2)["result"]["tools"]] == [TOOL_NAME]

    def test_negative_a_repointed_entry_stops_being_reachable(self, tmp_path):
        """The reachability probe is not a constant True."""
        absent = tmp_path / "absent" / "server.py"
        process = subprocess.Popen(
            [sys.executable, str(absent)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
        )
        _stdout, _stderr = process.communicate("", timeout=90)

        assert process.returncode != 0


class TestAssertionMappingIsComplete:
    """The equivalence claim must name every assertion, including the gaps."""

    def test_every_hook_test_is_accounted_for(self):
        """A mapping that silently omits a case is the failure mode AC 2 guards against."""
        if not HOOK_GATE_PATH.is_file():
            pytest.skip("the hook suite is gone (PRD FR-4); the mapping it describes no longer has a source")
        source = (REPO_ROOT / "tests" / "test_push_gate.py").read_text(encoding="utf-8")
        current_class = None
        found = set()
        for line in source.splitlines():
            stripped = line.strip()
            if stripped.startswith("class Test"):
                current_class = stripped[len("class ") :].split("(")[0].split(":")[0]
            elif stripped.startswith("def test_") and current_class:
                found.add("{0}.{1}".format(current_class, stripped[len("def ") :].split("(")[0]))

        assert found, "no tests were discovered in tests/test_push_gate.py"
        assert found == set(ASSERTION_MAP), "ASSERTION_MAP is stale: {0}".format(
            found.symmetric_difference(ASSERTION_MAP)
        )

    def test_the_uncarried_assertions_are_named_as_such(self):
        """The gap is stated, not left for a reader to discover."""
        uncarried = [key for key, value in ASSERTION_MAP.items() if value.startswith("NOT CARRIED OVER")]

        assert sorted(uncarried) == [
            "TestHookWiring.test_no_longer_invoked_from_post_tool_tracker",
            "TestHookWiring.test_registered_in_pre_tool_enforcer",
        ]

    def test_the_counts_in_this_module_docstring_are_pinned(self):
        """The docstring's four numbers were wrong twice before being measured.

        Pinning them here means the next person to change the mapping is told
        the prose is stale rather than leaving a plausible-looking count in
        place, which is the failure mode this effort has hit repeatedly.
        """
        verbatim = [key for key, value in ASSERTION_MAP.items() if value.startswith("PORTED VERBATIM")]
        equivalent = [key for key, value in ASSERTION_MAP.items() if value.startswith("EQUIVALENT")]
        uncarried = [key for key, value in ASSERTION_MAP.items() if value.startswith("NOT CARRIED OVER")]

        assert (len(ASSERTION_MAP), len(verbatim), len(equivalent), len(uncarried)) == (23, 17, 4, 2)
        assert len(verbatim) + len(equivalent) + len(uncarried) == len(ASSERTION_MAP), "a value uses an unknown prefix"
        assert "17 port verbatim, 4 carry over as stated equivalents, and 2 do" in __doc__

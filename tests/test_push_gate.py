"""Tests for the PreToolUse push gates (issue #249).

The gates they replace lived in PostToolUse and had four defects:

1. PostToolUse runs after the tool finishes, so a block reported a push that had
   already reached the remote.
2. The push was detected with ``"git push" in command``, so a grep for that text,
   an echo, or a commit message mentioning it all tripped the gate.
3. The VERSION question was answered from a session-wide list of edited files that
   spanned repositories and included scratchpad paths.
4. On a multi-commit branch the answer changed per push, so a follow-up commit
   re-reported a violation the branch already satisfied.

Windows-safe: ASCII only, no Unicode characters.
"""

import importlib.util as ilu
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
GATE_PATH = REPO_ROOT / "hooks" / "pre_tool_enforcer" / "policies" / "push_gate.py"


def _load_gate():
    """Load push_gate.py by path, since the policies package is loaded dynamically.

    Returns:
        module: The loaded push_gate module.
    """
    spec = ilu.spec_from_file_location("push_gate_under_test", str(GATE_PATH))
    module = ilu.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gate = _load_gate()


def _git(args, cwd):
    """Run git in a directory, raising on failure.

    Args:
        args: Arguments after the git executable.
        cwd: Working directory.

    Returns:
        str: Stripped stdout.
    """
    result = subprocess.run(["git"] + args, cwd=str(cwd), capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, "git {} failed: {}".format(" ".join(args), result.stderr)
    return result.stdout.strip()


@pytest.fixture
def repo(tmp_path):
    """Create a git repo with a main branch and one commit.

    Yields:
        Path: The repository root.
    """
    root = tmp_path / "repo"
    root.mkdir()
    _git(["init", "-q", "-b", "main"], root)
    _git(["config", "user.email", "t@t"], root)
    _git(["config", "user.name", "t"], root)
    (root / "VERSION").write_text("1.0.0\n", encoding="utf-8")
    (root / "app.py").write_text("x = 1\n", encoding="utf-8")
    _git(["add", "."], root)
    _git(["commit", "-q", "-m", "initial"], root)
    yield root


class TestPushDetection:
    """A push must be recognized by parsing, not by substring."""

    @pytest.mark.parametrize(
        "command",
        [
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
        ],
    )
    def test_not_treated_as_a_push(self, command):
        assert gate.find_push_target(command) is None, command

    @pytest.mark.parametrize(
        "command,expected",
        [
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
        ],
    )
    def test_recognized_as_a_push(self, command, expected):
        assert gate.find_push_target(command) == expected, command


class TestCommandSettlesStateBeforePush:
    """A command that commits before pushing must not be judged on its pre-state.

    PreToolUse can only see the repository as it is before the command runs, so a
    chained ``git commit && git push`` looks dirty and version-less at gate time
    even though the push that eventually happens is clean and bumped. Blocking
    there is unactionable: committing first is exactly what the user already wrote.
    """

    @pytest.mark.parametrize(
        "command",
        [
            "git add . && git commit -m x && git push",
            "git commit -qam x && git push",
            "git stash && git push",
            "git fetch && git rebase origin/main && git push",
            "git checkout -b b && git add f && git commit -m m && git push -u origin b",
        ],
    )
    def test_self_committing_commands_are_exempt(self, command):
        assert gate.command_settles_state_before_push(command) is True, command

    @pytest.mark.parametrize(
        "command",
        [
            "git push",
            "git status && git push",
            "git push && git commit -m after",
        ],
    )
    def test_plain_pushes_are_still_judged(self, command):
        assert gate.command_settles_state_before_push(command) is False, command

    def test_dirty_tree_does_not_block_a_self_committing_command(self, repo):
        (repo / "app.py").write_text("dirty\n", encoding="utf-8")
        command = "git -C {0} add . && git -C {0} commit -m x && git -C {0} push".format(repo)
        assert gate.check_push_clean_tree("Bash", {"command": command})[0] is False

    def test_version_rule_also_skipped_for_a_self_committing_command(self, repo):
        _git(["checkout", "-q", "-b", "feature"], repo)
        (repo / "app.py").write_text("x = 2\n", encoding="utf-8")
        command = "git -C {0} commit -qam change && git -C {0} push".format(repo)
        assert gate.check_push_version("Bash", {"command": command})[0] is False


class TestVersionGate:
    """The VERSION question must be asked of the branch, not of one push."""

    def test_branch_without_version_change_is_blocked(self, repo):
        _git(["checkout", "-q", "-b", "feature"], repo)
        (repo / "app.py").write_text("x = 2\n", encoding="utf-8")
        _git(["commit", "-qam", "change app"], repo)

        blocked, msg = gate.check_push_version("Bash", {"command": "git -C {} push".format(repo)})
        assert blocked is True
        assert "no VERSION change on this branch" in msg

    def test_branch_with_version_change_is_allowed(self, repo):
        _git(["checkout", "-q", "-b", "feature"], repo)
        (repo / "VERSION").write_text("1.0.1\n", encoding="utf-8")
        _git(["commit", "-qam", "bump"], repo)

        blocked, _ = gate.check_push_version("Bash", {"command": "git -C {} push".format(repo)})
        assert blocked is False

    def test_later_commit_on_a_bumped_branch_still_allowed(self, repo):
        """The multi-commit false positive: one bump must cover the whole branch."""
        _git(["checkout", "-q", "-b", "feature"], repo)
        (repo / "VERSION").write_text("1.0.1\n", encoding="utf-8")
        _git(["commit", "-qam", "bump"], repo)
        (repo / "app.py").write_text("x = 3\n", encoding="utf-8")
        _git(["commit", "-qam", "follow-up change with no bump"], repo)

        blocked, _ = gate.check_push_version("Bash", {"command": "git -C {} push".format(repo)})
        assert blocked is False, "a follow-up commit must not re-report a satisfied branch"

    def test_repo_without_a_version_file_is_never_blocked(self, tmp_path):
        """Only 4 of the 25 repos in this workspace track a VERSION file.

        Blocking the rest would be unsatisfiable: there is no file to bump, so the
        gate must recognize that the repo does not participate in the policy.
        """
        root = tmp_path / "no-version-repo"
        root.mkdir()
        _git(["init", "-q", "-b", "main"], root)
        _git(["config", "user.email", "t@t"], root)
        _git(["config", "user.name", "t"], root)
        (root / "server.py").write_text("x = 1\n", encoding="utf-8")
        _git(["add", "."], root)
        _git(["commit", "-q", "-m", "initial"], root)
        _git(["checkout", "-q", "-b", "feature"], root)
        (root / "server.py").write_text("x = 2\n", encoding="utf-8")
        _git(["commit", "-qam", "change"], root)

        blocked, _ = gate.check_push_version("Bash", {"command": "git -C {} push".format(root)})
        assert blocked is False, "a repo with no VERSION file must not be blocked"

    def test_non_push_command_never_blocks(self, repo):
        blocked, _ = gate.check_push_version("Bash", {"command": 'grep -n "git push" x.py'})
        assert blocked is False

    def test_non_bash_tool_never_blocks(self):
        assert gate.check_push_version("Write", {"file_path": "x"})[0] is False

    def test_unresolvable_repo_fails_open(self, tmp_path):
        outside = tmp_path / "not-a-repo"
        outside.mkdir()
        blocked, _ = gate.check_push_version("Bash", {"command": "git -C {} push".format(outside)})
        assert blocked is False


class TestCleanTreeGate:
    """Only tracked modifications block; untracked artifacts do not."""

    def test_modified_tracked_file_blocks(self, repo):
        (repo / "app.py").write_text("dirty\n", encoding="utf-8")
        blocked, msg = gate.check_push_clean_tree("Bash", {"command": "git -C {} push".format(repo)})
        assert blocked is True
        assert "uncommitted changes to tracked files" in msg

    def test_reported_paths_are_not_truncated(self, repo):
        """A porcelain-prefix slice used to eat the first character of the first path."""
        (repo / "app.py").write_text("dirty\n", encoding="utf-8")
        _, msg = gate.check_push_clean_tree("Bash", {"command": "git -C {} push".format(repo)})
        assert "app.py" in msg
        assert "pp.py" not in msg.replace("app.py", "")

    def test_untracked_file_does_not_block(self, repo):
        (repo / ".coverage").write_text("artifact\n", encoding="utf-8")
        blocked, _ = gate.check_push_clean_tree("Bash", {"command": "git -C {} push".format(repo)})
        assert blocked is False, "untracked artifacts must not block a push"

    def test_clean_tree_allows(self, repo):
        blocked, _ = gate.check_push_clean_tree("Bash", {"command": "git -C {} push".format(repo)})
        assert blocked is False

    def test_dirty_repo_does_not_block_a_push_in_another_repo(self, tmp_path, repo):
        """The old gate used a session-wide file list that spanned repositories."""
        other = tmp_path / "other"
        other.mkdir()
        _git(["init", "-q", "-b", "main"], other)
        _git(["config", "user.email", "t@t"], other)
        _git(["config", "user.name", "t"], other)
        (other / "VERSION").write_text("2.0.0\n", encoding="utf-8")
        _git(["add", "."], other)
        _git(["commit", "-q", "-m", "initial"], other)

        (repo / "app.py").write_text("dirty in the first repo\n", encoding="utf-8")

        blocked, _ = gate.check_push_clean_tree("Bash", {"command": "git -C {} push".format(other)})
        assert blocked is False, "a dirty unrelated repo must not block this push"


class TestHookWiring:
    """The gates must be registered on PreToolUse and gone from PostToolUse."""

    def test_registered_in_pre_tool_enforcer(self):
        source = (REPO_ROOT / "hooks" / "pre_tool_enforcer" / "core.py").read_text(encoding="utf-8")
        assert '("push_version", _new_check_push_version)' in source
        assert '("push_clean_tree", _new_check_push_clean_tree)' in source

    def test_no_longer_invoked_from_post_tool_tracker(self):
        source = (REPO_ROOT / "hooks" / "post_tool_tracker" / "core.py").read_text(encoding="utf-8")
        assert "check_level_3_10_version_release(tool_name" not in source
        assert "_block, _msg = check_uncommitted_before_push(" not in source

    def test_pre_tool_hook_exits_two_on_a_blocked_push(self, repo):
        """End to end through the real hook entry point, so wiring is covered."""
        (repo / "app.py").write_text("dirty\n", encoding="utf-8")
        payload = '{{"session_id":"t","tool_name":"Bash","tool_input":{{"command":"git -C {} push"}}}}'.format(
            str(repo).replace("\\", "/")
        )
        result = subprocess.run(
            [sys.executable, str(REPO_ROOT / "hooks" / "pre-tool-enforcer.py")],
            input=payload,
            capture_output=True,
            text=True,
            timeout=120,
            cwd=str(REPO_ROOT),
        )
        assert result.returncode == 2, result.stdout + result.stderr

    def test_pre_tool_hook_allows_a_command_merely_mentioning_push(self):
        payload = '{"session_id":"t","tool_name":"Bash","tool_input":{"command":"grep -rn \\"git push\\" hooks/"}}'
        result = subprocess.run(
            [sys.executable, str(REPO_ROOT / "hooks" / "pre-tool-enforcer.py")],
            input=payload,
            capture_output=True,
            text=True,
            timeout=120,
            cwd=str(REPO_ROOT),
        )
        assert result.returncode == 0, result.stdout + result.stderr

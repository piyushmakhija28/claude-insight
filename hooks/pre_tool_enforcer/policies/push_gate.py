# pre_tool_enforcer/policies/push_gate.py
# Pre-push gates: VERSION bump present on the branch, tracked changes committed.
# Windows-safe: ASCII only, no Unicode characters.
"""Gate ``git push`` before it runs.

These checks used to live in the PostToolUse tracker, where they could not work:

- PostToolUse fires *after* the tool completes, so the push had already reached the
  remote by the time the gate printed "git push blocked". It never prevented anything.
- The push was detected with ``"git push" in command``, so any command merely
  containing that text -- a grep for the string, an echo, a commit message -- tripped
  the gate.
- The VERSION question was asked against a globally accumulated list of every file
  edited in the session, which spanned repos and even included scratchpad paths, so
  it was answered from the wrong set of files.
- On a branch with more than one commit the answer changed per push: bump VERSION,
  push, then any follow-up push reported a violation again even though the branch
  already carried the bump.

Here the same two rules are enforced where a non-zero result actually stops the
push, the command is parsed rather than substring-matched, and both questions are
asked of the specific repository being pushed.

Every check fails open: any error resolving git state allows the push, because a
gate that cannot determine the answer must not stand in the way.
"""

import os
import shlex
import subprocess
import sys

_GIT_NAMES = {"git", "git.exe"}

# Global options that take a value, so the subcommand is not the token after them.
_GIT_OPTS_WITH_VALUE = {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path"}

# A push carrying any of these is not publishing commits, so neither rule applies.
_EXEMPT_PUSH_FLAGS = {"--dry-run", "-n", "--delete", "-d", "--tags"}

_SEPARATORS = ("&&", "||", ";", "|", "\n")

_VERSION_NAMES = {"version", "version.txt"}

_GIT_TIMEOUT_SEC = 10


def _split_segments(command):
    """Split a shell command into separately executed segments.

    Args:
        command: Raw command string from the tool input.

    Returns:
        list[str]: Segment strings, in order.
    """
    segments = [command]
    for sep in _SEPARATORS:
        nxt = []
        for seg in segments:
            nxt.extend(seg.split(sep))
        segments = nxt
    return [s.strip() for s in segments if s.strip()]


def _strip_quotes(token):
    """Remove one matching pair of surrounding quotes from a token.

    Args:
        token: Token as produced by non-posix shlex.

    Returns:
        str: Token without its outer quotes.
    """
    if len(token) >= 2 and token[0] == token[-1] and token[0] in ("'", '"'):
        return token[1:-1]
    return token


def _tokenize(segment):
    """Tokenize one command segment, tolerating unbalanced quotes.

    Non-posix mode is used on Windows because posix mode treats a backslash as an
    escape character, which turns ``git -C C:\\path\\repo push`` into
    ``C:pathrepo`` -- the directory then fails to resolve and the gate silently
    allows the push. Non-posix mode keeps backslashes but leaves quotes attached
    to tokens, so they are stripped afterwards.

    Args:
        segment: A single command segment.

    Returns:
        list[str]: Tokens, or an empty list when the segment cannot be parsed.
    """
    posix = sys.platform != "win32"
    for attempt in (posix, not posix):
        try:
            tokens = shlex.split(segment, posix=attempt)
        except ValueError:
            continue
        return tokens if attempt else [_strip_quotes(t) for t in tokens]
    return []


def _command_index(tokens):
    """Return the index of a segment's actual command token.

    Skips leading ``VAR=value`` assignments and wrappers such as ``env`` or
    ``sudo``. Only this position may be treated as the program being run: scanning
    every token instead would read ``echo git push`` as a push, since ``git`` and
    ``push`` appear as bare arguments there.

    Args:
        tokens: Tokens of a single command segment.

    Returns:
        int: Index of the command token, or -1 when there is none.
    """
    wrappers = {"env", "sudo", "nohup", "time", "command", "exec", "nice", "stdbuf"}
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if "=" in token and not token.startswith("-") and "/" not in token.split("=", 1)[0]:
            index += 1
            continue
        if os.path.basename(token).lower() in wrappers:
            index += 1
            continue
        return index
    return -1


def _git_subcommand(tokens):
    """Return the git subcommand and the -C directory for a token list.

    Args:
        tokens: Tokens of a single command segment.

    Returns:
        tuple[str, str]: (subcommand, -C directory). Both "" when not a git call.
    """
    index = _command_index(tokens)
    if index < 0 or os.path.basename(tokens[index]).lower() not in _GIT_NAMES:
        return "", ""

    directory = ""
    cursor = index + 1
    while cursor < len(tokens):
        token_at = tokens[cursor]
        if token_at in _GIT_OPTS_WITH_VALUE:
            if token_at == "-C" and cursor + 1 < len(tokens):
                directory = tokens[cursor + 1]
            cursor += 2
            continue
        if token_at.startswith("-"):
            cursor += 1
            continue
        return token_at, directory
    return "", directory


def find_push_target(command):
    """Locate a real ``git push`` in a command and the directory it runs in.

    Handles the common ``cd <dir> && git push`` shape by tracking cd targets across
    segments, and honors ``git -C <dir>``.

    Args:
        command: Raw command string.

    Returns:
        str or None: Directory the push runs in ("" meaning the hook's own cwd), or
            None when the command contains no push that publishes commits.
    """
    cwd = ""
    for segment in _split_segments(command):
        tokens = _tokenize(segment)
        if not tokens:
            continue

        if os.path.basename(tokens[0]).lower() in ("cd", "chdir") and len(tokens) > 1:
            cwd = tokens[1]
            continue

        subcommand, directory = _git_subcommand(tokens)
        if subcommand != "push":
            continue
        if any(flag in tokens for flag in _EXEMPT_PUSH_FLAGS):
            continue
        return directory or cwd
    return None


def _git(args, cwd):
    """Run a git command and return its stdout, or None on any failure.

    Args:
        args: Argument list after the git executable.
        cwd: Working directory.

    Returns:
        str or None: Stripped stdout, or None when git failed.
    """
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=cwd or None,
            capture_output=True,
            text=True,
            timeout=_GIT_TIMEOUT_SEC,
        )
    except Exception:
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def _repo_root(cwd):
    """Resolve the repository root for a directory.

    Args:
        cwd: Directory the push runs in; "" means the hook's own cwd.

    Returns:
        str or None: Absolute repo root, or None when not inside a repo.
    """
    expanded = os.path.expanduser(cwd) if cwd else os.getcwd()
    if not os.path.isdir(expanded):
        return None
    return _git(["rev-parse", "--show-toplevel"], expanded)


def _branch_files(repo):
    """List files the current branch changes relative to its merge base.

    Asking about the branch rather than the individual push is what stops a
    follow-up commit from re-reporting a violation the branch already satisfied.

    Args:
        repo: Repository root.

    Returns:
        list[str] or None: Changed paths, or None when it cannot be determined.
    """
    head = _git(["rev-parse", "--abbrev-ref", "HEAD"], repo)
    if head is None:
        return None

    base = None
    for ref in ("origin/main", "origin/master", "main", "master"):
        base = _git(["merge-base", ref, "HEAD"], repo)
        if base:
            break

    if not base or base == _git(["rev-parse", "HEAD"], repo):
        # Nothing on top of the base (or no base found): fall back to the last
        # commit, which is the only thing this push can be publishing.
        out = _git(["diff", "--name-only", "HEAD~1", "HEAD"], repo)
        return [] if out is None else [line for line in out.splitlines() if line.strip()]

    out = _git(["diff", "--name-only", base, "HEAD"], repo)
    if out is None:
        return None
    return [line for line in out.splitlines() if line.strip()]


def _repo_tracks_a_version_file(repo):
    """Return True when the repo participates in the version-release policy.

    Only a repo that actually tracks a VERSION file can satisfy a "bump VERSION"
    rule. Of the repos in this workspace only a handful do, so without this check
    the gate would block every push in the rest of them permanently, with no way
    to comply short of inventing a file the project never had.

    Args:
        repo: Repository root.

    Returns:
        bool: True when a VERSION file is tracked at the repo root.
    """
    out = _git(["ls-files", "--", "VERSION", "version.txt"], repo)
    return bool(out)


def _has_version_change(paths):
    """Return True when a VERSION file appears among the given paths.

    Args:
        paths: Repo-relative paths.

    Returns:
        bool: True when one of them is a VERSION file.
    """
    for path in paths:
        if os.path.basename(path.strip()).lower() in _VERSION_NAMES:
            return True
    return False


def _modified_tracked_files(repo):
    """List tracked files with staged or unstaged modifications.

    Untracked files are excluded on purpose: build artifacts and coverage files
    would otherwise block every push, while a forgotten edit to a tracked file is
    the case this rule exists to catch.

    Uses ``diff --name-only HEAD`` rather than ``status --porcelain``: porcelain
    prefixes each path with a two-character status plus a space, and the leading
    space of the first line is lost to the strip() in _git, so slicing the prefix
    off silently truncated the first path by a character.

    Args:
        repo: Repository root.

    Returns:
        list[str] or None: Modified tracked paths, or None when undeterminable.
    """
    out = _git(["diff", "--name-only", "HEAD"], repo)
    if out is None:
        return None
    return [line.strip() for line in out.splitlines() if line.strip()]


def check_push_version(tool_name, tool_input):
    """Block a push whose branch carries no VERSION change.

    Args:
        tool_name: Tool about to run.
        tool_input: Tool parameters.

    Returns:
        tuple[bool, str]: (blocked, message).
    """
    if tool_name != "Bash":
        return False, ""

    command = (tool_input or {}).get("command", "") or ""
    target = find_push_target(command)
    if target is None:
        return False, ""

    repo = _repo_root(target)
    if repo is None:
        return False, ""
    if not _repo_tracks_a_version_file(repo):
        return False, ""

    paths = _branch_files(repo)
    if paths is None or not paths:
        return False, ""
    if _has_version_change(paths):
        return False, ""

    preview = ", ".join(paths[:5]) + ("" if len(paths) <= 5 else " ...")
    msg = (
        "[BLOCKED L3.10] git push blocked - no VERSION change on this branch\n"
        "  Repo     : " + repo + "\n"
        "  Branch   : " + (_git(["rev-parse", "--abbrev-ref", "HEAD"], repo) or "?") + "\n"
        "  Changes  : " + preview + "\n"
        "  Policy   : version-release-policy.md\n"
        "  Rule     : the branch being pushed must include a VERSION update.\n"
        "  Action   : python scripts/tools/release.py patch   (or edit VERSION), commit, push.\n"
        "  Note     : checked against the branch's merge base, so one bump covers every\n"
        "             push on this branch."
    )
    return True, msg


def check_push_clean_tree(tool_name, tool_input):
    """Block a push while tracked files in the same repo have uncommitted changes.

    Args:
        tool_name: Tool about to run.
        tool_input: Tool parameters.

    Returns:
        tuple[bool, str]: (blocked, message).
    """
    if tool_name != "Bash":
        return False, ""

    command = (tool_input or {}).get("command", "") or ""
    target = find_push_target(command)
    if target is None:
        return False, ""

    repo = _repo_root(target)
    if repo is None:
        return False, ""

    modified = _modified_tracked_files(repo)
    if not modified:
        return False, ""

    preview = ", ".join(modified[:5]) + ("" if len(modified) <= 5 else " ...")
    msg = (
        "[BLOCKED L3.11] git push blocked - uncommitted changes to tracked files\n"
        "  Repo     : " + repo + "\n"
        "  Files    : " + preview + "\n"
        "  Policy   : git-workflow-policy.md\n"
        "  Rule     : commit tracked changes before pushing.\n"
        "  Action   : git add <files> && git commit, or git stash, then push.\n"
        "  Note     : untracked files are ignored; only tracked modifications block."
    )
    return True, msg

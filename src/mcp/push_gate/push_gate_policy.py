"""The two version-push rules, ported off the PreToolUse hook (PRD FR-23).

WHAT THIS ENFORCES, MEASURED RATHER THAN INFERRED FROM ITS NAME
--------------------------------------------------------------
Exactly two rules, both asked of the repository the push targets:

1. VERSION-ON-BRANCH -- the branch being pushed carries a change to a VERSION
   or version.txt file, measured against the branch's merge base.
2. CLEAN-TREE -- no tracked file in that repository has staged or unstaged
   modifications.

It does NOT enforce branch protection. ``origin/main`` appears only as one of
four candidate refs for resolving a merge base, and no rule anywhere consults
the branch's name, its protection status or its relationship to a default
branch. A reader who assumes otherwise from the word "gate" will be wrong. The
rules are also a no-op in a repository that tracks no VERSION file at all,
because a repository with no such file cannot satisfy a bump rule and blocking
it would be unsatisfiable rather than protective.

FAIL-OPEN IS PRESERVED DELIBERATELY, AND MADE VISIBLE
-----------------------------------------------------
Every git query that fails -- a timeout, a non-zero exit, a directory that is
not a repository -- yields "not blocked", exactly as the hook does. That
behaviour is carried over unchanged: changing it during a port would move the
gate's semantics under cover of a move, and whether the gate should fail closed
is a separate decision for whoever wants to make it.

What IS new is that a fail-open is reported. ``evaluate_push`` returns a
``determination`` of ``UNDETERMINED`` when a rule could not be answered, next to
the ``allowed`` verdict the hook could only express as False. No decision
changes; a silence becomes legible.

WHY THE CALLER MUST SUPPLY ITS WORKING DIRECTORY
------------------------------------------------
The hook ran inside Claude Code's own process tree, so ``os.getcwd()`` was the
directory a bare ``git push`` would run in. An MCP server is a long-lived child
process spawned from a path in the settings file; its working directory is
whatever spawned it and bears no relation to the project the caller is in.
``evaluate_push`` therefore takes an explicit ``caller_cwd``. Omitting it falls
back to this process's own directory, which is what the hook did and is very
likely wrong here -- the returned payload says so via ``cwd_source``.

Windows-safe: ASCII only, no Unicode characters.
"""

import os
import shlex
import subprocess
import sys

GIT_NAMES = frozenset({"git", "git.exe"})

GIT_OPTS_WITH_VALUE = frozenset({"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path"})

EXEMPT_PUSH_FLAGS = frozenset({"--dry-run", "-n", "--delete", "-d", "--tags"})

SEPARATORS = ("&&", "||", ";", "|", "\n")

VERSION_NAMES = frozenset({"version", "version.txt"})

SETTLING_SUBCOMMANDS = frozenset({"commit", "stash", "merge", "rebase", "cherry-pick", "revert", "am", "apply"})

WRAPPERS = frozenset({"env", "sudo", "nohup", "time", "command", "exec", "nice", "stdbuf"})

GIT_TIMEOUT_SEC = 10

RULE_VERSION = "version-on-branch"
RULE_CLEAN_TREE = "clean-tree"

CODE_VERSION = "L3.10"
CODE_CLEAN_TREE = "L3.11"

DETERMINATION_ALLOWED = "ALLOWED"
DETERMINATION_BLOCKED = "BLOCKED"
DETERMINATION_UNDETERMINED = "UNDETERMINED"


def _split_segments(command):
    """Split a shell command into separately executed segments.

    Args:
        command: Raw command string from the tool input.

    Returns:
        list: Segment strings, in order.
    """
    segments = [command]
    for sep in SEPARATORS:
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

    Non-posix mode is used on Windows because posix mode treats a backslash as
    an escape character, which turns ``git -C C:\\path\\repo push`` into
    ``C:pathrepo`` -- the directory then fails to resolve and the gate silently
    allows the push. Non-posix mode keeps backslashes but leaves quotes attached
    to tokens, so they are stripped afterwards.

    Args:
        segment: A single command segment.

    Returns:
        list: Tokens, or an empty list when the segment cannot be parsed.
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
    ``sudo``. Only this position may be treated as the program being run:
    scanning every token instead would read ``echo git push`` as a push, since
    ``git`` and ``push`` appear as bare arguments there.

    Args:
        tokens: Tokens of a single command segment.

    Returns:
        int: Index of the command token, or -1 when there is none.
    """
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if "=" in token and not token.startswith("-") and "/" not in token.split("=", 1)[0]:
            index += 1
            continue
        if os.path.basename(token).lower() in WRAPPERS:
            index += 1
            continue
        return index
    return -1


def _git_subcommand(tokens):
    """Return the git subcommand and the -C directory for a token list.

    Args:
        tokens: Tokens of a single command segment.

    Returns:
        tuple: ``(subcommand, -C directory)``. Both empty when not a git call.
    """
    index = _command_index(tokens)
    if index < 0 or os.path.basename(tokens[index]).lower() not in GIT_NAMES:
        return "", ""

    directory = ""
    cursor = index + 1
    while cursor < len(tokens):
        token_at = tokens[cursor]
        if token_at in GIT_OPTS_WITH_VALUE:
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

    Handles the common ``cd <dir> && git push`` shape by tracking cd targets
    across segments, and honors ``git -C <dir>``.

    Args:
        command: Raw command string.

    Returns:
        str or None: Directory the push runs in (empty string meaning the
        caller's own working directory), or None when the command contains no
        push that publishes commits.
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
        if any(flag in tokens for flag in EXEMPT_PUSH_FLAGS):
            continue
        return directory or cwd
    return None


def command_settles_state_before_push(command):
    """Return True when the command itself changes git state before its push.

    Both rules ask about repository state, but a gate consulted before the
    command runs can only see the state as it is now. A chained
    ``git commit && git push`` therefore looks dirty and version-less at gate
    time even though the push that eventually happens is clean and bumped.
    Asking about a state the command is about to replace produces a block the
    user cannot act on: committing first is exactly what they already wrote.

    Args:
        command: Raw command string.

    Returns:
        bool: True when a state-changing git subcommand precedes the push.
    """
    for segment in _split_segments(command):
        tokens = _tokenize(segment)
        if not tokens:
            continue
        subcommand, _ = _git_subcommand(tokens)
        if subcommand == "push":
            return False
        if subcommand in SETTLING_SUBCOMMANDS:
            return True
    return False


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
            timeout=GIT_TIMEOUT_SEC,
        )
    except Exception:
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def _repo_root(cwd, fallback_cwd=None):
    """Resolve the repository root for a directory.

    Args:
        cwd: Directory the push runs in; empty means the caller's own directory.
        fallback_cwd: Directory to use when ``cwd`` is empty. Defaults to this
            process's working directory, which is the hook's behaviour and is
            very likely wrong for a separately spawned server.

    Returns:
        str or None: Absolute repo root, or None when not inside a repo.
    """
    base = cwd or fallback_cwd or os.getcwd()
    expanded = os.path.expanduser(base)
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
        list or None: Changed paths, or None when it cannot be determined.
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
        out = _git(["diff", "--name-only", "HEAD~1", "HEAD"], repo)
        return [] if out is None else [line for line in out.splitlines() if line.strip()]

    out = _git(["diff", "--name-only", base, "HEAD"], repo)
    if out is None:
        return None
    return [line for line in out.splitlines() if line.strip()]


def _repo_tracks_a_version_file(repo):
    """Return True when the repo participates in the version-release policy.

    Only a repo that actually tracks a VERSION file can satisfy a "bump VERSION"
    rule. Of the repos in this workspace only a handful do, so without this
    check the gate would block every push in the rest of them permanently, with
    no way to comply short of inventing a file the project never had.

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
        if os.path.basename(path.strip()).lower() in VERSION_NAMES:
            return True
    return False


def _modified_tracked_files(repo):
    """List tracked files with staged or unstaged modifications.

    Untracked files are excluded on purpose: build artifacts and coverage files
    would otherwise block every push, while a forgotten edit to a tracked file
    is the case this rule exists to catch.

    Uses ``diff --name-only HEAD`` rather than ``status --porcelain``: porcelain
    prefixes each path with a two-character status plus a space, and the leading
    space of the first line is lost to the strip in ``_git``, so slicing the
    prefix off silently truncated the first path by a character.

    Args:
        repo: Repository root.

    Returns:
        list or None: Modified tracked paths, or None when undeterminable.
    """
    out = _git(["diff", "--name-only", "HEAD"], repo)
    if out is None:
        return None
    return [line.strip() for line in out.splitlines() if line.strip()]


def check_push_version(tool_name, tool_input, caller_cwd=None):
    """Block a push whose branch carries no VERSION change.

    Args:
        tool_name: Tool about to run.
        tool_input: Tool parameters.
        caller_cwd: Directory a bare ``git push`` would run in.

    Returns:
        tuple: ``(blocked, message)``.
    """
    if tool_name != "Bash":
        return False, ""

    command = (tool_input or {}).get("command", "") or ""
    target = find_push_target(command)
    if target is None:
        return False, ""

    repo = _repo_root(target, caller_cwd)
    if repo is None:
        return False, ""
    if not _repo_tracks_a_version_file(repo):
        return False, ""

    paths = _branch_files(repo)
    if paths is None:
        return False, ""
    pending = _modified_tracked_files(repo) or []
    paths = list(paths) + list(pending)

    if not paths:
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


def check_push_clean_tree(tool_name, tool_input, caller_cwd=None):
    """Block a push while tracked files in the same repo have uncommitted changes.

    Args:
        tool_name: Tool about to run.
        tool_input: Tool parameters.
        caller_cwd: Directory a bare ``git push`` would run in.

    Returns:
        tuple: ``(blocked, message)``.
    """
    if tool_name != "Bash":
        return False, ""

    command = (tool_input or {}).get("command", "") or ""
    target = find_push_target(command)
    if target is None:
        return False, ""
    if command_settles_state_before_push(command):
        return False, ""

    repo = _repo_root(target, caller_cwd)
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


def _undetermined_reasons(command, target, repo):
    """Name every question that was not answered with a pass for this push.

    A rule that did not block returns the same "not blocked" whether it looked
    and found nothing wrong, could not look at all, or was never applicable.
    The hook's two-value result could not tell those apart. This recovers the
    distinction, and it covers three different situations on purpose, because
    all three mean the same thing to a caller deciding how much the verdict is
    worth -- this rule did not pass, it simply did not refuse:

    1. GENUINE FAIL-OPEN -- git could not be queried, or the push target is not
       a repository. The rule was unanswerable.
    2. NOT APPLICABLE -- the repository tracks no VERSION file, so the version
       rule cannot be satisfied and deliberately does not apply.
    3. DELIBERATE STAND-DOWN -- the command commits or stashes before pushing,
       so the clean-tree rule steps aside rather than judging a state the
       command is about to replace.

    Only computed when nothing blocked. A refusal is already the strongest
    thing the caller needs to know, and listing unanswered questions beside it
    would bury it.

    Args:
        command: Raw command string.
        target: Directory the push runs in, as returned by find_push_target.
        repo: Resolved repository root, or None.

    Returns:
        list: Human-readable reasons, empty when every rule was asked and passed.
    """
    if repo is None:
        return ["the push target {0!r} could not be resolved to a git repository".format(target or ".")]

    reasons = []
    if not _repo_tracks_a_version_file(repo):
        reasons.append("{0} tracks no VERSION file, so the version rule does not apply to it".format(repo))
    elif _branch_files(repo) is None:
        reasons.append("the branch's changed-file set could not be determined in {0}".format(repo))

    if _modified_tracked_files(repo) is None:
        reasons.append("the working-tree state could not be determined in {0}".format(repo))
    elif command_settles_state_before_push(command):
        reasons.append("the command commits or stashes before pushing, so the clean-tree rule stands down")
    return reasons


def evaluate_push(command, tool_name="Bash", caller_cwd=None):
    """Decide whether a command's ``git push`` may proceed.

    Both rules are always evaluated, so a caller sees every reason a push is
    refused rather than only the first. The verdict is the conjunction: a push
    is allowed only when neither rule blocks it.

    Args:
        command: The shell command about to run.
        tool_name: The tool the command belongs to. Only ``Bash`` is judged.
        caller_cwd: The directory a bare ``git push`` would run in. Supply it:
            this process's own working directory is not the caller's.

    Returns:
        dict: ``push_detected``, ``allowed``, ``determination``, ``violations``,
        ``undetermined``, ``repo``, ``target`` and ``cwd_source``.
    """
    text = command or ""
    target = find_push_target(text) if tool_name == "Bash" else None
    if target is None:
        return {
            "push_detected": False,
            "allowed": True,
            "determination": DETERMINATION_ALLOWED,
            "violations": [],
            "undetermined": [],
            "repo": None,
            "target": None,
            "cwd_source": "caller" if caller_cwd else "server-process",
        }

    repo = _repo_root(target, caller_cwd)

    violations = []
    version_blocked, version_message = check_push_version(tool_name, {"command": text}, caller_cwd)
    if version_blocked:
        violations.append({"rule": RULE_VERSION, "code": CODE_VERSION, "message": version_message})
    clean_blocked, clean_message = check_push_clean_tree(tool_name, {"command": text}, caller_cwd)
    if clean_blocked:
        violations.append({"rule": RULE_CLEAN_TREE, "code": CODE_CLEAN_TREE, "message": clean_message})

    undetermined = [] if violations else _undetermined_reasons(text, target, repo)
    if violations:
        determination = DETERMINATION_BLOCKED
    elif undetermined:
        determination = DETERMINATION_UNDETERMINED
    else:
        determination = DETERMINATION_ALLOWED

    return {
        "push_detected": True,
        "allowed": not violations,
        "determination": determination,
        "violations": violations,
        "undetermined": undetermined,
        "repo": repo,
        "target": target,
        "cwd_source": "caller" if caller_cwd else "server-process",
    }

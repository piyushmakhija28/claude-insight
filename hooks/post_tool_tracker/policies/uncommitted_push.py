"""
post_tool_tracker/policies/uncommitted_push.py - Level 3.11 policy.

SUPERSEDED: the PostToolUse hook no longer calls this. Blocking from PostToolUse
cannot work -- it runs after the tool finishes, so the push has already reached the
remote. The live gate is hooks/pre_tool_enforcer/policies/push_gate.py, which also
scopes the question to the repository being pushed and ignores untracked files.
This module is retained only because tests/test_post_tool_tracker.py exercises it
through the legacy re-export; do not wire it back into the hook.

Blocks git push when uncommitted changes exist in the repository.
Policy: git-workflow-policy.md
"""


def check_uncommitted_before_push(tool_name, tool_input):
    """Level 3.11: BLOCK git push when uncommitted changes exist in the repo.

    Policy: git-workflow-policy.md
    Rule: All changes must be committed before pushing to the remote.
    This prevents accidental pushes that skip the commit step.

    Detection: runs `git status --porcelain` in the current working directory.
    If it returns any output (staged or unstaged changes), the push is blocked.

    Args:
        tool_name (str):   Current tool being invoked.
        tool_input (dict): Bash tool input dict (checked for git push command).

    Returns:
        (bool, str): (True, message) if blocked, (False, '') otherwise.
    """
    if tool_name != "Bash":
        return False, ""
    cmd = (tool_input or {}).get("command", "").lower()
    if "git push" not in cmd or "--dry-run" in cmd or "--delete" in cmd:
        return False, ""
    try:
        import subprocess as _sp

        result = _sp.run(["git", "status", "--porcelain"], capture_output=True, text=True, timeout=10)
        dirty_lines = [item for item in result.stdout.splitlines() if item.strip()]
        if not dirty_lines:
            return False, ""
        preview = dirty_lines[:5]
        more = len(dirty_lines) - 5 if len(dirty_lines) > 5 else 0
        msg = (
            "[BLOCKED L3.11] git push blocked - uncommitted changes detected!\n"
            "  Dirty files : " + str(len(dirty_lines)) + " file(s) with changes\n"
            "  Preview"
            + " "
            + ": "
            + "\n"
            + "\n".join("    " + item for item in preview)
            + ("\n    ... and " + str(more) + " more" if more else "")
            + "\n"
            "  Policy" + "      : git-workflow-policy.md\n"
            "  Rule" + "        : All changes must be committed before pushing.\n"
            "  Action" + '      : git add <files> && git commit -m "..." then push again.'
        )
        return True, msg
    except Exception:
        return False, ""  # Fail-open: never block on git status errors


# Backward-compat alias (original name in post-tool-tracker.py)
check_level_3_11_git_status = check_uncommitted_before_push

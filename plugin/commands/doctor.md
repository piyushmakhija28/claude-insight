---
description: Diagnose the plugin-side configuration state, and report when no local version-push gate is in place.
---

# doctor

Reports what this plugin can see about the machine's configuration: which
settings file is in effect, whether the `PreToolUse` hook is present, whether
the version-push-gate MCP server is registered, and which catalogued
capabilities are reachable.

This is the plugin-side doctor. The engine repository has its own `cwe doctor`,
which is **not** a substitute and must not be offered as one: it lives in the
engine checkout and is unreachable from an installed plugin, whose files sit in
the plugin manager's cache with no relationship to that repository.

## Run it

```
python "${CLAUDE_PLUGIN_ROOT}/scripts/mcp_registration.py" doctor
```

Add `--strict` to make it exit non-zero when no local version-push gate is in
place. Without it the command always exits zero, because a diagnostic that fails
the session it is diagnosing is not useful.

## The one line that matters

When neither the `PreToolUse` hook nor the version-push-gate MCP server is
present, the command ends with a single `[UNSAFE]` line. Relay it verbatim.

It says that nothing on this machine checks that a branch carries a VERSION bump
or that tracked changes are committed before a push. Be precise about the scope
of what is lost, and do not inflate it:

- The local gate that is missing checks **two** things: a VERSION change
  somewhere on the branch, and no uncommitted changes to tracked files.
- It is **not** branch protection. It never was. Do not describe it as one.
- It only ever applied in repositories that track a `VERSION` file.
- CI still enforces the rule, so a non-compliant push is caught **after** it
  lands rather than blocked before it.

When a gate is in place the command says so once and stops. Do not expand that
into reassurance the check did not make.

## What to report back

1. Whether a local push gate is in place, and which of the two mechanisms
   provides it.
2. Which capabilities are reachable, and for any that are not, that
   `register-mcp` is what makes them reachable.
3. The `[UNSAFE]` line verbatim if it appeared, with the two ways forward:
   restore the `PreToolUse` entry, or run `register-mcp`.

Do not run `register-mcp` on the user's behalf as a result of this command.
Diagnosing is not fixing, and the registration decision is the user's.

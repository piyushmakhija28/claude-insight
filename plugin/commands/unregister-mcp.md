---
description: Reverse register-mcp. Removes only the user-scope MCP entries this plugin added, and refuses by default if that would leave no local version-push gate.
---

# unregister-mcp

The exact inverse of `register-mcp`. It removes user-scope MCP registrations
that `register-mcp` wrote, and only those - provenance comes from the plugin's
own ledger, never from guessing which entries in `settings.json` look like ours.
A server the user registered by any other route is never touched.

## Start-up check (run this first)

```
python "${CLAUDE_PLUGIN_ROOT}/scripts/mcp_registration.py" precondition
```

It prints one line when no local version-push gate is in place, and prints
nothing at all otherwise. If a line appears, relay it verbatim before doing
anything else, then continue - it reports a state, it does not block this
command. Silence means the gate is in place; do not invent reassurance for it.

## Run it

```
python "${CLAUDE_PLUGIN_ROOT}/scripts/mcp_registration.py" unregister
```

## It refuses by default in one specific case

If `PreToolUse` is absent from the settings file's hooks block, the hook-side
version-push gate is not running. Removing the MCP-side gate as well would leave
**neither**, and the command refuses with exit status 2 rather than proceeding.

The refusal names the consequence and both ways forward:

1. Restore the `PreToolUse` entry in `settings.json`, then re-run.
2. Re-run with `--acknowledge-no-push-gate` to proceed anyway.

Do not add the acknowledgement flag on the user's behalf. The action must stay
possible and must never happen by accident; choosing it is the user's, and the
refusal exists so that choice is made knowingly. If the user does choose it,
state plainly that the CI-side assertion still applies but the local guard will
not, so a non-compliant push is caught after the fact rather than blocked.

## Removing is not always deleting

Where `register-mcp --force` took over a name that already held the user's own
entry, reversing that registration means **restoring** the displaced entry, not
deleting the name. The command reports `RESTORED` rather than `REMOVED` in that
case. Report which of the two happened for each entry; they are different
outcomes and the user's configuration differs afterwards.

## What to report back

1. Which entries were removed, and which were restored to a previous entry.
2. That the change takes effect in a **new** session.
3. That the capabilities are now unreachable, and that `register-mcp` restores
   them.

## What is and is not guaranteed

- **Reversible**: what this plugin wrote is undone - removed where it added a
  name, restored where it displaced one - and nothing else is touched.
- **Round trip**: a capability reachable after `register-mcp` is unreachable
  again after this command.
- **Not byte-identical**: the settings file is re-serialised with two-space
  indentation, so a file that was formatted differently will differ in bytes
  after a round trip even though it is equal as an object. Do not claim the file
  is restored byte-for-byte.

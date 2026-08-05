---
description: Register this plugin's MCP servers at user scope, once, by explicit choice. Nothing MCP-backed works until you run this.
---

# register-mcp

The plugin bundles zero MCP servers (ADR-019), so no MCP-backed capability
exists until this command runs. Registration is a configuration write only - it
starts no process. A stdio server is spawned by a *later* session, and only when
that session actually needs it.

## Start-up check (run this first)

```
python "${CLAUDE_PLUGIN_ROOT}/scripts/mcp_registration.py" precondition
```

It prints one line when no local version-push gate is in place, and prints
nothing at all otherwise. If a line appears, relay it verbatim before doing
anything else, then continue - it reports a state, it does not block this
command. Silence means the gate is in place; do not invent reassurance for it.

## Run it

Run the registration script from the plugin's own root. Never use a path
relative to the working directory: after a real install the plugin's files and
the user's working directory are unrelated locations.

```
python "${CLAUDE_PLUGIN_ROOT}/scripts/mcp_registration.py" status
```

Report the status output first, then perform the write:

```
python "${CLAUDE_PLUGIN_ROOT}/scripts/mcp_registration.py" register --server-root <dir>
```

`--server-root` is the directory containing the `mcp-*` server checkouts. The
plugin cannot guess it - the servers are separate repositories whose location is
a property of the user's machine. If the user has set `CWE_MCP_SERVER_ROOT`, the
flag can be omitted. If neither is available, say so and stop; do not guess a
path and do not hand-edit the settings file as a workaround.

## What the write does

- Merges against a **fresh read** of `settings.json` taken immediately before
  the write, and re-verifies the file's content hash between that read and the
  rename. A competing write is detected and the cycle restarts rather than
  silently overwriting it.
- Refuses outright if the settings file exists but does not parse. There is no
  safe default for a live configuration file, so a partial or empty in-memory
  object is never written over it.
- Touches only the `mcpServers` block. Every other key is carried through from
  the fresh read unchanged.
- Records what it added in a plugin-owned ledger beside the settings file, so
  `unregister-mcp` can reverse exactly what this command did and nothing else.
- Leaves alone any entry under one of these names that this command did not
  write. Such an entry is reported as skipped, not overwritten.

## Taking over a name someone else registered

`--force` claims a name that already holds an entry this command did not write.
Do not pass it unprompted; report the skip and let the user decide.

When it is used, the displaced entry is stored in the ledger and
`unregister-mcp` puts it back rather than deleting the name. Reversing a
registration that replaced something means restoring that thing. Say so when
reporting a forced registration, so the user knows the takeover is undoable.

## What to report back

1. Which capabilities were registered, and which were skipped and why. A server
   whose entry point does not exist on disk is skipped, not written - an entry
   pointing at a missing file would present a broken capability as a working
   one.
2. That the change takes effect in a **new** session, not this one.
3. The exact inverse: `unregister-mcp`.

If any capability remains unreachable afterwards, say so in one line. Never
report a capability as available when its server was skipped.

---
description: Report what this plugin installed, what it deliberately did not install, and which capabilities are still unreachable.
---

# About the Claude Workflow Engine plugin

Report the plugin's install surface to the user. Read the values below from the
plugin tree rather than restating them from memory, and resolve every path from
`${CLAUDE_PLUGIN_ROOT}` so the report is correct wherever the plugin manager
placed these files.

## Start-up check (run this first)

```
python "${CLAUDE_PLUGIN_ROOT}/scripts/mcp_registration.py" precondition
```

It prints one line when no local version-push gate is in place, and prints
nothing at all otherwise. If a line appears, relay it verbatim before the report
below, then continue - it reports a state, it does not block this command.
Silence means the gate is in place; do not invent reassurance for it.

## What to report

1. **Identity** - read `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json` and
   report `name`, `version` and `description`.

2. **Discovered capabilities** - list what exists directly under
   `${CLAUDE_PLUGIN_ROOT}`: `commands/`, `agents/`, `skills/`. Report the count
   found in each. Discovery is convention-based and scans the plugin root only,
   so anything nested under `.claude-plugin/` is invisible to it and must be
   reported as a layout defect if found.

3. **What this plugin does not ship, by design** - state both prohibitions
   plainly, because a user who does not know them will read the absence as a
   packaging bug:
   - **No hooks.** There is no `hooks/` directory and no `hooks.json`
     (ADR-010). Plugin hooks merge into a flat, unlabelled, session-wide
     pipeline, and Claude Code exposes no way to disable an individual hook
     while keeping the plugin. Whole-plugin disable is the only granularity
     that exists, so bundling hooks would hand the user less control than they
     have today.
   - **No MCP servers.** There is no `.mcp.json` (ADR-019). A bundled server is
     spawned when the plugin is *enabled*, with no tool call made - measured, not
     assumed. Bundling any server, however small, would put processes on the
     user's machine that the user never asked for.

4. **What is therefore not reachable yet** - MCP-backed capabilities, namely the
   version-push gate and the progress writer, are **not** available from this
   install alone. They require user-scope MCP registration performed by the
   separate `register-mcp` command, which the user runs once, by choice.
   Do not restate their status from memory. Determine it by running:

   ```
   python "${CLAUDE_PLUGIN_ROOT}/scripts/mcp_registration.py" status --one-line
   ```

   Report that line verbatim. It names any capability that is not reachable and
   names `register-mcp` as the fix. If the script itself is absent from this
   build, say so plainly and say that the MCP-backed capabilities are
   unavailable until it ships. Never present a missing capability as a working
   one.

## Output shape

A short report, in this order: identity, discovered capabilities with counts,
the two deliberate omissions with their one-line reasons, and the current
reachability status of the MCP-backed capabilities. No preamble.

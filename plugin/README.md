# claude-workflow-engine (Claude Code plugin)

The installable packaging of the Claude Workflow Engine's SDLC orchestration
entry points.

## Install

```
/plugin marketplace add techdeveloper-org/claude-workflow-engine
/plugin install claude-workflow-engine@techdeveloper-org
```

That single step delivers the plugin's **commands, agents and skills**. No
`settings.json` is hand-edited at any point.

## What install does not deliver, and why

This plugin ships **no hooks** and **no bundled MCP servers**. Both are
deliberate, recorded decisions, not gaps:

| Omitted | Decision | Reason |
|---|---|---|
| `hooks/`, `hooks.json` | ADR-010 | Plugin hooks merge into a flat, session-wide pipeline with no per-plugin label, so no per-hook disable can exist. Shipping one would give the user less control than they have today. |
| `.mcp.json` | ADR-019 | A bundled stdio server is spawned when the plugin is *enabled*, with no tool call made. Measured, not assumed: two spawns in an isolated session whose prompt forbade tool use. |

The consequence is explicit rather than silent: **MCP-backed capabilities are
not available after install alone.** The version-push gate and the progress
writer become reachable only after the separate `register-mcp` command writes
user-scope MCP registrations, which the user runs once, by choice.
`unregister-mcp` reverses it.

`register-mcp` is not part of this build. Until it ships, the MCP-backed
capabilities are unreachable, and any command that needs one says so rather than
failing quietly.

## Layout

```
plugin/
  .claude-plugin/plugin.json    <- identity manifest, this file only
  commands/                     <- slash commands
  agents/                       <- subagent personas
  skills/{name}/SKILL.md        <- skill packages
  README.md
```

Capability directories sit at the plugin **root**. Discovery scans the root
only - a capability directory nested inside `.claude-plugin/` is invisible to
it, and produces a plugin that installs cleanly and exposes nothing.

## Conformance

`scripts/verify_plugin_conformance.py` in the engine repository enforces the
manifest schema, the zero-hooks rule and the zero-MCP rule as a CI gate. Both
prohibitions are CRITICAL: a violation fails the build.

## Uninstall

`/plugin uninstall claude-workflow-engine` removes the plugin. It does not
return the machine to its exact pre-install state, and that is host behaviour
this plugin does not control: `enabledPlugins` and `extraKnownMarketplaces` are
emptied to `{}` but left in `settings.json`, and the version cache directory
survives on disk marked `.orphaned_at`, which `claude plugin prune` does not
clean.

Your own `Stop` and `Notification` hooks in `~/.claude/settings.json` are
untouched by both install and uninstall. This plugin never owned them.

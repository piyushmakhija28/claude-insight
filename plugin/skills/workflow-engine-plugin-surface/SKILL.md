---
name: workflow-engine-plugin-surface
description: "What the Claude Workflow Engine plugin ships, what it deliberately omits, and why a capability that looks missing is usually a recorded decision rather than a packaging defect. Use when a user asks why the plugin has no hooks, why an MCP-backed capability is unreachable after install, how plugin-internal paths resolve, or what a one-step install actually delivers. Keywords: claude-workflow-engine plugin, zero hooks, zero MCP servers, register-mcp, CLAUDE_PLUGIN_ROOT, plugin install surface."
allowed-tools: Read,Glob,Grep
user-invocable: true
---

# Claude Workflow Engine Plugin Surface

## What one `/plugin install` actually delivers

Installing this plugin delivers its **commands, agents and skills** in a single
step, with no hand-edited `settings.json`. That is the complete functional
surface for everything that does not need an MCP server.

It does **not** deliver MCP-backed capabilities. Those require one further,
explicit step. This split is deliberate and recorded, not an oversight, and the
reasoning is below. When a user reports that an MCP-backed capability is
missing after install, the first thing to establish is whether that second step
has been run - not whether the install is broken.

## The two things this plugin never ships

### No hooks (ADR-010)

There is no `hooks/` directory and no `hooks.json` anywhere in the plugin tree.

The reason is a property of how Claude Code composes hooks. A plugin's hook
entries **merge** into the session-wide hook pipeline for their event; they do
not override anything and they carry no per-plugin label once merged. The
consequence is structural: because the merged pipeline is a flat, unlabelled
list, there is no information left in it that says which plugin contributed
which entry. So the platform cannot offer a per-hook toggle even in principle -
whole-plugin enable/disable is the only control surface that can be computed
correctly, because it is applied *before* the merge rather than after it.

A `PreToolUse` or `PostToolUse` handler also fires on **every** matching tool
call in the session, not only on calls this plugin's own features initiated. A
handler that throws, hangs, or blocks degrades every tool call system-wide.

This project exists to remove per-tool-call hook overhead. Shipping hooks would
reintroduce exactly the overhead being removed, with less user control than the
status quo. An empty set cannot activate silently, so shipping zero hooks makes
the question moot rather than answering it.

**What this does not mean:** the user's own `Stop` and `Notification` hooks in
`~/.claude/settings.json` are untouched. This plugin never owned, installed, or
modified them, and uninstalling the plugin cannot and does not remove them.

### No MCP servers (ADR-019)

There is no `.mcp.json` in the plugin tree at all.

A bundled stdio server is spawned when the plugin is **enabled**, not when one
of its tools is first called. This was measured, not inferred: a fresh, isolated
session whose prompt explicitly forbade tool use still produced two full process
spawns of a bundled test server. Any bundled server, however minimal, therefore
puts processes on the user's machine that the user never asked for - which is
the same defect as bundling hooks, arriving through a different door.

An explicit opt-in command cures that defect where a bundled server cannot: the
user can decline by not running it, and reverse it by running the inverse
command.

## What is consequently unreachable until the user opts in

`register-mcp` writes user-scope MCP registrations and `unregister-mcp` reverses
them. Until `register-mcp` has been run:

- the version-push gate has no local MCP-side enforcement point;
- the progress writer's MCP query surface does not exist.

Crash recovery is unaffected - progress is a field of the checkpoint record
written in-process, and the MCP tool is only a projection of it, never the
writer.

**Reporting rule.** If a command in this plugin needs an MCP-backed capability
that is not registered, it must say so in one actionable line naming
`register-mcp`. A missing capability must never present as a working one, and it
must never present as a crash.

## Resolving plugin-internal paths

Every reference to a file this plugin ships resolves from the plugin's own root,
never from the current working directory:

- **Primary:** the `CLAUDE_PLUGIN_ROOT` environment variable, which Claude Code
  populates in the real process environment of anything it spawns, and
  substitutes into `${CLAUDE_PLUGIN_ROOT}` inside command definitions.
- **Defence in depth:** ascend from the running file's own directory until a
  directory containing `.claude-plugin/plugin.json` is found. This covers being
  run directly by a developer, outside any Claude Code-spawned process.

A current-working-directory-relative path is never correct here. It happens to
work during local development only because the author's shell is usually sitting
in the plugin's own repository at that moment. After a real install the plugin's
files live under the plugin manager's cache directory while the working
directory is whatever project the user is in - two unrelated locations. Such a
path passes every test the author runs and fails for essentially every installed
user.

## Uninstall is not a total subtraction

`/plugin uninstall` does not return the machine to its pre-install state, and
this is host behaviour the plugin does not control. Measured: the
`enabledPlugins` and `extraKnownMarketplaces` keys are emptied to `{}` but never
removed from `settings.json`, and the plugin's version cache directory survives
on disk with an `.orphaned_at` marker that `claude plugin prune` does not clean.

Assert on **plugin-attributable** residue only. A whole-file equality assertion
against a pre-install snapshot will fail on host behaviour, not on a defect.

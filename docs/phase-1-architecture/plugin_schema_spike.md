# FR-14a Plugin Schema Spike -- Empirical Results

Status: 5 of 5 items measured empirically. Claude Code CLI 2.1.220 (Windows).
Method: `claude plugin` CLI subcommands (install/uninstall/marketplace),
never hand-edited `settings.json`. A throwaway plugin
(`fr14a-spike-plugin@fr14a-spike-marketplace`, version `0.1.0`) was built
under the system temp scratch directory and installed/uninstalled at user
scope. Raw evidence files (settings.json snapshots at each stage, the MCP
server spawn log) are retained in the scratch directory for this session
and are not committed to the repo.

Important process note: this spike did **not** need to fall back to "could
not measure, here are manual instructions." `claude plugin install`,
`claude plugin uninstall`, `claude plugin marketplace add/remove`, and
`claude plugin validate` are non-interactive CLI subcommands (distinct
from the interactive `/plugin` slash command inside the REPL) and were
invoked directly from Bash. This closes the gap the task anticipated for
items 3 and 4.

---

## Item 1 -- Does `${CLAUDE_PLUGIN_ROOT}` resolve inside `.mcp.json` stdio `command`/`args`?

**RESULT: MEASURED -- YES, it resolves.**

`.mcp.json` in the throwaway plugin declared:

```json
{
  "mcpServers": {
    "fr14a-spike-server": {
      "command": "python",
      "args": [
        "${CLAUDE_PLUGIN_ROOT}/mcp_server.py",
        "--plugin-root-arg=${CLAUDE_PLUGIN_ROOT}"
      ]
    }
  }
}
```

The spawned server logged its own `sys.argv` as the very first action.
Observed argv from a real spawn during a fresh session:

```
argv[0] = C:/.../scratchpad/plugin-spike/marketplace/test-plugin/mcp_server.py
argv[1] = --plugin-root-arg=C:/.../scratchpad/plugin-spike/marketplace/test-plugin
```

Both occurrences of the literal string `${CLAUDE_PLUGIN_ROOT}` were
substituted with the plugin's actual absolute install path before the
process was spawned. `claude plugin list --json` still shows the
*unsubstituted* template in its `mcpServers` field (that output reflects
the manifest, not a live invocation) -- substitution happens at spawn
time, not at manifest-parse/display time.

Design consequence: bundled MCP servers **can** use `${CLAUDE_PLUGIN_ROOT}`-relative
paths in `.mcp.json`. No alternate distribution strategy is needed on this
axis.

Note on doc currency: the task briefed this as undocumented for
`.mcp.json`. As of this spike's WebFetch of
`code.claude.com/docs/en/plugins-reference`, the docs now show an
explicit `${CLAUDE_PLUGIN_ROOT}` example inside an `mcpServers` block and
state "hook commands, monitors, MCP servers, and LSP servers" all resolve
`${CLAUDE_PLUGIN_ROOT}". The docs appear to have been updated after the
HLD was written; this spike's empirical result independently corroborates
that documentation rather than relying on it.

---

## Item 2 -- Is `CLAUDE_PLUGIN_ROOT` present in `os.environ` for a spawned Python process?

**RESULT: MEASURED -- YES, and two more variables besides.**

`mcp_server.py`'s first action (before any MCP handshake) was:

```python
record = {
    "env_CLAUDE_PLUGIN_ROOT": os.environ.get("CLAUDE_PLUGIN_ROOT"),
    "env_CLAUDE_PLUGIN_DATA": os.environ.get("CLAUDE_PLUGIN_DATA"),
    "env_CLAUDE_PROJECT_DIR": os.environ.get("CLAUDE_PROJECT_DIR"),
    ...
}
```

Actual logged values from a real spawn:

```
env_CLAUDE_PLUGIN_ROOT = C:\Users\techd\AppData\...\scratchpad\plugin-spike\marketplace\test-plugin
env_CLAUDE_PLUGIN_DATA = C:\Users\techd\.claude\plugins\data\fr14a-spike-plugin-fr14a-spike-marketplace
env_CLAUDE_PROJECT_DIR = C:\Users\techd\AppData\...\scratchpad\plugin-spike\fresh-session-cwd
```

`CLAUDE_PLUGIN_ROOT` is present in the actual OS-level environment block
handed to the child process, not just substituted into the command-line
string. `CLAUDE_PLUGIN_DATA` is also present (populated even though the
directory itself is not created until first referenced by something that
writes to it -- confirmed separately: no `data/fr14a-spike-plugin-...`
directory existed on disk after the run). `CLAUDE_PROJECT_DIR` correctly
tracked the cwd Claude Code was launched from for that session.

**ADR-009a branch 2 verdict:** the plugin-bundled policy snapshot can
resolve its own root via `os.environ.get("CLAUDE_PLUGIN_ROOT")` directly,
with no `__file__`-ascent required at runtime. ADR-012's claim that the
`__file__`-ascent to `.claude-plugin/plugin.json` "removes this
dependency" should be read as **defense-in-depth, not a required
fallback**: `CLAUDE_PLUGIN_ROOT` was reliably present in every one of the
3 observed spawns in this spike. Recommend keeping the `__file__`-ascent
as a fallback only for the case where the script is invoked outside a
Claude Code-spawned process (e.g. a developer running it directly by hand
during plugin development), not as the primary resolution path.

---

## Item 3 -- Exactly which keys does `/plugin install` (CLI: `claude plugin install`) write to `settings.json`?

**RESULT: MEASURED.**

Structural diff performed at every stage (parsed JSON, not text diff):

| Stage | Command | Top-level keys added |
|---|---|---|
| 0 -> 1 | `claude plugin marketplace add <path>` | `extraKnownMarketplaces` |
| 1 -> 2 | `claude plugin install fr14a-spike-plugin@fr14a-spike-marketplace -s user` | `enabledPlugins` |

Exact structure written by `marketplace add`:

```json
"extraKnownMarketplaces": {
  "fr14a-spike-marketplace": {
    "source": {
      "source": "directory",
      "path": "C:\\Users\\techd\\AppData\\...\\scratchpad\\plugin-spike\\marketplace"
    }
  }
}
```

Exact structure written by `install`:

```json
"enabledPlugins": {
  "fr14a-spike-plugin@fr14a-spike-marketplace": true
}
```

No other top-level keys changed at either stage (the 5 existing hook
registrations and 25 `mcpServers` entries were untouched -- confirmed by
diffing every other top-level key between snapshots). The plugin's own
`.mcp.json` server (`fr14a-spike-server`) was **not** merged into the
top-level `mcpServers` key in `settings.json`; it stays scoped to the
plugin and is tracked separately (see `claude plugin list --json`, which
echoes it back from the plugin's own manifest, and
`~/.claude/plugins/installed_plugins.json`).

Additional install-time side effects observed outside `settings.json`
(all under `~/.claude/plugins/`, not touched by hand):
- Plugin copied to `~/.claude/plugins/cache/fr14a-spike-marketplace/fr14a-spike-plugin/0.1.0/`
- `~/.claude/plugins/installed_plugins.json` gained an entry
- `~/.claude/plugins/known_marketplaces.json` gained the marketplace entry (mirrors `extraKnownMarketplaces` in `settings.json`)

Design consequence: a v2.0.0 packaging design that needs to detect
"is our plugin installed/enabled" can rely on
`settings.json.enabledPlugins["<plugin>@<marketplace>"] === true`, matching
the "baseline has NO `enabledPlugins` key" premise -- the key is created
fresh on first install, not present-but-empty beforehand.

---

## Item 4 -- What does `/plugin uninstall` (CLI: `claude plugin uninstall`) leave behind?

**RESULT: MEASURED -- leaves residue on both settings.json and disk.**

`claude plugin uninstall fr14a-spike-plugin -s user -y`:
- `settings.json`: `enabledPlugins` key is **not removed**; it is emptied
  to `{}` and left in place.
- `~/.claude/plugins/installed_plugins.json`: entry correctly removed
  (`"plugins": {}`).
- `~/.claude/plugins/cache/fr14a-spike-marketplace/fr14a-spike-plugin/0.1.0/`:
  **left on disk**, all files intact, plus a new marker file
  `.orphaned_at` added to the directory. This is the mechanism `--prune`
  and `claude plugin prune` are meant to clean up later.
- `~/.claude/plugins/data/` : no directory was created for this plugin
  (it never wrote persistent data), so there was nothing to test
  `--keep-data` against in this spike.

`claude plugin marketplace remove fr14a-spike-marketplace`:
- `settings.json`: `extraKnownMarketplaces` key is **not removed**; it is
  emptied to `{}` and left in place (same pattern as `enabledPlugins`).
- `~/.claude/plugins/known_marketplaces.json`: entry removed.
- `~/.claude/plugins/marketplaces/` (the marketplace's own local metadata
  dir, if any) was empty/absent after removal.
- `~/.claude/plugins/cache/fr14a-spike-marketplace/`: **the orphaned
  plugin cache directory from the earlier uninstall survives marketplace
  removal too** -- it is not tied to marketplace registration lifecycle.

`claude plugin prune -y` (ran as a further cleanup attempt, itself an
official plugin-family command, not a hand-edit): reported
`"Nothing to prune (no auto-installed plugins at user scope)"` and did
**not** touch the orphaned cache directory. Cache residue from a manually
installed-then-uninstalled plugin is apparently not `prune`'s target;
`prune`/`autoremove` is scoped to auto-installed *dependency* plugins
only, per its own help text ("Remove auto-installed dependencies that are
no longer needed").

Design consequence: `~/.claude/plugins/cache/` **does accumulate**
residue across an install/uninstall cycle unless a separate GC pass
(not identified by this spike) reclaims `.orphaned_at`-marked
directories. A v2.0.0 uninstaller/updater flow should not assume
`plugin uninstall` is a full clean removal from disk, and should not
assume the two `settings.json` housekeeping keys disappear once emptied.

---

## Item 5 -- Are bundled `.mcp.json` stdio servers spawned merely because the plugin is enabled, never invoked? (ADR-018 / NFR-1)

**RESULT: MEASURED -- YES, they are spawned on enable, with no tool call needed. NFR-1 fails via this mechanism.**

After installing (and thereby enabling) the plugin, a brand-new, fully
isolated session was started:

```
claude -p "Reply with exactly the single word OK and do not call any tools."
```

This session never referenced the plugin, its skill, or its MCP tool in
any way -- the prompt explicitly forbade tool use, and the model's only
output was the string `OK`. Despite this, `mcp_server.py`'s spawn-time
log recorded **two full process spawns** during that single `-p`
invocation, both logging `cwd` equal to the isolated session's working
directory (confirming they came from that session, not a stray earlier
run):

```
spawn 1: pid 34408, cwd = .../fresh-session-cwd
spawn 2: pid 28084, cwd = .../fresh-session-cwd
```

(A third, separate spawn -- pid 27968, `cwd` = the *unrelated*
`claude-workflow-engine\scripts` directory -- was also logged around the
same time. This did not come from the isolated `-p` command above; the
most plausible explanation is that an already-running, separate Claude
Code session sharing this same user's `~/.claude` config picked up the
newly-enabled plugin's MCP server without an explicit
`/reload-plugins`, contradicting the docs' claim that mid-session plugin
changes require a manual reload. This is a secondary, unconfirmed
observation -- flagged for awareness, not asserted as fact -- since this
spike cannot rule out every alternative explanation for that third
spawn's origin.)

Design consequence -- **this is the sharpest finding of the spike**: for
the two confirmed spawns, Claude Code connects configured MCP servers
(runs their `initialize` handshake) as part of normal session/plugin
startup for every enabled plugin, independent of whether the model ever
calls one of that server's tools. This directly contradicts NFR-1 ("zero
engine-attributable processes in an idle session") for any packaging
design (ADR-018) that bundles the engine's MCP servers inside a plugin
and merely relies on "the user hasn't invoked it yet" to keep the engine
dormant. If NFR-1 must hold, the v2.0.0 design needs either: (a) an
explicit lazy-connect mechanism that this spike found no evidence of, (b)
to not bundle heavyweight servers as always-on plugin `mcpServers`
entries and instead trigger them via a lighter mechanism (skill-invoked
subprocess, hook, or on-demand registration), or (c) to accept
NFR-1 as unmet for the plugin-enabled-but-idle state and revise the NFR.

---

## Final settings.json Verification

```
Baseline sha256 (recorded before this spike started):
  63283b4f709217ccf937ab579380f4563808dd6dc3ba57c162f2d7e08d3d1910

Final sha256 (after uninstall + marketplace remove + prune):
  479cbcfe9472799f2d4fbdf50ca65378a322d8a5476da7ea2367b7092c631353

Match: NO
```

Per the spike's hard rules, no repair was attempted. Structural diff
(parsed JSON, not text) between baseline and final state:

```
added top-level keys : enabledPlugins, extraKnownMarketplaces
removed top-level keys : (none)
changed keys : (none -- the 5 hook registrations and 25 pre-existing
                mcpServers entries are byte-for-byte identical to baseline)
```

Both residual keys hold empty objects:

```json
"enabledPlugins": {},
"extraKnownMarketplaces": {}
```

This is exactly the item 4 residue described above, surfacing here as a
non-matching final hash. The backup taken before this spike
(`C:\Users\techd\.claude\settings.json.backup-20260801-121210`, sha256
`63283b4f709217ccf937ab579380f4563808dd6dc3ba57c162f2d7e08d3d1910`, byte-identical
to the pre-spike live file) is available if the user wants to restore the
exact pre-spike file. Restoring is a user decision, not performed here.
Functionally, both residual keys are empty and inert -- they do not
re-enable the plugin, do not re-register the marketplace, and do not
reference the now-deleted scratch directory in any live-effect way (the
`extraKnownMarketplaces` path string is gone; the marketplace itself was
removed) -- but they are still a byte-level and structural difference
from the recorded baseline.

Also still present on disk (not in `settings.json`, but from this
spike's plugin cache):

```
C:\Users\techd\.claude\plugins\cache\fr14a-spike-marketplace\fr14a-spike-plugin\0.1.0\
```

with `.orphaned_at` marker, per the item 4 findings above.

---

## Summary Table

| Item | Result | Verdict |
|---|---|---|
| 1. `${CLAUDE_PLUGIN_ROOT}` in `.mcp.json` command/args | Measured | Resolves correctly at spawn time |
| 2. `CLAUDE_PLUGIN_ROOT` in spawned process `os.environ` | Measured | Present, along with `CLAUDE_PLUGIN_DATA` and `CLAUDE_PROJECT_DIR` |
| 3. Keys `/plugin install` writes to settings.json | Measured | `extraKnownMarketplaces` (on marketplace add), `enabledPlugins` (on install) |
| 4. Residue after `/plugin uninstall` | Measured | Empty `{}` keys left in settings.json; orphaned plugin cache dir left on disk; `prune` does not clean it |
| 5. MCP servers spawned merely on enable (NFR-1) | Measured | YES -- spawned with zero tool invocations; NFR-1 fails via this mechanism as currently understood |

Nothing in this spike required the "could not measure, here are manual
instructions" fallback -- all 5 items were settled by direct CLI
invocation and file/process observation.

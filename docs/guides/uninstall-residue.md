# Uninstall residue runbook

**Scope: what survives `claude plugin uninstall claude-workflow-engine@techdeveloper-org`, and how to
remove each item by hand.**

This is the deliverable for PRD FR-24 / SRS FR-36. FR-36 is deliberately a document rather than a
command: once uninstall completes the plugin's files are unreachable, so there is no plugin-side
execution point left from which a cleanup command could run.

**Document mode.** Sections 4 and 5 are the procedure and are written as a how-to guide: every
sentence in them directs an action or states a check. Sections 1, 2, 6 and 9 are explanation and are
labelled as such, so a reader working through the procedure can skip them and a reader trying to
understand the residue can read only them. This split is deliberate and mirrors
`docs/guides/adr-020-path-c-verification.md`, the sibling document written by V2-016.

---

## 1. Why residue exists at all (explanation)

`claude plugin uninstall` is Claude Code's own command. It removes the plugin manager's own records
of the plugin, and it does not remove two classes of thing:

1. Bookkeeping keys it wrote into `settings.json`. It empties them to `{}` and leaves the keys in
   place rather than deleting them.
2. The plugin's cached files under `~/.claude/plugins/cache/`, which it marks with an `.orphaned_at`
   file and leaves on disk.

There is no plugin-side interception point for either. The plugin ships zero hooks (ADR-010), and by
the time uninstall has run, nothing of the plugin is loaded. This is the reason SRS FR-31 was
narrowed to *plugin-attributable* residue and the Claude-Code-owned residue was moved to FR-36 --
that is, to this document -- rather than asserted absent. See section 6.

A third class exists and is specific to this plugin: anything the `register-mcp` command wrote before
uninstall. That command writes outside the plugin tree on purpose, so that an uninstalled plugin
still leaves the user able to find and reverse what it registered. Section 4 removes it in the
supported way; section 5 removes it by hand once the supported way is gone.

## 2. What the evidence is, and what it does not cover (explanation)

Every MEASURED claim below traces to one source: the FR-14a plugin schema spike,
`docs/phase-1-architecture/plugin_schema_spike.md`, Item 4 (lines 171-213 as of 2026-08-03), with
supporting detail in its Final settings.json Verification section (lines 269-318 as of 2026-08-03).
Line numbers in this document are dated hints and drift when the cited file grows; resolve by heading
text if a number lands somewhere unexpected.

**The spike measured a throwaway plugin, not this one.** It built, installed and uninstalled a
disposable plugin at user scope and diffed parsed JSON at every stage. It therefore measured the
*behaviour* of `claude plugin uninstall`. It did not measure this plugin's own paths, which are
derived here by substituting this plugin's manifest strings into the layout the spike observed.
Section 3 labels that distinction per row rather than blurring it.

**The measurement cannot be repeated on demand.** The project owner ruled during V2-016 that no live
`claude plugin install` or `/plugin uninstall` may be run, precisely because install mutates
`settings.json` in ways uninstall does not reverse. That ruling is recorded in
`docs/guides/adr-020-path-c-verification.md` section 1. Nothing in this document was produced by
running an install or an uninstall.

**What was re-measured for this document, on 2026-08-03, read-only:**

| Check | Result |
|---|---|
| `claude --version` | `2.1.220`, identical to the CLI version the spike recorded (spike line 3 as of 2026-08-03). The spike's measurement is **not** stale against the CLI in use. |
| `enabledPlugins` in `~/.claude/settings.json` | Key present, value `{}`. Item 4's settings residue independently re-confirmed two days later. |
| `extraKnownMarketplaces` in `~/.claude/settings.json` | Key present, value `{}`. Same. |
| `~/.claude/plugins/cache/` | **Empty.** The orphaned directory the spike left behind is no longer on disk. |
| `~/.claude/plugins/installed_plugins.json` | `{"version": 2, "plugins": {}}` -- the spike's entry is gone, as it measured. |
| `~/.claude/plugins/known_marketplaces.json` | `{}` -- same. |
| `~/.claude/cwe-mcp-registrations.json` | Absent. `register-mcp` has never run on this machine. |

The empty cache directory is a divergence from the spike and is reported here rather than smoothed
over. **Its cause is unknown.** It is consistent with the separate garbage-collection pass the spike
itself hypothesised but could not identify (spike lines 206-212 as of 2026-08-03); it is equally
consistent with a manual deletion by the machine's owner in the two days since. This document does
not attribute it, and does not claim the cache residue is fixed. The procedure below is written as
check-then-remove so that it is correct whether or not the directory is present.

---

## 3. Residue inventory (reference)

Every path is written for **user scope**, which is the scope the spike measured and the scope
`register-mcp` defaults to. If the plugin was installed with `-s project` or `-s local`, substitute
the settings file for that scope; the key names do not change.

Two evidence columns, because the two halves of each claim have different strength. **Behaviour** is
whether the item survives uninstall. **Path** is whether the exact location named here was read from
an artefact or derived by substitution. Each is exactly one of `MEASURED`, `INFERRED`, or
`NOT MEASURED`.

| ID | Exact path or key | Behaviour | Path | Source of the path |
|---|---|---|---|---|
| R1 | `~/.claude/settings.json`, top-level key `enabledPlugins`, emptied to `{}` and retained. Before uninstall it holds `"claude-workflow-engine@techdeveloper-org": true`. | MEASURED | MEASURED | Fixed key name and fixed file; spike lines 143-145, 176-178 as of 2026-08-03. Re-confirmed on this machine 2026-08-03. |
| R2 | `~/.claude/settings.json`, top-level key `extraKnownMarketplaces`, emptied to `{}` and retained. Before removal it holds a `techdeveloper-org` entry. | MEASURED | MEASURED | Fixed key name and fixed file; spike lines 129-137, 188-191 as of 2026-08-03. Re-confirmed on this machine 2026-08-03. |
| R3 | `~/.claude/plugins/cache/techdeveloper-org/claude-workflow-engine/0.1.0/`, together with the `.orphaned_at` marker file written inside it. | MEASURED | INFERRED | Layout observed once in the spike (lines 180-183, 194-196 as of 2026-08-03). The three segments are this plugin's marketplace name, plugin name and version, read from `.claude-plugin/marketplace.json` and `plugin/.claude-plugin/plugin.json` on 2026-08-03. |
| R4 | `~/.claude/settings.json`, `mcpServers` entry `post-tool-tracker`, written only if the user ran `register-mcp`. | INFERRED | MEASURED | Entry id read from `plugin/mcp-registry.json`. Settings file reported by `mcp_registration.py status --json`. Survival across uninstall is ADR-020 Path C, which is **not measured** -- see the warning below this table. |
| R5 | `~/.claude/cwe-mcp-registrations.json`, the provenance ledger `register-mcp` writes beside the settings file. | INFERRED | MEASURED | File name and location read from `plugin/scripts/mcp_registration.py` (`LEDGER_FILE_NAME`, line 80, and the ledger path expression, line 931, as of 2026-08-03). |
| R6 | `~/.claude/plugins/data/claude-workflow-engine-techdeveloper-org/` | NOT MEASURED | INFERRED | Naming pattern taken from a single observed `CLAUDE_PLUGIN_DATA` value (spike line 91 as of 2026-08-03). The spike could not test this: its plugin never wrote persistent data, so there was nothing for `--keep-data` to act on (spike lines 184-186 as of 2026-08-03). Expected absent for this plugin: nothing under `plugin/` reads or writes `CLAUDE_PLUGIN_DATA` (grep, 2026-08-03). |

**R4 names one entry today and may name two later.** `plugin/mcp-registry.json` lists two servers,
`post-tool-tracker` and `push-gate`. As of 2026-08-03 only the first can be written: the registry
marks `push-gate` as not built, and `register-mcp` reports that capability unavailable rather than
writing an entry pointing at a file that does not exist. Once V2-024 lands, treat `push-gate` as a
second R4 entry. Procedures A and B both read the ledger rather than a fixed list, so neither needs
editing when that happens -- but this row does.

**Warning on R4.** Whether `claude plugin uninstall` removes an `mcpServers` entry that `register-mcp`
wrote is the open question ADR-020 calls Path C. It is **INFERRED safe, not measured safe**, and the
executable procedure that would settle it is `docs/guides/adr-020-path-c-verification.md`, which has
not been performed. Treat R4 as "may or may not survive": check for it rather than assuming either
answer. Do not cite this runbook as evidence that it survives.

**Not residue -- measured removed.** Do not hunt for these; the spike confirmed uninstall clears them
(lines 178-196 as of 2026-08-03), and this machine's copies are clean as of 2026-08-03:

- the plugin's entry in `~/.claude/plugins/installed_plugins.json`
- the marketplace's entry in `~/.claude/plugins/known_marketplaces.json`
- `~/.claude/plugins/marketplaces/`, which was empty or absent after marketplace removal

**A note on `claude plugin prune`.** It does not clean R3. The spike ran it and it reported
`Nothing to prune (no auto-installed plugins at user scope)` and left the orphaned directory
untouched; its own help text scopes it to auto-installed dependency plugins (spike lines 198-205 as
of 2026-08-03). Running it is harmless and pointless here.

---

## 4. Procedure A -- the plugin is still installed (preferred)

Use this whenever the plugin has not yet been uninstalled. It is strictly better than Procedure B,
because step A1 uses the plugin's own supported reversal command, and that command stops existing the
moment the plugin is removed.

**Preconditions.**

- The plugin `claude-workflow-engine@techdeveloper-org` is currently installed.
- You can write to the settings file for the scope it was installed at.
- Nothing else is writing that settings file while you work.

**Point of no return: step A3. Rollback is valid up to and including step A2.** A1 and A2 have true
inverses -- reinstall, then re-register -- so the procedure is cleanly reversible while you are
inside them. A3 onward do not: they delete state whose only recovery is the backup you take in A0,
and A5 and A6 have no recovery at all. Section 7 states this per step.

A separate ordering hazard sits at A2 and is not the same thing: running A2 before A1 does not make
the procedure irreversible, but it does remove `unregister-mcp` from disk, which is the only
supported way to perform A1. If that has already happened, use Procedure B in section 5.

### A0. Back up the settings file

```
python -c "import pathlib,shutil,sys; p=pathlib.Path(sys.argv[1]).expanduser(); shutil.copy2(p, p.with_suffix('.json.pre-residue-cleanup')); print('backup:', p.with_suffix('.json.pre-residue-cleanup'))" ~/.claude/settings.json
```

*Verification:* the command prints a path, and that file exists and is byte-identical to
`~/.claude/settings.json`.

*Idempotent:* no. Re-running overwrites the backup with the current file. If you have already started
editing, re-running destroys the only copy of the original. Do not re-run.

### A1. Reverse the MCP registration, if there is one

```
python "${CLAUDE_PLUGIN_ROOT}/scripts/mcp_registration.py" unregister
```

*Verification:* the command reports `REMOVED` or `RESTORED` for each entry, and
`mcp_registration.py status` afterwards lists no capability as `REACHABLE` via a registered server.

*Idempotent:* yes. With an empty ledger it removes nothing and reports nothing removed.

Three things this step is doing that a manual edit cannot:

1. It removes only entries the ledger records as ours. An entry you registered yourself under the
   same name is never touched.
2. Where `register-mcp --force` displaced an entry you already had, it **restores** that entry rather
   than deleting the name. Reversal is not always deletion.
3. It refuses, with exit status 2, if removing the MCP-side push gate would leave no local push gate
   at all. That refusal is a decision for you to make, not for a cleanup script.

If the command refuses and you accept the consequence, re-run it with `--acknowledge-no-push-gate`.
Read `plugin/commands/unregister-mcp.md` before you do.

### A2. Uninstall the plugin

```
claude plugin uninstall claude-workflow-engine@techdeveloper-org
claude plugin marketplace remove techdeveloper-org
```

*Verification:* `claude plugin list` no longer lists `claude-workflow-engine`,
`~/.claude/plugins/installed_plugins.json` contains `"plugins": {}`, and both `enabledPlugins` and
`extraKnownMarketplaces` in `~/.claude/settings.json` are `{}`. That last clause is the state step A3
requires; check it here rather than discovering in A3 that it does not hold.

*Idempotent:* yes for practical purposes -- a second run reports the plugin is not installed and
changes nothing.

### A3. Remove the emptied bookkeeping keys (R1, R2)

Remove them only if they are empty. A non-empty value means another plugin or marketplace is still
registered, and deleting the key would deregister it too.

```
python -c "import json,pathlib,sys; p=pathlib.Path(sys.argv[1]).expanduser(); d=json.loads(p.read_text(encoding='utf-8')); removed=[k for k in ('enabledPlugins','extraKnownMarketplaces') if d.get(k)=={}]; [d.pop(k) for k in removed]; p.write_text(json.dumps(d, indent=2)+chr(10), encoding='utf-8'); print('removed:', removed)" ~/.claude/settings.json
```

*Verification:* the command prints the keys it removed, and re-reading the file shows neither
`enabledPlugins` nor `extraKnownMarketplaces` among its top-level keys.

*Idempotent:* yes. A second run finds neither key and prints `removed: []`.

Both keys are inert while empty. They do not re-enable anything and they reference nothing. Removing
them is cosmetic -- it restores the file's key set to its pre-install shape. It will not restore the
file's original bytes, because the file is re-serialised with two-space indentation.

### A4. Remove the orphaned cache directory (R3)

Check first. It may already be absent; see section 6.

```
python -c "import pathlib,shutil; p=pathlib.Path('~/.claude/plugins/cache/techdeveloper-org/claude-workflow-engine/0.1.0').expanduser(); print('present:', p.is_dir()); print('orphan marker:', (p/'.orphaned_at').is_file()); shutil.rmtree(p, ignore_errors=True); print('present after:', p.is_dir())"
```

*Verification:* the command prints `present after: False`.

*Idempotent:* yes. On an already-absent directory it prints `present: False` and removes nothing.

If `present` was `True` but `orphan marker` was `False`, stop. An unmarked directory is not an
orphan, and may belong to a live installation. Re-check that A2 completed.

Afterwards you may also remove the now-empty parent directories
`~/.claude/plugins/cache/techdeveloper-org/claude-workflow-engine/` and
`~/.claude/plugins/cache/techdeveloper-org/`, if no other version or plugin remains under them.

### A5. Remove the plugin data directory (R6), if it exists

```
python -c "import pathlib,shutil; p=pathlib.Path('~/.claude/plugins/data/claude-workflow-engine-techdeveloper-org').expanduser(); print('present:', p.is_dir()); shutil.rmtree(p, ignore_errors=True); print('present after:', p.is_dir())"
```

*Verification:* the command prints `present after: False`.

*Idempotent:* yes.

Expect `present: False`. Nothing in this plugin writes to `CLAUDE_PLUGIN_DATA`. If it prints `True`,
that is a finding worth reporting -- something wrote data this plugin is not known to write.

### A6. Remove the provenance ledger (R5) -- last

```
python -c "import pathlib; p=pathlib.Path('~/.claude/cwe-mcp-registrations.json').expanduser(); print('present:', p.is_file()); p.unlink(missing_ok=True); print('present after:', p.is_file())"
```

*Verification:* the command prints `present after: False`.

*Idempotent:* yes.

**This step is last on purpose, and the ordering is not stylistic.** The ledger is the only record of
which `mcpServers` entries this plugin added and which of your own entries it displaced. Delete it
before A1 has run and that record is gone: you can no longer tell an entry the plugin added from an
entry you added yourself, and a displaced entry can never be correctly restored. That is the
provenance-loss failure in general form, and the ledger exists specifically to avoid it. Removing it
after A1 costs nothing, because A1 has already consumed it.

If you reach A6 having skipped A1 -- for instance because you arrived here from Procedure B -- do
**not** delete the ledger until section 5 step B2 has used it.

---

## 5. Procedure B -- the plugin is already uninstalled (recovery)

Use this only if `claude plugin uninstall` has already run and `unregister-mcp` was never run. You
are past Procedure A's point of no return, so the supported reversal is unavailable and the steps
below edit `settings.json` by hand.

**Preconditions.**

- The plugin is no longer installed and `${CLAUDE_PLUGIN_ROOT}` no longer resolves.
- You can write to `~/.claude/settings.json`.
- Nothing else is writing that file while you work.

### B0. Back up the settings file

Identical to A0, with the same verification and the same warning about not re-running it.

### B1. Read the ledger before changing anything

```
python -c "import json,pathlib; p=pathlib.Path('~/.claude/cwe-mcp-registrations.json').expanduser(); print(p.read_text(encoding='utf-8') if p.is_file() else 'NO LEDGER')"
```

*Verification:* the command prints either JSON mapping server ids to records, or `NO LEDGER`.

*Idempotent:* yes -- it only reads.

If it prints `NO LEDGER`, `register-mcp` never ran, R4 and R5 do not apply to you, and you should
skip to B3. Do not remove any `mcpServers` entry on suspicion: without the ledger you cannot tell
this plugin's entries from your own, and `post-tool-tracker` in particular is a name a user may
legitimately have registered independently. On the machine this document was written against,
`mcpServers` contained `post-tool-tracker` and no ledger existed -- that entry was the user's own.

### B2. Remove or restore each entry the ledger names

Each ledger record holds a `spec` object, which is what `register-mcp` wrote, and optionally a
`displaced` object, which is the entry it took the name from. For each server id in the ledger:

- If its record contains a `displaced` object, **replace** the `mcpServers` entry of that id with the
  `displaced` object. That restores the entry you had before `register-mcp --force` took the name.
- Otherwise, **delete** the `mcpServers` entry of that id.

Before either action, compare the current `mcpServers` entry against the record's `spec`. If they
differ, something changed that entry after `register-mcp` wrote it -- most likely you did. Leave it
alone and report it rather than overwriting an edit you may want. The supported command does not make
this comparison; by hand you can afford to.

*Verification:* for every id in the ledger, `settings.json` either no longer contains that key, or
contains exactly the object recorded under `displaced`. No `mcpServers` key absent from the ledger
has changed.

*Idempotent:* yes, if applied as stated -- the target state is fixed by the ledger's contents.

Change no `mcpServers` entry whose id does not appear in the ledger.

### B3. Continue with the remaining residue

Run steps A3, A4 and A5 as written, then A6 last. All four are idempotent and none of them depends on
the plugin being present.

---

## 6. Accepted Claude-Code-level limitation: the orphaned plugin cache directory

**This section is the reason SRS FR-31 measures plugin-attributable residue rather than total
residue. It is referenced by V2-022 (GitHub #278). Do not rename it without updating that issue and
`tests/test_uninstall_residue_runbook.py`.**

The two items below are **known and accepted limitations of Claude Code itself**. They are not
defects in this plugin, they are not something this plugin can prevent or detect, and no test in this
repository should assert they are absent after an uninstall.

1. **The orphaned plugin cache directory.** `claude plugin uninstall` leaves the plugin's cached files
   at `~/.claude/plugins/cache/techdeveloper-org/claude-workflow-engine/0.1.0/`.
2. **The `.orphaned_at` marker file** written inside that directory to mark it as superseded.

Three facts fix this as accepted rather than open:

- **It is measured, not suspected.** The spike observed exactly this, with all files intact and the
  marker added, at `plugin_schema_spike.md` Item 4 (lines 180-183 as of 2026-08-03).
- **`claude plugin prune` does not reclaim it.** Measured, same source (lines 198-205 as of
  2026-08-03). `prune` targets auto-installed dependency plugins, which this is not.
- **No plugin-side control exists, of any kind.** The plugin ships zero hooks (ADR-010), so there is
  no interception point before uninstall; and after uninstall the plugin is gone, so there is no
  execution point for a check afterwards. Prevention and detection are both structurally unavailable,
  which is why the mitigation is this document and section 4 step A4 rather than code.

The two `settings.json` bookkeeping keys, R1 and R2, are accepted on the same grounds and for the
same reason: `claude plugin uninstall` empties them and does not remove them, and no plugin-side
control can change that. They are covered here so that a test may assert their *emptiness*, never
their absence.

**One qualification, stated because it would otherwise read as stronger than the evidence.** On
2026-08-03 the cache directory left behind by the spike was no longer on disk (section 2). Whether
something reclaims these directories over time is unknown -- the spike hypothesised a garbage
collector it could not identify, and a manual deletion is equally consistent with what was observed.
The limitation is therefore stated as "uninstall leaves it", which is measured, and not as "it stays
forever", which is not.

---

## 7. Rollback

Rollback is listed in reverse order of the forward steps, and each entry states the state it needs to
be applicable.

**Rollback is valid up to and including step A2; step A3 is the point of no return.** A1 and A2 have
true inverses. A3 onward do not: A3 is recoverable only from the A0 backup, and only for
`settings.json`, while A4, A5 and A6 delete state that no inverse restores.

| Undo | Forward step | Applicable when | How |
|---|---|---|---|
| Restore the ledger | A6 | Never -- deletion is final | No inverse. The ledger is not reconstructible; this is why A6 is ordered last. |
| Restore the data directory | A5 | Never | No inverse. Expected to have been absent. |
| Restore the cache directory | A4 | Marketplace source still reachable | Reinstall the plugin. Not a true inverse: the restored tree is a fresh fetch, not the bytes you deleted, and it is not marked `.orphaned_at`. |
| Restore the bookkeeping keys | A3 | The A0 backup exists and nothing has written the file since | `cp` the A0 backup over `~/.claude/settings.json`. This reverts every change made after A0, not only A3. |
| Reinstall the plugin | A2 | Always | `claude plugin marketplace add` then `claude plugin install`. |
| Re-register the MCP entries | A1 | The plugin is installed again | Run `register-mcp`. This is a compensating action, not an inverse: it writes a fresh registration, and a displaced entry that A1 restored is displaced again only if you pass `--force`. |

Restoring the A0 backup is the single control that covers every `settings.json` change in this
runbook. It restores the object, not the bytes, if the file was formatted differently before.

## 8. Escalation

**No regulatory reporting window applies.** This procedure edits a developer machine's local
configuration. It processes no personal data, transmits nothing, and is not a security incident
class, so neither the CERT-In Directions 2022 reporting timeline nor GIGW 3.0 attaches to it. The
budgets below are working limits so that a stuck operator stops rather than improvising; they are not
a compliance clock and should not be presented as one.

| Stage | Budget | Escalate to |
|---|---|---|
| A verification point fails and the immediate cause is not obvious | 15 minutes | Stop editing. Restore the A0 backup (section 7) and re-read section 3 before trying again. |
| The restore itself does not produce a file that parses as JSON | 15 minutes | Stop. Do not hand-repair the file. Raise an issue against SRS FR-36 with the backup and the current file attached. |
| A path in section 3 does not exist and is not covered by section 6 | 30 minutes | Raise an issue against SRS FR-36. A path that is wrong here is a defect in this document, and the test named in section 6 should have caught it. |
| `unregister-mcp` refuses and you are unsure whether to acknowledge | No budget -- do not rush it | Read `plugin/commands/unregister-mcp.md`. This is a deliberate decision point, not an obstacle to clear. |

Handoff context for any of the above: the CLI version from `claude --version`, the settings path you
used, whether the A0 backup exists, and which step number you stopped at.

## 9. What this runbook does not establish (explanation)

Stated so it is not read as broader than it is.

- **It does not establish that R4 survives uninstall.** ADR-020 Path C is inferred, not measured. The
  procedure that would settle it is `docs/guides/adr-020-path-c-verification.md`, and it has not been
  run. Section 4 handles R4 by checking rather than by assuming.
- **It does not establish that R3 and R6 are at exactly these paths for this plugin.** The layout was
  observed once, against a different plugin, and this plugin's names were substituted into it. The
  substitution is machine-checked against the two manifests by
  `tests/test_uninstall_residue_runbook.py`, which proves the strings are *current*, not that the
  layout is *right*.
- **It does not establish anything about a CLI version other than 2.1.220.** Uninstall behaviour is a
  property of the host, and the host changes. If `claude --version` reports something else, treat
  every MEASURED label in section 3 as expiring without notice and re-open the spike.
- **It does not cover project or local scope.** The spike measured user scope only. Key names are
  scope-independent; which file holds them is not.
- **It does not cover a partly-failed uninstall.** Every measurement was taken after an uninstall
  that reported success.

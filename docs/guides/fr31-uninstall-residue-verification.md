# FR-31 uninstall residue verification procedure

**Status: NOT PERFORMED. Blocked by an explicit owner ruling, not by a technical limitation.**

This is the executable procedure for SRS FR-31 / PRD FR-18 acceptance criterion (a): after
`claude plugin uninstall`, no MCP tool the plugin registered remains callable in a fresh
session. It exists because that measurement could not be performed during V2-022.

It is deliberately the same shape as `docs/guides/adr-020-path-c-verification.md`, which V2-016
wrote for the same reason. The two procedures overlap and **should be run in the same sitting**:
they need the same authorisation, the same install/uninstall cycle and the same snapshots.
Section 7 states exactly how they differ, so neither is mistaken for the other.

---

## 1. Why this is a document rather than a result (explanation)

The criterion asks whether a tool this plugin registered is still callable after the plugin is
uninstalled. Answering it requires a real `claude plugin install` followed by a real
`claude plugin uninstall`.

The project owner ruled, during V2-016 and again for V2-022, that no live install/uninstall
cycle may be run. The measured reason is FR-14a spike item 4: install writes `enabledPlugins`
and `extraKnownMarketplaces` into a settings scope and **uninstall never removes those keys, it
only empties them**, and it leaves an orphaned cache directory that `claude plugin prune` does
not reclaim. At user scope that mutates the owner's live configuration. At local scope it
mutates `.claude/settings.local.json`, which is git-tracked in this repository.

Two things were deliberately **not** done in place of the measurement:

- The cycle was not approximated by hand-editing a settings file. That measures whether the
  engineer can delete a key, which is a different question, and reporting it as the FR-31 result
  would be a fake green.
- The test was not written to pass in the absence of the measurement. It skips, and the skip
  message names the ruling, the criterion and the way forward.

**Criterion (a) is therefore NOT MET, and the cause is an owner decision.**

## 2. What is already measured, and is not blocked (explanation)

Criterion (a) decomposes into two sub-claims with different evidence. Stated separately so the
blocked half is not read as blocking the whole.

| Sub-claim | Route | Status |
|---|---|---|
| A tool registered by `register-mcp` stops being callable after `unregister-mcp` | the plugin's own supported reversal | **MEASURED.** `tests/test_register_mcp.py::TestReachabilityIsMeasured::test_capability_flips_unreachable_reachable_unreachable` spawns the process the settings entry names and completes a real JSON-RPC lifecycle handshake at each state. |
| A tool registered by `register-mcp` stops being callable after `claude plugin uninstall`, without `unregister-mcp` having run | Claude Code's own command | **NOT MEASURED.** This procedure. Identical to ADR-020 Path C. |

Under ADR-019 the plugin bundles zero MCP servers, so `register-mcp` is the only route by which
this plugin can put a tool in `mcpServers` at all. That is why the second row is the whole of
the remaining question.

## 3. What a failure would cost (explanation)

If uninstall does **not** remove the entry, a tool the plugin registered stays callable after
the plugin is gone. Its entry point still exists on the user's machine -- `register-mcp` writes
an absolute path to a separate server checkout, not to anything inside the plugin -- so the
entry does not merely linger, it keeps working.

There is no plugin-side control available. Prevention is impossible: the plugin ships zero hooks
(ADR-010), so there is no interception point before uninstall. Detection is impossible: after
uninstall the plugin is gone, so no `doctor` command and no per-command precondition can run.

**Named mitigation, stated in advance so it is not chosen under pressure:** the mitigation is
`docs/guides/uninstall-residue.md` Procedure B, which reverses the registration by hand using
the provenance ledger. The ledger is written beside the settings file rather than inside the
plugin tree exactly so that it survives the plugin's removal. Step 6 below confirms it did.

---

## 4. Procedure

Budget: about 15 minutes. Requires authorisation to install and uninstall a plugin against a
real settings scope.

### 4.0 Preconditions

- A settings scope you are authorised to mutate. Prefer a throwaway `CLAUDE_CONFIG_DIR` over the
  live `~/.claude` if the harness under test honours one; if it does not, this procedure
  necessarily runs against the real scope, which is the whole reason for the ruling.
- The `mcp-*` server checkouts available, and their parent directory noted as `<SERVER_ROOT>`.
- A scratch directory for the snapshots, noted as `<SNAP>`.
- Nothing else writing the settings file for the duration. This matters: see step 5.

Record the CLI version now, not at the end. Uninstall behaviour is a property of the host, and
a result recorded without a version cannot be compared against a later run.

```
claude --version
```

### 4.1 Resolve the settings and ledger paths -- do not assume them

Every later step is invalid if the settings path is not the file `register-mcp` actually writes.
Do not infer it. After step 4.2 has installed the plugin:

```
python "${CLAUDE_PLUGIN_ROOT}/scripts/mcp_registration.py" status --json
```

The `settings` and `ledger` fields of that output are the paths to use verbatim.
`settings_sha256` in the same output is a free cross-check.

`CLAUDE_PLUGIN_ROOT` is populated by Claude Code for processes it spawns and is usually unset in
a bare terminal. Either run these steps through the `/register-mcp` command inside a Claude Code
session, or export `CLAUDE_PLUGIN_ROOT` by hand pointing at the installed plugin directory -- the
one containing `.claude-plugin/plugin.json`.

### 4.2 Install the plugin

```
claude plugin marketplace add techdeveloper-org/claude-workflow-engine
claude plugin install claude-workflow-engine@techdeveloper-org
```

### 4.3 Register, then snapshot the BEFORE state

```
python "${CLAUDE_PLUGIN_ROOT}/scripts/mcp_registration.py" register --server-root <SERVER_ROOT>
```

Confirm the command reported `ADDED post-tool-tracker`. If it reported `SKIP`, the entry point
was not found and **there is nothing to measure** -- fix `<SERVER_ROOT>` and repeat. A run with
no entry written reproduces exactly the gap that made this unmeasurable in the first place.

Copy both files, using the paths step 4.1 reported:

```
cp <SETTINGS> <SNAP>/before.json
cp <LEDGER>   <SNAP>/ledger.json
```

Take the ledger copy **now**, before uninstall. Step 6 checks whether the original survived; the
copy is what the verdict is computed from either way.

### 4.4 Uninstall

```
claude plugin uninstall claude-workflow-engine@techdeveloper-org
```

### 4.5 Snapshot the AFTER state, and run the test

```
cp <SETTINGS> <SNAP>/after.json
```

```
CWE_ALLOW_LIVE_PLUGIN_INSTALL=1 \
CWE_UNINSTALL_SNAPSHOT_BEFORE=<SNAP>/before.json \
CWE_UNINSTALL_SNAPSHOT_AFTER=<SNAP>/after.json \
CWE_UNINSTALL_SNAPSHOT_LEDGER=<SNAP>/ledger.json \
python -m pytest tests/test_uninstall_residue_attribution.py -p no:randomly \
  -k test_live_uninstall_leaves_zero_attributable_residue -v
```

The test computes the verdict. It reports two things separately, and both must be empty:

- **residue** -- an `mcpServers` entry whose id the ledger claims and whose value is still the
  spec `register-mcp` wrote. This is criterion (a) failing.
- **damage** -- an `mcpServers` entry the ledger does **not** claim that changed, or a `displaced`
  entry that was not restored. This is the opposite failure and is a finding in its own right.

| Test outcome | Verdict |
|---|---|
| PASSED | Criterion (a) is **MET** for this CLI version. Record it per section 5. |
| FAILED on `residue` | Criterion (a) is **NOT MET**. Uninstall left a callable tool behind. Record it, and raise the FR-31 mitigation as scope. |
| FAILED on `damage` | A different and more serious defect: uninstall touched configuration this plugin never claimed. Report it regardless of the residue result. |
| SKIPPED | The environment variables did not take effect. The measurement did not run. Do not record a verdict. |

**A skip is not a pass.** If the run reports `1 skipped`, one of the four variables is unset or
names a file that does not exist. Fix it and repeat.

### 4.6 The control that stops a false PASS

The verdict is a two-point comparison across a window in which other writers exist.

```
python -c "import json,sys; a=json.load(open(sys.argv[1])); b=json.load(open(sys.argv[2])); ak=set(a)-{'mcpServers'}; bk=set(b)-{'mcpServers'}; print('non-mcpServers keys added:', sorted(bk-ak)); print('non-mcpServers keys removed:', sorted(ak-bk))" <SNAP>/before.json <SNAP>/after.json
```

- `non-mcpServers keys added` is expected to contain `enabledPlugins` and
  `extraKnownMarketplaces` if they were not already present. That is measured host behaviour --
  they are emptied, never removed -- and is the accepted limitation recorded in
  `docs/guides/uninstall-residue.md` section 6. **It is not a finding.**
- Anything in `non-mcpServers keys removed` **is** a finding and should be reported regardless of
  the criterion (a) verdict.

### 4.7 Confirm the ledger outlived the plugin

The provenance ledger lives beside the settings file, not inside the plugin, specifically so that
an uninstalled plugin still leaves the user able to identify and reverse what it registered. That
is the entire mitigation named in section 3.

```
python -c "import pathlib,sys; p=pathlib.Path(sys.argv[1]); print('ledger present after uninstall:', p.is_file())" <LEDGER>
```

If it prints `False`, the design intent failed: a user whose plugin is uninstalled has no
supported way to tell this plugin's `mcpServers` entries from their own. Report it. It does not
change the criterion (a) verdict, and it does change the severity of a FAIL.

### 4.8 Restore

If the run touched a live scope, follow `docs/guides/uninstall-residue.md` Procedure B, which
uses the ledger copy from step 4.3. Do not delete `mcpServers` entries by name.

---

## 5. Recording the result

Record four facts, not one: the verdict, the date, the CLI version from step 4.0, and the
settings path used. A verdict without the CLI version cannot be compared against a later run; a
verdict without the settings path cannot be reproduced.

Amend this document's status line in place, and amend the FR-31 row wherever the issue tracker
records acceptance. On a FAIL, also raise the mitigation as scope against whoever owns FR-18.

## 6. Run this with the ADR-020 Path C procedure, not instead of it

Both procedures need the same authorisation and the same install/uninstall cycle. Run them
together and take one set of snapshots. They are not the same question:

- **ADR-020 Path C** (`docs/guides/adr-020-path-c-verification.md`) asks whether the entry
  **survives**. Its PASS is `post-tool-tracker` still present after uninstall, because Path C
  wants the local push gate to outlive the plugin.
- **FR-31 criterion (a)** asks whether the tool **stops being callable**. Its PASS is
  `post-tool-tracker` absent after uninstall, because FR-31 wants zero functional residue.

**The two have opposite pass conditions on the same measurement.** That is a genuine, unresolved
tension between two requirements, not a mistake in either document, and whoever runs the cycle
will observe exactly one outcome and must record it against both. It is called out here so it is
discovered before the run rather than during it.

## 7. What this procedure does not establish

Stated so a result is not read as broader than it is.

- It measures **one** entry, `post-tool-tracker`, written by **one** command version, against
  **one** CLI version. `push-gate` is not built yet (V2-024); once it is, it becomes a second
  entry and this procedure covers it without modification, because the test reads the ledger
  rather than a fixed list.
- It does not test the `--force` path, where `register-mcp` displaced an entry the user already
  had. The test's `damage` check covers that case if the snapshots contain it, but this procedure
  does not create it. A forced registration has a strictly larger blast radius, because a loss
  there is the user's own configuration rather than ours.
- It does not establish anything about the orphaned plugin cache directory or the emptied
  bookkeeping keys. Those are accepted Claude-Code-level limitations, documented at
  `docs/guides/uninstall-residue.md` section 6, and no step here asserts they are absent.
- It does not cover project or local scope. Key names are scope-independent; which file holds
  them is not.
- It does not cover a partly-failed uninstall.

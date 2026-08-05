# NFR-11 lifecycle verification procedure (install and uninstall halves)

**Status: NOT PERFORMED. Blocked by an explicit owner ruling, not by a technical limitation.**

This is the executable procedure for the two halves of SRS NFR-11 / PRD NFR-5 that cannot be
measured without a live plugin lifecycle: the **install** test and the **uninstall** test. The
**invoke** test and the **register/unregister round trip** are not blocked and are measured in
`tests/test_plugin_lifecycle.py` on every run.

It is deliberately the same shape as `docs/guides/adr-020-path-c-verification.md` (V2-016) and
`docs/guides/fr31-uninstall-residue-verification.md` (V2-022). **All three should be run in the
same sitting.** They need the same authorisation and the same install/uninstall cycle, and this
one adds only two extra snapshots taken earlier in that same cycle. Section 6 states exactly how
the three differ, so no result is recorded against the wrong question.

---

## 1. Why this is a document rather than a result (explanation)

NFR-11's install test asks which keys `claude plugin install` writes to `settings.json`, and its
uninstall test asks what survives `claude plugin uninstall`. Both need the real commands.

The project owner ruled, during V2-016, again for V2-022, and again for V2-023, that no live
install/uninstall cycle may be run. The measured reason is `plugin_schema_spike.md` Item 4:
install writes `enabledPlugins` and `extraKnownMarketplaces` into a settings scope and
**uninstall never removes those keys, it only empties them**, and it leaves an orphaned cache
directory that `claude plugin prune` does not reclaim. At user scope that mutates the owner's
live configuration. At local scope it mutates `.claude/settings.local.json`, which is git-tracked
in this repository.

Two things were deliberately **not** done in place of the measurement:

- The cycle was not approximated by hand-editing a settings file. That measures whether the
  engineer can add a key, which is a different question, and reporting it as the NFR-11 result
  would be a fake green.
- Neither test was written to pass in the absence of the measurement. Both skip, and each skip
  message names the ruling, the criterion and the way forward.

**The install and uninstall halves of NFR-11 are therefore NOT MET, and the cause is an owner
decision.**

## 2. What is already measured, and is not blocked (explanation)

Stated separately so the blocked halves are not read as blocking the whole requirement.

| Claim | Route | Status |
|---|---|---|
| The plugin ships NO `.mcp.json`, by either the filesystem route or the manifest `mcpServers` path-override | `scripts/verify_plugin_conformance.py` FF-3, called directly by the test | **MEASURED**, every run |
| A fresh install cannot make any MCP capability reachable (FR-26 (a)) | Follows from the row above: the plugin ships no route to an `mcpServers` entry | **MEASURED**, every run |
| The progress writer flips unreachable to reachable across the two steps (FR-26 (b)) | Real process spawn plus a real JSON-RPC handshake at each state | **MEASURED**, every run |
| The full unreachable -> reachable -> unreachable round trip | `tests/test_register_mcp.py::TestReachabilityIsMeasured::test_capability_flips_unreachable_reachable_unreachable` | **MEASURED** by V2-016; credited, not re-proved |
| register/unregister returns `settings.json` to its pre-registration state, at the OBJECT level | Real command pair against a scratch settings file | **MEASURED**, every run |
| Byte-identical restoration | Same, in both branches of the condition | **MEASURED** as a conditional: it holds only when the file was already two-space indented with matching line endings |
| The settings delta `claude plugin install` produces | This procedure, step 4.3 | **NOT MEASURED** |
| What survives `claude plugin uninstall` | This procedure, step 4.6 | **NOT MEASURED** |

The push-gate half of FR-26 (b) is **not satisfiable today** and this is measured rather than
assumed: the catalogue marks the push-gate server `not_built_yet` (V2-024), so `register-mcp`
writes no entry for it and it stays unreachable after step two. FR-26 (b) asks for two
capabilities to flip; one can.

## 3. The owner ruling this procedure records (explanation)

V2-022 found that ADR-020 Path C and PRD FR-18 acceptance criterion (a) demand opposite outcomes
from the same one-shot measurement. Path C's PASS is that uninstall does NOT remove a
`register-mcp`-written `mcpServers` entry, so the version push gate outlives the plugin.
FR-18 (a)'s PASS is that it is gone.

**The owner ruled that ADR-020 Path C wins.** A `register-mcp`-written entry persists in
user-scope settings across plugin uninstall unless the user explicitly removed it. FR-18 (a) is
scope-limited to plugin-specific **operational** tools and does not reach safety-enforcement
gates. Non-essential residue -- caches, ephemeral state -- is still purged.

The ruling is recorded at `docs/REVIEW-INDEX.md` item 37, which is the authority for everything
below. `tests/test_plugin_lifecycle.py` pins itself to that record clause by clause, so a revert
of the ruling breaks a test rather than silently leaving the tests asserting the wrong verdict.

`tests/test_plugin_lifecycle.py::uninstall_verdict` encodes exactly that narrowing: it partitions
V2-022's residue report by the catalogue's own `capability` field, so a surviving
safety-enforcement gate is **expected persistence** and a surviving operational tool is still
**residue**.

Three consequences are recorded here rather than discovered during a run:

1. **`tests/test_uninstall_residue_attribution.py` and `tests/test_plugin_lifecycle.py` will
   disagree on a surviving gate entry, on purpose.** V2-022's test is the unnarrowed reading and
   fails; this one is the narrowed reading and passes. That difference is the ruling. Record both
   outcomes; do not treat the disagreement as a defect in either.
2. **The catalogue currently offers no gate entry to exempt.** `push-gate` is `not_built_yet`, so
   the only entry `register-mcp` can write today is the operational progress writer, which the
   narrowing does NOT exempt. A run performed before V2-024 lands therefore resolves the tension
   against an operational entry, and FR-18 (a) can still FAIL. Record that as the result; it is
   an outcome of the ruling, not a bug.
3. **Three shipped documents are stale against the ruling.** `docs/phase-0-requirements/prd-v2.md`
   FR-18 and `SRS.md` FR-31 still carry the unnarrowed "no MCP tool the plugin registered remains
   callable" wording, and `docs/guides/adr-020-path-c-verification.md` still presents Path C as an
   open question with a FAIL branch that promotes ADV-012. Whoever owns those requirements should
   amend them. Until then, follow this document, not those texts.

---

## 4. Procedure

Budget: about 20 minutes when run together with the other two procedures. Requires authorisation
to install and uninstall a plugin against a real settings scope.

### 4.0 Preconditions

- A settings scope you are authorised to mutate. Prefer a throwaway `CLAUDE_CONFIG_DIR` over the
  live `~/.claude` if the harness under test honours one; if it does not, this procedure
  necessarily runs against the real scope, which is the whole reason for the ruling.
- The `mcp-*` server checkouts available, and their parent directory noted as `<SERVER_ROOT>`.
- A scratch directory for the snapshots, noted as `<SNAP>`.
- Nothing else writing the settings file for the duration. This matters: see step 4.7.

Record the CLI version now, not at the end. Install and uninstall behaviour are properties of the
host, and a result recorded without a version cannot be compared against a later run.

```
claude --version
```

### 4.1 Snapshot the PRE-INSTALL state

Take this **before** `marketplace add`, not after. The install test's whole subject is the delta
across the marketplace-add and install steps, so a baseline taken later measures nothing.

```
cp <SETTINGS> <SNAP>/install-before.json
```

`<SETTINGS>` at this point is your intended target -- normally `~/.claude/settings.json`, or
whatever `CLAUDE_SETTINGS_FILE` redirects to. Step 4.3 re-confirms it against what the plugin
actually writes; if they disagree, discard this baseline and start again from 4.1.

### 4.2 Install the plugin

```
claude plugin marketplace add techdeveloper-org/claude-workflow-engine
claude plugin install claude-workflow-engine@techdeveloper-org
```

### 4.3 Resolve the settings and ledger paths -- do not assume them

```
python "${CLAUDE_PLUGIN_ROOT}/scripts/mcp_registration.py" status --json
```

The `settings` and `ledger` fields of that output are the paths to use verbatim for every later
step. `settings_sha256` is a free cross-check.

`CLAUDE_PLUGIN_ROOT` is populated by Claude Code for processes it spawns and is usually unset in
a bare terminal. Either run these steps through the `/register-mcp` command inside a Claude Code
session, or export `CLAUDE_PLUGIN_ROOT` by hand pointing at the installed plugin directory -- the
one containing `.claude-plugin/plugin.json`.

If the `settings` field is not the file you snapshotted in 4.1, **stop**. Re-snapshot against the
reported path and repeat from 4.1.

### 4.4 Snapshot the POST-INSTALL state, and run the install test

Take this **before** `register-mcp` runs. Registration writes `mcpServers`, which is not part of
what install does, and including it would attribute the plugin's own command to the host's.

```
cp <SETTINGS> <SNAP>/install-after.json
```

```
CWE_ALLOW_LIVE_PLUGIN_INSTALL=1 \
CWE_INSTALL_SNAPSHOT_BEFORE=<SNAP>/install-before.json \
CWE_INSTALL_SNAPSHOT_AFTER=<SNAP>/install-after.json \
python -m pytest tests/test_plugin_lifecycle.py -p no:randomly \
  -k test_live_install_writes_only_the_measured_keys -v
```

The test computes the verdict. It permits exactly two top-level keys to move --
`extraKnownMarketplaces` and `enabledPlugins`, whether they were added or re-filled from an
earlier `{}` -- and requires that `enabledPlugins` names **this** plugin.

| Test outcome | Verdict |
|---|---|
| PASSED | The install half is **MET** for this CLI version. Record it per section 5. |
| FAILED naming a top-level key | Install touched a key the spike never measured. Record it and report it against FR-14a Item 3, whose measurement it contradicts. |
| FAILED naming a hook event | Install added or altered a hook. This is an ADR-010 violation and is more serious than the criterion it failed. Report it regardless. |
| FAILED on `enabledPlugins` not naming this plugin | The snapshot did not capture an install of this plugin. Do not record a verdict; fix and repeat. |
| SKIPPED | The environment variables did not take effect. The measurement did not run. Do not record a verdict. |

**A skip is not a pass.** If the run reports `1 skipped`, one of the three variables is unset or
names a file that does not exist. Fix it and repeat.

### 4.5 Register, then snapshot the pre-uninstall state

```
python "${CLAUDE_PLUGIN_ROOT}/scripts/mcp_registration.py" register --server-root <SERVER_ROOT>
```

Confirm the command reported `ADDED post-tool-tracker`. If it reported `SKIP`, the entry point
was not found and **there is nothing to measure** -- fix `<SERVER_ROOT>` and repeat.

```
cp <SETTINGS> <SNAP>/before.json
cp <LEDGER>   <SNAP>/ledger.json
```

Take the ledger copy **now**, before uninstall. The copy is what the verdict is computed from
whether or not the original survives.

These are the same two snapshots
`docs/guides/fr31-uninstall-residue-verification.md` step 4.3 asks for, under the same names. Take
them once.

### 4.6 Uninstall, snapshot the AFTER state, and run the uninstall test

```
claude plugin uninstall claude-workflow-engine@techdeveloper-org
```

```
cp <SETTINGS> <SNAP>/after.json
```

```
CWE_ALLOW_LIVE_PLUGIN_INSTALL=1 \
CWE_UNINSTALL_SNAPSHOT_BEFORE=<SNAP>/before.json \
CWE_UNINSTALL_SNAPSHOT_AFTER=<SNAP>/after.json \
CWE_UNINSTALL_SNAPSHOT_LEDGER=<SNAP>/ledger.json \
python -m pytest tests/test_plugin_lifecycle.py -p no:randomly \
  -k test_live_uninstall_leaves_no_operational_residue -v
```

The test reports three things and only the first two are asserted on:

- **residue** -- a surviving `mcpServers` entry the ledger claims, whose capability is NOT a
  safety-enforcement gate. This is the narrowed FR-18 (a) failing.
- **damage** -- an entry the ledger does not claim that changed, or a `displaced` entry that was
  not restored. The opposite failure, and a finding in its own right.
- **expected_persistence** -- a surviving entry whose capability IS a safety-enforcement gate.
  Under the owner's ruling this is correct behaviour and is reported, never failed on.

| Test outcome | Verdict |
|---|---|
| PASSED with `expected_persistence` empty | Nothing of ours survived. Record it. |
| PASSED with `expected_persistence` non-empty | ADR-020 Path C is **measured safe**. Record it against ADR-020 as well, and leave ADV-012 `NAMED, NOT ADOPTED`. |
| FAILED on `residue` | The narrowed FR-18 (a) is **NOT MET**. Record it, and raise the mitigation as scope against whoever owns FR-18. |
| FAILED on `damage` | Uninstall touched configuration this plugin never claimed. Report it regardless of the residue result. |
| SKIPPED | The measurement did not run. Do not record a verdict. |

Run V2-022's test on the **same three snapshots** in the same sitting:

```
python -m pytest tests/test_uninstall_residue_attribution.py -p no:randomly \
  -k test_live_uninstall_leaves_zero_attributable_residue -v
```

Per section 3 item 1, the two will disagree if a gate entry survived. Record both.

### 4.7 The control that stops a false PASS

Both verdicts are two-point comparisons across a window in which other writers exist.

```
python -c "import json,sys; a=json.load(open(sys.argv[1])); b=json.load(open(sys.argv[2])); ak=set(a)-{'mcpServers'}; bk=set(b)-{'mcpServers'}; print('non-mcpServers keys added:', sorted(bk-ak)); print('non-mcpServers keys removed:', sorted(ak-bk))" <SNAP>/before.json <SNAP>/after.json
```

- `non-mcpServers keys added` is expected to contain `enabledPlugins` and
  `extraKnownMarketplaces` if they were not already present. That is measured host behaviour --
  they are emptied, never removed -- and is the accepted limitation recorded in
  `docs/guides/uninstall-residue.md` section 6. **It is not a finding.**
- Anything in `non-mcpServers keys removed` **is** a finding and should be reported regardless of
  either verdict.

### 4.8 Restore

If the run touched a live scope, follow `docs/guides/uninstall-residue.md` Procedure B, which uses
the ledger copy from step 4.5. Do not delete `mcpServers` entries by name.

---

## 5. Recording the result

Record five facts, not one: the install verdict, the uninstall verdict, the date, the CLI version
from step 4.0, and the settings path used. A verdict without the CLI version cannot be compared
against a later run; a verdict without the settings path cannot be reproduced.

Amend this document's status line in place, and amend the NFR-11 row wherever the issue tracker
records acceptance. Where the run also settles ADR-020 Path C or FR-31, amend those records too --
one cycle answers all three questions and leaving two of them open would waste the authorisation.

## 6. How the three procedures differ

They share one cycle and one set of snapshots. They do not share a question.

- **`adr-020-path-c-verification.md`** asks whether a `register-mcp`-written entry **survives**
  uninstall. Its PASS is the entry still present.
- **`fr31-uninstall-residue-verification.md`** asks whether the tool **stops being callable**. Its
  PASS is the entry absent, on the UNNARROWED reading of FR-31.
- **This document** asks the same uninstall question on the **NARROWED** reading the owner ruled
  for, and additionally asks what **install** wrote. Its uninstall PASS is: no surviving
  *operational* entry, with a surviving *safety-enforcement gate* entry permitted.

The first two have opposite pass conditions on the same measurement. The owner resolved that in
favour of the first; this document is where that resolution is executable. The second is not yet
amended and will still report a FAIL on a surviving gate entry -- see section 3 item 1.

## 7. What this procedure does not establish

Stated so a result is not read as broader than it is.

- It measures **one** install of **one** plugin from **one** marketplace against **one** CLI
  version. Install behaviour is a property of the host and a result expires without notice when
  the host changes.
- The install verdict says nothing about process count. NFR-1's "zero processes attributable to
  the plugin in an uninvoked session" is a separate measurement with its own harness at
  `tests/test_nfr1_harness.py`.
- It does not exercise the `--force` registration path, where `register-mcp` displaced an entry
  the user already had. The uninstall test's `damage` check covers that case if the snapshots
  contain it, but no step here creates it. A forced registration has a strictly larger blast
  radius, because a loss there is the user's own configuration rather than ours.
- It does not establish anything about the orphaned plugin cache directory or the emptied
  bookkeeping keys. Those are accepted Claude-Code-level limitations documented at
  `docs/guides/uninstall-residue.md` section 6, and no step here asserts they are absent.
- It does not cover project or local scope. Key names are scope-independent; which file holds them
  is not.
- It does not cover a partly-failed install or a partly-failed uninstall.

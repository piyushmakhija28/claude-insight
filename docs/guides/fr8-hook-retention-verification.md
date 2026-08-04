# FR-8 hook retention verification procedure (Stop and Notification across a full cycle)

**Status: NOT PERFORMED. Blocked by an explicit owner ruling, not by a technical limitation.**

This is the executable procedure for PRD FR-8 / SRS FR-18: an install/uninstall cycle must leave
the pre-existing user-level `Stop` and `Notification` hook registrations byte-identical to their
pre-install state.

It is deliberately the same shape as `docs/guides/adr-020-path-c-verification.md` (V2-016),
`docs/guides/fr31-uninstall-residue-verification.md` (V2-022) and
`docs/guides/nfr11-lifecycle-verification.md` (V2-023). **All four should be run in the same
sitting.** They need the same authorisation and the same cycle, and this one adds no new steps at
all: it consumes two snapshots the NFR-11 procedure already takes. Section 6 states exactly how
the four differ, so no result is recorded against the wrong question.

---

## 1. Why this is a document rather than a result (explanation)

The criterion names a full `claude plugin install` followed by a full `claude plugin uninstall`.
There is no way to observe what that cycle does to a hook registration without running it.

The project owner ruled, during V2-016, again for V2-022 and again for V2-023, that no live
install/uninstall cycle may be run. The measured reason is `plugin_schema_spike.md` Item 4:
install writes `enabledPlugins` and `extraKnownMarketplaces` into a settings scope and
**uninstall never removes those keys, it only empties them**, and it leaves an orphaned cache
directory that `claude plugin prune` does not reclaim. At user scope that mutates the owner's live
configuration. At local scope it mutates `.claude/settings.local.json`, which is git-tracked in
this repository.

Two things were deliberately **not** done in place of the measurement:

- The cycle was not approximated by hand-editing a settings file. That measures whether the
  engineer can leave a key alone, which is a different question, and reporting it as the FR-8
  result would be a fake green.
- The test was not written to pass in the absence of the measurement. It skips, the skip message
  names the ruling and the criterion, and a rehearsal test drives the identical body against
  synthetic snapshots so the blocked test is known to reach both verdicts.

**FR-8 is therefore BLOCKED, and the cause is an owner decision.**

## 2. What V2-027 already proved, and why it is not this (explanation)

V2-027 removed the `PreToolUse`, `PostToolUse` and `UserPromptSubmit` registrations from the live
user-scope settings file and proved that `Stop` and `Notification` came through unchanged, by
comparing canonical-JSON digests of the retained entries rather than checking that their names
were still present. Those digests, re-measured against the live file on 2026-08-04 and unchanged
since:

| Hook | Canonical digest of the entry value |
|---|---|
| `Stop` | `910f4153dbba5f6afa4087ac24cd357e1756b59e73085c2d35f1631306d78d87` |
| `Notification` | `431869a74e0eae33a29780ee11510dac31f7b15b8f7d017e7d052eab8b720084` |

**That is evidence about a hook-deletion operation, not about an install/uninstall cycle.** They
are different operations against the same two keys, and a result for one is not a result for the
other. What carries over is the instrument, not the verdict:
`tests/test_hook_retention_across_install.py` imports `RETAINED_HOOKS` and `digest_of` from
`scripts/remove_hook_registrations.py` rather than respelling either, so both results are computed
by one canonicaliser and stay comparable.

## 3. What "byte-identical" is being asserted at, and what it is not (explanation)

Byte-identity is not one claim. It means four different things at four granularities, and the
criterion does not say which. The test measures all four and asserts two of them.

| Rung | Granularity | What it digests | Status |
|---|---|---|---|
| G1 | whole file | the settings file's own bytes | **REPORTED.** Guaranteed to differ across any install, because install writes the two bookkeeping keys. It says nothing about hooks. |
| G2 | hooks block | canonical JSON of `settings["hooks"]` | **REPORTED** for events other than the two retained ones; V2-023's install test owns that assertion for the install half. |
| G3 | entry value | canonical JSON of one hook event's value | **ASSERTED, unconditionally.** This is what V2-027 proved and what the criterion most plausibly means. |
| G0 | entry source bytes | the raw text span that spells the entry | **ASSERTED, conditionally** -- only while the document's own serialisation style is unchanged across the cycle. |

Three consequences, stated here rather than discovered during a run:

1. **G1 will differ. That is not a finding.** Recording "the file changed" as an FR-8 failure would
   be recording measured host behaviour as a defect in this plugin.
2. **G3 and G0 are genuinely different claims, and not only because of re-indentation.** A rewrite
   that re-orders the keys inside the `Stop` entry passes G3 and fails G0 at unchanged formatting.
   `tests/test_hook_retention_across_install.py::TestTheFourGranularitiesAreGenuinelyDifferent`
   measures exactly that case so the distinction is proved rather than argued.
3. **G0 is conditional, and the condition is the same one V2-016 was forced into.** A host that
   re-serialises the settings file changes the bytes of every entry in it without changing any
   entry's meaning. Asserting byte-identity across such a rewrite would be asserting something
   about the host's formatter. When the formatting fingerprint moves, the test records the byte
   claim as NOT CLAIMED, by name, in its `unproved` list, and the operator records that in the
   result. **A claim that was not made must not be recorded as a claim that passed.**

**The honest reading: the criterion as written is only literally checkable at G1, and at G1 it is
unachievable for reasons that have nothing to do with hooks. The strongest hook-level claim
available is G3 unconditionally plus G0 conditionally, and that is what is asserted.** Whoever owns
FR-8 should consider amending its wording to say so; this document does not amend it.

## 4. Procedure

Budget: zero additional minutes when run with `docs/guides/nfr11-lifecycle-verification.md`. It
consumes that procedure's snapshots and adds no step to the cycle.

### 4.0 Preconditions

- Run `docs/guides/nfr11-lifecycle-verification.md` steps 4.0 through 4.6. Record the CLI version
  it asks for; this result expires with the host version just as that one does.
- Two of the snapshots that procedure produces are this one's inputs:

| This procedure needs | NFR-11 step | NFR-11 file |
|---|---|---|
| the PRE-INSTALL state | 4.1 | `<SNAP>/install-before.json` |
| the POST-UNINSTALL state | 4.6 | `<SNAP>/after.json` |

**Do not substitute `<SNAP>/before.json`.** That file is taken after install and after
`register-mcp`, which is a strictly narrower window than this criterion's. Using it here would
measure the register/unregister window and report it as the install/uninstall cycle.

### 4.1 Record the fingerprint of the pre-install state

Run this against `<SNAP>/install-before.json` and again against `<SNAP>/after.json`, and keep both
outputs with the result. The test computes the verdict; this is what lets a later reader see the
inputs the verdict was computed from.

```
python -c "
import hashlib, json, re, sys
raw = open(sys.argv[1], encoding='utf-8').read()
hooks = json.loads(raw).get('hooks') or {}
quote = chr(34)
decoder = json.JSONDecoder()
def canon(value):
    text = json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
    return hashlib.sha256(text.encode('utf-8')).hexdigest()
def source(name):
    hits = []
    for match in re.finditer(re.escape(quote + name + quote) + r'\s*:\s*', raw):
        try:
            decoded, end = decoder.raw_decode(raw, match.end())
        except ValueError:
            continue
        if decoded == hooks[name]:
            hits.append((match.end(), end))
    if len(hits) != 1:
        return None
    return hashlib.sha256(raw[hits[0][0]:hits[0][1]].encode('utf-8')).hexdigest()
names = [name for name in ('Stop', 'Notification') if name in hooks]
print(json.dumps({'file': hashlib.sha256(raw.encode('utf-8')).hexdigest(), 'hooks_block': canon(hooks), 'entries': {name: canon(hooks[name]) for name in names}, 'entry_bytes': {name: source(name) for name in names}}, indent=2, sort_keys=True))
" <SNAPSHOT>
```

If `entries` is empty for `<SNAP>/install-before.json`, neither retained hook was registered before
the cycle and **there is nothing to measure**. Do not record a verdict; this machine is not a valid
subject for the criterion.

If `entry_bytes` reports `null` for a hook, the entry's source span could not be located
unambiguously and the byte-level claim cannot be made for it. Report that; do not treat it as a
pass.

### 4.2 Run the test

```
CWE_ALLOW_LIVE_PLUGIN_INSTALL=1 \
CWE_HOOK_SNAPSHOT_BEFORE=<SNAP>/install-before.json \
CWE_HOOK_SNAPSHOT_AFTER=<SNAP>/after.json \
python -m pytest tests/test_hook_retention_across_install.py -p no:randomly \
  -k test_live_cycle_leaves_the_retained_hooks_intact -v
```

The test asserts on two lists and reports the rest:

- **problems** -- a retained entry that was altered, lost, or created by the cycle. This is FR-8
  failing at G3.
- **byte_problems** -- a retained entry whose source bytes moved while the document's formatting
  did not, or whose span could not be located. This is FR-8 failing at G0.
- **unproved** -- claims that were NOT made, by name: a re-serialised document suppresses the G0
  claim, and a hook that did not exist before the cycle is not claimed about at all.
- **siblings** and **whole_file** -- reported, never asserted.

| Test outcome | Verdict |
|---|---|
| PASSED, `unproved` empty | FR-8 is **MET** at G3 and G0 for this CLI version. Record it per section 5. |
| PASSED, `unproved` naming a re-serialisation | FR-8 is **MET at G3 only**. Record it as the conditional it is; do not record it as byte-identical. |
| FAILED on `problems` | FR-8 is **NOT MET**. The cycle disturbed a user hook. Report it against ADR-010 as well; the plugin ships zero hooks and must have no route to a user's hook block. |
| FAILED on `byte_problems` | FR-8 is **NOT MET at G0** while holding at G3. Record both rungs separately; the distinction is the whole point of section 3. |
| SKIPPED | The environment variables did not take effect. The measurement did not run. Do not record a verdict. |

**A skip is not a pass.** If the run reports `1 skipped`, one of the three variables is unset or
names a file that does not exist. Fix it and repeat.

### 4.3 The control that stops a false PASS

Use `docs/guides/nfr11-lifecycle-verification.md` step 4.7 unchanged. Both verdicts are two-point
comparisons across a window in which other writers exist, and if anything else wrote the settings
file during the cycle then a PASS here is a coincidence rather than a measurement.

One additional check specific to this criterion: confirm that nothing on the machine rewrote the
hook block for an unrelated reason during the window. The `Stop` hook is under active review
(`docs/REVIEW-INDEX.md` item 40) and must not be edited while a cycle is being measured.

### 4.4 Restore

If the run touched a live scope, follow `docs/guides/uninstall-residue.md` Procedure B. Nothing in
this procedure writes anything.

---

## 5. Recording the result

Record six facts, not one: the G3 verdict, the G0 verdict, the contents of `unproved`, the date,
the CLI version, and the settings path used. A verdict without the CLI version cannot be compared
against a later run; a verdict without the settings path cannot be reproduced; a verdict without
`unproved` cannot be distinguished from a stronger one.

Amend this document's status line in place, and amend the FR-8 row wherever the issue tracker
records acceptance.

## 6. How the four procedures differ

They share one cycle and one set of snapshots. They do not share a question.

- **`adr-020-path-c-verification.md`** asks whether a `register-mcp`-written `mcpServers` entry
  **survives** uninstall. Its PASS is the entry still present.
- **`fr31-uninstall-residue-verification.md`** asks whether that tool **stops being callable**. Its
  PASS is the entry absent, on the unnarrowed reading of FR-31.
- **`nfr11-lifecycle-verification.md`** asks what **install** wrote, and asks the uninstall question
  on the narrowed reading the owner ruled for.
- **This document** asks about neither `mcpServers` nor residue. It asks whether the user's own two
  hook registrations came through the **whole** cycle untouched. Its window is the widest of the
  four: it opens before install and closes after uninstall, where the other three open after
  install.

## 7. What this procedure does not establish

Stated so a result is not read as broader than it is.

- It measures **one** cycle of **one** plugin from **one** marketplace against **one** CLI version.
  Install and uninstall behaviour are properties of the host and a result expires without notice
  when the host changes.
- It says nothing about whether the retained hooks WORK. It is a preservation check on their
  registration, not an invocation check. `Stop` in particular is a hook whose behaviour is under
  active review at `docs/REVIEW-INDEX.md` item 40, and a byte-identical `Stop` entry is a hook
  preserved exactly as it is, defects included.
- **It does not cover a hook registered at project, local or managed scope, and that is a gap in
  the criterion rather than in this procedure.** Hook contributions merge across the four settings
  scopes into one flat unlabelled list per event. An install that registered a `Stop` handler at
  project scope would leave the user-scope `Stop` entry byte-identical -- satisfying FR-8 to the
  letter -- while changing what actually runs when the session stops. Nothing measurable from a
  single user-scope snapshot can see that. For this plugin the gap is closed by a different and
  already-executed control: FF-2 in `scripts/verify_plugin_conformance.py` asserts the plugin ships
  no hooks artefact at all, by both the filesystem route and the manifest path-override route.
  **FR-8's own wording does not close it, and a future plugin that did ship a hook would pass FR-8
  while changing the user's Stop pipeline.**
- It does not cover a partly-failed install or a partly-failed uninstall.
- It does not establish anything about the orphaned plugin cache directory or the emptied
  bookkeeping keys. Those are accepted Claude-Code-level limitations documented at
  `docs/guides/uninstall-residue.md` section 6, and no step here asserts they are absent.
- A tab-indented settings file reports an indent width of 0 in the formatting fingerprint, which is
  the same value an unindented file reports. Both still compare equal to themselves, so the G0
  conditional holds; the fingerprint is not a general formatter classifier and is not used as one.

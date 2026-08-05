# ADR-020 Path C verification procedure

**Status: NOT PERFORMED. Blocked by an explicit owner ruling, not by a technical limitation.**

This document is the executable procedure for the verification task ADR-020 attaches to
whoever implements `register-mcp` (`docs/phase-2-validation/hld_v2.md`, ADR-020, the
VERIFICATION TASK paragraph). It exists because that verification could not be performed
during V2-016.

---

## 1. Why this is a document rather than a result

ADR-020 Path C asks a single question: **does an `mcpServers` entry written by
`register-mcp` survive `/plugin uninstall` of the plugin that provided the command?**

Answering it requires a real `claude plugin install` followed by a real `/plugin uninstall`.
The project owner ruled, during V2-016 and after being shown the trade-off, that no live
install/uninstall cycle may be run. The measured reason (spike item 4) is that install writes
`enabledPlugins` and `extraKnownMarketplaces` into a settings scope and **never removes those
keys on uninstall -- it only empties them** -- plus it leaves an orphaned cache directory that
`claude plugin prune` does not clean. At user scope that mutates the owner's live
configuration; at local scope it mutates a git-tracked file in this repository.

Two things were deliberately **not** done in place of the real measurement:

- The cycle was not approximated by hand-editing a settings file. That measures whether the
  engineer can delete a key, which is a different question, and reporting it as the Path C
  result would be a fake green.
- The result was not inferred from the design and reported as measured. ADR-020 already
  records the inference; repeating it adds nothing and would blur the line the ADR drew.

**Path C therefore remains INFERRED safe, not measured safe, and V2-016's AC 4 is NOT MET.**

## 2. Why the window is still open, and how long it stays open

ADR-020 describes this as performable "at the only moment it can be performed" -- when
`register-mcp` exists -- and `sequencing_risks.md` R-10 marks it time-boxed. Both are slightly
too strong, and the correction matters for scheduling.

The window opened when `register-mcp` landed (V2-016) and it does **not** close on a date. It
closes when someone deletes `PreToolUse` (PRD FR-4 / V2-027) without having measured this,
because from that point a wrong inference has already cost the local push gate rather than
merely risking it. So the true deadline is **before V2-027 merges**, and the procedure below
should be run in batch F or G, not "as soon as possible".

## 3. What a failure would cost

Path C is the one path in ADR-020's table with **no available control** if the inference is
wrong. Prevention is impossible: `/plugin uninstall` is Claude Code's own command and the
plugin ships no hooks (ADR-010), so there is no interception point. Detection is impossible
too: after uninstall the plugin is gone, so neither a `doctor` command nor a per-command
precondition check can run. Every other path in the table degrades to a weaker control; Path C
degrades to none.

**Named fallback, stated in advance so the decision is not taken under pressure:** if this
procedure returns FAIL, **ADV-012's git `pre-push` hook moves from `NAMED, NOT ADOPTED` to
REQUIRED.** It is the only surviving mechanism, because it lives in git configuration
independently of the plugin and therefore outlives the plugin's own removal. ADV-012 is a git
hook, not a Claude Code hook, so ADR-010 does not govern it, and it spawns a process only on an
explicit `git push`, so NFR-1 is unaffected. The change is a promotion of an item that already
exists in `docs/phase-2-validation/advisory_items.json`; it is not new design work.

---

## 4. Procedure

Budget: about 10 minutes. Requires authorisation to install and uninstall a plugin against a
real settings scope.

### 4.0 Preconditions

- A settings scope you are authorised to mutate. Prefer a throwaway `CLAUDE_CONFIG_DIR` over
  your live `~/.claude` if the harness under test honours one; if it does not, this procedure
  necessarily runs against the real scope, which is the whole reason for the owner ruling.
- The `mcp-*` server checkouts available, and their parent directory noted as `<SERVER_ROOT>`.
- Nothing else writing the settings file for the duration. This matters: see step 4.6.

### 4.0.1 Resolve `<SETTINGS>`, `<LEDGER>` and the plugin root -- do not assume them

Every later step is invalid if `<SETTINGS>` is not the file `register-mcp` actually writes.
Do not infer it. After step 4.2 has installed the plugin, ask the command itself:

```
python "${CLAUDE_PLUGIN_ROOT}/scripts/mcp_registration.py" status --json
```

The `settings` and `ledger` fields of that output **are** `<SETTINGS>` and `<LEDGER>`. Use
those values verbatim for the rest of the procedure. `settings_sha256` in the same output is a
free cross-check against the baseline hash from 4.1.

Two resolution notes that will otherwise cost a run:

- `CLAUDE_PLUGIN_ROOT` is populated by Claude Code for processes it spawns. In a bare terminal
  it is usually unset and the command above expands to a broken path. Either run the steps
  through the `/register-mcp` command inside a Claude Code session, or set `CLAUDE_PLUGIN_ROOT`
  by hand to the installed plugin directory (the one containing `.claude-plugin/plugin.json`)
  and export it before running anything.
- `register-mcp` targets `CLAUDE_SETTINGS_FILE` when that variable is set, and
  `~/.claude/settings.json` otherwise. If you set `CLAUDE_SETTINGS_FILE` to redirect the run
  away from a live scope, confirm via `status --json` that the redirect took effect **before**
  installing, because a redirect that silently did not apply is the failure mode that ends with
  a live configuration mutated.

Record the Claude Code CLI version now, not at the end:

```
claude --version
```

This is a measurement of host behaviour, and host behaviour is a property of a version. A
result recorded without one cannot be compared against a later run.

### 4.1 Capture the baseline

```
python -c "import hashlib,json,pathlib,sys; p=pathlib.Path(sys.argv[1]); b=p.read_bytes(); d=json.loads(b); print(json.dumps({'sha256':hashlib.sha256(b).hexdigest(),'size':len(b),'mcpServers':sorted(d.get('mcpServers',{})),'topLevelKeys':sorted(d)},indent=2))" <SETTINGS> > baseline.json
```

Also copy the whole file, because a hash tells you *that* it changed and not *what* changed:

```
cp <SETTINGS> baseline-settings.json
```

Record the value of `<SETTINGS>` used. Every later step must use the same path.

Ordering note: 4.0.1 resolves `<SETTINGS>` by asking the installed plugin, which means it can
only run after 4.2. Take this baseline against the path you *intend* to use, then re-confirm in
4.0.1 that the command agrees. If it does not, discard the baseline, take a fresh one against
the path the command reported, and start again from 4.1 -- a baseline of the wrong file makes
every downstream comparison meaningless.

### 4.2 Install the plugin

```
claude plugin marketplace add techdeveloper-org/claude-workflow-engine
claude plugin install claude-workflow-engine@techdeveloper-org
```

Snapshot again into `after-install.json` and `after-install-settings.json` using the same two
commands as 4.1. This snapshot is what separates "uninstall removed our entry" from "install
never wrote it".

### 4.3 Register

```
python "${CLAUDE_PLUGIN_ROOT}/scripts/mcp_registration.py" register --server-root <SERVER_ROOT>
```

Confirm the command reported `ADDED post-tool-tracker`. If it reported `SKIP`, the entry point
was not found and **there is nothing to measure** -- fix `<SERVER_ROOT>` and repeat, because a
run with no entry written reproduces exactly the gap that made Path C unmeasurable in the
first place.

Snapshot into `after-register.json` and `after-register-settings.json`.

Record two further facts, because they are the actual subject of the test:

- the resolved plugin root, `echo "${CLAUDE_PLUGIN_ROOT}"`;
- the ledger path printed by
  `python "${CLAUDE_PLUGIN_ROOT}/scripts/mcp_registration.py" status`.

### 4.4 Uninstall

```
claude plugin uninstall claude-workflow-engine@techdeveloper-org
```

Snapshot into `after-uninstall.json` and `after-uninstall-settings.json`.

### 4.5 The decision rule

```
python -c "import json,sys; a=json.load(open(sys.argv[1])); b=json.load(open(sys.argv[2])); print('post-tool-tracker in after-register:', 'post-tool-tracker' in a['mcpServers']); print('post-tool-tracker in after-uninstall:', 'post-tool-tracker' in b['mcpServers'])" after-register.json after-uninstall.json
```

| after-register | after-uninstall | Verdict |
|---|---|---|
| True | True | **PASS.** Path C is measured safe. ADR-020 needs a status update only, and ADV-012 stays `NAMED, NOT ADOPTED`. |
| True | False | **FAIL.** Uninstall removed an entry `register-mcp` wrote. Promote ADV-012 to REQUIRED (section 3) and raise an issue against ADR-020 to replace the inference with the measurement. |
| False | anything | **INVALID RUN.** Step 4.3 did not write the entry. Do not record a verdict; fix and repeat. |

`PASS` is only valid if step 4.6 also passes.

### 4.6 The control that stops a false PASS and a false FAIL

The verdict above is a two-point comparison across a window in which other writers exist. Do
not skip this.

```
python -c "import json,sys; a=json.load(open('after-register-settings.json')); b=json.load(open('after-uninstall-settings.json')); ak=set(a)-{'mcpServers'}; bk=set(b)-{'mcpServers'}; print('non-mcpServers keys added:', sorted(bk-ak)); print('non-mcpServers keys removed:', sorted(ak-bk)); print('other mcpServers entries lost:', sorted(set(a.get('mcpServers',{}))-set(b.get('mcpServers',{}))-{'post-tool-tracker'}))"
```

- **`other mcpServers entries lost` must be empty.** If unrelated entries also vanished, the
  cause is a whole-file clobber by some writer, not Path C, and a `FAIL` verdict would be
  attributed to the wrong mechanism. Re-run with nothing else touching the file.
- `non-mcpServers keys added` is expected to contain `enabledPlugins` and
  `extraKnownMarketplaces` if they were not already present. That is measured host behaviour
  (they are emptied, never removed) and is not a finding.
- Anything else in `non-mcpServers keys removed` **is** a finding and should be reported
  regardless of the Path C verdict.

### 4.7 Second measurement, free at this point

The provenance ledger `register-mcp` writes lives beside the settings file, not inside the
plugin, specifically so that an uninstalled plugin still leaves the user able to identify and
remove what it registered. Confirm it:

```
python -c "import json,pathlib,sys; p=pathlib.Path(sys.argv[1]); print('ledger present after uninstall:', p.is_file()); print(p.read_text(encoding='utf-8') if p.is_file() else '')" <LEDGER>
```

If the ledger is gone, the design intent failed and a user whose plugin is uninstalled has no
supported way to reverse the registration. Report it; it does not change the Path C verdict.

### 4.8 Restore

If the run touched a live scope, restore it:

```
cp baseline-settings.json <SETTINGS>
```

Then re-diff against `baseline.json` and confirm the hash matches. Note that a matching hash
here is only meaningful if nothing else wrote the file meanwhile.

---

## 5. Recording the result

Amend ADR-020 in `docs/phase-2-validation/hld_v2.md` in place, replacing the VERIFICATION TASK
paragraph's "Not measured; verification task attached" with the verdict, the date, the Claude
Code CLI version captured in 4.0.1, and the settings path used. On `FAIL`, also amend
ADV-012's `disposition` in `docs/phase-2-validation/advisory_items.json` and raise the
promotion as scope against whoever owns FR-23.

Record all four. A verdict without the CLI version cannot be compared against a later run; a
verdict without the settings path cannot be reproduced.

## 6. What this procedure does not establish

Stated so the result is not read as broader than it is.

- It measures **one** entry, `post-tool-tracker`, written by **one** command version, against
  **one** CLI version. A `PASS` is evidence that uninstall does not remove that entry, not a
  guarantee about all future CLI versions. ADR-020's inference rests on uninstall keeping
  plugin-scoped registrations in a different store from top-level `mcpServers`; if a later CLI
  changes that, this result expires without notice.
- It does not test the `--force` path, where `register-mcp` displaced an entry the user already
  had. If uninstall were to remove such an entry, the loss would be the user's original
  configuration rather than ours. That case is worth adding to the run if a forced registration
  is realistic for the deployment, and is a strictly larger blast radius than the plain case.
- A `PASS` says nothing about Path A or Path B. Those have their own controls in ADR-020 and
  are unaffected by this measurement either way.

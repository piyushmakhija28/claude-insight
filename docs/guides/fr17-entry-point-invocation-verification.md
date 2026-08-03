# SRS FR-17 entry-point invocation verification procedure

**Status: NOT PERFORMED. Blocked by an explicit owner ruling, not by a technical limitation.**

This document is the executable procedure for the half of SRS FR-17 acceptance criterion 1
that a unit suite cannot reach: whether Claude Code actually discovers the six entry points
by name from an installed plugin.

It follows the shape `docs/guides/adr-020-path-c-verification.md` established, and its
companion test is
`tests/test_pipeline_entry_points.py::TestLiveInvocationByName::test_every_entry_point_is_discovered_by_name_in_an_installed_plugin`.

---

## 1. What is and is not already measured

AC 1 has two halves. Only one of them is blocked.

| Half | Status | Where |
|---|---|---|
| Each entry point reaches its pipeline steps | **MEASURED** | `tests/test_pipeline_entry_points.py`, plan and graph layers |
| Each entry point is invocable **by name** | **BLOCKED** | this document |

What is already measured, so it is not re-measured here:

- Each of the six names has a command file at `plugin/commands/<name>.md`, and no seventh
  pipeline command file exists without a plan.
- The command each file ships resolves and reports its own steps when executed from its
  **stored** form, with `${CLAUDE_PLUGIN_ROOT}` expanded the way Claude Code expands it.
- The capability directory sits at the plugin **root**, which is what discovery scans.
  `scripts/verify_plugin_conformance.py` FF-4 fails the build otherwise, and its
  `--json` discovery trace reports `commands/` as FOUND.
- The full-pipeline command's declared plan equals the step set measured from the real
  `create_flow_graph(hook_mode=False)` graph, and those steps are reachable in ascending
  order.

What remains unmeasured is the single step none of the above can substitute for: that a
live Claude Code session, with the plugin installed, offers `/plan`, `/implement`,
`/review`, `/document`, `/release` and `/run-pipeline` and routes each to its own file.

## 2. Why this is a document rather than a result

Answering it requires a real `claude plugin install`. The project owner ruled, during
V2-016 and after being shown the trade-off, that no live install/uninstall cycle may be
run. The measured reason (FR-14a spike item 3) is that install writes `enabledPlugins` and
`extraKnownMarketplaces` into a settings scope and **never removes those keys on uninstall
-- it only empties them** -- plus it leaves an orphaned cache directory that
`claude plugin prune` does not clean. At user scope that mutates the owner's live
configuration; at local scope it mutates a git-tracked file in this repository.

Two things were deliberately **not** done in place of the real measurement:

- The discovery was not approximated by asserting the files exist. That measures whether
  an engineer can create a file, which is a different question, and reporting it as the
  discovery result would be a fake green.
- The result was not inferred from the conformance gate and reported as measured. FF-4
  proves the layout is discoverable; it does not prove the host discovered it.

**AC 1's invocation half therefore remains INFERRED, not measured.**

## 3. What a failure would cost

Every other v2.0.0 deliverable assumes these six commands are the pipeline's only reachable
entry point once PRD FR-4 and FR-5 delete the hooks. If discovery silently finds nothing --
the failure mode the packaging skill names as the most expensive available, because the
plugin installs cleanly and reports no error -- the engine becomes unreachable at exactly
the moment the old entry point is removed.

**Named fallback, stated in advance so the decision is not taken under pressure:** if this
procedure returns FAIL, V2-027 (PRD FR-4 / FR-5, hook deletion) must not merge. The
sequencing constraint already recorded in `sequencing_risks.md` R-5 becomes a hard block
rather than an ordering preference.

---

## 4. Procedure

Budget: about 10 minutes. Requires authorisation to install and uninstall a plugin against
a real settings scope.

### 4.0 Preconditions

- A settings scope you are authorised to mutate. Prefer a throwaway `CLAUDE_CONFIG_DIR`
  over your live Claude home if the harness under test honours one; if it does not, this
  procedure necessarily runs against the real scope, which is the whole reason for the
  owner ruling.
- Nothing else writing the settings file for the duration.

Record the Claude Code CLI version now, not at the end:

```
claude --version
```

This is a measurement of host behaviour, and host behaviour is a property of a version. A
result recorded without one cannot be compared against a later run.

### 4.1 Capture the baseline

Snapshot the settings file before anything is installed, exactly as
`docs/guides/adr-020-path-c-verification.md` section 4.1 does. Keep both the digest and a
full copy: a hash tells you *that* something changed and not *what*.

### 4.2 Install the plugin

```
claude plugin marketplace add techdeveloper-org/claude-workflow-engine
claude plugin install claude-workflow-engine@techdeveloper-org
```

Then, in the session:

```
/reload-plugins
```

Skipping `/reload-plugins` is the documented cause of "I installed it but it is not there".
A missing command after an install with no reload is not a FAIL; it is an invalid run.

### 4.3 Capture what was discovered

In the installed session, list the available slash commands and write the names this
plugin contributed into a JSON file:

```
{
  "cli_version": "<output of claude --version>",
  "commands": ["plan", "implement", "review", "document", "release", "run-pipeline"]
}
```

Record what you actually observed, not the list above. The list above is what a PASS looks
like, and writing it down without observing it is the fake green this whole procedure
exists to avoid.

Save it, and note its path as `<SNAPSHOT>`.

### 4.4 Judge it

```
CWE_ALLOW_LIVE_PLUGIN_INSTALL=1 CWE_FR17_DISCOVERED_COMMANDS=<SNAPSHOT> \
  python -m pytest tests/test_pipeline_entry_points.py::TestLiveInvocationByName -v
```

| Result | Verdict |
|---|---|
| The test passes | **PASS.** All six entry points are discovered by name. |
| The test fails naming missing entry points | **FAIL.** Section 3's fallback applies: V2-027 is blocked until it is fixed. |
| The test skips | **INVALID RUN.** The environment variables did not take effect, or `<SNAPSHOT>` does not exist. Fix and repeat; do not record a verdict. |
| The test fails with "measures nothing" | **INVALID RUN.** Step 4.3 captured an empty command list. |

### 4.5 The control that stops a false PASS

A discovered *name* is not a reached *command*. Invoke one command that changes nothing and
confirm it ran the right file:

```
/plan
```

It must ask for a task, print its coverage line beginning `plan: owns Step 0 ...`, and
either print the resolved dispatch or refuse with `REFUSED:` naming `CWE_ENGINE_ROOT`.
A refusal here is a **PASS** for this control: it proves the command file was found,
executed, and reached the plugin's own dispatcher. What would be a FAIL is silence,
"unknown command", or output belonging to a different entry point.

Do **not** run `/implement`, `/review`, `/document`, `/release` or `/run-pipeline` as part
of this procedure. Each of them dispatches the engine for real, and every one of them
reaches Step 8, which creates a GitHub issue, a branch, a pull request and a merge.

### 4.6 Uninstall and restore

```
claude plugin uninstall claude-workflow-engine@techdeveloper-org
```

Restore the settings file from the 4.1 copy if the run touched a live scope, then re-diff
against the baseline digest. Note that a matching hash is only meaningful if nothing else
wrote the file meanwhile, and that `enabledPlugins` and `extraKnownMarketplaces` are
expected to survive as emptied keys -- that is measured host behaviour recorded in
`docs/guides/uninstall-residue.md`, not a finding.

---

## 5. Recording the result

Amend this document's status line in place with the verdict, the date, the Claude Code CLI
version captured in section 4.0, and the settings path used. Record all four. A verdict
without the CLI version cannot be compared against a later run; a verdict without the
settings path cannot be reproduced.

## 6. What this procedure does not establish

Stated so the result is not read as broader than it is.

- It measures discovery and one command's routing against **one** CLI version. A PASS is
  evidence that this version discovers these six names, not a guarantee about later ones.
- It does not measure that any entry point other than `plan` reaches the engine, because
  every other one runs the pipeline for real. Their dispatch is measured in the unit suite
  against a scratch engine root instead, which is a strictly weaker claim and is labelled
  as one there.
- It says nothing about AC 2's execution half. That a full run performs Steps 0 through 8
  in order is asserted against the graph's structure, never against a run, and no procedure
  in this repository authorises the destructive alternative.

# Migration guide -- v1.21.5 to v2.0.0

**Scope: what a user running v1.21.5 must do to reach v2.0.0, in what order, and which orderings
are unsafe.**

This is the reader-facing form of `docs/phase-2-validation/hld_v2.md` section 10, "Migration Design
-- What a v1.21.4 User Must Do". Section 3 below reproduces that runbook's eight steps verbatim,
because the ordering constraints are carried in the step wording itself and paraphrase loses them.

**The HLD says "v1.21.4"; the released predecessor is v1.21.5.** The HLD was written before v1.21.5
shipped, and v1.21.5 changed only the layout of `docs/` and the standards loader that reads it.
Nothing in the runbook depends on the difference. This document is titled for the version a user is
actually upgrading from.

**Document mode.** Sections 3, 4 and 6 are the procedure and are written as a how-to guide: every
sentence in them directs an action or states a check. Sections 1, 2, 5, 7 and 8 are explanation and
are labelled as such, so a reader working the procedure can skip them and a reader trying to
understand the change can read only them. The split mirrors `docs/guides/uninstall-residue.md`.

**Line citations in this document are dated hints.** Citations in this project have been measured to
drift; resolve by heading text if a number lands somewhere unexpected.

---

## 1. What actually changes (explanation)

Three hook registrations are deleted from your user-scope settings file, and the pipeline stops
running unless you ask it to by name.

| Before (v1.21.5) | After (v2.0.0) |
|---|---|
| `UserPromptSubmit` ran `scripts/3-level-flow.py` on every prompt | Nothing runs on a prompt |
| `PreToolUse` validated every tool call, and held the version-push gate | The push gate answers as an MCP tool; nothing validates tool calls locally |
| `PostToolUse` wrote progress after every tool call | No per-tool-call progress writing |
| `Stop` and `Notification` registered | `Stop` and `Notification` registered, unchanged |
| Enforcement was automatic and unconditional | Enforcement happens only inside an invoked command |

**MEASURED at v2.0.0**, by reading the live `~/.claude/settings.json` read-only: the `hooks` object
holds exactly `Stop` and `Notification`. The other three keys are absent.

The last row is the whole trade-off. Under ADR-006 a session in which you invoke no command runs no
engine code, and therefore enforces nothing. That is the intended design, not a regression, and it
is the change you will notice first.

---

## 2. Pre-migration checklist (explanation, then four checks)

A migration guide's pre-migration checklist is heavier than a runbook's preconditions because the
transition happens once. Four things must be true before you start. Each is a check you run, not a
claim you accept.

| # | Check | How you know it passed |
|---|---|---|
| P1 | You have a backup of `~/.claude/settings.json`, stored **outside any repository** | The backup file exists at the path you chose, and `python -c "import json,pathlib;json.loads(pathlib.Path(r'<backup>').read_text(encoding='utf-8'))"` exits 0 |
| P2 | You know which MCP servers are currently registered | `mcpServers` key count, recorded before you begin. At the release cut this was 25, and became 26 after step 2 |
| P3 | You accept that enforcement becomes opt-in | You have read section 1's last row |
| P4 | You are not mid-task | No branch is waiting on a pipeline run to finish |

P1 is the one that matters. The migration edits a live settings file by hand, and no step in this
guide can reconstruct a file you did not copy first.

**Backup verification is a check, not a step.** Copying the file proves nothing; parsing the copy
proves it is a settings file and not a truncated write. That is why P1's evidence column names a
parse, not an `ls`.

---

## 3. The eight migration steps

Reproduced from `docs/phase-2-validation/hld_v2.md` section 10 (table at lines 1346-1355 as of
2026-08-04). Step wording is verbatim; the annotations below each step are this document's.

### Step 1 -- Install the plugin first, while hooks still run

> `/plugin marketplace add techdeveloper-org/<repo>` then
> `/plugin install claude-workflow-engine@techdeveloper-org`. Installs commands, agents and skills
> only -- **no MCP servers** (ADR-019)

**Reversible?** Yes -- `/plugin uninstall`, with residue; see section 6.
**Idempotent?** Yes. Re-running an install that already succeeded changes nothing.
**Precondition:** the v1.21.5 hooks are still registered and running.
**Postcondition (verify this):** the plugin's commands appear in the slash-command list, and
`~/.claude/settings.json` has gained `extraKnownMarketplaces` and `enabledPlugins` keys.

### Step 2 -- Register the MCP servers

> `/{plugin-name}:register-mcp`. **Opt-in by design (ADR-019)** -- the plugin ships no `.mcp.json`,
> so no MCP-backed capability exists until this runs. Writes user-scope registrations via
> merge-against-fresh-read (SS 8.4). **Required before steps 3 and 5**

The plugin name is `claude-workflow-engine`, so the command is
`/claude-workflow-engine:register-mcp`.

**Reversible?** Yes -- `/claude-workflow-engine:unregister-mcp`.
**Idempotent?** Yes. The write is a merge against a fresh read, so a second run re-registers the
same entries rather than duplicating them.
**Precondition:** the postcondition of step 1 -- the plugin's commands appear in the
slash-command list.
**Postcondition (verify this):** `mcpServers` holds one entry more than the count you recorded at
P2, and the new entry is the push gate.

**The bolded clause is the ordering constraint this whole runbook exists to carry.** Step 2 is
optional for the migration as a whole and mandatory for step 5. That conditional is the reason
step 2 is a numbered step rather than a sentence of prose.

### Step 3 -- Verify the FR-23 replacement is reachable

> The version-push gate answers as an MCP tool. **Cannot pass before step 2** -- if it fails, the
> cause is almost always an unrun step 2, not a broken migration. **This must pass before step 5**

**Reversible?** n/a -- this step reads, it does not write.
**Idempotent?** Yes. A check has no effect to repeat.
**Precondition:** the postcondition of step 2 -- `mcpServers` holds one entry more than P2's count,
and the new entry is the push gate.
**Postcondition (verify this):** a real `tools/call` against the push gate completes and returns a
determination. Not a settings entry, not a `tools/list`: a completed call.

**A settings entry is not evidence.** The release itself proved reachability by spawning the process
the settings entry names, reading argv verbatim from `mcpServers` rather than substituting anything
from a catalogue, and completing `initialize`, `tools/list` and a `tools/call` that returned
`ALLOWED`. Anything weaker checks that a line of JSON exists, which is the thing that was already
true when the gate was unreachable.

### Step 4 -- Learn the explicit entry points (FR-7)

> Slash commands for plan/decompose, implement, review, document, release, plus one command that
> runs Steps 0-8 for the old end-to-end behaviour

As shipped, the six names are `plan`, `implement`, `review`, `document`, `release` and
`run-pipeline`. **MEASURED** against `scripts/pipeline_invocation.py`, constant `FR17_COMMANDS`.

**Reversible?** n/a.
**Idempotent?** Yes.
**Precondition:** the postcondition of step 3 -- a real `tools/call` against the push gate completes
and returns a determination.
**Postcondition (verify this):** running `scripts/3-level-flow.py` with no `--invoked-by=` argument
prints a refusal naming all six commands and exits 0; running it with `--invoked-by=nonsense` exits
2. Two different exits, on purpose: an absent declaration means nobody asked for a run, while a
misspelled one means a caller tried and would otherwise silently lose a whole run.

### Step 5 -- Remove `PreToolUse` and `PostToolUse` from `~/.claude/settings.json`

> Hand-edited by the user. The plugin cannot do this and must not try (ADR-010).
> **Do not perform this step if step 3 did not pass** -- see the safety note below.
> Removing `PostToolUse` also ends per-tool-call progress writing; crash recovery is unaffected
> (`CheckpointManager` is in-process, ADR-011), but the progress *query surface* is MCP-backed and
> therefore also depends on step 2

**Reversible?** Yes -- restore the two entries.
**Idempotent?** Yes. Deleting an absent key is a no-op.
**Precondition:** the postcondition of step 3 -- a real `tools/call` against the push gate completes
and returns a determination. This is the same assertion, in the same words, that step 3 leaves true.
That is what makes the chain hold; if the two were merely similar, this step's safety would be
unproven.
**Postcondition (verify this):** the `hooks` object no longer holds `PreToolUse` or `PostToolUse`,
and the `Stop` and `Notification` entries are byte-identical to your P1 backup.

**Compare the entries, do not just count them.** The release proved `Stop` and `Notification`
survived by comparing canonical-JSON digests of the entries, not their presence. Presence is
satisfied by an entry that has been silently rewritten.

**Two corrections to this step, both MEASURED.** See section 5.

### Step 6 -- Take `UserPromptSubmit` off the hot path

> `scripts/3-level-flow.py` stops being the every-prompt entry point

**Reversible?** Yes.
**Idempotent?** Yes.
**Precondition:** the postcondition of step 5 -- `hooks` no longer holds `PreToolUse` or
`PostToolUse`, and `Stop` and `Notification` are byte-identical to the P1 backup.
**Postcondition (verify this):** the `hooks` object no longer holds `UserPromptSubmit`, so `hooks`
holds exactly `Stop` and `Notification`.

### Step 7 -- Leave `Stop` and `Notification` alone

> The plugin never owned them. FR-8a/FR-21 repair happens in place, separately from packaging

**Reversible?** n/a -- this step is an instruction not to act.
**Idempotent?** Yes, trivially.
**Precondition:** the postcondition of step 6 -- `hooks` holds exactly `Stop` and `Notification`.
**Postcondition (verify this):** unchanged from the precondition.

**Do not edit anything under `hooks/stop_notifier/` while migrating**, and in particular do not
change any `sys.path` line there. See section 5 for why.

### Step 8 -- Expect enforcement to stop being automatic

> **This is the behaviour change.** Nothing is enforced on a session where no command is invoked
> (ADR-006)

**Reversible?** By reverting step 5.
**Idempotent?** n/a -- this step is an expectation, not an action.
**Precondition:** the postcondition of step 7 -- `hooks` holds exactly `Stop` and `Notification`.
**Postcondition:** none to check on the day. This step's postcondition is what section 4's bake
window measures.

---

## 4. Post-migration verification, including the bake window

Two checks on the day, then a window.

**On the day.** Both are `hooks`-object assertions and both must hold:

1. `hooks` holds exactly `Stop` and `Notification`.
2. A `tools/call` against the push gate still completes and returns a determination.

**Then a bake window of ten working sessions.** A single point-in-time check is the wrong instrument
here, and not as a matter of taste. The defect class this migration introduces is *a thing that used
to happen automatically and now silently does not*, and its defining property is that it surfaces
only when you happen to do the work that would have triggered it. If any one session has roughly a
1-in-10 chance of exercising a given lost automatic behaviour, a single post-migration check catches
it about 10% of the time, while ten sessions catch it about 65% of the time -- the same monitoring,
six times the confidence, purely from letting it run longer.

**What to watch during the window**, in descending order of how quietly it fails:

| Watch for | Was provided by | Now requires |
|---|---|---|
| A push landing on a branch that bumped no `VERSION` | `PreToolUse` push gate | The MCP push gate, reachable only if step 2 ran |
| Progress queries returning nothing | `PostToolUse` | An MCP-backed query surface, step 2 again |
| A task you expected to be planned running unplanned | `UserPromptSubmit` | You invoking `plan` by name |

**Ten sessions is a floor, not a target.** If you have not exercised a push during the window, the
window has not tested the row that matters most, and it should continue until you have.

---

## 5. What this runbook does not say, and should (explanation)

Five findings. Each is MEASURED at v2.0.0, and none of them is fixed by this document -- naming them
is what this section is for.

**5.1 -- `scripts/settings-config.json` still registers all three deleted hooks.** Recorded as
REVIEW-INDEX 46 and re-verified for this release by parsing the file: its `hooks` object holds
`PreToolUse`, `PostToolUse`, `UserPromptSubmit` and `Stop`. It is the template a machine's
`~/.claude/settings.json` is bootstrapped from, and nothing in the migration touches it. **Setting up
a second machine from that template re-creates exactly what step 5 and step 6 remove**, and no gate
catches it. If you bootstrap another machine, either edit that template first or repeat steps 5 and
6 there. A migration guide that omitted this would be describing a deletion that does not stay
deleted.

**5.2 -- Step 5 understates what you must remove.** Its title names `PreToolUse` and `PostToolUse`
only, and step 6 speaks of taking `UserPromptSubmit` "off the hot path" rather than of deleting its
registration. As actually shipped, all three registrations were deleted. Following steps 5 and 6 as
literally worded leaves `UserPromptSubmit` registered and the migration incomplete. Step 6's
postcondition above is written for the shipped end state rather than the step's own wording, and
this is the one place where those two disagree.

**5.3 -- The durable checkpointer does not exist at runtime.** Recorded as REVIEW-INDEX 42 and
re-verified: `langgraph.checkpoint.sqlite` and `langgraph_checkpoint_sqlite` both raise
`ModuleNotFoundError`, while `requirements.txt` line 31 declares `langgraph-checkpoint-sqlite>=1.0.0`.
Requesting a durable checkpointer returns an in-memory one and logs nothing. This matters to step 5
specifically: that step reassures you that "crash recovery is unaffected (`CheckpointManager` is
in-process, ADR-011)". The reassurance is true about the *architecture* and does not establish that
durable recovery works, because the durable backend is absent. Treat crash recovery as in-memory
only until that import resolves.

**5.4 -- The retained `Stop` hook attempts a pull request on every response turn.** Recorded as
REVIEW-INDEX 40, escalated and then partly de-escalated by REVIEW-INDEX 45. Two independent
conditions currently stand between it and succeeding. Step 7 tells you to leave `Stop` alone, and
that instruction is correct for a different reason than a reader might assume: not because the hook
is known-good, but because it is the one component whose failure mode is *opening real pull requests
unprompted, once per turn, on any feature branch*. Do not change any `sys.path` line under
`hooks/stop_notifier/` while migrating. Restoring either missing import without first revisiting the
trigger conditions is the specific action that would make it fire.

**5.5 -- The irreversible part of v2.0.0 did not ship.** Section 10 of the HLD states that "the
irreversible part of v2.0.0 is the three ADR-009b policy deletions (1,864 lines, recorded informed
decision)". Measured across the release range `873db04..00c31f8`, the only file deletions are 13
generated `.drawio` diagrams; `policies/` and `docs/policies/` are unchanged. **The migration this
release actually ships contains no irreversible step of that kind**, which is why section 6 can name
a full rollback rather than a point past which rollback stops being available.

---

## 6. Rollback

Rollback runs in **strict reverse order** of section 3. This is not a formatting preference: each
inverse step's precondition is the state that existed just before its forward counterpart ran, so an
inverse can only be applied once every later step has already been undone. Attempting these in
forward order fails at the first one, because undoing step 1 while step 2's registrations still
exist removes the plugin that owns the `unregister-mcp` command you need for step 2.

| Undo | Action | Precondition that must hold when you run it |
|---|---|---|
| Step 6 | Restore the `UserPromptSubmit` entry from your P1 backup | You have the P1 backup |
| Step 5 | Restore the `PreToolUse` and `PostToolUse` entries from your P1 backup | `UserPromptSubmit` is back |
| Steps 4, 3 | Nothing to undo -- neither wrote anything | n/a |
| Step 2 | `/claude-workflow-engine:unregister-mcp` | `PreToolUse` is back. The command **refuses by default** when `PreToolUse` is absent, because unregistering the MCP gate on a machine that also has no `PreToolUse` gate leaves no push gate at all |
| Step 1 | `/plugin uninstall`, then the by-hand cleanup in `docs/guides/uninstall-residue.md` | The MCP registrations are gone |

**There is no point of no return in this migration.** Every step above has a true inverse or a
documented compensating action, so the invertible prefix runs the full length of the procedure.
Section 5.5 gives the measurement behind that claim; if the ADR-009b policy deletions ship in a
later release, this sentence stops being true and the point of no return becomes that deletion.

**Step 1's inverse is a compensation, not a true inverse.** `plugin uninstall` leaves
`extraKnownMarketplaces` and `enabledPlugins` present-but-emptied, plus an orphaned cache directory
that `claude plugin prune` does not clean. `docs/guides/uninstall-residue.md` sections 4 and 5 remove
that residue by hand. Rollback is complete only after that document has been worked through.

### The one unsafe state, which is not a point of no return

Step 5 carries the clause **Do not perform this step if step 3 did not pass**. That clause names an
unsafe state, not a point of no return. The two are different failures, and conflating them would
hide the one that can actually hurt you:

- A *point of no return* is a step past which rollback is unavailable. This migration has none.
- The *unsafe state* is step 5 performed without steps 2 and 3. Deleting `PreToolUse` removes the
  local version-push gate, and under ADR-019 the MCP replacement does not exist until step 2 runs.
  A machine in that state has **no local push gate at all**, reopening exactly the bypass that
  commit `1bb4303` closed. It is fully reversible -- restore the two entries, or complete step 2 --
  and it is dangerous the entire time it persists, because nothing announces it.

The CI-side assertion still protects the shared repository, so nothing non-compliant merges from a
machine in that state. Local protection is what is absent.

**This precondition is enforced, not merely documented.** `unregister-mcp` refuses by default when
`PreToolUse` is absent, and every command runs a start-up check that reports the unsafe state. That
matters because `unregister-mcp` can reach the unsafe state **without passing through this runbook**
at all, so wording here could never have covered it. In a project whose founding finding is that
documented-only policies do not run, a numbered step in a guide must not be mistaken for a control.

---

## 7. Valid stopping points (explanation)

A partial migration is a coherent end state, not a failure.

| Stopped after | Safe? | Why |
|---|---|---|
| Step 1 | **Yes -- fully coherent** | Plugin commands work, all v1.21.5 hooks still run, enforcement unchanged. You gained the commands and gave up nothing. This is the expected resting state for a user who does not want MCP |
| Step 2 or 3 | Yes | The above plus MCP-backed capabilities registered and verified. Nothing lost |
| Step 4 | Yes | The above plus knowledge of the entry points. Nothing lost |
| Step 5 or 6, **having passed step 3** | Yes -- the target state | Hook-free, explicit invocation, MCP-backed gate present. You give up automatic enforcement, by design |
| Step 5, **having skipped steps 2-3** | **NO** | No local push gate whatsoever. Do not stop here and do not pass through here. Restore the two entries or complete step 2 |

If step 3's reachability check is the first thing you try and it fails, read that as "step 2 has not
been run", not "the migration failed".

---

## 8. Data migration, and what does not apply (explanation)

**Data migration: none.** `CheckpointManager` state stays at its existing location and format.
ADR-011 changes the durability contract, not the layout -- and see section 5.3 for what that
contract currently delivers.

**No India regulatory layer applies to this document.** The migration touches a single developer's
local tooling configuration. It processes no personal data, classifies no cyber-security incident,
and serves no public-sector digital service, so neither the CERT-In reporting window nor GIGW 3.0's
plain-language mandate is triggered. This is stated rather than left silent because those citations
appear in adjacent documents in this project and their absence here is deliberate, not an oversight.

**Escalation, therefore, has no regulatory clock.** If a step's postcondition does not hold and this
document does not explain why, stop and restore from the P1 backup rather than continuing. There is
one operator and no handoff.

---

## 9. Provenance

| Claim | Source | Status |
|---|---|---|
| The eight steps, verbatim | `docs/phase-2-validation/hld_v2.md` section 10, table at lines 1346-1355 as of 2026-08-04 | Reproduced |
| `hooks` holds exactly `Stop` and `Notification` | Read-only parse of the live `~/.claude/settings.json` | MEASURED 2026-08-04 |
| The six FR-17 command names | `scripts/pipeline_invocation.py`, constant `FR17_COMMANDS` | MEASURED 2026-08-04 |
| `scripts/settings-config.json` registers three deleted hooks | Parse of that file's `hooks` object | MEASURED 2026-08-04 |
| Both sqlite checkpoint modules raise `ModuleNotFoundError` | Import attempt in the project interpreter | MEASURED 2026-08-04 |
| The ADR-009b deletions did not ship | `git log --diff-filter=D` over `873db04..00c31f8` | MEASURED 2026-08-04 |
| The `Stop` hook's PR behaviour | `docs/REVIEW-INDEX.md` entries 40 and 45 | Carried forward, not re-measured |
| The uninstall residue shape | `docs/guides/uninstall-residue.md`, itself derived from the FR-14a spike | Carried forward, not re-measured |

**Not verified by this document:** no `plugin install`, `plugin uninstall`, `register-mcp` or
`unregister-mcp` was run while writing it, and no settings file was written. The project owner's
standing ruling forbids running install or uninstall live, precisely because install mutates
`settings.json` in ways uninstall does not reverse. Every step's postcondition above is therefore a
check this document specifies for you to run, not one it has run for you.

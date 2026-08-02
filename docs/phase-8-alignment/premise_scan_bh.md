# Premise-Staleness Scan -- Batches B through H

**Date:** 2026-08-02
**Author:** architecture-conformance-auditor
**Mode:** READ-ONLY. No sprint artifact was modified by this pass.
**Scope:** 29 issues, keys V2-009 through V2-037, live as #265-#293.

**Verdict:** **2 stale premises, 1 incoherent acceptance criterion, 1 stale-or-ambiguous build
status, and 1 systematic citation-drift defect spanning 7 issues.** Batches C and H are clean of the
hunted class. The rate is far below batch A's -- and that is the finding, not a disappointment.

## What was hunted

The class, defined by the V2-004 instance: **an issue whose body or acceptance criterion rests on a
state claim that was true when written and is false now.** V2-004 asserted a file was absent; it had
been written 20 minutes earlier; nothing downstream re-checked it.

**Method.** For every state claim, I opened the path, ran the grep, or counted the thing. Nothing was
accepted by reasoning that it was probably still true. That is the only difference between this and a
reading, and it is the difference that matters -- V2-004's defect survived four artifacts and a live
issue precisely because everyone downstream reasoned from the claim.

## Scope arithmetic, verified not assumed

MEASURED by grouping `github_issues.json` by batch and cross-joining `issue_key_map.json`:

| B | C | D | E | F | G | H | Sum |
|---|---|---|---|---|---|---|-----|
| 2 | 4 | 3 | 6 | 3 | 9 | 2 | **29** |

Keys V2-009..V2-037 = 29. Issue numbers 265-293 = 29 contiguous, no gaps. The brief's split is
correct. **29 expected, 29 examined.**

---

## 1. Stale premises found

### S-01 -- V2-009 (#265, batch B) -- HIGH

**Claim as written:**

> PROPAGATION HAZARD: the supersession is recorded in hld_v2.md section 12 OAQ 4, but ADR-013's own
> body (hld_v2.md:406 and :436-443) and the binding clause at hld_v2.md:1696-1700 **still carry the
> superseded four-site framing with no pointer to the correction.**

**What is true now.** All three named sites carry the corrected framing. MEASURED:

- `hld_v2.md:406` reads *"**Context (current state, as of Phase 5 -- MEASURED at runtime).** The
  builder discovers only **300 of 411** Python files. **The binding cap is
  `langgraph_engine/parsers/call_graph_builder_legacy.py:64`**"* -- one binding cap named, no
  four-site list.
- `hld_v2.md:444-445` reads *"**[CORRECTED Phase 5] 17 truncation sites exist; exactly TWO bind. The
  prior 'four independent sites' framing was wrong in substance, not only in attribution.**"*
- `hld_v2.md:1696` is the rules/45 data-source inversion note and names
  `call_graph_builder_legacy.py`.

**When it flipped.** Commit `14f742a`, 2026-08-02 07:50:31, *"docs(adr-013): correct the binding
target"*, +77 lines to both HLDs. The issue was drafted at `7b29820` on 2026-08-01 17:08:00.

**This is the exact V2-004 shape.** True when written, false now, still standing in the live issue.
It is advisory rather than blocking -- but it sends the implementer of the highest-risk call-graph
item to three places to fix something already fixed, and implies a correction did not land when it
did.

### S-02 -- V2-020 (#276, batch E) -- LOW

**Claim:** *"only the personas for DISPATCHABLE agents -- not all **505** agent directories."*

**MEASURED:** 508 agents, 996 skills. `agents_all.json` holds 508 and `skills_all.json` 996; the
on-disk directory counts agree exactly (`agents/*/` = 508, `skills/*/` = 996).

Nothing hangs on it -- none of V2-020's three ACs references a count. **MEASURED: this is the only
stale library count in all 29 issues.** Searching every body and AC for 505, 508, 992 and 996 returns
exactly this one hit; no issue cites 992.

### S-03 -- Line-citation drift, 7 issues -- MEDIUM

The requirements and architecture documents grew after the issues were drafted, so `file:line`
citations no longer resolve. MEASURED, at draft commit `7b29820` versus now:

| Document | At draft | Now | Delta |
|---|---|---|---|
| `SRS.md` | 975 | 1131 | **+156** |
| `hld_v2.md` | 1946 | 2023 | **+77** |
| `hld.md` | 1946 | 2023 | **+77** |
| `prd-v2.md` | 507 | 511 | +4 |
| `product-sequencing-v2.md` | 760 | 760 | 0 |
| `REVIEW-INDEX.md` | 325 | 325 | 0 |

**17 of the 18** md line citations in B-H point into a document that changed length. I resolved 16
individually; **8 are confirmed wrong**:

| Citation | Issue | Now lands on |
|---|---|---|
| `SRS.md:296` | V2-010 | **a blank line** |
| `SRS.md:307` | V2-012 | **a blank line** |
| `SRS.md:749` | V2-030 | the FR-22 row, not FR-34 |
| `SRS.md:808` | V2-030 | FR-11 prose. The OUTSTANDING Change Log obligation it names is now at **`SRS.md:968`** |
| `hld_v2.md:661` | V2-025 | circuit-breaker false-open math |
| `hld_v2.md:683` | V2-025 | `message-queues-core` lease model |
| `hld_v2.md:1318` | V2-036 | the NFR cross-interaction table |
| `hld_v2.md:1319` | V2-036 | same table. SS 10's runbook now begins at **`hld_v2.md:1342`** |

The other 8 sampled citations still resolve, because they sit above the insertion points. Every cited
*fact* still exists somewhere in its document -- only the pointers rot. It costs a search, except for
the two landing on blank lines, which read as a deleted section.

*Probe limitation: 16 of 18 were opened individually. **8 confirmed wrong is a floor, not a total.***

---

## 2. Unsatisfiable / incoherent acceptance criteria

### U-01 -- V2-033 (#289, batch G) -- MEDIUM

The body and the AC attribute the same bound of **2** to two different, non-overlapping sets:

> **Body:** "The true floor is approximately 2 -- **the unconditional git rev-parse calls**."
> **AC2:** "asserts the per-turn spawn count is at most 2 (**the two scripts confirmed to exist**)"

**MEASURED:** `hooks/stop_notifier/` holds **17** subprocess spawn sites across `core.py`,
`post_impl.py` and `voice.py`. Exactly **2** are git rev-parse calls, both in `post_impl.py` at `:56`
and `:209`. Separately, the **2** surviving scripts each have their own spawn: `sync-version.py` via
`subprocess.run([sys.executable, str(sync_script)])` in `post_impl.py`, and `voice-notifier.py` via
`subprocess.Popen` in `voice.py`.

That is four distinct spawn opportunities, not two. **A test asserting "at most 2" cannot be written
without deciding which set the bound covers, and the issue supplies both answers.** An implementer who
instruments 20 real invocations and measures 3 or 4 cannot tell whether that is a pass with a
documented exception or a failure.

Same shape as V2-004's AC3 -- rigour that cannot be evaluated. Weaker, because an owner ruling fixes
it rather than the criterion being self-contradictory on its face.

### U-02 -- V2-017 (#273, batch D) -- MEDIUM

**Claim:** *"**No doctor command** and no commands/ directory exist on disk (verified absent
2026-08-01)."*

Half true, and the false half is one grep away. MEASURED: there is no `commands/` directory anywhere
-- that holds. But a doctor command **does** exist: `scripts/cli.py:209` defines `cmd_doctor(args)`
and `scripts/cli.py:340` registers `cwe doctor` with help *"Diagnose common issues"*.

What does not exist is a **plugin** doctor implementing ADR-020's DETECT layer, which is what the
issue means. It cuts both ways: an implementer grepping for `doctor` finds a live command and may
conclude the layer is partly built, or may extend the engine CLI instead of building the plugin
command.

---

## 3. Claims I checked that turned out accurate

A clean check is a result. Each of these was a live opportunity for the V2-004 defect and did not take
it.

| Issue | Claim | Verification |
|---|---|---|
| **V2-034** #290 | 9 scripts referenced, 7 absent, only `sync-version.py` and `voice-notifier.py` exist | **Exact.** All 7 return nothing from a repo-wide `find` *and* nothing under `~/.claude`; all 7 are referenced from `stop_notifier/core.py`; the 2 exist at `scripts/tools/`. 7 + 2 = 9 |
| **V2-035** #291 | 6 application + 3 definition timeout sites, 9 total; `task_orchestration.py:160` composes to 75s | **Accurate at every one of the 9 lines.** `:160` reads `timeout=_pg_inner_timeout + 15,` with `_pg_inner_timeout = 60` at `:128`. 60 + 15 = 75 confirmed |
| **V2-019** #275 | 19 `open()` sites lacking `encoding=`, up from a 12-count grep that missed the mode-less form | **Independently reproduced.** My own AST scan of `langgraph_engine/`, `hooks/`, `scripts/`, `src/` returned exactly **19**, of which **7 are the mode-less form** -- the precise trap the issue names |
| **V2-031** #287 | `step_decorator.py:169` swallows a checkpoint failure; CheckpointManager survives FR-4 | **Exact.** `:169` is `logger.warning("[step_decorator] Checkpoint save failed: %s" % exc)` inside an `except`. `resume_flow` at `orchestrator.py:941`, `resume_from_checkpoint` at `recovery_handler.py:462` |
| **V2-027/029** #283/#285 | 135 of 2,218 nodes (6.09%); ~6 of 116 spawn sites; 17 retained | **Accurate, and 116 reconciles.** `impact_analysis_graph.json` holds exactly 135 `affected_nodes`; 135/2218 = 6.086%. `audit_surface.json` says 112 spawn sites, and correction #7's 4 missed aliased imports gives 112 + 4 = **116**. A grep of `stop_notifier/` returns **17** |
| **V2-021** #277 | `docs/guides/uninstall-residue.md` absent | **Still true.** 14 other files in `docs/guides/`, not this one |
| **V2-015** #271 | `.claude-plugin/plugin.json` absent | **Still true.** Neither file nor directory exists |
| **V2-026** #282 | No `commands/` directory | **Still true** |
| **V2-028** #284 | `3-level-flow.py` registered, 120s timeout | **Still true**, read from `~/.claude/settings.json` |
| **V2-014** #270 | `~/.claude/rules/model-fallback.md` live, no repo copy | **Still true** |
| **V2-016/022** #272/#278 | 17 settings.json writers, a lower bound | **Matches its enumeration** (17 declared / 17 in array; siblings 62/62 and 112/112), and both issues correctly hedge it. `setup_wizard.py` exists at `scripts/setup/` |
| **V2-037** #293 | VERSION 1.21.5 vs CLAUDE.md 1.21.4 | **Still true** |
| **V2-036** #292 | product-sequencing's "NOT YET" runbook statements are stale | **The staleness note is itself correct** -- an issue correctly *handling* a stale premise instead of inheriting it. The statements survive at `:348, :606, :617, :714, :722`, and they are stale: `hld_v2.md:2013` records *"register-mcp inserted as step 2; sequence renumbered to 8 steps"* |
| **V2-018** #274 | The 13-vs-95 dispute stands unreconciled | **Immunised by construction.** AC6 requires figures *"reported as MEASURED values, never asserted against a pre-committed number"* -- the one issue that cannot contract this defect |

## 4. Checks that came back clean, and why

| Check | Method | Result |
|---|---|---|
| Any B-H issue asserting the policy audit is missing or non-conformant? | Searched 29 bodies/ACs for `policy-implementation-audit`, `audit matrix`, `46-row`, `46 polic` | **CLEAN.** Only V2-024/V2-027/V2-034 referencing the ledger as a *dependency*. The `e520b5e` reshape stranded nothing. Confirmed independently: the file is now 556 lines, matrix header `\| # \| Policy file \| Status \| Evidence \| Post-plugin plan \| Basis \| Verification \|`, exactly **46** data rows, tally 18/11/8/8/1 |
| Any issue assuming audited corpus == runtime corpus? | Searched for `get_policies_dir`, `~/.claude/policies`, `docs/policies` | **CLEAN. Zero hits.** The corpus divergence does not reach B-H; it stays a batch A problem |
| Any issue naming `parsers/config.py` as a fix target? | Searched 29 for `config.py` | **CLEAN.** One hit, V2-009, naming it *only* to say it is dead and that the amended AC drops it |
| Any issue scoped as a 17-site or 4-site job? | Searched for `17 truncation`, `17 sites`, `four sites`, `4 named sites` | **CLEAN.** V2-009 only, using the old framing to describe what it superseded |
| Any issue still carrying V2-009 at 5 points? | Searched for `5 points`, `size 5` | **CLEAN outside V2-009 itself.** No issue inherited the stale size |
| Any issue relying on the two fixed MCP defects? | Searched for `non-idempotent`, `POST retry`, `25-row`, `page cap` | **CLEAN. Zero hits.** Both were tooling faults; no body depends on either |
| **Batch C (4) and batch H (2) clean?** | All 6 examined individually | **CLEAN of the hunted class.** C's four are build-from-scratch items whose *"no code exists to assess"* status cannot go stale by something being built elsewhere, and is MEASURED still true. H's two are both correct. Their only defect is citation drift (V2-012, V2-036) |

---

## 5. Discrepancy with the brief -- reported, not adopted

The brief states *"10 of the 18 ENFORCED policies are absent from the tree `get_policies_dir()`
actually reads."*

**I measure 9.** Enumerated, so the count matches its enumeration:

1. `final-summary-policy.md`
2. `hook-system-policy.md`
3. `issue-closure-policy.md`
4. `quality-gate-policy.md`
5. `recovery-policy.md`
6. `test-generation-policy.md`
7. `tool-optimization-policy.md`
8. `unicode-fix-policy.md`
9. `windows-path-policy.md`

**Method:** parsed the 46-row matrix, took the 18 rows with Status ENFORCED, tested each filename
against the `.md` basenames from an `os.walk` over `~/.claude/policies`.

The brief's surrounding figures **are** confirmed: `docs/policies` 46, `~/.claude/policies` 35 unique
basenames, 18 of 46 audited policies absent in total.

**A plausible source of the 10.** Three absent names have near-miss neighbours live --
`tool-optimization-policy.md` vs `tool-usage-optimization-policy.md`, `test-generation-policy.md` vs
`test-case-policy.md`, `issue-closure-policy.md` vs `github-issues-integration-policy.md`. A
prefix or fuzzy matcher would report **6**; exact-basename matching gives **9**. Neither yields 10, so
the difference is more likely a transcription than a method difference.

---

## 6. Probes I discarded

Held to the standard the Phase 8 report set when it discarded a non-recursive glob.

1. **A path-existence probe** resolved bare basenames (`graph_model.py`, `sequencing_risks.md`)
   against the repo root and reported 44 of 74 asserted paths as MISSING. Almost all were relative or
   partial references resolving elsewhere. **Discarded. No path-absence finding is reported from it.**
2. **A case-sensitive grep** for `NOT YET` in `product-sequencing-v2.md` returned 2 and appeared to
   refute V2-036's staleness note. Case-insensitively it returns **13**, of which 5 concern the
   runbook. **Discarded; V2-036 is recorded as accurate.**

**And my own prior citations have rotted.** The Phase 8 readiness report cites `SRS.md:1048`, `:740`
and `:736`. SRS.md has since grown 1056 -> 1131 (`92a9a5d`, then `f26940d`). Those findings remain
open but have moved: the dead-constant risk row is now **`SRS.md:1122`**, the FR-21 four-site AC row
is now **`SRS.md:748`**, FR-17 is now **`SRS.md:744`**. Recorded because this pass audits exactly that
failure mode, and exempting itself would be the defect.

---

## 7. What I could not verify

- **The live issue bodies for #265-#293.** The github-api MCP server has no `get_issue` and no
  `list_comments`. Everything here is against `github_issues.json`. If scrum-master-agent has amended
  that file concurrently, some findings may already be closed.
- **Whether U-01's four spawn opportunities actually co-fire on one turn.** Settling V2-033's real
  floor needs the Stop hook run with instrumentation -- which is the work V2-033 exists to do. My 17
  and 2 are static counts.
- **2 of the 18 line citations** were counted but not opened, so S-03's "8 confirmed wrong" is a floor.
- **Whether `hld.md` carries the same corrections as `hld_v2.md`.** `14f742a` touched both with
  identical +77 deltas, consistent with them being byte-identical, but I verified the corrected text
  in `hld_v2.md` only.
- **Unsatisfiability arising from un-takeable measurements** rather than internal contradiction. Only
  V2-033's AC2 and V2-017's build status surfaced under the tests I applied; a criterion that is
  merely *expensive* to satisfy would not have.

---

## Summary

| | Count | IDs |
|---|---|---|
| Stale premises | **3** | S-01 (HIGH), S-02 (LOW), S-03 (MEDIUM, spans 7 issues) |
| Incoherent / ambiguous ACs | **2** | U-01 (MEDIUM), U-02 (MEDIUM) |
| **Total findings** | **5** | 1 HIGH, 3 MEDIUM, 1 LOW |
| Issues examined | **29 of 29** | V2-009..V2-037 |
| Batches clean of the hunted class | **2** | C, H |

Machine-readable detail: `docs/phase-8-alignment/premise_scan_bh.json`.

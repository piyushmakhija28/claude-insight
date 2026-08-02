# Product Sequencing v2.0.0 -- WSJF, MVP Boundary, NFR Ownership, Critical Path

**Phase:** 0 (original), amended at **Phase 2.2** (re-validation against the APPROVED HLD and the
completed FR-14a spike) and again at **Phase 2.3** (re-sequencing after `solution-architect` decided
the NFR-1/bundled-MCP-server question) -- both amendment passes by product-manager-agent, post BA
normalisation, post Deliverable-1 approval
**Author:** product-manager-agent
**Date:** 2026-08-01 (Phase 0 baseline; Phase 2.2 and Phase 2.3 amendments, same day)
**Target repo:** `claude-workflow-engine` v1.21.4 -> v2.0.0
**Primary input (Phase 0):** `docs/phase-0-requirements/prd-v2.md` (475 lines, 14 sections, BA-validated FR/NFR set + RTM)
**Primary inputs (Phase 2.2 amendment):** `docs/phase-1-architecture/hld.md` (APPROVED, consensus
iteration 4), `docs/phase-1-architecture/plugin_schema_spike.md` (5/5 items measured),
`docs/phase-1-architecture/consensus_summary_phase1.md`, `docs/orchestration_prompt.md` SS 1.2/1.4/3.3
**Primary inputs (Phase 2.3 amendment):** `docs/phase-1-architecture/hld.md` ADR-019 (SS 4.2), the
coordinator's relay of `solution-architect`'s decision, `docs/phase-2-validation/ba_review.json`
(FIND-09, FIND-10), `docs/phase-2-validation/advisory_items.json` (ADV-011/ADV-012)

**Phase 2.2 amendment summary:** six items re-scored or newly sized (SS 0a), two new subsections
added (SS 2a re-scored WSJF rows, SS 2b NFR-1/bundled-MCP-server options for `solution-architect`'s
Phase 2.3 decision), SS 5/6/7/8 re-derived accordingly.

**Phase 2.3 amendment summary:** `solution-architect` decided the SS 2b question -- **option (a)**,
not (b) -- via ADR-019 (zero bundled MCP servers, explicit opt-in `register-mcp` command). New SS 2c
records the decision, sizes the new `register-mcp`/`unregister-mcp` work (size 5, WSJF 3.80), confirms
the MVP boundary does not move to v2.1, names the one-step-install property the boundary was
silently carrying and now states explicitly, and confirms this document's boundary has no remaining
dependency on business-analyst-agent's FR-14 wording decision (already applied). SS 4/5/6/7/8
re-derived accordingly.

Per this document's own append-and-correct precedent (see the Kano rework note below), superseded
figures are struck through in place rather than silently deleted, so every correction stays traceable.

**Delegation note (corrected rule applied):** WSJF scoring below uses a **named reference
implementation** rather than a hand-derived proof or a delegated math-expert call. WSJF arithmetic
follows Reinertsen (2009) *Principles of Product Development Flow* as reproduced in
`claude-global-library/skills/product-management-core/SKILL.md` SS M1 (WSJF = CoD/size, CoD =
UBV+TC+RROE, SAFe 1-10 rubric, Fibonacci job-sizing) -- the rank-order-optimality proof there is
cited, not re-derived.

**Kano classification was considered and rejected, not applied.** The same skill file's SS 13
("What Not to Do") states, verbatim: *"Do not apply Kano classification without a proper survey --
informally guessing Kano categories is unreliable; must use the functional/dysfunctional
questionnaire methodology."* An earlier draft of this document cited that exact line as if it
licensed an unsurveyed classification -- it does the opposite, and the error is corrected here
rather than patched over with a relabel. This project has one user (the developer) and no survey
population to draw a second respondent from; a proper Kano functional/dysfunctional questionnaire
is not merely skipped here, it is structurally unobtainable. Keeping the M/P/A/I vocabulary under a
softer label ("inferred heuristic") would not fix the underlying problem -- it would still be one
person's unvalidated guess about how a population would react, wearing a disclaimer. SS 3 below
re-derives every prioritisation call this document makes on grounds it can actually support: gate
dependency, the FR-8a acceptance criterion's own constraints, revealed usage evidence, and
Reinertsen cost-of-delay -- the same WSJF instrument already used in SS 2, not a second framework
standing next to it.

---

## 0. What Changed Since the Requirement Doc Was Written

`docs/orchestration_prompt.md` SS 3.3 records: **Deliverable 1 (policy audit) is APPROVED as of
2026-08-01, with three binding resolutions.** This retires the single hardest constraint the original
task brief anticipated ("the entire critical path runs through the policy audit"). Consequences for
this document:

- Workstream B (hook removal) is UNBLOCKED, subject to Resolution 1 (CallGraph fix is in-scope, FR-9a)
  and Resolution 2 (Stop-hook items become "repair what it should do", folded into FR-8a).
- The **new** critical path bottleneck is FR-9a -> FR-10 (SS 6), not the audit.
- ADR-009b's five-policy merge decision (`prd-v2.md` SS 8) is explicitly called out as **separate and
  still open** -- it gates FR-19 only, not the section 9 deliverable chain. FR-19 is therefore excluded
  from the v2.0.0 critical path in SS 6 and addressed as a standalone deferred item in SS 3.

---

## 0a. Phase 2.2 Re-Validation -- What the Approved HLD Invalidated

**Phase:** 2.2 (product-manager-agent), re-validating this document against the APPROVED HLD
(`docs/phase-1-architecture/hld.md`, consensus APPROVED 2026-08-01, iteration 4) and the completed
FR-14a spike (`docs/phase-1-architecture/plugin_schema_spike.md`, 5/5 items measured empirically).

**Method note (rule reapplied):** every re-score below still uses the named reference implementation
from SS 0 -- Reinertsen (2009) WSJF = CoD/size, CoD = UBV+TC+RROE, SAFe 1-10 rubric -- no
hand-derivation, no Kano.

Six items required re-scoring, not merely re-noting:

1. **NFR-3 was overscored on a false premise.** SS 2 originally sized "NFR-3 replacement
   crash-recovery writer" at 8 points / WSJF 3.00 on the Phase 0 claim that `post-tool-tracker.py`
   was the sole writer of checkpoint state. HLD OAQ 1 (SS 12) independently re-verified against live
   source (`checkpoint_manager.py`, exact method count and line numbers matched byte-for-byte by the
   Phase 1.4 consensus reviewer) that `CheckpointManager` is a **pre-existing, already-wired**
   step-boundary writer that survives FR-4 untouched. The remaining v2.0.0 work is materially
   smaller: name the contract, fix 3 durability defects (ADR-011 -- swallowed checkpoint-save
   failure, checkpoint/progress dual-write, non-idempotent replay), and port progress writes to
   `mcp-post-tool-tracker`. **Re-scored: size 8 -> 3, WSJF 3.00 -> 6.33.** See SS 2a.

2. **NFR-2's scope is larger than SS 2 modeled, not smaller.** NFR-2 previously shared a single
   3-point "measurement harness" row with NFR-1. ADR-016 found NFR-2 is **already violated inside
   the engine, independent of hooks**: 6 `timeout=` application sites across 5 files
   (`prompt_gen_expert_caller.py:228`, `todo_decomposer.py:147`, `orchestrator_agent_caller.py:137`,
   `todo_executor.py:114`, `task_orchestration.py:160,217` -- the last of which is the 75-second
   wall-clock abort, `STEP1_PROMPT_GEN_TIMEOUT` default 60 + a 15s margin, on the pipeline's own
   critical path). Deleting the two hooks satisfies none of these. ADR-016's fix is five distinct
   non-temporal control mechanisms (attempt-count budget, lease renewal, convergence-hash detection,
   circuit breaker with exponential-backoff-plus-jitter per external dependency, slow-call-rate trip)
   -- a resilience-engineering build, not a static scan. **Split out as its own row: size 8, WSJF
   2.88.** NFR-1's measurement-harness work is split out separately at size 2, WSJF 10.50 -- the
   process-count-delta protocol was always genuinely small; it was NFR-2's timeout-removal work that
   was hidden by being bundled into the same row. See SS 2a.

3. **De-hooking's process-footprint claim needed re-deriving, and shrinks.** FR-4/FR-5's row carried
   UBV=9 partly on a "core NFR-1 outcome" framing. ADR-018's corrected spawn-site census (112
   AST-detected + 4 alias-blind-spot sites = 116 total, independently grep-confirmed) shows FR-4+FR-5
   remove **roughly 6 of 116 spawn sites (~5%)** -- `hooks/stop_notifier/` alone retains 17 spawn
   sites by ADR-010's own deliberate "keep Stop" decision. Hook deletion's real value is **invocation
   frequency** (two Python interpreter starts *per tool call*, not aggregate spawn-site count) --
   that argument survives intact, but the "core NFR-1 outcome" framing does not: ADR-018 item 5
   (spike-measured) shows bundled `.mcp.json` stdio servers spawn on plugin enable with zero tool
   invocations, so **hook deletion is necessary but not sufficient for NFR-1**. **Re-scored: UBV
   9 -> 8, CoD 21 -> 20, WSJF 7.00 -> 6.67**, and NFR-1's actual closure now depends on the Phase 2.3
   decision in SS 2b.

4. **FR-18 is not achievable as written -- sized, not resolved, here.** FR-14a item 4 (measured):
   `claude plugin uninstall` empties `enabledPlugins` and `extraKnownMarketplaces` to `{}` but never
   removes the keys, and leaves an `.orphaned_at`-marked plugin-cache directory that `claude plugin
   prune` does not clean. FR-18's AC as written ("uninstall leaves no orphaned hooks, no stale MCP
   registrations, no leftover `settings.json` entries") is **unsatisfiable against platform behaviour
   this team does not control**. `business-analyst-agent` owns the AC rewrite (two candidate paths:
   narrow the AC to plugin-attributable residue only, or add a plugin-shipped cleanup command). This
   document sizes both contingencies in SS 2a so D5 is ready whichever way the AC lands. **CRITICAL,
   carried into SS 4/SS 9:** Deliverable 5's own gate text in
   `v2.0.0-plugin-transformation-requirements.md` SS 9 ("installs and uninstalls cleanly on Windows")
   is the identical falsified claim one level up and needs the same synchronized rewrite, by the same
   owner -- not a second, independent decision.

5. **FR-14a is RESOLVED -- all 5 items measured, nothing deferred to inference.** Retired from the
   active WSJF table (spent, like D1) and from the "second-riskiest link" framing in SS 6/SS 7 below.
   ADR-009a branch 2 is unblocked (item 2 measured PRESENT, plus `CLAUDE_PLUGIN_DATA` and
   `CLAUDE_PROJECT_DIR`); ADR-012's `__file__`-ascent is now defence-in-depth, not the required path.

6. **NEW, unsized in the prior revision -- the NFR-1/bundled-MCP-server conflict (ADR-018 item 5,
   measured).** Enabling the plugin spawns its `.mcp.json` stdio servers even when no tool is ever
   called -- two confirmed spawns in a session whose prompt explicitly forbade tool use. This
   directly contradicts NFR-1. The user assigned the DECISION to `solution-architect` at Phase 2.3;
   this document does not decide it, only sizes the three plausible outcomes so the MVP boundary is
   ready either way. See SS 2b.

---

## 1. Deliverable Units (aligned to section 9 + new FRs)

Section 9 of `v2.0.0-plugin-transformation-requirements.md` fixes 7 gates in strict sequential order.
**That order is not a WSJF input; WSJF sequences work inside each gate, and decides what can defer
past the gate closing.** Units below are grouped by the gate they belong to.

| Gate | Contains | New FRs folded in |
|---|---|---|
| D1 Policy audit | FR-1, FR-2, FR-3 | FR-20 (orphan dispositions), FR-23's disposition record | **DONE, approved 2026-08-01** |
| D2 ADR-006 doc | FR-6 | -- |
| D3 KG rebuild | FR-9 (library drift) | -- |
| D4 KG selector | FR-10, FR-11, FR-12, FR-13 | FR-9a (mandatory prerequisite) |
| D5 Plugin skeleton | FR-14 | FR-14a (mandatory prerequisite), FR-15, FR-16, FR-17, FR-18, NFR-5 |
| D6 Hook removal | FR-4, FR-5, FR-7, FR-8 | FR-4a (informs), FR-8a, FR-21, FR-22, FR-23 (mandatory before FR-4), NFR-1, NFR-2, NFR-3 |
| D7 Docs/release | Migration guide, CHANGELOG, VERSION bump | FR-22's Change Log row lands here too |

Excluded from the gate chain (separate track, see SS 3): **FR-19** (`get_policies_dir()` resolver) --
blocked on the ADR-009b five-policy sign-off, a human decision with no engineering WSJF score.

---

## 2. WSJF Table (Phase 0 baseline -- SUPERSEDED for FR-14a/NFR-1/NFR-2/NFR-3/FR-4/FR-5 by SS 2a)

CoD components scored 1-10 (SAFe rubric, reinterpreted for a no-market internal tool per the hard
constraint: **UBV = developer-time-saved**, not revenue; **TC = time-criticality/blocking-ness**;
**RROE = risk-reduction, weighted heavily for correctness defects and the NFR-1 crash-recovery/
governance guarantees named in `prd-v2.md`**). Size in Fibonacci story points. WSJF = CoD / size.

| Unit | Gate | UBV | TC | RROE | CoD | Size | **WSJF** |
|---|---|---|---|---|---|---|---|
| FR-22 SRS append (owner named, content scoped) | D6 | 2 | 6 | 5 | 13 | 1 | **13.00** |
| FR-6 ADR-006 doc (content already exists, needs filing) | D2 | 3 | 6 | 3 | 12 | 1 | **12.00** |
| FR-23 push_gate -> MCP port (MANDATORY before FR-4) | D6 | 5 | 9 | 9 | 23 | 3 | **7.67** |
| ~~FR-4/FR-5 hook deletion (core NFR-1 outcome)~~ -- **re-scored, see SS 2a** | D6 | ~~9~~ | 8 | 4 | ~~21~~ | 3 | ~~7.00~~ |
| ~~NFR-1/NFR-2 measurement harness~~ -- **split, see SS 2a** | D6 | 9 | 7 | 5 | 21 | 3 | ~~7.00~~ |
| FR-9 KG rebuild (mechanical, Workstream C) | D3 | 4 | 5 | 3 | 12 | 2 | **6.00** |
| ~~FR-14a plugin-schema spike (4 unknowns)~~ -- **DONE 2026-08-01, all 5 items measured, retired from active table (SS 0a item 5)** | D5 | -- | -- | -- | -- | -- | -- |
| FR-15/FR-17 remediation (13 + 19 sites, counts already narrowed) | D5 | 4 | 4 | 6 | 14 | 3 | **4.67** |
| FR-7 slash commands (entry points, prerequisite for safe FR-5) | D6 | 8 | 8 | 5 | 21 | 5 | **4.20** |
| FR-9a CallGraph scope-aware fix (prerequisite for FR-10) | D4 | 6 | 9 | 8 | 23 | **8** | **2.88** |

> **Re-pointed and recomputed 2026-08-02.** This row published size **5** and WSJF **4.60** until
> today. FR-9a's acceptance criterion was strengthened by owner ruling to require runtime proof --
> a probe harness, an independent enumeration oracle, module-scoped log capture and a negative test --
> which invalidated the two-constant basis the 5 was estimated against. Re-pointed to **8**
> (provenance `RE_ESTIMATED`). Cost of delay is unchanged at 23, since the re-point moved size and
> not CoD, so WSJF becomes `23 / 8 = 2.875`, shown as **2.88** at the two decimals this table uses.
>
> This drops FR-9a from 10th to joint 13th of the 17 WSJF-bearing units. **Nothing was reordered.**
> No batch boundary and no intra-batch ordering in this plan derives from WSJF -- FR-9a stays first
> in its batch because FR-9b hard-blocks on it.
>
> Carried forward and not laundered: recomputing makes the score arithmetically consistent with the
> new size. It does not make it calibrated. The inputs 6, 9 and 8 remain single-pass estimates never
> cross-checked against a completed item, and NFR-2 now scores an identical 2.875 from a materially
> different split of 8, 8 and 7 -- a fair illustration of what compressing three uncalibrated
> integers into one ratio costs.
| FR-16 build-time snapshot script | D5 | 5 | 5 | 4 | 14 | 5 | **2.80** |
| ~~NFR-3 replacement crash-recovery writer~~ -- **re-scored, see SS 2a** | D6 | ~~7~~ | 8 | 9 | ~~24~~ | ~~8~~ | ~~3.00~~ |
| FR-18/NFR-5 uninstall lifecycle + 3 tests (contingent addendum was SS 2a FR-18a, INVALIDATED not merely un-activated -- see SS 2d) | D5 | 5 | 5 | 6 | 16 | 5 | **3.20** |
| FR-14 plugin skeleton build (gate-text caveat: see SS 4) | D5 | 8 | 7 | 4 | 19 | 8 | **2.38** |
| FR-10..FR-13 KG-driven selector | D4 | 9 | 6 | 7 | 22 | 13 | **1.69** |
| FR-8a decision + instrumentation + FR-21 minimal retire (ships v2.0.0; see SS 3) | D6 | 4 | 6 | 8 | 18 | 3 | **6.00** |
| FR-8a rebuild-if-decided, per capability (unsized -- scope set by the v2.0.0 decision session; presumptive v2.1, see SS 3) | -- | -- | -- | -- | -- | unsized | not scored |
| Migration guide + CHANGELOG + VERSION bump | D7 | 6 | 3 | 2 | 11 | 2 | **5.50** |

**Reading this table correctly (unchanged from Phase 0):** the two highest-WSJF items (FR-22, FR-6)
are high only because their size is trivial (1 point each) -- Reinertsen's formula rewards small
high-stakes jobs. FR-10's selector remains the flagship deliverable despite the lowest WSJF (1.69),
because its size (13) is large and its value cannot be decomposed smaller without breaking FR-9a's
prerequisite relationship. **WSJF sequences within gates; it does not override the fixed D1-D7 order,
and it does not demote FR-10 out of v2.0.0.** The re-derived top-5 is in SS 2a.

---

## 2a. Re-Scored WSJF Rows (Phase 2.2 -- supersedes the struck-through rows in SS 2)

| Unit | Gate | UBV | TC | RROE | CoD | Size | **WSJF** | Change from SS 2 |
|---|---|---|---|---|---|---|---|---|
| NFR-1 measurement harness (process-count delta, per-component attribution, excludes retained Stop hook per HLD SS 9) | D6 | 9 | 7 | 5 | 21 | 2 | **10.50** | Split out of the old combined row; genuinely small on its own |
| FR-23 push_gate -> MCP port | D6 | 5 | 9 | 9 | 23 | 3 | **7.67** | unchanged, reprinted for ranking context |
| FR-4/FR-5 hook deletion (label corrected: necessary but NOT sufficient for NFR-1, per ADR-018) | D6 | 8 | 8 | 4 | 20 | 3 | **6.67** | UBV 9->8, CoD 21->20, WSJF 7.00->6.67 |
| NFR-3 CheckpointManager contract + 3 durability defect fixes (ADR-011; not a new writer) | D6 | 5 | 5 | 9 | 19 | 3 | **6.33** | UBV 7->5, TC 8->5, CoD 24->19, size 8->3, WSJF 3.00->6.33 |
| ~~FR-18a plugin-shipped cleanup command~~ -- **INVALIDATED, not merely un-activated; see SS 2d** | D5 | ~~4~~ | ~~5~~ | ~~4~~ | ~~13~~ | ~~2~~ | ~~6.50~~ | Struck, not carried forward: a plugin-shipped command cannot execute after uninstall, which is when the residue exists. Folds into FR-24 (already-sized documentation work) at size 0, not re-scored |
| NFR-2 timeout-removal engineering (5 non-temporal control mechanisms across 6 `timeout=` sites / 5 files, ADR-016) | D6 | 8 | 8 | 7 | 23 | 8 | **2.88** | Split out of the old combined row; this is where the real size was hiding |

**Re-derived WSJF top-5 (in order, replaces SS 2's top-5):**
1. FR-22 SRS append -- 13.00 (unchanged)
2. FR-6 ADR-006 doc -- 12.00 (unchanged)
3. **NFR-1 measurement harness -- 10.50 (NEW entrant, displaces the old #4 tie)**
4. FR-23 push_gate MCP port -- 7.67 (unchanged, now #4 not #3)
5. FR-4/FR-5 hook deletion -- 6.67 (was tied #4 at 7.00; now #5)

NFR-3's re-scored WSJF (6.33) ranks ahead of FR-9 KG rebuild (6.00) and FR-8a's decision unit (6.00);
it does not displace the top-5 above because it is gated inside D6 behind other prerequisites, and in
practice should be pulled forward alongside FR-22/FR-6-style small wins rather than left at its old
position implied by the retired 3.00 figure. **FR-18a is not part of this ranking discussion** -- it
is struck from the table above and invalidated, not merely deprioritized; see SS 2d.

---

## 2b. NFR-1 / Bundled-MCP-Server Options (DECIDED 2026-08-01 -- option (a), ADR-019. Sizing below is
the original Phase 2.2 sizing, kept intact as the record of what was handed to `solution-architect`
as cost data; see SS 2c for the decision, its consequences, and the new work it creates.)

ADR-018 item 5 (FR-14a spike, measured): enabling the plugin spawns its `.mcp.json` stdio servers --
**two confirmed spawns in a session whose prompt explicitly forbade tool use.** This fails NFR-1's
"zero engine-attributable processes in an idle session" acceptance criterion via the exact mechanism
chosen as hooks' replacement. Per the task brief, this document does not decide the resolution --
`solution-architect` does, at Phase 2.3 -- but sizes the three plausible outcomes so the MVP boundary
is ready whichever way the decision lands.

| Option | Description | Job size (rough) | CoD reasoning | Preserves MVP boundary? |
|---|---|---|---|---|
| (a) Bundle NO MCP servers | Plugin ships zero `.mcp.json` entries; all 13 servers (including the FR-23 push gate) become user/project-scope registrations the plugin documents but does not ship | ~5 pts -- rewrites FR-14's "installable in one step" AC, the D5 gate text, the FR-23-precedes-FR-4 reachability story, and the migration runbook's step 2 ("verify the FR-23 replacement is reachable" no longer follows from install alone) | UBV low (removes the one-step-install value FR-14 exists to deliver); TC high (touches the FR-23 MUST-PRECEDE-FR-4 constraint that gates D6); RROE high (fully eliminates the NFR-1/MCP conflict) | **NO.** Requires a PRD/AC change to FR-14 itself, owned by business-analyst-agent, not just an architecture choice -- returns to this document for re-sequencing once decided |
| (b) Redefine NFR-1 to exclude a minimum-viable bundled set | Bundle only the FR-23 push gate + progress-writer `.mcp.json` servers (the two the HLD's ADR-018 "Chosen" design already assumes); reference the remaining 11 as user-scope, documented not shipped; NFR-1's AC text is amended to name the 2 declared exceptions explicitly | ~1 pt -- an NFR-1 AC edit (business-analyst-agent), since the engineering (FR-23 port, minimum-viable `.mcp.json`) is already priced into existing SS 2/2a rows | UBV/TC/RROE not separately scored -- this is a documentation-level change riding on work already budgeted | **YES.** This is the option the HLD's ADR-018 already designed against; choosing it confirms sunk architecture work rather than re-opening it |
| (c) Per-server opt-in / lazy connect | Wait for or build a mechanism that connects a bundled MCP server only on first tool use, not on plugin enable | ~8+ pts, high uncertainty -- FR-14a item 5 found **no evidence** this exists as a platform capability (2 confirmed eager spawns with zero tool calls); the only fallback inside ADR-018's own "Rejected" analysis is a non-standard trigger (skill-invoked subprocess or on-demand registration outside `.mcp.json`), which forfeits standard MCP tool-discovery UX and is itself unbuilt | UBV/TC/RROE not scored -- this is unproven-platform-capability risk, not a normal engineering estimate | **NO, or NOT YET.** Depends on undocumented/nonexistent Claude Code behaviour; would require its own spike before it could be priced with confidence, pushing D5/D6 out |

**Recommendation basis for solution-architect (sizing only, not a decision):** option (b) is the only
one of the three that does not require re-opening FR-14's AC or waiting on unproven platform
behaviour, and it is already the HLD's working design. Options (a) and (c) are both larger and each
would need to come back through this document for re-sequencing before D5/D6 could close under them.

**Outcome (recorded here, decided in SS 2c below):** `solution-architect` chose **option (a)**, not
(b). The sizing above was passed to `solution-architect` explicitly labelled "cost data, not a
recommendation," and was used as intended: the "(b) preserves the boundary without rework" line is a
statement about schedule, not about which option is correct. It was outweighed by a measurement-
integrity argument this document did not model, because WSJF has no CoD term for "does the metric
remain falsifiable" -- see SS 2c for why that argument is accepted here without dispute.

---

## 2c. Phase 2.3 Amendment -- ADR-019 Decided Option (a); Re-Sequencing the Consequences

**The decision, and why this document accepts it without dispute.** `solution-architect` chose: the
plugin is designed to bundle **zero** MCP servers; registration is designed as an explicit opt-in
`register-mcp` command (`unregister-mcp` is designed to reverse it) (HLD ADR-019). **Both commands are
PROPOSED -- no code exists yet; this is the design that was decided, not a built capability.** The
decisive reasoning: NFR-1 had already taken one
carve-out (the retained Stop hook, excluded via per-component attribution, SS 5). A second carve-out
for "small enough" bundled MCP would leave **nothing** capable of making NFR-1 fail -- the metric
would pass by construction while the user's machine ran more processes than before. This is a
measurement-validity argument, not a cost argument, and WSJF has no term for it (CoD scores value,
time-criticality, and risk-reduction of doing a piece of work -- it does not score whether a metric
stays falsifiable). Accepting a schedule-costlier option to keep the project's primary success metric
falsifiable is not a WSJF override; it is a decision made on grounds this document's instrument was
never built to weigh, correctly resolved outside it.

**1. Does the MVP boundary move?** **No -- it does not move to v2.1.** Nothing that was in v2.0.0's
scope under option (b) is deferred. What changes is composition, not boundary: `register-mcp` /
`unregister-mcp` is **new, mandatory v2.0.0 work** (sized below), because under option (a) it is the
*only* path to any MCP-backed capability at all -- there is no "ship it bundled instead" fallback to
defer to. **What the boundary lost was an implicit property, not a line item, and that is the sharper
finding.** SS 4's "Ships in v2.0.0" bullet for D5 never listed "one-step install of the complete
capability set" as its own entry -- it was carried silently inside FR-14's original wording ("plus
FR-18/NFR-5 lifecycle tests") and inside D5's own gate text ("installs... cleanly"). An implicit
property that fails silently is worse than an explicit one consciously traded away, per the
coordinator's framing, and that is exactly what happened here until this pass: FR-14 promised
one-step install of everything; ADR-019 gives up that property for the MCP-backed half; and this
document's SS 4 never named the property, so it could not have flagged the loss on its own. **Fixed
here:** SS 4's D5 bullet (below) now names "one-step install of commands/agents/skills; MCP-backed
capabilities require the separate `register-mcp` step" as an explicit line item, not an inherited
assumption.

**2. Size of ADR-019's new work.** One new WSJF row, D5, using the same reference implementation as
every other row in this document (Reinertsen 2009, WSJF = CoD/size):

| Unit | Gate | UBV | TC | RROE | CoD | Size | **WSJF** |
|---|---|---|---|---|---|---|---|
| ADR-019 `register-mcp`/`unregister-mcp` command pair -- **PROPOSED, not built** -- designed to write/reverse a `settings.json` merge-against-fresh-read, plus the ADR-019-mandated discoverability check (designed so plugin commands detect an unregistered server and emit one actionable line naming `register-mcp`, so a missing capability never presents as a working one) | D5 | 7 | 6 | 6 | 19 | 5 | **3.80** |

*CoD reasoning:* **UBV=7** -- without this command pair, all MCP-backed capability (including the
FR-23 push gate) is permanently unreachable; this is the sole path to functionality ADR-018's
minimum-viable bundle would otherwise have delivered by default. **TC=6**, not higher, because the
one thing it does *not* block is D6's actual gate: FR-23's mechanically-enforced ordering runs in CI
(ADR-017), not locally, so D6 does not structurally wait on `register-mcp` existing -- but FR-14a/
NFR-5's install-test AC and the discoverability requirement both do. **RROE=6** -- closes a real
correctness/UX gap (silent absence of a capability presenting as a working install) and a new NFR-5
test scenario (round-trip: register then unregister returns `settings.json` to its pre-registration
state), but is new-feature work, not a defect fix, so it does not score as high as NFR-3's re-scored
defect-fix row (6.33). **Size=5**, comparable to FR-7's "entry points" row (also size 5) -- two new
user-facing commands, a shared `settings.json` write-safety helper two writers must now use
consistently (flagged separately in `docs/phase-2-validation/advisory_items.json` as sharpened by
this change, ESCALATION CANDIDATE not merely advisory), and one new automated round-trip test.

This row sits comfortably mid-table: below FR-23 (7.67) and FR-4/FR-5 (6.67), above FR-16's build-time
snapshot script (2.80). It does not enter the WSJF top-5 (SS 2a's re-derived top-5 is unaffected by
this addition).

**Favourable side effect on FR-4/FR-5's earlier caveat.** SS 2a re-scored FR-4/FR-5 down (WSJF
7.00 -> 6.67) partly because hook deletion alone was "necessary but not sufficient for NFR-1" --
ADR-018's finding that even a minimum-viable bundle spawns on enable. **Under ADR-019, sufficiency is
restored, and at zero additional engineering cost**: hook deletion plus *shipping nothing* (an
absence, not a build) together make NFR-1 achievable by construction (HLD SS 9: "ACHIEVABLE, and
still falsifiable"). This is not re-scored back upward here, because the FR-4/FR-5 row's own job
did not change size or CoD -- only the external context resolved favourably, and WSJF rows are not
adjusted for context that does not change the unit's own work.

**3. Does the critical path move?** **Yes, one new internal dependency inside D5; the top-level D1-D7
gate order and D4's FR-9a->FR-10 riskiest-link status are both unaffected.**

```
... -> D5: FR-14 plugin skeleton --PREREQUISITE--> ADR-019 register-mcp/unregister-mcp build
        (PROPOSED, no code yet) --PREREQUISITE--> NFR-5's 4th round-trip test scenario --> D5 gate closes
     -> D6: FR-23 MUST-PRECEDE-FR-4, designed to be CI-enforced (ADR-017 -- itself a PROPOSED CI
        assertion, not yet wired as of this revision) independent of whether any given user ever
        runs register-mcp, once it exists -- D6's actual gate does NOT newly depend on ADR-019's
        command pair
```

FR-9a -> FR-10 remains the single riskiest link (SS 6, unchanged). FR-23's CI-side ordering assertion
remains the mechanism that actually protects D6 -- ADR-019 changes what protects a user who never
registers (CI only, detective rather than preventive locally; filed as ADV-012, a git pre-push hook,
NOT adopted -- named scope belonging to FR-23's owner, per the coordinator's FYI, no action from this
document). **One open item this document surfaces but does not own:** `hld.md` SS 10's migration
runbook step 2 ("Verify the FR-23 replacement is reachable... This must pass before step 4") is
written against the pre-ADR-019 assumption that the push gate is reachable immediately after install.
It has not yet been updated to insert an explicit `register-mcp` step before that verification can be
attempted -- flagged by business-analyst-agent's review (`ba_review.json` FIND-10) as owned by
`solution-architect`, not fixed as of this revision. This does not block D5/D6 in this document's own
gate logic, but a user following the runbook as currently worded would attempt step 2 before its own
now-unstated prerequisite exists.

**4. Does this document's boundary depend on business-analyst-agent's FR-14 wording decision?**
**No -- already resolved, checked directly rather than assumed.** `docs/phase-2-validation/ba_review.json`
FIND-09 records business-analyst-agent chose to **amend** FR-14's text (not accept the one-step-install
miss silently): `prd-v2.md`'s FR-14 row and its Section 5 AC now state explicitly that one-step install
covers commands/agents/skills only, that MCP-backed capabilities require the separate `register-mcp`
step, and that this is a recorded, deliberate trade-off. This is APPLIED, not pending -- the only open
item on that document is a Section 8 sign-off unrelated to FR-14. This document's SS 4 update below is
written to match that already-applied wording rather than hedge against an unresolved outcome.

**Housekeeping correction, found while verifying the above (not requested, recorded for accuracy;
SUPERSEDED by SS 2d below -- the rationale here was incomplete, not just brief):** SS 2a's FR-18a
contingent row ("plugin-shipped cleanup command, IF business-analyst-agent selects this path over
AC-narrowing") did not activate. A separate, earlier business-analyst-agent pass (`prd-v2.md`
change-log entry "1.1, Phase 2.1 reconciliation") already resolved FR-18 via **AC-narrowing** (scoped
to plugin-attributable residue only) plus a **new FR-24** -- a documentation-only uninstall-residue
runbook (`docs/guides/uninstall-residue.md`), not an executable command, since no plugin-owned
execution point exists at uninstall time (the same structural gap ADR-012 found at install time).
FR-18a's WSJF row (6.50) is retired as not-activated; FR-24 is documentation-only and is not sized
here as new engineering scope. **This framed FR-18a as a road not taken. SS 2d, below, corrects that:
it was never a buildable road.**

---

## 2d. Phase 2.3 Correction -- FR-18a Invalidated, Not Merely Un-Activated (ADR-020 Path C)

`solution-architect` fully enumerated this document's Phase 2.2 findings against their own responses
(9/9 answered) and flagged this one as missed and requiring correction rather than acknowledgement:
FR-18a, as sized, describes a capability the architecture cannot deliver at all -- not a capability
BA declined to fund. The SS 2c housekeeping note above retired the row for the wrong reason.

**"9/9" reconciled against `docs/phase-2-validation/pm_review.json`'s `findings` array (CONFIRMED, not
left unverified):** that array holds exactly 9 entries. Mapped 1:1 against the coordinator's two
relay messages: #1 (deliverable-5 gate text) fixed directly by the orchestrator; #2, #4, #5, #7, #9
ACCEPTED outright; #3 (FR-23 CI enforcement) ACCEPTED, amended for the preventive/detective
disclosure; #8 (FR-14a retirement) ACCEPTED, with the ADR-012 attribution correction carried forward
as a follow-up on the same finding; #6 (FR-18's AC, which includes the FR-18a contingency) is the
finding this section corrects. That accounts for all 9 with no gap and no double-count, and also
identifies both "two had been missed" items the coordinator referenced without enumerating: FR-18a
(finding #6, this section) and the ADR-012 attribution (a follow-up on finding #8, corrected via the
`pm_review.json` edit and documented in SS 8's "Direct answers" block, item 3). This reconciliation is
this document's own cross-check, not an independently re-run gate.

**Same row, not a distinct one.** This is SS 2a's FR-18a ("plugin-shipped cleanup command," D5,
size 2, WSJF 6.50), previously retired once already in SS 2c as "not-activated." It is the identical
row resurfacing -- not a new finding about a new unit -- with a stronger and different reason
supplied than the one this document gave the first time.

**Why FR-18a cannot exist in the shape it was sized.** The measured residue it was sized to clean --
two `settings.json` bookkeeping keys (`enabledPlugins`, `extraKnownMarketplaces`) emptied to `{}` but
not removed, and an orphaned plugin-cache directory `claude plugin prune` does not clean -- comes into
being at the moment `claude plugin uninstall` completes, which is exactly when the plugin's own code
stops running. There is no plugin-side execution point after that instant: no uninstall-time hook, no
post-uninstall callback, nothing analogous to the install-time execution point ADR-012 already found
absent. This is structurally identical to HLD ADR-020's Path C finding: once the plugin is gone, no
plugin code runs, so **neither prevention nor detection is available to it**. "A plugin-shipped
cleanup command for post-uninstall residue" is not a capability that was deprioritized -- it names a
contradiction (code that runs after the thing that would run it no longer exists).

**Disposition: FOLD INTO FR-24. Not re-scoped as pre-uninstall preparation.** Two shapes were offered
by `solution-architect`; this document checks both against the actual measured residue rather than
picking one by default:
- **(a) Pre-uninstall preparation** -- a command run *while the plugin still exists*, reducing what
  uninstall will orphan. **Not adopted, because there is nothing left for it to do.** The plugin's
  only pre-uninstall-reachable state is its own MCP registrations, and `unregister-mcp` (SS 2c, sized
  at size 5 / WSJF 3.80 -- **PROPOSED by ADR-019, not built; zero lines of code exist**) is designed
  to reach those in full, once it exists. The remaining residue -- the two bookkeeping keys and the
  orphaned cache directory -- is written and owned entirely by Claude Code's own uninstall and caching
  machinery, not by anything the plugin created; no pre-uninstall action by the plugin changes what
  Claude Code itself does at uninstall time. Sizing FR-18a as (a) would size a command whose entire
  effective scope would duplicate `unregister-mcp`'s designed scope -- a second name for work already
  on the books, not new work.
- **(b) Fold into FR-24** -- **adopted.** FR-24 (`docs/guides/uninstall-residue.md`, **NAMED by
  business-analyst-agent at Phase 2.1 with a defined AC; status "Named at Phase 2.1; not started" per
  `prd-v2.md`; the file does not exist on disk, verified**) is the shape that would actually work,
  because a human would run it after the plugin is gone -- the only time the residue exists and the
  only actor left who could act on it. FR-18a's original intent (tell the user what residue exists and
  what to do about it) is fully subsumed by FR-24's already-defined, not-yet-built scope; nothing
  FR-18a was trying to add is missing from what FR-24 already specifies.

**Size: retired at zero, not carried at 6.50 or any other figure.** Per the reference implementation
(Reinertsen 2009, WSJF = CoD/size, via `product-management-core/SKILL.md`), a contingency that
resolves to no independent work has no CoD left to score -- the capability falls fully within FR-24's
already-defined-but-not-yet-built scope, and the only genuine pre-uninstall opportunity falls fully
within `unregister-mcp`'s already-defined-but-not-yet-built scope. This zero is a scoping conclusion
(no independent unit of work exists to size once FR-24 and `unregister-mcp` are built as designed),
not a claim that either is currently complete. FR-18a is struck from SS 2a's table (done above) rather
than carried
forward at 6.50 or re-priced at some smaller nonzero figure to seem conservative; an honest zero is
the correct number when the work is fully subsumed elsewhere, not a hedge.

---

## 3. FR-8a Disposition -- Correctness-vs-Enhancement and Cost of Delay (Kano rejected, see SS 0)

FR-8a's own text (`prd-v2.md` SS 4) already separates two different things this document keeps
separate: **deciding** the disposition of each of the 7 dead Stop-hook script references and the 3
broken maintenance policies (rebuild or retire, per capability), versus **building** whichever of
those the decision lands on "rebuild." Resolution 2 (`orchestration_prompt.md` SS 3.3) mandates the
DECISION as in-scope now -- "decide per capability whether it is still wanted, then either rebuild
it or formally delete the reference" -- and explicitly names "delete the reference" as one of the
two valid end states per capability, not a fallback. The user's "repair what it should do" framing
is therefore satisfied by either outcome for any given capability; it does not mandate
rebuild-everything, and this document does not read it that way.

**Grounds for a v2.0.0 / v2.1 split (gate dependency and cost of delay, not a satisfaction category):**

1. **Gate dependency.** No FR, AC, or D1-D7 gate in `prd-v2.md` section 9 requires any of the 5
   candidate rebuilds (auto-save-session, archive-old-sessions, plan-session-archiver,
   preference-auto-tracker, common-failures-prevention) to exist before D6 closes. D6's own gate
   criterion is "NFR-1 measured and met," scoped to PreToolUse/PostToolUse -- not the Stop hook,
   which ADR-010 confirms the plugin never owns.
2. **FR-8a's own acceptance criterion penalises rebuilding, not just tolerates deferring it.** Its
   measurable AC (`prd-v2.md` SS 5) requires the reduced design's regression test to assert a
   per-turn spawn count of <= 2 "unless a named exception is documented with a rationale." Every
   capability rebuilt that adds a subprocess spawn must individually clear that bar -- rebuilding is
   a cost this FR was written to constrain, not a free win.
3. **Revealed usage evidence, not an inferred category.** The 7 dead references have failed
   silently, with zero logged trace and zero recorded complaint, for an unmeasured but evidently
   non-trivial period (FR-21, `prd-v2.md` SS 4). That is a direct observation of realised impact --
   nobody built a workaround, nobody filed an issue -- not a guess about how a population would
   answer a questionnaire it was never given.
4. **Cost of delay is low; job size is comparatively large.** Nothing downstream depends on these 5
   capabilities, so deferring them costs nothing measurable against NFR-1, the project's stated
   single primary success metric. Rebuilding all 5, in aggregate, is a comparatively large job (5
   independent design-build-test cycles) against that near-zero cost of delay -- the same CoD/size
   logic as SS 2's WSJF table, without a formal row here because the rebuild scope is not yet defined
   pending the decision session (item 5).
5. **The decision does not defer -- only the build does.** The instrumentation script, the
   per-capability decision with rationale, and reference retirement for every capability decided
   "not rebuilt" all ship in v2.0.0. This is cheap and is exactly what FR-8a's AC requires to pass
   (see the recomputed WSJF unit in SS 2, "FR-8a decision + instrumentation + retire").

**Conclusion: the deferral survives, narrowed.** v2.0.0 ships the FR-8a decision process, the
instrumentation, and reference retirement for every capability not selected for rebuild. Any
capability the decision session lands on "rebuild" defaults to v2.1 unless that session
independently surfaces a blocking reason -- none is currently known for any of the 5. This is a
conditional default set by dependency and cost-of-delay evidence, not a unilateral override of the
user's per-capability process; decision authority for which capabilities to rebuild stays with that
session, not with this document.

---

## 4. MVP Boundary

### Ships in v2.0.0

- D1 Policy audit (already done/approved)
- D2 FR-6 ADR-006 doc
- D3 FR-9 KG rebuild + validation
- D4 FR-9a CallGraph scope-aware fix (prerequisite) + FR-10..FR-13 KG-driven selector
- D5 FR-14a spike (**DONE 2026-08-01**, SS 0a item 5) + FR-14 plugin skeleton + FR-15/FR-16/FR-17
  remediation + FR-18/NFR-5 lifecycle tests (FR-18 resolved via AC-narrowing to plugin-attributable
  residue; FR-24, a documentation-only uninstall runbook, added alongside it -- SS 2c housekeeping
  note) **+ ADR-019's `register-mcp`/`unregister-mcp` command pair (NEW, SS 2c, size 5, WSJF 3.80) --
  now mandatory v2.0.0 scope, not optional, because under the decided option (a) it is the only path
  to any MCP-backed capability.** **Explicit line item this revision adds (previously implicit and
  silently at risk, per SS 2c item 1): one-step install covers commands, agents, and skills only.**
  MCP-backed capabilities (the FR-23 push gate, the progress writer) require the separate,
  explicit `register-mcp` step -- no hand-edited `settings.json`, so "no manual surgery" still holds
  in full, but "one step" no longer covers the complete capability set. This is a deliberate,
  disclosed trade-off (HLD ADR-019 "what is lost"; `prd-v2.md` FR-14 amended accordingly,
  `ba_review.json` FIND-09, APPLIED) not a silent regression. Deliverable-5's gate text in the
  canonical source was corrected directly by the orchestrator (no action needed from this document).
- D6 FR-23 (MCP port, sequenced before FR-4; CI-side ordering per ADR-017 is the mechanical
  protection regardless of whether a given user ever runs `register-mcp` -- SS 2c item 3) + FR-4/FR-5
  hook deletion (re-scored, SS 2a; the "necessary but not sufficient for NFR-1" caveat is now resolved
  favourably under ADR-019 at zero extra cost, SS 2c) + FR-7
  slash commands + NFR-1 measurement harness (re-scored, SS 2a) + NFR-2 timeout-removal engineering
  (re-scored and materially larger than the Phase 0 draft assumed, SS 2a) + NFR-3 CheckpointManager
  contract + durability fixes (re-scored and materially smaller, SS 2a) + FR-22 SRS append +
  **FR-8a's
  decision process and instrumentation, plus reference retirement for every capability the decision
  session does not select for rebuild** (the 7 dangling `.exists()` references in
  `hooks/stop_notifier/core.py` and the 3 broken maintenance policies) -- see SS 3 for the full
  reasoning and the conditional rebuild deferral
- D7 Migration guide + CHANGELOG + VERSION bump to 2.0.0

### Defers to v2.1

| Item | Justification against NFR-1 / gate dependency / cost of delay |
|---|---|
| FR-8a: **rebuilding** (not retiring) any of the 5 dead Stop-hook capabilities (auto-save-session, archive-old-sessions, plan-session-archiver, preference-auto-tracker, common-failures-prevention) that the v2.0.0 decision session selects for rebuild | See SS 3 in full. Summary: no D1-D7 gate requires these; Stop/Notification hooks are explicitly non-plugin-owned (ADR-010) and outside the NFR-1 idle-process measurement; FR-8a's own AC penalises added spawns from a rebuild unless individually justified; 7 references have failed silently with zero recorded complaint (revealed low usage, not an inferred category); cost of delay is near-zero since nothing downstream depends on them. The DECISION for each capability, and retirement of every one not selected, still ships in v2.0.0 -- only a selected rebuild's build work defers. |
| Rebuild (not retirement) of session-memory / session-pruning / git-auto-commit maintenance policies (folded into FR-8a per Resolution 2) | Same SS 3 reasoning -- Stop-hook-adjacent, non-plugin-owned, no gate dependency. Retirement of the broken reference, which closes the correctness defect, ships now regardless. |
| FR-19 `get_policies_dir()` four-branch resolver | Blocked on the ADR-009b five-policy human sign-off (`prd-v2.md` SS 8), which has no target date. It has zero effect on NFR-1 (idle-process count) or on the D1-D7 gate chain -- it is a policy-corpus canonicalisation concern with no runtime-overhead dimension. Cannot ship in v2.0.0 if sign-off does not land in time; not worth blocking the release for. |
| Residual FR-20 orphan-disposition polish beyond what D1's approved audit already recorded | Low stakes, audit-adjacent; if the approved audit already populated the "Post-plugin plan" column for all 14 orphans this is a non-issue, and if not, it is a documentation-only gap with no NFR-1 impact. |
| ADR-008 marketplace listing polish beyond bare install/uninstall mechanics | No gate in section 9 requires more than bare install/uninstall mechanics; those are already in FR-14/NFR-5's in-scope work. Polish beyond that has no named dependent and no cost-of-delay driver. |

---

## 5. NFR Ownership Map (Phase 2.2 update -- NFR-1/NFR-2/NFR-3 measurement methods and owners re-derived)

| NFR | Owner | Measurement method |
|---|---|---|
| NFR-1 (zero overhead when idle) | Workstream B (hook-removal engineer) | **Process-count based, never timing-based, per-component attributed.** OS-level process-list count taken immediately before and after 10 tool calls in a fresh session with the plugin installed but not invoked; pass = delta of 0 processes attributable to **the plugin** (its command entry points -- **no `.mcp.json` servers to count, SS 2c**). Per HLD SS 9, **exactly one exclusion is permitted**: the retained user-level Stop/Notification hooks (`hooks/stop_notifier/`, 17 spawn sites, fires every response turn by ADR-010's own deliberate "keep" decision) -- a window spanning a turn boundary otherwise records a non-zero delta from a component this design was never asked to remove. **No exclusion for MCP-attributable processes** (ADR-019). **DECIDED 2026-08-01 (SS 2c): option (a), zero bundled MCP servers.** Closure no longer waits on a packaging decision -- ADR-019 makes NFR-1 achievable by construction (nothing bundled to spawn) rather than by redefinition, and the metric stays falsifiable: any future component that spawns without invocation still fails this test. |
| NFR-2 (no fixed per-call timeout) | Workstream B | Static scan for `timeout=`, `signal.alarm`, and subprocess `timeout` kwargs across bundled plugin code **and the engine pipeline path** (not just the two deleted hooks); pass = zero unconditional matches, any surviving timeout is configurable and default unbounded/user-overridable. **Re-scoped (SS 2a):** ADR-016 names 6 application sites across 5 engine-side files, including a 75-second wall-clock abort on the Step 1 pipeline path -- none of these are touched by hook deletion, so this is a build (5 non-temporal control mechanisms), not a scan-and-confirm. |
| NFR-3 (crash recovery after de-hooking) | Workstream B, owning `langgraph_engine/checkpoint_manager.py::CheckpointManager` -- **an existing component, not a new one to be designed** (HLD OAQ 1, ADR-011) | Kill-the-process-mid-pipeline test against `CheckpointManager`'s existing output, triggered at `core/step_decorator.py` step boundaries. Second test covers the per-tool-call progress replacement via `mcp-post-tool-tracker`, wired as a **projection of the checkpoint record**, not a second writer (avoids the dual-write defect ADR-011 flags). **Re-scoped (SS 2a):** MET in principle already; remaining work is 3 named durability defects (swallowed save failure, dual-write risk, non-idempotent replay), not a new writer. |
| NFR-4 (no silent regression) | Workstream A (policy-audit owner) | Script cross-checks all 27 `capability_loss.md` names against the audit matrix; fails if any is missing a disposition or carries an empty/"disappeared" value. **COUNT CORRECTED 2026-08-02 (owner ruling), was 25:** the ledger's three tables hold 16 + 9 + 2 = 27 data rows, the PreToolUse table being **16 PreToolUse components (14 policy gates plus the daemon and registry mechanism)**. The 25 figure counted only the 14 policy gates and dropped the `daemon.py` (NFR-1) and `registry.py` (FR-9) rows. Otherwise unchanged from Phase 0. |
| NFR-5 (install/invoke/uninstall each tested) | Workstream D (plugin packaging) | 3 automated Gherkin-backed tests (`prd-v2.md` SS 7): install leaves zero overhead + no PreToolUse/PostToolUse/UserPromptSubmit entries; invoke reaches all 27 capabilities with a decided disposition and full selector explainability; uninstall test **now depends on business-analyst-agent's FR-18 AC rewrite (SS 0a item 4)** -- the Phase 0 wording ("no orphaned settings.json or plugin-cache state") is measured-false against `claude plugin uninstall`'s own behaviour and cannot be tested as originally written. FR-14a is no longer a gating unknown -- **DONE, all 5 items measured 2026-08-01.** |

---

## 6. New Critical Path (Phase 2.3 update -- ADR-019 decided)

With D1 done, FR-14a's spike DONE, and the NFR-1/MCP-bundling question DECIDED (SS 2c), the critical
path through the remaining 6 gates is:

```
D2 (FR-6, trivial) -> D3 (FR-9, trivial, Workstream C)
   -> D4: FR-9a (scope-aware CallGraph fix, ADR-013 design RESOLVED) --PREREQUISITE--> FR-10..FR-13 (selector)
   -> D5: FR-14 plugin skeleton (designed to ship no .mcp.json -- ADR-019)
        --PREREQUISITE--> ADR-019 register-mcp/unregister-mcp command pair (PROPOSED, not built;
        NEW WSJF row, SS 2c, size 5)
        --PREREQUISITE--> NFR-5's 4th round-trip test scenario --> FR-15/16/17/18 close out D5
   -> D6: FR-23 (MCP port) --MUST PRECEDE, DESIGNED TO BE CI-ENFORCED (ADR-017 -- itself a PROPOSED
        CI assertion, not yet wired) INDEPENDENT OF register-mcp, once built-->
        FR-4/FR-5 (deletion) + FR-7 + NFR-1(harness, achievable-by-construction under ADR-019) +
        NFR-2(re-scoped, larger) + NFR-3(re-scoped, smaller) + FR-22 + FR-21(minimal)
   -> D7: migration guide / CHANGELOG / VERSION bump (still needs the register-mcp step inserted
        into hld.md SS 10's runbook step 2 -- flagged by ba_review.json FIND-10, owned by
        solution-architect, NOT YET fixed as of this revision)
```

**The single riskiest link remains FR-9a -> FR-10**, unchanged by this amendment. HLD OAQ 4 resolves
it as a four-phase coverage-complete discovery (ADR-013) with a concrete, independently-re-walked
regression test (`test_discovery_covers_every_package`) and identifies **four** truncation points
(not the one Phase 0 named) that must each reach a recorded end state. The risk is "the design, as
specified, is not yet built," not "no design exists" -- but not zero, because sites #2 and #4
(`call_graph_builder_legacy.py`, `code-graph-analyzer.py` hyphenated duplicate) are easy to leave
unfixed by looking unused.

**Second-riskiest link, unchanged in rank, sharpened by ADR-019: FR-23's MUST-PRECEDE-FR-4 constraint
is designed to protect a WEAKER local guarantee than before.** HLD ADR-017 names the CI mechanism
(replacement-reachability, not hook-presence); this remains specified but not yet merged as of this
revision (`orchestration_prompt.md` SS 1.2 Consequence 2a names the owners) -- **as of today, neither
the local command nor the CI assertion exists, so neither preventive nor detective protection is
actually in place yet; both are proposed.** **What changed in the design:** before ADR-019, the push
gate would have shipped as a bundled server, reachable on every machine that installed the plugin.
Under the ADR-019 design, once `register-mcp` exists, a user who never runs it would have no local
MCP-side gate at all -- CI enforcement is designed to be the *only* mechanical protection once ADR-017's
assertion is merged, and the guarantee is designed to move from **preventive** (blocked at push time,
if bundled) to **detective** (caught in CI, after the fact). A git `pre-push` hook was proposed to
restore local prevention and filed as ADV-012, **not adopted** -- named scope belonging to FR-23's
owner, not this document's to size or push into v2.0.0 unasked.

**FR-14a and the SS 2b options question are both RETIRED as open risks** (SS 0a item 5; SS 2c) --
FR-14a fully measured; the NFR-1/MCP question decided (option (a), ADR-019). Neither belongs in this
section's risk framing any longer.

**New dependency, replacing the retired Phase 2.2 placeholder:** the ADR-019 `register-mcp`/
`unregister-mcp` command pair is a new internal D5 prerequisite (SS 2c item 3) -- FR-14's plugin
skeleton must exist before it can be built, and NFR-5's 4th round-trip scenario cannot be written
until it exists. This does **not** block D6's actual gate (CI-side ordering is independent of it),
but it does block D5's own close-out and, separately, `hld.md` SS 10's migration runbook is not yet
updated to describe it as a required step -- both are named explicitly here rather than left implicit.

---

## 7. Top-3 Sequencing Risks (Phase 2.3 re-derivation -- FR-14a and the SS 2b options question both retired)

| # | Risk | Trigger |
|---|---|---|
| 1 | FR-9a's scope-aware fix (ADR-013, now designed) closes the four named truncation points without being exhaustive in implementation, so FR-10 ships against inputs that are provably-better-but-still-incomplete -- reproducing the "worthless inputs" failure mode Resolution 1 was written to prevent. Unchanged ranking since Phase 2.2; unaffected by ADR-019. | `test_discovery_covers_every_package`'s general assertions (1-4) pass, but sites #2/#4 (the legacy and hyphenated-duplicate builders) are left unmigrated because they "look unused," and a caller of one of them is missed. |
| 2 | FR-23's MUST-PRECEDE-FR-4 constraint is specified (ADR-017) but not yet wired into CI, and a PR deleting `hooks/pre_tool_enforcer/` merges before the MCP port lands -- silently reopening the version-push bypass commit `1bb4303` closed, with no test failure to catch it (`tests/test_push_gate.py` still covers only the hook path as of this revision). **Sharpened by ADR-019 (SS 2c/SS 6):** once both are built, this CI assertion is designed to be the ONLY mechanical protection for a user who never runs `register-mcp` -- the guarantee is designed to move from preventive to detective. Today, neither the CI assertion nor `register-mcp` exists, so neither form of protection is actually in place yet. A `pre-push`-hook mitigation was named (ADV-012, proposed) but not adopted; that is FR-23's owner's call, not re-scoped here. | The replacement-reachability CI assertion named in ADR-017 and `orchestration_prompt.md` SS 1.2 Consequence 2a is not actually merged before FR-4 work starts. |
| 3 | **REPLACES the retired Phase 2.2 placeholder (the SS 2b options question is now DECIDED, not a risk).** `hld.md` SS 10's migration runbook step 2 ("Verify the FR-23 replacement is reachable... This must pass before step 4") is written against the pre-ADR-019 assumption that the push gate is reachable immediately after install, and has not yet been updated to insert the now-required `register-mcp` step (`ba_review.json` FIND-10, flagged not fixed, owned by `solution-architect`). A user following the runbook as currently worded could attempt step 2 before its own unstated prerequisite exists. | The runbook is used as written before `solution-architect` inserts the missing step, and the user is unable to verify FR-23's replacement because they have not yet been told to run `register-mcp`. |

**Fourth risk noted but not ranked in the top 3 (per FR-19's explicit exclusion from this critical
path, SS 0 / SS 4):** the ADR-009b five-policy sign-off has no committed date. If it lands very late,
FR-19 slips past v2.0.0 entirely (already reflected as a v2.1 deferral in SS 4) -- this is a schedule
risk to a deferred item, not a v2.0.0 ship risk, so it is called out here rather than displacing one
of the three risks above.

**Fifth item, tracked but not ranked:** FR-18's AC was unsatisfiable as written against measured
platform behaviour (SS 0a item 4) -- **RESOLVED** by a separate business-analyst-agent pass via
AC-narrowing plus the new documentation-only FR-24 (SS 2c housekeeping note). No longer an open item.

---

## 8. Return Value Summary (Phase 2.3 revision -- ADR-019 decided)

**Re-derived WSJF top-5 (in order, supersedes the Phase 0 top-5 in SS 2; unchanged by ADR-019 --
the new `register-mcp` row does not enter the top-5):** (1) FR-22 SRS append -- 13.00; (2) FR-6
ADR-006 doc -- 12.00; (3) NFR-1 measurement harness -- 10.50; (4) FR-23 push_gate MCP port -- 7.67;
(5) FR-4/FR-5 hook deletion -- 6.67. Reference implementation unchanged: Reinertsen (2009)
WSJF = CoD/size via `skills/product-management-core/SKILL.md` SS M1 -- proof cited, not re-derived.

**What Phase 1 (the APPROVED HLD) invalidated, re-scored (SS 0a/SS 2a):**
- **NFR-3**: false premise (replacement writer assumed built from scratch; `CheckpointManager`
  already exists and is already wired). Size 8 -> 3, WSJF 3.00 -> 6.33.
- **NFR-2**: under-scoped by being bundled with NFR-1's harness. ADR-016 found 6 real `timeout=`
  sites across 5 engine files, including a 75-second pipeline-path abort. Split out: size 8, WSJF 2.88.
- **NFR-1**: measurement work, once split from NFR-2, is genuinely small: size 2, WSJF 10.50.
- **FR-4/FR-5**: "core NFR-1 outcome" framing corrected -- ~6 of 116 spawn sites removed (~5%), value
  is invocation-frequency not footprint. UBV 9 -> 8, CoD 21 -> 20, WSJF 7.00 -> 6.67.
- **FR-14a**: RESOLVED, all 5 items measured; retired from the active WSJF table.

**What Phase 2.3 (ADR-019, the decided NFR-1/MCP-bundling question) changed, on top of the above
(SS 2c in full):**
- **The SS 2b options question is DECIDED, not sized-and-pending.** `solution-architect` chose option
  (a): the plugin bundles zero MCP servers; `register-mcp`/`unregister-mcp` is the sole opt-in path.
  The sizing in SS 2b was used correctly, as cost data, not as the decision criterion -- a
  measurement-falsifiability argument outside WSJF's own instrument decided it, and this document
  accepts that reasoning without dispute (SS 2c).
- **NEW WSJF row:** ADR-019 `register-mcp`/`unregister-mcp` command pair, D5, size 5, **WSJF 3.80**
  (mid-table; does not enter the top-5).
- **FR-4/FR-5's "necessary but not sufficient for NFR-1" caveat is now resolved favourably**, at zero
  additional engineering cost -- hook deletion plus shipping nothing together make NFR-1 achievable
  by construction. The row's own CoD/size is unchanged; only the external context improved.
- **Housekeeping, found while verifying FR-14's dependency (not requested, recorded for accuracy;
  CORRECTED below, not merely restated):** FR-18's AC was resolved by a separate, earlier
  business-analyst-agent pass via AC-narrowing plus a new documentation-only FR-24 (uninstall
  runbook) -- **not** the FR-18a cleanup-command contingency this document had sized.
- **FR-18a INVALIDATED (SS 2d, `solution-architect` finding, not a scoring correction):** a
  plugin-shipped cleanup command cannot execute after the plugin is uninstalled -- exactly when the
  measured residue exists (structurally identical to HLD ADR-020's Path C: no plugin code runs once
  the plugin is gone, so neither prevention nor detection is available to it). This is the same row
  this document retired once already as "not-activated" -- that framing was incomplete; the row was
  never buildable as scoped, independent of any BA choice. **Disposition: folds into FR-24** (the
  shape that would actually work, since a human would run it after the fact -- FR-24 is NAMED with a
  defined AC, not built; the runbook file does not exist on disk); pre-uninstall preparation was
  checked and not adopted, because `unregister-mcp` (SS 2c -- **PROPOSED by ADR-019, not built**) is
  designed to cover the only genuine pre-uninstall opportunity (the plugin's own MCP registrations),
  once it exists, and the remaining residue is Claude-Code-owned, reachable by no plugin-side action
  at any time. **Size: retired at zero**, not carried at 6.50 -- an honest zero (no independent unit
  of work remains to size once FR-24 and `unregister-mcp` are built as designed), not a hedge, and not
  a claim that either already exists.

**Rework note (carried from the prior revision, unchanged):** the earlier draft cited
`skills/product-management-core/SKILL.md` SS 13's Kano warning as if it licensed an unsurveyed
classification -- it is a prohibition, not a licence. Kano has been removed and the FR-8a v2.1
deferral re-derived in SS 3 on gate dependency, FR-8a's own AC, revealed usage evidence, and cost of
delay. **The deferral survives, narrowed**, and is unaffected by this revision's re-scoring.

**MVP boundary -- does NOT move to v2.1. What moves is composition, and one previously-implicit
property is now an explicit, consciously-traded-away line item (SS 2c item 1):**
- **Ships:** D1(done), D2 FR-6, D3 FR-9, D4 FR-9a+FR-10..13, D5 FR-14a(done)+FR-14+FR-15+FR-16+FR-17+FR-18/NFR-5(resolved via AC-narrowing)+FR-24(documentation-only)+**ADR-019 register-mcp/unregister-mcp (NEW, mandatory)**, D6 FR-23+FR-4+FR-5+FR-7+NFR-1(achievable by construction)+NFR-2(larger than modeled)+NFR-3(smaller than modeled)+FR-22+FR-8a(decision+instrumentation+retire-if-not-rebuilt, SS 3), D7 migration/CHANGELOG/VERSION(+register-mcp step still needed in hld.md SS 10, not yet inserted).
- **Explicit line item this revision adds:** one-step install now covers commands/agents/skills only;
  MCP-backed capabilities require the separate `register-mcp` step. This was previously carried
  silently inside FR-14's wording and D5's gate text; it is named here so it cannot fail silently a
  second time. `prd-v2.md`'s FR-14 row/AC were already amended by business-analyst-agent to match
  (`ba_review.json` FIND-09, APPLIED) -- this document's boundary does not depend on that decision
  landing differently, because it already landed.
- **Defers to v2.1:** any FR-8a capability the v2.0.0 decision session selects for **rebuild** (of the 5 candidates; none currently known to be blocking), FR-19 (blocked on ADR-009b sign-off, no NFR-1 impact), residual FR-20 polish, ADR-008 marketplace polish beyond bare mechanics. Unchanged from Phase 0.

**NFR ownership (compact, re-derived):** NFR-1 -> Workstream B, process-count delta=0 attributed
per-component, achievable by construction under ADR-019 (no bundled `.mcp.json` to spawn). NFR-2 ->
Workstream B, 5 non-temporal control mechanisms across 6 sites/5 files (build, not scan). NFR-3 ->
Workstream B, existing `CheckpointManager` contract + 3 durability fixes (not a new writer; unaffected
by ADR-019, HLD cross-NFR check confirmed). NFR-4 -> Workstream A, 27-capability disposition
cross-check (count corrected 2026-08-02, was 25). NFR-5 -> Workstream D, 3 Gherkin-backed lifecycle tests plus a 4th
register/unregister round-trip scenario (ADR-019); FR-14a gate satisfied (DONE); uninstall test
resolved via FR-18's AC-narrowing.

**New critical path:** D2 -> D3 -> D4(FR-9a PREREQUISITE FR-10..13, design-resolved via ADR-013) ->
D5(FR-14a DONE; FR-14 plugin skeleton --PREREQUISITE--> ADR-019 register-mcp/unregister-mcp build
--PREREQUISITE--> NFR-5's 4th round-trip scenario) -> D6(FR-23 PRECEDES FR-4/5, CI-enforced via
ADR-017 independent of register-mcp -- plus FR-7/NFR-1(achievable-by-construction)/NFR-2(larger)/
NFR-3(smaller)/FR-22/FR-21-minimal) -> D7(migration guide still needs a register-mcp step inserted
into `hld.md` SS 10, flagged not fixed). Deliverable 1's audit remains not the bottleneck. FR-9a ->
FR-10 remains the single riskiest link; FR-23's designed-to-be-CI-enforced-but-then-detective-only
ordering (both the CI assertion and `register-mcp` remain unbuilt today) is the second; the
migration-runbook gap left by ADR-019 (SS 10 step 2, not yet updated) is the third, replacing the
now-decided SS 2b options question.

**Top-3 risks (re-derived):** (1) FR-9a's now-designed fix (ADR-013) is built incompletely against its
four named truncation points, reproducing the worthless-input failure FR-10 depends on it to prevent.
(2) FR-23's MUST-PRECEDE-FR-4 CI assertion is specified (ADR-017) but not yet merged; ADR-019 also
is designed to weaken the *local* guarantee from preventive to detective for a user who never runs
`register-mcp`, once `register-mcp` exists (ADV-012's pre-push-hook mitigation named, not adopted).
(3) `hld.md` SS 10's migration runbook has not yet been updated to insert the `register-mcp` step
ADR-019 requires before its own step 2 can be
attempted (`ba_review.json` FIND-10, owned by `solution-architect`, not fixed as of this revision).
FR-14a and the SS 2b options question, Phase 2.2's #2 and #3, are both retired -- fully resolved.

**Direct answers to the coordinator's four questions:**
1. **MVP boundary under option (a): does NOT move to v2.1.** Composition changed (register-mcp is
   new mandatory v2.0.0 scope); one implicit property (one-step install of everything) is now an
   explicit, consciously-traded-away line item rather than a silent assumption.
2. **Size of ADR-019's `register-mcp` work: size 5, WSJF 3.80** (CoD 19 = UBV 7 + TC 6 + RROE 6),
   gated inside D5, mid-table, does not enter the WSJF top-5.
3. **Critical path moves:** one new internal D5 dependency (FR-14 -> register-mcp/unregister-mcp ->
   NFR-5's 4th test); D6's own gate is unaffected since CI enforcement (ADR-017) does not depend on
   register-mcp. FR-9a -> FR-10 remains the single riskiest link overall.
4. **Dependency on BA's FR-14 decision: none remaining.** Already resolved -- business-analyst-agent
   chose to amend FR-14's wording (not accept the miss silently), applied in `prd-v2.md` and recorded
   in `ba_review.json` FIND-09. This document's boundary is written to match the applied wording.

**Direct answers to the coordinator's third round (FR-18a invalidation + ADR-012 attribution, SS 2d):**
1. **FR-18a disposition: folds into FR-24, size retired at zero.** Not re-scoped as pre-uninstall
   preparation (a) -- `unregister-mcp` (**PROPOSED by ADR-019, not built**) is designed to cover the
   only genuine pre-uninstall opportunity (the plugin's own MCP registrations), once it exists, and the
   remaining measured residue (two `settings.json` bookkeeping keys, the orphaned cache directory) is
   Claude-Code-owned and unreachable by any plugin-side action at any time, before or after uninstall.
   FR-24's already-defined, not-yet-built documentation-only scope is designed to deliver FR-18a's
   original intent in full once written.
2. **Same row, not a distinct one.** This is SS 2a's FR-18a, previously retired once in SS 2c as
   "not-activated." That framing was incomplete, not wrong in outcome (the row is retired either way)
   but wrong in reasoning (it implied a road not taken rather than a road that was never buildable).
   SS 2d corrects the reasoning; the disposition (retired, no WSJF contribution) is unchanged.
3. **ADR-012 attribution confirmed and corrected where found.** This document's own SS 0a item 5 text
   was already correctly attributed (unblocked by FR-14a item 2's measurement -- `CLAUDE_PLUGIN_ROOT`
   present in `os.environ` -- with ADR-012's ascent as defence-in-depth, not the unblocking mechanism).
   One incorrect instance was found and fixed: `docs/phase-2-validation/pm_review.json`'s ADVISORY
   finding on FR-14a credited "ADR-009a branch 2 is unblocked via ADR-012's manifest-anchored ascent,
   independent of the spike's answer" -- corrected to credit the measurement, with ADR-012 named
   explicitly as defence-in-depth (would have unblocked branch 2 had the env var been absent; is not
   what actually did).

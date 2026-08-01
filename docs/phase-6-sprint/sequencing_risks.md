# v2.0.0 Sequencing Risks -- Orderings That Are Correctness Constraints

**Phase:** 6 (sprint planning)
**Author:** scrum-master-agent
**Date:** 2026-08-01
**Companion documents:** `sprint_plan.md`, `github_issues.json` (37 drafts, none created on GitHub)

---

## How to read this document

Each entry states an ordering, what breaks if it is violated, and how the violation would be
detected -- or, where it would not be detected, says so. A constraint whose violation produces no
failing test is more dangerous than one that does, and those are marked.

**Severity vocabulary:**

- **CORRECTNESS-CRITICAL** -- violating the order produces work that looks complete and is wrong, or
  removes a live protection. Four of these were named in the planning brief; this pass confirms all
  four and adds three more.
- **SCOPE-CRITICAL** -- violating the order causes work to be sized, started or closed against a
  figure or an artifact that does not hold.
- **HYGIENE** -- a real defect with a bounded, visible consequence.

**Build-status vocabulary used throughout:** where a component is described as DESIGNED, NOT BUILT,
that label is carried at every mention, not just the first.

---

## R-1. The push gate: PRD FR-4 must not land before BOTH `register-mcp` AND the ADR-017 CI assertion

**Severity: CORRECTNESS-CRITICAL. This is the single most dangerous ordering in the plan.**

**Constraint:** V2-027 (PRD FR-4 / SRS FR-13, delete PreToolUse and PostToolUse) is blocked by
V2-016 (`register-mcp` / `unregister-mcp`), V2-024 (PRD FR-23, push gate ported to an MCP tool) and
V2-025 (ADR-017 CI assertion). All three, not any one.

**Current state, stated precisely:**

- The push gate is protected **today** only because PRD FR-4 has not run and the live PreToolUse hook
  still fires. `hooks/pre_tool_enforcer/policies/push_gate.py` exists on disk (verified 2026-08-01),
  covered by `tests/test_push_gate.py` (verified 2026-08-01).
- **`register-mcp` is DESIGNED, NOT BUILT.** `hld_v2.md:759` states verbatim that it "does not exist
  yet". `unregister-mcp` is described at `hld_v2.md:738` as "is designed to read and write"
  `settings.json`, a wording downgrade that file's own change log records at line 1934.
- **The ADR-017 CI assertion is DESIGNED, NOT BUILT.** Its formal signature exists at `hld_v2.md`
  section 7.7 as `assert_push_gate_reachable()`. Recorded as correction #17 in
  `docs/REVIEW-INDEX.md` section 7 -- it had previously been documented as an active governance
  guarantee when it does not exist.
- **ADV-012** (a git `pre-push` hook that would restore local preventive protection) is NAMED, NOT
  ADOPTED.

**What breaks if violated:** after FR-4, with neither replacement built, the version-push gate has
**no preventive cover and no detective cover**. Commit `1bb4303` was deliberate governance work
closing a version-push bypass. Deleting `hooks/pre_tool_enforcer/` before the replacement lands
reopens that bypass.

**How the violation would be detected: it would NOT be.** `tests/test_push_gate.py` currently covers
only the hook path. Delete the hook and the test either fails loudly (best case, and only if it is
not deleted alongside the hook) or is removed with the package it tests (likely case, and silent).
The CI assertion that would catch it is the very thing that does not exist. **This is a constraint
with no mechanical enforcement until V2-025 lands, which means it is enforced by this document and by
review, and by nothing else.**

**Degradation even when honoured.** Once both are built, ADR-019 has changed what protection means
for a user who never runs `register-mcp`: `hld_v2.md:683` records the guarantee moving from
**PREVENTIVE to DETECTIVE**. The bad push is caught in CI, after the fact, not blocked at push time.
Restoring local prevention is exactly what ADV-012 proposes and it is not adopted. **This is a
consciously accepted reduction in guarantee strength, not an oversight -- but it should be accepted
knowingly.**

**Ordering in the plan:** V2-016 -> V2-024 -> V2-025 -> V2-027. Batch F must close in full before
batch G opens.

---

## R-2. PRD FR-9a must land before PRD FR-10

**Severity: CORRECTNESS-CRITICAL.**

**Constraint:** V2-011 (PRD FR-10 / SRS FR-22, the KG-driven selector) is blocked by V2-009 (PRD
FR-9a / SRS FR-21, call-graph discovery).

**What breaks if violated:** the selector consumes call-graph risk signals from a builder whose
binding cap stops discovery at 300 of 411 Python files -- 111 files, 27 percent of the codebase,
invisible (`hld_v2.md:1598-1604`, MEASURED). Building the selector first makes FR-10 "done" against
inputs that are provably worthless for exactly the code that matters most.

**How the violation would be detected:** FR-10's own acceptance criterion partially catches it. It
requires each of 10 sample task descriptions to return a ranked agent set with a non-empty KG edge
path "verified against `docs/phase-0-reverse-engineering/ast_call_graph.json` or a rebuilt
(FR-9a-fixed) call graph, **never the current truncated builder**". That clause is the guard. It is
a review-enforced clause, not an automated one -- nothing in the AC mechanically distinguishes a
fixed builder's output from a truncated one at the point the selector reads it.

---

## R-3. PRD FR-9a and PRD FR-9b are one deliverable, not two sequenced ones

**Severity: CORRECTNESS-CRITICAL.**

**Constraint:** V2-010 (PRD FR-9b / SRS FR-38, resolver) is blocked by V2-009 (PRD FR-9a, discovery),
and **batch C does not open until both have landed**.

**What breaks if violated:** FR-9a fixes call-graph **discovery** (which files are seen). FR-9b fixes
call-graph **resolution** (what an edge points at once a file is seen). Shipping FR-9a alone yields a
**larger** graph feeding the same broken resolver -- more files, the same wrong `hot_nodes` and
`danger_zones`, and a **higher collided in-degree on the same wrong nodes**. The result is not
"partially improved"; it is worse-looking-better.

The defect is at `langgraph_engine/parsers/graph_model.py:265`, verified on disk by this pass
2026-08-01: the line reads `return candidates[0]`, the third of three returns inside
`_resolve_target()`, reached when a bare simple method name matches multiple FQNs and none is in the
caller's file. MEASURED consequences (by two independent agents, not re-derived here):

| Collision | Inflated target | Measured in-degree |
|---|---|---|
| `list.append()` | `JsonlAppender.append` | 1,592 |
| `str.format()` | `ErrorMessages.format` | 755 to 756 (two agents measured 755 and 756; reported as a range, not adjudicated) |
| `dict.get()` / `dict.set()` | `_MemoryLayer.get` / `_MemoryLayer.set` | not separately reported |

55.5 percent of cross-file "resolved" edges are collision artifacts. Of 26,114 total: 18,608
unresolved + 2,853 builtin-collision + 433 cross-file ambiguity = 21,894, leaving 4,220
high-confidence. The arithmetic reconciles exactly.

**Why it is not cosmetic:** `sdlc_pipeline/call_graph_analyzer.py` builds `danger_zones` (`:303`) and
`hot_nodes` (`:1197`) on an `n >= 5` caller-count gate, and `_classify_risk` (`:56-67`) labels
per-method risk on an 8+ gate. Both are caller-count-only. `JsonlAppender.append` therefore currently
ranks as the codebase's top danger zone on the strength of every `list.append()` in the repo, and
that ranking is injected into the Step 0 planning prompt via `prompt_gen_expert_caller.py`.

**How the violation would be detected: partially, and late.** SRS FR-38's acceptance criterion
assertion (1) is the mechanical check -- it fails if any `danger_zones` or `hot_nodes` entry's simple
name collides with a builtin and its fan-in does not survive excluding collided edges. But that check
is delivered **by V2-010 itself**. Ship V2-009 alone and no check exists to fail.

**Explicitly NOT part of this defect:** `resolve_edges()` writes to `_resolved_edges`, not
`graph.edges`, so reading `graph.edges` returns 656 instead of 7,004. **No shipping code does this**
-- all four consumers use `get_edges()` (`:155`, `:455`, `:600`, `:1209`). It caught an agent, not
the pipeline. Do not conflate the two.

---

## R-4. PRD FR-9a's real scope is TWO binding sites, and the written AC names neither pair correctly

**Severity: CORRECTNESS-CRITICAL and SCOPE-CRITICAL.**

**Constraint:** V2-009 must close against the two sites that bind, not against the four the AC names
and not against the 17 the probe enumerated.

**The three different numbers, and what each means:**

| Number | What it counts | Where it comes from |
|---|---|---|
| 17 | Truncation **code locations** of every class | Phase 5 probe enumeration, `docs/REVIEW-INDEX.md` section 4b |
| 4 | The sites named in the **written acceptance criterion** | `prd-v2.md` section 5 FR-9a row; mirrored at `SRS.md:736` |
| **2** | Sites that **actually bind today** | Phase 5 probe, MEASURED at runtime; `hld_v2.md:1617-1636` |

**The two that bind, both verified on disk by this pass 2026-08-01:**

1. `langgraph_engine/parsers/call_graph_builder_legacy.py:64` -- line 64 reads `MAX_FILES = 300`.
   Enforced at `:107` and `:118`. **MEASURED.**
2. `langgraph_engine/parsers/graph_model.py:43` -- line 43 reads
   `DEFAULT_MAX_PATHS = _env_int("CLAUDE_CG_MAX_PATHS", 500)`. **MEASURED.**

**What breaks, two distinct ways:**

**(a) Padding sends the implementer to inert sites.** Of the AC's four, `parsers/config.py:11` is
**dead code read by nothing** -- correction #22 in `docs/REVIEW-INDEX.md`, found by running the
builder rather than reading it, and cited in **19 files across every phase including `SRS.md`**.
Fixing it changes nothing while appearing to succeed. Two more of the AC's four are dormant
near-duplicates that can be "left unfixed because they look unused". A work list padded with inert
sites invites exactly the failure this whole finding is about.

**(b) The omission is worse than the padding. `graph_model.py:43` is in NEITHER the PRD AC nor the
SRS AC.** It survives fixing the file cap. Both probe runs emitted
`hit max_paths=500 limit; results truncated`. Every sequence and interaction diagram is capped at 500
paths no matter how many files are ingested. **An implementer working strictly to the written AC
would fix four sites, one of which is dead, watch every assertion in the AC pass, and leave a binding
truncation in production.**

**How the violation would be detected: it would NOT be.** The AC's own regression test
(`test_discovery_covers_every_package`, with the canary asserting
`manifest.packages["langgraph_engine/sdlc_pipeline"].analysed_n == 45`) tests **discovery coverage**.
`graph_model.py:43` truncates **path enumeration**, which the canary does not observe. The AC would
go green with the defect intact.

**Additional propagation hazard.** The supersession is recorded in `hld_v2.md` SS 12 OAQ 4 but is
**not propagated document-wide**: ADR-013's own body (`hld_v2.md:406`, `:436-443`) still states
"`parsers/config.py:11` sets `MAX_FILES = 300`" and "The defect exists at FOUR independent sites",
and the binding clause at `hld_v2.md:1696-1700` still says "each of sites 1-4". An implementer who
reads ADR-013 rather than OAQ 4 gets the superseded list with no pointer to the correction. This is
correction class #14 (backward propagation) still live inside the HLD.

**Disposition in the plan:** V2-009 carries the AC as written, flags it superseded, names
`graph_model.py:43` as the omission, and is labelled `needs-decision`. **This plan does not rewrite
a gate-passed acceptance criterion.** The amendment is an owner decision and is a prerequisite to
closing V2-009 correctly.

---

## R-5. PRD FR-7 must land before PRD FR-5 (found by this pass, not in the brief)

**Severity: CORRECTNESS-CRITICAL.**

**Constraint:** V2-028 (PRD FR-5 / SRS FR-15, remove `UserPromptSubmit` from the hot path) is blocked
by V2-026 (PRD FR-7 / SRS FR-17, the six slash-command entry points).

**Evidence:** `product-sequencing-v2.md` section 2 labels the FR-7 row verbatim "slash commands
(entry points, **prerequisite for safe FR-5**)". `hld_v2.md` SS 10 step 4 places "Learn the explicit
entry points (FR-7)" before step 6 "Take `UserPromptSubmit` off the hot path". SRS FR-15's own
acceptance criterion (`SRS.md:730`) states "pipeline execution begins only from an explicit FR-17
command" -- the AC for removing the old entry point is written in terms of the new one existing.

**What breaks if violated:** `scripts/3-level-flow.py` stops being the every-prompt entry point and
nothing replaces it. The pipeline becomes unreachable. No slash command exists to invoke it -- a
`commands/` directory does not exist on disk (verified absent 2026-08-01).

**How the violation would be detected:** immediately and loudly, on the first attempt to run the
pipeline. This is the least dangerous of the correctness-critical constraints precisely because its
violation is impossible to miss. It is listed because it is easy to violate while re-ordering batch G
for convenience -- FR-4 and FR-5 look like one deletion job and they are not.

---

## R-6. Deliverable 1 is recorded DONE while the artifacts its ACs require are absent

**Severity: SCOPE-CRITICAL. 18 ASSUMED points hang on this.**

**The contradiction, three sources:**

- `product-sequencing-v2.md` SS 1 records D1 as "**DONE, approved 2026-08-01**", and SS 0 states the
  audit "retires the single hardest constraint the original task brief anticipated".
- `prd-v2.md` section 2 lists PRD FR-1, FR-2 and FR-3 as **Partial**, and FR-2's note states that the
  required file path `docs/reports/policy-implementation-audit-v2.md` "does not exist yet".
- `SRS.md:152-157` lists the whole v2.0.0 block as DESIGNED, NOT BUILT and names
  `docs/reports/policy-implementation-audit-v2.md` among files "verified absent on disk on
  2026-08-01".

**Verified independently by this pass, 2026-08-01:**
`docs/reports/policy-implementation-audit-v2.md` -- **ABSENT.**

**Reconciliation:** what was approved was the Deliverable-1 **decision set** (three binding
resolutions recorded in `orchestration_prompt.md` SS 3.3), not the Deliverable-1 **artifact**. The
two are being referred to by the same name.

**What breaks if this is not resolved before planning is treated as final:** either 18 ASSUMED points
of real work are missing from every downstream estimate, or five issues (V2-004 through V2-008) are
phantom scope that will be closed as already-done and skew any velocity measurement taken from them.
**Both failure modes corrupt the first velocity figure this project ever produces**, which is the one
figure every later forecast will be anchored to.

**Owner decision required.** If D1 is genuinely discharged, V2-004 through V2-008 drop from the plan.
If it is not, they stay and 18 ASSUMED points are real. This plan carries them as real, because the
artifact is absent and two of the three sources say so.

---

## R-7. PRD FR-22's remaining half is blocked by PRD FR-4, so the highest-WSJF item cannot go first

**Severity: HYGIENE, but it inverts the published priority order.**

**Constraint:** V2-030 (PRD FR-22 / SRS FR-34, the SRS Change Log row) is blocked by V2-027 (PRD
FR-4, the deletion PR).

**Evidence:** SRS FR-34's acceptance criterion (`SRS.md:749`) has two clauses. Clause one -- the
appended superseding FR entry -- is recorded as **already satisfied** by the Phase 5 append. Clause
two -- a Change Log row "dated to the PR that deletes `PreToolUse`/`PostToolUse`, referencing that FR
by number" -- is recorded verbatim as "NOT and cannot be until that PR exists". `SRS.md:808` carries
it as an explicit OUTSTANDING obligation with a PENDING date rather than a back-dated row.

**What breaks if violated:** a planner reading `product-sequencing-v2.md`'s WSJF table sees FR-22 at
13.00, ranked first, sized 1, and schedules it in the first batch. It cannot be done there. It is
half done already and the other half is at the end of the dependency chain.

**Why this is worth recording rather than silently fixing:** the WSJF figure is arithmetically
correct. It is the **input scope** that changed under it -- half the job was completed by a later
pass, and no WSJF row was updated. The number is right and unusable, which is a different failure
from a number being wrong.

---

## R-8. `SRS.md`'s own FR count disagrees with its enumeration

**Severity: HYGIENE, in the document that carries the v2.0.0 scope statement.**

`SRS.md:143` states the appended block "runs FR-10 through FR-37 (**28 entries**)" and `SRS.md:159`
states "These **28 entries** are the v2.0.0 MVP boundary".

**Enumerated by this pass:** the block runs FR-10 through **FR-38** -- **29 entries**. Confirmed
three ways: 29 `Source:` lines between `SRS.md:169` and `SRS.md:452`; FR-38 present at `SRS.md:448`;
FR-38's acceptance criterion present at `SRS.md:753`.

FR-38 (the call-graph resolver defect, PRD FR-9b) was appended in a later Phase 5 pass and the header
count and the range in the same sentence were not updated with it.

**This is one more instance of correction class #9-13** -- a summary count disagreeing with its
enumeration -- and it is exactly the class that FR-25 (proposed) was written to catch and that
FR-25's own file records it might not catch. **Recorded, not fixed here:** editing `SRS.md` is
governed by rules/44 (append-only) and by whoever owns the SRS. This plan uses 29.

---

## R-9. PRD FR-15 must not be sized before its AST classifier runs

**Severity: SCOPE-CRITICAL.**

**Constraint:** V2-018 carries no point value. Its first task is the classifier; its second is
remediation, whose size is unknown until the first completes.

**Evidence:** `prd-v2.md` section 5 records the prior FR-15 acceptance criterion as **WITHDRAWN**
because it "asserted 13 as fact inside a gate-passed acceptance criterion" while a second,
differently-derived measurement stands unreconciled. `product-sequencing-v2.md` SS 2a records the
FR-15/FR-17 paired WSJF row (size 3) as derived from the withdrawn figure and requiring recomputation.
`hld_v2.md` OAQ 6 states plainly: "Both cannot stand."

**The two measurements:** 13 live-code sites / 103 comments (AST-based, `path_violations.md`) versus
approximately 95 live-code / 23 comments (independent line-oriented grep). **Approximately a 7x swing
in remediation scope.** The grep cannot structurally separate docstring bodies from code, so it does
not refute the AST figure -- but 13 has never been verified by an independent method either.

**What breaks if violated:** FR-15 is sized at 3 points (or at any number), the batch total looks
settled, and remediation turns out to be 95 sites. **An absent number is not a small number.**

**Note:** FR-17's 19-site count is independently confirmed and stable. The PM's own guidance is that
the FR-15/FR-17 pairing must split rather than be re-estimated as a unit. This plan splits them.

---

## R-10. ADR-020 Path C is INFERRED safe, not measured safe, and the only moment to measure it is when `register-mcp` is built

**Severity: CORRECTNESS-CRITICAL, and it is time-boxed to a window that will close.**

**Constraint:** V2-016 (`register-mcp`, DESIGNED NOT BUILT) carries the ADR-020 Path C verification
task as an in-scope item, not a follow-up.

**Evidence:** `hld_v2.md:741-742` states verbatim: "**Path C is INFERRED safe, not measured safe. The
inference is well-grounded; the certainty is not yet earned, and the stake is high enough that the
distinction matters.**" `hld_v2.md:773` attaches a "**VERIFICATION TASK (owner: whoever implements
`register-mcp`; ~10 minutes, at the only moment it can be performed)**".

**Why the window closes:** what was measured is that `/plugin uninstall` left 5 hook registrations
and 25 pre-existing `mcpServers` entries byte-identical to baseline. What was **not** measured is
what happens to an entry `register-mcp` wrote -- because, per `hld_v2.md:758-760`, "**no entry
written by `register-mcp` was present during the measured uninstall, because `register-mcp` does not
exist yet.**" The measurement can only be taken once the command exists and before anyone relies on
the inference.

**What breaks if the inference is wrong:** `hld_v2.md:766-771` -- "**if the inference is wrong, Path
C is the one path with NO available control.**" Prevention is impossible and detection is impossible,
because the plugin is gone, so no `doctor` command and no per-command check can run. Every other path
in ADR-020's table degrades to a weaker control. Path C degrades to none.

**Fallback if it fails:** ADV-012's git `pre-push` hook would have to move from **proposed** to
**required**. ADV-012 is currently NAMED, NOT ADOPTED.

---

## R-11. PRD FR-21's retirement path depends on PRD FR-3's disposition ledger existing

**Severity: HYGIENE.**

**Constraint:** V2-034 (PRD FR-21 / SRS FR-33) is blocked by V2-006 (PRD FR-3 / SRS FR-12) and
V2-008 (PRD NFR-4 / SRS NFR-10).

**Evidence:** SRS FR-33's acceptance criterion (`SRS.md:748`) offers exactly two end states per dead
reference, and the second is "the reference is removed from `hooks/stop_notifier/core.py` **and the
lost capability appears with a disposition in the FR-12/NFR-10 ledger**". If that ledger does not
exist, the retirement path is unavailable and only the rebuild path remains -- which
`product-sequencing-v2.md` SS 3 defers to v2.1 and FR-8a's own AC penalises.

**What breaks if violated:** FR-21 closes with 7 references deleted and no disposition recorded, which
is precisely the "silently broken" end state FR-21 exists to prevent. `prd-v2.md` FR-21 states
verbatim: "silently broken is not an acceptable end state for either choice."

---

## R-12. PRD NFR-1's harness can be built early but cannot be measured early

**Severity: HYGIENE.**

**Constraint:** V2-003 sits in batch A because the harness build is unblocked. It carries a
`closes_after` field naming V2-015 (plugin exists to install) and V2-027 (hooks deleted).

**Evidence:** the NFR-1 acceptance criterion measures a process-count delta "with the plugin
installed but not invoked", per component, excluding the retained Stop and Notification hooks, with
cold and warm counts reported as two separate numbers and a measurement window that must not span a
response-turn boundary. None of that is measurable before a plugin exists.

**What breaks if violated:** an issue is closed on a harness that has never produced a pass, and
NFR-1 -- the project's stated single primary success metric -- is recorded green on an unexecuted
test.

---

## R-13. The MVP boundary is softer than the WSJF precision implies -- carried forward, not laundered

**Severity: SCOPE-CRITICAL, and it applies to every ordering claim not covered above.**

**The claim, stated at full strength.** The WSJF arithmetic in `product-sequencing-v2.md` is exact
and verified -- it was checked by the Phase 2 consensus gate and no arithmetic defect was found. **The
input integers are a different matter.** They are the product manager's single-pass estimates, entered
once, never cross-checked by a second party. `docs/REVIEW-INDEX.md` section 2 records this as
**UNVALIDATED JUDGEMENT** and adds: "Normal for WSJF and not a defect -- but the MVP line is softer
than the precision of the numbers implies."

**Where this plan's ordering rests on a small WSJF delta, and what that means:**

| Comparison | Delta | Does the plan rely on it? |
|---|---|---|
| NFR-3 (6.33) vs FR-9 library rebuild (6.00) vs FR-8a (6.00) | 0.33 | **No.** The plan puts FR-9 in batch A and NFR-3 in batch G, which **inverts** the WSJF order. That inversion is deliberate: gate order and dependency beat a 0.33 delta on integers estimated once. |
| register-mcp (3.80) vs FR-18/NFR-5 (3.20) vs FR-16 (2.80) | under 1.0 across three | **No.** All three are inside D5 and their order is set entirely by `blocked_by`. |
| FR-23 (7.67) vs FR-4/FR-5 (6.67) | 1.00 | **No, and it would not matter.** This ordering is independently forced by R-1, a correctness constraint. The WSJF ranking happens to agree; the constraint is what binds. |

**The honest summary: no batch boundary and no intra-batch ordering in `sprint_plan.md` is derived
from WSJF.** Every one is derived from a dependency, a fixed gate, or a correctness constraint. WSJF
is reported for continuity with the source document and is not load-bearing anywhere in this plan.
That is a deliberate choice given the softness above, not an accident of construction.

**What this does NOT license.** The softness is in the inputs, not in the arithmetic, and it is not a
reason to re-rank items by feel. If the ordering ever does need to rest on WSJF, the correct move is
to have a second party re-score the CoD integers -- not to substitute a different unvalidated
judgement for the existing one.

---

## R-14. Summary table

| ID | Ordering | Severity | Detected if violated? |
|---|---|---|---|
| R-1 | `register-mcp` AND ADR-017 CI assertion before FR-4 | CORRECTNESS-CRITICAL | **No** -- no mechanism exists until V2-025 lands |
| R-2 | FR-9a before FR-10 | CORRECTNESS-CRITICAL | Partially -- by review of FR-10's AC clause, not automatically |
| R-3 | FR-9a and FR-9b as one deliverable | CORRECTNESS-CRITICAL | **No** if FR-9a ships alone -- the check is delivered by FR-9b |
| R-4 | FR-9a closes against 2 binding sites, not 4 or 17 | CORRECTNESS-CRITICAL | **No** -- the AC's canary tests discovery, not path enumeration |
| R-5 | FR-7 before FR-5 | CORRECTNESS-CRITICAL | Yes, immediately and loudly |
| R-6 | D1 artifacts exist before D1 is treated as closed | SCOPE-CRITICAL | Yes, by file existence check |
| R-7 | FR-22's Change Log row after FR-4 | HYGIENE | Yes -- the row cannot be dated |
| R-8 | SRS count 28 vs 29 enumerated | HYGIENE | Only by enumeration |
| R-9 | FR-15 classifier before FR-15 sizing | SCOPE-CRITICAL | **No** -- a wrong size looks exactly like a right one |
| R-10 | ADR-020 Path C measured when `register-mcp` is built | CORRECTNESS-CRITICAL | **No** -- and the window to measure closes |
| R-11 | FR-3 ledger before FR-21 retirement | HYGIENE | Yes, by the ledger lookup failing |
| R-12 | NFR-1 harness measured after FR-14 and FR-4 | HYGIENE | Yes, if the run is actually attempted |
| R-13 | WSJF deltas are not load-bearing | SCOPE-CRITICAL | n/a -- this is a caveat, not an ordering |

**Seven of thirteen would not be detected by any existing mechanism if violated.** Four of those
seven are CORRECTNESS-CRITICAL. That concentration is the single most important property of this
table: the constraints that matter most are the ones with the least mechanical enforcement behind
them, which is why they are written down rather than assumed.

---

## R-15. What this document could not verify

Stated so it is not mistaken for verified ground.

1. **The 55.5 percent collision rate and the in-degree figures** (1,592 for `JsonlAppender.append`;
   755 to 756 for `ErrorMessages.format`) were MEASURED by two other agents and are cited, not
   re-run by this pass. The arithmetic reconciliation (18,608 + 2,853 + 433 = 21,894;
   26,114 - 21,894 = 4,220) was checked and is exact.
2. **The 300-of-411-files truncation figure** is cited from the Phase 5 probe, not re-measured. What
   this pass verified directly is that the constants exist at the stated lines.
3. **The Stop-hook per-turn spawn count of approximately 2** is a static filesystem inference (7 of 9
   scripts absent), never observed at runtime. FR-8a's own AC requires runtime instrumentation over
   20 consecutive invocations; a static re-derivation does NOT satisfy it.
4. **`audit_surface.json`'s counts are LOWER BOUNDS.** Its AST scan missed 4 aliased subprocess
   imports. The same blind spot may affect its 62 credential sites and 17 `settings.json` writers --
   nobody has checked.
5. **Team size, working pattern, and any throughput figure.** Nothing about capacity is verified
   because nothing about capacity has ever been measured on this project.
6. **Whether the repository currently has zero open issues.** Stated in the planning brief and taken
   as given. No GitHub call was made by this pass, by instruction.

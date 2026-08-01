# v2.0.0 Delivery Plan -- Dependency-Ordered Batches (NOT time-boxed sprints)

**Phase:** 6 (sprint planning)
**Author:** scrum-master-agent
**Date:** 2026-08-01
**Target:** `claude-workflow-engine` v1.21.5 -> v2.0.0
**Status of this document:** DRAFT. Nothing in it has been created on GitHub. `github_issues.json`
in this directory holds 37 issue drafts, none created.

---

## 0. Read This First -- Why There Are No Sprints, No Dates, and No Velocity

There is **no velocity data for this project**. No sprint history exists, no team size is on record,
no throughput has ever been measured. This document therefore contains:

- **No sprint length in days.**
- **No calendar dates.**
- **No velocity figure.**
- **No forecast of when v2.0.0 ships.**

Inventing any of those would produce a precise-looking number with nothing behind it -- the exact
defect class this project has caught 24 times (see `docs/REVIEW-INDEX.md` section 7). Every
capacity-shaped statement below is labelled **ASSUMPTION**, not finding.

What this document contains instead: a **dependency-ordered set of batches**, each batch being a
dependency-closed set of work that can be started once its predecessor batch is complete. Sizing is
**relative**, with the anchor stated in section 2.

### How this converts to sprints later, with zero rework

The batches are a topological ordering, not a schedule. When a velocity figure exists:

1. Take the issue list in `github_issues.json` in batch order (A, B, C, ... H), and within a batch in
   `blocked_by` topological order.
2. Cut the cumulative point total at the velocity figure. That cut is sprint 1. Repeat.
3. **The only rule the cut must respect** is that no issue enters a sprint before every issue in its
   `blocked_by` array has entered an earlier or the same sprint. Every dependency is machine-readable
   in `github_issues.json`, so this cut can be made by script.

Nothing needs re-sizing, re-scoping, or re-ordering to perform that conversion. A batch may split
across sprints; a sprint may absorb more than one batch. Batch boundaries are dependency boundaries,
not capacity boundaries, so they survive any velocity value.

### The four capacity ASSUMPTIONS this plan makes

| # | ASSUMPTION | Why it is an assumption and not a finding |
|---|---|---|
| A1 | Relative point sizes are comparable across issues drawn from `product-sequencing-v2.md` and issues sized by this document. | The former are the product manager's single-pass Fibonacci estimates; the latter are this document's. Neither has ever been calibrated against a completed item, because no item has completed. |
| A2 | A batch is workable by one person or a small team without further decomposition. | No team size is on record. If the work is parallelised across more than one person, batches B, E and G contain issues that can proceed concurrently; batches A, D and F contain serial chains that cannot. |
| A3 | The 34 ASSUMED points added by this document (section 2) are of the same currency as the 74 sourced points. | They were sized against the same anchor, but by a different estimator in a different pass. Treat the two totals separately until one completed item calibrates them. |
| A4 | No batch contains hidden work discovered only on contact. | Contradicted in advance for at least two items -- PRD FR-15 is explicitly unsizable until an AST re-derivation runs, and PRD FR-9a's written acceptance criterion is known to be both padded and incomplete (section 5). Both are named rather than absorbed. |

---

## 1. Sizing Basis and Anchor

**Instrument:** relative story points on a Fibonacci scale (1, 2, 3, 5, 8, 13), the same scale
`docs/phase-0-requirements/product-sequencing-v2.md` section 2 already uses.

**Anchor: 1 point = PRD FR-6 / SRS FR-16, the ADR-006 document.** That job is: create one file at
one known path from text that is already written and pre-committed, and confirm one section is
present and unedited. No design, no measurement, no dependency, no test to write. Every other size
in this plan is expressed as a multiple of that job.

**Provenance of every size is recorded per issue.** Two values only:

- **SOURCED** -- the size comes from `product-sequencing-v2.md` section 2 or 2a or 2c. 74 points total.
- **ASSUMED** -- the size was set by this document against the anchor above, because the source set
  contains no size for the unit. 34 points total, across 13 issues.
- **UNSIZED BY MANDATE** -- 1 issue (PRD FR-15 / SRS FR-28). `product-sequencing-v2.md` section 2a
  and `prd-v2.md` section 5 both state FR-15 must not be sized until the AST classifier has run.
  This plan honours that and assigns no number.

**Total: 74 SOURCED + 34 ASSUMED = 108 points, plus 1 unsized item.** These two totals are reported
separately and deliberately not merged into a single headline figure.

**What a point is NOT here:** it is not a day, not an hour, not a percentage of a sprint. It has no
time interpretation at all until a velocity measurement exists.

---

## 2. Size Ledger

### 2.1 SOURCED sizes (74 points, from `product-sequencing-v2.md`)

| Unit | Source section | Size | WSJF (as published) |
|---|---|---|---|
| PRD FR-6 ADR-006 doc | SS 2 | 1 | 12.00 |
| PRD FR-9 library KG drift | SS 2 | 2 | 6.00 |
| PRD NFR-1 measurement harness | SS 2a | 2 | 10.50 |
| PRD FR-9a CallGraph discovery fix | SS 2 | 5 | 4.60 |
| PRD FR-10..FR-13 KG selector (set) | SS 2 | 13 | 1.69 |
| PRD FR-14 plugin skeleton | SS 2 | 8 | 2.38 |
| ADR-019 register-mcp / unregister-mcp | SS 2c | 5 | 3.80 |
| PRD FR-16 build-time snapshot script | SS 2 | 5 | 2.80 |
| PRD FR-18 + NFR-5 uninstall lifecycle + tests (set) | SS 2 | 5 | 3.20 |
| PRD FR-23 push_gate to MCP port | SS 2 / 2a | 3 | 7.67 |
| PRD FR-7 slash commands | SS 2 | 5 | 4.20 |
| PRD FR-4 + FR-5 hook deletion (set) | SS 2a | 3 | 6.67 |
| PRD FR-22 SRS append | SS 2 | 1 | 13.00 |
| PRD NFR-3 CheckpointManager contract + 3 durability fixes | SS 2a | 3 | 6.33 |
| PRD NFR-2 timeout-removal engineering | SS 2a | 8 | 2.88 |
| PRD FR-8a decision + instrumentation + FR-21 minimal retire (set) | SS 2 | 3 | 6.00 |
| D7 migration guide + CHANGELOG + VERSION bump | SS 2 | 2 | 5.50 |

**Withdrawn source size, not used:** the FR-15/FR-17 paired row (size 3, WSJF 4.67).
`product-sequencing-v2.md` SS 2a and `prd-v2.md` section 5 both state the pairing must split and
FR-15's figure must be recomputed after measurement. This plan splits them: FR-17 carries an ASSUMED
size, FR-15 carries none.

### 2.2 ASSUMED sizes (34 points, set by this document)

| Unit | Size | Basis relative to the 1-point anchor |
|---|---|---|
| PRD FR-1 policy audit document | 8 | Line-by-line read of 46 policy documents plus a 46-row evidence table. The read pass, not the writing, dominates. |
| PRD FR-2 audit matrix, 7 columns x 46 rows | 3 | Mechanical once FR-1's read exists; the vocabulary is fixed and the row set is known. |
| PRD FR-3 dispositions for 15 hook-coupled policies | 3 | 15 judgement calls with a written rationale each, one of which (push_gate) is pre-decided. |
| PRD FR-20 dispositions for 14 orphan policies | 2 | 14 judgement calls, no new evidence gathering, list already enumerated. |
| PRD NFR-4 25-capability cross-check script | 2 | One script over two existing lists. |
| PRD FR-9b resolver fix | 5 | One-line source fix at `graph_model.py:265` is trivial; the cost is the two-field confidence reporting at 6 named consumption points plus a committed collision check plus a unit test. |
| PRD FR-17 encoding= remediation | 2 | 19 confirmed mechanical sites plus one scan with an exemption list. |
| PRD FR-24 uninstall-residue runbook | 1 | One document, paths already measured and enumerated. Same shape as the anchor. |
| ADR-017 CI assertion | 2 | One CI check with a specified signature plus its negative test. |
| SRS NFR-12 / ADR-020 PREVENT + DETECT layers | 3 | A refusal path in `unregister-mcp`, a `doctor` command, and a start-up check every FR-7 command runs. |
| PRD FR-4a blast-radius record | 1 | The measurement exists; only the three consequences need recording. |
| PRD FR-8 Stop/Notification preservation assertion | 1 | One install/uninstall test asserting byte-identical entries. |
| VERSION vs CLAUDE.md contradiction | 1 | One-character edit plus verification. |

### 2.3 Sizes split inside a sourced set (no new points added)

Where the source sized a set, this document splits it across issues without changing the total.
Each split is ASSUMED; each set total is SOURCED.

| Set (sourced total) | Split |
|---|---|
| PRD FR-10..FR-13 selector (13) | FR-10 = 8, FR-11 = 2, FR-12 = 2, FR-13 = 1 |
| PRD FR-18 + NFR-5 (5) | FR-18 = 3, NFR-5 = 2 |
| PRD FR-4 + FR-5 (3) | FR-4 = 2, FR-5 = 1 |
| PRD FR-8a + FR-21 (3) | FR-8a = 2, FR-21 = 1 |

---

## 3. The Batches

Eight batches. A batch may begin when every issue it depends on has landed. Within a batch, the
`blocked_by` array in `github_issues.json` gives the internal order.

**Note on the two FR numbering series.** `prd-v2.md` has its own FR-1..FR-24 series. `SRS.md` has
FR-10..FR-38. They are different requirements. Every reference below names the document. This is the
naming collision `SRS.md:145-150` documents and does not work around.

### Batch A -- Foundation (8 issues, 5 SOURCED + 18 ASSUMED = 23 points)

Everything here has zero blocking dependency on any other batch. Batch A is the only batch that can
start today.

| Key | Requirement | Size |
|---|---|---|
| V2-001 | PRD FR-6 / SRS FR-16 -- ADR-006 hook-free-execution document | 1 SOURCED |
| V2-002 | PRD FR-9 / SRS FR-20 -- `claude-global-library` master-graph count drift | 2 SOURCED |
| V2-003 | PRD NFR-1 / SRS NFR-7 -- process-count measurement harness | 2 SOURCED |
| V2-004 | PRD FR-1 / SRS FR-10 -- policy implementation audit document | 8 ASSUMED |
| V2-005 | PRD FR-2 / SRS FR-11 -- 7-column audit matrix, 46 rows | 3 ASSUMED |
| V2-006 | PRD FR-3 / SRS FR-12 -- dispositions for the 15 hook-coupled policies | 3 ASSUMED |
| V2-007 | PRD FR-20 / SRS FR-32 -- dispositions for the 14 orphan policies | 2 ASSUMED |
| V2-008 | PRD NFR-4 / SRS NFR-10 -- 25-capability disposition cross-check | 2 ASSUMED |

**V2-003 caveat, stated rather than hidden:** the harness can be *built* with no dependency, but its
acceptance criterion measures a session with the plugin installed. The issue therefore carries a
`closes_after` field naming V2-015 and V2-027. It is in batch A because the build is unblocked, not
because it can close there.

**Scope discrepancy this batch surfaces (see `sequencing_risks.md` R-6).**
`product-sequencing-v2.md` records Deliverable 1 as "DONE, approved 2026-08-01". The artifacts its
own acceptance criteria require are **absent on disk, verified 2026-08-01 by this pass**:
`docs/reports/policy-implementation-audit-v2.md` does not exist. `SRS.md:152-157` independently lists
SRS FR-10, FR-11, FR-12 and FR-32 as DESIGNED, NOT BUILT. What was approved was the Deliverable-1
*decision set*, not the deliverable. Batch A therefore carries this work as real, unsized-in-source
scope. If the project owner reads D1 as fully discharged, these five issues drop and 18 ASSUMED
points leave the plan -- that is an owner decision, not a planning one.

### Batch B -- Call-graph correctness (2 issues, 5 SOURCED + 5 ASSUMED = 10 points)

**These two are ONE deliverable split across two issues for reviewability. Neither ships alone.**

| Key | Requirement | Size |
|---|---|---|
| V2-009 | PRD FR-9a / SRS FR-21 -- call-graph discovery truncation | 5 SOURCED |
| V2-010 | PRD FR-9b / SRS FR-38 -- call-graph resolver ambiguous-name bind | 5 ASSUMED |

Shipping V2-009 alone yields a larger graph feeding the same broken resolver: more files, the same
wrong `hot_nodes` and `danger_zones`, and a *higher* collided in-degree on the same wrong nodes.
`prd-v2.md` FR-9b states this explicitly ("FR-9a alone is INSUFFICIENT"), as does `SRS.md:296-297`.
V2-010 carries a hard `blocked_by` on V2-009 and both are gated as a pair before batch C opens.

### Batch C -- KG-driven selector (4 issues, 13 SOURCED = 13 points)

| Key | Requirement | Size |
|---|---|---|
| V2-011 | PRD FR-10 / SRS FR-22 -- KG-driven selection, zero hardcoded lists | 8 (split of 13) |
| V2-012 | PRD FR-11 / SRS FR-23 -- selection explainability, 5 fields | 2 (split of 13) |
| V2-013 | PRD FR-12 / SRS FR-24 -- no-match / low-confidence fallback | 2 (split of 13) |
| V2-014 | PRD FR-13 / SRS FR-25 -- model fallback protocol conformance | 1 (split of 13) |

### Batch D -- Plugin skeleton and MCP registration (3 issues, 13 SOURCED + 3 ASSUMED = 16 points)

Strictly serial. Each issue blocks the next.

| Key | Requirement | Size |
|---|---|---|
| V2-015 | PRD FR-14 / SRS FR-26 -- `.claude-plugin/plugin.json`, zero hooks, zero `.mcp.json` | 8 SOURCED |
| V2-016 | SRS FR-37 / ADR-019 -- `register-mcp` and `unregister-mcp` | 5 SOURCED |
| V2-017 | SRS NFR-12 / ADR-020 -- PREVENT and DETECT layers on the push gate | 3 ASSUMED |

**Both `register-mcp` and `unregister-mcp` are DESIGNED, NOT BUILT.** `hld_v2.md:759` states
verbatim that `register-mcp` "does not exist yet". `hld_v2.md:738` describes `unregister-mcp` as "is
designed to read and write" `settings.json` -- a wording downgrade recorded in that file's own change
log at line 1934. Zero lines of code exist for either.

**V2-016 carries the ADR-020 Path C verification task** (`hld_v2.md:773`, "~10 minutes, at the only
moment it can be performed"). Path C -- a user running `/plugin uninstall` after removing PreToolUse
-- is INFERRED safe, not measured safe, and it is the one path with no available control if the
inference is wrong.

### Batch E -- Plugin hardening and lifecycle (6 issues, 10 SOURCED + 3 ASSUMED = 13 points + 1 unsized)

| Key | Requirement | Size |
|---|---|---|
| V2-018 | PRD FR-15 / SRS FR-28 -- home-directory AST classifier and remediation | **UNSIZED BY MANDATE** |
| V2-019 | PRD FR-17 / SRS FR-30 -- `encoding=` at every text-mode `open()` | 2 ASSUMED |
| V2-020 | PRD FR-16 / SRS FR-29 -- build-time library snapshot script | 5 SOURCED |
| V2-021 | PRD FR-24 / SRS FR-36 -- uninstall-residue runbook | 1 ASSUMED |
| V2-022 | PRD FR-18 / SRS FR-31 -- plugin-attributable uninstall residue = 0 | 3 (split of 5) |
| V2-023 | PRD NFR-5 / SRS NFR-11 -- install / invoke / uninstall + round-trip tests | 2 (split of 5) |

**V2-018 must run its AST classifier before it can be sized.** `hld_v2.md` OAQ 6 records two
irreconcilable measurements of the same surface: 13 live-code sites / 103 comments (AST-based) versus
approximately 95 / 23 (line-oriented grep). That is close to a 7x swing in remediation scope. The
classifier is the first task inside V2-018; the remediation is the second, and its size is unknown
until the first completes. **Do not treat V2-018's absent number as a small number.**

### Batch F -- Push-gate replacement and entry points (3 issues, 8 SOURCED + 2 ASSUMED = 10 points)

**This batch is the safety precondition for batch G. Nothing in batch G may start before it closes.**

| Key | Requirement | Size |
|---|---|---|
| V2-024 | PRD FR-23 / SRS FR-35 -- `push_gate.py` reachable as a named MCP tool | 3 SOURCED |
| V2-025 | ADR-017 -- `assert_push_gate_reachable()` CI assertion | 2 ASSUMED |
| V2-026 | PRD FR-7 / SRS FR-17 -- six slash-command entry points | 5 SOURCED |

**V2-025 has no acceptance criterion in the PRD or the SRS.** Its AC in `github_issues.json` is drawn
from `hld_v2.md` section 7.7 (the formal signature) and `hld_v2.md:661-664` (ADR-017 Chosen), and is
labelled HLD-sourced rather than PRD/SRS-sourced. SRS FR-35's AC covers commit ordering; it does not
specify the CI check itself. **The CI assertion is DESIGNED, NOT BUILT** -- recorded as correction
#17 in `docs/REVIEW-INDEX.md` section 7, where it had previously been documented as active.

**V2-026 is a prerequisite for safe FR-5, not merely for FR-5.** `product-sequencing-v2.md` SS 2
labels FR-7 "entry points, prerequisite for safe FR-5". Removing `UserPromptSubmit` from the hot path
with no slash commands in place leaves the pipeline with no user-reachable entry point at all. See
`sequencing_risks.md` R-5.

### Batch G -- Hook deletion and NFR closure (9 issues, 18 SOURCED + 2 ASSUMED = 20 points)

| Key | Requirement | Size |
|---|---|---|
| V2-027 | PRD FR-4 / SRS FR-13 -- delete PreToolUse and PostToolUse | 2 (split of 3) |
| V2-028 | PRD FR-5 / SRS FR-15 -- `UserPromptSubmit` off the hot path | 1 (split of 3) |
| V2-029 | PRD FR-4a / SRS FR-14 -- blast-radius record and 3 consequences | 1 ASSUMED |
| V2-030 | PRD FR-22 / SRS FR-34 -- SRS Change Log row on the deletion PR | 1 SOURCED |
| V2-031 | PRD NFR-3 / SRS NFR-9 -- CheckpointManager contract + 3 durability fixes | 3 SOURCED |
| V2-032 | PRD FR-8 / SRS FR-18 -- Stop and Notification left byte-identical | 1 ASSUMED |
| V2-033 | PRD FR-8a / SRS FR-19 -- Stop-hook instrumentation and per-capability decision | 2 (split of 3) |
| V2-034 | PRD FR-21 / SRS FR-33 -- 7 dead Stop-hook script references fixed or retired | 1 (split of 3) |
| V2-035 | PRD NFR-2 / SRS NFR-8 -- 5 non-temporal control mechanisms | 8 SOURCED |

**V2-035 has no technical dependency on any other issue in this plan.** It is engine-side work at 6
`timeout=` application sites across 5 files, including a 75-second wall-clock abort on the Step 1
pipeline path. It sits in batch G only because `product-sequencing-v2.md` SS 1 fixes the D1-D7 gate
order and NFR-2 belongs to D6. **If work is parallelised, V2-035 is the single best candidate to pull
forward** -- it is the largest sourced item outside the selector and it blocks nothing and is blocked
by nothing.

**V2-031 likewise has no dependency** on the plugin or on hook deletion. `CheckpointManager` already
exists and survives FR-4 untouched (`hld_v2.md` OAQ 1 / ADR-011). The remaining work is three named
durability defects, not a new writer.

### Batch H -- Release (2 issues, 2 SOURCED + 1 ASSUMED = 3 points)

| Key | Requirement | Size |
|---|---|---|
| V2-036 | D7 -- migration guide, CHANGELOG, VERSION bump to 2.0.0 | 2 SOURCED |
| V2-037 | `VERSION` (1.21.5) vs `CLAUDE.md` (1.21.4) contradiction | 1 ASSUMED |

V2-037 is a pre-existing, unowned contradiction recorded in `docs/REVIEW-INDEX.md` section 2. Both
values verified on disk 2026-08-01: `VERSION` reads `1.21.5`, `CLAUDE.md:4` reads `1.21.4`. Rule 11
makes `VERSION` authoritative, so `CLAUDE.md` is the stale one. It is bundled here because a version
bump touches both files anyway.

---

## 4. Critical Path

The longest dependency chain through the plan. Every arrow is a hard `blocked_by`.

```
V2-015 (PRD FR-14, plugin skeleton, 8)
   -> V2-016 (register-mcp / unregister-mcp, 5)          [DESIGNED, NOT BUILT]
      -> V2-024 (PRD FR-23, push_gate -> MCP tool, 3)
         -> V2-025 (ADR-017 CI assertion, 2)             [DESIGNED, NOT BUILT]
            -> V2-027 (PRD FR-4, hook deletion, 2)
               -> V2-030 (PRD FR-22, SRS Change Log row, 1)
                  -> V2-036 (D7 release, 2)
```

**Critical path length: 23 points across 7 issues.**

A second chain of comparable weight runs through the selector and is **independent of the plugin
chain until the release**:

```
V2-009 (PRD FR-9a, discovery, 5)
   -> V2-010 (PRD FR-9b, resolution, 5)
      -> V2-011 (PRD FR-10, selector, 8)
         -> V2-012 / V2-013 / V2-014 (5 combined)
            -> V2-036 (D7 release, 2)
```

**Selector chain length: 25 points across 7 issues.** By raw point count this chain is *longer* than
the plugin chain, and the source documents agree on its risk: `product-sequencing-v2.md` SS 6 names
FR-9a -> FR-10 "the single riskiest link" across three separate revisions.

**Both chains converge only at V2-036.** With more than one worker they run in parallel and the
critical path is the selector chain at 25 points. With a single worker the critical path is the whole
plan and this distinction has no scheduling meaning. **Which of these holds is unknown -- team size
is not on record (ASSUMPTION A2).**

**What is NOT on the critical path, despite high WSJF:** PRD FR-22 (WSJF 13.00, the published #1) and
PRD FR-6 (WSJF 12.00, the published #2). FR-6 genuinely is a free early win. FR-22 is not -- see
section 5.

---

## 5. Where This Plan Departs From Its Sources, and Why

Six departures. Each is a place where following the source document literally would produce wrong
work. None is a silent correction.

**5.1 The published WSJF #1 cannot be done first.** `product-sequencing-v2.md` ranks PRD FR-22 (SRS
append) at WSJF 13.00, top of the table. But SRS FR-34's own acceptance criterion
(`SRS.md:749`) splits into two clauses and records the first as **already satisfied by the Phase 5
append** and the second as one that "is NOT and cannot be until that PR exists" -- the PR being the
one that deletes PreToolUse/PostToolUse. So the remaining half of the highest-WSJF item is blocked by
FR-4, which is nearly the last thing to land. It sits in batch G as V2-030, not in batch A. The WSJF
number is arithmetically correct and operationally unusable for this item.

**5.2 PRD FR-9a's written acceptance criterion is both padded and incomplete.** The AC in
`prd-v2.md` section 5 and its mirror at `SRS.md:736` name **four** truncation sites. The Phase 5
runtime probe, recorded in `docs/REVIEW-INDEX.md` section 4b and in `hld_v2.md` SS 12 OAQ 4
(lines 1570-1636), measured that of 17 truncation sites only **two** bind:

| Site | Status | Verified by this pass |
|---|---|---|
| `langgraph_engine/parsers/call_graph_builder_legacy.py:64` (`MAX_FILES = 300`) | **BINDING** | Read directly on disk 2026-08-01: line 64 is `MAX_FILES = 300`. MEASURED. |
| `langgraph_engine/parsers/graph_model.py:43` (`DEFAULT_MAX_PATHS`, 500) | **BINDING** | Read directly on disk 2026-08-01: line 43 is `DEFAULT_MAX_PATHS = _env_int("CLAUDE_CG_MAX_PATHS", 500)`. MEASURED. |
| `langgraph_engine/parsers/config.py:11` (`MAX_FILES = 300`) | **DEAD CODE** -- read by nothing | Correction #22 in `docs/REVIEW-INDEX.md`. Cited in 19 files across every phase, including `SRS.md`. |
| Two `code_graph_analyzer` variants (sites 3 and 4 in the AC) | dormant / downstream | Per the probe's classification table. |

**`graph_model.py:43` appears in NEITHER the PRD AC nor the SRS AC.** It survives fixing the file
cap, and both probe runs emitted `hit max_paths=500 limit; results truncated`. An implementer working
strictly to the written AC would fix four sites, one of which is dead, and would **leave a binding
truncation in place** while every check in the AC passed.

**This plan does not rewrite the AC.** Rewriting a gate-passed acceptance criterion is not a sprint
planner's call. V2-009's issue body carries the AC as written, flags it as superseded, names
`graph_model.py:43` as an omission, and marks the issue `needs-decision`. **The AC amendment is an
owner decision and is a prerequisite to closing V2-009 correctly.**

**5.3 `product-sequencing-v2.md`'s sequencing risk #3 is stale and is not carried forward.** That
document states three times (SS 6, SS 7, SS 8) that `hld_v2.md` SS 10's migration runbook has "NOT
YET" been updated to insert `register-mcp` before the FR-23 reachability check. **It has been.**
`hld_v2.md:1318` is step 2, `register-mcp`; `hld_v2.md:1319` is step 3, the FR-23 reachability
verification, which reads "Cannot pass before step 2". The edit is recorded in that file's own change
log at line 1936 (draft-11, BA FIND-10) and the runbook now runs to 8 steps.
`docs/REVIEW-INDEX.md:25` agrees the runbook is rebuilt. This plan treats risk #3 as closed and
replaces it (see `sequencing_risks.md` R-6, R-7).

**5.4 `SRS.md`'s own FR count does not match its enumeration.** `SRS.md:143` states the block "runs
FR-10 through FR-37 (28 entries)" and `SRS.md:159` states "These 28 entries are the v2.0.0 MVP
boundary". The block actually runs FR-10 through **FR-38 -- 29 entries**. Enumerated by this pass:
29 `Source:` lines between `SRS.md:169` and `SRS.md:452`, and FR-38 is present at `SRS.md:448` with
its acceptance criterion at `SRS.md:753`. FR-38 (the resolver defect) was appended in a later Phase 5
pass and the header count was not updated with it. **This is one more instance of correction class
#9-13** (a summary count disagreeing with its enumeration), occurring in the document that carries the
v2.0.0 scope statement. Filed as `sequencing_risks.md` R-8. This plan uses 29.

**5.5 Deliverable 1 is recorded DONE while its artifacts are absent.** See batch A above and
`sequencing_risks.md` R-6. 18 ASSUMED points hang on this.

**5.6 The MVP boundary rests on WSJF inputs that were never cross-checked.** The WSJF arithmetic in
`product-sequencing-v2.md` is exact and verified. The **input integers are the product manager's
single-pass estimates, entered once, never reviewed by a second party** (`docs/REVIEW-INDEX.md`
section 2, recorded as UNVALIDATED JUDGEMENT). Where this plan's ordering rests on a small WSJF
delta, it says so:

- **PRD NFR-3 (6.33) versus PRD FR-9 library rebuild (6.00) versus PRD FR-8a (6.00).** A delta of
  0.33 across a CoD built from three integers each estimated once. **This ordering is not
  load-bearing and this plan does not rely on it.** NFR-3 sits in batch G and FR-9 in batch A for
  dependency reasons, not WSJF reasons -- which happens to invert the WSJF order. That inversion is
  deliberate and is the correct call: gate order and dependency beat a 0.33 delta on unvalidated
  integers.
- **ADR-019 `register-mcp` (3.80) versus PRD FR-18/NFR-5 (3.20) versus PRD FR-16 (2.80).** All three
  sit inside D5, all three within 1.0 WSJF of each other. Their relative order in this plan is set
  entirely by `blocked_by`, never by WSJF.
- **Where WSJF IS load-bearing in this plan:** nowhere. Every batch boundary and every intra-batch
  order in this document is derived from a dependency, a gate, or a correctness constraint. WSJF is
  reported in section 2.1 for continuity with the source, and is not used to sequence anything.

---

## 6. What Is In Scope and What Is Not

### In v2.0.0 (this plan, 37 issues)

D1 completion (PRD FR-1, FR-2, FR-3, FR-20, NFR-4) -- D2 (FR-6) -- D3 (FR-9) --
D4 (FR-9a, FR-9b, FR-10..FR-13) -- D5 (FR-14, register-mcp/unregister-mcp, FR-15, FR-16, FR-17,
FR-18, FR-24, NFR-5, ADR-020 layers) -- D6 (FR-23, ADR-017 CI assertion, FR-4, FR-4a, FR-5, FR-7,
FR-8, FR-8a, FR-21, FR-22, NFR-1, NFR-2, NFR-3) -- D7 (migration, CHANGELOG, VERSION).

**One-step install covers commands, agents and skills only.** MCP-backed capabilities (the FR-23
push gate, the progress writer) require the separate `register-mcp` step. This is a deliberate,
disclosed trade-off under ADR-019, applied to `prd-v2.md` FR-14's wording, not a silent regression.

### Deferred to v2.1 (no issues drafted)

- **PRD FR-19** `get_policies_dir()` four-branch resolver -- blocked on the ADR-009b five-policy human
  sign-off, which has no committed date. Explicitly not carried into `SRS.md` (`SRS.md:159-162`).
- **PRD FR-8a rebuilds** -- any of the 5 dead Stop-hook capabilities the v2.0.0 decision session
  selects for rebuild. The decision and the retirement of everything not selected ship in v2.0.0 as
  V2-033 and V2-034; only a selected rebuild's build work defers.
- **ADV-001** the fifth truncator at `build_dependency_resolver/parsers.py:682` -- a different defect
  class (a truncated boolean, not a truncated graph), deliberately out of FR-9a scope.
- **ADV-002** package-level import SCC / extraction seam.
- Residual PRD FR-20 polish beyond D1's recorded dispositions; ADR-008 marketplace polish.

### Proposed but NOT accepted -- owner decision required, no issues drafted

**FR-25 (proposed)** and **FR-26 (proposed)** exist only in
`docs/phase-2-validation/advisory_items.json`. `prd-v2.md` stops at FR-24 and `SRS.md` does not carry
them. FR-25 (proposed) is a CI check recomputing every annotated counting basis; FR-26 (proposed) is
an ADR impact registry with a commit-level cross-file backward-propagation check. Each was narrowed
three times in three passes as new instances outgrew its scope, and FR-25's own file records that a
recomputation check "would have PASSED both before and after the fix while the diagram was actively
contradicting an ADR."

**No issues are drafted for either.** Drafting one would be the "(proposed)" hedge silently dropping,
which is recorded as correction #21 in `docs/REVIEW-INDEX.md`. Accept into the PRD, defer to v2.1, or
drop -- this is the project owner's call. If accepted, both land in batch A (neither has a technical
dependency) and both would need sizing, which this plan does not pre-empt.

**ADV-012** (git `pre-push` hook restoring local PREVENTIVE push-gate protection) is NAMED, NOT
ADOPTED, and belongs to whoever owns PRD FR-23. It is not drafted as an issue here. Its absence is
the reason the post-FR-4 push gate is detective-only rather than preventive for a user who never runs
`register-mcp` -- see `sequencing_risks.md` R-1.

---

## 7. Batch Summary

| Batch | Issues | SOURCED pts | ASSUMED pts | Unsized | Blocked by |
|---|---|---|---|---|---|
| A Foundation | 8 | 5 | 18 | 0 | nothing |
| B Call-graph correctness | 2 | 5 | 5 | 0 | nothing |
| C KG selector | 4 | 13 | 0 | 0 | B (both issues) |
| D Plugin skeleton + MCP registration | 3 | 13 | 3 | 0 | nothing |
| E Plugin hardening + lifecycle | 6 | 10 | 3 | 1 | D (V2-015, V2-016) |
| F Push gate + entry points | 3 | 8 | 2 | 0 | D (V2-016) |
| G Hook deletion + NFR closure | 9 | 18 | 2 | 0 | **F in full** |
| H Release | 2 | 2 | 1 | 0 | A-G |
| **Total** | **37** | **74** | **34** | **1** | |

Sum check: issues 8+2+4+3+6+3+9+2 = 37. SOURCED 5+5+13+13+10+8+18+2 = 74. ASSUMED 18+5+0+3+3+2+2+1 = 34.

---

## 8. Related Documents

- `docs/phase-6-sprint/github_issues.json` -- 37 issue drafts, none created on GitHub.
- `docs/phase-6-sprint/sequencing_risks.md` -- orderings that are correctness-critical and what
  breaks if each is violated.

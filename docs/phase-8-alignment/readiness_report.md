# Phase 8 Pre-Implementation Alignment -- Readiness Report

**Date:** 2026-08-02
**Author:** architecture-conformance-auditor
**Gate:** last check before code is written against batch A
**Verdict:** **NOT READY AS WRITTEN.** 3 of batch A's 8 issues can start today against a correct
premise. One more can start but its stated starting condition is false on disk. Four are blocked by
in-batch predecessors.

This report was written adversarially. It tried to start batch A and records what stopped it. Where
a check found nothing, the check and its method are stated rather than padded.

---

## Citation-integrity revision, 2026-08-02

**Every line citation in this report was re-opened on 2026-08-02 and corrected where it had rotted.**
`SRS.md` grew 974 -> 1130 lines and `hld_v2.md` 1945 -> 2022 (`wc -l`) during the correction passes,
so line-keyed addresses stopped finding what they named. **Citations are now keyed to stable anchors**
-- a heading, an ADR number, a table-row prefix, or a constant name -- with the line number kept only
as a scanning hint. Where no stable anchor exists, the citation says what it points at, so a reader
can find the target by content when the number rots again.

**Findings MEASURED as resolved since this report was written.** Recorded so no reader acts on a
closed item; the finding text below is left intact as the record of what was found.

| ID | Status now | Evidence |
|---|---|---|
| B-01, B-02, B-03 | **RESOLVED** | `SRS.md` gained **`### Revised Acceptance Criterion for FR-10 (APPENDED 2026-08-02)`** (line 775), which rules `docs/policies/` the authoritative 46-file corpus, records `~/.claude/policies/` as a PARTIAL MIRROR, and states that `get_policies_dir()` (`src/utils/path_resolver.py:255-261`) resolves to the mirror. The audit file was reshaped by `e520b5e` to a 7-column, 46-row matrix. |
| B-11 | **RESOLVED** | `issue_key_map.json` now carries V2-009 at `size 8`, `RE_ESTIMATED`. |
| B-13 | **RESOLVED** | ASSUMPTION A3 now reads "69 SOURCED"; A5 reads "11 RE-ESTIMATED". |
| B-14 | **RESOLVED** | The "Still open" paragraph has been removed from `sprint_plan.md`. |
| B-15 | **RESOLVED** | WSJF recomputed. `sprint_plan.md` line 113 shows `~~4.60~~ **2.875, recomputed**`, and its before/after rank table (lines 287-292) records FR-9a dropping from 10th to joint 13th/14th -- confirming the rank consequence this report INFERRED. `github_issues.json` now holds `wsjf_as_published: 2.88` plus a `wsjf_note`. |
| B-19 | **STILL OPEN** | `product-sequencing-v2.md:187` still publishes FR-9a at size 5 / WSJF **4.60**, unstruck. The file is unchanged since `7699e89`. |
| B-09, B-18, B-20 | **STILL OPEN** | Re-verified by opening each anchor on 2026-08-02; see the corrected addresses in section 2. |

**The point ledger has moved and this report's figures are superseded.** This report states 111 points
(69 SOURCED + 34 ASSUMED + 8 RE_ESTIMATED). MEASURED 2026-08-02 by recomputing from
`github_issues.json`: **45 SOURCED + 24 SOURCED_SET_SPLIT + 26 ASSUMED + 11 RE_ESTIMATED = 106
points**, 37 issues, 1 unsized (V2-018). `sprint_plan.md` agrees, stating "69 SOURCED + 26 ASSUMED +
11 RE-ESTIMATED = 106 points". **`github_issues.json`'s own `meta.totals` block still reads
`assumed_points: 34`, `combined_points: 111`, `reestimated_points: 8` -- it now disagrees with its own
enumeration.** That file was being written by another agent during this pass and was not modified
here; the disagreement is reported, not fixed, and may be transient.

**Not re-audited.** B-04 through B-08, B-10, B-12, B-16 and B-17 were not re-checked in this pass.
Their absence from the resolved table means only that -- not that they are open.

---

## Evidence labelling

| Label | Meaning |
|---|---|
| MEASURED | Checked against disk, git, or the live GitHub API by this pass, now. |
| CITED | Read from an artifact. Not independently re-derived here. |
| INFERRED | Derived by reasoning over MEASURED or CITED inputs. The derivation is stated. |

An unlabelled number in this document is a defect. Report it.

---

## 1. Can batch A actually start?

Batch A is 8 open issues. Enumerated: **#256 (V2-001), #258 (V2-002), #259 (V2-003), #260 (V2-004),
#261 (V2-005), #262 (V2-006), #263 (V2-007), #264 (V2-008)** -- 8 items, listed. Issue #257 is a
closed duplicate of #256 and is excluded; the `batch:A` label returns 9 rows because it still carries
the closed duplicate. MEASURED via a per-batch label listing that returned 9 rows, under the observed
25-row page cap, so complete.

| Issue | Key | AC an implementer could hold someone to? | Routed agent, persona liftable? | Unmet blocker? | Can start today? |
|---|---|---|---|---|---|
| #256 | V2-001 | Yes, 4 items, file-existence and section-unedited checks | solution-architect, agent.md exists | none | **YES** |
| #258 | V2-002 | Yes, 4 items, three count sources must agree + 2 scripts exit 0 | automation-engineer, agent.md exists | none | **YES** |
| #259 | V2-003 | Yes, 6 items, all mechanically checkable | harness-evaluation-engineer, agent.md exists | none for the BUILD; `closes_after` V2-015, V2-027 for the RUN | **YES, build only** |
| #260 | V2-004 | 3 items, but **AC3 is unsatisfiable as written** (B-03) | business-analyst-agent, agent.md exists | none encoded | **Premise false -- see B-01/B-02** |
| #261 | V2-005 | Yes, 3 items | business-analyst-agent, agent.md exists | **V2-004** | NO |
| #262 | V2-006 | Yes, 2 items | business-analyst-agent, agent.md exists | **V2-005** | NO |
| #263 | V2-007 | Yes, 2 items | business-analyst-agent, agent.md exists | **V2-005** | NO |
| #264 | V2-008 | 2 items, but the **count is contested** (B-06) | automation-engineer, agent.md exists | **V2-006, V2-007** | NO |

**The D1 set is a four-level serial chain**, not a parallel batch:
`V2-004 -> V2-005 -> {V2-006, V2-007} -> V2-008`. It carries 18 of batch A's 23 points. MEASURED from
`github_issues.json` `blocked_by` fields.

`sprint_plan.md` states: *"Everything here has zero blocking dependency on any other batch. Batch A is
the only batch that can start today."* That sentence is literally accurate -- it scopes the claim to
*other batches*. But the batch A table has no `blocked_by` column, so a reader staffing batch A in
parallel finds 4 of 8 immediately blocked. Recorded as **B-04**.

### The blocking finding: V2-004's premise is false

**MEASURED.** `docs/reports/policy-implementation-audit-v2.md` **exists**: 507 lines, 28,780 bytes,
committed as `bf92747` on 2026-08-01 at **17:23:00 +0530**.

Four artifacts assert it is absent, plus the live issue body:

| Artifact | What it says |
|---|---|
| `github_issues.json` V2-004 `build_status` | "verified ABSENT on disk 2026-08-01 by this pass" |
| `sprint_plan.md` batch A section | "does not exist" |
| `sequencing_risks.md` R-6 | "Verified independently by this pass, 2026-08-01: **ABSENT**" |
| `SRS.md` SS 3.1, the **"Build status"** paragraph opening *"Verified absent on disk on 2026-08-01:"* (line 157) | names it among files verified absent |
| live GitHub issue #260 | created from the above |

The timeline, MEASURED from git and the GitHub API:

```
17:08:00 +0530   7b29820   sprint plan + 37 issue drafts + sequencing risks committed
                           ("verified ABSENT" was TRUE at this moment)
17:23:00 +0530   bf92747   the audit file is written and committed  <-- premise flips here
17:43:28 +0530   (12:13:28Z) GitHub issue #260 created, carrying the now-false premise
```

The assertion was true for **15 minutes**. The issue was filed on GitHub **20 minutes after** it
became false. This is correction class #14 (backward propagation) reproducing itself in the sprint
artifacts -- the exact class the project has caught 8 times already.

**But the file does not satisfy the issue either.** MEASURED against V2-004's three ACs:

- **AC1** ("exactly 46 policy rows") -- the file has 9 table blocks. The policy enumerations are
  **four separate tables of 18 / 11 / 8 / 8 rows**, plus one STALE-TOPOLOGY policy named in prose.
  Not one 46-row matrix. The counts do reconcile to 46 (18+11+8+8+1+0), and each table states its own
  row count, so the file is internally sound -- it just is not the artifact AC1 describes.
- **AC2** ("each row has a non-empty Evidence cell citing file:line or an explicit NONE") -- only the
  18-row ENFORCED table has an `Enforcement point` column. The PARTIAL (11), CONTRADICTED (8) and
  DOCUMENTED-ONLY (8) tables are **2-column** and carry no evidence cell. 27 of 46 rows fail AC2.
- **AC3** ("the header states the read pass covered the corpus line-by-line, not just a metadata
  scan") -- the header states the **opposite**: *"Scope of this pass: consolidation plus
  spot-verification, NOT re-analysis."* Its section 8 states *"41 of the 46 individual classifications
  were not re-verified."*
- V2-005's 7-column requirement is also already unmet: the string `Post-plugin` occurs **0 times** in
  the file, and **no table exceeds 4 columns**.

So V2-004 is neither done nor cleanly startable. Recorded as **B-01** and **B-02**.

### AC3 names a directory that cannot yield 46 rows

**MEASURED.** V2-004 AC3 requires attesting to a line-by-line read of `~/.claude/policies/`.

| Tree | Contents |
|---|---|
| `~/.claude/policies/` | 44 `.md` recursively across 5 subdirectories; 10 are `README.md`, 2 are non-policy summaries -> **32 policy documents** |
| `docs/policies/` | **46** `.md`, flat |
| `policy_enforcement_raw.json` | **46** records |

**18 of the 46 policies named in `docs/policies/` do not exist in `~/.claude/policies/`** (enumerated
in `blockers.json` B-03). Seven names exist live that are not in `docs/policies/`, three of which are
the policies ADR-009b deletes permanently.

AC1 demands 46 rows; AC3 demands the evidence come from a tree holding 32 policies. The two criteria
cannot both be met. This lands on all five D1 issues. Recorded as **B-03**.

*Method note:* my first probe of this directory used a non-recursive glob and returned 0 files. That
result was wrong and was discarded, not reported. The figures above are from a recursive `find`.

---

## 2. Cross-artifact disagreements

Hunting the two dominant classes specifically: **(a) a summary count disagreeing with its own
enumeration**, and **(b) backward propagation**.

### Class (b) -- backward propagation

1. **The V2-004 absence claim**, standing in 4 artifacts plus the live issue after the file was
   committed. See section 1. **B-01.**
2. **Corrections #23 and #24 are unowned and un-propagated.** MEASURED: `CLAUDE.md:25` still reads
   *"578 classes, 3,985 methods, 4 languages (Python/Java/TS/Kotlin)"*, repeated at `:190`, `:248`,
   `:250`; `CHANGELOG.md:433`; `ADR-002-call-graph-intelligence.md:51, :72, :96`;
   `PIPELINE_ARCHITECTURE.md:137, :212`. All five publishing documents still carry both false claims.
   MEASURED: searching `github_issues.json` for `578`, `3,985`, `3985`, `4 languages`, `Kotlin` and
   `TypeScript` returns **NO ISSUE** for every term. V2-037 covers only the version string. True
   figures per the correction record: 480 / 3,506, and zero Java/TS/Kotlin files ever. **B-07.**
3. **SRS.md's risk table still directs an implementer at the dead constant.** In `SRS.md` section
   **`## Risks & Mitigation`**, the row beginning **`| Large codebase exceeds CallGraph limits |`**
   (line 1122) reads
   *"MAX_FILES=300, MAX_FILE_SIZE_KB=100 in `parsers/config.py`"* as the live mitigation -- correction
   #22's dead code, in the requirements document of record. The same file corrects this error
   thoroughly under **`**FR-21:**`** in SS 3.1 and under **`### Revised Acceptance Criterion for
   FR-21`** (lines ~267-289 and ~840-919) and explicitly DROPS `parsers/config.py` from the FR-9a
   assertion set at `:820`. **One file both corrects and repeats the defect.** **B-09.**
4. **`CLAUDE.md:151` claims `docs/policies/` mirrors `~/.claude/policies/`.** MEASURED false: 18
   absent, 7 extra. **B-08.**

### Class (a) -- summary count vs its own enumeration

5. **V2-008's "25 capabilities" vs `capability_loss.md`'s 27 rows.** MEASURED: the file holds three
   tables of **16 + 9 + 2 = 27** data rows. V2-008 AC1 and SRS NFR-10 say **25**. `REVIEW-INDEX.md`
   section 5 describes the same file as "14 PreToolUse gates, 9 PostToolUse capabilities" = **23**.
   Three counts for one file.
   **It reconciles**, but only under an unstated rule: 25 = 14 + 9 + 2, excluding PreToolUse rows 15
   and 16 -- "Warm-daemon fast path" and "PolicyRegistry", the latter explicitly tagged
   *"FR-9 (mechanism)"*. V2-008 AC2 mandates *"a script cross-checks the 25 names against the matrix
   and fails if any is missing"*. A script parsing the tables gets 27 and fails on two rows never
   meant to be in scope. The exclusion rule appears in no AC. **B-06.**

### Class (b) continued -- the V2-009 / FR-9a correction cluster

Both recent corrections to V2-009 (#265, batch B) propagated incompletely. Every row below is
MEASURED; the load-bearing ones were re-verified independently of the probe that found them.

**The 5 -> 8 re-point (commit `c4fd55d`, 2026-08-02):**

6. **`issue_key_map.json` still holds V2-009 at `size: 5`, `size_provenance: "SOURCED"`.** MEASURED
   by comparing all 36 sized entries against `github_issues.json` key-by-key: **V2-009 is the only
   mismatch of 36**. Summing each file's sizes gives **108 in `issue_key_map.json` against 111 in
   `github_issues.json`**. The value `RE_ESTIMATED` does not appear anywhere in the key map, so
   fixing the number alone leaves the provenance wrong. This is the file the routing layer consumes.
   **B-11.**
7. **V2-009's issue body and AC contradict its own size field.** MEASURED: `size: 8`, label
   `size:8`, while the body reads *"SIZE FLAG: 5 points ... deliberately NOT re-pointed here"* and
   acceptance criterion item 10 of 14 reads *"this issue's size 5 ... The size field is deliberately
   UNCHANGED here."* Both false against the object containing them. **B-12.**
8. **`sprint_plan.md` ASSUMPTION A3 still says "74 sourced points" and "the two totals".** A5,
   directly beneath it and added by the same correction, says 69 and "all three totals". The document
   says 69 in five other places. Two adjacent rows disagree. **B-13.**
9. **WSJF was never recomputed.** 23/5 = 4.60; 23/8 = 2.875. Five sites still publish 4.60, only one
   of which (`wsjf_as_published`) is defensibly labelled. Quarantined by section 5.6's *"Where WSJF
   IS load-bearing in this plan: nowhere"*, so wrong but not load-bearing. **B-15.**
10. **Both Phase 7 routing artifacts carry the stale flag** *"the 5-point estimate does not hold"* --
    and MEASURED, both were **regenerated twice on 2026-08-02 after the re-point** (`9a658eb`, then
    `6d48371`), carrying it forward each time. **B-16.**
11. **`product-sequencing-v2.md:187`** publishes size 5 / WSJF 4.60 unstruck, the only superseded row
    in its table not annotated to the table's own convention. **B-19.**

**The FR-9a acceptance-criterion rewrite (commit `92a9a5d`, 2026-08-01):**

12. **`sprint_plan.md`'s "Still open" paragraph is false on all three targets it names.** It claims
    the amendment *"did not propagate to `prd-v2.md` section 5, `SRS.md:736`, or the ADR-013 bodies at
    `hld_v2.md`."* MEASURED via `git show`: **this paragraph was added by the correction commit
    `c4fd55d` itself.** `prd-v2.md` and `SRS.md` had been corrected the previous day by `92a9a5d`;
    `hld_v2.md` was corrected by `14f742a` at 07:50:31, **four minutes after** `c4fd55d` at 07:46:21.
    `hld_v2.md:444-445` now reads *"[CORRECTED Phase 5] 17 truncation sites exist; exactly TWO bind."*
    A correction commit introducing a fresh stale claim about the propagation it was performing.
    **B-14.**
13. **`sequencing_risks.md` R-4 describes the AC in the present tense as unamended** -- *"not against
    the four the AC names"*, and *"The amendment IS an owner decision and is a prerequisite to closing
    V2-009 correctly."* MEASURED: the file has not been touched since `7b29820`, so no part of R-4
    reflects the amendment. Its R-14 summary row also records the AC as testing *"discovery, not path
    enumeration"*, which the new clause (C) directly contradicts. **B-17.**
14. **The four-site framing survives unmarked in SRS.md's normative text.** Addressed by anchor,
    because every one of these moved while this report was open. MEASURED 2026-08-02:
    - the **`**FR-21:**`** SHALL statement in SS 3.1 (line 267) still requires the fix *"at all four
      known truncation sites"*;
    - the paragraph beginning **`The four sites, as corrected:`** (line 285) still enumerates them,
      retaining `config.py:11` as item 4;
    - the **`| FR-21 |`** row of **`### Acceptance Criteria for the v2.0.0 Requirements`** (line 748)
      still reads *"Each of the 4 named sites"*;
    - the sentence containing **`FR-21's four-site closure requirement`** (line 951) refers to it.

    The revised 14-item criterion is appended under **`### Revised Acceptance Criterion for FR-21
    (APPENDED 2026-08-01, per rules/44 section 4.2)`** (line 840), but none of those four locations
    carries an inline pointer to it. Same at `product-sequencing-v2.md` (unchanged since 7699e89):
    `:578, :615, :718`. Retention is correct under rules/44's append-only rule; the defect is the
    missing supersession marker at the point of use. **B-18.**
15. **Three artifacts cite `SRS.md:736` for the FR-21 acceptance criterion; it has never been that
    row.** MEASURED 2026-08-02: line 736 is now a table separator (`|---|---|`). The FR-21 row is the
    **`| FR-21 |`** row of **`### Acceptance Criteria for the v2.0.0 Requirements`**, currently line
    **748**. Verified against `git show 92a9a5d^:SRS.md` that 736 was the FR-17 row before the append
    too, so the citation was already wrong when written -- pre-existing, not drift. **B-20.**

The criterion itself is sound where it landed: MEASURED, the `acceptance_criteria` array has exactly
**14 items**, and `sprint_plan.md` is the only artifact stating a count -- it says 14, correctly. No
artifact miscounts it.

### Where I looked and found nothing

- **The point ledger.** I recomputed every batch from its own enumeration: 69 SOURCED (45 pure + 24
  SET_SPLIT) + 34 ASSUMED + 8 RE_ESTIMATED = **111 points, plus 1 unsized (V2-018)**, and 37 issues.
  Every figure matches `meta.totals` exactly, including the V2-009 re-point arithmetic (5 left
  SOURCED, 8 entered RE_ESTIMATED, net +3, 108 -> 111). Batch A's own "5 SOURCED + 18 ASSUMED = 23"
  reconciles. No discrepancy found.
- **`routing_table.md` vs `routing_map.json`.** All 37 per-issue sections parsed and compared on issue
  number, confidence and primary agent: **0 mismatches**, tally 29 HIGH / 8 MEDIUM matching meta.
- **The audit file's internal arithmetic.** 18+11+8+8+1+0 = 46, each table stating its own row count,
  the single STALE-TOPOLOGY policy named. Internally sound.
- **The 14-item AC itself.** MEASURED: the `acceptance_criteria` array has exactly 14 elements, and
  the only artifact stating a count says 14. No miscount found.

---

## 3. Is the dispatch contract executable?

**Yes. This is the cleanest area of the plan, and it was checked exhaustively rather than sampled.**

| Check | Method | Result |
|---|---|---|
| Every routed agent has a real `agent.md` | Resolved all **37** `primary_agent_md_path` plus all **36** `supporting_agents[].agent_md_path` against the library root with `os.path.isfile` | **73 of 73 exist. 0 missing.** |
| Agents exist in the catalogue | Membership in `agents_all.json` (508 agents) | 26 distinct agents, **0 misses**; the `meta.distinct_agents` list matches the set actually referenced in both directions |
| Skills exist | Membership in `skills_all.json` (996 skills) **and** `SKILL.md` on disk | 50 distinct skills, **0 misses** in either check |
| The gate is live | `hooks/pre_tool_enforcer/policies/agent_persona.py` exists, loaded at `core.py:177`, registered in the dispatch table at `core.py:468`; `PreToolUse` registered in `~/.claude/settings.json` | **Live and enforcing** -- it blocked this pass's own tool calls during the audit |

**No routing row points at a missing agent.md.** Every persona the contract demands can be lifted from
a file that exists.

*Method note:* an earlier regex probe of `routing_table.md` matched only 4 rows, because that file is
section-structured rather than row-structured. That probe was discarded as non-exhaustive rather than
read as "4 rows found". The 37/37 figure above is from a section parse.

---

## 4. State of the known open items

| Item | State | Detail |
|---|---|---|
| Push gate uncovered after FR-4 until **both** V2-016 and V2-025 are built | **Correctly stated; encoded for the three keys it names** | MEASURED: V2-027 `blocked_by` = `['V2-016','V2-024','V2-025','V2-006','V2-031']`, mirrored in `issue_key_map.json` as `[272, 280, 281, 262, 287]`. Both remain DESIGNED, NOT BUILT. R-1 states plainly the constraint has **no mechanical enforcement until V2-025 itself lands**. **Gap: V2-017 is omitted -- see below.** |
| **V2-017 dependency gap** (new finding) | **DRIFTED** | MEASURED: V2-017 (ADR-020 PREVENT/DETECT layers) is **absent from V2-027's `blocked_by`**, and **absent from V2-026's** despite V2-026's body stating *"Every command built here must carry the ADR-020 layer-2 start-up check delivered by V2-017"*. V2-017 appears in exactly one `blocked_by` in the whole file (V2-036). Its ordering before V2-027 rests only on batch letter D < G, and batches are explicitly "a topological ordering, not a schedule" permitting intra-batch parallelisation. **B-05.** |
| FR-25 / FR-26 PROPOSED, unfunded, no issues | **Confirmed, no drift** | MEASURED: no issue in `github_issues.json`, `issue_key_map.json` or `routing_map.json` implements PRD FR-25 or FR-26. All apparent hits are the unrelated **SRS** FR-25/FR-26 (V2-014, V2-015), and both bodies carry explicit COLLISION WARNING text. Listed in `meta.not_drafted` and `sprint_plan.md` section 6. |
| V2-016 MEDIUM for two reasons; Path C is one-shot | **Correctly stated, and the timing IS encoded** | V2-016's body names Path C in scope *"at the only moment it can be performed"*, and **acceptance_criteria item 4** repeats it, correctly labelled HLD-sourced not PRD/SRS-sourced. `capability_gaps.md:229-231` states Path C has *"no owner in the library, new agents included."* Residual risk is routing-side only: the `mcp-base`/`AtomicJsonStore` reuse instruction and the Path C timing must both be supplied as prompt notes. |
| FR-7 must precede FR-5 | **Correctly stated and enforced by the graph** | MEASURED: V2-028 (#284) `blocked_by` = `['V2-026']` (#282), cross-referenced 284 <- 282. Batch order F < G alone would **not** guarantee it. V2-028's AC also encodes the dependency in its own wording, and R-14 records this violation as self-detecting *"immediately and loudly"* -- unlike R-1. |
| WSJF inputs are single-pass, never cross-checked | **Correctly stated and correctly quarantined** | `sprint_plan.md` 5.6: *"Where WSJF IS load-bearing in this plan: nowhere."* MEASURED: V2-004..V2-008 carry `wsjf_as_published: null`, so the contested D1 chain has no WSJF input at all. The three orderings resting on small deltas are each named and each resolved by `blocked_by`. |

---

## 5. What will break first

**V2-004 (#260) will be closed on the file that already exists, and it will take V2-005 through
V2-008 with it.**

The argument:

1. **Week one is batch A.** The plan says it is the only batch that can start today, so this is where
   the first work happens.
2. **V2-004 is the root of 78% of batch A.** 18 of 23 points sit in a four-level serial chain
   downstream of it. Nothing in that chain can be checked independently of it.
3. **The issue tells the implementer the file is absent. It is present.** The fastest available
   reconciliation for someone who finds a committed, 507-line, authoritative-looking document that
   the issue says should not exist is *"the issue is stale, the work is done."* That reading is
   reinforced by AC1 being half-true: the file exists, and its policy enumerations really do total 46.
4. **Nothing mechanically distinguishes done from not-done.** AC2 and AC3 do fail -- but AC2's failure
   requires noticing that three of four tables are 2-column, and AC3's failure requires reading the
   file's own scope statement against a criterion that names a directory (`~/.claude/policies/`) which
   does not hold 46 policies anyway. An implementer who resolves the AC3 contradiction by ignoring it
   -- the natural move, since it is unsatisfiable -- has removed the one criterion that would have
   caught the premature close.
5. **The plan predicted this exact failure and the prediction went stale.** R-6 names both modes:
   *"either 18 ASSUMED points of real work are missing from every downstream estimate, or five issues
   (V2-004 through V2-008) are phantom scope that will be closed as already-done and skew any velocity
   measurement taken from them. Both failure modes corrupt the first velocity figure this project ever
   produces, which is the one figure every later forecast will be anchored to."* R-6 resolved the
   question by asserting the artifact is absent -- an assertion that became false 15 minutes after it
   was committed. **The control built to catch this failure now argues for the wrong branch.**
6. **There is no velocity data to contradict it.** `capacity_statement`: *"NO velocity data exists for
   this project."* Week one's output **is** the anchor. Closing V2-004..V2-008 as already-done books
   23 points against roughly 5 points of real work -- a ~4.6x inflation on the first and only
   calibration point every later forecast inherits.

The competing candidate -- an implementer regenerating the audit and destroying section 3's retraction
of the false 46/46 figure, section 6's citation-defect record and section 8's seven-item limits list
-- is more destructive but less likely, because it requires deliberate action where the premature
close requires none.

**The cheapest thing that prevents it:** rule on B-01 before batch A is staffed, and restate V2-004 as
*extend the committed audit*, with an explicit do-not-regenerate instruction and a corrected AC3.

---

## 6. What I could not verify

- **The live GitHub issue bodies.** The `github-api` MCP server exposes no `get_issue` and no
  `list_comments` tool. Every body-level finding here is against `github_issues.json`, the recorded
  source the bodies were created from. I could not confirm the live bodies match it.
- **Whether the 26 cross-reference comments were duplicated** by the non-idempotent POST retry. Same
  missing tools. `issue_key_map.json` records the same limitation.
- **Whether the POST-retry fix is live.** `issue_key_map.json` states commit `33af037` requires an MCP
  server restart that did not happen, so every write in the issue-creation run was made under the
  unfixed client. I did not re-test it.
- **The 41 of 46 policy classifications** the committed audit itself records as CITED and not
  re-verified. This pass did not re-derive them either.
- **Batches B through H were not swept for stale on-disk premises.** B-01 is a premise-staleness
  defect found in batch A because batch A is what I was asked to try to start. The same class may
  exist elsewhere. This is the largest unexamined area in this report.
- **Which tree `get_policies_dir()` reads at runtime.** B-03 and B-08 both hinge on it; resolving it
  requires executing the resolver, which I did not do.
- **The ADR-013 bodies inside `hld.md` and `hld_v2.md`** were spot-checked at the corrected clause
  only (`hld_v2.md:444-445`). I did not read either 1,976-line HLD in full, so superseded four-site
  framing may survive elsewhere in them.
- **`sprint_plan.md`'s own section-2 size tables** were not audited row-by-row. I recomputed every
  batch total from `github_issues.json` instead. Both routes agree on 111 points across 37 issues,
  which is strong evidence but is not the same as a line-by-line read of the plan's own tables.

---

## Blocker summary

| ID | Severity | Title | Issues affected |
|---|---|---|---|
| B-01 | **BLOCKER** | V2-004's premise false: the artifact it declares ABSENT is committed | #260, cascades to #261-#264 |
| B-02 | **BLOCKER** | The existing audit satisfies none of V2-004's three ACs | #260, #261 |
| B-03 | **BLOCKER** | AC3 names a tree holding 32 policies while AC1 demands 46 rows | #260-#264 |
| B-04 | HIGH | Only 4 of 8 batch-A issues have an empty `blocked_by`; the plan's table hides it | #261-#264 |
| B-05 | HIGH | V2-017 absent from the `blocked_by` of both issues whose bodies require it | #273, #282, #283 |
| B-06 | MEDIUM | "25 capabilities" vs 27 enumerated rows vs 23 in REVIEW-INDEX | #264 |
| B-07 | MEDIUM | Corrections #23/#24 unowned; 5 documents still publish the false claims | none -- that is the finding |
| B-08 | MEDIUM | CLAUDE.md's `docs/policies` mirror claim is measured false | none |
| B-09 | MEDIUM | SRS.md `## Risks & Mitigation`, the CallGraph-limits row, still names the dead constant | #265 |
| B-11 | HIGH | `issue_key_map.json` holds V2-009 at size 5 / SOURCED; sums to 108 vs 111 | #265 |
| B-12 | HIGH | V2-009's body and AC item 10 assert "size 5" against its own `size: 8` | #265 |
| B-13 | MEDIUM | ASSUMPTION A3 says "74 sourced points"; A5 beneath it says 69 | none |
| B-14 | MEDIUM | The "Still open" paragraph is false on all 3 targets; added by the correction commit | #265 |
| B-15 | MEDIUM | WSJF never recomputed: 4.60 published at 5 sites, true value 2.88 | #265 |
| B-16 | MEDIUM | Both routing artifacts carried the stale 5-point flag through 2 post-correction regenerations | #265 |
| B-17 | MEDIUM | `sequencing_risks.md` R-4 states the AC amendment as still pending | #265 |
| B-18 | MEDIUM | Four-site framing unmarked in SRS.md's SHALL statement and FR-21 AC row | #265 |
| B-19 | LOW | `product-sequencing-v2.md:187` is the only unstruck superseded WSJF row | #265 |
| B-20 | LOW | Three artifacts cite SRS.md:736 for FR-21; the FR-21 AC row is elsewhere and always was | #265 |
| B-10 | LOW | SRS.md's Next Review date precedes its Last Updated date | none |

**20 blockers.** Counted from `blockers.json` rather than by hand, and enumerated in full:

| Severity | Count | IDs |
|---|---|---|
| BLOCKER | 3 | B-01, B-02, B-03 |
| HIGH | 4 | B-04, B-05, B-11, B-12 |
| MEDIUM | 10 | B-06, B-07, B-08, B-09, B-13, B-14, B-15, B-16, B-17, B-18 |
| LOW | 3 | B-10, B-19, B-20 |
| **Total** | **20** | 3 + 4 + 10 + 3 = 20 |

Machine-readable detail: `docs/phase-8-alignment/blockers.json`.

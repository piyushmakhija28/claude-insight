# Consensus Verdict -- Phase 2.5 (Cross-Validation Close), Loop Iteration 4

## Verdict: JOINT APPROVED

## Why

OPEN-7 is confirmed fixed by direct reading: `sa_defence.json` line 39 now explicitly retracts the
over-certain wording ("THE ADR-017 CI ASSERTION DOES NOT EXIST. No governance guarantee survives,
because none is running"), states the two-state truth (PROTECTED today via the live PreToolUse hook;
UNPROTECTED preventively and detectively after FR-4 unless both `register-mcp` and the CI assertion
land), and cross-references `PM-CRITICAL-3.true_state_now` as the entry it must stay consistent with.
Severity updated to "real weakening, disclosed -- and currently unmitigated."

**The validator was extracted from its stored JSON string and executed independently** (per the
explicit instruction: run the stored form, not any version quoted in prose):

```
unclassified_fields: []
count: 0
status: PASS
scope: 14 top-level sections (independently enumerated, matches the claim exactly)
```

Ran **four** negative tests, not one -- injecting an unclassified field into `meta`, `coverage_accounting_now`,
`stale_review_artifact_class_now`, and specifically **`decision_2_3_bundled_mcp_vs_nfr1_now`, the exact
section that held OPEN-7 last iteration**. All four were caught with correctly-pathed violation
messages. This is the load-bearing check: the coordinator's claim that the former defect site is now
under mechanical coverage was verified by injection, not accepted from the file's self-description.

No new instance of the defect class was found anywhere in the file this round.

## Mandatory checks

| # | Check | Result |
|---|---|---|
| 1 | ADR-019/ADR-020 structure | PASS (spot-confirmed) |
| 2 | Settled ADRs recorded, not reversed | PASS (spot-confirmed) |
| 3 | NFR-2 / ADR-016 unchanged | PASS (spot-confirmed) |
| 4 | BA 10/10, PM 9/9 arithmetic | PASS (unaffected by the rename) |
| 5 | Internal consistency, full re-run | **PASS** -- first clean pass in four iterations |
| 6 | Commands framed as design | PASS (spot-confirmed) |
| 7 | Path C labelled INFERRED | PASS (spot-confirmed, line 287 intact) |

## Ruling on the residual limitation

**Honestly stated and acceptable.** "The convention classifies FIELDS... it does NOT verify that a
`_now` field's content is actually current -- only that its staleness is checkable rather than
invisible" is precise about what was built and does not overreach. A naming schema plus a structural
validator makes omission of the record/claim distinction impossible (the same "inexpressible rather
than discouraged" design principle the file cites from ADR-013's non-optional argument and ADR-015's
three-way union) -- but no naming convention can verify a correctly-suffixed `_now` field's *content*
is true without a human or fact-check rereading it against source. That second failure mode remains
possible and is not claimed to be closed. This is exactly the same boundary iteration 3's WSJF ruling
drew between arithmetic exactness and judgment-input correctness -- drawn consistently across two
different conventions in this review, which is itself evidence the project understands the boundary
rather than asserting it once.

## Final state assessment

Four iterations, three rejections, each on a real, independently-verified defect (a stale ADR heading,
a guarantee documented as active when it did not exist, and a live instance of that claim inside an
honestly-disclosed exclusion zone). The response pattern shifted from single-sentence patches to a
genuine structural mechanism, verified this round by executing it and trying to break it four different
ways -- not by reading its description. Nothing broke. **JOINT APPROVED.**

## What was and was not examined

Scoped to the coordinator's single-file instruction: extracted and executed `validator_source` from
the live JSON, ran four negative tests (one more than described, targeting the exact former defect
site), and read the OPEN-7 fix location plus the full `_field_semantics_contract` block. Spot-confirmed
checks 1-4, 6, 7 against known-good anchors; no drift. Did not re-read `ba_findings_now`/`pm_findings_now`'s
full narrative content beyond confirming counts/IDs unchanged. `product-sequencing-v2.md` SS 2c-8
remain not read line-by-line by me personally -- carried forward from iteration 2's disclosure, not
silently dropped; that file is unchanged since. `hld.md` Sections 1, 2, 5, 6, 7, 8/STRIDE, 11, 13, 13a
remain not re-read fresh since iteration 1, consistent with no changelog entry pointing at them across
any iteration. JOINT APPROVED rests on the specific defect chain this review found and confirmed
fixed, plus the mandatory checks re-verified each round -- not on a claim of exhaustively re-examining
every artifact in scope from iteration 1 onward.

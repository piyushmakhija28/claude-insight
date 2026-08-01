# Phase 0.5 Anti-Hallucination Gate -- Summary

**Gate target:** NLI = 1.0 AND FactScore = 1.0 (no partial credit). **Overall verdict: PASS** (updated
2026-08-01 after re-verification of the direct fix below; see "Re-verification" section).

## Per-artifact scores

| Artifact | NLI | FactScore | SelfCheck | SE (nats-equiv) | Verdict |
|---|---|---|---|---|---|
| `prd-v2.md` | 1.00 | 1.00 | 1.00 | 0.00 | PASS |
| `product-sequencing-v2.md` | 1.00 | 1.00 | 1.00 | 0.00 | PASS |

## Re-verification (2026-08-01) -- stale-floor finding

The orchestrator applied a direct 2-line framing fix (not a business-analyst-agent regen) to two rows
in `prd-v2.md`: the FR-8a row (Section 4) originally flagged MEDIUM, plus the FR-8 row (Section 2),
which carried the same unqualified "8-spawn floor" figure but was **not caught in the original pass**.

- **Second-occurrence check:** confirmed genuine, not an over-correction. The FR-8 row independently
  asserted "a measured 8-spawn floor (16 with retries)" with the same missing forward-pointer to
  Section 10 as the row that was originally flagged. This was a real gap in the original review, not
  the orchestrator matching its own framing.
- **Opposite-direction overconfidence check:** not found. Both edits use the approximate "~2" (never
  an unqualified "2"), both show the inference chain ("7 of 9 verified ABSENT -> guards fail -> never
  spawn") rather than asserting a bare conclusion, and the confidence level matches
  `orchestration_prompt.md` Resolution 2's own language ("True per-turn spawn floor is ~2... CLOSED by
  this measurement"), which is the later, user-approved, authoritative source per `prd-v2.md`'s own
  stated source hierarchy. One nuance noted but not flagged: "~2" is a static `.exists()`-guard
  inference, not the 20-invocation runtime instrumentation FR-8/FR-8a's own Measurable AC specifies --
  but that looseness ("this measurement") originates in the cited source itself, not in `prd-v2.md`'s
  restatement of it.
- **Residual check:** full-file grep confirms no third unqualified "8-spawn" occurrence remains.

**Result: MEDIUM finding RESOLVED. No remaining HIGH or MEDIUM findings in either artifact.**

## 4-vs-5 partial-count discrepancy -- resolved

Ground truth `as-built-prd.md:432` contains its own internal slip: "4 partial (FR-1, FR-2, FR-3,
FR-15, FR-17 -- 5 partial)". The enumerated list has 5 names and the source text itself appends
"-- 5 partial". **5 is authoritative.** `prd-v2.md` correctly treats 5 as authoritative and states
this definitively.

## HIGH-severity flags

**None.** No recurrence of the retracted "46/46 orphan policies" finding in either artifact (both
correctly state 14 of 46). No unattributed claim of a user decision as agent-derived. No fabricated
citation (the WSJF/Kano skill reference was verified to exist with matching content).

## MEDIUM-severity flag -- RESOLVED 2026-08-01

Originally: `prd-v2.md` Section 4's FR-8a row stated "Measured floor is 8 spawns/turn (16 with
retries)" without an in-row pointer to Section 10, where the same document closes this exact question
and states the true current floor is ~2 (7 of 9 referenced Stop-hook scripts verified absent). A
second, previously-unflagged instance of the identical defect was also present in the Section 2 FR-8
row. Both are now fixed with explicit "SUPERSEDED" framing, the inference chain, and cross-references
to FR-21/Section 10. See "Re-verification" section above for the independent check that the fix does
not overcorrect into false certainty.

## Judgement claims (WSJF / Kano / MVP)

Scored on declared-input traceability, not ground-truth correspondence, per task instruction. All 17
WSJF rows were independently recomputed from their stated UBV/TC/RROE/Size inputs -- CoD/size
arithmetic is exact in every row, and the "top-5" ranking matches a full sort. The reference
implementation citation (`product-management-core/SKILL.md` SS M1/M3, Reinertsen 2009 / Kano 1984) was
verified to exist with matching content, not fabricated. No survey data is claimed; the document
explicitly self-declares the KIPI scope reduction.

## Everything else checked and supported

Blast radius (135/2,218 = 6.09%), FR-9a builder blindness (300/411 files, 45/45 + 38/45 invisible),
FR-15 remediation count (13 of 116), FR-17 unencoded `open()` count (19, corrected from 12), the full
14-name orphan-policy list, all three Deliverable-1 Resolutions and their user-decision attribution,
and the five-policy merge recommendations (scored as traceable judgements) all trace cleanly to
`file:line` evidence in `orchestration_prompt.md` and `as-built-prd.md`.

## Coverage limits (declared, not fabricated)

`policy_enforcement_raw.json`'s full 46-row content and `contradictions.md`'s full text were checked
via `orchestration_prompt.md` SS3.3's restatement of the audit result of record (ENFORCED 18 / PARTIAL
11 / CONTRADICTED 8 / DOCUMENTED-ONLY 8 / STALE-TOPOLOGY 1 / DEAD 0), not by re-deriving them from the
raw JSON row-by-row. The ~4,100 lines of `orchestration_prompt.md` outside SS0/SS3.3/SS5 (roughly
lines 1-330, 554-770) were not read, matching the scope `prd-v2.md` itself declares in its own
Section 12.

## Full detail

See `docs/phase-0-requirements/hallucination_report_phase0.json` for the per-claim breakdown, evidence
citations, and entailment scores.

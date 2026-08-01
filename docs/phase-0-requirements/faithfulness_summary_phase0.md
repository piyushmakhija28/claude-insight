# Faithfulness Scorecard -- Phase 0.5 Gate (2026-08-01, Revision 2: Re-verification)

**Artifacts:** `prd-v2.md` (475 lines), `product-sequencing-v2.md` (288 lines, revised)

## Scores (Revision 2)

| Artifact | F | AR | CP | CR | TruLens HM | SummaC | BERTScore F1 |
|---|---|---|---|---|---|---|---|
| prd-v2.md | 0.98 | 0.93 | 0.92 | 0.82 | 0.918 | 0.93 | 0.895 |
| product-sequencing-v2.md | 0.97 | 0.94 | 0.92 | 0.84 | 0.922 | 0.90 | 0.875 |

(Revision 1: prd-v2.md F=0.94, product-sequencing-v2.md F=0.89.)

## Gate Verdict: PASS (both artifacts, both gates)

Name-existence sweep unchanged: **0 fabricated names**, either revision. FactScore=1.0 gate: **PASS**
for both, modulo one still-open (not contradicted) numeric claim in prd-v2.md.

## R1 findings -- disposition

| # | Artifact | Finding | Status |
|---|---|---|---|
| 1 | product-sequencing-v2.md | Kano/KIPI citation inverted the skill's actual warning | **FIXED** -- framework removed (not relabeled); re-verified against SKILL.md directly: "SS 13, What Not to Do" heading at line 1307, quoted prohibition at line 1314, both now cited correctly and verbatim |
| 2 | prd-v2.md | `rules/model-fallback.md` cited as repo-relative | **FIXED** -- both occurrences now read `~/.claude/rules/model-fallback.md (global-only)`, matches filesystem |
| 3 | prd-v2.md | `orchestration_prompt.md` "4,478 lines" vs actual 4,600 | **FIXED** -- static count removed entirely with rationale (file amended continuously; cite sections not totals) |
| 4 | prd-v2.md | `path_resolver.py` "18 helper functions" vs actual 23 | **FIXED** -- now "23 top-level functions, verified 2026-08-01" + correct location `src/utils/path_resolver.py` |
| 5 | prd-v2.md | `SRS.md:131` cited for content actually at `SRS.md:133` | **WITHDRAWN** -- see position below |

## Position on the SRS.md:131 challenge

**Agree on the fact, both times.** Re-ran the line check directly: line 131 is exactly
`#### FR-9: Hook System` (heading); line 133 is the sentence containing the four-hook-types claim.
This is not in dispute -- the coordinator's verification and mine are identical.

**The disagreement was about citation granularity, not content.** `SRS.md:206` (the AC citation)
points to the exact line containing the exact claimed text -- verified exact match. `SRS.md:131`
points to the section's heading, two lines above the supporting sentence. I treated that as an
inconsistency in precision within the same sentence.

**Withdrawing this as a flagged-for-fix item, not retracting the fact.** Citing a section's heading
as the anchor for "this FR-9 entry states X" is a defensible, common documentation convention,
especially when heading and sentence sit inside one unbroken 3-line block with nothing intervening.
It was already scored "minor" in r1 and didn't move any number materially. The coordinator's read of
the citation convention is reasonable; I'm not re-asserting a low-value stylistic preference against
it. Full reasoning logged in `faithfulness_scorecard_phase0.json` -> `srs_131_position`.

## Confirmation: the 7 Kano mentions are rejection-record, verified independently

Grepped `product-sequencing-v2.md` directly (not taken on trust): 7 case-insensitive "kano" hits at
lines 16, 17, 18, 22, 116, 261, 262 -- the rejection statement + verbatim correctly-sectioned quote,
the "structurally unobtainable" reasoning, a cross-reference heading, and the rework note. A second
sweep for residual classification vocabulary (`must-be|delighter|indifferent|performance
feature|attractive|M/P/A/I|KIPI`) returns exactly one hit (line 23), itself part of the rejection
explanation, not an applied label. **Zero residual classifications confirmed.**

## Attribution routing check

All four r1 minor/moderate findings were correctly attributed to `prd-v2.md` in both my original JSON
(`per_artifact[0]`) and my original chat summary (explicitly prefixed "prd-v2.md" on findings 2-5).
The Kano finding was the only one attributed to `product-sequencing-v2.md`, correctly. If PM received
these routed to the wrong file, that happened downstream of this scorecard, not in it.

## New findings from the edits themselves

None material. Spot-checked the new FR-8a re-derivation in product-sequencing-v2.md SS 3 (gate
dependency, AC text, revealed-usage framing, cost-of-delay) against `prd-v2.md` directly -- the `<=2
spawn count unless a named exception` AC quote matches exactly, and the new WSJF row arithmetic
(4+6+8=18, 18/3=6.00) checks out. The MVP boundary genuinely narrowed (decision + instrumentation +
retirement now ship in v2.0.0; only a selected rebuild defers), not just re-worded.

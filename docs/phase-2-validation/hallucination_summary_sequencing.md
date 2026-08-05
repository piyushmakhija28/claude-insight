# Phase 2.5 Gate -- product-sequencing-v2.md (first-ever examination, 726 lines, full coverage)

**Gate verdict: RETRY.** NLI ~0.89, FactScore ~0.89 (gate requires 1.0, no partial credit).
One HIGH finding in an otherwise unusually clean, first-time-examined document.

## Item 1 -- WSJF arithmetic: ALL PASS

Recomputed 19 rows against WSJF=CoD/size, CoD=UBV+TC+RROE (Reinertsen 2009, correctly cited via
`skills/product-management-core/SKILL.md` SS M1). Every stated figure matches: NFR-3
(19/3=6.33), NFR-2 (23/8=2.88), NFR-1 (21/2=10.50), FR-4/FR-5 (20/3=6.67), register-mcp
(19/5=3.80, CoD=7+6+6), FR-18a (13/2=6.50, correctly struck-through/historical), plus all 13
unstruck Phase-0-baseline rows. Zero arithmetic defects anywhere in the document.

## Item 2 -- Kano: CLEAN, no surviving classification

Kano appears 6 times, all as the rejection record. SS0's correction note quotes the skill's
prohibition verbatim and explains why a proper survey is structurally impossible (one user, no
population). Zero occurrences of must-be/delighter/indifferent/KIPI/M-P-A-I anywhere.

## Item 3 -- Present-tense claim about a non-existent thing: ONE HIGH FOUND

**Line 721**: "unregister-mcp already covers the only genuine pre-uninstall opportunity" --
present tense, as if an existing capability. `unregister-mcp` is a PROPOSED ADR-019 command,
zero lines of code. This directly contradicts the document's OWN correct hedge 60 lines earlier
(line 403-404: "PROPOSED by ADR-019, not built; zero lines of code exist ... is designed to
reach those in full, once it exists"). This is the exact "already covers"/"already reads and
writes" pattern independently found in `pm_review.json` and `sa_defence.json` this cycle --
confirmed as a systemic drafting habit, now found here too. `doctor`, FR-25, FR-26 do not
appear in this document (correctly out of scope). ADV-012 is consistently hedged (3 mentions,
all "named"/"not adopted").

## Item 4 -- Stale positions / SS2b marking: PASS (addendum's sharpened concern)

**SS2b is adequately marked as superseded.** Its own header states "(DECIDED 2026-08-01 --
option (a) ... Sizing below is the original Phase 2.2 sizing, kept intact as the record ...)"
and repeats the outcome at its close. No reader could mistake it for live guidance.
**No pre-ADR-019 bundling assumption survives as live guidance** -- all 4 "minimum-viable
bundle" mentions are either inside the marked-superseded SS2b record or explicit
past/counterfactual tense (SS2c). **FR-18a's 6.50 does not survive anywhere** as a live
figure -- struck through in SS2a, retired-at-zero in SS2d and again in SS8's summary. FR-4/FR-5's
row is correctly explained as unchanged-in-its-own-numbers despite the surrounding ADR-019
context improving favorably. This is the best-defended area against the addendum's specific
concern.

## Item 5 -- count-vs-enumeration: no confirmed defect

7 gates / 6 remaining (7-1=6) consistent. Top-3 risks table has exactly 3 rows, with a 4th/5th
explicitly disclaimed as not-top-3. "9/9 answered" (line 378) could not be fully reconciled
against pm_review.json's exact finding count within budget -- flagged unverified, not scored as
a defect. The struck "4 unknowns" vs "5 items measured" is a correctly-preserved historical
figure, not a live miscount.

## Item 6 -- critical path: consistent everywhere

FR-9a->FR-10..13, FR-23->FR-4/FR-5, and the new FR-14->register-mcp->NFR-5's-4th-test chain are
each restated 4-8 times across SS0/2a/2c/6/7/8 with zero drift or contradiction found.

## PM's pre-emptive confidence flag

**PM flagged nothing in SS2b/2c/2d.** This pass's independent recomputation corroborates that
confidence -- all SS2c/SS2d figures check out exactly. The one defect found (item 3) is a
tense/wording slip, not an arithmetic or sizing error, and would not have been caught by a
sizing-confidence flag.

## Not examined

prd-v2.md/hld.md not re-read line-by-line (relied on prior-pass familiarity per addendum
priority); orchestration_prompt.md SS1.2/1.4/3.3 not re-read; "9/9" not fully reconciled;
FR-8a's capability-loss cross-check not independently re-verified; D1-D7 gate assignments not
recomputed against the canonical source, only cited.

Full detail: `docs/phase-2-validation/hallucination_report_sequencing.json`.

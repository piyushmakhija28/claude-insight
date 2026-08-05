# Phase 1.3 Faithfulness Gate -- hld.md (Pass 3)

**Verdict: no defect found in what was examined** (not "verified" -- matching SS 13a's own framing,
per instruction). All 5 checklist items pass. FactScore=1.0 for the items examined this pass;
not claimed for the whole document (SS 1-3/5-6/12(partial)/14 remain unswept). Scores
(evaluator-estimated, not machine-computed): F=0.96 AR=0.96 G=0.95 SummaC 0.97/0.85 BERTScore=0.98
FE=+0.44.

Scope this pass, per coordinator instruction: NOT re-checked -- counts 505/992/99, the 4 aliased
imports, the 5th truncator, ADR-012/016/017/018 citations, `push_gate`/`1bb4303` (all cleared pass 2).

## 1. EmptyByData deletion -- CONFIRMED, not load-bearing
Full-document grep for `EmptyByData`: exactly 3 hits -- ADR-015 prose (line 484, explains the earlier
draft's variant was deleted, not adjusted), SS 13a correction #4 (line 1454), changelog (line 1486).
The live SS 7.4 contract reads `DomainEdges = Parsed(edges) | ParseError(...)` -- genuine two-way
union, zero trace of a third variant anywhere else.

## 2. Container-first resolution -- CONFIRMED load-bearing
SS 7.4 states it as a numbered two-step procedure plus an explicit `invariant:` line ("unrecognised
container or edge-type key yields ParseError, NEVER an empty list"). ADR-015 has a dedicated "Why
container-first dispatch" paragraph tying the ordering directly to the root cause of the original
mismeasurement. Argued, not incidental.

## 3. Conformance test -- CONFIRMED as specified
`assert isinstance(result, Parsed)` then `assert len(result.edges) > 0` for all 99 domains. A
regression that dropped the `relationships` container form would make `read_domain()` return
`ParseError` for those 7 domains (per the SS 7.4 invariant), failing the `isinstance` check
immediately -- the test fails loudly on exactly the regression it's meant to catch.

## 4. 486 total + 7 per-domain counts -- CONFIRMED exact transcription
Independently re-read `len(data['relationships'])` from the raw JSON on disk this pass (fresh read):
agritech=85, insurance=84, supply-chain=81, embedded-firmware-kernel=63, mobile-engineering=60,
assembly-boot=59, systems-programming=54, sum=486. Matches the document's ADR-015 prose and changelog
entry exactly, same order, same numbers. Zero transcription errors.

## 5. SS 13a rescoped sentence -- CONFIRMED
Now reads: "No fabricated name or path was found in any file path or symbol reference examined by
these passes -- which is a statement about what was checked, not a guarantee about the whole
document." Directly replaces the pass-2-flagged unqualified version.

## Still weak in the ADR-015 rewrite (none are factual errors)
1. SS 7.4 names two `ParseError` triggers (bad container, bad edge-type key) but never explicitly
   routes a raw JSON-syntax failure (malformed/truncated/non-UTF8 file) through the same path --
   likely intended, but not spelled out, and this is exactly the class of implicit case that caused
   the original "empty" mismeasurement.
2. SS 7.4 uses the word "invariant" for two different guarantee strengths: the ParseError rule (a
   real structural/code-level invariant) and "zero domains in the library are empty" (an
   empirically-true-today fact enforced only by the conformance test re-running against the live
   corpus, not by the type system). Conflating the labels risks a future implementer treating the
   second as compiler-enforced.
3. The test pseudocode calls `observed_container_forms()`/`observed_edge_type_keys()` without
   defining them -- reasonable at HLD level, but an unspecified implementation detail worth noting.

## Not reached
Full 62/116-entry credential/spawn lists; exact "ten skills" list for the checkpoint-durability gap
(open since pass 1); SS 1-3/5-6/12(partial)/14. The "edge_type is the only non-standard key, all 10
cases" claim was presented as orchestrator-verified background, not one of this pass's 5 items, and
was not independently re-derived. Scores remain evaluator-estimated throughout.

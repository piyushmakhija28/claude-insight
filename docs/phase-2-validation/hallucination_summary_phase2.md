# Phase 2.4 Anti-Hallucination Gate -- hld.md draft-12 + Phase 2 validation set

**Gate verdict: RETRY.** NLI ~0.75, FactScore ~0.75 over audited scope (gate requires 1.0,
no partial credit). Three HIGH findings, one LOW.

## Item 1 -- Measured vs inferred: ADR-020's "Path C is safe"

**RULING: INFERRED, presented as measured. HIGH, load-bearing.** The spike (Item 4) measured
that (a) the spike's own bundled MCP server never touched `settings.json`'s `mcpServers` key
at all (tracked separately via the plugin manifest system), and (b) 25 PRE-EXISTING, unrelated
`mcpServers` entries survived the full install/uninstall cycle untouched. It never created an
entry via a plugin-owned write (what `register-mcp` would do) and tested whether uninstall
removes it. The HLD states "they survive plugin uninstall" as flat fact with zero hedging, and
ADR-020's table marks Path C "None needed" specifically because of this claim. The inference is
reasonable (uninstall doesn't touch the `mcpServers` key at all, regardless of entry origin) but
is not what was measured, and the document does not say so.

## HIGH findings

1. **ADR-020 Path C (above).**
2. **SS3 C4 Level 2 diagram is stale vs ADR-019/ADR-012**, both in the same document. Node
   `MCPJSON` still reads `.mcp.json -- minimal set (ADR-018)` -- directly contradicting ADR-019
   ("the plugin ships no `.mcp.json`"), whose own text marks ADR-018 "Superseded in part."
   Node `ROOT` still implies `PluginRootResolver` ascent is primary, not reflecting ADR-012's
   Phase 2 "STATUS UPDATE" reframing it as defence-in-depth (env var now primary). No
   `register-mcp`/`unregister-mcp` nodes appear despite this being new mandatory v2.0.0 scope.
   The diagram's own node-count arithmetic (21 of 50) is internally correct -- the content is
   what's wrong, not the count.
3. **sa_defence.json's coverage-completeness arithmetic does not reconcile.** Its own sentence
   ("BA filed 8, 6 relayed; PM filed 9, 6 responded to... omitted 4... All 4 are answered
   below") is self-inconsistent (8-6=2, 9-6=3, sum=5, not 4), and `addendum_findings`'s actual
   IDs show 3 BA + 2 PM + 1 non-BA/PM item, not "4" and not the 2-BA/3-PM split implied.
   `ba_review.json` has 10 findings on disk, not 8 as "BA filed" states; cross-referencing
   leaves `FIND-08` untracked anywhere in `sa_defence.json`. Mitigating: `FIND-08`'s underlying
   issue (FR-16 missing from HLD SS1.3) was independently confirmed fixed in live `hld.md`
   anyway -- but the "All 4 answered" completeness claim is false on its own terms.

## Item 3 -- pm_review.json stale-claim sweep

Known case (SS10 register-mcp step) correctly NOT flagged -- true when PM wrote it, fixed by
SA afterward. Found one **additional instance of the identical benign pattern**, in the sibling
document `ba_review.json`: FIND-08 says "NOT APPLIED... flagged for a future revision" about
FR-16 missing from HLD SS1.3 -- but SS1.3 was in fact fixed since. Same category, not a
hallucination, surfaced per the coordinator's request to check for other such cases.

## Item 4 -- count-defect-class sweep

hld.md's ADR-count line (7+10=17, 15 headings) and OAQ2's policy-disposition totals (5+5+5=15)
are both re-verified exact -- the sixth recurrence ADV-011 flagged was already fixed correctly.
Two new instances found: `prd-v2.md`'s header still says "Version: 1.1" while its own Change
Log's latest, already-applied row is "1.2" (LOW, cosmetic -- body content matches v1.2). And
`sa_defence.json`'s addendum arithmetic (HIGH, above).

## Item 5 -- NFR-3 survival argument: HOLDS

Verified against ADR-011's actual text: CheckpointManager (in-process, `step_decorator.py`
step-boundary writes) is the sole writer; `mcp-post-tool-tracker` is explicitly "a projection
... not an independent writer" per ADR-011 defect 2. `register-mcp` being opt-in therefore
loses only the per-tool-call progress query surface, never crash-recovery correctness. Both
`hld.md`'s new SS9 cross-NFR table and `sa_defence.json` state this identically and correctly.

## Not examined this pass

`product-sequencing-v2.md` SS2b/2c WSJF arithmetic not hand-recomputed; `advisory_items.json`
ADV-001..009; `orchestration_prompt.md` SS1.2/1.4/3.3 not re-read; `ba_review.json`'s
fr_coverage/ac_implementability/rtm_gaps sections; `sa_defence.json`'s
critical_items_fixed_in_session and ba_completed_work_noted_no_action arrays.

Full detail: `docs/phase-2-validation/hallucination_report_phase2.json`.

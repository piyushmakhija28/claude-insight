# Phase 2.4 Faithfulness Gate -- hld_v2.md (1802 lines, was 1551)

**Verdict: RETRY.** Zero non-existent names presented as existing, zero wrong line numbers. One
unhedged-certainty claim on a load-bearing safety point (Path C). Scores (evaluator-estimated, not
machine-computed): F=0.95 AR=0.96 G=0.94 SummaC 0.96/0.55 BERTScore=0.97 FactScore=0.96 FE=+0.40.

## Three commands + pre-push + FR-25: framing verdict
**register-mcp**: CORRECT throughout -- every occurrence under an ADR "Chosen:" block, inside SS 10
("Migration Design"), or in conditional voice ("for a user who never runs..."). **unregister-mcp**:
CORRECT, one weak sentence -- ADR-020 line 727 says it "already reads and writes settings.json
(ADR-019)"; the word "already" is loose but bounded by the (ADR-019) citation and section context;
recommend rewording to "is designed to". **doctor**: CORRECT -- only 2 occurrences total, both under
"Chosen:"/changelog. **git pre-push hook (ADV-012)**: CORRECT, explicitly disclaimed -- "named as the
option, not adopted here... Filed as ADV-012." **FR-25**: CORRECT and safest of all -- does not
appear in hld_v2.md at all (0 hits); exists only in advisory_items.json/pm_review.json/sa_defence.json,
every occurrence marked "(proposed)".

## Path C ruling: INFERENCE presented as fact -- MISLABELED
Measured (plugin_schema_spike.md item 3/4): the spike's own plugin used a bundled `.mcp.json` never
written into settings.json's `mcpServers` key; uninstall's structural diff shows **zero** changes to
any key except `enabledPlugins`/`extraKnownMarketplaces` -- 25 *pre-existing* mcpServers entries
survived byte-for-byte. NOT measured: whether an entry `register-mcp` itself writes into that same
key is treated identically when *that same plugin* is later uninstalled -- `register-mcp` doesn't
exist, so no such entry has ever been tested. The inference is well-grounded (uninstall doesn't touch
the key's contents at all, for anyone) but ADR-020 states "they survive plugin uninstall" as flat,
unhedged fact, unlike ADV-010's careful "flagged for awareness, not asserted as fact" hedge elsewhere
in the same document. **Load-bearing**: if wrong, uninstall silently removes the push gate with Path
C explicitly marked "None needed" for control. Recommend separating the measured fact from the
inference and adding a 6th spike item once register-mcp exists.

## Checkpoint/setup_wizard/prd-v2/spike checks -- all clean
5 new CheckpointManager citations (load_checkpoint_by_id:265, get_last_checkpoint:294,
load_checkpoint_metadata:239, delete_checkpoint:366, clear_all:386) all byte-exact; full method sweep
confirms "9 public + 2 private helpers" is exactly right. `setup_wizard.py:282` re-read this pass,
unchanged. prd-v2.md v1.2's 4 FR-9a truncation sites transcribed identically to prior-verified source
truth. `plugin_schema_spike.md` (334 lines) exists; all 4 sampled citations into it resolve exactly.

## Noticed, not verified (out of assigned scope)
ADR-012 was reframed between passes (env var now primary, per changelog draft-9) -- grounded in real
spike data (Item 2), not fabricated on inspection, but not on this pass's checklist and not
independently re-verified end-to-end. Not re-swept: 17-ADR count, byte-identity, SS10 step position,
register-mcp's 18-occurrence count (orchestrator-verified), pm_review.json staleness (known, moot).

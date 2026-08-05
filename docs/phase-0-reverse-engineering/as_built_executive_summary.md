# AS-BUILT Executive Summary -- claude-workflow-engine v1.21.4 (2026-08-01)

## Five things that most change what v2.0.0 should do

1. **Impact analysis is blind to the code it protects.** The call-graph builder is capped at 300
   files against 411 on disk. The entire Level-2 SDLC core (45 files) and 38/45 hook files are 100%
   invisible to it; 25% of the budget burns on `tests/`. Fix before trusting any CallGraph-driven
   v2.0.0 decision.
   **SITE CORRECTED 2026-08-01:** this originally cited `parsers/config.py` as the cap. That
   constant is **dead code, read by nothing**. The binding cap is
   `parsers/call_graph_builder_legacy.py:64` (enforced `:107`, `:118`), and a second cap,
   `parsers/graph_model.py:43` (`MAX_PATHS = 500`), survives fixing it. See
   `docs/phase-5-uml/callgraph_coverage_probe.md`.
2. **Three "always-on" maintenance policies are silent no-ops today, hooks aside.** Auto-commit,
   session-save, and session-pruning target `scripts/architecture/` subtrees that don't exist. Their
   `.exists()` guards fail with zero log trace, every turn -- already broken before any hook is touched.
3. **"46/46 orphan policies" was a briefing artifact, not a finding.** SRS.md was never fed to that
   KG build. Redone against SRS's real 15 FR/NFR entries: **14 of 46 (30%) are genuine orphans.** Six
   would stay orphaned even with perfect SRS coverage -- independently broken or out of SRS's scope.
4. **Two hook-removal casualties are real and specific.** Deleting PreToolUse/PostToolUse falsifies
   SRS FR-9's own acceptance criterion for 2 of 4 hook events, and removes the sole writer of the
   checkpoint state NFR-3 depends on. Blast radius to surviving code is genuinely zero -- but these
   two consequences are not, and aren't yet decided.
5. **Two measurement conflicts are unresolved -- don't let either get silently picked.** Stop-hook
   spawn floor: "8/turn assuming scripts exist" vs. verified-absent scripts (true floor maybe 2).
   Decomposability: 70%-of-subpackages import SCC vs. zero function-level SCCs / 708 fragmented
   communities -- no clean plugin boundary exists at precision despite the import graph looking
   monolithic.

## Three decisions being requested

1. **Fix or explicitly accept the CallGraph blindness** before v2.0.0 relies on it for anything --
   raise/remove `MAX_FILES=300`, or make discovery scope-aware, or accept the blind spot in writing.
2. **Decide the 3 already-broken maintenance policies separately from hook removal.** They are dead
   paths today regardless of FR-4/FR-5's outcome; fixing/demoting/deleting them is a distinct call.
3. **Decide who owns the SRS.md FR-9 rewrite.** v2.0.0's deliverable list doesn't include updating the
   acceptance criterion the hook deletion will falsify -- someone must own that edit in Workstream B.

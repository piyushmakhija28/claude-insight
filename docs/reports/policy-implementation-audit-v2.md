# Policy Implementation Audit v2 (Deliverable 1)

Generated 2026-08-01, reshaped 2026-08-02. The Deliverable-1 record for the 46-policy corpus:
one row per policy, with status, evidence, post-plugin plan, the basis for that plan, and
verification provenance. Consumed by V2-005 through V2-008.

## Provenance of this document, and what read pass it does and does not rest on

Stated first because V2-004 AC3 makes a specific claim about the read pass, and this
document must not assert one it did not perform.

**What was done.** The classifications come from the Phase C.2 Part B analysis pass, which
read all 46 files in the repository's `docs/policies/` and classified each against
`ast_call_graph.json` plus direct source reads. That analysis was approved by the project
owner. This document consolidates it into the required matrix shape, assigns a post-plugin
plan per row, and adds a spot-verification of 9 rows against live code. It deliberately does
**not** re-derive the status counts, because regenerating figures risks diverging from an
approved deliverable.

**AC3 is NOT satisfied by this pass, and is recorded as open rather than claimed.** AC3
requires the header to state that the read pass covered `~/.claude/policies/` line-by-line
rather than a metadata scan. This pass did not perform a line-by-line read of
`~/.claude/policies/`, and the underlying Phase C.2 pass read `docs/policies/` instead.
Writing a sentence asserting otherwise would document a guarantee that does not exist,
which is correction class #17 in `docs/REVIEW-INDEX.md`. The honest status is: **the read
pass covered the repository corpus `docs/policies/`, not the runtime corpus
`~/.claude/policies/`.**

**That distinction turns out to be material, not pedantic.** MEASURED 2026-08-02: the two
corpora are not the same set. See section 4. Anyone treating this matrix as a description
of what the running system enforces should read that section first.

## Evidence labelling

| Label | Meaning |
|---|---|
| MEASURED | Checked against disk or source by this pass. Reproducible from the stated file:line. |
| CITED | From a Phase 0 source artifact. Not independently re-checked here. |
| INFERRED | Derived from MEASURED or CITED inputs; the derivation is stated. |

The `Verification` column carries exactly these three values. A row that was not checked is
CITED. No row was upgraded to MEASURED merely because the column exists.

---

## 1. The 46-row policy implementation matrix

**Row count: 46.** Counted from the enumeration below, not asserted independently. The rows
were generated programmatically from the 46 records in
`docs/phase-0-reverse-engineering/policy_enforcement_raw.json`, with the row count asserted
at generation time, so a summary-versus-enumeration mismatch cannot arise here. That is this
project's most-caught defect class (corrections #9-13).

**Post-plugin plan vocabulary** is V2-005's set, spelled exactly as V2-005 spells it:
`keep-as-is` / `port-to-plugin` / `port-to-MCP` / `demote-to-advisory` / `delete`. A value
outside that set fails V2-005's review, so no other token appears in that column. **13 cells
are deliberately empty** -- see section 1.2 for why that is the correct outcome rather than a
gap to be filled.

Sorted alphabetically by policy filename, case-insensitive.

| # | Policy file | Status | Evidence | Post-plugin plan | Basis | Verification |
|---|---|---|---|---|---|---|
| 1 | `anti-hallucination-enforcement.md` | CONTRADICTED | `langgraph_engine/sdlc_pipeline/architecture/00-prompt-generation/anti_hallucination_enforcement.py:38-133`; zero importers repo-wide |  | Broken independently of de-hooking; the fix/delete/demote choice is a product decision no source makes | MEASURED |
| 2 | `architecture-script-mapping-policy.md` | CONTRADICTED | NONE as runtime code. `docs/policies/architecture-script-mapping-policy.md` is itself the only artifact; a reference document, not code |  | Broken independently of de-hooking; the fix/delete/demote choice is a product decision no source makes | CITED |
| 3 | `automatic-task-breakdown-policy.md` | ENFORCED | `hooks/pre_tool_enforcer/policies/task_breakdown.py:12` `check_task_breakdown_pending`, registered `core.py:455` `_BLOCKING_POLICIES` | demote-to-advisory | OAQ 2 row 6 | CITED |
| 4 | `callgraph-analysis-policy.md` | CONTRADICTED | `langgraph_engine/parsers/call_graph_builder_legacy.py:64` `MAX_FILES=300`, bound at `:76`, enforced `:107` and `:118`; second cap `parsers/graph_model.py:43` |  | Broken independently of de-hooking; the fix/delete/demote choice is a product decision no source makes | MEASURED |
| 5 | `code-graph-analysis-policy.md` | ENFORCED | `langgraph_engine/sdlc_pipeline/architecture/00-code-graph-analysis/code_graph_analyzer.py:340-637` (`build_graph`, `compute_graph_metrics`) | keep-as-is | judged: no hook coupling; enforcement is pipeline code de-hooking does not touch | CITED |
| 6 | `coding-standards-enforcement-policy.md` | ENFORCED | `langgraph_engine/standards/selector.py:114` `detect_framework`, `:202` `_detect_java_framework` (reach=True) | keep-as-is | judged: no hook coupling; enforcement is pipeline code de-hooking does not touch | CITED |
| 7 | `common-failures-prevention.md` | PARTIAL | `hooks/pre_tool_enforcer/policies/failure_kb.py:11` `check_failure_kb_hints`, called non-blocking at `core.py:517-523`; Stop-side script absent | port-to-MCP | OAQ 2 row 7 | CITED |
| 8 | `common-standards-policy.md` | ENFORCED | `langgraph_engine/standards/selector.py:449` `select_standards`, `:273` `load_custom_standards`, `:358` `load_framework_standards` | keep-as-is | judged: no hook coupling; enforcement is pipeline code de-hooking does not touch | CITED |
| 9 | `context-management-policy.md` | PARTIAL | `hooks/pre_tool_enforcer/policies/level1_sync.py:15` `check_level1_sync_complete`, registered `core.py:458`; token-budget code not located under this name | demote-to-advisory | OAQ 2 row 8 | CITED |
| 10 | `context-reading-policy.md` | ENFORCED | `hooks/pre_tool_enforcer/policies/context_read.py:14` `check_context_read_complete`, registered `core.py:457` `_BLOCKING_POLICIES` | demote-to-advisory | OAQ 2 row 9 | MEASURED |
| 11 | `cross-project-patterns-policy.md` | ENFORCED | `langgraph_engine/context_sync/architecture/pattern_detector.py:388` `detect_patterns`, `:525` `scan_all_projects` | keep-as-is | judged: no hook coupling; enforcement is pipeline code de-hooking does not touch | CITED |
| 12 | `documentation-update-policy.md` | PARTIAL | `langgraph_engine/sdlc_pipeline/nodes/closure_docs_summary_wrapper.py:62` `step7_project_documentation_update`, `:153` `step7_docs_update_node` | keep-as-is | judged: no hook coupling; enforcement is pipeline code de-hooking does not touch | CITED |
| 13 | `encoding-validation-policy.md` | PARTIAL | `langgraph_engine/preflight_guard/nodes.py:150-237` `node_encoding_validation` (reach=True, cc=17) | keep-as-is | judged: no hook coupling; enforcement is pipeline code de-hooking does not touch | CITED |
| 14 | `error-recovery-policy.md` | PARTIAL | `langgraph_engine/engine_logging/error_logger.py` `ErrorLogger.log_error` (reach=True, cc=3), `log_validation_result` | keep-as-is | judged: no hook coupling; enforcement is pipeline code de-hooking does not touch | CITED |
| 15 | `EXECUTION-SYSTEM-FIXES-SUMMARY.md` | DOCUMENTED-ONLY | NONE. Point-in-time changelog, not a policy with a runtime mechanism |  | No runtime mechanism to keep, port or delete; retaining it is a product decision no source makes | CITED |
| 16 | `file-management-policy.md` | DOCUMENTED-ONLY | NONE found |  | No runtime mechanism to keep, port or delete; retaining it is a product decision no source makes | CITED |
| 17 | `final-summary-policy.md` | ENFORCED | `langgraph_engine/sdlc_pipeline/nodes/closure_docs_summary_wrapper.py:70` `step8_final_summary_generation`, `:202` `step8_final_summary_node` | keep-as-is | judged: no hook coupling; enforcement is pipeline code de-hooking does not touch | CITED |
| 18 | `git-auto-commit-policy.md` | CONTRADICTED | `hooks/stop_notifier/core.py:74-96` spawns `scripts/architecture/03-execution-system/09-git-commit/git-auto-commit-policy.py`, which does not exist | delete | OAQ 2 row 10 | MEASURED |
| 19 | `github-issues-integration-policy.md` | PARTIAL | `langgraph_engine/sdlc_pipeline/github_lifecycle.py` `Level3GitHubWorkflow.step2_create_issue:125` (reach=False), `.step3_create_branch:294` (reach=False) | keep-as-is | judged: no hook coupling; enforcement is pipeline code de-hooking does not touch | CITED |
| 20 | `hook-system-policy.md` | ENFORCED | `hooks/pre-tool-enforcer.py` shim into `hooks/pre_tool_enforcer/core.py:453-469` `_BLOCKING_POLICIES` | delete | OAQ 2 row 1 | CITED |
| 21 | `implementation-execution-policy.md` | PARTIAL | `langgraph_engine/sdlc_pipeline/nodes/implementation_and_review_wrapper.py:84` `step4_implementation_note` (reach=True) | demote-to-advisory | OAQ 2 row 2 | CITED |
| 22 | `intelligent-decision-engine-policy.md` | CONTRADICTED | NONE found. Describes an "OpenRouter consolidation" never built; the systems it unifies were deleted in v1.13 |  | Broken independently of de-hooking; the fix/delete/demote choice is a product decision no source makes | CITED |
| 23 | `intelligent-model-selection-policy.md` | STALE-TOPOLOGY | NONE found under this description. One of its 5 inputs (plan-mode decision) was deleted in v1.13, so the retranslated question is unanswerable |  | Retranslated question is unanswerable (a v1.13-deleted input); nothing decides its fate | CITED |
| 24 | `INTELLIGENT-PROMPT-GENERATION-UPGRADE.md` | DOCUMENTED-ONLY | NONE. Point-in-time changelog |  | No runtime mechanism to keep, port or delete; retaining it is a product decision no source makes | CITED |
| 25 | `issue-closure-policy.md` | ENFORCED | `langgraph_engine/sdlc_pipeline/github_lifecycle.py:543` `step6_close_issue`, `:603` `_build_closing_comment` (both reach=True) | keep-as-is | judged: no hook coupling; enforcement is pipeline code de-hooking does not touch | CITED |
| 26 | `mcp-plugin-discovery-policy.md` | DOCUMENTED-ONLY | `langgraph_engine/state/state_definition.py:184` `mcp_plugins_path` -- a FlowState field only, no discovery logic |  | No runtime mechanism to keep, port or delete; retaining it is a product decision no source makes | CITED |
| 27 | `metrics-monitoring-policy.md` | PARTIAL | `langgraph_engine/metrics/aggregator.py` `aggregate_sessions:96`, `aggregate_step_performance:191`, `aggregate_llm_usage:307`, `aggregate_tool_usage:408` | port-to-MCP | OAQ 2 row 3 | CITED |
| 28 | `parallel-execution-policy.md` | DOCUMENTED-ONLY | NONE found as engine code. Describes calling-agent behaviour, not a pipeline capability |  | No runtime mechanism to keep, port or delete; retaining it is a product decision no source makes | CITED |
| 29 | `pr-code-review-policy.md` | PARTIAL | `langgraph_engine/sdlc_pipeline/github_code_review.py` `run_code_review:283`, `check_python_best_practices:53` (all reach=False) | keep-as-is | judged: no hook coupling; enforcement is pipeline code de-hooking does not touch | CITED |
| 30 | `proactive-consultation-policy.md` | DOCUMENTED-ONLY | NONE. Explicitly deprecated by its own text |  | No runtime mechanism to keep, port or delete; retaining it is a product decision no source makes | CITED |
| 31 | `prompt-generation-policy.md` | ENFORCED | `langgraph_engine/sdlc_pipeline/architecture/prompt_gen_expert_caller.py:159` `_build_filled_prompt`, `:253` `main` (reach=True) | keep-as-is | judged: no hook coupling; enforcement is pipeline code de-hooking does not touch | CITED |
| 32 | `quality-gate-policy.md` | ENFORCED | `langgraph_engine/sdlc_pipeline/quality_gate.py:637` `evaluate_quality_gate` (reach=True, cc=9), with `_evaluate_sonar_gate:142`, `_evaluate_coverage_gate:248` | keep-as-is | judged: no hook coupling; enforcement is pipeline code de-hooking does not touch | CITED |
| 33 | `recovery-policy.md` | ENFORCED | `langgraph_engine/preflight_guard/recovery.py:234` `fix_preflight_guard_issues` (reach=True, cc=45) | keep-as-is | judged: no hook coupling; enforcement is pipeline code de-hooking does not touch | CITED |
| 34 | `session-chaining-policy.md` | PARTIAL | `src/mcp/session_hooks.py`, `src/mcp/session_mcp_server.py` (`session_link`-adjacent surface, module reach=True); `clear-session-handler.py` named by the policy not found | keep-as-is | judged: no hook coupling; enforcement is pipeline code de-hooking does not touch | CITED |
| 35 | `session-memory-policy.md` | CONTRADICTED | `hooks/stop_notifier/core.py:104-127` spawns `scripts/architecture/01-sync-system/session-management/auto-save-session.py`, which does not exist | delete | OAQ 2 row 11 | MEASURED |
| 36 | `session-pruning-policy.md` | CONTRADICTED | `hooks/stop_notifier/core.py:131-181` spawns `archive-old-sessions.py` and `session-pruner.py` under `scripts/architecture/01-sync-system/`; neither exists | delete | OAQ 2 row 12 | MEASURED |
| 37 | `task-phase-enforcement-policy.md` | ENFORCED | `hooks/pre_tool_enforcer/policies/task_breakdown.py:12` `check_task_breakdown_pending` -- same point as row 3 | demote-to-advisory | OAQ 2 row 13 | CITED |
| 38 | `task-progress-tracking-policy.md` | PARTIAL | `hooks/post_tool_tracker/policies/task_tracking.py`, `.../task_breakdown_clear.py` (both present; reach not individually traced -- LOW confidence) | port-to-MCP | OAQ 2 row 14 | CITED |
| 39 | `test-case-policy.md` | DOCUMENTED-ONLY | NONE found as a distinct gate |  | No runtime mechanism to keep, port or delete; retaining it is a product decision no source makes | CITED |
| 40 | `test-generation-policy.md` | ENFORCED | `langgraph_engine/sdlc_pipeline/test_generator.py` `detect_language:39`, `detect_test_framework:61`, `_generate_python_tests:544` | keep-as-is | judged: no hook coupling; enforcement is pipeline code de-hooking does not touch | CITED |
| 41 | `tool-optimization-policy.md` | ENFORCED | `hooks/pre_tool_enforcer/policies/read_opt.py:8` `check_read_opt`, `grep_opt.py:8` `check_grep_opt`, registered `core.py:466-467` | port-to-MCP | OAQ 2 row 4 | MEASURED |
| 42 | `tool-usage-optimization-policy.md` | CONTRADICTED | No distinct point. Shares row 41's registration: `hooks/pre_tool_enforcer/policies/read_opt.py:8` `check_read_opt` and `grep_opt.py:8` `check_grep_opt`, registered once at `hooks/pre_tool_enforcer/core.py:466-467`, while this policy's own text claims "NO DUPLICATION" | delete | OAQ 2 row 15 | MEASURED |
| 43 | `unicode-fix-policy.md` | ENFORCED | `langgraph_engine/preflight_guard/nodes.py:62-147` `node_unicode_fix`, wired `orchestrator.py:657`, on the `START` edge at `:663` | keep-as-is | judged: no hook coupling; enforcement is pipeline code de-hooking does not touch | MEASURED |
| 44 | `user-preferences-policy.md` | DOCUMENTED-ONLY | `langgraph_engine/sdlc_pipeline/nodes/pre_nodes.py:191` `result['user_preferences_context']` -- a passthrough state field, not a learning function |  | No runtime mechanism to keep, port or delete; retaining it is a product decision no source makes | CITED |
| 45 | `version-release-policy.md` | ENFORCED | `hooks/pre_tool_enforcer/policies/push_gate.py:354` `check_push_version`, `:408` `check_push_clean_tree`, registered `core.py:464-465` | port-to-MCP | OAQ 2 row 5 | CITED |
| 46 | `windows-path-policy.md` | ENFORCED | `langgraph_engine/preflight_guard/nodes.py:240-323` `node_windows_path_check` (reach=True, cc=17) | keep-as-is | judged: no hook coupling; enforcement is pipeline code de-hooking does not touch | CITED |

### 1.1 Matrix integrity checks

All MEASURED by re-counting the table above.

| Check | Result |
|---|---|
| Data rows | **46** |
| Rows with a non-empty Evidence cell | **46 of 46**, zero blanks (AC2) |
| Evidence citing a real code `file:line` | **37** |
| Evidence stating an explicit NONE / no runtime mechanism | **9** |
| Status values summing to the corpus | 18 + 11 + 8 + 8 + 1 + 0 = **46** |
| Post-plugin plan cells populated | **33 of 46**; **13 deliberately empty** |
| Post-plugin values outside V2-005's vocabulary | **0** |
| Basis cells populated | **46 of 46**, including all 13 empty-plan rows |
| Verification cells populated | **46 of 46** (9 MEASURED, 37 CITED, 0 INFERRED) |

**The 9 rows whose evidence is an explicit NONE** (rows 2, 15, 16, 22, 23, 24, 28, 30, 39):
`architecture-script-mapping-policy.md`, `EXECUTION-SYSTEM-FIXES-SUMMARY.md`,
`file-management-policy.md`, `intelligent-decision-engine-policy.md`,
`intelligent-model-selection-policy.md`, `INTELLIGENT-PROMPT-GENERATION-UPGRADE.md`,
`parallel-execution-policy.md`, `proactive-consultation-policy.md`, `test-case-policy.md`.
Count of names listed: 9. Evidence density is therefore **37/46 (80.4%) real citations**.
"NONE found" is a populated evidence cell under AC2; an empty cell would not be.

### 1.2 Post-plugin plan: distribution, decision rule, and the 13 empty cells

| Value | Count | Source |
|---|---|---|
| `keep-as-is` | 18 | this pass's judgement, rule below |
| `port-to-plugin` | 0 | no source assigns it; not invented |
| `port-to-MCP` | 5 | `hld.md` SS 12 OAQ 2 (RESOLVED) |
| `demote-to-advisory` | 5 | `hld.md` SS 12 OAQ 2 (RESOLVED) |
| `delete` | 5 | `hld.md` SS 12 OAQ 2 (RESOLVED) |
| *(empty)* | 13 | no decision derivable; see below |
| **Total** | **46** | |

**Provenance split: 15 rows from OAQ 2, 18 from this pass's judgement, 13 left empty.**
15 + 18 + 13 = 46. The `Basis` column makes the split machine-readable per row: OAQ-2-sourced
rows cite `OAQ 2 row N`, self-judged rows are prefixed `judged:`, and empty-plan rows carry
the reason no decision was possible.

**The 15 OAQ-2 rows are exactly the 15 hook-coupled policies.** MEASURED: filtering
`policy_enforcement_raw.json` on `hook_coupled_by_implementation == true` returns 15 records,
and that set is **identical** to OAQ 2's 15 table rows -- asserted by set equality at
generation time, so neither set contains a policy absent from the other. OAQ 2's totals
(5 port-to-MCP, 5 demote-to-advisory, 5 delete) reconcile with the per-row values
transcribed here.

**Decision rule for the remaining 31.** Stated so it can be checked rather than trusted:

> A non-hook-coupled policy is assigned `keep-as-is` **only if** it has a live enforcement
> point in pipeline code (status ENFORCED or PARTIAL). In that case de-hooking provably does
> not touch it: its enforcement is in `langgraph_engine/` or `src/mcp/`, not in a hook, so it
> continues to behave exactly as it does today. That is a real decision backed by the
> Evidence cell, not a neutral filler.
>
> Every other non-hook-coupled policy gets an **empty** cell.

This yields **18 `keep-as-is`** (12 ENFORCED, 6 PARTIAL) and **13 empty**.

**Why the 13 are empty rather than assigned a value.** Two groups:

- **5 rows are broken or unanswerable independently of de-hooking** -- 4 CONTRADICTED
  (`anti-hallucination-enforcement`, `architecture-script-mapping`, `callgraph-analysis`,
  `intelligent-decision-engine`) and 1 STALE-TOPOLOGY (`intelligent-model-selection`).
  `keep-as-is` would assert that v2.0.0 is content to ship a known-broken policy unchanged,
  which is false to the evidence. The real choice is fix / delete / demote, and **no source
  artifact makes it** -- OAQ 2 scopes itself to the hook-coupled 15 and stops there.
- **8 rows are DOCUMENTED-ONLY** (`EXECUTION-SYSTEM-FIXES-SUMMARY`,
  `INTELLIGENT-PROMPT-GENERATION-UPGRADE`, `file-management`, `mcp-plugin-discovery`,
  `parallel-execution`, `proactive-consultation`, `test-case`, `user-preferences`). There is
  no runtime mechanism to keep, port or delete. `keep-as-is` here would assert a product
  decision -- that v2.0.0 retains an unimplemented policy document -- that nothing
  establishes. `mcp-plugin-discovery` is the sharpest case: v2.0.0 *is* the plugin
  transformation, so a policy about MCP plugin discovery is plausibly in scope for
  `port-to-plugin`, but "plausibly" is not evidence and this pass will not manufacture it.

Count check: 5 + 8 = 13, matching the table above.

**These 13 empty cells will fail PRD FR-2 and FR-20 loudly, and that is the intended
outcome.** FR-2 fails on an empty Post-plugin plan cell and FR-20 demands a non-empty value.
A placeholder such as "UNDECIDED" would be non-empty while encoding "no decision has been
made" -- satisfying the letter of both requirements while defeating exactly what they exist
to force, structurally the same escape hatch NFR-4 closes when it forbids a "disappeared"
disposition. **13 rows are work someone must do**, and the column says so visibly rather than
laundering it into a value that passes review.

### 1.3 Status counts, unchanged

| Status | Count |
|---|---|
| ENFORCED | 18 |
| PARTIAL | 11 |
| CONTRADICTED | 8 |
| DOCUMENTED-ONLY | 8 |
| STALE-TOPOLOGY | 1 |
| DEAD | 0 |
| **Total** | **46** |

Unchanged from the approved figures. `18 + 11 + 8 + 8 + 1 + 0 = 46`. Re-derived by grouping
the 46 matrix rows by their Status column and re-counting; the group sizes match the approved
values exactly. No policy was reclassified by this pass, and assigning post-plugin plans
changed no status.

**Zero DEAD is deliberate.** CITED: Class Hierarchy Analysis seeds every module's own
`__main__` block as an entry point, so a module can report `reachable_cha: true` purely from
being a standalone CLI script. Given that confound, ambiguous cases were classified
CONTRADICTED (positive evidence of a mismatch) or PARTIAL, reserving DEAD for a confidently
unreachable case that did not arise. Row 1 is first-hand confirmation of the confound.

---

## 2. Correction record: the "46/46 orphan policies" figure was FALSE

**An earlier pass reported "46 of 46 orphan policies". That figure is retracted. The correct
figure is 14 of 46.** CITED.

Stated explicitly here so that anyone who saw the earlier number finds its retraction.

**Root cause.** Not a measurement error and not fabrication. An orchestrator briefing error:
`SRS.md` was never supplied to the knowledge-graph build, so it had no requirement corpus to
correlate against. Every policy matched nothing, and "matched nothing" was recorded as
"orphaned" -- absence of evidence written down as evidence of absence. CITED from
`docs/REVIEW-INDEX.md` correction #1; `as-built-prd.md` notes it replaces the false
`orphan_policies_count: 46` in `codebase_kg/kg_report.json`.

**Corrected figure: 14 of 46 (30.4%) are genuine orphans.** CITED, not re-derived by this
pass -- re-deriving it means re-running the SRS correlation, which is the re-analysis this
work was scoped out of. The figure carries its source's confidence, not this pass's.

**Six of the 14 would stay orphaned under perfect SRS coverage.** CITED:
`anti-hallucination-enforcement`, `architecture-script-mapping`, `git-auto-commit`,
`intelligent-decision-engine`, `session-pruning`, and `cross-project-patterns`. The first
five are independently CONTRADICTED; the sixth is a live ENFORCED capability the current SRS
never states as a requirement. The remaining eight are orphaned because of the ingestion gap
and form the addressable population.

The gap between 46 and 14 changes the conclusion from "the policy corpus is entirely
disconnected from requirements" to "about a third is, and half of that third is disconnected
for reasons an SRS fix cannot touch". Any v2.0.0 planning that inherited 46 was working from
a briefing artifact.

---

## 3. Spot-verification against live code

**Sample: 9 policies of 46, across 3 of the 6 status categories.** The 9 MEASURED rows in
the matrix are exactly this sample.

**Selection basis.** Not random. All 3 policies previously reported as silent no-ops, since
they are the highest-consequence operational claim; 2 ENFORCED chosen for *different
enforcement mechanisms* (hook dispatch table, LangGraph node) so a pass would not confirm one
code path twice; 3 CONTRADICTED chosen for different contradiction *kinds* (configuration
cap, unreferenced module, duplicated enforcement point); and 1 further ENFORCED
(`tool-optimization`) verified incidentally, because the duplication check for row 42
necessarily established row 41's enforcement point at the same time.

**37 of 46 classifications were NOT verified by this pass.** PARTIAL, DOCUMENTED-ONLY and
STALE-TOPOLOGY were not sampled at all, so no claim is made that any individual policy in
those three groups is correctly classified. Their Verification cells read CITED.

> **Correction to this report's own prior revision.** The 2026-08-01 revision stated "41 of
> the 46 individual classifications were not re-verified" while describing a sample of "5
> policies plus 3 no-op checks" -- 8 distinct policies, which implies 38 unverified, not 41.
> The summary count disagreed with its own enumeration, this project's most-caught defect
> class, committed in the section disclosing verification limits. Counted against the
> Verification column above, the figure is **37 unverified (CITED) / 9 MEASURED**, and
> 9 + 37 = 46. The disclosure's substance is unchanged and if anything understated: most rows
> rest on citation, not measurement. **The figure 41 should not be reintroduced** -- it
> reconciles with no enumeration in this document.

### 3.1 The three maintenance no-ops

Prior finding, CITED: auto-commit, session-save and session-pruning target
`scripts/architecture/` subtrees that do not exist, and their `.exists()` guards fail
silently every turn.

**Result: CONFIRMED. All three target scripts are absent.** MEASURED.

MEASURED detail: `scripts/architecture/` contains exactly two entries,
`03-execution-system/` and `generate_system_diagram.py`. `scripts/architecture/01-sync-system/`
does not exist at all, accounting for both session-save and session-pruning in one stroke.
No `09-git-commit/` directory exists at any level.

A near miss that would mislead a reader skimming the tree:
`03-execution-system/failure-prevention/` **does exist** and holds `failure-kb.json`, but the
script the Stop hook spawns from that same directory, `common-failures-prevention.py`,
**does not**. The present directory makes the spawn look plausible on a casual check while
still no-opping.

The silence is confirmed by inspection of `hooks/stop_notifier/core.py:78`, `:106`, `:159`
(MEASURED): each spawn is `if <script>.exists():` with **no `else` and no log statement on
the negative path**. The enclosing `try/except` logs only on a raised exception, and a
`False` from `.exists()` raises nothing. There is no runtime signal of any kind that these
three policies are inert.

### 3.2 ENFORCED, reachability

The requirement was to confirm the enforcing code is *reachable*, not merely present.

**Row 10, `context-reading-policy.md`: REACHABLE, CONFIRMED.** MEASURED.
`check_context_read_complete` is present at `policies/context_read.py:14` and, decisively,
is registered as `("context_read", check_context_read_complete)` in `_BLOCKING_POLICIES` at
`hooks/pre_tool_enforcer/core.py:453-469`. That list is what `_evaluate_tool_call` iterates,
so registration is the reachability evidence, not mere presence.

**Row 43, `unicode-fix-policy.md`: REACHABLE, CONFIRMED.** MEASURED. Defined at
`preflight_guard/nodes.py:62`, added to the graph at `orchestrator.py:657` as
`preflight_guard_unicode`. The decisive evidence is the edge, not the node registration:
`orchestrator.py:663` adds `graph.add_edge(START, "preflight_guard_unicode")`, making it the
first node after `START` and therefore unconditionally reachable on every run. Outbound edge
to `preflight_guard_encoding` at `:664`; re-entry from `fix_preflight_guard` at `:693`.

**Row 41, `tool-optimization-policy.md`: REACHABLE, CONFIRMED.** MEASURED incidentally via
the row 42 duplication check. `check_read_opt` and `check_grep_opt` are registered at
`core.py:466-467`.

### 3.3 CONTRADICTED, does the contradiction still hold

**Row 1, `anti-hallucination-enforcement.md`: HOLDS.** MEASURED. A repo-wide grep for
`anti_hallucination` across all `.py` files returns hits in exactly one file, its own, and
every hit is a self-reference (docstring usage examples, log strings, print statements).
**No file anywhere in the repository imports it.** Its only entry path is manual CLI
invocation.

**Row 4, `callgraph-analysis-policy.md`: HOLDS, and the cap is genuinely binding.** MEASURED:
`parsers/call_graph_builder_legacy.py:64` sets `MAX_FILES = 300`; `:76` uses it as the
`max_files` default in `CallGraphBuilder.__init__`; the discovery loop enforces it at `:107`
and `:118` (`if len(found) >= self.max_files: break`). Repo `.py` files on disk, excluding
`.git`, `__pycache__` and `.venv`: **411**. A second independent cap survives fixing the
first: `parsers/graph_model.py:43` `DEFAULT_MAX_PATHS = 500`, truncating path traversal
regardless of file count.

**Row 42, `tool-usage-optimization-policy.md`: HOLDS.** MEASURED. Exactly one pair of check
functions exists, defined once in `policies/read_opt.py` and `grep_opt.py`, aliased at
`core.py:193-194`, re-exported at `:373-374`, registered once each at `:466-467`. Both
policies resolve to that single registration; there is no second gate for the second policy
to own.

---

## 4. The audited corpus is not the runtime corpus

Found while checking AC3's premise. MEASURED 2026-08-02. This does not change any status
count, and no row was reclassified, but it bounds what the matrix describes.

`CLAUDE.md` states that `docs/policies/` mirrors `~/.claude/policies/`, and that the
`~/.claude/` copy is what `get_policies_dir()` reads
(`src/utils/path_resolver.py:389`, consumed at `langgraph_engine/standards/selector.py:40`).
**The mirror claim is false at the level of membership.**

| Measure | `docs/policies/` (audited) | `~/.claude/policies/` (runtime) |
|---|---|---|
| Shape | flat | nested tree: `01-sync-system/`, `02-standards-system/`, `03-execution-system/`, `failure-prevention/`, `testing/` |
| Policy `.md` files | 46 | 34 (plus 1 `README.md`, 35 `.md` total) |

- **6 policies exist only at runtime and were never audited**:
  `adaptive-skill-registry.md`, `auto-plan-mode-suggestion-policy.md`,
  `auto-skill-agent-selection-policy.md`, `core-skills-mandate.md`,
  `github-branch-pr-policy.md`, `recommendations-policy.md`. Count listed: 6. **These are
  outside the 46-row matrix entirely** -- no status, evidence, post-plugin plan or
  verification exists for them.
- **18 audited policies do not exist in the runtime tree**, including 10 of the 18 ENFORCED
  rows (`hook-system`, `metrics-monitoring`, `quality-gate`, `unicode-fix`, `windows-path`,
  `recovery`, `test-generation`, `tool-optimization`, `final-summary`, `issue-closure`).
- **28 filenames appear in both.**

**On content divergence, do not over-read the raw figure.** A byte comparison reports all 28
shared files as differing, but that figure is inflated by line-ending differences. I sampled
**3 of the 28** and normalized line endings and trailing whitespace before comparing:
`tool-usage-optimization-policy.md` is then **identical**; `context-reading-policy.md`
differs on **3 lines** (the runtime copy still says `"project_name": "claude-insight"`, the
pre-rename name); `session-memory-policy.md` differs on **11 lines** (different example
session paths). **On a 3-of-28 sample the divergences are cosmetic or stale-naming, not
semantic**, and nothing in the sample would change a classification. The other 25 were not
examined.

**Why this matters for AC3 and for V2-005.** The matrix describes the repository corpus. If
the intent behind AC3 was to audit what the running system loads, then 6 policies are missing
from the matrix and 18 rows describe documents the runtime does not have. Which corpus is
canonical is an owner decision, not one this pass can settle.

**A methodological note on how this was found, because the first attempt was wrong.** The
initial probe globbed `~/.claude/policies/*.md` non-recursively, got 0 matches, and would
have supported the false conclusion "the runtime policy directory is empty". The directory is
a nested tree; the correct probe is `rglob`. This is the same defect as correction #16 (a
probe's limited scope read as exhaustive), caught here before it reached a claim.

---

## 5. Stop hook: dead-script count

CITED prior finding (`docs/REVIEW-INDEX.md` correction #3): 7 of the 9 scripts referenced by
the Stop hook do not exist, reducing the spawn floor from a claimed 8 per turn to roughly 2.
Three policies no-op every turn for this reason alone, independently of any hook change.

**Measured count: 7. Confirms the prior figure.** MEASURED. Enumerated by grepping every
`.exists()`-guarded `subprocess.run` in `hooks/stop_notifier/` and resolving each path;
**9 spawn targets**, matching the prior denominator.

| # | Target as referenced | At referenced path | Anywhere in repo |
|---|---|---|---|
| 1 | `scripts/architecture/03-execution-system/09-git-commit/git-auto-commit-policy.py` | NO | NO |
| 2 | `scripts/architecture/01-sync-system/session-management/auto-save-session.py` | NO | NO |
| 3 | `scripts/architecture/01-sync-system/session-management/archive-old-sessions.py` | NO | NO |
| 4 | `scripts/architecture/01-sync-system/session-pruner.py` | NO | NO |
| 5 | `scripts/architecture/03-execution-system/failure-prevention/common-failures-prevention.py` | NO | NO |
| 6 | `scripts/architecture/01-sync-system/user-preferences/preference-auto-tracker.py` | NO | NO |
| 7 | `scripts/architecture/03-execution-system/02-plan-mode/plan-session-archiver.py` | NO | NO |
| 8 | `hooks/stop_notifier/sync-version.py` (`post_impl.py:285`) | NO | YES, `scripts/tools/sync-version.py` |
| 9 | `<CURRENT_DIR>/voice-notifier.py` (`helpers.py:142`) | NO (this environment) | YES, `scripts/tools/voice-notifier.py` |

**The reported number is 7**, on the criterion "does not exist anywhere in the repository":
rows 1-7. Two discrepancies are preserved rather than merged into that figure:

- **Row 8 is unconditionally broken too, and is not environment-dependent.**
  `post_impl.py:285` resolves the script as `Path(__file__).resolve().parent /
  "sync-version.py"`, a sibling of `post_impl.py` inside `hooks/stop_notifier/`. No such file
  is there. A copy exists at `scripts/tools/sync-version.py`, so a filename search finds it
  and it is reasonably counted as existing -- but **the hook cannot reach it**, because the
  path it computes never points there. On a strict "does the spawn resolve" criterion the
  count is **8 of 9**, not 7. Reported as 7 for consistency with the approved figure, with
  the divergence flagged rather than smoothed.
- **Row 9 is environment-dependent and undetermined.** `VOICE_SCRIPT` is
  `CURRENT_DIR / "voice-notifier.py"`, where `CURRENT_DIR` derives from
  `CLAUDE_IDE_INSTALL_DIR`. Unset, as here, it resolves to
  `~/.claude/memory/current/voice-notifier.py`, which does not exist (nor does
  `~/.claude/scripts/`). Under IDE mode it could resolve. **Not counted as dead.**

The three maintenance policies are unaffected by either discrepancy: rows 1-4 cover them and
are absent repo-wide without ambiguity.

---

## 6. Citation defect in the source artifacts: partially remediated

Reported in this document's 2026-08-01 revision and **re-checked 2026-08-02**. The state has
changed since, so the earlier finding is updated rather than repeated.

The issue: several Phase 0 artifacts cited `parsers/config.py:11` as the call-graph
truncation site. That constant is **dead code** -- MEASURED: its only importer is
`parsers/__init__.py:22`, which merely re-exports it, and no consumer exists anywhere in
`langgraph_engine/`. Acting on it would produce a diff resembling the fix while leaving
discovery capped at 300. The binding caps are `parsers/call_graph_builder_legacy.py:64` and
`parsers/graph_model.py:43`.

**Remediation status, MEASURED 2026-08-02:**

| Artifact | Correction present |
|---|---|
| `as_built_executive_summary.md` | YES ("SITE CORRECTED 2026-08-01") |
| `builder_divergence.md` | YES ("Recommendation SUPERSEDED 2026-08-01") |
| `policy_enforcement_raw.json` | **YES, new** -- corrected 17:23 on 2026-08-01, adds an `enforcement_point_corrected_2026_08_01` field |
| `contradictions.md` | **YES, new** -- corrected 17:24 on 2026-08-01 |
| `as-built-prd.md` (lines 113, 133) | **NO** |
| `ast_call_graph_summary.md` (line 50) | **NO** |
| `codebase_kg/kg_report.json` (line 97) | **NO** |
| `codebase_kg/nodes.json` (lines 40081-40082) | **NO** |

**4 corrected, 4 still carrying it.** Two of the four flagged on 2026-08-01 were fixed within
the hour. Two remain, and re-checking surfaced **two further carriers not in the original
list**: the knowledge-graph artifacts `kg_report.json` and `nodes.json`. Those two are
notable because `kg_report.json` is the same file that held the false
`orphan_policies_count: 46` of section 2 -- the KG outputs have now been the origin or
carrier of both defects recorded in this document.

Row 4 of the matrix uses the corrected site. No status count is affected; only site
attribution was ever wrong. **This document modifies none of those four files**; correcting
them is a separate change with its own review.

---

## 7. Hook coupling

CITED except where section 3 measured it.

- **4 of 4 match.** Every policy naming a hook in its own text (`hook-system`,
  `implementation-execution`, `metrics-monitoring`, `tool-optimization`) is confirmed
  hook-coupled. No policy overclaims a hook it does not have.
- **11 are hook-coupled without saying so**: `automatic-task-breakdown`,
  `common-failures-prevention`, `context-management`, `context-reading`, `git-auto-commit`,
  `session-memory`, `session-pruning`, `task-phase-enforcement`, `task-progress-tracking`,
  `tool-usage-optimization`, `version-release`. Count listed: 11. With the 4 above this is
  the 15-policy hook-coupled set that OAQ 2 dispositions, and it is exactly the 15 rows whose
  Basis cell cites OAQ 2.
- **Coupling to a hook is not the same as the hook's target running.** Three of the 15
  (`git-auto-commit`, `session-memory`, `session-pruning`) are genuinely hook-coupled and
  still no-op, because the coupled path spawns a script that is not on disk. MEASURED,
  section 3.1. All three are dispositioned `delete` by OAQ 2.

---

## 8. What this pass could NOT determine

1. **37 of 46 classifications were not independently verified.** Counts are MEASURED; the
   per-policy status decisions are CITED. PARTIAL, DOCUMENTED-ONLY and STALE-TOPOLOGY were
   not sampled at all.
2. **AC3 is not satisfied.** No line-by-line read of `~/.claude/policies/` was performed by
   this pass, and the underlying analysis read `docs/policies/`. Recorded as open rather than
   asserted. See the header and section 4.
3. **13 of 46 post-plugin plan cells are empty** because no decision is derivable from the
   evidence and no source artifact makes one. Enumerated in section 1.2. This is the largest
   single block of outstanding work the matrix exposes.
4. **`port-to-plugin` is assigned to zero rows.** No source assigns it, and this pass did not
   infer it -- including for `mcp-plugin-discovery-policy.md`, where it is plausible but
   unevidenced.
5. **The 14-of-46 orphan figure is CITED, not re-derived.**
6. **25 of the 28 shared runtime/repo policy files were not content-compared.** The
   "cosmetic, not semantic" characterisation rests on a 3-file sample.
7. **Whether `voice-notifier.py` resolves in production is undetermined** (section 5, row 9).
8. **CHA under-reports hook-policy liveness generally.** CITED: `pre-tool-enforcer.py` loads
   `core.py` via `importlib.util.spec_from_file_location` and aliases `policies/*.py`
   functions through module attributes; the static pass traces neither hop, so those
   functions show `reachable_cha: false` despite being live. Section 3.2 worked around this
   by reading the dispatch table and graph edges directly, but only for three rows.
9. **Rows 12 and 19's creation-side methods** show `reachable_cha: false` on a class
   instantiated once in a wrapper file while sibling methods show `true`. CITED: scored
   PARTIAL rather than DEAD given item 8, and **not re-verified by call-site tracing** by the
   original pass or this one. Both carry `keep-as-is`, which rests on the enforcement point
   being pipeline code -- true regardless of its reachability.
10. **The Stop-hook spawn floor itself remains an open measurement conflict.** CITED: "8 per
    turn assuming scripts exist" against a verified-absent script set implying a floor near
    2. This pass confirmed the absences, not the runtime spawn count.
11. **No coverage or runtime-trace evidence was consulted.** TestCoverage was unavailable to
    the original pass; `lhs.json` substitutes a DocCoverage-only proxy, explicitly flagged.

---

## 9. Summary

- **46-row matrix. Evidence cell populated in all 46, zero blanks** -- 37 real `file:line`
  citations, 9 explicit NONE.
- **Status counts unchanged and reconciling: 18 / 11 / 8 / 8 / 1 / 0 = 46.**
- **Post-plugin plan uses V2-005's vocabulary exactly**, zero out-of-vocabulary values:
  18 `keep-as-is`, 5 `port-to-MCP`, 5 `demote-to-advisory`, 5 `delete`, 0 `port-to-plugin`,
  **13 deliberately empty**. Provenance: 15 from OAQ 2, 18 judged, 13 undecidable.
- **The 13 empty cells fail FR-2 and FR-20 by design.** They mark real outstanding decisions
  rather than laundering them into a placeholder that passes review.
- **"46/46 orphan policies" retracted**; real figure 14 of 46, six beyond any SRS fix.
- **Three maintenance policies are dead paths today**, before any hook change; all three are
  `delete` under OAQ 2.
- **7 of 9 Stop-hook target scripts absent**; an 8th exists but not where the hook looks.
- **The audited corpus is not the runtime corpus**: 6 runtime policies never audited, 18
  audited policies absent at runtime.
- **AC3 not satisfied**, and not claimed.
- **37 of 46 classifications remain CITED.** Best available, not verified.

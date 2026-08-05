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
outside that set fails V2-005's review, so no other token appears in that column. **All 46
cells are now populated.** 42 were decided from evidence on disk; the final 4 were closed by
owner and architect rulings on 2026-08-02 and are labelled as rulings, not as findings --
see section 1.2.2.

Sorted alphabetically by policy filename, case-insensitive.

| # | Policy file | Status | Evidence | Post-plugin plan | Basis | Verification |
|---|---|---|---|---|---|---|
| 1 | `anti-hallucination-enforcement.md` | CONTRADICTED | `langgraph_engine/sdlc_pipeline/architecture/00-prompt-generation/anti_hallucination_enforcement.py:38-133`; zero importers repo-wide | delete | OWNER RULING 2026-08-02, not an evidence finding: implementing a prompt-quality gate is scope creep for v2.0.0's core execution scope. Recorded as a SCOPE decision, not a defect in the policy -- the module is sound and simply unwired. NOTE: the vocabulary has no `defer`, so `delete` is the nearest member; if v2.1 wants this gate the policy must be recovered from git history, which is available since `docs/policies/` is versioned | MEASURED |
| 2 | `architecture-script-mapping-policy.md` | CONTRADICTED | NONE as runtime code. `docs/policies/architecture-script-mapping-policy.md` is itself the only artifact; a reference document, not code | port-to-plugin | OWNER RULING 2026-08-02: align the tree's mapping with the modern structure rather than delete it. FR-9a keeps that tree alive as a live-but-non-binding cap, so it survives v2.0.0. **PRECONDITION, MEASURED 2026-08-02: the mapping is wrong in BOTH directions -- 0 of the 3 scripts it names exist, and the one script that does exist under `scripts/architecture/` is unlisted. Porting it as written would carry a broken inventory into the plugin; the mapping must be corrected as part of the port.** First and only `port-to-plugin` row in the matrix | CITED |
| 3 | `automatic-task-breakdown-policy.md` | ENFORCED | `hooks/pre_tool_enforcer/policies/task_breakdown.py:12` `check_task_breakdown_pending`, registered `core.py:455` `_BLOCKING_POLICIES` | demote-to-advisory | OAQ 2 row 6 -- demoted because Step 1's `todo_decomposer` already performs decomposition in-pipeline, so a per-tool-call enforcement point would duplicate it | CITED |
| 4 | `callgraph-analysis-policy.md` | CONTRADICTED | `langgraph_engine/parsers/call_graph_builder_legacy.py:64` `MAX_FILES=300`, bound at `:76`, enforced `:107` and `:118`; second cap `parsers/graph_model.py:43` | keep-as-is | `prd-v2.md` FR-9a superseding AC (owner ruling, in v2.0.0 scope) + `hld.md` OAQ 4 / ADR-013 repair both binding caps in `langgraph_engine/parsers/`, pipeline code de-hooking does not touch | MEASURED |
| 5 | `code-graph-analysis-policy.md` | ENFORCED | `langgraph_engine/sdlc_pipeline/architecture/00-code-graph-analysis/code_graph_analyzer.py:340-637` (`build_graph`, `compute_graph_metrics`) | keep-as-is | judged: no hook coupling; enforcement is pipeline code de-hooking does not touch | CITED |
| 6 | `coding-standards-enforcement-policy.md` | ENFORCED | `langgraph_engine/standards/selector.py:114` `detect_framework`, `:202` `_detect_java_framework` (reach=True) | keep-as-is | judged: no hook coupling; enforcement is pipeline code de-hooking does not touch | CITED |
| 7 | `common-failures-prevention.md` | PARTIAL | `hooks/pre_tool_enforcer/policies/failure_kb.py:11` `check_failure_kb_hints`, called non-blocking at `core.py:517-523`; Stop-side script absent | port-to-MCP | OAQ 2 row 7 -- ported because its `failure-kb.json` data is a lookup table and so a natural deterministic MCP tool; only the PreToolUse side is live today, its Stop-side script being one of FR-21's 7 missing files | CITED |
| 8 | `common-standards-policy.md` | ENFORCED | `langgraph_engine/standards/selector.py:449` `select_standards`, `:273` `load_custom_standards`, `:358` `load_framework_standards` | keep-as-is | judged: no hook coupling; enforcement is pipeline code de-hooking does not touch | CITED |
| 9 | `context-management-policy.md` | PARTIAL | `hooks/pre_tool_enforcer/policies/level1_sync.py:15` `check_level1_sync_complete`, registered `core.py:458`; token-budget code not located under this name | demote-to-advisory | OAQ 2 row 8 -- demoted because the rule is judgement-shaped and its deterministic part already belongs to `mcp-token-optimizer` | CITED |
| 10 | `context-reading-policy.md` | ENFORCED | `hooks/pre_tool_enforcer/policies/context_read.py:14` `check_context_read_complete`, registered `core.py:457` `_BLOCKING_POLICIES` | demote-to-advisory | OAQ 2 row 9 -- demoted on the same judgement-shaped grounds as `context-management-policy.md`, this being the rule that produced the chunked-read guidance | MEASURED |
| 11 | `cross-project-patterns-policy.md` | ENFORCED | `langgraph_engine/context_sync/architecture/pattern_detector.py:388` `detect_patterns`, `:525` `scan_all_projects` | keep-as-is | judged: no hook coupling; enforcement is pipeline code de-hooking does not touch | CITED |
| 12 | `documentation-update-policy.md` | PARTIAL | `langgraph_engine/sdlc_pipeline/nodes/closure_docs_summary_wrapper.py:62` `step7_project_documentation_update`, `:153` `step7_docs_update_node` | keep-as-is | judged: no hook coupling; enforcement is pipeline code de-hooking does not touch | CITED |
| 13 | `encoding-validation-policy.md` | PARTIAL | `langgraph_engine/preflight_guard/nodes.py:150-237` `node_encoding_validation` (reach=True, cc=17) | keep-as-is | judged: no hook coupling; enforcement is pipeline code de-hooking does not touch | CITED |
| 14 | `error-recovery-policy.md` | PARTIAL | `langgraph_engine/engine_logging/error_logger.py` `ErrorLogger.log_error` (reach=True, cc=3), `log_validation_result` | keep-as-is | judged: no hook coupling; enforcement is pipeline code de-hooking does not touch | CITED |
| 15 | `EXECUTION-SYSTEM-FIXES-SUMMARY.md` | DOCUMENTED-ONLY | NONE. Point-in-time changelog, not a policy with a runtime mechanism | delete | `as-built-prd.md` SS 4.2 classifies it a point-in-time changelog, not an ongoing SHALL; ADR-009 scopes `docs/policies/` to the policy corpus the plugin bundles, and git retention makes removal recoverable | CITED |
| 16 | `file-management-policy.md` | DOCUMENTED-ONLY | NONE found | demote-to-advisory | Its rules are model-judged conduct (temp-file placement, protected paths) with no gate anywhere -- OAQ 2 row 2's stated criterion for the plugin's agent-instruction layer; deleting would drop a live rule under NFR-4 | CITED |
| 17 | `final-summary-policy.md` | ENFORCED | `langgraph_engine/sdlc_pipeline/nodes/closure_docs_summary_wrapper.py:70` `step8_final_summary_generation`, `:202` `step8_final_summary_node` | keep-as-is | judged: no hook coupling; enforcement is pipeline code de-hooking does not touch | CITED |
| 18 | `git-auto-commit-policy.md` | CONTRADICTED | `hooks/stop_notifier/core.py:74-96` spawns `scripts/architecture/03-execution-system/09-git-commit/git-auto-commit-policy.py`, which does not exist | delete | OAQ 2 row 10 -- deleted because the reference is confirmed silently non-functional today, independent of any hook change, its `.exists()` guard targeting a script that was never built, with the capability loss recorded in the NFR-4 ledger rather than dropped | MEASURED |
| 19 | `github-issues-integration-policy.md` | PARTIAL | `langgraph_engine/sdlc_pipeline/github_lifecycle.py` `Level3GitHubWorkflow.step2_create_issue:125` (reach=False), `.step3_create_branch:294` (reach=False) | keep-as-is | judged: no hook coupling; enforcement is pipeline code de-hooking does not touch | CITED |
| 20 | `hook-system-policy.md` | ENFORCED | `hooks/pre-tool-enforcer.py` shim into `hooks/pre_tool_enforcer/core.py:453-469` `_BLOCKING_POLICIES` | delete | OAQ 2 row 1 -- deleted because it documents the very hook mechanism FR-4 removes, so shipping it would guarantee a permanent contradiction with shipped behaviour | CITED |
| 21 | `implementation-execution-policy.md` | PARTIAL | `langgraph_engine/sdlc_pipeline/nodes/implementation_and_review_wrapper.py:84` `step4_implementation_note` (reach=True) | demote-to-advisory | OAQ 2 row 2 -- demoted because it governs Step 4 conduct, which is model-judged and therefore belongs in the plugin's agent-instruction layer rather than in a gate | CITED |
| 22 | `intelligent-decision-engine-policy.md` | CONTRADICTED | NONE found. Describes an "OpenRouter consolidation" never built; the systems it unifies were deleted in v1.13 | delete | MEASURED 2026-08-02: its named script path `scripts/architecture/03-execution-system/04-model-selection/` and every OpenRouter reference are absent repo-wide, and the 4 systems it unifies went in v1.13 / v1.15.3 -- `prd-v2.md` SS 8's stated delete rationale for a policy governing a step that no longer exists | CITED |
| 23 | `intelligent-model-selection-policy.md` | STALE-TOPOLOGY | NONE found under this description. One of its 5 inputs (plan-mode decision) was deleted in v1.13, so the retranslated question is unanswerable | demote-to-advisory | ARCHITECT RULING 2026-08-02: stale but not obsolete, so it is retained as guidance rather than deleted or retranslated now. Model selection remains a live concern (`langgraph_engine/version_selector.py` exists, MEASURED), and retranslating its remaining 4 inputs against the 2-provider topology stays available later. No OAQ covers this row; the ruling is the source | CITED |
| 24 | `INTELLIGENT-PROMPT-GENERATION-UPGRADE.md` | DOCUMENTED-ONLY | NONE. Point-in-time changelog | delete | `as-built-prd.md` SS 4.2 classifies it a point-in-time changelog, not an ongoing SHALL; ADR-009 scopes `docs/policies/` to the policy corpus the plugin bundles, and git retention makes removal recoverable | CITED |
| 25 | `issue-closure-policy.md` | ENFORCED | `langgraph_engine/sdlc_pipeline/github_lifecycle.py:543` `step6_close_issue`, `:603` `_build_closing_comment` (both reach=True) | keep-as-is | judged: no hook coupling; enforcement is pipeline code de-hooking does not touch | CITED |
| 26 | `mcp-plugin-discovery-policy.md` | DOCUMENTED-ONLY | `langgraph_engine/state/state_definition.py:184` `mcp_plugins_path` -- a FlowState field only, no discovery logic | delete | ADR-019 replaces auto-discovery with opt-in `register-mcp` and ADR-010 / FR-4 delete the `pre-tool-enforcer` AUTO-ROUTE mode it configures; MEASURED 2026-08-02: the `mcp_plugin_loader` module it imports is absent repo-wide (stale `.pyc` only, zero importers) -- OAQ 2 row 1's criterion for a document of a removed mechanism | CITED |
| 27 | `metrics-monitoring-policy.md` | PARTIAL | `langgraph_engine/metrics/aggregator.py` `aggregate_sessions:96`, `aggregate_step_performance:191`, `aggregate_llm_usage:307`, `aggregate_tool_usage:408` | port-to-MCP | OAQ 2 row 3 -- ported because its rules are deterministic counters, and `metrics_exporter.py` plus `mcp-post-tool-tracker` already provide the tool surface to carry them | CITED |
| 28 | `parallel-execution-policy.md` | DOCUMENTED-ONLY | NONE found as engine code. Describes calling-agent behaviour, not a pipeline capability | demote-to-advisory | `as-built-prd.md` SS 4.2: calling-agent behaviour, not a pipeline capability, so there is no gate to keep or port -- OAQ 2 row 2's criterion for the plugin's agent-instruction layer | CITED |
| 29 | `pr-code-review-policy.md` | PARTIAL | `langgraph_engine/sdlc_pipeline/github_code_review.py` `run_code_review:283`, `check_python_best_practices:53` (all reach=False) | keep-as-is | judged: no hook coupling; enforcement is pipeline code de-hooking does not touch | CITED |
| 30 | `proactive-consultation-policy.md` | DOCUMENTED-ONLY | NONE. Explicitly deprecated by its own text | delete | Its own header declares `Status: DEPRECATED (2026-03-17)` with the reason and the three named replacements; shipping it in the v2.0.0 corpus would carry a rule its own text retired | CITED |
| 31 | `prompt-generation-policy.md` | ENFORCED | `langgraph_engine/sdlc_pipeline/architecture/prompt_gen_expert_caller.py:159` `_build_filled_prompt`, `:253` `main` (reach=True) | keep-as-is | judged: no hook coupling; enforcement is pipeline code de-hooking does not touch | CITED |
| 32 | `quality-gate-policy.md` | ENFORCED | `langgraph_engine/sdlc_pipeline/quality_gate.py:637` `evaluate_quality_gate` (reach=True, cc=9), with `_evaluate_sonar_gate:142`, `_evaluate_coverage_gate:248` | keep-as-is | judged: no hook coupling; enforcement is pipeline code de-hooking does not touch | CITED |
| 33 | `recovery-policy.md` | ENFORCED | `langgraph_engine/preflight_guard/recovery.py:234` `fix_preflight_guard_issues` (reach=True, cc=45) | keep-as-is | judged: no hook coupling; enforcement is pipeline code de-hooking does not touch | CITED |
| 34 | `session-chaining-policy.md` | PARTIAL | `src/mcp/session_hooks.py`, `src/mcp/session_mcp_server.py` (`session_link`-adjacent surface, module reach=True); `clear-session-handler.py` named by the policy not found | keep-as-is | judged: no hook coupling; enforcement is pipeline code de-hooking does not touch | CITED |
| 35 | `session-memory-policy.md` | CONTRADICTED | `hooks/stop_notifier/core.py:104-127` spawns `scripts/architecture/01-sync-system/session-management/auto-save-session.py`, which does not exist | delete | OAQ 2 row 11 -- deleted on the same root cause and evidence as `git-auto-commit-policy.md`, and independently scored CONTRADICTED as a confirmed no-op, with the capability loss recorded in the NFR-4 ledger | MEASURED |
| 36 | `session-pruning-policy.md` | CONTRADICTED | `hooks/stop_notifier/core.py:131-181` spawns `archive-old-sessions.py` and `session-pruner.py` under `scripts/architecture/01-sync-system/`; neither exists | delete | OAQ 2 row 12 -- deleted on the same root cause and evidence as the other two Stop-hook maintenance policies, its spawn target being absent repo-wide, with the capability loss recorded in the NFR-4 ledger | MEASURED |
| 37 | `task-phase-enforcement-policy.md` | ENFORCED | `hooks/pre_tool_enforcer/policies/task_breakdown.py:12` `check_task_breakdown_pending` -- same point as row 3 | demote-to-advisory | OAQ 2 row 13 -- demoted because phase ordering is a planning concern the pipeline already sequences, so enforcing it per tool call was always the wrong altitude | CITED |
| 38 | `task-progress-tracking-policy.md` | PARTIAL | `hooks/post_tool_tracker/policies/task_tracking.py`, `.../task_breakdown_clear.py` (both present; reach not individually traced -- LOW confidence) | port-to-MCP | OAQ 2 row 14 -- ported because it is OAQ 1's (B) replacement, namely `mcp-post-tool-tracker.increment_progress` called explicitly instead of fired by a hook | CITED |
| 39 | `test-case-policy.md` | DOCUMENTED-ONLY | NONE found as a distinct gate | demote-to-advisory | `as-built-prd.md` SS 4.2: a behavioural instruction to the calling agent, not a pipeline gate -- OAQ 2 row 2's criterion for the plugin's agent-instruction layer | CITED |
| 40 | `test-generation-policy.md` | ENFORCED | `langgraph_engine/sdlc_pipeline/test_generator.py` `detect_language:39`, `detect_test_framework:61`, `_generate_python_tests:544` | keep-as-is | judged: no hook coupling; enforcement is pipeline code de-hooking does not touch | CITED |
| 41 | `tool-optimization-policy.md` | ENFORCED | `hooks/pre_tool_enforcer/policies/read_opt.py:8` `check_read_opt`, `grep_opt.py:8` `check_grep_opt`, registered `core.py:466-467` | port-to-MCP | OAQ 2 row 4 -- ported because `mcp-token-optimizer` already implements the deterministic half, with the read-in-chunks guidance demoting to advisory as the judgement-shaped remainder | MEASURED |
| 42 | `tool-usage-optimization-policy.md` | CONTRADICTED | No distinct point. Shares row 41's registration: `hooks/pre_tool_enforcer/policies/read_opt.py:8` `check_read_opt` and `grep_opt.py:8` `check_grep_opt`, registered once at `hooks/pre_tool_enforcer/core.py:466-467`, while this policy's own text claims "NO DUPLICATION" | delete | OAQ 2 row 15 -- deleted and merged into `tool-optimization-policy.md`'s disposition because it self-claims NO DUPLICATION while sharing that policy's single enforcement point, so keeping both would preserve a documented false claim | MEASURED |
| 43 | `unicode-fix-policy.md` | ENFORCED | `langgraph_engine/preflight_guard/nodes.py:62-147` `node_unicode_fix`, wired `orchestrator.py:657`, on the `START` edge at `:663` | keep-as-is | judged: no hook coupling; enforcement is pipeline code de-hooking does not touch | MEASURED |
| 44 | `user-preferences-policy.md` | DOCUMENTED-ONLY | `langgraph_engine/sdlc_pipeline/nodes/pre_nodes.py:191` `result['user_preferences_context']` -- a passthrough state field, not a learning function | port-to-MCP | OWNER RULING 2026-08-02: preference learning is in v2.0.0 scope. Its mechanism is deterministic rather than model-judged -- a 3-occurrence learning threshold -- which is why it ports to a tool surface instead of demoting to advisory like rows 16, 28 and 39. **PRECONDITION, MEASURED 2026-08-02: `track-preference.py` is absent repo-wide, and `pre_nodes.py:191` carries only a passthrough state field, not a learning function. The port is a BUILD, not a move** | CITED |
| 45 | `version-release-policy.md` | ENFORCED | `hooks/pre_tool_enforcer/policies/push_gate.py:354` `check_push_version`, `:408` `check_push_clean_tree`, registered `core.py:464-465` | port-to-MCP | OAQ 2 row 5 -- this is `push_gate.py`, and PRD FR-23 fixes it at MANDATORY `port-to-MCP` plus ADR-017's CI-gate ordering assertion rather than leaving it to generic classification, because once FR-4 deletes the hook the version-push bypass closed by commit 1bb4303 has NEITHER preventive NOR detective cover until both `register-mcp` and that CI assertion exist, and both are DESIGNED, NOT BUILT | CITED |
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
| Post-plugin plan cells populated | **46 of 46**; **0 empty** |
| Post-plugin values outside V2-005's vocabulary | **0** |
| Basis cells populated | **46 of 46**, including all 4 ruling-decided rows |
| Verification cells populated | **46 of 46** (9 MEASURED, 37 CITED, 0 INFERRED) |

**The 9 rows whose evidence is an explicit NONE** (rows 2, 15, 16, 22, 23, 24, 28, 30, 39):
`architecture-script-mapping-policy.md`, `EXECUTION-SYSTEM-FIXES-SUMMARY.md`,
`file-management-policy.md`, `intelligent-decision-engine-policy.md`,
`intelligent-model-selection-policy.md`, `INTELLIGENT-PROMPT-GENERATION-UPGRADE.md`,
`parallel-execution-policy.md`, `proactive-consultation-policy.md`, `test-case-policy.md`.
Count of names listed: 9. Evidence density is therefore **37/46 (80.4%) real citations**.
"NONE found" is a populated evidence cell under AC2; an empty cell would not be.

### 1.2 Post-plugin plan: distribution, decision rules, and the 4 remaining empty cells

| Value | Count | Source |
|---|---|---|
| `keep-as-is` | 19 | 18 from the non-hook-coupled rule below; 1 (row 4) decided at V2-005 |
| `port-to-plugin` | 1 | row 2, owner ruling 2026-08-02 |
| `port-to-MCP` | 6 | 5 from `hld.md` SS 12 OAQ 2 (RESOLVED); 1 (row 44) owner ruling |
| `demote-to-advisory` | 9 | 5 from OAQ 2; 3 at V2-005; 1 (row 23) architect ruling |
| `delete` | 11 | 5 from OAQ 2; 5 at V2-005; 1 (row 1) owner ruling |
| *(empty)* | 0 | none remain |
| **Total** | **46** | |

**Provenance split: 15 rows from OAQ 2, 18 from the non-hook-coupled rule, 9 decided at
V2-005, 4 by owner or architect ruling.** 15 + 18 + 9 + 4 = 46. The `Basis` column makes the
split machine-readable per row: OAQ-2-sourced rows **open** with `OAQ 2 row N` followed by a
one-sentence rationale, rows from the non-hook-coupled rule are prefixed `judged:`, V2-005 rows
name the artifact that determined them, and the 4 ruling rows are prefixed `OWNER RULING` or
`ARCHITECT RULING` with the date. That prefix is deliberate: those four are DECISIONS, not
evidence findings, and a reader must be able to tell the difference.

**Match on the opening, not on a substring search.** MEASURED 2026-08-02: **19** rows contain
the string `OAQ 2 row` somewhere in `Basis`, but only **15** open with it. The other four are
rows 16, 26, 28 and 39, which *quote* an OAQ 2 criterion (row 1's or row 2's) as the reasoning
they borrow while being dispositioned at V2-005, not by OAQ 2. A grep for `OAQ 2` returns 19 and
would overstate the OAQ-2-sourced set by four; the anchored form `^OAQ 2 row \d+` returns exactly
the 15. Both figures are enumerable from the matrix above.

**Where a `Basis` cell carries a `MEASURED` tag, that tag qualifies the disposition's
evidence, not the row's `Verification` value.** No row was upgraded to MEASURED by this
pass; the 9 MEASURED / 37 CITED split of section 1.1 is unchanged.

**The 15 OAQ-2 rows are exactly the 15 hook-coupled policies.** MEASURED: filtering
`policy_enforcement_raw.json` on `hook_coupled_by_implementation == true` returns 15 records,
and that set is **identical** to OAQ 2's 15 table rows -- asserted by set equality at
generation time, so neither set contains a policy absent from the other. OAQ 2's totals
(5 port-to-MCP, 5 demote-to-advisory, 5 delete) reconcile with the per-row values
transcribed here.

**Rule 1 -- the non-hook-coupled `keep-as-is` rule.** Stated so it can be checked rather
than trusted:

> A non-hook-coupled policy is assigned `keep-as-is` **only if** it has a live enforcement
> point in pipeline code (status ENFORCED or PARTIAL). In that case de-hooking provably does
> not touch it: its enforcement is in `langgraph_engine/` or `src/mcp/`, not in a hook, so it
> continues to behave exactly as it does today. That is a real decision backed by the
> Evidence cell, not a neutral filler.

This yields **18 `keep-as-is`** (12 ENFORCED, 6 PARTIAL). It reaches no CONTRADICTED,
STALE-TOPOLOGY or DOCUMENTED-ONLY row, which is why 13 cells stood empty until V2-005.

#### 1.2.1 The 9 dispositions decided at V2-005, and the evidence for each

An earlier revision left all 13 empty on the grounds that no source artifact reached them.
That was right about OAQ 2, which scopes itself to the hook-coupled 15 and stops -- but it
was not right that *nothing* on disk reaches them. Nine do resolve, against evidence a
reviewer can open. Each is derived from a named artifact or from the policy's own text; none
rests on plausibility.

| # | Policy | Plan | Determining evidence |
|---|---|---|---|
| 4 | `callgraph-analysis-policy.md` | `keep-as-is` | `prd-v2.md`'s superseding FR-9a AC (owner ruling, in v2.0.0 scope) and `hld.md` OAQ 4 / ADR-013 both repair the two binding caps *in pipeline code*. The row is the one case where `keep-as-is` does **not** mean shipping a known-broken policy unchanged: v2.0.0 has a scoped, runtime-proved fix for its enforcement point, and that point is not in a hook |
| 15, 24 | the two changelogs | `delete` | `as-built-prd.md` SS 4.2 classifies both as point-in-time changelog entries, "not an ongoing SHALL". ADR-009 scopes `docs/policies/` to the policy corpus the plugin bundles; a changelog carries no capability, so removal writes nothing to the NFR-4 ledger, and `docs/policies/` is under git, so unlike ADR-009b's `~/.claude/` slate the removal is recoverable |
| 22 | `intelligent-decision-engine-policy.md` | `delete` | MEASURED 2026-08-02: the script path it names (`scripts/architecture/03-execution-system/04-model-selection/`) does not exist, and `OpenRouter` -- its declared and only LLM provider -- has zero references in `langgraph_engine/`, `src/` or `scripts/`. All four systems it claims to unify were removed in v1.13, and the provider chain was cut to two in v1.15.3. This is `prd-v2.md` SS 8's own delete rationale applied to the row it did not reach: porting it forward resurrects governance over a step that no longer exists |
| 26 | `mcp-plugin-discovery-policy.md` | `delete` | The sharpest case in the earlier revision, and it resolves against ADR-019 rather than for `port-to-plugin`. Its Step 1 imports `MCPPluginLoader` from `mcp_plugin_loader`, which is absent repo-wide with zero importers (MEASURED 2026-08-02; a stale `.pyc` is the only trace). Its AUTO-ROUTE mode configures `pre-tool-enforcer.py`, which ADR-010 and FR-4 delete. Its discovery model -- scan and auto-enable -- is exactly what ADR-019 replaces with explicit opt-in `register-mcp`, guarded refuse-by-default by ADR-020. Keeping it guarantees the permanent contradiction with shipped behaviour that OAQ 2 row 1 gives as its stated reason to delete `hook-system` |
| 30 | `proactive-consultation-policy.md` | `delete` | The policy's own header: `Status: DEPRECATED (2026-03-17)`, with the reason (`AskUserQuestion` is unavailable in subprocess execution) and three named replacements. No external artifact is needed |
| 16, 28, 39 | `file-management`, `parallel-execution`, `test-case` | `demote-to-advisory` | All three are model-judged conduct with no gate anywhere in the codebase -- `as-built-prd.md` SS 4.2 says so in as many words for two of them ("calling-agent behavior ... not a pipeline capability"; "a behavioral instruction to the calling agent, not a pipeline gate"). OAQ 2 row 2 states the criterion this pass applies: conduct that is model-judged "belongs in the plugin's agent-instruction layer, not a gate." That criterion is not hook-specific, which is why it transfers; OAQ 2 simply never reached these rows. `keep-as-is` is excluded by Rule 1 (no enforcement point exists to keep), and `delete` would drop live rules with nothing recording the loss |

**On the transfer in the last row, stated so it can be rejected cleanly.** OAQ 2 row 2's
criterion is applied to three policies OAQ 2 did not disposition. That is a deliberate
extension of a stated rule to rows sharing its stated precondition, not a new decision -- but
it is the weakest link among the nine, and a reviewer who thinks a criterion must not travel
outside its section's scope should strike these three back to empty rather than to a
different value.

#### 1.2.2 The 4 closed by ruling rather than by evidence

`keep-as-is` would assert that v2.0.0 ships a known-broken policy unchanged; a placeholder
such as "UNDECIDED" would be non-empty while encoding that no decision was made, satisfying
the letter of FR-2 and FR-20 while defeating exactly what both exist to force -- structurally
the same escape hatch NFR-4 closes when it forbids a "disappeared" disposition. Neither is
used. These four rows carry an empty cell because the choice between two genuinely available
options is a product or architecture ruling, and no artifact on disk makes it.

| # | Policy | What is missing | Who decides |
|---|---|---|---|
| 1 | `anti-hallucination-enforcement.md` | Whether v2.0.0 wants a prompt-quality gate at all. The module is on disk with zero importers, so wiring it up costs about what deleting it costs; `as-built-prd.md` SS 4.2 declined to map it to any FR because the mapping would be manufactured | Product owner, as a new FR or an explicit decision not to have one |
| 2 | `architecture-script-mapping-policy.md` | Whether `scripts/architecture/` survives v2.0.0. MEASURED 2026-08-02: 0 of the 3 scripts it maps exist, and `03-execution-system/00-code-graph-analysis/code-graph-analyzer.py`, which does exist, is unlisted -- the inventory is wrong in both directions, so correcting it is as available as deleting it. FR-9a's 17-site enumeration keeps that file alive as a live-but-non-binding cap, so nothing schedules the tree's removal | Owner, on the tree; the policy's disposition follows mechanically |
| 23 | `intelligent-model-selection-policy.md` | A retranslation against the current topology. Only one of its five inputs (plan-mode decision) was deleted in v1.13; model selection itself is live (`langgraph_engine/version_selector.py` exists, MEASURED), so the policy is stale rather than obsolete and rewriting it around the remaining four inputs is a real option | Architect. No OAQ covers it; unlike OAQ 4 for row 4, there is no resolved fix to point at |
| 44 | `user-preferences-policy.md` | Whether preference learning is in v2.0.0 scope. Unlike rows 16/28/39 this policy specifies a *deterministic* mechanism -- a 3-occurrence threshold and a `track-preference.py` that is absent repo-wide (MEASURED 2026-08-02) -- so `port-to-MCP` (OAQ 2 row 7's lookup-table criterion) and `delete` are both live. `prd-v2.md` FR-10 calls its selection ad hoc but scopes its own fix to KG-driven agent/skill selection, not preference persistence | Product owner |

Count check: 9 decided from evidence + 4 decided by ruling = 13, matching the earlier
revision's empty set.

**These 4 were closed on 2026-08-02 by owner and architect rulings, and are labelled as
rulings rather than as findings.** They stayed empty until then rather than being filled with
a placeholder, and the AC7 gate failed on them for exactly that period -- which is how they
reached a decider instead of passing review unnoticed. PRD FR-2 and FR-20 are now satisfied
for all 46 rows.

**Two carry preconditions that the disposition alone does not convey**, recorded on the rows
themselves: row 2's mapping is wrong in both directions, so porting it as written would carry
a broken inventory into the plugin; and row 44's `track-preference.py` is absent repo-wide, so
its port is a BUILD rather than a move.

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
  Basis cell **opens with** `OAQ 2 row N`. **MEASURED 2026-08-02, derived independently:** the
  set was re-enumerated from `as-built-prd.md` SS 6.3 (4 self-declaring + 11 undeclared),
  resolved to corpus filenames, and compared to the 15 anchored-`OAQ 2 row N` rows as a
  symmetric difference in both directions. **Empty both ways -- the two sets are identical.**
  Their OAQ 2 row numbers also map one-to-one, and every disposition transcribed here matches
  OAQ 2's, reproducing its 5 `port-to-MCP` / 5 `demote-to-advisory` / 5 `delete` split.
- **All 15 now carry a one-sentence rationale alongside the citation.** Before this pass all 15
  `Basis` cells read the bare token `OAQ 2 row N` and none carried a rationale, so **15 of 15
  genuinely needed one added**; none was a duplicate of an existing sentence. The rationales are
  CITED from `hld.md` SS 12 OAQ 2's own `Rationale` column, condensed to one sentence each, not
  newly reasoned here.
- **The set is right but the usual shorthand for it is wrong, and the shorthand should not be
  reused.** These 15 are often described as the policies "whose sole enforcement mechanism is a
  PreToolUse block". Counted against this matrix's own `Evidence` cells (MEASURED 2026-08-02),
  only **8** of the 15 are PreToolUse *blocks* (rows 3, 9, 10, 20, 37, 41, 42, 45). Of the
  remaining 7: row 7 is PreToolUse but its own Evidence records it as called **non-blocking**;
  rows 18, 35 and 36 are **Stop**-hook coupled; row 38 is **PostToolUse** (`hooks/post_tool_tracker/`);
  and rows 21 and 27 cite no `hooks/` path at all, their Evidence resolving to pipeline code.
  8 + 1 + 3 + 1 + 2 = 15. `as-built-prd.md` SS 6.3 itself says "hook-coupled", never "PreToolUse",
  so the membership of the set is not in doubt -- only the descriptor is. Anyone scoping work
  from the PreToolUse phrasing rather than from the enumeration will scope it to roughly half
  the set.
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
3. **4 of 46 post-plugin plan cells are empty** because the choice between two available
   options was a product or architecture ruling no artifact on disk made. All four were
   ruled on 2026-08-02 and are recorded as rulings in section 1.2.2.
4. **`port-to-plugin` is assigned to zero rows.** No source assigns it, and this pass did not
   infer it. `mcp-plugin-discovery-policy.md` was the candidate and resolved the other way:
   ADR-019 replaces auto-discovery with opt-in registration, so the row is `delete` on
   evidence rather than `port-to-plugin` on plausibility (section 1.2.1). A zero count here
   is a finding, not an omission.
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
  19 `keep-as-is`, 6 `port-to-MCP`, 9 `demote-to-advisory`, 11 `delete`, 1 `port-to-plugin`,
  **0 empty**. Provenance: 15 from OAQ 2, 18 from the non-hook-coupled rule, 9 decided at
  V2-005 against named evidence, 4 by owner or architect ruling on 2026-08-02.
- **The final 4 cells were closed by ruling on 2026-08-02, not by evidence**, and are
  labelled as such so the distinction survives; section 1.2.2
  names the missing input and the deciding role for each.
- **All 15 hook-coupled rows now carry a disposition AND a one-sentence rationale.** All 15
  previously held the bare token `OAQ 2 row N`, so 15 of 15 genuinely needed one; the rationales
  are condensed from `hld.md` SS 12 OAQ 2's own `Rationale` column, not newly reasoned. The
  15-row set was re-derived independently from `as-built-prd.md` SS 6.3 and matched the
  OAQ-2-sourced rows exactly, symmetric difference empty in both directions (section 7).
- **`push_gate.py`'s row (row 45, `version-release-policy.md`) reads `port-to-MCP`**, fixed
  there by PRD FR-23 rather than open to generic classification. **It already read `port-to-MCP`
  before this pass and its value was not changed**; only its rationale was added, recording that
  after FR-4 the bypass closed by commit 1bb4303 has neither preventive nor detective cover until
  `register-mcp` and the ADR-017 CI assertion exist, and that both are DESIGNED, NOT BUILT.
- **"Sole enforcement mechanism is a PreToolUse block" is the wrong descriptor for the 15** --
  only 8 of them are, by this matrix's own Evidence. The enumeration in `as-built-prd.md` SS 6.3
  is authoritative; the shorthand is not. Section 7 carries the breakdown.
- **"46/46 orphan policies" retracted**; real figure 14 of 46, six beyond any SRS fix.
- **Three maintenance policies are dead paths today**, before any hook change; all three are
  `delete` under OAQ 2.
- **7 of 9 Stop-hook target scripts absent**; an 8th exists but not where the hook looks.
- **The audited corpus is not the runtime corpus**: 6 runtime policies never audited, 18
  audited policies absent at runtime.
- **AC3 not satisfied**, and not claimed.
- **37 of 46 classifications remain CITED.** Best available, not verified.

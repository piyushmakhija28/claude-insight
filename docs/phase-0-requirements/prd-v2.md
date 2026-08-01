# PRD v2.0.0 -- Hook-Free Plugin Transformation (Normalised Requirement Set)

**Phase:** 2.1 -- Business Analysis reconciliation against the APPROVED Phase 1 HLD (originally
authored at Phase 0, pre-HLD; this is the post-HLD reconciliation pass)
**Author:** business-analyst-agent
**Date:** 2026-08-01
**Version:** 1.2 (see Section 13 Change Log — header corrected by orchestrator 2026-08-01; the 1.2 Change Log row had been added without bumping this field)
**Status:** Reconciled against `hld.md` (APPROVED, consensus iteration 4) and `plugin_schema_spike.md`
(5/5 FR-14a items measured) -- Section 9's ADR-009b sign-off item is UNAFFECTED by this pass and
remains blocking for FR-19
**Target repo:** `claude-workflow-engine` v1.21.4 -> v2.0.0

**Skill files requested but ABSENT from the library** (per task instruction, reporting rather than
substituting): `skills/requirements-elicitation/SKILL.md`, `skills/acceptance-criteria-definition/SKILL.md`,
`skills/requirements-traceability/SKILL.md` do not exist under
`claude-global-library/skills/`. The closest existing library skills are
`business-requirements-analysis-core`, `requirements-traceability-core`,
`acceptance-testing-bdd-core`, and `bdd-acceptance-testing-core`, but the task instruction was to
skip absent files, not silently substitute, so none of the four were read or applied. This document
follows the task's own explicit instructions (validate -> measurable AC -> RTM -> Gherkin) instead.

---

## 1. Purpose and Method

This document reconciles two things that currently disagree in dateable, evidenced ways:

1. The **AS-IS truth**: `docs/phase-0-reverse-engineering/as-built-prd.md` (512 lines, Appendix E
   gap analysis, Appendix F open questions), generated 2026-08-01 from static analysis of the
   working tree.
2. The **TO-BE requirement**: `docs/releases/v2.0.0-plugin-transformation-requirements.md`
   (FR-1..FR-18, NFR-1..NFR-5, AC-1..AC-7), plus `docs/orchestration_prompt.md`, which was generated
   from the SAME Phase 0 execution and carries amendments made AFTER the Appendix E gap table was
   frozen (ADR-006..010, FR-4a, FR-8a, FR-9a, FR-14a, ADR-009a, ADR-009b, the STALE-TOPOLOGY status).

Where the two disagree, this document treats `orchestration_prompt.md` as the later, more-measured
source (it cites file:line evidence gathered after Appendix E was written) and says so explicitly at
each point of disagreement, rather than silently picking one.

**Hard rules honoured throughout:** FR-1..FR-18, NFR-1..NFR-5, AC-1..AC-7 keep their original numbers.
New requirements get new IDs (FR-19 onward) or reuse an ID the execution phase already minted (FR-4a,
FR-8a, FR-9a, FR-14a). ADR-006..010, 009a, 009b are treated as settled; this document flags
consequences, it does not reopen them.

---

## 2. Validated Functional Requirements (FR-1..FR-18)

Verdict column reconciles Appendix E (as-built-prd.md) against `orchestration_prompt.md`'s later
measurements. "AGREE" means both sources land on the same verdict; "REVISED" means
`orchestration_prompt.md` supersedes Appendix E's wording with new evidence.

| FR | Statement (short) | Appendix E verdict | Reconciled verdict | Note |
|----|---|---|---|---|
| FR-1 | Read/internalise all policies | Partial | **AGREE -- Partial** | This synthesis pass itself is the read-and-normalise evidence; `~/.claude/policies/` inventoried but not re-read line-by-line. |
| FR-2 | Policy implementation matrix | Partial | **AGREE -- Partial** | `policy_enforcement_raw.json` has 5 of 7 required columns for all 46 policies; missing "Post-plugin plan" column and the required file path `docs/reports/policy-implementation-audit-v2.md` does not exist yet. |
| FR-3 | Classify policies surviving de-hooking | Partial | **AGREE -- Partial, scope corrected** | `capability_loss.md` enumerates 25 lost capabilities but zero recorded per-policy demotion decisions. `orchestration_prompt.md` (Consequence 2, FR-4a) additionally NAMES one disposition as MANDATORY rather than open: the version-push gate (`push_gate.py`) must be `port-to-MCP`, not left to generic classification -- see FR-23 below. |
| FR-4 | Delete PreToolUse/PostToolUse | Not started | **AGREE -- Not started, blast radius now measured** | Both fully wired today. `orchestration_prompt.md` FR-4a adds a structural finding Appendix E did not have: 135/2,218 nodes (6.09%) go dark, zero surviving cross-boundary edges after confidence verification -- deletion is structurally safe. Capability-level safety is a separate question (see FR-4a consequences 1-3, Section 10). |
| FR-5 | Remove UserPromptSubmit from hot path | Not started | **AGREE -- Not started** | `scripts/3-level-flow.py` remains the registered entry point, 120s timeout, unchanged. |
| FR-6 | ADR-006 trade-off documented | Not started | **REVISED -- Now satisfied** | Appendix E found no `ADR-006-hook-free-execution.md` file. `orchestration_prompt.md` Section 5 now contains the full ADR-006 text (chosen/why/rejected/consequence), pre-committed by the user. The written artifact at the required path (`docs/architecture/ADR-006-hook-free-execution.md`) still needs to be created from that text -- content exists, file does not. |
| FR-7 | Explicit entry points / slash commands | Not started | **AGREE -- Not started** | No slash-command layer exists; `orchestration_prompt.md` Section 1.2 restates the minimum set (plan/decompose, implement, review, document, release, plus one full-pipeline command) as design input, not as delivered code. |
| FR-8 | Stop/Notification hook fate decided | Not started as decision, data exists | **REVISED -- Decided, then re-opened as FR-8a** | `orchestration_prompt.md` Section 1.2 states FR-8 is now formally resolved (keep both) -- but immediately reclassifies the "keep" as conditional via FR-8a: Stop fires every response turn, not once per session as FR-8's original rationale assumed, at an initially-measured 8-spawn floor (16 with retries) -- a figure since SUPERSEDED to a true floor of ~2, because 7 of the 9 referenced scripts were verified absent and their guards never fire (see FR-21 and Section 10). "Keep" survives, but "keep everything it currently runs" does not -- FR-8a is a mandatory audit-and-reduce follow-on. See Section 5 for the FR-8a measurable AC. |
| FR-9 (v2.0.0: library count drift) | Resolve 541/1030 vs 506/993 drift | Out of repo scope, not assessed | **REVISED -- Assessed, narrower than described** | Appendix E marked this "out of this repo's scope" because it concerns `claude-global-library`. `orchestration_prompt.md` (read-only inspection of that library, permitted under the v2.0.0 doc's own scope) found the drift is NOT filesystem-vs-README as the requirement doc assumed: `knowledge-graph/_master/README.md` (505/992) already matches the filesystem; the stale artifact is `master_graph.md` alone, from an earlier same-session build (21:33 vs 21:42 on 2026-07-31). Fix is narrow: `build_master.py --full` regeneration + `validate.py` + `test_invariant_checker.py`, not a full graph rebuild. **Flag:** the fix still executes inside `claude-global-library`, so "out of repo scope" is correct for WHO does the work; "not assessed" is no longer correct -- it was assessed and scoped down. Do not carry forward the original doc's larger drift framing. |
| FR-10 | KG-driven selection, zero hardcoded lists | Contradicted | **AGREE -- Contradicted, with a named prerequisite defect** | No graph-query-based selection exists anywhere in live scope; `user-preferences-policy.md` selection is ad hoc. `orchestration_prompt.md` adds FR-9a (below): the call-graph risk signal FR-10 is supposed to consume comes from a builder that is itself blind to 100% of `sdlc_pipeline/`. Building the selector before fixing the builder would make FR-10 "done" against worthless inputs. |
| FR-11 | Selection explainability | Not assessed in code | **AGREE -- Not assessed** | No selection-explainability mechanism exists to assess; this is a build-from-scratch requirement, not a partial one. |
| FR-12 | No-match/low-confidence fallback | Not assessed in code | **AGREE -- Not assessed** | Same as FR-11 -- no code exists yet. |
| FR-13 | Model fallback protocol respected | Not assessed in code | **AGREE -- Not assessed as code, but the rule exists** | `~/.claude/rules/model-fallback.md` (global-only -- no repo-relative copy exists) is a live, standing Claude Code rule (haiku->sonnet->opus->escalate); it is a behavioural contract on the calling agent, not code in this repo, so "not assessed in code" is accurate but should not be read as "does not exist." |
| FR-14 | Installable plugin manifest | Not started | **REVISED -- Research complete, spike complete, build not started** | Appendix E found zero manifest files (still true -- build has not started). `orchestration_prompt.md` Section 1.4's pre-build verification was COMPLETE as of 2026-08-01. **(Phase 2.1 reconciliation, item 5)** `plugin_schema_spike.md` now closes the remaining blocking unknowns: all 5 FR-14a items (the spike grew from 4 to 5 per `hld.md` ADR-018) are MEASURED, none PROVISIONAL. Item 1: `${CLAUDE_PLUGIN_ROOT}` DOES resolve inside `.mcp.json` `command`/`args` (substituted at spawn time). Item 2: `CLAUDE_PLUGIN_ROOT` IS present in a spawned Python process's `os.environ`, alongside `CLAUDE_PLUGIN_DATA` and `CLAUDE_PROJECT_DIR` -- this de-risks but does not gate ADR-012's design, since ADR-012 already made manifest-anchored ascent (not the env var) the primary mechanism; the env var now serves only as a confirmed corroborating override. Item 3: `/plugin install` writes exactly `extraKnownMarketplaces` (on marketplace add) and `enabledPlugins` (on install), no other top-level `settings.json` keys touched. Item 4: see the revised FR-18 row above. Item 5 (ADR-018's addition): MCP servers spawn eagerly on plugin enable, zero tool calls needed -- see the revised NFR-1 row above. **"Not started" remains the correct verdict for the manifest artifact itself; every empirical unknown that used to block the packaging design is now closed.** **[Phase 2.1 addendum, post-dating item 5's resolution]** ADR-019 (zero bundled MCP servers, superseding ADR-018's minimum-viable-bundle mitigation) has a consequence for FR-14 that this pass records explicitly rather than lets pass silently: FR-14's original wording promises the plugin is installable in one step, and names MCP server references among the bundled content that step delivers. Under ADR-019, `/plugin install` alone delivers commands, agents, and skills -- a complete, functional surface with no hand-edited `settings.json` required, so "no manual surgery" still holds in full. But MCP-backed capabilities (the FR-23 push gate, the progress writer) are NOT available after that one step; they require a second, explicit `register-mcp` command the user must separately choose to run. **"One step" is therefore no longer accurate for the full capability set, and this document amends FR-14's acceptance criterion below to say so, rather than leaving FR-14 read as though one-step install of everything is still promised.** This is recorded as an accepted, deliberate trade-off (the alternative -- bundling MCP to preserve one-step install -- reopens NFR-1, per the revised NFR-1 row above) and not as an unflagged regression. |
| FR-15 | Self-contained, path_resolver everywhere | Partial | **AGREE -- Partial, count corrected** | Original Appendix E language said 13-of-many; `orchestration_prompt.md`'s Encoding Contract addendum narrows this precisely: of 116 total home-directory references, only 13 are live-code defaults needing replacement (the other 103 are comments/docstrings) -- the remediation surface is 13 call sites, not 116. `path_resolver.py` itself is comprehensive (23 top-level functions, verified 2026-08-01; it lives at `src/utils/path_resolver.py`) and 0 absolute path literals exist anywhere (positive finding, not a gap). |
| FR-16 | Bundle, do not duplicate | Not started | **REVISED -- Design settled, build not started** | Appendix E found no bundling/sync mechanism. `orchestration_prompt.md` Section 1.4 records the user decision: pinned build-time snapshot (ADR-007) of routing registries + only the personas for dispatchable agents, not all 505 agent directories, with a `CLAUDE_PLUGIN_DEV_MODE=1` escape hatch for local iteration. Verdict for the artifact stays "not started"; the open design question Appendix E implicitly left (which mechanism?) is now closed. |
| FR-17 | Cross-platform correctness | Partial | **AGREE -- Partial, count corrected** | 0 absolute path literals (fully compliant) confirmed by both sources. Unencoded `open()` count is corrected upward from Appendix E's already-corrected 19 -- `orchestration_prompt.md`'s Encoding Contract addendum re-verifies 19 as the accurate figure (not 12) and adds that any detection tooling must catch the mode-less `open(path)` form, which the original 12-count grep missed. |
| FR-18 | Clean uninstall | Not started | **REVISED -- Not started, AND the AC as originally written is unachievable; narrowed below** | **(Phase 2.1 reconciliation, item 4)** No install/uninstall lifecycle code exists -- that part is unchanged. But `plugin_schema_spike.md` Item 4 (now MEASURED, not open) empirically closes the spike FR-14a assigned, and the result is that FR-18's original bar -- "uninstall leaves no orphaned files, MCP registrations, or settings entries" -- **cannot be met by any plugin design**, because the residue is produced by Claude Code's own `claude plugin uninstall`, which the plugin does not control and cannot intercept (no uninstall-time execution point exists for a plugin, the same structural gap `hld.md` ADR-012 already found at install time). Measured: (a) `settings.json`'s `enabledPlugins` and `extraKnownMarketplaces` keys are emptied to `{}` on uninstall/marketplace-remove, not removed -- functionally inert (they re-enable nothing) but a byte-level and structural difference from a pre-install baseline; (b) the plugin's cache directory under `~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/` survives uninstall with a `.orphaned_at` marker, all files intact; (c) `claude plugin prune` does NOT clean this residue -- its own help text scopes it to "auto-installed dependencies," not a manually installed-then-uninstalled plugin. **This is stated plainly, not quietly narrowed: the original "no orphaned files, MCP registrations, or settings entries" AC was unachievable as written**, because it implicitly assumed the plugin (or `claude plugin uninstall`) has a cleanup mechanism that does not exist. See the rewritten AC in Section 5 and the new FR-24 below. |
| **FR-9 (SRS.md: Hook System)** | *Not a v2.0.0 requirement -- flagged because of a naming collision* | Direct AS-IS-vs-TO-BE conflict | **AGREE -- Contradicted, and unresolved** | `SRS.md:131` and its AC at `SRS.md:206` state all four hook events fire and a blocking PreToolUse policy returns exit code 2. v2.0.0 FR-4/FR-5 propose removing two of those four events. Per `rules/44` (append-only), this SRS text cannot be edited in place. Neither source names an owner for the required SRS supersession entry -- see new FR-22, Section 4. **Naming collision warning: this is SRS.md's own FR-9, unrelated in content to v2.0.0's FR-9 (library count drift) above. Every reference to "FR-9" in downstream artifacts must specify which document it comes from.** |

**Appendix E internal inconsistency flagged:** `as-built-prd.md`'s own summary line says "4 partial
(FR-1, FR-2, FR-3, FR-15, FR-17 -- 5 partial)" -- the prose says 4, the parenthetical says 5, and the
list itself has 5 entries. This document treats 5 as authoritative (the enumerated list is the primary
evidence; "4" is a transcription slip in the summary sentence) and used 5 throughout.

**Count summary (reconciled):** 0 of 18 fully satisfied. 5 partial (FR-1, FR-2, FR-3, FR-15, FR-17).
1 contradicted (FR-10). 2 revised-from-"not started"-to-"researched/designed, not built"
(FR-6 content exists / FR-14 research complete / FR-16 design settled -- three FRs moved from blind
to scoped, though none moved to "done"). 1 revised-from-"out of scope"-to-"assessed and narrowed"
(FR-9 library drift). 9 remain "not started" or "not assessed in code" with no new information
(FR-4, FR-5, FR-7, FR-11, FR-12, FR-13, FR-18, plus FR-8 whose "not started" reclassifies as
"decided-then-partially-reopened" via FR-8a, and FR-3 whose partial status gains one mandatory
sub-disposition via Consequence 2).

---

## 3. Validated Non-Functional Requirements (NFR-1..NFR-5)

| NFR | Statement | Appendix E verdict | Reconciled verdict | Note |
|---|---|---|---|---|
| NFR-1 | Zero overhead when uninvoked | Contradicted by current architecture | **REVISED -- Contradicted, AND the acceptance criterion itself was ill-defined until per-component attribution was added** | **(Phase 2.1 reconciliation, ADR-018 + `hld.md` SS 9)** All four active hooks fire unconditionally today -- that finding is unchanged. But the retained Stop hook (ADR-010 keeps it; the plugin never owned it) is itself claude-workflow-engine code living in this repo, holds >=17 subprocess spawn sites, and fires every response turn. A delta=0 measurement window spanning a turn boundary would therefore record a non-zero delta caused by a component the design deliberately keeps -- the original AC ("delta = 0 processes attributable to claude-workflow-engine") could never pass as worded, independent of anything the plugin does. The AC must attribute per component: pass = 0 processes attributable to **the plugin specifically** (its `.mcp.json` servers and command entry points), explicitly excluding the user-level Stop and Notification hooks. Separately, `plugin_schema_spike.md` Item 5 (now MEASURED, not open) found plugin-registered `.mcp.json` stdio servers ARE spawned on plugin enable with zero tool calls made (2 confirmed process spawns in an isolated session that never invoked the plugin) -- so a design that bundles all 13 MCP servers as always-on plugin entries fails NFR-1 by construction. **SUPERSEDED at Phase 2.1 by ADR-019, not disputed -- this constraint was correct when written and was overtaken by measurement, not by an analysis error.** ADR-018's minimum-viable-bundle mitigation (bundle only the FR-23 push gate and the progress writer) is no longer the design: `plugin_schema_spike.md` Item 5 measured that even a two-server minimum-viable bundle spawns on enable with zero tool calls, so ANY bundled `.mcp.json`, however small, fails NFR-1 the same way a 13-server bundle does. solution-architect's decisive argument: NFR-1 already took one carve-out (the retained Stop hook, via per-component attribution); a second carve-out for "small enough" bundled MCP would leave nothing that could make NFR-1 fail -- a metric that cannot fail measures nothing. **Decision: the plugin bundles ZERO MCP servers (ADR-019).** All MCP registration, including the FR-23 push gate and the progress writer, moves to an explicit opt-in `register-mcp` command the user runs as a separate step after install. |
| NFR-2 | No fixed per-call timeout | Contradicted by current architecture | **REVISED -- Contradicted on a wider surface than scoped; hook deletion does not satisfy it** | **(Phase 2.1 reconciliation, ADR-016)** Every active hook carries a fixed timeout (60s x3, 120s x1) -- that part is unchanged. But `hld.md` SS 4.2 ADR-016 found NFR-2 is **already violated inside the engine, on the pipeline path, independently of hooks**: 6 `timeout=` APPLICATION sites across 5 files (`prompt_gen_expert_caller.py:228`, `todo_decomposer.py:147`, `orchestrator_agent_caller.py:137`, `todo_executor.py:114`, `task_orchestration.py:160`, `task_orchestration.py:217`) plus 3 DEFINITION sites (2 module-level constants -- `STEP1_PROMPT_GEN_TIMEOUT` default 60 at `prompt_gen_expert_caller.py:54`, `STEP1_TODO_DECOMPOSER_TIMEOUT` default 90 at `todo_decomposer.py:37` -- and 1 function-local read at `task_orchestration.py:128`). `task_orchestration.py:160` composes to a 75-second fixed wall-clock timeout on the Step 1 pipeline path (`_pg_inner_timeout + 15` = 60 + 15). None of these 9 sites appear in any Phase 0 artifact -- Phase 0 scoped NFR-2 to the 4 hook timeouts only. **Deleting the hooks (FR-4/FR-5) does not satisfy NFR-2; it satisfies only the hook half of a two-part defect.** The HLD's accepted design (ADR-016) replaces the aborting timeout with five non-temporal liveness mechanisms -- attempt-count abort (not elapsed-time abort), lease renewal in place of a fixed deadline, a convergence/no-progress signal, a circuit breaker per external dependency (claude CLI, GitHub, Jira, Anthropic API) with exponential reopen-wait and full-jitter retry, and slow-call-rate as a trip signal rather than a per-call abort. One exception is explicitly permitted: socket/HTTP-level timeouts on a single network I/O call remain allowed, provided they raise into the circuit breaker rather than aborting the enclosing pipeline task. |
| NFR-3 | Observability after de-hooking | Not designed | **REVISED -- The premise was a conflation of two systems; correctly scoped, NFR-3 is MET and cheaper than believed** | **(Phase 2.1 reconciliation, ADR-011 / OAQ 1)** The prior verdict rested on treating `post_tool_tracker.py` as "the sole writer of session-progress/checkpoint state." `hld.md` SS 12 OAQ 1 verified this directly against live source and found it conflates **two independent systems**. **(A) Step-boundary crash recovery** -- `langgraph_engine/checkpoint_manager.py::CheckpointManager` (9 public methods + `_atomic_write`), triggered at every step boundary by `core/step_decorator.py` (`save_success_checkpoint`, `save_failure_checkpoint`) on both the success and failure path, with a real resume entry point (`orchestrator.py::resume_flow` -> `quality/recovery_handler.py::resume_from_checkpoint`). This is hook-independent, lives entirely outside the three deleted hook packages, and SURVIVES FR-4 untouched -- it is exactly the granularity SRS's "resume from any step after crash" guarantee is written at. **(B) Per-tool-call progress** -- `hooks/post_tool_tracker/progress_tracker.py`, finer-grained than any SRS step guarantee, and this part genuinely dies with FR-4. Its replacement is the existing `mcp-post-tool-tracker` MCP server, called explicitly by the pipeline as a *projection of the checkpoint record*, not an independent writer (avoids a dual-write split-brain between state and progress). **Corrected verdict: NFR-3 is closer to telemetry loss (system B) than crash-recovery loss (system A) -- the crash-recovery guarantee was never at risk.** Three binding durability defects remain to fix, not a build-from-scratch task: (1) `step_decorator.py:169` currently swallows a checkpoint-save failure with a warning and continues -- a best-effort write cannot back a contractual guarantee; it must raise or set an explicit `checkpoint_degraded` flag the resume path refuses to trust; (2) checkpoint and progress must not become a dual write -- addressed by the projection design above; (3) replay must be idempotent, since resume re-executes from the last successful step boundary (session id + step number is the natural idempotency key for side-effecting steps like GitHub issue creation). **Separately corrected: the "PostToolUse-backed warm-daemon" attribution in the prior verdict is wrong.** The warm daemon lives at `hooks/pre_tool_enforcer/daemon.py` and is reached from the PreToolUse hook, not PostToolUse -- a grep of the PostToolUse packages returns no daemon reference. Both hooks are deleted regardless, so the capability is lost either way, but a replacement must not be designed against the wrong component; its replacement is structural (an MCP stdio server is already warm/long-lived), subject to the same NFR-1/ADR-018 eager-spawn caveat. **Flagged for product-manager-agent:** `product-sequencing-v2.md` SS 2 sizes "NFR-3 replacement crash-recovery writer" at 8 points / WSJF 3.00 on the premise that a new writer must be built from scratch. That premise is inaccurate -- the writer already exists -- and the estimate should be revisited; re-sizing is Workstream B's call, not this document's. |
| NFR-4 | No silent regression | Precondition satisfied, decision not made | **AGREE -- Precondition satisfied, decision not made** | `capability_loss.md` is exactly the required "every capability gets a disposition" ledger (25 capabilities named); none of the 25 yet carries a decided disposition. |
| NFR-5 | Install/invoke/uninstall each tested | Not started | **AGREE -- Not started, and now has a named blocking prerequisite** | No install/uninstall code exists. FR-14a's four empirical spike questions (Section 5) are a stated BLOCKING prerequisite before packaging design -- and therefore before NFR-5 tests can even be written, since the spike determines what "clean uninstall" is measured against. |

---

## 4. New FRs Surfaced by As-Built Analysis

None of these renumber an existing FR. FR-4a/FR-8a/FR-9a/FR-14a were already minted during Phase 0
execution and are carried forward, not reinvented. FR-19 onward are new IDs proposed by this pass.

| ID | Requirement | Why the as-built analysis proves it is needed | Status |
|---|---|---|---|
| **FR-4a** (existing, carried forward) | Blast-radius measurement + 3 named consequences of hook deletion | Already minted in `orchestration_prompt.md`. Structural blast radius is small (6.09%, zero surviving edges) but 3 capability-level consequences do NOT reduce to "safe": SRS FR-9 violation, version-push-gate bypass reopening, NFR-3 crash-recovery loss. | Measured; consequences un-actioned |
| **FR-8a** (existing, carried forward) | Stop-hook overhead audit-and-reduce | **Floor figure SUPERSEDED (2026-08-01) -- read with FR-21 below.** Initially measured at 8 spawns/turn (16 with retries) against the docstring's "4+". That measurement assumed the gated target scripts exist. 7 of the 9 referenced scripts were subsequently verified ABSENT, so their `.exists()` guards fail and they never spawn: the TRUE floor is ~2 (the unconditional `git rev-parse` calls). Consequence: FR-8a is NOT primarily an overhead problem. Stop does fire every response turn -- NOT once-per-session as FR-8's original "keep" rationale assumed -- but the per-turn cost is small; the real defect is correctness, tracked as FR-21. `hooks/stop_notifier/` has zero test coverage -- characterisation tests are a blocking prerequisite for any reduction work. | Measured; work not started |
| **FR-9a** (existing, carried forward) | Fix the call-graph builder's `MAX_FILES=300` blindness before FR-10 depends on it | **SITE CORRECTED 2026-08-01 (Phase 5 probe) -- `parsers/config.py:11` IS DEAD CODE, read by nothing; its only importer (`parsers/__init__.py:22`) re-exports it, and its docstring's claim to be "a single source of truth" is false. Changing it fixes nothing while producing a diff that looks exactly like this requirement. THE BINDING CAP IS `parsers/call_graph_builder_legacy.py:64`, enforced at `:107` and `:118`. A SECOND binding cap survives fixing the first: `parsers/graph_model.py:43` (`MAX_PATHS = 500`), which truncates every sequence and interaction path regardless of file count -- this requirement is only satisfied when BOTH are addressed. 17 truncation sites exist in total; only these 2 bind. See `docs/phase-5-uml/callgraph_coverage_probe.md`.** The cap limits analysis to 300 of 411 `.py` files. The entire Level-2 SDLC core (45/45 files) and 38/45 hook files are 100% invisible to the builder FR-10's selector would consume for "call-graph risk signals." This is a PREREQUISITE, not a parallel task -- selection built on these inputs is provably worthless for the code that matters most. Interim source until fixed: `docs/phase-0-reverse-engineering/ast_call_graph.json` (2,218 nodes, Phase 0.1 snapshot). | Root-caused; fix not started |
| **FR-9b (new, Phase 5 -- ruled IN v2.0.0 SCOPE by the project owner)** | Fix the call-graph resolver's ambiguous-name fallback, which silently binds builtin and stdlib method calls to same-named project classes and thereby poisons the risk signal injected into the Step 1 planning prompt | **Numbering, stated so it is not mistaken for an arbitrary choice:** this is FR-9b, not FR-25. FR-25 is already claimed by a proposed CI check in `docs/phase-2-validation/advisory_items.json`, and reusing it would create exactly the ID collision this document's own FR-9 naming-collision warning exists to prevent. FR-9b is also semantically correct: FR-9a covers call-graph **discovery** blindness (which files are seen); FR-9b covers call-graph **resolution** incorrectness (what an edge points at once a file is seen). Same engine, same subsystem, same fix window. **The defect (VERIFIED against source by this pass):** `langgraph_engine/parsers/graph_model.py:265` returns `candidates[0]` when a bare simple method name matches multiple known method FQNs and none is in the caller's file -- an arbitrary first-match bind with no disambiguation and no confidence marker. Lines 253-254 and 263-264 (the `len(candidates) == 1` cases) are legitimate; line 265 is the defect. The dotted path at 243-255 correctly returns the target unresolved when ambiguous, so the defect is specific to bare names. **Measured consequences (MEASURED at runtime by two independent agents that hit this separately; NOT re-derived by this pass):** `list.append()` binds to `JsonlAppender.append` (`src/mcp/base/persistence.py:222`) at in-degree 1592; `str.format()` binds to `ErrorMessages.format` (`langgraph_engine/error_messages.py:568`) at in-degree **755-756** -- the two agents measured 755 and 756 respectively, and the one-edge discrepancy is reported as a range rather than resolved to a single figure this pass cannot adjudicate; `dict.get()`/`dict.set()` bind to `_MemoryLayer.get`/`_MemoryLayer.set` (`langgraph_engine/cache_system.py:101` and `:113`). **55.5 percent of cross-file "resolved" call edges are name-collision artifacts.** Of 26,114 total edges: 18,608 unresolved + 2,853 dropped for builtin-name collision + 433 dropped for cross-file ambiguity = 21,894, leaving **4,220 high-confidence**. That enumeration reconciles to the stated total exactly (26,114 - 21,894 = 4,220) and was arithmetically checked by this pass; the underlying measurements were not re-run. **Why this is v2.0.0 scope and not cosmetic -- VERIFIED against source by this pass:** `langgraph_engine/sdlc_pipeline/call_graph_analyzer.py:56-67` (`_classify_risk`) classifies risk PURELY by caller count (low 0-2, medium 3-7, high 8+), with no other input. `danger_zones` (built at `:303`, gate `n >= 5`) and `hot_nodes` (built at `:1197`, gate `n >= 5`) are likewise caller-count-only. **Precision correction to the finding as relayed:** `_classify_risk`'s 8+ threshold sets the per-method `risk` label (`:292`) and the overall risk verdict; the `danger_zones`/`hot_nodes` membership gate is a separate `n >= 5`. Both are caller-count-only, which is the load-bearing point, but they are not the same threshold. The counts come from an impact map built over `graph.get_edges()` (`:155`, `:455`, `:600`, `:1209`), and `get_edges()` (`graph_model.py:282-286`) returns `_resolved_edges` when populated -- which `call_graph_builder_legacy.py:96` does populate on every build. The collided edges therefore reach the analyzer. From there `prompt_gen_expert_caller.py:179-182` reads `risk_level`, `danger_zones`, `affected_methods` and `hot_nodes` and substitutes them into the Step 1 orchestration template at `:204-207`. **Consequence: `JsonlAppender.append` currently ranks as the codebase's top danger zone on the strength of every `list.append()` call in the repo, and the planning prompt has been receiving noise as risk signal.** **FR-9a alone is INSUFFICIENT, stated explicitly:** fixing discovery without fixing resolution produces a LARGER graph that is still misleading -- more files feeding the same broken resolver, and a higher collided in-degree on the same wrong nodes. FR-9b does not supersede FR-9a and FR-9a does not subsume FR-9b; both must land, and FR-9b should not be scheduled after FR-9a on the assumption that a bigger graph is a better one. **Consumer trap, flagged separately and explicitly NOT part of this defect:** `resolve_edges()` (`graph_model.py:194-223`) writes its output to `self._resolved_edges` (`:222`) and never back to `graph.edges`, so any consumer reading `graph.edges` directly gets raw unresolved edges. That divergence does **not** affect shipping code -- the analyzer uses `get_edges()`, which reads `_resolved_edges` -- and it is named here only so a future consumer does not reach for `.edges` and get a silently different graph. Do not conflate the two. | Root-caused and source-verified; fix NOT started |
| **FR-14a** (existing, carried forward) | Empirical plugin-schema spike, blocking before packaging design freezes | **(Phase 2.1: RESOLVED, item 5)** Originally four items UNDOCUMENTED in Claude Code's own docs. `hld.md` ADR-018 added a fifth: whether plugin-registered `.mcp.json` stdio servers spawn eagerly at session start or lazily on first tool use (gates NFR-1, the project's primary success metric). All 5 are now MEASURED in `plugin_schema_spike.md`: (1) `${CLAUDE_PLUGIN_ROOT}` resolves in `.mcp.json` -- YES; (2) `CLAUDE_PLUGIN_ROOT` present in spawned `os.environ` -- YES (de-risks but no longer gates ADR-009a branch 2, since ADR-012 made manifest-anchored ascent primary); (3) `/plugin install` writes exactly `extraKnownMarketplaces` + `enabledPlugins` -- MEASURED; (4) `/plugin uninstall` leaves `{}`-emptied `settings.json` keys and an orphaned, `prune`-immune cache directory -- MEASURED, and this makes FR-18's original AC unachievable (see revised FR-18 row); (5) MCP servers spawn EAGERLY on enable with zero tool calls -- MEASURED, and this fails NFR-1 for any design that bundles all 13 servers as always-on plugin entries (see revised NFR-1 row and `hld.md` ADR-018's minimal-bundle mitigation). | **Spike COMPLETE -- all 5 items MEASURED, none PROVISIONAL** |
| **FR-19 (new)** | Implement the ADR-009a four-branch `get_policies_dir()` resolution order in `path_resolver.py` | ADR-009 (canonical = `docs/policies/`) and ADR-007 (pinned plugin snapshot) collide the moment the plugin runs outside this workspace: a naive resolver either finds nothing or silently reads a stale `~/.claude/policies/` copy. `orchestration_prompt.md` already specifies the four branches (dev-mode live checkout / plugin snapshot / repo checkout / loud hard-error, never a silent `~/.claude/policies/` fallback) but no code implements it yet, and per ADR-009b (Section 9) this FR is **gated**: it may not begin until the five-policy merge decision is signed off, because canonicalising the resolver before merging would make the 5-6 unique `~/.claude/policies/`-only files unreachable by any branch. | Specified; blocked on Section 9 sign-off |
| **FR-20 (new)** | Decided post-plugin disposition for all 14 genuine policy orphans (Appendix E Section 4.2), independent of any SRS FR anchor | FR-2's audit matrix is scoped to the 46 policies, and 32 of them map cleanly to an SRS FR/NFR. The 14 genuine orphans (`anti-hallucination-enforcement.md`, `architecture-script-mapping-policy.md`, two point-in-time changelog files, `cross-project-patterns-policy.md`, `file-management-policy.md`, `git-auto-commit-policy.md`, `intelligent-decision-engine-policy.md`, `parallel-execution-policy.md`, `proactive-consultation-policy.md`, `session-chaining-policy.md`, `session-pruning-policy.md`, `test-case-policy.md`, `user-preferences-policy.md`) have no FR to hang a disposition off in FR-2's row-per-policy scheme without a supplementary rule. FR-20 makes explicit that "no SRS FR maps to it" is not a reason to skip a disposition -- 6 of the 14 are independently CONTRADICTED or broken regardless of SRS coverage and need a decision on their own evidence, not a pass because AC-1 technically only requires "an evidenced status," which all 14 already have, and "a decided post-plugin disposition," which none of the 14 yet have. | Gap named; not started |
| **FR-21 (new)** | Fix or formally retire the Stop hook's 7 dead script references (of 9 total) | This is a CORRECTNESS defect, separable from FR-8a's overhead-reduction scope. `hooks/stop-notifier.py` references 9 scripts; 7 (`archive-old-sessions.py`, `auto-save-session.py`, `common-failures-prevention.py`, `git-auto-commit-policy.py`, `plan-session-archiver.py`, `preference-auto-tracker.py`, `session-pruner.py`) do not exist on disk -- only `sync-version.py` and `voice-notifier.py` exist. Each missing-script `.exists()` guard fails silently, every turn, with zero log trace. FR-8a as scoped is a "measure and reduce overhead" task; it will correctly measure the REAL 2-spawn floor (the two scripts that exist) and could plausibly report "already optimal," which would be true for overhead and false for correctness -- 7 of 9 advertised behaviours (auto-save, archiving, common-failure prevention, git auto-commit, plan-session archiving, preference tracking) have never executed. FR-21 requires each of the 7 to be explicitly fixed (script created) or retired (reference deleted, capability's loss recorded in the FR-3/NFR-4 disposition ledger) -- "silently broken" is not an acceptable end state for either choice. | Root-caused; not started |
| **FR-22 (new, targets SRS.md not this document)** | Append a superseding entry to SRS.md that retires FR-9's (SRS numbering) four-hook-event guarantee | Required by `rules/44` (SRS is append-only) and identified as an unowned gap by `orchestration_prompt.md` FR-4a Consequence 1: v2.0.0's own deliverable list (Section 9 of the requirement doc) does not include this edit. Without it, `SRS.md:206`'s acceptance criterion becomes permanently false the moment PreToolUse/PostToolUse are deleted, with no compensating record of why. Owner must be assigned in Phase 1 (`as_built_executive_summary.md`'s third open decision names this exact gap and asks "who owns the SRS.md FR-9 rewrite"). | Owner unassigned |
| **FR-23 (new, refines FR-3's disposition for one named policy)** | Mandatory `port-to-MCP` disposition for the version-push gate before PreToolUse is deleted | `hooks/pre_tool_enforcer/policies/push_gate.py` (covered by `tests/test_push_gate.py`) is singled out in `orchestration_prompt.md` FR-4a Consequence 2 as a MANDATORY port-to-MCP candidate, not a generic "decide one of four options" item like the rest of FR-3's scope -- commit `1bb4303` was recent, deliberate governance work closing a version-push bypass, and letting FR-4's blanket PreToolUse deletion re-open it silently would undo that work without anyone deciding to. Called out separately so it cannot be lost inside a 46-row audit table. | Disposition mandated; port not started |
| **FR-24 (new, Phase 2.1 -- judged necessary, not merely narrowed away)** | A documented, user-run manual cleanup runbook for post-uninstall residue that FR-18 explicitly cannot own | `plugin_schema_spike.md` Item 4 (MEASURED) found `claude plugin uninstall` leaves inert `{}`-emptied `settings.json` keys and an orphaned, `.orphaned_at`-marked cache directory that `claude plugin prune` does not reclaim. Per `hld.md` ADR-012's own finding (no install-time execution point exists for a plugin), the symmetric fact holds at uninstall time too -- `/plugin uninstall` is not documented to execute plugin code, so **no plugin-shipped command can run automatically during uninstall to clean this up**. Silently accepting the residue with no user-facing record would leave FR-18 narrowed with no compensating documentation, the same defect pattern FR-22 was created to avoid for the SRS FR-9 gap. This is deliberately NOT proposed as an executable plugin command (there is no execution point for one to run automatically); it is a documentation deliverable the user can act on manually, e.g. before requesting uninstall support from Claude Code itself, or to periodically reclaim `~/.claude/plugins/cache/` disk space by hand. | Named at Phase 2.1; not started |

---

## 5. Measurable Acceptance Criteria (Partial / Contradicted FRs and NFRs)

One per item. Each replaces a vague "it's removed" / "it's done" formulation with something a script
or a reviewer can check without interpretation.

| Requirement | Measurable AC |
|---|---|
| FR-1 (Partial) | `docs/reports/policy-implementation-audit-v2.md` exists and contains exactly 46 policy rows, each with a non-empty Evidence cell citing a `file:line` or an explicit `NONE`; the file's own header states the read pass covered `~/.claude/policies/` line-by-line (not just `policy_corpus_inventory.json`'s metadata scan). |
| FR-2 (Partial) | The audit matrix has 7 non-empty columns for all 46 rows, including "Post-plugin plan" populated from the fixed vocabulary (`keep-as-is`/`port-to-plugin`/`port-to-MCP`/`demote-to-advisory`/`delete`) -- a row with an empty Post-plugin plan cell fails this AC. |
| FR-3 (Partial) | Every policy whose sole enforcement mechanism is a `PreToolUse` block (15 policies per Section 6.3 of `as-built-prd.md`: the 4 that self-declare hook-coupling plus the 11 that do not) has a recorded disposition with a one-sentence rationale in the audit matrix; `push_gate.py`'s row specifically reads `port-to-MCP` (FR-23) and no other value passes review. |
| FR-6 (content exists, file does not) | `docs/architecture/ADR-006-hook-free-execution.md` exists on disk, its "Consequence" section is present and unedited from the pre-committed text (enforcement becomes opt-in), and `git log` shows the file was added, not generated from a template with the consequence section blank. |
| FR-8/FR-8a | A committed instrumentation script reports, for 20 consecutive real Stop-hook invocations on this repo's current checkout: (a) exact subprocess count per invocation, (b) wall-clock duration per invocation, (c) which of the 9 referenced scripts actually ran vs hit a failed `.exists()` guard. The reduced design's regression test asserts the per-turn spawn count is <= 2 (the two scripts confirmed to exist) unless a named exception is documented with a rationale. |
| FR-9 (v2.0.0: library drift) | `knowledge-graph/_master/master_graph.md`'s header-reported agent/skill/domain counts equal `README.md`'s counts, equal the filesystem's directory counts (post-dedup), and `validate.py` plus `test_invariant_checker.py` both exit 0 -- all three numbers must match, not just two. |
| FR-9a (Root-caused; fix not started -- **AC added at Phase 2.1, escalated from ADVISORY to required by the coordinator**) | **Prior gap:** this row did not exist; FR-9a's only definition of done was the RTM's "(prerequisite for FR-10's AC)", which makes FR-9a's completion parasitic on FR-10's tests rather than independently checkable -- an implementer could fix the one site Phase 0 named, watch FR-10 go green, and leave three more truncation points intact. `hld.md` SS 12 OAQ 4 found FR-9a's true scope is **four** independent silent truncators, not one: (1) `langgraph_engine/parsers/config.py:11` (`MAX_FILES = 300`, consumed via `parsers/__init__.py:22` -- the one Phase 0 named); (2) `langgraph_engine/parsers/call_graph_builder_legacy.py:64` (`MAX_FILES = 300`, used at `:76`); (3) `langgraph_engine/sdlc_pipeline/architecture/00-code-graph-analysis/code_graph_analyzer.py:73` (`MAX_FILES = 500`, used at `:137`/`:154`/`:169` -- lives inside `sdlc_pipeline/`, the very package site 1 drops entirely); (4) `scripts/architecture/03-execution-system/00-code-graph-analysis/code-graph-analyzer.py:68` (`MAX_FILES = 500`, used at `:120`/`:137`/`:152` -- a near-duplicate of site 3 under a hyphenated filename). **Measurable AC:** each of the four sites above reaches exactly one of two recorded end states -- migrated to the ADR-013 coverage-complete contract (ENUMERATE -> ALLOCATE -> RECONCILE -> PROPAGATE, non-optional `DiscoveryManifest` constructor argument, default budget unbounded) or formally retired with the removal recorded (valid for sites 2 and 4 if no live caller remains); "fixed the one Phase 0 named" is explicitly NOT an acceptable end state. The ADR-013 regression test `test_discovery_covers_every_package` must pass, and its assertion 5 (the named canary) must confirm `manifest.packages["langgraph_engine/sdlc_pipeline"].analysed_n == 45` -- i.e. the package site 1 alone would silently drop is present in builder output at full count. **Explicitly out of scope, by decision not oversight:** a fifth truncator exists at `langgraph_engine/build_dependency_resolver/parsers.py:682` (`max_files_scanned = 1000`, used at `:696`) which returns a truncated `False` from a directory-detection helper rather than a truncated graph. `hld.md` OAQ 4 rules it a different defect class (a boolean, not a graph, and therefore not inspectable the way sites 1-4 are) and defers it to a v2.1 follow-on under ADR-013's general principle; it is not part of FR-9a's four-site closure requirement and its absence from the list above is deliberate. |
| FR-9b (new, Phase 5 -- ruled in scope by the project owner) | Three assertions, all mechanically checkable. **(1) No builtin/stdlib-name collision survives into the risk signal.** A committed check enumerates every method FQN appearing in `danger_zones` or `hot_nodes` for a full-repo analysis run and fails if any entry's simple name collides with a Python builtin or a stdlib method name (`append`, `format`, `get`, `set`, `read`, `write`, `close`, `keys`, `items`, `values`, `update`, `pop`, `sort`, `join`, `split`, `strip`, `add`, `remove`, `count`, `index` at minimum, sourced from `builtins` plus the collection/str/dict/list method sets rather than hand-maintained) **on the strength of collided edges**. An entry whose fan-in survives after collided edges are excluded is legitimate and passes; the check is on the collision, not on the name. **(2) Confidence is reported, never silently collapsed.** Wherever fan-in is consumed -- `_classify_risk`'s input, `danger_zones`' `callers_count`, `hot_nodes`' `callers_count`, and the four `graph.get_edges()` consumers at `call_graph_analyzer.py:155`, `:455`, `:600`, `:1209` -- the high-confidence edge count is reported alongside the raw count, as two distinct fields. A consumer that reads only one number fails review. **(3) The arbitrary bind is gone at the source.** `graph_model.py:265` no longer returns `candidates[0]` for an ambiguous bare name; it returns either the unresolved target or a resolution explicitly marked ambiguous, and a unit test asserts that a bare name matching 2 or more FQNs with no same-file candidate does NOT produce a confident edge. **Regression baseline:** the check runs against the measured figures above, so a re-run reports the collision rate; the AC does not assert 55.5 percent must become any specific number, because no post-fix figure has been measured and pre-committing one would be a fabricated target. It asserts the collision rate is REPORTED and that assertions (1) and (3) hold. |
| FR-10 (Contradicted) | A grep for agent-name or skill-name string literals across the selection code path returns zero matches outside test fixtures; every one of 10 sample task descriptions run through the selector returns a ranked agent set where each entry carries a non-empty KG edge-path array (never `[]`), verified against `docs/phase-0-reverse-engineering/ast_call_graph.json` or a rebuilt (FR-9a-fixed) call graph, never the current truncated builder. |
| FR-14 (research done, build not started) | `.claude-plugin/plugin.json` exists, `jsonschema`-validates against the confirmed CONFIRMED-list contract in `orchestration_prompt.md` Section 1.4 (required `name`+`description`, explicit semver `version`), and a `find` over the plugin tree for `hooks/` or `*hooks.json` returns zero results (ADR-010 conformance, enforced as a CI gate per the architecture-conformance-auditor CRITICAL check already specified). **Amended at Phase 2.1 for ADR-019's two-step consequence, decided explicitly rather than left as a silent miss (see the FR-14 note in Section 2 for the reasoning):** "installable in one step" is satisfied for commands, agents, and skills only -- `/plugin install` alone, no hand-edited `settings.json`, matching AC-6's "no manual surgery" bar in full. It is NOT satisfied for MCP-backed capabilities: the FR-23 push gate and the progress writer additionally require the user to run the explicit `register-mcp` command (ADR-019) as a second step. The AC therefore splits: (a) a fresh install with no `register-mcp` run confirms commands/agents/skills are functional and confirms the FR-23 push gate is NOT YET reachable (expected, not a defect); (b) after `register-mcp` runs, the push gate and progress writer become reachable, per NFR-5's fourth test assertion (Section 5, NFR-5 row). |
| FR-15 (Partial, DISPUTED count -- AC replaced, NOT sized) | **(Phase 2.1: superseding this document's own prior AC, per `hld.md` SS 12 OAQ 6's explicit delegation to business-analyst-agent)** The prior wording below is WITHDRAWN because it asserted "13" as fact inside a gate-passed acceptance criterion while a second, differently-derived measurement (`~95 live-code / 23 comment` via an independent line-oriented grep) remains unreconciled against the AST-based 13/103 split (`path_violations.md`). `hld.md` states plainly: "Both cannot stand." FR-15 is NOT sized on either figure, in this document or in `product-sequencing-v2.md`, until the AST re-derivation runs. **Replacement AC:** an AST-based classifier partitions every `~/.claude/...` occurrence in `langgraph_engine/`, `hooks/`, `scripts/`, `src/` into CODE, DOCSTRING, or COMMENT by enclosing node type (a string in `ast.arguments.defaults`, an `ast.Call` keyword, or an assignment RHS => CODE; the first statement of a module/class/function body => DOCSTRING; a `tokenize.COMMENT` token => COMMENT), emitting one record per occurrence as `file:line:node_type:classification`. After remediation, the count of occurrences classified CODE is zero, **excluding `src/utils/path_resolver.py` itself**, which is the canonical source of these strings and is not a violation (a defect present in the withdrawn AC below, which did not state this exclusion). A separate check confirms 0 absolute path literals remain. The classifier's output is committed as the evidence artifact; the total occurrence count and the CODE/DOCSTRING/COMMENT split are reported as MEASURED values, never asserted against a pre-committed number. **Rescoping consequence:** FR-15's WSJF row (currently paired with FR-17 at 4.67, size 3, in `product-sequencing-v2.md`) is derived from the withdrawn 13-figure and must be recomputed once the classifier's measured CODE count exists; FR-17's 19-site count is independently confirmed and stable, so the pairing should split rather than re-estimate as a unit. ~~A grep for the 13 named `~/.claude/...` code-level string defaults (not the 103 comment/docstring occurrences) across `langgraph_engine/`, `hooks/`, `scripts/`, `src/` returns zero matches after remediation; a separate check confirms 0 absolute path literals remain (regression against the existing positive finding, not just a one-time pass).~~ *(withdrawn wording, struck through and retained for audit trail, not deleted)* |
| FR-17 (Partial, count corrected) | A grep for mode-less `open(` and explicit-text-mode `open(..., "r"` / `"w"` / `"a"` calls lacking `encoding=` returns zero matches across the 19 confirmed sites (not the earlier undercount of 12); binary-mode and `tarfile`/`urllib` calls remain excluded by the same grep's exemption list. |
| FR-18 (Not started -- **AC added at Phase 2.1; Section 6's RTM row previously pointed to a Section 5 row that did not exist -- this is that missing row, and its own gap**) | **Narrowed per `plugin_schema_spike.md` Item 4 (MEASURED) -- the original "no orphaned files, MCP registrations, or settings entries" bar is unachievable by any plugin design, stated plainly, not silently narrowed.** Replacement AC, scoped to PLUGIN-ATTRIBUTABLE residue only: (a) after `claude plugin uninstall`, no MCP tool the plugin registered remains callable in a fresh session (functional residue = 0, even though the `enabledPlugins`/`extraKnownMarketplaces` bookkeeping keys are emptied to `{}` rather than removed -- that emptying is Claude-Code-owned behavior outside FR-18's control and is explicitly out of scope for this AC); (b) the uninstall test asserts the settings.json delta attributable to the plugin, never whole-file equality against a pre-install snapshot (consistent with `hld.md` SS 8.4's stated principle for the 17 pre-existing `settings.json` writers); (c) the orphaned plugin cache directory under `~/.claude/plugins/cache/` and its `.orphaned_at` marker are DOCUMENTED as a known, accepted Claude-Code-level limitation in the uninstall runbook (FR-24, below) rather than asserted to be zero, since `claude plugin prune` does not reclaim it and the plugin has no uninstall-time execution point to clean it itself. |
| FR-19 (new) | `path_resolver.py`'s `get_policies_dir()` has exactly 4 branches in source order matching ADR-009a, a unit test exists per branch (4 tests minimum), and the 4th (hard-error) branch's test asserts the raised exception's message names all 3 attempted paths and never silently returns `~/.claude/policies/`. |
| FR-20 (new) | All 14 orphan-policy rows in the audit matrix (Section 4) have a non-empty Post-plugin plan value; a script comparing the 46-row matrix against `as-built-prd.md` Section 4.2's 14-name list confirms zero name mismatches and zero empty dispositions among them. |
| FR-21 (new) | For each of the 7 missing Stop-hook scripts, exactly one of two states holds and is recorded: (a) the script file exists on disk and its corresponding `.exists()` guard now evaluates true in a test run, or (b) the reference to it is removed from `hooks/stop_notifier/core.py` and the lost capability appears with a disposition in the FR-3/NFR-4 ledger. A grep for the 7 filenames inside `hooks/stop_notifier/` after remediation returns either a real file or zero references -- never a dangling reference to an absent file. |
| FR-22 (new) | `SRS.md` contains a new FR entry (numbered per the next available FR-N, appended, not replacing FR-9's text) whose acceptance criterion explicitly states the v2.0.0 replacement guarantee for the two removed hook events, and `SRS.md`'s Change Log table (Section 6) has a new row dated to the PR that deletes PreToolUse/PostToolUse, referencing this FR by number. |
| FR-23 (new) | `push_gate.py`'s logic is reachable as an MCP tool callable by name, `tests/test_push_gate.py`'s existing assertions (or their direct equivalents) pass against the MCP-tool code path, and this happens BEFORE (verified by commit ordering) the PR that deletes `hooks/pre_tool_enforcer/`. |
| FR-24 (new, Phase 2.1) | A committed uninstall runbook document exists (e.g. `docs/guides/uninstall-residue.md`) naming, by exact path, every item `plugin_schema_spike.md` Item 4 measured as surviving uninstall (the two `{}`-emptied `settings.json` keys, the `~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/` directory and its `.orphaned_at` marker) with manual removal steps for each; the NFR-5 uninstall test asserts the runbook file exists and its named paths match the plugin's actual marketplace/plugin name strings (no stale placeholder text). |
| NFR-1 (Contradicted) | **(Phase 2.1 REVISED per ADR-018; bundle constraint SUPERSEDED by ADR-019 -- see Section 3's NFR-1 note for the full reasoning)** With the plugin installed but not invoked, an OS-level process count is taken immediately before and after 10 tool calls in a fresh session, attributed PER COMPONENT. Pass = 0 processes attributable to **the plugin** (its command entry points; it has no bundled MCP servers to count). The retained user-level `Stop` and `Notification` hooks are explicitly excluded from this count (ADR-010 -- the plugin never owned them). The measurement window must not span a response-turn boundary, since the retained Stop hook fires every turn and would otherwise register a false-positive delta. Cold and warm counts are reported as two separate numbers, never blended. **The plugin bundles ZERO MCP servers (ADR-019)** -- a `.mcp.json` at the plugin root containing any server entry fails this AC outright, regardless of the process-count result, because `plugin_schema_spike.md` Item 5 confirmed eager spawn on enable for any bundled server, however minimal. All MCP registration, including the FR-23 push gate and the progress writer, is deferred to the explicit opt-in `register-mcp` command (ADR-019), invoked as a separate step after install. |
| NFR-2 (Contradicted) | **(Phase 2.1 REVISED per ADR-016)** Static scan for `timeout=`, `signal.alarm`, or a subprocess `timeout` keyword argument returns zero unconditional fixed timeouts on the long-running pipeline path, scanned across BOTH the plugin's bundled code (commands, MCP tool handlers) AND the engine pipeline path under `langgraph_engine/sdlc_pipeline/architecture/` and `langgraph_engine/sdlc_pipeline/nodes/` -- specifically the 6 named application sites and 3 named definition sites in the reconciled NFR-2 row above. Any timeout present must be configurable and default to unbounded or user-overridable, with exactly one documented exception: a single-call socket/HTTP-level I/O timeout that raises a retryable error into a circuit breaker rather than aborting the enclosing pipeline task. The regression test asserts all 5 ADR-016 mechanisms are present: attempt-count/iteration bound, lease renewal, a convergence (no-progress) signal, a circuit breaker per external dependency with non-fixed reopen-wait, and full-jitter retry. |
| NFR-3 (Not designed) | **(Phase 2.1 REVISED per ADR-011 / OAQ 1 -- reclassify from "Not designed" to "Verify + repair 3 defects")** The replacement writer is NOT a new component: `langgraph_engine/checkpoint_manager.py::CheckpointManager`, triggered by `core/step_decorator.py` at every step boundary. The "resume from any step after crash" test (already implied by SRS NFR-3) kills the process mid-pipeline and confirms `orchestrator.py::resume_flow` -> `quality/recovery_handler.py::resume_from_checkpoint` picks up at the correct step using this existing writer -- no new writer is designed or built. Passing this AC additionally requires the three ADR-011 durability defects fixed: (1) `step_decorator.py:169` no longer swallows a checkpoint-save failure silently -- it raises or sets a `checkpoint_degraded` flag the resume path refuses to trust; (2) the per-tool-call progress replacement (`mcp-post-tool-tracker`) is implemented as a projection of the checkpoint record, not an independent writer, so no dual-write path exists; (3) a replay-idempotency test confirms re-executing a side-effecting step (e.g. GitHub issue creation) twice with the same session-id+step-number key produces no duplicate external effect. |
| NFR-4 (Precondition only) | All 25 capabilities named in `capability_loss.md` have a non-"disappeared" disposition value in the audit matrix; a script cross-checks the 25 names against the matrix and fails if any is missing or has an empty disposition cell. |
| NFR-5 (Not started -- **UNBLOCKED as of Phase 2.1**) | `docs/phase-1-architecture/plugin_schema_spike.md` exists with all **5** FR-14a items (grew from 4 per `hld.md` ADR-018) resolved to CONFIRMED -- **satisfied: all 5 are MEASURED, none PROVISIONAL, as of this reconciliation pass.** The blocking gate on writing the 3 lifecycle tests is therefore cleared. Three automated tests must exist and pass: install (see Gherkin Section 8, plus a settings.json diff assertion matching Item 3's measured keys), invoke, and uninstall (assert only plugin-attributable delta per the revised FR-18 AC below -- NOT whole-directory/whole-file equality, since Item 4 confirmed Claude-Code-owned residue is unavoidable). **The install test must assert the plugin ships NO `.mcp.json` at all (ADR-019, superseding the earlier ADR-018 minimum-viable-set mitigation -- Item 5 confirmed eager spawn on enable for any bundled server, however minimal).** A fourth, new assertion is required: the "invoke" test must exercise TWO steps, not one -- `/plugin install` followed by the explicit `register-mcp` command -- and confirm the FR-23 push gate and progress writer are unreachable after step one alone and reachable only after step two (ADR-019's two-step consequence, see the revised FR-14 row above). |

---

## 6. Requirements Traceability Matrix (RTM)

FR/NFR -> Acceptance Criterion -> Owning Workstream -> Target Artifact. Broad ACs (AC-1..AC-7) come
from the original v2.0.0 doc Section 12; per-FR ACs (Section 5 above) are the measurable refinements.

| FR/NFR | AC(s) | Workstream | Target artifact |
|---|---|---|---|
| FR-1 | AC-1 + Section 5 row | A | `docs/reports/policy-implementation-audit-v2.md` |
| FR-2 | AC-1 + Section 5 row | A | `docs/reports/policy-implementation-audit-v2.md` |
| FR-3 | AC-1 + Section 5 row | A | `docs/reports/policy-implementation-audit-v2.md` |
| FR-4 | AC-2 | B | `~/.claude/settings.json` (PreToolUse/PostToolUse entries removed) |
| FR-4a | (informs FR-4/FR-3/FR-22 ACs) | B | `docs/phase-0-reverse-engineering/impact_analysis_graph.json` (already produced) |
| FR-5 | AC-3 | B | `~/.claude/settings.json` (UserPromptSubmit off hot path) + new slash command(s) |
| FR-6 | Section 5 row | B | `docs/architecture/ADR-006-hook-free-execution.md` |
| FR-7 | AC-3 | B | `commands/` (plugin slash commands) |
| FR-8 / FR-8a | Section 5 row | B | `hooks/stop_notifier/` (reduced) + new characterisation test suite |
| FR-9 (v2.0.0 drift) | AC-5 + Section 5 row | C | `claude-global-library/knowledge-graph/_master/master_graph.md` |
| FR-9a | Section 5 row (Phase 2.1: own dedicated AC added -- previously only "prerequisite for FR-10's AC", a defect this pass fixed) | C | Four sites: `langgraph_engine/parsers/config.py`, `langgraph_engine/parsers/call_graph_builder_legacy.py`, `langgraph_engine/sdlc_pipeline/architecture/00-code-graph-analysis/code_graph_analyzer.py`, `scripts/architecture/03-execution-system/00-code-graph-analysis/code-graph-analyzer.py` (each migrated or formally retired) + `test_discovery_covers_every_package` regression test |
| FR-9b | Section 5 row (Phase 5) | C (same workstream and fix window as FR-9a; NOT a substitute for it -- both must land) | `langgraph_engine/parsers/graph_model.py:265` (the ambiguous bare-name bind) + a confidence field on every `graph.get_edges()` consumer in `langgraph_engine/sdlc_pipeline/call_graph_analyzer.py` + the collision regression check (new) |
| FR-10 | AC-4 + Section 5 row | C | KG-driven selector module (new) |
| FR-11 | AC-4 | C | Selector output schema / logs |
| FR-12 | AC-4 | C | Selector fallback path |
| FR-13 | (no dedicated AC; existing rule) | C | `~/.claude/rules/model-fallback.md` (global-only -- no repo-relative copy exists) conformance in selector |
| FR-14 | AC-6 + Section 5 row | D | `.claude-plugin/plugin.json` |
| FR-14a | (blocking spike, gates FR-14/15/18) | D | `docs/phase-1-architecture/plugin_schema_spike.md` |
| FR-15 | AC-6 + Section 5 row (Phase 2.1: AC replaced with an AST-classifier method; NOT sized on 13 or 95) | D | AST-classifier evidence artifact (new) + `path_resolver.py` CODE-classified call sites (count TBD by classifier, not pre-asserted) |
| FR-16 | AC-6 | D | Build-time snapshot script (new) |
| FR-17 | AC-6 + Section 5 row | D | `open()` call sites (19 remediated) |
| FR-18 | AC-6 + Section 5 row | D | Uninstall test suite (new) |
| FR-19 | Section 5 row | A/D (crosses; gated by Section 9) | `path_resolver.py`'s `get_policies_dir()` |
| FR-20 | AC-1 + Section 5 row | A | `docs/reports/policy-implementation-audit-v2.md` (14 orphan rows) |
| FR-21 | NFR-4's AC + Section 5 row | B (Stop-hook scope) | `hooks/stop_notifier/core.py` |
| FR-22 | Section 5 row | (cross-cutting; not a v2.0.0 workstream) | `SRS.md` (new appended FR + Change Log row) |
| FR-23 | FR-3's AC + Section 5 row | A/B | MCP tool wrapping `push_gate.py` |
| FR-24 | Section 5 row | D | `docs/guides/uninstall-residue.md` (new) |
| NFR-1 | AC-2/AC-7 + Section 5 row | B | Process-count test harness (new) |
| NFR-2 | AC-7 + Section 5 row | B | Static timeout scan (new) |
| NFR-3 | Section 5 row | B | Replacement telemetry/checkpoint writer (new) |
| NFR-4 | Section 5 row | A | `capability_loss.md` cross-check script (new) |
| NFR-5 | AC-6 + Section 5 row | D | `docs/phase-1-architecture/plugin_schema_spike.md` + 3 lifecycle tests |
| SRS FR-9 conflict | FR-22's AC | (cross-cutting) | `SRS.md` |

**RTM gap count: 0 (revised at Phase 2.1; was silently 1 before this pass).** Every FR/NFR in the
reconciled Section 2/3 tables and every new FR in Section 4 has at least one AC and one target
artifact above. **Correction made at Phase 2.1:** this row previously pointed FR-18 at "AC-6 +
Section 5 row" while no FR-18 row actually existed in Section 5 -- a genuine RTM gap the original
gate passes did not catch. That row has been added (see FR-18 in Section 5) and FR-24's row is new
in both Section 4 and Section 5. The 6-item **Five-Policy Merge Decision** (Section
9) is intentionally NOT an FR -- it is a one-time content decision gating FR-19's start, tracked
there rather than duplicated into this table.

---

## 7. BDD Gherkin -- NFR-5 (Plugin Install / Invoke / Uninstall)

```gherkin
Feature: Plugin lifecycle correctness (NFR-5, AC-6)
  As the maintainer of claude-workflow-engine
  I want plugin install, invoke, and uninstall to each be independently testable
  So that FR-14..FR-18 can be verified rather than assumed

  Background:
    Given the plugin ships ZERO bundled hooks (ADR-010) -- no "hooks/" directory, no "hooks.json"
    And the plugin manifest is ".claude-plugin/plugin.json" with an explicit semver "version" field (ADR-008)
    And CLAUDE_PLUGIN_DEV_MODE is unset (production build, ADR-007)

  Scenario: Install leaves an uninvoked session with zero added overhead
    Given a clean Claude Code installation with no claude-workflow-engine plugin present
    And a snapshot of "settings.json" is taken before install
    When the user runs "/plugin marketplace add techdeveloper-org/claude-workflow-engine-plugin"
    And the user runs "/plugin install claude-workflow-engine@techdeveloper-org"
    Then the plugin install completes with a success exit status
    And a diff of "settings.json" before and after shows no "PreToolUse" entry added
    And the diff shows no "PostToolUse" entry added
    And the diff shows no "UserPromptSubmit" entry added
    And the diff shows the pre-existing user-level "Stop" and "Notification" entries unchanged (ADR-010 consequence)
    And the plugin ships NO ".mcp.json" at all -- ZERO bundled MCP servers (ADR-019, superseding
      the earlier ADR-018 minimum-viable-bundle mitigation; `plugin_schema_spike.md` Item 5 measured
      that even a two-server minimum-viable bundle spawns eagerly on enable, so no bundle size is
      small enough to satisfy NFR-1)
    And a fresh session with the plugin installed but not invoked spawns zero processes
      attributable to the PLUGIN specifically, asserted by a per-component OS process-list count
      taken before and after 10 tool calls, with the retained "Stop"/"Notification" hook spawns
      explicitly excluded from the count (NFR-1, AC-2, revised at Phase 2.1 -- this now holds
      unconditionally, since there is no bundled server left to spawn)
    And the FR-23 push gate and the progress writer are NOT yet reachable, because MCP registration
      is a separate, explicit step (the "register-mcp" command, ADR-019) the user has not yet run

  Scenario: Explicit invocation reaches every capability that used to run via UserPromptSubmit
    Given the plugin is installed per the previous scenario
    When the user invokes the bundled slash command for the full pipeline
      (the FR-7 "one command that runs Steps 0-8" entry point)
    Then Steps 0 through 8 execute in order
    And every one of the 25 capabilities listed in
      "docs/phase-0-reverse-engineering/capability_loss.md" shows a decided, non-"disappeared"
      disposition in "docs/reports/policy-implementation-audit-v2.md" (NFR-4, AC-3)
    And for every agent the selector picks during the run, the log emits agent name,
      source domain, matched skills, KG edge path, and confidence score (AC-4, FR-11)
    And zero agent or skill name appears as a string literal anywhere in the selection
      code path exercised by the run (AC-4, FR-10)

  Scenario: Uninstall removes all plugin-attributable functional residue (FR-18, narrowed at Phase 2.1)
    Given the plugin is installed and has been invoked at least once
    And a snapshot of "settings.json" and "~/.claude/plugins/cache/" is taken before uninstall
    When the user runs "/plugin uninstall claude-workflow-engine@techdeveloper-org"
    Then none of the plugin's bundled MCP tools are callable in a fresh session (functional removal)
    And the "enabledPlugins" and "extraKnownMarketplaces" keys in "settings.json" are emptied to "{}"
      -- this is Claude-Code-owned behaviour, MEASURED by `plugin_schema_spike.md` Item 4, and is
      explicitly accepted rather than asserted to be absent (the original "no entry remains" wording
      is WITHDRAWN as unachievable)
    And "~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/" survives with an ".orphaned_at"
      marker, is NOT reclaimed by "claude plugin prune", and is documented by name in
      "docs/guides/uninstall-residue.md" (FR-24) rather than asserted to be empty
    And the retained user-level "Stop" and "Notification" hooks are unchanged and still point at
      their pre-existing scripts (ADR-010 -- the plugin never owned them, so uninstall cannot
      touch them)
```

---

## 8. Five-Policy Merge Decision -- ADR-009b, User Sign-Off Required

**Why this blocks work:** ADR-009b (`docs/orchestration_prompt.md`, Section 5) found the premise
behind ADR-009 was wrong. ADR-009 assumed three DIVERGENT COPIES of one policy corpus; measurement
shows three PARTIALLY DISJOINT corpora. Six files exist ONLY in `~/.claude/policies/` with no
`docs/policies/` counterpart. One of the six (`github-branch-pr-policy.md`) is a verified
content-identical rename of `docs/policies/pr-code-review-policy.md` and needs no decision here. The
other five are genuinely unique content and are the subject of this section.

**BLOCKING constraint (already in force per ADR-009b):** no agent may delete, move, or overwrite any
file under `~/.claude/policies/` until this decision is signed off. FR-19 (`get_policies_dir()`
canonicalisation) may not start until then either.

For each policy: what it does, whether anything references it today, and a recommendation. The
recommendation is not a default -- the user decides each of the five independently.

### 8.1 `recommendations-policy.md` (v3.0.0, 427 lines)

- **What it does:** Task-aware recommendation engine -- suggests skills/agents, best practices,
  optimisations, and technology-specific guidance based on detected stack and complexity.
- **References found:** `docs/policies/pr-code-review-policy.md` line 6 lists it under
  **"Depends On"** -- a hard dependency, not a soft mention. `pr-code-review-policy.md` maps to
  v2.0.0-mapped SRS FR-2 (Step 5) and is itself `PARTIAL`/`ENFORCED`-adjacent, i.e. a real, live
  policy the canonicalisation would leave with a dangling cross-reference if this file is dropped.
- **Recommendation: PORT into `docs/policies/`.** This is the clearest of the five -- a mapped,
  real policy in the canonical corpus explicitly depends on it. Deleting it breaks a working
  reference; leaving it only in `~/.claude/policies/` leaves the canonical corpus incomplete by its
  own stated dependency.

### 8.2 `auto-skill-agent-selection-policy.md` (v3.0.0, 710 lines)

- **What it does:** Step-7 auto-selection of skills/agents from a task-type + complexity +
  model-selection context; its own header states it CONSOLIDATES `core-skills-mandate.md` and
  `adaptive-skill-registry.md`.
- **References found:** Three, all soft. `docs/policies/hook-system-policy.md` line 62 lists it in
  a PreToolUse check table ("Skill context hint... Inject per-file skill context") -- that whole
  table is PreToolUse-coupled behaviour being deleted under FR-4 regardless. `pr-code-review-policy.md`
  line 7 lists it under "Related To" (not "Depends On"). `parallel-execution-policy.md` line 1541
  lists it under "Related Policies" in a references appendix; that policy is itself one of the 14
  genuine orphans (DOCUMENTED-ONLY, no SRS FR).
- **Recommendation: DELETE, with the rationale recorded in the FR-2 audit matrix.** This file IS the
  hardcoded selection mechanism v2.0.0 FR-10 exists to replace ("any place that names an agent or
  skill as a string literal is a defect to be removed... selection must query the graph, never a
  hardcoded list"). Porting it forward would import the exact anti-pattern the new selector is being
  built to remove. All three referencing files use it as a soft "related" pointer, not a hard
  dependency -- `pr-code-review-policy.md`'s one line needs editing (drop the reference), not the
  policy itself needs preserving.

### 8.3 `core-skills-mandate.md` (602 lines, "ALWAYS ACTIVE")

- **What it does:** Model-tier selection quick-reference (search->Explore/haiku,
  implement->Sonnet, architecture->Plan/opus) plus an "efficient exploration strategy" section
  (prefer `tree`/`ls`/`Glob` over spawning an Explore agent for simple lookups).
- **References found:** `docs/policies/task-phase-enforcement-policy.md` line 374 cites
  `~/.claude/memory/core-skills-mandate.md` -- note the path says `memory/`, not `policies/`; this
  reference is already broken/inconsistent today, independent of any v2.0.0 decision.
  `docs/policies/session-memory-policy.md` line 457 lists it under "Works WITH" (descriptive, not a
  hard dependency); `session-memory-policy.md` is itself `CONTRADICTED` (confirmed no-op) per the
  as-built audit.
- **Recommendation: PARTIAL PORT, as advisory content, not as a policy file.** The model-tier
  guidance (which model for which task shape) is orthogonal to FR-10's agent/skill KG selection --
  FR-10 is about which agent/skill to pick, this file is about which Claude model to run it under --
  so it is not superseded by the new selector the way Section 8.2's file is. Recommend folding its
  model-tiering guidance into the plugin's agent-instruction layer (FR-3's "advisory, model-enforced"
  disposition) rather than keeping it as a standalone policy file with two already-inconsistent
  inbound references to clean up either way.

### 8.4 `adaptive-skill-registry.md` (109 lines)

- **What it does:** A tracking ledger for skills/agents auto-created by an
  `adaptive-skill-intelligence` system -- TEMPORARY vs PERMANENT lifecycle, a "protected, never
  delete" list frozen at 2026-01-23 (roughly 15 skills, 11 agents).
- **References found:** None inside `docs/policies/`. It appears only in
  `auto-skill-agent-selection-policy.md`'s own header as one of three things that policy claims to
  consolidate (Section 8.2) -- i.e. its only referencer is itself recommended for deletion.
- **Recommendation: DELETE.** No live dependent in the canonical corpus. Its content is a
  hand-maintained snapshot of a ~15/~11-item subset, already six months stale against the master
  KG's actual 505 agents / 992 skills, and the entire point of FR-9/FR-10 is that this repo stops
  hand-maintaining such lists in favour of querying the KG. Keeping a stale manual registry
  contradicts the requirement it would be ported alongside.

### 8.5 `auto-plan-mode-suggestion-policy.md` (1,045 lines -- the largest of the five)

- **What it does:** Step-2 logic that scores task complexity and auto-suggests or enforces
  "plan mode" before execution, keyed to a specific pipeline step sequence.
- **References found:** None inside `docs/policies/`.
- **Recommendation: DELETE.** Independent, corroborating evidence from two other artifacts already
  in scope: `CLAUDE.md`'s own version history states the plan-mode decision step was **removed from
  the pipeline in v1.13** ("Step 1: plan mode decision [REMOVED in v1.13]"), and
  `as-built-prd.md` AS-FR-011 independently found the same thing while investigating a different
  policy (`intelligent-model-selection-policy.md`, STALE-TOPOLOGY): "one of five stated inputs
  (plan-mode decision) was itself removed from the pipeline in v1.13." This is the largest file of
  the five and describes a mechanism the codebase has not executed in roughly eight minor versions.
  Porting it forward would resurrect governance over a pipeline step that no longer exists.

### 8.6 Summary for quick sign-off

| Policy | Recommendation | One-line reason |
|---|---|---|
| `recommendations-policy.md` | **PORT** | Hard dependency from a mapped, live policy (`pr-code-review-policy.md`). |
| `auto-skill-agent-selection-policy.md` | **DELETE** | IS the hardcoded-selection mechanism FR-10 exists to replace; only soft referencers. |
| `core-skills-mandate.md` | **PARTIAL PORT (advisory)** | Model-tiering guidance is orthogonal to FR-10; fold into agent instructions, don't keep as a policy file. |
| `adaptive-skill-registry.md` | **DELETE** | No live dependent; stale hand-maintained list the KG-driven approach obsoletes by design. |
| `auto-plan-mode-suggestion-policy.md` | **DELETE** | Governs a pipeline step removed in v1.13; corroborated by two independent sources; no referencers. |

*(`github-branch-pr-policy.md`, the sixth ADR-009b file, needs no decision here -- it is a verified
duplicate of `docs/policies/pr-code-review-policy.md` under a different name; recommend simply not
copying it, since the canonical content already exists.)*

---

## 9. Settled ADRs -- Consequences Flagged, None Reopened

Per the task's hard rule, ADR-006 through ADR-010 (including 009a, 009b) are treated as decided. The
following are consequences this pass surfaced that the user may not have had in view when each ADR
was accepted -- flagged for awareness, not for re-litigation.

- **ADR-006 (hook-free):** accepted consequence is "enforcement becomes opt-in." This pass adds that
  the SAME deletion also removes the sole writer of crash-recovery checkpoint state (NFR-3,
  Section 3) and reopens a deliberately-closed version-push bypass (FR-23) -- both are downstream of
  ADR-006 but were not enumerated in the ADR's own "Consequence" line. Recommend the ADR-006 document
  cross-reference FR-4a's three named consequences explicitly rather than leaving them only in the
  orchestration prompt.
- **ADR-007 (pinned snapshot):** no new consequence found; the dev-mode escape hatch's three guard
  rails (env-var-only, `mode: dev` tagging, publish-time hard fail) are sound as specified.
- **ADR-008 (marketplace):** no new consequence found.
- **ADR-009 / ADR-009a / ADR-009b (canonical policy location + resolution order + merge-first):**
  already self-correcting (009b amends 009 on evidence); this pass's only addition is Section 8's
  five-policy content review, which ADR-009b explicitly delegates to business-analyst-agent at
  "Phase 0 STOP 0" -- delivered above.
- **ADR-010 (zero bundled hooks):** no new consequence found; this pass's Gherkin (Section 7)
  operationalises its "plugin never owns Stop/Notification" consequence into a testable assertion.

---

## 10. Open Questions Carried Forward (Appendix F)

- **F.1 (Stop-hook per-turn spawn floor) -- CLOSED by this pass, per new evidence supplied in the
  task instructions.** Appendix F.1 left "8/turn assuming scripts exist" vs. "true floor maybe 2"
  explicitly unresolved. New verification (post-Appendix-E) confirms 7 of the 9 referenced scripts do
  not exist on disk; only `sync-version.py` and `voice-notifier.py` do. The real per-turn spawn floor
  for this checkout is **2, not 8**. This closes F.1's open measurement question but OPENS FR-21
  (Section 4): the reason the floor is 2 instead of 8 is that 7 advertised behaviours have been
  silently non-functional, which is a correctness defect, not a performance win. Do not report "floor
  is already 2, FR-8a is nearly done" without also reporting FR-21.
- **F.2 (decomposability granularity divergence) -- remains OPEN, correctly.** Package-level import
  SCC (70% of subpackages cyclic) and function-level call-graph SCC (zero non-trivial SCCs, 708
  fragmented communities) measure different graphs and do not contradict each other. No new evidence
  in this pass changes this. Carried forward unchanged: no clean plugin-extraction boundary exists at
  function-level precision, so no v2.0.0 workstream should treat the package-level cyclicity as proof
  a clean architectural cut exists.
- **F.3 (CHA under-reporting, class-instantiation blind spots, reduced-sample LHS inputs, missing
  TestCoverage, `task-progress-tracking-policy.md` scope reduction, `project_session.py` reachability,
  `src/mcp/` partial trace)** -- all carried forward unchanged; none bear directly on the v2.0.0
  FR/NFR set validated in Sections 2-3, and re-resolving them was out of this pass's budget.

---

## 11. Risks and Assumptions

- **Risk:** FR-19 (`get_policies_dir()` resolver) is currently the only FR in this document gated on
  a human decision (Section 8) rather than an engineering task. If sign-off is delayed, every
  downstream FR that assumes a canonical, complete `docs/policies/` (FR-1, FR-2, FR-3, FR-20) is
  working from an incomplete corpus.
- **Risk:** FR-9a (call-graph builder fix) is a prerequisite for FR-10, and FR-14a's spike is a
  prerequisite for FR-14/15/18. Both are BLOCKING per their own source text. Scheduling FR-10 or
  packaging work before either completes would produce work built on an admittedly-worthless or
  admittedly-unverified foundation.
- **Assumption carried from Appendix E and not independently re-verified in this pass:** the
  `~/.claude/settings.json` hook table (Section 1.2 of `orchestration_prompt.md`) was not re-read
  live during this BA pass; this document trusts the 2026-08-01 verification already on record.
- **Assumption:** the five-policy merge recommendations in Section 8 are content-and-reference-based
  (what exists, what points to it); they do not re-verify runtime enforcement status for
  `auto-skill-agent-selection-policy.md`, `core-skills-mandate.md`, or `auto-plan-mode-suggestion-policy.md`
  beyond what `docs/policies/` cross-references and `CLAUDE.md`'s version history already establish.
  If a hidden code path still invokes any of the two DELETE-recommended selection policies, that
  would need to surface during FR-1's full read-and-internalise pass before FR-19 executes.

---

## 12. Coverage Statement and Scope Reductions

This pass read `as-built-prd.md` (full, 512 lines), `as_built_executive_summary.md` (full, 32
lines), `v2.0.0-plugin-transformation-requirements.md` (full, 292 lines), `SRS.md` (full, 386
lines), and the sections of `docs/orchestration_prompt.md` (line count deliberately not cited -- the file is amended continuously as Phase 0 findings land, so any fixed figure goes stale immediately; cite sections, not line totals) that carry the
named amendments (ADR-006..010, FR-4a, FR-8a, FR-9a, FR-14a, STALE-TOPOLOGY, the five-policy merge
trigger) -- roughly lines 1-330 and 555-682 of that file, located by targeted search rather than a
full linear read, given the context budget for this task. The remaining ~4,100 lines of
`docs/orchestration_prompt.md` (agent dispatch sequencing, per-phase gate mechanics, Phase 6-8
sprint/release detail) were not read and are not represented in this document; none of the six
task instructions required them. The five `~/.claude/policies/`-only files in Section 8 were read
to their first ~45 lines each (purpose/header sections), not in full (2,893 combined lines across
the five) -- sufficient to state what each does and support a recommendation, but a full line-by-line
read is properly FR-1's job, not this scoping pass's.

---

## 13. Change Log (this document)

| Date | Version | Change | Status |
|---|---|---|---|
| 2026-08-01 | 1.0 (draft) | Initial normalisation of the v2.0.0 requirement set against Appendix E/F of the as-built PRD, per Phase 0 BA task. | Awaiting user sign-off on Section 8 |
| 2026-08-01 | 1.1 (Phase 2.1 reconciliation) | Reconciled against the APPROVED `hld.md` (consensus iteration 4) and `plugin_schema_spike.md` (5/5 FR-14a items measured). Rewrote NFR-1, NFR-2, NFR-3 reconciled verdicts and measurable ACs (ADR-018, ADR-016, ADR-011); narrowed FR-18's AC to plugin-attributable residue (unachievable-as-written, stated explicitly, not silently); added FR-24 (uninstall residue runbook) with its own AC and RTM row; replaced FR-15's AC per `hld.md`'s explicit delegation to business-analyst-agent (withdrew the disputed 13-figure, substituted an AST-classifier method, struck through rather than deleted the withdrawn wording); closed a genuine RTM gap where FR-18 had no Section 5 row despite Section 6 pointing to one; updated the Section 7 Gherkin scenarios to match the revised NFR-1/FR-18 ACs; unblocked NFR-5 (FR-14a spike complete); added a dedicated FR-9a AC (4-site closure requirement per `hld.md` OAQ 4, ADR-013 regression-test canary, explicit v2.1 deferral of the 5th truncator) and repointed its RTM row away from a parasitic dependency on FR-10's tests -- escalated from this pass's own initial ADVISORY classification to CRITICAL by the coordinator's independent re-verification. See `docs/phase-2-validation/ba_review.json` for the full coverage/RTM/findings report. | Reconciliation complete; still awaiting user sign-off on Section 8 (unaffected by this pass) |
| 2026-08-01 | 1.3 (Phase 5 -- FR-9b added) | The project owner ruled a newly-found defect IN v2.0.0 scope: the call-graph resolver's ambiguous bare-name fallback at `graph_model.py:265` binds builtin and stdlib method calls to same-named project classes, so `JsonlAppender.append` currently ranks as the codebase's top danger zone on the strength of every `list.append()` call, and that noise is injected into the Step 1 planning prompt as risk signal. Added as **FR-9b**, not FR-25 (FR-25 is already claimed by a proposed CI check in `advisory_items.json`; FR-9b is also semantically correct -- FR-9a is discovery blindness, FR-9b is resolution incorrectness). Added: a Section 4 row, a Section 5 measurable AC (3 assertions), and a Section 6 RTM row. The dependency is stated explicitly in all three: **FR-9a alone is insufficient** -- fixing discovery without fixing resolution yields a larger graph that is still misleading. All source claims in the new rows were verified against the working tree by this pass; the runtime edge counts were measured by two other agents and are labelled as not re-derived here. A separate `resolve_edges()`/`graph.edges` divergence is named as a consumer trap and explicitly marked as NOT affecting shipping code. Mirrored into `SRS.md` as SRS FR-38 (append-only, per rules/44). | Added; fix not started |
| 2026-08-01 | 1.2 (ADR-019 supersession) | solution-architect decided the NFR-1/bundled-MCP question: the plugin bundles ZERO MCP servers (ADR-019, superseding ADR-018's minimum-viable-bundle mitigation adopted at v1.1), with an explicit opt-in `register-mcp` command. Updated all three NFR-1 sites (Section 3 verdict, Section 5 AC, Section 7 Gherkin) and NFR-5's install-test AC to the zero-bundle wording; marked the superseded ADR-018 constraint as correct-when-written-but-overtaken, not disputed. Amended FR-14 (Section 2 note and Section 5 AC) to state explicitly that one-step install now covers commands/agents/skills only, with MCP-backed capabilities (FR-23 push gate, progress writer) requiring the separate `register-mcp` step -- a deliberate, acknowledged trade-off rather than a silent miss, per explicit solution-architect request for BA/PM acknowledgement. See `docs/phase-2-validation/ba_review.json` FIND-02 (superseded), FIND-09 (FR-14 amendment), FIND-10 (flagged, not fixed here -- hld.md Section 10 migration-runbook ordering needs a register-mcp step inserted, owned by solution-architect). | Supersession applied; still awaiting user sign-off on Section 8 (unaffected) |

---

## 14. Return Value Summary

- **FR validation counts (18 total):** 5 Partial (FR-1, FR-2, FR-3, FR-15, FR-17) -- note
  `as-built-prd.md`'s own summary line says "4" but lists 5, flagged in Section 2 as authoritative-5.
  1 Contradicted (FR-10). 3 revised from "not started" to "researched/designed but not built"
  (FR-6, FR-14, FR-16). 1 revised from "out of scope" to "assessed and narrowed" (FR-9 library
  drift). 8 unchanged "not started"/"not assessed" (FR-4, FR-5, FR-7, FR-8 partially via FR-8a,
  FR-11, FR-12, FR-13, FR-18). 0 fully satisfied.
- **NFR validation counts (5 total):** 2 Contradicted (NFR-1, NFR-2). 2 Not designed/started (NFR-3
  with a sharpened stakes-finding, NFR-5 with a new blocking prerequisite). 1 Precondition-only
  (NFR-4). 0 satisfied.
- **New FRs surfaced:** FR-4a, FR-8a, FR-9a, FR-14a (carried forward from `orchestration_prompt.md`,
  not newly minted here) plus FR-19, FR-20, FR-21, FR-22, FR-23 (newly proposed by this pass).
- **RTM gap count: 0** -- every FR/NFR in Sections 2-4 has at least one AC (Section 5 or the original
  AC-1..7) and one target artifact (Section 6).
- **Five-policy merge recommendations (Section 8, one line each):**
  1. `recommendations-policy.md` -> **PORT** (hard dependency from `pr-code-review-policy.md`).
  2. `auto-skill-agent-selection-policy.md` -> **DELETE** (is the hardcoded-selection mechanism FR-10 replaces).
  3. `core-skills-mandate.md` -> **PARTIAL PORT as advisory content** (model-tiering is orthogonal to FR-10).
  4. `adaptive-skill-registry.md` -> **DELETE** (stale manual list, no live dependent, KG obsoletes it).
  5. `auto-plan-mode-suggestion-policy.md` -> **DELETE** (governs a pipeline step removed in v1.13; corroborated twice).

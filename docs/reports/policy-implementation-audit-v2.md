# Policy Implementation Audit v2 (Deliverable 1, consolidated)

Generated 2026-08-01. Consolidates the Phase 0 policy-enforcement analysis into the
Deliverable-1 document of record. The findings below were produced by the Phase C.2 Part B
analysis pass and approved by the project owner; this document was recorded DONE but was
never written to disk. Sprint issues V2-004 through V2-008 (18 story points) rest on it.

**Scope of this pass: consolidation plus spot-verification, NOT re-analysis.** The
underlying audit exists and passed both Phase 0 quality gates. Re-deriving the figures
independently would risk producing numbers that diverge from an approved deliverable. The
approved figures are reproduced here unchanged. What is added is (a) an independent
arithmetic reconciliation, (b) a live-code spot check across status categories, and (c) a
record of one defect found in the source artifacts during that check.

## Evidence labelling

Every figure in this document carries one of three labels. This convention exists because
this project has caught 24 defects whose dominant mode was faithful propagation of
unverified numbers, not fabrication.

| Label | Meaning |
|---|---|
| MEASURED | Checked against disk or source by this pass, now. Reproducible from the stated command or file:line. |
| CITED | Taken from a Phase 0 source artifact. Not independently re-checked by this pass. |
| INFERRED | Derived by reasoning over MEASURED or CITED inputs. The derivation is stated. |

An unlabelled number is a defect. Report it.

---

## 1. Arithmetic reconciliation (first action)

`18 + 11 + 8 + 8 + 1 + 0 = 46`. **The status counts reconcile to the 46-policy corpus.**
MEASURED.

This was checked before anything else and no figure was adjusted to make it sum.

Two further reconciliations, both MEASURED:

- `docs/policies/*.md` on disk: **46 files.** Matches the corpus size.
- `policy_enforcement_raw.json` holds **46 records, 46 unique `policy_file` values, 0 of
  which are missing from disk.** Every record maps to a real file; no record is duplicated;
  no policy is unaccounted for.

A total-check alone is not sufficient evidence. Correction #9-13 in `docs/REVIEW-INDEX.md`
records a wrong policy-disposition tally (4/6/5 against a true 5/5/5) that any total-check
passes, because both sum to 15. The counts below are therefore reported as a full
enumeration, not as a summary. Each count is the length of the list printed beneath it.

---

## 2. Status counts

| Status | Count | Basis |
|---|---|---|
| ENFORCED | 18 | MEASURED (enumeration below) |
| PARTIAL | 11 | MEASURED |
| CONTRADICTED | 8 | MEASURED |
| DOCUMENTED-ONLY | 8 | MEASURED |
| STALE-TOPOLOGY | 1 | MEASURED |
| DEAD | 0 | MEASURED |
| **Total** | **46** | **MEASURED** |

MEASURED here means: this pass re-derived the counts by grouping all 46 records in
`policy_enforcement_raw.json` by their `status` field and counting each group. The
classification decisions themselves are CITED from Phase C.2 Part B; this pass did not
re-classify any policy.

**Zero DEAD is deliberate, not an omission.** CITED: Class Hierarchy Analysis seeds every
module's own `__main__` block as an entry point, so a module can report `reachable_cha:
true` purely from being a standalone CLI script, independent of production use. Given that
confound, ambiguous cases were classified CONTRADICTED (positive evidence of a mismatch) or
PARTIAL, reserving DEAD for a confidently-unreachable case that did not arise.

### 2.1 ENFORCED (18)

| Policy | Confidence | Enforcement point |
|---|---|---|
| automatic-task-breakdown-policy.md | HIGH | `hooks/pre_tool_enforcer/policies/task_breakdown.py:12` |
| code-graph-analysis-policy.md | HIGH | `langgraph_engine/sdlc_pipeline/architecture/00-code-graph-analysis/` |
| coding-standards-enforcement-policy.md | MEDIUM | `langgraph_engine/standards/selector.py:114` |
| common-standards-policy.md | MEDIUM | `langgraph_engine/standards/selector.py:449`, `:273` |
| context-reading-policy.md | HIGH | `hooks/pre_tool_enforcer/policies/context_read.py:14` |
| cross-project-patterns-policy.md | MEDIUM | `langgraph_engine/context_sync/architecture/pattern_detector.py:388` |
| final-summary-policy.md | HIGH | `langgraph_engine/sdlc_pipeline/nodes/closure_docs_summary_wrapper.py:70` |
| hook-system-policy.md | HIGH | `hooks/pre_tool_enforcer/core.py:453-469` (`_BLOCKING_POLICIES`) |
| issue-closure-policy.md | HIGH | `langgraph_engine/sdlc_pipeline/github_lifecycle.py:543` |
| prompt-generation-policy.md | HIGH | `langgraph_engine/sdlc_pipeline/architecture/prompt_gen_expert_caller.py:159` |
| quality-gate-policy.md | HIGH | `langgraph_engine/sdlc_pipeline/quality_gate.py:637` |
| recovery-policy.md | MEDIUM | `langgraph_engine/preflight_guard/recovery.py:234` |
| task-phase-enforcement-policy.md | HIGH | `hooks/pre_tool_enforcer/policies/task_breakdown.py:12` |
| test-generation-policy.md | HIGH | `langgraph_engine/sdlc_pipeline/test_generator.py:39` |
| tool-optimization-policy.md | HIGH | `hooks/pre_tool_enforcer/policies/read_opt.py:8`, `grep_opt.py:8` |
| unicode-fix-policy.md | HIGH | `langgraph_engine/preflight_guard/nodes.py:62-147` |
| version-release-policy.md | MEDIUM | `hooks/pre_tool_enforcer/policies/push_gate.py:354`, `:408` |
| windows-path-policy.md | HIGH | `langgraph_engine/preflight_guard/nodes.py:240-323` |

Count of rows: 18. Enforcement points are CITED except the two spot-verified in section 4.

### 2.2 PARTIAL (11)

| Policy | Confidence |
|---|---|
| common-failures-prevention.md | HIGH |
| context-management-policy.md | MEDIUM |
| documentation-update-policy.md | MEDIUM |
| encoding-validation-policy.md | HIGH |
| error-recovery-policy.md | MEDIUM |
| github-issues-integration-policy.md | MEDIUM |
| implementation-execution-policy.md | HIGH |
| metrics-monitoring-policy.md | HIGH |
| pr-code-review-policy.md | MEDIUM |
| session-chaining-policy.md | MEDIUM |
| task-progress-tracking-policy.md | LOW |

Count of rows: 11.

`task-progress-tracking-policy.md` is the corpus's only LOW-confidence record. CITED: it
was scored on module-level evidence only, without tracing `task_tracking.py`'s check
function into `core.py`'s dispatch table the way the 12 PreToolUse policies were. That is a
stated scope reduction, not an assumed ENFORCED.

### 2.3 CONTRADICTED (8)

| Policy | Nature of the contradiction |
|---|---|
| anti-hallucination-enforcement.md | Real code, zero production importers repo-wide |
| architecture-script-mapping-policy.md | Self-contradictory (3 vs 6 in its own text); names 12+ target files absent from the repo |
| callgraph-analysis-policy.md | File-scan cap makes impact analysis blind to the package it protects (see section 6 for a citation defect on this row) |
| git-auto-commit-policy.md | Hook-coupled path targets a directory that does not exist |
| intelligent-decision-engine-policy.md | Describes a consolidation never built; the systems it unifies were deleted in v1.13 |
| session-memory-policy.md | Hook-coupled path targets a directory that does not exist |
| session-pruning-policy.md | Hook-coupled path targets a directory that does not exist |
| tool-usage-optimization-policy.md | Self-claims "NO DUPLICATION" while sharing its sole enforcement point with two other files |

Count of rows: 8.

### 2.4 DOCUMENTED-ONLY (8)

| Policy | Reason |
|---|---|
| EXECUTION-SYSTEM-FIXES-SUMMARY.md | Point-in-time changelog, no runtime mechanism |
| INTELLIGENT-PROMPT-GENERATION-UPGRADE.md | Point-in-time changelog |
| file-management-policy.md | No enforcement point found |
| mcp-plugin-discovery-policy.md | Only a FlowState passthrough field exists |
| parallel-execution-policy.md | No engine code; describes calling-agent behaviour |
| proactive-consultation-policy.md | Explicitly deprecated by its own text |
| test-case-policy.md | No distinct gate found |
| user-preferences-policy.md | Only a passthrough context field exists |

Count of rows: 8.

### 2.5 STALE-TOPOLOGY (1)

`intelligent-model-selection-policy.md`. CITED: every eligible policy was retranslated to
the current Level 0/1/2 plus Steps 0-8 naming before classification, and retranslation
resolved 16 of the raw token-grep floor into other statuses via `LEGACY_MARKER_ALIASES`
(old Step 12/13/14 mapping to SDLC_STEP_6/7/8). Only this one policy stayed
STALE-TOPOLOGY, because one of its five inputs (the plan-mode decision) was itself deleted
in v1.13, leaving the retranslated question unanswerable rather than merely renamed.

### 2.6 DEAD (0)

Empty by design. See the note under section 2.

---

## 3. Correction record: the "46/46 orphan policies" figure was FALSE

**An earlier pass on this deliverable reported "46 of 46 orphan policies". That figure is
retracted. The correct figure is 14 of 46.**

Anyone who saw the earlier number needs to find its retraction, so it is stated here
explicitly rather than only in the artifact that superseded it.

**Root cause.** Not a measurement error and not agent fabrication. It was an orchestrator
briefing error: `SRS.md` was never supplied to the knowledge-graph build, so that build had
no requirement corpus to correlate policies against. Every policy therefore matched nothing,
and "matched nothing" was written down as "orphaned". The output was absence of evidence
recorded as evidence of absence. CITED from `docs/REVIEW-INDEX.md` correction #1 and
`as-built-prd.md`, which notes it replaces the false `orphan_policies_count: 46` finding in
`codebase_kg/kg_report.json`.

**Corrected figure.** Redone against the SRS's real 15 FR/NFR entries: **14 of 46 (30.4%)
are genuine orphans.** CITED.

**Six of the 14 would stay orphaned even under perfect SRS coverage.** CITED. They are
`anti-hallucination-enforcement`, `architecture-script-mapping`, `git-auto-commit`,
`intelligent-decision-engine`, `session-pruning`, and `cross-project-patterns`. The first
five are independently CONTRADICTED; the sixth is a live ENFORCED capability that the
current SRS simply never states as a requirement at any priority. In all six cases the
capability is either broken or genuinely out of the SRS's stated scope, so a perfect
correlation pass would still classify them NONE. The remaining eight are orphaned because
of the SRS-ingestion gap and are the addressable population.

**Why this matters for reading the rest of this report.** The gap between 46 and 14 is not
a rounding difference; it changes the conclusion from "the policy corpus is entirely
disconnected from requirements" to "roughly a third is disconnected, and half of that third
is disconnected for reasons an SRS fix cannot touch". Any v2.0.0 planning that inherited
the 46 figure was working from a briefing artifact.

---

## 4. Spot-verification against live code

This section is what allows the document to rest on evidence rather than on recollection of
an approved result.

**Sample size: 8 checks across 4 of the 6 status categories, plus 1 corpus-level check.**

**Selection basis** (stated so the sample is not mistaken for a survey):

1. All 3 policies previously reported as silent no-ops, because they are the report's
   highest-consequence operational claim and were named for verification.
2. 2 ENFORCED policies, chosen for *different enforcement mechanisms* rather than at
   random, so that a pass does not merely confirm one code path twice: one hook dispatch-table
   policy and one LangGraph node policy.
3. 3 CONTRADICTED policies, chosen for different contradiction *kinds*: a configuration cap,
   an unreferenced module, and a duplicated enforcement point. Two were required; a third was
   added because it was cheap to check on the same evidence.

**I did NOT verify all 46 policies.** PARTIAL, DOCUMENTED-ONLY and STALE-TOPOLOGY were not
sampled at all. Their counts are MEASURED (the enumeration is real) but their individual
classifications remain CITED and unverified by this pass.

### 4.1 The three maintenance no-ops (required check)

Prior finding, CITED: auto-commit, session-save and session-pruning target
`scripts/architecture/` subtrees that do not exist, and their `.exists()` guards fail
silently with no log trace, on every turn.

**Result: CONFIRMED. All three target directories are absent.** MEASURED.

| Policy | Guard target | On disk |
|---|---|---|
| git-auto-commit-policy.md | `scripts/architecture/03-execution-system/09-git-commit/git-auto-commit-policy.py` | MISSING |
| session-memory-policy.md | `scripts/architecture/01-sync-system/session-management/auto-save-session.py` | MISSING |
| session-pruning-policy.md | `scripts/architecture/01-sync-system/session-pruner.py` | MISSING |

MEASURED detail: `scripts/architecture/` contains exactly two entries,
`03-execution-system/` and `generate_system_diagram.py`. The directory
`scripts/architecture/01-sync-system/` does not exist at all, which accounts for the
session-save and session-pruning failures in one stroke. `scripts/architecture/09-git-commit/`
does not exist; neither does `03-execution-system/09-git-commit/`. The
`03-execution-system/` subtree that does exist holds only
`00-code-graph-analysis/code-graph-analyzer.py` and `failure-prevention/failure-kb.json`.

MEASURED, and worth noting because it is a near miss that would mislead a reader skimming
the tree: `03-execution-system/failure-prevention/` **exists and contains `failure-kb.json`**,
but the script the Stop hook actually spawns from that same directory,
`common-failures-prevention.py`, **does not exist**. The directory being present makes the
spawn look plausible on a casual check while still no-opping.

The silence is confirmed by inspection of `hooks/stop_notifier/core.py:78, :106, :159`
(MEASURED): each spawn is wrapped in `if <script>.exists():` with **no `else` branch and no
log statement on the negative path**. The surrounding `try/except` writes a log line only
when an exception is raised, and a `False` from `.exists()` raises nothing. There is
therefore no runtime signal of any kind that these three policies are inert.

### 4.2 ENFORCED, reachability check (required: at least 2)

The requirement was to confirm the enforcing code is *reachable*, not merely present. Both
checks target the reachability link specifically.

**Check 1: `context-reading-policy.md`.** Cited point:
`hooks/pre_tool_enforcer/policies/context_read.py:14 check_context_read_complete`.

Result: **REACHABLE. CONFIRMED.** MEASURED. The function is present at the cited line, and
critically it is registered as `("context_read", check_context_read_complete)` in the
`_BLOCKING_POLICIES` list at `hooks/pre_tool_enforcer/core.py:453-469`. That list is the
dispatch table `_evaluate_tool_call` iterates, so registration is the reachability
evidence, not mere presence. The function guards `Write`, `Edit`, `NotebookEdit` and `Bash`.

**Check 2: `unicode-fix-policy.md`.** Cited point:
`langgraph_engine/preflight_guard/nodes.py:62-147 node_unicode_fix`.

Result: **REACHABLE. CONFIRMED.** MEASURED. Defined at `nodes.py:62`, and wired into the
graph at `langgraph_engine/orchestrator.py:657` as node `preflight_guard_unicode`. The
decisive evidence is the edge, not the node registration: `orchestrator.py:663` adds
`graph.add_edge(START, "preflight_guard_unicode")`, making it the **first node after START**
and therefore unconditionally reachable on every pipeline run. It has an outbound edge to
`preflight_guard_encoding` (`:664`) and a re-entry edge from `fix_preflight_guard` (`:693`).

### 4.3 CONTRADICTED, does-it-still-hold check (required: at least 2)

**Check 3: `anti-hallucination-enforcement.md`.** Claim: real code, zero production
importers repo-wide.

Result: **CONTRADICTION STILL HOLDS.** MEASURED. A repo-wide grep for `anti_hallucination`
across all `.py` files returns hits in exactly one file,
`langgraph_engine/sdlc_pipeline/architecture/00-prompt-generation/anti_hallucination_enforcement.py`,
and every hit is a self-reference (its own docstring usage examples, its own log strings,
its own print statements). **No file anywhere in the repository imports it.** Its only
entry path is manual CLI invocation. This is also a first-hand confirmation of the CHA
confound described in section 2: the module reports as reachable purely because of its own
`__main__` block.

**Check 4: `callgraph-analysis-policy.md`.** Claim: the file-scan cap makes impact analysis
blind to the package it is meant to analyze.

Result: **CONTRADICTION STILL HOLDS, and is worse than a cap-versus-corpus comparison
suggests.** MEASURED:

- `langgraph_engine/parsers/call_graph_builder_legacy.py:64` sets `MAX_FILES = 300`.
- It binds: `:76` uses it as the `max_files` default in `CallGraphBuilder.__init__`, and
  the value is enforced in the discovery loop at `:107` and `:118` (`if len(found) >=
  self.max_files: break`).
- Repo `.py` files on disk, excluding `.git`, `__pycache__` and `.venv`: **411**. The cap is
  genuinely binding, not a ceiling above the corpus.
- A second, independent cap survives fixing the first:
  `langgraph_engine/parsers/graph_model.py:43` sets `DEFAULT_MAX_PATHS = 500`
  (`CLAUDE_CG_MAX_PATHS`), truncating path traversal regardless of file count.

**Check 5: `tool-usage-optimization-policy.md`.** Claim: it shares its sole enforcement
point with `tool-optimization-policy.md` while its own text claims "NO DUPLICATION".

Result: **CONTRADICTION STILL HOLDS.** MEASURED. There is exactly one pair of check
functions, `check_read_opt` and `check_grep_opt`, defined once in
`hooks/pre_tool_enforcer/policies/read_opt.py` and `grep_opt.py`, aliased in
`core.py:193-194`, re-exported at `:373-374`, and registered once each in
`_BLOCKING_POLICIES` at `:466-467`. Both policies resolve to that same single registration.
There is no second, distinct gate for the second policy to own.

### 4.4 Corpus-level check

**Check 6:** all 46 `policy_file` paths in `policy_enforcement_raw.json` resolve to files
that exist on disk, and `docs/policies/` contains exactly 46 `.md` files. **CONFIRMED,
0 missing, 0 duplicated.** MEASURED.

---

## 5. Stop hook: dead-script count

The prior finding, CITED from `docs/REVIEW-INDEX.md` correction #3, is that **7 of the 9
scripts referenced by the Stop hook do not exist**, reducing the true spawn floor from a
claimed 8 per turn to roughly 2. This materially affects how the whole report is read,
because three policies no-op on every turn for this reason alone, independently of any hook
change that v2.0.0 might make.

**The count I measured is 7, and it confirms the prior figure. But the framing needs one
correction that the bare number hides.** MEASURED.

I enumerated the spawn targets by grepping every `subprocess.run` guarded by an `.exists()`
check in the `hooks/stop_notifier/` package and resolving each path. **9 spawn targets**,
which matches the prior enumeration's denominator.

| # | Script target as referenced | Exists at referenced path | Exists anywhere in repo |
|---|---|---|---|
| 1 | `scripts/architecture/03-execution-system/09-git-commit/git-auto-commit-policy.py` | NO | NO |
| 2 | `scripts/architecture/01-sync-system/session-management/auto-save-session.py` | NO | NO |
| 3 | `scripts/architecture/01-sync-system/session-management/archive-old-sessions.py` | NO | NO |
| 4 | `scripts/architecture/01-sync-system/session-pruner.py` | NO | NO |
| 5 | `scripts/architecture/03-execution-system/failure-prevention/common-failures-prevention.py` | NO | NO |
| 6 | `scripts/architecture/01-sync-system/user-preferences/preference-auto-tracker.py` | NO | NO |
| 7 | `scripts/architecture/03-execution-system/02-plan-mode/plan-session-archiver.py` | NO | NO |
| 8 | `hooks/stop_notifier/sync-version.py` (`post_impl.py:285`) | NO | YES, at `scripts/tools/sync-version.py` |
| 9 | `<CURRENT_DIR>/voice-notifier.py` (`helpers.py:142`) | NO (this environment) | YES, at `scripts/tools/voice-notifier.py` |

**The number I report is 7**, on the criterion "does not exist anywhere in the repository":
rows 1 through 7, all under `scripts/architecture/`. This reconciles exactly with the prior
finding, and I take the prior denominator of 9 to be the same set enumerated here.

Two refinements that the figure of 7 conceals, both MEASURED:

- **Row 8 is unconditionally broken too, and is not environment-dependent.**
  `post_impl.py:285` resolves the script as `Path(__file__).resolve().parent /
  "sync-version.py"`, that is, as a sibling of `post_impl.py` inside
  `hooks/stop_notifier/`. No such file is there. A copy does exist at
  `scripts/tools/sync-version.py`, so a search for the filename finds it and it is
  reasonably counted as "exists" -- but **the hook cannot reach it**, because the path it
  computes never points there. On a strict "does the spawn resolve" criterion the count is
  **8 of 9**, not 7. I report 7 to stay consistent with the approved figure, and flag the
  discrepancy rather than smoothing it.
- **Row 9 is environment-dependent and I cannot assert it in general.** `VOICE_SCRIPT` is
  `CURRENT_DIR / "voice-notifier.py"` where `CURRENT_DIR` derives from
  `CLAUDE_IDE_INSTALL_DIR`. With that variable unset, as it is here, it resolves to
  `C:\Users\techd\.claude\memory\current\voice-notifier.py`, which does not exist (nor does
  `C:\Users\techd\.claude\scripts\`). Under IDE mode it could resolve to an installed copy.
  **I could not determine whether this one resolves in production**, and I have not counted
  it as dead.

The consequence for the three maintenance policies is unaffected by either refinement: rows
1 through 4 cover auto-commit, session-save and session-pruning, and all four are absent
repo-wide with no ambiguity.

---

## 6. Defect found in the source artifacts during this pass

Reported rather than smoothed, per the accuracy rules. This is a live instance of correction
class #14 in `docs/REVIEW-INDEX.md`, backward propagation: a claim corrected in one place
and left standing in the artifacts it was copied into.

**`policy_enforcement_raw.json`, the primary machine artifact behind this very deliverable,
still cites the dead-code site as the enforcement point for
`callgraph-analysis-policy.md`.** MEASURED. At `policy_enforcement_raw.json:42` the
`enforcement_point` field reads `langgraph_engine/call_graph_builder.py ->
langgraph_engine/parsers/config.py:11 MAX_FILES=300`, and the `evidence` field at `:44`
repeats it.

`parsers/config.py:11` is **dead code**. MEASURED: its `MAX_FILES = 300` is imported by
exactly one file, `parsers/__init__.py:22`, which merely re-exports it; a repo-wide grep
finds **no consumer of that constant anywhere in `langgraph_engine/`**. Changing it would
produce a diff that looks like the fix, pass review, and leave file discovery stopped at
300. The binding caps are `parsers/call_graph_builder_legacy.py:64` and
`parsers/graph_model.py:43`, as verified in section 4.3.

**Propagation status across the Phase 0 artifacts** (MEASURED, by grepping
`docs/phase-0-reverse-engineering/` for `parsers/config.py`):

| Artifact | Carries the dead-code citation | Correction present |
|---|---|---|
| `as_built_executive_summary.md` | yes, in context | YES, "SITE CORRECTED 2026-08-01" |
| `builder_divergence.md` | yes, in context | YES, "Recommendation SUPERSEDED 2026-08-01" |
| `policy_enforcement_raw.json` | yes | **NO** |
| `contradictions.md` | yes (lines 17, 32) | **NO** |
| `as-built-prd.md` | yes (lines 113, 133) | **NO** |
| `ast_call_graph_summary.md` | yes (line 50) | **NO** |

**2 artifacts corrected, 4 still carrying it.** The two corrected are the human-facing
summaries; the four uncorrected include the machine-readable record and the ranked
contradictions list, which are the artifacts most likely to be consumed programmatically or
cited downstream.

**This does not change any status count.** `callgraph-analysis-policy.md` remains correctly
classified CONTRADICTED, and the contradiction is real and still holds; only the site
attribution in four artifacts is wrong. Recorded here because a reader who follows the
citation from `contradictions.md` or the raw JSON will land on a constant whose modification
accomplishes nothing.

**This report does not modify those four files.** Correcting them is a separate change with
its own review.

---

## 7. Hook coupling

CITED throughout this section; not spot-verified beyond the three no-ops in section 4.1.

- **4 of 4 match.** Every policy that names a hook in its own text (`hook-system`,
  `implementation-execution`, `metrics-monitoring`, `tool-optimization`) is confirmed
  hook-coupled. No case was found of a policy description overclaiming a hook it does not
  have.
- **11 policies are hook-coupled without saying so**: `automatic-task-breakdown`,
  `common-failures-prevention`, `context-management`, `context-reading`, `git-auto-commit`,
  `session-memory`, `session-pruning`, `task-phase-enforcement`, `task-progress-tracking`,
  `tool-usage-optimization`, `version-release`. Count of names listed: 11.
- **Coupling to a hook is not the same as the hook's target running.** Three of those 11
  (`git-auto-commit`, `session-memory`, `session-pruning`) are genuinely hook-coupled and
  still no-op, because the coupled path spawns a script that is not on disk. Section 4.1
  confirms this MEASURED.

---

## 8. What this pass could NOT determine

Stated as clearly as what it could, because a bounded check reported as a clean one is the
defect class this project has caught most often.

1. **41 of the 46 individual classifications were not re-verified.** The sample was 5
   policies plus 3 no-op checks. The counts are MEASURED; the per-policy status decisions
   remain CITED. PARTIAL, DOCUMENTED-ONLY and STALE-TOPOLOGY were not sampled at all, so no
   claim is made that any individual policy in those three groups is correctly classified.
2. **The 14-of-46 orphan figure is CITED, not re-derived.** Re-deriving it would require
   re-running the SRS correlation, which is exactly the re-analysis this pass was scoped
   out of. The retraction of the 46/46 figure is what is being recorded; the replacement
   figure carries its source's confidence, not this pass's.
3. **Whether `voice-notifier.py` resolves in production is undetermined.** It depends on
   `CLAUDE_IDE_INSTALL_DIR` at hook runtime. See section 5, row 9.
4. **CHA under-reports hook-policy liveness, and this pass did not correct for it
   generally.** CITED: `pre-tool-enforcer.py` loads `core.py` via
   `importlib.util.spec_from_file_location` and then aliases `policies/*.py` functions
   through module attributes; the static pass cannot trace either hop, so those functions
   show `reachable_cha: false` despite being live. The two ENFORCED spot checks in section
   4.2 worked around this by reading the dispatch table and graph edges directly, but only
   for those two policies.
5. **Two PARTIAL policies' creation-side methods** (`documentation-update-policy.md`,
   `github-issues-integration-policy.md`) show `reachable_cha: false` on a class
   instantiated once in a wrapper file, while sibling methods on the same class show `true`.
   CITED: scored PARTIAL rather than DEAD given the blind spot in item 4, and **not
   independently re-verified by call-site tracing** either by the original pass or by this
   one.
6. **The Stop-hook spawn floor itself remains an open measurement conflict.** CITED from
   `as_built_executive_summary.md`: "8 per turn assuming scripts exist" against a
   verified-absent script set implying a true floor near 2. This pass confirms the script
   absences that drive the low estimate, but did not measure actual spawn counts at runtime.
7. **No `sonarqube`, coverage or runtime-trace evidence was consulted.** TestCoverage was
   unavailable to the original pass as well; `lhs.json` substitutes a DocCoverage-only
   proxy, explicitly flagged as such rather than fabricated.

---

## 9. Summary for the sprint

- Status counts reconcile: **46 policies, 18/11/8/8/1/0**. MEASURED.
- The **"46/46 orphan policies" figure is retracted**; the real figure is **14 of 46**, six
  of which no SRS fix would rescue. This is the correction most likely to have propagated
  into v2.0.0 planning.
- **Three maintenance policies are already dead paths today**, before any hook change is
  made. Confirmed against disk. Deciding their fate is a separate call from the hook-removal
  decision, because their failure does not depend on it.
- **7 of 9 Stop-hook target scripts do not exist** (MEASURED, confirming the prior figure);
  an 8th exists in the repo but not at the path the hook computes.
- One **citation defect found in four source artifacts** during verification, reported in
  section 6, changing no count.
- **41 of 46 classifications remain CITED and unverified.** Treat them as best available,
  not as verified.

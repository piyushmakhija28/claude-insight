# Policy Corpus Inventory Summary (Phase C.2-A, code-independent)

Generated 2026-08-01. Scope: markdown/JSON policy and standards documents only -- no Python source read. Enforcement status is NOT determined here (Part B, post-call-graph).

## Counts

- **docs/policies/** (canonical per ADR-009): 46 files, all catalogued.
- **~/.claude/policies/** (what `get_policies_dir()` reads today): 5 top-level dirs (`01-sync-system`, `02-standards-system`, `03-execution-system`, `failure-prevention` nested under `03-execution-system`, `testing`); ~34 policy `.md` files + `failure-kb.json`.
- **policies/** in target repo: 1 file only -- `03-execution-system/failure-prevention/failure-kb.json`.
- **docs/standards/**: 52 files catalogued (46 numbered rules 01-46 + 6 unnumbered framework files).
- **unstated_mechanism_count**: 6 (`architecture-script-mapping-policy.md`, `EXECUTION-SYSTEM-FIXES-SUMMARY.md`, `INTELLIGENT-PROMPT-GENERATION-UPGRADE.md`, `test-case-policy.md`, `user-preferences-policy.md`, `file-management-policy.md`).

## Hook-Dependent Policies (explicit PreToolUse/PostToolUse/Stop hook named)

Only **4 of 46** docs/policies files explicitly name a Claude Code hook type as their enforcement mechanism:

1. **hook-system-policy.md** -- defines the architecture itself: PreToolUse -> `pre-tool-enforcer.py`, PostToolUse -> `script-chain-executor.py` -> `post-tool-tracker.py`.
2. **implementation-execution-policy.md** -- "Stop hook auto-triggers Steps 11-14" in Hook Mode.
3. **metrics-monitoring-policy.md** -- per-session metrics "aggregated at session completion (Step 14 or Stop hook)".
4. **tool-optimization-policy.md** -- limits "enforced by the PreToolUse hook".

The remaining 42 files either name a pipeline Step/Level number (most common), name a script without calling it a "hook", or state no mechanism at all (the 6 UNSTATED cases above). These 42 are the policies most exposed to silent breakage if PreToolUse/PostToolUse hooks are ever deleted or bypassed, precisely because their documents do NOT claim hook-based enforcement -- meaning either (a) they rely on an undocumented hook mechanism, or (b) they were never hook-enforced to begin with. Part B must determine which.

## Top 5 Ranked Internal Contradictions

1. **[CRITICAL] Pipeline renumbering staleness, corpus-wide.** Nearly all 46 docs/policies files and all docs/standards files reference the OLD topology -- `Level -1`/`Level 1`/`Level 2`/`Level 3: Execution System (15 Steps: 0-14)`, `Level 2 Standards System` -- while the project's own root CLAUDE.md (2026-07-31) documents the renamed current topology: `Level 0` (Pre-Flight), `Level 1` (Context Sync), `Level 2` (SDLC Execution Core, 9 active Steps 0-8 only), with the old "Level 2: Standards" retired from the numbered-level count entirely. Steps 9-14 referenced throughout the policy corpus (Branch Setup, Implementation, PR Review, Issue Closure, Documentation, Final Summary) do not exist under those numbers today.
2. **[HIGH] Duplicate, conflicting tool-optimization policies.** `tool-optimization-policy.md` (explicit limits table, claims PreToolUse-hook enforcement) and `tool-usage-optimization-policy.md` (v2.0.0 "CONSOLIDATED", Step 5, explicitly claims "NO DUPLICATION") cover the identical subject with different mechanisms and different specifics; a third file, `docs/standards/TOOL-OPTIMIZATION-LEVEL2-STANDARD.md`, adds a third treatment.
3. **[MEDIUM-HIGH] Contradictory claims about interactive user prompting.** `proactive-consultation-policy.md` (deprecated) says mid-pipeline interactive consultation is categorically impossible ("cannot be used within LangGraph pipeline execution context"); `recovery-policy.md` describes a live interactive "auto-fix vs skip" choice that is bypassed only in non-TTY/hook mode -- implying it IS reachable otherwise.
4. **[MEDIUM] Undefined task-to-issue cardinality.** `automatic-task-breakdown-policy.md` v2.0.0 mandates >=1 Task per request unconditionally; `github-issues-integration-policy.md` v3.0.0 mandates one issue per "problem statement," not per task. Neither document states the task-to-problem-statement mapping rule.
5. **[MEDIUM] Copy drift in an otherwise-identical policy.** `context-management-policy.md` is version-identical (v3.0.0) in docs/policies and home-claude, but the two copies name different implementation scripts (`context-monitor.py` vs `context-monitor-v2.py`).

## Three-Location Reconciliation Verdict

The three locations are **not a single source of truth with two mirrors** -- they are three partially-overlapping, independently-drifted corpora. Of the policy concepts checked: several pairs are byte-identical in their opening sections (git-auto-commit, prompt-generation, github-issues-integration v3.0.0, test-case, common-failures-prevention), one pair is content-identical but filed under **different filenames** in each location (`pr-code-review-policy.md` docs-side vs `github-branch-pr-policy.md` home-side -- a naming drift that would fool any filename-based reconciliation tool), one pair is version-identical but names a **different implementation script** (context-management), and a **full policy subtree** (skill/agent selection: `adaptive-skill-registry.md`, `auto-skill-agent-selection-policy.md`, `core-skills-mandate.md`) plus two standalone policies (`auto-plan-mode-suggestion-policy.md`, `recommendations-policy.md`) exist **only** in home-claude with no docs/policies counterpart at all -- despite `pr-code-review-policy.md` in docs/policies explicitly listing `recommendations-policy.md` as a hard dependency it cannot resolve from within its own declared-canonical corpus. Conversely, **14 of the 46** docs/policies files (roughly 30%) have no home-claude counterpart under any of the 5 subdirectories, meaning that if CLAUDE.md's claim that `get_policies_dir()` reads only home-claude is accurate, those 14 policies are currently invisible to the runtime loader -- a claim Part B must verify against code, not assumed here. The repository's own `policies/` tree contributes almost nothing to this reconciliation: it holds only the `failure-kb.json` data file, consistent with CLAUDE.md's note that the historical `00-auto-fix/01-sync/02-standards/testing` subtrees do not exist on disk there.

## docs/standards/ Catalogue

52 files: 46 numbered rules (01-46, matching `~/.claude/rules/`) covering common/backend/microservices/frontend/security standards (01-05), five language standards mirrored verbatim from this session's own loaded rules (06 TypeScript, 07 Go, 08 Rust, 09 Swift, 10 Kotlin), documentation governance (11) and docstrings-only (12), thirteen Spring-Boot-specific conventions (13-32), a universal test roadmap (33), frontend package structure (34), five testing-standard tiers (35-43), and the three Level-2.3-numbered lifecycle rules for SRS (44), UML diagrams (45), and architecture documentation (46) -- plus 6 unnumbered framework files (C#, Django, Flask, Java, Spring Boot, and a Tool-Optimization-as-Level-2-Standard note) that independently overlap the tool-optimization contradiction above.

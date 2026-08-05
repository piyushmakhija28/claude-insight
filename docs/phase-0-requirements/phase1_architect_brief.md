# Phase 1 Architect Brief -- v2.0.0 Hook-Free Plugin Transformation

**To:** solution-architect, Phase 1.1 (HLD)
**From:** prompt-generation-expert, Phase 0.7
**Status:** Both Phase 0.5 validation gates PASSED at 1.00/1.00 (NLI + FactScore). This brief is
prepended to your AGREED CONTRACTS. Read it before the source artifacts, not instead of them.

---

## 1. Architecturally Significant Requirements

Ranked by WSJF (`product-sequencing-v2.md` SS2, Reinertsen CoD/size) where the item has an HLD-shaping
design consequence, not just an implementation task.

1. **FR-23 -- push_gate -> MCP port, MUST PRECEDE FR-4 (WSJF 7.67).** Architecturally significant
   because it is an ordering constraint with no mechanical enforcement today (SS1's risk #3): the HLD
   must specify a CI assertion (existence-and-reachability of the MCP-side replacement, not "old hook
   still present") that fails the build if PreToolUse is gone with no working replacement gate.
2. **FR-4/FR-5 -- delete PreToolUse+PostToolUse, take UserPromptSubmit off the hot path (WSJF 7.00).**
   This is ADR-006 itself. Structurally safe (135/2,218 nodes, 6.09%, zero surviving cross-boundary
   edges) but carries three named consequences (SRS FR-9 violation, push-gate reopening, NFR-3 loss)
   that the HLD must design around, not merely note.
3. **NFR-1/NFR-2 -- zero-overhead-when-idle + no-fixed-timeout measurement harness (WSJF 7.00).** These
   are the project's primary success metrics. NFR-1 is process-count-delta based, never timing-based --
   the HLD's packaging design must be provably compatible with a process-count test, not just "probably
   fast."
4. **NFR-3 -- replacement crash-recovery writer, explicitly named (unsized, but structurally
   mandatory).** `post-tool-tracker.py` is the SOLE writer of checkpoint state backing SRS's
   "resume from any step after crash" guarantee, and also backs an NFR-1 warm-daemon performance path.
   Deleting PostToolUse without designing this replacement silently breaks two guarantees at once.
5. **FR-9a -- CallGraph scope-aware fix, prerequisite for FR-10 (WSJF 4.60, but the single riskiest
   critical-path link).** Not a cap raise: discovery is alphabetical-by-subpackage, so
   `sdlc_pipeline/` (45/45 files) is dropped entirely today. The HLD must specify scope-aware discovery
   that cannot silently drop a package, plus a regression test asserting `sdlc_pipeline/` presence.
6. **FR-10..FR-13 -- KG-driven agent/skill selector (WSJF 1.69, lowest score, largest job, flagship
   deliverable -- size cannot be decomposed without breaking the FR-9a prerequisite).** Also carries a
   mandatory sub-requirement not separately WSJF-scored: the 99 domain-KG `relationships.json` files
   have SIX distinct schema shapes (58/22/7/7/3/2 split by edge-key and container form); the selector's
   KG-read boundary needs a normalising adapter that distinguishes `PARSE_ERROR` from genuine no-match
   -- a silent parse failure masquerading as FR-12's degraded fallback is explicitly called out as the
   worst available outcome.
7. **FR-14a -- plugin-schema spike, 4 unknowns (WSJF 6.33, gates D5 packaging freeze).** Item 2
   (`CLAUDE_PLUGIN_ROOT` in a spawned Python process's `os.environ`) directly gates ADR-009a branch 2;
   a NO answer without a working fallback breaks FR-15 for standalone (non-dev-mode) installs, the
   primary distribution mode under ADR-008.
8. **FR-14 -- plugin skeleton build.** Manifest + convention-based directory discovery + ADR-010
   zero-hooks conformance (CI CRITICAL check: any `hooks/` or `hooks.json` in the plugin tree fails the
   build). This is where ADR-006 through ADR-010 all become one artifact.
9. **FR-15/FR-17 -- path_resolver/encoding remediation (WSJF 4.67).** Sizing is explicitly UNRESOLVED
   for FR-15 -- see OAQ 6 below. FR-17's 19-site `open()` count is confirmed and stable.
10. **FR-16/NFR-5 -- pinned build-time snapshot + install/invoke/uninstall lifecycle tests (WSJF 3.20 /
    2.80).** Gated by FR-14a; the snapshot only bundles routing registries + dispatchable-agent
    personas, not all 505 agent directories (ADR-007).
11. **FR-8a -- Stop-hook decision + instrumentation + reference retirement (WSJF 6.00, ships v2.0.0;
    see Settled Decisions below for the scope split).** Architecturally significant because the
    retained Stop hook must not reintroduce NFR-2's fixed-timeout failure mode while it is being
    audited and reduced.
12. **FR-6/FR-22 -- ADR-006 doc + SRS append (WSJF 13.00 / 12.00, highest-WSJF only because size=1;
    do them immediately, not as "the most important work").** Governance-critical: FR-22 is the only
    mechanism that keeps SRS.md truthful after FR-4/FR-5 land, and rules/44 makes it append-only.

**Count: 12 architecturally significant requirements** (FR-4/FR-5 and FR-15/FR-17 each counted once
as paired items per the source tables' own grouping).

---

## 2. Settled Decisions

Record these; do not re-derive them. You may flag a consequence you believe the user did not foresee,
but the decision itself stands.

- **ADR-006 (hook-free execution).** Remove PreToolUse+PostToolUse; UserPromptSubmit off the hot path.
  State the trade-off plainly in the ADR document, not softened: **enforcement becomes opt-in**.
  Policies stop auto-applying on any session where the plugin is not invoked. This is the accepted
  consequence, not a risk to mitigate away.
- **ADR-007 (pinned build-time snapshot).** Reproducible installs; staleness check against
  `claude-global-library/VERSION`. `CLAUDE_PLUGIN_DEV_MODE=1` escape hatch for local iteration, with
  three hard guardrails: env-var-only (never a bundled config flag), every dev-mode result/log tagged
  `mode: dev`, and the release script fails the build if the flag is set in the publishing environment.
- **ADR-008 (private marketplace under techdeveloper-org).** `.claude-plugin/marketplace.json`,
  install by name, matches the existing 14-repo MCP organisation.
- **ADR-009 / ADR-009a / ADR-009b.** ADR-009 (docs/policies/ canonical) stands. ADR-009a fixes a
  four-branch resolution order in `path_resolver.py`: (1) `CLAUDE_PLUGIN_DEV_MODE=1` -> live workspace
  `docs/policies/`, (2) plugin-bundled snapshot `policies/`, (3) repo `docs/policies/` (contributor
  path), (4) hard error naming all three attempted paths -- **never** a silent fallback to
  `~/.claude/policies/`. ADR-009b resolved the merge-before-canonicalise question with a user-approved
  slate, EXECUTED EXACTLY AS FOLLOWS at canonicalisation time (a Workstream B/C task, not Phase 0):
  **PORT** `recommendations-policy.md` (hard dependency from `pr-code-review-policy.md`); **PARTIAL
  PORT as advisory** `core-skills-mandate.md` (model-tiering is orthogonal to FR-10's KG selection);
  **DELETE permanently** `auto-skill-agent-selection-policy.md`, `adaptive-skill-registry.md`,
  `auto-plan-mode-suggestion-policy.md`. The three deletions are 1,864 irrecoverable lines
  (`~/.claude/` is not under git) -- the user was shown this and chose permanent deletion; do not
  reopen it and do not silently back the files up.
- **ADR-010 (zero bundled hooks, non-negotiable).** The plugin ships NO `hooks/` directory and no
  `hooks.json`, ever, because Claude Code plugin hooks cannot be individually disabled once merged.
  The retained Stop/Notification hooks stay exactly where they are today, as user-level
  `~/.claude/settings.json` entries the plugin neither owns nor modifies.
- **Deliverable 1 (policy audit) APPROVED 2026-08-01**, with three binding resolutions: (1) CallGraph
  blindness is in-scope for the HLD -- scope-aware discovery, not a cap raise (feeds FR-9a above);
  (2) the three silently-broken maintenance policies (`session-memory`, `session-pruning`,
  `git-auto-commit` -- their `.exists()` guards at `core.py:78,106,135,159` target scripts that were
  never built) fold into FR-8a under the user's chosen approach, **"repair what it should do"**: decide
  per capability whether it is still wanted, then rebuild or formally delete the reference -- deletion
  is a valid end state, not a fallback, and this does not mandate rebuild-everything; (3) SRS.md's
  FR-9 (hook system) and v2.0.0's FR-9 (library drift) are DISAMBIGUATED and must never be conflated --
  the former is owned by business-analyst-agent + product-manager-agent at Phase 5 (append-only
  supersession per rules/44), the latter by python-backend-engineer at Workstream C.
- **FR-8a's measured basis.** 8 of 9 referenced Stop-hook scripts checked -- only `sync-version.py`
  and `voice-notifier.py` exist. The inferred per-turn spawn floor is ~2 (unconditional
  `git rev-parse` calls), refuting the docstring-derived "8, 16 with retries" figure -- but ~2 is a
  STATIC inference (file-existence check), not a runtime measurement, and FR-8a's acceptance criterion
  requires a RUNTIME-INSTRUMENTED count before any reduction work proceeds.

---

## 3. Open Architectural Questions

Only genuine unknowns. None of these restate a settled decision above.

1. **NFR-3's crash-recovery replacement design.** `post-tool-tracker.py` is confirmed the sole writer
   of checkpoint state backing "resume from any step after crash." What component owns this write once
   PostToolUse is deleted, and how does it also recover the warm-daemon NFR-1 performance path that
   rides on the same hook? Both losses are real; the HLD must name a replacement for both, not just one.
2. **Per-policy disposition for the 15 hook-coupled policies (FR-3's scope).** Only 4 of 46 policies
   SELF-DECLARE hook coupling in their own text; 11 more are hook-coupled without saying so
   (`automatic-task-breakdown`, `common-failures-prevention`, `context-management`, `context-reading`,
   `git-auto-commit`, `session-memory`, `session-pruning`, `task-phase-enforcement`,
   `task-progress-tracking`, `tool-usage-optimization`, `version-release`). For each of the 15: MCP
   tool, advisory instruction, CI gate, or delete? Not yet decided per-policy.
3. **Plugin self-root-resolution without an absolute path.** FR-14a item 2 (`CLAUDE_PLUGIN_ROOT` in a
   spawned Python process's `os.environ`) is UNVERIFIED and directly gates whether ADR-009a branch 2 is
   implementable as specified. Genuinely open until the spike runs.
4. **Whether the FR-9a CallGraph fix is scope-aware or merely a higher cap.** The user ruled it must
   NOT be a cap-raise (Resolution 1); the open design question is HOW the HLD makes silent
   package-dropping structurally impossible (not just less likely at the current file count), including
   the regression test's exact assertion surface.
5. **Plugin extraction boundary -- no clean cut exists at function-level precision.** C.1 found a
   package-level import SCC across 16 of ~23 `langgraph_engine` subpackages (~70%, giant-SCC). C.2.5
   found ZERO non-trivial function-level SCCs and 708 fragmented Louvain communities (largest 9% of
   nodes, purity 0.25-0.40). Both are correct measurements of different graphs; they do not contradict
   each other, and the package-level cyclicity is NOT proof a clean architectural cut exists at the
   granularity the plugin/library split actually needs. This is a real design constraint the HLD must
   work within, not a measurement artifact to explain away.
6. **FR-15's home-directory reference split -- UNRESOLVED, do not size on either figure.** The total
   (~116-118 references) is corroborated across sources. The live-code-vs-comment split is NOT: C.1
   (`path_violations.md`) reports 13 live-code defaults / 103 comments-or-docstrings, and this exact
   13-figure is already written into prd-v2.md's FR-15 measurable AC ("a grep for the 13 named
   `~/.claude/...` code-level string defaults... returns zero matches") -- i.e. a validated,
   gate-passed artifact has already treated 13 as fact. An independent orchestrator grep pass produced
   ~95 live / 23 comments instead. That pass was line-oriented and cannot structurally distinguish a
   docstring body from executable code, so it does NOT refute C.1's method -- but it means the split is
   unverified by any independent means, and the gap (13 vs 95 remediation sites) is large enough to
   change FR-15's job size by roughly 7x. Require an AST-based re-derivation before FR-15's scope enters
   the HLD as a sized deliverable.

---

## 4. Fixed Constraints

Python 3.10+; LangGraph 0.2.0+; FastMCP. Windows 11 / PowerShell as the primary target platform. All
path construction goes through `path_resolver.py` (`src/utils/path_resolver.py`, 23 top-level
functions, verified comprehensive, 0 absolute path literals anywhere in the repo today -- a positive
finding to preserve, not fix). ASCII-only Python source (cp1252-safe). Explicit `encoding="utf-8"` on
every text-mode `open()` call -- 19 confirmed sites currently lack it, including the mode-less
`open(path)` form. Governance: rules/11 (max 5 root docs), rules/12 (docstrings only, zero inline
narration in new/modified functions), rules/44 (SRS is append-only), rules/45 (13 UML diagram types),
rules/46 (architecture-doc update triggers). All git and GitHub operations go through the `git-ops` and
`github-api` MCP servers, never raw CLI. NFR-2 forbids any fixed per-call wall-clock timeout anywhere
on the long-running pipeline path -- this applies to whatever the HLD designs as FR-8a's retained Stop
hook and to any MCP tool handler on the pipeline path, not only to the hooks being deleted.

---

## 5. Mandatory Pre-Design Verification

**DONE -- do not redo this.** The claude-code-guide documentation verification completed 2026-08-01
and is CONFIRMED, not provisional: manifest path is `.claude-plugin/plugin.json`; `name` is the
namespace prefix for everything the plugin ships; omitting `version` under git distribution makes the
commit SHA the version, so an explicit semver `version` is mandatory (ADR-008 requires it); directory
discovery is convention-based (`skills/{name}/SKILL.md`, `agents/`, `commands/`, `hooks/hooks.json`,
`.mcp.json`, `.lsp.json`, `monitors/monitors.json`, `bin/`), flat, not nested-namespace-aware;
`.mcp.json` sits at plugin root using the same schema as user/project scope; marketplace mechanics are
`.claude-plugin/marketplace.json` at repo root with private-repo, local-path, and URL support all
confirmed viable; `${CLAUDE_PLUGIN_ROOT}` is confirmed usable in hook command paths and
`monitors.json`. Treat all of this as load-bearing input, not a question to re-ask.

**OUTSTANDING -- blocking, before the packaging section of the HLD freezes.** FR-14a's four empirical
items require a throwaway-plugin spike (owned by automation-engineer) that has not yet run:
(1) does `${CLAUDE_PLUGIN_ROOT}` resolve inside `.mcp.json` stdio `command`/`args`; (2) is
`CLAUDE_PLUGIN_ROOT` present in `os.environ` for a Python process the plugin spawns -- **this item
alone gates ADR-009a branch 2**, and a NO answer without a working fallback (a small install-time
config file `path_resolver.py` reads) puts FR-15 at risk for standalone installs; (3) exactly which
`settings.json` fields does `/plugin install` write -- needed to verify FR-18's clean uninstall claim
against a real baseline, not an assumed one; (4) what does `/plugin uninstall` leave behind, including
`~/.claude/plugins/cache/` residue and whether `/plugin prune` is needed. Any item still unresolved
after the spike is marked PROVISIONAL in the HLD with its stated fallback -- never silently assumed as
CONFIRMED. Results land in `docs/phase-1-architecture/plugin_schema_spike.md` before you freeze
Workstream D's design.

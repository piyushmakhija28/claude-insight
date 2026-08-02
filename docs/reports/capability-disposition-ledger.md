# Capability Disposition Ledger (NFR-4)

Generated 2026-08-02. One row per capability named in
`docs/phase-0-reverse-engineering/capability_loss.md`, keyed by **capability** rather than by
policy filename. Consumed by `scripts/verify_policy_capability_dispositions.py`.

## Why this document exists rather than more rows in the audit matrix

NFR-4 forbids a "disappeared" capability -- one neither preserved by a kept enforcement point nor
explicitly given up by a recorded disposition. The V2-008 gate found that 20 of the 27 capabilities
in `capability_loss.md` had no accounting anywhere.

The obvious repair -- add rows to `docs/reports/policy-implementation-audit-v2.md` -- is
**structurally impossible**. That matrix's AC1 asserts row-set identity between its Policy-file
column and the `.md` basenames in `docs/policies/`, tested as an empty symmetric difference in both
directions. A capability such as the warm daemon (`daemon.py`) or the policy dispatcher
(`registry.py`) has no policy `.md` file at all, so any row added for it fails AC1 immediately and
in both directions. The two documents are keyed differently and cannot be merged without breaking
one of them.

The project owner ruled on 2026-08-02 for a **second, capability-keyed ledger**. This is that
ledger. It does not replace the audit matrix and does not restate it.

## Relationship to the audit matrix, and the drift risk that creates

Seven of the 27 capabilities are already accounted for by an audit-matrix row whose Evidence cell
names their owner file. Those seven rows below carry a **cross-reference** to the matrix row that
owns the decision -- not a second, independently argued decision. Their Disposition cell mirrors
the matrix row's value.

**That mirroring is a real drift risk and is stated rather than hidden.** No mechanical check joins
this ledger to the matrix, so a change to one of those seven matrix rows will not automatically
surface here. Anyone editing a cross-referenced matrix row must update the mirrored value in this
ledger in the same change.

## The join, stated explicitly

No requirement document previously said how a capability corresponds to a disposition row, and that
silence had a measurable cost: a loose reading left 2 capabilities unaccounted, a strict reading left
20. The difference was not a matter of taste -- it decided whether NFR-4 was nearly satisfied or
substantially unmet. It is written here so no future maintainer has to reconstruct it.

**The join is by CAPABILITY NAME, one ledger row per `capability_loss.md` entry, matched strictly.**

- `capability_loss.md` is machine-generated and is the sole authority on what was lost. Its row set
  defines this ledger's row set exactly: the gate asserts an EMPTY SYMMETRIC DIFFERENCE in both
  directions, never a count.
- The key is the capability name, NOT the owner file. Two cross-cutting capabilities share a single
  owner file (`policy_tracking_helper.py`); an owner-file join would silently collapse them and let
  one disposition discharge both.
- STRICT, not package-level. Under a loose join, one row citing anything beneath
  `hooks/pre_tool_enforcer/` would discharge all 16 PreToolUse capabilities at once. That is exactly
  the silent discharge NFR-4 exists to prevent, which is why the strict reading was chosen even
  though it produced the larger unaccounted figure.
- A bundled entry stays ONE row. `capability_loss.md` row 6 names two capabilities in one entry, and
  the ledger carries one disposition for it, because splitting the row would fail the symmetric
  difference. The split is recorded in that row's Basis instead.

## Evidence labelling

The same three labels the audit matrix uses, with the same meanings, so both documents read alike.

| Label | Meaning |
|---|---|
| MEASURED | Checked against disk or source by this pass. Reproducible from the stated file:line. |
| CITED | From an approved artifact (ADR, HLD OAQ, audit-matrix row). Not independently re-checked here. |
| INFERRED | Derived from MEASURED or CITED inputs; the derivation is stated in the Basis cell. |

## Disposition vocabulary

`keep-as-is` / `port-to-plugin` / `port-to-MCP` / `demote-to-advisory` / `delete` -- V2-005's set,
spelled exactly as V2-005 spells it and exactly as the audit matrix spells it. No token outside
that set appears in the Disposition column. No capability below required a sixth token, so none is
proposed.

## Empty Disposition cells are deliberate, and the gate is expected to fail on them

Eight rows below carry an **empty** Disposition cell. That is not an oversight and not a gap in this
pass. A capability whose disposition no evidence on disk supports is left blank, because a non-empty
value encoding "undecided" -- `TBD`, `deferred`, `pending`, `disappeared` -- satisfies the letter of
NFR-4 while defeating exactly what NFR-4 exists to force. That trap has been sprung once in this
project and was rejected.

`scripts/verify_policy_capability_dispositions.py` AC1 is therefore **EXPECTED TO FAIL** while those
eight remain blank, and that failure is the mechanism that surfaces them for a decision. Each blank
row names, in its Basis cell, what evidence is missing and who must supply the ruling.

---

## 1. The 27-row capability disposition ledger

**Row count: 27.** Enumerated from `capability_loss.md` -- 16 PreToolUse, 9 PostToolUse, 2
cross-cutting -- not asserted independently. `capability_loss.md` is machine-generated and carries a
do-not-edit banner; it is read here and never written.

**Decided: 19 of 27** -- seven by cross-reference to an audit-matrix row, twelve decided by this
pass from evidence already on disk. Eight left blank. **Verification split: 14 MEASURED, 12 CITED,
1 INFERRED.**

Both figures were recomputed from the rows below at creation on 2026-08-02, but **no check enforces
them**, unlike the audit matrix's AC6. They are therefore dated summaries, not guarantees. The live
figures are the ones `scripts/verify_policy_capability_dispositions.py` prints: AC1's note reports
the decided/empty split and the per-disposition tally on every run. Prefer the gate output over
these two sentences whenever they disagree.

| # | Capability | Owner file | Requirement | Disposition | Basis | Verification |
|---|---|---|---|---|---|---|
| 1 | Task-breakdown-pending block (blocks Write/Edit/Bash until task list exists) | `hooks/pre_tool_enforcer/policies/task_breakdown.py` | FR-9 | demote-to-advisory | CROSS-REFERENCE, not a second decision: audit matrix rows 3 (`automatic-task-breakdown-policy.md`) and 37 (`task-phase-enforcement-policy.md`) both cite this file and own this disposition; the value here mirrors those rows and must not be edited independently of them | CITED |
| 2 | Skill/agent-selection-pending block | `hooks/pre_tool_enforcer/policies/skill_selection.py` |  FR-9 | delete | RULING (solution-architect, 2026-08-02) on a MEASURED fact, not a finding. Under v2.0.0 selection is performed by the pipeline at Step 1 (FR-10 KG selector), so on any path through the plugin selection has already happened and the gate has nothing to guard; off that path ADR-006 makes enforcement opt-in and no gate runs. OAQ 2 rows 10-12 shape: a mechanism whose function is subsumed, not a capability given up | MEASURED |
| 3 | Review-checkpoint block (blocks code-changing tools mid-review) | `hooks/pre_tool_enforcer/policies/checkpoint.py` | FR-9 | delete | RULING (solution-architect, 2026-08-02). Same structure as row 2: review is Step 5, an explicit sequenced stage, and a per-tool-call review-pending flag guards a concurrent-edit window the sequenced pipeline does not have | MEASURED |
| 4 | Context-read-gate (blocks Write/Edit/NotebookEdit/Bash until context files read) | `hooks/pre_tool_enforcer/policies/context_read.py` | FR-9 | demote-to-advisory | CROSS-REFERENCE, not a second decision: audit matrix row 10 (`context-reading-policy.md`) cites this file and owns this disposition; the value here mirrors that row and must not be edited independently of it | CITED |
| 5 | Level-1-sync-gate | `hooks/pre_tool_enforcer/policies/level1_sync.py` | FR-9 | demote-to-advisory | CROSS-REFERENCE, not a second decision: audit matrix row 9 (`context-management-policy.md`) cites this file and owns this disposition; the value here mirrors that row and must not be edited independently of it | CITED |
| 6 | Windows-only-shell-command detection + branch protection | `hooks/pre_tool_enforcer/policies/bash_commands.py` | FR-9, NFR-5 | demote-to-advisory | OWNER RULING 2026-08-02. This capability_loss.md entry BUNDLES TWO capabilities and the ledger must carry one token, because AC2 asserts a strict one-to-one correspondence with that file. solution-architect ruled the halves differently: shell detection demote-to-advisory, branch protection port-to-MCP. The owner ruled the row demote-to-advisory. SHELL DETECTION: NOT equivalent to the kept node_windows_path_check, MEASURED -- that node validates PATH LITERALS (forward slashes, drive letters), not shell commands, so it is a different subject and not merely a different trigger. The loss is real but self-correcting: a Windows-only command fails visibly and immediately. BRANCH PROTECTION IS LOST WITH NO REPLACEMENT, and this is recorded rather than softened. The ruling's stated reason was that push_gate.py already covers it; MEASURED 2026-08-02 that it does NOT -- push_gate.py's own header reads 'Pre-push gates: VERSION bump present on the branch, tracked changes committed', and its origin/main and origin/master references at :280 resolve a MERGE BASE, not a protected-branch block. `bash_commands.py:61-70` blocking `git push origin main/master` has no successor in the plugin. ADV-012's proposed git pre-push hook is the only mechanism that would restore it, and it is DESIGNED, NOT BUILT. | CITED |
| 7 | Python/Windows cp1252 Unicode-crash detection | `hooks/pre_tool_enforcer/policies/python_unicode.py` | FR-9, NFR-5 | demote-to-advisory | RULING (solution-architect, 2026-08-02). NOT equivalent to the kept Level 0 nodes, and by a wider margin than this ledger first suspected. MEASURED: `node_unicode_fix` never inspects file content at all -- it reconfigures sys.stdout/sys.stderr to UTF-8 so the pipeline's own printing does not crash, a different capability rather than an adjacent one. `node_encoding_validation` does scan content but is DETECTIVE (pipeline start, on files already written), .py-only, and itself capped at 500 files (`langgraph_engine/preflight_guard/nodes.py:40`, enforced `:53-54`). The deleted gate was PREVENTIVE, pre-write, any file type. Preventive becomes detective and scope narrows: something is genuinely lost and is recorded as such | CITED |
| 8 | Known-failure-pattern lookup (failure-kb.json) | `hooks/pre_tool_enforcer/policies/failure_kb.py` | FR-9, NFR-3 | port-to-MCP | CROSS-REFERENCE, not a second decision: audit matrix row 7 (`common-failures-prevention.md`) cites this file and owns this disposition; the value here mirrors that row and must not be edited independently of it | CITED |
| 9 | Grep content-mode head_limit enforcement | `hooks/pre_tool_enforcer/policies/grep_opt.py` | FR-9 | port-to-MCP | Audit matrix row 41 (`tool-optimization-policy.md`, port-to-MCP per OAQ 2 row 4) already names this enforcement point in its Evidence cell -- `grep_opt.py:8` `check_grep_opt`, registered `core.py:466-467` -- so the capability was accounted for all along and read as unaccounted only because that Evidence cell writes the path in shorthand rather than repository-relative form. MEASURED 2026-08-02: `check_grep_opt` is entry 10 of `core.py:453-469` `_BLOCKING_POLICIES`, the same registration row 41 cites | MEASURED |
| 10 | Read large-file offset/limit enforcement | `hooks/pre_tool_enforcer/policies/read_opt.py` | FR-9 | port-to-MCP | CROSS-REFERENCE, not a second decision: audit matrix row 41 (`tool-optimization-policy.md`) cites this file and owns this disposition; row 42 (`tool-usage-optimization-policy.md`, delete) shares the same enforcement point but is explicitly merged into row 41's disposition, so row 41 is the owning row. The value here mirrors row 41 and must not be edited independently of it | CITED |
| 11 | Write/Edit tool-optimization hints | `hooks/pre_tool_enforcer/policies/write_edit.py` | FR-9 | delete | MEASURED 2026-08-02: this capability is already a no-op today, independent of hook removal. `check_write_edit` returns `(False, "")` on every path -- `hooks/pre_tool_enforcer/policies/write_edit.py:25` and `:30`, with the module docstring at `:4` stating it never blocks -- and the function appears in no live call site: it is absent from `core.py:453-469` `_BLOCKING_POLICIES` and reached only through the backward-compat re-export at `core.py:350`. That is exactly the condition HLD SS 12 OAQ 2 rows 10-12 dispose as `delete` with a mandatory NFR-4 ledger entry, deleting an already-broken reference rather than working capability | MEASURED |
| 12 | General-purpose subagent persona gate | `hooks/pre_tool_enforcer/policies/agent_persona.py` | FR-9 | demote-to-advisory | RULING (solution-architect, 2026-08-02) on the ARCHITECTURAL HALF ONLY, and recorded as a FLOOR rather than a preference. ADR-010 forbids the plugin shipping hooks, so this gate cannot survive as a gate under any owner decision and advisory is the only surviving form. OPEN, ROUTED TO PROJECT OWNER: whether the convention persists as an instruction or is dropped entirely. The owner may downgrade this to `delete` with no architectural rework | MEASURED |
| 13 | Dynamic skill/agent context injection by file type | `hooks/pre_tool_enforcer/policies/skill_context.py` | FR-9 | demote-to-advisory | RULING (solution-architect, 2026-08-02), grounded on this row's OWN measured nature rather than by extending OAQ 2 row 2's criterion past its stated scope. MEASURED: never blocks -- invoked at `hooks/pre_tool_enforcer/core.py:497-502` outside `_BLOCKING_POLICIES`, under a comment reading 'non-blocking'. The file-type to skill mapping has standalone value and belongs in the plugin's skills/ and agent-instruction layer: the per-tool-call injection does not survive, the content does | MEASURED |
| 14 | **Version-push gate** -- blocks `git push` without a VERSION bump on the branch, and blocks push with an unclean tree (the bypass this repo's own commit history records fixing: `1bb4303 "close a bypass in the version push rule"`) | `hooks/pre_tool_enforcer/policies/push_gate.py` | FR-9, rules/44 (SRS lifecycle), rules/11 | port-to-MCP | CROSS-REFERENCE, not a second decision: audit matrix row 45 (`version-release-policy.md`) cites this file and owns this disposition, which PRD FR-23 fixes at MANDATORY rather than leaving to classification. The value here mirrors that row and must not be edited independently of it | CITED |
| 15 | Warm-daemon fast path -- keeps a long-lived process so PreToolUse checks skip cold Python-interpreter startup on every tool call | `hooks/pre_tool_enforcer/daemon.py` | NFR-1 (Performance) | delete | ADR-006 section 4.1, Consequence 3, paragraph "Warm daemon, correctly attributed", names `hooks/pre_tool_enforcer/daemon.py` by path, records that it is lost because both hooks are deleted, and states the replacement is structural rather than a port: "an MCP stdio server is already a warm, long-lived process, so the warm-path benefit returns through the MCP transport." Nothing of this module moves, so `delete` is the accurate token and `port-to-MCP` would overstate what happens. ADR-010 independently forbids the plugin shipping any `hooks/` tree at CI-CRITICAL, leaving a PreToolUse daemon no home | CITED |
| 16 | PolicyRegistry -- ordered, fail-open policy-check dispatch used by all 14 policies above | `hooks/pre_tool_enforcer/registry.py` | FR-9 (mechanism) | delete | Two independent grounds. (i) MEASURED 2026-08-02: `PolicyRegistry` is bound at `hooks/pre_tool_enforcer/core.py:162` but never instantiated anywhere under `hooks/` -- the live dispatch iterates the plain `_BLOCKING_POLICIES` list at `core.py:453-469` -- so the ledger's "used by all 14 policies above" does not describe the live path, and the class is already dead code, the condition OAQ 2 rows 10-12 dispose as `delete`. (ii) ADR-010 forbids any `hooks/` directory or `hooks.json` in the plugin tree at CI-CRITICAL, so a PreToolUse dispatcher has no home regardless. Matrix row 20 (`hook-system-policy.md`, delete) rests on the same `core.py:453-469` registration surface | MEASURED |
| 17 | Session progress/checkpoint state (progress delta dict, session file I/O) -- this is the writer behind NFR-3's "Checkpoint recovery: pipeline can resume from any step after crash" | `hooks/post_tool_tracker/progress_tracker.py` | **NFR-3 (Reliability)** | port-to-MCP | ADR-006 section 4.1, Consequence 3, names this file by path as the genuine per-tool-call loss and names its replacement: `mcp-post-tool-tracker` (`increment_progress`), called explicitly by the pipeline and required to be a projection of the checkpoint record rather than an independent second writer. ADR-011 makes `CheckpointManager` the contractual crash-recovery writer, so the part of this capability the requirement cell claims -- step-boundary resume -- was never hook-owned and is not lost; what ports is the per-tool-call progress surface | CITED |
| 18 | Tool-usage metrics tracking (per-tool counts, timing) | `hooks/post_tool_tracker/core.py` | NFR-3 | port-to-MCP | Derivation, from one MEASURED and two CITED inputs. MEASURED 2026-08-02: no `track_tool_usage` symbol exists anywhere under `hooks/`, so this row's owner cell names the replacement tool rather than a live hook symbol. CITED: ADR-006 section 4.1 Consequence 3 names `mcp-post-tool-tracker` (`increment_progress`, `track_tool_usage`) as the replacement surface; audit matrix row 27 (`metrics-monitoring-policy.md`) disposes deterministic counters port-to-MCP per OAQ 2 row 3 on the grounds that `metrics_exporter.py` and `mcp-post-tool-tracker` already provide that surface. Both inputs point at the same destination | INFERRED |
| 19 | Phase-complexity enforcement | `hooks/post_tool_tracker/policies/phase_complexity.py` | FR-9 | demote-to-advisory | MEASURED 2026-08-02: the module self-declares its owning policy in its docstring -- `Policy: task-phase-enforcement-policy.md` at `hooks/post_tool_tracker/policies/phase_complexity.py:10`, repeated at `:19`. Audit matrix row 37 disposes that policy demote-to-advisory per OAQ 2 row 13, on the grounds that phase ordering is a planning concern the pipeline already sequences and enforcing it per tool call was always the wrong altitude. Row 37's Evidence cites `task_breakdown.py` rather than this file, which is why the capability read as unaccounted; the source's own declaration supplies the missing link | MEASURED |
| 20 | Post-merge VERSION/doc sync trigger | `hooks/post_tool_tracker/policies/post_merge_update.py` | FR-9, rules/44/45/46 | port-to-MCP | MEASURED 2026-08-02: the module self-declares `Policy: version-release-policy.md` at `hooks/post_tool_tracker/policies/post_merge_update.py:5`, repeated at `:16`. Audit matrix row 45 disposes that policy port-to-MCP. PRD FR-23's MANDATORY qualifier is scoped to `push_gate.py` specifically and is not claimed for this half; what carries here is the policy-level disposition, which is the same token | MEASURED |
| 21 | Skill-selection flag clearing (Level 3.5) | `hooks/post_tool_tracker/policies/skill_selection_clear.py` | FR-9 | delete | FINDING, follows row 2 by the dependency this ledger already states: this module exists only to clear the flag row 2's gate sets, so it cannot outlive it | MEASURED |
| 22 | Task-breakdown flag clearing (Level 3.1) | `hooks/post_tool_tracker/policies/task_breakdown_clear.py` | FR-9 | port-to-MCP | Audit matrix row 38 (`task-progress-tracking-policy.md`, port-to-MCP per OAQ 2 row 14) already names this file in its Evidence cell as `.../task_breakdown_clear.py`, so the capability was accounted for all along and read as unaccounted only because that Evidence cell abbreviates the path. Row 38's own Verification is CITED and it records reach as not individually traced (LOW confidence); that caveat carries here unchanged and is not upgraded by this pass | CITED |
| 23 | Task-update-frequency warning | `hooks/post_tool_tracker/policies/task_tracking.py` | FR-9 | port-to-MCP | CROSS-REFERENCE, not a second decision: audit matrix row 38 (`task-progress-tracking-policy.md`) cites this file and owns this disposition; the value here mirrors that row and must not be edited independently of it | CITED |
| 24 | Uncommitted-push policy (Level 3.11) | `hooks/post_tool_tracker/policies/uncommitted_push.py` | FR-9 | delete | MEASURED 2026-08-02: already dead, independent of hook removal. The module header at `hooks/post_tool_tracker/policies/uncommitted_push.py:4-10` records it SUPERSEDED -- the PostToolUse hook no longer calls it, because blocking from PostToolUse cannot work when the tool has already run and the push has already reached the remote -- and states it is retained only so a legacy test re-export keeps resolving, with an explicit instruction not to wire it back. Its live replacement is `push_gate.py`, row 14 above. This is the OAQ 2 rows 10-12 condition: delete an already-broken reference, with the loss recorded here rather than dropped. Secondary note: it declares `Policy: git-workflow-policy.md`, which is absent from the 46-policy corpus | MEASURED |
| 25 | Auto-close GitHub issues on task completion | `hooks/post_tool_tracker/github_integration.py` | FR-4 (integration lifecycle) | delete | RULING (solution-architect, 2026-08-02) on this ledger's own row-24 precedent: delete a superseded mechanism and name the live replacement. Replacement is pipeline-side Step 6 closure (`langgraph_engine/sdlc_pipeline/github_lifecycle.py:543`). What is lost is only the heuristic trigger -- closing on post-tool 'task completion detection' -- which the pipeline replaces with an explicit step boundary: a better-defined trigger, not a worse one | MEASURED |
| 26 | Policy-execution recording (feeds the policy-enforcement MCP server's flow-trace aggregate) | `hooks/policy_tracking_helper.py` | NFR-3 | port-to-MCP | MEASURED 2026-08-02: the destination already exists. In the sibling `mcp-policy-enforcement` server repo (outside this repository), `server.py:278` defines `record_policy_execution` as an MCP tool, so the capability's surface is already MCP-side and what dies with the hooks is the call site, not the mechanism -- the same shape ADR-011 uses for progress, where the pipeline calls the MCP tool explicitly instead of a hook firing it. MEASURED GAP, stated rather than glossed: the owner cell also names `record_sub_operation`, and that function has no counterpart in that server; the port is therefore partial and must add it | MEASURED |
| 27 | Flow-trace summary retrieval | `hooks/policy_tracking_helper.py` | NFR-3 | port-to-MCP | MEASURED 2026-08-02: in the sibling `mcp-policy-enforcement` server repo (outside this repository), `server.py:394` already defines `get_flow_trace_summary` as an MCP tool with the same name and purpose, so this capability's destination exists today and only the hook-side caller is lost | MEASURED |

---

## 2. What is still open, and who owns it

Eight capabilities carry an empty Disposition cell. Grouped by decider, so a single ruling can close
a group rather than eight separate ones.

| Decider | Rows | What is needed |
|---|---|---|
| solution-architect (OAQ 2 extension) | 2, 3, 13 | HLD SS 12 OAQ 2 dispositioned 15 hook-coupled *policies*. These three are live hook *mechanisms* that no corpus policy claims, so OAQ 2's criteria do not reach them. Extending OAQ 2 to cover unclaimed mechanisms would close all three at once |
| solution-architect (equivalence ruling) | 6, 7 | Whether a kept Level 0 pre-flight node is accepted as covering a deleted per-tool-call block, given the two fire at different points. Row 7 needs the ruling for cp1252 detection; row 6 needs it for Windows-command detection, plus a separate disposition for the branch-protection half that no artifact addresses |
| solution-architect (corpus repair) | 25 | The module names an owning policy that does not exist in the corpus. Either the policy is missing from `docs/policies/` or the reference is stale; whichever it is, the capability cannot be routed to a matrix row until it is resolved |
| project owner | 12 | The persona gate enforces the owner's own global convention rather than a project policy, so whether it survives as a plugin agent-instruction is the owner's call |
| follows row 2 | 21 | Not a separate decision. The flag-clearing half must follow the gate it clears |

## 3. Change log

| Date | Change |
|---|---|
| 2026-08-02 | Created. 27 rows enumerated from `capability_loss.md`; 7 cross-referenced to their owning audit-matrix row, 12 decided from evidence on disk, 8 left deliberately blank with their missing evidence and decider named |

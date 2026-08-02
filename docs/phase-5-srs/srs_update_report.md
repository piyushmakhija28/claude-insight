# Phase 5 -- SRS.md Update Report (v2.0.0)

**Phase:** 5 -- SRS lifecycle append
**Author:** business-analyst-agent
**Date:** 2026-08-01
**Target file:** `SRS.md` (repository root)
**Governing rule:** `~/.claude/rules/44-srs-lifecycle.md` section 4 -- SRS is APPEND-ONLY
**Repo VERSION at time of append:** `1.21.5` (read from `VERSION`)

---

## 1. What Was Appended

Four append operations, all additive. No line that existed in `SRS.md` before this pass was edited,
reordered or deleted.

| # | Section touched | What was added |
|---|---|---|
| 1 | `### 3.1 Functional Requirements` | FR-10 through FR-37 (28 entries), appended after the FR-9 block |
| 2 | `### 3.2 Non-Functional Requirements` | NFR-7 through NFR-12 (6 entries), appended after the NFR-6 block |
| 3 | `## 4. Acceptance Criteria` | Revised `AC-9` per rules/44 section 4.2, plus a 34-row AC table for FR-10..FR-37 and NFR-7..NFR-12, appended below the existing 9-row table |
| 4 | `## 5. Out of Scope` and `## 6. Change Log` | A v2.1 deferral subsection under section 5; 4 new Change Log rows under section 6 |

**Verification that the append was non-destructive:** the pre-existing FR-1..FR-9 blocks, the
NFR-1..NFR-6 blocks, the original 9-row Acceptance Criteria table, the original Out of Scope list and
the single pre-existing Change Log row (dated 2026-07-30) are all present and unmodified.

---

## 2. FR Numbering -- Starting Number and Why

**Starting number chosen: FR-10.**

`SRS.md` before this pass contained FR-1 through FR-9 and nothing higher. Rules/44 section 4.1
mandates `FR-{next_number}`, and section 6 item 3 requires only that the new number "does not
duplicate an existing `FR-{N}` in the file". FR-10 is the next available number in this file, so
FR-10 is what was used. The block runs FR-10..FR-37 inclusive -- 28 entries, which matches the 28
requirements enumerated in section 4 below.

**NAMING COLLISION, DISCLOSED NOT WORKED AROUND.** `docs/phase-0-requirements/prd-v2.md` has its own
independent FR-1..FR-24 series. SRS FR-10..FR-37 therefore overlap numerically with PRD FR-10..FR-24
while meaning entirely different things -- for example, SRS FR-22 is the knowledge-graph-driven
selector, whereas PRD FR-22 is the SRS append itself (which became SRS FR-34). `prd-v2.md` section 2
already flagged this exact class of hazard for FR-9 ("Every reference to FR-9 in downstream artifacts
must specify which document it comes from"). The collision cannot be avoided while following rules/44
section 4.1, so it is handled three ways instead: a prominent warning block at the head of the
appended FR section, a `Source:` line on every single appended entry naming its PRD requirement
explicitly, and this report's traceability table.

**NFR numbering: NFR-7.** `SRS.md` contained NFR-1..NFR-6. The same collision applies (PRD has its
own NFR-1..NFR-5) and is handled the same way.

---

## 3. The FR-9 Acceptance Criterion Change

This was the specific assignment carried forward from Phase 0 and formally assigned by the project
owner.

### 3.1 Before -- quoted verbatim

Located at `SRS.md:206` before this pass (row in the `## 4. Acceptance Criteria` table), and still
present at that content position after it:

```
| FR-9 | All four hook events fire, and a blocking policy returns exit code 2 from the PreToolUse hook so the tool call does not proceed. |
```

The requirement it belongs to is at `SRS.md:131-136` before this pass:

```
#### FR-9: Hook System

**Description:** Pipeline must integrate with Claude Code's 4 hook types (UserPromptSubmit, PreToolUse, PostToolUse, Stop) for automated trigger and enforcement.
**Priority:** High
**Status:** Implemented
**Key Scripts:** `hooks/pre-tool-enforcer.py`, `hooks/post-tool-tracker.py`, `hooks/stop-notifier.py`, `scripts/3-level-flow.py` (UserPromptSubmit)
```

### 3.2 After -- appended, original retained

The original row was NOT deleted and NOT edited. A superseding criterion was appended in the rules/44
section 4.2 format (`**AC-{FR_number} (Updated {YYYY-MM-DD}):**`):

```
**AC-9 (Updated 2026-08-01):** From v2.0.0 onward, of the four hook events named in FR-9, exactly one
-- `Stop` -- remains registered and firing; it is engine-owned and user-level, and the plugin neither
installs nor modifies it (ADR-010). `PreToolUse` and `PostToolUse` are absent from
`~/.claude/settings.json` (FR-13), and `UserPromptSubmit` is no longer the every-prompt entry point
(FR-15). The exit-code-2 blocking guarantee that FR-9's original criterion asserted is therefore no
longer available from any hook, and is replaced by three compensating controls, all of which are
DESIGNED, NOT BUILT as of 2026-08-01: (a) the version-push gate reachable as a named MCP tool once
the user has run `register-mcp` (FR-35, FR-37); (b) ADR-017's CI-side replacement-reachability
assertion, which runs in CI rather than on the user's machine and therefore protects the shared
repository regardless of any individual user's local configuration; and (c) ADR-020's refuse-by-
default guard in `unregister-mcp` plus a start-up precondition check in every FR-17 command (NFR-12).
Enforcement is opt-in per ADR-006: no policy blocks any tool call on a session where no plugin
command is invoked. This is the accepted price of removing involuntary per-tool-call execution, not a
regression to be mitigated away.
```

A second paragraph was appended bounding the scope of the falsification precisely:

- FR-13 (PRD FR-4) deletes **2 of the 4** events outright -- `PreToolUse` and `PostToolUse`. This is
  the Phase 0 finding as stated.
- FR-15 (PRD FR-5) affects a **third**, `UserPromptSubmit`, by taking it off the every-prompt hot
  path. Whether its `settings.json` registration is deleted outright or merely repointed is **not
  specified by any artifact reviewed for this append**. That is recorded as open in the SRS rather
  than guessed, because guessing it would either overstate the falsification (3 of 4) or understate
  it (2 of 4) without evidence.
- The **fourth**, `Stop`, is unaffected and is deliberately retained (ADR-010).

---

## 4. Traceability -- PRD FR to SRS FR

28 SRS functional requirements were added. 27 map to a numbered requirement in `prd-v2.md`; 1 does
not and is labelled as such.

| PRD (`prd-v2.md`) | SRS (appended) | Short statement | Deliverable |
|---|---|---|---|
| FR-1 | FR-10 | Line-by-line read of all 46 policies with file:line evidence | D1 |
| FR-2 | FR-11 | 7-column x 46-row policy implementation matrix | D1 |
| FR-3 | FR-12 | Disposition for the 15 PreToolUse-only-enforced policies | D1 |
| FR-4 | FR-13 | Delete PreToolUse and PostToolUse registrations | D6 |
| FR-4a | FR-14 | Blast-radius measurement plus 3 named consequences | D6 |
| FR-5 | FR-15 | Remove UserPromptSubmit from the every-prompt hot path | D6 |
| FR-6 | FR-16 | File `docs/architecture/ADR-006-hook-free-execution.md` | D2 |
| FR-7 | FR-17 | Explicit slash-command entry points (6 named) | D6 |
| FR-8 | FR-18 | Keep Stop and Notification as user-level, plugin never owns | D6 |
| FR-8a | FR-19 | Stop-hook instrumentation, decision, reference retirement | D6 |
| FR-9 (library drift) | FR-20 | Reconcile master graph / README / filesystem counts | D3 |
| FR-9a | FR-21 | Coverage-complete discovery at 4 truncation sites | D4 |
| FR-10 | FR-22 | KG-driven selection, zero hardcoded name literals | D4 |
| FR-11 | FR-23 | Selection explainability (5 emitted fields) | D4 |
| FR-12 | FR-24 | No-match / low-confidence fallback path | D4 |
| FR-13 | FR-25 | Model fallback protocol conformance | D4 |
| FR-14 | FR-26 | Installable plugin manifest (two-step for MCP) | D5 |
| FR-14a | FR-27 | Plugin schema spike -- COMPLETE | D5 |
| FR-15 | FR-28 | Zero CODE-classified home-directory defaults | D5 |
| FR-16 | FR-29 | Pinned build-time snapshot, not duplication | D5 |
| FR-17 | FR-30 | Explicit `encoding=` at every text-mode `open()` | D5 |
| FR-18 | FR-31 | Zero plugin-attributable functional residue on uninstall | D5 |
| **FR-19** | **NOT CARRIED** | Four-branch `get_policies_dir()` resolver | -- (v2.1) |
| FR-20 | FR-32 | Dispositions for the 14 genuine policy orphans | D1 |
| FR-21 | FR-33 | Fix-or-retire the 7 dead Stop-hook script references | D6 |
| FR-22 | FR-34 | This SRS append itself | D6 |
| FR-23 | FR-35 | Port the version-push gate to MCP before deleting PreToolUse | D6 |
| FR-24 | FR-36 | Uninstall-residue runbook | D5 |
| *(none)* | FR-37 | `register-mcp` / `unregister-mcp` command pair | D5 |
| **FR-9b** | **FR-38** | **Call-graph resolution correctness -- no arbitrary bare-name bind; confidence reported alongside raw fan-in** | **D4** |

**Count reconciliation (updated for the Phase 5 follow-up).** `prd-v2.md` now defines 29 distinct FR
identifiers: FR-1..FR-18 (18) plus the five carried-forward or newly-minted variants FR-4a, FR-8a,
FR-9a, **FR-9b**, FR-14a (5) plus FR-19..FR-24 (6). 18 + 5 + 6 = 29. Of those, 28 were carried into
the SRS and 1 (FR-19) was not. 28 carried + 1 non-PRD entry (FR-37) = 29 appended SRS FRs, FR-10
through FR-38 inclusive (38 - 10 + 1 = 29). The three counts agree.

*(Superseded, retained for traceability: before the FR-9b follow-up this section read 28 PRD
identifiers, 27 carried, 28 SRS FRs FR-10..FR-37.)*

### 4.1 NFR traceability

| PRD | SRS (appended) | Short statement |
|---|---|---|
| NFR-1 | NFR-7 | Zero plugin-attributable processes in an idle session |
| NFR-2 | NFR-8 | No unconditional fixed wall-clock timeout on the pipeline path |
| NFR-3 | NFR-9 | Crash-recovery durability; 3 named defects in the existing writer |
| NFR-4 | NFR-10 | Decided disposition for all 25 lost capabilities |
| NFR-5 | NFR-11 | Install / invoke / uninstall each independently tested |
| *(none)* | NFR-12 | ADR-020 push-gate precondition control (prevent / detect / prevent-harm) |

6 NFRs appended. 5 map to a PRD NFR; NFR-12 does not -- it comes from `hld_v2.md` ADR-020, which
post-dates `prd-v2.md`, and is carried because it is the security control that FR-13's hook deletion
makes necessary. This satisfies the task's requirement for NFR coverage of the security/governance
items, specifically the ADR-020 push-gate control.

---

## 5. Change Log Rows Added

**4 rows appended**, plus the pre-existing 2026-07-30 row retained. Enumerated:

1. `2026-08-01 | 1.21.5 | v2.0.0 requirement append -- functional requirements` -- FR-10..FR-37.
2. `2026-08-01 | 1.21.5 | v2.0.0 requirement append -- non-functional requirements` -- NFR-7..NFR-12.
3. `2026-08-01 | 1.21.5 | Supersede SRS FR-9's four-hook-event acceptance criterion` -- the revised
   AC-9, plus the appended AC table and the v2.1 deferral subsection.
4. `PENDING | 2.0.0 | FR-34 completion row (NOT YET ADDED)` -- status `OUTSTANDING`.

Row 4 needs explaining because it is deliberately undated. PRD FR-22's own acceptance criterion
requires "a new row dated to the PR that deletes PreToolUse/PostToolUse, referencing this FR by
number". **That PR does not exist as of 2026-08-01.** The row was therefore recorded as an explicit
outstanding obligation rather than back-dated to today (which would be false) or omitted (which would
lose the obligation). SRS FR-34's own status line states the same thing: this append satisfies the
first clause of its AC and not the second.

**Version field.** Rules/44 section 4.3 specifies `{current_version}`. The rows use `1.21.5`, read
from the repo's `VERSION` file, not `2.0.0` -- the version bump is deliverable D7 and has not
happened. Note in passing: `VERSION` reads `1.21.5` while `CLAUDE.md`'s header table and both
`prd-v2.md` and `product-sequencing-v2.md` state the current version as `1.21.4`. That discrepancy is
pre-existing, is outside this task's scope to fix, and is flagged here rather than silently absorbed.

---

## 6. What in `prd-v2.md` Was NOT Carried Over, and Why

### 6.1 PRD FR-19 -- the only requirement deliberately dropped

`prd-v2.md` FR-19 (implement the four-branch `get_policies_dir()` resolution order) has **no SRS FR
number** in this append. Reason: `product-sequencing-v2.md` section 4 places it in "Defers to v2.1".
It is blocked on the ADR-009b five-policy human sign-off, which has no target date; it has zero effect
on NFR-7 (the project's primary success metric) and no D1-D7 gate depends on it. Assigning it an SRS
FR number in a v2.0.0 requirement block would assert it as v2.0.0 scope, which is false. It is instead
recorded by name in the appended v2.1 deferral subsection under section 5, so it is not lost.

### 6.2 Content classes not carried, by design

| Not carried | Why |
|---|---|
| `prd-v2.md` sections 2 and 3 verdict columns ("AGREE", "REVISED", Appendix E reconciliation) | Reconciliation history between two Phase 0 artifacts. The SRS records the requirement and its criterion, not the audit trail of how two prior documents were made to agree. |
| The withdrawn/struck-through FR-15 wording (the disputed 13-site figure) | It is explicitly WITHDRAWN in the source. Carrying a withdrawn AC into the SRS would reintroduce a figure `hld_v2.md` OAQ 6 ruled UNRESOLVED. The replacement AST-classifier method was carried instead, with no count asserted. |
| `prd-v2.md` section 7 Gherkin scenarios | Test-level specification. The SRS carries the acceptance criterion; the Gherkin is the executable expression of it and belongs with the test suite. |
| `prd-v2.md` section 8, the five-policy merge content review | A one-time content decision awaiting human sign-off, explicitly not an FR in its own source ("intentionally NOT an FR"). Its downstream gate, FR-19, is recorded in the v2.1 deferral list. |
| `prd-v2.md` sections 10 and 11 (Appendix F open questions, risks and assumptions) | Open questions and risk register. Neither is a requirement. F.2 and F.3 explicitly "do not bear directly on the v2.0.0 FR/NFR set". |
| `prd-v2.md` sections 12, 13, 14 (coverage statement, its own change log, return value summary) | Metadata about that document, not requirements of this system. |
| AC-1..AC-7, the original broad acceptance criteria | Superseded in practice by the per-FR measurable ACs in `prd-v2.md` section 5, which is what was carried. Carrying both would create two criteria per requirement and invite them to drift apart. |
| The `register-mcp` sizing figures (size 5, WSJF 3.80) | Prioritisation data, not requirement content. The capability itself was carried as SRS FR-37. |
| The fifth discovery truncator at `build_dependency_resolver/parsers.py:682` | Explicitly ruled a different defect class and deferred to v2.1 by `hld_v2.md` OAQ 4. Recorded by name in the v2.1 deferral subsection so its exclusion reads as deliberate. |

---

## 7. Accuracy Discipline Applied

### 7.1 Designed-versus-built labelling

Every appended entry carries an explicit `Status:` line. 27 of the 28 FRs and all 6 NFRs are labelled
**DESIGNED, NOT BUILT as of 2026-08-01**, in those words. The single exception is SRS FR-27 (the
plugin schema spike), whose artifact exists.

The ADR-020 push-gate controls named in the task brief are labelled accordingly and individually:
`register-mcp` refuse-by-default guard, the `doctor` command, the per-command start-up check, and
ADR-017's CI assertion are each recorded as designed with zero lines of code. SRS FR-37's status line
says so verbatim ("zero lines of code exist"), and NFR-12 states "NONE of the three currently exists
as code".

### 7.2 Existence checks performed on 2026-08-01

Run against the working tree before writing the append:

| Path | Result |
|---|---|
| `VERSION` | EXISTS, contains `1.21.5` |
| `docs/phase-1-architecture/plugin_schema_spike.md` | EXISTS (basis for FR-27's COMPLETE status) |
| `hooks/pre_tool_enforcer/policies/push_gate.py` | EXISTS (basis for FR-35's claim) |
| `hooks/stop_notifier/core.py` | EXISTS (basis for FR-33's claim) |
| `tests/test_push_gate.py` | EXISTS (basis for FR-35's AC) |
| `docs/reports/policy-implementation-audit-v2.md` | ABSENT |
| `docs/architecture/ADR-006-hook-free-execution.md` | ABSENT |
| `.claude-plugin/plugin.json` | ABSENT |
| `.mcp.json` | ABSENT |
| `docs/guides/uninstall-residue.md` | ABSENT |
| `commands/` | ABSENT |

### 7.3 Encoding

The appended content is ASCII-only. A full-file scan found 8 non-ASCII lines in `SRS.md`, all of them
pre-existing (lines 13, 36, 84, 126, 765, 766, 767, 833 in the post-append file) and none inside any
appended range. Append-only editing means none of them was introduced or touched here.

---

## 8. Explicit Statement of What Was NOT Verified

Stated plainly so no reader treats this append as an independent audit. It is not one.

1. **No source-code line reference in the appended content was independently re-verified.** Every
   `file:line` citation inside the appended FR/NFR entries -- the four discovery truncation sites in
   FR-21, the 6 application plus 3 definition timeout sites in NFR-8, `step_decorator.py:169` in
   NFR-9 -- is **quoted from `hld_v2.md`**, and each entry says so on its own status line. Files were
   confirmed to exist; the specific lines and their contents were not re-opened. If `hld_v2.md` is
   wrong about any of them, this SRS append reproduces that error.

2. **Counts quoted from source documents were not re-derived.** Specifically: 46 policies, 15
   PreToolUse-only-enforced policies, 14 genuine policy orphans, 25 lost capabilities, 19 `open()`
   sites, 7 of 9 dead Stop-hook script references, 135 of 2,218 nodes at 6.09 percent, and the 5
   plugin-schema spike items. These are carried as they were written. The one count this report
   derives itself is the 28/27/1 FR reconciliation in section 4, which is checked three ways.

3. **The `~/.claude/settings.json` hook table was not read live.** No assertion in this append about
   which hook events are currently registered rests on a fresh reading of that file. `prd-v2.md`
   section 11 records the same limitation for itself.

4. **`UserPromptSubmit`'s exact post-v2.0.0 end state is unknown and is recorded as unknown.** No
   artifact reviewed here states whether FR-15 deletes the registration or repoints it. The appended
   AC-9 says so rather than resolving it.

5. **The `/plugin uninstall` behaviour toward `register-mcp`-written entries is INFERRED, not
   measured, and the SRS records it as such.** It could not have been measured, because
   `register-mcp` does not exist. NFR-12 carries the verification task and states the consequence if
   the inference is wrong: that path would have no available control at all.

6. **Only the sections listed below were read.** `prd-v2.md` was read in full (502 lines).
   `product-sequencing-v2.md` was read at its section headings plus sections 0, 0a, 1, 2, 2d, 3, 4
   and 5; sections 2a, 2b, 2c, 6, 7 and 8 were located by heading but not read in full.
   `hld_v2.md` was read at its section headings plus sections 4.1, ADR-019, ADR-020 and section 10;
   sections 5, 6, 7, 8, 9, 11, 12 and 13 were not read. `docs/phase-1-architecture/hld.md`
   (ADR-006..ADR-018) was **not opened at all** -- the ADR-006..ADR-018 content used here came from
   `hld_v2.md` section 4.1, which restates the settled ADRs. `plugin_schema_spike.md` was confirmed
   to exist but was not read; every claim attributed to it is second-hand via `prd-v2.md` and
   `hld_v2.md`.

7. **No test was run and no code was executed** beyond filesystem existence checks and a non-ASCII
   character scan of `SRS.md`.

8. **The task brief's description of the source set was inaccurate and is corrected rather than
   silently followed.** The brief describes `prd-v2.md` as containing "FR-1..FR-26". It does not.
   A grep for `FR-25` and `FR-26` in that file returns zero matches. The actual identifier set is
   FR-1..FR-18 plus FR-4a/FR-8a/FR-9a/FR-14a plus FR-19..FR-24, which is 28 identifiers, not 26. The
   append was built against the actual set.

---

## 8a. Phase 5 Follow-Up -- FR-9b / SRS FR-38 and Two Corrections

### 8a.1 What was added

| File | Change |
|---|---|
| `docs/phase-0-requirements/prd-v2.md` | New **FR-9b** row in section 4; measurable AC row in section 5; RTM row in section 6; change-log row (v1.3) in section 13 |
| `SRS.md` | New **FR-38** appended after FR-37; its AC appended to the v2.0.0 AC table; 2 change-log rows |

**SRS number assigned: FR-38** -- the next free number after FR-37, which this pass established as
the end of the appended range.

**Why FR-9b and not FR-25.** FR-25 is already claimed by a proposed CI check in
`docs/phase-2-validation/advisory_items.json`; reusing it would create precisely the ID collision
that `prd-v2.md`'s own FR-9 collision warning exists to prevent. FR-9b is also the semantically
correct slot: FR-9a is call-graph **discovery** blindness (which files are seen), FR-9b is call-graph
**resolution** incorrectness (what an edge points at once a file is seen).

### 8a.2 Verification performed before writing -- every claim checked against source

| Claim to verify | Result |
|---|---|
| `_resolve_target()` exists with a `candidates[0]` fallback | **CONFIRMED. `langgraph_engine/parsers/graph_model.py:265`** -- returns `candidates[0]` for a bare simple name matching multiple FQNs with no same-file candidate. Method defined at `:225`. The `len(candidates) == 1` branches at `:253-254` and `:263-264` are legitimate; the dotted path at `:243-255` correctly returns unresolved when ambiguous. The defect is `:265` alone. |
| `call_graph_analyzer.py:56-65` thresholds; risk is caller-count-only | **CONFIRMED, with a precision correction.** `_classify_risk` spans `:56-67` (not `:56-65`), thresholds low 0-2 / medium 3-7 / high 8+, caller count is its only input. Correction: that 8+ threshold sets the per-method `risk` label (`:292`) and the overall verdict; `danger_zones` (`:303`) and `hot_nodes` (`:1197`) use a **separate `n >= 5` gate**. Both are caller-count-only -- the load-bearing point holds -- but they are not the same threshold, and the requirement says so rather than repeating the conflation. |
| Analyzer uses `graph.get_edges()` at 155, 455, 600 | **CONFIRMED**, plus a fourth consumer at `:1209` that the brief did not list. `get_edges()` (`graph_model.py:282-286`) returns `_resolved_edges` when populated, else raw `self.edges`. |
| The collided edges actually reach the pipeline | **CONFIRMED, and this was the load-bearing check.** `resolve_edges()` is invoked at `langgraph_engine/parsers/call_graph_builder_legacy.py:96` on every build, so `_resolved_edges` is populated and `get_edges()` returns the collided resolution. Had `resolve_edges()` never been called, the defect would not reach shipping code and the requirement would have been unwarranted. |
| Injection into the planning prompt | **CONFIRMED.** `prompt_gen_expert_caller.py:179-182` reads `risk_level`, `danger_zones`, `affected_methods`, `hot_nodes`; substitutes at `:204-207`. Note the prompt is the **Step 1** orchestration template consuming **Step 0**'s call-graph output; the requirement states it that way. |
| Collision target classes are real | **CONFIRMED.** `JsonlAppender.append` (`src/mcp/base/persistence.py:222`, class at `:185`), `ErrorMessages.format` (`langgraph_engine/error_messages.py:568`, class at `:561`), `_MemoryLayer.get`/`.set` (`langgraph_engine/cache_system.py:101` / `:113`, class at `:92`). |
| Edge-count arithmetic | **CHECKED HERE.** 18,608 + 2,853 + 433 = 21,894; 26,114 - 21,894 = 4,220. The enumeration reconciles to the stated total exactly. The underlying measurements were **not** re-run. |
| `resolve_edges()` / `graph.edges` divergence | **CONFIRMED as a separate issue and recorded as such.** `resolve_edges()` writes `self._resolved_edges` at `:222` and never back to `graph.edges`. This does **NOT** affect shipping code, because the analyzer reads `get_edges()`. It is named in both documents only as a consumer trap, explicitly marked as not affecting shipping code, and explicitly not conflated with FR-38. |

### 8a.3 Correction 1 -- the `config.py` truncation-site citation

**One line of my own appended content needed it: `SRS.md:260`**, the FR-21 status line, which named
`langgraph_engine/parsers/config.py:11` as the first of four truncation sites.

VERIFIED: `parsers/config.py:11` does define `MAX_FILES = 300`, but it is dead code. Its only
importer is `langgraph_engine/parsers/__init__.py:22`, which re-exports it (and lists it in `__all__`
at `:131`). No consumer reads it. The binding cap is
`langgraph_engine/parsers/call_graph_builder_legacy.py:64`, defaulted into `CallGraphBuilder.__init__`
at `:76`, stored at `:79`, and **enforced at `:107` and `:118`**. A fix applied to `config.py` would
change nothing.

The FR-21 status line now names the binding site first, retains `config.py:11` explicitly relabelled
as a dead-code cleanup item rather than a functional truncator, and adds the enforcement lines for
sites 2 and 3 (`code_graph_analyzer.py:154`/`:169`, `code-graph-analyzer.py:137`/`:152`), both
confirmed present.

**Method note, flagged as a judgment call rather than buried.** This was an **in-place edit**, not an
append, which sits in tension with rules/44's append-only rule. It was confined strictly to text this
same pass appended earlier the same day, in an uncommitted working tree (`git status` shows `SRS.md`
as modified, not committed); no content predating 2026-08-01 was touched. A dedicated change-log row
discloses exactly what changed and why, so the audit trail is preserved. The alternative -- appending
a correction note and leaving the wrong citation intact in FR-21's body -- was rejected because this
citation has already propagated to 19 files and leaving a 20th live copy would be the more harmful
outcome. If the project owner prefers strict append-only even for same-pass content, this is the one
edit to revert.

**Not fixed, as instructed: the other 18 files.** They are reported, not touched, and remain unowned.

### 8a.4 Correction 2 -- the four-language claim

**Zero lines of my own appended content needed this correction.** A grep for `4 languages`, `Java`,
`TypeScript` and `Kotlin` across `SRS.md` returns 5 hits, and **all 5 are pre-existing**, outside
every range this pass appended:

| Line | Content | Status |
|---|---|---|
| `SRS.md:37` | Scope "Included": AST-based call graph analysis (Python/Java/TypeScript/Kotlin) | Pre-existing -- NOT edited (rules/44) |
| `SRS.md:77` | FR-3 description: "supporting Python (AST), Java, TypeScript, Kotlin (regex)" | Pre-existing -- NOT edited |
| `SRS.md:583` | FR-3's acceptance criterion: "resolves classes and methods for Python, Java, TypeScript and Kotlin sources" | Pre-existing -- NOT edited |
| `SRS.md:786` | Implementation Status checklist: "AST call graph analysis (4 languages)" | Pre-existing -- NOT edited |
| `SRS.md:863` | Risks table: "MAX_FILES=300, MAX_FILE_SIZE_KB=100 in `parsers/config.py`" | Pre-existing -- carries the SAME dead-code citation as correction 1, NOT edited |

MEASURED 2026-08-01, excluding `.venv/`, `.git/` and `node_modules/`: **411 `.py` files; 0 `.java`,
0 `.ts`, 0 `.tsx`, 0 `.kt`.** `parsers/config.py:17` declares all five extensions in
`SUPPORTED_EXTENSIONS`, so the four-language claim describes a declared *capability*, not a measured
*corpus*. The measurement was recorded as a scope note inside FR-21's status line -- which is my own
appended content and therefore editable -- rather than by touching any of the five pre-existing lines.

**What I could NOT verify on this point:** the claim that zero such files existed in the 2026-03 tree
from which the published figures came. I verified the current working tree only. I did not check out
or inspect any historical revision.

### 8a.5 What I could not verify on the FR-9b defect

1. **None of the runtime edge counts was re-derived.** 1592, 755-756, 55.5 percent, 26,114, 18,608,
   2,853, 433, 4,220 are all MEASURED BY TWO OTHER AGENTS and are labelled as such in both documents.
   I verified the code paths that make those numbers *possible* and I checked the arithmetic; I did
   not run the builder.
2. **The 755 versus 756 discrepancy is unresolved and recorded as a range.** Two agents measured
   different values one edge apart. I did not adjudicate it and did not silently pick one.
3. **No post-fix collision rate exists**, so the AC deliberately asserts that the rate is REPORTED
   rather than that it must reach any particular number. Pre-committing a target would be fabrication.
4. **Which 300 of the 411 `.py` files the builder actually reaches is glob-order dependent** and was
   not determined. The in-degree figures are therefore a property of one particular truncated build,
   and would change once FR-21 lands -- which is precisely the FR-21/FR-38 interaction the
   requirement states.
5. **`hld_v2.md` OAQ 4 has not been corrected.** It is the origin of the `config.py` citation that
   propagated to 19 files. Correcting it was out of scope for this pass and is unowned.

---

## 8b. Phase 6 Follow-Up -- FR-9a / SRS FR-21 Acceptance Criterion Corrected and Strengthened

Owner ruling, 2026-08-01. Defect found by the Phase 6 scrum-master agent. Three files touched.

### 8b.1 What was wrong

FR-9a's acceptance criterion asserted on FOUR truncation sites, of which one
(`langgraph_engine/parsers/config.py:11`) is dead code read by nothing, and it OMITTED
`langgraph_engine/parsers/graph_model.py:43` entirely -- a cap that BINDS and that survives any fix
to the file cap. An implementer working strictly to that AC would have fixed four sites, one of them
dead, watched every assertion pass, and left a binding truncation in production. The AC also
asserted on *end states of constants*, and constant-inspection is the exact failure mode that
produced the defect: reading `config.py:11` and concluding the cap had been found is what 19 files
across every phase did.

The coordinator corrected FR-9a's DESCRIPTION column earlier the same day but not its AC. This pass
closes that.

### 8b.2 Verification performed before writing

| Claim | Result |
|---|---|
| `graph_model.py:43` is `DEFAULT_MAX_PATHS = _env_int("CLAUDE_CG_MAX_PATHS", 500)` | **CONFIRMED**, exact text. Applied at `:320-321`, enforced at `:354`, `:357`, `:388`; warning emitted at `:390-392`. |
| The truncation warning string | **CONFIRMED** at `graph_model.py:390-391`: `"compute_call_paths: hit max_paths=%d limit; results truncated. Increase via CLAUDE_CG_MAX_PATHS env var or pass max_paths kwarg."` |
| `call_graph_builder_legacy.py:64` binds | **CONFIRMED.** `MAX_FILES = 300`, defaulted into `__init__` at `:76`, stored at `:79`, enforced at `:107` and `:118`. |
| `config.py:11` is dead | **CONFIRMED.** Only importer is `parsers/__init__.py:22`, which re-exports it. |
| 17 sites total, 2 binding | **CONFIRMED against `callgraph_coverage_probe.md`, and the enumeration reconciles:** 4 file-count + 4 file-size + 2 traversal + 2 different-class + 5 diagram = 17. Binding = FC-2 and GT-2 = 2. Non-binding = 1 dead + 1 dormant + 1 live-but-above-corpus + 4 file-size + 1 non-binding traversal + 2 different-class + 5 diagram = 15. 15 + 2 = 17. |
| Post-fix runtime figures | **CONFIRMED as MEASURED-RUNTIME in the probe:** 411 files / 480 classes / 3,506 methods (also 1,340 functions, 26,114 call edges, 7,004 resolved), against truncated 300 / 449 / 2,844. |
| `sdlc_pipeline` canary | **CONFIRMED:** 45 files, 0 of 45 analysed today; first `sdlc_pipeline` file at discovery index 304, so the 300-file budget is exhausted five files before the tree begins. |
| max_paths fired even with the file cap lifted | **CONFIRMED** -- the probe records the warning emitted verbatim on BOTH runs. This is why assertion (C) is load-bearing. |
| The def-time binding trap | **CONFIRMED, and folded into the AC as assertion (E).** The probe measured that rebinding the module global `MAX_FILES` is a silent no-op (still 300), while the constructor kwarg and `__init__.__defaults__` patching both reach 411. |

### 8b.3 The design choice I made, and why

The ruling said to ground the assertions in the measured figures. I did **not** translate that into
hardcoded equality assertions (`files_analyzed == 411`), because a legitimately added source file
would then fail the suite and the natural fix would be to bump the number -- reintroducing a
maintained constant into the thing that is supposed to prove constants are gone. Instead:

- **(A)** and **(B)** assert **set equality / empty symmetric difference** against an independent
  enumeration oracle. Exact, growth-safe, and no magic number.
- **(D)** uses the measured figures as a **floor** (`>= 411`, `>= 480`, `>= 3506`), so growth passes
  and any regression toward the truncated 300 / 449 / 2,844 fails. The exact 2026-08-01 values are
  recorded in the test as the documented baseline.

This is a deviation in form from "assert the measured figures" and is flagged as such rather than
applied silently. If the owner wants literal equality assertions, (D) is the one clause to change.

### 8b.4 Original criterion retained -- confirmation

- **`prd-v2.md`:** the superseding row was **inserted above** the original FR-9a AC row. The
  original row's **acceptance-criterion cell (column 2) is byte-identical and untouched**. Only its
  row-label cell (column 1) gained a supersession marker, so a reader cannot encounter the old
  criterion without also seeing its disposition. Stated precisely because "verbatim" was a
  requirement: the AC text is verbatim; the label is not.
- **`SRS.md`:** append-only was honoured strictly. The `| FR-21 |` row in the acceptance-criteria
  table is untouched -- verified present exactly once by grep after the edit. The revised criterion
  was appended as a new "Revised Acceptance Criterion for FR-21" block using the rules/44 section 4.2
  `**AC-21 (Updated 2026-08-01):**` form, matching how AC-9 was handled.
- **`github_issues.json`:** the four superseded AC strings are retained verbatim as the last four
  entries of V2-009's `acceptance_criteria` array, each prefixed `SUPERSEDED AC, RETAINED VERBATIM`.

### 8b.5 V2-009 change, and proof nothing else moved

Changed fields on V2-009 only: `acceptance_criteria` (4 items -> 14), `acceptance_criteria_source`,
and the closing paragraph of `body` (the "OWNER DECISION REQUIRED" block, which is
acceptance-criteria content) rewritten to "OWNER DECISION TAKEN 2026-08-01".

Machine-verified after the write:

| Check | Result |
|---|---|
| Issue count | 37, unchanged |
| Key order | preserved exactly |
| `meta` block | unchanged (hash match) |
| Issues whose content changed | `['V2-009']` -- exactly one |
| V2-009 `size` / `size_provenance` / `wsjf_as_published` | 5 / SOURCED / 4.6 -- **untouched** |
| V2-009 `blocked_by` / `labels` / `implements` / `gate` / `batch` / `title` | untouched |
| Dangling `blocked_by` references across all 37 | none |
| Non-ASCII characters in file | 0 |

Dependency closure and acyclicity are therefore undisturbed: no `blocked_by` array on any issue was
read, written, or reordered.

### 8b.6 Judgement on the 5-point size -- FLAGGED, NOT APPLIED

**My judgement: 5 no longer holds.** It was estimated against a two-site constant-change assumption
-- edit two numbers, retire two dead sites. The strengthened AC adds four things that are
verification engineering rather than constant edits: a runtime probe harness that builds in-process,
an independent file-enumeration oracle (which must replicate the builder's own eligibility rules
without importing them, or the test proves nothing), log capture wired to a specific module logger,
and a negative test asserting that the def-time binding trap cannot be used to fake a pass. Assertion
(E) in particular is a test that must demonstrate a *failure mode*, which is strictly more work than
asserting a success.

I have **not** re-pointed it. `size`, `size_provenance` and `wsjf_as_published` are untouched in the
JSON, and the flag is recorded in three places (the PRD AC, the SRS AC, and V2-009's own AC array) so
it cannot be missed. Re-sizing is product-manager-agent's call, consistent with how FR-15 was left
unsized.

### 8b.7 What I could not verify on this correction

1. **I did not re-run the probe.** Every runtime figure (411 / 480 / 3,506 / 1,340 / 26,114 / 7,004,
   the truncated 300 / 449 / 2,844, discovery index 304, depths 11 and 7) is read from
   `docs/phase-5-uml/callgraph_coverage_probe.md` and labelled MEASURED-RUNTIME there. I verified the
   code paths that produce them and re-verified both binding sites on disk; I did not execute a build.
2. **The 17-site enumeration is the probe's, not mine.** I checked that its parts sum to 17 and that
   the binding/non-binding split is internally consistent. I did not independently re-grep the repo
   for a possible 18th site.
3. **`hld_v2.md` still carries the superseded four-site framing** in ADR-013's body and its binding
   clause, per V2-009's own propagation-hazard note. Correcting `hld_v2.md` was not in scope for this
   pass and remains unowned.
4. **I did not verify that `test_discovery_covers_every_package` exists.** The superseded AC names it
   and the new AC assumes it is the test to extend. If it does not exist, the AC describes a test to
   be written, not extended -- which would push the size estimate further.
5. **JSON reformatting.** The file was rewritten with `json.dumps(indent=2)`. Object-level hashing
   confirms all 36 other issues and `meta` are semantically identical, and the original file already
   used 2-space indentation, but I did not perform a byte-level diff of the unchanged regions.

---

## 8c. Phase 8 Follow-Up -- V2-004 / PRD FR-1 / SRS FR-10 Acceptance Criterion Re-Scoped

Owner ruling, 2026-08-02. AC3 was unsatisfiable as written. Three files touched.

### 8c.1 The unsatisfiability, MEASURED

| Quantity | Value | Method |
|---|---|---|
| `docs/policies/*.md` | **46** | Direct enumeration, 2026-08-02 |
| `~/.claude/policies/**/*.md` files | **44** across 4 subdirectories (`01-sync-system` 11, `02-standards-system` 3, `03-execution-system` 28, `testing` 2) | Direct enumeration |
| `~/.claude/policies/` distinct basenames | **35** (so 9 basenames are duplicated across subdirectories) | Direct enumeration |
| Basename overlap | **28** | Set intersection |
| In `docs/policies/`, absent from `~/.claude/` | **18** | Set difference |
| In `~/.claude/`, absent from `docs/policies/` | **7** (`README.md` plus the six ADR-009b files) | Set difference |

46 - 28 = 18; 28 + 18 = 46. AC1's 46 rows and AC3's line-by-line read of a tree missing 18 of them
cannot both be satisfied.

**Corroboration:** the 7 home-only names are exactly `README.md` plus the six files ADR-009b already
identified as existing only in `~/.claude/policies/` (`recommendations-policy.md`,
`auto-skill-agent-selection-policy.md`, `core-skills-mandate.md`, `adaptive-skill-registry.md`,
`auto-plan-mode-suggestion-policy.md`, `github-branch-pr-policy.md`). Two independently derived
findings agree.

**Figure correction to the ruling as received.** The `~/.claude/` tree was described as holding 32
policy documents. It holds 44 files resolving to 35 distinct basenames. **The load-bearing conclusion
is unaffected** -- the 18-absent finding derives from the 28-basename overlap and holds at any tree
size -- but the number is corrected rather than repeated.

### 8c.2 Authoritative tree and the runtime resolver -- stated, not assumed

`docs/policies/` (46 files, in-repo, version-controlled) is authoritative per ADR-009 and is what the
46 rows count. `~/.claude/policies/` is a partial mirror and is not the audit's corpus.

`get_policies_dir()` (`src/utils/path_resolver.py:255-261`, module wrapper at `:389-395`) returns
`{CLAUDE_HOME}/policies`, overridable by `CLAUDE_POLICIES_DIR`. **Executed on 2026-08-02, it resolves
to `~/.claude/policies` -- the partial mirror -- not to `docs/policies/`.** The ADR-009a four-branch
resolver that would make `docs/policies/` canonical is PRD FR-19, deferred to v2.1. The re-scoped AC
therefore does not depend on the runtime resolver at all, and says so explicitly in all three files:
an implementer must not use `get_policies_dir()` to enumerate the corpus for this issue.

### 8c.3 Vocabulary choice

The ruling proposed `MEASURED | CITED | NOT-VERIFIED`. The audit document already publishes its own
closed vocabulary at `docs/reports/policy-implementation-audit-v2.md:22-25`:
**`MEASURED` / `CITED` / `INFERRED`**. I used the document's existing vocabulary rather than
introducing a fourth value that would have to be reconciled later. `NOT-VERIFIED` is expressible as
`CITED` (taken from a source artifact, not independently re-checked), which is precisely what the 41
unverified classifications are. Flagged as a deviation in form, not in intent.

### 8c.4 Original criteria retained -- confirmation

- **`prd-v2.md`:** superseding row inserted **above** the original FR-1 AC row. The original row's
  criterion cell is byte-identical -- verified by string match after the edit. Only its label cell
  gained a supersession marker.
- **`SRS.md`:** append-only honoured. The `| FR-10 |` acceptance-criteria row is untouched, verified
  present by string match. FR-10's requirement statement in section 3.1 also keeps its
  now-superseded "line-by-line" wording, with a note beneath recording that it is no longer the
  standard of done. The revised criterion was appended as `**AC-10 (Updated 2026-08-02):**` per
  rules/44 section 4.2 -- the same form used for AC-9 and AC-21, both of which remain present.
- **`github_issues.json`:** all three original criteria retained verbatim as the last three entries
  of V2-004's `acceptance_criteria`, each labelled, with AC3 additionally marked
  "NO LONGER IN FORCE" and carrying its retirement reason.

### 8c.5 Second in-place correction: FR-10's stale artifact status

FR-10's status line, appended by me on 2026-08-01, read "DESIGNED, NOT BUILT (verified absent
2026-08-01)". **That was true when checked and is now false.**
`docs/reports/policy-implementation-audit-v2.md` exists at 507 lines / 28,780 bytes, commit
`bf92747`, mtime 2026-08-01 17:21 -- written after my existence check ran. Corrected in place with
the supersession disclosed inline and in a Change Log row, same method and same justification as the
`config.py` correction in section 8a.3: content this pass appended, in an uncommitted tree, nothing
predating 2026-08-01 touched. Left uncorrected, it would have licensed someone to rebuild an artifact
that already exists.

### 8c.6 V2-005's column AC -- CHECKED, and it does NOT match

**Reported, not fixed -- the instruction was to change only V2-004.**

V2-005's AC requires the `Post-plugin plan` column to be populated from the fixed vocabulary
`keep-as-is / port-to-plugin / port-to-MCP / demote-to-advisory / delete`, and states "a value
outside that set fails review". The regeneration in flight uses
`PORT-TO-MCP | DEMOTE-TO-ADVISORY | DELETE | UNAFFECTED | UNDECIDED`.

| | Count | Values |
|---|---|---|
| Shared | 3 | `port-to-MCP`, `demote-to-advisory`, `delete` |
| In V2-005's AC only | 2 | `keep-as-is`, `port-to-plugin` |
| In the regeneration only | 2 | `UNAFFECTED`, `UNDECIDED` |
| Union | 7 | -- |

3 + 2 = 5 per side; 3 + 2 + 2 = 7 union. Two problems, one cosmetic and one substantive:

1. **Case.** The AC's values are lower-hyphen, the regeneration's are upper-hyphen. Trivial if the
   checker normalises, fatal if it takes "a value outside that set fails review" literally -- which
   is how it is written. Every row would fail.
2. **`UNDECIDED` defeats the intent of two separate requirements, and this is the one worth
   escalating.** PRD FR-2's AC states "a row with an empty Post-plugin plan cell fails this AC", and
   PRD FR-20 requires "a non-empty Post-plugin plan value" for all 14 orphans. `UNDECIDED` is a
   non-empty cell that encodes "no decision has been made" -- it satisfies the letter of both while
   defeating what both were written to force. This is structurally the same escape hatch that NFR-4's
   AC closes by name when it forbids a "disappeared" disposition value. If `UNDECIDED` is retained,
   FR-2's and FR-20's ACs need an explicit clause excluding it from counting as populated;
   otherwise the audit can pass its gate with every hard decision deferred.
3. **`UNAFFECTED` has no counterpart** in the AC vocabulary. `keep-as-is` is the nearest, but they
   are not synonyms: `keep-as-is` is a decision to retain, `UNAFFECTED` is an assertion that the
   change does not touch the policy.

**Recommendation (not applied):** reconcile the two vocabularies in one place before V2-005 is worked,
and if `UNDECIDED` survives, amend FR-2's and FR-20's ACs to state that it does not count as a
populated disposition. Owner of that edit is unassigned.

### 8c.7 What the live GitHub issue #260 needs

Not edited -- the `github-api` MCP server exposes no issue-update tool (`github_add_comment` exists;
no update/edit tool is available). The following should be posted as a comment:

> **AC3 re-scoped and a false premise corrected (2026-08-02, owner ruling).**
>
> **1. This issue's premise is wrong.** It asserts
> `docs/reports/policy-implementation-audit-v2.md` is ABSENT. It EXISTS: 507 lines, 28,780 bytes,
> commit `bf92747`, written ~20 minutes before this issue was drafted from a plan nobody re-read.
> The artifact is BUILT and is being RESHAPED. Do not close this issue against the file's current
> shape and do not treat the artifact as missing. What is actually outstanding: the file does not yet
> present a single 46-row matrix (it carries several grouped tables) and has no per-row Verification
> label. That is a reshape, not a rebuild.
>
> **2. AC3 was unsatisfiable.** It demanded a line-by-line read of `~/.claude/policies/` while AC1
> demands 46 rows keyed to `docs/policies/`. MEASURED 2026-08-02: `docs/policies/` = 46 `.md` files;
> `~/.claude/policies/` = 44 `.md` files across 4 subdirectories, 35 distinct basenames; overlap 28;
> **18 of the 46 are absent from the `~/.claude/` tree**. No line-by-line read of that tree can
> evidence 46 rows. Original-AC defect, not a shortfall in work produced.
>
> **3. Authoritative corpus:** `docs/policies/` (ADR-009). `~/.claude/policies/` is a partial mirror.
> **Runtime note:** `get_policies_dir()` (`src/utils/path_resolver.py:255-261`) resolves to
> `~/.claude/policies`, the partial mirror -- verified by execution. FR-19, which would fix that, is
> deferred to v2.1. **Do not use `get_policies_dir()` to enumerate the corpus for this issue.**
>
> **4. AC3 is replaced by a POLICY-TO-CODE MAPPING VERIFICATION** -- six machine-checkable
> assertions that test the original intent (a classification is grounded in code, not asserted)
> without re-auditing 46 policies by hand: (1) row-set identity as a set equality against
> `docs/policies/`; (2) every row carries a `MEASURED`/`CITED`/`INFERRED` label from the audit's own
> published vocabulary; (3) `MEASURED` rows carry a resolvable `path:line`; (4) `CITED` rows name an
> existing source artifact; (5) `NONE` is explicit and never blank, and never `MEASURED`; (6) the
> reported coverage split equals the split recomputed from the rows. **No minimum MEASURED count is
> set** -- the audit discloses 41 of 46 remain CITED, so a 46-MEASURED bar would be unsatisfiable in
> a new way.
>
> **5. Size flag.** The 8 points were anchored on the line-by-line read, which no longer exists, and
> on producing an artifact that already exists. 8 is judged too high. Not re-pointed here --
> product-manager-agent's call.
>
> Full text: `prd-v2.md` section 5 (FR-1 superseding row), `SRS.md` appended AC-10,
> `docs/phase-6-sprint/github_issues.json` V2-004.

### 8c.8 What I could not verify

1. **I did not verify issue #260's live body text**, only what the local draft says. If the live
   issue diverges from `github_issues.json`, the comment above addresses the draft's wording.
2. **I did not inspect the in-flight regeneration.** V2-005's vocabulary mismatch is assessed against
   the value set as relayed (`PORT-TO-MCP | DEMOTE-TO-ADVISORY | DELETE | UNAFFECTED | UNDECIDED`),
   not against a produced file. `post-plugin` occurs **0 times** in the current audit -- MEASURED --
   so there is nothing yet to compare against.
3. **I did not re-verify the 46 classifications**, which is the whole point of the re-scope. The
   41-of-46-CITED disclosure is read from the audit at `:460` and `:506`, not re-derived.
4. **The 9 duplicated basenames** in `~/.claude/policies/` mean a basename-keyed comparison is
   ambiguous for those files. The 18-absent figure is basename-based; a content-based comparison
   could differ and was not performed.
5. **Whether `test`-side tooling exists** to run the six new assertions was not checked; the
   verification script is DESIGNED, NOT BUILT.

---

## 9. Outstanding Obligations Created by This Append

1. **A Change Log row dated to the PreToolUse/PostToolUse deletion PR** must be appended when that PR
   lands, referencing SRS FR-34 by number. Until then, SRS FR-34's acceptance criterion is only
   half-satisfied and the placeholder row in section 6 is marked `OUTSTANDING`.
2. **The `register-mcp` uninstall-survival verification** (roughly 10 minutes, performable only once
   `register-mcp` exists) determines whether NFR-12's uninstall path is measured safe or acquires a
   mandatory external control.
3. **The `VERSION` versus `CLAUDE.md`/PRD version discrepancy** (`1.21.5` versus `1.21.4`) is flagged
   and unowned.

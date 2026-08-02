# ADR-006: Hook-Free Execution Model

**Status:** Accepted (SETTLED at the STEP 0.5 consultation gate; pre-committed by the project owner and not open for re-litigation)
**Date:** 2026-08-01
**Deciders:** Project owner (decision), solution-architect (recording)
**Target release:** v2.0.0
**Implements:** PRD FR-6 (`docs/phase-0-requirements/prd-v2.md`, Deliverable D2) / SRS FR-16 (`SRS.md`)
**Build status of the decision itself:** DESIGNED, NOT BUILT. This document records a decision. The
hook removal it decides (SRS FR-13, SRS FR-15) has not been performed. See section "Build status of
everything referenced here".

---

## 1. Context

The pipeline integrates with four Claude Code hook types -- `UserPromptSubmit`, `PreToolUse`,
`PostToolUse` and `Stop` (`SRS.md` FR-9 "Hook System", line 133 as of 2026-08-02). A `Notification`
hook additionally exists as a user-level registration outside that set
(`docs/phase-1-architecture/hld.md` section 1 hook inventory table, Notification row, line 52 as of
2026-08-02).

Two of the four, `PreToolUse` and
`PostToolUse`, are registered on `matcher: ""`, so they fire on every tool call. Each fires a
synchronous Python process spawn with a 60s timeout, and the user's global instruction mandates
`async: false` for all hooks. The worst case is up to 120s of blocking before Claude sees any prompt,
and a hook crash blocks the tool call outright.

The question at the STEP 0.5 consultation gate was whether v2.0.0 keeps that model, narrows it, or
removes it.

This document is the standalone record of that decision at the path PRD FR-6 and SRS FR-16 require.
The decision text is not authored here. It is pre-committed by the project owner in
`docs/orchestration_prompt.md` section 5, under the heading `ADR-006: Hook-Free Execution Model`
(line 803 as of 2026-08-02), and recorded in the HLD at
`docs/phase-1-architecture/hld.md` section 4.1, heading `#### ADR-006: Hook-Free Execution Model
(SETTLED)` (line 213 as of 2026-08-02). `docs/phase-2-validation/hld_v2.md` is the Phase 2 copy of
the same HLD content.

---

## 2. Decision

**Chosen:** Remove `PreToolUse` and `PostToolUse` entirely; take `UserPromptSubmit` off the hot path.

That is two hook events removed, enumerated: (1) `PreToolUse`, (2) `PostToolUse`. A third,
`UserPromptSubmit`, is retained but moved off the every-prompt hot path (SRS FR-15). The `Stop` and
`Notification` hooks are unaffected by this ADR and remain user-level registrations that the plugin
neither owns, installs, nor modifies (SRS FR-18; ADR-010).

**Why:** Two synchronous Python process spawns per tool call on `matcher: ""` with 60s timeouts each;
up to 120s blocking before Claude sees any prompt. Dominant latency on long tasks and a single-point
failure surface -- a hook crash blocks the tool call.

Source: `docs/orchestration_prompt.md` section 5, ADR-006 `Chosen:` and `Why:` lines (lines 804-807
as of 2026-08-02); `docs/phase-1-architecture/hld.md` section 4.1, ADR-006 `Chosen` and `Why` bullets
(lines 215-218 as of 2026-08-02).

---

## 3. Alternatives Rejected

Two alternatives were considered and rejected. Enumerated:

| # | Alternative | Why rejected |
|---|---|---|
| 1 | Keep hooks but set `async: true` | The user's global instruction mandates `async: false` for all hooks. It also does not remove the process-spawn cost; it only hides its latency. |
| 2 | Narrow the matcher instead of deleting | Reduces but does not eliminate per-call overhead, and leaves the 60s timeout failure mode intact. |

Source: `docs/orchestration_prompt.md` section 5, ADR-006 `Rejected:` block (lines 808-812 as of
2026-08-02); `docs/phase-1-architecture/hld.md` section 4.1, ADR-006 `Rejected` bullet (lines 219-222
as of 2026-08-02).

A third option -- keeping a reduced `PostToolUse` hook purely for checkpointing -- was raised later,
during ADR-011, and rejected there on the grounds that it violates this ADR and reinstates the
per-tool-call process spawn this project exists to remove
(`docs/phase-1-architecture/hld.md` ADR-011 `Rejected` bullet, line 330 as of 2026-08-02). It is
listed here for completeness and is not one of the two alternatives weighed at the original gate.

---

## 4. Consequence

The pre-committed consequence text, quoted verbatim and not softened:

> Consequence (MUST be stated in the ADR, not softened): enforcement becomes opt-in. Policies do not
> apply on sessions where the plugin is never invoked. Accepted by the user.

-- `docs/orchestration_prompt.md` section 5, ADR-006 `Consequence` lines (lines 813-814 as of
2026-08-02).

The HLD states the same consequence at full strength, quoted verbatim:

> **Consequence, stated plainly and not softened:** **Enforcement becomes opt-in. Policies do not
> apply on any session where the plugin is never invoked.** A developer who never types the slash
> command gets no policy enforcement at all -- no PreToolUse block, no push gate, no standards
> injection, no progress tracking. Coverage becomes a function of user habit rather than a property
> of the system. This is not a risk to be mitigated away; it is the accepted price of removing
> involuntary per-tool-call execution. Accepted by the user.

-- `docs/phase-1-architecture/hld.md` section 4.1, ADR-006 `Consequence` bullet (lines 223-228 as of
2026-08-02).

This design does not make enforcement better. It makes enforcement opt-in. That is the accepted cost
of ADR-006 (`docs/phase-1-architecture/hld.md` section 1.4 "The governing trade-off", lines 80-81 as
of 2026-08-02). It is recorded as an accepted risk, not an open item, in `docs/REVIEW-INDEX.md`
section 3 "ACCEPTED RISKS", row "Enforcement becomes opt-in" (line 62 as of 2026-08-02).

### 4.1 The three named consequences (PRD FR-4a / SRS FR-14)

PRD FR-6 and SRS FR-16 require this document to cross-reference all three capability-level
consequences that survived the blast-radius measurement. Per SRS FR-16's acceptance criterion, a
consequence recorded only in `docs/orchestration_prompt.md` does not satisfy the requirement, so all
three are stated here in full.

There are exactly three. Enumerated: (1) SRS FR-9 supersession, (2) version-push-gate bypass
reopening, (3) per-tool-call progress loss.

They are named in `docs/phase-1-architecture/hld.md` section 4.1, ADR-006 bullet "Required
cross-reference in the ADR-006 document (FR-6)" (lines 229-231 as of 2026-08-02) and in `SRS.md`
FR-14 (lines 210-212 as of 2026-08-02).

**Structural context, so the three are not mistaken for a wider breakage claim.** The measured
structural blast radius is small and was verified: 135 of 2,218 call-graph nodes disappear (6.09
percent), entirely inside the three deleted packages; of 26 candidate cross-boundary edges, zero
survived confidence verification, and 4 were manually spot-checked and confirmed to be bare-name
collisions. Nothing outside the deletion set breaks structurally
(`docs/orchestration_prompt.md` FR-4a, paragraph beginning "Structurally contained (good news,
verified):", lines 145-151 as of 2026-08-02). The three consequences below are capability-level, not
structural, and the two must not be conflated.

#### Consequence 1 -- the change set violates the project's own SRS

`SRS.md` FR-9 (Hook System) and its acceptance criterion state that all four hook events fire and
that a blocking policy returns exit code 2 from the `PreToolUse` hook so the tool call does not
proceed. Deleting `PreToolUse` and `PostToolUse` falsifies this for two of the four events.

Per `rules/44` (mirrored in this repo at `docs/standards/44-srs-lifecycle.md`) the SRS is
append-only, so FR-9 cannot be quietly edited in place. The
required handling is a superseding append that retires FR-9's four-event guarantee, states the v2.0.0
replacement guarantee, and adds a Change Log row. An agent that silently rewrites FR-9 in place is in
violation of `rules/44` and its output must be rejected.

- Owning requirement: PRD FR-22 / SRS FR-34.
- Status: **PARTIALLY SATISFIED.** The superseding append and the revised AC-9 are already in
  `SRS.md`. One element remains outstanding and is **DESIGNED, NOT BUILT**: SRS FR-34's acceptance
  criterion requires a Change Log row dated to the PR that deletes `PreToolUse`/`PostToolUse`, and
  that PR does not exist. `SRS.md` records this as an explicit outstanding obligation rather than
  back-dating it (Change Log row beginning "PENDING -- date of the PR that deletes", line 968 as of
  2026-08-02).
- Sources: `docs/orchestration_prompt.md` FR-4a, paragraph beginning "*Consequence 1 -- the change set
  violates the project's own SRS.*" (lines 156-162 as of 2026-08-02); `SRS.md` FR-34 (lines 418-428
  as of 2026-08-02).

#### Consequence 2 -- deletion re-opens a bypass that was deliberately closed

Among the lost `PreToolUse` policy gates is the version-push gate,
`hooks/pre_tool_enforcer/policies/push_gate.py`, covered by `tests/test_push_gate.py`. Commit
`1bb4303` ("fix: generate the SRS where it is read, and close a bypass in the version push rule
(#251)") is recent, deliberate governance work, and removing `PreToolUse` discards its enforcement
permanently. Re-opening a bypass someone explicitly closed is not an acceptable silent outcome of a
refactor.

The gate's disposition is therefore MANDATORY `port-to-MCP`, not `demote-to-advisory` and not one of
four open options.

**Consequence 2a -- the ordering constraint is not self-enforcing.** The port must land BEFORE
`PreToolUse` is deleted. At present that is a sequencing statement in a document; nothing mechanical
enforces it. An out-of-order merge silently re-opens the bypass and no test fails, because the gate
stops existing rather than starting to misbehave. The required control is a CI assertion, landed as
part of the port and before the deletion, that fails the build if the `PreToolUse` registration is
absent while no equivalent MCP-side version-push gate is reachable. It must be an
existence-and-reachability check on the REPLACEMENT, not a check that the old hook is still present,
otherwise it would block the very deletion this project is delivering.

- Owning requirement: PRD FR-23 / SRS FR-35; the CI assertion is ADR-017.
- Status: disposition MANDATED; the port is **DESIGNED, NOT BUILT**, and the ADR-017 CI assertion is
  **DESIGNED, NOT BUILT**. Both `hooks/pre_tool_enforcer/policies/push_gate.py` and
  `tests/test_push_gate.py` exist on disk (verified 2026-08-01 per `SRS.md` FR-35).
- Sources: `docs/orchestration_prompt.md` FR-4a, paragraphs beginning "*Consequence 2 -- deletion
  re-opens a bypass that was deliberately closed.*" and "*Consequence 2a -- the ordering constraint
  that protects the push gate is not enforced by anything*" (lines 164-184 as of 2026-08-02);
  `SRS.md` FR-35 (lines 430-439 as of 2026-08-02).

#### Consequence 3 -- per-tool-call progress loss (NFR-3, as re-scoped)

**Read the correction before the claim.** The original Phase 0 framing of this consequence was WRONG
and was superseded on 2026-08-01. It asserted that `post-tool-tracker.py` is the sole writer of
session-progress and checkpoint state, and therefore that hook deletion loses crash recovery. Direct
verification showed that sentence conflates two separate state systems.

The corrected position, which is what this ADR records:

1. **Step-boundary crash recovery SURVIVES, hook-independent.**
   `langgraph_engine/checkpoint_manager.py::CheckpointManager` is driven at every step boundary by
   `langgraph_engine/core/step_decorator.py`, with a real resume entry point at
   `orchestrator.py::resume_flow` delegating to `quality/recovery_handler.py::resume_from_checkpoint`.
   None of this lives under `hooks/`. The SRS "resume from any step after crash" guarantee is written
   at step granularity and is backed by this system, so it is NOT at risk from hook deletion.
2. **Per-tool-call progress tracking DIES with `PostToolUse`.** This is the hook-owned system
   (`hooks/post_tool_tracker/progress_tracker.py`) and it is the genuine loss. It is at per-tool-call
   granularity, finer than any SRS step guarantee.

The loss is therefore closer to the original "telemetry loss" framing than to the escalated "crash
recovery loss" framing. The escalation was an orchestrator error propagated from a Phase 0.2 claim
that named a single sole writer where two independent writers exist.

The replacement is the existing `mcp-post-tool-tracker` MCP server (`increment_progress`,
`track_tool_usage`), called explicitly by the pipeline at defined boundaries, and required to be a
projection of the checkpoint record rather than an independent second writer -- otherwise checkpoint
and progress become a dual write that can disagree after a crash.

**Warm daemon, correctly attributed.** The warm-daemon fast path is at
`hooks/pre_tool_enforcer/daemon.py`. It is a `PreToolUse` asset, not a `PostToolUse` one; earlier text
attributed it to `PostToolUse`. It is lost either way, because both hooks are deleted, but it belongs
to the `PreToolUse` deletion. Its replacement is structural: an MCP stdio server is already a warm,
long-lived process, so the warm-path benefit returns through the MCP transport.

- Owning requirement: PRD NFR-3 / SRS NFR-9; the ownership decision is ADR-011.
- Status: **DESIGNED, NOT BUILT.** The replacement writer is not a new component and already exists,
  but three durability defects and the progress-projection port are unbuilt: (i) the checkpoint-save
  failure currently swallowed with a warning must instead raise or set a `checkpoint_degraded` flag
  the resume path refuses to trust; (ii) the progress replacement must be a projection of the
  checkpoint record, never an independent second writer; (iii) replay must be idempotent on a
  session-id-plus-step-number key for side-effecting steps.
- Sources: `docs/orchestration_prompt.md` FR-4a, paragraphs beginning "*Consequence 3 -- SUPERSEDED
  2026-08-01.*" and "*Consequence 3a -- warm daemon mis-attributed*" (lines 186-217 as of
  2026-08-02); `docs/phase-1-architecture/hld.md` section 12, heading "### OAQ 1 -- NFR-3
  crash-recovery replacement -- **RESOLVED**" (lines 1455-1507 as of 2026-08-02); `SRS.md` NFR-9
  (lines 616-630 as of 2026-08-02).

---

## 5. Build status of everything referenced here

Nothing in this ADR describes shipped behaviour. Enumerated, six items:

| # | Item | Owning requirement | Status |
|---|---|---|---|
| 1 | Delete `PreToolUse` and `PostToolUse` | SRS FR-13 | DESIGNED, NOT BUILT |
| 2 | Take `UserPromptSubmit` off the hot path | SRS FR-15 | DESIGNED, NOT BUILT |
| 3 | SRS FR-9 supersession append | SRS FR-34 | PARTIALLY SATISFIED; cutover Change Log row DESIGNED, NOT BUILT |
| 4 | Version-push gate ported to MCP | SRS FR-35 | DESIGNED, NOT BUILT |
| 5 | CI assertion enforcing port-before-delete ordering | ADR-017 | DESIGNED, NOT BUILT |
| 6 | Progress writer as a projection of the checkpoint record, plus the three durability fixes | SRS NFR-9 / ADR-011 | DESIGNED, NOT BUILT |

This document itself (PRD FR-6 / SRS FR-16) is the deliverable being satisfied by its own creation.

---

## 6. Citation note

Line numbers in this document are dated hints, valid as of 2026-08-02. `SRS.md` and
`docs/phase-2-validation/hld_v2.md` both grew during earlier correction passes, which invalidated
line-number-only citations elsewhere in this project. Every citation above therefore leads with a
stable anchor -- a section number, a heading, an FR or ADR number, or a quoted sentence opening --
and carries the line number only as a secondary aid. Resolve by anchor first.

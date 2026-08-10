# Session Management Policy

**Version:** 3.0.0
**Status:** ACTIVE
**Last Updated:** 2026-08-10
**Supersedes:** `session-chaining-policy.md`, `session-memory-policy.md`, `session-pruning-policy.md` (1,876 lines combined)
**Design record:** the architecture this policy governs is specified in the session-management remediation blueprint (ADR). This document states the *rules*; the blueprint states the *design*.

---

## 0. Why this document replaced three others

The three superseded policies described a system that was never built. Between them they named
fourteen scripts — `session-loader.py`, `session-search.py`, `auto-save-session.py`,
`session-auto-save-daemon.py`, `session-pruning-daemon.py`, `archive-old-sessions.py`,
`session-start.sh`, `session-chain-manager.py`, `clear-session-handler.py` and others. None of them
existed on disk. The real implementation was a different shape entirely: an MCP server and a
LangGraph node.

Because the spec and the code never described the same system, drift between them was undetectable
by construction. Every defect found in the 2026-08 audit was downstream of that.

This policy is therefore written to be **falsifiable**: §7 names real module paths and marks each
one's status, so a reader can check the claim rather than trust it. Section 4's invariant **I6**
makes keeping that section honest a rule rather than a courtesy.

---

## 1. Purpose

Session management provides continuity across Claude Code sessions: it restores what previous work
established, accumulates what the current run does, and persists a summary that the next run can
use. It is the state-persistence layer beneath the workflow engine, not a part of it.

---

## 2. Scope — what session management owns

| Concern | Description |
|---|---|
| **Identity** | Resolving and publishing the one session ID every component agrees on |
| **Chaining** | Parent/child links, related-session links, tags, and the index over them |
| **Accumulation** | Per-request records: prompt, task type, skill, model, complexity, cwd |
| **Summary** | A finalized, human-readable record produced once per session |
| **Project memory** | The cumulative per-project summary that makes the next session cheaper |
| **Retention** | Pruning and archival of sessions past their useful life |

---

## 3. Out of scope

Session management **must never import or call** git, GitHub, PR, Jira, or any other SDLC
integration. Those are Level 2 pipeline steps and own their own lifecycles.

This is a hard architectural boundary, not a style preference. The superseded
`session-memory-policy.md` carried an entire `Git Auto-Commit Integration` section that ran
`git add -A` / `commit` / `push` from the session layer, and a session schema with
`repos_committed` and `commit_hashes` fields. That coupling is removed and must not return.

**The one permitted direction — inbound, opaque, one-way.** The SDLC layer MAY write metadata
*into* the session store: `issue_id`, `agent_id`, failure reasons, and similar references. The
session layer stores and returns these values without interpreting them and without any dependency
on the layer that produced them. This is what allows the question *"which agent failed in which
session?"* to be answered without coupling.

Also out of scope: the LangGraph graph topology, and re-registering the hooks that ADR-017
unregistered.

---

## 4. Invariants

These must hold at all times. A change that violates one is a defect regardless of what it enables.

**I1 — Restore before anything else.**
The session node is the first substantive node after the Level 0 pre-flight guard, and its first
action is to restore: session identity, then chain context, then project summary. No downstream
node may run before restore completes. Nodes that fan out after it are entitled to assume restored
context is present.

**I2 — Identity is keyed to Claude Code's own session UUID.**
Where Claude Code supplies a session UUID, that value is canonical and is stored verbatim so a
session can be joined to its transcript. A synthetic ID may be minted only when no Claude session
exists, and must be **marked as synthetic**. A UUID is never truncated into an ID: a truncated
UUID is not a join key, it only looks like one.

**I3 — Every write goes through the locked entry point.**
Session state is written by concurrent agents. All mutations of shared session JSON must use the
mutually-exclusive read-modify-write path, never a bare read-then-write. An unlocked
last-writer-wins save exists and is legitimate for single-writer files; it is not permitted for
the chain index or the accumulator. Losing a write silently while reporting success is the failure
mode this prevents.

**I4 — Finalize is idempotent and fires from two independent triggers.**
The Stop hook fires per Claude session; the pipeline terminal node fires per run. These are **not**
symmetric redundancy — only the terminal node covers every run, and only the Stop hook covers a
session that ends without a pipeline run. Both must be able to finalize the same session without
producing a double record, and the check-and-write must be a single locked transaction.

**I5 — The session layer never depends on the SDLC layer.** See §3.

**I6 — Spec and implementation must name each other.**
Any module implementing this policy is listed in §7 with its status. Any module listed in §7 must
exist at the stated path, or be explicitly marked as planned with the phase that delivers it.
Naming a component that does not exist is the specific failure that made the superseded policies
worthless.

---

## 5. Data model

The on-disk contract. Locations are canonical; a component reading or writing session state
elsewhere is a defect.

| Artifact | Location | Purpose |
|---|---|---|
| Session directory | `{memory}/logs/sessions/{session_id}/` | Everything belonging to one session |
| Session pointer | `{memory}/.current-session.json` | The active session ID |
| Chain index | one file, under `{memory}/logs/` | Nodes, parent/child/related edges, tags, tag index |
| Accumulator | `{session_dir}/session-summary.json` | Per-request records and aggregates |
| Session summary | `{session_dir}/session-summary.md` | Finalized human-readable record |
| Project summary | per project | Cumulative context restored at session start |
| Archives | grouped by `YYYY-MM` | Compressed sessions past the retention window |

**The chain index is a derived cache.** It must be rebuildable from the session directories. It is
never the only copy of anything that matters.

**Field ownership must be explicit.** Every field is either session-owned or inbound-opaque (§3).
Inbound-opaque fields are stored and returned unmodified and are never interpreted by this layer.

---

## 6. Lifecycle

```
RESTORE     identity -> chain context -> project summary        (I1, first node)
   |
ACCUMULATE  one record per request                              (I3)
   |
CHECKPOINT  explicit save points only                           (I3)
   |
FINALIZE    summary + project summary update                    (I4, idempotent)
   |
PRUNE       archive past the retention window
```

**Checkpoints are explicit, not continuous.** Saving on every node transition is prohibited — the
overhead is real and the value is not. Only declared checkpoint points write. The set of
checkpoints and their per-run cost are specified in the blueprint, which is required to state that
cost as a measured number.

**Restore is bounded.** Restored context is capped. An unbounded project summary cannot serve as a
cheap restore and must not be allowed to grow into one.

---

## 7. Component map

Per invariant **I6**, this section is the falsifiable claim. Status is as of 2026-08-10.

| Component | Path | Status |
|---|---|---|
| Session identity resolution | `hooks/session_context.py` | **Working** — single authority; also provides `FileLock`, `atomic_write_text`, `locked_json_update` |
| Session MCP surface | `mcp-session-mgr` (separate repo) | **Live** — this is the server Claude actually runs |
| Session store (shared logic) | to be extracted | **Planned** — blueprint Phase 2 |
| Atomic/locked IO | to be extracted | **Planned** — blueprint Phase 1 |
| Level 1 session node | `langgraph_engine/context_sync/session_loader.py` | **Partial** — creates the session; does not yet restore (I1) |
| Pruning | `langgraph_engine/context_sync/architecture/session_pruner.py` | **Present, non-functional** — collects files, but sessions are directories |
| In-engine MCP server copy | `src/mcp/session_mcp_server.py` | **Being retired** — superseded by the standalone |

**Two implementations existed.** The in-engine copy and the standalone repo diverged by over 1,300
lines while both remained live: Claude's MCP tool calls reached one, the engine's in-process
imports reached the other. Authority is now split **by layer** — shared logic is canonical in the
engine, the MCP surface is canonical in the standalone — and the in-engine server is retired.

**The generator is destructive.** `scripts/tools/create_mcp_repos.py` overwrites `server.py` and
replaces `base/` in existing repos. All 13 target repos have evolved past their generated state
(75 commits, ~29 merged PRs). It must not be run until it is made non-destructive.

---

## 8. Retention

- Keep the most recent sessions regardless of age.
- Archive beyond the retention window, grouped by month, compressed.
- **Never archive a project summary.**
- Archival is one layout. A second, incompatible layout is a defect, not an alternative.
- Pruning must be verified against the real directory-per-session layout before it is trusted —
  a pruner that silently archives nothing looks identical to one with nothing to do.

---

## 9. Governance

This file is the single source of truth for session-management policy. It lives in the repository
so that policy and code change together and in one place.

The three superseded policies previously existed in two locations — this repository and
`~/.claude/policies/01-sync-system/session-management/` — with no synchronisation between them.
The unversioned copies are retired **only after this document is committed**.

Changes to session-management behaviour update this file in the same change as the code. A
component named here that does not exist, or a component that exists and is not named here,
violates **I6** and is a defect in this document.

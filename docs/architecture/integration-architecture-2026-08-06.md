# Integration architecture: what exists, what is connected, and what to build

Written 2026-08-06 from three independent surveys — the MCP server surface, policy conformance,
and library routing — each done by a separate agent against live code rather than documentation.

---

## 1. The diagnosis

**Almost everything needed already exists. Very little of it is connected to anything else.**

This is not a shortage of capability. It is a shortage of wiring, and the same two failure shapes
recur in every layer surveyed.

### Failure shape A — built, tested, never called

| Component | State |
|---|---|
| `selection/selector.py::select_agents()` | KG scoring engine with confidence floors and four named outcomes. **Zero production callers.** Exercised only by three test files. |
| `skills/agent_loader.py::SkillAgentLoader` | Reads `~/.claude/skills` and `~/.claude/agents`, parses frontmatter. **Zero production callers.** |
| 19 of 21 sibling MCP servers | Registered, real tools, **zero Python call sites** in the engine. |
| `mcp-jira-api` (52 tools), `mcp-figma` (47 tools) | Large, real toolkits. Nothing calls them. |

### Failure shape B — imports of things that do not exist, failing silently

| Call site | Imports | Reality |
|---|---|---|
| `hooks/stop_notifier/post_impl.py:164,270` | `github_mcp_server` | Extracted to `mcp-github-api`. Only a stale `.pyc` remains. |
| `sdlc_pipeline/jira_lifecycle.py` | `jira_mcp_server` from `src/mcp/` | **Never existed.** Jira lifecycle silently no-ops. |
| `sdlc_pipeline/figma_workflow.py` | `figma_mcp_server` from `src/mcp/` | **Never existed.** Figma workflow silently no-ops. |
| Stop hook policy scripts | 9 spawn targets | **7 absent repo-wide.** `.exists()` guards fail every turn. |
| `mcp-plugin-discovery-policy.md` | `MCPPluginLoader` | Absent repo-wide, stale `.pyc` only. |

Every one of these is caught, logged, and continues. **The system is designed to survive its own
missing pieces, which is why nobody noticed how many are missing.**

---

## 2. What is actually load-bearing today

Of 26 registered MCP servers, **two** are reached by running code:

- **`session-mgr`** — and not over MCP. The engine imports an in-engine copy directly
  (`src/mcp/session_hooks.py`), so the protocol is bypassed entirely.
- **`push-gate`** — in-engine, registered by the plugin, replacing the deleted PreToolUse hook.

The other 24 registrations are the operator's personal configuration. They predate v2.0.0 and sit
entirely outside anything the plugin installs or knows about. **The plugin's own
`mcp-registry.json` contains exactly two entries.**

Meanwhile the engine reimplements, in-process, what several of those servers already provide:
PyGithub instead of `github-api`, `urllib.request` instead of `jenkins-ci`, an internal
`DiagramFactory` instead of `uml-diagram` and `drawio-diagram`, the `anthropic` SDK instead of
the four LLM provider servers.

**Naming hazard:** `langgraph_engine/github/mcp.py` defines a class called `GitHubMCP` that is a
PyGithub wrapper with no relation to the `mcp-github-api` server. Anyone grepping for it finds
the wrong thing.

---

## 3. What the surveys corrected

Three claims that were being repeated and are not true:

1. **`docs/policies/` does not mirror `~/.claude/policies/`.** 46 flat files versus a nested tree
   of 34. **18 have no counterpart; 6 exist only in the runtime copy and were never audited.**
   This matters because `standards/selector.py` reads the runtime copy — a policy can be correct
   in the audited set and absent from what actually loads.
2. **ADR-010, ADR-017, ADR-019 and ADR-020 have no standalone files.** Only ADR-002 through
   ADR-006 exist. Four decisions the architecture rests on are cited everywhere and recorded
   nowhere.
3. **`CLAUDE.md`'s MCP table is internally inconsistent** — its 13 rows sum to 137 tools while its
   header claims 295, and `jira-api` (10 → 52) and `figma-api` (10 → 47) are stale by a wide
   margin. The library documentation, by contrast, is accurate: `orchestration_prompt.md` records
   505/992 against a real 509/997.

One thing checked and found **healthy**: `mcp-base` has no drift. `decorators.py`, `response.py`,
`persistence.py` and `__init__.py` are byte-identical across all 19 copies. `clients.py` differs
only where `mcp-github-api` carries a deliberate idempotency fix.

---

## 4. Target architecture

The goal: everything becomes a plugin; plugins compose; the library goes public but is reached
only through a plugin that loads a selected subset into context.

### 4.0 The execution model: in-session, not subprocess

**Owner ruling, 2026-08-06: the flow runs in the active Claude Code session. No `claude -p`
subprocesses.**

This is the largest change in this document, because the engine currently does the opposite.
`sdlc_pipeline/architecture/prompt_gen_expert_caller.py`, `todo_decomposer.py` and
`orchestrator_agent_caller.py` each spawn the `claude` CLI and capture stdout. Step 1 alone is
two subprocess calls, and `todo_executor` adds one per TODO.

The shift is from **"Python orchestrates LLM subprocesses"** to **"the live session orchestrates
itself, calling Python for the deterministic parts."**

Three consequences, and the first two are the reason the ruling is right:

1. **It removes a spawn class entirely.** Every subprocess call is a process the session pays for.
   Today's NFR-1 work measured the cost of exactly this shape: the observer's own startup — shell
   spawn, Python boot, imports — was around 20 seconds. Every `claude -p` call carries a
   comparable cost, invisibly, on the pipeline's hot path.
2. **It dissolves the content-injection problem rather than solving it.** See 4.2.
3. It makes the plugin's commands the real entry points, which is what v2.0.0 set out to do. The
   subprocess callers are hook-era leftovers that outlived the hooks.

What this does **not** mean: Python stops mattering. Deterministic work — KG routing, catalogue
scoring, process measurement, git and GitHub calls — stays in Python and is invoked as tooling.
What ends is Python asking an LLM a question through a pipe and parsing the answer.

### 4.1 MCP servers as plugins — and the constraint that decides the design

ADR-019 exists because bundled MCP servers **spawn eagerly on plugin enable, with zero tool
calls**. That was measured, and NFR-1 was measured again today: an installed, uninvoked plugin
contributes zero processes.

**If 22 MCP servers become 22 plugins that each bundle a `.mcp.json`, every one of them passes
NFR-1 individually while the aggregate reproduces exactly what ADR-019 forbade** — 22 servers
spawning at every session start, distributed so that no single plugin looks guilty.

The pattern that avoids this is already built and proven: **a plugin ships a registry entry, not
a server.** `plugin/mcp-registry.json` plus `register-mcp` is how `push-gate` reached this
machine. Extend that, do not replace it.

Design rule: **a plugin may declare an MCP server; only an explicit user action may start one.**

### 4.2 Just-in-time capability loading

The vision is: the library is public, but a user never loads 509 agents and 997 skills at once —
the plugin selects a relevant subset, materialises it, and loads it.

The value here is **not secrecy**. A public library can be cloned by anyone. The value is
**context discipline**: loading everything destroys answer quality. That reframing matters,
because it gives the design a measurable success criterion — how much was loaded, what was
rejected, and why.

Three of the four pieces exist:

| Stage | Component | State |
|---|---|---|
| Select | `selection/selector.py::select_agents()` | Built, tested, **unwired** |
| Route | `routing/kg_router.py` | **Live**, but only passes names into an LLM prompt |
| Materialise | `skills/agent_loader.py::SkillAgentLoader` — reads `~/.claude/skills`, `~/.claude/agents` | Built, **unwired** |
| Inject content | — | **Missing.** `SKILL.md` bodies are loaded in exactly one place, `standards/library_adapter.py`, and only via a fixed `(project_type, framework)` map. |

So the work is mostly **connection, not construction**: `select_agents()` → materialise into
`~/.claude/` → the session loads it.

**The in-session ruling (4.0) changes what "inject content" means, and makes it easier.** Under
the subprocess model, injection meant serialising skill bodies into a prompt string and piping
them to `claude -p` — which is why the current code passes only names: bodies are large and the
pipe is the wrong shape for them. In the active session there is no pipe. A materialised skill
in `~/.claude/skills/` is loaded by the session the same way any other skill is, and today's
measurement showed that happens **without a restart** — eleven plugin skills became live
mid-session.

So content injection is not a component to build. It is what materialisation already produces,
once the subprocess boundary is removed. **The missing piece was never injection; it was the
subprocess in the middle.**

Two constraints remain:

- **Writing into `~/.claude/skills` and `~/.claude/agents` mutates user-scope state.** This is the
  #284 concern and it needs an explicit answer, not a note.
- **A selection budget must be measured, not guessed.** How many agents and skills can be live
  before quality degrades is an empirical question, and the project now has a habit of answering
  those by measuring.

### 4.2.1 Ephemeral capability lifecycle

A capability loaded for one task must not still be loaded three tasks later. Without a teardown,
`~/.claude/skills` accumulates until the selection gate is pointless — the very context blowout
the gate exists to prevent, reached slowly instead of at once.

The lifecycle needs four properties, and each is testable:

| Property | Requirement |
|---|---|
| **Namespaced** | Materialised capabilities land under a reserved prefix, never mixed with the user's own. Anything outside that prefix is never touched. |
| **Inventoried** | A manifest records what was materialised, when, and for which task. Teardown reads the manifest; it never pattern-matches directory names. |
| **Reversible** | Teardown removes exactly what the manifest lists and reports what it removed. |
| **Self-healing** | A stale manifest from a crashed session is detected and cleaned on next load, so a crash cannot leave capabilities live indefinitely. |

**Where teardown runs is a real design constraint, not a detail.** The obvious hook for it is
`Stop` — the one hook still registered. But this document's own Phase 0 finds that the Stop hook
is already the least trustworthy component in the system: 7 of 9 of its spawn targets are absent,
and its auto-PR path has historically committed and pushed unprompted. **Adding capability
teardown to that hook would place a correctness-critical cleanup inside the component with the
worst reliability record here.**

Preferred instead: teardown is an explicit step of the command that materialised the capability,
with the Stop hook used only as a **backstop that reconciles the manifest** — never as the
primary mechanism. That keeps the guarantee inside the flow that made the mess.

### 4.3 Reconciling the engine's own implementations

Where the engine reimplements a server's capability in-process (GitHub, Jenkins, diagrams, LLM
providers), there is a real choice, and it should be made deliberately per capability rather than
by default:

- **In-process** is faster, has no spawn cost, and cannot fail NFR-1.
- **Via MCP** is reusable across projects and is what the operator's own standing instruction
  prefers for interactive work.

Recommendation: keep in-process for the autonomous pipeline's hot path; expose MCP for
interactive and cross-project use. But **name them differently** — the current `GitHubMCP` class
name actively misleads.

---

## 5. Sequence

Ordered by what unblocks what, not by size.

**Phase 0 — stop the silent failures.** Nothing built on this foundation is trustworthy while
imports of non-existent modules are swallowed every turn.

1. **Hard-disable the Stop hook's auto-PR and auto-merge path.** *Owner ruling, 2026-08-06.*
   Historically it committed 25 times, pushed 16, opened 35 PRs and attempted 244 merges. It is
   currently disarmed **only by two broken imports** and it re-triggers every few minutes — it
   fired on this very branch at 16 commits ahead. Repairing the import first would arm it.
   The capability is not lost: the plugin already ships `/claude-workflow-engine:review`, which
   does the same work when asked. **Removal, not repair** — and a test that fails if the path
   returns.
2. Decide each remaining dead import: wire it to the real module, or delete the path.
   `jira_mcp_server`, `figma_mcp_server`, the 7 absent Stop-hook scripts, `MCPPluginLoader`.
3. **Delete 159 orphan `.pyc` files** — compiled modules with no `.py` source, measured
   repo-wide: 48 under `tests/`, 33 under `langgraph_engine/`, 24 under `scripts/`, 16 under
   `src/mcp/`. They include `level2_standards`, `toon_compression`, `session-pruner`,
   `inference_router` and `deepseek_reasoning` — all purged in v1.15.x/v1.16.0.
   These are not merely clutter: **they make the codebase lie about what exists.** `grep` and
   `find` report them, and this survey was misled by them twice — once tracing
   `github_mcp_server`, once tracing the removed LLM providers. Add a CI check so orphaned
   bytecode cannot accumulate again.
4. Make a swallowed import fail loudly in CI, so this class cannot recur silently.
5. Amend `intelligent-decision-engine-policy.md`, the only policy still naming removed providers
   (an "OpenRouter consolidation" whose scripts do not exist and whose provider has zero
   references). No standard or rule names them; the engine's own sources do not either — the
   only remaining traces were the orphan `.pyc` files in item 3.

**Phase 1 — make the record match the system.**

4. Write the four missing ADR files (010, 017, 019, 020) from the decisions already cited.
5. Reconcile `docs/policies/` with `~/.claude/policies/`, or state plainly which is authoritative.
   The runtime copy is what `standards/selector.py` reads.
6. Correct `CLAUDE.md`'s MCP table, or generate it from `mcp-registry.json` so it cannot drift.
7. Retire `hook-system-policy.md` — its entire content describes three hooks that no longer exist.

**Phase 2 — connect what is already built.**

8. Wire `select_agents()` into the pipeline, or delete it. Tested code with no callers is a
   liability either way.
9. Fix the PR-body key mismatch: `step1_selected_skills`/`step1_selected_agents` are read but
   never written; the real keys are `step1_skills`/`step1_agents`. Every PR body's selected-skills
   section is currently empty.
10. Build content injection, and connect select → materialise → load.

**Phase 3 — the plugin-of-plugins model.**

11. Extend `mcp-registry.json` to cover the servers a user actually needs, keeping the
    declare-but-do-not-start rule.
12. Use `mcp-server-engineer` and `claude-code-plugin-engineer` from the library to package the
    MCP servers as plugins.
13. Measure NFR-1 again with several plugins enabled. The instrument exists now; use it before
    the count grows, not after.

---

## 6. What this document does not settle

- Whether the Stop hook's auto-PR capability should be repaired, gated, or removed. That is a
  policy decision, and the plugin already ships `/claude-workflow-engine:review` which does the
  same work on request.
- Whether each duplicated capability should live in-process or behind MCP.
- What the selection budget should be — how many agents and skills may be loaded at once. That
  number needs measuring, not guessing.

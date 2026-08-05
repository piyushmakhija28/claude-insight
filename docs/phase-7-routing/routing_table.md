# Phase 7 Routing Table

All 37 v2.0.0 sprint issues routed to agents and skills from the
claude-global-library master knowledge graph. Grouped by batch, in execution order.

| Property | Value |
|----------|-------|
| Issues routed | 37 of 37 |
| Library version | 29.72.0 |
| Agent catalogue | knowledge-graph/_master/agents_all.json (508 agents) |
| Skill catalogue | knowledge-graph/_master/skills_all.json (996 skills) |
| Distinct agents used | 26 |
| HIGH / MEDIUM / LOW / NO MATCH | 29 / 8 / 0 / 0 |
| Generated | 2026-08-02 |
| Revised | 2026-08-02 (library gap acceptance re-route) |

---

## Revision 2026-08-02 - library gap acceptance re-route

The three agents and four skills specified in `library_gap_spec.md` were delivered. This
file was re-run against them. Eleven rows changed; every other row is untouched and was not
re-litigated. Each changed row carries a dated note naming the specific delivered passage
that justifies the change. The before/after distribution is recorded at the end of this
file.

Changed rows: V2-004, V2-015, V2-016, V2-017, V2-020, V2-021, V2-022, V2-024, V2-026,
V2-032, V2-036. That is 11 rows, enumerated.

---

## Name verification method

Every agent name and every skill name below passed BOTH checks before this file was written,
and the same two checks were re-run on 2026-08-02 against the grown catalogues:

1. **Catalogue membership.** The name is an exact member of
   `knowledge-graph/_master/agents_all.json -> agents[*].name` (508 entries) or
   `knowledge-graph/_master/skills_all.json -> skills[*].name` (996 entries).
2. **Filesystem existence.** `agents/<name>/agent.md` or `skills/<name>/SKILL.md`
   exists on disk in the library checkout.

The two catalogues and the filesystem were reconciled first: 508 of 508 agents in
`agents_all.json` have a directory on disk, 508 of 508 directories on disk appear in the
catalogue, and 996 of 996 skills likewise. The set difference in both directions is empty
except for `agents/INDEX.md` and `skills/INDEX.md`, which are files rather than capability
directories and are correctly absent from both catalogues. There is no name that exists in
one and not the other, so either check alone is sufficient and both were run anyway.

The three new agents (`mcp-server-engineer`, `claude-code-plugin-engineer`,
`technical-writer-agent`) and the four new skills (`mcp-server-engineering-core`,
`claude-code-plugin-packaging-core`, `technical-writing-core`,
`procedural-documentation-core`) each passed both checks individually. The rewrite script
aborts before writing any file if a single name fails either check. No name here was
inferred from a topic, and nothing was sourced from `~/.claude/agents/` or
`~/.claude/skills/`.

**Recorded, not fixed:** the library `VERSION` file still reads `29.72.0` and
`agents_all.json`'s own `library_version` field still reads `29.72.0`, while its
`agent_count` has moved 505 -> 508. The counts were rebuilt; the version string was not
bumped alongside them. This is the same class of count/version drift that V2-002 exists to
fix, observed here in the library rather than in the engine.

---

## Dispatch contract - how to actually run these agents

Library agents are **not** registered subagent types. None of the names below can be
passed as `subagent_type`. To run one:

1. Read the agent's `agent.md` at the path recorded in the row.
2. Spawn `subagent_type: "general-purpose"`.
3. Put a `---persona---` block at the very top of the prompt carrying, at minimum:
   `name`, `description`, `tools`, `model`, and the agent's `## Skill Dependencies`
   section lifted verbatim from that file.

A live PreToolUse hook BLOCKS any generic subagent spawned without such a block, so a
routing row that names an agent without recording where its persona comes from is not
executable. Every row below records the path.

All 24 agent.md files live under
`C:/Users/techd/Documents/workspace-spring-tool-suite-4-4.27.0-new/claude-global-library/`.
Paths in the rows are relative to that root.

---

## Batch A (8 issues)

Deliverable-1 audit trail plus two unblocked builds. Nothing here has an external blocker.

### V2-001 (#256) - PRD FR-6 / SRS FR-16: create docs/architecture/ADR-006-hook-free-execution.md

| Field | Value |
|-------|-------|
| Gate | D2 |
| Primary agent | `solution-architect` |
| Persona source | `agents/solution-architect/agent.md` |
| Supporting agents | none - single capability |
| Mandatory skills | `system-design`, `clean-architecture` |
| Confidence | **HIGH** |

ADR authoring is solution-architect's named output artifact; the job is to place an already-decided ADR at its required path with its Consequence section unedited.

### V2-002 (#258) - PRD FR-9 / SRS FR-20: reconcile claude-global-library master graph count drift

| Field | Value |
|-------|-------|
| Gate | D3 |
| Primary agent | `automation-engineer` |
| Persona source | `agents/automation-engineer/agent.md` |
| Supporting agents | `codebase-kg-engineer` (`agents/codebase-kg-engineer/agent.md`) |
| Mandatory skills | `python-system-scripting`, `error-handling-patterns`, `logging-patterns`, `codebase-knowledge-graph` |
| Confidence | **MEDIUM** |

Narrow fix: re-run build_master.py --full, validate.py and test_invariant_checker.py in a second repo and make three count sources agree. That is Python build-script operation (automation-engineer); codebase-kg-engineer supports on graph-artifact invariants.

### V2-003 (#259) - PRD NFR-1 / SRS NFR-7: build the per-component process-count measurement harness

| Field | Value |
|-------|-------|
| Gate | D6 |
| Primary agent | `harness-evaluation-engineer` |
| Persona source | `agents/harness-evaluation-engineer/agent.md` |
| Supporting agents | `performance-testing-engineer` (`agents/performance-testing-engineer/agent.md`) |
| Mandatory skills | `eval-harness-design-core`, `deterministic-replay-trace-core`, `agent-regression-harness-core`, `performance-testing-core` |
| Confidence | **HIGH** |

Build an observability/measurement harness over an agentic tool harness, with a pass/fail regression gate. performance-testing-engineer supports on measurement rigour: cold vs warm reported separately, window must not cross a response-turn boundary.

### V2-004 (#260) - PRD FR-1 / SRS FR-10: produce docs/reports/policy-implementation-audit-v2.md

| Field | Value |
|-------|-------|
| Gate | D1 |
| Primary agent | `business-analyst-agent` |
| Persona source | `agents/business-analyst-agent/agent.md` |
| Supporting agents | `codebase-archaeology-agent` (`agents/codebase-archaeology-agent/agent.md`)<br>`technical-writer-agent` (`agents/technical-writer-agent/agent.md`) |
| Mandatory skills | `business-requirements-analysis-core`, `requirements-traceability-core`, `codebase-archaeology`, `technical-writing-core` |
| Confidence | **HIGH** |

A 46-row audit matrix where every row carries an Evidence cell citing file:line or explicit NONE is a requirements-traceability matrix. codebase-archaeology-agent supports the code-side evidence hunt.

**CHANGED 2026-08-02 - agent added, confidence unchanged.** GAP-3 recorded that the matrix half was owned but the surrounding prose of `policy-implementation-audit-v2.md` was not. `technical-writer-agent` now owns it: `technical-writing-core` section 1 supplies the Diataxis two-axis classification that decides whether an audit report is Reference or Explanation before a sentence is written, and section 2 supplies task-based information architecture and inverted-pyramid ordering for the report body. Added to this row only. V2-005, V2-006 and V2-007 are matrix-cell population with no prose deliverable and V2-008 is a script, so all four are untouched.

### V2-005 (#261) - PRD FR-2 / SRS FR-11: populate all 7 audit-matrix columns for all 46 policies

| Field | Value |
|-------|-------|
| Gate | D1 |
| Primary agent | `business-analyst-agent` |
| Persona source | `agents/business-analyst-agent/agent.md` |
| Supporting agents | none - single capability |
| Mandatory skills | `requirements-traceability-core`, `business-requirements-analysis-core` |
| Confidence | **HIGH** |

Populate the 7th column across 46 rows from a fixed closed vocabulary. Pure traceability-matrix completion, no second capability needed.

### V2-006 (#262) - PRD FR-3 / SRS FR-12: record a disposition and rationale for each of the 15 hook-coupled policies

| Field | Value |
|-------|-------|
| Gate | D1 |
| Primary agent | `business-analyst-agent` |
| Persona source | `agents/business-analyst-agent/agent.md` |
| Supporting agents | `solution-architect` (`agents/solution-architect/agent.md`) |
| Mandatory skills | `requirements-traceability-core`, `business-requirements-analysis-core`, `system-design` |
| Confidence | **HIGH** |

A disposition-plus-rationale ledger over 15 hook-coupled policies. solution-architect supports because port-to-MCP / demote-to-advisory / delete are architecture decisions, and push_gate.py's row is pre-decided as port-to-MCP.

### V2-007 (#263) - PRD FR-20 / SRS FR-32: record a post-plugin disposition for all 14 genuine policy orphans

| Field | Value |
|-------|-------|
| Gate | D1 |
| Primary agent | `business-analyst-agent` |
| Persona source | `agents/business-analyst-agent/agent.md` |
| Supporting agents | `automation-engineer` (`agents/automation-engineer/agent.md`) |
| Mandatory skills | `requirements-traceability-core`, `python-system-scripting` |
| Confidence | **HIGH** |

Disposition for 14 orphan policies plus a name-reconciliation script; BA owns the disposition semantics, automation-engineer owns the comparison script.

### V2-008 (#264) - PRD NFR-4 / SRS NFR-10: cross-check all 27 capability_loss.md names against the audit matrix

| Field | Value |
|-------|-------|
| Gate | D1 |
| Primary agent | `automation-engineer` |
| Persona source | `agents/automation-engineer/agent.md` |
| Supporting agents | `business-analyst-agent` (`agents/business-analyst-agent/agent.md`) |
| Mandatory skills | `python-system-scripting`, `error-handling-patterns`, `requirements-traceability-core` |
| Confidence | **MEDIUM** |

The deliverable is a script that fails on an empty disposition and on the literal value 'disappeared'. Script authoring is automation-engineer; BA supports on what a valid disposition is. No agent in the library owns coverage-ledger cross-checking as a named capability.

---

## Batch B (2 issues)

The paired call-graph fix. V2-009 and V2-010 ship together or not at all.

### V2-009 (#265) - PRD FR-9a / SRS FR-21: fix call-graph DISCOVERY truncation

| Field | Value |
|-------|-------|
| Gate | D4 |
| Primary agent | `ast-graph-engineer` |
| Persona source | `agents/ast-graph-engineer/agent.md` |
| Supporting agents | `harness-evaluation-engineer` (`agents/harness-evaluation-engineer/agent.md`)<br>`unit-testing-specialist` (`agents/unit-testing-specialist/agent.md`) |
| Mandatory skills | `ast-call-graph-engineering`, `codebase-archaeology`, `dead-code-detection`, `agent-regression-harness-core`, `deterministic-replay-trace-core`, `unit-testing-core`, `mutation-testing-core` |
| Confidence | **HIGH** |

The parser half (discovery caps at call_graph_builder_legacy.py:64 and graph_model.py:43) is ast-graph-engineer's core domain. The strengthened AC is test engineering as much as parser work, so it needs BOTH supporting agents: harness-evaluation-engineer for the probe harness and module-scoped log capture, unit-testing-specialist for the independent enumeration oracle and the negative test that proves the check can fail. SIZE FLAG: the 5-point estimate does not hold with the runtime-proof AC.

### V2-010 (#266) - PRD FR-9b / SRS FR-38: fix the call-graph RESOLVER ambiguous bare-name bind

| Field | Value |
|-------|-------|
| Gate | D4 |
| Primary agent | `ast-graph-engineer` |
| Persona source | `agents/ast-graph-engineer/agent.md` |
| Supporting agents | `impact-analysis-agent` (`agents/impact-analysis-agent/agent.md`) |
| Mandatory skills | `ast-call-graph-engineering`, `codebase-archaeology`, `change-impact-analysis` |
| Confidence | **HIGH** |

graph_model.py:265 returning candidates[0] for an ambiguous bare name is exactly call-graph edge-resolution precision (the CHA -> RTA refinement axis). impact-analysis-agent supports because the four fan-in consumers being corrected are danger_zones / hot_nodes blast-radius consumers.

---

## Batch C (4 issues)

The flagship selector. Hard prerequisite: both batch B issues must have landed.

### V2-011 (#267) - PRD FR-10 / SRS FR-22: KG-driven agent and skill selection, zero hardcoded lists

| Field | Value |
|-------|-------|
| Gate | D4 |
| Primary agent | `harness-engineering-architect` |
| Persona source | `agents/harness-engineering-architect/agent.md` |
| Supporting agents | `codebase-kg-engineer` (`agents/codebase-kg-engineer/agent.md`)<br>`python-backend-engineer` (`agents/python-backend-engineer/agent.md`) |
| Mandatory skills | `agent-routing-dispatch-policy-core`, `tool-call-mediation-core`, `codebase-knowledge-graph`, `ast-call-graph-engineering`, `python-core` |
| Confidence | **HIGH** |

A selector that ranks agents from a knowledge graph with zero hardcoded name literals is agent-routing-dispatch-policy work. codebase-kg-engineer supports on typed-graph edge-path traversal and on verifying edge paths against ast_call_graph.json or a rebuilt FR-9a-fixed graph; python-backend-engineer supplies the implementation in this Python codebase.

### V2-012 (#268) - PRD FR-11 / SRS FR-23: emit selection explainability, five fields per selected agent

| Field | Value |
|-------|-------|
| Gate | D4 |
| Primary agent | `graph-orchestration-runtime-engineer` |
| Persona source | `agents/graph-orchestration-runtime-engineer/agent.md` |
| Supporting agents | `harness-engineering-architect` (`agents/harness-engineering-architect/agent.md`) |
| Mandatory skills | `graph-observability-error-handling-core`, `agent-routing-dispatch-policy-core` |
| Confidence | **MEDIUM** |

Five auditable fields emitted per selected agent during a full LangGraph pipeline run is graph-runtime observability. harness-engineering-architect supports on what a selection record must contain. Confidence is MEDIUM because no agent owns decision-provenance schema design as a named capability.

### V2-013 (#269) - PRD FR-12 / SRS FR-24: explicit no-match and low-confidence fallback path

| Field | Value |
|-------|-------|
| Gate | D4 |
| Primary agent | `harness-engineering-architect` |
| Persona source | `agents/harness-engineering-architect/agent.md` |
| Supporting agents | none - single capability |
| Mandatory skills | `agent-routing-dispatch-policy-core`, `stop-condition-budget-control-core` |
| Confidence | **HIGH** |

Defining the no-match / below-threshold outcome so a silent default pick is impossible is dispatch-policy design; the threshold and the explicit stop outcome are both in this agent's mandatory skill set.

### V2-014 (#270) - PRD FR-13 / SRS FR-25: conform to the model fallback protocol

| Field | Value |
|-------|-------|
| Gate | D4 |
| Primary agent | `multi-model-router-architect` |
| Persona source | `agents/multi-model-router-architect/agent.md` |
| Supporting agents | `harness-engineering-architect` (`agents/harness-engineering-architect/agent.md`) |
| Mandatory skills | `multi-model-routing-core`, `model-capability-profiling-core`, `retry-backoff-circuit-breaker-core` |
| Confidence | **HIGH** |

haiku -> sonnet -> opus -> escalate is a cascade router topology with confidence gates, which is this agent's stated design surface. harness-engineering-architect supports on the rate-limit retry/escalation mechanics.

---

## Batch D (3 issues)

Plugin manifest and the MCP registration command pair, which everything downstream depends on.

### V2-015 (#271) - PRD FR-14 / SRS FR-26: build the installable plugin manifest, zero hooks, zero .mcp.json

| Field | Value |
|-------|-------|
| Gate | D5 |
| Primary agent | `claude-code-plugin-engineer` |
| Persona source | `agents/claude-code-plugin-engineer/agent.md` |
| Supporting agents | `architecture-conformance-auditor` (`agents/architecture-conformance-auditor/agent.md`) |
| Mandatory skills | `claude-code-plugin-packaging-core`, `architecture-fitness-function-core`, `github-actions-ci`, `system-design` |
| Confidence | **HIGH** (was LOW) |

**CHANGED 2026-08-02 - GAP-1 CLOSED, LOW -> HIGH, primary agent replaced.**

What lifted it, specifically:

- The manifest half of the AC. `claude-code-plugin-packaging-core` section 1 fixes the manifest at `.claude-plugin/plugin.json`, states the permitted field set is capped at **eight fields** and is validated closed-world ("reference marketplace CI pipelines validate `plugin.json` by REJECTING any property outside that set"), and names `name`, `version` (semver string), `description` and `author` in a field table. The AC's required `name` + `description` + explicit semver `version` are three of those four. The agent carries this as Operating Rule 2, which escalates an out-of-schema key to "a hard rejection of the whole manifest ... not a warning to note and move past".
- The zero-hooks half. Section 3 derives hook composition as merge rather than override and states the consequence in the agent's own terms: "Because merge produces a FLAT, UNLABELED union at execution time ... there is no metadata surviving the merge that says 'this particular handler came from plugin X'", proved as an impossibility in M3, with "the only control surface exposed to the user is therefore whole-plugin enable/disable". That is exactly the fact that forced ADR-010, and it is now the agent's Operating Rule 5 and MUST NOT 1.
- The discovery half, which the AC's part (a) depends on. Section 1 lists the nine fixed root-level names and flags nesting `commands/`, `agents/` or `skills/` inside `.claude-plugin/` as "the single most common authoring mistake ... a plugin authored this way will install cleanly ... but expose ZERO discovered capabilities".

`architecture-conformance-auditor` is retained unchanged for the CI-gate half the AC names by capability. `release-engineering-specialist` was dropped: the only thing it was carrying was "explicit semver", which is now one field in a schema the primary agent owns.

**Residual prompt input, and it is not domain knowledge.** The CONFIRMED-list contract in `orchestration_prompt.md` section 1.4 and the measured "2 confirmed spawns" figure are project artefacts that any row would cite. Note also that the eager-spawn rationale for shipping zero `.mcp.json` lives in `mcp-server-engineering-core` section 3 and M6, **not** in the plugin skill - the plugin skill only says a bundled `.mcp.json` is wired into the session's MCP server registry at install. If the dispatcher wants the ADR-019 argument in one persona, add `mcp-server-engineer` as a second supporting agent.

### V2-016 (#272) - SRS FR-37 / ADR-019: build register-mcp and unregister-mcp

| Field | Value |
|-------|-------|
| Gate | D5 |
| Primary agent | `mcp-server-engineer` |
| Persona source | `agents/mcp-server-engineer/agent.md` |
| Supporting agents | none - single capability |
| Mandatory skills | `mcp-server-engineering-core`, `python-system-scripting`, `error-handling-patterns`, `logging-patterns` |
| Confidence | **MEDIUM** (was LOW) |

**CHANGED 2026-08-02 - GAP-2 PARTIALLY CLOSED, LOW -> MEDIUM, primary agent replaced. Deliberately not lifted to HIGH.**

What lifted it, specifically:

- User-scope registration. `mcp-server-engineering-core` section 3 names the surface exactly: "**User scope - the `mcpServers` block inside `~/.claude/settings.json`** (or `settings.local.json` for machine-only, uncommitted entries)", alongside the project-scope `.mcp.json` alternative. This is the registration format the row previously instructed the dispatcher to paste in.
- The round trip. Same section: "Registering a server is a pure configuration mutation - nothing spawns at registration time ... Unregistering (deleting the entry) is the exact mirror". That is the AC's reversibility and reachable-then-unreachable-again clause stated as a property of the platform.
- Merge-against-fresh-read, by name. Section 4 titles the first mitigation `Re-read immediately before writing ("merge against fresh read")` and - more valuably than the bare technique - marks it honestly as "a *probabilistic* improvement, not a correctness guarantee", then ranks optimistic concurrency and OS-level locking above it. It also carries the warning the ADV-008 discussion most needs: atomic rename-into-place "does **not** by itself solve the lost-update problem between two independent read-modify-write sequences", and is "platform-fragile on Windows". The agent encodes this as Core Responsibility 6, Operating Rules 7 and 8, and MUST NOT 3 ("this is the minimum mitigation, not an optional hardening").

**Why this is MEDIUM and not HIGH - two named residuals.**

1. **The `mcp-base` amendment did not land.** `library_gap_spec.md`'s AMENDMENT (commit `0974e4d`) required the skill to be written against the 21 existing servers and to name `MCPResponse`, `@mcp_tool_handler`, `AtomicJsonStore` and `LazyClient`, plus the vendored-by-copy propagation hazard. Grep-verified on 2026-08-02: **zero occurrences** of `mcp-base`, `mcp_base`, `AtomicJsonStore`, `MCPResponse`, `mcp_tool_handler`, `LazyClient` or `vendored` across all seven delivered files. The agent therefore teaches the correct technique and will implement a **new** write-safety helper, when `AtomicJsonStore` (`mcp_base/persistence.py:26`) already implements a thread-safe atomic read-modify-write with write-to-temp-then-rename. Since ADV-008 already flags a shared write-safety helper as an ESCALATION CANDIDATE, a 22nd private implementation is a real cost, not a cosmetic one. It is a reuse-discovery gap, not a correctness gap: section 4 alone would still produce a correct implementation.
2. **ADR-020 Path C has no owner in the library, new agents included.** The one-shot verification at `hld_v2.md:804` (re-anchored 2026-08-02; was cited as 773, stale by document growth -- see REVIEW-INDEX correction 28) is a measurement task, not an MCP-engineering task. Nothing delivered addresses it.

**Prompt notes required (two lines, both project facts):** (a) reuse `AtomicJsonStore` from the vendored `base/` rather than writing a new helper, and note that `mcp-base` is vendored by copy so fixing one copy reaches nothing else; (b) perform and record the ADR-020 Path C verification at the only moment it can be performed.

### V2-017 (#273) - SRS NFR-12 / ADR-020: PREVENT and DETECT layers on the push gate

| Field | Value |
|-------|-------|
| Gate | D5 |
| Primary agent | `mcp-server-engineer` |
| Persona source | `agents/mcp-server-engineer/agent.md` |
| Supporting agents | `site-reliability-engineer` (`agents/site-reliability-engineer/agent.md`) |
| Mandatory skills | `mcp-server-engineering-core`, `python-system-scripting`, `logging-patterns`, `observability-engineering-core` |
| Confidence | **HIGH** (was MEDIUM) |

Layer 1 (unregister-mcp refuses by default, names the consequence, states two ways forward) is a CLI guard. Layer 2 (doctor command plus a cheap startup precondition emitting one unmissable line, without spawning a process) is detective-control and signal design, which is site-reliability-engineer's observability surface.

**CHANGED 2026-08-02 - GAP-2 CLOSED for this row, MEDIUM -> HIGH, primary agent replaced.** Layer 1 acts on the unregistration write path, which is `mcp-server-engineer` Core Responsibility 6 verbatim ("implement the write path that adds or removes a server entry"). Layer 2's hardest constraint - a startup precondition that must not spawn a process - is answered directly by `mcp-server-engineering-core` section 3: registration state is pure configuration and "a stdio server's child process is spawned only when an active session that has the entry in its resolved configuration actually needs it", so the precondition is a config read by construction. `automation-engineer` was dropped as primary because the registration-CLI write path it was standing in for is now owned by name; `site-reliability-engineer` is retained unchanged for the detective-control and one-unmissable-line signal design.

---

## Batch E (6 issues)

Path hygiene, snapshot bundling, and the uninstall lifecycle.

### V2-018 (#274) - PRD FR-15 / SRS FR-28: AST-classify every home-directory occurrence, then remediate the CODE ones

| Field | Value |
|-------|-------|
| Gate | D5 |
| Primary agent | `static-analysis-engineer` |
| Persona source | `agents/static-analysis-engineer/agent.md` |
| Supporting agents | `python-backend-engineer` (`agents/python-backend-engineer/agent.md`) |
| Mandatory skills | `static-code-analysis-engine-core`, `linting-style-governance-core`, `python-core` |
| Confidence | **HIGH** |

An AST rule engine that partitions occurrences by enclosing node type (ast.arguments.defaults, ast.Call keyword, assignment RHS, docstring position, tokenize.COMMENT) is exactly static-code-analysis-engine-core, and the exemption of src/utils/path_resolver.py is suppression/exemption governance. python-backend-engineer supports on the remediation edits. Task 2 cannot be sized until task 1 runs.

### V2-019 (#275) - PRD FR-17 / SRS FR-30: pass encoding= at every text-mode open()

| Field | Value |
|-------|-------|
| Gate | D5 |
| Primary agent | `static-analysis-engineer` |
| Persona source | `agents/static-analysis-engineer/agent.md` |
| Supporting agents | none - single capability |
| Mandatory skills | `static-code-analysis-engine-core`, `linting-style-governance-core` |
| Confidence | **HIGH** |

A detection rule that must catch the mode-less open(path) form and carry a binary/tarfile/urllib exemption list, applied over 19 sites, is a linter rule with a suppression budget. No second capability needed.

### V2-020 (#276) - PRD FR-16 / SRS FR-29: build-time library snapshot script

| Field | Value |
|-------|-------|
| Gate | D5 |
| Primary agent | `release-engineering-specialist` |
| Persona source | `agents/release-engineering-specialist/agent.md` |
| Supporting agents | `automation-engineer` (`agents/automation-engineer/agent.md`)<br>`devsecops-engineer` (`agents/devsecops-engineer/agent.md`)<br>`claude-code-plugin-engineer` (`agents/claude-code-plugin-engineer/agent.md`) |
| Mandatory skills | `release-versioning-management-core`, `github-actions-ci`, `python-system-scripting`, `devsecops-core`, `claude-code-plugin-packaging-core` |
| Confidence | **MEDIUM** (unchanged) |

A pinned build-time snapshot with a staleness check against the library VERSION and a release script that FAILS when CLAUDE_PLUGIN_DEV_MODE is set is release-pipeline work. automation-engineer supports on the snapshot script; devsecops-engineer supports on ADV-006, running secrets_check.py against the snapshot artifact rather than only the source tree.

**CHANGED 2026-08-02 - agent added, confidence deliberately UNCHANGED.** `claude-code-plugin-packaging-core` section 4 supplies the one plugin fact this row needed: the snapshot ships inside the plugin and must be located through `${CLAUDE_PLUGIN_ROOT}`, never a CWD-relative path. M6's correct-by-construction vs correct-by-coincidence proof describes this row's exact latent defect - "an author testing locally is ... almost always running FROM the plugin's own repository root, so CWD-relative paths resolve correctly BY COINCIDENCE during every test the author runs", breaking only once installed under `~/.claude/plugins/<hash>/`. This is **not** a confidence lift: the stated reason this row was MEDIUM is the multi-way capability split (release pipeline / snapshot script / ADV-006 secrets scan), which is unchanged and is now four-way rather than three. If the dispatcher caps supporting agents at two, drop `devsecops-engineer` first - ADV-006 is a single `secrets_check.py` invocation against a different input path.

### V2-021 (#277) - PRD FR-24 / SRS FR-36: publish the uninstall-residue runbook

| Field | Value |
|-------|-------|
| Gate | D5 |
| Primary agent | `technical-writer-agent` |
| Persona source | `agents/technical-writer-agent/agent.md` |
| Supporting agents | `claude-code-plugin-engineer` (`agents/claude-code-plugin-engineer/agent.md`) |
| Mandatory skills | `technical-writing-core`, `procedural-documentation-core`, `claude-code-plugin-packaging-core` |
| Confidence | **HIGH** (was LOW) |

**CHANGED 2026-08-02 - GAP-3 CLOSED, LOW -> HIGH, primary agent replaced. This is the cleanest lift in the set.**

The stated reason this row was LOW was that the library's only runbook skill fires from incident telemetry after a production incident, and "the skill's shape is right; its trigger and inputs are wrong." The delivered agent answers that objection by name, in its own text:

> **Distinct from `postmortem-facilitator-agent`.** That agent GENERATES diagnostic runbooks by MINING a corpus of historical incident telemetry ... This agent AUTHORS documentation - including runbooks - PROACTIVELY, from a process a human already understands, independent of and typically before any specific incident corpus exists ... use this agent when the starting point is a known process that needs to be written down correctly; hand off to `postmortem-facilitator-agent` when the starting point is a corpus of past incidents.

V2-021 is unambiguously the former: a measured residue list and a manual removal procedure, no incident, no telemetry, no root cause.

What supplies the craft:

- `procedural-documentation-core` section 1 gives the six-part runbook anatomy as a required ordered structure - purpose, preconditions, numbered steps where "each step is ONE atomic action, never a paragraph of options", verification points, a distinctly labelled rollback section, and an escalation path. The AC's "manual removal steps for each" measured path maps onto steps-plus-verification-points directly.
- Section 3 grounds a verification point as the literal Hoare postcondition of its step rather than a vague "make sure it worked", which is what makes "this path is now gone" checkable per item.
- Section 2's 5 A's include **Accurate** ("matches the CURRENT state of the system, not a stale prior version"), which is the AC's third clause about no stale placeholder text.

`claude-code-plugin-engineer` supports because the residue list is a plugin-lifecycle fact set, not prose: `claude-code-plugin-packaging-core` section 2 documents the orphaned-version cache under `~/.claude/plugins/` and its 7-day retention window, and states plainly that this "does not address residue the plugin left behind in systems it merged into" with "no documented mechanism ... for verifying COMPLETE removal". M4 derives why `enabledPlugins` / `extraKnownMarketplaces` residue is not cleanly attributable. That lets the writer verify the measured list rather than transcribe it.

`postmortem-facilitator-agent` no longer appears anywhere in this routing table.

### V2-022 (#278) - PRD FR-18 / SRS FR-31: zero plugin-attributable functional residue after uninstall

| Field | Value |
|-------|-------|
| Gate | D5 |
| Primary agent | `claude-code-plugin-engineer` |
| Persona source | `agents/claude-code-plugin-engineer/agent.md` |
| Supporting agents | `integration-testing-engineer` (`agents/integration-testing-engineer/agent.md`) |
| Mandatory skills | `claude-code-plugin-packaging-core`, `integration-testing-core`, `contract-testing-core`, `python-system-scripting` |
| Confidence | **HIGH** (was MEDIUM) |

Part (a), leaving no plugin-attributable functional residue, is uninstall-path behaviour in the command layer. Part (b), asserting a settings.json delta attributable to the plugin rather than whole-file equality, is integration/contract test design.

**CHANGED 2026-08-02 - GAP-1 CLOSED for this row, MEDIUM -> HIGH, primary agent replaced.** The load-bearing word in this AC is "attributable", and that is precisely what M4 of `claude-code-plugin-packaging-core` derives: the four-scope precedence-resolution function makes a plugin's effective state "a MERGE across up to four files, not one row in one table", so uninstall is not a total subtraction. Section 2 states the mechanism in plain terms - "the install did not confine its effects to files the plugin exclusively owns; it merged contributions into systems other plugins (and the user's own configuration) also write to". That is the reasoning that narrowed FR-18 away from whole-file equality and added FR-24. The agent carries it as Core Responsibility 8 (uninstall-residue risk assessment), Operating Rule 6 ("Never assert that 'uninstall' is a clean, total subtraction") and MUST NOT 3 and 5. `integration-testing-engineer` is retained unchanged for part (b)'s delta assertion.

### V2-023 (#279) - PRD NFR-5 / SRS NFR-11: install, invoke, uninstall and register round-trip lifecycle tests

| Field | Value |
|-------|-------|
| Gate | D5 |
| Primary agent | `acceptance-testing-bdd-engineer` |
| Persona source | `agents/acceptance-testing-bdd-engineer/agent.md` |
| Supporting agents | `integration-testing-engineer` (`agents/integration-testing-engineer/agent.md`) |
| Mandatory skills | `bdd-acceptance-testing-core`, `acceptance-testing-bdd-core`, `test-automation-architecture-core`, `integration-testing-core` |
| Confidence | **HIGH** |

Gherkin scenarios for install/invoke/uninstall are already written in prd-v2.md section 7, and this agent implements Behave step definitions from Gherkin specs. integration-testing-engineer supports on the register/unregister round trip that crosses a process boundary.

---

## Batch F (3 issues)

The push-gate port and its CI assertion. Both must exist before batch G deletes anything.

### V2-024 (#280) - PRD FR-23 / SRS FR-35: port push_gate.py to a named MCP tool BEFORE PreToolUse is deleted

| Field | Value |
|-------|-------|
| Gate | D6 |
| Primary agent | `mcp-server-engineer` |
| Persona source | `agents/mcp-server-engineer/agent.md` |
| Supporting agents | `python-backend-engineer` (`agents/python-backend-engineer/agent.md`)<br>`integration-testing-engineer` (`agents/integration-testing-engineer/agent.md`) |
| Mandatory skills | `mcp-server-engineering-core`, `api-design-core`, `contract-testing-core`, `python-core` |
| Confidence | **HIGH** (was LOW) |

**CHANGED 2026-08-02 - GAP-2 CLOSED for this row, LOW -> HIGH, primary agent replaced.**

The AC's first clause is "reachable as an MCP tool callable by name", and "reachable by name" is now a defined capability rather than a phrase the dispatcher had to explain:

- `mcp-server-engineering-core` section 1 gives the primitive triad table - `tools/list` to enumerate, `tools/call` to invoke, `notifications/tools/list_changed` to refresh - and the rule that "a server declares which of these three it supports in its `initialize` response's `capabilities` object", which is what makes a tool reachable at all.
- Section 2 gives the descriptor shape (`name`, `description`, `inputSchema`, optional `outputSchema`), the verb-object naming convention with the exact example form `get_pull_request_status`, and the requirement that a description "must state **both** what the tool does **and** when a model should reach for it".
- The agent's Core Responsibility 1 owns the schema and its `ToolAnnotations`; Core Responsibility 9 owns the contract tests asserting schema conformance, which is the AC's second clause.

The agent's own Agent Priority draws the boundary this row needs: "Do NOT invoke this agent for the business logic a tool merely wraps". `python-backend-engineer` is therefore retained - demoted from primary to supporting - for `push_gate.py`'s own logic, and `integration-testing-engineer` is retained for the contract-equivalence AC. The row went from having no owner for the MCP layer to having a named owner for each of its three parts.

### V2-025 (#281) - ADR-017: build the assert_push_gate_reachable() CI assertion

| Field | Value |
|-------|-------|
| Gate | D6 |
| Primary agent | `architecture-conformance-auditor` |
| Persona source | `agents/architecture-conformance-auditor/agent.md` |
| Supporting agents | `unit-testing-specialist` (`agents/unit-testing-specialist/agent.md`) |
| Mandatory skills | `architecture-fitness-function-core`, `unit-testing-core`, `mutation-testing-core` |
| Confidence | **HIGH** |

assert_push_gate_reachable() is an architecture fitness function run in CI that asserts on the replacement's reachability and must not assert on the old hook's presence. unit-testing-specialist supports on the mandatory companion negative test proving the assertion can fail.

### V2-026 (#282) - PRD FR-7 / SRS FR-17: six explicit slash-command entry points

| Field | Value |
|-------|-------|
| Gate | D6 |
| Primary agent | `claude-code-plugin-engineer` |
| Persona source | `agents/claude-code-plugin-engineer/agent.md` |
| Supporting agents | `automation-engineer` (`agents/automation-engineer/agent.md`)<br>`graph-orchestration-runtime-engineer` (`agents/graph-orchestration-runtime-engineer/agent.md`) |
| Mandatory skills | `claude-code-plugin-packaging-core`, `python-system-scripting`, `linux-shell-scripting`, `graph-orchestration-framework-comparison-core` |
| Confidence | **HIGH** (was MEDIUM) |

Six named command entry points is CLI-surface construction. graph-orchestration-runtime-engineer supports because the sixth command drives the full LangGraph pipeline Steps 0 through 8 in order. Each command must also carry V2-017's non-spawning startup check.

**CHANGED 2026-08-02 - GAP-1 CLOSED for this row, MEDIUM -> HIGH, primary agent replaced.** Six slash commands are only entry points if discovery finds them, and that was the missing half. `claude-code-plugin-packaging-core` section 1 fixes `commands/` at the plugin ROOT among the nine known names and names the failure mode explicitly: nesting it under `.claude-plugin/` yields a plugin that "will install cleanly (the manifest is well-formed) but expose ZERO discovered capabilities, a silent failure that is easy to miss because nothing errors; the plugin simply does nothing". Section 4 then requires each command definition to reference its own bundled script through `${CLAUDE_PLUGIN_ROOT}`. The agent carries both as Operating Rules 1 and 4 and as Core Responsibilities 2 and 5. `automation-engineer` is retained - demoted from primary to supporting - for the Python behind the commands; `graph-orchestration-runtime-engineer` is retained unchanged.

---

## Batch G (9 issues)

The deletions and the durability/resilience work that must survive them.

### V2-027 (#283) - PRD FR-4 / SRS FR-13: delete the PreToolUse and PostToolUse hook registrations

| Field | Value |
|-------|-------|
| Gate | D6 |
| Primary agent | `automation-engineer` |
| Persona source | `agents/automation-engineer/agent.md` |
| Supporting agents | `impact-analysis-agent` (`agents/impact-analysis-agent/agent.md`) |
| Mandatory skills | `python-system-scripting`, `error-handling-patterns`, `change-impact-analysis` |
| Confidence | **MEDIUM** |

The action is a settings.json registration removal; the risk is what goes dark. impact-analysis-agent supports on confirming the measured 135-of-2218-node blast radius and zero surviving cross-boundary edges. Do not start until all five blockers have landed.

### V2-028 (#284) - PRD FR-5 / SRS FR-15: take UserPromptSubmit off the every-prompt hot path

| Field | Value |
|-------|-------|
| Gate | D6 |
| Primary agent | `automation-engineer` |
| Persona source | `agents/automation-engineer/agent.md` |
| Supporting agents | none - single capability |
| Mandatory skills | `python-system-scripting`, `error-handling-patterns` |
| Confidence | **MEDIUM** |

Removing UserPromptSubmit from the every-prompt path is the same registration-surface edit as V2-027, gated on V2-026 existing. No second capability needed.

### V2-029 (#285) - PRD FR-4a / SRS FR-14: record the blast-radius measurement and its three named consequences

| Field | Value |
|-------|-------|
| Gate | D6 |
| Primary agent | `solution-architect` |
| Persona source | `agents/solution-architect/agent.md` |
| Supporting agents | `impact-analysis-agent` (`agents/impact-analysis-agent/agent.md`) |
| Mandatory skills | `system-design`, `change-impact-analysis` |
| Confidence | **HIGH** |

The deliverable is ADR-006 body content cross-referencing three named consequences, which is ADR authorship. impact-analysis-agent supports on the blast-radius measurement being recorded.

### V2-030 (#286) - PRD FR-22 / SRS FR-34: add the SRS Change Log row dated to the hook-deletion PR

| Field | Value |
|-------|-------|
| Gate | D6 |
| Primary agent | `business-analyst-agent` |
| Persona source | `agents/business-analyst-agent/agent.md` |
| Supporting agents | none - single capability |
| Mandatory skills | `requirements-traceability-core`, `business-requirements-analysis-core` |
| Confidence | **HIGH** |

An append-only SRS Change Log row referencing a superseding FR by number is requirements-document lifecycle work. The row must be dated to the hook-deletion PR, not back-dated.

### V2-031 (#287) - PRD NFR-3 / SRS NFR-9: name the CheckpointManager contract and fix 3 durability defects

| Field | Value |
|-------|-------|
| Gate | D6 |
| Primary agent | `graph-orchestration-runtime-engineer` |
| Persona source | `agents/graph-orchestration-runtime-engineer/agent.md` |
| Supporting agents | `distributed-consensus-engineer` (`agents/distributed-consensus-engineer/agent.md`) |
| Mandatory skills | `checkpointing-persistence-architecture-core`, `human-in-the-loop-interrupt-resume-core`, `graph-observability-error-handling-core`, `distributed-transactions-core` |
| Confidence | **HIGH** |

Naming the CheckpointManager contract, refusing a best-effort checkpoint write, and making the progress surface a projection rather than a second writer is checkpointing-persistence architecture on a LangGraph runtime. distributed-consensus-engineer supports on defect 3, replay idempotency for side-effecting steps under a session-id-plus-step-number key.

### V2-032 (#288) - PRD FR-8 / SRS FR-18: keep Stop and Notification as user-level registrations, byte-identical across install/uninstall

| Field | Value |
|-------|-------|
| Gate | D6 |
| Primary agent | `integration-testing-engineer` |
| Persona source | `agents/integration-testing-engineer/agent.md` |
| Supporting agents | `claude-code-plugin-engineer` (`agents/claude-code-plugin-engineer/agent.md`) |
| Mandatory skills | `integration-testing-core`, `contract-testing-core`, `claude-code-plugin-packaging-core` |
| Confidence | **HIGH** (was MEDIUM) |

A standing test that an install/uninstall cycle leaves the user-level Stop and Notification entries byte-identical. Lifecycle assertion over a boundary the plugin must never touch.

**CHANGED 2026-08-02 - GAP-1 CLOSED for this row, MEDIUM -> HIGH, supporting agent added.** The stated reason for MEDIUM was "no library agent owns plugin-lifecycle testing specifically". The lifecycle half now has an owner. `claude-code-plugin-packaging-core` section 2's four-scope table places `user` (`~/.claude/settings.json`) as a distinct layer from anything the plugin's own install writes, and section 2 documents the full lifecycle verb set plus the `/reload-plugins` sync step. M4 derives why a merged key cannot be cleanly subtracted, which is exactly the property "byte-identical across install/uninstall" asserts for a key the plugin must never contribute to in the first place. The agent carries this as Core Responsibility 6 (settings-scope attribution) and Operating Rule 8 ("never assume a plugin's effective configuration lives in a single settings.json file"). `integration-testing-engineer` stays primary because the deliverable is a standing test, not a design.

### V2-033 (#289) - PRD FR-8a / SRS FR-19: instrument the Stop hook over 20 invocations and decide each capability

| Field | Value |
|-------|-------|
| Gate | D6 |
| Primary agent | `harness-evaluation-engineer` |
| Persona source | `agents/harness-evaluation-engineer/agent.md` |
| Supporting agents | `performance-testing-engineer` (`agents/performance-testing-engineer/agent.md`) |
| Mandatory skills | `agent-regression-harness-core`, `deterministic-replay-trace-core`, `eval-harness-design-core`, `performance-testing-core` |
| Confidence | **HIGH** |

Instrumenting 20 consecutive REAL Stop-hook invocations for subprocess count, wall-clock duration and which .exists() guards fired is runtime trace capture over an agent harness, with a regression gate at most-2 spawns. A static re-derivation does not satisfy it. performance-testing-engineer supports on the per-invocation timing methodology.

### V2-034 (#290) - PRD FR-21 / SRS FR-33: fix or formally retire the 7 dead Stop-hook script references

| Field | Value |
|-------|-------|
| Gate | D6 |
| Primary agent | `codebase-archaeology-agent` |
| Persona source | `agents/codebase-archaeology-agent/agent.md` |
| Supporting agents | `business-analyst-agent` (`agents/business-analyst-agent/agent.md`) |
| Mandatory skills | `dead-code-detection`, `codebase-archaeology`, `requirements-traceability-core` |
| Confidence | **MEDIUM** |

Seven references in hooks/stop_notifier/ that point at files absent from disk are dangling references, which is dead-code-detection territory. business-analyst-agent supports because the retirement path requires each lost capability to appear with a disposition in the FR-12 / NFR-10 ledger.

### V2-035 (#291) - PRD NFR-2 / SRS NFR-8: replace fixed pipeline timeouts with 5 non-temporal control mechanisms

| Field | Value |
|-------|-------|
| Gate | D6 |
| Primary agent | `harness-engineering-architect` |
| Persona source | `agents/harness-engineering-architect/agent.md` |
| Supporting agents | `loop-safety-engineer` (`agents/loop-safety-engineer/agent.md`) |
| Mandatory skills | `retry-backoff-circuit-breaker-core`, `stop-condition-budget-control-core`, `agent-loop-lifecycle-core`, `tool-call-mediation-core`, `loop-termination-safety-core` |
| Confidence | **HIGH** |

The best single match in the set: four of the five required ADR-016 mechanisms map directly onto this agent's mandatory skills (attempt-count bound and convergence signal to stop-condition-budget-control-core; circuit breaker with non-fixed reopen-wait and full-jitter retry to retry-backoff-circuit-breaker-core). loop-safety-engineer supports on the no-progress/termination proof. Lease renewal is the one mechanism neither agent owns by name.

---

## Batch H (2 issues)

Release close-out.

### V2-036 (#292) - D7: migration guide, CHANGELOG, and VERSION bump to 2.0.0

| Field | Value |
|-------|-------|
| Gate | D7 |
| Primary agent | `release-engineering-specialist` |
| Persona source | `agents/release-engineering-specialist/agent.md` |
| Supporting agents | `technical-writer-agent` (`agents/technical-writer-agent/agent.md`) |
| Mandatory skills | `release-versioning-management-core`, `github-actions-ci`, `procedural-documentation-core`, `technical-writing-core` |
| Confidence | **HIGH** (unchanged) |

VERSION to 2.0.0, Keep a Changelog with an ISO 8601 date, and SemVer bump determination are this agent's exact lifecycle.

**CHANGED 2026-08-02 - supporting agent CORRECTED, confidence unchanged.** `postmortem-facilitator-agent` was carrying the migration-guide half only because it held the library's one runbook skill, and it was the wrong trigger here for the same reason it was wrong on V2-021. `technical-writer-agent` replaces it. `procedural-documentation-core` section 1 treats a migration guide as a distinct four-part form rather than a runbook variant - pre-migration checklist, phased steps, post-migration verification including a bake-time window, and a rollback/abort plan - and notes that migrations "routinely include steps with no clean inverse". Section 4's point-of-no-return discipline is what makes the 8-step runbook's step-2 "Required before steps 3 and 5" safety property a structural property rather than a sentence to copy. This is a correctness fix to the dispatch, not a confidence lift.

### V2-037 (#293) - Resolve the VERSION vs CLAUDE.md version contradiction

| Field | Value |
|-------|-------|
| Gate | D7 |
| Primary agent | `release-engineering-specialist` |
| Persona source | `agents/release-engineering-specialist/agent.md` |
| Supporting agents | none - single capability |
| Mandatory skills | `release-versioning-management-core` |
| Confidence | **HIGH** |

VERSION is the single source of truth under rules/11 and CLAUDE.md:4 is the stale side. Version-source-of-truth reconciliation is release-versioning-management-core. Closes as absorbed if V2-036 lands first and fixes both.

---

## Agent load distribution (revised 2026-08-02)

Counted as primary assignments. Confirms the work did not collapse onto one generalist.

| Agent | Issues as primary | Was |
|-------|-------------------|-----|
| `business-analyst-agent` | 5 | 5 |
| `automation-engineer` | 4 | 8 |
| `claude-code-plugin-engineer` | 3 | 0 (new) |
| `harness-engineering-architect` | 3 | 3 |
| `mcp-server-engineer` | 3 | 0 (new) |
| `release-engineering-specialist` | 3 | 4 |
| `ast-graph-engineer` | 2 | 2 |
| `graph-orchestration-runtime-engineer` | 2 | 2 |
| `harness-evaluation-engineer` | 2 | 2 |
| `solution-architect` | 2 | 2 |
| `static-analysis-engineer` | 2 | 2 |
| `acceptance-testing-bdd-engineer` | 1 | 1 |
| `architecture-conformance-auditor` | 1 | 1 |
| `codebase-archaeology-agent` | 1 | 1 |
| `integration-testing-engineer` | 1 | 1 |
| `multi-model-router-architect` | 1 | 1 |
| `technical-writer-agent` | 1 | 0 (new) |
| **Total** | **37** | **37** |

17 distinct agents appear as primary (was 16); 26 distinct agents appear across primary and
supporting positions combined (was 24).

Two agents left the primary column. `python-backend-engineer` drops from 1 to 0 as primary
but remains supporting on V2-011, V2-018 and V2-024. `postmortem-facilitator-agent` drops
from 1 to 0 and no longer appears anywhere in this table in any position - it was primary on
V2-021 and supporting on V2-036, and `technical-writer-agent` replaced it in both. That is
the single clearest signal that GAP-3 was a genuine gap: the agent that had been standing in
for it now has no role in this sprint at all.

The most concentrated agent, `automation-engineer`, drops from 8 primaries to 4. Its
remaining four (V2-002, V2-008, V2-027, V2-028) are all genuine Python build/registration
scripting with no plugin or MCP surface.

---

## Before / after confidence distribution - acceptance test result

The acceptance test in `library_gap_spec.md` is: "When those four rows [V2-015, V2-016,
V2-021, V2-024] can be raised to MEDIUM or HIGH with no pasted domain facts, the gap is
closed."

| Confidence | Before (2026-08-02, pre-delivery) | After (2026-08-02, post-delivery) | Delta |
|---|---|---|---|
| HIGH | 22 | 29 | +7 |
| MEDIUM | 11 | 8 | -3 |
| LOW | 4 | 0 | -4 |
| NO MATCH | 0 | 0 | 0 |
| **Total** | **37** | **37** | - |

**ACCEPTANCE TEST: PASS.** All four target rows cleared LOW.

| Row | Before | After | Verdict |
|---|---|---|---|
| V2-015 (#271) | LOW | **HIGH** | Pass. Manifest schema, discovery convention and hook-merge impossibility all delivered. |
| V2-016 (#272) | LOW | **MEDIUM** | Pass, at the floor of the bar. Technique delivered; `mcp-base` reuse and ADR-020 Path C remain as two prompt lines. |
| V2-021 (#277) | LOW | **HIGH** | Pass. The agent rebuts the exact objection that made this row LOW, in its own text. |
| V2-024 (#280) | LOW | **HIGH** | Pass. "Callable by name" is now a defined capability with a named owner. |

Four further rows moved MEDIUM -> HIGH as a second-order effect (V2-017, V2-022, V2-026,
V2-032), all of them GAP-1 or GAP-2 rows whose stated reason for MEDIUM was the missing
capability rather than a capability split.

Two rows changed agents without changing confidence, both deliberately: V2-020 (the MEDIUM
was caused by a multi-way capability split that still stands) and V2-036 (already HIGH; the
supporting agent was simply wrong).

Enumeration check: 4 lifts from LOW + 4 lifts from MEDIUM = 8 confidence changes; 3
agent-only changes (V2-004, V2-020, V2-036); 11 rows revised in total, matching the list in
the Revision section at the top of this file.

---

## Not routed, deliberately

FR-25 and FR-26 remain PROPOSED and carry no GitHub issue. They are absent from
`github_issues.json` and are not routed. Note the collision recorded in V2-014's body:
SRS FR-25 (the model fallback protocol, which IS routed, as V2-014) is a different thing
from the PROPOSED FR-25 in `advisory_items.json`.

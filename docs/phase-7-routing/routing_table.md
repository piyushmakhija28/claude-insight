# Phase 7 Routing Table

All 37 v2.0.0 sprint issues routed to agents and skills from the
claude-global-library master knowledge graph. Grouped by batch, in execution order.

| Property | Value |
|----------|-------|
| Issues routed | 37 of 37 |
| Library version | 29.72.0 |
| Agent catalogue | knowledge-graph/_master/agents_all.json (505 agents) |
| Skill catalogue | knowledge-graph/_master/skills_all.json (992 skills) |
| Distinct agents used | 24 |
| HIGH / MEDIUM / LOW / NO MATCH | 22 / 11 / 4 / 0 |
| Generated | 2026-08-02 |

---

## Name verification method

Every agent name and every skill name below passed BOTH checks before this file was written:

1. **Catalogue membership.** The name is an exact member of
   `knowledge-graph/_master/agents_all.json -> agents[*].name` (505 entries) or
   `knowledge-graph/_master/skills_all.json -> skills[*].name` (992 entries).
2. **Filesystem existence.** `agents/<name>/agent.md` or `skills/<name>/SKILL.md`
   exists on disk in the library checkout.

The two catalogues and the filesystem were reconciled first: 505 of 505 agents in
`agents_all.json` have a directory on disk, 505 of 505 directories on disk appear in the
catalogue, and 992 of 992 skills likewise. There is no name that exists in one and not
the other, so either check alone is sufficient and both were run anyway.

The generator aborts before writing any file if a single name fails either check. No name
here was inferred from a topic, and nothing was sourced from `~/.claude/agents/` or
`~/.claude/skills/`.

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
| Supporting agents | `codebase-archaeology-agent` (`agents/codebase-archaeology-agent/agent.md`) |
| Mandatory skills | `business-requirements-analysis-core`, `requirements-traceability-core`, `codebase-archaeology` |
| Confidence | **HIGH** |

A 46-row audit matrix where every row carries an Evidence cell citing file:line or explicit NONE is a requirements-traceability matrix. codebase-archaeology-agent supports the code-side evidence hunt.

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

### V2-008 (#264) - PRD NFR-4 / SRS NFR-10: cross-check all 25 capability_loss.md names against the audit matrix

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
| Primary agent | `release-engineering-specialist` |
| Persona source | `agents/release-engineering-specialist/agent.md` |
| Supporting agents | `architecture-conformance-auditor` (`agents/architecture-conformance-auditor/agent.md`) |
| Mandatory skills | `release-versioning-management-core`, `github-actions-ci`, `architecture-fitness-function-core` |
| Confidence | **LOW** |

GAP. No agent in the library covers Claude Code plugin packaging or manifest authoring. release-engineering-specialist is closest on the shippable-artifact and explicit-semver half; architecture-conformance-auditor is an exact fit for the ADR-010 CI gate (find for hooks/ returns zero, enforced at CRITICAL) which the AC names in those words.

### V2-016 (#272) - SRS FR-37 / ADR-019: build register-mcp and unregister-mcp

| Field | Value |
|-------|-------|
| Gate | D5 |
| Primary agent | `automation-engineer` |
| Persona source | `agents/automation-engineer/agent.md` |
| Supporting agents | none - single capability |
| Mandatory skills | `python-system-scripting`, `error-handling-patterns`, `logging-patterns` |
| Confidence | **LOW** |

GAP. No MCP-protocol or Claude Code plugin-command agent exists. automation-engineer genuinely covers 'build a reversible CLI command that edits a JSON config safely', which is the merge-against-fresh-read requirement, but it carries no MCP registration knowledge and none of the ADR-020 Path C verification context.

### V2-017 (#273) - SRS NFR-12 / ADR-020: PREVENT and DETECT layers on the push gate

| Field | Value |
|-------|-------|
| Gate | D5 |
| Primary agent | `automation-engineer` |
| Persona source | `agents/automation-engineer/agent.md` |
| Supporting agents | `site-reliability-engineer` (`agents/site-reliability-engineer/agent.md`) |
| Mandatory skills | `python-system-scripting`, `logging-patterns`, `observability-engineering-core` |
| Confidence | **MEDIUM** |

Layer 1 (unregister-mcp refuses by default, names the consequence, states two ways forward) is a CLI guard. Layer 2 (doctor command plus a cheap startup precondition emitting one unmissable line, without spawning a process) is detective-control and signal design, which is site-reliability-engineer's observability surface.

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
| Supporting agents | `automation-engineer` (`agents/automation-engineer/agent.md`)<br>`devsecops-engineer` (`agents/devsecops-engineer/agent.md`) |
| Mandatory skills | `release-versioning-management-core`, `github-actions-ci`, `python-system-scripting`, `devsecops-core` |
| Confidence | **MEDIUM** |

A pinned build-time snapshot with a staleness check against the library VERSION and a release script that FAILS when CLAUDE_PLUGIN_DEV_MODE is set is release-pipeline work. automation-engineer supports on the snapshot script; devsecops-engineer supports on ADV-006, running secrets_check.py against the snapshot artifact rather than only the source tree.

### V2-021 (#277) - PRD FR-24 / SRS FR-36: publish the uninstall-residue runbook

| Field | Value |
|-------|-------|
| Gate | D5 |
| Primary agent | `postmortem-facilitator-agent` |
| Persona source | `agents/postmortem-facilitator-agent/agent.md` |
| Supporting agents | none - single capability |
| Mandatory skills | `postmortem-runbook-engineering-core` |
| Confidence | **LOW** |

GAP. postmortem-runbook-engineering-core is the only runbook-authoring skill in the library and its agent's domain is blameless incident postmortems, not product uninstall procedures. The capability actually needed - author a procedural runbook naming measured residue by exact path - has no owner.

### V2-022 (#278) - PRD FR-18 / SRS FR-31: zero plugin-attributable functional residue after uninstall

| Field | Value |
|-------|-------|
| Gate | D5 |
| Primary agent | `automation-engineer` |
| Persona source | `agents/automation-engineer/agent.md` |
| Supporting agents | `integration-testing-engineer` (`agents/integration-testing-engineer/agent.md`) |
| Mandatory skills | `python-system-scripting`, `integration-testing-core`, `contract-testing-core` |
| Confidence | **MEDIUM** |

Part (a), leaving no plugin-attributable functional residue, is uninstall-path behaviour in the command layer. Part (b), asserting a settings.json delta attributable to the plugin rather than whole-file equality, is integration/contract test design.

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
| Primary agent | `python-backend-engineer` |
| Persona source | `agents/python-backend-engineer/agent.md` |
| Supporting agents | `integration-testing-engineer` (`agents/integration-testing-engineer/agent.md`) |
| Mandatory skills | `python-core`, `api-design-core`, `clean-architecture`, `contract-testing-core` |
| Confidence | **LOW** |

GAP. No MCP-server engineering agent exists. Exposing existing push_gate.py logic as a named, schema-described callable tool is api-design-core work, which python-backend-engineer covers generically. integration-testing-engineer supports because the AC is a contract equivalence: the existing assertions must pass against the new code path.

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
| Primary agent | `automation-engineer` |
| Persona source | `agents/automation-engineer/agent.md` |
| Supporting agents | `graph-orchestration-runtime-engineer` (`agents/graph-orchestration-runtime-engineer/agent.md`) |
| Mandatory skills | `python-system-scripting`, `linux-shell-scripting`, `graph-orchestration-framework-comparison-core` |
| Confidence | **MEDIUM** |

Six named command entry points is CLI-surface construction. graph-orchestration-runtime-engineer supports because the sixth command drives the full LangGraph pipeline Steps 0 through 8 in order. Each command must also carry V2-017's non-spawning startup check.

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
| Supporting agents | none - single capability |
| Mandatory skills | `integration-testing-core`, `contract-testing-core` |
| Confidence | **MEDIUM** |

A standing test that an install/uninstall cycle leaves the user-level Stop and Notification entries byte-identical. Lifecycle assertion over a boundary the plugin must never touch; no library agent owns plugin-lifecycle testing specifically.

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
| Supporting agents | `postmortem-facilitator-agent` (`agents/postmortem-facilitator-agent/agent.md`) |
| Mandatory skills | `release-versioning-management-core`, `github-actions-ci`, `postmortem-runbook-engineering-core` |
| Confidence | **HIGH** |

VERSION to 2.0.0, Keep a Changelog with an ISO 8601 date, and SemVer bump determination are this agent's exact lifecycle. postmortem-facilitator-agent supports on reproducing the 8-step runbook, including step 2's 'Required before steps 3 and 5' safety property, verbatim.

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

## Agent load distribution

Counted as primary assignments. Confirms the work did not collapse onto one generalist.

| Agent | Issues as primary |
|-------|-------------------|
| `automation-engineer` | 8 |
| `business-analyst-agent` | 5 |
| `release-engineering-specialist` | 4 |
| `harness-engineering-architect` | 3 |
| `ast-graph-engineer` | 2 |
| `graph-orchestration-runtime-engineer` | 2 |
| `harness-evaluation-engineer` | 2 |
| `solution-architect` | 2 |
| `static-analysis-engineer` | 2 |
| `acceptance-testing-bdd-engineer` | 1 |
| `architecture-conformance-auditor` | 1 |
| `codebase-archaeology-agent` | 1 |
| `integration-testing-engineer` | 1 |
| `multi-model-router-architect` | 1 |
| `postmortem-facilitator-agent` | 1 |
| `python-backend-engineer` | 1 |
| **Total** | **37** |

16 distinct agents appear as primary; 24 distinct agents appear across primary and
supporting positions combined.

---

## Not routed, deliberately

FR-25 and FR-26 remain PROPOSED and carry no GitHub issue. They are absent from
`github_issues.json` and are not routed. Note the collision recorded in V2-014's body:
SRS FR-25 (the model fallback protocol, which IS routed, as V2-014) is a different thing
from the PROPOSED FR-25 in `advisory_items.json`.

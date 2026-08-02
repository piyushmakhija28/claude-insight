# Phase 7 Capability Gaps

Where the claude-global-library has no agent whose stated domain genuinely covers a
v2.0.0 sprint issue, or covers only part of it.

| Metric | Value |
|--------|-------|
| Issues routed | 37 of 37 |
| NO MATCH | 0 |
| LOW confidence | 4 (V2-015, V2-016, V2-021, V2-024) |
| MEDIUM confidence | 11 |
| HIGH confidence | 22 |
| Named capability gaps | 6 (3 structural, 3 narrow) |

Every issue got a route. None of them got a route by inventing a name; the four LOW rows
are honest LOW, and they cluster on exactly the three subject areas the library does not
cover: Claude Code plugin packaging, MCP server engineering, and procedural documentation
authoring.

---

## How "no such capability" was established

The claim "no agent covers X" is a negative, so it was tested rather than assumed:

- 505 agent names and 93 domain names were enumerated from
  `knowledge-graph/_master/agents_all.json` and grouped by `primary_home_kg` (93 distinct
  values, none null). There is no documentation domain, no packaging domain, and no
  protocol-tooling domain among the 93.
- A case-insensitive content grep across all 505 `agents/*/agent.md` files for
  `Model Context Protocol|MCP server|.mcp.json|Claude Code plugin` returns 2 files, and
  neither is an owner: `vaadin-engineer` documents *consuming* Vaadin's own MCP server for
  up-to-date docs, and `llm-attack-surface-analyst` lists MCP integrations as an attack
  surface to enumerate. Neither builds one.
- The same grep for `technical writ|documentation engineer|docs-as-code|style guide`
  returns 1 file, `mermaid-diagram-engineer`, and only for diagram-as-code embedding.
- Skill-name search over all 992 skills: the only `plugin` skill is
  `figma-plugin-widget-core`; the only `doc` skills are `as-built-documentation-synthesis`,
  `docker`, `honey-document-core`, `legal-document-ai-core` and
  `molecular-docking-virtual-screening-core`; the only `runbook` skill is
  `postmortem-runbook-engineering-core`. There is no packaging, MCP, or technical-writing
  skill.

---

## GAP-1 (structural): Claude Code plugin packaging and manifest authoring

**Issues affected:** V2-015 (#271, LOW), V2-020 (#276, MEDIUM), V2-022 (#278, MEDIUM),
V2-026 (#282, MEDIUM), V2-032 (#288, MEDIUM).

**Missing capability.** Authoring and validating a `.claude-plugin/plugin.json` manifest;
knowing the plugin install/enable/uninstall lifecycle; knowing what a marketplace entry
does to `settings.json`; knowing that plugin hooks merge silently and cannot be
individually disabled, and that a bundled MCP server spawns eagerly on enable. Those
facts are the substance of ADR-010 and ADR-019 and therefore of V2-015's real difficulty.

**Closest existing agents and why each is insufficient.**

- `release-engineering-specialist` (`agents/release-engineering-specialist/agent.md`) -
  owns SemVer bump determination, changelog generation, git tagging and release pipeline
  automation. It covers "produce a versioned shippable artifact with an explicit semver"
  and nothing else in the AC. It has no model of a plugin manifest schema, an install
  surface, or an uninstall residue.
- `architecture-conformance-auditor` (`agents/architecture-conformance-auditor/agent.md`) -
  an exact fit for the *gate* half of V2-015 (a CI fitness function asserting that a find
  over the plugin tree for `hooks/` or `*hooks.json` returns zero, at CRITICAL). V2-015's
  own AC names this agent's check by name. But a conformance auditor asserts on an
  artifact someone else designed; it does not design the artifact.
- `figma-plugin-engineer` (`agents/figma-plugin-engineer/agent.md`) - the only agent in the
  library with plugin manifest experience, and it is Figma manifest v2, a dual-context
  browser sandbox with a scene graph. Nothing transfers. Do not route to it.

**Consequence for execution.** V2-015 must be run with the ADR-010 / ADR-019 constraints
and the CONFIRMED-list manifest contract from `orchestration_prompt.md` section 1.4
supplied *in the prompt as source material*, not left to the agent's domain knowledge.
The agent will not know these.

---

## GAP-2 (structural): MCP server and tool engineering

**Issues affected:** V2-016 (#272, LOW), V2-024 (#280, LOW), V2-017 (#273, MEDIUM).

**Missing capability.** Writing an MCP server or tool; registering user-scope MCP servers
into `settings.json`; knowing what "reachable by name" means for an MCP tool; the
register/unregister round trip. Under ADR-019 this command pair is the *only* path to any
MCP-backed capability in v2.0.0, so this gap sits on the critical path.

**Closest existing agents and why each is insufficient.**

- `automation-engineer` (`agents/automation-engineer/agent.md`) - builds CLI tools and
  manages system-level operations in Python. It genuinely covers "write a reversible
  command that edits a JSON config file by merge-against-fresh-read", which is the
  ADV-008 clobber-safety requirement and the hardest correctness constraint in V2-016. It
  covers none of the MCP semantics, and it does not know the ADR-020 Path C verification
  is a one-shot opportunity.
- `python-backend-engineer` (`agents/python-backend-engineer/agent.md`) - `api-design-core`
  covers "expose existing logic as a named, schema-described, callable surface", which is
  structurally what V2-024 asks for when porting `push_gate.py`. It has no MCP protocol
  knowledge, so the transport and naming details must be supplied.
- `integration-testing-engineer` (`agents/integration-testing-engineer/agent.md`) -
  `contract-testing-core` is the right frame for "the existing `tests/test_push_gate.py`
  assertions pass against the MCP code path", but it tests a contract, it does not build
  a server.

**Consequence for execution.** For V2-016 and V2-024 the prompt must carry the MCP
registration format, the existing `mcp-post-tool-tracker` / push-gate code, and HLD
section 8.4's write-safety rule as literal input. Expect more owner review on these two
than on any HIGH-confidence row.

---

## GAP-3 (structural): technical writing and procedural documentation authoring

**Issues affected:** V2-021 (#277, LOW). Partial on V2-001 (#256), V2-029 (#285),
V2-036 (#292), and the whole V2-004 through V2-008 audit series.

**Missing capability.** Authoring a procedural document for a human reader: a runbook, a
migration guide, an ADR body, an audit report. Across 505 agents and 93 domains there is
no technical writer, no documentation engineer, and no docs-as-code agent.

**Closest existing agents and why each is insufficient.**

- `postmortem-facilitator-agent` (`agents/postmortem-facilitator-agent/agent.md`) - holds
  `postmortem-runbook-engineering-core`, the library's only runbook skill. Its runbooks are
  generated from historical incident telemetry after a production incident resolves. The
  V2-021 runbook is a product uninstall procedure with no incident, no telemetry and no
  root cause. The skill's shape is right; its trigger and inputs are wrong. This is why
  V2-021 is LOW rather than MEDIUM.
- `as-built-doc-generator` (`agents/as-built-doc-generator/agent.md`) - synthesises
  documentation, but Chikofsky-Level-3 as-built documentation *recovered from source code*
  (C4 diagrams, BDD mining, DDD aggregates). It reconstructs what a system is; it does not
  write a procedure a human follows.
- `solution-architect` (`agents/solution-architect/agent.md`) - genuinely produces
  Architecture Decision Records as a named output, which is why V2-001 and V2-029 are HIGH
  and not LOW. It does not extend to runbooks or migration guides.
- `business-analyst-agent` (`agents/business-analyst-agent/agent.md`) - carries
  `requirements-traceability-core`, which is the correct frame for the 46-row audit matrix
  and its Evidence cells, so V2-004 through V2-007 are HIGH on the *matrix* half. The
  surrounding prose of `policy-implementation-audit-v2.md` has no owner.

---

## GAP-4 (narrow): coverage-ledger cross-checking

**Issue affected:** V2-008 (#264, MEDIUM).

**Missing capability.** A script whose job is to prove no item silently disappeared from a
ledger - fail on a missing name, fail on an empty disposition, and specifically fail on the
literal value `disappeared` because that is the absence of a disposition rather than one.
This is a traceability-completeness oracle.

**Closest and why insufficient.** `requirements-traceability-core` (held by
`business-analyst-agent`) owns the *semantics* of "every requirement maps to something",
which is exactly the right definition of pass. `automation-engineer` owns the script. No
single agent owns both, so V2-008 is split across the two and is MEDIUM rather than HIGH.

---

## GAP-5 (narrow): decision-provenance schema design

**Issue affected:** V2-012 (#268, MEDIUM).

**Missing capability.** Designing the record a selector must emit so a selection can be
audited after the fact - the field set, its completeness rule, and its failure mode when a
field is empty.

**Closest and why insufficient.** `graph-orchestration-runtime-engineer` holds
`graph-observability-error-handling-core` and owns *where* the record is emitted during a
LangGraph run. `harness-engineering-architect` holds `agent-routing-dispatch-policy-core`
and owns *what decision* is being recorded. Neither owns the record schema itself, and the
five field names must in any case be read from SRS.md:307-310 rather than restated from
memory, per the issue body.

---

## GAP-6 (narrow): distributed lease renewal

**Issue affected:** V2-035 (#291, HIGH overall).

**Missing capability.** Lease renewal is one of the five ADR-016 mechanisms the regression
test must assert present. The other four map cleanly onto
`harness-engineering-architect`'s mandatory skills - attempt-count/iteration bound and the
convergence (no-progress) signal onto `stop-condition-budget-control-core`, the per-
dependency circuit breaker with non-fixed reopen-wait and full-jitter retry onto
`retry-backoff-circuit-breaker-core`. Lease renewal maps onto neither, nor onto
`loop-safety-engineer`'s `loop-termination-safety-core`.

**Closest unrouted option.** `distributed-consensus-engineer`
(`agents/distributed-consensus-engineer/agent.md`) holds `consensus-algorithms-core`, where
leader leases and renewal live. It was not added as a third supporting agent on V2-035
because one mechanism of five does not justify a third persona in the dispatch; supply the
lease-renewal definition in the prompt instead. It IS routed as supporting on V2-031 for
the replay-idempotency defect.

---

## Gaps recorded but not blocking

These were checked and are NOT gaps, recorded so they are not re-investigated:

- **AST and call-graph work** (V2-009, V2-010, V2-018, V2-019, V2-034). Well covered.
  `ast-graph-engineer` owns CHA/RTA/points-to call graph construction and edge-precision
  refinement, which is exactly the V2-010 resolver defect. `static-analysis-engineer` owns
  AST rule-engine architecture with exemption governance, which is exactly V2-018's
  node-type classifier and V2-019's `open()` rule. Both HIGH.
- **CI assertion work** (V2-025). `architecture-conformance-auditor` owns fitness functions
  run as CI gates, and `unit-testing-specialist` covers the mandatory companion negative
  test. HIGH.
- **Resilience work** (V2-035, V2-031). The library's `harness-engineering` and
  `graph-engineering` domains are a close fit for an agentic pipeline's control loop and
  its checkpoint durability respectively. Both HIGH, subject to GAP-6.
- **Test authoring** (V2-003, V2-023, V2-033). `harness-evaluation-engineer` covers agent
  harness instrumentation and regression gates; `acceptance-testing-bdd-engineer` covers
  the already-written Gherkin scenarios in prd-v2.md section 7. HIGH.
- **Release close-out** (V2-036, V2-037). `release-engineering-specialist` covers SemVer,
  changelog format and version-source-of-truth reconciliation directly. HIGH.

---

## Recommendation

Three agents are worth adding to the library, in this order of value to this project:

1. **An MCP server engineer.** Blocks the critical path in v2.0.0 and will recur in every
   future project that replaces hooks with MCP. Skills it would need do not exist either.
2. **A Claude Code plugin packaging engineer.** Same reasoning; manifest, marketplace,
   install/uninstall lifecycle, and the hook/MCP bundling constraints.
3. **A technical writer.** The widest gap by issue count and the cheapest to add, since it
   needs no new domain mathematics. Enumerated: the 9 issues carrying the `type:docs`
   label are V2-001, V2-004, V2-005, V2-006, V2-007, V2-021, V2-029, V2-030 and V2-036.

Until they exist, the four LOW rows must carry their domain facts in the dispatch prompt
as literal source material. Naming an agent does not supply knowledge the agent does not
have.

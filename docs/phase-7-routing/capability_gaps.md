# Phase 7 Capability Gaps

Where the claude-global-library has no agent whose stated domain genuinely covers a
v2.0.0 sprint issue, or covers only part of it.

**STATUS 2026-08-02: GAP-1, GAP-2 and GAP-3 are CLOSED** by the three agents and four
skills delivered against `library_gap_spec.md`. GAP-2 closes with one recorded residual,
detailed in its section. GAP-4, GAP-5 and GAP-6 remain open by design - the spec's
"NOT NEEDED" section deliberately excluded them.

| Metric | Before delivery | After delivery |
|--------|--------|--------|
| Issues routed | 37 of 37 | 37 of 37 |
| NO MATCH | 0 | 0 |
| LOW confidence | 4 (V2-015, V2-016, V2-021, V2-024) | **0** |
| MEDIUM confidence | 11 | 8 |
| HIGH confidence | 22 | 29 |
| Structural gaps open | 3 (GAP-1, GAP-2, GAP-3) | **0** |
| Narrow gaps open | 3 (GAP-4, GAP-5, GAP-6) | 3 (unchanged, by design) |
| Library agents / skills | 505 / 992 | 508 / 996 |

Every issue got a route. None of them got a route by inventing a name; the four LOW rows
were honest LOW, and they clustered on exactly the three subject areas the library did not
cover: Claude Code plugin packaging, MCP server engineering, and procedural documentation
authoring. All four have now cleared LOW.

---

## Delivery verification (2026-08-02)

Everything below was checked before any gap was marked CLOSED. Same two-check method as the
original run, re-applied to the grown catalogues:

1. **Catalogue membership.** Exact member of `agents_all.json -> agents[*].name` (now 508)
   or `skills_all.json -> skills[*].name` (now 996).
2. **Filesystem existence.** `agents/<name>/agent.md` or `skills/<name>/SKILL.md` present
   on disk in the library checkout.

Both checks passed for all seven delivered entries. The catalogue/filesystem reconciliation
was re-run in both directions and is clean: the only disk entries absent from the catalogues
are `agents/INDEX.md` and `skills/INDEX.md`, which are files, not capability directories.

| Delivered | Type | Lines | In catalogue | On disk |
|---|---|---|---|---|
| `mcp-server-engineer` | agent | 104 | yes | yes |
| `claude-code-plugin-engineer` | agent | 107 | yes | yes |
| `technical-writer-agent` | agent | 152 | yes | yes |
| `mcp-server-engineering-core` | skill | 407 | yes | yes |
| `claude-code-plugin-packaging-core` | skill | 334 | yes | yes |
| `technical-writing-core` | skill | 298 | yes | yes |
| `procedural-documentation-core` | skill | 321 | yes | yes |

Seven entries, enumerated. Counts moved 505 -> 508 agents and 992 -> 996 skills, matching
exactly.

**Recorded, not fixed:** the library `VERSION` file and `agents_all.json`'s own
`library_version` field both still read `29.72.0` while `agent_count` has moved to 508. The
master graph was rebuilt without a version bump.

---

## Acceptance test result -- at a glance

The bar set in `library_gap_spec.md`: "Each new agent must be able to take its assigned issue
WITHOUT the domain facts supplied as prompt input ... When those four rows can be raised to
MEDIUM or HIGH with no pasted domain facts, the gap is closed."

| Row | Before | After | Verdict |
|---|---|---|---|
| V2-015 (#271) plugin manifest | LOW | **HIGH** | PASS |
| V2-016 (#272) register-mcp | LOW | **MEDIUM** | PASS, at the floor |
| V2-021 (#277) uninstall runbook | LOW | **HIGH** | PASS |
| V2-024 (#280) push-gate MCP port | LOW | **HIGH** | PASS |

**ACCEPTANCE TEST: PASS.** 4 of 4 target rows cleared LOW. Zero LOW rows remain anywhere in
the routing table.

Second-order effect: four further rows moved MEDIUM -> HIGH (V2-017, V2-022, V2-026,
V2-032), all of them GAP-1 or GAP-2 rows whose recorded reason for MEDIUM was the missing
capability itself rather than a capability split. Full distribution and per-row notes are in
`routing_table.md`.

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

## GAP-1 (structural): Claude Code plugin packaging and manifest authoring -- CLOSED 2026-08-02

**CLOSED BY:** `claude-code-plugin-engineer` (107 lines) +
`claude-code-plugin-packaging-core` (334 lines).

**Row outcomes:** V2-015 LOW -> HIGH, V2-022 MEDIUM -> HIGH, V2-026 MEDIUM -> HIGH,
V2-032 MEDIUM -> HIGH, V2-020 MEDIUM -> MEDIUM (agent added, confidence deliberately held).
Five rows, enumerated, matching the affected list below.

**Evidence that closed it.** Every fact the gap named is present, and each is traceable to a
specific passage:

| Fact the gap named as missing | Where it landed |
|---|---|
| Authoring/validating `.claude-plugin/plugin.json` | `packaging-core` SS1: manifest location, closed eight-field schema, "reference marketplace CI pipelines validate `plugin.json` by REJECTING any property outside that set" |
| Convention-based discovery | `packaging-core` SS1: the nine fixed root-level names, plus the nesting-under-`.claude-plugin/` failure that "install[s] cleanly ... but expose[s] ZERO discovered capabilities" |
| Install / enable / uninstall lifecycle | `packaging-core` SS2: lifecycle verbs, the `/reload-plugins` sync step, four-scope table (user/project/local/managed) |
| What a marketplace entry writes to settings.json | `packaging-core` SS2: `extraKnownMarketplaces` committed into PROJECT-scope `.claude/settings.json`; marketplace catalog kept distinct from a plugin's own manifest |
| Hooks merge silently, cannot be individually disabled (ADR-010's forcing fact) | `packaging-core` SS3 + M3: merge produces "a FLAT, UNLABELED union", proved information-lossy as an impossibility, so "the only control surface exposed to the user is therefore whole-plugin enable/disable" |
| `${CLAUDE_PLUGIN_ROOT}` / manifest-anchored resolution (ADR-012) | `packaging-core` SS4 + M6: correct-by-construction vs correct-by-coincidence, with the CWD failure described as latent until real install |
| Uninstall residue not fully attributable (why FR-18 narrowed, FR-24 added) | `packaging-core` SS2 + M4: bundled resources are "install-time side effects into SHARED systems"; four-scope precedence makes uninstall a non-total subtraction |

The agent carries each of these as an enforceable rule rather than background: Operating
Rules 1 (root-level layout), 2 (closed schema, hard rejection), 4
(`${CLAUDE_PLUGIN_ROOT}`), 5 (no per-hook toggle), 6 (uninstall is not total subtraction),
8 (four-scope attribution); MUST NOT 1, 2, 3, 5.

**One fact from the spec landed elsewhere, not here.** The spec required this agent to know
"that a bundled `.mcp.json` stdio server **spawns eagerly on plugin enable** - the fact that
forced ADR-019". `packaging-core` SS2 gets close ("Installing the plugin wires these directly
into the running session's MCP server registry and hook pipeline") but never states eager
spawn. That statement lives in `mcp-server-engineering-core` SS3 and M6 instead, and the
plugin skill only cross-references it once, at M5. This is a split, not an absence - the
two agents' Agent Priority sections explicitly compose - but a dispatcher wanting the full
ADR-019 argument in one persona should add `mcp-server-engineer` as a second supporting
agent on V2-015.

**Original gap record follows, retained unedited for provenance.**

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

## GAP-2 (structural): MCP server and tool engineering -- CLOSED 2026-08-02, with one recorded residual

**CLOSED BY:** `mcp-server-engineer` (104 lines) + `mcp-server-engineering-core` (407 lines).

**Row outcomes:** V2-016 LOW -> MEDIUM, V2-024 LOW -> HIGH, V2-017 MEDIUM -> HIGH. Three
rows, enumerated, matching the affected list below.

**Evidence that closed it.**

| Fact the gap named as missing | Where it landed |
|---|---|
| Writing an MCP server / exposing tools | `mcp-core` SS1: JSON-RPC 2.0 wire format, three-step lifecycle handshake, tools/resources/prompts triad with list/action/change-notification methods; SS2: descriptor shape, per-property descriptions, `ToolAnnotations` |
| Registering user-scope servers into settings.json | `mcp-core` SS3: "**User scope - the `mcpServers` block inside `~/.claude/settings.json`**", contrasted with project-scope `.mcp.json` |
| Register / unregister round trip | `mcp-core` SS3: "Registering a server is a pure configuration mutation - nothing spawns at registration time ... Unregistering (deleting the entry) is the exact mirror" |
| "Reachable by name" for an MCP tool | `mcp-core` SS1 primitive table (`tools/list` -> `tools/call`) + SS2 naming convention and capability declaration |
| Merge-against-fresh-read (the ADV-008 constraint) | `mcp-core` SS4, by that exact name, ranked honestly as "a *probabilistic* improvement, not a correctness guarantee", above which sit optimistic concurrency and OS locking; plus the warning that atomic rename "does **not** by itself solve the lost-update problem" |
| Bundled stdio server spawns eagerly on enable (ADR-019's forcing fact) | `mcp-core` SS3's four compounding costs + M6's expected-cost proof that opt-in is never worse and strictly better below p=0.5 |

Agent enforcement: Core Responsibility 6 (registration write path), Operating Rules 7, 8, 9,
MUST NOT 3 and 4.

**THE RESIDUAL, VERIFIED NOT ACCEPTED.** The AMENDMENT added to `library_gap_spec.md` in
commit `0974e4d` required the skill to be written against the owner's 21 existing servers
and the vendored `mcp-base` framework, naming `MCPResponse`, `@mcp_tool_handler`,
`AtomicJsonStore` and `LazyClient`, plus the vendored-by-copy propagation hazard. A
case-insensitive grep for `mcp-base|mcp_base|AtomicJsonStore|MCPResponse|mcp_tool_handler|LazyClient|vendored`
across all seven delivered files returns **zero matches**. Neither of the two teaching-material
commits (`33af037`, `bc79339`) is cited either, though both defect *classes* did land as
`mcp-core` SS5 (non-idempotent retry causing duplicate creation, with the idempotency-key
fix) and SS6 (filter-after-paginate silently dropping results, with the "narrow before you
bound" invariant). The amendment landed after the team had started, which explains but does
not remove the gap.

**Ruling: not material enough to hold V2-016 at LOW; material enough to hold it at MEDIUM
rather than HIGH.** The reasoning:

- The acceptance test is stated in terms of *domain facts*. The MCP domain facts are now
  fully in the library. `mcp-base`'s existence and `AtomicJsonStore`'s location are facts
  about this owner's workspace, not about MCP - and every routing row in this table already
  carries project facts (file paths, ADR numbers, measured figures). A one-line reuse note
  is not the same thing as pasting the registration format and the write-safety rule in as
  literal source, which is what the LOW rows were doing.
- The cost is real but bounded and is a *reuse* cost, not a *correctness* cost. Section 4
  plus Operating Rules 7 and 8 would produce a correct write path. What the agent will do
  wrong is build a 22nd private helper when `AtomicJsonStore` (`mcp_base/persistence.py:26`)
  already implements a thread-safe atomic read-modify-write with write-to-temp-then-rename.
  Since ADV-008 already flags a shared write-safety helper as an ESCALATION CANDIDATE, that
  duplication works directly against a decision the project has already taken - which is why
  it costs V2-016 the HIGH rather than costing it nothing.
- A second, independent reason keeps V2-016 off HIGH regardless of `mcp-base`: the ADR-020
  Path C verification (`hld_v2.md:773`) is a one-shot measurement task with no owner in the
  library, new agents included. Even a perfect MCP agent would not cover that half of the AC.

**What the team should be told, plainly.** The `mcp-base` amendment was not implemented. The
skill is a good general-MCP skill written from the public specification; it is not the
"written against the existing corpus so it produces a 22nd server consistent with the other
21" skill the amendment asked for. Two additions would close it: a section naming the four
`mcp-base` primitives with `AtomicJsonStore` presented as the ready-made answer to SS4, and a
paragraph on the vendored-by-copy propagation hazard with the `33af037` fix-one-copy incident
as the worked example. Until then, V2-016 and V2-024 both carry the reuse instruction as a
prompt note.

**Original gap record follows, retained unedited for provenance.**

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

## GAP-3 (structural): technical writing and procedural documentation authoring -- CLOSED 2026-08-02

**CLOSED BY:** `technical-writer-agent` (152 lines) + `technical-writing-core` (298 lines) +
`procedural-documentation-core` (321 lines).

**Row outcomes:** V2-021 LOW -> HIGH. V2-004 HIGH (agent added for the report prose).
V2-036 HIGH (supporting agent corrected from `postmortem-facilitator-agent`). V2-001,
V2-029, V2-005, V2-006, V2-007, V2-008 untouched - see below for why each.

**Evidence that closed it.** The gap's own argument was that
`postmortem-runbook-engineering-core` had the right shape but the wrong trigger and inputs.
The delivered agent answers that objection directly, in its own text:

> **Distinct from `postmortem-facilitator-agent`.** That agent GENERATES diagnostic runbooks
> by MINING a corpus of historical incident telemetry ... This agent AUTHORS documentation -
> including runbooks - PROACTIVELY, from a process a human already understands, independent
> of and typically before any specific incident corpus exists.

It also draws explicit boundaries against `as-built-doc-generator` and
`business-analyst-agent`, the other two agents the gap record named as near misses. The
craft itself: `procedural-documentation-core` SS1 gives a six-part runbook anatomy and a
separate four-part migration-guide anatomy; SS2 gives the SRE 5 A's including **Accurate**
("matches the CURRENT state of the system, not a stale prior version"); SS3 grounds every
verification point as a literal Hoare postcondition; SS4 requires the point-of-no-return
step to be named. `technical-writing-core` SS1 gives Diataxis mode classification and SS2
task-based information architecture for the report-prose half.

**Rows deliberately NOT changed, with reasons:**

- **V2-001 (#256) and V2-029 (#285)** - both already HIGH on `solution-architect`, whose
  named output artifact is an ADR. Notably, the delivered `technical-writer-agent` does
  **not** claim ADR bodies: neither its description, its Role, nor `technical-writing-core`
  contains the string "ADR" anywhere (grep-verified). The spec's PRIORITY 3 asked for
  "runbooks, migration guides, ADR bodies, audit report prose". ADR bodies did not land. No
  change was warranted on these rows either way, but the omission is recorded below.
- **V2-005, V2-006, V2-007** - matrix-cell population from a closed vocabulary, no prose
  deliverable. `business-analyst-agent` remains correct and sufficient.
- **V2-008** - a coverage-ledger cross-checking script. That is GAP-4, which is still open by
  design.

**Original gap record follows, retained unedited for provenance.**

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

## GAP-4 (narrow): coverage-ledger cross-checking -- STILL OPEN, by design

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

## GAP-5 (narrow): decision-provenance schema design -- STILL OPEN, by design

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

## GAP-6 (narrow): distributed lease renewal -- STILL OPEN, by design

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

## Recommendation -- SATISFIED 2026-08-02

Three agents were recommended for the library, in this order of value to this project:

1. **An MCP server engineer.** Blocks the critical path in v2.0.0 and will recur in every
   future project that replaces hooks with MCP. Skills it would need do not exist either.
   -> **DELIVERED** as `mcp-server-engineer` + `mcp-server-engineering-core`, with one
   recorded residual (the `mcp-base` amendment, see GAP-2).
2. **A Claude Code plugin packaging engineer.** Same reasoning; manifest, marketplace,
   install/uninstall lifecycle, and the hook/MCP bundling constraints.
   -> **DELIVERED** as `claude-code-plugin-engineer` +
   `claude-code-plugin-packaging-core`. The most complete of the three deliveries.
3. **A technical writer.** The widest gap by issue count and the cheapest to add, since it
   needs no new domain mathematics. Enumerated: the 9 issues carrying the `type:docs`
   label are V2-001, V2-004, V2-005, V2-006, V2-007, V2-021, V2-029, V2-030 and V2-036.
   -> **DELIVERED** as `technical-writer-agent` + `technical-writing-core` +
   `procedural-documentation-core`, minus ADR-body authoring (see below).

The closing sentence of the original record - "Naming an agent does not supply knowledge the
agent does not have" - is the standard this re-run applied. No row was lifted because a
plausibly-named file appeared; every lift above cites the passage that supplies the
previously-missing fact.

---

## Where a delivery is thinner than its spec required

Recorded plainly so the team can fix it. None of these blocked a gap from closing, and two
of the three cost a specific row a confidence level.

1. **`mcp-server-engineering-core` does not implement the `0974e4d` AMENDMENT.** Zero
   occurrences of `mcp-base`, `mcp_base`, `AtomicJsonStore`, `MCPResponse`,
   `mcp_tool_handler`, `LazyClient` or `vendored` across all seven delivered files
   (grep-verified). The spec's skill table said, in bold, "Write it against `mcp-base` and
   the 21 existing servers". It was instead written from the public MCP specification. Cost:
   V2-016 is MEDIUM rather than HIGH. The two teaching-material commits `33af037` and
   `bc79339` are also uncited, though both defect *classes* landed as SS5 and SS6 - so the
   pedagogy is present and only the provenance is missing.
2. **`technical-writer-agent` does not claim ADR bodies or audit-report prose.** The spec's
   PRIORITY 3 named "runbooks, migration guides, ADR bodies, audit report prose". The
   delivered agent's description and Role both enumerate "READMEs, API guides, conceptual
   explanations, onboarding tutorials, incident runbooks, and migration guides" and stop
   there; the string "ADR" appears nowhere in the agent or in `technical-writing-core`
   (grep-verified). No cost to any row - `solution-architect` already owns ADR authoring at
   HIGH on V2-001 and V2-029 - but the library still has no agent that will write an ADR
   *body* well as prose rather than as an architecture decision.
3. **The ADR-019 eager-spawn fact is split across two skills.**
   `claude-code-plugin-packaging-core` SS2 stops at "installing the plugin wires these
   directly into the running session's MCP server registry"; the eager-spawn statement and
   its cost proof live only in `mcp-server-engineering-core` SS3 and M6. A plugin engineer
   dispatched alone on V2-015 has the zero-hooks argument in full but only half the
   zero-MCP-servers argument. Cheapest fix: one cross-referencing paragraph in
   `packaging-core` SS2.

Not a thinness, but worth stating: `claude-code-plugin-packaging-core` covers every item the
spec listed for it, and `procedural-documentation-core` covers every item listed for it. The
plugin and procedural-documentation deliveries are at or above spec.

---

## What could not be verified

- **Whether these agents actually perform.** This is a static content audit. Every lift above
  rests on a passage being present and enforceable, not on an observed run. The routing table
  is now a prediction; V2-015, V2-016, V2-021 and V2-024 executing successfully is the only
  thing that would confirm it.
- **The MCP protocol claims themselves.** `mcp-server-engineering-core`'s wire-format,
  handshake and `ToolAnnotations` default-value claims were not checked against the current
  published MCP specification. They are internally consistent and match the shape of the
  owner's existing servers, but that is not verification.
- **The eight-field `plugin.json` schema cap.** `claude-code-plugin-packaging-core` attributes
  it to a community JSON-schema project and to reference marketplace CI. Not independently
  confirmed against Claude Code's own documentation in this run. V2-015's AC only requires
  `name`, `description` and a semver `version`, all three of which are in the cited set, so
  the row does not depend on the cap being exactly eight.
- **Library VERSION.** Still `29.72.0` after 505 -> 508 agents and 992 -> 996 skills. Whether
  that is intentional (batched for a later bump) or an oversight was not established.

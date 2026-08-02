# Library Gap Spec -- what to author in claude-global-library

**For:** Piyush Makhija - handoff spec, to be built elsewhere and brought back
**Source:** `docs/phase-7-routing/capability_gaps.md` (Phase 7 routing, 2026-08-02)
**Library:** `claude-global-library` v29.72.0 - 505 agents, 992 skills, 93 domains
**Conventions:** agents live at `agents/{name}/agent.md`, skills at `skills/{name}/SKILL.md`

Three agents and four skills. Priority order below is by critical path, not by size.

Everything here was established by enumeration over the master knowledge graph, not by
impression: `agents_all.json` (505) and `skills_all.json` (992) were reconciled against the
filesystem in both directions with zero orphans, and a content grep was run across all 505
`agent.md` files.

---

## PRIORITY 1 -- `mcp-server-engineer` (ON THE CRITICAL PATH)

**Unblocks:** V2-016 (#272), V2-024 (#280), V2-017 (#273)
**Why first:** under ADR-019 the plugin bundles ZERO MCP servers, so the `register-mcp`
command pair is the *only* path to any MCP-backed capability in v2.0.0. V2-016 sits on the
plugin/gate critical chain, and the push gate has no preventive cover until it lands.

**Evidence the gap is real.** A content grep across all 505 `agent.md` files for
`Model Context Protocol|MCP server|.mcp.json|Claude Code plugin` returns **2 files**, neither
an owner: `vaadin-engineer` *consumes* an MCP server, `llm-attack-surface-analyst` lists MCP
as an attack surface.

**Must know:**
- Writing an MCP server and exposing tools with schema-described, callable surfaces
- Registering **user-scope** MCP servers into `settings.json`, and the register/unregister
  round trip
- What "reachable by name" means for an MCP tool
- **Merge-against-fresh-read** when editing a shared JSON config, so a concurrent writer is
  not clobbered. This is the hardest correctness constraint in V2-016 (ADV-008) and the one
  most likely to be got wrong
- That a bundled `.mcp.json` stdio server **spawns eagerly on plugin enable** - the fact
  that forced ADR-019

**Closest existing, and why insufficient:**
| Agent | Covers | Missing |
|---|---|---|
| `automation-engineer` | reversible CLI tools, JSON config editing in Python | all MCP semantics |
| `python-backend-engineer` | `api-design-core` - exposing logic as a named callable surface | MCP protocol, transport, naming |
| `integration-testing-engineer` | `contract-testing-core` - asserting a contract holds | builds no server |

**Suggested skills:** `mcp-server-engineering-core` (new, see below), plus existing
`api-design-core`, `contract-testing-core`, `error-handling-patterns`.

---

## PRIORITY 2 -- `claude-code-plugin-engineer`

**Unblocks:** V2-015 (#271), V2-020 (#276), V2-022 (#278), V2-026 (#282), V2-032 (#288)

**Evidence the gap is real.** The library's only plugin agent is `figma-plugin-engineer` -
Figma manifest v2, a dual-context browser sandbox with a scene graph. **Nothing transfers.
Do not route plugin work to it.**

**Must know:**
- Authoring and validating a `.claude-plugin/plugin.json` manifest, and convention-based
  discovery
- The install / enable / uninstall lifecycle, and what a marketplace entry writes to
  `settings.json`
- **Plugin hooks merge silently and cannot be individually disabled** - the fact that forced
  ADR-010's zero-bundled-hooks decision
- `${CLAUDE_PLUGIN_ROOT}` semantics and manifest-anchored `__file__` ascent for root
  resolution (ADR-012)
- That uninstall residue is **not fully attributable** to the plugin, which is why FR-18 was
  narrowed and FR-24 added

**Closest existing, and why insufficient:**
| Agent | Covers | Missing |
|---|---|---|
| `release-engineering-specialist` | SemVer, changelog, tagging, release pipeline | no manifest schema, install surface or uninstall model |
| `architecture-conformance-auditor` | exact fit for the CI **gate** half of V2-015 | asserts on an artifact someone else designed |
| `figma-plugin-engineer` | a different product's manifest | everything |

**Suggested skills:** `claude-code-plugin-packaging-core` (new), plus existing
`architecture-fitness-function-core`, `system-design`.

---

## PRIORITY 3 -- `technical-writer-agent`

**Unblocks:** V2-021 (#277). Partial on V2-001 (#256), V2-029 (#285), V2-036 (#292), and the
V2-004..V2-008 audit series.

**Evidence the gap is real.** Across **505 agents and 93 domains there is no technical
writer, no documentation engineer and no docs-as-code agent.** This is the broadest gap
found, and it is not specific to this release.

**Must know:** authoring a procedural document for a human reader - runbooks, migration
guides, ADR bodies, audit report prose. Sequenced steps, preconditions, verification points,
rollback.

**Closest existing, and why insufficient:**
| Agent | Covers | Missing |
|---|---|---|
| `postmortem-facilitator-agent` | `postmortem-runbook-engineering-core`, the only runbook skill | fires from **incident telemetry after a production incident**. A product uninstall procedure has no incident, no telemetry, no root cause. Right shape, wrong trigger and inputs |
| `as-built-doc-generator` | Chikofsky-Level-3 docs **recovered from source** | reconstructs what a system *is*; does not write a procedure a human *follows* |
| `solution-architect` | genuinely produces ADRs as a named output | does not extend to runbooks or migration guides |
| `business-analyst-agent` | `requirements-traceability-core` - correct for the 46-row audit matrix | the surrounding prose has no owner |

**Suggested skills:** `technical-writing-core` (new), `procedural-documentation-core` (new),
plus existing `requirements-traceability-core`.

---

## NEW SKILLS REQUIRED

| Skill | For | Must cover |
|---|---|---|
| `mcp-server-engineering-core` | P1 | MCP protocol, tool schema design, stdio transport, user-scope registration, merge-against-fresh-read config safety, register/unregister round trip |
| `claude-code-plugin-packaging-core` | P2 | manifest schema, convention discovery, install/enable/uninstall lifecycle, hook-merge semantics, `${CLAUDE_PLUGIN_ROOT}`, marketplace entries |
| `technical-writing-core` | P3 | audience analysis, information architecture, procedural vs reference vs explanatory modes, minimalism (Carroll) |
| `procedural-documentation-core` | P3 | runbooks, migration guides, preconditions, verification points, rollback steps, numbered-step discipline |

---

## NOT NEEDED -- do not author these

GAP-4, GAP-5 and GAP-6 are **narrow**, not structural. They are single missing techniques
inside issues that already have a competent owner, and are better handled as prompt input
than as new library entries:

- **GAP-4** coverage-ledger cross-checking (V2-008)
- **GAP-5** decision-provenance schema design (V2-012)
- **GAP-6** distributed lease renewal - one of five ADR-016 mechanisms. The other four map
  directly onto `harness-engineering-architect`'s mandatory skills

Authoring agents for these would add library surface without adding capability.

---

## SOURCE MATERIAL FOR WHOEVER BUILDS THESE

Do not have the author invent the domain facts. This run produced them, measured:

| Fact | Where |
|---|---|
| Zero bundled MCP servers; opt-in `register-mcp` | `docs/phase-2-validation/hld_v2.md` ADR-019 |
| Three-layer push-gate control | `hld_v2.md` ADR-020 |
| Plugin hooks merge silently, cannot be disabled individually | `docs/phase-1-architecture/hld.md` ADR-010 |
| Manifest-anchored root resolution | `hld.md` ADR-012 |
| What install/uninstall actually writes | `docs/phase-1-architecture/plugin_schema_spike.md` (FR-14a spike, run against a backed-up `settings.json` verified byte-identical after) |
| 8-step migration runbook | `hld_v2.md` SS 10 |
| Manifest contract, CONFIRMED list | `docs/orchestration_prompt.md` SS 1.4 |
| Two real MCP defects, with root causes | `mcp-github-api` commits `33af037` (non-idempotent POST retry duplicated a created issue) and `bc79339` (silent 25-row listing cap, PR filter applied after the slice) |

**The two MCP defect commits are the best available teaching material for
`mcp-server-engineering-core`** - both are real, both were found by measurement, and both are
the kind of bug an MCP author will otherwise reproduce.

---

## ACCEPTANCE -- how to tell each agent is good enough

Each new agent must be able to take its assigned issue **without the domain facts supplied as
prompt input**. That is precisely the test the current library fails: today V2-015, V2-016,
V2-021 and V2-024 are routed LOW and their rows instruct the dispatcher to paste the manifest
contract, the MCP registration format and the HLD write-safety rule in as literal source.

When those four rows can be raised to MEDIUM or HIGH with no pasted domain facts, the gap is
closed.

# System Requirements Analysis

**Project:** Claude Workflow Engine
**Version:** 1.21.4
**Date:** 2026-07-30
**Author:** Claude Workflow Engine Team

---

## Executive Summary


Claude Workflow Engine is a LangGraph-based 3-level pipeline that automates the full Software Development Life Cycle (SDLC) — from task analysis to merged PR closure — using LLM inference, template-driven orchestration, AST-based call graph analysis, and 13 MCP servers (295 tools). It is the only AI tool that automates all 8 active SDLC steps including GitHub Issues, branch creation, code review, PR merge, Jira tracking, Figma design-to-code, Jenkins CI/CD, SonarQube scanning, UML generation, and documentation updates.

---

## 1. Purpose
Claude Workflow Engine automates software development lifecycle tasks that normally require human coordination across multiple tools (GitHub, Jira, Figma, Jenkins, SonarQube, LLM APIs). A developer provides a natural language task description; the engine handles everything from analysis to delivery.

The system aims to:
- Automate the full SDLC pipeline from task intake to issue closure
- Enforce project-specific coding standards at every step via 63 policy files
- Reduce LLM inference costs by 60-85% through template-driven orchestration and token optimization
- Support multi-project, multi-language codebases (20+ languages, 15+ frameworks)
- Provide pluggable, extensible architecture so individual steps/levels can be added or removed

---

## 2. Scope

### Included
- Python 3.8+ pipeline execution on Windows/Linux/macOS
- LangGraph StateGraph orchestration (Level 0 through Level 2)
- 13 FastMCP servers (295 tools) for GitHub, Jira, Figma, Jenkins, Git, LLM, etc.
- Template-driven orchestration (single LLM call for full planning phase)
- Hybrid LLM inference (Claude CLI → Anthropic API)
- AST-based call graph analysis (Python/Java/TypeScript/Kotlin)
- 13 UML diagram types (Mermaid + PlantUML + Kroki.io rendering)
- Hook system (UserPromptSubmit, PreToolUse, PostToolUse, Stop)

---

## 3. Requirements

### 3.1 Functional Requirements


#### FR-1: 3-Level Pipeline Execution

**Description:** Pipeline must execute 3 levels in order: Level 0 (Pre-Flight Sanity Guard), Level 1 (Session & Context Synchronization), Level 2 (SDLC Execution Core). Each level must be independently removable or bypassable. Standards loading (project type/framework detection, policy loading) is an always-on, disk-loaded mechanism -- not a numbered pipeline level; it has never had pipeline nodes of its own.
**Priority:** Critical
**Status:** Implemented
**Key Module:** `orchestrator.py`

#### FR-2: 9-Step SDLC Automation (Level 2)

**Description:** Level 2 (SDLC Execution Core) must execute 9 active steps (Steps 0-8) with optional Hook Mode (Steps 0-3 only) via `CLAUDE_HOOK_MODE` env var.

| Step | Action |
|------|--------|
| Step 0 | Pre-Analysis & CallGraph Scan: CallGraph scan, template fast-path detection |
| Step 1 | Task Orchestration & Planning: template fill (prompt_gen_expert_caller) + orchestration execution |
| Step 2 | Issue Tracking: GitHub Issue + Jira Issue creation (dual, cross-linked) |
| Step 3 | Branch & Workspace Setup (from Jira key if ENABLE_JIRA) |
| Step 4 | Implementation & Code Generation + Jira "In Progress" + Figma "started" |
| Step 5 | Pull Request & Automated Review: PR creation + code review + Jira "In Review" + Figma fidelity check |
| Step 6 | Issue & Ticket Closure: GitHub + Jira "Done" + Figma "complete" |
| Step 7 | Documentation & UML Generation: doc update + 13 UML diagram types |
| Step 8 | Final Telemetry & Summary Report + voice notification |

**Priority:** Critical
**Status:** Implemented
**Key Module:** `sdlc_pipeline/subgraph.py`

#### FR-3: AST-Based Call Graph Analysis

**Description:** Full class-level call graph supporting Python (AST), Java, TypeScript, Kotlin (regex). Used at Steps 0, 1, 4, and 5 for impact analysis, implementation context, and PR review.
**Priority:** High
**Status:** Implemented
**Key Modules:** `parsers/` (Abstract Factory), `call_graph_builder.py`, `call_graph_analyzer.py`

#### FR-4: Integration Lifecycle Management

**Description:** All integrations follow Create → Update → Close lifecycle. Jira and Figma are toggled via env flags. Operations are non-blocking (failure of one integration does not stop others).

| Integration | Flag | Lifecycle Steps |
|-------------|------|----------------|
| Jira | `ENABLE_JIRA=1` | Create (2), Branch (3), In Progress (4), In Review (5), Done (6) |
| Figma | `ENABLE_FIGMA=1` | Extract (Step 1 template), Comment started (4), Review (5), Comment done (6) |
| Jenkins | `ENABLE_JENKINS=1` | Trigger (4), Validate (5) |
| SonarQube | `ENABLE_SONARQUBE=1` | Scan (4), Auto-fix loop |

**Priority:** Medium
**Status:** Implemented
**Key Module:** `integrations/` (Abstract Factory + Template Method)

#### FR-5: Modular Pipeline Construction

**Description:** Pipeline must be constructable via `PipelineBuilder` chainable API. Individual levels must be addable/removable without modifying orchestrator.
**Priority:** High
**Status:** Implemented
**Key Module:** `orchestrator.py` (`create_flow_graph`)

```python
# Levels are wired in the single canonical factory:
create_flow_graph(hook_mode=True)   # Level 0 + Level 1 + Level 2 (Steps 0-3)
create_flow_graph(hook_mode=False)  # full run (Steps 0-8)
```

#### FR-6: 13 MCP Servers (295 Tools)

**Description:** All external service operations (GitHub, Jira, Figma, Jenkins, Git, LLM, etc.) must be accessible as MCP tools registered in `~/.claude/settings.json`.
**Priority:** High
**Status:** Implemented
**Key Location:** `src/mcp/`

#### FR-7: Multi-Project Standards Enforcement

**Description:** The always-on, non-numbered Standards mechanism must auto-detect project type (language, framework) and load appropriate coding standards from 63 policy files, read directly from `policies/` on disk (no pipeline nodes involved).
**Priority:** High
**Status:** Implemented
**Key Module:** `langgraph_engine/standards/`

#### FR-8: Hybrid LLM Inference

**Description:** LLM calls must follow fallback chain: Claude CLI → Anthropic API. Model selection must be complexity-based.
**Priority:** High
**Status:** Implemented
**Key Module:** `langgraph_engine/llm_call.py`

#### FR-9: Hook System

**Description:** Pipeline must integrate with Claude Code's 4 hook types (UserPromptSubmit, PreToolUse, PostToolUse, Stop) for automated trigger and enforcement.
**Priority:** High
**Status:** Implemented
**Key Scripts:** `hooks/pre-tool-enforcer.py`, `hooks/post-tool-tracker.py`, `hooks/stop-notifier.py`, `scripts/3-level-flow.py` (UserPromptSubmit)

---

### 3.2 Non-Functional Requirements


#### NFR-1: Performance

- **Hook Mode target:** Steps 0-3 complete in < 60 seconds
- **Full Mode target:** All 9 active steps complete in < 170 seconds
- **Template fast-path:** Bypasses Step 1 entirely, jumps directly to Step 2
- **Token savings:** 60-85% reduction via AST navigation + dedup
- **Status:** Implemented

#### NFR-2: Extensibility

- Adding a new pipeline level: implement subgraph, call `PipelineBuilder().add_my_level()`
- Adding a new routing rule: add function to `routing/` package, register in orchestrator
- Adding a new integration: extend `AbstractIntegration` in `integrations/`
- Adding a new UML diagram: extend `AbstractDiagramGenerator` in `diagrams/`
- Adding a new language parser: extend `AbstractLanguageParser` in `parsers/`
- **Status:** Implemented via 9 modular packages (v1.5.0)

#### NFR-3: Reliability

- Checkpoint recovery: pipeline can resume from any step after crash
- Signal handling: Ctrl+C triggers graceful recovery with checkpoint save
- Non-blocking integrations: Jira/Figma/Jenkins failure does not abort pipeline
- Error propagation: `node_error_handler` decorator standardizes all node failures
- **Status:** Implemented

#### NFR-4: Backward Compatibility

- All existing imports continue to work unchanged:
  - `from langgraph_engine.flow_state import FlowState` (shim re-exports from `state/`)
  - `from langgraph_engine.uml_generators import generate_all` (shim re-exports from `diagrams/`)
  - `from langgraph_engine.call_graph_builder import CallGraphBuilder` (shim re-exports from `parsers/`)
- **Status:** Implemented

#### NFR-5: Platform Compatibility

- Python 3.8+ on Windows (cp1252-safe ASCII-only source files), Linux, macOS
- Cross-platform paths via `path_resolver.py`
- UTF-8 encoding throughout; no non-ASCII characters in `.py` files
- **Status:** Implemented

#### NFR-6: Security

- API keys read from `.env` file, never hardcoded
- Input sanitization before LLM calls
- GitHub tokens scoped to minimum required permissions
- **Status:** Implemented (hardening ongoing)

---

## 4. Acceptance Criteria

One criterion per functional requirement, per rules/44 section 2.

| Requirement | Acceptance Criterion |
|---|---|
| FR-1 | `create_flow_graph()` builds Level 0, Level 1 and Level 2 in order, and a run with any single level removed still reaches a terminal node. |
| FR-2 | A full-mode run executes Steps 0-8 in order; with `CLAUDE_HOOK_MODE=1` it stops after Step 3 and reports the remaining steps as skipped. |
| FR-3 | The call graph resolves classes and methods for Python, Java, TypeScript and Kotlin sources, and Steps 0 and 5 read impact data from it rather than rebuilding it. |
| FR-4 | With an integration flag unset its steps are skipped without error; with it set the Create -> Update -> Close transitions all fire, and a failure in one integration does not abort the others. |
| FR-5 | Levels can be added or removed by editing `create_flow_graph` alone, with no change to any node module. |
| FR-6 | Every registered MCP server starts over stdio and reports its documented tool count. |
| FR-7 | Project type and framework are detected from the working tree, and the matching policy files are loaded from `policies/` before any code change is written. |
| FR-8 | An LLM call falls through Claude CLI to the Anthropic API, and returns None rather than raising when no provider is available. |
| FR-9 | All four hook events fire, and a blocking policy returns exit code 2 from the PreToolUse hook so the tool call does not proceed. |

---

## 5. Out of Scope

Explicitly excluded, to prevent scope creep:
- Web UI / GUI (CLI-only)
- Direct database writes (all DB access via MCP tools)
- Custom LLM training or fine-tuning
- Real-time collaboration between multiple users simultaneously

---

## 6. Change Log

| Date | Version | Task | Change Summary | Status |
|------|---------|------|----------------|--------|
| 2026-07-30 | 1.21.2 | Restructure SRS to rules/11 + rules/44 | Numbered sections adopted; Acceptance Criteria, Out of Scope and this Change Log added; three claims corrected against the working tree (TOON removed in v1.15.2, `pipeline_builder.py` deleted in favour of `create_flow_graph`, hook entry points live in `hooks/`). | Done |

---

## Project Context
- **Domain:** Software Development Automation / DevOps
- **Target Users:** Solo developers, engineering teams using Claude Code CLI
- **Deployment:** Local machine, triggered by Claude Code hooks on every user prompt
- **Integration Points:** GitHub, Jira (Cloud+Server), Figma, Jenkins, SonarQube, Anthropic API

---

## Architecture & Design


### System Architecture

```
User Prompt
    |
    v
[UserPromptSubmit Hook] -> scripts/3-level-flow.py
    |
    v
[LangGraph StateGraph] (orchestrator.py)
    |
    +-- Level 0: Pre-Flight Sanity Guard (Unicode, encoding, path checks)
    |
    +-- Level 1:  Session & Context Synchronization (session, complexity scoring)
    |
    +-- Standards (non-numbered, always-on): project detection, policy loading from disk
    |
    +-- Level 2:  SDLC Execution Core (9-step pipeline)
            |
            +-- Step 0: CallGraph pre-analysis + template fast-path detection
            +-- Step 1: Template fill + orchestration execution (2 subprocess calls)
            +-- Integration lifecycle (Jira/Figma/Jenkins/SonarQube)
            +-- MCP tool calls (13 servers, 295 tools)
```

### Technology Stack

| Layer | Technology | Version | Rationale |
|-------|-----------|---------|-----------|
| Orchestration | LangGraph | 0.2.0+ | Stateful graph execution with conditional routing |
| LLM Framework | LangChain | 0.1.0+ | LLM abstraction, prompt templates |
| MCP Protocol | FastMCP (mcp) | 1.0+ | Stdio JSON-RPC tool protocol |
| Language | Python | 3.8+ | Primary implementation language |
| Testing | pytest | 7.0+ | 75 test files, 1,608 passing tests |
| AST Analysis | Python ast | stdlib | Call graph extraction for Python |

### Package Architecture (v1.5.0 Modularization)

| Package | Pattern | Files | Replaces |
|---------|---------|-------|---------|
| `core/` | Decorator + Factory | 7 | 25+ copy-pasted loguru blocks, 9 integration hooks, 15+ step wrappers |
| `state/` | — | 6 | `flow_state.py` (1,131 lines monolith) |
| `routing/` | — | 5 | Routing functions embedded in `orchestrator.py` |
| `helper_nodes/` | — | 6 | Helper node functions embedded in `orchestrator.py` |
| `diagrams/` | Strategy | 15 | `uml_generators.py` (1,556 lines monolith) |
| `parsers/` | Abstract Factory | 8 | `call_graph_builder.py` (1,419 lines monolith) |
| `sonarqube/` | Facade | 6 | `sonarqube_scanner.py` (1,639 lines monolith) |
| `integrations/` | Abstract Factory + Template | 7 | Scattered lifecycle code in 3+ files |
| `pipeline_builder.py` | Builder | 1 | `create_flow_graph()` inline in orchestrator |

---

## Implementation Status


### Completed Features (v1.15.1)

- [x] 4-Level pipeline (Level -1, 1, 2, 3)
- [x] 8-step active SDLC automation (Pre-0, Step 0, Steps 8-14)
- [x] 13 MCP servers (295 tools)
- [x] Template-driven orchestration (single planning LLM call)
- [x] Hybrid LLM inference (2 providers: claude_cli, anthropic)
- [x] AST call graph analysis (4 languages)
- [x] 13 UML diagram types
- [x] Jira full lifecycle integration
- [x] Figma design-to-code integration
- [x] Jenkins CI/CD integration
- [x] SonarQube scan + auto-fix loop
- [x] Hook system (4 hook types)
- [x] Policy system (63 policies)
- [x] Token optimization (60-85% savings)
- [x] Session management + TOON compression
- [x] Checkpoint recovery
- [x] **Modular architecture: 9 packages, design patterns** (v1.5.0)
- [x] Backward-compatible shims for all refactored modules

### In Progress

- [ ] Code coverage measurement (pytest --cov, 70% threshold)
- [ ] GitHub Actions CI pipeline
- [ ] Docker containerization

### Planned

- [ ] PyPI package (`pip install claude-workflow-engine`)
- [ ] CLI interface (`cwe run "fix the bug"`)
- [ ] Configuration wizard for first-time setup
- [ ] Multi-region / team deployment

---

## Testing Strategy


### Unit Testing

- Framework: pytest
- Test files: 75
- Passing: 1,608 tests
- Coverage target: 70%+

### Integration Testing

- Full pipeline integration tests at `tests/integration/`
- MCP server tests: `pytest tests/test_*mcp*.py`
- CallGraph tests: `pytest tests/test_call_graph_builder.py tests/test_call_graph_analyzer.py`

### Known Failing Tests (Pre-existing)

- `tests/test_recovery_handler.py::test_save_step_checkpoint_success` — pre-existing fixture issue

---

## Deployment & Operations


### Deployment Process

1. Developer runs `git clone` and `pip install -r requirements.txt`
2. Copy `.env.example` to `.env`, fill in API keys
3. Run `python scripts/sync-mcp-servers.py` to register MCP servers in `~/.claude/settings.json`
4. Pipeline triggers automatically via Claude Code hook on every user prompt

### Operational Requirements

- **Monitoring:** Per-step JSONL telemetry, metrics aggregator CLI (`metrics_aggregator.py`)
- **Logging:** Structured loguru / stdlib logging throughout
- **Recovery:** Checkpoint at every step boundary; resume via `--resume` flag
- **Backup:** Session data backed up to `BackupManager` on each checkpoint

---

## Risks & Mitigation


| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|-----------|
| All LLM providers fail | High | Low | 4-provider fallback chain; pipeline halts gracefully |
| Jira/Figma API unavailable | Low | Medium | Non-blocking; pipeline continues without that integration |
| Large codebase exceeds CallGraph limits | Medium | Low | MAX_FILES=300, MAX_FILE_SIZE_KB=100 in `parsers/config.py` |
| Windows encoding issues | Medium | Low | ASCII-only .py files; path_resolver.py for cross-platform paths |

---

**Last Updated:** 2026-07-30
**Next Review:** 2026-06-21

---

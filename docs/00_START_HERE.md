# Getting Started with Claude Workflow Engine

**Version:** 1.15.1 | **Status:** Active

---

## What Is This?

Claude Workflow Engine automates the Software Development Life Cycle using a
3-level LangGraph orchestration pipeline. From a single natural language prompt,
it handles task analysis, GitHub issues, branching, PR creation, code review,
documentation, and issue closure.

---

## Current Pipeline

```
Level 0: Pre-Flight Sanity Guard (Unicode, encoding, paths)
Level 1: Session & Context Synchronization (complexity, session)
Standards: always-on, loaded from disk (common, Java, tool-opt, MCP discovery) -- non-numbered
Level 2: SDLC Execution Core
  Step 0: Pre-Analysis & CallGraph Scan -- call graph scan + template fast-path detection
  Step 1: Task Orchestration & Planning (prompt-gen-expert + orchestrator-agent chain)
  Step 2: Issue Tracking -- GitHub Issue Creation
  Step 3: Branch & Workspace Setup
  Step 4: Implementation & Code Generation
  Step 5: Pull Request & Automated Review (with retry loop)
  Step 6: Issue & Ticket Closure
  Step 7: Documentation & UML Generation
  Step 8: Final Telemetry & Summary Report
```

**The old Steps 1, 3, 4, 5, 6, 7 (pre-v1.13.0 numbering) were removed in v1.13.0** -- collapsed
into the single consolidated Task Orchestration node (now Step 1). See `CLAUDE.md` for the full
architecture, including the domain-driven Level/Step rename this pipeline diagram reflects.

---

## Quick Start

```bash
python scripts/3-level-flow.py --task "your task description"
```

## Full Documentation

See the root `CLAUDE.md` for complete architecture, configuration, and development
guidelines.

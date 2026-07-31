# Documentation Index

Every document in this repository lives under `docs/`, grouped by what it is.
The repository root carries only the five files `rules/11-documentation-files.md`
permits: `README.md`, `CLAUDE.md`, `SRS.md`, `CHANGELOG.md` and `VERSION`.

| Folder | Contains | Files |
|---|---|---|
| [`standards/`](standards/) | Coding and testing standards | 52 |
| [`policies/`](policies/) | Pipeline policies | 46 |
| [`architecture/`](architecture/) | Architecture and design | 17 |
| [`guides/`](guides/) | How-to guides and runbooks | 14 |
| [`reports/`](reports/) | Investigations and audits | 20 |
| [`releases/`](releases/) | Per-release design notes | 6 |
| [`contributing/`](contributing/) | Contribution and community files | 5 |
| [`api/`](api/) | API specifications | 1 |
| [`phase-1-architecture/`](phase-1-architecture/) | Phase 1 architecture artefacts | 2 |

---

## `standards/` -- Coding and testing standards

Numbered rules 01-46 plus per-language standards. These mirror `~/.claude/rules/`, which is what the Standards mechanism loads at runtime; the copies here are for reading, not execution.

<details><summary>52 file(s)</summary>

- [01-common-standards.md](standards/01-common-standards.md)
- [02-backend-standards.md](standards/02-backend-standards.md)
- [03-microservices-standards.md](standards/03-microservices-standards.md)
- [04-frontend-standards.md](standards/04-frontend-standards.md)
- [05-security-standards.md](standards/05-security-standards.md)
- [06-typescript-standards.md](standards/06-typescript-standards.md)
- [07-go-standards.md](standards/07-go-standards.md)
- [08-rust-standards.md](standards/08-rust-standards.md)
- [09-swift-standards.md](standards/09-swift-standards.md)
- [10-kotlin-standards.md](standards/10-kotlin-standards.md)
- [11-documentation-files.md](standards/11-documentation-files.md)
- [12-docstrings-only.md](standards/12-docstrings-only.md)
- [13-spring-cloud-infrastructure.md](standards/13-spring-cloud-infrastructure.md)
- [14-entity-design-patterns.md](standards/14-entity-design-patterns.md)
- [15-dto-form-separation.md](standards/15-dto-form-separation.md)
- [16-validation-sequence-pattern.md](standards/16-validation-sequence-pattern.md)
- [17-api-response-wrapper.md](standards/17-api-response-wrapper.md)
- [18-service-layer-conventions.md](standards/18-service-layer-conventions.md)
- [19-exception-handling-hierarchy.md](standards/19-exception-handling-hierarchy.md)
- [20-inter-service-communication.md](standards/20-inter-service-communication.md)
- [21-caching-strategy.md](standards/21-caching-strategy.md)
- [22-common-library-design.md](standards/22-common-library-design.md)
- [23-enum-as-domain-model.md](standards/23-enum-as-domain-model.md)
- [24-constants-organization.md](standards/24-constants-organization.md)
- [25-jpa-auditing-pattern.md](standards/25-jpa-auditing-pattern.md)
- [26-openapi-documentation.md](standards/26-openapi-documentation.md)
- [27-centralized-logging.md](standards/27-centralized-logging.md)
- [28-test-coverage-enforcement.md](standards/28-test-coverage-enforcement.md)
- [29-container-deployment.md](standards/29-container-deployment.md)
- [30-maven-build-conventions.md](standards/30-maven-build-conventions.md)
- [31-security-authentication.md](standards/31-security-authentication.md)
- [32-repository-conventions.md](standards/32-repository-conventions.md)
- [33-test-case-roadmap.md](standards/33-test-case-roadmap.md)
- [34-frontend-package-structure.md](standards/34-frontend-package-structure.md)
- [35-positive-testing-standards.md](standards/35-positive-testing-standards.md)
- [36-negative-testing-standards.md](standards/36-negative-testing-standards.md)
- [37-edge-case-testing-standards.md](standards/37-edge-case-testing-standards.md)
- [38-test-mocking-strategy.md](standards/38-test-mocking-strategy.md)
- [39-cross-cutting-test-patterns.md](standards/39-cross-cutting-test-patterns.md)
- [40-universal-test-patterns-abstract.md](standards/40-universal-test-patterns-abstract.md)
- [41-testing-standards-python-fastapi.md](standards/41-testing-standards-python-fastapi.md)
- [42-testing-standards-nodejs-express.md](standards/42-testing-standards-nodejs-express.md)
- [43-testing-standards-go.md](standards/43-testing-standards-go.md)
- [44-srs-lifecycle.md](standards/44-srs-lifecycle.md)
- [45-uml-diagram-lifecycle.md](standards/45-uml-diagram-lifecycle.md)
- [46-architecture-documentation.md](standards/46-architecture-documentation.md)
- [TOOL-OPTIMIZATION-LEVEL2-STANDARD.md](standards/TOOL-OPTIMIZATION-LEVEL2-STANDARD.md)
- [csharp-standards.md](standards/csharp-standards.md)
- [django-standards.md](standards/django-standards.md)
- [flask-standards.md](standards/flask-standards.md)
- [java-standards.md](standards/java-standards.md)
- [spring-boot-standards.md](standards/spring-boot-standards.md)

</details>

## `policies/` -- Pipeline policies

One document per policy the SDLC pipeline enforces. These mirror `~/.claude/policies/`, which is the directory `get_policies_dir()` actually reads.

<details><summary>46 file(s)</summary>

- [EXECUTION-SYSTEM-FIXES-SUMMARY.md](policies/EXECUTION-SYSTEM-FIXES-SUMMARY.md)
- [INTELLIGENT-PROMPT-GENERATION-UPGRADE.md](policies/INTELLIGENT-PROMPT-GENERATION-UPGRADE.md)
- [anti-hallucination-enforcement.md](policies/anti-hallucination-enforcement.md)
- [architecture-script-mapping-policy.md](policies/architecture-script-mapping-policy.md)
- [automatic-task-breakdown-policy.md](policies/automatic-task-breakdown-policy.md)
- [callgraph-analysis-policy.md](policies/callgraph-analysis-policy.md)
- [code-graph-analysis-policy.md](policies/code-graph-analysis-policy.md)
- [coding-standards-enforcement-policy.md](policies/coding-standards-enforcement-policy.md)
- [common-failures-prevention.md](policies/common-failures-prevention.md)
- [common-standards-policy.md](policies/common-standards-policy.md)
- [context-management-policy.md](policies/context-management-policy.md)
- [context-reading-policy.md](policies/context-reading-policy.md)
- [cross-project-patterns-policy.md](policies/cross-project-patterns-policy.md)
- [documentation-update-policy.md](policies/documentation-update-policy.md)
- [encoding-validation-policy.md](policies/encoding-validation-policy.md)
- [error-recovery-policy.md](policies/error-recovery-policy.md)
- [file-management-policy.md](policies/file-management-policy.md)
- [final-summary-policy.md](policies/final-summary-policy.md)
- [git-auto-commit-policy.md](policies/git-auto-commit-policy.md)
- [github-issues-integration-policy.md](policies/github-issues-integration-policy.md)
- [hook-system-policy.md](policies/hook-system-policy.md)
- [implementation-execution-policy.md](policies/implementation-execution-policy.md)
- [intelligent-decision-engine-policy.md](policies/intelligent-decision-engine-policy.md)
- [intelligent-model-selection-policy.md](policies/intelligent-model-selection-policy.md)
- [issue-closure-policy.md](policies/issue-closure-policy.md)
- [mcp-plugin-discovery-policy.md](policies/mcp-plugin-discovery-policy.md)
- [metrics-monitoring-policy.md](policies/metrics-monitoring-policy.md)
- [parallel-execution-policy.md](policies/parallel-execution-policy.md)
- [pr-code-review-policy.md](policies/pr-code-review-policy.md)
- [proactive-consultation-policy.md](policies/proactive-consultation-policy.md)
- [prompt-generation-policy.md](policies/prompt-generation-policy.md)
- [quality-gate-policy.md](policies/quality-gate-policy.md)
- [recovery-policy.md](policies/recovery-policy.md)
- [session-chaining-policy.md](policies/session-chaining-policy.md)
- [session-memory-policy.md](policies/session-memory-policy.md)
- [session-pruning-policy.md](policies/session-pruning-policy.md)
- [task-phase-enforcement-policy.md](policies/task-phase-enforcement-policy.md)
- [task-progress-tracking-policy.md](policies/task-progress-tracking-policy.md)
- [test-case-policy.md](policies/test-case-policy.md)
- [test-generation-policy.md](policies/test-generation-policy.md)
- [tool-optimization-policy.md](policies/tool-optimization-policy.md)
- [tool-usage-optimization-policy.md](policies/tool-usage-optimization-policy.md)
- [unicode-fix-policy.md](policies/unicode-fix-policy.md)
- [user-preferences-policy.md](policies/user-preferences-policy.md)
- [version-release-policy.md](policies/version-release-policy.md)
- [windows-path-policy.md](policies/windows-path-policy.md)

</details>

## `architecture/` -- Architecture and design

ADRs, pipeline architecture, level design, flow diagrams and the orchestration prompt.

<details><summary>17 file(s)</summary>

- [ADR-002-call-graph-intelligence.md](architecture/ADR-002-call-graph-intelligence.md)
- [ADR-003-runtime-verification-decorator.md](architecture/ADR-003-runtime-verification-decorator.md)
- [ADR-004-opt-in-default.md](architecture/ADR-004-opt-in-default.md)
- [ADR-005-no-llm-in-verifier.md](architecture/ADR-005-no-llm-in-verifier.md)
- [ARCHITECTURE_QUICK_SUMMARY.md](architecture/ARCHITECTURE_QUICK_SUMMARY.md)
- [ARCHITECTURE_REVIEW.md](architecture/ARCHITECTURE_REVIEW.md)
- [HYBRID-EVENT-DRIVEN-ARCHITECTURE.md](architecture/HYBRID-EVENT-DRIVEN-ARCHITECTURE.md)
- [LANGGRAPH-ENGINE.md](architecture/LANGGRAPH-ENGINE.md)
- [LEVEL3-DESIGN.md](architecture/LEVEL3-DESIGN.md)
- [PERMANENT-SOLUTION-ARCHITECTURE.md](architecture/PERMANENT-SOLUTION-ARCHITECTURE.md)
- [PIPELINE_ARCHITECTURE.md](architecture/PIPELINE_ARCHITECTURE.md)
- [POLICIES-AND-SCRIPTS-FLOW.md](architecture/POLICIES-AND-SCRIPTS-FLOW.md)
- [POLICY-CHAIN-FLOWCHART.md](architecture/POLICY-CHAIN-FLOWCHART.md)
- [call-graph-diagram.md](architecture/call-graph-diagram.md)
- [impact_map-l3-collapse-draft.md](architecture/impact_map-l3-collapse-draft.md)
- [orchestration-prompt-v2.1-generic-rules.md](architecture/orchestration-prompt-v2.1-generic-rules.md)
- [orchestration_prompt.md](architecture/orchestration_prompt.md)

</details>

## `guides/` -- How-to guides and runbooks

Getting started, deployment, testing, troubleshooting and operational runbooks.

<details><summary>14 file(s)</summary>

- [00_START_HERE.md](guides/00_START_HERE.md)
- [DEPLOYMENT_GUIDE.md](guides/DEPLOYMENT_GUIDE.md)
- [DOCUMENTATION_TEMPLATES.md](guides/DOCUMENTATION_TEMPLATES.md)
- [LEVEL3-IMPLEMENTATION-GUIDE.md](guides/LEVEL3-IMPLEMENTATION-GUIDE.md)
- [MCP-TOOLS.md](guides/MCP-TOOLS.md)
- [PARALLEL_EXECUTION_STRATEGY.md](guides/PARALLEL_EXECUTION_STRATEGY.md)
- [RUNBOOK_STALE_GRAPH.md](guides/RUNBOOK_STALE_GRAPH.md)
- [STEP-BY-STEP-PROMPTS.md](guides/STEP-BY-STEP-PROMPTS.md)
- [SYNTHESIS-INTEGRATION-GUIDE.md](guides/SYNTHESIS-INTEGRATION-GUIDE.md)
- [TESTING_GUIDE.md](guides/TESTING_GUIDE.md)
- [TROUBLESHOOTING_GUIDE.md](guides/TROUBLESHOOTING_GUIDE.md)
- [WORKFLOW.md](guides/WORKFLOW.md)
- [computer-use-preflight-checklist.md](guides/computer-use-preflight-checklist.md)
- [parallel-execution-quick-guide.md](guides/parallel-execution-quick-guide.md)

</details>

## `reports/` -- Investigations and audits

One-off analyses, audit results, migration notes and summaries. Point-in-time records, not living documents.

<details><summary>20 file(s)</summary>

- [AUTO-FIX-ENFORCEMENT-SUMMARY.md](reports/AUTO-FIX-ENFORCEMENT-SUMMARY.md)
- [AUTO-SYNC-POLICIES.md](reports/AUTO-SYNC-POLICIES.md)
- [CONTEXT_READ_ENFORCEMENT.md](reports/CONTEXT_READ_ENFORCEMENT.md)
- [DEPENDENCY-RESEARCH-STEP.md](reports/DEPENDENCY-RESEARCH-STEP.md)
- [HOOKS-SETUP-2026-03-10.md](reports/HOOKS-SETUP-2026-03-10.md)
- [IMPLEMENTATION-NOTES.md](reports/IMPLEMENTATION-NOTES.md)
- [PLAN-DETECTION-SUMMARY.md](reports/PLAN-DETECTION-SUMMARY.md)
- [SESSION-BLOAT-ANALYSIS.md](reports/SESSION-BLOAT-ANALYSIS.md)
- [SMART-ADAPTIVE-SUMMARY.md](reports/SMART-ADAPTIVE-SUMMARY.md)
- [STEP7_DOCUMENTATION_IMPLEMENTATION.md](reports/STEP7_DOCUMENTATION_IMPLEMENTATION.md)
- [TESTING_SUMMARY.md](reports/TESTING_SUMMARY.md)
- [anthropic-feedback-letter.md](reports/anthropic-feedback-letter.md)
- [naming_audit_report.md](reports/naming_audit_report.md)
- [noqa-audit-todo.md](reports/noqa-audit-todo.md)
- [qa_stream1_verification_report.md](reports/qa_stream1_verification_report.md)
- [refactoring-plan.md](reports/refactoring-plan.md)
- [review-checkpoint-consistency-fix.md](reports/review-checkpoint-consistency-fix.md)
- [session-id-tracking.md](reports/session-id-tracking.md)
- [session-isolation-fix.md](reports/session-isolation-fix.md)
- [session-management-comparison.md](reports/session-management-comparison.md)

</details>

## `releases/` -- Per-release design notes

Design briefs, blueprints and review notes tied to a specific version.

<details><summary>6 file(s)</summary>

- [v1.14.0-design-brief.md](releases/v1.14.0-design-brief.md)
- [v1.14.0-design-output.md](releases/v1.14.0-design-output.md)
- [v1.18.0-blueprint.md](releases/v1.18.0-blueprint.md)
- [v1.18.0-consensus-review.md](releases/v1.18.0-consensus-review.md)
- [v1.18.0-runtime-verification.md](releases/v1.18.0-runtime-verification.md)
- [v1.18.0-squad-lead-instruction.md](releases/v1.18.0-squad-lead-instruction.md)

</details>

## `contributing/` -- Contribution and community files

Issue and PR templates, contributing guide, code of conduct. They live here rather than the repo root because rules/11 permits only five documentation files at the root.

<details><summary>5 file(s)</summary>

- [CODE_OF_CONDUCT.md](contributing/CODE_OF_CONDUCT.md)
- [CONTRIBUTING.md](contributing/CONTRIBUTING.md)
- [bug_report.md](contributing/bug_report.md)
- [feature_request.md](contributing/feature_request.md)
- [pull_request_template.md](contributing/pull_request_template.md)

</details>

## `api/` -- API specifications

OpenAPI and related interface specs.

<details><summary>1 file(s)</summary>

- [OPENAPI_SPEC.yaml](api/OPENAPI_SPEC.yaml)

</details>

## `phase-1-architecture/` -- Phase 1 architecture artefacts

High-level design and feasibility output from the original phase-1 work.

<details><summary>2 file(s)</summary>

- [feasibility_analysis.json](phase-1-architecture/feasibility_analysis.json)
- [hld.md](phase-1-architecture/hld.md)

</details>

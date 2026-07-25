"""standards/integration.py -- Standards Integration Points - Level 2 (SDLC Execution Core).

Moved from langgraph_engine/standards_integration.py to the standards/ domain package.
Backward-compat shim at the original location re-exports from here.

Defines WHERE and HOW standards are applied during execution flow.
Each integration point hooks into a specific step to ensure compliance.

2 Integration Points (live -- both wired into the current graph):
  Step 4 - During code review (after implementation, before PR review)
  Step 7 - During doc update

CHANGE LOG (Level/Step domain-driven rename):
  Removed the old step_1/step_2/step_5 integration points (pre-v1.13.0
  Plan Mode Decision / Plan Execution / Skill Selection hooks). Nothing in
  the live graph has called apply_standards_at_step() with those numbers
  since v1.13.0 collapsed those steps into the single consolidated task-
  orchestration node -- confirmed via repo-wide grep before deletion. Their
  handler functions had also silently collided under one shared name
  (_apply_step1_standards x3) after the mechanical step-prefix rename,
  since old steps 1/2/5 all mapped to the same new-scheme step number;
  removing the dead entries resolves that collision at its root instead of
  papering over it with distinct names for otherwise-unreachable code.

Windows-safe: ASCII only (cp1252 compatible).
"""

from typing import Any, Dict, List

from langgraph_engine.engine_logging.error_logger import ErrorLogger
from langgraph_engine.flow_state import FlowState

STANDARDS_INTEGRATION_POINTS = {
    "step_4": {
        "location": "Code review",
        "purpose": "Code review checks standards compliance",
        "trigger": "during_implementation",
        "applies_to": ["all"],
        "blocking": True,
        "description": (
            "During the implementation review step, code is evaluated against "
            "loaded standards (naming conventions, docstring format, test coverage "
            "thresholds). Review failures trigger a retry loop up to 3 times."
        ),
    },
    "step_7": {
        "location": "Documentation",
        "purpose": "Documentation matches standards",
        "trigger": "during_doc_update",
        "applies_to": ["all"],
        "blocking": False,
        "description": (
            "When updating documentation, standards specify which files must be "
            "updated (e.g., CLAUDE.md, README.md), the required format, and "
            "whether a version bump is needed."
        ),
    },
}


def load_standards(state: FlowState) -> Dict[str, Any]:
    """Load applicable standards from FlowState.

    Aggregates all standards data from FlowState into a single dict for
    use by integration hooks.

    Args:
        state: Current FlowState with loaded standards data.

    Returns:
        Dict with standards data and metadata keyed by standards domain.
    """
    standards: Dict[str, Any] = {}

    tool_rules = state.get("tool_optimization_rules")
    if tool_rules:
        standards["tool_optimization"] = tool_rules

    spring_patterns = state.get("spring_boot_patterns")
    if spring_patterns:
        standards["spring_boot"] = spring_patterns

    merged_rules = state.get("standards_merged_rules")
    if merged_rules:
        standards["merged_rules"] = merged_rules

    standards_selection = state.get("standards_selection")
    if standards_selection:
        standards["selection"] = standards_selection

    is_java = state.get("is_java_project", False)
    detected_framework = state.get("detected_framework", "")
    selection_project_type = (standards_selection or {}).get("project_type", "") if standards_selection else ""

    if selection_project_type:
        project_type = selection_project_type
    elif is_java:
        project_type = "java"
    else:
        project_type = "python"

    standards_count = state.get("standards_count", 0)
    standards["__meta"] = {
        "count": standards_count,
        "loaded": state.get("standards_loaded", False),
        "legacy_level2_status": state.get("level2_status", "UNKNOWN"),
        "project_type": project_type,
        "framework": detected_framework or (standards_selection or {}).get("framework", "unknown"),
        "priority_chain": "custom(4) > team(3) > framework(2) > library_skill(1.5) > language(1) > library_language_skill(0.5)",
    }

    return standards


def apply_standards_at_step(step: int, state: FlowState) -> FlowState:
    """Apply standards at a specific pipeline step.

    Args:
        step: Step number (4 or 7).
        state: Current FlowState.

    Returns:
        Updated FlowState with standards_applied_at_step_N flag set.
    """
    step_key = "step_{}".format(step)
    integration = STANDARDS_INTEGRATION_POINTS.get(step_key)

    if not integration:
        return state

    import os

    session_id = state.get("session_id") or os.environ.get("CURRENT_SESSION_ID", "") or "unknown-session"
    logger = ErrorLogger(session_id)

    logger.log_decision(
        step="Level 2 Standards - Step {}".format(step),
        decision="Applying standards at {}".format(integration["location"]),
        reasoning=integration["purpose"],
        options=["apply", "skip"],
        chosen_option="apply",
    )

    standards = load_standards(state)

    hook_dispatch = {
        4: _apply_step4_standards,
        7: _apply_step7_standards,
    }

    hook_fn = hook_dispatch.get(step)
    if hook_fn:
        try:
            result = hook_fn(state, standards, logger)
            if result:
                state.update(result)
        except Exception as exc:
            logger.log_error(
                step="Level 2 - Step {}".format(step),
                error_message="Standards hook raised an exception: {}".format(exc),
                severity="WARNING",
                error_type="StandardsHookError",
                recovery_action="Continuing without standards enforcement for this step",
                context={"step": step, "integration_point": step_key},
            )

    state["standards_applied_step{}".format(step)] = True
    logger.save_audit_trail()

    return state


def _apply_step4_standards(
    state: FlowState,
    standards: Dict[str, Any],
    logger: ErrorLogger,
) -> Dict[str, Any]:
    """Step 4 hook: provide standards checklist for code review.

    Args:
        state:     Current FlowState.
        standards: Aggregated standards dict.
        logger:    ErrorLogger for audit trail.

    Returns:
        State updates to merge.
    """
    updates: Dict[str, Any] = {}

    project_type = standards.get("__meta", {}).get("project_type", "unknown")
    checklist = _build_review_checklist(project_type, standards)

    updates["step4_standards_checklist"] = {
        "checklist": checklist,
        "total_checks": len(checklist),
        "project_type": project_type,
        "note": "All checklist items must pass before PR can be merged.",
    }

    logger.log_decision(
        step="Level 2 - Step 4",
        decision="Code review standards checklist prepared",
        reasoning="project_type={}, checks={}".format(project_type, len(checklist)),
        chosen_option="checklist_ready",
    )

    return updates


def _apply_step7_standards(
    state: FlowState,
    standards: Dict[str, Any],
    logger: ErrorLogger,
) -> Dict[str, Any]:
    """Step 7 hook: specify documentation requirements from standards.

    Args:
        state:     Current FlowState.
        standards: Aggregated standards dict.
        logger:    ErrorLogger for audit trail.

    Returns:
        State updates to merge.
    """
    updates: Dict[str, Any] = {}

    project_type = standards.get("__meta", {}).get("project_type", "unknown")
    doc_requirements = _build_doc_requirements(project_type, standards)

    updates["step7_standards_doc_requirements"] = {
        "required_updates": doc_requirements,
        "total_required": len(doc_requirements),
        "project_type": project_type,
        "note": "Documentation must satisfy these requirements before closure.",
    }

    logger.log_decision(
        step="Level 2 - Step 7",
        decision="Documentation requirements loaded from standards",
        reasoning="project_type={}, required_updates={}".format(project_type, len(doc_requirements)),
        chosen_option="doc_requirements_set",
    )

    return updates


def _build_review_checklist(
    project_type: str,
    standards: Dict[str, Any],
) -> List[Dict[str, str]]:
    """Build code review checklist derived from active standards."""
    checklist: List[Dict[str, str]] = []

    checklist += [
        {"check": "no_syntax_errors", "description": "Code has no syntax errors"},
        {"check": "no_bare_except", "description": "No bare except clauses"},
        {"check": "no_hardcoded_secrets", "description": "No hardcoded API keys or passwords"},
    ]

    if project_type == "python":
        checklist += [
            {"check": "snake_case_functions", "description": "All function names use snake_case"},
            {"check": "pascal_case_classes", "description": "All class names use PascalCase"},
            {"check": "type_hints_present", "description": "Public functions have type hints"},
            {"check": "docstrings_present", "description": "Public functions have docstrings"},
            {"check": "pytest_tests_exist", "description": "pytest tests present for new code"},
            {"check": "service_layer_separation", "description": "Business logic in services/, not in route handlers"},
        ]

        tool_rules = standards.get("tool_optimization", {})
        if tool_rules:
            checklist.append(
                {
                    "check": "tool_optimization_compliant",
                    "description": (
                        "Read calls respect {} line limit; "
                        "Grep calls use head_limit <= {}".format(
                            tool_rules.get("read_max_lines", 500),
                            tool_rules.get("grep_max_results", 100),
                        )
                    ),
                }
            )

    elif project_type == "java":
        checklist += [
            {"check": "spring_annotations", "description": "Spring annotations used correctly"},
            {"check": "service_layer", "description": "@Service classes contain business logic"},
            {"check": "repository_layer", "description": "@Repository classes handle persistence"},
            {"check": "exception_handling", "description": "Exceptions handled via @ControllerAdvice or similar"},
        ]

    checklist += _build_selected_standards_checklist_items(standards)

    return checklist


def _build_selected_standards_checklist_items(standards: Dict[str, Any]) -> List[Dict[str, str]]:
    """Surface each standard select_standards() loaded (FR-3/FR-4, ADR-4) as a
    checklist item.

    Reads ``standards["selection"]["standards_list"]`` -- populated via
    ``state["standards_selection"]``, which Step 0's PRE-INJECTION D block
    sets from ``select_standards()`` -- so custom/team/framework/
    library_skill/language/library_language-sourced content actually reaches
    Step 4's review checklist instead of only the hardcoded project_type
    defaults above.
    """
    items: List[Dict[str, str]] = []
    selection = standards.get("selection") or {}
    for std in selection.get("standards_list", []):
        std_id = std.get("id", "unknown")
        source = std.get("source", "unknown")
        items.append(
            {
                "check": "standards_source_{}".format(std_id),
                "description": "Code complies with '{}' ({})".format(std_id, source),
            }
        )
    return items


def _build_doc_requirements(
    project_type: str,
    standards: Dict[str, Any],
) -> List[Dict[str, str]]:
    """Build documentation update requirements from standards."""
    requirements: List[Dict[str, str]] = [
        {
            "file": "CLAUDE.md",
            "action": "update",
            "note": "Reflect any new components, patterns, or dependencies added",
        },
    ]

    if project_type == "python":
        requirements += [
            {
                "file": "requirements.txt",
                "action": "update_if_changed",
                "note": "Keep in sync if new packages were added",
            },
        ]
    elif project_type == "java":
        requirements += [
            {
                "file": "pom.xml / build.gradle",
                "action": "update_if_changed",
                "note": "Keep dependency versions accurate",
            },
        ]

    requirements += _build_selected_standards_doc_requirements(standards)

    return requirements


def _build_selected_standards_doc_requirements(standards: Dict[str, Any]) -> List[Dict[str, str]]:
    """Surface library-sourced standards loaded by select_standards() (FR-4,
    ADR-4) as a documentation requirement note.

    Reads ``standards["selection"]["standards_list"]`` the same way
    ``_build_selected_standards_checklist_items`` does, but scoped to the
    ``library_skill_standards``/``library_language_standards`` sources only
    -- these are the newly-introduced FR-4 content this fix is closing the
    loop for, and are worth calling out explicitly in doc requirements
    rather than adding a requirement row per custom/team markdown file.
    """
    items: List[Dict[str, str]] = []
    selection = standards.get("selection") or {}
    for std in selection.get("standards_list", []):
        source = std.get("source", "unknown")
        if source not in ("library_skill_standards", "library_language_standards"):
            continue
        items.append(
            {
                "file": std.get("file", "unknown"),
                "action": "reference",
                "note": "Documentation should reflect the '{}' standard sourced from {}".format(
                    std.get("id", "unknown"), source
                ),
            }
        )
    return items


def _is_python_only_skill(skill_name: str) -> bool:
    """Return True if a skill name is clearly Python-only."""
    python_keywords = {"flask", "django", "fastapi", "python", "pydantic", "sqlalchemy"}
    name_lower = skill_name.lower()
    return any(kw in name_lower for kw in python_keywords)


def _is_java_only_skill(skill_name: str) -> bool:
    """Return True if a skill name is clearly Java-only."""
    java_keywords = {"spring", "java", "maven", "gradle", "hibernate", "jpa", "quarkus"}
    name_lower = skill_name.lower()
    return any(kw in name_lower for kw in java_keywords)

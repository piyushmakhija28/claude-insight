"""StepKeys - Constants for flow state dictionary keys.

Centralizes all step state key strings so typos become import errors
instead of silent bugs. String VALUES are preserved for backward
compatibility with flow-trace.json and existing state serialization,
except where noted in CHANGE LOG entries below.

Naming scheme (domain-driven rename, see CHANGE LOG):
    Level 0 - Pre-Flight Sanity Guard   (was "Level -1: Auto-Fix")
    Level 1 - Session & Context Sync    (unchanged)
    Level 2 - SDLC Execution Core       (was "Level 3: Execution"; dead
                                          "Level 2: Standards" retired --
                                          it never had pipeline nodes)
    Step 0  - Pre-Analysis & CallGraph Scan       (was "Pre-0")
    Step 1  - Task Orchestration & Planning       (was "Step 0")
    Step 2  - Issue Tracking (GitHub/Jira)        (was "Step 8")
    Step 3  - Branch & Workspace Setup            (was "Step 9")
    Step 4  - Implementation & Code Generation    (was "Step 10")
    Step 5  - Pull Request & Automated Review     (was "Step 11")
    Step 6  - Issue & Ticket Closure              (was "Step 12")
    Step 7  - Documentation & UML Generation      (was "Step 13")
    Step 8  - Final Telemetry & Summary Report    (was "Step 14")

CHANGE LOG (this rename):
    Renamed all Level/Step key VALUES to the scheme above. Deleted ~25
    entries confirmed (via repo-wide grep) to have zero readers outside
    this file -- they described old Steps 1-7 (pre-v1.13.0 scheme) that
    no longer execute: STEP1_REASONING/ERROR, PLAN_STATUS, STEP2_ERROR/
    IMPACT_ANALYSIS/GRAPH_RISK_LEVEL/AFFECTED_METHODS, STEP3_TASK_COUNT/
    VALIDATION_STATUS/ERROR/PHASE_FILE_MAP/GRAPH_SNAPSHOT, STEP4_
    REFINEMENT_STATUS/COMPLEXITY_ADJUSTED/ERROR/PHASE_CONTEXTS/
    PHASE_SCOPE_FILES/OLD_CONTEXT_CLEARED, STEP5_REASONING/ERROR,
    STEP6_VALIDATION_STATUS/ERROR, SKILL_READY, AGENT_READY,
    PROMPT_SAVED/FILE/SIZE, STEP7_ERROR, LEVEL2_STATUS (never assigned
    a real value anywhere -- "Level 2: Standards" has no pipeline nodes).
    Old Steps 1-7 identifiers named above are gone; fields still
    actively read (SELECTED_MODEL, SKILL, AGENT, SKILLS, AGENTS,
    SKILL_DEFINITION, AGENT_DEFINITION, PLAN_REQUIRED, PLAN_EXECUTION,
    TASKS_VALIDATED) were re-prefixed to step1_* because the single
    consolidated Step 1 (Task Orchestration) node is what actually
    populates them now.

Usage:
    state.get(StepKeys.TASK_TYPE, "task")
    state[StepKeys.REVIEW_PASSED] = True
"""


class StepKeys:
    """Constants for flow state dictionary keys."""

    # ------------------------------------------------------------------
    # SESSION / PROJECT IDENTIFICATION
    # ------------------------------------------------------------------
    SESSION_ID = "session_id"
    TIMESTAMP = "timestamp"
    PROJECT_ROOT = "project_root"
    IS_JAVA_PROJECT = "is_java_project"
    IS_FRESH_PROJECT = "is_fresh_project"
    SESSION_DIR = "session_dir"
    SESSION_PATH = "session_path"

    # ------------------------------------------------------------------
    # USER MESSAGE
    # ------------------------------------------------------------------
    USER_MESSAGE = "user_message"
    USER_MESSAGE_ORIGINAL = "user_message_original"

    # ------------------------------------------------------------------
    # LEVEL 0: PRE-FLIGHT SANITY GUARD
    # ------------------------------------------------------------------
    PREFLIGHT_STATUS = "preflight_status"
    PREFLIGHT_USER_CHOICE = "preflight_user_choice"
    PREFLIGHT_RETRY_COUNT = "preflight_retry_count"
    PREFLIGHT_FIXES_APPLIED = "preflight_fixes_applied"
    PREFLIGHT_FIX_ERRORS = "preflight_fix_errors"
    PREFLIGHT_READY_TO_RETRY = "preflight_ready_to_retry"
    PREFLIGHT_MAX_ATTEMPTS_REACHED = "preflight_max_attempts_reached"
    PREFLIGHT_FATAL_FAILURE = "preflight_fatal_failure"
    PREFLIGHT_FAILED_CHECKS = "preflight_failed_checks"
    ENCODING_NONASCII_FILES = "encoding_nonascii_files"
    UNICODE_CHECK = "unicode_check"
    ENCODING_CHECK = "encoding_check"
    WINDOWS_PATH_CHECK = "windows_path_check"
    FAILURE_KB_LOADED = "failure_kb_loaded"
    FAILURE_KB_SUGGESTIONS = "failure_kb_suggestions"

    # ------------------------------------------------------------------
    # LEVEL 1: SESSION & CONTEXT SYNCHRONIZATION
    # ------------------------------------------------------------------
    CONTEXT_LOADED = "context_loaded"
    CONTEXT_PERCENTAGE = "context_percentage"
    CONTEXT_THRESHOLD_EXCEEDED = "context_threshold_exceeded"
    CONTEXT_CACHE_HIT = "context_cache_hit"
    FILES_LOADED_COUNT = "files_loaded_count"
    SESSION_CHAIN_LOADED = "session_chain_loaded"
    SESSION_PARENT_ID = "session_parent_id"
    SESSION_TAGS = "session_tags"
    SESSION_PRUNING_ERRORS = "session_pruning_errors"
    PATTERNS_DETECTED = "patterns_detected"
    PREFERENCES_DATA = "preferences_data"
    COMPLEXITY_SCORE = "complexity_score"
    GRAPH_COMPLEXITY_SCORE = "graph_complexity_score"
    COMBINED_COMPLEXITY_SCORE = "combined_complexity_score"
    LEVEL1_STATUS = "level1_status"

    # ------------------------------------------------------------------
    # STANDARDS (always-on, loaded from disk -- not a numbered pipeline
    # level; the old "Level 2: Standards" had zero pipeline nodes and is
    # retired from the level count. These fields are still populated by
    # Level 1's context loader.)
    # ------------------------------------------------------------------
    STANDARDS_LOADED = "standards_loaded"
    STANDARDS_COUNT = "standards_count"
    JAVA_STANDARDS_LOADED = "java_standards_loaded"
    SPRING_BOOT_PATTERNS = "spring_boot_patterns"
    TOOL_OPTIMIZATION_RULES = "tool_optimization_rules"
    TOOL_OPTIMIZATION_LOADED = "tool_optimization_loaded"
    DETECTED_FRAMEWORK = "detected_framework"
    MCP_DISCOVERED_COUNT = "mcp_discovered_count"

    # ------------------------------------------------------------------
    # STEP 0: PRE-ANALYSIS & CALLGRAPH SCAN
    # ------------------------------------------------------------------
    STEP0_PROJECT_CONTEXT = "step0_project_context"
    STEP0_FILES_READ = "step0_files_read"
    STEP0_PROJECT_CONTEXT_ERROR = "step0_project_context_error"
    STEP0_PROJECT_CONTEXT_TIME_MS = "step0_project_context_time_ms"
    STEP0_CALLGRAPH_SNAPSHOT = "step0_callgraph_snapshot"
    STEP0_CALLGRAPH_AVAILABLE = "step0_callgraph_available"
    STEP0_CALLGRAPH_ERROR = "step0_callgraph_error"
    STEP0_CALLGRAPH_TIME_MS = "step0_callgraph_time_ms"

    # ------------------------------------------------------------------
    # USER PREFERENCES CONTEXT
    # ------------------------------------------------------------------
    USER_PREFERENCES_CONTEXT = "user_preferences_context"

    # ------------------------------------------------------------------
    # STEP 1: TASK ORCHESTRATION & PLANNING
    # ------------------------------------------------------------------
    TASK_TYPE = "step1_task_type"
    COMPLEXITY = "step1_complexity"
    REASONING = "step1_reasoning"
    TASKS = "step1_tasks"
    TASK_COUNT = "step1_task_count"
    STEP1_DOCS_FOUND = "step1_docs_found"
    STEP1_TARGET_FILES = "step1_target_files"
    STEP1_ERROR = "step1_error"
    ORCHESTRATION_PROMPT = "orchestration_prompt"
    ROUTING = "routing"
    ORCHESTRATOR_RESULT = "orchestrator_result"
    PLAN_REQUIRED = "step1_plan_required"
    PLAN_EXECUTION = "step1_plan_execution"
    TASKS_VALIDATED = "step1_tasks_validated"
    SELECTED_MODEL = "step1_model"
    SKILL = "step1_skill"
    AGENT = "step1_agent"
    SKILLS = "step1_skills"
    AGENTS = "step1_agents"
    SKILL_DEFINITION = "step1_skill_definition"
    AGENT_DEFINITION = "step1_agent_definition"

    # ------------------------------------------------------------------
    # STEP 2: ISSUE TRACKING (GITHUB / JIRA)
    # ------------------------------------------------------------------
    ISSUE_STATUS = "step2_status"
    ISSUE_URL = "step2_issue_url"
    STEP2_ERROR = "step2_error"

    # ------------------------------------------------------------------
    # STEP 3: BRANCH & WORKSPACE SETUP
    # ------------------------------------------------------------------
    BRANCH_NAME = "step3_branch_name"
    BRANCH_STATUS = "step3_status"
    STEP3_ERROR = "step3_error"

    # ------------------------------------------------------------------
    # STEP 4: IMPLEMENTATION & CODE GENERATION
    # ------------------------------------------------------------------
    IMPLEMENTATION_STATUS = "step4_implementation_status"
    STEP4_ERROR = "step4_error"
    STEP4_CALL_CONTEXT = "step4_call_context"
    STEP4_PRE_CHANGE_GRAPH = "step4_pre_change_graph"
    STEP4_SUGGESTED_TEST_SCOPE = "step4_suggested_test_scope"

    # ------------------------------------------------------------------
    # STEP 5: PULL REQUEST & AUTOMATED REVIEW
    # ------------------------------------------------------------------
    REVIEW_PASSED = "step5_review_passed"
    RETRY_COUNT = "step5_retry_count"
    PR_URL = "step5_pr_url"
    STEP5_STATUS = "step5_status"
    STEP5_ERROR = "step5_error"
    STEP5_IMPACT_REVIEW = "step5_impact_review"
    STEP5_BREAKING_CHANGES = "step5_breaking_changes"
    STEP5_RISK_ASSESSMENT = "step5_risk_assessment"

    # ------------------------------------------------------------------
    # JIRA INTEGRATION
    # ------------------------------------------------------------------
    JIRA_ENABLED = "jira_enabled"
    JIRA_ISSUE_KEY = "jira_issue_key"
    JIRA_ISSUE_URL = "jira_issue_url"
    JIRA_ISSUE_CREATED = "jira_issue_created"
    JIRA_PR_LINKED = "jira_pr_linked"
    JIRA_ISSUE_CLOSED = "jira_issue_closed"
    JIRA_ERROR = "jira_error"

    # ------------------------------------------------------------------
    # FIGMA INTEGRATION
    # ------------------------------------------------------------------
    FIGMA_ENABLED = "figma_enabled"
    FIGMA_FILE_KEY = "figma_file_key"
    FIGMA_DESIGN_TOKENS = "figma_design_tokens"
    FIGMA_PROMPT_SNIPPET = "figma_prompt_snippet"
    FIGMA_ERROR = "figma_error"

    # ------------------------------------------------------------------
    # STEP 6: ISSUE & TICKET CLOSURE
    # ------------------------------------------------------------------
    ISSUE_CLOSED = "step6_issue_closed"
    STEP6_STATUS = "step6_status"
    STEP6_ERROR = "step6_error"

    # ------------------------------------------------------------------
    # STEP 7: DOCUMENTATION & UML GENERATION
    # ------------------------------------------------------------------
    DOCUMENTATION_STATUS = "step7_documentation_status"
    UPDATE_COUNT = "step7_update_count"
    STEP7_DOCS_CREATED = "step7_docs_created"
    STEP7_ERROR = "step7_error"

    # ------------------------------------------------------------------
    # STEP 8: FINAL TELEMETRY & SUMMARY REPORT
    # ------------------------------------------------------------------
    SUMMARY_SAVED = "step8_summary_saved"
    STEP8_STATUS = "step8_status"
    VOICE_SENT = "step8_voice_sent"
    STEP8_ERROR = "step8_error"

    # ------------------------------------------------------------------
    # WORKFLOW MEMORY & OPTIMIZATION
    # ------------------------------------------------------------------
    WORKFLOW_MEMORY = "workflow_memory"
    WORKFLOW_MEMORY_SIZE_KB = "workflow_memory_size_kb"
    STEP_OPTIMIZATION_STATS = "step_optimization_stats"

    # ------------------------------------------------------------------
    # PIPELINE & OUTPUT
    # ------------------------------------------------------------------
    PIPELINE = "pipeline"
    ERRORS = "errors"
    WARNINGS = "warnings"
    FINAL_STATUS = "final_status"

    # ------------------------------------------------------------------
    # USER INTERACTION SYSTEM
    # ------------------------------------------------------------------
    USER_INTERACTIONS = "user_interactions"
    PENDING_INTERACTIONS = "pending_interactions"

    # ------------------------------------------------------------------
    # DEPENDENCY RESOLUTION
    # ------------------------------------------------------------------
    DEPENDENCY_RESOLUTION = "dependency_resolution"
    UNRESOLVED_INTERNAL_DEPS = "unresolved_internal_deps"
    DEPENDENCY_GRAPH_ENHANCED = "dependency_graph_enhanced"

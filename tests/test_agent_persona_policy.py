"""
test_agent_persona_policy.py - Unit tests for
hooks/pre_tool_enforcer/policies/agent_persona.py

Covers check_agent_persona: blocks general-purpose (or unset) subagent_type
spawns that lack an injected library persona, blocks a '---persona---'
block that names an agent but never actually carries its skills (empty
skills: field, or declared skills with no matching SKILL.md read path),
allows named built-in subagent types, allows the '[GENERIC-OK]' escape
hatch, and never raises on malformed input.

Windows-safe: ASCII only, no Unicode characters.
"""

import importlib.util as _ilu
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_MODULE_PATH = _REPO_ROOT / "hooks" / "pre_tool_enforcer" / "policies" / "agent_persona.py"

_spec = _ilu.spec_from_file_location("agent_persona", _MODULE_PATH)
agent_persona = _ilu.module_from_spec(_spec)
sys.modules["agent_persona"] = agent_persona
_spec.loader.exec_module(agent_persona)


_COMPLIANT_PROMPT = (
    "---persona---\n"
    "agent: deep-web-researcher\n"
    "kg_route: rnd-intelligence\n"
    "skills: [research-methodology-core]\n"
    "---\n"
    "You are deep-web-researcher.\n\n"
    "FIRST, before doing anything, READ these skill files and apply them:\n"
    "- skills/research-methodology-core/SKILL.md\n\n"
    "TASK: research X"
)


class TestCheckAgentPersona:
    def test_blocks_general_purpose_without_persona(self):
        blocked, msg = agent_persona.check_agent_persona(
            "Agent",
            {"subagent_type": "general-purpose", "prompt": "go research X"},
        )
        assert blocked is True
        assert "PRE-TOOL BLOCKED" in msg

    def test_allows_when_persona_carries_its_skills(self):
        blocked, msg = agent_persona.check_agent_persona(
            "Agent",
            {"subagent_type": "general-purpose", "prompt": _COMPLIANT_PROMPT},
        )
        assert blocked is False
        assert msg == ""

    def test_allows_when_generic_ok_escape_hatch_present(self):
        blocked, msg = agent_persona.check_agent_persona(
            "Agent",
            {"subagent_type": "general-purpose", "prompt": "[GENERIC-OK] one-off cleanup task"},
        )
        assert blocked is False
        assert msg == ""

    def test_allows_named_builtin_subagent_type(self):
        blocked, msg = agent_persona.check_agent_persona(
            "Agent",
            {"subagent_type": "Explore", "prompt": "find config loader"},
        )
        assert blocked is False
        assert msg == ""

    def test_ignores_non_agent_tool_names(self):
        blocked, msg = agent_persona.check_agent_persona(
            "Bash",
            {"subagent_type": "general-purpose", "prompt": "go research X"},
        )
        assert blocked is False
        assert msg == ""

    def test_blocks_task_tool_with_general_purpose(self):
        blocked, msg = agent_persona.check_agent_persona(
            "Task",
            {"subagent_type": "general-purpose", "prompt": "go research X"},
        )
        assert blocked is True
        assert "PRE-TOOL BLOCKED" in msg

    def test_blocks_when_subagent_type_missing_entirely(self):
        blocked, msg = agent_persona.check_agent_persona(
            "Agent",
            {"prompt": "go research X"},
        )
        assert blocked is True

    def test_uses_description_when_prompt_absent(self):
        blocked, msg = agent_persona.check_agent_persona(
            "Agent",
            {"subagent_type": "general-purpose", "description": _COMPLIANT_PROMPT},
        )
        assert blocked is False

    def test_none_tool_input_does_not_raise(self):
        blocked, msg = agent_persona.check_agent_persona("Agent", None)
        assert blocked is False
        assert msg == ""

    def test_malformed_subagent_type_does_not_raise(self):
        blocked, msg = agent_persona.check_agent_persona(
            "Agent",
            {"subagent_type": 12345, "prompt": None},
        )
        assert isinstance(blocked, bool)

    def test_empty_dict_tool_input_does_not_raise(self):
        blocked, msg = agent_persona.check_agent_persona("Agent", {})
        assert blocked is True

    def test_non_dict_tool_input_does_not_raise(self):
        blocked, msg = agent_persona.check_agent_persona("Agent", "not-a-dict")
        assert blocked is False
        assert msg == ""

    def test_allows_skill_md_authoring_without_marker(self):
        blocked, msg = agent_persona.check_agent_persona(
            "Agent",
            {
                "subagent_type": "general-purpose",
                "prompt": "Write the file `skills/r-statistical-computing-core/SKILL.md` for claude-global-library.",
            },
        )
        assert blocked is False
        assert msg == ""

    def test_allows_agent_md_authoring_without_marker(self):
        blocked, msg = agent_persona.check_agent_persona(
            "Agent",
            {
                "subagent_type": "general-purpose",
                "description": "Author agents/zig-mathematics-expert/agent.md for Domain 67.",
            },
        )
        assert blocked is False
        assert msg == ""

    def test_allows_skill_md_authoring_with_backslash_path(self):
        blocked, msg = agent_persona.check_agent_persona(
            "Agent",
            {
                "subagent_type": "general-purpose",
                "prompt": r"Write skills\r-advanced-modeling-core\SKILL.md now.",
            },
        )
        assert blocked is False
        assert msg == ""

    def test_still_blocks_unrelated_generic_prompt_mentioning_skills_word(self):
        blocked, msg = agent_persona.check_agent_persona(
            "Agent",
            {
                "subagent_type": "general-purpose",
                "prompt": "Review our skills and agents directory structure and summarize it.",
            },
        )
        assert blocked is True

    # --- hollow-persona coverage (the actual bug this hardening closes) ---

    def test_blocks_persona_with_no_skills_field(self):
        blocked, msg = agent_persona.check_agent_persona(
            "Agent",
            {
                "subagent_type": "general-purpose",
                "prompt": "---persona---\nagent: deep-web-researcher\n---\nresearch X",
            },
        )
        assert blocked is True
        assert "skills:" in msg

    def test_blocks_persona_with_empty_skills_list(self):
        blocked, msg = agent_persona.check_agent_persona(
            "Agent",
            {
                "subagent_type": "general-purpose",
                "prompt": "---persona---\nagent: deep-web-researcher\nskills: []\n---\nresearch X",
            },
        )
        assert blocked is True
        assert "skills:" in msg

    def test_blocks_persona_with_declared_skill_but_no_read_path(self):
        blocked, msg = agent_persona.check_agent_persona(
            "Agent",
            {
                "subagent_type": "general-purpose",
                "prompt": (
                    "---persona---\nagent: deep-web-researcher\n"
                    "skills: [research-methodology-core]\n---\nresearch X, no read instruction"
                ),
            },
        )
        assert blocked is True
        assert "research-methodology-core" in msg

    def test_blocks_persona_with_unclosed_block(self):
        blocked, msg = agent_persona.check_agent_persona(
            "Agent",
            {
                "subagent_type": "general-purpose",
                "prompt": "---persona---\nagent: deep-web-researcher\nskills: [research-methodology-core]\nno closing dashes here",
            },
        )
        assert blocked is True

    def test_allows_persona_with_multiline_yaml_skills_list(self):
        prompt = (
            "---persona---\n"
            "agent: orchestrator-agent\n"
            "skills:\n"
            "  - ai-agents-core\n"
            "  - system-design\n"
            "---\n"
            "READ these skill files first:\n"
            "- skills/ai-agents-core/SKILL.md\n"
            "- skills/system-design/SKILL.md\n"
            "TASK: plan the workflow"
        )
        blocked, msg = agent_persona.check_agent_persona(
            "Agent",
            {"subagent_type": "general-purpose", "prompt": prompt},
        )
        assert blocked is False
        assert msg == ""

    def test_allows_persona_with_backslash_skill_read_path(self):
        prompt = (
            "---persona---\nagent: deep-web-researcher\n"
            "skills: [research-methodology-core]\n---\n"
            r"READ: skills\research-methodology-core\SKILL.md" + "\nTASK: research X"
        )
        blocked, msg = agent_persona.check_agent_persona(
            "Agent",
            {"subagent_type": "general-purpose", "prompt": prompt},
        )
        assert blocked is False
        assert msg == ""

    def test_blocks_persona_when_only_some_declared_skills_have_read_paths(self):
        prompt = (
            "---persona---\n"
            "agent: orchestrator-agent\n"
            "skills: [ai-agents-core, system-design]\n"
            "---\n"
            "READ:\n- skills/ai-agents-core/SKILL.md\n"
            "TASK: plan the workflow"
        )
        blocked, msg = agent_persona.check_agent_persona(
            "Agent",
            {"subagent_type": "general-purpose", "prompt": prompt},
        )
        assert blocked is True
        problem_line = [line for line in msg.splitlines() if "Problem" in line][0]
        assert "system-design" in problem_line
        assert "ai-agents-core" not in problem_line

    def test_escape_hatch_still_bypasses_hollow_persona_check(self):
        blocked, msg = agent_persona.check_agent_persona(
            "Agent",
            {
                "subagent_type": "general-purpose",
                "prompt": "[GENERIC-OK] ---persona---\nagent: x\n---\nno skills here, but explicitly generic-ok",
            },
        )
        assert blocked is False
        assert msg == ""

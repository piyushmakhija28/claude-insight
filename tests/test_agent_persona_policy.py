"""
test_agent_persona_policy.py - Unit tests for
hooks/pre_tool_enforcer/policies/agent_persona.py

Covers check_agent_persona: blocks general-purpose (or unset) subagent_type
spawns that lack an injected library persona, blocks a '---persona---'
block that names an agent but never actually carries its skills (empty
skills: field, or declared skills with no matching SKILL.md read path),
blocks a self-consistent-but-incomplete persona block that omits a real
mandatory skill for a known library agent (ground-truth cross-check
against a knowledge-graph/_master/agents_all.json registry, fail-open when
that registry cannot be located -- this hook runs globally, not just in
projects that use claude-global-library), allows named built-in
subagent types, allows the '[GENERIC-OK]' escape hatch, and never raises
on malformed input.

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


_FAKE_REGISTRY = [
    {
        "name": "hallucination-detector",
        "mandatory_skills": ["hallucination-detection-core", "uncertainty-quantification-core"],
    },
    {
        "name": "orchestrator-agent",
        "mandatory_skills": ["ai-agents-core", "prompt-engineering-core", "system-design"],
    },
]


def _compliant_prompt_for(agent_name, skills):
    skills_yaml = ", ".join(skills)
    reads = "\n".join("- skills/{0}/SKILL.md".format(s) for s in skills)
    return (
        "---persona---\n"
        "agent: {0}\n"
        "skills: [{1}]\n"
        "---\n"
        "READ these skill files first:\n"
        "{2}\n"
        "TASK: do the thing"
    ).format(agent_name, skills_yaml, reads)


class TestGroundTruthMandatorySkillCheck:
    """Covers failure mode 3: a persona block that is internally
    self-consistent (checks 1-2 pass) but omits a real mandatory skill for
    a known library agent, per a (monkeypatched) agents_all.json registry.
    """

    def test_blocks_when_registry_agent_missing_a_mandatory_skill(self, monkeypatch):
        monkeypatch.setattr(agent_persona, "_resolve_agents_registry", lambda prompt: _FAKE_REGISTRY)
        prompt = _compliant_prompt_for("hallucination-detector", ["hallucination-detection-core"])
        blocked, msg = agent_persona.check_agent_persona(
            "Agent", {"subagent_type": "general-purpose", "prompt": prompt}
        )
        assert blocked is True
        assert "uncertainty-quantification-core" in msg
        assert "hallucination-detector" in msg

    def test_allows_when_registry_agent_has_all_mandatory_skills(self, monkeypatch):
        monkeypatch.setattr(agent_persona, "_resolve_agents_registry", lambda prompt: _FAKE_REGISTRY)
        prompt = _compliant_prompt_for(
            "hallucination-detector", ["hallucination-detection-core", "uncertainty-quantification-core"]
        )
        blocked, msg = agent_persona.check_agent_persona(
            "Agent", {"subagent_type": "general-purpose", "prompt": prompt}
        )
        assert blocked is False
        assert msg == ""

    def test_allows_extra_optional_skills_beyond_mandatory_set(self, monkeypatch):
        monkeypatch.setattr(agent_persona, "_resolve_agents_registry", lambda prompt: _FAKE_REGISTRY)
        prompt = _compliant_prompt_for(
            "hallucination-detector",
            ["hallucination-detection-core", "uncertainty-quantification-core", "rag-faithfulness-core"],
        )
        blocked, msg = agent_persona.check_agent_persona(
            "Agent", {"subagent_type": "general-purpose", "prompt": prompt}
        )
        assert blocked is False
        assert msg == ""

    def test_fails_open_when_agent_name_not_in_registry(self, monkeypatch):
        monkeypatch.setattr(agent_persona, "_resolve_agents_registry", lambda prompt: _FAKE_REGISTRY)
        prompt = _compliant_prompt_for("some-project-local-custom-agent", ["some-custom-skill-core"])
        blocked, msg = agent_persona.check_agent_persona(
            "Agent", {"subagent_type": "general-purpose", "prompt": prompt}
        )
        assert blocked is False
        assert msg == ""

    def test_fails_open_when_registry_cannot_be_resolved(self, monkeypatch):
        monkeypatch.setattr(agent_persona, "_resolve_agents_registry", lambda prompt: None)
        prompt = _compliant_prompt_for("hallucination-detector", ["hallucination-detection-core"])
        blocked, msg = agent_persona.check_agent_persona(
            "Agent", {"subagent_type": "general-purpose", "prompt": prompt}
        )
        assert blocked is False
        assert msg == ""

    def test_escape_hatch_bypasses_mandatory_skill_check_too(self, monkeypatch):
        monkeypatch.setattr(agent_persona, "_resolve_agents_registry", lambda prompt: _FAKE_REGISTRY)
        prompt = "[GENERIC-OK] " + _compliant_prompt_for("hallucination-detector", ["hallucination-detection-core"])
        blocked, msg = agent_persona.check_agent_persona(
            "Agent", {"subagent_type": "general-purpose", "prompt": prompt}
        )
        assert blocked is False
        assert msg == ""

    def test_real_filesystem_lookup_with_no_env_var_or_path_line_fails_open(self):
        # No monkeypatch here -- exercises the real _resolve_agents_registry
        # against the compliant prompt fixture, which carries neither
        # GLOBAL_LIBRARY_PATH nor a WORKING DIRECTORY & LIBRARY PATH line.
        blocked, msg = agent_persona.check_agent_persona(
            "Agent", {"subagent_type": "general-purpose", "prompt": _COMPLIANT_PROMPT}
        )
        assert blocked is False
        assert msg == ""


class TestResolveAgentsRegistry:
    def test_resolves_via_env_var(self, tmp_path, monkeypatch):
        kg_dir = tmp_path / "knowledge-graph" / "_master"
        kg_dir.mkdir(parents=True)
        (kg_dir / "agents_all.json").write_text(
            '{"agents": [{"name": "foo-agent", "mandatory_skills": ["bar-core"]}]}',
            encoding="utf-8",
        )
        monkeypatch.setenv("GLOBAL_LIBRARY_PATH", str(tmp_path))
        agents = agent_persona._resolve_agents_registry("irrelevant prompt text")
        assert agents == [{"name": "foo-agent", "mandatory_skills": ["bar-core"]}]

    def test_resolves_via_working_directory_line(self, tmp_path, monkeypatch):
        monkeypatch.delenv("GLOBAL_LIBRARY_PATH", raising=False)
        kg_dir = tmp_path / "knowledge-graph" / "_master"
        kg_dir.mkdir(parents=True)
        (kg_dir / "agents_all.json").write_text(
            '{"agents": [{"name": "foo-agent", "mandatory_skills": ["bar-core"]}]}',
            encoding="utf-8",
        )
        prompt = "WORKING DIRECTORY & LIBRARY PATH: {0}. Read from here.\nTASK: x".format(str(tmp_path))
        agents = agent_persona._resolve_agents_registry(prompt)
        assert agents == [{"name": "foo-agent", "mandatory_skills": ["bar-core"]}]

    def test_returns_none_when_nothing_resolves(self, monkeypatch):
        monkeypatch.delenv("GLOBAL_LIBRARY_PATH", raising=False)
        agents = agent_persona._resolve_agents_registry("no path info here at all")
        assert agents is None

    def test_returns_none_on_malformed_registry_json(self, tmp_path, monkeypatch):
        monkeypatch.delenv("GLOBAL_LIBRARY_PATH", raising=False)
        kg_dir = tmp_path / "knowledge-graph" / "_master"
        kg_dir.mkdir(parents=True)
        (kg_dir / "agents_all.json").write_text("{not valid json", encoding="utf-8")
        prompt = "WORKING DIRECTORY & LIBRARY PATH: {0}. Read from here.\nTASK: x".format(str(tmp_path))
        agents = agent_persona._resolve_agents_registry(prompt)
        assert agents is None

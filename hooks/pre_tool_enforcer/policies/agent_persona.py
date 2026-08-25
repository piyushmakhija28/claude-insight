# pre_tool_enforcer/policies/agent_persona.py
# PreToolUse policy: block general-purpose subagent spawns lacking a library persona,
# and block persona spawns that name the agent but never actually carry its skills.
# Windows-safe: ASCII only, no Unicode characters.

import re

_GENERIC_TYPES = ("general-purpose", "claude", "")
_PERSONA_MARKER = "---persona---"
_ESCAPE_HATCH = "[GENERIC-OK]"

# Auto-exempt pattern: dispatches whose prompt targets writing a brand-new
# skills/{name}/SKILL.md or agents/{name}/agent.md file. There is never a
# persona to inject for these -- the file being authored IS the persona/skill,
# and it does not exist yet. This is the single most common recurring
# generic-dispatch case in this library's domain-creation workflow (7-Phase
# Protocol Phase 2 "Skill Creation" / Phase 5 "Agent Creation"), so it is
# auto-exempted permanently instead of requiring a manual [GENERIC-OK] marker
# on every call. Scoped narrowly to this one path shape so it cannot be used
# to silently bypass the persona requirement for unrelated generic work.
_SKILL_OR_AGENT_AUTHOR_PATTERN = re.compile(
    r"skills[/\\][a-z0-9][a-z0-9\-]*[/\\]SKILL\.md|agents[/\\][a-z0-9][a-z0-9\-]*[/\\]agent\.md",
    re.IGNORECASE,
)

# Persona block body: everything between '---persona---' and the next line
# that is just dashes (the template's closing '---'). MULTILINE + '^-{3,}$'
# tolerates the small whitespace variations real dispatch prompts have,
# rather than requiring the exact spacing shown in ORCHESTRATION_TEMPLATE.md.
_PERSONA_BLOCK_RE = re.compile(r"---persona---(.*?)^-{3,}\s*$", re.DOTALL | re.MULTILINE)

# 'skills:' field value, captured up to the next top-level 'key:' line (or
# end of block). Works for both inline ('skills: [a, b]') and YAML-list
# ('skills:\n  - a\n  - b') forms used across real dispatch prompts.
_SKILLS_FIELD_RE = re.compile(r"skills\s*:\s*(.*?)(?:\n[ \t]*[A-Za-z_][\w-]*\s*:|\Z)", re.DOTALL | re.IGNORECASE)

# A skill slug: lowercase, at least one hyphen (every real skill in this
# library is named like 'ai-agents-core' / 'system-design') -- this avoids
# matching stray single words or YAML punctuation inside the skills: value.
_SKILL_TOKEN_RE = re.compile(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)+")

_BLOCK_MSG_NO_PERSONA = (
    "[PRE-TOOL BLOCKED] Generic subagent spawned without a library persona!\n"
    "  Tool       : Agent/Task spawn with subagent_type=general-purpose (or unset)\n"
    "  Problem    : No agents/{name}/agent.md persona was injected into the prompt.\n"
    "  Required   : Route to a library agent, read its Skill Dependencies, then\n"
    "               inject its persona as a '---persona---' YAML block at the top\n"
    "               of the prompt (see ORCHESTRATION_TEMPLATE.md STEP 0.05,\n"
    "               Subagent Dispatch Contract).\n"
    "  Escape hatch: prefix the prompt/description with [GENERIC-OK] for a\n"
    "               genuinely generic one-off task with no matching persona,\n"
    "               OR a recurring task with no persona to inject because the\n"
    "               persona/skill IS what the task produces (e.g. authoring a\n"
    "               new SKILL.md / agent.md for a library that doesn't have\n"
    "               that persona yet).\n"
    "  Note       : Local code exploration should use the built-in 'Explore'\n"
    "               subagent_type instead -- it is not gated by this policy.\n"
    "  Action     : Add subagent_type of a named library agent, or inject the\n"
    "               '---persona---' block, or prefix with [GENERIC-OK]."
)

_BLOCK_MSG_HOLLOW_PERSONA = (
    "[PRE-TOOL BLOCKED] Persona injected but its skills were not actually carried!\n"
    "  Tool       : Agent/Task spawn with subagent_type=general-purpose (or unset)\n"
    "  Problem    : {detail}\n"
    "  Required   : Per ORCHESTRATION_TEMPLATE.md STEP 0.05, the persona block's\n"
    "               'skills:' field must list the agent's full skill set (mandatory\n"
    "               AGENT_USES_SKILL edges + OPTIONAL_SKILL edges), and the prompt\n"
    "               body must instruct the subagent to READ each one at its real\n"
    "               'skills/<name>/SKILL.md' path before doing anything else. A\n"
    "               persona name alone is a hollow dispatch -- the subagent never\n"
    "               receives the skill knowledge it is supposed to apply.\n"
    "  Escape hatch: prefix the prompt/description with [GENERIC-OK] only if this\n"
    "               agent genuinely has zero skill dependencies (rare -- check its\n"
    "               agent.md Skill Dependencies section first)."
)


def _extract_declared_skills(persona_block_text):
    """Return the deduped, lowercased skill slugs listed in a persona block's
    'skills:' field. Empty list if the field is missing, empty, or unparseable.
    """
    field_match = _SKILLS_FIELD_RE.search(persona_block_text)
    if not field_match:
        return []
    tokens = _SKILL_TOKEN_RE.findall(field_match.group(1))
    declared = []
    for token in tokens:
        lowered = token.lower()
        if lowered not in declared:
            declared.append(lowered)
    return declared


def _skill_read_path_present(prompt, skill):
    """True if the prompt instructs reading skill's real SKILL.md path."""
    pattern = re.compile(r"skills[/\\]" + re.escape(skill) + r"[/\\]SKILL\.md", re.IGNORECASE)
    return bool(pattern.search(prompt))


def check_agent_persona(tool_name, tool_input):
    """PreToolUse policy: block general-purpose subagent spawns lacking a
    real, skill-carrying persona.

    A general-purpose (or unset) subagent_type must carry a library agent
    persona injected as a '---persona---' YAML block at the top of its
    prompt, per the Subagent Dispatch Contract -- and that block must
    actually carry the agent's skills, not just its name. Two failure modes
    are gated:
      1. No '---persona---' block at all (the original check).
      2. A '---persona---' block present but hollow -- no 'skills:' field,
         an empty one, or skills declared with no matching
         'skills/<name>/SKILL.md' read instruction in the prompt body. A
         persona shell without its skill knowledge defeats the whole point
         of persona injection: the subagent never actually reads the
         domain skill it is supposed to apply.

    Named built-in subagent types (e.g. Explore, Plan) are never gated. An
    explicit '[GENERIC-OK]' marker in the prompt/description is an escape
    hatch for genuinely generic one-off tasks, or for the rare agent with
    zero real skill dependencies. Dispatches that target writing a new
    skills/{name}/SKILL.md or agents/{name}/agent.md file are auto-exempt
    permanently (no marker needed) via _SKILL_OR_AGENT_AUTHOR_PATTERN,
    since there is never a persona to inject there -- the file being
    authored IS the persona/skill and does not exist yet.

    Args:
        tool_name (str): Name of the tool (must be 'Agent' or 'Task' to trigger).
        tool_input (dict): Tool parameters dict with 'subagent_type' and
            'prompt' (or 'description') keys. Any non-dict value (None,
            malformed payload) is treated as fail-open, never as a block.

    Returns:
        tuple: (blocked: bool, message: str)
    """
    if tool_name not in ("Agent", "Task"):
        return False, ""

    if not isinstance(tool_input, dict):
        return False, ""

    subagent_type = str(tool_input.get("subagent_type") or "").strip().lower()
    if subagent_type not in _GENERIC_TYPES:
        return False, ""

    prompt = str(tool_input.get("prompt") or tool_input.get("description") or "")

    if _ESCAPE_HATCH in prompt:
        return False, ""

    if _PERSONA_MARKER not in prompt:
        # The skill/agent-authoring exemption only applies to prompts with no
        # persona block: its premise is "the target agent.md/SKILL.md doesn't
        # exist yet, so there is nothing to inject". Once a '---persona---'
        # block is present, that premise no longer holds -- the dispatch IS a
        # routed persona call, and a 'skills/<name>/SKILL.md' substring inside
        # it is far more likely to be a legitimate READ instruction than an
        # authoring target, so it must go through full hollow-persona
        # validation below rather than short-circuit past it.
        if _SKILL_OR_AGENT_AUTHOR_PATTERN.search(prompt):
            return False, ""
        return True, _BLOCK_MSG_NO_PERSONA

    block_match = _PERSONA_BLOCK_RE.search(prompt)
    if not block_match:
        return True, _BLOCK_MSG_HOLLOW_PERSONA.format(
            detail="'---persona---' marker found but the block never closes with "
            "a matching '---' line, so no skills: field could be parsed."
        )

    declared_skills = _extract_declared_skills(block_match.group(1))
    if not declared_skills:
        return True, _BLOCK_MSG_HOLLOW_PERSONA.format(
            detail="the persona block has no 'skills:' field (or it is empty) -- "
            "no skill knowledge is being injected into the subagent."
        )

    missing = [s for s in declared_skills if not _skill_read_path_present(prompt, s)]
    if missing:
        return True, _BLOCK_MSG_HOLLOW_PERSONA.format(
            detail="skills declared in the persona block have no matching "
            "'skills/<name>/SKILL.md' read instruction in the prompt: " + ", ".join(missing)
        )

    return False, ""

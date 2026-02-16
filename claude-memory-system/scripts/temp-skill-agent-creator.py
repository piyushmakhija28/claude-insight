#!/usr/bin/env python3
"""
Temporary Skill/Agent Creator
Creates temporary skills and agents for specialized tasks
"""

import json
import sys
from datetime import datetime
from pathlib import Path


def load_temp_registry():
    """Load temporary skills/agents registry."""
    registry_file = Path.home() / ".claude/memory/temp/temp-skills-registry.json"

    if registry_file.exists():
        with open(registry_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    # Initialize empty registry
    return {
        "temporary_skills": {},
        "temporary_agents": {}
    }


def save_temp_registry(registry):
    """Save temporary skills/agents registry."""
    registry_file = Path.home() / ".claude/memory/temp/temp-skills-registry.json"
    registry_file.parent.mkdir(parents=True, exist_ok=True)

    with open(registry_file, 'w', encoding='utf-8') as f:
        json.dump(registry, f, indent=2)


def register_temp_skill(name, skill_def):
    """Register temporary skill in registry."""
    registry = load_temp_registry()

    registry["temporary_skills"][name] = skill_def

    save_temp_registry(registry)


def register_temp_agent(name, agent_def):
    """Register temporary agent in registry."""
    registry = load_temp_registry()

    registry["temporary_agents"][name] = agent_def

    save_temp_registry(registry)


def generate_skill_markdown(skill_def):
    """Generate skill.md content from definition."""

    content = f"""# {skill_def['name']}

**Type:** Temporary Skill (Auto-Generated)
**Created:** {skill_def['created']}
**Status:** Active

## Description

{skill_def['description']}

## Capabilities

"""

    for capability in skill_def.get('capabilities', []):
        content += f"- {capability}\n"

    content += """

## Usage

This is a temporary skill created for specialized task execution.
It will be automatically evaluated for retention or deletion based on usage patterns.

## Metadata

- **Temporary:** Yes
- **Created:** {created}
- **Usage Count:** {usage_count}
- **Last Used:** {last_used}

---

**NOTE:** This skill is temporary and may be deleted if not actively used.
""".format(
        created=skill_def['created'],
        usage_count=skill_def.get('usage_count', 0),
        last_used=skill_def.get('last_used', 'Never')
    )

    return content


def create_temporary_skill(name, description, capabilities):
    """
    Create a temporary skill for specialized task.

    Args:
        name: Skill name (e.g., "graphql-migration-expert")
        description: What the skill does
        capabilities: List of capabilities

    Returns:
        skill_path: Path to created skill
    """

    # Generate skill definition
    skill_def = {
        "name": name,
        "description": description,
        "capabilities": capabilities,
        "temporary": True,
        "created": datetime.now().isoformat(),
        "usage_count": 0,
        "last_used": None,
        "user_marked_useful": False
    }

    # Create skill directory
    skill_dir = Path.home() / f".claude/skills/temp/{name}"
    skill_dir.mkdir(parents=True, exist_ok=True)

    # Write skill.md
    skill_file = skill_dir / "skill.md"
    with open(skill_file, 'w', encoding='utf-8') as f:
        f.write(generate_skill_markdown(skill_def))

    # Register in temp registry
    register_temp_skill(name, skill_def)

    print(f"✅ Created temporary skill: {name}")
    print(f"📁 Location: {skill_dir}")
    print(f"📄 File: {skill_file}")

    return str(skill_dir)


def create_temporary_agent(name, description, tools):
    """
    Create a temporary agent for specialized execution.

    Args:
        name: Agent name (e.g., "legacy-api-migrator")
        description: What the agent does
        tools: List of tools the agent can use

    Returns:
        agent_config: Agent configuration
    """

    # Generate agent definition
    agent_def = {
        "name": name,
        "description": description,
        "tools": tools,
        "temporary": True,
        "created": datetime.now().isoformat(),
        "usage_count": 0,
        "last_used": None,
        "user_marked_useful": False
    }

    # Register in temp registry
    register_temp_agent(name, agent_def)

    print(f"✅ Created temporary agent: {name}")
    print(f"🛠️ Tools: {', '.join(tools)}")

    return agent_def


def list_temp_resources():
    """List all temporary skills and agents."""
    registry = load_temp_registry()

    print()
    print("=" * 80)
    print("📋 TEMPORARY RESOURCES")
    print("=" * 80)
    print()

    # List skills
    skills = registry.get("temporary_skills", {})
    if skills:
        print(f"🔧 Temporary Skills ({len(skills)}):")
        print()

        for name, skill_def in skills.items():
            usage = skill_def.get('usage_count', 0)
            created = skill_def.get('created', 'Unknown')
            last_used = skill_def.get('last_used', 'Never')

            print(f"  • {name}")
            print(f"    Created: {created}")
            print(f"    Usage: {usage} times")
            print(f"    Last Used: {last_used}")
            print()
    else:
        print("🔧 Temporary Skills: None")
        print()

    # List agents
    agents = registry.get("temporary_agents", {})
    if agents:
        print(f"🤖 Temporary Agents ({len(agents)}):")
        print()

        for name, agent_def in agents.items():
            usage = agent_def.get('usage_count', 0)
            created = agent_def.get('created', 'Unknown')
            last_used = agent_def.get('last_used', 'Never')

            print(f"  • {name}")
            print(f"    Created: {created}")
            print(f"    Usage: {usage} times")
            print(f"    Last Used: {last_used}")
            print()
    else:
        print("🤖 Temporary Agents: None")
        print()

    print("=" * 80)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Manage temporary skills and agents")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Create skill
    skill_parser = subparsers.add_parser("create-skill", help="Create temporary skill")
    skill_parser.add_argument("--name", required=True, help="Skill name")
    skill_parser.add_argument("--description", required=True, help="Skill description")
    skill_parser.add_argument("--capabilities", nargs='+', required=True, help="Skill capabilities")

    # Create agent
    agent_parser = subparsers.add_parser("create-agent", help="Create temporary agent")
    agent_parser.add_argument("--name", required=True, help="Agent name")
    agent_parser.add_argument("--description", required=True, help="Agent description")
    agent_parser.add_argument("--tools", nargs='+', required=True, help="Agent tools")

    # List resources
    list_parser = subparsers.add_parser("list", help="List temporary resources")

    args = parser.parse_args()

    if args.command == "create-skill":
        create_temporary_skill(args.name, args.description, args.capabilities)

    elif args.command == "create-agent":
        create_temporary_agent(args.name, args.description, args.tools)

    elif args.command == "list":
        list_temp_resources()

    else:
        parser.print_help()
        sys.exit(1)

#!/usr/bin/env python3
"""
Temporary Resource Manager
Manages lifecycle of temporary skills and agents
"""

import json
import sys
import shutil
from datetime import datetime, timedelta
from pathlib import Path


def load_temp_registry():
    """Load temporary skills/agents registry."""
    registry_file = Path.home() / ".claude/memory/temp/temp-skills-registry.json"

    if registry_file.exists():
        with open(registry_file, 'r', encoding='utf-8') as f:
            return json.load(f)

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


def skill_exists(name):
    """Check if skill exists (permanent or temporary)."""
    # Check permanent skills
    perm_skill_dir = Path.home() / f".claude/skills/{name}"
    if perm_skill_dir.exists():
        return True

    # Check temporary skills
    temp_skill_dir = Path.home() / f".claude/skills/temp/{name}"
    return temp_skill_dir.exists()


def is_redundant_with_existing(resource_name, resource_type):
    """Check if temporary resource is redundant with existing permanent resources."""

    if resource_type == "skill":
        # Check if similar permanent skill exists
        # This is a simplified check - in production, would use semantic similarity
        registry = load_temp_registry()
        temp_resource = registry.get("temporary_skills", {}).get(resource_name, {})

        # Extract keywords from name
        keywords = resource_name.lower().replace('-', ' ').split()

        # Check permanent skills directory
        skills_dir = Path.home() / ".claude/skills"
        if skills_dir.exists():
            for skill_path in skills_dir.iterdir():
                if skill_path.is_dir() and skill_path.name != "temp":
                    skill_name = skill_path.name.lower()

                    # Check for keyword overlap
                    if any(keyword in skill_name for keyword in keywords):
                        return True

    return False


def decide_keep_or_delete(resource_name, resource_type):
    """
    Decide whether to keep or delete a temporary resource.

    Decision Criteria:
        KEEP if:
        - Used 3+ times
        - Used in last 7 days
        - Marked as useful by user
        - Solves common problem

        DELETE if:
        - One-time use only
        - Not used in 30+ days
        - Redundant with existing skill/agent
        - Task completed and no future need

    Returns:
        (decision: str, reason: str)
    """

    registry = load_temp_registry()

    if resource_type == "skill":
        resource = registry.get("temporary_skills", {}).get(resource_name)
    elif resource_type == "agent":
        resource = registry.get("temporary_agents", {}).get(resource_name)
    else:
        return "delete", "Unknown resource type"

    if not resource:
        return "delete", "Resource not found"

    # Check usage
    usage_count = resource.get("usage_count", 0)
    last_used = resource.get("last_used")

    if last_used:
        last_used_dt = datetime.fromisoformat(last_used)
        days_since_last_use = (datetime.now() - last_used_dt).days
    else:
        days_since_last_use = 999  # Never used

    # Decision logic
    if usage_count >= 3:
        return "keep", f"Used {usage_count} times - shows value"

    if last_used and days_since_last_use <= 7:
        return "keep", "Recently used - might be needed again"

    if resource.get("user_marked_useful"):
        return "keep", "User marked as useful"

    if days_since_last_use >= 30:
        return "delete", f"Not used in {days_since_last_use} days"

    if usage_count == 1 and days_since_last_use >= 7:
        return "delete", "One-time use, no recent activity"

    # Check for redundancy
    if is_redundant_with_existing(resource_name, resource_type):
        return "delete", "Redundant with existing skill/agent"

    # Default: keep for now (pending further usage data)
    return "keep", "Pending further usage data"


def delete_temp_skill(skill_name):
    """Delete temporary skill."""
    # Delete skill directory
    skill_dir = Path.home() / f".claude/skills/temp/{skill_name}"
    if skill_dir.exists():
        shutil.rmtree(skill_dir)

    # Remove from registry
    registry = load_temp_registry()
    if skill_name in registry.get("temporary_skills", {}):
        del registry["temporary_skills"][skill_name]
        save_temp_registry(registry)


def delete_temp_agent(agent_name):
    """Delete temporary agent."""
    # Remove from registry
    registry = load_temp_registry()
    if agent_name in registry.get("temporary_agents", {}):
        del registry["temporary_agents"][agent_name]
        save_temp_registry(registry)


def promote_temp_skill_to_permanent(skill_name):
    """Promote temporary skill to permanent."""
    temp_skill_dir = Path.home() / f".claude/skills/temp/{skill_name}"
    perm_skill_dir = Path.home() / f".claude/skills/{skill_name}"

    if temp_skill_dir.exists():
        # Move directory
        shutil.move(str(temp_skill_dir), str(perm_skill_dir))

        # Update registry
        registry = load_temp_registry()
        if skill_name in registry.get("temporary_skills", {}):
            del registry["temporary_skills"][skill_name]
            save_temp_registry(registry)

        print(f"✅ Promoted {skill_name} to permanent skill")


def cleanup_temp_resources(dry_run=False):
    """
    Cleanup temporary resources based on keep/delete decisions.

    Args:
        dry_run: If True, only show what would be deleted without actually deleting

    Returns:
        (deleted_count: int, kept_count: int, promoted_count: int)
    """

    registry = load_temp_registry()

    deleted_count = 0
    kept_count = 0
    promoted_count = 0

    print()
    print("=" * 80)
    print("🗑️ TEMPORARY RESOURCE CLEANUP")
    print("=" * 80)
    print()

    if dry_run:
        print("⚠️ DRY RUN MODE - No actual deletions will occur")
        print()

    # Check temporary skills
    skills = registry.get("temporary_skills", {})
    if skills:
        print(f"🔧 Checking {len(skills)} temporary skill(s)...")
        print()

        for skill_name in list(skills.keys()):
            decision, reason = decide_keep_or_delete(skill_name, "skill")

            if decision == "delete":
                print(f"  🗑️ DELETE: {skill_name}")
                print(f"     Reason: {reason}")

                if not dry_run:
                    delete_temp_skill(skill_name)

                deleted_count += 1

            elif decision == "promote":
                print(f"  ⬆️ PROMOTE: {skill_name}")
                print(f"     Reason: {reason}")

                if not dry_run:
                    promote_temp_skill_to_permanent(skill_name)

                promoted_count += 1

            else:  # keep
                print(f"  ✅ KEEP: {skill_name}")
                print(f"     Reason: {reason}")

                kept_count += 1

        print()

    # Check temporary agents
    agents = registry.get("temporary_agents", {})
    if agents:
        print(f"🤖 Checking {len(agents)} temporary agent(s)...")
        print()

        for agent_name in list(agents.keys()):
            decision, reason = decide_keep_or_delete(agent_name, "agent")

            if decision == "delete":
                print(f"  🗑️ DELETE: {agent_name}")
                print(f"     Reason: {reason}")

                if not dry_run:
                    delete_temp_agent(agent_name)

                deleted_count += 1

            else:  # keep
                print(f"  ✅ KEEP: {agent_name}")
                print(f"     Reason: {reason}")

                kept_count += 1

        print()

    print("=" * 80)
    print(f"📊 CLEANUP SUMMARY:")
    print(f"   Deleted:  {deleted_count}")
    print(f"   Kept:     {kept_count}")
    print(f"   Promoted: {promoted_count}")
    print("=" * 80)
    print()

    return deleted_count, kept_count, promoted_count


def mark_resource_used(resource_name, resource_type):
    """Mark a resource as used (update usage count and last_used timestamp)."""
    registry = load_temp_registry()

    if resource_type == "skill":
        if resource_name in registry.get("temporary_skills", {}):
            resource = registry["temporary_skills"][resource_name]
            resource["usage_count"] = resource.get("usage_count", 0) + 1
            resource["last_used"] = datetime.now().isoformat()

    elif resource_type == "agent":
        if resource_name in registry.get("temporary_agents", {}):
            resource = registry["temporary_agents"][resource_name]
            resource["usage_count"] = resource.get("usage_count", 0) + 1
            resource["last_used"] = datetime.now().isoformat()

    save_temp_registry(registry)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Manage temporary resources")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Cleanup command
    cleanup_parser = subparsers.add_parser("cleanup", help="Cleanup temporary resources")
    cleanup_parser.add_argument("--dry-run", action="store_true", help="Show what would be deleted without actually deleting")

    # Mark used command
    mark_parser = subparsers.add_parser("mark-used", help="Mark resource as used")
    mark_parser.add_argument("--name", required=True, help="Resource name")
    mark_parser.add_argument("--type", required=True, choices=["skill", "agent"], help="Resource type")

    # Promote command
    promote_parser = subparsers.add_parser("promote", help="Promote temporary skill to permanent")
    promote_parser.add_argument("--name", required=True, help="Skill name")

    args = parser.parse_args()

    if args.command == "cleanup":
        cleanup_temp_resources(dry_run=args.dry_run)

    elif args.command == "mark-used":
        mark_resource_used(args.name, args.type)
        print(f"✅ Marked {args.type} '{args.name}' as used")

    elif args.command == "promote":
        promote_temp_skill_to_permanent(args.name)

    else:
        parser.print_help()
        sys.exit(1)

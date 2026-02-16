#!/usr/bin/env python3
"""
Skill Manager - CRUD operations for skill registry
Part of Claude Memory System

Usage:
  python skill-manager.py add --id "my-skill" --name "My Skill" --file "~/.claude/skills/my-skill.md"
  python skill-manager.py update --id "my-skill" --keywords "python,api,rest"
  python skill-manager.py remove --id "my-skill"
  python skill-manager.py stats
"""

import json
import sys
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# Paths
MEMORY_DIR = Path.home() / '.claude' / 'memory'
SKILLS_REGISTRY = MEMORY_DIR / 'skills-registry.json'
SKILL_MANAGER_LOG = MEMORY_DIR / 'logs' / 'skill-manager.log'


class SkillManager:
    def __init__(self):
        self.registry = self._load_registry()
        self.skills = self.registry.get('skills', {})
        self.categories = self.registry.get('categories', {})
        self.statistics = self.registry.get('statistics', {})

    def _load_registry(self) -> Dict:
        """Load skills registry from JSON"""
        if not SKILLS_REGISTRY.exists():
            return {
                "version": "1.0.0",
                "last_updated": datetime.now().strftime('%Y-%m-%d'),
                "skills": {},
                "categories": {},
                "statistics": {
                    "total_skills": 0,
                    "by_language": {},
                    "by_category": {}
                }
            }

        with open(SKILLS_REGISTRY, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _save_registry(self):
        """Save updated registry back to JSON"""
        self.registry['last_updated'] = datetime.now().strftime('%Y-%m-%d')
        self.registry['skills'] = self.skills
        self.registry['categories'] = self.categories
        self.registry['statistics'] = self.statistics

        with open(SKILLS_REGISTRY, 'w', encoding='utf-8') as f:
            json.dump(self.registry, f, indent=2, ensure_ascii=False)

        self._log_event("registry-saved")

    def add_skill(self, skill_id: str, **kwargs) -> bool:
        """
        Add a new skill to the registry

        Required kwargs:
        - name: str
        - file: str
        - description: str
        - language: str
        - category: str
        - keywords: List[str]
        """
        if skill_id in self.skills:
            print(f"Error: Skill '{skill_id}' already exists")
            return False

        # Required fields
        required = ['name', 'file', 'description', 'language', 'category', 'keywords']
        for field in required:
            if field not in kwargs:
                print(f"Error: Missing required field '{field}'")
                return False

        # Create skill entry
        self.skills[skill_id] = {
            'name': kwargs['name'],
            'file': kwargs['file'],
            'description': kwargs['description'],
            'version': kwargs.get('version', '1.0.0'),
            'size': kwargs.get('size', 'N/A'),
            'language': kwargs['language'],
            'category': kwargs['category'],
            'keywords': kwargs['keywords'] if isinstance(kwargs['keywords'], list) else kwargs['keywords'].split(','),
            'trigger_patterns': kwargs.get('trigger_patterns', []),
            'auto_suggest': kwargs.get('auto_suggest', True),
            'requires_context7': kwargs.get('requires_context7', False),
            'dependencies': kwargs.get('dependencies', []),
            'usage_count': 0,
            'last_used': None,
            'tags': kwargs.get('tags', [])
        }

        # Update category
        category = kwargs['category']
        if category not in self.categories:
            self.categories[category] = {
                'description': kwargs.get('category_description', f'{category} skills'),
                'skills': []
            }
        self.categories[category]['skills'].append(skill_id)

        # Update statistics
        self._update_statistics()

        self._save_registry()
        self._log_event(f"skill-added | {skill_id}")

        print(f"✓ Skill '{skill_id}' added successfully")
        return True

    def update_skill(self, skill_id: str, **kwargs) -> bool:
        """Update an existing skill"""
        if skill_id not in self.skills:
            print(f"Error: Skill '{skill_id}' not found")
            return False

        # Update allowed fields
        updatable = ['name', 'description', 'keywords', 'trigger_patterns',
                     'auto_suggest', 'requires_context7', 'tags', 'version', 'size']

        for field, value in kwargs.items():
            if field in updatable:
                if field == 'keywords' and isinstance(value, str):
                    value = value.split(',')
                self.skills[skill_id][field] = value

        self._save_registry()
        self._log_event(f"skill-updated | {skill_id}")

        print(f"✓ Skill '{skill_id}' updated successfully")
        return True

    def remove_skill(self, skill_id: str) -> bool:
        """Remove a skill from the registry"""
        if skill_id not in self.skills:
            print(f"Error: Skill '{skill_id}' not found")
            return False

        # Remove from category
        skill_data = self.skills[skill_id]
        category = skill_data.get('category')
        if category and category in self.categories:
            self.categories[category]['skills'] = [
                s for s in self.categories[category]['skills'] if s != skill_id
            ]

        # Remove skill
        del self.skills[skill_id]

        # Update statistics
        self._update_statistics()

        self._save_registry()
        self._log_event(f"skill-removed | {skill_id}")

        print(f"✓ Skill '{skill_id}' removed successfully")
        return True

    def get_skill(self, skill_id: str) -> Optional[Dict]:
        """Get skill details"""
        return self.skills.get(skill_id)

    def list_skills(self, category: Optional[str] = None) -> List[str]:
        """List all skills or by category"""
        if category:
            return self.categories.get(category, {}).get('skills', [])
        return list(self.skills.keys())

    def _update_statistics(self):
        """Update registry statistics"""
        self.statistics['total_skills'] = len(self.skills)

        # By language
        by_language = {}
        for skill_data in self.skills.values():
            lang = skill_data.get('language', 'unknown')
            by_language[lang] = by_language.get(lang, 0) + 1
        self.statistics['by_language'] = by_language

        # By category
        by_category = {}
        for skill_data in self.skills.values():
            cat = skill_data.get('category', 'unknown')
            by_category[cat] = by_category.get(cat, 0) + 1
        self.statistics['by_category'] = by_category

        # Most/least used
        usage_counts = {sid: data.get('usage_count', 0) for sid, data in self.skills.items()}
        if usage_counts:
            self.statistics['most_used'] = max(usage_counts, key=usage_counts.get)
            self.statistics['least_used'] = min(usage_counts, key=usage_counts.get)

    def show_statistics(self):
        """Display registry statistics"""
        print("=== Skill Registry Statistics ===\n")

        print(f"Total Skills: {self.statistics.get('total_skills', 0)}")
        print(f"Version: {self.registry.get('version', 'N/A')}")
        print(f"Last Updated: {self.registry.get('last_updated', 'N/A')}\n")

        print("By Language:")
        for lang, count in self.statistics.get('by_language', {}).items():
            print(f"  {lang}: {count}")

        print("\nBy Category:")
        for cat, count in self.statistics.get('by_category', {}).items():
            print(f"  {cat}: {count}")

        if self.statistics.get('most_used'):
            most_used_id = self.statistics['most_used']
            most_used = self.skills[most_used_id]
            print(f"\nMost Used: {most_used['name']} ({most_used.get('usage_count', 0)} times)")

        print()

    def export_skill(self, skill_id: str, output_file: str) -> bool:
        """Export a single skill to JSON"""
        if skill_id not in self.skills:
            print(f"Error: Skill '{skill_id}' not found")
            return False

        export_data = {
            'skill_id': skill_id,
            'data': self.skills[skill_id]
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

        print(f"✓ Skill exported to: {output_file}")
        return True

    def import_skill(self, import_file: str) -> bool:
        """Import a skill from JSON"""
        try:
            with open(import_file, 'r', encoding='utf-8') as f:
                import_data = json.load(f)

            skill_id = import_data.get('skill_id')
            skill_data = import_data.get('data')

            if not skill_id or not skill_data:
                print("Error: Invalid import file format")
                return False

            if skill_id in self.skills:
                print(f"Warning: Skill '{skill_id}' already exists. Updating...")

            self.skills[skill_id] = skill_data
            self._update_statistics()
            self._save_registry()

            print(f"✓ Skill '{skill_id}' imported successfully")
            return True

        except Exception as e:
            print(f"Error importing skill: {e}")
            return False

    def _log_event(self, message: str):
        """Log skill manager events"""
        SKILL_MANAGER_LOG.parent.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] {message}\n"

        with open(SKILL_MANAGER_LOG, 'a', encoding='utf-8') as f:
            f.write(log_entry)


def main():
    """CLI interface for skill manager"""
    parser = argparse.ArgumentParser(description='Manage Claude skills registry')
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Add skill
    add_parser = subparsers.add_parser('add', help='Add a new skill')
    add_parser.add_argument('--id', required=True, help='Skill ID')
    add_parser.add_argument('--name', required=True, help='Skill name')
    add_parser.add_argument('--file', required=True, help='Skill file path')
    add_parser.add_argument('--description', required=True, help='Description')
    add_parser.add_argument('--language', required=True, help='Programming language')
    add_parser.add_argument('--category', required=True, help='Skill category')
    add_parser.add_argument('--keywords', required=True, help='Comma-separated keywords')
    add_parser.add_argument('--version', default='1.0.0', help='Version')
    add_parser.add_argument('--size', help='File size')
    add_parser.add_argument('--context7', action='store_true', help='Requires Context7')

    # Update skill
    update_parser = subparsers.add_parser('update', help='Update a skill')
    update_parser.add_argument('--id', required=True, help='Skill ID')
    update_parser.add_argument('--name', help='New name')
    update_parser.add_argument('--description', help='New description')
    update_parser.add_argument('--keywords', help='New keywords (comma-separated)')
    update_parser.add_argument('--version', help='New version')

    # Remove skill
    remove_parser = subparsers.add_parser('remove', help='Remove a skill')
    remove_parser.add_argument('--id', required=True, help='Skill ID to remove')

    # List skills
    subparsers.add_parser('list', help='List all skills')

    # Show stats
    subparsers.add_parser('stats', help='Show registry statistics')

    # Export skill
    export_parser = subparsers.add_parser('export', help='Export a skill')
    export_parser.add_argument('--id', required=True, help='Skill ID')
    export_parser.add_argument('--output', required=True, help='Output file')

    # Import skill
    import_parser = subparsers.add_parser('import', help='Import a skill')
    import_parser.add_argument('--file', required=True, help='Import file')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    manager = SkillManager()

    if args.command == 'add':
        manager.add_skill(
            args.id,
            name=args.name,
            file=args.file,
            description=args.description,
            language=args.language,
            category=args.category,
            keywords=args.keywords,
            version=args.version,
            size=args.size,
            requires_context7=args.context7
        )

    elif args.command == 'update':
        kwargs = {}
        if args.name: kwargs['name'] = args.name
        if args.description: kwargs['description'] = args.description
        if args.keywords: kwargs['keywords'] = args.keywords
        if args.version: kwargs['version'] = args.version

        manager.update_skill(args.id, **kwargs)

    elif args.command == 'remove':
        manager.remove_skill(args.id)

    elif args.command == 'list':
        skills = manager.list_skills()
        print("=== All Skills ===")
        for skill_id in skills:
            skill_data = manager.get_skill(skill_id)
            print(f"• {skill_id}: {skill_data['name']}")

    elif args.command == 'stats':
        manager.show_statistics()

    elif args.command == 'export':
        manager.export_skill(args.id, args.output)

    elif args.command == 'import':
        manager.import_skill(args.file)


if __name__ == '__main__':
    main()

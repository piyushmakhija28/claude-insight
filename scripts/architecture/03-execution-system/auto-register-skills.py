#!/usr/bin/env python3
"""
Auto-Register Skills - Discover and register all skills from ~/.claude/skills/
Part of Claude Memory System

Automatically scans skills folder and registers any new/unregistered skills.
Integrates with adaptive skill intelligence for dynamically created skills.

Usage:
  python auto-register-skills.py                # Auto-discover and register all
  python auto-register-skills.py --dry-run      # Show what would be registered
  python auto-register-skills.py --force        # Re-register all (update existing)
"""

import json
import sys
import re
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Paths
CLAUDE_DIR = Path.home() / '.claude'
SKILLS_DIR = CLAUDE_DIR / 'skills'
MEMORY_DIR = CLAUDE_DIR / 'memory'
SKILLS_REGISTRY = MEMORY_DIR / 'skills-registry.json'
AUTO_REGISTER_LOG = MEMORY_DIR / 'logs' / 'auto-register.log'


class SkillAutoRegister:
    def __init__(self):
        self.registry = self._load_registry()
        self.skills = self.registry.get('skills', {})
        self.registered_count = 0
        self.updated_count = 0
        self.skipped_count = 0

        # Manual keyword enhancements for specific skills
        self.keyword_overrides = {
            'payment-integration-python': {
                'add_keywords': ['stripe', 'razorpay', 'paypal', 'square', 'braintree', 'gateway', 'checkout', 'refund', 'subscription'],
                'add_triggers': ['payment.*python', 'stripe.*flask', 'razorpay.*django', 'paypal.*python']
            },
            'payment-integration-java': {
                'add_keywords': ['stripe', 'razorpay', 'paypal', 'square', 'braintree', 'gateway', 'checkout', 'refund', 'subscription'],
                'add_triggers': ['payment.*java', 'payment.*spring', 'stripe.*spring', 'razorpay.*spring', 'razorpay.*java', 'paypal.*spring']
            },
            'payment-integration-typescript': {
                'add_keywords': ['stripe', 'razorpay', 'paypal', 'square', 'braintree', 'gateway', 'checkout', 'refund', 'subscription'],
                'add_triggers': ['payment.*typescript', 'stripe.*express', 'razorpay.*nestjs', 'paypal.*node']
            },
            'adaptive-skill-intelligence': {
                'add_keywords': ['skill', 'agent', 'factory', 'create', 'dynamic', 'auto', 'generate', 'adaptive'],
                'add_triggers': ['adaptive.*skill', 'auto.*create.*skill', 'dynamic.*agent']
            },
            'memory-enforcer': {
                'add_keywords': ['memory', 'enforcer', 'enforcement', 'policy', 'system', 'mandate', 'rules'],
                'add_triggers': ['memory.*enforcement', 'memory.*system', 'policy.*enforcement']
            },
            'phased-execution-intelligence': {
                'add_keywords': ['phased', 'execution', 'phase', 'milestone', 'checkpoint', 'breakdown', 'stages', 'progressive'],
                'add_triggers': ['phased.*execution', 'phase.*breakdown', 'milestone.*execution']
            },
            'task-planning-intelligence': {
                'add_keywords': ['task', 'planning', 'plan', 'breakdown', 'complexity', 'analysis', 'strategy', 'organize'],
                'add_triggers': ['task.*planning', 'task.*breakdown', 'plan.*complexity']
            }
        }

    def _load_registry(self) -> Dict:
        """Load existing registry"""
        if not SKILLS_REGISTRY.exists():
            return {
                "version": "1.0.0",
                "last_updated": datetime.now().strftime('%Y-%m-%d'),
                "skills": {},
                "categories": {},
                "statistics": {"total_skills": 0}
            }

        with open(SKILLS_REGISTRY, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _save_registry(self):
        """Save updated registry"""
        self.registry['last_updated'] = datetime.now().strftime('%Y-%m-%d')
        self.registry['skills'] = self.skills
        self._update_statistics()

        with open(SKILLS_REGISTRY, 'w', encoding='utf-8') as f:
            json.dump(self.registry, f, indent=2, ensure_ascii=False)

    def _update_statistics(self):
        """Update registry statistics"""
        stats = self.registry.get('statistics', {})
        stats['total_skills'] = len(self.skills)

        # By language
        by_language = {}
        for skill_data in self.skills.values():
            lang = skill_data.get('language', 'unknown')
            by_language[lang] = by_language.get(lang, 0) + 1
        stats['by_language'] = by_language

        # By category
        by_category = {}
        for skill_data in self.skills.values():
            cat = skill_data.get('category', 'unknown')
            by_category[cat] = by_category.get(cat, 0) + 1
        stats['by_category'] = by_category

        self.registry['statistics'] = stats

        # Update categories
        categories = {}
        for skill_id, skill_data in self.skills.items():
            cat = skill_data.get('category', 'unknown')
            if cat not in categories:
                categories[cat] = {'skills': [], 'description': f'{cat} skills'}
            categories[cat]['skills'].append(skill_id)
        self.registry['categories'] = categories

    def _parse_frontmatter(self, content: str) -> Optional[Dict]:
        """Parse YAML frontmatter from markdown file"""
        if not content.startswith('---'):
            return None

        try:
            # Find frontmatter boundaries
            parts = content.split('---', 2)
            if len(parts) < 3:
                return None

            frontmatter_text = parts[1].strip()

            # Simple YAML parser (key: value format)
            frontmatter = {}
            for line in frontmatter_text.split('\n'):
                line = line.strip()
                if ':' in line:
                    key, value = line.split(':', 1)
                    frontmatter[key.strip()] = value.strip()

            return frontmatter if frontmatter else None

        except Exception:
            return None

    def _metadata_from_frontmatter(self, file_path: Path, frontmatter: Dict, content: str, total_lines: int) -> Dict:
        """Create metadata from frontmatter"""
        # Get name from frontmatter or filename
        name = frontmatter.get('name', file_path.stem.replace('-', ' ').title())

        # Get description from frontmatter
        description = frontmatter.get('description', '')
        if not description:
            # Fall back to first paragraph after frontmatter
            parts = content.split('---', 2)
            if len(parts) >= 3:
                body = parts[2].strip()
                for line in body.split('\n'):
                    if line.strip() and not line.startswith('#'):
                        description = line.strip()
                        break

        # Extract individual words from name (primary keywords)
        name_words = [w for w in name.lower().replace('-', ' ').split() if len(w) >= 3]

        # Extract keywords from description
        desc_keywords = self._extract_keywords_from_text(description)

        # Prioritize: name words first, then description keywords
        keywords = []

        # Add name words first (these are the primary identifiers)
        for word in name_words:
            if word not in ['core', 'skill', 'agent']:  # Skip generic words
                keywords.append(word)

        # Add description keywords (avoiding duplicates)
        for keyword in desc_keywords:
            if keyword not in keywords:
                keywords.append(keyword)

        keywords = keywords[:15]  # Limit to 15

        # Detect language
        language = self._detect_language(file_path, content)

        # Detect category
        category = self._detect_category(file_path, content)

        # Generate trigger patterns from description keywords
        trigger_patterns = self._generate_triggers_from_keywords(keywords, language)

        # Check if requires Context7
        requires_context7 = 'context7' in content.lower() or 'latest' in content.lower()

        # Apply manual keyword enhancements if available
        skill_id = file_path.parent.name.lower() if file_path.stem.upper() in ['SKILL', 'INSTRUCTIONS'] else file_path.stem.lower()
        keywords, trigger_patterns = self._apply_keyword_overrides(skill_id, keywords, trigger_patterns)

        return {
            'name': name.title(),
            'file': str(file_path).replace('\\', '/'),
            'description': description[:200],
            'version': '1.0.0',
            'size': f'{total_lines} lines',
            'language': language,
            'category': category,
            'keywords': keywords[:20],  # Increased to 20 to accommodate overrides
            'trigger_patterns': trigger_patterns[:8],  # Increased to 8
            'auto_suggest': True,
            'requires_context7': requires_context7,
            'dependencies': [],
            'usage_count': 0,
            'last_used': None,
            'tags': [language, category],
            'auto_registered': True,
            'registered_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

    def _extract_keywords_from_text(self, text: str) -> List[str]:
        """Extract keywords from text (description, etc.)"""
        text_lower = text.lower()
        keywords = []

        # Tech keywords to look for
        tech_keywords = [
            # Languages
            'python', 'java', 'typescript', 'javascript', 'kotlin', 'swift', 'go', 'rust',
            # Docker/Container
            'docker', 'dockerfile', 'container', 'containerize', 'compose', 'docker-compose',
            'image', 'registry', 'build',
            # Kubernetes
            'kubernetes', 'k8s', 'kubectl', 'helm', 'pod', 'deployment',
            # Frameworks
            'flask', 'django', 'fastapi', 'spring boot', 'spring', 'express', 'nestjs',
            'react', 'vue', 'angular', 'javafx', 'swiftui',
            # Payment
            'stripe', 'razorpay', 'paypal', 'square', 'braintree',
            'payment', 'checkout', 'subscription', 'refund', 'webhook',
            # Database
            'database', 'sql', 'nosql', 'mongodb', 'postgres', 'mysql', 'redis',
            # DevOps
            'ci/cd', 'jenkins', 'gitlab', 'github actions', 'devops', 'deployment',
            # UI/Design
            'ui', 'ux', 'design', 'layout', 'component', 'theme', 'css', 'animation',
            # API
            'api', 'rest', 'graphql', 'endpoint', 'controller', 'microservice',
            # Security
            'security', 'auth', 'jwt', 'oauth', 'ssl', 'tls',
            # General
            'integration', 'automation', 'testing', 'optimize', 'troubleshoot'
        ]

        for keyword in tech_keywords:
            if keyword in text_lower:
                keywords.append(keyword)

        # Also extract words from text (alphanumeric, 3+ chars)
        words = re.findall(r'\b[a-z]{3,}\b', text_lower)
        for word in words:
            if word not in keywords and word not in ['the', 'and', 'for', 'with', 'when', 'user', 'this', 'that']:
                keywords.append(word)

        return keywords

    def _apply_keyword_overrides(self, skill_id: str, keywords: List[str], triggers: List[str]) -> Tuple[List[str], List[str]]:
        """Apply manual keyword enhancements for specific skills"""
        if skill_id not in self.keyword_overrides:
            return keywords, triggers

        overrides = self.keyword_overrides[skill_id]

        # Add override keywords (at the beginning for priority)
        if 'add_keywords' in overrides:
            for keyword in overrides['add_keywords']:
                if keyword not in keywords:
                    keywords.insert(0, keyword)

        # Add override triggers (at the beginning for priority)
        if 'add_triggers' in overrides:
            for trigger in overrides['add_triggers']:
                if trigger not in triggers:
                    triggers.insert(0, trigger)

        return keywords, triggers

    def _generate_triggers_from_keywords(self, keywords: List[str], language: str) -> List[str]:
        """Generate trigger patterns from primary keywords"""
        triggers = []

        if len(keywords) >= 1:
            # Single primary keyword (most important!)
            triggers.append(f"\\b{keywords[0]}\\b")

            if len(keywords) >= 2:
                # Primary keyword + secondary keyword
                triggers.append(f"{keywords[0]}.*{keywords[1]}")

                # Add more combinations if we have more keywords
                if len(keywords) >= 3:
                    triggers.append(f"{keywords[0]}.*{keywords[2]}")

                # Primary keyword + language (if not general)
                if language not in ['general', 'typescript']:  # Avoid bad language matches
                    triggers.append(f"{keywords[0]}.*{language}")

        return triggers

    def _is_skill_file(self, file_path: Path) -> bool:
        """Determine if file is an actual skill (not a guide/quickstart)"""
        name = file_path.stem.upper()

        # Include SKILL.md and instructions.md files explicitly
        if name in ['SKILL', 'INSTRUCTIONS']:
            return True

        # Exclude guide files
        exclude_patterns = [
            'GUIDE', 'QUICK-START', 'QUICKSTART', 'README',
            'INDEX', 'TEMPLATE', 'EXAMPLE', 'TEST'
        ]

        for pattern in exclude_patterns:
            if pattern in name:
                return False

        return True

    def _extract_skill_metadata(self, file_path: Path) -> Optional[Dict]:
        """
        Extract skill metadata from markdown file

        Looks for:
        - YAML frontmatter (if present)
        - Title (first # heading)
        - Description (first paragraph after title)
        - Language (from filename or content)
        - Keywords (from content analysis)
        - Size (line count)
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            lines = content.split('\n')
            total_lines = len(lines)

            # Check for YAML frontmatter
            frontmatter = self._parse_frontmatter(content)
            if frontmatter:
                # Use frontmatter metadata if available
                return self._metadata_from_frontmatter(file_path, frontmatter, content, total_lines)

            # Extract title (first # heading)
            title = None
            for line in lines:
                if line.startswith('# '):
                    title = line[2:].strip()
                    break

            if not title:
                title = file_path.stem.replace('-', ' ').title()

            # Extract description (first non-empty paragraph after title)
            description = ""
            in_description = False
            for line in lines:
                if line.startswith('# ') and title in line:
                    in_description = True
                    continue
                if in_description and line.strip() and not line.startswith('#'):
                    description = line.strip()
                    # Remove markdown bold/italic
                    description = re.sub(r'\*\*(.*?)\*\*', r'\1', description)
                    description = re.sub(r'\*(.*?)\*', r'\1', description)
                    break

            if not description:
                description = f"Skill for {title}"

            # Detect language from filename or content
            language = self._detect_language(file_path, content)

            # Detect category
            category = self._detect_category(file_path, content)

            # Extract keywords from content
            keywords = self._extract_keywords(file_path, content)

            # Generate trigger patterns
            trigger_patterns = self._generate_triggers(file_path, keywords, language)

            # Check if requires Context7
            requires_context7 = 'context7' in content.lower() or 'latest' in content.lower()

            # Apply manual keyword enhancements if available
            skill_id = file_path.parent.name.lower() if file_path.stem.upper() in ['SKILL', 'INSTRUCTIONS'] else file_path.stem.lower()
            keywords, trigger_patterns = self._apply_keyword_overrides(skill_id, keywords, trigger_patterns)

            return {
                'name': title,
                'file': str(file_path).replace('\\', '/'),
                'description': description[:200],  # Limit length
                'version': '1.0.0',
                'size': f'{total_lines} lines',
                'language': language,
                'category': category,
                'keywords': keywords[:20],  # Increased limit
                'trigger_patterns': trigger_patterns[:8],  # Increased limit
                'auto_suggest': True,
                'requires_context7': requires_context7,
                'dependencies': [],
                'usage_count': 0,
                'last_used': None,
                'tags': [language, category],
                'auto_registered': True,
                'registered_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

        except Exception as e:
            self._log(f"Error extracting metadata from {file_path}: {e}")
            return None

    def _detect_language(self, file_path: Path, content: str) -> str:
        """Detect programming language from filename or content"""
        filename_lower = file_path.stem.lower()
        content_lower = content.lower()

        # Language detection order: filename → content
        languages = {
            'python': ['python', 'py', 'flask', 'django', 'fastapi'],
            'java': ['java', 'spring', 'javafx', 'maven'],
            'typescript': ['typescript', 'ts', 'node', 'express', 'nestjs'],
            'javascript': ['javascript', 'js', 'react', 'vue', 'angular'],
            'csharp': ['csharp', 'c#', 'dotnet', '.net'],
            'go': ['golang', 'go'],
            'rust': ['rust'],
            'kotlin': ['kotlin', 'android'],
            'swift': ['swift', 'ios', 'swiftui']
        }

        for lang, patterns in languages.items():
            for pattern in patterns:
                if pattern in filename_lower or pattern in content_lower[:1000]:
                    return lang

        return 'general'

    def _detect_category(self, file_path: Path, content: str) -> str:
        """Detect skill category from filename or content"""
        filename_lower = file_path.stem.lower()
        content_lower = content.lower()

        categories = {
            'payment': ['payment', 'stripe', 'razorpay', 'paypal', 'checkout'],
            'ui': ['ui', 'javafx', 'swiftui', 'react', 'vue', 'angular', 'frontend'],
            'database': ['database', 'sql', 'mongodb', 'postgres', 'mysql'],
            'api': ['api', 'rest', 'graphql', 'grpc'],
            'testing': ['test', 'testing', 'junit', 'pytest'],
            'deployment': ['deploy', 'docker', 'kubernetes', 'ci/cd'],
            'security': ['security', 'auth', 'jwt', 'oauth'],
            'automation': ['automation', 'script', 'cli', 'tool']
        }

        for cat, patterns in categories.items():
            for pattern in patterns:
                if pattern in filename_lower or pattern in content_lower[:1000]:
                    return cat

        return 'general'

    def _extract_keywords(self, file_path: Path, content: str) -> List[str]:
        """Extract relevant keywords from filename and content"""
        keywords = set()

        # From filename
        filename_parts = file_path.stem.lower().replace('-', ' ').replace('_', ' ').split()
        keywords.update(filename_parts)

        # Common tech keywords from content (first 2000 chars)
        sample = content.lower()[:2000]

        tech_keywords = [
            # Languages
            'python', 'java', 'typescript', 'javascript', 'kotlin', 'swift',
            # Frameworks
            'flask', 'django', 'fastapi', 'spring boot', 'express', 'nestjs',
            'react', 'vue', 'angular', 'javafx', 'swiftui',
            # Payment
            'stripe', 'razorpay', 'paypal', 'square', 'braintree',
            'payment', 'checkout', 'subscription', 'refund', 'webhook',
            # UI/UX
            'ui', 'ux', 'design', 'layout', 'component', 'theme',
            # API
            'api', 'rest', 'graphql', 'endpoint', 'controller',
            # Database
            'database', 'sql', 'mongodb', 'postgres', 'mysql',
            # General
            'integration', 'automation', 'deployment', 'testing'
        ]

        for keyword in tech_keywords:
            if keyword in sample:
                keywords.add(keyword)

        # Limit to 15 most relevant
        return sorted(list(keywords))[:15]

    def _generate_triggers(self, file_path: Path, keywords: List[str], language: str) -> List[str]:
        """Generate trigger patterns from keywords and language"""
        triggers = []

        # Main keyword combinations
        if len(keywords) >= 2:
            # Combine first 2 keywords with .*
            triggers.append(f"{keywords[0]}.*{keywords[1]}")
            if language != 'general':
                triggers.append(f"{keywords[0]}.*{language}")

        # Add filename-based triggers
        filename_parts = file_path.stem.lower().split('-')
        if len(filename_parts) >= 2:
            triggers.append(f"{filename_parts[0]}.*{filename_parts[1]}")

        return triggers[:5]  # Limit to 5 patterns

    def discover_skills(self) -> List[Path]:
        """Discover all skill files in skills directory (recursive)"""
        if not SKILLS_DIR.exists():
            self._log("Skills directory does not exist")
            return []

        # Recursively find all .md files in skills directory and subdirectories
        all_files = list(SKILLS_DIR.rglob('*.md'))
        skill_files = [f for f in all_files if self._is_skill_file(f)]

        return skill_files

    def register_skill(self, file_path: Path, force: bool = False) -> bool:
        """Register a skill from file path"""
        # Generate skill ID from filename or parent directory
        # If file is named SKILL.md or skill.md or instructions.md, use parent directory name
        if file_path.stem.upper() in ['SKILL', 'INSTRUCTIONS']:
            skill_id = file_path.parent.name.lower()
        else:
            skill_id = file_path.stem.lower()

        # Check if already registered
        if skill_id in self.skills and not force:
            self.skipped_count += 1
            return False

        # Extract metadata
        metadata = self._extract_skill_metadata(file_path)
        if not metadata:
            self._log(f"Failed to extract metadata: {file_path.name}")
            return False

        # Add/update in registry
        if skill_id in self.skills:
            # Preserve usage stats if updating
            metadata['usage_count'] = self.skills[skill_id].get('usage_count', 0)
            metadata['last_used'] = self.skills[skill_id].get('last_used', None)
            self.updated_count += 1
        else:
            self.registered_count += 1

        self.skills[skill_id] = metadata
        return True

    def auto_register_all(self, dry_run: bool = False, force: bool = False) -> Dict:
        """Auto-discover and register all skills"""
        skill_files = self.discover_skills()

        if dry_run:
            print(f"DRY RUN: Would register {len(skill_files)} skills\n")

        for skill_file in skill_files:
            if dry_run:
                metadata = self._extract_skill_metadata(skill_file)
                if metadata:
                    print(f"• {skill_file.name}")
                    print(f"  Name: {metadata['name']}")
                    print(f"  Language: {metadata['language']}")
                    print(f"  Category: {metadata['category']}")
                    print(f"  Keywords: {', '.join(metadata['keywords'][:5])}")
                    print()
            else:
                self.register_skill(skill_file, force=force)

        if not dry_run:
            self._save_registry()
            self._log(f"Auto-registered: {self.registered_count} new, {self.updated_count} updated, {self.skipped_count} skipped")

        return {
            'total_discovered': len(skill_files),
            'registered': self.registered_count,
            'updated': self.updated_count,
            'skipped': self.skipped_count
        }

    def _log(self, message: str):
        """Log auto-register events"""
        AUTO_REGISTER_LOG.parent.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] {message}\n"

        with open(AUTO_REGISTER_LOG, 'a', encoding='utf-8') as f:
            f.write(log_entry)

        print(log_entry.strip())


def main():
    parser = argparse.ArgumentParser(description='Auto-register skills from skills directory')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be registered without making changes')
    parser.add_argument('--force', action='store_true', help='Re-register all skills (update existing)')

    args = parser.parse_args()

    registrar = SkillAutoRegister()
    results = registrar.auto_register_all(dry_run=args.dry_run, force=args.force)

    if not args.dry_run:
        print("\n=== Auto-Registration Complete ===")
        print(f"Total discovered: {results['total_discovered']}")
        print(f"Newly registered: {results['registered']}")
        print(f"Updated: {results['updated']}")
        print(f"Skipped (already registered): {results['skipped']}")
        print(f"\nRegistry: {SKILLS_REGISTRY}")


if __name__ == '__main__':
    main()

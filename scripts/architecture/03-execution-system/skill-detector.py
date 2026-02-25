#!/usr/bin/env python3
"""
Skill Detection System - Auto-suggest relevant skills based on user messages
Part of Claude Memory System

Usage:
  python skill-detector.py "I need to add Stripe payment to my Flask app"
  python skill-detector.py --analyze "build an IDE with JavaFX"
  python skill-detector.py --list
"""

import json
import re
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from collections import defaultdict

# Paths
MEMORY_DIR = Path.home() / '.claude' / 'memory'
SKILLS_REGISTRY = MEMORY_DIR / 'skills-registry.json'
SKILL_DETECTOR_LOG = MEMORY_DIR / 'logs' / 'skill-detector.log'

class SkillDetector:
    def __init__(self):
        self.registry = self._load_registry()
        self.skills = self.registry.get('skills', {})

    def _load_registry(self) -> Dict:
        """Load skills registry from JSON"""
        if not SKILLS_REGISTRY.exists():
            return {"skills": {}, "statistics": {}}

        with open(SKILLS_REGISTRY, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _save_registry(self):
        """Save updated registry back to JSON"""
        with open(SKILLS_REGISTRY, 'w', encoding='utf-8') as f:
            json.dump(self.registry, f, indent=2, ensure_ascii=False)

    def detect_skills(self, user_message: str, threshold: float = 0.3) -> List[Dict]:
        """
        Detect relevant skills from user message

        Args:
            user_message: User's input text
            threshold: Minimum relevance score (0.0-1.0)

        Returns:
            List of matched skills with relevance scores, sorted by score (descending)
        """
        matches = []

        for skill_id, skill_data in self.skills.items():
            if not skill_data.get('auto_suggest', False):
                continue

            score = self._calculate_relevance(user_message, skill_data)

            if score >= threshold:
                matches.append({
                    'skill_id': skill_id,
                    'name': skill_data['name'],
                    'description': skill_data['description'],
                    'score': score,
                    'file': skill_data['file'],
                    'requires_context7': skill_data.get('requires_context7', False),
                    'tags': skill_data.get('tags', [])
                })

        # Sort by relevance score (descending)
        matches.sort(key=lambda x: x['score'], reverse=True)

        return matches

    def _calculate_relevance(self, message: str, skill_data: Dict) -> float:
        """
        Calculate relevance score between message and skill

        Scoring:
        - Trigger pattern match: +0.5
        - Keyword match: +0.1 per keyword (max +0.4)
        - Language match: +0.2
        - Category match: +0.1
        """
        message_lower = message.lower()
        score = 0.0

        # 1. Check trigger patterns (highest weight)
        trigger_patterns = skill_data.get('trigger_patterns', [])
        for pattern in trigger_patterns:
            if re.search(pattern, message_lower, re.IGNORECASE):
                score += 0.5
                break  # Only count once

        # 2. Check keywords
        keywords = skill_data.get('keywords', [])
        keyword_matches = 0
        for keyword in keywords:
            if keyword.lower() in message_lower:
                keyword_matches += 1

        # Cap keyword contribution at 0.4
        keyword_score = min(keyword_matches * 0.1, 0.4)
        score += keyword_score

        # 3. Check language mention
        language = skill_data.get('language', '')
        if language and language.lower() in message_lower:
            score += 0.2

        # 4. Check category relevance
        category = skill_data.get('category', '')
        if category and category.lower() in message_lower:
            score += 0.1

        # Cap at 1.0
        return min(score, 1.0)

    def suggest_skills(self, user_message: str, max_suggestions: int = 3) -> str:
        """
        Generate user-friendly skill suggestions

        Returns formatted suggestion text
        """
        matches = self.detect_skills(user_message)

        if not matches:
            return ""

        # Limit to top N suggestions
        top_matches = matches[:max_suggestions]

        suggestions = []
        suggestions.append("=== Relevant Skills Detected ===\n")

        for i, match in enumerate(top_matches, 1):
            skill_name = match['name']
            description = match['description']
            score_pct = int(match['score'] * 100)
            context7_note = " [Context7 Required]" if match['requires_context7'] else ""

            suggestions.append(
                f"{i}. {skill_name} ({score_pct}% match){context7_note}\n"
                f"   {description}\n"
            )

        suggestions.append("\nUse: Read the skill file to apply it to your task.")

        return "".join(suggestions)

    def update_usage(self, skill_id: str):
        """Update usage statistics for a skill"""
        if skill_id not in self.skills:
            return

        # Update skill usage
        self.skills[skill_id]['usage_count'] = self.skills[skill_id].get('usage_count', 0) + 1
        self.skills[skill_id]['last_used'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Update global statistics
        stats = self.registry.get('statistics', {})

        # Find most/least used
        usage_counts = {sid: data.get('usage_count', 0) for sid, data in self.skills.items()}
        if usage_counts:
            stats['most_used'] = max(usage_counts, key=usage_counts.get)
            stats['least_used'] = min(usage_counts, key=usage_counts.get)

        self.registry['statistics'] = stats
        self._save_registry()

        # Log usage
        self._log_event(f"skill-used | {skill_id} | count={self.skills[skill_id]['usage_count']}")

    def list_all_skills(self) -> str:
        """List all available skills"""
        output = []
        output.append("=== Available Skills ===\n")

        for skill_id, skill_data in self.skills.items():
            name = skill_data['name']
            category = skill_data.get('category', 'N/A')
            language = skill_data.get('language', 'N/A')
            size = skill_data.get('size', 'N/A')
            usage = skill_data.get('usage_count', 0)

            output.append(
                f"• {name}\n"
                f"  ID: {skill_id}\n"
                f"  Category: {category} | Language: {language} | Size: {size}\n"
                f"  Used: {usage} times\n"
            )

        # Add statistics
        stats = self.registry.get('statistics', {})
        output.append(f"\nTotal Skills: {stats.get('total_skills', len(self.skills))}")
        if stats.get('most_used'):
            output.append(f"Most Used: {stats['most_used']}")

        return "".join(output)

    def get_skill_by_id(self, skill_id: str) -> Optional[Dict]:
        """Get skill details by ID"""
        return self.skills.get(skill_id)

    def search_skills(self, query: str) -> List[Dict]:
        """Search skills by keyword"""
        query_lower = query.lower()
        results = []

        for skill_id, skill_data in self.skills.items():
            # Search in name, description, keywords, tags
            searchable = [
                skill_data.get('name', ''),
                skill_data.get('description', ''),
                ' '.join(skill_data.get('keywords', [])),
                ' '.join(skill_data.get('tags', []))
            ]

            searchable_text = ' '.join(searchable).lower()

            if query_lower in searchable_text:
                results.append({
                    'skill_id': skill_id,
                    'name': skill_data['name'],
                    'description': skill_data['description'],
                    'file': skill_data['file']
                })

        return results

    def _log_event(self, message: str):
        """Log skill detector events"""
        SKILL_DETECTOR_LOG.parent.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] {message}\n"

        with open(SKILL_DETECTOR_LOG, 'a', encoding='utf-8') as f:
            f.write(log_entry)


def main():
    """CLI interface for skill detector"""
    detector = SkillDetector()

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python skill-detector.py 'user message here'")
        print("  python skill-detector.py --list")
        print("  python skill-detector.py --search 'keyword'")
        print("  python skill-detector.py --used 'skill-id'")
        sys.exit(1)

    command = sys.argv[1]

    if command == '--list':
        print(detector.list_all_skills())

    elif command == '--search':
        if len(sys.argv) < 3:
            print("Error: --search requires a query")
            sys.exit(1)

        query = sys.argv[2]
        results = detector.search_skills(query)

        if results:
            print(f"Search results for '{query}':\n")
            for result in results:
                print(f"• {result['name']}")
                print(f"  {result['description']}")
                print(f"  File: {result['file']}\n")
        else:
            print(f"No skills found for '{query}'")

    elif command == '--used':
        if len(sys.argv) < 3:
            print("Error: --used requires a skill ID")
            sys.exit(1)

        skill_id = sys.argv[2]
        detector.update_usage(skill_id)
        print(f"Updated usage for: {skill_id}")

    else:
        # Treat as user message for detection
        user_message = command
        suggestions = detector.suggest_skills(user_message)

        if suggestions:
            print(suggestions)
        else:
            print("No relevant skills detected for this message.")


if __name__ == '__main__':
    main()

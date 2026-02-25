#!/usr/bin/env python3
"""
Model Selection Enforcer
Analyzes requests and enforces correct model selection
"""

import sys
import re
import json
import argparse
from pathlib import Path
from datetime import datetime

class ModelSelectionEnforcer:
    def __init__(self):
        self.memory_dir = Path.home() / '.claude' / 'memory'
        self.usage_log = self.memory_dir / 'logs' / 'model-usage.log'

        # Ensure log directory exists
        self.usage_log.parent.mkdir(parents=True, exist_ok=True)

        # Model selection rules
        self.rules = {
            'haiku': {
                'keywords': ['search', 'find', 'grep', 'glob', 'list', 'show', 'read', 'view', 'check', 'status', 'get'],
                'patterns': [
                    r'\b(search|find|grep|list|show)\b',
                    r'\b(read|view|check|status)\b',
                    r'\bget\s+\w+',
                ],
                'description': 'Quick searches, reads, status checks',
                'priority': 1
            },
            'sonnet': {
                'keywords': ['implement', 'create', 'write', 'edit', 'modify', 'update', 'fix', 'refactor', 'add', 'build'],
                'patterns': [
                    r'\b(implement|create|write|build)\b',
                    r'\b(edit|modify|update|fix)\b',
                    r'\b(add|refactor|change)\b',
                ],
                'description': 'Implementation, editing, fixes',
                'priority': 2
            },
            'opus': {
                'keywords': ['design', 'architecture', 'plan', 'analyze', 'complex', 'system', 'strategy', 'approach'],
                'patterns': [
                    r'\b(design|architect|plan)\b',
                    r'\b(analyze|evaluate|assess)\b',
                    r'\b(complex|system|strategy)\b',
                ],
                'description': 'Architecture, planning, complex analysis',
                'priority': 3
            }
        }

    def analyze_request(self, message):
        """Analyze request and determine required model"""
        message_lower = message.lower()

        scores = {
            'haiku': 0,
            'sonnet': 0,
            'opus': 0
        }

        # Score based on keywords
        for model, rules in self.rules.items():
            for keyword in rules['keywords']:
                if keyword in message_lower:
                    scores[model] += 1

            # Score based on patterns
            for pattern in rules['patterns']:
                if re.search(pattern, message_lower):
                    scores[model] += 2

        # Detect special cases
        if any(word in message_lower for word in ['architecture', 'design system', 'plan implementation', 'design microservices']):
            scores['opus'] += 5

        if any(word in message_lower for word in ['implement', 'create function', 'write code', 'build feature', 'add functionality']):
            scores['sonnet'] += 4  # Increased weight for implementation

        if any(word in message_lower for word in ['find file', 'search for', 'list all', 'show me', 'get list']):
            scores['haiku'] += 3

        # Determine recommended model
        # If "analyze" present, strongly prefer Opus
        if re.search(r'\banalyz[e|ing]\b', message_lower) and scores['opus'] >= 2:
            recommended = 'opus'
        # If "implement" (but not "improvement") is in message, prefer Sonnet
        elif re.search(r'\bimplement(ation|ing|ed|s)?\b', message_lower) and scores['sonnet'] >= 2:
            recommended = 'sonnet'
        elif scores['opus'] >= 5:  # Increased threshold for Opus
            recommended = 'opus'
        elif scores['sonnet'] >= 2:
            recommended = 'sonnet'
        elif scores['haiku'] >= 1:
            recommended = 'haiku'
        else:
            # Default to sonnet for ambiguous requests
            recommended = 'sonnet'

        result = {
            'message': message[:100],
            'recommended_model': recommended,
            'scores': scores,
            'reasoning': self._get_reasoning(recommended, scores),
            'confidence': self._calculate_confidence(scores, recommended)
        }

        return result

    def _get_reasoning(self, model, scores):
        """Get reasoning for model selection"""
        if model == 'haiku':
            return "Quick search/read operation - Haiku is fastest and most cost-effective"
        elif model == 'sonnet':
            return "Implementation/modification task - Sonnet provides good balance of capability and speed"
        elif model == 'opus':
            return "Complex planning/architecture task - Opus required for deep reasoning"
        return "Default selection"

    def _calculate_confidence(self, scores, recommended):
        """Calculate confidence in recommendation"""
        max_score = scores[recommended]
        other_scores = [s for m, s in scores.items() if m != recommended]

        if not other_scores or max(other_scores) == 0:
            return 1.0

        # Confidence based on score difference
        diff = max_score - max(other_scores)
        confidence = min(1.0, 0.5 + (diff * 0.1))

        return round(confidence, 2)

    def log_usage(self, model, request_type, context=None):
        """Log model usage"""
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] {model.upper()} | {request_type}"

        if context:
            log_entry += f" | {context}"

        log_entry += "\n"

        with open(self.usage_log, 'a', encoding='utf-8') as f:
            f.write(log_entry)

    def enforce(self, message, current_model='sonnet'):
        """Enforce model selection"""
        analysis = self.analyze_request(message)
        recommended = analysis['recommended_model']

        result = {
            'current_model': current_model,
            'recommended_model': recommended,
            'should_change': current_model != recommended,
            'analysis': analysis
        }

        # Log the enforcement
        self.log_usage(
            recommended,
            'ENFORCEMENT',
            f"current={current_model}, confidence={analysis['confidence']}"
        )

        return result

    def get_usage_stats(self, days=7):
        """Get model usage statistics"""
        if not self.usage_log.exists():
            return {
                'total_requests': 0,
                'by_model': {},
                'percentage': {}
            }

        stats = {
            'haiku': 0,
            'sonnet': 0,
            'opus': 0
        }

        try:
            with open(self.usage_log, 'r', encoding='utf-8') as f:
                for line in f:
                    for model in ['HAIKU', 'SONNET', 'OPUS']:
                        if model in line:
                            stats[model.lower()] += 1
                            break
        except:
            pass

        total = sum(stats.values())

        result = {
            'total_requests': total,
            'by_model': stats,
            'percentage': {}
        }

        if total > 0:
            for model, count in stats.items():
                result['percentage'][model] = round((count / total) * 100, 1)

        return result

def main():
    parser = argparse.ArgumentParser(description='Model selection enforcer')
    parser.add_argument('--analyze', help='Analyze request message')
    parser.add_argument('--enforce', nargs=2, metavar=('MESSAGE', 'CURRENT_MODEL'),
                       help='Enforce model selection')
    parser.add_argument('--stats', action='store_true', help='Show usage statistics')
    parser.add_argument('--init', action='store_true', help='Initialize enforcer')
    parser.add_argument('--test', action='store_true', help='Test model selection')

    args = parser.parse_args()

    enforcer = ModelSelectionEnforcer()

    if args.init:
        print("Model selection enforcer initialized")
        print(f"Usage log: {enforcer.usage_log}")
        return 0

    if args.test:
        print("Testing model selection...")

        test_cases = [
            ("Find all Python files in the src directory", "haiku"),
            ("Implement a user authentication system with JWT", "sonnet"),
            ("Design the microservices architecture for our application", "opus"),
            ("Read the configuration file", "haiku"),
            ("Fix the bug in the login function", "sonnet"),
            ("Analyze the performance bottlenecks and suggest improvements", "opus"),
        ]

        correct = 0
        for message, expected in test_cases:
            result = enforcer.analyze_request(message)
            actual = result['recommended_model']

            if actual == expected:
                print(f"[OK] '{message[:50]}...' -> {actual}")
                correct += 1
            else:
                print(f"[FAIL] '{message[:50]}...' -> {actual} (expected {expected})")

        print(f"\nResults: {correct}/{len(test_cases)} correct ({correct/len(test_cases)*100:.0f}%)")

        if correct == len(test_cases):
            print("[OK] All tests passed!")
            return 0
        else:
            print("[WARN] Some tests failed")
            return 1

    if args.analyze:
        result = enforcer.analyze_request(args.analyze)
        print(json.dumps(result, indent=2))
        return 0

    if args.enforce:
        message, current_model = args.enforce
        result = enforcer.enforce(message, current_model)
        print(json.dumps(result, indent=2))
        return 0

    if args.stats:
        stats = enforcer.get_usage_stats()
        print(json.dumps(stats, indent=2))
        return 0

    parser.print_help()
    return 1

if __name__ == '__main__':
    sys.exit(main())

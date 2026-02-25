#!/usr/bin/env python3
"""
Failure KB Auto-Update Script
Manages project-specific failure learning and pattern promotion
"""

import os
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

class FailurePattern:
    def __init__(self, signature: str, details: str):
        self.signature = signature
        self.details = details
        self.frequency = 1
        self.first_seen = datetime.now()
        self.last_seen = datetime.now()
        self.status = "Monitoring"  # Monitoring → Learning → Confirmed → Global
        self.confidence = 0.0
        self.solution = None
        self.preventions_successful = 0
        self.preventions_attempted = 0

    def to_dict(self):
        return {
            'signature': self.signature,
            'details': self.details,
            'frequency': self.frequency,
            'first_seen': self.first_seen.isoformat(),
            'last_seen': self.last_seen.isoformat(),
            'status': self.status,
            'confidence': self.confidence,
            'solution': self.solution,
            'preventions_successful': self.preventions_successful,
            'preventions_attempted': self.preventions_attempted
        }

    @classmethod
    def from_dict(cls, data):
        pattern = cls(data['signature'], data['details'])
        pattern.frequency = data['frequency']
        pattern.first_seen = datetime.fromisoformat(data['first_seen'])
        pattern.last_seen = datetime.fromisoformat(data['last_seen'])
        pattern.status = data['status']
        pattern.confidence = data['confidence']
        pattern.solution = data.get('solution')
        pattern.preventions_successful = data.get('preventions_successful', 0)
        pattern.preventions_attempted = data.get('preventions_attempted', 0)
        return pattern


class FailureKB:
    def __init__(self, project_name: str):
        self.project_name = project_name
        self.home = Path.home()
        self.session_dir = self.home / ".claude" / "memory" / "sessions" / project_name
        self.failures_file = self.session_dir / "failures.md"
        self.failures_json = self.session_dir / "failures.json"  # Internal storage
        self.global_kb = self.home / ".claude" / "memory" / "common-failures-prevention.md"
        self.patterns: Dict[str, FailurePattern] = {}

        self._load()

    def _load(self):
        """Load existing patterns from JSON storage"""
        if self.failures_json.exists():
            with open(self.failures_json, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for pattern_data in data.get('patterns', []):
                    pattern = FailurePattern.from_dict(pattern_data)
                    self.patterns[pattern.signature] = pattern

    def _save(self):
        """Save patterns to JSON and generate markdown report"""
        # Save JSON (internal)
        self.session_dir.mkdir(parents=True, exist_ok=True)
        with open(self.failures_json, 'w', encoding='utf-8') as f:
            json.dump({
                'project': self.project_name,
                'last_updated': datetime.now().isoformat(),
                'patterns': [p.to_dict() for p in self.patterns.values()]
            }, f, indent=2)

        # Generate markdown report
        self._generate_markdown()

    def _generate_markdown(self):
        """Generate human-readable markdown report"""
        total_failures = sum(p.frequency for p in self.patterns.values())
        active_patterns = [p for p in self.patterns.values() if p.status in ['Confirmed', 'Learning']]
        confirmed_patterns = [p for p in self.patterns.values() if p.status == 'Confirmed']
        monitoring_patterns = [p for p in self.patterns.values() if p.status == 'Monitoring']

        total_preventions = sum(p.preventions_attempted for p in self.patterns.values())
        successful_preventions = sum(p.preventions_successful for p in self.patterns.values())
        prevention_rate = (successful_preventions / total_preventions * 100) if total_preventions > 0 else 0

        with open(self.failures_file, 'w', encoding='utf-8') as f:
            f.write(f"# Failure Memory: {self.project_name}\n\n")
            f.write(f"**Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Total Failures Recorded:** {total_failures}\n")
            f.write(f"**Patterns Learned:** {len(self.patterns)}\n")
            f.write(f"**Prevention Success Rate:** {prevention_rate:.1f}%\n\n")
            f.write("---\n\n")

            # Quick Stats
            f.write("## 📊 Quick Stats\n\n")
            f.write("| Metric | Value |\n")
            f.write("|--------|-------|\n")
            f.write(f"| Total Failures | {total_failures} |\n")
            f.write(f"| Active Patterns | {len(active_patterns)} |\n")
            f.write(f"| Confirmed Patterns | {len(confirmed_patterns)} |\n")
            f.write(f"| Under Observation | {len(monitoring_patterns)} |\n")
            f.write(f"| Prevention Success Rate | {prevention_rate:.1f}% |\n\n")
            f.write("---\n\n")

            # Active Patterns (Confirmed)
            f.write("## ✅ Active Patterns (Auto-Applied)\n\n")
            if confirmed_patterns:
                for pattern in confirmed_patterns:
                    f.write(f"### {pattern.signature}\n\n")
                    f.write(f"**Status:** Confirmed ✅\n")
                    f.write(f"**Frequency:** {pattern.frequency} occurrences\n")
                    f.write(f"**Confidence:** {pattern.confidence:.0f}%\n")
                    f.write(f"**First Seen:** {pattern.first_seen.strftime('%Y-%m-%d')}\n")
                    if pattern.solution:
                        f.write(f"**Solution:** {pattern.solution}\n")
                    f.write(f"**Prevention Stats:** {pattern.preventions_successful}/{pattern.preventions_attempted} successful\n\n")
                    f.write(f"**Details:** {pattern.details}\n\n")
                    f.write("---\n\n")
            else:
                f.write("*(No confirmed patterns yet)*\n\n")

            # Learning Patterns
            f.write("## ⚠️ Learning Patterns (Being Validated)\n\n")
            learning_patterns = [p for p in self.patterns.values() if p.status == 'Learning']
            if learning_patterns:
                for pattern in learning_patterns:
                    f.write(f"### {pattern.signature}\n\n")
                    f.write(f"**Status:** Learning ⚠️\n")
                    f.write(f"**Frequency:** {pattern.frequency} occurrences\n")
                    f.write(f"**First Seen:** {pattern.first_seen.strftime('%Y-%m-%d')}\n")
                    f.write(f"**Details:** {pattern.details}\n\n")
                    f.write("---\n\n")
            else:
                f.write("*(No learning patterns)*\n\n")

            # Monitoring
            f.write("## 👁️ Failed Attempts (Under Observation)\n\n")
            if monitoring_patterns:
                for pattern in monitoring_patterns:
                    f.write(f"### {pattern.signature}\n\n")
                    f.write(f"**Status:** Monitoring 👁️\n")
                    f.write(f"**First Seen:** {pattern.first_seen.strftime('%Y-%m-%d')}\n")
                    f.write(f"**Details:** {pattern.details}\n\n")
                    f.write("*Waiting for 2nd occurrence to confirm pattern...*\n\n")
                    f.write("---\n\n")
            else:
                f.write("*(No patterns under observation)*\n\n")

    def log_failure(self, signature: str, details: str, solution: Optional[str] = None) -> str:
        """Log a new failure or update existing pattern"""

        if signature in self.patterns:
            # Existing pattern - update
            pattern = self.patterns[signature]
            pattern.frequency += 1
            pattern.last_seen = datetime.now()

            # Update status based on frequency
            if pattern.frequency >= 2 and pattern.status == 'Monitoring':
                pattern.status = 'Learning'
            elif pattern.frequency >= 3 and pattern.status == 'Learning':
                if pattern.confidence >= 80:
                    pattern.status = 'Confirmed'

            if solution:
                pattern.solution = solution

            self._save()
            return f"Pattern updated: {signature} (frequency: {pattern.frequency}, status: {pattern.status})"
        else:
            # New pattern
            pattern = FailurePattern(signature, details)
            if solution:
                pattern.solution = solution
            self.patterns[signature] = pattern
            self._save()
            return f"New pattern logged: {signature} (status: Monitoring)"

    def log_prevention(self, signature: str, success: bool):
        """Log a prevention attempt"""
        if signature in self.patterns:
            pattern = self.patterns[signature]
            pattern.preventions_attempted += 1
            if success:
                pattern.preventions_successful += 1

            # Update confidence
            pattern.confidence = (pattern.preventions_successful / pattern.preventions_attempted) * 100

            self._save()

    def check_pattern(self, signature: str) -> Optional[Dict]:
        """Check if pattern exists and return solution"""
        if signature in self.patterns:
            pattern = self.patterns[signature]
            if pattern.status in ['Learning', 'Confirmed'] and pattern.confidence >= 80:
                return {
                    'found': True,
                    'solution': pattern.solution,
                    'confidence': pattern.confidence,
                    'status': pattern.status
                }
        return None

    def check_promotion_eligibility(self) -> List[str]:
        """Check which patterns should be promoted to global KB"""
        eligible = []
        for signature, pattern in self.patterns.items():
            if (pattern.status == 'Confirmed' and
                pattern.confidence == 100 and
                pattern.frequency >= 5):
                eligible.append(signature)
        return eligible


def log_failure(project_name: str, signature: str, details: str, solution: str = None):
    """Public API: Log a failure"""
    kb = FailureKB(project_name)
    result = kb.log_failure(signature, details, solution)
    print(result)

    # Check promotion eligibility
    eligible = kb.check_promotion_eligibility()
    if eligible:
        print(f"\n⭐ Patterns eligible for global promotion: {', '.join(eligible)}")


def log_prevention(project_name: str, signature: str, success: bool):
    """Public API: Log a prevention attempt"""
    kb = FailureKB(project_name)
    kb.log_prevention(signature, success)
    print(f"Prevention logged: {signature} - {'Success' if success else 'Failed'}")


def check_pattern(project_name: str, signature: str):
    """Public API: Check if pattern exists"""
    kb = FailureKB(project_name)
    result = kb.check_pattern(signature)
    if result:
        print(f"Pattern found: {signature}")
        print(f"  Solution: {result['solution']}")
        print(f"  Confidence: {result['confidence']:.0f}%")
        print(f"  Status: {result['status']}")
    else:
        print(f"No pattern found for: {signature}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 4:
        print("Usage:")
        print("  Log failure:    python update-failure-kb.py PROJECT_NAME log SIGNATURE DETAILS [SOLUTION]")
        print("  Log prevention: python update-failure-kb.py PROJECT_NAME prevent SIGNATURE SUCCESS")
        print("  Check pattern:  python update-failure-kb.py PROJECT_NAME check SIGNATURE")
        sys.exit(1)

    project = sys.argv[1]
    action = sys.argv[2]

    if action == "log":
        sig = sys.argv[3]
        det = sys.argv[4] if len(sys.argv) > 4 else "No details"
        sol = sys.argv[5] if len(sys.argv) > 5 else None
        log_failure(project, sig, det, sol)

    elif action == "prevent":
        sig = sys.argv[3]
        success = sys.argv[4].lower() == "true"
        log_prevention(project, sig, success)

    elif action == "check":
        sig = sys.argv[3]
        check_pattern(project, sig)

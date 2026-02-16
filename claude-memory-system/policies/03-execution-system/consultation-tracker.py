#!/usr/bin/env python3
"""
Consultation Tracker
Tracks user consultation decisions to avoid repeated questions
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

class ConsultationTracker:
    def __init__(self):
        self.memory_dir = Path.home() / '.claude' / 'memory'
        self.consultations_log = self.memory_dir / 'logs' / 'consultations.log'
        self.preferences_file = self.memory_dir / 'consultation-preferences.json'

        # Ensure files exist
        self.consultations_log.parent.mkdir(parents=True, exist_ok=True)
        if not self.preferences_file.exists():
            self.preferences_file.write_text('{}')

    def load_preferences(self):
        """Load consultation preferences"""
        try:
            return json.loads(self.preferences_file.read_text())
        except:
            return {}

    def save_preferences(self, preferences):
        """Save consultation preferences"""
        self.preferences_file.write_text(json.dumps(preferences, indent=2))

    def log_consultation(self, decision_type, question, options, user_choice):
        """Log a consultation decision"""
        timestamp = datetime.now().isoformat()
        log_entry = {
            'timestamp': timestamp,
            'decision_type': decision_type,
            'question': question,
            'options': options,
            'user_choice': user_choice
        }

        # Append to log
        with open(self.consultations_log, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry) + '\n')

        # Update preferences
        self._update_preference(decision_type, user_choice, options)

    def _update_preference(self, decision_type, choice, options):
        """Update preference based on choice"""
        preferences = self.load_preferences()

        if decision_type not in preferences:
            preferences[decision_type] = {
                'choices': [],
                'last_choice': None,
                'consistent': False
            }

        pref = preferences[decision_type]
        pref['choices'].append({
            'choice': choice,
            'timestamp': datetime.now().isoformat()
        })
        pref['last_choice'] = choice

        # Check consistency (last 3 choices)
        recent_choices = [c['choice'] for c in pref['choices'][-3:]]
        if len(recent_choices) >= 2 and len(set(recent_choices)) == 1:
            pref['consistent'] = True
            pref['default'] = choice
        else:
            pref['consistent'] = False

        self.save_preferences(preferences)

    def should_consult(self, decision_type):
        """Check if should consult user or use default"""
        preferences = self.load_preferences()

        if decision_type not in preferences:
            return {
                'should_ask': True,
                'reason': 'No previous decision',
                'default': None
            }

        pref = preferences[decision_type]

        if pref['consistent']:
            return {
                'should_ask': False,
                'reason': 'Consistent pattern detected',
                'default': pref['default']
            }

        return {
            'should_ask': True,
            'reason': 'Inconsistent choices',
            'last_choice': pref.get('last_choice')
        }

    def get_decision_history(self, decision_type=None):
        """Get decision history"""
        if not self.consultations_log.exists():
            return []

        history = []
        try:
            with open(self.consultations_log, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        if decision_type is None or entry['decision_type'] == decision_type:
                            history.append(entry)
                    except:
                        pass
        except:
            pass

        return history

    def get_all_preferences(self):
        """Get all consultation preferences"""
        return self.load_preferences()

    def reset_preference(self, decision_type):
        """Reset a specific preference"""
        preferences = self.load_preferences()

        if decision_type in preferences:
            del preferences[decision_type]
            self.save_preferences(preferences)
            return True

        return False

    def get_statistics(self):
        """Get consultation statistics"""
        preferences = self.load_preferences()
        history = self.get_decision_history()

        stats = {
            'total_consultations': len(history),
            'unique_decision_types': len(preferences),
            'consistent_preferences': 0,
            'by_decision_type': {}
        }

        for decision_type, pref in preferences.items():
            if pref['consistent']:
                stats['consistent_preferences'] += 1

            stats['by_decision_type'][decision_type] = {
                'total_choices': len(pref['choices']),
                'consistent': pref['consistent'],
                'default': pref.get('default')
            }

        return stats

def main():
    parser = argparse.ArgumentParser(description='Consultation tracker')
    parser.add_argument('--log', nargs=4, metavar=('TYPE', 'QUESTION', 'OPTIONS', 'CHOICE'),
                       help='Log a consultation')
    parser.add_argument('--check', help='Check if should consult for decision type')
    parser.add_argument('--history', help='Get decision history (optional: for specific type)')
    parser.add_argument('--preferences', action='store_true', help='Show all preferences')
    parser.add_argument('--stats', action='store_true', help='Show statistics')
    parser.add_argument('--reset', help='Reset preference for decision type')
    parser.add_argument('--test', action='store_true', help='Test consultation tracking')

    args = parser.parse_args()

    tracker = ConsultationTracker()

    if args.test:
        print("Testing consultation tracker...")

        # Test 1: Log consultations
        print("\n1. Log consultations")
        tracker.log_consultation(
            'planning_mode',
            'Should I enter plan mode?',
            ['yes', 'no'],
            'yes'
        )
        print("   [OK] Logged consultation 1")

        tracker.log_consultation(
            'planning_mode',
            'Should I enter plan mode?',
            ['yes', 'no'],
            'yes'
        )
        print("   [OK] Logged consultation 2")

        # Test 2: Check if should consult
        print("\n2. Check if should consult")
        result = tracker.should_consult('planning_mode')
        print(f"   Should ask: {result['should_ask']}")
        print(f"   Reason: {result['reason']}")

        if result['should_ask']:
            # Log one more to establish pattern
            print("   Logging one more to establish pattern...")
            tracker.log_consultation(
                'planning_mode',
                'Should I enter plan mode?',
                ['yes', 'no'],
                'yes'
            )

            result = tracker.should_consult('planning_mode')
            print(f"   Now should ask: {result['should_ask']}")
            print(f"   Default: {result.get('default')}")

        # Test 3: Get statistics
        print("\n3. Get statistics")
        stats = tracker.get_statistics()
        print(f"   Total consultations: {stats['total_consultations']}")
        print(f"   Consistent preferences: {stats['consistent_preferences']}")

        print("\n[OK] All tests completed!")
        return 0

    if args.log:
        decision_type, question, options_str, choice = args.log
        try:
            options = json.loads(options_str)
        except:
            options = options_str.split(',')

        tracker.log_consultation(decision_type, question, options, choice)
        print(f"Consultation logged: {decision_type} = {choice}")
        return 0

    if args.check:
        result = tracker.should_consult(args.check)
        print(json.dumps(result, indent=2))
        return 0

    if args.history is not None:
        decision_type = args.history if args.history else None
        history = tracker.get_decision_history(decision_type)
        print(json.dumps(history, indent=2))
        return 0

    if args.preferences:
        preferences = tracker.get_all_preferences()
        print(json.dumps(preferences, indent=2))
        return 0

    if args.stats:
        stats = tracker.get_statistics()
        print(json.dumps(stats, indent=2))
        return 0

    if args.reset:
        success = tracker.reset_preference(args.reset)
        if success:
            print(f"Preference reset: {args.reset}")
        else:
            print(f"Preference not found: {args.reset}")
        return 0

    parser.print_help()
    return 1

if __name__ == '__main__':
    sys.exit(main())

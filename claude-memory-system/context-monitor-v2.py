#!/usr/bin/env python3
"""
Context Monitor v2
Enhanced monitoring with actionable recommendations
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

class ContextMonitorV2:
    def __init__(self):
        self.memory_dir = Path.home() / '.claude' / 'memory'
        self.context_file = self.memory_dir / '.context-usage'
        self.estimate_file = self.memory_dir / '.context-estimate'

        # Thresholds
        self.thresholds = {
            'green': 70,    # < 70% OK
            'yellow': 85,   # 70-85% use cache
            'orange': 90,   # 85-90% use external state
            'red': 95       # 90%+ save and restart
        }

    def get_context_percentage(self):
        """Get current context usage percentage"""
        # Try to read from context file
        if self.context_file.exists():
            try:
                data = json.loads(self.context_file.read_text())
                return data.get('percentage', 0)
            except:
                pass

        # Try estimate file
        if self.estimate_file.exists():
            try:
                data = self.estimate_file.read_text().strip()
                return float(data)
            except:
                pass

        return 0

    def get_status_level(self, percentage):
        """Get status level based on percentage"""
        if percentage < self.thresholds['green']:
            return 'green'
        elif percentage < self.thresholds['yellow']:
            return 'yellow'
        elif percentage < self.thresholds['orange']:
            return 'orange'
        else:
            return 'red'

    def get_recommendations(self, percentage):
        """Get actionable recommendations based on usage"""
        level = self.get_status_level(percentage)
        recommendations = []

        if level == 'green':
            recommendations.append("[OK] Context usage healthy")

        elif level == 'yellow':
            recommendations.append("[WARN]  Context usage elevated (70-85%)")
            recommendations.append("-> Use cached file summaries when available")
            recommendations.append("-> Use offset/limit for large file reads")
            recommendations.append("-> Use head_limit for Grep searches")

        elif level == 'orange':
            recommendations.append("[HIGH] Context usage high (85-90%)")
            recommendations.append("-> REQUIRED: Reference session state instead of full history")
            recommendations.append("-> Use context cache aggressively")
            recommendations.append("-> Extract summaries from tool outputs")
            recommendations.append("-> Consider saving session and continuing in new context")

        else:  # red
            recommendations.append("[CRITICAL] Context usage critical (90%+)")
            recommendations.append("-> IMMEDIATE: Save current session state")
            recommendations.append("-> IMMEDIATE: Start new session with state reference")
            recommendations.append("-> DO NOT execute large tool calls")

        return recommendations

    def get_optimization_suggestions(self):
        """Get general optimization suggestions"""
        return [
            "Use pre-execution-optimizer.py before tool calls",
            "Use context-extractor.py after tool outputs",
            "Check context-cache.py for cached summaries",
            "Use session-state.py to reference external state",
            "Review files accessed 3+ times for caching"
        ]

    def get_current_status(self):
        """Get complete current status"""
        percentage = self.get_context_percentage()
        level = self.get_status_level(percentage)
        recommendations = self.get_recommendations(percentage)

        status = {
            'percentage': percentage,
            'level': level,
            'thresholds': self.thresholds,
            'recommendations': recommendations,
            'timestamp': datetime.now().isoformat()
        }

        # Add cache stats if available
        try:
            from pathlib import Path
            cache_dir = self.memory_dir / '.cache'
            if cache_dir.exists():
                cache_files = len(list(cache_dir.rglob('*.json')))
                status['cache_entries'] = cache_files
        except:
            pass

        # Add session state info
        try:
            state_dir = self.memory_dir / '.state'
            if state_dir.exists():
                state_files = list(state_dir.glob('*.json'))
                status['active_sessions'] = len(state_files)
        except:
            pass

        return status

    def update_percentage(self, percentage):
        """Update context percentage"""
        data = {
            'percentage': percentage,
            'updated_at': datetime.now().isoformat()
        }

        self.context_file.write_text(json.dumps(data, indent=2))
        self.estimate_file.write_text(str(percentage))

        return True

    def simulate(self, percentage):
        """Simulate context usage at percentage"""
        print(f"\n{'='*60}")
        print(f"SIMULATING CONTEXT AT {percentage}%")
        print(f"{'='*60}\n")

        # Temporarily update
        original = self.get_context_percentage()
        self.update_percentage(percentage)

        # Get status
        status = self.get_current_status()

        # Print status
        print(f"Level: {status['level'].upper()}")
        print(f"\nRecommendations:")
        for rec in status['recommendations']:
            print(f"  {rec}")

        print(f"\nOptimization Suggestions:")
        for sug in self.get_optimization_suggestions():
            print(f"  • {sug}")

        # Restore original
        self.update_percentage(original)

        return status

    def init(self):
        """Initialize monitoring"""
        # Create necessary directories
        (self.memory_dir / '.cache').mkdir(exist_ok=True)
        (self.memory_dir / '.cache' / 'summaries').mkdir(exist_ok=True)
        (self.memory_dir / '.cache' / 'queries').mkdir(exist_ok=True)
        (self.memory_dir / '.state').mkdir(exist_ok=True)

        # Initialize context file if not exists
        if not self.context_file.exists():
            self.update_percentage(0)

        print("[OK] Context monitoring initialized")
        return True

def main():
    parser = argparse.ArgumentParser(description='Context monitor v2')
    parser.add_argument('--current-status', action='store_true', help='Get current status')
    parser.add_argument('--update', type=float, help='Update percentage')
    parser.add_argument('--simulate', type=float, help='Simulate percentage')
    parser.add_argument('--init', action='store_true', help='Initialize monitoring')
    parser.add_argument('--recommendations', action='store_true', help='Get recommendations only')

    args = parser.parse_args()

    monitor = ContextMonitorV2()

    if args.init:
        monitor.init()
        return 0

    if args.simulate is not None:
        monitor.simulate(args.simulate)
        return 0

    if args.update is not None:
        monitor.update_percentage(args.update)
        print(f"Context percentage updated to {args.update}%")
        return 0

    if args.recommendations:
        percentage = monitor.get_context_percentage()
        recommendations = monitor.get_recommendations(percentage)
        for rec in recommendations:
            print(rec)
        return 0

    # Default: show current status
    status = monitor.get_current_status()
    print(json.dumps(status, indent=2))

    return 0

if __name__ == '__main__':
    sys.exit(main())

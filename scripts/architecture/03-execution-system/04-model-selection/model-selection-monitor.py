#!/usr/bin/env python3
"""
Model Selection Monitor
Monitors model usage distribution and alerts on issues
"""

# Fix encoding for Windows console
import sys
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    try:
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        import io
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


import sys
import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

class ModelSelectionMonitor:
    def __init__(self):
        self.memory_dir = Path.home() / '.claude' / 'memory'
        # Use REAL model selection log with JSON format
        self.usage_log = self.memory_dir / 'logs' / 'model-selection.log'

        # Expected distribution ranges (based on policy)
        self.expected_ranges = {
            'haiku': (35, 45),   # 35-45% for searches
            'sonnet': (50, 60),  # 50-60% for implementation
            'opus': (3, 8)       # 3-8% for architecture
        }

    def parse_log_entry(self, line):
        """Parse log entry - JSON format from real model selection"""
        # Format: {"timestamp": "...", "model": "...", "complexity": ..., "risks": [...]}
        try:
            data = json.loads(line.strip())
            return {
                'timestamp': datetime.fromisoformat(data['timestamp']),
                'model': data['model'].lower(),
                'complexity': data.get('complexity', 0),
                'risks': data.get('risks', []),
                'confidence': data.get('confidence', 'unknown')
            }
        except:
            pass

        return None

    def get_usage_data(self, days=7):
        """Get usage data from log"""
        if not self.usage_log.exists():
            return []

        cutoff = datetime.now() - timedelta(days=days)
        usage_data = []

        try:
            with open(self.usage_log, 'r', encoding='utf-8') as f:
                for line in f:
                    entry = self.parse_log_entry(line)
                    if entry and entry['timestamp'] >= cutoff:
                        usage_data.append(entry)
        except:
            pass

        return usage_data

    def calculate_distribution(self, usage_data):
        """Calculate model usage distribution"""
        counts = defaultdict(int)

        for entry in usage_data:
            counts[entry['model']] += 1

        total = sum(counts.values())

        distribution = {
            'total_requests': total,
            'counts': dict(counts),
            'percentages': {}
        }

        if total > 0:
            for model, count in counts.items():
                distribution['percentages'][model] = round((count / total) * 100, 1)

        return distribution

    def check_distribution(self, distribution):
        """Check if distribution matches expected ranges"""
        issues = []
        warnings = []

        percentages = distribution['percentages']
        total = distribution['total_requests']

        # Check if we have enough data
        if total < 10:
            warnings.append({
                'type': 'insufficient_data',
                'message': f'Only {total} requests logged, need at least 10 for accurate analysis'
            })

        # Check each model's usage
        for model, (min_pct, max_pct) in self.expected_ranges.items():
            actual_pct = percentages.get(model, 0)

            if actual_pct < min_pct:
                issues.append({
                    'model': model,
                    'type': 'underused',
                    'expected': f'{min_pct}-{max_pct}%',
                    'actual': f'{actual_pct}%',
                    'message': f'{model.capitalize()} underused: {actual_pct}% (expected {min_pct}-{max_pct}%)'
                })
            elif actual_pct > max_pct:
                issues.append({
                    'model': model,
                    'type': 'overused',
                    'expected': f'{min_pct}-{max_pct}%',
                    'actual': f'{actual_pct}%',
                    'message': f'{model.capitalize()} overused: {actual_pct}% (expected {min_pct}-{max_pct}%)'
                })

        return {
            'issues': issues,
            'warnings': warnings,
            'compliant': len(issues) == 0
        }

    def get_usage_trends(self, usage_data):
        """Get usage trends over time"""
        # Group by day
        by_day = defaultdict(lambda: defaultdict(int))

        for entry in usage_data:
            day = entry['timestamp'].date().isoformat()
            by_day[day][entry['model']] += 1

        trends = []
        for day in sorted(by_day.keys()):
            day_total = sum(by_day[day].values())
            trends.append({
                'date': day,
                'total': day_total,
                'by_model': dict(by_day[day])
            })

        return trends

    def generate_report(self, days=7):
        """Generate comprehensive usage report"""
        usage_data = self.get_usage_data(days)
        distribution = self.calculate_distribution(usage_data)
        compliance = self.check_distribution(distribution)
        trends = self.get_usage_trends(usage_data)

        report = {
            'period_days': days,
            'generated_at': datetime.now().isoformat(),
            'distribution': distribution,
            'compliance': compliance,
            'trends': trends,
            'expected_ranges': self.expected_ranges
        }

        return report

    def alert_if_non_compliant(self, report):
        """Generate alert if distribution is non-compliant"""
        if not report['compliance']['compliant']:
            alert = {
                'severity': 'WARNING',
                'message': 'Model usage distribution does not match policy',
                'issues': report['compliance']['issues'],
                'recommendations': self._get_recommendations(report['compliance']['issues'])
            }
            return alert

        return None

    def _get_recommendations(self, issues):
        """Get recommendations based on issues"""
        recommendations = []

        for issue in issues:
            model = issue['model']
            issue_type = issue['type']

            if issue_type == 'underused':
                if model == 'haiku':
                    recommendations.append("Use Haiku for more searches and status checks")
                elif model == 'sonnet':
                    recommendations.append("Use Sonnet for more implementation tasks")
                elif model == 'opus':
                    recommendations.append("Use Opus for more architecture and planning tasks")

            elif issue_type == 'overused':
                if model == 'haiku':
                    recommendations.append("Reduce Haiku usage - may be using it for implementation tasks")
                elif model == 'sonnet':
                    recommendations.append("Review if Sonnet is being used appropriately - consider Haiku for simple tasks")
                elif model == 'opus':
                    recommendations.append("Reduce Opus usage - may be using it for simple implementation tasks")

        return recommendations

def main():
    parser = argparse.ArgumentParser(description='Model selection monitor')
    parser.add_argument('--report', action='store_true', help='Generate usage report')
    parser.add_argument('--distribution', action='store_true', help='Show distribution only')
    parser.add_argument('--trend', action='store_true', help='Show daily trend data for charts')
    parser.add_argument('--check-compliance', action='store_true', help='Check compliance only')
    parser.add_argument('--days', type=int, default=7, help='Number of days to analyze')
    parser.add_argument('--alert', action='store_true', help='Generate alert if non-compliant')

    args = parser.parse_args()

    monitor = ModelSelectionMonitor()

    if args.report:
        report = monitor.generate_report(args.days)
        print(json.dumps(report, indent=2))
        return 0

    if args.distribution:
        usage_data = monitor.get_usage_data(args.days)
        distribution = monitor.calculate_distribution(usage_data)
        print(json.dumps(distribution, indent=2))
        return 0

    if args.trend:
        # Get trend data formatted for chart display
        usage_data = monitor.get_usage_data(args.days)
        trends = monitor.get_usage_trends(usage_data)

        # Format for chart: daily labels and separate arrays for each model
        from datetime import datetime, timedelta

        # Create labels for all days in range (even if no data)
        labels = []
        haiku_data = []
        sonnet_data = []
        opus_data = []

        today = datetime.now()
        trends_dict = {t['date']: t['by_model'] for t in trends}

        for i in range(args.days - 1, -1, -1):
            day = today - timedelta(days=i)
            day_str = day.date().isoformat()
            label = day.strftime('%m/%d')

            labels.append(label)

            # Get counts for this day
            day_models = trends_dict.get(day_str, {})
            haiku_data.append(day_models.get('haiku', 0))
            sonnet_data.append(day_models.get('sonnet', 0))
            opus_data.append(day_models.get('opus', 0))

        trend_output = {
            'labels': labels,
            'haiku_data': haiku_data,
            'sonnet_data': sonnet_data,
            'opus_data': opus_data
        }

        print(json.dumps(trend_output, indent=2))
        return 0

    if args.check_compliance:
        usage_data = monitor.get_usage_data(args.days)
        distribution = monitor.calculate_distribution(usage_data)
        compliance = monitor.check_distribution(distribution)
        print(json.dumps(compliance, indent=2))
        return 0

    if args.alert:
        report = monitor.generate_report(args.days)
        alert = monitor.alert_if_non_compliant(report)

        if alert:
            print(json.dumps(alert, indent=2))
            return 1  # Exit code 1 for non-compliance
        else:
            print(json.dumps({
                'status': 'OK',
                'message': 'Model usage distribution is compliant'
            }, indent=2))
            return 0

    # Default: show distribution
    usage_data = monitor.get_usage_data(args.days)
    distribution = monitor.calculate_distribution(usage_data)
    print(json.dumps(distribution, indent=2))
    return 0

if __name__ == '__main__':
    sys.exit(main())

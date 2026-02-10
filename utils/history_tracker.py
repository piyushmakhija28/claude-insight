"""
History Tracker - Track daily metrics for historical analysis
"""
import os
import json
from datetime import datetime, timedelta
from pathlib import Path


class HistoryTracker:
    """Track and store historical metrics for the dashboard"""

    def __init__(self):
        self.memory_dir = Path.home() / '.claude' / 'memory'
        self.history_file = self.memory_dir / 'dashboard_history.json'
        self.ensure_history_file()

    def ensure_history_file(self):
        """Ensure history file exists"""
        if not self.history_file.exists():
            self.history_file.parent.mkdir(parents=True, exist_ok=True)
            self.history_file.write_text(json.dumps({
                'daily_metrics': [],
                'last_updated': datetime.now().isoformat()
            }))

    def load_history(self):
        """Load historical data from file"""
        try:
            if self.history_file.exists():
                return json.loads(self.history_file.read_text())
            return {'daily_metrics': [], 'last_updated': None}
        except Exception as e:
            print(f"Error loading history: {e}")
            return {'daily_metrics': [], 'last_updated': None}

    def save_history(self, data):
        """Save historical data to file"""
        try:
            self.history_file.write_text(json.dumps(data, indent=2))
        except Exception as e:
            print(f"Error saving history: {e}")

    def add_daily_metric(self, metrics):
        """Add a daily metric snapshot"""
        history = self.load_history()
        today = datetime.now().strftime('%Y-%m-%d')

        # Check if today's entry already exists
        existing_index = None
        for i, entry in enumerate(history['daily_metrics']):
            if entry.get('date') == today:
                existing_index = i
                break

        metric_entry = {
            'date': today,
            'timestamp': datetime.now().isoformat(),
            'health_score': metrics.get('health_score', 0),
            'errors_24h': metrics.get('errors_24h', 0),
            'policy_hits': metrics.get('policy_hits', 0),
            'context_usage': metrics.get('context_usage', 0),
            'tokens_used': metrics.get('tokens_used', 0),
            'daemons_running': metrics.get('daemons_running', 0),
            'daemons_total': metrics.get('daemons_total', 8)
        }

        if existing_index is not None:
            # Update existing entry
            history['daily_metrics'][existing_index] = metric_entry
        else:
            # Add new entry
            history['daily_metrics'].append(metric_entry)

        # Keep only last 90 days
        history['daily_metrics'] = sorted(
            history['daily_metrics'],
            key=lambda x: x['date'],
            reverse=True
        )[:90]

        history['last_updated'] = datetime.now().isoformat()
        self.save_history(history)

    def get_last_n_days(self, days=7):
        """Get metrics for the last N days"""
        history = self.load_history()
        metrics = history.get('daily_metrics', [])

        # Sort by date descending
        metrics = sorted(metrics, key=lambda x: x['date'], reverse=True)

        # Get last N days
        last_n = metrics[:days]

        # Reverse to get chronological order
        return list(reversed(last_n))

    def get_chart_data(self, days=7):
        """Get data formatted for Chart.js"""
        metrics = self.get_last_n_days(days)

        if not metrics:
            # Return empty data structure
            return {
                'dates': [],
                'health_scores': [],
                'errors': [],
                'policy_hits': [],
                'context_usage': [],
                'tokens_used': []
            }

        return {
            'dates': [m['date'] for m in metrics],
            'health_scores': [m.get('health_score', 0) for m in metrics],
            'errors': [m.get('errors_24h', 0) for m in metrics],
            'policy_hits': [m.get('policy_hits', 0) for m in metrics],
            'context_usage': [m.get('context_usage', 0) for m in metrics],
            'tokens_used': [m.get('tokens_used', 0) for m in metrics]
        }

    def get_summary_stats(self, days=7):
        """Get summary statistics for the last N days"""
        metrics = self.get_last_n_days(days)

        if not metrics:
            return {
                'avg_health_score': 0,
                'total_errors': 0,
                'total_policy_hits': 0,
                'avg_context_usage': 0,
                'total_tokens': 0,
                'min_health_score': 0,
                'max_health_score': 0
            }

        health_scores = [m.get('health_score', 0) for m in metrics]
        errors = [m.get('errors_24h', 0) for m in metrics]
        policy_hits = [m.get('policy_hits', 0) for m in metrics]
        context_usage = [m.get('context_usage', 0) for m in metrics]
        tokens = [m.get('tokens_used', 0) for m in metrics]

        return {
            'avg_health_score': round(sum(health_scores) / len(health_scores), 1) if health_scores else 0,
            'total_errors': sum(errors),
            'total_policy_hits': sum(policy_hits),
            'avg_context_usage': round(sum(context_usage) / len(context_usage), 1) if context_usage else 0,
            'total_tokens': sum(tokens),
            'min_health_score': min(health_scores) if health_scores else 0,
            'max_health_score': max(health_scores) if health_scores else 0,
            'trend': self._calculate_trend(health_scores)
        }

    def _calculate_trend(self, values):
        """Calculate trend direction (up/down/stable)"""
        if len(values) < 2:
            return 'stable'

        # Compare first half vs second half
        mid = len(values) // 2
        first_half_avg = sum(values[:mid]) / len(values[:mid]) if mid > 0 else 0
        second_half_avg = sum(values[mid:]) / len(values[mid:]) if len(values[mid:]) > 0 else 0

        diff = second_half_avg - first_half_avg

        if diff > 5:
            return 'up'
        elif diff < -5:
            return 'down'
        else:
            return 'stable'

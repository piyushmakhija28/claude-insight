"""
Metrics Collector
Collects metrics from Claude Memory System
"""

import os
import json
import subprocess
from pathlib import Path
from datetime import datetime, timedelta

class MetricsCollector:
    def __init__(self):
        self.memory_dir = Path.home() / '.claude' / 'memory'

    def get_system_health(self):
        """Get overall system health"""
        try:
            result = subprocess.run(
                ['python', str(self.memory_dir / 'pid-tracker.py'), '--health'],
                capture_output=True,
                text=True,
                timeout=10,
                cwd=str(self.memory_dir)
            )

            if result.returncode == 0 and result.stdout.strip():
                health_data = json.loads(result.stdout)
                return {
                    'status': 'healthy' if health_data.get('health_score', 0) >= 90 else 'degraded',
                    'health_score': health_data.get('health_score', 0),
                    'score': health_data.get('health_score', 0),
                    'running_daemons': health_data.get('running', 0),
                    'total_daemons': health_data.get('total_daemons', 8),
                    'context_usage': 45,  # Default until we get from context script
                    'memory_usage': 60,   # Default
                    'uptime': 'Active'
                }
        except Exception as e:
            print(f"Error getting system health: {e}")
            import traceback
            traceback.print_exc()

        return {
            'status': 'unknown',
            'health_score': 0,
            'score': 0,
            'running_daemons': 0,
            'total_daemons': 8,
            'context_usage': 0,
            'memory_usage': 0
        }

    def get_daemon_status(self):
        """Get status of all daemons"""
        try:
            # Use pid-tracker since it gives us daemon status
            result = subprocess.run(
                ['python', str(self.memory_dir / 'pid-tracker.py'), '--health'],
                capture_output=True,
                text=True,
                timeout=10,
                cwd=str(self.memory_dir)
            )

            if result.returncode == 0 and result.stdout.strip():
                health_data = json.loads(result.stdout)
                daemons_dict = health_data.get('daemons', {})

                # Convert dict to list of daemon objects
                daemon_list = []
                for name, data in daemons_dict.items():
                    daemon_list.append({
                        'name': name,
                        'status': 'running' if data.get('is_running') else 'stopped',
                        'pid': data.get('pid', 'N/A'),
                        'uptime': 'Active' if data.get('is_running') else 'Stopped'
                    })

                return daemon_list
        except Exception as e:
            print(f"Error getting daemon status: {e}")
            import traceback
            traceback.print_exc()

        return []

    def get_health_score(self):
        """Get current health score"""
        health = self.get_system_health()
        return health.get('score', 0)

    def get_running_daemon_count(self):
        """Get count of running daemons"""
        health = self.get_system_health()
        return health.get('running_daemons', 0)

    def get_context_usage(self):
        """Get current context usage estimate"""
        try:
            result = subprocess.run(
                ['python', str(self.memory_dir / 'context-monitor-v2.py'), '--current-status'],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                status = json.loads(result.stdout)
                return {
                    'percentage': status.get('percentage', 0),
                    'level': status.get('level', 'unknown'),
                    'status': status.get('status', 'unknown')
                }
        except Exception as e:
            print(f"Error getting context usage: {e}")

        return {'percentage': 0, 'level': 'unknown', 'status': 'unknown'}

    def get_cost_comparison(self):
        """Calculate cost comparison: before vs after optimization"""

        # Estimated costs (based on Claude API pricing)
        SONNET_COST_PER_1M_INPUT = 3.00  # $3 per 1M input tokens
        SONNET_COST_PER_1M_OUTPUT = 15.00  # $15 per 1M output tokens

        # Average session metrics (estimated)
        AVG_SESSION_TOKENS_BEFORE = 50000  # Before optimization
        AVG_SESSION_TOKENS_AFTER = 30000   # After optimization (40% reduction)

        # Calculate costs for 100 sessions
        sessions = 100

        before_tokens = AVG_SESSION_TOKENS_BEFORE * sessions
        after_tokens = AVG_SESSION_TOKENS_AFTER * sessions

        # Assuming 70% input, 30% output
        before_cost = (before_tokens * 0.7 / 1000000 * SONNET_COST_PER_1M_INPUT) + \
                     (before_tokens * 0.3 / 1000000 * SONNET_COST_PER_1M_OUTPUT)

        after_cost = (after_tokens * 0.7 / 1000000 * SONNET_COST_PER_1M_INPUT) + \
                    (after_tokens * 0.3 / 1000000 * SONNET_COST_PER_1M_OUTPUT)

        savings = before_cost - after_cost
        savings_percent = (savings / before_cost) * 100

        return {
            'before': {
                'tokens': before_tokens,
                'cost': round(before_cost, 2),
                'sessions': sessions
            },
            'after': {
                'tokens': after_tokens,
                'cost': round(after_cost, 2),
                'sessions': sessions
            },
            'savings': {
                'tokens': before_tokens - after_tokens,
                'cost': round(savings, 2),
                'percent': round(savings_percent, 1)
            }
        }

    def get_optimization_impact(self):
        """Get optimization impact metrics"""
        try:
            # Read policy hits log to count optimizations
            policy_log = self.memory_dir / 'logs' / 'policy-hits.log'

            if policy_log.exists():
                with open(policy_log, 'r', encoding='utf-8') as f:
                    lines = f.readlines()

                context_opts = sum(1 for line in lines if 'CONTEXT_OPTIMIZATION' in line)
                failure_prevented = sum(1 for line in lines if 'FAILURE_PREVENTION' in line)
                model_enforced = sum(1 for line in lines if 'MODEL_SELECTION' in line)

                return {
                    'context_optimizations': context_opts,
                    'failures_prevented': failure_prevented,
                    'model_selections': model_enforced,
                    'total_optimizations': context_opts + failure_prevented + model_enforced
                }
        except Exception as e:
            print(f"Error getting optimization impact: {e}")

        return {
            'context_optimizations': 0,
            'failures_prevented': 0,
            'model_selections': 0,
            'total_optimizations': 0
        }

    def restart_daemon(self, daemon_name):
        """Restart a specific daemon"""
        try:
            result = subprocess.run(
                ['python', str(self.memory_dir / 'daemon-manager.py'), '--restart', daemon_name],
                capture_output=True,
                text=True,
                timeout=30
            )

            return result.returncode == 0
        except Exception as e:
            print(f"Error restarting daemon: {e}")
            return False

    def get_failure_kb_stats(self):
        """Get failure knowledge base statistics"""
        try:
            result = subprocess.run(
                ['python', str(self.memory_dir / 'pre-execution-checker.py'), '--stats'],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                return json.loads(result.stdout)
        except Exception as e:
            print(f"Error getting KB stats: {e}")

        return {'total_patterns': 0, 'high_confidence': 0, 'by_tool': {}}

    def get_model_usage_stats(self):
        """Get model usage distribution"""
        try:
            result = subprocess.run(
                ['python', str(self.memory_dir / 'model-selection-monitor.py'), '--distribution', '--days', '7'],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                return json.loads(result.stdout)
        except Exception as e:
            print(f"Error getting model stats: {e}")

        return {'total_requests': 0, 'counts': {}, 'percentages': {}}

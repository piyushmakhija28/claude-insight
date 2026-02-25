"""
Policy Compliance Analyzer (Issue #13)
Analyzes policy compliance trends and generates statistics over time.

Reads from:
  - ~/.claude/memory/logs/sessions/*/flow-trace.json

Provides:
  - Compliance percentages per policy and level
  - Trend analysis over time
  - Failing policy identification
  - Report data for /api/policies/compliance/stats
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class PolicyComplianceAnalyzer:
    """Analyze compliance trends across all policies."""

    def __init__(self):
        self.memory_dir = Path.home() / '.claude' / 'memory'
        self.sessions_dir = self.memory_dir / 'logs' / 'sessions'

    STEP_LEVEL_MAP = {
        'LEVEL_MINUS_1': -1,
        'LEVEL_1_CONTEXT': 1,
        'LEVEL_1_SESSION': 1,
        'LEVEL_2_STANDARDS': 2,
        'LEVEL_3_STEP_3_0': 3,
        'LEVEL_3_STEP_3_1': 3,
        'LEVEL_3_STEP_3_2': 3,
        'LEVEL_3_STEP_3_3': 3,
        'LEVEL_3_STEP_3_4': 3,
        'LEVEL_3_STEP_3_5': 3,
        'LEVEL_3_STEP_3_6': 3,
        'LEVEL_3_STEP_3_7': 3,
        'LEVEL_3_STEP_3_8': 3,
        'LEVEL_3_STEP_3_9': 3,
        'LEVEL_3_STEP_3_10': 3,
        'LEVEL_3_STEP_3_11': 3,
        'LEVEL_3_STEP_3_12': 3,
    }

    STEP_NAMES = {
        'LEVEL_MINUS_1': 'Auto-Fix Enforcement',
        'LEVEL_1_CONTEXT': 'Context Management',
        'LEVEL_1_SESSION': 'Session Management',
        'LEVEL_2_STANDARDS': 'Standards Enforcement',
        'LEVEL_3_STEP_3_0': 'Prompt Generation',
        'LEVEL_3_STEP_3_1': 'Task Breakdown',
        'LEVEL_3_STEP_3_2': 'Plan Mode',
        'LEVEL_3_STEP_3_3': 'Context Check',
        'LEVEL_3_STEP_3_4': 'Model Selection',
        'LEVEL_3_STEP_3_5': 'Skill/Agent Selection',
        'LEVEL_3_STEP_3_6': 'Tool Optimization',
        'LEVEL_3_STEP_3_7': 'Failure Prevention',
        'LEVEL_3_STEP_3_8': 'Parallel Analysis',
        'LEVEL_3_STEP_3_9': 'Task Execution',
        'LEVEL_3_STEP_3_10': 'Session Save',
        'LEVEL_3_STEP_3_11': 'Git Auto-Commit',
        'LEVEL_3_STEP_3_12': 'Logging',
    }

    def _load_traces(self, hours: int = 720) -> list:
        """Load flow-trace.json files within the time window."""
        cutoff = datetime.now() - timedelta(hours=hours)
        traces = []

        if not self.sessions_dir.exists():
            return traces

        try:
            trace_files = sorted(
                self.sessions_dir.glob('*/flow-trace.json'),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )[:1000]

            for tf in trace_files:
                try:
                    if datetime.fromtimestamp(tf.stat().st_mtime) < cutoff:
                        continue
                    data = json.loads(tf.read_text(encoding='utf-8', errors='ignore'))
                    traces.append(data)
                except Exception:
                    continue
        except Exception:
            pass

        return traces

    def get_compliance_stats(self, hours: int = 168) -> dict:
        """Get compliance statistics aggregated by step/policy."""
        traces = self._load_traces(hours)

        # Per-step counters
        step_stats = defaultdict(lambda: {'total': 0, 'passed': 0, 'duration_ms': []})

        for trace in traces:
            for step in trace.get('pipeline', []):
                step_name = step.get('step', '')
                if not step_name:
                    continue
                duration_ms = step.get('duration_ms', -1)
                step_stats[step_name]['total'] += 1
                if duration_ms >= 0:
                    step_stats[step_name]['passed'] += 1
                    step_stats[step_name]['duration_ms'].append(duration_ms)

        # Build per-level aggregates
        level_stats = defaultdict(lambda: {'total': 0, 'passed': 0})
        policies = []

        for step_name, counts in step_stats.items():
            total = counts['total']
            passed = counts['passed']
            failed = total - passed
            avg_dur = (sum(counts['duration_ms']) / len(counts['duration_ms'])
                       if counts['duration_ms'] else 0)
            pass_rate = round((passed / total * 100), 1) if total > 0 else 0
            level = self.STEP_LEVEL_MAP.get(step_name, 3)

            level_stats[level]['total'] += total
            level_stats[level]['passed'] += passed

            policies.append({
                'step': step_name,
                'name': self.STEP_NAMES.get(step_name, step_name),
                'level': level,
                'total': total,
                'passed': passed,
                'failed': failed,
                'pass_rate': pass_rate,
                'avg_duration_ms': round(avg_dur, 1),
                'compliant': pass_rate >= 80,
            })

        # Sort by compliance issues first
        policies.sort(key=lambda x: x['pass_rate'])

        # Overall compliance
        grand_total = sum(p['total'] for p in policies)
        grand_passed = sum(p['passed'] for p in policies)
        overall_compliance = round((grand_passed / grand_total * 100), 1) if grand_total > 0 else 0

        # Level compliance summaries
        level_summaries = {}
        for level_num, counts in level_stats.items():
            t = counts['total']
            p = counts['passed']
            level_summaries[f'level_{level_num}'] = {
                'level': level_num,
                'total': t,
                'passed': p,
                'compliance_pct': round((p / t * 100), 1) if t > 0 else 0,
            }

        # Failing policies (< 80% pass rate)
        failing = [p for p in policies if p['pass_rate'] < 80 and p['total'] > 0]

        return {
            'timeframe_hours': hours,
            'total_sessions_analyzed': len(traces),
            'overall_compliance_pct': overall_compliance,
            'total_policy_executions': grand_total,
            'total_passed': grand_passed,
            'total_failed': grand_total - grand_passed,
            'failing_policies': failing,
            'by_level': level_summaries,
            'policies': policies,
        }

    def get_compliance_trend(self, days: int = 7) -> dict:
        """Get daily compliance trend for the last N days."""
        traces = self._load_traces(hours=days * 24)

        daily = defaultdict(lambda: {'total': 0, 'passed': 0})

        for trace in traces:
            flow_start = trace.get('meta', {}).get('flow_start', '')
            if not flow_start:
                continue
            try:
                day = flow_start[:10]  # YYYY-MM-DD
            except Exception:
                continue

            for step in trace.get('pipeline', []):
                duration_ms = step.get('duration_ms', -1)
                daily[day]['total'] += 1
                if duration_ms >= 0:
                    daily[day]['passed'] += 1

        labels = sorted(daily.keys())
        compliance_pcts = []
        for label in labels:
            t = daily[label]['total']
            p = daily[label]['passed']
            compliance_pcts.append(round((p / t * 100), 1) if t > 0 else 0)

        return {
            'days': days,
            'labels': labels,
            'compliance_pct': compliance_pcts,
            'executions': [daily[l]['total'] for l in labels],
        }

    def get_level_compliance(self, level: int, hours: int = 168) -> dict:
        """Get compliance details for a specific level."""
        stats = self.get_compliance_stats(hours)
        level_key = f'level_{level}'
        level_summary = stats['by_level'].get(level_key, {})
        level_policies = [p for p in stats['policies'] if p['level'] == level]

        return {
            'level': level,
            'timeframe_hours': hours,
            'summary': level_summary,
            'policies': level_policies,
        }

    def get_report_data(self, hours: int = 168) -> dict:
        """Generate full compliance report data (for PDF/CSV export)."""
        stats = self.get_compliance_stats(hours)
        trend = self.get_compliance_trend(days=min(7, hours // 24))

        return {
            'generated_at': datetime.now().isoformat(),
            'timeframe_hours': hours,
            'summary': {
                'overall_compliance': stats['overall_compliance_pct'],
                'sessions_analyzed': stats['total_sessions_analyzed'],
                'total_executions': stats['total_policy_executions'],
                'passing': stats['total_passed'],
                'failing': stats['total_failed'],
                'failing_policies_count': len(stats['failing_policies']),
            },
            'by_level': stats['by_level'],
            'all_policies': stats['policies'],
            'failing_policies': stats['failing_policies'],
            'trend': trend,
        }

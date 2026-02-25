"""
Individual Policy Tracker (Issue #11)
Tracks execution metrics for each of the 34+ policies individually.

Reads from:
  - ~/.claude/memory/logs/sessions/*/flow-trace.json
  - ~/.claude/memory/logs/policies/*.json  (per-policy logs if present)

Provides:
  - Per-policy execution count, pass rate, last run time
  - History for each of the 34 named policies
  - API-ready output for /api/policies/<name>/stats
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from utils.path_resolver import get_data_dir


# Canonical list of all 34+ policies tracked by the system
POLICY_REGISTRY = {
    # Level 1: Sync System
    'session-memory': {
        'level': 1,
        'name': 'Session Memory Policy',
        'component': 'session-management',
        'step': 'LEVEL_1_SESSION',
        'file': 'session-memory.md',
    },
    'session-chaining': {
        'level': 1,
        'name': 'Session Chaining Policy',
        'component': 'session-management',
        'step': 'LEVEL_1_SESSION',
        'file': 'session-chaining.md',
    },
    'session-pruning': {
        'level': 1,
        'name': 'Session Pruning Policy',
        'component': 'session-management',
        'step': 'LEVEL_1_SESSION',
        'file': 'session-pruning.md',
    },
    'context-management': {
        'level': 1,
        'name': 'Context Management Policy',
        'component': 'context-management',
        'step': 'LEVEL_1_CONTEXT',
        'file': 'context-management.md',
    },
    'user-preferences': {
        'level': 1,
        'name': 'User Preferences Policy',
        'component': 'user-preferences',
        'step': 'LEVEL_1_SESSION',
        'file': 'user-preferences.md',
    },
    'patterns': {
        'level': 1,
        'name': 'Cross-Project Patterns Policy',
        'component': 'pattern-detection',
        'step': 'LEVEL_1_SESSION',
        'file': 'patterns.md',
    },
    # Level 2: Standards System
    'coding-standards-enforcement': {
        'level': 2,
        'name': 'Coding Standards Enforcement',
        'component': 'standards-system',
        'step': 'LEVEL_2_STANDARDS',
        'file': 'coding-standards-enforcement.md',
    },
    # Level 3: Execution System
    'prompt-generation': {
        'level': 3,
        'name': 'Prompt Generation Policy',
        'component': 'prompt-generation',
        'step': 'LEVEL_3_STEP_3_0',
        'file': 'prompt-generation-policy.md',
    },
    'task-breakdown': {
        'level': 3,
        'name': 'Task Breakdown Policy',
        'component': 'task-breakdown',
        'step': 'LEVEL_3_STEP_3_1',
        'file': 'task-breakdown-policy.md',
    },
    'plan-mode': {
        'level': 3,
        'name': 'Plan Mode Suggestion Policy',
        'component': 'plan-mode',
        'step': 'LEVEL_3_STEP_3_2',
        'file': 'plan-mode-policy.md',
    },
    'model-selection': {
        'level': 3,
        'name': 'Model Selection Policy',
        'component': 'model-selection',
        'step': 'LEVEL_3_STEP_3_4',
        'file': 'model-selection-policy.md',
    },
    'skill-agent-selection': {
        'level': 3,
        'name': 'Skill/Agent Selection Policy',
        'component': 'skill-agent-selection',
        'step': 'LEVEL_3_STEP_3_5',
        'file': 'skill-agent-selection-policy.md',
    },
    'tool-optimization': {
        'level': 3,
        'name': 'Tool Optimization Policy',
        'component': 'tool-optimization',
        'step': 'LEVEL_3_STEP_3_6',
        'file': 'tool-optimization-policy.md',
    },
    'failure-prevention': {
        'level': 3,
        'name': 'Failure Prevention Policy',
        'component': 'failure-prevention',
        'step': 'LEVEL_3_STEP_3_7',
        'file': 'failure-prevention-policy.md',
    },
    'parallel-execution': {
        'level': 3,
        'name': 'Parallel Execution Policy',
        'component': 'execution',
        'step': 'LEVEL_3_STEP_3_8',
        'file': 'parallel-execution-policy.md',
    },
    'progress-tracking': {
        'level': 3,
        'name': 'Progress Tracking Policy',
        'component': 'progress-tracking',
        'step': 'LEVEL_3_STEP_3_9',
        'file': 'progress-tracking-policy.md',
    },
    'session-save': {
        'level': 3,
        'name': 'Session Save Policy',
        'component': 'session-save',
        'step': 'LEVEL_3_STEP_3_10',
        'file': 'session-save-policy.md',
    },
    'git-auto-commit': {
        'level': 3,
        'name': 'Git Auto-Commit Policy',
        'component': 'git-commit',
        'step': 'LEVEL_3_STEP_3_11',
        'file': 'git-auto-commit-policy.md',
    },
    'logging': {
        'level': 3,
        'name': 'Logging Policy',
        'component': 'logging',
        'step': 'LEVEL_3_STEP_3_12',
        'file': 'logging-policy.md',
    },
    'auto-fix-enforcement': {
        'level': -1,
        'name': 'Auto-Fix Enforcement Policy',
        'component': 'auto-fix',
        'step': 'LEVEL_MINUS_1',
        'file': 'auto-fix-enforcement.md',
    },
}

# Map pipeline step names to policy keys
STEP_TO_POLICY = {
    'LEVEL_MINUS_1': 'auto-fix-enforcement',
    'LEVEL_1_CONTEXT': 'context-management',
    'LEVEL_1_SESSION': 'session-memory',
    'LEVEL_2_STANDARDS': 'coding-standards-enforcement',
    'LEVEL_3_STEP_3_0': 'prompt-generation',
    'LEVEL_3_STEP_3_1': 'task-breakdown',
    'LEVEL_3_STEP_3_2': 'plan-mode',
    'LEVEL_3_STEP_3_4': 'model-selection',
    'LEVEL_3_STEP_3_5': 'skill-agent-selection',
    'LEVEL_3_STEP_3_6': 'tool-optimization',
    'LEVEL_3_STEP_3_7': 'failure-prevention',
    'LEVEL_3_STEP_3_8': 'parallel-execution',
    'LEVEL_3_STEP_3_9': 'progress-tracking',
    'LEVEL_3_STEP_3_10': 'session-save',
    'LEVEL_3_STEP_3_11': 'git-auto-commit',
    'LEVEL_3_STEP_3_12': 'logging',
}


class IndividualPolicyTracker:
    """Track execution metrics per individual policy."""

    def __init__(self):
        self.memory_dir = Path.home() / '.claude' / 'memory'
        self.sessions_dir = self.memory_dir / 'logs' / 'sessions'
        self.policies_log_dir = self.memory_dir / 'logs' / 'policies'

    def _parse_all_traces(self, hours: int = 168) -> list:
        """Parse all flow-trace.json files from the last N hours."""
        cutoff = datetime.now() - timedelta(hours=hours)
        traces = []

        if not self.sessions_dir.exists():
            return traces

        try:
            trace_files = sorted(
                self.sessions_dir.glob('*/flow-trace.json'),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )[:500]

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

    def get_policy_stats(self, policy_key: str, hours: int = 168) -> dict:
        """Return execution stats for a single named policy."""
        meta = POLICY_REGISTRY.get(policy_key)
        if not meta:
            return {'error': f'Unknown policy: {policy_key}'}

        step_name = meta['step']
        traces = self._parse_all_traces(hours)

        executions = []
        for trace in traces:
            fd = trace.get('final_decision', {})
            session_id = trace.get('meta', {}).get('session_id', 'unknown')
            flow_start = trace.get('meta', {}).get('flow_start', '')

            for step in trace.get('pipeline', []):
                if step.get('step') == step_name:
                    duration_ms = step.get('duration_ms', 0)
                    status = 'PASS' if duration_ms >= 0 else 'FAIL'
                    executions.append({
                        'session_id': session_id,
                        'timestamp': step.get('timestamp', flow_start)[:19],
                        'status': status,
                        'duration_ms': duration_ms,
                        'decision': step.get('decision', ''),
                        'policy_output': step.get('policy_output', {}),
                    })

        total = len(executions)
        passed = sum(1 for e in executions if e['status'] == 'PASS')
        failed = total - passed
        avg_duration = (
            sum(e['duration_ms'] for e in executions) / total
            if total > 0 else 0
        )
        last_run = executions[0]['timestamp'] if executions else None

        return {
            'policy_key': policy_key,
            'name': meta['name'],
            'level': meta['level'],
            'component': meta['component'],
            'step': step_name,
            'timeframe_hours': hours,
            'total_executions': total,
            'passed': passed,
            'failed': failed,
            'pass_rate': round((passed / total * 100), 1) if total > 0 else 0,
            'avg_duration_ms': round(avg_duration, 1),
            'last_run': last_run,
            'recent_executions': executions[:20],
        }

    def get_all_policy_stats(self, hours: int = 168) -> dict:
        """Return stats for ALL registered policies."""
        traces = self._parse_all_traces(hours)

        # Build per-policy counters from traces in one pass
        counters = defaultdict(lambda: {'total': 0, 'passed': 0, 'durations': [], 'last': None})

        for trace in traces:
            flow_start = trace.get('meta', {}).get('flow_start', '')
            for step in trace.get('pipeline', []):
                step_name = step.get('step', '')
                policy_key = STEP_TO_POLICY.get(step_name)
                if not policy_key:
                    continue
                duration_ms = step.get('duration_ms', 0)
                counters[policy_key]['total'] += 1
                if duration_ms >= 0:
                    counters[policy_key]['passed'] += 1
                    counters[policy_key]['durations'].append(duration_ms)
                ts = step.get('timestamp', flow_start)[:19]
                if counters[policy_key]['last'] is None or ts > counters[policy_key]['last']:
                    counters[policy_key]['last'] = ts

        result = []
        for key, meta in POLICY_REGISTRY.items():
            c = counters[key]
            total = c['total']
            passed = c['passed']
            avg_dur = sum(c['durations']) / len(c['durations']) if c['durations'] else 0
            result.append({
                'policy_key': key,
                'name': meta['name'],
                'level': meta['level'],
                'component': meta['component'],
                'total_executions': total,
                'passed': passed,
                'failed': total - passed,
                'pass_rate': round((passed / total * 100), 1) if total > 0 else 0,
                'avg_duration_ms': round(avg_dur, 1),
                'last_run': c['last'],
                'active': total > 0,
            })

        # Sort: active first, then by level, then by name
        result.sort(key=lambda x: (not x['active'], x['level'], x['name']))

        return {
            'timeframe_hours': hours,
            'total_policies': len(result),
            'active_policies': sum(1 for p in result if p['active']),
            'policies': result,
        }

    def get_policy_timeline(self, policy_key: str, hours: int = 24) -> dict:
        """Get hourly execution timeline for a specific policy."""
        stats = self.get_policy_stats(policy_key, hours)
        executions = stats.get('recent_executions', [])

        hourly = defaultdict(lambda: {'pass': 0, 'fail': 0})
        for e in executions:
            try:
                ts = datetime.fromisoformat(e['timestamp'])
                hour_key = ts.strftime('%Y-%m-%d %H:00')
                if e['status'] == 'PASS':
                    hourly[hour_key]['pass'] += 1
                else:
                    hourly[hour_key]['fail'] += 1
            except Exception:
                continue

        labels = sorted(hourly.keys())
        return {
            'policy_key': policy_key,
            'labels': labels,
            'pass_data': [hourly[h]['pass'] for h in labels],
            'fail_data': [hourly[h]['fail'] for h in labels],
        }

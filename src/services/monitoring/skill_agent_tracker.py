"""
Skill & Agent Selection Tracker
Tracks:
- Skill usage and auto-selection
- Agent invocations
- Plan mode suggestions
"""
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add path resolver for portable paths
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from utils.path_resolver import get_data_dir, get_logs_dir
from collections import defaultdict


class SkillAgentTracker:
    """Track skill and agent usage from Claude Memory System"""

    def __init__(self):
        self.memory_dir = get_data_dir()
        self.logs_dir = self.memory_dir / 'logs'
        self.skills_dir = Path.home() / '.claude' / 'skills'
        self.sessions_dir = self.logs_dir / 'sessions'

    def _load_flow_traces(self, max_files=100):
        """Load flow-trace.json files from sessions directory"""
        traces = []
        if not self.sessions_dir.exists():
            return traces
        try:
            trace_files = sorted(
                self.sessions_dir.glob('*/flow-trace.json'),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )[:max_files]
            for tf in trace_files:
                try:
                    data = json.loads(tf.read_text(encoding='utf-8', errors='ignore'))
                    traces.append(data)
                except Exception:
                    continue
        except Exception:
            pass
        return traces

    def _get_skill_agent_step(self, trace):
        """Extract LEVEL_3_STEP_3_5 policy_output from a trace"""
        for step in trace.get('pipeline', []):
            if step.get('step') == 'LEVEL_3_STEP_3_5':
                return step.get('policy_output', {})
        return {}

    def get_skill_selection_stats(self):
        """
        Track skill usage and auto-selection
        Reads from flow-trace.json LEVEL_3_STEP_3_5 policy_output
        """
        stats = {
            'total_skill_invocations': 0,
            'auto_selected': 0,
            'manual_invoked': 0,
            'skills_by_name': defaultdict(int),
            'recent_invocations': [],
            'top_skills': []
        }

        traces = self._load_flow_traces()
        if not traces:
            return stats

        try:
            for trace in traces:
                po = self._get_skill_agent_step(trace)
                if not po:
                    continue

                selected_type = po.get('selected_type', '')
                selected_name = po.get('selected_name', '')

                if selected_type != 'skill' or not selected_name:
                    continue

                stats['total_skill_invocations'] += 1
                # All flow-trace selections are auto-selected by the 4-layer system
                stats['auto_selected'] += 1
                stats['skills_by_name'][selected_name] += 1

                # Store recent (last 20)
                if len(stats['recent_invocations']) < 20:
                    fd = trace.get('final_decision', {})
                    stats['recent_invocations'].append({
                        'timestamp': trace.get('meta', {}).get('flow_start', datetime.now().isoformat()),
                        'skill_name': selected_name,
                        'reason': po.get('reason', ''),
                        'task_type': fd.get('task_type', ''),
                        'complexity': fd.get('complexity', 0)
                    })

            # Get top 10 skills
            stats['top_skills'] = sorted(
                [{'name': k, 'count': v} for k, v in stats['skills_by_name'].items()],
                key=lambda x: x['count'],
                reverse=True
            )[:10]

            # Convert defaultdict
            stats['skills_by_name'] = dict(stats['skills_by_name'])

        except Exception as e:
            stats['error'] = str(e)

        return stats

    def get_agent_usage_stats(self):
        """
        Track agent invocations
        Reads from flow-trace.json LEVEL_3_STEP_3_5 policy_output
        """
        stats = {
            'total_agent_invocations': 0,
            'agents_by_type': defaultdict(int),
            'avg_agent_duration': 0,
            'parallel_agents': 0,
            'sequential_agents': 0,
            'recent_invocations': [],
            'top_agents': []
        }

        traces = self._load_flow_traces()
        if not traces:
            return stats

        try:
            total_duration = 0

            for trace in traces:
                po = self._get_skill_agent_step(trace)
                if not po:
                    continue

                selected_type = po.get('selected_type', '')
                selected_name = po.get('selected_name', '')

                if selected_type != 'agent' or not selected_name:
                    continue

                stats['total_agent_invocations'] += 1
                stats['agents_by_type'][selected_name] += 1

                # Duration from final_decision
                fd = trace.get('final_decision', {})
                meta = trace.get('meta', {})
                duration = meta.get('duration_seconds', 0)
                total_duration += duration

                # Execution mode
                if fd.get('execution_mode', '') == 'parallel':
                    stats['parallel_agents'] += 1
                else:
                    stats['sequential_agents'] += 1

                # Store recent (last 15)
                if len(stats['recent_invocations']) < 15:
                    stats['recent_invocations'].append({
                        'timestamp': meta.get('flow_start', datetime.now().isoformat()),
                        'agent_type': selected_name,
                        'reason': po.get('reason', ''),
                        'task_type': fd.get('task_type', ''),
                        'complexity': fd.get('complexity', 0),
                        'duration_seconds': round(duration, 1)
                    })

            # Calculate average duration
            if stats['total_agent_invocations'] > 0:
                stats['avg_agent_duration'] = round(total_duration / stats['total_agent_invocations'], 1)

            # Get top 10 agents
            stats['top_agents'] = sorted(
                [{'type': k, 'count': v} for k, v in stats['agents_by_type'].items()],
                key=lambda x: x['count'],
                reverse=True
            )[:10]

            # Convert defaultdict
            stats['agents_by_type'] = dict(stats['agents_by_type'])

        except Exception as e:
            stats['error'] = str(e)

        return stats

    def get_plan_mode_suggestions(self):
        """
        Track plan mode auto-suggestions
        Reads from flow-trace.json final_decision.plan_mode and complexity
        """
        stats = {
            'total_suggestions': 0,
            'auto_entered': 0,
            'user_approved': 0,
            'user_declined': 0,
            'complexity_scores': [],
            'recent_suggestions': []
        }

        traces = self._load_flow_traces()
        if not traces:
            stats['avg_complexity'] = 0
            return stats

        try:
            for trace in traces:
                fd = trace.get('final_decision', {})
                complexity = fd.get('complexity', 0)

                # Find plan mode step
                plan_mode_triggered = False
                for step in trace.get('pipeline', []):
                    if step.get('step') == 'LEVEL_3_STEP_3_2':
                        po = step.get('policy_output', {})
                        plan_mode_val = po.get('plan_mode_required', False)
                        if plan_mode_val or fd.get('plan_mode', False):
                            plan_mode_triggered = True
                        break

                stats['total_suggestions'] += 1
                stats['complexity_scores'].append(complexity)

                # Categorize outcome based on final_decision.plan_mode
                if fd.get('plan_mode', False):
                    stats['auto_entered'] += 1
                else:
                    stats['user_declined'] += 1

                # Store recent (last 10)
                if len(stats['recent_suggestions']) < 10:
                    stats['recent_suggestions'].append({
                        'timestamp': trace.get('meta', {}).get('flow_start', datetime.now().isoformat()),
                        'plan_mode': fd.get('plan_mode', False),
                        'complexity': complexity,
                        'task_type': fd.get('task_type', ''),
                        'model': fd.get('model_selected', '')
                    })

            # Calculate average complexity
            if stats['complexity_scores']:
                stats['avg_complexity'] = round(
                    sum(stats['complexity_scores']) / len(stats['complexity_scores']), 1
                )
            else:
                stats['avg_complexity'] = 0

        except Exception as e:
            stats['error'] = str(e)
            stats['avg_complexity'] = 0

        return stats

    def get_plan_mode_stats(self):
        """Alias for get_plan_mode_suggestions()"""
        return self.get_plan_mode_suggestions()

    def get_agent_invocation_stats(self):
        """Alias for get_agent_usage_stats()"""
        return self.get_agent_usage_stats()

    def get_comprehensive_stats(self):
        """
        Get all skill/agent statistics in one call
        """
        return {
            'skills': self.get_skill_selection_stats(),
            'agents': self.get_agent_usage_stats(),
            'plan_mode': self.get_plan_mode_suggestions(),
            'timestamp': datetime.now().isoformat()
        }

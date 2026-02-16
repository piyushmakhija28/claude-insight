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

    def get_skill_selection_stats(self):
        """
        Track skill usage and auto-selection
        Reads from policy-hits.log and skill usage logs
        """
        policy_log = self.logs_dir / 'policy-hits.log'

        stats = {
            'total_skill_invocations': 0,
            'auto_selected': 0,
            'manual_invoked': 0,
            'skills_by_name': defaultdict(int),
            'recent_invocations': [],
            'top_skills': []
        }

        if not policy_log.exists():
            return stats

        try:
            lines = policy_log.read_text().splitlines()

            for line in lines:
                if 'skill' in line.lower() and ('invoked' in line.lower() or 'selected' in line.lower()):
                    stats['total_skill_invocations'] += 1

                    # Detect auto vs manual
                    if 'auto' in line.lower():
                        stats['auto_selected'] += 1
                    else:
                        stats['manual_invoked'] += 1

                    # Extract skill name
                    if ':' in line:
                        try:
                            skill_name = line.split('skill:')[1].strip().split()[0].strip('",')
                            stats['skills_by_name'][skill_name] += 1
                        except:
                            pass

                    # Store recent (last 20)
                    if len(stats['recent_invocations']) < 20:
                        stats['recent_invocations'].append({
                            'timestamp': datetime.now().isoformat(),
                            'log_entry': line[:200]
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
        Track agent invocations (Task tool usage)
        Reads from agent usage logs
        """
        policy_log = self.logs_dir / 'policy-hits.log'

        stats = {
            'total_agent_invocations': 0,
            'agents_by_type': defaultdict(int),
            'avg_agent_duration': 0,
            'parallel_agents': 0,
            'sequential_agents': 0,
            'recent_invocations': [],
            'top_agents': []
        }

        if not policy_log.exists():
            return stats

        try:
            lines = policy_log.read_text().splitlines()

            for line in lines:
                if 'agent' in line.lower() and ('invoked' in line.lower() or 'task tool' in line.lower()):
                    stats['total_agent_invocations'] += 1

                    # Extract agent type
                    if 'subagent_type' in line.lower() or 'agent:' in line.lower():
                        try:
                            # Try different patterns
                            if 'subagent_type:' in line:
                                agent_type = line.split('subagent_type:')[1].strip().split()[0].strip('",')
                            elif 'agent:' in line:
                                agent_type = line.split('agent:')[1].strip().split()[0].strip('",')
                            else:
                                agent_type = 'unknown'

                            stats['agents_by_type'][agent_type] += 1
                        except:
                            pass

                    # Detect parallel vs sequential
                    if 'parallel' in line.lower():
                        stats['parallel_agents'] += 1
                    else:
                        stats['sequential_agents'] += 1

                    # Store recent (last 15)
                    if len(stats['recent_invocations']) < 15:
                        stats['recent_invocations'].append({
                            'timestamp': datetime.now().isoformat(),
                            'log_entry': line[:200]
                        })

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
        Reads from auto-plan-mode logs
        """
        policy_log = self.logs_dir / 'policy-hits.log'

        stats = {
            'total_suggestions': 0,
            'auto_entered': 0,
            'user_approved': 0,
            'user_declined': 0,
            'complexity_scores': [],
            'recent_suggestions': []
        }

        if not policy_log.exists():
            return stats

        try:
            lines = policy_log.read_text().splitlines()

            for line in lines:
                if 'plan mode' in line.lower() or 'enter plan' in line.lower():
                    stats['total_suggestions'] += 1

                    # Detect outcome
                    if 'auto-enter' in line.lower() or 'mandatory' in line.lower():
                        stats['auto_entered'] += 1
                    elif 'approved' in line.lower() or 'accepted' in line.lower():
                        stats['user_approved'] += 1
                    elif 'declined' in line.lower() or 'skipped' in line.lower():
                        stats['user_declined'] += 1

                    # Extract complexity score
                    if 'complexity:' in line.lower() or 'score:' in line.lower():
                        try:
                            score = int(line.split('score:' if 'score:' in line.lower() else 'complexity:')[1].strip().split()[0])
                            stats['complexity_scores'].append(score)
                        except:
                            pass

                    # Store recent (last 10)
                    if len(stats['recent_suggestions']) < 10:
                        stats['recent_suggestions'].append({
                            'timestamp': datetime.now().isoformat(),
                            'log_entry': line[:200]
                        })

            # Calculate average complexity
            if stats['complexity_scores']:
                stats['avg_complexity'] = sum(stats['complexity_scores']) / len(stats['complexity_scores'])
            else:
                stats['avg_complexity'] = 0

        except Exception as e:
            stats['error'] = str(e)

        return stats

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

"""
Automation System Tracker
Tracks all CLAUDE.md automation components:
- Session-start recommendations
- Task breakdown enforcement
- 9th daemon (auto-recommendation)
- Task auto-tracker
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


class AutomationTracker:
    """Track Claude Memory System automation components"""

    def __init__(self):
        self.memory_dir = get_data_dir()
        self.logs_dir = self.memory_dir / 'logs'
        self.sessions_dir = self.memory_dir / 'sessions'

    def get_session_start_recommendations(self):
        """
        Get latest session-start recommendations
        Reads from: ~/.claude/memory/.last-automation-check.json
        """
        recommendations_file = self.memory_dir / '.last-automation-check.json'

        if not recommendations_file.exists():
            return {
                'available': False,
                'message': 'No recommendations available. Run session-start.sh first.',
                'recommendations': None
            }

        try:
            with open(recommendations_file, 'r') as f:
                data = json.load(f)

            return {
                'available': True,
                'timestamp': data.get('timestamp'),
                'model_recommendation': data.get('model'),
                'skills_recommended': data.get('skills', []),
                'agents_recommended': data.get('agents', []),
                'context_status': data.get('context_status', 'UNKNOWN'),
                'context_percentage': data.get('context_percentage', 0),
                'optimizations_needed': data.get('optimizations', []),
                'daemons_status': data.get('daemons', {})
            }
        except Exception as e:
            return {
                'available': False,
                'error': str(e),
                'message': 'Failed to read recommendations'
            }

    def get_9th_daemon_status(self):
        """
        Get status of 9th daemon (auto-recommendation-daemon)
        """
        pid_file = self.memory_dir / '.pids' / 'auto-recommendation-daemon.pid'
        log_file = self.logs_dir / 'daemons' / 'auto-recommendation-daemon.log'

        status = {
            'name': 'auto-recommendation-daemon',
            'description': 'Generates recommendations every 5 seconds',
            'status': 'not_started',
            'pid': None,
            'last_activity': None,
            'recommendations_generated': 0
        }

        # Check PID
        if pid_file.exists():
            try:
                pid = int(pid_file.read_text().strip())
                if self._is_process_running(pid):
                    status['status'] = 'running'
                    status['pid'] = pid
                else:
                    status['status'] = 'stopped'
            except Exception:
                status['status'] = 'error'

        # Check log for activity
        if log_file.exists():
            try:
                lines = log_file.read_text().splitlines()
                if lines:
                    # Get last log timestamp
                    last_line = lines[-1]
                    if '[' in last_line:
                        timestamp_str = last_line.split('[')[1].split(']')[0]
                        status['last_activity'] = timestamp_str

                    # Count recommendations
                    status['recommendations_generated'] = sum(1 for line in lines if 'recommendation' in line.lower())
            except Exception:
                pass

        return status

    def _is_process_running(self, pid):
        """Check if process is running"""
        try:
            import psutil
            return psutil.pid_exists(pid)
        except ImportError:
            try:
                os.kill(pid, 0)
                return True
            except OSError:
                return False

    def get_task_breakdown_stats(self):
        """
        Track task-phase-enforcer.py executions
        Reads from policy-hits.log and task breakdown logs
        """
        policy_log = self.logs_dir / 'policy-hits.log'

        stats = {
            'total_analyses': 0,
            'tasks_required': 0,
            'phases_required': 0,
            'complexity_distribution': defaultdict(int),
            'recent_breakdowns': []
        }

        if not policy_log.exists():
            return stats

        try:
            lines = policy_log.read_text().splitlines()

            for line in lines:
                if 'task-phase-enforcer' in line or 'task-breakdown' in line:
                    stats['total_analyses'] += 1

                    # Parse complexity
                    if 'complexity:' in line.lower():
                        try:
                            complexity = int(line.split('complexity:')[1].strip().split()[0])
                            if complexity >= 3:
                                stats['tasks_required'] += 1
                            if complexity >= 6:
                                stats['phases_required'] += 1
                            stats['complexity_distribution'][complexity] += 1
                        except:
                            pass

                    # Store recent breakdowns (last 10)
                    if len(stats['recent_breakdowns']) < 10:
                        stats['recent_breakdowns'].append({
                            'timestamp': datetime.now().isoformat(),
                            'log_entry': line[:200]
                        })

            # Convert defaultdict to regular dict
            stats['complexity_distribution'] = dict(stats['complexity_distribution'])

        except Exception as e:
            stats['error'] = str(e)

        return stats

    def get_task_tracker_stats(self):
        """
        Get task auto-tracker statistics
        Tracks automatic task progress updates
        """
        # This would read from task tracking logs
        # For now, return placeholder
        return {
            'enabled': True,
            'total_tasks_tracked': 0,
            'auto_updates': 0,
            'manual_updates': 0,
            'completion_rate': 0,
            'average_progress_updates': 0
        }

    def get_comprehensive_automation_stats(self):
        """
        Get all automation statistics in one call
        """
        return {
            'session_start': self.get_session_start_recommendations(),
            'task_breakdown': self.get_task_breakdown_stats(),
            'task_tracker': self.get_task_tracker_stats(),
            'timestamp': datetime.now().isoformat()
        }

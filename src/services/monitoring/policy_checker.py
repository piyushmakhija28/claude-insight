"""
Policy Checker
Checks status of all policies in Claude Memory System
"""

import os
import json
import subprocess
from pathlib import Path

class PolicyChecker:
    def __init__(self):
        self.memory_dir = Path.home() / '.claude' / 'memory'

        self.policies = [
            {
                'id': 'context-management',
                'name': 'Context Management',
                'description': 'Proactive context optimization (-30 to -50% usage)',
                'files': ['pre-execution-optimizer.py', 'context-cache.py', 'session-state.py'],
                'phase': 1
            },
            {
                'id': 'daemon-infrastructure',
                'name': 'Daemon Infrastructure',
                'description': 'Cross-platform daemons with auto-restart',
                'files': ['daemon-manager.py', 'pid-tracker.py', 'health-monitor-daemon.py'],
                'phase': 2
            },
            {
                'id': 'failure-prevention',
                'name': 'Failure Prevention',
                'description': 'Auto-fix known failures (7 patterns)',
                'files': ['failure-detector-v2.py', 'pre-execution-checker.py', 'failure-kb.json'],
                'phase': 3
            },
            {
                'id': 'model-selection',
                'name': 'Model Selection',
                'description': 'Automatic model selection (Haiku/Sonnet/Opus)',
                'files': ['model-selection-enforcer.py', 'model-selection-monitor.py'],
                'phase': 4
            },
            {
                'id': 'consultation-tracking',
                'name': 'Consultation Tracking',
                'description': 'Auto-skip repeated questions (after 2 same choices)',
                'files': ['consultation-tracker.py', 'consultation-preferences.json'],
                'phase': 4
            },
            {
                'id': 'core-skills',
                'name': 'Core Skills Enforcement',
                'description': 'Mandatory skills execution order',
                'files': ['core-skills-enforcer.py'],
                'phase': 4
            }
        ]

    def get_all_policies_status(self):
        """Get status of all policies"""
        statuses = []

        for policy in self.policies:
            status = self._check_policy_status(policy)
            statuses.append({
                'id': policy['id'],
                'name': policy['name'],
                'description': policy['description'],
                'phase': policy['phase'],
                'status': status['status'],
                'details': status['details']
            })

        return statuses

    def _check_policy_status(self, policy):
        """Check status of a single policy"""
        # Check if all required files exist
        all_files_exist = True
        missing_files = []

        for file_name in policy['files']:
            file_path = self.memory_dir / file_name
            if not file_path.exists():
                all_files_exist = False
                missing_files.append(file_name)

        if not all_files_exist:
            return {
                'status': 'error',
                'details': f"Missing files: {', '.join(missing_files)}"
            }

        # Additional checks for specific policies
        if policy['id'] == 'daemon-infrastructure':
            # Check if daemons are running
            daemon_status = self._check_daemons()
            if daemon_status['running'] < daemon_status['total']:
                return {
                    'status': 'warning',
                    'details': f"Only {daemon_status['running']}/{daemon_status['total']} daemons running"
                }

        elif policy['id'] == 'failure-prevention':
            # Check KB patterns
            kb_stats = self._get_kb_stats()
            if kb_stats['patterns'] == 0:
                return {
                    'status': 'warning',
                    'details': 'No patterns in knowledge base'
                }
            return {
                'status': 'active',
                'details': f"{kb_stats['patterns']} patterns, {kb_stats['high_conf']} high confidence"
            }

        elif policy['id'] == 'model-selection':
            # Check model usage
            model_stats = self._get_model_stats()
            return {
                'status': 'active',
                'details': f"{model_stats['requests']} requests tracked"
            }

        # Default: policy is active
        return {
            'status': 'active',
            'details': 'All files present and operational'
        }

    def _check_daemons(self):
        """Check daemon status"""
        try:
            result = subprocess.run(
                ['python', str(self.memory_dir / 'daemon-manager.py'), '--status-all', '--format', 'json'],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                statuses = json.loads(result.stdout)
                running = sum(1 for s in statuses.values() if s.get('running'))
                return {'running': running, 'total': len(statuses)}
        except:
            pass

        return {'running': 0, 'total': 8}

    def _get_kb_stats(self):
        """Get failure KB stats"""
        try:
            result = subprocess.run(
                ['python', str(self.memory_dir / 'pre-execution-checker.py'), '--stats'],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                stats = json.loads(result.stdout)
                return {
                    'patterns': stats.get('total_patterns', 0),
                    'high_conf': stats.get('high_confidence', 0)
                }
        except:
            pass

        return {'patterns': 0, 'high_conf': 0}

    def _get_model_stats(self):
        """Get model usage stats"""
        try:
            result = subprocess.run(
                ['python', str(self.memory_dir / 'model-selection-monitor.py'), '--distribution', '--days', '7'],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                stats = json.loads(result.stdout)
                return {'requests': stats.get('total_requests', 0)}
        except:
            pass

        return {'requests': 0}

    def get_detailed_policy_status(self):
        """Get detailed status for all policies"""
        detailed = {
            'total_policies': len(self.policies),
            'active_policies': 0,
            'warning_policies': 0,
            'error_policies': 0,
            'policies': []
        }

        for policy in self.policies:
            status = self._check_policy_status(policy)

            policy_data = {
                'id': policy['id'],
                'name': policy['name'],
                'description': policy['description'],
                'phase': f"Phase {policy['phase']}",
                'status': status['status'],
                'details': status['details'],
                'files': policy['files']
            }

            detailed['policies'].append(policy_data)

            if status['status'] == 'active':
                detailed['active_policies'] += 1
            elif status['status'] == 'warning':
                detailed['warning_policies'] += 1
            elif status['status'] == 'error':
                detailed['error_policies'] += 1

        return detailed

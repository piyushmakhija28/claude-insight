"""
Policy Checker
Checks status of all policies in Claude Memory System
"""

import os
import json
import subprocess
from pathlib import Path
import sys

# Add path resolver for portable paths
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from utils.path_resolver import get_data_dir, get_logs_dir

class PolicyChecker:
    def __init__(self):
        self.memory_dir = get_data_dir()
        # Import MemorySystemMonitor for daemon checks
        from services.monitoring.memory_system_monitor import MemorySystemMonitor
        self.memory_monitor = MemorySystemMonitor()

        # 3-Level Architecture Policies (v3.2.0) - Auto-generated
        self.policies = [
            {
                'id': 'auto-fix-enforcement',
                'name': 'Auto-Fix Enforcement',
                'description': 'Zero-Tolerance blocking enforcement - checks all systems',
                'files': ['auto-fix-enforcer.sh', 'blocking-policy-enforcer.py'],
                'phase': -1,
                'level': 'LEVEL -1'
            },
            {
                'id': 'prompt-generation',
                'name': 'Prompt Generation',
                'description': 'Anti-hallucination verified prompt generation (Step 0)',
                'files': ['03-execution-system/00-prompt-generation/prompt-generator.py'],
                'phase': 0,
                'level': 'LEVEL 3'
            },
            {
                'id': 'context-management',
                'name': 'Context Management',
                'description': 'Proactive context optimization (-30 to -50% usage)',
                'files': ['01-sync-system/context-management/context-monitor-v2.py'],
                'phase': 1,
                'level': 'LEVEL 1'
            },
            {
                'id': 'session-management',
                'name': 'Session Management',
                'description': 'Session ID tracking and state management',
                'files': ['session-id-generator.py'],
                'phase': 1,
                'level': 'LEVEL 1'
            },
            {
                'id': 'task-breakdown',
                'name': 'Task Breakdown',
                'description': 'Automatic task and phase breakdown (Step 1)',
                'files': ['03-execution-system/01-task-breakdown/task-auto-analyzer.py'],
                'phase': 1,
                'level': 'LEVEL 3'
            },
            {
                'id': 'standards-loader',
                'name': 'Standards Loader',
                'description': '13 coding standards with 77+ rules enforcement',
                'files': ['02-standards-system/standards-loader.py'],
                'phase': 2,
                'level': 'LEVEL 2'
            },
            {
                'id': 'plan-mode-suggestion',
                'name': 'Plan Mode Suggestion',
                'description': 'Auto plan mode detection based on complexity (Step 2)',
                'files': ['03-execution-system/02-plan-mode/auto-plan-mode-suggester.py'],
                'phase': 2,
                'level': 'LEVEL 3'
            },
            {
                'id': 'daemon-infrastructure',
                'name': 'Daemon Infrastructure',
                'description': 'Cross-platform daemon management (10 core daemons)',
                'files': ['utilities/daemon-manager.py', 'utilities/pid-tracker.py'],
                'phase': 2,
                'level': 'Infrastructure'
            },
            {
                'id': 'model-selection',
                'name': 'Model Selection',
                'description': 'Intelligent model selection - Haiku/Sonnet/Opus (Step 4)',
                'files': ['03-execution-system/04-model-selection/model-auto-selector.py'],
                'phase': 4,
                'level': 'LEVEL 3'
            },
            {
                'id': 'skill-agent-selection',
                'name': 'Skill & Agent Selection',
                'description': 'Auto skill and agent recommendation (Step 5)',
                'files': ['03-execution-system/05-skill-agent-selection/auto-skill-agent-selector.py'],
                'phase': 5,
                'level': 'LEVEL 3'
            },
            {
                'id': 'tool-optimization',
                'name': 'Tool Optimization',
                'description': 'Tool usage optimization - offset/limit/head_limit (Step 6)',
                'files': ['03-execution-system/06-tool-optimization/pre-execution-optimizer.py'],
                'phase': 6,
                'level': 'LEVEL 3'
            },
            {
                'id': 'failure-prevention',
                'name': 'Failure Prevention',
                'description': 'Pre-execution checks and auto-fixes (Step 7)',
                'files': ['03-execution-system/failure-prevention/pre-execution-checker.py'],
                'phase': 7,
                'level': 'LEVEL 3'
            },
            {
                'id': 'parallel-execution',
                'name': 'Parallel Execution',
                'description': 'Auto-detect parallel task execution opportunities (Step 8)',
                'files': ['scripts/auto-parallel-detector.py'],
                'phase': 8,
                'level': 'LEVEL 3'
            },
            {
                'id': 'git-auto-commit',
                'name': 'Git Auto-Commit',
                'description': 'Auto-commit on phase completion (Step 11)',
                'files': ['03-execution-system/09-git-commit/auto-commit-enforcer.py'],
                'phase': 11,
                'level': 'LEVEL 3'
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
            # Use MemorySystemMonitor directly instead of subprocess
            daemon_status = self.memory_monitor.get_daemon_status()
            running = len([d for d in daemon_status if d.get('status') == 'running'])
            total = len(daemon_status)
            return {'running': running, 'total': total}
        except Exception as e:
            print(f"Error checking daemons: {e}")
            return {'running': 0, 'total': 10}

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

        # Get policy hits from log
        policy_hits = self._count_policy_hits()

        for policy in self.policies:
            status = self._check_policy_status(policy)

            # Get hits for this policy
            hits = policy_hits.get(policy['id'], 0)

            policy_data = {
                'id': policy['id'],
                'name': policy['name'],
                'description': policy['description'],
                'phase': f"Phase {policy['phase']}",
                'status': status['status'],
                'details': status['details'],
                'files': policy['files'],
                'hits': hits  # Add hits count
            }

            detailed['policies'].append(policy_data)

            if status['status'] == 'active':
                detailed['active_policies'] += 1
            elif status['status'] == 'warning':
                detailed['warning_policies'] += 1
            elif status['status'] == 'error':
                detailed['error_policies'] += 1

        return detailed

    def _count_policy_hits(self):
        """Count policy hits from policy-hits.log"""
        hits = {}
        policy_log = self.memory_dir / 'logs' / 'policy-hits.log'

        try:
            if not policy_log.exists():
                return hits

            with open(policy_log, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue

                    # Parse line format: [timestamp] policy-name | action | context
                    try:
                        if '[' in line and ']' in line:
                            # Extract policy name (between ] and first |)
                            rest = line.split(']', 1)[1].strip()
                            policy_name = rest.split('|')[0].strip()

                            # Map daemon names to policy IDs
                            policy_id = self._map_daemon_to_policy_id(policy_name)
                            if policy_id:
                                hits[policy_id] = hits.get(policy_id, 0) + 1
                    except:
                        continue
        except Exception as e:
            print(f"Error counting policy hits: {e}")

        return hits

    def _map_daemon_to_policy_id(self, daemon_name):
        """Map daemon/script name to policy ID"""
        daemon_name_lower = daemon_name.lower()

        # Map common daemon names to policy IDs
        mappings = {
            'commit': 'git-auto-commit',
            'session': 'session-management',
            'context': 'context-management',
            'task': 'task-breakdown',
            'prompt': 'prompt-generation',
            'model': 'model-selection',
            'skill': 'skill-agent-selection',
            'agent': 'skill-agent-selection',
            'tool': 'tool-optimization',
            'plan': 'plan-mode-suggestion',
            'daemon': 'daemon-infrastructure',
            'parallel': 'parallel-execution',
            'failure': 'failure-prevention',
            'standards': 'standards-loader',
            'auto-fix': 'auto-fix-enforcement'
        }

        for key, policy_id in mappings.items():
            if key in daemon_name_lower:
                return policy_id

        return None

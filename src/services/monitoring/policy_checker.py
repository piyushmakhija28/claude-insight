"""
Policy Checker
Checks status of all policies in Claude Memory System
"""

import json
import subprocess
from pathlib import Path
import sys

# Add path resolver for portable paths
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from utils.path_resolver import get_data_dir

class PolicyChecker:
    def __init__(self):
        self.memory_dir = get_data_dir()

        # 3-Level Architecture Policies (v3.3.1) - 16 policies (1 + 2 + 1 + 12 steps)
        # File references: hook scripts for Level -1/1, policy .md for CLAUDE.md-enforced policies
        self.policies = [
            # LEVEL -1: Auto-Fix Enforcement (1 policy)
            {
                'id': 'auto-fix-enforcement',
                'name': 'Auto-Fix Enforcement',
                'description': 'Zero-Tolerance blocking enforcement - checks all systems before every request',
                'files': ['current/blocking-policy-enforcer.py', 'current/auto-fix-enforcer.sh'],
                'phase': -1,
                'level': 'LEVEL -1'
            },

            # LEVEL 1: Sync System - Foundation (2 policies)
            {
                'id': 'context-management',
                'name': 'Context Management',
                'description': 'Proactive context optimization - monitors usage and applies optimizations',
                'files': ['current/context-monitor-v2.py'],
                'phase': 1,
                'level': 'LEVEL 1'
            },
            {
                'id': 'session-management',
                'name': 'Session Management',
                'description': 'Session ID tracking, state persistence, and clear-session handling',
                'files': ['current/session-id-generator.py', 'current/clear-session-handler.py'],
                'phase': 1,
                'level': 'LEVEL 1'
            },

            # LEVEL 2: Standards System - Middle Layer (1 policy)
            {
                'id': 'coding-standards',
                'name': 'Coding Standards',
                'description': '14 coding standards with 89+ rules - Java, Spring Boot, API, DB, Security',
                'files': ['02-standards-system/coding-standards-enforcement-policy.md'],
                'phase': 2,
                'level': 'LEVEL 2'
            },

            # LEVEL 3: Execution System - 12 Steps (12 policies)
            {
                'id': 'prompt-generation',
                'name': 'Prompt Generation',
                'description': 'Anti-hallucination verified prompt generation (Step 3.0)',
                'files': ['03-execution-system/00-prompt-generation/prompt-generation-policy.md'],
                'phase': 0,
                'level': 'LEVEL 3'
            },
            {
                'id': 'task-breakdown',
                'name': 'Task Breakdown',
                'description': 'Automatic task and phase breakdown with dependency chains (Step 3.1)',
                'files': ['03-execution-system/01-task-breakdown/automatic-task-breakdown-policy.md'],
                'phase': 1,
                'level': 'LEVEL 3'
            },
            {
                'id': 'plan-mode-suggestion',
                'name': 'Plan Mode Suggestion',
                'description': 'Auto plan mode detection based on complexity score (Step 3.2)',
                'files': ['03-execution-system/02-plan-mode/auto-plan-mode-suggestion-policy.md'],
                'phase': 2,
                'level': 'LEVEL 3'
            },
            {
                'id': 'context-recheck',
                'name': 'Context Re-Check',
                'description': 'Re-verify context usage before execution begins (Step 3.3)',
                'files': ['current/context-monitor-v2.py'],
                'phase': 3,
                'level': 'LEVEL 3'
            },
            {
                'id': 'model-selection',
                'name': 'Model Selection',
                'description': 'Intelligent Haiku/Sonnet/Opus selection - hardcoded in CLAUDE.md (Step 3.4)',
                'files': ['03-execution-system/04-model-selection/model-selection-enforcement.md'],
                'phase': 4,
                'level': 'LEVEL 3'
            },
            {
                'id': 'skill-agent-selection',
                'name': 'Skill & Agent Selection',
                'description': '21 skills + 12 agents selection - hardcoded in CLAUDE.md (Step 3.5)',
                'files': ['03-execution-system/05-skill-agent-selection/core-skills-mandate.md'],
                'phase': 5,
                'level': 'LEVEL 3'
            },
            {
                'id': 'tool-optimization',
                'name': 'Tool Optimization',
                'description': 'Tool usage rules: offset/limit/head_limit - hardcoded in CLAUDE.md (Step 3.6)',
                'files': ['03-execution-system/06-tool-optimization/tool-usage-optimization-policy.md'],
                'phase': 6,
                'level': 'LEVEL 3'
            },
            {
                'id': 'failure-prevention',
                'name': 'Failure Prevention',
                'description': 'Pre-execution checks, auto-fixes, and failure knowledge base (Step 3.7)',
                'files': ['03-execution-system/failure-prevention/pre-execution-checker.py'],
                'phase': 7,
                'level': 'LEVEL 3'
            },
            {
                'id': 'parallel-execution',
                'name': 'Parallel Execution',
                'description': 'Auto-detect and launch parallel task execution opportunities (Step 3.8)',
                'files': ['scripts/auto-parallel-detector.py'],
                'phase': 8,
                'level': 'LEVEL 3'
            },
            {
                'id': 'session-save',
                'name': 'Session Save',
                'description': 'Auto-save session state on milestones and task completion (Step 3.10)',
                'files': ['current/session-logger.py', 'current/stop-notifier.py'],
                'phase': 10,
                'level': 'LEVEL 3'
            },
            {
                'id': 'git-auto-commit',
                'name': 'Git Auto-Commit',
                'description': 'Auto-commit on phase completion - hardcoded in CLAUDE.md (Step 3.11)',
                'files': ['03-execution-system/09-git-commit/git-auto-commit-policy.md'],
                'phase': 11,
                'level': 'LEVEL 3'
            },
            {
                'id': 'logging',
                'name': 'Logging',
                'description': 'Log all policy applications, session events, and tool usage (Step 3.12)',
                'files': ['current/session-logger.py'],
                'phase': 12,
                'level': 'LEVEL 3'
            }
        ]

    def get_all_policies(self):
        """Return the list of policy definitions (id, name, description, level)"""
        return self.policies

    def check_policy_status(self, policy_id):
        """Check status of a policy by its id string"""
        for policy in self.policies:
            if policy['id'] == policy_id:
                result = self._check_policy_status(policy)
                return {
                    'id': policy_id,
                    'exists': result['status'] != 'error',
                    'status': result['status'],
                    'details': result['details']
                }
        return {'id': policy_id, 'exists': False, 'status': 'unknown', 'details': 'Policy not found'}

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
        if policy['id'] == 'logging':
            log_file = self.memory_dir / 'logs' / 'policy-hits.log'
            if log_file.exists():
                lines = log_file.read_text(encoding='utf-8', errors='ignore').splitlines()
                return {
                    'status': 'active',
                    'details': f"{len(lines)} policy events logged"
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

    def _get_kb_stats(self):
        """Get failure KB stats"""
        try:
            result = subprocess.run(
                ['python', str(self.memory_dir / '03-execution-system' / 'failure-prevention' / 'pre-execution-checker.py'), '--stats'],
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
        """Get model usage stats from log file directly"""
        try:
            model_log = self.memory_dir / 'logs' / 'model-usage.log'
            if model_log.exists():
                lines = model_log.read_text(encoding='utf-8', errors='ignore').splitlines()
                return {'requests': len(lines)}
        except Exception as e:
            print(f"Error reading model log: {e}")

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
                'phase_num': policy['phase'],  # Add numeric phase for sorting
                'level': policy['level'],  # Add level for grouping
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

        # Map log entry names to policy IDs
        mappings = {
            'commit': 'git-auto-commit',
            'session-save': 'session-save',
            'session': 'session-management',
            'context-recheck': 'context-recheck',
            'context': 'context-management',
            'task': 'task-breakdown',
            'prompt': 'prompt-generation',
            'model': 'model-selection',
            'skill': 'skill-agent-selection',
            'agent': 'skill-agent-selection',
            'tool': 'tool-optimization',
            'plan': 'plan-mode-suggestion',
            'parallel': 'parallel-execution',
            'failure': 'failure-prevention',
            'standards': 'coding-standards',
            'logging': 'logging',
            'logger': 'logging',
            'auto-fix': 'auto-fix-enforcement'
        }

        for key, policy_id in mappings.items():
            if key in daemon_name_lower:
                return policy_id

        return None

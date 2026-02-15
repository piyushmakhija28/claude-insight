"""
Memory System Integration Monitor
Monitors all Claude Memory System v2.2.0 components, policies, and automation
"""
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict


class MemorySystemMonitor:
    """Monitor Claude Memory System v2.2.0 health, policies, and automation"""

    def __init__(self):
        self.memory_dir = Path.home() / '.claude' / 'memory'
        self.logs_dir = self.memory_dir / 'logs'
        self.sessions_dir = self.memory_dir / 'sessions'

        # Daemon tracking
        self.daemons = [
            'context-daemon',
            'session-auto-save-daemon',
            'preference-tracker-daemon',
            'skill-suggester-daemon',
            'git-auto-commit-daemon',
            'session-pruning-daemon',
            'pattern-detection-daemon',
            'failure-prevention-daemon'
        ]

    def get_daemon_status(self):
        """Get status of all 8 memory system daemons"""
        pids_dir = self.memory_dir / '.pids'
        statuses = []

        for daemon in self.daemons:
            pid_file = pids_dir / f'{daemon}.pid'
            status = {
                'name': daemon,
                'status': 'unknown',
                'pid': None,
                'last_activity': None
            }

            if pid_file.exists():
                try:
                    pid = int(pid_file.read_text().strip())
                    # Check if process is actually running
                    if self._is_process_running(pid):
                        status['status'] = 'running'
                        status['pid'] = pid
                    else:
                        status['status'] = 'stopped'
                except Exception:
                    status['status'] = 'error'
            else:
                status['status'] = 'not_started'

            # Check last activity from logs
            log_file = self.logs_dir / f'{daemon}.log'
            if log_file.exists():
                try:
                    lines = log_file.read_text().splitlines()
                    if lines:
                        # Get last log line timestamp
                        last_line = lines[-1]
                        if '[' in last_line:
                            timestamp_str = last_line.split('[')[1].split(']')[0]
                            status['last_activity'] = timestamp_str
                except Exception:
                    pass

            statuses.append(status)

        return statuses

    def _is_process_running(self, pid):
        """Check if process is running (cross-platform)"""
        try:
            import psutil
            return psutil.pid_exists(pid)
        except ImportError:
            # Fallback for systems without psutil
            try:
                os.kill(pid, 0)
                return True
            except OSError:
                return False

    def get_policy_enforcement_stats(self):
        """Get policy enforcement statistics from policy-hits.log"""
        policy_hits_file = self.logs_dir / 'policy-hits.log'

        if not policy_hits_file.exists():
            return {'total_enforcements': 0, 'by_policy': {}, 'recent_activity': []}

        try:
            lines = policy_hits_file.read_text().splitlines()

            by_policy = defaultdict(int)
            recent_activity = []

            for line in lines[-100:]:  # Last 100 entries
                if '|' in line:
                    parts = line.split('|')
                    if len(parts) >= 2:
                        policy_name = parts[1].strip()
                        by_policy[policy_name] += 1

                        if len(recent_activity) < 10:
                            recent_activity.append({
                                'timestamp': parts[0].strip() if len(parts) > 0 else '',
                                'policy': policy_name,
                                'action': parts[2].strip() if len(parts) > 2 else ''
                            })

            return {
                'total_enforcements': len(lines),
                'by_policy': dict(by_policy),
                'recent_activity': recent_activity
            }
        except Exception as e:
            print(f"Error reading policy hits: {e}")
            return {'total_enforcements': 0, 'by_policy': {}, 'recent_activity': []}

    def get_context_optimization_stats(self):
        """Get context optimization and cache statistics"""
        cache_dir = self.memory_dir / '.cache'

        stats = {
            'cache_size': 0,
            'cached_files': 0,
            'cache_hits': 0,
            'token_savings': 0,
            'optimizations_applied': 0
        }

        if cache_dir.exists():
            try:
                cached_files = list(cache_dir.glob('*.json'))
                stats['cached_files'] = len(cached_files)

                # Calculate total cache size
                total_size = sum(f.stat().st_size for f in cached_files)
                stats['cache_size'] = total_size

                # Read cache hits from log
                cache_log = self.logs_dir / 'context-cache.log'
                if cache_log.exists():
                    lines = cache_log.read_text().splitlines()
                    stats['cache_hits'] = len([l for l in lines if 'CACHE HIT' in l])
                    stats['token_savings'] = stats['cache_hits'] * 500  # Estimated
            except Exception as e:
                print(f"Error reading cache stats: {e}")

        # Read optimization log
        opt_log = self.logs_dir / 'optimizations.log'
        if opt_log.exists():
            try:
                lines = opt_log.read_text().splitlines()
                stats['optimizations_applied'] = len(lines)
            except Exception:
                pass

        return stats

    def get_failure_prevention_stats(self):
        """Get failure prevention statistics"""
        failures_file = self.memory_dir / 'failures.log'
        kb_file = self.memory_dir / 'failure-kb.json'

        stats = {
            'failures_prevented': 0,
            'auto_fixes_applied': 0,
            'patterns_learned': 0,
            'by_tool': {},
            'recent_fixes': []
        }

        # Read failures log
        if failures_file.exists():
            try:
                lines = failures_file.read_text().splitlines()
                stats['failures_prevented'] = len(lines)

                by_tool = defaultdict(int)
                for line in lines[-50:]:
                    if 'FIXED' in line:
                        stats['auto_fixes_applied'] += 1
                        if 'Bash:' in line:
                            by_tool['Bash'] += 1
                        elif 'Edit:' in line:
                            by_tool['Edit'] += 1
                        elif 'Read:' in line:
                            by_tool['Read'] += 1
                        elif 'Grep:' in line:
                            by_tool['Grep'] += 1

                stats['by_tool'] = dict(by_tool)
            except Exception as e:
                print(f"Error reading failures log: {e}")

        # Read KB
        if kb_file.exists():
            try:
                kb_data = json.loads(kb_file.read_text())
                for tool, patterns in kb_data.items():
                    if isinstance(patterns, list):
                        stats['patterns_learned'] += len(patterns)
            except Exception:
                pass

        return stats

    def get_model_selection_distribution(self):
        """Get model selection distribution stats"""
        model_log = self.logs_dir / 'model-usage.log'

        stats = {
            'total_requests': 0,
            'haiku': 0,
            'sonnet': 0,
            'opus': 0,
            'haiku_percent': 0,
            'sonnet_percent': 0,
            'opus_percent': 0
        }

        if model_log.exists():
            try:
                lines = model_log.read_text().splitlines()
                stats['total_requests'] = len(lines)

                for line in lines:
                    if 'haiku' in line.lower():
                        stats['haiku'] += 1
                    elif 'sonnet' in line.lower():
                        stats['sonnet'] += 1
                    elif 'opus' in line.lower():
                        stats['opus'] += 1

                if stats['total_requests'] > 0:
                    stats['haiku_percent'] = (stats['haiku'] / stats['total_requests']) * 100
                    stats['sonnet_percent'] = (stats['sonnet'] / stats['total_requests']) * 100
                    stats['opus_percent'] = (stats['opus'] / stats['total_requests']) * 100
            except Exception as e:
                print(f"Error reading model usage: {e}")

        return stats

    def get_session_memory_stats(self):
        """Get session memory statistics"""
        stats = {
            'total_sessions': 0,
            'active_sessions': 0,
            'pruned_sessions': 0,
            'total_size_mb': 0
        }

        if self.sessions_dir.exists():
            try:
                session_dirs = [d for d in self.sessions_dir.iterdir() if d.is_dir()]
                stats['total_sessions'] = len(session_dirs)

                total_size = 0
                for session_dir in session_dirs:
                    # Check if session is active (modified in last 7 days)
                    summary_file = session_dir / 'project-summary.md'
                    if summary_file.exists():
                        mtime = datetime.fromtimestamp(summary_file.stat().st_mtime)
                        if datetime.now() - mtime < timedelta(days=7):
                            stats['active_sessions'] += 1

                    # Calculate size
                    for file in session_dir.rglob('*'):
                        if file.is_file():
                            total_size += file.stat().st_size

                stats['total_size_mb'] = round(total_size / (1024 * 1024), 2)
            except Exception as e:
                print(f"Error reading session stats: {e}")

        # Check pruning log
        prune_log = self.logs_dir / 'session-pruning.log'
        if prune_log.exists():
            try:
                lines = prune_log.read_text().splitlines()
                stats['pruned_sessions'] = len([l for l in lines if 'PRUNED' in l])
            except Exception:
                pass

        return stats

    def get_git_autocommit_stats(self):
        """Get git auto-commit statistics"""
        git_log = self.logs_dir / 'git-auto-commit.log'

        stats = {
            'total_commits': 0,
            'commits_today': 0,
            'commits_this_week': 0,
            'recent_commits': []
        }

        if git_log.exists():
            try:
                lines = git_log.read_text().splitlines()
                stats['total_commits'] = len([l for l in lines if 'COMMIT' in l])

                now = datetime.now()
                today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
                week_start = now - timedelta(days=7)

                for line in lines:
                    if '[' in line and ']' in line:
                        try:
                            timestamp_str = line.split('[')[1].split(']')[0]
                            timestamp = datetime.fromisoformat(timestamp_str)

                            if timestamp >= today_start:
                                stats['commits_today'] += 1
                            if timestamp >= week_start:
                                stats['commits_this_week'] += 1
                        except Exception:
                            pass

                # Get recent commits
                for line in lines[-10:]:
                    if 'COMMIT' in line:
                        stats['recent_commits'].append(line)
            except Exception as e:
                print(f"Error reading git log: {e}")

        return stats

    def get_system_health_score(self):
        """Calculate overall memory system health score"""
        daemon_statuses = self.get_daemon_status()
        running_daemons = len([d for d in daemon_statuses if d['status'] == 'running'])

        # Components scoring
        daemon_score = (running_daemons / len(self.daemons)) * 40  # 40% weight

        # Check if critical daemons are running
        critical_daemons = ['context-daemon', 'failure-prevention-daemon']
        critical_running = len([d for d in daemon_statuses if d['name'] in critical_daemons and d['status'] == 'running'])
        critical_score = (critical_running / len(critical_daemons)) * 30  # 30% weight

        # Check policy enforcement (if active in last hour)
        policy_stats = self.get_policy_enforcement_stats()
        policy_score = 20 if policy_stats['total_enforcements'] > 0 else 0  # 20% weight

        # Check cache effectiveness
        cache_stats = self.get_context_optimization_stats()
        cache_score = 10 if cache_stats['cached_files'] > 0 else 0  # 10% weight

        total_score = daemon_score + critical_score + policy_score + cache_score

        return {
            'overall_score': round(total_score, 1),
            'daemon_health': round(daemon_score, 1),
            'critical_health': round(critical_score, 1),
            'policy_activity': round(policy_score, 1),
            'cache_efficiency': round(cache_score, 1),
            'status': 'healthy' if total_score >= 80 else 'degraded' if total_score >= 60 else 'critical'
        }

    def get_comprehensive_stats(self):
        """Get all memory system statistics in one call"""
        return {
            'system_health': self.get_system_health_score(),
            'daemons': self.get_daemon_status(),
            'policies': self.get_policy_enforcement_stats(),
            'context_optimization': self.get_context_optimization_stats(),
            'failure_prevention': self.get_failure_prevention_stats(),
            'model_selection': self.get_model_selection_distribution(),
            'session_memory': self.get_session_memory_stats(),
            'git_autocommit': self.get_git_autocommit_stats(),
            'timestamp': datetime.now().isoformat()
        }

    def get_policy_status(self):
        """Get status of all 10 policies"""
        policies = [
            {'name': 'Core Skills Mandate', 'file': 'core-skills-mandate.md', 'status': 'active'},
            {'name': 'Model Selection', 'file': 'model-selection-enforcement.md', 'status': 'active'},
            {'name': 'Proactive Consultation', 'file': 'proactive-consultation-policy.md', 'status': 'active'},
            {'name': 'Session Memory', 'file': 'session-memory-policy.md', 'status': 'active'},
            {'name': 'Failure Prevention', 'file': 'common-failures-prevention.md', 'status': 'active'},
            {'name': 'File Management', 'file': 'file-management-policy.md', 'status': 'active'},
            {'name': 'Git Auto-Commit', 'file': 'git-auto-commit-policy.md', 'status': 'active'},
            {'name': 'User Preferences', 'file': 'user-preferences-policy.md', 'status': 'active'},
            {'name': 'Session Pruning', 'file': 'session-pruning-policy.md', 'status': 'active'},
            {'name': 'Context Integration', 'file': 'CONTEXT-SESSION-INTEGRATION.md', 'status': 'active'}
        ]

        # Check if policy files exist
        for policy in policies:
            policy_file = self.memory_dir / policy['file']
            policy['exists'] = policy_file.exists()
            policy['active'] = policy['exists'] and policy['status'] == 'active'

        return policies

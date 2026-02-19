"""
Log Parser
Parses and analyzes log files from Claude Memory System.
Supports policy-hits.log, daemon logs, and 3-level flow session logs.
"""

import os
from pathlib import Path
import sys

# Add path resolver for portable paths
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from utils.path_resolver import get_data_dir, get_logs_dir
from datetime import datetime, timedelta, timezone
import re

class LogParser:
    def __init__(self):
        self.memory_dir = get_data_dir()
        self.logs_dir = self.memory_dir / 'logs'

    def get_available_logs(self):
        """Get list of available log files"""
        log_files = []

        if self.logs_dir.exists():
            for log_file in self.logs_dir.glob('*.log'):
                size = log_file.stat().st_size
                modified = datetime.fromtimestamp(log_file.stat().st_mtime)

                log_files.append({
                    'name': log_file.name,
                    'path': str(log_file),
                    'size': self._format_size(size),
                    'modified': modified.strftime('%Y-%m-%d %H:%M:%S')
                })

        return sorted(log_files, key=lambda x: x['name'])

    def _format_size(self, size):
        """Format file size"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

    def _map_action_to_type(self, action):
        """Map action to activity type for dashboard display"""
        action_upper = action.upper()

        # Error types
        if any(keyword in action_upper for keyword in ['ERROR', 'FAILED', 'FAIL']):
            return 'error'

        # Warning types
        if any(keyword in action_upper for keyword in ['WARNING', 'WARN']):
            return 'warning'

        # Success types
        if any(keyword in action_upper for keyword in ['SUCCESS', 'COMPLETE', 'OK', 'PASSED']):
            return 'success'

        # Info types (default)
        return 'info'

    def get_recent_activity(self, limit=10):
        """Get recent activity from policy hits log"""
        activities = []

        policy_log = self.logs_dir / 'policy-hits.log'

        if policy_log.exists():
            try:
                with open(policy_log, 'r', encoding='utf-8') as f:
                    lines = f.readlines()

                # Get last N lines
                for line in lines[-limit:]:
                    line = line.strip()
                    if line:
                        # Parse log line: [timestamp] daemon-name | action | context
                        # Updated regex to match hyphens in daemon names
                        match = re.match(r'\[(.*?)\]\s+([\w-]+)\s+\|\s+(.*?)\s+\|\s+(.*)', line)
                        if match:
                            timestamp, policy, action, context = match.groups()

                            # Map to format expected by dashboard JavaScript
                            # type = action type (for color/icon), message = formatted message
                            activity_type = self._map_action_to_type(action)
                            message = f"{policy}: {action} - {context[:80]}"

                            activities.append({
                                'timestamp': timestamp,
                                'type': activity_type,
                                'message': message,
                                'policy': policy,
                                'action': action,
                                'context': context[:100]
                            })
                        else:
                            # Fallback parsing
                            activities.append({
                                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                'type': 'info',
                                'message': line[:80],
                                'policy': 'SYSTEM',
                                'action': 'Activity',
                                'context': line[:100]
                            })
            except Exception as e:
                print(f"Error reading policy log: {e}")

        return list(reversed(activities))  # Most recent first

    def get_error_count(self, hours=24):
        """Get error count in last N hours"""
        error_count = 0
        cutoff_time = datetime.now() - timedelta(hours=hours)

        if self.logs_dir.exists():
            for log_file in self.logs_dir.glob('*.log'):
                try:
                    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                        for line in f:
                            if 'ERROR' in line or 'CRITICAL' in line or 'FAIL' in line:
                                # Try to extract timestamp
                                match = re.search(r'\[(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\]', line)
                                if match:
                                    try:
                                        log_time = datetime.strptime(match.group(1), '%Y-%m-%d %H:%M:%S')
                                        if log_time >= cutoff_time:
                                            error_count += 1
                                    except:
                                        pass
                                else:
                                    # No timestamp, count it anyway
                                    error_count += 1
                except Exception as e:
                    print(f"Error reading {log_file}: {e}")

        return error_count

    def get_recent_errors(self, limit=5):
        """Get recent error log entries"""
        errors = []
        cutoff_time = datetime.now() - timedelta(hours=24)

        if self.logs_dir.exists():
            for log_file in self.logs_dir.glob('*.log'):
                try:
                    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                        for line in f:
                            if 'ERROR' in line or 'CRITICAL' in line or 'FAIL' in line:
                                # Extract timestamp
                                timestamp_match = re.search(r'\[(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\]', line)
                                timestamp = timestamp_match.group(1) if timestamp_match else datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                                # Extract error level
                                level = 'ERROR'
                                if 'CRITICAL' in line:
                                    level = 'CRITICAL'
                                elif 'FAIL' in line:
                                    level = 'FAILED'

                                # Clean message
                                message = line.strip()
                                if len(message) > 200:
                                    message = message[:200] + '...'

                                errors.append({
                                    'timestamp': timestamp,
                                    'level': level,
                                    'message': message,
                                    'source': log_file.name
                                })
                except Exception as e:
                    print(f"Error reading {log_file}: {e}")

        # Sort by timestamp (most recent first) and limit
        errors.sort(key=lambda x: x['timestamp'], reverse=True)
        return errors[:limit]

    def analyze_log_file(self, log_file_name, search_term='', log_level='all'):
        """Analyze a specific log file"""
        results = {
            'lines': [],
            'total_lines': 0,
            'error_count': 0,
            'warning_count': 0,
            'info_count': 0
        }

        log_file = self.logs_dir / log_file_name

        if not log_file.exists():
            return results

        try:
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()

            results['total_lines'] = len(lines)

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # Count by level
                if 'ERROR' in line or 'CRITICAL' in line:
                    results['error_count'] += 1
                elif 'WARNING' in line or 'WARN' in line:
                    results['warning_count'] += 1
                elif 'INFO' in line:
                    results['info_count'] += 1

                # Filter by search term
                if search_term and search_term.lower() not in line.lower():
                    continue

                # Filter by log level
                if log_level != 'all':
                    if log_level == 'error' and not ('ERROR' in line or 'CRITICAL' in line):
                        continue
                    elif log_level == 'warning' and not ('WARNING' in line or 'WARN' in line):
                        continue
                    elif log_level == 'info' and 'INFO' not in line:
                        continue

                # Extract log level
                level = 'INFO'
                if 'ERROR' in line or 'CRITICAL' in line:
                    level = 'ERROR'
                elif 'WARNING' in line or 'WARN' in line:
                    level = 'WARNING'

                results['lines'].append({
                    'content': line,
                    'level': level
                })

        except Exception as e:
            print(f"Error analyzing log file: {e}")

        # Limit results to last 1000 lines
        if len(results['lines']) > 1000:
            results['lines'] = results['lines'][-1000:]

        return results

    def get_policy_history(self, days=7):
        """
        Get policy execution history counts from flow-trace.json files.
        Counts sessions within the last N days for each policy category:
        - context_optimization: sessions where context >= 70% (optimization applied)
        - failure_prevention: sessions where Level -1 auto-fix enforcement passed
        - model_selection: all sessions (model always selected)
        - consultation: sessions where plan_mode was triggered
        """
        counts = {
            'context_optimization': 0,
            'failure_prevention': 0,
            'model_selection': 0,
            'consultation': 0
        }

        sessions_dir = Path.home() / '.claude' / 'memory' / 'logs' / 'sessions'
        if not sessions_dir.exists():
            return counts

        cutoff = datetime.now() - timedelta(days=days)

        try:
            import json as _json
            trace_files = sessions_dir.glob('*/flow-trace.json')
            for tf in trace_files:
                try:
                    # Quick mtime check before parsing
                    if datetime.fromtimestamp(tf.stat().st_mtime) < cutoff:
                        continue

                    data = _json.loads(tf.read_text(encoding='utf-8', errors='ignore'))
                    fd = data.get('final_decision', {})

                    # model_selection: always (every session selects a model)
                    if fd.get('model_selected'):
                        counts['model_selection'] += 1

                    # failure_prevention: Level -1 ran (auto-fix enforcement)
                    for step in data.get('pipeline', []):
                        if step.get('step') == 'LEVEL_MINUS_1':
                            counts['failure_prevention'] += 1
                            break

                    # context_optimization: context >= 70% triggered optimization
                    ctx_pct = fd.get('context_pct', 0)
                    if ctx_pct >= 70:
                        counts['context_optimization'] += 1

                    # consultation: plan_mode was triggered
                    if fd.get('plan_mode', False):
                        counts['consultation'] += 1

                except Exception:
                    continue

        except Exception as e:
            print(f"Error reading policy history from flow-traces: {e}")

        return counts

    # -------------------------------------------------------------------------
    # 3-Level Flow Session Log Parsing
    # -------------------------------------------------------------------------

    def get_3level_sessions_dir(self):
        """Return path to 3-level flow session log directory"""
        return Path.home() / '.claude' / 'memory' / 'logs' / 'sessions'

    def list_3level_sessions(self, limit=20):
        """List available session log directories (most recent first)"""
        sessions_dir = self.get_3level_sessions_dir()
        if not sessions_dir.exists():
            return []
        dirs = [d for d in sessions_dir.iterdir() if d.is_dir()]
        dirs.sort(key=lambda d: d.stat().st_mtime, reverse=True)
        result = []
        for d in dirs[:limit]:
            result.append({
                'session_id': d.name,
                'path': str(d),
                'modified': datetime.fromtimestamp(d.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                'files': [f.name for f in sorted(d.glob('*.log'))]
            })
        return result

    def get_3level_session_log(self, session_id, log_name):
        """Read contents of a specific 3-level session log file"""
        sessions_dir = self.get_3level_sessions_dir()
        log_file = sessions_dir / session_id / log_name
        if not log_file.exists():
            return None
        try:
            return log_file.read_text(encoding='utf-8', errors='ignore')
        except Exception as e:
            print(f"Error reading session log {log_file}: {e}")
            return None

    def get_auto_enforcement_log(self, tail_lines=100):
        """Read last N lines from auto-enforcement.log"""
        log_file = Path.home() / '.claude' / 'memory' / 'logs' / 'auto-enforcement.log'
        if not log_file.exists():
            return []
        try:
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            return [line.rstrip() for line in lines[-tail_lines:]]
        except Exception as e:
            print(f"Error reading auto-enforcement log: {e}")
            return []

    def get_3level_flow_summary(self):
        """Return a quick summary of the 3-level flow from the latest session"""
        from services.monitoring.three_level_flow_tracker import ThreeLevelFlowTracker
        tracker = ThreeLevelFlowTracker()
        latest = tracker.get_latest_execution()
        if not latest:
            return {
                'available': False,
                'message': 'No 3-level flow sessions found'
            }
        return {
            'available': True,
            'session_id': latest['session_id'],
            'started': latest.get('started'),
            'user_prompt': latest.get('user_prompt'),
            'overall_status': latest.get('overall_status', 'unknown'),
            'level_minus_1_status': latest['level_minus_1'].get('status', 'unknown'),
            'context_pct': latest['level_1'].get('context_pct'),
            'standards': latest['level_2'].get('standards'),
            'rules': latest['level_2'].get('rules'),
            'complexity': latest['level_3'].get('complexity'),
            'task_type': latest['level_3'].get('task_type'),
            'model': latest['level_3'].get('model'),
            'tasks': latest['level_3'].get('tasks'),
            'duration': latest.get('duration')
        }

    def get_daemon_activity_summary(self, hours=24):
        """Summarize daemon activity from policy-hits.log"""
        policy_log = self.logs_dir / 'policy-hits.log'
        if not policy_log.exists():
            return {}

        cutoff = datetime.now() - timedelta(hours=hours)
        daemon_counts = {}
        action_counts = {}

        try:
            with open(policy_log, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    m = re.match(r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]\s+([\w-]+)\s+\|\s+(\w+)\s+\|', line)
                    if m:
                        try:
                            ts = datetime.strptime(m.group(1), '%Y-%m-%d %H:%M:%S')
                            if ts < cutoff:
                                continue
                        except Exception:
                            pass
                        daemon = m.group(2)
                        action = m.group(3)
                        daemon_counts[daemon] = daemon_counts.get(daemon, 0) + 1
                        action_counts[action] = action_counts.get(action, 0) + 1
        except Exception as e:
            print(f"Error summarizing daemon activity: {e}")

        return {
            'daemon_counts': daemon_counts,
            'action_counts': action_counts,
            'total_entries': sum(daemon_counts.values())
        }

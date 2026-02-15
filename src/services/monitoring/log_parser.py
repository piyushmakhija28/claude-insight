"""
Log Parser
Parses and analyzes log files from Claude Memory System
"""

import os
from pathlib import Path
from datetime import datetime, timedelta
import re

class LogParser:
    def __init__(self):
        self.memory_dir = Path.home() / '.claude' / 'memory'
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
                        # Parse log line: [timestamp] POLICY | action | context
                        match = re.match(r'\[(.*?)\]\s+(\w+)\s+\|\s+(.*?)\s+\|\s+(.*)', line)
                        if match:
                            timestamp, policy, action, context = match.groups()
                            activities.append({
                                'timestamp': timestamp,
                                'policy': policy,
                                'action': action,
                                'context': context[:100]  # Limit context length
                            })
                        else:
                            # Fallback parsing
                            activities.append({
                                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
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
        """Get policy execution history"""
        history = {
            'context_optimization': [],
            'failure_prevention': [],
            'model_selection': [],
            'consultation': []
        }

        policy_log = self.logs_dir / 'policy-hits.log'

        if policy_log.exists():
            try:
                with open(policy_log, 'r', encoding='utf-8') as f:
                    lines = f.readlines()

                cutoff_date = datetime.now() - timedelta(days=days)

                for line in lines:
                    line = line.strip()
                    if not line:
                        continue

                    # Extract timestamp
                    match = re.match(r'\[(.*?)\]', line)
                    if match:
                        try:
                            timestamp = datetime.strptime(match.group(1), '%Y-%m-%d %H:%M:%S')
                            if timestamp < cutoff_date:
                                continue
                        except:
                            pass

                    if 'CONTEXT_OPTIMIZATION' in line:
                        history['context_optimization'].append(line)
                    elif 'FAILURE_PREVENTION' in line:
                        history['failure_prevention'].append(line)
                    elif 'MODEL_SELECTION' in line:
                        history['model_selection'].append(line)
                    elif 'CONSULTATION' in line:
                        history['consultation'].append(line)

            except Exception as e:
                print(f"Error reading policy history: {e}")

        # Return counts for each policy
        return {
            'context_optimization': len(history['context_optimization']),
            'failure_prevention': len(history['failure_prevention']),
            'model_selection': len(history['model_selection']),
            'consultation': len(history['consultation'])
        }

"""
Performance Profiler Service
Tracks and analyzes performance metrics for tool operations
"""

import json
import os
from pathlib import Path
from datetime import datetime, timedelta
from collections import deque
import statistics
from typing import Dict, List, Optional, Any


class PerformanceProfiler:
    """
    Collects, analyzes, and stores performance metrics for all tool operations.
    Identifies bottlenecks and slow operations.
    """

    def __init__(self, storage_dir: str = None):
        """Initialize the performance profiler"""
        if storage_dir is None:
            storage_dir = os.path.expanduser("~/.claude/memory/performance")
            self._is_default_storage = True
        else:
            self._is_default_storage = False

        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        # In-memory buffers for fast access
        self.recent_operations = deque(maxlen=1000)  # Last 1000 operations
        self.slow_operations = deque(maxlen=100)     # Last 100 slow operations
        self.bottleneck_cache = {}                    # Top bottlenecks by tool

        # Performance thresholds (in milliseconds)
        self.SLOW_THRESHOLD = 2000  # 2 seconds
        self.CRITICAL_THRESHOLD = 5000  # 5 seconds

        # Load recent operations from disk
        self._load_recent_operations()

    def _load_recent_operations(self):
        """
        Load recent operations.
        Primary: today's operations_YYYY-MM-DD.json (from track_operation calls)
        Fallback: parse flow-trace.json files from session logs (always available)
        """
        today_file = self.storage_dir / f"operations_{datetime.now().strftime('%Y-%m-%d')}.json"

        if today_file.exists():
            try:
                with open(today_file, 'r') as f:
                    data = json.load(f)
                    operations = data.get('operations', [])
                    for op in operations[-1000:]:
                        self.recent_operations.append(op)
                        if op.get('duration_ms', 0) >= self.SLOW_THRESHOLD:
                            self.slow_operations.append(op)
                if self.recent_operations:
                    return  # Primary source had data, done
            except Exception as e:
                print(f"Error loading recent operations: {e}")

        # Fallback: read from flow-trace.json session logs (only for default storage)
        # 3-level-flow.py writes these for every request with real duration_ms per step
        if self._is_default_storage:
            self._load_from_flow_traces()

    def _load_from_flow_traces(self):
        """
        Parse flow-trace.json files from ~/.claude/memory/logs/sessions/
        Each pipeline step becomes a tracked operation with real timing data.
        """
        try:
            import os
            home = Path(os.path.expanduser('~'))
            sessions_dir = home / '.claude' / 'memory' / 'logs' / 'sessions'

            if not sessions_dir.exists():
                return

            # Collect all flow-trace files, sorted by modification time (newest first)
            trace_files = sorted(
                sessions_dir.glob('*/flow-trace.json'),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )[:50]  # Last 50 sessions max

            seen_count = 0
            for trace_file in trace_files:
                try:
                    with open(trace_file, 'r', encoding='utf-8', errors='replace') as f:
                        trace = json.load(f)

                    session_id = trace.get('meta', {}).get('session_id', 'unknown')
                    pipeline = trace.get('pipeline', [])

                    for step in pipeline:
                        duration_ms = step.get('duration_ms', 0)
                        if duration_ms <= 0:
                            continue  # skip steps with no timing

                        op = {
                            'tool': step.get('step', 'unknown'),
                            'target': step.get('name', ''),
                            'duration_ms': duration_ms,
                            'timestamp': step.get('timestamp', trace.get('meta', {}).get('flow_start', '')),
                            'success': True,
                            'optimization_applied': False,
                            'session_id': session_id,
                            'level': step.get('level', -1)
                        }
                        self.recent_operations.append(op)
                        if duration_ms >= self.SLOW_THRESHOLD:
                            self.slow_operations.append(op)
                        seen_count += 1

                except Exception:
                    continue

        except Exception as e:
            print(f"Error loading flow traces: {e}")

    def track_operation(self, tool: str, target: str, duration_ms: float,
                       metadata: Optional[Dict[str, Any]] = None,
                       success: bool = True,
                       optimization_applied: bool = False):
        """
        Track a tool operation

        Args:
            tool: Tool name (Read, Write, Edit, Grep, Glob, Bash, etc.)
            target: Target file path or command
            duration_ms: Operation duration in milliseconds
            metadata: Additional tool-specific data
            success: Whether operation succeeded
            optimization_applied: Whether optimizations (offset/limit/head_limit) were used
        """
        operation = {
            'tool': tool,
            'target': target,
            'duration_ms': duration_ms,
            'timestamp': datetime.now().isoformat(),
            'success': success,
            'optimization_applied': optimization_applied,
            'metadata': metadata or {}
        }

        # Add file size for file operations
        if tool in ['Read', 'Write', 'Edit'] and os.path.exists(target):
            try:
                operation['size_bytes'] = os.path.getsize(target)
            except:
                operation['size_bytes'] = 0

        # Add to recent operations
        self.recent_operations.append(operation)

        # Add to slow operations if applicable
        if duration_ms >= self.SLOW_THRESHOLD:
            self.slow_operations.append(operation)

        # Update bottleneck cache
        self._update_bottleneck_cache(operation)

        # Persist to disk (async would be better in production)
        self._save_operation(operation)

    def _update_bottleneck_cache(self, operation: Dict):
        """Update the bottleneck cache with this operation"""
        tool = operation['tool']
        duration = operation['duration_ms']

        if tool not in self.bottleneck_cache:
            self.bottleneck_cache[tool] = []

        # Add to tool's bottleneck list
        self.bottleneck_cache[tool].append({
            'target': operation['target'],
            'duration_ms': duration,
            'timestamp': operation['timestamp']
        })

        # Keep only top 10 slowest per tool
        self.bottleneck_cache[tool] = sorted(
            self.bottleneck_cache[tool],
            key=lambda x: x['duration_ms'],
            reverse=True
        )[:10]

    def _save_operation(self, operation: Dict):
        """Save operation to today's file"""
        today_file = self.storage_dir / f"operations_{datetime.now().strftime('%Y-%m-%d')}.json"

        try:
            # Load existing data
            if today_file.exists():
                with open(today_file, 'r') as f:
                    data = json.load(f)
            else:
                data = {'operations': []}

            # Append new operation
            data['operations'].append(operation)

            # Save back
            with open(today_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving operation: {e}")

    def get_slow_operations(self, threshold_ms: int = None, limit: int = 50) -> List[Dict]:
        """
        Get recent slow operations

        Args:
            threshold_ms: Duration threshold (default: SLOW_THRESHOLD)
            limit: Maximum number to return

        Returns:
            List of slow operations, newest first
        """
        if threshold_ms is None:
            threshold_ms = self.SLOW_THRESHOLD

        # Filter operations by threshold
        slow_ops = [
            op for op in self.recent_operations
            if op.get('duration_ms', 0) >= threshold_ms
        ]

        # Sort by timestamp (newest first)
        slow_ops.sort(key=lambda x: x['timestamp'], reverse=True)

        return slow_ops[:limit]

    def get_bottlenecks(self) -> Dict[str, List[Dict]]:
        """
        Get top bottlenecks by tool type

        Returns:
            Dictionary mapping tool names to their top 10 slowest operations
        """
        return self.bottleneck_cache.copy()

    def get_stats_summary(self) -> Dict[str, Any]:
        """
        Get performance statistics summary

        Returns:
            Dictionary with performance statistics
        """
        if not self.recent_operations:
            return {
                'total_operations': 0,
                'avg_duration_ms': 0,
                'median_duration_ms': 0,
                'p95_duration_ms': 0,
                'p99_duration_ms': 0,
                'slow_operations_count': 0,
                'critical_operations_count': 0,
                'tools_breakdown': {},
                'success_rate': 100.0,
                'optimization_rate': 0.0
            }

        # Calculate statistics
        durations = [op['duration_ms'] for op in self.recent_operations]
        successes = [op['success'] for op in self.recent_operations]
        optimizations = [op['optimization_applied'] for op in self.recent_operations]

        # Tools breakdown
        tools_breakdown = {}
        for op in self.recent_operations:
            tool = op['tool']
            tools_breakdown[tool] = tools_breakdown.get(tool, 0) + 1

        # Count slow/critical operations
        slow_count = sum(1 for d in durations if d >= self.SLOW_THRESHOLD)
        critical_count = sum(1 for d in durations if d >= self.CRITICAL_THRESHOLD)

        return {
            'total_operations': len(self.recent_operations),
            'avg_duration_ms': statistics.mean(durations),
            'median_duration_ms': statistics.median(durations),
            'p95_duration_ms': self._percentile(durations, 0.95),
            'p99_duration_ms': self._percentile(durations, 0.99),
            'slow_operations_count': slow_count,
            'critical_operations_count': critical_count,
            'tools_breakdown': tools_breakdown,
            'success_rate': (sum(successes) / len(successes)) * 100,
            'optimization_rate': (sum(optimizations) / len(optimizations)) * 100
        }

    def _percentile(self, data: List[float], percentile: float) -> float:
        """Calculate percentile value"""
        if not data:
            return 0.0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile)
        return sorted_data[min(index, len(sorted_data) - 1)]

    def get_recommendations(self) -> List[Dict[str, str]]:
        """
        Generate optimization recommendations based on recent operations

        Returns:
            List of recommendation dictionaries
        """
        recommendations = []

        # Analyze slow operations
        slow_ops = self.get_slow_operations(limit=100)

        # Group by tool
        tools_data = {}
        for op in slow_ops:
            tool = op['tool']
            if tool not in tools_data:
                tools_data[tool] = []
            tools_data[tool].append(op)

        # Generate tool-specific recommendations
        for tool, ops in tools_data.items():
            if tool == 'Read':
                # Check for large files read without optimization
                large_unoptimized = [
                    op for op in ops
                    if not op.get('optimization_applied', False)
                    and op.get('size_bytes', 0) > 100000  # >100KB
                ]

                if large_unoptimized:
                    recommendations.append({
                        'type': 'optimization',
                        'severity': 'high',
                        'title': f'{len(large_unoptimized)} Large Files Read Without Optimization',
                        'description': f'Found {len(large_unoptimized)} file reads >100KB without offset/limit parameters',
                        'suggestion': 'Use Read tool with offset/limit parameters for files >500 lines',
                        'example': 'Read(file_path="large_file.py", offset=0, limit=500)'
                    })

            elif tool == 'Grep':
                # Check for grep without head_limit
                no_head_limit = [
                    op for op in ops
                    if not op.get('optimization_applied', False)
                ]

                if no_head_limit:
                    recommendations.append({
                        'type': 'optimization',
                        'severity': 'medium',
                        'title': f'{len(no_head_limit)} Grep Operations Without head_limit',
                        'description': f'Found {len(no_head_limit)} Grep operations without head_limit parameter',
                        'suggestion': 'Always use head_limit parameter to reduce token usage',
                        'example': 'Grep(pattern="search", head_limit=100)'
                    })

            elif tool == 'Bash':
                # Check for long-running commands
                very_slow = [op for op in ops if op['duration_ms'] > self.CRITICAL_THRESHOLD]

                if very_slow:
                    recommendations.append({
                        'type': 'warning',
                        'severity': 'medium',
                        'title': f'{len(very_slow)} Slow Bash Commands Detected',
                        'description': f'Found {len(very_slow)} commands taking >{self.CRITICAL_THRESHOLD}ms',
                        'suggestion': 'Consider optimizing or running in background',
                        'example': 'Use run_in_background=True for long commands'
                    })

        # Check for repetitive file reads (caching opportunity)
        file_reads = {}
        for op in self.recent_operations:
            if op['tool'] == 'Read':
                target = op['target']
                file_reads[target] = file_reads.get(target, 0) + 1

        repeated_reads = {k: v for k, v in file_reads.items() if v >= 3}
        if repeated_reads:
            recommendations.append({
                'type': 'optimization',
                'severity': 'high',
                'title': f'{len(repeated_reads)} Files Read Multiple Times',
                'description': f'Detected {len(repeated_reads)} files read 3+ times without caching',
                'suggestion': 'Use context-cache.py for frequently accessed files',
                'example': 'python ~/.claude/memory/context-cache.py --set-file "path" --summary "..."'
            })

        return recommendations

    def analyze_trends(self, days: int = 7) -> Dict[str, Any]:
        """
        Analyze performance trends over time.
        Primary: reads operations_YYYY-MM-DD.json files.
        Fallback: groups flow-trace.json data by date when no operation files exist.
        """
        trend_data = {
            'labels': [],
            'avg_durations': [],
            'operation_counts': [],
            'slow_op_counts': []
        }

        # Try primary source first (operations files per day)
        found_any = False
        for i in range(days - 1, -1, -1):  # oldest to newest
            date = datetime.now() - timedelta(days=i)
            date_str = date.strftime('%Y-%m-%d')
            file_path = self.storage_dir / f"operations_{date_str}.json"

            if file_path.exists():
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                        operations = data.get('operations', [])

                        if operations:
                            durations = [op['duration_ms'] for op in operations]
                            slow_count = sum(1 for d in durations if d >= self.SLOW_THRESHOLD)

                            trend_data['labels'].append(date_str)
                            trend_data['avg_durations'].append(round(statistics.mean(durations), 1))
                            trend_data['operation_counts'].append(len(operations))
                            trend_data['slow_op_counts'].append(slow_count)
                            found_any = True
                except Exception as e:
                    print(f"Error loading data for {date_str}: {e}")

        if found_any:
            return trend_data

        # Fallback: build daily trend from flow-trace.json files
        return self._analyze_trends_from_flow_traces(days)

    def _analyze_trends_from_flow_traces(self, days: int = 7) -> Dict[str, Any]:
        """
        Build daily trend data by grouping flow-trace.json pipeline steps by date.
        Each session trace contributes its step durations to the day it occurred.
        """
        from collections import defaultdict
        import os

        trend_data = {
            'labels': [],
            'avg_durations': [],
            'operation_counts': [],
            'slow_op_counts': []
        }

        # Group operations by date
        daily: Dict[str, list] = defaultdict(list)

        try:
            home = Path(os.path.expanduser('~'))
            sessions_dir = home / '.claude' / 'memory' / 'logs' / 'sessions'
            if not sessions_dir.exists():
                return trend_data

            cutoff = datetime.now() - timedelta(days=days)

            for trace_file in sessions_dir.glob('*/flow-trace.json'):
                try:
                    with open(trace_file, 'r', encoding='utf-8', errors='replace') as f:
                        trace = json.load(f)

                    flow_start = trace.get('meta', {}).get('flow_start', '')
                    if not flow_start:
                        continue

                    # Parse date from flow_start ISO string
                    try:
                        dt = datetime.fromisoformat(flow_start[:19])
                    except Exception:
                        continue

                    if dt < cutoff:
                        continue

                    date_str = dt.strftime('%Y-%m-%d')

                    for step in trace.get('pipeline', []):
                        dur = step.get('duration_ms', 0)
                        if dur > 0:
                            daily[date_str].append(dur)

                except Exception:
                    continue

        except Exception as e:
            print(f"Error in trend fallback: {e}")
            return trend_data

        # Build ordered labels (last N days with data)
        all_days = sorted(daily.keys())[-days:]
        for date_str in all_days:
            durations = daily[date_str]
            if durations:
                slow = sum(1 for d in durations if d >= self.SLOW_THRESHOLD)
                trend_data['labels'].append(date_str)
                trend_data['avg_durations'].append(round(statistics.mean(durations), 1))
                trend_data['operation_counts'].append(len(durations))
                trend_data['slow_op_counts'].append(slow)

        return trend_data

    def get_resource_usage(self) -> Dict[str, Any]:
        """
        Get current resource usage statistics

        Returns:
            Dictionary with resource usage data
        """
        import psutil

        try:
            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()

            return {
                'memory_mb': memory_info.rss / 1024 / 1024,
                'cpu_percent': process.cpu_percent(interval=0.1),
                'num_threads': process.num_threads(),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

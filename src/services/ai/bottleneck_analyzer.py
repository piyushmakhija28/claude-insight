"""
Bottleneck Analyzer Service
AI-powered analysis and optimization recommendations for performance bottlenecks
"""

import statistics
from typing import List, Dict, Any
from collections import defaultdict, Counter


class BottleneckAnalyzer:
    """
    Analyzes performance data to identify bottlenecks and generate
    AI-powered optimization recommendations
    """

    def __init__(self):
        """Initialize the bottleneck analyzer"""
        self.SLOW_THRESHOLD = 2000  # 2 seconds
        self.LARGE_FILE_THRESHOLD = 100000  # 100KB
        self.REPETITION_THRESHOLD = 3  # Same file read 3+ times

    def generate_recommendations(self, operations: List[Dict]) -> List[Dict[str, str]]:
        """
        Generate optimization recommendations based on operations

        Args:
            operations: List of operation dictionaries

        Returns:
            List of recommendation dictionaries with type, severity, title, description, suggestion, example
        """
        if not operations:
            return []

        recommendations = []

        # Analyze different aspects
        recommendations.extend(self._analyze_file_operations(operations))
        recommendations.extend(self._analyze_repetitive_operations(operations))
        recommendations.extend(self._analyze_bash_commands(operations))
        recommendations.extend(self._analyze_grep_operations(operations))
        recommendations.extend(self._analyze_performance_regression(operations))

        # Sort by severity
        severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        recommendations.sort(key=lambda x: severity_order.get(x['severity'], 999))

        return recommendations

    def _analyze_file_operations(self, operations: List[Dict]) -> List[Dict]:
        """Analyze file read/write operations for optimization opportunities"""
        recommendations = []

        # Filter file operations
        file_ops = [op for op in operations if op['tool'] in ['Read', 'Write', 'Edit']]

        if not file_ops:
            return recommendations

        # Find large files read without optimization
        large_unoptimized = [
            op for op in file_ops
            if op['tool'] == 'Read'
            and not op.get('optimization_applied', False)
            and op.get('size_bytes', 0) > self.LARGE_FILE_THRESHOLD
        ]

        if large_unoptimized:
            total_size = sum(op.get('size_bytes', 0) for op in large_unoptimized)
            recommendations.append({
                'type': 'optimization',
                'severity': 'high',
                'title': f'{len(large_unoptimized)} Large Files Read Without Optimization',
                'description': f'Found {len(large_unoptimized)} files (total {total_size / 1024 / 1024:.1f}MB) '
                             f'read without offset/limit parameters. This wastes significant tokens.',
                'suggestion': 'Use Read tool with offset and limit parameters for files >500 lines. '
                            'Read only the sections you need, or use sandwich reading (first 50 + last 50 lines).',
                'example': 'Read(file_path="large_file.py", offset=0, limit=500)\n'
                          '# Or for structure overview:\n'
                          'Read(file_path="large_file.py", offset=0, limit=50)  # Header\n'
                          'Read(file_path="large_file.py", offset=-50)  # Footer'
            })

        # Find slow file writes
        slow_writes = [
            op for op in file_ops
            if op['tool'] == 'Write'
            and op.get('duration_ms', 0) > self.SLOW_THRESHOLD
        ]

        if slow_writes:
            recommendations.append({
                'type': 'warning',
                'severity': 'medium',
                'title': f'{len(slow_writes)} Slow File Write Operations',
                'description': f'Detected {len(slow_writes)} file writes taking >{self.SLOW_THRESHOLD}ms. '
                             f'This may indicate large files or disk I/O issues.',
                'suggestion': 'Consider breaking large files into smaller chunks or using Edit tool '
                            'for partial updates instead of full file writes.',
                'example': 'Edit(file_path="file.py", old_string="...", new_string="...")\n'
                          '# Instead of:\n'
                          'Write(file_path="file.py", content="... entire file ...")'
            })

        return recommendations

    def _analyze_repetitive_operations(self, operations: List[Dict]) -> List[Dict]:
        """Analyze for repetitive operations that could be cached"""
        recommendations = []

        # Count file reads by target
        read_counts = Counter()
        read_ops = defaultdict(list)

        for op in operations:
            if op['tool'] == 'Read':
                target = op['target']
                read_counts[target] += 1
                read_ops[target].append(op)

        # Find files read multiple times
        repeated_reads = {k: v for k, v in read_counts.items() if v >= self.REPETITION_THRESHOLD}

        if repeated_reads:
            # Calculate token waste
            total_reads = sum(repeated_reads.values())
            unique_files = len(repeated_reads)

            # Estimate token savings (assume average file is 1000 tokens)
            estimated_waste = (total_reads - unique_files) * 1000

            recommendations.append({
                'type': 'optimization',
                'severity': 'high',
                'title': f'{unique_files} Files Read Multiple Times ({total_reads} total reads)',
                'description': f'Detected {unique_files} files read {self.REPETITION_THRESHOLD}+ times. '
                             f'Estimated token waste: ~{estimated_waste:,} tokens. '
                             f'Using cache could save significant context.',
                'suggestion': 'Implement tiered caching for frequently accessed files. '
                            'Hot files (5+ accesses) should be kept in full cache. '
                            'Warm files (3-4 accesses) should use summary cache.',
                'example': 'python ~/.claude/memory/tiered-cache.py --get-file "path/to/file"\n'
                          '# If cache miss:\n'
                          'python ~/.claude/memory/tiered-cache.py --set-file "path/to/file" --content "..."'
            })

            # List top repeated files
            top_repeated = sorted(repeated_reads.items(), key=lambda x: x[1], reverse=True)[:5]
            file_list = '\n'.join([f'  - {file}: {count} reads' for file, count in top_repeated])

            recommendations.append({
                'type': 'info',
                'severity': 'low',
                'title': 'Top Repeated File Reads',
                'description': f'Most frequently read files:\n{file_list}',
                'suggestion': 'Prioritize caching these files first for maximum impact.',
                'example': ''
            })

        return recommendations

    def _analyze_bash_commands(self, operations: List[Dict]) -> List[Dict]:
        """Analyze Bash command performance"""
        recommendations = []

        bash_ops = [op for op in operations if op['tool'] == 'Bash']

        if not bash_ops:
            return recommendations

        # Find very slow commands
        very_slow = [op for op in bash_ops if op.get('duration_ms', 0) > 5000]  # >5 seconds

        if very_slow:
            # Group by command pattern
            command_patterns = defaultdict(list)
            for op in very_slow:
                cmd = op['target'][:30]  # First 30 chars as pattern
                command_patterns[cmd].append(op)

            recommendations.append({
                'type': 'warning',
                'severity': 'medium',
                'title': f'{len(very_slow)} Slow Bash Commands Detected',
                'description': f'Found {len(very_slow)} commands taking >5 seconds. '
                             f'Long-running commands block execution and waste time.',
                'suggestion': 'Use run_in_background=True for long commands like npm install, '
                            'docker build, test runs, etc. Monitor with TaskOutput.',
                'example': 'Bash(command="npm install", run_in_background=True)\n'
                          '# Then check later:\n'
                          'TaskOutput(task_id="...", block=False)'
            })

        # Check for commands that should use dedicated tools
        misused_commands = []
        for op in bash_ops:
            cmd = op['target'].lower()
            if any(word in cmd for word in ['grep', 'find', 'cat', 'head', 'tail']):
                misused_commands.append(op)

        if misused_commands:
            recommendations.append({
                'type': 'optimization',
                'severity': 'medium',
                'title': f'{len(misused_commands)} Bash Commands Should Use Dedicated Tools',
                'description': f'Detected {len(misused_commands)} Bash commands using grep/find/cat/etc. '
                             f'Dedicated tools are faster and more efficient.',
                'suggestion': 'Use Grep instead of bash grep, Glob instead of find, Read instead of cat.',
                'example': '# Instead of: Bash("grep pattern file.txt")\n'
                          'Grep(pattern="pattern", path="file.txt")\n\n'
                          '# Instead of: Bash("find . -name *.py")\n'
                          'Glob(pattern="**/*.py")'
            })

        return recommendations

    def _analyze_grep_operations(self, operations: List[Dict]) -> List[Dict]:
        """Analyze Grep operations for optimization"""
        recommendations = []

        grep_ops = [op for op in operations if op['tool'] == 'Grep']

        if not grep_ops:
            return recommendations

        # Find grep without head_limit
        no_head_limit = [
            op for op in grep_ops
            if not op.get('optimization_applied', False)
        ]

        if no_head_limit:
            recommendations.append({
                'type': 'optimization',
                'severity': 'medium',
                'title': f'{len(no_head_limit)} Grep Operations Missing head_limit',
                'description': f'Found {len(no_head_limit)} Grep operations without head_limit parameter. '
                             f'This can return hundreds of results, wasting tokens.',
                'suggestion': 'Always use head_limit parameter. Start conservative (10-20), '
                            'expand only if needed. Use progressive refinement strategy.',
                'example': 'Grep(pattern="function", head_limit=10)  # Start small\n'
                          '# If not enough:\n'
                          'Grep(pattern="function.*User", head_limit=20)  # Refine pattern\n'
                          '# Or filter by type:\n'
                          'Grep(pattern="function", type="ts", head_limit=30)'
            })

        # Analyze grep patterns for optimization
        slow_greps = [op for op in grep_ops if op.get('duration_ms', 0) > self.SLOW_THRESHOLD]

        if slow_greps:
            recommendations.append({
                'type': 'warning',
                'severity': 'low',
                'title': f'{len(slow_greps)} Slow Grep Operations',
                'description': f'Detected {len(slow_greps)} Grep operations taking >{self.SLOW_THRESHOLD}ms. '
                             f'May indicate overly broad patterns or large search spaces.',
                'suggestion': 'Narrow search scope using glob patterns or file type filters. '
                            'Use more specific patterns.',
                'example': 'Grep(pattern="AuthService.login", glob="src/auth/**", head_limit=20)\n'
                          '# Instead of:\n'
                          'Grep(pattern="login", head_limit=100)  # Too broad'
            })

        return recommendations

    def _analyze_performance_regression(self, operations: List[Dict]) -> List[Dict]:
        """Detect performance regression trends"""
        recommendations = []

        if len(operations) < 20:
            return recommendations  # Not enough data

        # Split into two halves: recent vs earlier
        mid_point = len(operations) // 2
        recent_ops = operations[:mid_point]
        earlier_ops = operations[mid_point:]

        # Calculate average durations
        recent_avg = statistics.mean([op['duration_ms'] for op in recent_ops])
        earlier_avg = statistics.mean([op['duration_ms'] for op in earlier_ops])

        # Check for regression (>20% slower)
        if recent_avg > earlier_avg * 1.2:
            increase_percent = ((recent_avg - earlier_avg) / earlier_avg) * 100

            recommendations.append({
                'type': 'warning',
                'severity': 'high',
                'title': 'Performance Regression Detected',
                'description': f'Recent operations are {increase_percent:.1f}% slower than earlier ones. '
                             f'Average duration increased from {earlier_avg:.0f}ms to {recent_avg:.0f}ms.',
                'suggestion': 'Investigate recent changes. Check for increased file sizes, '
                            'broader search patterns, or missing optimizations.',
                'example': 'Review recent operations and compare:\n'
                          '- File sizes being read\n'
                          '- Grep patterns (too broad?)\n'
                          '- Cache hit rates\n'
                          '- Number of repetitive operations'
            })

        # Check for improvement (good news!)
        elif recent_avg < earlier_avg * 0.8:
            improvement_percent = ((earlier_avg - recent_avg) / earlier_avg) * 100

            recommendations.append({
                'type': 'info',
                'severity': 'low',
                'title': 'Performance Improvement Detected',
                'description': f'Recent operations are {improvement_percent:.1f}% faster than earlier ones! '
                             f'Average duration decreased from {earlier_avg:.0f}ms to {recent_avg:.0f}ms.',
                'suggestion': 'Great job! Continue applying current optimization strategies.',
                'example': ''
            })

        return recommendations

    def analyze_tool_efficiency(self, operations: List[Dict]) -> Dict[str, Any]:
        """
        Analyze efficiency by tool type

        Returns:
            Dictionary with efficiency metrics per tool
        """
        tool_stats = defaultdict(lambda: {
            'count': 0,
            'total_duration': 0,
            'avg_duration': 0,
            'optimized_count': 0,
            'slow_count': 0
        })

        for op in operations:
            tool = op['tool']
            duration = op.get('duration_ms', 0)

            tool_stats[tool]['count'] += 1
            tool_stats[tool]['total_duration'] += duration

            if op.get('optimization_applied', False):
                tool_stats[tool]['optimized_count'] += 1

            if duration >= self.SLOW_THRESHOLD:
                tool_stats[tool]['slow_count'] += 1

        # Calculate averages
        for tool, stats in tool_stats.items():
            if stats['count'] > 0:
                stats['avg_duration'] = stats['total_duration'] / stats['count']
                stats['optimization_rate'] = (stats['optimized_count'] / stats['count']) * 100

        return dict(tool_stats)

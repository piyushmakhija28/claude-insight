"""
Tool Optimization Tracker
Tracks 15 token optimization strategies from ADVANCED-TOKEN-OPTIMIZATION.md:
1. Response Compression
2. Diff-Based Editing
3. Smart Tool Selection (tree, Glob vs Grep)
4. Smart Grep Optimization
5. Tiered Caching
6. Session State (Aggressive)
7. Incremental Updates
8. File Type Optimization
9. Lazy Context Loading
10. Smart File Summarization
11. Batch File Operations
12. MCP Response Filtering
13. Conversation Pruning
14. AST-Based Code Navigation
15. Parallel Tool Calls
"""
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict


class OptimizationTracker:
    """Track tool optimization strategies and token savings"""

    def __init__(self):
        self.memory_dir = Path.home() / '.claude' / 'memory'
        self.logs_dir = self.memory_dir / 'logs'
        self.docs_dir = self.memory_dir / 'docs'

    def get_tool_optimization_metrics(self):
        """
        Track 15 optimization strategies
        """
        policy_log = self.logs_dir / 'policy-hits.log'

        # Define 15 optimization strategies
        strategies = {
            'response_compression': {'count': 0, 'tokens_saved': 0, 'description': 'Ultra-brief responses'},
            'diff_based_editing': {'count': 0, 'tokens_saved': 0, 'description': 'Show only changed lines'},
            'smart_tool_selection': {'count': 0, 'tokens_saved': 0, 'description': 'tree vs Glob/Grep'},
            'smart_grep': {'count': 0, 'tokens_saved': 0, 'description': 'head_limit, files_with_matches'},
            'tiered_caching': {'count': 0, 'tokens_saved': 0, 'description': 'Hot/Warm/Cold cache'},
            'session_state': {'count': 0, 'tokens_saved': 0, 'description': 'Aggressive external state'},
            'incremental_updates': {'count': 0, 'tokens_saved': 0, 'description': 'Partial updates only'},
            'file_type_optimization': {'count': 0, 'tokens_saved': 0, 'description': 'Language-specific'},
            'lazy_context_loading': {'count': 0, 'tokens_saved': 0, 'description': 'Load only when needed'},
            'smart_summarization': {'count': 0, 'tokens_saved': 0, 'description': 'Intelligent summaries'},
            'batch_operations': {'count': 0, 'tokens_saved': 0, 'description': 'Combine multiple operations'},
            'mcp_filtering': {'count': 0, 'tokens_saved': 0, 'description': 'Filter MCP responses'},
            'conversation_pruning': {'count': 0, 'tokens_saved': 0, 'description': 'Remove old messages'},
            'ast_navigation': {'count': 0, 'tokens_saved': 0, 'description': 'AST-based code nav'},
            'parallel_tools': {'count': 0, 'tokens_saved': 0, 'description': 'Parallel tool calls'}
        }

        if not policy_log.exists():
            return {
                'strategies': strategies,
                'total_optimizations': 0,
                'total_tokens_saved': 0,
                'top_strategies': []
            }

        try:
            lines = policy_log.read_text().splitlines()

            for line in lines:
                line_lower = line.lower()

                # Detect strategy usage
                if 'compression' in line_lower or 'brief response' in line_lower:
                    strategies['response_compression']['count'] += 1
                    strategies['response_compression']['tokens_saved'] += 100  # Estimate

                if 'diff' in line_lower or 'changed lines' in line_lower:
                    strategies['diff_based_editing']['count'] += 1
                    strategies['diff_based_editing']['tokens_saved'] += 200

                if 'tree' in line_lower and ('glob' in line_lower or 'grep' in line_lower):
                    strategies['smart_tool_selection']['count'] += 1
                    strategies['smart_tool_selection']['tokens_saved'] += 500

                if 'head_limit' in line_lower or 'files_with_matches' in line_lower:
                    strategies['smart_grep']['count'] += 1
                    strategies['smart_grep']['tokens_saved'] += 300

                if 'cache' in line_lower and ('hot' in line_lower or 'warm' in line_lower or 'cold' in line_lower):
                    strategies['tiered_caching']['count'] += 1
                    strategies['tiered_caching']['tokens_saved'] += 400

                if 'session state' in line_lower or 'external state' in line_lower:
                    strategies['session_state']['count'] += 1
                    strategies['session_state']['tokens_saved'] += 600

                if 'incremental' in line_lower or 'partial update' in line_lower:
                    strategies['incremental_updates']['count'] += 1
                    strategies['incremental_updates']['tokens_saved'] += 250

                if 'file type' in line_lower or 'language-specific' in line_lower:
                    strategies['file_type_optimization']['count'] += 1
                    strategies['file_type_optimization']['tokens_saved'] += 150

                if 'lazy load' in line_lower or 'on-demand' in line_lower:
                    strategies['lazy_context_loading']['count'] += 1
                    strategies['lazy_context_loading']['tokens_saved'] += 350

                if 'summariz' in line_lower or 'summary' in line_lower:
                    strategies['smart_summarization']['count'] += 1
                    strategies['smart_summarization']['tokens_saved'] += 450

                if 'batch' in line_lower or 'combine operations' in line_lower:
                    strategies['batch_operations']['count'] += 1
                    strategies['batch_operations']['tokens_saved'] += 200

                if 'mcp' in line_lower and 'filter' in line_lower:
                    strategies['mcp_filtering']['count'] += 1
                    strategies['mcp_filtering']['tokens_saved'] += 300

                if 'prune' in line_lower or 'cleanup conversation' in line_lower:
                    strategies['conversation_pruning']['count'] += 1
                    strategies['conversation_pruning']['tokens_saved'] += 800

                if 'ast' in line_lower or 'syntax tree' in line_lower:
                    strategies['ast_navigation']['count'] += 1
                    strategies['ast_navigation']['tokens_saved'] += 400

                if 'parallel' in line_lower and 'tool' in line_lower:
                    strategies['parallel_tools']['count'] += 1
                    strategies['parallel_tools']['tokens_saved'] += 150

            # Calculate totals
            total_optimizations = sum(s['count'] for s in strategies.values())
            total_tokens_saved = sum(s['tokens_saved'] for s in strategies.values())

            # Get top 5 strategies
            top_strategies = sorted(
                [{'name': k, **v} for k, v in strategies.items()],
                key=lambda x: x['tokens_saved'],
                reverse=True
            )[:5]

            return {
                'strategies': strategies,
                'total_optimizations': total_optimizations,
                'total_tokens_saved': total_tokens_saved,
                'estimated_savings_percentage': min(80, (total_tokens_saved / 1000) if total_tokens_saved > 0 else 0),
                'top_strategies': top_strategies
            }

        except Exception as e:
            return {
                'strategies': strategies,
                'total_optimizations': 0,
                'total_tokens_saved': 0,
                'error': str(e)
            }

    def get_standards_enforcement_stats(self):
        """
        Track coding standards loading and enforcement
        Java Spring Boot standards, Config Server rules, etc.
        """
        policy_log = self.logs_dir / 'policy-hits.log'

        stats = {
            'total_enforcements': 0,
            'standards_by_type': defaultdict(int),
            'violations_detected': 0,
            'auto_fixes_applied': 0,
            'recent_enforcements': []
        }

        if not policy_log.exists():
            return stats

        try:
            lines = policy_log.read_text().splitlines()

            for line in lines:
                line_lower = line.lower()

                if 'standard' in line_lower or 'coding rule' in line_lower or 'pattern' in line_lower:
                    stats['total_enforcements'] += 1

                    # Categorize standard type
                    if 'java' in line_lower or 'spring' in line_lower:
                        stats['standards_by_type']['java_spring_boot'] += 1
                    elif 'config server' in line_lower or 'configuration' in line_lower:
                        stats['standards_by_type']['config_server'] += 1
                    elif 'secret' in line_lower:
                        stats['standards_by_type']['secret_management'] += 1
                    elif 'api' in line_lower or 'rest' in line_lower:
                        stats['standards_by_type']['api_design'] += 1
                    elif 'database' in line_lower or 'entity' in line_lower:
                        stats['standards_by_type']['database'] += 1
                    else:
                        stats['standards_by_type']['general'] += 1

                    # Detect violations and fixes
                    if 'violation' in line_lower or 'not compliant' in line_lower:
                        stats['violations_detected'] += 1

                    if 'fix applied' in line_lower or 'corrected' in line_lower:
                        stats['auto_fixes_applied'] += 1

                    # Store recent (last 15)
                    if len(stats['recent_enforcements']) < 15:
                        stats['recent_enforcements'].append({
                            'timestamp': datetime.now().isoformat(),
                            'log_entry': line[:200]
                        })

            # Convert defaultdict
            stats['standards_by_type'] = dict(stats['standards_by_type'])

        except Exception as e:
            stats['error'] = str(e)

        return stats

    def get_comprehensive_optimization_stats(self):
        """
        Get all optimization statistics in one call
        """
        return {
            'tool_optimization': self.get_tool_optimization_metrics(),
            'standards_enforcement': self.get_standards_enforcement_stats(),
            'timestamp': datetime.now().isoformat()
        }

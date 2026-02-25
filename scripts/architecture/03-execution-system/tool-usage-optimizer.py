#!/usr/bin/env python3
"""
Tool Usage Optimizer
Pre-execution checker that optimizes tool parameters for token efficiency
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional


class ToolUsageOptimizer:
    """
    Optimizes tool parameters before execution to reduce token usage
    """

    def __init__(self):
        self.optimization_log = []
        self.cache_dir = Path.home() / ".claude" / "memory" / ".cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def optimize(
        self,
        tool_name: str,
        params: Dict[str, Any],
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Main optimization entry point
        """
        context = context or {}

        print(f"\n{'='*60}")
        print(f"🔍 TOOL OPTIMIZATION: {tool_name}")
        print(f"{'='*60}")

        original_params = params.copy()

        if tool_name == 'Read':
            optimized = self.optimize_read(params, context)
        elif tool_name == 'Grep':
            optimized = self.optimize_grep(params, context)
        elif tool_name == 'Glob':
            optimized = self.optimize_glob(params, context)
        elif tool_name == 'Bash':
            optimized = self.optimize_bash(params, context)
        elif tool_name == 'Edit':
            optimized = params  # Edit is optimized in output
        elif tool_name == 'Write':
            optimized = params  # Write is optimized in output
        else:
            optimized = params

        # Show changes
        changes = self.get_parameter_changes(original_params, optimized)
        if changes:
            print(f"\n📊 Optimizations Applied:")
            for change in changes:
                print(f"   • {change}")

        # Estimate savings
        savings = self.estimate_savings(tool_name, original_params, optimized)
        if savings > 0:
            print(f"\n💰 Estimated Token Savings: ~{savings}%")

        print(f"{'='*60}\n")

        # Log
        self.log_optimization(tool_name, original_params, optimized, savings)

        return optimized

    def optimize_read(self, params: Dict, context: Dict) -> Dict:
        """
        Optimize Read tool parameters
        """
        file_path = params.get('file_path', '')

        # Check file size
        file_size = self.get_file_size(file_path)

        if file_size and file_size > 500:
            # Large file - apply offset/limit
            if 'offset' not in params and 'limit' not in params:
                # Check context for what we need
                looking_for = context.get('looking_for', '')

                if 'imports' in looking_for.lower() or 'top' in looking_for.lower():
                    params['offset'] = 0
                    params['limit'] = 50
                elif 'recent' in looking_for.lower() or 'bottom' in looking_for.lower():
                    params['offset'] = max(0, file_size - 50)
                    params['limit'] = 50
                else:
                    # Default: top 100 lines
                    params['offset'] = 0
                    params['limit'] = 100

        # Check cache
        access_count = self.get_access_count(file_path)
        if access_count >= 3:
            cached_content = self.get_from_cache(file_path)
            if cached_content:
                params['_use_cache'] = True  # Flag for caller

        return params

    def optimize_grep(self, params: Dict, context: Dict) -> Dict:
        """
        Optimize Grep tool parameters
        """
        # MANDATORY: Always add head_limit if not present
        if 'head_limit' not in params:
            params['head_limit'] = 100

        # Default to file list unless content explicitly needed
        if 'output_mode' not in params:
            if context.get('need_content'):
                params['output_mode'] = 'content'
                params['head_limit'] = min(params.get('head_limit', 100), 50)
                params['-A'] = 2  # Limit context
                params['-B'] = 1
            else:
                params['output_mode'] = 'files_with_matches'

        # File type filtering if known
        if context.get('file_type') and 'type' not in params:
            params['type'] = context['file_type']

        # Path restriction if known
        if context.get('directory') and 'path' not in params:
            params['path'] = context['directory']

        return params

    def optimize_glob(self, params: Dict, context: Dict) -> Dict:
        """
        Optimize Glob tool parameters
        """
        pattern = params.get('pattern', '')

        # Add path restriction if service known
        if context.get('service_name') and 'path' not in params:
            service = context['service_name']
            params['path'] = f"backend/{service}/"

        # Limit broad patterns
        if '**/*' in pattern and not context.get('need_deep_search'):
            # Make pattern more specific if possible
            if context.get('file_extension'):
                ext = context['file_extension']
                if f'*.{ext}' not in pattern:
                    params['pattern'] = pattern.replace('*', f'*.{ext}')

        return params

    def optimize_bash(self, params: Dict, context: Dict) -> Dict:
        """
        Optimize Bash tool parameters
        """
        command = params.get('command', '')

        # 🌳 TREE PATTERN: Suggest tree for structure understanding
        if context.get('first_time_in_directory'):
            directory = context.get('directory', '')
            if directory and 'tree' not in command:
                suggestion = f"tree -L 3 {directory}"
                print(f"\n💡 SUGGESTION: Use tree to understand structure first:")
                print(f"   {suggestion}")
                print(f"   Then you'll know exact file locations!")

        # Combine sequential commands if multiple
        if context.get('commands') and len(context['commands']) > 1:
            if context.get('sequential'):
                params['command'] = ' && '.join(context['commands'])

        # Add output limiting
        if 'find' in command and '| head' not in command:
            params['command'] = command + ' | head -20'

        if 'ls' in command and '-l' in command:
            # Detailed listing not usually needed
            params['command'] = command.replace('ls -l', 'ls -1')

        # Quiet mode for build commands if just checking success
        if context.get('just_check_success'):
            if 'mvn' in command and '-q' not in command:
                params['command'] = command + ' -q'

        # Tree command optimizations
        if 'tree' in command:
            # Ensure depth limit
            if '-L' not in command and '--level' not in command:
                params['command'] = command + ' -L 3'
                print("   • Added depth limit: -L 3")

            # Suggest specific patterns
            if context.get('file_type') and '-P' not in command:
                file_type = context['file_type']
                print(f"   💡 Consider: tree -P '*.{file_type}' for specific files")

        return params

    def get_file_size(self, file_path: str) -> Optional[int]:
        """Get file size in lines"""
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    return sum(1 for _ in f)
        except:
            pass
        return None

    def get_access_count(self, file_path: str) -> int:
        """Get how many times file has been accessed"""
        cache_file = self.cache_dir / "access_counts.json"

        if cache_file.exists():
            with open(cache_file, 'r') as f:
                counts = json.load(f)
                return counts.get(file_path, 0)

        return 0

    def get_from_cache(self, file_path: str) -> Optional[str]:
        """Get cached file content"""
        # Simplified - would use tiered-cache.py in practice
        return None

    def get_parameter_changes(
        self,
        original: Dict,
        optimized: Dict
    ) -> list:
        """Get list of parameter changes"""
        changes = []

        for key, value in optimized.items():
            if key not in original:
                changes.append(f"Added: {key}={value}")
            elif original[key] != value:
                changes.append(f"Changed: {key}={original[key]} → {value}")

        return changes

    def estimate_savings(
        self,
        tool_name: str,
        original: Dict,
        optimized: Dict
    ) -> int:
        """Estimate token savings percentage"""
        if tool_name == 'Read':
            if 'limit' in optimized and 'limit' not in original:
                # Limited read vs full read
                return 70  # Estimated 70% savings

        elif tool_name == 'Grep':
            if 'head_limit' in optimized:
                # Limited results
                if optimized.get('output_mode') == 'files_with_matches':
                    return 80  # File list only
                else:
                    return 50  # Limited content

        elif tool_name == 'Glob':
            if 'path' in optimized and 'path' not in original:
                return 40  # Path restriction

        elif tool_name == 'Bash':
            if '&&' in optimized.get('command', ''):
                return 30  # Combined commands

        return 0

    def log_optimization(
        self,
        tool: str,
        original: Dict,
        optimized: Dict,
        savings: int
    ):
        """Log optimization for analysis"""
        self.optimization_log.append({
            'tool': tool,
            'original_params': original,
            'optimized_params': optimized,
            'estimated_savings': savings
        })


def main():
    """CLI interface"""
    import sys

    if len(sys.argv) < 3:
        print("="*60)
        print("Tool Usage Optimizer")
        print("="*60)
        print("\nUsage:")
        print("  python tool-usage-optimizer.py TOOL_NAME params.json [context.json]")
        print("\nExample:")
        print("  python tool-usage-optimizer.py Read read_params.json")
        print("\nSupported Tools:")
        print("  - Read")
        print("  - Grep")
        print("  - Glob")
        print("  - Bash")
        print("  - Edit")
        print("  - Write")
        sys.exit(1)

    tool_name = sys.argv[1]

    # Load params
    with open(sys.argv[2], 'r') as f:
        params = json.load(f)

    # Load context if provided
    context = {}
    if len(sys.argv) > 3:
        with open(sys.argv[3], 'r') as f:
            context = json.load(f)

    # Optimize
    optimizer = ToolUsageOptimizer()
    optimized = optimizer.optimize(tool_name, params, context)

    # Output
    print("\n" + "="*60)
    print("OPTIMIZED PARAMETERS")
    print("="*60)
    print(json.dumps(optimized, indent=2))


if __name__ == "__main__":
    main()

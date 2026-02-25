#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Automatic Tool Wrapper
Runs before every Read/Grep/Glob to optimize automatically

Features:
1. Check tiered cache
2. Get file type optimization
3. Auto-summarize large files
4. Use AST for code files
5. Log token usage

Usage (called by Claude before tool use):
    python auto-tool-wrapper.py --tool Read --params '{"file_path": "..."}'
    python auto-tool-wrapper.py --tool Grep --params '{"pattern": "..."}'
"""

import sys
import os
import json
import subprocess
from datetime import datetime

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

MEMORY_DIR = os.path.expanduser("~/.claude/memory")
TOKEN_LOG = os.path.join(MEMORY_DIR, "logs/token-optimization.log")

def log_optimization(tool, optimization_type, tokens_saved, details=""):
    """Log token optimization"""
    try:
        os.makedirs(os.path.dirname(TOKEN_LOG), exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {tool} | {optimization_type} | Saved: {tokens_saved} tokens | {details}\n"

        with open(TOKEN_LOG, 'a', encoding='utf-8') as f:
            f.write(log_entry)
    except Exception as e:
        print(f"Warning: Could not log optimization: {e}", file=sys.stderr)

def check_cache(filepath):
    """Check tiered cache for file"""
    try:
        result = subprocess.run(
            ["python", os.path.join(MEMORY_DIR, "tiered-cache.py"), "--get-file", filepath],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0:
            data = json.loads(result.stdout)
            if data.get('cache_hit'):
                return data
        return None
    except:
        return None

def get_file_optimization(filepath, purpose='general'):
    """Get file type specific optimization"""
    try:
        result = subprocess.run(
            ["python", os.path.join(MEMORY_DIR, "file-type-optimizer.py"),
             "--file", filepath, "--purpose", purpose],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0:
            return json.loads(result.stdout)
        return None
    except:
        return None

def should_summarize(filepath):
    """Check if file should be summarized"""
    try:
        # Get file size
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            line_count = sum(1 for _ in f)

        return line_count > 500
    except:
        return False

def get_summary(filepath):
    """Get smart summary for large file"""
    try:
        result = subprocess.run(
            ["python", os.path.join(MEMORY_DIR, "smart-file-summarizer.py"),
             "--file", filepath, "--strategy", "auto"],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            return json.loads(result.stdout)
        return None
    except:
        return None

def use_ast(filepath):
    """Check if should use AST navigation"""
    ext = os.path.splitext(filepath)[1].lower()
    return ext in ['.java', '.ts', '.js', '.py']

def get_ast_structure(filepath):
    """Get AST structure"""
    try:
        result = subprocess.run(
            ["python", os.path.join(MEMORY_DIR, "ast-code-navigator.py"),
             "--file", filepath],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            return json.loads(result.stdout)
        return None
    except:
        return None

def optimize_read_params(params):
    """Optimize Read tool parameters"""
    filepath = params.get('file_path', '')

    if not filepath or not os.path.exists(filepath):
        return {
            'optimized': False,
            'original_params': params,
            'message': 'File not found or invalid'
        }

    optimizations = []

    # 1. Check cache first
    cache_data = check_cache(filepath)
    if cache_data and cache_data.get('cache_hit'):
        tier = cache_data.get('tier')
        if tier == 'HOT':
            optimizations.append({
                'type': 'cache_hit_hot',
                'tokens_saved': 1500,  # Estimate: no file read needed
                'message': 'Using cached full content (HOT tier)'
            })
            return {
                'optimized': True,
                'strategy': 'cache_hot',
                'use_cache': True,
                'cache_data': cache_data.get('cached_data'),
                'optimizations': optimizations
            }
        elif tier == 'WARM':
            optimizations.append({
                'type': 'cache_hit_warm',
                'tokens_saved': 1000,
                'message': 'Using cached summary (WARM tier)'
            })

    # 2. Check if should use AST
    if use_ast(filepath):
        ast_data = get_ast_structure(filepath)
        if ast_data and not ast_data.get('error'):
            optimizations.append({
                'type': 'ast_navigation',
                'tokens_saved': 1800,  # 95% savings on 2000 token file
                'message': 'Using AST structure instead of full read'
            })
            return {
                'optimized': True,
                'strategy': 'ast',
                'ast_data': ast_data,
                'optimizations': optimizations
            }

    # 3. Check if should summarize
    if should_summarize(filepath):
        summary_data = get_summary(filepath)
        if summary_data and not summary_data.get('error'):
            optimizations.append({
                'type': 'smart_summary',
                'tokens_saved': int(summary_data.get('token_savings', '70%').replace('%', '')) * 20,
                'message': f"Using {summary_data.get('strategy')} summary"
            })
            return {
                'optimized': True,
                'strategy': 'summary',
                'summary_data': summary_data,
                'optimizations': optimizations
            }

    # 4. Get file type optimization
    file_opt = get_file_optimization(filepath)
    if file_opt:
        optimizations.append({
            'type': 'file_type_optimization',
            'tokens_saved': 500,
            'message': file_opt.get('recommended_strategy', '')
        })

    # 5. Apply offset/limit if large
    if should_summarize(filepath) and 'offset' not in params:
        params['offset'] = 0
        params['limit'] = 500
        optimizations.append({
            'type': 'offset_limit',
            'tokens_saved': 1000,
            'message': 'Applied offset=0, limit=500 for large file'
        })

    # Log all optimizations
    for opt in optimizations:
        log_optimization('Read', opt['type'], opt['tokens_saved'], opt['message'])

    return {
        'optimized': len(optimizations) > 0,
        'strategy': 'optimized_read',
        'optimized_params': params,
        'optimizations': optimizations,
        'total_tokens_saved': sum(opt['tokens_saved'] for opt in optimizations)
    }

def optimize_grep_params(params):
    """Optimize Grep tool parameters"""
    optimizations = []

    # 1. Apply low head_limit if not specified
    if 'head_limit' not in params:
        params['head_limit'] = 10  # Start conservative
        optimizations.append({
            'type': 'smart_grep_limit',
            'tokens_saved': 360,  # 90 results avoided
            'message': 'Applied head_limit=10 (progressive refinement)'
        })

    # 2. Suggest file type filter if possible
    pattern = params.get('pattern', '')
    if pattern and 'type' not in params and 'glob' not in params:
        optimizations.append({
            'type': 'grep_suggestion',
            'tokens_saved': 0,
            'message': 'Consider adding --type or --glob to narrow search'
        })

    # Log optimizations
    for opt in optimizations:
        log_optimization('Grep', opt['type'], opt['tokens_saved'], opt['message'])

    return {
        'optimized': len(optimizations) > 0,
        'optimized_params': params,
        'optimizations': optimizations,
        'total_tokens_saved': sum(opt['tokens_saved'] for opt in optimizations)
    }

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Auto Tool Wrapper')
    parser.add_argument('--tool', required=True, choices=['Read', 'Grep', 'Glob'])
    parser.add_argument('--params', required=True, help='Tool parameters as JSON')

    args = parser.parse_args()

    try:
        params = json.loads(args.params)
    except:
        print(json.dumps({'error': 'Invalid JSON params'}))
        return

    if args.tool == 'Read':
        result = optimize_read_params(params)
    elif args.tool == 'Grep':
        result = optimize_grep_params(params)
    else:
        result = {'optimized': False, 'message': 'Tool not supported yet'}

    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()

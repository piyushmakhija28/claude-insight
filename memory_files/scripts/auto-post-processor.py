#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Automatic Post-Tool Processor
Runs after every tool execution to cache results and log tokens

Features:
1. Update tiered cache
2. Extract essentials from output
3. Log token usage
4. Update session state

Usage (called by Claude after tool use):
    python auto-post-processor.py --tool Read --result '{...}' --filepath "..."
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

def log_token_usage(tool, tokens_used, tokens_saved, optimization):
    """Log token usage"""
    try:
        os.makedirs(os.path.dirname(TOKEN_LOG), exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] POST-{tool} | Used: {tokens_used} | Saved: {tokens_saved} | Optimization: {optimization}\n"

        with open(TOKEN_LOG, 'a', encoding='utf-8') as f:
            f.write(log_entry)
    except Exception as e:
        print(f"Warning: Could not log token usage: {e}", file=sys.stderr)

def estimate_tokens(text):
    """Rough token estimation (4 chars ≈ 1 token)"""
    if not text:
        return 0
    return len(str(text)) // 4

def update_cache(filepath, content):
    """Update tiered cache with content"""
    try:
        subprocess.run(
            ["python", os.path.join(MEMORY_DIR, "tiered-cache.py"),
             "--set-file", filepath, "--content", content[:10000]],  # Limit content size
            capture_output=True,
            text=True,
            timeout=5
        )
    except:
        pass

def extract_essentials(tool, result):
    """Extract essential info from tool result"""
    if tool == 'Read':
        # For Read tool, extract summary
        content = result.get('content', '')
        lines = content.split('\n') if content else []

        return {
            'line_count': len(lines),
            'first_10_lines': '\n'.join(lines[:10]),
            'last_10_lines': '\n'.join(lines[-10:]) if len(lines) > 10 else '',
            'total_chars': len(content),
            'estimated_tokens': estimate_tokens(content)
        }

    elif tool == 'Grep':
        # For Grep, summarize matches
        matches = result.get('matches', [])
        return {
            'match_count': len(matches),
            'files_matched': len(set(m.get('file') for m in matches if 'file' in m)),
            'estimated_tokens': estimate_tokens(str(matches))
        }

    elif tool == 'Glob':
        # For Glob, count files
        files = result.get('files', [])
        return {
            'file_count': len(files),
            'estimated_tokens': estimate_tokens(str(files))
        }

    return {}

def process_read_result(filepath, result):
    """Process Read tool result"""
    content = result.get('content', '')
    tokens_used = estimate_tokens(content)

    # Update cache
    if filepath:
        update_cache(filepath, content)

    # Extract essentials
    essentials = extract_essentials('Read', {'content': content})

    # Log
    log_token_usage('Read', tokens_used, 0, 'cached_for_future')

    return {
        'processed': True,
        'tokens_used': tokens_used,
        'essentials': essentials,
        'cached': True
    }

def process_grep_result(result):
    """Process Grep tool result"""
    essentials = extract_essentials('Grep', result)
    tokens_used = essentials.get('estimated_tokens', 0)

    # Log
    log_token_usage('Grep', tokens_used, 0, 'result_processed')

    return {
        'processed': True,
        'tokens_used': tokens_used,
        'essentials': essentials
    }

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Auto Post Processor')
    parser.add_argument('--tool', required=True, choices=['Read', 'Grep', 'Glob'])
    parser.add_argument('--result', required=True, help='Tool result as JSON')
    parser.add_argument('--filepath', help='File path (for Read tool)')

    args = parser.parse_args()

    try:
        result = json.loads(args.result)
    except:
        print(json.dumps({'error': 'Invalid JSON result'}))
        return

    if args.tool == 'Read':
        processed = process_read_result(args.filepath, result)
    elif args.tool == 'Grep':
        processed = process_grep_result(result)
    else:
        processed = {'processed': False, 'message': 'Tool not supported yet'}

    print(json.dumps(processed, indent=2))

if __name__ == "__main__":
    main()

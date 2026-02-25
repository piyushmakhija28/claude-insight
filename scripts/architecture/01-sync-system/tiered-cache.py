#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tiered Caching System for Token Optimization
Hot/Warm/Cold cache tiers based on access frequency

Tiers:
- HOT (5+ accesses in last hour): Full content in memory
- WARM (3-4 accesses): Summary cached
- COLD (1-2 accesses): No caching

Usage:
    python tiered-cache.py --get-file "{filepath}"
    python tiered-cache.py --set-file "{filepath}" --content "{content}"
    python tiered-cache.py --get-tier "{filepath}"
    python tiered-cache.py --stats
"""

import sys
import os
import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

CACHE_DIR = os.path.expanduser("~/.claude/memory/.cache")
CACHE_INDEX = os.path.join(CACHE_DIR, "tiered-index.json")
HOT_THRESHOLD = 5  # 5+ accesses = HOT
WARM_THRESHOLD = 3  # 3-4 accesses = WARM
TIME_WINDOW = 3600  # 1 hour in seconds

def ensure_cache_dir():
    """Ensure cache directory exists"""
    os.makedirs(CACHE_DIR, exist_ok=True)

def load_index():
    """Load cache index"""
    if not os.path.exists(CACHE_INDEX):
        return {}

    try:
        with open(CACHE_INDEX, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def save_index(index):
    """Save cache index"""
    try:
        with open(CACHE_INDEX, 'w', encoding='utf-8') as f:
            json.dump(index, f, indent=2)
    except Exception as e:
        print(f"Error saving index: {e}", file=sys.stderr)

def file_hash(filepath):
    """Generate hash for filepath"""
    return hashlib.md5(filepath.encode()).hexdigest()

def cleanup_old_accesses(accesses, time_window):
    """Remove accesses older than time window"""
    cutoff = datetime.now().timestamp() - time_window
    return [ts for ts in accesses if ts > cutoff]

def get_tier(filepath):
    """Determine cache tier for file"""
    index = load_index()
    fhash = file_hash(filepath)

    if fhash not in index:
        return "COLD", 0

    entry = index[fhash]

    # Cleanup old accesses
    accesses = cleanup_old_accesses(entry.get('accesses', []), TIME_WINDOW)
    access_count = len(accesses)

    if access_count >= HOT_THRESHOLD:
        return "HOT", access_count
    elif access_count >= WARM_THRESHOLD:
        return "WARM", access_count
    else:
        return "COLD", access_count

def record_access(filepath):
    """Record file access"""
    ensure_cache_dir()
    index = load_index()
    fhash = file_hash(filepath)

    if fhash not in index:
        index[fhash] = {
            'filepath': filepath,
            'accesses': [],
            'created': datetime.now().isoformat()
        }

    # Add current access
    index[fhash]['accesses'].append(datetime.now().timestamp())

    # Cleanup old accesses
    index[fhash]['accesses'] = cleanup_old_accesses(
        index[fhash]['accesses'],
        TIME_WINDOW
    )

    index[fhash]['last_access'] = datetime.now().isoformat()

    save_index(index)

    # Return current tier
    tier, count = get_tier(filepath)
    return tier, count

def cache_content(filepath, content, tier):
    """Cache file content based on tier"""
    ensure_cache_dir()
    fhash = file_hash(filepath)
    cache_file = os.path.join(CACHE_DIR, f"{fhash}.cache")

    if tier == "HOT":
        # Store full content
        cache_data = {
            'tier': 'HOT',
            'filepath': filepath,
            'content': content,
            'size': len(content),
            'cached_at': datetime.now().isoformat()
        }
    elif tier == "WARM":
        # Store summary only
        lines = content.split('\n')
        summary = '\n'.join(lines[:50]) + '\n... (truncated)'
        cache_data = {
            'tier': 'WARM',
            'filepath': filepath,
            'summary': summary,
            'line_count': len(lines),
            'cached_at': datetime.now().isoformat()
        }
    else:
        # COLD: No caching
        return None

    try:
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f)
        return cache_file
    except Exception as e:
        print(f"Error caching content: {e}", file=sys.stderr)
        return None

def get_cached_content(filepath):
    """Get cached content if available"""
    fhash = file_hash(filepath)
    cache_file = os.path.join(CACHE_DIR, f"{fhash}.cache")

    if not os.path.exists(cache_file):
        return None

    try:
        with open(cache_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return None

def get_stats():
    """Get cache statistics"""
    index = load_index()

    hot_count = 0
    warm_count = 0
    cold_count = 0

    for fhash, entry in index.items():
        tier, _ = get_tier(entry['filepath'])
        if tier == "HOT":
            hot_count += 1
        elif tier == "WARM":
            warm_count += 1
        else:
            cold_count += 1

    return {
        'total_files': len(index),
        'hot': hot_count,
        'warm': warm_count,
        'cold': cold_count,
        'cache_dir': CACHE_DIR
    }

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Tiered Caching System')
    parser.add_argument('--get-file', help='Get cached content for file')
    parser.add_argument('--set-file', help='Cache file content')
    parser.add_argument('--content', help='File content to cache')
    parser.add_argument('--get-tier', help='Get cache tier for file')
    parser.add_argument('--stats', action='store_true', help='Show cache statistics')

    args = parser.parse_args()

    if args.stats:
        stats = get_stats()
        print(json.dumps(stats, indent=2))
        return

    if args.get_tier:
        tier, count = get_tier(args.get_tier)
        print(json.dumps({
            'filepath': args.get_tier,
            'tier': tier,
            'access_count': count
        }, indent=2))
        return

    if args.get_file:
        # Record access
        tier, count = record_access(args.get_file)

        # Try to get cached content
        cached = get_cached_content(args.get_file)

        if cached:
            print(json.dumps({
                'filepath': args.get_file,
                'tier': tier,
                'access_count': count,
                'cache_hit': True,
                'cached_data': cached
            }, indent=2))
        else:
            print(json.dumps({
                'filepath': args.get_file,
                'tier': tier,
                'access_count': count,
                'cache_hit': False,
                'message': 'No cached content, read from disk'
            }, indent=2))
        return

    if args.set_file and args.content:
        tier, count = record_access(args.set_file)
        cache_file = cache_content(args.set_file, args.content, tier)

        print(json.dumps({
            'filepath': args.set_file,
            'tier': tier,
            'access_count': count,
            'cached': cache_file is not None,
            'cache_file': cache_file
        }, indent=2))
        return

    parser.print_help()

if __name__ == "__main__":
    main()

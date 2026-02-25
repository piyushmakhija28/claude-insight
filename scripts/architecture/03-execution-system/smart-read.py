#!/usr/bin/env python3
"""
Smart Read - Automatically optimized file reading

Usage:
    python smart-read.py <filepath> [options]

Features:
    - Auto-detects file size
    - Suggests offset/limit for large files
    - Shows file summary first
    - Provides reading strategy

Instead of manually deciding offset/limit, this script recommends it.
"""

import os
import sys
from pathlib import Path

def analyze_file(filepath):
    """Analyze file and recommend reading strategy"""

    if not os.path.exists(filepath):
        return {"error": f"File not found: {filepath}"}

    # Get file stats
    size = os.path.getsize(filepath)
    size_kb = size / 1024
    size_mb = size_kb / 1024

    # Count lines (for text files)
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            lines = sum(1 for _ in f)
    except:
        lines = 0

    # Determine strategy
    strategy = {}

    if lines == 0:
        strategy = {
            "type": "binary",
            "recommendation": "Binary file - use file metadata only",
            "command": f"file {filepath}",
            "read": False
        }
    elif lines < 100:
        strategy = {
            "type": "small",
            "recommendation": "Small file - read full content",
            "command": f"Read {filepath}",
            "read": True,
            "params": {}
        }
    elif lines < 500:
        strategy = {
            "type": "medium",
            "recommendation": "Medium file - read full or with limit",
            "command": f"Read {filepath}",
            "read": True,
            "params": {"limit": 500}
        }
    elif lines < 2000:
        strategy = {
            "type": "large",
            "recommendation": "Large file - use offset/limit",
            "command": f"Read {filepath} (offset=0, limit=500)",
            "read": True,
            "params": {"offset": 0, "limit": 500}
        }
    else:
        strategy = {
            "type": "very_large",
            "recommendation": "Very large file - read in chunks or use Grep",
            "command": f"Grep pattern {filepath} --head_limit 100",
            "read": False,
            "alternative": f"Read {filepath} (offset=0, limit=500) for first chunk"
        }

    return {
        "filepath": filepath,
        "size_bytes": size,
        "size_kb": round(size_kb, 2),
        "size_mb": round(size_mb, 2),
        "lines": lines,
        "strategy": strategy
    }

def main():
    if len(sys.argv) < 2:
        print("Usage: python smart-read.py <filepath>")
        print("\nExamples:")
        print("  python smart-read.py /path/to/file.java")
        print("  python smart-read.py C:\\Users\\user\\file.ts")
        sys.exit(1)

    filepath = sys.argv[1]
    result = analyze_file(filepath)

    if "error" in result:
        print(f"ERROR: {result['error']}")
        sys.exit(1)

    # Display results
    print(f"\n{'='*60}")
    print(f"SMART READ ANALYSIS")
    print(f"{'='*60}\n")

    print(f"File: {result['filepath']}")
    print(f"Size: {result['size_kb']:.2f} KB ({result['size_bytes']} bytes)")
    print(f"Lines: {result['lines']:,}")
    print(f"Type: {result['strategy']['type'].upper()}")
    print()

    print(f"RECOMMENDATION:")
    print(f"  {result['strategy']['recommendation']}")
    print()

    print(f"COMMAND:")
    print(f"  {result['strategy']['command']}")

    if 'alternative' in result['strategy']:
        print(f"\nALTERNATIVE:")
        print(f"  {result['strategy']['alternative']}")

    if result['strategy']['read'] and 'params' in result['strategy']:
        params = result['strategy']['params']
        if params:
            print(f"\nPARAMETERS:")
            for key, value in params.items():
                print(f"  {key}: {value}")

    print(f"\n{'='*60}\n")

    return 0

if __name__ == "__main__":
    sys.exit(main())

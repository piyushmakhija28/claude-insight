#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File Type Optimizer
Optimize file reading based on file type

Usage:
    python file-type-optimizer.py --file "{filepath}" --purpose "{purpose}"
"""

import sys
import os
import json
import subprocess

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

def get_file_type(filepath):
    """Detect file type"""
    ext = os.path.splitext(filepath)[1].lower()

    type_map = {
        '.json': 'json',
        '.yml': 'yaml',
        '.yaml': 'yaml',
        '.log': 'log',
        '.md': 'markdown',
        '.java': 'code',
        '.ts': 'code',
        '.js': 'code',
        '.py': 'code',
        '.properties': 'config',
        '.xml': 'config',
        '.png': 'binary',
        '.jpg': 'binary',
        '.jar': 'binary',
    }

    return type_map.get(ext, 'text')

def optimize_read(filepath, purpose='general'):
    """Get optimized read strategy"""
    file_type = get_file_type(filepath)

    strategies = {
        'json': {
            'structure': 'Use jq to get keys only',
            'specific_key': 'Use jq .path.to.key',
            'general': 'Read with offset/limit'
        },
        'yaml': {
            'structure': 'Use yq to get keys',
            'specific_key': 'Use yq .path.to.key',
            'general': 'Read with offset/limit'
        },
        'log': {
            'recent': 'tail -100',
            'errors': 'grep ERROR | tail -50',
            'general': 'tail -200'
        },
        'markdown': {
            'structure': 'grep "^##" (headers only)',
            'section': 'Read specific section by header',
            'general': 'Read with offset/limit'
        },
        'code': {
            'structure': 'AST parser or grep class/function',
            'imports': 'Read offset=0 limit=20',
            'function': 'grep function_name -A 20',
            'general': 'Read with offset/limit'
        },
        'config': {
            'general': 'Read full (usually small)'
        },
        'binary': {
            'general': 'file command (metadata only, never content)'
        }
    }

    strategy = strategies.get(file_type, {}).get(purpose, 'Read full file')

    return {
        'filepath': filepath,
        'file_type': file_type,
        'purpose': purpose,
        'recommended_strategy': strategy,
        'command_hint': generate_command(file_type, filepath, purpose)
    }

def generate_command(file_type, filepath, purpose):
    """Generate optimized command"""
    commands = {
        'json': {
            'structure': f'jq "keys" "{filepath}"',
            'general': f'jq . "{filepath}" | head -50'
        },
        'yaml': {
            'structure': f'yq eval "keys" "{filepath}"',
            'general': f'cat "{filepath}" | head -50'
        },
        'log': {
            'recent': f'tail -100 "{filepath}"',
            'errors': f'grep ERROR "{filepath}" | tail -50'
        },
        'markdown': {
            'structure': f'grep "^##" "{filepath}"',
        },
        'code': {
            'structure': f'grep -E "^(class|interface|function|def)" "{filepath}"',
            'imports': f'head -20 "{filepath}"'
        },
        'binary': {
            'general': f'file "{filepath}"'
        }
    }

    return commands.get(file_type, {}).get(purpose, f'cat "{filepath}"')

def main():
    import argparse
    parser = argparse.ArgumentParser(description='File Type Optimizer')
    parser.add_argument('--file', required=True, help='File path')
    parser.add_argument('--purpose', default='general',
                       help='Purpose: structure, recent, errors, imports, function, specific_key, section')

    args = parser.parse_args()

    result = optimize_read(args.file, args.purpose)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()

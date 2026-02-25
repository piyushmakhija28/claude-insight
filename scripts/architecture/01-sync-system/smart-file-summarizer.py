#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Smart File Summarizer
Generate intelligent summaries for large files

Strategies:
- First 50 + Last 50 lines (sandwich read)
- AST-based for code files
- Cached summaries

Usage:
    python smart-file-summarizer.py --file "{filepath}" --strategy "{strategy}"
"""

import sys
import os
import json

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

def get_file_size(filepath):
    """Get file line count"""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            return sum(1 for _ in f)
    except:
        return 0

def sandwich_read(filepath, head_lines=50, tail_lines=50):
    """Read first N and last N lines"""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()

        total_lines = len(lines)

        if total_lines <= (head_lines + tail_lines):
            return {
                'strategy': 'full_read',
                'content': ''.join(lines),
                'lines': total_lines
            }

        head = ''.join(lines[:head_lines])
        tail = ''.join(lines[-tail_lines:])
        skipped = total_lines - head_lines - tail_lines

        summary = f"{head}\n... [{skipped} lines skipped] ...\n\n{tail}"

        return {
            'strategy': 'sandwich',
            'summary': summary,
            'head_lines': head_lines,
            'tail_lines': tail_lines,
            'skipped_lines': skipped,
            'total_lines': total_lines,
            'token_savings': f"{int((skipped / total_lines) * 100)}%"
        }
    except Exception as e:
        return {'error': str(e)}

def ast_summary(filepath):
    """Generate AST-based summary for code"""
    ext = os.path.splitext(filepath)[1].lower()

    if ext == '.java':
        return java_summary(filepath)
    elif ext in ['.ts', '.js']:
        return typescript_summary(filepath)
    elif ext == '.py':
        return python_summary(filepath)
    else:
        return {'error': 'AST not supported for this file type'}

def java_summary(filepath):
    """Extract Java structure"""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        # Simple regex-based extraction (TODO: Use proper parser)
        import re

        package = re.search(r'package\s+([\w.]+);', content)
        classes = re.findall(r'class\s+(\w+)', content)
        interfaces = re.findall(r'interface\s+(\w+)', content)
        methods = re.findall(r'(public|private|protected)\s+\w+\s+(\w+)\s*\(', content)

        return {
            'strategy': 'ast',
            'file_type': 'java',
            'package': package.group(1) if package else None,
            'classes': classes,
            'interfaces': interfaces,
            'methods': [m[1] for m in methods],
            'summary': f"Package: {package.group(1) if package else 'N/A'}\nClasses: {', '.join(classes)}\nMethods: {len(methods)}"
        }
    except Exception as e:
        return {'error': str(e)}

def typescript_summary(filepath):
    """Extract TypeScript structure"""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        import re

        classes = re.findall(r'class\s+(\w+)', content)
        interfaces = re.findall(r'interface\s+(\w+)', content)
        functions = re.findall(r'function\s+(\w+)', content)
        exports = re.findall(r'export\s+(?:class|interface|function|const)\s+(\w+)', content)

        return {
            'strategy': 'ast',
            'file_type': 'typescript',
            'classes': classes,
            'interfaces': interfaces,
            'functions': functions,
            'exports': exports,
            'summary': f"Classes: {', '.join(classes)}\nInterfaces: {', '.join(interfaces)}\nFunctions: {len(functions)}"
        }
    except Exception as e:
        return {'error': str(e)}

def python_summary(filepath):
    """Extract Python structure using AST"""
    try:
        import ast

        with open(filepath, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read())

        classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]

        return {
            'strategy': 'ast',
            'file_type': 'python',
            'classes': classes,
            'functions': functions,
            'summary': f"Classes: {', '.join(classes)}\nFunctions: {', '.join(functions)}"
        }
    except Exception as e:
        return {'error': str(e)}

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Smart File Summarizer')
    parser.add_argument('--file', required=True, help='File path')
    parser.add_argument('--strategy', default='auto',
                       choices=['auto', 'sandwich', 'ast'],
                       help='Summarization strategy')

    args = parser.parse_args()

    # Auto-detect strategy
    if args.strategy == 'auto':
        ext = os.path.splitext(args.file)[1].lower()
        size = get_file_size(args.file)

        if size > 500 and ext in ['.java', '.ts', '.js', '.py']:
            args.strategy = 'ast'
        elif size > 100:
            args.strategy = 'sandwich'
        else:
            print(json.dumps({'message': 'File small enough, read normally'}))
            return

    # Execute strategy
    if args.strategy == 'sandwich':
        result = sandwich_read(args.file)
    elif args.strategy == 'ast':
        result = ast_summary(args.file)
    else:
        result = {'error': 'Unknown strategy'}

    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()

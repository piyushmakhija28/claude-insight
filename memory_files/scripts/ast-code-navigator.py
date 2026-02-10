#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AST-Based Code Navigator
Extract code structure without reading full files

Supports: Java, TypeScript, JavaScript, Python

Usage:
    python ast-code-navigator.py --file "{filepath}"
    python ast-code-navigator.py --file "{filepath}" --show-methods
"""

import sys
import os
import json
import re

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

def navigate_java(filepath, show_methods=False):
    """Extract Java file structure"""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        # Extract structure
        package = re.search(r'package\s+([\w.]+);', content)
        imports = re.findall(r'import\s+([\w.]+);', content)
        classes = re.findall(r'(?:public\s+)?class\s+(\w+)', content)
        interfaces = re.findall(r'(?:public\s+)?interface\s+(\w+)', content)

        result = {
            'file': filepath,
            'language': 'java',
            'package': package.group(1) if package else None,
            'imports': imports[:10],  # First 10 imports
            'classes': classes,
            'interfaces': interfaces,
        }

        if show_methods:
            methods = re.findall(
                r'(public|private|protected)\s+(?:static\s+)?(\w+)\s+(\w+)\s*\([^)]*\)',
                content
            )
            result['methods'] = [
                {
                    'visibility': m[0],
                    'return_type': m[1],
                    'name': m[2]
                }
                for m in methods
            ]

        return result

    except Exception as e:
        return {'error': str(e)}

def navigate_typescript(filepath, show_methods=False):
    """Extract TypeScript file structure"""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        imports = re.findall(r'import\s+.*?from\s+[\'"]([^\'"]+)[\'"]', content)
        classes = re.findall(r'export\s+class\s+(\w+)', content)
        interfaces = re.findall(r'export\s+interface\s+(\w+)', content)
        functions = re.findall(r'export\s+function\s+(\w+)', content)
        consts = re.findall(r'export\s+const\s+(\w+)', content)

        result = {
            'file': filepath,
            'language': 'typescript',
            'imports': imports[:10],
            'classes': classes,
            'interfaces': interfaces,
            'functions': functions,
            'constants': consts,
        }

        if show_methods:
            # Extract method signatures from classes
            class_methods = re.findall(
                r'(\w+)\s*\([^)]*\)\s*:\s*(\w+)',
                content
            )
            result['methods'] = [
                {'name': m[0], 'return_type': m[1]}
                for m in class_methods
            ]

        return result

    except Exception as e:
        return {'error': str(e)}

def navigate_python(filepath, show_methods=False):
    """Extract Python file structure"""
    try:
        import ast

        with open(filepath, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read(), filename=filepath)

        imports = []
        classes = []
        functions = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                if isinstance(node, ast.Import):
                    imports.extend([alias.name for alias in node.names])
                else:
                    imports.append(node.module)
            elif isinstance(node, ast.ClassDef):
                classes.append({
                    'name': node.name,
                    'line': node.lineno,
                    'methods': [m.name for m in node.body if isinstance(m, ast.FunctionDef)] if show_methods else []
                })
            elif isinstance(node, ast.FunctionDef):
                if not any(node in cls.body for cls in ast.walk(tree) if isinstance(cls, ast.ClassDef)):
                    functions.append({
                        'name': node.name,
                        'line': node.lineno
                    })

        return {
            'file': filepath,
            'language': 'python',
            'imports': imports[:10],
            'classes': classes,
            'functions': functions,
        }

    except Exception as e:
        return {'error': str(e)}

def navigate_code(filepath, show_methods=False):
    """Navigate code file based on extension"""
    ext = os.path.splitext(filepath)[1].lower()

    if ext == '.java':
        return navigate_java(filepath, show_methods)
    elif ext in ['.ts', '.tsx']:
        return navigate_typescript(filepath, show_methods)
    elif ext == '.py':
        return navigate_python(filepath, show_methods)
    else:
        return {'error': f'Unsupported file type: {ext}'}

def main():
    import argparse
    parser = argparse.ArgumentParser(description='AST Code Navigator')
    parser.add_argument('--file', required=True, help='Code file path')
    parser.add_argument('--show-methods', action='store_true',
                       help='Show method signatures')

    args = parser.parse_args()

    result = navigate_code(args.file, args.show_methods)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()

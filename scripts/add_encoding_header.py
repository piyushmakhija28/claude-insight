#!/usr/bin/env python3
"""
Add UTF-8 encoding reconfiguration to all Python scripts
This ensures all output works on Windows console (cp1252)
"""
import os
import re
from pathlib import Path

ENCODING_HEADER = '''
# Fix encoding for Windows console
import sys
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    try:
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        import io
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
'''

def has_encoding_fix(content):
    """Check if file already has encoding fix"""
    return 'sys.stdout.reconfigure' in content or 'reconfigure(encoding=' in content

def add_encoding_to_file(file_path):
    """Add encoding fix to a Python file"""
    try:
        # Read file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Skip if already has fix
        if has_encoding_fix(content):
            return False, "Already has encoding fix"

        # Find where to insert (after shebang and docstring)
        lines = content.split('\n')
        insert_index = 0

        # Skip shebang
        if lines and lines[0].startswith('#!'):
            insert_index = 1

        # Skip module docstring
        in_docstring = False
        docstring_start = -1
        for i in range(insert_index, len(lines)):
            line = lines[i].strip()

            # Check for docstring start
            if line.startswith('"""') or line.startswith("'''"):
                if not in_docstring:
                    in_docstring = True
                    docstring_start = i
                    # Check if it's a one-liner docstring
                    if line.count('"""') == 2 or line.count("'''") == 2:
                        insert_index = i + 1
                        break
                else:
                    # End of docstring
                    insert_index = i + 1
                    break
            elif in_docstring:
                continue
            elif line and not line.startswith('#'):
                # First non-comment, non-docstring line
                insert_index = i
                break

        # Insert encoding fix
        lines.insert(insert_index, ENCODING_HEADER)
        new_content = '\n'.join(lines)

        # Write back
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

        return True, "Added encoding fix"

    except Exception as e:
        return False, f"Error: {e}"

def main():
    """Add encoding fix to all Python files"""
    memory_path = Path.home() / '.claude' / 'memory'

    if not memory_path.exists():
        print(f"[ERROR] Memory path not found: {memory_path}")
        return

    print("=" * 70)
    print("Encoding Header Adder - Starting...")
    print("=" * 70)
    print()

    # Find all Python files
    python_files = list(memory_path.rglob('*.py'))

    print(f"[INFO] Found {len(python_files)} Python files")
    print()

    fixed_count = 0

    for file_path in python_files:
        fixed, reason = add_encoding_to_file(file_path)
        if fixed:
            fixed_count += 1
            print(f"[ADDED] {file_path.relative_to(memory_path)}")
        elif "Error" in reason:
            print(f"[ERROR] {file_path.relative_to(memory_path)}: {reason}")

    print()
    print("=" * 70)
    print(f"[DONE] Added encoding fix to {fixed_count} files")
    print("=" * 70)

if __name__ == '__main__':
    main()

"""
Batch rename script to update all references from claude-monitoring-system to claude-insight
"""
import os
import re
from pathlib import Path

# Define replacements
replacements = {
    'Claude Monitoring System': 'Claude Insight',
    'claude-monitoring-system': 'claude-insight',
    'Claude monitoring system': 'Claude Insight',
    'CLAUDE MONITORING SYSTEM': 'CLAUDE INSIGHT',
}

# Extensions to process
extensions = ['.py', '.md', '.html', '.txt', '.json', '.yml', '.yaml']

# Directories to skip
skip_dirs = {'__pycache__', '.git', 'node_modules', 'venv', '.idea'}

def should_process_file(file_path):
    """Check if file should be processed"""
    # Skip this script itself
    if file_path.name == 'rename_references.py':
        return False

    # Check extension
    if file_path.suffix not in extensions:
        return False

    # Check if in skip directory
    for skip_dir in skip_dirs:
        if skip_dir in file_path.parts:
            return False

    return True

def update_file(file_path):
    """Update a single file"""
    try:
        # Read file
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        original_content = content

        # Apply replacements
        for old, new in replacements.items():
            content = content.replace(old, new)

        # Write back only if changed
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"[OK] Updated: {file_path}")
            return True
        return False
    except Exception as e:
        print(f"[ERROR] processing {file_path}: {e}")
        return False

def main():
    """Main function"""
    root_dir = Path(__file__).parent
    print(f"Scanning directory: {root_dir}")
    print(f"Looking for references to update...\n")

    updated_count = 0
    scanned_count = 0

    # Walk through all files
    for file_path in root_dir.rglob('*'):
        if file_path.is_file() and should_process_file(file_path):
            scanned_count += 1
            if update_file(file_path):
                updated_count += 1

    print(f"\nComplete!")
    print(f"Scanned: {scanned_count} files")
    print(f"Updated: {updated_count} files")

if __name__ == '__main__':
    main()

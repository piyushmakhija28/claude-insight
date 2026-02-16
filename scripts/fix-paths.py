#!/usr/bin/env python
"""
Batch fix hardcoded ~/.claude/memory paths in service files
"""

import re
from pathlib import Path

# Files to fix
FILES_TO_FIX = [
    'src/services/ai/anomaly_detector.py',
    'src/services/ai/predictive_analytics.py',
    'src/services/monitoring/automation_tracker.py',
    'src/services/monitoring/log_parser.py',
    'src/services/monitoring/memory_system_monitor.py',
    'src/services/monitoring/metrics_collector.py',
    'src/services/monitoring/optimization_tracker.py',
    'src/services/monitoring/policy_checker.py',
    'src/services/monitoring/session_tracker.py',
    'src/services/monitoring/skill_agent_tracker.py',
    'src/services/widgets/community_manager.py',
    'src/services/notifications/alert_routing.py',
    'src/services/notifications/alert_sender.py',
    'src/services/notifications/notification_manager.py',
]

PROJECT_ROOT = Path(__file__).parent.parent

def fix_file(file_path):
    """Fix hardcoded paths in a file"""
    print(f"Fixing: {file_path}")

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content

    # Add import if not present
    if 'from utils.path_resolver import' not in content:
        # Find where to add import (after existing imports)
        import_pattern = r'(from pathlib import Path\n)'
        replacement = r'\1import sys\n\n# Add path resolver for portable paths\nsys.path.insert(0, str(Path(__file__).parent.parent.parent))\nfrom utils.path_resolver import get_data_dir, get_logs_dir\n'
        content = re.sub(import_pattern, replacement, content)

    # Replace hardcoded paths
    replacements = [
        (r"Path\.home\(\) / '\.claude' / 'memory'", "get_data_dir()"),
        (r'Path\.home\(\) / "\.claude" / "memory"', 'get_data_dir()'),
        (r"self\.memory_dir = Path\.home\(\) / '\.claude' / 'memory'", "self.memory_dir = get_data_dir()"),
        (r'self\.memory_dir = Path\.home\(\) / "\.claude" / "memory"', 'self.memory_dir = get_data_dir()'),
        (r"self\.data_dir = Path\.home\(\) / '\.claude' / 'memory' / '(\w+)'", r"self.data_dir = get_data_dir('\1')"),
        (r'self\.data_dir = Path\.home\(\) / "\.claude" / "memory" / "(\w+)"', r'self.data_dir = get_data_dir("\1")'),
    ]

    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content)

    if content != original:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  [OK] Fixed!")
        return True
    else:
        print(f"  - No changes needed")
        return False

def main():
    """Main entry point"""
    print("=" * 60)
    print("Fixing hardcoded paths in service files...")
    print("=" * 60)
    print()

    fixed_count = 0

    for file in FILES_TO_FIX:
        file_path = PROJECT_ROOT / file
        if file_path.exists():
            if fix_file(file_path):
                fixed_count += 1
        else:
            print(f"WARNING: File not found: {file}")

    print()
    print("=" * 60)
    print(f"Fixed {fixed_count} / {len(FILES_TO_FIX)} files")
    print("=" * 60)

if __name__ == "__main__":
    main()

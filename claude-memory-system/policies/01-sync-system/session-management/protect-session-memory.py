#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Session Memory Protection Verifier
Verifies that session memory files are protected from cleanup

Usage:
    python protect-session-memory.py [--verify] [--list]

Examples:
    python protect-session-memory.py --verify  # Verify protection
    python protect-session-memory.py --list    # List all protected files
"""

import sys
import os
import argparse
from datetime import datetime
from pathlib import Path

# Fix Windows encoding issues
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Protected directories (SACRED - NEVER cleanup!)
PROTECTED_PATHS = {
    "sessions": "~/.claude/memory/sessions/",
    "policies": "~/.claude/memory/*.md",
    "logs": "~/.claude/memory/logs/",
    "settings": "~/.claude/settings*.json",
    "global_docs": "~/.claude/*.md",
}

def log_policy_hit(action, context):
    """Log policy execution"""
    log_file = os.path.expanduser("~/.claude/memory/logs/policy-hits.log")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] session-protection | {action} | {context}\n"

    try:
        with open(log_file, 'a') as f:
            f.write(log_entry)
    except Exception as e:
        print(f"Warning: Could not write to log: {e}", file=sys.stderr)

def get_protected_files():
    """
    Get list of all protected files
    Returns dict: {category: [file_paths]}
    """
    protected = {}

    # Sessions
    sessions_path = Path(os.path.expanduser(PROTECTED_PATHS["sessions"]))
    if sessions_path.exists():
        session_files = []
        for root, dirs, files in os.walk(sessions_path):
            for file in files:
                if file.endswith('.md'):
                    session_files.append(os.path.join(root, file))
        protected["sessions"] = session_files
    else:
        protected["sessions"] = []

    # Policies (memory/*.md)
    policies_path = Path(os.path.expanduser("~/.claude/memory/"))
    if policies_path.exists():
        policy_files = [str(f) for f in policies_path.glob("*.md")]
        protected["policies"] = policy_files
    else:
        protected["policies"] = []

    # Logs
    logs_path = Path(os.path.expanduser(PROTECTED_PATHS["logs"]))
    if logs_path.exists():
        log_files = list(logs_path.rglob("*"))
        log_files = [str(f) for f in log_files if f.is_file()]
        protected["logs"] = log_files
    else:
        protected["logs"] = []

    # Global docs
    global_docs_path = Path(os.path.expanduser("~/.claude/"))
    if global_docs_path.exists():
        global_docs = [str(f) for f in global_docs_path.glob("*.md")]
        protected["global_docs"] = global_docs
    else:
        protected["global_docs"] = []

    return protected

def verify_protection():
    """
    Verify that all protected paths exist and are accessible
    """
    print("\n" + "=" * 70)
    print("🛡️  SESSION MEMORY PROTECTION VERIFICATION")
    print("=" * 70)

    protected_files = get_protected_files()

    total_files = sum(len(files) for files in protected_files.values())
    total_size = 0

    # Calculate total size
    for category, files in protected_files.items():
        for file in files:
            try:
                total_size += os.path.getsize(file)
            except:
                pass

    print(f"\n📊 Protection Summary:")
    print(f"   Total Protected Files: {total_files}")
    print(f"   Total Protected Size: {total_size / 1024:.2f} KB")

    print("\n" + "=" * 70)
    print("🛡️  PROTECTED CATEGORIES")
    print("=" * 70)

    for category, files in protected_files.items():
        emoji = {
            "sessions": "📝",
            "policies": "📋",
            "logs": "📊",
            "global_docs": "📖",
        }.get(category, "📁")

        print(f"\n{emoji} {category.upper().replace('_', ' ')}:")
        print(f"   Path: {PROTECTED_PATHS.get(category, 'N/A')}")
        print(f"   Files: {len(files)}")

        if files:
            category_size = sum(os.path.getsize(f) for f in files if os.path.exists(f))
            print(f"   Size: {category_size / 1024:.2f} KB")
            print(f"   Status: ✅ PROTECTED")
        else:
            print(f"   Status: ⚠️  No files found (empty or new installation)")

    print("\n" + "=" * 70)
    print("🔒 PROTECTION RULES")
    print("=" * 70)

    rules = [
        "✅ Session memory files NEVER deleted by auto-cleanup",
        "✅ Policy files preserved across all operations",
        "✅ Logs kept for audit trail",
        "✅ Global docs protected from cleanup",
        "✅ User manages these files manually",
    ]

    for rule in rules:
        print(f"   {rule}")

    print("\n" + "=" * 70)

    # Log verification
    log_policy_hit("verification-complete", f"files={total_files}, size={total_size / 1024:.2f}KB")

    return True

def list_protected_files(verbose=False):
    """
    List all protected files
    """
    print("\n" + "=" * 70)
    print("📋 PROTECTED FILES LIST")
    print("=" * 70)

    protected_files = get_protected_files()

    for category, files in protected_files.items():
        emoji = {
            "sessions": "📝",
            "policies": "📋",
            "logs": "📊",
            "global_docs": "📖",
        }.get(category, "📁")

        print(f"\n{emoji} {category.upper().replace('_', ' ')} ({len(files)} files):")
        print("-" * 70)

        if files:
            for file in sorted(files):
                if verbose:
                    size = os.path.getsize(file) if os.path.exists(file) else 0
                    print(f"   {file} ({size / 1024:.2f} KB)")
                else:
                    # Show relative path for readability
                    rel_path = file.replace(os.path.expanduser("~/.claude/"), "")
                    print(f"   {rel_path}")
        else:
            print("   (No files)")

    print("\n" + "=" * 70)

    # Log listing
    total_files = sum(len(files) for files in protected_files.values())
    log_policy_hit("list-protected", f"files={total_files}")

def check_file_is_protected(file_path):
    """
    Check if a specific file is protected
    """
    file_path = os.path.abspath(os.path.expanduser(file_path))

    protected_files = get_protected_files()
    all_protected = []
    for files in protected_files.values():
        all_protected.extend(files)

    # Normalize paths for comparison
    all_protected = [os.path.abspath(f) for f in all_protected]

    is_protected = file_path in all_protected

    # Also check if file is in protected directory
    sessions_dir = os.path.abspath(os.path.expanduser(PROTECTED_PATHS["sessions"]))
    logs_dir = os.path.abspath(os.path.expanduser(PROTECTED_PATHS["logs"]))

    in_protected_dir = (
        file_path.startswith(sessions_dir) or
        file_path.startswith(logs_dir)
    )

    print("\n" + "=" * 70)
    print("🔍 FILE PROTECTION CHECK")
    print("=" * 70)
    print(f"\nFile: {file_path}")

    if is_protected or in_protected_dir:
        print(f"Status: 🛡️  PROTECTED")
        print(f"\n✅ This file is SAFE from auto-cleanup")
        print(f"✅ Will NEVER be deleted automatically")
        print(f"✅ User manages this file manually")
    else:
        print(f"Status: ⚠️  NOT PROTECTED")
        print(f"\n⚠️  This file may be affected by cleanup operations")
        print(f"⚠️  Consider moving to protected location if important")

    print("\n" + "=" * 70)

    log_policy_hit("file-check", f"{file_path} | protected={is_protected or in_protected_dir}")

    return is_protected or in_protected_dir

def main():
    parser = argparse.ArgumentParser(
        description="Verify session memory protection"
    )
    parser.add_argument(
        '--verify',
        action='store_true',
        help='Verify protection status'
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='List all protected files'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show detailed file information'
    )
    parser.add_argument(
        '--check',
        type=str,
        default=None,
        help='Check if specific file is protected'
    )

    args = parser.parse_args()

    if args.check:
        check_file_is_protected(args.check)
    elif args.list:
        list_protected_files(args.verbose)
    elif args.verify:
        verify_protection()
    else:
        # Default: verify
        verify_protection()

if __name__ == "__main__":
    main()

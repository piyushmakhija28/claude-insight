#!/usr/bin/env python3
"""
Unicode Emoji Fixer - Replaces all emoji Unicode with [TEXT] equivalents
Fixes Windows cp1252 encoding issues in policy enforcement scripts
"""
import os
import re
from pathlib import Path

# Common emoji to text mappings
EMOJI_REPLACEMENTS = {
    '\U0001f9e0': '[BRAIN]',      # 🧠
    '\U0001f50d': '[SEARCH]',     # 🔍
    '\u2705': '[CHECK]',          # ✅
    '\u274c': '[CROSS]',          # ❌
    '\U0001f6a8': '[ALERT]',      # 🚨
    '\U0001f4cb': '[CLIPBOARD]',  # 📋
    '\U0001f3af': '[TARGET]',     # 🎯
    '\U0001f916': '[ROBOT]',      # 🤖
    '\U0001f527': '[WRENCH]',     # 🔧
    '\U0001f4ca': '[CHART]',      # 📊
    '\U0001f517': '[LINK]',       # 🔗
    '\U0001f4a1': '[BULB]',       # 💡
    '\U0001f512': '[LOCK]',       # 🔒
    '\U0001f4b0': '[MONEY]',      # 💰
    '\U0001f504': '[CYCLE]',      # 🔄
    '\U0001f4c4': '[PAGE]',       # 📄
    '\U0001f6e1': '[SHIELD]',     # 🛡️
    '\u26a1': '[ZAP]',            # ⚡
    '\U0001f680': '[ROCKET]',     # 🚀
    '\U0001f4be': '[FLOPPY]',     # 💾
    '\U0001f4a6': '[SWEAT]',      # 💦
    '\U0001f525': '[FIRE]',       # 🔥
    '\U0001f4aa': '[MUSCLE]',     # 💪
    '\U0001f440': '[EYES]',       # 👀
    '\U0001f446': '[UP]',         # 👆
    '\U0001f4d6': '[BOOK]',       # 📖
    '\U0001f9ea': '[TEST]',       # 🧪
    '\u23f8': '[PAUSE]',          # ⏸️
    '\u231b': '[TIMER]',          # ⏳
    '\U0001f534': '[RED]',        # 🔴
    '\U0001f7e2': '[GREEN]',      # 🟢
    '\U0001f7e1': '[YELLOW]',     # 🟡
    '\U0001f7e0': '[ORANGE]',     # 🟠
    '\U0001f535': '[BLUE]',       # 🔵
    '\U0001f6ab': '[PROHIBITED]', # 🚫
    '\u2139': '[INFO]',           # ℹ️
    '\u2714': '[CHECKMARK]',      # ✔️
    '\u2b07': '[DOWN]',           # ⬇️
    '\u27a1': '[RIGHT]',          # ➡️
    '\U0001f9f0': '[TOOLBOX]',    # 🧰
    '\u2753': '[QUESTION]',       # ❓
    '\u2757': '[EXCLAMATION]',    # ❗
    '\u26a0': '[WARNING]',        # ⚠️
    '\u2611': '[CHECKBOX]',       # ☑️
    '\u2610': '[UNCHECKED]',      # ☐
    '\u25b6': '[PLAY]',           # ▶️
    '\u23f1': '[STOPWATCH]',      # ⏱️
    '\U0001f4dd': '[MEMO]',       # 📝
    '\U0001f4e6': '[PACKAGE]',    # 📦
    '\U0001f310': '[GLOBE]',      # 🌐
    '\U0001f4e2': '[LOUDSPEAKER]', # 📢
    '\U0001f50e': '[MAG_RIGHT]',  # 🔎
    '\U0001f4c5': '[CALENDAR]',   # 📅
    '\U0001f4c8': '[CHART_UP]',   # 📈
    '\U0001f4c9': '[CHART_DOWN]', # 📉
}

def fix_file_encoding(file_path):
    """Fix Unicode encoding in a single file"""
    try:
        # Read file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content
        changes = 0

        # Replace all emojis
        for emoji, replacement in EMOJI_REPLACEMENTS.items():
            if emoji in content:
                count = content.count(emoji)
                content = content.replace(emoji, replacement)
                changes += count

        # Also replace any other Unicode characters > \u007F with safe alternatives
        # Use regex to find any remaining problematic Unicode
        def replace_unknown_unicode(match):
            char = match.group(0)
            codepoint = ord(char)
            if codepoint > 127:
                return f'[U+{codepoint:04X}]'
            return char

        # Find Unicode characters that might cause issues
        content = re.sub(r'[\U00010000-\U0010FFFF]', replace_unknown_unicode, content)

        # Write back if changes were made
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, changes

        return False, 0

    except Exception as e:
        print(f"[ERROR] Failed to process {file_path}: {e}")
        return False, 0

def main():
    """Fix all Python files in the memory system"""
    memory_path = Path.home() / '.claude' / 'memory'

    if not memory_path.exists():
        print(f"[ERROR] Memory path not found: {memory_path}")
        return

    print("=" * 70)
    print("Unicode Encoding Fixer - Starting...")
    print("=" * 70)
    print()

    # Find all Python files
    python_files = list(memory_path.rglob('*.py'))

    print(f"[INFO] Found {len(python_files)} Python files")
    print()

    fixed_count = 0
    total_changes = 0

    for file_path in python_files:
        fixed, changes = fix_file_encoding(file_path)
        if fixed:
            fixed_count += 1
            total_changes += changes
            print(f"[FIXED] {file_path.relative_to(memory_path)} ({changes} replacements)")

    print()
    print("=" * 70)
    print(f"[DONE] Fixed {fixed_count} files ({total_changes} total replacements)")
    print("=" * 70)

    if fixed_count == 0:
        print("[INFO] No files needed fixing - all clean!")

if __name__ == '__main__':
    main()

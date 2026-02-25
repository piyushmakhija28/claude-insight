#!/usr/bin/env python
# Script Name: pre-tool-enforcer.py
# Version: 1.0.0
# Last Modified: 2026-02-19
# Description: PreToolUse hook - Level 3.6 (tool optimization) + Level 3.7 (failure prevention)
# Author: Claude Memory System
#
# Hook Type: PreToolUse
# Trigger: Runs BEFORE every tool call
# Exit 0 = Allow tool (may print hints to stdout)
# Exit 1 = BLOCK tool (prints reason to stderr)
#
# Policies enforced:
#   Level 3.6 - Tool Usage Optimization:
#     - Grep: warn if missing head_limit
#     - Read: warn if missing offset+limit (for large files)
#   Level 3.7 - Failure Prevention:
#     - Bash: BLOCK Windows-only commands (del, copy, dir, xcopy, etc.)
#     - Write/Edit/NotebookEdit: BLOCK Unicode chars in .py files on Windows
#
# Windows-safe: ASCII only, no Unicode chars

import sys
import json

# Unicode chars that CRASH Python on Windows (cp1252 encoding)
# Listed as escape sequences so THIS file stays ASCII-safe
UNICODE_DANGER = [
    '\u2705', '\u274c', '\u2728', '\U0001f4dd', '\u2192', '\u2193', '\u2191',
    '\u2713', '\u2717', '\u2022', '\u2605', '\U0001f680', '\u26a0', '\U0001f6a8',
    '\U0001f4ca', '\U0001f4cb', '\U0001f50d', '\u2b50', '\U0001f4c4', '\u270f',
    '\u2714', '\u2716', '\U0001f527', '\U0001f4a1', '\U0001f916', '\u2139',
    '\U0001f512', '\U0001f513', '\U0001f3af', '\u21d2', '\u2764', '\U0001f4a5',
    '\u2714', '\u25cf', '\u25cb', '\u25a0', '\u25a1', '\u2660', '\u2663',
    '\u2665', '\u2666', '\u00bb', '\u00ab', '\u2026', '\u2014', '\u2013',
    '\u201c', '\u201d', '\u2018', '\u2019', '\u00ae', '\u00a9', '\u2122',
    '\u00b7', '\u00b0', '\u00b1', '\u00d7', '\u00f7', '\u221e', '\u2248',
    '\u2260', '\u2264', '\u2265', '\u00bc', '\u00bd', '\u00be',
]

# Windows-only commands that fail in bash shell
# Format: (windows_cmd_prefix, bash_equivalent)
WINDOWS_CMDS = [
    ('del ',    'rm'),
    ('del\t',   'rm'),
    ('copy ',   'cp'),
    ('xcopy ',  'cp -r'),
    ('move ',   'mv'),
    ('ren ',    'mv'),
    ('md ',     'mkdir'),
    ('rd ',     'rmdir'),
    ('dir ',    'ls'),
    ('dir\n',   'ls'),
    ('type ',   'cat'),
    ('attrib ', 'chmod'),
    ('icacls ', 'chmod'),
    ('taskkill','kill'),
    ('tasklist','ps aux'),
    ('where ',  'which'),
    ('findstr ','grep'),
    ('cls\n',   'clear'),
    ('cls\r',   'clear'),
    ('cls',     'clear'),
    ('ipconfig','ifconfig / ip addr'),
    ('netstat ','netstat / ss'),
    ('systeminfo','uname -a'),
    ('schtasks ','cron'),
    ('sc ',     'systemctl'),
    ('net ',    'systemctl / id'),
    ('reg ',    'No equivalent in bash'),
    ('regedit', 'No equivalent in bash'),
    ('msiexec', 'No equivalent in bash'),
]


def check_bash(command):
    """Level 3.7: Detect Windows-only commands that fail in bash."""
    hints = []
    blocks = []
    cmd_stripped = command.strip()
    cmd_lower = cmd_stripped.lower()

    for win_cmd, bash_equiv in WINDOWS_CMDS:
        win_lower = win_cmd.lower()
        # Check if command starts with win_cmd or has it after newline/semicolon/&&
        if (cmd_lower.startswith(win_lower) or
                ('\n' + win_lower) in cmd_lower or
                ('; ' + win_lower) in cmd_lower or
                ('&& ' + win_lower) in cmd_lower):
            blocks.append(
                '[PRE-TOOL L3.7] BLOCKED - Windows command in bash shell!\n'
                '  Detected : ' + win_cmd.strip() + '\n'
                '  Use instead: ' + bash_equiv + '\n'
                '  Fix the command and retry.'
            )
            break  # One block message is enough

    return hints, blocks


def check_python_unicode(content):
    """Level 3.7: Detect Unicode chars in Python files (crash on Windows cp1252)."""
    blocks = []
    found_count = 0
    sample = []

    for char in UNICODE_DANGER:
        if char in content:
            found_count += 1
            if len(sample) < 5:
                sample.append(repr(char))

    if found_count > 0:
        blocks.append(
            '[PRE-TOOL L3.7] BLOCKED - Unicode chars in Python file!\n'
            '  Platform : Windows (cp1252 encoding)\n'
            '  Problem  : ' + str(found_count) + ' unicode char(s) will cause UnicodeEncodeError\n'
            '  Sample   : ' + ', '.join(sample) + '\n'
            '  Fix      : Replace with ASCII: [OK] [ERROR] [WARN] [INFO] -> * #\n'
            '  Rule     : NEVER use Unicode in Python scripts on Windows!'
        )

    return blocks


def check_write_edit(tool_name, tool_input):
    """Level 3.7: Check Python files for Unicode before writing."""
    hints = []
    blocks = []

    file_path = (
        tool_input.get('file_path', '') or
        tool_input.get('notebook_path', '') or
        ''
    )

    if file_path.endswith('.py'):
        content = (
            tool_input.get('content', '') or
            tool_input.get('new_string', '') or
            tool_input.get('new_source', '') or
            ''
        )
        if content:
            blocks.extend(check_python_unicode(content))

    return hints, blocks


def check_grep(tool_input):
    """Level 3.6: Grep optimization - warn about missing head_limit."""
    hints = []
    head_limit = tool_input.get('head_limit', 0)

    if not head_limit:
        hints.append(
            '[PRE-TOOL L3.6] Grep hint: head_limit not set - '
            'add head_limit=100 to save tokens (CLAUDE.md default rule)'
        )

    return hints, []


def check_read(tool_input):
    """Level 3.6: Read optimization - hint about offset+limit for large files."""
    hints = []
    limit = tool_input.get('limit')
    offset = tool_input.get('offset')

    if not limit and not offset:
        hints.append(
            '[PRE-TOOL L3.6] Read hint: No limit/offset set - '
            'if file >500 lines, use offset+limit to save tokens'
        )

    return hints, []


def main():
    # Read tool info from stdin
    try:
        raw = sys.stdin.read()
        if not raw or not raw.strip():
            sys.exit(0)
        data = json.loads(raw)
    except Exception:
        # Never block on parse errors
        sys.exit(0)

    tool_name = data.get('tool_name', '')
    tool_input = data.get('tool_input', {})

    if not isinstance(tool_input, dict):
        tool_input = {}

    all_hints = []
    all_blocks = []

    # Route to appropriate checker
    if tool_name == 'Bash':
        command = tool_input.get('command', '')
        h, b = check_bash(command)
        all_hints.extend(h)
        all_blocks.extend(b)

    elif tool_name in ('Write', 'Edit', 'NotebookEdit'):
        h, b = check_write_edit(tool_name, tool_input)
        all_hints.extend(h)
        all_blocks.extend(b)

    elif tool_name == 'Grep':
        h, b = check_grep(tool_input)
        all_hints.extend(h)
        all_blocks.extend(b)

    elif tool_name == 'Read':
        h, b = check_read(tool_input)
        all_hints.extend(h)
        all_blocks.extend(b)

    # Output hints to stdout (shown to Claude as context - non-blocking)
    for hint in all_hints:
        sys.stdout.write(hint + '\n')
    sys.stdout.flush()

    # Output blocks to stderr and exit 1 (BLOCKS the tool call)
    if all_blocks:
        for block in all_blocks:
            sys.stderr.write(block + '\n')
        sys.stderr.flush()
        sys.exit(1)

    sys.exit(0)


if __name__ == '__main__':
    main()

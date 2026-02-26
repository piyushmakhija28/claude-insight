#!/usr/bin/env python
# Script Name: pre-tool-enforcer.py
# Version: 2.3.0 (Multi-Window Isolation)
# Last Modified: 2026-02-24
# Description: PreToolUse hook - L3.1/3.5 blocking + L3.6 hints + L3.7 prevention
#              Now with PID-based window isolation to prevent multi-window conflicts
# v2.3.0: Added window-isolation helpers for PID-specific flag isolation
# v2.2.0: Checkpoint blocking disabled - hook shows table, Claude auto-proceeds (no ok/proceed needed)
# v2.1.0: Enhanced optimization hints with consistent [OPTIMIZATION] format and clearer guidance
# Author: Claude Memory System
#
# Hook Type: PreToolUse
# Trigger: Runs BEFORE every tool call
# Exit 0 = Allow tool (may print hints to stdout)
# Exit 1 = BLOCK tool (prints reason to stderr)
#
# Policies enforced:
#   Level 3.3 - Review Checkpoint:
#     - DISABLED (v2.2.0): Hook shows checkpoint table, Claude auto-proceeds. No blocking.
#     - Flag file .checkpoint-pending-*.json is NEVER written (removed from 3-level-flow.py)
#   Level 3.1 - Task Breakdown (Loophole #7 Fix):
#     - Write/Edit/NotebookEdit: BLOCK if .task-breakdown-pending.json exists (same session+PID)
#     - Bash/Task NOT blocked: investigation and exploration allowed before TaskCreate
#     - Cleared when TaskCreate is called (post-tool-tracker.py)
#   Level 3.5 - Skill/Agent Selection (Loophole #7 Fix):
#     - Write/Edit/NotebookEdit: BLOCK if .skill-selection-pending.json exists (same session+PID)
#     - Bash/Task NOT blocked: Bash needed for git/tests, Task IS how Step 3.5 is done
#     - Cleared when Skill or Task tool is called (post-tool-tracker.py)
#   Level 3.6 - Tool Usage Optimization:
#     - Grep: warn if missing head_limit
#     - Read: warn if missing offset+limit (for large files)
#   Level 3.7 - Failure Prevention:
#     - Bash: BLOCK Windows-only commands (del, copy, dir, xcopy, etc.)
#     - Write/Edit/NotebookEdit: BLOCK Unicode chars in .py files on Windows
#
# Windows-safe: ASCII only, no Unicode chars

import sys
import os
import json
import glob as _glob
from pathlib import Path
from datetime import datetime, timedelta

# Use ide_paths for IDE self-contained installations (with fallback for standalone mode)
try:
    from ide_paths import (FLAG_DIR, CURRENT_SESSION_FILE)
except ImportError:
    # Fallback for standalone mode (no IDE_INSTALL_DIR set)
    FLAG_DIR = Path.home() / '.claude'
    CURRENT_SESSION_FILE = Path.home() / '.claude' / 'memory' / '.current-session.json'

# Tools that are BLOCKED while checkpoint is pending (file-modification tools ONLY)
# Write/Edit/NotebookEdit are the ONLY tools that directly create/modify source files.
# Bash, Task are NOT blocked: Bash is needed for git/investigation/tests.
# Task is a delegation mechanism (subagent tools are independently checked).
BLOCKED_WHILE_CHECKPOINT_PENDING = {'Write', 'Edit', 'NotebookEdit'}

# Tools that are ALWAYS ALLOWED (everything except direct file modification)
ALWAYS_ALLOWED = {'Read', 'Grep', 'Glob', 'WebFetch', 'WebSearch', 'Task', 'Bash'}

# Max age for enforcement flags - auto-expire after 60 minutes (stale flag safety)
CHECKPOINT_MAX_AGE_MINUTES = 60


def get_current_session_id():
    """
    Read the active session ID from .current-session.json.
    Returns empty string if not available (fail open - don't block on missing data).
    """
    try:
        if CURRENT_SESSION_FILE.exists():
            with open(CURRENT_SESSION_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data.get('current_session_id', '')
    except Exception:
        pass
    return ''


def find_session_flag(pattern_prefix, current_session_id):
    """
    Find PID-isolated session-specific flag file for the current window.
    Returns (flag_path, flag_data) or (None, None) if not found.
    Also auto-cleans stale flags (>60 min) from current session.

    MULTI-WINDOW FIX: Looks for flags with matching SESSION_ID AND PID.
    Pattern: .{prefix}-{SESSION_ID}-{PID}.json

    Returns:
        (flag_path, flag_data) for current window's flag, or (None, None)
    """
    current_pid = os.getpid()
    pid_specific_pattern = '{}-{}-{}.json'.format(pattern_prefix, current_session_id, current_pid)
    pid_specific_path = FLAG_DIR / pid_specific_pattern

    if pid_specific_path.exists():
        try:
            with open(pid_specific_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Auto-expire stale flags (>60 min)
            created_at_str = data.get('created_at', '')
            if created_at_str:
                try:
                    created_at = datetime.fromisoformat(created_at_str)
                    age = datetime.now() - created_at
                    if age > timedelta(minutes=CHECKPOINT_MAX_AGE_MINUTES):
                        pid_specific_path.unlink(missing_ok=True)
                        return (None, None)
                except Exception:
                    pass

            return (pid_specific_path, data)
        except Exception:
            pass

    return (None, None)


def check_checkpoint_pending(tool_name):
    """
    Level 3.3: Block code-changing tools if review checkpoint is pending.
    User must say 'ok'/'proceed' before coding can start.

    SESSION-AWARE (Loophole #11): Uses session-specific flag files.
    Each window has its own flag file. No cross-window interference.

    Returns (hints, blocks) tuple.
    """
    hints = []
    blocks = []

    if tool_name not in BLOCKED_WHILE_CHECKPOINT_PENDING:
        return hints, blocks

    current_session_id = get_current_session_id()
    if not current_session_id:
        return hints, blocks

    flag_path, flag_data = find_session_flag('.checkpoint-pending', current_session_id)
    if flag_path is None:
        return hints, blocks

    # --- Same session: block until user says ok ---
    session_id = flag_data.get('session_id', 'unknown')
    prompt_preview = flag_data.get('prompt_preview', '')[:80]

    blocks.append(
        '[PRE-TOOL BLOCKED] Review checkpoint is pending!\n'
        '  Session  : ' + session_id + '\n'
        '  Task     : ' + prompt_preview + '\n'
        '  Tool     : ' + tool_name + ' is BLOCKED until user confirms.\n'
        '  Required : User must reply with "ok" or "proceed" first.\n'
        '  Reason   : CLAUDE.md policy - no coding before checkpoint review.\n'
        '  Action   : Show the [REVIEW CHECKPOINT] to user and WAIT.'
    )

    return hints, blocks

def check_task_breakdown_pending(tool_name):
    """
    Level 3.1: Block code-changing tools if task breakdown is pending.
    Claude MUST call TaskCreate before any Write/Edit/Bash/Task.

    SESSION-AWARE (Loophole #11): Uses session-specific flag files.

    Returns (hints, blocks) tuple.
    """
    hints = []
    blocks = []

    # Only file-modification tools blocked. Bash/Task allowed for investigation.
    BLOCKED_WHILE_TASK_PENDING = {'Write', 'Edit', 'NotebookEdit'}

    if tool_name not in BLOCKED_WHILE_TASK_PENDING:
        return hints, blocks

    current_session_id = get_current_session_id()
    if not current_session_id:
        return hints, blocks

    flag_path, flag_data = find_session_flag('.task-breakdown-pending', current_session_id)
    if flag_path is None:
        return hints, blocks

    session_id = flag_data.get('session_id', 'unknown')
    prompt_preview = flag_data.get('prompt_preview', '')[:80]

    blocks.append(
        '[PRE-TOOL BLOCKED] Step 3.1 Task Breakdown is pending!\n'
        '  Session  : ' + session_id + '\n'
        '  Task     : ' + prompt_preview + '\n'
        '  Tool     : ' + tool_name + ' is BLOCKED until TaskCreate is called.\n'
        '  Required : Call TaskCreate tool FIRST to create task(s) for this request.\n'
        '  Reason   : CLAUDE.md Step 3.1 - TaskCreate MANDATORY before any coding.\n'
        '  Action   : Call TaskCreate with subject and description, then continue.'
    )

    return hints, blocks


def check_skill_selection_pending(tool_name):
    """
    Level 3.5: Block code-changing tools if skill/agent selection is pending.
    Claude MUST invoke Skill tool or Task(agent) before any Write/Edit.

    Note: Task/Bash NOT blocked - Task IS how Step 3.5 is done, Bash needed for git/tests.
    SESSION-AWARE (Loophole #11): Uses session-specific flag files.

    Returns (hints, blocks) tuple.
    """
    hints = []
    blocks = []

    # Only file-modification tools blocked. Bash allowed for git/investigation/tests.
    BLOCKED_WHILE_SKILL_PENDING = {'Write', 'Edit', 'NotebookEdit'}

    if tool_name not in BLOCKED_WHILE_SKILL_PENDING:
        return hints, blocks

    current_session_id = get_current_session_id()
    if not current_session_id:
        return hints, blocks

    flag_path, flag_data = find_session_flag('.skill-selection-pending', current_session_id)
    if flag_path is None:
        return hints, blocks

    session_id = flag_data.get('session_id', 'unknown')
    required_skill = flag_data.get('required_skill', 'unknown')
    required_type = flag_data.get('required_type', 'skill')

    if required_type == 'agent':
        action_required = 'Launch agent via Task tool: Task(subagent_type="' + required_skill + '")'
    else:
        action_required = 'Invoke skill via Skill tool: Skill(skill="' + required_skill + '")'

    blocks.append(
        '[PRE-TOOL BLOCKED] Step 3.5 Skill/Agent Selection is pending!\n'
        '  Session  : ' + session_id + '\n'
        '  Tool     : ' + tool_name + ' is BLOCKED until Skill/Agent is invoked.\n'
        '  Required : ' + action_required + '\n'
        '  Reason   : CLAUDE.md Step 3.5 - Skill/Agent MUST be invoked before coding.\n'
        '  Action   : Invoke the skill/agent first, then continue coding.'
    )

    return hints, blocks


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
            '[OPTIMIZATION] Grep: Add head_limit=100 to prevent excessive output. '
            'Default CLAUDE.md rule: ALWAYS set head_limit on Grep calls.'
        )

    return hints, []


def check_read(tool_input):
    """Level 3.6: Read optimization - hint about offset+limit for large files."""
    hints = []
    limit = tool_input.get('limit')
    offset = tool_input.get('offset')

    if not limit and not offset:
        hints.append(
            '[OPTIMIZATION] Read: No limit/offset set. '
            'For files >500 lines, use offset+limit to save context tokens.'
        )

    return hints, []


def main():
    # INTEGRATION: Load tool optimization policies from scripts/architecture/
    # This runs before every tool to apply optimizations
    try:
        script_dir = Path(__file__).parent
        tool_opt_script = script_dir / 'architecture' / '03-execution-system' / '06-tool-optimization' / 'tool-usage-optimizer.py'
        if tool_opt_script.exists():
            import subprocess
            subprocess.run([sys.executable, str(tool_opt_script)], timeout=3, capture_output=True)
    except:
        pass  # Policy execution is optional, don't block

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

    # CHECKPOINT ENFORCEMENT (Level 3.3 - runs first, before all other checks)
    h, b = check_checkpoint_pending(tool_name)
    all_hints.extend(h)
    all_blocks.extend(b)

    # If already blocked by checkpoint, skip other checks (no need to pile on)
    # Exit code 2 = blocking error (Claude Code docs: stderr fed to Claude, tool blocked)
    if all_blocks:
        for hint in all_hints:
            sys.stdout.write(hint + '\n')
        sys.stdout.flush()
        for block in all_blocks:
            sys.stderr.write(block + '\n')
        sys.stderr.flush()
        sys.exit(2)

    # TASK BREAKDOWN ENFORCEMENT (Level 3.1 - TaskCreate must be called first)
    h, b = check_task_breakdown_pending(tool_name)
    all_hints.extend(h)
    all_blocks.extend(b)

    if all_blocks:
        for hint in all_hints:
            sys.stdout.write(hint + '\n')
        sys.stdout.flush()
        for block in all_blocks:
            sys.stderr.write(block + '\n')
        sys.stderr.flush()
        sys.exit(2)

    # SKILL/AGENT SELECTION ENFORCEMENT (Level 3.5 - Skill/Task must be invoked first)
    h, b = check_skill_selection_pending(tool_name)
    all_hints.extend(h)
    all_blocks.extend(b)

    if all_blocks:
        for hint in all_hints:
            sys.stdout.write(hint + '\n')
        sys.stdout.flush()
        for block in all_blocks:
            sys.stderr.write(block + '\n')
        sys.stderr.flush()
        sys.exit(2)

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

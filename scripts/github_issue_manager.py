#!/usr/bin/env python
# Script Name: github_issue_manager.py
# Version: 2.1.0
# Last Modified: 2026-02-28
# Description: GitHub Issues + Branch integration for Level 3 Execution.
#              Auto-creates issues on TaskCreate, auto-closes on TaskUpdate(completed).
#              Creates issue branches on first task (issue-N-slug format).
#              Uses gh CLI. Non-blocking - never fails the hook if GitHub is unavailable.
# Author: Claude Memory System
#
# Safety:
#   - Max 10 GitHub operations per session (create + close combined)
#   - 15s timeout on all gh CLI calls
#   - All public functions wrapped in try/except (never raises)
#   - gh auth status is the implicit enable/disable toggle

import sys
import os
import json
import subprocess
from pathlib import Path
from datetime import datetime

# Use ide_paths for IDE self-contained installations (with fallback for standalone mode)
try:
    from ide_paths import SESSION_STATE_FILE
except ImportError:
    SESSION_STATE_FILE = Path.home() / '.claude' / 'memory' / 'logs' / 'session-progress.json'

MAX_OPS_PER_SESSION = 10
GH_TIMEOUT = 15  # seconds

# Cached per-invocation (module-level)
_gh_available = None
_ops_count = 0


def _get_session_id():
    """Get current session ID from session-progress.json."""
    try:
        if SESSION_STATE_FILE.exists():
            with open(SESSION_STATE_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data.get('session_id', '')
    except Exception:
        pass
    return ''


def _get_repo_root():
    """Get the git repo root from CWD, or None."""
    try:
        result = subprocess.run(
            ['git', 'rev-parse', '--show-toplevel'],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except Exception:
        pass
    return None


def _get_mapping_file():
    """Get path to the github-issues.json mapping file for current session."""
    session_id = _get_session_id()
    if session_id:
        session_dir = Path.home() / '.claude' / 'memory' / 'logs' / 'sessions' / session_id
        return session_dir / 'github-issues.json'
    # Fallback: use a general mapping file
    return Path.home() / '.claude' / 'memory' / 'logs' / 'github-issues.json'


def _load_issues_mapping():
    """Load task-to-issue mapping from disk."""
    mapping_file = _get_mapping_file()
    try:
        if mapping_file.exists():
            with open(mapping_file, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        pass
    return {'task_to_issue': {}, 'ops_count': 0, 'session_id': _get_session_id()}


def _save_issues_mapping(mapping):
    """Persist task-to-issue mapping to disk."""
    mapping_file = _get_mapping_file()
    try:
        mapping_file.parent.mkdir(parents=True, exist_ok=True)
        with open(mapping_file, 'w', encoding='utf-8') as f:
            json.dump(mapping, f, indent=2)
    except Exception:
        pass


def _get_ops_count():
    """Get number of GitHub operations performed this session."""
    mapping = _load_issues_mapping()
    return mapping.get('ops_count', 0)


def _increment_ops_count():
    """Increment and persist the ops counter."""
    mapping = _load_issues_mapping()
    mapping['ops_count'] = mapping.get('ops_count', 0) + 1
    _save_issues_mapping(mapping)


def is_gh_available():
    """Check if gh CLI is installed and authenticated. Cached per invocation."""
    global _gh_available
    if _gh_available is not None:
        return _gh_available

    try:
        result = subprocess.run(
            ['gh', 'auth', 'status'],
            capture_output=True, text=True, timeout=GH_TIMEOUT
        )
        _gh_available = (result.returncode == 0)
    except Exception:
        _gh_available = False

    return _gh_available


def extract_task_id_from_response(tool_response):
    """
    Parse task ID from a TaskCreate tool response.

    The response content typically looks like:
      "Task #1 created successfully: ..."
    Returns the task ID string (e.g. '1') or empty string.
    """
    try:
        content = ''
        if isinstance(tool_response, dict):
            c = tool_response.get('content', '')
            if isinstance(c, str):
                content = c
            elif isinstance(c, list):
                for item in c:
                    if isinstance(item, dict):
                        content += item.get('text', '')
                    elif isinstance(item, str):
                        content += item
        elif isinstance(tool_response, str):
            content = tool_response

        # Pattern: "Task #N created successfully"
        if 'Task #' in content:
            after_hash = content.split('Task #', 1)[1]
            task_id = ''
            for ch in after_hash:
                if ch.isdigit():
                    task_id += ch
                else:
                    break
            return task_id
    except Exception:
        pass
    return ''


def _get_flow_trace_context():
    """
    Load flow-trace.json to get current session's execution context:
    task type, complexity, model, skill/agent, context usage, etc.
    Returns dict with extracted fields, or empty dict.
    """
    session_id = _get_session_id()
    if not session_id:
        return {}
    trace_file = Path.home() / '.claude' / 'memory' / 'logs' / 'sessions' / session_id / 'flow-trace.json'
    try:
        if trace_file.exists():
            with open(trace_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return {
                'task_type': data.get('task_type', ''),
                'complexity': data.get('complexity', 0),
                'model': data.get('model', ''),
                'skill': data.get('skill', ''),
                'context_pct': data.get('context_pct', 0),
                'plan_mode': data.get('plan_mode', False),
            }
    except Exception:
        pass
    return {}


def _get_session_progress_context():
    """
    Load session-progress.json for current tool counts, tasks completed, modified files.
    Returns dict with extracted fields, or empty dict.
    """
    try:
        if SESSION_STATE_FILE.exists():
            with open(SESSION_STATE_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return {
                'tool_counts': data.get('tool_counts', {}),
                'tasks_completed': data.get('tasks_completed', 0),
                'total_progress': data.get('total_progress', 0),
                'modified_files': data.get('modified_files_since_commit', []),
                'errors_seen': data.get('errors_seen', 0),
                'started_at': data.get('started_at', ''),
                'context_estimate_pct': data.get('context_estimate_pct', 0),
            }
    except Exception:
        pass
    return {}


def _get_tool_activity_for_task(task_id):
    """
    Scan tool-tracker.jsonl for activity related to a specific task.
    Returns dict with files_read, files_written, files_edited, commands_run, searches.
    Scans entries AFTER the TaskCreate for this task_id until the TaskUpdate(completed).
    """
    tracker_log = Path.home() / '.claude' / 'memory' / 'logs' / 'tool-tracker.jsonl'
    result = {
        'files_read': [],
        'files_written': [],
        'files_edited': [],
        'commands_run': [],
        'searches': [],
        'edits': [],
        'total_tools': 0,
    }
    try:
        if not tracker_log.exists():
            return result

        # Read all entries, find the window for this task
        recording = False
        with open(tracker_log, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except Exception:
                    continue

                tool = entry.get('tool', '')

                # Start recording after this task's TaskCreate
                if tool == 'TaskCreate' and str(entry.get('task_subject', '')) != '':
                    # Rough match - we start recording from the most recent TaskCreate
                    # that hasn't been closed yet
                    recording = True
                    result = {
                        'files_read': [], 'files_written': [], 'files_edited': [],
                        'commands_run': [], 'searches': [], 'edits': [], 'total_tools': 0,
                    }
                    continue

                # Stop recording when this task is marked completed
                if tool == 'TaskUpdate' and entry.get('task_id') == str(task_id):
                    if entry.get('task_status') == 'completed':
                        break

                if not recording:
                    continue

                result['total_tools'] += 1
                file_path = entry.get('file', '')

                if tool == 'Read' and file_path:
                    if file_path not in result['files_read']:
                        result['files_read'].append(file_path)
                elif tool == 'Write' and file_path:
                    if file_path not in result['files_written']:
                        result['files_written'].append(file_path)
                    lines = entry.get('content_lines', 0)
                    if lines:
                        result['edits'].append(file_path + ' (' + str(lines) + ' lines written)')
                elif tool == 'Edit' and file_path:
                    if file_path not in result['files_edited']:
                        result['files_edited'].append(file_path)
                    old_hint = entry.get('old_hint', '')
                    new_hint = entry.get('new_hint', '')
                    edit_size = entry.get('edit_size', 0)
                    if old_hint or new_hint:
                        edit_desc = file_path
                        if edit_size:
                            edit_desc += ' (' + ('+' if edit_size > 0 else '') + str(edit_size) + ' chars)'
                        result['edits'].append(edit_desc)
                elif tool == 'Bash':
                    cmd = entry.get('command', '')
                    desc = entry.get('desc', '')
                    if cmd:
                        result['commands_run'].append(desc or cmd[:100])
                elif tool in ('Grep', 'Glob'):
                    pattern = entry.get('pattern', '')
                    if pattern:
                        result['searches'].append(tool + ': ' + pattern)

    except Exception:
        pass
    return result


def create_github_issue(task_id, subject, description):
    """
    Create a comprehensive GitHub issue for a task.

    Includes: full description, acceptance criteria, session context,
    execution environment info, complexity analysis, and related metadata.

    Args:
        task_id: Task ID string (e.g. '1')
        subject: Task subject line
        description: Task description

    Returns:
        Issue number (int) on success, None on failure.
    """
    try:
        if not is_gh_available():
            return None

        if _get_ops_count() >= MAX_OPS_PER_SESSION:
            return None

        repo_root = _get_repo_root()
        if not repo_root:
            return None

        # Build issue title and body
        title = '[TASK-' + str(task_id) + '] ' + subject if task_id else subject
        # Truncate title to 256 chars (GitHub limit is higher but keep it readable)
        title = title[:256]

        session_id = _get_session_id()
        flow_ctx = _get_flow_trace_context()
        progress_ctx = _get_session_progress_context()

        # --- Build comprehensive issue body ---
        body_lines = []

        # Section 1: Task Overview
        body_lines.append('## Task Overview')
        body_lines.append('')
        body_lines.append('| Field | Value |')
        body_lines.append('|-------|-------|')
        body_lines.append('| **Task ID** | ' + str(task_id) + ' |')
        body_lines.append('| **Subject** | ' + subject + ' |')
        if flow_ctx.get('task_type'):
            body_lines.append('| **Type** | ' + flow_ctx['task_type'] + ' |')
        if flow_ctx.get('complexity'):
            body_lines.append('| **Complexity** | ' + str(flow_ctx['complexity']) + '/25 |')
        if flow_ctx.get('model'):
            body_lines.append('| **Model** | ' + flow_ctx['model'] + ' |')
        if flow_ctx.get('skill'):
            body_lines.append('| **Skill/Agent** | ' + flow_ctx['skill'] + ' |')
        if flow_ctx.get('plan_mode'):
            body_lines.append('| **Plan Mode** | Required |')
        body_lines.append('')

        # Section 2: Description (full, untruncated)
        body_lines.append('## Description')
        body_lines.append('')
        if description:
            body_lines.append(description)
        else:
            body_lines.append('_(no description provided)_')
        body_lines.append('')

        # Section 3: Acceptance Criteria (auto-derived from description)
        body_lines.append('## Acceptance Criteria')
        body_lines.append('')
        if description:
            # Parse description for actionable items
            criteria_found = False
            for line in description.split('\n'):
                line = line.strip()
                if line.startswith('- ') or line.startswith('* '):
                    body_lines.append('- [ ] ' + line[2:])
                    criteria_found = True
                elif line and len(line) > 15:
                    # Convert sentence-like descriptions into checklist
                    body_lines.append('- [ ] ' + line)
                    criteria_found = True
            if not criteria_found:
                body_lines.append('- [ ] ' + subject)
        else:
            body_lines.append('- [ ] ' + subject)
        body_lines.append('')

        # Section 4: Session Context
        body_lines.append('## Session Context')
        body_lines.append('')
        body_lines.append('| Field | Value |')
        body_lines.append('|-------|-------|')
        if session_id:
            body_lines.append('| **Session ID** | `' + session_id + '` |')
        body_lines.append('| **Created At** | ' + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ' |')
        if progress_ctx.get('started_at'):
            body_lines.append('| **Session Started** | ' + progress_ctx['started_at'] + ' |')
        if progress_ctx.get('context_estimate_pct'):
            body_lines.append('| **Context Usage** | ' + str(progress_ctx['context_estimate_pct']) + '% |')
        if progress_ctx.get('tasks_completed'):
            body_lines.append('| **Tasks Completed So Far** | ' + str(progress_ctx['tasks_completed']) + ' |')
        if progress_ctx.get('total_progress'):
            body_lines.append('| **Session Progress** | ' + str(progress_ctx['total_progress']) + '% |')

        # Get current branch
        try:
            branch_result = subprocess.run(
                ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                capture_output=True, text=True, timeout=5, cwd=repo_root
            )
            if branch_result.returncode == 0:
                body_lines.append('| **Branch** | `' + branch_result.stdout.strip() + '` |')
        except Exception:
            pass

        # Get repo name
        try:
            remote_result = subprocess.run(
                ['git', 'remote', 'get-url', 'origin'],
                capture_output=True, text=True, timeout=5, cwd=repo_root
            )
            if remote_result.returncode == 0:
                remote_url = remote_result.stdout.strip()
                # Extract repo name from URL
                repo_name = remote_url.rsplit('/', 1)[-1].replace('.git', '')
                body_lines.append('| **Repository** | ' + repo_name + ' |')
        except Exception:
            pass

        body_lines.append('')

        # Section 5: Related files (if any modified files tracked)
        if progress_ctx.get('modified_files'):
            body_lines.append('## Files Modified (Before This Task)')
            body_lines.append('')
            for f in progress_ctx['modified_files'][:15]:
                body_lines.append('- `' + f + '`')
            body_lines.append('')

        # Footer
        body_lines.append('---')
        body_lines.append('')
        body_lines.append('_Auto-created by Claude Memory System (Level 3 Execution) | v2.1.0_')

        body = '\n'.join(body_lines)

        # Build labels list
        labels = ['task-auto-created', 'level-3-execution']

        # Detect type from subject/description
        combined = (subject + ' ' + (description or '')).lower()
        if any(w in combined for w in ['fix', 'bug', 'error', 'broken', 'crash']):
            labels.append('bugfix')
        elif any(w in combined for w in ['refactor', 'cleanup', 'reorganize', 'simplify']):
            labels.append('refactor')
        elif any(w in combined for w in ['doc', 'readme', 'comment', 'documentation']):
            labels.append('docs')
        else:
            labels.append('feature')

        # Create issue via gh CLI
        cmd = [
            'gh', 'issue', 'create',
            '--title', title,
            '--body', body,
        ]

        # Try with labels, fall back without if labels don't exist
        cmd_with_labels = cmd + ['--label', ','.join(labels)]

        result = subprocess.run(
            cmd_with_labels,
            capture_output=True, text=True, timeout=GH_TIMEOUT,
            cwd=repo_root
        )

        # If label creation failed, retry without labels
        if result.returncode != 0 and 'label' in result.stderr.lower():
            result = subprocess.run(
                cmd,
                capture_output=True, text=True, timeout=GH_TIMEOUT,
                cwd=repo_root
            )

        if result.returncode == 0 and result.stdout.strip():
            # stdout contains the issue URL, e.g. https://github.com/user/repo/issues/42
            issue_url = result.stdout.strip()
            issue_number = None
            if '/issues/' in issue_url:
                num_str = issue_url.rsplit('/issues/', 1)[1].strip()
                if num_str.isdigit():
                    issue_number = int(num_str)

            # Save mapping
            mapping = _load_issues_mapping()
            task_key = str(task_id) if task_id else 'unknown'
            mapping['task_to_issue'][task_key] = {
                'issue_number': issue_number,
                'issue_url': issue_url,
                'title': title,
                'created_at': datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
                'status': 'open'
            }
            mapping['ops_count'] = mapping.get('ops_count', 0) + 1
            _save_issues_mapping(mapping)

            return issue_number

    except Exception:
        pass
    return None


def _build_close_comment(task_id, issue_data):
    """
    Build a comprehensive closing comment for a GitHub issue.

    Includes:
      - Resolution summary (what was done)
      - Files changed (read/written/edited)
      - Commands executed
      - Duration (created_at -> now)
      - RCA analysis (if bugfix type)
      - Tool usage breakdown
      - Session metrics

    Returns comment string.
    """
    lines = []

    lines.append('## Resolution Summary')
    lines.append('')

    task_title = issue_data.get('title', 'Task ' + str(task_id))
    created_at = issue_data.get('created_at', '')
    closed_at = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')

    # Calculate duration
    duration_str = ''
    if created_at:
        try:
            start = datetime.strptime(created_at, '%Y-%m-%dT%H:%M:%S')
            end = datetime.strptime(closed_at, '%Y-%m-%dT%H:%M:%S')
            delta = end - start
            total_secs = int(delta.total_seconds())
            if total_secs >= 3600:
                hours = total_secs // 3600
                mins = (total_secs % 3600) // 60
                duration_str = str(hours) + 'h ' + str(mins) + 'm'
            elif total_secs >= 60:
                mins = total_secs // 60
                secs = total_secs % 60
                duration_str = str(mins) + 'm ' + str(secs) + 's'
            else:
                duration_str = str(total_secs) + 's'
        except Exception:
            pass

    lines.append('**Status:** Completed')
    if duration_str:
        lines.append('**Duration:** ' + duration_str)
    lines.append('**Closed At:** ' + closed_at)
    lines.append('')

    # Get tool activity for this task
    activity = _get_tool_activity_for_task(task_id)

    # Section: What Was Done (files changed)
    all_changed_files = list(set(activity.get('files_written', []) + activity.get('files_edited', [])))
    if all_changed_files:
        lines.append('## Files Changed')
        lines.append('')
        for f in all_changed_files[:20]:
            lines.append('- `' + f + '`')
        lines.append('')

    # Section: Detailed Edits
    edits = activity.get('edits', [])
    if edits:
        lines.append('## Changes Made')
        lines.append('')
        for edit in edits[:15]:
            lines.append('- ' + edit)
        lines.append('')

    # Section: Files Read (research/investigation)
    files_read = activity.get('files_read', [])
    if files_read:
        lines.append('## Files Investigated')
        lines.append('')
        for f in files_read[:15]:
            lines.append('- `' + f + '`')
        lines.append('')

    # Section: Commands Executed
    commands = activity.get('commands_run', [])
    if commands:
        lines.append('## Commands Executed')
        lines.append('')
        for cmd in commands[:10]:
            lines.append('- `' + cmd + '`')
        lines.append('')

    # Section: Searches Performed
    searches = activity.get('searches', [])
    if searches:
        lines.append('## Searches Performed')
        lines.append('')
        for s in searches[:10]:
            lines.append('- ' + s)
        lines.append('')

    # Section: RCA (Root Cause Analysis) - only for bugfix issues
    issue_title_lower = task_title.lower()
    is_bugfix = any(w in issue_title_lower for w in ['fix', 'bug', 'error', 'broken', 'crash', 'issue'])
    if is_bugfix:
        lines.append('## Root Cause Analysis (RCA)')
        lines.append('')
        # Build RCA from available data
        if files_read:
            lines.append('**Investigation:** ' + str(len(files_read)) + ' files investigated')
        if all_changed_files:
            lines.append('**Root Cause Location:** ' + ', '.join(['`' + f + '`' for f in all_changed_files[:5]]))
        if edits:
            lines.append('**Fix Applied:** ' + str(len(edits)) + ' edit(s) made')
            for edit in edits[:5]:
                lines.append('  - ' + edit)
        if commands:
            lines.append('**Verification:** ' + str(len(commands)) + ' command(s) run to verify fix')
        lines.append('')

    # Section: Tool Usage Summary
    total_tools = activity.get('total_tools', 0)
    if total_tools > 0:
        lines.append('## Tool Usage')
        lines.append('')
        lines.append('| Metric | Value |')
        lines.append('|--------|-------|')
        lines.append('| Total Tool Calls | ' + str(total_tools) + ' |')
        if files_read:
            lines.append('| Files Read | ' + str(len(files_read)) + ' |')
        if all_changed_files:
            lines.append('| Files Changed | ' + str(len(all_changed_files)) + ' |')
        if commands:
            lines.append('| Commands Run | ' + str(len(commands)) + ' |')
        if searches:
            lines.append('| Searches | ' + str(len(searches)) + ' |')
        lines.append('')

    # Section: Session Context
    progress_ctx = _get_session_progress_context()
    flow_ctx = _get_flow_trace_context()

    if progress_ctx or flow_ctx:
        lines.append('## Session Context')
        lines.append('')
        lines.append('| Field | Value |')
        lines.append('|-------|-------|')
        session_id = _get_session_id()
        if session_id:
            lines.append('| Session | `' + session_id + '` |')
        if flow_ctx.get('complexity'):
            lines.append('| Complexity | ' + str(flow_ctx['complexity']) + '/25 |')
        if flow_ctx.get('model'):
            lines.append('| Model | ' + flow_ctx['model'] + ' |')
        if flow_ctx.get('skill'):
            lines.append('| Skill/Agent | ' + flow_ctx['skill'] + ' |')
        if progress_ctx.get('tasks_completed'):
            lines.append('| Tasks Completed | ' + str(progress_ctx['tasks_completed']) + ' |')
        if progress_ctx.get('context_estimate_pct'):
            lines.append('| Context Usage | ' + str(progress_ctx['context_estimate_pct']) + '% |')
        if progress_ctx.get('errors_seen'):
            lines.append('| Errors Encountered | ' + str(progress_ctx['errors_seen']) + ' |')
        lines.append('')

    # Footer
    lines.append('---')
    lines.append('_Auto-closed by Claude Memory System (Level 3 Execution) | v2.1.0_')

    return '\n'.join(lines)


def close_github_issue(task_id):
    """
    Close the GitHub issue associated with a task with a comprehensive summary comment.

    The closing comment includes:
      - What was done (files changed, edits made)
      - RCA analysis (if bugfix type)
      - Tool usage breakdown
      - Duration, session context, commands run

    Args:
        task_id: Task ID string (e.g. '1')

    Returns:
        True if closed successfully, False otherwise.
    """
    try:
        if not is_gh_available():
            return False

        if _get_ops_count() >= MAX_OPS_PER_SESSION:
            return False

        repo_root = _get_repo_root()
        if not repo_root:
            return False

        # Look up issue number from mapping
        mapping = _load_issues_mapping()
        task_key = str(task_id)
        issue_data = mapping.get('task_to_issue', {}).get(task_key)

        if not issue_data:
            return False

        issue_number = issue_data.get('issue_number')
        if not issue_number:
            return False

        # Already closed?
        if issue_data.get('status') == 'closed':
            return True

        # Build comprehensive closing comment
        close_comment = _build_close_comment(task_id, issue_data)

        # Close via gh CLI with detailed comment
        result = subprocess.run(
            ['gh', 'issue', 'close', str(issue_number),
             '--comment', close_comment],
            capture_output=True, text=True, timeout=GH_TIMEOUT,
            cwd=repo_root
        )

        if result.returncode == 0:
            # Update mapping
            issue_data['status'] = 'closed'
            issue_data['closed_at'] = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
            mapping['task_to_issue'][task_key] = issue_data
            mapping['ops_count'] = mapping.get('ops_count', 0) + 1
            _save_issues_mapping(mapping)
            return True

    except Exception:
        pass
    return False


def _slugify(text, max_len=40):
    """
    Convert text to a URL/branch-safe slug.
    Lowercase, hyphens only, no special chars, max max_len chars.
    """
    slug = ''
    for ch in text.lower():
        if ch.isalnum():
            slug += ch
        elif ch in (' ', '-', '_', '/'):
            if slug and slug[-1] != '-':
                slug += '-'
    # Remove leading/trailing hyphens
    slug = slug.strip('-')
    # Truncate at max_len, but don't cut mid-word if possible
    if len(slug) > max_len:
        cut = slug[:max_len]
        last_hyphen = cut.rfind('-')
        if last_hyphen > max_len // 2:
            slug = cut[:last_hyphen]
        else:
            slug = cut
    return slug.strip('-')


def create_issue_branch(issue_number, subject):
    """
    Create and checkout a git branch named issue-{N}-{slug}.
    Only creates if currently on main/master.
    Stores branch name in github-issues.json under 'session_branch'.

    Args:
        issue_number: GitHub issue number (int)
        subject: Task subject for slug generation

    Returns:
        Branch name string on success, None on failure.
    """
    try:
        repo_root = _get_repo_root()
        if not repo_root:
            return None

        # Check current branch - only create from main/master
        result = subprocess.run(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            capture_output=True, text=True, timeout=5,
            cwd=repo_root
        )
        if result.returncode != 0:
            return None

        current_branch = result.stdout.strip()
        if current_branch not in ('main', 'master'):
            # Already on a feature branch - don't create another
            return None

        # Build branch name
        slug = _slugify(subject)
        branch_name = 'issue-' + str(issue_number)
        if slug:
            branch_name += '-' + slug

        # Create and checkout new branch
        result = subprocess.run(
            ['git', 'checkout', '-b', branch_name],
            capture_output=True, text=True, timeout=10,
            cwd=repo_root
        )

        if result.returncode == 0:
            # Store branch name in mapping
            mapping = _load_issues_mapping()
            mapping['session_branch'] = branch_name
            mapping['branch_created_at'] = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
            mapping['branch_from_issue'] = issue_number
            _save_issues_mapping(mapping)
            return branch_name
        else:
            # Branch might already exist - try checkout
            result = subprocess.run(
                ['git', 'checkout', branch_name],
                capture_output=True, text=True, timeout=10,
                cwd=repo_root
            )
            if result.returncode == 0:
                mapping = _load_issues_mapping()
                mapping['session_branch'] = branch_name
                _save_issues_mapping(mapping)
                return branch_name

    except Exception:
        pass
    return None


def get_session_branch():
    """
    Get the branch name stored for the current session.
    Returns branch name string or None if no session branch exists.
    """
    try:
        mapping = _load_issues_mapping()
        return mapping.get('session_branch')
    except Exception:
        pass
    return None


def is_on_issue_branch():
    """
    Check if the current git branch starts with 'issue-'.
    Returns True if on an issue branch, False otherwise.
    """
    try:
        repo_root = _get_repo_root()
        if not repo_root:
            return False

        result = subprocess.run(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            capture_output=True, text=True, timeout=5,
            cwd=repo_root
        )
        if result.returncode == 0:
            return result.stdout.strip().startswith('issue-')
    except Exception:
        pass
    return False

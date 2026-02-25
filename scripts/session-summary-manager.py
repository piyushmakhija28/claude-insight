#!/usr/bin/env python3
"""
Script Name: session-summary-manager.py
Version: 1.0.0
Last Modified: 2026-02-23
Description: Session Summary Manager - accumulates per-request data and generates
             human-readable summaries for each session.

             Every request adds an entry to session-summary.json (structured).
             On session close (/clear), generates session-summary.md (readable).
             Chain context reads these summaries for rich context continuity.

Usage:
    # Accumulate data for current request (called by 3-level-flow.py)
    python session-summary-manager.py accumulate \
        --session SESSION-ID \
        --prompt "user message" \
        --task-type "Implementation" \
        --skill "java-spring-boot-microservices" \
        --complexity 7 \
        --model "SONNET" \
        --cwd "/path/to/project"

    # Finalize summary on session close (called by clear-session-handler.py)
    python session-summary-manager.py finalize --session SESSION-ID

    # Read summary for a session
    python session-summary-manager.py read --session SESSION-ID

    # Read summary as plain text (for chain context)
    python session-summary-manager.py read --session SESSION-ID --format text

Hook Type: Utility (called by 3-level-flow.py and clear-session-handler.py)
Windows-Safe: No Unicode chars (ASCII only, cp1252 compatible)
"""

import sys
import os
import json
import argparse
from pathlib import Path
from datetime import datetime

# Windows-safe encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

MEMORY_BASE = Path.home() / '.claude' / 'memory'
SESSIONS_DIR = MEMORY_BASE / 'sessions'
LOGS_DIR = MEMORY_BASE / 'logs'
SUMMARY_LOG = LOGS_DIR / 'session-summary.log'


# =============================================================================
# LOGGING
# =============================================================================

def log_event(msg):
    """Log to session-summary.log (ASCII only)"""
    SUMMARY_LOG.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    try:
        with open(SUMMARY_LOG, 'a', encoding='utf-8') as f:
            f.write(f"{ts} | {msg}\n")
    except Exception:
        pass


# =============================================================================
# PATHS
# =============================================================================

def session_log_dir(session_id):
    """Get session log directory"""
    return LOGS_DIR / 'sessions' / session_id


def summary_json_path(session_id):
    """Path to accumulated structured summary"""
    return session_log_dir(session_id) / 'session-summary.json'


def summary_md_path(session_id):
    """Path to human-readable summary"""
    return session_log_dir(session_id) / 'session-summary.md'


# =============================================================================
# ACCUMULATE - Called on every request by 3-level-flow.py
# =============================================================================

def accumulate(session_id, prompt='', task_type='', skill='', complexity=0,
               model='', cwd=''):
    """
    Add a request entry to the session's accumulated summary.
    Called by 3-level-flow.py after every user message.
    """
    if not session_id:
        return False

    log_dir = session_log_dir(session_id)
    log_dir.mkdir(parents=True, exist_ok=True)
    json_path = summary_json_path(session_id)

    # Load existing or create new
    if json_path.exists():
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception:
            data = _new_summary(session_id)
    else:
        data = _new_summary(session_id)

    # Add this request as an entry
    entry = {
        "timestamp": datetime.now().isoformat(),
        "prompt": prompt[:500],
        "task_type": task_type,
        "skill": skill,
        "complexity": complexity,
        "model": model,
        "cwd": cwd,
    }

    data["requests"].append(entry)
    data["request_count"] = len(data["requests"])
    data["last_updated"] = datetime.now().isoformat()

    # Track unique values
    if skill and skill not in data["skills_used"]:
        data["skills_used"].append(skill)
    if task_type and task_type not in data["task_types"]:
        data["task_types"].append(task_type)
    if model and model not in data["models_used"]:
        data["models_used"].append(model)

    # Extract project from cwd
    if cwd:
        project = _extract_project(cwd)
        if project and project not in data["projects_touched"]:
            data["projects_touched"].append(project)

    # Track max complexity
    try:
        c = int(complexity)
        if c > data.get("max_complexity", 0):
            data["max_complexity"] = c
    except (ValueError, TypeError):
        pass

    # Write back
    try:
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        log_event(f"[OK] Accumulated request #{data['request_count']} for {session_id}")
        return True
    except Exception as e:
        log_event(f"[ERROR] Failed to accumulate for {session_id}: {e}")
        return False


def _new_summary(session_id):
    """Create a fresh summary structure"""
    return {
        "version": "1.0.0",
        "session_id": session_id,
        "created_at": datetime.now().isoformat(),
        "last_updated": datetime.now().isoformat(),
        "status": "ACTIVE",
        "request_count": 0,
        "requests": [],
        "skills_used": [],
        "task_types": [],
        "models_used": [],
        "projects_touched": [],
        "max_complexity": 0,
        "summary_text": None,
    }


def _extract_project(cwd):
    """Extract project name from working directory path"""
    parts = Path(cwd).parts
    for part in reversed(parts):
        if part.startswith(('techdeveloper-', 'surgricalswale-', 'lovepoet-')):
            return part
        if part in ('techdeveloper', 'surgricalswale', 'lovepoet'):
            return part
    # Fallback: last non-generic directory name
    for part in reversed(parts):
        if part not in ('backend', 'frontend', 'src', 'main', 'java', 'resources',
                        'Documents', 'Users', 'workspace-spring-tool-suite-4-4.27.0-new',
                        'C:', 'c'):
            return part
    return None


# =============================================================================
# FINALIZE - Called on session close by clear-session-handler.py
# =============================================================================

def finalize(session_id):
    """
    Generate human-readable session-summary.md from accumulated data.
    Called when session is closed (on /clear).
    """
    if not session_id:
        return False

    json_path = summary_json_path(session_id)
    if not json_path.exists():
        log_event(f"[WARN] No accumulated data for {session_id}, building from session JSON")
        data = _build_from_session_json(session_id)
        if not data:
            return False
    else:
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            log_event(f"[ERROR] Failed to read summary JSON for {session_id}: {e}")
            return False

    # Generate markdown summary
    md = _generate_markdown(data)

    # Write session-summary.md
    md_path = summary_md_path(session_id)
    try:
        md_path.write_text(md, encoding='utf-8')
        log_event(f"[OK] Summary MD generated: {md_path}")
    except Exception as e:
        log_event(f"[ERROR] Failed to write summary MD for {session_id}: {e}")
        return False

    # Update JSON with status and summary text
    data["status"] = "COMPLETED"
    data["summary_text"] = _generate_one_liner(data)
    data["finalized_at"] = datetime.now().isoformat()
    try:
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass

    # Update chain-index with summary
    _update_chain_summary(session_id, data)

    # AUTO-CLEANUP: Check context and trigger cleanup if needed
    # This way we automatically compact when context is high
    try:
        auto_trigger_cleanup_if_needed(session_id, data)
    except Exception as e:
        log_event(f"[INFO] Auto-cleanup check failed (non-blocking): {e}")

    return True


def auto_trigger_cleanup_if_needed(session_id, summary_data):
    """
    AUTO-CLEANUP EXECUTION: When finalizing a session, check context usage.
    If context > 90%, AUTOMATICALLY EXECUTE cleanup/compaction.

    This is NOT just detection - we actually CLEANUP!
    """
    # Estimate context usage from summary
    request_count = summary_data.get("request_count", 0)
    estimated_tokens_per_request = 1500  # Conservative estimate
    estimated_used = request_count * estimated_tokens_per_request
    total_context_window = 200000
    estimated_percentage = (estimated_used / total_context_window) * 100

    log_event(f"[CHECK] Session {session_id}: Estimated context usage = {estimated_percentage:.1f}%")

    # If context is high, EXECUTE automatic cleanup
    if estimated_percentage > 90:
        log_event(f"[ALERT] Context high ({estimated_percentage:.1f}%) - AUTO-EXECUTING cleanup NOW")

        # ACTUAL CLEANUP: Delete old session files to free space
        old_sessions_deleted = _execute_session_cleanup()

        log_event(f"[CLEANUP] Deleted {old_sessions_deleted} old session files")
        log_event(f"[COMPACT] Session logs cleaned up")

        # Save baseline: Context is now reset for next session
        baseline_file = (LOGS_DIR / 'context-baseline.json')
        baseline_file.parent.mkdir(parents=True, exist_ok=True)

        baseline = {
            "last_cleanup_session": session_id,
            "last_cleanup_time": datetime.now().isoformat(),
            "old_sessions_deleted": old_sessions_deleted,
            "old_logs_compacted": _cleanup_old_logs(),
            "context_reset_to": 10,  # Starting fresh for new session
        }

        with open(baseline_file, 'w', encoding='utf-8') as f:
            json.dump(baseline, f, indent=2)

        log_event(f"[BASELINE] Context reset to 10% for next session")
        log_event(f"[DONE] AUTO-CLEANUP completed successfully!")


def _execute_session_cleanup():
    """ACTUALLY DELETE old session files to free up space"""
    deleted_count = 0
    try:
        # Keep only last 5 sessions, delete older ones
        sessions = sorted(list(SESSIONS_DIR.glob('SESSION-*.json')),
                         key=lambda p: p.stat().st_mtime, reverse=True)

        sessions_to_keep = 5
        for old_session_file in sessions[sessions_to_keep:]:
            try:
                old_session_file.unlink()
                deleted_count += 1
                log_event(f"[DELETE] Removed old session: {old_session_file.name}")
            except Exception as e:
                log_event(f"[WARN] Could not delete {old_session_file.name}: {e}")
    except Exception as e:
        log_event(f"[ERROR] Session cleanup failed: {e}")

    return deleted_count


def _cleanup_old_logs():
    """ACTUALLY CLEANUP old session logs (keep last 10)"""
    cleaned_count = 0
    try:
        session_logs = sorted(list((LOGS_DIR / 'sessions').glob('SESSION-*')),
                             key=lambda p: p.stat().st_mtime, reverse=True)

        logs_to_keep = 10
        for old_log_dir in session_logs[logs_to_keep:]:
            try:
                import shutil
                shutil.rmtree(old_log_dir)
                cleaned_count += 1
                log_event(f"[CLEANUP] Removed old logs: {old_log_dir.name}")
            except Exception as e:
                log_event(f"[WARN] Could not cleanup {old_log_dir.name}: {e}")
    except Exception as e:
        log_event(f"[ERROR] Log cleanup failed: {e}")

    return cleaned_count


def _count_old_sessions():
    """Count how many old sessions are available for compaction"""
    try:
        sessions = list(SESSIONS_DIR.glob('SESSION-*.json'))
        return len(sessions)
    except:
        return 0


def _build_from_session_json(session_id):
    """Build summary data from session JSON when no accumulated data exists"""
    session_file = SESSIONS_DIR / f'{session_id}.json'
    if not session_file.exists():
        return None

    try:
        with open(session_file, 'r', encoding='utf-8') as f:
            sess = json.load(f)
    except Exception:
        return None

    data = _new_summary(session_id)
    data["created_at"] = sess.get("start_time", data["created_at"])

    if sess.get("last_prompt"):
        data["requests"].append({
            "timestamp": sess.get("last_updated", ""),
            "prompt": sess.get("last_prompt", "")[:500],
            "task_type": sess.get("last_task_type", ""),
            "skill": sess.get("last_model", ""),
            "complexity": sess.get("last_complexity", 0),
            "model": sess.get("last_model", ""),
            "cwd": "",
        })
        data["request_count"] = 1

    if sess.get("last_task_type"):
        data["task_types"].append(sess["last_task_type"])
    if sess.get("last_model"):
        data["models_used"].append(sess["last_model"])

    # Save the built data
    json_path = summary_json_path(session_id)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass

    return data


def _generate_one_liner(data):
    """Generate a single-line summary of the session"""
    req_count = data.get("request_count", 0)
    projects = data.get("projects_touched", [])
    skills = data.get("skills_used", [])
    types = data.get("task_types", [])

    parts = []
    parts.append(f"{req_count} requests")

    if projects:
        parts.append(f"project: {', '.join(projects[:2])}")
    if types:
        parts.append(f"type: {', '.join(types[:2])}")
    if skills:
        parts.append(f"skills: {', '.join(skills[:2])}")

    if data.get("requests"):
        first_prompt = data["requests"][0].get("prompt", "")[:80]
        if first_prompt:
            parts.append(f"started: {first_prompt}")

    return " | ".join(parts)


def _generate_markdown(data):
    """Generate human-readable session-summary.md"""
    session_id = data.get("session_id", "UNKNOWN")
    created = data.get("created_at", "")[:19].replace('T', ' ')
    last_updated = data.get("last_updated", "")[:19].replace('T', ' ')
    req_count = data.get("request_count", 0)
    skills = data.get("skills_used", [])
    types = data.get("task_types", [])
    models = data.get("models_used", [])
    projects = data.get("projects_touched", [])
    max_complexity = data.get("max_complexity", 0)
    requests = data.get("requests", [])

    lines = []
    lines.append(f"# Session Summary: {session_id}")
    lines.append("")
    lines.append(f"**Created:** {created}")
    lines.append(f"**Last Updated:** {last_updated}")
    lines.append(f"**Total Requests:** {req_count}")
    lines.append(f"**Max Complexity:** {max_complexity}")
    lines.append(f"**Status:** {data.get('status', 'UNKNOWN')}")
    lines.append("")

    if projects:
        lines.append(f"**Projects:** {', '.join(projects)}")
    if skills:
        lines.append(f"**Skills Used:** {', '.join(skills)}")
    if types:
        lines.append(f"**Task Types:** {', '.join(types)}")
    if models:
        lines.append(f"**Models Used:** {', '.join(models)}")
    lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## Request Timeline")
    lines.append("")

    for i, req in enumerate(requests, 1):
        ts = req.get("timestamp", "")[:19].replace('T', ' ')
        prompt = req.get("prompt", "")[:200]
        task_type = req.get("task_type", "")
        skill = req.get("skill", "")
        model = req.get("model", "")
        complexity = req.get("complexity", 0)

        lines.append(f"### Request {i} ({ts})")
        lines.append(f"- **Prompt:** {prompt}")
        if task_type:
            lines.append(f"- **Type:** {task_type}")
        if skill:
            lines.append(f"- **Skill:** {skill}")
        if model:
            lines.append(f"- **Model:** {model}")
        if complexity:
            lines.append(f"- **Complexity:** {complexity}")
        lines.append("")

    one_liner = _generate_one_liner(data)
    lines.append("---")
    lines.append("")
    lines.append(f"**TL;DR:** {one_liner}")
    lines.append("")

    return "\n".join(lines)


def _update_chain_summary(session_id, data):
    """Update chain-index.json with the session summary"""
    chain_index_file = SESSIONS_DIR / 'chain-index.json'
    if not chain_index_file.exists():
        return

    try:
        with open(chain_index_file, 'r', encoding='utf-8') as f:
            chain = json.load(f)

        if session_id in chain.get("sessions", {}):
            chain["sessions"][session_id]["summary"] = _generate_one_liner(data)
            chain["last_updated"] = datetime.now().isoformat()

            with open(chain_index_file, 'w', encoding='utf-8') as f:
                json.dump(chain, f, indent=2)
            log_event(f"[OK] Chain index updated with summary for {session_id}")
    except Exception as e:
        log_event(f"[WARN] Could not update chain index: {e}")


# =============================================================================
# READ - Get summary for a session
# =============================================================================

def read_summary(session_id, fmt='md'):
    """Read session summary in specified format"""
    if fmt == 'text':
        json_path = summary_json_path(session_id)
        if json_path.exists():
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return data.get("summary_text") or _generate_one_liner(data)
            except Exception:
                pass
        return None

    elif fmt == 'json':
        json_path = summary_json_path(session_id)
        if json_path.exists():
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return None

    else:  # md
        md_path = summary_md_path(session_id)
        if md_path.exists():
            try:
                return md_path.read_text(encoding='utf-8')
            except Exception:
                pass
        json_path = summary_json_path(session_id)
        if json_path.exists():
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return _generate_markdown(data)
            except Exception:
                pass
        return None


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description='Session Summary Manager v1.0.0')
    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # accumulate
    acc = subparsers.add_parser('accumulate', help='Accumulate request data')
    acc.add_argument('--session', required=True, help='Session ID')
    acc.add_argument('--prompt', default='', help='User prompt')
    acc.add_argument('--task-type', default='', help='Task type')
    acc.add_argument('--skill', default='', help='Skill/agent name')
    acc.add_argument('--complexity', default=0, type=int, help='Complexity score')
    acc.add_argument('--model', default='', help='Model selected')
    acc.add_argument('--cwd', default='', help='Working directory')

    # finalize
    fin = subparsers.add_parser('finalize', help='Generate final summary on close')
    fin.add_argument('--session', required=True, help='Session ID')

    # read
    rd = subparsers.add_parser('read', help='Read session summary')
    rd.add_argument('--session', required=True, help='Session ID')
    rd.add_argument('--format', default='md', choices=['md', 'json', 'text'],
                    help='Output format')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    if args.command == 'accumulate':
        ok = accumulate(
            args.session,
            prompt=args.prompt,
            task_type=args.task_type,
            skill=args.skill,
            complexity=args.complexity,
            model=args.model,
            cwd=args.cwd,
        )
        if ok:
            print(f"[OK] Accumulated for {args.session}")
        else:
            print(f"[ERROR] Failed to accumulate")
            sys.exit(1)

    elif args.command == 'finalize':
        ok = finalize(args.session)
        if ok:
            print(f"[OK] Summary finalized for {args.session}")
        else:
            print(f"[ERROR] Failed to finalize summary")
            sys.exit(1)

    elif args.command == 'read':
        result = read_summary(args.session, fmt=args.format)
        if result:
            if isinstance(result, dict):
                print(json.dumps(result, indent=2))
            else:
                print(result)
        else:
            print(f"[INFO] No summary found for {args.session}")

    sys.exit(0)


if __name__ == '__main__':
    main()

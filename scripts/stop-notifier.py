#!/usr/bin/env python3
"""
Script Name: stop-notifier.py
Version: 3.2.0 (Reliability Enhanced)
Last Modified: 2026-02-24
Description: Stop hook - speaks dynamic English voice updates via LLM.
v3.2.0: Increased LLM timeout (5s -> 15s), retry logic, better error handling
v3.1.0: Non-blocking speak (fire-and-forget), faster LLM (5s timeout), auto work-done detection

VOICE TRIGGERS (3 flag files, checked in priority order):
  1. ~/.claude/.session-start-voice   -> New session started
  2. ~/.claude/.task-complete-voice    -> Task completed
  3. ~/.claude/.session-work-done      -> All work done (written by Claude)

HOW IT WORKS:
  1. Fires on every Claude 'Stop' event (after each AI response)
  2. Checks for any voice flag files (in priority order)
  3. If flag EXISTS: reads context, calls OpenRouter LLM to generate
     a natural dynamic message, speaks it via voice-notifier.py
  4. LLM TIMEOUT: 15 seconds (increased from 5s for reliability)
  5. RETRY LOGIC: Up to 3 retries if LLM fails (flag not deleted)
  6. If all retries fail: uses static English fallback, then deletes flag
  7. If no flags: stays completely silent (most responses)

PERSONALITY: Boss-assistant style
  - Addresses user as "Sir"
  - Professional but warm Indian English
  - Short, clear, natural updates
  - Voice: en-IN-NeerjaNeural

LLM: OpenRouter API (multiple models, longest timeout wins)
API Key: ~/.claude/config/openrouter-api-key
Timeout: 15 seconds (gives API time to respond fully)

Windows-Safe: ASCII only (no Unicode/emojis in print statements)
"""

import sys
import os
import json
import subprocess
from pathlib import Path
from datetime import datetime
from urllib import request as urllib_request

# Windows ASCII-safe encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

MEMORY_BASE = Path.home() / '.claude' / 'memory'
SCRIPTS_DIR = Path.home() / '.claude' / 'scripts'
CURRENT_DIR = SCRIPTS_DIR if SCRIPTS_DIR.exists() else (MEMORY_BASE / 'current')
VOICE_SCRIPT = CURRENT_DIR / 'voice-notifier.py'
FLAG_DIR = Path.home() / '.claude'
API_KEY_FILE = Path.home() / '.claude' / 'config' / 'openrouter-api-key'

# Voice flag files (checked in this priority order)
SESSION_START_FLAG = FLAG_DIR / '.session-start-voice'
TASK_COMPLETE_FLAG = FLAG_DIR / '.task-complete-voice'
WORK_DONE_FLAG = FLAG_DIR / '.session-work-done'

# Log file
STOP_LOG = MEMORY_BASE / 'logs' / 'stop-notifier.log'

# OpenRouter config
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
# Fast models in priority order (cheapest first)
LLM_MODELS = [
    "meta-llama/llama-3.1-8b-instruct",
    "mistralai/mistral-7b-instruct",
    "google/gemini-2.0-flash-001",
]

VOICE_SYSTEM_PROMPT = (
    "You are Neerja, a professional Indian English-speaking female voice assistant. "
    "You address the user as 'Sir'. You are warm, professional, and concise. "
    "Generate a SHORT spoken notification message (1-2 sentences max, under 30 words). "
    "The message will be spoken aloud via text-to-speech, so keep it natural and conversational. "
    "Do NOT use any special characters, markdown, emojis, or formatting. "
    "Just plain spoken English text. Be specific about what happened if context is provided."
)


# =============================================================================
# LOGGING
# =============================================================================

def log_s(msg):
    STOP_LOG.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    try:
        with open(STOP_LOG, 'a', encoding='utf-8') as f:
            f.write(f"{ts} | {msg}\n")
    except Exception:
        pass


# =============================================================================
# READ HOOK STDIN
# =============================================================================

def read_hook_stdin():
    """Read JSON data from Claude Code Stop hook stdin"""
    try:
        if not sys.stdin.isatty():
            raw = sys.stdin.read()
            if raw and raw.strip():
                return json.loads(raw.strip())
    except Exception:
        pass
    return {}


# =============================================================================
# FLAG FILE HELPERS
# =============================================================================

def read_flag(flag_path):
    """Read a flag file's content. Returns content or empty string. Does NOT delete."""
    if not flag_path.exists():
        return ''
    try:
        return flag_path.read_text(encoding='utf-8').strip()
    except Exception as e:
        log_s(f"Error reading flag {flag_path.name}: {e}")
        return ''


def delete_flag(flag_path):
    """Delete a flag file after successful processing."""
    if not flag_path.exists():
        return
    try:
        flag_path.unlink()
        log_s(f"Flag deleted (success): {flag_path.name}")
    except Exception as e:
        log_s(f"Could not delete flag {flag_path.name}: {e}")


def increment_retry(flag_path):
    """Increment retry counter for a flag. Returns True if still has retries."""
    try:
        data = json.loads(flag_path.read_text(encoding='utf-8')) if flag_path.suffix == '.json' else {'retries': 0}
        if not isinstance(data, dict):
            data = {'content': str(data), 'retries': 0}
        retries = data.get('retries', 0)
        if retries < 3:  # Max 3 retries
            data['retries'] = retries + 1
            flag_path.write_text(json.dumps(data), encoding='utf-8')
            log_s(f"Flag retry incremented: {flag_path.name} (attempt {retries + 1}/3)")
            return True
        else:
            log_s(f"Flag max retries exceeded: {flag_path.name} (3/3), giving up")
            return False
    except Exception as e:
        log_s(f"Error incrementing retry for {flag_path.name}: {e}")
        return False


# =============================================================================
# LLM MESSAGE GENERATION (OpenRouter)
# =============================================================================

def load_api_key():
    """Load OpenRouter API key from config file."""
    if not API_KEY_FILE.exists():
        return None
    try:
        return API_KEY_FILE.read_text(encoding='utf-8').strip()
    except Exception:
        return None


def generate_dynamic_message(event_type, context=''):
    """
    Call OpenRouter LLM to generate a natural, dynamic voice message.
    Falls back to None if API fails (caller uses static fallback).
    v3.2.0: Better error logging, longer timeout (15s), multiple model fallback
    """
    api_key = load_api_key()
    if not api_key:
        log_s(f"[llm] No API key found for {event_type} - using static message")
        return None

    log_s(f"[llm] Starting LLM call for {event_type} (timeout: 15s, retries: 3 models)")

    hour = datetime.now().hour
    if hour < 12:
        time_context = "morning"
    elif hour < 17:
        time_context = "afternoon"
    else:
        time_context = "evening"

    # Build the user prompt based on event type
    if event_type == 'session_start':
        user_prompt = (
            f"It is {time_context}. A new coding session just started. "
            f"Generate a greeting for the user. "
            f"Context: {context}" if context else
            f"It is {time_context}. A new coding session just started. "
            f"Generate a brief greeting for the user."
        )
    elif event_type == 'task_complete':
        user_prompt = (
            f"A coding task was just completed. Context: {context}. "
            f"Generate a brief completion notification."
        )
    elif event_type == 'work_done':
        user_prompt = (
            f"All coding tasks for this session are done. Summary: {context}. "
            f"Generate a brief wrap-up notification."
        )
    else:
        user_prompt = f"Generate a brief notification. Context: {context}"

    # Try each model until one works
    for attempt, model in enumerate(LLM_MODELS, 1):
        try:
            log_s(f"[llm] Attempt {attempt}/{len(LLM_MODELS)}: {model}")

            payload = json.dumps({
                "model": model,
                "messages": [
                    {"role": "system", "content": VOICE_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                "max_tokens": 60,
                "temperature": 0.7,
            }).encode('utf-8')

            req = urllib_request.Request(
                OPENROUTER_URL,
                data=payload,
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {api_key}',
                    'HTTP-Referer': 'https://claude-code-voice.local',
                    'X-Title': 'Claude Code Voice',
                },
                method='POST'
            )

            # v3.2.0: Increased timeout from 5s to 15s for API reliability
            # Allows OpenRouter sufficient time to generate response
            log_s(f"[llm] Connecting to OpenRouter (timeout: 15s)...")
            with urllib_request.urlopen(req, timeout=15) as resp:
                result = json.loads(resp.read().decode('utf-8'))
                message = result.get('choices', [{}])[0].get('message', {}).get('content', '').strip()

                if message:
                    # Clean up any markdown or special chars
                    message = message.replace('*', '').replace('#', '').replace('`', '')
                    message = message.replace('\n', ' ').strip()
                    # Remove quotes if the LLM wrapped it
                    if message.startswith('"') and message.endswith('"'):
                        message = message[1:-1]
                    log_s(f"[llm] SUCCESS ({model}): {message[:80]}")
                    return message
                else:
                    log_s(f"[llm] {model} returned empty message, trying next...")

        except urllib_request.URLError as e:
            log_s(f"[llm] {model} URL error (network/timeout): {str(e)[:80]}")
            continue
        except Exception as e:
            error_type = type(e).__name__
            error_msg = str(e)[:80]
            log_s(f"[llm] {model} failed ({error_type}): {error_msg}")
            continue

    log_s(f"[llm] All {len(LLM_MODELS)} models failed - will use static fallback message")
    return None


# =============================================================================
# SPEAK VIA voice-notifier.py
# =============================================================================

def speak(text):
    """
    Launch voice-notifier.py as DETACHED process (fire-and-forget).
    v3.1.0: Changed from subprocess.run (BLOCKING) to subprocess.Popen (NON-BLOCKING).
    Root cause fix: subprocess.run waited for audio to finish, causing hook timeout kills.
    Now the voice process runs independently - stop-notifier exits immediately.
    """
    if not text or not text.strip():
        return

    if not VOICE_SCRIPT.exists():
        log_s(f"[ERROR] voice-notifier.py not found at {VOICE_SCRIPT}")
        return

    try:
        creation_flags = 0
        if sys.platform == 'win32':
            creation_flags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NO_WINDOW

        subprocess.Popen(
            [sys.executable, str(VOICE_SCRIPT), text],
            creationflags=creation_flags,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            close_fds=True,
        )
        log_s(f"[voice] Launched (detached): {text[:80]}")
    except Exception as e:
        log_s(f"[voice] Error launching detached: {e}")


# =============================================================================
# STATIC FALLBACK MESSAGES (English, boss-assistant style)
# =============================================================================

def get_session_start_default():
    """Static fallback for session start greeting."""
    hour = datetime.now().hour
    if hour < 12:
        greeting = "Good morning"
    elif hour < 17:
        greeting = "Good afternoon"
    else:
        greeting = "Good evening"
    return f"{greeting} Sir. New session started. I am ready for your commands."


def get_task_complete_default():
    """Static fallback for task completion."""
    return "Sir, task completed successfully. What would you like to do next?"


def get_work_done_default():
    """Static fallback for all-work-done."""
    return "Sir, all tasks are completed. Everything looks good. Let me know if you need anything else."


# =============================================================================
# MAIN
# =============================================================================

def main():
    # INTEGRATION: Load git commit policies from scripts/architecture/
    try:
        from pathlib import Path
        import subprocess
        script_dir = Path(__file__).parent
        git_commit_script = script_dir / 'architecture' / '03-execution-system' / '09-git-commit' / 'auto-commit-enforcer.py'
        if git_commit_script.exists():
            subprocess.run([sys.executable, str(git_commit_script)], timeout=5, capture_output=True)
    except:
        pass  # Policy execution is optional

    hook_data = read_hook_stdin()

    # Track which flags we found
    spoke_something = False

    # PRIORITY 1: Session start voice
    if SESSION_START_FLAG.exists():
        context = read_flag(SESSION_START_FLAG)
        # Try LLM first for dynamic message
        message = generate_dynamic_message('session_start', context)
        if message:
            # LLM succeeded - delete flag and speak
            log_s(f"[session-start] LLM success, speaking: {message[:80]}")
            print(f"[VOICE] Session start notification...")
            speak(message)
            delete_flag(SESSION_START_FLAG)
            spoke_something = True
        else:
            # LLM failed - use fallback
            if increment_retry(SESSION_START_FLAG):
                # Still has retries - will retry next time
                message = context if context else get_session_start_default()
                log_s(f"[session-start] LLM failed, speaking fallback: {message[:80]}")
                print(f"[VOICE] Session start notification (fallback)...")
                speak(message)
                spoke_something = True
            else:
                # Max retries exceeded - use fallback and delete flag
                message = context if context else get_session_start_default()
                log_s(f"[session-start] Max retries, speaking fallback: {message[:80]}")
                print(f"[VOICE] Session start notification (final)...")
                speak(message)
                delete_flag(SESSION_START_FLAG)
                spoke_something = True

    # PRIORITY 2: Task complete voice
    if TASK_COMPLETE_FLAG.exists():
        context = read_flag(TASK_COMPLETE_FLAG)
        message = generate_dynamic_message('task_complete', context)
        if message:
            log_s(f"[task-complete] LLM success, speaking: {message[:80]}")
            print(f"[VOICE] Task completion notification...")
            speak(message)
            delete_flag(TASK_COMPLETE_FLAG)
            spoke_something = True
        else:
            if increment_retry(TASK_COMPLETE_FLAG):
                message = context if context else get_task_complete_default()
                log_s(f"[task-complete] LLM failed, speaking fallback: {message[:80]}")
                print(f"[VOICE] Task completion notification (fallback)...")
                speak(message)
                spoke_something = True
            else:
                message = context if context else get_task_complete_default()
                log_s(f"[task-complete] Max retries, speaking fallback: {message[:80]}")
                print(f"[VOICE] Task completion notification (final)...")
                speak(message)
                delete_flag(TASK_COMPLETE_FLAG)
                spoke_something = True

    # PRIORITY 3: All work done voice (MOST IMPORTANT - always ensure it plays)
    if WORK_DONE_FLAG.exists():
        context = read_flag(WORK_DONE_FLAG)
        message = generate_dynamic_message('work_done', context)
        if message:
            log_s(f"[work-done] LLM success, speaking: {message[:80]}")
            print(f"[VOICE] All work completed notification...")
            speak(message)
            delete_flag(WORK_DONE_FLAG)
            spoke_something = True
        else:
            if increment_retry(WORK_DONE_FLAG):
                message = context if context else get_work_done_default()
                log_s(f"[work-done] LLM failed, speaking fallback: {message[:80]}")
                print(f"[VOICE] All work completed notification (fallback)...")
                speak(message)
                spoke_something = True
            else:
                # CRITICAL: This must always speak - most important notification
                message = context if context else get_work_done_default()
                log_s(f"[work-done] FINAL ATTEMPT - speaking: {message[:80]}")
                print(f"[VOICE] SESSION COMPLETE NOTIFICATION...")
                speak(message)
                delete_flag(WORK_DONE_FLAG)
                spoke_something = True

    if not spoke_something:
        log_s("[OK] Stop hook fired | No voice flags found (normal, most stops are silent)")

    sys.exit(0)


if __name__ == '__main__':
    main()

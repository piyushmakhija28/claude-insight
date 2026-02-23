#!/usr/bin/env python3
"""
Script Name: stop-notifier.py
Version: 3.0.0
Last Modified: 2026-02-23
Description: Stop hook - speaks dynamic English voice updates via LLM.

VOICE TRIGGERS (3 flag files, checked in priority order):
  1. ~/.claude/.session-start-voice   -> New session started
  2. ~/.claude/.task-complete-voice    -> Task completed
  3. ~/.claude/.session-work-done      -> All work done (written by Claude)

HOW IT WORKS:
  1. Fires on every Claude 'Stop' event (after each AI response)
  2. Checks for any voice flag files (in priority order)
  3. If flag EXISTS: reads context, calls OpenRouter LLM to generate
     a natural dynamic message, speaks it via voice-notifier.py
  4. If LLM fails: falls back to static English defaults
  5. If no flags: stays completely silent (most responses)

PERSONALITY: Boss-assistant style
  - Addresses user as "Sir"
  - Professional but warm Indian English
  - Short, clear, natural updates
  - Voice: en-IN-NeerjaNeural

LLM: OpenRouter API (google/gemma-2-9b-it:free or fallback models)
API Key: ~/.claude/config/openrouter-api-key

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
CURRENT_DIR = MEMORY_BASE / 'current'
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

def read_and_delete_flag(flag_path):
    """Read a flag file's content and delete it. Returns content or empty string."""
    if not flag_path.exists():
        return ''
    try:
        content = flag_path.read_text(encoding='utf-8').strip()
    except Exception as e:
        log_s(f"Error reading flag {flag_path.name}: {e}")
        content = ''
    try:
        flag_path.unlink()
        log_s(f"Flag deleted: {flag_path.name}")
    except Exception as e:
        log_s(f"Could not delete flag {flag_path.name}: {e}")
    return content


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
    """
    api_key = load_api_key()
    if not api_key:
        log_s("[llm] No API key found - using static message")
        return None

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
    for model in LLM_MODELS:
        try:
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

            with urllib_request.urlopen(req, timeout=8) as resp:
                result = json.loads(resp.read().decode('utf-8'))
                message = result.get('choices', [{}])[0].get('message', {}).get('content', '').strip()

                if message:
                    # Clean up any markdown or special chars
                    message = message.replace('*', '').replace('#', '').replace('`', '')
                    message = message.replace('\n', ' ').strip()
                    # Remove quotes if the LLM wrapped it
                    if message.startswith('"') and message.endswith('"'):
                        message = message[1:-1]
                    log_s(f"[llm] Generated ({model}): {message[:80]}")
                    return message

        except Exception as e:
            log_s(f"[llm] {model} failed: {str(e)[:60]}")
            continue

    log_s("[llm] All models failed - using static fallback")
    return None


# =============================================================================
# SPEAK VIA voice-notifier.py
# =============================================================================

def speak(text):
    """Call voice-notifier.py to speak the message"""
    if not text or not text.strip():
        return

    if not VOICE_SCRIPT.exists():
        log_s(f"[ERROR] voice-notifier.py not found at {VOICE_SCRIPT}")
        print(f"[VOICE] {text}")
        return

    try:
        result = subprocess.run(
            [sys.executable, str(VOICE_SCRIPT), text],
            timeout=25,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        log_s(f"[voice] Spoke (rc={result.returncode}): {text[:80]}")
    except subprocess.TimeoutExpired:
        log_s("[voice] Timeout - audio still playing in background")
    except Exception as e:
        log_s(f"[voice] Error: {e}")
        print(f"[VOICE] {text}")


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
    hook_data = read_hook_stdin()

    # Track which flags we found
    spoke_something = False

    # PRIORITY 1: Session start voice
    if SESSION_START_FLAG.exists():
        context = read_and_delete_flag(SESSION_START_FLAG)
        # Try LLM first for dynamic message
        message = generate_dynamic_message('session_start', context)
        if not message:
            message = context if context else get_session_start_default()
        log_s(f"[session-start] Speaking: {message[:80]}")
        print(f"[VOICE] Session start notification...")
        speak(message)
        spoke_something = True

    # PRIORITY 2: Task complete voice
    if TASK_COMPLETE_FLAG.exists():
        context = read_and_delete_flag(TASK_COMPLETE_FLAG)
        message = generate_dynamic_message('task_complete', context)
        if not message:
            message = context if context else get_task_complete_default()
        log_s(f"[task-complete] Speaking: {message[:80]}")
        print(f"[VOICE] Task completion notification...")
        speak(message)
        spoke_something = True

    # PRIORITY 3: All work done voice
    if WORK_DONE_FLAG.exists():
        context = read_and_delete_flag(WORK_DONE_FLAG)
        message = generate_dynamic_message('work_done', context)
        if not message:
            message = context if context else get_work_done_default()
        log_s(f"[work-done] Speaking: {message[:80]}")
        print(f"[VOICE] All work completed notification...")
        speak(message)
        spoke_something = True

    if not spoke_something:
        log_s("Stop hook fired | No voice flags found")

    sys.exit(0)


if __name__ == '__main__':
    main()

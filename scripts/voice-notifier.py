#!/usr/bin/env python3
"""
Script Name: voice-notifier.py
Version: 2.1.0
Last Modified: 2026-02-23
Description: Text-to-Speech notifier with Indian English female voice.
             Uses edge-tts (Microsoft Neural TTS - FREE, no API key needed)
             with pyttsx3 as offline fallback.

             Primary Voice: en-IN-NeerjaNeural (Indian English Female)
             Fallback Voice: Windows SAPI5 female (Microsoft Zira / Heera)
             Personality: Boss-assistant style (addresses user as Sir)
             Language: English only

             Auto-installs: edge-tts, pyttsx3 if not present

Windows-Safe: ASCII only output (no Unicode/emojis)
"""

import sys
import os
import subprocess
import tempfile
from pathlib import Path
from datetime import datetime

# Windows ASCII-safe encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

VOICE_LOG = Path.home() / '.claude' / 'memory' / 'logs' / 'voice-notifier.log'
# Fixed output file - gets overwritten each time (no temp file cleanup issues)
VOICE_OUT_FILE = Path.home() / '.claude' / 'memory' / 'logs' / 'last-voice.mp3'

# Indian English female voice - neural quality, natural pronunciation
EDGE_TTS_VOICE = "en-IN-NeerjaNeural"

# Emotion profiles: (rate, pitch) adjustments for edge-tts prosody
# rate: "+N%" faster, "-N%" slower
# pitch: "+NHz" higher, "-NHz" lower
EMOTION_PROFILES = {
    'greeting':  ('+8%',  '+5Hz'),   # Warm, professional - session start
    'done':      ('+5%',  '+3Hz'),   # Satisfied, warm - task complete
    'calm':      ('+0%',  '+0Hz'),   # Default neutral
    'happy':     ('+12%', '+8Hz'),   # Cheerful - all work done
    'concerned': ('-5%',  '-3Hz'),   # Worried, slower
}

def detect_emotion(text):
    """
    Auto-detect emotion from text content to pick right prosody.
    Returns emotion key for EMOTION_PROFILES.
    """
    text_lower = text.lower()
    # Session start / greeting signals
    if any(w in text_lower for w in ['session started', 'new session', 'ready for', 'good morning', 'good evening', 'welcome']):
        return 'greeting'
    # All work done signals
    if any(w in text_lower for w in ['all tasks', 'all done', 'everything', 'all completed', 'wrapped up']):
        return 'happy'
    # Task done signals
    if any(w in text_lower for w in ['completed', 'done', 'finished', 'marked complete', "what's next", 'next task']):
        return 'done'
    # Concerned signals
    if any(w in text_lower for w in ['problem', 'error', 'fail', 'issue', 'blocked']):
        return 'concerned'
    return 'calm'


# =============================================================================
# LOGGING
# =============================================================================

def log_v(msg):
    VOICE_LOG.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    try:
        with open(VOICE_LOG, 'a', encoding='utf-8') as f:
            f.write(f"{ts} | {msg}\n")
    except Exception:
        pass


# =============================================================================
# AUTO-INSTALL PACKAGES
# =============================================================================

def try_install(package_name, import_name=None):
    """Auto-install a package if not found"""
    import_name = import_name or package_name.replace('-', '_')
    try:
        __import__(import_name)
        return True
    except ImportError:
        log_v(f"Installing {package_name}...")
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'install', package_name, '-q', '--no-warn-script-location'],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode == 0:
            log_v(f"Installed {package_name} successfully")
            return True
        else:
            log_v(f"Failed to install {package_name}: {result.stderr[:200]}")
            return False


# =============================================================================
# AUDIO PLAYBACK (Windows - non-blocking, detached process)
# =============================================================================

def play_mp3_async(mp3_path):
    """
    Play MP3 file on Windows.
    Tries multiple methods in order of reliability.
    Non-blocking: returns immediately, audio plays in background.
    """
    mp3_str = str(mp3_path)

    # METHOD 1: playsound - non-daemon thread so audio completes even in detached process
    try:
        import threading
        try_install('playsound', 'playsound')
        from playsound import playsound
        t = threading.Thread(target=playsound, args=(mp3_str,), daemon=False)
        t.start()
        log_v(f"[audio] playsound playing: {mp3_path}")
        t.join(timeout=30)  # Wait up to 30s for audio to finish (critical for detached process)
        log_v(f"[audio] playsound done: {mp3_path}")
        return True
    except Exception as e:
        log_v(f"[audio] playsound failed: {e} - trying WMP")

    # METHOD 2: Windows Media Player COM object
    try:
        ps_script = f"""
$wmp = New-Object -ComObject WMPlayer.OCX.7
$wmp.settings.autoStart = $true
$wmp.URL = '{mp3_str}'
$wmp.controls.play()
Start-Sleep -Seconds 20
$wmp.controls.stop()
"""
        subprocess.Popen(
            ['powershell', '-WindowStyle', 'Hidden', '-NonInteractive', '-Command', ps_script],
            creationflags=(subprocess.DETACHED_PROCESS | subprocess.CREATE_NO_WINDOW)
            if sys.platform == 'win32' else 0,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            close_fds=True
        )
        log_v(f"[audio] WMP COM playing: {mp3_path}")
        return True
    except Exception as e:
        log_v(f"[audio] WMP COM failed: {e} - trying Start-Process")

    # METHOD 3: Start-Process (opens default media app)
    try:
        subprocess.Popen(
            ['powershell', '-Command', f'Start-Process "{mp3_str}"'],
            creationflags=(subprocess.DETACHED_PROCESS | subprocess.CREATE_NO_WINDOW)
            if sys.platform == 'win32' else 0,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        log_v(f"[audio] Start-Process playing: {mp3_path}")
        return True
    except Exception as e:
        log_v(f"[audio] All playback methods failed: {e}")
        return False


# =============================================================================
# TTS ENGINE 1: edge-tts (PRIMARY - Indian girl voice, free, online)
# =============================================================================

def speak_edge_tts(text):
    """
    Speak using Microsoft Edge TTS - completely FREE.
    Voice: en-IN-NeerjaNeural = Indian English Female
    No API key needed. Uses Edge browser's neural TTS infrastructure.
    """
    if not try_install('edge-tts', 'edge_tts'):
        return False

    try:
        import asyncio
        import edge_tts

        # Auto-detect emotion and get prosody settings
        emotion = detect_emotion(text)
        rate, pitch = EMOTION_PROFILES.get(emotion, ('+0%', '+0Hz'))
        log_v(f"[emotion] detected={emotion} | rate={rate} | pitch={pitch}")

        async def _generate():
            communicate = edge_tts.Communicate(
                text,
                EDGE_TTS_VOICE,
                rate=rate,
                pitch=pitch
            )
            VOICE_OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
            await communicate.save(str(VOICE_OUT_FILE))

        asyncio.run(_generate())

        if VOICE_OUT_FILE.exists() and VOICE_OUT_FILE.stat().st_size > 0:
            play_mp3_async(VOICE_OUT_FILE)
            log_v(f"[edge-tts:{EDGE_TTS_VOICE}] emotion={emotion} Spoke: {text[:80]}")
            return True
        else:
            log_v("[edge-tts] Generated file is empty or missing")
            return False

    except ImportError:
        log_v("[edge-tts] Import failed after install attempt")
        return False
    except Exception as e:
        log_v(f"[edge-tts] Error: {e}")
        return False


# =============================================================================
# TTS ENGINE 2: pyttsx3 (FALLBACK - offline, Windows SAPI female voice)
# =============================================================================

def speak_pyttsx3(text):
    """
    Fallback TTS using pyttsx3 + Windows SAPI5.
    Works completely offline. Uses Microsoft Zira (US female) or Heera (Indian female).
    """
    if not try_install('pyttsx3', 'pyttsx3'):
        return False

    try:
        import pyttsx3
        engine = pyttsx3.init()
        voices = engine.getProperty('voices')

        if not voices:
            log_v("[pyttsx3] No SAPI voices found")
            return False

        # Prefer Indian/female voices by name
        female_keywords = ['zira', 'heera', 'hazel', 'female', 'woman', 'aria', 'jenny', 'neerja']
        female_id = None
        for voice in voices:
            name_lower = voice.name.lower()
            if any(kw in name_lower for kw in female_keywords):
                female_id = voice.id
                log_v(f"[pyttsx3] Selected voice: {voice.name}")
                break

        if not female_id and len(voices) > 1:
            # Second voice is often female on Windows
            female_id = voices[1].id
            log_v(f"[pyttsx3] Using second voice: {voices[1].name}")
        elif not female_id:
            female_id = voices[0].id
            log_v(f"[pyttsx3] Using first voice: {voices[0].name}")

        engine.setProperty('voice', female_id)
        engine.setProperty('rate', 148)    # Natural speaking pace
        engine.setProperty('volume', 0.95)

        engine.say(text)
        engine.runAndWait()

        log_v(f"[pyttsx3] Spoke: {text[:80]}")
        return True

    except Exception as e:
        log_v(f"[pyttsx3] Error: {e}")
        return False


# =============================================================================
# PUBLIC API
# =============================================================================

def clean_text(text):
    """
    Clean text before speaking - remove backslashes, fix common TTS artifacts.
    Ensures natural speech without reading escape characters.
    """
    # Remove backslashes (bash/shell escape artifacts)
    text = text.replace('\\', '')
    # Remove double spaces
    while '  ' in text:
        text = text.replace('  ', ' ')
    return text.strip()


def speak(text):
    """
    Speak text using the best available TTS engine.
    Order: edge-tts (Indian girl, free) > pyttsx3 (Windows girl) > silent log
    """
    if not text or not text.strip():
        return

    text = clean_text(text)
    log_v(f"speak() called: {text[:100]}")

    # Try edge-tts first (best quality Indian English voice)
    if speak_edge_tts(text):
        return

    # Fallback to pyttsx3 (offline)
    if speak_pyttsx3(text):
        return

    # Silent fallback - at least log it
    log_v(f"[SILENT - no TTS engine available] Would have said: {text}")
    print(f"[VOICE] {text}")


# =============================================================================
# CLI USAGE
# =============================================================================

def main():
    if len(sys.argv) < 2 or sys.argv[1] in ('--help', '-h'):
        print("voice-notifier.py v2.1.0 - Indian English voice TTS")
        print()
        print("Usage:")
        print("  python voice-notifier.py <text to speak>")
        print()
        print("Examples:")
        print('  python voice-notifier.py "Good morning Sir. New session started."')
        print('  python voice-notifier.py "Sir, all tasks completed successfully."')
        print()
        print("Voice: en-IN-NeerjaNeural (Indian English Female)")
        print("Requires: edge-tts (auto-installed), pyttsx3 (fallback)")
        sys.exit(0)

    if sys.argv[1] == '--list-voices':
        try:
            import asyncio
            import edge_tts

            async def _list():
                voices = await edge_tts.list_voices()
                indian = [v for v in voices if 'IN' in v.get('ShortName', '')]
                print("Indian voices in edge-tts:")
                for v in indian:
                    print(f"  {v['ShortName']} - {v['FriendlyName']}")

            asyncio.run(_list())
        except Exception as e:
            print(f"Error listing voices: {e}")
        sys.exit(0)

    text = ' '.join(sys.argv[1:])
    speak(text)


if __name__ == '__main__':
    main()

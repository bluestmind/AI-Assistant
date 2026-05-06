"""
Voice Output — Text-to-Speech engine for JARVIS.

Uses pyttsx3 for offline TTS with a tuned British-style voice.
Runs speech in a background thread to avoid blocking the UI.
"""

import threading
import logging
import pyttsx3

logger = logging.getLogger(__name__)

# Global state to track active engine for interruption
_current_engine = None
_speech_lock = threading.Lock()


def _get_engine() -> pyttsx3.Engine:
    """Create and configure a fresh TTS engine."""
    engine = pyttsx3.init()

    # Try to find a male English voice (closest to JARVIS)
    voices = engine.getProperty("voices")
    for voice in voices:
        name_lower = voice.name.lower()
        if "david" in name_lower or "mark" in name_lower:
            engine.setProperty("voice", voice.id)
            break
        elif "english" in name_lower and "female" not in name_lower:
            engine.setProperty("voice", voice.id)

    engine.setProperty("rate", 170)
    engine.setProperty("volume", 0.9)
    return engine


def stop():
    """Interrupt the current speech."""
    global _current_engine
    if _current_engine:
        try:
            _current_engine.stop()
            logger.info("Speech interrupted by user.")
        except Exception as e:
            logger.error(f"Error stopping TTS: {e}")


def speak(text: str):
    """Speak text aloud in a background thread (non-blocking)."""
    def _speak():
        global _current_engine
        with _speech_lock:
            try:
                _current_engine = _get_engine()
                _current_engine.say(text)
                _current_engine.runAndWait()
                _current_engine.stop()
            except Exception as e:
                logger.error(f"TTS error: {e}")
            finally:
                _current_engine = None

    thread = threading.Thread(target=_speak, daemon=True)
    thread.start()


def speak_sync(text: str):
    """Speak text aloud (blocking). Use for startup/shutdown."""
    global _current_engine
    with _speech_lock:
        try:
            _current_engine = _get_engine()
            _current_engine.say(text)
            _current_engine.runAndWait()
            _current_engine.stop()
        except Exception as e:
            logger.error(f"TTS error: {e}")
        finally:
            _current_engine = None

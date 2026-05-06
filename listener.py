"""
Voice Listener — Handles microphone input and speech-to-text.

Runs in a background thread and pushes recognized text
to a callback function. Uses multiple hypotheses from Google
for better accent handling.
"""

import threading
import logging
import speech_recognition as sr
from config import (
    RECOGNITION_LANGUAGE,
    VOSK_MODEL_PATH,
    ENERGY_THRESHOLD,
    PAUSE_THRESHOLD,
    DYNAMIC_ENERGY,
)
import vosk
import json

logger = logging.getLogger(__name__)


class VoiceListener:
    """Continuous voice listener that runs in a background thread."""

    def __init__(
        self,
        on_result: callable,
        on_hypotheses: callable,
        on_status: callable,
    ):
        """
        Args:
            on_result:     callback(text: str) called with best recognized speech.
            on_hypotheses: callback(texts: list[str]) called with ALL hypotheses.
            on_status:     callback(msg: str) called with status updates.
        """
        self._on_result = on_result
        self._on_hypotheses = on_hypotheses
        self._on_status = on_status
        self._recognizer = sr.Recognizer()
        self._recognizer.energy_threshold = ENERGY_THRESHOLD
        self._recognizer.pause_threshold = PAUSE_THRESHOLD
        self._recognizer.dynamic_energy_threshold = DYNAMIC_ENERGY
        self._running = False
        self._thread: threading.Thread | None = None

    def start(self):
        """Start listening in a background thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """Signal the listener to stop."""
        self._running = False

    @property
    def is_running(self) -> bool:
        return self._running

    def _listen_loop(self):
        """Main loop: listen → recognize → callback."""
        try:
            mic = sr.Microphone()
        except (OSError, AttributeError) as e:
            logger.error(f"Microphone error: {e}")
            self._on_status("❌ No microphone found!")
            self._running = False
            return

        try:
            self._on_status("🧠 Loading Vosk Model...")
            model = vosk.Model(VOSK_MODEL_PATH)
            rec = vosk.KaldiRecognizer(model, 16000)
            rec.SetWords(True)
        except Exception as e:
            logger.error(f"Failed to load Vosk model: {e}")
            self._on_status("❌ Vosk model error!")
            self._running = False
            return

        with mic as source:
            # Longer calibration for better ambient noise baseline
            self._on_status("🔧 Calibrating mic...")
            self._recognizer.adjust_for_ambient_noise(source, duration=2)
            self._on_status("🎤 Listening...")

            while self._running:
                try:
                    audio = self._recognizer.listen(
                        source, timeout=5, phrase_time_limit=6
                    )
                    self._on_status("⏳ Processing...")

                    # ── Process with Vosk ────────────
                    raw_data = audio.get_raw_data(convert_rate=16000, convert_width=2)
                    rec.AcceptWaveform(raw_data)
                    result = json.loads(rec.FinalResult())
                    text = result.get("text", "").strip()

                    if not text:
                        self._on_status("🎤 Listening...")
                        continue

                    hypotheses = [text]
                    best = text
                    logger.info(f"Heard: {best}")

                    # Send the result
                    self._on_result(best)
                    self._on_hypotheses(hypotheses)

                    self._on_status("🎤 Listening...")

                except sr.WaitTimeoutError:
                    # No speech detected within timeout — just keep listening
                    continue
                except sr.UnknownValueError:
                    self._on_status("🎤 Listening...")
                    continue
                except sr.RequestError as e:
                    logger.error(f"API error: {e}")
                    self._on_status("⚠️ Network error, retrying...")
                    continue
                except Exception as e:
                    logger.error(f"Listener error: {e}")
                    continue

        self._on_status("⏹️ Stopped")

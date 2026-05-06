"""
J.A.R.V.I.S. — Entry Point

Just A Rather Very Intelligent System.
Wires together the HUD, Voice Listener, Command Engine, and TTS.
"""

import logging
from ui import JarvisUI
from listener import VoiceListener
import commands
from commands import execute_from_hypotheses
from tts import speak
import jarvis
from memory import Memory
from brain import Brain
import keyboard

# ── Logging ──────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)s │ %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def main():
    # Initialize intelligence
    memory = Memory()
    brain = Brain(model="qwen2.5-coder:7b")  # Using the qwen2.5-coder:7b model
    commands.init(memory, brain)

    listener: VoiceListener | None = None

    # ── Callbacks ────────────────────────────────────────────────
    def on_voice_result(text: str):
        """Best transcript — just for logging."""
        logger.info(f"Best transcript: {text}")

    def on_hypotheses(hypotheses: list[str]):
        """Try all alternatives for best accent handling."""
        result = execute_from_hypotheses(hypotheses)
        top = hypotheses[0] if hypotheses else ""
        if result:
            ui.set_log(f'🗣️  "{top}"\n\n{result}')
            speak(result)  # JARVIS speaks back!
            logger.info(result)

    def on_status(msg: str):
        ui.set_status(msg)

    def on_toggle(is_active: bool):
        """Activate / deactivate JARVIS."""
        nonlocal listener
        if is_active:
            listener = VoiceListener(
                on_result=on_voice_result,
                on_hypotheses=on_hypotheses,
                on_status=on_status,
            )
            listener.start()
            ui.set_active(True)

            greeting = jarvis.get_greeting()
            ui.set_log(greeting)
            speak(greeting)
        else:
            if listener:
                listener.stop()
                listener = None
            ui.set_active(False)
            ui.set_status("Systems on standby.")
            msg = "Going to standby, sir. I'll be here if you need me."
            ui.set_log(msg)
            speak(msg)

    def on_text_command(text: str):
        """Handle text input from the UI."""
        result = commands.execute_command(text)
        if result:
            ui.set_log(f'⌨️  "{text}"\n\n{result}')
            speak(result)

    # ── Launch ───────────────────────────────────────────────────
    ui = JarvisUI(on_toggle=on_toggle, on_command=on_text_command)

    # Global Hotkey (Ctrl+Shift+J)
    try:
        keyboard.add_hotkey('ctrl+shift+j', lambda: ui.toggle_from_hotkey())
        logger.info("Global hotkey registered: Ctrl+Shift+J")
    except Exception as e:
        logger.warning(f"Could not register hotkey: {e}")

    # Startup intro
    intro = jarvis.get_intro()
    ui.set_log(intro)

    try:
        ui.run()
    finally:
        logger.info("J.A.R.V.I.S. shutting down...")
        try:
            keyboard.unhook_all()
        except:
            pass
        if listener:
            listener.stop()


if __name__ == "__main__":
    main()

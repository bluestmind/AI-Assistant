import os
import sys

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

"""
App Registry — Add new apps here to scale the assistant.

Each entry maps a keyword to its executable path and process name.
The assistant will match voice commands against these keywords.

To add a new app, just add a new entry to APP_REGISTRY:
    "appname": {
        "path": r"C:\path\to\app.exe",
        "process": "app.exe",
        "aliases": ["alternative name", "another name"],
    }
"""

APP_REGISTRY = {
    "telegram": {
        "path": r"F:\Telegrams\Telegram Desktop\Telegram.exe",
        "process": "Telegram.exe",
        "aliases": [
            "telegram", "tele", "telegrams", "teligram", "telagram",
            "telegraph", "telegram desktop", "tele gram",
        ],
    },
    "chrome": {
        "path": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        "process": "chrome.exe",
        "aliases": [
            "chrome", "google chrome", "browser", "crome", "krome",
            "google", "web browser",
        ],
    },
    "notepad": {
        "path": r"C:\Windows\notepad.exe",
        "process": "notepad.exe",
        "aliases": ["notepad", "note pad", "notes", "note", "text editor"],
    },
    "calculator": {
        "path": "calc.exe",
        "process": "CalculatorApp.exe",
        "aliases": ["calculator", "calc", "calculate", "calculation"],
    },
    "explorer": {
        "path": "explorer.exe",
        "process": "explorer.exe",
        "aliases": [
            "explorer", "file explorer", "files", "file manager",
            "my computer", "this pc", "folder",
        ],
    },
}

# ── Assistant Identity ───────────────────────────────────────────
ASSISTANT_NAME = "J.A.R.V.I.S."

# ── AI Brain Settings ────────────────────────────────────────────
DEFAULT_MODEL = "qwen2.5-coder:7b"
VISION_MODEL = "llava"

# ── Voice Recognition Settings ───────────────────────────────────
RECOGNITION_LANGUAGE = "en-US"
VOSK_MODEL_PATH = os.path.join(BASE_DIR, "vosk-models", "vosk-model-en-us-0.42-gigaspeech")
ENERGY_THRESHOLD = 300          # Microphone sensitivity (lower = more sensitive)
PAUSE_THRESHOLD = 0.8           # Seconds of silence before phrase is considered complete
DYNAMIC_ENERGY = True           # Auto-adjust to ambient noise

# ── Fuzzy Matching Settings ──────────────────────────────────────
FUZZY_THRESHOLD = 65            # Minimum similarity score (0-100) to consider a match.
                                # Lower = more forgiving with accents, higher = stricter.
                                # 65 works well for non-native speakers.

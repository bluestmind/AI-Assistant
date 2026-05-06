"""
Memory System — Persistent JSON storage for JARVIS.

Stores everything locally in ~/.jarvis/memory.json:
- Notes: user-dictated reminders
- Habits: timestamped command log for pattern analysis
- Custom commands: user-taught multi-step routines
- Conversation history: recent exchanges for LLM context

All data stays on your machine. Nothing leaves.
"""

import json
import os
import logging
from datetime import datetime, timedelta
from collections import Counter

logger = logging.getLogger(__name__)

MEMORY_DIR = os.path.join(os.path.expanduser("~"), ".jarvis")
MEMORY_FILE = os.path.join(MEMORY_DIR, "memory.json")

# Default structure
_DEFAULT_MEMORY = {
    "notes": [],                # [{"text": "...", "created": "ISO timestamp"}]
    "habits": [],               # [{"command": "...", "action": "...", "app": "...", "time": "ISO"}]
    "custom_commands": {},      # {"trigger phrase": ["open chrome", "open telegram"]}
    "conversation": [],         # [{"role": "user/assistant", "content": "..."}]
    "preferences": {},          # {"favorite_app": "chrome", ...}
    "stats": {                  # Usage statistics
        "total_commands": 0,
        "first_use": None,
        "last_use": None,
    },
}

MAX_CONVERSATION_HISTORY = 20  # Keep last N exchanges for LLM context
MAX_HABITS_LOG = 500           # Keep last N habit entries


class Memory:
    """Persistent memory manager for JARVIS."""

    def __init__(self):
        self._data = None
        self._load()

    # ── Persistence ──────────────────────────────────────────────

    def _load(self):
        """Load memory from disk, or create fresh."""
        os.makedirs(MEMORY_DIR, exist_ok=True)
        if os.path.exists(MEMORY_FILE):
            try:
                with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
                # Ensure all keys exist (upgrade-safe)
                for key, default in _DEFAULT_MEMORY.items():
                    if key not in self._data:
                        self._data[key] = default
                logger.info(f"Memory loaded: {len(self._data['notes'])} notes, "
                           f"{len(self._data['habits'])} habit entries")
            except Exception as e:
                logger.error(f"Failed to load memory: {e}")
                self._data = json.loads(json.dumps(_DEFAULT_MEMORY))
        else:
            self._data = json.loads(json.dumps(_DEFAULT_MEMORY))
            self._save()
            logger.info("Fresh memory initialized")

    def _save(self):
        """Save memory to disk."""
        try:
            os.makedirs(MEMORY_DIR, exist_ok=True)
            with open(MEMORY_FILE, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save memory: {e}")

    # ── Notes ────────────────────────────────────────────────────

    def add_note(self, text: str) -> int:
        """Save a note. Returns the note index (1-based)."""
        note = {
            "text": text,
            "created": datetime.now().isoformat(),
        }
        self._data["notes"].append(note)
        self._save()
        return len(self._data["notes"])

    def get_notes(self) -> list[dict]:
        """Get all notes."""
        return self._data["notes"]

    def delete_note(self, index: int) -> bool:
        """Delete a note by 1-based index."""
        idx = index - 1
        if 0 <= idx < len(self._data["notes"]):
            self._data["notes"].pop(idx)
            self._save()
            return True
        return False

    def clear_notes(self):
        """Clear all notes."""
        self._data["notes"] = []
        self._save()

    # ── Habits ───────────────────────────────────────────────────

    def log_habit(self, command: str, action: str = "", app: str = ""):
        """Log a command for habit tracking."""
        entry = {
            "command": command,
            "action": action,
            "app": app,
            "time": datetime.now().isoformat(),
            "hour": datetime.now().hour,
            "weekday": datetime.now().strftime("%A"),
        }
        self._data["habits"].append(entry)
        # Trim old entries
        if len(self._data["habits"]) > MAX_HABITS_LOG:
            self._data["habits"] = self._data["habits"][-MAX_HABITS_LOG:]
        # Update stats
        self._data["stats"]["total_commands"] = self._data["stats"].get("total_commands", 0) + 1
        if not self._data["stats"].get("first_use"):
            self._data["stats"]["first_use"] = datetime.now().isoformat()
        self._data["stats"]["last_use"] = datetime.now().isoformat()
        self._save()

    def get_top_apps(self, n: int = 5) -> list[tuple[str, int]]:
        """Get the most frequently used apps."""
        apps = [h["app"] for h in self._data["habits"] if h.get("app")]
        return Counter(apps).most_common(n)

    def get_habits_by_hour(self) -> dict[int, list[str]]:
        """Group app usage by hour of day."""
        by_hour = {}
        for h in self._data["habits"]:
            if h.get("app"):
                hour = h.get("hour", 0)
                if hour not in by_hour:
                    by_hour[hour] = []
                by_hour[hour].append(h["app"])
        return by_hour

    def get_habit_summary(self) -> str:
        """Generate a human-readable habit summary."""
        if not self._data["habits"]:
            return "I haven't collected enough data yet, sir. Keep using me and I'll learn your patterns."

        top_apps = self.get_top_apps(3)
        by_hour = self.get_habits_by_hour()
        total = self._data["stats"].get("total_commands", 0)

        summary = f"Based on {total} commands, sir: "

        if top_apps:
            top_list = ", ".join(f"{app} ({count}x)" for app, count in top_apps)
            summary += f"Your most used apps are {top_list}. "

        # Find peak hours
        if by_hour:
            hour_counts = {h: len(apps) for h, apps in by_hour.items()}
            peak_hour = max(hour_counts, key=hour_counts.get)
            period = "morning" if peak_hour < 12 else "afternoon" if peak_hour < 17 else "evening"
            summary += f"You're most active in the {period} around {peak_hour}:00."

        return summary

    # ── Custom Commands ──────────────────────────────────────────

    def add_custom_command(self, trigger: str, actions: list[str]):
        """Save a custom compound command."""
        self._data["custom_commands"][trigger.lower()] = actions
        self._save()

    def get_custom_command(self, trigger: str) -> list[str] | None:
        """Look up a custom command by trigger phrase."""
        return self._data["custom_commands"].get(trigger.lower())

    def get_all_custom_commands(self) -> dict:
        """Get all custom commands."""
        return self._data["custom_commands"]

    def delete_custom_command(self, trigger: str) -> bool:
        """Delete a custom command."""
        if trigger.lower() in self._data["custom_commands"]:
            del self._data["custom_commands"][trigger.lower()]
            self._save()
            return True
        return False

    # ── Conversation History ─────────────────────────────────────

    def add_conversation(self, role: str, content: str):
        """Add a message to conversation history."""
        self._data["conversation"].append({
            "role": role,
            "content": content,
        })
        # Trim to max
        if len(self._data["conversation"]) > MAX_CONVERSATION_HISTORY * 2:
            self._data["conversation"] = self._data["conversation"][-MAX_CONVERSATION_HISTORY * 2:]
        self._save()

    def get_conversation(self) -> list[dict]:
        """Get conversation history for LLM context."""
        return self._data["conversation"]

    def clear_conversation(self):
        """Clear conversation history."""
        self._data["conversation"] = []
        self._save()

    # ── Stats ────────────────────────────────────────────────────

    def get_stats(self) -> dict:
        return self._data["stats"]

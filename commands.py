"""
Command Engine — Parses voice text and executes actions.

Priority order:
1. Custom commands (user-taught)
2. Built-in commands (open/close, time, date, status)
3. Memory commands (remember, recall, forget)
4. Habit queries
5. FALLBACK → Ollama AI (anything else gets an intelligent answer)

Uses fuzzy matching for accent tolerance.
Uses JARVIS personality for all responses.
"""

import subprocess
import os
import re
import logging
from thefuzz import fuzz
from config import APP_REGISTRY, FUZZY_THRESHOLD
import jarvis
import tts
import vision
import pyautogui
import time

logger = logging.getLogger(__name__)

# These get injected by main.py after initialization
_memory = None
_brain = None


def init(memory, brain):
    """Initialize with memory and brain references."""
    global _memory, _brain
    _memory = memory
    _brain = brain


# ── Fuzzy App Finder ─────────────────────────────────────────────

def _build_alias_map() -> dict[str, tuple[str, dict]]:
    alias_map = {}
    for app_name, app_info in APP_REGISTRY.items():
        all_names = [app_name] + app_info.get("aliases", [])
        for name in all_names:
            alias_map[name.lower()] = (app_name, app_info)
    return alias_map


_ALIAS_MAP = _build_alias_map()


def _find_app(text: str) -> tuple[str, dict, int] | None:
    text_lower = text.lower()

    for alias, (app_name, app_info) in _ALIAS_MAP.items():
        if alias in text_lower:
            return app_name, app_info, 100

    words = text_lower.split()
    candidates = list(words)
    for i in range(len(words) - 1):
        candidates.append(f"{words[i]} {words[i+1]}")

    best_score = 0
    best_match = None
    all_aliases = list(_ALIAS_MAP.keys())

    for candidate in candidates:
        for alias in all_aliases:
            score = max(
                fuzz.ratio(candidate, alias),
                fuzz.partial_ratio(candidate, alias),
                fuzz.token_sort_ratio(candidate, alias),
            )
            if score > best_score:
                best_score = score
                best_match = alias

    if best_match and best_score >= FUZZY_THRESHOLD:
        app_name, app_info = _ALIAS_MAP[best_match]
        logger.info(f"Fuzzy: '{text}' → '{best_match}' (score: {best_score})")
        return app_name, app_info, best_score

    return None


# ── Command Classification ───────────────────────────────────────

_OPEN_WORDS = ["open", "start", "launch", "run", "begin", "execute", "load"]
_CLOSE_WORDS = ["close", "stop", "kill", "quit", "exit", "shut", "end", "terminate"]
_TIME_WORDS = ["time", "clock", "hour"]
_DATE_WORDS = ["date", "day", "today", "calendar"]
_STATUS_WORDS = ["status", "system", "diagnostics", "health", "report", "cpu", "battery"]
_REMEMBER_WORDS = ["remember", "save", "store", "note", "memorize", "keep"]
_RECALL_WORDS = ["recall", "notes", "memories", "what did i tell", "what do you remember"]
_FORGET_WORDS = ["forget", "delete note", "remove note", "clear notes"]
_HABIT_WORDS = ["habits", "habit", "usage", "most used", "patterns", "analytics"]
_LEARN_WORDS = ["learn", "teach", "create command", "new command", "custom command"]
_CLEAR_WORDS = ["clear context", "reset context", "forget conversation", "new conversation"]
_STOP_WORDS = ["stop", "shut up", "quiet", "silence", "be quiet", "stop talking", "stop saying", "enough", "hush"]
_VISION_SCREEN_WORDS = ["look at my screen", "what's on my screen", "what is this on screen", "screen analysis", "see my screen"]
_VISION_WEBCAM_WORDS = ["what do you see", "what is this", "describe what you see", "look at this", "who is this", "what am i holding"]
_MOUSE_MOVE_WORDS = ["move mouse to", "cursor to", "move cursor to"]
_MOUSE_CLICK_WORDS = ["click", "left click", "right click", "double click"]
_MOUSE_SCROLL_WORDS = ["scroll up", "scroll down"]


def _classify(text: str) -> str:
    """Classify the command type."""
    t = text.lower()
    words = t.split()

    # Memory commands (check before utility — "remember" is specific)
    for phrase in _RECALL_WORDS:
        if phrase in t:
            return "recall"
    for phrase in _FORGET_WORDS:
        if phrase in t:
            return "forget"
    for word in words:
        if word in _REMEMBER_WORDS and len(words) > 2:
            return "remember"

    # Habit queries
    for word in words:
        if word in _HABIT_WORDS:
            return "habits"

    # Custom command learning
    for word in words:
        if word in _LEARN_WORDS:
            return "learn"

    # Clear conversation
    for phrase in _CLEAR_WORDS:
        if phrase in t:
            return "clear"

    # Stop command
    for phrase in _STOP_WORDS:
        if phrase in t:
            return "stop"

    # Utility commands
    for word in words:
        if word in _TIME_WORDS:
            return "time"
        if word in _DATE_WORDS:
            return "date"
        if word in _STATUS_WORDS:
            return "status"

    # App commands
    for word in words:
        if word in _OPEN_WORDS:
            return "open"
        if word in _CLOSE_WORDS:
            return "close"

    # Fuzzy fallback for app commands
    for word in words:
        for target in _OPEN_WORDS:
            if fuzz.ratio(word, target) >= 75:
                return "open"
        for target in _CLOSE_WORDS:
            if fuzz.ratio(word, target) >= 75:
                return "close"

    # Vision commands
    for phrase in _VISION_SCREEN_WORDS:
        if phrase in t:
            return "vision_screen"
    for phrase in _VISION_WEBCAM_WORDS:
        if phrase in t:
            return "vision_webcam"

    # Mouse commands
    for phrase in _MOUSE_MOVE_WORDS:
        if phrase in t:
            return "mouse_move"
    for phrase in _MOUSE_CLICK_WORDS:
        if phrase in t:
            return "mouse_click"
    for phrase in _MOUSE_SCROLL_WORDS:
        if phrase in t:
            return "mouse_scroll"

    return "ai"  # Everything else → Ollama


# ── Action Handlers ──────────────────────────────────────────────

def handle_open(app_name: str, app_info: dict) -> str:
    path = app_info["path"]
    if not os.path.isfile(path) and not os.path.basename(path) == path:
        return jarvis.app_not_found(app_name, path)
    try:
        subprocess.Popen(
            [path], shell=False,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        return jarvis.app_opened(app_name)
    except Exception as e:
        logger.error(f"Failed to open {app_name}: {e}")
        return jarvis.app_failed(app_name)


def handle_close(app_name: str, app_info: dict) -> str:
    process = app_info["process"]
    
    # Safety: Do not allow closing explorer.exe or other system criticals
    if process.lower() == "explorer.exe":
        return "I'm afraid I cannot close File Explorer, sir. It is a critical system process."
    
    try:
        result = subprocess.run(
            ["taskkill", "/IM", process, "/F"],
            capture_output=True, text=True,
        )
        if result.returncode == 0:
            return jarvis.app_closed(app_name)
        else:
            return jarvis.app_not_running(app_name)
    except Exception as e:
        logger.error(f"Failed to close {app_name}: {e}")
        return jarvis.app_failed(app_name)


# ── Memory Handlers ──────────────────────────────────────────────

def handle_remember(text: str) -> str:
    """Extract and save a note from the voice text."""
    # Strip out the "remember" trigger word
    clean = text.lower()
    for word in _REMEMBER_WORDS:
        clean = clean.replace(word, "", 1)
    clean = re.sub(r"^[\s,.:;that\s]+", "", clean).strip()

    if not clean:
        return "What would you like me to remember, sir?"

    idx = _memory.add_note(clean)
    return f"Noted, sir. I've saved that as note #{idx}: \"{clean}\""


def handle_recall() -> str:
    """List all saved notes."""
    notes = _memory.get_notes()
    if not notes:
        return "I don't have any saved notes, sir."

    lines = [f"I have {len(notes)} note{'s' if len(notes) > 1 else ''} on file, sir:"]
    for i, note in enumerate(notes, 1):
        lines.append(f"  #{i}: {note['text']}")
    return "\n".join(lines)


def handle_forget(text: str) -> str:
    """Delete a note or clear all."""
    t = text.lower()
    if "all" in t or "clear" in t:
        _memory.clear_notes()
        return "All notes cleared, sir."

    # Try to find a number
    numbers = re.findall(r"\d+", text)
    if numbers:
        idx = int(numbers[0])
        if _memory.delete_note(idx):
            return f"Note #{idx} deleted, sir."
        else:
            return f"I couldn't find note #{idx}, sir."

    return "Which note should I forget, sir? Say a number or 'all'."


def handle_habits() -> str:
    """Report usage habits."""
    return _memory.get_habit_summary()


def handle_learn(text: str) -> str:
    """Teach JARVIS a custom command."""
    # Expected: "learn when I say work mode open chrome and telegram"
    # or: "learn work mode means open chrome and open telegram"
    t = text.lower()

    # Try to parse: "when I say [trigger], [actions]"
    patterns = [
        r"(?:learn|teach).*?when i say (.+?),?\s*(open|close|launch|start)(.+)",
        r"(?:learn|teach)\s+(.+?)\s+(?:means?|is)\s+(.+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, t)
        if match:
            groups = match.groups()
            trigger = groups[0].strip()
            rest = " ".join(groups[1:]).strip()
            actions = [a.strip() for a in re.split(r"\s+and\s+", rest) if a.strip()]

            if trigger and actions:
                _memory.add_custom_command(trigger, actions)
                return (
                    f"Understood, sir. When you say \"{trigger}\", "
                    f"I'll execute: {', '.join(actions)}."
                )

    return (
        "I didn't quite catch the pattern, sir. "
        "Try: \"Learn when I say work mode, open Chrome and open Telegram\""
    )


def handle_custom_command(trigger: str) -> str | None:
    """Check if text matches a custom command and execute it."""
    if not _memory:
        return None

    customs = _memory.get_all_custom_commands()
    for cmd_trigger, actions in customs.items():
        if cmd_trigger in trigger.lower() or fuzz.ratio(trigger.lower(), cmd_trigger) >= 80:
            results = []
            for action_text in actions:
                result = _execute_single(action_text)
                if result:
                    results.append(result)
            if results:
                return f"Executing routine \"{cmd_trigger}\", sir.\n" + "\n".join(results)

    return None


def handle_clear() -> str:
    """Clear conversation context."""
    if _brain:
        _brain.clear_context()
    if _memory:
        _memory.clear_conversation()
    return "Conversation context cleared, sir. Starting fresh."


def handle_stop() -> str:
    """Stop the assistant from speaking."""
    tts.stop()
    return ""  # Return empty so nothing new is spoken


def handle_vision(text: str, source: str) -> str:
    """Capture image and analyze it."""
    if not _brain:
        return "My AI systems are not initialized, sir."
    
    if source == "screen":
        image_data = vision.capture_screen()
        prompt = "Analyze my current screen and tell me what you see. Be concise but descriptive."
    else:
        image_data = vision.capture_webcam()
        prompt = "Look through the camera and tell me what you see or who is there. Be concise."

    if not image_data:
        return "I'm having trouble seeing right now, sir. Is the camera or screen accessible?"

    return _brain.think(prompt, image_data=image_data)


def handle_mouse(text: str, cmd_type: str) -> str:
    """Handle mouse control commands."""
    try:
        if cmd_type == "mouse_move":
            # Extract coordinates
            nums = re.findall(r"\d+", text)
            if len(nums) >= 2:
                x, y = int(nums[0]), int(nums[1])
                pyautogui.moveTo(x, y, duration=0.5)
                return f"Moving cursor to {x}, {y}, sir."
            return "Please specify the X and Y coordinates, sir."

        if cmd_type == "mouse_click":
            if "right" in text:
                pyautogui.rightClick()
                return "Right clicking, sir."
            if "double" in text:
                pyautogui.doubleClick()
                return "Double clicking, sir."
            pyautogui.click()
            return "Clicking, sir."

        if cmd_type == "mouse_scroll":
            amount = 500 if "up" in text else -500
            pyautogui.scroll(amount)
            return f"Scrolling {'up' if amount > 0 else 'down'}, sir."

    except Exception as e:
        logger.error(f"Mouse command failed: {e}")
        return "I encountered an error while attempting to move the mouse, sir."
    return ""


# ── AI Handler ───────────────────────────────────────────────────

def handle_ai(text: str) -> str:
    """Send to Ollama for an AI response."""
    if not _brain:
        return "My AI systems are not initialized, sir."

    if not _brain.is_available:
        return (
            "My AI core is currently offline, sir. "
            "Please start Ollama with: ollama serve"
        )

    # Provide memory context to the LLM
    memory_context = ""
    if _memory:
        notes = _memory.get_notes()
        if notes:
            notes_text = "; ".join(n["text"] for n in notes[-5:])
            memory_context = f"User's recent notes: {notes_text}"

    response = _brain.think(text, memory_context)

    # Save to conversation memory
    if _memory:
        _memory.add_conversation("user", text)
        _memory.add_conversation("assistant", response)

    return response


# ── Single Command Executor ──────────────────────────────────────

def _execute_single(text: str) -> str:
    """Execute a single action string (used by custom commands)."""
    cmd_type = _classify(text)

    if cmd_type in ("open", "close"):
        result = _find_app(text)
        if result:
            app_name, app_info, _ = result
            if cmd_type == "open":
                return handle_open(app_name, app_info)
            else:
                return handle_close(app_name, app_info)
    return ""


# ── Main Execute ─────────────────────────────────────────────────

def execute_command(text: str) -> str:
    """Parse and execute a command. Returns response string."""
    if not text or not text.strip():
        return ""

    # Log habit
    if _memory:
        cmd_type = _classify(text)
        app_result = _find_app(text)
        app_name = app_result[0] if app_result else ""
        _memory.log_habit(text, cmd_type, app_name)

    # 1. Check custom commands first
    custom_result = handle_custom_command(text)
    if custom_result:
        return custom_result

    # 2. Classify and route
    cmd_type = _classify(text)

    # Utility commands
    if cmd_type == "time":
        return jarvis.get_time_response()
    if cmd_type == "date":
        return jarvis.get_date_response()
    if cmd_type == "status":
        return jarvis.get_system_status()

    # Memory commands
    if cmd_type == "remember":
        return handle_remember(text)
    if cmd_type == "recall":
        return handle_recall()
    if cmd_type == "forget":
        return handle_forget(text)
    if cmd_type == "habits":
        return handle_habits()
    if cmd_type == "learn":
        return handle_learn(text)
    if cmd_type == "clear":
        return handle_clear()
    if cmd_type == "stop":
        return handle_stop()
    if cmd_type == "vision_screen":
        return handle_vision(text, "screen")
    if cmd_type == "vision_webcam":
        return handle_vision(text, "webcam")
    if cmd_type in ("mouse_move", "mouse_click", "mouse_scroll"):
        return handle_mouse(text, cmd_type)

    # App commands
    if cmd_type in ("open", "close"):
        result = _find_app(text)
        if result:
            app_name, app_info, confidence = result
            if cmd_type == "open":
                return handle_open(app_name, app_info)
            else:
                return handle_close(app_name, app_info)
        else:
            return jarvis.no_app(text)

    # 3. FALLBACK → AI
    return handle_ai(text)


def execute_from_hypotheses(hypotheses: list[str]) -> str:
    """Try multiple speech hypotheses until one matches a built-in command."""
    for text in hypotheses:
        cmd_type = _classify(text)

        # If it's a definite built-in, execute immediately
        if cmd_type != "ai":
            logger.info(f"Matched hypothesis: '{text}' → {cmd_type}")
            return execute_command(text)

    # No built-in matched — use the best transcript for AI
    top = hypotheses[0] if hypotheses else ""
    return execute_command(top)

"""
J.A.R.V.I.S. — Personality & Response Engine

Generates JARVIS-style responses with the iconic British-butler tone.
All responses flow through here so the personality stays consistent.
"""

import datetime
import psutil
import logging
from config import ASSISTANT_NAME

logger = logging.getLogger(__name__)

# ── JARVIS Greeting ──────────────────────────────────────────────

def get_greeting() -> str:
    """Time-aware JARVIS greeting."""
    hour = datetime.datetime.now().hour
    if hour < 6:
        period = "It's quite late, sir."
    elif hour < 12:
        period = "Good morning, sir."
    elif hour < 17:
        period = "Good afternoon, sir."
    elif hour < 21:
        period = "Good evening, sir."
    else:
        period = "Good evening, sir. Burning the midnight oil, I see."

    return f"{period} All systems are operational. How may I assist you?"


# ── Response Wrappers ────────────────────────────────────────────

def app_opened(app_name: str) -> str:
    responses = {
        "telegram":   f"Opening Telegram for you, sir.",
        "chrome":     f"Launching your web browser now, sir.",
        "notepad":    f"Notepad is ready for your notes, sir.",
        "calculator": f"Calculator is at your service, sir.",
        "explorer":   f"Opening your file system, sir.",
    }
    return responses.get(app_name, f"I've launched {app_name} for you, sir.")


def app_closed(app_name: str) -> str:
    responses = {
        "telegram":   f"Telegram has been shut down, sir.",
        "chrome":     f"Browser sessions terminated, sir.",
        "notepad":    f"Notepad closed, sir.",
        "calculator": f"Calculator dismissed, sir.",
        "explorer":   f"File explorer closed, sir.",
    }
    return responses.get(app_name, f"{app_name.title()} has been terminated, sir.")


def app_not_running(app_name: str) -> str:
    return f"It appears {app_name} is not currently running, sir."


def app_not_found(app_name: str, path: str) -> str:
    return f"I'm unable to locate {app_name} on your system, sir."


def app_failed(app_name: str) -> str:
    return f"I encountered an issue while trying to handle {app_name}, sir. My apologies."


def no_action(text: str) -> str:
    return f"I heard you say \"{text}\", but I'm not sure what action to take, sir."


def no_app(text: str) -> str:
    return f"I couldn't identify which application you're referring to, sir."


def unknown_action(action: str) -> str:
    return f"I'm not familiar with the action \"{action}\" yet, sir."


# ── Utility Responses ────────────────────────────────────────────

def get_time_response() -> str:
    now = datetime.datetime.now()
    return f"The current time is {now.strftime('%I:%M %p')}, sir."


def get_date_response() -> str:
    now = datetime.datetime.now()
    return f"Today is {now.strftime('%A, %B %d, %Y')}, sir."


def get_system_status() -> str:
    """Report system vitals like a proper AI assistant."""
    try:
        cpu = psutil.cpu_percent(interval=0.5)
        ram = psutil.virtual_memory()
        ram_used = ram.used / (1024 ** 3)
        ram_total = ram.total / (1024 ** 3)
        battery = psutil.sensors_battery()

        report = f"CPU usage is at {cpu}%. "
        report += f"Memory: {ram_used:.1f} of {ram_total:.1f} GB in use. "

        if battery:
            report += f"Battery is at {battery.percent}%"
            if battery.power_plugged:
                report += " and charging."
            else:
                report += "."
        else:
            report += "No battery detected — running on mains power."

        return f"System status report: {report}"
    except Exception as e:
        logger.error(f"System status error: {e}")
        return "I'm having trouble accessing system diagnostics, sir."


def get_intro() -> str:
    """Startup line using the current assistant name."""
    if ASSISTANT_NAME == "J.A.R.V.I.S.":
        return (
            "J.A.R.V.I.S. online. "
            "Just A Rather Very Intelligent System, at your service."
        )
    return f"{ASSISTANT_NAME} online and at your service, sir."

# 🤖 AI-Assistant (J.A.R.V.I.S.)

A modular, multi-modal personal AI assistant designed to handle voice commands, vision analysis, and complex task automation. Inspired by advanced personal agents, this project focuses on a distinct personality and extensible core.

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python&logoColor=white)
![Status](https://img.shields.io/badge/Status-Active-brightgreen)

---

## 🌟 Key Features

### 🎙️ Speech & Voice
- **Listener:** Real-time speech recognition using Vosk.
- **TTS:** High-quality text-to-speech output.
- **Natural Interaction:** Supports conversational flows and wake-word detection.

### 🧠 Advanced Brain & Memory
- **Logical Processing:** Centralized "brain" module for reasoning and command execution.
- **Persistent Memory:** Long-term memory storage to remember user preferences and past interactions.
- **Personality System:** Defined identity through `SOUL.md`, `IDENTITY.md`, and `AGENTS.md`.

### 👁️ Vision System
- **Screen Analysis:** Capability to "see" and understand what's on your screen.
- **Image Recognition:** Integration for visual tasks and webcam interaction.

### 🛠️ Extensible Tools
- **Modular Commands:** Easily add new capabilities via the `commands.py` system.
- **Automation:** Control system functions, mouse, and keyboard.

---

## 📂 Project Structure

```
Assistant/
├── jarvis.py        # Main entry point and assistant core
├── brain.py         # Reasoning and logic processing
├── ui.py            # Graphical User Interface
├── listener.py      # Speech-to-text management
├── tts.py           # Text-to-speech engine
├── vision.py        # Computer vision capabilities
├── memory.py        # Database and persistent storage
├── commands.py      # Action and command definitions
├── config.py        # Global settings and API keys
└── metadata/        # Personality and identity definitions (SOUL, IDENTITY, etc.)
```

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.11+
- [Ollama](https://ollama.ai/) (for local LLM capabilities)
- Vosk Models (for offline speech recognition)

### 2. Installation
```bash
pip install -r requirements.txt
```

### 3. Usage
```bash
python main.py
```

---

## 🛠️ Configuration
Edit `config.py` to customize:
- Assistant name (default: JARVIS)
- Model selection
- Voice and language settings
- Hotkeys and triggers

---

## 📄 Documentation
Detailed information about the assistant's internal systems:
- [IDENTITY.md](./IDENTITY.md) - Personality traits and behavioral constraints.
- [SOUL.md](./SOUL.md) - Core philosophical and ethical guidelines.
- [TOOLS.md](./TOOLS.md) - Available system tools and integration guides.

---

## 📜 License
MIT License.

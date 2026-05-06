"""
Brain — Ollama LLM client + intelligence layer for JARVIS.

Connects to local Ollama server for AI conversation.
Maintains conversation context and JARVIS personality.
Gracefully falls back when Ollama is not running.
"""

import logging
import threading
import os

# Force local connection if OLLAMA_HOST is set to 0.0.0.0 (which breaks Python client)
if os.environ.get("OLLAMA_HOST") == "0.0.0.0:11434":
    os.environ["OLLAMA_HOST"] = "127.0.0.1:11434"

import ollama
from config import VISION_MODEL, ASSISTANT_NAME

logger = logging.getLogger(__name__)

# Assistant system prompt
SYSTEM_PROMPT = f"""You are {ASSISTANT_NAME}, a highly intelligent AI assistant inspired by Tony Stark's AI from Iron Man.

Your personality:
- Speak in a polished, British-butler tone — formal but warm
- Address the user as "sir" naturally (not every sentence)
- Be concise — you're an efficient assistant, not a lecturer
- Show wit and dry humor when appropriate
- Be confident and knowledgeable
- When you don't know something, admit it gracefully

Keep responses SHORT — ideally 1-3 sentences. You are being spoken to via voice, and your response will be read aloud via text-to-speech. Long responses are exhausting to listen to.

You are running locally on the user's machine via Ollama. You are fully offline and private."""


class Brain:
    """Ollama-powered AI brain for JARVIS."""

    def __init__(self, model: str = "qwen2.5-coder:7b"):
        self.model = model
        self._available = False
        self._checking = False
        self._conversation: list[dict] = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]
        self._lock = threading.Lock()
        # Check availability in background
        self._check_availability()

    def _check_availability(self):
        """Check if Ollama is running and model is available."""
        def _check():
            try:
                models = ollama.list()
                model_names = [m.model for m in models.models] if models.models else []
                if any(self.model in name for name in model_names):
                    self._available = True
                    logger.info(f"Ollama ready: {self.model}")
                else:
                    logger.warning(
                        f"Model {self.model} not found. "
                        f"Available: {model_names}. "
                        f"Run: ollama pull {self.model}"
                    )
                    self._available = False
            except Exception as e:
                logger.warning(f"Ollama not available: {e}")
                self._available = False
            self._checking = False

        self._checking = True
        thread = threading.Thread(target=_check, daemon=True)
        thread.start()

    @property
    def is_available(self) -> bool:
        return self._available

    def think(self, user_message: str, memory_context: str = "", image_data: str = None) -> str:
        """
        Send a message to the LLM and get a response.

        Args:
            user_message: What the user said.
            memory_context: Optional context from memory (notes, habits).
            image_data: Optional base64 encoded image for vision models.

        Returns:
            The AI response string.
        """
        if not self._available:
            return self._fallback_response()

        with self._lock:
            try:
                # Use vision model if an image is provided
                model = VISION_MODEL if image_data else self.model
                # Add memory context if provided
                if memory_context:
                    self._conversation.append({
                        "role": "system",
                        "content": f"Context from user's memory: {memory_context}",
                    })

                # Current message
                msg = {"role": "user", "content": user_message}
                if image_data:
                    msg["images"] = [image_data]

                # Call Ollama
                response = ollama.chat(
                    model=model,
                    messages=self._conversation + [msg],
                )

                reply = response["message"]["content"].strip()

                # Save exchange to context (without the bulky image)
                self._conversation.append({"role": "user", "content": user_message})
                self._conversation.append({"role": "assistant", "content": reply})

                # Trim conversation to avoid context overflow
                # Keep system prompt + last 20 exchanges
                if len(self._conversation) > 42:  # 1 system + 20 pairs + buffer
                    self._conversation = (
                        [self._conversation[0]]  # system prompt
                        + self._conversation[-40:]  # last 20 exchanges
                    )

                return reply

            except Exception as e:
                logger.error(f"Ollama error: {e}")
                # Remove the failed messages
                if self._conversation and self._conversation[-1]["role"] == "user":
                    self._conversation.pop()
                return self._fallback_response()

    def clear_context(self):
        """Reset conversation context."""
        self._conversation = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]

    def _fallback_response(self) -> str:
        return (
            "My AI core is currently offline, sir. "
            "Please ensure Ollama is running with: ollama serve"
        )

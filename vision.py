"""
Vision System — Screen and Webcam capture for JARVIS.

Allows the assistant to see what's on the screen or in front of the camera.
Images are encoded to base64 for processing by local VLMs (like LLaVA).
"""

import pyautogui
import cv2
import base64
import io
import logging
from PIL import Image

logger = logging.getLogger(__name__)

def capture_screen() -> str:
    """Capture the entire screen and return as base64 JPEG string."""
    try:
        # Take screenshot
        screenshot = pyautogui.screenshot()
        
        # Convert to bytes
        buffered = io.BytesIO()
        screenshot.save(buffered, format="JPEG", quality=70)
        
        logger.info("Screen captured successfully.")
        return base64.b64encode(buffered.getvalue()).decode('utf-8')
    except Exception as e:
        logger.error(f"Failed to capture screen: {e}")
        return ""

def capture_webcam() -> str:
    """Capture a single frame from the default webcam."""
    # Open default camera
    cam = cv2.VideoCapture(0)
    if not cam.isOpened():
        logger.error("Could not open webcam.")
        return ""

    try:
        # Allow camera to warm up/auto-adjust
        # We take a few frames and keep the last one
        for _ in range(5):
            ret, frame = cam.read()
            
        if not ret:
            logger.error("Failed to read from webcam.")
            return ""

        # Convert BGR to RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame_rgb)
        
        # Convert to bytes
        buffered = io.BytesIO()
        img.save(buffered, format="JPEG", quality=70)
        
        logger.info("Webcam frame captured successfully.")
        return base64.b64encode(buffered.getvalue()).decode('utf-8')
    except Exception as e:
        logger.error(f"Webcam error: {e}")
        return ""
    finally:
        cam.release()

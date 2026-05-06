"""
J.A.R.V.I.S. HUD — Futuristic holographic-style interface.

Dark background, glowing cyan/blue accents, animated arc reactor,
and a minimalist data display — inspired by Tony Stark's lab.
"""

import tkinter as tk
from tkinter import font as tkfont
import math
import logging
import tts
from config import ASSISTANT_NAME

logger = logging.getLogger(__name__)

# ── JARVIS Color Palette ─────────────────────────────────────────
BG          = "#0a0e17"      # Deep space black
BG_PANEL    = "#0d1320"      # Panel background
CYAN        = "#00d4ff"      # Primary glow (arc reactor blue)
CYAN_DIM    = "#0a4a5e"      # Dimmed cyan
CYAN_DARK   = "#062a35"      # Very dim cyan (borders)
GOLD        = "#f0c040"      # Accent (like JARVIS status text)
WHITE       = "#e8f0f8"      # Text white
WHITE_DIM   = "#6a7a8a"      # Secondary text
RED         = "#ff3040"      # Alert / stopped
GREEN       = "#00ff88"      # Active / success
FONT_FAM    = "Consolas"     # Monospace for that HUD feel
FONT_FAM2   = "Segoe UI"    # For labels


class JarvisUI:
    """JARVIS-style floating HUD window."""

    def __init__(self, on_toggle: callable, on_command: callable):
        self._on_toggle = on_toggle
        self._on_command = on_command
        self._active = False
        self._pulse_angle = 0
        self._ring_angles = [0, 120, 240]  # Three rotating rings

        # ── Window ───────────────────────────────────────────────
        self.root = tk.Tk()
        self.root.title(ASSISTANT_NAME)
        self.root.geometry("420x650")
        self.root.resizable(True, True)
        self.root.configure(bg=BG)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.96)
        self.root.bind("<space>", lambda e: tts.stop())
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        try:
            self.root.iconbitmap(default="")
        except Exception:
            pass

        # ── Fonts ────────────────────────────────────────────────
        self._font_title   = tkfont.Font(family=FONT_FAM, size=14, weight="bold")
        self._font_sub     = tkfont.Font(family=FONT_FAM, size=8)
        self._font_status  = tkfont.Font(family=FONT_FAM2, size=9)
        self._font_log     = tkfont.Font(family=FONT_FAM2, size=10)
        self._font_btn     = tkfont.Font(family=FONT_FAM, size=10, weight="bold")
        self._font_label   = tkfont.Font(family=FONT_FAM, size=7)

        # ── Header ───────────────────────────────────────────────
        header = tk.Frame(self.root, bg=BG, pady=6, padx=16)
        header.pack(fill="x")

        # Title with glow effect
        tk.Label(
            header, text=ASSISTANT_NAME, fg=CYAN, bg=BG,
            font=self._font_title,
        ).pack(side="left")

        tk.Label(
            header, text="v2.0  //  ONLINE", fg=CYAN_DIM, bg=BG,
            font=self._font_sub,
        ).pack(side="left", padx=(8, 0), pady=(4, 0))

        # ── Arc Reactor Canvas ───────────────────────────────────
        self._canvas = tk.Canvas(
            self.root, width=420, height=220,
            bg=BG, highlightthickness=0,
        )
        self._canvas.pack()

        # ── Separator ────────────────────────────────────────────
        sep = tk.Frame(self.root, bg=CYAN_DARK, height=1)
        sep.pack(fill="x", padx=16, pady=(0, 4))

        # ── Status Section ───────────────────────────────────────
        status_frame = tk.Frame(self.root, bg=BG, padx=20, pady=4)
        status_frame.pack(fill="x")

        tk.Label(
            status_frame, text="STATUS", fg=CYAN_DIM, bg=BG,
            font=self._font_label, anchor="w",
        ).pack(fill="x")

        self._status_var = tk.StringVar(value="Systems on standby. Awaiting activation.")
        self._status_label = tk.Label(
            status_frame, textvariable=self._status_var,
            fg=WHITE_DIM, bg=BG, font=self._font_status, anchor="w",
        )
        self._status_label.pack(fill="x")

        # ── Bottom Bar ───────────────────────────────────────────
        bottom = tk.Frame(self.root, bg=BG, padx=16, pady=10)
        bottom.pack(side="bottom", fill="x")

        self._btn = tk.Button(
            bottom, text="▶  ACTIVATE", fg=BG, bg=CYAN,
            font=self._font_btn, bd=0, padx=20, pady=6,
            activebackground="#00b8dd", activeforeground=BG,
            cursor="hand2", command=self._toggle,
        )
        self._btn.pack(side="right")

        self._power_dot = tk.Label(
            bottom, text="●", fg=RED, bg=BG,
            font=tkfont.Font(family=FONT_FAM, size=12),
        )
        self._power_dot.pack(side="left")

        self._power_label = tk.Label(
            bottom, text="  OFFLINE", fg=RED, bg=BG,
            font=self._font_label,
        )
        self._power_label.pack(side="left")

        # ── Text Input ───────────────────────────────────────────
        input_outer = tk.Frame(self.root, bg=CYAN_DARK, padx=1, pady=1)
        input_outer.pack(fill="x", padx=16, pady=(4, 8))

        input_frame = tk.Frame(input_outer, bg=BG_PANEL)
        input_frame.pack(fill="x")

        self._input_entry = tk.Entry(
            input_frame, fg=WHITE, bg=BG, font=self._font_log,
            insertbackground=CYAN, bd=0, highlightthickness=0,
            relief="flat"
        )
        self._input_entry.pack(fill="x", side="left", expand=True, pady=8, padx=10)
        self._input_entry.bind("<Return>", self._handle_text_input)

        # ── Response Log ─────────────────────────────────────────
        log_outer = tk.Frame(self.root, bg=CYAN_DARK, padx=1, pady=1)
        log_outer.pack(fill="both", expand=True, padx=16, pady=(8, 4))

        log_frame = tk.Frame(log_outer, bg=BG_PANEL, padx=12, pady=10)
        log_frame.pack(fill="both", expand=True)

        tk.Label(
            log_frame, text="COMM LOG", fg=CYAN_DIM, bg=BG_PANEL,
            font=self._font_label, anchor="w",
        ).pack(fill="x")

        self._log_text = tk.Text(
            log_frame, fg=WHITE, bg=BG_PANEL, font=self._font_log,
            wrap="word", bd=0, highlightthickness=0, state="disabled",
            height=6  # Fixed initial height to prevent pushing other UI elements
        )
        self._log_text.pack(fill="both", expand=True)
        
        # Add initial text
        self._log_text.config(state="normal")
        self._log_text.insert("end", '"Activate me and say a command, sir."\n')
        self._log_text.config(state="disabled")

        # ── Start animation loop ─────────────────────────────────
        self._draw_reactor()
        self._animate()

    # ── Arc Reactor Drawing ──────────────────────────────────────

    def _draw_reactor(self):
        """Draw the arc reactor HUD element."""
        c = self._canvas
        c.delete("all")
        cx, cy = 210, 110  # Center
        active = self._active

        # ── Outer glow (subtle) ──────────────────────────────────
        if active:
            for i in range(3):
                r = 95 - i * 2
                alpha_hex = ["1a", "10", "08"][i]
                color = f"#00d4ff"  # tkinter doesn't support alpha, use rings
                c.create_oval(
                    cx - r, cy - r, cx + r, cy + r,
                    outline=CYAN_DARK, width=1, dash=(2, 4),
                )

        # ── Outer ring ───────────────────────────────────────────
        ring_color = CYAN if active else CYAN_DIM
        c.create_oval(cx - 85, cy - 85, cx + 85, cy + 85,
                      outline=ring_color, width=2)

        # ── Rotating segments ────────────────────────────────────
        for i, base_angle in enumerate(self._ring_angles):
            r = 75 - i * 12
            color = CYAN if active else CYAN_DARK
            arc_len = 40
            c.create_arc(
                cx - r, cy - r, cx + r, cy + r,
                start=base_angle, extent=arc_len,
                outline=color, width=2, style="arc",
            )
            c.create_arc(
                cx - r, cy - r, cx + r, cy + r,
                start=base_angle + 180, extent=arc_len,
                outline=color, width=2, style="arc",
            )

        # ── Inner ring ───────────────────────────────────────────
        inner_r = 35
        c.create_oval(
            cx - inner_r, cy - inner_r, cx + inner_r, cy + inner_r,
            outline=ring_color, width=2,
        )

        # ── Core glow ───────────────────────────────────────────
        core_r = 18
        if active:
            # Pulsing core
            pulse = 2 * math.sin(math.radians(self._pulse_angle))
            cr = core_r + pulse
            # Layered glow
            for layer in range(4, 0, -1):
                lr = cr + layer * 4
                c.create_oval(
                    cx - lr, cy - lr, cx + lr, cy + lr,
                    fill="", outline=CYAN_DARK, width=1,
                )
            c.create_oval(
                cx - cr, cy - cr, cx + cr, cy + cr,
                fill=CYAN, outline=CYAN, width=0,
            )
            # White hot center
            wr = cr * 0.5
            c.create_oval(
                cx - wr, cy - wr, cx + wr, cy + wr,
                fill=WHITE, outline=WHITE, width=0,
            )
        else:
            c.create_oval(
                cx - core_r, cy - core_r, cx + core_r, cy + core_r,
                fill=CYAN_DARK, outline=CYAN_DIM, width=1,
            )

        # ── Decorative data lines ────────────────────────────────
        data_color = CYAN_DIM if active else CYAN_DARK
        # Left data column
        for i in range(5):
            y = 20 + i * 14
            w = [60, 45, 70, 35, 55][i]
            c.create_line(10, y, 10 + w, y, fill=data_color, width=1)
            c.create_oval(6, y - 2, 10, y + 2, fill=data_color, outline="")

        # Right data column
        for i in range(5):
            y = 20 + i * 14
            w = [50, 65, 40, 55, 45][i]
            x_start = 410 - w
            c.create_line(x_start, y, 410, y, fill=data_color, width=1)
            c.create_oval(410, y - 2, 414, y + 2, fill=data_color, outline="")

        # ── Corner brackets ──────────────────────────────────────
        bk = CYAN_DIM if active else CYAN_DARK
        bk_len = 15
        # Top-left
        c.create_line(5, 5, 5 + bk_len, 5, fill=bk, width=1)
        c.create_line(5, 5, 5, 5 + bk_len, fill=bk, width=1)
        # Top-right
        c.create_line(415, 5, 415 - bk_len, 5, fill=bk, width=1)
        c.create_line(415, 5, 415, 5 + bk_len, fill=bk, width=1)
        # Bottom-left
        c.create_line(5, 215, 5 + bk_len, 215, fill=bk, width=1)
        c.create_line(5, 215, 5, 215 - bk_len, fill=bk, width=1)
        # Bottom-right
        c.create_line(415, 215, 415 - bk_len, 215, fill=bk, width=1)
        c.create_line(415, 215, 415, 215 - bk_len, fill=bk, width=1)

        # ── Bottom text ──────────────────────────────────────────
        status_text = "● ACTIVE  —  VOICE LINK ESTABLISHED" if active else "○ STANDBY"
        text_color = GREEN if active else WHITE_DIM
        c.create_text(
            cx, 200, text=status_text, fill=text_color,
            font=self._font_label, anchor="center",
        )

    def _animate(self):
        """Animation loop — rotates rings and pulses core."""
        if self._active:
            self._pulse_angle = (self._pulse_angle + 6) % 360
            self._ring_angles = [(a + 1.5) % 360 for a in self._ring_angles]
            # Counter-rotate middle ring
            self._ring_angles[1] = (self._ring_angles[1] - 3) % 360
        else:
            # Slow idle rotation
            self._ring_angles = [(a + 0.3) % 360 for a in self._ring_angles]

        self._draw_reactor()
        self.root.after(50, self._animate)  # ~20 FPS

    # ── Public API ───────────────────────────────────────────────

    def set_status(self, text: str):
        """Update status label."""
        self._status_label.config(text=text)

    def _handle_text_input(self, event=None):
        """Process command from text entry."""
        text = self._input_entry.get().strip()
        if text:
            self._input_entry.delete(0, "end")
            if self._on_command:
                self._on_command(text)

    def toggle_from_hotkey(self):
        """Toggle activation state from external hotkey."""
        self.root.after(0, self._toggle)

    def _on_close(self):
        """Cleanly exit the application."""
        if self._active:
            self._on_toggle(False)
        self.root.destroy()

    def set_log(self, msg: str):
        """Update comm log (thread-safe)."""
        def _update():
            self._log_text.config(state="normal")
            self._log_text.insert("end", "\n" + msg + "\n")
            self._log_text.see("end")
            self._log_text.config(state="disabled")
        self.root.after(0, _update)

    def set_active(self, active: bool):
        """Switch between active/standby visual state."""
        self._active = active
        if active:
            self.root.after(0, lambda: (
                self._power_dot.config(fg=GREEN),
                self._power_label.config(text="  ONLINE", fg=GREEN),
                self._btn.config(text="■  DEACTIVATE", bg=RED),
            ))
        else:
            self.root.after(0, lambda: (
                self._power_dot.config(fg=RED),
                self._power_label.config(text="  OFFLINE", fg=RED),
                self._btn.config(text="▶  ACTIVATE", bg=CYAN),
            ))

    def run(self):
        """Start the main loop."""
        self.root.mainloop()

    # ── Internal ─────────────────────────────────────────────────

    def _toggle(self):
        new_state = not self._active
        self._on_toggle(new_state)

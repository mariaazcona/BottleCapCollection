# ui_theme.py
# Theme helpers for the "Dark Mode Pro" UI
# UI theme definitions (colors, fonts, spacing) used by the application.

import tkinter as tk

# Palette
BG = "#1e1e1e"
PANEL = "#252525"
CARD = "#2a2a2a"
ACCENT = "#0d7377"
ACCENT_HOVER = "#14a098"
TEXT = "#eeeeee"
MUTED = "#bdbdbd"
ERROR = "#e74c3c"

FONT = ("Segoe UI", 10)
FONT_BOLD = ("Segoe UI", 11, "bold")
FONT_BIG = ("Segoe UI", 12, "bold")

def style_root(root):
    root.configure(bg=BG)
    try:
        root.option_add("*Font", FONT)
    except:
        pass

# Styled button (flat) with hover
class AccentButton(tk.Button):
    def __init__(self, master, text="", command=None, width=None, **kwargs):
        super().__init__(master,
                         text=text,
                         command=command,
                         bg=ACCENT,
                         fg=TEXT,
                         activebackground=ACCENT_HOVER,
                         bd=0,
                         relief="flat",
                         highlightthickness=0,
                         **kwargs)
        if width:
            self.configure(width=width)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    def _on_enter(self, e):
        self.configure(bg=ACCENT_HOVER)

    def _on_leave(self, e):
        self.configure(bg=ACCENT)

# Ghost button (outline)
class GhostButton(tk.Button):
    def __init__(self, master, text="", command=None, **kwargs):
        super().__init__(master,
                         text=text,
                         command=command,
                         bg=PANEL,
                         fg=TEXT,
                         bd=1,
                         relief="flat",
                         highlightthickness=0,
                         **kwargs)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    def _on_enter(self, e):
        self.configure(bg="#303030")

    def _on_leave(self, e):
        self.configure(bg=PANEL)

# Card frame (for results)
class Card(tk.Frame):
    def __init__(self, master, width=600, height=100, **kwargs):
        super().__init__(master, bg=CARD, bd=0, highlightthickness=0, **kwargs)
        self.default_bg = CARD
        self.hover_bg = "#313131"
        self.configure(padx=8, pady=8)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    def _on_enter(self, e):
        self.configure(bg=self.hover_bg)

    def _on_leave(self, e):
        self.configure(bg=self.default_bg)

# Small label helpers
def Title(master, text):
    lbl = tk.Label(master, text=text, bg=BG, fg=TEXT, font=FONT_BIG)
    return lbl

def SubTitle(master, text):
    lbl = tk.Label(master, text=text, bg=BG, fg=MUTED, font=FONT_BOLD)
    return lbl

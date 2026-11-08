"""Design tokens and font cache for the canvas-based interface."""

from __future__ import annotations

import tkinter as tk
import tkinter.font as tkfont

# Palette follows the FileExplorer reference: graphite surfaces, thin borders,
# a single blue accent, yellow warnings and a muted red for failures.
BG = "#1e1f22"
SURFACE = "#25272a"
SURFACE_ALT = "#2b2d30"
FIELD = "#1e1f22"
INK = "#2f6bff"  # primary accent, kept as INK for the drawing primitives
TEXT = "#d7dae0"
TEXT_BRIGHT = "#f0f1f2"
MUTED = "#8b9098"
FAINT = "#666a70"
LINE = "#3a3d41"
LINE_STRONG = "#45484d"
SELECT = "#354968"
GREEN = "#6ea4ff"
PINK = "#f2bd45"
RED = "#e65b63"
WHITE = "#ffffff"
ACCENT_HOVER = "#3c76ff"
ACCENT_BORDER = "#4279ff"
ACCENT_LIGHT = "#6ea4ff"
FONT_FAMILY = "Microsoft YaHei UI"

_fonts: dict[tuple[int, str], tkfont.Font] = {}


def ui_font(size: int, weight: str = "normal") -> tkfont.Font:
    key = (size, weight)
    font = _fonts.get(key)
    if font is None:
        font = tkfont.Font(root=tk._default_root, family=FONT_FAMILY,
                           size=size, weight=weight)
        _fonts[key] = font
    return font


def parent_background(master, fallback: str = BG) -> str:
    """Return the parent's fill colour for transparent-looking canvases."""
    try:
        return master.cget("background")
    except (tk.TclError, AttributeError):
        return fallback


__all__ = [
    "ACCENT_BORDER",
    "ACCENT_HOVER",
    "ACCENT_LIGHT",
    "BG",
    "FAINT",
    "FIELD",
    "FONT_FAMILY",
    "GREEN",
    "INK",
    "LINE",
    "LINE_STRONG",
    "MUTED",
    "PINK",
    "RED",
    "SELECT",
    "SURFACE",
    "SURFACE_ALT",
    "TEXT",
    "TEXT_BRIGHT",
    "WHITE",
    "parent_background",
    "ui_font",
]

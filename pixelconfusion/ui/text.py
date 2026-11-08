"""Text and label helpers for the desktop views."""

from __future__ import annotations

import tkinter as tk

from pixelconfusion.ui.theme import SURFACE, TEXT, ui_font


def make_label(parent, text, size=9, weight="normal", fg=TEXT, bg=SURFACE,
               **kwargs) -> tk.Label:
    return tk.Label(parent, text=text, font=ui_font(size, weight), fg=fg, bg=bg,
                    bd=0, highlightthickness=0, **kwargs)


def ellipsize(text, max_width, size=9, weight="normal") -> str:
    font = ui_font(size, weight)
    if font.measure(text) <= max_width:
        return text
    clipped = text
    while clipped and font.measure(clipped + "…") > max_width:
        clipped = clipped[:-1]
    return clipped + "…"


def format_dimensions(width, height) -> str:
    return f"{width} × {height}"


__all__ = ["ellipsize", "format_dimensions", "make_label"]

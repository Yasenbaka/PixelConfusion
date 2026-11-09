"""A small canvas switch for boolean options."""

from __future__ import annotations

import tkinter as tk

from pixelconfusion.ui.drawing import draw_round
from pixelconfusion.ui.theme import (
    INK,
    LINE_STRONG,
    SURFACE_ALT,
    TEXT,
    TEXT_BRIGHT,
    WHITE,
    parent_background,
    ui_font,
)


class ToggleSwitch(tk.Canvas):
    """Label on the left, track and knob on the right."""

    TRACK_WIDTH = 38
    TRACK_HEIGHT = 20

    def __init__(self, master, text, value=False, on_change=None, height=30,
                 outer_bg=None):
        super().__init__(master, bg=outer_bg or parent_background(master),
                         highlightthickness=0, bd=0, height=height, takefocus=0)
        self._text = text
        self._on_change = on_change
        self._enabled = True
        self._hover = False
        self.value = bool(value)
        self.bind("<Configure>", lambda _event: self._draw())
        self.bind("<Enter>", self._enter)
        self.bind("<Leave>", self._leave)
        self.bind("<ButtonRelease-1>", self._click)
        self._draw()

    def _draw(self):
        self.delete("all")
        width = max(self.winfo_width(), 2)
        height = max(self.winfo_height(), 2)
        text_color = TEXT_BRIGHT if self._hover and self._enabled else TEXT
        if not self._enabled:
            text_color = "#686c72"
        self.create_text(1, height / 2, text=self._text, fill=text_color,
                         font=ui_font(9), anchor="w")
        track_w = self.TRACK_WIDTH
        track_h = self.TRACK_HEIGHT
        x2 = width - 2
        x1 = x2 - track_w
        y1 = (height - track_h) / 2
        y2 = y1 + track_h
        if self._enabled:
            fill = INK if self.value else SURFACE_ALT
            outline = "#6ea4ff" if self.value else LINE_STRONG
        else:
            fill = "#35373b"
            outline = LINE_STRONG
        draw_round(self, x1, y1, x2, y2, track_h / 2, fill, outline)
        knob_x = x2 - track_h / 2 if self.value else x1 + track_h / 2
        knob_r = track_h / 2 - 4
        knob_color = WHITE if self._enabled else "#686c72"
        self.create_oval(knob_x - knob_r, height / 2 - knob_r,
                         knob_x + knob_r, height / 2 + knob_r,
                         fill=knob_color, outline="")

    def _enter(self, _event):
        self._hover = True
        if self._enabled:
            self.configure(cursor="hand2")
        self._draw()

    def _leave(self, _event):
        self._hover = False
        self.configure(cursor="")
        self._draw()

    def _click(self, event):
        if not self._enabled:
            return
        if 0 <= event.x <= self.winfo_width() and 0 <= event.y <= self.winfo_height():
            self.set_value(not self.value, notify=True)

    def set_value(self, value, notify=False):
        value = bool(value)
        if value == self.value:
            return
        self.value = value
        self._draw()
        if notify and self._on_change:
            self._on_change(value)

    def set_enabled(self, enabled):
        self._enabled = bool(enabled)
        self.configure(cursor="hand2" if enabled and self._hover else "")
        self._draw()


__all__ = ["ToggleSwitch"]

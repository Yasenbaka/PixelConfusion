"""Small status, hint and progress widgets."""

from __future__ import annotations

import tkinter as tk

from pixelconfusion.ui.drawing import draw_round
from pixelconfusion.ui.images import icon_photo
from pixelconfusion.ui.theme import (
    ACCENT_LIGHT,
    FAINT,
    FIELD,
    INK,
    LINE,
    LINE_STRONG,
    MUTED,
    SURFACE_ALT,
    TEXT_BRIGHT,
    parent_background,
    ui_font,
)


class Pill(tk.Canvas):
    def __init__(self, master, text, bg=SURFACE_ALT, fg=MUTED, dot=None, icon=None,
                 border=LINE_STRONG, height=23, pad=9, outer_bg=None):
        self._text = text
        self._bg = bg
        self._fg = fg
        self._dot = dot
        self._icon = icon
        self._border = border
        self._height = height
        self._pad = pad
        self._font = ui_font(8)
        width = self._natural_width()
        super().__init__(master, bg=outer_bg or parent_background(master),
                         highlightthickness=0, bd=0, width=width, height=height,
                         takefocus=0)
        self.bind("<Configure>", lambda _event: self._draw())
        self._draw()

    def _natural_width(self):
        lead = (10 if self._dot else 0) + (17 if self._icon else 0)
        return self._pad * 2 + lead + self._font.measure(self._text)

    def _draw(self):
        self.delete("all")
        width = max(self.winfo_width(), 2)
        height = self._height
        draw_round(self, 1.5, 1.5, width - 1.5, height - 1.5, 4,
                   self._bg, self._border or self._bg)
        x = self._pad
        if self._dot:
            self.create_oval(x, height / 2 - 2.5, x + 5, height / 2 + 2.5,
                             fill=self._dot, outline=self._dot)
            x += 10
        if self._icon:
            self.create_image(x, height / 2,
                              image=icon_photo(self._icon, self._fg, 12), anchor="w")
            x += 17
        self.create_text(x, height / 2, text=self._text, fill=self._fg,
                         font=self._font, anchor="w")

    def update_pill(self, text=None, bg=None, fg=None, dot=None, icon=None,
                    border=None):
        if text is not None:
            self._text = text
        if bg is not None:
            self._bg = bg
        if fg is not None:
            self._fg = fg
        if dot is not None:
            self._dot = dot
        if icon is not None:
            self._icon = icon
        if border is not None:
            self._border = border
        self.configure(width=self._natural_width())
        self._draw()


class HintBox(tk.Canvas):
    def __init__(self, master, text="", height=46, outer_bg=None):
        super().__init__(master, bg=outer_bg or parent_background(master),
                         highlightthickness=0, bd=0, height=height, takefocus=0)
        self._text = text
        self.bind("<Configure>", lambda _event: self._draw())
        self._draw()

    def _draw(self):
        self.delete("all")
        width = max(self.winfo_width(), 2)
        height = max(self.winfo_height(), 2)
        draw_round(self, 2, 2, width - 2, height - 2, 6, FIELD, LINE)
        self.create_image(14, 15, image=icon_photo("info", MUTED, 13), anchor="w")
        self.create_text(33, 9, text=self._text, fill=MUTED, font=ui_font(8),
                         width=max(20, width - 44), anchor="nw")

    def set_text(self, text):
        self._text = text
        self._draw()


class Steps(tk.Canvas):
    LABELS = (("选图", 1), ("参数", 2), ("处理", 3), ("保存", 4))

    def __init__(self, master, active=1, outer_bg=None):
        super().__init__(master, bg=outer_bg or parent_background(master),
                         highlightthickness=0, bd=0, height=22, width=1,
                         takefocus=0)
        self.active = active
        self.bind("<Configure>", lambda _event: self._draw())
        self._draw()

    def _draw(self):
        self.delete("all")
        x = 0
        y = 11
        for index, (label, number) in enumerate(self.LABELS):
            done = number < self.active
            active = number == self.active
            if active:
                dot, label_color, weight = INK, TEXT_BRIGHT, "bold"
            elif done:
                dot, label_color, weight = ACCENT_LIGHT, MUTED, "normal"
            else:
                dot, label_color, weight = "#4a668f", FAINT, "normal"
            self.create_oval(x, y - 3, x + 6, y + 3, fill=dot, outline="")
            x += 12
            label_font = ui_font(9, weight)
            self.create_text(x, y, text=label, fill=label_color, font=label_font,
                             anchor="w")
            x += label_font.measure(label)
            if index < len(self.LABELS) - 1:
                self.create_line(x + 8, y, x + 14, y, fill=LINE_STRONG)
                x += 22
        self.configure(width=max(80, x))

    def set_active(self, active):
        self.active = active
        self._draw()


class ProgressBar(tk.Canvas):
    def __init__(self, master, width=72, height=3, outer_bg=None):
        super().__init__(master, bg=outer_bg or parent_background(master),
                         highlightthickness=0, bd=0, width=width, height=height,
                         takefocus=0)
        self._value = 0.0
        self.bind("<Configure>", lambda _event: self._draw())
        self._draw()

    def _draw(self):
        self.delete("all")
        width = max(self.winfo_width(), 2)
        self.create_line(0, 1.5, width, 1.5, fill=LINE, width=2)
        end = width * max(0.0, min(1.0, self._value))
        if end > 0:
            self.create_line(0, 1.5, end, 1.5, fill=INK, width=2)

    def set(self, value):
        self._value = value
        self._draw()


__all__ = ["HintBox", "Pill", "ProgressBar", "Steps"]

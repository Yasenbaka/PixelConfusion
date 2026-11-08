"""Surface containers for the flat card layout."""

from __future__ import annotations

import tkinter as tk

from pixelconfusion.ui.drawing import draw_round
from pixelconfusion.ui.theme import LINE, SURFACE, parent_background


class Card(tk.Canvas):
    def __init__(self, master, height=100, radius=8, bg=SURFACE, border=LINE,
                 outer_bg=None, inset=12):
        super().__init__(master, bg=outer_bg or parent_background(master),
                         highlightthickness=0, bd=0, height=height, width=1,
                         takefocus=0)
        self._radius = radius
        self._fill = bg
        self._border = border
        self._inset = inset
        self.content = tk.Frame(self, bg=bg)
        self._win = self.create_window(inset, inset, anchor="nw", window=self.content)
        self.bind("<Configure>", self._redraw)

    def _redraw(self, _event=None):
        width = max(self.winfo_width(), 4)
        height = max(self.winfo_height(), 4)
        self.delete("cardbg")
        draw_round(self, 2, 2, width - 2, height - 2, self._radius,
                   self._fill, self._border, tags="cardbg")
        self.tag_lower("cardbg")
        self.coords(self._win, self._inset, self._inset)
        self.itemconfigure(self._win, width=max(1, width - self._inset * 2),
                           height=max(1, height - self._inset * 2))
        self.tag_raise(self._win)


__all__ = ["Card"]

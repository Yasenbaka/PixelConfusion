"""Forward and reverse scramble actions below the sidebar."""

from __future__ import annotations

import tkinter as tk

from pixelconfusion.ui.theme import BG
from pixelconfusion.ui.widgets import PillButton


class ActionRow(tk.Frame):
    def __init__(self, master, *, on_scramble, on_restore):
        super().__init__(master, bg=BG)
        self.grid_columnconfigure(0, weight=1, uniform="action")
        self.grid_columnconfigure(1, weight=1, uniform="action")
        # Reverse is the blue button on the left, forward the rose button on the
        # right. Both are the same permutation, just opposite directions.
        self.restore_button = PillButton(self, "反向混淆", command=on_restore,
                                         icon="arrow-left", kind="primary", height=38)
        self.restore_button.grid(row=0, column=0, sticky="ew")
        self.scramble_button = PillButton(self, "正向混淆", command=on_scramble,
                                          icon="arrow-right", kind="rose", height=38)
        self.scramble_button.grid(row=0, column=1, sticky="ew", padx=(8, 0))

    def set_enabled(self, has_source: bool, busy: bool) -> None:
        enabled = has_source and not busy
        self.scramble_button.set_enabled(enabled)
        self.restore_button.set_enabled(enabled)


__all__ = ["ActionRow"]

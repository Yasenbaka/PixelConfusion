"""Full-bleed application header with brand, steps and help."""

from __future__ import annotations

import tkinter as tk

from pixelconfusion.ui.images import brand_photo
from pixelconfusion.ui.text import make_label
from pixelconfusion.ui.theme import LINE, LINE_STRONG, MUTED, SURFACE, TEXT_BRIGHT
from pixelconfusion.ui.widgets import IconButton, Steps


class AppBar(tk.Frame):
    def __init__(self, master, *, on_help, side_pad=26, active_step=1):
        super().__init__(master, bg=SURFACE, height=62)
        self.grid_propagate(False)
        tk.Frame(self, bg=LINE, height=1).place(relx=0, rely=1, anchor="sw",
                                                relwidth=1)

        self._left = tk.Frame(self, bg=SURFACE)
        self._left.pack(side="left", pady=15, padx=(side_pad, 0))
        tk.Label(self._left, image=brand_photo(31), bg=SURFACE, bd=0).pack(side="left")
        make_label(self._left, "PixelConfusion", 13, "bold", TEXT_BRIGHT,
                   SURFACE).pack(side="left", padx=(10, 0))
        tk.Frame(self._left, bg=LINE_STRONG, width=1, height=22).pack(
            side="left", padx=13, pady=4)
        title_block = tk.Frame(self._left, bg=SURFACE)
        title_block.pack(side="left")
        make_label(title_block, "图片混淆与复原", 12, "bold", TEXT_BRIGHT,
                   SURFACE).pack(anchor="w")
        make_label(
            title_block,
            "打乱像素顺序，再用相同的参数完整还原。所有处理都在本机完成。",
            8,
            fg=MUTED,
            bg=SURFACE,
        ).pack(anchor="w", pady=(2, 0))

        self._right = tk.Frame(self, bg=SURFACE)
        self._right.pack(side="right", pady=16, padx=(0, side_pad))
        IconButton(self._right, "help", command=on_help, size=30, icon_size=16,
                   tooltip="使用说明", outer_bg=SURFACE).pack(side="right", padx=(7, 0))
        self.steps = Steps(self._right, active=active_step, outer_bg=SURFACE)
        self.steps.pack(side="right")

    def set_insets(self, inset: int) -> None:
        self._left.pack_configure(padx=(inset, 0))
        self._right.pack_configure(padx=(0, inset))

    def set_steps(self, active: int) -> None:
        self.steps.set_active(active)


__all__ = ["AppBar"]

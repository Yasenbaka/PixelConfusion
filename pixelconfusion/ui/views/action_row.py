"""Direction buttons plus the automatic batch controls."""

from __future__ import annotations

import tkinter as tk

from pixelconfusion.ui.theme import BG
from pixelconfusion.ui.widgets import PillButton


class ActionRow(tk.Frame):
    def __init__(self, master, *, on_scramble, on_restore, on_auto, on_auto_next):
        super().__init__(master, bg=BG)
        self.grid_columnconfigure(0, weight=1, uniform="action")
        self.grid_columnconfigure(1, weight=1, uniform="action")
        self._mode = "single"
        self._auto = False
        self._has_source = False
        self._busy = False
        self._has_batch = False
        self._can_next = True

        # Regular direction buttons.
        self.restore_button = PillButton(self, "反向混淆", command=on_restore,
                                         icon="arrow-left", kind="primary",
                                         height=38)
        self.restore_button.grid(row=0, column=0, sticky="ew")
        self.scramble_button = PillButton(self, "正向混淆", command=on_scramble,
                                          icon="arrow-right", kind="rose",
                                          height=38)
        self.scramble_button.grid(row=0, column=1, sticky="ew", padx=(8, 0))

        # Automatic batch buttons use the same blue primary accent.
        self.auto_button = PillButton(self, "自动混淆", command=on_auto,
                                      icon="shuffle", kind="primary", height=38)
        self.auto_button.grid(row=0, column=0, sticky="ew")
        self.auto_next_button = PillButton(self, "自动下一批混淆",
                                           command=on_auto_next,
                                           icon="arrow-right", kind="primary",
                                           height=38)
        self.auto_next_button.grid(row=0, column=1, sticky="ew", padx=(8, 0))
        self.auto_button.grid_remove()
        self.auto_next_button.grid_remove()
        self._apply_visibility()
        self._apply_enabled()

    def set_mode(self, mode: str, auto: bool):
        self._mode = mode
        self._auto = bool(auto)
        self._apply_visibility()
        self._apply_enabled()

    def set_enabled(self, has_source: bool, busy: bool, has_batch: bool = False,
                    can_next: bool = True):
        self._has_source = has_source
        self._busy = busy
        self._has_batch = has_batch
        self._can_next = can_next
        self._apply_enabled()

    def _apply_visibility(self):
        automatic = self._mode == "batch" and self._auto
        if automatic:
            self.restore_button.grid_remove()
            self.scramble_button.grid_remove()
            self.auto_button.grid()
            self.auto_next_button.grid()
        else:
            self.auto_button.grid_remove()
            self.auto_next_button.grid_remove()
            self.restore_button.grid()
            self.scramble_button.grid()

    def _apply_enabled(self):
        enabled = self._has_source and not self._busy
        self.restore_button.set_enabled(enabled)
        self.scramble_button.set_enabled(enabled)
        self.auto_button.set_enabled(enabled)
        self.auto_next_button.set_enabled(
            enabled and self._has_batch and self._can_next)


__all__ = ["ActionRow"]

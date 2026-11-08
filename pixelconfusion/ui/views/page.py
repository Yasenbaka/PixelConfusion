"""Top-level page shell and responsive content inset."""

from __future__ import annotations

import tkinter as tk

from pixelconfusion.ui.theme import BG
from pixelconfusion.ui.views.app_bar import AppBar
from pixelconfusion.ui.views.workspace import WorkspaceView


class PageView(tk.Frame):
    """Full-bleed header plus a width-capped, centred content column."""

    CONTENT_WIDTH = 1320
    SIDE_PAD = 26

    def __init__(
        self,
        master,
        *,
        on_help,
        on_pick,
        on_clear,
        on_demo,
        on_method_change,
        on_scramble,
        on_restore,
        on_use_result,
        on_save,
    ):
        super().__init__(master, bg=BG)
        self._inset_job = None
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.appbar = AppBar(self, on_help=on_help, side_pad=self.SIDE_PAD)
        self.appbar.grid(row=0, column=0, sticky="ew")

        self.main = tk.Frame(self, bg=BG)
        self.main.grid(row=1, column=0, sticky="nsew", padx=self.SIDE_PAD)
        self.main.grid_columnconfigure(0, weight=1)
        self.main.grid_rowconfigure(0, weight=1)

        self.workspace = WorkspaceView(
            self.main,
            on_pick=on_pick,
            on_clear=on_clear,
            on_demo=on_demo,
            on_method_change=on_method_change,
            on_scramble=on_scramble,
            on_restore=on_restore,
            on_use_result=on_use_result,
            on_save=on_save,
        )
        self.workspace.grid(row=0, column=0, sticky="nsew", pady=(18, 18))
        self.bind("<Configure>", self._schedule_inset)

    def _schedule_inset(self, event) -> None:
        if event.widget is not self:
            return
        if self._inset_job:
            self.after_cancel(self._inset_job)
        self._inset_job = self.after(20, self.apply_inset)

    def apply_inset(self) -> None:
        self._inset_job = None
        if not self.winfo_exists():
            return
        inset = self.SIDE_PAD + max(0, self.winfo_width() - self.CONTENT_WIDTH) // 2
        self.main.grid_configure(padx=inset)
        self.appbar.set_insets(inset)

    def cancel_pending(self) -> None:
        if self._inset_job:
            try:
                self.after_cancel(self._inset_job)
            except tk.TclError:
                pass
            self._inset_job = None


__all__ = ["PageView"]

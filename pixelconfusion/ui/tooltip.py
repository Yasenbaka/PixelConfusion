"""Delayed hover tooltip used by icon buttons."""

from __future__ import annotations

import tkinter as tk

from pixelconfusion.ui.theme import LINE_STRONG, SURFACE_ALT, TEXT, ui_font


class Tooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.job = None
        self.tip = None
        widget.bind("<Enter>", self._schedule, add="+")
        widget.bind("<Leave>", self._hide, add="+")
        widget.bind("<ButtonPress>", self._hide, add="+")

    def _schedule(self, _event=None):
        self._cancel()
        self.job = self.widget.after(550, self._show)

    def _show(self):
        if self.tip or not self.widget.winfo_exists():
            return
        x = self.widget.winfo_rootx() + self.widget.winfo_width() // 2
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 6
        self.tip = tk.Toplevel(self.widget)
        self.tip.overrideredirect(True)
        self.tip.attributes("-topmost", True)
        frame = tk.Frame(self.tip, bg=SURFACE_ALT, padx=8, pady=4,
                         highlightbackground=LINE_STRONG, highlightthickness=1)
        frame.pack()
        tk.Label(frame, text=self.text, bg=SURFACE_ALT, fg=TEXT,
                 font=ui_font(8)).pack()
        self.tip.update_idletasks()
        width = self.tip.winfo_width()
        self.tip.geometry(f"+{x - width // 2}+{y}")

    def _cancel(self):
        if self.job:
            self.widget.after_cancel(self.job)
            self.job = None

    def _hide(self, _event=None):
        self._cancel()
        if self.tip:
            self.tip.destroy()
            self.tip = None


__all__ = ["Tooltip"]

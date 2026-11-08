"""Canvas buttons and text links."""

from __future__ import annotations

import tkinter as tk

from pixelconfusion.ui.drawing import draw_round
from pixelconfusion.ui.images import icon_photo
from pixelconfusion.ui.theme import (
    ACCENT_BORDER,
    ACCENT_HOVER,
    FAINT,
    INK,
    LINE,
    MUTED,
    ROSE,
    ROSE_BORDER,
    ROSE_HOVER,
    SURFACE_ALT,
    TEXT,
    WHITE,
    parent_background,
    ui_font,
)
from pixelconfusion.ui.tooltip import Tooltip


class PillButton(tk.Canvas):
    def __init__(self, master, text, command=None, icon=None, kind="primary",
                 height=40, width=None, small=False, outer_bg=None):
        self._label = text
        self._command = command
        self._icon = icon
        self._kind = kind
        self._small = small
        self._font = ui_font(8 if small else 9, "bold")
        self._icon_size = 13 if small else 15
        self._padding = 11 if small else 18
        natural = (self._padding * 2 + self._font.measure(text)
                   + (self._icon_size + 6 if icon else 0))
        super().__init__(master, bg=outer_bg or parent_background(master),
                         highlightthickness=0, bd=0, height=height,
                         width=width or natural, takefocus=0)
        self._enabled = True
        self._hover = False
        self._pressed = False
        self.bind("<Configure>", lambda _event: self._draw())
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)
        self._draw()

    def _colors(self):
        if not self._enabled:
            if self._kind == "ghost":
                return parent_background(self.master), FAINT, FAINT
            return SURFACE_ALT, "#686c72", "#686c72"
        if self._kind == "primary":
            fill = ACCENT_HOVER if self._hover else INK
            return fill, WHITE, WHITE
        if self._kind == "rose":
            fill = ROSE_HOVER if self._hover else ROSE
            return fill, WHITE, WHITE
        if self._kind == "secondary":
            fill = "#414449" if self._hover else "#35373b"
            return fill, TEXT, TEXT
        fill = SURFACE_ALT if self._hover else parent_background(self.master)
        return fill, MUTED, MUTED

    def _draw(self):
        self.delete("all")
        width = max(self.winfo_width(), 2)
        height = max(self.winfo_height(), 2)
        fill, foreground, icon_color = self._colors()
        outline = ""
        if self._kind == "secondary" and self._enabled:
            outline = "#5c6066" if self._hover else "#4a4d52"
        elif self._kind == "primary" and self._enabled:
            outline = "#6ea4ff" if self._hover else ACCENT_BORDER
        elif self._kind == "rose" and self._enabled:
            outline = ROSE_BORDER
        elif not self._enabled and self._kind != "ghost":
            outline = LINE
        draw_round(self, 2, 2, width - 2, height - 2, 5, fill, outline)
        icon_width = (self._icon_size + 6) if self._icon else 0
        total = self._font.measure(self._label) + icon_width
        x = (width - total) / 2
        if self._icon:
            self.create_image(x, height / 2,
                              image=icon_photo(self._icon, icon_color, self._icon_size),
                              anchor="w")
            x += icon_width
        self.create_text(x, height / 2, text=self._label, fill=foreground,
                         font=self._font, anchor="w")

    def _on_enter(self, _event):
        if self._enabled:
            self._hover = True
            self.configure(cursor="hand2")
            self._draw()

    def _on_leave(self, _event):
        self._hover = False
        self._pressed = False
        self.configure(cursor="")
        self._draw()

    def _on_press(self, _event):
        if self._enabled:
            self._pressed = True

    def _on_release(self, event):
        if not self._enabled or not self._pressed:
            return
        self._pressed = False
        if 0 <= event.x <= self.winfo_width() and 0 <= event.y <= self.winfo_height():
            if self._command:
                self._command()

    def set_enabled(self, enabled: bool):
        if self._enabled != enabled:
            self._enabled = enabled
            self.configure(cursor="hand2" if enabled and self._hover else "")
            self._draw()


class IconButton(tk.Canvas):
    def __init__(self, master, icon, command=None, size=28, icon_size=15,
                 tooltip=None, outer_bg=None, enabled=True):
        super().__init__(master, bg=outer_bg or parent_background(master),
                         highlightthickness=0, bd=0, width=size, height=size,
                         takefocus=0)
        self._icon = icon
        self._icon_size = icon_size
        self._command = command
        self._enabled = enabled
        self._hover = False
        self.bind("<Configure>", lambda _event: self._draw())
        self.bind("<Enter>", self._enter)
        self.bind("<Leave>", self._leave)
        self.bind("<ButtonRelease-1>", self._click)
        if tooltip:
            Tooltip(self, tooltip)
        self._draw()

    def _draw(self):
        self.delete("all")
        width = max(self.winfo_width(), 2)
        height = max(self.winfo_height(), 2)
        if self._hover and self._enabled:
            draw_round(self, 1, 1, width - 1, height - 1, 4, "#35373b")
        color = "#b8bec6" if self._enabled else "#686c72"
        self.create_image(width / 2, height / 2,
                          image=icon_photo(self._icon, color, self._icon_size))

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
        if (self._enabled
                and 0 <= event.x <= self.winfo_width()
                and 0 <= event.y <= self.winfo_height()):
            if self._command:
                self._command()

    def set_enabled(self, enabled: bool):
        self._enabled = enabled
        self._draw()


class TextLink(tk.Canvas):
    def __init__(self, master, text, command=None, icon="sparkles", font_size=8,
                 outer_bg=None):
        self._font = ui_font(font_size)
        self._label = text
        self._icon = icon
        self._command = command
        width = self._font.measure(text) + 24
        super().__init__(master, bg=outer_bg or parent_background(master),
                         highlightthickness=0, bd=0, width=width, height=22,
                         takefocus=0)
        self._hover = False
        self._enabled = True
        self.bind("<Configure>", lambda _event: self._draw())
        self.bind("<Enter>", self._enter)
        self.bind("<Leave>", self._leave)
        self.bind("<ButtonRelease-1>", self._click)
        self._draw()

    def _draw(self):
        self.delete("all")
        width = max(self.winfo_width(), 2)
        if self._hover and self._enabled:
            draw_round(self, 1, 1, width - 1, 20, 4, "#35373b")
        color = MUTED if self._enabled else "#686c72"
        if self._hover and self._enabled:
            color = TEXT
        self.create_image(5, 11, image=icon_photo(self._icon, color, 12), anchor="w")
        self.create_text(22, 11, text=self._label, fill=color, font=self._font,
                         anchor="w")

    def _enter(self, _event):
        self._hover = True
        self.configure(cursor="hand2")
        self._draw()

    def _leave(self, _event):
        self._hover = False
        self.configure(cursor="")
        self._draw()

    def _click(self, event):
        if self._enabled and 0 <= event.x <= self.winfo_width() and 0 <= event.y <= 22:
            if self._command:
                self._command()

    def set_text(self, text):
        self._label = text
        self.configure(width=self._font.measure(text) + 24)
        self._draw()

    def set_enabled(self, enabled):
        self._enabled = enabled
        self._draw()


__all__ = ["IconButton", "PillButton", "TextLink"]

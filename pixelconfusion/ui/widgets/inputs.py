"""Segmented control, numeric stepper and text field widgets."""

from __future__ import annotations

import tkinter as tk

from pixelconfusion.ui.drawing import draw_round
from pixelconfusion.ui.images import icon_photo
from pixelconfusion.ui.theme import (
    FAINT,
    FIELD,
    INK,
    LINE,
    LINE_STRONG,
    MUTED,
    SELECT,
    SURFACE_ALT,
    TEXT,
    TEXT_BRIGHT,
    parent_background,
    ui_font,
)


class Segmented(tk.Canvas):
    DEFAULT_OPTIONS = (
        ("gilbert", "Gilbert", "route"),
        ("arnold", "Arnold", "grid"),
    )

    def __init__(self, master, value, options=None, on_change=None, height=38,
                 outer_bg=None):
        super().__init__(master, bg=outer_bg or parent_background(master),
                         highlightthickness=0, bd=0, height=height, takefocus=0)
        self.value = value
        self._on_change = on_change
        self._enabled = True
        self._hover = None
        self.options = tuple(options) if options else self.DEFAULT_OPTIONS
        self.bind("<Configure>", lambda _event: self._draw())
        self.bind("<ButtonRelease-1>", self._click)
        self.bind("<Motion>", self._motion)
        self.bind("<Leave>", self._leave)
        self._draw()

    def _draw(self):
        self.delete("all")
        width = max(self.winfo_width(), 2)
        height = max(self.winfo_height(), 2)
        draw_round(self, 2, 2, width - 2, height - 2, 6, FIELD, LINE_STRONG)
        pad = 4
        count = max(1, len(self.options))
        cell = (width - pad * 2) / count
        for index, option in enumerate(self.options):
            value, label = option[0], option[1]
            icon = option[2] if len(option) > 2 else None
            x1 = pad + index * cell
            x2 = x1 + cell
            active = value == self.value
            if active:
                draw_round(self, x1, pad, x2, height - pad, 4,
                           SELECT if self._enabled else SURFACE_ALT,
                           "#47709f" if self._enabled else LINE)
            color = TEXT_BRIGHT if active else MUTED
            if active:
                icon_color = "#cfe0ff"
            else:
                icon_color = color
            if not self._enabled:
                color = "#686c72"
                icon_color = color
            label_font = ui_font(9, "bold" if active else "normal")
            icon_width = 13 if icon else 0
            gap = 5 if icon else 0
            total = icon_width + gap + label_font.measure(label)
            start = (x1 + x2 - total) / 2
            if icon:
                self.create_image(start, height / 2,
                                  image=icon_photo(icon, icon_color, 13),
                                  anchor="w")
            self.create_text(start + icon_width + gap, height / 2, text=label,
                             fill=color, font=label_font, anchor="w")
        if self._enabled:
            self.configure(cursor="hand2")

    def _click(self, event):
        if not self._enabled:
            return
        width = self.winfo_width()
        pad = 4
        cell = max(1.0, (width - pad * 2) / max(1, len(self.options)))
        index = int((event.x - pad) // cell)
        index = max(0, min(len(self.options) - 1, index))
        value = self.options[index][0]
        if value != self.value:
            self.value = value
            self._draw()
            if self._on_change:
                self._on_change(value)

    def _motion(self, _event):
        if self._enabled:
            self.configure(cursor="hand2")

    def _leave(self, _event):
        self.configure(cursor="")

    def set(self, value):
        self.value = value
        self._draw()

    def set_enabled(self, enabled):
        self._enabled = enabled
        self._draw()


class NumberStepper(tk.Canvas):
    def __init__(self, master, variable: tk.StringVar, minimum=1, maximum=1_000_000,
                 height=38, outer_bg=None):
        super().__init__(master, bg=outer_bg or parent_background(master),
                         highlightthickness=0, bd=0, height=height, takefocus=0)
        self.var = variable
        self.minimum = minimum
        self.maximum = maximum
        self._enabled = True
        self._hover = None
        self._focus = False
        self._entry = tk.Entry(self, textvariable=variable, relief="flat", bd=0,
                               highlightthickness=0, justify="center", bg=FIELD,
                               fg=TEXT, insertbackground=INK, font=ui_font(9))
        self._entry_win = self.create_window(35, height / 2, anchor="w",
                                             window=self._entry, width=120,
                                             height=24, tags="entry")
        self._entry_font_size = 9
        variable.trace_add("write", lambda *_args: self._fit_entry_font())
        self._entry.bind("<FocusIn>", self._focus_in)
        self._entry.bind("<FocusOut>", self._focus_out)
        self._entry.bind("<MouseWheel>", self._wheel)
        self.bind("<Configure>", self._redraw)
        self.bind("<ButtonRelease-1>", self._click)
        self.bind("<Motion>", self._motion)
        self.bind("<Leave>", self._leave)
        self._redraw()

    def _redraw(self, _event=None):
        width = max(self.winfo_width(), 2)
        height = max(self.winfo_height(), 2)
        self.delete("chrome")
        fill = FIELD if self._enabled else SURFACE_ALT
        border = (INK if self._focus and self._enabled
                  else (LINE_STRONG if self._enabled else LINE))
        draw_round(self, 2, 2, width - 2, height - 2, 5, fill, border, tags="chrome")
        self._entry.configure(
            bg=fill,
            state="normal" if self._enabled else "disabled",
            fg=TEXT if self._enabled else "#686c72",
            insertbackground=TEXT_BRIGHT,
            disabledbackground=SURFACE_ALT,
            disabledforeground="#686c72",
        )
        self.coords(self._entry_win, 35, height / 2)
        self.itemconfigure(self._entry_win, width=max(20, width - 70), height=24)
        value = self._value()
        minus_color = MUTED if self._enabled and value > self.minimum else "#4a4d52"
        plus_color = MUTED if self._enabled and value < self.maximum else "#4a4d52"
        if self._hover == "minus":
            draw_round(self, 7, height / 2 - 13, 35, height / 2 + 13, 4,
                       "#35373b", tags="chrome")
        if self._hover == "plus":
            draw_round(self, width - 35, height / 2 - 13, width - 7, height / 2 + 13,
                       4, "#35373b", tags="chrome")
        self.create_image(21, height / 2, image=icon_photo("minus", minus_color, 14),
                          tags="chrome")
        self.create_image(width - 21, height / 2,
                          image=icon_photo("plus", plus_color, 14), tags="chrome")
        self.tag_raise("entry")
        self._fit_entry_font()

    def _fit_entry_font(self):
        width = max(self.winfo_width(), 80)
        available = max(30, width - 78)
        text = self.var.get()
        size = 9
        while size > 7 and ui_font(size).measure(text) > available:
            size -= 1
        if size != self._entry_font_size:
            self._entry_font_size = size
            self._entry.configure(font=ui_font(size))

    def _value(self):
        try:
            return int(self.var.get())
        except ValueError:
            return 1

    def _click(self, event):
        if not self._enabled:
            return
        value = self._value()
        if event.x < 38:
            value -= 1
        elif event.x > self.winfo_width() - 38:
            value += 1
        else:
            return
        value = max(self.minimum, min(self.maximum, value))
        self.var.set(str(value))
        self._redraw()

    def _motion(self, event):
        if not self._enabled:
            return
        if event.x < 38:
            side = "minus"
        elif event.x > self.winfo_width() - 38:
            side = "plus"
        else:
            side = None
        if side != self._hover:
            self._hover = side
            self.configure(cursor="hand2" if side else "")
            self._redraw()

    def _leave(self, _event):
        self._hover = None
        self.configure(cursor="")
        self._redraw()

    def _focus_in(self, _event):
        self._focus = True
        self._redraw()

    def _focus_out(self, _event):
        self._focus = False
        self._redraw()

    def _wheel(self, event):
        if not self._enabled:
            return
        value = self._value() + (1 if event.delta > 0 else -1)
        self.var.set(str(max(self.minimum, min(self.maximum, value))))
        self._redraw()

    def set_enabled(self, enabled):
        self._enabled = enabled
        if not enabled:
            self._focus = False
        self._redraw()


class TextField(tk.Canvas):
    def __init__(self, master, variable: tk.StringVar, placeholder="", height=38,
                 outer_bg=None):
        super().__init__(master, bg=outer_bg or parent_background(master),
                         highlightthickness=0, bd=0, height=height, takefocus=0)
        self.var = variable
        self.placeholder = placeholder
        self._enabled = True
        self._focus = False
        self._entry = tk.Entry(self, textvariable=variable, relief="flat", bd=0,
                               highlightthickness=0, bg=FIELD, fg=TEXT,
                               insertbackground=INK, font=ui_font(9))
        self._entry_win = self.create_window(12, height / 2, anchor="w",
                                             window=self._entry, width=100,
                                             height=24, tags="entry")
        self._placeholder = tk.Label(self, text=placeholder, bg=FIELD, fg=FAINT,
                                     font=ui_font(9), anchor="w")
        self._ph_win = self.create_window(13, height / 2, anchor="w",
                                          window=self._placeholder, tags="placeholder")
        self._placeholder.bind("<Button-1>", lambda _event: self._entry.focus_set())
        self._entry.bind("<FocusIn>", self._focus_in)
        self._entry.bind("<FocusOut>", self._focus_out)
        variable.trace_add("write", lambda *_args: self._sync_placeholder())
        self.bind("<Configure>", self._redraw)
        self._sync_placeholder()
        self._redraw()

    def _sync_placeholder(self):
        show = self._enabled and not self._focus and not self.var.get()
        self.itemconfigure(self._ph_win, state="normal" if show else "hidden")
        self._fit_font()

    def _fit_font(self):
        width = max(self.winfo_width(), 60)
        available = max(30, width - 32)
        text = self.var.get()
        size = 9
        while size > 7 and ui_font(size).measure(text) > available:
            size -= 1
        if getattr(self, "_entry_font_size", None) != size:
            self._entry_font_size = size
            self._entry.configure(font=ui_font(size))

    def _redraw(self, _event=None):
        width = max(self.winfo_width(), 2)
        height = max(self.winfo_height(), 2)
        self.delete("chrome")
        fill = FIELD if self._enabled else SURFACE_ALT
        border = (INK if self._focus and self._enabled
                  else (LINE_STRONG if self._enabled else LINE))
        draw_round(self, 2, 2, width - 2, height - 2, 5, fill, border, tags="chrome")
        self._entry.configure(
            bg=fill,
            state="normal" if self._enabled else "disabled",
            fg=TEXT if self._enabled else "#686c72",
            insertbackground=TEXT_BRIGHT,
            disabledbackground=SURFACE_ALT,
            disabledforeground="#686c72",
        )
        self._placeholder.configure(bg=fill, fg=FAINT if self._enabled else "#686c72")
        self.coords(self._entry_win, 12, height / 2)
        self.itemconfigure(self._entry_win, width=max(20, width - 24), height=24)
        self.coords(self._ph_win, 13, height / 2)
        self.tag_raise("entry")
        self.tag_raise("placeholder")
        self._sync_placeholder()

    def _focus_in(self, _event):
        self._focus = True
        self._redraw()

    def _focus_out(self, _event):
        self._focus = False
        self._redraw()

    def set_enabled(self, enabled):
        self._enabled = enabled
        if not enabled:
            self._focus = False
        self._redraw()


__all__ = ["NumberStepper", "Segmented", "TextField"]

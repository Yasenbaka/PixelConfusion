"""Canvas-based visual layer for the PixelConfusion desktop app.

The widgets here keep the flat, rounded look of the HTML prototype without
falling back to native ttk chrome.
"""

from __future__ import annotations

import math
import tkinter as tk
import tkinter.font as tkfont
from pathlib import Path

from PIL import Image, ImageDraw, ImageTk

# ---------------------------------------------------------------- tokens
# Palette follows the FileExplorer reference: graphite surfaces, thin borders,
# a single blue accent, yellow warnings and a muted red for failures.
BG = "#1e1f22"
SURFACE = "#25272a"
SURFACE_ALT = "#2b2d30"
FIELD = "#1e1f22"
INK = "#2f6bff"  # primary accent, kept as INK for the drawing primitives
TEXT = "#d7dae0"
TEXT_BRIGHT = "#f0f1f2"
MUTED = "#8b9098"
FAINT = "#666a70"
LINE = "#3a3d41"
LINE_STRONG = "#45484d"
SELECT = "#354968"
GREEN = "#6ea4ff"
PINK = "#f2bd45"
RED = "#e65b63"
WHITE = "#ffffff"
ACCENT_HOVER = "#3c76ff"
ACCENT_BORDER = "#4279ff"
ACCENT_LIGHT = "#6ea4ff"
FONT_FAMILY = "Microsoft YaHei UI"

ICON_DIR = Path(__file__).resolve().parent / "assets" / "icons"

_fonts: dict[tuple[int, str], tkfont.Font] = {}
_icon_photos: dict[tuple[str, str, int], ImageTk.PhotoImage] = {}
_icon_bases: dict[str, Image.Image] = {}
_brand_cache: dict[int, ImageTk.PhotoImage] = {}


def ui_font(size: int, weight: str = "normal") -> tkfont.Font:
    key = (size, weight)
    if key not in _fonts:
        _fonts[key] = tkfont.Font(root=tk._default_root, family=FONT_FAMILY,
                                  size=size, weight=weight)
    return _fonts[key]


def _base_icon(name: str) -> Image.Image:
    if name not in _icon_bases:
        _icon_bases[name] = Image.open(ICON_DIR / f"{name}.png").convert("RGBA")
    return _icon_bases[name]


def icon_photo(name: str, color: str, size: int) -> ImageTk.PhotoImage:
    key = (name, color, size)
    if key not in _icon_photos:
        base = _base_icon(name)
        tinted = Image.new("RGBA", base.size, color)
        tinted.putalpha(base.getchannel("A"))
        tinted = tinted.resize((size, size), Image.Resampling.LANCZOS)
        _icon_photos[key] = ImageTk.PhotoImage(tinted)
    return _icon_photos[key]


def brand_photo(size: int = 31) -> ImageTk.PhotoImage:
    if size in _brand_cache:
        return _brand_cache[size]
    scale = 2
    mark = Image.new("RGBA", (size * scale, size * scale), (0, 0, 0, 0))
    ImageDraw.Draw(mark).rounded_rectangle(
        (0, 0, size * scale - 1, size * scale - 1),
        radius=max(5, round(size * 0.26)) * scale,
        fill=INK,
    )
    icon = _base_icon("pixelconfusion")
    inner = round(size * 0.58) * scale
    icon = icon.resize((inner, inner), Image.Resampling.LANCZOS)
    white = Image.new("RGBA", icon.size, (255, 255, 255, 255))
    white.putalpha(icon.getchannel("A"))
    offset = (size * scale - inner) // 2
    mark.alpha_composite(white, (offset, offset))
    mark = mark.resize((size, size), Image.Resampling.LANCZOS)
    _brand_cache[size] = ImageTk.PhotoImage(mark)
    return _brand_cache[size]


def rounded_points(x1: float, y1: float, x2: float, y2: float, radius: float,
                   steps: int = 9) -> list[float]:
    radius = max(0, min(radius, (x2 - x1) / 2, (y2 - y1) / 2))
    points: list[float] = []
    corners = (
        (x2 - radius, y1 + radius, -90),
        (x2 - radius, y2 - radius, 0),
        (x1 + radius, y2 - radius, 90),
        (x1 + radius, y1 + radius, 180),
    )
    for cx, cy, start in corners:
        for index in range(steps + 1):
            angle = math.radians(start + 90 * index / steps)
            points.extend((cx + radius * math.cos(angle), cy + radius * math.sin(angle)))
    return points


def draw_round(canvas: tk.Canvas, x1, y1, x2, y2, radius, fill, outline="", width=1, tags=""):
    return canvas.create_polygon(*rounded_points(x1, y1, x2, y2, radius),
                                 fill=fill, outline=outline or fill, width=width,
                                 smooth=False, tags=tags)


def dashed_round(canvas: tk.Canvas, x1, y1, x2, y2, radius, color, dash=(5, 4), tags=""):
    points = rounded_points(x1, y1, x2, y2, radius)
    points.extend(points[:2])
    return canvas.create_line(*points, fill=color, width=1, dash=dash, tags=tags)


def _outer_bg(master, fallback=BG):
    try:
        return master.cget("background")
    except (tk.TclError, AttributeError):
        return fallback


def _format_dims(width, height):
    return f"{width} × {height}"


def preview_photo(image: Image.Image, max_width: int, max_height: int) -> ImageTk.PhotoImage:
    preview = image.copy()
    preview.thumbnail((max(1, max_width), max(1, max_height)), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", preview.size, (30, 31, 34, 255))
    if preview.mode != "RGBA":
        preview = preview.convert("RGBA")
    canvas.alpha_composite(preview)
    return ImageTk.PhotoImage(canvas.convert("RGB"))


def thumbnail_photo(image: Image.Image, size: int = 64) -> ImageTk.PhotoImage:
    scale = 2
    side = size * scale
    ring = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    draw = ImageDraw.Draw(ring)
    draw.rounded_rectangle((0, 0, side - 1, side - 1), radius=round(size * 0.17) * scale, fill=INK)
    inset = 2 * scale
    draw.rounded_rectangle((inset, inset, side - inset - 1, side - inset - 1),
                           radius=round(size * 0.15) * scale, fill=SURFACE)
    thumb = image.copy().convert("RGBA")
    thumb.thumbnail((side - 10 * scale, side - 10 * scale), Image.Resampling.LANCZOS)
    thumb_mask = Image.new("L", thumb.size, 0)
    ImageDraw.Draw(thumb_mask).rounded_rectangle(
        (0, 0, thumb.width - 1, thumb.height - 1),
        radius=round(thumb.width * 0.12), fill=255,
    )
    x = (side - thumb.width) // 2
    y = (side - thumb.height) // 2
    ring.paste(thumb, (x, y), thumb_mask)
    ring = ring.resize((size, size), Image.Resampling.LANCZOS)
    return ImageTk.PhotoImage(ring)


# ---------------------------------------------------------------- widgets
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
        natural = self._padding * 2 + self._font.measure(text) + (self._icon_size + 6 if icon else 0)
        super().__init__(master, bg=outer_bg or _outer_bg(master), highlightthickness=0, bd=0,
                         height=height, width=width or natural, takefocus=0)
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
                return _outer_bg(self.master), FAINT, FAINT
            return SURFACE_ALT, "#686c72", "#686c72"
        if self._kind == "primary":
            fill = ACCENT_HOVER if self._hover else INK
            return fill, WHITE, WHITE
        if self._kind == "secondary":
            fill = "#414449" if self._hover else "#35373b"
            return fill, TEXT, TEXT
        fill = SURFACE_ALT if self._hover else _outer_bg(self.master)
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
        elif not self._enabled and self._kind != "ghost":
            outline = LINE
        draw_round(self, 2, 2, width - 2, height - 2, 5, fill, outline)
        icon_width = (self._icon_size + 6) if self._icon else 0
        total = self._font.measure(self._label) + icon_width
        x = (width - total) / 2
        if self._icon:
            self.create_image(x, height / 2, image=icon_photo(self._icon, icon_color, self._icon_size),
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
    def __init__(self, master, icon, command=None, size=28, icon_size=15, tooltip=None,
                 outer_bg=None, enabled=True):
        super().__init__(master, bg=outer_bg or _outer_bg(master), highlightthickness=0, bd=0,
                         width=size, height=size, takefocus=0)
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
        self.create_image(width / 2, height / 2, image=icon_photo(self._icon, color, self._icon_size))

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
        if self._enabled and 0 <= event.x <= self.winfo_width() and 0 <= event.y <= self.winfo_height():
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
        super().__init__(master, bg=outer_bg or _outer_bg(master), highlightthickness=0, bd=0,
                         width=width, height=22, takefocus=0)
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
        self.create_text(22, 11, text=self._label, fill=color, font=self._font, anchor="w")

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
        super().__init__(master, bg=outer_bg or _outer_bg(master), highlightthickness=0, bd=0,
                         width=width, height=height, takefocus=0)
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
            self.create_image(x, height / 2, image=icon_photo(self._icon, self._fg, 12), anchor="w")
            x += 17
        self.create_text(x, height / 2, text=self._text, fill=self._fg,
                         font=self._font, anchor="w")

    def update_pill(self, text=None, bg=None, fg=None, dot=None, icon=None, border=None):
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


class Card(tk.Canvas):
    def __init__(self, master, height=100, radius=8, bg=SURFACE, border=LINE,
                 outer_bg=None, inset=12):
        super().__init__(master, bg=outer_bg or _outer_bg(master), highlightthickness=0, bd=0,
                         height=height, width=1, takefocus=0)
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


class Segmented(tk.Canvas):
    def __init__(self, master, value, on_change=None, height=38, outer_bg=None):
        super().__init__(master, bg=outer_bg or _outer_bg(master), highlightthickness=0, bd=0,
                         height=height, takefocus=0)
        self.value = value
        self._on_change = on_change
        self._enabled = True
        self._hover = None
        self.options = (("gilbert", "Gilbert", "route"), ("arnold", "Arnold", "grid"))
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
        cell = (width - pad * 2) / 2
        for index, (value, label, icon) in enumerate(self.options):
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
            icon_width = 13
            total = icon_width + 5 + label_font.measure(label)
            start = (x1 + x2 - total) / 2
            self.create_image(start, height / 2, image=icon_photo(icon, icon_color, 13), anchor="w")
            self.create_text(start + icon_width + 5, height / 2, text=label, fill=color,
                             font=label_font, anchor="w")
        if self._enabled:
            self.configure(cursor="hand2")

    def _click(self, event):
        if not self._enabled:
            return
        width = self.winfo_width()
        value = self.options[0][0] if event.x < width / 2 else self.options[1][0]
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
        super().__init__(master, bg=outer_bg or _outer_bg(master), highlightthickness=0, bd=0,
                         height=height, takefocus=0)
        self.var = variable
        self.minimum = minimum
        self.maximum = maximum
        self._enabled = True
        self._hover = None
        self._focus = False
        self._entry = tk.Entry(self, textvariable=variable, relief="flat", bd=0,
                               highlightthickness=0, justify="center", bg=FIELD, fg=TEXT,
                               insertbackground=INK, font=ui_font(9))
        self._entry_win = self.create_window(35, height / 2, anchor="w", window=self._entry,
                                             width=120, height=24, tags="entry")
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
        border = INK if self._focus and self._enabled else (LINE_STRONG if self._enabled else LINE)
        draw_round(self, 2, 2, width - 2, height - 2, 5, fill, border, tags="chrome")
        self._entry.configure(bg=fill, state="normal" if self._enabled else "disabled",
                              fg=TEXT if self._enabled else "#686c72",
                              insertbackground=TEXT_BRIGHT,
                              disabledbackground=SURFACE_ALT, disabledforeground="#686c72")
        self.coords(self._entry_win, 35, height / 2)
        self.itemconfigure(self._entry_win, width=max(20, width - 70), height=24)
        value = self._value()
        minus_color = MUTED if self._enabled and value > self.minimum else "#4a4d52"
        plus_color = MUTED if self._enabled and value < self.maximum else "#4a4d52"
        if self._hover == "minus":
            draw_round(self, 7, height / 2 - 13, 35, height / 2 + 13, 4, "#35373b", tags="chrome")
        if self._hover == "plus":
            draw_round(self, width - 35, height / 2 - 13, width - 7, height / 2 + 13,
                       4, "#35373b", tags="chrome")
        self.create_image(21, height / 2, image=icon_photo("minus", minus_color, 14), tags="chrome")
        self.create_image(width - 21, height / 2, image=icon_photo("plus", plus_color, 14), tags="chrome")
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
        super().__init__(master, bg=outer_bg or _outer_bg(master), highlightthickness=0, bd=0,
                         height=height, takefocus=0)
        self.var = variable
        self.placeholder = placeholder
        self._enabled = True
        self._focus = False
        self._entry = tk.Entry(self, textvariable=variable, relief="flat", bd=0,
                               highlightthickness=0, bg=FIELD, fg=TEXT, insertbackground=INK,
                               font=ui_font(9))
        self._entry_win = self.create_window(12, height / 2, anchor="w", window=self._entry,
                                             width=100, height=24, tags="entry")
        self._placeholder = tk.Label(self, text=placeholder, bg=FIELD, fg=FAINT,
                                     font=ui_font(9), anchor="w")
        self._ph_win = self.create_window(13, height / 2, anchor="w", window=self._placeholder,
                                          tags="placeholder")
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
        border = INK if self._focus and self._enabled else (LINE_STRONG if self._enabled else LINE)
        draw_round(self, 2, 2, width - 2, height - 2, 5, fill, border, tags="chrome")
        self._entry.configure(bg=fill, state="normal" if self._enabled else "disabled",
                              fg=TEXT if self._enabled else "#686c72",
                              insertbackground=TEXT_BRIGHT,
                              disabledbackground=SURFACE_ALT, disabledforeground="#686c72")
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


class HintBox(tk.Canvas):
    def __init__(self, master, text="", height=46, outer_bg=None):
        super().__init__(master, bg=outer_bg or _outer_bg(master), highlightthickness=0, bd=0,
                         height=height, takefocus=0)
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
        super().__init__(master, bg=outer_bg or _outer_bg(master), highlightthickness=0, bd=0,
                         height=22, width=1, takefocus=0)
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
            self.create_text(x, y, text=label, fill=label_color, font=label_font, anchor="w")
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
        super().__init__(master, bg=outer_bg or _outer_bg(master), highlightthickness=0, bd=0,
                         width=width, height=height, takefocus=0)
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


class PreviewTile(tk.Frame):
    def __init__(self, master, title, kind="input", on_pick=None):
        super().__init__(master, bg=SURFACE)
        self.kind = kind
        self._on_pick = on_pick
        self._mode = "empty"
        self._image = None
        self._photo = None
        self._busy_title = "正在处理"
        self._busy_fraction = 0.0
        self._spin_angle = 0
        self._spin_job = None
        self._draw_job = None
        self._empty_title = "还没有输入图片"
        self._empty_subtitle = "选择图片或使用内置测试图"
        self._empty_icon = "image"
        self._pickable = False
        header = tk.Frame(self, bg=SURFACE, height=18)
        header.pack(fill="x")
        dot = tk.Canvas(header, width=7, height=7, bg=SURFACE, highlightthickness=0, bd=0)
        dot.pack(side="left", padx=(2, 6), pady=(5, 0))
        if kind == "input":
            dot.create_oval(1, 1, 6, 6, fill=FAINT, outline="")
        else:
            dot.create_oval(1, 1, 6, 6, fill=INK, outline="")
        tk.Label(header, text=title, bg=SURFACE, fg=TEXT,
                 font=ui_font(9, "bold")).pack(side="left")
        self._dims = tk.Label(header, text="— × —", bg=SURFACE, fg=FAINT, font=ui_font(8))
        self._dims.pack(side="right")
        self._well = tk.Canvas(self, bg=SURFACE, highlightthickness=0, bd=0)
        self._well.pack(fill="both", expand=True, pady=(8, 0))
        self._well.bind("<Configure>", self._schedule)
        self._well.bind("<ButtonRelease-1>", self._click)
        self._pick_area = None

    def set_dims(self, text):
        self._dims.configure(text=text)

    def set_empty(self, title, subtitle, icon, pickable=False):
        self._mode = "empty"
        self._empty_title = title
        self._empty_subtitle = subtitle
        self._empty_icon = icon
        self._pickable = pickable
        self._stop_spin()
        self._schedule()
        self._well.configure(cursor="hand2" if pickable else "")

    def set_image(self, image, dims=None):
        self._mode = "image"
        self._image = image
        if dims:
            self.set_dims(dims)
        else:
            self.set_dims(_format_dims(image.width, image.height))
        self._stop_spin()
        self._schedule()
        self._well.configure(cursor="")

    def set_busy(self, title, fraction=0.0):
        self._mode = "busy"
        self._busy_title = title
        self._busy_fraction = fraction
        self.set_dims("处理中…")
        self._well.configure(cursor="")
        if self.kind == "output" and self._spin_job is None:
            self._start_spin()
        else:
            self._draw()

    def _schedule(self, _event=None):
        if self._draw_job:
            self.after_cancel(self._draw_job)
        self._draw_job = self.after(30, self._draw)

    def _draw(self):
        self._draw_job = None
        canvas = self._well
        canvas.delete("all")
        width = canvas.winfo_width()
        height = canvas.winfo_height()
        if width < 8 or height < 8:
            return
        if self._mode == "busy":
            draw_round(canvas, 2, 2, width - 2, height - 2, 6, FIELD, LINE)
            self._draw_busy(canvas, width, height)
            return
        if self._mode == "image" and self._image is not None:
            draw_round(canvas, 2, 2, width - 2, height - 2, 6, FIELD, LINE)
            self._photo = preview_photo(self._image, width - 40, height - 40)
            canvas.create_image(width / 2, height / 2, image=self._photo)
            return
        draw_round(canvas, 2, 2, width - 2, height - 2, 6, FIELD)
        dashed_round(canvas, 2, 2, width - 2, height - 2, 6, LINE_STRONG)
        center = height * 0.46
        draw_round(canvas, width / 2 - 18, center - 44, width / 2 + 18, center - 8, 7,
                   SURFACE_ALT, LINE)
        canvas.create_image(width / 2, center - 26,
                            image=icon_photo(self._empty_icon, MUTED, 16))
        canvas.create_text(width / 2, center + 8, text=self._empty_title, fill=TEXT,
                           font=ui_font(9, "bold"))
        canvas.create_text(width / 2, center + 26, text=self._empty_subtitle, fill=MUTED,
                           font=ui_font(8))
        self._pick_area = None
        if self._pickable:
            button_width, button_height = 88, 28
            x1 = width / 2 - button_width / 2
            y1 = center + 42
            x2 = x1 + button_width
            y2 = y1 + button_height
            draw_round(canvas, x1, y1, x2, y2, 5, "#35373b", "#4a4d52")
            canvas.create_image(x1 + 15, (y1 + y2) / 2,
                                image=icon_photo("image", TEXT, 12), anchor="w")
            canvas.create_text(x1 + 31, (y1 + y2) / 2, text="选择图片", fill=TEXT,
                               font=ui_font(8, "bold"), anchor="w")
            self._pick_area = (x1, y1, x2, y2)

    def _draw_busy(self, canvas, width, height):
        center_x, center_y = width / 2, height / 2 - 8
        box = 34
        canvas.create_oval(center_x - box / 2, center_y - box / 2,
                           center_x + box / 2, center_y + box / 2,
                           outline=LINE_STRONG, width=2)
        start = self._spin_angle
        canvas.create_arc(center_x - box / 2, center_y - box / 2,
                          center_x + box / 2, center_y + box / 2,
                          start=start, extent=110, style="arc", outline=INK, width=2)
        canvas.create_arc(center_x - box / 2, center_y - box / 2,
                          center_x + box / 2, center_y + box / 2,
                          start=start + 150, extent=70, style="arc", outline=ACCENT_LIGHT, width=2)
        canvas.create_text(center_x, center_y + 38, text=self._busy_title, fill=TEXT,
                           font=ui_font(9, "bold"))
        canvas.create_text(center_x, center_y + 55, text=f"{round(self._busy_fraction * 100)}%",
                           fill=FAINT, font=ui_font(8))

    def _start_spin(self):
        self._stop_spin()
        self._spin_angle = 0
        self._spin()

    def _spin(self):
        if self._mode != "busy":
            return
        self._spin_angle = (self._spin_angle + 18) % 360
        self._draw()
        self._spin_job = self.after(60, self._spin)

    def _stop_spin(self):
        if self._spin_job:
            self.after_cancel(self._spin_job)
            self._spin_job = None

    def set_busy_progress(self, fraction):
        self._busy_fraction = fraction
        if self._mode == "busy":
            self._draw()

    def _click(self, _event):
        if self._mode == "empty" and self._pickable and self._on_pick:
            self._on_pick()


class DropZone(tk.Canvas):
    def __init__(self, master, command=None, height=108, outer_bg=None):
        super().__init__(master, bg=outer_bg or _outer_bg(master), highlightthickness=0, bd=0,
                         height=height, takefocus=0)
        self.command = command
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
        height = max(self.winfo_height(), 2)
        fill = (SURFACE_ALT if self._hover else FIELD) if self._enabled else SURFACE
        border = ("#5c6066" if self._hover else LINE_STRONG) if self._enabled else LINE
        draw_round(self, 2, 2, width - 2, height - 2, 6, fill)
        dashed_round(self, 2, 2, width - 2, height - 2, 6, border)
        center = height / 2
        draw_round(self, width / 2 - 14, center - 33, width / 2 + 14, center - 5, 6,
                   SURFACE_ALT, LINE)
        self.create_image(width / 2, center - 19,
                          image=icon_photo("image", MUTED if self._enabled else FAINT, 14))
        self.create_text(width / 2, center + 10, text="选择一张图片",
                         fill=TEXT if self._enabled else MUTED, font=ui_font(9, "bold"))
        self.create_text(width / 2, center + 27, text="PNG / JPG / WEBP / BMP · 单帧",
                         fill=FAINT, font=ui_font(7))

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
        if self._enabled and 0 <= event.x <= self.winfo_width() and 0 <= event.y <= self.winfo_height():
            if self.command:
                self.command()

    def set_enabled(self, enabled):
        self._enabled = enabled
        self._draw()


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
        tk.Label(frame, text=self.text, bg=SURFACE_ALT, fg=TEXT, font=ui_font(8)).pack()
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

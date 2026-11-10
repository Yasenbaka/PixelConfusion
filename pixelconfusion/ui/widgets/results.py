"""Scrollable iteration result grids used by the batch preview stage."""

from __future__ import annotations

import math
import tkinter as tk

from pixelconfusion.batch import BatchItem
from pixelconfusion.ui.drawing import draw_round
from pixelconfusion.ui.images import icon_photo, preview_photo
from pixelconfusion.ui.text import make_label
from pixelconfusion.ui.theme import (
    FAINT,
    FIELD,
    INK,
    LINE,
    MUTED,
    ROSE,
    SURFACE,
    SURFACE_ALT,
    TEXT,
    TEXT_BRIGHT,
    ui_font,
)


class ResultTile(tk.Canvas):
    """One clickable thumbnail with its iteration number."""

    def __init__(self, master, item: BatchItem, command=None, width=126, height=150,
                 accent=INK, outer_bg=FIELD):
        super().__init__(master, bg=outer_bg, width=width, height=height,
                         highlightthickness=0, bd=0, takefocus=0)
        self.item = item
        self._command = command
        self._accent = accent
        self._width = width
        self._height = height
        self._enabled = True
        self._hover = False
        image_area = width - 18
        self._photo = preview_photo(item.thumbnail, image_area, image_area)
        self.bind("<Configure>", lambda _event: self._draw())
        self.bind("<Enter>", self._enter)
        self.bind("<Leave>", self._leave)
        self.bind("<ButtonRelease-1>", self._click)
        self._draw()

    def _draw(self):
        self.delete("all")
        width = max(self.winfo_width(), 2)
        height = max(self.winfo_height(), 2)
        fill = SURFACE_ALT if self._hover and self._enabled else FIELD
        outline = self._accent if self._hover and self._enabled else LINE
        draw_round(self, 1, 1, width - 1, height - 1, 6, fill, outline)
        image_area = self._width - 18
        self.create_image(width / 2, 8 + image_area / 2, image=self._photo)
        label_color = TEXT_BRIGHT if self._enabled else MUTED
        self.create_text(width / 2, height - 15, text=f"第 {self.item.iteration} 次",
                         fill=label_color, font=ui_font(8, "bold"))

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
        if not self._enabled:
            return
        if 0 <= event.x <= self.winfo_width() and 0 <= event.y <= self.winfo_height():
            if self._command:
                self._command(self.item)

    def set_enabled(self, enabled):
        self._enabled = bool(enabled)
        if not self._enabled:
            self._hover = False
            self.configure(cursor="")
        self._draw()


class _ScrollBar(tk.Canvas):
    """A slim, dark scrollbar that matches the canvas surfaces."""

    def __init__(self, master, command, width=7, outer_bg=SURFACE):
        super().__init__(master, bg=outer_bg, width=width, highlightthickness=0,
                         bd=0, takefocus=0)
        self._command = command
        self._first = 0.0
        self._last = 1.0
        self.bind("<Configure>", lambda _event: self._draw())
        self.bind("<Button-1>", self._jump)
        self.bind("<B1-Motion>", self._jump)
        self._draw()

    def set(self, first, last):
        self._first = float(first)
        self._last = float(last)
        self._draw()

    def _draw(self):
        self.delete("all")
        if self._last - self._first >= 0.999:
            return
        width = max(self.winfo_width(), 2)
        height = max(self.winfo_height(), 2)
        draw_round(self, 2, 2, width - 2, height - 2, (width - 4) / 2, LINE)
        top = 2 + (height - 4) * self._first
        bottom = 2 + (height - 4) * self._last
        if bottom - top < 8:
            bottom = min(height - 2, top + 8)
        draw_round(self, 2, top, width - 2, bottom, (width - 4) / 2, MUTED)

    def _jump(self, event):
        height = max(self.winfo_height(), 2)
        fraction = min(1.0, max(0.0, (event.y - 2) / max(1, height - 4)))
        self._command("moveto", str(fraction))


class ResultPane(tk.Frame):
    """Header plus a wheel-scrollable grid of result thumbnails."""

    PAD = 8
    GAP = 8
    SCROLLBAR_GUTTER = 12
    TILE_WIDTH = 120
    TILE_HEIGHT = 146

    def __init__(self, master, title="结果集", direction="reverse", on_open=None):
        super().__init__(master, bg=SURFACE)
        self._on_open = on_open
        self._direction = direction
        self._accent = INK if direction == "reverse" else ROSE
        self._tiles: list[ResultTile] = []
        self._columns = 0
        self._enabled = True
        self._placeholder_title = "还没有结果"
        self._placeholder_subtitle = "生成后会显示在这里"
        self._show_placeholder = True

        header = tk.Frame(self, bg=SURFACE)
        header.pack(fill="x")
        self._dot = tk.Canvas(header, width=7, height=7, bg=SURFACE,
                              highlightthickness=0, bd=0)
        self._dot.pack(side="left", padx=(2, 6), pady=(5, 0))
        self._dot_item = self._dot.create_oval(1, 1, 6, 6, fill=self._accent,
                                               outline="")
        self._title = make_label(header, title, 9, "bold")
        self._title.pack(side="left")
        self._meta = make_label(header, "", 8, fg=FAINT)
        self._meta.pack(side="right")

        body = tk.Frame(self, bg=SURFACE)
        body.pack(fill="both", expand=True, pady=(8, 0))
        self._canvas = tk.Canvas(body, bg=SURFACE, highlightthickness=0, bd=0,
                                 yscrollincrement=24)
        self._canvas.pack(side="left", fill="both", expand=True)
        # The scrollbar floats inside the result well so the solid border keeps
        # the same outer bounds as the dashed input well.
        self._scrollbar = _ScrollBar(body, command=self._scroll_to,
                                     outer_bg=FIELD)
        self._scrollbar.place(relx=1.0, x=-6, y=6, anchor="ne",
                              relheight=1.0, height=-12)
        self._scrollbar.bind("<MouseWheel>", self._on_wheel)
        self._inner = tk.Frame(self._canvas, bg=FIELD)
        self._window = self._canvas.create_window(self.PAD, self.PAD,
                                                  anchor="nw", window=self._inner)
        self._canvas.configure(yscrollcommand=self._scrollbar.set)
        self._canvas.bind("<Configure>", self._on_configure)
        self._canvas.bind("<MouseWheel>", self._on_wheel)
        self._inner.bind("<MouseWheel>", self._on_wheel)

    # ---------------------------------------------------------------- public
    def set_direction(self, direction, title=None):
        self._direction = direction
        self._accent = INK if direction == "reverse" else ROSE
        self._dot.itemconfigure(self._dot_item, fill=self._accent)
        if title is not None:
            self.set_title(title)

    def set_neutral_title(self, title="结果集"):
        """Show a direction-neutral heading before a batch is started."""
        self._direction = None
        self._accent = FAINT
        self._dot.itemconfigure(self._dot_item, fill=self._accent)
        self.set_title(title)

    def set_title(self, title):
        self._title.configure(text=title)

    def set_meta(self, text):
        self._meta.configure(text=text)

    def set_placeholder(self, title, subtitle):
        self._placeholder_title = title
        self._placeholder_subtitle = subtitle
        self._show_placeholder = not self._tiles
        self._draw_background()
        self._update_scrollregion()

    def clear(self):
        for tile in self._tiles:
            tile.destroy()
        self._tiles.clear()
        self._columns = 0
        self._show_placeholder = True
        self._canvas.yview_moveto(0)
        self._draw_background()
        self._update_scrollregion()

    def append_item(self, item: BatchItem):
        self._show_placeholder = False
        tile = ResultTile(self._inner, item, command=self._open_item,
                          width=self.TILE_WIDTH, height=self.TILE_HEIGHT,
                          accent=self._accent, outer_bg=FIELD)
        tile.bind("<MouseWheel>", self._on_wheel)
        self._tiles.append(tile)
        columns = self._columns or self._current_columns()
        self._columns = columns
        index = len(self._tiles) - 1
        self._grid_tile(tile, index, columns)
        tile.set_enabled(self._enabled)
        self._draw_background()
        self._update_scrollregion()

    def set_enabled(self, enabled):
        self._enabled = bool(enabled)
        for tile in self._tiles:
            tile.set_enabled(self._enabled)

    @property
    def count(self):
        return len(self._tiles)

    # --------------------------------------------------------------- layout
    def _available_width(self):
        width = max(self._canvas.winfo_width(),
                    self.TILE_WIDTH + self.PAD * 2 + self.SCROLLBAR_GUTTER)
        return width - self.PAD * 2 - self.SCROLLBAR_GUTTER

    def _current_columns(self):
        available = self._available_width()
        return max(1, (available + self.GAP) // (self.TILE_WIDTH + self.GAP))

    def _on_configure(self, _event=None):
        width = max(self._canvas.winfo_width(), 10)
        height = max(self._canvas.winfo_height(), 10)
        inner_width = max(1, width - self.PAD * 2 - self.SCROLLBAR_GUTTER)
        self._canvas.itemconfigure(self._window, width=inner_width)
        self._canvas.coords(self._window, self.PAD, self.PAD)
        columns = self._current_columns()
        if columns != self._columns:
            self._columns = columns
            self._layout_tiles()
        self._draw_background()
        self._update_scrollregion()

    def _layout_tiles(self):
        if not self._columns:
            return
        for index, tile in enumerate(self._tiles):
            self._grid_tile(tile, index, self._columns)

    def _grid_tile(self, tile, index, columns):
        column = index % columns
        right_pad = self.GAP if column < columns - 1 else 0
        tile.grid(row=index // columns, column=column,
                  padx=(0, right_pad), pady=(0, self.GAP), sticky="nw")

    def _update_scrollregion(self):
        width = max(self._canvas.winfo_width(), 10)
        height = max(self._canvas.winfo_height(), 10)
        rows = math.ceil(len(self._tiles) / self._columns) if self._columns else 0
        content = self.PAD * 2
        if rows:
            content += rows * self.TILE_HEIGHT + max(0, rows - 1) * self.GAP
        self._canvas.configure(scrollregion=(0, 0, width, max(content, height)))

    def _draw_background(self):
        canvas = self._canvas
        width = max(canvas.winfo_width(), 2)
        height = max(canvas.winfo_height(), 2)
        canvas.delete("bg")
        draw_round(canvas, 2, 2, width - 2, height - 2, 6, FIELD, LINE, tags="bg")
        canvas.tag_lower("bg")
        canvas.delete("placeholder")
        if self._show_placeholder and not self._tiles:
            center = height * 0.46
            draw_round(canvas, width / 2 - 18, center - 44, width / 2 + 18,
                       center - 8, 7, SURFACE_ALT, LINE, tags="placeholder")
            canvas.create_image(width / 2, center - 26,
                                image=icon_photo("sparkles", MUTED, 16),
                                tags="placeholder")
            canvas.create_text(width / 2, center + 8,
                               text=self._placeholder_title, fill=TEXT,
                               font=ui_font(9, "bold"), tags="placeholder")
            canvas.create_text(width / 2, center + 26,
                               text=self._placeholder_subtitle, fill=MUTED,
                               font=ui_font(8), tags="placeholder")
        canvas.tag_raise(self._window)

    def _on_wheel(self, event):
        units = -1 if event.delta > 0 else 1
        self._canvas.yview_scroll(units, "units")
        return "break"

    def _scroll_to(self, *args):
        self._canvas.yview(*args)

    def _open_item(self, item):
        if self._enabled and self._on_open:
            self._on_open(item)


__all__ = ["ResultPane", "ResultTile"]

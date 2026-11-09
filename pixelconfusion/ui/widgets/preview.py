"""Preview wells and the dashed source drop zone."""

from __future__ import annotations

import tkinter as tk

from pixelconfusion.ui.drawing import dashed_round, draw_round
from pixelconfusion.ui.images import icon_photo, preview_photo
from pixelconfusion.ui.text import format_dimensions
from pixelconfusion.ui.theme import (
    ACCENT_LIGHT,
    FAINT,
    FIELD,
    INK,
    LINE,
    LINE_STRONG,
    MUTED,
    SURFACE,
    SURFACE_ALT,
    TEXT,
    parent_background,
    ui_font,
)


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
        dot = tk.Canvas(header, width=7, height=7, bg=SURFACE, highlightthickness=0,
                        bd=0)
        dot.pack(side="left", padx=(2, 6), pady=(5, 0))
        if kind == "input":
            dot.create_oval(1, 1, 6, 6, fill=FAINT, outline="")
        else:
            dot.create_oval(1, 1, 6, 6, fill=INK, outline="")
        tk.Label(header, text=title, bg=SURFACE, fg=TEXT,
                 font=ui_font(9, "bold")).pack(side="left")
        self._dims = tk.Label(header, text="— × —", bg=SURFACE, fg=FAINT,
                              font=ui_font(8))
        self._dims.pack(side="right")
        self._well = tk.Canvas(self, bg=SURFACE, highlightthickness=0, bd=0)
        self._well.pack(fill="both", expand=True, pady=(8, 0))
        self._well.bind("<Configure>", self._schedule)
        self._well.bind("<ButtonRelease-1>", self._click)
        self._pick_area: tuple[float, float, float, float] | None = None

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
            self.set_dims(format_dimensions(image.width, image.height))
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
        draw_round(canvas, width / 2 - 18, center - 44, width / 2 + 18, center - 8,
                   7, SURFACE_ALT, LINE)
        canvas.create_image(width / 2, center - 26,
                            image=icon_photo(self._empty_icon, MUTED, 16))
        canvas.create_text(width / 2, center + 8, text=self._empty_title, fill=TEXT,
                           font=ui_font(9, "bold"))
        canvas.create_text(width / 2, center + 26, text=self._empty_subtitle,
                           fill=MUTED, font=ui_font(8))
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
                          start=start + 150, extent=70, style="arc",
                          outline=ACCENT_LIGHT, width=2)
        canvas.create_text(center_x, center_y + 38, text=self._busy_title, fill=TEXT,
                           font=ui_font(9, "bold"))
        canvas.create_text(center_x, center_y + 55,
                           text=f"{round(self._busy_fraction * 100)}%",
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
    def __init__(self, master, command=None, height=108, outer_bg=None,
                 compact=False):
        super().__init__(master, bg=outer_bg or parent_background(master),
                         highlightthickness=0, bd=0, height=height, takefocus=0)
        self.command = command
        self._hover = False
        self._enabled = True
        self._compact = compact
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
        if self._compact:
            self._draw_compact(width, height)
            return
        center = height / 2
        draw_round(self, width / 2 - 14, center - 33, width / 2 + 14, center - 5,
                   6, SURFACE_ALT, LINE)
        self.create_image(width / 2, center - 19,
                          image=icon_photo("image", MUTED if self._enabled else FAINT, 14))
        self.create_text(width / 2, center + 10, text="选择一张图片",
                         fill=TEXT if self._enabled else MUTED,
                         font=ui_font(9, "bold"))
        self.create_text(width / 2, center + 27, text="PNG / JPG / WEBP / BMP · 单帧",
                         fill=FAINT, font=ui_font(7))

    def _draw_compact(self, width, height):
        main_font = ui_font(9, "bold")
        sub_font = ui_font(8)
        main_text = "选择一张图片"
        sub_text = "PNG / JPG / WEBP / BMP · 单帧"
        icon_width = 14
        gap = 7
        sub_gap = 9
        total = (icon_width + gap + main_font.measure(main_text)
                 + sub_gap + sub_font.measure(sub_text))
        start = max(12, (width - total) / 2)
        center = height / 2
        self.create_image(start + icon_width / 2, center,
                          image=icon_photo("image",
                                           MUTED if self._enabled else FAINT, 14))
        main_x = start + icon_width + gap
        self.create_text(main_x, center, text=main_text,
                         fill=TEXT if self._enabled else MUTED,
                         font=main_font, anchor="w")
        self.create_text(main_x + main_font.measure(main_text) + sub_gap, center,
                         text=sub_text, fill=FAINT, font=sub_font, anchor="w")

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
        if (self._enabled and 0 <= event.x <= self.winfo_width()
                and 0 <= event.y <= self.winfo_height()):
            if self.command:
                self.command()

    def set_enabled(self, enabled):
        self._enabled = enabled
        self._draw()


__all__ = ["DropZone", "PreviewTile"]

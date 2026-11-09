"""Modal large preview for one batch result."""

from __future__ import annotations

import tkinter as tk

from PIL import Image

from pixelconfusion.ui.drawing import draw_round
from pixelconfusion.ui.images import preview_photo
from pixelconfusion.ui.text import make_label
from pixelconfusion.ui.theme import (
    BG,
    FIELD,
    INK,
    LINE,
    MUTED,
    RED,
    ROSE,
    SURFACE,
    SURFACE_ALT,
    TEXT_BRIGHT,
    ui_font,
)
from pixelconfusion.ui.widgets import IconButton, PillButton
from pixelconfusion.ui.window import apply_dark_title_bar


class ResultPreview(tk.Toplevel):
    """Shows one full-size result and exposes use/save actions."""

    def __init__(
        self,
        master,
        *,
        direction: str,
        iteration: int,
        batch_text: str,
        thumbnail: Image.Image,
        dims_text: str,
        on_use,
        on_save,
        on_close=None,
    ):
        super().__init__(master, bg=BG)
        self._direction = direction
        self._iteration = iteration
        self._thumbnail = thumbnail
        self._on_use = on_use
        self._on_save = on_save
        self._on_close = on_close
        self._image: Image.Image | None = None
        self._photo = None
        self._loading_text = "正在生成原尺寸预览…"
        self._error = ""
        self._closing = False

        self.title("PixelConfusion · 结果预览")
        self.transient(master)
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.bind("<Escape>", lambda _event: self.close())
        self._place_over_master(master)

        accent = INK if direction == "reverse" else ROSE
        direction_label = "反向结果" if direction == "reverse" else "正向结果"

        header = tk.Frame(self, bg=SURFACE, height=64)
        header.pack(side="top", fill="x")
        header.pack_propagate(False)
        tk.Frame(header, bg=LINE, height=1).place(relx=0, rely=1, anchor="sw",
                                                 relwidth=1)
        title_block = tk.Frame(header, bg=SURFACE)
        title_block.pack(side="left", padx=(18, 0), pady=10)
        title_row = tk.Frame(title_block, bg=SURFACE)
        title_row.pack(anchor="w")
        dot = tk.Canvas(title_row, width=7, height=7, bg=SURFACE,
                        highlightthickness=0, bd=0)
        dot.pack(side="left", padx=(0, 8), pady=(5, 0))
        dot.create_oval(1, 1, 6, 6, fill=accent, outline="")
        make_label(title_row, f"{direction_label} · 第 {iteration} 次", 10, "bold",
                   TEXT_BRIGHT).pack(side="left")
        make_label(title_block, f"{batch_text} · {dims_text}", 8, fg=MUTED).pack(
            anchor="w", pady=(3, 0))
        IconButton(header, "x", command=self.close, size=30, icon_size=15,
                   tooltip="关闭预览", outer_bg=SURFACE).pack(
            side="right", padx=(0, 14), pady=17)

        footer = tk.Frame(self, bg=SURFACE, height=60)
        footer.pack(side="bottom", fill="x")
        footer.pack_propagate(False)
        tk.Frame(footer, bg=LINE, height=1).place(relx=0, rely=0, anchor="nw",
                                                 relwidth=1)
        self._status = make_label(footer, self._loading_text, 8, fg=MUTED)
        self._status.place(x=18, rely=0.5, anchor="w")
        actions = tk.Frame(footer, bg=SURFACE)
        actions.place(relx=1.0, x=-18, rely=0.5, anchor="e")
        self.use_button = PillButton(actions, "用作输入", command=self._use,
                                     icon="corner", kind="secondary", small=True,
                                     height=32, outer_bg=SURFACE)
        self.use_button.pack(side="left")
        self.save_button = PillButton(actions, "保存 PNG", command=self._save,
                                      icon="download", kind="primary", small=True,
                                      height=32, outer_bg=SURFACE)
        self.save_button.pack(side="left", padx=(8, 0))
        self.set_actions_enabled(False)

        self._canvas = tk.Canvas(self, bg=BG, highlightthickness=0, bd=0)
        self._canvas.pack(fill="both", expand=True, padx=14, pady=14)
        self._canvas.bind("<Configure>", lambda _event: self._draw())
        self._draw()
        self.update_idletasks()
        try:
            self.grab_set()
        except tk.TclError:
            pass
        try:
            apply_dark_title_bar(self)
        except tk.TclError:
            pass

    # ------------------------------------------------------------- geometry
    def _place_over_master(self, master):
        self.update_idletasks()
        width = min(1040, max(720, int(self.winfo_screenwidth() * 0.74)))
        height = min(820, max(560, int(self.winfo_screenheight() * 0.78)))
        self.geometry(f"{width}x{height}")
        self.minsize(720, 560)
        try:
            master.update_idletasks()
            x = master.winfo_rootx() + max(0, (master.winfo_width() - width) // 2)
            y = master.winfo_rooty() + max(0, (master.winfo_height() - height) // 2)
        except tk.TclError:
            x = y = 0
        self.geometry(f"+{max(0, x)}+{max(0, y)}")

    # --------------------------------------------------------------- public
    def set_image(self, image: Image.Image):
        self._image = image
        self._error = ""
        self._loading_text = ""
        self._status.configure(text=f"原图已就绪 · {image.width} × {image.height}",
                               fg=MUTED)
        self.set_actions_enabled(True)
        self._draw()

    def set_error(self, message: str):
        self._error = message
        self._loading_text = ""
        self._status.configure(text=message, fg=RED)
        self.set_actions_enabled(False)
        self._draw()

    def set_status(self, text: str, tone: str = "idle"):
        colors = {"idle": MUTED, "ok": "#6ea4ff", "busy": "#f2bd45",
                  "error": RED}
        self._status.configure(text=text, fg=colors.get(tone, MUTED))

    def set_actions_enabled(self, enabled: bool):
        enabled = bool(enabled and self._image is not None)
        self.use_button.set_enabled(enabled)
        self.save_button.set_enabled(enabled)

    @property
    def image(self):
        return self._image

    def close(self):
        if self._closing:
            return
        self._closing = True
        try:
            self.grab_release()
        except tk.TclError:
            pass
        callback = self._on_close
        self._on_close = None
        try:
            self.destroy()
        finally:
            if callback:
                callback()

    # -------------------------------------------------------------- drawing
    def _draw(self):
        canvas = self._canvas
        canvas.delete("all")
        width = max(canvas.winfo_width(), 2)
        height = max(canvas.winfo_height(), 2)
        draw_round(canvas, 2, 2, width - 2, height - 2, 8, FIELD, LINE)
        source = self._image if self._image is not None else self._thumbnail
        if source is not None:
            self._photo = preview_photo(source, width - 48, height - 48)
            canvas.create_image(width / 2, height / 2, image=self._photo)
        if self._error:
            center = height - 34
            draw_round(canvas, width / 2 - 150, center - 15, width / 2 + 150,
                       center + 15, 6, SURFACE_ALT, LINE)
            canvas.create_text(width / 2, center, text=self._error, fill=RED,
                               font=ui_font(8))
        elif self._image is None:
            center = height - 34
            draw_round(canvas, width / 2 - 130, center - 15, width / 2 + 130,
                       center + 15, 6, SURFACE_ALT, LINE)
            canvas.create_text(width / 2, center, text=self._loading_text,
                               fill=MUTED, font=ui_font(8))

    # -------------------------------------------------------------- actions
    def _use(self):
        if self._image is None:
            return
        callback = self._on_use
        image = self._image
        if callback:
            callback(image)
        self.close()

    def _save(self):
        if self._image is None:
            return
        if self._on_save:
            self._on_save(self._image)


__all__ = ["ResultPreview"]

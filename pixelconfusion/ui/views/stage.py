"""Preview stage: header, input/output tiles and status footer."""

from __future__ import annotations

import tkinter as tk

from pixelconfusion.ui.images import icon_photo
from pixelconfusion.ui.text import ellipsize, make_label
from pixelconfusion.ui.theme import BG, FAINT, LINE, MUTED, PINK, RED, SURFACE
from pixelconfusion.ui.widgets import (
    Card,
    PillButton,
    PreviewTile,
    ProgressBar,
)


class StageView(Card):
    def __init__(self, master, *, on_pick, on_use_result, on_save, outer_bg=BG):
        super().__init__(master, height=560, outer_bg=outer_bg)
        inner = tk.Frame(self.content, bg=SURFACE)
        inner.pack(fill="both", expand=True)

        head = tk.Frame(inner, bg=SURFACE, height=54)
        head.pack(side="top", fill="x")
        head.pack_propagate(False)
        head_left = tk.Frame(head, bg=SURFACE)
        head_left.pack(side="left", padx=(6, 0), pady=17)
        make_label(head_left, "预览", 9, "bold").pack(side="left")
        hint = tk.Frame(head, bg=SURFACE)
        hint.pack(side="right", padx=(0, 6), pady=19)
        tk.Label(hint, image=icon_photo("info", FAINT, 12), bg=SURFACE,
                 bd=0).pack(side="left")
        make_label(hint, "自动适配预览 · 输出保留原始尺寸", 8,
                   fg=FAINT).pack(side="left", padx=(5, 0))

        footer_wrap = tk.Frame(inner, bg=SURFACE)
        footer_wrap.pack(side="bottom", fill="x")
        tk.Frame(footer_wrap, bg=LINE, height=1).pack(fill="x")
        footer = tk.Frame(footer_wrap, bg=SURFACE, height=56)
        footer.pack(fill="x")
        footer.pack_propagate(False)
        left_group = tk.Frame(footer, bg=SURFACE)
        left_group.place(x=12, rely=0.5, anchor="w")
        self.status_dot = tk.Canvas(left_group, width=7, height=7, bg=SURFACE,
                                    highlightthickness=0, bd=0)
        self.status_dot.pack(side="left", padx=(0, 7))
        self.status_dot.create_oval(0, 0, 6, 6, fill=FAINT, outline="", tags="dot")
        self.status_label = make_label(left_group, "", 8, fg=MUTED, anchor="w")
        self.status_label.pack(side="left")
        self.progress = ProgressBar(left_group, width=68, height=3,
                                    outer_bg=SURFACE)
        self.progress.pack(side="left", padx=(10, 0))
        make_label(left_group, "本机", 7, fg=FAINT).pack(side="left", padx=(8, 0))
        actions = tk.Frame(footer, bg=SURFACE)
        actions.place(relx=1.0, x=-12, rely=0.5, anchor="e")
        self.use_button = PillButton(actions, "用作输入", command=on_use_result,
                                     icon="corner", kind="secondary", small=True,
                                     height=30, outer_bg=SURFACE)
        self.use_button.pack(side="left")
        self.save_button = PillButton(actions, "保存 PNG", command=on_save,
                                      icon="download", kind="primary", small=True,
                                      height=30, outer_bg=SURFACE)
        self.save_button.pack(side="left", padx=(7, 0))

        body = tk.Frame(inner, bg=SURFACE)
        body.pack(fill="both", expand=True, padx=4, pady=(8, 8))
        body.grid_rowconfigure(0, weight=1)
        body.grid_columnconfigure(0, weight=1, uniform="preview")
        body.grid_columnconfigure(1, weight=1, uniform="preview")
        self.input_tile = PreviewTile(body, "输入", "input", on_pick=on_pick)
        self.input_tile.grid(row=0, column=0, sticky="nsew")
        self.output_tile = PreviewTile(body, "结果", "output")
        self.output_tile.grid(row=0, column=1, sticky="nsew", padx=(13, 0))

    def set_status(self, text: str, tone: str = "idle") -> None:
        colors = {"idle": FAINT, "ok": "#4d8df7", "busy": PINK, "error": RED}
        self.status_dot.itemconfigure("dot", fill=colors.get(tone, colors["idle"]))
        self.status_label.configure(text=ellipsize(text, 248, 8),
                                    fg=RED if tone == "error" else MUTED)

    def set_progress(self, value: float) -> None:
        self.progress.set(value)

    def begin_busy(self, label: str) -> None:
        self.output_tile.set_busy(f"正在{label}", 0)
        self.progress.set(0)

    def update_busy_progress(self, fraction: float) -> None:
        self.output_tile.set_busy_progress(fraction)

    def set_source_empty(self) -> None:
        self.input_tile.set_empty("还没有输入图片", "选择图片或使用内置测试图", "image",
                                  pickable=True)
        self.input_tile.set_dims("— × —")

    def set_source_image(self, image) -> None:
        self.input_tile.set_image(image)

    def reset_result(self) -> None:
        self.output_tile.set_empty("结果会出现在这里", "点击正向混淆或反向混淆开始处理", "sparkles")
        self.output_tile.set_dims("— × —")
        self.progress.set(0)

    def show_result(self, image) -> None:
        self.output_tile.set_image(image)

    def set_actions_enabled(self, has_result: bool, busy: bool) -> None:
        enabled = has_result and not busy
        self.use_button.set_enabled(enabled)
        self.save_button.set_enabled(enabled)


__all__ = ["StageView"]

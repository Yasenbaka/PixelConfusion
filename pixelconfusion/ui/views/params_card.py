"""Algorithm selector and parameter card."""

from __future__ import annotations

import tkinter as tk

from pixelconfusion.parameters import MAX_ITERATIONS
from pixelconfusion.ui.text import make_label
from pixelconfusion.ui.theme import BG, FAINT, MUTED, PINK, SURFACE
from pixelconfusion.ui.widgets import (
    Card,
    HintBox,
    NumberStepper,
    Segmented,
    TextField,
)


class ParamsCard(Card):
    def __init__(self, master, *, on_method_change, outer_bg=BG):
        super().__init__(master, height=360, outer_bg=outer_bg)
        self.iterations_var = tk.StringVar(value="1")
        self.offset_var = tk.StringVar(value="")
        self.param_a_var = tk.StringVar(value="1")
        self.param_b_var = tk.StringVar(value="1")

        body = tk.Frame(self.content, bg=SURFACE)
        body.pack(fill="both", expand=True, padx=10, pady=6)
        header = tk.Frame(body, bg=SURFACE, height=16)
        header.pack(fill="x")
        header.pack_propagate(False)
        make_label(header, "算法与参数", 9, "bold").pack(side="left")

        self.segmented = Segmented(body, "gilbert", on_change=on_method_change,
                                   outer_bg=SURFACE)
        self.segmented.pack(fill="x", pady=(12, 0))
        self.method_desc = make_label(body, "", 8, fg=MUTED, anchor="w")
        self.method_desc.pack(fill="x", pady=(8, 0))
        make_label(body, "迭代次数", 8, fg=MUTED).pack(anchor="w", pady=(12, 0))
        self.stepper = NumberStepper(body, self.iterations_var, 1, MAX_ITERATIONS,
                                     outer_bg=SURFACE)
        self.stepper.pack(fill="x", pady=(4, 0))

        self.param_block = tk.Frame(body, bg=SURFACE, height=60)
        self.param_block.pack(fill="x", pady=(12, 0))
        self.param_block.pack_propagate(False)
        self.offset_frame = tk.Frame(self.param_block, bg=SURFACE)
        self.offset_frame.place(x=0, y=0, relwidth=1, height=54)
        offset_head = tk.Frame(self.offset_frame, bg=SURFACE, height=14)
        offset_head.pack(fill="x")
        offset_head.pack_propagate(False)
        make_label(offset_head, "偏移量", 8, fg=MUTED).pack(side="left")
        make_label(offset_head, "留空自动", 7, fg=FAINT).pack(side="right")
        self.offset_field = TextField(self.offset_frame, self.offset_var, "黄金比",
                                      height=36, outer_bg=SURFACE)
        self.offset_field.pack(fill="x", pady=(4, 0))

        self.ab_frame = tk.Frame(self.param_block, bg=SURFACE)
        self.ab_frame.grid_columnconfigure(0, weight=1, uniform="ab")
        self.ab_frame.grid_columnconfigure(1, weight=1, uniform="ab")
        for column, (title, variable) in enumerate(
            (("参数 a", self.param_a_var), ("参数 b", self.param_b_var))
        ):
            field_wrap = tk.Frame(self.ab_frame, bg=SURFACE)
            field_wrap.grid(row=0, column=column, sticky="ew", padx=(4, 4))
            make_label(field_wrap, title, 8, fg=MUTED).pack(anchor="w")
            field = TextField(field_wrap, variable, "", height=36, outer_bg=SURFACE)
            field.pack(fill="x", pady=(4, 0))
            if column == 0:
                self.a_field = field
            else:
                self.b_field = field

        self.hint = HintBox(body, height=58, outer_bg=SURFACE)
        self.hint.pack(fill="x", pady=(12, 12))

        self.show_method("gilbert", None)

    def parameter_text(self) -> tuple[str, str, str, str]:
        """Return the raw field values in validation order."""
        return (
            self.iterations_var.get(),
            self.offset_var.get(),
            self.param_a_var.get(),
            self.param_b_var.get(),
        )

    def set_method(self, method: str) -> None:
        if self.segmented.value != method:
            self.segmented.set(method)

    def show_method(self, method: str, source_image) -> None:
        gilbert = method == "gilbert"
        if gilbert:
            self.method_desc.configure(text="广义希尔伯特曲线 · 支持任意宽高",
                                       fg=MUTED)
            self.hint.set_text("复原时请保持次数与偏移量一致；留空自动使用默认黄金比例偏移。")
            self.ab_frame.place_forget()
            self.offset_frame.place(x=0, y=0, relwidth=1, height=60)
        else:
            bad_size = (source_image is not None
                        and source_image.width != source_image.height)
            self.method_desc.configure(
                text="标准猫映射 · 仅支持正方形图片",
                fg=PINK if bad_size else MUTED,
            )
            self.hint.set_text("复原时请保持次数、a、b 一致；坐标变换仅在正方形图片上成立。")
            self.offset_frame.place_forget()
            self.ab_frame.place(x=0, y=0, relwidth=1, height=60)

    def set_enabled(self, enabled: bool) -> None:
        self.segmented.set_enabled(enabled)
        self.stepper.set_enabled(enabled)
        self.offset_field.set_enabled(enabled)
        self.a_field.set_enabled(enabled)
        self.b_field.set_enabled(enabled)


__all__ = ["ParamsCard"]

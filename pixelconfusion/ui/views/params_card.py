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
        self._mode = "single"
        self._method = "gilbert"
        self._source_image = None
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

        self.iterations_block = tk.Frame(body, bg=SURFACE)
        self.iterations_block.pack(fill="x", pady=(12, 0))
        make_label(self.iterations_block, "迭代次数", 8, fg=MUTED).pack(anchor="w")
        self.stepper = NumberStepper(self.iterations_block, self.iterations_var,
                                     1, MAX_ITERATIONS, outer_bg=SURFACE)
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

        self.hint = HintBox(body, height=40, outer_bg=SURFACE)
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

    def set_mode(self, mode: str) -> None:
        """Hide the single-run iteration field while batch mode is active."""
        self._mode = mode
        if mode == "batch":
            self.iterations_block.pack_forget()
            self.configure(height=270)
        else:
            if not self.iterations_block.winfo_manager():
                self.iterations_block.pack(fill="x", pady=(12, 0),
                                           before=self.param_block)
            self.configure(height=342)
        self.show_method(self._method, self._source_image)

    def show_method(self, method: str, source_image) -> None:
        self._method = method
        self._source_image = source_image
        gilbert = method == "gilbert"
        if gilbert:
            self.method_desc.configure(text="广义希尔伯特曲线 · 支持任意宽高",
                                       fg=MUTED)
            if self._mode == "batch":
                text = "批量次数由下方“等差迭代次数”控制。"
            else:
                text = "默认使用黄金比例偏移。"
            self.hint.set_text(text)
            self.ab_frame.place_forget()
            self.offset_frame.place(x=0, y=0, relwidth=1, height=60)
        else:
            bad_size = (source_image is not None
                        and source_image.width != source_image.height)
            self.method_desc.configure(
                text="标准猫映射 · 仅支持正方形图片",
                fg=PINK if bad_size else MUTED,
            )
            if self._mode == "batch":
                text = "批量次数由下方控制；仅支持正方形图片。"
            else:
                text = "仅支持正方形图片。"
            self.hint.set_text(text)
            self.offset_frame.place_forget()
            self.ab_frame.place(x=0, y=0, relwidth=1, height=60)

    def set_enabled(self, enabled: bool) -> None:
        self.segmented.set_enabled(enabled)
        self.stepper.set_enabled(enabled)
        self.offset_field.set_enabled(enabled)
        self.a_field.set_enabled(enabled)
        self.b_field.set_enabled(enabled)


__all__ = ["ParamsCard"]

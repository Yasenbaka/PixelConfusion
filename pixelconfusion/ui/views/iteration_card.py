"""Single-run versus multi-iteration mode selector."""

from __future__ import annotations

import tkinter as tk

from pixelconfusion.parameters import DEFAULT_BATCH_COUNT, MAX_BATCH_COUNT
from pixelconfusion.ui.text import make_label
from pixelconfusion.ui.theme import BG, FAINT, MUTED, SURFACE
from pixelconfusion.ui.widgets import (
    Card,
    NumberStepper,
    PillButton,
    Segmented,
    ToggleSwitch,
)


class IterationCard(Card):
    OPTIONS = (
        ("single", "单次", "rotate"),
        ("batch", "多次", "grid"),
    )
    HEIGHT_SINGLE = 128
    HEIGHT_BATCH = 276
    HEIGHT_BATCH_AUTO = 210

    def __init__(self, master, *, on_mode_change, on_auto_change, on_next_batch,
                 outer_bg=BG):
        super().__init__(master, height=self.HEIGHT_SINGLE, outer_bg=outer_bg)
        self.count_var = tk.StringVar(value=str(DEFAULT_BATCH_COUNT))
        self._mode = "single"
        self._auto = False
        self._enabled = True
        self._next_allowed = False
        self._next_visible = False
        self._on_next_batch = on_next_batch

        body = tk.Frame(self.content, bg=SURFACE)
        body.pack(fill="both", expand=True, padx=10, pady=6)
        header = tk.Frame(body, bg=SURFACE, height=16)
        header.pack(fill="x")
        header.pack_propagate(False)
        make_label(header, "迭代方式", 9, "bold").pack(side="left")

        self.segmented = Segmented(body, "single", options=self.OPTIONS,
                                   on_change=on_mode_change, height=36,
                                   outer_bg=SURFACE)
        self.segmented.pack(fill="x", pady=(12, 0))
        self.single_hint = make_label(
            body, "保持当前的单张处理流程。", 7, fg=FAINT, anchor="w")
        self.single_hint.pack(fill="x", pady=(8, 0))

        self.multi_block = tk.Frame(body, bg=SURFACE)
        make_label(self.multi_block, "从第 1 次开始，每批生成 N 张结果",
                   7, fg=FAINT, anchor="w").pack(fill="x")
        count_row = tk.Frame(self.multi_block, bg=SURFACE, height=36)
        count_row.pack(fill="x", pady=(8, 0))
        count_row.pack_propagate(False)
        make_label(count_row, "等差迭代次数", 8, fg=MUTED).pack(
            side="left", pady=(11, 0))
        make_label(count_row, f"1–{MAX_BATCH_COUNT}", 7, fg=FAINT).pack(
            side="right", pady=(11, 0))
        self.stepper = NumberStepper(count_row, self.count_var, 1,
                                     MAX_BATCH_COUNT, height=34,
                                     outer_bg=SURFACE)
        self.stepper.pack(side="right", fill="x", expand=True, padx=(10, 0))

        self.toggle = ToggleSwitch(self.multi_block, "正反自动混淆", value=False,
                                   on_change=on_auto_change, height=30,
                                   outer_bg=SURFACE)
        self.toggle.pack(fill="x", pady=(6, 0))

        self.next_row = tk.Frame(self.multi_block, bg=SURFACE)
        self.next_button = PillButton(self.next_row, "下一批",
                                      icon="arrow-right", kind="primary",
                                      height=38, command=self._next_clicked,
                                      outer_bg=SURFACE)
        self.next_button.pack(fill="x")
        self.next_button.set_enabled(False)
        self.next_meta = make_label(self.next_row, "", 7, fg=FAINT, anchor="w")
        self.next_meta.pack(fill="x", pady=(6, 0))
        self.set_mode("single")

    # ---------------------------------------------------------------- public
    @property
    def mode(self):
        return self._mode

    @property
    def auto_mixed(self):
        return self._auto

    def set_mode(self, mode: str):
        self._mode = mode
        if self.segmented.value != mode:
            self.segmented.set(mode)
        if mode == "batch":
            self.single_hint.pack_forget()
            if not self.multi_block.winfo_manager():
                self.multi_block.pack(fill="x", pady=(10, 0))
            self.configure(height=(self.HEIGHT_BATCH_AUTO if self._auto
                                   else self.HEIGHT_BATCH))
        else:
            self.multi_block.pack_forget()
            if not self.single_hint.winfo_manager():
                self.single_hint.pack(fill="x", pady=(8, 0))
            self.configure(height=self.HEIGHT_SINGLE)

    def set_auto(self, value: bool):
        self._auto = bool(value)
        self.toggle.set_value(self._auto)
        if self._mode == "batch":
            self.configure(height=(self.HEIGHT_BATCH_AUTO if self._auto
                                   else self.HEIGHT_BATCH))
        if self._auto:
            self.next_row.pack_forget()
            self._next_visible = False
        else:
            self._next_visible = True
            if not self.next_row.winfo_manager():
                self.next_row.pack(fill="x", pady=(8, 0))
        self._apply_next_state()

    def set_batch_state(self, index: int, start: int, count: int,
                        has_results: bool, can_next: bool, auto: bool):
        self._auto = bool(auto)
        if self._mode == "batch":
            self.configure(height=(self.HEIGHT_BATCH_AUTO if self._auto
                                   else self.HEIGHT_BATCH))
        if auto:
            self.next_row.pack_forget()
            self._next_visible = False
            self._next_allowed = False
            self._apply_next_state()
            return
        self._next_visible = True
        if not self.next_row.winfo_manager():
            self.next_row.pack(fill="x", pady=(8, 0))
        self._next_allowed = bool(has_results and can_next)
        if has_results and can_next:
            next_start = start + count
            next_end = next_start + count - 1
            self.next_meta.configure(text=f"下一批 {next_start}–{next_end} 次")
        elif has_results:
            self.next_meta.configure(text="已达迭代上限")
        else:
            self.next_meta.configure(
                text=f"本批 {start}–{start + count - 1} 次")
        self._apply_next_state()

    def set_enabled(self, enabled: bool):
        self._enabled = bool(enabled)
        self.segmented.set_enabled(self._enabled)
        self.stepper.set_enabled(self._enabled)
        self.toggle.set_enabled(self._enabled)
        self._apply_next_state()

    # --------------------------------------------------------------- private
    def _apply_next_state(self):
        self.next_button.set_enabled(self._enabled and self._next_allowed
                                     and self._next_visible)

    def _next_clicked(self):
        if self._next_allowed and self._on_next_batch:
            self._on_next_batch()


__all__ = ["IterationCard"]

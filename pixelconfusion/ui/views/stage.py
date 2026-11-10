"""Preview stage: single results or batch result grids."""

from __future__ import annotations

import tkinter as tk

from pixelconfusion.batch import BatchItem
from pixelconfusion.ui.images import icon_photo
from pixelconfusion.ui.text import ellipsize, make_label
from pixelconfusion.ui.theme import BG, FAINT, LINE, MUTED, PINK, RED, SURFACE
from pixelconfusion.ui.widgets import Card, PillButton, PreviewTile, ProgressBar, ResultPane


class StageView(Card):
    def __init__(self, master, *, on_pick, on_use_result, on_save, on_open_result,
                 outer_bg=BG):
        super().__init__(master, height=560, outer_bg=outer_bg)
        self._mode = "single"
        self._auto = False
        self._single_direction = "forward"
        self._has_result = False
        self._actions_busy = False

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
        self._head_hint = make_label(hint, "自动适配预览 · 输出保留原始尺寸", 8,
                                     fg=FAINT)
        self._head_hint.pack(side="left", padx=(5, 0))

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

        self.actions = tk.Frame(footer, bg=SURFACE)
        self.actions.place(relx=1.0, x=-12, rely=0.5, anchor="e")
        self.use_button = PillButton(self.actions, "用作输入",
                                     command=on_use_result, icon="corner",
                                     kind="secondary", small=True, height=30,
                                     outer_bg=SURFACE)
        self.use_button.pack(side="left")
        self.save_button = PillButton(self.actions, "保存 PNG", command=on_save,
                                      icon="download", kind="primary", small=True,
                                      height=30, outer_bg=SURFACE)
        self.save_button.pack(side="left", padx=(7, 0))

        self.batch_hint = make_label(footer, "点击结果可预览 · 保存 · 用作输入", 8,
                                     fg=FAINT)
        self.batch_hint.place(relx=1.0, x=-12, rely=0.5, anchor="e")
        self.batch_hint.place_forget()

        body = tk.Frame(inner, bg=SURFACE)
        body.pack(fill="both", expand=True, padx=4, pady=(8, 8))
        body.grid_rowconfigure(0, weight=1)
        body.grid_columnconfigure(0, weight=1, uniform="preview")
        body.grid_columnconfigure(1, minsize=12)
        body.grid_columnconfigure(2, weight=1, uniform="preview")
        self.body = body
        self.input_tile = PreviewTile(body, "输入", "input", on_pick=on_pick)
        self.output_tile = PreviewTile(body, "结果", "output")
        self.reverse_pane = ResultPane(body, "反向结果集", "reverse",
                                       on_open=on_open_result)
        self.forward_pane = ResultPane(body, "正向结果集", "forward",
                                       on_open=on_open_result)
        self._apply_layout()
        self._apply_actions_visibility()
        self._update_head_hint()
        self._apply_actions_state()

    # ---------------------------------------------------------------- modes
    def set_mode(self, mode: str, auto: bool):
        self._mode = mode
        self._auto = bool(auto)
        self._apply_layout()
        self._apply_actions_visibility()
        self._update_head_hint()

    def begin_batch(self, *, auto: bool, direction: str, index: int, start: int,
                    count: int):
        self._mode = "batch"
        self._auto = bool(auto)
        self._single_direction = direction
        self._has_result = False
        self._apply_layout()
        self._apply_actions_visibility()
        self._update_head_hint()
        self.reverse_pane.clear()
        self.forward_pane.clear()
        range_text = f"第 {index} 批 · {start}–{start + count - 1} 次"
        if auto:
            self.reverse_pane.set_direction("reverse", "反向结果集")
            self.forward_pane.set_direction("forward", "正向结果集")
            self.reverse_pane.set_meta(range_text)
            self.forward_pane.set_meta(range_text)
            self.reverse_pane.set_placeholder("正在生成反向结果集…", range_text)
            self.forward_pane.set_placeholder("正在生成正向结果集…", range_text)
        else:
            label = "反向结果集" if direction == "reverse" else "正向结果集"
            self.forward_pane.set_direction(direction, label)
            self.forward_pane.set_meta(range_text)
            self.forward_pane.set_placeholder(f"正在生成{label}…", range_text)
            self.reverse_pane.set_meta("")
        self.set_progress(0)

    def append_batch_item(self, item: BatchItem):
        if self._auto:
            if item.direction == "reverse":
                self.reverse_pane.append_item(item)
            else:
                self.forward_pane.append_item(item)
        else:
            self.forward_pane.append_item(item)

    def finish_batch(self, *, auto: bool, index: int, start: int, count: int):
        range_text = f"第 {index} 批 · {start}–{start + count - 1} 次"
        if auto:
            self.reverse_pane.set_meta(range_text)
            self.forward_pane.set_meta(range_text)
            if self.reverse_pane.count == 0:
                self.reverse_pane.set_placeholder("本批没有结果", range_text)
            if self.forward_pane.count == 0:
                self.forward_pane.set_placeholder("本批没有结果", range_text)
        else:
            self.forward_pane.set_meta(range_text)
            if self.forward_pane.count == 0:
                self.forward_pane.set_placeholder("本批没有结果", range_text)

    def reset_batch(self, auto: bool, direction: str = "forward"):
        self._auto = bool(auto)
        self._single_direction = direction
        self._has_result = False
        self.reverse_pane.clear()
        self.forward_pane.clear()
        if auto:
            self.reverse_pane.set_direction("reverse", "反向结果集")
            self.forward_pane.set_direction("forward", "正向结果集")
            self.reverse_pane.set_meta("")
            self.forward_pane.set_meta("")
            self.reverse_pane.set_placeholder("还没有批量结果", "点击自动混淆开始")
            self.forward_pane.set_placeholder("还没有批量结果", "点击自动混淆开始")
        else:
            self.forward_pane.set_neutral_title("结果集")
            self.forward_pane.set_meta("")
            self.forward_pane.set_placeholder("还没有批量结果",
                                              "点击正向混淆或反向混淆开始")
        self.set_progress(0)

    def set_batch_enabled(self, enabled: bool):
        self.reverse_pane.set_enabled(enabled)
        self.forward_pane.set_enabled(enabled)

    # ---------------------------------------------------------------- status
    def set_status(self, text: str, tone: str = "idle") -> None:
        colors = {"idle": FAINT, "ok": "#4d8df7", "busy": PINK, "error": RED}
        self.status_dot.itemconfigure("dot", fill=colors.get(tone, colors["idle"]))
        self.status_label.configure(text=ellipsize(text, 360, 8),
                                    fg=RED if tone == "error" else MUTED)

    def set_progress(self, value: float) -> None:
        self.progress.set(value)

    def begin_busy(self, label: str) -> None:
        if self._mode == "single":
            self.output_tile.set_busy(f"正在{label}", 0)
        self.progress.set(0)

    def update_busy_progress(self, fraction: float) -> None:
        if self._mode == "single":
            self.output_tile.set_busy_progress(fraction)

    def set_source_empty(self) -> None:
        self.input_tile.set_empty("还没有输入图片", "选择图片或使用内置测试图", "image",
                                  pickable=True)
        self.input_tile.set_dims("— × —")

    def set_source_image(self, image) -> None:
        self.input_tile.set_image(image)

    def reset_result(self) -> None:
        self.output_tile.set_empty("结果会出现在这里",
                                   "点击正向混淆或反向混淆开始处理", "sparkles")
        self.output_tile.set_dims("— × —")
        self.progress.set(0)
        self._has_result = False
        self._actions_busy = False
        self._apply_actions_state()

    def show_result(self, image) -> None:
        self.output_tile.set_image(image)
        self._has_result = True
        self._apply_actions_state()

    def set_actions_enabled(self, has_result: bool, busy: bool) -> None:
        self._has_result = has_result
        self._actions_busy = busy
        self._apply_actions_state()

    # --------------------------------------------------------------- private
    def _apply_layout(self):
        for widget in (self.input_tile, self.output_tile, self.reverse_pane,
                       self.forward_pane):
            widget.grid_remove()
        if self._mode == "single":
            self.input_tile.grid(row=0, column=0, sticky="nsew")
            self.output_tile.grid(row=0, column=2, sticky="nsew")
        elif self._auto:
            self.reverse_pane.grid(row=0, column=0, sticky="nsew")
            self.forward_pane.grid(row=0, column=2, sticky="nsew")
        else:
            self.input_tile.grid(row=0, column=0, sticky="nsew")
            self.forward_pane.grid(row=0, column=2, sticky="nsew")

    def _apply_actions_visibility(self):
        if self._mode == "single":
            self.batch_hint.place_forget()
            self.actions.place(relx=1.0, x=-12, rely=0.5, anchor="e")
        else:
            self.actions.place_forget()
            self.batch_hint.place(relx=1.0, x=-12, rely=0.5, anchor="e")

    def _apply_actions_state(self):
        enabled = self._has_result and not self._actions_busy
        self.use_button.set_enabled(enabled)
        self.save_button.set_enabled(enabled)

    def _update_head_hint(self):
        if self._mode == "single":
            text = "自动适配预览 · 输出保留原始尺寸"
        elif self._auto:
            text = "正反结果集同步显示 · 点击缩略图放大预览"
        else:
            text = "整批结果集 · 点击缩略图放大预览"
        self._head_hint.configure(text=text)


__all__ = ["StageView"]

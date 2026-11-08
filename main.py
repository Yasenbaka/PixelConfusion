#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PixelConfusion: a local image permutation tool with a flat desktop interface."""

from __future__ import annotations

import queue
import sys
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox

try:
    from PIL import Image, ImageDraw, ImageFont

    import ui
    from core import Transformer, load_image, save_png
except ImportError as error:
    command = f'"{sys.executable}" -m pip install -r "{Path(__file__).with_name("requirements.txt")}"'
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror("缺少依赖", f"请在终端执行以下命令后重新启动：\n\n{command}\n\n{error}", parent=root)
    root.destroy()
    raise SystemExit(1) from error


def make_demo() -> Image.Image:
    """A self-contained geometric picture for round-trip testing."""
    size = 640
    image = Image.new("RGBA", (size, size), "#eef4fa")
    draw = ImageDraw.Draw(image)
    for y in range(size):
        ratio = y / max(1, size - 1)
        color = (233 - int(8 * ratio), 241 - int(5 * ratio), 250 - int(2 * ratio), 255)
        draw.line((0, y, size, y), fill=color)
    draw.rounded_rectangle((48, 54, 596, 602), radius=34, fill="#dfeaf4")
    draw.rounded_rectangle((42, 42, 588, 588), radius=34, fill="#ffffff")
    draw.ellipse((100, 98, 300, 298), fill="#f1ad48")
    draw.ellipse((114, 112, 286, 284), outline="#ffffff", width=3)
    draw.rounded_rectangle((346, 116, 540, 270), radius=18, fill="#3e7cd3")
    draw.polygon(((112, 496), (236, 320), (360, 496)), fill="#44aa8b")
    for x in range(390, 540, 24):
        draw.rounded_rectangle((x, 360, x + 13, 506), radius=6, fill="#9568bf")
    try:
        font = ImageFont.truetype("segoeui.ttf", 16)
    except OSError:
        font = ImageFont.load_default()
    draw.text((100, 548), "PIXELCONFUSION  /  LOCAL TEST IMAGE", fill="#263750", font=font)
    draw.ellipse((550, 550, 562, 562), fill="#ee2a7b")
    return image


class App(tk.Tk):
    # The window chrome (header bar) is always full-bleed; only the content
    # column is capped and centred so wide windows stay readable.
    CONTENT_WIDTH = 1320
    SIDE_PAD = 26

    def __init__(self):
        super().__init__()
        self.title("PixelConfusion · 图片混淆与复原")
        self.configure(background=ui.BG)
        self.minsize(1160, 820)
        width, height = 1280, 880
        x = max(0, (self.winfo_screenwidth() - width) // 2)
        y = max(0, (self.winfo_screenheight() - height) // 2 - 18)
        self.geometry(f"{width}x{height}+{x}+{y}")
        try:
            self.iconphoto(True, ui.brand_photo(64))
        except tk.TclError:
            pass

        self.method = "gilbert"
        self.iterations = tk.StringVar(value="1")
        self.offset = tk.StringVar(value="")
        self.param_a = tk.StringVar(value="1")
        self.param_b = tk.StringVar(value="1")

        self.source_image = None
        self.result_image = None
        self.source_path = None
        self.source_name = ""
        self.source_stem = "catmap-demo"
        self.result_action = "scrambled"
        self._busy = False
        self._operation = None
        self._events: queue.Queue = queue.Queue()
        self._engine = Transformer()
        self._thumb_photo = None
        self._poll_job = None
        self._resize_job = None

        self._build_interface()
        self._show_empty_source()
        self._on_method_change("gilbert")
        self._set_status("就绪 · 选择图片或使用内置测试图", "idle")
        self._set_steps(1)
        self._refresh_controls()
        self.protocol("WM_DELETE_WINDOW", self._close)
        self.bind("<Configure>", self._on_window_configure)
        self.update_idletasks()
        self._resize_page()
        self._apply_dark_title_bar()
        self._poll_job = self.after(60, self._poll_events)

    def _apply_dark_title_bar(self):
        if sys.platform != "win32":
            return
        try:
            import ctypes

            hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
            enabled = ctypes.c_int(1)
            for attribute in (20, 19):
                ctypes.windll.dwmapi.DwmSetWindowAttribute(
                    hwnd, attribute, ctypes.byref(enabled), ctypes.sizeof(enabled))
        except Exception:
            pass

    # ------------------------------------------------------------ layout
    def _label(self, parent, text, size=9, weight="normal", fg=ui.TEXT, bg=ui.SURFACE, **kwargs):
        return tk.Label(parent, text=text, font=ui.ui_font(size, weight), fg=fg, bg=bg,
                        bd=0, highlightthickness=0, **kwargs)

    def _build_interface(self):
        self.page = tk.Frame(self, bg=ui.BG)
        self.page.place(x=0, y=0, relwidth=1, relheight=1)
        self.page.grid_columnconfigure(0, weight=1)
        self.page.grid_rowconfigure(1, weight=1)

        self._build_appbar(self.page)

        main = tk.Frame(self.page, bg=ui.BG)
        main.grid(row=1, column=0, sticky="nsew", padx=self.SIDE_PAD)
        self.main = main
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(0, weight=1)

        self._build_workspace(main)

    def _build_appbar(self, parent):
        bar = tk.Frame(parent, bg=ui.SURFACE, height=62)
        bar.grid(row=0, column=0, sticky="ew")
        bar.grid_propagate(False)
        self.appbar = bar
        tk.Frame(bar, bg=ui.LINE, height=1).place(relx=0, rely=1, anchor="sw", relwidth=1)
        left = tk.Frame(bar, bg=ui.SURFACE)
        left.pack(side="left", pady=15, padx=(self.SIDE_PAD, 0))
        self.appbar_left = left
        tk.Label(left, image=ui.brand_photo(31), bg=ui.SURFACE, bd=0).pack(side="left")
        self._label(left, "PixelConfusion", 13, "bold", ui.TEXT_BRIGHT, ui.SURFACE).pack(side="left", padx=(10, 0))
        tk.Frame(left, bg=ui.LINE_STRONG, width=1, height=22).pack(side="left", padx=13, pady=4)
        title_block = tk.Frame(left, bg=ui.SURFACE)
        title_block.pack(side="left")
        self._label(title_block, "图片混淆与复原", 12, "bold", ui.TEXT_BRIGHT, ui.SURFACE).pack(anchor="w")
        self._label(title_block, "打乱像素顺序，再用相同的参数完整还原。所有处理都在本机完成。", 8,
                    fg=ui.MUTED, bg=ui.SURFACE).pack(anchor="w", pady=(2, 0))

        right = tk.Frame(bar, bg=ui.SURFACE)
        right.pack(side="right", pady=16, padx=(0, self.SIDE_PAD))
        self.appbar_right = right
        help_button = ui.IconButton(right, "help", command=self._show_help, size=30, icon_size=16,
                                    tooltip="使用说明", outer_bg=ui.SURFACE)
        help_button.pack(side="right", padx=(7, 0))
        self.steps = ui.Steps(right, active=1, outer_bg=ui.SURFACE)
        self.steps.pack(side="right")

    def _build_workspace(self, parent):
        workspace = tk.Frame(parent, bg=ui.BG)
        workspace.grid(row=0, column=0, sticky="nsew", pady=(18, 18))
        workspace.grid_rowconfigure(0, weight=1)
        workspace.grid_columnconfigure(0, minsize=336)
        workspace.grid_columnconfigure(1, weight=1)
        self.workspace = workspace

        self.rail = tk.Frame(workspace, bg=ui.BG)
        self.rail.grid(row=0, column=0, sticky="nsew")
        self.rail.grid_columnconfigure(0, weight=1)
        self.rail.grid_rowconfigure(3, weight=1)
        self._build_source_card()
        tk.Frame(self.rail, bg=ui.BG, height=12).grid(row=1, column=0, sticky="ew")
        self._build_params_card()
        tk.Frame(self.rail, bg=ui.BG).grid(row=3, column=0, sticky="nsew")
        self._build_actions()

        self._build_stage()

    def _build_source_card(self):
        card = ui.Card(self.rail, height=206, outer_bg=ui.BG)
        card.grid(row=0, column=0, sticky="ew")
        body = tk.Frame(card.content, bg=ui.SURFACE)
        body.pack(fill="both", expand=True, padx=6, pady=6)
        header = tk.Frame(body, bg=ui.SURFACE, height=22)
        header.pack(fill="x")
        header.pack_propagate(False)
        self._label(header, "来源图片", 9, "bold").pack(side="left")
        self.source_pill = ui.Pill(header, "未选择", bg="#35373b", fg=ui.MUTED,
                                   dot=ui.FAINT, height=20, border=ui.LINE_STRONG)
        self.source_pill.pack(side="right")

        holder = tk.Frame(body, bg=ui.SURFACE, height=108)
        holder.pack(fill="x", pady=(8, 0))
        holder.pack_propagate(False)
        self.dropzone = ui.DropZone(holder, command=self._choose_image, outer_bg=ui.SURFACE)
        self.dropzone.pack(fill="both", expand=True)

        self.loaded_row = tk.Frame(holder, bg=ui.SURFACE)
        self.thumb_label = tk.Label(self.loaded_row, bg=ui.SURFACE, bd=0)
        self.thumb_label.pack(side="left")
        info = tk.Frame(self.loaded_row, bg=ui.SURFACE)
        info.pack(side="left", fill="both", expand=True, padx=(12, 4))
        self.file_name_label = self._label(info, "", 9, "bold", anchor="w", justify="left")
        self.file_name_label.pack(anchor="w", pady=(14, 0))
        self.file_meta_label = self._label(info, "", 8, fg=ui.FAINT, anchor="w")
        self.file_meta_label.pack(anchor="w", pady=(3, 0))
        actions = tk.Frame(self.loaded_row, bg=ui.SURFACE)
        actions.pack(side="right", fill="y")
        self.replace_button = ui.IconButton(actions, "upload", command=self._choose_image,
                                            size=24, icon_size=14, tooltip="更换图片",
                                            outer_bg=ui.SURFACE)
        self.replace_button.pack(side="left", pady=20)
        self.clear_button = ui.IconButton(actions, "x", command=self._clear_source,
                                          size=24, icon_size=14, tooltip="清空图片",
                                          outer_bg=ui.SURFACE)
        self.clear_button.pack(side="left", padx=(3, 0), pady=20)

        self.demo_link = ui.TextLink(body, "使用内置测试图", command=self._use_demo,
                                     outer_bg=ui.SURFACE)
        self.demo_link.pack(anchor="w", pady=(8, 0))

    def _build_params_card(self):
        card = ui.Card(self.rail, height=360, outer_bg=ui.BG)
        card.grid(row=2, column=0, sticky="ew")
        body = tk.Frame(card.content, bg=ui.SURFACE)
        body.pack(fill="both", expand=True, padx=10, pady=6)
        header = tk.Frame(body, bg=ui.SURFACE, height=16)
        header.pack(fill="x")
        header.pack_propagate(False)
        self._label(header, "算法与参数", 9, "bold").pack(side="left")

        self.segmented = ui.Segmented(body, "gilbert", on_change=self._on_method_change,
                                      outer_bg=ui.SURFACE)
        self.segmented.pack(fill="x", pady=(12, 0))
        self.method_desc = self._label(body, "", 8, fg=ui.MUTED, anchor="w")
        self.method_desc.pack(fill="x", pady=(8, 0))
        self._label(body, "迭代次数", 8, fg=ui.MUTED).pack(anchor="w", pady=(12, 0))
        self.stepper = ui.NumberStepper(body, self.iterations, 1, 1_000_000,
                                        outer_bg=ui.SURFACE)
        self.stepper.pack(fill="x", pady=(4, 0))

        self.param_block = tk.Frame(body, bg=ui.SURFACE, height=60)
        self.param_block.pack(fill="x", pady=(12, 0))
        self.param_block.pack_propagate(False)
        self.offset_frame = tk.Frame(self.param_block, bg=ui.SURFACE)
        self.offset_frame.place(x=0, y=0, relwidth=1, height=54)
        offset_head = tk.Frame(self.offset_frame, bg=ui.SURFACE, height=14)
        offset_head.pack(fill="x")
        offset_head.pack_propagate(False)
        self._label(offset_head, "偏移量", 8, fg=ui.MUTED).pack(side="left")
        self._label(offset_head, "留空自动", 7, fg=ui.FAINT).pack(side="right")
        self.offset_field = ui.TextField(self.offset_frame, self.offset, "黄金比", height=36,
                                         outer_bg=ui.SURFACE)
        self.offset_field.pack(fill="x", pady=(4, 0))

        self.ab_frame = tk.Frame(self.param_block, bg=ui.SURFACE)
        self.ab_frame.grid_columnconfigure(0, weight=1, uniform="ab")
        self.ab_frame.grid_columnconfigure(1, weight=1, uniform="ab")
        for column, (title, variable) in enumerate((("参数 a", self.param_a), ("参数 b", self.param_b))):
            field_wrap = tk.Frame(self.ab_frame, bg=ui.SURFACE)
            field_wrap.grid(row=0, column=column, sticky="ew", padx=(4, 4))
            self._label(field_wrap, title, 8, fg=ui.MUTED).pack(anchor="w")
            field = ui.TextField(field_wrap, variable, "", height=36, outer_bg=ui.SURFACE)
            field.pack(fill="x", pady=(4, 0))
            if column == 0:
                self.a_field = field
            else:
                self.b_field = field

        self.hint = ui.HintBox(body, height=58, outer_bg=ui.SURFACE)
        self.hint.pack(fill="x", pady=(12, 12))

    def _build_actions(self):
        actions = tk.Frame(self.rail, bg=ui.BG)
        actions.grid(row=4, column=0, sticky="ew")
        actions.grid_columnconfigure(0, weight=1, uniform="action")
        actions.grid_columnconfigure(1, weight=1, uniform="action")
        self.scramble_button = ui.PillButton(actions, "混淆图片", command=lambda: self._transform("scramble"),
                                             icon="shuffle", kind="primary", height=38)
        self.scramble_button.grid(row=0, column=0, sticky="ew")
        self.restore_button = ui.PillButton(actions, "复原图片", command=lambda: self._transform("restore"),
                                            icon="rotate", kind="secondary", height=38)
        self.restore_button.grid(row=0, column=1, sticky="ew", padx=(8, 0))

    def _build_stage(self):
        self.stage_card = ui.Card(self.workspace, height=560, outer_bg=ui.BG)
        self.stage_card.grid(row=0, column=1, sticky="nsew", padx=(16, 0))
        inner = tk.Frame(self.stage_card.content, bg=ui.SURFACE)
        inner.pack(fill="both", expand=True)

        head = tk.Frame(inner, bg=ui.SURFACE, height=54)
        head.pack(side="top", fill="x")
        head.pack_propagate(False)
        head_left = tk.Frame(head, bg=ui.SURFACE)
        head_left.pack(side="left", padx=(6, 0), pady=17)
        self._label(head_left, "预览", 9, "bold").pack(side="left")
        hint = tk.Frame(head, bg=ui.SURFACE)
        hint.pack(side="right", padx=(0, 6), pady=19)
        tk.Label(hint, image=ui.icon_photo("info", ui.FAINT, 12), bg=ui.SURFACE, bd=0).pack(side="left")
        self._label(hint, "自动适配预览 · 输出保留原始尺寸", 8, fg=ui.FAINT).pack(
            side="left", padx=(5, 0))

        footer_wrap = tk.Frame(inner, bg=ui.SURFACE)
        footer_wrap.pack(side="bottom", fill="x")
        tk.Frame(footer_wrap, bg=ui.LINE, height=1).pack(fill="x")
        footer = tk.Frame(footer_wrap, bg=ui.SURFACE, height=56)
        footer.pack(fill="x")
        footer.pack_propagate(False)
        left_group = tk.Frame(footer, bg=ui.SURFACE)
        left_group.place(x=12, rely=0.5, anchor="w")
        self.status_dot = tk.Canvas(left_group, width=7, height=7, bg=ui.SURFACE,
                                    highlightthickness=0, bd=0)
        self.status_dot.pack(side="left", padx=(0, 7))
        self.status_dot.create_oval(0, 0, 6, 6, fill=ui.FAINT, outline="", tags="dot")
        self.status_label = self._label(left_group, "", 8, fg=ui.MUTED, anchor="w")
        self.status_label.pack(side="left")
        self.progress = ui.ProgressBar(left_group, width=68, height=3, outer_bg=ui.SURFACE)
        self.progress.pack(side="left", padx=(10, 0))
        self._label(left_group, "本机", 7, fg=ui.FAINT).pack(side="left", padx=(8, 0))
        actions = tk.Frame(footer, bg=ui.SURFACE)
        actions.place(relx=1.0, x=-12, rely=0.5, anchor="e")
        self.use_button = ui.PillButton(actions, "用作输入", command=self._use_result,
                                        icon="corner", kind="secondary", small=True, height=30,
                                        outer_bg=ui.SURFACE)
        self.use_button.pack(side="left")
        self.save_button = ui.PillButton(actions, "保存 PNG", command=self._save,
                                         icon="download", kind="primary", small=True, height=30,
                                         outer_bg=ui.SURFACE)
        self.save_button.pack(side="left", padx=(7, 0))

        body = tk.Frame(inner, bg=ui.SURFACE)
        body.pack(fill="both", expand=True, padx=4, pady=(8, 8))
        body.grid_rowconfigure(0, weight=1)
        body.grid_columnconfigure(0, weight=1, uniform="preview")
        body.grid_columnconfigure(1, weight=1, uniform="preview")
        self.input_tile = ui.PreviewTile(body, "输入", "input", on_pick=self._choose_image)
        self.input_tile.grid(row=0, column=0, sticky="nsew")
        self.output_tile = ui.PreviewTile(body, "结果", "output")
        self.output_tile.grid(row=0, column=1, sticky="nsew", padx=(13, 0))

    # ------------------------------------------------------------ window
    def _on_window_configure(self, event):
        if event.widget is not self:
            return
        if self._resize_job:
            self.after_cancel(self._resize_job)
        self._resize_job = self.after(20, self._resize_page)

    def _side_inset(self, width=None):
        width = self.winfo_width() if width is None else width
        spare = max(0, width - self.CONTENT_WIDTH) // 2
        return self.SIDE_PAD + spare

    def _resize_page(self):
        self._resize_job = None
        if not self.winfo_exists():
            return
        inset = self._side_inset(self.winfo_width())
        self.main.grid_configure(padx=inset)
        self.appbar_left.pack_configure(padx=(inset, 0))
        self.appbar_right.pack_configure(padx=(0, inset))

    # ------------------------------------------------------------ states
    def _set_steps(self, active):
        self.steps.set_active(active)

    def _update_steps(self):
        if self._busy and self.source_image is not None:
            active = 3
        elif self._busy:
            active = 1
        elif self.result_image is not None:
            active = 4
        elif self.source_image is not None:
            active = 2
        else:
            active = 1
        self._set_steps(active)

    def _set_status(self, text, tone="idle"):
        colors = {"idle": ui.FAINT, "ok": "#4d8df7", "busy": ui.PINK, "error": ui.RED}
        self.status_dot.itemconfigure("dot", fill=colors.get(tone, colors["idle"]))
        self.status_label.configure(text=self._ellipsize(text, 248, 8),
                                    fg=ui.RED if tone == "error" else ui.MUTED)

    def _set_source_pill(self, text, tone):
        if tone == "loaded":
            self.source_pill.update_pill(text, bg="#2f405c", fg="#cfe0ff",
                                         dot="#4d8df7", border="#47709f")
        elif tone == "busy":
            self.source_pill.update_pill(text, bg="#3a3322", fg=ui.PINK,
                                         dot=ui.PINK, border="#5c4a22")
        else:
            self.source_pill.update_pill(text, bg="#35373b", fg=ui.MUTED,
                                         dot=ui.FAINT, border=ui.LINE_STRONG)

    def _refresh_controls(self):
        busy = self._busy
        has_source = self.source_image is not None
        has_result = self.result_image is not None
        self.segmented.set_enabled(not busy)
        self.stepper.set_enabled(not busy)
        self.offset_field.set_enabled(not busy)
        self.a_field.set_enabled(not busy)
        self.b_field.set_enabled(not busy)
        self.dropzone.set_enabled(not busy)
        self.demo_link.set_enabled(not busy)
        self.replace_button.set_enabled(not busy)
        self.clear_button.set_enabled(not busy)
        self.scramble_button.set_enabled(has_source and not busy)
        self.restore_button.set_enabled(has_source and not busy)
        self.use_button.set_enabled(has_result and not busy)
        self.save_button.set_enabled(has_result and not busy)

    def _show_empty_source(self):
        self.dropzone.pack(fill="both", expand=True)
        self.loaded_row.place_forget()
        self.input_tile.set_empty("还没有输入图片", "选择图片或使用内置测试图", "image", pickable=True)
        self.input_tile.set_dims("— × —")
        self.output_tile.set_empty("结果会出现在这里", "点击混淆或复原开始处理", "sparkles")
        self.output_tile.set_dims("— × —")
        self.demo_link.set_text("使用内置测试图")

    def _show_empty_result(self):
        self.result_image = None
        self.output_tile.set_empty("结果会出现在这里", "点击混淆或复原开始处理", "sparkles")
        self.output_tile.set_dims("— × —")
        self.progress.set(0)

    # ------------------------------------------------------------ actions
    def _choose_image(self):
        if self._busy:
            return
        path = filedialog.askopenfilename(parent=self, title="选择普通图片", filetypes=[
            ("图片", "*.png *.jpg *.jpeg *.webp *.bmp *.tif *.tiff"), ("所有文件", "*.*")])
        if not path:
            return
        self._operation = "source"
        self._set_status("正在读取图片…", "busy")
        self._set_source_pill("读取中", "busy")
        self._start_worker(lambda: ("source", load_image(path), Path(path)))

    def _use_demo(self):
        if self._busy:
            return
        self._set_source(make_demo(), name="catmap-demo.png")

    def _set_source(self, image, path=None, name=None):
        self.source_image = image
        self.source_path = path
        self.source_name = name or (path.name if path else "内置测试图")
        self.source_stem = Path(self.source_name).stem or "catmap-demo"
        self.result_image = None
        self.result_action = "scrambled"
        self._thumb_photo = ui.thumbnail_photo(image)
        self.thumb_label.configure(image=self._thumb_photo)
        self.file_name_label.configure(text=self._ellipsize(self.source_name, 158, 9, "bold"))
        suffix = (path.suffix.lstrip(".").upper() if path else "PNG")
        meta = f"{image.width} × {image.height} · {suffix}"
        if path:
            try:
                meta += f" · {self._human_size(path.stat().st_size)}"
            except OSError:
                pass
        self.file_meta_label.configure(text=self._ellipsize(meta, 178, 8))
        self.dropzone.pack_forget()
        self.loaded_row.place(relx=0, rely=0.5, anchor="w", relwidth=1, height=64)
        self.demo_link.set_text("换成内置测试图")
        self._set_source_pill("已载入", "loaded")
        self.input_tile.set_image(image)
        self.input_tile.set_dims(f"{image.width} × {image.height}")
        self._show_empty_result()
        self._set_status("已载入图片 · 选择算法后开始处理", "ok")
        self._on_method_change(self.method)
        self._update_steps()
        self._refresh_controls()

    def _clear_source(self):
        if self._busy:
            return
        self.source_image = None
        self.source_path = None
        self.source_name = ""
        self.result_image = None
        self._thumb_photo = None
        self.thumb_label.configure(image="")
        self.dropzone.pack(fill="both", expand=True)
        self.loaded_row.place_forget()
        self._set_source_pill("未选择", "idle")
        self._show_empty_source()
        self.progress.set(0)
        self._set_status("就绪 · 选择图片或使用内置测试图", "idle")
        self._on_method_change(self.method)
        self._update_steps()
        self._refresh_controls()

    def _use_result(self):
        if self.result_image is None or self._busy:
            return
        image = self.result_image.copy()
        self._set_source(image, name="上一轮处理结果.png")
        self._set_status("已将结果作为输入", "ok")

    def _on_method_change(self, value=None):
        if value is not None and value != self.method:
            self.method = value
            self.segmented.set(value)
        gilbert = self.method == "gilbert"
        if gilbert:
            self.method_desc.configure(text="广义希尔伯特曲线 · 支持任意宽高", fg=ui.MUTED)
            self.hint.set_text("复原时请保持次数与偏移量一致；留空自动使用默认黄金比例偏移。")
            self.ab_frame.place_forget()
            self.offset_frame.place(x=0, y=0, relwidth=1, height=60)
        else:
            bad_size = (self.source_image is not None
                        and self.source_image.width != self.source_image.height)
            self.method_desc.configure(
                text="标准猫映射 · 仅支持正方形图片",
                fg=ui.PINK if bad_size else ui.MUTED)
            self.hint.set_text("复原时请保持次数、a、b 一致；坐标变换仅在正方形图片上成立。")
            self.offset_frame.place_forget()
            self.ab_frame.place(x=0, y=0, relwidth=1, height=60)
        self._refresh_controls()

    def _transform(self, action):
        if self.source_image is None or self._busy:
            return
        try:
            iterations = int(self.iterations.get())
            if not 1 <= iterations <= 1_000_000:
                raise ValueError("次数需在 1 到 1000000 之间。")
            method = self.method
            offset_text = self.offset.get().strip()
            offset = int(offset_text) if method == "gilbert" and offset_text else None
            a = int(self.param_a.get()) if method == "arnold" else 1
            b = int(self.param_b.get()) if method == "arnold" else 1
            if method == "arnold" and self.source_image.width != self.source_image.height:
                raise ValueError("标准 Arnold 猫映射需要正方形图片。长方形图片可以选择 Gilbert。")
        except ValueError as error:
            messagebox.showerror("参数有误", f"请检查次数和算法参数是否为整数。\n\n{error}", parent=self)
            return
        image = self.source_image
        label = "复原" if action == "restore" else "混淆"
        self._operation = "transform"
        self._set_status(f"正在{label}图片…", "busy")
        self._set_source_pill("处理中", "busy")
        self.output_tile.set_busy(f"正在{label}", 0)
        self.progress.set(0)
        self._update_steps()

        def task():
            started = time.perf_counter()
            result = self._engine.apply(image, method, action, iterations, offset, a, b,
                                        lambda n, text: self._events.put(("progress", (n, text))))
            return "result", result, action, label, method, iterations, time.perf_counter() - started

        self._start_worker(task)

    def _save(self):
        if self.result_image is None or self._busy:
            return
        suffix = "restored" if self.result_action == "restored" else "scrambled"
        path = filedialog.asksaveasfilename(
            parent=self, title="保存处理结果", initialfile=f"{self.source_stem}_{suffix}.png",
            defaultextension=".png", filetypes=[("PNG 图片", "*.png")])
        if not path:
            return
        if self.source_path and Path(path).resolve() == self.source_path.resolve():
            messagebox.showerror("请选择其他文件名", "请将结果保存为新文件，避免覆盖输入图片。", parent=self)
            return
        image = self.result_image
        self._operation = "save"
        self._set_status("正在保存 PNG…", "busy")

        def task():
            save_png(image, path)
            return "saved", path

        self._start_worker(task)

    def _start_worker(self, task):
        if self._busy:
            return
        self._busy = True
        self._refresh_controls()
        self._update_steps()

        def run():
            try:
                self._events.put(("done", task()))
            except Exception as error:
                self._events.put(("error", str(error) or type(error).__name__))

        threading.Thread(target=run, daemon=True).start()

    # ------------------------------------------------------------ events
    def _poll_events(self):
        while True:
            try:
                kind, payload = self._events.get_nowait()
            except queue.Empty:
                break
            if kind == "progress":
                fraction, text = payload
                self.progress.set(fraction)
                self.output_tile.set_busy_progress(fraction)
                self._set_status(f"{text} · {fraction:.0%}", "busy")
            elif kind == "error":
                self._busy = False
                operation = self._operation
                self._operation = None
                self.progress.set(0)
                if operation == "transform":
                    if self.result_image is not None:
                        self.output_tile.set_image(self.result_image)
                    else:
                        self._show_empty_result()
                    self._set_source_pill("已载入", "loaded")
                elif self.source_image is not None:
                    self._set_source_pill("已载入", "loaded")
                else:
                    self._set_source_pill("未选择", "idle")
                self._set_status("操作未完成 · 请检查输入图片或参数", "error")
                self._update_steps()
                self._refresh_controls()
                messagebox.showerror("操作失败", payload, parent=self)
            elif kind == "done":
                self._busy = False
                operation = self._operation
                self._operation = None
                self._refresh_controls()
                if payload[0] == "source":
                    self._set_source(payload[1], payload[2])
                elif payload[0] == "result":
                    _, image, action, label, method, iterations, elapsed = payload
                    self.result_image = image
                    self.result_action = "restored" if action == "restore" else "scrambled"
                    self.output_tile.set_image(image)
                    self._set_source_pill("已载入", "loaded")
                    self.progress.set(1.0)
                    self._set_status(f"{label}完成 · {image.width} × {image.height} · {elapsed:.2f} 秒", "ok")
                    self._update_steps()
                    self._refresh_controls()
                elif payload[0] == "saved":
                    path = payload[1]
                    self.progress.set(1.0)
                    self._set_status(f"已保存 · {Path(path).name}", "ok")
                    self._update_steps()
                    self._refresh_controls()
        self._poll_job = self.after(60, self._poll_events)

    # ------------------------------------------------------------ misc
    @staticmethod
    def _human_size(size):
        if size < 1024:
            return f"{size} B"
        if size < 1024 * 1024:
            return f"{size / 1024:.0f} KB"
        return f"{size / 1024 / 1024:.1f} MB"

    @staticmethod
    def _ellipsize(text, max_width, size=9, weight="normal"):
        font = ui.ui_font(size, weight)
        if font.measure(text) <= max_width:
            return text
        clipped = text
        while clipped and font.measure(clipped + "…") > max_width:
            clipped = clipped[:-1]
        return clipped + "…"

    def _show_help(self):
        messagebox.showinfo(
            "使用说明",
            "选择一张普通图片，或使用内置测试图。\n\n"
            "Gilbert 支持任意宽高；Arnold 需要正方形图片。\n"
            "混淆和复原时请使用相同的次数与参数。\n\n"
            "所有处理都在本机完成，不会上传任何文件。",
            parent=self)

    def _close(self):
        for job in (self._poll_job, self._resize_job):
            if job:
                try:
                    self.after_cancel(job)
                except tk.TclError:
                    pass
        self.destroy()


if __name__ == "__main__":
    App().mainloop()

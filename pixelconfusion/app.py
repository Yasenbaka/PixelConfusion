"""Tkinter window and interaction controller for PixelConfusion."""

from __future__ import annotations

import time
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox

from PIL import Image

from pixelconfusion.core import Transformer, load_image, save_png
from pixelconfusion.demo import make_demo
from pixelconfusion.formatting import human_size
from pixelconfusion.parameters import build_transform_request
from pixelconfusion.tasks import BackgroundRunner
from pixelconfusion.ui import theme
from pixelconfusion.ui.images import brand_photo, thumbnail_photo
from pixelconfusion.ui.views import PageView
from pixelconfusion.ui.window import apply_dark_title_bar


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self._configure_window()
        self._init_state()
        self._build_interface()
        self._show_empty_source()
        self._on_method_change("gilbert")
        self._set_status("就绪 · 选择图片或使用内置测试图", "idle")
        self._set_steps(1)
        self._refresh_controls()
        self.protocol("WM_DELETE_WINDOW", self._close)
        self.update_idletasks()
        self.page.apply_inset()
        apply_dark_title_bar(self)
        self._poll_job = self.after(60, self._poll_events)

    # ------------------------------------------------------------ state
    def _configure_window(self) -> None:
        self.title("PixelConfusion · 图片混淆与复原")
        self.configure(background=theme.BG)
        self.minsize(1160, 820)
        width, height = 1280, 880
        x = max(0, (self.winfo_screenwidth() - width) // 2)
        y = max(0, (self.winfo_screenheight() - height) // 2 - 18)
        self.geometry(f"{width}x{height}+{x}+{y}")
        try:
            self.iconphoto(True, brand_photo(64))
        except tk.TclError:
            pass

    def _init_state(self) -> None:
        self.method = "gilbert"
        self.source_image: Image.Image | None = None
        self.result_image: Image.Image | None = None
        self.source_path: Path | None = None
        self.source_name = ""
        self.source_stem = "catmap-demo"
        self.result_action = "scrambled"
        self._busy = False
        self._operation: str | None = None
        self._engine = Transformer()
        self._runner = BackgroundRunner()
        self._poll_job: str | None = None

    # ------------------------------------------------------------ layout
    def _build_interface(self) -> None:
        self.page = PageView(
            self,
            on_help=self._show_help,
            on_pick=self._choose_image,
            on_clear=self._clear_source,
            on_demo=self._use_demo,
            on_method_change=self._on_method_change,
            on_scramble=lambda: self._transform("scramble"),
            on_restore=lambda: self._transform("restore"),
            on_use_result=self._use_result,
            on_save=self._save,
        )
        self.page.place(x=0, y=0, relwidth=1, relheight=1)

        self.appbar = self.page.appbar
        self.workspace = self.page.workspace
        self.source_card = self.workspace.source_card
        self.params_card = self.workspace.params_card
        self.action_row = self.workspace.action_row
        self.stage = self.workspace.stage

    # ------------------------------------------------------------ view state
    def _set_steps(self, active: int) -> None:
        self.appbar.set_steps(active)

    def _update_steps(self) -> None:
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

    def _set_status(self, text: str, tone: str = "idle") -> None:
        self.stage.set_status(text, tone)

    def _set_source_pill(self, text: str, tone: str) -> None:
        self.source_card.set_pill(text, tone)

    def _refresh_controls(self) -> None:
        busy = self._busy
        has_source = self.source_image is not None
        has_result = self.result_image is not None
        self.params_card.set_enabled(not busy)
        self.source_card.set_enabled(not busy)
        self.action_row.set_enabled(has_source, busy)
        self.stage.set_actions_enabled(has_result, busy)

    def _show_empty_source(self) -> None:
        self.source_card.show_empty()
        self.stage.set_source_empty()
        self.stage.reset_result()

    def _show_empty_result(self) -> None:
        self.result_image = None
        self.stage.reset_result()

    # ------------------------------------------------------------ actions
    def _choose_image(self) -> None:
        if self._busy:
            return
        path = filedialog.askopenfilename(
            parent=self,
            title="选择普通图片",
            filetypes=[
                ("图片", "*.png *.jpg *.jpeg *.webp *.bmp *.tif *.tiff"),
                ("所有文件", "*.*"),
            ],
        )
        if not path:
            return
        self._operation = "source"
        self._set_status("正在读取图片…", "busy")
        self._set_source_pill("读取中", "busy")
        self._start_worker(lambda: ("source", load_image(path), Path(path)))

    def _use_demo(self) -> None:
        if self._busy:
            return
        self._set_source(make_demo(), name="catmap-demo.png")

    def _set_source(self, image, path=None, name=None) -> None:
        self.source_image = image
        self.source_path = path
        self.source_name = name or (path.name if path else "内置测试图")
        self.source_stem = Path(self.source_name).stem or "catmap-demo"
        self.result_image = None
        self.result_action = "scrambled"
        suffix = path.suffix.lstrip(".").upper() if path else "PNG"
        meta = f"{image.width} × {image.height} · {suffix}"
        if path:
            try:
                meta += f" · {human_size(path.stat().st_size)}"
            except OSError:
                pass
        self.source_card.show_loaded(thumbnail_photo(image), self.source_name, meta)
        self._set_source_pill("已载入", "loaded")
        self.stage.set_source_image(image)
        self._show_empty_result()
        self._set_status("已载入图片 · 选择算法后开始处理", "ok")
        self._on_method_change(self.method)
        self._update_steps()
        self._refresh_controls()

    def _clear_source(self) -> None:
        if self._busy:
            return
        self.source_image = None
        self.source_path = None
        self.source_name = ""
        self.result_image = None
        self.source_card.show_empty()
        self._set_source_pill("未选择", "idle")
        self.stage.set_source_empty()
        self.stage.reset_result()
        self._set_status("就绪 · 选择图片或使用内置测试图", "idle")
        self._on_method_change(self.method)
        self._update_steps()
        self._refresh_controls()

    def _use_result(self) -> None:
        if self.result_image is None or self._busy:
            return
        image = self.result_image.copy()
        self._set_source(image, name="上一轮处理结果.png")
        self._set_status("已将结果作为输入", "ok")

    def _on_method_change(self, value=None) -> None:
        if value is not None and value != self.method:
            self.method = value
            self.params_card.set_method(value)
        self.params_card.show_method(self.method, self.source_image)
        self._refresh_controls()

    def _transform(self, action: str) -> None:
        if self.source_image is None or self._busy:
            return
        try:
            iterations_text, offset_text, a_text, b_text = (
                self.params_card.parameter_text()
            )
            request = build_transform_request(
                self.method,
                action,
                iterations_text,
                offset_text,
                a_text,
                b_text,
                width=self.source_image.width,
                height=self.source_image.height,
            )
        except ValueError as error:
            messagebox.showerror(
                "参数有误",
                f"请检查次数和算法参数是否为整数。\n\n{error}",
                parent=self,
            )
            return

        image = self.source_image
        label = "复原" if action == "restore" else "混淆"
        self._operation = "transform"
        self._set_status(f"正在{label}图片…", "busy")
        self._set_source_pill("处理中", "busy")
        self.stage.begin_busy(label)
        self._update_steps()

        def task():
            started = time.perf_counter()
            result = self._engine.apply(
                image,
                request.method,
                request.action,
                request.iterations,
                request.offset,
                request.a,
                request.b,
                self._runner.report_progress,
            )
            return ("result", result, request.action, label,
                    time.perf_counter() - started)

        self._start_worker(task)

    def _save(self) -> None:
        if self.result_image is None or self._busy:
            return
        suffix = "restored" if self.result_action == "restored" else "scrambled"
        path = filedialog.asksaveasfilename(
            parent=self,
            title="保存处理结果",
            initialfile=f"{self.source_stem}_{suffix}.png",
            defaultextension=".png",
            filetypes=[("PNG 图片", "*.png")],
        )
        if not path:
            return
        if self.source_path and Path(path).resolve() == self.source_path.resolve():
            messagebox.showerror(
                "请选择其他文件名",
                "请将结果保存为新文件，避免覆盖输入图片。",
                parent=self,
            )
            return
        image = self.result_image
        self._operation = "save"
        self._set_status("正在保存 PNG…", "busy")

        def task():
            save_png(image, path)
            return "saved", path

        self._start_worker(task)

    def _start_worker(self, task) -> None:
        if self._busy:
            return
        self._busy = True
        self._refresh_controls()
        self._update_steps()
        self._runner.submit(task)

    # ------------------------------------------------------------ events
    def _poll_events(self) -> None:
        for kind, payload in self._runner.drain():
            if kind == "progress":
                fraction, text = payload
                self.stage.set_progress(fraction)
                self.stage.update_busy_progress(fraction)
                self._set_status(f"{text} · {fraction:.0%}", "busy")
            elif kind == "error":
                self._busy = False
                operation = self._operation
                self._operation = None
                self.stage.set_progress(0)
                if operation == "transform":
                    if self.result_image is not None:
                        self.stage.show_result(self.result_image)
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
                self._operation = None
                self._refresh_controls()
                if payload[0] == "source":
                    self._set_source(payload[1], payload[2])
                elif payload[0] == "result":
                    _, image, action, label, elapsed = payload
                    self.result_image = image
                    self.result_action = "restored" if action == "restore" else "scrambled"
                    self.stage.show_result(image)
                    self._set_source_pill("已载入", "loaded")
                    self.stage.set_progress(1.0)
                    self._set_status(
                        f"{label}完成 · {image.width} × {image.height} · {elapsed:.2f} 秒",
                        "ok",
                    )
                    self._update_steps()
                    self._refresh_controls()
                elif payload[0] == "saved":
                    path = payload[1]
                    self.stage.set_progress(1.0)
                    self._set_status(f"已保存 · {Path(path).name}", "ok")
                    self._update_steps()
                    self._refresh_controls()
        self._poll_job = self.after(60, self._poll_events)

    # ------------------------------------------------------------ misc
    def _show_help(self) -> None:
        messagebox.showinfo(
            "使用说明",
            "选择一张普通图片，或使用内置测试图。\n\n"
            "Gilbert 支持任意宽高；Arnold 需要正方形图片。\n"
            "混淆和复原时请使用相同的次数与参数。\n\n"
            "所有处理都在本机完成，不会上传任何文件。",
            parent=self,
        )

    def _close(self) -> None:
        if self._poll_job:
            try:
                self.after_cancel(self._poll_job)
            except tk.TclError:
                pass
        self.page.cancel_pending()
        self.destroy()


__all__ = ["App"]

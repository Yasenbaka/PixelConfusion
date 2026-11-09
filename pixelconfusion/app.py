"""Tkinter window and interaction controller for PixelConfusion."""

from __future__ import annotations

import time
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox

from PIL import Image

from pixelconfusion.batch import BatchItem
from pixelconfusion.core import Transformer, load_image, save_png
from pixelconfusion.demo import make_demo
from pixelconfusion.formatting import human_size
from pixelconfusion.parameters import (
    DEFAULT_BATCH_COUNT,
    MAX_BATCH_COUNT,
    MAX_ITERATIONS,
    build_batch_request,
    build_transform_request,
)
from pixelconfusion.tasks import BackgroundRunner
from pixelconfusion.ui import theme
from pixelconfusion.ui.images import brand_photo, thumbnail_photo
from pixelconfusion.ui.views import PageView
from pixelconfusion.ui.views.result_preview import ResultPreview
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
        self.result_action = "forward"

        self.iteration_mode = "single"
        self.auto_mixed = False
        self.batch_count = DEFAULT_BATCH_COUNT
        self.batch_start = 1
        self.batch_index = 1
        self.batch_direction: str | None = None
        self.batch_results: dict[str, list[BatchItem]] = {
            "reverse": [],
            "forward": [],
        }
        self.batch_has_results = False

        self._busy = False
        self._operation: str | None = None
        self._engine = Transformer()
        self._runner = BackgroundRunner()
        self._poll_job: str | None = None
        self._preview: ResultPreview | None = None
        self._preview_meta: tuple[str, int] | None = None
        self._preview_token = 0
        self._save_preview: ResultPreview | None = None

    # ------------------------------------------------------------ layout
    def _build_interface(self) -> None:
        self.page = PageView(
            self,
            on_help=self._show_help,
            on_pick=self._choose_image,
            on_clear=self._clear_source,
            on_demo=self._use_demo,
            on_method_change=self._on_method_change,
            on_scramble=lambda: self._on_direction("scramble"),
            on_restore=lambda: self._on_direction("restore"),
            on_use_result=self._use_result,
            on_save=self._save,
            on_iteration_mode_change=self._on_iteration_mode_change,
            on_auto_change=self._on_auto_change,
            on_next_batch=self._on_next_batch,
            on_auto_batch=self._on_auto_batch,
            on_auto_next_batch=self._on_auto_next_batch,
            on_open_result=self._open_batch_preview,
        )
        self.page.place(x=0, y=0, relwidth=1, relheight=1)

        self.appbar = self.page.appbar
        self.workspace = self.page.workspace
        self.source_card = self.workspace.source_card
        self.params_card = self.workspace.params_card
        self.iteration_card = self.workspace.iteration_card
        self.action_row = self.workspace.action_row
        self.stage = self.workspace.stage

        self.iteration_card.count_var.trace_add(
            "write", self._on_batch_count_changed)
        for variable in (self.params_card.offset_var,
                         self.params_card.param_a_var,
                         self.params_card.param_b_var):
            variable.trace_add("write", self._on_batch_param_changed)

        self.params_card.set_mode("single")
        self.iteration_card.set_mode("single")
        self.stage.set_mode("single", False)
        self.action_row.set_mode("single", False)

    # ------------------------------------------------------------ view state
    def _set_steps(self, active: int) -> None:
        self.appbar.set_steps(active)

    def _update_steps(self) -> None:
        if self._busy and self.source_image is not None:
            active = 3
        elif self._busy:
            active = 1
        elif self._visible_result_exists():
            active = 4
        elif self.source_image is not None:
            active = 2
        else:
            active = 1
        self._set_steps(active)

    def _visible_result_exists(self) -> bool:
        if self.iteration_mode == "batch":
            return self.batch_has_results or bool(
                self.batch_results["reverse"] or self.batch_results["forward"])
        return self.result_image is not None

    def _set_status(self, text: str, tone: str = "idle") -> None:
        self.stage.set_status(text, tone)

    def _set_source_pill(self, text: str, tone: str) -> None:
        self.source_card.set_pill(text, tone)

    def _batch_end(self) -> int:
        return self.batch_start + self.batch_count - 1

    def _next_batch_start(self) -> int:
        return self.batch_start + self.batch_count

    def _can_next_batch(self) -> bool:
        if not self.batch_has_results:
            return False
        next_start = self._next_batch_start()
        return next_start + self.batch_count - 1 <= MAX_ITERATIONS

    def _refresh_controls(self) -> None:
        busy = self._busy
        has_source = self.source_image is not None
        single = self.iteration_mode == "single"
        has_single_result = single and self.result_image is not None
        has_batch = (not single) and self.batch_has_results
        can_next = (not single) and self._can_next_batch()

        self.params_card.set_enabled(not busy)
        self.source_card.set_enabled(not busy)
        self.iteration_card.set_enabled(not busy)
        self.action_row.set_mode(self.iteration_mode, self.auto_mixed)
        self.action_row.set_enabled(has_source, busy, has_batch, can_next)
        self.stage.set_actions_enabled(has_single_result, busy)
        self.stage.set_batch_enabled((not single) and not busy)
        if not single:
            self.iteration_card.set_batch_state(
                self.batch_index, self.batch_start, self.batch_count,
                self.batch_has_results, can_next, self.auto_mixed,
            )

    def _show_empty_source(self) -> None:
        self.source_image = None
        self.source_path = None
        self.source_name = ""
        self.result_image = None
        self.source_card.show_empty()
        self.source_card.set_pill("未选择", "idle")
        self.stage.set_source_empty()
        self.stage.reset_result()
        self._reset_batch_state()

    def _show_empty_result(self) -> None:
        self.result_image = None
        self.stage.reset_result()

    def _reset_batch_state(self, *, clear_view: bool = True) -> None:
        self.batch_start = 1
        self.batch_index = 1
        self.batch_direction = None
        self.batch_results = {"reverse": [], "forward": []}
        self.batch_has_results = False
        if clear_view and self.iteration_mode == "batch":
            self.stage.reset_batch(self.auto_mixed, "forward")
        if hasattr(self, "iteration_card"):
            self.iteration_card.set_batch_state(
                1, 1, max(1, self.batch_count), False, False, self.auto_mixed,
            )

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
        self.result_action = "forward"
        self.batch_results = {"reverse": [], "forward": []}
        self.batch_has_results = False
        suffix = path.suffix.lstrip(".").upper() if path else "PNG"
        meta = f"{image.width} × {image.height} · {suffix}"
        if path:
            try:
                meta += f" · {human_size(path.stat().st_size)}"
            except OSError:
                pass
        self.source_card.show_loaded(thumbnail_photo(image, 56), self.source_name,
                                     meta)
        self._set_source_pill("已载入", "loaded")
        self.stage.set_source_image(image)
        self._show_empty_result()
        self._reset_batch_state()
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
        self.source_stem = "catmap-demo"
        self.result_image = None
        self.source_card.show_empty()
        self._set_source_pill("未选择", "idle")
        self.stage.set_source_empty()
        self.stage.reset_result()
        self._reset_batch_state()
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
        changed = value is not None and value != self.method
        if changed:
            self.method = value
            self.params_card.set_method(value)
        self.params_card.show_method(self.method, self.source_image)
        if changed and self.iteration_mode == "batch":
            self._reset_batch_state()
            self._set_status("算法已切换 · 批次已重置", "idle")
        self._refresh_controls()

    def _on_iteration_mode_change(self, mode: str) -> None:
        if self._busy or mode == self.iteration_mode:
            return
        self.iteration_mode = mode
        if mode == "single":
            self.auto_mixed = False
        self.params_card.set_mode(mode)
        self.iteration_card.set_mode(mode)
        self.iteration_card.set_auto(self.auto_mixed)
        self.action_row.set_mode(mode, self.auto_mixed)
        self.stage.set_mode(mode, self.auto_mixed)
        self.result_image = None
        self.stage.reset_result()
        self._reset_batch_state()
        if mode == "batch":
            self.iteration_card.set_batch_state(
                1, 1, max(1, self.batch_count), False, False, self.auto_mixed)
            self.stage.reset_batch(self.auto_mixed, "forward")
            self._set_status("多次迭代 · 设置次数后点正向或反向按钮", "idle")
        else:
            self._set_status("单次混淆 · 点击正向或反向按钮处理一张", "idle")
        self._update_steps()
        self._refresh_controls()

    def _on_auto_change(self, value: bool) -> None:
        if self._busy or self.iteration_mode != "batch":
            self.auto_mixed = False
            self.iteration_card.set_auto(False)
            return
        self.auto_mixed = bool(value)
        self.iteration_card.set_auto(self.auto_mixed)
        self.action_row.set_mode("batch", self.auto_mixed)
        self.stage.set_mode("batch", self.auto_mixed)
        self.result_image = None
        self.stage.reset_result()
        self._reset_batch_state(clear_view=False)
        self.stage.reset_batch(self.auto_mixed, "forward")
        if self.auto_mixed:
            self._set_status("正反自动混淆已开启 · 点击自动混淆开始", "idle")
        else:
            self._set_status("正反自动混淆已关闭 · 批次已重置", "idle")
        self._update_steps()
        self._refresh_controls()

    def _on_batch_count_changed(self, *_args) -> None:
        if self.iteration_mode != "batch" or self._busy:
            return
        try:
            count = int(self.iteration_card.count_var.get())
        except ValueError:
            return
        if not 1 <= count <= MAX_BATCH_COUNT or count == self.batch_count:
            return
        self.batch_count = count
        self._reset_batch_state()
        self._set_status(f"等差迭代次数已设为 {count} · 批次已重置", "idle")
        self._refresh_controls()

    def _on_batch_param_changed(self, *_args) -> None:
        if self.iteration_mode != "batch" or self._busy:
            return
        has_partial = bool(self.batch_results["reverse"]
                           or self.batch_results["forward"])
        if not self.batch_has_results and not has_partial and self.batch_index == 1:
            return
        self._reset_batch_state()
        self._set_status("参数已变更 · 批次已重置", "idle")
        self._refresh_controls()

    # ------------------------------------------------------------ transforms
    def _on_direction(self, action: str) -> None:
        if self.iteration_mode == "batch":
            if self.auto_mixed:
                return
            self._run_batch((action,), 1, 1)
            return
        self._transform(action)

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
        label = "反向混淆" if action == "restore" else "正向混淆"
        self._operation = "transform"
        self._set_status(f"正在{label}…", "busy")
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

    def _run_batch(self, actions: tuple[str, ...], start: int, index: int) -> None:
        if self.source_image is None or self._busy:
            return
        if self.iteration_mode != "batch":
            return
        count_text = self.iteration_card.count_var.get()
        iterations_text, offset_text, a_text, b_text = (
            self.params_card.parameter_text()
        )
        del iterations_text  # The batch count replaces the single-run field.
        try:
            request = build_batch_request(
                self.method,
                actions,
                start,
                count_text,
                offset_text,
                a_text,
                b_text,
                width=self.source_image.width,
                height=self.source_image.height,
            )
        except ValueError as error:
            messagebox.showerror(
                "参数有误",
                f"请检查等差迭代次数和算法参数。\n\n{error}",
                parent=self,
            )
            return

        count = request.count
        self.batch_count = count
        self.batch_start = start
        self.batch_index = index
        self.batch_direction = (self._direction_for(actions[0])
                                if len(actions) == 1 else None)
        self.batch_results = {"reverse": [], "forward": []}
        self.batch_has_results = False
        self.result_image = None
        self._operation = "batch"
        self._set_status(
            f"正在生成第 {index} 批 · {start}–{request.end} 次…", "busy")
        self._set_source_pill("处理中", "busy")
        self.stage.begin_batch(
            auto=self.auto_mixed,
            direction=self.batch_direction or "forward",
            index=index,
            start=start,
            count=count,
        )
        self._busy = True
        self._update_steps()
        self._refresh_controls()

        image = self.source_image
        total = len(actions) * count

        def task():
            started = time.perf_counter()
            completed = 0
            for offset_index in range(count):
                iteration = start + offset_index
                for action in actions:
                    direction = self._direction_for(action)
                    label = "反向混淆" if direction == "reverse" else "正向混淆"

                    def report(fraction, _text, done=completed,
                               current=iteration, current_label=label):
                        self._runner.report_progress(
                            (done + max(0.0, min(1.0, fraction))) / total,
                            f"{current_label} · 第 {current} 次",
                        )

                    result = self._engine.apply(
                        image,
                        request.method,
                        action,
                        iteration,
                        request.offset,
                        request.a,
                        request.b,
                        report,
                    )
                    thumbnail = result.copy()
                    thumbnail.thumbnail((240, 240), Image.Resampling.LANCZOS)
                    self._runner.emit("batch_item",
                                      BatchItem(direction, iteration, thumbnail))
                    completed += 1
                    self._runner.report_progress(
                        completed / total,
                        f"{label} · 第 {iteration} 次",
                    )
            return ("batch", index, start, count, actions,
                    time.perf_counter() - started)

        self._start_worker(task, already_busy=True)

    def _on_next_batch(self) -> None:
        if (self.iteration_mode != "batch" or self.auto_mixed or self._busy
                or not self.batch_has_results):
            return
        direction = self.batch_direction or "forward"
        action = "restore" if direction == "reverse" else "scramble"
        self._run_batch((action,), self._next_batch_start(), self.batch_index + 1)

    def _on_auto_batch(self) -> None:
        if (self.iteration_mode != "batch" or not self.auto_mixed
                or self._busy):
            return
        self._run_batch(("restore", "scramble"), 1, 1)

    def _on_auto_next_batch(self) -> None:
        if (self.iteration_mode != "batch" or not self.auto_mixed
                or self._busy or not self.batch_has_results):
            return
        self._run_batch(("restore", "scramble"), self._next_batch_start(),
                        self.batch_index + 1)

    @staticmethod
    def _direction_for(action: str) -> str:
        return "reverse" if action == "restore" else "forward"

    # ------------------------------------------------------------ previews
    def _open_batch_preview(self, item: BatchItem) -> None:
        if self._busy or self.source_image is None:
            return
        self._close_preview()
        self._preview_token += 1
        token = self._preview_token
        self._preview_meta = (item.direction, item.iteration)
        batch_text = (f"第 {self.batch_index} 批 · {self.batch_start}–"
                      f"{self._batch_end()} 次")
        self._preview = ResultPreview(
            self,
            direction=item.direction,
            iteration=item.iteration,
            batch_text=batch_text,
            thumbnail=item.thumbnail,
            dims_text=f"{self.source_image.width} × {self.source_image.height}",
            on_use=self._use_batch_result,
            on_save=self._save_preview_image,
            on_close=self._on_preview_closed,
        )
        self._operation = "preview"
        self._set_status(f"正在生成第 {item.iteration} 次预览…", "busy")
        self._busy = True
        self._update_steps()
        self._refresh_controls()

        image = self.source_image
        direction = item.direction
        iteration = item.iteration
        method = self.method
        _, offset_text, a_text, b_text = self.params_card.parameter_text()

        def task():
            action = "restore" if direction == "reverse" else "scramble"
            request = build_transform_request(
                method,
                action,
                str(iteration),
                offset_text,
                a_text,
                b_text,
                width=image.width,
                height=image.height,
            )
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
            return ("preview", token, result, time.perf_counter() - started)

        self._start_worker(task, already_busy=True)

    def _use_batch_result(self, image: Image.Image) -> None:
        meta = self._preview_meta
        if meta is None:
            return
        direction, iteration = meta
        label = "反向" if direction == "reverse" else "正向"
        self._set_source(image, name=f"第{iteration}次{label}结果.png")
        self._set_status(f"已将第 {iteration} 次{label}结果作为输入", "ok")

    def _save_preview_image(self, image: Image.Image) -> None:
        meta = self._preview_meta
        if meta is None:
            return
        direction, iteration = meta
        suffix = f"{direction}_{iteration}"
        self._save_image(image, suffix=suffix, preview=self._preview)

    def _on_preview_closed(self) -> None:
        if self._save_preview is self._preview:
            self._save_preview = None
        self._preview = None
        self._preview_meta = None
        self._preview_token += 1
        if not self._busy:
            self._refresh_controls()

    def _close_preview(self) -> None:
        preview = self._preview
        if preview is None:
            return
        try:
            preview.close()
        except tk.TclError:
            self._preview = None
            self._preview_meta = None
            self._preview_token += 1

    # ------------------------------------------------------------ saving
    def _save(self) -> None:
        if self.result_image is None or self._busy:
            return
        suffix = "reverse" if self.result_action == "reverse" else "forward"
        self._save_image(self.result_image, suffix=suffix)

    def _save_image(self, image: Image.Image, *, suffix: str,
                    preview: ResultPreview | None = None) -> None:
        path = filedialog.asksaveasfilename(
            parent=preview or self,
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
                parent=preview or self,
            )
            return
        self._operation = "save"
        self._save_preview = preview
        self._set_status("正在保存 PNG…", "busy")
        if preview is not None:
            preview.set_status("正在保存 PNG…", "busy")
            preview.set_actions_enabled(False)
        self._start_worker(lambda: self._save_task(image, path))

    @staticmethod
    def _save_task(image: Image.Image, path: str):
        save_png(image, path)
        return "saved", path

    # ------------------------------------------------------------ workers
    def _start_worker(self, task, *, already_busy: bool = False) -> None:
        if self._busy and not already_busy:
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
            elif kind == "batch_item":
                item = payload
                self.batch_results[item.direction].append(item)
                self.stage.append_batch_item(item)
            elif kind == "error":
                self._handle_error(payload)
            elif kind == "done":
                self._handle_done(payload)
        self._poll_job = self.after(60, self._poll_events)

    def _handle_done(self, payload) -> None:
        self._busy = False
        self._operation = None
        kind = payload[0]
        if kind == "source":
            self._set_source(payload[1], payload[2])
        elif kind == "result":
            _, image, action, label, elapsed = payload
            self.result_image = image
            self.result_action = "reverse" if action == "restore" else "forward"
            self.stage.show_result(image)
            self._set_source_pill("已载入", "loaded")
            self.stage.set_progress(1.0)
            self._set_status(
                f"{label}完成 · {image.width} × {image.height} · {elapsed:.2f} 秒",
                "ok",
            )
        elif kind == "batch":
            _, index, start, count, actions, elapsed = payload
            self.batch_start = start
            self.batch_index = index
            self.batch_count = count
            self.batch_has_results = bool(
                self.batch_results["reverse"] or self.batch_results["forward"])
            self.stage.finish_batch(auto=self.auto_mixed, index=index,
                                    start=start, count=count)
            self.stage.set_progress(1.0)
            self._set_source_pill("已载入", "loaded")
            if len(actions) == 2:
                summary = f"正反各 {count} 张"
            else:
                summary = f"{count} 张"
            self._set_status(
                f"第 {index} 批完成 · {start}–{start + count - 1} 次 · "
                f"{summary} · {elapsed:.2f} 秒",
                "ok",
            )
        elif kind == "preview":
            _, token, image, elapsed = payload
            if token == self._preview_token and self._preview is not None:
                self._preview.set_image(image)
                self.stage.set_progress(1.0)
                meta = self._preview_meta
                iteration = meta[1] if meta else 0
                self._set_status(
                    f"第 {iteration} 次预览已生成 · {elapsed:.2f} 秒", "ok")
            else:
                self._set_status("预览已关闭", "idle")
        elif kind == "saved":
            path = payload[1]
            self.stage.set_progress(1.0)
            self._set_status(f"已保存 · {Path(path).name}", "ok")
            if self._save_preview is not None:
                try:
                    self._save_preview.set_status(
                        f"已保存 · {Path(path).name}", "ok")
                    self._save_preview.set_actions_enabled(True)
                except tk.TclError:
                    pass
                self._save_preview = None
        self._update_steps()
        self._refresh_controls()

    def _handle_error(self, message: str) -> None:
        operation = self._operation
        self._operation = None
        self._busy = False
        self.stage.set_progress(0)
        if operation == "preview":
            if self._preview is not None:
                self._preview.set_error(message)
            self._set_status("预览生成未完成 · 请检查参数", "error")
            self._update_steps()
            self._refresh_controls()
            return
        if operation == "save":
            if self._save_preview is not None:
                try:
                    self._save_preview.set_status("保存失败", "error")
                    self._save_preview.set_actions_enabled(True)
                except tk.TclError:
                    pass
                self._save_preview = None
            self._set_status("保存未完成 · 请检查目标路径", "error")
            self._update_steps()
            self._refresh_controls()
            parent = self._preview or self
            messagebox.showerror("保存失败", message, parent=parent)
            return
        if operation == "batch":
            self.batch_has_results = False
            self.stage.finish_batch(auto=self.auto_mixed,
                                    index=self.batch_index,
                                    start=self.batch_start,
                                    count=max(1, self.batch_count))
            self._set_source_pill("已载入", "loaded")
            self._set_status("批量处理未完成 · 请检查输入图片或参数", "error")
        elif operation == "transform":
            if self.result_image is not None:
                self.stage.show_result(self.result_image)
            else:
                self._show_empty_result()
            self._set_source_pill("已载入", "loaded")
            self._set_status("操作未完成 · 请检查输入图片或参数", "error")
        elif self.source_image is not None:
            self._set_source_pill("已载入", "loaded")
            self._set_status("操作未完成 · 请检查输入图片或参数", "error")
        else:
            self._set_source_pill("未选择", "idle")
            self._set_status("操作未完成 · 请选择图片或检查参数", "error")
        self._update_steps()
        self._refresh_controls()
        messagebox.showerror("操作失败", message, parent=self)

    # ------------------------------------------------------------ misc
    def _show_help(self) -> None:
        messagebox.showinfo(
            "使用说明",
            "选择一张普通图片，或使用内置测试图。\n\n"
            "Gilbert 支持任意宽高；Arnold 需要正方形图片。\n"
            "正向混淆和反向混淆是同一置换的两个方向，反向混淆即复原。\n"
            "对未混淆的图片点反向混淆，也会得到一张混淆图，这是正常现象。\n\n"
            "单次混淆：按上方次数处理一张。\n"
            "多次迭代：从 1 到 N 生成整批结果；可开启正反自动混淆，"
            "同时查看反向和正向结果集。\n"
            "结果缩略图可点开预览，再选择用作输入或保存 PNG。\n\n"
            "两个方向请使用相同的次数与参数。\n\n"
            "所有处理都在本机完成，不会上传任何文件。",
            parent=self,
        )

    def _close(self) -> None:
        if self._poll_job:
            try:
                self.after_cancel(self._poll_job)
            except tk.TclError:
                pass
        self._close_preview()
        self.page.cancel_pending()
        self.destroy()


__all__ = ["App"]

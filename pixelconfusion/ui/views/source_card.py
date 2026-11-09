"""Full-width source strip below the application header."""

from __future__ import annotations

import tkinter as tk

from pixelconfusion.ui.text import ellipsize, make_label
from pixelconfusion.ui.theme import BG, FAINT, LINE_STRONG, MUTED, PINK, SURFACE
from pixelconfusion.ui.widgets import Card, DropZone, IconButton, Pill, TextLink


class SourceCard(Card):
    def __init__(self, master, *, on_pick, on_clear, on_demo, outer_bg=BG):
        super().__init__(master, height=100, outer_bg=outer_bg)
        self._thumb_photo = None

        body = tk.Frame(self.content, bg=SURFACE, height=64)
        body.pack(fill="both", expand=True, padx=6, pady=6)
        body.pack_propagate(False)

        title_block = tk.Frame(body, bg=SURFACE, width=96)
        title_block.pack(side="left", fill="y", padx=(0, 12))
        title_block.pack_propagate(False)
        make_label(title_block, "来源图片", 9, "bold").pack(anchor="w", pady=(7, 0))
        self.source_pill = Pill(title_block, "未选择", bg="#35373b", fg=MUTED,
                                dot=FAINT, height=20, border=LINE_STRONG)
        self.source_pill.pack(anchor="w", pady=(4, 0))

        self.demo_link = TextLink(body, "使用内置测试图", command=on_demo,
                                  outer_bg=SURFACE)
        self.demo_link.pack(side="right", pady=(21, 0))

        self.content_area = tk.Frame(body, bg=SURFACE)
        self.content_area.pack(side="left", fill="both", expand=True)

        self.dropzone = DropZone(self.content_area, command=on_pick,
                                 outer_bg=SURFACE, compact=True)
        self.loaded_row = tk.Frame(self.content_area, bg=SURFACE)
        self.thumb_label = tk.Label(self.loaded_row, bg=SURFACE, bd=0)
        self.thumb_label.pack(side="left", padx=(0, 12), pady=4)
        info = tk.Frame(self.loaded_row, bg=SURFACE)
        info.pack(side="left", fill="both", expand=True, padx=(0, 10))
        self.file_name_label = make_label(info, "", 9, "bold", anchor="w",
                                          justify="left")
        self.file_name_label.pack(anchor="w", pady=(8, 0))
        self.file_meta_label = make_label(info, "", 8, fg=FAINT, anchor="w")
        self.file_meta_label.pack(anchor="w", pady=(3, 0))
        actions = tk.Frame(self.loaded_row, bg=SURFACE)
        actions.pack(side="right", fill="y")
        self.replace_button = IconButton(actions, "upload", command=on_pick, size=24,
                                         icon_size=14, tooltip="更换图片",
                                         outer_bg=SURFACE)
        self.replace_button.pack(side="left", pady=20)
        self.clear_button = IconButton(actions, "x", command=on_clear, size=24,
                                       icon_size=14, tooltip="清空图片",
                                       outer_bg=SURFACE)
        self.clear_button.pack(side="left", padx=(3, 0), pady=20)

        self.show_empty()

    def show_empty(self) -> None:
        if not self.dropzone.winfo_manager():
            self.dropzone.pack(fill="both", expand=True)
        self.loaded_row.pack_forget()
        self._thumb_photo = None
        self.thumb_label.configure(image="")
        self.demo_link.set_text("使用内置测试图")

    def show_loaded(self, photo, name: str, meta: str) -> None:
        self._thumb_photo = photo
        self.thumb_label.configure(image=photo)
        self.file_name_label.configure(text=ellipsize(name, 300, 9, "bold"))
        self.file_meta_label.configure(text=ellipsize(meta, 360, 8))
        self.dropzone.pack_forget()
        self.loaded_row.pack(fill="both", expand=True)
        self.demo_link.set_text("换成内置测试图")

    def set_pill(self, text: str, tone: str) -> None:
        if tone == "loaded":
            self.source_pill.update_pill(text, bg="#2f405c", fg="#cfe0ff",
                                         dot="#4d8df7", border="#47709f")
        elif tone == "busy":
            self.source_pill.update_pill(text, bg="#3a3322", fg=PINK,
                                         dot=PINK, border="#5c4a22")
        else:
            self.source_pill.update_pill(text, bg="#35373b", fg=MUTED,
                                         dot=FAINT, border=LINE_STRONG)

    def set_enabled(self, enabled: bool) -> None:
        self.dropzone.set_enabled(enabled)
        self.demo_link.set_enabled(enabled)
        self.replace_button.set_enabled(enabled)
        self.clear_button.set_enabled(enabled)


__all__ = ["SourceCard"]

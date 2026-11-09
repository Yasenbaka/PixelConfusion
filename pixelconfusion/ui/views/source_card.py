"""Full-width source strip below the application header."""

from __future__ import annotations

import tkinter as tk

from pixelconfusion.ui.text import ellipsize, make_label
from pixelconfusion.ui.theme import BG, FAINT, LINE_STRONG, MUTED, PINK, SURFACE
from pixelconfusion.ui.widgets import (
    Card,
    DropZone,
    IconButton,
    Pill,
    PillButton,
    TextLink,
)

_LOADED_DOT = "#4d8df7"


class SourceCard(Card):
    def __init__(self, master, *, on_pick, on_clear, on_demo, outer_bg=BG):
        super().__init__(master, height=92, outer_bg=outer_bg)
        self._thumb_photo = None
        self._enabled = True
        self._loaded = False
        self._on_pick = on_pick

        body = tk.Frame(self.content, bg=SURFACE)
        body.pack(fill="both", expand=True, padx=(12, 12))
        body.grid_rowconfigure(0, weight=1)
        body.grid_columnconfigure(1, weight=1)

        self.thumb_label = tk.Label(body, bg=SURFACE, bd=0)
        self.thumb_label.bind("<ButtonRelease-1>", self._thumb_clicked)

        info = tk.Frame(body, bg=SURFACE)
        self._info = info
        make_label(info, "来源图片", 7, fg=FAINT).pack(anchor="w")
        name_row = tk.Frame(info, bg=SURFACE)
        name_row.pack(anchor="w", pady=(2, 0))
        self.file_name_label = make_label(name_row, "", 9, "bold", anchor="w",
                                          justify="left")
        self.file_name_label.pack(side="left")
        self.state_tag = Pill(name_row, "已载入", bg=SURFACE, fg=MUTED,
                              dot=_LOADED_DOT, height=18, pad=1,
                              border=SURFACE)
        self.state_tag.pack(side="left", padx=(9, 0))
        self.file_meta_label = make_label(info, "", 8, fg=FAINT, anchor="w")
        self.file_meta_label.pack(anchor="w", pady=(3, 0))

        self.dropzone = DropZone(body, command=on_pick, outer_bg=SURFACE,
                                 compact=True)

        actions = tk.Frame(body, bg=SURFACE)
        actions.grid(row=0, column=2, sticky="e", padx=(16, 2))
        self.replace_button = PillButton(actions, "更换图片", command=on_pick,
                                         icon="upload", kind="secondary",
                                         small=True, height=30, outer_bg=SURFACE)
        self.clear_button = IconButton(actions, "x", command=on_clear, size=30,
                                       icon_size=15, tooltip="清空图片",
                                       outer_bg=SURFACE)
        self._divider = tk.Frame(actions, bg=LINE_STRONG, width=1, height=22)
        self.demo_link = TextLink(actions, "使用内置测试图", command=on_demo,
                                  outer_bg=SURFACE)

        self.show_empty()

    def show_empty(self) -> None:
        self._loaded = False
        self.thumb_label.grid_remove()
        self._info.grid_remove()
        self._pack_file_actions(False)
        self.dropzone.grid(row=0, column=0, columnspan=2, sticky="nsew")
        self._thumb_photo = None
        self.thumb_label.configure(image="")
        self.thumb_label.configure(cursor="")
        self.demo_link.set_text("使用内置测试图")

    def show_loaded(self, photo, name: str, meta: str) -> None:
        self._loaded = True
        self._thumb_photo = photo
        self.thumb_label.configure(image=photo)
        self.file_name_label.configure(text=ellipsize(name, 480, 9, "bold"))
        self.file_meta_label.configure(text=ellipsize(meta, 360, 8))
        self.dropzone.grid_remove()
        self.thumb_label.grid(row=0, column=0, sticky="w", padx=(2, 12))
        self._info.grid(row=0, column=1, sticky="ew")
        self._pack_file_actions(True)
        self.thumb_label.configure(cursor="hand2" if self._enabled else "")
        self.demo_link.set_text("换成内置测试图")

    def set_state(self, text: str, tone: str) -> None:
        if tone == "loaded":
            foreground, dot = MUTED, _LOADED_DOT
        elif tone == "busy":
            foreground, dot = PINK, PINK
        else:
            foreground, dot = MUTED, FAINT
        self.state_tag.update_pill(text, bg=SURFACE, fg=foreground, dot=dot,
                                   border=SURFACE)

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = bool(enabled)
        self.dropzone.set_enabled(self._enabled)
        self.demo_link.set_enabled(self._enabled)
        self.replace_button.set_enabled(self._enabled)
        self.clear_button.set_enabled(self._enabled)
        self.thumb_label.configure(
            cursor="hand2" if self._enabled and self._loaded else "")

    # --------------------------------------------------------------- private
    def _pack_file_actions(self, visible: bool) -> None:
        if visible:
            self.replace_button.pack(side="left", before=self.demo_link)
            self.clear_button.pack(side="left", padx=(6, 0),
                                   before=self.demo_link)
            self._divider.pack(side="left", padx=(13, 13), pady=(4, 0),
                               before=self.demo_link)
        else:
            self.replace_button.pack_forget()
            self.clear_button.pack_forget()
            self._divider.pack_forget()
            if not self.demo_link.winfo_manager():
                self.demo_link.pack(side="left", pady=(4, 0))

    def _thumb_clicked(self, _event) -> None:
        if self._enabled and self._loaded and self._on_pick:
            self._on_pick()


__all__ = ["SourceCard"]

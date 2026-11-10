#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Launcher for the PixelConfusion desktop application."""

from __future__ import annotations

import sys
import tkinter as tk
from pathlib import Path
from tkinter import messagebox

from pixelconfusion.console import use_utf8_output
from pixelconfusion.version import (
    APP_TITLE,
    VERSION,
    version_components,
)

VERSION_FLAGS = frozenset({"--version", "-V"})


def _attach_console() -> bool:
    """Make stdout usable in a windowed build by joining the parent console."""
    if getattr(sys.stdout, "write", None) is not None:
        return True
    if sys.platform != "win32":
        return False
    try:
        import ctypes

        if not ctypes.windll.kernel32.AttachConsole(-1):
            return False
        sys.stdout = open("CONOUT$", "w", encoding="utf-8", buffering=1)
        sys.stderr = open("CONOUT$", "w", encoding="utf-8", buffering=1)
    except OSError:
        return False
    return True


def _show_version() -> int:
    """Print the version, or show it in a dialog when no console exists."""
    if _attach_console() and getattr(sys.stdout, "write", None) is not None:
        use_utf8_output()
        try:
            print(f"{APP_TITLE} {VERSION}")
            print(f"版本 {VERSION}（{version_components()}）")
        except OSError:
            pass
        return 0
    root = tk.Tk()
    root.withdraw()
    messagebox.showinfo(
        "版本信息",
        f"{APP_TITLE}\n\n版本 {VERSION}（{version_components()}）\n\n"
        "本地图片混淆与复原工具，所有处理都在本机完成。",
        parent=root,
    )
    root.destroy()
    return 0


def _report_missing_dependency(error: ImportError) -> None:
    command = (
        f'"{sys.executable}" -m pip install -r '
        f'"{Path(__file__).with_name("requirements.txt")}"'
    )
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror(
        "缺少依赖",
        f"请在终端执行以下命令后重新启动：\n\n{command}\n\n{error}",
        parent=root,
    )
    root.destroy()


def main(argv: list[str] | None = None) -> int:
    arguments = sys.argv[1:] if argv is None else list(argv)
    if any(argument in VERSION_FLAGS for argument in arguments):
        return _show_version()
    try:
        from pixelconfusion.app import App
    except ImportError as error:
        _report_missing_dependency(error)
        return 1
    App().mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

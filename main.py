#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Launcher for the PixelConfusion desktop application."""

from __future__ import annotations

import sys
import tkinter as tk
from pathlib import Path
from tkinter import messagebox


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


def main() -> int:
    try:
        from pixelconfusion.app import App
    except ImportError as error:
        _report_missing_dependency(error)
        return 1
    App().mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

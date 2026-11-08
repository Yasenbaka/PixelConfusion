"""Native window-chrome helpers."""

from __future__ import annotations

import sys
import tkinter as tk


def apply_dark_title_bar(window: tk.Tk) -> None:
    """Ask the Windows DWM for a dark title bar; ignore unsupported systems."""
    if sys.platform != "win32":
        return
    try:
        import ctypes

        hwnd = ctypes.windll.user32.GetParent(window.winfo_id())
        enabled = ctypes.c_int(1)
        for attribute in (20, 19):
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, attribute, ctypes.byref(enabled), ctypes.sizeof(enabled))
    except Exception:  # noqa: BLE001 - purely cosmetic best effort
        pass


__all__ = ["apply_dark_title_bar"]

"""Console output helpers shared by the launcher and the build script."""

from __future__ import annotations

import sys


def use_utf8_output() -> None:
    """Prefer UTF-8 for redirected output so Chinese logs stay readable.

    The Windows console itself already uses Unicode; this only affects pipes
    and files, where Python otherwise falls back to the legacy code page.
    """
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(encoding="utf-8")
        except (OSError, ValueError):
            pass


__all__ = ["use_utf8_output"]

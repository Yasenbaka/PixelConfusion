"""Display helpers that do not depend on Tkinter."""

from __future__ import annotations


def human_size(size: int) -> str:
    """Format a byte count for the source-image metadata line."""
    if size < 1024:
        return f"{size} B"
    if size < 1024 * 1024:
        return f"{size / 1024:.0f} KB"
    return f"{size / 1024 / 1024:.1f} MB"


__all__ = ["human_size"]

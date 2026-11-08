"""Rounded-canvas primitives shared by the custom widgets."""

from __future__ import annotations

import math
import tkinter as tk


def rounded_points(x1: float, y1: float, x2: float, y2: float, radius: float,
                   steps: int = 9) -> list[float]:
    radius = max(0, min(radius, (x2 - x1) / 2, (y2 - y1) / 2))
    points: list[float] = []
    corners = (
        (x2 - radius, y1 + radius, -90),
        (x2 - radius, y2 - radius, 0),
        (x1 + radius, y2 - radius, 90),
        (x1 + radius, y1 + radius, 180),
    )
    for cx, cy, start in corners:
        for index in range(steps + 1):
            angle = math.radians(start + 90 * index / steps)
            points.extend((cx + radius * math.cos(angle), cy + radius * math.sin(angle)))
    return points


def draw_round(canvas: tk.Canvas, x1, y1, x2, y2, radius, fill, outline="",
               width=1, tags=""):
    return canvas.create_polygon(*rounded_points(x1, y1, x2, y2, radius),
                                 fill=fill, outline=outline or fill, width=width,
                                 smooth=False, tags=tags)


def dashed_round(canvas: tk.Canvas, x1, y1, x2, y2, radius, color, dash=(5, 4),
                 tags=""):
    points = rounded_points(x1, y1, x2, y2, radius)
    points.extend(points[:2])
    return canvas.create_line(*points, fill=color, width=1, dash=dash, tags=tags)


__all__ = ["dashed_round", "draw_round", "rounded_points"]

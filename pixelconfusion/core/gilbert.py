"""Gilbert curve generation and permutation.

The subdivision is adapted from Jakub Červený's gilbert2d (2018).
SPDX-License-Identifier for the adapted subdivision: BSD-2-Clause.
See THIRD_PARTY_NOTICES.txt for the copyright and full license.
"""

from __future__ import annotations

import math
from functools import lru_cache

import numpy as np

from pixelconfusion.core.common import Progress

GOLDEN_RATIO = (math.sqrt(5) - 1) / 2


def _children(x, y, ax, ay, bx, by):
    w, h = abs(ax + ay), abs(bx + by)
    dax, day = (ax > 0) - (ax < 0), (ay > 0) - (ay < 0)
    dbx, dby = (bx > 0) - (bx < 0), (by > 0) - (by < 0)
    # Floor division also matches JavaScript's signed >> 1 for odd negatives.
    ax2, ay2, bx2, by2 = ax // 2, ay // 2, bx // 2, by // 2
    if 2 * w > 3 * h:
        if abs(ax2 + ay2) % 2 and w > 2:
            ax2, ay2 = ax2 + dax, ay2 + day
        return (
            (x, y, ax2, ay2, bx, by),
            (x + ax2, y + ay2, ax - ax2, ay - ay2, bx, by),
        )
    if abs(bx2 + by2) % 2 and h > 2:
        bx2, by2 = bx2 + dbx, by2 + dby
    return (
        (x, y, bx2, by2, ax2, ay2),
        (x + bx2, y + by2, ax, ay, bx - bx2, by - by2),
        (
            x + ax - dax + bx2 - dbx,
            y + ay - day + by2 - dby,
            -bx2,
            -by2,
            -(ax - ax2),
            -(ay - ay2),
        ),
    )


def _points(x, y, ax, ay, bx, by):
    w, h = abs(ax + ay), abs(bx + by)
    if h == 1 or w == 1:
        vx, vy = (ax, ay) if h == 1 else (bx, by)
        dx, dy = (vx > 0) - (vx < 0), (vy > 0) - (vy < 0)
        for i in range(w * h):
            yield x + i * dx, y + i * dy
        return
    for child in _children(x, y, ax, ay, bx, by):
        yield from _points(*child)


def gilbert_order(width: int, height: int, progress: Progress | None = None):
    """A permutation of row-major pixel indices for any positive dimensions."""
    if width <= 0 or height <= 0:
        raise ValueError("图片宽高必须大于 0。")
    total = width * height
    dtype = np.int32 if total < 2**31 else np.int64
    order = np.empty(total, dtype=dtype)
    cursor = 0
    reported = -1

    @lru_cache(maxsize=256)
    def local_path(ax, ay, bx, by):
        return np.fromiter(
            (x + y * width for x, y in _points(0, 0, ax, ay, bx, by)),
            dtype=dtype,
            count=abs(ax + ay) * abs(bx + by),
        )

    def fill(x, y, ax, ay, bx, by):
        nonlocal cursor, reported
        w, h = abs(ax + ay), abs(bx + by)
        count = w * h
        if w == 1 or h == 1:
            vx, vy = (ax, ay) if h == 1 else (bx, by)
            dx, dy = (vx > 0) - (vx < 0), (vy > 0) - (vy < 0)
            order[cursor:cursor + count] = (
                x + y * width + np.arange(count, dtype=dtype) * (dx + dy * width)
            )
            cursor += count
        elif count <= 4096:
            order[cursor:cursor + count] = local_path(ax, ay, bx, by) + (x + y * width)
            cursor += count
        else:
            for child in _children(x, y, ax, ay, bx, by):
                fill(*child)
        percent = cursor * 100 // total
        if progress and percent > reported:
            reported = percent
            progress(cursor / total, "生成 Gilbert 曲线路径")

    if width >= height:
        fill(0, 0, width, 0, 0, height)
    else:
        fill(0, 0, 0, height, width, 0)
    if cursor != total:
        raise RuntimeError("曲线路径长度异常。")
    return order


def default_offset(total: int) -> int:
    """JavaScript Math.round(phi * total), without Python's ties-to-even."""
    return math.floor(GOLDEN_RATIO * total + 0.5)


def gilbert_transform(pixels, order, shift: int, progress: Progress | None = None):
    """out[curve[i]] = in[curve[(i + shift) % total]]."""
    height, width, channels = pixels.shape
    total = width * height
    if order.shape != (total,):
        raise ValueError("曲线尺寸与图片不一致。")
    source = pixels.reshape(total, channels)
    output = np.empty_like(source)
    shift = int(shift) % total
    for start in range(0, total, 500_000):
        end = min(start + 500_000, total)
        indices = (np.arange(start, end, dtype=np.int64) + shift) % total
        output[order[start:end]] = source[order[indices]]
        if progress:
            progress(end / total, "重排像素")
    return output.reshape(height, width, channels)


__all__ = ["GOLDEN_RATIO", "default_offset", "gilbert_order", "gilbert_transform"]

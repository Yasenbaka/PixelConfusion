"""Pure image permutations, independent of the desktop interface.

Gilbert subdivision is adapted from Jakub Červený's gilbert2d (2018).
SPDX-License-Identifier for the adapted subdivision: BSD-2-Clause.
See THIRD_PARTY_NOTICES.txt for the copyright and full license.
"""

from __future__ import annotations

import math
from functools import lru_cache
from typing import Callable

import numpy as np
from PIL import Image

Progress = Callable[[float, str], None]
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
        (x + ax - dax + bx2 - dbx, y + ay - day + by2 - dby,
         -bx2, -by2, -(ax - ax2), -(ay - ay2)),
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


def _matrix_multiply(left, right, modulus):
    a, b, c, d = left
    e, f, g, h = right
    return ((a * e + b * g) % modulus, (a * f + b * h) % modulus,
            (c * e + d * g) % modulus, (c * f + d * h) % modulus)


def arnold_matrix(size: int, iterations: int, a: int = 1, b: int = 1):
    """Power of [[1, a], [b, ab+1]] modulo size; negative powers are inverse."""
    if size <= 0:
        raise ValueError("图片边长必须大于 0。")
    matrix = (1, a, b, a * b + 1)
    if iterations < 0:
        matrix = (a * b + 1, -a, -b, 1)
    matrix = tuple(value % size for value in matrix)
    result = (1 % size, 0, 0, 1 % size)
    exponent = abs(iterations)
    while exponent:
        if exponent & 1:
            result = _matrix_multiply(result, matrix, size)
        matrix = _matrix_multiply(matrix, matrix, size)
        exponent >>= 1
    return result


def arnold_transform(pixels, iterations: int, a: int = 1, b: int = 1,
                     progress: Progress | None = None):
    """Positive iterations restore the forward Arnold coordinate permutation."""
    height, width, _ = pixels.shape
    if width != height:
        raise ValueError("标准 Arnold 猫映射需要正方形图片，请选择 Gilbert 或更换图片。")
    aa, bb, cc, dd = arnold_matrix(width, iterations, a, b)
    output = np.empty_like(pixels)
    x = np.arange(width, dtype=np.int64)[None, :]
    for start in range(0, height, 128):
        end = min(start + 128, height)
        y = np.arange(start, end, dtype=np.int64)[:, None]
        source_x = (aa * x + bb * y) % width
        source_y = (cc * x + dd * y) % height
        output[start:end] = pixels[source_y, source_x]
        if progress:
            progress(end / height, "重排 Arnold 像素")
    return output


class Transformer:
    """Cache only the most recent Gilbert path to bound retained memory."""

    def __init__(self):
        self._size = None
        self._order = None

    def apply(self, image: Image.Image, method="gilbert", action="restore",
              iterations=1, offset=None, a=1, b=1, progress: Progress | None = None):
        if not isinstance(iterations, int) or iterations < 1:
            raise ValueError("次数必须是大于 0 的整数。")
        if action not in ("restore", "scramble"):
            raise ValueError("未知操作。")
        if method not in ("gilbert", "arnold"):
            raise ValueError("未知算法。")
        pixels = np.array(image.convert("RGBA"))
        height, width, _ = pixels.shape
        signed_iterations = iterations if action == "restore" else -iterations
        if method == "gilbert":
            if self._size != (width, height):
                self._order = None
                self._size = None
                callback = (lambda n, text: progress(n * 0.35, text)) if progress else None
                self._order = gilbert_order(width, height, callback)
                self._size = (width, height)
            offset = default_offset(width * height) if offset is None else int(offset)
            callback = (lambda n, text: progress(0.35 + n * 0.65, text)) if progress else None
            result = gilbert_transform(pixels, self._order, signed_iterations * offset, callback)
        else:
            result = arnold_transform(pixels, signed_iterations, int(a), int(b), progress)
        output = Image.fromarray(result)
        for key in ("icc_profile", "dpi"):
            if key in image.info:
                output.info[key] = image.info[key]
        return output


def load_image(path) -> Image.Image:
    with Image.open(path) as image:
        if getattr(image, "n_frames", 1) != 1:
            raise ValueError("请选择单帧图片，暂不处理动图或多页图片。")
        if image.mode.startswith("I") or image.mode == "F":
            raise ValueError("请选择常见的 8 位 PNG/JPEG 图片，暂不处理高位深图片。")
        image.load()
        output = image.convert("RGBA")
        for key in ("icc_profile", "dpi"):
            if key in image.info:
                output.info[key] = image.info[key]
        return output


def save_png(image: Image.Image, path):
    options = {key: image.info[key] for key in ("icc_profile", "dpi") if key in image.info}
    image.save(path, format="PNG", **options)

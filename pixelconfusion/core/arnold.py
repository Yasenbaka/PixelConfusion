"""Arnold cat-map matrix maths and pixel permutation."""

from __future__ import annotations

import numpy as np

from pixelconfusion.core.common import Progress


def _matrix_multiply(left, right, modulus):
    a, b, c, d = left
    e, f, g, h = right
    return (
        (a * e + b * g) % modulus,
        (a * f + b * h) % modulus,
        (c * e + d * g) % modulus,
        (c * f + d * h) % modulus,
    )


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


__all__ = ["arnold_matrix", "arnold_transform"]

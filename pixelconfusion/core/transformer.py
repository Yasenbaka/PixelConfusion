"""Image-level orchestration over the pure permutation algorithms."""

from __future__ import annotations

import numpy as np
from PIL import Image

from pixelconfusion.core.arnold import arnold_transform
from pixelconfusion.core.common import Progress
from pixelconfusion.core.gilbert import default_offset, gilbert_order, gilbert_transform


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


__all__ = ["Transformer"]

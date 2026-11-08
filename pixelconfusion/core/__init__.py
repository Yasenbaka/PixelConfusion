"""Pure image-processing API, independent of the desktop interface."""

from __future__ import annotations

from pixelconfusion.core.arnold import arnold_matrix, arnold_transform
from pixelconfusion.core.common import Progress
from pixelconfusion.core.gilbert import (
    GOLDEN_RATIO,
    default_offset,
    gilbert_order,
    gilbert_transform,
)
from pixelconfusion.core.image_io import load_image, save_png
from pixelconfusion.core.transformer import Transformer

__all__ = [
    "GOLDEN_RATIO",
    "Progress",
    "Transformer",
    "arnold_matrix",
    "arnold_transform",
    "default_offset",
    "gilbert_order",
    "gilbert_transform",
    "load_image",
    "save_png",
]

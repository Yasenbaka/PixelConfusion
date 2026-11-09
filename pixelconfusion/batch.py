"""Batch result records shared by the controller and the result grid."""

from __future__ import annotations

from dataclasses import dataclass

from PIL import Image


@dataclass(frozen=True)
class BatchItem:
    """One generated iteration thumbnail; the full image is recomputed on demand."""

    direction: str  # "reverse" or "forward"
    iteration: int
    thumbnail: Image.Image


__all__ = ["BatchItem"]

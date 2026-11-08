"""Shared types for the pure image-processing core."""

from __future__ import annotations

from typing import Callable

Progress = Callable[[float, str], None]

__all__ = ["Progress"]

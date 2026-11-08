"""Validation and normalization of the transform parameters."""

from __future__ import annotations

from dataclasses import dataclass

MAX_ITERATIONS = 1_000_000


@dataclass(frozen=True)
class TransformRequest:
    """Validated values passed to the image-processing core."""

    method: str
    action: str
    iterations: int
    offset: int | None
    a: int = 1
    b: int = 1


def build_transform_request(
    method: str,
    action: str,
    iterations_text: str,
    offset_text: str,
    a_text: str,
    b_text: str,
    *,
    width: int,
    height: int,
) -> TransformRequest:
    """Parse the sidebar fields, raising ValueError with a user-facing message."""
    iterations = int(iterations_text)
    if not 1 <= iterations <= MAX_ITERATIONS:
        raise ValueError("次数需在 1 到 1000000 之间。")
    offset_text = offset_text.strip()
    offset = int(offset_text) if method == "gilbert" and offset_text else None
    a = int(a_text) if method == "arnold" else 1
    b = int(b_text) if method == "arnold" else 1
    if method == "arnold" and width != height:
        raise ValueError("标准 Arnold 猫映射需要正方形图片。长方形图片可以选择 Gilbert。")
    return TransformRequest(
        method=method,
        action=action,
        iterations=iterations,
        offset=offset,
        a=a,
        b=b,
    )


__all__ = ["MAX_ITERATIONS", "TransformRequest", "build_transform_request"]

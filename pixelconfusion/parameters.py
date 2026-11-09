"""Validation and normalization of the transform parameters."""

from __future__ import annotations

from dataclasses import dataclass

MAX_ITERATIONS = 1_000_000
DEFAULT_BATCH_COUNT = 10
MAX_BATCH_COUNT = 50


@dataclass(frozen=True)
class TransformRequest:
    """Validated values passed to the image-processing core."""

    method: str
    action: str
    iterations: int
    offset: int | None
    a: int = 1
    b: int = 1


@dataclass(frozen=True)
class BatchRequest:
    """Validated range for one batch of forward and/or reverse results."""

    method: str
    actions: tuple[str, ...]
    start: int
    count: int
    offset: int | None
    a: int = 1
    b: int = 1

    @property
    def end(self) -> int:
        return self.start + self.count - 1


def _parse_common(
    method: str,
    offset_text: str,
    a_text: str,
    b_text: str,
    *,
    width: int,
    height: int,
) -> tuple[int | None, int, int]:
    if method not in ("gilbert", "arnold"):
        raise ValueError("未知算法。")
    offset_text = offset_text.strip()
    offset = int(offset_text) if method == "gilbert" and offset_text else None
    a = int(a_text) if method == "arnold" else 1
    b = int(b_text) if method == "arnold" else 1
    if method == "arnold" and width != height:
        raise ValueError("标准 Arnold 猫映射需要正方形图片。长方形图片可以选择 Gilbert。")
    return offset, a, b


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
    offset, a, b = _parse_common(method, offset_text, a_text, b_text,
                                 width=width, height=height)
    return TransformRequest(
        method=method,
        action=action,
        iterations=iterations,
        offset=offset,
        a=a,
        b=b,
    )


def build_batch_request(
    method: str,
    actions: tuple[str, ...],
    start: int,
    count_text: str,
    offset_text: str,
    a_text: str,
    b_text: str,
    *,
    width: int,
    height: int,
) -> BatchRequest:
    """Validate one batch range and return the shared algorithm parameters."""
    count = int(count_text)
    if not 1 <= count <= MAX_BATCH_COUNT:
        raise ValueError("等差迭代次数需在 1 到 50 之间。")
    if start < 1 or start + count - 1 > MAX_ITERATIONS:
        raise ValueError("本批迭代范围需在 1 到 1000000 之间。")
    if not actions or any(action not in ("restore", "scramble") for action in actions):
        raise ValueError("未知的批量处理方向。")
    offset, a, b = _parse_common(method, offset_text, a_text, b_text,
                                 width=width, height=height)
    return BatchRequest(
        method=method,
        actions=tuple(actions),
        start=start,
        count=count,
        offset=offset,
        a=a,
        b=b,
    )


__all__ = [
    "BatchRequest",
    "DEFAULT_BATCH_COUNT",
    "MAX_BATCH_COUNT",
    "MAX_ITERATIONS",
    "TransformRequest",
    "build_batch_request",
    "build_transform_request",
]

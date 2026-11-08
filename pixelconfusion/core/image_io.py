"""Load and save the single-frame images supported by the application."""

from __future__ import annotations

from PIL import Image


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


__all__ = ["load_image", "save_png"]

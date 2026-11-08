"""Built-in geometric test image for round-trip checks."""

from __future__ import annotations

from PIL import Image, ImageDraw, ImageFont


def make_demo() -> Image.Image:
    """A self-contained geometric picture for round-trip testing."""
    size = 640
    image = Image.new("RGBA", (size, size), "#eef4fa")
    draw = ImageDraw.Draw(image)
    for y in range(size):
        ratio = y / max(1, size - 1)
        color = (233 - int(8 * ratio), 241 - int(5 * ratio), 250 - int(2 * ratio), 255)
        draw.line((0, y, size, y), fill=color)
    draw.rounded_rectangle((48, 54, 596, 602), radius=34, fill="#dfeaf4")
    draw.rounded_rectangle((42, 42, 588, 588), radius=34, fill="#ffffff")
    draw.ellipse((100, 98, 300, 298), fill="#f1ad48")
    draw.ellipse((114, 112, 286, 284), outline="#ffffff", width=3)
    draw.rounded_rectangle((346, 116, 540, 270), radius=18, fill="#3e7cd3")
    draw.polygon(((112, 496), (236, 320), (360, 496)), fill="#44aa8b")
    for x in range(390, 540, 24):
        draw.rounded_rectangle((x, 360, x + 13, 506), radius=6, fill="#9568bf")
    try:
        font = ImageFont.truetype("segoeui.ttf", 16)
    except OSError:
        font = ImageFont.load_default()
    draw.text((100, 548), "PIXELCONFUSION  /  LOCAL TEST IMAGE", fill="#263750", font=font)
    draw.ellipse((550, 550, 562, 562), fill="#ee2a7b")
    return image


__all__ = ["make_demo"]

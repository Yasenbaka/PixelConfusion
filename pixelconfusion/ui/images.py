"""Generated raster images and their photo caches."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageTk

from pixelconfusion.ui.theme import INK, SURFACE

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ICON_DIR = PROJECT_ROOT / "assets" / "icons"

_icon_photos: dict[tuple[str, str, int], ImageTk.PhotoImage] = {}
_icon_bases: dict[str, Image.Image] = {}
_brand_cache: dict[int, ImageTk.PhotoImage] = {}


def _base_icon(name: str) -> Image.Image:
    base = _icon_bases.get(name)
    if base is None:
        base = Image.open(ICON_DIR / f"{name}.png").convert("RGBA")
        _icon_bases[name] = base
    return base


def icon_photo(name: str, color: str, size: int) -> ImageTk.PhotoImage:
    key = (name, color, size)
    photo = _icon_photos.get(key)
    if photo is None:
        base = _base_icon(name)
        tinted = Image.new("RGBA", base.size, color)
        tinted.putalpha(base.getchannel("A"))
        tinted = tinted.resize((size, size), Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(tinted)
        _icon_photos[key] = photo
    return photo


def brand_photo(size: int = 31) -> ImageTk.PhotoImage:
    photo = _brand_cache.get(size)
    if photo is not None:
        return photo
    scale = 2
    mark = Image.new("RGBA", (size * scale, size * scale), (0, 0, 0, 0))
    ImageDraw.Draw(mark).rounded_rectangle(
        (0, 0, size * scale - 1, size * scale - 1),
        radius=max(5, round(size * 0.26)) * scale,
        fill=INK,
    )
    icon = _base_icon("pixelconfusion")
    inner = round(size * 0.58) * scale
    icon = icon.resize((inner, inner), Image.Resampling.LANCZOS)
    white = Image.new("RGBA", icon.size, (255, 255, 255, 255))
    white.putalpha(icon.getchannel("A"))
    offset = (size * scale - inner) // 2
    mark.alpha_composite(white, (offset, offset))
    mark = mark.resize((size, size), Image.Resampling.LANCZOS)
    photo = ImageTk.PhotoImage(mark)
    _brand_cache[size] = photo
    return photo


def preview_photo(image: Image.Image, max_width: int, max_height: int) -> ImageTk.PhotoImage:
    preview = image.copy()
    preview.thumbnail((max(1, max_width), max(1, max_height)), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", preview.size, (30, 31, 34, 255))
    if preview.mode != "RGBA":
        preview = preview.convert("RGBA")
    canvas.alpha_composite(preview)
    return ImageTk.PhotoImage(canvas.convert("RGB"))


def thumbnail_photo(image: Image.Image, size: int = 64) -> ImageTk.PhotoImage:
    scale = 2
    side = size * scale
    ring = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    draw = ImageDraw.Draw(ring)
    draw.rounded_rectangle((0, 0, side - 1, side - 1), radius=round(size * 0.17) * scale,
                           fill=INK)
    inset = 2 * scale
    draw.rounded_rectangle((inset, inset, side - inset - 1, side - inset - 1),
                           radius=round(size * 0.15) * scale, fill=SURFACE)
    thumb = image.copy().convert("RGBA")
    thumb.thumbnail((side - 10 * scale, side - 10 * scale), Image.Resampling.LANCZOS)
    thumb_mask = Image.new("L", thumb.size, 0)
    ImageDraw.Draw(thumb_mask).rounded_rectangle(
        (0, 0, thumb.width - 1, thumb.height - 1),
        radius=round(thumb.width * 0.12), fill=255,
    )
    x = (side - thumb.width) // 2
    y = (side - thumb.height) // 2
    ring.paste(thumb, (x, y), thumb_mask)
    ring = ring.resize((size, size), Image.Resampling.LANCZOS)
    return ImageTk.PhotoImage(ring)


__all__ = [
    "ICON_DIR",
    "PROJECT_ROOT",
    "brand_photo",
    "icon_photo",
    "preview_photo",
    "thumbnail_photo",
]

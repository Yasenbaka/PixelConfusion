"""Generated raster images and their photo caches."""

from __future__ import annotations

from PIL import Image, ImageDraw, ImageTk

from pixelconfusion.paths import RESOURCE_ROOT
from pixelconfusion.ui.theme import INK, SURFACE

ICON_DIR = RESOURCE_ROOT / "assets" / "icons"
BRAND_DIR = RESOURCE_ROOT / "assets" / "brand"

_icon_photos: dict[tuple[str, str, int], ImageTk.PhotoImage] = {}
_icon_bases: dict[str, Image.Image] = {}
_brand_cache: dict[int, ImageTk.PhotoImage] = {}
_lockup_cache: dict[int, ImageTk.PhotoImage] = {}
_lockup_base: Image.Image | None = None
_brand_icon_base: Image.Image | None = None

# Directional arrows reuse the existing arrow glyph so the stroke style stays
# consistent; rotating the alpha mask is lossless.
_ROTATED_ICONS = {
    "arrow-right": ("arrow-down", Image.Transpose.ROTATE_90),
    "arrow-left": ("arrow-down", Image.Transpose.ROTATE_270),
}


def _base_icon(name: str) -> Image.Image:
    base = _icon_bases.get(name)
    if base is None:
        rotation = _ROTATED_ICONS.get(name)
        if rotation is None:
            base = Image.open(ICON_DIR / f"{name}.png").convert("RGBA")
        else:
            source, turn = rotation
            base = (Image.open(ICON_DIR / f"{source}.png")
                    .convert("RGBA").transpose(turn))
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


def _brand_lockup() -> Image.Image:
    global _lockup_base
    if _lockup_base is None:
        with Image.open(BRAND_DIR / "yasen-lockup.png") as image:
            _lockup_base = image.convert("RGBA")
    return _lockup_base


def _brand_icon() -> Image.Image:
    global _brand_icon_base
    if _brand_icon_base is None:
        with Image.open(BRAND_DIR / "yasen-icon.png") as image:
            _brand_icon_base = image.convert("RGBA")
    return _brand_icon_base


def _scaled_to_height(base: Image.Image, height: int) -> Image.Image:
    width = max(1, round(base.width * height / base.height))
    return base.resize((width, height), Image.Resampling.LANCZOS)


def brand_lockup_photo(height: int = 32) -> ImageTk.PhotoImage:
    """The header lockup: star-moon and Yasen cut as one piece."""
    photo = _lockup_cache.get(height)
    if photo is None:
        photo = ImageTk.PhotoImage(
            _scaled_to_height(_brand_lockup(), height))
        _lockup_cache[height] = photo
    return photo


def brand_photo(size: int = 64) -> ImageTk.PhotoImage:
    """Square app icon: the star-moon mark on a transparent canvas."""
    photo = _brand_cache.get(size)
    if photo is not None:
        return photo
    photo = ImageTk.PhotoImage(
        _brand_icon().resize((size, size), Image.Resampling.LANCZOS))
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
    "BRAND_DIR",
    "ICON_DIR",
    "RESOURCE_ROOT",
    "brand_lockup_photo",
    "brand_photo",
    "icon_photo",
    "preview_photo",
    "thumbnail_photo",
]

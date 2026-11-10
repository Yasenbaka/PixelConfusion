"""Single source of truth for the PixelConfusion version number.

The version is a three-part ``MAJOR.MINOR.PATCH`` number.  Each part keeps the
meaning used by this project:

* ``MAJOR`` — 大更新：整体架构或交互方式的大范围调整；
* ``MINOR`` — 中期更新：新增功能，并保持既有用法兼容；
* ``PATCH`` — 小更新：问题修复与细节调整。

``VERSION_PARTS`` below is the in-code default.  ``build.py`` resolves the final
value from the command line, the environment, an optional ``version.json`` or
this module, then embeds it in the executable.  The window title, the
``--version`` output, the file name and the Windows metadata therefore always
agree with each other.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from pixelconfusion.paths import RESOURCE_ROOT

APP_NAME = "PixelConfusion"
APP_NAME_CN = "像素混淆器"
APP_TITLE = f"{APP_NAME} · {APP_NAME_CN}"
AUTHOR = "Yasenbaka"
COPYRIGHT = "Copyright (c) 2026 Yasenbaka"

#: 打包时可用于临时指定版本号的环境变量。
ENV_VAR = "PIXELCONFUSION_VERSION"
#: 可选的版本配置文件，内容形如 ``{"version": "1.0.0"}``。
VERSION_CONFIG_NAME = "version.json"
#: 代码中的版本号来源，供打包脚本读取和写回。
VERSION_SOURCE = Path("pixelconfusion") / "version.py"

VERSION_LABELS: tuple[str, str, str] = ("大更新", "中期更新", "小更新")
VERSION_PATTERN = re.compile(r"(\d+)\.(\d+)\.(\d+)")

#: 版本号三元组：(大更新, 中期更新, 小更新)。修改版本号时只需改这一行。
VERSION_PARTS: tuple[int, int, int] = (1, 0, 0)

_VERSION_ASSIGNMENT = re.compile(
    r"^VERSION_PARTS\s*(?::\s*[^=\n]+)?=\s*"
    r"\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)",
    re.MULTILINE,
)


class VersionError(ValueError):
    """Raised when a version value cannot be parsed or persisted."""


def parse_version(value: object) -> tuple[int, int, int]:
    """Parse ``MAJOR.MINOR.PATCH`` into a three-item tuple."""
    text = str(value).strip()
    match = VERSION_PATTERN.fullmatch(text)
    if match is None:
        raise VersionError(
            f"版本号必须采用 MAJOR.MINOR.PATCH 格式，例如 1.0.0：{text!r}")
    return int(match.group(1)), int(match.group(2)), int(match.group(3))


def format_version(parts: tuple[int, int, int]) -> str:
    """Render a three-item version tuple as ``MAJOR.MINOR.PATCH``."""
    major, minor, patch = (int(part) for part in parts)
    if min(major, minor, patch) < 0:
        raise VersionError(f"版本号不能为负数：{parts!r}")
    return f"{major}.{minor}.{patch}"


def bump_version(
    parts: tuple[int, int, int], part: str
) -> tuple[int, int, int]:
    """Return ``parts`` incremented at ``part`` (``major``/``minor``/``patch``).

    The less significant parts reset to zero, so a major bump turns
    ``1.4.2`` into ``2.0.0``.
    """
    indexes = {"major": 0, "minor": 1, "patch": 2}
    try:
        index = indexes[part]
    except KeyError as error:
        raise VersionError(f"未知的版本部位：{part!r}") from error
    values = list(parts)
    values[index] += 1
    for lower in range(index + 1, 3):
        values[lower] = 0
    return values[0], values[1], values[2]


def read_version_parts(path: Path | str) -> tuple[int, int, int]:
    """Read ``VERSION_PARTS`` from a version module without importing it."""
    source = Path(path)
    try:
        text = source.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        raise VersionError(f"无法读取版本号源文件 {source}：{error}") from error
    match = _VERSION_ASSIGNMENT.search(text)
    if match is None:
        raise VersionError(
            f"{source} 中找不到 VERSION_PARTS = (MAJOR, MINOR, PATCH)")
    return int(match.group(1)), int(match.group(2)), int(match.group(3))


def write_version_source(path: Path | str, parts: tuple[int, int, int]) -> None:
    """Persist ``parts`` as ``VERSION_PARTS`` in a version module."""
    source = Path(path)
    try:
        text = source.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        raise VersionError(f"无法读取版本号源文件 {source}：{error}") from error
    major, minor, patch = parts
    replacement = (
        f"VERSION_PARTS: tuple[int, int, int] = ({major}, {minor}, {patch})")
    updated, count = _VERSION_ASSIGNMENT.subn(replacement, text, count=1)
    if count == 0:
        raise VersionError(
            f"{source} 中找不到 VERSION_PARTS = (MAJOR, MINOR, PATCH)")
    source.write_text(updated, encoding="utf-8", newline="\n")


def read_version_config(path: Path | str) -> tuple[int, int, int] | None:
    """Read ``{"version": "1.0.0"}``; return ``None`` when the file is absent."""
    source = Path(path)
    if not source.is_file():
        return None
    try:
        payload = json.loads(source.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as error:
        raise VersionError(f"无法读取版本配置文件 {source}：{error}") from error
    if not isinstance(payload, dict):
        raise VersionError(
            f'{source} 必须是 JSON 对象，例如 {{"version": "1.0.0"}}')
    if "version" not in payload:
        raise VersionError(
            f'{source} 中缺少 "version" 字段，例如 {{"version": "1.0.0"}}')
    return parse_version(payload["version"])


def write_version_config(path: Path | str, parts: tuple[int, int, int]) -> None:
    """Write ``parts`` into a version config, keeping other existing keys."""
    target = Path(path)
    payload: dict[str, object] = {}
    if target.is_file():
        try:
            existing = json.loads(target.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError) as error:
            raise VersionError(
                f"无法更新版本配置文件 {target}：{error}") from error
        if not isinstance(existing, dict):
            raise VersionError(
                f'{target} 必须是 JSON 对象，例如 {{"version": "1.0.0"}}')
        payload = existing
    payload["version"] = format_version(parts)
    target.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8", newline="\n")


@dataclass(frozen=True)
class ResolvedVersion:
    """A version and the source it was resolved from."""

    parts: tuple[int, int, int]
    source: str

    @property
    def text(self) -> str:
        return format_version(self.parts)

    def components(self) -> str:
        """Return ``大更新 1 · 中期更新 0 · 小更新 0``."""
        return " · ".join(
            f"{label} {value}"
            for label, value in zip(VERSION_LABELS, self.parts))

    def detail(self) -> str:
        """Return ``1.0.0（大更新 1 · 中期更新 0 · 小更新 0）``."""
        return f"{self.text}（{self.components()}）"


def resolve_version(
    root: Path | str,
    *,
    cli_version: str | None = None,
    environ: Mapping[str, str] | None = None,
) -> ResolvedVersion:
    """Resolve the version used by a build.

    Precedence: ``cli_version`` → ``PIXELCONFUSION_VERSION`` → ``version.json``
    → ``pixelconfusion/version.py``.
    """
    base = Path(root)
    if cli_version is not None:
        return ResolvedVersion(parse_version(cli_version), "命令行 --version")
    environment = os.environ if environ is None else environ
    raw = str(environment.get(ENV_VAR, "")).strip()
    if raw:
        return ResolvedVersion(parse_version(raw), f"环境变量 {ENV_VAR}")
    config = read_version_config(base / VERSION_CONFIG_NAME)
    if config is not None:
        return ResolvedVersion(config, VERSION_CONFIG_NAME)
    parts = read_version_parts(base / VERSION_SOURCE)
    return ResolvedVersion(parts, VERSION_SOURCE.as_posix())


def _runtime_version() -> ResolvedVersion:
    """Load the version running inside the app (bundled config wins)."""
    try:
        config = read_version_config(RESOURCE_ROOT / VERSION_CONFIG_NAME)
    except VersionError:
        config = None
    if config is not None:
        return ResolvedVersion(config, VERSION_CONFIG_NAME)
    return ResolvedVersion(VERSION_PARTS, VERSION_SOURCE.as_posix())


_RUNTIME = _runtime_version()
__version__ = _RUNTIME.text
#: 供界面代码引用的公开别名，与 ``__version__`` 保持一致。
VERSION = __version__


def version_components() -> str:
    """Return the current version components, e.g. ``大更新 1 · 中期更新 0``."""
    return _RUNTIME.components()


def version_detail() -> str:
    """Return the current version with its component labels."""
    return _RUNTIME.detail()


def version_source() -> str:
    """Return where the running version was loaded from."""
    return _RUNTIME.source


def window_title() -> str:
    """Return the window title including the version number."""
    return f"{APP_TITLE} v{__version__}"


__all__ = [
    "APP_NAME",
    "APP_NAME_CN",
    "APP_TITLE",
    "AUTHOR",
    "COPYRIGHT",
    "ENV_VAR",
    "ResolvedVersion",
    "VERSION",
    "VERSION_CONFIG_NAME",
    "VERSION_LABELS",
    "VERSION_PARTS",
    "VERSION_SOURCE",
    "VersionError",
    "bump_version",
    "format_version",
    "parse_version",
    "read_version_config",
    "read_version_parts",
    "resolve_version",
    "version_components",
    "version_detail",
    "version_source",
    "window_title",
    "write_version_config",
    "write_version_source",
]

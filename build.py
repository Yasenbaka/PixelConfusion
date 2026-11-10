#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Package PixelConfusion as a standalone executable.

The version is never duplicated here.  It is resolved from the command line,
the ``PIXELCONFUSION_VERSION`` environment variable, an optional
``version.json`` or ``pixelconfusion/version.py`` (in that order), then embedded
in the executable name, the Windows version resource, the icon and a bundled
``version.json`` that the running program reads back.  The window title, the
``--version`` output, the file name and the file properties therefore always
show the same number.

Examples::

    python build.py                        # 按代码中的版本号打包
    python build.py --bump patch           # 小更新：1.0.0 → 1.0.1，写回代码后打包
    python build.py --set-version 2.0.0    # 大更新：写回代码后打包
    python build.py --version 1.0.0        # 仅本次打包使用该版本号
    python build.py --print-version        # 只打印解析到的版本号
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import shlex
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pixelconfusion.console import use_utf8_output
from pixelconfusion.version import (  # noqa: E402
    APP_NAME,
    APP_TITLE,
    AUTHOR,
    COPYRIGHT,
    ENV_VAR,
    VERSION_CONFIG_NAME,
    VERSION_SOURCE,
    ResolvedVersion,
    VersionError,
    bump_version,
    format_version,
    parse_version,
    read_version_config,
    read_version_parts,
    resolve_version,
    write_version_config,
    write_version_source,
)

ASSET_DIR = ROOT / "assets"
BRAND_ICON = ASSET_DIR / "brand" / "yasen-icon.png"
BUILD_DIR = ROOT / "build" / "pyinstaller"
ICON_SIZES = ((16, 16), (24, 24), (32, 32), (48, 48), (64, 64),
              (128, 128), (256, 256))


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="将 PixelConfusion 打包为独立可执行程序，并写入版本号。",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "版本号优先级：--version > 环境变量 "
            f"{ENV_VAR} > {VERSION_CONFIG_NAME} > "
            f"{VERSION_SOURCE.as_posix()}\n"
            "版本号三段依次对应：大更新.中期更新.小更新"
        ),
    )
    version_group = parser.add_mutually_exclusive_group()
    version_group.add_argument(
        "--version", metavar="X.Y.Z",
        help="仅本次打包使用的版本号，不修改源文件")
    version_group.add_argument(
        "--set-version", metavar="X.Y.Z",
        help="将版本号写回版本来源（version.json 或 version.py）后打包")
    version_group.add_argument(
        "--bump", choices=("major", "minor", "patch"),
        help="递增版本号并写回版本来源后打包：major=大更新，"
             "minor=中期更新，patch=小更新")
    parser.add_argument(
        "--print-version", action="store_true",
        help="打印解析到的版本号后退出")
    parser.add_argument(
        "--name", default=APP_NAME,
        help=f"可执行程序基名（默认 {APP_NAME}）")
    parser.add_argument(
        "--output", default="dist",
        help="输出目录，相对路径以项目根目录为准（默认 dist）")
    parser.add_argument(
        "--onedir", action="store_true",
        help="输出文件夹模式，默认打包为单个可执行文件")
    parser.add_argument(
        "--console", action="store_true",
        help="保留控制台窗口，便于排查启动问题")
    parser.add_argument(
        "--no-version-suffix", action="store_true",
        help="可执行文件名不附加版本号")
    parser.add_argument(
        "--clean", action="store_true",
        help="打包前清理 PyInstaller 缓存与临时目录")
    parser.add_argument(
        "--dry-run", action="store_true",
        help="只解析版本并打印 PyInstaller 命令，不执行打包")
    return parser.parse_args(argv)


def _persist_version(root: Path, parts: tuple[int, int, int]) -> str:
    """Write ``parts`` back to the active version source and name it."""
    config_path = root / VERSION_CONFIG_NAME
    if config_path.is_file():
        write_version_config(config_path, parts)
        return VERSION_CONFIG_NAME
    write_version_source(root / VERSION_SOURCE, parts)
    return VERSION_SOURCE.as_posix()


def _escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace("'", "\\'")


def render_version_resource(
    resolved: ResolvedVersion, exe_name: str
) -> str:
    """Render the Windows ``VSVersionInfo`` structure as Python source."""
    major, minor, patch = resolved.parts
    file_version = (major, minor, patch, 0)
    fields = (
        ("CompanyName", AUTHOR),
        ("FileDescription", APP_TITLE),
        ("FileVersion", resolved.text),
        ("InternalName", APP_NAME),
        ("LegalCopyright", COPYRIGHT),
        ("OriginalFilename", exe_name),
        ("ProductName", APP_NAME),
        ("ProductVersion", resolved.text),
    )
    strings = "\n".join(
        f"              StringStruct('{_escape(key)}', "
        f"'{_escape(value)}'),"
        for key, value in fields
    )
    return f"""# UTF-8
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers={file_version!r},
    prodvers={file_version!r},
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0),
  ),
  kids=[
    StringFileInfo(
      [
        StringTable(
          '080404b0',
          [
{strings}
          ],
        ),
      ],
    ),
    VarFileInfo([VarStruct('Translation', [2052, 1200])]),
  ],
)
"""


def _write_text(target: Path, text: str) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8", newline="\n")


def _write_icon(target: Path) -> None:
    from PIL import Image

    with Image.open(BRAND_ICON) as source:
        image = source.convert("RGBA")
    target.parent.mkdir(parents=True, exist_ok=True)
    image.save(target, format="ICO", sizes=ICON_SIZES)


def _write_version_snapshot(target: Path, resolved: ResolvedVersion) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {"version": resolved.text}
    target.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8", newline="\n")


def _require_pyinstaller() -> None:
    if importlib.util.find_spec("PyInstaller") is None:
        raise SystemExit(
            "未安装 PyInstaller，无法打包。请先运行：\n"
            f'  "{sys.executable}" -m pip install -r '
            f'"{ROOT / "requirements-dev.txt"}"')


def _exe_suffix() -> str:
    return ".exe" if os.name == "nt" else ""


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _pyinstaller_arguments(
    args: argparse.Namespace,
    exe_name: str,
    output: Path,
    icon: Path,
    version_file: Path,
    snapshot: Path,
) -> list[str]:
    arguments = [
        str(ROOT / "main.py"),
        "--noconfirm",
        "--distpath", str(output),
        "--workpath", str(BUILD_DIR / "work"),
        "--specpath", str(BUILD_DIR / "spec"),
        "--name", exe_name,
        "--icon", str(icon),
        "--version-file", str(version_file),
        "--paths", str(ROOT),
        "--add-data", f"{ASSET_DIR}{os.pathsep}assets",
        "--add-data", f"{snapshot.parent}{os.pathsep}.",
        "--onedir" if args.onedir else "--onefile",
        "--console" if args.console else "--windowed",
    ]
    if args.clean:
        arguments.append("--clean")
    return arguments


def _resolve_for_build(args: argparse.Namespace) -> ResolvedVersion:
    """Resolve the build version, persisting bumps unless it is a dry run."""
    if not (args.bump or args.set_version):
        return resolve_version(ROOT, cli_version=args.version)
    if os.environ.get(ENV_VAR, "").strip():
        raise SystemExit(
            f"环境变量 {ENV_VAR} 会覆盖写回的版本号，"
            "请先清除该变量再使用 --bump 或 --set-version。")
    config_path = ROOT / VERSION_CONFIG_NAME
    current = (read_version_config(config_path)
               if config_path.is_file()
               else read_version_parts(ROOT / VERSION_SOURCE))
    target = (parse_version(args.set_version) if args.set_version
              else bump_version(current, args.bump))
    source = (VERSION_CONFIG_NAME if config_path.is_file()
              else VERSION_SOURCE.as_posix())
    if args.dry_run:
        print(f"版本号将写回 {source}：{format_version(target)}")
        return ResolvedVersion(target, f"待写回 {source}")
    written = _persist_version(ROOT, target)
    print(f"版本号已写回 {written}：{format_version(target)}")
    return resolve_version(ROOT)


def _build(args: argparse.Namespace) -> int:
    resolved = _resolve_for_build(args)
    if args.print_version:
        print(resolved.text)
        return 0

    exe_name = (args.name if args.no_version_suffix
                else f"{args.name}-{resolved.text}")
    output = Path(args.output)
    if not output.is_absolute():
        output = ROOT / output
    work = BUILD_DIR
    icon = work / "app.ico"
    version_file = work / "version_info.txt"
    snapshot = work / "bundle" / VERSION_CONFIG_NAME
    artifact = (output / exe_name / (exe_name + _exe_suffix())
                if args.onedir
                else output / (exe_name + _exe_suffix()))

    print(f"版本号：{resolved.detail()}")
    print(f"版本来源：{resolved.source}")
    print(f"输出文件：{_display_path(artifact)}")

    arguments = _pyinstaller_arguments(
        args, exe_name, output, icon, version_file, snapshot)

    if args.dry_run:
        print("PyInstaller 命令：")
        print("  " + " ".join(shlex.quote(item) for item in arguments))
        return 0

    _require_pyinstaller()

    if args.clean:
        shutil.rmtree(work / "work", ignore_errors=True)
        shutil.rmtree(work / "spec", ignore_errors=True)
    (work / "work").mkdir(parents=True, exist_ok=True)
    (work / "spec").mkdir(parents=True, exist_ok=True)
    _write_icon(icon)
    _write_text(
        version_file,
        render_version_resource(resolved, exe_name + _exe_suffix()))
    _write_version_snapshot(snapshot, resolved)
    output.mkdir(parents=True, exist_ok=True)

    from PyInstaller.__main__ import run as pyinstaller_run

    try:
        pyinstaller_run(arguments)
    except SystemExit as error:
        if error.code not in (0, None):
            raise SystemExit(f"PyInstaller 打包失败，退出码：{error.code}") from None

    if not artifact.exists():
        raise SystemExit(f"打包结束但未找到产物：{artifact}")
    size = (artifact.stat().st_size if artifact.is_file()
            else sum(item.stat().st_size for item in artifact.rglob("*")
                     if item.is_file()))
    print()
    print(f"打包完成：{_display_path(artifact)}")
    print(f"版本号：{resolved.detail()}")
    print(f"版本来源：{resolved.source}")
    print(f"文件大小：{size / (1024 * 1024):.1f} MB")
    return 0


def main(argv: list[str] | None = None) -> int:
    use_utf8_output()
    args = _parse_args(argv)
    try:
        return _build(args)
    except VersionError as error:
        print(f"版本号错误：{error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

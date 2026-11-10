"""Filesystem roots that work both from source and from a frozen bundle."""

from __future__ import annotations

import sys
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_ROOT.parent


def resource_root() -> Path:
    """Return the directory that holds data files such as ``assets/``.

    PyInstaller extracts one-file bundles into a temporary directory and exposes
    it as ``sys._MEIPASS``.  Data added with ``--add-data`` is placed there, so
    resolving resources against it keeps the packaged program identical to the
    source checkout.
    """
    bundle = getattr(sys, "_MEIPASS", None)
    if bundle:
        return Path(bundle)
    return PROJECT_ROOT


RESOURCE_ROOT = resource_root()


def resource_path(*parts: str) -> Path:
    """Join ``parts`` onto :data:`RESOURCE_ROOT`."""
    return RESOURCE_ROOT.joinpath(*parts)


__all__ = ["PACKAGE_ROOT", "PROJECT_ROOT", "RESOURCE_ROOT", "resource_path",
           "resource_root"]

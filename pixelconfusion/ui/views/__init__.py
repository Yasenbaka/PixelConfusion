"""Composite views assembled from the shared widget library."""

from __future__ import annotations

from pixelconfusion.ui.views.action_row import ActionRow
from pixelconfusion.ui.views.app_bar import AppBar
from pixelconfusion.ui.views.iteration_card import IterationCard
from pixelconfusion.ui.views.page import PageView
from pixelconfusion.ui.views.params_card import ParamsCard
from pixelconfusion.ui.views.source_card import SourceCard
from pixelconfusion.ui.views.stage import StageView
from pixelconfusion.ui.views.workspace import WorkspaceView

__all__ = [
    "ActionRow",
    "AppBar",
    "IterationCard",
    "PageView",
    "ParamsCard",
    "SourceCard",
    "StageView",
    "WorkspaceView",
]

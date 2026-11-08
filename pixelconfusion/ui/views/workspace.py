"""Two-column workspace: sidebar cards on the left, preview stage on the right."""

from __future__ import annotations

import tkinter as tk

from pixelconfusion.ui.theme import BG
from pixelconfusion.ui.views.action_row import ActionRow
from pixelconfusion.ui.views.params_card import ParamsCard
from pixelconfusion.ui.views.source_card import SourceCard
from pixelconfusion.ui.views.stage import StageView


class WorkspaceView(tk.Frame):
    def __init__(
        self,
        master,
        *,
        on_pick,
        on_clear,
        on_demo,
        on_method_change,
        on_scramble,
        on_restore,
        on_use_result,
        on_save,
    ):
        super().__init__(master, bg=BG)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, minsize=336)
        self.grid_columnconfigure(1, weight=1)

        rail = tk.Frame(self, bg=BG)
        rail.grid(row=0, column=0, sticky="nsew")
        rail.grid_columnconfigure(0, weight=1)
        rail.grid_rowconfigure(3, weight=1)
        self.source_card = SourceCard(rail, on_pick=on_pick, on_clear=on_clear,
                                      on_demo=on_demo)
        self.source_card.grid(row=0, column=0, sticky="ew")
        tk.Frame(rail, bg=BG, height=12).grid(row=1, column=0, sticky="ew")
        self.params_card = ParamsCard(rail, on_method_change=on_method_change)
        self.params_card.grid(row=2, column=0, sticky="ew")
        tk.Frame(rail, bg=BG).grid(row=3, column=0, sticky="nsew")
        self.action_row = ActionRow(rail, on_scramble=on_scramble,
                                    on_restore=on_restore)
        self.action_row.grid(row=4, column=0, sticky="ew")

        self.stage = StageView(self, on_pick=on_pick, on_use_result=on_use_result,
                               on_save=on_save)
        self.stage.grid(row=0, column=1, sticky="nsew", padx=(16, 0))


__all__ = ["WorkspaceView"]

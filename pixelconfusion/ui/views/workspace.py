"""Workspace: full-width source strip above the sidebar and preview stage."""

from __future__ import annotations

import tkinter as tk

from pixelconfusion.ui.theme import BG
from pixelconfusion.ui.views.action_row import ActionRow
from pixelconfusion.ui.views.iteration_card import IterationCard
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
        on_iteration_mode_change,
        on_auto_change,
        on_next_batch,
        on_auto_batch,
        on_auto_next_batch,
        on_open_result,
    ):
        super().__init__(master, bg=BG)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, minsize=336)
        self.grid_columnconfigure(1, weight=1)

        self.source_card = SourceCard(self, on_pick=on_pick, on_clear=on_clear,
                                      on_demo=on_demo)
        self.source_card.grid(row=0, column=0, columnspan=2, sticky="ew",
                              pady=(0, 12))

        rail = tk.Frame(self, bg=BG)
        rail.grid(row=1, column=0, sticky="nsew")
        rail.grid_columnconfigure(0, weight=1)
        rail.grid_rowconfigure(2, weight=1)
        self.iteration_card = IterationCard(
            rail,
            on_mode_change=on_iteration_mode_change,
            on_auto_change=on_auto_change,
            on_next_batch=on_next_batch,
        )
        self.iteration_card.grid(row=0, column=0, sticky="ew")
        self.params_card = ParamsCard(rail, on_method_change=on_method_change)
        self.params_card.grid(row=1, column=0, sticky="ew", pady=(12, 0))
        tk.Frame(rail, bg=BG).grid(row=2, column=0, sticky="nsew")
        self.action_row = ActionRow(rail, on_scramble=on_scramble,
                                    on_restore=on_restore, on_auto=on_auto_batch,
                                    on_auto_next=on_auto_next_batch)
        self.action_row.grid(row=3, column=0, sticky="ew")

        self.stage = StageView(self, on_pick=on_pick, on_use_result=on_use_result,
                               on_save=on_save, on_open_result=on_open_result)
        self.stage.grid(row=1, column=1, sticky="nsew", padx=(16, 0))


__all__ = ["WorkspaceView"]

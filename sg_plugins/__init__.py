from __future__ import annotations

from typing import TYPE_CHECKING, Any

import gi

gi.require_version("Gimp", "3.0")
from gi.repository import Gimp

if TYPE_CHECKING:
    from sg_structures import ApiClient, MyShelf


class PluginBase:
    menu_label: str
    # Gimp.ProcedureSensitivityMask.ALWAYS
    # | Gimp.ProcedureSensitivityMask.NO_DRAWABLES
    sensitivity_mask = Gimp.ProcedureSensitivityMask.DRAWABLE
    menu_path: str = "<Image>/SHSMAD/"
    description: str

    def __init__(self, api: ApiClient | None = None, settings: MyShelf | None = None) -> None:
        self.api = api
        self.settings = settings

    def main(
        self,
        procedure: Gimp.Procedure,
        run_mode: Gimp.RunMode,
        image: Gimp.Image,
        drawables: list[Gimp.Drawable],
        config: Gimp.ProcedureConfig,
        data: Any,
    ) -> Gimp.ProcedureReturn: ...

    def add_arguments(self, procedure: Gimp.Procedure) -> None: ...

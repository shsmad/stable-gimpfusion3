import gi

gi.require_version("Gimp", "3.0")
from gi.repository import Gimp


class PluginBase:
    menu_label: str
    # Gimp.ProcedureSensitivityMask.ALWAYS
    # | Gimp.ProcedureSensitivityMask.NO_DRAWABLES
    sensitivity_mask = Gimp.ProcedureSensitivityMask.DRAWABLE
    menu_path: str = "<Image>/SHSMAD/"
    description: str

    def __init__(self, api=None, settings=None):
        self.api = api
        self.settings = settings

    def main(self, procedure, run_mode, image, drawables, config, data): ...

    def add_arguments(self, procedure): ...

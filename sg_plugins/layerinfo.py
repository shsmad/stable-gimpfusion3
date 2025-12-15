import json

import gi

from sg_i18n import _
from sg_structures import LayerData

gi.require_version("Gimp", "3.0")
gi.require_version("GimpUi", "3.0")
from gi.repository import Gimp, GLib

from sg_plugins import PluginBase


class LayerInfoPlugin(PluginBase):
    menu_path = "<Image>/GimpFusion/Config"
    menu_label = _("Layer Info")
    description = _("Show stable gimpfusion info associated with this layer")
    sensitivity_mask = Gimp.ProcedureSensitivityMask.DRAWABLE | Gimp.ProcedureSensitivityMask.DRAWABLES

    def add_arguments(self, procedure): ...

    def main(self, procedure, run_mode, image, drawables, config, data):
        msgs = [_("Selected layers have the following data associated with them:"), ""]

        msgs.extend(
            f"{layer.get_name()}: {json.dumps(LayerData(layer).data, sort_keys=True, indent=4)}" for layer in drawables
        )
        Gimp.message("\n".join(msgs))

        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())
        # handleShowLayerInfo


# class LayerInfoContextPlugin(PluginBase):
#     menu_path = "<Layers>/GimpFusion"
#     menu_label = "Layer Info"
#     description = "Show stable gimpfusion info associated with this layer"
#     sensitivity_mask = Gimp.ProcedureSensitivityMask.DRAWABLE | Gimp.ProcedureSensitivityMask.DRAWABLES
#
#     def add_arguments(self, procedure): ...
#
#     def main(self, procedure, run_mode, image, drawables, config, data):
#         msgs = ["Selected layers have the following data associated with them:", ""]
#
#         msgs.extend(
#             f"{layer.get_name()}: {json.dumps(LayerData(layer).data, sort_keys=True, indent=4)}" for layer in drawables
#         )
#         Gimp.message("\n".join(msgs))
#
#         return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())
#         # handleShowLayerInfoContext

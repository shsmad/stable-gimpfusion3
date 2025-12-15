#!/usr/bin/env python3
import logging
import os
import sys

import gi

from sg_plugins import PluginBase
from sg_plugins.config import ConfigModelPlugin, ConfigPlugin
from sg_plugins.config_controlnet import ConfigControlnetLayerPlugin
from sg_plugins.img2img import Image2imagePlugin
from sg_plugins.inpainting import InpaintingPlugin
from sg_plugins.layerinfo import LayerInfoPlugin
from sg_plugins.txt2img import Txt2imagePlugin

gi.require_version("Gimp", "3.0")
gi.require_version("GimpUi", "3.0")
from gi.repository import Gimp

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sg_constants import (
    AUTHOR,
    STABLE_GIMPFUSION_DEFAULT_SETTINGS,
)
from sg_structures import ApiClient, MyShelf
from sg_utils import fetch_stablediffusion_options, set_logging_dest

settings = MyShelf(STABLE_GIMPFUSION_DEFAULT_SETTINGS)
api = ApiClient(settings.get("api_base"))

logging.basicConfig(level=logging.DEBUG if settings.get("debug_logging") else logging.INFO)
set_logging_dest(settings.get("file_logging"))

# def PLUGIN_FIELDS_TXT2IMG(procedure):
#     PLUGIN_FIELDS_COMMON(procedure, samplers=SAMPLERS, selected_sampler=settings.get("sampler_name"))
#     PLUGIN_FIELDS_CONTROLNET_OPTIONS(procedure)


# def PLUGIN_FIELDS_IMG2IMG(procedure):
#     PLUGIN_FIELDS_RESIZE_MODE(procedure, resize_modes=RESIZE_MODES)
#     PLUGIN_FIELDS_TXT2IMG(procedure)

MODULES: dict[str, PluginBase] = {
    "stable-gimpfusion-config": ConfigPlugin(api=api, settings=settings),
    "stable-gimpfusion-config-model": ConfigModelPlugin(api=api, settings=settings),
    "stable-gimpfusion-txt2img": Txt2imagePlugin(api=api, settings=settings),
    # "stable-gimpfusion-txt2img-context": Txt2imageContextPlugin(api=api, settings=settings),
    "stable-gimpfusion-img2img": Image2imagePlugin(api=api, settings=settings),
    # "stable-gimpfusion-img2img-context": Image2imageContextPlugin(api=api, settings=settings),
    "stable-gimpfusion-inpainting": InpaintingPlugin(api=api, settings=settings),
    # "stable-gimpfusion-inpainting-context": InpaintingContextPlugin(api=api, settings=settings),
    "stable-gimpfusion-config-controlnet-layer": ConfigControlnetLayerPlugin(api=api, settings=settings),
    # "stable-gimpfusion-config-controlnet-layer-context": ConfigControlnetLayerContextPlugin(api=api, settings=settings),
    "stable-gimpfusion-layer-info": LayerInfoPlugin(api=api, settings=settings),
    # "stable-gimpfusion-layer-info-context": LayerInfoContextPlugin(api=api, settings=settings),
}


class GimpfusionPlugin(Gimp.PlugIn):
    def __init__(self):
        super().__init__()

        try:
            options = fetch_stablediffusion_options(api=api)
            settings.save(options)
        except Exception:
            logging.exception("ERROR: DynamicDropdownData.fetch")
            settings.save({"is_server_running", False})

    def do_set_i18n(self, name):
        return False

    def do_query_procedures(self):
        return list(MODULES.keys())

    def do_create_procedure(self, name: str) -> None:
        module = MODULES[name]

        procedure = Gimp.ImageProcedure.new(
            self,
            name,
            Gimp.PDBProcType.PLUGIN,
            module.main,
            None,
        )

        procedure.set_image_types("*")
        procedure.set_sensitivity_mask(module.sensitivity_mask)

        procedure.set_menu_label(module.menu_label)
        # procedure.set_icon_name(GimpUi.ICON_GEGL)
        procedure.add_menu_path(module.menu_path)

        procedure.set_documentation(module.description, module.description, name)
        procedure.set_attribution(AUTHOR, AUTHOR, "2025")

        if hasattr(module, "add_arguments"):
            module.add_arguments(procedure)

        return procedure


Gimp.main(GimpfusionPlugin.__gtype__, sys.argv)

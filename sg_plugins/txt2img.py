from __future__ import annotations

import logging

from typing import Any

import gi

from sg_constants import INSERT_MODES, SAMPLERS
from sg_gtk_utils import set_visibility_of
from sg_i18n import _
from sg_plugins.generation_base import GenerationPluginBase
from sg_proc_arguments import PLUGIN_FIELDS_COMMON, PLUGIN_FIELDS_CONTROLNET_OPTIONS

gi.require_version("Gimp", "3.0")
gi.require_version("GimpUi", "3.0")
from gi.repository import Gimp, GimpUi, GLib


class Txt2imagePlugin(GenerationPluginBase):
    menu_path = "<Image>/GimpFusion"
    menu_label = _("Text to image")
    description = _("Generate image from text")

    def add_arguments(self, procedure: Gimp.Procedure) -> None:
        # PLUGIN_FIELDS_TXT2IMG =
        PLUGIN_FIELDS_COMMON(procedure, samplers=SAMPLERS, selected_sampler=self.settings.get("sampler_name"))
        PLUGIN_FIELDS_CONTROLNET_OPTIONS(procedure)

    def main(
        self,
        procedure: Gimp.Procedure,
        run_mode: Gimp.RunMode,
        image: Gimp.Image,
        drawables: list[Gimp.Drawable],
        config: Gimp.ProcedureConfig,
        data: Any,
    ) -> Gimp.ProcedureReturn:
        if run_mode == Gimp.RunMode.INTERACTIVE:
            GimpUi.init(procedure.get_name())
            dialog = GimpUi.ProcedureDialog.new(procedure, config)

            vbox, grid = self.build_common_ui(procedure, config, dialog)
            boxes = self.build_common_parameter_boxes(dialog)

            # label = Gtk.Label.new_with_mnemonic("Scale")
            grid.attach(boxes["width"], 0, 0, 2, 1)
            grid.attach(boxes["height"], 2, 0, 2, 1)

            grid.attach(boxes["seed"], 0, 1, 1, 1)
            grid.attach(boxes["steps"], 1, 1, 1, 1)
            grid.attach(boxes["cfg_scale"], 2, 1, 1, 1)
            grid.attach(boxes["batch_size"], 3, 1, 1, 1)

            grid.attach(boxes["sampler_index"], 0, 3, 1, 1)
            grid.attach(boxes["denoising_strength"], 1, 3, 1, 1)
            grid.attach(boxes["restore_faces"], 2, 3, 1, 1)
            grid.attach(boxes["tiling"], 3, 3, 1, 1)

            grid.attach(boxes["cn1_enabled"], 0, 5, 1, 1)
            grid.attach(boxes["cn2_enabled"], 1, 5, 1, 1)
            grid.attach(boxes["cn1_layer"], 0, 6, 1, 1)
            grid.attach(boxes["cn2_layer"], 1, 6, 1, 1)

            set_visibility_of(
                [
                    boxes["width"],
                    boxes["height"],
                    boxes["steps"],
                    boxes["cfg_scale"],
                    boxes["restore_faces"],
                    boxes["tiling"],
                    boxes["cn1_enabled"],
                    boxes["cn2_enabled"],
                    boxes["seed"],
                    boxes["batch_size"],
                    boxes["sampler_index"],
                    boxes["denoising_strength"],
                ],
            )

            self.setup_controlnet_visibility(
                boxes["cn1_enabled"],
                boxes["cn1_layer"],
                boxes["cn2_enabled"],
                boxes["cn2_layer"],
            )

            dialog.resize(800, 600)

            dialog.fill(
                [
                    "cn_skip_annotator_layers",
                    "insert_mode",
                ],
            )

            if not dialog.run():
                return procedure.new_return_values(Gimp.PDBStatusType.CANCEL, GLib.Error())

        config_values = self.get_common_config_values(config)
        insert_mode = config.get_property("insert_mode")
        insert_mode = insert_mode if insert_mode in INSERT_MODES else INSERT_MODES[0]

        success, non_empty, x1, y1, x2, y2 = Gimp.Selection.bounds(image)
        selectionWidth, selectionHeight = x2 - x1, y2 - y1

        # Adjust width/height based on insert_mode
        width = selectionWidth if insert_mode == "Use selection size" else config_values["width"]
        height = selectionHeight if insert_mode == "Use selection size" else config_values["height"]

        data = self.build_base_data_dict(
            prompt=config_values["prompt"],
            negative_prompt=config_values["negative_prompt"],
            seed=config_values["seed"],
            batch_size=config_values["batch_size"],
            steps=config_values["steps"],
            cfg_scale=config_values["cfg_scale"],
            width=width,
            height=height,
            restore_faces=config_values["restore_faces"],
            tiling=config_values["tiling"],
            denoising_strength=config_values["denoising_strength"],
            sampler_index=config_values["sampler_index"],
        )
        data["enable_hr"] = False

        controlnet_units = self.build_controlnet_units(
            config_values["cn1_enabled"],
            config_values["cn1_layer"],
            config_values["cn2_enabled"],
            config_values["cn2_layer"],
        )
        self.add_controlnet_to_data(data, controlnet_units)

        try:
            response = self.call_api_with_progress(
                "/sdapi/v1/txt2img",
                data,
                progress_text=_("Calling Stable Diffusion /sdapi/v1/txt2img"),
            )

            Gimp.progress_set_text(_("Inserting layers from response"))

            self.handle_api_response(
                image,
                response,
                config_values["cn_skip_annotator_layers"],
                selectionWidth,
                selectionHeight,
                x1,
                y1,
                insert_mode,
            )

            return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())

        except Exception as ex:
            logging.exception("ERROR: StableGimpfusionPlugin.textToImage")
            Gimp.message(_("Error occurred: {error}").format(error=str(ex)))
            return procedure.new_return_values(
                Gimp.PDBStatusType.CALLING_ERROR,
                GLib.Error(message=repr(ex)),
            )
        finally:
            Gimp.progress_end()
            # self.cleanup()
            # self.files.removeAll()
            # self.checkUpdate()


# class Txt2imageContextPlugin(PluginBase):
#     menu_path = "<Layers>/GimpFusion"
#     menu_label = "Text to image"
#     description = "Text to image"
#
#     def add_arguments(self, procedure):
#         # PLUGIN_FIELDS_LAYERS + PLUGIN_FIELDS_TXT2IMG
#         # PLUGIN_FIELDS_TXT2IMG(procedure)
#         PLUGIN_FIELDS_COMMON(procedure, samplers=SAMPLERS, selected_sampler=self.settings.get("sampler_name"))
#         PLUGIN_FIELDS_CONTROLNET_OPTIONS(procedure)

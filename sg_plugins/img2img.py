from __future__ import annotations

import logging

from typing import Any

import gi

from sg_constants import RESIZE_MODES, SAMPLERS
from sg_gtk_utils import set_visibility_of
from sg_i18n import _
from sg_plugins.generation_base import GenerationPluginBase
from sg_proc_arguments import PLUGIN_FIELDS_COMMON, PLUGIN_FIELDS_CONTROLNET_OPTIONS, PLUGIN_FIELDS_RESIZE_MODE
from sg_structures import ResponseLayers, getActiveLayerAsBase64

gi.require_version("Gimp", "3.0")
gi.require_version("GimpUi", "3.0")
from gi.repository import Gimp, GimpUi, GLib


class Image2imagePlugin(GenerationPluginBase):
    menu_path = "<Image>/GimpFusion"
    menu_label = _("Image to image")
    description = _("Generate image based on other image")

    def add_arguments(self, procedure: Gimp.Procedure) -> None:
        # PLUGIN_FIELDS_IMG2IMG(procedure)
        PLUGIN_FIELDS_RESIZE_MODE(procedure, resize_modes=RESIZE_MODES)
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
        logging.getLogger().setLevel(level=logging.DEBUG if self.settings.get("debug_logging") else logging.INFO)

        if run_mode == Gimp.RunMode.INTERACTIVE:
            GimpUi.init(procedure.get_name())
            dialog = GimpUi.ProcedureDialog.new(procedure, config)

            vbox, grid = self.build_common_ui(procedure, config, dialog)
            boxes = self.build_common_parameter_boxes(dialog)
            resize_mode_box = dialog.fill_box("resize_mode_box", ["resize_mode"])
            mask_blur_box = dialog.fill_box("mask_blur_box", ["mask_blur"])

            grid.attach(boxes["width"], 0, 0, 2, 1)
            grid.attach(boxes["batch_size"], 2, 0, 1, 1)

            grid.attach(boxes["height"], 0, 1, 2, 1)
            grid.attach(boxes["steps"], 2, 1, 1, 1)

            grid.attach(boxes["cfg_scale"], 0, 2, 2, 1)
            grid.attach(boxes["seed"], 2, 2, 1, 1)

            grid.attach(resize_mode_box, 0, 3, 1, 1)
            grid.attach(boxes["sampler_index"], 1, 3, 1, 1)
            grid.attach(boxes["restore_faces"], 2, 3, 1, 1)

            grid.attach(boxes["denoising_strength"], 0, 4, 1, 1)
            grid.attach(mask_blur_box, 1, 4, 1, 1)
            grid.attach(boxes["tiling"], 2, 4, 1, 1)

            grid.attach(boxes["cn1_enabled"], 0, 6, 1, 1)
            grid.attach(boxes["cn2_enabled"], 1, 6, 1, 1)
            grid.attach(boxes["cn1_layer"], 0, 7, 1, 1)
            grid.attach(boxes["cn2_layer"], 1, 7, 1, 1)

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
                    resize_mode_box,
                    mask_blur_box,
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
                ],
            )

            if not dialog.run():
                return procedure.new_return_values(Gimp.PDBStatusType.CANCEL, GLib.Error())

        config_values = self.get_common_config_values(config)
        resize_mode = config.get_property("resize_mode")
        mask_blur = config.get_property("mask_blur")

        success, non_empty, x1, y1, x2, y2 = Gimp.Selection.bounds(image)
        selectionWidth, selectionHeight = x2 - x1, y2 - y1

        Gimp.progress_init(_("Saving active layer as base64"))

        data = self.build_base_data_dict(
            prompt=config_values["prompt"],
            negative_prompt=config_values["negative_prompt"],
            seed=config_values["seed"],
            batch_size=config_values["batch_size"],
            steps=config_values["steps"],
            cfg_scale=config_values["cfg_scale"],
            width=selectionWidth,
            height=selectionHeight,
            restore_faces=config_values["restore_faces"],
            tiling=config_values["tiling"],
            denoising_strength=config_values["denoising_strength"],
            sampler_index=config_values["sampler_index"],
        )
        data.update(
            {
                "init_images": [getActiveLayerAsBase64(image)],
                "resize_mode": RESIZE_MODES.index(resize_mode) if resize_mode in RESIZE_MODES else 0,
                "mask_blur": mask_blur,
            },
        )

        controlnet_units = self.build_controlnet_units(
            config_values["cn1_enabled"],
            config_values["cn1_layer"],
            config_values["cn2_enabled"],
            config_values["cn2_layer"],
        )
        self.add_controlnet_to_data(data, controlnet_units)

        # Merge with existing alwayson_scripts if any
        base_scripts = {
            "never oom integrated": {
                "args": [True, True],
            },
        }
        if "alwayson_scripts" in data:
            base_scripts.update(data["alwayson_scripts"])
        data["alwayson_scripts"] = base_scripts

        try:
            response = self.call_api_with_progress(
                "/sdapi/v1/img2img",
                data,
                progress_text=_("Calling Stable Diffusion /sdapi/v1/img2img"),
            )

            Gimp.progress_set_text(_("Inserting layers from response"))

            if "error" in response:
                return procedure.new_return_values(
                    Gimp.PDBStatusType.CALLING_ERROR,
                    GLib.Error(message=f"{response['error']}: {response.get('message')}"),
                )

            ResponseLayers(image, response, {"skip_annotator_layers": config_values["cn_skip_annotator_layers"]})
            # .resize(selectionWidth, selectionHeight).translate((x1, y1)).addSelectionAsMask()
            # Note: img2img doesn't resize/translate by default, but can be added if needed

            return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())

        except Exception as ex:
            logging.exception("ERROR: StableGimpfusionPlugin.imageToImage")
            Gimp.message(_("Error occurred: {error}").format(error=str(ex)))
            return procedure.new_return_values(
                Gimp.PDBStatusType.CALLING_ERROR,
                GLib.Error(message=repr(ex)),
            )
        finally:
            Gimp.progress_end()
            # self.cleanup()


# class Image2imageContextPlugin(PluginBase):
#     menu_path = "<Layers>/GimpFusion"
#     menu_label = "Image to image"
#     description = "Image to image"
#
#     def add_arguments(self, procedure):
#         # PLUGIN_FIELDS_LAYERS + PLUGIN_FIELDS_IMG2IMG
#         # PLUGIN_FIELDS_IMG2IMG(procedure)
#         PLUGIN_FIELDS_RESIZE_MODE(procedure, resize_modes=RESIZE_MODES)
#         PLUGIN_FIELDS_COMMON(procedure, samplers=SAMPLERS, selected_sampler=self.settings.get("sampler_name"))
#         PLUGIN_FIELDS_CONTROLNET_OPTIONS(procedure)
#
#     # handleImageToImageFromLayersContext

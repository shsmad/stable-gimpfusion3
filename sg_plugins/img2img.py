import logging
import random

import gi

from sg_constants import GENERATION_MESSAGES, MAX_BATCH_SIZE, RESIZE_MODES, SAMPLERS
from sg_plugins import PluginBase
from sg_proc_arguments import PLUGIN_FIELDS_COMMON, PLUGIN_FIELDS_CONTROLNET_OPTIONS, PLUGIN_FIELDS_RESIZE_MODE
from sg_structures import ResponseLayers, getActiveLayerAsBase64, getControlNetParams
from sg_utils import roundToMultiple

gi.require_version("Gimp", "3.0")
gi.require_version("GimpUi", "3.0")
from gi.repository import Gimp, GimpUi, GLib


class Image2imagePlugin(PluginBase):
    menu_path = "<Image>/GimpFusion"
    menu_label = "Image to image"
    description = "Image to image"

    def add_arguments(self, procedure):
        # PLUGIN_FIELDS_IMG2IMG(procedure)
        PLUGIN_FIELDS_RESIZE_MODE(procedure, resize_modes=RESIZE_MODES)
        PLUGIN_FIELDS_COMMON(procedure, samplers=SAMPLERS, selected_sampler=self.settings.get("sampler_name"))
        PLUGIN_FIELDS_CONTROLNET_OPTIONS(procedure)

    def main(self, procedure, run_mode, image, drawables, config, data):
        if run_mode == Gimp.RunMode.INTERACTIVE:
            GimpUi.init(procedure.get_name())
            dialog = GimpUi.ProcedureDialog.new(procedure, config)

            dialog.get_scale_entry("batch_size", 1)
            dialog.fill(["resize_mode"])
            dialog.fill(
                [
                    "prompt",
                    "negative_prompt",
                    "seed",
                    "batch_size",
                    "steps",
                    "mask_blur",
                    "width",
                    "height",
                    "cfg_scale",
                    "denoising_strength",
                    "sampler_index",
                    "restore_faces",
                    "tiling",
                    "cn1_enabled",
                    "cn1_layer",
                    "cn2_enabled",
                    "cn2_layer",
                    "cn_skip_annotator_layers",
                ],
            )

            if not dialog.run():
                return procedure.new_return_values(Gimp.PDBStatusType.CANCEL, GLib.Error())

        resize_mode = config.get_property("resize_mode")

        prompt = config.get_property("prompt")
        negative_prompt = config.get_property("negative_prompt")
        seed = config.get_property("seed")
        batch_size = config.get_property("batch_size")
        steps = config.get_property("steps")
        mask_blur = config.get_property("mask_blur")
        width = config.get_property("width")
        height = config.get_property("height")
        cfg_scale = config.get_property("cfg_scale")
        denoising_strength = config.get_property("denoising_strength")
        sampler_index = config.get_property("sampler_index")
        restore_faces = config.get_property("restore_faces")
        tiling = config.get_property("tiling")

        cn1_enabled = config.get_property("cn1_enabled")
        cn1_layer = config.get_property("cn1_layer")
        cn2_enabled = config.get_property("cn2_enabled")
        cn2_layer = config.get_property("cn2_layer")
        cn_skip_annotator_layers = config.get_property("cn_skip_annotator_layers")

        success, non_empty, x1, y1, x2, y2 = Gimp.Selection.bounds(image)
        origWidth, origHeight = x2 - x1, y2 - y1

        data = {
            "prompt": f"{prompt} {self.settings.get('prompt')}".strip(),
            "negative_prompt": f"{negative_prompt} {self.settings.get('negative_prompt')}".strip(),
            "seed": seed or -1,
            "batch_size": min(MAX_BATCH_SIZE, max(1, batch_size)),
            "steps": int(steps),
            "cfg_scale": float(cfg_scale),
            "width": roundToMultiple(width, 8),
            "height": roundToMultiple(height, 8),
            "restore_faces": restore_faces,
            "tiling": tiling,
            "denoising_strength": float(denoising_strength),
            "init_images": [getActiveLayerAsBase64(image)],
            "resize_mode": RESIZE_MODES.index(resize_mode),
            "mask_blur": mask_blur,
            "sampler_index": sampler_index if sampler_index in SAMPLERS else SAMPLERS[0],
        }

        try:
            Gimp.progress_init("")
            Gimp.progress_set_text(random.choice(GENERATION_MESSAGES))  # noqa: S311

            controlnet_units = []
            if cn1_enabled:
                controlnet_units.append(getControlNetParams(cn1_layer))
            if cn2_enabled:
                controlnet_units.append(getControlNetParams(cn2_layer))
            if controlnet_units:
                alwayson_scripts = {
                    "controlnet": {
                        "args": controlnet_units,
                    },
                }
                data["alwayson_scripts"] = alwayson_scripts

            response = self.api.post("/sdapi/v1/img2img", data)

            ResponseLayers(image, response, {"skip_annotator_layers": cn_skip_annotator_layers}).resize(
                origWidth,
                origHeight,
            )

            return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())

        except Exception as ex:
            logging.exception("ERROR: StableGimpfusionPlugin.imageToImage")
            Gimp.message(repr(ex))
            return procedure.new_return_values(
                Gimp.PDBStatusType.CALLING_ERROR,
                GLib.Error(message=repr(ex)),
            )
        finally:
            Gimp.progress_end()
            # self.cleanup()


class Image2imageContextPlugin(PluginBase):
    menu_path = "<Layers>/GimpFusion"
    menu_label = "Image to image"
    description = "Image to image"

    def add_arguments(self, procedure):
        # PLUGIN_FIELDS_LAYERS + PLUGIN_FIELDS_IMG2IMG
        # PLUGIN_FIELDS_IMG2IMG(procedure)
        PLUGIN_FIELDS_RESIZE_MODE(procedure, resize_modes=RESIZE_MODES)
        PLUGIN_FIELDS_COMMON(procedure, samplers=SAMPLERS, selected_sampler=self.settings.get("sampler_name"))
        PLUGIN_FIELDS_CONTROLNET_OPTIONS(procedure)

    # handleImageToImageFromLayersContext

from __future__ import annotations

import logging
import threading

from typing import Any

import gi

from sg_constants import INSERT_MODES, MAX_BATCH_SIZE, SAMPLERS
from sg_gtk_utils import add_textarea_to_container, set_visibility_control_by, set_visibility_of
from sg_i18n import _
from sg_plugins import PluginBase
from sg_proc_arguments import PLUGIN_FIELDS_COMMON, PLUGIN_FIELDS_CONTROLNET_OPTIONS
from sg_structures import ResponseLayers, getControlNetParams
from sg_utils import get_progress_at_background, roundToMultiple

gi.require_version("Gimp", "3.0")
gi.require_version("GimpUi", "3.0")
from gi.repository import Gimp, GimpUi, GLib, Gtk


class Txt2imagePlugin(PluginBase):
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

            vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, homogeneous=False, spacing=10)
            dialog.get_content_area().add(vbox)
            vbox.show()

            add_textarea_to_container(procedure, config, "prompt", vbox)
            add_textarea_to_container(procedure, config, "negative-prompt", vbox)

            # dialog.get_scale_entry("batch_size", 1)
            # dialog.get_scale_entry("steps", 1)
            dialog.get_scale_entry("width", 1).set_increments(8, 64)
            dialog.get_scale_entry("height", 1).set_increments(8, 64)
            dialog.get_scale_entry("cfg_scale", 1).set_increments(0.5, 1)
            # dialog.get_scale_entry("mask_blur", 1)

            # Create grid to set all the properties inside.
            grid = Gtk.Grid()
            grid.set_column_homogeneous(True)
            grid.set_column_spacing(10)
            grid.set_row_spacing(10)
            vbox.add(grid)
            grid.show()

            width_box = dialog.fill_box("width_box", ["width"])
            height_box = dialog.fill_box("height_box", ["height"])
            steps_box = dialog.fill_box("steps_box", ["steps"])
            cfg_scale_box = dialog.fill_box("cfg_scale_box", ["cfg_scale"])
            restore_faces_box = dialog.fill_box("restore_faces_box", ["restore_faces"])
            tiling_box = dialog.fill_box("tiling_box", ["tiling"])
            cn1_enabled_box = dialog.fill_box("cn1_enabled_box", ["cn1_enabled"])
            cn1_layer_box = dialog.fill_box("cn1_layer_box", ["cn1_layer"])
            cn2_enabled_box = dialog.fill_box("cn2_enabled_box", ["cn2_enabled"])
            cn2_layer_box = dialog.fill_box("cn2_layer_box", ["cn2_layer"])

            seed_box = dialog.fill_box("seed_box", ["seed"])
            batch_size_box = dialog.fill_box("batch_size_box", ["batch_size"])

            sampler_index_box = dialog.fill_box("sampler_index_box", ["sampler_index"])
            denoising_strength_box = dialog.fill_box("denoising_strength_box", ["denoising_strength"])

            # label = Gtk.Label.new_with_mnemonic("Scale")
            grid.attach(width_box, 0, 0, 2, 1)
            grid.attach(height_box, 2, 0, 2, 1)

            grid.attach(seed_box, 0, 1, 1, 1)
            grid.attach(steps_box, 1, 1, 1, 1)
            grid.attach(cfg_scale_box, 2, 1, 1, 1)
            grid.attach(batch_size_box, 3, 1, 1, 1)

            grid.attach(sampler_index_box, 0, 3, 1, 1)
            grid.attach(denoising_strength_box, 1, 3, 1, 1)
            grid.attach(restore_faces_box, 2, 3, 1, 1)
            grid.attach(tiling_box, 3, 3, 1, 1)

            grid.attach(cn1_enabled_box, 0, 5, 1, 1)
            grid.attach(cn2_enabled_box, 1, 5, 1, 1)
            grid.attach(cn1_layer_box, 0, 6, 1, 1)
            grid.attach(cn2_layer_box, 1, 6, 1, 1)

            set_visibility_of(
                [
                    width_box,
                    height_box,
                    steps_box,
                    cfg_scale_box,
                    restore_faces_box,
                    tiling_box,
                    cn1_enabled_box,
                    cn2_enabled_box,
                    seed_box,
                    batch_size_box,
                    sampler_index_box,
                    denoising_strength_box,
                ],
            )

            set_visibility_control_by(cn1_enabled_box, [cn1_layer_box])
            set_visibility_control_by(cn2_enabled_box, [cn2_layer_box])

            dialog.resize(800, 600)

            dialog.fill(
                [
                    "cn_skip_annotator_layers",
                    "insert_mode",
                ],
            )

            if not dialog.run():
                return procedure.new_return_values(Gimp.PDBStatusType.CANCEL, GLib.Error())

        prompt = config.get_property("prompt")
        negative_prompt = config.get_property("negative_prompt")
        seed = config.get_property("seed")
        batch_size = config.get_property("batch_size")
        steps = config.get_property("steps")
        # mask_blur = config.get_property("mask_blur")
        width = config.get_property("width")
        height = config.get_property("height")
        cfg_scale = config.get_property("cfg_scale")
        denoising_strength = config.get_property("denoising_strength")
        sampler_index = config.get_property("sampler_index")
        restore_faces = config.get_property("restore_faces")
        tiling = config.get_property("tiling")

        insert_mode = config.get_property("insert_mode")
        insert_mode = insert_mode if insert_mode in INSERT_MODES else INSERT_MODES[0]

        cn1_enabled = config.get_property("cn1_enabled")
        cn1_layer = config.get_property("cn1_layer")
        cn2_enabled = config.get_property("cn2_enabled")
        cn2_layer = config.get_property("cn2_layer")
        cn_skip_annotator_layers = config.get_property("cn_skip_annotator_layers")

        success, non_empty, x1, y1, x2, y2 = Gimp.Selection.bounds(image)
        selectionWidth, selectionHeight = x2 - x1, y2 - y1

        data = {
            "prompt": f"{prompt} {self.settings.get('prompt')}".strip(),
            "negative_prompt": f"{negative_prompt} {self.settings.get('negative_prompt')}".strip(),
            "seed": seed or -1,
            "batch_size": min(MAX_BATCH_SIZE, max(1, batch_size)),
            "steps": int(steps),
            "cfg_scale": float(cfg_scale),
            "width": roundToMultiple(selectionWidth if insert_mode == "Use selection size" else width, 8),
            "height": roundToMultiple(selectionHeight if insert_mode == "Use selection size" else height, 8),
            "restore_faces": restore_faces,
            "tiling": tiling,
            "denoising_strength": float(denoising_strength),
            "enable_hr": False,
            "sampler_index": sampler_index if sampler_index in SAMPLERS else SAMPLERS[0],
        }

        Gimp.progress_init(_("Calling Stable Diffusion /sdapi/v1/txt2img"))

        try:
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

            logging.debug("starting thread")
            thread = threading.Thread(target=get_progress_at_background, args=(self.api,), daemon=True)
            thread.start()

            logging.debug("requesting")
            response = self.api.post("/sdapi/v1/txt2img", data)

            thread.join()

            Gimp.progress_set_text(_("Inserting layers from response"))

            if "error" in response:
                Gimp.message(f"{response['error']}: {response.get('message')}")
                return procedure.new_return_values(
                    Gimp.PDBStatusType.CALLING_ERROR,
                    GLib.Error(message=repr(response.get("message") or response["error"])),
                )

            ResponseLayers(image, response, {"skip_annotator_layers": cn_skip_annotator_layers}).resize(
                selectionWidth,
                selectionHeight,
                strategy=insert_mode,
            ).translate((x1, y1)).addSelectionAsMask()

            return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())

        except Exception as ex:
            logging.exception("ERROR: StableGimpfusionPlugin.textToImage")
            Gimp.message(repr(ex))
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

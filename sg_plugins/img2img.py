import logging
import threading

import gi

from sg_constants import MAX_BATCH_SIZE, RESIZE_MODES, SAMPLERS
from sg_gtk_utils import add_textarea_to_container, set_visibility_control_by, set_visibility_of
from sg_i18n import _
from sg_plugins import PluginBase
from sg_proc_arguments import PLUGIN_FIELDS_COMMON, PLUGIN_FIELDS_CONTROLNET_OPTIONS, PLUGIN_FIELDS_RESIZE_MODE
from sg_structures import ResponseLayers, getActiveLayerAsBase64, getControlNetParams
from sg_utils import get_progress_at_background, roundToMultiple

gi.require_version("Gimp", "3.0")
gi.require_version("GimpUi", "3.0")
from gi.repository import Gimp, GimpUi, GLib, Gtk


class Image2imagePlugin(PluginBase):
    menu_path = "<Image>/GimpFusion"
    menu_label = _("Image to image")
    description = _("Generate image based on other image")

    def add_arguments(self, procedure):
        # PLUGIN_FIELDS_IMG2IMG(procedure)
        PLUGIN_FIELDS_RESIZE_MODE(procedure, resize_modes=RESIZE_MODES)
        PLUGIN_FIELDS_COMMON(procedure, samplers=SAMPLERS, selected_sampler=self.settings.get("sampler_name"))
        PLUGIN_FIELDS_CONTROLNET_OPTIONS(procedure)

    def main(self, procedure, run_mode, image, drawables, config, data):
        logging.getLogger().setLevel(level=logging.DEBUG if self.settings.get("debug_logging") else logging.INFO)

        if run_mode == Gimp.RunMode.INTERACTIVE:
            GimpUi.init(procedure.get_name())
            dialog = GimpUi.ProcedureDialog.new(procedure, config)

            vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, homogeneous=False, spacing=10)
            dialog.get_content_area().add(vbox)
            vbox.show()

            add_textarea_to_container(procedure, config, "prompt", vbox)
            add_textarea_to_container(procedure, config, "negative-prompt", vbox)

            dialog.get_scale_entry("width", 1).set_increments(8, 64)
            dialog.get_scale_entry("height", 1).set_increments(8, 64)
            dialog.get_scale_entry("cfg_scale", 1).set_increments(0.5, 1)

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

            resize_mode_box = dialog.fill_box("resize_mode_box", ["resize_mode"])
            mask_blur_box = dialog.fill_box("mask_blur_box", ["mask_blur"])

            grid.attach(width_box, 0, 0, 2, 1)
            grid.attach(batch_size_box, 2, 0, 1, 1)

            grid.attach(height_box, 0, 1, 2, 1)
            grid.attach(steps_box, 2, 1, 1, 1)

            grid.attach(cfg_scale_box, 0, 2, 2, 1)
            grid.attach(seed_box, 2, 2, 1, 1)

            grid.attach(resize_mode_box, 0, 3, 1, 1)
            grid.attach(sampler_index_box, 1, 3, 1, 1)
            grid.attach(restore_faces_box, 2, 3, 1, 1)

            grid.attach(denoising_strength_box, 0, 4, 1, 1)
            grid.attach(mask_blur_box, 1, 4, 1, 1)
            grid.attach(tiling_box, 2, 4, 1, 1)


            grid.attach(cn1_enabled_box, 0, 6, 1, 1)
            grid.attach(cn2_enabled_box, 1, 6, 1, 1)
            grid.attach(cn1_layer_box, 0, 7, 1, 1)
            grid.attach(cn2_layer_box, 1, 7, 1, 1)

            set_visibility_of([
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
                resize_mode_box,
                mask_blur_box,
            ])

            set_visibility_control_by(cn1_enabled_box, [cn1_layer_box])
            set_visibility_control_by(cn2_enabled_box, [cn2_layer_box])

            dialog.resize(800, 600)

            dialog.fill(
                [
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
        selectionWidth, selectionHeight = x2 - x1, y2 - y1

        Gimp.progress_init(_("Saving active layer as base64"))

        data = {
            "prompt": f"{prompt} {self.settings.get('prompt')}".strip(),
            "negative_prompt": f"{negative_prompt} {self.settings.get('negative_prompt')}".strip(),
            "seed": seed or -1,
            "batch_size": min(MAX_BATCH_SIZE, max(1, batch_size)),
            "steps": int(steps),
            "cfg_scale": float(cfg_scale),
            "width": roundToMultiple(selectionWidth, 8),
            "height": roundToMultiple(selectionHeight, 8),
            "restore_faces": restore_faces,
            "tiling": tiling,
            "denoising_strength": float(denoising_strength),
            "init_images": [getActiveLayerAsBase64(image)],
            "resize_mode": RESIZE_MODES.index(resize_mode),
            "mask_blur": mask_blur,
            "sampler_index": sampler_index if sampler_index in SAMPLERS else SAMPLERS[0],
        }

        Gimp.progress_set_text(_("Calling Stable Diffusion /sdapi/v1/img2img"))
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


            # Merge with existing alwayson_scripts if any
            base_scripts = {
                "never oom integrated": {
                    "args": [True, True],
                },
                # "multidiffusion integrated": {
                #     "args": [True, "MultiDiffusion", 768, 768, 64, 64],
                # },
            }
            if "alwayson_scripts" in data:
                base_scripts.update(data["alwayson_scripts"])
            data["alwayson_scripts"] = base_scripts

            logging.debug("starting thread")
            thread = threading.Thread(target=get_progress_at_background, args=(self.api,), daemon=True)
            thread.start()

            logging.debug("requesting")
            response = self.api.post("/sdapi/v1/img2img", data)

            thread.join()

            Gimp.progress_set_text(_("Inserting layers from response"))

            if "error" in response:
                # Gimp.message(f"{response['error']}: {response.get('message')}")
                return procedure.new_return_values(
                    Gimp.PDBStatusType.CALLING_ERROR,
                    GLib.Error(message=f"{response['error']}: {response.get('message')}"),
                )

            ResponseLayers(image, response, {"skip_annotator_layers": cn_skip_annotator_layers})
            #.resize(selectionWidth, selectionHeight).translate((x1, y1)).addSelectionAsMask()

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

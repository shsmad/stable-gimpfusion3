import logging

import gi

from sg_plugins import PluginBase
from sg_utils import set_logging_dest

gi.require_version("Gimp", "3.0")
gi.require_version("GimpUi", "3.0")
from gi.repository import Gimp, GimpUi, GLib, GObject

from sg_proc_arguments import PLUGIN_FIELDS_CHECKPOINT


class ConfigPlugin(PluginBase):
    menu_path = "<Image>/GimpFusion/Config"
    menu_label = "Global"
    description = "This is where you configure params that are shared between all API requests"

    def add_arguments(self, procedure):
        procedure.add_string_argument("prompt", "Prompt Suffix", "Prompt Suffix", "", GObject.ParamFlags.READWRITE)
        procedure.add_string_argument(
            "negative_prompt",
            "Negative Prompt Suffix",
            "Negative Prompt Suffix",
            "",
            GObject.ParamFlags.READWRITE,
        )
        procedure.add_string_argument(
            "api_base",
            "Backend API URL base",
            "Backend API URL base",
            "http://127.0.0.1:7860/",
            GObject.ParamFlags.READWRITE,
        )
        procedure.add_boolean_argument(
            "debug_logging",
            "Debug logging",
            "INFO if not set, DEBUG if set logging level",
            False,
            GObject.ParamFlags.READWRITE,
        )
        procedure.add_boolean_argument(
            "file_logging",
            "Log to file",
            "Log to file or console",
            False,
            GObject.ParamFlags.READWRITE,
        )

    def main(self, procedure, run_mode, image, drawables, config, data):
        # logging.debug(f"main run({procedure=}, {run_mode=}, {image=}, {drawables=}, {config=}, {data=})")

        if run_mode == Gimp.RunMode.INTERACTIVE:
            GimpUi.init(procedure.get_name())
            dialog = GimpUi.ProcedureDialog.new(procedure, config)

            dialog.fill(["prompt", "negative_prompt", "api_base", "debug_logging", "file_logging"])

            if not dialog.run():
                return procedure.new_return_values(Gimp.PDBStatusType.CANCEL, GLib.Error())

        prompt = config.get_property("prompt")
        negative_prompt = config.get_property("negative_prompt")
        api_base = config.get_property("api_base")
        debug_logging = config.get_property("debug_logging")
        file_logging = config.get_property("file_logging")

        logging.getLogger().setLevel(level=logging.DEBUG if debug_logging else logging.INFO)

        if file_logging != self.settings.get("file_logging"):
            set_logging_dest(file_logging)

        self.settings.save(
            {
                "prompt": prompt,
                "negative_prompt": negative_prompt,
                "api_base": api_base,
                "debug_logging": debug_logging,
                "file_logging": file_logging,
            },
        )
        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())


class ConfigModelPlugin(PluginBase):
    menu_path = "<Image>/GimpFusion/Config"
    menu_label = "Change Model"
    description = "Change the Checkpoint Model"

    def add_arguments(self, procedure):
        PLUGIN_FIELDS_CHECKPOINT(
            procedure,
            models=self.settings.get("models"),
            selected_model=self.settings.get("sd_model_checkpoint"),
        )

    def main(self, procedure, run_mode, image, drawables, config, data):
        if run_mode == Gimp.RunMode.INTERACTIVE:
            GimpUi.init(procedure.get_name())
            dialog = GimpUi.ProcedureDialog.new(procedure, config)

            dialog.get_int_combo("model", GimpUi.IntStore.new(self.settings.get("models")))

            dialog.fill(["model"])

            if not dialog.run():
                return procedure.new_return_values(Gimp.PDBStatusType.CANCEL, GLib.Error())

        model = config.get_property("model")

        if self.settings.get("model") != model:
            Gimp.progress_init("")
            Gimp.progress_set_text("Changing model...")

            try:
                # self.api.post("/sdapi/v1/options", {"sd_model_checkpoint": models[model]})
                self.api.post("/sdapi/v1/options", data={"sd_model_checkpoint": model})
                self.settings.set("sd_model_checkpoint", model)
            except Exception as e:
                logging.error(e)

            Gimp.progress_end()

        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())

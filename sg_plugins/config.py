import logging

import gi

from sg_gtk_utils import add_textarea_to_container
from sg_i18n import _
from sg_plugins import PluginBase
from sg_utils import set_logging_dest

gi.require_version("Gimp", "3.0")
gi.require_version("GimpUi", "3.0")
gi.require_version("Gtk", "3.0")
from gi.repository import Gimp, GimpUi, GLib, GObject, Gtk

from sg_proc_arguments import PLUGIN_FIELDS_CHECKPOINT


class ConfigPlugin(PluginBase):
    menu_path = "<Image>/GimpFusion/Config"
    menu_label = _("Global")
    description = _("This is where you configure params that are shared between all API requests")

    def add_arguments(self, procedure):
        procedure.add_string_argument(
            "prompt",
            _("Prompt Suffix"),
            _("Prompt Suffix to add to the prompt automatically"),
            "beauty, good skin, sharp skin, ultra detailed skin, high quality, RAW photo, analog film, 35mm photograph, 32K UHD, close-up, ultra realistic, clean",  # noqa: E501
            GObject.ParamFlags.READWRITE,
        )
        procedure.add_string_argument(
            "negative_prompt",
            _("Negative Prompt Suffix"),
            _("Negative Prompt Suffix to add to the negative prompt automatically"),
            "(deformed, distorted, disfigured:1.3), poorly drawn, bad anatomy, wrong anatomy, extra limb, missing limb, floating limbs, (mutated hands and fingers:1.4), disconnected limbs, mutation, mutated, ugly, disgusting, blurry, amputation",  # noqa: E501
            GObject.ParamFlags.READWRITE,
        )
        procedure.add_string_argument(
            "api_base",
            _("Backend API URL base"),
            _("Backend API URL base to use for requests"),
            "http://127.0.0.1:7860/",
            GObject.ParamFlags.READWRITE,
        )
        procedure.add_boolean_argument(
            "debug_logging",
            _("Debug logging"),
            _("INFO if not set, DEBUG if set logging level"),
            False,
            GObject.ParamFlags.READWRITE,
        )
        procedure.add_boolean_argument(
            "file_logging",
            _("Log to file"),
            _("Log to file or console"),
            False,
            GObject.ParamFlags.READWRITE,
        )

    def main(self, procedure, run_mode, image, drawables, config, data):
        # logging.debug(f"main run({procedure=}, {run_mode=}, {image=}, {drawables=}, {config=}, {data=})")

        if run_mode == Gimp.RunMode.INTERACTIVE:
            GimpUi.init(procedure.get_name())
            dialog = GimpUi.ProcedureDialog.new(procedure, config, title=_("Global gimpfusion settings"))

            vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, homogeneous=False, spacing=10)
            dialog.get_content_area().add(vbox)
            vbox.show()

            # props = dialog.fill_box("box1", ["api_base", "debug_logging", "file_logging"])
            # wid = dialog.fill_frame("box2", None, False, "box1")
            # wid.set_label("tutkee")

            add_textarea_to_container(procedure, config, "prompt", vbox)
            add_textarea_to_container(procedure, config, "negative-prompt", vbox)

            dialog.fill(["api_base", "debug_logging", "file_logging"])

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
    menu_label = _("Change Model")
    description = _("Change the Checkpoint Model")

    def add_arguments(self, procedure):
        PLUGIN_FIELDS_CHECKPOINT(
            procedure,
            models=self.settings.get("models"),
            selected_model=self.settings.get("sd_model_checkpoint"),
            sd_modules=self.settings.get("sd_modules"),
        )

    def main(self, procedure, run_mode, image, drawables, config, data):
        if run_mode == Gimp.RunMode.INTERACTIVE:
            GimpUi.init(procedure.get_name())
            dialog = GimpUi.ProcedureDialog.new(procedure, config)

            dialog.get_int_combo("model", GimpUi.IntStore.new(self.settings.get("models")))

            dialog.fill(["model", "flux_encoders_mode"])

            vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, homogeneous=False, spacing=10)
            dialog.get_content_area().add(vbox)
            vbox.show()

            add_textarea_to_container(procedure, config, "flux_encoders", vbox)

            if not dialog.run():
                return procedure.new_return_values(Gimp.PDBStatusType.CANCEL, GLib.Error())

        model = config.get_property("model")
        flux_encoders_mode = config.get_property("flux_encoders_mode")
        flux_encoders = config.get_property("flux_encoders")

        data = {"sd_model_checkpoint": model}
        if flux_encoders_mode == "Always add" or (
            flux_encoders_mode == "Autoguess" and ("flux" in model.lower() or model.lower().endswith(".gguf"))
        ):
            data["forge_additional_modules"] = flux_encoders.splitlines()
        elif flux_encoders_mode == "Never add":
            data["forge_additional_modules"] = []

        if self.settings.get("model") != model:
            Gimp.progress_init("")
            Gimp.progress_set_text(_("Changing model..."))

            try:
                # self.api.post("/sdapi/v1/options", {"sd_model_checkpoint": models[model]})
                self.api.post("/sdapi/v1/options", data=data)
                self.settings.set("sd_model_checkpoint", model)
            except Exception as e:
                logging.error(e)

                return procedure.new_return_values(
                    Gimp.PDBStatusType.CALLING_ERROR,
                    GLib.Error(message=e),
                )

            Gimp.progress_end()

        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())

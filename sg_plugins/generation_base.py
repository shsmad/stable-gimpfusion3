"""
Base class for image generation plugins (txt2img, img2img, inpainting).
Contains common UI building and ControlNet handling logic.
"""

from __future__ import annotations

import logging
import threading

from typing import Any

import gi

from sg_constants import INSERT_MODES, MAX_BATCH_SIZE, SAMPLERS
from sg_gtk_utils import add_textarea_to_container, set_visibility_control_by
from sg_plugins import PluginBase
from sg_structures import ResponseLayers, getControlNetParams
from sg_utils import get_progress_at_background, roundToMultiple

gi.require_version("Gimp", "3.0")
gi.require_version("GimpUi", "3.0")
from gi.repository import Gimp, GimpUi, Gtk


class GenerationPluginBase(PluginBase):
    """Base class for image generation plugins with common UI and ControlNet handling"""

    def build_common_ui(
        self,
        procedure: Gimp.Procedure,
        config: Gimp.ProcedureConfig,
        dialog: GimpUi.ProcedureDialog,
        additional_fields: list[str] | None = None,
    ) -> tuple[Gtk.Box, Gtk.Grid]:
        """
        Build common UI elements for generation plugins.

        Args:
            procedure: GIMP procedure
            config: Procedure config
            dialog: Dialog instance
            additional_fields: List of additional field names to fill

        Returns:
            Tuple of (vbox, grid) for further customization
        """
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, homogeneous=False, spacing=10)
        dialog.get_content_area().add(vbox)
        vbox.show()

        # Add prompt textareas
        add_textarea_to_container(procedure, config, "prompt", vbox)
        add_textarea_to_container(procedure, config, "negative-prompt", vbox)

        # Set increments for scale entries
        dialog.get_scale_entry("width", 1).set_increments(8, 64)
        dialog.get_scale_entry("height", 1).set_increments(8, 64)
        dialog.get_scale_entry("cfg_scale", 1).set_increments(0.5, 1)

        # Create grid for parameters
        grid = Gtk.Grid()
        grid.set_column_homogeneous(True)
        grid.set_column_spacing(10)
        grid.set_row_spacing(10)
        vbox.add(grid)
        grid.show()

        # Fill additional fields if provided
        if additional_fields:
            dialog.fill(additional_fields)

        return vbox, grid

    def build_common_parameter_boxes(
        self,
        dialog: GimpUi.ProcedureDialog,
    ) -> dict[str, Gtk.Widget]:
        """
        Build common parameter boxes for generation plugins.

        Returns:
            Dictionary mapping parameter names to their widget boxes
        """
        boxes = {
            "width": dialog.fill_box("width_box", ["width"]),
            "height": dialog.fill_box("height_box", ["height"]),
            "steps": dialog.fill_box("steps_box", ["steps"]),
            "cfg_scale": dialog.fill_box("cfg_scale_box", ["cfg_scale"]),
            "restore_faces": dialog.fill_box("restore_faces_box", ["restore_faces"]),
            "tiling": dialog.fill_box("tiling_box", ["tiling"]),
            "cn1_enabled": dialog.fill_box("cn1_enabled_box", ["cn1_enabled"]),
            "cn1_layer": dialog.fill_box("cn1_layer_box", ["cn1_layer"]),
            "cn2_enabled": dialog.fill_box("cn2_enabled_box", ["cn2_enabled"]),
            "cn2_layer": dialog.fill_box("cn2_layer_box", ["cn2_layer"]),
            "seed": dialog.fill_box("seed_box", ["seed"]),
            "batch_size": dialog.fill_box("batch_size_box", ["batch_size"]),
            "sampler_index": dialog.fill_box("sampler_index_box", ["sampler_index"]),
            "denoising_strength": dialog.fill_box("denoising_strength_box", ["denoising_strength"]),
        }
        return boxes

    def setup_controlnet_visibility(
        self,
        cn1_enabled_box: Gtk.Widget,
        cn1_layer_box: Gtk.Widget,
        cn2_enabled_box: Gtk.Widget,
        cn2_layer_box: Gtk.Widget,
    ) -> None:
        """Setup visibility control for ControlNet layers"""
        set_visibility_control_by(cn1_enabled_box, [cn1_layer_box])
        set_visibility_control_by(cn2_enabled_box, [cn2_layer_box])

    def get_common_config_values(self, config: Gimp.ProcedureConfig) -> dict[str, Any]:
        """
        Extract common configuration values from config.

        Returns:
            Dictionary with common parameter values
        """
        return {
            "prompt": config.get_property("prompt"),
            "negative_prompt": config.get_property("negative_prompt"),
            "seed": config.get_property("seed"),
            "batch_size": config.get_property("batch_size"),
            "steps": config.get_property("steps"),
            "width": config.get_property("width"),
            "height": config.get_property("height"),
            "cfg_scale": config.get_property("cfg_scale"),
            "sampler_index": config.get_property("sampler_index"),
            "restore_faces": config.get_property("restore_faces"),
            "tiling": config.get_property("tiling"),
            "denoising_strength": config.get_property("denoising_strength"),
            "cn1_enabled": config.get_property("cn1_enabled"),
            "cn1_layer": config.get_property("cn1_layer"),
            "cn2_enabled": config.get_property("cn2_enabled"),
            "cn2_layer": config.get_property("cn2_layer"),
            "cn_skip_annotator_layers": config.get_property("cn_skip_annotator_layers"),
        }

    def build_controlnet_units(
        self,
        cn1_enabled: bool,
        cn1_layer: Gimp.Layer | None,
        cn2_enabled: bool,
        cn2_layer: Gimp.Layer | None,
    ) -> list[dict[str, Any]]:
        """
        Build ControlNet units from configuration.

        Args:
            cn1_enabled: Whether ControlNet 1 is enabled
            cn1_layer: ControlNet 1 layer
            cn2_enabled: Whether ControlNet 2 is enabled
            cn2_layer: ControlNet 2 layer

        Returns:
            List of ControlNet unit dictionaries
        """
        controlnet_units = []
        if cn1_enabled and cn1_layer:
            params = getControlNetParams(cn1_layer)
            if params:
                controlnet_units.append(params)
        if cn2_enabled and cn2_layer:
            params = getControlNetParams(cn2_layer)
            if params:
                controlnet_units.append(params)
        return controlnet_units

    def build_base_data_dict(
        self,
        prompt: str,
        negative_prompt: str,
        seed: int,
        batch_size: int,
        steps: int,
        cfg_scale: float,
        width: int,
        height: int,
        restore_faces: bool,
        tiling: bool,
        denoising_strength: float,
        sampler_index: str,
    ) -> dict[str, Any]:
        """
        Build base data dictionary with common parameters.

        Returns:
            Dictionary with common API parameters
        """
        return {
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
            "sampler_index": sampler_index if sampler_index in SAMPLERS else SAMPLERS[0],
        }

    def add_controlnet_to_data(self, data: dict[str, Any], controlnet_units: list[dict[str, Any]]) -> None:
        """
        Add ControlNet units to data dictionary.

        Args:
            data: Data dictionary to modify
            controlnet_units: List of ControlNet unit dictionaries
        """
        if controlnet_units:
            data["alwayson_scripts"] = {
                "controlnet": {
                    "args": controlnet_units,
                },
            }

    def call_api_with_progress(
        self,
        endpoint: str,
        data: dict[str, Any],
        progress_text: str | None = None,
    ) -> dict[str, Any]:
        """
        Call API endpoint with progress tracking in background thread.

        Args:
            endpoint: API endpoint to call
            data: Data to send
            progress_text: Optional progress text

        Returns:
            API response dictionary
        """
        if progress_text:
            Gimp.progress_init(progress_text)
        else:
            Gimp.progress_init("")

        logging.debug("starting thread")
        thread = threading.Thread(target=get_progress_at_background, args=(self.api,), daemon=True)
        thread.start()

        logging.debug("requesting")
        response = self.api.post(endpoint, data)

        thread.join()

        return response

    def handle_api_response(
        self,
        image: Gimp.Image,
        response: dict[str, Any],
        cn_skip_annotator_layers: bool,
        selection_width: int,
        selection_height: int,
        selection_x: int,
        selection_y: int,
        insert_mode: str = INSERT_MODES[0],
    ) -> ResponseLayers:
        """
        Handle API response and create ResponseLayers.

        Args:
            image: GIMP image
            response: API response
            cn_skip_annotator_layers: Whether to skip annotator layers
            selection_width: Selection width
            selection_height: Selection height
            selection_x: Selection X coordinate
            selection_y: Selection Y coordinate
            insert_mode: Insert mode strategy

        Returns:
            ResponseLayers instance
        """
        if "error" in response:
            raise ValueError(f"{response['error']}: {response.get('message', '')}")

        response_layers = ResponseLayers(
            image,
            response,
            {"skip_annotator_layers": cn_skip_annotator_layers},
        )

        response_layers.resize(
            selection_width,
            selection_height,
            strategy=insert_mode if insert_mode in INSERT_MODES else INSERT_MODES[0],
        ).translate((selection_x, selection_y)).addSelectionAsMask()

        return response_layers

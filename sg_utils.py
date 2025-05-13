from __future__ import annotations

import logging
import os
import tempfile

from typing import TYPE_CHECKING, Any

import gi

if TYPE_CHECKING:
    from sg_structures import ApiClient

gi.require_version("Gimp", "3.0")
from gi.repository import Gimp


def make_choice_from_dict(data: dict[str, Any]) -> Gimp.Choice:
    choise = Gimp.Choice.new()
    # nick, id, label, help
    for key, value in data.items():
        choise.add(value, key, value, value)

    return choise


def make_choice_from_list(data: list[str]) -> Gimp.Choice:
    choise = Gimp.Choice.new()
    # nick, id, label, help
    for key, value in enumerate(data):
        choise.add(value, key, value, value)

    return choise


def roundToMultiple(value, multiple):
    return multiple * round(float(value) / multiple)


def fetch_stablediffusion_options(api: ApiClient) -> dict[str, Any]:
    """Get the StableDiffusion data needed for dynamic gimpfu.PF_OPTION lists"""

    options = api.get("/sdapi/v1/options") or {}
    sd_model_checkpoint = options.get("sd_model_checkpoint", None)
    models = [x["title"].removesuffix(f" [{x.get('hash')}]") for x in api.get("/sdapi/v1/sd-models") or []]
    sd_modules = [x["filename"] for x in api.get("/sdapi/v1/sd-modules") or []]
    cn_models = (api.get("/controlnet/model_list") or {}).get("model_list", [])

    # /sdapi/v1/samplers, /sdapi/v1/schedulers, /sdapi/v1/upscalers
    # /sdapi/v1/scripts, /sdapi/v1/script-info

    return {
        "models": models,
        "sd_modules": sd_modules,
        "cn_models": cn_models,
        "sd_model_checkpoint": sd_model_checkpoint,
        "is_server_running": True,
    }


def set_logging_dest(use_file_logging: bool) -> None:
    logging_file = os.path.join(tempfile.gettempdir(), "gimpfusion.log")
    new_handler = logging.FileHandler(logging_file) if use_file_logging else logging.StreamHandler()
    new_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    root_logger = logging.getLogger()
    for old_handler in root_logger.handlers[:]:
        root_logger.removeHandler(old_handler)
    root_logger.addHandler(new_handler)

def aspect_resize(selection_width, selection_height, image_width, image_height, fill=False):
    scale_factor_w = selection_width / image_width
    scale_factor_h = selection_height / image_height
    scale_factor = max(scale_factor_w, scale_factor_h) if fill else min(scale_factor_w, scale_factor_h)
    return int(image_width * scale_factor), int(image_height * scale_factor)

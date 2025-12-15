from __future__ import annotations

import logging
import os
import tempfile
import time

from typing import TYPE_CHECKING, Any

import gi

if TYPE_CHECKING:
    from sg_structures import ApiClient

gi.require_version("Gimp", "3.0")
from gi.repository import Gimp


def make_choice_from_dict(data: dict[str, Any]) -> Gimp.Choice:
    choice = Gimp.Choice.new()
    # nick, id, label, help
    for key, value in data.items():
        choice.add(value, key, value, value)

    return choice


def make_choice_from_list(data: list[str]) -> Gimp.Choice:
    choice = Gimp.Choice.new()
    # nick, id, label, help
    for key, value in enumerate(data):
        choice.add(value, key, value, value)

    return choice


def roundToMultiple(value: float | int, multiple: int) -> int:
    return multiple * round(float(value) / multiple)


def fetch_stablediffusion_options(api: ApiClient) -> dict[str, Any]:
    """Get the StableDiffusion data needed for dynamic gimpfu.PF_OPTION lists"""

    has_sd_modules_support = True

    options = api.get("/sdapi/v1/options") or {}
    sd_model_checkpoint = options.get("sd_model_checkpoint", None)
    models = [x["title"].removesuffix(f" [{x.get('hash')}]") for x in api.get("/sdapi/v1/sd-models") or []]
    sd_modules = []
    cn_models = (api.get("/controlnet/model_list") or {}).get("model_list", [])

    try:
        sd_modules = [x["filename"] for x in api.get("/sdapi/v1/sd-modules") or []]
    except Exception as ex:
        has_sd_modules_support = False
        logging.warning(f"sd-modules not supported on SD instance: {ex}")


    # /sdapi/v1/samplers, /sdapi/v1/schedulers, /sdapi/v1/upscalers
    # /sdapi/v1/scripts, /sdapi/v1/script-info

    return {
        "models": models,
        "sd_modules": sd_modules,
        "cn_models": cn_models,
        "sd_model_checkpoint": sd_model_checkpoint,
        "is_server_running": True,
        "has_sd_modules_support": has_sd_modules_support,
    }


def set_logging_dest(use_file_logging: bool) -> None:
    logging_file = os.path.join(tempfile.gettempdir(), "gimpfusion.log")
    new_handler = logging.FileHandler(logging_file) if use_file_logging else logging.StreamHandler()
    new_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    root_logger = logging.getLogger()
    for old_handler in root_logger.handlers[:]:
        root_logger.removeHandler(old_handler)
    root_logger.addHandler(new_handler)


def aspect_resize(
    selection_width: int,
    selection_height: int,
    image_width: int,
    image_height: int,
    fill: bool = False,
) -> tuple[int, int]:
    scale_factor_w = selection_width / image_width
    scale_factor_h = selection_height / image_height
    scale_factor = max(scale_factor_w, scale_factor_h) if fill else min(scale_factor_w, scale_factor_h)
    return int(image_width * scale_factor), int(image_height * scale_factor)


def get_progress_at_background(api: ApiClient) -> None:
    progress = 0
    job_count = -1
    try:
        while progress < 1 and job_count != 0:
            time.sleep(2)
            result = api.get("/sdapi/v1/progress", params={"skip_current_image": "true"})
            if not result or "progress" not in result:
                logging.warning("Invalid progress response, stopping")
                break
            progress = result.get("progress", 0)
            state = result.get("state", {})
            job_count = state.get("job_count", 0)
            eta = result.get("eta_relative", 0)

            Gimp.progress_update(progress)
            Gimp.progress_set_text(f"Progress: {round(progress * 100, 2)}%, ETA: {round(eta)}s")
            logging.debug(f"get_progress_at_background {result=}")
    except Exception as ex:
        logging.exception(f"Error in progress thread: {ex}")
    finally:
        Gimp.progress_end()

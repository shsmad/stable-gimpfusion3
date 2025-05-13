AUTHOR = "SHSMAD"

MAX_BATCH_SIZE = 20

STABLE_GIMPFUSION_DEFAULT_SETTINGS = {
    "sampler_name": "Euler a",
    "denoising_strength": 0.8,
    "cfg_scale": 7.5,
    "steps": 50,
    "width": 512,
    "height": 512,
    "prompt": "",
    "negative_prompt": "",
    "batch_size": 1,
    "mask_blur": 4,
    "seed": -1,
    "api_base": "http://127.0.0.1:7860",
    "model": "",
    "models": [],
    "cn_models": [],
    "sd_model_checkpoint": None,
    "is_server_running": False,
}

RESIZE_MODES = [
    "Just Resize",
    "Crop And Resize",
    "Resize And Fill",
    "Just Resize (Latent Upscale)",
]

CONTROL_MODES = [
    "Balanced",
    "My prompt is more important",
    "ControlNet is more important",
]

SAMPLERS = [
    "Euler a",
    "Euler",
    "LMS",
    "Heun",
    "DPM2",
    "DPM2 a",
    "DPM++ 2S a",
    "DPM++ 2M",
    "DPM++ SDE",
    "DPM fast",
    "DPM adaptive",
    "LMS Karras",
    "DPM2 Karras",
    "DPM2 a Karras",
    "DPM++ 2S a Karras",
    "DPM++ 2M Karras",
    "DPM++ SDE Karras",
    "DDIM",
]

CONTROLNET_RESIZE_MODES = [
    "Just Resize",
    "Scale to Fit (Inner Fit)",
    "Envelope (Outer Fit)",
]

CONTROLNET_MODULES = [
    "none",
    "canny",
    "depth",
    "depth_leres",
    "hed",
    "mlsd",
    "normal_map",
    "openpose",
    "openpose_hand",
    "clip_vision",
    "color",
    "pidinet",
    "scribble",
    "fake_scribble",
    "segmentation",
    "binary",
]

CONTROLNET_DEFAULT_SETTINGS = {
    "input_image": "",
    "mask": "",
    "module": "none",
    "model": "none",
    "weight": 1.0,
    "resize_mode": "Scale to Fit (Inner Fit)",
    "lowvram": False,
    "processor_res": 64,
    "threshold_a": 64,
    "threshold_b": 64,
    "guidance": 1.0,
    "guidance_start": 0.0,
    "guidance_end": 1.0,
    "control_mode": 0,
}

GENERATION_MESSAGES = [
    "Making happy little pixels...",
    "Fetching pixels from a digital art museum...",
    "Waiting for bot-painters to finish...",
    "Waiting for the prompt to bake...",
    "Fetching random pixels from the internet",
    "Taking a random screenshot from an AI dream",
    "Throwing pixels at screen and seeing what sticks",
    "Converting random internet comment to RGB values",
    "Computer make pretty picture, you happy.",
    "Computer is hand-painting pixels...",
    "Turning the Gimp knob up to 11...",
    "Pixelated dreams come true, thanks to AI.",
    "AI is doing its magic...",
    "Pocket Picasso is speed-painting...",
    "Instant Rembrandt! Well, relatively instant...",
    "Doodle buddy is doing its thing...",
    "Waiting for the digital paint to dry...",
]

INPAINT_FILL_MODES = [
    "fill", "original", "latent noise", "latent nothing",
]

INSERT_MODES = [
    "Resize to selection",
    "Insert as is",
    "Aspect fill",
    "Aspect fit",
    "Use selection size",
]

from gi.repository import GObject

from sg_utils import make_choice_from_list


def PLUGIN_FIELDS_CHECKPOINT(procedure, models, selected_model):
    procedure.add_choice_argument(
        "model",
        "Model",
        "Model",
        make_choice_from_list(models),
        selected_model,
        GObject.ParamFlags.READWRITE,
    )


def PLUGIN_FIELDS_COMMON(procedure, samplers, selected_sampler):
    procedure.add_string_argument(
        "prompt",
        "Prompt",
        "A text string that describes the image you want to generate",
        "",
        GObject.ParamFlags.READWRITE,
    )
    procedure.add_string_argument(
        "negative_prompt",
        "Negative Prompt",
        "A text description on what you don't want to see in the image ",
        "",
        GObject.ParamFlags.READWRITE,
    )
    procedure.add_int_argument(
        "seed",
        "Seed",
        "Value that determines the output of a random number generator (0 or -1 for random)",
        0,
        65535,
        0,
        GObject.ParamFlags.READWRITE,
    )
    procedure.add_int_argument(
        "batch_size",
        "Batch count",
        "Specifies the number of results you want to get.",
        1,
        20,
        1,
        GObject.ParamFlags.READWRITE,
    )
    procedure.add_int_argument(
        "steps",
        "Steps",
        """The number of denoising steps used by the AI model when generating an image from the text prompt.
        A higher number results in longer generation time, and does not necessarily guarantee higher image quality.""",
        5,
        150,
        10,
        GObject.ParamFlags.READWRITE,
    )
    procedure.add_int_argument(
        "mask_blur",
        "Mask Blur",
        "Feathering of a mask (from edges to inside the mask)",
        0,
        64,
        4,
        GObject.ParamFlags.READWRITE,
    )
    procedure.add_int_argument(
        "width", "Width", "Width of the image you want to generate", 64, 2048, 512, GObject.ParamFlags.READWRITE,
    )
    procedure.add_int_argument(
        "height", "Height", "Height of the image that you want to generate",
        64, 2048, 512, GObject.ParamFlags.READWRITE,
    )
    procedure.add_double_argument(
        "cfg_scale",
        "CFG Scale",
        """Governs how closely it follows the prompt. 7 or 7.5 usually works best.
You can increase the value if the generated image doesn’t match your prompt.

Low numbers (0-6 ish): You're telling SD that it can ignore your prompt.
Mid-range (6-10 ish): You're telling SD you'd like it to do what you're asking, but you don't mind a bit of variation.
High numbers (10+): We found that high cfg often results in a really bad image.""",
        1,
        30,
        7,
        GObject.ParamFlags.READWRITE,
    )
    procedure.add_double_argument(
        "denoising_strength",
        "Denoising Strength",
        """Strength of image transfomation during inpainting precess.

High means more influence during transformation.
A value between 0.5 and 1 is optimal for maintaining image consistency.""",
        0,
        1,
        0.75,
        GObject.ParamFlags.READWRITE,
    )
    procedure.add_choice_argument(
        "sampler_index",
        "Sampler",
        "Sampler",
        make_choice_from_list(samplers),
        selected_sampler,
        GObject.ParamFlags.READWRITE,
    )
    procedure.add_boolean_argument(
        "restore_faces",
        "Restore faces",
        "Use GFPGAN / CodeFormer to restore faces",
        False,
        GObject.ParamFlags.READWRITE,
    )
    procedure.add_boolean_argument(
        "tiling",
        "Tiling",
        "Tiling",
        False,
        GObject.ParamFlags.READWRITE,
    )


def PLUGIN_FIELDS_CONTROLNET_OPTIONS(procedure):
    procedure.add_boolean_argument(
        "cn1_enabled",
        "Enable ControlNet 1",
        "Enable ControlNet 1",
        False,
        GObject.ParamFlags.READWRITE,
    )
    procedure.add_layer_argument(
        "cn1_layer",
        "ControlNet 1 Layer",
        "ControlNet 1 Layer",
        True,
        GObject.ParamFlags.READWRITE,
    )
    procedure.add_boolean_argument(
        "cn2_enabled",
        "Enable ControlNet 2",
        "Enable ControlNet 2",
        False,
        GObject.ParamFlags.READWRITE,
    )
    procedure.add_layer_argument(
        "cn2_layer",
        "ControlNet 2 Layer",
        "ControlNet 2 Layer",
        True,
        GObject.ParamFlags.READWRITE,
    )
    procedure.add_boolean_argument(
        "cn_skip_annotator_layers",
        "Skip annotator layers",
        "Skip annotator layers",
        True,
        GObject.ParamFlags.READWRITE,
    )


def PLUGIN_FIELDS_RESIZE_MODE(procedure, resize_modes):
    procedure.add_choice_argument(
        "resize_mode",
        "Resize Mode",
        "Resize Mode",
        make_choice_from_list(resize_modes),
        resize_modes[0],
        GObject.ParamFlags.READWRITE,
    )


def PLUGIN_FIELDS_INPAINTING(procedure, inpaint_fill_modes):
    procedure.add_boolean_argument(
        "invert_mask",
        "Invert Mask",
        "Determines whether you want to inpaint the masked object or outside of the masked object",
        False,
        GObject.ParamFlags.READWRITE,
    )
    procedure.add_boolean_argument(
        "inpaint_full_res",
        "Inpaint Whole Picture",
        """Refers to the inpaint area. It can be either true or false.

        If set to true, inpaint area will be the same resolution as the starting image.
        If set to false, inpaint area will stretch to fit the starting image.""",
        True,
        GObject.ParamFlags.READWRITE,
    )
    procedure.add_choice_argument(
        "inpainting_fill",
        "Mask fill mode",
        "Choose the fill content in mask",
        make_choice_from_list(inpaint_fill_modes),
        inpaint_fill_modes[0],
        GObject.ParamFlags.READWRITE,
    )


def PLUGIN_FIELDS_CONTROLNET(procedure, cn_modules, cn_models, cn_resize_modes, control_modes):
    procedure.add_choice_argument(
        "module",
        "Module",
        "Module",
        make_choice_from_list(cn_modules),
        cn_modules[0],
        GObject.ParamFlags.READWRITE,
    )
    procedure.add_choice_argument(
        "model",
        "Model",
        "Model",
        make_choice_from_list(cn_models),
        cn_models[0],
        GObject.ParamFlags.READWRITE,
    )
    procedure.add_double_argument(
        "weight",
        "Weight",
        """Determines how closely the control map should follow the prompt.
By default it is 1 and it will deviate from the control map as it gets closer to 0""",
        0,
        2,
        1,
        GObject.ParamFlags.READWRITE,
    )
    procedure.add_choice_argument(
        "resize_mode",
        "Resize Mode",
        "Resize Mode",
        make_choice_from_list(cn_resize_modes),
        cn_resize_modes[0],
        GObject.ParamFlags.READWRITE,
    )
    procedure.add_boolean_argument(
        "lowvram",
        "Low VRAM",
        "Only recommended if you have less than 8gb VRAM",
        False,
        GObject.ParamFlags.READWRITE,
    )
    procedure.add_choice_argument(
        "control_mode",
        "Control Mode",
        "Control Mode",
        make_choice_from_list(control_modes),
        control_modes[0],
        GObject.ParamFlags.READWRITE,
    )
    procedure.add_double_argument(
        "guidance_start",
        "Guidance Start (T)",
        "Guidance Start (T)",
        0,
        1,
        0,
        GObject.ParamFlags.READWRITE,
    )
    procedure.add_double_argument(
        "guidance_end",
        "Guidance End (T)",
        "Guidance End (T)",
        0,
        1,
        1,
        GObject.ParamFlags.READWRITE,
    )
    procedure.add_double_argument("guidance", "Guidance", "Guidance", 0, 1, 1, GObject.ParamFlags.READWRITE)
    procedure.add_int_argument(
        "processor_res",
        "Processor Resolution",
        "set this to 512. There’s an ongoing bug that results in the cv2 error if it’s not set",
        64,
        2048,
        512,
        GObject.ParamFlags.READWRITE,
    )
    procedure.add_int_argument("threshold_a", "Threshold A", "Threshold A", 64, 2048, 64, GObject.ParamFlags.READWRITE)
    procedure.add_int_argument("threshold_b", "Threshold B", "Threshold B", 64, 2048, 64, GObject.ParamFlags.READWRITE)

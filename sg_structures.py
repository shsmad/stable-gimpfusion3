import base64
import json
import logging
import os
import tempfile

import gi
import requests

from sg_constants import CONTROLNET_DEFAULT_SETTINGS

gi.require_version("Gimp", "3.0")
from gi.repository import Gegl, Gimp, Gio

from sg_utils import roundToMultiple


class TempFiles:
    def __new__(cls):
        if not hasattr(cls, "instance"):
            cls.instance = super().__new__(cls)
        return cls.instance

    def __init__(self):
        self.files = []

    def get(self, filename):
        self.files.append(filename)
        return os.path.join(tempfile.gettempdir(), filename)

    def removeAll(self):
        try:
            unique_list = list(set(self.files))
            for tmpfile in unique_list:
                if os.path.exists(tmpfile):
                    os.remove(tmpfile)
        except Exception as ex:
            ex = ex


class LayerData:
    def __init__(self, layer, defaults=None):
        if defaults is None:
            defaults = {}
        self.name = "gimpfusion"
        self.layer = layer
        self.image = layer.get_image()
        self.defaults = defaults
        self.had_parasite = False
        self.load()

    def load(self):
        # Gimp Item get_parasite
        parasite = self.layer.get_parasite(self.name)
        if not parasite:
            self.data = self.defaults.copy()
        else:
            self.had_parasite = True
            # TODO bytes to str
            self.data = json.loads(''.join(chr(x) for x in parasite.get_data()))
        return self.data

    def save(self, data):
        data_as_str = json.dumps(data)
        parasite = Gimp.Parasite.new(self.name, Gimp.PARASITE_PERSISTENT, data_as_str.encode())
        self.layer.attach_parasite(parasite)

# GLOBALS
layer_counter = 1

class Layer:
    def __init__(self, layer=None):
        global layer_counter
        self.id = layer_counter
        layer_counter = layer_counter + 1
        if layer is not None:
            self.layer = layer
            self.image = layer.get_image()

    @staticmethod
    def create(image, name, width, height, image_type, opacity, mode):
        layer = Gimp.Layer.new(image, name, width, height, image_type, opacity, mode)
        return Layer(layer)

    @staticmethod
    def fromBase64(img, base64Data):
        filepath = TempFiles().get("generated.png")
        with open(filepath, "wb+") as imageFile:
            imageFile.write(base64.b64decode(base64Data))
        layer = Gimp.file_load_layer(Gimp.RunMode.NONINTERACTIVE, img, Gio.File.new_for_path(filepath))
        return Layer(layer)

    def rename(self, name):
        self.layer.set_name(name)
        return self

    def saveData(self, data):
        LayerData(self.layer).save(data)
        return self

    def loadData(self, default_data):
        return LayerData(self.layer, default_data).data.copy()

    def copy(self):
        copy = self.layer.copy()
        return Layer(copy)

    def scale(self, new_scale=1.0):
        if new_scale != 1.0:
            self.layer.scale(int(new_scale * self.layer.width), int(new_scale * self.layer.height), False)
        return self

    def resize(self, width, height):
        logging.info("Resizing to %dx%d", width, height)
        self.layer.scale(width, height, False)

    def resizeToMultipleOf(self, multiple):
        self.layer.scale(
            roundToMultiple(self.layer.width, multiple), roundToMultiple(self.layer.height, multiple), False,
        )
        return self

    def translate(self, offset=None):
        if offset is not None:
            self.layer.set_offsets(offset[0], offset[1])
        return self

    def insert(self):
        self.image.insert_layer(self.layer, None, -1)
        return self

    def insertTo(self, image=None):
        image = image or self.image
        image.insert_layer(self.layer, None, -1)
        return self

    def addSelectionAsMask(self):
        mask = self.layer.create_mask(Gimp.AddMaskType.SELECTION)
        self.layer.add_mask(mask)
        return self

    def saveMaskAs(self, filepath):
        logging.debug(f"saveMaskAs {filepath=}")
        new_image = Gimp.Image.new(self.layer.get_width(), self.layer.get_height(), Gimp.ImageBaseType.RGB)
        layer = Gimp.Layer.new_from_drawable(self.layer.get_mask(), new_image)
        new_image.insert_layer(layer, None, -1)
        Gimp.file_save(Gimp.RunMode.NONINTERACTIVE, new_image, Gio.File.new_for_path(filepath), None)
        return self

    def saveAs(self, filepath):
        logging.debug(f"saveAs {filepath=}")
        new_image = Gimp.Image.new(self.layer.get_width(), self.layer.get_height(), Gimp.ImageBaseType.RGB)
        layer = Gimp.Layer.new_from_drawable(self.layer, new_image)
        new_image.insert_layer(layer, None, -1)
        Gimp.file_save(Gimp.RunMode.NONINTERACTIVE, new_image, Gio.File.new_for_path(filepath), None)
        return self

    def maskToBase64(self):
        filepath = TempFiles().get(f"mask{self.id}.png")
        self.saveMaskAs(filepath)
        with open(filepath, "rb") as file:
            return base64.b64encode(file.read()).decode()

    def toBase64(self):
        filepath = TempFiles().get(f"layer{self.id}.png")
        self.saveAs(filepath)
        with open(filepath, "rb") as file:
            return base64.b64encode(file.read()).decode()

    def remove(self):
        self.layer.get_image().remove_layer(self.layer)
        return self

class ResponseLayers:
    def __init__(self, img, response, options=None):
        if options is None:
            options = {}
        self.image = img
        color = Gimp.context_get_foreground()
        Gimp.context_set_foreground(Gegl.Color.new("#000000"))

        layers = []
        try:
            info = json.loads(response["info"])
            infotexts = info["infotexts"]
            seeds = info["all_seeds"]
            logging.debug(f"{infotexts=}")
            logging.debug(f"{seeds=}")
            total_images = len(seeds)
            for index, image in enumerate(response["images"]):
                if index < total_images:
                    layer_data = {"info": infotexts[index], "seed": seeds[index]}
                    layer = (
                        Layer.fromBase64(img, image)
                        .rename(f"Generated Layer {seeds[index]}")
                        .saveData(layer_data)
                        .insertTo(img).saveAs(TempFiles().get(f"result{index}.png"))
                    )
                elif "skip_annotator_layers" in options and not options["skip_annotator_layers"]:
                    # annotator layers
                    layer = (
                        Layer
                        .fromBase64(img, image)
                        .rename("Annotator Layer")
                        .insertTo(img).saveAs(TempFiles().get("AnnotatorLayer.png"))
                    )
                layers.append(layer.layer)
        except Exception as e:
            logging.exception(f"ResponseLayers: {e}")

        Gimp.context_set_foreground(color)
        self.layers = layers

    def scale(self, new_scale=1.0):
        if new_scale != 1.0:
            for layer in self.layers:
                Layer(layer).scale(new_scale)
        return self

    def resize(self, width, height):
        for layer in self.layers:
            Layer(layer).resize(width, height)
        return self

    def translate(self, offset=None):
        if offset is not None:
            for layer in self.layers:
                Layer(layer).translate(offset)
        return self

    def insertTo(self, image=None):
        image = image or self.image
        for layer in self.layers:
            Layer(layer).insertTo(image)
        return self

    def addSelectionAsMask(self):
        success, non_empty, x1, y1, x2, y2 = Gimp.Selection.bounds(self.image)
        if not non_empty:
            return
        if (x1 == 0) and (y1 == 0) and (x2 - x1 == self.image.get_width()) and (y2 - y1 == self.image.get_height()):
            return
        for layer in self.layers:
            Layer(layer).addSelectionAsMask()
        return self

class MyShelf:
    """GimpShelf is not available at init time, so we keep our persistent data in a json file"""

    def __init__(self, default_shelf=None):
        if default_shelf is None:
            default_shelf = {}
        self.file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "stable_gimpfusion.json")
        self.load(default_shelf)

    def load(self, default_shelf=None):
        if default_shelf is None:
            default_shelf = {}
        self.data = default_shelf
        try:
            if os.path.isfile(self.file_path):
                logging.info(f"Loading shelf from {self.file_path}")
                with open(self.file_path) as f:
                    self.data = json.load(f)
                logging.info("Successfully loaded shelf")
        except Exception as e:
            logging.debug(e)

    def save(self, data=None):
        if data is None:
            data = {}
        try:
            self.data.update(data)
            logging.info(f"Saving shelf to {self.file_path}")
            with open(self.file_path, "w") as f:
                json.dump(self.data, f)
            logging.info("Successfully saved shelf")

        except Exception as e:
            logging.debug(e)

    def get(self, name, default_value=None):
        #return self.data[name] if name in self.data else default_value
        return self.data.get(name, default_value)

    def set(self, name, default_value=None):
        self.data[name] = default_value
        self.save()

class ApiClient:
    """Simple API client used to interface with StableDiffusion JSON endpoints"""

    def __init__(self, base_url):
        self.setBaseUrl(base_url)

    def setBaseUrl(self, base_url):
        self.base_url = base_url.strip("/")

    def post(self, endpoint, data=None, params=None, headers=None):
        try:
            url = self.base_url + endpoint
            headers = headers or {"Content-Type": "application/json", "Accept": "application/json"}

            # logging.debug(f"POST {url}, data {data}")

            response = requests.post(url=url, params=params, headers=headers, json=data)

            data = response.json()

            # logging.debug(f"response: {data}")
            return data
        except Exception as ex:
            logging.exception(f"ERROR: ApiClient.post: {ex}")

    def get(self, endpoint, params=None, headers=None):
        try:
            url = self.base_url + endpoint
            logging.debug(f"GET {url}")
            headers = headers or {"Content-Type": "application/json", "Accept": "application/json"}

            response = requests.get(url=url, params=params, headers=headers)
            return response.json()
        except Exception as ex:
            logging.exception(f"ERROR: ApiClient.get: {ex}")

def getLayerAsBase64(layer):
    # store active_layer
    active_layers = layer.get_image().get_selected_layers()
    copy = Layer(layer).copy().insert()
    result = copy.toBase64()
    copy.remove()
    # restore active_layer
    layer.get_image().set_selected_layers(active_layers)
    return result


def getActiveLayerAsBase64(image):
    return getLayerAsBase64(image.get_selected_layers()[0])

def getLayerMaskAsBase64(layer):
    success, non_empty, x1, y1, x2, y2 = Gimp.Selection.bounds(layer.get_image())

    if non_empty:
        # selection to base64

        # store active_layer
        active_layers = layer.get_image().get_selected_layers()

        # selection to file
        # disable=pdb.gimp_image_undo_disable(layer.image)
        tmp_layer = Layer.create(
            layer.get_image(),
            "mask",
            layer.get_image().get_width(),
            layer.get_image().get_height(),
            Gimp.ImageType.RGBA_IMAGE,
            100,
            Gimp.LayerMode.NORMAL,
        )
        tmp_layer.addSelectionAsMask().insert()

        result = tmp_layer.maskToBase64()
        tmp_layer.remove()
        # enable = pdb.gimp_image_undo_enable(layer.image)

        # restore active_layer
        layer.get_image().set_selected_layers(active_layers)

        return result
    elif layer.get_mask():
        # mask to file
        tmp_layer = Layer(layer)
        return tmp_layer.maskToBase64()
    else:
        return ""


def getActiveMaskAsBase64(image):
    return getLayerMaskAsBase64(image.get_selected_layers()[0])

def getControlNetParams(cn_layer):
    if not cn_layer:
        return None

    layer = Layer(cn_layer)
    data = layer.loadData(CONTROLNET_DEFAULT_SETTINGS)
    # ControlNet image size need to be in multiples of 64
    layer64 = layer.copy().insert().resizeToMultipleOf(64)
    data.update({"input_image": layer64.toBase64()})
    if cn_layer.mask:
        data.update({"mask": layer64.maskToBase64()})
    layer64.remove()
    return data

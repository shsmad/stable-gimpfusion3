# Stable-Gimpfusion-3

This is a plugin for using GIMP 3 with Stable Diffusion.

[Original plugin by ArtBIT](https://github.com/ArtBIT/stable-gimpfusion) was written on python2 for GIMP 2.10.

Rewriten version runs on python3 for GIMP 3. Some refactoring and UI/UX optimisation was made.

Tested on Ubuntu 24.04 with PPA GIMP 3.0.6 (no sandboxed environments like AppImage, snap of flatpak) with API:

- [Stable Diffusion WebUI Forge](https://github.com/lllyasviel/stable-diffusion-webui-forge)
- [Stable Diffusion WebUI Forge - Classic](https://github.com/Haoming02/sd-webui-forge-classic)

## Installation

- Download all `*.py` scripts including the directory `sg_plugins`,
- In GIMP plug-ins directory create an appropriate empty subdirectory called, for example, `stable-gimpfusion3`,
  save files into your just created gimp plug-ins directory, ie (replace `3.0` with your real version):
  - Linux: `$HOME/.gimp-3.0/plug-ins/stable-gimpfusion3` or `$XDG_CONFIG_HOME/GIMP/3.0/plug-ins/stable-gimpfusion3`
  - Windows: `%APPDATA%\GIMP\3.0\plug-ins\stable-gimpfusion3` or `C:\Users\{your_id}\AppData\Roaming\GIMP\3.0\plug-ins\stable-gimpfusion3`
  - OSX: `$HOME/Library/GIMP/3.0/plug-ins/stable-gimpfusion3` or `$HOME/Library/Application Support/GIMP/3.0/plug-ins/stable-gimpfusion3`
- Ensure the execute bit is set on MacOS and Linux by running `chmod +x YOUR_PATH_TO/plugins/stable-gimpfusion3/stable-gimpfusion3.py`
- Restart Gimp, and you will see a new menu item called `GimpFusion`
- Run script via `GimpFusion -> Config` and set the backend API URL base (should be `http://127.0.0.1:7860/` by default)

## Translation

By default, GIMP plug-ins look up gettext compiled message catalogs in the subdirectory locale/
under the plug-in folder (same folder as gimp_get_progname()) with a text domain equal to the plug-in name
(regardless procedure_name).

To add new translation:

```bash
cd path/to/project/stable-gimpfusion3/
mkdir -p locale/{YOUR_LANG}/LC_MESSAGES
msginit -l ru -i locale/stable-gimpfusion3.pot -o locale/{YOUR_LANG}/LC_MESSAGES/stable-gimpfusion3.po
```

Edit `locale/{YOUR_LANG}/LC_MESSAGES/stable-gimpfusion3.po`, add translations.

To update from new pot-file:

```bash
msgmerge -U locale/{YOUR_LANG}/LC_MESSAGES/stable-gimpfusion3.po locale/stable-gimpfusion3.pot
```

Then compile translation:

```bash
msgfmt locale/ru/LC_MESSAGES/stable-gimpfusion3.po -o locale/{YOUR_LANG}/LC_MESSAGES/stable-gimpfusion3.mo
```

### Translate

- Names of menus and menu items
- Descriptions of parameters
- Error messages for the user
- Progress messages

### DO NOT translate

- Technical names (sampler names, module names, Resize modes, Control modes, Insert modes)
- Names of API parameters
- File names and paths
- Logs and debugging messages

### Usage examples

Use `_()` in code for all strings, that should be translated:

```python
from sg_i18n import _

menu_label = _("Text to image")
description = _("Generate image from text prompt")
error_message = _("Error occurred: {error}").format(error=str(ex))
```

## GIMP Plugins dev docs

- <https://developer.gimp.org/api/3.0/libgimp/index.html>
- <https://developer.gimp.org/api/3.0/libgimpui/index.html>
- <https://gegl.org/operations/>
- <https://github.com/mix1009/sdwebuiapi> for scripts params details
- <https://www.gitbook.com/book/athenajc/python-gtk-3-api> gtk via python
- <https://gist.github.com/DarkStoorM/4b1684e5d42532e8d55517e61001d97a>
- <https://www.digitalcreativeai.net/en/post/how-to-use-stable-diffusion-web-ui-image-to-image>

## TODO

- <https://github.com/shsmad/gimp-stable-boy> X/Y plotting, Upscale
- ugly, worst quality, low quality, plastic, fake, anime, cartoon, artifacts, painting, 3d for negprompt
- img2img soft inpaint

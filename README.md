# Stable-Gimpfusion-3

This is a plugin for using GIMP 3 with Stable Diffusion.

[Original plugin by ArtBIT](https://github.com/ArtBIT/stable-gimpfusion) was written on python2 for GIMP 2.10.

Rewriten version runs on python3 for GIMP 3. Some refactoring and UI/UX optimisation was made.

Tested on Ubuntu 24.04 with PPA GIMP (no sandboxed environments like AppImage, snap of flatpak) and
[Stable Diffusion Forge](https://github.com/lllyasviel/stable-diffusion-webui-forge).

# Installation

- Download all `*.py` scripts including the directory `sg_plugins`,
- In GIMP plug-ins directory create an appropriate empty subdirectory called, for example, `StableGimpfusion3`,
  save files into your just created gimp plug-ins directory, ie:
  - Linux: `$HOME/.gimp-2.10/plug-ins/StableGimpfusion3` or `$XDG_CONFIG_HOME/GIMP/2.10/plug-ins/StableGimpfusion3`
  - Windows: `%APPDATA%\GIMP\2.10\plug-ins\StableGimpfusion3` or `C:\Users\{your_id}\AppData\Roaming\GIMP\2.10\plug-ins\StableGimpfusion3`
  - OSX: `$HOME/Library/GIMP/2.10/plug-ins/StableGimpfusion3` or `$HOME/Library/Application Support/GIMP/2.10/plug-ins/StableGimpfusion3`
- Ensure the execute bit is set on MacOS and Linux by running `chmod -R +x /StableGimpfusion3`
- Restart Gimp, and you will see a new menu item called `GimpFusion`
- Run script via `GimpFusion -> Config` and set the backend API URL base (should be `http://127.0.0.1:7860/` by default)

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

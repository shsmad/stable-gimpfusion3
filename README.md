# Stable-Gimpfusion-3

This is a plugin for using GIMP 3 with Stable Diffusion.

[Original plugin by ArtBIT](https://github.com/ArtBIT/stable-gimpfusion) was written on python2 for GIMP 2.10.

Rewriten version runs on python3 for GIMP 3. Some refactoring and UI/UX optimisation was made.

Tested on Ubuntu 24.04 with PPA GIMP (no sandboxed environments like AppImage, snap of flatpak) and
[Stable Diffusion Forge](https://github.com/lllyasviel/stable-diffusion-webui-forge).

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

# Stable-Gimpfusion-3

This is a plugin for using GIMP 3 with Stable Diffusion.

[Original plugin by ArtBIT](https://github.com/ArtBIT/stable-gimpfusion) was written on python2 for GIMP 2.10.

Rewriten version runs on python3 for GIMP 3. Some refactoring and UI/UX optimisation was made.

Tested on Ubuntu 24.04 with PPA GIMP (no sandboxed environments like AppImage, snap of flatpak) and
[Stable Diffusion Forge](https://github.com/lllyasviel/stable-diffusion-webui-forge).

## GIMP Plugins dev docs

- https://developer.gimp.org/api/3.0/libgimp/index.html
- https://developer.gimp.org/api/3.0/libgimpui/index.html
- https://gegl.org/operations/
- https://github.com/mix1009/sdwebuiapi for scripts params details

## TODO

- https://github.com/shsmad/gimp-stable-boy X/Y plotting, Upscale
- beauty, good skin, sharp skin, ultra detailed skin, high quality, RAW photo, analog film, 35mm photograph, 32K UHD, close-up, ultra realistic, clean for prompt, ugly, worst quality, low quality, plastic, fake, anime, cartoon, artifacts, painting, 3d for negprompt
- при выборе flux1-dev-bnb-nf4-v2.safetensors добавить выбор ae.safetensors clip_l.safetensors t5xxl_fp16.safetensors

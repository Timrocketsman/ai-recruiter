#!/bin/bash
# Установка нейро-конвейера обложек ВНУТРИ my-ubuntu (правило Тима: ничего на хосте).
# Запуск: bash install_models.sh [--yes]   (без --yes — показ, что будет скачано)
set -e
COMFY=/opt/timlabs/render/ComfyUI; M=$COMFY/models; HF=https://huggingface.co
[ -f /opt/timlabs/render/.env ] && set -a && . /opt/timlabs/render/.env && set +a   # HF_TOKEN, не печатать
auth=(); [ -n "$HF_TOKEN" ] && auth=(-H "Authorization: Bearer $HF_TOKEN")
true
dl(){ local url=$1 dst=$2; if [ -f "$dst" ]; then echo "есть  $dst"; return; fi; echo "качаю $dst"; if [ "$YES" = 1 ]; then curl -sS -L --retry 8 --retry-all-errors -C - "${auth[@]}" -o "$dst.part" "$url" && mv "$dst.part" "$dst"; fi; }
[ "$1" = "--yes" ] && YES=1 || YES=0
mkdir -p $M/{unet,diffusion_models,text_encoders,vae,model_patches,loras} /opt/timlabs/render/blender /opt/timlabs/render/hdri
# 1. ComfyUI-GGUF (загрузчик квантованных моделей)
[ -d $COMFY/custom_nodes/ComfyUI-GGUF ] || { echo "ставлю ComfyUI-GGUF"; if [ $YES = 1 ]; then git clone https://github.com/city96/ComfyUI-GGUF $COMFY/custom_nodes/ComfyUI-GGUF && $COMFY/venv/bin/python -m pip install -r $COMFY/custom_nodes/ComfyUI-GGUF/requirements.txt; fi; }
# 2. Qwen-Image-2512 (Apache-2.0, коммерчески можно) — генерация: 15 ГБ Q5_K_M
dl $HF/unsloth/Qwen-Image-2512-GGUF/resolve/main/qwen-image-2512-Q5_K_M.gguf $M/unet/qwen-image-2512-Q5_K_M.gguf
dl $HF/Comfy-Org/Qwen-Image_ComfyUI/resolve/main/split_files/text_encoders/qwen_2.5_vl_7b_fp8_scaled.safetensors $M/text_encoders/qwen_2.5_vl_7b_fp8_scaled.safetensors
dl $HF/Comfy-Org/Qwen-Image_ComfyUI/resolve/main/split_files/vae/qwen_image_vae.safetensors $M/vae/qwen_image_vae.safetensors
# 3. Qwen-Image-Edit-2511 (Apache-2.0) — доводка 3D-рендера Blender до гиперреализма: 13 ГБ Q4_K_M
dl $HF/unsloth/Qwen-Image-Edit-2511-GGUF/resolve/main/qwen-image-edit-2511-Q4_K_M.gguf $M/unet/qwen-image-edit-2511-Q4_K_M.gguf
# 4. ControlNet глубины (DiffSynth) — чтобы нейросеть держала композицию Blender
dl $HF/Comfy-Org/Qwen-Image-DiffSynth-ControlNets/resolve/main/split_files/model_patches/qwen_image_depth_diffsynth_controlnet.safetensors $M/model_patches/qwen_image_depth_diffsynth_controlnet.safetensors
# 5. Blender 4.2 LTS (другая сессия его на сервере не нашла — его там и не было; ставим внутрь контейнера)
if [ ! -x /opt/timlabs/render/blender/blender ]; then echo "качаю Blender 4.2.3 (352 МБ)"; if [ $YES = 1 ]; then curl -sS -L --retry 5 -o /tmp/blender.tar.xz https://download.blender.org/release/Blender4.2/blender-4.2.3-linux-x64.tar.xz && tar -xJf /tmp/blender.tar.xz -C /opt/timlabs/render/blender --strip-components=1 && rm /tmp/blender.tar.xz; fi; fi
dl https://dl.polyhaven.org/file/ph-assets/HDRIs/hdr/2k/studio_small_09_2k.hdr /opt/timlabs/render/hdri/studio_small_09_2k.hdr
echo "Итого на диск ≈ 31 ГБ. Проверка: /opt/timlabs/render/blender/blender -b --version; curl -s 127.0.0.1:8188/object_info/UnetLoaderGGUF | head -c 200"

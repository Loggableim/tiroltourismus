#!/usr/bin/env python3
from __future__ import annotations

import gc
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(r"F:/tiroltourismus/wappen")
VENDOR = ROOT / ".vendor"
if VENDOR.exists():
    sys.path.insert(0, str(VENDOR))

import torch
from diffusers import StableDiffusion3Pipeline
from huggingface_hub import hf_hub_download, snapshot_download
from transformers import CLIPTextModelWithProjection, T5EncoderModel

REPO = "stabilityai/stable-diffusion-3.5-medium"
TOKEN = (Path.home() / ".cache" / "huggingface" / "token").read_text().strip()
MODEL_DIR = ROOT / "models" / "sd35"
MODEL_FILE = MODEL_DIR / "sd3.5_medium.safetensors"
CONFIG_DIR = ROOT / "diffusers-sd35-config"
COMP_DIR = ROOT / "models" / "sd35_components"
OUT_DIR = ROOT / "img" / "test-sd35"

PROMPT = (
    "cute anthropomorphic furry mascot logo, clean heraldic emblem, bold geometric shapes, "
    "red and gold, white background, centered composition, crisp vector look, no text, no watermark"
)
NEG = "photo, realistic, 3d render, blurry, noisy, low quality, text, letters, watermark, extra limbs"

CONFIG_PATTERNS = [
    "model_index.json",
    "scheduler/scheduler_config.json",
    "transformer/config.json",
    "vae/config.json",
    "text_encoder/config.json",
    "text_encoder_2/config.json",
    "text_encoder_3/config.json",
    "tokenizer/vocab.json",
    "tokenizer/merges.txt",
    "tokenizer/tokenizer_config.json",
    "tokenizer/special_tokens_map.json",
    "tokenizer_2/vocab.json",
    "tokenizer_2/merges.txt",
    "tokenizer_2/tokenizer_config.json",
    "tokenizer_2/special_tokens_map.json",
    "tokenizer_3/tokenizer.json",
    "tokenizer_3/tokenizer_config.json",
    "tokenizer_3/special_tokens_map.json",
    "tokenizer_3/spiece.model",
]


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def ensure_config() -> Path:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    snapshot_download(
        repo_id=REPO,
        token=TOKEN,
        local_dir=str(CONFIG_DIR),
        local_dir_use_symlinks=False,
        allow_patterns=CONFIG_PATTERNS,
    )
    return CONFIG_DIR


def _prepare_comp_dir(name: str) -> Path:
    d = COMP_DIR / name
    d.mkdir(parents=True, exist_ok=True)
    return d


def _copy_config(src_name: str, dst_dir: Path) -> None:
    shutil.copy2(CONFIG_DIR / src_name / "config.json", dst_dir / "config.json")


def _download_and_load_clip(subfolder: str, filename: str) -> CLIPTextModelWithProjection:
    d = _prepare_comp_dir(subfolder)
    _copy_config(subfolder, d)
    fp = hf_hub_download(
        repo_id=REPO,
        filename=filename,
        token=TOKEN,
        local_dir=str(d),
        local_dir_use_symlinks=False,
    )
    fp = Path(fp)
    target = d / "model.safetensors"
    if fp != target:
        if target.exists():
            target.unlink()
        fp.replace(target)
    model = CLIPTextModelWithProjection.from_pretrained(
        d,
        torch_dtype=torch.float16,
        use_safetensors=True,
    )
    shutil.rmtree(d, ignore_errors=True)
    gc.collect()
    return model


def _download_and_load_t5() -> T5EncoderModel:
    d = _prepare_comp_dir("text_encoder_3")
    _copy_config("text_encoder_3", d)
    fp = hf_hub_download(
        repo_id=REPO,
        filename="text_encoders/t5xxl_fp8_e4m3fn.safetensors",
        token=TOKEN,
        local_dir=str(d),
        local_dir_use_symlinks=False,
    )
    fp = Path(fp)
    target = d / "model.safetensors"
    if fp != target:
        if target.exists():
            target.unlink()
        fp.replace(target)
    model = T5EncoderModel.from_pretrained(
        d,
        torch_dtype=torch.float16,
        use_safetensors=True,
    )
    shutil.rmtree(d, ignore_errors=True)
    gc.collect()
    return model


def ensure_model_file() -> Path:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    if MODEL_FILE.exists() and MODEL_FILE.stat().st_size > 1_000_000_000:
        return MODEL_FILE
    fp = hf_hub_download(
        repo_id=REPO,
        filename="sd3.5_medium.safetensors",
        token=TOKEN,
        local_dir=str(MODEL_DIR),
        local_dir_use_symlinks=False,
    )
    return Path(fp)


def build_pipe() -> StableDiffusion3Pipeline:
    log("preparing config")
    ensure_config()

    # Free any stale checkpoint file before staging the auxiliary components.
    if MODEL_FILE.exists():
        try:
            MODEL_FILE.unlink()
        except Exception:
            pass
    shutil.rmtree(MODEL_DIR / ".cache", ignore_errors=True)

    log("loading CLIP text encoder 1")
    clip1 = _download_and_load_clip("text_encoder", "text_encoder/model.safetensors")
    log("loading CLIP text encoder 2")
    clip2 = _download_and_load_clip("text_encoder_2", "text_encoder_2/model.safetensors")
    log("loading T5 text encoder 3")
    t5 = _download_and_load_t5()

    log("downloading single-file checkpoint")
    model = ensure_model_file()

    log("loading pipeline from single-file checkpoint")
    pipe = StableDiffusion3Pipeline.from_single_file(
        str(model),
        config=str(CONFIG_DIR),
        local_files_only=True,
        torch_dtype=torch.float16,
        text_encoder=clip1,
        text_encoder_2=clip2,
        text_encoder_3=t5,
    )
    try:
        pipe.enable_vae_tiling()
    except Exception:
        pass
    try:
        pipe.enable_model_cpu_offload()
    except Exception:
        pipe.to("cuda")
    return pipe


def gen_one(pipe: StableDiffusion3Pipeline, seed: int, idx: int) -> Path:
    g = torch.Generator(device="cuda").manual_seed(seed)
    image = pipe(
        prompt=PROMPT,
        negative_prompt=NEG,
        height=768,
        width=768,
        guidance_scale=4.0,
        num_inference_steps=18,
        max_sequence_length=256,
        generator=g,
    ).images[0]
    out = OUT_DIR / f"sd35_test_{idx:02d}.png"
    image.save(out)
    log(f"saved {out}")
    return out


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    pipe = build_pipe()
    for idx, seed in enumerate([111, 112], start=1):
        gen_one(pipe, seed, idx)
    log("done")


if __name__ == "__main__":
    main()

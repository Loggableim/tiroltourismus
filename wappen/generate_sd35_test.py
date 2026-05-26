#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

ROOT = Path(r"F:/tiroltourismus/wappen")
VENDOR = ROOT / ".vendor"
if VENDOR.exists():
    sys.path.insert(0, str(VENDOR))

import torch
from huggingface_hub import hf_hub_download, snapshot_download
from diffusers import StableDiffusion3Pipeline
from transformers import CLIPTextModelWithProjection

REPO = "stabilityai/stable-diffusion-3.5-medium"
TOKEN = (Path.home() / ".cache" / "huggingface" / "token").read_text().strip()
MODEL_DIR = ROOT / "models" / "sd35"
CONFIG_DIR = ROOT / "diffusers-sd35-config"
OUT_DIR = ROOT / "img" / "test-sd35"
MODEL_FILE = MODEL_DIR / "sd3.5_medium.safetensors"

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
    log(f"snapshot_download config files -> {CONFIG_DIR}")
    snapshot_download(
        repo_id=REPO,
        token=TOKEN,
        local_dir=str(CONFIG_DIR),
        local_dir_use_symlinks=False,
        allow_patterns=CONFIG_PATTERNS,
    )
    return CONFIG_DIR


def ensure_model() -> Path:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    if MODEL_FILE.exists() and MODEL_FILE.stat().st_size > 1_000_000_000:
        log(f"model already present: {MODEL_FILE} ({MODEL_FILE.stat().st_size} bytes)")
        return MODEL_FILE
    log(f"downloading single-file checkpoint -> {MODEL_FILE}")
    hf_hub_download(
        repo_id=REPO,
        filename="sd3.5_medium.safetensors",
        token=TOKEN,
        local_dir=str(MODEL_DIR),
        local_dir_use_symlinks=False,
    )
    return MODEL_FILE


def build_pipe() -> StableDiffusion3Pipeline:
    config = ensure_config()
    model = ensure_model()
    log("loading CLIP text encoder 1")
    clip1 = CLIPTextModelWithProjection.from_pretrained(
        REPO,
        subfolder="text_encoder",
        token=TOKEN,
        torch_dtype=torch.float16,
    )
    log("loading CLIP text encoder 2")
    clip2 = CLIPTextModelWithProjection.from_pretrained(
        REPO,
        subfolder="text_encoder_2",
        token=TOKEN,
        torch_dtype=torch.float16,
    )
    log("loading pipeline from single-file checkpoint")
    pipe = StableDiffusion3Pipeline.from_single_file(
        str(model),
        config=str(config),
        local_files_only=True,
        torch_dtype=torch.float16,
        text_encoder=clip1,
        text_encoder_2=clip2,
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

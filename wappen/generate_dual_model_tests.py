#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import torch
from PIL import Image

ROOT = Path(r"F:/tiroltourismus/wappen")
VENDOR = ROOT / ".vendor"
if VENDOR.exists():
    sys.path.insert(0, str(VENDOR))

from diffusers import (  # noqa: E402
    AutoencoderKL,
    FlowMatchEulerDiscreteScheduler,
    FluxPipeline,
    FluxTransformer2DModel,
    StableDiffusion3Pipeline,
)
from transformers import CLIPTextConfig, CLIPTokenizer, T5Config, T5Tokenizer  # noqa: E402
from accelerate import init_empty_weights  # noqa: E402

PROMPT = (
    "cute anthropomorphic furry mascot logo, clean heraldic emblem, bold geometric shapes, "
    "red and gold, white background, centered composition, crisp vector look, no text, no watermark"
)
NEG = "photo, realistic, 3d render, blurry, noisy, low quality, text, letters, watermark, extra limbs"

FLUX_MODEL = ROOT / "models" / "flux" / "flux1-dev-nvfp4.safetensors"
FLUX_FALLBACK = ROOT / "models" / "flux_merged" / "flux1-dev-fp8.safetensors"
SD35_MODEL_ID = "stabilityai/stable-diffusion-3.5-medium"
HF_CACHE = ROOT / ".hf-cache"
FLUX_CONFIG = ROOT / "diffusers-flux-config"
OUT_FLUX = ROOT / "img" / "test-flux"
OUT_SD35 = ROOT / "img" / "test-sd35"


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def ensure_flux_config() -> Path:
    FLUX_CONFIG.mkdir(parents=True, exist_ok=True)
    model_index = {
        "_class_name": "FluxPipeline",
        "_diffusers_version": "0.38.0",
        "scheduler": ["diffusers", "FlowMatchEulerDiscreteScheduler"],
        "vae": ["diffusers", "AutoencoderKL"],
        "text_encoder": ["transformers", "CLIPTextModel"],
        "tokenizer": ["transformers", "CLIPTokenizer"],
        "text_encoder_2": ["transformers", "T5EncoderModel"],
        "tokenizer_2": ["transformers", "T5Tokenizer"],
        "transformer": ["diffusers", "FluxTransformer2DModel"],
    }
    (FLUX_CONFIG / "model_index.json").write_text(json.dumps(model_index, indent=2), encoding="utf-8")

    # scheduler
    sch = FLUX_CONFIG / "scheduler"
    sch.mkdir(exist_ok=True)
    FlowMatchEulerDiscreteScheduler().save_pretrained(sch)

    # transformer config
    tr = FLUX_CONFIG / "transformer"
    tr.mkdir(exist_ok=True)
    with init_empty_weights():
        model = FluxTransformer2DModel(
            patch_size=1,
            in_channels=64,
            out_channels=64,
            num_layers=19,
            num_single_layers=38,
            attention_head_dim=128,
            num_attention_heads=24,
            joint_attention_dim=4096,
            pooled_projection_dim=768,
            guidance_embeds=True,
            axes_dims_rope=(16, 56, 56),
        )
    model.save_config(tr)

    # VAE config
    vae = FLUX_CONFIG / "vae"
    vae.mkdir(exist_ok=True)
    with init_empty_weights():
        model = AutoencoderKL(
            in_channels=3,
            out_channels=3,
            down_block_types=("DownEncoderBlock2D", "DownEncoderBlock2D", "DownEncoderBlock2D", "DownEncoderBlock2D"),
            up_block_types=("UpDecoderBlock2D", "UpDecoderBlock2D", "UpDecoderBlock2D", "UpDecoderBlock2D"),
            block_out_channels=(128, 256, 512, 512),
            layers_per_block=2,
            act_fn="silu",
            latent_channels=16,
            norm_num_groups=32,
            sample_size=256,
            scaling_factor=0.3611,
            shift_factor=0.1159,
            force_upcast=True,
            use_quant_conv=True,
            use_post_quant_conv=True,
            mid_block_add_attention=True,
        )
    model.save_config(vae)

    # text encoder configs + tokenizers
    te = FLUX_CONFIG / "text_encoder"
    te.mkdir(exist_ok=True)
    CLIPTextConfig(
        vocab_size=49408,
        hidden_size=768,
        intermediate_size=3072,
        projection_dim=768,
        num_hidden_layers=12,
        num_attention_heads=12,
        max_position_embeddings=77,
        hidden_act="quick_gelu",
        layer_norm_eps=1e-5,
        attention_dropout=0.0,
        initializer_range=0.02,
        bos_token_id=49406,
        eos_token_id=49407,
        pad_token_id=1,
    ).save_pretrained(te)
    CLIPTokenizer.from_pretrained("openai/clip-vit-large-patch14").save_pretrained(te)

    te2 = FLUX_CONFIG / "text_encoder_2"
    te2.mkdir(exist_ok=True)
    t5_cfg = T5Config(
        vocab_size=32128,
        d_model=4096,
        d_kv=64,
        d_ff=10240,
        num_layers=24,
        num_heads=64,
        relative_attention_num_buckets=32,
        feed_forward_proj="gated-gelu",
        decoder_start_token_id=0,
        eos_token_id=1,
        pad_token_id=0,
    )
    t5_cfg.is_encoder_decoder = False
    t5_cfg.use_cache = False
    t5_cfg.save_pretrained(te2)
    T5Tokenizer.from_pretrained("google/t5-v1_1-xxl").save_pretrained(te2)

    return FLUX_CONFIG


def ensure_dirs() -> None:
    for p in [OUT_FLUX, OUT_SD35, HF_CACHE, ROOT / "models" / "flux", ROOT / "models" / "sd35"]:
        p.mkdir(parents=True, exist_ok=True)


def pick_flux_model() -> Path:
    if FLUX_MODEL.exists():
        return FLUX_MODEL
    if FLUX_FALLBACK.exists():
        return FLUX_FALLBACK
    raise FileNotFoundError(
        f"Missing FLUX model. Expected {FLUX_MODEL} or {FLUX_FALLBACK}."
    )


def gen_flux() -> None:
    model_path = pick_flux_model()
    config_dir = ensure_flux_config()
    log(f"FLUX model: {model_path}")
    pipe = FluxPipeline.from_single_file(
        str(model_path),
        config=str(config_dir),
        local_files_only=True,
        torch_dtype=torch.float16,
    )
    pipe.to("cuda")

    for i, seed in enumerate([101, 102], start=1):
        g = torch.Generator(device="cuda").manual_seed(seed)
        img = pipe(
            prompt=PROMPT,
            prompt_2=PROMPT,
            negative_prompt=NEG,
            negative_prompt_2=NEG,
            true_cfg_scale=1.0,
            guidance_scale=3.5,
            height=768,
            width=768,
            num_inference_steps=8,
            max_sequence_length=256,
            generator=g,
        ).images[0]
        out = OUT_FLUX / f"flux_test_{i:02d}.png"
        img.save(out)
        log(f"saved {out}")


def gen_sd35() -> None:
    log("loading SD3.5 medium from Hugging Face")
    pipe = StableDiffusion3Pipeline.from_pretrained(
        SD35_MODEL_ID,
        torch_dtype=torch.float16,
        use_safetensors=True,
        cache_dir=str(HF_CACHE),
    )
    pipe.to("cuda")

    for i, seed in enumerate([201, 202], start=1):
        g = torch.Generator(device="cuda").manual_seed(seed)
        img = pipe(
            prompt=PROMPT,
            negative_prompt=NEG,
            height=768,
            width=768,
            guidance_scale=4.0,
            num_inference_steps=20,
            max_sequence_length=256,
            generator=g,
        ).images[0]
        out = OUT_SD35 / f"sd35_test_{i:02d}.png"
        img.save(out)
        log(f"saved {out}")


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-flux", action="store_true", help="Skip FLUX generation")
    ap.add_argument("--skip-sd35", action="store_true", help="Skip SD 3.5 Medium generation")
    args = ap.parse_args()

    ensure_dirs()
    ROOT.joinpath("models", "flux").mkdir(parents=True, exist_ok=True)
    ROOT.joinpath("models", "sd35").mkdir(parents=True, exist_ok=True)

    if not args.skip_flux:
        log("=== FLUX ===")
        gen_flux()
    if not args.skip_sd35:
        log("=== SD 3.5 Medium ===")
        gen_sd35()
    log("done")


if __name__ == "__main__":
    main()

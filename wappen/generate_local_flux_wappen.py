#!/usr/bin/env python3
"""Local FLUX inference for Tyrolean wappen generation using explicit local model paths.

This version avoids Hugging Face resolution by using direct file-based loading where possible.
If your diffusers build still tries to reach the hub, use the local ComfyUI model paths below
and prefer the fallback ComfyUI-compatible output workflow in this workspace.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from PIL import Image
import torch

ROOT = Path(r"F:/tiroltourismus/wappen")
OUT_DIR = ROOT / "img" / "lokal"
META_PATH = ROOT / "wappen_page_data.json"

# Direct local model files already present in ComfyUI.
UNET_PATH = Path(r"E:/HermesPortable/ComfyUI/models/unet/flux1-dev-fp8-e4m3fn.safetensors")
VAE_PATH = Path(r"E:/HermesPortable/ComfyUI/models/vae/flux-vae-bf16.safetensors")
CLIP_L_PATH = Path(r"E:/HermesPortable/ComfyUI/models/clip/clip_l.safetensors")
T5_PATH = Path(r"E:/HermesPortable/ComfyUI/models/clip/t5xxl_fp16.safetensors")

WORK_W = int(os.environ.get("FLUX_WORK_W", "768"))
WORK_H = int(os.environ.get("FLUX_WORK_H", "896"))
TARGET_W = int(os.environ.get("FLUX_TARGET_W", "120"))
TARGET_H = int(os.environ.get("FLUX_TARGET_H", "144"))
STEPS = int(os.environ.get("FLUX_STEPS", "4"))
GUIDANCE = float(os.environ.get("FLUX_GUIDANCE", "3.5"))

PROMPT_TEMPLATE = (
    "modern minimalist flat vector coat of arms for {name} in {bezirk} Tyrol, "
    "clean heraldic shield, bold flat colors, geometric simplified shapes, "
    "precise edges, high contrast, no text, no watermark, logo-like, premium quality"
)
NEGATIVE_PROMPT = (
    "photorealistic, 3d render, complicated background, text, watermark, blur, "
    "noisy, messy, low detail, grain, shadowy illustration"
)


@dataclass
class Target:
    name: str
    bezirk: str
    source_image: Path
    out_path: Path


def safe(name: str) -> str:
    s = name.lower().replace(" ", "_").replace("(", "").replace(")", "").replace(".", "")
    for a, b in [("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss")]:
        s = s.replace(a, b)
    return "".join(c for c in s if c.isalnum() or c == "_")


def assert_local_models() -> None:
    paths = [UNET_PATH, VAE_PATH, CLIP_L_PATH, T5_PATH]
    missing = [str(p) for p in paths if not p.exists()]
    if missing:
        raise FileNotFoundError("Missing local FLUX files:\n" + "\n".join(missing))


def load_metadata() -> list[Target]:
    with META_PATH.open(encoding="utf-8") as f:
        data = json.load(f)

    existing = {
        fn.replace("wappen_", "").split("_modern_")[0]
        for fn in os.listdir(OUT_DIR)
        if fn.startswith("wappen_") and fn.endswith(".png") and "_modern_" in fn
    }

    items: list[Target] = []
    for b in data["bezirke"]:
        for o in b["orte"]:
            key = safe(o["name"])
            if key in existing:
                continue
            src = o.get("img", "") or b.get("img", "")
            if not src:
                continue
            src_path = ROOT / src
            if not src_path.exists():
                continue
            out_path = OUT_DIR / f"wappen_{key}_flux_modern_00001_.png"
            items.append(Target(o["name"], b["name"], src_path, out_path))
    return items


def ensure_outdir() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)


def load_pipe():
    # Lazy import so the script can list targets without loading heavy deps.
    from diffusers import FluxPipeline

    # Try direct local loading only.
    pipe = FluxPipeline.from_single_file(
        str(UNET_PATH),
        local_files_only=True,
        torch_dtype=torch.bfloat16,
    )
    pipe.to('cuda')
    return pipe


def gen_one(pipe, target: Target, seed: int) -> Path:
    prompt = PROMPT_TEMPLATE.format(name=target.name, bezirk=target.bezirk)
    g = torch.Generator(device="cuda").manual_seed(seed)
    result = pipe(
        prompt=prompt,
        negative_prompt=NEGATIVE_PROMPT,
        num_inference_steps=STEPS,
        guidance_scale=GUIDANCE,
        height=WORK_H,
        width=WORK_W,
        generator=g,
    )
    img = result.images[0].convert("RGBA")
    img = img.resize((TARGET_W, TARGET_H), Image.LANCZOS)
    target.out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(target.out_path)
    return target.out_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--seed", type=int, default=12345)
    parser.add_argument("--retry", type=int, default=2)
    parser.add_argument("--sleep", type=float, default=1.0)
    parser.add_argument("--list-only", action="store_true")
    args = parser.parse_args()

    ensure_outdir()
    assert_local_models()
    targets = load_metadata()
    if args.limit and args.limit > 0:
        targets = targets[: args.limit]

    print(f"Missing targets: {len(targets)}")
    if args.list_only:
        for t in targets:
            print(f"- {t.bezirk}: {t.name} -> {t.source_image}")
        return 0

    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is not available in PyTorch")

    print("Loading local FLUX from explicit file path...")
    print(f"UNET={UNET_PATH}")
    print(f"VAE={VAE_PATH}")
    print(f"CLIP_L={CLIP_L_PATH}")
    print(f"T5={T5_PATH}")
    pipe = load_pipe()
    print(f"Loaded. Working size={WORK_W}x{WORK_H} target={TARGET_W}x{TARGET_H} steps={STEPS}")

    ok = 0
    fail = 0
    for idx, target in enumerate(targets, 1):
        print(f"[{idx}/{len(targets)}] {target.bezirk} / {target.name}")
        made = False
        for attempt in range(1, args.retry + 2):
            try:
                seed = args.seed + idx * 1009 + attempt * 17
                t0 = time.time()
                out = gen_one(pipe, target, seed)
                dt = time.time() - t0
                print(f"  OK -> {out.name} ({dt:.1f}s)")
                ok += 1
                made = True
                break
            except torch.cuda.OutOfMemoryError:
                print("  OOM -> clearing cache and retrying")
                torch.cuda.empty_cache()
                time.sleep(2)
            except Exception as e:
                print(f"  ERR attempt {attempt}: {e}")
                time.sleep(2)
        if not made:
            fail += 1
        time.sleep(args.sleep)

    print(f"Done: {ok} ok, {fail} failed")
    return 0 if fail == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())

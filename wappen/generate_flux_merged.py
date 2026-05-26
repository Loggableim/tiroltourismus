#!/usr/bin/env python3
"""Local FLUX img2img generation using a merged single-file checkpoint.

This is the alternate setup: no ComfyUI queue, no REST API, just diffusers
loading the public merged Flux checkpoint from a local path.

Output naming matches the existing gallery convention:
    wappen_<safe_name>_modern_00001_.png
"""
from __future__ import annotations

import argparse
import json
import os
import re
import time
from pathlib import Path

import torch
from PIL import Image
from diffusers import FluxImg2ImgPipeline

ROOT = Path(r"F:/tiroltourismus/wappen")
DATA = ROOT / "wappen_page_data.json"
MODEL = ROOT / "models" / "flux_merged" / "flux1-dev-fp8.safetensors"
OUT = ROOT / "img" / "lokal"
LOG = ROOT / "gen_flux_merged.log"

PROMPT = (
    "modern minimalist flat vector coat of arms redesign, heraldic shield, clean geometric shapes, "
    "bold flat colors, simplified minimalist style, premium quality, no text, no watermark"
)

NEG = (
    "photo, realistic, 3d render, text, letters, watermark, blurry, noisy, low quality, distorted shield"
)


def log(msg: str) -> None:
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open('a', encoding='utf-8', errors='replace') as f:
        f.write(line + "\n")


def safe(name: str) -> str:
    s = name.lower().replace(' ', '_').replace('(', '').replace(')', '').replace('.', '')
    for a, b in [('ä', 'ae'), ('ö', 'oe'), ('ü', 'ue'), ('ß', 'ss')]:
        s = s.replace(a, b)
    return ''.join(c for c in s if c.isalnum() or c == '_')


def desired_output(name: str) -> Path:
    return OUT / f"wappen_{safe(name)}_modern_00001_.png"


def existing_keys() -> set[str]:
    keys = set()
    if not OUT.exists():
        return keys
    for fn in os.listdir(OUT):
        if not fn.lower().endswith('.png'):
            continue
        if not fn.startswith('wappen_'):
            continue
        base = fn[len('wappen_'):]
        base = re.sub(r'_\d{5}_(?=\.png$)', '_', base)
        base = base.replace('_flux_modern', '_modern')
        if base.endswith('.png'):
            base = base[:-4]
        keys.add(base)
    return keys


def load_jobs(limit: int | None = None):
    data = json.loads(DATA.read_text(encoding='utf-8'))
    done = existing_keys()
    jobs = []
    for bezirk in data['bezirke']:
        for ort in bezirk['orte']:
            k = f"{safe(ort['name'])}_modern"
            if k in done:
                continue
            img = ROOT / ort['img']
            if img.exists():
                jobs.append((bezirk['name'], ort['name'], img))
    return jobs[:limit] if limit else jobs


def load_pipe():
    if not MODEL.exists():
        raise FileNotFoundError(f"Missing model: {MODEL}")
    log(f"loading model: {MODEL}")
    pipe = FluxImg2ImgPipeline.from_single_file(
        str(MODEL),
        torch_dtype=torch.float16,
        local_files_only=True,
    )
    pipe.enable_attention_slicing()
    try:
        pipe.vae.enable_slicing()
    except Exception:
        pass
    try:
        pipe.vae.enable_tiling()
    except Exception:
        pass
    try:
        pipe.enable_model_cpu_offload()
    except Exception:
        pipe.to('cuda')
    return pipe


def prep_image(path: Path, width: int, height: int) -> Image.Image:
    img = Image.open(path).convert('RGB')
    return img.resize((width, height), Image.LANCZOS)


def gen_one(pipe, bezirk: str, name: str, src: Path, steps: int, strength: float, width: int, height: int, seed: int):
    img = prep_image(src, width, height)
    g = torch.Generator(device='cuda').manual_seed(seed)
    prompt = f"{PROMPT}. municipality: {name}. district: {bezirk}."
    out = pipe(
        prompt=prompt,
        prompt_2=prompt,
        negative_prompt=NEG,
        negative_prompt_2=NEG,
        true_cfg_scale=1.0,
        image=img,
        width=width,
        height=height,
        strength=strength,
        num_inference_steps=steps,
        guidance_scale=3.5,
        generator=g,
        max_sequence_length=512,
    )
    image = out.images[0]
    final = image.resize((120, 144), Image.LANCZOS)
    out_path = desired_output(name)
    final.save(out_path)
    return out_path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--limit', type=int, default=0)
    ap.add_argument('--steps', type=int, default=12)
    ap.add_argument('--strength', type=float, default=0.55)
    ap.add_argument('--width', type=int, default=512)
    ap.add_argument('--height', type=int, default=608)
    ap.add_argument('--seed', type=int, default=42)
    args = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    jobs = load_jobs(args.limit if args.limit else None)
    log(f'jobs={len(jobs)}')
    if not jobs:
        log('nothing to do')
        return

    pipe = load_pipe()
    ok = 0
    for idx, (bezirk, name, src) in enumerate(jobs, 1):
        log(f'[{idx}/{len(jobs)}] {bezirk} / {name}')
        for attempt in range(1, 4):
            try:
                seed = args.seed + idx * 1000 + attempt
                out_path = gen_one(pipe, bezirk, name, src, args.steps, args.strength, args.width, args.height, seed)
                log(f'OK {name} -> {out_path.name}')
                ok += 1
                break
            except Exception as e:
                log(f'fail {name} attempt={attempt}: {e}')
                if attempt == 3:
                    raise
                time.sleep(5)
    log(f'done ok={ok}/{len(jobs)}')


if __name__ == '__main__':
    main()

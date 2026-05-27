#!/usr/bin/env python3
"""1 subject × 5 styles — txt2img (kein HF-Download nötig)."""
import sys, time
from pathlib import Path
import torch
from diffusers import StableDiffusionXLPipeline

MODEL = Path(r"C:/HermesPortable/ComfyUI/models/checkpoints/sd_xl_base_1.0.safetensors")
OUT = Path(r"F:/tiroltourismus/public/images/magazin/apres-ski-in-tirol-die-besten-adressen")

def log(m):
    sys.stdout.write(f"[{time.strftime('%H:%M:%S')}] {m}\n"); sys.stdout.flush()

# Gleiches Motiv in 5 verschiedenen Stilen
VARIANTS = [
    {
        "name": "01_comic",
        "prompt": "Alpine après-ski hut in snow at golden hour, warm windows, mountain backdrop. Comic book style, bold black outlines, cel shading, vibrant colors, graphic novel aesthetic, halftone dots",
        "neg": "photorealistic, painting, watercolor, blur, 3d render",
        "seed": 42,
    },
    {
        "name": "02_pop_art",
        "prompt": "Alpine après-ski hut in snow at golden hour, warm windows, mountain backdrop. Pop art style, Andy Warhol inspired, bold flat colors, high contrast, screen print aesthetic, saturated graphic",
        "neg": "photorealistic, painting, blur, 3d, sketch",
        "seed": 137,
    },
    {
        "name": "03_fotoreal",
        "prompt": "Alpine après-ski hut in snow at golden hour, warm windows, mountain backdrop. Ultra photorealistic, National Geographic photography, hyperdetailed, sharp focus, natural lighting, 8k",
        "neg": "cartoon, painting, illustration, sketch, 3d, anime, drawing",
        "seed": 256,
    },
    {
        "name": "04_skizze",
        "prompt": "Alpine après-ski hut in snow at golden hour, warm windows, mountain backdrop. Pencil sketch, hand-drawn, charcoal on paper, rough lines, monochrome, artistic, textured paper",
        "neg": "photo, painting, colorful, 3d, digital, render, vibrant",
        "seed": 384,
    },
    {
        "name": "05_aquarell",
        "prompt": "Alpine après-ski hut in snow at golden hour, warm windows, mountain backdrop. Watercolor painting, soft washes, paper texture, loose brush strokes, transparent colors, artistic painterly",
        "neg": "photo, comic, 3d, sharp lines, digital art, graphic, neon",
        "seed": 511,
    },
]

log("Loading SDXL...")
pipe = StableDiffusionXLPipeline.from_single_file(str(MODEL), torch_dtype=torch.float16)
pipe.to("cuda")
pipe.vae.enable_slicing()
log(f"Loaded. VRAM: {torch.cuda.memory_allocated()/1024**3:.1f} GB")

for v in VARIANTS:
    out = OUT / f"{v['name']}.png"
    log(f"[{v['name']}] seed={v['seed']}...")
    gen = torch.Generator(device="cuda").manual_seed(v["seed"])
    img = pipe(
        prompt=v["prompt"], negative_prompt=v["neg"],
        height=1024, width=1024,
        guidance_scale=7.0, num_inference_steps=25, generator=gen,
    ).images[0]
    img.save(out)
    log(f"  ✓ ({out.stat().st_size/1024:.0f} KB)")

log("Done!")

#!/usr/bin/env python3
"""Generate 5 magazine images using SDXL (fits 12GB VRAM)."""
import sys, time
from pathlib import Path

import torch
from diffusers import StableDiffusionXLPipeline

MODEL = Path(r"C:/HermesPortable/ComfyUI/models/checkpoints/sd_xl_base_1.0.safetensors")
OUT = Path(r"F:/tiroltourismus/public/images/magazin/apres-ski-in-tirol-die-besten-adressen")
OUT.mkdir(parents=True, exist_ok=True)

def log(m):
    sys.stdout.write(f"[{time.strftime('%H:%M:%S')}] {m}\n")
    sys.stdout.flush()

STYLE = (
    "editorial magazine photography, warm alpine atmosphere, soft golden-hour lighting, "
    "cinematic, rich colors, shallow depth of field, premium travel magazine aesthetic, "
    "professional photography, 8k detail, warm tones, atmospheric depth"
)
NEG = (
    "cartoon, anime, illustration, painting, drawing, text, watermark, logo, "
    "overexposed, harsh shadows, low quality, blurry, grainy, "
    "deformed, unnatural colors, amateur, snapshot, oversaturated"
)

VARIANTS = [
    {
        "name": "01_après_ski_hütte",
        "prompt": "Wooden après-ski hut in the alps at golden hour, warm glowing lights inside, snow-covered roof, steam rising from mulled wine, friends laughing at wooden tables, austrian alps mountain panorama, " + STYLE,
        "seed": 42,
    },
    {
        "name": "02_skifahrer_panorama",
        "prompt": "Skiers carving down a groomed alpine slope, dramatic mountain panorama, deep blue sky with soft clouds, snow sparkling in afternoon sun, tyrolean alps, aerial mountain view, " + STYLE,
        "seed": 137,
    },
    {
        "name": "03_glühwein_abend",
        "prompt": "Cozy alpine evening scene, friends holding steaming mulled wine glasses, warm firelight reflecting on faces, wooden alpine hut interior, candlelight, soft warm bokeh, authentic tyrolean atmosphere, " + STYLE,
        "seed": 256,
    },
    {
        "name": "04_berggipfel_dämmerung",
        "prompt": "Dramatic alpine mountain peak at twilight, last sunlight hitting the summit, deep purple and orange sky, snow-capped mountains, alpine glow phenomenon, tyrolean alps panorama, " + STYLE,
        "seed": 384,
    },
    {
        "name": "05_seilbahn_ski",
        "prompt": "Modern ski gondola ascending above tree line, golden sunset light, skiers on the slope below, dramatic cloud formations, birds-eye cinematic view, tyrolean ski resort, " + STYLE,
        "seed": 511,
    },
]

log(f"Loading SDXL from {MODEL}...")
pipe = StableDiffusionXLPipeline.from_single_file(
    str(MODEL),
    torch_dtype=torch.float16,
)
pipe.to("cuda")
pipe.vae.enable_slicing()
log(f"Loaded. VRAM: {torch.cuda.memory_allocated()/1024**3:.1f} GB")

for v in VARIANTS:
    out_path = OUT / f"{v['name']}.png"
    log(f"Generating [{v['name']}] seed={v['seed']}...")
    gen = torch.Generator(device="cuda").manual_seed(v["seed"])
    img = pipe(
        prompt=v["prompt"],
        negative_prompt=NEG,
        height=1024, width=1024,
        guidance_scale=7.0,
        num_inference_steps=25,
        generator=gen,
    ).images[0]
    img.save(out_path)
    log(f"  ✓ {out_path.name} ({out_path.stat().st_size/1024:.0f} KB)")

log("Finished! 5/5 variants generated.")

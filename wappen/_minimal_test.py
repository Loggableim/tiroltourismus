#!/usr/bin/env python3
"""Minimal FLUX generation test - with CPU offload to handle 12GB VRAM."""
import sys, time
from pathlib import Path

import torch
from diffusers import FluxPipeline

MODEL = Path(r"C:/projekte/offlinebildgeneratoren/models/flux_merged/flux1-dev-fp8.safetensors")
OUT = Path(r"F:/tiroltourismus/public/images/magazin/apres-ski-in-tirol-die-besten-adressen")
OUT.mkdir(parents=True, exist_ok=True)

def log(m):
    sys.stdout.write(f"[{time.strftime('%H:%M:%S')}] {m}\n")
    sys.stdout.flush()

log("Loading pipeline...")
pipe = FluxPipeline.from_single_file(
    str(MODEL),
    torch_dtype=torch.float16,
)
# Use sequential CPU offload to stay within 12GB VRAM
pipe.enable_model_cpu_offload()
pipe.vae.enable_slicing()
log("Loaded!")

seed = 42
gen = torch.Generator(device="cuda").manual_seed(seed)
img = pipe(
    prompt="editorial photography of a cozy alpine ski hut at golden hour, warm lighting",
    height=800, width=1200,
    guidance_scale=3.5, num_inference_steps=12,
    max_sequence_length=256, generator=gen,
).images[0]
img.save(OUT / "test.png")
log(f"Saved test.png ({Path(OUT/'test.png').stat().st_size/1024:.0f} KB)")

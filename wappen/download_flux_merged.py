#!/usr/bin/env python3
from pathlib import Path
from huggingface_hub import hf_hub_download

OUT = Path(r'F:/tiroltourismus/wappen/models/flux_merged')
OUT.mkdir(parents=True, exist_ok=True)
path = hf_hub_download(
    repo_id='Comfy-Org/flux1-dev',
    filename='flux1-dev-fp8.safetensors',
    local_dir=str(OUT),
    local_dir_use_symlinks=False,
    resume_download=True,
)
print(path)

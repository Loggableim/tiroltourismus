#!/usr/bin/env python3
from pathlib import Path
from huggingface_hub import hf_hub_download

repo_id = 'Comfy-Org/flux1-dev'
filename = 'flux1-dev-fp8.safetensors'
base = Path(r'F:/tiroltourismus/wappen/models/flux_merged')
cache_dir = base / '.cache'
cache_dir.mkdir(parents=True, exist_ok=True)
path = hf_hub_download(
    repo_id=repo_id,
    filename=filename,
    cache_dir=str(cache_dir),
    force_download=False,
    resume_download=True,
)
print(path)

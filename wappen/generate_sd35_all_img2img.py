#!/usr/bin/env python3
from __future__ import annotations

import gc
import json
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(r"F:/tiroltourismus/wappen")
VENDOR = ROOT / ".vendor"
if VENDOR.exists():
    sys.path.insert(0, str(VENDOR))

import torch
from PIL import Image
from diffusers import StableDiffusion3Img2ImgPipeline
from huggingface_hub import hf_hub_download, snapshot_download
from transformers import CLIPTextModelWithProjection, T5EncoderModel

REPO = "stabilityai/stable-diffusion-3.5-medium"
OUT_ROOT = ROOT / "img" / "sd35"
MODEL_DIR = ROOT / "models" / "sd35"
MODEL_FILE = MODEL_DIR / "sd3.5_medium.safetensors"
CONFIG_DIR = ROOT / "diffusers-sd35-config"
STAGE_DIR = ROOT / "models" / "sd35_stage"
LOG = ROOT / "generate_sd35_all_img2img.log"
DATA = ROOT / "wappen_page_data.json"

PROMPT = (
    "modern minimalist flat vector coat of arms redesign, heraldic shield, clean geometric shapes, "
    "bold flat colors, simplified minimalist style, premium quality, no text, no watermark"
)
NEG = (
    "photo, realistic, 3d render, blurry, noisy, low quality, text, letters, watermark, extra limbs, "
    "messy background, illegible details"
)

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
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8", errors="replace") as f:
        f.write(line + "\n")


def safe_rel(rel: str) -> str:
    return rel.replace("\\", "/")


def ensure_config() -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    log(f"snapshot_download config -> {CONFIG_DIR}")
    snapshot_download(
        repo_id=REPO,
        local_dir=str(CONFIG_DIR),
        local_dir_use_symlinks=False,
        allow_patterns=CONFIG_PATTERNS,
    )


def _stage_dir(name: str) -> Path:
    d = STAGE_DIR / name
    d.mkdir(parents=True, exist_ok=True)
    return d


def _copy_config(subfolder: str, dst: Path) -> None:
    src = CONFIG_DIR / subfolder / "config.json"
    dst.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst / "config.json")


def _load_clip(subfolder: str, filename: str) -> CLIPTextModelWithProjection:
    dst = _stage_dir(subfolder)
    _copy_config(subfolder, dst)
    log(f"download {filename}")
    fp = hf_hub_download(
        repo_id=REPO,
        filename=filename,
        local_dir=str(dst),
        local_dir_use_symlinks=False,
    )
    fp = Path(fp)
    target = dst / "model.safetensors"
    if fp != target:
        if target.exists():
            target.unlink()
        fp.replace(target)
    log(f"load {subfolder}")
    model = CLIPTextModelWithProjection.from_pretrained(dst, torch_dtype=torch.float16, use_safetensors=True)
    shutil.rmtree(dst, ignore_errors=True)
    gc.collect()
    return model


def _load_t5() -> T5EncoderModel:
    dst = _stage_dir("text_encoder_3")
    _copy_config("text_encoder_3", dst)
    log("download text_encoders/t5xxl_fp8_e4m3fn.safetensors")
    fp = hf_hub_download(
        repo_id=REPO,
        filename="text_encoders/t5xxl_fp8_e4m3fn.safetensors",
        local_dir=str(dst),
        local_dir_use_symlinks=False,
    )
    fp = Path(fp)
    target = dst / "model.safetensors"
    if fp != target:
        if target.exists():
            target.unlink()
        fp.replace(target)
    log("load text_encoder_3")
    model = T5EncoderModel.from_pretrained(dst, torch_dtype=torch.float16, use_safetensors=True)
    shutil.rmtree(dst, ignore_errors=True)
    gc.collect()
    return model


def ensure_model_file() -> Path:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    if MODEL_FILE.exists() and MODEL_FILE.stat().st_size > 1_000_000_000:
        return MODEL_FILE
    log(f"download checkpoint -> {MODEL_FILE}")
    fp = hf_hub_download(
        repo_id=REPO,
        filename="sd3.5_medium.safetensors",
        local_dir=str(MODEL_DIR),
        local_dir_use_symlinks=False,
    )
    return Path(fp)


def build_pipe() -> StableDiffusion3Img2ImgPipeline:
    ensure_config()

    # Load text encoders one at a time to keep disk pressure low.
    clip1 = _load_clip("text_encoder", "text_encoder/model.safetensors")
    clip2 = _load_clip("text_encoder_2", "text_encoder_2/model.safetensors")
    t5 = _load_t5()

    model_file = ensure_model_file()
    log("loading pipeline from single-file checkpoint")
    pipe = StableDiffusion3Img2ImgPipeline.from_single_file(
        str(model_file),
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


def prep_image(path: Path, width: int, height: int) -> Image.Image:
    img = Image.open(path).convert("RGB")
    return img.resize((width, height), Image.LANCZOS)


def output_path(src_rel: str) -> Path:
    rel = Path(safe_rel(src_rel))
    return OUT_ROOT / rel.relative_to("img")


def load_jobs():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    jobs = []
    for bezirk in data["bezirke"]:
        jobs.append({
            "kind": "bezirk",
            "district": bezirk["name"],
            "district_key": bezirk["key"],
            "name": bezirk["name"],
            "src": bezirk["img"],
        })
        for ort in bezirk["orte"]:
            jobs.append({
                "kind": "ort",
                "district": bezirk["name"],
                "district_key": bezirk["key"],
                "name": ort["name"],
                "src": ort["img"],
            })
    return jobs


def gen_one(pipe: StableDiffusion3Img2ImgPipeline, job: dict, idx: int, total: int) -> Path:
    src = ROOT / job["src"]
    out = output_path(job["src"])
    if out.exists() and out.stat().st_size > 0:
        return out

    out.parent.mkdir(parents=True, exist_ok=True)
    prompt = (
        f"{PROMPT}. coat of arms of {job['name']}. district: {job['district']}. "
        f"kind: {job['kind']}."
    )
    img = prep_image(src, 512, 608)
    seed = (abs(hash((job['district_key'], job['name'], job['kind']))) % 2_000_000_000) + 1000
    g = torch.Generator(device="cuda").manual_seed(seed)
    result = pipe(
        prompt=prompt,
        prompt_2=prompt,
        prompt_3=prompt,
        negative_prompt=NEG,
        negative_prompt_2=NEG,
        negative_prompt_3=NEG,
        image=img,
        strength=0.55,
        num_inference_steps=12,
        guidance_scale=4.0,
        width=512,
        height=608,
        generator=g,
        max_sequence_length=256,
    ).images[0]
    final = result.resize((120, 144), Image.LANCZOS)
    final.save(out)
    return out


def main() -> None:
    jobs = load_jobs()
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    log(f"jobs={len(jobs)}")
    pipe = build_pipe()
    done = 0
    for i, job in enumerate(jobs, 1):
        out = output_path(job["src"])
        if out.exists() and out.stat().st_size > 0:
            log(f"skip {i}/{len(jobs)} {job['name']} -> exists")
            continue
        log(f"[{i}/{len(jobs)}] {job['district']} / {job['name']}")
        for attempt in range(1, 4):
            try:
                out = gen_one(pipe, job, i, len(jobs))
                log(f"OK {job['name']} -> {out.relative_to(OUT_ROOT)}")
                done += 1
                break
            except Exception as e:
                log(f"fail {job['name']} attempt={attempt}: {e}")
                if attempt == 3:
                    raise
                time.sleep(5)
        if i % 10 == 0:
            try:
                torch.cuda.empty_cache()
            except Exception:
                pass
    log(f"done generated={done}/{len(jobs)}")


if __name__ == "__main__":
    main()

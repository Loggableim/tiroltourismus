#!/usr/bin/env python3
from __future__ import annotations

import json
import time
from pathlib import Path

import torch
from PIL import Image
from diffusers import StableDiffusionImg2ImgPipeline

ROOT = Path(r"F:/tiroltourismus/wappen")
DATA = ROOT / "wappen_page_data.json"
MODEL_DIR = ROOT / "models" / "sd15_repo"
OUT_ROOT = ROOT / "img" / "sd15_ultra_minimal"
INPUT_ROOT = ROOT / "img" / "sd15_ultra_minimal_inputs"
HTML_OUT = ROOT / "sd15_ultra_minimal.html"
JSON_OUT = ROOT / "sd15_ultra_minimal.json"

WIDTH = 576
HEIGHT = 720
NUM_STEPS = 16
GUIDANCE = 6.0
STRENGTH = 0.85

PROMPT = (
    "Ultra-minimal contemporary civic emblem, flat geometric logo, 1-2 solid colors, clean negative space, "
    "Swiss modernist precision, sharp but simple silhouette, premium identity design, distinctive and abstract, "
    "not a classical coat of arms, not medieval, no ornament, no towers, no lions, no crowns, no scrollwork, "
    "no extra symbols, no text, no watermark, no realistic shading, no background scene."
)

NEGATIVE = (
    "coat of arms, wappen, heraldry, medieval ornament, lion, tower, crown, scrollwork, baroque, emblem clutter, "
    "text, watermark, photo, realistic, 3d render, background, scenery, people, landscape, gradients, shading, texture, blurry"
)


def log(msg: str) -> None:
    print(msg, flush=True)


def slug(name: str) -> str:
    return (
        name.lower()
        .replace("ä", "ae")
        .replace("ö", "oe")
        .replace("ü", "ue")
        .replace("ß", "ss")
        .replace(".", "")
        .replace(" ", "_")
        .replace("-", "_")
    )


def load_data() -> list[dict]:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    rows: list[dict] = []
    for bez in data["bezirke"]:
        bez_key = bez["key"]
        for ort in bez["orte"]:
            rows.append(
                {
                    "bezirk": bez["name"],
                    "bezirk_key": bez_key,
                    "ort": ort["name"],
                    "src": ROOT / ort["img"],
                    "out": OUT_ROOT / bez_key / f"{slug(ort['name'])}.png",
                    "input": INPUT_ROOT / bez_key / f"{slug(ort['name'])}.png",
                }
            )
    return rows


def prepare_input(src: Path, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    img = Image.open(src).convert("RGB")
    img = img.resize((WIDTH, HEIGHT), Image.LANCZOS)
    img.save(dest)
    return dest


def load_pipe() -> StableDiffusionImg2ImgPipeline:
    pipe = StableDiffusionImg2ImgPipeline.from_pretrained(
        MODEL_DIR,
        torch_dtype=torch.float16,
        variant="fp16",
        use_safetensors=True,
        safety_checker=None,
        requires_safety_checker=False,
    )
    pipe.to("cuda")
    pipe.enable_attention_slicing()
    pipe.enable_vae_slicing()
    return pipe


def build_html(results: list[dict]) -> None:
    sections = []
    current = None
    cards = []

    def flush_block(block_name: str | None, block_cards: list[str]) -> str:
        if not block_name:
            return ""
        return f'''<section class="block"><h2>{block_name}</h2><div class="grid">{''.join(block_cards)}</div></section>'''

    for row in results:
        if current != row["bezirk"]:
            if current is not None:
                sections.append(flush_block(current, cards))
            current = row["bezirk"]
            cards = []
        cards.append(
            f'''<article class="card"><div class="label">{row['ort']}</div><img src="{row['img_rel']}" alt="{row['ort']} ultra minimal"></article>'''
        )
    if current is not None:
        sections.append(flush_block(current, cards))

    html = f'''<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Tirol Wappen – Ultra Minimal</title>
<style>
:root {{ color-scheme: dark; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif; background:#0b0d12; color:#eee; }}
header {{ padding:20px 24px; background:linear-gradient(135deg,#151922,#0d1016); border-bottom:1px solid #23293a; position:sticky; top:0; z-index:5; }}
h1 {{ margin:0 0 8px; font-size:1.4rem; }}
.sub {{ color:#9aa3b2; font-size:.92rem; line-height:1.45; }}
main {{ padding:18px 24px 30px; }}
.block {{ margin-bottom:34px; }}
.block h2 {{ margin:0 0 14px; padding-bottom:8px; border-bottom:1px solid #23293a; font-size:1.15rem; }}
.grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(160px,1fr)); gap:12px; }}
.card {{ background:#121621; border:1px solid #23293a; border-radius:14px; overflow:hidden; }}
.label {{ padding:10px 12px; font-size:.72rem; text-transform:uppercase; letter-spacing:.06em; color:#97a1b7; border-bottom:1px solid #23293a; background:#171b26; }}
.card img {{ display:block; width:100%; aspect-ratio:4/5; object-fit:contain; background:#0b0d12; }}
footer {{ padding:18px 24px 30px; color:#788; font-size:.8rem; border-top:1px solid #23293a; }}
code {{ color:#a8c7ff; }}
</style>
</head>
<body>
<header>
  <h1>Tirol Wappen – Ultra Minimal</h1>
  <div class="sub">Prompt-basierte Batch-Generierung für alle Wappen von Tirol. Der Stil ist bewusst ultrareduziert: flat, geometrisch, abstrakt, ohne klassische Heraldik-Deko.</div>
</header>
<main>
{''.join(sections)}
</main>
<footer>
  Öffnen: <code>file:///F:/tiroltourismus/wappen/sd15_ultra_minimal.html</code>
</footer>
</body>
</html>'''
    HTML_OUT.write_text(html, encoding="utf-8")


def main() -> None:
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is not available")
    torch.backends.cuda.matmul.allow_tf32 = True
    rows = load_data()
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    INPUT_ROOT.mkdir(parents=True, exist_ok=True)
    pipe = load_pipe()

    results: list[dict] = []
    total = len(rows)
    for idx, row in enumerate(rows, start=1):
        out_path = row["out"]
        input_path = prepare_input(row["src"], row["input"])
        out_path.parent.mkdir(parents=True, exist_ok=True)
        if out_path.exists() and out_path.stat().st_size > 0:
            log(f"[{idx}/{total}] skip {row['bezirk']} / {row['ort']}")
            results.append({
                "bezirk": row["bezirk"],
                "ort": row["ort"],
                "img_rel": out_path.relative_to(ROOT).as_posix(),
            })
            continue
        seed = abs(hash((row["bezirk_key"], row["ort"]))) % (2**31)
        generator = torch.Generator(device="cuda").manual_seed(seed)
        log(f"[{idx}/{total}] gen {row['bezirk']} / {row['ort']} seed={seed}")
        for attempt in range(1, 4):
            try:
                result = pipe(
                    prompt=f"{PROMPT} Subject: {row['ort']}, Tirol, Austria.",
                    negative_prompt=NEGATIVE,
                    image=Image.open(input_path).convert("RGB"),
                    strength=STRENGTH,
                    guidance_scale=GUIDANCE,
                    num_inference_steps=NUM_STEPS,
                    generator=generator,
                )
                img = result.images[0]
                img.save(out_path)
                log(f"[{idx}/{total}] saved {out_path} ({out_path.stat().st_size} bytes)")
                results.append({
                    "bezirk": row["bezirk"],
                    "ort": row["ort"],
                    "img_rel": out_path.relative_to(ROOT).as_posix(),
                })
                break
            except Exception as e:
                log(f"[{idx}/{total}] error attempt {attempt}: {e}")
                if attempt == 3:
                    raise
                time.sleep(4)
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    JSON_OUT.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    build_html(results)
    log(f"wrote {HTML_OUT}")
    log(f"generated {len(results)}/{total}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
from __future__ import annotations

import json
import time
from pathlib import Path

import torch
from PIL import Image
from diffusers import StableDiffusionImg2ImgPipeline

ROOT = Path(r"F:/tiroltourismus/wappen")
MODEL_DIR = ROOT / "models" / "sd15_repo"
OUT_ROOT = ROOT / "img" / "sd15_radical_variants"
INPUT_ROOT = ROOT / "img" / "sd15_radical_inputs"
HTML_OUT = ROOT / "sd15_radical_variants.html"
PROMPT_JSON = ROOT / "sd15_radical_variants.json"

SOURCES = [
    {
        "id": "innsbruck",
        "title": "Innsbruck",
        "src": ROOT / "img" / "orte" / "statutarstadt_innsbruck" / "stadtwappen.png",
        "base_prompt": (
            "A radical reinterpretation of the Innsbruck coat of arms as a contemporary abstract brand mark. "
            "Preserve only a vertical shield silhouette and the civic identity. Remove medieval ornament, towers, sub-shields, figures, scrollwork, and text. "
            "Turn it into a minimal geometric symbol that feels like a cutting-edge identity system."
        ),
    },
    {
        "id": "kitzbuehel",
        "title": "Kitzbühel",
        "src": ROOT / "img" / "orte" / "kitzbühel" / "kitzbühel.png",
        "base_prompt": (
            "A radical reinterpretation of the Kitzbühel coat of arms as a contemporary abstract alpine brand mark. "
            "Preserve only a vertical shield silhouette and the alpine civic identity. Remove medieval ornament, towers, sub-shields, figures, scrollwork, and text. "
            "Turn it into a minimal geometric symbol that feels like a cutting-edge identity system."
        ),
    },
]

STYLES = [
    ("ultra_minimal", "Ultra Minimal", "ultra-minimal flat emblem, two-tone geometry, Swiss-style precision, generous negative space, crisp corporate identity, highly simplified"),
    ("abstract_mountain", "Abstract Mountain", "abstract alpine mountain geometry, sharp faceted planes, summit silhouette, poster-like composition, modern outdoor brand, bold and sparse"),
    ("monoline_icon", "Monoline Icon", "single-line icon symbol, continuous stroke, minimal contour drawing, elegant and modern, logo-ready, no ornament"),
    ("paper_cut", "Paper Cut", "paper-cut poster, layered flat shapes, torn edges, tactile yet clean, modern editorial design, abstract civic badge"),
    ("ink_stamp", "Ink Stamp", "monochrome ink-stamp symbol, worn paper texture, strong black form, simple and authoritative, very minimal"),
    ("negative_space", "Negative Space", "negative-space emblem, hollow center, bold outer silhouette, smart and contemporary, pure shape language"),
]

NEGATIVE = "towers, castle, miniature shield, extra shields, figures, people, animals, scrollwork, ornament, medieval detail, text, watermark, photo, realistic, 3d render, landscape, scenery, clutter, blurry"
WIDTH = 576
HEIGHT = 720
NUM_STEPS = 28
GUIDANCE = 8.0
STRENGTH = 0.90


def log(msg: str) -> None:
    print(msg, flush=True)


def prepare_input(src: Path, subject: str) -> Path:
    out = INPUT_ROOT / subject / src.name
    out.parent.mkdir(parents=True, exist_ok=True)
    img = Image.open(src).convert("RGB")
    img = img.resize((WIDTH, HEIGHT), Image.LANCZOS)
    img.save(out)
    return out


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


def main() -> None:
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is not available")
    torch.backends.cuda.matmul.allow_tf32 = True
    pipe = load_pipe()
    OUT_ROOT.mkdir(parents=True, exist_ok=True)

    results = []
    for source in SOURCES:
        input_img = prepare_input(source["src"], source["id"])
        subject_out = OUT_ROOT / source["id"]
        subject_out.mkdir(parents=True, exist_ok=True)
        log(f"source={source['title']} input={input_img}")
        variants = []
        for idx, (key, label, extra) in enumerate(STYLES, start=1):
            out_path = subject_out / f"{idx:02d}_{key}.png"
            prompt = f"{source['base_prompt']} Style direction: {extra}. No text, no watermark, no medieval ornament."
            seed = abs(hash((source['id'], key))) % (2**31)
            generator = torch.Generator(device="cuda").manual_seed(seed)
            for attempt in range(1, 4):
                try:
                    log(f"gen {source['title']} / {label} attempt {attempt} seed={seed}")
                    result = pipe(
                        prompt=prompt,
                        negative_prompt=NEGATIVE,
                        image=Image.open(input_img).convert("RGB"),
                        strength=STRENGTH,
                        guidance_scale=GUIDANCE,
                        num_inference_steps=NUM_STEPS,
                        generator=generator,
                    )
                    img = result.images[0]
                    img.save(out_path)
                    log(f"saved {out_path} ({out_path.stat().st_size} bytes)")
                    variants.append({"key": key, "label": label, "img_rel": out_path.relative_to(ROOT).as_posix(), "prompt": prompt})
                    break
                except Exception as e:
                    log(f"error {source['title']} / {label} attempt {attempt}: {e}")
                    if attempt == 3:
                        raise
                    time.sleep(4)
            del result
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        results.append({"title": source["title"], "src_rel": input_img.relative_to(ROOT).as_posix(), "variants": variants})

    PROMPT_JSON.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    build_html(results)
    log(f"wrote {HTML_OUT}")


def build_html(results: list[dict]) -> None:
    sections = []
    for block in results:
        cards = [f'''<div class="card orig"><div class="label">Upscaled source</div><img src="{block['src_rel']}" alt="{block['title']} source"></div>''']
        for var in block["variants"]:
            cards.append(f'''<div class="card"><div class="label">{var['label']}</div><img src="{var['img_rel']}" alt="{block['title']} {var['label']}"><div class="prompt">{var['prompt']}</div></div>''')
        sections.append(f'''
        <section class="block">
          <h2>{block['title']}</h2>
          <div class="grid">{''.join(cards)}</div>
        </section>''')

    html = f'''<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Radical Wappen Variants</title>
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
.grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:14px; }}
.card {{ background:#121621; border:1px solid #23293a; border-radius:14px; overflow:hidden; }}
.card.orig {{ border-color:#334; }}
.label {{ padding:10px 12px; font-size:.74rem; text-transform:uppercase; letter-spacing:.06em; color:#97a1b7; border-bottom:1px solid #23293a; background:#171b26; }}
.card img {{ display:block; width:100%; aspect-ratio:4/5; object-fit:cover; background:#0b0d12; }}
.prompt {{ padding:10px 12px 12px; color:#aab4ca; font-size:.76rem; line-height:1.35; border-top:1px solid #23293a; }}
footer {{ padding:18px 24px 30px; color:#788; font-size:.8rem; border-top:1px solid #23293a; }}
code {{ color:#a8c7ff; }}
</style>
</head>
<body>
<header>
  <h1>Radikale Wappen-Varianten</h1>
  <div class="sub">Prompt-basierte img2img-Generationen mit stärkeren Abstraktions-Anweisungen: keine Mini-Wappen, keine Türmchen, keine Heraldik-Deko, sondern echte Reinterpretationen.</div>
</header>
<main>
{''.join(sections)}
</main>
<footer>
  Öffnen: <code>file:///F:/tiroltourismus/wappen/sd15_radical_variants.html</code>
</footer>
</body>
</html>'''
    HTML_OUT.write_text(html, encoding="utf-8")


if __name__ == "__main__":
    main()

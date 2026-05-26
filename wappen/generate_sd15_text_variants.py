#!/usr/bin/env python3
from __future__ import annotations

import json
import time
from pathlib import Path

import torch
from diffusers import StableDiffusionPipeline

ROOT = Path(r"F:/tiroltourismus/wappen")
MODEL_DIR = ROOT / "models" / "sd15_repo"
OUT_ROOT = ROOT / "img" / "sd15_text_variants"
HTML_OUT = ROOT / "sd15_text_variants.html"
PROMPT_JSON = ROOT / "sd15_text_variants.json"

SUBJECTS = [
    {
        "id": "innsbruck",
        "title": "Innsbruck",
        "base_prompt": (
            "A contemporary alpine civic identity for Innsbruck, Austria. Not a classical coat of arms; instead a modern brand mark, abstract symbol, premium logo design, "
            "inspired by mountain city life, river crossing, and urban-alpine energy, no medieval ornament, no lions, no towers, no scrollwork, no text, no watermark."
        ),
    },
    {
        "id": "kitzbuehel",
        "title": "Kitzbühel",
        "base_prompt": (
            "A contemporary alpine civic identity for Kitzbühel, Austria. Not a classical coat of arms; instead a modern brand mark, abstract symbol, premium logo design, "
            "inspired by alpine town elegance, ski culture, mountain geometry, and outdoor lifestyle, no medieval ornament, no lions, no towers, no scrollwork, no text, no watermark."
        ),
    },
]

STYLES = [
    ("ultra_minimal", "Ultra Minimal", "ultra-minimal flat logo, strong geometry, two-tone palette, generous negative space, Swiss-style precision, crisp and distinctive"),
    ("abstract_mountain", "Abstract Mountain", "abstract mountain geometry, faceted peaks, sleek alpine forms, poster-like composition, modern outdoor brand aesthetic"),
    ("monoline_icon", "Monoline Icon", "single-line icon, elegant continuous stroke, minimal contour drawing, logo-ready, contemporary and refined"),
    ("paper_cut", "Paper Cut", "paper-cut poster, layered flat shapes, torn edges, tactile editorial design, abstract civic badge"),
    ("ink_stamp", "Ink Stamp", "monochrome ink-stamp symbol, worn paper texture, simple authoritative mark, minimal and bold"),
    ("negative_space", "Negative Space", "negative-space emblem, hollow center, bold outer silhouette, smart contemporary branding, pure shape language"),
]

NEGATIVE = "coat of arms, wappen, heraldry, medieval ornament, lion, tower, crown, scrollwork, shield full of symbols, text, watermark, photo, realistic, 3d render, clutter, blurry, extra details"
WIDTH = 576
HEIGHT = 720
NUM_STEPS = 24
GUIDANCE = 7.5


def log(msg: str) -> None:
    print(msg, flush=True)


def load_pipe() -> StableDiffusionPipeline:
    pipe = StableDiffusionPipeline.from_pretrained(
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
    for subject in SUBJECTS:
        subj_out = OUT_ROOT / subject["id"]
        subj_out.mkdir(parents=True, exist_ok=True)
        variants = []
        log(f"subject={subject['title']}")
        for idx, (key, label, extra) in enumerate(STYLES, start=1):
            out_path = subj_out / f"{idx:02d}_{key}.png"
            prompt = f"{subject['base_prompt']} Style direction: {extra}."
            seed = abs(hash((subject['id'], key))) % (2**31)
            generator = torch.Generator(device="cuda").manual_seed(seed)
            for attempt in range(1, 4):
                try:
                    log(f"gen {subject['title']} / {label} attempt {attempt} seed={seed}")
                    result = pipe(
                        prompt=prompt,
                        negative_prompt=NEGATIVE,
                        width=WIDTH,
                        height=HEIGHT,
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
                    log(f"error {subject['title']} / {label} attempt {attempt}: {e}")
                    if attempt == 3:
                        raise
                    time.sleep(4)
            del result
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        results.append({"title": subject["title"], "variants": variants})

    PROMPT_JSON.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    build_html(results)
    log(f"wrote {HTML_OUT}")


def build_html(results: list[dict]) -> None:
    sections = []
    for block in results:
        cards = []
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
<title>SD1.5 Text Variants</title>
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
.label {{ padding:10px 12px; font-size:.74rem; text-transform:uppercase; letter-spacing:.06em; color:#97a1b7; border-bottom:1px solid #23293a; background:#171b26; }}
.card img {{ display:block; width:100%; aspect-ratio:4/5; object-fit:cover; background:#0b0d12; }}
.prompt {{ padding:10px 12px 12px; color:#aab4ca; font-size:.76rem; line-height:1.35; border-top:1px solid #23293a; }}
footer {{ padding:18px 24px 30px; color:#788; font-size:.8rem; border-top:1px solid #23293a; }}
code {{ color:#a8c7ff; }}
</style>
</head>
<body>
<header>
  <h1>SD1.5 Prompt-Only Varianten</h1>
  <div class="sub">Neue, bewusst abstrakte Stilrichtungen — ohne img2img. Das ist näher an einer echten Stilfindung: nicht Filter, sondern prompt-getriebene Reinterpretationen.</div>
</header>
<main>
{''.join(sections)}
</main>
<footer>
  Öffnen: <code>file:///F:/tiroltourismus/wappen/sd15_text_variants.html</code>
</footer>
</body>
</html>'''
    HTML_OUT.write_text(html, encoding="utf-8")


if __name__ == "__main__":
    main()

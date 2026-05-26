#!/usr/bin/env python3
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Iterable

from PIL import Image
from huggingface_hub import InferenceClient

ROOT = Path(r"F:/tiroltourismus/wappen")
OUT_ROOT = ROOT / "img" / "flux_kontext_variants"
INPUT_ROOT = ROOT / "img" / "flux_kontext_inputs"
HTML_OUT = ROOT / "flux_kontext_variants.html"
PROMPT_JSON = ROOT / "flux_kontext_variants.json"
TOKEN_FILE = Path.home() / ".cache" / "huggingface" / "token"
MODEL = "black-forest-labs/FLUX.1-Kontext-dev"
TARGET_SIZE = {"width": 768, "height": 960}

SOURCES = [
    {
        "id": "innsbruck",
        "title": "Innsbruck",
        "src": ROOT / "img" / "orte" / "statutarstadt_innsbruck" / "stadtwappen.png",
        "base_prompt": (
            "A completely reimagined heraldic emblem for Innsbruck, alpine capital and historic gateway city. "
            "Preserve a strong shield silhouette and ceremonial presence, but transform it into a distinctive contemporary design language. "
            "Use alpine urban identity, bridge or river cues, crisp geometry, refined negative space, and a premium editorial look. "
            "No text, no watermark, no photo realism, no background scene."
        ),
    },
    {
        "id": "kitzbuehel",
        "title": "Kitzbühel",
        "src": ROOT / "img" / "orte" / "kitzbühel" / "kitzbühel.png",
        "base_prompt": (
            "A completely reimagined heraldic emblem for Kitzbühel, an alpine mountain town with sporty, elegant identity. "
            "Preserve a strong shield silhouette and ceremonial presence, but transform it into a distinctive contemporary design language. "
            "Use mountain town cues, alpine elegance, crisp geometry, refined negative space, and a premium editorial look. "
            "No text, no watermark, no photo realism, no background scene."
        ),
    },
]

STYLES = [
    {
        "key": "modern_badge",
        "label": "Modern Badge",
        "extra": "Style direction: modern civic badge, crisp vector-like geometry, bold but restrained, clean edges, premium logo design, highly legible, strong contrast, contemporary municipal identity.",
    },
    {
        "key": "stained_glass",
        "label": "Stained Glass",
        "extra": "Style direction: stained glass heraldry, luminous panes, leaded outlines, jewel-like colors, cathedral atmosphere, elegant symmetry, luminous and artistic, not photorealistic.",
    },
    {
        "key": "kintsugi",
        "label": "Kintsugi",
        "extra": "Style direction: kintsugi crest, cracked porcelain repaired with gold seams, refined Japanese craft influence, dark lacquer and warm gold highlights, elegant object design, singular and precious.",
    },
    {
        "key": "topographic",
        "label": "Topographic",
        "extra": "Style direction: alpine topographic emblem, contour lines, map-like ridge forms, mountain-cartography abstraction, technical yet beautiful, layered linework, modern outdoor brand aesthetic.",
    },
    {
        "key": "riso_poster",
        "label": "Riso Poster",
        "extra": "Style direction: risograph poster print, limited ink palette, slight misregistration, bold paper texture, contemporary graphic design, screenprint energy, a collectible art print feel.",
    },
    {
        "key": "brutalist_shield",
        "label": "Brutalist Shield",
        "extra": "Style direction: brutalist angular shield, hard surfaces, carved planes, sharp cuts, monumental and architectural, bold shadows, contemporary city-brand emblem, abstract and powerful.",
    },
    {
        "key": "celestial_seal",
        "label": "Celestial Seal",
        "extra": "Style direction: celestial compass seal, orbit rings, star geometry, cosmic symmetry, elegant badge with navigational feel, mysterious but polished, emblematic and modern.",
    },
    {
        "key": "paper_collage",
        "label": "Paper Collage",
        "extra": "Style direction: cut-paper collage, layered torn paper, assembled geometric fragments, tactile mixed-media design, sophisticated poster composition, handmade but clean and modern.",
    },
]

NEGATIVE = (
    "photo, realistic, 3d render, cartoon, messy background, extra shields, extra symbols, text, watermark, logo mockup, blurry, low quality, clutter, people"
)


def log(msg: str) -> None:
    print(msg, flush=True)


def upscale_input(src: Path, dest: Path, width: int = 768, height: int = 960) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    img = Image.open(src).convert("RGB")
    img = img.resize((width, height), Image.LANCZOS)
    img.save(dest)
    return dest


def download_input(src: Path, subject: str) -> Path:
    out = INPUT_ROOT / subject / src.name
    return upscale_input(src, out)


def prompt_variants(base_prompt: str) -> Iterable[tuple[str, str, str]]:
    for style in STYLES:
        prompt = f"{base_prompt}\n\n{style['extra']}"
        yield style["key"], style["label"], prompt


def main() -> None:
    token = TOKEN_FILE.read_text(encoding="utf-8").strip()
    client = InferenceClient(token=token, model=MODEL)
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    INPUT_ROOT.mkdir(parents=True, exist_ok=True)

    results = []
    for source in SOURCES:
        subject_dir = OUT_ROOT / source["id"]
        subject_dir.mkdir(parents=True, exist_ok=True)
        input_img = download_input(source["src"], source["id"])
        src_rel = input_img.relative_to(ROOT).as_posix()
        log(f"source={source['title']} input={input_img}")
        variant_rows = []
        for idx, (key, label, prompt) in enumerate(prompt_variants(source["base_prompt"]), start=1):
            out_path = subject_dir / f"{idx:02d}_{key}.png"
            if out_path.exists() and out_path.stat().st_size > 0:
                log(f"skip existing {out_path}")
                variant_rows.append({"key": key, "label": label, "img_rel": out_path.relative_to(ROOT).as_posix(), "prompt": prompt})
                continue
            for attempt in range(1, 4):
                try:
                    log(f"gen {source['title']} / {label} attempt {attempt}")
                    img = client.image_to_image(
                        image=input_img,
                        prompt=prompt,
                        negative_prompt=NEGATIVE,
                        num_inference_steps=24,
                        guidance_scale=4.5,
                        target_size=TARGET_SIZE,
                    )
                    img.save(out_path)
                    log(f"saved {out_path} ({out_path.stat().st_size} bytes)")
                    variant_rows.append({"key": key, "label": label, "img_rel": out_path.relative_to(ROOT).as_posix(), "prompt": prompt})
                    break
                except Exception as e:
                    log(f"error {source['title']} / {label} attempt {attempt}: {e}")
                    if attempt == 3:
                        raise
                    time.sleep(5)
        results.append({"title": source["title"], "src_rel": src_rel, "variants": variant_rows})

    PROMPT_JSON.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    build_html(results)
    log(f"wrote {HTML_OUT}")


def build_html(results: list[dict]) -> None:
    sections = []
    for block in results:
        cards = [f'''<div class="card orig"><div class="label">Upscaled input</div><img src="{block['src_rel']}" alt="{block['title']} source"></div>''']
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
<title>Flux Kontext Wappen-Varianten</title>
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
.card img {{ display:block; width:100%; aspect-ratio:5/6; object-fit:contain; background:#0b0d12; }}
.prompt {{ padding:10px 12px 12px; color:#aab4ca; font-size:.76rem; line-height:1.35; border-top:1px solid #23293a; }}
footer {{ padding:18px 24px 30px; color:#788; font-size:.8rem; border-top:1px solid #23293a; }}
code {{ color:#a8c7ff; }}
</style>
</head>
<body>
<header>
  <h1>Flux Kontext Wappen-Varianten</h1>
  <div class="sub">Das sind echte prompt-basierte i2i-Generationen mit FLUX.1-Kontext-dev über Hugging Face Inference — keine Filter, keine nachträglichen Bildtricks. Jede Variante hat einen eigenen Prompt und wird direkt aus dem Original-Wappen abgeleitet.</div>
</header>
<main>
{''.join(sections)}
</main>
<footer>
  Öffnen: <code>file:///F:/tiroltourismus/wappen/flux_kontext_variants.html</code>
</footer>
</body>
</html>'''
    HTML_OUT.write_text(html, encoding="utf-8")


if __name__ == "__main__":
    main()

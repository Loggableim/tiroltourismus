#!/usr/bin/env python3
from __future__ import annotations

import json
import time
from pathlib import Path

import torch
from PIL import Image
from huggingface_hub import hf_hub_download
from diffusers import StableDiffusionPipeline, StableDiffusionImg2ImgPipeline

ROOT = Path(r"F:/tiroltourismus/wappen")
MODEL_DIR = ROOT / "models" / "sd15_single"
MODEL_FILE = MODEL_DIR / "v1-5-pruned-emaonly.safetensors"
CONFIG_FILE = MODEL_DIR / "v1-inference.yaml"
OUT_ROOT = ROOT / "img" / "sd15_prompt_variants"
INPUT_ROOT = ROOT / "img" / "sd15_inputs"
HTML_OUT = ROOT / "sd15_prompt_variants.html"
PROMPT_JSON = ROOT / "sd15_prompt_variants.json"
REPO = "runwayml/stable-diffusion-v1-5"

SOURCES = [
    {
        "id": "innsbruck",
        "title": "Innsbruck",
        "src": ROOT / "img" / "orte" / "statutarstadt_innsbruck" / "stadtwappen.png",
        "base_prompt": (
            "A complete redesign of the Innsbruck city coat of arms as a premium heraldic emblem. "
            "Keep the vertical shield format and ceremonial dignity, but reimagine it as a modern, creative civic symbol. "
            "The result should feel like a new logo / art print, not a copied illustration."
        ),
    },
    {
        "id": "kitzbuehel",
        "title": "Kitzbühel",
        "src": ROOT / "img" / "orte" / "kitzbühel" / "kitzbühel.png",
        "base_prompt": (
            "A complete redesign of the Kitzbühel coat of arms as a premium heraldic emblem. "
            "Keep the vertical shield format and ceremonial dignity, but reimagine it as a modern, creative alpine symbol. "
            "The result should feel like a new logo / art print, not a copied illustration."
        ),
    },
]

STYLES = [
    ("modern_badge", "Modern Badge", "modern civic badge, crisp vector geometry, refined negative space, premium municipal branding, clean edges, balanced symmetry"),
    ("stained_glass", "Stained Glass", "stained glass heraldry, luminous panes, leaded outlines, jewel tones, cathedral atmosphere, artistic and radiant"),
    ("kintsugi", "Kintsugi", "kintsugi crest, cracked porcelain repaired with gold seams, dark lacquer, elegant craft object, precious and symbolic"),
    ("topographic", "Topographic", "alpine topographic emblem, contour lines, mountain cartography, technical linework, outdoor-brand aesthetic, clean and smart"),
    ("riso_poster", "Riso Poster", "risograph poster print, limited ink palette, slight misregistration, paper texture, bold graphic energy, contemporary art print"),
    ("brutalist_shield", "Brutalist Shield", "brutalist angular shield, carved planes, sharp cuts, architectural mass, powerful shadow shapes, abstract and monumental"),
    ("celestial_seal", "Celestial Seal", "celestial compass seal, orbit rings, star geometry, navigational symbolism, elegant badge, mysterious and polished"),
    ("paper_collage", "Paper Collage", "cut-paper collage, layered torn paper, mixed-media fragments, tactile poster composition, handmade but clean, modern editorial design"),
]

NEGATIVE = "photo, realistic, 3d render, landscape, background scene, people, text, watermark, blurry, low quality, messy, extra symbols, extra shields, clutter"
WIDTH = 576
HEIGHT = 720
NUM_STEPS = 24
GUIDANCE = 7.0
STRENGTH = 0.78


def log(msg: str) -> None:
    print(msg, flush=True)


def ensure_config() -> Path:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    if not CONFIG_FILE.exists():
        config_url = "https://raw.githubusercontent.com/CompVis/stable-diffusion/main/configs/stable-diffusion/v1-inference.yaml"
        import requests
        r = requests.get(config_url, timeout=60)
        r.raise_for_status()
        CONFIG_FILE.write_text(r.text, encoding="utf-8")
    return CONFIG_FILE


def download_model() -> Path:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    if not MODEL_FILE.exists() or MODEL_FILE.stat().st_size == 0:
        log(f"downloading {REPO} single-file checkpoint")
        hf_hub_download(
            repo_id=REPO,
            filename="v1-5-pruned-emaonly.safetensors",
            local_dir=str(MODEL_DIR),
            local_dir_use_symlinks=False,
        )
    return MODEL_FILE


def prepare_input(src: Path, subject: str) -> Path:
    out = INPUT_ROOT / subject / src.name
    out.parent.mkdir(parents=True, exist_ok=True)
    img = Image.open(src).convert("RGB")
    img = img.resize((WIDTH, HEIGHT), Image.LANCZOS)
    img.save(out)
    return out


def load_pipe() -> StableDiffusionImg2ImgPipeline:
    ensure_config()
    download_model()
    base = StableDiffusionPipeline.from_single_file(
        str(MODEL_FILE),
        original_config_file=str(CONFIG_FILE),
        torch_dtype=torch.float16,
        safety_checker=None,
        requires_safety_checker=False,
    )
    pipe = StableDiffusionImg2ImgPipeline.from_pipe(base)
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
            if out_path.exists() and out_path.stat().st_size > 0:
                log(f"skip existing {out_path}")
                variants.append({"key": key, "label": label, "img_rel": out_path.relative_to(ROOT).as_posix()})
                continue
            prompt = f"{source['base_prompt']} Style direction: {extra}. No text, no watermark, no background scene."
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
                    variants.append({"key": key, "label": label, "img_rel": out_path.relative_to(ROOT).as_posix()})
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
            cards.append(f'''<div class="card"><div class="label">{var['label']}</div><img src="{var['img_rel']}" alt="{block['title']} {var['label']}"></div>''')
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
<title>SD1.5 Prompt Wappen-Varianten</title>
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
footer {{ padding:18px 24px 30px; color:#788; font-size:.8rem; border-top:1px solid #23293a; }}
code {{ color:#a8c7ff; }}
</style>
</head>
<body>
<header>
  <h1>SD1.5 Prompt-Varianten für Wappen</h1>
  <div class="sub">Echte prompt-basierte img2img-Generierung auf lokalem GPU-Stack mit Stable Diffusion 1.5. Keine Filter, keine nachträgliche Bildbearbeitung — jede Variante kommt direkt aus dem Modell und einem eigenen Prompt.</div>
</header>
<main>
{''.join(sections)}
</main>
<footer>
  Öffnen: <code>file:///F:/tiroltourismus/wappen/sd15_prompt_variants.html</code>
</footer>
</body>
</html>'''
    HTML_OUT.write_text(html, encoding="utf-8")


if __name__ == "__main__":
    main()

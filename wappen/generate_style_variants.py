#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageFilter, ImageOps, ImageEnhance, ImageDraw, ImageChops

ROOT = Path(r"F:/tiroltourismus/wappen")
SRC = ROOT / "img" / "orte" / "statutarstadt_innsbruck" / "stadtwappen.png"
OUT_DIR = ROOT / "img" / "style_variants"
HTML_OUT = ROOT / "style_variants.html"


def log(msg: str) -> None:
    print(msg, flush=True)


def fit_canvas(img: Image.Image, size=(320, 384)) -> Image.Image:
    canvas = Image.new("RGBA", size, (11, 13, 18, 255))
    bg = img.convert("RGBA")
    bg.thumbnail((size[0] - 24, size[1] - 24), Image.LANCZOS)
    x = (size[0] - bg.width) // 2
    y = (size[1] - bg.height) // 2
    canvas.alpha_composite(bg, (x, y))
    return canvas.convert("RGB")


def add_frame(img: Image.Image, color=(30, 34, 46)) -> Image.Image:
    framed = ImageOps.expand(img, border=10, fill=color)
    framed = ImageOps.expand(framed, border=2, fill=(80, 86, 104))
    return framed


def style_flat(src: Image.Image) -> Image.Image:
    img = src.convert("RGB").resize((900, 1080), Image.LANCZOS)
    img = ImageEnhance.Color(img).enhance(1.35)
    img = ImageEnhance.Contrast(img).enhance(1.45)
    img = img.filter(ImageFilter.EDGE_ENHANCE_MORE)
    img = ImageOps.posterize(img, 3)
    img = ImageOps.autocontrast(img)
    img = ImageOps.colorize(ImageOps.grayscale(img), black="#1a1a1a", white="#f4d06f")
    # bring back some red accents by masking strong tones from original
    orig = src.convert("RGB").resize(img.size, Image.LANCZOS)
    r, g, b = orig.split()
    red_mask = Image.eval(r, lambda p: 255 if p > 120 else 0)
    red_layer = Image.new("RGB", img.size, "#b32025")
    img = Image.composite(red_layer, img, red_mask)
    img = ImageEnhance.Sharpness(img).enhance(2.2)
    return fit_canvas(add_frame(img, (22, 26, 38)))


def style_engraved(src: Image.Image) -> Image.Image:
    img = src.convert("L").resize((900, 1080), Image.LANCZOS)
    img = ImageEnhance.Contrast(img).enhance(1.8)
    img = img.filter(ImageFilter.EDGE_ENHANCE_MORE)
    img = img.filter(ImageFilter.EMBOSS)
    img = ImageEnhance.Contrast(img).enhance(1.25)
    img = ImageOps.colorize(img, black="#26160f", white="#f2dfc4")
    # subtle parchment vignette
    vignette = Image.new("L", img.size, 0)
    d = ImageDraw.Draw(vignette)
    d.ellipse((-180, -220, img.size[0] + 180, img.size[1] + 220), fill=255)
    vignette = vignette.filter(ImageFilter.GaussianBlur(120))
    parchment = Image.new("RGB", img.size, "#c8ad7f")
    img = Image.composite(img, parchment, vignette)
    img = ImageEnhance.Sharpness(img).enhance(1.6)
    return fit_canvas(add_frame(img, (43, 31, 24)))


def style_modern(src: Image.Image) -> Image.Image:
    img = src.convert("RGB").resize((900, 1080), Image.LANCZOS)
    img = ImageEnhance.Sharpness(img).enhance(0.9)
    img = ImageEnhance.Color(img).enhance(0.7)
    img = ImageEnhance.Contrast(img).enhance(1.25)
    img = ImageOps.posterize(img, 4)
    img = img.filter(ImageFilter.SMOOTH_MORE)
    # isolate darker edges for a crisp emblem look
    gray = ImageOps.grayscale(img)
    edges = gray.filter(ImageFilter.FIND_EDGES)
    edges = ImageEnhance.Contrast(edges).enhance(2.5)
    ink = ImageOps.colorize(edges, black="#0f1117", white="#2a3245")
    base = Image.new("RGB", img.size, "#f5f4ef")
    img = Image.blend(base, img, 0.78)
    img = Image.blend(img, ink, 0.18)
    img = ImageOps.colorize(ImageOps.grayscale(img), black="#203047", white="#f0e7d7")
    return fit_canvas(add_frame(img, (17, 21, 29)))


def build_html(paths: list[tuple[str, str, Path]]) -> None:
    cards = [f'''<article class="card"><h2>Original</h2><img src="{SRC.as_posix().split('F:/tiroltourismus/wappen/',1)[-1]}" alt="Original"><p>Ausgangsbild</p></article>''']
    for label, sub, path in paths:
        cards.append(f'''<article class="card"><h2>{label}</h2><img src="img/style_variants/{path.name}" alt="{label}"><p>{sub}</p></article>''')
    html = f'''<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>3 Wappen-Varianten</title>
<style>
:root {{ color-scheme: dark; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif; background:#0b0d12; color:#eee; }}
header {{ padding:20px 24px; background:linear-gradient(135deg,#151922,#0d1016); border-bottom:1px solid #23293a; position:sticky; top:0; z-index:5; }}
h1 {{ margin:0 0 8px; font-size:1.4rem; }}
.sub {{ color:#9aa3b2; font-size:.92rem; }}
main {{ padding:18px 24px; display:grid; grid-template-columns:repeat(auto-fit,minmax(260px,1fr)); gap:16px; }}
.card {{ background:#121621; border:1px solid #23293a; border-radius:14px; overflow:hidden; }}
.card h2 {{ margin:0; padding:12px 14px; border-bottom:1px solid #23293a; font-size:1rem; }}
.card img {{ display:block; width:100%; background:#0b0d12; }}
.card p {{ margin:0; padding:10px 14px; color:#8b93a7; font-size:.8rem; }}
footer {{ padding:18px 24px 30px; color:#788; font-size:.8rem; border-top:1px solid #23293a; }}
a {{ color:#7cb7ff; }}
</style>
</head>
<body>
<header>
  <h1>3 Stilvarianten eines Wappens</h1>
  <div class="sub">Ausgang: Innsbruck Stadtwappen · Wähle eine Stilrichtung für die komplette Tirol-Serie.</div>
</header>
<main>
{''.join(cards)}
</main>
<footer>
  Öffne die Vergleichsseite: <code>file:///F:/tiroltourismus/wappen/style_variants.html</code>
</footer>
</body>
</html>'''
    HTML_OUT.write_text(html, encoding='utf-8')


def main() -> None:
    if not SRC.exists():
        raise FileNotFoundError(SRC)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    src = Image.open(SRC).convert("RGB")
    variants = [
        ("Heraldic Bold", "flat, high-contrast, thicker outlines", style_flat(src)),
        ("Engraved Seal", "vintage etched, parchment feel", style_engraved(src)),
        ("Modern Badge", "minimal, clean, contemporary", style_modern(src)),
    ]
    results = []
    for label, desc, img in variants:
        out = OUT_DIR / f"{label.lower().replace(' ', '_')}.png"
        img.save(out)
        results.append((label, desc, out))
        log(f"saved {out}")
    build_html(results)
    log(f"wrote {HTML_OUT}")


if __name__ == '__main__':
    main()

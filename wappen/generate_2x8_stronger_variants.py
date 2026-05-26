#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageOps, ImageEnhance, ImageFilter, ImageDraw, ImageChops

ROOT = Path(r"F:/tiroltourismus/wappen")
OUT_DIR = ROOT / "img" / "two_wappen_variants_strong"
HTML_OUT = ROOT / "two_wappen_variants_strong.html"

SETS = [
    {
        "id": "innsbruck",
        "title": "Innsbruck Stadtwappen",
        "src": ROOT / "img" / "orte" / "statutarstadt_innsbruck" / "stadtwappen.png",
    },
    {
        "id": "kitzbuehel",
        "title": "Kitzbühel Wappen",
        "src": ROOT / "img" / "orte" / "kitzbühel" / "kitzbühel.png",
    },
]


# --- helpers -----------------------------------------------------

def fit_canvas(img: Image.Image, size=(360, 432), bg=(11, 13, 18)) -> Image.Image:
    canvas = Image.new("RGBA", size, (*bg, 255))
    inner = img.convert("RGBA")
    inner.thumbnail((size[0] - 24, size[1] - 24), Image.LANCZOS)
    x = (size[0] - inner.width) // 2
    y = (size[1] - inner.height) // 2
    canvas.alpha_composite(inner, (x, y))
    return canvas.convert("RGB")


def frame(img: Image.Image, inner=(22, 26, 36), outer=(84, 92, 112)) -> Image.Image:
    return ImageOps.expand(ImageOps.expand(img, 8, fill=inner), 2, fill=outer)


def grid_overlay(img: Image.Image, color=(255, 255, 255), alpha=14, step=16) -> Image.Image:
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    w, h = img.size
    for x in range(0, w, step):
        d.line((x, 0, x, h), fill=(*color, alpha), width=1)
    for y in range(0, h, step):
        d.line((0, y, w, y), fill=(*color, alpha), width=1)
    return Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB")


def vignette(img: Image.Image, strength=120) -> Image.Image:
    mask = Image.new("L", img.size, 0)
    d = ImageDraw.Draw(mask)
    d.ellipse((-180, -220, img.size[0] + 180, img.size[1] + 220), fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(strength))
    bg = Image.new("RGB", img.size, "#10131a")
    return Image.composite(img, bg, mask)


def posterize_tonal(img: Image.Image, levels: int) -> Image.Image:
    return ImageOps.posterize(img, levels)


def extract_edges(src: Image.Image, contrast=2.5) -> Image.Image:
    gray = ImageOps.grayscale(src)
    edges = gray.filter(ImageFilter.FIND_EDGES)
    edges = ImageEnhance.Contrast(edges).enhance(contrast)
    return edges


def scaled(src: Image.Image, size=(980, 1176)) -> Image.Image:
    return src.convert("RGB").resize(size, Image.LANCZOS)


# --- style functions --------------------------------------------

def style_neo_heraldic(src: Image.Image) -> Image.Image:
    img = scaled(src)
    img = ImageEnhance.Color(img).enhance(1.05)
    img = ImageEnhance.Contrast(img).enhance(1.65)
    img = posterize_tonal(img, 3)
    edges = extract_edges(img, 3.0)
    ink = ImageOps.colorize(edges, black="#10131a", white="#f1c24d")
    base = Image.new("RGB", img.size, "#f6f3ee")
    img = Image.blend(base, img, 0.42)
    img = Image.blend(img, ink, 0.38)
    # hard crop / badge feel
    mask = Image.new("L", img.size, 0)
    d = ImageDraw.Draw(mask)
    w, h = img.size
    d.rounded_rectangle((70, 40, w - 70, h - 40), radius=90, fill=255)
    img = Image.composite(img, Image.new("RGB", img.size, "#11131a"), mask)
    img = fit_canvas(frame(img, (18, 22, 31), (92, 72, 22)), bg=(17, 20, 28))
    return img


def style_minimal_monoline(src: Image.Image) -> Image.Image:
    img = scaled(src)
    gray = ImageOps.grayscale(img)
    edges = gray.filter(ImageFilter.FIND_EDGES)
    edges = ImageEnhance.Contrast(edges).enhance(3.2)
    # mostly white background, thin dark lines, a single red accent
    line = ImageOps.colorize(edges, black="#111111", white="#f7f7f2")
    accent_mask = gray.point(lambda p: 255 if p > 150 else 0)
    accent = Image.new("RGB", img.size, "#bf1d2d")
    line = Image.composite(accent, line, accent_mask)
    line = ImageEnhance.Sharpness(line).enhance(1.7)
    line = ImageOps.autocontrast(line)
    line = grid_overlay(line, color=(255,255,255), alpha=4, step=28)
    line = fit_canvas(frame(line, (250, 248, 242), (130, 130, 130)), bg=(248, 247, 242))
    return line


def style_duotone_red_gold(src: Image.Image) -> Image.Image:
    img = scaled(src)
    img = ImageEnhance.Color(img).enhance(0.55)
    img = ImageEnhance.Contrast(img).enhance(1.45)
    gray = ImageOps.grayscale(img)
    gray = ImageEnhance.Contrast(gray).enhance(2.0)
    duo = ImageOps.colorize(gray, black="#6a0f16", white="#f2cf74")
    duo = ImageEnhance.Sharpness(duo).enhance(1.5)
    duo = vignette(duo, 80)
    return fit_canvas(frame(duo, (17, 14, 18), (140, 103, 36)))


def style_duotone_blue_silver(src: Image.Image) -> Image.Image:
    img = scaled(src)
    img = ImageEnhance.Color(img).enhance(0.5)
    img = ImageEnhance.Contrast(img).enhance(1.5)
    gray = ImageOps.grayscale(img)
    gray = ImageEnhance.Contrast(gray).enhance(2.1)
    duo = ImageOps.colorize(gray, black="#10243f", white="#dfe7f1")
    duo = ImageEnhance.Sharpness(duo).enhance(1.4)
    duo = ImageOps.posterize(duo, 4)
    return fit_canvas(frame(duo, (14, 20, 34), (88, 106, 128)))


def style_abstract_cutout(src: Image.Image) -> Image.Image:
    img = scaled(src)
    img = ImageEnhance.Color(img).enhance(0.75)
    img = ImageEnhance.Contrast(img).enhance(1.75)
    img = ImageOps.posterize(img, 3)
    img = ImageOps.autocontrast(img)
    # create strong geometric overlays so it doesn't look like the original
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    w, h = img.size
    d.polygon([(0, 0), (w*0.62, 0), (w*0.42, h*0.42), (0, h*0.25)], fill=(8, 12, 18, 110))
    d.polygon([(w*0.58, h*0.08), (w, 0), (w, h*0.36)], fill=(192, 30, 45, 95))
    d.polygon([(0, h*0.76), (w*0.48, h*0.56), (w*0.82, h), (0, h)], fill=(255, 208, 92, 78))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    img = grid_overlay(img, color=(255,255,255), alpha=10, step=20)
    img = vignette(img, 85)
    return fit_canvas(frame(img, (16, 18, 25), (72, 80, 96)))


def style_dark_premium(src: Image.Image) -> Image.Image:
    img = scaled(src)
    img = ImageEnhance.Color(img).enhance(0.9)
    img = ImageEnhance.Contrast(img).enhance(1.85)
    img = ImageEnhance.Sharpness(img).enhance(1.3)
    gray = extract_edges(img, 2.8)
    gold = ImageOps.colorize(gray, black="#07090d", white="#d5af4a")
    bg = Image.new("RGB", img.size, "#090b10")
    img = Image.blend(bg, gold, 0.72)
    img = grid_overlay(img, color=(255, 215, 120), alpha=8, step=40)
    return fit_canvas(frame(img, (8, 10, 15), (183, 146, 52)))


def style_stencil_symbol(src: Image.Image) -> Image.Image:
    img = scaled(src)
    gray = ImageOps.grayscale(img)
    # turn into hard binary-ish silhouette
    bw = gray.point(lambda p: 255 if p > 138 else 0)
    bw = ImageEnhance.Contrast(bw).enhance(2.0)
    bw = ImageOps.colorize(bw, black="#0d1117", white="#f0f0ea")
    bw = ImageEnhance.Sharpness(bw).enhance(1.2)
    bw = ImageOps.posterize(bw, 2)
    # add one accent block like a modern logo
    overlay = Image.new("RGBA", bw.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    w, h = bw.size
    d.rectangle((w*0.08, h*0.08, w*0.92, h*0.22), fill=(180, 32, 42, 120))
    d.rectangle((w*0.12, h*0.78, w*0.88, h*0.9), fill=(241, 196, 88, 95))
    bw = Image.alpha_composite(bw.convert("RGBA"), overlay).convert("RGB")
    return fit_canvas(frame(bw, (240, 240, 236), (120, 120, 120)), bg=(244, 243, 239))


STYLE_FUNCS = [
    ("neo_heraldic", "Neo Heraldic", style_neo_heraldic),
    ("minimal_monoline", "Minimal Monoline", style_minimal_monoline),
    ("duotone_red_gold", "Duotone Red/Gold", style_duotone_red_gold),
    ("duotone_blue_silver", "Duotone Blue/Silver", style_duotone_blue_silver),
    ("abstract_cutout", "Abstract Cutout", style_abstract_cutout),
    ("dark_premium", "Dark Premium", style_dark_premium),
    ("stencil_symbol", "Stencil Symbol", style_stencil_symbol),
]


def build_html(blocks: list[dict]) -> None:
    section_html = []
    for block in blocks:
        cards = []
        cards.append(f'''<div class="card orig"><div class="label">Original</div><img src="{block['src_rel']}" alt="{block['title']} original"></div>''')
        for var in block['variants']:
            cards.append(f'''<div class="card"><div class="label">{var['label']}</div><img src="{var['img_rel']}" alt="{block['title']} {var['label']}"></div>''')
        section_html.append(f'''
        <section class="block">
          <h2>{block['title']}</h2>
          <div class="grid">{''.join(cards)}</div>
        </section>''')

    html = f'''<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>2 Wappen – noch stärkere Varianten</title>
<style>
:root {{ color-scheme: dark; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif; background:#0b0d12; color:#eee; }}
header {{ padding:20px 24px; background:linear-gradient(135deg,#151922,#0d1016); border-bottom:1px solid #23293a; position:sticky; top:0; z-index:5; }}
h1 {{ margin:0 0 8px; font-size:1.4rem; }}
.sub {{ color:#9aa3b2; font-size:.92rem; }}
main {{ padding:18px 24px 30px; }}
.block {{ margin-bottom:30px; }}
.block h2 {{ margin:0 0 14px; padding-bottom:8px; border-bottom:1px solid #23293a; font-size:1.15rem; }}
.grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:14px; }}
.card {{ background:#121621; border:1px solid #23293a; border-radius:14px; overflow:hidden; }}
.card.orig {{ border-color:#334; }}
.label {{ padding:10px 12px; font-size:.74rem; text-transform:uppercase; letter-spacing:.06em; color:#97a1b7; border-bottom:1px solid #23293a; background:#171b26; }}
.card img {{ display:block; width:100%; aspect-ratio:5/6; object-fit:contain; background:#0b0d12; }}
footer {{ padding:18px 24px 30px; color:#788; font-size:.8rem; border-top:1px solid #23293a; }}
code {{ color:#a8c7ff; }}
</style>
</head>
<body>
<header>
  <h1>2 Wappen – mehr Distanz zum Original</h1>
  <div class="sub">Die Varianten sind absichtlich stärker verändert: mehr Abstraktion, härtere Farbbrüche, mehr Logo-/Emblem-Charakter.</div>
</header>
<main>
{''.join(section_html)}
</main>
<footer>Öffnen: <code>file:///F:/tiroltourismus/wappen/two_wappen_six_variants.html</code> · Neue Variante: <code>file:///F:/tiroltourismus/wappen/two_wappen_variants_strong.html</code></footer>
</body>
</html>'''
    HTML_OUT.write_text(html, encoding='utf-8')


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    blocks = []
    for spec in SETS:
        src = spec['src']
        if not src.exists():
            raise FileNotFoundError(src)
        src_img = Image.open(src).convert('RGB')
        src_rel = src.relative_to(ROOT).as_posix()
        variants = []
        for key, label, func in STYLE_FUNCS:
            out_dir = OUT_DIR / spec['id']
            out_dir.mkdir(parents=True, exist_ok=True)
            out = out_dir / f'{key}.png'
            func(src_img).save(out)
            variants.append({'label': label, 'img_rel': out.relative_to(ROOT).as_posix()})
        blocks.append({'title': spec['title'], 'src_rel': src_rel, 'variants': variants})
    build_html(blocks)
    print(f'wrote {HTML_OUT}')
    print(f'images: {sum(1 for p in OUT_DIR.rglob("*.png"))}')


if __name__ == '__main__':
    main()

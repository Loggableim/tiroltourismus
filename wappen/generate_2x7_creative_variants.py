#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageOps, ImageEnhance, ImageFilter, ImageDraw, ImageChops

ROOT = Path(r"F:/tiroltourismus/wappen")
OUT_DIR = ROOT / "img" / "two_wappen_variants_creative"
HTML_OUT = ROOT / "two_wappen_variants_creative.html"

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


def fit_canvas(img: Image.Image, size=(360, 432), bg=(11, 13, 18)) -> Image.Image:
    canvas = Image.new("RGBA", size, (*bg, 255))
    inner = img.convert("RGBA")
    inner.thumbnail((size[0] - 24, size[1] - 24), Image.LANCZOS)
    x = (size[0] - inner.width) // 2
    y = (size[1] - inner.height) // 2
    canvas.alpha_composite(inner, (x, y))
    return canvas.convert("RGB")


def frame(img: Image.Image, inner=(18, 20, 28), outer=(88, 96, 114)) -> Image.Image:
    return ImageOps.expand(ImageOps.expand(img, 8, fill=inner), 2, fill=outer)


def scaled(src: Image.Image, size=(980, 1176)) -> Image.Image:
    return src.convert("RGB").resize(size, Image.LANCZOS)


def grid_overlay(img: Image.Image, color=(255, 255, 255), alpha=16, step=18) -> Image.Image:
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    w, h = img.size
    for x in range(0, w, step):
        d.line((x, 0, x, h), fill=(*color, alpha), width=1)
    for y in range(0, h, step):
        d.line((0, y, w, y), fill=(*color, alpha), width=1)
    return Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB")


def vignette(img: Image.Image, strength=110) -> Image.Image:
    mask = Image.new("L", img.size, 0)
    d = ImageDraw.Draw(mask)
    d.ellipse((-200, -240, img.size[0] + 200, img.size[1] + 240), fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(strength))
    return Image.composite(img, Image.new("RGB", img.size, "#0b0d12"), mask)


def mask_blend(base: Image.Image, overlay: Image.Image, mask: Image.Image) -> Image.Image:
    return Image.composite(overlay, base, mask)


def edge_img(src: Image.Image, contrast=2.5) -> Image.Image:
    g = ImageOps.grayscale(src)
    e = g.filter(ImageFilter.FIND_EDGES)
    e = ImageEnhance.Contrast(e).enhance(contrast)
    return e


def style_prism_cut(src: Image.Image) -> Image.Image:
    img = scaled(src)
    e = edge_img(img, 3.0)
    base = ImageOps.colorize(e, black="#141a28", white="#f1f4ff")
    base = ImageEnhance.Color(base).enhance(0.65)
    w, h = base.size
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    d.polygon([(0, 0), (w * 0.42, 0), (w * 0.58, h * 0.36), (0, h * 0.28)], fill=(26, 86, 255, 110))
    d.polygon([(w * 0.58, 0), (w, 0), (w, h * 0.42), (w * 0.72, h * 0.26)], fill=(242, 94, 77, 105))
    d.polygon([(0, h * 0.70), (w * 0.36, h * 0.50), (w * 0.70, h), (0, h)], fill=(240, 196, 65, 90))
    base = Image.alpha_composite(base.convert("RGBA"), overlay).convert("RGB")
    base = ImageOps.posterize(base, 3)
    base = grid_overlay(base, alpha=8, step=24)
    return fit_canvas(frame(vignette(base, 90), (12, 16, 26), (70, 90, 136)))


def style_halftone_pop(src: Image.Image) -> Image.Image:
    img = scaled(src)
    gray = ImageOps.grayscale(img)
    # halftone dot simulation by pixelation + contrast
    small = gray.resize((120, 144), Image.NEAREST)
    small = ImageEnhance.Contrast(small).enhance(2.3)
    small = ImageOps.autocontrast(small)
    tone = ImageOps.colorize(small, black="#0c0f15", white="#f9f1e1")
    tone = ImageEnhance.Color(tone).enhance(0.8)
    w, h = tone.size
    layer = Image.new("RGBA", tone.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for y in range(0, h, 24):
        for x in range(0, w, 24):
            r = 4 + ((x + y) // 24) % 10
            d.ellipse((x, y, x + r * 2, y + r * 2), fill=(182, 32, 42, 95))
    tone = Image.alpha_composite(tone.convert("RGBA"), layer).convert("RGB")
    tone = ImageOps.posterize(tone, 3)
    return fit_canvas(frame(tone, (24, 18, 20), (120, 64, 70)))


def style_geo_layers(src: Image.Image) -> Image.Image:
    img = scaled(src)
    img = ImageEnhance.Color(img).enhance(0.55)
    img = ImageEnhance.Contrast(img).enhance(1.7)
    gray = ImageOps.grayscale(img)
    base = ImageOps.colorize(gray, black="#101826", white="#e9eef5")
    w, h = base.size
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.polygon([(0, h * 0.15), (w * 0.46, 0), (w * 0.65, h * 0.34), (w * 0.24, h * 0.48)], fill=(19, 102, 150, 120))
    d.polygon([(w * 0.35, h * 0.46), (w, h * 0.10), (w, h * 0.6), (w * 0.62, h * 0.76)], fill=(189, 24, 47, 108))
    d.polygon([(0, h * 0.72), (w * 0.52, h * 0.58), (w, h), (0, h)], fill=(231, 189, 55, 104))
    base = Image.alpha_composite(base.convert("RGBA"), layer).convert("RGB")
    base = ImageChops.screen(base, Image.new("RGB", base.size, "#11131a"))
    base = ImageOps.posterize(base, 4)
    return fit_canvas(frame(base, (13, 19, 27), (73, 103, 136)))


def style_riso_duo(src: Image.Image) -> Image.Image:
    img = scaled(src)
    img = ImageEnhance.Contrast(img).enhance(1.6)
    img = ImageOps.posterize(img, 2)
    g = ImageOps.grayscale(img)
    g = ImageEnhance.Contrast(g).enhance(2.0)
    red = ImageOps.colorize(g, black="#2b0f16", white="#e73d4b")
    gold = ImageOps.colorize(g, black="#2d2106", white="#f4c84f")
    # split into two diagonally blended color plates
    mask = Image.new("L", img.size, 0)
    d = ImageDraw.Draw(mask)
    d.polygon([(0, 0), (img.size[0], 0), (0, img.size[1])], fill=255)
    duo = Image.composite(red, gold, mask)
    duo = Image.blend(duo, img, 0.18)
    duo = grid_overlay(duo, alpha=10, step=32)
    return fit_canvas(frame(duo, (26, 14, 18), (154, 72, 80)))


def style_paper_collage(src: Image.Image) -> Image.Image:
    img = scaled(src)
    gray = ImageOps.grayscale(img)
    mask = gray.point(lambda p: 255 if p > 128 else 0)
    cut = ImageOps.colorize(mask, black="#ead9bf", white="#20242d")
    paper = Image.new("RGB", img.size, "#f7f0e4")
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    w, h = img.size
    d.polygon([(w*0.06, h*0.03), (w*0.78, h*0.10), (w*0.62, h*0.72), (w*0.12, h*0.58)], fill=(187, 162, 120, 118))
    d.polygon([(w*0.34, h*0.20), (w*0.96, h*0.18), (w*0.86, h*0.92), (w*0.42, h*0.76)], fill=(72, 84, 104, 88))
    collage = Image.alpha_composite(paper.convert("RGBA"), layer).convert("RGB")
    collage = Image.blend(collage, cut, 0.46)
    collage = ImageEnhance.Contrast(collage).enhance(1.25)
    collage = ImageOps.posterize(collage, 3)
    collage = vignette(collage, 100)
    return fit_canvas(frame(collage, (40, 34, 28), (118, 105, 84)), bg=(245, 239, 229))


def style_signal_ink(src: Image.Image) -> Image.Image:
    img = scaled(src)
    gray = ImageOps.grayscale(img)
    edges = gray.filter(ImageFilter.FIND_EDGES)
    edges = ImageEnhance.Contrast(edges).enhance(3.0)
    line = ImageOps.colorize(edges, black="#09101d", white="#dfe8f2")
    w, h = line.size
    layer = Image.new("RGBA", line.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.rectangle((0, h*0.12, w, h*0.18), fill=(41, 161, 255, 95))
    d.rectangle((0, h*0.78, w, h*0.84), fill=(239, 68, 68, 88))
    d.polygon([(w*0.67, 0), (w, 0), (w, h*0.48)], fill=(250, 204, 21, 72))
    line = Image.alpha_composite(line.convert("RGBA"), layer).convert("RGB")
    line = ImageOps.posterize(line, 3)
    line = ImageEnhance.Sharpness(line).enhance(1.5)
    return fit_canvas(frame(line, (10, 14, 24), (74, 110, 180)))


def style_mask_silhouette(src: Image.Image) -> Image.Image:
    img = scaled(src)
    g = ImageOps.grayscale(img)
    bw = g.point(lambda p: 255 if p > 140 else 0)
    bw = ImageEnhance.Contrast(bw).enhance(2.5)
    bw = ImageOps.colorize(bw, black="#111111", white="#f7f6f0")
    # hard abstract cut using large blocks
    layer = Image.new("RGBA", bw.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    w, h = bw.size
    d.rectangle((w*0.05, h*0.05, w*0.36, h*0.92), fill=(190, 27, 43, 114))
    d.rectangle((w*0.64, h*0.05, w*0.92, h*0.95), fill=(245, 198, 72, 92))
    bw = Image.alpha_composite(bw.convert("RGBA"), layer).convert("RGB")
    bw = ImageOps.posterize(bw, 2)
    return fit_canvas(frame(bw, (242, 242, 238), (118, 118, 118)), bg=(247, 246, 241))


STYLE_FUNCS = [
    ("prism_cut", "Prism Cut", style_prism_cut),
    ("halftone_pop", "Halftone Pop", style_halftone_pop),
    ("geo_layers", "Geo Layers", style_geo_layers),
    ("riso_duo", "Riso Duo", style_riso_duo),
    ("paper_collage", "Paper Collage", style_paper_collage),
    ("signal_ink", "Signal Ink", style_signal_ink),
    ("mask_silhouette", "Mask Silhouette", style_mask_silhouette),
]


def build_html(blocks: list[dict]) -> None:
    sections = []
    for block in blocks:
        cards = [f'''<div class="card orig"><div class="label">Original</div><img src="{block['src_rel']}" alt="{block['title']} original"></div>''']
        for var in block['variants']:
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
<title>2 Wappen – 7 neue kreative Varianten</title>
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
  <h1>2 Wappen – 7 kreative Stilrichtungen</h1>
  <div class="sub">Die neuen Varianten driften noch stärker vom Original weg: abstrakter, grafischer, collage-artiger und weniger wappenhaft im klassischen Sinn.</div>
</header>
<main>
{''.join(sections)}
</main>
<footer>
  Öffnen: <code>file:///F:/tiroltourismus/wappen/two_wappen_variants_creative.html</code>
</footer>
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
        out_dir = OUT_DIR / spec['id']
        out_dir.mkdir(parents=True, exist_ok=True)
        for key, label, func in STYLE_FUNCS:
            out = out_dir / f'{key}.png'
            func(src_img).save(out)
            variants.append({'label': label, 'img_rel': out.relative_to(ROOT).as_posix()})
            print(f'saved {out}', flush=True)
        blocks.append({'title': spec['title'], 'src_rel': src_rel, 'variants': variants})
    build_html(blocks)
    print(f'wrote {HTML_OUT}', flush=True)
    print(f'images: {sum(1 for p in OUT_DIR.rglob("*.png"))}', flush=True)


if __name__ == '__main__':
    main()

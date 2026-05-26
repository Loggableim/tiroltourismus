#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageOps, ImageEnhance, ImageFilter, ImageDraw, ImageChops

ROOT = Path(r"F:/tiroltourismus/wappen")
OUT_DIR = ROOT / "img" / "two_wappen_variants_experimental"
HTML_OUT = ROOT / "two_wappen_variants_experimental.html"

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


def vignette(img: Image.Image, strength=120) -> Image.Image:
    mask = Image.new("L", img.size, 0)
    d = ImageDraw.Draw(mask)
    d.ellipse((-180, -220, img.size[0] + 180, img.size[1] + 220), fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(strength))
    return Image.composite(img, Image.new("RGB", img.size, "#0b0d12"), mask)


def radial_grid(img: Image.Image, alpha=14) -> Image.Image:
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    w, h = img.size
    cx, cy = w / 2, h / 2
    # radiating lines
    for i in range(0, 360, 12):
        import math
        ang = math.radians(i)
        x = cx + math.cos(ang) * w * 0.55
        y = cy + math.sin(ang) * h * 0.55
        d.line((cx, cy, x, y), fill=(255, 255, 255, alpha), width=1)
    # concentric circles
    for r in range(40, int(min(w, h) * 0.62), 44):
        d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(255, 255, 255, alpha // 2), width=1)
    return Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB")


def glitch_bands(img: Image.Image) -> Image.Image:
    w, h = img.size
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for y in range(0, h, 96):
        d.rectangle((0, y, w, min(h, y + 18)), fill=(255, 255, 255, 26))
    for y in range(24, h, 128):
        d.rectangle((0, y, w, min(h, y + 9)), fill=(193, 29, 42, 56))
    for x in range(0, w, 118):
        d.rectangle((x, 0, min(w, x + 8), h), fill=(255, 205, 82, 22))
    return Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB")


def color_block_mask(src: Image.Image, threshold=135) -> Image.Image:
    gray = ImageOps.grayscale(src)
    bw = gray.point(lambda p: 255 if p > threshold else 0)
    return bw


def style_stained_glass(src: Image.Image) -> Image.Image:
    img = scaled(src)
    edges = ImageOps.grayscale(img).filter(ImageFilter.FIND_EDGES)
    edges = ImageEnhance.Contrast(edges).enhance(3.2)
    line = ImageOps.colorize(edges, black="#080a10", white="#e8eef8")
    # bright glass panes
    base = Image.new("RGB", img.size, "#101722")
    d = ImageDraw.Draw(base)
    w, h = img.size
    panes = [
        ((0, 0), (w*0.45, h*0.22), "#2b6cb0"),
        ((w*0.38, 0), (w, h*0.18), "#d53f8c"),
        ((0, h*0.16), (w*0.60, h*0.46), "#dd6b20"),
        ((w*0.52, h*0.14), (w, h*0.50), "#38a169"),
        ((0, h*0.46), (w*0.40, h), "#805ad5"),
        ((w*0.34, h*0.44), (w, h), "#e53e3e"),
    ]
    for (x1, y1), (x2, y2), col in panes:
        d.polygon([(x1, y1), (x2, y1 + 20), (x2 - 25, y2), (x1 + 10, y2 - 16)], fill=col)
    mix = Image.blend(base, line, 0.36)
    mix = ImageOps.posterize(mix, 3)
    mix = radial_grid(mix, alpha=8)
    return fit_canvas(frame(vignette(mix, 80), (12, 14, 20), (130, 120, 100)), bg=(14, 15, 20))


def style_topographic(src: Image.Image) -> Image.Image:
    img = scaled(src)
    gray = ImageOps.grayscale(img)
    # contour-like bands
    contour = gray.filter(ImageFilter.CONTOUR)
    contour = ImageEnhance.Contrast(contour).enhance(2.4)
    contour = ImageOps.colorize(contour, black="#0d1117", white="#dfe8f4")
    w, h = contour.size
    overlay = Image.new("RGBA", contour.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    for i, y in enumerate(range(-60, h + 60, 24)):
        col = (29, 78, 216, 46 if i % 2 == 0 else 28)
        d.arc((-50, y, w + 50, y + 240), start=0, end=180, fill=col, width=2)
    for x in range(0, w, 120):
        d.line((x, 0, x + 40, h), fill=(217, 70, 60, 34), width=2)
    contour = Image.alpha_composite(contour.convert("RGBA"), overlay).convert("RGB")
    contour = ImageEnhance.Sharpness(contour).enhance(1.35)
    contour = ImageOps.posterize(contour, 4)
    return fit_canvas(frame(contour, (12, 17, 25), (72, 120, 142)), bg=(18, 20, 28))


def style_ceramic_mosaic(src: Image.Image) -> Image.Image:
    img = scaled(src)
    img = ImageEnhance.Color(img).enhance(0.6)
    img = ImageEnhance.Contrast(img).enhance(1.45)
    # mosaic by chunky posterize + edges
    chunk = img.resize((68, 82), Image.NEAREST).resize(img.size, Image.NEAREST)
    chunk = ImageEnhance.Sharpness(chunk).enhance(1.8)
    chunk = ImageOps.posterize(chunk, 3)
    edges = ImageOps.grayscale(img).filter(ImageFilter.FIND_EDGES)
    edges = ImageEnhance.Contrast(edges).enhance(3.0)
    grout = ImageOps.colorize(edges, black="#0f1115", white="#f4f1ea")
    mix = Image.blend(chunk, grout, 0.28)
    mix = vignette(mix, 70)
    return fit_canvas(frame(mix, (18, 20, 28), (132, 111, 92)), bg=(238, 233, 224))


def style_kintsugi(src: Image.Image) -> Image.Image:
    img = scaled(src)
    gray = ImageOps.grayscale(img)
    base = ImageOps.colorize(gray, black="#1b1420", white="#efe4d2")
    # crack lines + gold seams
    seam = gray.filter(ImageFilter.FIND_EDGES)
    seam = ImageEnhance.Contrast(seam).enhance(4.0)
    gold = ImageOps.colorize(seam, black="#1a1206", white="#f0c85a")
    base = Image.blend(base, gold, 0.33)
    d = ImageDraw.Draw(base)
    w, h = base.size
    for i in range(8):
        y = int(h * (0.08 + i * 0.11))
        d.line((0, y, w, y + (i % 3) * 8 - 6), fill="#d4af37", width=4)
    base = ImageEnhance.Sharpness(base).enhance(1.1)
    base = ImageOps.posterize(base, 4)
    return fit_canvas(frame(base, (32, 24, 12), (205, 172, 74)), bg=(26, 20, 12))


def style_ink_splash(src: Image.Image) -> Image.Image:
    img = scaled(src)
    gray = ImageOps.grayscale(img)
    bw = gray.point(lambda p: 255 if p > 125 else 0)
    bw = ImageEnhance.Contrast(bw).enhance(2.2)
    bw = ImageOps.colorize(bw, black="#0a0b0f", white="#fbf8f2")
    # dynamic splash / brush arcs
    layer = Image.new("RGBA", bw.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    w, h = bw.size
    d.arc((w*0.05, h*0.02, w*0.95, h*0.90), start=15, end=300, fill=(194, 33, 45, 120), width=14)
    d.arc((w*0.15, h*0.10, w*0.86, h*0.96), start=210, end=60, fill=(23, 114, 204, 95), width=10)
    d.ellipse((w*0.18, h*0.15, w*0.36, h*0.30), fill=(255, 202, 76, 120))
    splash = Image.alpha_composite(bw.convert("RGBA"), layer).convert("RGB")
    splash = vignette(splash, 95)
    splash = ImageOps.posterize(splash, 3)
    return fit_canvas(frame(splash, (15, 14, 18), (90, 91, 101)), bg=(245, 241, 234))


def style_transparent_cut(src: Image.Image) -> Image.Image:
    img = scaled(src)
    gray = ImageOps.grayscale(img)
    bw = gray.point(lambda p: 255 if p > 146 else 0)
    bw = ImageEnhance.Contrast(bw).enhance(2.4)
    line = ImageOps.colorize(bw, black="#111111", white="#f2efe9")
    # create cutout style with transparent-like holes via compositing with background blocks
    w, h = line.size
    holes = Image.new("RGBA", line.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(holes)
    d.ellipse((w*0.20, h*0.18, w*0.43, h*0.38), fill=(18, 22, 33, 180))
    d.polygon([(w*0.56, h*0.08), (w*0.92, h*0.20), (w*0.70, h*0.56)], fill=(198, 31, 47, 170))
    d.polygon([(w*0.08, h*0.64), (w*0.48, h*0.48), (w*0.34, h*0.92)], fill=(243, 199, 69, 155))
    cut = Image.alpha_composite(line.convert("RGBA"), holes).convert("RGB")
    cut = ImageOps.posterize(cut, 2)
    cut = ImageEnhance.Sharpness(cut).enhance(1.5)
    return fit_canvas(frame(cut, (244, 243, 238), (120, 120, 120)), bg=(247, 246, 242))


def style_dynamic_gradient(src: Image.Image) -> Image.Image:
    img = scaled(src)
    gray = ImageOps.grayscale(img)
    grad = ImageOps.colorize(gray, black="#0f172a", white="#f8fafc")
    w, h = grad.size
    overlay = Image.new("RGBA", grad.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    for i in range(0, w, 80):
        d.polygon([(i, 0), (i + 120, 0), (i + 40, h)], fill=(59, 130, 246, 35))
    for i in range(0, h, 88):
        d.polygon([(0, i), (w, i + 20), (w, i + 44), (0, i + 24)], fill=(244, 63, 94, 20))
    grad = Image.alpha_composite(grad.convert("RGBA"), overlay).convert("RGB")
    grad = ImageEnhance.Contrast(grad).enhance(1.25)
    grad = ImageOps.posterize(grad, 4)
    return fit_canvas(frame(grad, (13, 17, 24), (94, 106, 126)))


def style_unfolded_badge(src: Image.Image) -> Image.Image:
    img = scaled(src)
    # split and offset to create a more experimental folded badge
    left = img.crop((0, 0, img.width // 2, img.height))
    right = img.crop((img.width // 2, 0, img.width, img.height))
    canvas = Image.new("RGB", img.size, "#f2ede2")
    canvas.paste(ImageEnhance.Contrast(left).enhance(1.4), (0, 0))
    canvas.paste(ImageEnhance.Contrast(right).enhance(1.4), (img.width // 2 + 22, 12))
    canvas = canvas.resize((980, 1176), Image.LANCZOS)
    canvas = ImageEnhance.Color(canvas).enhance(0.85)
    canvas = ImageOps.posterize(canvas, 3)
    canvas = vignette(canvas, 90)
    return fit_canvas(frame(canvas, (34, 28, 24), (120, 100, 84)), bg=(239, 233, 225))


STYLE_FUNCS = [
    ("stained_glass", "Stained Glass", style_stained_glass),
    ("topographic", "Topographic", style_topographic),
    ("ceramic_mosaic", "Ceramic Mosaic", style_ceramic_mosaic),
    ("kintsugi", "Kintsugi", style_kintsugi),
    ("ink_splash", "Ink Splash", style_ink_splash),
    ("transparent_cut", "Transparent Cut", style_transparent_cut),
    ("dynamic_gradient", "Dynamic Gradient", style_dynamic_gradient),
    ("unfolded_badge", "Unfolded Badge", style_unfolded_badge),
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
<title>2 Wappen – 8 experimentelle Varianten</title>
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
  <h1>2 Wappen – 8 experimentelle Stilrichtungen</h1>
  <div class="sub">Hier wird nicht mehr nur gefiltert: Die Wappen werden in neue Bildsprachen übersetzt – Glas, Topographie, Collage, Kintsugi, Splash, Gradient und Fold.</div>
</header>
<main>
{''.join(sections)}
</main>
<footer>
  Öffnen: <code>file:///F:/tiroltourismus/wappen/two_wappen_variants_creative.html</code><br>
  Neu: <code>file:///F:/tiroltourismus/wappen/two_wappen_variants_experimental.html</code>
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

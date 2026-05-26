#!/usr/bin/env python3
from __future__ import annotations

import math
from pathlib import Path
from PIL import Image, ImageOps, ImageEnhance, ImageFilter, ImageDraw, ImageChops

ROOT = Path(r"F:/tiroltourismus/wappen")
OUT_DIR = ROOT / "img" / "two_wappen_variants_remix"
HTML_OUT = ROOT / "two_wappen_variants_remix.html"

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


# ---------------- helpers ----------------

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


def grid(img: Image.Image, step=20, alpha=10, color=(255, 255, 255)) -> Image.Image:
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    w, h = img.size
    for x in range(0, w, step):
        d.line((x, 0, x, h), fill=(*color, alpha), width=1)
    for y in range(0, h, step):
        d.line((0, y, w, y), fill=(*color, alpha), width=1)
    return Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB")


def paste_rot(base: Image.Image, tile: Image.Image, box: tuple[int, int], angle: float, scale: float = 1.0) -> None:
    t = tile.copy().convert("RGBA")
    if scale != 1.0:
        t = t.resize((max(1, int(t.width * scale)), max(1, int(t.height * scale))), Image.LANCZOS)
    if angle:
        t = t.rotate(angle, resample=Image.BICUBIC, expand=True)
    base.alpha_composite(t, box)


def lineart(src: Image.Image, contrast=3.0) -> Image.Image:
    g = ImageOps.grayscale(src)
    e = g.filter(ImageFilter.FIND_EDGES)
    e = ImageEnhance.Contrast(e).enhance(contrast)
    return e


# ---------------- remix styles ----------------

def style_shard_burst(src: Image.Image) -> Image.Image:
    img = scaled(src)
    w, h = img.size
    base = Image.new("RGBA", img.size, (15, 18, 26, 255))
    # central emblem and shards
    center = img.crop((w * 0.18, h * 0.14, w * 0.82, h * 0.86))
    center = center.resize((620, 760), Image.LANCZOS)
    base.alpha_composite(center.convert("RGBA"), ((w - 620) // 2, (h - 760) // 2))
    for i, ang in enumerate([-24, -12, 8, 22, 38, -36]):
        shard = img.crop((w * (0.08 + 0.1 * (i % 3)), h * (0.08 + 0.08 * (i % 2)), w * (0.5 + 0.08 * i), h * (0.5 + 0.05 * i)))
        shard = shard.resize((260 + i * 30, 180 + i * 18), Image.LANCZOS)
        shard = ImageEnhance.Contrast(shard).enhance(1.4)
        paste_rot(base, shard, (int(30 + i * 55), int(60 + i * 68)), ang, 0.9)
    d = ImageDraw.Draw(base)
    d.arc((-120, -60, w + 120, h + 60), 18, 338, fill=(247, 197, 72, 100), width=12)
    d.arc((80, 120, w - 80, h - 120), 200, 54, fill=(193, 30, 46, 100), width=8)
    out = base.convert("RGB")
    out = ImageEnhance.Contrast(out).enhance(1.35)
    out = ImageOps.posterize(out, 3)
    out = vignette(out, 95)
    return fit_canvas(frame(out, (12, 16, 22), (90, 82, 56)))


def style_orbit_seal(src: Image.Image) -> Image.Image:
    img = scaled(src)
    gray = ImageOps.grayscale(img)
    base = ImageOps.colorize(gray, black="#10131a", white="#f2eadc")
    # circular crop
    mask = Image.new("L", base.size, 0)
    d = ImageDraw.Draw(mask)
    w, h = base.size
    d.ellipse((w * 0.10, h * 0.05, w * 0.90, h * 0.90), fill=255)
    base = Image.composite(base, Image.new("RGB", base.size, "#0d1016"), mask)
    # orbit rings
    ring = Image.new("RGBA", base.size, (0, 0, 0, 0))
    rd = ImageDraw.Draw(ring)
    for r, col, sw in [(400, (249, 196, 74, 120), 6), (320, (83, 157, 255, 95), 4), (250, (192, 38, 45, 95), 5)]:
        rd.ellipse((w/2-r, h/2-r, w/2+r, h/2+r), outline=col, width=sw)
    rd.line((w*0.12, h*0.72, w*0.88, h*0.35), fill=(255,255,255,60), width=3)
    rd.line((w*0.18, h*0.28, w*0.82, h*0.76), fill=(255,255,255,45), width=2)
    base = Image.alpha_composite(base.convert("RGBA"), ring).convert("RGB")
    base = grid(base, step=26, alpha=5)
    return fit_canvas(frame(vignette(base, 80), (16, 18, 24), (92, 106, 140)))


def style_folded_poster(src: Image.Image) -> Image.Image:
    img = scaled(src)
    # fold into panels
    panel = Image.new("RGB", img.size, "#f1ede5")
    thirds = [img.crop((0, 0, img.width // 3, img.height)), img.crop((img.width // 3, 0, 2 * img.width // 3, img.height)), img.crop((2 * img.width // 3, 0, img.width, img.height))]
    xoffs = [0, 28, 58]
    for i, p in enumerate(thirds):
        p = p.resize((260, 1176), Image.LANCZOS)
        p = ImageEnhance.Contrast(p).enhance(1.5)
        panel.paste(p, (i * 260 + xoffs[i], 0))
    panel = ImageEnhance.Color(panel).enhance(0.82)
    panel = ImageOps.posterize(panel, 3)
    # crease lines
    d = ImageDraw.Draw(panel)
    for x in [260, 520, 780]:
        d.line((x, 0, x + 12, panel.height), fill=(20, 22, 28), width=6)
    for y in [220, 460, 710, 940]:
        d.line((0, y, panel.width, y + 8), fill=(180, 40, 48), width=2)
    return fit_canvas(frame(vignette(panel, 90), (34, 30, 25), (122, 108, 92)), bg=(240, 235, 228))


def style_negative_space(src: Image.Image) -> Image.Image:
    img = scaled(src)
    g = ImageOps.grayscale(img)
    bw = g.point(lambda p: 255 if p > 132 else 0)
    bw = ImageEnhance.Contrast(bw).enhance(2.6)
    base = ImageOps.colorize(bw, black="#101215", white="#f7f5f0")
    # punch out silhouette holes
    holes = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(holes)
    w, h = base.size
    d.ellipse((w*0.14, h*0.12, w*0.42, h*0.40), fill=(17, 20, 28, 220))
    d.polygon([(w*0.52, h*0.08), (w*0.90, h*0.20), (w*0.72, h*0.58)], fill=(193, 31, 45, 170))
    d.polygon([(w*0.18, h*0.70), (w*0.52, h*0.50), (w*0.40, h*0.92)], fill=(250, 200, 74, 160))
    base = Image.alpha_composite(base.convert("RGBA"), holes).convert("RGB")
    base = ImageOps.posterize(base, 2)
    return fit_canvas(frame(base, (242, 240, 234), (122, 122, 122)), bg=(247, 246, 242))


def style_radar_map(src: Image.Image) -> Image.Image:
    img = scaled(src)
    g = ImageOps.grayscale(img)
    contours = g.filter(ImageFilter.CONTOUR)
    contours = ImageEnhance.Contrast(contours).enhance(2.7)
    base = ImageOps.colorize(contours, black="#09203a", white="#e7f3ff")
    w, h = base.size
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    # radar rings and sweep
    for r, alpha in [(120, 24), (220, 30), (320, 24), (420, 18)]:
        d.ellipse((w/2-r, h/2-r, w/2+r, h/2+r), outline=(58, 181, 255, alpha), width=2)
    d.polygon([(w/2, h/2), (w*0.92, h*0.18), (w*0.86, h*0.18), (w/2, h/2)], fill=(37, 99, 235, 55))
    base = Image.alpha_composite(base.convert("RGBA"), layer).convert("RGB")
    base = grid(base, step=24, alpha=6, color=(64, 196, 255))
    return fit_canvas(frame(base, (10, 16, 28), (86, 148, 196)))


def style_mosaic_break(src: Image.Image) -> Image.Image:
    img = scaled(src)
    # explode into chunky tiles and recolor them
    tile = img.resize((72, 86), Image.NEAREST).resize(img.size, Image.NEAREST)
    tile = ImageEnhance.Contrast(tile).enhance(1.6)
    tile = ImageOps.posterize(tile, 3)
    # create irregular mosaic seams
    seams = ImageOps.grayscale(img).filter(ImageFilter.FIND_EDGES)
    seams = ImageEnhance.Contrast(seams).enhance(3.5)
    seams = ImageOps.colorize(seams, black="#111111", white="#f5efe6")
    tile = Image.blend(tile, seams, 0.28)
    # shift and offset blocks
    layer = Image.new("RGB", tile.size, "#f4efe7")
    for i in range(4):
        crop = tile.crop((i * 220, 0, min(tile.width, i * 220 + 260), tile.height))
        crop = crop.rotate((i - 1.5) * 6, expand=True)
        layer.paste(crop, (i * 230 - 40, int((i % 2) * 18)))
    layer = ImageEnhance.Sharpness(layer).enhance(1.4)
    return fit_canvas(frame(vignette(layer, 85), (38, 30, 24), (148, 136, 108)), bg=(242, 236, 226))


def style_typographic_shield(src: Image.Image) -> Image.Image:
    img = scaled(src)
    gray = ImageOps.grayscale(img)
    edges = gray.filter(ImageFilter.FIND_EDGES)
    edges = ImageEnhance.Contrast(edges).enhance(4.0)
    shield = ImageOps.colorize(edges, black="#101010", white="#f7f4ef")
    w, h = shield.size
    mask = Image.new("L", shield.size, 0)
    d = ImageDraw.Draw(mask)
    d.rounded_rectangle((w*0.18, h*0.10, w*0.82, h*0.90), radius=120, fill=255)
    shield = Image.composite(shield, Image.new("RGB", shield.size, "#0e1117"), mask)
    # bold typographic bars (as design language, no text)
    bar = Image.new("RGBA", shield.size, (0, 0, 0, 0))
    bd = ImageDraw.Draw(bar)
    bd.rectangle((0, h*0.08, w, h*0.16), fill=(183, 28, 40, 95))
    bd.rectangle((0, h*0.83, w, h*0.91), fill=(249, 200, 72, 92))
    bd.rectangle((w*0.75, 0, w*0.82, h), fill=(60, 128, 255, 65))
    shield = Image.alpha_composite(shield.convert("RGBA"), bar).convert("RGB")
    shield = ImageOps.posterize(shield, 3)
    return fit_canvas(frame(shield, (16, 16, 20), (96, 96, 102)))


def style_ghost_outline(src: Image.Image) -> Image.Image:
    img = scaled(src)
    # blurred ghost silhouette with crisp outline
    blur = img.filter(ImageFilter.GaussianBlur(6))
    blur = ImageEnhance.Contrast(blur).enhance(1.4)
    outline = lineart(img, 3.6)
    outline = ImageOps.colorize(outline, black="#12151b", white="#f3ead8")
    glow = ImageOps.colorize(ImageOps.grayscale(blur), black="#13233c", white="#b7d4ff")
    mix = Image.blend(glow, outline, 0.48)
    # one surreal crop
    mix = ImageChops.offset(mix, 34, -22)
    mix = grid(mix, step=30, alpha=8)
    return fit_canvas(frame(vignette(mix, 100), (12, 18, 28), (92, 120, 160)))


STYLE_FUNCS = [
    ("shard_burst", "Shard Burst", style_shard_burst),
    ("orbit_seal", "Orbit Seal", style_orbit_seal),
    ("folded_poster", "Folded Poster", style_folded_poster),
    ("negative_space", "Negative Space", style_negative_space),
    ("radar_map", "Radar Map", style_radar_map),
    ("mosaic_break", "Mosaic Break", style_mosaic_break),
    ("typographic_shield", "Typographic Shield", style_typographic_shield),
    ("ghost_outline", "Ghost Outline", style_ghost_outline),
]


def build_html(blocks: list[dict]) -> None:
    sec = []
    for block in blocks:
        cards = [f'''<div class="card orig"><div class="label">Original</div><img src="{block['src_rel']}" alt="{block['title']} original"></div>''']
        for var in block['variants']:
            cards.append(f'''<div class="card"><div class="label">{var['label']}</div><img src="{var['img_rel']}" alt="{block['title']} {var['label']}"></div>''')
        sec.append(f'''
        <section class="block">
          <h2>{block['title']}</h2>
          <div class="grid">{''.join(cards)}</div>
        </section>''')
    html = f'''<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>2 Wappen – experimental remix</title>
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
  <h1>2 Wappen – experimenteller Remix</h1>
  <div class="sub">Die Varianten sind jetzt bewusst als neue Bildideen gebaut: Shards, Orbit, Fold, Negative Space, Radar, Mosaic, Typo und Ghost. Damit sieht es nicht mehr wie „Original mit Filter“ aus.</div>
</header>
<main>
{''.join(sec)}
</main>
<footer>Öffnen: <code>file:///F:/tiroltourismus/wappen/two_wappen_variants_remix.html</code></footer>
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

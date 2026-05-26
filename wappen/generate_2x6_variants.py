#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageOps, ImageEnhance, ImageFilter, ImageDraw

ROOT = Path(r"F:/tiroltourismus/wappen")
OUT_DIR = ROOT / "img" / "two_wappen_variants"
HTML_OUT = ROOT / "two_wappen_variants.html"

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

VARIANTS = [
    ("modern_badge", "Modern Badge", "clean, reduced, logo-like"),
    ("heraldic_bold", "Heraldic Bold", "strong coat-of-arms, sharp contrast"),
    ("engraved_seal", "Engraved Seal", "etched, antique, parchment feel"),
    ("minimal_line", "Minimal Line", "thin lines, white space, minimal"),
    ("dark_premium", "Dark Premium", "dark background, premium gold accents"),
    ("cutout_poster", "Cutout Poster", "blocky, posterized, contemporary"),
]


def log(msg: str) -> None:
    print(msg, flush=True)


def fit_canvas(img: Image.Image, size=(360, 432), bg=(11, 13, 18)) -> Image.Image:
    canvas = Image.new("RGBA", size, (*bg, 255))
    inner = img.convert("RGBA")
    inner.thumbnail((size[0] - 24, size[1] - 24), Image.LANCZOS)
    x = (size[0] - inner.width) // 2
    y = (size[1] - inner.height) // 2
    canvas.alpha_composite(inner, (x, y))
    return canvas.convert("RGB")


def add_frame(img: Image.Image, inner=(20, 24, 34), outer=(72, 80, 98)) -> Image.Image:
    img = ImageOps.expand(img, border=8, fill=inner)
    img = ImageOps.expand(img, border=2, fill=outer)
    return img


def overlay_texture(img: Image.Image, tint=(255, 255, 255), alpha=24) -> Image.Image:
    tex = Image.new("RGBA", img.size, (*tint, 0))
    d = ImageDraw.Draw(tex)
    w, h = img.size
    for x in range(0, w, 16):
        d.line((x, 0, x, h), fill=(*tint, alpha if x % 32 == 0 else alpha // 2), width=1)
    for y in range(0, h, 16):
        d.line((0, y, w, y), fill=(*tint, alpha if y % 32 == 0 else alpha // 2), width=1)
    return Image.alpha_composite(img.convert("RGBA"), tex).convert("RGB")


def style_modern_badge(src: Image.Image) -> Image.Image:
    img = src.convert("RGB").resize((980, 1176), Image.LANCZOS)
    img = ImageEnhance.Color(img).enhance(0.72)
    img = ImageEnhance.Contrast(img).enhance(1.35)
    img = ImageEnhance.Sharpness(img).enhance(1.05)
    gray = ImageOps.grayscale(img).filter(ImageFilter.FIND_EDGES)
    gray = ImageEnhance.Contrast(gray).enhance(2.2)
    line = ImageOps.colorize(gray, black="#0f172a", white="#f3e8d6")
    base = Image.new("RGB", img.size, "#eef2f7")
    img = Image.blend(base, img, 0.60)
    img = Image.blend(img, line, 0.24)
    img = ImageOps.posterize(img, 4)
    return fit_canvas(add_frame(img, (17, 21, 31)))


def style_heraldic_bold(src: Image.Image) -> Image.Image:
    img = src.convert("RGB").resize((980, 1176), Image.LANCZOS)
    img = ImageEnhance.Color(img).enhance(1.25)
    img = ImageEnhance.Contrast(img).enhance(1.55)
    img = ImageOps.posterize(img, 3)
    img = ImageEnhance.Sharpness(img).enhance(1.7)
    ink = ImageOps.grayscale(img).filter(ImageFilter.FIND_EDGES)
    ink = ImageEnhance.Contrast(ink).enhance(2.8)
    ink = ImageOps.colorize(ink, black="#121212", white="#f0c85a")
    red = Image.new("RGB", img.size, "#9a1f24")
    img = Image.blend(red, img, 0.35)
    img = Image.blend(img, ink, 0.32)
    return fit_canvas(add_frame(img, (24, 24, 34), (84, 66, 24)))


def style_engraved_seal(src: Image.Image) -> Image.Image:
    img = src.convert("L").resize((980, 1176), Image.LANCZOS)
    img = ImageEnhance.Contrast(img).enhance(1.75)
    img = img.filter(ImageFilter.EMBOSS)
    img = img.filter(ImageFilter.FIND_EDGES)
    img = ImageEnhance.Contrast(img).enhance(1.35)
    img = ImageOps.colorize(img, black="#24160f", white="#f4dfc2")
    img = overlay_texture(img, tint=(255, 255, 255), alpha=18)
    vignette = Image.new("L", img.size, 0)
    d = ImageDraw.Draw(vignette)
    d.ellipse((-180, -220, img.size[0] + 180, img.size[1] + 220), fill=255)
    vignette = vignette.filter(ImageFilter.GaussianBlur(120))
    parchment = Image.new("RGB", img.size, "#c4aa7d")
    img = Image.composite(img, parchment, vignette)
    return fit_canvas(add_frame(img, (42, 31, 22), (110, 93, 63)))


def style_minimal_line(src: Image.Image) -> Image.Image:
    img = src.convert("RGB").resize((980, 1176), Image.LANCZOS)
    img = ImageEnhance.Color(img).enhance(0.35)
    img = ImageEnhance.Contrast(img).enhance(1.25)
    gray = ImageOps.grayscale(img)
    edges = gray.filter(ImageFilter.FIND_EDGES)
    edges = ImageEnhance.Contrast(edges).enhance(3.0)
    # Clean black/white linework with one accent tone.
    lines = ImageOps.colorize(edges, black="#101010", white="#f6f6f2")
    accent_mask = gray.point(lambda p: 255 if p > 145 else 0)
    accent = Image.new("RGB", img.size, "#c12a2a")
    lines = Image.composite(accent, lines, accent_mask)
    lines = ImageOps.autocontrast(lines)
    return fit_canvas(add_frame(lines, (20, 20, 20), (92, 92, 92)), bg=(246, 246, 242))


def style_dark_premium(src: Image.Image) -> Image.Image:
    img = src.convert("RGB").resize((980, 1176), Image.LANCZOS)
    img = ImageEnhance.Color(img).enhance(0.9)
    img = ImageEnhance.Contrast(img).enhance(1.6)
    img = ImageEnhance.Sharpness(img).enhance(1.25)
    gray = ImageOps.grayscale(img)
    edges = gray.filter(ImageFilter.FIND_EDGES)
    edges = ImageEnhance.Contrast(edges).enhance(2.2)
    gold = ImageOps.colorize(edges, black="#0d1117", white="#d8b35a")
    bg = Image.new("RGB", img.size, "#090b10")
    img = Image.blend(bg, gold, 0.72)
    img = overlay_texture(img, tint=(255, 255, 255), alpha=8)
    return fit_canvas(add_frame(img, (10, 12, 18), (172, 137, 42)))


def style_cutout_poster(src: Image.Image) -> Image.Image:
    img = src.convert("RGB").resize((980, 1176), Image.LANCZOS)
    img = ImageEnhance.Color(img).enhance(0.8)
    img = ImageEnhance.Contrast(img).enhance(1.55)
    img = ImageOps.posterize(img, 3)
    img = ImageOps.autocontrast(img)
    # geometric color blocking
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    w, h = img.size
    d.rectangle((0, 0, w, h * 0.16), fill=(11, 13, 18, 140))
    d.polygon([(0, h*0.86), (w*0.58, h), (0, h)], fill=(180, 28, 36, 120))
    d.polygon([(w*0.68, 0), (w, 0), (w, h*0.45)], fill=(240, 200, 90, 90))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    return fit_canvas(add_frame(img, (19, 22, 31), (70, 77, 91)))


STYLE_FUNCS = {
    "modern_badge": style_modern_badge,
    "heraldic_bold": style_heraldic_bold,
    "engraved_seal": style_engraved_seal,
    "minimal_line": style_minimal_line,
    "dark_premium": style_dark_premium,
    "cutout_poster": style_cutout_poster,
}


def build_html(items: list[dict]) -> None:
    sections = []
    for block in items:
        cards = [
            f'''<div class="card orig"><div class="label">Original</div><img src="{block['src_rel']}" alt="{block['title']} original"></div>'''
        ]
        for item in block['variants']:
            cards.append(f'''<div class="card"><div class="label">{item['label']}</div><img src="{item['img_rel']}" alt="{block['title']} {item['label']}"></div>''')
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
<title>2 Wappen – je 6 Varianten</title>
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
.label {{ padding:10px 12px; font-size:.75rem; text-transform:uppercase; letter-spacing:.06em; color:#97a1b7; border-bottom:1px solid #23293a; background:#171b26; }}
.card img {{ display:block; width:100%; background:#0b0d12; aspect-ratio: 5 / 6; object-fit:contain; }}
footer {{ padding:18px 24px 30px; color:#788; font-size:.8rem; border-top:1px solid #23293a; }}
code {{ color:#a8c7ff; }}
</style>
</head>
<body>
<header>
  <h1>2 Wappen – je 6 Stilvarianten</h1>
  <div class="sub">Vergleich von Innsbruck und Kitzbühel. Die moderne Richtung ist dabei nur eine Variante; die anderen sind bewusst anders, damit der Stil klar unterscheidbar bleibt.</div>
</header>
<main>
{''.join(sections)}
</main>
<footer>
  Öffnen: <code>file:///F:/tiroltourismus/wappen/two_wappen_six_variants.html</code>
</footer>
</body>
</html>'''
    (ROOT / "two_wappen_six_variants.html").write_text(html, encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    blocks = []
    for spec in SETS:
        src = spec["src"]
        if not src.exists():
            raise FileNotFoundError(src)
        src_rel = src.relative_to(ROOT).as_posix()
        src_img = Image.open(src).convert("RGB")
        variants = []
        for key, label, desc in VARIANTS:
            out_dir = OUT_DIR / spec["id"]
            out_dir.mkdir(parents=True, exist_ok=True)
            out = out_dir / f"{key}.png"
            STYLE_FUNCS[key](src_img).save(out)
            variants.append({
                "label": label,
                "desc": desc,
                "img_rel": out.relative_to(ROOT).as_posix(),
            })
            log(f"saved {out}")
        blocks.append({
            "title": spec["title"],
            "src_rel": src_rel,
            "variants": variants,
        })
    build_html(blocks)
    log(f"wrote {ROOT / 'two_wappen_six_variants.html'}")


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageOps, ImageEnhance, ImageFilter, ImageDraw

ROOT = Path(r"F:/tiroltourismus/wappen")
OUT_DIR = ROOT / "img" / "style_variants2"
HTML_OUT = ROOT / "style_variants_more.html"

SOURCES = [
    {
        "key": "innsbruck_modern",
        "title": "Innsbruck – Modern Badge",
        "src": ROOT / "img" / "orte" / "statutarstadt_innsbruck" / "stadtwappen.png",
        "desc": "bereits akzeptierte Modern-Badge-Richtung",
        "style": "modern_a",
    },
    {
        "key": "kitzbuehel_modern",
        "title": "Kitzbühel – Modern Badge",
        "src": ROOT / "img" / "orte" / "kitzbühel" / "kitzbühel.png",
        "desc": "anderes Wappen, gleiche moderne Richtung",
        "style": "modern_b",
    },
    {
        "key": "lienz_modern",
        "title": "Lienz – Modern Badge",
        "src": ROOT / "img" / "orte" / "lienz" / "lienz.png",
        "desc": "anderes Wappen, noch klarer und reduzierter",
        "style": "modern_c",
    },
]


def fit_canvas(img: Image.Image, size=(360, 432)) -> Image.Image:
    canvas = Image.new("RGBA", size, (10, 12, 18, 255))
    inner = img.convert("RGBA")
    inner.thumbnail((size[0] - 24, size[1] - 24), Image.LANCZOS)
    x = (size[0] - inner.width) // 2
    y = (size[1] - inner.height) // 2
    canvas.alpha_composite(inner, (x, y))
    return canvas.convert("RGB")


def add_frame(img: Image.Image, color=(21, 26, 38)) -> Image.Image:
    return ImageOps.expand(ImageOps.expand(img, 8, fill=color), 2, fill=(72, 80, 98))


def modern_a(src: Image.Image) -> Image.Image:
    img = src.convert("RGB").resize((980, 1176), Image.LANCZOS)
    img = ImageEnhance.Color(img).enhance(0.75)
    img = ImageEnhance.Contrast(img).enhance(1.3)
    img = ImageEnhance.Sharpness(img).enhance(1.1)
    gray = ImageOps.grayscale(img).filter(ImageFilter.FIND_EDGES)
    gray = ImageEnhance.Contrast(gray).enhance(2.0)
    ink = ImageOps.colorize(gray, black="#16233a", white="#f1e7d6")
    base = Image.new("RGB", img.size, "#eef2f7")
    img = Image.blend(base, img, 0.62)
    img = Image.blend(img, ink, 0.22)
    img = ImageOps.posterize(img, 4)
    img = ImageOps.autocontrast(img)
    return fit_canvas(add_frame(img, (17, 21, 31)))


def modern_b(src: Image.Image) -> Image.Image:
    img = src.convert("RGB").resize((980, 1176), Image.LANCZOS)
    img = ImageEnhance.Color(img).enhance(1.05)
    img = ImageEnhance.Contrast(img).enhance(1.45)
    img = ImageEnhance.Sharpness(img).enhance(1.4)
    g = ImageOps.grayscale(img)
    g = ImageEnhance.Contrast(g).enhance(2.2)
    edges = g.filter(ImageFilter.FIND_EDGES)
    edges = ImageEnhance.Contrast(edges).enhance(2.3)
    overlay = ImageOps.colorize(edges, black="#0f172a", white="#eab308")
    tint = Image.new("RGB", img.size, "#f5efe4")
    img = Image.blend(tint, img, 0.58)
    img = Image.blend(img, overlay, 0.24)
    img = ImageOps.posterize(img, 3)
    return fit_canvas(add_frame(img, (23, 28, 40)))


def modern_c(src: Image.Image) -> Image.Image:
    img = src.convert("RGB").resize((980, 1176), Image.LANCZOS)
    img = ImageEnhance.Color(img).enhance(0.58)
    img = ImageEnhance.Contrast(img).enhance(1.55)
    img = ImageEnhance.Sharpness(img).enhance(0.95)
    gray = ImageOps.grayscale(img)
    poster = ImageOps.posterize(gray, 3)
    poster = ImageEnhance.Contrast(poster).enhance(1.6)
    base = ImageOps.colorize(poster, black="#16202b", white="#f5f1e6")
    red = Image.new("RGB", img.size, "#8f1d1d")
    mask = gray.point(lambda p: 255 if p < 120 else 0)
    img = Image.composite(red, base, mask)
    # subtle geometric panel feel
    panel = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(panel)
    w, h = img.size
    d.polygon([(0, 0), (w * 0.7, 0), (w * 0.55, h), (0, h)], fill=(255, 255, 255, 24))
    img = Image.alpha_composite(img.convert("RGBA"), panel).convert("RGB")
    return fit_canvas(add_frame(img, (20, 24, 34)))


STYLES = {"modern_a": modern_a, "modern_b": modern_b, "modern_c": modern_c}


def build_html(items: list[tuple[str, Path, Path, str]]) -> None:
    cards = []
    for title, src, out, desc in items:
        cards.append(f'''
        <article class="card">
          <h2>{title}</h2>
          <div class="pair">
            <div><div class="label">Original</div><img src="{src.as_posix()}" alt="{title} original"></div>
            <div><div class="label">Modern</div><img src="{out.as_posix()}" alt="{title} modern"></div>
          </div>
          <p>{desc}</p>
        </article>''')
    html = f'''<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Zusätzliche moderne Wappen-Varianten</title>
<style>
:root {{ color-scheme: dark; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif; background:#0b0d12; color:#eee; }}
header {{ padding:20px 24px; background:linear-gradient(135deg,#151922,#0d1016); border-bottom:1px solid #23293a; position:sticky; top:0; z-index:5; }}
h1 {{ margin:0 0 8px; font-size:1.4rem; }}
.sub {{ color:#9aa3b2; font-size:.92rem; }}
main {{ padding:18px 24px; display:grid; grid-template-columns:repeat(auto-fit,minmax(340px,1fr)); gap:16px; }}
.card {{ background:#121621; border:1px solid #23293a; border-radius:14px; overflow:hidden; }}
.card h2 {{ margin:0; padding:12px 14px; border-bottom:1px solid #23293a; font-size:1rem; }}
.pair {{ display:grid; grid-template-columns:1fr 1fr; }}
.pair > div {{ padding:10px; border-right:1px solid #23293a; }}
.pair > div:last-child {{ border-right:0; }}
.label {{ color:#8b93a7; font-size:.72rem; margin:0 0 8px; text-transform:uppercase; letter-spacing:.06em; }}
img {{ display:block; width:100%; background:#0b0d12; border-radius:10px; }}
.card p {{ margin:0; padding:10px 14px 14px; color:#a3acc0; font-size:.84rem; }}
footer {{ padding:18px 24px 30px; color:#788; font-size:.8rem; border-top:1px solid #23293a; }}
</style>
</head>
<body>
<header>
  <h1>2 weitere moderne Wappen-Varianten</h1>
  <div class="sub">Ein anderes Ausgangswappen, aber gleiche moderne Stilrichtung – damit du sehen kannst, ob der Stil auf unterschiedliche Wappen trägt.</div>
</header>
<main>
{''.join(cards)}
</main>
<footer>Öffnen: <code>file:///F:/tiroltourismus/wappen/style_variants_more.html</code></footer>
</body>
</html>'''
    HTML_OUT.write_text(html, encoding='utf-8')


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    items = []
    for spec in SOURCES:
        src = spec['src']
        if not src.exists():
            raise FileNotFoundError(src)
        img = Image.open(src).convert('RGB')
        out = OUT_DIR / f"{spec['key']}.png"
        styled = STYLES[spec['style']](img)
        styled.save(out)
        items.append((spec['title'], src, out, spec['desc']))
        print(f'saved {out}', flush=True)
    build_html(items)
    print(f'wrote {HTML_OUT}', flush=True)


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
from __future__ import annotations

import json
import html as html_mod
import re
from pathlib import Path

ROOT = Path(r"F:/tiroltourismus/wappen")
DATA = ROOT / "wappen_page_data.json"
OUT = ROOT / "sd35_uebersicht.html"
GEN_ROOT = ROOT / "img" / "sd35"


def sanitize(name: str) -> str:
    s = name.lower().replace('ä','ae').replace('ö','oe').replace('ü','ue').replace('ß','ss')
    s = s.replace(' ','_').replace('/','_')
    s = re.sub(r'[^a-z0-9_\-]+', '_', s)
    s = re.sub(r'_+', '_', s).strip('_')
    return s


def gpath(rel: str) -> str:
    return str(Path('img/sd35') / Path(rel).relative_to('img'))


def exists(rel: str) -> bool:
    return (GEN_ROOT / Path(rel).relative_to('img')).exists()


def card(title: str, orig_rel: str, gen_rel: str, district_key: str) -> str:
    orig = orig_rel
    gen = gpath(gen_rel)
    ok = 1 if exists(gen_rel) else 0
    return f'''
    <article class="card" data-n="{html_mod.escape(title.lower())}" data-b="{html_mod.escape(district_key)}" data-k="{ok}">
      <div class="card-h">
        <div class="title">{html_mod.escape(title)}</div>
        <div class="badge">{'✓ generiert' if ok else '⏳ fehlt'}</div>
      </div>
      <div class="pair">
        <div class="pane">
          <div class="label">Original</div>
          <img src="{html_mod.escape(orig)}" alt="{html_mod.escape(title)} Original" loading="lazy" onclick="openLight(this.src, '{html_mod.escape(title)} – Original')">
        </div>
        <div class="pane">
          <div class="label">SD 3.5 lokal</div>
          <img src="{html_mod.escape(gen)}" alt="{html_mod.escape(title)} SD 3.5" loading="lazy" onclick="openLight(this.src, '{html_mod.escape(title)} – SD 3.5')">
        </div>
      </div>
    </article>'''


def main() -> None:
    data = json.loads(DATA.read_text(encoding='utf-8'))
    sections = []
    total = 0
    generated = 0

    for bezirk in data['bezirke']:
        bname = bezirk['name']
        bkey = sanitize(bezirk['key'] if 'key' in bezirk else bname)
        cards = []

        # district original + generated overview card first
        orig_d = bezirk.get('img', '')
        gen_d = orig_d and str((GEN_ROOT / Path(orig_d).relative_to('img')).as_posix())
        if orig_d:
            ok = 1 if gen_d and Path(gen_d).exists() else 0
            generated += ok
            total += 1
            cards.append(f'''
            <article class="card district" data-n="{html_mod.escape(bname.lower())}" data-b="{html_mod.escape(bkey)}" data-k="{ok}">
              <div class="card-h">
                <div class="title">{html_mod.escape(bname)} – Bezirk</div>
                <div class="badge">{'✓ generiert' if ok else '⏳ fehlt'}</div>
              </div>
              <div class="pair">
                <div class="pane">
                  <div class="label">Original</div>
                  <img src="{html_mod.escape(orig_d)}" alt="{html_mod.escape(bname)} Original" loading="lazy" onclick="openLight(this.src, '{html_mod.escape(bname)} – Original')">
                </div>
                <div class="pane">
                  <div class="label">SD 3.5 lokal</div>
                  <img src="{html_mod.escape(gen_d)}" alt="{html_mod.escape(bname)} SD 3.5" loading="lazy" onclick="openLight(this.src, '{html_mod.escape(bname)} – SD 3.5')">
                </div>
              </div>
            </article>''')

        for ort in bezirk['orte']:
            title = ort['name']
            orig_rel = ort['img']
            gen_rel = orig_rel
            cards.append(card(title, orig_rel, gen_rel, bkey))
            total += 1
            if exists(gen_rel):
                generated += 1

        sections.append(f'''
        <section class="district" data-b="{html_mod.escape(bkey)}">
          <h2>{html_mod.escape(bname)} <span>{generated if False else ''}</span></h2>
          <div class="grid">{''.join(cards)}</div>
        </section>''')

    html = f'''<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Tirol Wappen – Original vs SD 3.5 lokal</title>
<style>
:root {{ color-scheme: dark; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif; background:#0b0d12; color:#e8e8e8; }}
header {{ padding:20px 24px; background:linear-gradient(135deg,#151922,#0d1016); border-bottom:1px solid #212532; position:sticky; top:0; z-index:10; }}
h1 {{ margin:0 0 8px; font-size:1.35rem; }}
.meta {{ display:flex; flex-wrap:wrap; gap:10px; font-size:.9rem; color:#aab; }}
.meta span {{ background:#171b26; border:1px solid #252b3b; padding:4px 10px; border-radius:999px; }}
.controls {{ display:flex; gap:10px; flex-wrap:wrap; margin-top:14px; }}
.controls input, .controls select {{ background:#121621; color:#eee; border:1px solid #293044; border-radius:10px; padding:10px 12px; min-width:180px; }}
.controls button {{ background:#151a27; color:#ddd; border:1px solid #293044; border-radius:10px; padding:10px 12px; cursor:pointer; }}
.controls button.on {{ background:#28553a; border-color:#2f7a52; }}
main {{ padding:18px 24px 30px; }}
section.district {{ margin:0 0 28px; }}
section.district h2 {{ margin:0 0 14px; padding-bottom:8px; border-bottom:1px solid #23293a; font-size:1.15rem; }}
.grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(480px,1fr)); gap:14px; }}
.card {{ background:#121621; border:1px solid #23293a; border-radius:14px; overflow:hidden; }}
.card-h {{ display:flex; justify-content:space-between; gap:10px; align-items:center; padding:10px 12px; background:#171b26; border-bottom:1px solid #23293a; }}
.title {{ font-weight:700; font-size:.95rem; }}
.badge {{ font-size:.78rem; color:#9aa7ff; white-space:nowrap; }}
.pair {{ display:grid; grid-template-columns:1fr 1fr; gap:0; }}
.pane {{ padding:10px; border-right:1px solid #23293a; }}
.pane:last-child {{ border-right:0; }}
.label {{ font-size:.72rem; color:#8b93a7; margin:0 0 8px; text-transform:uppercase; letter-spacing:.06em; }}
.pane img {{ width:100%; aspect-ratio: 5 / 6; object-fit:contain; background:#0b0d12; border-radius:10px; cursor:pointer; }}
.pane img:hover {{ outline:2px solid #3a7; }}
.hidden {{ display:none !important; }}
.lightbox {{ position:fixed; inset:0; background:rgba(0,0,0,.88); display:none; align-items:center; justify-content:center; z-index:100; flex-direction:column; gap:14px; padding:20px; }}
.lightbox.show {{ display:flex; }}
.lightbox img {{ max-width:92vw; max-height:86vh; object-fit:contain; border-radius:14px; box-shadow:0 20px 60px rgba(0,0,0,.5); }}
.lightbox .cap {{ color:#ddd; font-size:.95rem; background:rgba(10,10,14,.7); padding:8px 14px; border-radius:999px; }}
footer {{ padding:18px 24px 30px; color:#788; font-size:.8rem; border-top:1px solid #23293a; }}
@media (max-width: 900px) {{ .grid {{ grid-template-columns:1fr; }} .pair {{ grid-template-columns:1fr; }} .pane {{ border-right:0; border-bottom:1px solid #23293a; }} .pane:last-child {{ border-bottom:0; }} }}
</style>
</head>
<body>
<header>
  <h1>Tirol Wappen – Original vs SD 3.5 lokal</h1>
  <div class="meta">
    <span>{total} Einträge</span>
    <span>{generated} mit lokalem SD 3.5</span>
    <span>Originale links, generierte Version rechts</span>
  </div>
  <div class="controls">
    <input id="q" placeholder="Suchen…" oninput="apply()">
    <select id="b" onchange="apply()">
      <option value="">Alle Bezirke</option>
      {''.join(f'<option value="{html_mod.escape(sanitize(bz["key"] if "key" in bz else bz["name"]))}">{html_mod.escape(bz["name"])}</option>' for bz in data['bezirke'])}
    </select>
    <button id="ba" class="on" onclick="mode('a')">Alle</button>
    <button id="bg" onclick="mode('g')">Nur generierte</button>
    <button id="bo" onclick="mode('o')">Nur Originale</button>
  </div>
</header>
<main>
{''.join(sections)}
</main>
<div class="lightbox" id="lb" onclick="hideLb()"><img id="lbimg" alt=""><div class="cap" id="lbcap"></div></div>
<footer>Lokale Vorschau aus <code>F:/tiroltourismus/wappen/img/sd35</code>. Klick auf ein Bild öffnet die Großansicht.</footer>
<script>
let current='a';
function mode(m) {{ current=m; ['ba','bg','bo'].forEach(id=>document.getElementById(id).classList.remove('on')); document.getElementById('b'+m).classList.add('on'); apply(); }}
function apply() {{
  const q=document.getElementById('q').value.toLowerCase();
  const b=document.getElementById('b').value;
  document.querySelectorAll('article.card').forEach(c=>{{
    const text=c.dataset.n || '';
    const dk=c.dataset.k || '0';
    const ok=( !q || text.includes(q) ) && ( !b || c.closest('section.district').dataset.b===b );
    const okMode=(current==='a') || (current==='g' && dk==='1') || (current==='o' && dk==='0');
    c.classList.toggle('hidden', !(ok && okMode));
  }});
  document.querySelectorAll('section.district').forEach(s=>{{
    const vis=[...s.querySelectorAll('article.card')].some(c=>!c.classList.contains('hidden'));
    s.classList.toggle('hidden', !vis);
  }});
}}
function openLight(src, cap) {{ document.getElementById('lbimg').src = src; document.getElementById('lbcap').textContent = cap; document.getElementById('lb').classList.add('show'); }}
function hideLb() {{ document.getElementById('lb').classList.remove('show'); }}
</script>
</body>
</html>'''

    OUT.write_text(html, encoding='utf-8')
    print(f"Wrote {OUT} ({len(html)} bytes)")


if __name__ == '__main__':
    main()

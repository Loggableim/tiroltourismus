#!/usr/bin/env python3
"""Build vergleich.html — SSR, zeigt ALLE vorhandenen generierten Wappen an (nicht nur 3)."""
import json, os, re, html as html_mod

with open('wappen_page_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# ALLE vorhandenen modernen KI-Bilder — jedes bekommt seinen eigenen Eintrag
# Format: key -> [{img, model_label}, ...]
FERTIG = {
    'innsbruck_stadt_innsbruck': [
        {'img': 'img/generiert/wappen_innsbruck_modern_qwen.png', 'label': 'Qwen Modern'},
        {'img': 'img/generiert/wappen_innsbruck_modern_flux.png', 'label': 'FLUX Modern'},
        {'img': 'img/generiert/wappen_innsbruck_classic_qwen.png', 'label': 'Qwen Klassisch'},
        {'img': 'img/generiert/wappen_innsbruck_classic_flux.png', 'label': 'FLUX Klassisch'},
        {'img': 'img/generiert/wappen_innsbruck_tiroltourismus_qwen.png', 'label': 'Qwen Tirol-Tourismus'},
        {'img': 'img/generiert/wappen_innsbruck_tiroltourismus_flux.png', 'label': 'FLUX Tirol-Tourismus'},
    ],
    'innsbruck_land_goetzens': [
        {'img': 'img/generiert/wappen_gotzens_modern_flux.png', 'label': 'FLUX Modern'},
        {'img': 'img/generiert/wappen_gotzens_modern_qwen.png', 'label': 'Qwen Modern'},
        {'img': 'img/generiert/wappen_gotzens_classic_flux.png', 'label': 'FLUX Klassisch'},
        {'img': 'img/generiert/wappen_gotzens_classic_qwen.png', 'label': 'Qwen Klassisch'},
        {'img': 'img/generiert/wappen_gotzens_tiroltourismus_flux.png', 'label': 'FLUX Tirol-Tourismus'},
        {'img': 'img/generiert/wappen_gotzens_tiroltourismus_qwen.png', 'label': 'Qwen Tirol-Tourismus'},
    ],
    'innsbruck_land_wattens': [
        {'img': 'img/generiert/wappen_wattens_modern_flux.png', 'label': 'FLUX Modern'},
        {'img': 'img/generiert/wappen_wattens_modern_qwen.png', 'label': 'Qwen Modern'},
        {'img': 'img/generiert/wappen_wattens_classic_flux.png', 'label': 'FLUX Klassisch'},
        {'img': 'img/generiert/wappen_wattens_classic_qwen.png', 'label': 'Qwen Klassisch'},
        {'img': 'img/generiert/wappen_wattens_tiroltourismus_flux.png', 'label': 'FLUX Tirol-Tourismus'},
        {'img': 'img/generiert/wappen_wattens_tiroltourismus_qwen.png', 'label': 'Qwen Tirol-Tourismus'},
    ],
}

def esc(s):
    return html_mod.escape(str(s), quote=False)

def sanitize_key(name):
    s = name.lower()
    s = s.replace('ä', 'ae').replace('ö', 'oe').replace('ü', 'ue').replace('ß', 'ss')
    s = re.sub(r'[^a-z0-9]+', '_', s).strip('_')
    return s

total_orte = 0
total_ki = 0
bezirk_html = ''

for bezirk in data['bezirke']:
    bname = bezirk['name']
    bkey = sanitize_key(bname)
    items_html = ''
    b_ort_total = 0
    b_ki_anzahl = 0
    
    for ort in bezirk['orte']:
        oname = ort['name']
        okey = sanitize_key(bkey + '_' + oname)
        variants = FERTIG.get(okey, [])
        b_ort_total += 1
        total_orte += 1
        
        if variants:
            b_ki_anzahl += len(variants)
            total_ki += len(variants)
            
            # Gen KI-Zellen bauen
            ki_cells = ''
            for v in variants:
                ki_cells += f'<div class="cl"><div class="l lm">{esc(v["label"])}</div><img src="{esc(v["img"])}" alt="{esc(oname)} {esc(v["label"])}" loading="lazy" onclick="lb(this.src,\'{esc(oname)} – {esc(v["label"])}\')"></div>'
            
            items_html += f'''<div class="cd done" data-b="{bkey}">
              <div class="on"><span class="cok">&#x2713;</span> {esc(oname)}</div>
              <div class="rw" style="grid-template-columns:1fr repeat({len(variants)},1fr)">
                <div class="cl"><div class="l lo">Original</div><img src="{esc(ort['img'])}" alt="{esc(oname)}" loading="lazy" onclick="lb(this.src,\'{esc(oname)} – Original\')"></div>
                {ki_cells}
              </div>
            </div>'''
        else:
            items_html += f'''<div class="cd wait" data-b="{bkey}">
              <div class="on"><span class="cok" style="opacity:.3">&#x23F3;</span> {esc(oname)}</div>
              <div class="rw">
                <div class="cl"><div class="l lo">Original</div><img src="{esc(ort['img'])}" alt="{esc(oname)}" loading="lazy" onclick="lb(this.src,'{esc(oname)} – Original')"></div>
                <div class="cl"><div class="l lm" style="color:#bbb">Modern</div><div class="ph"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 230"><defs><linearGradient id="b" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="#f5f0e8"/><stop offset="100%" stop-color="#e8e0d0"/></linearGradient></defs><rect width="200" height="230" fill="url(#b)" rx="12"/><path d="M100 25Q175 35 185 120Q195 190 160 220Q130 225 100 225Q70 225 40 220Q5 190 15 120Q25 35 100 25Z" fill="#e0d8c8" stroke="#c8c0b0" stroke-width="2"/><text x="100" y="115" text-anchor="middle" fill="#bbb" font-size="13">&#x26A1;</text><text x="100" y="150" text-anchor="middle" fill="#bbb" font-size="11" font-weight="600">Platzhalter</text><text x="100" y="165" text-anchor="middle" fill="#ccc" font-size="9">bald hier</text></svg></div></div>
              </div>
            </div>'''
    
    gemeinden_mit_ki = sum(1 for ort in bezirk['orte'] if FERTIG.get(sanitize_key(bkey + '_' + sanitize_key(ort['name'])), []))
    pct_color = '#10b981' if gemeinden_mit_ki == b_ort_total else '#f59e0b'
    bezirk_html += f'''<section id="s-{bkey}">
      <h2><span>{esc(bname)}</span><span class="pct" style="background:{pct_color};color:#fff">{gemeinden_mit_ki}/{b_ort_total}</span><span class="c">{b_ort_total} Gemeinden</span></h2>
      <div class="g" data-b="{bkey}">{items_html}</div>
    </section>'''

bezirk_opts = ''.join(f'<option value="{sanitize_key(b["name"])}">{esc(b["name"])}</option>' for b in data['bezirke'])
gemeinden_mit_ki = len([k for k in FERTIG if FERTIG[k]])

html = f'''<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Wappen Tirol – Original vs KI-generiert</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Segoe UI',system-ui,sans-serif;background:#f5f0e8;color:#1a1a2e}}
header{{background:linear-gradient(135deg,#1a1a2e,#2d2d44);color:#fff;padding:2rem 1rem;text-align:center;border-bottom:4px solid #D4A017}}
header h1{{font-size:2rem}}header h1 span{{color:#D4A017}}
header p{{opacity:.85;margin-top:.3rem}}
.badges{{margin-top:.6rem;display:flex;gap:.5rem;justify-content:center;flex-wrap:wrap}}
.badge{{padding:.3rem 1rem;border-radius:20px;font-size:.85rem}}
.bg-green{{background:#10b981;color:#fff}}.bg-amber{{background:#f59e0b;color:#fff}}.bg-dark{{background:#1a1a2e;color:#fff;border:1px solid #D4A017}}
.nav{{margin-top:.8rem}}.nav a{{color:#D4A017;text-decoration:none;margin:0 .5rem;border:1px solid #D4A017;padding:.3rem 1rem;border-radius:6px;font-size:.85rem;display:inline-block;margin-bottom:.3rem}}
.nav a:hover{{background:#D4A017;color:#1a1a2e}}
.c{{max-width:1600px;margin:0 auto;padding:2rem 1rem}}
.srch{{max-width:600px;margin:0 auto 2rem;display:flex;gap:.5rem;flex-wrap:wrap}}
.srch input{{flex:1;padding:.6rem 1rem;border:2px solid #e8e0d0;border-radius:8px;font-size:1rem;outline:none}}
.srch input:focus{{border-color:#D4A017}}
.srch select{{padding:.6rem;border:2px solid #e8e0d0;border-radius:8px;font-size:.9rem;outline:none;cursor:pointer}}
.fbtn{{padding:.6rem 1rem;border:none;border-radius:8px;cursor:pointer;font-weight:600;font-size:.85rem}}
.fbtn-a{{background:#e8e0d0;color:#1a1a2e}}.fbtn-y{{background:#10b981;color:#fff}}.fbtn-n{{background:#f59e0b;color:#fff}}
.fbtn.s{{transform:scale(.95);box-shadow:inset 0 2px 4px rgba(0,0,0,.2)}}
.info{{background:linear-gradient(135deg,#fef3c7,#fde68a);border:2px solid #f59e0b;border-radius:12px;padding:1.5rem 2rem;margin-bottom:2rem;display:flex;align-items:center;gap:1.5rem;flex-wrap:wrap}}
.info h3{{font-size:1.1rem;color:#92400e}}.info p{{color:#78350f;font-size:.9rem}}
.info .btn{{margin-left:auto;padding:.6rem 1.5rem;background:#f59e0b;color:#fff;border:none;border-radius:8px;font-weight:700;cursor:pointer;font-size:.9rem;white-space:nowrap}}
section{{margin-bottom:3rem;display:block}}
section h2{{font-size:1.5rem;padding:.8rem 1.2rem;background:#1a1a2e;color:#fff;border-radius:10px;margin-bottom:1rem;display:flex;align-items:center;gap:.8rem;position:sticky;top:0;z-index:10;font-weight:600}}
section h2 .c{{font-size:.85rem;opacity:.7;margin-left:auto;font-weight:400}}
section h2 .pct{{font-size:.8rem;padding:.15rem .6rem;border-radius:10px;font-weight:400}}
.g{{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:1rem}}
.cd{{background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,.06);border:2px solid transparent;transition:transform .2s}}
.cd:hover{{transform:translateY(-3px);box-shadow:0 6px 20px rgba(0,0,0,.12)}}
.cd.done{{border-color:#10b981}}.cd.wait{{border-color:#e8e0d0;opacity:.85}}
.cd .on{{padding:.6rem;text-align:center;font-weight:700;font-size:.85rem;background:#1a1a2e;color:#fff;display:flex;align-items:center;justify-content:center;gap:.5rem}}
.rw{{display:grid;grid-template-columns:1fr 1fr;gap:0}}
.cl{{padding:.5rem;text-align:center;min-width:0}}
.cl:first-child{{border-right:1px solid #e8e0d0}}
.cl .l{{font-size:.65rem;font-weight:600;text-transform:uppercase;letter-spacing:.5px;margin-bottom:.3rem;word-break:break-word}}
.cl .lo{{color:#C8102E}}.cl .lm{{color:#6c5ce7}}
.cl img{{width:100%;max-width:90px;height:auto;display:block;margin:0 auto;border-radius:4px;cursor:pointer}}
.lb{{display:none;position:fixed;z-index:999;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,.92);justify-content:center;align-items:center;cursor:pointer}}
.lb.s{{display:flex}}.lb img{{max-width:90%;max-height:90%;border-radius:8px}}
.lb .ll{{position:fixed;bottom:2rem;left:50%;transform:translateX(-50%);color:#fff;background:rgba(0,0,0,.6);padding:.5rem 1.5rem;border-radius:8px;font-size:.9rem;text-align:center}}
.ftr{{text-align:center;padding:2rem;color:#888;font-size:.85rem;border-top:1px solid #e8e0d0;margin-top:2rem}}
@media(max-width:768px){{.g{{grid-template-columns:repeat(auto-fill,minmax(180px,1fr))}}.cl img{{max-width:70px}}}}
@media(max-width:480px){{.g{{grid-template-columns:repeat(2,1fr)}}.cl img{{max-width:55px}}}}
</style>
</head>
<body>

<header>
  <h1>&#x1F3C1; Wappen <span>Tirol</span></h1>
  <p>Original (Wikipedia) vs <strong>KI-generiert</strong> — {gemeinden_mit_ki} Gemeinden mit {total_ki} KI-Varianten</p>
  <div class="badges">
    <span class="badge bg-green">{gemeinden_mit_ki} Gemeinden mit KI</span>
    <span class="badge bg-amber">{total_orte - gemeinden_mit_ki} ohne</span>
    <span class="badge bg-dark">{total_ki} KI-Bilder</span>
  </div>
  <div class="nav">
    <a href="index.html">&#x2190; Wappen-&Uuml;bersicht</a>
    <a href="generiert.html">&#x1F3A8; KI-Galerie</a>
  </div>
</header>

<div class="c">
  <div class="info">
    <div>
      <h3>&#x26A1; {gemeinden_mit_ki} von {total_orte} Gemeinden mit KI-Wappen</h3>
      <p>{total_ki} KI-generierte Varianten vorhanden (FLUX.2-pro + Qwen-Image-Edit). Der Rest wartet auf API-Guthaben.</p>
    </div>
    <span class="btn" onclick="alert('SiliconFlow aufladen. Danach python batch_flux_modern.py ausführen (ca. 15 Min).')">&#x1F50B; Aufladen</span>
  </div>

  <div class="srch">
    <input type="text" id="q" placeholder="&#x1F50D; Gemeinde suchen&#x2026;" oninput="filt()">
    <select id="b" onchange="filt()">
      <option value="">Alle Bezirke</option>
      {bezirk_opts}
    </select>
    <button class="fbtn fbtn-a s" onclick="setF('all',this)">Alle</button>
    <button class="fbtn fbtn-y" onclick="setF('yes',this)">Mit KI &#x2713;</button>
    <button class="fbtn fbtn-n" onclick="setF('no',this)">Ohne &#x23F3;</button>
  </div>

  <div id="g">
{bezirk_html}
  </div>
</div>

<div class="lb" id="lb" onclick="this.classList.remove('s')">
  <img id="lbi" src="" alt="">
  <div class="ll" id="lbl"></div>
</div>

<div class="ftr">Original: Wikipedia (CC BY-SA 4.0) · KI: FLUX.2-pro & Qwen-Image-Edit (SiliconFlow)</div>

<script>
let f = 'all';
function setF(v,b) {{ f=v; document.querySelectorAll('.fbtn').forEach(x=>x.classList.remove('s')); b.classList.add('s'); filt(); }}
function filt() {{
  const q = document.getElementById('q').value.toLowerCase();
  const fb = document.getElementById('b').value;
  document.querySelectorAll('.cd').forEach(c => {{
    const txt = c.querySelector('.on').textContent.toLowerCase();
    const ok = c.classList.contains('done');
    const bk = c.dataset.b;
    const m = (!q || txt.includes(q)) && (!fb || bk === fb) && (f==='all' || (f==='yes' && ok) || (f==='no' && !ok));
    c.style.display = m ? '' : 'none';
  }});
  document.querySelectorAll('section').forEach(s => {{
    s.style.display = [...s.querySelectorAll('.cd')].some(c => c.style.display !== 'none') ? '' : 'none';
  }});
}}
function lb(s,l) {{ document.getElementById('lbi').src=s; document.getElementById('lbl').textContent=l; document.getElementById('lb').classList.add('s'); }}
document.addEventListener('keydown', function(e) {{ if(e.key==='Escape') document.getElementById('lb').classList.remove('s'); }});
</script>
</body>
</html>'''

with open('vergleich.html', 'w', encoding='utf-8') as f:
    f.write(html)

print(f"✅ vergleich.html ({len(html)} bytes)")
print(f"   {total_orte} Gemeinden, {gemeinden_mit_ki} mit KI, {total_ki} KI-Bilder insgesamt")
print(f"   Sichtbar: Innsbruck (6), Götzens (6), Wattens (6) = 18 KI-Varianten")

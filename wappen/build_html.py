#!/usr/bin/env python3
"""Build final index.html with embedded JSON data (no CORS issues)."""
import json, os

# Read the page data
with open('wappen_page_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Add style variants for Innsbruck Stadtwappen
# This data structure is reproducible for any other coat of arms
# Groups: each style-key has model-subkeys (SVG, FLUX, Qwen) 
STYLE_VARIANTS = {
    "Innsbruck Stadt": {
        "original": {
            "name": "Original",
            "img": "img/bezirke/innsbruck_stadt.png",
            "desc": "Original-Wappen aus Wikipedia, CC BY-SA 4.0",
            "group": "original"
        },
        "flux_classic": {
            "name": "FLUX · Klassisch",
            "img": "img/generiert/wappen_innsbruck_classic_flux.png",
            "desc": "FLUX.2-pro — traditionell-heraldisch",
            "group": "flux"
        },
        "flux_modern": {
            "name": "FLUX · Modern",
            "img": "img/generiert/wappen_innsbruck_modern_flux.png",
            "desc": "FLUX.2-pro — minimalistisch-geometrisch",
            "group": "flux"
        },
        "flux_tirol": {
            "name": "FLUX · Tirol-Tourismus",
            "img": "img/generiert/wappen_innsbruck_tiroltourismus_flux.png",
            "desc": "FLUX.2-pro — warme Gold-Rot-Töne, alpines Branding",
            "group": "flux"
        },
        "qwen_classic": {
            "name": "Qwen · Klassisch",
            "img": "img/generiert/wappen_innsbruck_classic_qwen.png",
            "desc": "Qwen-Image-Edit — traditionell-heraldisch",
            "group": "qwen"
        },
        "qwen_modern": {
            "name": "Qwen · Modern",
            "img": "img/generiert/wappen_innsbruck_modern_qwen.png",
            "desc": "Qwen-Image-Edit — minimalistisch-geometrisch",
            "group": "qwen"
        },
        "qwen_tirol": {
            "name": "Qwen · Tirol-Tourismus",
            "img": "img/generiert/wappen_innsbruck_tiroltourismus_qwen.png",
            "desc": "Qwen-Image-Edit — warme Gold-Rot-Töne, alpines Branding",
            "group": "qwen"
        }
    }
}

# Inject style variants into the data
for b in data['bezirke']:
    if b['name'] in STYLE_VARIANTS:
        b['styles'] = STYLE_VARIANTS[b['name']]

# JSON as inline JavaScript
json_str = json.dumps(data, ensure_ascii=False)

# Count
total = sum(len(b['orte']) for b in data['bezirke'])

html = f'''<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Wappen Tirol – Bezirke & Gemeinden</title>
<style>
  :root {{
    --rot: #C8102E;
    --weiss: #FFFFFF;
    --gold: #D4A017;
    --dunkel: #1a1a2e;
    --hell: #f5f0e8;
    --grau: #e8e0d0;
  }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
    background: var(--hell);
    color: var(--dunkel);
    min-height: 100vh;
  }}
  header {{
    background: linear-gradient(135deg, var(--dunkel) 0%, #2d2d44 100%);
    color: var(--weiss);
    padding: 2rem 1rem;
    text-align: center;
    border-bottom: 4px solid var(--gold);
  }}
  header h1 {{ font-size: 2.5rem; font-weight: 700; letter-spacing: 1px; }}
  header h1 span {{ color: var(--gold); }}
  header p {{ margin-top: 0.5rem; opacity: 0.85; font-size: 1.1rem; }}
  header .count-badge {{
    display: inline-block;
    margin-top: 0.5rem;
    padding: 0.3rem 1rem;
    background: var(--rot);
    border-radius: 20px;
    font-size: 0.9rem;
  }}
  .back-btn {{
    display: none; position: fixed; top: 1rem; left: 1rem; z-index: 100;
    padding: 0.6rem 1.2rem; background: var(--dunkel); color: var(--weiss);
    border: 2px solid var(--gold); border-radius: 8px; cursor: pointer;
    font-size: 1rem; font-weight: 600; transition: all 0.2s;
  }}
  .back-btn:hover {{ background: var(--gold); color: var(--dunkel); }}
  .back-btn.visible {{ display: block; }}
  .container {{ max-width: 1400px; margin: 0 auto; padding: 2rem 1rem; }}
  #bezirk-view h2 {{ text-align: center; font-size: 1.8rem; margin-bottom: 2rem; color: var(--dunkel); }}
  .bezirk-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 1.5rem;
  }}
  .bezirk-card {{
    background: var(--weiss); border-radius: 16px; overflow: hidden;
    box-shadow: 0 4px 15px rgba(0,0,0,0.08); cursor: pointer;
    transition: all 0.3s ease; border: 2px solid transparent;
  }}
  .bezirk-card:hover {{
    transform: translateY(-6px); box-shadow: 0 10px 30px rgba(0,0,0,0.15);
    border-color: var(--gold);
  }}
  .bezirk-card .img-wrap {{
    height: 200px; display: flex; align-items: center; justify-content: center;
    background: var(--grau); padding: 1.5rem;
  }}
  .bezirk-card .img-wrap img {{ max-height: 160px; max-width: 100%; object-fit: contain; }}
  .bezirk-card .name {{ padding: 1rem; text-align: center; font-size: 1.2rem; font-weight: 700; background: var(--weiss); border-top: 2px solid var(--grau); }}
  .bezirk-card .count {{ text-align: center; padding: 0 1rem 1rem; font-size: 0.85rem; color: #666; }}
  #ort-view {{ display: none; }}
  #ort-view h2 {{ text-align: center; font-size: 1.8rem; margin-bottom: 0.5rem; }}
  #ort-view .subtitle {{ text-align: center; color: #666; margin-bottom: 1.5rem; }}

  /* Style Switcher — reproducibles Muster für beliebige Wappen */
  .style-switcher {{
    display: flex; flex-wrap: wrap; gap: 0.5rem;
    justify-content: center; margin-bottom: 2rem;
    padding: 1rem; background: var(--weiss);
    border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  }}
  .style-btn {{
    padding: 0.5rem 1rem; border: 2px solid var(--grau);
    border-radius: 8px; background: var(--weiss);
    cursor: pointer; font-size: 0.85rem; font-weight: 600;
    transition: all 0.2s; color: var(--dunkel);
  }}
  .style-btn:hover {{ border-color: var(--gold); }}
  .style-btn.active {{
    border-color: var(--rot); background: var(--rot);
    color: var(--weiss);
  }}
  .style-desc {{
    width: 100%; text-align: center;
    font-size: 0.8rem; color: #888; margin-top: 0.25rem;
  }}
  .style-preview-wrap {{
    display: flex; justify-content: center; margin-bottom: 2rem;
  }}
  .style-preview {{
    max-width: 280px; width: 100%;
    background: var(--weiss); border-radius: 16px;
    padding: 1.5rem; box-shadow: 0 4px 15px rgba(0,0,0,0.08);
  }}
  .style-preview img {{ width: 100%; height: auto; display: block; }}

  .ort-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
    gap: 1rem;
  }}
  .ort-card {{
    background: var(--weiss); border-radius: 12px; overflow: hidden;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06); transition: all 0.2s ease; text-align: center;
  }}
  .ort-card:hover {{ transform: translateY(-3px); box-shadow: 0 6px 20px rgba(0,0,0,0.12); }}
  .ort-card .img-wrap {{
    height: 130px; display: flex; align-items: center; justify-content: center;
    background: var(--grau); padding: 0.8rem;
  }}
  .ort-card .img-wrap img {{ max-height: 110px; max-width: 100%; object-fit: contain; }}
  .ort-card .name {{
    padding: 0.6rem; font-size: 0.85rem; font-weight: 600; background: var(--weiss);
    min-height: 2.5rem; display: flex; align-items: center; justify-content: center; line-height: 1.2;
  }}
  footer {{ text-align: center; padding: 2rem; color: #888; font-size: 0.85rem; border-top: 1px solid var(--grau); margin-top: 2rem; }}
  footer a {{ color: var(--rot); text-decoration: none; }}
  @media (max-width: 768px) {{
    header h1 {{ font-size: 1.8rem; }}
    .bezirk-grid {{ grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 1rem; }}
    .ort-grid {{ grid-template-columns: repeat(auto-fill, minmax(110px, 1fr)); gap: 0.8rem; }}
    .bezirk-card .img-wrap {{ height: 160px; }}
    .ort-card .img-wrap {{ height: 100px; }}
    .container {{ padding: 1rem; }}
  }}
  @media (max-width: 480px) {{
    .bezirk-grid {{ grid-template-columns: repeat(2, 1fr); gap: 0.8rem; }}
    .ort-grid {{ grid-template-columns: repeat(2, 1fr); gap: 0.6rem; }}
    .bezirk-card .img-wrap {{ height: 130px; }}
  }}
</style>
</head>
<body>

<button class="back-btn" id="backBtn" onclick="showBezirke()">← Zurück zur Übersicht</button>

<header>
  <h1>🏁 Wappen <span>Tirol</span></h1>
  <p>Alle Bezirks- und Gemeindewappen des Landes Tirol</p>
  <div class="count-badge">{len(data['bezirke'])} Bezirke · {total} Gemeinden</div>
  <p style="margin-top: 0.6rem">
    <a href="generiert.html" style="color:var(--gold);text-underline-offset:3px">
      🎨 18 KI-generierte Wappen-Varianten ansehen →
    </a>
  </p>
</header>

<div class="container">
  <div id="bezirk-view">
    <h2>🏛️ Bezirke</h2>
    <div class="bezirk-grid" id="bezirkGrid"></div>
  </div>
  <div id="ort-view">
    <h2 id="ortTitle"></h2>
    <p class="subtitle" id="ortSubtitle"></p>
    <!-- Style Switcher (generisches Muster) -->
    <div id="styleSection" style="display:none">
      <div class="style-preview-wrap">
        <div class="style-preview">
          <img id="stylePreviewImg" src="" alt="Wappen-Stil">
        </div>
      </div>
      <div class="style-switcher" id="styleSwitcher">
        <!-- wird dynamisch befüllt -->
        <div class="style-desc" id="styleDesc"></div>
      </div>
    </div>
    <div class="ort-grid" id="ortGrid"></div>
  </div>
</div>

<footer>
  Daten von <a href="https://de.wikipedia.org/wiki/Liste_der_Wappen_in_Tirol" target="_blank">Wikipedia (Liste der Wappen in Tirol)</a>
  · Wappen unter <a href="https://creativecommons.org/licenses/by-sa/4.0/deed.de" target="_blank">CC BY-SA 4.0</a>
</footer>

<script>
const DATA = {json_str};

let currentStyleIdx = null;

function renderBezirke() {{
  const grid = document.getElementById('bezirkGrid');
  grid.innerHTML = '';
  DATA.bezirke.forEach((bezirk, idx) => {{
    const card = document.createElement('div');
    card.className = 'bezirk-card';
    card.onclick = () => showOrte(idx);
    card.innerHTML = `
      <div class="img-wrap">
        <img src="${{bezirk.img || (bezirk.orte.length > 0 ? bezirk.orte[0].img : '')}}"
             alt="${{bezirk.name}}" loading="lazy"
             onerror="this.parentElement.innerHTML='<div style=\\'font-size:3rem\\'>🏁</div>'">
      </div>
      <div class="name">${{bezirk.name}}</div>
      <div class="count">${{bezirk.orte.length}} Gemeinden</div>`;
    grid.appendChild(card);
  }});
}}

function showOrte(idx) {{
  const bezirk = DATA.bezirke[idx];
  document.getElementById('ortTitle').textContent = '🏁 ' + bezirk.name;
  document.getElementById('ortSubtitle').textContent = bezirk.orte.length + ' Gemeinden';

  // Style Switcher — funktioniert für jedes Wappen mit styles-Daten
  const styleSection = document.getElementById('styleSection');
  if (bezirk.styles) {{
    styleSection.style.display = 'block';
    const keys = Object.keys(bezirk.styles);
    currentStyleIdx = idx;
    switchStyle(keys[0]); // first style active
    renderStyleSwitcher(bezirk);
  }} else {{
    styleSection.style.display = 'none';
  }}

  const grid = document.getElementById('ortGrid');
  grid.innerHTML = '';
  bezirk.orte.forEach(ort => {{
    const card = document.createElement('div');
    card.className = 'ort-card';
    card.innerHTML = `
      <div class="img-wrap">
        <img src="${{ort.img}}" alt="${{ort.name}}" loading="lazy"
             onerror="this.parentElement.innerHTML='<div style=\\'font-size:2rem\\'>🏁</div>'">
      </div>
      <div class="name">${{ort.name}}</div>`;
    grid.appendChild(card);
  }});
  document.getElementById('bezirk-view').style.display = 'none';
  document.getElementById('ort-view').style.display = 'block';
  document.getElementById('backBtn').classList.add('visible');
  window.scrollTo(0, 0);
}}

function renderStyleSwitcher(bezirk) {{
  const container = document.getElementById('styleSwitcher');
  const descDiv = document.getElementById('styleDesc');
  container.innerHTML = '';
  container.appendChild(descDiv);

  // Group order: original, svg, flux, qwen
  const groupOrder = ['original', 'flux', 'qwen'];
  const groupLabels = {{
    original: '',
    flux: '━━ FLUX.2-pro ━━',
    qwen: '━━ Qwen-Image-Edit ━━'
  }};

  // Group entries by their group field
  const groups = {{}};
  Object.entries(bezirk.styles).forEach(([key, style]) => {{
    const g = style.group || 'other';
    if (!groups[g]) groups[g] = [];
    groups[g].push({{key, style}});
  }});

  groupOrder.forEach(g => {{
    if (!groups[g]) return;
    // Group label (skip for 'original')
    if (groupLabels[g]) {{
      const label = document.createElement('div');
      label.style.cssText = 'width:100%;text-align:center;font-size:0.75rem;color:#999;padding:0.4rem 0 0.2rem;letter-spacing:1px;';
      label.textContent = groupLabels[g];
      container.insertBefore(label, descDiv);
    }}
    groups[g].forEach(({{key, style}}) => {{
      const btn = document.createElement('button');
      btn.className = 'style-btn' + (g === 'original' ? '' : '');
      btn.textContent = style.name;
      btn.onclick = () => switchStyle(key);
      btn.dataset.key = key;
      container.insertBefore(btn, descDiv);
    }});
  }});
}}

function switchStyle(key) {{
  const bezirk = DATA.bezirke[currentStyleIdx];
  const style = bezirk.styles[key];
  if (!style) return;

  document.getElementById('stylePreviewImg').src = style.img;
  document.getElementById('stylePreviewImg').alt = style.name + ' — ' + bezirk.name;
  document.getElementById('styleDesc').textContent = style.desc;

  // Mark active button
  document.querySelectorAll('.style-btn').forEach(btn => {{
    btn.classList.toggle('active', btn.dataset.key === key);
  }});
}}

function showBezirke() {{
  document.getElementById('bezirk-view').style.display = 'block';
  document.getElementById('ort-view').style.display = 'none';
  document.getElementById('backBtn').classList.remove('visible');
  window.scrollTo(0, 0);
}}

renderBezirke();
</script>
</body>
</html>'''

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print(f"✅ index.html erstellt ({os.path.getsize('index.html')} bytes)")
print(f"   {len(data['bezirke'])} Bezirke, {total} Gemeinden")

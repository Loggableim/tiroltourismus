#!/usr/bin/env python3
"""Build vergleich.html with embedded JSON (no CORS)."""
import json, os, re

# Read page data
with open('wappen_page_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Fertige KI-Bilder (hartcodiert, wächst mit der Zeit)
FERTIG = {
    'innsbruck_stadt_innsbruck': 'img/generiert/wappen_innsbruck_modern_qwen.png',
    'innsbruck_land_gotzens': 'img/generiert/wappen_gotzens_modern_flux.png',
    'innsbruck_land_wattens': 'img/generiert/wappen_wattens_modern_flux.png',
}

# Build allData array
all_entries = []
for bezirk in data['bezirke']:
    for ort in bezirk['orte']:
        key = re.sub(r'[^a-z0-9]+', '_', (bezirk['name'] + '_' + ort['name']).lower()).strip('_')
        has_modern = json.dumps(FERTIG.get(key, None))
        all_entries.append({
            'bezirk': bezirk['name'],
            'ort': ort['name'],
            'original': ort['img'],
            'modern': FERTIG.get(key, None),
        })

all_data_json = json.dumps(all_entries, ensure_ascii=False)
total = len(all_entries)
ready = len(FERTIG)

# Build unique bezirk list for filter
bezirk_list = sorted(set(e['bezirk'] for e in all_entries))
bezirk_opts = ''.join(f'<option value="{b}">{b}</option>' for b in bezirk_list)

html = f'''<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Wappen Tirol – Original vs Modern (Vorschau)</title>
<style>
  :root {{
    --rot: #C8102E; --weiss: #FFFFFF; --gold: #D4A017;
    --dunkel: #1a1a2e; --hell: #f5f0e8; --grau: #e8e0d0;
  }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: 'Segoe UI', system-ui, sans-serif;
    background: var(--hell); color: var(--dunkel);
  }}
  header {{
    background: linear-gradient(135deg, var(--dunkel), #2d2d44);
    color: var(--weiss); padding: 2rem 1rem; text-align: center;
    border-bottom: 4px solid var(--gold);
  }}
  header h1 {{ font-size: 2rem; }}
  header h1 span {{ color: var(--gold); }}
  header p {{ opacity: 0.85; margin-top: 0.3rem; }}
  header .badges {{ margin-top: 0.6rem; display: flex; gap: 0.5rem; justify-content: center; flex-wrap: wrap; }}
  header .badge {{ padding: 0.3rem 1rem; border-radius: 20px; font-size: 0.85rem; }}
  .badge-ready {{ background: #10b981; color: #fff; }}
  .badge-pending {{ background: #f59e0b; color: #fff; }}
  .badge-info {{ background: var(--dunkel); color: var(--weiss); border: 1px solid var(--gold); }}
  .nav-links {{ margin-top: 0.8rem; }}
  .nav-links a {{
    color: var(--gold); text-decoration: none; margin: 0 0.5rem;
    border: 1px solid var(--gold); padding: 0.3rem 1rem;
    border-radius: 6px; font-size: 0.85rem; transition: all 0.2s;
  }}
  .nav-links a:hover {{ background: var(--gold); color: var(--dunkel); }}
  .container {{ max-width: 1600px; margin: 0 auto; padding: 2rem 1rem; }}
  .bezirk-section {{ margin-bottom: 3rem; }}
  .bezirk-section h2 {{
    font-size: 1.5rem; padding: 0.8rem 1.2rem;
    background: var(--dunkel); color: var(--weiss);
    border-radius: 10px; margin-bottom: 1rem;
    display: flex; align-items: center; gap: 0.8rem;
    position: sticky; top: 0; z-index: 10;
  }}
  .bezirk-section h2 .b-count {{ font-size: 0.85rem; font-weight: 400; opacity: 0.7; margin-left: auto; }}
  .bezirk-section h2 .b-progress {{ font-size: 0.8rem; font-weight: 400; opacity: 0.8; margin-left: 0.5rem; padding: 0.15rem 0.6rem; border-radius: 10px; }}
  .vergleich-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
    gap: 1rem;
  }}
  .vergleich-card {{
    background: var(--weiss); border-radius: 12px; overflow: hidden;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06); transition: transform 0.2s;
    border: 2px solid transparent;
  }}
  .vergleich-card:hover {{ transform: translateY(-3px); box-shadow: 0 6px 20px rgba(0,0,0,0.12); }}
  .vergleich-card.fertig {{ border-color: #10b981; }}
  .vergleich-card.aussteht {{ border-color: var(--grau); opacity: 0.85; }}
  .vergleich-card .ort-name {{
    padding: 0.6rem; text-align: center; font-weight: 700; font-size: 0.85rem;
    background: var(--dunkel); color: var(--weiss);
    display: flex; align-items: center; justify-content: center; gap: 0.5rem;
  }}
  .vergleich-row {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0;
  }}
  .vergleich-item {{ padding: 0.5rem; text-align: center; }}
  .vergleich-item:first-child {{ border-right: 1px solid var(--grau); }}
  .vergleich-item .label {{ font-size: 0.65rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 0.3rem; }}
  .vergleich-item .label.orig {{ color: var(--rot); }}
  .vergleich-item .label.qwen {{ color: #6c5ce7; }}
  .vergleich-item img {{ width: 100%; max-width: 110px; height: auto; display: block; margin: 0 auto; border-radius: 4px; cursor: pointer; transition: transform 0.15s; }}
  .vergleich-item img:hover {{ transform: scale(1.15); }}
  .search-bar {{
    max-width: 600px; margin: 0 auto 2rem;
    display: flex; gap: 0.5rem; flex-wrap: wrap;
  }}
  .search-bar input {{
    flex: 1; padding: 0.6rem 1rem; border: 2px solid var(--grau);
    border-radius: 8px; font-size: 1rem; outline: none;
  }}
  .search-bar input:focus {{ border-color: var(--gold); }}
  .search-bar select {{
    padding: 0.6rem; border: 2px solid var(--grau);
    border-radius: 8px; font-size: 0.9rem; outline: none; cursor: pointer;
  }}
  .search-bar .filter-btn {{
    padding: 0.6rem 1rem; border: none; border-radius: 8px;
    cursor: pointer; font-weight: 600; font-size: 0.85rem; transition: all 0.2s;
  }}
  .filter-btn.all {{ background: var(--grau); color: var(--dunkel); }}
  .filter-btn.fertig {{ background: #10b981; color: #fff; }}
  .filter-btn.aus {{ background: #f59e0b; color: #fff; }}
  .filter-btn.active {{ transform: scale(0.95); box-shadow: inset 0 2px 4px rgba(0,0,0,0.2); }}
  .lightbox {{
    display: none; position: fixed; z-index: 999; top: 0; left: 0;
    width: 100%; height: 100%; background: rgba(0,0,0,0.92);
    justify-content: center; align-items: center; cursor: pointer;
  }}
  .lightbox.show {{ display: flex; }}
  .lightbox img {{ max-width: 90%; max-height: 90%; border-radius: 8px; }}
  .lightbox .lb-label {{
    position: fixed; bottom: 2rem; left: 50%; transform: translateX(-50%);
    color: #fff; background: rgba(0,0,0,0.6); padding: 0.5rem 1.5rem; border-radius: 8px; font-size: 0.9rem;
  }}
  .info-banner {{
    background: linear-gradient(135deg, #fef3c7, #fde68a);
    border: 2px solid #f59e0b; border-radius: 12px;
    padding: 1.5rem 2rem; margin-bottom: 2rem;
    display: flex; align-items: center; gap: 1.5rem; flex-wrap: wrap;
  }}
  .info-banner h3 {{ font-size: 1.1rem; color: #92400e; }}
  .info-banner p {{ color: #78350f; font-size: 0.9rem; }}
  .info-banner .btn {{
    margin-left: auto; padding: 0.6rem 1.5rem;
    background: #f59e0b; color: #fff; border: none; border-radius: 8px;
    font-weight: 700; cursor: pointer; font-size: 0.9rem;
    text-decoration: none; white-space: nowrap;
  }}
  .info-banner .btn:hover {{ background: #d97706; }}
  footer {{ text-align: center; padding: 2rem; color: #888; font-size: 0.85rem; border-top: 1px solid var(--grau); }}
  @media (max-width: 768px) {{ .vergleich-grid {{ grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); }} .vergleich-item img {{ max-width: 80px; }} }}
  @media (max-width: 480px) {{ .vergleich-grid {{ grid-template-columns: repeat(2, 1fr); }} .vergleich-item img {{ max-width: 60px; }} }}
</style>
</head>
<body>

<header>
  <h1>🏁 Wappen <span>Tirol</span></h1>
  <p>Original (Wikipedia) vs <strong>Modern — FLUX.2-pro / Qwen-Image-Edit</strong></p>
  <div class="badges">
    <span class="badge badge-ready">{ready} fertig</span>
    <span class="badge badge-pending">{total - ready} Platzhalter</span>
    <span class="badge badge-info">{total} Gemeinden</span>
  </div>
  <div class="nav-links">
    <a href="index.html">← Wappen-Übersicht</a>
    <a href="generiert.html">🎨 KI-Galerie</a>
  </div>
</header>

<div class="container">

  <div class="info-banner" id="infoBanner">
    <div>
      <h3>⚡ {ready} von {total} Wappen generiert</h3>
      <p>{'Alle Gemeinden sind fertig! 🎉' if ready == total else f'Es fehlen noch {total - ready}. SiliconFlow-Konto aufladen für den Rest.'}</p>
    </div>
    <span class="btn" onclick="alert('SiliconFlow-Konto aufladen (ca. $5-10 für alle 276).\\n\\nDann `python batch_flux_modern.py` ausführen —~15 Minuten.')">
      🔋 Aufladen & Generieren
    </span>
  </div>

  <div class="search-bar">
    <input type="text" id="searchInput" placeholder="🔍 Gemeinde suchen…" oninput="filterGemeinden()">
    <select id="filterBezirk" onchange="filterGemeinden()">
      <option value="">Alle Bezirke</option>
      {bezirk_opts}
    </select>
    <button class="filter-btn all active" onclick="setFilter('all', this)" id="fAll">Alle</button>
    <button class="filter-btn fertig" onclick="setFilter('fertig', this)" id="fFertig">Fertig ✓</button>
    <button class="filter-btn aus" onclick="setFilter('aus', this)" id="fAus">Platzhalter ⏳</button>
  </div>

  <div id="gallery"></div>
</div>

<div class="lightbox" id="lightbox" onclick="closeLightbox()">
  <img id="lbImg" src="" alt="">
  <div class="lb-label" id="lbLabel"></div>
</div>

<footer>
  Original-Wappen: Wikipedia (CC BY-SA 4.0) · Ki-Versionen: FLUX.2-pro & Qwen-Image-Edit (SiliconFlow)
</footer>

<script>
// Daten inline (kein CORS-Problem!)
const ALL_DATA = {all_data_json};
const BEZIRKE = {json.dumps(bezirk_list, ensure_ascii=False)};
let currentFilter = 'all';

function updateBadges() {{
  const ready = ALL_DATA.filter(d => d.modern).length;
  const total = ALL_DATA.length;
  document.getElementById('countReady').textContent = ready + ' fertig';
  document.getElementById('countPending').textContent = (total - ready) + ' Platzhalter';
  const h3 = document.querySelector('#infoBanner h3');
  if (h3) h3.textContent = ready === total ? '🎉 Alle fertig!' : `⚡ ${{ready}} von ${{total}} Wappen generiert`;
}}

function setFilter(filter, btn) {{
  currentFilter = filter;
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  renderAll();
}}

function renderAll() {{
  const container = document.getElementById('gallery');
  container.innerHTML = '';
  const searchText = document.getElementById('searchInput').value.toLowerCase();
  const filterBezirk = document.getElementById('filterBezirk').value;

  const groups = {{}};
  ALL_DATA.forEach(d => {{
    if (!groups[d.bezirk]) groups[d.bezirk] = [];
    groups[d.bezirk].push(d);
  }});

  Object.entries(groups).forEach(([bezirkName, items]) => {{
    if (filterBezirk && bezirkName !== filterBezirk) return;

    let filtered = items.filter(d => d.ort.toLowerCase().includes(searchText));
    if (currentFilter === 'fertig') filtered = filtered.filter(d => d.modern);
    else if (currentFilter === 'aus') filtered = filtered.filter(d => !d.modern);
    if (filtered.length === 0) return;

    const readyCount = filtered.filter(d => d.modern).length;

    const section = document.createElement('div');
    section.className = 'bezirk-section';
    section.innerHTML = `<h2>
      <span>${{bezirkName}}</span>
      <span class="b-progress" style="background:${{readyCount === filtered.length ? '#10b981' : '#f59e0b'}};color:#fff;">${{readyCount}}/${{filtered.length}}</span>
      <span class="b-count">${{filtered.length}} Gemeinden</span>
    </h2>`;

    const grid = document.createElement('div');
    grid.className = 'vergleich-grid';

    filtered.forEach(item => {{
      const card = document.createElement('div');
      card.className = 'vergleich-card ' + (item.modern ? 'fertig' : 'aussteht');

      if (item.modern) {{
        card.innerHTML = `
          <div class="ort-name"><span class="check">✓</span> ${{item.ort}}</div>
          <div class="vergleich-row">
            <div class="vergleich-item">
              <div class="label orig">Original</div>
              <img src="${{item.original}}" alt="${{item.ort}}" loading="lazy"
                   onclick="openLightbox(this.src, '${{item.ort}} – Original')">
            </div>
            <div class="vergleich-item">
              <div class="label qwen">Modern</div>
              <img src="${{item.modern}}" alt="${{item.ort}} Modern" loading="lazy"
                   onclick="openLightbox(this.src, '${{item.ort}} – Modern')">
            </div>
          </div>`;
      }} else {{
        card.innerHTML = `
          <div class="ort-name"><span style="opacity:0.3">⏳</span> ${{item.ort}}</div>
          <div class="vergleich-row">
            <div class="vergleich-item">
              <div class="label orig">Original</div>
              <img src="${{item.original}}" alt="${{item.ort}}" loading="lazy"
                   onclick="openLightbox(this.src, '${{item.ort}} – Original')">
            </div>
            <div class="vergleich-item">
              <div class="label qwen" style="color:#bbb">Modern</div>
              <div class="placeholder">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 230" width="200" height="230">
                  <defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="#f5f0e8"/><stop offset="100%" stop-color="#e8e0d0"/></linearGradient></defs>
                  <rect width="200" height="230" fill="url(#bg)" rx="12" ry="12"/>
                  <path d="M100 25 Q175 35 185 120 Q195 190 160 220 Q130 225 100 225 Q70 225 40 220 Q5 190 15 120 Q25 35 100 25Z" fill="#e0d8c8" stroke="#c8c0b0" stroke-width="2"/>
                  <text x="100" y="115" text-anchor="middle" fill="#bbb" font-size="13">⚡</text>
                  <text x="100" y="150" text-anchor="middle" fill="#bbb" font-size="11" font-weight="600">Platzhalter</text>
                  <text x="100" y="165" text-anchor="middle" fill="#ccc" font-size="9">bald hier</text>
                </svg>
              </div>
            </div>
          </div>`;
      }}
      grid.appendChild(card);
    }});
    section.appendChild(grid);
    container.appendChild(section);
  }});
}}

function filterGemeinden() {{ renderAll(); }}
function openLightbox(src, label) {{
  document.getElementById('lbImg').src = src;
  document.getElementById('lbLabel').textContent = label;
  document.getElementById('lightbox').classList.add('show');
}}
function closeLightbox() {{ document.getElementById('lightbox').classList.remove('show'); }}
document.addEventListener('keydown', e => {{ if (e.key === 'Escape') closeLightbox(); }});

updateBadges();
renderAll();
</script>
</body>
</html>'''

with open('vergleich.html', 'w', encoding='utf-8') as f:
    f.write(html)

print(f"✅ vergleich.html erstellt ({len(html)} bytes)")
print(f"   {total} Gemeinden, {ready} fertig, {total - ready} Platzhalter")

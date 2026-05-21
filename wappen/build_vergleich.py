#!/usr/bin/env python3
"""Build vergleich.html — auto-scan ALL folders, no hardcode."""
import json, os, re, html as html_mod

with open('wappen_page_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

def sanitize(name):
    s = name.lower().replace('ä','ae').replace('ö','oe').replace('ü','ue').replace('ß','ss')
    s = re.sub(r'[^a-z0-9]+', '_', s).strip('_')
    return s

# ─── Scan all images ──────────────────────────────────────────────
all_images = {}

for folder, source_label in [('img/generiert', 'API'), ('img/lokal', 'LOKAL')]:
    if not os.path.isdir(folder): continue
    for fn in sorted(os.listdir(folder)):
        fpath = os.path.join(folder, fn).replace('\\', '/')
        if not fn.endswith('.png'): continue
        
        core = fn.replace('.png','')
        if not core.startswith('wappen_'): continue
        core = core[7:]
        
        # Label
        label = 'Sonstige'
        if 'qwen' in fn.lower():
            if 'modern' in fn: label = 'Qwen Modern'
            elif 'classic' in fn or 'klassisch' in fn: label = 'Qwen Klassisch'
            elif 'tirol' in fn: label = 'Qwen Tirol-Tourismus'
            else: label = 'Qwen'
        elif 'flux' in fn.lower() and source_label == 'API':
            if 'modern' in fn: label = 'FLUX.2-pro Modern'
            elif 'classic' in fn or 'klassisch' in fn: label = 'FLUX.2-pro Klassisch'
            elif 'tirol' in fn: label = 'FLUX.2-pro Tirol-Tourismus'
            else: label = 'FLUX.2-pro'
        elif 'flux' in fn.lower():
            label = 'FLUX Dev Lokal'
        elif 'realvisxl' in fn.lower() or ('sdxl' not in fn.lower() and source_label == 'LOKAL'):
            label = 'RealVisXL Lokal'
        elif 'sdxl' in fn.lower():
            label = 'SDXL Lokal'
        else:
            label = 'Lokal'
        
        core_clean = re.sub(r'_(modern|classic|klassisch|tiroltourismus|flux|qwen|sdxl|realvisxl)(_\d{5}_)?$', '', core).strip('_')
        
        for bezirk in data['bezirke']:
            bkey = sanitize(bezirk['name'])
            for ort in bezirk['orte']:
                okey = sanitize(ort['name'])
                test_keys = [okey]
                if okey == 'goetzens': test_keys.append('gotzens')
                for tk in test_keys:
                    if core_clean == tk or core_clean.startswith(tk + '_') or core_clean.endswith('_' + tk):
                        ik = f"{bkey}_{okey}"
                        if ik not in all_images:
                            all_images[ik] = {'ort_name': ort['name'], 'bezirk_name': bezirk['name'], 'bezirk_key': bkey, 'imgs': []}
                        if not any(i['path'] == fpath for i in all_images[ik]['imgs']):
                            all_images[ik]['imgs'].append({'path': fpath, 'label': label, 'source': source_label})
                        break
                else: continue
                break
            else: continue
            break

LABEL_ORDER = ['FLUX.2-pro Modern','FLUX.2-pro Klassisch','FLUX.2-pro Tirol-Tourismus','Qwen Modern','Qwen Klassisch','Qwen Tirol-Tourismus','FLUX Dev Lokal','RealVisXL Lokal','SDXL Lokal','Lokal','Sonstige']
for v in all_images.values():
    # Deduplicate by label
    seen = set()
    deduped = []
    for img in v['imgs']:
        if img['label'] not in seen:
            seen.add(img['label'])
            deduped.append(img)
    # Also keep only the first occurrence of each label+source combination
    seen2 = set()
    final = []
    for img in deduped:
        key = (img['label'], img['source'])
        if key not in seen2:
            seen2.add(key)
            final.append(img)
    v['imgs'] = final
    v['imgs'].sort(key=lambda x: LABEL_ORDER.index(x['label']) if x['label'] in LABEL_ORDER else 999)

# Stats
total_orte = gemeinden_mit_ki = 0
api_gemeinden, lokal_gemeinden = set(), set()
for bezirk in data['bezirke']:
    bkey = sanitize(bezirk['name'])
    for ort in bezirk['orte']:
        total_orte += 1
        ik = f"{bkey}_{sanitize(ort['name'])}"
        if ik in all_images:
            gemeinden_mit_ki += 1
            if any(i['source']=='API' for i in all_images[ik]['imgs']): api_gemeinden.add(ik)
            if any(i['source']=='LOKAL' for i in all_images[ik]['imgs']): lokal_gemeinden.add(ik)

total_ki = sum(len(v['imgs']) for v in all_images.values())
H = html_mod.escape

def card(ort_name, bezirk_name, orig_img, bkey):
    okey, ik = sanitize(ort_name), f"{bkey}_{sanitize(ort_name)}"
    if ik not in all_images:
        if not orig_img: return None
        return f'<div class="c" data-n="{H(ort_name.lower())}" data-b="{H(bkey)}" data-k="0"><div class="ch"><span class="cn">{H(ort_name)}</span><span class="cb">⏳</span></div><div class="cv"><div class="vc"><img src="{H(orig_img)}" alt="{H(ort_name)}" loading="lazy" onclick="ol(this.src,\'{H(ort_name)}\')"><span class="vl">Original</span></div></div></div>'
    imgs, cols = all_images[ik]['imgs'], []
    if orig_img: cols.append(f'<div class="vc"><img src="{H(orig_img)}" alt="{H(ort_name)}" loading="lazy" onclick="ol(this.src,\'{H(ort_name)} – Original\')"><span class="vl">Original</span></div>')
    for img in imgs:
        cols.append(f'<div class="vc"><img src="{H(img["path"])}" alt="{H(ort_name)} {H(img["label"])}" loading="lazy" onclick="ol(this.src,\'{H(ort_name)} – {H(img["label"])}\')"><span class="vl">{H(img["label"])}</span></div>')
    return f'<div class="c" data-n="{H(ort_name.lower())}" data-b="{H(bkey)}" data-k="1"><div class="ch"><span class="cn">{H(ort_name)}</span><span class="cb">✓</span></div><div class="cv">{"".join(cols)}</div></div>'

sections = []
cards_ki = 0
for bezirk in data['bezirke']:
    bname, bkey, bimg = bezirk['name'], sanitize(bezirk['name']), bezirk.get('img','')
    cards, bt, bk = [], 0, 0
    for ort in bezirk['orte']:
        c = card(ort['name'], bname, ort.get('img','') or bimg, bkey)
        if c:
            cards.append(c); bt += 1
            if f"{bkey}_{sanitize(ort['name'])}" in all_images: bk += 1; cards_ki += 1
    if cards:
        sections.append(f'<section class="bs" data-b="{H(bkey)}"><h2>{H(bname)} <span class="bc">{bk}/{bt}</span></h2><div class="cg">{"".join(cards)}</div></section>')

html = f'''<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Wappenvergleich Tirol – Original vs KI</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#0c0e14;color:#e0e0e0;}}
.hdr{{background:linear-gradient(135deg,#1a1d2e,#0f111a);padding:24px 32px;border-bottom:1px solid #2a2d3a;}}
.hdr h1{{font-size:1.6rem;color:#fff;}} .hdr h1 small{{font-size:.9rem;color:#888;font-weight:400;}}
.st{{display:flex;gap:16px;margin-top:8px;flex-wrap:wrap;}}
.st span{{background:#1e2130;padding:6px 14px;border-radius:20px;font-size:.85rem;color:#aaa;}}
.st strong{{color:#fff;}}
.ct{{display:flex;gap:10px;padding:16px 32px;flex-wrap:wrap;align-items:center;background:#11131c;border-bottom:1px solid #222;}}
.ct input{{flex:1;min-width:200px;padding:8px 14px;border-radius:8px;border:1px solid #333;background:#1a1d2e;color:#e0e0e0;}}
.ct select{{padding:8px 14px;border-radius:8px;border:1px solid #333;background:#1a1d2e;color:#e0e0e0;}}
.ct button{{padding:6px 16px;border-radius:8px;border:1px solid #333;background:#1e2130;color:#ccc;cursor:pointer;}}
.ct button.on{{background:#2d6b3f;border-color:#3a8a52;color:#fff;}}
.lk{{margin-left:auto;display:flex;gap:10px;}}
.lk a{{color:#6b9eff;text-decoration:none;font-size:.9rem;}}
main{{padding:20px 32px;}}
.bs{{margin-bottom:36px;}}
.bs h2{{font-size:1.3rem;color:#fff;margin-bottom:12px;padding-bottom:8px;border-bottom:1px solid #222;}}
.bc{{font-size:.8rem;color:#6b9eff;font-weight:400;margin-left:10px;}}
.cg{{display:grid;grid-template-columns:repeat(auto-fill,minmax(420px,1fr));gap:16px;}}
.c{{background:#161822;border-radius:12px;overflow:hidden;border:1px solid #222;}}
.c:hover{{border-color:#3a3d4a;}}
.ch{{display:flex;justify-content:space-between;align-items:center;padding:8px 12px;background:#1a1d2e;border-bottom:1px solid #222;}}
.cn{{font-weight:600;color:#e0e0e0;font-size:.9rem;}}
.cb{{font-size:.75rem;padding:2px 8px;border-radius:10px;}}
.c[data-k="1"] .cb{{background:#2d6b3f30;color:#4ade80;}}
.c[data-k="0"] .cb{{background:#333;color:#666;}}
.cv{{display:flex;overflow-x:auto;}}
.vc{{flex:0 0 auto;width:130px;text-align:center;padding:8px 4px;border-right:1px solid #222;}}
.vc:last-child{{border-right:0;}}
.vc img{{width:110px;height:110px;object-fit:contain;cursor:pointer;border-radius:4px;background:#0e1018;}}
.vc img:hover{{transform:scale(1.08);}}
.vl{{display:block;font-size:.65rem;color:#888;margin-top:4px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}}
.lb{{display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,.85);z-index:999;justify-content:center;align-items:center;cursor:pointer;}}
.lb.s{{display:flex;}}
.lb img{{max-width:90vw;max-height:90vh;border-radius:8px;}}
.lb .ll{{position:absolute;bottom:30px;left:50%;transform:translateX(-50%);color:#ccc;font-size:.9rem;background:rgba(0,0,0,.7);padding:6px 16px;border-radius:20px;}}
.ft{{text-align:center;padding:20px;color:#555;font-size:.8rem;border-top:1px solid #222;}}
@media(max-width:640px){{.cg{{grid-template-columns:1fr;}}.vc{{width:100px;}}.vc img{{width:80px;height:80px;}}}}
</style></head>
<body>
<div class="hdr"><h1>🏁 Wappenvergleich Tirol <small>Original vs KI-generiert</small></h1>
<div class="st"><span><strong>{total_orte}</strong> Gemeinden</span><span><strong>{gemeinden_mit_ki} ✨</strong> mit KI</span><span><strong>{total_ki}</strong> KI-Bilder</span><span><strong>{len(api_gemeinden)}</strong> API</span><span><strong>{len(lokal_gemeinden)}</strong> Lokal</span></div></div>
<div class="ct">
<input id="fs" placeholder="🔍 Gemeinde suchen…" oninput="f()">
<select id="fb" onchange="f()"><option value="">Alle Bezirke</option>
<option value="imst">Imst</option><option value="innsbruck_stadt">Innsbruck Stadt</option><option value="innsbruck_land">Innsbruck-Land</option>
<option value="kitzbuehel">Kitzbühel</option><option value="kufstein">Kufstein</option><option value="landeck">Landeck</option>
<option value="lienz">Lienz (Osttirol)</option><option value="reutte">Reutte (Außerfern)</option><option value="schwaz">Schwaz</option></select>
<button id="fa" class="on" onclick="sf(\'a\')">Alle</button>
<button id="fk" onclick="sf(\'k\')">Mit KI ✓</button>
<button id="fn" onclick="sf(\'n\')">Nur Original ⏳</button>
<div class="lk"><a href="index.html">← Übersicht</a><a href="generiert.html">🎨 Galerie</a></div></div>
<main>{"".join(sections)}</main>
<div class="lb" id="lb" onclick="this.classList.remove(\'s\')"><img id="lbi" src=""><div class="ll" id="lbl"></div></div>
<div class="ft">Originale: Wikipedia (CC BY-SA 4.0) · API: SiliconFlow · Lokal: RTX 3060 FLUX Dev + RealVisXL</div>
<script>
let cf='a';function sf(f){{cf=f;document.querySelectorAll('.ct button').forEach(b=>b.className='');document.getElementById('f'+f).className='on';f();}}
function f(){{
const q=document.getElementById('fs').value.toLowerCase(),b=document.getElementById('fb').value;
document.querySelectorAll('.c').forEach(c=>{{const ok=(!q||c.dataset.n.includes(q))&&(!b||c.dataset.b===b)&&(cf==='a'||(cf==='k'&&c.dataset.k==='1')||(cf==='n'&&c.dataset.k==='0'));c.style.display=ok?'':'none';}});
document.querySelectorAll('.bs').forEach(s=>{{s.style.display=[...s.querySelectorAll('.c')].some(c=>c.style.display!=='none')?'':'none';}});}}
function ol(s,l){{document.getElementById('lbi').src=s;document.getElementById('lbl').textContent=l;document.getElementById('lb').classList.add('s');}}
</script></body></html>'''

with open('vergleich.html','w',encoding='utf-8') as f: f.write(html)

print(f"✅ vergleich.html ({len(html)} bytes)")
print(f"   {total_orte} Gemeinden, {gemeinden_mit_ki} mit KI, {total_ki} KI-Bilder")
print(f"   API: {len(api_gemeinden)}, Lokal: {len(lokal_gemeinden)}")
coms = ', '.join(f'{v["ort_name"]} ({len(v["imgs"])})' for v in sorted(all_images.values(), key=lambda x: x['ort_name']))
print(f"   {coms}")

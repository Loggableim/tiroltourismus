#!/usr/bin/env python3
"""Generiert ALLE 276 Wappen Tirols — sequentiell, Model bleibt geladen."""
import requests, json, os, time, uuid, sqlite3, datetime

COMFY = "http://127.0.0.1:8188"
OUT = "img/lokal"
BOARD_DB = "/e/HermesPortable/home/kanban/boards/wappen-batch/kanban.db"
os.makedirs(OUT, exist_ok=True)

CLIP_L = "modern minimalist flat vector coat of arms, heraldic shield with clean geometric shapes, bold flat colors, simplified minimalist style, no text, premium quality"
T5_BASE = "modern minimalist flat vector coat of arms redesign for {name} in {bezirk} Tyrol, heraldic shield with clean geometric simplified shapes, bold flat vector colors, minimalist logo-style heraldry, modern reinterpretation, premium quality vector illustration, no text, no watermark"

def up(path):
    with open(path,'rb') as f:
        r = requests.post(f"{COMFY}/upload/image",
            files={"image":(os.path.basename(path),f,"image/png")},
            data={"type":"input","overwrite":"true"}, timeout=30)
    return r.json()["name"] if r.ok else None

def submit_and_save(image_fn, oname, bname, seed=42):
    """Submit one workflow, poll, save result. Returns elapsed time or None."""
    safe = oname.lower().replace(' ','_').replace('(','').replace(')','').replace('.','')
    safe = safe.replace('ä','ae').replace('ö','oe').replace('ü','ue').replace('ß','ss')
    safe = ''.join(c for c in safe if c.isalnum() or c=='_')
    
    wf = {
        "1":{"class_type":"LoadImage","inputs":{"image":image_fn}},
        "2":{"class_type":"ImageScale","inputs":{"image":["1",0],"upscale_method":"lanczos","width":120,"height":144,"crop":"disabled"}},
        "3":{"class_type":"VAELoader","inputs":{"vae_name":"flux-vae-bf16.safetensors"}},
        "4":{"class_type":"UNETLoader","inputs":{"unet_name":"flux1-dev-fp8-e4m3fn.safetensors","weight_dtype":"default"}},
        "5":{"class_type":"DualCLIPLoader","inputs":{"clip_name1":"clip_l.safetensors","clip_name2":"t5xxl_fp16.safetensors","type":"flux"}},
        "7":{"class_type":"VAEEncode","inputs":{"pixels":["2",0],"vae":["3",0]}},
        "8":{"class_type":"CLIPTextEncodeFlux","inputs":{"clip":["5",0],"clip_l":CLIP_L,"t5xxl":T5_BASE.format(name=oname, bezirk=bname),"guidance":2.0}},
        "9":{"class_type":"KSampler","inputs":{"seed":seed,"steps":4,"cfg":1.0,"sampler_name":"euler","scheduler":"simple","denoise":0.35,"model":["4",0],"positive":["8",0],"negative":["8",0],"latent_image":["7",0]}},
        "10":{"class_type":"VAEDecode","inputs":{"samples":["9",0],"vae":["3",0]}},
        "11":{"class_type":"SaveImage","inputs":{"filename_prefix":f"wappen_{safe}_modern","images":["10",0]}}
    }
    
    r = requests.post(f"{COMFY}/prompt", json={"prompt":wf, "client_id":str(uuid.uuid4())})
    if r.status_code != 200: return None
    pid = r.json()["prompt_id"]
    
    t0 = time.time()
    while time.time()-t0 < 120:
        try:
            r = requests.get(f"{COMFY}/history/{pid}", timeout=10)
            if r.status_code==200 and pid in r.json():
                h = r.json()[pid]
                if h['status'].get('completed'):
                    for nid,no in h.get('outputs',{}).items():
                        for img in no.get('images',[]):
                            ir = requests.get(f"{COMFY}/view?filename={img['filename']}&type=output")
                            op = os.path.join(OUT, img['filename'])
                            with open(op,'wb') as f: f.write(ir.content)
                            return time.time()-t0
        except: pass
        time.sleep(1)
    return None

def kanban_complete(tid, summary):
    try:
        conn = sqlite3.connect(BOARD_DB)
        now = datetime.datetime.now().timestamp()
        conn.execute("UPDATE tasks SET status='done', completed_at=?, result=? WHERE id=?", (now, summary[:500], tid))
        conn.commit(); conn.close()
    except: pass

def kanban_comment(tid, text):
    try:
        conn = sqlite3.connect(BOARD_DB)
        now = datetime.datetime.now().timestamp()
        conn.execute("INSERT INTO task_comments (task_id, author, body, created_at) VALUES (?, 'system', ?, ?)", (tid, text[:500], now))
        conn.commit(); conn.close()
    except: pass

# ─── Load data ────────────────────────────────────────────────────
with open('wappen_page_data.json', encoding='utf-8') as f:
    data = json.load(f)

total = sum(len(b['orte']) for b in data['bezirke'])
done = 0
fail = 0
t_start = time.time()

print(f"🏁 Starte {total} Wappen-Generierungen...")

for bezirk in data['bezirke']:
    bname = bezirk['name']
    bk = bname.lower().replace(' ','_').replace('(','').replace(')','')[:20]
    tid = f"t_wappen_{bk}"
    bk_count = 0
    bk_ok = 0
    bk_t0 = time.time()
    
    for ort in bezirk['orte']:
        oname = ort['name']
        img_path = ort.get('img','') or bezirk.get('img','')
        if not img_path or not os.path.exists(img_path):
            print(f"  ❌ Kein Input: {oname}")
            fail += 1
            continue
        
        fn = up(img_path)
        if not fn:
            print(f"  ❌ Upload: {oname}")
            fail += 1
            continue
        
        dur = submit_and_save(fn, oname, bname)
        if dur:
            done += 1
            bk_ok += 1
            if done % 20 == 0:
                elapsed = time.time() - t_start
                rate = done / elapsed
                rem = (total - done) / rate if rate > 0 else 0
                print(f"  [{done}/{total}] {(time.time()-t_start)/60:.0f}min, noch ~{rem:.0f}s | ⌀ {elapsed/done:.1f}s/Bild")
        else:
            fail += 1
            print(f"  ❌ Fail: {oname}")
        
        bk_count += 1
    
    # Bezirk done
    b_dur = time.time()-bk_t0
    print(f"  ✅ {bname}: {bk_ok}/{bk_count} in {b_dur:.0f}s")
    kanban_comment(tid, f"✅ {bk_ok}/{bk_count} Bilder in {b_dur:.0f}s")
    kanban_complete(tid, f"{bk_ok}/{bk_count} Wappen in {b_dur:.0f}s")

t_total = time.time()-t_start
print(f"\n{'='*50}")
print(f"🏁 FERTIG: {done}/{total} Wappen ({fail} Fehler)")
print(f"   Dauer: {t_total/60:.0f}min (⌀ {t_total/done:.1f}s/Bild)")
print(f"   python build_vergleich.py für aktualisierte Seite")

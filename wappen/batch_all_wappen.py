#!/usr/bin/env python3
"""Master batch: ALL 276 Tirol coats of arms in ONE run, kanban-tracked.
Batches of 3-4 per ComfyUI workflow. Model loaded once per batch."""
import requests, json, os, time, uuid, sqlite3, datetime

# ─── Config ───────────────────────────────────────────────────────
COMFY = "http://127.0.0.1:8188"
OUT = "img/lokal"
WAPPEN_DIR = "."
BOARD_DB = "/e/HermesPortable/home/kanban/boards/wappen-batch/kanban.db"
os.makedirs(OUT, exist_ok=True)

BEZIRK_ORDER = [
    "Imst", "Innsbruck Stadt", "Innsbruck-Land", "Kitzbühel",
    "Kufstein", "Landeck", "Lienz (Osttirol)", "Reutte (Außerfern)", "Schwaz"
]

PROMPT_CLIP_L = "modern minimalist flat vector coat of arms, heraldic shield with clean geometric shapes, bold flat colors, simplified minimalist style, no text, premium quality"
PROMPT_T5_BASE = "modern minimalist flat vector coat of arms redesign, heraldic shield with clean geometric simplified shapes, bold flat vector colors, minimalist logo-style heraldry, modern reinterpretation, premium quality vector illustration, no text, no watermark"

# ─── Helpers ──────────────────────────────────────────────────────
def upload_image(path):
    with open(path,'rb') as f:
        r = requests.post(f"{COMFY}/upload/image",
            files={"image":(os.path.basename(path),f,"image/png")},
            data={"type":"input","overwrite":"true"}, timeout=30)
    return r.json()["name"] if r.ok else None

def save_results(pid):
    try:
        r = requests.get(f"{COMFY}/history/{pid}", timeout=10)
        if r.status_code == 200 and pid in r.json():
            h = r.json()[pid]
            if not h['status'].get('completed'): return 0
            saved = 0
            for nid, no in h.get('outputs',{}).items():
                for img in no.get('images',[]):
                    ir = requests.get(f"{COMFY}/view?filename={img['filename']}&type=output")
                    op = os.path.join(OUT, img['filename'])
                    with open(op,'wb') as f: f.write(ir.content)
                    saved += 1
            return saved
    except: pass
    return 0

def db():
    return sqlite3.connect(BOARD_DB)

def kanban_task_id(bezirk_name):
    """Return consistent task ID for a bezirk."""
    prefix = bezirk_name.lower().replace(' ','_').replace('(','').replace(')','')[:20]
    return f"t_wappen_{prefix}"

def kanban_create_task(tid, title, body):
    """Create a kanban task via direct SQLite."""
    conn = db()
    cur = conn.cursor()
    now = datetime.datetime.now().timestamp()
    cur.execute("""INSERT OR IGNORE INTO tasks 
        (id, title, body, assignee, status, priority, created_at, max_runtime_seconds, max_retries)
        VALUES (?, ?, ?, ?, 'ready', 1, ?, 7200, 2)""",
        (tid, title, body[:1900], 'feat-builder', now))
    conn.commit()
    conn.close()

def kanban_complete_task(tid, summary):
    conn = db()
    cur = conn.cursor()
    now = datetime.datetime.now().timestamp()
    cur.execute("UPDATE tasks SET status='done', completed_at=?, result=? WHERE id=?", 
        (now, summary[:500], tid))
    # Promote children
    cur.execute("""UPDATE tasks SET status='ready' WHERE id IN (
        SELECT l.child_id FROM task_links l
        JOIN tasks p ON p.id = l.parent_id
        WHERE NOT EXISTS (
            SELECT 1 FROM task_links l2
            JOIN tasks p2 ON p2.id = l2.parent_id
            WHERE l2.child_id = l.child_id AND p2.status != 'done'
        ) AND l.parent_id = ?)""", (tid,))
    conn.commit()
    conn.close()

def kanban_add_comment(tid, text):
    conn = db()
    cur = conn.cursor()
    now = datetime.datetime.now().timestamp()
    cur.execute("INSERT INTO task_comments (task_id, author, body, created_at) VALUES (?, ?, ?, ?)",
        (tid, 'system', text[:500], now))
    conn.commit()
    conn.close()

# ─── Load data ────────────────────────────────────────────────────
with open('wappen_page_data.json', encoding='utf-8') as f:
    data = json.load(f)

all_bezirke = {b['name']: b for b in data['bezirke']}

# ─── Create kanban tasks ─────────────────────────────────────────
print("=" * 60)
print("📋 Kanban-Tasks erstellen...")
for bname in BEZIRK_ORDER:
    if bname not in all_bezirke: continue
    b = all_bezirke[bname]
    tid = kanban_task_id(bname)
    n = len(b['orte'])
    kanban_create_task(tid, f"Wappen: {bname} ({n})",
        f"PROJEKT-PFAD: /f/tiroltourismus/wappen\nBEZIRK: {bname}\n{n} Gemeinden\nGeneriere moderne Wappen im 124x148px FLUX Dev Stil.")
    print(f"  [{tid:30}] {bname:30} ({n}) — ready")

print("\n🧪 Batch-Generierung starten...")
print("=" * 60)

# ─── Process each Bezirk ─────────────────────────────────────────
total_generated = 0
bezirke_done = 0

for bname in BEZIRK_ORDER:
    if bname not in all_bezirke: continue
    b = all_bezirke[bname]
    orte = b['orte']
    tid = kanban_task_id(bname)
    
    print(f"\n{'─'*60}")
    print(f"🏔️  {bname} ({len(orte)} Gemeinden)")
    print(f"{'─'*60}")
    
    bezirk_start = time.time()
    bezirk_ok = 0
    bezirk_fail = 0
    
    # Process in sub-batches of 3-4 (VRAM limit)
    batch_size = 3
    for batch_start in range(0, len(orte), batch_size):
        batch_orte = orte[batch_start:batch_start + batch_size]
        batch_names = [o['name'] for o in batch_orte]
        batch_imgs = [o.get('img','') for o in batch_orte]
        
        # Upload all images first
        uploads = {}
        all_ok = True
        for i, o in enumerate(batch_orte):
            img_path = o.get('img','') or b.get('img','')
            if not img_path or not os.path.exists(img_path):
                print(f"  ⚠️  Kein Bild: {o['name']}")
                all_ok = False
                continue
            fn = upload_image(img_path)
            if fn:
                uploads[str(i)] = fn
            else:
                print(f"  ❌ Upload fail: {o['name']}")
                all_ok = False
        
        if not all_ok or not uploads:
            print(f"  ⏭️  Batch übersprungen")
            continue
        
        # Build ComfyUI workflow with parallel chains
        wf = {}
        nid = 1
        
        # Shared models (once per batch)
        wf[str(nid)] = {"class_type": "VAELoader", "inputs": {"vae_name": "flux-vae-bf16.safetensors"}}; nid += 1
        VAE = str(nid-1)
        wf[str(nid)] = {"class_type": "UNETLoader", "inputs": {"unet_name": "flux1-dev-fp8-e4m3fn.safetensors", "weight_dtype": "default"}}; nid += 1
        UNET = str(nid-1)
        wf[str(nid)] = {"class_type": "DualCLIPLoader", "inputs": {"clip_name1": "clip_l.safetensors", "clip_name2": "t5xxl_fp16.safetensors", "type": "flux"}}; nid += 1
        CLIP = str(nid-1)
        
        for i, o in enumerate(batch_orte):
            key = str(i)
            if key not in uploads: continue
            oname = o['name']
            
            wf[str(nid)] = {"class_type": "LoadImage", "inputs": {"image": uploads[key]}}; nid += 1
            LOAD = str(nid-1)
            wf[str(nid)] = {"class_type": "ImageScale", "inputs": {"image": [LOAD,0], "upscale_method": "lanczos", "width": 124, "height": 148, "crop": "disabled"}}; nid += 1
            SCALE = str(nid-1)
            wf[str(nid)] = {"class_type": "VAEEncode", "inputs": {"pixels": [SCALE,0], "vae": [VAE,0]}}; nid += 1
            LATENT = str(nid-1)
            wf[str(nid)] = {"class_type": "CLIPTextEncodeFlux", "inputs": {"clip": [CLIP,0], "clip_l": PROMPT_CLIP_L, "t5xxl": f"{PROMPT_T5_BASE}, {oname} {bname} coat of arms", "guidance": 2.0}}; nid += 1
            TEXT = str(nid-1)
            wf[str(nid)] = {"class_type": "KSampler", "inputs": {"seed": hash(oname) % 99999, "steps": 4, "cfg": 1.0, "sampler_name": "euler", "scheduler": "simple", "denoise": 0.35, "model": [UNET,0], "positive": [TEXT,0], "negative": [TEXT,0], "latent_image": [LATENT,0]}}; nid += 1
            KS = str(nid-1)
            wf[str(nid)] = {"class_type": "VAEDecode", "inputs": {"samples": [KS,0], "vae": [VAE,0]}}; nid += 1
            DEC = str(nid-1)
            
            # Use sanitized name for filename
            safe_name = oname.lower().replace(' ','_').replace('(','').replace(')','').replace('.','').replace(',','')
            safe_name = safe_name.replace('ä','ae').replace('ö','oe').replace('ü','ue').replace('ß','ss')
            safe_name = ''.join(c for c in safe_name if c.isalnum() or c == '_')
            
            wf[str(nid)] = {"class_type": "SaveImage", "inputs": {"filename_prefix": f"wappen_{safe_name}_modern", "images": [DEC,0]}}; nid += 1
        
        # Submit workflow
        resp = requests.post(f"{COMFY}/prompt", json={"prompt": wf, "client_id": str(uuid.uuid4())})
        if resp.status_code != 200:
            print(f"  ❌ Submit fail: {resp.status_code}")
            continue
        
        pid = resp.json()["prompt_id"]
        print(f"  ⏳ Batch {batch_names[0]}... (+{len(uploads)})", end=" ", flush=True)
        
        # Wait
        t = time.time()
        while time.time() - t < 300:
            try:
                r = requests.get(f"{COMFY}/history/{pid}", timeout=10)
                if r.status_code == 200 and pid in r.json():
                    h = r.json()[pid]
                    if h['status'].get('completed'):
                        # Count results
                        saved = 0
                        for nid_no, no in h.get('outputs',{}).items():
                            for img in no.get('images',[]):
                                ir = requests.get(f"{COMFY}/view?filename={img['filename']}&type=output")
                                op = os.path.join(OUT, img['filename'])
                                with open(op,'wb') as f: f.write(ir.content)
                                saved += 1
                        bezirk_ok += saved
                        total_generated += saved
                        print(f"✅ {saved} Bilder ({time.time()-t:.0f}s)")
                        break
            except: pass
            time.sleep(2)
        else:
            print(f"❌ Timeout")
            bezirk_fail += 1
        
        # Small pause between batches
        time.sleep(1)
    
    # Bezirk done
    elapsed = time.time() - bezirk_start
    print(f"  📊 {bname}: {bezirk_ok} Bilder in {elapsed:.0f}s ({elapsed/60:.1f} min)")
    kanban_add_comment(tid, f"✅ {bezirk_ok} Bilder generiert in {elapsed:.0f}s")
    kanban_complete_task(tid, f"Bezirk {bname}: {bezirk_ok} Bilder, {bezirk_fail} Fehler")
    bezirke_done += 1

# ─── Summary ──────────────────────────────────────────────────────
print(f"\n{'='*60}")
print(f"🏁 FERTIG! ({bezirke_done}/9 Bezirke)")
print(f"   {total_generated} Bilder generiert in img/lokal/")
print(f"   Lauf: python build_vergleich.py für aktualisierte Vergleichsseite")
print(f"{'='*60}")

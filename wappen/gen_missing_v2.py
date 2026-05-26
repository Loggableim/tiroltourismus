#!/usr/bin/env python3
"""Generate ALL missing Wappen. Single image per prompt, retry on fail."""
import requests, json, os, time, uuid

COMFY = "http://127.0.0.1:8188"
OUT = "img/lokal"
os.makedirs(OUT, exist_ok=True)

CLIP_L = "modern minimalist flat vector coat of arms, heraldic shield with clean geometric shapes, bold flat colors, simplified minimalist style, no text, premium quality"
T5_BASE = "modern minimalist flat vector coat of arms redesign for {name} in {bezirk} Tyrol, heraldic shield with clean geometric simplified shapes, bold flat vector colors, minimalist logo-style heraldry, modern reinterpretation, premium quality vector illustration, no text, no watermark"

def safe(name):
    s = name.lower().replace(' ','_').replace('(','').replace(')','').replace('.','')
    s = s.replace('ä','ae').replace('ö','oe').replace('ü','ue').replace('ß','ss')
    s = ''.join(c for c in s if c.isalnum() or c=='_')
    return s

def upload(path, retries=2):
    for attempt in range(retries):
        try:
            with open(path,'rb') as f:
                r = requests.post(f"{COMFY}/upload/image",
                    files={"image":(os.path.basename(path),f,"image/png")},
                    data={"type":"input","overwrite":"true"}, timeout=60)
                if r.ok: return r.json()["name"]
        except: pass
        if attempt < retries-1: time.sleep(3)
    return None

def gen_one(oname, bname, img_fn):
    sn = safe(oname)
    wf = {
        "1":{"class_type":"LoadImage","inputs":{"image":img_fn}},
        "2":{"class_type":"ImageScale","inputs":{"image":["1",0],"upscale_method":"lanczos","width":120,"height":144,"crop":"disabled"}},
        "3":{"class_type":"VAELoader","inputs":{"vae_name":"flux-vae-bf16.safetensors"}},
        "4":{"class_type":"UNETLoader","inputs":{"unet_name":"flux1-dev-fp8-e4m3fn.safetensors","weight_dtype":"default"}},
        "5":{"class_type":"DualCLIPLoader","inputs":{"clip_name1":"clip_l.safetensors","clip_name2":"t5xxl_fp16.safetensors","type":"flux"}},
        "7":{"class_type":"VAEEncode","inputs":{"pixels":["2",0],"vae":["3",0]}},
        "8":{"class_type":"CLIPTextEncodeFlux","inputs":{"clip":["5",0],"clip_l":CLIP_L,"t5xxl":T5_BASE.format(name=oname,bezirk=bname),"guidance":2.0}},
        "9":{"class_type":"KSampler","inputs":{"seed":hash(sn)%99999,"steps":4,"cfg":1.0,"sampler_name":"euler","scheduler":"simple","denoise":0.35,"model":["4",0],"positive":["8",0],"negative":["8",0],"latent_image":["7",0]}},
        "10":{"class_type":"VAEDecode","inputs":{"samples":["9",0],"vae":["3",0]}},
        "11":{"class_type":"SaveImage","inputs":{"filename_prefix":f"wappen_{sn}_modern","images":["10",0]}}
    }
    r = requests.post(f"{COMFY}/prompt", json={"prompt":wf, "client_id":str(uuid.uuid4())}, timeout=30)
    if r.status_code != 200: return None
    pid = r.json()["prompt_id"]
    t0 = time.time()
    while time.time()-t0 < 180:
        r = requests.get(f"{COMFY}/history/{pid}", timeout=15)
        if r.status_code==200 and pid in r.json():
            h = r.json()[pid]
            if h['status'].get('completed'):
                for nid,no in h.get('outputs',{}).items():
                    for img in no.get('images',[]):
                        ir = requests.get(f"{COMFY}/view?filename={img['filename']}&type=output")
                        with open(os.path.join(OUT,img['filename']),'wb') as f: f.write(ir.content)
                        return time.time()-t0
            elif h['status'].get('status_str') == 'error':
                return None
        time.sleep(2)
    return None

# Load data
with open('wappen_page_data.json', encoding='utf-8') as f:
    data = json.load(f)

existing = set()
for fn in os.listdir(OUT):
    if fn.endswith('.png') and fn.startswith('wappen_') and '_modern_00001' in fn:
        existing.add(fn.replace('wappen_','').split('_modern_')[0])

# Collect missing with proper paths
missing = []
for b in data['bezirke']:
    for o in b['orte']:
        if safe(o['name']) not in existing:
            ip = o.get('img','') or b.get('img','')
            if ip and os.path.exists(ip):
                missing.append((o['name'], b['name'], ip))

print(f"🏁 {len(missing)} fehlen")
done = fail = 0
t0 = time.time()

for i, (oname, bname, ipath) in enumerate(missing):
    fn = upload(ipath)
    if not fn:
        fail += 1
        if fail > 5:
            print("  ⚠️  Zu viele Upload-Fehler, neustart...")
            time.sleep(10)
            fn = upload(ipath, retries=3)
            if not fn:
                fail += 1
                continue
        fail += 1
        continue
    
    dur = gen_one(oname, bname, fn)
    if dur:
        done += 1
        if done % 20 == 0:
            elapsed = time.time()-t0
            print(f"  [{done}/{len(missing)}] {elapsed/60:.0f}min, ~{(len(missing)-done)/(done/elapsed):.0f}s verbleibend")
    else:
        fail += 1
        if fail > 3:
            print("  ⚠️  Zu viele Fehler, warte 30s...")
            time.sleep(30)
            fail = 0

print(f"\n✅ {done}/{len(missing)} ({fail} Fehler) in {(time.time()-t0)/60:.1f}min")

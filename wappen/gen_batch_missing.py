#!/usr/bin/env python3
"""Generate missing Wappen in BATCHES of 3 — shared model, ~35s pro Batch."""
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

def poll_until_done(pid, timeout=180):
    t0 = time.time()
    while time.time()-t0 < timeout:
        try:
            r = requests.get(f"{COMFY}/history/{pid}", timeout=15)
            if r.status_code == 200 and pid in r.json():
                h = r.json()[pid]
                if h['status'].get('completed'):
                    saved = 0
                    for nid, no in h.get('outputs',{}).items():
                        for img in no.get('images',[]):
                            ir = requests.get(f"{COMFY}/view?filename={img['filename']}&type=output")
                            op = os.path.join(OUT, img['filename'])
                            with open(op,'wb') as f: f.write(ir.content)
                            saved += 1
                    return saved
        except: pass
        time.sleep(2)
    return 0

def upload(path):
    try:
        with open(path,'rb') as f:
            r = requests.post(f"{COMFY}/upload/image",
                files={"image":(os.path.basename(path),f,"image/png")},
                data={"type":"input","overwrite":"true"}, timeout=30)
            return r.json()["name"] if r.ok else None
    except:
        return None

# Load data + find missing
with open('wappen_page_data.json', encoding='utf-8') as f:
    data = json.load(f)

existing = set()
for fn in os.listdir(OUT):
    if fn.endswith('.png') and fn.startswith('wappen_') and '_modern_00001' in fn:
        existing.add(fn.replace('wappen_','').split('_modern_')[0])

missing = []
for b in data['bezirke']:
    for o in b['orte']:
        if safe(o['name']) not in existing:
            img_path = o.get('img','') or b.get('img','')
            if img_path and os.path.exists(img_path):
                missing.append((o['name'], b['name'], img_path))

print(f"🏁 {len(missing)} fehlen — starte Batch-Generierung...")

BATCH_SIZE = 3
done = 0
fail = 0
t0 = time.time()
batch_num = 0

for i in range(0, len(missing), BATCH_SIZE):
    batch = missing[i:i+BATCH_SIZE]
    batch_num += 1
    
    # Upload all images
    uploads = {}
    all_uploaded = True
    for oname, bname, ipath in batch:
        fn = upload(ipath)
        if fn:
            uploads[oname] = fn
        else:
            fail += 1
            all_uploaded = False
    
    if not all_uploaded or not uploads:
        continue
    
    # Build workflow with shared models + parallel chains
    wf = {}
    nid = 1
    wf[str(nid)] = {"class_type":"VAELoader","inputs":{"vae_name":"flux-vae-bf16.safetensors"}}; nid+=1; V=str(nid-1)
    wf[str(nid)] = {"class_type":"UNETLoader","inputs":{"unet_name":"flux1-dev-fp8-e4m3fn.safetensors","weight_dtype":"default"}}; nid+=1; U=str(nid-1)
    wf[str(nid)] = {"class_type":"DualCLIPLoader","inputs":{"clip_name1":"clip_l.safetensors","clip_name2":"t5xxl_fp16.safetensors","type":"flux"}}; nid+=1; C=str(nid-1)
    
    for oname, bname, ipath in batch:
        fn = uploads.get(oname)
        if not fn: continue
        sn = safe(oname)
        wf[str(nid)] = {"class_type":"LoadImage","inputs":{"image":fn}}; nid+=1; L=str(nid-1)
        wf[str(nid)] = {"class_type":"ImageScale","inputs":{"image":[L,0],"upscale_method":"lanczos","width":120,"height":144,"crop":"disabled"}}; nid+=1; S=str(nid-1)
        wf[str(nid)] = {"class_type":"VAEEncode","inputs":{"pixels":[S,0],"vae":[V,0]}}; nid+=1; LA=str(nid-1)
        wf[str(nid)] = {"class_type":"CLIPTextEncodeFlux","inputs":{"clip":[C,0],"clip_l":CLIP_L,"t5xxl":T5_BASE.format(name=oname,bezirk=bname),"guidance":2.0}}; nid+=1; T=str(nid-1)
        wf[str(nid)] = {"class_type":"KSampler","inputs":{"seed":hash(sn)%99999,"steps":4,"cfg":1.0,"sampler_name":"euler","scheduler":"simple","denoise":0.35,"model":[U,0],"positive":[T,0],"negative":[T,0],"latent_image":[LA,0]}}; nid+=1; K=str(nid-1)
        wf[str(nid)] = {"class_type":"VAEDecode","inputs":{"samples":[K,0],"vae":[V,0]}}; nid+=1; D=str(nid-1)
        wf[str(nid)] = {"class_type":"SaveImage","inputs":{"filename_prefix":f"wappen_{sn}_modern","images":[D,0]}}; nid+=1
    
    # Submit
    try:
        r = requests.post(f"{COMFY}/prompt", json={"prompt":wf,"client_id":str(uuid.uuid4())}, timeout=30)
        if r.status_code != 200:
            fail += len(batch)
            continue
        pid = r.json()["prompt_id"]
        saved = poll_until_done(pid)
        done += saved
        if done % 15 == 0:
            elapsed = time.time()-t0
            print(f"  [{done}/{len(missing)}] {elapsed/60:.0f}min | Batch {batch_num}")
    except:
        fail += len(batch)
        # Restart ComfyUI if connection lost
        try:
            requests.get(f"{COMFY}/system_stats", timeout=3)
        except:
            print("  ⚠️  ComfyUI down, skip batch")
            time.sleep(5)

print(f"\n✅ {done}/{len(missing)} ({fail} Fehler) in {(time.time()-t0)/60:.1f}min")
total_images = done + 164  # existing good ones
print(f"   Gesamt: ~{total_images}/276")
print(f"   python build_vergleich.py")

#!/usr/bin/env python3
"""ONE workflow: ALL 6 communities × 3 styles = 18 Bilder, Modelle nur 1× laden."""
import requests, json, os, time, uuid

COMFY = "http://127.0.0.1:8188"
OUT = "img/lokal"
os.makedirs(OUT, exist_ok=True)

def up(path):
    with open(path,'rb') as f:
        r = requests.post(f"{COMFY}/upload/image",
            files={"image":(os.path.basename(path),f,"image/png")},
            data={"type":"input","overwrite":"true"}, timeout=30)
    return r.json()["name"] if r.ok else None

STYLES = {
    "modern": {
        "clip_l": "modern minimalist flat vector coat of arms redesign, heraldic shield with clean geometric shapes, bold flat colors, simplified minimalist style, no text, premium vector quality",
        "t5xxl": "modern minimalist flat vector coat of arms redesign, heraldic shield with clean geometric simplified shapes, bold flat vector colors, minimalist logo-style heraldry, modern reinterpretation, premium quality vector illustration, no text, no watermark"
    },
    "mittelalter": {
        "clip_l": "traditional medieval heraldic coat of arms design, detailed ornate shield, gold accents, rich colors, classic heraldic style, ornamental borders, royal medieval aesthetic, no text",
        "t5xxl": "traditional medieval heraldic coat of arms artwork, ornate detailed shield with decorative borders and scrollwork, rich royal colors with gold accents, classic heraldic elements, historical medieval style, detailed ornamental heraldry, premium quality illustration, no text, no watermark"
    },
    "tourismus": {
        "clip_l": "bright modern alpine tourism style coat of arms, friendly outdoor design, vibrant colors blue green yellow, clean modern vector style, Tyrolean tourism branding, no text",
        "t5xxl": "bright vibrant alpine tourism style coat of arms redesign, friendly outdoor-oriented design with mountain and nature elements, clean modern vector style in blue green and yellow tones, Tyrolean tourism branding aesthetic, modern clean lines, appealing tourist-friendly look, premium quality vector illustration, no text, no watermark"
    }
}

GEMEINDEN = [
    ("innsbruck", "img/bezirke/innsbruck_stadt.png"),
    ("wattens",   "img/orte/innsbruck-land/wattens.png"),
    ("zirl",      "img/orte/innsbruck-land/zirl.png"),
    ("hall_in_tirol", "img/orte/innsbruck-land/hall_in_tirol.png"),
    ("kitzbuehel","img/orte/kitzbühel/kitzbühel.png"),
    ("alpbach",   "img/orte/kufstein/alpbach.png"),
]

# Upload ALL images
uploads = {}
for name, path in GEMEINDEN:
    fn = up(path)
    if fn: uploads[name] = fn
    print(f"📤 {name:15} → {fn}")

# ─── Build ONE giant workflow ─────────────────────────────────────
wf = {}
nid = 1

# Shared model nodes (loaded ONCE)
wf[str(nid)] = {"class_type":"VAELoader","inputs":{"vae_name":"flux-vae-bf16.safetensors"}}; nid+=1
VAE = str(nid-1)

wf[str(nid)] = {"class_type":"UNETLoader","inputs":{"unet_name":"flux1-dev-fp8-e4m3fn.safetensors","weight_dtype":"default"}}; nid+=1
UNET = str(nid-1)

wf[str(nid)] = {"class_type":"DualCLIPLoader","inputs":{"clip_name1":"clip_l.safetensors","clip_name2":"t5xxl_fp16.safetensors","type":"flux"}}; nid+=1
CLIP = str(nid-1)

# Per-community: LoadImage → ImageScale(124×148) → VAEEncode → 3× Style chains
for name, path in GEMEINDEN:
    fn = uploads.get(name)
    if not fn: continue
    
    # Load + Scale input
    wf[str(nid)] = {"class_type":"LoadImage","inputs":{"image":fn}}; nid+=1
    LOAD = str(nid-1)
    
    wf[str(nid)] = {"class_type":"ImageScale","inputs":{"image":[LOAD,0],"upscale_method":"lanczos","width":124,"height":148,"crop":"disabled"}}; nid+=1
    SCALE = str(nid-1)
    
    wf[str(nid)] = {"class_type":"VAEEncode","inputs":{"pixels":[SCALE,0],"vae":[VAE,0]}}; nid+=1
    LATENT = str(nid-1)
    
    # 3 parallel style chains
    for style, cfg in STYLES.items():
        # CLIP encode
        wf[str(nid)] = {"class_type":"CLIPTextEncodeFlux","inputs":{"clip":[CLIP,0],"clip_l":cfg["clip_l"],"t5xxl":f"{cfg['t5xxl']}, {name} Tyrol coat of arms","guidance":2.0}}; nid+=1
        TEXT = str(nid-1)
        
        # KSampler (SPEEDY: 4 steps)
        wf[str(nid)] = {"class_type":"KSampler","inputs":{
            "seed":42,"steps":4,"cfg":1.0,"sampler_name":"euler","scheduler":"simple",
            "denoise":0.35,
            "model":[UNET,0],"positive":[TEXT,0],"negative":[TEXT,0],
            "latent_image":[LATENT,0]
        }}; nid+=1
        KS = str(nid-1)
        
        # VAE Decode
        wf[str(nid)] = {"class_type":"VAEDecode","inputs":{"samples":[KS,0],"vae":[VAE,0]}}; nid+=1
        DEC = str(nid-1)
        
        # Save
        wf[str(nid)] = {"class_type":"SaveImage","inputs":{"filename_prefix":f"wappen_{name}_{style}","images":[DEC,0]}}; nid+=1

print(f"\n🧩 Workflow: {nid-1} nodes total")
print(f"   Shared: 1 VAE + 1 UNET + 1 CLIP")
print(f"   Per community: 1 Load + 1 Scale + 1 Encode + 3× (Text+KSampler+Decode+Save)")
print(f"   Submit...")

# Submit
r = requests.post(f"{COMFY}/prompt", json={"prompt":wf, "client_id":str(uuid.uuid4())})
if r.status_code != 200:
    print(f"❌ Submit: {r.status_code} {r.text[:200]}")
    exit(1)

pid = r.json()["prompt_id"]
print(f"✅ Prompt ID: {pid}")

# Poll
print(f"\n⏳ Warte auf Fertigstellung... (ca. 15-20 min)")
t = time.time()
last_status = 0
while True:
    try:
        r = requests.get(f"{COMFY}/history/{pid}", timeout=10)
        if r.status_code == 200 and pid in r.json():
            h = r.json()[pid]
            if h['status'].get('completed'):
                elapsed = time.time() - t
                # Gather outputs
                saved = 0
                for nid_no, no in h.get('outputs',{}).items():
                    for img in no.get('images',[]):
                        ir = requests.get(f"{COMFY}/view?filename={img['filename']}&type=output")
                        op = os.path.join(OUT, img['filename'])
                        with open(op,'wb') as f: f.write(ir.content)
                        saved += 1
                print(f"✅ DONE in {elapsed:.0f}s ({elapsed/60:.1f} min) — {saved} Bilder")
                for f in sorted(os.listdir(OUT)):
                    if f.endswith(".png") and f.startswith("wappen_") and f not in [x for x in os.listdir(OUT) if x.startswith("wappen_")]:
                        pass
                break
            if h['status'].get('status_str') == 'error':
                print(f"❌ ERROR: {h['status']}")
                break
        # Queue progress
        q = requests.get(f"{COMFY}/queue", timeout=10).json()
        rr = len(q.get('queue_running',[]))
        rp = len(q.get('queue_pending',[]))
        elapsed = time.time() - t
        if int(elapsed/30) > last_status:
            last_status = int(elapsed/30)
            print(f"  ⏳ {elapsed:.0f}s — {rr} running, {rp} pending")
    except: pass
    time.sleep(5)

# List results
print(f"\n📸 Generierte Bilder:")
for f in sorted(os.listdir(OUT)):
    if not f.endswith(".png"): continue
    sz = os.path.getsize(os.path.join(OUT,f))
    if sz < 50000 and "_realvisxl_" in f: continue  # skip old
    if sz < 50000 and "_flux_" in f and "_modern_" in f:
        print(f"  {f} ({sz//1024}KB)")

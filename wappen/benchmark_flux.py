#!/usr/bin/env python3
"""Benchmark FLUX Dev — 3 Stufen (Best/Balanced/Speedy) für Inzing Wappen, 110x100px."""
import requests, json, os, time, uuid

COMFY = "http://127.0.0.1:8188"
OUT = "img/benchmark"
os.makedirs(OUT, exist_ok=True)

def up(path):
    with open(path,'rb') as f:
        r = requests.post(f"{COMFY}/upload/image", files={"image":(os.path.basename(path),f,"image/png")}, data={"type":"input","overwrite":"true"}, timeout=30)
    return r.json()["name"] if r.ok else None

def poll(pid, timeout=900):
    t=time.time()
    while time.time()-t<timeout:
        try:
            r=requests.get(f"{COMFY}/history/{pid}",timeout=10)
            if r.status_code==200 and pid in r.json():
                h=r.json()[pid]
                if h['status'].get('completed'): return time.time()-t, h.get('outputs',{})
        except: pass
        time.sleep(1)
    return None, None

# Upload Inzing once
print("Upload Inzing...")
fn = up("img/orte/innsbruck-land/inzing.png")
print(f"  Uploaded: {fn}")

CLIP_L = "modern minimalist flat vector coat of arms redesign, heraldic shield with clean geometric shapes, bold flat colors, simplified minimalist style, no text, premium quality"
T5XXL = "modern minimalist flat vector coat of arms redesign for Inzing Tyrol, heraldic shield with clean geometric simplified shapes, bold flat vector colors, minimalist logo-style heraldry, modern reinterpretation, premium quality vector illustration, no text, no watermark"

configs = [
    ("BEST",   "Best Quality - 20 steps dpmpp_3m",  {"seed":42,"steps":20,"cfg":1.0,"sampler":"dpmpp_3m","scheduler":"sgm_uniform","denoise":0.55,"guidance":4.0}),
    ("BALANCED","Balanced - 8 steps dpmpp_2m",       {"seed":42,"steps":8,"cfg":1.0,"sampler":"dpmpp_2m","scheduler":"simple","denoise":0.45,"guidance":3.0}),
    ("SPEEDY",  "Speedy - 4 steps euler",             {"seed":42,"steps":4,"cfg":1.0,"sampler":"euler","scheduler":"simple","denoise":0.35,"guidance":2.0}),
]

results = []
for tag, desc, cfg in configs:
    print(f"\n=== {tag}: {desc} ===")
    
    wf = {
        "1":{"class_type":"LoadImage","inputs":{"image":fn}},
        "2":{"class_type":"VAELoader","inputs":{"vae_name":"flux-vae-bf16.safetensors"}},
        "3":{"class_type":"UNETLoader","inputs":{"unet_name":"flux1-dev-fp8-e4m3fn.safetensors","weight_dtype":"default"}},
        "4":{"class_type":"DualCLIPLoader","inputs":{"clip_name1":"clip_l.safetensors","clip_name2":"t5xxl_fp16.safetensors","type":"flux"}},
        "5":{"class_type":"VAEEncode","inputs":{"pixels":["1",0],"vae":["2",0]}},
        "6":{"class_type":"CLIPTextEncodeFlux","inputs":{"clip":["4",0],"clip_l":CLIP_L,"t5xxl":T5XXL,"guidance":cfg["guidance"]}},
        "7":{"class_type":"KSampler","inputs":{
            "seed":cfg["seed"],"steps":cfg["steps"],"cfg":cfg["cfg"],
            "sampler_name":cfg["sampler"],"scheduler":cfg["scheduler"],
            "denoise":cfg["denoise"],
            "model":["3",0],"positive":["6",0],"negative":["6",0],
            "latent_image":["5",0]
        }},
        "8":{"class_type":"VAEDecode","inputs":{"samples":["7",0],"vae":["2",0]}},
        "9":{"class_type":"SaveImage","inputs":{"filename_prefix":f"inzing_{tag.lower()}","images":["8",0]}}
    }
    
    start = time.time()
    r = requests.post(f"{COMFY}/prompt", json={"prompt":wf, "client_id":str(uuid.uuid4())})
    if r.status_code != 200:
        print(f"  ❌ Submit: {r.status_code} {r.text[:100]}")
        continue
    
    pid = r.json()["prompt_id"]
    print(f"  ⏳ {pid}...")
    
    duration, outputs = poll(pid)
    if outputs:
        for nid,no in outputs.items():
            for img in no.get("images",[]):
                ir = requests.get(f"{COMFY}/view?filename={img['filename']}&type=output")
                op = os.path.join(OUT, img['filename'])
                with open(op,'wb') as f: f.write(ir.content)
                size_kb = len(ir.content)//1024
                print(f"  ✅ {duration:.1f}s | {op} ({size_kb}KB)")
                results.append({"tag":tag,"desc":desc,"path":op,"duration":duration,"size":size_kb,"settings":cfg})
    else:
        print(f"  ❌ Timeout")

print(f"\n{'='*60}")
print(f"RESULTS ({len(results)}/3):")
for r in results:
    print(f"\n  {r['tag']}: {r['desc']}")
    print(f"    Duration: {r['duration']:.1f}s")
    print(f"    File: {r['path']} ({r['size']}KB)")
    print(f"    Settings: {r['settings']}")

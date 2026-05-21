#!/usr/bin/env python3
"""Generate all 6 communities with RealVisXL img2img — fast, local, free."""
import requests, json, os, time, uuid

COMFY = "http://127.0.0.1:8188"
OUT = "img/lokal"
os.makedirs(OUT, exist_ok=True)

def up(path):
    with open(path,'rb') as f:
        r = requests.post(f"{COMFY}/upload/image", files={"image":(os.path.basename(path),f,"image/png")}, data={"type":"input","overwrite":"true"}, timeout=30)
    return r.json()["name"] if r.ok else None

def poll(pid, timeout=300):
    t=time.time()
    while time.time()-t<timeout:
        try:
            r=requests.get(f"{COMFY}/history/{pid}",timeout=5)
            if r.status_code==200 and pid in r.json():
                h=r.json()[pid]
                if h['status'].get('completed'): return h.get('outputs',{})
        except: pass
        time.sleep(2)
    return None

jobs = [
    ("innsbruck",      "img/bezirke/innsbruck_stadt.png",
     "modern minimalist flat vector coat of arms redesign, red shield with two white towers connected by white bridge, clean geometric shapes, bold flat colors red white gold, simplified minimalist heraldic style, no text, premium vector illustration"),
    ("wattens",        "img/orte/innsbruck-land/wattens.png",
     "modern minimalist flat vector coat of arms redesign, diagonal shield black and light blue, white wavy band, six-pointed star, celestial circle, clean geometric shapes, bold flat colors, simplified minimalist heraldic style, no text"),
    ("zirl",           "img/orte/innsbruck-land/zirl.png",
     "modern minimalist flat vector coat of arms redesign, heraldic shield with clean geometric shapes, bold flat colors, simplified minimalist Tyrolean heraldic style, no text, premium vector illustration"),
    ("hall_in_tirol",  "img/orte/innsbruck-land/hall_in_tirol.png",
     "modern minimalist flat vector coat of arms redesign, golden lion rampant on black and red divided shield, clean geometric shapes, bold flat colors gold red black, simplified minimalist heraldic style, no text"),
    ("kitzbuehel",     "img/orte/kitzbühel/kitzbühel.png",
     "modern minimalist flat vector coat of arms redesign, red chamois horn on white shield, clean geometric shapes, bold flat colors red white, simplified minimalist Tyrolean heraldic style, no text"),
    ("alpbach",        "img/orte/kufstein/alpbach.png",
     "modern minimalist flat vector coat of arms redesign, green hill with silver fir tree, diagonal silver band, clean geometric shapes, bold flat colors green silver white, simplified minimalist heraldic style, no text"),
]

for name, img_path, prompt in jobs:
    print(f"\n=== {name} ===")
    fn = up(img_path)
    if not fn: print("  ❌ Upload"); continue

    wf = {
        "1":{"class_type":"LoadImage","inputs":{"image":fn}},
        "4":{"class_type":"CheckpointLoaderSimple","inputs":{"ckpt_name":"RealVisXL_V4.0.safetensors"}},
        "12":{"class_type":"VAEEncode","inputs":{"pixels":["1",0],"vae":["4",2]}},
        "6":{"class_type":"CLIPTextEncode","inputs":{"text":prompt,"clip":["4",1]}},
        "7":{"class_type":"CLIPTextEncode","inputs":{"text":"ugly, blurry, low quality, deformed, text, watermark, messy, noisy, photorealistic, 3d","clip":["4",1]}},
        "3":{"class_type":"KSampler","inputs":{"seed":42,"steps":25,"cfg":7.0,"sampler_name":"dpmpp_2m","scheduler":"karras","denoise":0.45,"model":["4",0],"positive":["6",0],"negative":["7",0],"latent_image":["12",0]}},
        "8":{"class_type":"VAEDecode","inputs":{"samples":["3",0],"vae":["4",2]}},
        "9":{"class_type":"SaveImage","inputs":{"filename_prefix":f"wappen_{name}_realvisxl_modern","images":["8",0]}}
    }

    r = requests.post(f"{COMFY}/prompt", json={"prompt":wf, "client_id":str(uuid.uuid4())})
    if r.status_code != 200: print(f"  ❌ {r.status_code}"); continue

    pid = r.json()["prompt_id"]
    print(f"  ⏳ Generiere...")
    out = poll(pid)
    if out:
        for nid,no in out.items():
            for img in no.get("images",[]):
                ir = requests.get(f"{COMFY}/view?filename={img['filename']}&type=output")
                op = os.path.join(OUT, img['filename'])
                with open(op,'wb') as f: f.write(ir.content)
                print(f"  ✅ {op} ({len(ir.content)//1024}KB)")
    else:
        print(f"  ❌ Timeout")

print(f"\n✅ 6 RealVisXL Bilder in {OUT}/")

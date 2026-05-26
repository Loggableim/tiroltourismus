#!/usr/bin/env python3
"""Hall in Tirol — high-res FLUX Dev, modern style, portrait format."""
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

fn = up("img/orte/innsbruck-land/hall_in_tirol.png")
print(f"Upload: {fn}")

wf = {
    "1":{"class_type":"LoadImage","inputs":{"image":fn}},
    "2":{"class_type":"ImageScale","inputs":{"image":["1",0],"upscale_method":"lanczos","width":768,"height":896,"crop":"disabled"}},
    "3":{"class_type":"VAELoader","inputs":{"vae_name":"flux-vae-bf16.safetensors"}},
    "4":{"class_type":"UNETLoader","inputs":{"unet_name":"flux1-dev-fp8-e4m3fn.safetensors","weight_dtype":"default"}},
    "5":{"class_type":"DualCLIPLoader","inputs":{"clip_name1":"clip_l.safetensors","clip_name2":"t5xxl_fp16.safetensors","type":"flux"}},
    "6":{"class_type":"VAEEncode","inputs":{"pixels":["2",0],"vae":["3",0]}},
    "7":{"class_type":"CLIPTextEncodeFlux","inputs":{"clip":["5",0],
        "clip_l":"modern minimalist flat vector coat of arms redesign, golden lion rampant on black and red divided shield, clean geometric shapes, bold flat colors gold red black, simplified minimalist heraldic style, no text, premium quality",
        "t5xxl":"modern minimalist flat vector coat of arms redesign for Hall in Tirol, heraldic shield divided black and red with golden lion rampant, clean geometric simplified shapes, bold flat vector colors gold black and red, minimalist logo-style heraldry, premium quality vector illustration, no text, no watermark, professional heraldic design",
        "guidance":3.5}},
    "8":{"class_type":"KSampler","inputs":{"seed":42,"steps":12,"cfg":1.0,"sampler_name":"dpmpp_2m","scheduler":"sgm_uniform","denoise":0.55,"model":["4",0],"positive":["7",0],"negative":["7",0],"latent_image":["6",0]}},
    "9":{"class_type":"VAEDecode","inputs":{"samples":["8",0],"vae":["3",0]}},
    "10":{"class_type":"SaveImage","inputs":{"filename_prefix":"wappen_hall_in_tirol_modern","images":["9",0]}}
}

start = time.time()
r = requests.post(f"{COMFY}/prompt", json={"prompt":wf, "client_id":str(uuid.uuid4())})
if r.status_code != 200:
    print(f"Submit: {r.status_code} {r.text[:200]}")
    exit(1)

pid = r.json()["prompt_id"]
print(f"⏳ {pid}...")

while True:
    r = requests.get(f"{COMFY}/history/{pid}", timeout=10)
    if r.status_code == 200 and pid in r.json():
        h = r.json()[pid]
        if h['status'].get('completed'):
            elapsed = time.time()-start
            for nid,no in h.get('outputs',{}).items():
                for img in no.get('images',[]):
                    ir = requests.get(f"{COMFY}/view?filename={img['filename']}&type=output")
                    op = os.path.join(OUT, img['filename'])
                    with open(op,'wb') as f: f.write(ir.content)
                    sz = len(ir.content)//1024
                    from PIL import Image
                    im = Image.open(op)
                    print(f"✅ {elapsed:.0f}s | {op} ({sz}KB) | {im.size}")
            break
        if h['status'].get('status_str') == 'error':
            print(f"❌ {h['status']}")
            break
    time.sleep(2)

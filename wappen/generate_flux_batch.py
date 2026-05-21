#!/usr/bin/env python3
"""FLUX Dev FP8 img2img Batch — 6 Wappen, RTX 3060 optimiert (16 steps)."""
import requests, json, os, time, uuid

COMFY = "http://127.0.0.1:8188"
OUT = "img/lokal"
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
                if h['status'].get('completed'): return h.get('outputs',{})
        except: pass
        time.sleep(5)
    return None

def poll_queue(timeout=900):
    t=time.time()
    while time.time()-t<timeout:
        try:
            q=requests.get(f"{COMFY}/queue",timeout=10).json()
            if len(q['queue_running'])==0 and len(q['queue_pending'])==0: return True
        except: pass
        time.sleep(10)
    return False

jobs = [
    ("innsbruck", "img/bezirke/innsbruck_stadt.png",
     "modern minimalist flat vector coat of arms, two white towers on red shield connected by white bridge, clean geometric shapes, bold flat colors red white gold",
     "modern minimalist flat vector coat of arms redesign for Innsbruck city, heraldic red shield with two white stylized towers connected by white arched bridge, golden details, clean geometric simplified shapes, bold flat vector colors red white gold, minimalist logo-style heraldry, premium quality, no text"),
    ("wattens", "img/orte/innsbruck-land/wattens.png",
     "modern minimalist flat vector coat of arms, diagonal shield black light blue, white wavy band, six-pointed star, celestial symbol, clean geometric shapes, bold flat colors",
     "modern minimalist flat vector coat of arms redesign for Wattens, heraldic shield diagonally divided black and light blue, white wavy diagonal band, six-pointed gold star in diamond motif, celestial circle, clean geometric shapes, bold flat colors, minimalist logo-style heraldry, no text"),
    ("zirl", "img/orte/innsbruck-land/zirl.png",
     "modern minimalist flat vector coat of arms, heraldic shield with clean geometric shapes, bold flat colors, simplified Tyrolean style",
     "modern minimalist flat vector coat of arms redesign for Zirl, Tyrolean heraldic shield with clean geometric shapes, bold flat colors, minimalist logo-style heraldry, modern reinterpretation, premium quality, no text"),
    ("hall_in_tirol", "img/orte/innsbruck-land/hall_in_tirol.png",
     "modern minimalist flat vector coat of arms, golden lion rampant on black and red divided shield, clean geometric shapes, bold flat colors gold red black",
     "modern minimalist flat vector coat of arms redesign for Hall in Tirol, heraldic shield divided black and red with golden lion rampant, clean geometric shapes, bold flat colors gold black red, minimalist logo-style heraldry, no text"),
    ("kitzbuehel", "img/orte/kitzbühel/kitzbühel.png",
     "modern minimalist flat vector coat of arms, red chamois horn on white shield, clean geometric shapes, bold flat colors red white, Tyrolean style",
     "modern minimalist flat vector coat of arms redesign for Kitzbühel, heraldic white shield with stylized red chamois horn, clean geometric shapes, bold flat colors red and white, minimalist logo-style Tyrolean heraldry, no text"),
    ("alpbach", "img/orte/kufstein/alpbach.png",
     "modern minimalist flat vector coat of arms, green hill with silver fir tree, diagonal silver band, clean geometric shapes, bold flat colors green silver white",
     "modern minimalist flat vector coat of arms redesign for Alpbach, heraldic shield with green ground and stylized silver fir tree, diagonal silver bend, clean geometric shapes, bold flat colors green silver white, minimalist logo-style heraldry, no text"),
]

for name, img_path, clip_l, t5xxl in jobs:
    print(f"\n=== {name} ===")
    fn = up(img_path)
    if not fn: print("  ❌ Upload"); continue

    wf = {
        "1":{"class_type":"LoadImage","inputs":{"image":fn}},
        "2":{"class_type":"VAELoader","inputs":{"vae_name":"flux-vae-bf16.safetensors"}},
        "3":{"class_type":"UNETLoader","inputs":{"unet_name":"flux1-dev-fp8-e4m3fn.safetensors","weight_dtype":"default"}},
        "4":{"class_type":"DualCLIPLoader","inputs":{"clip_name1":"clip_l.safetensors","clip_name2":"t5xxl_fp16.safetensors","type":"flux"}},
        "5":{"class_type":"VAEEncode","inputs":{"pixels":["1",0],"vae":["2",0]}},
        "6":{"class_type":"CLIPTextEncodeFlux","inputs":{"clip":["4",0],"clip_l":clip_l,"t5xxl":t5xxl,"guidance":3.5}},
        "7":{"class_type":"KSampler","inputs":{"seed":42,"steps":16,"cfg":1.0,"sampler_name":"euler","scheduler":"simple","denoise":0.5,"model":["3",0],"positive":["6",0],"negative":["6",0],"latent_image":["5",0]}},
        "8":{"class_type":"VAEDecode","inputs":{"samples":["7",0],"vae":["2",0]}},
        "9":{"class_type":"SaveImage","inputs":{"filename_prefix":f"wappen_{name}_flux_modern","images":["8",0]}}
    }

    r = requests.post(f"{COMFY}/prompt", json={"prompt":wf, "client_id":str(uuid.uuid4())})
    if r.status_code != 200:
        print(f"  ❌ Submit: {r.status_code} — queue full, waiting...")
        poll_queue(); r = requests.post(f"{COMFY}/prompt", json={"prompt":wf, "client_id":str(uuid.uuid4())})
        if r.status_code != 200: print(f"  ❌ Retry: {r.text[:200]}"); continue

    pid = r.json()["prompt_id"]
    print(f"  ⏳ FLUX ({pid}) 16 steps...")
    out = poll(pid)
    if out:
        for nid,no in out.items():
            for img in no.get("images",[]):
                ir = requests.get(f"{COMFY}/view?filename={img['filename']}&type=output")
                op = os.path.join(OUT, img['filename'])
                with open(op,'wb') as f: f.write(ir.content)
                print(f"  ✅ {img['filename']} ({len(ir.content)//1024}KB)")
    else:
        print(f"  ❌ No result")

ok = sum(1 for n in ["innsbruck","wattens","zirl","hall_in_tirol","kitzbuehel","alpbach"] if any(f.startswith(f"wappen_{n}_flux_modern") for f in os.listdir(OUT)))
print(f"\n✅ {ok}/6 FLUX Dev Bilder in {OUT}/")

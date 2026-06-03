"""
Generate homepage images via ComfyUI - Colored Pencil Sketch style
Run from terminal to bypass execute_code sandbox
"""
import json, time, urllib.request, os, shutil

COMFY = "http://127.0.0.1:8188"
OUTPUT = r"E:\HermesPortable\ComfyUI\output"
DST = r"F:\tiroltourismus\public\assets\images"
HERO_DST = r"F:\tiroltourismus\public\brand\hero-logos"

def gen(prompt, negative, width=1216, height=832, steps=25, prefix="gen", cfg=7.0, model="RealVisXL_V4.0.safetensors"):
    seed = int(time.time() * 1000) % 2**32
    wf = {
        "4": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": model}},
        "5": {"class_type": "EmptyLatentImage", "inputs": {"width": width, "height": height, "batch_size": 1}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": ["4", 1]}},
        "7": {"class_type": "CLIPTextEncode", "inputs": {"text": negative, "clip": ["4", 1]}},
        "3": {"class_type": "KSampler", "inputs": {
            "seed": seed, "steps": steps, "cfg": cfg,
            "sampler_name": "dpmpp_2m", "scheduler": "karras", "denoise": 1.0,
            "model": ["4", 0], "positive": ["6", 0], "negative": ["7", 0],
            "latent_image": ["5", 0]
        }},
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["4", 2]}},
        "9": {"class_type": "SaveImage", "inputs": {"filename_prefix": prefix, "images": ["8", 0]}}
    }
    data = json.dumps({"prompt": wf, "client_id": f"gen_{prefix}"}).encode()
    req = urllib.request.Request(f"{COMFY}/prompt", data=data, headers={"Content-Type": "application/json"})
    resp = json.loads(urllib.request.urlopen(req, timeout=60).read())
    pid = resp["prompt_id"]
    print(f"  Submitted {prefix} (pid={pid}) seed={seed}")
    
    for i in range(120):
        time.sleep(3)
        try:
            req = urllib.request.Request(f"{COMFY}/history/{pid}")
            hist = json.loads(urllib.request.urlopen(req, timeout=10).read())
        except: continue
        if pid in hist:
            s = hist[pid].get("status", {})
            if s.get("completed"):
                for nid, o in hist[pid].get("outputs", {}).items():
                    for img in o.get("images", []):
                        fn = img["filename"]
                        src = os.path.join(OUTPUT, fn)
                        if os.path.exists(src):
                            print(f"  DONE: {fn} ({os.path.getsize(src)//1024} KB)")
                            return src
                return None
            elif s.get("status_str") == "error":
                print(f"  ERROR: {s}")
                return None
    print("  TIMEOUT")
    return None

def copy(src, dst_name):
    dst = os.path.join(DST, dst_name)
    shutil.copy2(src, dst)
    # Also convert to .webp if needed
    webp = dst.replace('.png', '.webp').replace('.jpg', '.webp')
    if dst.endswith('.png'):
        from PIL import Image
        img = Image.open(dst)
        img.save(webp, 'WEBP', quality=85)
        print(f"  -> {dst_name.replace('.png','.webp')} ({os.path.getsize(webp)//1024} KB)")
    return dst

SKETCH_PROMPT_PREFIX = "Colored pencil sketch drawing on cream paper of"
SKETCH_NEGATIVE = "photorealistic, 3d render, photograph, realistic texture, hyperrealistic, cinematic lighting, shadows, gradient, oil painting, airbrush, digital art, smooth shading, dark, gloomy, oversaturated, harsh lines"

# ====== 1. HERO IMAGE ======
print("=== 1. HERO IMAGE ===")
src = gen(
    prompt=f"{SKETCH_PROMPT_PREFIX} a breathtaking panoramic view of the Austrian Tyrolean Alps, majestic snow-covered mountain peaks, a charming alpine village with traditional wooden houses and a church spire in a green valley, crystal clear mountain river, wildflowers in the foreground, warm golden sunlight illuminating the scene, inviting and beautiful travel destination, highly detailed artistic colored pencil landscape",
    negative=SKETCH_NEGATIVE,
    width=1664, height=960, steps=28, prefix="hero_xl", model="sd_xl_base_1.0.safetensors"
)
if src:
    dst = os.path.join(HERO_DST, "hero_colorsketch.png")
    shutil.copy2(src, dst)
    # Convert to webp
    from PIL import Image
    webp_dst = dst.replace('.png', '.webp')
    Image.open(dst).save(webp_dst, 'WEBP', quality=88)
    print(f"  HERO: {dst.replace('.png','.webp')} ({os.path.getsize(webp_dst)//1024} KB)")

# ====== 2. REGION IMAGES ======
print("\n=== 2. REGION IMAGES ===")
regions = [
    ("innsbruck", "Innsbruck, capital of Tyrol, with the iconic Nordkette mountain range towering behind the historic old town with golden roof, colorful buildings, alpine panorama"),
    ("oetztal", "Oetztal valley in Tyrol, dramatic alpine scenery with glaciers, deep green valley, traditional Tyrolean farms, waterfall cascading down rocky cliff"),
    ("zillertal", "Zillertal valley in Tyrol, lush green alpine pastures dotted with wildflowers, traditional wooden farmhouses, majestic mountains in background, crystal clear stream"),
]

for slug, desc in regions:
    print(f"\n  --- {slug} ---")
    src = gen(
        prompt=f"{SKETCH_PROMPT_PREFIX} {desc}, warm sunny day, detailed colored pencil art, beautiful travel illustration, soft pastel colors",
        negative=SKETCH_NEGATIVE,
        width=1216, height=832, steps=25, prefix=f"reg_{slug}"
    )
    if src:
        copy(src, f"region_{slug}_sketch.png")

print("\n✅ DONE")

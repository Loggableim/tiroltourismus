#!/usr/bin/env python3
"""Generate 3 styles × 3 Orte × 2 Models = 18 coat of arms images.

Styles: classic, modern, tiroltourismus (replaces woodcut)
Models: FLUX.2-pro, Qwen-Image-Edit
Orte: Innsbruck Stadt, Götzens, Wattens
"""
import requests, json, base64, os, sys, time
from concurrent.futures import ThreadPoolExecutor, as_completed

API_KEY = "sk-jflggfbmhvbarpjfgifnhusjvyggksbqbmtdebjxrvjtqwnl"
URL = "https://api.siliconflow.com/v1/images/generations"
OUT_DIR = "img/generiert"
os.makedirs(OUT_DIR, exist_ok=True)

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# === Image references (base64) ===
def load_img(path):
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    return f"data:image/png;base64,{b64}"

refs = {
    "innsbruck": load_img("img/bezirke/innsbruck_stadt.png"),
    "gotzens": load_img("img/orte/innsbruck-land/götzens.png"),
    "wattens": load_img("img/orte/innsbruck-land/wattens.png"),
}

# === Job definitions ===
# 3 Styles × 3 Orte × 2 Models
STYLES = {
    "classic": {
        "name": "Klassisch",
        "desc": "Traditionell-heraldische Darstellung",
    },
    "modern": {
        "name": "Modern",
        "desc": "Clean geometrisch-minimalistisch",
    },
    "tiroltourismus": {
        "name": "Tirol-Tourismus",
        "desc": "Optimiert für tiroltourismus.com mit warmen Gold-Rot-Tönen",
    },
}

ORTE_PROMPTS = {
    "innsbruck": {
        "img": refs["innsbruck"],
        "subject": "Innsbruck city coat of arms with two towers connected by a bridge on a red shield",
    },
    "gotzens": {
        "img": refs["gotzens"],
        "subject": "Götzens coat of arms with a white squirrel holding a golden egg on a blue shield",
    },
    "wattens": {
        "img": refs["wattens"],
        "subject": "Wattens coat of arms, diagonally divided shield black and light blue, white wavy band, celestial circle with cross and six-pointed star in diamond",
    },
}

# Style-specific prompt suffixes
STYLE_PROMPTS = {
    "classic": {
        "flux": ", traditional European heraldic style, detailed heraldic illustration, clean vector lines, flat heraldic colors, black outline, symmetrical, coat of arms, no text, professional heraldic rendering",
        "qwen": "Transform this coat of arms into a traditional European heraldic illustration style. Detailed heraldic rendering, clean vector lines, flat colors, black outlines, symmetrical composition, professional coat of arms, no text",
    },
    "modern": {
        "flux": ", modern minimalist flat geometric style, clean shapes, simplified forms, contemporary vector art, flat design, bold colors, minimalist, logo-like appearance, no text, premium quality",
        "qwen": "Transform this coat of arms into a modern minimalist flat geometric design. Clean simplified shapes, contemporary vector art style, flat bold colors, minimalist logo-like appearance, premium quality, no text",
    },
    "tiroltourismus": {
        "flux": ", elegant alpine tourism branding style, warm gold and red tones, premium travel aesthetic, refined heraldic elements, Tirol Austria alpine feel, sophisticated color palette, luxury tourism brand style, no text, high quality",
        "qwen": "Transform this coat of arms into an elegant alpine tourism branding design. Warm gold and red color palette, premium travel aesthetic, refined heraldic elements, Tirol Austria alpine feel, sophisticated luxury tourism brand style, no text",
    },
}

# Build all jobs
jobs = []
seed_base = 1001
for model_name, model_id in [("flux", "black-forest-labs/FLUX.2-pro"), ("qwen", "Qwen/Qwen-Image-Edit")]:
    for style_key in ["classic", "modern", "tiroltourismus"]:
        for ort_key in ["innsbruck", "gotzens", "wattens"]:
            jid = f"{ort_key}_{style_key}_{model_name}"
            prompt = ORTE_PROMPTS[ort_key]["subject"] + STYLE_PROMPTS[style_key][model_name]
            jobs.append({
                "id": jid,
                "model": model_id,
                "prompt": prompt,
                "image": ORTE_PROMPTS[ort_key]["img"],
                "seed": seed_base,
                "style_key": style_key,
                "ort_key": ort_key,
                "model_name": model_name,
            })
            seed_base += 1

print(f"=== {len(jobs)} Jobs ===\n")

def generate(job):
    jid = job["id"]
    payload = {
        "model": job["model"],
        "prompt": job["prompt"],
        "image": job["image"],
        "n": 1,
        "size": "1024x1024",
        "seed": job["seed"]
    }
    try:
        sys.stderr.write(f"  [{jid}] Sending...\n")
        resp = requests.post(URL, json=payload, headers=headers, timeout=120)
        result = resp.json()
        if resp.status_code != 200:
            return jid, None, f"HTTP {resp.status_code}: {str(result)[:200]}"
        
        img_url = result["images"][0]["url"]
        sys.stderr.write(f"  [{jid}] Downloading...\n")
        
        img_resp = requests.get(img_url, timeout=60)
        outpath = os.path.join(OUT_DIR, f"wappen_{jid}.png")
        with open(outpath, "wb") as f:
            f.write(img_resp.content)
        return jid, outpath, None
    except Exception as e:
        return jid, None, str(e)

# Run in parallel (max 3 workers to avoid rate limits)
results = []
with ThreadPoolExecutor(max_workers=3) as ex:
    fut = {ex.submit(generate, j): j["id"] for j in jobs}
    for f in as_completed(fut):
        jid, path, err = f.result()
        if err:
            print(f"❌ {jid}: {err}")
        else:
            size = os.path.getsize(path)
            print(f"✅ {jid}: {path} ({size} bytes)")
            results.append((jid, path))

print(f"\n=== Fertig: {len(results)}/{len(jobs)} ===")

# Print MEDIA paths
for jid, path in sorted(results):
    ort, style, model = jid.rsplit('_', 2)
    print(f"  MEDIA:{os.path.abspath(path)}")

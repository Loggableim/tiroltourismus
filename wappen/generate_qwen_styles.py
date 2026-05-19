#!/usr/bin/env python3
"""Generate 3 styles with Qwen/Qwen-Image-Edit via img2img."""
import requests, json, base64, os, sys
from concurrent.futures import ThreadPoolExecutor, as_completed

API_KEY = "sk-jflggfbmhvbarpjfgifnhusjvyggksbqbmtdebjxrvjtqwnl"
URL = "https://api.siliconflow.com/v1/images/generations"
OUT_DIR = "img/generiert"
os.makedirs(OUT_DIR, exist_ok=True)

with open("img/bezirke/innsbruck_stadt.png", "rb") as f:
    img_b64 = base64.b64encode(f.read()).decode("utf-8")
data_uri = f"data:image/png;base64,{img_b64}"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

jobs = [
    {
        "id": "qwen_klassisch",
        "prompt": "Transform this coat of arms into a classic European heraldic illustration. Red shield (gules) with black border. Two symmetrical silver-white stone towers with steep pointed roofs. Wooden bridge between towers. Flat heraldic colors, clean vector style, traditional coat of arms, no text",
        "seed": 94401
    },
    {
        "id": "qwen_modern",
        "prompt": "Transform this coat of arms into a modern minimalist flat design. Clean geometric shapes, two simplified towers connected by a bridge, red and white color scheme, contemporary vector art, flat design, premium logo style, no text",
        "seed": 95502
    },
    {
        "id": "qwen_woodcut",
        "prompt": "Transform this coat of arms into a medieval woodcut print style. Rough textured lines, hand-carved block print look, rustic paper texture, black ink cross-hatching, vintage historical print aesthetic, old world charm, no text",
        "seed": 96603
    }
]

def generate(job):
    jid = job["id"]
    payload = {
        "model": "Qwen/Qwen-Image-Edit",
        "prompt": job["prompt"],
        "image": data_uri,
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
        seed = result.get("seed", "N/A")
        sys.stderr.write(f"  [{jid}] Seed={seed}, downloading...\n")
        
        img_resp = requests.get(img_url, timeout=60)
        outpath = os.path.join(OUT_DIR, f"wappen_innsbruck_{jid}.png")
        with open(outpath, "wb") as f:
            f.write(img_resp.content)
        return jid, outpath, None
    except Exception as e:
        return jid, None, str(e)

print("=== Generate 3 Qwen-Image-Edit Styles ===")

with ThreadPoolExecutor(max_workers=3) as ex:
    fut = {ex.submit(generate, j): j["id"] for j in jobs}
    for f in as_completed(fut):
        jid, path, err = f.result()
        if err:
            print(f"❌ {jid}: {err}")
        else:
            size = os.path.getsize(path)
            print(f"✅ {jid}: {path} ({size} bytes)")

print("\nFertig!")

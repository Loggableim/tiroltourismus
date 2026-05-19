#!/usr/bin/env python3
"""Generate 3 styles of Innsbruck coat of arms via FLUX.2-pro img2img."""
import requests, json, base64, os, sys, time
from concurrent.futures import ThreadPoolExecutor, as_completed

API_KEY = "sk-jflggfbmhvbarpjfgifnhusjvyggksbqbmtdebjxrvjtqwnl"
URL = "https://api.siliconflow.com/v1/images/generations"
OUT_DIR = "img/generiert"
os.makedirs(OUT_DIR, exist_ok=True)

# Read reference image
with open("img/bezirke/innsbruck_stadt.png", "rb") as f:
    img_b64 = base64.b64encode(f.read()).decode("utf-8")
data_uri = f"data:image/png;base64,{img_b64}"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

jobs = [
    {
        "id": "klassisch",
        "prompt": "Heraldic coat of arms, traditional European heraldry style. Red shield with thick black border. Two symmetrical silver-white stone towers with steep gabled roofs, each with a square window. Wooden bridge connecting the towers. Clean vector lines, flat heraldic colors, detailed stone texture on roofs, symmetrical composition, professional heraldic illustration, high quality, no text",
        "strength": 0.55,
        "seed": 61101
    },
    {
        "id": "modern",
        "prompt": "Modern minimalist coat of arms design, flat geometric style. Red background, clean white geometric shapes representing two towers connected by a bridge. Simplified architecture, rounded corners, subtle gradients, contemporary vector art style, clean lines, flat design, symmetrical, modern heraldry reinterpretation, premium quality, no text",
        "strength": 0.40,
        "seed": 72202
    },
    {
        "id": "woodcut",
        "prompt": "Medieval woodcut illustration style. Hand-carved wooden block print of a coat of arms. Red shield, two towers with pointed roofs, wooden bridge, rough textured lines, rustic paper texture background, black ink lines, cross-hatching shading, vintage old world charm, historical print aesthetic, rough edges, no text",
        "strength": 0.45,
        "seed": 83303
    }
]

def generate(job):
    jid = job["id"]
    payload = {
        "model": "black-forest-labs/FLUX.2-pro",
        "prompt": job["prompt"],
        "image": data_uri,
        "image_strength": job["strength"],
        "n": 1,
        "size": "1024x1024",
        "seed": job["seed"]
    }
    try:
        sys.stderr.write(f"  [{jid}] Sending request...\n")
        resp = requests.post(URL, json=payload, headers=headers, timeout=120)
        result = resp.json()
        if resp.status_code != 200:
            return jid, None, f"HTTP {resp.status_code}: {str(result)[:200]}"
        
        img_url = result["images"][0]["url"]
        seed = result.get("seed", "N/A")
        sys.stderr.write(f"  [{jid}] Seed={seed}, downloading...\n")
        
        img_resp = requests.get(img_url, timeout=60)
        outpath = os.path.join(OUT_DIR, f"wappen_innsbruck_flux_{jid}.png")
        with open(outpath, "wb") as f:
            f.write(img_resp.content)
        return jid, outpath, None
    except Exception as e:
        return jid, None, str(e)

print("=== Generate 3 FLUX.2-pro Styles ===")
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

print(f"\nFertig: {len(results)}/3 generiert")
for jid, path in results:
    print(f"  {jid}: MEDIA:{os.path.abspath(path)}")

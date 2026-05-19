#!/usr/bin/env python3
"""Batch-generate Qwen-Image-Edit Modern style for ALL 276 municipalities.

Uses img2img: sends the original Wikipedia coat of arms as reference,
prompts the model to transform it to modern-minimalist style.
"""
import requests, json, base64, os, sys, time, re, random
from concurrent.futures import ThreadPoolExecutor, as_completed

LOG_FILE = "batch_qwen_modern.log"
OUT_DIR = "img/qwen_modern"
URL = "https://api.siliconflow.com/v1/images/generations"
OUT_DIR = "img/qwen_modern"
os.makedirs(OUT_DIR, exist_ok=True)

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# Modern style prompt (same for all — img2img preserves the specific subject)
MODERN_PROMPT = (
    "Transform this coat of arms into a modern minimalist flat geometric design. "
    "Clean simplified shapes, flat bold colors, contemporary vector art style, "
    "minimalist logo-like appearance, premium quality, no text, no letters"
)

def sanitize_name(name):
    """Create a safe filesystem-friendly name."""
    s = name.lower().replace(' ', '_')
    s = s.replace('ä', 'ae').replace('ö', 'oe').replace('ü', 'ue').replace('ß', 'ss')
    s = s.replace('(', '').replace(')', '').replace('.', '').replace(',', '')
    s = re.sub(r'[^a-z0-9_-]', '', s)
    return s[:60]  # keep it reasonable

def load_jobs():
    """Read all municipaties from page data, return list of jobs."""
    with open('wappen_page_data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    jobs = []
    for bezirk in data['bezirke']:
        bname = bezirk['name']
        for ort in bezirk['orte']:
            oname = ort['name']
            img_path = ort['img']
            
            # Unique ID
            safe_bezirk = sanitize_name(bname)
            safe_ort = sanitize_name(oname)
            uid = f"{safe_bezirk}_{safe_ort}"
            
            jobs.append({
                'id': uid,
                'bezirk': bname,
                'ort': oname,
                'img_path': img_path,
                'output': f"{OUT_DIR}/{uid}.png",
            })
    return jobs

def generate(job):
    """Generate one Qwen Modern image via img2img."""
    try:
        # Read and encode image
        with open(job['img_path'], 'rb') as f:
            b64 = base64.b64encode(f.read()).decode('utf-8')
        data_uri = f"data:image/png;base64,{b64}"
        
        payload = {
            "model": "Qwen/Qwen-Image-Edit",
            "prompt": MODERN_PROMPT,
            "image": data_uri,
            "n": 1,
            "size": "1024x1024",
            "seed": random.randint(1, 999999)
        }
        
        resp = requests.post(URL, json=payload, headers=headers, timeout=120)
        result = resp.json()
        
        if resp.status_code != 200:
            return job['id'], None, f"HTTP {resp.status_code}: {str(result)[:100]}"
        
        img_url = result["images"][0]["url"]
        img_resp = requests.get(img_url, timeout=60)
        
        with open(job['output'], 'wb') as f:
            f.write(img_resp.content)
        
        return job['id'], job['output'], None
    except Exception as e:
        return job['id'], None, str(e)

# === MAIN ===
jobs = load_jobs()
total = len(jobs)
print(f"=== {total} Jobs geladen ===")
print(f"Ausgabe-Verzeichnis: {OUT_DIR}")

# Count already done
already_done = sum(1 for j in jobs if os.path.exists(j['output']) and os.path.getsize(j['output']) > 1000)
print(f"Bereits vorhanden: {already_done}/{total}")

# Filter only new jobs
pending = [j for j in jobs if not (os.path.exists(j['output']) and os.path.getsize(j['output']) > 1000)]
print(f"Noch zu generieren: {len(pending)}")

if not pending:
    print("✅ Alle bereits generiert!")
    sys.exit(0)

# Generate in parallel (3 workers)
success = 0
failures = []
done_count = already_done

print(f"\nStarte Batch-Generierung (max 3 parallel)...")
print(f"Geschätzte Zeit: ~{len(pending) * 15 // 3 // 60} Minuten\n")

with ThreadPoolExecutor(max_workers=3) as ex:
    fut = {ex.submit(generate, j): j['id'] for j in pending}
    start_time = time.time()
    
    for f in as_completed(fut):
        jid, path, err = f.result()
        done_count += 1
        elapsed = time.time() - start_time
        remaining = len(pending) - (done_count - already_done)
        
        if err:
            failures.append((jid, err))
            print(f"  ❌ [{done_count}/{total}] {jid}: {err}")
        else:
            success += 1
            size = os.path.getsize(path)
            print(f"  ✅ [{done_count}/{total}] {jid} ({size//1024}KB)")

print(f"\n=== Fertig ===")
print(f"Erfolgreich: {success}/{len(pending)}")
print(f"Fehlgeschlagen: {len(failures)}")
print(f"Gesamt im Ordner: {len([f for f in os.listdir(OUT_DIR) if f.endswith('.png')])}")

if failures:
    print(f"\nFehlerdetails:")
    for jid, err in failures[:20]:
        print(f"  {jid}: {err}")
    if len(failures) > 20:
        print(f"  ... und {len(failures)-20} weitere")

# Write a manifest for the comparison page
manifest = []
for j in jobs:
    exists = os.path.exists(j['output']) and os.path.getsize(j['output']) > 100
    manifest.append({
        'bezirk': j['bezirk'],
        'ort': j['ort'],
        'original': j['img_path'],
        'qwen': j['output'] if exists else None,
    })

with open(f'{OUT_DIR}/manifest.json', 'w', encoding='utf-8') as f:
    json.dump(manifest, f, indent=2, ensure_ascii=False)
print(f"\nManifest gespeichert: {OUT_DIR}/manifest.json")

#!/usr/bin/env python3
"""Batch-generate Qwen-Image-Edit Modern style for ALL 276 municipalities.
Logs progress to batch_qwen_modern.log for monitoring.
"""
import requests, json, base64, os, sys, time, re, random
from concurrent.futures import ThreadPoolExecutor, as_completed

API_KEY = "sk-jflggfbmhvbarpjfgifnhusjvyggksbqbmtdebjxrvjtqwnl"
URL = "https://api.siliconflow.com/v1/images/generations"
OUT_DIR = "img/qwen_modern"
LOG = "batch_qwen_modern.log"
os.makedirs(OUT_DIR, exist_ok=True)

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

MODERN_PROMPT = (
    "Transform this coat of arms into a modern minimalist flat geometric design. "
    "Clean simplified shapes, flat bold colors, contemporary vector art style, "
    "minimalist logo-like appearance, premium quality, no text, no letters"
)

def log(msg):
    ts = time.strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with open(LOG, 'a', encoding='utf-8') as f:
        f.write(line + "\n")

def sanitize_name(name):
    s = name.lower().replace(' ', '_')
    s = s.replace('ä', 'ae').replace('ö', 'oe').replace('ü', 'ue').replace('ß', 'ss')
    s = s.replace('(', '').replace(')', '').replace('.', '').replace(',', '')
    s = re.sub(r'[^a-z0-9_-]', '', s)
    return s[:60]

def load_jobs():
    with open('wappen_page_data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    jobs = []
    for bezirk in data['bezirke']:
        bname = bezirk['name']
        for ort in bezirk['orte']:
            oname = ort['name']
            img_path = ort['img']
            safe_b = sanitize_name(bname)
            safe_o = sanitize_name(oname)
            uid = f"{safe_b}_{safe_o}"
            jobs.append({
                'id': uid, 'bezirk': bname, 'ort': oname,
                'img_path': img_path,
                'output': f"{OUT_DIR}/{uid}.png",
            })
    return jobs

def generate(job):
    """Generate one Qwen Modern image via img2img, with retries."""
    max_retries = 3
    for attempt in range(max_retries):
        try:
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

            resp = requests.post(URL, json=payload, headers=headers, timeout=180)
            result = resp.json()

            if resp.status_code != 200:
                if attempt < max_retries - 1:
                    time.sleep(5 * (attempt + 1))
                    continue
                return job['id'], None, f"HTTP {resp.status_code}"

            img_url = result["images"][0]["url"]
            img_resp = requests.get(img_url, timeout=120)
            with open(job['output'], 'wb') as f:
                f.write(img_resp.content)
            return job['id'], job['output'], None
        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                wait = 10 * (attempt + 1)
                log(f"  ⏱️ [{job['id']}] Timeout (Attempt {attempt+1}/{max_retries}), retry in {wait}s...")
                time.sleep(wait)
                continue
            return job['id'], None, "Timeout after retries"
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(5 * (attempt + 1))
                continue
            return job['id'], None, str(e)
    return job['id'], None, "Max retries exceeded"

# === MAIN ===
jobs = load_jobs()
total = len(jobs)
log(f"=== {total} Jobs geladen ===")
log(f"Ausgabe: {OUT_DIR}/")

already_done = sum(1 for j in jobs if os.path.exists(j['output']) and os.path.getsize(j['output']) > 1000)
log(f"Bereits vorhanden: {already_done}/{total}")

pending = [j for j in jobs if not (os.path.exists(j['output']) and os.path.getsize(j['output']) > 1000)]
log(f"Noch zu generieren: {len(pending)}")

if not pending:
    log("✅ Alle bereits generiert!")
    # Write manifest anyway
    manifest = [{'bezirk': j['bezirk'], 'ort': j['ort'], 'original': j['img_path'],
                 'qwen': j['output'] if os.path.exists(j['output']) and os.path.getsize(j['output']) > 100 else None}
                for j in jobs]
    with open(f'{OUT_DIR}/manifest.json', 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    sys.exit(0)

log(f"Starte Batch (3 parallel)...")
done_count = already_done
success = 0
failures = []
start_time = time.time()

with ThreadPoolExecutor(max_workers=3) as ex:
    fut = {ex.submit(generate, j): j['id'] for j in pending}
    for f in as_completed(fut):
        jid, path, err = f.result()
        done_count += 1
        elapsed = time.time() - start_time
        rate = done_count / (elapsed / 60) if elapsed > 0 else 0
        remaining = total - done_count
        eta_min = remaining / rate if rate > 0 else 0

        if err:
            failures.append((jid, err))
            log(f"  ❌ [{done_count}/{total}] {jid}: {err}")
        else:
            success += 1
            kb = os.path.getsize(path) // 1024
            log(f"  ✅ [{done_count}/{total}] {jid} ({kb}KB) | {rate:.1f}/min | ETA {eta_min:.0f}min")

elapsed = time.time() - start_time
log(f"\n=== Fertig in {elapsed/60:.1f} Minuten ===")
log(f"Erfolgreich: {success}/{len(pending)}")
log(f"Fehlgeschlagen: {len(failures)}")
log(f"Gesamt im Ordner: {len([f for f in os.listdir(OUT_DIR) if f.endswith('.png')])}")

if failures:
    log(f"\nFehlerdetails:")
    for jid, err in failures[:20]:
        log(f"  {jid}: {err}")

# Write manifest
manifest = []
for j in jobs:
    exists = os.path.exists(j['output']) and os.path.getsize(j['output']) > 100
    manifest.append({
        'bezirk': j['bezirk'], 'ort': j['ort'],
        'original': j['img_path'],
        'qwen': j['output'] if exists else None,
    })

with open(f'{OUT_DIR}/manifest.json', 'w', encoding='utf-8') as f:
    json.dump(manifest, f, indent=2, ensure_ascii=False)
log(f"Manifest gespeichert: {OUT_DIR}/manifest.json")

#!/usr/bin/env python3
"""FLUX.2-pro Modern batch generation for ALL 276 municipalities.
~10-15s per image, ~15-20 min total with 3 parallel workers.
"""
import requests, json, base64, os, sys, time, re, random
from concurrent.futures import ThreadPoolExecutor, as_completed

API_KEY = "sk-jflggfbmhvbarpjfgifnhusjvyggksbqbmtdebjxrvjtqwnl"
URL = "https://api.siliconflow.com/v1/images/generations"
OUT_DIR = "img/qwen_modern"
LOG = "batch_flux_modern.log"
os.makedirs(OUT_DIR, exist_ok=True)

headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

MODERN_PROMPT = (
    "A modern minimalist flat geometric redesign of this coat of arms. "
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
    s = s.replace('(', '').replace(')', '').replace('.', '').replace(',', '').replace('__', '_')
    s = re.sub(r'[^a-z0-9_-]', '', s)
    return s.strip('_')[:60]

def load_jobs():
    with open('wappen_page_data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    jobs = []
    for bezirk in data['bezirke']:
        bname = bezirk['name']
        for ort in bezirk['orte']:
            oname = ort['name']
            safe_b = sanitize_name(bname)
            safe_o = sanitize_name(oname)
            uid = f"{safe_b}_{safe_o}" if safe_b and safe_o else f"{safe_b or 'x'}_{safe_o or 'y'}"
            jobs.append({
                'id': uid, 'bezirk': bname, 'ort': oname,
                'img_path': ort['img'],
                'output': f"{OUT_DIR}/{uid}.png",
            })
    return jobs

def write_manifest(jobs, out_dir):
    manifest = []
    for j in jobs:
        exists = os.path.exists(j['output']) and os.path.getsize(j['output']) > 100
        manifest.append({
            'bezirk': j['bezirk'], 'ort': j['ort'],
            'original': j['img_path'],
            'qwen': j['output'] if exists else None,
        })
    with open(f'{out_dir}/manifest.json', 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    log(f"Manifest: {out_dir}/manifest.json")

def generate(job):
    for attempt in range(2):
        try:
            with open(job['img_path'], 'rb') as f:
                b64 = base64.b64encode(f.read()).decode('utf-8')
            data_uri = f"data:image/png;base64,{b64}"
            payload = {
                "model": "black-forest-labs/FLUX.2-pro",
                "prompt": MODERN_PROMPT,
                "image": data_uri,
                "image_strength": 0.55,
                "n": 1, "size": "1024x1024",
            }
            resp = requests.post(URL, json=payload, headers=headers, timeout=60)
            result = resp.json()
            if resp.status_code != 200:
                if attempt == 0: time.sleep(5); continue
                return job['id'], None, f"HTTP {resp.status_code}"
            img_url = result["images"][0]["url"]
            img_resp = requests.get(img_url, timeout=30)
            with open(job['output'], 'wb') as f:
                f.write(img_resp.content)
            return job['id'], job['output'], None
        except Exception as e:
            if attempt == 0: time.sleep(5); continue
            return job['id'], None, str(e)
    return job['id'], None, "Max retries"

# === MAIN ===
jobs = load_jobs()
total = len(jobs)
log(f"=== {total} Gemeinden ===")

already_done = sum(1 for j in jobs if os.path.exists(j['output']) and os.path.getsize(j['output']) > 1000)
log(f"Bereits: {already_done}/{total}")

pending = [j for j in jobs if not (os.path.exists(j['output']) and os.path.getsize(j['output']) > 1000)]
log(f"Noch: {len(pending)}")

if not pending:
    log("✅ Alle fertig!")
    write_manifest(jobs, OUT_DIR)
    sys.exit(0)

log(f"Starte FLUX.2-pro (3 parallel)...")
done_count = already_done
success = 0
fails = []
start = time.time()

with ThreadPoolExecutor(max_workers=3) as ex:
    fut = {ex.submit(generate, j): j['id'] for j in pending}
    for f in as_completed(fut):
        jid, path, err = f.result()
        done_count += 1
        elapsed = time.time() - start
        new_count = done_count - already_done
        rate = new_count / (elapsed / 60) if elapsed > 10 else 3
        eta = (len(pending) - new_count) / rate if rate > 0 else 0

        if err:
            fails.append((jid, err))
            log(f"  ❌ [{done_count}/{total}] {jid}: {err}")
        else:
            success += 1
            kb = os.path.getsize(path) // 1024
            log(f"  ✅ [{done_count}/{total}] {jid} ({kb}KB) | {rate:.1f}/min | noch ~{eta:.0f}min")

t = (time.time() - start) / 60
total_success = success + already_done
log(f"\n=== Fertig in {t:.1f}min: {total_success}/{total} OK, {len(fails)} Fehler ===")
if fails:
    log("Fehler (max 10):")
    for jid, err in fails[:10]:
        log(f"  {jid}: {err}")

write_manifest(jobs, OUT_DIR)

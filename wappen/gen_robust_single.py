#!/usr/bin/env python3
"""Robust single-image queue with auto-restart/retry for missing Tyrol wappen."""
from __future__ import annotations
import json, os, time, uuid, subprocess, sys
from pathlib import Path
import requests

ROOT = Path('F:/tiroltourismus/wappen')
COMFY = 'http://127.0.0.1:8188'
OUT = ROOT / 'img' / 'lokal'
COMFY_DIR = Path('/e/HermesPortable/ComfyUI')
DB_PATH = COMFY_DIR / 'user' / 'comfyui.db'
PY = COMFY_DIR / '.venv' / 'Scripts' / 'python'
MAIN = COMFY_DIR / 'main.py'
OUT.mkdir(parents=True, exist_ok=True)

CLIP_L = 'modern minimalist flat vector coat of arms, heraldic shield with clean geometric shapes, bold flat colors, simplified minimalist style, no text, premium quality'
T5_BASE = 'modern minimalist flat vector coat of arms redesign for {name} in {bezirk} Tyrol, heraldic shield with clean geometric simplified shapes, bold flat vector colors, minimalist logo-style heraldry, modern reinterpretation, premium quality vector illustration, no text, no watermark'


def safe(name: str) -> str:
    s = name.lower().replace(' ', '_').replace('(', '').replace(')', '').replace('.', '')
    for a, b in [('ä', 'ae'), ('ö', 'oe'), ('ü', 'ue'), ('ß', 'ss')]:
        s = s.replace(a, b)
    return ''.join(c for c in s if c.isalnum() or c == '_')


def comfy_up() -> bool:
    try:
        r = requests.get(f'{COMFY}/system_stats', timeout=5)
        return r.ok
    except Exception:
        return False


def kill_comfy():
    # kill python main.py processes only
    try:
        out = subprocess.check_output(['bash', '-lc', "ps aux | grep -i 'python.*main.py' | grep -v grep | awk '{print $2}'"], text=True)
        for pid in [p.strip() for p in out.splitlines() if p.strip()]:
            subprocess.run(['bash', '-lc', f'kill -9 {pid} >/dev/null 2>&1 || true'])
    except Exception:
        pass
    try:
        if DB_PATH.exists():
            DB_PATH.unlink()
    except Exception:
        pass


def start_comfy() -> None:
    # start fresh
    kill_comfy()
    subprocess.Popen(['bash', '-lc', f'cd {COMFY_DIR} && "{PY}" "{MAIN}" --port 8188'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(60):
        if comfy_up():
            return
        time.sleep(2)
    raise RuntimeError('ComfyUI did not come up')


def upload_image(path: Path, retries=3) -> str | None:
    for attempt in range(1, retries + 1):
        try:
            with path.open('rb') as f:
                r = requests.post(
                    f'{COMFY}/upload/image',
                    files={'image': (path.name, f, 'image/png')},
                    data={'type': 'input', 'overwrite': 'true'},
                    timeout=60,
                )
            if r.ok:
                return r.json()['name']
        except Exception:
            pass
        time.sleep(2 * attempt)
    return None


def make_workflow(upload_name: str, out_prefix: str, name: str, bezirk: str):
    return {
        '1': {'class_type': 'LoadImage', 'inputs': {'image': upload_name}},
        '2': {'class_type': 'ImageScale', 'inputs': {'image': ['1', 0], 'upscale_method': 'lanczos', 'width': 120, 'height': 144, 'crop': 'disabled'}},
        '3': {'class_type': 'VAELoader', 'inputs': {'vae_name': 'flux-vae-bf16.safetensors'}},
        '4': {'class_type': 'UNETLoader', 'inputs': {'unet_name': 'flux1-dev-fp8-e4m3fn.safetensors', 'weight_dtype': 'default'}},
        '5': {'class_type': 'DualCLIPLoader', 'inputs': {'clip_name1': 'clip_l.safetensors', 'clip_name2': 't5xxl_fp16.safetensors', 'type': 'flux'}},
        '6': {'class_type': 'VAEEncode', 'inputs': {'pixels': ['2', 0], 'vae': ['3', 0]}},
        '7': {'class_type': 'CLIPTextEncodeFlux', 'inputs': {'clip': ['5', 0], 'clip_l': CLIP_L, 't5xxl': T5_BASE.format(name=name, bezirk=bezirk), 'guidance': 2.0}},
        '8': {'class_type': 'KSampler', 'inputs': {'seed': hash(safe(name)) % 99999, 'steps': 4, 'cfg': 1.0, 'sampler_name': 'euler', 'scheduler': 'simple', 'denoise': 0.35, 'model': ['4', 0], 'positive': ['7', 0], 'negative': ['7', 0], 'latent_image': ['6', 0]}},
        '9': {'class_type': 'VAEDecode', 'inputs': {'samples': ['8', 0], 'vae': ['3', 0]}},
        '10': {'class_type': 'SaveImage', 'inputs': {'filename_prefix': out_prefix, 'images': ['9', 0]}},
    }


def prompt_and_wait(name: str, bezirk: str, source: Path, max_wait=180) -> bool:
    up = upload_image(source)
    if not up:
        return False
    wf = make_workflow(up, f'wappen_{safe(name)}_modern', name, bezirk)
    r = requests.post(f'{COMFY}/prompt', json={'prompt': wf, 'client_id': str(uuid.uuid4())}, timeout=30)
    if not r.ok:
        return False
    pid = r.json()['prompt_id']
    t0 = time.time()
    while time.time() - t0 < max_wait:
        try:
            hr = requests.get(f'{COMFY}/history/{pid}', timeout=15)
            if hr.ok:
                h = hr.json().get(pid)
                if h and h['status'].get('completed'):
                    for no in h.get('outputs', {}).values():
                        for img in no.get('images', []):
                            ir = requests.get(f"{COMFY}/view?filename={img['filename']}&type=output", timeout=60)
                            if ir.ok:
                                (OUT / img['filename']).write_bytes(ir.content)
                    return True
                if h and h['status'].get('status_str') == 'error':
                    return False
        except Exception:
            pass
        time.sleep(2)
    return False


# Load data and compute missing
with (ROOT / 'wappen_page_data.json').open(encoding='utf-8') as f:
    data = json.load(f)

existing = {
    fn.replace('wappen_', '').split('_modern_')[0]
    for fn in os.listdir(OUT)
    if fn.startswith('wappen_') and '_modern_' in fn and fn.endswith('.png')
}

missing = []
for b in data['bezirke']:
    for o in b['orte']:
        if safe(o['name']) not in existing:
            ip = o.get('img', '') or b.get('img', '')
            if ip and (ROOT / ip).exists():
                missing.append((o['name'], b['name'], ROOT / ip))

print(f'Missing: {len(missing)}')
print('Will process in strict single queue with auto-restart/retry')

if not comfy_up():
    print('Starting ComfyUI...')
    start_comfy()

ok = 0
fail = 0
restart_count = 0

for idx, (name, bezirk, src) in enumerate(missing, 1):
    print(f'[{idx}/{len(missing)}] {name} ({bezirk})')
    attempts = 0
    while attempts < 4:
        attempts += 1
        try:
            if not comfy_up():
                print('  -> ComfyUI down, restarting')
                restart_count += 1
                start_comfy()
            # ensure queue empty-ish before submitting
            q = requests.get(f'{COMFY}/queue', timeout=10).json()
            if q.get('queue_running') or q.get('queue_pending'):
                print('  -> queue busy, waiting 5s')
                time.sleep(5)
                continue
            if prompt_and_wait(name, bezirk, src, max_wait=240):
                ok += 1
                print('  -> OK')
                break
            else:
                print('  -> FAIL, retrying')
                time.sleep(5)
        except Exception as e:
            print(f'  -> error {e}, restart/retry')
            time.sleep(5)
            if attempts >= 2:
                restart_count += 1
                start_comfy()
    else:
        fail += 1
        print('  -> gave up')

print(f'Finished: {ok} OK, {fail} failed, {restart_count} restarts')

#!/usr/bin/env python3
from __future__ import annotations
import json, os, time, uuid, subprocess
from pathlib import Path
import requests

ROOT = Path('F:/tiroltourismus/wappen')
OUT = ROOT / 'img' / 'lokal'
COMFY_DIR = Path('/e/HermesPortable/ComfyUI')
PY = COMFY_DIR / '.venv' / 'Scripts' / 'python'
MAIN = COMFY_DIR / 'main.py'
DB = COMFY_DIR / 'user' / 'comfyui.db'
COMFY = 'http://127.0.0.1:8188'
OUT.mkdir(parents=True, exist_ok=True)

CLIP_L = 'modern minimalist flat vector coat of arms, heraldic shield with clean geometric shapes, bold flat colors, simplified minimalist style, no text, premium quality'
T5 = 'modern minimalist flat vector coat of arms redesign for {name} in {bezirk} Tyrol, heraldic shield with clean geometric simplified shapes, bold flat vector colors, minimalist logo-style heraldry, modern reinterpretation, premium quality vector illustration, no text, no watermark'


def safe(name: str) -> str:
    s = name.lower().replace(' ', '_').replace('(', '').replace(')', '').replace('.', '')
    for a, b in [('ä','ae'), ('ö','oe'), ('ü','ue'), ('ß','ss')]:
        s = s.replace(a, b)
    return ''.join(c for c in s if c.isalnum() or c == '_')


def kill_comfy():
    try:
        out = subprocess.check_output(['bash', '-lc', "ps aux | grep -i 'python.*main.py' | grep -v grep | awk '{print $2}'"], text=True)
        for pid in [p for p in out.splitlines() if p.strip()]:
            subprocess.run(['bash', '-lc', f'kill -9 {pid} >/dev/null 2>&1 || true'])
    except Exception:
        pass
    try:
        if DB.exists(): DB.unlink()
    except Exception:
        pass


def start_comfy():
    kill_comfy()
    subprocess.Popen(['bash', '-lc', f'cd {COMFY_DIR} && "{PY}" "{MAIN}" --port 8188'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(60):
        try:
            if requests.get(f'{COMFY}/system_stats', timeout=2).ok:
                return True
        except Exception:
            pass
        time.sleep(1)
    return False


def wait_idle(max_wait=20):
    t0 = time.time()
    while time.time()-t0 < max_wait:
        try:
            q = requests.get(f'{COMFY}/queue', timeout=3).json()
            if not q.get('queue_running') and not q.get('queue_pending'):
                return True
        except Exception:
            pass
        time.sleep(1)
    return False


def upload(path: Path):
    for _ in range(2):
        try:
            with path.open('rb') as f:
                r = requests.post(f'{COMFY}/upload/image', files={'image': (path.name, f, 'image/png')}, data={'type':'input','overwrite':'true'}, timeout=20)
            if r.ok:
                return r.json()['name']
        except Exception:
            pass
        time.sleep(1)
    return None


def prompt_one(name, bezirk, src: Path):
    up = upload(src)
    if not up:
        return False
    wf = {
        '1': {'class_type': 'LoadImage', 'inputs': {'image': up}},
        '2': {'class_type': 'ImageScale', 'inputs': {'image': ['1', 0], 'upscale_method': 'lanczos', 'width': 120, 'height': 144, 'crop': 'disabled'}},
        '3': {'class_type': 'VAELoader', 'inputs': {'vae_name': 'flux-vae-bf16.safetensors'}},
        '4': {'class_type': 'UNETLoader', 'inputs': {'unet_name': 'flux1-dev-fp8-e4m3fn.safetensors', 'weight_dtype': 'default'}},
        '5': {'class_type': 'DualCLIPLoader', 'inputs': {'clip_name1': 'clip_l.safetensors', 'clip_name2': 't5xxl_fp16.safetensors', 'type': 'flux'}},
        '6': {'class_type': 'VAEEncode', 'inputs': {'pixels': ['2', 0], 'vae': ['3', 0]}},
        '7': {'class_type': 'CLIPTextEncodeFlux', 'inputs': {'clip': ['5', 0], 'clip_l': CLIP_L, 't5xxl': T5.format(name=name, bezirk=bezirk), 'guidance': 2.0}},
        '8': {'class_type': 'KSampler', 'inputs': {'seed': hash(safe(name)) % 99999, 'steps': 4, 'cfg': 1.0, 'sampler_name': 'euler', 'scheduler': 'simple', 'denoise': 0.35, 'model': ['4', 0], 'positive': ['7', 0], 'negative': ['7', 0], 'latent_image': ['6', 0]}},
        '9': {'class_type': 'VAEDecode', 'inputs': {'samples': ['8', 0], 'vae': ['3', 0]}},
        '10': {'class_type': 'SaveImage', 'inputs': {'filename_prefix': f'wappen_{safe(name)}_modern', 'images': ['9', 0]}},
    }
    r = requests.post(f'{COMFY}/prompt', json={'prompt': wf, 'client_id': str(uuid.uuid4())}, timeout=10)
    if not r.ok:
        return False
    pid = r.json()['prompt_id']
    t0 = time.time()
    while time.time()-t0 < 45:
        try:
            h = requests.get(f'{COMFY}/history/{pid}', timeout=5).json().get(pid)
            if h and h['status'].get('completed'):
                for no in h.get('outputs', {}).values():
                    for img in no.get('images', []):
                        ir = requests.get(f"{COMFY}/view?filename={img['filename']}&type=output", timeout=20)
                        if ir.ok:
                            (OUT / img['filename']).write_bytes(ir.content)
                return True
            if h and h['status'].get('status_str') == 'error':
                return False
        except Exception:
            pass
        time.sleep(1)
    return False


# Load missing list
with (ROOT / 'wappen_page_data.json').open(encoding='utf-8') as f:
    data = json.load(f)
existing = {fn.replace('wappen_', '').split('_modern_')[0] for fn in os.listdir(OUT) if fn.startswith('wappen_') and '_modern_' in fn and fn.endswith('.png')}
missing = []
for b in data['bezirke']:
    for o in b['orte']:
        if safe(o['name']) not in existing:
            ip = o.get('img', '') or b.get('img', '')
            if ip and (ROOT / ip).exists():
                missing.append((o['name'], b['name'], ROOT / ip))
print(f'Missing: {len(missing)}')

if not start_comfy():
    raise SystemExit('ComfyUI failed to start')

ok = 0
restart = 0
for i, (name, bezirk, src) in enumerate(missing, 1):
    print(f'[{i}/{len(missing)}] {name} ({bezirk})')
    attempt = 0
    while attempt < 5:
        attempt += 1
        try:
            if not requests.get(f'{COMFY}/system_stats', timeout=2).ok:
                restart += 1
                print('  restart')
                if not start_comfy():
                    continue
            wait_idle(5)
            if prompt_one(name, bezirk, src):
                ok += 1
                print('  OK')
                break
            print('  retry')
        except Exception:
            restart += 1
            print('  hard restart')
            start_comfy()
    else:
        print('  FAIL')
    time.sleep(1)
print(f'done {ok}/{len(missing)} restarts={restart}')

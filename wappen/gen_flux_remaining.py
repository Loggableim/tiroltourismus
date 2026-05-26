#!/usr/bin/env python3
"""Aggressive FLUX headless batch for the remaining Tyrol wappen.

Goals:
- use the already-installed local FLUX models inside ComfyUI's model folders
- strict one-at-a-time execution
- short timeouts
- hard restart after repeated failures
- minimal hanging
"""
from __future__ import annotations

import json
import os
import subprocess
import time
import uuid
from pathlib import Path

import requests

ROOT = Path(r'F:/tiroltourismus/wappen')
OUT = ROOT / 'img' / 'lokal'
LOG = ROOT / 'gen_flux_remaining.log'
COMFY_DIR = Path(r'E:/HermesPortable/ComfyUI')
MAIN = COMFY_DIR / 'main.py'
PY = COMFY_DIR / '.venv' / 'Scripts' / 'python'
DB = COMFY_DIR / 'user' / 'comfyui.db'
COMFY = 'http://127.0.0.1:8188'
PORT = '8188'

UNET = 'flux1-dev-fp8-e4m3fn.safetensors'
VAE = 'flux-vae-bf16.safetensors'
CLIP_L = 'clip_l.safetensors'
T5 = 't5xxl_fp16.safetensors'

CLIP_L_PROMPT = (
    'modern minimalist flat vector coat of arms, heraldic shield with clean geometric shapes, '
    'bold flat colors, simplified minimalist style, no text, premium quality'
)
T5_PROMPT = (
    'modern minimalist flat vector coat of arms redesign for {name} in {bezirk} Tyrol, '
    'heraldic shield with clean geometric simplified shapes, bold flat vector colors, '
    'minimalist logo-style heraldry, modern reinterpretation, premium quality vector illustration, '
    'no text, no watermark'
)

WORK_W = 768
WORK_H = 896
TARGET_W = 120
TARGET_H = 144
STEPS = 16
GUIDANCE = 3.5
DENOISE = 0.5


def log(msg: str) -> None:
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open('a', encoding='utf-8') as f:
        f.write(line + '\n')


def safe(name: str) -> str:
    s = name.lower().replace(' ', '_').replace('(', '').replace(')', '').replace('.', '')
    for a, b in [('ä', 'ae'), ('ö', 'oe'), ('ü', 'ue'), ('ß', 'ss')]:
        s = s.replace(a, b)
    return ''.join(c for c in s if c.isalnum() or c == '_')


def port_pids() -> list[str]:
    try:
        out = subprocess.check_output(
            ['bash', '-lc', f'netstat -ano 2>/dev/null | grep ":{PORT}" | grep LISTEN | awk "{{print $5}}" | sort -u'],
            text=True,
        )
        return [p.strip() for p in out.splitlines() if p.strip() and p.strip().isdigit()]
    except Exception:
        return []


def kill_pid(pid: str) -> None:
    subprocess.run(['bash', '-lc', f'taskkill //F //PID {pid} >/dev/null 2>&1 || kill -9 {pid} >/dev/null 2>&1 || true'])


def comfy_up() -> bool:
    try:
        return requests.get(f'{COMFY}/system_stats', timeout=2).ok
    except Exception:
        return False


def queue_idle() -> bool:
    try:
        q = requests.get(f'{COMFY}/queue', timeout=3).json()
        return len(q.get('queue_running', [])) == 0 and len(q.get('queue_pending', [])) == 0
    except Exception:
        return False


def wait_queue_clear(timeout: int = 20) -> bool:
    t0 = time.time()
    while time.time() - t0 < timeout:
        if comfy_up() and queue_idle():
            return True
        time.sleep(1)
    return False


def hard_restart() -> bool:
    log('hard restart comfyui')
    for pid in port_pids():
        log(f'kill port pid={pid}')
        kill_pid(pid)
    try:
        out = subprocess.check_output(
            ['bash', '-lc', "ps aux | grep -i 'python.*main.py' | grep -v grep | awk '{print $2}'"],
            text=True,
        )
        for pid in [p.strip() for p in out.splitlines() if p.strip()]:
            log(f'kill main pid={pid}')
            kill_pid(pid)
    except Exception:
        pass
    try:
        if DB.exists():
            DB.unlink()
    except Exception:
        pass
    for _ in range(10):
        if not port_pids():
            break
        time.sleep(1)
    subprocess.Popen(
        ['bash', '-lc', f'cd {COMFY_DIR} && "{PY}" "{MAIN}" --port {PORT}'],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    for _ in range(30):
        if comfy_up():
            log('comfyui ready')
            return True
        time.sleep(2)
    log('comfyui did not come up in time')
    return False


def upload_image(path: Path) -> str | None:
    for attempt in range(1, 3):
        try:
            with path.open('rb') as f:
                r = requests.post(
                    f'{COMFY}/upload/image',
                    files={'image': (path.name, f, 'image/png')},
                    data={'type': 'input', 'overwrite': 'true'},
                    timeout=15,
                )
            if r.ok:
                return r.json()['name']
            log(f'upload failed {path.name}: {r.status_code}')
        except Exception as e:
            log(f'upload exception {path.name} try {attempt}: {e}')
        time.sleep(2 * attempt)
    return None


def build_workflow(upload_name: str, name: str, bezirk: str):
    return {
        '1': {'class_type': 'LoadImage', 'inputs': {'image': upload_name}},
        '2': {'class_type': 'VAELoader', 'inputs': {'vae_name': VAE}},
        '3': {'class_type': 'UNETLoader', 'inputs': {'unet_name': UNET, 'weight_dtype': 'default'}},
        '4': {'class_type': 'DualCLIPLoader', 'inputs': {'clip_name1': CLIP_L, 'clip_name2': T5, 'type': 'flux'}},
        '5': {'class_type': 'VAEEncode', 'inputs': {'pixels': ['1', 0], 'vae': ['2', 0]}},
        '6': {'class_type': 'CLIPTextEncodeFlux', 'inputs': {'clip': ['4', 0], 'clip_l': CLIP_L_PROMPT, 't5xxl': T5_PROMPT.format(name=name, bezirk=bezirk), 'guidance': GUIDANCE}},
        '7': {'class_type': 'KSampler', 'inputs': {'seed': hash(safe(name)) % 99999, 'steps': STEPS, 'cfg': 1.0, 'sampler_name': 'euler', 'scheduler': 'simple', 'denoise': DENOISE, 'model': ['3', 0], 'positive': ['6', 0], 'negative': ['6', 0], 'latent_image': ['5', 0]}},
        '8': {'class_type': 'VAEDecode', 'inputs': {'samples': ['7', 0], 'vae': ['2', 0]}},
        '9': {'class_type': 'SaveImage', 'inputs': {'filename_prefix': f'wappen_{safe(name)}_flux_modern', 'images': ['8', 0]}},
    }


def prompt_one(name: str, bezirk: str, src: Path) -> bool:
    up = upload_image(src)
    if not up:
        return False
    wf = build_workflow(up, name, bezirk)
    try:
        r = requests.post(
            f'{COMFY}/prompt',
            json={'prompt': wf, 'client_id': str(uuid.uuid4())},
            timeout=10,
        )
    except Exception as e:
        log(f'prompt post exception {name}: {e}')
        return False
    if not r.ok:
        log(f'prompt post failed {name}: {r.status_code} {r.text[:120]}')
        return False

    pid = r.json()['prompt_id']
    log(f'prompt {name}: {pid}')
    t0 = time.time()
    while time.time() - t0 < 180:
        try:
            hr = requests.get(f'{COMFY}/history/{pid}', timeout=6)
            if hr.ok:
                h = hr.json().get(pid)
                if h and h['status'].get('completed'):
                    saved = 0
                    for no in h.get('outputs', {}).values():
                        for img in no.get('images', []):
                            ir = requests.get(f"{COMFY}/view?filename={img['filename']}&type=output", timeout=20)
                            if ir.ok:
                                (OUT / img['filename']).write_bytes(ir.content)
                                saved += 1
                    log(f'completed {name}: saved={saved}')
                    return saved > 0
                if h and h['status'].get('status_str') == 'error':
                    log(f'error state {name}')
                    return False
        except Exception:
            pass
        time.sleep(1.5)
    log(f'timeout {name}')
    return False


def load_missing():
    data = json.loads((ROOT / 'wappen_page_data.json').read_text(encoding='utf-8'))
    existing = {
        fn.replace('wappen_', '').split('_flux_modern')[0]
        for fn in os.listdir(OUT)
        if fn.startswith('wappen_') and '_flux_modern' in fn and fn.endswith('.png')
    }
    missing = []
    for b in data['bezirke']:
        for o in b['orte']:
            k = safe(o['name'])
            if k not in existing:
                ip = o.get('img', '') or b.get('img', '')
                if ip and (ROOT / ip).exists():
                    missing.append((o['name'], b['name'], ROOT / ip))
    return missing


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    missing = load_missing()
    log(f'missing={len(missing)}')
    if not comfy_up() and not hard_restart():
        raise SystemExit('comfyui failed to start')

    ok = 0
    failures = 0
    for i, (name, bezirk, src) in enumerate(missing, 1):
        log(f'[{i}/{len(missing)}] {bezirk} / {name}')
        success = False
        for attempt in range(1, 4):
            if not wait_queue_clear(timeout=20):
                hard_restart()
                wait_queue_clear(timeout=20)
            if not comfy_up():
                if not hard_restart():
                    continue
            try:
                success = prompt_one(name, bezirk, src)
            except Exception as e:
                log(f'prompt exception {name}: {e}')
                success = False
            wait_queue_clear(timeout=10)
            if success:
                ok += 1
                failures = 0
                break
            failures += 1
            log(f'fail {name} attempt={attempt}')
            if failures >= 2:
                hard_restart()
                failures = 0
            time.sleep(2)
        if not success:
            log(f'gave up {name}')
        time.sleep(0.5)
    log(f'done ok={ok} total={len(missing)}')


if __name__ == '__main__':
    main()

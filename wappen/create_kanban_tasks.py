#!/usr/bin/env python3
"""Create 9 kanban tasks (1 per Bezirk) for coat of arms batch generation."""
import subprocess, json, sys

BASE = "/f/tiroltourismus"
ENV = {**__import__('os').environ, "HERMES_KANBAN_BOARD": "wappen-batch", "PYTHONPATH": "/e/HermesPortable/cids-hermes-agent"}
PY = ["python", "-m", "hermes_cli.main", "kanban"]

def kanban(*args):
    r = subprocess.run([sys.executable, "-m", "hermes_cli.main", "kanban", *args, "--json"],
        capture_output=True, text=True, timeout=30, cwd=BASE, env=ENV)
    if r.returncode != 0:
        print(f"ERR: {r.stderr[:200]}")
        return None
    try: return json.loads(r.stdout)
    except: print(f"PARSE: {r.stdout[:200]}"); return None

# Load data
with open("wappen_page_data.json", encoding='utf-8') as f:
    data = json.load(f)

# Stats über alle Gemeinden
total = sum(len(b['orte']) for b in data['bezirke'])
print(f"Total: {total} Gemeinden in {len(data['bezirke'])} Bezirken")
print(f"Output: 124x148px, Style: Modern, Modell: FLUX Dev (4 steps)\n")

tasks = []
for b in data['bezirke']:
    bname = b['name']
    orte = b['orte']
    n = len(orte)
    
    # List municipalities for the task body
    orte_list = "\n".join(f"  {i+1}. {o['name']} ({o.get('img','?')})" for i, o in enumerate(orte))
    
    body = f"""PROJEKT-PFAD: /f/tiroltourismus/wappen
BEZIRK: {bname}
ANZAHL: {n} Gemeinden

Generiere alle {n} Wappen des Bezirks {bname} im modern-minimalistischen Stil.
Output: 124x148px, FLUX Dev FP8, 4 steps, euler, denoise 0.35, guidance 2.0
Dateiname: wappen_{{ort}}_{{style}}_00001_.png

Gemeinden:
{orte_list}

Hinweis: Batch-Verarbeitung via ComfyUI API (localhost:8188).
3-4 Gemeinden pro ComfyUI-Workflow (parallel chains, shared model).
"""
    
    result = kanban("create", f"Wappen: {bname} ({n})",
        "--body", body[:1800],
        "--assignee", "feat-builder")
    
    if result:
        tid = result.get('id', '?')
        tasks.append((tid, bname, n))
        print(f"  [{tid:15}] {bname:30} ({n} Gemeinden)")
    else:
        print(f"  ❌ {bname}")

print(f"\n✅ {len(tasks)}/{len(data['bezirke'])} Tasks erstellt")

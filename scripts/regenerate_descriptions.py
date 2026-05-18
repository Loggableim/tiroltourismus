#!/usr/bin/env python3
"""Regenerate descriptions for entries with <5 sentences - reads key from .env_key"""
import json, glob, os, urllib.request, time, sys, re

# Read key from temp file (written by parent process with actual env access)
key_path = "E:/HermesPortable/home/.env_key"
api_key = ""
if os.path.exists(key_path):
    with open(key_path) as f:
        api_key = f.read().strip()

if not api_key:
    print("NO API KEY")
    sys.exit(1)

def count_s(text):
    return len([s for s in re.split(r'(?<=[.!?:;])\s+', text.replace("</p>", ".")) if s.strip()])

ROOT = "F:/tiroltourismus/src/data"
tl_map = {"hotel":"Hotel","gasthof":"Gasthof","ferienwohnung":"Ferienwohnung","ferienhaus":"Ferienhaus",
          "jugendherberge":"Jugendherberge","camping":"Campingplatz","bauernhof":"Bauernhof",
          "natur":"Natur","kultur":"Kultur","aussicht":"Aussicht","museum":"Museum","sport":"Sport"}

under = []
for coll in ["unterkuenfte", "sehenswuerdigkeiten", "camping"]:
    for f in glob.glob(f"{ROOT}/{coll}/*/index.json"):
        d = json.load(open(f))
        desc = d.get("beschreibung", "")
        if desc and len(desc.strip()) >= 10 and count_s(desc) < 5:
            under.append((f, d))

print(f"START: {len(under)} Eintraege unter 5 Saetzen")
sys.stdout.flush()

fixed = 0
for idx, (fp, d) in enumerate(under):
    name = d.get("name", "?")
    ort = d.get("ort", "Tirol")
    typ = tl_map.get(d.get("typ",""), d.get("typ",""))
    
    prompt = f'Beschreibe "{name}" in {ort}, Tirol. Art: {typ}. MINDESTENS 5 Saetze, maximal 8 Saetze. Sachlich, informativ. HTML: <p>...</p>'
    body = json.dumps({"model": "deepseek-v4-flash", "messages": [
        {"role": "system", "content": "MINDESTENS 5 Saetze, maximal 8. Deutsch, HTML, sachlich."},
        {"role": "user", "content": prompt}
    ], "max_tokens": 400, "temperature": 0.4}).encode()
    
    try:
        req = urllib.request.Request("https://opencode.ai/zen/go/v1/chat/completions", data=body, headers={
            "Content-Type": "application/json", "Authorization": f"Bearer {api_key}"
        }, method="POST")
        resp = urllib.request.urlopen(req, timeout=30)
        text = json.loads(resp.read())["choices"][0]["message"]["content"].strip()
        desc = ("<p>" + text + "</p>") if not text.startswith("<") else text
        d["beschreibung"] = desc
        json.dump(d, open(fp, "w"), indent=2, ensure_ascii=False)
        fixed += 1
    except Exception as e:
        pass  # silent retry on error
    
    if (idx+1) % 25 == 0:
        print(f"[{idx+1}/{len(under)}] {fixed} OK, {idx+1-fixed} ERR")
        sys.stdout.flush()
    
    time.sleep(0.8)

print(f"DONE: {fixed}/{len(under)} regeneriert")
sys.stdout.flush()

#!/usr/bin/env python3
"""Retry entries that got empty or too-short descriptions."""
import json, os, sys, time, ssl, urllib.request

# Load API key
API_KEY = os.environ.get("OPENCODE_GO_API_KEY", "")
if not API_KEY:
    env_file = os.path.expanduser("~/.hermes/.env")
    alt_file = r"C:\Users\logga\.hermes\.env"
    for ep in [env_file, alt_file]:
        if os.path.exists(ep):
            with open(ep) as f:
                for line in f:
                    if line.startswith("OPENCODE_GO_API_KEY="):
                        API_KEY = line.split("=", 1)[1].strip()
                        break
        if API_KEY:
            break

if not API_KEY:
    API_KEY = os.environ.get("HERMES_OPENCODE_GO_API_KEY", "")

API_URL = "https://opencode.ai/zen/go/v1/chat/completions"
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "data", "unterkuenfte")

print(f"API Key loaded: {len(API_KEY)} chars")

# Check what entries we loaded from the batch files
batches = list(range(21, 31))
all_items = []
for b in batches:
    bf = os.path.join(os.path.dirname(os.path.abspath(__file__)), "batches", f"batch_{b:03d}.json")
    batch = json.load(open(bf, encoding="utf-8"))
    all_items.extend(batch)

print(f"Total items from batches 21-30: {len(all_items)}")

# Find those needing retry
to_retry = []
for item in all_items:
    fp = item["filepath"]
    if not os.path.exists(fp):
        print(f"  MISSING: {item['slug']} - file not found")
        continue
    entry = json.load(open(fp, encoding="utf-8"))
    desc = entry.get("beschreibung", "")
    if len(desc.strip("<>p/ ")) < 10:
        to_retry.append(item)
        print(f"  NEEDS RETRY: {item['name']} in {item['ort']} (desc len={len(desc)})")

print(f"\n=== {len(to_retry)} entries need retry ===")

if not to_retry:
    print("All good!")
    sys.exit(0)

# Process each one
enriched = 0
for item in to_retry:
    fp = item["filepath"]
    entry = json.load(open(fp, encoding="utf-8"))
    
    name = item["name"]
    ort = item["ort"]
    typ = item["typ"]
    region = item["region"]
    
    typ_label = {"hotel": "Hotel", "gasthof": "Gasthof", "ferienwohnung": "Ferienwohnung",
                 "ferienhaus": "Ferienhaus", "jugendherberge": "Jugendherberge",
                 "camping": "Campingplatz", "bauernhof": "Bauernhof"}.get(typ, typ)
    
    prompt = (
        f"Schreibe 2-3 Sätze HTML über '{name}' in {ort}, Tirol, Österreich. "
        f"Art: {typ_label}. "
        f"Beschreibe die Lage, Atmosphäre und was Gäste erwartet. "
        f"Sachlich, kein Marketington, kein Superlativ. "
        f"Maximal 120 Wörter. "
        f"Format: <p>Text mit <strong>Hervorhebungen</strong>.</p>"
        f"Wichtig: Mindestens 80 Zeichen, echte Information über die Unterkunft."
    )
    
    body = {
        "model": "deepseek-v4-flash",
        "messages": [
            {"role": "system", "content": "Du schreibst kurze, sachliche Beschreibungen für ein Tirol-Tourismusportal. Deutsch, maximal 120 Wörter, als HTML-Paragraph. Antworte direkt mit dem HTML, ohne nachzudenken."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 2000,
        "temperature": 0.5,
    }
    
    print(f"  {name} in {ort}...", end=" ", flush=True)
    
    req = urllib.request.Request(
        API_URL,
        data=json.dumps(body).encode(),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}",
            "User-Agent": "Mozilla/5.0",
        },
        method="POST"
    )
    
    ctx = ssl.create_default_context()
    try:
        resp = urllib.request.urlopen(req, timeout=60, context=ctx)
        result = json.loads(resp.read())
        text = result["choices"][0]["message"]["content"].strip()
        if not text.startswith("<"):
            text = f"<p>{text}</p>"
        
        if len(text.strip("<>p/ ")) >= 10:
            entry["beschreibung"] = text
            json.dump(entry, open(fp, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
            enriched += 1
            print(f"✅ ({len(text)} chars)")
        else:
            print(f"❌ too short ({len(text)} chars): {text[:50]}")
    except Exception as e:
        print(f"❌ API error: {e}")
    
    time.sleep(1.1)

print(f"\n✅ {enriched}/{len(to_retry)} entries enriched on retry")

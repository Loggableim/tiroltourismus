#!/usr/bin/env python3
"""Process a single batch file by index (81-88)."""
import json, os, sys, time, re, urllib.request, ssl

batch_idx = int(sys.argv[1]) if len(sys.argv) > 1 else 0

batch_file = f"F:/tiroltourismus/scripts/batches/b16/batch_{batch_idx:03d}.json"
if not os.path.exists(batch_file):
    print(f"Batch file not found: {batch_file}")
    sys.exit(1)

API_KEY = os.environ.get("OPENCODE_GO_API_KEY", "")
if not API_KEY:
    for _ep in ["E:/HermesPortable/home/.env", os.path.expanduser(r"~\.hermes\.env")]:
        if os.path.exists(_ep):
            with open(_ep, "r", encoding="utf-8") as _f:
                for _line in _f:
                    _line = _line.strip()
                    if _line.startswith("OPENCODE_GO_API_KEY="):
                        API_KEY = _line.split("=", 1)[1].strip()
                        break
            if API_KEY:
                break

TYP_LABELS = {"hotel":"Hotel","gasthof":"Gasthof","ferienwohnung":"Ferienwohnung","ferienhaus":"Ferienhaus","jugendherberge":"Jugendherberge","camping":"Campingplatz","bauernhof":"Bauernhof"}

def count_sentences(html_text):
    text = re.sub(r'<[^>]+>', '', html_text).strip()
    if not text: return 0
    return len([p for p in re.split(r'(?<=[.!?])\s+', text) if p.strip()])

def generate(name, ort, typ):
    typ_label = TYP_LABELS.get(typ, typ)
    ort_str = ort if ort else "Tirol"
    prompt = (
        f"Beschreibe '{name}' in {ort_str}, Tirol, Österreich. "
        f"Art: {typ_label}.\n\n"
        f"MINDESTENS 5 und maximal 8 Sätze. "
        f"Themen: Lage und Umgebung, Ausstattung, Atmosphäre und Stil, Zielgruppe. "
        f"Sachlich, informativ. Verwende <strong> für Hervorhebungen.\n\n"
        f"Format: <p>Text mit Sätzen.</p>"
    )
    body = {
        "model": "deepseek-v4-flash",
        "messages": [
            {"role": "system", "content": "Du schreibst sachliche Beschreibungen für Tirol-Tourismus. Deutsch, MINDESTENS 5 Sätze, max 8. Antworte direkt mit <p>...</p>."},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": 4096,
        "temperature": 0.3,
    }
    req = urllib.request.Request(
        "https://opencode.ai/zen/go/v1/chat/completions",
        data=json.dumps(body).encode(),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        },
        method="POST"
    )
    resp = urllib.request.urlopen(req, timeout=120, context=ssl._create_unverified_context())
    result = json.loads(resp.read())
    text = result["choices"][0]["message"]["content"].strip()
    if not text:
        raise ValueError("Empty response")
    if "<p>" in text and "</p>" in text:
        start = text.index("<p>")
        end = text.rindex("</p>") + len("</p>")
        text = text[start:end]
    elif not text.startswith("<"):
        text = f"<p>{text}</p>"
    return text

batch = json.load(open(batch_file, encoding="utf-8"))
print(f"Batch {batch_idx}: {len(batch)} entries")

for i, item in enumerate(batch):
    fp = item["filepath"]
    name = item["name"]
    ort = item["ort"]
    typ = item["typ"]
    slug = item["slug"]
    
    entry = json.load(open(fp, encoding="utf-8"))
    old_s = count_sentences(entry.get("beschreibung",""))
    
    if old_s >= 5:
        print(f"  [{i+1}] {slug}: {old_s} Sätze — SKIP (already OK)")
        continue
    
    print(f"  [{i+1}] {slug}: {old_s}→", end="", flush=True)
    
    # Try up to 3 times
    text = None
    for attempt in range(3):
        try:
            text = generate(name, ort, typ)
            sc = count_sentences(text)
            if sc >= 5:
                entry["beschreibung"] = text
                if not entry.get("tier"):
                    entry["tier"] = "basic"
                json.dump(entry, open(fp, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
                print(f"{sc} ✅", flush=True)
                break
            else:
                print(f"({sc} Sätze, retry {attempt+1})", end="", flush=True)
        except Exception as e:
            print(f"(error: {e})", end="", flush=True)
        time.sleep(2)
    else:
        # Write whatever we got
        if text:
            entry["beschreibung"] = text
            json.dump(entry, open(fp, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
            sc = count_sentences(text)
            print(f"{sc} ⚠️", flush=True)
        else:
            print("FAIL ❌", flush=True)
    
    time.sleep(0.5)

print(f"Batch {batch_idx} done!")

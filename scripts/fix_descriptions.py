#!/usr/bin/env python3
"""Fix descriptions that exceed 5 sentences or are corrupt."""
import json, glob, os, urllib.request, time, sys

API_URL = "https://opencode.ai/zen/go/v1/chat/completions"
API_KEY = os.environ.get("OPENCODE_GO_API_KEY", "")

def count_sentences(text):
    return len([s for s in text.replace("</p>", ".").replace("</li>", ".").split(".") if s.strip()])

def is_corrupt(text):
    if not text or len(text) < 20:
        return True
    # Check for markdown artifacts, code blocks, non-German content
    bad_patterns = ["```", "{#", "日本語", "calisch", "block).", "SuSto", "pgn-archiv"]
    return any(p in text.lower() for p in bad_patterns)

def fix_description(name, ort, typ):
    """Generate a SHORT description (max 5 sentences)."""
    tl = {"hotel":"Hotel","gasthof":"Gasthof","ferienwohnung":"Ferienwohnung","ferienhaus":"Ferienhaus",
          "jugendherberge":"Jugendherberge","camping":"Campingplatz","bauernhof":"Bauernhof",
          "natur":"Natur","kultur":"Kultur","aussicht":"Aussicht","museum":"Museum","sport":"Sport"}.get(typ, typ)
    
    prompt = f'Beschreibe "{name}" in {ort}, Tirol. Art: {tl}. MAXIMAL 3-5 Saetze. Kurz, sachlich, kein Marketing. Als HTML-Paragraph: <p>...</p>'
    
    body = json.dumps({
        "model": "deepseek-v4-flash",
        "messages": [
            {"role": "system", "content": "Du schreibst kurze Beschreibungen fuer ein Tirol-Portal. MAXIMAL 5 Saetze. Deutsch, HTML-Format, sachlich."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 250,
        "temperature": 0.3,
    }).encode()
    
    try:
        req = urllib.request.Request(API_URL, data=body, headers={
            "Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"
        }, method="POST")
        resp = urllib.request.urlopen(req, timeout=30)
        text = json.loads(resp.read())["choices"][0]["message"]["content"].strip()
        return ("<p>" + text + "</p>") if not text.startswith("<") else text
    except:
        return ""

# Find all entries that need fixing
data_dirs = ["src/data/unterkuenfte", "src/data/sehenswuerdigkeiten", "src/data/camping", "src/data/gastro"]
fix_needed = []

for dd in data_dirs:
    for f in glob.glob(f"{dd}/*/index.json"):
        d = json.load(open(f))
        desc = d.get("beschreibung", "")
        if not desc or len(desc.strip()) < 10:
            continue
        sentences = count_sentences(desc)
        if sentences > 5 or is_corrupt(desc):
            fix_needed.append((f, d, sentences))

print(f"${len(fix_needed)} Eintraege muessen gefixt werden (ueber 5 Saetze oder korrupt)")
fixed = 0

for idx, (fp, d, sentences) in enumerate(fix_needed):
    name = d.get("name", "?")
    ort = d.get("ort", "")
    typ = d.get("typ", "")
    print(f"  [{idx+1}/{len(fix_needed)}] {name} ({sentences} S) => ", end="", flush=True)
    
    new_desc = fix_description(name, ort, typ)
    if new_desc:
        d["beschreibung"] = new_desc
        json.dump(d, open(fp, "w"), indent=2, ensure_ascii=False)
        fixed += 1
        print("✅")
    else:
        print("❌")
    
    time.sleep(1.1)

print(f"\n✅ {fixed}/{len(fix_needed)} Beschreibungen gefixt")

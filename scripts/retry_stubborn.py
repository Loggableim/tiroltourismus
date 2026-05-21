#!/usr/bin/env python3
"""Retry the stubborn entries with a modified prompt."""
import json, os, sys, time, ssl, urllib.request

API_KEY = os.environ.get("OPENCODE_GO_API_KEY", "")
if not API_KEY:
    for ep in [os.path.expanduser("~/.hermes/.env"), r"C:\Users\logga\.hermes\.env"]:
        if os.path.exists(ep):
            with open(ep) as f:
                for line in f:
                    if line.startswith("OPENCODE_GO_API_KEY="):
                        API_KEY = line.split("=", 1)[1].strip()
                        break
        if API_KEY:
            break

API_URL = "https://opencode.ai/zen/go/v1/chat/completions"

entries = [
    # slug, name, ort, typ, region - entries returning empty HTML
    ("bauernhof-ferienwohnung-hecherhof", "Bauernhof-Ferienwohnung Hecherhof", "Thiersee", "ferienwohnung", "kufstein"),
    ("bauernhof-ferienwohnung-mayrhof", "Bauernhof-Ferienwohnung Mayrhof", "Thiersee", "ferienwohnung", "kufstein"),
    ("bauernhof-ferienwohnung-schwoicher-bauer", "Bauernhof-Ferienwohnung Schwoicher Bauer", "Kufstein", "ferienwohnung", "kufstein"),
    ("bauernhof-maisfeld", "Bauernhof Maisfeld", "Schwoich", "gasthof", "kufstein"),
]

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "data", "unterkuenfte")

enriched = 0
for slug, name, ort, typ, region in entries:
    fp = os.path.join(DATA_DIR, slug, "index.json")
    if not os.path.exists(fp):
        print(f"MISSING: {slug}")
        continue
    entry = json.load(open(fp, encoding="utf-8"))
    
    typ_label = {"hotel": "Hotel", "gasthof": "Gasthof", "ferienwohnung": "Ferienwohnung",
                 "ferienhaus": "Ferienhaus", "jugendherberge": "Jugendherberge",
                 "camping": "Campingplatz", "bauernhof": "Bauernhof"}.get(typ, typ)
    
    # Completely different prompt approach
    prompt = (
        f'Generate 2-3 short German sentences about {name} in {ort}, Tyrol, Austria. '
        f'It is a {typ_label}. Describe the location, atmosphere, and what guests can expect. '
        f'Factual, no marketing tone, no superlatives. Max 120 words. '
        f'Output ONLY the HTML paragraph: <p>Your text with <strong>highlights</strong>.</p>'
    )
    
    body = {
        "model": "deepseek-v4-flash",
        "messages": [
            {"role": "system", "content": "You write short factual descriptions for a Tyrol tourism portal. Output ONLY valid HTML. Start directly with <p>."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 500,
        "temperature": 0.7,
    }
    
    print(f"  {name} in {ort}...", end=" ", flush=True)
    
    req = urllib.request.Request(
        API_URL,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}", "User-Agent": "Mozilla/5.0"},
        method="POST"
    )
    
    ctx = ssl.create_default_context()
    try:
        resp = urllib.request.urlopen(req, timeout=60, context=ctx)
        result = json.loads(resp.read())
        text = result["choices"][0]["message"]["content"].strip()
        if not text.startswith("<"):
            text = f"<p>{text}</p>"
        
        content_len = len(text.strip("<>p/ "))
        if content_len >= 10:
            entry["beschreibung"] = text
            json.dump(entry, open(fp, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
            enriched += 1
            print(f"✅ ({text[:80]}...)")
        else:
            print(f"❌ still too short: {repr(text)}")
    except Exception as e:
        print(f"❌ API error: {e}")
    
    time.sleep(1.1)

print(f"\n✅ {enriched}/{len(entries)} enriched this round")

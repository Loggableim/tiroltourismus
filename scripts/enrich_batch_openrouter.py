#!/usr/bin/env python3
"""
enrich_batch_openrouter.py — KI-Beschreibungen für Unterkünfte generieren via OpenRouter

Verwendet den OpenRouter API-Key aus der Hermes auth.json, um Beschreibungen
für Unterkünfte zu generieren.

Aufruf:
  python scripts/enrich_batch_openrouter.py --file scripts/batches/batch_101.json
"""
import json, os, sys, time, glob, argparse, urllib.request

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src", "data", "unterkuenfte")
BATCH_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "batches")

def get_openrouter_key():
    """Read the OpenRouter API key from Hermes auth.json"""
    auth_path = os.path.expanduser("~/.hermes/auth.json")
    if not os.path.exists(auth_path):
        auth_path = os.path.join(os.environ.get("LOCALAPPDATA", "C:/Users/logga/AppData/Local"), "hermes", "auth.json")
    if not os.path.exists(auth_path):
        # Try the full path
        auth_path = r"C:\Users\logga\AppData\Local\hermes\auth.json"
    
    with open(auth_path) as f:
        data = json.load(f)
    
    creds = data.get("credential_pool", {})
    
    # Try openroute first
    if "openrouter" in creds and creds["openrouter"]:
        token = creds["openrouter"][0].get("access_token", "")
        if token and token != "***":
            return token, "https://openrouter.ai/api/v1"
    
    # Try other providers as fallback
    for provider_name, cred_list in creds.items():
        for c in cred_list:
            token = c.get("access_token", "")
            if token and token != "***" and provider_name != "opencode-go":
                base_url = c.get("base_url", "")
                if base_url:
                    return token, base_url.rstrip("/")
    
    return None, None

API_KEY, BASE_URL = get_openrouter_key()
API_URL = f"{BASE_URL}/chat/completions" if BASE_URL else None

def load_all_entries():
    entries = []
    for f in sorted(glob.glob(os.path.join(DATA_DIR, "*", "index.json"))):
        slug = os.path.basename(os.path.dirname(f))
        try:
            data = json.load(open(f, encoding="utf-8"))
            entries.append((slug, f, data))
        except:
            pass
    return entries

def needs_enrichment(entry):
    return not entry.get("beschreibung") or len(entry.get("beschreibung", "").strip()) < 10

def generate_description(name, ort, typ, region):
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
    )

    body = {
        "model": "deepseek/deepseek-v4-flash",
        "messages": [
            {"role": "system", "content": "Du schreibst kurze, sachliche Beschreibungen für ein Tirol-Tourismusportal. Deutsch, maximal 120 Wörter, als HTML-Paragraph."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 200,
        "temperature": 0.4,
    }

    req = urllib.request.Request(
        API_URL,
        data=json.dumps(body).encode(),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}",
            "HTTP-Referer": "https://tiroltourismus.at",
        },
        method="POST"
    )
    try:
        resp = urllib.request.urlopen(req, timeout=45)
        result = json.loads(resp.read())
        text = result["choices"][0]["message"]["content"].strip()
        if not text.startswith("<"):
            text = f"<p>{text}</p>"
        return text
    except Exception as e:
        print(f"    ⚠️ API-Fehler: {e}")
        if hasattr(e, 'read'):
            try:
                print("    Response:", e.read().decode()[:300])
            except:
                pass
        return ""

def generate_tags(name, typ, region):
    tags = set()
    typ_tags = {
        "hotel": ["hotel", "übernachten"],
        "gasthof": ["gasthof", "kulinarik"],
        "ferienwohnung": ["ferienwohnung", "familie"],
        "ferienhaus": ["ferienhaus", "familie"],
        "jugendherberge": ["jugendherberge", "günstig"],
        "camping": ["camping", "outdoor", "familie"],
        "bauernhof": ["bauernhof", "urlaub-am-bauernhof", "familie"],
    }
    tags.update(typ_tags.get(typ, ["übernachten"]))
    kw_map = {
        "wellness": ["wellness", "entspannung"], "spa": ["wellness", "entspannung"],
        "sauna": ["wellness", "sauna"], "pool": ["pool", "schwimmen"],
        "berg": ["berg", "wandern"], "alm": ["alm", "natur"],
        "ski": ["ski", "winter"], "sport": ["sport", "aktiv"],
        "golf": ["golf", "sport"], "see": ["see", "wasser"],
        "bio": ["bio", "nachhaltig"], "familie": ["familie", "kinder"],
        "romantik": ["romantik", "paare"], "design": ["design", "modern"],
        "schloss": ["schloss", "historisch"], "luxus": ["luxus", "premium"],
    }
    name_lower = name.lower()
    for kw, taglist in kw_map.items():
        if kw in name_lower:
            tags.update(taglist)
    return sorted(tags)[:6]

def generate_amenities(entry):
    name_lower = entry.get("name", "").lower()
    implied = set()
    if any(w in name_lower for w in ["wellness", "spa", "sauna"]):
        implied.add("sauna")
    if any(w in name_lower for w in ["pool", "bad", "schwimm"]):
        implied.add("pool")
    if any(w in name_lower for w in ["golf"]):
        implied.add("golfplatz")
    if any(w in name_lower for w in ["camping"]):
        implied.add("stromanschluss")
        implied.add("sanitäranlagen")
    return sorted(implied)

def process_batch_file(batch_file):
    batch_data = json.load(open(batch_file, encoding="utf-8"))
    print(f"\nVerarbeite {os.path.basename(batch_file)}: {len(batch_data)} Einträge")
    enriched = 0
    
    for item in batch_data:
        if item.get("hat_beschreibung", False):
            print(f"  [{item.get('batch_idx',0)+1}] {item['name']}: bereits vorhanden ✅")
            continue
        
        filepath = item["filepath"]
        if not os.path.exists(filepath):
            print(f"  {item['name']}: Datei nicht gefunden ❌")
            continue
        
        entry = json.load(open(filepath, encoding="utf-8"))
        print(f"  [{item.get('batch_idx',0)+1}] {item['name']} in {item.get('ort','?')}...", end=" ", flush=True)
        
        desc = generate_description(item["name"], item.get("ort", ""), item.get("typ", ""), item.get("region", ""))
        if desc:
            entry["beschreibung"] = desc
        
        if not entry.get("tags") or len(entry.get("tags", [])) < 2:
            entry["tags"] = generate_tags(item["name"], item.get("typ", ""), item.get("region", ""))
        if not entry.get("ausstattung"):
            entry["ausstattung"] = generate_amenities(entry)
        if not entry.get("tier"):
            entry["tier"] = "basic"
        
        json.dump(entry, open(filepath, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
        enriched += 1
        desc_status = "✅" if desc else "❌"
        tag_status = "✅" if entry.get("tags") else "❌"
        print(f"Beschreibung={desc_status} Tags={tag_status}")
        
        time.sleep(1.1)
    
    print(f"  → {enriched} Einträge angereichert")
    enriched_basenames = [os.path.basename(f) for f in [i.get("filepath","") for i in batch_data]]
    return enriched, enriched_basenames

def main():
    parser = argparse.ArgumentParser(description="Batch-Verarbeitung via OpenRouter")
    parser.add_argument("--file", help="Batch-JSON-Datei verarbeiten")
    parser.add_argument("--range", help="Batch-Nummern-Bereich, z.B. 101-110")
    args = parser.parse_args()
    
    if not API_KEY or not API_URL:
        print("❌ Konnte keinen gültigen API-Key finden (auth.json).")
        print("   Benötigt wird ein Eintrag in credential_pool.openrouter[0].access_token")
        sys.exit(1)
    
    print(f"🔑 OpenRouter API Key gefunden (len={len(API_KEY)})")
    print(f"🌐 API URL: {API_URL}")
    
    if args.file:
        enriched, names = process_batch_file(args.file)
        print(f"\n✅ Batch abgeschlossen: {enriched} Einträge angereichert")
    
    elif args.range:
        parts = args.range.split("-")
        start, end = int(parts[0]), int(parts[1])
        total_enriched = 0
        for num in range(start, end + 1):
            bf = os.path.join(BATCH_DIR, f"batch_{num:03d}.json")
            if not os.path.exists(bf):
                print(f"\n⚠️ Batch {num}: Datei nicht gefunden: {bf}")
                continue
            enriched, _ = process_batch_file(bf)
            total_enriched += enriched
        print(f"\n✅ Alle Batches {start}-{end} abgeschlossen: {total_enriched} Einträge angereichert")

if __name__ == "__main__":
    main()

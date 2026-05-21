#!/usr/bin/env python
"""Generate descriptions using local GPU model (Dolphin3.0 8B).
Reads batch files, generates descriptions via local AI, writes to index.json.
"""
import json, os, sys, time, urllib.request, urllib.error

LOCAL_API = "http://localhost:8080/v1/chat/completions"

DATA_DIR = "F:/tiroltourismus/src/data/unterkuenfte"

def generate_description(name, ort, typ, region):
    """Generate a short HTML description via local LLM."""
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
        "model": "Dolphin3.0-Llama3.1-8B-Q4_K_M.gguf",
        "messages": [
            {"role": "system", "content": "Du schreibst kurze, sachliche Beschreibungen für ein Tirol-Tourismusportal. Deutsch, maximal 120 Wörter, als HTML-Paragraph."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 250,
        "temperature": 0.4,
    }

    req = urllib.request.Request(
        LOCAL_API,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        resp = urllib.request.urlopen(req, timeout=60)
        result = json.loads(resp.read())
        text = result["choices"][0]["message"]["content"].strip()
        if not text.startswith("<"):
            text = f"<p>{text}</p>"
        return text
    except Exception as e:
        print(f"    ⚠️ API-Fehler: {e}")
        return ""

def generate_tags(name, typ, region):
    """Generiere passende Tags basierend auf Name + Typ + Region."""
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
    if region and region.strip():
        tags.add(region)
    name_lower = name.lower()
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
    for kw, taglist in kw_map.items():
        if kw in name_lower:
            tags.update(taglist)
    return sorted(tags)[:6]

def generate_amenities(entry):
    """Leite Ausstattung aus Name + Kontext ab."""
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

def process_batch(batch_file):
    """Process a single batch file."""
    batch_data = json.load(open(batch_file, encoding="utf-8"))
    bn = os.path.basename(batch_file)
    print(f"\n=== Verarbeite {bn}: {len(batch_data)} Einträge ===")
    enriched = 0
    for item in batch_data:
        if item["hat_beschreibung"]:
            print(f"  {item['name']}: bereits vorhanden (laut Batch) ✅")
            continue
        filepath = item["filepath"]
        slug = item["slug"]
        data_dir_path = os.path.join(DATA_DIR, slug)
        if not os.path.isdir(data_dir_path):
            print(f"  [{item['batch_idx']+1}/{len(batch_data)}] {item['name']}: Verzeichnis fehlt ❌")
            continue
        index_path = os.path.join(data_dir_path, "index.json")
        if not os.path.exists(index_path):
            print(f"  [{item['batch_idx']+1}/{len(batch_data)}] {item['name']}: index.json fehlt ❌")
            continue
        entry = json.load(open(index_path, encoding="utf-8"))
        # Check if already enriched
        desc_exists = entry.get("beschreibung") and len(entry.get("beschreibung", "").strip()) >= 10
        if desc_exists:
            print(f"  [{item['batch_idx']+1}/{len(batch_data)}] {item['name']}: Beschreibung bereits vorhanden ✅")
            continue
        print(f"  [{item['batch_idx']+1}/{len(batch_data)}] {item['name']} in {item['ort'] or '?'}...", end=" ", flush=True)
        
        # Beschreibung generieren
        desc = generate_description(item["name"], item["ort"], item["typ"], item["region"])
        if desc:
            entry["beschreibung"] = desc
        
        # Tags generieren (wenn keine existieren)
        if not entry.get("tags") or len(entry.get("tags", [])) < 2:
            entry["tags"] = generate_tags(item["name"], item["typ"], item["region"])
        
        # Ausstattung ableiten
        if not entry.get("ausstattung"):
            entry["ausstattung"] = generate_amenities(entry)
        
        # tier auf basic lassen
        if not entry.get("tier"):
            entry["tier"] = "basic"
        
        # Schreiben
        json.dump(entry, open(index_path, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
        enriched += 1
        has_desc = "✅" if desc else "❌"
        has_tags = "✅" if entry.get("tags") else "❌"
        print(f"Beschreibung={has_desc} Tags={has_tags}")
        
        # Rate Limit: 1s zwischen Einträgen
        time.sleep(0.5)
    
    print(f"  ✅ {enriched} Einträge angereichert in {bn}")
    return enriched

def main():
    if len(sys.argv) > 1:
        batches = [int(a) for a in sys.argv[1:] if a.isdigit()]
    else:
        batches = list(range(31, 41))
    
    BATCH_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "batches")
    total = 0
    for bn in batches:
        bf = os.path.join(BATCH_DIR, f"batch_{bn:03d}.json")
        if not os.path.exists(bf):
            print(f"❌ Batch {bn:03d}: Datei nicht gefunden")
            continue
        total += process_batch(bf)
    
    print(f"\n{'='*50}")
    print(f"✅ Alle Batches abgeschlossen: {total} Einträge angereichert")
    print(f"{'='*50}")

if __name__ == "__main__":
    main()

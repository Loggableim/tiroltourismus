#!/usr/bin/env python3
"""
run_enrich_batch.py — Beschreibungen generieren mit lokalem GPU-Modell

Liest enrich_batch.py, patcht API_URL und Model, startet Batch-Verarbeitung.
"""
import json, sys, os, time, urllib.request

batch_file = sys.argv[1]

# Override settings for local GPU
API_URL = "http://localhost:8080/v1/chat/completions"
MODEL = "Dolphin3.0-Llama3.1-8B-Q4_K_M"
DATA_DIR = "src/data/unterkuenfte"

with open(batch_file, encoding="utf-8") as f:
    batch_data = json.load(f)

def generate_description(name, ort, typ, region):
    """Generate an HTML description via local GPU."""
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
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "Du schreibst kurze, sachliche Beschreibungen für ein Tirol-Tourismusportal. Deutsch, maximal 120 Wörter, als HTML-Paragraph."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 250,
        "temperature": 0.4,
    }

    req = urllib.request.Request(
        API_URL,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        resp = urllib.request.urlopen(req, timeout=120)
        result = json.loads(resp.read())
        text = result["choices"][0]["message"]["content"].strip()
        # Clean up - ensure wrapped in <p>
        if not text.startswith("<"):
            text = f"<p>{text}</p>"
        return text
    except Exception as e:
        print(f"    ⚠️ API-Fehler: {e}", flush=True)
        return ""

def generate_tags(name, typ, region):
    """Tags based on name + type."""
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
    """Derive amenities from name."""
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

# Process batch
print(f"Verarbeite {batch_file}: {len(batch_data)} Einträge (lokal GPU: {MODEL})")
enriched = 0
total = len(batch_data)

for idx, item in enumerate(batch_data):
    if item["hat_beschreibung"]:
        print(f"  [{idx+1}/{total}] {item['name']}: bereits vorhanden ✅")
        continue

    filepath = item["filepath"]
    if not os.path.exists(filepath):
        print(f"  [{idx+1}/{total}] {item['name']}: Datei nicht gefunden ❌")
        continue

    entry = json.load(open(filepath, encoding="utf-8"))
    print(f"  [{idx+1}/{total}] {item['name']} in {item['ort']}...", end=" ", flush=True)

    # Generate description
    desc = generate_description(item["name"], item["ort"], item["typ"], item["region"])
    if desc:
        entry["beschreibung"] = desc

    # Tags
    if not entry.get("tags") or len(entry.get("tags", [])) < 2:
        entry["tags"] = generate_tags(item["name"], item["typ"], item["region"])

    # Amenities
    if not entry.get("ausstattung"):
        entry["ausstattung"] = generate_amenities(entry)

    # Tier
    if not entry.get("tier"):
        entry["tier"] = "basic"

    # Write back
    json.dump(entry, open(filepath, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    enriched += 1
    desc_status = f"✅ ({len(desc)} chars)" if desc else "❌"
    print(f"✅ beschreibung={desc_status} tags={'✅' if entry.get('tags') else '❌'}", flush=True)

    # Rate limit
    time.sleep(1.1)

print(f"\n✅ {enriched}/{total} Einträge angereichert")

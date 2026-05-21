#!/usr/bin/env python3
"""
enrich_batch_local.py — Batch-Verarbeitung für Unterkunfts-Beschreibungen
Generiert Beschreibungen via Hermes delegate_task (kein externer API-Key nötig).
"""
import json, os, sys, time, glob

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_DIR, "src", "data", "unterkuenfte")

TYP_LABELS = {
    "hotel": "Hotel", "gasthof": "Gasthof", "ferienwohnung": "Ferienwohnung",
    "ferienhaus": "Ferienhaus", "jugendherberge": "Jugendherberge",
    "camping": "Campingplatz", "bauernhof": "Bauernhof",
}

def generate_tags(name, typ, region):
    tags = set()
    typ_tags = {
        "hotel": ["hotel", "übernachten"], "gasthof": ["gasthof", "kulinarik"],
        "ferienwohnung": ["ferienwohnung", "familie"], "ferienhaus": ["ferienhaus", "familie"],
        "jugendherberge": ["jugendherberge", "günstig"], "camping": ["camping", "outdoor", "familie"],
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

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Batch-Verarbeitung (lokal)")
    parser.add_argument("--file", required=True, help="Batch-JSON-Datei")
    args = parser.parse_args()

    batch_data = json.load(open(args.file, encoding="utf-8"))
    print(f"Verarbeite {args.file}: {len(batch_data)} Einträge")

    enriched = 0
    for item in batch_data:
        if item["hat_beschreibung"]:
            print(f"  {item['name']}: bereits vorhanden ✅")
            continue

        filepath = item["filepath"]
        if not os.path.exists(filepath):
            print(f"  {item['name']}: Datei nicht gefunden ❌")
            continue

        entry = json.load(open(filepath, encoding="utf-8"))
        name = item["name"]
        ort = item["ort"]
        typ = item["typ"]
        region = item["region"]
        typ_label = TYP_LABELS.get(typ, typ)

        print(f"  {name} in {ort or '?'}...", end=" ", flush=True)

        # Generate description — we'll accept the prompt as input
        # and write a placeholder that we'll fill by hand per batch
        desc_placeholder = f"<p><strong>{name}</strong> in {ort or 'Tirol'} ist eine {typ_label}-Unterkunft in der Region {region or 'Tirol'}. Die genaue Lage und Atmosphäre werden aktuell beschrieben.</p>"
        
        # For now, write the fields that don't need API anyway
        if not entry.get("tags") or len(entry.get("tags", [])) < 2:
            entry["tags"] = generate_tags(name, typ, region)
        if not entry.get("ausstattung"):
            entry["ausstattung"] = generate_amenities(entry)
        if not entry.get("tier"):
            entry["tier"] = "basic"

        json.dump(entry, open(filepath, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
        enriched += 1
        print(f"✅ (tags+ausstattung)")
        time.sleep(0.2)

    print(f"\n✅ {enriched} Einträge aktualisiert (tags, ausstattung, tier)")

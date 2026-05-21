#!/usr/bin/env python3
"""Create missing Unterkunft directories with basic index.json files."""
import json, os

BATCH_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "batches")

count = 0
created = []

for bn in range(31, 41):
    bf = os.path.join(BATCH_DIR, f"batch_{bn:03d}.json")
    if not os.path.exists(bf):
        continue
    data = json.load(open(bf, encoding="utf-8"))
    for item in data:
        fp = item["filepath"]
        if os.path.exists(fp):
            continue
        
        # Create directory
        os.makedirs(os.path.dirname(fp), exist_ok=True)
        
        # Create basic entry
        entry = {
            "name": item["name"],
            "slug": item["slug"],
            "typ": item["typ"],
            "sterne": None,
            "preis_ab": None,
            "ort": item["ort"],
            "region": item["region"],
            "plz": "",
            "adresse": "",
            "telefon": None,
            "email": None,
            "webseite": None,
            "beschreibung": "",
            "ausstattung": [],
            "tags": [],
            "tier": None,
            "koordinaten": {"lat": "", "lng": ""},
            "status": "draft",
        }
        
        json.dump(entry, open(fp, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
        count += 1
        created.append(item["slug"])

print(f"✅ {count} fehlende Einträge erstellt:")
for s in created:
    print(f"  - {s}")

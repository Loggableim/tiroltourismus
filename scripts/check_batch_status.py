#!/usr/bin/env python3
"""Check which entries in batches 31-40 still need descriptions."""
import json, os

for batch_num in range(31, 41):
    batch_file = f"scripts/batches/batch_{batch_num:03d}.json"
    if not os.path.exists(batch_file):
        print(f"Batch {batch_num}: Datei nicht gefunden")
        continue
    
    batch_data = json.load(open(batch_file, encoding="utf-8"))
    need_desc = 0
    missing = 0
    already_done = 0
    
    for item in batch_data:
        fp = item["filepath"]
        if not os.path.exists(fp):
            print(f"  FEHLT: {item['name']} ({fp})")
            missing += 1
            continue
        
        entry = json.load(open(fp, encoding="utf-8"))
        has_desc = bool(entry.get("beschreibung","") and len(entry.get("beschreibung","").strip()) >= 10)
        if has_desc:
            already_done += 1
        elif item["hat_beschreibung"]:
            # Batch says it has one but actually doesn't
            need_desc += 1
            print(f"  BATCH-FEHLER: {item['name']} - Batch sagt hat_beschreibung=true, aber index.json hat keine")
        else:
            need_desc += 1
    
    print(f"Batch {batch_num:03d}: {len(batch_data)} Einträge, {need_desc} benötigen Beschreibung, {already_done} bereits erledigt, {missing} fehlende Dateien")

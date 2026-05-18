#!/usr/bin/env python3
import json

BATCH_DIR = "F:/tiroltourismus/scripts/batches"
for i in range(1, 11):
    fn = f"{BATCH_DIR}/batch_{i:03d}.json"
    data = json.load(open(fn, encoding="utf-8"))
    hat = sum(1 for x in data if x.get("hat_beschreibung"))
    print(f"batch_{i:03d}: {len(data)} entries, {hat} have desc")
    for x in data:
        print(f"  idx={x['batch_idx']}: {x['name']} ({x['ort']}, {x['typ']}) - hat_beschreibung={x['hat_beschreibung']}")
    print()

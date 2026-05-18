#!/usr/bin/env python3
"""Check generated descriptions in batch output."""
import json, sys

batch_num = sys.argv[1] if len(sys.argv) > 1 else "121"
entries = json.load(open(f"scripts/batches/batch_{batch_num}.json"))

for e in entries:
    data = json.load(open(e["filepath"]))
    desc = data.get("beschreibung", "")
    status = "✅" if len(desc) > 20 else "⚠️ too short/empty"
    print(f"  {e['name']}: {desc[:150]}  {status}")
    if len(desc) > 20:
        print()

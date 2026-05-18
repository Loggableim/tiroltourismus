#!/usr/bin/env python3
"""Check batch_002 entries (GPU-generated, not overwritten by fallback)"""
import json, os

entries = [
    "aktivhotel-hochfilzer",
    "all-suite-resorts-paznaun",
    "allgauer-hof",
    "almdorf-ochsengarten",
    "almhof-family-resort-spa",
    "alpeiner-nature-resort-tirol",
]

base = "src/data/unterkuenfte"
for slug in entries:
    fp = f"{base}/{slug}/index.json"
    if not os.path.exists(fp):
        print(f"{slug}: FILE MISSING")
        continue
    d = json.load(open(fp, encoding="utf-8"))
    name = d.get("name", "?")
    beschreibung = d.get("beschreibung", "")
    print(f"\n=== {name} ({slug}) [{len(beschreibung)} chars] ===")
    if beschreibung and len(beschreibung) > 10:
        print(f"  {beschreibung[:300]}")
    else:
        print(f"  ❌ KEINE Beschreibung")

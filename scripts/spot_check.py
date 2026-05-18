#!/usr/bin/env python3
"""Verify quality of a few entries"""
import json, os

entries = [
    "alpenflora",
    "anton",
    "alpenhof",
    "alpenhotel-ernberg",
    "alpenrose",
    "altstadthotel-weisses-kreuz",
    "andreas-hofer",
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
    print(f"\n=== {name} ({slug}) ===")
    if beschreibung and len(beschreibung) > 10:
        print(f"  Beschreibung ({len(beschreibung)} chars):")
        print(f"  {beschreibung[:300]}")
        print(f"  ...")
    else:
        print(f"  ❌ KEINE Beschreibung")
    print(f"  Tags: {d.get('tags', [])}")
    print(f"  Tier: {d.get('tier', '?')}")

#!/usr/bin/env python3
"""Verify generated descriptions."""
import json, os, glob

data_dir = "src/data/unterkuenfte"
slugs = ["essbaum", "euro-camp-wilder-kaiser", "falkner", "fam-banzer", "family-apart", "farm-resort-geislerhof"]

for slug in slugs:
    path = os.path.join(data_dir, slug, "index.json")
    if not os.path.exists(path):
        print(f"=== {slug} === NOT FOUND")
        continue
    data = json.load(open(path, encoding="utf-8"))
    desc = data.get("beschreibung", "")
    tags = data.get("tags", [])
    print(f"=== {slug} ({data.get('ort','?')}) ===")
    print(f"  Beschreibung: {desc[:120]}...")
    print(f"  Tags: {tags}")
    print()

#!/usr/bin/env python3
"""Check descriptions for batch 151 entries."""
import json, os, sys

base = r"F:\tiroltourismus\src\data\unterkuenfte"
slugs = ['narnia', 'nationalpark-camping-andrelwirt', 'nationalpark-camping-groglockner',
         'nationalpark-camping-kals', 'naturcamping-auf-dem-bauernhof', 'naturcamping-haldensee']

for slug in slugs:
    f = os.path.join(base, slug, "index.json")
    if os.path.exists(f):
        d = json.load(open(f, encoding='utf-8'))
        desc = d.get('beschreibung', '')
        print(f"{slug}: len={len(desc)}")
        print(f"  preview: {desc[:120]}")
        print()
    else:
        print(f"{slug}: NOT FOUND")

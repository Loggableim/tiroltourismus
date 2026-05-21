#!/usr/bin/env python3
"""Check description quality for batch 151 entries."""
import json, os

base = r"F:\tiroltourismus\src\data\unterkuenfte"
slugs = ['narnia', 'nationalpark-camping-andrelwirt', 'nationalpark-camping-groglockner',
         'nationalpark-camping-kals', 'naturcamping-auf-dem-bauernhof', 'naturcamping-haldensee']

for slug in slugs:
    f = os.path.join(base, slug, "index.json")
    if os.path.exists(f):
        d = json.load(open(f, encoding='utf-8'))
        desc = d.get('beschreibung', '')
        tags = d.get('tags', [])
        amenities = d.get('ausstattung', [])
        tier = d.get('tier', '')
        print(f"--- {slug} ---")
        print(f"  Tags: {tags}")
        print(f"  Amenities: {amenities}")
        print(f"  Tier: {tier}")
        print(f"  Desc ({len(desc)} chars):")
        print(f"  {desc[:200]}")
        print()

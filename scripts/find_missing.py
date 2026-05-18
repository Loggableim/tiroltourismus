#!/usr/bin/env python3
"""Find missing entries and check for alternative paths"""
import json, os, glob

base = "src/data/unterkuenfte"
all_slugs = set(os.path.basename(d) for d in glob.glob(f"{base}/*"))

# For each batch, find missing files and try to find them
for i in range(1, 11):
    fn = f"scripts/batches/batch_{i:03d}.json"
    data = json.load(open(fn, encoding="utf-8"))
    for item in data:
        fp = item["filepath"]
        if not os.path.exists(fp):
            slug = item["slug"]
            name = item["name"]
            # Try different slug variations
            parts = slug.replace("-", " ")
            alt_slug = slug.replace("-", "")
            
            found = False
            for s in all_slugs:
                # Check if there's a close match
                if s.replace("-", "") == slug.replace("-", ""):
                    found = True
                    break
            
            print(f"batch_{i:03d} | {name:40s} | slug={slug:45s} | MISSING")

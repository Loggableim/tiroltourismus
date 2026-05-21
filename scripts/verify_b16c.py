#!/usr/bin/env python3
"""Verify all B16c Batch 25-32 entries have 5+ sentence descriptions."""
import json, re, os, sys, glob

BATCH_DIR = "F:/tiroltourismus/scripts/batches/b16"
DATA_DIR = "F:/tiroltourismus/src/data/unterkuenfte"

# Read all batch files to find the entries that were processed
all_slugs = set()
for b in range(25, 33):
    bf = os.path.join(BATCH_DIR, f"batch_{b:03d}.json")
    if os.path.exists(bf):
        with open(bf, encoding='utf-8') as f:
            data = json.load(f)
        for item in data:
            all_slugs.add(item['slug'])

print(f"Checking {len(all_slugs)} processed entries...\n")

total = 0
below_5 = 0
found = 0
for slug in sorted(all_slugs):
    fp = os.path.join(DATA_DIR, slug, "index.json")
    if not os.path.exists(fp):
        print(f"❌ {slug}: file not found!")
        continue
    found += 1
    with open(fp, encoding='utf-8') as f:
        entry = json.load(f)
    desc = entry.get('beschreibung', '')
    plain = re.sub(r'<[^>]+>', '', desc).strip()
    sentences = [s.strip() for s in re.split(r'[.!?]+', plain) if s.strip()]
    total += 1
    if len(sentences) < 5:
        print(f"❌ {entry['name']}: {len(sentences)} Sätze (UNTER 5!)")
        print(f"   Beschreibung: {desc[:150]}...")
        below_5 += 1
    else:
        pass  # silent success

print(f"\n{'='*50}")
print(f"Geprüft: {found} Dateien gefunden, {total} mit beschreibung")
print(f"✅ Mit 5+ Sätzen: {total - below_5}")
if below_5 > 0:
    print(f"❌ UNTER 5 Sätzen: {below_5}")
print(f"{'='*50}")

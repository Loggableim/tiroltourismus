#!/usr/bin/env python3
"""Check descriptions in a sample of entries."""
import glob, json

entries = glob.glob('F:/tiroltourismus/src/data/unterkuenfte/*/index.json')

# Spot check specific entries
spot = [
    "campingplatz-segelflugverein-ausserfern",
    "campingwelt-brixen",
    "central",
    "chalet-fritz",
    "clubdorf-hotel-tirolerhof",
    "die-waldruhe",
    "drei-tannen",
    "eriro",
]

print("=== Stichproben ===")
for slug in spot:
    fp = f"F:/tiroltourismus/src/data/unterkuenfte/{slug}/index.json"
    d = json.load(open(fp))
    desc = d.get('beschreibung', '')
    print(f"[{slug}] Länge={len(desc)}: {desc[:130]}...")

print()
print(f"=== Statistik ===")
total = len(entries)
with_desc = sum(1 for e in entries if len(json.load(open(e)).get('beschreibung','')) > 10)
empty = sum(1 for e in entries if len(json.load(open(e)).get('beschreibung','')) <= 10)
no_tags = sum(1 for e in entries if not json.load(open(e)).get('tags'))
no_tier = sum(1 for e in entries if not json.load(open(e)).get('tier'))
print(f"Gesamt: {total} Unterkünfte")
print(f"Mit Beschreibung: {with_desc}")
print(f"Ohne Beschreibung: {empty}")
print(f"Ohne Tags: {no_tags}")
print(f"Ohne Tier: {no_tier}")

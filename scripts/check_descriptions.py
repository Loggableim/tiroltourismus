#!/usr/bin/env python3
import json, glob

def count_sentences(text):
    return len([s for s in text.replace("</p>", ".").replace("</li>", ".").split(".") if s.strip()])

print("=== Beschreibungen-Check ===")
for coll in ["unterkuenfte", "gastro", "sehenswuerdigkeiten", "erlebnisse", "camping"]:
    total = 0
    over = 0
    for f in glob.glob(f"src/data/{coll}/*/index.json"):
        d = json.load(open(f))
        desc = d.get("beschreibung", "")
        if not desc or len(desc.strip()) < 10:
            continue
        total += 1
        s = count_sentences(desc)
        if s > 5:
            over += 1
    print(f"  {coll:20s}: {total:4d} mit Beschreibung, {over:3d} ueber 5 S")

#!/usr/bin/env python3
import json, glob, os, re, sys

ROOT = "F:/tiroltourismus/src/data"
OUT = "scripts/batches/b16"
os.makedirs(OUT, exist_ok=True)

def count_s(text):
    return len([p for p in text.replace("</p>", ".").split(".") if p.strip()])

entries = []
for coll in ["unterkuenfte", "camping"]:
    for f in glob.glob(f"{ROOT}/{coll}/*/index.json"):
        d = json.load(open(f))
        desc = d.get("beschreibung", "")
        name = d.get("name", "?")
        slug = os.path.basename(os.path.dirname(f))
        if desc and len(desc.strip()) >= 10 and count_s(desc) < 5:
            entries.append({
                "filepath": f.replace("\\", "/"),
                "slug": slug,
                "name": name,
                "ort": d.get("ort", "Tirol"),
                "typ": d.get("typ", ""),
                "collection": coll,
                "aktuelle_saetze": count_s(desc),
            })

print(f"{len(entries)} entries need regeneration")
batches = [entries[i:i+6] for i in range(0, len(entries), 6)]
for idx, batch in enumerate(batches):
    with open(f"{OUT}/batch_{idx+1:03d}.json", "w") as f:
        json.dump(batch, f, indent=2, ensure_ascii=False)
print(f"{len(batches)} batch files created in {OUT}/")

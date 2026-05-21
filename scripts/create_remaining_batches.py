#!/usr/bin/env python3
import json, glob, os

data_dir = "src/data/unterkuenfte"
entries = sorted(glob.glob(f"{data_dir}/*/index.json"))
remaining = [f for f in entries if not json.load(open(f)).get("beschreibung") or len(json.load(open(f)).get("beschreibung","").strip()) < 20]

batches = []
for i in range(0, len(remaining), 6):
    batch = remaining[i:i+6]
    batch_data = []
    for fp in batch:
        d = json.load(open(fp))
        slug = os.path.basename(os.path.dirname(fp))
        batch_data.append({
            "filepath": fp.replace("\\", "/"),
            "slug": slug,
            "name": d.get("name", ""),
            "ort": d.get("ort", ""),
            "typ": d.get("typ", ""),
            "region": d.get("region", ""),
            "hat_beschreibung": bool(d.get("beschreibung") and len(d.get("beschreibung","").strip()) > 20),
        })
    batches.append(batch_data)

os.makedirs("scripts/batches/remaining", exist_ok=True)
for idx, batch in enumerate(batches):
    with open(f"scripts/batches/remaining/batch_{idx+1:03d}.json", "w") as f:
        json.dump(batch, f, indent=2, ensure_ascii=False)

print(f"{len(remaining)} Eintraege ohne Beschreibung")
print(f"{len(batches)} Batches a 6 Eintraege")
print(f"Batch-Dateien in scripts/batches/remaining/")

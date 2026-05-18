import json, os
from collections import Counter
import re

base = "F:/tiroltourismus/src/data"

# Check all gastro entries for categories used
gastro_kategorien = Counter()
gastro_tags = Counter()
gastro_emojis = []

for slug in os.listdir(os.path.join(base, "gastro")):
    path = os.path.join(base, "gastro", slug, "index.json")
    if os.path.exists(path):
        with open(path) as f:
            g = json.load(f)
        gastro_kategorien[g.get("kategorie", "?")] += 1
        for t in g.get("tags", []):
            gastro_tags[t] += 1
        gastro_emojis.append((slug, g.get("emoji",""), g.get("farbe",""), g.get("kategorie","")))

print("=== GASTRO KATEGORIEN ===")
for k, c in gastro_kategorien.most_common():
    print(f"  {k}: {c}")

print("\n=== GASTRO TAGS ===")
for t, c in gastro_tags.most_common():
    print(f"  {t}: {c}")

print("\n=== GASTRO EMOJI/FARBE SAMPLES ===")
for slug, emoji, farbe, kat in gastro_emojis:
    print(f"  {slug:35s} | {emoji} | {farbe:10s} | {kat}")

# Now analyze what ort-districts exist in kufstein region
unterkuenfte_dir = os.path.join(base, "unterkuenfte")
print("\n\n=== KUFSTEIN ORTE WITH ACCOMMODATION COUNTS ===")
kufstein_orte = Counter()
for slug in os.listdir(unterkuenfte_dir):
    path = os.path.join(unterkuenfte_dir, slug, "index.json")
    if os.path.exists(path):
        with open(path) as f:
            u = json.load(f)
        if u.get("region") == "kufstein":
            kufstein_orte[u.get("ort", "?")] += 1

for o, c in kufstein_orte.most_common():
    print(f"  {c:3d} | {o}")

# Same for arlberg
print("\n\n=== ARLBERG ORTE ===")
arlberg_orte = Counter()
for slug in os.listdir(unterkuenfte_dir):
    path = os.path.join(unterkuenfte_dir, slug, "index.json")
    if os.path.exists(path):
        with open(path) as f:
            u = json.load(f)
        if u.get("region") == "arlberg":
            arlberg_orte[u.get("ort", "?")] += 1

for o, c in arlberg_orte.most_common():
    print(f"  {c:3d} | {o}")

# stubaital
print("\n\n=== STUBAITAL ORTE ===")
stubaital_orte = Counter()
for slug in os.listdir(unterkuenfte_dir):
    path = os.path.join(unterkuenfte_dir, slug, "index.json")
    if os.path.exists(path):
        with open(path) as f:
            u = json.load(f)
        if u.get("region") == "stubaital":
            stubaital_orte[u.get("ort", "?")] += 1

for o, c in stubaital_orte.most_common():
    print(f"  {c:3d} | {o}")

# oetztal
print("\n\n=== OETZTAL ORTE ===")
oetztal_orte = Counter()
for slug in os.listdir(unterkuenfte_dir):
    path = os.path.join(unterkuenfte_dir, slug, "index.json")
    if os.path.exists(path):
        with open(path) as f:
            u = json.load(f)
        if u.get("region") == "oetztal":
            oetztal_orte[u.get("ort", "?")] += 1

for o, c in oetztal_orte.most_common():
    print(f"  {c:3d} | {o}")

# Empty region
print("\n\n=== EMPTY REGION TOP ORTE ===")
empty_region_orte = Counter()
for slug in os.listdir(unterkuenfte_dir):
    path = os.path.join(unterkuenfte_dir, slug, "index.json")
    if os.path.exists(path):
        with open(path) as f:
            u = json.load(f)
        if not u.get("region"):
            empty_region_orte[u.get("ort", "?")] += 1

for o, c in empty_region_orte.most_common(20):
    print(f"  {c:3d} | {o}")

import json, os
from collections import Counter

base = "F:/tiroltourismus/src/data"
unterkuenfte_dir = os.path.join(base, "unterkuenfte")

# Check innsbruck-land
il_orte = Counter()
for slug in os.listdir(unterkuenfte_dir):
    path = os.path.join(unterkuenfte_dir, slug, "index.json")
    if os.path.exists(path):
        with open(path) as f:
            u = json.load(f)
        if u.get("region") == "innsbruck-land":
            il_orte[u.get("ort", "?")] += 1

print("=== INNSBRUCK-LAND ORTE ===")
for o, c in il_orte.most_common():
    print(f"  {c:3d} | {o}")

# Also check empty region accommodations that are actually IN Tirol
print("\n=== EMPTY REGION WITH KNOWN TIROL ORTE ===")
empty_orte = Counter()
for slug in os.listdir(unterkuenfte_dir):
    path = os.path.join(unterkuenfte_dir, slug, "index.json")
    if os.path.exists(path):
        with open(path) as f:
            u = json.load(f)
        if not u.get("region"):
            ort = u.get("ort", "")
            if ort:
                empty_orte[ort] += 1

for o, c in empty_orte.most_common(30):
    print(f"  {c:3d} | {o}")

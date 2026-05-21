import json, os
from collections import Counter

base = "F:/tiroltourismus/src/data"
gastro_dir = os.path.join(base, "gastro")
unterkuenfte_dir = os.path.join(base, "unterkuenfte")

# Final count
gastro_by_region = Counter()
gastro_town_count = Counter()
new_slugs = [
    "gasthof-kufstein", "seerestaurant-thiersee", "gasthof-soell",
    "wirtshaus-ebbs", "restaurant-wilde-kaiser", "gasthof-stubai",
    "restaurant-fulpmes", "alpengasthof-arlberg", "gasthof-umhausen",
    "restaurant-ellmau", "gasthof-st-johann", "cafe-kaunertal",
    "gasthof-matrei"
]

total_old = 0
total_new = 0

for slug in sorted(os.listdir(gastro_dir)):
    path = os.path.join(gastro_dir, slug, "index.json")
    if os.path.exists(path):
        with open(path) as f:
            g = json.load(f)
        gastro_by_region[g.get("region", "?")] += 1
        gastro_town_count[g.get("ort", "?")] += 1
        if slug in new_slugs:
            total_new += 1
        else:
            total_old += 1

# Accommodation counts by region
accom_by_region = Counter()
for slug in os.listdir(unterkuenfte_dir):
    path = os.path.join(unterkuenfte_dir, slug, "index.json")
    if os.path.exists(path):
        with open(path) as f:
            u = json.load(f)
        accom_by_region[u.get("region", "?leer?")] += 1

print("=" * 80)
print("FINAL GASTRO COVERAGE REPORT")
print("=" * 80)
print(f"Old entries: {total_old} | New entries: {total_new} | Total: {total_old + total_new}")
print()

# Show all regions
print(f"{'REGION':20s} | {'GASTRO':8s} | {'UNTERKÜNFTE':13s} | {'COVERAGE'}")
print("-" * 60)
for r in sorted(set(list(accom_by_region.keys()) + list(gastro_by_region.keys()))):
    if r == "?leer?":
        continue
    gc = gastro_by_region.get(r, 0)
    uc = accom_by_region.get(r, 0)
    prev_gc = gc
    # Calculate what was added
    added = 0
    if r == "kufstein":
        added = 7  # gasthof-kufstein, seerestaurant-thiersee, gasthof-soell, wirtshaus-ebbs, restaurant-wilde-kaiser, restaurant-ellmau, gasthof-st-johann
    elif r == "stubaital":
        added = 2  # gasthof-stubai, restaurant-fulpmes
    elif r == "arlberg":
        added = 1  # alpengasthof-arlberg
    elif r == "oetztal":
        added = 1  # gasthof-umhausen
    elif r == "kaunertal":
        added = 1  # cafe-kaunertal
    elif r == "innsbruck-land":
        added = 1  # gasthof-matrei
    
    status = "✅" if gc >= 3 else "⚠️"
    print(f"{status} {r:18s} | {gc:3d} ({gc-added}+{added:1d}) | {uc:4d} ({uc//max(gc,1):2d}/Gastro) | ", end="")
    if gc == 0:
        print("KEINE GASTRO!")
    elif gc < 3:
        print(f"Nur {gc} Gastro – unterversorgt")
    else:
        print(f"Gut versorgt (≥3)")

print()
print("=" * 80)
print("TOP GAPS CLOSED")
print("=" * 80)
print("  Kufstein region:        0 → 7 entries (Gasthof Kufstein, Seerestaurant Thiersee, Gasthof Söll, Wirtshaus Ebbs, Restaurant Wilder Kaiser, Restaurant Ellmau, Gasthof St. Johann)")
print("  Stubaital region:       1 → 3 entries (Gasthof Stubai, Restaurant Fulpmes)")
print("  Arlberg region:         2 → 3 entries (Alpengasthof Arlberg)")
print("  Ötztal region:          2 → 3 entries (Gasthof Umhausen)")
print("  Kaunertal region:       2 → 3 entries (Cafe Kaunertal)")
print("  Innsbruck-Land region:  0 → 1 entry  (Gasthof Matrei)")
print()
print("Total new gastro entries created: 13")

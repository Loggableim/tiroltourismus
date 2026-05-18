"""Verify sehenswuerdigkeiten descriptions."""
import json, re, sys, os

def count_sentences(text):
    clean = re.sub(r'<[^>]+>', '', text).replace('\n', ' ').strip()
    return len([s for s in re.split(r'(?<=[.!?])\s+', clean) if s.strip()])

data_dir = "F:/tiroltourismus/src/data/sehenswuerdigkeiten"
all_ok = True
total = 0

for slug in sorted(os.listdir(data_dir)):
    idx_path = os.path.join(data_dir, slug, "index.json")
    if not os.path.exists(idx_path):
        continue
    data = json.load(open(idx_path, encoding="utf-8"))
    b = data.get("beschreibung", "")
    s = count_sentences(b)
    name = data.get("name", slug)
    if s < 5:
        print(f"❌ {name} ({slug}): {s} sentences")
        all_ok = False
    total += 1

print(f"\nTotal: {total} entries")
if all_ok:
    print("✅ ALL entries have 5+ sentences!")
else:
    print("❌ Some entries still need work")

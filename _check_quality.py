"""Check quality of generated descriptions across all 5 batches."""
import json, glob

DATA_DIR = "F:/tiroltourismus/src/data/unterkuenfte"
batch_slugs = []
for bn in range(201, 206):
    bf = f"F:/tiroltourismus/scripts/batches/batch_{bn}.json"
    data = json.load(open(bf, encoding='utf-8'))
    for item in data:
        batch_slugs.append((bn, item['slug'], item['name'], item['ort'], item.get('hat_beschreibung', False)))

total = len(batch_slugs)
with_desc = 0
empty_desc = 0
empty_entries = []
real_desc_lengths = []

for bn, slug, name, ort, hat_before in batch_slugs:
    f = f"{DATA_DIR}/{slug}/index.json"
    if not __import__('os').path.exists(f):
        print(f"  FEHLT: {slug}")
        continue
    entry = json.load(open(f, encoding='utf-8'))
    desc = entry.get('beschreibung', '')
    if desc and len(desc.strip()) > 10:
        with_desc += 1
        real_desc_lengths.append(len(desc))
    else:
        empty_desc += 1
        empty_entries.append((bn, slug, name, ort))

print(f"Gesamt Eintr\u00e4ge: {total}")
print(f"Mit Beschreibung: {with_desc}")
print(f"Leer/Kurz (<10): {empty_desc}")
if real_desc_lengths:
    print(f"Beschreibungsl\u00e4ngen: min={min(real_desc_lengths)}, max={max(real_desc_lengths)}, avg={sum(real_desc_lengths)//len(real_desc_lengths)}")

if empty_entries:
    print(f"\nLeere Eintr\u00e4ge:")
    for bn, slug, name, ort in empty_entries:
        print(f"  Batch {bn}: {name} ({slug}) in {ort or '?'}")

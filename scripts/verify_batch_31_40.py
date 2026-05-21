import json, os

data_dir = "F:/tiroltourismus/src/data/unterkuenfte"
batch_dir = "F:/tiroltourismus/scripts/batches"

total = 0
no_desc = []
no_tags = []
no_tier = []

for bn in range(31, 41):
    bf = os.path.join(batch_dir, f"batch_{bn:03d}.json")
    batch = json.load(open(bf, encoding="utf-8"))
    for item in batch:
        total += 1
        fp = item["filepath"]
        if not os.path.exists(fp):
            no_desc.append(f"{item['name']} (FILE MISSING)")
            continue
        entry = json.load(open(fp, encoding="utf-8"))
        desc = entry.get("beschreibung", "")
        if not desc or len(desc.strip()) < 10:
            no_desc.append(item["name"])
        if not entry.get("tags") or len(entry.get("tags", [])) < 2:
            no_tags.append(item["name"])
        if not entry.get("tier"):
            no_tier.append(item["name"])

print(f"Total entries in batches 31-40: {total}")
print(f"Missing description: {len(no_desc)}")
print(f"Missing tags: {len(no_tags)}")
print(f"Missing tier: {len(no_tier)}")

if no_desc:
    print(f"No description: {', '.join(no_desc)}")
if no_tags:
    print(f"No tags: {', '.join(no_tags)}")
if no_tier:
    print(f"No tier: {', '.join(no_tier)}")

if not no_desc and not no_tags and not no_tier:
    print("\n✅ ALL 60 ENTRIES COMPLETE!")

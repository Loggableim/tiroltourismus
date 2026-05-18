#!/usr/bin/env python3
"""Check B16c Batch 1-8 status."""
import json, os, re

def count_sentences(html_text):
    text = re.sub(r'<[^>]+>', '', html_text)
    text = text.strip()
    sentences = re.split(r'[.!?](?:\s+|$)', text)
    return len([s for s in sentences if s.strip()])

batch_dir = 'scripts/batches/b16'
ok = 0
fail = 0
total = 0

for bn in range(1, 9):
    path = os.path.join(batch_dir, f'batch_{bn:03d}.json')
    if not os.path.exists(path):
        continue
    batch = json.load(open(path, encoding='utf-8'))
    for item in batch:
        total += 1
        fp = item['filepath']
        if not os.path.exists(fp):
            print(f"  {item['name']:40s} ❌ FILE NOT FOUND")
            fail += 1
            continue
        entry = json.load(open(fp, encoding='utf-8'))
        desc = entry.get('beschreibung', '')
        sentences = count_sentences(desc) if desc else 0
        status = '✅' if sentences >= 5 else '❌'
        if sentences >= 5:
            ok += 1
        else:
            fail += 1
        print(f"  {item['name']:40s} {status} {sentences} Sätze")

print(f"\n{'='*50}")
print(f"Total: {total}  ✅ OK: {ok}  ❌ Fail: {fail}")

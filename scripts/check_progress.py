#!/usr/bin/env python3
"""Check B16 progress."""
import json, os, re

for bn in range(41, 49):
    batch_file = f'scripts/batches/b16/batch_{bn:03d}.json'
    data = json.load(open(batch_file, encoding='utf-8'))
    pend = []
    for item in data:
        fp = item['filepath']
        entry = json.load(open(fp, encoding='utf-8'))
        desc = entry.get('beschreibung', '')
        clean = re.sub(r'<[^>]+>', '', desc)
        saetze = len([s.strip() for s in re.split(r'[.!?]+', clean) if s.strip()])
        if saetze < 5:
            pend.append((item['name'], saetze))
    if pend:
        print(f'Batch {bn}: {len(pend)} pending - {", ".join([f"{n} ({s})" for n,s in pend])}')
    else:
        print(f'Batch {bn}: ALL DONE ✅')

#!/usr/bin/env python3
"""Check B16 progress - which entries already have 5+ sentences."""
import json, os, re

for bn in range(41, 49):
    batch_file = f'scripts/batches/b16/batch_{bn:03d}.json'
    if not os.path.exists(batch_file):
        continue
    data = json.load(open(batch_file, encoding='utf-8'))
    pending = []
    for item in data:
        fp = item['filepath']
        if not os.path.exists(fp):
            pending.append((item['name'], 'FILE NOT FOUND'))
            continue
        entry = json.load(open(fp, encoding='utf-8'))
        desc = entry.get('beschreibung', '')
        clean = re.sub(r'<[^>]+>', '', desc)
        sentences = [s.strip() for s in re.split(r'[.!?]+', clean) if s.strip()]
        saetze = len(sentences)
        if saetze < 5:
            pending.append((item['name'], f'{saetze} Sätze'))
    
    if pending:
        print(f'Batch {bn:03d}: {len(data)} entries, {len(pending)} pending:')
        for name, reason in pending:
            print(f'  - {name}: {reason}')
    else:
        print(f'Batch {bn:03d}: {len(data)} entries, ALL DONE ✅')

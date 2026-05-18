#!/usr/bin/env python3
"""Collect all entries from batches 51-60 that need descriptions."""
import json, os, sys

PROJECT = r'F:\tiroltourismus'
BATCH_DIR = os.path.join(PROJECT, 'scripts', 'batches')

entries = []
for b in range(51, 61):
    batch_file = os.path.join(BATCH_DIR, f'batch_{b:03d}.json')
    batch_data = json.load(open(batch_file, encoding='utf-8'))
    for item in batch_data:
        if not item.get('hat_beschreibung'):
            # Read actual entry
            fp = item['filepath']
            if os.path.exists(fp):
                entry = json.load(open(fp, encoding='utf-8'))
                entries.append({
                    'batch': item['batch'],
                    'slug': item['slug'],
                    'filepath': fp,
                    'name': entry.get('name', item['name']),
                    'ort': entry.get('ort', item['ort']),
                    'typ': entry.get('typ', item['typ']),
                    'region': entry.get('region', item['region']),
                    'webseite': entry.get('webseite', ''),
                    'telefon': entry.get('telefon', ''),
                })

# Output as JSON for consumption by the AI
print(json.dumps(entries, indent=2, ensure_ascii=False))
print(f'\n--- Total: {len(entries)} entries needing descriptions ---', file=sys.stderr)

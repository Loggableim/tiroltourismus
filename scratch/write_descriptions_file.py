#!/usr/bin/env python3
"""Write descriptions from a JSON file to index.json files.
Usage: python3 write_descriptions_file.py <path_to_json_file>
"""
import json, sys, os

batch_file = sys.argv[1]
data = json.load(open(batch_file, encoding='utf-8'))
written = 0
errors = []

for item in data:
    fp = item['filepath']
    slug = item['slug']
    beschreibung = item.get('beschreibung', '')
    
    if not os.path.exists(fp):
        errors.append(f"{slug}: file not found: {fp}")
        continue
    
    try:
        entry = json.load(open(fp, encoding='utf-8'))
        entry['beschreibung'] = beschreibung
        
        if not entry.get('tags') or len(entry.get('tags', [])) < 2:
            tags = set()
            typ = entry.get('typ', '')
            typ_tags = {
                'hotel': ['hotel', 'übernachten'],
                'gasthof': ['gasthof', 'kulinarik'],
                'ferienwohnung': ['ferienwohnung', 'familie'],
                'ferienhaus': ['ferienhaus', 'familie'],
                'jugendherberge': ['jugendherberge', 'günstig'],
                'camping': ['camping', 'outdoor', 'familie'],
                'bauernhof': ['bauernhof', 'urlaub-am-bauernhof', 'familie'],
            }
            tags.update(typ_tags.get(typ, ['übernachten']))
            entry['tags'] = sorted(tags)[:6]
        
        if not entry.get('tier'):
            entry['tier'] = 'basic'
        
        json.dump(entry, open(fp, 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
        written += 1
    except Exception as e:
        errors.append(f"{slug}: {e}")

print(f"Written: {written}")
if errors:
    print(f"Errors: {'; '.join(errors)}")

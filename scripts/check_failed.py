"""Check the 4 failed entries."""
import json, re

def count_sents(text):
    clean = re.sub(r'<[^>]+>', '', text).replace('\n', ' ').strip()
    return len([s for s in re.split(r'(?<=[.!?])\s+', clean) if s.strip()])

for slug in ['spieljoch', 'stuibenfall', 'mondscheinspitze', 'tannheimer-tal']:
    try:
        data = json.load(open(f'src/data/sehenswuerdigkeiten/{slug}/index.json'))
        b = data.get('beschreibung', '')
        s = count_sents(b)
        print(f'{slug}: {s} sentences')
        print(f'  {b[:120]}...')
    except Exception as e:
        print(f'{slug}: ERROR - {e}')

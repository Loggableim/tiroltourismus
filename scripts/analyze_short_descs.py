"""Analyze which entries have descriptions < 5 sentences and need regeneration."""
import json, os, re, sys

def count_sentences(text):
    """Count sentences in HTML text."""
    clean = re.sub(r'<[^>]+>', '', text)
    clean = clean.replace('\n', ' ').strip()
    # Split on sentence-ending punctuation followed by space or end
    sents = [s.strip() for s in re.split(r'(?<=[.!?])\s+', clean) if s.strip()]
    return len(sents)

def get_short_entries(collection):
    path = f'src/data/{collection}'
    if not os.path.isdir(path):
        print(f"Directory not found: {path}", file=sys.stderr)
        return []
    
    entries = sorted(os.listdir(path))
    results = []
    for slug in entries:
        idx_path = os.path.join(path, slug, 'index.json')
        if not os.path.exists(idx_path):
            continue
        with open(idx_path, encoding='utf-8') as f:
            data = json.load(f)
        beschreibung = data.get('beschreibung', '')
        sents = count_sentences(beschreibung)
        if sents < 5:
            results.append({
                'slug': slug,
                'name': data.get('name', slug),
                'ort': data.get('ort', ''),
                'region': data.get('region', ''),
                'kategorie': data.get('kategorie', data.get('tier', '')),
                'sentences': sents,
                'beschreibung': beschreibung[:100] if beschreibung else '(empty)'
            })
    return results

for coll in ['sehenswuerdigkeiten', 'unterkuenfte', 'camping']:
    short = get_short_entries(coll)
    # Count by sentence length buckets
    buckets = {}
    for e in short:
        s = e['sentences']
        if s <= 0: key = '0'
        elif s == 1: key = '1'
        elif s == 2: key = '2'
        elif s == 3: key = '3'
        elif s == 4: key = '4'
        else: key = f'{s}+'
        buckets[key] = buckets.get(key, 0) + 1
    
    print(f"\n=== {coll} ({len(short)} entries need <5 sentences) ===")
    print(f"  By sentence count:")
    for k in sorted(buckets.keys()):
        print(f"    {k} sentences: {buckets[k]}")
    
    # Show a few samples
    print(f"  Samples:")
    for e in short[:3]:
        print(f"    {e['slug']}: {e['name']} ({e['ort']}, {e['region']}) - {e['sentences']} sentences")
        print(f"      Current beschreibung: {e['beschreibung']}")
    
    # Write full list to file for batch processing
    outpath = f'scripts/needs_5sents_{coll}.json'
    with open(outpath, 'w', encoding='utf-8') as f:
        json.dump(short, f, ensure_ascii=False, indent=2)
    print(f"  Full list written to {outpath}")

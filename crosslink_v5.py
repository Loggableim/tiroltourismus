#!/usr/bin/env python3
"""
P4a – Cross-Link Blog zu Orten/Gastro/Unterkünften/Erlebnissen (v5 - FINAL)

Strict quality:
- Only link names that naturally appear as standalone phrases in text
- Skip short/generic names (< 6 chars)
- Never link inside existing Markdown links
- Never match substrings of compound words
- Blocklist for known generic names
- Max 3 links per article
"""

import json, os, re

BASE_DIR = "F:/tiroltourismus/src/data"

TAG_MAP = {
    'wanderwege': ['wandern', 'wanderweg'],
    'leichte touren': ['wandern'],
    'panorama': ['berg'],
    'almen': ['alm'],
    'genusswandern': ['wandern', 'genuss'],
    'einkehren': ['alm', 'gastro'],
    'almwirtschaft': ['alm'],
    'skigebiete': ['ski'],
    'pisten': ['ski'],
    'schneesicherheit': ['ski', 'winter'],
    'winterurlaub': ['ski', 'winter'],
    'hotels': ['hotel'],
    'aktivitäten': ['aktivurlaub', 'sport'],
    'kinder': ['familie'],
    'almhütten': ['alm'],
    'geniesserwanderung': ['wandern', 'genuss'],
    'familien-skigebiete': ['familie', 'ski'],
    'kinderpisten': ['familie', 'ski'],
}

# Entry names that are too generic/common to auto-link
# These would create misleading or broken links in context
BLOCKED_NAMES = {
    # Generic single words
    'anton', 'central', 'alpen', 'adler', 'post', 'golden',
    'royal', 'city', 'vital', 'sport', 'aktiv', 'nature',
    'classic', 'modern', 'vienna', 'lodge', 'inn', 'club',
    'studio', 'suite', 'home', 'dream', 'traum', 'life',
    'time', 'land', 'world', 'park', 'point', 'family',
    'gasthof', 'hotel', 'restaurant', 'cafe', 'almwirtschaft',
    'wirtshaus', 'stube', 'hütte', 'huette', 'gipfel',
    'berg', 'alm', 'see', 'dorf', 'haus', 'hof', 'bad',
    'tal', 'weg', 'stein', 'fels', 'wild', 'hoch', 'tief',
    'kirche', 'burg', 'museum', 'brücke', 'brucke', 'pfad',
    'garten', 'sonne', 'therme', 'spa', 'zentrum', 'center',
    'sankt', 'st.', 'heil', 'welt', 'platz', 'markt',
    'camping', 'dorfer', 'kaser', 'bichl', 'bergkristall',
    'landhaus', 'ferienhaus', 'apartment', 'appartement',
    'neustift', 'fulpmes', 'tulfes', 'ehrwald', 'reutte',
    # Short names that are common in compound contexts
    'anger', 'bach', 'berg', 'bichl', 'bruck', 'buehel',
    'dorf', 'feld', 'graben', 'gries', 'hof', 'leiten',
    'mais', 'moos', 'rain', 'ried', 'rohr', 'schmied',
    'see', 'wald', 'wand', 'wies', 'anger', 'au', 'egg',
}

def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write('\n')

def get_name(entry):
    return entry.get('name') or entry.get('titel') or entry.get('_slug', '')

def get_slug(entry):
    return entry.get('slug') or entry.get('_slug', '')

def get_tags(entry):
    return [str(t).lower().strip() for t in (entry.get('tags') or []) if t]

def link_for(entry):
    path_map = {'orte': '/orte', 'gastro': '/gastro', 'unterkuenfte': '/unterkuenfte', 'erlebnisse': '/erlebnisse'}
    return f'[{get_name(entry)}]({path_map[entry["_type"]]}/{get_slug(entry)}/)'

def build_tag_index(entries):
    idx = {}
    for e in entries:
        for t in get_tags(e):
            idx.setdefault(t, []).append(e)
    return idx

def expand_tags(tags):
    expanded = set()
    for t in tags:
        tl = t.lower().strip()
        expanded.add(tl)
        expanded.update(TAG_MAP.get(tl, []))
    return list(expanded)

def too_generic(entry):
    """Return True if entry name is too generic/short to link."""
    name = get_name(entry).strip()
    
    # Minimum length check
    if len(name) < 5:
        return True
    
    nl = name.lower()
    
    # Blocklisted names (exact match)
    if nl in BLOCKED_NAMES:
        return True
    
    # Single-word names matching generic patterns
    if ' ' not in name:
        if re.match(r'^(gasthof|hotel|restaurant|cafe|alm|berg|stube|hütte|wirtshaus|kirche|burg|museum|park|bad|therme|dorf|haus|hof|see|gipfel|tal|alpen|adler|post|royal|city|vital|sport|lodge|club)$', nl):
            return True
    
    # Names that are just a single common German first name or surname
    common_names = {'anton', 'anna', 'hans', 'sepp', 'franz', 'max', 'peter', 'paul', 'maria', 
                    'thomas', 'simon', 'lisa', 'josef', 'johann', 'andreas', 'michael',
                    'albert', 'rudolf', 'karl', 'heinrich', 'alois', 'fritz'}
    if ' ' not in name and nl in common_names:
        return True
    
    return False

def is_inside_link(text, match_start, match_end):
    """
    Check if a match falls inside an existing Markdown link [...](...).
    Returns True if the match is between an unclosed [ and its closing ](...).
    """
    before = text[:match_start]
    
    # Find the relevant brackets before the match
    last_open_b = before.rfind('[')
    last_close_b = before.rfind(']')
    last_paren_c = before.rfind(')')
    
    # If there's an unclosed '[' after the last ']' and last ')',
    # we're inside the link text portion of [...](...)
    if last_open_b > last_close_b and last_open_b > last_paren_c:
        after = text[match_end:]
        # Check if there's a '](' or '] (' pattern after the match
        next_close = after.find(']')
        if next_close >= 0:
            after_close = after[next_close+1:]
            if after_close.startswith('(') or after_close.startswith(' ('):
                # Look for matching closing paren
                paren_search_start = 1 if after_close.startswith('(') else 2
                after_paren = after_close[paren_search_start:]
                depth = 0
                for i, c in enumerate(after_paren):
                    if c == '(':
                        depth += 1
                    elif c == ')':
                        if depth == 0:
                            return True  # Found matching link pattern
                        depth -= 1
    return False

def find_linkable_occurrences(text, name):
    """Find safe positions to link an entry name, ensuring it's not already linked."""
    if not name or len(name) < 5:
        return []
    
    occurrences = []
    # Word boundary pattern for single-word names
    if ' ' not in name:
        pattern = rf'\b{re.escape(name)}\b'
    else:
        pattern = re.escape(name)
    
    for match in re.finditer(pattern, text):
        start, end = match.start(), match.end()
        
        # 1. Skip if inside existing Markdown link
        if is_inside_link(text, start, end):
            continue
        
        # 2. Skip if preceded by [ (would create [[Name])
        if start > 0 and text[start-1] == '[':
            continue
        
        # 3. For single-word names, verify NOT part of a compound word
        if ' ' not in name:
            if start > 0:
                prev_char = text[start-1]
                if prev_char.isalpha() or prev_char == '-':
                    continue
            if end < len(text):
                next_char = text[end]
                if next_char.isalpha() or next_char == '-':
                    continue
        
        # 4. Context check: ensure the matched text is exactly the name (case-insensitive)
        matched_text = text[start:end]
        if matched_text.lower() != name.lower():
            continue
        
        occurrences.append((start, end))
    
    return occurrences

def score_entry(entry, expanded_tags):
    """Score relevance for linking."""
    score = 0
    tags = get_tags(entry)
    common = set(tags) & set(expanded_tags)
    score += len(common) * 3
    
    type_bonus = {'orte': 2, 'erlebnisse': 2, 'gastro': 1, 'unterkuenfte': 1}
    score += type_bonus.get(entry['_type'], 0)
    
    name = get_name(entry)
    if len(name) > 15: score += 1
    if len(name) > 25: score += 1
    
    if set(tags).issubset({'gastro', 'hotel'}): score -= 2
    
    return score

def main():
    print("=" * 60)
    print("P4a – Cross-Link Blog (v5 FINAL)")
    print("=" * 60)
    
    # 1. Load articles
    print("\n[1] Loading articles...")
    mag_dir = os.path.join(BASE_DIR, 'magazin')
    articles = []
    for slug in sorted(os.listdir(mag_dir)):
        ipath = os.path.join(mag_dir, slug, 'index.json')
        if os.path.isfile(ipath):
            try:
                d = load_json(ipath)
                d['_slug'] = slug
                articles.append(d)
            except: pass
    print(f"  {len(articles)} articles")
    
    # 2. Load reference entries
    print("\n[2] Loading reference entries...")
    all_entries = []
    for etype in ['orte', 'gastro', 'unterkuenfte', 'erlebnisse']:
        d = os.path.join(BASE_DIR, etype)
        if os.path.isdir(d):
            count = 0
            for slug in os.listdir(d):
                ipath = os.path.join(d, slug, 'index.json')
                if os.path.isfile(ipath):
                    try:
                        data = load_json(ipath)
                        data['_type'] = etype
                        data['_slug'] = slug
                        all_entries.append(data)
                        count += 1
                    except: pass
            print(f"  {etype}: {count}")
    print(f"  Total: {len(all_entries)}")
    
    # 3. Build tag index
    print("\n[3] Building tag index...")
    tag_index = build_tag_index(all_entries)
    print(f"  {len(tag_index)} tags")
    
    # 4. Process
    print("\n[4] Processing...")
    total_links = 0
    linked_articles = 0
    skipped = 0
    generic_filtered = 0
    
    for article in articles:
        title = article.get('titel', '?')
        slug = article.get('_slug', '')
        article_tags = get_tags(article)
        inhalt = article.get('inhalt', '')
        
        if not article_tags or not inhalt:
            skipped += 1
            continue
        
        expanded = expand_tags(article_tags)
        matches = []
        seen = set()
        for tag in expanded:
            for entry in tag_index.get(tag, []):
                s = get_slug(entry)
                if s not in seen:
                    matches.append(entry)
                    seen.add(s)
        
        if not matches:
            skipped += 1
            continue
        
        # Score and filter
        scored = [(score_entry(e, expanded), e) for e in matches]
        scored.sort(key=lambda x: -x[0])
        
        linked = 0
        mods = []
        
        for score, entry in scored:
            if linked >= 3:
                break
            
            if too_generic(entry):
                generic_filtered += 1
                continue
            
            name = get_name(entry)
            link = link_for(entry)
            
            occs = find_linkable_occurrences(inhalt, name)
            if occs:
                mods.append((occs[0][0], occs[0][1], link))
                linked += 1
        
        if linked:
            mods.sort(key=lambda x: -x[0])
            for start, end, link in mods:
                inhalt = inhalt[:start] + link + inhalt[end:]
            
            article['inhalt'] = inhalt
            save_json(os.path.join(mag_dir, slug, 'index.json'), article)
            total_links += linked
            linked_articles += 1
            print(f"  OK '{title}': {linked} link(s)")
        else:
            skipped += 1
    
    print(f"\n[5] Summary")
    print(f"  Articles: {linked_articles}/{len(articles)} with links")
    print(f"  Links added: {total_links}")
    print(f"  Skipped: {skipped}")
    print(f"  Generic entries filtered: {generic_filtered}")
    print("=" * 60)

if __name__ == '__main__':
    main()

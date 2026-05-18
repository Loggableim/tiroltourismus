#!/usr/bin/env python3
"""
P4a – Cross-Link Blog zu Orten/Gastro/Unterkünften/Erlebnissen (v4 - FINAL)

For each magazine article:
1. Find entries in orte/gastro/unterkuenfte/erlebnisse with matching tags (fuzzy)
2. Only link if the entry's name appears naturally in the article text
3. NEVER link inside existing Markdown links [...](...)
4. NEVER match names that are substrings of larger German compound words
5. Skip generic/short entry names
6. Max 3 links per article
"""

import json, os, re

BASE_DIR = "F:/tiroltourismus/src/data"

# Tag expansion for articles with non-standard tags
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

# Entry names that are too generic to auto-link
GENERIC_NAMES = {
    'hof', 'berg', 'alm', 'see', 'dorf', 'haus', 'park', 'bad',
    'gasthof', 'hotel', 'restaurant', 'cafe', 'wirtshaus',
    'stube', 'hütte', 'huette', 'gipfel', 'tal', 'kirche',
    'burg', 'museum', 'brücke', 'brucke', 'weg', 'pfad',
    'garten', 'sonne', 'stein', 'fels', 'wild', 'hoch', 'tief',
    'sankt', 'st.', 'therme', 'spa', 'zentrum', 'center',
    'camping', 'gasthof', 'almwirtschaft', 'wirtshaus',
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
    """Return True if entry name is too generic to link."""
    name = get_name(entry).strip()
    if len(name) < 5:
        return True
    nl = name.lower()
    if nl in GENERIC_NAMES:
        return True
    # Single-word names matching generic patterns
    if ' ' not in name:
        if re.match(r'^(gasthof|hotel|restaurant|cafe|alm|berg|stube|hütte|wirtshaus|kirche|burg|museum|park|bad|therme|dorf|haus|hof|see|gipfel|tal)$', nl):
            return True
    return False

def is_inside_existing_link(text, match_start, match_end):
    """
    Check if a text match is inside an existing Markdown link [...](...).
    We scan backwards for an unclosed [ and forwards for matching ] and ).
    """
    # Scan BACKWARDS from match_start
    before = text[:match_start]
    
    # Find the last '[' before the match
    last_open = before.rfind('[')
    last_close = before.rfind(']')
    last_paren_close = before.rfind(')')
    
    # If there's an unclosed '[' (appears after last ']' and last ')'), 
    # we might be inside a link's text portion
    if last_open > last_close and last_open > last_paren_close:
        # There's an open bracket before us - check if it forms a link
        # by looking for ](...) pattern after the match
        after = text[match_end:]
        
        # Find the next ] and subsequent (
        next_close_bracket = after.find(']')
        next_open_paren = after.find('(')
        
        if next_close_bracket >= 0:
            # Check if after ] there's an immediate (
            after_close = after[next_close_bracket+1:]
            if after_close.startswith('('):
                next_close_paren = after_close.find(')')
                if next_close_paren >= 0:
                    return True  # It's [...](...) so we're inside a link
    
    return False

def find_linkable_occurrences(text, name):
    """
    Find all safe positions to link an entry name in the text.
    Returns list of (start, end) tuples.
    """
    if not name or len(name) < 5:
        return []
    
    occurrences = []
    # Use word boundaries for single-word names
    if ' ' not in name:
        pattern = rf'\b{re.escape(name)}\b'
    else:
        pattern = re.escape(name)
    
    for match in re.finditer(pattern, text):
        start, end = match.start(), match.end()
        
        # 1. Check if already inside an existing Markdown link
        if is_inside_existing_link(text, start, end):
            continue
        
        # 2. Check if preceded by [ (would create [[Name] or [Name])
        if start > 0 and text[start-1] == '[':
            continue
        
        # 3. For single-word names, verify they're not part of a compound word
        if ' ' not in name:
            if start > 0:
                prev = text[start-1]
                if prev.isalpha() or prev == '-':
                    continue  # Part of larger word
            if end < len(text):
                nxt = text[end]
                if nxt.isalpha() or nxt == '-':
                    continue  # Part of larger word
        
        # 4. Check we're not inside **bold** markers (partial check)
        before_context = text[max(0, start-5):start]
        after_context = text[end:end+5]
        # If surrounded by ** patterns, skip (links inside bold are fine if not already linked)
        
        occurrences.append((start, end))
    
    return occurrences

def score_entry(entry, expanded_tags):
    """Score how relevant an entry is for linking."""
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
    print("P4a – Cross-Link Blog zu Orten/Gastro/Unterkünften (v4 FINAL)")
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
    print(f"  {len(tag_index)} unique tags")
    
    # 4. Process each article
    print("\n[4] Processing...")
    total_links = 0
    linked_articles = 0
    skipped = 0
    
    for article in articles:
        title = article.get('titel', '?')
        slug = article.get('_slug', '')
        article_tags = get_tags(article)
        inhalt = article.get('inhalt', '')
        
        if not article_tags or not inhalt:
            skipped += 1
            continue
        
        # Find matching entries
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
    print(f"  Articles with links: {linked_articles}/{len(articles)}")
    print(f"  Total links added: {total_links}")
    print(f"  Skipped: {skipped}")
    print("=" * 60)

if __name__ == '__main__':
    main()

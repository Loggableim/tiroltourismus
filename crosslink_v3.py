#!/usr/bin/env python3
"""
P4a – Cross-Link Blog zu Orten/Gastro/Unterkünften/Erlebnissen (v3)

Strict quality approach:
1. Build tag index (with fuzzy matching for article tags)
2. Find best matching entries (max 3 per article)
3. ONLY link if entry name appears as a standalone word/phrase in text
4. No false matches (skip common words, short names, substrings)
5. No fallback insertion - only replace existing text
"""

import json
import os
import re
import unicodedata

BASE_DIR = "F:/tiroltourismus/src/data"

# Tag expansion for fuzzy matching
TAG_SIMILARITY_MAP = {
    'wanderwege': ['wandern', 'wanderweg'],
    'leichte touren': ['wandern'],
    'panorama': ['berg', 'aussicht'],
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

# Common German words that should never be auto-linked even if they match entry names
COMMON_WORDS = {
    'hof', 'berg', 'alm', 'see', 'dorf', 'haus', 'park', 'bad', 'gasthof',
    'hotel', 'restaurant', 'cafe', 'wirtshaus', 'almwirtschaft', 'gasthof',
    'stube', 'stuben', 'hütte', 'huette', 'gipfel', 'tal', 'wasserfall',
    'kirche', 'burg', 'museum', 'brücke', 'brucke', 'weg', 'pfad',
    'garten', 'blume', 'sonne', 'mond', 'stern', 'stein', 'fels',
    'wild', 'hoch', 'tief', 'lang', 'kurz', 'neu', 'alt',
    'sankt', 'st.', 'bad', 'therme', 'spa', 'zentrum', 'center',
}

# Also skip single-word entries that are too generic by checking if they exist as standalone
# words in the German language (rough check via length + common patterns)

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
    tags = entry.get('tags', [])
    if not tags:
        return []
    return [str(t).lower().strip() for t in tags if t]

def get_link_path(entry_type):
    path_map = {'orte': '/orte', 'gastro': '/gastro', 'unterkuenfte': '/unterkuenfte', 'erlebnisse': '/erlebnisse'}
    return path_map.get(entry_type, f'/{entry_type}')

def make_link(entry):
    return f'[{get_name(entry)}]({get_link_path(entry["_type"])}/{get_slug(entry)}/)'

def build_tag_index(entries):
    tag_index = {}
    for entry in entries:
        for tag in get_tags(entry):
            tag_index.setdefault(tag, []).append(entry)
    return tag_index

def expand_tags(article_tags):
    expanded = set()
    for tag in article_tags:
        tag_lower = tag.lower().strip()
        expanded.add(tag_lower)
        for similar in TAG_SIMILARITY_MAP.get(tag_lower, []):
            expanded.add(similar)
    return list(expanded)

def is_entry_too_generic(entry):
    """Check if an entry name is too generic/common to auto-link."""
    name = get_name(entry).strip()
    if len(name) < 5:
        return True
    name_lower = name.lower()
    if name_lower in COMMON_WORDS:
        return True
    # Single-word entries that are common nouns
    if ' ' not in name and len(name.split()) == 1:
        if name_lower in COMMON_WORDS:
            return True
        # Skip single-word entries that match dictionary patterns
        single_word_patterns = [
            r'^(gasthof|hotel|restaurant|cafe|alm|berg)$',
            r'^(stube|huette|hütte|wirtshaus|kirche|burg)$',
            r'^(museum|park|bad|therme|zentrum|center)$',
            r'^(dorf|haus|hof|stein|fels|gipfel|tal)$',
            r'^(see|bach|fluss|wasserfall|brucke|brücke)$',
        ]
        for pat in single_word_patterns:
            if re.match(pat, name_lower):
                return True
    return False

def find_safe_name_occurrences(text, name):
    """
    Find occurrences of entry name in text where:
    - It's a standalone word/phrase (not part of a larger word)
    - It's not already inside a Markdown link
    - The match is of sufficient quality
    """
    if not name or len(name) < 5:
        return []
    
    occurrences = []
    escaped = re.escape(name)
    
    # Use word-boundary-aware matching
    # For multi-word names, look for the phrase as-is
    # For single-word names, ensure word boundaries
    pattern = rf'\b{escaped}\b' if ' ' not in name else re.escape(name)
    
    for match in re.finditer(pattern, text):
        start, end = match.start(), match.end()
        
        # Get surrounding context
        before = text[max(0, start-20):start]
        after = text[end:end+20]
        
        # Skip if already inside a Markdown link [...](...)
        # Check if we're after an unclosed [ before a ]
        text_before_full = text[max(0, start-200):start]
        last_bracket_open = text_before_full.rfind('[')
        last_bracket_close = text_before_full.rfind(']')
        last_paren_open = text_before_full.rfind('(')
        
        if last_bracket_open > last_bracket_close:
            # We're inside [ ... ] - could be link text
            # Only skip if there's a matching ) after
            text_after_full = text[end:end+200]
            next_paren_close = text_after_full.find(')')
            next_bracket_close = text_after_full.find(']')
            if next_paren_close >= 0 and (next_bracket_close < 0 or next_paren_close < next_bracket_close):
                # This looks like it's inside a Markdown link
                continue
        
        # Skip if preceded by [ (already linked)
        if start > 0 and text[start-1] == '[':
            continue
        
        # Skip if part of a larger compound word (German compounds)
        # e.g., "Hof" in "Gasthof" or "Berg" in "Bergsee"
        if ' ' not in name:
            # Check character before match
            if start > 0:
                prev_char = text[start-1]
                if prev_char.isalpha() or prev_char == '-':
                    # Name is part of a larger word
                    continue
            # Check character after match
            if end < len(text):
                next_char = text[end]
                if next_char.isalpha() or next_char == '-':
                    continue
        
        occurrences.append((start, end, match.group()))
    
    return occurrences

def find_matching_entries(article_tags, tag_index):
    """Find entries with tag overlap."""
    expanded_tags = expand_tags(article_tags)
    matches = []
    seen_slugs = set()
    
    for tag in expanded_tags:
        if tag in tag_index:
            for entry in tag_index[tag]:
                slug = get_slug(entry)
                if slug not in seen_slugs:
                    matches.append(entry)
                    seen_slugs.add(slug)
    return matches

def score_entry(entry, article_tags, expanded_tags):
    """Score relevance for linking."""
    score = 0
    name = get_name(entry)
    tags = get_tags(entry)
    
    # Higher score for more shared tags
    common = set(tags) & set(expanded_tags)
    score += len(common) * 3
    
    # Prefer orte and erlebnisse
    type_bonus = {'orte': 2, 'erlebnisse': 2, 'gastro': 1, 'unterkuenfte': 1}
    score += type_bonus.get(entry['_type'], 0)
    
    # Prefer longer/more descriptive names (likely more specific)
    if len(name) > 15:
        score += 1
    if len(name) > 25:
        score += 1
    
    # Penalize entries with only generic tags
    if set(tags).issubset({'gastro', 'hotel', 'restaurant'}):
        score -= 2
    
    return score

def main():
    print("=" * 60)
    print("P4a – Cross-Link Blog zu Orten/Gastro/Unterkünften (v3)")
    print("=" * 60)
    
    # Load articles
    print("\n[1] Loading magazine articles...")
    magazin_dir = os.path.join(BASE_DIR, 'magazin')
    articles = []
    for slug in sorted(os.listdir(magazin_dir)):
        ipath = os.path.join(magazin_dir, slug, 'index.json')
        if os.path.isfile(ipath):
            try:
                data = load_json(ipath)
                data['_slug'] = slug
                articles.append(data)
            except Exception as e:
                print(f"  Warning: {e}")
    print(f"  Loaded {len(articles)} articles")
    
    # Load reference entries
    print("\n[2] Loading reference entries...")
    all_entries = []
    for etype in ['orte', 'gastro', 'unterkuenfte', 'erlebnisse']:
        directory = os.path.join(BASE_DIR, etype)
        if os.path.isdir(directory):
            count = 0
            for slug in os.listdir(directory):
                ipath = os.path.join(directory, slug, 'index.json')
                if os.path.isfile(ipath):
                    try:
                        data = load_json(ipath)
                        data['_type'] = etype
                        data['_slug'] = slug
                        all_entries.append(data)
                        count += 1
                    except:
                        pass
            print(f"  {etype}: {count} entries")
    print(f"  Total: {len(all_entries)} entries")
    
    # Build tag index
    print("\n[3] Building tag index...")
    tag_index = build_tag_index(all_entries)
    print(f"  Unique tags: {len(tag_index)}")
    
    # Process articles
    print("\n[4] Processing articles...")
    total_links_added = 0
    articles_with_links = 0
    articles_skipped = 0
    false_matches_caught = 0
    
    for article in articles:
        title = article.get('titel', 'Untitled')
        slug = article.get('_slug', '')
        article_tags = get_tags(article)
        inhalt = article.get('inhalt', '')
        
        if not article_tags or not inhalt:
            print(f"  SKIP '{title}': No tags or content")
            articles_skipped += 1
            continue
        
        # Find matching entries
        matches = find_matching_entries(article_tags, tag_index)
        if not matches:
            print(f"  SKIP '{title}': No tag matches")
            articles_skipped += 1
            continue
        
        # Score and filter
        expanded_tags = expand_tags(article_tags)
        scored = [(score_entry(e, article_tags, expanded_tags), e) for e in matches]
        scored.sort(key=lambda x: -x[0])
        
        # Try top candidates until we find names in text (max 3 links)
        links_this = 0
        modifications = []
        
        for score, entry in scored:
            if links_this >= 3:
                break
            
            name = get_name(entry)
            
            # Skip generic entries
            if is_entry_too_generic(entry):
                false_matches_caught += 1
                continue
            
            occurrences = find_safe_name_occurrences(inhalt, name)
            
            if occurrences:
                start, end, matched = occurrences[0]
                link_md = make_link(entry)
                modifications.append((start, end, link_md))
                links_this += 1
        
        if links_this > 0:
            # Apply in reverse order
            modifications.sort(key=lambda x: -x[0])
            for start, end, link_md in modifications:
                inhalt = inhalt[:start] + link_md + inhalt[end:]
            
            article['inhalt'] = inhalt
            save_json(os.path.join(magazin_dir, slug, 'index.json'), article)
            total_links_added += links_this
            articles_with_links += 1
            print(f"  OK '{title}': {links_this} link(s)")
        else:
            print(f"  SKIP '{title}': Names not in text")
            articles_skipped += 1
    
    print(f"\n[5] Summary")
    print(f"  Articles with links: {articles_with_links}/{len(articles)}")
    print(f"  Total links added: {total_links_added}")
    print(f"  Skipped: {articles_skipped}")
    print(f"  Generic entries filtered: {false_matches_caught}")
    print("=" * 60)

if __name__ == '__main__':
    main()

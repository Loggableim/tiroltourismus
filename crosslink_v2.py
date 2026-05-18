#!/usr/bin/env python3
"""
P4a – Cross-Link Blog zu Orten/Gastro/Unterkünften/Erlebnissen (v2)

Quality approach:
1. Build tag index from all orte/gastro/unterkuenfte/erlebnisse entries
2. For each article, find entries sharing at least one tag (with fuzzy matching)
3. For candidate entries, check if their name appears naturally in the inhalt text
4. Only insert links where the name is found - replace plain text with [Name](/type/slug/)
5. Max 3 links per article, skip if name not found
6. No artificial "mehr unter" phrases - links must feel natural
"""

import json
import os
import re
import sys
from difflib import get_close_matches

BASE_DIR = "F:/tiroltourismus/src/data"

# Tag mapping for fuzzy matching: broad tags in articles -> specific tags in reference entries
TAG_SIMILARITY_MAP = {
    'wanderwege': ['wandern', 'wanderweg', 'wanderungen'],
    'leichte touren': ['wandern', 'wanderweg'],
    'panorama': ['berg', 'aussicht'],
    'almen': ['alm', 'hütte'],
    'genusswandern': ['wandern', 'genuss', 'alm'],
    'einkehren': ['alm', 'hütte', 'gastro'],
    'almwirtschaft': ['alm', 'hütte'],
    'tirol': [],  # too generic
    'skigebiete': ['ski'],
    'pisten': ['ski'],
    'schneesicherheit': ['ski', 'winter'],
    'winterurlaub': ['ski', 'winter', 'schnee'],
    'hotels': ['hotel', 'unterkunft'],
    'aktivitäten': ['aktivurlaub', 'outdoor', 'sport'],
    'kinder': ['familie', 'kids'],
    'almhütten': ['alm', 'hütte'],
    'geniesserwanderung': ['wandern', 'genuss'],
    'familien-skigebiete': ['familie', 'ski', 'kinder'],
    'kinderpisten': ['familie', 'ski', 'kinder'],
}

GENERIC_TAGS = {'gastro', 'hotel', 'tirol', 'aktivurlaub', 'outdoor', 'natur', 'sommer', 'winter', 'urlaub'}

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
    path_map = {
        'orte': '/orte',
        'gastro': '/gastro',
        'unterkuenfte': '/unterkuenfte',
        'erlebnisse': '/erlebnisse',
    }
    return path_map.get(entry_type, f'/{entry_type}')

def make_link(entry):
    name = get_name(entry)
    slug = get_slug(entry)
    link_path = get_link_path(entry['_type'])
    return f'[{name}]({link_path}/{slug}/)'

def build_tag_index(entries):
    tag_index = {}
    for entry in entries:
        tags = get_tags(entry)
        for tag in tags:
            if tag not in tag_index:
                tag_index[tag] = []
            tag_index[tag].append(entry)
    return tag_index

def expand_tags(article_tags):
    """Expand article tags with fuzzy/similar tags."""
    expanded = set()
    for tag in article_tags:
        tag_lower = tag.lower().strip()
        expanded.add(tag_lower)
        # Check similarity map
        if tag_lower in TAG_SIMILARITY_MAP:
            for similar in TAG_SIMILARITY_MAP[tag_lower]:
                expanded.add(similar)
    return list(expanded)

def find_matching_entries(article_tags, tag_index):
    """Find entries that share tags with the article using expanded matching."""
    matches = []
    seen_slugs = set()
    
    expanded_tags = expand_tags(article_tags)
    
    for tag in expanded_tags:
        if tag in tag_index:
            for entry in tag_index[tag]:
                slug = get_slug(entry)
                if slug not in seen_slugs:
                    matches.append(entry)
                    seen_slugs.add(slug)
    
    return matches

def score_entry(entry, article_tags, all_article_tags_expanded):
    """Score relevance of entry for linking."""
    score = 0
    tags = get_tags(entry)
    entry_tags_set = set(tags)
    article_tags_set = set(all_article_tags_expanded)
    
    common = entry_tags_set & article_tags_set
    score += len(common) * 3
    
    # Bonus for non-generic tags
    specific_common = [t for t in common if t not in GENERIC_TAGS]
    score += len(specific_common) * 2
    
    # Bonus for entries with descriptions
    desc = entry.get('beschreibung', '') or entry.get('kurzbeschreibung', '') or ''
    if len(desc) > 50:
        score += 1
    
    # Penalize generic entries
    if tags == ['gastro'] or tags == ['hotel'] or not tags:
        score -= 2
    
    # Prefer orte and erlebnisse over gastro/unterkuenfte (more interesting for readers)
    type_bonus = {'orte': 2, 'erlebnisse': 2, 'gastro': 1, 'unterkuenfte': 1}
    score += type_bonus.get(entry['_type'], 0)
    
    return score

def find_name_occurrences(text, name):
    """Find all occurrences of an entry name in text, skipping already-linked ones."""
    occurrences = []
    escaped = re.escape(name)
    for match in re.finditer(escaped, text, re.IGNORECASE):
        start, end = match.start(), match.end()
        matched_text = match.group()
        
        # Check if already linked - look for [Text](...) pattern
        before = text[max(0, start-1):start]
        after = text[end:end+1]
        
        # Skip if already part of a link
        if before == '[' and after == ']':
            continue
        
        # Also check if we're inside an existing [...]() link
        # Look backwards for unclosed [
        text_before = text[max(0, start-50):start]
        link_open = text_before.rfind('[')
        link_close = text_before.rfind(']')
        paren_start = text_before.rfind('(')
        
        if link_open > link_close and paren_start > link_open:
            continue
        
        occurrences.append((start, end, matched_text))
    
    return occurrences

def main():
    print("=" * 60)
    print("P4a – Cross-Link Blog zu Orten/Gastro/Unterkünften (v2)")
    print("=" * 60)
    
    # Step 1: Load magazine articles
    print("\n[1] Loading magazine articles...")
    magazin_dir = os.path.join(BASE_DIR, 'magazin')
    articles = []
    for slug in sorted(os.listdir(magazin_dir)):
        index_path = os.path.join(magazin_dir, slug, 'index.json')
        if os.path.isfile(index_path):
            try:
                data = load_json(index_path)
                data['_slug'] = slug
                articles.append(data)
            except Exception as e:
                print(f"  Warning: Could not load {index_path}: {e}")
    print(f"  Loaded {len(articles)} articles")
    
    # Step 2: Load reference entries
    print("\n[2] Loading reference entries...")
    all_entries = []
    for entry_type in ['orte', 'gastro', 'unterkuenfte', 'erlebnisse']:
        directory = os.path.join(BASE_DIR, entry_type)
        entries = []
        if os.path.isdir(directory):
            for slug in os.listdir(directory):
                index_path = os.path.join(directory, slug, 'index.json')
                if os.path.isfile(index_path):
                    try:
                        data = load_json(index_path)
                        data['_type'] = entry_type
                        data['_slug'] = slug
                        entries.append(data)
                    except Exception as e:
                        pass  # skip malformed entries
        print(f"  {entry_type}: {len(entries)} entries")
        all_entries.extend(entries)
    print(f"  Total: {len(all_entries)} entries")
    
    # Step 3: Build tag index
    print("\n[3] Building tag index...")
    tag_index = build_tag_index(all_entries)
    print(f"  Unique tags: {len(tag_index)}")
    
    # Step 4: Process articles
    print("\n[4] Processing articles...")
    total_links_added = 0
    articles_with_links = 0
    articles_skipped_no_match = 0
    articles_skipped_no_name = 0
    
    for article in articles:
        title = article.get('titel', 'Untitled')
        slug = article.get('_slug', '')
        article_tags = get_tags(article)
        inhalt = article.get('inhalt', '')
        
        if not article_tags:
            print(f"  SKIP '{title}': No tags")
            articles_skipped_no_match += 1
            continue
        
        if not inhalt:
            print(f"  SKIP '{title}': No content")
            articles_skipped_no_match += 1
            continue
        
        # Find matching entries
        matches = find_matching_entries(article_tags, tag_index)
        
        if not matches:
            print(f"  SKIP '{title}': No matching entries (tags: {article_tags})")
            articles_skipped_no_match += 1
            continue
        
        # Score entries
        expanded_tags = expand_tags(article_tags)
        scored_entries = []
        for entry in matches:
            score = score_entry(entry, article_tags, expanded_tags)
            scored_entries.append((score, entry))
        
        scored_entries.sort(key=lambda x: -x[0])
        
        # Now try to link: iterate through best entries, find name in text
        links_this_article = 0
        modifications = []  # (start, end, link_md) in order of appearance
        
        for score, entry in scored_entries:
            if links_this_article >= 3:
                break
            
            name = get_name(entry)
            if not name:
                continue
            
            # Skip very short names that might match accidentally (< 3 chars)
            if len(name.strip()) < 3:
                continue
            
            link_md = make_link(entry)
            occurrences = find_name_occurrences(inhalt, name)
            
            if occurrences:
                # Use the first (leftmost) occurrence
                pos = occurrences[0]
                start, end, matched = pos
                
                modifications.append((start, end, link_md))
                links_this_article += 1
        
        if links_this_article > 0:
            # Apply modifications in reverse order (to preserve positions)
            modifications.sort(key=lambda x: -x[0])
            for start, end, link_md in modifications:
                inhalt = inhalt[:start] + link_md + inhalt[end:]
            
            article['inhalt'] = inhalt
            index_path = os.path.join(magazin_dir, slug, 'index.json')
            save_json(index_path, article)
            total_links_added += links_this_article
            articles_with_links += 1
            print(f"  OK '{title}': Added {links_this_article} link(s)")
        else:
            print(f"  SKIP '{title}': Found matching entries but names not in text")
            articles_skipped_no_name += 1
    
    print(f"\n[5] Summary")
    print(f"  Articles processed: {len(articles)}")
    print(f"  Articles with links: {articles_with_links}")
    print(f"  Total links added: {total_links_added}")
    print(f"  Skipped (no tag match): {articles_skipped_no_match}")
    print(f"  Skipped (name not in text): {articles_skipped_no_name}")
    print("=" * 60)

if __name__ == '__main__':
    main()

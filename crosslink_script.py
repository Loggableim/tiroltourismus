#!/usr/bin/env python3
"""
P4a – Cross-Link Blog zu Orten/Gastro/Unterkünften/Erlebnissen

For each magazine article:
1. Check if there are entries in /orte/, /gastro/, /unterkuenfte/, /erlebnisse/ with matching tags
2. If a tag match exists, insert a natural link in 'inhalt' (Markdown)
3. Max 3 links per article, only where thematically appropriate
"""

import json
import os
import re
import sys

BASE_DIR = "F:/tiroltourismus/src/data"

def load_json(path):
    """Load a JSON file."""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(path, data):
    """Save a JSON file with pretty formatting."""
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_all_entries(directory, entry_type):
    """Load all index.json files from a directory of entries."""
    entries = []
    if not os.path.isdir(directory):
        return entries
    for slug in os.listdir(directory):
        index_path = os.path.join(directory, slug, 'index.json')
        if os.path.isfile(index_path):
            try:
                data = load_json(index_path)
                data['_type'] = entry_type
                data['_slug'] = slug
                entries.append(data)
            except (json.JSONDecodeError, KeyError) as e:
                print(f"  Warning: Could not load {index_path}: {e}")
    return entries

def get_name(entry):
    """Get the display name from an entry."""
    return entry.get('name') or entry.get('titel') or entry.get('_slug', '')

def get_slug(entry):
    """Get the slug for linking."""
    return entry.get('slug') or entry.get('_slug', '')

def get_tags(entry):
    """Get normalized tags from an entry."""
    tags = entry.get('tags', [])
    if not tags:
        return []
    # Normalize: lowercase and strip
    return [str(t).lower().strip() for t in tags if t]

def get_link_type(entry_type):
    """Get the URL path prefix for an entry type."""
    type_map = {
        'orte': '/orte',
        'gastro': '/gastro',
        'unterkuenfte': '/unterkuenfte',
        'erlebnisse': '/erlebnisse',
    }
    return type_map.get(entry_type, f'/{entry_type}')

def make_link(entry):
    """Create a Markdown link string for an entry."""
    name = get_name(entry)
    slug = get_slug(entry)
    link_type = get_link_type(entry['_type'])
    return f'[{name}]({link_type}/{slug}/)'

def find_link_positions(text, entry_name):
    """Find positions where a link could be inserted naturally.
    Returns list of (start, end, match_text) tuples sorted by position."""
    positions = []
    # Escape special regex characters in the name
    escaped = re.escape(entry_name)
    for match in re.finditer(escaped, text, re.IGNORECASE):
        positions.append((match.start(), match.end(), match.group()))
    return positions

def insert_link_at(text, pos, entry_name, link_md):
    """Insert a link at a specific position, replacing the plain name.
    Returns updated text."""
    start, end, match_text = pos
    # Check if already linked (surrounded by [...]())
    before = text[max(0, start-1):start]
    after = text[end:end+1]
    if before == '[' and after == ']':
        return text  # Already part of a link
    
    # Replace the matched text with the link
    new_text = text[:start] + link_md + text[end:]
    return new_text

def build_tag_index(entries):
    """Build a mapping from tag to list of entries."""
    tag_index = {}
    for entry in entries:
        tags = get_tags(entry)
        for tag in tags:
            if tag not in tag_index:
                tag_index[tag] = []
            tag_index[tag].append(entry)
    return tag_index

def find_matching_entries(article_tags, tag_index):
    """Find entries that share at least one tag with the article.
    Returns dict mapping tag to list of (entry, shared_tag) tuples."""
    matches = []
    seen_slugs = set()
    
    for tag in article_tags:
        normalized_tag = tag.lower().strip()
        if normalized_tag in tag_index:
            for entry in tag_index[normalized_tag]:
                slug = get_slug(entry)
                if slug not in seen_slugs:
                    # Also check that the shared tag is meaningful (not too generic)
                    matches.append((entry, normalized_tag))
                    seen_slugs.add(slug)
    
    return matches

# Tags that are too generic to use for cross-linking
GENERIC_TAGS = {'gastro', 'hotel', 'tirol', 'aktivurlaub', 'outdoor', 'natur', 'sommer', 'winter', 'familie'}

def score_entry_relevance(entry, article_tags, shared_tag):
    """Score how relevant an entry is for linking in this article."""
    score = 0
    name = get_name(entry)
    tags = get_tags(entry)
    
    # Prefer entries where the shared tag is a region or specific topic
    shared_tag_lower = shared_tag.lower()
    if shared_tag_lower not in GENERIC_TAGS:
        score += 2
    
    # More shared tags = better match
    common = set(tags) & set(article_tags)
    score += len(common)
    
    # Prefer entries with more detailed info (longer description)
    desc = entry.get('beschreibung', '') or entry.get('kurzbeschreibung', '') or ''
    if len(desc) > 50:
        score += 1
    
    return score

def main():
    print("=" * 60)
    print("P4a – Cross-Link Blog zu Orten/Gastro/Unterkünften")
    print("=" * 60)
    
    # Step 1: Load all magazine articles
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
            except (json.JSONDecodeError, KeyError) as e:
                print(f"  Warning: Could not load {index_path}: {e}")
    print(f"  Loaded {len(articles)} articles")
    
    # Step 2: Load all entries from orte, gastro, unterkuenfte, erlebnisse
    print("\n[2] Loading reference entries...")
    all_entries = []
    for entry_type in ['orte', 'gastro', 'unterkuenfte', 'erlebnisse']:
        directory = os.path.join(BASE_DIR, entry_type)
        entries = load_all_entries(directory, entry_type)
        print(f"  {entry_type}: {len(entries)} entries")
        all_entries.extend(entries)
    print(f"  Total: {len(all_entries)} entries")
    
    # Step 3: Build tag index
    print("\n[3] Building tag index...")
    tag_index = build_tag_index(all_entries)
    print(f"  Tags indexed: {len(tag_index)}")
    
    # Step 4: Process each article
    print("\n[4] Processing articles for cross-linking...")
    total_links_added = 0
    articles_with_links = 0
    
    for article in articles:
        title = article.get('titel', 'Untitled')
        slug = article.get('_slug', '')
        article_tags = get_tags(article)
        
        if not article_tags:
            print(f"  SKIP '{title}': No tags")
            continue
        
        # Find matching entries
        matches = find_matching_entries(article_tags, tag_index)
        
        if not matches:
            print(f"  SKIP '{title}': No matching entries found")
            continue
        
        # Score and sort matches
        scored = []
        for entry, shared_tag in matches:
            score = score_entry_relevance(entry, article_tags, shared_tag)
            scored.append((score, entry, shared_tag))
        
        scored.sort(key=lambda x: -x[0])
        
        # Select top entries (max 3)
        top_entries = scored[:3]
        
        # Now try to insert links
        inhalt = article.get('inhalt', '')
        if not inhalt:
            print(f"  SKIP '{title}': No content")
            continue
        
        links_added = 0
        modifications = []
        
        for score, entry, shared_tag in top_entries:
            if links_added >= 3:
                break
            
            name = get_name(entry)
            link_md = make_link(entry)
            
            # Find occurrences of the entry name in the content
            positions = find_link_positions(inhalt, name)
            
            if positions:
                # Use the first occurrence that's not already linked
                for pos in positions:
                    start, end, match_text = pos
                    # Skip if there's already a link next to it
                    before = inhalt[max(0, start-1):start]
                    after = inhalt[end:end+1]
                    if before == '[' and after == ']':
                        continue
                    modifications.append((start, end, match_text, link_md))
                    links_added += 1
                    break
        
        if links_added == 0:
            # Try a different approach: just insert at the end of a relevant paragraph
            # Look for sentences/paragraphs mentioning the tag
            for score, entry, shared_tag in top_entries[:3]:
                if links_added >= 3:
                    break
                
                name = get_name(entry)
                link_md = make_link(entry)
                
                # Check if the shared tag appears in the content
                tag = shared_tag.lower()
                tag_positions = find_link_positions(inhalt.lower(), tag)
                
                if tag_positions:
                    # Insert near a tag mention
                    for tag_start, tag_end, _ in tag_positions:
                        # Check nearby text (within 200 chars after)
                        nearby = inhalt[tag_end:tag_end+200]
                        # Find end of sentence or paragraph
                        sentence_end = re.search(r'[.!?]\s', nearby)
                        para_end = re.search(r'\n\n', nearby)
                        insert_at = tag_end
                        if sentence_end:
                            insert_at = tag_end + sentence_end.end()
                        elif para_end:
                            insert_at = tag_end + para_end.end()
                        else:
                            insert_at = tag_end + len(nearby)
                        
                        # Insert at the end of the sentence/paragraph
                        # Only if not already linking something
                        link_sentence = f" Entdecken Sie mehr unter {link_md}."
                        inhalt = inhalt[:insert_at] + link_sentence + inhalt[insert_at:]
                        links_added += 1
                        break
                else:
                    # Last resort: mention the place at the end of the article
                    link_sentence = f"\n\nMehr zum Thema finden Sie mit {link_md}."
                    inhalt += link_sentence
                    links_added += 1
        
        if links_added > 0:
            # Apply modifications from first approach
            if modifications:
                # Sort in reverse order to preserve positions
                modifications.sort(key=lambda x: -x[0])
                for start, end, match_text, link_md in modifications:
                    inhalt = inhalt[:start] + link_md + inhalt[end:]
            
            # Save the updated article
            article['inhalt'] = inhalt
            index_path = os.path.join(magazin_dir, slug, 'index.json')
            save_json(index_path, article)
            total_links_added += links_added
            articles_with_links += 1
            print(f"  OK '{title}': Added {links_added} link(s)")
        else:
            print(f"  SKIP '{title}': Could not place links naturally")
    
    print(f"\n[5] Summary")
    print(f"  Articles processed: {len(articles)}")
    print(f"  Articles with links added: {articles_with_links}")
    print(f"  Total links added: {total_links_added}")
    print("=" * 60)

if __name__ == '__main__':
    main()

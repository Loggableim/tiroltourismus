#!/usr/bin/env python3
"""Clean HTML tags from FR gastro kurzbeschreibung fields."""
import json, os, re, sys

FR_DIR = "src/data/fr/gastro"
DE_DIR = "src/data/gastro"

def remove_html_tags(text):
    """Remove HTML tags like <h1>, <h2>, <p> etc., keeping content."""
    if not text:
        return text
    # Remove common block-level tags but keep content
    text = re.sub(r'</?(?:h[1-6]|p|div|span|b|i|u|strong|em|br|hr)(?:\s[^>]*)?>', '', text)
    # Remove stray self-closing tags
    text = re.sub(r'<[^>]+>', '', text)
    # Clean up double spaces/newlines from tag removal
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)
    return text.strip()

fixed = 0
total = 0
has_html = 0

for slug in sorted(os.listdir(FR_DIR)):
    fp = os.path.join(FR_DIR, slug, "index.json")
    if not os.path.exists(fp):
        continue
    total += 1
    with open(fp, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    original = data.get('kurzbeschreibung', '')
    cleaned = remove_html_tags(original)
    
    if original != cleaned:
        data['kurzbeschreibung'] = cleaned
        with open(fp, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        fixed += 1
        if '<' in original:
            has_html += 1

print(f"FR gastro: {total} Einträge geprüft")
print(f"  Bereinigt (HTML-Tags entfernt): {fixed}")
print(f"  Davon mit HTML-Tags: {has_html}")
print(f"  Unverändert (keine HTML): {total - has_html}")

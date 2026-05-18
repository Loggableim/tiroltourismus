#!/usr/bin/env python3
"""
add_image_fields.py — Fügt 'bilder' und 'hero_bild' Felder zu allen index.json-Einträgen hinzu
und legt die public/images/-Ordnerstruktur für die Bilderverwaltung an.

Verwendung:
  python scripts/add_image_fields.py

Was passiert:
  1. Allen index.json-Einträgen (in src/data/*/) werden leere Felder hinzugefügt:
     "bilder": []
     "hero_bild": null
  2. public/images/{collection}/{slug}/.gitkeep und slug.json werden angelegt
  3. Bestehende Felder werden NICHT überschrieben

Danach kann man einfach .webp Dateien ins Verzeichnis legen und
hero_bild: '/images/unterkuenfte/hotel-xyz/hero.webp' setzen.
"""

import json
import os
import sys

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_DIR, 'src', 'data')
PUBLIC_IMAGES_DIR = os.path.join(PROJECT_DIR, 'public', 'images')

# Alle Collections, die index.json-Einträge haben können
COLLECTIONS = [
    'regionen',
    'unterkuenfte',
    'gastro',
    'orte',
    'sehenswuerdigkeiten',
    'magazin',
    'erlebnisse',
    'events',
]


def find_index_files(data_dir):
    """Findet alle index.json Dateien in den Collections."""
    files = []
    for collection in COLLECTIONS:
        coll_dir = os.path.join(data_dir, collection)
        if not os.path.isdir(coll_dir):
            continue
        for slug_dir in sorted(os.listdir(coll_dir)):
            slug_path = os.path.join(coll_dir, slug_dir)
            if not os.path.isdir(slug_path):
                continue
            index_path = os.path.join(slug_path, 'index.json')
            if os.path.isfile(index_path):
                files.append((collection, slug_dir, index_path))
    return files


def add_image_fields(entry, collection, slug):
    """Fügt bilder/hero_bild Felder hinzu, falls nicht vorhanden."""
    changed = False
    if 'bilder' not in entry:
        entry['bilder'] = []
        changed = True
    if 'hero_bild' not in entry:
        entry['hero_bild'] = None
        changed = True
    return changed


def ensure_image_dir(collection, slug):
    """Erstellt public/images/{collection}/{slug}/ mit .gitkeep und slug.json."""
    img_dir = os.path.join(PUBLIC_IMAGES_DIR, collection, slug)
    os.makedirs(img_dir, exist_ok=True)

    # .gitkeep damit leere Ordner in git erhalten bleiben
    gitkeep = os.path.join(img_dir, '.gitkeep')
    if not os.path.exists(gitkeep):
        with open(gitkeep, 'w') as f:
            f.write('')

    # slug.json als Platzhalter/Metadaten
    slug_json = os.path.join(img_dir, 'slug.json')
    if not os.path.exists(slug_json):
        meta = {
            "collection": collection,
            "slug": slug,
            "hinweis": "Lege .webp Dateien in dieses Verzeichnis und setze hero_bild in der index.json",
            "hero": "hero.webp",
            "bilder": []
        }
        with open(slug_json, 'w', encoding='utf-8') as f:
            json.dump(meta, f, indent=2, ensure_ascii=False)
            f.write('\n')


def main():
    index_files = find_index_files(DATA_DIR)
    total = len(index_files)
    updated = 0
    errors = 0
    image_dirs_created = 0

    print(f"🔍 Gefundene index.json Einträge: {total}")
    print()

    for collection, slug, path in index_files:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                entry = json.load(f)

            changed = add_image_fields(entry, collection, slug)

            if changed:
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(entry, f, indent=2, ensure_ascii=False)
                    f.write('\n')
                updated += 1

            # Image-Verzeichnis anlegen
            ensure_image_dir(collection, slug)
            image_dirs_created += 1

            if changed:
                print(f"  ✓ {collection}/{slug} — Felder hinzugefügt")

        except json.JSONDecodeError as e:
            print(f"  ✗ {collection}/{slug} — JSON-Fehler: {e}")
            errors += 1
        except Exception as e:
            print(f"  ✗ {collection}/{slug} — Fehler: {e}")
            errors += 1

    print()
    print(f"✅ Fertig!")
    print(f"   Aktualisierte index.json Dateien: {updated} von {total}")
    print(f"   Angelegte Image-Verzeichnisse:    {image_dirs_created}")
    print(f"   Fehler:                          {errors}")
    print()

    # Zusammenfassung pro Collection
    print("📊 Verteilung:")
    for collection in COLLECTIONS:
        coll_dir = os.path.join(DATA_DIR, collection)
        if os.path.isdir(coll_dir):
            count = len([d for d in os.listdir(coll_dir)
                        if os.path.isdir(os.path.join(coll_dir, d))])
            img_dir = os.path.join(PUBLIC_IMAGES_DIR, collection)
            dirs = 0
            if os.path.isdir(img_dir):
                dirs = len([d for d in os.listdir(img_dir)
                           if os.path.isdir(os.path.join(img_dir, d))])
            print(f"   {collection:20s} → {count:4d} Einträge, {dirs:4d} Image-Ordner")


if __name__ == '__main__':
    main()

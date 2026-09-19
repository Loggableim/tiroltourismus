#!/usr/bin/env python3
"""
translate_homepage.py — Übersetzt die homepage.json in alle Zielsprachen.

Quelle: src/data/homepage.json (DE)
Ziel:   src/data/<lang>/homepage.json

Übersetzt alle Text-Felder (hero, seelen, whyTirol, regionen, unterkuenfte,
activities, events, magazin) mit DeepSeek 4.1 Flash.

Nutzung:
  python scripts/translate_homepage.py <lang>            # eine Sprache
  python scripts/translate_homepage.py <lang> --force    # alles neu übersetzen
  python scripts/translate_homepage.py all               # alle Sprachen
"""
import os, sys, json, time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "src" / "data"

# Worker-Modul laden für translate_text
import importlib.util
spec = importlib.util.spec_from_file_location("tw", str(BASE_DIR / "scripts" / "translate_worker.py"))
tw = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tw)

LANGS = ["en", "fr", "cs", "nl", "it", "es", "zh", "pl", "hu", "sk"]

# Felder die NICHT übersetzt werden (URLs, Bilder, Farben, Klassen)
SKIP_KEYS = {"bgImage", "img", "href", "class", "iconClass", "statClass", "tagColor",
             "barColor", "dateBoxClass", "catClass", "badgeClass", "slug", "link",
             "tag", "stars", "day", "month", "price", "count", "stat", "icon", "emoji"}

def translate_value(val, lang, force=False):
    """Rekursiv übersetzen — nur Strings mit Text."""
    if isinstance(val, str):
        # Skip: URLs, Bilder, Farben, CSS-Klassen, Emojis-only, Zahlen
        if val.startswith('/') or val.startswith('http') or val.startswith('var(') or val.startswith('#'):
            return val
        if len(val.strip()) < 3:
            return val
        # Emoji-only
        stripped = val.strip()
        if all(ord(c) > 0x2000 for c in stripped if c.strip()):
            return val
        return tw.translate_text(val, lang, provider='ollama')
    elif isinstance(val, list):
        return [translate_value(v, lang, force) for v in val]
    elif isinstance(val, dict):
        out = {}
        for k, v in val.items():
            if k in SKIP_KEYS:
                out[k] = v
            else:
                out[k] = translate_value(v, lang, force)
        return out
    return val

def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("lang", help="Zielsprache oder 'all'")
    ap.add_argument("--force", action="store_true", help="Alles neu übersetzen")
    args = ap.parse_args()

    source = json.load(open(DATA_DIR / "homepage.json", encoding="utf-8"))
    langs = LANGS if args.lang == "all" else [args.lang]

    for lang in langs:
        target_path = DATA_DIR / lang / "homepage.json"
        target_path.parent.mkdir(parents=True, exist_ok=True)

        if target_path.exists() and not args.force:
            existing = json.load(open(target_path, encoding="utf-8"))
            # Merge: nur fehlende Sektionen übersetzen
            merged = dict(existing)
            missing_sections = [k for k in source.keys() if k not in existing]
            if not missing_sections:
                print(f"✅ {lang}: homepage.json vollständig — skip")
                continue
            print(f"🌍 {lang}: {len(missing_sections)} fehlende Sektionen: {missing_sections}")
            for section in missing_sections:
                print(f"   → übersetze '{section}'...")
                merged[section] = translate_value(source[section], lang)
            json.dump(merged, open(target_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
            print(f"   ✅ {lang}/homepage.json aktualisiert")
        else:
            print(f"🌍 {lang}: komplette Übersetzung...")
            translated = translate_value(source, lang)
            json.dump(translated, open(target_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
            print(f"   ✅ {lang}/homepage.json geschrieben")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
worker_gastro.py — Gastro Content Enricher
Generiert bessere deutsche Beschreibungen für Gastro-Einträge.
Nutzt die batch_extend-Infrastruktur.

Aufruf: python scripts/worker_gastro.py [--limit N] [--dry-run]
"""
import json, os, sys, re, time, argparse
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "src" / "data" / "gastro"

API_KEY = os.environ.get("OPENCODE_GO_API_KEY", "")
if not API_KEY:
    for env_file in [
        "E:/HermesPortable/home/.env",
        os.path.expanduser(r"~\.hermes\.env"),
    ]:
        if os.path.exists(env_file):
            with open(env_file) as f:
                for line in f:
                    if line.startswith("OPENCODE_GO_API_KEY="):
                        API_KEY = line.split("=", 1)[1].strip()
                        break
            if API_KEY:
                break

API_URL = "https://opencode.ai/zen/go/v1/chat/completions"

def needs_enrichment(slug):
    fp = DATA_DIR / slug / "index.json"
    if not fp.exists():
        return False
    with open(fp, encoding="utf-8") as f:
        data = json.load(f)
    kurz = data.get("kurzbeschreibung", "")
    # Enrich if kurz is very short (just "X in Tirol" pattern) or empty
    return len(kurz.strip()) < 60 or kurz.strip().endswith("in Tirol")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=3)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    slugs = sorted(os.listdir(DATA_DIR))
    todo = [s for s in slugs if needs_enrichment(s)]
    
    if not todo:
        print("✅ Alle Gastro-Einträge haben ausreichende Beschreibungen")
        return
    
    if args.dry_run:
        print(f"📊 {len(todo)} Einträge benötigen Anreicherung (zeige erste {min(5, len(todo))}):")
        for s in todo[:5]:
            fp = DATA_DIR / s / "index.json"
            with open(fp) as f:
                d = json.load(f)
            print(f"  • {d['name']}: \"{d.get('kurzbeschreibung','')[:60]}\"")
        return
    
    print(f"📊 {len(todo)} Einträge zu verarbeiten (Limit: {args.limit})")
    print(f"🔑 API-Key {'✓' if API_KEY else '✗ fehlt!'}")
    sys.exit(0)  # Placeholder — full enrichment via batch_extend

if __name__ == "__main__":
    main()

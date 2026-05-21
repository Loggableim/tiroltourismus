#!/usr/bin/env python3
"""
extend_descriptions.py — Beschreibungen auf min. 5 Sätze erweitern (alle Collections)

Durchläuft alle Einträge in sehenswuerdigkeiten, unterkuenfte, camping,
prüft die Satzanzahl und generiert bei Bedarf neue 5-8-sätzige Beschreibungen
über die opencode-go API (deepseek-v4-flash).

Aufruf:
  python scripts/extend_descriptions.py                          # alle Collections
  python scripts/extend_descriptions.py --collection camping      # nur eine
  python scripts/extend_descriptions.py --max 30                 # max 30 Einträge
  python scripts/extend_descriptions.py --batch 5 --resume       # Batch-Größe + Resume-Modus
  python scripts/extend_descriptions.py --skip-api               # Nur Analyse, kein API-Call
"""

import json, os, sys, time, re, ssl, urllib.request, argparse, glob

# ── Konfiguration ──────────────────────────────────────────────────────────
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src", "data")
API_URL = "https://opencode.ai/zen/go/v1/chat/completions"

# API-Key aus .env laden
API_KEY = os.environ.get("OPENCODE_GO_API_KEY", "")
if not API_KEY:
    for env_file in [
        "E:/HermesPortable/home/.env",
        os.path.expanduser(r"~\.hermes\.env"),
        r"C:\Users\logga\.hermes\.env",
    ]:
        if os.path.exists(env_file):
            with open(env_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("OPENCODE_GO_API_KEY="):
                        API_KEY = line.split("=", 1)[1].strip()
                        break
            if API_KEY:
                break

# Versuche requests (bessere SSL-Handhabung auf Windows)
try:
    import requests as req_lib
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# Collection-Konfiguration
COLLECTIONS = {
    "sehenswuerdigkeiten": {
        "dir": "sehenswuerdigkeiten",
        "label": "Sehenswürdigkeit",
        "typ_field": "kategorie",  # Feldname für den Typ
        "name_field": "name",
        "ort_field": "ort",
        "region_field": "region",
    },
    "unterkuenfte": {
        "dir": "unterkuenfte",
        "label": "Unterkunft",
        "typ_field": "typ",
        "name_field": "name",
        "ort_field": "ort",
        "region_field": "region",
    },
    "camping": {
        "dir": "camping",
        "label": "Campingplatz",
        "typ_field": "typ",
        "name_field": "name",
        "ort_field": "ort",
        "region_field": "region",
    },
}

PROGRESS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "extend_descriptions_progress.json")

# ── Hilfsfunktionen ────────────────────────────────────────────────────────

def count_sentences(text):
    """Zähle Sätze in HTML-Text."""
    clean = re.sub(r'<[^>]+>', '', text)
    clean = clean.replace('\n', ' ').strip()
    sents = [s.strip() for s in re.split(r'(?<=[.!?])\s+', clean) if s.strip()]
    return len(sents)


def load_entries(collection_name, collection_cfg):
    """Lade alle index.json eines Collections."""
    path = os.path.join(DATA_DIR, collection_cfg["dir"])
    if not os.path.isdir(path):
        print(f"  ⚠️ Verzeichnis nicht gefunden: {path}")
        return []
    
    entries = []
    for slug in sorted(os.listdir(path)):
        idx_path = os.path.join(path, slug, "index.json")
        if not os.path.exists(idx_path):
            continue
        try:
            with open(idx_path, encoding="utf-8") as f:
                data = json.load(f)
            name = data.get(collection_cfg["name_field"], slug)
            entries.append({
                "slug": slug,
                "filepath": idx_path,
                "collection": collection_name,
                "name": name,
                "ort": data.get(collection_cfg["ort_field"], ""),
                "region": data.get(collection_cfg["region_field"], ""),
                "typ": data.get(collection_cfg["typ_field"], ""),
                "beschreibung": data.get("beschreibung", ""),
                "data": data,
            })
        except Exception as e:
            print(f"  ⚠️ Fehler beim Lesen von {idx_path}: {e}")
    return entries


def generate_description(name, ort, region, typ, collection_label):
    """Generiere 5-8 Sätze Beschreibung via API."""
    
    prompt = (
        f"Schreibe eine sachlich-informative Beschreibung von 5 bis 8 Sätzen "
        f"über die {collection_label} '{name}' in {ort}, Tirol, Österreich. "
        f"Kategorie/Typ: {typ}. "
        f"Beschreibe die Lage, Angebote, Besonderheiten und was Besucher/Gäste erwartet. "
        f"Sachlich, informativ, kein Marketing-Jargon, keine Superlative. "
        f"Keine Wiederholungen. "
        f"Format: <p>Text mit <strong>Hervorhebungen</strong>.</p>"
    )

    body = {
        "model": "deepseek-v4-flash",
        "messages": [
            {"role": "system", "content": "Du schreibst sachliche, informative Beschreibungen für ein Tirol-Tourismusportal. Deutsch, 5-8 Sätze, als HTML-Paragraph. Kein Marketington, keine Übertreibungen. Keine Denkprozesse ausgeben – nur das HTML direkt."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 4096,
        "temperature": 0.3,
    }

    if HAS_REQUESTS:
        text = _call_via_requests(body)
    else:
        text = _call_via_urllib(body)
    
    if text:
        # Clean up: remove markdown code fences if any
        text = re.sub(r'^```(?:html)?\s*', '', text)
        text = re.sub(r'\s*```$', '', text)
        text = text.strip()
        # Ensure HTML wrapper
        if not text.startswith("<"):
            text = f"<p>{text}</p>"
        return text
    return ""


def _call_via_requests(body):
    try:
        resp = req_lib.post(
            API_URL,
            json=body,
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            },
            timeout=120,
        )
        if resp.status_code != 200:
            print(f"    ⚠️ HTTP {resp.status_code}: {resp.text[:200]}")
            # Retry once
            time.sleep(3)
            resp = req_lib.post(
                API_URL,
                json=body,
                headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                },
                timeout=120,
            )
            if resp.status_code != 200:
                raise ValueError(f"HTTP {resp.status_code} after retry")
        result = resp.json()
        text = result["choices"][0]["message"]["content"].strip()
        if not text:
            raise ValueError("Empty content from API")
        return text
    except Exception as e:
        print(f"    ⚠️ API-Fehler: {e}")
        return ""


def _call_via_urllib(body):
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        API_URL, data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        },
        method="POST",
    )
    try:
        resp = urllib.request.urlopen(req, timeout=120)
        result = json.loads(resp.read())
        text = result["choices"][0]["message"]["content"].strip()
        if not text:
            raise ValueError("Empty content")
        return text
    except Exception as e:
        print(f"    ⚠️ API-Fehler: {e}")
        try:
            time.sleep(3)
            resp = urllib.request.urlopen(req, timeout=120)
            result = json.loads(resp.read())
            text = result["choices"][0]["message"]["content"].strip()
            if not text:
                raise ValueError("Empty content on retry")
            return text
        except Exception as e2:
            print(f"    ⚠️ Retry fehlgeschlagen: {e2}")
            return ""


def save_progress(progress):
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(progress, f, indent=2, ensure_ascii=False)


def load_progress():
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {"processed": [], "collection_index": {}, "total_done": 0}


# ── Hauptlogik ─────────────────────────────────────────────────────────────

def process_entries(entries, collection_name, batch_size=6, max_entries=None, resume=False):
    """Verarbeite eine Liste von Einträgen (nur solche mit <5 Sätzen)."""
    
    progress = load_progress() if resume else {"processed": [], "collection_index": {}, "total_done": 0}
    processed_slugs = set(progress.get("processed", []))
    collection_done = progress.get("collection_index", {}).get(collection_name, 0)
    
    # Filtern: nur Einträge mit <5 Sätzen
    needs_work = []
    for entry in entries:
        if entry["slug"] in processed_slugs:
            continue
        sents = count_sentences(entry["beschreibung"])
        if sents < 5:
            needs_work.append((entry, sents))
    
    print(f"\n  {len(needs_work)} Einträge benötigen Update (von {len(entries)} total)")
    
    if max_entries:
        needs_work = needs_work[:max_entries]
        print(f"  Limitiert auf {max_entries} Einträge")
    
    if not needs_work:
        print("  ✅ Keine Arbeit nötig!")
        return 0
    
    total = len(needs_work)
    enriched = 0
    failed = 0
    skipped = 0
    
    for idx, (entry, old_sents) in enumerate(needs_work):
        if entry["slug"] in processed_slugs:
            skipped += 1
            continue
        
        num = collection_done + idx + 1
        print(f"\n  [{num}/{collection_done + total}] {entry['name']} in {entry['ort']} ({old_sents} Sätze -> 5-8)...", end=" ")
        sys.stdout.flush()
        
        # Beschreibung generieren
        desc = generate_description(
            entry["name"],
            entry["ort"],
            entry["region"],
            entry["typ"],
            COLLECTIONS[collection_name]["label"],
        )
        
        if desc and len(desc.strip("<>p/ ")) >= 20:
            # Verify sentence count
            new_sents = count_sentences(desc)
            if new_sents >= 5:
                entry["data"]["beschreibung"] = desc
                # Write back
                try:
                    with open(entry["filepath"], "w", encoding="utf-8") as f:
                        json.dump(entry["data"], f, indent=2, ensure_ascii=False)
                    print(f"✅ ({new_sents} Sätze)")
                    enriched += 1
                except Exception as e:
                    print(f"❌ Schreibfehler: {e}")
                    failed += 1
            else:
                print(f"⚠️ Nur {new_sents} Sätze, übersprungen")
                failed += 1
        else:
            print(f"❌ Leere Antwort")
            failed += 1
        
        # Progress speichern
        processed_slugs.add(entry["slug"])
        progress["processed"] = list(processed_slugs)
        progress["collection_index"][collection_name] = num
        progress["total_done"] = enriched
        save_progress(progress)
        
        # Rate Limit
        time.sleep(1.1)
    
    print(f"\n  ✅ {collection_name}: {enriched} aktualisiert, {failed} fehlgeschlagen, {skipped} übersprungen")
    return enriched


def analyze_only(entries, collection_name):
    """Nur Analyse ohne API-Calls."""
    from collections import Counter
    sents_dist = Counter()
    for entry in entries:
        sents_dist[count_sentences(entry["beschreibung"])] += 1
    
    print(f"\n  Total: {len(entries)} Einträge")
    print(f"  Satz-Verteilung:")
    for k in sorted(sents_dist.keys()):
        bar = "█" * (sents_dist[k] // 5) if sents_dist[k] >= 5 else "▏"
        print(f"    {k:2d} Sätze: {sents_dist[k]:4d} {bar}")
    
    needs = sum(c for k, c in sents_dist.items() if k < 5)
    print(f"  Benötigen Update (<5 Sätze): {needs}")
    return needs


def main():
    parser = argparse.ArgumentParser(description="Beschreibungen auf 5+ Sätze erweitern")
    parser.add_argument("--collection", choices=list(COLLECTIONS.keys()), help="Nur eine Collection verarbeiten")
    parser.add_argument("--batch", type=int, default=6, help="Batch-Größe (default: 6)")
    parser.add_argument("--max", type=int, help="Max Einträge pro Collection")
    parser.add_argument("--resume", action="store_true", help="Fortsetzen (Progress-Datei laden)")
    parser.add_argument("--skip-api", action="store_true", help="Nur Analyse, keine API-Calls")
    parser.add_argument("--reset-progress", action="store_true", help="Progress-Datei zurücksetzen")
    args = parser.parse_args()
    
    if args.reset_progress and os.path.exists(PROGRESS_FILE):
        os.remove(PROGRESS_FILE)
        print("Progress zurückgesetzt.")
        return
    
    collections_to_process = [args.collection] if args.collection else list(COLLECTIONS.keys())
    
    total_enriched = 0
    total_needs = 0
    
    for coll_name in collections_to_process:
        coll_cfg = COLLECTIONS[coll_name]
        print(f"\n{'='*60}")
        print(f"📂 {coll_name} ({coll_cfg['label']})")
        print(f"{'='*60}")
        
        entries = load_entries(coll_name, coll_cfg)
        
        if args.skip_api:
            needs = analyze_only(entries, coll_name)
            total_needs += needs
        else:
            enriched = process_entries(
                entries, coll_name,
                batch_size=args.batch,
                max_entries=args.max,
                resume=args.resume,
            )
            total_enriched += enriched
    
    if args.skip_api:
        print(f"\n{'='*60}")
        print(f"📊 Analyse abgeschlossen: {total_needs} Einträge benötigen Update")
        print(f"{'='*60}")
    else:
        print(f"\n{'='*60}")
        print(f"✅ Fertig! {total_enriched} Einträge auf 5+ Sätze erweitert")
        print(f"{'='*60}")


if __name__ == "__main__":
    main()
